/*
 * Generate a deterministic surrogate key from one or more columns.
 *
 * Uses MD5 hash for consistency across DuckDB and Snowflake backends.
 * Null-safe: coalesces null values to empty string before hashing.
 *
 * Usage:
 *   {{ generate_surrogate_key(['legislature', 'vote_id', 'legislator_name']) }}
 */

{% macro generate_surrogate_key(field_list) %}

    MD5(
        {% for field in field_list %}
            COALESCE(CAST({{ field }} AS VARCHAR), '')
            {% if not loop.last %} || '|' || {% endif %}
        {% endfor %}
    )

{% endmacro %}
