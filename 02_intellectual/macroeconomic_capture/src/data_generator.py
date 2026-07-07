import pandas as pd
import numpy as np
import os

RANDOM_SEED = 42


def generate_macro_data(start_year=2000, end_year=2025):
    """Synthetic quarterly macro data for a *structural* study of fiscal crowding-out.

    Design goal: the crowding-out relationship must be a genuine (if synthetic)
    structural effect that an analyst has to RECOVER, not an algebraic identity
    read straight back out. Two properties make it honest:

      1. Private investment responds to the real yield through a KNOWN structural
         slope (B_YIELD), but yield is only one of several drivers — there is also
         an output-growth (accelerator) term and idiosyncratic noise, so nothing is
         a tautology.
      2. A latent business cycle is a CONFOUNDER: it pushes the sovereign yield up
         (monetary-policy reaction) AND output growth up (boom), and growth in turn
         lifts investment. So the *naive* correlation between yield and investment is
         biased; the true crowding-out slope only emerges once the analyst controls
         for the cycle (Output_Growth_Pct). That is the point of the notebook.
    """
    print(f"[*] Generating structural macro time series from {start_year} to {end_year}...")
    rng = np.random.default_rng(RANDOM_SEED)

    dates = pd.date_range(start=f"{start_year}-01-01", end=f"{end_year}-12-31", freq="QE")
    n = len(dates)

    # --- Latent business cycle: AR(1) output gap (the confounder) ---
    cycle = np.zeros(n)
    for t in range(1, n):
        cycle[t] = 0.82 * cycle[t - 1] + rng.normal(0, 1.0)

    # --- Real output: trend + cycle; quarterly growth is the OBSERVABLE cycle proxy ---
    gdp = 6000.0 + 35.0 * np.arange(n) + 180.0 * cycle
    output_growth = np.zeros(n)
    output_growth[1:] = np.diff(gdp) / gdp[:-1] * 100.0  # % q/q

    # --- Government budget constraint (countercyclical spending, procyclical taxes) ---
    g_spending = 1000.0 + np.cumsum(rng.normal(8, 4, n)) - 10.0 * cycle
    taxes = 0.85 * g_spending + 8.0 * cycle + rng.normal(0, 12, n)
    deficit = g_spending - taxes
    debt = np.cumsum(deficit)
    debt_to_gdp = debt / gdp

    # --- Sovereign real yield: debt channel (crowding-out source) + policy reaction + noise ---
    dz = (debt_to_gdp - debt_to_gdp.mean()) / debt_to_gdp.std()
    yield_10y = 0.040 + 0.009 * dz + 0.012 * cycle + rng.normal(0, 0.003, n)
    yield_10y = np.clip(yield_10y, 0.001, None)
    yld_pct = yield_10y * 100.0

    # --- Private fixed capital formation: TRUE structural model with a KNOWN slope ---
    B_GROWTH = 40.0  # accelerator: investment rises with output growth
    B_YIELD = 75.0   # crowding-out: each +1 pp of yield lowers investment by ~75 (the quantity to recover)
    private = (
        2600.0
        + B_GROWTH * output_growth
        - B_YIELD * yld_pct
        + rng.normal(0, 35, n)
    )

    df_macro = pd.DataFrame({
        "Date": dates,
        "Government_Spending": g_spending,
        "Tax_Revenue": taxes,
        "Sovereign_Debt_Outstanding": debt,
        "Sovereign_Yield_10Y": yield_10y,
        "Output_Growth_Pct": output_growth,
        "Private_Capital_Formation": private,
    })

    os.makedirs("data", exist_ok=True)
    out_path = "data/macroeconomic_budget_synthetic.csv"
    df_macro.to_csv(out_path, index=False)
    # the true structural coefficient, recorded so the notebook can compare its estimate
    print(f"[+] Saved macro data to {out_path}  (true crowding-out slope B_YIELD = -{B_YIELD} per pp)")


def generate_corporate_zombie_data(n_companies=1000, n_years=10):
    """Synthetic cross-section for unsupervised recovery of 'zombie' firms.

    Design goal: zombie firms form a genuinely SEPARABLE density cluster in
    feature space (low ROIC, low interest-coverage, high state subsidies, high
    leverage), distinct from market-driven firms — with enough spread and a few
    ambiguous firms that recovery is good but not trivially perfect. A density
    method (DBSCAN on standardized features) can then recover the cluster WITHOUT
    using the label, and the recovery is validated against the known Is_Zombie
    ground truth (precision / recall). The planted structure is disclosed; the
    method demo is what is being shown.
    """
    print(f"[*] Generating corporate cross-section for {n_companies} firms...")
    rng = np.random.default_rng(RANDOM_SEED + 1)

    # ~15% of firms are subsidy-sustained zombies
    is_zombie = rng.random(n_companies) < 0.15
    n = n_companies

    roic = np.where(is_zombie, rng.normal(0.005, 0.020, n), rng.normal(0.090, 0.040, n))
    icr = np.where(is_zombie, rng.normal(0.55, 0.25, n), rng.normal(3.50, 1.20, n))
    subsidies = np.clip(
        np.where(is_zombie, rng.normal(280, 90, n), rng.exponential(8, n)), 0, None
    )
    leverage = np.clip(
        np.where(is_zombie, rng.normal(3.5, 0.8, n), rng.normal(1.2, 0.6, n)), 0.1, None
    )
    sector = np.where(
        is_zombie,
        "State_Subsidized",
        rng.choice(["Tech", "Manufacturing", "Services"], n),
    )

    df_corp = pd.DataFrame({
        "Company_ID": [f"Corp_{i}" for i in range(n_companies)],
        "Sector": sector,
        "ROIC_Avg": roic,
        "Interest_Coverage_Ratio": icr,
        "State_Subsidies_Millions": subsidies,
        "Debt_to_Equity": leverage,
        "Is_Zombie": is_zombie.astype(int),
    })

    os.makedirs("data", exist_ok=True)
    out_path = "data/corporate_zombies_synthetic.csv"
    df_corp.to_csv(out_path, index=False)
    print(f"[+] Saved corporate data to {out_path}  ({int(is_zombie.sum())} zombies / {n_companies})")


if __name__ == "__main__":
    generate_macro_data()
    generate_corporate_zombie_data()
    print("Generation complete.")
