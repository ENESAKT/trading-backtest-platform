# PiyasaPilot v2.0 — System Architecture

## Overview

PiyasaPilot v2.0 is a professional browser-based trading terminal built with vanilla TypeScript
and Vite. It delivers real-time and near-real-time market data for BIST, US equities, Crypto,
and FX/Commodity instruments with zero mock data policy.

---

## File & Folder Structure

```
piyasapilot-v2/
├── docs/
│   ├── ARCHITECTURE.md       ← This file
│   ├── INDICATORS.md         ← Indicator formulas & usage
│   ├── STRATEGIES.md         ← Strategy logic & backtest methodology
│   └── PORTFOLIO.md          ← Paper trading rules & localStorage schema
│
├── src/
│   ├── types.ts              ← All TypeScript interfaces & enums
│   ├── constants/
│   │   ├── tr.ts             ← Turkish UI string constants
│   │   └── symbols.ts        ← Market symbol master list (BIST/US/Crypto/FX)
│   │
│   ├── core/
│   │   ├── AnomalyFilter.ts  ← IQR + Z-Score hybrid spike cleaner
│   │   ├── WebSocketManager.ts ← Binance WS with exponential backoff
│   │   ├── PollingManager.ts ← Yahoo Finance REST polling with cache
│   │   ├── PortfolioEngine.ts ← Paper trading state & PnL engine
│   │   └── DataEngine.ts     ← Central coordinator / event hub
│   │
│   ├── indicators/
│   │   ├── ema.ts            ← Exponential Moving Average
│   │   ├── sma.ts            ← Simple Moving Average
│   │   ├── rsi.ts            ← Relative Strength Index
│   │   ├── macd.ts           ← MACD (line, signal, histogram)
│   │   ├── bollinger.ts      ← Bollinger Bands (upper, mid, lower)
│   │   ├── atr.ts            ← Average True Range
│   │   ├── vwap.ts           ← Volume Weighted Average Price
│   │   ├── stochastic.ts     ← Stochastic Oscillator (%K, %D)
│   │   └── index.ts          ← computeIndicators() aggregator
│   │
│   ├── strategies/
│   │   ├── TrendFollowing.ts ← EMA crossover + RSI momentum
│   │   ├── MeanReversion.ts  ← Bollinger Band bounce
│   │   ├── BreakoutDetector.ts ← ATR consolidation + volume breakout
│   │   └── index.ts          ← StrategyManager
│   │
│   ├── components/
│   │   ├── ChartPanel.ts     ← Lightweight Charts renderer + fullscreen
│   │   ├── Sidebar.ts        ← Collapsible market explorer + search
│   │   ├── PortfolioPanel.ts ← Paper trading UI + Chart.js pie
│   │   ├── StrategyPanel.ts  ← Strategy selector + signals + equity curve
│   │   └── Screener.ts       ← Multi-filter market screener table
│   │
│   └── app.ts                ← Entry point: tab routing + global init
│
├── index.html                ← Single HTML shell
├── style.css                 ← Global dark terminal stylesheet
├── package.json
├── tsconfig.json
├── vite.config.ts
├── README.md
└── CHANGELOG.md
```

---

## Data Flow Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────────┐
│                        EXTERNAL SOURCES                         │
│                                                                 │
│  Binance WSS                    Yahoo Finance REST              │
│  stream.binance.com             query1.finance.yahoo.com        │
│  /{symbol}@kline_{tf}           /v8/finance/chart/{symbol}      │
└────────────┬────────────────────────────┬───────────────────────┘
             │  WebSocket frames          │  JSON via corsproxy.io
             ▼                            ▼
┌────────────────────┐       ┌────────────────────────┐
│  WebSocketManager  │       │    PollingManager       │
│  • exp. backoff    │       │  • 15s/10s poll         │
│  • heartbeat 30s   │       │  • cache TTL = interval-3s│
│  • msg queue       │       │  • rate limit 2 req/s   │
└────────┬───────────┘       └────────────┬────────────┘
         │                               │
         └─────────────┬─────────────────┘
                       │ raw OHLCV[]
                       ▼
              ┌─────────────────┐
              │  AnomalyFilter  │
              │  IQR + Z-Score  │
              │  Winsorization  │
              └────────┬────────┘
                       │ clean OHLCV[]
                       ▼
              ┌─────────────────┐
              │   DataEngine    │  ← Central event hub (EventEmitter)
              │  activeSymbol   │
              │  activeTimeframe│
              │  priceCache     │
              └──┬──────────┬───┘
                 │          │
        ┌────────┘          └─────────────────────────┐
        │ dataUpdate event                            │ priceUpdate event
        ▼                                             ▼
