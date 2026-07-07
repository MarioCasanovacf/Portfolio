# Data

## Files

### `macroeconomic_budget_synthetic.csv`
Synthetic quarterly macroeconomic time series (2000-2025) modeling the Government Budget Constraint and fiscal crowding-out. Yields respond to the debt level and to a latent business cycle; private capital formation follows a structural model (an output-growth accelerator minus a **known** crowding-out response to yields, plus noise). It is built so the crowding-out coefficient must be *recovered* by controlling for the cycle — not read off a raw correlation.

| Column | Type | Description |
|--------|------|-------------|
| Date | date | Quarter-end date (e.g., 2000-03-31) |
| Government_Spending | float | Government expenditure (G_t); structural growth, countercyclical |
| Tax_Revenue | float | Tax revenue (T_t) ≈ 0.85·spending, procyclical, plus noise |
| Sovereign_Debt_Outstanding | float | Cumulative government debt from accumulated deficits |
| Sovereign_Yield_10Y | float | 10-year real yield; responds to debt-to-GDP and to the business cycle (policy reaction) |
| Output_Growth_Pct | float | Quarterly output growth (%) — observable proxy for the latent cycle, used as a control |
| Private_Capital_Formation | float | Private fixed investment = accelerator·growth − (known) crowding-out·yield + noise |

### `corporate_zombies_synthetic.csv`
Cross-sectional dataset of 1,000 synthetic corporations. A ~15% subsidy-sustained "zombie" sub-population is planted as a **separable cluster** (low ROIC and interest-coverage, high state subsidies and leverage); market-driven firms show healthy fundamentals. Used to demonstrate unsupervised recovery (DBSCAN) of that cluster, validated against the label.

| Column | Type | Description |
|--------|------|-------------|
| Company_ID | str | Unique company identifier (e.g., "Corp_0") |
| Sector | str | One of: "Tech", "Manufacturing", "State_Subsidized", "Services" |
| ROIC_Avg | float | Average Return on Invested Capital (~0.5% for zombies, ~9% for market firms) |
| Interest_Coverage_Ratio | float | EBIT / Interest Expenses (~0.55 for zombies, ~3.5 for market firms) |
| State_Subsidies_Millions | float | Government subsidies received in millions (high for zombies, near-zero otherwise) |
| Debt_to_Equity | float | Leverage (~3.5 for zombies, ~1.2 for market firms) |
| Is_Zombie | int | Ground-truth flag: 1 for the planted subsidy-sustained zombie sub-population (~15%) |

## Regeneration

To regenerate the data files, run from the project root:

```bash
python src/data_generator.py
```

Macroeconomic data uses `np.random.default_rng(42)`. Corporate data uses `np.random.default_rng(43)`.
