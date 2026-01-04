import pandas as pd
import numpy as np
from price_action_lib import PriceActionLib

def generate_sample_data(n=200):
    """Generate artificial price data with structure"""
    np.random.seed(42)
    # Create an uptrend then a downtrend
    trend = np.linspace(100, 110, 100).tolist() + np.linspace(110, 95, 100).tolist()
    noise = np.random.normal(0, 0.5, n)
    prices = np.array(trend) + noise
    
    data = pd.DataFrame({
        'open': prices - 0.2,
        'high': prices + 0.5,
        'low': prices - 0.5,
        'close': prices,
        'volume': np.random.randint(100, 1000, n)
    })
    return data

def test_elite_logic():
    pa = PriceActionLib()
    data = generate_sample_data()
    
    print("Testing Elite Logic Analysis...")
    result = pa.analyze_all(data)
    
    # Check for new columns
    expected_cols = [
        'bos', 'choch', 'trend_bias', 
        'eqh', 'eql', 'sweep_high', 'sweep_low',
        'is_discount', 'is_premium'
    ]
    
    for col in expected_cols:
        if col in result.columns:
            count = result[col].sum() if result[col].dtype == bool else (result[col] != 0).sum()
            print(f"[OK] Column '{col}' found. Hits: {count}")
        else:
            print(f"[ERROR] Column '{col}' MISSING!")

    # Check for BOS/CHoCH specifically
    bos_count = result['bos'].sum()
    choch_count = result['choch'].sum()
    print(f"\nStructure analysis: {bos_count} BOS, {choch_count} CHoCH found.")
    
    # Check bias
    final_bias = result['trend_bias'].iloc[-1]
    bias_str = "BULLISH" if final_bias == 1 else "BEARISH" if final_bias == -1 else "NEUTRAL"
    print(f"Final Market Bias: {bias_str}")

if __name__ == "__main__":
    test_elite_logic()
