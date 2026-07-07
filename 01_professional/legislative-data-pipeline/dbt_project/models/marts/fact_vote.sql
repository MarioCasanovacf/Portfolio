/*
 * fact_vote: individual legislator votes, CONFORMED across dipMex + SITL.
 *
 * Grain: one row per legislator per vote event (a real cast vote). Each source
 * joins its dim_legislator version AS-OF the vote date (the version whose
 * [effective_from, effective_to) span contains it): for dipMex that resolves the
 * term occupant; for SITL it resolves which CAUCUS the deputy belonged to that
 * day. The join is on (source, legislator_id) so the two id-spaces (dipMex seat
 * ids vs SITL iddipt) never collide.
 */

WITH dipmex_votes AS (
    SELECT 'dipmex' AS source, vote_sk, legislature, vote_id, legislator_id, vote_date, vote_cast
    FROM {{ ref('stg_votes') }}
),

sitl_votes AS (
    SELECT 'sitl' AS source, vote_sk, legislature, vote_id, legislator_id, vote_date, vote_cast
    FROM {{ ref('stg_sitl_votes') }}
),

votes AS (
    SELECT * FROM dipmex_votes
    UNION ALL
    SELECT * FROM sitl_votes
),

legislators AS (
    SELECT * FROM {{ ref('dim_legislator') }}
)

SELECT
    v.vote_sk AS vote_key,
    CAST(REPLACE(CAST(v.vote_date AS VARCHAR), '-', '') AS INT) AS date_key,
    l.legislator_key,
    v.source,
    v.legislator_id,
    v.legislature,
    v.vote_id AS vote_event_id,
    v.vote_cast,
    (v.vote_cast = 'FOR')      AS is_affirmative,
    (v.vote_cast != 'ABSENT')  AS is_present
FROM votes v
LEFT JOIN legislators l
    ON v.source = l.source
    AND v.legislator_id = l.legislator_id
    AND v.vote_date >= l.effective_from
    AND v.vote_date <  l.effective_to
