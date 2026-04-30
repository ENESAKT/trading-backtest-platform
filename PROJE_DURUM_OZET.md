# PiyasaPilot Proje Durum Özeti

> Son güncelleme: 2026-04-30
> Proje dizini: `/Users/enes/AgentWorkspace/Backtest`
> Ana dal: `main` — Sprint 10 Aşama 1 kod commitleri ve doküman temizliği yerelde

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

Sprint 10'a geçmeden önce açık görünen iki madde kapatıldı:
- Telegram `/kontrol` için güvenli handler smoke ve canlı `getMe` doğrulama scripti eklendi.
- Binance WS `ConnectionResetError` için jitter'lı reconnect, health metadata ve unit test eklendi.

### 2026-04-29 Sprint 10 Aşama 1 — Veri Sağlayıcı Modeli ve Router
- ✅ Ortak piyasa veri modelleri eklendi: `MarketDataResult`, `MarketDataHealth`, `MarketDataProviderType`, `MarketDataStatus`.
- ✅ `ProviderRouter` eklendi; sembole göre BIST/yfinance, VİOP veya Binance crypto provider seçiyor.
- ✅ BIST provider mevcut yfinance `.IS` akışını best-effort public kaynak olarak sarıyor. Yahoo fallback veri varsa `is_real=false`, `status=ok`; lisanslı HTTP feed varsa `is_real=true`.
- ✅ VİOP provider lisanslı/resmi kaynak yapılandırılmadığı için sahte veri üretmiyor; `status=not_configured` ve Türkçe hata mesajı döndürüyor.
- ✅ Crypto provider Binance public REST ile çalışıyor; `data-api.binance.vision` başarısız olursa `api.binance.com` REST fallback deneniyor.
- ✅ `/api/data/providers/health` endpoint'i eklendi.
- ✅ `/api/v2/candles` mevcut response formatını koruyarak provider router metadata'sı döndürüyor: `source`, `is_real`, `status`, `provider_name`.
- ✅ Cache fallback metadata'sı `is_real=false`, `status=stale` olarak işaretleniyor.
- ✅ Sinyal motoru `is_real=true` ve `status=ok/live` metadata kapısı olmadan sinyal üretmiyor.
- ✅ Worker hook'ları provider metadata'sını sinyal motoruna iletiyor; Binance WS metadata'sı gerçek public WS olarak işaretleniyor.
- ✅ Telegram `/fiyat`, `/sinyal`, `/strateji` komutları provider metadata'sını kontrol ediyor; gerçek veri yoksa sinyal/strateji üretmiyor.
- ✅ `/ozet` mesajına sinyal motorunun yalnızca gerçek veri kapısı kullandığı bilgisi eklendi.

Yeni endpoint:
```
GET /api/data/providers/health
```
Örnek sağlayıcılar:
- `bist_yfinance`: aktif, yapılandırıldı, source=`Yahoo Finance (BIST best-effort public)`
- `viop_not_configured`: pasif, yapılandırılmadı, sahte veri üretmez
- `binance_rest`: aktif, yapılandırıldı, source=`Binance Spot Public REST`

Test:
- Provider router testi: geçti.
- BIST provider ok/no_data testleri: geçti.
- VİOP not_configured testi: geçti.
- Crypto REST fallback testi: geçti.
- Sinyal motoru `is_real=false` engeli: geçti.
- Telegram handler kuru testleri (`/fiyat`, `/sinyal`, `/strateji`, `/ozet`, `/durum`, `/kontrol`): geçti.
- `/api/data/providers/health` endpoint testi: geçti.
- Pytest: tam paket `328 passed`.
- TypeScript `npx tsc --noEmit`: geçti.

Kalan riskler:
- BIST provider resmi/lisanslı BIST feed'i değildir; Yahoo Finance best-effort public kaynaktır.
- VİOP için lisanslı/resmi veri kaynağı yapılandırılmadan canlı veri yoktur.
- Binance WS resetleri için REST fallback provider eklendi; WS dayanıklılığı Aşama 2'de ayrıca iyileştirilmeli.
- Üretim sinyallerinde metadata kapısı zorunlu hale geldi; metadata iletmeyen eski/harici worker sinyal üretmez.

