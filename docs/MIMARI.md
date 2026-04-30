# PiyasaPilot Mimari Dokümanı

## Genel Bakış

PiyasaPilot, BIST 100, kripto, ABD piyasaları ve FX/emtia için gerçek zamanlı veri toplama, teknik analiz, otomatik backtest ve paper trading yapabilen bir algoritmik trading terminalidir.

## Katmanlar

### 1. Data Layer (Veri Katmanı)

```
İnternet (Binance WS/REST / yfinance REST / lisanslı HTTP feed / MCP)
    ↓
ProviderRouter + Worker'lar (backend/workers/)
    ↓ [IQR spike filter]
SQLite Cache (data/cache/ohlcv.sqlite3)
    ↓ [cache-aside pattern]
REST API (/api/v2/candles)
    ↓
Frontend (DataEngine → ChartPanel)
```

#### Worker Tipleri
- **BinanceWSWorker:** 10 kripto paritesi, kline_1m/15m stream, jitter'lı reconnect ve health metadata
- **YahooPoller:** ABD endeksleri + FX + emtia (60s interval, yfinance 60 req/dk limit)
- **BISTPoller:** BIST 30+100 hisseleri (.IS suffix, batch 5'er, 60s interval)
- **Configured HTTP Bridges:** `BIST_HTTP_URL_TEMPLATE` ve `VIOP_HTTP_URL_TEMPLATE` varsa lisanslı feed barları `is_real=true` olarak akar; yoksa sahte veri üretilmez.
- **MCP:** `borsa` ve `tradingview` sunucuları `.mcp.json` + `scripts/mcp_uvx.sh` ile bağlanır.

#### Cache-Aside Pattern
1. Frontend `/api/v2/candles?symbol=X&interval=15m` ister
2. API SQLite cache'e bakar → hit ise döndür
3. Miss ise → provider'dan çek → spike filter → cache'e yaz → döndür

### 2. Signal Layer (Sinyal Katmanı)

```
Worker on_bar hook
    ↓
SignalGenerator v2
    ├── Metadata kapısı (is_real=true, status ok/live)
    ├── 9 strateji çalıştır (thread pool)
    ├── Sinyal gücü hesapla (RSI + trend confluence)
    ├── Konsensüs kontrolü (5+ strateji → STRONG)
    └── Metadata ekle (RSI, trend, ATR, volatilite)
    ↓
SignalBus (pub/sub)
    ├── /ws/signals → Frontend (SignalFeed + toast)
    ├── PaperExecutor → SQLite trade kaydı
    └── Notifier → Telegram/Email/macOS
```

### 3. Backtest Layer

```
POST /api/backtest/run
    ↓
BacktestRunner
    ├── Cache'ten veri çek
    ├── Blueprint parametreleri doğrula
    └── BacktestEngine çalıştır (lookahead-free)
    ↓
Response: metrics + equity_curve + trades + signals
```

**8 Strateji:** SMA Crossover, RSI Reversion, Bollinger Reversion, Buy & Hold, Donchian Breakout, MACD Divergence, Supertrend, Mean Reversion VWAP

### 4. Paper Trading Layer

```
SignalBus → PaperExecutor
    ├── get_or_create_wallet(strategy_id)
    ├── Risk kontrolü (günlük %10 limit)
    ├── BUY: nakit × %10 → pozisyon
    └── SELL: pozisyon → PnL hesaplama → nakit
    ↓
PaperDB (SQLite)
    ├── paper_trades (tüm işlemler)
    ├── paper_portfolio (cüzdan durumu)
    └── paper_equity_curve (zaman serisi)
```

### 5. Frontend Layer

```
MultiChartLayout
    ├── Pane 1: ChartPanel (kendi sembol + WS bağlantısı)
    ├── Pane 2: ChartPanel
    ├── Pane 3: ChartPanel
    └── Pane 4: ChartPanel (2×2 modunda)
    ↓
Tab Navigation
    ├── Grafik (MultiChartLayout)
    ├── Portföy (PortfolioPanel v2)
    ├── Strateji (StrategyPanel)
    ├── Tarayıcı (Screener)
    └── Sinyaller (SignalFeed + toast)
```

## Veri Akış Diyagramı

```
           ┌─────────────┐
           │   Binance    │──── WS ────→ BinanceWSWorker
           └─────────────┘               │
                                         ├─ spike_filter()
           ┌─────────────┐               │
           │   yfinance   │──── REST ───→ YahooPoller / BISTPoller
           └─────────────┘               │
                                         ↓
                                   ┌───────────┐
                                   │ OHLCVCache │ (SQLite)
                                   └─────┬─────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              │                          │                          │
    /api/v2/candles              SignalGenerator              /api/paper/*
              │                          │                          │
              ↓                          ↓                          ↓
    ChartPanel (frontend)     SignalBus → /ws/signals     PortfolioPanel
                                         │
                              ┌──────────┼──────────┐
                              ↓          ↓          ↓
                        SignalFeed  PaperExecutor  Notifier
                        (toast)    (SQLite)       (Telegram)
```

## Güvenlik & Kısıtlamalar

- **Rate Limit:** yfinance 60 req/dk → batch 5'er, 60s interval
- **Zero-Demo:** Frontend doğrudan dış API'ye çıkmaz
- **Spike Filter:** IQR + hacim ağırlıklı Winsorize (silme yok)
- **Lookahead-free:** BacktestEngine gelecek veriye erişim engeller
- **Paper Trading:** Gerçek emir yok, sadece sanal işlem
- **Secret Safety:** Telegram/SMTP/LLM değerleri `.env` içinde kalır, endpoint/loglarda maskelenir
- **No Fake Data:** BIST/VİOP resmi feed yoksa sistem `no_data`/`not_configured` döndürür; sinyal üretmez

## Doğrulama Kapıları

| Kapı | Komut |
|------|-------|
| Python test | `make test` |
| TypeScript + build | `make lint` |
| Playwright E2E | `make e2e` |
| MCP bağlantısı | `make mcp-check` |
| Docker restart | `make docker-restart-check` |
| Stres smoke/live | `make stress-smoke` / `make stress-live` |
