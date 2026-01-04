"""
Strategy Templates - Pre-built trading strategies for quick start
"""


class StrategyTemplates:
    """Manage pre-built strategy templates"""
    
    def __init__(self):
        self.templates = {
            'rsi_oversold': {
                'id': 'rsi_oversold',
                'name': 'RSI Aşırı Satım/Alım',
                'category': 'Oscillator',
                'description': 'RSI 30\'un altında al, 70\'in üstünde sat',
                'timeframe': 'H1',
                'summary': 'Bu strateji RSI (Relative Strength Index) indikatörünü kullanır. RSI 30\'un altına düştüğünde aşırı satım bölgesi olarak kabul edilir ve alım sinyali verilir. RSI 70\'in üzerine çıktığında ise aşırı alım bölgesi olarak kabul edilir ve satış sinyali verilir.',
                'code': '''import pandas as pd
import numpy as np

def strategy(data, position):
    """RSI Oversold/Overbought Strategy"""
    # Ensure we have enough data
    if len(data) < 20:
        return 'HOLD'
    
    # Calculate RSI (14-period)
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # Get current values
    current_rsi = rsi.iloc[-1]
    
    # Trading logic
    if current_rsi < 30 and position <= 0:
        return 'BUY'  # Oversold - Buy signal
    elif current_rsi > 70 and position >= 0:
        return 'SELL'  # Overbought - Sell signal
    
    return 'HOLD'
'''
            },
            
            'sma_crossover': {
                'id': 'sma_crossover',
                'name': 'SMA Kesişimi (Golden/Death Cross)',
                'category': 'Trend Following',
                'description': 'SMA 50, SMA 200\'ü yukarı keserse al (Golden Cross), aşağı keserse sat (Death Cross)',
                'timeframe': 'D1',
                'summary': 'Klasik trend takip stratejisi. Kısa vadeli SMA (50) uzun vadeli SMA (200)\'ü yukarı kestiğinde güçlü yükseliş sinyali (Golden Cross), aşağı kestiğinde düşüş sinyali (Death Cross) verir.',
                'code': '''import pandas as pd
import numpy as np

def strategy(data, position):
    """SMA Crossover Strategy (Golden/Death Cross)"""
    # Ensure we have enough data
    if len(data) < 200:
        return 'HOLD'
    
    # Calculate SMAs
    sma_50 = data['close'].rolling(window=50).mean()
    sma_200 = data['close'].rolling(window=200).mean()
    
    # Get current and previous values
    current_sma50 = sma_50.iloc[-1]
    current_sma200 = sma_200.iloc[-1]
    prev_sma50 = sma_50.iloc[-2]
    prev_sma200 = sma_200.iloc[-2]
    
    # Detect crossover
    golden_cross = (prev_sma50 <= prev_sma200) and (current_sma50 > current_sma200)
    death_cross = (prev_sma50 >= prev_sma200) and (current_sma50 < current_sma200)
    
    # Trading logic
    if golden_cross and position <= 0:
        return 'BUY'  # Golden Cross - Strong uptrend
    elif death_cross and position >= 0:
        return 'SELL'  # Death Cross - Strong downtrend
    
    return 'HOLD'
'''
            },
            
            'ict_fvg': {
                'id': 'ict_fvg',
                'name': 'ICT Fair Value Gap (FVG)',
                'category': 'ICT/Smart Money',
                'description': 'Fair Value Gap (boşluk) oluştuğunda geri dönüş bekle ve trade al',
                'timeframe': 'H1',
                'summary': 'ICT (Inner Circle Trader) konsepti olan Fair Value Gap stratejisi. Fiyat hızlı hareket ettiğinde oluşan boşlukları (FVG) tespit eder ve bu boşlukların doldurulmasını bekler. Bullish FVG\'de alım, Bearish FVG\'de satış sinyali verir.',
                'code': '''import pandas as pd
import numpy as np

def strategy(data, position):
    """ICT Fair Value Gap (FVG) Strategy"""
    # Ensure we have enough data
    if len(data) < 20:
        return 'HOLD'
    
    # Use pre-calculated FVG from Price Action Library
    # The backtest engine calls pa.analyze_all(data) before strategy execution
    
    # Get current values
    current_price = data['close'].iloc[-1]
    
    # Check for Bullish FVG (buy opportunity)
    if 'bullish_fvg' in data.columns:
        bullish_fvg = data['bullish_fvg'].iloc[-1]
        if bullish_fvg and position <= 0:
            return 'BUY'
    
    # Check for Bearish FVG (sell opportunity)
    if 'bearish_fvg' in data.columns:
        bearish_fvg = data['bearish_fvg'].iloc[-1]
        if bearish_fvg and position >= 0:
            return 'SELL'
    
    return 'HOLD'
'''
            },
            
            'breakout': {
                'id': 'breakout',
                'name': 'Breakout (Kırılım) Stratejisi',
                'category': 'Breakout',
                'description': 'Son 20 barın en yüksek/düşük seviyesini kırdığında trade al',
                'timeframe': 'H4',
                'summary': 'Fiyat belirli bir aralıkta konsolide olduktan sonra kırılım yaparsa güçlü hareket beklenir. Bu strateji son 20 barın en yüksek seviyesini yukarı kırarsa alım, en düşük seviyesini aşağı kırarsa satış sinyali verir.',
                'code': '''import pandas as pd
import numpy as np

def strategy(data, position):
    """Breakout Strategy"""
    # Ensure we have enough data
    if len(data) < 25:
        return 'HOLD'
    
    # Calculate 20-period high/low
    period = 20
    highest_high = data['high'].iloc[-period:-1].max()  # Exclude current bar
    lowest_low = data['low'].iloc[-period:-1].min()
    
    # Get current price
    current_close = data['close'].iloc[-1]
    current_high = data['high'].iloc[-1]
    current_low = data['low'].iloc[-1]
    
    # Breakout detection
    bullish_breakout = current_high > highest_high
    bearish_breakout = current_low < lowest_low
    
    # Trading logic
    if bullish_breakout and position <= 0:
        return 'BUY'  # Upside breakout
    elif bearish_breakout and position >= 0:
        return 'SELL'  # Downside breakout
    
    return 'HOLD'
'''
            },
            
            'mean_reversion': {
                'id': 'mean_reversion',
                'name': 'Mean Reversion (Bollinger Bands)',
                'category': 'Mean Reversion',
                'description': 'Fiyat alt banda değerse al, üst banda değerse sat',
                'timeframe': 'H1',
                'summary': 'Ortalamaya dönüş stratejisi. Bollinger Bands kullanarak fiyatın aşırı sapma yaptığı noktaları tespit eder. Alt banda dokunduğunda (aşırı satım) alım, üst banda dokunduğunda (aşırı alım) satış sinyali verir.',
                'code': '''import pandas as pd
import numpy as np

def strategy(data, position):
    """Mean Reversion Strategy using Bollinger Bands"""
    # Ensure we have enough data
    if len(data) < 25:
        return 'HOLD'
    
    # Calculate Bollinger Bands (20-period, 2 std dev)
    period = 20
    sma = data['close'].rolling(window=period).mean()
    std = data['close'].rolling(window=period).std()
    
    upper_band = sma + (2 * std)
    lower_band = sma - (2 * std)
    
    # Get current values
    current_price = data['close'].iloc[-1]
    current_upper = upper_band.iloc[-1]
    current_lower = lower_band.iloc[-1]
    current_sma = sma.iloc[-1]
    
    # Mean reversion logic
    # Buy when price touches lower band (oversold)
    if current_price <= current_lower and position <= 0:
        return 'BUY'
    
    # Sell when price touches upper band (overbought)
    elif current_price >= current_upper and position >= 0:
        return 'SELL'
    
    # Exit when price returns to mean
    elif position != 0 and abs(current_price - current_sma) < (current_upper - current_sma) * 0.3:
        if position == 1:
            return 'SELL'  # Close long
        else:
            return 'BUY'  # Close short
    
    return 'HOLD'
'''
            },
            
            'ict_smart_money': {
                'id': 'ict_smart_money',
                'name': 'ICT Smart Money (Tested)',
                'category': 'ICT/Smart Money',
                'description': 'Trend + Discount/Premium + FVG/OB kombinasyonu (137 trade, %15 getiri)',
                'timeframe': 'H1',
                'summary': 'Test edilmiş ICT stratejisi. Trend yönünde, discount/premium bölgelerinde, FVG veya Order Block oluştuğunda işlem açar. OR mantığı kullandığı için daha fazla sinyal üretir.',
                'code': '''import pandas as pd
import numpy as np

def strategy(data, position):
    """ICT Smart Money Strategy - Tested and Verified"""
    if len(data) < 50:
        return 'HOLD'
    
    if 'trend_bias' not in data.columns:
        return 'HOLD'
    
    trend = data['trend_bias'].iloc[-1] if 'trend_bias' in data.columns else 0
    is_discount = data['is_discount'].iloc[-1] if 'is_discount' in data.columns else False
    is_premium = data['is_premium'].iloc[-1] if 'is_premium' in data.columns else False
    bullish_fvg = data['bullish_fvg'].iloc[-1] if 'bullish_fvg' in data.columns else False
    bearish_fvg = data['bearish_fvg'].iloc[-1] if 'bearish_fvg' in data.columns else False
    bullish_ob = data['bullish_ob'].iloc[-1] if 'bullish_ob' in data.columns else False
    bearish_ob = data['bearish_ob'].iloc[-1] if 'bearish_ob' in data.columns else False
    
    if trend >= 0 and (is_discount or bullish_fvg or bullish_ob):
        if position <= 0:
            return 'BUY'
    
    if trend <= 0 and (is_premium or bearish_fvg or bearish_ob):
        if position >= 0:
            return 'SELL'
    
    return 'HOLD'
'''
            }
        }
    
    def list_templates(self):
        """Get list of all templates with metadata"""
        return [
            {
                'id': t['id'],
                'name': t['name'],
                'category': t['category'],
                'description': t['description'],
                'timeframe': t['timeframe']
            }
            for t in self.templates.values()
        ]
    
    def get_template(self, template_id):
        """Get full template by ID"""
        if template_id not in self.templates:
            return {
                'success': False,
                'error': f'Template {template_id} not found'
            }
        
        template = self.templates[template_id]
        return {
            'success': True,
            'id': template['id'],
            'name': template['name'],
            'category': template['category'],
            'description': template['description'],
            'timeframe': template['timeframe'],
            'summary': template['summary'],
            'code': template['code']
        }
    
    def customize_template(self, template_id, params=None):
        """
        Customize template with user parameters
        
        Args:
            template_id: Template ID
            params: Optional dict with customization params
                    e.g., {'rsi_period': 14, 'rsi_oversold': 30}
        
        Returns:
            Customized template
        """
        template = self.get_template(template_id)
        
        if not template['success']:
            return template
        
        # For now, just return the template as-is
        # In future, we can add parameter substitution
        # e.g., replace "14" with params['rsi_period']
        
        return template
