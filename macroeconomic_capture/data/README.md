# Data

## Files

### `macroeconomic_budget_synthetic.csv`
Synthetic quarterly macroeconomic time series (2000-2025) modeling the Government Budget Constraint and fiscal crowding-out dynamics. Sovereign debt accumulates from persistent deficits, and rising yields depress private capital formation.

| Column | Type | Description |
|--------|------|-------------|
| Date | date | Quarter-end date (e.g., 2000-03-31) |
| Government_Spending | float | Government expenditure (G_t), trending upward from ~1000 |
| Tax_Revenue | float | Tax revenue (T_t), stochastic fraction (70-95%) of spending |
| Sovereign_Debt_Outstanding | float | Cumulative government debt from accumulated deficits |
| Sovereign_Yield_10Y | float | 10-year sovereign bond yield, positively correlated with debt level |
| Private_Capital_Formation | float | Private sector fixed investment, inversely correlated with yield |

### `corporate_zombies_synthetic.csv`
Cross-sectional dataset of 1,000 synthetic corporations for zombie-firm classification. State-subsidized firms exhibit low profitability and interest coverage, while market-driven firms show healthy fundamentals.

| Column | Type | Description |
|--------|------|-------------|
| Company_ID | str | Unique company identifier (e.g., "Corp_0") |
| Sector | str | One of: "Tech", "Manufacturing", "State_Subsidized", "Services" |
| ROIC_Avg | float | Average Return on Invested Capital (~1% for state-subsidized, ~8% for others) |
| Interest_Coverage_Ratio | float | EBIT / Interest Expenses (< 1.0 indicates inability to cover debt service) |
| State_Subsidies_Millions | float | Government subsidies received in millions |
| Debt_to_Equity | float | Leverage ratio, uniform in [0.1, 5.0] |
| Is_Zombie | int | Binary flag: 1 if ICR < 1.0 and Debt_to_Equity > 2.0 |

## Regeneration

To regenerate the data files, run from the project root:

```bash
python src/data_generator.py
```

Macroeconomic data uses `np.random.seed(42)`. Corporate zombie data uses `np.random.seed(43)`.
