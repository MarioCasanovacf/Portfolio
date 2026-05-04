# Sesión de trabajo — 2 de abril de 2026

## Contexto

Se revisaron dos documentos estratégicos (`portfolio_gap_analysis.md` y `portfolio_preprompt.md`) que diagnosticaban brechas entre las capacidades reales de Mario (Snowflake, ETL, PowerBI, código de producción en SimCorp) y lo que el portafolio mostraba (solo notebooks exploratorios). La conclusión: construir un **pipeline de datos legislativos mexicanos** como pieza central que cerrara las brechas 1-4 de un golpe.

---

## Qué se construyó

Se creó el proyecto **`legislative-data-pipeline/`** desde cero dentro de la carpeta Portfolio. **44 archivos** organizados profesionalmente.

### Estructura final del proyecto

```
legislative-data-pipeline/
├── .github/workflows/ci.yml          ← CI/CD con GitHub Actions
├── .gitignore
├── .pre-commit-config.yaml           ← Hooks: ruff, mypy, trailing whitespace
├── pyproject.toml                     ← Build config (setuptools), deps, tool config
├── README.md                          ← Documentación principal con Mermaid
├── CHANGELOG_SESSION_2026-04-02.md    ← Este archivo
│
├── src/                               ← Código de producción
│   ├── __init__.py
│   ├── config.py                      ← Configuración centralizada (pydantic-settings)
│   │
│   ├── capture/                       ← Módulo de captura de datos
│   │   ├── __init__.py
│   │   ├── base.py                    ← BaseScraper: retries, rate limiting, logging
│   │   ├── cli.py                     ← Entry point: `python -m capture.cli`
│   │   ├── dipmex.py                  ← Client para dipMex (GitHub CSV académico)
│   │   └── diputados.py              ← Scraper HTML para diputados.gob.mx
│   │
│   ├── loaders/                       ← Cargadores al warehouse
│   │   ├── __init__.py
│   │   └── duckdb_loader.py           ← Proxy local de Snowflake con DuckDB
│   │
│   └── models/                        ← Data contracts (Pydantic)
│       ├── __init__.py
│       └── legislative.py             ← Deputy, VoteRecord, VoteSummary, CaptureMetadata
│
├── sql/                               ← SQL puro (showcase de Snowflake)
│   ├── ddl/
│   │   ├── 01_raw_schema.sql          ← Landing zone: tables, stages, file formats, streams
│   │   ├── 02_staging_schema.sql      ← Limpieza: QUALIFY, ROW_NUMBER, surrogate keys
│   │   └── 03_dimensional_models.sql  ← Star schema: dims (SCD2), facts, views analíticas
│   │
│   └── queries/
│       ├── staging_transforms.sql     ← Transforms para DuckDB local
│       ├── analytics_transforms.sql   ← Build dimensional models localmente
│       └── advanced_analytics.sql     ← 6 queries avanzadas (showcase)
│
├── flows/                             ← Orquestación con Prefect
│   ├── __init__.py
│   └── legislative_pipeline.py        ← Flow principal: capture → load → transform → validate
│
├── dbt_project/                       ← Transformaciones dbt
│   ├── dbt_project.yml
│   ├── profiles.yml                   ← DuckDB (dev) + Snowflake (prod)
│   ├── macros/
│   │   └── generate_surrogate_key.sql
│   └── models/
│       ├── staging/
│       │   ├── schema.yml             ← Tests: unique, not_null, accepted_values
│       │   ├── stg_votes.sql
│       │   ├── stg_deputies.sql
│       │   └── stg_vote_summaries.sql
│       └── marts/
│           ├── schema.yml
│           ├── dim_legislator.sql     ← SCD Type 2
│           ├── dim_party.sql          ← Seed data de partidos mexicanos
│           ├── fact_vote.sql          ← Grain: 1 legislador × 1 evento
│           └── fact_vote_summary.sql  ← Grain: 1 evento con totales
│
├── dashboard/                         ← Capa de consumo
│   └── app.py                         ← Streamlit: 3 tabs (Overview, Party, Legislator)
│
├── tests/                             ← Suite de tests (pytest)
│   ├── __init__.py
│   ├── test_models.py                 ← 9 tests: validación Pydantic, normalización
│   ├── test_capture.py                ← 5 tests: BaseScraper, DipMexClient (mocked HTTP)
│   └── test_loaders.py               ← 6 tests: DuckDB loader (schemas, CSV, DataFrame)
│
└── docs/                              ← Documentación técnica
    ├── architecture.md                ← Diagrama Mermaid completo + stack justification
    └── adr/
        ├── 001-orchestrator-choice.md ← Prefect vs Airflow vs Dagster
        └── 002-star-schema-design.md  ← Star vs Snowflake schema
```

