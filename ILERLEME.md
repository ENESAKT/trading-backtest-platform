# İlerleme Raporu — PiyasaPilot v2

> **Tarih:** 2026-04-29
> **Branch:** `main`
> **Tek doğruluk kaynağı:** `planlama.md`.

---

## 1. Sprint Durumu (Özet)

| Sprint | Konu | Durum |
|--------|------|-------|
| Sprint 0 | Bağlam ve Onay | ✅ Tamamlandı |
| Sprint 1 | Backend Data Gateway | ✅ Tamamlandı |
| Sprint 2 | Frontend Birleşimi | ✅ Tamamlandı |
| Sprint 3 | Strateji & Backtest Birleşimi | ✅ Tamamlandı |
| Sprint 4 | Paper Trading & Portföy | ✅ Tamamlandı |
| Sprint 5 | Agent + Skill + MCP + Hook | ✅ Tamamlandı |
| Sprint 6 | AI Sinyal Motoru | ✅ Tamamlandı |
| Sprint 7 | Always-On & Bildirim | ✅ Tamamlandı |
| Sprint 8 | Test, Doküman, Hand-off | ✅ Tamamlandı |
| Sprint 9 | Polish & Production Hardening | ✅ Tamamlandı |
| Sprint 10 Aşama 1 | ProviderRouter + gerçek veri kapısı + Telegram tercihleri | ✅ Tamamlandı |
| Sprint 10 Aşama 2 | MCP entegrasyonu + E2E/stres/Docker canlı doğrulamalar | ✅ Tamamlandı |

**Sprint 10 Aşama 1 ve Aşama 2 tamamlanmıştır.** borsa/tradingview MCP bağlantısı, E2E, stres smoke, Docker restart check, lisanslı veri köprüleri ve Telegram/SMTP doğrulama kapıları hazırdır.

---

## 2. Hızlı Sayılar

| Metrik | Değer |
|--------|-------|
| Test (pytest) | **301 passed, 1 deselected**, 1 FutureWarning (`test_ws_quotes_symbol_filter` Makefile filtresiyle dışarıda) |
| TSC compile | ✅ Temiz (0 hata) |
| Vite build | ✅ Temiz |
| Stratejiler | 8 (ema_cross, rsi_reversion, bb_reversion, breakout, donchian, macd_div, supertrend, vwap_mean_rev) |
| Sembol kapsamı | ~130 (BIST 98 + Kripto 10 + FX/Emtia) |
| Frontend bileşenler | 7 (ChartPanel, MultiChartLayout, PortfolioPanel, StrategyPanel, Screener, Sidebar, SignalFeed) |
| Backend API endpoint'leri | 18+ (health, provider health, notifier preferences, backtest, paper, candles, WS quotes, WS signals) |
| Sub-agent'lar | 8 |
| Skill'ler | 15 |
| Slash command'lar | 5 |

---

## 3. Mimari Katmanlar

```
Tarayıcı (Vite SPA) ──HTTP/WS──→ FastAPI Gateway (port 8000)
                                    ├── /api/v2/candles (cache-aside)
                                    ├── /api/backtest/run (8 strateji)
                                    ├── /api/paper/* (cüzdan, trade, equity)
                                    ├── /ws/quotes (canlı bar fan-out)
                                    └── /ws/signals (sinyal fan-out)
                                           │
              ┌───────────────────────────┤
              ▼                           ▼
   Worker Supervisor              SignalGenerator v2
   ├── BinanceKlineWorker         ├── 8 strateji paralel
   ├── YahooPoller                ├── RSI + Trend confluence
   └── BistStockPoller            ├── Konsensüs (STRONG_BUY/SELL)
         │                        └── Metadata (RSI, ATR, volatilite)
         ▼
   ProviderRouter ──→ SQLite OHLCV Cache ──→ IQR Spike Filter
```

---

## 4. Kapanan Risk Kalemleri

**Gizli bilgi ve dış servis kapıları:**
- [x] Telegram token/chat id `.env` içinde kalır; değerler log/API/Telegram cevabında maskelenir.
- [x] SMTP ayarları `.env.example` ve `/api/notifier/status.email` üzerinden güvenli doğrulanır.
- [x] `make up` / Docker stack doğrulandı; `scripts/docker_restart_check.sh` geçti.

**Canlı doğrulama ve otomasyonlar:**
- [x] Stres testi otomasyonu: `scripts/stress_live_data.py`; smoke sonucu 470 istek / 0 altyapı hatası.
- [x] Playwright E2E: `npm run e2e` → 2 passed.
- [x] Docker restart testi: `scripts/docker_restart_check.sh` → geçti.
- [x] Notifier uçtan uca kapısı: Telegram tercih UI + email status + handler smoke testleri.
- [x] Telegram `/kontrol`: `scripts/telegram_roundtrip_check.py` handler smoke geçti; `--live` token varsa getMe kontrolü yapar.
- [x] Binance WS reset dayanıklılığı: jitter'lı backoff + reconnect metadata + unit test.

**Veri ve ML kapıları:**
- [x] LightGBM temeli: feature extraction + readiness gate; veri yoksa sahte model üretmez.
- [x] VİOP resmi/lisanslı veri köprüsü: `VIOP_HTTP_URL_TEMPLATE`.
- [x] BIST resmi/lisanslı veri köprüsü: `BIST_HTTP_URL_TEMPLATE`; yoksa Yahoo best-effort fallback açıkça etiketlenir.
- [x] borsa-mcp + tradingview-mcp: `claude mcp list` ile Connected.

---

## 5. Son Commit'ler

```
(sprint-9-polish)  feat: Sprint 9 polish — STRONG sinyal UI + docker workers fix
dd43786 fix: Telegram env yükleme ve gizli bilgi maskeleme
7211dab feat: add market data provider router
b0c9b22 feat: add Telegram notification controls
69a384d docs: Sprint 8 tamamlandı — README + Mimari + Agent/Skill rehberleri
90d7190 feat: Sprint 6 + Sprint 7 tamamlandı — AI sinyal motoru + bildirim altyapısı
a7c0d50 feat: Sprint 5 tamamlandı — Agent + Skill + MCP + Hook ekosistemi kuruldu
```

## 6. Hızlı Başlangıç

```bash
# 1. .env dosyasını doldur
cp .env.example .env
# TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SMTP_* gir

# 2. Docker ile çalıştır
make up          # build + docker compose up -d
make health      # /api/health kontrol
make status      # tüm servisler + sağlık

# 3. Geliştirme ortamı
make dev         # backend (port 8000)
make dev-frontend  # frontend (port 5173)
```
