/*
 * v_legislator_attendance: attendance per dated legislator version.
 *
 * Grain matches dim_legislator (one row per validity span). attendance_rate =
 * share of the version's eligible votes where the deputy was present (any cast
 * other than ABSENT). For SITL this is genuinely per-caucus-stint; for dipMex
 * it is per-term.
 */

{{ config(materialized='view') }}

SELECT
    l.legislator_key,
    l.source,
    l.legislature,
    l.legislator_id,
    l.full_name,
    l.party,
    COUNT(f.vote_key)                              AS votes_eligible,
    COUNT(f.vote_key) FILTER (WHERE f.is_present)  AS votes_present,
    ROUND(AVG(CASE WHEN f.is_present THEN 1.0 ELSE 0.0 END), 4) AS attendance_rate
FROM {{ ref('dim_legislator') }} l
LEFT JOIN {{ ref('fact_vote') }} f USING (legislator_key)
GROUP BY 1, 2, 3, 4, 5, 6
