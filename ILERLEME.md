# İlerleme Raporu — PiyasaPilot v2

> **Tarih:** 2026-04-30
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
| Sprint 11.3 | Frontend Performans + UX | ✅ Tamamlandı |
| Sprint 11.4 | Gözlemlenebilirlik + Uyarılar | ✅ Tamamlandı |
| Sprint 11.5 | Güvenlik + Graceful Shutdown | ✅ Tamamlandı |

**Sprint 11 Adım 3–5 tamamlanmıştır.** Sidebar lazy-load, mobil responsive, sinyal localStorage, Prometheus metrics, Grafana dashboard, worker çöküş uyarıları, API key auth, env validation ve graceful shutdown hazırdır.

---

## 2. Hızlı Sayılar

| Metrik | Değer |
|--------|-------|
| Test (pytest) | **328 passed** |
| TSC compile | ✅ Temiz (0 hata) |
| Vite build | ✅ Temiz (39 modül, 612ms) |
| Stratejiler | 9 (sma, rsi, bollinger, buy_hold, donchian, macd, supertrend, vwap, lightgbm_probability) |
| Sembol kapsamı | ~130 (BIST 98 + Kripto 10 + FX/Emtia) |
| Frontend bileşenler | 7 (ChartPanel, MultiChartLayout, PortfolioPanel, StrategyPanel, Screener, Sidebar, SignalFeed) |
| Backend API endpoint'leri | 20+ (health, metrics, provider health, notifier preferences, backtest, paper, candles, WS quotes, WS signals) |
| Sub-agent'lar | 8 |
| Skill'ler | 15 |
| Slash command'lar | 5 |

---

## 3. Sprint 11 Yeni Eklenen Özellikler

### 11.3 Frontend Performans + UX
- **Sidebar lazy-load**: IntersectionObserver ile 15'lik batch'ler, 130 sembol artık performanslı
- **Mobil responsive**: 768px altında sidebar gizlenir, tek sütun grid, touch scroll
- **Tablet responsive**: 769–1024px arasında daraltılmış sidebar
- **İndikatör toggle**: Aktif/pasif durumda yeşil dot ve line-through görsel feedback
- **Sinyal geçmişi**: localStorage ile kalıcı; sayfa yenilendiğinde son 50 sinyal korunur

### 11.4 Gözlemlenebilirlik + Uyarılar
- **Prometheus `/metrics`**: Stdlib exposition format, dış bağımlılık yok (cache bars, symbols, worker up, signal bus)
- **Grafana dashboard**: `docker/grafana/dashboard.json` — 3 panel: API latency, cache stats, worker durumu
- **Docker Compose overlay**: `docker-compose.monitor.yml` + `docker/prometheus.yml`
- **Worker çöküş uyarısı**: `WorkerHealthMonitor` — 30s periyodik kontrol, 5dk cooldown, Telegram bildirim
- **Günlük sağlık raporu**: `scripts/daily_health_report.py` — /api/health çek, Telegram'a gönder
- **Makefile target'ları**: `make monitor`, `make monitor-down`, `make daily-report`, `make wal-check`

### 11.5 Güvenlik + Graceful Shutdown
- **API key auth**: `backend/middleware/api_key_auth.py` — API_KEY varsa X-API-Key header zorunlu; /api/health muaf
- **Env validation**: `backend/env_validator.py` — STRICT_ENV_VALIDATION=1 modunda eksik zorunlu değişken RuntimeError
- **SIGTERM graceful shutdown**: Lifespan finally'de paper_db.checkpoint() + WAL pragma
- **WAL checkpoint testi**: `scripts/wal_checkpoint_test.py` — veri bütünlüğü doğrulaması

---

## 4. Mimari Katmanlar

```
Tarayıcı (Vite SPA) ──HTTP/WS──→ FastAPI Gateway (port 8000)
                                    ├── /api/v2/candles (cache-aside)
                                    ├── /api/backtest/run (9 strateji)
                                    ├── /api/paper/* (cüzdan, trade, equity)
                                    ├── /metrics (Prometheus)
                                    ├── /ws/quotes (canlı bar fan-out)
                                    └── /ws/signals (sinyal fan-out)
                                           │
              ┌───────────────────────────┤
              ▼                           ▼
   Worker Supervisor              SignalGenerator v2
   ├── BinanceKlineWorker         ├── 9 strateji paralel
   ├── YahooPoller                ├── RSI + Trend confluence
   └── BistStockPoller            ├── Konsensüs (STRONG_BUY/SELL)
         │                        └── Metadata (RSI, ATR, volatilite)
         ▼
   ProviderRouter ──→ SQLite OHLCV Cache ──→ IQR Spike Filter
                                    │
              ┌─────────────────────┤
              ▼                     ▼
   WorkerHealthMonitor       Prometheus /metrics
   (çöküş → Telegram)       (Grafana dashboard)
```

---

## 5. Kalan İşler

| Adım | Konu | Durum | Bağımlılık |
|------|------|-------|------------|
| 11.1 | Lisanslı BIST/VİOP Feed | ✅ Kod + doğrulama kapısı hazır | Gerçek URL verilirse `make provider-check-strict` |
| 11.2 | LightGBM Sinyal Modeli | ✅ Eğitim akışı + strateji hazır | Model eğitimi için yeterli cache/veri gerekli |
| 11.3-E2E | Playwright mobil/localStorage testleri | ✅ Tamamlandı | `npm run e2e` |

---

## 6. Hızlı Başlangıç

```bash
# 1. .env dosyasını doldur
cp .env.example .env
# TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SMTP_*, API_KEY (opsiyonel) gir

# 2. Docker ile çalıştır
make up          # build + docker compose up -d
make health      # /api/health kontrol

# 3. İzleme altyapısı (Grafana + Prometheus)
make monitor     # Grafana: localhost:3000, Prometheus: localhost:9090

# 4. Geliştirme ortamı
make dev         # backend (port 8000)
make dev-frontend  # frontend (port 5173)

# 5. Test & doğrulama
make test        # 324 pytest
make lint        # TSC + Vite build
make wal-check   # WAL checkpoint testi
make daily-report-stdout  # Sağlık raporu (stdout)
```
