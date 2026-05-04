# PRODUCTION_TEMPLATE.md

**Contrato de calidad de producción para los 9 proyectos del portafolio.**
Destilado de una auditoría de 5 ejes sobre `legislative-data-pipeline/` (plantilla de referencia). Este documento es la fuente de verdad — cada proyecto elevado debe cumplirlo o documentar la desviación explícitamente.

---

## 0. Golden Path Checklist

Un proyecto está "en producción" cuando cumple todo esto. Marca lo que ya tengas; el resto se implementa.

**Estructura**
- [ ] `pyproject.toml` único (setuptools, `requires-python = ">=3.11"`) con dependencias + optional-groups (`dev`, `docs`, extensiones propias)
- [ ] Layout `src/` con subpaquetes por dominio (no flat, no monolítico)
- [ ] `src/config.py` con Pydantic Settings y `env_prefix` por proyecto
- [ ] CLI entrypoint en `[project.scripts]` (ej. `qfinance = "quantitative_finance.cli:main"`)

**Pipeline**
- [ ] `data/` con tres zonas: `raw/` (inmutable + timestamp en nombre), `staging/`, `processed/`
- [ ] Logging con `structlog` (`logger.bind(...)` para contexto)
- [ ] Retry con `tenacity` (exponential backoff, excepciones específicas)
- [ ] Secretos solo vía env vars (Pydantic Settings lee `.env` opcional en dev)
- [ ] Idempotencia: surrogate keys determinísticos (MD5 de business keys) + `INSERT OVERWRITE`
- [ ] Metadata columns `_source_file` y `_loaded_at` en tablas raw

**Testing**
- [ ] `tests/` paralelo a `src/`, con `conftest.py` centralizado
- [ ] Fixtures reutilizables (factories para modelos) en `conftest.py`
- [ ] `@pytest.mark.unit` / `@pytest.mark.integration` en todos los tests
- [ ] HTTP mocking con `pytest-httpx` (no `unittest.mock.patch` crudo)
- [ ] Coverage threshold **75% mínimo** en `pyproject.toml` (`--cov-fail-under=75`)
- [ ] Parametrización en casos de borde (Unicode, None, whitespace)

**CI/Quality**
- [ ] `.pre-commit-config.yaml` con: `ruff` (lint + format), `mypy` (strict), `bandit`, `gitleaks`
- [ ] `.github/workflows/ci.yml` con jobs: `lint`, `test`, `security`
- [ ] Matrix Python `3.11` + `3.12` + `3.13`
- [ ] `pip-audit` como step en CI
- [ ] `.github/dependabot.yml` para auto-update semanal
- [ ] `permissions: contents: read` en todos los workflows

**Docs & DX**
- [ ] `README.md` con: problema resuelto, stack como tabla, diagrama Mermaid, Quick Start (≤10 líneas bash), estructura de carpetas
- [ ] `CONTRIBUTING.md` (estilo, tests, commit convention, ADR process)
- [ ] `LICENSE` como archivo real (no solo mencionado en `pyproject.toml`)
- [ ] `CHANGELOG.md` versionado (Keep a Changelog)
- [ ] `docs/adr/` con ≥1 ADR justificando decisiones técnicas clave
- [ ] `CLAUDE.md` con contexto para agentes (overview, archivos clave, triggers)
- [ ] Docstrings Google-style, ≥85% cobertura en públicos
- [ ] Type hints 100% (`disallow_untyped_defs = true`)

---

## 1. Estructura

```
<project>/
├── src/<project>/          # src layout — subpaquetes por dominio
│   ├── __init__.py
│   ├── config.py           # Pydantic Settings, env_prefix
│   ├── cli.py              # entrypoint del [project.scripts]
│   ├── <dominio_1>/        # ej. capture/, models/, loaders/
│   └── <dominio_2>/
├── tests/
│   ├── conftest.py         # fixtures centralizadas
│   ├── unit/
│   └── integration/
├── sql/                    # si aplica — DDL + queries en 3 capas
│   ├── ddl/
│   └── queries/
├── flows/                  # si aplica — Prefect/Airflow
├── docs/
│   ├── architecture.md
│   └── adr/                # Architecture Decision Records
├── .github/
│   ├── workflows/ci.yml
│   └── dependabot.yml
├── data/
│   ├── raw/                # inmutable, timestamped filenames
│   ├── staging/
│   └── processed/
├── .pre-commit-config.yaml
├── .gitignore
├── pyproject.toml
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
└── CLAUDE.md
```

**Decisiones explícitas (con justificación):**

