# macroeconomic-capture

> Two macroeconomic hypotheses normally argued in prose, here quantified with
> synthetic data and basic econometrics: **fiscal crowding-out** of private
> investment, and the identification of **zombie firms** (companies that survive
> only because the cost of capital is artificially low).

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Why this project

Macroeconomics is full of hypotheses that are hard to test because controlled
experiments are impossible. But you can: (a) generate synthetic data
consistent with a hypothesized causal mechanism, (b) fit a model that assumes
that mechanism, and (c) see what conditions make the effect detectable. That
is valuable both pedagogically and as a methodology test bench.

## Stack

| Layer | Technology |
|---|---|
| Synthetic generation | `numpy` + `pandas` |
| Models | `statsmodels (seasonal_decompose)` |
| Visualization | `matplotlib` + `seaborn` |

## Notebooks

| # | Notebook | Hypothesis |
|---|---|---|
| 01 | `01_Fiscal_Crowding_Out.ipynb` | More public debt → less private investment |
| 02 | `02_Zombie_Corporations.ipynb` | Low rates keep unprofitable firms alive |

## Architecture

```mermaid
flowchart LR
    G[data_generator] --> B[(macroeconomic_budget_synthetic.csv)]
    G --> Z[(corporate_zombies_synthetic.csv)]
    B --> N1[01 Crowding-out controlled OLS]
    Z --> N2[02 Zombie identification]
```

## Quick Start

```bash
git clone https://github.com/MarioCasanovacf/Portfolio.git
cd Portfolio/macroeconomic_capture
pip install -e ".[dev,notebooks]"
python src/data_generator.py
jupyter lab notebooks/
pytest -m unit
```

## License

MIT — see [LICENSE](LICENSE).
