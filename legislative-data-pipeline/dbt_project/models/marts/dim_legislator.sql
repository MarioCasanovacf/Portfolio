/*
 * dim_legislator: SCD Type 2 legislator dimension.
 *
 * Tracks party changes (cambios de bancada) over time. In recent Mexican
 * legislatures, several high-profile party switches occurred — accurate
 * party attribution per vote requires temporal tracking.
 *
 * For the initial load, all records are marked as current. Subsequent
 * loads would use a MERGE with change detection on the _hash column.
 */

WITH deputies AS (
    SELECT * FROM {{ ref('stg_deputies') }}
),

hashed AS (
    SELECT
        *,
        MD5(
            COALESCE(party, '') || '|' ||
            COALESCE(state, '') || '|' ||
            COALESCE(district_type, '') || '|' ||
            COALESCE(district_number, '')
        ) AS _hash
    FROM deputies
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
FROM hashed
