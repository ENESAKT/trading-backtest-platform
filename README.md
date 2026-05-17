# PiyasaPilot — Algoritmik Trading Terminali

<p align="center">
  <strong>BIST 100 · Kripto · ABD Piyasaları · FX/Emtia</strong><br>
  Gerçek zamanlı veri · 9 strateji · Paper trading · AI sinyal motoru
</p>

---

## 🏗️ Mimari

```
┌──────────────────────────────────────────────────────────────────┐
│                        PiyasaPilot Frontend                      │
│  TypeScript · Vite · lightweight-charts v4 · Chart.js            │
│  MultiChartLayout · Sidebar · StrategyPanel · PortfolioPanel     │
│  Screener · SignalFeed (toast) · Çoklu pencere (1×1/1×2/2×2)    │
└──────────┬──────────────────────────────────┬────────────────────┘
           │ REST /api/*                      │ WS /ws/quotes
           │                                  │ WS /ws/signals
┌──────────▼──────────────────────────────────▼────────────────────┐
│                    FastAPI Gateway (port 8000)                    │
│  Cache-aside OHLCV · ProviderRouter · Paper Trading API          │
│  SignalGenerator v2 (konsensüs) · SignalBus · QuoteBus           │
│  Gerçek veri metadata kapısı · IQR Spike Filter · Healthcheck    │
└──────────┬──────────────────────────────────┬────────────────────┘
           │                                  │
┌──────────▼──────────┐  ┌────────────────────▼───────────────────┐
│  Data Workers        │  │  Paper Executor                        │
│  • Binance WS (10)   │  │  • Sinyal → sanal emir                │
│  • Yahoo poller      │  │  • Strateji-bazlı izole cüzdan        │
│  • BIST hisse poller │  │  • Risk limitleri (%10 günlük)         │
└──────────────────────┘  └────────────────────────────────────────┘
```

**Zero-Demo Rule:** Frontend asla doğrudan dış API'ye istek yapmaz. Her şey lokal backend üzerinden.

## 📦 Tech Stack

| Katman | Teknoloji |
|:---|:---|
| **Frontend** | TypeScript, Vite 8, lightweight-charts v4, Chart.js, Playwright |
| **Backend** | Python 3.11, FastAPI, uvicorn |
| **Cache DB (mevcut)** | SQLite (OHLCV cache + paper trades) |
| **OHLCV DB (hedef)** | ClickHouse 24.3 |
| **Metadata DB (hedef)** | MySQL 8.0 |
| **Cache/Pub-Sub (hedef)** | Redis 7 |
| **Soğuk arşiv** | Parquet + DuckDB |
| **Veri** | yfinance (BIST/FX/emtia), Binance WS/REST, borsapy, borsa-mcp, tradingview-mcp |
| **Backtest** | Custom engine (lookahead-free, 9+ strateji, WFA, Monte Carlo) |
| **ML** | LightGBM (sinyal güçlendirme) |
| **Bildirim** | Telegram Bot (11 komut), Email (SMTP), macOS notification |
| **Deployment** | Docker Compose, nginx reverse proxy |
| **AI Ekosistemi** | Claude Code — 20 skill, 12 agent, MCP (borsa + tradingview) |

## 🚀 Hızlı Başlangıç

```bash
# 1. Sanal ortamı oluştur
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Ortam değişkenlerini ayarla
cp .env.example .env
# .env dosyasını düzenleyip JWT_SECRET, MYSQL_*, REDIS_URL vb. doldur

# 3. MySQL migration'larını uygula (001 → 010 sırayla, atlamadan)
mysql -h localhost -u appuser -p piyasapilot < infra/mysql/migrations/001_instruments.sql
mysql -h localhost -u appuser -p piyasapilot < infra/mysql/migrations/002_providers.sql
mysql -h localhost -u appuser -p piyasapilot < infra/mysql/migrations/003_inventory.sql
mysql -h localhost -u appuser -p piyasapilot < infra/mysql/migrations/004_retention.sql
mysql -h localhost -u appuser -p piyasapilot < infra/mysql/migrations/005_financial_analysis.sql
mysql -h localhost -u appuser -p piyasapilot < infra/mysql/migrations/006_financial_enhanced.sql
mysql -h localhost -u appuser -p piyasapilot < infra/mysql/migrations/007_auth_tables.sql
mysql -h localhost -u appuser -p piyasapilot < infra/mysql/migrations/008_security_extensions.sql
mysql -h localhost -u appuser -p piyasapilot < infra/mysql/migrations/009_growth_tables.sql
mysql -h localhost -u appuser -p piyasapilot < infra/mysql/migrations/010_mobile_payment_contracts.sql
# ⚠️ Migration 007 auth tablolarını, 008 güvenlik uzantılarını oluşturur — sıra kritik

# 4. Backend'i başlat
uvicorn backend.api.main:app --port 8000 --reload

# 5. Frontend'i başlat (geliştirme)
cd frontend && npm install && npm run dev

# 6. Veya Docker ile
make up
```