---

## Detalle por componente

### 1. Captura de datos (`src/capture/`)

**Problema resuelto:** Los datos legislativos mexicanos no tienen API oficial. Están dispersos en HTML, PDFs, y repos académicos.

**Fuentes identificadas:**

| Fuente | Tipo | Qué tiene |
|---|---|---|
| dipMex (GitHub) | CSV directo | Votaciones nominales de legislaturas LXIV-LXVI |
| diputados.gob.mx | HTML scraping | Resúmenes de votación por sesión |
| INE Datos Abiertos | CSV | Resultados electorales (futuro) |
| SIL (SEGOB) | HTML scraping | Tracker legislativo consolidado (futuro) |

**Qué se implementó:**
- `BaseScraper` — Clase abstracta con:
  - httpx como HTTP client (async-ready, connection pooling)
  - Retries con exponential backoff via tenacity (3 intentos, espera 1-30s)
  - Rate limiting configurable (1 request/segundo por default)
  - Logging estructurado con structlog (JSON en prod, consola en dev)
  - Persistencia de archivos raw con metadata de linaje
- `DipMexClient` — Descarga 6 datasets CSV del repo emagar/dipMex
- `DiputadosScraper` — Parsea tablas HTML de votación con BeautifulSoup + lxml
- `cli.py` — Entry point: `python -m capture.cli dipmex diputados`

### 2. SQL / Snowflake DDL (`sql/ddl/`)

**Problema resuelto:** Cero artefactos SQL en el portafolio, cuando Mario usa Snowflake diariamente.

**Tres capas:**

**01_raw_schema.sql:**
- `CREATE DATABASE LEGISLATIVE_MX` con data retention
- File formats (CSV, JSON) con manejo de nulls
- Internal stages para carga
- 4 raw tables: `raw_dipmex_votes`, `raw_dipmex_deputies`, `raw_diputados_votes`, `raw_ine_election_results`
- Streams para CDC (Change Data Capture) — procesamiento incremental

**02_staging_schema.sql:**
- 3 staged tables con: date casting, deduplicación (QUALIFY + ROW_NUMBER), normalización, surrogate keys (MD5)
- Queries de transformación documentadas como comentarios
- Data quality checks como assertions ejecutables

**03_dimensional_models.sql:**
- **Star Schema** con:
  - `dim_date` — Calendario + metadata de periodos legislativos mexicanos
  - `dim_legislator` — **SCD Type 2** para rastrear cambios de bancada (partido)
  - `dim_party` — Con seed data de los 8 partidos principales + ideología
  - `dim_committee` — Comisiones legislativas
  - `fact_vote` — Votos individuales (grain: 1 legislador × 1 evento)
  - `fact_vote_summary` — Resultados agregados con métricas computadas
- 2 views analíticas:
  - `v_party_cohesion` — Qué tan unificado vota cada partido
  - `v_legislator_attendance` — Tasa de asistencia por legislador
- Task de Snowflake para refresh programado (comentado, demo)

**advanced_analytics.sql — 6 queries showcase:**

| # | Query | Técnica SQL |
|---|---|---|
| Q1 | Party Loyalty Score | PERCENT_RANK, NTILE, DENSE_RANK, self-join |
| Q2 | Voting Streaks | Gap-and-island con ROW_NUMBER difference |
| Q3 | Rolling Approval Rate | Window frames (ROWS BETWEEN), LAG, trend detection |
| Q4 | Cross-Party Alignment Matrix | Self-join + clasificación de relaciones |
| Q5 | Absence Sessionization | LAG + conditional running sum |
| Q6 | Influence Chains | Recursive CTE para graph traversal |

### 3. Orquestación (`flows/`)

**Problema resuelto:** Ningún DAG ni pipeline orquestado en el portafolio.

**Prefect se eligió sobre Airflow** porque:
- Zero infraestructura local (no requiere daemon, PostgreSQL, ni webserver)
- API Pythonic (flows y tasks son funciones decoradas)
- Testing simple con pytest
- Razón documentada en ADR 001

