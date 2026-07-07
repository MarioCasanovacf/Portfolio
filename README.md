# Mario Casanova — Code Portfolio

> **"The totality of the real is rational only insofar as it is understood."** — Alexandre Kojève

---

## Two tracks, on purpose

This repository is split in two, because the work in it does two different jobs.

A portfolio that spreads eleven projects across seven domains asks a reviewer to discount the breadth — amplitude gets read as unfocused, and depth is what actually gets rewarded. So I've separated the work that proves **what I can be hired to do** from the work that shows **how I think**:

| Track | What it's for | What's in it |
|---|---|---|
| **[`01_professional/`](01_professional/)** | A short, deep professional portfolio — transferable, hireable engineering capability | data-engineering pipeline · quantitative finance · operational analytics & ML · product analytics · production NLP (review sentiment) · applied ML (real-estate valuation) |
| **[`02_intellectual/`](02_intellectual/)** | An intellectual testbed tied to my blog — demonstrations of a thesis, where the argument is the point | quantified philosophy · computational physics · structural biology as geometry · macro narratives put to data |

The professional track is intentionally **six projects, not eleven**. The intellectual track's five aren't lesser work — they're a different *kind* of work. A numerically reproduced physical law or a quantified Hegelian dialectic reads as noise in a hiring context but as a brand asset on a blog. Putting each where it belongs is the whole point of the split.

Start with whichever track fits why you're here:

- **Hiring or contracting?** → **[`01_professional/`](01_professional/)**
- **Curious how I reason through a hard idea?** → **[`02_intellectual/`](02_intellectual/)**

---

## Technical stack

| Domain | Tools |
|---|---|
| Data engineering | `DuckDB`, `dbt`, `Prefect`, `httpx` + `BeautifulSoup`, Streamlit |
| Statistical analysis | `SciPy`, `Statsmodels` |
| Machine learning | `scikit-learn` |
| NLP / transformers | `transformers` (XLM-RoBERTa), `PyTorch` |
| Time series & forecasting | `Statsmodels` (ARIMA/SARIMA) |
| Optimization & graphs | `NetworkX`, `scipy.cluster.hierarchy` |
| Numerical methods | `NumPy`, `SciPy` sparse, `Numba` (JIT) |
| Structural biology | `numpy` + stdlib (manual PDB parsing, cross-product dihedrals) |
| Synthetic data | `NumPy`, `Pandas`, `Faker` |
| Visualization | `Matplotlib`, `Seaborn`, `Plotly` |
| Config & logging | `pydantic-settings`, `structlog` |
| Quality & CI | `ruff`, `mypy`, `pytest`, `bandit`, `pre-commit`, GitHub Actions |

---

## Repository structure

```
Portfolio/
├── README.md                       ← you are here
├── portfolio_style.py              ← shared brand rcParams for figures
│
├── 01_professional/                ← short & deep: hireable engineering capability
│   ├── README.md                   ← framing: read each project by its transferable skill
│   ├── legislative-data-pipeline/  ← ELT: scrape → DuckDB → dbt (SCD2) → Streamlit
│   ├── quantitative_finance/       ← LOB microstructure + Heston pricing + HRP
│   ├── cloud_infrastructure_support/ ← 5-layer analytics + live API integration
│   ├── subscription_economics/     ← cohorts + churn + A/B testing
│   ├── review_sentiment_ml/        ← two XLM-R sentiment cascades + the labeling method under them
│   └── real_estate/                ← real King County valuation: does location's lift survive a new ZIP code?
│
├── 02_intellectual/                ← hypothesis experiments tied to the blog
│   ├── README.md                   ← framing: each project as a thesis made computable
│   ├── continental_philosophy/     ← Hegel knowledge graph + Kojève game theory
│   ├── computational_physics/      ← Rutherford Monte Carlo + Schrödinger Crank–Nicolson
│   ├── proteins_ramachandran_plot/ ← dihedral φ/ψ angles computed from scratch
│   ├── proteins_alphafold_distances/ ← Cα–Cα distance matrices from PDB structures
│   └── macroeconomic_capture/      ← fiscal crowding-out + zombie corporations
│
└── _pendiente_decision/            ← parked, un-placed (currently empty)
```

Each project folder is independently installable and follows the same convention — `notebooks/`, `src/`, `tests/`, `pyproject.toml`, a project `README.md` — with two exceptions: `legislative-data-pipeline/` (a production pipeline with `flows/`, `dbt_project/`, and a `dashboard/` instead of notebooks) and `review_sentiment_ml/` (two sibling sub-projects whose scripts are reference implementations of work done on proprietary data — readable, not runnable; see its README for the honest boundary).

```bash
git clone https://github.com/MarioCasanovacf/Portfolio.git
cd Portfolio/01_professional/<project>      # or 02_intellectual/<project>
pip install -e ".[dev,notebooks]"
pytest -m unit
```

---

## On synthetic data

Several case studies run on synthetic datasets I designed to mirror operational reality, rather than waiting for access to production data. That's a deliberate demonstration: realistic distributions, seasonal patterns and edge cases require deep domain understanding, and modeling a scenario before you have the data is its own skill.

*"I don't need someone to hand me the data. I design the scenario to test the model."*

(A few exceptions run the other way. The legislative pipeline runs on **real** Mexican legislative data captured from government sources. The review-sentiment case study was trained on **real** proprietary review data that cannot be redistributed — there the synthetic part is only the 25-row schema samples that ship in its place. And the real-estate valuation study runs on the **real** King County, WA sale-price dataset; the synthetic version it used to run on entirely survives only as a declared benchmark — a positive control with its generating parameters stated next to any number it's compared against, never presented as evidence about the market.)

---

## About

**Mario Casanova — Mexico City**

I enjoy building things. Most of what's in this repo started as a thing I wanted to understand and then turned into code. Continental philosophy, derivatives, protein geometry, SaaS retention — those aren't the same field, but they hide the same shape: a structure to learn, a method to pick, an output that has to actually work. I'm not trying to specialize in one of them, I'm trying to specialize in getting through any of them.

**Why this portfolio exists**

Two reasons. First, these are problems I genuinely enjoy thinking about — the repo is where I park what I learn so I don't lose it. Second, I'm building toward sharing knowledge and being able to showcase how I can help. If you're hiring or contracting someone to solve a real problem in your data, the [professional track](01_professional/) is what I look like when I'm working on my own — feel free to call.

**Why I build**

A lot of industries have a "bullshit problem" — people throwing around terms they don't really understand about things they understand even less, mostly to look smart. I don't have time for that. The work in this repo goes in the other direction: pick a hard topic, do the math openly, show the code, ship the plot. I publish only things that I can reproduce. If I can't explain what the model is doing, the model isn't done, yet.

**Stack & details**

- Python, SQL, Power BI, Tableau, C#
- Fluent in Spanish and English
- LinkedIn: [mario-casanova](https://www.linkedin.com/in/mario-casanova/)