## 📊 Özellikler

### Çoklu Pencere Layout
4 layout modu: 1×1, 1×2, 2×1, 2×2. Her pencere kendi sembol/timeframe seçimine sahip.
**G** tuşu ile layout döngüsü.

### 8 Backtest Stratejisi
| Strateji | Açıklama |
|----------|----------|
| SMA Crossover | Hızlı/yavaş SMA çakışması |
| RSI Reversion | Aşırı alım/satım geri dönüşü |
| Bollinger Reversion | BB bandı geri dönüşü |
| Buy & Hold | Benchmark |
| Donchian Breakout | Kanal kırılımı |
| MACD Divergence | Sinyal çizgisi kesişimi |
| Supertrend | ATR tabanlı trend takibi |
| Mean Reversion VWAP | VWAP sapma geri dönüşü |

### Paper Trading
- Strateji-bazlı izole sanal cüzdanlar (10.000₺)
- Otomatik emir icra (PaperExecutor)
- Risk limitleri: pozisyon %10, günlük zarar %10
- Equity curve + drawdown grafikleri
- 6 metrik kartı: equity, PnL, win rate, profit factor, max DD, ort. K/Z

### AI Sinyal Motoru
- Sinyal gücü (1-10): RSI + trend confluence
- Konsensüs sistemi: 5+ strateji → STRONG_BUY/STRONG_SELL
- Gerçek veri kapısı: `is_real=true` ve güvenli `status` olmadan sinyal üretmez
- In-app toast bildirimi
- Telegram + email bildirim

### Telegram Asistan ve Bildirim Tercihleri
- 11 komutlu Telegram listener: `/yardim`, `/durum`, `/fiyat`, `/sinyal`, `/strateji`, `/ozet`, `/son`, `/hata`, `/kontrol`, `/gorev`, `/duzelt`
- Dashboard Sinyaller tab'ında Telegram durum çubuğu ve bildirim filtreleri
- Token/chat id endpoint ve loglarda maskelenir; `.env` commitlenmez

### Sprint 10 Doğrulama Araçları
- `make mcp-check` — borsa/tradingview MCP konfigürasyonunu doğrular
- `make e2e` — Playwright smoke testleri
- `make stress-live` — 100 sembol / 1 saat HTTP polling stres testi
- `make docker-restart-check` — Docker API restart healthcheck
- `python scripts/ml_readiness.py` — LightGBM veri yeterliliği raporu
- `make provider-check` / `make provider-check-strict` — lisanslı BIST/VİOP feed doğrulama
- `make retrain` — yeterli cache varsa LightGBM model eğitimi
- `make metrics-check` — canlı `/metrics` Prometheus çıktısı kontrolü

### Sembol Kapsamı
- **BIST 100:** 98/100 hisse
- **Kripto:** 10 parite (BTC, ETH, BNB, SOL, XRP, ADA, AVAX, DOT, DOGE, LINK)
- **ABD:** 20 hisse (AAPL, MSFT, NVDA, GOOGL, AMZN...)
- **FX/Emtia:** 8 parite (USD/TRY, EUR/TRY, GBP/TRY, Altın, Gümüş, Petrol, Doğalgaz, Bakır)

## 📁 Proje Yapısı

