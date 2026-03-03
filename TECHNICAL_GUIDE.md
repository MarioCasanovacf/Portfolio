# Technical Reference Guide
## Mario Casanova — Nutanix GSO Analytics Engineering Portfolio

> **Audience:** Data engineers, senior analysts, hiring managers with technical background.
> **Purpose:** Explain the architectural decisions, statistical methodology, and "what happens if you change X" scenarios for every component of this portfolio.

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Data Architecture — Synthetic Dataset Design](#2-data-architecture)
3. [Layer 1 — Descriptive Analytics Deep Dive](#3-layer-1-descriptive-analytics)
4. [Layer 2 — Diagnostic Analytics Deep Dive](#4-layer-2-diagnostic-analytics)
5. [Layer 3 — Predictive Analytics Deep Dive](#5-layer-3-predictive-analytics)
6. [Layer 4 — Prescriptive Analytics Deep Dive](#6-layer-4-prescriptive-analytics)
7. [Extension Guide — Moving to Real Data](#7-extension-guide)

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA SOVEREIGNTY LAYER                          │
│                                                                          │
│  src/data_generator.py                                                   │
│  ├── generate_support_tickets()   → 100,000 rows / 17 columns            │
│  ├── generate_pulse_telemetry()   →  54,750 rows /  8 columns            │
│  └── generate_migration_cohorts() →      24 rows / 11 columns            │
│                           ↓                                              │
│                  data/synthetic/*.csv                                    │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │  all notebooks read from here
          ┌────────────────┴────────────────┐
          │                                 │
┌─────────▼──────────┐           ┌──────────▼──────────┐
│   Layer 1 (01_)    │           │   Layer 2 (02_)      │
│   Descriptive      │           │   Diagnostic         │
│   pandas / seaborn │           │   statsmodels STL    │
│   scipy.stats      │           │   GESD / 3σ          │
└─────────┬──────────┘           └──────────┬───────────┘
          │                                 │
┌─────────▼──────────┐           ┌──────────▼──────────┐
│   Layer 3 (03_)    │           │   Layer 4 (04_)      │
│   Predictive       │           │   Prescriptive       │
│   SARIMA           │           │   Random Forest      │
│   Ljung-Box / RMSE │           │   Logistic Reg.      │
└────────────────────┘           └─────────────────────┘
          │
┌─────────▼──────────┐
│   Layer 5 (05_)    │
│   API Integration  │
│   Nutanix v4 SDK   │
│   OpenAPI / REST   │
└────────────────────┘
```

**Key design decision:** All notebooks are independent and can run in any order as long as the CSV files exist. Running `python src/data_generator.py` first is the only prerequisite.

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
| `aos_version` | str | Uniform across 10 AOS versions (6.1.1 → 6.8.2) |
| `migration_type` | str | VMware-to-AHV=28%, AOS-Upgrade=22%, Greenfield=18%, None=20%, HW-Refresh=12% |
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

### 2.2 Pulse Telemetry (`pulse_telemetry.csv`)

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

24 migration waves, each representing a batch of clusters migrating from VMware vSphere to Nutanix AHV. Duration ranges from 45 to 180 days. Used in Layer 1 for impact analysis and as context for Layer 3 forecasting.

---

## 3. Layer 1 — Descriptive Analytics

**File:** `notebooks/01_layer1_descriptive_gso_health_monitor.ipynb`
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
- Switch to mean instead of median: mean is sensitive to outliers (that one 2,000-hour P3 ticket pulls the average up significantly). Median is more robust and is what Nutanix would actually track in Salesforce reports

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
Action: That region needs either (a) dedicated on-call P1 SREs in that timezone, or (b) a follow-the-sun routing policy that redirects P1s to an active region during off-hours.

### 3.3 Backlog Aging

**Simulation logic:** We treat tickets created in the last 90 days as "open" (since their resolution might not yet be complete in a real scenario). In production, you would filter on `status IN ('open', 'in_progress')` from the Salesforce API.

**Bucketing strategy:**
```
<4h    → Fresh (within initial response window for P1/P2)
4-24h  → Active (working)
1-3d   → Aging (approaching P3 SLA)
3-7d   → At-risk (approaching P4 SLA)
>7d    → Stale (breach territory)
```

**What if you segment by engineer instead of AOS version?**
This reveals engineer-level bottlenecks — which SREs have disproportionate backlog aging. Useful for workforce management but requires careful handling to avoid creating unfair performance optics.

### 3.4 NPS Bootstrap Confidence Intervals

**Why bootstrap instead of normal CI?**
NPS scores (0–10 integers) are not normally distributed — they cluster at extremes (0–2 for detractors, 9–10 for promoters). The normal approximation `μ ± 1.96σ/√n` would produce artificially narrow or wide intervals. Bootstrap resampling (n=500 resamples) gives exact empirical CIs for any distribution.

**What if you increase n_boot from 500 to 5000?**
More stable CI estimates, especially for months with few NPS responses (<50 respondents). The tradeoff is computation time: 500 boots takes ~0.5s per month, 5000 takes ~5s. For a production pipeline running nightly, 1000 is a good balance.

**What if you track NPS by customer tier instead of overall?**
Strategic accounts have the highest NPS impact per point change (they generate the most revenue). A separate `strategic_nps` trend often moves earlier than overall NPS, making it a leading indicator.

---

## 4. Layer 2 — Diagnostic Analytics

**File:** `notebooks/02_layer2_diagnostic_anomaly_detection.ipynb`
**Libraries:** statsmodels, scipy, pandas, numpy

### 4.1 STL Seasonal Decomposition

**Model:** Additive decomposition: `Y(t) = Trend(t) + Seasonal(t) + Residual(t)`

**Why additive and not multiplicative?**
Multiplicative decomposition (`Y = T × S × R`) is appropriate when the seasonal amplitude grows proportionally with the trend level — e.g., airline ticket prices where summer peaks get larger as the baseline price grows. For IO latency, anomaly spikes are absolute (a hardware fault adds ~X µs regardless of the baseline trend level), making additive decomposition the correct choice.

**Period=7 (weekly):**
The synthetic data has a weekday factor of 1.0 vs. 0.72 on weekends. This 28% weekday premium creates a clear 7-day periodicity. In real Nutanix telemetry, you would confirm this with a periodogram before assuming weekly seasonality — data centers with 24/7 financial clients may show no weekly pattern.

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

**File:** `notebooks/03_layer3_predictive_ticket_forecasting.ipynb`
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
TICKETS_PER_SRE_PER_WEEK = 8   # assumption: 1 SRE handles 8 P1+P2 tickets/week
SREs_needed = ceil(peak_forecast / TICKETS_PER_SRE_PER_WEEK)
```
This constant should be calibrated from historical productivity data (e.g., from Salesforce time-tracking). If your SREs are senior and handle 12 tickets/week, the staffing recommendation decreases by 33%.

---

## 6. Layer 4 — Prescriptive Analytics

**File:** `notebooks/04_layer4_prescriptive_escalation_risk.ipynb`
**Libraries:** sklearn (RandomForest, LogisticRegression, Pipeline), scipy

### 6.1 Feature Engineering Decisions

**`sla_consumption_ratio = ttr_hours / sla_threshold_hours`**
This single feature captures both the raw TTR value and the priority context. A 5-hour resolution time is fine for P3 (ratio=1.25, mild breach) but catastrophic for P1 (ratio=10, severe breach). Without this ratio, the model would struggle to generalize across priorities.

**`eng_esc_rate` (engineer's historical escalation rate)**
This is a "leaky" feature in a strict ML sense — in real-time scoring of a new ticket, you don't yet know whether that ticket will escalate. However, the feature represents the *engineer's historical tendency* (before this ticket), not the outcome of this specific ticket. Using 80-20 train/test split with stratification ensures this is computed on training data and generalized correctly.

**What if you add `customer_sentiment` as a feature?**
In a real GSO environment, Salesforce Case Comments contain text from the customer. Running a pre-trained sentiment classifier (e.g., VADER or a fine-tuned BERT) on those comments and using the sentiment score as a feature would likely be the single most predictive addition. Estimated AUC-ROC improvement: +0.05 to +0.12 based on similar support ticket studies.

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
This would increase Recall (catch more escalations) at the cost of Precision (more false positives flagged for RM review). If the cost of a missed escalation >> cost of a false positive RM review, increase the weight on the minority class.

### 6.3 Model Comparison — Why Random Forest Wins

| Criterion | Logistic Regression | Random Forest |
|---|---|---|
| AUC-ROC | ~0.78 | ~0.85 |
| Interpretability | High (coefficients) | Medium (feature importance) |
| Handles non-linearity | No (linear decision boundary) | Yes (tree splits) |
| Handles feature interactions | No (explicitly needed) | Yes (implicit in splits) |
| Training time | <1s | ~30s |
| Production latency | <1ms per prediction | ~5ms per prediction |

**Recommendation:** Use Random Forest as the scoring engine; use Logistic Regression as the "explainability model" when a Resolution Manager asks "why was this ticket flagged?". The LR coefficients provide a human-readable explanation.

### 6.4 Threshold Optimization

**Default sklearn threshold = 0.50**
This minimizes overall error but is not optimal for imbalanced classes.

**Optimal threshold search:**
We sweep thresholds from 0.20 to 0.85 and select the one maximizing F1 score. F1 is the harmonic mean of Precision and Recall — it penalizes both missing escalations (low Recall) and over-flagging (low Precision).

**What if you optimize for Recall only (minimize missed escalations)?**
Lower the threshold to 0.25–0.30. Recall will approach 0.90+ but Precision drops to 0.15–0.20, meaning 80–85% of flagged tickets are false positives. This is only tolerable if RM review is very cheap (automated first-pass) and you have a second-stage human filter.

**What if you want to set a budget of "no more than 5% of tickets flagged"?**
Sort tickets by predicted probability descending. Take the top 5%. The probability threshold at the 95th percentile becomes your operational threshold. This is a "fixed budget" approach, common in operations with fixed RM headcount.

---

## 7. Extension Guide — Moving to Real Data

### 7.1 Replacing Synthetic Tickets with Salesforce Data

```python
import simple_salesforce

sf = simple_salesforce.Salesforce(
    username='your_user@nutanix.com',
    password='your_pass',
    security_token='your_token'
)

# SOQL query for Case objects
cases = sf.query_all("""
    SELECT Id, CaseNumber, CreatedDate, ClosedDate, Priority,
           Status, Account.Name, Account.Type, OwnerId,
           IsEscalated, NPS_Score__c, AOS_Version__c
    FROM Case
    WHERE CreatedDate >= 2022-01-01T00:00:00Z
    LIMIT 100000
""")

df = pd.DataFrame(cases['records']).drop('attributes', axis=1)
```

You would then apply the same TTR calculation: `ttr_hours = (ClosedDate - CreatedDate).dt.total_seconds() / 3600`

### 7.2 Replacing Synthetic Telemetry with Nutanix Pulse API v4

See `notebooks/05_nutanix_api_v4_integration.ipynb` for the full implementation. The key SDK call:

```python
from ntnx_vmm_py_client import ApiClient, Configuration
from ntnx_vmm_py_client.api import StatsApi

config = Configuration()
config.host = 'https://prism-central.your-org.nutanix.com:9440'
config.username = 'api_user'
config.password = 'api_password'

client = ApiClient(configuration=config)
stats_api = StatsApi(api_client=client)

# Get IO latency for all clusters, last 7 days
# OData $filter for performance optimization
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
  → Pull last 7 days of Salesforce cases
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

*Mario Casanova | Analytics Engineering Portfolio*
*For non-technical overview: see `FOR_NON_ENGINEERS.md`*
