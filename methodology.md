# 📘 Methodology

This document outlines the full end-to-end methodology used to build the SaaS Customer Churn Analytics & Experiment Evaluation project. It summarizes each component of the pipeline—from data generation to modeling, analytics engineering, and dashboard creation.

## 🧪 Data Generation & Simulation (Python)

A synthetic dataset was created to mimic realistic SaaS user behavior. Simulation allowed full control over the data-generating processes and ensured reproducibility across stages of the pipeline.

### Key Components

- User profile generation (age, country, signup date, plan type)
- Subscription lifecycles with renewals & cancellations
- Engagement simulation (event counts, active days, recency windows)
- Satisfaction data (NPS, CSAT, comment metadata)
- Randomized A/B test assignment
- Churn probability modeled using recency + low-activity heuristics

**Outcome:** A realistic, multi-table dataset suitable for warehousing, modeling, and BI.

## 🏗️ Snowflake Data Warehouse & Schema Design

A full Snowflake warehouse environment was built following a layered architecture (RAW → TRANSFORM → ANALYTICS).
This ensured clean separation between input data, cleaned data, and finalized analytic datasets.

### 🔹 RAW Layer

Raw CSV imports preserved the original structure for auditability.

#### Tables created

- USERS_RAW
- SUBSCRIPTIONS_RAW
- EVENTS_RAW
- SURVEY_RESPONSES_RAW
- EXPERIMENT_ASSIGNMENTS_RAW

### 🔹 TRANSFORM Layer

Raw fields were cast, cleaned, normalized, and staged.

#### Operations included

- Date type casting
- Categorical normalization
- Cleaning duration & price fields
- Creating staging tables:
  - STG_USERS
  - STG_SUBSCRIPTIONS
  - STG_EVENTS
  - STG_SURVEYS
  - STG_EXPERIMENT_ASSIGNMENTS

### 🔹 AGGREGATE Layer (Analytics Engineering)

User-level aggregates were built to prepare features for modeling:

**USER_EVENTS_AGG**

- Total events
- Active days
- Engagement events
- Events in last 7 / 30 days
- First & last event date

**USER_SUBSCRIPTION_AGG**

- Number of subscriptions
- Total revenue
- Last subscription start/end
- Active subscription flag

**USER_SURVEY_AGG**

- Avg NPS & CSAT
- % Promoter, % Detractor
- Count of meaningful comments

**USER_EXPERIMENT_AGG**

- Variant assignment
- Treatment flag
- Last assignment date

**USER_CHURN_LABEL**

Churn = inactive >45 days or subscription ended >45 days before the reference date.

## ⭐ Feature Table Creation (FTR_CHURN)

All aggregates were joined using USER_ID to produce a single wide table for modeling and BI.

### Features Included

- Subscription lifecycle metrics
- Revenue features
- Engagement recency/activity
- Satisfaction features
- A/B experiment assignment
- Churn label

This table served as the input to machine learning and Tableau dashboards.

## 🔍 Exploratory Data Analysis (Python + SQL)

EDA validated data quality and identified early churn patterns.

### Techniques Used

- Correlation analysis
- Recency/activity distributions
- Subscription tenure visualizations
- Early churn segmentation
- Revenue bucket analysis

### Key Insights

 - Engagement recency is strongly correlated with churn
 - Low lifetime activity → elevated churn probability
 - Subscription depth and revenue increase retention

## 🧪 A/B Experiment Evaluation

A simulated randomized experiment tested whether a treatment improved retention.

### Evaluation Steps

- Validated balanced assignment
- Compared churn, engagement, revenue
- Evaluated effect size
- Assessed practical significance

**Result:** Minimal lift — treatment not meaningful.

## 📊 Predictive Modeling (Logistic Regression + Random Forest)

Two models were trained to estimate churn probability and identify top drivers.

### Pipeline

- Train/test split with stratification
- One-hot encoding for categorical variables
- Model evaluation using AUC, precision, recall, F1

### Model Outcomes

- Both models reached ~98% AUC
- Top predictors:
  - Number of Subscriptions
  - Total Revenue
  - Has Active Subscription
  - Days Since Last Event

## 🧠 SHAP Model Explainability

SHAP explainability clarified how features influence churn predictions.

### SHAP Artifacts Generated

- Global feature importance bar chart
- Beeswarm distribution plot
- Dependence plot (Days Since Last Event × Subscription Count)

These validated the same behavioral patterns discovered during EDA.

## 📈 Dashboard Development (Tableau)

Five dashboards were built to allow stakeholders to explore insights interactively:

1. Project Overview Page
2. Customer Churn Overview
3. Churn Drivers & Behavioral Insights
4. Satisfaction & Segment Insights
5. Experiment Summary
6. Conclusions & Recommendations

📌 *Tableau Public link:*
[VIEW DASHBOARDS](https://public.tableau.com/views/SaaSCustomerChurnAnalyticsABTesting/SaaSCustomerChurnAnalyticsExperimentEvaluation?:language=en-US&publish=yes&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)

## 🔚 Summary

This methodology outlines a fully integrated data engineering → data science → BI workflow demonstrating skills in:

- Python
- SQL & Snowflake warehousing
- Data modeling
- Machine learning
- SHAP interpretability
- Experiment evaluation
- Tableau dashboard development

This structure mirrors real enterprise data workflows used in SaaS retention analytics.
