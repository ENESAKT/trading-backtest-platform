# PiyasaPilot Proje Durum Özeti

> Son güncelleme: 2026-04-29
> Proje dizini: `/Users/enes/AgentWorkspace/Backtest`
> Ana dal: `main` — origin'den 3 commit ileride

---

## Son Durum

### 2026-04-29 Güvenlik ve Telegram Çalışma Düzeltmeleri
- ✅ Backend, notifier ve Telegram listener için ortak `.env` yükleme helper'ı eklendi (`backend/config.py`).
- ✅ `.env` içeriği, token, API key ve chat id terminale/endpoint'e/Telegram cevabına açık yazdırılmayacak şekilde merkezi maskeleme eklendi.
- ✅ `/api/notifier/status` artık `token_son4` veya açık `chat_id` döndürmüyor; yalnızca yapılandırma boolean'ları dönüyor.
- ✅ `/api/assistant/status` listener durumunu ayrı notifier sürecinden heartbeat ile okuyabiliyor; mesaj içeriği yerine güvenli komut özeti tutuluyor.
- ✅ `python -m backend.notifier.main` ile listener `.env` değerlerini görebiliyor ve token/chat id loglamadan başlıyor.
- ✅ `httpx/httpcore` INFO logları notifier sürecinde kapatıldı; Telegram API URL'si token ile loglanmıyor.
- ✅ Telegram Markdown parse hatasında bildirim düz metin fallback ile tekrar gönderiliyor.
- ✅ `/kontrol` komutu çıplak `python` yerine `.venv/bin/python` kullanıyor; venv yoksa `sys.executable` fallback'i var.
- ✅ `scripts/test_telegram.py` token veya chat id yazdırmıyor, sadece yapılandırma durumunu bildiriyor.
- ✅ `data/runtime/` heartbeat dosyaları `.gitignore` kapsamına alındı.
- ✅ Başlatıldı/durduruldu sistem bildirimleri FastAPI import/test/reload döngüsünden çıkarıldı; yalnızca notifier sürecinden gider ve aynı olay 60 saniye içinde tekrarlanmaz.
- ✅ Telegram mesajlarında kaynak etiketi var: `Sistem bildirimi`, `Sinyal bildirimi`, `Komut cevabı`.
- ✅ `/durum` worker sağlık bilgisini `/api/health` listesinden doğru okuyor; veri yoksa `Worker durumu henüz raporlanmadı.` mesajı veriyor.

Doğrulama:
- `/api/notifier/status`: 200, gizli bilgi yok, `telegram_yapilandirildi=true`, `yetkili_kullanici_yapilandirildi=true`, `aktif=true`.
- `/api/assistant/status`: 200, gizli bilgi yok, `listener_aktif=true`, `llm_aktif=false`.
- Import testleri: geçti.
- Telegram listener import testi: geçti.
- Telegram commands import testi: geçti.
- `/kontrol` handler testi: Python yolu sorunu düzeldi.
- Telegram canlı test: yetkili kullanıcı tarafından `/yardim` ve `/durum` cevapları doğrulandı; sinyal bildirimi geldi. Handler seviyesinde `/kontrol` de temiz.
- Pytest kısa/full çalıştırma: `pytest tests/` sonucu 292 geçti, 1 warning.
- TypeScript `npx tsc --noEmit`: geçti.

Sprint 10'a geçmeden önce kalanlar:
- Gerçek Telegram roundtrip için yetkili kullanıcıdan bota `/kontrol` gönderilip cevap gözle doğrulanmalı.
- Binance WS tarafındaki `ConnectionResetError` uyarıları Sprint 10 veri sağlayıcı mimarisi içinde ele alınmalı.

