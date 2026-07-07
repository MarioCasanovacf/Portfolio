-- Exactly one is_current = TRUE row per legislator (within a source — the two
-- id-spaces are disjoint). Zero would orphan the "where are they now" query;
-- more than one breaks the dated-history invariant.
SELECT
    source,
    legislator_id,
    COUNT(*) FILTER (WHERE is_current) AS n_current
FROM {{ ref('dim_legislator') }}
GROUP BY source, legislator_id
HAVING COUNT(*) FILTER (WHERE is_current) <> 1