| Decisión | Por qué |
|---|---|
| `setuptools` + `pyproject.toml` | Estándar PyPA, más compatible que poetry/uv para portafolio público |
| `src/` layout | Evita imports ambiguos, fuerza instalación editable |
| `pydantic-settings` con `env_prefix` por proyecto | Separa secrets por dominio (`QFINANCE_*`, `CLOUD_*`) |
| CLI en `[project.scripts]` | Un entrypoint oficial, no scripts sueltos |
| Sin `requirements.txt` | Todo en `pyproject.toml` + `optional-dependencies` |

---

## 2. Pipeline (cuando aplique)

Proyectos tipo `capture`, `quantitative_finance`, `cloud_infrastructure_support`, `subscription_economics` tienen pipeline real. Proyectos tipo `continental_philosophy`, `computational_physics` pueden tener pipeline reducido (datos sintéticos → modelo → reporte).

**Stack canónico:**

| Capa | Librería | Uso |
|---|---|---|
| HTTP | `httpx` | Cliente sync/async con timeouts |
| Retry | `tenacity` | `@retry(stop_after_attempt(3), wait_exponential(multiplier=2, min=1, max=30))` |
| Rate limiting | `time.sleep(delay)` configurable | Simple y suficiente |
| Logging | `structlog` | `logger.bind(context=value)` |
| Config | `pydantic-settings` | Settings jerárquicos + env vars |
| Warehouse local | `duckdb` | Dev rápido, sin infra |
| Warehouse prod | Snowflake/Postgres | Toggleable vía `WAREHOUSE_BACKEND` |
| Models | `pydantic` v2 | Data contracts con `@field_validator` |
| Orquestación | `prefect` v3 | `@task(cache_key_fn=task_input_hash)` |

**SQL en 3 capas:**

```
raw/         Mirror fiel + columnas _source_file, _loaded_at
staging/     Dedup (ROW_NUMBER OVER ... ORDER BY _loaded_at DESC), type casting, surrogate keys (MD5)
analytics/   Star schema — facts + dims + materialized views
```

**Convenciones `data/raw/`:**
- Subcarpeta por fuente: `data/raw/<source>/`
- Nombres con timestamp: `votes_2026-04-16.csv` (no `votes.csv`)
- Inmutables — nunca se sobreescriben

**Gaps identificados en el template que debemos cerrar en los 9 proyectos:**
1. HTTP caching (`requests-cache` o equivalente) para evitar re-fetches
2. Alertas en fallos (Slack webhook o similar)
3. Data quality checks post-load (integridad referencial, distribuciones esperadas)
4. Tests de idempotencia explícitos (correr pipeline 2x = mismo output)

---

## 3. Testing

**Layout mínimo:**
```
tests/
├── conftest.py              # fixtures centralizadas
├── unit/
│   ├── test_models.py
│   └── test_transforms.py
└── integration/
    ├── test_pipeline.py
    └── test_db.py
```

**`conftest.py` debe exportar:**
- Factory fixtures por modelo principal (`@pytest.fixture def <model>_factory()`)
- Fixture de config de test (Settings con valores fijos)
- Fixture de DuckDB in-memory si aplica

**Categorización obligatoria:**
```python
@pytest.mark.unit
def test_model_validation(): ...

@pytest.mark.integration
def test_end_to_end_pipeline(): ...
```
Esto permite `pytest -m unit` (rápido, en pre-commit) vs `pytest -m integration` (lento, solo en CI).

**Configuración en `pyproject.toml`:**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "unit: fast, isolated tests",
    "integration: tests that touch DB, filesystem, or network",
]
addopts = "--cov=src --cov-report=term-missing --cov-fail-under=75"
```

**Anti-patrones prohibidos:**
- `unittest.mock.patch` crudo para HTTP → usar `pytest-httpx`
- Fixtures duplicadas entre archivos → mover a `conftest.py`
- Tests sin `@pytest.mark` → bloqueado en review
- CLI sin tests (0% coverage) → siempre incluir al menos un smoke test

---

## 4. CI/Quality

**Pre-commit hooks (`.pre-commit-config.yaml`):**

| Hook | Versión | Función |
|---|---|---|
| `ruff` | 0.4.4+ | Lint + format (autofix) |
| `ruff-format` | 0.4.4+ | Formato estilo black |
| `mypy` | 1.10.0+ | Type checking strict |
| `bandit` | 1.7+ | Seguridad estática Python |
| `gitleaks` | 8.18+ | Secrets scanning |
| `pre-commit-hooks` | 4.6+ | trailing-whitespace, EOF, YAML |

**Ruff config (`pyproject.toml`):**
```toml
[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "A", "SIM", "TCH", "S"]
```

**Mypy config:**
```toml
[tool.mypy]
python_version = "3.11"
strict = true
disallow_untyped_defs = true
warn_return_any = true
ignore_missing_imports = true
```

**GitHub Actions (`.github/workflows/ci.yml`) — 3 jobs:**

| Job | Matrix | Qué hace |
|---|---|---|
| `lint` | py3.11 | `pre-commit run --all-files` |
| `test` | py3.11, 3.12, 3.13 | `pytest -m unit` + `pytest -m integration` con coverage |
| `security` | py3.11 | `pip-audit` + `bandit -r src/` |

**Permisos mínimos:** `contents: read` en todos los workflows (no escalar sin razón).

**Dependabot (`.github/dependabot.yml`):**
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "monthly"
```

