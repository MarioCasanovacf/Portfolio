# Mario Casanova — Data Science & Analytics Portfolio

> **"I don't wait for data — I design the scenario, build the model, and deliver the insight."**

---

## About This Portfolio

This repository is a living collection of applied **Data Science, Statistical Analytics, and Mathematical Modeling** projects across multiple industries and domains. Each case study demonstrates end-to-end analytical thinking: from synthetic data generation and exploratory analysis to predictive modeling and prescriptive decision support.

The portfolio is organized by **thematic case studies** — each one self-contained, reproducible, and built to answer real business questions with rigorous methodology.

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

### Real Estate — House Price Prediction
**`real_estate/`**

Regression modeling on the King County (Washington) housing dataset. Demonstrates core machine learning competencies: EDA, feature engineering, polynomial transformations, Ridge regularization, cross-validation, and R² model evaluation.

| Notebook | Techniques |
|---|---|
| `house_sales_king_county.ipynb` | Linear/polynomial regression, sklearn Pipelines, Ridge regularization, cross-validation |

### Future Case Studies (Planned)

| Domain | Focus Area |
|---|---|
| **Finance** | Risk modeling, portfolio optimization, time series forecasting |
| **Pharma / Biotech** | Molecular property prediction, clinical trial analysis |
| **Proteins & Molecules** | Structural data analysis, computational chemistry |

---

## Documentation

| Document | Audience | Description |
|---|---|---|
| **[TECHNICAL_GUIDE.md](./TECHNICAL_GUIDE.md)** | Engineers, hiring managers | Statistical methodology, architecture decisions, "what if you change X" scenarios |
| **[FOR_NON_ENGINEERS.md](./FOR_NON_ENGINEERS.md)** | Everyone | Plain-language explanations using analogies — no jargon required |

---

## Technical Stack

| Domain | Tools |
|---|---|
| Data Generation | `Faker`, `NumPy`, `Pandas` |
| Statistical Analysis | `SciPy`, `Statsmodels` |
| Machine Learning | `Scikit-learn` (Ridge, Logistic Regression, Random Forest) |
| Time Series | `Statsmodels ARIMA/SARIMA`, `pmdarima` |
| Visualization | `Matplotlib`, `Seaborn` |
| API Integration | `requests`, REST API (OpenAPI spec) |

---

## Repository Structure

```
├── README.md                         ← You are here
├── TECHNICAL_GUIDE.md                ← Deep technical reference
├── FOR_NON_ENGINEERS.md              ← Plain language guide
├── requirements.txt                  ← pip install -r requirements.txt
│
├── cloud_infrastructure_support/     ← Case study: HCI support operations
│   ├── notebooks/
│   │   ├── 01_descriptive_health_monitor.ipynb
│   │   ├── 02_diagnostic_anomaly_detection.ipynb
│   │   ├── 03_predictive_ticket_forecasting.ipynb
│   │   ├── 04_prescriptive_escalation_risk.ipynb
│   │   └── 05_api_integration.ipynb
│   ├── src/
│   │   └── data_generator.py         ← Synthetic data engine (100K tickets + telemetry)
│   └── data/
│       └── synthetic/                ← Generated datasets (gitignored for size)
│
└── real_estate/                      ← Case study: house price prediction
    └── house_sales_king_county.ipynb
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

**Mario Casanova** | Data Scientist & Analytics Engineer

- 4+ years as Financial Analyst (PGIM, SimCorp ecosystem)
- Creator of the SHILD Method (value protection framework)
- Deep foundation in mathematics, statistics, and applied modeling
- LinkedIn: [mario-casanova](https://www.linkedin.com/in/mario-casanova/)

*Combining mathematical rigor with practical problem-solving across industries.*
