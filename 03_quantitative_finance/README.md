# 03 — Quantitative Finance

**Domain:** Market microstructure, derivatives pricing, portfolio optimization
**Status:** In development — code being consolidated from existing work
**Profile:** Institutional-grade, not retail trading signals

---

## Design Philosophy

> Financial data repositories are full of portfolios that visualize S&P 500 closing prices from Yahoo Finance and call it "quantitative analysis." That is not this.
>
> The signal of real institutional competence comes from building infrastructure that solves problems of latency, concurrency, statistical rigor, and mathematical depth at a corporate level. The architecture here reflects an understanding of the full data lifecycle: from raw tick-by-tick ingestion to derivative valuation.

---

## Planned Projects

### Project A — Limit Order Book Reconstruction
**What it does:** Reconstructs the full Limit Order Book state from raw Level 2 tick-by-tick data, calculating real-time microstructure metrics.

**Why it's hard:** Each tick event is an incremental update (add order, cancel order, execute trade). Maintaining a correct, deterministic order book state in memory across millions of events requires processing them strictly in sequence while computing derived metrics asynchronously.

**Key outputs:**
- Order book depth at each timestamp (bid/ask price levels × quantities)
- Order book imbalance: `OBI = (bid_qty - ask_qty) / (bid_qty + ask_qty)`
- Effective bid-ask spread (transaction-cost adjusted)
- Volume-weighted average price (VWAP)

**Techniques:** Async Python event processing, sorted dictionary order book, time series persistence

**Mathematical foundation:**
```
Effective spread = 2 × d × (P_transaction - M_t)
where d = +1 (buy) or -1 (sell), M_t = bid-ask midpoint at time t
```

---

### Project B — Exotic Options Pricing Under Stochastic Volatility
**What it does:** Prices European and barrier options using two methods: Monte Carlo simulation with variance reduction, and finite differences solving the PDE numerically.

**Model:** Heston stochastic volatility — volatility is itself a mean-reverting stochastic process:
```
dS = μS dt + √v S dW₁
dv = κ(θ - v) dt + σ √v dW₂
corr(dW₁, dW₂) = ρ dt
```

**Key outputs:**
- Implied volatility surface (3D) calibrated against listed options
- Option price as function of strike × maturity
- Greeks: Δ, Γ, Vega, Θ under stochastic vol

**Why Heston over Black-Scholes:** Black-Scholes assumes constant volatility. Real markets show volatility smiles and term structure. Heston captures this with two additional parameters (mean reversion speed κ, long-term vol θ) and the vol-of-vol σ.

**Variance reduction:** Antithetic variates + control variates reduce Monte Carlo standard error by ~60% for equivalent sample size.

---

### Project C — Hierarchical Risk Parity Portfolio Optimizer
**What it does:** Allocates capital across assets using graph theory and hierarchical clustering rather than inverting a covariance matrix (which is numerically unstable for large portfolios).

**Why HRP over Markowitz:**
- Markowitz mean-variance optimization requires inverting the covariance matrix Σ⁻¹, which becomes ill-conditioned when assets are highly correlated or when T (observations) < N (assets)
- HRP builds a dendrogram of asset correlations, quasi-diagonalizes the covariance matrix, and allocates risk through recursive bisection — never inverting the matrix
- Empirically: HRP outperforms Markowitz out-of-sample when correlation structures shift (which they always do in market stress)

**Algorithm steps:**
1. Compute correlation matrix from returns: `ρ = diag(Σ)^(-½) Σ diag(Σ)^(-½)`
2. Convert to distance matrix: `d = √(½(1-ρ))`
3. Hierarchical clustering (Ward linkage) on distance matrix
4. Quasi-diagonalization: reorder assets to cluster similar ones
5. Recursive bisection: split portfolio into two sub-portfolios at each node, allocating inverse-variance weights

```python
# Simplified recursive bisection
def recursive_bisect(covariance, sorted_items):
    if len(sorted_items) == 1: return {sorted_items[0]: 1.0}
    left, right = split_cluster(sorted_items)
    left_var  = cluster_variance(covariance, left)
    right_var = cluster_variance(covariance, right)
    alpha = 1 - left_var / (left_var + right_var)
    weights = {}
    for k, v in recursive_bisect(covariance, left).items():
        weights[k] = alpha * v
    for k, v in recursive_bisect(covariance, right).items():
        weights[k] = (1 - alpha) * v
    return weights
```

**Benchmark comparison:** HRP vs. Equal Weight vs. Minimum Variance vs. Max Sharpe (in-sample and out-of-sample)

---

### Project D — Macrofinancial Crowding-Out Engine
*(See also `05_macroeconomics/` for the fiscal policy framing)*

**Government Budget Constraint:**
```
G_t + r·B_{t-1} = T_t + B_t + ΔM_t
```
Operationalized as a time series model that quantifies the empirical differential between public credit expansion and private fixed capital formation.

---

## Data Sources

- **Tick data:** Lobster Data (NASDAQ order book), IEX Cloud API
- **Options data:** CBOE datashop, Yahoo Finance options chain
- **Asset prices:** yfinance (development), Bloomberg API / Refinitiv (production)
- **Macro data:** FRED API (Federal Reserve), World Bank API, national transparency portals

---

## Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| Event processing | Python asyncio / C# | Minimize latency for LOB reconstruction |
| Numerical PDE solver | numpy, scipy.sparse | Finite difference grids for options pricing |
| Monte Carlo | numpy vectorized | SIMD-parallelizable across paths |
| Data persistence | Snowflake / DuckDB | Columnar for time series aggregation |
| Visualization | Plotly 3D | Interactive volatility surface |

---

*Code being consolidated. Next update will include working implementations of HRP and Heston Monte Carlo.*
