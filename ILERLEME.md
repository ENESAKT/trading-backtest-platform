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
| Sprint 10 Aşama 2 | borsa-mcp entegrasyonu + canlı roundtrip testleri | 📋 Sırada |

**Sprint 10 Aşama 1 tamamlanmış ve commitlenmiştir.** borsa-mcp işi artık Sprint 10 Aşama 2 olarak ayrı takip edilir.

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

## 4. Açık/Ertelenmiş Kalemler

**Enes ortamında yapılandırılacak:**
- [ ] `.env` dosyasına `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` girişi
- [ ] `.env` dosyasına `SMTP_HOST` + `SMTP_USER` + `SMTP_PASSWORD` girişi
- [ ] `make up` ile Docker stack ilk çalıştırma + doğrulama

**Canlı ortam gerektiren testler:**
- [ ] Stres testi: 100 sembol × 1 saat polling, 0 hata
- [ ] Tarayıcı E2E: `make dev` + `make dev-frontend` → 5 tab + WS canlı
- [ ] Docker restart testi: `docker compose kill api` → 5 sn'de geri gel
- [ ] Notifier uçtan uca: test sinyali → 4 kanala düşüyor
- [ ] Telegram `/kontrol` canlı roundtrip testi
- [ ] Binance WS reset dayanıklılığı

**Uzun vadeli (veri birikimi gerekli):**
- [ ] ML model temelleri (LightGBM — cache 3–6 ay birikimine bağlı)
- [ ] E2E Playwright testleri (detaylı senaryo seti)
- [ ] VİOP resmi/lisanslı veri kaynağı
- [ ] BIST resmi anlık veri alternatifi
- [ ] borsa-mcp kurulumu ve `/sinyal` hibrit test

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
