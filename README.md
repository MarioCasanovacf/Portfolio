# Mario Casanova — Code Portfolio

> **"The totality of the real is rational only insofar as it is understood."** — Alexandre Kojève

---

## About This Portfolio

A living collection of self-contained case studies across **data science, data analytics, data engineering, software engineering, mathematical modeling, and applied research**. Every project is independently installable, tested, and reproducible — each one built to solve a concrete problem with whatever tools the domain actually demands.

Case studies span quantitative finance, computational physics, structural biology, macroeconomics, product analytics, philosophy, and more.

---

## Case Studies

### Cloud Infrastructure Support Operations
**`cloud_infrastructure_support/`**

A five-layer analytical maturity framework applied to enterprise technical support operations for hyper-converged infrastructure (HCI). Demonstrates the full spectrum from descriptive dashboards to machine learning-based escalation risk scoring.

| Layer | Notebook | Question Answered |
|---|---|---|
| **1 — Descriptive** | `01_descriptive_health_monitor.ipynb` | What is happening in support operations right now? |
| **2 — Diagnostic** | `02_diagnostic_anomaly_detection.ipynb` | Why are anomalies occurring in infrastructure telemetry? |
| **3 — Predictive** | `03_predictive_ticket_forecasting.ipynb` | How many support tickets should we expect in 18 months? |
| **4 — Prescriptive** | `04_prescriptive_escalation_risk.ipynb` | Which open tickets have the highest risk of escalation? |
| **5 — Integration** | `05_api_integration.ipynb` | How does this connect to a live production API? |

**Key techniques:** Log-normal TTR distributions, STL decomposition, GESD anomaly detection, SARIMA forecasting, Random Forest classification, bootstrap confidence intervals, OData REST API integration.

---

### Real Estate — House Price Prediction
**`real_estate/`**

Regression modeling on the King County (Washington) housing dataset. Demonstrates core machine learning competencies: EDA, feature engineering, polynomial transformations, Ridge regularization, cross-validation, and R² model evaluation.

| Notebook | Techniques |
|---|---|
| `house_sales_king_county.ipynb` | Linear/polynomial regression, sklearn Pipelines, Ridge regularization, cross-validation |

---

### Quantitative Finance
**`quantitative_finance/`**

Focuses on institutional-grade financial mechanics, microstructure, and portfolio optimization simulating ultra-low latency logic.

| Notebook | Focus Area | Techniques |
|---|---|---|
| `01_LOB_Reconstruction.ipynb` | Market Microstructure | Asynchronous processing, Limit Order Book L2 |
| `02_Exotic_Options_Heston.ipynb` | Stochastic Volatility Derivatives | Monte Carlo, Finite Differences, Heston Model |
| `03_Hierarchical_Risk_Parity.ipynb` | Portfolio Optimization | Unsupervised ML (Clustering), Graph Theory |

---

### Macroeconomic Capture
**`macroeconomic_capture/`**

Analyzes the mathematical friction between public policy and private capital formation using a Schumpeterian approach.

| Notebook | Focus Area | Techniques |
|---|---|---|
| `01_Fiscal_Crowding_Out.ipynb` | Government Budget Constraint | Time series analysis, Pearson correlation |
| `02_Zombie_Corporations.ipynb` | Paretian & Schumpeterian Survival | Density-based spatial clustering (DBSCAN) |

---

### Proteins & Molecules
**`proteins_alphafold_distances/`** & **`proteins_ramachandran_plot/`**

Deconstructs structural biology into pure geometric data science, converting 3D atomic coordinates into computable mathematical topology.

| Notebook | Focus Area | Techniques |
|---|---|---|
| `proteins_alphafold_distances ...` | PDB Spatial Density | File parsing, 3D Euclidean distance matrices |
| `proteins_ramachandran_plot ...` | Thermodynamic Topology | Linear algebra vectorization, cross products, dihedral $\phi$ / $\psi$ calculation |

---

### Continental Philosophy
**`continental_philosophy/`**

Translates phenomenological exegesis and historical dialectics into computable graph topology and agent-based game theory.

| Notebook | Focus Area | Techniques |
|---|---|---|
| `01_Dialectical_Knowledge_Graph.ipynb` | Hegelian Aufhebung | Semantic Triplets (NLP), Eigenvector Centrality |
| `02_Kojeve_Evolutionary_Game...` | Kojevian Dialectics | Asymmetric Payoffs, Agent-Based Stochastic Modeling |

---

### Computational Physics
**`computational_physics/`**

Applies deterministic numerical methods and sparse linear algebra to simulate Hamiltonian systems and quantum mechanics.

| Notebook | Focus Area | Techniques |
|---|---|---|
| `01_Rutherford...` | Symplectic Kinematics | Verlet Integrators, Monte Carlo Ensembles, Numba JIT |
| `02_Schrodinger...` | Quantum Tunneling | Crank-Nicolson PDEs, Tridiagonal Sparse Matrices |

---

### Subscription Economics & Product Analytics
**`subscription_economics/`**

Simulates a SaaS/Hardware (IoT) Data Warehouse to analyze unit economics, behavior telemetry, and product optimization.