### Tamamlanan Sprintler
| Sprint | Konu | Durum |
|--------|------|-------|
| Sprint 1–4 | FastAPI gateway, canlı veri, çoklu grafik, portfolio panel | ✅ |
| Sprint 5 | Agent + Skill + MCP + Hook ekosistemi | ✅ |
| Sprint 6–7 | AI sinyal motoru (8 strateji, konsensüs, STRONG sinyaller) + bildirim altyapısı | ✅ |
| Sprint 8 | README + Mimari + rehber dokümanlar | ✅ |
| Sprint 9 | Telegram bildirim sistemi (7 olay tipi), dashboard durum çubuğu, workers standalone | ✅ |
| Sprint 10-pre | Telegram asistan / sohbet botu — listener, 11 komut, güvenlik katmanı | ✅ |
| Sprint 10 | borsa-mcp (Türk borsası / BIST / VİOP gerçek veri entegrasyonu) | 📋 Planlandı |

### Telegram Bildirim Sistemi
- ✅ 7 olay tipi: bot başladı/durdu, yeni sinyal, alım, satım, cüzdan donduruldu, hata, günlük özet
- ✅ STRONG_BUY / STRONG_SELL sinyallerinde otomatik Telegram bildirimi
- ✅ `/api/notifier/status` endpoint aktif
- ✅ Dashboard Sinyaller tab'ında canlı Telegram durum çubuğu (`#tg-status`)
- ⚠️ `.env`'de `TELEGRAM_BOT_TOKEN` ve `TELEGRAM_CHAT_ID` ayarlanmadan bildirimler pasif

### Telegram Asistan Sistemi
- ✅ Long polling listener (`backend/notifier/telegram_listener.py`)
- ✅ 11 komut: `/yardim`, `/durum`, `/fiyat`, `/sinyal`, `/strateji`, `/ozet`, `/son`, `/hata`, `/kontrol`, `/gorev`, `/duzelt`
- ✅ Yalnızca `TELEGRAM_CHAT_ID` sahibi kullanıcıya yanıt — diğerleri `⛔ Yetkisiz erişim`
- ✅ Rate limit: komut başına 5s cooldown, saatlik 60 mesaj limiti, hata susturma 5dk
- ✅ 27-pattern güvenlik filtresi (rm, sudo, git push, .env okuma, token yazdırma vb.)
- ✅ Serbest sohbet: `ANTHROPIC_API_KEY` varsa `claude-haiku` ile yanıtlanır; yoksa komut listesine yönlendirir
- ✅ `/api/assistant/status` endpoint aktif

### Backend Endpoint Durumu
```
GET /api/health              ✅ çalışıyor
GET /api/notifier/status     ✅ çalışıyor (restart sonrası aktif)
GET /api/assistant/status    ✅ çalışıyor (restart sonrası aktif)
GET /api/v2/candles          ✅ cache-aside OHLCV
GET /api/paper/wallets       ✅ paper trading
WS  /ws/signals              ✅ canlı sinyal fan-out
WS  /ws/quotes               ✅ canlı bar fan-out
```

### Dashboard Durumu
- ✅ 5-tab SPA: Grafikler, Sinyaller, Portfolio, Backtest, Ayarlar
- ✅ Sinyaller tab'ında Telegram durum çubuğu (30s polling)
- ✅ STRONG sinyal toast bildirimleri
- ✅ TypeScript: 0 hata
- Frontend port: 5173 (Vite), Backend port: 8000 (uvicorn)

### Güvenlik Durumu
- ✅ Telegram: yalnızca `TELEGRAM_CHAT_ID`'den gelen mesajlar işlenir
- ✅ `safe_actions.py`: 27 yasak pattern — rm, sudo, git push/commit/reset/clean, .env, token adları, printenv, export, /proc/, /etc/ vb.
- ✅ Gerçek alım-satım emri yok — yalnızca paper trading (sanal cüzdan)
- ✅ Demo/mock veri yok — veri yoksa "bulunamadı" döner
- ✅ Token/secret hiçbir zaman Telegram mesajına yazılmaz (`_mask_sensitive()` filtresi)

---

## Atılan Commitler (Son 3)

```
b66e324  feat: Telegram asistan komutları ve güvenlik katmanı
7519096  feat: Telegram worker ve dashboard durumunu tamamla
73504a6  feat: Telegram bildirim sistemi kuruldu
```

---

## Eklenen Özellikler

