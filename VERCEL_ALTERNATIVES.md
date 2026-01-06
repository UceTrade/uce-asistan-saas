# Vercel ve Ücretsiz Cloud Alternatifleri

## ❓ Vercel'de Backend Çalıştırılabilir mi?

### Vercel Sınırlamaları

**🔴 SORUNLAR:**

1. **Serverless Timeout**
   - Hobby (Free): 10 saniye max
   - Pro: 60 saniye max
   - ⚠️ WebSocket sürekli açık kalamaz

2. **WebSocket Desteği Yok**
   - Vercel Serverless Functions HTTP only
   - Long-lived connections desteklenmez
   - ⚠️ MT5 real-time bağlantı imkansız

3. **MT5 Kütüphanesi**
   - MetaTrader5 Python library Windows-only
   - Vercel Linux container'da çalışmaz
   - ⚠️ Native MT5 bağlantısı yok

4. **Cold Start**
   - Her request yeni container başlatır
   - 5-10 saniye ilk yanıt
   - ⚠️ Real-time trading için çok yavaş

**✅ NE YAPILABİLİR (Sınırlı):**

### 1. Vercel Cron Jobs (Scheduled Functions)

```javascript
// api/cron/scan-markets.js
export const config = {
  runtime: 'nodejs18.x',
  maxDuration: 60, // Pro plan (Free: 10 saniye)
};

export default async function handler(req, res) {
  // Her 1 saatte bir çalışır
  // Market verilerini kontrol et
  const signals = await scanMarkets();
  
  // Kullanıcılara email/telegram gönder
  await notifyUsers(signals);
  
  return res.json({ success: true });
}
```

**vercel.json:**
```json
{
  "crons": [{
    "path": "/api/cron/scan-markets",
    "schedule": "0 * * * *"  // Her saat
  }]
}
```