┌───────────────┐   ┌──────────────┐   ┌─────────────────────┐
│  ChartPanel   │   │  Indicators  │   │   PortfolioEngine   │
│  LW Charts    │   │  Engine      │   │   updatePrices()    │
│  4 sub-charts │   │  computeAll()│   │   PnL recalc        │
└───────┬───────┘   └──────┬───────┘   └──────────┬──────────┘
        │                  │                       │
        │                  ▼                       ▼
        │         ┌────────────────┐    ┌──────────────────┐
        │         │  StrategyPanel │    │  PortfolioPanel  │
        │         │  signals, BT   │    │  positions, PnL  │
        │         └────────────────┘    └──────────────────┘
        │
        ▼
┌───────────────┐
│   Screener    │
│  (all cached  │
│   symbols)    │
└───────────────┘
```

---

## API Sources Matrix

| Asset Class | Symbol Example   | Data Source          | Method      | Update Rate | Notes                       |
|-------------|------------------|----------------------|-------------|-------------|-----------------------------|
| Crypto      | BTCUSDT          | Binance WebSocket    | WebSocket   | Real-time   | `@kline_{interval}` stream  |
| Crypto hist.| BTCUSDT          | Binance REST         | GET         | On-demand   | `/api/v3/klines`            |
| BIST Equity | THYAO.IS         | Yahoo Finance        | GET (proxy) | 15s poll    | `.IS` suffix required       |
| US Equity   | AAPL             | Yahoo Finance        | GET (proxy) | 15s poll    | Standard ticker             |
| FX          | USDTRY=X         | Yahoo Finance        | GET (proxy) | 15s poll    | `=X` suffix for currencies  |
| Commodity   | GC=F             | Yahoo Finance        | GET (proxy) | 15s poll    | `=F` suffix for futures     |

**CORS Proxy**: `https://corsproxy.io/?` prefixed to Yahoo Finance URLs (browser constraint).

**Binance WebSocket URL**: `wss://stream.binance.com:9443/ws/{symbol_lower}@kline_{interval}`

**Yahoo Finance Chart URL**:
```
https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}
  ?interval={yf_interval}
  &range={range}
  &includePrePost=false
  &events=div,splits
```

### Timeframe mapping

| UI Label | Internal | Yahoo Finance | Binance   | Range    |
|----------|----------|---------------|-----------|----------|
| 1D       | 1m       | 1m            | 1m        | 1d       |
| 5D       | 5m       | 5m            | 5m        | 5d       |
| 15D      | 15m      | 15m           | 15m       | 5d       |
| 30D      | 30m      | 30m           | 30m       | 1mo      |
| 1S       | 1h       | 60m           | 1h        | 1mo      |
| 4S       | 4h       | —             | 4h        | 3mo      |
| 1G       | 1d       | 1d            | 1d        | 1y       |
| 1H       | 1w       | 1wk           | 1w        | 5y       |

---

## Technology Decisions

| Concern          | Choice                  | Justification                                              |
|------------------|-------------------------|------------------------------------------------------------|
| Language         | TypeScript 5.x          | Type safety across 30+ module boundaries; IDE autocomplete |
| Build tool       | Vite 5.x                | Sub-second HMR, native ESM, zero config TS support         |
| Charts           | Lightweight Charts v4   | TradingView-grade performance; 60fps canvas rendering      |
| Portfolio charts | Chart.js v4             | Pie + line charts with minimal overhead                    |
| No framework     | Vanilla TS + DOM        | Zero virtual DOM overhead; direct chart lib integration    |
| State            | EventEmitter pattern    | Decoupled pub/sub; avoids prop-drilling across components  |
| Persistence      | localStorage            | Zero backend dependency for paper trading                  |
| Data format      | OHLCV (columnar struct) | Cache-efficient; direct feed into chart lib primitives     |
| CSS              | Vanilla CSS variables   | GitHub dark palette; no runtime CSS-in-JS overhead         |

---

## Caching & Rate Limiting Strategy

### PollingManager Cache
- Per-symbol, per-timeframe `Map<string, CacheEntry>`
- TTL = `pollInterval - 3s` (avoids stale reads between polls)
- On cache hit: return cached data immediately, skip HTTP request
- Cache key format: `"${symbol}:${timeframe}"`

### Rate Limiter
- Token bucket: max 2 tokens, refill 1 token/500ms
- Overflow requests queued (max 50 items); oldest dropped if full
- Applies globally across all symbols being polled

### WebSocket Reconnect Backoff
```
attempt 0: 1000ms
attempt 1: 2000ms
attempt 2: 4000ms
attempt 3: 8000ms
attempt 4+: 30000ms (cap)
```

### Message Queue (WebSocket offline buffer)
- Max 200 messages buffered during reconnect
- Flushed in FIFO order on reconnect
- Older messages purged if capacity exceeded
