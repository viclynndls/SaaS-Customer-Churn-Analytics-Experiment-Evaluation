USE DATABASE CX_ANALYTICS;
USE SCHEMA ANALYTICS;

CREATE OR REPLACE TABLE FACT_SUBSCRIPTIONS AS
SELECT
    s.SUBSCRIPTION_ID,
    s.USER_ID,
    s.START_DATE,
    s.END_DATE,
    s.DURATION_DAYS,
    s.BILLING_PERIOD,
    s.PRICE_USD,
    s.IS_ACTIVE,
    s.IS_DURATION_VALID,
    s.IS_PRICE_VALID,
    s.IS_KNOWN_USER,

    -- standardized billing period
    CASE
        WHEN LOWER(s.BILLING_PERIOD) = 'monthly' THEN 'monthly'
        WHEN LOWER(s.BILLING_PERIOD) = 'annual'  THEN 'annual'
        ELSE 'other'
    END AS BILLING_PERIOD_STD,

    -- clean price
    CASE
        WHEN s.IS_PRICE_VALID = TRUE THEN s.PRICE_USD
        ELSE NULL
    END AS PRICE_USD_CLEAN,

    -- status based on end date + is_active flag
    CASE
        WHEN s.END_DATE IS NULL AND s.IS_ACTIVE = TRUE THEN 'active_no_end'
        WHEN s.END_DATE >= CURRENT_DATE AND s.IS_ACTIVE = TRUE THEN 'active'
        WHEN s.END_DATE < CURRENT_DATE THEN 'expired'
        ELSE 'unknown'
    END AS SUBSCRIPTION_STATUS

FROM CX_ANALYTICS.TRANSFORM.STG_SUBSCRIPTIONS s;
