# PiyasaPilot — Mimari Dokümantasyonu

> Tarih: 2026-05-10 · Branch: `codex/financials-ui-api-v1`

---

## 1. Genel Bakış

PiyasaPilot, BIST ve kripto piyasaları için algoritmik analiz, backtest ve paper trading platformudur.

```
┌─────────────────────────────────────────────────────────┐
│                     Kullanıcı Tarayıcısı                │
│  TypeScript SPA (Vite + lightweight-charts + Chart.js)  │
│  Sekmeler: Graf | Portföy | Strateji | Tarayıcı |       │
│           Sinyaller | Eğitim | Finansallar | Haberler   │
└────────────────────────────┬────────────────────────────┘
                             │ HTTP / WebSocket
                             ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Gateway (port 8000)                 │
│  backend/api/main.py                                    │
│  • REST endpoint'leri (/api/*)                          │
│  • WebSocket hub'ları (/ws/quotes, /ws/signals)         │
│  • Paper trading executor loop                          │
│  • Haber arka plan worker (30dk interval)               │
└──────┬─────────────┬────────────────┬───────────────────┘
       │             │                │
       ▼             ▼                ▼
┌──────────┐  ┌──────────────┐  ┌─────────────────────────┐
│  SQLite  │  │  Worker      │  │  Mali Analiz             │
│  Cache   │  │  Supervisor  │  │  backend/mali_analiz/    │
│  (OHLCV) │  │  • BinanceWS │  │  • MySQL (finansallar)  │
│  (paper) │  │  • BistPoller│  │  • borsapy veri çekme   │
│  (news)  │  │  • YahooPoller│  │  • SQLite ratio cache  │
└──────────┘  └──────────────┘  └─────────────────────────┘
```

---

## 2. Katman Yapısı

### 2.1 Frontend (`frontend/`)

```
frontend/
├── src/
│   ├── app.ts                 # Ana orkestratör — tab yönetimi, URL deep-link, tema
│   ├── types.ts               # Paylaşılan TypeScript arayüzleri
│   └── components/
│       ├── ChartPanel.ts      # lightweight-charts v4 — 2980 satır
│       │   ├── Göstergeler: RSI, MACD, BB, ATR, Stoch, EMA, VWAP, GMMA, KAIRI, BBW
│       │   ├── Çizim araçları: trendline, hline, vline, fib, regression, measure
│       │   ├── Multi-sembol karşılaştırma (max 3 sembol, normalize-100 çizgi)
│       │   ├── Olay işaretçileri (G9 — KAP, bilanço, temettü)
│       │   └── Şablon sistemi (localStorage kalıcı)
│       ├── MultiChartLayout.ts # Çoklu panel layout (1x1, 1x2, 2x2)
│       ├── StrategyPanel.ts   # Backtest UI — 1870 satır
│       │   ├── Blueprint/spec/preset modları
│       │   ├── Equity curve (Chart.js)
│       │   ├── Optimizasyon heatmap (Canvas 2D)
│       │   ├── Walk-Forward tab (Chart.js bar)
│       │   └── Monte Carlo tab (Chart.js çizgi — 30 path + P5/P50/P95)
│       ├── MaliAnalizPanel.ts # Finansal analiz paneli
│       │   ├── 7 sekme: Özet | BIST30 | Bilanço | Gelir | Nakit | Oranlar | Grafikler
│       │   ├── lightweight-charts (14 finansal metrik serisi)
│       │   └── Waterfall Chart.js (Ciro/BrütKar/EBITDA/NetKar)
│       ├── NewsPanel.ts       # Haber akışı (8. sekme)
│       │   ├── yfinance haberleri (SQLite cache)
│       │   ├── Sembol + kelime filtresi
│       │   └── 5 dakikalık auto-refresh
│       ├── PortfolioPanel.ts  # Paper trading portföy görünümü
│       ├── Screener.ts        # Teknik tarayıcı (RSI, hacim, trend)
│       ├── SignalFeed.ts      # WS sinyal listesi + localStorage geçmişi
│       └── EducationPanel.ts  # 57 indikatör makalesi
├── style.css                  # CSS değişkenleri, tema, animasyonlar
├── playwright.config.ts       # E2E test konfigürasyonu
└── tests/e2e/                 # Playwright test suite
    ├── smoke.spec.ts          # 15+ kapsamlı UI testi
    └── critical_flows.spec.ts # 6 kritik akış testi
```

### 2.2 Backend (`backend/`)

