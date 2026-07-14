# Predicting Trendiness of YouTube Videos Using Pre-Upload Metadata

## Project Overview

Every day, thousands of videos are uploaded to YouTube, but only a small percentage gain enough traction to appear on the platform's Trending list. Understanding which factors contribute to a video's likelihood of trending can help content creators optimize their publishing strategy before a video goes live.

This project develops an end-to-end machine learning pipeline that predicts whether a YouTube video will become trending using only pre-upload metadata. Unlike many existing studies that rely on post-upload engagement metrics such as views, likes, and comments, this project focuses exclusively on information available before publication, making the prediction practically useful for creators.

The project combines publicly available trending video data from Kaggle with non-trending video metadata collected using the YouTube Data API v3. After extensive data preprocessing, feature engineering, exploratory data analysis, and statistical validation, multiple classification models were developed and evaluated to identify the most effective approach.

---

## Objectives

- Identify which pre-upload metadata features influence whether a video trends.
- Perform exploratory data analysis to understand relationships between metadata and trending status.
- Build machine learning models capable of predicting trending videos.
- Compare multiple classification algorithms.
- Generate actionable insights for YouTube content creators.

---

## Project Workflow

→ Data Collection
→ Data Cleaning
→ Data Preprocessing
→ Feature Engineering
→ Exploratory Data Analysis
→ Feature Selection
→ Model Training
→ Model Evaluation
→ Feature Importance Analysis
→ Business Insights

---

## Dataset

The dataset was created by combining two sources:

- Trending videos collected from the Kaggle YouTube Trending Videos Dataset.
- Non-trending videos collected using the YouTube Data API v3.

### Scope

- Country: India
- Upload Year: 2023
- Categories:
  - Entertainment
  - Music
  - Gaming

Using non-trending videos from the same channels as trending videos helped reduce channel popularity bias and enabled a fairer comparison.

---

## Technologies Used

- Python
- Pandas
- NumPy
- Scikit-learn
- XGBoost
- Matplotlib
- Seaborn
- SciPy
- VADER Sentiment
- WordCloud
- Google YouTube Data API v3
- Jupyter Notebook
- Spyder IDE

---

## Project Structure

```
youtube-trending-prediction/
│
├── Codes/
├── Datasets/
├── Documentation/
├── README.md
├── requirements.txt
└── .gitignore
```

---

## Machine Learning Models

Three supervised classification models were developed and compared.

| Model | Purpose |
|---------|----------|
| Logistic Regression | Baseline interpretable model |
| Random Forest | Non-linear ensemble model |
| XGBoost | Gradient boosting model |

---

## Model Performance

| Model               | Accuracy  | Precision | ROC AUC   |
| ------------------- | --------- | --------- | --------- |
| Logistic Regression | 81.5%     | 86.3%     | 89.8%     |
| Random Forest       | 89.0%     | 94.7%     | 96.8%     |
| XGBoost             | 89.6%     | 93.1%     | 96.6%     |

Random Forest consistently performed well across all three metrics, making it the final selected model.
---

## Business Insights

The analysis revealed several metadata characteristics associated with trending videos:

- Longer video durations were more common among trending videos.
- Channels with a stronger history of trending content had a higher probability of producing additional trending videos.
- Longer and richer video descriptions improved discoverability.
- Videos containing more relevant tags performed better.
- Better alignment between titles and tags increased trending likelihood.
- Upload timing (day and hour) showed measurable influence on trend probability.
- Positive sentiment in descriptions showed a slight association with trending.
- Excessive emoji usage in titles did not improve trending performance.

---

## Visualizations

The repository includes:

- Exploratory Data Analysis
- Feature Distributions
- Boxplots
- Statistical Test Results
- Model Comparison
- Feature Importance

---

## Installation

git clone ...
cd youtube-trending-prediction

pip install -r requirements.txt

---

## Future Improvements

- Deploy the model as a Streamlit web application.
- Support real-time predictions using the YouTube Data API.
- Extend the analysis across multiple countries.
- Train category-specific prediction models.
- Explore transformer-based NLP models for title and description analysis.
- Perform automated hyperparameter optimization.
- Build an explainable AI dashboard using SHAP values.
- Develop an automated retraining pipeline for new YouTube trends.

---

## Author

Shivani Bhardwaj
