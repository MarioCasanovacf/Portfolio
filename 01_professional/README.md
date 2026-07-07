# Professional Portfolio

> Five projects, chosen for depth. Each one is here because it demonstrates a **transferable, hireable engineering capability** — the kind of work I'd do on a team, against real constraints, with tests and CI.

This track is deliberately short. A portfolio that sprawls across ten projects and seven domains asks a reviewer to discount the breadth; depth is what gets rewarded. So the work that proves *what I can be hired to do* lives here, separately from the [intellectual testbed](../02_intellectual/) that shows *how I think*.

Read each entry below by the **capability** it demonstrates, not the domain it happens to sit in.

---

## `legislative-data-pipeline/` — Data Engineering

**Capability: build a production data platform end to end, from a messy public source to a served analytics model.**

A real ELT pipeline (not a notebook study) that captures Mexican Chamber of Deputies roll-call votes, attendance, and committee membership by scraping government HTML, lands them in a DuckDB warehouse, models them with dbt, and serves them through a Streamlit dashboard — orchestrated with Prefect and guarded by CI.

| Stage | Tooling | What it produces |
|---|---|---|
| Capture | `httpx` + `BeautifulSoup` | roll-call votes, attendance, committees from `diputados.gob.mx` (SITL) and dipMex |
| Load | DuckDB | the `legislative.duckdb` warehouse |
| Model | dbt | a star schema: `dim_legislator`, `dim_party`, `fact_vote`, vote summaries |
| Serve | Streamlit + Plotly | an interactive dashboard |

The dimensional model is the engineering centrepiece: a **Slowly Changing Dimension (Type 2)** for legislators backed by an **identity-resolution bridge** (fuzzy-matching scraped names to stable IDs, with manual review of the unresolved) and an **as-of join** so every historical vote is attributed to the party a legislator *actually held on the vote date* — not their current one. Validity ranges are anchored to each legislature, the dimension materializes incrementally via `MERGE`, and singular dbt tests enforce referential integrity (no orphaned votes, no overlapping validity ranges, exactly one current row per legislator).

**Transferable skills:** web scraping of unstructured sources · dimensional modeling (SCD2, as-of joins, stable surrogate keys) · dbt · DuckDB · data-quality testing · pipeline orchestration · dashboarding.

---

## `quantitative_finance/` — Quantitative & Numerical Methods

**Capability: implement institutional-grade financial mechanics correctly, with numerical rigor.**

Three self-contained studies in market microstructure, derivatives pricing, and portfolio construction.

| Notebook | Focus | Methods |
|---|---|---|
| `01_LOB_Reconstruction` | Market microstructure | asynchronous event processing, L2 limit-order-book reconstruction |
| `02_Exotic_Options_Heston` | Stochastic-volatility derivatives | Heston model, Monte Carlo (Euler–Maruyama), Asian options |
| `03_Hierarchical_Risk_Parity` | Portfolio optimization | hierarchical clustering, recursive bisection, out-of-sample vs. Markowitz |

The HRP study is validated where it counts — out-of-sample, against minimum-variance and equal-weight benchmarks — rather than asserted. Configuration is typed (`pydantic-settings`) and runs emit structured logs (`structlog`).

**Transferable skills:** stochastic simulation · numerical methods · unsupervised ML · async Python · typed configuration and structured logging · benchmarking discipline.

---

## `cloud_infrastructure_support/` — Operational Analytics & ML

**Capability: turn raw operational telemetry into decisions, across the full analytical maturity curve, against a live API.**

Five notebooks that climb from *what happened* to *what to do about it* on hyper-converged-infrastructure (HCI) support operations.

| Layer | Question | Method |
|---|---|---|
| Descriptive | What is happening now? | health monitoring, log-normal TTR distributions |
| Diagnostic | Why are anomalies occurring? | **Generalized ESD (Rosner)** per-cluster anomaly detection |
| Predictive | How many tickets in 18 months? | SARIMA forecasting |
| Prescriptive | Which tickets will escalate? | logistic regression vs. random forest, bootstrap CIs |
| Integration | How does this hit production? | OData REST integration against a v4 stats API |

The anomaly detector and the API→schema mapping live in importable, unit-tested modules (`src/anomaly.py`, `src/api_integration.py`) so the notebooks and the test suite exercise the *same* code — the GESD detector is validated against the canonical Rosner/NIST example and against an injected ground-truth label (precision/recall 1.00).

**Transferable skills:** the descriptive→diagnostic→predictive→prescriptive arc · anomaly detection · time-series forecasting · classification with honest validation · REST/OData API integration · single-source-of-truth code that is both demoed and tested.

---

## `subscription_economics/` — Product & Growth Analytics

**Capability: drive product and pricing decisions with unit economics, predictive churn, and controlled experiments.**

A simulated SaaS + IoT-hardware data warehouse, analyzed three ways.

| Notebook | Focus | Methods |
|---|---|---|
| `01_Cohort_Retention_and_LTV` | Unit economics | cohort retention, hardware attach rate, ARPU, LTV projection |
| `02_Churn_Prediction_Telemetry` | Behavioral analytics | DAU/MAU stickiness, logistic regression on telemetry features |
| `03_AB_Testing_Onboarding` | Experimentation | two-proportion Z-test, A/B inference on conversion |

**Transferable skills:** SaaS unit economics · cohort analysis · churn modeling on behavioral signals · A/B testing and statistical inference for product decisions.

---

## `real_estate/` — Applied Machine Learning

**Capability: turn a stock model comparison into a real, falsifiable question, and validate it against every way it could quietly cheat.**

A regression study on the real King County, WA housing market (21,613 sales, 2014–2015, public county records), built around one question with no guaranteed answer: how much predictive lift does modeling location as a non-additive geographic surface buy over a strong additive baseline, and does that lift survive a ZIP code the model has never seen a sale in — or is it mostly memorized neighborhood averages that evaporate on contact with a new area.

| Layer | Method |
|---|---|
| Leak-safe pipeline | imputation and scaling fit inside the CV fold, never before the split |
| Uncertainty | repeated K-fold (mean ± sd), not a single train/test split |
| Spatial honesty | ZIP-code-blocked `GroupKFold`, isolating genuine geographic generalization from memorized ZIP averages |
| Assumption tests, executed | VIF (collinearity), Breusch-Pagan (heteroscedasticity), Moran's I (spatial autocorrelation of residuals — implemented from scratch, `esda`/`libpysal` aren't in the shared venv) |
| Declared benchmark | a synthetic dataset with a known, stated planted spatial signal, used only as a positive control against the real result — never presented as evidence about the market |

The headline finding is a real, falsifiable result rather than a model-comparison cliché: raw coordinates carry a modest but durable geographic signal that survives ZIP-blocking, while ZIP-code target encoding's much larger apparent lift collapses — below the no-location baseline — once the model can no longer average over sales it has already seen in that exact neighborhood.

**Transferable skills:** leak-safe cross-validation design · spatial/grouped CV · executed statistical assumption testing · collinearity diagnosis (VIF) · fold-safe categorical target encoding · permutation importance · honest baselines.

---

## Conventions

Every project here is independently installable and tested:

```bash
cd 01_professional/<project>
pip install -e ".[dev,notebooks]"
pytest -m unit
```

Each ships `src/` (the importable package), `tests/` (a pytest suite), `pyproject.toml`, and a project-specific `README.md`. `legislative-data-pipeline/` is the one structural exception — a production pipeline with `flows/`, `dbt_project/`, and a `dashboard/` instead of `notebooks/`.
