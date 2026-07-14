#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 21 16:16:31 2025

@author: sunnybhardwaj
"""

import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
import isodate
import os

#API Setup
api_key = 'AIzaSyD8Ww6U520-8vENnOfuoVB_4rci0vCynPU'
youtube = build('youtube', 'v3', developerKey=api_key)

#Define Timeframe (for 2023 data)
published_after = '2023-01-01T00:00:00Z'
published_before = '2023-12-31T23:59:59Z'

#File Paths for Resumption
PROCESSED_CHANNELS_FILE = 'processed_channels_for_non_trending.txt'
TEMP_NON_TRENDING_DATA_FILE = 'temp_non_trending_videos.csv'

#Load Existing Trending Dataset & Setup for Resumption
df_trending_existing = pd.read_csv('Final/IN_youtube_trending_data.csv', dtype={'video_id': str})
df_trending_existing.columns

#Filtering required categories
req_cat = [10, 20, 24]
df_trending_existing = df_trending_existing[df_trending_existing['categoryId'].isin(req_cat)]

df_trending_existing['trending_date'] = pd.to_datetime(df_trending_existing['trending_date'])

#Filtering just 2023 trending videos
df_trending_existing = df_trending_existing[df_trending_existing['trending_date'].dt.year == 2023]
df_trending_existing = df_trending_existing.copy()
df_trending_existing.shape

#Filtering the required columns to be used in this process
df_trending_existing = df_trending_existing[['channelId', 'video_id', 'publishedAt']].drop_duplicates()
df_trending_existing.shape

#Get unique channel IDs from your trending data to process
selected_channel_ids = df_trending_existing['channelId'].unique().tolist()

#Initialize a set with ALL video IDs that are already there (from trending)
#This set will grow with non-trending videos, preventing duplicates
collected_video_ids_set = set(df_trending_existing['video_id'].unique())

print(f"Loaded {len(df_trending_existing)} existing trending videos from {len(selected_channel_ids)} unique channels.")
print(f"Initialized filter set with {len(collected_video_ids_set)} existing trending video IDs.")


#Load previously processed channels and non-trending data for resumption
processed_channels = []
if os.path.exists(PROCESSED_CHANNELS_FILE):
    with open(PROCESSED_CHANNELS_FILE, 'r') as f:
        processed_channels = [line.strip() for line in f if line.strip()]
    print(f"Resuming: {len(processed_channels)} channels already processed.")

all_non_trending_data = []
if os.path.exists(TEMP_NON_TRENDING_DATA_FILE):
    df_temp_non_trending = pd.read_csv(TEMP_NON_TRENDING_DATA_FILE)
    all_non_trending_data.extend(df_temp_non_trending.to_dict('records'))
    # Update collected_video_ids_set with previously fetched non-trending videos
    collected_video_ids_set.update(df_temp_non_trending['video_id'].dropna().unique())
    print(f"Resuming: Loaded {len(all_non_trending_data)} non-trending videos from temporary file.")

#Collection Parameters
#Max results per API request for videos/playlistItems/channels
BATCH_SIZE = 50

#Aim for this many non-trending videos per channel if available
TARGET_NON_TRENDING_VIDEOS_PER_CHANNEL = 15

print(f"\nStarting collection for {len(selected_channel_ids)} channels within 2023...")
print(f"Aiming for {TARGET_NON_TRENDING_VIDEOS_PER_CHANNEL} non-trending videos per channel.")


#Collect all 2023 videos from selected channels (excluding existing trending)
for i, channel_id in enumerate(selected_channel_ids):
    if channel_id in processed_channels:
        print(f"Skipping already processed channel: {channel_id}")
        continue

    print(f"Processing channel {i+1}/{len(selected_channel_ids)}: {channel_id}")
    videos_fetched_for_current_channel = 0
    
    try:
        #Get the uploads playlist ID for the channel
        channel_request = youtube.channels().list(
            part="contentDetails",
            id=channel_id
        )
        channel_response = channel_request.execute()
        if not channel_response.get('items'):
            print(f"  Channel {channel_id} not found or no contentDetails. Skipping.")
            #Mark as processed if truly cannot find it, to avoid retrying
            with open(PROCESSED_CHANNELS_FILE, 'a') as f:
                f.write(f"{channel_id}\n")
            continue
        uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        next_page_token_playlist = None
        
        while videos_fetched_for_current_channel < TARGET_NON_TRENDING_VIDEOS_PER_CHANNEL:
            playlist_request = youtube.playlistItems().list(
                part='snippet', #snippet contains videoId and publishedAt
                playlistId=uploads_playlist_id,
                maxResults=BATCH_SIZE,
                pageToken=next_page_token_playlist
            )
            playlist_response = playlist_request.execute()

            video_ids_to_detail_in_batch = []
            
            #Filter videos from this playlist page
            for item in playlist_response.get('items', []):
                video_id = item['snippet']['resourceId']['videoId']
                published_at_str = item['snippet']['publishedAt']

                #Optimization: Stop if videos are too old for the target range
                if published_at_str < published_after:
                    print(f"  Videos for {channel_id} are now older than {published_after.split('T')[0]}. Stopping this channel's playlist scan.")
                    videos_fetched_for_current_channel = TARGET_NON_TRENDING_VIDEOS_PER_CHANNEL #Force loop break
                    break #Break out of this for-loop (inner loop)
                
                #Filter by publish date AND ensure it's not already collected (trending or non-trending)
                if (published_after <= published_at_str <= published_before and
                    video_id not in collected_video_ids_set):
                    video_ids_to_detail_in_batch.append(video_id)

            if videos_fetched_for_current_channel >= TARGET_NON_TRENDING_VIDEOS_PER_CHANNEL:
                break #Break out of the while True loop if we've hit the target for this channel
                
            if not playlist_response.get('items') or not playlist_response.get('nextPageToken') and not video_ids_to_detail_in_batch:
                #No more videos in playlist, or no new relevant videos found and no more pages
                print(f"  No more new relevant videos for {channel_id} within the specified timeframe.")
                break #Break if no more videos or no relevant ones in this page

            #Fetch full details for the identified video IDs in sub-batches
            #Only make videos.list call if there are IDs to fetch
            if video_ids_to_detail_in_batch:
                for j in range(0, len(video_ids_to_detail_in_batch), BATCH_SIZE):
                    sub_batch_ids = video_ids_to_detail_in_batch[j : j + BATCH_SIZE]
                    if not sub_batch_ids: continue

                    details_request = youtube.videos().list(
                        part='snippet,statistics,contentDetails,status', #contentDetails for video length
                        id=','.join(sub_batch_ids)
                    )
                    details_response = details_request.execute()

                    for item in details_response.get('items', []):
                        snippet = item['snippet']
                        stats = item.get('statistics', {})
                        content_details = item.get('contentDetails', {})
                        status = item.get('status', {})

                        #Parse video duration from ISO 8601 format
                        duration_iso = content_details.get('duration', 'PT0S')
                        try:
                            duration_seconds = isodate.parse_duration(duration_iso).total_seconds()
                        except:
                            duration_seconds = 0 #Handle parsing errors

                        data = {
                            'video_id': item['id'],
                            'title': snippet.get('title'),
                            'publishedAt': snippet.get('publishedAt'),
                            'channelId': snippet.get('channelId'),
                            'channelTitle': snippet.get('channelTitle'),
                            'categoryId': snippet.get('categoryId'),
                            'trending_status': 'Non-Trending', #adding this column having non-trending status
                            'tags': snippet.get('tags', []),
                            'view_count': int(stats.get('viewCount', 0)),
                            'likes': int(stats.get('likeCount', 0)),
                            'dislikes': None, #Keeping this column as present in trending dataset but do not get these from YouTube now
                            'comment_count': int(stats.get('commentCount', 0)),
                            'thumbnail_link': snippet['thumbnails']['default']['url'],
                            'comments_disabled': not status.get('commentStatus', 'allowed') == 'allowed',
                            'ratings_disabled': not status.get('publicStatsViewable', True),
                            'description': snippet.get('description'),
                            'video_duration_seconds': duration_seconds
                        }
                        all_non_trending_data.append(data)
                        #Add to set to track all collected videos
                        collected_video_ids_set.add(item['id'])
                        videos_fetched_for_current_channel += 1
                        
                        if videos_fetched_for_current_channel >= TARGET_NON_TRENDING_VIDEOS_PER_CHANNEL:
                            print(f"  Reached target of {TARGET_NON_TRENDING_VIDEOS_PER_CHANNEL} non-trending videos for {channel_id}. Moving to next channel.")
                            break #Break from sub-batch loop

                if videos_fetched_for_current_channel >= TARGET_NON_TRENDING_VIDEOS_PER_CHANNEL:
                    break #Break from playlist item loop if target reached

            next_page_token_playlist = playlist_response.get('nextPageToken')
            if not next_page_token_playlist:
                break #No more pages for this channel's uploads
                #Short delay between playlist pages
            time.sleep(0.5) 

        #Mark channel as processed only after completing its collection loop
        with open(PROCESSED_CHANNELS_FILE, 'a') as f:
            f.write(f"{channel_id}\n")
        #Save non-trending data incrementally
        pd.DataFrame(all_non_trending_data).to_csv(TEMP_NON_TRENDING_DATA_FILE, index=False)

    except HttpError as e:
        if e.resp.status == 403 and 'quotaExceeded' in str(e):
            print(f"Quota Exceeded for channel {channel_id}. Script will stop. Resume tomorrow.")
            #Do NOT mark channel as processed if quota is exceeded mid-way
            break #Break main channel loop
        else:
            print(f"An HTTP error occurred for channel {channel_id}: {e}")
            #Mark as processed if it's not a quota error and likely won't resolve
            with open(PROCESSED_CHANNELS_FILE, 'a') as f:
                f.write(f"{channel_id}\n")
            time.sleep(5) #Longer sleep on other errors
            continue #Continue to next channel
    except Exception as e:
        print(f"An unexpected error occurred for channel {channel_id}: {e}")
        #Mark as processed for unexpected errors as well, might be specific channel issue
        with open(PROCESSED_CHANNELS_FILE, 'a') as f:
            f.write(f"{channel_id}\n")
        time.sleep(5) #Longer sleep on unexpected errors
        continue #Continue to next channel


df_non_trending = pd.DataFrame(all_non_trending_data)
print(f"\nTotal non-trending videos fetched (same-channel strategy, excluding existing trending): {len(df_non_trending)}")
print(df_non_trending.head())
