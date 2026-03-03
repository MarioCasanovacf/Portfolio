import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

def generate_macro_data(start_year=2000, end_year=2025):
    """
    Generates synthetic macroeconomic time series data to model 
    Fiscal Crowding-out and the Government Budget Constraint.
    Fixed seed (42) to ensure verifiable deterministic relationships
    between public debt expansion and private capital friction.
    """
    print(f"[*] Generating macro time series from {start_year} to {end_year}...")
    
    dates = pd.date_range(start=f'{start_year}-01-01', end=f'{end_year}-12-31', freq='QE')
    n_periods = len(dates)
    
    # Government Budget Constraint components
    # G_t: Government Spending
    g_spending_base = 1000 + np.cumsum(np.random.normal(10, 5, n_periods))
    # T_t: Taxes collected
    taxes_base = g_spending_base * np.random.uniform(0.70, 0.95, n_periods)
    
    # B_t: Government Debt (accumulating deficit G - T)
    deficit = g_spending_base - taxes_base
    debt_issuance = np.cumsum(deficit)
    
    # Soverign yield curve component (r) heavily influenced by debt levels (crowding out proxy)
    sovereign_yield_10y = 0.02 + (debt_issuance / np.max(debt_issuance)) * 0.05 + np.random.normal(0, 0.005, n_periods)
    
    # Private sector Fixed Capital Formation (inversely correlated to yield spikes)
    private_investment_base = 2500 * (1 - (sovereign_yield_10y * 5)) + np.cumsum(np.random.normal(5, 10, n_periods))
    
    df_macro = pd.DataFrame({
        'Date': dates,
        'Government_Spending': g_spending_base,
        'Tax_Revenue': taxes_base,
        'Sovereign_Debt_Outstanding': debt_issuance,
        'Sovereign_Yield_10Y': sovereign_yield_10y,
        'Private_Capital_Formation': private_investment_base
    })
    
    os.makedirs('../data', exist_ok=True)
    out_path = '../data/macroeconomic_budget_synthetic.csv'
    df_macro.to_csv(out_path, index=False)
    print(f"[+] Saved Macroeconomic data to {out_path}")

def generate_corporate_zombie_data(n_companies=1000, n_years=10):
    """
    Genera dataset transversal simulando corporaciones zombis sostenidas 
    por intervencionismo vs empresas sujetas a destrucción creativa.
    """
    print(f"[*] Generating corporate sector data for {n_companies} companies over {n_years} years...")
    
    np.random.seed(RANDOM_SEED + 1) # Slight shift for different distribution
    
    companies = [f'Corp_{i}' for i in range(n_companies)]
    
    # Sectors
    sectors = np.random.choice(['Tech', 'Manufacturing', 'State_Subsidized', 'Services'], n_companies, p=[0.2, 0.3, 0.2, 0.3])
    
    # ROIC (Return on Invested Capital)
    # State subsidized have lower ROIC artificially sustained
    roic = np.where(
        sectors == 'State_Subsidized',
        np.random.normal(0.01, 0.02, n_companies), # Mean 1%, struggles
        np.random.normal(0.08, 0.05, n_companies)  # Mean 8%, market driven
    )
    
    # Interest Coverage Ratio (ICR = EBIT / Interest Expenses)
    # Zombie companies have ICR < 1 for extended periods
    icr = np.where(
        sectors == 'State_Subsidized',
        np.random.normal(0.6, 0.3, n_companies),   # Cannot cover interest
        np.random.normal(3.5, 1.5, n_companies)    # Healthy coverage
    )
    
    # Public Subsidies (Bailouts / Tax breaks)
    subsidies = np.where(
        sectors == 'State_Subsidized',
        np.random.uniform(50, 500, n_companies),
        np.random.uniform(0, 20, n_companies) * (icr < 1).astype(int) # Only failing private get tiny bailouts occasionally
    )
    
    df_corp = pd.DataFrame({
        'Company_ID': companies,
        'Sector': sectors,
        'ROIC_Avg': roic,
        'Interest_Coverage_Ratio': icr,
        'State_Subsidies_Millions': subsidies,
        'Debt_to_Equity': np.random.uniform(0.1, 5.0, n_companies)
    })
    
    # Create zombie classification (ICR < 1 AND heavily indebted)
    df_corp['Is_Zombie'] = ((df_corp['Interest_Coverage_Ratio'] < 1.0) & (df_corp['Debt_to_Equity'] > 2.0)).astype(int)
    
    out_path = '../data/corporate_zombies_synthetic.csv'
    df_corp.to_csv(out_path, index=False)
    print(f"[+] Saved Corporate Zombie data to {out_path}")

if __name__ == "__main__":
    generate_macro_data()
    generate_corporate_zombie_data()
    print("Generation complete.")
