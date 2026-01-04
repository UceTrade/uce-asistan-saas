import pandas as pd
import numpy as np

def strategy(data, position):
    """
    Strategy: Buy when RSI < 30, Sell when RSI > 70
    """
    # Need at least 14 bars for RSI
    if len(data) < 14:
        return 'HOLD'
    
    # Calculate RSI
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    current_rsi = rsi.iloc[-1]
    
    # Trading logic
    if position == 0:  # No position
        if current_rsi < 30:
            return 'BUY'
        elif current_rsi > 70:
            return 'SELL'
    elif position == 1:  # Long position
        if current_rsi > 70:
            return 'SELL'  # Close long
    elif position == -1:  # Short position
        if current_rsi < 30:
            return 'BUY'  # Close short
    
    return 'HOLD'
