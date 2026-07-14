#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 25 18:30:01 2025

@author: sunnybhardwaj
"""

import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
import isodate
import os

#API Setup
API_KEY = 'AIzaSyD8Ww6U520-8vENnOfuoVB_4rci0vCynPU'
youtube = build('youtube', 'v3', developerKey=API_KEY)

##Load Existing Trending Dataset
df_trending_existing = pd.read_csv('Final/IN_youtube_trending_data.csv', dtype={'video_id': str})

#Output CSV file where video IDs and their lengths will be saved
OUTPUT_VIDEO_LENGTHS_CSV = 'IN_youtube_trending_req_col_with_lengths.csv'


#Global Data Storage
video_lengths_data = []
#To track which video IDs we've already fetched duration for
processed_video_ids_for_duration = set() 

#Max video IDs per API request
BATCH_SIZE = 50

#Load Video IDs from Input CSV
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
df_input_ids = df_trending_existing[['channelId', 'video_id', 'publishedAt']].drop_duplicates()
df_input_ids.shape


unique_video_ids = df_input_ids['video_id'].dropna().unique().tolist()
print(f"Loaded {len(unique_video_ids)} unique video IDs from the input file.")


#Fetch Video Lengths from YouTube API
#If a temporary file exists from a previous run, load it to resume
if os.path.exists(OUTPUT_VIDEO_LENGTHS_CSV):
    try:
        df_temp_results = pd.read_csv(OUTPUT_VIDEO_LENGTHS_CSV)
        video_lengths_data.extend(df_temp_results.to_dict('records'))
        processed_video_ids_for_duration.update(df_temp_results['video_id'].dropna().unique())
        print(f"Resuming: Loaded {len(video_lengths_data)} previous results from '{OUTPUT_VIDEO_LENGTHS_CSV}'.")
    except Exception as e:
        print(f"Warning: Could not load existing '{OUTPUT_VIDEO_LENGTHS_CSV}' for resumption: {e}. Starting fresh.")
        #If loading fails, start fresh, the set remains empty.

video_ids_to_fetch = [
    vid for vid in unique_video_ids
    if vid not in processed_video_ids_for_duration #Skip already processed
]
print(f"Will fetch durations for {len(video_ids_to_fetch)} new video IDs.")


#Process video IDs in batches
for i in range(0, len(video_ids_to_fetch), BATCH_SIZE):
    batch_ids = video_ids_to_fetch[i : i + BATCH_SIZE]
    if not batch_ids: continue #Should not happen unless list is empty or last batch is processed

    try:
        details_request = youtube.videos().list(
            part='contentDetails', #Only need contentDetails for duration
            id=','.join(batch_ids)
        )
        details_response = details_request.execute()

        for item in details_response.get('items', []):
            content_details = item.get('contentDetails', {})
            duration_iso = content_details.get('duration', 'PT0S')
            try:
                duration_seconds = isodate.parse_duration(duration_iso).total_seconds()
            except:
                duration_seconds = 0 #Handle parsing errors for invalid duration strings

            video_lengths_data.append({
                'video_id': item['id'],
                'video_duration_seconds': duration_seconds
            })
            processed_video_ids_for_duration.add(item['id']) #Mark as processed
        
        #Save results incrementally after each batch
        pd.DataFrame(video_lengths_data).to_csv(OUTPUT_VIDEO_LENGTHS_CSV, index=False)
        time.sleep(0.1) #Small delay to respect API rate limits

    except HttpError as e:
        if e.resp.status == 403 and 'quotaExceeded' in str(e):
            print(f"Quota Exceeded. Script will stop. Results saved to '{OUTPUT_VIDEO_LENGTHS_CSV}'.")
            break #Break the loop if quota is hit
        elif e.resp.status == 404: #Not Found (e.g., deleted video)
            print(f"Warning: Video(s) in batch {batch_ids} not found (404 error). Skipping.")
            #Still mark as processed to avoid retrying deleted videos
            for vid_id in batch_ids:
                if vid_id not in processed_video_ids_for_duration: #Only add if not already added
                    video_lengths_data.append({'video_id': vid_id, 'video_duration_seconds': None}) #Mark as not found
                    processed_video_ids_for_duration.add(vid_id)
            pd.DataFrame(video_lengths_data).to_csv(OUTPUT_VIDEO_LENGTHS_CSV, index=False)
            time.sleep(1)
            continue
        else:
            print(f"An HTTP error occurred for batch {batch_ids}: {e}")
            time.sleep(2)
            continue #Continue to next batch
    except Exception as e:
        print(f"An unexpected error occurred for batch {batch_ids}: {e}")
        time.sleep(2)
        continue #Continue to next batch

#Final Export
df_video_lengths = pd.DataFrame(video_lengths_data)
print(f"\nFinal count of video lengths fetched: {len(df_video_lengths)}")
print(df_video_lengths.head())

df_video_lengths.to_csv(OUTPUT_VIDEO_LENGTHS_CSV, index=False)
print(f"\nAll video IDs with lengths exported to '{OUTPUT_VIDEO_LENGTHS_CSV}'")