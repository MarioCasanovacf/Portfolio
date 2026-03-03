import pandas as pd
import numpy as np
import uuid
from datetime import datetime, timedelta
import os

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

def generate_lob_data(n_events=50000, start_price=150.0):
    """
    Generates synthetic Level 2 Tick-by-Tick Limit Order Book (LOB) data.
    Note: We explicitly fix the seed to RANDOM_SEED=42 to guarantee reproducibility.
    Since this portfolio targets institutional profiles, the recruiter or reviewer
    must be able to verify our findings deterministically without random fluctuations
    interfering with the analysis of microstructural variables (such as effective 
    bid-ask spread or order imbalance).
    """
    print(f"[*] Generating {n_events} LOB events...")
    timestamps = [datetime(2025, 1, 1, 9, 30, 0) + timedelta(milliseconds=i*10 + int(np.random.exponential(5))) for i in range(n_events)]
    
    # Random walk for mid price
    price_changes = np.random.normal(0, 0.01, n_events)
    mid_prices = start_price + np.cumsum(price_changes)
    
    # Types of events: 1=Submission, 2=Cancellation, 3=Execution
    event_types = np.random.choice([1, 2, 3], size=n_events, p=[0.7, 0.2, 0.1])
    sides = np.random.choice(['Bid', 'Ask'], size=n_events)
    
    sizes = np.random.lognormal(mean=np.log(100), sigma=1.0, size=n_events).astype(int)
    sizes = np.maximum(sizes, 1) # At least 1 share
    
    # LOB Prices
    bid_ask_spreads = np.random.uniform(0.01, 0.05, n_events)
    prices = np.where(sides == 'Bid', mid_prices - bid_ask_spreads/2, mid_prices + bid_ask_spreads/2)
    prices = np.round(prices, 2)
    
    order_ids = [uuid.uuid4().hex[:8] for _ in range(n_events)]
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'order_id': order_ids,
        'event_type': event_types,
        'side': sides,
        'price': prices,
        'size': sizes
    })
    
    os.makedirs('../data', exist_ok=True)
    out_path = '../data/lob_events_synthetic.csv'
    df.to_csv(out_path, index=False)
    print(f"[+] Saved LOB data to {out_path}")


def generate_asset_prices_correlation(n_assets=50, n_days=1000):
    """
    Generates correlated synthetic daily prices for Hierarchical Risk Parity.
    Uses RANDOM_SEED=42 structurally to ensure the topological clusters found
    during unsupervised clustering (HRP) remain stable across executions.
    """
    print(f"[*] Generating correlated asset prices for {n_assets} assets over {n_days} days...")
    
    # Generate random positive definite covariance matrix
    A = np.random.rand(n_assets, n_assets)
    cov_matrix = np.dot(A, A.transpose()) 
    
    # Convert to correlation matrix
    d = np.sqrt(np.diag(cov_matrix))
    corr_matrix = cov_matrix / np.outer(d, d)
    
    # Generate daily returns based on correlation matrix
    returns = np.random.multivariate_normal(mean=np.zeros(n_assets), cov=corr_matrix, size=n_days)
    
    # Add some market states/regimes
    regime_multiplier = np.ones(n_days)
    regime_multiplier[300:400] = 3.0 # High vol regime
    regime_multiplier[700:850] = 2.0 # Medium vol regime
    
    for i in range(n_assets):
        returns[:, i] = returns[:, i] * regime_multiplier * 0.01 # scale returns
        
    prices = np.exp(np.cumsum(returns, axis=0)) * 100
    
    dates = [datetime(2020, 1, 1) + timedelta(days=i) for i in range(n_days)]
    
    df = pd.DataFrame(prices, columns=[f'Asset_{i+1}' for i in range(n_assets)])
    df['Date'] = dates
    df.set_index('Date', inplace=True)
    
    out_path = '../data/correlated_assets_synthetic.csv'
    df.to_csv(out_path)
    print(f"[+] Saved correlated assets data to {out_path}")


if __name__ == "__main__":
    print(f"Initializing synthetic data generation with RANDOM_SEED={RANDOM_SEED}...")
    generate_lob_data()
    generate_asset_prices_correlation()
    print("Generation complete.")
