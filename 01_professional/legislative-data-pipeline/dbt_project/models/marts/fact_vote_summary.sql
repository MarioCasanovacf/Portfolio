/*
 * fact_vote_summary: Aggregate vote outcomes.
 *
 * Grain: One row per vote event.
 * Enriches staged summaries with computed metrics.
 */

WITH summaries AS (
    SELECT * FROM {{ ref('stg_vote_summaries') }}
)

SELECT
    ROW_NUMBER() OVER (ORDER BY legislature, session_date, vote_id) AS vote_summary_key,
    CAST(REPLACE(CAST(session_date AS VARCHAR), '-', '') AS INT) AS date_key,
    legislature,
    vote_id AS vote_event_id,
    description,
    votes_for,
    votes_against,
    abstentions,
    absences,
    total_votes AS total_present,
    (total_votes + absences) AS total_eligible,
    approval_rate,
    (approval_rate > 0.5) AS is_approved,
    FALSE AS requires_qualified,
    detail_url
FROM summaries
