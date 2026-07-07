/*
 * v_party_cohesion: party voting cohesion via the Rice index.
 *
 * Rice = |#for - #against| / (#for + #against) within a party on a single vote
 * (0 = evenly split, 1 = perfectly unified), averaged over votes. Computed on
 * PRESENT voters only, and only for party-votes with enough present members to be
 * meaningful (>= 5), so a near-empty party page can't manufacture a 1.0.
 *
 * Conformed across both sources: party comes from dim_legislator AS-OF the vote
 * date, so a SITL deputy who changed caucus is scored under whichever party they
 * held that day — the dated history feeds the cohesion measure correctly.
 */

{{ config(materialized='view') }}

WITH party_vote AS (
    SELECT
        f.source,
        f.legislature,
        l.party,
        f.vote_event_id,
        COUNT(*) FILTER (WHERE f.vote_cast = 'FOR')     AS n_for,
        COUNT(*) FILTER (WHERE f.vote_cast = 'AGAINST') AS n_against
    FROM {{ ref('fact_vote') }} f
    JOIN {{ ref('dim_legislator') }} l USING (legislator_key)
    WHERE l.party IS NOT NULL
    GROUP BY 1, 2, 3, 4
    HAVING (n_for + n_against) >= 5
)

SELECT
    source,
    legislature,
    party,
    COUNT(*)                                                            AS votes_scored,
    ROUND(AVG(ABS(n_for - n_against) * 1.0 / (n_for + n_against)), 4)   AS rice_index
FROM party_vote
GROUP BY 1, 2, 3
ORDER BY legislature, rice_index DESC
