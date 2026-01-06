# 🚀 Koyeb Deployment Guide

## ✅ Hazır Dosyalar
- ✅ `Dockerfile` - Container yapılandırması
- ✅ `.dockerignore` - Gereksiz dosyaları hariç tut
- ✅ Health check endpoint eklendi

## 📋 Adım Adım Deployment

### 1. GitHub'a Push Edin

```bash
cd ai-trading-coach
git add backend/Dockerfile backend/.dockerignore backend/start_server.py
git commit -m "Add Koyeb deployment configuration"
git push origin main
```

### 2. Koyeb Hesabı Oluşturun

1. **https://app.koyeb.com/auth/signup** adresine gidin
2. GitHub ile giriş yapın (EN KOLAY)
3. **Credit card GEREKMİYOR!** ✅

### 3. Uygulama Oluşturun

#### Dashboard'dan:
1. **Create App** butonuna tıklayın
2. **GitHub** deployment metodunu seçin
3. Repository: `ai-trading-coach`
4. Branch: `main`

#### Build Ayarları:
- **Builder**: Dockerfile
- **Dockerfile path**: `backend/Dockerfile`
- **Build context**: `backend`

#### Instance Ayarları:
- **Instance type**: Eco (Ücretsiz)
- **Regions**: Frankfurt (veya yakın lokasyon)
- **Port**: `8766`

### 4. Environment Variables (Çevre Değişkenleri)

**Add Environment Variables** bölümünde:

```
GROQ_API_KEY=gsk_xxxxxxxxxxxxx
TELEGRAM_BOT_TOKEN=1234567890:ABCxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=123456789
HOST=0.0.0.0
PORT=8766
```

> **Not:** Bu değişkenleri backend/.env dosyanızdan kopyalayın

### 5. Health Check Ayarları

- **Health check path**: `/health` (opsiyonel, zaten WebSocket var)
- **Port**: `8766`

### 6. Deploy!

**Deploy** butonuna tıklayın → 2-3 dakika içinde hazır!

## 🔗 Deployment Sonrası

### Backend URL'nizi Alın

Deploy tamamlanınca:
```
https://uceasistan-backend-RANDOM.koyeb.app
```

WebSocket URL:
```
wss://uceasistan-backend-RANDOM.koyeb.app
```

### Desktop App'i Güncelleyin

**mt5-connector.js** dosyasını düzenleyin:

```javascript
// SEÇENEK 1: Sadece cloud backend
const BACKEND_URL = 'wss://uceasistan-backend-RANDOM.koyeb.app';

// SEÇENEK 2: Otomatik geçiş (lokal varsa lokal, yoksa cloud)
const BACKEND_URL = navigator.onLine && window.location.protocol !== 'file:'
    ? 'wss://uceasistan-backend-RANDOM.koyeb.app'  // Cloud
    : 'ws://localhost:8766';                        // Local
```

## 🧪 Test Etme

### 1. Backend Çalışıyor mu?

Tarayıcıda açın:
```
https://uceasistan-backend-RANDOM.koyeb.app
```

WebSocket test:
```javascript
const ws = new WebSocket('wss://uceasistan-backend-RANDOM.koyeb.app');
ws.onopen = () => console.log('Connected!');
ws.send(JSON.stringify({action: 'health'}));
```

### 2. Logs Kontrolü

Koyeb Dashboard → App → **Logs** sekmesi:
```
[START] MT5 WebSocket Server started on ws://0.0.0.0:8766
[WAIT] Waiting for connections...
```

## ⚠️ Önemli Notlar

### MT5 Bağlantısı Sorunları

Koyeb'de MT5 native çalışmaz (Windows-only kütüphane). **Çözümler:**

#### Çözüm 1: Yahoo Finance Kullan (ÖNERİLEN)
Market verileri için Yahoo Finance kullanın:
```python
# Backend'de zaten var: yahoo_finance_provider.py
data = await yahoo_provider.get_data(symbol='EURUSD')
```

#### Çözüm 2: Hybrid Mimari
- **Cloud**: Market taraması + bildirimler
- **Lokal**: MT5 bağlantısı + trade execution

### Ücretsiz Tier Limitleri

- 512 MB RAM
- 100 GB bandwidth/ay
- 1 app (ücretsiz versiyonda)
- Always-on ✅

## 🔄 Auto-Deploy

Her `git push` sonrası otomatik deploy:

```bash
git add .
git commit -m "Update backend"
git push origin main
# Koyeb otomatik build ve deploy eder!
```

## 📊 Monitoring

**Koyeb Dashboard'da:**
- CPU/RAM kullanımı
- Bandwidth
- Logs (real-time)
- Deploy history

## 🎯 Sonuç

✅ **7/24 backend çalışıyor**
✅ **Ücretsiz (credit card yok)**
✅ **Auto-deploy (GitHub)**
✅ **WebSocket tam destek**

---

## ❓ Sorun Giderme

### Build Hatası

**Hata:** `Cannot find Dockerfile`
**Çözüm:** Build context'i `backend` olarak ayarlayın

**Hata:** `Port already in use`
**Çözüm:** Dockerfile'da `EXPOSE 8766` kontrol edin

### Runtime Hatası

**Hata:** `ModuleNotFoundError`
**Çözüm:** requirements.txt'e ekleyin ve redeploy

**Hata:** `Health check failed`
**Çözüm:** Health check endpoint'i kaldırın (WebSocket zaten bağlantı kontrolü yapıyor)

### Connection Timeout

- Koyeb'in free tier'ı başlangıçta yavaş olabilir (cold start)
- İlk bağlantı 5-10 saniye sürebilir
- Sonrası hızlı

---

## 🚀 İLERİ SEVİYE

### Custom Domain

Paid plan gerekir ($5.5/ay):
- **uceasistan.com** → Koyeb app
- SSL otomatik

### Persistent Storage

Stratejileri saklamak için harici DB:
- **Supabase** (ücretsiz PostgreSQL)
- **MongoDB Atlas** (ücretsiz 512 MB)

### Scaling

Paid plan'da:
- Auto-scaling
- Daha fazla RAM (2 GB+)
- Daha hızlı CPU

---

**Deployment başarılı olunca bana bildirin!** 🎉
