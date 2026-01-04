# 🐆 UceAsistan - Premium Trading Intelligence Platform

<p align="center">
  <img src="assets/jaguar_logo.jpg" alt="UceAsistan Logo" width="150" />
</p>

<p align="center">
  <strong>AI-Powered Trading Coach & Risk Guardian</strong><br>
  MetaTrader 5 ile entegre çalışan profesyonel trading platformu
</p>

<p align="center">
  <a href="#özellikler">Özellikler</a> •
  <a href="#kurulum">Kurulum</a> •
  <a href="#kullanım">Kullanım</a> •
  <a href="#api">API</a> •
  <a href="#geliştirme">Geliştirme</a>
</p>

---

## 📋 İçindekiler

- [Özellikler](#özellikler)
- [Sistem Gereksinimleri](#sistem-gereksinimleri)
- [Hızlı Kurulum](#hızlı-kurulum)
- [Yapılandırma](#yapılandırma)
- [Kullanım](#kullanım)
- [API Referansı](#api-referansı)
- [Mimari](#mimari)
- [Geliştirme](#geliştirme)
- [Docker ile Çalıştırma](#docker-ile-çalıştırma)
- [Lisans](#lisans)

---

## ✨ Özellikler

### 🤖 AI Destekli Özellikler
- **AI Strategy Wizard** - Doğal dille strateji oluşturma (Groq/OpenAI/Gemini)
- **Smart Chat Coach** - 4 farklı kişilik ile etkileşimli trading koçu
- **Strategy Evolution** - Mevcut stratejileri AI ile optimize etme

### 📊 Trading Araçları
- **Backtest Engine** - Profesyonel strateji test motoru
- **Neural Pulse** - Gerçek zamanlı Smart Money Concepts (SMC) analizi
- **Global Confluence Radar** - 20+ sembolde eş zamanlı sinyal tarama
- **Oracle Path Projection** - AI destekli fiyat projeksiyonu

### ⚠️ Risk Yönetimi
- **Prop Firm Rules Engine** - FTMO, TopStep, MFF kuralları otomatik takip
- **Drawdown Recovery Planner** - Kayıp telafi planlaması
- **Real-time Risk Alerts** - Telegram bildirimleri

### 📝 Analiz & Raporlama
- **Trade Journal** - Otomatik trade günlüğü
- **Performance Analytics** - Detaylı performans metrikleri
- **Multi-Timeframe Analysis** - Çoklu zaman dilimi analizi

---

## 💻 Sistem Gereksinimleri

| Bileşen | Minimum | Önerilen |
|---------|---------|----------|
| **İşletim Sistemi** | Windows 10 | Windows 11 |
| **Python** | 3.10+ | 3.11+ |
| **RAM** | 4 GB | 8 GB |
| **MetaTrader 5** | Terminal kurulu | Algo trading aktif |
| **Tarayıcı** | Chrome/Edge | Chrome (son sürüm) |

---

## 🚀 Hızlı Kurulum

### 1. Repository'yi Klonlayın
```bash
git clone https://github.com/yourusername/uceasistan.git
cd uceasistan
```

### 2. Python Bağımlılıklarını Kurun
```bash
cd backend
pip install -r requirements.txt
```

### 3. Yapılandırma Dosyasını Oluşturun
```bash
cp .env.example .env
# .env dosyasını düzenleyin ve API anahtarlarınızı ekleyin
```

### 4. Sunucuyu Başlatın
```bash
python start_server.py
```

### 5. Web Arayüzünü Açın
Tarayıcıda `index.html` dosyasını açın veya:
```bash
# Basit HTTP server ile
python -m http.server 8000
# http://localhost:8000 adresine gidin
```

---

## ⚙️ Yapılandırma

### Ortam Değişkenleri (.env)

```env
# Server
HOST=localhost
PORT=8766
DEBUG=false

# AI Provider (En az birini doldurun)
GROQ_API_KEY=gsk_xxxxx          # Ücretsiz: https://console.groq.com
OPENAI_API_KEY=sk-xxxxx         # Ücretli: https://platform.openai.com
GEMINI_API_KEY=xxxxx            # Ücretsiz: https://aistudio.google.com

# Telegram Bildirimleri (Opsiyonel)
TELEGRAM_BOT_TOKEN=123456:ABCxxx
TELEGRAM_CHAT_ID=123456789
TELEGRAM_ENABLED=true
```

### Prop Firm Ayarları

Web arayüzündeki **Ayarlar** menüsünden:
- Maximum Drawdown limiti (%)
- Günlük kayıp limiti (%)
- Prop firm seçimi (otomatik algılama)

---

## 📖 Kullanım

### Dashboard
Ana ekran gerçek zamanlı olarak şunları gösterir:
- 💰 Bakiye ve Equity
- 📈 Günlük kar/zarar
- ⚠️ Risk durumu ve drawdown
- 📊 Açık pozisyonlar

### AI Strateji Oluşturma
1. **Backtest** sekmesine gidin
2. Stratejinizi doğal dille açıklayın
3. **"AI ile Üret"** butonuna tıklayın
4. Üretilen kodu inceleyin ve backtest çalıştırın
5. Başarılı stratejileri **Şablon Olarak Kaydet**

### Neural Pulse Analizi
1. **Neural Pulse** sekmesine gidin
2. Sembol seçin (EURUSD, XAUUSD, vb.)
3. Gerçek zamanlı SMC verilerini inceleyin:
   - Trend Bias
   - Order Blocks
   - Liquidity Sweeps
   - Fair Value Gaps

---

## 🔌 API Referansı

### REST API (Port 8080)

```bash
# Health Check
GET /api/v1/health

# Account Info
GET /api/v1/account
GET /api/v1/account/positions

# Market Analysis
GET /api/v1/market/{symbol}
GET /api/v1/market/symbols

# Strategies
GET /api/v1/strategies
POST /api/v1/strategies
DELETE /api/v1/strategies/{id}

# Templates
GET /api/v1/templates
```

### WebSocket API (Port 8766)

```javascript
// Bağlantı
const ws = new WebSocket('ws://localhost:8766');

// Hesap verisi al
ws.send(JSON.stringify({ action: 'get_account_data' }));

// Market analizi
ws.send(JSON.stringify({ action: 'get_market_analysis', symbol: 'EURUSD' }));

// Backtest çalıştır
ws.send(JSON.stringify({
    action: 'run_backtest',
    strategy_code: '...',
    symbol: 'EURUSD',
    timeframe: 'H1',
    start_date: '2024-01-01',
    end_date: '2024-12-31'
}));
```

---

## 🏗️ Mimari

```
┌─────────────────────────────────────────────────────┐
│                    Web Browser                       │
│  ┌─────────────────────────────────────────────┐    │
│  │           Frontend (HTML/CSS/JS)             │    │
│  │  • Dashboard  • Backtest  • Neural Pulse    │    │
│  └───────────────────────┬─────────────────────┘    │
└──────────────────────────┼──────────────────────────┘
                           │ WebSocket / REST
┌──────────────────────────┼──────────────────────────┐
│              Python Backend                          │
│  ┌───────────────────────┴─────────────────────┐    │
│  │  start_server.py (WebSocket :8766)          │    │
│  │  api.py (FastAPI REST :8080)                │    │
│  └───────────┬───────────────────┬─────────────┘    │
│              │                   │                   │
│  ┌───────────┴───┐   ┌───────────┴───────┐         │
│  │  MT5 Bridge   │   │   AI Providers    │         │
│  │  (MetaTrader) │   │ (Groq/OpenAI/...)│         │
│  └───────────────┘   └───────────────────┘         │
└─────────────────────────────────────────────────────┘
```

---

## 🧪 Geliştirme

### Proje Yapısı

```
uceasistan/
├── backend/
│   ├── start_server.py      # Ana WebSocket server
│   ├── api.py               # REST API (FastAPI)
│   ├── config.py            # Konfigürasyon
│   ├── models.py            # Database modelleri
│   ├── error_handler.py     # Hata yönetimi
│   ├── ai_strategy_parser.py
│   ├── backtest_engine.py
│   ├── live_trader.py
│   └── ...
├── assets/
├── docker/
├── .github/workflows/
├── index.html
├── app.js
├── styles.css
└── ...
```

### Test Çalıştırma

```bash
cd backend
pytest -v
```

### Linting

```bash
ruff check backend/
```

---

## 🐳 Docker ile Çalıştırma

```bash
# Build
docker-compose build

# Başlat
docker-compose up -d

# Logları izle
docker-compose logs -f
```

> **Not:** MT5 Windows gerektirdiğinden, tam işlevsellik için backend'i native Windows'ta çalıştırmanız önerilir.

---

## 📄 Lisans

© 2024 UceAsistan. Tüm hakları saklıdır.

---

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit edin (`git commit -m 'Add amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

---

<p align="center">
  Made with ❤️ for traders
</p>
