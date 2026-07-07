# Architecture

## High-level

```mermaid
flowchart TB
    subgraph user[User Interface]
        CLI[qfinance CLI<br/>argparse]
        NB[Jupyter Notebooks]
    end

    subgraph core[Core Package]
        CFG[config.py<br/>pydantic-settings]
        LOG[utils/logging.py<br/>structlog]
        GEN[data/generator.py<br/>numpy.default_rng]
    end

    subgraph models[Models layer — planned]
        HRP[models/hrp.py]
        HES[models/heston.py]
        LOB[models/lob_microstructure.py]
    end

    subgraph reports[Reports — planned]
        HTML[HTML report<br/>Plotly + Jinja2]
    end

    subgraph storage[Storage]
        CSV[(CSV files<br/>data/)]
        DUCK[(DuckDB<br/>data/qfinance.duckdb)]
    end

    CLI --> CFG
    CLI --> LOG
    CLI --> GEN
    NB --> GEN
    NB -.-> HRP
    NB -.-> HES
    NB -.-> LOB
    GEN --> CSV
    HRP --> HTML
    HES --> HTML
    LOB --> HTML
    CSV -.-> DUCK
```

## Data flow (current state)

1. **Generation** — `qfinance generate-data` invokes `data.generator.generate_all` which:
   - Reads `Settings` (env vars + defaults).
   - Builds two seeded `numpy.random.Generator` instances (offset by 1 to decouple LOB and asset streams).
   - Produces `lob_events_synthetic.csv` and `correlated_assets_synthetic.csv`.
2. **Analysis** — Notebooks load the CSVs, run their respective algorithms, and visualize results inline.

## Data flow (target state)

```mermaid
sequenceDiagram
    participant U as User (CLI)
    participant Cfg as Config
    participant Gen as Generator / Fetcher
    participant Stg as Staging (DuckDB)
    participant Mdl as Model
    participant Rpt as Report
    U->>Cfg: load Settings
    Cfg-->>U: validated config
    U->>Gen: generate / fetch
    Gen->>Stg: write raw + staging tables
    U->>Mdl: train / score
    Mdl->>Stg: load features
    Stg-->>Mdl: feature DataFrame
    Mdl->>Rpt: predictions / weights
    Rpt-->>U: HTML report
```

## Module responsibilities

| Module | Responsibility | Stable API? |
|---|---|---|
| `config` | Single source of truth for tunables. | ✅ |
| `utils.logging` | Process-wide structlog setup. | ✅ |
| `data.generator` | Reproducible synthetic data, pure-function core + I/O wrapper. | ✅ |
| `cli` | Thin orchestration over data & models. | ✅ |
| `models.*` | Algorithmic implementations (HRP, Heston, LOB). | ⏳ planned |
| `reports.*` | HTML + chart rendering. | ⏳ planned |

## Determinism invariant

The generator MUST produce bit-identical output for a given `(random_seed,
lob_n_events, assets_n, assets_n_days, regime windows)` tuple. This is enforced
by `test_lob_deterministic`, `test_assets_deterministic`, and `test_idempotent_runs`.
Any future change touching `data/generator.py` must re-run the test suite and
update fixtures intentionally if the contract is broken.
