# Mario Casanova — Analytics Engineering Portfolio

> **"My goal is not just to deliver reports, but to build autonomous analytical systems that allow the GSO to anticipate failures through Pulse telemetry, eliminating dependence on central teams and accelerating strategic decision-making."**

---

## Strategic Context

This portfolio demonstrates applied **Statistical Analytics & Data Sovereignty** for enterprise support operations environments — specifically aligned with the analytical maturity needs of a Global Support Organization (GSO) in a high-growth cloud infrastructure company.

The work here is structured around a four-layer framework of operational efficiency, using **synthetic data modeled after real-world HCI (Hyper-Converged Infrastructure) support operations**, including ticket management, telemetry signals, and SLA compliance.

---

## Documentation

| Document | Audience | Description |
|---|---|---|
| **[TECHNICAL_GUIDE.md](./TECHNICAL_GUIDE.md)** | Engineers, hiring managers | Deep dive: statistical choices, code architecture, "what if you change X" scenarios |
| **[FOR_NON_ENGINEERS.md](./FOR_NON_ENGINEERS.md)** | Everyone | Plain language — the hospital analogy, what each notebook does, why it matters |

---

## Portfolio Architecture: Five Layers of Analytical Maturity

```
Layer 1 — Descriptive Analytics (Hindsight)
    → What is happening in our support operations RIGHT NOW?
    → KPIs: TTR (P50/P90), Backlog Aging, SLA Compliance, NPS

Layer 2 — Diagnostic Analytics (Insight)
    → WHY are anomalies occurring? Where is the signal in the noise?
    → Technique: Seasonal Decomposition + Generalized ESD (3σ thresholds)

Layer 3 — Predictive Analytics (Foresight)
    → What WILL the ticket volume look like in the next 18 months?
    → Technique: ARIMA/SARIMA time series forecasting with Ljung-Box validation

Layer 4 — Prescriptive Analytics (Optimization)
    → WHAT SHOULD WE DO to prevent escalations before they impact NPS?
    → Technique: Logistic Regression / Random Forest escalation risk scoring

Layer 5 — API Integration (Production-Ready)
    → HOW DOES THIS RUN on real Nutanix data?
    → Nutanix Prism Central v4 REST API + ntnx_vmm_py_client SDK
    → OData filtering, pagination, retry logic, schema mapping
```

---

## Repository Structure

```
├── README.md                    ← You are here
├── TECHNICAL_GUIDE.md           ← Deep technical reference + what-if scenarios
├── FOR_NON_ENGINEERS.md         ← Plain language guide (no jargon)
├── requirements.txt             ← pip install -r requirements.txt
│
├── notebooks/
│   ├── 01_layer1_descriptive_gso_health_monitor.ipynb
│   ├── 02_layer2_diagnostic_anomaly_detection.ipynb
│   ├── 03_layer3_predictive_ticket_forecasting.ipynb
│   ├── 04_layer4_prescriptive_escalation_risk.ipynb
│   └── 05_nutanix_api_v4_integration.ipynb   ← Live API demo (DEMO/LIVE modes)
│
├── src/
│   └── data_generator.py        ← Synthetic data engine (100k tickets + telemetry)
│
├── data/
│   └── synthetic/               ← Generated datasets (gitignored for size)
│
└── House_Sales_in_King_Count_USA_FinalProject_MarioCasanova.ipynb
    ← IBM Data Science foundation project (regression, pipelines, model evaluation)
```

---

## Technical Stack

| Domain | Tools |
|---|---|
| Data Generation | `Faker`, `NumPy`, `Pandas` |
| Statistical Analysis | `SciPy`, `Statsmodels`, `Pingouin` |
| Machine Learning | `Scikit-learn` (Ridge, Logistic Regression, Random Forest) |
| Time Series | `Statsmodels ARIMA/SARIMA`, `pmdarima` |
| Visualization | `Matplotlib`, `Seaborn`, `Plotly` |
| API Integration | `requests`, Nutanix v4 API (OpenAPI / `ntnx_vmm_py_client`) |

---

## Data Sovereignty Approach

Since access to production data from a live GSO environment requires authorization, this portfolio demonstrates **proactive data sovereignty**: designing and generating realistic synthetic datasets that mirror operational reality, including:

- **100,000 synthetic support tickets** with realistic distributions of TTR, priority, region, product version, and escalation patterns
- **Telemetry signals** (avg_io_latency_usecs, CPU/memory usage, IOPS) linked to ticket spikes
- **VMware-to-AHV migration cohorts** to simulate the real-world demand surge from platform transitions

This approach proves the core value proposition: *"I don't wait for data — I design the scenario to test the model."*

---

## Key Analytical Deliverables

### Layer 1 — GSO Health Monitor Dashboard
- Median TTR and P90 TTR by priority tier and region
- Backlog aging analysis by product version cohort
- SLA compliance tracking (P1: 30min, P2: 2hr, P3: 4hr, P4: 8hr)
- NPS trend correlation with resolution velocity

### Layer 2 — Nutanix Pulse Telemetry Anomaly Detector
- Seasonal decomposition of IO latency (`avg_io_latency_usecs`) time series
- Generalized Extreme Studentized Deviate (GESD) test for dynamic threshold setting
- 3σ residual anomaly flagging linked to ticket creation spikes

### Layer 3 — Workload Forecasting Model
- SARIMA model for 18-month ticket volume prediction
- Ljung-Box test to validate white-noise residuals
- RMSE evaluation for forecast reliability reporting to executive leadership
- VMware migration wave segmentation as exogenous regressor

### Layer 4 — Real-Time Escalation Risk Score
- Binary classifier (Logistic Regression + Random Forest ensemble)
- Features: TTR velocity, customer tier, sentiment proxy, product version risk
- Precision/Recall optimization for high-NPS-impact case prevention
- Actionable output: probability score + recommended Resolution Manager intervention

---

## Foundation Project

**[IBM Data Analysis with Python — King County House Sales](./House_Sales_in_King_Count_USA_FinalProject_MarioCasanova.ipynb)**

Demonstrates core modeling competencies:
- Exploratory Data Analysis (EDA) with correlation analysis
- Linear regression, multi-feature regression with sklearn Pipelines
- Polynomial feature transformation
- Ridge regularization and cross-validation
- R² model evaluation and selection

---

## About

**Mario Casanova** | Statistical Analyst & Analytics Engineer

- 4+ years as Financial Analyst (PGIM, SimCorp ecosystem)
- Creator of the SHILD Method (value protection framework)
- LinkedIn: [mario-casanova](https://www.linkedin.com/in/mario-casanova/)

*Applying rigorous financial modeling standards to enterprise support operations analytics.*
