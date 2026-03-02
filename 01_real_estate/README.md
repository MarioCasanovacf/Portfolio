# 01 — Real Estate Analytics

**Domain:** Real estate price modeling | **Status:** Complete
**Source:** IBM Data Science Professional Certificate — Final Project

---

## Business Problem

Predict house sale prices in King County (Seattle area) from property features. This is the classic supervised regression problem: given 21 features about a house (size, location, condition, year built), can we build a model that explains price variation and generalizes to unseen properties?

## What's Demonstrated

| Skill | Implementation |
|---|---|
| Exploratory Data Analysis | Correlation matrix, distribution analysis, outlier detection |
| Feature selection | Identifying `sqft_living` (r=0.70), `grade` (r=0.67) as key drivers |
| Data wrangling | Handling NaNs in `bedrooms` and `bathrooms` with mean imputation |
| Regression pipeline | sklearn `Pipeline` with `StandardScaler` + `PolynomialFeatures` + `LinearRegression` |
| Regularization | Ridge regression (α=0.1) to control overfitting on polynomial features |
| Model evaluation | R² from 0.0005 (baseline: `long` feature) → 0.70 (polynomial Ridge pipeline) |
| Train/test split | 85/15 split with `random_state=1` for reproducibility |

## Key Result

A polynomial Ridge regression pipeline achieves **R² = 0.70** on the held-out test set — a 140,000% improvement over the single-feature baseline (`longitude` alone explains 0.05% of price variance).

The lesson that transfers to every other domain in this portfolio: baseline models exist to be beaten, and systematic feature selection + regularization is the reliable path.

## How It Connects to the Rest of the Portfolio

The techniques here are the statistical backbone reused at higher complexity in other sections:

| Concept learned here | Where it reappears |
|---|---|
| Ridge regularization (α=0.1) | Logistic Regression in `02_cloud_infrastructure_support/04_prescriptive_escalation_risk` |
| sklearn Pipeline | Feature preprocessing in all classification models |
| R² evaluation | RMSE/Ljung-Box evaluation in `02_cloud_infrastructure_support/03_predictive_volume_forecasting` |
| Polynomial feature transformation | Nonlinear relationship modeling in bioinformatics section |

## Run

```bash
jupyter notebook house_sales_king_county_analysis.ipynb
```

No additional data download required — the notebook loads the dataset from IBM's public S3 bucket.
