
import time
import sys
import os

# Backend klasörünü path'e ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from live_trader import LiveTrader

# --- PROFESYONEL STRATEJİ KODU ---
# Strateji: Trend Hunter & RSI Reversal
# Mantık: 
# 1. Ana Trendi Belirle (EMA 200)
# 2. Düzeltmeleri Yakala (RSI Aşırı Alım/Satım)
# 3. Yükselen trendde düşüşleri al, düşen trendde yükselişleri sat.

STRATEGY_CODE = """
def strategy(data, position):
    # İndikatör Hesaplamaları
    close = data['close']
    
    # RSI (14)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # EMA (200) - Trend Filtresi
    ema200 = close.ewm(span=200, adjust=False).mean()
    
    # Son Değerler
    current_price = close.iloc[-1]
    current_rsi = rsi.iloc[-1]
    current_ema = ema200.iloc[-1]
    
    # --- SİNYAL MANTIĞI ---
    
    # ALIŞ (BUY) Sinyali
    # 1. Fiyat EMA 200'ün üzerinde (Yükseliş Trendi)
    # 2. RSI 30'un altına indi (Aşırı Satım / Düzeltme)
    if position == 0:
        if current_price > current_ema and current_rsi < 35:
            return 'BUY'
            
    # SATIŞ (SELL) Sinyali
    # 1. Fiyat EMA 200'ün altında (Düşüş Trendi)
    # 2. RSI 70'in üzerine çıktı (Aşırı Alım / Düzeltme)
    if position == 0:
        if current_price < current_ema and current_rsi > 65:
            return 'SELL'
            
    # POZİSYON KAPATMA
    # RSI ters yöne aşırı giderse erkenden kâr al
    if position == 1 and current_rsi > 75:
        return 'SELL' # Long Kapat
        
    if position == -1 and current_rsi < 25:
        return 'BUY' # Short Kapat
        
    return 'HOLD'
"""

def main():
    print("🦁 UceAsistan AI Trader Başlatılıyor...")
    print("📈 Strateji: Trend Hunter Pro v1")
    print("📊 Sembol: XAUUSD (Altın)")
    print("⏱️ Zaman Dilimi: M5 (Scalping Modu)")
    
    # Trader'ı Başlat
    trader = LiveTrader()
    
    # XAUUSD, M5, Risk/Reward: 2.0, Lot: 0.01
    success, msg = trader.start(
        strategy_code=STRATEGY_CODE,
        symbol="XAUUSD",
        timeframe_str="M5",
        rr_ratio=2.0,
        lot_size=0.01
    )
    
    if success:
        print(f"✅ BAŞARILI: {msg}")
        print("Bot şu an piyasayı izliyor... (Durdurmak için Ctrl+C)")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Bot durduruluyor...")
            trader.stop()
            print("Bot durduruldu.")
    else:
        print(f"❌ HATA: {msg}")

if __name__ == "__main__":
    main()
