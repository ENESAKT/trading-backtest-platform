# PiyasaPilot v2.0

Professional trading terminal for Turkish retail traders and investors. Real-time data for BIST, Crypto, US Equities, FX, and Commodities — **zero mock data policy**.

---

## Features

| Module | Description |
|---|---|
| **Live Charts** | TradingView Lightweight Charts with Candlestick / Line / Bar |
| **Multi-pane** | Volume, RSI, MACD below main chart — synchronized scroll/zoom |
| **Indicators** | EMA(9/21/50), SMA20, Bollinger Bands, ATR, VWAP, Stochastic |
| **Fullscreen** | Native `requestFullscreen` + CSS fallback, ESC and F key support |
| **Market Explorer** | Collapsible sidebar: BIST30, BIST100, US, Crypto, FX/Commodity |
| **Live Search** | Debounced fuzzy search across 135+ symbols |
| **Screener** | 5 filters (RSI oversold/overbought, EMA crossover, BB lower, high volume) |
| **Portfolio** | Paper trading with 100.000 ₺ virtual balance, real PnL tracking |
| **Strategies** | Trend Following, Mean Reversion, Breakout Detector |
| **Backtest** | Return, Sharpe, MaxDrawdown, WinRate, ProfitFactor + equity curve |
| **Anomaly Filter** | IQR + Z-Score spike detection with linear interpolation repair |
| **WebSocket** | Binance live kline stream with exponential backoff reconnect |
| **REST Polling** | Yahoo Finance via CORS proxy with rate limiting and caching |

---

## Prerequisites

- Node.js 18+ (for `fetch`, `AbortSignal.timeout`)
- Modern browser (Chrome 80+, Firefox 80+, Safari 14+)
- Internet connection (all data is fetched from external APIs)

---

## Installation & Run

```bash
# Navigate to the project directory
cd piyasapilot-v2

# Install dependencies
npm install

# Start development server (opens browser automatically)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The app will be available at `http://localhost:5173` (dev) or `http://localhost:4173` (preview).

---

## Configuration

### API Endpoints

| Service | URL | Notes |
|---|---|---|
| Binance WebSocket | `wss://stream.binance.com:9443/ws/` | Public, no auth required |
| Binance REST | `https://api.binance.com/api/v3/klines` | Public, no auth required |
| Yahoo Finance | `https://query1.finance.yahoo.com/v8/finance/chart/` | Via CORS proxy |
| CORS Proxy | `https://corsproxy.io/?` | Free proxy, rate limited |

### No environment variables required.

All API calls are made directly from the browser. No backend server is needed.

---

## Usage Guide

### Chart Tab
1. Click any symbol in the left sidebar to load it
2. Use timeframe buttons (1D → 1H) to switch intervals
3. Toggle indicators (BB, EMA, VWAP, RSI, MACD) with the control bar
4. Press **F** or click ⛶ for fullscreen
5. Crosshair shows OHLCV + indicator values in top-left overlay

### Portfolio Tab
1. Enter a symbol, select BUY/SELL, enter quantity and price
2. Leave price blank to use the current market price
3. Click **Uygula** to execute the paper trade
4. Click **Kapat** on any position row to close it at current price
5. Pie chart updates automatically to show allocation

### Strategy Tab
1. Select one of the 3 strategy cards
2. Backtest runs automatically on the currently loaded symbol's data
3. Signals show entry/exit points with reason text and strength indicator
4. Equity curve shows hypothetical portfolio value over time

### Screener Tab
1. Click filter buttons to activate filters (AND logic within each filter, OR across filters)
2. Click **Tara** to scan all cached symbols
3. Results show RSI, EMA signal, BB position, and volume alerts

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `1` | Go to Chart tab |
| `2` | Go to Portfolio tab |
| `3` | Go to Strategy tab |
| `4` | Go to Screener tab |
| `F` | Toggle fullscreen (Chart) |
| `ESC` | Exit fullscreen |

---

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full system design.

---

## Data Policy

> **Sıfır demo veri politikası**: Hiçbir ekranda demo, sahte ya da mock veri kullanılmaz.
> API veri vermezse grafik bekleme durumunda kalır, sahte veri göstermez.

---

## Tech Stack

- **TypeScript 5** — full type coverage
- **Vite 5** — build tool with ESM-native bundling
- **Lightweight Charts v4** — TradingView-grade canvas charts
- **Chart.js v4** — portfolio pie + equity curve
- **Vanilla DOM** — zero framework overhead