**Flow principal (`legislative_pipeline.py`):**
```
capture_dipmex ──┐
                 ├──→ load_raw_files → staging_transforms → analytics_transforms → validate
capture_diputados┘
```

Cada task tiene: retries, tags, logging con Prefect logger, idempotencia.

### 4. dbt (`dbt_project/`)

**Problema resuelto:** Sin transformaciones reproducibles ni testeables.

- **profiles.yml** con dual target: DuckDB (dev) y Snowflake (prod)
- **3 staging models** — Limpieza, dedup, normalización
- **4 mart models** — Star schema dimensional
- **schema.yml** con tests:
  - `unique` y `not_null` en surrogate keys
  - `accepted_values` en vote_cast: ['FOR', 'AGAINST', 'ABSTAIN', 'ABSENT']
- **Macro** `generate_surrogate_key` — MD5 null-safe reutilizable

### 5. Dashboard (`dashboard/app.py`)

**Problema resuelto:** Sin dashboards ni visualizaciones BI.

Streamlit app con 3 tabs:
1. **Legislative Overview** — KPIs (total votes, approval rate, attendance), scatter plot temporal
2. **Party Analysis** — Distribución de votos por partido, barras de cohesión
3. **Legislator Profiles** — Tabla searchable con attendance rate, affirmative rate, histograma

Conecta directamente a DuckDB. Usa Plotly para interactividad.

### 6. Código de producción (transversal)

**Problema resuelto:** Solo notebooks, sin código que se pudiera deployar.

Qué lo hace "de producción":
- **Type hints** en todo el código (compatible con mypy strict)
- **Pydantic models** como data contracts entre capas
- **Configuración** via environment variables (pydantic-settings)
- **Tests** con pytest: 20 test cases cubriendo models, capture, y loaders
- **CI/CD**: GitHub Actions con ruff lint, ruff format, mypy, pytest+coverage, dbt compile
- **Pre-commit hooks**: ruff, trailing whitespace, YAML validation, large file check
- **Logging estructurado** con structlog (JSON para prod, consola para dev)
- **Error handling** con tenacity retries y graceful degradation

### 7. Documentación

- **README.md** — Mermaid diagram, quick start, stack table, decisiones de diseño
- **architecture.md** — Diagrama completo de flujo, descripción de cada capa, stack justification
- **ADR 001** — Prefect vs Airflow vs Dagster (con pros/contras concretos)
- **ADR 002** — Star Schema vs Snowflake Schema (con justificación dimensional)

---

## Brechas del gap analysis que esto cierra

| Brecha | Status | Cómo |
|---|---|---|
| 1. SQL / Snowflake | ✅ Cerrada | 3 DDL files + 6 advanced queries + dbt models |
| 2. ETL / Orquestación | ✅ Cerrada | Prefect flows + dbt transforms + capture module |
| 3. PowerBI / BI | ⚠️ Parcial | Streamlit dashboard listo; PowerBI requiere .pbix (no generado) |
| 4. Código de producción | ✅ Cerrada | src layout, tests, CI/CD, type hints, Pydantic |
| 5. C# / SimCorp | ❌ Pendiente | Proyecto separado |
| 6. Deep Learning / AI | ❌ Pendiente | Proyecto separado |
| 7. Documentación | ✅ Cerrada | README, ADRs, architecture.md |

---

## Dependencias instaladas

Todas las dependencias se instalaron exitosamente con Python 3.14.3:
- Core: httpx, beautifulsoup4, lxml, duckdb, pandas, pyarrow, prefect, structlog, tenacity, pydantic, pydantic-settings
- Dev: pytest, pytest-cov, pytest-asyncio, ruff, mypy, pre-commit
- Dashboard: streamlit, plotly

**Nota:** Se cambió el build backend de `hatchling` a `setuptools` porque hatchling no era compatible con Python 3.14.

---

## Próximos pasos sugeridos

1. **Correr tests:** `cd legislative-data-pipeline && pytest tests/ -v` (con `PYTHONPATH=src`)
2. **Ejecutar captura real:** `cd src && python -m capture.cli dipmex` (descarga ~6 CSVs de GitHub)
3. **Lanzar dashboard:** `streamlit run dashboard/app.py`
4. **Siguiente proyecto:** SQL Showcase standalone o AI/ML Engineering
5. **PowerBI:** Crear .pbix conectando a DuckDB (requiere PowerBI Desktop)
