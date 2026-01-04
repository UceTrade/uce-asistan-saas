"""
Forecasting Engine (The Oracle)
Projects future price paths based on SMC structure.
"""
import pandas as pd
import numpy as np

class ForecastingEngine:
    def __init__(self, pa_lib):
        self.pa = pa_lib

    def project_paths(self, df):
        """
        Generates 2-3 likely paths for the next 24-48 hours.
        Returns a list of coordinate sets for the UI to draw.
        """
        latest = df.iloc[-1]
        price = latest['close']
        bias = latest.get('trend_bias', 0)
        
        # 1. Identify Key Targets (Unfilled FVG, OB, Liquidity Pools)
        targets = []
        
        # Pull latest FVG/OB from data
        # We look for the nearest 'unfilled' ones
        # For simplicity, we'll take the most recent detected ones
        
        if latest.get('bullish_fvg'):
            targets.append({'price': latest['fvg_bottom'], 'type': 'BULL_FVG', 'weight': 0.8})
        if latest.get('bearish_fvg'):
            targets.append({'price': latest['fvg_top'], 'type': 'BEAR_FVG', 'weight': 0.8})
        
        # Equilibrium is always a target
        targets.append({'price': latest.get('equilibrium', price), 'type': 'EQ', 'weight': 0.5})

        # 2. Build Scenario A (The Primary Trend Follower)
        path_a = self._build_path(price, bias, targets, scenario='primary')
        
        # 3. Build Scenario B (The Reversal / Liquidity Grab)
        path_b = self._build_path(price, -bias if bias != 0 else 1, targets, scenario='reversal')

        return {
            'primary': path_a,
            'secondary': path_b
        }

    def _build_path(self, start_price, bias, targets, scenario='primary'):
        """Generates a simple zigzag path towards logical targets"""
        path = [{'x': 0, 'y': start_price}]
        
        # Simple heuristic:
        # If Bullish Bias, target nearest High Liquidity or Bearish OB
        # If Bearish Bias, target nearest Low Liquidity or Bullish OB
        
        step_x = 10 # Units of "time" in UI
        volatility = start_price * 0.001
        
        current_y = start_price
        
        for i in range(1, 4):
            # Add some "noise" zigzag
            offset = (bias * volatility * 2) if scenario == 'primary' else (-bias * volatility * 2)
            noise = (np.random.random() - 0.5) * volatility
            
            target_y = current_y + offset + noise
            path.append({'x': i * step_x, 'y': target_y})
            current_y = target_y
            
        return path
