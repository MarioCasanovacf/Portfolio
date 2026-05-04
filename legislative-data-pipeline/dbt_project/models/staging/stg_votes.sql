/*
 * stg_votes: Cleaned and deduplicated individual vote records.
 *
 * Source: raw.raw_dipmex_votes (dipMex academic dataset)
 * Grain: One row per legislator per vote event
 *
 * Transformations:
 *   1. Cast vote_date from string to DATE
 *   2. Standardize vote_cast to English enum values
 *   3. Normalize party and state strings
 *   4. Deduplicate on (legislature, vote_id, legislator_name), keeping latest load
 *   5. Generate deterministic surrogate key via MD5
 */

WITH source AS (
    SELECT * FROM {{ source('raw', 'raw_dipmex_votes') }}
),

cleaned AS (
    SELECT
        legislature,
        CAST(vote_date AS DATE) AS vote_date,
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
WHERE _row_num = 1
