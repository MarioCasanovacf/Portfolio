-- No legislator may have two validity spans that overlap. Half-open ranges
-- [effective_from, effective_to) overlap iff a.from < b.to AND b.from < a.to.
-- An overlap would let one vote match two dimension versions (double counting).
SELECT
    a.legislator_id,
    a.legislator_key AS key_a,
    b.legislator_key AS key_b,
    a.effective_from AS from_a,
    a.effective_to   AS to_a,
    b.effective_from AS from_b,
    b.effective_to   AS to_b
FROM {{ ref('dim_legislator') }} a
JOIN {{ ref('dim_legislator') }} b
    ON a.source = b.source
    AND a.legislator_id = b.legislator_id
    AND a.legislator_key < b.legislator_key
    AND a.effective_from < b.effective_to
    AND b.effective_from < a.effective_to
