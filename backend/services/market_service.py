"""
Market Analysis Service - Handles market data and technical analysis
Refactored from start_server.py for better modularity
"""
from datetime import datetime, time
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

from services.mt5_service import get_mt5_service
from price_action_lib import PriceActionLib
from forecasting_engine import ForecastingEngine


class MarketService:
    """Service for market analysis and technical indicators"""
    
    def __init__(self):
        self.mt5 = get_mt5_service()
        self.pa_lib = PriceActionLib()
        self.forecaster = ForecastingEngine(self.pa_lib)
    
    def get_market_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive market analysis for a symbol"""
        # 1. Get current price (Tick)
        tick = self.mt5.get_symbol_tick(symbol)
        
        # 2. Get recent rates for indicators
        rates = self.mt5.get_rates(symbol, count=100)
        
        if rates is None or len(rates) < 50:
            # Check if symbol even exists
            si = self.mt5.get_symbol_info(symbol)
            if si is None:
                return {'error': f'{symbol} sembolü bulunamadı. Lütfen Market Watch\'a ekleyin.'}
            return {'error': f'{symbol} için yeterli veri yok (En az 50 bar H1 gerekli).'}

        # 3. Weekend Fallback
        current_price = tick.ask if tick is not None else rates[-1]['close']
        is_weekend_data = tick is None
        
        if current_price == 0:
            return {'error': f'{symbol} için fiyat verisi alınamadı.'}
            
        df = pd.DataFrame(rates)
        
        # Calculate RSI 14
        current_rsi = self._calculate_rsi(df['close'], 14)
        
        # Calculate SMAs
        sma_20 = df['close'].rolling(window=20).mean().iloc[-1]
        sma_50 = df['close'].rolling(window=50).mean().iloc[-1]
        
        # Calculate 24h change (approx 24 bars for H1)
        price_24h_ago = df['close'].iloc[-24] if len(df) >= 24 else df['open'].iloc[0]
        change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
        
        # Determine trend
        trend = 'neutral'
        if current_price > sma_50:
            trend = 'uptrend' 
        elif current_price < sma_50:
            trend = 'downtrend'
            
        # Advanced SMC Analysis
        smc_data = self._get_smc_analysis(df, is_weekend_data)
            
        return {
            'symbol': symbol,
            'price': current_price,
            'change_24h': round(change_24h, 2),
            'rsi_14': round(current_rsi, 2),
            'sma_20': round(sma_20, 5),
            'sma_50': round(sma_50, 5),
            'trend': trend,
            'smc': smc_data,
            'forecast': self.forecaster.project_paths(df) if hasattr(self.forecaster, 'project_paths') else {},
            'off_market': is_weekend_data,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    
    def _get_smc_analysis(self, df: pd.DataFrame, is_weekend: bool) -> Dict[str, Any]:
        """Get Smart Money Concepts analysis"""
        try:
            # Perform deep analysis
            analysis_df = self.pa_lib.analyze_all(df)
            latest = analysis_df.iloc[-1]
            
            # Extract SMC metrics
            return {
                'trend_bias': int(latest.get('trend_bias', 0)),
                'bos_detected': bool(latest.get('bos', False)),
                'choch_detected': bool(latest.get('choch', False)),
                'is_discount': bool(latest.get('is_discount', False)),
                'is_premium': bool(latest.get('is_premium', False)),
                'sweep_high': bool(latest.get('sweep_high', False)),
                'sweep_low': bool(latest.get('sweep_low', False)),
                'bullish_ob': bool(latest.get('bullish_ob', False)),
                'bearish_ob': bool(latest.get('bearish_ob', False)),
                'eqh_price': float(latest.get('eqh_price', 0)) if not np.isnan(latest.get('eqh_price', np.nan)) else 0,
                'eql_price': float(latest.get('eql_price', 0)) if not np.isnan(latest.get('eql_price', np.nan)) else 0,
                'bos_count': int(analysis_df['bos'].sum()),
                'choch_count': int(analysis_df['choch'].sum()),
                'confluence_score': float(latest.get('confluence_score', 0)),
                'session_info': self._get_session_info(),
                'coach_advice': self._generate_coach_advice(latest, analysis_df, is_weekend)
            }
        except Exception as e:
            print(f"[ERROR] SMC analysis failed: {e}")
            return {}
    
    def _get_session_info(self) -> Dict[str, str]:
        """Identify current ICT/Global trading session (UTC based)"""
        now_utc = datetime.utcnow().time()
        
        # ICT Killzones (Simplified UTC)
        if time(0, 0) <= now_utc < time(6, 0):
            return {"name": "ASYA KONSOLİDASYONU", "status": "LİKİDİTE BİRİKİMİ", "color": "#00d2ff"}
        elif time(7, 0) <= now_utc < time(10, 0):
            return {"name": "LONDRA AÇILIŞI", "status": "VOLATİLİTE YÜKSEK", "color": "#38ef7d"}
        elif time(12, 0) <= now_utc < time(15, 0):
            return {"name": "NEW YORK OPEN", "status": "KURUMSAL HACİM", "color": "#ff0080"}
        elif time(15, 0) <= now_utc < time(17, 0):
            return {"name": "LONDON CLOSE", "status": "TREND SONU / REVERSAL", "color": "#f45c43"}
        else:
            return {"name": "OFF-PEAK", "status": "DÜŞÜK HACİM", "color": "rgba(255,255,255,0.5)"}

    def _generate_coach_advice(self, latest: pd.Series, df: pd.DataFrame, is_weekend: bool) -> str:
        """Generate human-like trading advice based on SMC data"""
        if is_weekend:
            return "Haftasonu piyasalar kapalı. Pazartesi Londra açılışında likidite süpürmesini bekle."
        
        bias = latest.get('trend_bias', 0)
        is_discount = bool(latest.get('is_discount', False))
        is_premium = bool(latest.get('is_premium', False))
        has_choch = bool(latest.get('choch', False))
        
        if bias == 1:  # Bullish
            if is_discount:
                return "Bias BULLISH ve İndirim bölgesindeyiz. Bullish Order Block retesti için alım fırsatı kolla."
            else:
                return "Bias BULLISH ama fiyat Pahalı (Premium) bölgede. Geri çekilme (retracement) beklemeden girme."
        elif bias == -1:  # Bearish
            if is_premium:
                return "Bias BEARISH ve Premium (Satış) bölgesindeyiz. Bearish OB veya FVG girişleri için yerleş."
            else:
                return "Bias BEARISH ama fiyat İndirimli bölgede. Satış için düzeltme hareketini bekle."
        
        if has_choch:
            return "Trend dönüşü (CHoCH) saptandı. Piyasa yapısı değişiyor, yeni bias onayını bekle."
            
        return "Piyasa şu an karar aşamasında (Equilibrium). Net bir BOS veya Swings kırılımı bekle."
    
    def run_global_scan(self, symbols: list = None) -> list:
        """Scan multiple symbols for confluence opportunities"""
        if symbols is None:
            symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD']
        
        results = []
        for sym in symbols:
            try:
                analysis = self.get_market_analysis(sym)
                if 'error' not in analysis:
                    results.append({
                        'symbol': sym,
                        'score': analysis['smc'].get('confluence_score', 0),
                        'bias': analysis['trend'],
                        'price': analysis['price']
                    })
            except Exception:
                continue
        
        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        return results


# Singleton instance
_market_service: Optional[MarketService] = None


def get_market_service() -> MarketService:
    """Get or create the market service singleton"""
    global _market_service
    if _market_service is None:
        _market_service = MarketService()
    return _market_service
