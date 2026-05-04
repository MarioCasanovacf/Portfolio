# ADR 002: Star Schema over Snowflake Schema for Dimensional Model

**Status:** Accepted
**Date:** 2026-03-24
**Context:** Diseño del modelo dimensional para el warehouse legislativo.

## Opciones Evaluadas

### Star Schema
- Dimensiones completamente desnormalizadas.
- Queries simples con JOINs directos fact → dimension.
- Redundancia de datos en dimensiones (e.g., party_name repetido en cada row de dim_legislator).

### Snowflake Schema
- Dimensiones normalizadas (e.g., dim_party separada de dim_legislator, dim_state separada).
- Menor redundancia de almacenamiento.
- Queries más complejas con múltiples JOINs entre dimensiones.

### Wide Denormalized Tables (One Big Table)
- Todo en una tabla plana.
- Máxima simplicidad de queries.
- Imposible mantener historicidad (SCD) sin duplicación masiva.

## Decisión

**Star Schema** con SCD Type 2 en dim_legislator.

## Justificación

1. **Cardinalidad baja:** México tiene ~500 diputados y ~128 senadores por legislatura, y ~8 partidos relevantes. La redundancia de un star schema es despreciable (~KB).

2. **Query simplicity:** Los consumidores (PowerBI, Streamlit) generan queries simples. Un JOIN fact_vote → dim_legislator → dim_date cubre el 90% de los análisis.

3. **SCD requirement:** Los cambios de bancada (party switches) son políticamente significativos. Un legislador que cambia de PRI a MORENA mid-legislatura debe tener dos records en dim_legislator con date ranges. Star schema + SCD2 maneja esto limpiamente.

4. **Tool compatibility:** PowerBI y dbt trabajan naturalmente con star schemas. Los relationships en PowerBI model view mapean 1:1 a fact-dimension JOINs.

## Consecuencias

- dim_party existe como tabla separada (no normalización snowflake, sino referencia con seed data).
- dim_legislator incluye campos de SCD2: effective_from, effective_to, is_current, _hash.
- fact_vote usa legislator_key (surrogate) para el JOIN, garantizando que cada voto se atribuya al party correcto en ese momento.
