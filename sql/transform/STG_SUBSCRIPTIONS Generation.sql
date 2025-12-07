USE DATABASE CX_ANALYTICS;
USE SCHEMA TRANSFORM;

CREATE OR REPLACE TABLE STG_SUBSCRIPTIONS AS
WITH parsed AS (
    SELECT
        SUBSCRIPTION_ID,
        USER_ID,

        -- Parse dates
        TRY_TO_DATE(START_DATE, 'YYYY-MM-DD') AS START_DATE,
        TRY_TO_DATE(END_DATE,   'YYYY-MM-DD') AS END_DATE,

        -- Duration in days 
        DATEDIFF(
            'day',
            TRY_TO_DATE(START_DATE, 'YYYY-MM-DD'),
            TRY_TO_DATE(END_DATE,   'YYYY-MM-DD')
        ) AS DURATION_DAYS,

        -- Standardize billing_period
        CASE
            WHEN LOWER(TRIM(BILLING_PERIOD)) IN ('monthly', 'mth', 'mo') 
            THEN 'monthly'
            WHEN LOWER(TRIM(BILLING_PERIOD)) IN ('annual', 'yr', 'yearly') 
            THEN 'annual'
            ELSE NULL
        END AS BILLING_PERIOD,

        -- Clean price
        CASE
            WHEN TRY_TO_NUMBER(PRICE_USD) BETWEEN 0 AND 50
                THEN TRY_TO_NUMBER(PRICE_USD)
            ELSE NULL
        END AS PRICE_USD,

        -- Clean is_active
        CASE
            WHEN UPPER(TRIM(TO_VARCHAR(IS_ACTIVE))) IN ('TRUE', '1', 'T') THEN TRUE
            WHEN UPPER(TRIM(TO_VARCHAR(IS_ACTIVE))) IN ('FALSE', '0', 'F') THEN FALSE
            ELSE NULL
        END AS IS_ACTIVE

    FROM CX_ANALYTICS.RAW.SUBSCRIPTIONS_RAW
),


with_flags AS (
    SELECT
        p.*,

        -- Duration sanity check
        CASE
            WHEN DURATION_DAYS IN (30, 365) THEN TRUE
            ELSE FALSE
        END AS IS_DURATION_VALID,

        -- Price sanity check
        CASE
            WHEN PRICE_USD IS NOT NULL THEN TRUE
            ELSE FALSE
        END AS IS_PRICE_VALID

    FROM parsed p
),

with_user_flag AS (
    SELECT
        f.*,
        CASE
            WHEN u.USER_ID IS NULL THEN FALSE
            ELSE TRUE
        END AS IS_KNOWN_USER
    FROM with_flags f
    LEFT JOIN CX_ANALYTICS.TRANSFORM.STG_USERS u
        ON f.USER_ID = u.USER_ID
)

SELECT
    SUBSCRIPTION_ID,
    USER_ID,
    START_DATE,
    END_DATE,
    DURATION_DAYS,
    BILLING_PERIOD,
    PRICE_USD,
    IS_ACTIVE,
    IS_DURATION_VALID,
    IS_PRICE_VALID,
    IS_KNOWN_USER
FROM with_user_flag;
