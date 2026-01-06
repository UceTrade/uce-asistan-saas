"""
Multi-Timeframe Analysis Module
Analyzes multiple timeframes to identify trend alignment and high-probability setups
"""

from mt5_proxy import mt5
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional


class MultiTimeframeAnalyzer:
    """
    Analyzes multiple timeframes for confluence trading signals
    Uses HTF (Higher Timeframe) for trend, MTF (Medium) for zones, LTF (Lower) for entries
    """
    
    # Timeframe mappings
    TIMEFRAMES = {
        'M1': mt5.TIMEFRAME_M1,
        'M5': mt5.TIMEFRAME_M5,
        'M15': mt5.TIMEFRAME_M15,
        'M30': mt5.TIMEFRAME_M30,
        'H1': mt5.TIMEFRAME_H1,
        'H4': mt5.TIMEFRAME_H4,
        'D1': mt5.TIMEFRAME_D1,
        'W1': mt5.TIMEFRAME_W1
    }
    
    # Default timeframe combinations
    PRESETS = {
        'scalping': {'htf': 'H1', 'mtf': 'M15', 'ltf': 'M5'},
        'intraday': {'htf': 'H4', 'mtf': 'H1', 'ltf': 'M15'},
        'swing': {'htf': 'D1', 'mtf': 'H4', 'ltf': 'H1'},
        'position': {'htf': 'W1', 'mtf': 'D1', 'ltf': 'H4'}
    }
    
    def __init__(self):
        self.cache = {}
        self.cache_expiry = 60  # seconds
    
    def analyze(self, symbol: str, preset: str = 'intraday', 
                custom_tfs: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Perform multi-timeframe analysis on a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            preset: Preset timeframe combination ('scalping', 'intraday', 'swing', 'position')
            custom_tfs: Custom timeframe dict {'htf': 'D1', 'mtf': 'H1', 'ltf': 'M15'}
            
        Returns:
            Complete MTF analysis with trend, zones, and signals
        """
        # Get timeframes
        if custom_tfs:
            tfs = custom_tfs
        else:
            tfs = self.PRESETS.get(preset, self.PRESETS['intraday'])
        
        # Fetch data for all timeframes
        htf_data = self._get_data(symbol, tfs['htf'], bars=100)
        mtf_data = self._get_data(symbol, tfs['mtf'], bars=200)
        ltf_data = self._get_data(symbol, tfs['ltf'], bars=300)
        
        if htf_data is None or mtf_data is None or ltf_data is None:
            return {'error': f'Failed to get data for {symbol}'}
        
        # Analyze each timeframe
        htf_analysis = self._analyze_timeframe(htf_data, 'HTF')
        mtf_analysis = self._analyze_timeframe(mtf_data, 'MTF')
        ltf_analysis = self._analyze_timeframe(ltf_data, 'LTF')
        
        # Calculate confluence
        confluence = self._calculate_confluence(htf_analysis, mtf_analysis, ltf_analysis)
        
        # Generate trading decision
        decision = self._generate_decision(confluence, htf_analysis, mtf_analysis, ltf_analysis)
        
        return {
            'symbol': symbol,
            'preset': preset,
            'timeframes': {
                'htf': tfs['htf'],
                'mtf': tfs['mtf'],
                'ltf': tfs['ltf']
            },
            'htf_analysis': htf_analysis,
            'mtf_analysis': mtf_analysis,
            'ltf_analysis': ltf_analysis,
            'confluence': confluence,
            'decision': decision,
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_data(self, symbol: str, timeframe: str, bars: int = 100) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data from MT5"""
        tf = self.TIMEFRAMES.get(timeframe)
        if tf is None:
            return None
            
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
        if rates is None or len(rates) == 0:
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    
    def _analyze_timeframe(self, df: pd.DataFrame, tf_type: str) -> Dict[str, Any]:
        """Analyze a single timeframe"""
        # Calculate indicators
        df = self._add_indicators(df)
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Trend analysis
        trend = self._determine_trend(df)
        
        # Market structure
        structure = self._analyze_structure(df)
        
        # Key levels
        levels = self._find_key_levels(df)
        
        # Momentum
        momentum = self._analyze_momentum(df)
        
        # Current price position
        price_position = self._get_price_position(df)
        
        return {
            'type': tf_type,
            'current_price': float(latest['close']),
            'trend': trend,
            'structure': structure,
            'levels': levels,
            'momentum': momentum,
            'price_position': price_position,
            'sma_20': float(latest.get('sma_20', 0)),
            'sma_50': float(latest.get('sma_50', 0)),
            'rsi': float(latest.get('rsi', 50))
        }
    
    def _add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to dataframe"""
        # SMA
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=min(200, len(df)-1)).mean()
        
        # EMA
        df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14).mean()
        
        # Swing points
        df['swing_high'] = df['high'].rolling(window=5, center=True).max() == df['high']
        df['swing_low'] = df['low'].rolling(window=5, center=True).min() == df['low']
        
        return df
    
    def _determine_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Determine trend direction and strength"""
        latest = df.iloc[-1]
        
        # Price position relative to MAs
        above_sma_20 = latest['close'] > latest['sma_20']
        above_sma_50 = latest['close'] > latest['sma_50']
        above_sma_200 = latest['close'] > latest.get('sma_200', latest['sma_50'])
        
        # EMA alignment
        ema_bullish = latest['ema_9'] > latest['ema_21']
        
        # Higher highs / Lower lows check
        recent_highs = df['high'].tail(20)
        recent_lows = df['low'].tail(20)
        
        hh = recent_highs.iloc[-1] > recent_highs.iloc[0]  # Higher high
        hl = recent_lows.iloc[-1] > recent_lows.iloc[0]    # Higher low
        
        # Determine direction
        bullish_points = sum([above_sma_20, above_sma_50, above_sma_200, ema_bullish, hh, hl])
        
        if bullish_points >= 5:
            direction = 'BULLISH'
            strength = 'strong'
        elif bullish_points >= 4:
            direction = 'BULLISH'
            strength = 'moderate'
        elif bullish_points >= 3:
            direction = 'NEUTRAL'
            strength = 'weak'
        elif bullish_points >= 2:
            direction = 'BEARISH'
            strength = 'moderate'
        else:
            direction = 'BEARISH'
            strength = 'strong'
        
        return {
            'direction': direction,
            'strength': strength,
            'score': bullish_points,
            'above_sma_20': above_sma_20,
            'above_sma_50': above_sma_50,
            'ema_aligned': ema_bullish
        }
    
    def _analyze_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze market structure (BOS, CHoCH)"""
        highs = df[df['swing_high'] == True]['high'].values
        lows = df[df['swing_low'] == True]['low'].values
        
        if len(highs) < 2 or len(lows) < 2:
            return {'type': 'UNCLEAR', 'bos': False, 'choch': False}
        
        # Check for Break of Structure
        last_high = highs[-1] if len(highs) > 0 else 0
        prev_high = highs[-2] if len(highs) > 1 else 0
        last_low = lows[-1] if len(lows) > 0 else 0
        prev_low = lows[-2] if len(lows) > 1 else 0
        
        bos_bullish = last_high > prev_high  # Higher high
        bos_bearish = last_low < prev_low    # Lower low
        
        # Simplified structure determination
        if bos_bullish and not bos_bearish:
            structure_type = 'BULLISH'
        elif bos_bearish and not bos_bullish:
            structure_type = 'BEARISH'
        else:
            structure_type = 'RANGING'
        
        return {
            'type': structure_type,
            'bos': bos_bullish or bos_bearish,
            'last_swing_high': float(last_high),
            'last_swing_low': float(last_low)
        }
    
    def _find_key_levels(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Find key support and resistance levels"""
        highs = df[df['swing_high'] == True]['high'].tail(5).values.tolist()
        lows = df[df['swing_low'] == True]['low'].tail(5).values.tolist()
        
        current_price = df.iloc[-1]['close']
        
        # Find nearest resistance and support
        resistances = [h for h in highs if h > current_price]
        supports = [l for l in lows if l < current_price]
        
        nearest_resistance = min(resistances) if resistances else None
        nearest_support = max(supports) if supports else None
        
        return {
            'resistance': resistances[:3] if resistances else [],
            'support': supports[:3] if supports else [],
            'nearest_resistance': float(nearest_resistance) if nearest_resistance else None,
            'nearest_support': float(nearest_support) if nearest_support else None
        }
    
    def _analyze_momentum(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze momentum using RSI and price action"""
        latest = df.iloc[-1]
        rsi = latest['rsi']
        
        # RSI zones
        if rsi >= 70:
            rsi_zone = 'overbought'
        elif rsi <= 30:
            rsi_zone = 'oversold'
        elif rsi >= 60:
            rsi_zone = 'bullish'
        elif rsi <= 40:
            rsi_zone = 'bearish'
        else:
            rsi_zone = 'neutral'
        
        # Price momentum (recent candles)
        recent_closes = df['close'].tail(5)
        momentum_up = (recent_closes.diff() > 0).sum() >= 3
        
        return {
            'rsi': float(rsi),
            'rsi_zone': rsi_zone,
            'is_bullish': momentum_up,
            'description': f"RSI {rsi:.1f} ({rsi_zone})"
        }
    
    def _get_price_position(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Determine current price position in range"""
        latest = df.iloc[-1]
        
        # Calculate range (last 20 bars)
        recent_high = df['high'].tail(20).max()
        recent_low = df['low'].tail(20).min()
        current = latest['close']
        
        range_size = recent_high - recent_low
        position = (current - recent_low) / range_size if range_size > 0 else 0.5
        
        # Determine zone
        if position >= 0.8:
            zone = 'premium'
            zone_name = 'Premium Zone (Üst)'
        elif position <= 0.2:
            zone = 'discount'
            zone_name = 'Discount Zone (Alt)'
        elif position >= 0.5:
            zone = 'upper_equilibrium'
            zone_name = 'Üst Denge'
        else:
            zone = 'lower_equilibrium'
            zone_name = 'Alt Denge'
        
        return {
            'zone': zone,
            'zone_name': zone_name,
            'position_percent': round(position * 100, 1),
            'range_high': float(recent_high),
            'range_low': float(recent_low)
        }
    
    def _calculate_confluence(self, htf: Dict, mtf: Dict, ltf: Dict) -> Dict[str, Any]:
        """Calculate confluence score across timeframes"""
        score = 0
        max_score = 10
        factors = []
        
        # HTF trend alignment (3 points)
        if htf['trend']['direction'] != 'NEUTRAL':
            score += 2
            factors.append(f"HTF trend: {htf['trend']['direction']}")
            if htf['trend']['strength'] == 'strong':
                score += 1
                factors.append("HTF trend güçlü")
        
        # MTF alignment with HTF (2 points)
        if htf['trend']['direction'] == mtf['trend']['direction']:
            score += 2
            factors.append("HTF-MTF trend uyumu ✓")
        
        # LTF entry zone (2 points)
        ltf_in_discount = ltf['price_position']['zone'] == 'discount'
        ltf_in_premium = ltf['price_position']['zone'] == 'premium'
        
        if htf['trend']['direction'] == 'BULLISH' and ltf_in_discount:
            score += 2
            factors.append("LTF discount bölgesinde (Alış için ideal)")
        elif htf['trend']['direction'] == 'BEARISH' and ltf_in_premium:
            score += 2
            factors.append("LTF premium bölgesinde (Satış için ideal)")
        
        # Momentum alignment (2 points)
        all_bullish = all([
            htf['momentum']['is_bullish'],
            mtf['momentum']['is_bullish'],
            ltf['momentum']['is_bullish']
        ])
        all_bearish = not any([
            htf['momentum']['is_bullish'],
            mtf['momentum']['is_bullish'],
            ltf['momentum']['is_bullish']
        ])
        
        if all_bullish or all_bearish:
            score += 2
            factors.append("Tüm TF'lerde momentum uyumu")
        
        # RSI not extreme in HTF (1 point)
        htf_rsi = htf['momentum']['rsi']
        if 30 < htf_rsi < 70:
            score += 1
            factors.append("HTF RSI aşırı değil")
        
        # Calculate percentage
        percentage = (score / max_score) * 100
        
        # Determine strength
        if percentage >= 70:
            strength = 'STRONG'
            strength_tr = 'GÜÇLÜ'
        elif percentage >= 50:
            strength = 'MODERATE'
            strength_tr = 'ORTA'
        else:
            strength = 'WEAK'
            strength_tr = 'ZAYIF'
        
        return {
            'score': score,
            'max_score': max_score,
            'percentage': round(percentage, 1),
            'strength': strength,
            'strength_tr': strength_tr,
            'factors': factors
        }
    
    def _generate_decision(self, confluence: Dict, htf: Dict, mtf: Dict, ltf: Dict) -> Dict[str, Any]:
        """Generate trading decision based on analysis"""
        
        # Determine direction
        htf_dir = htf['trend']['direction']
        mtf_dir = mtf['trend']['direction']
        
        if htf_dir == mtf_dir and htf_dir != 'NEUTRAL':
            direction = 'BUY' if htf_dir == 'BULLISH' else 'SELL'
            aligned = True
        else:
            direction = 'WAIT'
            aligned = False
        
        # Check for entry conditions
        entry_ready = False
        entry_reason = ""
        
        if aligned:
            ltf_zone = ltf['price_position']['zone']
            
            if direction == 'BUY' and ltf_zone in ['discount', 'lower_equilibrium']:
                entry_ready = True
                entry_reason = "LTF discount/alt denge bölgesinde - Alış fırsatı"
            elif direction == 'SELL' and ltf_zone in ['premium', 'upper_equilibrium']:
                entry_ready = True
                entry_reason = "LTF premium/üst denge bölgesinde - Satış fırsatı"
            else:
                entry_reason = "LTF henüz ideal giriş bölgesinde değil"
        else:
            entry_reason = "Timeframe'ler uyumsuz - Bekleme modu"
        
        # Generate advice
        if entry_ready and confluence['percentage'] >= 60:
            action = direction
            confidence = 'HIGH'
            advice_tr = f"✅ {direction} pozisyonu için güçlü sinyal"
        elif entry_ready:
            action = direction
            confidence = 'MEDIUM'
            advice_tr = f"⚠️ {direction} mümkün ama dikkatli ol"
        else:
            action = 'WAIT'
            confidence = 'LOW'
            advice_tr = "⏳ Bekle - Henüz giriş için ideal değil"
        
        return {
            'action': action,
            'direction': direction,
            'aligned': aligned,
            'entry_ready': entry_ready,
            'entry_reason': entry_reason,
            'confidence': confidence,
            'advice_tr': advice_tr,
            'suggested_sl': ltf['levels']['nearest_support'] if direction == 'BUY' else ltf['levels']['nearest_resistance'],
            'suggested_tp': ltf['levels']['nearest_resistance'] if direction == 'BUY' else ltf['levels']['nearest_support']
        }


# Standalone test
if __name__ == "__main__":
    if not mt5.initialize():
        print("MT5 initialization failed")
    else:
        analyzer = MultiTimeframeAnalyzer()
        result = analyzer.analyze('EURUSD', preset='intraday')
        
        print("=== MTF ANALYSIS ===")
        print(f"Symbol: {result['symbol']}")
        print(f"Confluence: {result['confluence']['percentage']}% ({result['confluence']['strength_tr']})")
        print(f"Decision: {result['decision']['advice_tr']}")
        print(f"Factors: {result['confluence']['factors']}")
        
        mt5.shutdown()
