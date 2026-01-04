"""
Test script to verify the pandas Series conversion fix
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from backtest_engine import BacktestEngine
import pandas as pd
import numpy as np

# Test strategy that intentionally returns a Series (common AI mistake)
BAD_STRATEGY = """
import pandas as pd
import numpy as np

def strategy(data, position):
    if len(data) < 20:
        return 'HOLD'
    
    # Calculate simple moving average
    sma = data['close'].rolling(window=20).mean()
    
    # WRONG: This returns a Series, not a string
    # The backtest engine should now handle this gracefully
    signal = pd.Series(['HOLD'] * len(data))
    signal.iloc[-1] = 'BUY' if data['close'].iloc[-1] > sma.iloc[-1] else 'SELL'
    
    return signal  # Returns Series instead of string
"""

# Test strategy with correct implementation
GOOD_STRATEGY = """
import pandas as pd
import numpy as np

def strategy(data, position):
    if len(data) < 20:
        return 'HOLD'
    
    # Calculate simple moving average
    sma = data['close'].rolling(window=20).mean()
    
    # CORRECT: Extract the last value and return a string
    current_price = data['close'].iloc[-1]
    current_sma = sma.iloc[-1]
    
    if current_price > current_sma and position <= 0:
        return 'BUY'
    elif current_price < current_sma and position >= 0:
        return 'SELL'
    
    return 'HOLD'
"""

def test_backtest():
    """Test both bad and good strategies"""
    engine = BacktestEngine()
    
    print("=" * 60)
    print("Testing FIXED Backtest Engine")
    print("=" * 60)
    
    # Test with BAD strategy (should now work thanks to our fix)
    print("\n[TEST 1] Testing BAD strategy (returns Series)...")
    print("Expected: Should handle gracefully and convert to string")
    
    result = engine.run_backtest(
        strategy_code=BAD_STRATEGY,
        symbol='EURUSD',
        timeframe='H1',
        initial_balance=10000,
        start_date='2024-11-01',
        end_date='2024-11-15',
        lot_size=0.01
    )
    
    if result['success']:
        print("[SUCCESS] Bad strategy handled gracefully")
        print(f"   Total trades: {result['metrics']['total_trades']}")
    else:
        print(f"[FAILED] {result['error']}")
    
    # Test with GOOD strategy
    print("\n[TEST 2] Testing GOOD strategy (returns string)...")
    print("Expected: Should work perfectly")
    
    result = engine.run_backtest(
        strategy_code=GOOD_STRATEGY,
        symbol='EURUSD',
        timeframe='H1',
        initial_balance=10000,
        start_date='2024-11-01',
        end_date='2024-11-15',
        lot_size=0.01
    )
    
    if result['success']:
        print("[SUCCESS] Good strategy works as expected")
        print(f"   Total trades: {result['metrics']['total_trades']}")
        print(f"   Win rate: {result['metrics']['win_rate']}%")
        print(f"   Net profit: ${result['metrics']['net_profit']}")
    else:
        print(f"[FAILED] {result['error']}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == '__main__':
    test_backtest()
