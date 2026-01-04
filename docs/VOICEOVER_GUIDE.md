# 🎤 Video Seslendirme Kılavuzu

Bu kılavuz UceAsistan eğitim videoları için Türkçe seslendirme oluşturmayı açıklar.

---

## 🆓 Ücretsiz Türkçe TTS Araçları

### 1. Narakeet (Önerilen - Ücretsiz)
🔗 https://www.narakeet.com/languages/turkish-text-to-speech/

**Özellikler:**
- 74 farklı Türkçe ses
- Kayıt gerektirmez
- MP3 indirme
- Ücretsiz kullanım

**Kullanım:**
1. Siteye git
2. Metni yapıştır
3. Ses seç (erkek/kadın)
4. "Create Audio" tıkla
5. MP3 indir

---

### 2. ElevenLabs (En Kaliteli)
🔗 https://elevenlabs.io

**Özellikler:**
- Doğal ses kalitesi
- Duygu kontrolü
- Ücretsiz: 10.000 karakter/ay

**Kullanım:**
1. Ücretsiz hesap oluştur
2. "Speech Synthesis" seç
3. Dil: Turkish seç
4. Metni gir → Generate

---

### 3. CAMB.AI (Ücretsiz)
🔗 https://camb.ai/text-to-speech/turkish

**Özellikler:**
- Tamamen ücretsiz
- Doğal tonlama
- Hızlı oluşturma

---

## 📝 Video Seslendirme Metinleri

### Video 1: Dashboard Kullanımı (45 sn)
```
UceAsistan Dashboard'a hoş geldiniz.

Üst kısımda bakiye, varlık ve günlük kâr-zarar bilgilerinizi görebilirsiniz.

Risk durumu bölümü, maksimum düşüş ve günlük risk kullanımınızı gösterir.
Yeşil renk güvenli bölgede olduğunuzu ifade eder.

Açık işlemler bölümünde aktif pozisyonlarınız listelenir.
Varlık grafiği ise hesap performansınızı görselleştirir.

Hızlı strateji başlatıcı ile kayıtlı stratejilerinizi anında çalıştırabilirsiniz.
```

### Video 2: Strateji Test Etme (60 sn)
```
Backtest özelliği ile stratejilerinizi geçmiş verilerde test edebilirsiniz.

Hazır şablonlardan birini seçin veya kendi stratejinizi doğal dille tanımlayın.

RSI stratejisini seçtiğimizde, yapay zeka otomatik olarak Python kodunu oluşturur.

Test Parametreleri bölümünde sembol, zaman dilimi ve bakiye ayarlayın.

Testi Başlat butonuna tıklayın.

Sonuçlar bölümünde kazanma oranı, kâr faktörü ve maksimum düşüş görüntülenir.

Başarılı stratejileri Canlıya Al butonu ile gerçek işlemlerde kullanabilirsiniz.
```

### Video 3: API Kurulumu (90 sn)
```
UceAsistan'ın yapay zeka özelliklerini kullanmak için API anahtarı gereklidir.

Ayarlar butonuna tıklayın.

Yapay Zeka Sağlayıcı bölümünden Groq'u seçin. Groq ücretsiz ve hızlıdır.

API anahtarı almak için console.groq.com adresine gidin.

Google veya GitHub ile giriş yapın.

API Keys bölümünden Create API Key butonuna tıklayın.

Oluşturulan anahtarı kopyalayın.

UceAsistan'a dönün ve anahtarı yapıştırın.

Telegram bildirimleri için Bot Token ve Chat ID bilgilerinizi girin.

Ayarları Kaydet butonuna tıklayın.

Artık yapay zeka asistanınız hazır.
```

### Video 4: AI Asistan Kullanımı (45 sn)
```
UceAsistan yapay zeka asistanı sizi her konuda destekler.

Sağ alt köşedeki jaguar ikonuna tıklayarak sohbeti açın.

Piyasa analizi, strateji önerileri veya risk değerlendirmesi isteyebilirsiniz.

Örneğin: EURUSD için analiz yapar mısın?

Yapay zeka, gerçek zamanlı piyasa verilerini analiz eder ve size öneriler sunar.

İşlem yapmak istediğinizde: EURUSD al, yüzde bir stop ile

Asistan risk hesaplaması yapar ve onayınızla işlemi gerçekleştirir.
```

---

## 🎬 Video ile Sesi Birleştirme

### FFmpeg ile (Terminal)
```bash
# Sesi video ile birleştir
ffmpeg -i video.mp4 -i ses.mp3 -c:v copy -c:a aac -shortest output.mp4

# Tüm videolar için
ffmpeg -i dashboard_demo.mp4 -i dashboard_ses.mp3 -c:v copy -c:a aac -shortest dashboard_final.mp4
```

### DaVinci Resolve ile (Görsel)
1. DaVinci Resolve'u aç (ücretsiz)
2. Import → Video dosyasını ekle
3. Import → Ses dosyasını ekle
4. Timeline'a sürükle
5. Sesi videoya hizala
6. Export → MP4

---

## ⏱️ Zamanlama İpuçları

| Video | Süre | Ses Hızı |
|-------|------|----------|
| Dashboard | 45 sn | Normal |
| Backtest | 60 sn | Biraz yavaş |
| API Setup | 90 sn | Normal |
| AI Chat | 45 sn | Normal |

---

## 📂 Dosya Yapısı

```
assets/tutorials/
├── dashboard_demo.mp4      # Sessiz video
├── dashboard_ses.mp3       # Seslendirme
├── dashboard_final.mp4     # Sesli video ✓
├── backtest_demo.mp4
├── backtest_final.mp4
├── api_setup_demo.mp4
├── api_setup_final.mp4
├── ai_chat_demo.mp4
└── ai_chat_final.mp4
```

Sesli videoları oluşturduktan sonra `index.html`'deki video kaynaklarını `*_final.mp4` olarak güncelleyin.
