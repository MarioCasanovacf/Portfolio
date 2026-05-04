# ADR 001 — Synthetic data strategy

**Status:** Accepted
**Date:** 2026-04-20

## Context

The toolkit demonstrates three quantitative-finance workloads (LOB
microstructure, Heston pricing, HRP allocation). Production-grade workloads
typically depend on paid data providers (Refinitiv, Bloomberg, Polygon.io). For
a portfolio project we need to balance:

- **Reproducibility** for reviewers — they should be able to clone and run
  identical analyses without API keys.
- **Realism** — the data must exhibit the structural properties the algorithms
  are designed to exploit (volatility clustering, regime shifts, correlation
  topology, lognormal sizes).
- **Cost / latency** — no recurring fees, no network dependency in CI.

## Options considered

1. **Real free data via `yfinance`**
   - Pros: realistic prices for HRP; zero cost.
   - Cons: rate-limited, schema drifts, inconsistent history → CI flakiness.
2. **Real paid data (Polygon.io, Alpha Vantage)**
   - Pros: full realism for LOB and options.
   - Cons: requires API keys, recurring spend, hard to reproduce externally.
3. **Synthetic data with documented generative process**
   - Pros: 100% reproducible, no external dependency, parameters tunable for
     stress-testing algorithms.
   - Cons: must justify that synthetic data exercises the algorithms meaningfully.

## Decision

Adopt option **3 (synthetic data)** for v0.1.0, with the following design:

- Generators live in `src/quantitative_finance/data/generator.py`.
- Use `numpy.random.default_rng(seed)` (modern Generator API) for full determinism.
- Inject realistic structural features:
  - LOB: random-walk mid price, Bid/Ask balance, lognormal sizes.
  - Asset prices: random PD covariance matrix + injected high-vol and medium-vol
    regimes.
- Expose all parameters via `Settings` (env-overridable).

## Consequences

**Positive**
- CI is fast and deterministic.
- Reviewers can verify findings byte-for-byte.
- New parameter regimes can be tested by tweaking env vars only.

**Negative**
- Numerical results (Sharpe ratios, option prices) do not generalize to real
  markets — this must be stated explicitly in any report.
- The HRP Sharpe-ratio comparison vs equal-weight is "synthetic vs synthetic" —
  a future ADR may revisit this when integrating yfinance for a realism overlay.

## Future revisit triggers

- A reviewer (recruiter, hiring manager) asks for results on real tickers.
- The Heston pricer is extended to calibrate against market implied vol.
- Prefect orchestration is introduced and we want a "real data" branch in
  parallel to "synthetic data".
