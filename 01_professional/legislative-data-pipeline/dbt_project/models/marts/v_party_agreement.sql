/*
 * v_party_agreement: how often two parties land on the SAME side of a vote.
 *
 * Rice (v_party_cohesion) measures discipline WITHIN a party. This measures
 * alignment BETWEEN parties: for every roll-call, each party is reduced to the
 * side its present majority took (FOR / AGAINST; ties dropped, they pick no side),
 * and for each pair we report the share of co-voted events where the two sides
 * agree. 1.00 = the two parties are an effective bloc; 0.50 = they vote together
 * no more than chance.
 *
 * Conformed like every other view: party comes from dim_legislator AS-OF the vote
 * date, so a caucus switch moves the deputy's weight to the right party that day.
 * Emitted once per unordered pair (party_a < party_b) to avoid double counting.
 */

{{ config(materialized='view') }}

WITH party_pos AS (
    SELECT
        f.source,
        f.legislature,
        f.vote_event_id,
        l.party,
        COUNT(*) FILTER (WHERE f.vote_cast = 'FOR')     AS n_for,
        COUNT(*) FILTER (WHERE f.vote_cast = 'AGAINST') AS n_against
    FROM {{ ref('fact_vote') }} f
    JOIN {{ ref('dim_legislator') }} l USING (legislator_key)
    WHERE l.party IS NOT NULL
    GROUP BY 1, 2, 3, 4
    HAVING (n_for + n_against) >= 5
),

sided AS (
    SELECT
        source,
        legislature,
        vote_event_id,
        party,
        CASE WHEN n_for > n_against THEN 'FOR' ELSE 'AGAINST' END AS side
    FROM party_pos
    WHERE n_for <> n_against           -- a tie is no side; it can't agree or disagree
),

pairs AS (
    SELECT
        a.source,
        a.legislature,
        a.party AS party_a,
        b.party AS party_b,
        COUNT(*)                                       AS co_voted,
        COUNT(*) FILTER (WHERE a.side = b.side)         AS agreed
    FROM sided a
    JOIN sided b
      ON  a.source        = b.source
      AND a.legislature   = b.legislature
      AND a.vote_event_id = b.vote_event_id
      AND a.party < b.party             -- one row per unordered pair
    GROUP BY 1, 2, 3, 4
)

SELECT
    source,
    legislature,
    party_a,
    party_b,
    co_voted,
    agreed,
    ROUND(agreed * 1.0 / co_voted, 4) AS agreement_rate
FROM pairs
WHERE co_voted >= 20                   -- need enough shared votes to mean anything
ORDER BY legislature, agreement_rate DESC
