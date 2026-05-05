# real-estate

> House sale price prediction on the **King County (Seattle area, 2014–2015)**
> dataset — EDA, feature engineering, and regression models, done with the
> discipline of a production project rather than as a throwaway notebook.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Why this project

The King County dataset is the "Iris of real estate" — everyone uses it
because it is accessible, messy enough to be interesting, and has a clear
target variable (`price`). Most notebooks that touch it stop at superficial
EDA. This project walks the full pipeline: cleaning → geospatial feature
engineering → linear vs gradient-boosted baselines → residual diagnostics.

## Stack

| Layer | Technology |
|---|---|
| EDA + transformations | `pandas` + `numpy` |
| Visualization | `matplotlib` + `seaborn` |
| Models | `scikit-learn` (linear, ridge, RF, GBM) |
| Optional boosting | `xgboost` / `lightgbm` |

## Analysis

| Notebook | Question |
|---|---|
| `house_sales_king_county.ipynb` | Which features best explain price, and which baseline wins? |

## Architecture

```mermaid
flowchart LR
    G[data_generator] --> D[(king_county.csv)]
    D --> E[EDA + cleaning]
    E --> F[Feature engineering]
    F --> M1[Linear / Ridge]
    F --> M2[Random Forest]
    F --> M3[Gradient Boosting]
    M1 & M2 & M3 --> R[Comparison + residuals]
```

## Quick Start

```bash
git clone https://github.com/MarioCasanovacf/Portfolio.git
cd Portfolio/real_estate
pip install -e ".[dev,notebooks]"
python src/data_generator.py
jupyter lab house_sales_king_county.ipynb
pytest -m unit
```

## License

MIT — see [LICENSE](LICENSE).
