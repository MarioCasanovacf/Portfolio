# Technical Reference Guide
## Mario Casanova — Data Science & Analytics Portfolio

> **Audience:** Data engineers, senior analysts, hiring managers with technical background.
> **Purpose:** Explain the architectural decisions, statistical methodology, and "what happens if you change X" scenarios for every component of this portfolio.

---

## Table of Contents

### Cloud Infrastructure Support
1. [System Architecture](#1-system-architecture)
2. [Data Architecture — Synthetic Dataset Design](#2-data-architecture)
3. [Layer 1 — Descriptive Analytics Deep Dive](#3-layer-1-descriptive-analytics)
4. [Layer 2 — Diagnostic Analytics Deep Dive](#4-layer-2-diagnostic-analytics)
5. [Layer 3 — Predictive Analytics Deep Dive](#5-layer-3-predictive-analytics)
6. [Layer 4 — Prescriptive Analytics Deep Dive](#6-layer-4-prescriptive-analytics)
7. [Extension Guide — Moving to Real Data](#7-extension-guide)

### Additional Case Studies
8. [Quantitative Finance](#8-quantitative-finance)
9. [Macroeconomic Capture](#9-macroeconomic-capture)
10. [Proteins & Structural Biology](#10-proteins--structural-biology)
11. [Continental Philosophy](#11-continental-philosophy)
12. [Computational Physics](#12-computational-physics)
13. [Subscription Economics & Product Analytics](#13-subscription-economics--product-analytics)

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA SOVEREIGNTY LAYER                              │
│                                                                              │
│  Each case study owns its data pipeline:                                     │
│  ├── cloud_infrastructure_support/src/data_generator.py                      │
│  │   ├── generate_support_tickets()   → 100,000 rows / 17 columns           │
│  │   ├── generate_pulse_telemetry()   →  54,750 rows /  8 columns           │
│  │   └── generate_migration_cohorts() →      24 rows / 11 columns           │
│  ├── quantitative_finance/src/data_generator.py                              │
│  │   ├── LOB tick events              →  synthetic L2 order book             │
│  │   └── Correlated asset returns     →  multi-asset correlation matrix      │
│  ├── macroeconomic_capture/src/data_generator.py                             │
│  │   ├── Sovereign budget constraint  →  quarterly fiscal series             │
│  │   └── Corporate zombie panel       →  1,000 firms × financial metrics     │
│  ├── continental_philosophy/src/data_generator.py                            │
│  │   ├── Hegelian triplets (NLP)      →  semantic knowledge graph            │
│  │   └── Kojevian agent population    →  1,000 agents × trait vectors        │
│  ├── computational_physics/src/data_generator.py                             │
│  │   ├── Rutherford particle ensemble →  5,000 alpha particles               │
│  │   └── Quantum barrier profile      →  spatial potential grid              │
│  ├── subscription_economics/src/data_generator.py                            │
│  │   ├── Hardware users + subs        →  SaaS/IoT data warehouse             │
│  │   └── Telemetry logs               →  daily app usage events              │
│  └── proteins_*/src/data_fetcher.py                                          │
│      └── RCSB PDB coordinate fetch    →  atomic 3D coordinates               │
└──────────────────────────┬──────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ CLOUD INFRA   │  │ QUANT FINANCE │  │ MACRO CAPTURE │
│ SUPPORT (5)   │  │           (3) │  │           (2) │
│ Descriptive   │  │ LOB Recon     │  │ Fiscal        │
│ Diagnostic    │  │ Heston MC     │  │ Crowding-Out  │
│ Predictive    │  │ HRP Portfolio │  │ Zombie Corps  │
│ Prescriptive  │  └───────────────┘  └───────────────┘
│ API Integr.   │
└───────────────┘  ┌───────────────┐  ┌───────────────┐
                   │ PROTEINS (2)  │  │ PHILOSOPHY (2)│
┌───────────────┐  │ AlphaFold     │  │ Dialectical   │
│ COMP PHYSICS  │  │ Distance Map  │  │ Knowledge     │
│           (2) │  │ Ramachandran  │  │ Graph         │
│ Rutherford    │  │ Dihedral Plot │  │ Kojève Game   │
│ Schrödinger   │  └───────────────┘  │ Theory        │
└───────────────┘                     └───────────────┘
                   ┌───────────────┐
                   │ SUBSCRIPTION  │  ┌───────────────┐
                   │ ECONOMICS (3) │  │ REAL ESTATE   │
                   │ Cohort LTV    │  │           (1) │
                   │ Churn Pred.   │  │ King County   │
                   │ A/B Testing   │  │ Regression    │
                   └───────────────┘  └───────────────┘
```

**Key design decision:** All notebooks are independent. Each case study is self-contained with its own `src/data_generator.py` (or `data_fetcher.py`). Running the generator first is the only prerequisite per case study.

---

## 2. Data Architecture

### 2.1 Support Tickets (`support_tickets.csv`)

| Column | Type | Distribution / Logic |
|---|---|---|
| `ticket_id` | str | Sequential `TKT-0000001` → `TKT-0100000` |
| `created_at` | datetime | Uniform random between 2022-01-01 and 2024-12-31 |
| `ttr_hours` | float | **Log-normal** per priority (see below) |
| `priority` | str | Multinomial: P1=8%, P2=22%, P3=45%, P4=25% |
| `region` | str | Uniform across 7 global regions |
| `customer_tier` | str | Uniform: Enterprise, Mid-Market, SMB, Strategic |
| `aos_version` | str | Uniform across 10 infrastructure OS versions |
| `migration_type` | str | VMware-to-native=28%, OS-Upgrade=22%, Greenfield=18%, None=20%, HW-Refresh=12% |
| `escalated` | bool | Probability engine (see escalation logic below) |
| `sla_breached` | bool | `ttr_hours > SLA_HOURS[priority]` |
| `nps_score` | int/null | Inversely correlated with TTR breach ratio; 15% null (no-response) |

**TTR log-normal parameterization:**

```
P1: μ=log(3.5),  σ=2.1/3.5=0.60  → median≈3.5h,  P90≈8.5h
P2: μ=log(12.0), σ=8.5/12.0=0.71 → median≈12h,   P90≈30h
P3: μ=log(36.0), σ=24.0/36.0=0.67→ median≈36h,   P90≈90h
P4: μ=log(96.0), σ=48.0/96.0=0.50→ median≈96h,   P90≈210h
```

Why log-normal and not normal?
TTR is bounded at zero and exhibits a heavy right tail — a few very difficult cases take much longer than the median. The log-normal distribution captures this empirical reality of support ticket data.

**Escalation probability engine:**
```python
base_prob = 0.03                        # baseline: 3%
if priority == 'P1' and sla_breached:
    base_prob = 0.22                    # P1 breach: 22% escalation risk
elif priority == 'P2' and sla_breached:
    base_prob = 0.12                    # P2 breach: 12%
if customer_tier == 'Strategic':
    base_prob *= 1.8                    # Strategic accounts: elevated pressure
```

**What happens if you change this:**
- `PRIORITY_WEIGHTS = [0.12, 0.28, 0.40, 0.20]` — increases P1/P2 volume → Layer 4 classifier sees more positive class examples → AUC-ROC improves slightly, but escalation rate in the data increases, which the staffing recommendation in Layer 3 would need to account for
- Increasing `sigma` in the log-normal → wider TTR distribution → more SLA breaches → NPS drops → Layer 1 NPS trend shows a downward slope

### 2.2 Infrastructure Telemetry (`pulse_telemetry.csv`)

| Column | Type | Description |
|---|---|---|
| `timestamp` | datetime | Daily grain; 50 clusters × 1,095 days = 54,750 rows |
| `avg_io_latency_usecs` | float | Healthy: 200–800µs. Anomaly days: 3×–8× normal |
| `cpu_usage_pct` | float | Baseline 25–60%, weekday factor applied |
| `memory_usage_pct` | float | Baseline 40–75%, independent of weekday |
| `iops` | float | Baseline 5,000–25,000; anomaly days 1.8×–3.5× |
| `anomaly_injected` | bool | 5% of days per cluster are injected anomalies |

**Why 50 clusters, not 500?**
At daily grain, 500 clusters × 3 years = 547,500 rows. This is manageable, but for portfolio purposes 50 clusters with 54,750 rows is sufficient to demonstrate the methodology without excessive memory consumption. In production, you would stream or partition by cluster.

**Weekday factor:** `weekday_factor = 1.0 if ts.weekday() < 5 else 0.72`
This introduces the 7-day seasonality that `seasonal_decompose(period=7)` in Layer 2 is designed to capture. If you remove this factor, the seasonal component of the decomposition becomes flat and the residual absorbs more variance, potentially producing false positive anomalies.

### 2.3 Migration Cohorts (`migration_cohorts.csv`)

24 migration waves, each representing a batch of clusters migrating from a legacy hypervisor to a native platform. Duration ranges from 45 to 180 days. Used in Layer 1 for impact analysis and as context for Layer 3 forecasting.

---

## 3. Layer 1 — Descriptive Analytics

**File:** `cloud_infrastructure_support/notebooks/01_descriptive_health_monitor.ipynb`
**Libraries:** pandas, numpy, scipy.stats, seaborn, matplotlib

### 3.1 TTR P50 / P90 Analysis

**Why P90 and not P95 or P99?**
P90 is the industry standard for SLA reporting in enterprise support. P95/P99 are dominated by outlier cases (hardware failures requiring part shipment, escalations awaiting executive approval) and are not representative of operational performance. P50 alone would hide the tail-risk that executives care about.

**Statistical implementation:**
```python
ttr_stats = df.groupby('priority')['ttr_hours'].agg(
    p50=lambda x: x.quantile(0.50),
    p90=lambda x: x.quantile(0.90),
)
```

**What if you change the percentiles?**
- Switch to P75/P95: captures more of the tail, will show a higher "gap" between actual and SLA — more alarming optics, useful if you want to make the case for more hiring
- Switch to mean instead of median: mean is sensitive to outliers (that one 2,000-hour P3 ticket pulls the average up significantly). Median is more robust and is what any enterprise support org would actually track in their CRM reports

**Log scale on the Y axis:**
Applied because P1 SLA is 0.5 hours and P4 SLA is 8 hours — a 16x range. Linear scale would make P1 bars invisible. Log scale preserves relative proportions across all priority tiers.

### 3.2 SLA Compliance Heatmap

**Statistical construction:**
```python
sla_compliance = df.groupby(['region', 'priority']).apply(
    lambda g: (1 - g['sla_breached'].mean()) * 100
)
```

**What if you add customer tier as a third dimension?**
You would get a 3D structure (region × priority × tier). This is better implemented as a FacetGrid of heatmaps — one heatmap per tier — rather than a single chart. The pattern you would expect: Strategic accounts should have higher compliance because they receive priority routing.

**What if a region shows <60% P1 compliance?**
Action: That region needs either (a) dedicated on-call P1 engineers in that timezone, or (b) a follow-the-sun routing policy that redirects P1s to an active region during off-hours.

### 3.3 Backlog Aging

**Simulation logic:** We treat tickets created in the last 90 days as "open" (since their resolution might not yet be complete in a real scenario). In production, you would filter on `status IN ('open', 'in_progress')` from the CRM API.

**Bucketing strategy:**
```
<4h    → Fresh (within initial response window for P1/P2)
4-24h  → Active (working)
1-3d   → Aging (approaching P3 SLA)
3-7d   → At-risk (approaching P4 SLA)
>7d    → Stale (breach territory)
```

**What if you segment by engineer instead of OS version?**
This reveals engineer-level bottlenecks — which engineers have disproportionate backlog aging. Useful for workforce management but requires careful handling to avoid creating unfair performance optics.

### 3.4 NPS Bootstrap Confidence Intervals

**Why bootstrap instead of normal CI?**
NPS scores (0–10 integers) are not normally distributed — they cluster at extremes (0–2 for detractors, 9–10 for promoters). The normal approximation `μ ± 1.96σ/√n` would produce artificially narrow or wide intervals. Bootstrap resampling (n=500 resamples) gives exact empirical CIs for any distribution.

**What if you increase n_boot from 500 to 5000?**
More stable CI estimates, especially for months with few NPS responses (<50 respondents). The tradeoff is computation time: 500 boots takes ~0.5s per month, 5000 takes ~5s. For a production pipeline running nightly, 1000 is a good balance.

**What if you track NPS by customer tier instead of overall?**
Strategic accounts have the highest NPS impact per point change (they generate the most revenue). A separate `strategic_nps` trend often moves earlier than overall NPS, making it a leading indicator.

---

## 4. Layer 2 — Diagnostic Analytics

**File:** `cloud_infrastructure_support/notebooks/02_diagnostic_anomaly_detection.ipynb`
**Libraries:** statsmodels, scipy, pandas, numpy

### 4.1 STL Seasonal Decomposition

**Model:** Additive decomposition: `Y(t) = Trend(t) + Seasonal(t) + Residual(t)`

**Why additive and not multiplicative?**
Multiplicative decomposition (`Y = T × S × R`) is appropriate when the seasonal amplitude grows proportionally with the trend level — e.g., airline ticket prices where summer peaks get larger as the baseline price grows. For IO latency, anomaly spikes are absolute (a hardware fault adds ~X µs regardless of the baseline trend level), making additive decomposition the correct choice.

**Period=7 (weekly):**
The synthetic data has a weekday factor of 1.0 vs. 0.72 on weekends. This 28% weekday premium creates a clear 7-day periodicity. In real infrastructure telemetry, you would confirm this with a periodogram before assuming weekly seasonality — data centers with 24/7 financial clients may show no weekly pattern.

**What if you change period=7 to period=30 (monthly)?**
The seasonal component would capture monthly billing cycles or maintenance windows instead of the weekly work pattern. The residual would then contain the weekly pattern as "noise," producing many false positive anomalies on Mondays. Always validate your assumed period with a Fourier analysis or ACF plot first.

**What if the decomposition fails with "ValueError: time series has too many missing values"?**
This happens when the daily series has gaps (missing days). Solution: `latency_series.asfreq('D').ffill()` fills forward (as implemented). Alternative: use `interpolate(method='time')` for a smoother gap fill that accounts for time distance.

### 4.2 GESD Anomaly Detection

**Full name:** Generalized Extreme Studentized Deviate test

**How it works, step by step:**
1. Compute mean (μ) and std (σ) of the entire residual series
2. Find the observation with the maximum |z-score|: `z = |x - μ| / σ`
3. Test: is this z-score larger than the critical value λ?
4. If yes → flag it as an anomaly and **remove it from the series**
5. Recompute μ and σ on the reduced series, repeat
6. Stop when no more significant outliers are found (or max_anomalies reached)

**Why the iterative removal?** The "masking effect": if there are multiple outliers, each one inflates σ slightly, making the others look less extreme. By removing confirmed outliers before the next test, we unmask hidden anomalies.

**Critical value formula:**
```python
n = len(working)
t_crit = scipy.stats.t.ppf(1 - alpha / (2 * n), df=n - 2)
lambda_k = (n - 1) * t_crit / sqrt(n * (n - 2 + t_crit**2))
```
At α=0.05 and n=1,000, λ ≈ 4.1σ (stricter than the standard 3σ rule due to Bonferroni-style adjustment for multiple comparisons).

**What if you lower alpha from 0.05 to 0.01?**
More conservative → fewer anomalies flagged → fewer false positives → more false negatives (missed real anomalies). For a support operations context, missing an anomaly is more costly than a false positive (an unnecessary check costs 5 minutes; a missed pre-failure costs a P1 ticket and an NPS hit). Recommendation: keep α=0.05 or even raise to 0.10.

**What if you use a rolling z-score instead of GESD?**
```python
z = (residual - residual.rolling(30).mean()) / residual.rolling(30).std()
anomalies = z.abs() > 3
```
Simpler to implement, but does not handle the masking effect. Will miss clusters of anomalies. GESD is more statistically correct for production alerting.

### 4.3 Cross-Correlation Analysis

**What it measures:** Does a spike in IO latency residual today predict a spike in P1/P2 ticket volume in the next N days?

**Expected result pattern:**
- Lag 0 (same day): moderate positive correlation — anomaly and ticket happen simultaneously
- Lag 1 (next day): typically highest correlation — customers notice the issue and open tickets 12–24 hours after onset
- Lag 2–3: diminishing correlation as the causal signal decays

**What if the correlation at all lags is near zero?**
The synthetic ticket data is generated independently of the telemetry anomaly injection — they share the same cluster IDs but the random seeds don't force co-occurrence. In real data, this correlation should be positive and significant (lag 1–2 days) because telemetry degradation genuinely precedes support tickets. Low correlation in production would mean either: (a) the telemetry signal is not predictive of customer-reported issues, or (b) the customer notification channels (email, phone) introduce noise in the ticket timing.

---

## 5. Layer 3 — Predictive Analytics

**File:** `cloud_infrastructure_support/notebooks/03_predictive_ticket_forecasting.ipynb`
**Libraries:** statsmodels (SARIMAX, adfuller, acorr_ljungbox), sklearn

### 5.1 Stationarity — Augmented Dickey-Fuller Test

**Null hypothesis (H₀):** The series has a unit root → it is non-stationary (has a trend)
**Alternative (H₁):** The series is stationary

**ADF test statistic interpretation:**
```
ADF statistic = -2.3, p = 0.18  → fail to reject H₀ → non-stationary → apply d=1
ADF statistic = -5.1, p = 0.001 → reject H₀ → stationary → d=0
```

**What if the first-differenced series is still non-stationary?**
Apply second differencing (d=2). This is rare for support ticket volumes but can occur if there are structural breaks (e.g., a major product launch that permanently shifts volume to a new level). In that case, consider ARIMAX with a dummy variable for the structural break rather than over-differencing.

### 5.2 ACF / PACF Order Identification

**Reading the plots:**

| Pattern in ACF | Pattern in PACF | Suggested model |
|---|---|---|
| Geometric decay | Spike at lag 1, then cuts off | AR(1) |
| Spike at lag q, cuts off | Geometric decay | MA(q) |
| Geometric decay | Geometric decay | ARMA(p,q) |
| Spike at lag S (seasonal) | Spike at lag S | Add seasonal component |

**SARIMA(1,1,1)(1,0,1)[4] explained:**
```
(p=1, d=1, q=1) → AR(1) + one difference + MA(1) for non-seasonal part
(P=1, D=0, Q=1) → seasonal AR(1) + no seasonal diff + seasonal MA(1)
[S=4]           → 4-week seasonal cycle (monthly pattern)
```

**What if you use `auto_arima` from pmdarima instead of manual order selection?**
```python
from pmdarima import auto_arima
model = auto_arima(train, seasonal=True, m=4, stepwise=True, information_criterion='aic')
```
`auto_arima` conducts a grid search over (p,d,q)(P,D,Q) using AIC as the selection criterion. More robust than manual selection, especially when ACF/PACF patterns are ambiguous. Recommended for production. The manual approach in the notebook demonstrates that you understand what `auto_arima` is doing under the hood.

### 5.3 Ljung-Box White Noise Test

**What it tests:** Whether residuals have any remaining autocorrelation structure.

**Null hypothesis (H₀):** Residuals are white noise (no autocorrelation at any tested lag)
**If H₀ is rejected** (p < 0.05 at any lag): the model missed a systematic pattern → improve the model.

**Lags tested:** [4, 8, 12, 16] — rule of thumb is to test up to `min(10, T/5)` lags where T is the series length. Testing at multiple lags guards against the model fitting well at short lags but failing at longer ones.

**What if Ljung-Box fails at lag 4 (p=0.02)?**
The model has a 4-lag cycle it's not capturing. For a weekly series, this suggests a residual monthly pattern. Solutions:
1. Increase P or Q in the seasonal component: `(1,0,2)[4]` or `(2,0,1)[4]`
2. Add a Fourier term for the monthly cycle using `SARIMAX(exog=fourier_terms)`
3. Switch to a Fourier-based model (Prophet or Holt-Winters with custom seasonality)

### 5.4 RMSE and Forecast Validation

**RMSE formula:** `√(Σ(actual - predicted)² / n)`

**Interpretation:** An RMSE of 8.5 tickets/week means the model's predictions are off by an average of 8.5 tickets per week. If the mean weekly volume is 65 tickets, that's a MAPE of ~13% — generally acceptable for operational planning.

**What if RMSE is very high (>30% of mean)?**
Possible causes:
1. Insufficient training data (need at least 2–3 full seasonal cycles, i.e., 8–12 weeks for a 4-week seasonal model)
2. Structural break in the test period (e.g., a major product release that caused a volume spike)
3. Wrong seasonal period assumed — re-run ACF on the first-differenced series

**Staffing formula used:**
```python
TICKETS_PER_SRE_PER_WEEK = 8   # assumption: 1 engineer handles 8 P1+P2 tickets/week
SREs_needed = ceil(peak_forecast / TICKETS_PER_SRE_PER_WEEK)
```
This constant should be calibrated from historical productivity data (e.g., from CRM time-tracking). If your engineers are senior and handle 12 tickets/week, the staffing recommendation decreases by 33%.

---

## 6. Layer 4 — Prescriptive Analytics

**File:** `cloud_infrastructure_support/notebooks/04_prescriptive_escalation_risk.ipynb`
**Libraries:** sklearn (RandomForest, LogisticRegression, Pipeline), scipy

### 6.1 Feature Engineering Decisions

**`sla_consumption_ratio = ttr_hours / sla_threshold_hours`**
This single feature captures both the raw TTR value and the priority context. A 5-hour resolution time is fine for P3 (ratio=1.25, mild breach) but catastrophic for P1 (ratio=10, severe breach). Without this ratio, the model would struggle to generalize across priorities.

**`eng_esc_rate` (engineer's historical escalation rate)**
This is a "leaky" feature in a strict ML sense — in real-time scoring of a new ticket, you don't yet know whether that ticket will escalate. However, the feature represents the *engineer's historical tendency* (before this ticket), not the outcome of this specific ticket. Using 80-20 train/test split with stratification ensures this is computed on training data and generalized correctly.

**What if you add `customer_sentiment` as a feature?**
In a real support environment, CRM case comments contain text from the customer. Running a pre-trained sentiment classifier (e.g., VADER or a fine-tuned BERT) on those comments and using the sentiment score as a feature would likely be the single most predictive addition. Estimated AUC-ROC improvement: +0.05 to +0.12 based on similar support ticket studies.

### 6.2 Class Imbalance Strategy

**Problem:** Only ~6–8% of tickets escalate. A naive classifier that predicts "never escalate" achieves 92–94% accuracy — but is completely useless.

**Solution used:** `class_weight='balanced'` in sklearn
This internally computes sample weights: `weight_for_class_i = n_samples / (n_classes × n_samples_of_class_i)`
For a 94%/6% split: weight for majority class = 0.53, weight for minority class = 8.33.

**What if you use SMOTE (Synthetic Minority Over-sampling Technique) instead?**
```python
from imblearn.over_sampling import SMOTE
X_res, y_res = SMOTE(random_state=42).fit_resample(X_train, y_train)
```
SMOTE creates synthetic minority class examples by interpolating between existing positive examples. Generally produces slightly higher Recall than `class_weight='balanced'`, at the cost of introducing synthetic noise. For this use case, either approach is valid.

**What if you use `class_weight={0: 1, 1: 15}` (custom weights)?**
This would increase Recall (catch more escalations) at the cost of Precision (more false positives flagged for manager review). If the cost of a missed escalation >> cost of a false positive review, increase the weight on the minority class.

### 6.3 Model Comparison — Why Random Forest Wins

| Criterion | Logistic Regression | Random Forest |
|---|---|---|
| AUC-ROC | ~0.78 | ~0.85 |
| Interpretability | High (coefficients) | Medium (feature importance) |
| Handles non-linearity | No (linear decision boundary) | Yes (tree splits) |
| Handles feature interactions | No (explicitly needed) | Yes (implicit in splits) |
| Training time | <1s | ~30s |
| Production latency | <1ms per prediction | ~5ms per prediction |

**Recommendation:** Use Random Forest as the scoring engine; use Logistic Regression as the "explainability model" when a manager asks "why was this ticket flagged?". The LR coefficients provide a human-readable explanation.

### 6.4 Threshold Optimization

**Default sklearn threshold = 0.50**
This minimizes overall error but is not optimal for imbalanced classes.

**Optimal threshold search:**
We sweep thresholds from 0.20 to 0.85 and select the one maximizing F1 score. F1 is the harmonic mean of Precision and Recall — it penalizes both missing escalations (low Recall) and over-flagging (low Precision).

**What if you optimize for Recall only (minimize missed escalations)?**
Lower the threshold to 0.25–0.30. Recall will approach 0.90+ but Precision drops to 0.15–0.20, meaning 80–85% of flagged tickets are false positives. This is only tolerable if the review is very cheap (automated first-pass) and you have a second-stage human filter.

**What if you want to set a budget of "no more than 5% of tickets flagged"?**
Sort tickets by predicted probability descending. Take the top 5%. The probability threshold at the 95th percentile becomes your operational threshold. This is a "fixed budget" approach, common in operations with fixed headcount.

---

## 7. Extension Guide — Moving to Real Data

### 7.1 Replacing Synthetic Tickets with CRM Data

```python
import simple_salesforce

sf = simple_salesforce.Salesforce(
    username='your_user@company.com',
    password='your_pass',
    security_token='your_token'
)

# SOQL query for Case objects
cases = sf.query_all("""
    SELECT Id, CaseNumber, CreatedDate, ClosedDate, Priority,
           Status, Account.Name, Account.Type, OwnerId,
           IsEscalated, NPS_Score__c, Platform_Version__c
    FROM Case
    WHERE CreatedDate >= 2022-01-01T00:00:00Z
    LIMIT 100000
""")

df = pd.DataFrame(cases['records']).drop('attributes', axis=1)
```

You would then apply the same TTR calculation: `ttr_hours = (ClosedDate - CreatedDate).dt.total_seconds() / 3600`

### 7.2 Replacing Synthetic Telemetry with a Live API

See `cloud_infrastructure_support/notebooks/05_api_integration.ipynb` for the full implementation. The key pattern:

```python
# Generic REST API integration pattern
config = Configuration()
config.host = 'https://management-platform.your-org.com:9440'
config.username = 'api_user'
config.password = 'api_password'

client = ApiClient(configuration=config)
stats_api = StatsApi(api_client=client)

# OData filtering for performance optimization
response = stats_api.list_cluster_stats(
    _filter="startTime ge '2024-12-01T00:00:00Z'",
    _select='clusterId,avgIoLatencyUsecs,cpuUsagePpm,storageUsageBytes',
    _limit=10000
)
```

**OData filtering matters:** Without `_filter`, the API returns all historical data for all clusters, which can be GBs of response payload. Always filter at the API layer, not after loading.

### 7.3 Model Retraining Strategy

For production deployment:

```
Weekly:
  → Pull last 7 days of CRM cases
  → Append to historical dataset
  → Retrain Layer 4 classifier (fast: <2 min)
  → Log new AUC-ROC to MLflow or similar

Monthly:
  → Pull last 30 days of telemetry
  → Refit SARIMA model with extended history
  → Update staffing recommendation report

Quarterly:
  → Full EDA refresh (Layer 1)
  → Review GESD threshold (Layer 2)
  → Validate staffing formula constants against actual hiring data
```

---

## 8. Quantitative Finance

**Directory:** `quantitative_finance/`
**Libraries:** numpy, pandas, matplotlib, seaborn, scipy, asyncio

### 8.1 Limit Order Book Reconstruction

**File:** `quantitative_finance/notebooks/01_LOB_Reconstruction.ipynb`

**What it does:** Reconstructs the state of a Level 2 Limit Order Book (LOB) asynchronously from tick-by-tick market data events. Maintains dual dictionaries (bids/asks) mapping price levels to cumulative size, processing order submissions, cancellations, and executions.

**Key metrics computed:**
- **Mid-price:** `Mid = (Best Ask + Best Bid) / 2`
- **Effective spread:** `Spread = Best Ask - Best Bid` (basis points)
- **OHLC aggregation:** Microsecond-level events resampled to 1-second bars via forward-fill

**Implementation detail — asynchronous processing:**
```python
async def process_event(event, book):
    if event.type == 1:         # submission → add to book
        book[event.side][event.price] += event.size
    elif event.type in (2, 3):  # cancel/execute → remove
        book[event.side][event.price] -= event.size
```
Uses Python's `asyncio` to simulate concurrent event handling with proper event loop yielding — the same pattern used in production ultra-low-latency systems, though real HFT would use C++ or Rust.

**Book consistency validation:** Before recording metrics, the notebook validates `best_bid < best_ask`. A crossed book (bid ≥ ask) indicates a processing error or a momentary arbitrage opportunity that would be immediately consumed.

**What if you change this:**
- Remove the consistency check → crossed book events appear in the spread time series as negative values, producing misleading analytics
- Increase event volume 10× → mid-price shows less volatile tick-to-tick swings (law of large numbers smooths noise)
- Change event type probabilities → non-uniform order flow creates directional bias in mid-price momentum

### 8.2 Exotic Options — Heston Stochastic Volatility

**File:** `quantitative_finance/notebooks/02_Exotic_Options_Heston.ipynb`

**What it does:** Values a discrete arithmetic average Asian Call option via Monte Carlo simulation under the Heston stochastic volatility model. Asian options are path-dependent — payoff depends on the average price over the option's life, not just the terminal price.

**Heston model dynamics:**
```
Asset:    dS = r·S·dt + √v·S·dW_S
Variance: dv = κ(θ - v)·dt + ξ·√v·dW_v    (CIR process)
Correlation: ρ between dW_S and dW_v        (leverage effect)
```

**Euler-Maruyama discretization with correlated Brownian motions:**
```python
Z_v = np.random.normal(0, 1)
Z_s = rho * Z_v + sqrt(1 - rho**2) * np.random.normal(0, 1)
v_next = np.maximum(0, v + kappa*(theta - v)*dt + xi*sqrt(v)*sqrt(dt)*Z_v)
S_next = S * np.exp((r - 0.5*v)*dt + sqrt(v)*sqrt(dt)*Z_s)
```

**Why `np.maximum(0, v)`?** The CIR process can produce negative variance in discrete simulation (the continuous process cannot). The floor at zero is the simplest fix; alternatives include the Milstein scheme or the QE scheme (Andersen 2008) for better accuracy near zero.

**Monte Carlo valuation:** `V = e^{-rT} × E[max(S̄ - K, 0)]` where S̄ is the arithmetic average. Standard error decreases as 1/√N with N paths. At 50,000 paths, SE is typically ±$0.04 on a ~$1.20 option value.

**What if you change this:**
- Increase κ (faster mean reversion) → volatility anchors to θ more quickly → path variance shrinks → option value decreases
- Change ρ from −0.7 to +0.7 → positive leverage effect (vol rises with prices) → right-tail fattening → call option becomes more expensive
- Reduce ξ (lower vol-of-vol) → volatility becomes more predictable → Heston converges toward Black-Scholes behavior
- Increase N from 50k to 500k → SE shrinks by √10 ≈ 3.16× → reveals price estimate precision to 4 decimal places

### 8.3 Hierarchical Risk Parity (HRP)

**File:** `quantitative_finance/notebooks/03_Hierarchical_Risk_Parity.ipynb`

**What it does:** Implements the HRP portfolio construction method (López de Prado, 2016) that avoids the numerical instability of Markowitz mean-variance optimization. Instead of inverting the covariance matrix (ill-conditioned for correlated assets), HRP uses hierarchical clustering to partition assets by correlation topology, then allocates capital recursively.

**Step-by-step algorithm:**

1. **Correlation → Distance transform:** `D_ij = √(0.5(1 - ρ_ij))` — converts correlation matrix to a proper metric space satisfying the triangle inequality

2. **Hierarchical clustering (Ward's method):** Agglomerative algorithm minimizing within-cluster variance. Produces a dendrogram showing asset relationships.

3. **Quasi-diagonalization:** Reorder assets via dendrogram leaf positions so correlated assets sit adjacent — this is what makes recursive bisection work.

4. **Recursive bisection:**
```python
def allocate(cluster, weights):
    if len(cluster) == 1:
        weights[cluster[0]] = 1.0
        return
    left, right = split(cluster)
    var_left  = cluster_variance(left, cov)
    var_right = cluster_variance(right, cov)
    alpha = 1 - var_left / (var_left + var_right)
    allocate(left, weights * alpha)
    allocate(right, weights * (1 - alpha))
```
Capital is allocated inversely proportional to cluster variance — riskier clusters receive less capital.

5. **Inverse Variance Portfolio (IVP) within clusters:** `w_i = (1/σ_i²) / Σ(1/σ_j²)`

**Why HRP over Markowitz?**
Markowitz requires inverting Σ (covariance matrix). For N > 50 correlated assets, Σ is nearly singular — small estimation errors in correlations produce wildly unstable weights. HRP never inverts Σ; it only uses pairwise distances and cluster variances.

**What if you change this:**
- Change Ward → single linkage → clusters become stringy/linear; less balanced allocation across sectors
- Use Spearman instead of Pearson correlations → more robust to outliers; HRP weights shift toward tail-resilient assets
- Swap IVP with equal-weight within clusters → removes size bias; tends to over-weight volatile assets

---

## 9. Macroeconomic Capture

**Directory:** `macroeconomic_capture/`
**Libraries:** numpy, pandas, matplotlib, seaborn, scipy, sklearn

### 9.1 Fiscal Crowding-Out

**File:** `macroeconomic_capture/notebooks/01_Fiscal_Crowding_Out.ipynb`

**What it does:** Quantifies the fiscal crowding-out hypothesis: government deficit spending drives up sovereign bond yields, which increases private sector borrowing costs, thereby reducing private capital formation.

**Government Budget Constraint (GBC):**
```
G_t + r·B_{t-1} = T_t + B_t + ΔM_t

G_t      = Government spending
r·B_{t-1} = Debt service cost (interest on outstanding debt)
T_t      = Tax revenue
B_t      = New debt issuance
ΔM_t     = Monetary expansion (central bank accommodation)
```

**Key computations:**
- **Primary deficit:** `Deficit_t = G_t - T_t` (excludes debt service)
- **Debt service:** `Service_t = B_{t-1} × (r_t / 4)` (quarterly annualization)
- **Total deficit:** Primary deficit + debt service
- **Crowding-out coefficient:** Pearson correlation between 10Y sovereign yield and private capital formation

**What if you change this:**
- Increase primary deficit by 50% → debt accumulates faster → yield curve steepens → crowding-out effect amplified
- Monetary accommodation (ΔM increases) → reduces sovereign yield pressure → private capital formation less crowded out
- Halve the interest rate → debt service costs drop → total deficit shrinks → less treasury issuance needed
- Include corporate tax sensitivity → higher sovereign yields → higher corporate borrowing cost → earnings pressure → reduced capex → negative feedback loop

### 9.2 Zombie Corporations — Schumpeterian Survival Analysis

**File:** `macroeconomic_capture/notebooks/02_Zombie_Corporations.ipynb`

**What it does:** Identifies "zombie corporations" — firms that cannot service debt from operating income (ICR < 1) but persist through government subsidies, preventing Schumpeterian creative destruction. Uses DBSCAN clustering to detect anomalous concentrations of subsidized insolvency.

**Zombie identification metrics:**
- **Interest Coverage Ratio (ICR):** `EBIT / Interest Expense` — ICR < 1 means the firm cannot pay interest from operations
- **Debt-to-Equity:** Leverage ratio indicating financial fragility
- **State Subsidies:** Government transfer value keeping insolvent firms alive

**DBSCAN clustering:**
```python
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

X_scaled = StandardScaler().fit_transform(df[['icr', 'debt_equity', 'subsidies']])
labels = DBSCAN(eps=0.8, min_samples=20).fit_predict(X_scaled)
```

**Why DBSCAN and not K-Means?**
K-Means requires specifying k (number of clusters) and assumes spherical, equal-size clusters. DBSCAN finds arbitrarily shaped clusters and naturally identifies noise points (outliers). Zombie firms are precisely these outliers — they exist in sparse regions of the ICR × leverage × subsidy space where healthy firms don't cluster.

**What if you change this:**
- Increase eps (DBSCAN tolerance) → clusters merge → noise points absorb into productive clusters → zombie detection sensitivity decreases
- Change min_samples from 20 to 5 → smaller clusters detected → more granular sector identification
- Raise ICR threshold from 1.0 to 1.5 → stricter solvency standard → more firms classified as vulnerable
- Add time dimension (multi-period panel) → track zombie persistence probability → show whether subsidies are temporary or permanently sticky

---

## 10. Proteins & Structural Biology

**Directories:** `proteins_alphafold_distances/`, `proteins_ramachandran_plot/`
**Libraries:** numpy, pandas, matplotlib, seaborn, scipy

### 10.1 AlphaFold Spatial Distance Matrix

**File:** `proteins_alphafold_distances/notebooks/01_AlphaFold_Spatial_Distances.ipynb`

**What it does:** Transforms 3D protein atomic coordinates (from PDB files) into a 2D Euclidean distance matrix, revealing topological density and identifying spatially proximal regions that may indicate functional domains or active sites.

**PDB file parsing:**
```python
# Fixed-width format (PDB standard)
# Columns 12:16 = atom name (filter for CA = Alpha Carbon)
# Columns 22:26 = residue number
# Columns 30:38, 38:46, 46:54 = X, Y, Z coordinates (Angstroms)
```

**Why alpha carbons only?**
Each amino acid has ~8–20 atoms. Using all atoms for a 200-residue protein gives a 3,000×3,000 matrix — noisy and dominated by local side-chain distances. Alpha carbons (one per residue) reduce this to 200×200 while preserving the backbone geometry that defines the fold.

**Distance matrix computation:**
```python
from scipy.spatial import distance_matrix
D = distance_matrix(coords, coords)  # N × N symmetric matrix
```
`D_ij = √((x_i - x_j)² + (y_i - y_j)² + (z_i - z_j)²)` — Euclidean distance in Angstroms.

**Reading the heatmap:**
- Main diagonal: always 0 (distance to self)
- Off-diagonal warm bands: long-range spatial contacts (residues far in sequence but close in 3D space) — these indicate secondary/tertiary structure (helices, sheets, disulfide bridges)
- Uniform light color: regions with no spatial proximity → flexible loops or disordered regions

**What if you change this:**
- Include all atoms (not just CA) → matrix becomes denser; high-frequency local noise obscures fold-level signal
- Threshold distances (e.g., only show d < 8Å) → binary contact map reveals hydrogen-bond network directly
- Apply PCA to the distance matrix → top 2 eigenvectors reveal principal folding axes; 2D projection of 3D fold
- Change protein (e.g., from 1UBQ to a multi-chain complex) → inter-chain distances now visible; identifies domain interfaces

### 10.2 Ramachandran Plot — Dihedral Angle Computation

**File:** `proteins_ramachandran_plot/notebooks/01_Ramachandran_Plot_Generator.ipynb`

**What it does:** Computes backbone dihedral angles (φ, ψ) from raw atomic coordinates using vector calculus (cross products, dot products, atan2). The resulting Ramachandran plot reveals sterically allowed conformations and identifies secondary structure.

**Dihedral angle calculation (from-scratch, no library):**
For four consecutive backbone atoms (p0, p1, p2, p3):
```python
b1 = p1 - p0    # bond vector 1
b2 = p2 - p1    # bond vector 2 (rotation axis)
b3 = p3 - p2    # bond vector 3

n1 = cross(b1, b2)       # normal to plane 1
n2 = cross(b2, b3)       # normal to plane 2
m1 = cross(n1, b2/|b2|)  # projection vector

angle = atan2(dot(m1, n2), dot(n1, n2))  # signed angle in [-π, π]
```

**Why atan2 instead of acos?**
`acos(dot(n1, n2))` only gives the unsigned angle [0°, 180°]. `atan2` preserves sign (quadrant information), giving the full [-180°, 180°] range. This is critical — φ = -60° (alpha helix) and φ = +60° (left-handed helix) are biologically very different conformations.

**Angle definitions:**
- **φ (phi):** Dihedral of (C_prev, N, CA, C) — rotation around the N-CA bond
- **ψ (psi):** Dihedral of (N, CA, C, N_next) — rotation around the CA-C bond

**Expected clusters in the Ramachandran plot:**
| Region | φ (approx) | ψ (approx) | Structure |
|---|---|---|---|
| α-helix | -60° | -45° | Right-handed helix |
| β-sheet | -120° | +120° | Extended strand |
| Left-handed helix | +60° | +45° | Rare (Gly only) |

**What if you change this:**
- Analyze a disordered protein → scatter becomes diffuse with no clusters → indicates conformational flexibility
- Separate Proline residues → restricted φ range (-60° only) due to cyclic structure; distinct sub-population
- Apply to MD simulation trajectory → watch clusters shift over time; conformational sampling dynamics
- Use hexbin with linear scale instead of log → dominant clusters (α-helix) overwhelm rare conformations; log scale reveals full distribution

---

## 11. Continental Philosophy

**Directory:** `continental_philosophy/`
**Libraries:** numpy, pandas, networkx, matplotlib, seaborn

### 11.1 Dialectical Knowledge Graph

**File:** `continental_philosophy/notebooks/01_Dialectical_Knowledge_Graph.ipynb`

**What it does:** Operationalizes Hegelian phenomenology by converting philosophical text into a machine-readable knowledge graph. Triplets (Subject-Predicate-Object) create a directed graph where Eigenvector Centrality reveals which concepts absorb the most logical weight as the dialectic progresses toward absolute knowledge.

**Triplet extraction:**
```python
# Philosophical assertions → (Subject, Predicate, Object)
("Being", "transitions_toward", "Nothing")
("Nothing", "aufhebung_toward", "Becoming")
("Becoming", "confluences_in", "Self-knowledge")
```

**Directed graph construction:**
```python
import networkx as nx
G = nx.DiGraph()
for subj, pred, obj in triplets:
    G.add_edge(subj, obj, relation=pred)
```

**Eigenvector centrality — the key metric:**
Solves the eigenvalue problem `Ax = λx` where A is the adjacency matrix. A node's centrality is high if it is pointed to by other high-centrality nodes. This captures the Hegelian intuition that later concepts (Becoming, Spirit) "contain" and "sublate" earlier ones.

```python
centrality = nx.eigenvector_centrality(G, max_iter=1000, tol=1e-6)
```

**Why eigenvector centrality and not degree centrality?**
Degree centrality counts connections equally. Eigenvector centrality weights connections by the importance of the connecting node. In the dialectic, a concept derived from "Spirit" carries more weight than one derived from "Sense-Certainty" — eigenvector centrality captures this hierarchical accumulation.

**Visualization:** Kamada-Kawai force-directed layout. Node size proportional to centrality score (normalized to [0, 100]). Edge arrows show logical flow; color-coded by relation type.

**What if you change this:**
- Use betweenness centrality instead → reveals which concepts are "bridges" between historically disparate stages (information bottlenecks)
- Add bidirectional edges → removes temporal hierarchy; all concepts become equi-weighted; dialectical directionality lost
- Weight aufhebung edges 2× → concepts connected via sublation dominate; pure logical relations deprioritized

### 11.2 Kojève Evolutionary Game Theory

**File:** `continental_philosophy/notebooks/02_Kojeve_Evolutionary_Game_Theory.ipynb`

**What it does:** Operationalizes Alexandre Kojève's historical dialectic as a stochastic agent-based model. 1,000 agents with continuous "Desire for Recognition" vs. "Fear of Death" parameters interact in asymmetric payoff tournaments. The system exhibits phase transitions from neutral plurality → master/slave bifurcation → universal homogeneous state.

**Asymmetric payoff matrix:**
```
                    Agent B advances    Agent B yields
Agent A advances    (Extinct, Extinct)  (Master, Slave)
Agent A yields      (Slave, Master)     (Neutral, Neutral)

Decision rule: Agent advances if Desire > Fear
```

**Struggle resolution and sublation:**
```python
for epoch in range(N_EPOCHS):
    np.random.shuffle(agents)
    for i in range(0, len(agents), 2):
        a, b = agents[i], agents[i+1]
        a_advances = a.desire > a.fear
        b_advances = b.desire > b.fear
        if a_advances and b_advances:
            a.status = b.status = 'Extinct'
        elif a_advances and not b_advances:
            a.status, b.status = 'Extractive', 'Productive'
        # ... symmetric cases
    # Sublation: Master-Slave pairs → Universal Citizens
    # Probability: 30% per epoch per pair
```

**Phase transition dynamics:**
The system exhibits an S-curve: slow initial bifurcation (most agents are Neutral), rapid class formation (Master/Slave pairs multiply), then sublation drives convergence to the Universal State. Once the Universal Citizen threshold is crossed, the reverse transition is negligible — it's an absorbing state, demonstrating the "End of History" thesis computationally.

**What if you change this:**
- Set sublation probability to 0 → Master/Slave classes persist indefinitely; system locks into extractive topology (no historical end)
- Increase sublation probability from 0.3 to 0.7 → system converges to Universal State by epoch 8 (vs. 12–15); history "accelerates"
- Change threshold from `Desire > Fear` to `Desire > 2*Fear` → fewer agents advance; Neutral class dominates; bifurcation delayed
- Add agent learning (adjust Fear/Desire based on outcome history) → system exhibits chaotic dynamics; convergence becomes non-monotonic

---

## 12. Computational Physics

**Directory:** `computational_physics/`
**Libraries:** numpy, pandas, matplotlib, seaborn, scipy, numba

### 12.1 Rutherford Scattering — Velocity-Verlet Integrator

**File:** `computational_physics/notebooks/01_Rutherford_Scattering_Simulation.ipynb`

**What it does:** Simulates alpha particle scattering off a gold nucleus under Coulomb potential using the Velocity-Verlet symplectic integrator. A 5,000-particle ensemble undergoes elastic scattering; the final angle distribution validates the Rutherford scattering formula.

**Coulomb force:**
```
F = k_e × q₁ × Q / r²    (radial, repulsive)
k_e = 1.0 (naturalized units)
Q = 79 (gold nucleus charge)
q₁ = +2 (alpha particle charge)
```

**Velocity-Verlet integration (symplectic):**
```python
@numba.jit(nopython=True)
def step(x, y, vx, vy, dt):
    ax, ay = acceleration(x, y)
    x_new = x + vx*dt + 0.5*ax*dt**2
    y_new = y + vy*dt + 0.5*ay*dt**2
    ax_new, ay_new = acceleration(x_new, y_new)
    vx_new = vx + 0.5*(ax + ax_new)*dt
    vy_new = vy + 0.5*(ay + ay_new)*dt
    return x_new, y_new, vx_new, vy_new
```

**Why Velocity-Verlet and not Euler?**
Euler integration is non-symplectic — it does not preserve the Hamiltonian (total energy). Over thousands of time steps, energy drifts artificially. Verlet preserves phase space volume (Liouville's theorem), keeping the total energy `E = ½m(vx² + vy²) + V(r)` constant to machine precision.

**Singularity handling:** `r² = max(x² + y², 1.0)` — a smoothing floor prevents the force from diverging when particles pass very close to the nucleus. Without this, the integrator would produce NaN or infinite velocities.

**Numba JIT:** `@jit(nopython=True)` compiles the inner loop to machine code, achieving ~100× speedup vs. pure Python. Essential for 5,000 particles × 5,000 time steps = 25 million force evaluations.

**Expected result:** Scattering angle histogram shows a power-law tail at large angles, validating the Rutherford formula: `dσ/dΩ ∝ sin⁻⁴(θ/2)`.

**What if you change this:**
- Increase Q (nucleus charge) from 79 to 200 → stronger Coulomb repulsion → more backscattering → cross section increases ∝ Q²
- Switch to Euler integrator → energy drifts; particles appear to "stick" near nucleus after many orbits
- Remove Numba → same results but 100× slower; impractical for ensemble sizes > 500
- Add magnetic field (Lorentz force) → helical trajectories; breaks azimuthal symmetry

### 12.2 Schrödinger Equation — Crank-Nicolson Method

**File:** `computational_physics/notebooks/02_Schrodinger_Crank_Nicolson.ipynb`

**What it does:** Solves the time-dependent Schrödinger equation numerically to simulate quantum tunneling of a Gaussian wave packet through a potential barrier. Computes the transmission coefficient (fraction of probability amplitude that penetrates the barrier).

**Schrödinger equation (1D, natural units ℏ = 2m = 1):**
```
i ∂Ψ/∂t = (-∂²/∂x² + V(x)) Ψ
```

**Crank-Nicolson scheme (implicit, unconditionally stable):**
```
(I + iΔt/2 · H) Ψⁿ⁺¹ = (I - iΔt/2 · H) Ψⁿ
```

**Why Crank-Nicolson and not explicit Euler?**
Explicit methods for the Schrödinger equation require `Δt < Δx²/2` for stability (CFL condition). Crank-Nicolson is unconditionally stable for any Δt — you can choose Δt for accuracy rather than stability. More importantly, it conserves the norm `∫|Ψ|² dx = 1` exactly, which is physically required (total probability must be 1).

**Tridiagonal matrix structure:**
```python
from scipy.sparse import diags
from scipy.sparse.linalg import splu

# Hamiltonian matrix (tridiagonal)
main_diag = 2/dx**2 + V       # N elements
off_diag  = -1/dx**2 * ones   # N-1 elements
H = diags([off_diag, main_diag, off_diag], [-1, 0, 1], format='csc')

# LU factorize once, solve many times
M_L = splu(I + 0.5j*dt*H)
for step in range(n_steps):
    rhs = (I - 0.5j*dt*H) @ psi
    psi = M_L.solve(rhs)
```

**LU pre-factorization:** The matrix `(I + iΔt/2 · H)` never changes. Factorizing once via `splu()` and reusing the factors for each time step reduces the per-step cost from O(N³) to O(N).

**Initial Gaussian wave packet:**
```
Ψ(x,0) = exp(-(x-x₀)²/(2σ²)) × exp(ik₀x)
```
Gaussian envelope (localized in space) × plane wave (definite momentum k₀). The uncertainty principle guarantees Δx·Δp ≥ ℏ/2 — a narrower packet (smaller σ) has more momentum spread.

**Transmission coefficient:** `T = ∫_{x > barrier} |Ψ_final|² dx` — fraction of probability that tunneled through.

**What if you change this:**
- Increase barrier height (V₀) → transmission drops exponentially; at V₀ = 100, transmission < 1%
- Widen barrier → transmission ∝ e^{-2√(2m(V-E))·L/ℏ}; doubling width roughly halves the log-transmission
- Increase initial momentum k₀ → higher kinetic energy → barrier appears relatively lower → transmission increases strongly
- Decrease σ (sharper packet) → momentum uncertainty increases (uncertainty principle) → some components tunnel, others reflect → richer interference pattern

---

## 13. Subscription Economics & Product Analytics

**Directory:** `subscription_economics/`
**Libraries:** numpy, pandas, matplotlib, seaborn, scipy, sklearn

### 13.1 Cohort Retention and LTV

**File:** `subscription_economics/notebooks/01_Cohort_Retention_and_LTV.ipynb`

**What it does:** Analyzes a hardware-plus-subscription business model (security cameras + cloud storage). Calculates hardware-to-subscription attach rates by cohort, measures churn rates by device type, and projects Lifetime Value (LTV) to optimize marketing spend allocation.

**Key computations:**
- **Attach rate:** `Attach = Total Subscribers / Total Hardware Buyers × 100%`
- **Churn rate:** `Churn = Cancellations / Starts × 100%` (cohort perspective)
- **ARPU:** Average Revenue Per User (monthly fee averaged across subscribers)
- **LTV formula:** `LTV = (ARPU × Margin) / Churn_decimal`

**Why this LTV formula?**
The formula assumes constant churn rate and infinite time horizon. Under these assumptions, a subscriber with churn rate c has expected lifetime 1/c months. Revenue per month is ARPU × Margin. Therefore LTV = ARPU × Margin × (1/c) = ARPU × Margin / c. This is the standard SaaS unit economics formula used by investors and product teams.

**Cohort analysis implementation:**
```python
cohort_pivot = df.pivot_table(
    index='cohort_month', columns='device_type',
    values='attach_rate', aggfunc='mean'
)
```
Rows = acquisition month, columns = device type. Heatmap coloring reveals whether newer cohorts convert better (product/marketing improvement) or worse (market saturation).

**What if you change this:**
- Reduce Doorbell churn from 35% to 25% → LTV jumps from ~$216 to ~$277 (28% improvement); this single metric change shifts the entire marketing budget allocation
- ARPU increases from $8/mo to $12/mo (premium tier) → LTV scales proportionally; allows 50% higher Customer Acquisition Cost (CAC)
- Device-specific margin (cameras: 85%, doorbells: 70%) → cameras become more attractive on LTV basis; budget reallocation away from doorbells

### 13.2 Churn Prediction via Behavioral Telemetry

**File:** `subscription_economics/notebooks/02_Churn_Prediction_Telemetry.ipynb`

**What it does:** Predicts customer churn using app usage telemetry (March 2023 data → June 2023 churn outcome). The key feature is the "Stickiness Ratio" (DAU/MAU proxy), and the model is a logistic regression that produces an interpretable churn probability curve.

**Feature extraction from daily telemetry:**
```python
user_features = telemetry.groupby('user_id').agg(
    days_active=('date', 'nunique'),
    total_app_opens=('event', 'count'),
    avg_minutes=('duration', 'mean')
)
user_features['stickiness'] = user_features['days_active'] / 31 * 100
```

**Stickiness Ratio:** `Days Active / Days in Month × 100%` — percentage of the month the user actively engaged. This is a DAU/MAU proxy at the individual level.

**Logistic regression model:**
```python
LogisticRegression(class_weight='balanced', C=1.0)
# P(Churn=1) = 1 / (1 + exp(-(β₀ + β₁·stickiness + β₂·opens + β₃·minutes)))
```

**Why logistic regression and not XGBoost?**
For this use case, interpretability trumps marginal accuracy. The logistic curve directly shows: "Below 30% stickiness, churn probability exceeds 50%." This is immediately actionable — the product team can set up an automated reactivation campaign triggered at the 30% threshold. XGBoost would likely improve AUC by 5–10% but lose the single-variable interpretability.

**What if you change this:**
- Add recency (days since last app open) → more predictive than stickiness alone; sudden drop triggers immediate alert
- Use XGBoost → captures non-linear interactions; AUC improves by 5–10%; loses the clean sigmoid interpretability
- Reduce stickiness threshold from 30% to 20% → more aggressive reactivation campaigns; higher false positive rate but catches more at-risk users early

### 13.3 A/B Testing — Onboarding Flow Optimization

**File:** `subscription_economics/notebooks/03_AB_Testing_Onboarding.ipynb`

**What it does:** Evaluates whether a redesigned hardware onboarding flow (Variant) improves the subscription conversion rate compared to the Control (classic) flow. Uses a two-proportions z-test to determine statistical significance at α = 0.05.

**Two-proportions z-test:**
```python
# Null hypothesis H₀: p_variant = p_control
# Alternative H₁: p_variant > p_control (one-tailed)

p_pool = (conv_V + conv_C) / (n_V + n_C)
SE = sqrt(p_pool * (1 - p_pool) * (1/n_V + 1/n_C))
Z = (p_hat_V - p_hat_C) / SE
p_value = 1 - scipy.stats.norm.cdf(Z)
```

**Why one-tailed and not two-tailed?**
The business hypothesis is directional: "The new onboarding is better." We don't care if the new onboarding is significantly worse (we'd just not ship it). One-tailed test has more statistical power for the direction we care about (critical value 1.645 vs. 1.96 for two-tailed).

**Confidence intervals:** Wilson score intervals via `statsmodels.stats.proportion.proportion_confint` — more accurate than the Wald interval for proportions near 0 or 1.

**Decision rule:**
- p < 0.05 → Reject H₀ → "Significant improvement — ship the variant"
- p ≥ 0.05 → Fail to reject → "Inconclusive — collect more data or iterate on the design"

**What if you change this:**
- Switch to two-tailed test → harder to reject null (critical value 1.96 vs. 1.645); larger p-value
- Reduce α from 0.05 to 0.01 → requires stronger evidence; protects against false positives in multiple concurrent tests
- Increase sample size 10× → standard error shrinks by √10; if the original difference was marginal, larger n reveals the true effect
- Implement sequential testing (Bayesian) → allows early stopping if effect becomes clear; reduces required sample size

---

*Mario Casanova | Data Science & Analytics Portfolio*
*For non-technical overview: see `FOR_NON_ENGINEERS.md`*
