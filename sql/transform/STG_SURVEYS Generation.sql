USE DATABASE CX_ANALYTICS;
USE SCHEMA TRANSFORM;

CREATE OR REPLACE TABLE STG_SURVEYS AS
WITH parsed AS (
    SELECT
        RESPONSE_ID,
        USER_ID,

        -- Parse response_date
        COALESCE(
            TRY_TO_DATE(RESPONSE_DATE, 'DD-MM-YYYY'),
            TRY_TO_DATE(RESPONSE_DATE, 'YYYY-MM-DD')
        ) AS RESPONSE_DATE,

        -- Clean NPS
        CASE
            WHEN TRY_TO_NUMBER(NPS_SCORE) BETWEEN 0 AND 10 THEN TRY_TO_NUMBER(NPS_SCORE)
            ELSE NULL
        END AS NPS_SCORE,

        -- Clean CSAT
        CASE
            WHEN TRY_TO_NUMBER(CSAT_SCORE) BETWEEN 1 AND 5 THEN TRY_TO_NUMBER(CSAT_SCORE)
            ELSE NULL
        END AS CSAT_SCORE,

        -- Standardize ease_of_use
        CASE
            WHEN LOWER(TRIM(EASE_OF_USE)) IN ('very_easy', 'vry_easy') THEN 'very_easy'
            WHEN LOWER(TRIM(EASE_OF_USE)) = 'easy'                     THEN 'easy'
            WHEN LOWER(TRIM(EASE_OF_USE)) = 'neutral'                  THEN 'neutral'
            WHEN LOWER(TRIM(EASE_OF_USE)) = 'hard'                     THEN 'hard'
            WHEN LOWER(TRIM(EASE_OF_USE)) = 'very_difficult'           THEN 'very_difficult'
            ELSE NULL
        END AS EASE_OF_USE,

        -- Raw comment
        COMMENT_TEXT,

        -- Strip basic HTML tags like <br> and trim whitespace
        TRIM(REGEXP_REPLACE(COMMENT_TEXT, '<[^>]+>', '')) AS COMMENT_TEXT_CLEAN,

        -- Flags for text content
        CASE WHEN COMMENT_TEXT ILIKE '%http%' THEN TRUE ELSE FALSE END AS HAS_URL,
        CASE WHEN COMMENT_TEXT ILIKE '%<%' AND COMMENT_TEXT ILIKE '%>%' THEN TRUE ELSE FALSE END AS HAS_HTML

    FROM CX_ANALYTICS.RAW.SURVEY_RESPONSES_RAW
),

with_labels AS (
    SELECT
        p.*,

        -- Standard NPS buckets
        CASE
            WHEN NPS_SCORE BETWEEN 0 AND 6 THEN 'detractor'
            WHEN NPS_SCORE BETWEEN 7 AND 8 THEN 'passive'
            WHEN NPS_SCORE BETWEEN 9 AND 10 THEN 'promoter'
            ELSE 'no response'
        END AS NPS_CATEGORY,

        -- Simple CSAT buckets
        CASE
            WHEN CSAT_SCORE IS NULL THEN 'no response'
            WHEN CSAT_SCORE <= 2 THEN 'low'
            WHEN CSAT_SCORE = 3  THEN 'neutral'
            WHEN CSAT_SCORE >= 4 THEN 'high'
        END AS CSAT_CATEGORY

    FROM parsed p
),

with_user_flag AS (
    SELECT
        w.*,
        CASE
            WHEN u.USER_ID IS NULL THEN FALSE
            ELSE TRUE
        END AS IS_KNOWN_USER
    FROM with_labels w
    LEFT JOIN CX_ANALYTICS.TRANSFORM.STG_USERS u
        ON w.USER_ID = u.USER_ID
)

SELECT
    RESPONSE_ID,
    USER_ID,
    RESPONSE_DATE,
    NPS_SCORE,
    NPS_CATEGORY,
    CSAT_SCORE,
    CSAT_CATEGORY,
    EASE_OF_USE,
    COMMENT_TEXT,
    COMMENT_TEXT_CLEAN,
    HAS_URL,
    HAS_HTML,
    IS_KNOWN_USER
FROM with_user_flag;
