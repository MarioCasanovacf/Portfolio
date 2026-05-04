/*
 * fact_vote: Individual legislator votes.
 *
 * Grain: One row per legislator per vote event.
 * Joins staging votes with dim_legislator to get the dimension key.
 * Adds boolean convenience columns for common analytical patterns.
 */

WITH votes AS (
    SELECT * FROM {{ ref('stg_votes') }}
),

legislators AS (
    SELECT * FROM {{ ref('dim_legislator') }}
)

SELECT
    ROW_NUMBER() OVER (ORDER BY v.legislature, v.vote_date, v.vote_id, v.legislator_name) AS vote_key,
    CAST(REPLACE(CAST(v.vote_date AS VARCHAR), '-', '') AS INT) AS date_key,
    l.legislator_key,
    v.legislature,
    v.vote_id AS vote_event_id,
    v.vote_cast,
    (v.vote_cast = 'FOR') AS is_affirmative,
    (v.vote_cast != 'ABSENT') AS is_present
FROM votes v
LEFT JOIN legislators l
    ON v.legislator_name = l.full_name
    AND v.legislature = l.legislature
    AND l.is_current = TRUE
