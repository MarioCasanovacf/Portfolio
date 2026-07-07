/*
 * STAGING TRANSFORMS — DuckDB local execution
 * =============================================
 * These transforms run against the DuckDB local warehouse to populate
 * staging tables from raw data. In production (Snowflake), dbt handles
 * these transforms. This file provides a dbt-free path for local testing.
 */

-- stg_votes: Clean and deduplicate individual vote records
CREATE OR REPLACE TABLE staging.stg_votes AS
WITH source AS (
    SELECT * FROM raw.raw_dipmex_votes_64
    UNION ALL
    SELECT * FROM raw.raw_dipmex_votes_65
    UNION ALL
    SELECT * FROM raw.raw_dipmex_votes_66
),
cleaned AS (
    SELECT
        legislature,
        TRY_CAST(vote_date AS DATE) AS vote_date,
        vote_id,
        TRIM(legislator_name) AS legislator_name,
        UPPER(TRIM(party)) AS party,
        TRIM(state) AS state,
        TRIM(district) AS district,
        CASE UPPER(TRIM(vote_cast))
            WHEN 'FAVOR'       THEN 'FOR'
            WHEN 'A FAVOR'     THEN 'FOR'
            WHEN 'CONTRA'      THEN 'AGAINST'
            WHEN 'EN CONTRA'   THEN 'AGAINST'
            WHEN 'ABSTENCIÓN'  THEN 'ABSTAIN'
            WHEN 'ABSTENCION'  THEN 'ABSTAIN'
            WHEN 'AUSENTE'     THEN 'ABSENT'
            ELSE UPPER(TRIM(vote_cast))
        END AS vote_cast,
        _loaded_at,
        ROW_NUMBER() OVER (
            PARTITION BY legislature, vote_id, legislator_name
            ORDER BY _loaded_at DESC
        ) AS _row_num
    FROM source
)
SELECT
    MD5(CAST(legislature AS VARCHAR) || '|' || vote_id || '|' || legislator_name) AS vote_sk,
    legislature,
    vote_date,
    vote_id,
    legislator_name,
    party,
    state,
    district,
    vote_cast,
    _loaded_at
FROM cleaned
WHERE _row_num = 1;

-- stg_deputies: Clean legislator profiles
CREATE OR REPLACE TABLE staging.stg_deputies AS
WITH source AS (
    SELECT * FROM raw.raw_dipmex_deputies_64
    UNION ALL
    SELECT * FROM raw.raw_dipmex_deputies_65
    UNION ALL
    SELECT * FROM raw.raw_dipmex_deputies_66
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
WHERE _row_num = 1;
