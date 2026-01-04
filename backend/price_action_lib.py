"""
Price Action Library - Core logic for ICT and Price Action concepts
"""
import pandas as pd
import numpy as np

class PriceActionLib:
    """
    Library of Price Action functions to be used by the AI Strategy Engine.
    Exposed as 'pa' in the strategy execution namespace.
    """
    
    def identify_swings(self, data: pd.DataFrame, length: int = 5) -> pd.DataFrame:
        """
        Identify Swing Highs and Swing Lows (Fractals).
        Adds 'swing_high' and 'swing_low' columns (boolean).
        """
        df = data.copy()
        
        # Shift logic to find local min/max
        # A swing high is higher than 'length' bars before and after it
        # Note: This looks into the future for backtesting, but for live trading
        # it would signal 'length' bars late. We simulate this lag.
        
        # Simple Pivot Logic (High > neighbors)
        # Using a centered window approach for historical identification
        
        df['swing_high'] = False
        df['swing_low'] = False
        
        # We need to iterate or use rolling. Rolling is faster.
        # Max of window centered at i
        # But for strategy execution bar-by-bar, we can only know a swing formed 'length' bars ago.
        # So we identify swings that are confirmed.
        
        # Optimized vectorized swing detection
        # High[i] > High[i-1]...High[i-L] AND High[i] > High[i+1]...High[i+L]
        
        # For simplicity and speed in this version, we use a 3-bar pivot (Fractal)
        # High > Left and High > Right
        
        # Left side check
        left_high = df['high'].shift(1) < df['high']
        right_high = df['high'].shift(-1) < df['high']
        left_low = df['low'].shift(1) > df['low']
        right_low = df['low'].shift(-1) > df['low']
        
        # For length > 1, we would need more shifts. Keeping it simple (Fractal style)
        if length >= 2:
            left_high = left_high & (df['high'].shift(2) < df['high'])
            right_high = right_high & (df['high'].shift(-2) < df['high'])
            left_low = left_low & (df['low'].shift(2) > df['low'])
            right_low = right_low & (df['low'].shift(-2) > df['low'])
            
        df.loc[left_high & right_high, 'swing_high'] = True
        df.loc[left_low & right_low, 'swing_low'] = True
        
        return df

    def detect_order_blocks(self, data: pd.DataFrame, lookback: int = 50) -> pd.DataFrame:
        """
        Identify Order Blocks.
        Bullish OB: The last bearish candle before a strong bullish move that breaks structure (Swings).
        Bearish OB: The last bullish candle before a strong bearish move that breaks structure.
        """
        # Optimization: Return if already calculated
        if 'bullish_ob' in data.columns and 'bearish_ob' in data.columns:
            return data.copy()

        df = self.identify_swings(data, length=3)
        df['bullish_ob'] = False
        df['bearish_ob'] = False
        df['ob_top'] = np.nan
        df['ob_bottom'] = np.nan
        
        # Provide raw boolean arrays for faster loop access
        opens = df['open'].values
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        
        # Iterate to find patterns (optimized where possible is better, but OB logic is complex)
        # We look for a Swing High being broken
        
        # Simplified Logic for AI usage:
        # Bullish OB = Down Candle followed by series of Up candles breaking a local high
        
        for i in range(20, len(df) - 5): # Simple scan range
            # 1. Identify Candle Color
            is_down = closes[i] < opens[i]
            is_up = closes[i] > opens[i]
            
            # Potential Bullish OB: Must be a down candle (or small doji)
            if is_down:
                # RELAXED LOGIC: Check for strong reaction (Next candle is strong UP)
                # Broke structure or just engulfed?
                # Let's simple look for Engulfing + Follow through OR just strong move
                
                if closes[i+1] > opens[i+1] and closes[i+1] > highs[i]:
                    # Engulfing / Strong move up
                    # Check break of local high within 10 bars
                    # Fix: Ensure indices are within bounds and valid range
                    start_idx = max(0, i-10)
                    if i > start_idx:
                        recent_high = np.max(highs[start_idx:i])
                        if np.max(closes[i+1:min(len(closes), i+4)]) > recent_high:
                             df.at[i, 'bullish_ob'] = True
                             df.at[i, 'ob_top'] = highs[i]
                             df.at[i, 'ob_bottom'] = lows[i]

            # Potential Bearish OB
            if is_up:
                # RELAXED LOGIC
                if closes[i+1] < opens[i+1] and closes[i+1] < lows[i]:
                    # Check break of recent low
                    start_idx = max(0, i-10)
                    if i > start_idx:
                        recent_low = np.min(lows[start_idx:i])
                        if np.min(closes[i+1:min(len(closes), i+4)]) < recent_low:
                            df.at[i, 'bearish_ob'] = True
                            df.at[i, 'ob_top'] = highs[i]
                            df.at[i, 'ob_bottom'] = lows[i]
                        
        return df

    def detect_fvg(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Identify Fair Value Gaps (FVG).
        Bullish FVG: Low of candle 3 > High of candle 1 (Gap between them)
        Bearish FVG: High of candle 3 < Low of candle 1
        """
        df = data.copy()
        
        high = df['high']
        low = df['low']
        
        # Shift to align Candle 1, 2, 3
        # If we are at index i (Candle 3):
        # Candle 1 is at i-2
        
        # Optimization: Return if already calculated
        if 'bullish_fvg' in df.columns and 'bearish_fvg' in df.columns:
            return df
        
        # Bullish FVG
        # Low[i] > High[i-2]
        # Current candle (i) is usually Green and (i-1) is large Green
        df['bullish_fvg'] = (low > high.shift(2)) & (df['close'] > df['open'])
        
        # Bearish FVG
        # High[i] < Low[i-2]
        df['bearish_fvg'] = (high < low.shift(2)) & (df['close'] < df['open'])
        
        # Store Gap Levels
        df['fvg_top'] = np.where(df['bullish_fvg'], df['low'], np.where(df['bearish_fvg'], df['low'].shift(2), np.nan))
        df['fvg_bottom'] = np.where(df['bullish_fvg'], df['high'].shift(2), np.where(df['bearish_fvg'], df['high'], np.nan))
        
        return df

    def get_market_structure(self, data: pd.DataFrame) -> str:
        """
        Determine simple market structure bias.
        Returns: 'BULLISH', 'BEARISH', or 'RANGING'
        """
        df = self.identify_swings(data, length=5)
        
        # Get last 2 swing highs and lows
        last_highs = df[df['swing_high']]['high'].tail(2).values
        last_lows = df[df['swing_low']]['low'].tail(2).values
        
        if len(last_highs) < 2 or len(last_lows) < 2:
            return 'RANGING'
            
        hh = last_highs[1] > last_highs[0] # Higher High
        hl = last_lows[1] > last_lows[0]   # Higher Low
        
        lh = last_highs[1] < last_highs[0] # Lower High
        ll = last_lows[1] < last_lows[0]   # Lower Low
        
        if hh and hl:
            return 'BULLISH'
        elif lh and ll:
            return 'BEARISH'
        
        return 'RANGING'

    def detect_structure(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Detect BOS (Break of Structure) and CHoCH (Change of Character).
        BOS: Trend continuation (HH broken in uptrend, LL broken in downtrend).
        CHoCH: Trend reversal (LH broken in downtrend, HL broken in uptrend).
        """
        df = self.identify_swings(data, length=5)
        df['bos'] = False
        df['choch'] = False
        df['trend_bias'] = 0 # 1 for bullish, -1 for bearish
        
        current_bias = 0
        last_high = np.nan
        last_low = np.nan
        
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        # We need a loop to maintain 'state' of the market structure
        for i in range(10, len(df)):
            # Update last confirmed swings
            if df.at[i-5, 'swing_high']:
                last_high = highs[i-5]
            if df.at[i-5, 'swing_low']:
                last_low = lows[i-5]
                
            if np.isnan(last_high) or np.isnan(last_low):
                continue
                
            # BULLISH BREAKOUTS
            if closes[i] > last_high:
                if current_bias == 1:
                    df.at[i, 'bos'] = True
                elif current_bias == -1:
                    df.at[i, 'choch'] = True
                    current_bias = 1
                else:
                    current_bias = 1 # Initial bias set
                last_high = np.nan # Reset until next swing confirmed
                
            # BEARISH BREAKOUTS
            elif closes[i] < last_low:
                if current_bias == -1:
                    df.at[i, 'bos'] = True
                elif current_bias == 1:
                    df.at[i, 'choch'] = True
                    current_bias = -1
                else:
                    current_bias = -1 # Initial bias set
                last_low = np.nan # Reset until next swing confirmed
            
            df.at[i, 'trend_bias'] = current_bias
            
        return df

    def detect_liquidity(self, data: pd.DataFrame, threshold_percent: float = 0.05) -> pd.DataFrame:
        """
        Detect Equal Highs (EQH) and Equal Lows (EQL) - Liquidity Pools.
        Also detects Liquidity Sweeps (Price takes a swing then reverses).
        """
        df = data.copy()
        df = self.identify_swings(df, length=5)
        df['eqh'] = False
        df['eql'] = False
        df['eqh_price'] = np.nan
        df['eql_price'] = np.nan
        df['sweep_high'] = False
        df['sweep_low'] = False
        
        highs = df['high'].values
        lows = df['low'].values
        
        # 1. Detect EQH/EQL (Price clustering at similar levels)
        # We look for historical swing points that are very close to each other
        swing_highs = df[df['swing_high']]['high'].tail(5).values
        swing_lows = df[df['swing_low']]['low'].tail(5).values
        
        if len(swing_highs) >= 2:
            if abs(swing_highs[-1] - swing_highs[-2]) / swing_highs[-1] < (threshold_percent / 100):
                df.at[df.index[-1], 'eqh'] = True
                df.at[df.index[-1], 'eqh_price'] = swing_highs[-1]
                
        if len(swing_lows) >= 2:
            if abs(swing_lows[-1] - swing_lows[-2]) / swing_lows[-1] < (threshold_percent / 100):
                df.at[df.index[-1], 'eql'] = True
                df.at[df.index[-1], 'eql_price'] = swing_lows[-1]

        # 2. Detect Liquidity Sweeps
        # Price spikes above a recent swing high then closes below it
        for i in range(20, len(df)):
            # Look back for previous swing high
            prev_highs = df['high'].iloc[i-20:i][df['swing_high'].iloc[i-20:i]]
            if not prev_highs.empty:
                recent_target = prev_highs.max()
                if highs[i] > recent_target and df['close'].iloc[i] < recent_target:
                    df.at[df.index[i], 'sweep_high'] = True
            
            # Look back for previous swing low
            prev_lows = df['low'].iloc[i-20:i][df['swing_low'].iloc[i-20:i]]
            if not prev_lows.empty:
                recent_target = prev_lows.min()
                if lows[i] < recent_target and df['close'].iloc[i] > recent_target:
                    df.at[df.index[i], 'sweep_low'] = True
                    
        return df

    def get_premium_discount(self, data: pd.DataFrame, lookback: int = 100) -> pd.DataFrame:
        """
        Calculate Premium/Discount zones based on current dealing range.
        Equilibrium = (Range High + Range Low) / 2
        Premium = > Equilibrium (Sell zone)
        Discount = < Equilibrium (Buy zone)
        """
        df = data.copy()
        df['range_high'] = df['high'].rolling(lookback).max()
        df['range_low'] = df['low'].rolling(lookback).min()
        df['equilibrium'] = (df['range_high'] + df['range_low']) / 2
        
        df['is_discount'] = df['close'] < df['equilibrium']
        df['is_premium'] = df['close'] > df['equilibrium']
        
        # Percent into range (0 to 1)
        df['range_pct'] = (df['close'] - df['range_low']) / (df['range_high'] - df['range_low'])
        
        return df

    def is_in_zone(self, price, zone_top, zone_bottom, threshold_pips=5):
        """Helper to check if price is reacting to a zone (OB/FVG)"""
        # A simple proximity check
        # threshold is roughly converted (assuming standard Forex 0.0001 or 0.01)
        tol = threshold_pips * 0.0001
        
        upper = max(zone_top, zone_bottom) + tol
        lower = min(zone_top, zone_bottom) - tol
        
        return lower <= price <= upper
        
    def analyze_all(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Run ALL Price Action detection algorithms.
        Returns DataFrame with ALL PA columns:
        - swing_high, swing_low
        - bullish_ob, bearish_ob, ob_top, ob_bottom
        - bullish_fvg, bearish_fvg, fvg_top, fvg_bottom
        - bos, choch, trend_bias
        - eqh, eql, sweep_high, sweep_low
        - range_high, range_low, equilibrium, is_discount, is_premium
        """
        # 1. OBs & Swings
        df = self.detect_order_blocks(data)
        
        # 2. FVGs
        df = self.detect_fvg(df)
        
        # 3. Market Structure (BOS/CHoCH)
        df = self.detect_structure(df)
        
        # 4. Liquidity
        df = self.detect_liquidity(df)
        
        # 5. Premium/Discount
        df = self.get_premium_discount(df)
        
        # 6. Confluence Scoring
        df = self.calculate_confluence_scores(df)
            
        return df

    def calculate_confluence_scores(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates a weighted confluence score (0-100) for each bar.
        Weights:
        - Trend Bias: 30 pts
        - Liquidity Sweep: 25 pts
        - CHoCH (Trend Change): 20 pts
        - OB/FVG Proximity: 15 pts
        - Premium/Discount Alignment: 10 pts
        """
        df = data.copy()
        df['confluence_score'] = 0.0
        
        # 1. Trend Alignment (30 pts)
        # Score is high if we match the latest trend_bias
        df['confluence_score'] += np.where(df['trend_bias'] != 0, 30, 0)
        
        # 2. Liquidity Sweeps (25 pts)
        df['confluence_score'] += np.where(df['sweep_high'] | df['sweep_low'], 25, 0)
        
        # 3. CHoCH - Change of Character (20 pts)
        df['confluence_score'] += np.where(df['choch'], 20, 0)
        
        # 4. OB/FVG Presence (15 pts)
        df['confluence_score'] += np.where(df['bullish_ob'] | df['bearish_ob'] | df['bullish_fvg'] | df['bearish_fvg'], 15, 0)
        
        # 5. Premium/Discount Alignment (10 pts)
        # Bullish + Discount = Good (10 pts)
        # Bearish + Premium = Good (10 pts)
        bull_align = (df['trend_bias'] == 1) & df['is_discount']
        bear_align = (df['trend_bias'] == -1) & df['is_premium']
        df['confluence_score'] += np.where(bull_align | bear_align, 10, 0)
        
        return df
