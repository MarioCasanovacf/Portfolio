# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- HTTP report generator (Plotly + Jinja2) for end-to-end pipeline output.
- Promotion of LOB Reconstruction notebook to `models/lob_microstructure.py`.
- Promotion of Heston notebook to `models/heston.py`.
- Promotion of HRP notebook to `models/hrp.py` with property-based tests.
- Walk-forward validation harness for time-series models.

## [0.1.0] - 2026-04-20

### Added
- Production scaffolding: `src/quantitative_finance/` package with subpackages (`data`, `utils`, `models`, planned).
- `pyproject.toml` (setuptools, src layout, deps + optional groups).
- Pydantic Settings configuration in `config.py` with `QFINANCE_` env prefix.
- CLI entrypoint `qfinance` (`generate-data`, `--version`).
- Synthetic data generator refactored into `data.generator` with type hints, docstrings, and structlog logging.
- Tests: `conftest.py` with shared fixtures, unit tests for generator and config, coverage threshold 75%.
- CI: GitHub Actions with `lint`, `test` (Python 3.11/3.12/3.13 matrix), and `security` (bandit + pip-audit) jobs.
- Pre-commit hooks: ruff, mypy, bandit, gitleaks, nbstripout, standard hygiene.
- Dependabot for weekly pip updates.
- Documentation: `README.md` with Mermaid diagram + Quick Start, `CONTRIBUTING.md`, `CLAUDE.md`, `docs/architecture.md`, ADRs.

### Migrated
- `src/data_generator.py` → `src/quantitative_finance/data/generator.py` (refactored, not just moved).
