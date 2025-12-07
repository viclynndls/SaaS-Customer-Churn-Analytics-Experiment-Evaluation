# Data Architecture Overview

The project follows a modern, layered SaaS analytics architecture, moving data through clearly defined stages from raw ingestion to modeling and visualization. This structure mirrors production-grade analytical environments and supports reproducibility, scalability, and clean separation of responsibilities.

```
                          ┌─────────────────────────┐
                          │   Synthetic CSV Files   │
                          │ (Users, Events, Subs...)│
                          └───────────┬─────────────┘
                                      │
                                      ▼
                    ┌───────────────────────────────────┐
                    │     RAW LAYER (Snowflake)         │
                    │  • USERS_RAW                      │
                    │  • SUBSCRIPTIONS_RAW              │
                    │  • EVENTS_RAW                     │
                    │  • SURVEY_RESPONSES_RAW           │
                    │  • EXPERIMENT_ASSIGNMENTS_RAW     │
                    └───────────────────┬───────────────┘
                                        │  Cleaning, Casting,
                                        │  Normalization
                                        ▼
                    ┌───────────────────────────────────┐
                    │  TRANSFORM / STAGING LAYER        │
                    │  • STG_USERS                      │
                    │  • STG_SUBSCRIPTIONS              │
                    │  • STG_EVENTS                     │
                    │  • STG_SURVEYS                    │
                    │  • STG_EXPERIMENT_ASSIGNMENTS     │
                    └───────────────────┬───────────────┘
                                        │ Aggregation,
                                        │ Feature Engineering
                                        ▼
            ┌─────────────────────────────────────────────────────────┐
            │                 ANALYTICS / STAR SCHEMA                 │
            │                                                         │
            │ Dimension:                                              │
            │   • DIM_USERS                                           │
            │                                                         │
            │ Fact Tables:                                            │
            │   • FACT_EVENTS                                         │
            │   • FACT_SUBSCRIPTIONS_CLEAN                            │
            │   • FACT_SURVEY_RESPONSES                               │
            │   • FACT_EXPERIMENT_ASSIGNMENTS                         │
            │                                                         │
            │ Aggregations:                                           │
            │   • USER_EVENTS_AGG                                     │
            │   • USER_SUBSCRIPTION_AGG                               │
            │   • USER_SURVEY_AGG                                     │
            │   • USER_EXPERIMENT_AGG                                 │
            │   • USER_CHURN_LABEL                                    │
            └───────────────────┬─────────────────────────────────────┘
                                │ Unified Feature Construction
                                ▼
                  ┌───────────────────────────────────┐
                  │          FTR_CHURN TABLE          │
                  │  (Final ML Feature Dataset)       │
                  │  • Lifecycle features             │
                  │  • Engagement windows             │
                  │  • Revenue metrics                │
                  │  • Satisfaction aggregates        │
                  │  • Experiment variant             │
                  │  • Churn label                    │
                  └───────────────────┬───────────────┘
                                      │
                         ML Modeling  │  (Python: LR, RF, SHAP)
                                      ▼
                  ┌───────────────────────────────────┐
                  │   Predictive Modeling & SHAP      │
                  │ • Logistic Regression             │
                  │ • Random Forest                   │
                  │ • SHAP explainability             │
                  └───────────────────┬───────────────┘
                                      │
                     Visualization    │  (Tableau Dashboards)
                                      ▼
                  ┌───────────────────────────────────┐
                  │        Tableau Dashboards         │
                  │ • Customer Churn Overview         │
                  │ • Behavioral Drivers              │
                  │ • Satisfaction Insights           │
                  │ • Experiment Evaluation           │
                  │ • Conclusion & Recommendations    │
                  └───────────────────────────────────┘

```

This architecture follows a layered, modular design similar to enterprise SaaS analytics systems. Data is first ingested into a RAW layer in Snowflake, preserving the unaltered structure of the CSV exports. It is then cleaned, standardized, and cast into appropriate data types in the Transform Layer, creating staging tables ready for integration.

Next, the Analytics / Star Schema Layer organizes data into dimension and fact tables, enabling efficient BI queries and supporting downstream aggregations. User-level aggregates (events, subscriptions, surveys, experiments) and churn labels are created to provide high-quality analytical signals.

These components feed the FTR_CHURN feature table, the unified dataset used for machine learning modeling in Python (logistic regression, random forest, SHAP explainability). Finally, results are surfaced through interactive Tableau dashboards, supporting stakeholder storytelling and decision-making.