```
backend/
├── api/
│   └── main.py               # FastAPI app factory — ~2100 satır
│       ├── Lifespan: workers + paper executor + news worker
│       └── Tüm REST + WS endpoint'leri
├── workers/
│   ├── __init__.py           # WorkerSupervisor
│   ├── binance_ws.py         # Binance WebSocket kline daemon
│   ├── bist_poller.py        # BIST hisse fiyat poller (yfinance)
│   ├── yahoo_poller.py       # Yahoo Finance genel poller
│   └── health_monitor.py     # Worker sağlık izleyici (Telegram uyarısı)
├── mali_analiz/
│   ├── symbols.py            # BIST_30_SYMBOLS, BIST_100_SYMBOLS (~93 sembol)
│   ├── harvester.py          # borsapy → MySQL veri hasat
│   ├── repository.py         # MySQL sorgu katmanı
│   ├── borsapy_provider.py   # borsapy adaptörü
│   └── ratios.py             # Finansal oran hesaplamaları
├── news/
│   ├── __init__.py           # NewsStore + fetch_news_for_symbol export
│   ├── news_store.py         # SQLite WAL — unique URL constraint
│   └── news_fetcher.py       # yfinance.Ticker.news → normalize
├── signals/
│   └── signal_bus.py         # WS sinyal yayın hub'ı
├── ml/
│   └── signal_model.py       # LightGBM sinyal modeli (test ortamı)
└── quant_engine/
    ├── backtest/engine.py    # Backtest motoru (dokunulmamalı)
    ├── strategy/indicators.py # RSI, MACD, BB, ATR, EMA hesaplamaları
    └── data/providers/       # veri sağlayıcılar (dokunulmamalı)
```

---

## 3. Veri Akışı

### 3.1 Canlı Fiyat Verisi
```
Binance WS / Yahoo Finance
    │
    ▼
WorkerSupervisor (background tasks)
    │  on_bar callback
    ▼
OHLCVCache (SQLite)  ←→  QuoteBus
    │                        │
    ▼                        ▼
GET /api/v2/candles     WS /ws/quotes
    │                        │
    ▼                        ▼
Frontend ChartPanel    Frontend SignalFeed
```

### 3.2 Backtest Akışı
```
Frontend StrategyPanel
    │  POST /api/backtest/run
    ▼
FastAPI → quant_engine.backtest.Engine
    │
    ├── OHLCVCache.get_window() → OHLCV bars
    ├── Strategy.evaluate() → signals
    ├── RiskManager → position sizing
    └── EquityTracker → equity_curve + trades
    │
    ▼
BacktestResult (JSON) → SQLite archive
    │
    ▼
Frontend: equity curve (Chart.js) + trade markers (lightweight-charts)
```

### 3.3 Mali Analiz Akışı
```
borsapy (finansal veri kaynağı)
    │
    ▼
MaliAnalizHarvester (Python threads, max_workers=4)
    │
    ▼
MySQL (finansal tablolar: bilanço, gelir, nakit)
    │
    ▼
MaliAnalizRepository (SQL sorguları)
    │
    ▼
GET /api/mali-analiz/{symbol}/*
    │
    ▼
Frontend MaliAnalizPanel (7 sekme + grafikler)
```

### 3.4 Haber Akışı
```
yfinance.Ticker(symbol).news
    │
    ├── Background Worker (30dk interval, BIST30[:15])
    └── On-demand (GET /api/news?fresh=true)
    │
    ▼
SQLite news.sqlite3 (WAL, unique URL)
    │
    ▼
GET /api/news → Frontend NewsPanel (kart + filtre + auto-refresh)
```

---

## 4. Durum Yönetimi (Frontend)

| Mekanizma | Kullanım |
|-----------|---------|
| `localStorage` | Tema, göstergeler, çizimler, şablonlar, sinyal geçmişi |
| `URL params` (?symbol=&tab=) | Deep-link — sayfa yenileme/paylaşım |
| `history.replaceState` | Tab değişiminde URL güncelleme (sayfa yenileme yok) |
| `CustomEvent` | Bileşenler arası iletişim (openSymbolOnChart, addSymbolToBacktest) |
| `WebSocket` | Canlı fiyat + sinyal akışı |

---

## 5. Tema Sistemi

CSS değişken tabanlı iki tema:

```css
/* Dark (varsayılan) */
:root { --bg: #07080a; --panel: #0e1118; --text: #8b93a3; --text-bold: #f4f6fa; }

/* Light */
html.light { --bg: #f4f6f8; --panel: #ffffff; --text: #536071; --text-bold: #111722; }
```

Tema değişimi: `window.dispatchEvent(new CustomEvent('piyasapilot:theme-change', {detail: {theme, accent}}))`

Dinleyiciler:
- `ChartPanel` → `applyThemeOptions()` — lightweight-charts `applyOptions()`
- `MaliAnalizPanel` → `loadTab()` (charts sekmesi yeniden yüklenir)
- `StrategyPanel` → `renderReport()` (performance/wf/mc sekmeleri yeniden çizilir)

---

## 6. Kritik Kısıtlamalar

| Kural | Açıklama |
|-------|---------|
| **Dokunma yasağı** | `quant_engine/backtest/engine.py`, `quant_engine/data/providers/`, `quant_engine/data/live_feed.py` |
| **Bellek güvenliği** | `node_modules`, `.git`, `dist`, `build`, `venv`, `__pycache__` okunmaz |
| **Commit onayı** | Her commit için açık kullanıcı onayı gereklidir |
| **Model seçimi** | Varsayılan: Sonnet. Opus yalnızca Enes istediğinde |

---

## 7. Docker Compose

```yaml
services:
  gateway:     # FastAPI — port 8000
  frontend:    # Nginx (prod build) — port 80
  redis:       # Cache + pub/sub
  clickhouse:  # Zaman serisi OHLCV
  mysql:       # Finansal tablolar
```

Geliştirme: `uvicorn backend.api.main:create_app --reload` + `npm run dev`
