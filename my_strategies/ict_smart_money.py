"""
ICT Smart Money Strategy - Tested and Verified
Created: 2024-12-24
Performance: 137 trades, 15.14% return, $1,514 profit

This strategy uses ICT concepts:
- Trend Bias (bullish/bearish/neutral)
- Premium/Discount zones
- Fair Value Gaps (FVG)
- Order Blocks (OB)
"""
import pandas as pd
import numpy as np

def strategy(data, position):
    """
    ICT Smart Money Strategy - Relaxed Version
    
    Conditions (OR logic for flexibility):
    - BUY: Trend bullish/neutral AND (discount OR bullish_fvg OR bullish_ob)
    - SELL: Trend bearish/neutral AND (premium OR bearish_fvg OR bearish_ob)
    """
    # Ensure we have enough data
    if len(data) < 50:
        return 'HOLD'
    
    # Check if required columns exist (PA analysis should be pre-done by backtest engine)
    if 'trend_bias' not in data.columns:
        return 'HOLD'
    
    # Get the LAST value using .iloc[-1]
    trend = data['trend_bias'].iloc[-1] if 'trend_bias' in data.columns else 0
    is_discount = data['is_discount'].iloc[-1] if 'is_discount' in data.columns else False
    is_premium = data['is_premium'].iloc[-1] if 'is_premium' in data.columns else False
    bullish_fvg = data['bullish_fvg'].iloc[-1] if 'bullish_fvg' in data.columns else False
    bearish_fvg = data['bearish_fvg'].iloc[-1] if 'bearish_fvg' in data.columns else False
    bullish_ob = data['bullish_ob'].iloc[-1] if 'bullish_ob' in data.columns else False
    bearish_ob = data['bearish_ob'].iloc[-1] if 'bearish_ob' in data.columns else False
    
    # BUY: Trend neutral/bullish AND (discount OR FVG OR OB)
    if trend >= 0 and (is_discount or bullish_fvg or bullish_ob):
        if position <= 0:
            return 'BUY'
    
    # SELL: Trend neutral/bearish AND (premium OR FVG OR OB)
    if trend <= 0 and (is_premium or bearish_fvg or bearish_ob):
        if position >= 0:
            return 'SELL'
    
    return 'HOLD'
