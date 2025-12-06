CREATE OR REPLACE SCHEMA CX_ANALYTICS.TRANSFORM;

USE DATABASE CX_ANALYTICS;
USE SCHEMA TRANSFORM;

CREATE OR REPLACE TABLE STG_USERS AS
WITH parsed AS (
    SELECT
        USER_ID,

        -- Parse messy signup_date strings into a proper DATE
        COALESCE(
            TRY_TO_DATE(SIGNUP_DATE, 'YYYY-MM-DD'),
            TRY_TO_DATE(SIGNUP_DATE, 'DD-MM-YYYY'),
            TRY_TO_DATE(SIGNUP_DATE, 'MM/DD/YYYY'),
            TRY_TO_DATE(SIGNUP_DATE, 'MON DD YYYY')
        ) AS SIGNUP_DATE,

        -- Standardize country
        UPPER(TRIM(COUNTRY)) AS COUNTRY,

        -- Clean age and null out nonsense ages
        CASE
            WHEN TRY_TO_NUMBER(AGE) BETWEEN 16 AND 100 THEN TRY_TO_NUMBER(AGE)
            ELSE NULL
        END AS AGE,

        -- Standardize gender
        CASE
            WHEN LOWER(TRIM(GENDER)) IN ('female', 'fmale', 'femal', 'f') THEN 'female'
            WHEN LOWER(TRIM(GENDER)) IN ('male', 'mle', 'ml', 'm') THEN 'male'
            WHEN LOWER(TRIM(GENDER)) LIKE '%non%' THEN 'nonbinary'
            WHEN LOWER(TRIM(GENDER)) LIKE '%prefer%' THEN 'prefer_not_to_say'
            ELSE 'unknown'
        END AS GENDER,

        -- Standardize plan_type
        CASE
            WHEN LOWER(TRIM(PLAN_TYPE)) LIKE '%free%' THEN 'free'
            WHEN LOWER(TRIM(PLAN_TYPE)) LIKE '%basic%' THEN 'basic'
            WHEN LOWER(TRIM(PLAN_TYPE)) LIKE '%premium%' THEN 'premium'
            ELSE NULL
        END AS PLAN_TYPE,

        -- Clean acquisition_channel
        CASE
            WHEN LOWER(TRIM(ACQUISITION_CHANNEL)) IN ('facebook_ads', 'facebook', 'fb', 'fbook', 'meta_ads')
                THEN 'facebook_ads'
            WHEN LOWER(TRIM(ACQUISITION_CHANNEL)) IN ('google_ads', 'google', 'adwords', 'ggl')
                THEN 'google_ads'
            WHEN LOWER(TRIM(ACQUISITION_CHANNEL)) IN ('referral', 'referal', 'friend_ref')
                THEN 'referral'
            WHEN LOWER(TRIM(ACQUISITION_CHANNEL)) IN ('organic', 'org') OR LOWER(TRIM(ACQUISITION_CHANNEL)) LIKE '%org%'
                THEN 'organic'
            WHEN LOWER(TRIM(ACQUISITION_CHANNEL)) LIKE '%mail%'
                THEN 'email'
            ELSE 'unknown'
        END AS ACQUISITION_CHANNEL,

        -- Clean primary_device
        CASE
            WHEN LOWER(TRIM(PRIMARY_DEVICE)) IN ('ios') THEN 'ios'
            WHEN LOWER(TRIM(PRIMARY_DEVICE)) IN ('android') THEN 'android'
            WHEN LOWER(TRIM(PRIMARY_DEVICE)) IN ('web') THEN 'web'
            ELSE 'unknown'
        END AS PRIMARY_DEVICE

    FROM CX_ANALYTICS.RAW.USERS_RAW
),

deduped AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY USER_ID ORDER BY SIGNUP_DATE DESC) AS RN
    FROM parsed
)

SELECT
    USER_ID,
    SIGNUP_DATE,
    COUNTRY,
    AGE,
    GENDER,
    PLAN_TYPE,
    ACQUISITION_CHANNEL,
    PRIMARY_DEVICE
FROM deduped
WHERE RN = 1;

SELECT * FROM CX_ANALYTICS.TRANSFORM.STG_USERS LIMIT 20;