### Telegram Bildirim Olayları (`backend/notifier/telegram.py`)
- `bildir_bot_basladi()` / `bildir_bot_durdu()`
- `bildir_yeni_sinyal(signal)` — STRONG sinyal detayı
- `bildir_alim(strategy, symbol, price, qty, tutar, reason)`
- `bildir_satim(strategy, symbol, price, qty, pnl, reason)`
- `bildir_cuzdан_donduruldu(strategy, daily_loss, initial_capital)`
- `bildir_hata(hata, baglam)`
- `bildir_gunluk_ozet(wallets, trades)` — her gün 09:00'da otomatik

### Telegram Komutları (`backend/notifier/telegram_commands.py`)
| Komut | Açıklama |
|-------|----------|
| `/yardim` | Komut listesi |
| `/durum` | Sistem durumu (backend health, worker, Telegram, cache) |
| `/fiyat SEMBOL` | Anlık fiyat (örn: `/fiyat THYAO`, `/fiyat BTCUSDT`) |
| `/sinyal SEMBOL` | RSI + EMA + hacim analizi, AL/SAT/BEKLE kararı, güç skoru |
| `/strateji SEMBOL` | Teknik göstergeler (RSI, EMA, destek/direnç) |
| `/ozet` | Günlük paper trading özeti |
| `/son` | Son 20 sinyal listesi |
| `/hata` | Son backend hataları (token maskelenerek) |
| `/kontrol` | Proje sağlık kontrolü (import + TSC + pytest + backend) |
| `/gorev [metin]` | Görev analizi (git status + grep + log, değişiklik yapmaz) |
| `/duzelt [metin]` | Sorun analizi + rapor (commit atmaz) |

### Güvenlik Filtreleri (`backend/assistant/safe_actions.py`)
Yasak pattern'lar (27 adet):
`rm`, `sudo`, `git push`, `git reset`, `git clean`, `git add -A/.`, `git commit`, `git merge`, `git rebase`, `docker prune/rm/rmi`, `> /dev`, `chmod`, `chown`, `pkill`, `killall`, `DROP TABLE`, `DELETE FROM`, `truncate`, `.env`, `os.environ`, `telegram_bot_token`, `telegram_chat_id`, `anthropic_api_key`, `bot_token`, `printenv`, `export`, `/proc/`, `cat /etc/`

### Rate Limit (`backend/notifier/telegram_listener.py`)
- Komut başına 5s cooldown
- Saatlik 60 mesaj limiti
- Aynı hata tipi 5 dakikada bir kez Telegram'a iletilir

### Yetkisiz Chat ID Engeli
- `TELEGRAM_CHAT_ID`'den farklı her chat → `⛔ Yetkisiz erişim.`
- `TELEGRAM_CHAT_ID` boşsa tüm mesajlar sessizce reddedilir

### Dashboard Telegram Durum Alanı
- `piyasapilot-v2/src/components/SignalFeed.ts` — `pollTelegramStatus()` her 30s
- Renkli dot göstergesi: 🟢 aktif / 🟡 uyarı / 🔴 kapalı / ⚪ bilinmiyor
- STRONG sinyal toast bildirimleri (5s otomatik kapanır)

---

## Önemli Dosyalar

```
backend/
  notifier/
    telegram.py              — 7 olay bildirimi, send_telegram()
    telegram_commands.py     — 11 komut işleyicisi
    telegram_listener.py     — long polling, auth, rate limit
    main.py                  — notification_loop + daily_summary_loop + listener_loop
  assistant/
    safe_actions.py          — güvenli subprocess çalıştırıcı, 27 yasak pattern
    project_assistant.py     — /kontrol, /gorev, /duzelt mantığı
  api/
    main.py                  — FastAPI app, /api/notifier/status, /api/assistant/status
  paper/
    executor.py              — paper trading, Telegram bildirim entegrasyonu
  workers/
    __main__.py              — standalone cache-filler entry point (Docker split profil)
  signals/
    generator.py             — 8 strateji, STRONG konsensüs, RSI+trend confluence

piyasapilot-v2/
  src/components/SignalFeed.ts   — Telegram durum çubuğu, STRONG badge
  style.css                      — tg-*, signal-strong, toast CSS

Dockerfile.workers               — standalone workers container CMD
docker-compose.yml               — api + notifier + workers (split profil)
scripts/test_telegram.py         — 6 senaryolu Telegram bağlantı testi
```

