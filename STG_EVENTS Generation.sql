USE DATABASE CX_ANALYTICS;
USE SCHEMA TRANSFORM;

CREATE OR REPLACE TABLE STG_EVENTS AS
WITH parsed AS (
    SELECT
        EVENT_ID,
        USER_ID,

        -- Parse ISO event_time into proper TIMESTAMP (no timezone)
        TRY_TO_TIMESTAMP_NTZ(EVENT_TIME) AS EVENT_TIMESTAMP,

        TO_DATE(TRY_TO_TIMESTAMP_NTZ(EVENT_TIME)) AS EVENT_DATE,

        -- Standardize event_type
        CASE
            WHEN LOWER(TRIM(EVENT_TYPE)) IN ('app_open', 'ap_open', 'open', 'appopen')
                THEN 'app_open'
            WHEN LOWER(TRIM(EVENT_TYPE)) IN ('complete_session', 'complete', 'finish_session')
                THEN 'complete_session'
            WHEN LOWER(TRIM(EVENT_TYPE)) IN ('view_paywall', 'view_pay', 'paywall_view')
                THEN 'view_paywall'
            WHEN LOWER(TRIM(EVENT_TYPE)) = 'start_trial'
                THEN 'start_trial'
            WHEN LOWER(TRIM(EVENT_TYPE)) = 'cancel'
                THEN 'cancel'
            ELSE NULL
        END AS EVENT_TYPE,

        -- Clean session_id
        NULLIF(TRIM(SESSION_ID), '') AS SESSION_ID,

        -- Standardize device_type
        CASE
            WHEN LOWER(TRIM(DEVICE_TYPE)) = 'ios' 
            THEN 'ios'
            WHEN LOWER(TRIM(DEVICE_TYPE)) = 'android' 
            THEN 'android'
            WHEN LOWER(TRIM(DEVICE_TYPE)) = 'web'             
            THEN 'web'
            WHEN LOWER(TRIM(DEVICE_TYPE)) IN ('windows phone', 'playstation')
                THEN 'other'
            ELSE NULL
        END AS DEVICE_TYPE,

        -- Standardize platform
        CASE
            WHEN LOWER(TRIM(PLATFORM)) = 'ios'  
            THEN 'ios'
            WHEN LOWER(TRIM(PLATFORM)) = 'android'           
            THEN 'android'
            WHEN LOWER(TRIM(PLATFORM)) = 'web'               
            THEN 'web'
            WHEN LOWER(TRIM(PLATFORM)) = 'playstation'       
            THEN 'other'
            ELSE NULL
        END AS PLATFORM

    FROM CX_ANALYTICS.RAW.EVENTS_RAW
),


with_user_flag AS (
    SELECT
        p.*,
        CASE
            WHEN u.USER_ID IS NULL THEN FALSE
            ELSE TRUE
        END AS IS_KNOWN_USER
    FROM parsed p
    LEFT JOIN CX_ANALYTICS.TRANSFORM.STG_USERS u
        ON p.USER_ID = u.USER_ID
)

SELECT
    EVENT_ID,
    USER_ID,
    EVENT_TIMESTAMP,
    EVENT_DATE,
    EVENT_TYPE,
    SESSION_ID,
    DEVICE_TYPE,
    PLATFORM,
    IS_KNOWN_USER
FROM with_user_flag;
