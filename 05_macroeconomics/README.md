# 05 — Macroeconomics & Fiscal Policy Analytics

**Domain:** Macroeconomic modeling, sovereign debt, fiscal analysis
**Status:** In development
**Approach:** Institutional, not descriptive. We model the economy as a mathematical system, not a set of bar charts from government APIs.

---

## Design Philosophy

> Conventional macroeconomic analysis in public repositories degenerates into acritical visualization of government time series. That is not this.
>
> The institutional approach requires modeling macroeconomics and public finance as the mathematical manifestation of institutional capture and rent-seeking. Fiscal narratives must be decomposed into structured, auditable data flows — not taken at face value.

---

## Central Analytical Framework

### Government Budget Constraint (the axiomatic starting point)
```
G_t + r·B_{t-1} = T_t + B_t + ΔM_t
```
Where:
- `G_t` = government expenditure at time t
- `r·B_{t-1}` = interest service on prior debt
- `T_t` = tax revenue
- `B_t` = new debt issuance
- `ΔM_t` = monetary base expansion (seigniorage)

This identity is the auditing framework. Every fiscal policy claim must satisfy this equation. Violations indicate hidden monetization, off-balance-sheet liabilities, or accounting manipulation.

---

## Planned Projects

### Project A — Fiscal Crowding-Out Quantification Engine

**What it does:** Measures the empirical differential between public credit expansion and private gross fixed capital formation, using the government budget constraint as the auditing framework.

**Data pipeline:**
1. **Ingestion (Python async):** Balance of payments, sovereign yield curve components, granular public procurement records
2. **Persistence (Snowflake columnar store):** Normalized time series by country, sector, and maturity
3. **Transformation (SQL):** Calculate `ΔPrivate_Credit = GFCF_t - GFCF_{t-1}` and `ΔPublic_Deficit = (G_t - T_t) - (G_{t-1} - T_{t-1})`
4. **Modeling (Python statsmodels):** Vector Autoregression (VAR) to estimate the Granger-causal relationship between deficit expansion and private investment contraction

**Key output:** The crowding-out coefficient — for every 1% increase in the fiscal deficit as % of GDP, private investment contracts by X%.

**Paretian/Schumpeterian overlay:** Cross-reference deficit distribution with sectoral profitability rates to isolate zombie corporations (firms surviving only via implicit government subsidy) from sectors undergoing genuine creative destruction.

### Project B — Sovereign Yield Curve Decomposition

**What it does:** Decomposes sovereign yield curves into:
- **Real rate component:** Compensation for deferred consumption
- **Inflation premium:** Market expectation of purchasing power erosion
- **Term premium:** Compensation for duration risk and liquidity
- **Credit risk spread:** Default probability × recovery rate

**Technique:** Nelson-Siegel-Svensson parametric curve fitting + Kalman filter for dynamic estimation

**Cross-country comparison:** Yield curve inversions as leading indicators of recession across OECD economies

### Project C — Institutional Quality Index

**What it does:** Operationalizes the theory of extractive institutions (Acemoglu-Robinson) as a quantifiable index built from:
- Public procurement concentration (Herfindahl-Hirschman Index on contract recipients)
- Regulatory capture metrics (revolving door density in key sectors)
- Fiscal opacity score (off-balance-sheet liability disclosure rate)
- Rule-of-law indices (WJP, Transparency International)

**Output layer:** PowerBI DAX dashboard projecting the opportunity cost of capital captured by extractive structures — the counterfactual private investment foregone.

---

## Data Sources

- **Fiscal data:** IMF World Economic Outlook, national treasury APIs, OpenSpending
- **Yield curves:** FRED (Federal Reserve), ECB Statistical Data Warehouse, Banco de México
- **Procurement:** national transparency portals (Mexico's CompraNet, EU TED, USASpending.gov)
- **Institutional quality:** World Bank Governance Indicators, WJP Rule of Law Index

---

## Technology Stack

- **Ingestion:** Python `asyncio` + `aiohttp` for parallel API extraction
- **Storage:** Snowflake (columnar, analytical workloads) or DuckDB (local development)
- **Transformation:** SQL (pure, auditable transformations)
- **Modeling:** `statsmodels` VAR, Nelson-Siegel curve fitting, Kalman filtering
- **Visualization:** PowerBI with DAX measures for executive-facing output

---

*Code being consolidated from existing work. Initial implementation focuses on the crowding-out engine for Mexico and LATAM economies.*