---

## 5. Docs & DX

**README.md — estructura obligatoria:**

```markdown
# <Project Name>

> Una línea: qué problema resuelve (no feature list).

[badges: CI | Coverage | License | Python version]

## ¿Por qué este proyecto?
Contexto del problem-solving. Qué existe antes. Qué agrega este proyecto.

## Stack
| Capa | Tecnología | Por qué |
|---|---|---|
...

## Arquitectura
```mermaid
graph LR
    ...
```

## Quick Start
```bash
git clone <repo-url>
cd <project>
pip install -e ".[dev]"
<project> --help   # CLI funciona
pytest -m unit     # tests pasan
```

## Estructura
```
src/...
```

## ADRs
- [001 — decisión X](docs/adr/001-...)

## Licencia
MIT — ver [LICENSE](LICENSE).
```

**ADR format (`docs/adr/NNN-titulo.md`):**
```markdown
# NNN — <Título>

**Status:** Accepted | Superseded by XXX
**Date:** YYYY-MM-DD

## Context
Problema o fuerza motriz.

## Options considered
1. Opción A — pros/cons
2. Opción B — pros/cons

## Decision
Qué se eligió.

## Consequences
Positivas / negativas / neutrales.
```

**CLAUDE.md obligatorio** — contexto para agentes futuros:
- Overview del proyecto (3 líneas)
- Archivos clave con 1 línea de descripción
- Triggers de skills del portafolio que apliquen
- Limitaciones conocidas

**Docstrings:** Google-style, 100% en APIs públicas. Type hints 100%.

---

## 6. Automatización en el harness

Este repo tiene (o tendrá, pendiente de aprobación):

- **Hooks** en `.claude/settings.json` para lint automático, validación de notebooks, bloqueo de comandos destructivos.
- **Skills custom** en `.claude/commands/`:
  - `/elevate-project <name>` — orquesta el upgrade completo
  - `/validate-template <name>` — gap-analysis vs este template
  - `/scaffold-pipeline <type>` — genera boilerplate según tipo
  - `/promote-notebook <path>` — convierte notebook en módulo `src/` + tests

---

## Apéndice — proyectos del portafolio y su tipo

| Proyecto | Tipo de pipeline | Notas |
|---|---|---|
| `quantitative_finance` | API-ML (precios → modelo → reporte) | **Prioridad 1** |
| `macroeconomic_capture` | Capture (scraper → DuckDB) | Nombre sugiere paralelo con `legislative-data-pipeline` |
| `cloud_infrastructure_support` | Synthetic + ML (logs → anomaly detection) | Ya tiene notebooks descriptivos/predictivos |
| `subscription_economics` | Synthetic + AB testing | Cohortes, churn, A/B |
| `proteins_alphafold_distances` | Research (PDB fetch → análisis) | Comparte patrón con `ramachandran` |
| `proteins_ramachandran_plot` | Research (PDB fetch → análisis) | Agrupar con `alphafold` |
| `computational_physics` | Synthetic (simulación → visualización) | Rutherford + Schrödinger |
| `continental_philosophy` | Synthetic + NLP (corpus → grafo) | Kojève + Hegel |
| `real_estate` | EDA + ML | King County dataset |

Agrupación sugerida para Fase 2 (proyectos con pipeline análogo se hacen juntos con subagentes paralelos):
- **Group A — Research fetchers:** `proteins_alphafold_distances` + `proteins_ramachandran_plot`
- **Group B — Synthetic/ML:** `cloud_infrastructure_support` + `subscription_economics`
- **Group C — Simulación:** `computational_physics` + `continental_philosophy`
- **Solo:** `macroeconomic_capture`, `real_estate`

---

*Última actualización: 2026-04-16. Derivado de auditoría paralela de 5 ejes sobre `legislative-data-pipeline/`.*
