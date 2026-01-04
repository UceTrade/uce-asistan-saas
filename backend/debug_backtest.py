
import sys
import os
import pandas as pd
import numpy as np

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backtest_engine import BacktestEngine
from price_action_lib import PriceActionLib

def strategy_simple_ma(data, position):
    # Simple Moving Average Crossover
    # Only needs pandas
    if len(data) < 21: return 'HOLD'
    
    close = data['close']
    ma10 = close.rolling(10).mean().iloc[-1]
    ma20 = close.rolling(20).mean().iloc[-1]
    
    ma10_prev = close.rolling(10).mean().iloc[-2]
    ma20_prev = close.rolling(20).mean().iloc[-2]
    
    if ma10 > ma20 and ma10_prev <= ma20_prev:
        return 'BUY'
    elif ma10 < ma20 and ma10_prev >= ma20_prev:
        return 'SELL'
    return 'HOLD'

def strategy_pa_ob(data, position):
    # Tests Order Block Logic
    # Expects 'bullish_ob' column to exist
    if 'bullish_ob' not in data.columns:
        # If columns missing, try to calculate (should assume pre-calc but this is robust)
        # NOTE: In our engine, we pre-calc. Strategy receives slice.
        # But slice of df with cols HAS cols.
        return 'HOLD'

    # Check last bar
    # Note: Pre-calc logic has look-ahead unless careful.
    # But let's see if we see ANY True values.
    last = data.iloc[-1]
    
    if last['bullish_ob']:
        return 'BUY'
    if last['bearish_ob']:
        return 'SELL'
    return 'HOLD'

def run_debug():
    print("--- STARTING DEBUG ---")
    engine = BacktestEngine()
    
    # 1. Fetch Data (Mock or Real)
    # We'll try to fetch real data via MT5 if available, else mock.
    # Since we are in the user environment where MT5 is installed, let's try.
    # Or simpler: Create a dummy dataframe to be deterministic.
    
    print("Creating Synthetic Data...")
    dates = pd.date_range(start='2024-01-01', periods=500, freq='H')
    # Create a sine wave price + structure
    price = 100 + np.sin(np.linspace(0, 20, 500)) * 10 
    # Add some "Order Block" like moves (sharp drop then rise)
    price[50:55] = [95, 94, 93, 105, 106] # Sharp V
    price[100:105] = [110, 111, 112, 100, 99] # Sharp Inverted V
    
    df = pd.DataFrame({
        'time': dates,
        'open': price, # Simple mock
        'high': price + 1,
        'low': price - 1,
        'close': price,
        'volume': 1000
    })
    
    # Needs to be nicer for candles
    df['open'] = price - 0.5
    df['close'] = price + 0.5
    df['high'] = price + 2
    df['low'] = price - 2
    
    # 2. Test PA Library Logic Directly
    print("\nTesting PriceActionLib...")
    pa = PriceActionLib()
    df_pa = pa.analyze_all(df)
    
    print(f"Columns: {df_pa.columns.tolist()}")
    print(f"Swings Found: {df_pa['swing_high'].sum()} Highs, {df_pa['swing_low'].sum()} Lows")
    print(f"OBs Found: {df_pa['bullish_ob'].sum()} Bullish, {df_pa['bearish_ob'].sum()} Bearish")
    print(f"FVGs Found: {df_pa['bullish_fvg'].sum()} Bullish, {df_pa['bearish_fvg'].sum()} Bearish")
    
    # 3. Test Backtest Logic (Mocking fetch_data)
    print("\nTesting Backtest Engine (Simple MA)...")
    
    # We override get_historical_data to return our df
    engine.get_historical_data = lambda s, t, sd, ed: df
    
    # Code string for Simple MA
    code_ma = """
def strategy(data, position):
    if len(data) < 21: return 'HOLD'
    close = data['close']
    ma10 = close.rolling(10).mean().iloc[-1]
    ma20 = close.rolling(20).mean().iloc[-1]
    ma10_prev = close.rolling(10).mean().iloc[-2]
    ma20_prev = close.rolling(20).mean().iloc[-2]
    if ma10 > ma20 and ma10_prev <= ma20_prev: return 'BUY'
    elif ma10 < ma20 and ma10_prev >= ma20_prev: return 'SELL'
    return 'HOLD'
"""
    result_ma = engine.run_backtest(code_ma, 'TEST', 'H1', 10000, '2024-01-01', '2024-01-10')
    print("MA Results:", result_ma['metrics'])
    
    # 4. Test Backtest Logic (PA Strategy)
    print("\nTesting Backtest Engine (PA OB)...")
    code_pa = """
def strategy(data, position):
    # Try to use PA columns
    # Re-calc check?
    # df = pa.analyze_all(data) # Should be instant due to caching
    
    if len(data) < 5: return 'HOLD'
    last = data.iloc[-1]
    
    if last.get('bullish_ob', False): return 'BUY'
    if last.get('bearish_ob', False): return 'SELL'
    return 'HOLD'
"""
    result_pa = engine.run_backtest(code_pa, 'TEST', 'H1', 10000, '2024-01-01', '2024-01-10')
    print("PA Results:", result_pa.get('metrics', result_pa.get('error', 'Unknown Error')))
    print("Trades:", len(result_pa.get('trades', [])))

if __name__ == "__main__":
    run_debug()
