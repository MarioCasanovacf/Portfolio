/*
 * dipmex_date: assemble a DATE from dipMex's split year/month/day columns.
 *
 * dipMex stores seat entry/exit and vote dates as three string columns and uses
 * '.' (and sometimes '') as the "no value" marker. Returns NULL when the year is
 * absent; pads month/day; casts safely (TRY_CAST) so malformed parts yield NULL
 * rather than failing the build.
 */
{% macro dipmex_date(yr, mo, dy) %}
    TRY_CAST(
        CASE
            WHEN NULLIF(NULLIF(TRIM({{ yr }}), '.'), '') IS NULL THEN NULL
            ELSE NULLIF(NULLIF(TRIM({{ yr }}), '.'), '')
                 || '-' || LPAD(COALESCE(NULLIF(NULLIF(TRIM({{ mo }}), '.'), ''), '1'), 2, '0')
                 || '-' || LPAD(COALESCE(NULLIF(NULLIF(TRIM({{ dy }}), '.'), ''), '1'), 2, '0')
        END AS DATE
    )
{% endmacro %}
