# Data

## Files

### `lob_events_synthetic.csv`
Synthetic Level 2 tick-by-tick Limit Order Book (LOB) data with 50,000 events. Simulates order submissions, cancellations, and executions around a random-walk mid price starting at 150.0. Each execution exerts a **permanent price impact** on the mid in the aggressor's direction (size-proportional, `lob_impact` coefficient), so signed order flow causally leads price — a recoverable Kyle-lambda relationship the notebook measures.

| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | Event timestamp starting at 2025-01-01 09:30:00, millisecond resolution |
| order_id | str | 8-character hex order identifier |
| event_type | int | Event type: 1 = Submission, 2 = Cancellation, 3 = Execution |
| side | str | Order side: "Bid" or "Ask" |
| price | float | Order price, derived from mid price +/- half spread |
| size | int | Order size in shares (lognormal distribution, minimum 1) |

### `correlated_assets_synthetic.csv`
Synthetic daily price series for 50 correlated assets over 1,000 trading days (starting 2020-01-01). Generated from a **factor model that plants five recoverable sectors** (a common market factor + one factor per sector + idiosyncratic noise → high within-sector / low between-sector correlation), with injected volatility regimes (high-vol at days 300-400, medium-vol at days 700-850). Assets are contiguous blocks of 10 (Asset_1..10 → sector 0, …). Used for Hierarchical Risk Parity analysis (cluster recovery + out-of-sample portfolio comparison).

| Column | Type | Description |
|--------|------|-------------|
| Date | date | Trading date |
| Asset_1 ... Asset_50 | float | Daily closing price for each synthetic asset (starting near 100) |

## Regeneration

To regenerate the data files, run from the project root:

```bash
qfinance generate-data --all
```

All files are generated deterministically with `QFINANCE_RANDOM_SEED=42`.
