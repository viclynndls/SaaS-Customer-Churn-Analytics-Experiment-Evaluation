USE DATABASE CX_ANALYTICS;
USE SCHEMA TRANSFORM;

CREATE OR REPLACE TABLE STG_EXPERIMENT_ASSIGNMENTS AS
WITH parsed AS (
    SELECT
        EXP_ASSIGNMENT_ID,
        USER_ID,

        -- Clean experiment name
        LOWER(TRIM(EXPERIMENT_NAME)) AS EXPERIMENT_NAME,

        -- Parse messy assignment_date strings into a proper DATE
        COALESCE(
            TRY_TO_DATE(ASSIGNMENT_DATE, 'MM/DD/YYYY'),
            TRY_TO_DATE(ASSIGNMENT_DATE, 'YYYY-MM-DD')
        ) AS ASSIGNMENT_DATE,

        -- Standardize variant values
        CASE
            WHEN LOWER(TRIM(VARIANT)) IN ('control', 'cntrl', 'cotnrol')
                THEN 'control'
            WHEN LOWER(TRIM(VARIANT)) IN ('treatment', 'treatmentt')
                THEN 'treatment'
            ELSE NULL
        END AS VARIANT

    FROM CX_ANALYTICS.RAW.EXPERIMENT_ASSIGNMENTS_RAW
),

-- Deduplicate: keep the latest assignment per user + experiment
deduped AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY USER_ID, EXPERIMENT_NAME
            ORDER BY ASSIGNMENT_DATE DESC, EXP_ASSIGNMENT_ID
        ) AS RN
    FROM parsed
),


with_user_flag AS (
    SELECT
        d.*,
        CASE
            WHEN u.USER_ID IS NULL THEN FALSE
            ELSE TRUE
        END AS IS_KNOWN_USER
    FROM deduped d
    LEFT JOIN CX_ANALYTICS.TRANSFORM.STG_USERS u
        ON d.USER_ID = u.USER_ID
    WHERE d.RN = 1
)

SELECT
    EXP_ASSIGNMENT_ID,
    USER_ID,
    EXPERIMENT_NAME,
    ASSIGNMENT_DATE,
    VARIANT,
    IS_KNOWN_USER
FROM with_user_flag;
