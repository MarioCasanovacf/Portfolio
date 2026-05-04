# PLAN.md — quantitative_finance elevation

Status of upgrade to [PRODUCTION_TEMPLATE.md](../PRODUCTION_TEMPLATE.md).

## Snapshot — 2026-04-20

| Section | Coverage |
|---|---|
| Estructura | 4/4 ✅ |
| Pipeline | 3/6 (data layer done; warehouse + retry pendientes hasta integrar fetcher real) |
| Testing | 5/6 ✅ (falta property-based con `hypothesis`) |
| CI/Quality | 6/6 ✅ |
| Docs & DX | 8/8 ✅ |
| **Total** | **~26/30 items aplicables** (de 24 del checklist + 6 extras de pipeline) |

## Done in v0.1.0

- ✅ `pyproject.toml` (setuptools, src layout, optional groups `dev`/`notebooks`)
- ✅ Pydantic Settings (`QFINANCE_*` env prefix)
- ✅ CLI `qfinance generate-data [--lob|--assets|--all]`
- ✅ structlog logging
- ✅ `data/generator.py` refactor — fully deterministic via `np.random.default_rng`
- ✅ Tests: `conftest.py` + 14 unit/integration tests + CLI smoke tests + 75% threshold
- ✅ CI: lint, test (matrix py3.11/3.12/3.13), security (bandit + pip-audit)
- ✅ Pre-commit: ruff, mypy, bandit, gitleaks, nbstripout
- ✅ Dependabot weekly
- ✅ README with Mermaid + Quick Start
- ✅ CONTRIBUTING, CHANGELOG, LICENSE, CLAUDE.md
- ✅ docs/architecture.md + 2 ADRs

## Pending — backlog

Ordered by impact-to-effort ratio.

### Soon (next 1-2 sessions)
1. **Promote `notebooks/03_Hierarchical_Risk_Parity.ipynb`** → `src/quantitative_finance/models/hrp.py`
   - Use `/promote-notebook` skill.
   - Add walk-forward validation test.
   - Compare Sharpe vs equal-weight baseline.
2. **Promote `notebooks/02_Exotic_Options_Heston.ipynb`** → `src/quantitative_finance/models/heston.py`
   - Convergence test (compare N=10k vs N=50k Monte Carlo paths, diff < 0.5%).
3. **Promote `notebooks/01_LOB_Reconstruction.ipynb`** → `src/quantitative_finance/models/lob_microstructure.py`
   - Async LOB processor + spread/imbalance metrics.

### Medium term
4. **HTML report renderer** (`reports/html_report.py`) — Plotly + Jinja2 templates;
   one section per workload; CLI `qfinance report --out report.html`.
5. **DuckDB warehouse layer** (`warehouse/duckdb_client.py`) — 3-layer schema
   (raw / staging / processed) per template section 2.
6. **Property-based tests** with `hypothesis` for invariants
   (covariance PSD, prices > 0, spreads positive).

### Long term (when integrating real data)
7. **`yfinance` fetcher** with `tenacity` retry + `requests-cache` for HRP on
   real tickers (gated by ADR 003).
8. **Streamlit dashboard** for interactive parameter exploration.
9. **Prefect flow** for end-to-end orchestration if the pipeline grows.

## Decisions deferred

- Warehouse backend choice (DuckDB only vs DuckDB + Snowflake toggle) — defer
  until we have a real-data flow.
- Real-vs-synthetic data — see [ADR 001](docs/adr/001-synthetic-data-strategy.md).

## How to resume

```bash
cd Portfolio
# Verify current state
/validate-template quantitative_finance
# Pick the next item
/promote-notebook quantitative_finance/notebooks/03_Hierarchical_Risk_Parity.ipynb
```
