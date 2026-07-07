-- Data-quality cross-check: our independent per-deputy SITL capture must
-- reproduce SITL's OFFICIAL per-party tallies exactly, for every vote. We
-- aggregate our per-deputy vote_cast by vote and compare to the sum of the
-- official tally columns (the estadistico page's per-party breakdown). Any row
-- returned is a vote where our counts diverge from the official record.
WITH ours AS (
    SELECT
        vote_id,
        COUNT(*) FILTER (WHERE vote_cast = 'FOR')     AS a_favor,
        COUNT(*) FILTER (WHERE vote_cast = 'AGAINST') AS en_contra,
        COUNT(*) FILTER (WHERE vote_cast = 'ABSTAIN') AS abstencion,
        COUNT(*) FILTER (WHERE vote_cast = 'PRESENT') AS solo_asistencia,
        COUNT(*) FILTER (WHERE vote_cast = 'ABSENT')  AS ausente
    FROM {{ ref('stg_sitl_votes') }}
    GROUP BY vote_id
),

official AS (
    SELECT
        CAST(votaciont AS INT)            AS vote_id,
        SUM(CAST(a_favor AS INT))         AS a_favor,
        SUM(CAST(en_contra AS INT))       AS en_contra,
        SUM(CAST(abstencion AS INT))      AS abstencion,
        SUM(CAST(solo_asistencia AS INT)) AS solo_asistencia,
        SUM(CAST(ausente AS INT))         AS ausente
    FROM {{ source('raw', 'raw_sitl_tallies') }}
    GROUP BY 1
)

SELECT o.vote_id
FROM ours o
JOIN official f USING (vote_id)
WHERE o.a_favor         <> f.a_favor
   OR o.en_contra       <> f.en_contra
   OR o.abstencion      <> f.abstencion
   OR o.solo_asistencia <> f.solo_asistencia
   OR o.ausente         <> f.ausente
