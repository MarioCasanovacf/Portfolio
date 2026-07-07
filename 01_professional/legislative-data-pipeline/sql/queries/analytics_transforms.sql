/*
 * ANALYTICS TRANSFORMS — Build dimensional models from staging
 * ==============================================================
 * DuckDB local execution. In production, dbt handles these.
 */

-- dim_party: Political party reference
CREATE OR REPLACE TABLE analytics.dim_party AS
SELECT * FROM (
    VALUES
        ('MORENA', 'Movimiento Regeneración Nacional', 'LEFT', 2014, TRUE),
        ('PAN', 'Partido Acción Nacional', 'CENTER_RIGHT', 1939, TRUE),
        ('PRI', 'Partido Revolucionario Institucional', 'CENTER', 1929, TRUE),
        ('PRD', 'Partido de la Revolución Democrática', 'CENTER_LEFT', 1989, TRUE),
        ('PVEM', 'Partido Verde Ecologista de México', 'CENTER', 1986, TRUE),
        ('PT', 'Partido del Trabajo', 'LEFT', 1990, TRUE),
        ('MC', 'Movimiento Ciudadano', 'CENTER_LEFT', 1999, TRUE),
        ('SP', 'Sin Partido (Independiente)', 'CENTER', NULL, TRUE)
) AS t(party_code, party_name, ideology_spectrum, founded_year, is_active);

-- dim_legislator: SCD Type 2 (initial load — all records current)
CREATE OR REPLACE TABLE analytics.dim_legislator AS
WITH hashed AS (
    SELECT
        *,
        MD5(
            COALESCE(party, '') || '|' ||
            COALESCE(state, '') || '|' ||
            COALESCE(district_type, '') || '|' ||
            COALESCE(district_number, '')
        ) AS _hash
    FROM staging.stg_deputies
)
SELECT
    ROW_NUMBER() OVER (ORDER BY legislature, legislator_id) AS legislator_key,
    legislator_id,
    full_name,
    first_name,
    last_name,
    party,
    state,
    district_type,
    district_number,
    gender,
    legislature,
    CAST('2018-09-01' AS DATE) AS effective_from,
    CAST('9999-12-31' AS DATE) AS effective_to,
    TRUE AS is_current,
    _hash
FROM hashed;

-- fact_vote: Individual votes joined with legislator dimension
CREATE OR REPLACE TABLE analytics.fact_vote AS
SELECT
    ROW_NUMBER() OVER (ORDER BY v.legislature, v.vote_date, v.vote_id, v.legislator_name) AS vote_key,
    CAST(REPLACE(CAST(v.vote_date AS VARCHAR), '-', '') AS INT) AS date_key,
    l.legislator_key,
    v.legislature,
    v.vote_id AS vote_event_id,
    v.vote_cast,
    (v.vote_cast = 'FOR') AS is_affirmative,
    (v.vote_cast != 'ABSENT') AS is_present
FROM staging.stg_votes v
LEFT JOIN analytics.dim_legislator l
    ON v.legislator_name = l.full_name
    AND v.legislature = l.legislature
    AND l.is_current = TRUE;
