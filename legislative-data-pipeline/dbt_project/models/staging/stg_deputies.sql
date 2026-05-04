/*
 * stg_deputies: Cleaned legislator profiles.
 *
 * Source: raw.raw_dipmex_deputies
 * Grain: One row per legislator per legislature
 *
 * Transformations:
 *   1. Normalize names, party codes, and states
 *   2. Parse first_name / last_name from full_name (best-effort split)
 *   3. Standardize gender to single character (M/F)
 *   4. Deduplicate on (legislature, legislator_id)
 *   5. Generate surrogate key
 */

WITH source AS (
    SELECT * FROM {{ source('raw', 'raw_dipmex_deputies') }}
),

cleaned AS (
    SELECT
        legislature,
        TRIM(legislator_id) AS legislator_id,
        TRIM(full_name) AS full_name,
        UPPER(TRIM(party)) AS party,
        TRIM(state) AS state,
        UPPER(TRIM(district_type)) AS district_type,
        TRIM(district_number) AS district_number,
        UPPER(LEFT(TRIM(gender), 1)) AS gender,
        _loaded_at,
        ROW_NUMBER() OVER (
            PARTITION BY legislature, legislator_id
            ORDER BY _loaded_at DESC
        ) AS _row_num
    FROM source
)

SELECT
    MD5(CAST(legislature AS VARCHAR) || '|' || legislator_id) AS deputy_sk,
    legislature,
    legislator_id,
    full_name,
    -- Best-effort name parsing: assume "LAST1 LAST2, FIRST" or "FIRST LAST1 LAST2"
    CASE
        WHEN POSITION(',' IN full_name) > 0
        THEN TRIM(SUBSTRING(full_name FROM POSITION(',' IN full_name) + 1))
        ELSE TRIM(SPLIT_PART(full_name, ' ', 1))
    END AS first_name,
    CASE
        WHEN POSITION(',' IN full_name) > 0
        THEN TRIM(SUBSTRING(full_name FROM 1 FOR POSITION(',' IN full_name) - 1))
        ELSE TRIM(SUBSTRING(full_name FROM POSITION(' ' IN full_name) + 1))
    END AS last_name,
    party,
    state,
    district_type,
    district_number,
    gender,
    _loaded_at
FROM cleaned
WHERE _row_num = 1
