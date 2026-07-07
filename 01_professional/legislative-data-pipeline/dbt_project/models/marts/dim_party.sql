/*
 * dim_party: Political party reference dimension.
 *
 * Seeded with major Mexican political parties. Could be maintained as a
 * dbt seed instead, but modeled here for consistency with the star schema.
 */

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
) AS t(party_code, party_name, ideology_spectrum, founded_year, is_active)