```
├── backend/                 # FastAPI gateway + Python servisleri
│   ├── api/main.py          # App factory + tüm endpoint'ler (1352 satır)
│   ├── backtest/            # Backtest runner + blueprint'ler
│   ├── data/                # OHLCVCache, repositories (CH/MySQL/Redis/SQLite)
│   ├── mali_analiz/         # Mali Analiz API + cache
│   ├── middleware/          # APIKeyMiddleware
│   ├── paper/               # Paper trading (db + executor)
│   ├── signals/             # SignalGenerator v2 (konsensüs)
│   ├── notifier/            # Telegram + email + macOS
│   └── workers/             # Binance WS + Yahoo/BIST pollers
├── frontend/                # TypeScript SPA
│   └── src/
│       ├── components/      # 9 UI bileşeni (Chart, Strategy, Portfolio, vb.)
│       ├── core/            # DataEngine, QuoteStream, HistoricalLoader
│       ├── indicators/      # 10 teknik indikatör
│       └── content/         # 57 eğitim makalesi
├── quant_engine/            # Bağımsız Python backtest framework
│   ├── backtest/engine.py   # Lookahead-free motor ⚠️
│   ├── data/                # ProviderRouter, live_feed ⚠️
│   ├── research/            # WFA, Monte Carlo, optimization_v2
│   └── strategy/            # 9 strateji + DSL + katalog + pack
├── infra/                   # Tüm Docker Compose dosyaları
│   ├── docker-compose.yml       # Geliştirme uygulama servisleri
│   ├── docker-compose.dev.yml   # Geliştirme DB (CH/MySQL/Redis)
│   ├── docker-compose.prod.yml  # Production tam stack
│   └── docker-compose.monitor.yml  # Grafana + Prometheus
├── docker/                  # Tüm Dockerfile'lar + nginx + izleme
│   ├── Dockerfile.api / .workers / .notifier / .frontend
│   ├── nginx.conf
│   └── prometheus.yml + grafana/
├── .claude/                 # Claude Code AI ekosistemi
│   ├── agents/              # 12 sub-agent
│   ├── skills/              # 20 skill
│   └── hooks/               # SessionStart, Stop, vb.
├── tests/                   # 59 dosya — unit + integration
├── scripts/                 # Denetim ve veri platform scriptleri
├── docs/                    # Teknik dokümantasyon + archive/
│   ├── YAPILANLAR.md        # Teknik envanter ve sprint özeti
│   └── YAPILACAKLAR.md      # Kalan işler, sunucu çıkış, güvenlik
└── Makefile                 # Kısayollar
```

## 🛠️ CLI Araçları ve Denetim

```bash
# Veri platformu
make data-inventory           # Sembol/timeframe envanter raporu
make derive-timeframes        # Timeframe rollup (1m → 5m → 1h vb.)
make retention-cleanup        # Retention politikası uygula
make backfill-bist100         # BIST 100 tarihsel veri doldurucu

# Denetim scriptleri
make repo-cleanup-report      # Büyük dosya ve artifact raporu
make borfin-integration-check # Borfin telif denetimi
make production-package-check # Docker paket kontrolü
make deployment-check         # Canlıya çıkış hazırlık kontrolü
make backup-now               # Production MySQL + ClickHouse yedeği

# İzleme
make monitor                  # Grafana (3000) + Prometheus (9090) başlat
make health                   # /api/health çıktısı
make prod-health              # Production sağlık kontrolü

# Test
make test                     # Hızlı pytest
make lint                     # TSC + vite build
make e2e                      # Playwright e2e
```

## 🧪 Testler

```bash
# Tüm testleri çalıştır
make test

# Detaylı çıktı
make test-full

# Lint (TSC + Vite build)
make lint
```

## 📋 Sprint / Faz Durumu

| Sprint / Faz | Durum | Konu |
|---|---|---|
| Sprint 0–8 | ✅ | Backend, Frontend, Paper, Agent/Skill, Sinyal, Docker, Docs |
| Sprint 9–12 | ✅ | MCP, LightGBM, stres test, sabah brifing, risk skill'leri |
| Faz 0A–0C | ✅ | ClickHouse/MySQL/Redis infra, repo temizliği, denetim skill'leri |
| Faz 1A | ✅ | Eğitimler paneli — 57 makale, arama, grafik/preset köprüleri |
| Faz 1B | ✅ | Mali Analiz metadata/API/UI v1 — universe, empty state |
| Faz 2 (G1–G10) | ✅ | Grafik Lab — ölçek, indikatör merkezi, PnL, çizim, multi-chart, Fibonacci |
| Faz 3 (B1–B13) | ✅ | Backtest Lab — WFA, Monte Carlo, optimize, tarayıcı, portföy, strategy pack |
| **Kalan** | 🔄 | ClickHouse/MySQL API bağlantısı, TLS domain/sertifika, Mali Analiz gerçek veri |

Detay: `docs/YAPILANLAR.md` (envanter) · `docs/YAPILACAKLAR.md` (kalan işler + güvenlik) · `docs/planning/` (alt planlar)

## 📄 Lisans

Bu proje kişisel araştırma ve eğitim amaçlıdır.

---

<p align="center">
  <sub>PiyasaPilot — Algoritma tabanlı trading terminali</sub>
</p>
