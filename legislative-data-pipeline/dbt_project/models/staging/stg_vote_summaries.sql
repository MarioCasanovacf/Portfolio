/*
 * stg_vote_summaries: Aggregate vote outcomes from web scraping.
 *
 * Source: raw.raw_diputados_votes
 * Grain: One row per vote event
 *
 * Transformations:
 *   1. Parse session_date to DATE
 *   2. Compute total_votes and approval_rate
 *   3. Deduplicate on (legislature, vote_id)
 *   4. Generate surrogate key
 */

WITH source AS (
    SELECT * FROM {{ source('raw', 'raw_diputados_votes') }}
),

cleaned AS (
    SELECT
        legislature,
        CAST(session_date AS DATE) AS session_date,
        vote_id,
        TRIM(description) AS description,
        COALESCE(votes_for, 0) AS votes_for,
        COALESCE(votes_against, 0) AS votes_against,
        COALESCE(abstentions, 0) AS abstentions,
        COALESCE(absences, 0) AS absences,
        TRIM(detail_url) AS detail_url,
        _loaded_at,
        ROW_NUMBER() OVER (
            PARTITION BY legislature, vote_id
            ORDER BY _loaded_at DESC
        ) AS _row_num
    FROM source
)

SELECT
    MD5(CAST(legislature AS VARCHAR) || '|' || vote_id) AS vote_summary_sk,
    legislature,
    session_date,
    vote_id,
    description,
    votes_for,
    votes_against,
    abstentions,
    absences,
    (votes_for + votes_against + abstentions) AS total_votes,
    CASE
        WHEN (votes_for + votes_against + abstentions) > 0
        THEN CAST(votes_for AS FLOAT) / (votes_for + votes_against + abstentions)
        ELSE NULL
    END AS approval_rate,
    detail_url,
    _loaded_at
FROM cleaned
WHERE _row_num = 1
