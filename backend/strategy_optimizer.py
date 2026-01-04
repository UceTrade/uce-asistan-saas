"""
Strategy Optimizer - Türkçe - Backtest sonuçlarını analiz et ve iyileştirmeler öner
"""


class StrategyOptimizer:
    """Backtest sonuçlarını analiz et ve optimizasyon öner"""
    
    def __init__(self):
        self.min_trades_threshold = 10
        self.good_win_rate = 50.0
        self.max_acceptable_drawdown = 20.0
    
    def analyze_backtest(self, strategy_code, backtest_results):
        """
        Backtest'i analiz et ve iyileştirmeler öner
        
        Args:
            strategy_code: Orijinal strateji kodu
            backtest_results: Backtest sonuçları dict
        
        Returns:
            issue, suggestion, code_change içeren öneriler listesi
        """
        if not backtest_results.get('success'):
            return [{
                'issue': 'Backtest Başarısız',
                'suggestion': 'Optimizasyon öncesi strateji hatalarını düzeltin',
                'priority': 'high',
                'code_change': None
            }]
        
        metrics = backtest_results.get('metrics', {})
        suggestions = []
        
        # Sorun 1: Düşük kazanma oranı
        win_rate = metrics.get('win_rate', 0)
        if win_rate < 40:
            suggestions.append({
                'issue': f'Düşük Kazanma Oranı ({win_rate:.1f}%)',
                'suggestion': 'Trend karşıtı işlemlerden kaçınmak için trend filtresi ekleyin',
                'priority': 'high',
                'code_change': '''
# Giriş mantığınızdan önce bunu ekleyin:
# Trend Filtresi - SMA 200
sma_200 = data['close'].rolling(window=200).mean()
current_price = data['close'].iloc[-1]
trend_up = current_price > sma_200.iloc[-1]

# Sadece yükseliş trendinde AL, sadece düşüş trendinde SAT
if your_buy_condition and trend_up:
    return 'BUY'
elif your_sell_condition and not trend_up:
    return 'SELL'
'''
            })
        
        # Sorun 2: Yüksek düşüş
        max_dd = metrics.get('max_drawdown_pct', 0)
        if max_dd > self.max_acceptable_drawdown:
            suggestions.append({
                'issue': f'Yüksek Düşüş ({max_dd:.1f}%)',
                'suggestion': 'Stop loss\'u sıkılaştırın veya pozisyon boyutunu küçültün',
                'priority': 'critical',
                'code_change': '''
# Pozisyon boyutunu mevcut değerin %50'sine düşür
# Veya daha sıkı stop loss mantığı ekle
# ATR bazlı stop kullanmayı düşünün
'''
            })
        
        # Sorun 3: Çok az işlem
        total_trades = metrics.get('total_trades', 0)
        if total_trades < self.min_trades_threshold:
            suggestions.append({
                'issue': f'Çok Az İşlem ({total_trades})',
                'suggestion': 'Giriş koşullarını gevşetin veya daha kısa zaman dilimi kullanın',
                'priority': 'medium',
                'code_change': '''
# Seçenek 1: Eşikleri gevşet
# Şu yerine: if rsi < 30
# Şunu dene: if rsi < 35

# Seçenek 2: Daha fazla giriş sinyali ekle
# AND yerine OR ile birden fazla koşulu birleştir
'''
            })
        
        # Sorun 4: Negatif kar faktörü
        profit_factor = metrics.get('profit_factor', 0)
        if profit_factor < 1.0:
            suggestions.append({
                'issue': f'Negatif Kar Faktörü ({profit_factor:.2f})',
                'suggestion': 'Strateji zarar ediyor - büyük revizyon gerekli',
                'priority': 'critical',
                'code_change': '''
# Düşünün:
# 1. Stratejiyi tersine çevirin (AL -> SAT olsun)
# 2. Onay indikatörleri ekleyin
# 3. Farklı zaman dilimi kullanın
# 4. Tamamen farklı bir yaklaşım deneyin
'''
            })
        
        # Sorun 5: İyi kazanma oranı ama düşük kar
        net_profit = metrics.get('net_profit', 0)
        if win_rate > 60 and net_profit < 0:
            suggestions.append({
                'issue': 'Yüksek Kazanma Oranı Ama Para Kaybı',
                'suggestion': 'Kayıplar çok büyük - risk/ödül oranını iyileştirin',
                'priority': 'high',
                'code_change': '''
# Kazananlarınız küçük, kaybedenleriniz büyük
# Çözüm: Kazananları koşturun, kaybedenleri hızlıca kesin
# - Küçük kar sonrası stop loss'u başabaşa taşıyın
# - Trailing stop kullanın
# - Take profit hedefini artırın
'''
            })
        
        # Olumlu geri bildirim
        if win_rate >= 50 and profit_factor > 1.5 and max_dd < 15:
            suggestions.append({
                'issue': 'Strateji İyi Görünüyor! ✅',
                'suggestion': 'Küçük iyileştirmeler daha da geliştirebilir',
                'priority': 'low',
                'code_change': '''
# Opsiyonel iyileştirmeler:
# - Zaman filtreleri ekleyin (haber saatlerinden kaçının)
# - Pozisyon boyutunu volatiliteye göre ölçeklendirin
# - Birden fazla take profit seviyesi ekleyin
'''
            })
        
        return suggestions
    
    def apply_optimization(self, original_code, optimization):
        """
        Önerilen optimizasyonu koda uygula
        
        Args:
            original_code: Orijinal strateji kodu
            optimization: code_change içeren optimizasyon dict
        
        Returns:
            Değiştirilmiş kod
        """
        if not optimization.get('code_change'):
            return original_code
        
        # Şimdilik basit ekleme
        # Gelecekte, kodu akıllıca eklemek için AST kullanılabilir
        modified = original_code + "\n\n# OTOMATİK OPTİMİZASYON ÖNERİSİ:\n"
        modified += optimization['code_change']
        
        return modified
    
    def generate_optimization_report(self, suggestions):
        """
        İnsan tarafından okunabilir optimizasyon raporu oluştur
        
        Returns:
            Formatlanmış rapor string'i
        """
        if not suggestions:
            return "Optimizasyon önerisi yok."
        
        report = "📊 **Backtest Analizi & Optimizasyon Önerileri**\n\n"
        
        # Önceliğe göre grupla
        critical = [s for s in suggestions if s['priority'] == 'critical']
        high = [s for s in suggestions if s['priority'] == 'high']
        medium = [s for s in suggestions if s['priority'] == 'medium']
        low = [s for s in suggestions if s['priority'] == 'low']
        
        if critical:
            report += "🚨 **KRİTİK SORUNLAR:**\n"
            for s in critical:
                report += f"- **{s['issue']}**: {s['suggestion']}\n"
            report += "\n"
        
        if high:
            report += "⚠️ **YÜKSEK ÖNCELİK:**\n"
            for s in high:
                report += f"- **{s['issue']}**: {s['suggestion']}\n"
            report += "\n"
        
        if medium:
            report += "📌 **ORTA ÖNCELİK:**\n"
            for s in medium:
                report += f"- **{s['issue']}**: {s['suggestion']}\n"
            report += "\n"
        
        if low:
            report += "💡 **ÖNERİLER:**\n"
            for s in low:
                report += f"- **{s['issue']}**: {s['suggestion']}\n"
        
        return report


# Örnek kullanım
if __name__ == '__main__':
    optimizer = StrategyOptimizer()
    
    # Kötü backtest sonuçlarını simüle et
    bad_results = {
        'success': True,
        'metrics': {
            'win_rate': 35.0,
            'max_drawdown_pct': 25.0,
            'total_trades': 5,
            'profit_factor': 0.8,
            'net_profit': -500
        }
    }
    
    suggestions = optimizer.analyze_backtest("", bad_results)
    report = optimizer.generate_optimization_report(suggestions)
    print(report)
    
    print("\n" + "="*50 + "\n")
    
    # İyi sonuçları simüle et
    good_results = {
        'success': True,
        'metrics': {
            'win_rate': 55.0,
            'max_drawdown_pct': 12.0,
            'total_trades': 45,
            'profit_factor': 1.8,
            'net_profit': 2500
        }
    }
    
    suggestions = optimizer.analyze_backtest("", good_results)
    report = optimizer.generate_optimization_report(suggestions)
    print(report)
