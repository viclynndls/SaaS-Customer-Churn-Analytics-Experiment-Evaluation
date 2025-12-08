# -*- coding: utf-8 -*-
"""
Created on Mon Dec  1 16:34:40 2025

@author: books
"""

import pandas as pd
import snowflake.connector
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import shap
import numpy as np
import os

####Connect to Snowflake#######################################################
conn = snowflake.connector.connect(
    user="USERNAME",              
    password="PASSWORD",    
    account="ACCOUNT ID",          
    warehouse="COMPUTE_WH",             
    database="CX_ANALYTICS",
    schema="ANALYTICS",
    role="SYSADMIN",                    
    authenticator="snowflake"   
)

cur = conn.cursor()
cur.execute("USE DATABASE CX_ANALYTICS;")
cur.execute("USE SCHEMA ANALYTICS;")
cur.close()



####Pull Relevant Dataset######################################################
query = "SELECT * FROM FTR_CHURN;"
df = pd.read_sql(query, conn)
conn.close()

print("Loaded rows:", len(df))
df.head()



####Handle age missingness properly############################################
df['AGE_MISSING'] = df['AGE'].isna().astype(int)
df['AGE'] = df['AGE'].fillna(0)



####Setup logistic regression model############################################
df_model = df.copy()

y = df_model["CHURNED"]

drop_cols = ["USER_ID", 
             "SIGNUP_DATE", "SIGNUP_MONTH", 
             "FIRST_EVENT_DATE", "LAST_EVENT_DATE",
             "LAST_SUB_START", "LAST_SUB_END",
             "LABEL_LAST_EVENT_DATE", "LABEL_LAST_SUB_END", "LAST_SURVEY_DATE"]

X = df_model.drop(columns=drop_cols + ["CHURNED"])

numeric_features = X.select_dtypes(include=['int64', 'float64']).columns.tolist()

categorical_features = X.select_dtypes(include=['object']).columns.tolist()

print("Numeric:", numeric_features)
print("Categorical:", categorical_features)

preprocess = ColumnTransformer(
    transformers=[
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features),
        ('num', 'passthrough', numeric_features)
    ]
)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y)

log_model = Pipeline(steps=[
    ('preprocess', preprocess),
    ('model', LogisticRegression(max_iter=200, class_weight='balanced'))
])

log_model.fit(X_train, y_train)

y_pred = log_model.predict(X_test)
y_prob = log_model.predict_proba(X_test)[:,1]

print("Logistic Regression Results")
print(classification_report(y_test, y_pred))
print("AUC:", roc_auc_score(y_test, y_prob))



####Setup Random Forest model##################################################
rf_model = Pipeline(steps=[
    ('preprocess', preprocess),
    ('model', RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        class_weight='balanced',
        random_state=42
    ))
])

rf_model.fit(X_train, y_train)

y_pred_rf = rf_model.predict(X_test)
y_prob_rf = rf_model.predict_proba(X_test)[:,1]

print("Random Forest Results")
print(classification_report(y_test, y_pred_rf))
print("AUC:", roc_auc_score(y_test, y_prob_rf))


####Confusion Matrix####
cm = confusion_matrix(y_test, y_pred_rf)
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
plt.title("Random Forest Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.show()


####Extract feature names####
ohe = rf_model.named_steps['preprocess'].named_transformers_['cat']
cat_feature_names = ohe.get_feature_names_out(categorical_features)

feature_names = list(cat_feature_names) + numeric_features
importances = rf_model.named_steps['model'].feature_importances_

fi_df = pd.DataFrame({
    'feature': feature_names,
    'importance': importances
}).sort_values('importance', ascending=False)

fi_df.head(20)


####Set up Feature Importance Plot#############################################
top_n = 10  

fi_df_head = fi_df.head(top_n)

plt.figure(figsize=(8, 10))
plt.barh(fi_df_head['feature'], fi_df_head['importance'])
plt.gca().invert_yaxis()  
plt.xlabel("Importance")
plt.title(f"Top {top_n} Feature Importances (Random Forest)")
plt.tight_layout()
plt.show()


####Set up SHAP Analysis and plots#############################################

preprocess_fitted = rf_model.named_steps['preprocess']
X_train_transformed = preprocess_fitted.transform(X_train)


if hasattr(X_train_transformed, "toarray"):
    X_train_dense = X_train_transformed.toarray()
else:
    X_train_dense = X_train_transformed


cat_transformer = preprocess_fitted.named_transformers_['cat']

if isinstance(cat_transformer, Pipeline):
    ohe = cat_transformer.named_steps['onehot']
else:
    ohe = cat_transformer  

cat_feature_names = ohe.get_feature_names_out(categorical_features)
feature_names = list(cat_feature_names) + numeric_features

print("X_train_dense shape:", X_train_dense.shape)
print("Number of feature names:", len(feature_names))


rf_estimator = rf_model.named_steps['model']
explainer = shap.TreeExplainer(rf_estimator)

shap_values = explainer.shap_values(X_train_dense)

if isinstance(shap_values, list):
    shap_values_churn = shap_values[1]
else:
    if shap_values.ndim == 3:
        shap_values_churn = shap_values[:, :, 1]
    else:
        shap_values_churn = shap_values

print("shap_values_churn shape:", shap_values_churn.shape)


# Beeswarm summary – direction & distribution
shap.summary_plot(
    shap_values_churn,
    X_train_dense,
    feature_names=feature_names,
    max_display=20,
    show=False
)

plt.title("SHAP Summary Plot – Direction & Magnitude of Feature Effects")
plt.tight_layout()
plt.savefig("figures/shap_summary_beeswarm.png", dpi=300, bbox_inches="tight")
plt.show()



os.makedirs("figures", exist_ok=True)

# Bar summary – global importance
shap.summary_plot(
    shap_values_churn,
    X_train_dense,
    feature_names=feature_names,
    plot_type="bar",
    max_display=10,
    show=False
)

plt.title("Global Feature Importance for Churn Model")
plt.tight_layout()
plt.savefig("figures/shap_global_importance_bar.png", dpi=300, bbox_inches="tight")
plt.show()



# Dependence plot – DAYS_SINCE_LAST_EVENT colored by NUM_SUBSCRIPTIONS
shap.dependence_plot(
    "DAYS_SINCE_LAST_EVENT",
    shap_values_churn,
    X_train_dense,
    feature_names=feature_names,
    interaction_index=feature_names.index("NUM_SUBSCRIPTIONS"),  # ensure color = num subs
    show=False
)

plt.title("SHAP Dependence – Days Since Last Event × Number of Subscriptions")
plt.tight_layout()
plt.savefig("figures/shap_dependence_days_since_last_event.png", dpi=300, bbox_inches="tight")
plt.show()