**Avantajları:**
✅ Ücretsiz (Hobby plan'da 1 cron)
✅ Market taraması yapabilir
✅ Bildirim gönderebilir

**Dezavantajları:**
🔴 Real-time değil (min. 1 dakika interval)
🔴 Trade açamaz (MT5 yok)
🔴 WebSocket yok

---

## 🆓 ÜCRETSIZ/DÜŞÜK MALİYETLİ ALTERNATİFLER

### 1. Railway.app ⭐ ÖNERİLEN

**Ücretsiz Tier:**
- $5 kredi/ay (500 saat çalışma)
- WebSocket ✅
- Long-running processes ✅
- Python + PostgreSQL ✅

**Deployment:**
```bash
# railway.toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python backend/start_server.py"

[[services]]
name = "uceasistan-backend"
port = 8766
```

**Maliyet:**
- Ücretsiz: ~$5 kredi (1 GB RAM, 500 saat)
- Paid: $5/ay'dan başlar

**Avantajlar:**
✅ WebSocket tam destek
✅ PostgreSQL dahil
✅ GitHub entegrasyon
✅ Basit deploy

**Dezavantajlar:**
🔴 MT5 Windows-only (Wine gerekir)

---

### 2. Render.com

**Ücretsiz Tier:**
- 750 saat/ay Free Web Service
- Otomatik sleep (15 dk inactivity)
- WebSocket ✅
- Python/PostgreSQL ✅

**render.yaml:**
```yaml
services:
  - type: web
    name: uceasistan-backend
    env: python
    plan: free
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python start_server.py"
    envVars:
      - key: PORT
        value: 8766
```

**Avantajlar:**
✅ Tamamen ücretsiz (750 saat)
✅ WebSocket destekler
✅ Auto-deploy

**Dezavantajlar:**
🔴 15 dk sonra uyur (first request 30 sn)
🔴 MT5 Wine ile

---

### 3. Fly.io

**Ücretsiz Tier:**
- 3 GB persistent volume
- 160GB outbound data
- WebSocket ✅

**fly.toml:**
```toml
app = "uceasistan"

[build]
  builder = "paketobuildpacks/builder:base"

[[services]]
  internal_port = 8766
  protocol = "tcp"

  [[services.ports]]
    port = 8766
```

**Avantajlar:**
✅ Edge locations
✅ WebSocket
✅ Persistent volume

**Dezavantajlar:**
🔴 Setup daha karmaşık

---

### 4. Koyeb

**Ücretsiz Tier:**
- Always-on FREE instance
- WebSocket ✅
- Global deployment

**Deployment:**
```bash
koyeb app init uceasistan \
  --git github.com/yourusername/uceasistan \
  --git-branch main \
  --docker \
  --ports 8766:http
```

**Avantajlar:**
✅ Tamamen ücretsiz
✅ Always-on (sleep yok!)
✅ WebSocket

---

## 🎯 ÖNERİLEN ÇÖZÜM: HYBRID

### Strateji: Railway (Monitoring) + Local (Trading)

```
┌─────────────────────────────────┐
│    RAILWAY.APP (Ücretsiz)       │
│  🔔 Strategy Monitoring         │
│                                 │
│  Python Backend (Hafif)         │
│  ├─ Market scanner              │
│  ├─ Signal detector             │
│  └─ Notification service        │
│                                 │
│  PostgreSQL (Stratejiler)       │
│  └─ User strategies DB          │
│                                 │
│  Maliyet: $0-5/ay ✅            │
└─────────────────────────────────┘
         ↓ WebSocket wss://
         
┌─────────────────────────────────┐
│   KULLANICI BİLGİSAYARI         │
│  UceAsistan.exe                 │
│  ├─ UI (Electron)               │
│  └─ MT5 Trading (Python exe)   │
│                                 │
│  Açıkken: Trade execution       │
│  Kapalıyken: Notifications only │
└─────────────────────────────────┘
```

### Implementation

**Railway Backend (Minimal):**
```python
# cloud_monitor.py - Railway'de çalışır
import asyncio
import websockets
from sqlalchemy import create_engine

async def monitor_strategies():
    """Sürekli market'i tara"""
    while True:
        # Database'den aktif stratejileri al
        strategies = db.get_active_strategies()
        
        for strategy in strategies:
            # Yahoo Finance'den veri al (MT5 gerekmez!)
            data = await yahoo_finance.get_data(strategy.symbol)
            
            # Stratejiyi çalıştır
            signal = await run_strategy(strategy.code, data)
            
            if signal:
                # Kullanıcıya bildir
                await notify_user_telegram(strategy.user, signal)
                await notify_user_email(strategy.user, signal)
                
                # WebSocket ile desktop app'e gönder (açıksa)
                await websocket_notify(strategy.user, signal)
        
        await asyncio.sleep(60)  # 1 dakika bekle

# 7/24 çalışır!
asyncio.run(monitor_strategies())
```

**Desktop App:**
```javascript
// WebSocket ile Railway'e bağlan
const ws = new WebSocket('wss://uceasistan.railway.app');

ws.on('message', (signal) => {
    if (settings.autoTrade && mt5.isConnected()) {
        // Kullanıcı açıksa trade aç
        mt5.executeTrade(signal);
    } else {
        // Kapalıysa sadece notification (zaten Telegram'a gitti)
        console.log('Signal received while inactive:', signal);
    }
});
```

---

## 💰 Maliyet Karşılaştırması (Aylık)

| Platform | Ücretsiz | Paid Plan | WebSocket | Always-On |
|----------|----------|-----------|-----------|-----------|
| **Vercel** | ✅ | $20/ay | 🔴 Sınırlı | 🔴 Hayır |
| **Railway** | $5 kredi | $5/ay+ | ✅ | ✅ |
| **Render** | ✅ 750h | $7/ay | ✅ | ⚠️ 15dk sleep |
| **Fly.io** | ✅ | $1.94/ay+ | ✅ | ✅ |
| **Koyeb** | ✅ | $5.5/ay | ✅ | ✅ |
| **VPS** | 🔴 | $60-100/ay | ✅ | ✅ |

---

## 🎯 ÖNERİM

### FAZ 1: PyInstaller (Önce bu!) ✅
```
Python dependency sorunu çözülsün
Kullanıcı deneyimi iyileşsin
Maliyet: $0
```

### FAZ 2: Railway Monitoring 🔔
```
7/24 market taraması
Telegram/Email bildirimleri
Trade execution hala lokal
Maliyet: $0-5/ay
```

### FAZ 3: (İsteğe Bağlı) Full Cloud 🚀
```
Windows VPS + MT5
Tam otomatik trading
Maliyet: $60-100/ay
```

**İLK ADIM:** PyInstaller build'i başlatalım! 🎯
