# Changelog

All notable changes to PiyasaPilot are documented here.
Format: [Semantic Versioning](https://semver.org/).

---

## [2.0.0] — 2026-04-25

### Added

**Core Data Engine**
- `AnomalyFilter`: IQR + Z-Score hybrid spike detection with per-asset-type thresholds (FX 5%, Equity 8%, Crypto 15%); linear interpolation repair; zero-volume candle handling
- `WebSocketManager`: Binance `@kline_{interval}` stream; exponential backoff reconnect (1s→2s→4s→8s→30s cap); heartbeat ping every 30s; 200-message offline buffer queue
- `PollingManager`: Yahoo Finance REST via corsproxy.io; 15s (equity/FX) and 10s (crypto) polling; token-bucket rate limiter (2 req/s); per-symbol TTL cache; 3-attempt exponential retry; `live`/`delayed`/`offline` status reporting
- `DataEngine`: Central EventEmitter coordinator; routes crypto symbols to WebSocket path and others to REST polling; emits `dataUpdate`, `priceUpdate`, `statusChange` events; singleton export
- `PortfolioEngine`: Paper trading with 100.000 ₺ initial balance; `buy()`, `sell()`, `closePosition()`, `updatePrices()` operations; `getStats()` for total value, PnL, win rate; localStorage persistence; `getAllocation()` for pie chart

**Technical Indicators** (all pure functions, typed, NaN-safe)
- `EMA(closes, period)` — exponential moving average, SMA-seeded
- `SMA(closes, period)` — sliding window simple moving average
- `RSI(closes, period=14)` — Wilder smoothing
- `MACD(closes, fast=12, slow=26, signal=9)` — line, signal, histogram
- `BollingerBands(closes, period=20, stdDev=2)` — upper, mid, lower
- `ATR(candles, period=14)` — Wilder smoothing, true range
- `VWAP(candles)` — session VWAP with daily reset
- `Stochastic(candles, k=14, d=3)` — %K and %D
- `computeIndicators(candles)` — full IndicatorSet in one call

**Chart Panel** (Lightweight Charts v4)
- Candlestick / Line / Bar switching at runtime
- Overlay indicators on main chart: BB bands (dashed), EMA9/21/50 lines, VWAP
- Synchronized sub-charts: Volume (color-coded), RSI, MACD histogram+lines
- Crosshair overlay: OHLCV + RSI + MACD + EMA9/21 values
- Fullscreen: native `requestFullscreen()` + CSS `position:fixed` fallback; F key and ESC key
- Responsive resize with ResizeObserver (debounced 150ms)
- Timeframe buttons: 1D, 5D, 15D, 30D, 1S, 4S, 1G, 1H
- Per-indicator visibility toggles (BB, EMA, VWAP, RSI, MACD)

**Sidebar Market Explorer**
- 135+ symbols across BIST30, BIST100, ABD, Kripto, Döviz/Emtia
- Collapsible accordion groups per market category
- Live price ticker + % change (color-coded green/red) per symbol
- Debounced 300ms fuzzy search on symbol + name
- `localStorage` persistence of last selected symbol

**Portfolio Panel**
- Summary cards: Total Value, Total PnL, Cash, Open Positions
- Positions table with per-row Close button at current price
- Trade form with symbol autocomplete (datalist), BUY/SELL toggle, market price autofill
- Trade history table (last 50 trades)
- Doughnut allocation chart (Chart.js) — updates live

**Strategy Engine**
- `TrendFollowing`: EMA9 × EMA21 crossover + RSI > 50 + close > EMA50 entry; EMA cross down or RSI < 45 exit; strength score 1–10
- `MeanReversion`: BB lower touch + RSI < 35 long entry; BB upper touch + RSI > 65 signal; midline return exit
- `BreakoutDetector`: ATR consolidation detection (< 0.7× 20-period average); N-day high breakout with volume > 1.5× average; stop-loss at breakout candle low
- Generic `runBacktest()` engine: total return %, Sharpe ratio, max drawdown %, win rate %, total trades, profit factor, equity curve

**Strategy Panel**
- 3 strategy selector cards (Trend, Mean Reversion, Breakout)
- Backtest metrics grid (6 KPIs)
- Live signals list with strength bar, reason text, price, timestamp
- Equity curve (Chart.js line chart, sampled to max 200 points)

**Screener**
- 5 filter buttons: RSI Oversold, RSI Overbought, EMA Bullish, BB Lower, High Volume
- Scans all cached symbols; displays RSI, EMA signal, BB position, volume alert columns
- Alert tags per row

**UI / UX**
- GitHub dark palette (`#0d1117` base)
- JetBrains Mono for data, Syne for headings
- Fixed 40px topbar with tab navigation (keyboard shortcuts 1–4)
- 220px collapsible sidebar
- Status badge: CANLI / GECİKMELİ / BAĞLANTI YOK / BAĞLANIYOR
- Last-update counter: green < 30s, yellow 30–60s, red > 60s
- All UI text in Turkish (`src/constants/tr.ts`)
- Turkish number formatting (. thousands, , decimal)
- Turkish date/time (DD.MM.YYYY HH:mm)
- Custom scrollbar styling
- CSS transitions, no page reloads

### Breaking Changes (from v1)
- Complete rewrite in TypeScript (v1 was plain HTML + inline JS)
- Requires Node.js 18+ and npm for build
- No Python backend dependency (fully browser-side)
- `workspace.json` format from v1 is not compatible

---

## [1.x] — Legacy

Previous versions used a Python/Streamlit backend. See `quant_engine/` directory for legacy code.