---

## Çalıştırma Komutları

### Backend Başlatma
```bash
source .venv/bin/activate
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

### Notifier + Listener Başlatma (ayrı terminal)
```bash
source .venv/bin/activate
python -m backend.notifier.main
```

### Frontend Başlatma
```bash
cd piyasapilot-v2
npm run dev
```

### Test Çalıştırma
```bash
# Python testler
source .venv/bin/activate
python -m pytest tests/ -q --tb=short

# TypeScript tip kontrolü
cd piyasapilot-v2 && npx tsc --noEmit

# Telegram bağlantı testi (token .env'de ayarlı olmalı)
python scripts/test_telegram.py
```

### Endpoint Kontrol
```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/notifier/status
curl http://localhost:8000/api/assistant/status
```

### Docker ile Çalıştırma
```bash
# Temel mod (api + notifier)
docker-compose up

# Split mod (workers ayrı container)
docker-compose --profile split up
```

---

## Dikkat Edilecekler

- `.env` asla commit'e alınmaz — `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `ANTHROPIC_API_KEY` burada
- Token ve API key'ler asla Telegram mesajına, loga veya ekrana yazılmaz
- `git add -A` kullanılmaz — her dosya tek tek eklenir
- Gerçek alım-satım emri yok — `PaperExecutor` yalnızca sanal cüzdan yönetir
- Demo/mock fiyat verisi yok — veri yoksa `❌ bulunamadı` döner
- `data/cache/`, `*.sqlite3` commit'e alınmaz

---

## Kalan Eksikler

| Madde | Durum |
|-------|-------|
| Backend restart (yeni kod aktif olsun) | ✅ Bu oturumda yapıldı |
| `/api/notifier/status` canlı test | ✅ `{"telegram_yapilandirildi":false,...}` döndü |
| `/api/assistant/status` canlı test | ✅ `{"listener_aktif":false,"komutlar":[...]}` döndü |
| Telegram bota `/yardim` yazıp canlı test | ⏳ Token `.env`'de ayarlandığında yapılacak |
| VPS / sunucu deployment | 📋 Henüz yapılmadı |
| Sprint 10: borsa-mcp entegrasyonu | 📋 Planlandı, başlanmadı |
| BIST / VİOP gerçek veri entegrasyonu | 📋 Sprint 10 kapsamında |

---

## Yeni Yapay Zekaya Verilecek Kısa Bağlam

```
Proje: PiyasaPilot — Python/FastAPI backend + TypeScript/Vite SPA trading terminali.
Dizin: /Users/enes/AgentWorkspace/Backtest
Dal: main (3 commit ileride origin'den)

Tamamlananlar:
- Sprint 1–9: canlı veri, sinyal motoru (8 strateji), paper trading, Telegram bildirim sistemi
- Sprint 10-pre: Telegram asistan botu (long polling, 11 komut, güvenlik filtresi)

Aktif servisler:
- Backend: uvicorn backend.api.main:app --port 8000
- Notifier+Listener: python -m backend.notifier.main (listener_loop dahil)
- Frontend: cd piyasapilot-v2 && npm run dev (port 5173)

Güvenlik kuralları (sor):
- .env asla okunmaz/yazılmaz/commitlenmez
- git add -A kullanılmaz
- git commit/push için her seferinde onay al
- rm, sudo, git push, git reset gibi tehlikeli komut çalıştırılmaz
- Gerçek alım-satım emri verilmez

Sıradaki iş: Sprint 10 — borsa-mcp (Türk borsası gerçek veri entegrasyonu)
Referans dosyalar: planlama.md, ROADMAP.md, ILERLEME.md
Test: python -m pytest tests/ -q (292 test, 1 flaky WS testi aralıklı başarısız)
```
