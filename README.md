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
| **Veritabanı** | SQLite (OHLCV cache + paper trades) |
| **Veri** | ProviderRouter, yfinance best-effort BIST/FX/emtia, Binance WS/REST, lisanslı BIST/VİOP HTTP köprüleri |
| **Backtest** | Custom engine (lookahead-free, 9 strateji) |
| **Bildirim** | Telegram bot, Email (SMTP), macOS notification |
| **Deployment** | Docker Compose, nginx reverse proxy |
| **AI Ekosistemi** | Claude Code agents/skills/hooks/MCP |

## 🚀 Hızlı Başlangıç

```bash
# 1. Sanal ortamı oluştur
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Backend'i başlat
uvicorn backend.api.main:app --port 8000 --reload

# 3. Frontend'i başlat (geliştirme)
cd piyasapilot-v2 && npm install && npm run dev

# 4. Veya Docker ile
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
├── backend/                 # FastAPI gateway
│   ├── api/main.py          # App factory + tüm endpoint'ler
│   ├── backtest/            # Backtest runner + blueprint'ler
│   ├── data/                # OHLCVCache + spike filter
│   ├── paper/               # Paper trading (db + executor)
│   ├── signals/             # SignalGenerator v2
│   ├── notifier/            # Telegram + email + macOS
│   └── workers/             # Binance WS + Yahoo/BIST pollers
├── piyasapilot-v2/          # TypeScript frontend
│   ├── src/components/      # UI bileşenleri
│   ├── src/core/            # DataEngine, QuoteStream
│   └── src/indicators/      # Teknik göstergeler
├── quant_engine/            # Python backtest framework
│   ├── backtest/            # Lookahead-free engine
│   ├── data/                # ProviderRouter + market data modelleri
│   └── strategy/            # 9 strateji implementasyonu
├── .claude/                 # AI ekosistemi
│   ├── agents/              # 8 sub-agent
│   ├── skills/              # 15 skill
│   ├── commands/            # 5 slash command
│   └── hooks/               # 4 hook script
├── tests/                   # 301+ test (unit + integration)
├── docker-compose.yml       # Deployment
└── Makefile                 # Kısayollar
```

## 🛠️ CLI Araçları ve Denetim (Agent Skills)

PiyasaPilot repomuz AI ekosistemi tarafından kullanılmak veya kullanıcı tarafından elle tetiklenmek üzere çesitli Python scriptleri içerir:

```bash
# Veri platformu kontrolleri
python src/scripts/check_data_inventory.py
python src/scripts/check_timeframe_graph.py
python src/scripts/check_retention.py

# Deployment ve Temizlik kontrolleri
python src/scripts/scan_repo_weight.py
python src/scripts/check_borfin_integration.py
python src/scripts/check_production_package.py
python src/scripts/check_deployment_readiness.py
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

## 📋 Sprint Durumu

| Sprint | Durum | Açıklama |
|--------|-------|----------|
| 0 — Planlama | ✅ | CLAUDE.md, iskelet, sembol listesi |
| 1 — Backend Gateway | ✅ | FastAPI, SQLite, worker'lar |
| 2 — Frontend Terminal | ✅ | Sidebar, ChartPanel, MultiChartLayout |
| 3 — Backtest API | ✅ | 9 strateji, sinyal feed, signal bus |
| 4 — Paper Trading | ✅ | PaperDB, PaperExecutor, PortfolioPanel v2 |
| 5 — Agent/Skill/Hook | ✅ | 8 agent, 15 skill, 5 command, 4 hook |
| 6 — AI Sinyal Motoru | ✅ | Konsensüs, sinyal gücü, metadata |
| 7 — Always-On | ✅ | Docker, Telegram, email, toast |
| 8 — Doküman | ✅ | README, mimari, rehberler |

## 📄 Lisans

Bu proje kişisel araştırma ve eğitim amaçlıdır.

---

<p align="center">
  <sub>PiyasaPilot v2.0 — Algoritma tabanlı trading terminali</sub>
</p>
