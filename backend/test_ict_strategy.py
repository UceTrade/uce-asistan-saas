"""
Test ICT Strategy with relaxed conditions - for debugging
"""
import pandas as pd
import numpy as np

def strategy(data, position):
    """
    ICT Smart Money Strategy - Relaxed Version
    
    Conditions (OR logic instead of AND):
    - BUY: Trend bullish AND (discount OR bullish_fvg OR bullish_ob)
    - SELL: Trend bearish AND (premium OR bearish_fvg OR bearish_ob)
    """
    # Ensure we have enough data
    if len(data) < 50:
        return 'HOLD'
    
    # Get last bar values
    trend = data['trend_bias'].iloc[-1] if 'trend_bias' in data.columns else 0
    
    # Check for discount/premium zones
    is_discount = data['is_discount'].iloc[-1] if 'is_discount' in data.columns else False
    is_premium = data['is_premium'].iloc[-1] if 'is_premium' in data.columns else False
    
    # Check for FVG
    bullish_fvg = data['bullish_fvg'].iloc[-1] if 'bullish_fvg' in data.columns else False
    bearish_fvg = data['bearish_fvg'].iloc[-1] if 'bearish_fvg' in data.columns else False
    
    # Check for Order Blocks
    bullish_ob = data['bullish_ob'].iloc[-1] if 'bullish_ob' in data.columns else False
    bearish_ob = data['bearish_ob'].iloc[-1] if 'bearish_ob' in data.columns else False
    
    # BUY CONDITIONS (Relaxed - only need ONE of these + trend)
    buy_signal = False
    if trend >= 0:  # Neutral or bullish trend
        if is_discount or bullish_fvg or bullish_ob:
            buy_signal = True
    
    # SELL CONDITIONS (Relaxed)
    sell_signal = False
    if trend <= 0:  # Neutral or bearish trend
        if is_premium or bearish_fvg or bearish_ob:
            sell_signal = True
    
    # Execute
    if buy_signal and position <= 0:
        return 'BUY'
    elif sell_signal and position >= 0:
        return 'SELL'
    
    return 'HOLD'


# Test function
if __name__ == "__main__":
    from price_action_lib import PriceActionLib
    import MetaTrader5 as mt5
    from datetime import datetime, timedelta
    
    mt5.initialize()
    
    # Get test data
    end = datetime.now()
    start = end - timedelta(days=30)
    rates = mt5.copy_rates_range("EURUSD", mt5.TIMEFRAME_H1, start, end)
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.rename(columns={'tick_volume': 'volume'})
    
    # Apply PA analysis
    pa = PriceActionLib()
    df = pa.analyze_all(df)
    
    # Count signals
    signals = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
    for i in range(50, len(df)):
        sig = strategy(df.iloc[:i+1], 0)
        signals[sig] += 1
    
    print(f"\\nSignal Distribution (30 days, H1):")
    print(f"  BUY:  {signals['BUY']}")
    print(f"  SELL: {signals['SELL']}")
    print(f"  HOLD: {signals['HOLD']}")
    
    # Check PA column stats
    print(f"\\nPA Column Analysis:")
    print(f"  Bullish OB:  {df['bullish_ob'].sum()} occurrences")
    print(f"  Bearish OB:  {df['bearish_ob'].sum()} occurrences")
    print(f"  Bullish FVG: {df['bullish_fvg'].sum()} occurrences")
    print(f"  Bearish FVG: {df['bearish_fvg'].sum()} occurrences")
    print(f"  Sweep High:  {df['sweep_high'].sum()} occurrences")
    print(f"  Sweep Low:   {df['sweep_low'].sum()} occurrences")
    print(f"  Discount:    {df['is_discount'].sum()} bars")
    print(f"  Premium:     {df['is_premium'].sum()} bars")