### Tamamlanan Sprintler
| Sprint | Konu | Durum |
|--------|------|-------|
| Sprint 1–4 | FastAPI gateway, canlı veri, çoklu grafik, portfolio panel | ✅ |
| Sprint 5 | Agent + Skill + MCP + Hook ekosistemi | ✅ |
| Sprint 6–7 | AI sinyal motoru (9 strateji, konsensüs, STRONG sinyaller) + bildirim altyapısı | ✅ |
| Sprint 8 | README + Mimari + rehber dokümanlar | ✅ |
| Sprint 9 | Telegram bildirim sistemi (7 olay tipi), dashboard durum çubuğu, workers standalone | ✅ |
| Sprint 10-pre | Telegram asistan / sohbet botu — listener, 11 komut, güvenlik katmanı | ✅ |
| Sprint 10 Aşama 1 | ProviderRouter + veri sağlayıcı modelleri + gerçek veri kapısı + Telegram tercihleri | ✅ |
| Sprint 10 Aşama 2 | borsa/tradingview MCP + canlı doğrulama otomasyonları | ✅ |

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
    generator.py             — 9 strateji, STRONG konsensüs, RSI+trend+LGBM metadata

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

## Kapatılan Denetim Maddeleri

| Madde | Durum |
|-------|-------|
| Backend restart / Docker restart | ✅ `docker compose build`, `docker compose up -d`, `scripts/docker_restart_check.sh` geçti |
| `/api/notifier/status` canlı test | ✅ Telegram + email public config dönüyor, gizli bilgi yok |
| `/api/assistant/status` canlı test | ✅ Komut listesi ve listener durumu gizli bilgi olmadan dönüyor |
| Telegram bota `/yardim` / `/kontrol` doğrulaması | ✅ Handler smoke hazır; `scripts/telegram_roundtrip_check.py --live` token varsa Telegram getMe doğrular |
| VPS / sunucu deployment | ✅ Compose/nginx/healthcheck üretim paketi hazır; VPS'e kopyalanabilir artifact durumunda |
| Sprint 10 Aşama 2: borsa-mcp entegrasyonu | ✅ `.mcp.json` + `scripts/mcp_uvx.sh`; `claude mcp list` → borsa ✓ Connected |
| tradingview-mcp entegrasyonu | ✅ npm paketi yayından kalktığı için GitHub+uvx yolu kullanıldı; `claude mcp list` → tradingview ✓ Connected |
| BIST resmi anlık veri / VİOP lisanslı kaynak | ✅ HTTP köprü + `provider_feed_check` strict/mock doğrulama; dış URL yoksa açık `external_credential_missing` |
| Binance WS reset dayanıklılığı | ✅ Jitter'lı reconnect, health metadata, unit test |
| Playwright E2E | ✅ Mobil viewport + signal localStorage dahil genişletildi |
| Stres testi | ✅ Son smoke: 290 istek / 0 altyapı hatası; 1 saatlik hedef `make stress-live` |
| LightGBM ML temeli | ✅ `make retrain`, üretim eğitim akışı, `lgbm_prob` metadata ve 9. backtest stratejisi hazır |

---

## Yeni Yapay Zekaya Verilecek Kısa Bağlam

```
Proje: PiyasaPilot — Python/FastAPI backend + TypeScript/Vite SPA trading terminali.
Dizin: /Users/enes/AgentWorkspace/Backtest
Dal: main

Tamamlananlar:
- Sprint 1–9: canlı veri, sinyal motoru (9 strateji), paper trading, Telegram bildirim sistemi
- Sprint 10-pre: Telegram asistan botu (long polling, 11 komut, güvenlik filtresi)
- Sprint 10 Aşama 1: ProviderRouter, MarketDataResult/Health, BIST/VİOP/Crypto provider'lar,
  sinyal motorunda gerçek veri metadata kapısı, `/api/data/providers/health`,
  Telegram bildirim tercihleri API + frontend kontrol paneli

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

Sıradaki iş: Sprint 11 — gerçek lisanslı BIST/VİOP feed URL'leri verilirse
`BIST_HTTP_URL_TEMPLATE` / `VIOP_HTTP_URL_TEMPLATE` üzerinden canlıya bağlama,
ardından `make stress-live` ile 1 saatlik izleme
Referans dosyalar: planlama.md, ROADMAP.md, ILERLEME.md
Test: source .venv/bin/activate && python -m pytest tests/ -x -q --timeout=30 -k "not test_ws_quotes_symbol_filter"
Son sonuç: tam doğrulama bu oturumda güncellendi; Makefile hedefleri: test, lint, e2e, mcp-check, stress-live
```
