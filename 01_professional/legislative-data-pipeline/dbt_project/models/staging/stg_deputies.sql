/*
 * stg_deputies: cleaned legislator roster with real seat-occupancy dates.
 *
 * Source: raw.raw_dipmex_roster (dipMex dipdat{60,61}.csv)
 * Grain: One row per legislator per legislature.
 *
 * dipMex gives a stable `id` (suffix p=propietario / s=suplente), a single
 * `part` (party), `nomregexp` (a name regex for matching), and up to three seat
 * entry/exit intervals as yr/mo/dy columns ('.' = no value). Those in/out dates
 * are kept as descriptive occupancy ATTRIBUTES on dim_legislator (licencias,
 * suplente substitutions) — they proved too imprecise to bound the roll-call, so
 * the dated version history is versioned by legislature term, not by them (ADR 003).
 */

WITH source AS (
    SELECT * FROM {{ source('raw', 'raw_dipmex_roster') }}
),

dedup AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY legislature, id ORDER BY ord) AS _rn
    FROM source
)

SELECT
    MD5(CAST(legislature AS VARCHAR) || '|' || TRIM(id)) AS deputy_sk,
    legislature,
    TRIM(id) AS legislator_id,
    TRIM(nom) AS full_name,
    TRIM(nomregexp) AS name_regex,
    UPPER(TRIM(part)) AS party,
    UPPER(TRIM(edo)) AS state,
    (TRIM(id) LIKE '%s') AS is_suplente,
    -- Up to three real seat-occupancy intervals ('.'-aware date assembly):
    {{ dipmex_date('yrin1', 'moin1', 'dyin1') }}    AS in1_date,
    {{ dipmex_date('yrout1', 'moout1', 'dyout1') }} AS out1_date,
    {{ dipmex_date('yrin2', 'moin2', 'dyin2') }}    AS in2_date,
    {{ dipmex_date('yrout2', 'moout2', 'dyout2') }} AS out2_date,
    {{ dipmex_date('yrin3', 'moin3', 'dyin3') }}    AS in3_date
FROM dedup
WHERE _rn = 1
