# Video Eğitimler Klasörü

Bu klasör UceAsistan eğitim videolarını içerir.

## Video Dosyaları

Aşağıdaki video dosyalarını bu klasöre yerleştirin:

| Dosya Adı | Açıklama | Kaynak |
|-----------|----------|--------|
| `dashboard_demo.mp4` | Dashboard kullanımı | WebP'den dönüştürülecek |
| `backtest_demo.mp4` | Strateji test etme | WebP'den dönüştürülecek |
| `api_setup_demo.mp4` | API kurulumu | WebP'den dönüştürülecek |
| `ai_chat_demo.mp4` | AI asistan kullanımı | WebP'den dönüştürülecek |

## WebP'den MP4'e Dönüştürme

Kayıtlar WebP formatındadır. MP4'e dönüştürmek için:

### FFmpeg ile (Önerilen)
```bash
# FFmpeg kurulu değilse: https://ffmpeg.org/download.html

# Tek dosya dönüştürme
ffmpeg -i uceasistan_dashboard_demo_*.webp -c:v libx264 dashboard_demo.mp4

# Tüm videoları dönüştürme
ffmpeg -i uceasistan_login_demo_*.webp -c:v libx264 login_demo.mp4
ffmpeg -i uceasistan_dashboard_demo_*.webp -c:v libx264 dashboard_demo.mp4
ffmpeg -i uceasistan_terminal_journal_*.webp -c:v libx264 terminal_journal_demo.mp4
ffmpeg -i uceasistan_ai_features_*.webp -c:v libx264 ai_chat_demo.mp4
ffmpeg -i uceasistan_api_setup_*.webp -c:v libx264 api_setup_demo.mp4
```

### Online Dönüştürücü
1. https://cloudconvert.com/webp-to-mp4
2. WebP dosyasını yükleyin
3. MP4 olarak indirin
4. Bu klasöre taşıyın

## Kaynak Dosyalar

WebP kayıtları şu klasörde:
```
C:\Users\umutc\.gemini\antigravity\brain\f91958af-0f55-4af4-b974-97e1fbb857b1\
```

Dosyalar:
- `uceasistan_login_demo_*.webp`
- `uceasistan_dashboard_demo_*.webp`
- `uceasistan_terminal_journal_*.webp`
- `uceasistan_ai_features_*.webp`
- `uceasistan_api_setup_*.webp`

## Seslendirme Ekleme

Seslendirme metinleri için: `docs/VIDEO_SCRIPTS.md`

```bash
# Seslendirme ile birleştirme
ffmpeg -i video.mp4 -i narration.mp3 -c:v copy -c:a aac output_with_audio.mp4
```
