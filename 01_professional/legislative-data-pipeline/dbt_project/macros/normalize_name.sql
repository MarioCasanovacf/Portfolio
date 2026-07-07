/*
 * normalize_name: canonical, order-insensitive form of a legislator name.
 *
 * Used to bridge scraped vote names (raw_dipmex_votes.legislator_name) to the
 * stable legislator_id roster (raw_dipmex_deputies.full_name). Steps:
 *   1. strip_accents  -> PÉREZ -> PEREZ
 *   2. upper          -> case-insensitive
 *   3. drop honorifics (DIP., DIPUTADO/A) and punctuation -> spaces
 *   4. collapse whitespace
 *   5. split into tokens, sort them, rejoin -> "PEREZ, JUAN" == "JUAN PEREZ"
 *
 * The sorted-token form makes the match robust to "LAST, FIRST" vs "FIRST LAST"
 * ordering, which differs between the votes feed and the deputies roster.
 */
{% macro normalize_name(col) %}
    array_to_string(
        list_sort(
            string_split_regex(
                trim(regexp_replace(
                    regexp_replace(
                        upper(strip_accents(coalesce({{ col }}, ''))),
                        '\bDIP(UTAD[OA])?\b\.?', ' ', 'g'      -- drop honorifics
                    ),
                    '[^A-Z0-9 ]', ' ', 'g'                      -- punctuation -> space
                )),
                '\s+'                                           -- split on whitespace runs
            )
        ),
        ' '
    )
{% endmacro %}
