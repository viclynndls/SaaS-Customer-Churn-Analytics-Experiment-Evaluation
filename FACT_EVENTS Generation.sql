USE DATABASE CX_ANALYTICS;
USE SCHEMA ANALYTICS;

CREATE OR REPLACE TABLE FACT_EVENTS AS
SELECT
    e.EVENT_ID,
    e.USER_ID,
    e.EVENT_TIMESTAMP,
    e.EVENT_DATE,
    e.EVENT_TYPE,
    e.SESSION_ID,
    e.DEVICE_TYPE,
    e.PLATFORM,
    e.IS_KNOWN_USER,

    
    -- day of week for usage patterns
    DAYOFWEEK(e.EVENT_DATE) AS EVENT_DAY_OF_WEEK,   -- 0=Sunday in Snowflake

    -- simple engagement flag
    CASE
        WHEN LOWER(e.EVENT_TYPE) IN ('app_open', 'complete_session', 'view_paywall', 'start_trial')
            THEN 1
        ELSE 0
    END AS IS_ENGAGEMENT_EVENT

FROM CX_ANALYTICS.TRANSFORM.STG_EVENTS e;
