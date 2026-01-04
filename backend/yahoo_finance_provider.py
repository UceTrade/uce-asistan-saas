"""
Yahoo Finance Data Provider
Ücretsiz piyasa verisi (API key gerekmez)
"""

import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd


class YahooFinanceProvider:
    """Yahoo Finance üzerinden ücretsiz piyasa verisi sağlar"""
    
    def __init__(self):
        # Symbol mapping: Internal -> Yahoo Finance format
        self.symbol_map = {
            # Major FX
            'EURUSD': 'EURUSD=X',
            'GBPUSD': 'GBPUSD=X',
            'USDJPY': 'USDJPY=X',
            'USDCHF': 'USDCHF=X',
            'USDCAD': 'USDCAD=X',
            'AUDUSD': 'AUDUSD=X',
            'NZDUSD': 'NZDUSD=X',
            
            # Minor FX
            'EURGBP': 'EURGBP=X',
            'EURJPY': 'EURJPY=X',
            'GBPJPY': 'GBPJPY=X',
            'AUDJPY': 'AUDJPY=X',
            'EURAUD': 'EURAUD=X',
            'EURCAD': 'EURCAD=X',
            'GBPCHF': 'GBPCHF=X',
            
            # Crypto
            'BTCUSD': 'BTC-USD',
            'ETHUSD': 'ETH-USD',
            'XRPUSD': 'XRP-USD',
            'LTCUSD': 'LTC-USD',
            
            # Metals
            'XAUUSD': 'GC=F',  # Gold Futures
            'XAGUSD': 'SI=F',  # Silver Futures
            
            # Indices
            'US30': '^DJI',     # Dow Jones
            'SPX500': '^GSPC',  # S&P 500 
            'NAS100': '^IXIC',  # NASDAQ
            'GER40': '^GDAXI',  # DAX
            'DXY': 'DX-Y.NYB',  # US Dollar Index
            'VIX': '^VIX',      # Volatility Index (Fear)
            
            # Commodities
            'USOUSD': 'CL=F',  # Crude Oil
        }
        
        # Cache for rate limiting
        self._cache = {}
        self._cache_time = {}
        self._cache_duration = 10  # seconds
    
    def get_yahoo_symbol(self, symbol):
        """Convert internal symbol to Yahoo Finance format"""
        return self.symbol_map.get(symbol, symbol)
    
    def get_quote(self, symbol):
        """Get real-time quote for a symbol"""
        try:
            yahoo_symbol = self.get_yahoo_symbol(symbol)
            
            # Check cache
            cache_key = f"quote_{yahoo_symbol}"
            if cache_key in self._cache:
                cache_age = (datetime.now() - self._cache_time[cache_key]).total_seconds()
                if cache_age < self._cache_duration:
                    return self._cache[cache_key]
            
            # Fetch from Yahoo
            ticker = yf.Ticker(yahoo_symbol)
            info = ticker.fast_info
            
            # Get historical data for change calculation
            hist = ticker.history(period='2d')
            
            if hist.empty:
                return {'error': f'No data for {symbol}'}
            
            current_price = float(info.last_price) if hasattr(info, 'last_price') else float(hist['Close'].iloc[-1])
            
            # Calculate 24h change
            if len(hist) >= 2:
                prev_close = float(hist['Close'].iloc[-2])
                change_24h = ((current_price - prev_close) / prev_close) * 100
            else:
                change_24h = 0
            
            # Get OHLC
            today = hist.iloc[-1]
            
            result = {
                'symbol': symbol,
                'price': current_price,
                'change_24h': round(change_24h, 2),
                'open': float(today['Open']),
                'high': float(today['High']),
                'low': float(today['Low']),
                'close': float(today['Close']),
                'volume': int(today['Volume']) if 'Volume' in today else 0,
                'trend': 'uptrend' if change_24h > 0.1 else 'downtrend' if change_24h < -0.1 else 'neutral',
                'source': 'yahoo_finance',
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache result
            self._cache[cache_key] = result
            self._cache_time[cache_key] = datetime.now()
            
            return result
            
        except Exception as e:
            return {
                'error': str(e),
                'symbol': symbol,
                'source': 'yahoo_finance'
            }
    
    def get_multiple_quotes(self, symbols):
        """Get quotes for multiple symbols"""
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_quote(symbol)
        return results
    
    def get_historical(self, symbol, period='1mo', interval='1d'):
        """Get historical data for a symbol
        
        Args:
            symbol: Trading symbol
            period: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
            interval: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
        """
        try:
            yahoo_symbol = self.get_yahoo_symbol(symbol)
            ticker = yf.Ticker(yahoo_symbol)
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                return {'error': f'No historical data for {symbol}'}
            
            # Convert to list of dicts
            data = []
            for idx, row in hist.iterrows():
                data.append({
                    'time': idx.isoformat(),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume']) if 'Volume' in row else 0
                })
            
            return {
                'symbol': symbol,
                'period': period,
                'interval': interval,
                'data': data,
                'source': 'yahoo_finance'
            }
            
        except Exception as e:
            return {'error': str(e), 'symbol': symbol}
    
    def get_all_terminal_data(self):
        """Get all data needed for market terminal"""
        all_symbols = list(self.symbol_map.keys())
        return self.get_multiple_quotes(all_symbols)


# Global instance
yahoo_provider = YahooFinanceProvider()