| Notebook | Focus Area | Techniques |
|---|---|---|
| `01_Cohort_Retention...` | Unit Economics | Cohort Analysis, Hardware Attach Rate, ARPU, LTV Projections |
| `02_Churn_Prediction...` | Behavioral Analytics | Stickiness Ratio (DAU/MAU), Logistic Regression for Churn Propensity |
| `03_AB_Testing...` | Product Optimization | Hypothesis Testing, Z-Tests, A/B Test Inference (Conversion Rates) |

---

### Future Case Studies (Planned)

| Domain | Focus Area |
|---|---|
| **Pharma / Biotech** | Molecular property prediction, clinical trial analysis |

---

## Technical Stack

| Domain | Tools |
|---|---|
| Data generation | `NumPy`, `Pandas`, `Faker` |
| Statistical analysis | `SciPy`, `Statsmodels`, `lifelines` |
| Machine learning | `scikit-learn`, `XGBoost`, `LightGBM` |
| Time series & forecasting | `Statsmodels` (ARIMA/SARIMA), `Prophet` |
| Optimization & graphs | `NetworkX`, `scipy.cluster.hierarchy` |
| Structural biology | `Biopython` (PDB parsing, dihedrals) |
| Storage & I/O | `DuckDB`, `pyarrow`, `Parquet`, CSV |
| Visualization | `Matplotlib`, `Seaborn`, `Plotly` |
| Configuration & logging | `pydantic-settings`, `structlog` |
| Quality & CI | `ruff`, `mypy`, `pytest`, `bandit`, `pre-commit`, GitHub Actions |
| API integration | `httpx`, `requests`, REST APIs (OpenAPI) |

---

## Repository Structure

```
Portfolio/
├── README.md                         ← You are here
├── TECHNICAL_GUIDE.md                ← Deep technical reference
├── FOR_NON_ENGINEERS.md              ← Plain-language guide
│
├── cloud_infrastructure_support/     ← 5-layer analytics on HCI support operations
├── computational_physics/            ← Rutherford Monte Carlo + Schrödinger Crank–Nicolson
├── continental_philosophy/           ← Hegel knowledge graph + Kojève game theory
├── macroeconomic_capture/            ← Fiscal crowding-out + zombie corporations
├── proteins_alphafold_distances/     ← Spatial distances on RCSB PDB structures
├── proteins_ramachandran_plot/       ← Dihedral angles φ / ψ computed from scratch
├── quantitative_finance/             ← LOB microstructure + Heston pricing + HRP allocation
├── real_estate/                      ← King County housing regression
└── subscription_economics/           ← Cohorts + churn + A/B testing
```

Every case study folder follows the same convention:

```
<case_study>/
├── notebooks/        ← Jupyter analyses with rendered outputs
├── src/              ← data generator, fetcher, or production package
├── tests/            ← pytest suite (pytest -m unit | integration)
├── data/             ← inputs and outputs (gitignored where appropriate)
├── pyproject.toml    ← installable package with project-specific deps
├── README.md         ← project-specific quick start and architecture
└── LICENSE
```

## Quick Start

Each case study is independently installable — pick whichever interests you:

```bash
git clone https://github.com/MarioCasanovacf/Portfolio.git
cd Portfolio/<case_study>
pip install -e ".[dev,notebooks]"
jupyter lab notebooks/
pytest -m unit
```

---

## Data Sovereignty Philosophy

Rather than waiting for access to production data, this portfolio demonstrates **proactive data sovereignty**: designing and generating realistic synthetic datasets that mirror operational reality. This proves:

- Deep domain understanding — realistic distributions, seasonal patterns, edge cases
- Ability to work autonomously and deliver value from day one
- Statistical rigor in modeling scenarios before having real data

*"I don't need someone to hand me the data. I design the scenario to test the model."*

---

## About

**Mario Casanova — Mexico City**

I enjoy building things. Most of what's in this repo started as a thing I wanted to understand and then turned into code. Continental philosophy, derivatives, protein geometry, SaaS retention — those aren't the same field, but they hide the same shape: a structure to learn, a method to pick, an output that has to actually work. I'm not trying to specialize in one of them, I'm trying to specialize in getting through any of them.

**Why this portfolio exists**

Two reasons. First, these are problems I genuinely enjoy thinking about — the repo is where I park what I learn so I don't lose it. Second, I'm building toward sharing knowledge and being able to showcase how I can help. If you're hiring or contracting someone to solve a real problem in your data, this is what I look like when I'm working on my own — feel free to call.

**Why I build**

A lot of industries have a "bullshit problem" — people throwing around terms they don't really understand about things they understand even less, mostly to look smart. I don't have time for that. The work in this repo goes in the other direction: pick a hard topic, do the math openly, show the code, ship the plot. I publish only things that I can reproduce. If I can't explain what the model is doing, the model isn't done, yet.

**Stack & details**

- Python, SQL, Power BI, Tableau, C#
- Fluent in Spanish and English
- LinkedIn: [mario-casanova](https://www.linkedin.com/in/mario-casanova/)
