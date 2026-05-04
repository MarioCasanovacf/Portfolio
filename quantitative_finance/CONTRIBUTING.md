# Contributing to quantitative-finance

Thanks for considering a contribution. This project follows the portfolio-wide
[PRODUCTION_TEMPLATE.md](../PRODUCTION_TEMPLATE.md) contract — please skim it first.

## Local setup

```bash
git clone https://github.com/MarioCasanovacf/Portfolio.git
cd Portfolio/quantitative_finance
python -m venv .venv
source .venv/bin/activate    # or .venv/Scripts/activate on Windows
pip install -e ".[dev,notebooks]"
pre-commit install
```

## Code style

- **Formatting + linting**: `ruff check --fix && ruff format` (also enforced via pre-commit).
- **Type checking**: `mypy src/` — `disallow_untyped_defs = true` is on.
- **Imports**: stdlib → third-party → first-party (`quantitative_finance`), enforced by ruff isort.
- **Docstrings**: Google-style, mandatory on all public APIs.

## Tests

- **Layout**: `tests/unit/` and `tests/integration/`, mirroring `src/` structure.
- **Markers**: every test must carry `@pytest.mark.unit` or `@pytest.mark.integration`.
- **Fixtures**: shared fixtures live in `tests/conftest.py`, never duplicated inline.
- **Coverage**: ≥ 75% overall (`--cov-fail-under=75`); critical modules (`models/`, `data/generator.py`) target 100%.

Run locally:

```bash
pytest -m unit              # fast, no I/O
pytest -m integration       # slower, touches filesystem
pytest --cov=src/quantitative_finance --cov-report=term-missing
```

## Commit convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new user-facing capability
- `fix:` bug fix
- `refactor:` internal restructuring with no behavior change
- `test:` adding or fixing tests
- `docs:` documentation only
- `chore:` build, CI, deps

Example: `feat(models): add Heston Asian-option Monte Carlo pricer`

## Architecture decisions

Significant choices (warehouse backend, model selection, API providers) must be
recorded in [docs/adr/](docs/adr/) using the existing template (`Status / Context /
Options / Decision / Consequences`). See [ADR 001](docs/adr/001-synthetic-data-strategy.md)
for an example.

## Pull requests

1. Branch from `main`: `git checkout -b feat/<short-name>`
2. Run `pre-commit run --all-files` and `pytest` before pushing.
3. Open the PR with a description that links the relevant ADR or issue.
4. CI must be green before review.
