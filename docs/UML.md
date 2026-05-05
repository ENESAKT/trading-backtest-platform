# PiyasaPilot — UML Diyagramları

> Tarih: 2026-05-05 · Tüm diyagramlar Mermaid formatındadır.

---

## 1. Sistem Mimarisi (C4 — Component)

```mermaid
graph TB
    subgraph KULLANICI["Kullanıcı"]
        BROWSER["🌐 Tarayıcı"]
        TELEGRAM["📱 Telegram"]
    end

    subgraph FRONTEND["Frontend — TypeScript / Vite (port 5173)"]
        APP["app.ts\n(Tab Yönetici)"]
        CHART["ChartPanel\n(OHLCV Grafik)"]
        STRATEGY["StrategyPanel\n(Backtest Lab)"]
        PORTFOLIO["PortfolioPanel\n(Paper Trading)"]
        SCREENER["Screener\n(Tarayıcı)"]
        SIGNALFEED["SignalFeed\n(Sinyaller)"]
        EDUCATION["EgitimlerPanel\n(57 makale)"]
        FINANCIAL["MaliAnalizPanel\n(Finansal)"]
        MULTICHART["MultiChartLayout\n(Grid 1×1 / 2×2)"]
        DATAENGINE["DataEngine\n(REST Cache)"]
        QUOTESTREAM["QuoteStream\n(WS /ws/quotes)"]
    end

    subgraph NGINX["nginx (port 80/443)"]
        PROXY["Reverse Proxy\nTLS Termination"]
    end

    subgraph BACKEND["Backend — FastAPI / uvicorn (port 8000)"]
        MAIN["main.py\n(App Factory)"]
        APIKEY["APIKeyMiddleware\nX-API-Key"]
        CORS["CORSMiddleware"]

        subgraph BUS["Event Bus'lar"]
            QUOTEBUS["QuoteBus\n(/ws/quotes fan-out)"]
            SIGNALBUS["SignalBus\n(/ws/signals fan-out)"]
        end

        subgraph WORKERS["Veri İşçileri"]
            SUPERVISOR["WorkerSupervisor"]
            BINANCE["BinanceKlineWorker\n(WS — 10 kripto)"]
            YAHOO["YahooPoller\n(REST — 60s)"]
            BIST["BistStockPoller\n(REST — 60s)"]
        end

        subgraph SIGNALS["Sinyal Motoru"]
            SIGGEN["SignalGenerator\n(8 kural tipi)"]
            DECISION["DecisionEngine\n(Konsensüs)"]
        end

        subgraph DATA["Veri Katmanı"]
            CACHE["OHLCVCache\n(SQLite)"]
            HISTSTORE["HistoricalStore\n(Parquet)"]
            SPIKEFILTER["SpikeFilter\n(IQR + VWAP)"]
            CHREPO["ClickHouseRepository\n(⚠ bağlanmadı)"]
            MYSQLREPO["MySQLMetadataRepository\n(⚠ bağlanmadı)"]
            REDISCACHE["RedisMarketCache\n(⚠ bağlanmadı)"]
        end

        subgraph BACKTEST["Backtest Modülü"]
            RUNNER["BacktestRunner"]
            ARCHIVE["BacktestArchive\n(SQLite)"]
        end

        subgraph PAPER["Paper Trading"]
            EXECUTOR["PaperExecutor"]
            PAPERDB["PaperDB\n(SQLite)"]
        end

        subgraph NOTIFIER["Bildirim"]
            TELEGRAM_SVC["TelegramListener\n(11 komut)"]
            EMAIL["EmailNotifier\n(SMTP)"]
        end

        subgraph MALI["Mali Analiz"]
            MALISVC["FinancialAnalysisService\n(metadata-only)"]
            MALICACHE["FinancialAnalysisCache\n(SQLite)"]
        end
    end

    subgraph QUANTENGINE["quant_engine — Backtest Framework (Python)"]
        ENGINE["BacktestEngine\n(Lookahead-free)"]
        PORTFOLIO_QE["Portfolio\n(Position / Fill / Order)"]
        STRATEGIES["Strategy Implementations\n(9 strateji)"]
        PROVIDER_ROUTER["ProviderRouter"]
        LIVE_FEED["LiveDataService"]
        WFA["WalkForwardAnalysis"]
        MONTECARLO["MonteCarloReport"]
        OPTIMIZER["GridSearchOptimizer"]
        STRATSTORE["StrategyStore\n(SQLite)"]
    end

    subgraph DB["Veritabanları"]
        SQLITE["SQLite\n(aktif — cache)"]
        CLICKHOUSE["ClickHouse\n(hedef — OHLCV)"]
        MYSQL["MySQL\n(hedef — metadata)"]
        REDIS["Redis\n(hedef — cache/pubsub)"]
        PARQUET["Parquet\n(soğuk arşiv)"]
    end

    subgraph PROVIDERS["Harici Veri Sağlayıcıları"]
        BINANCE_EXT["Binance\nWebSocket + REST"]
        YFINANCE["yfinance\nBIST / FX / Emtia"]
        BORSAPY["borsapy\n(BIST)"]
    end

    BROWSER -- "HTTPS (REST+WS)" --> NGINX
    TELEGRAM -- "Bot API" --> TELEGRAM_SVC
    NGINX --> FRONTEND
    NGINX -- "/api/*" --> MAIN
    NGINX -- "/ws/*" --> MAIN

    APP --> CHART & STRATEGY & PORTFOLIO & SCREENER & SIGNALFEED & EDUCATION & FINANCIAL & MULTICHART
    CHART --> DATAENGINE
    STRATEGY --> DATAENGINE
    DATAENGINE --> QUOTESTREAM
    MULTICHART --> CHART

    MAIN --> APIKEY --> CORS
    MAIN --> BUS & WORKERS & SIGNALS & DATA & BACKTEST & PAPER & MALI
    SUPERVISOR --> BINANCE & YAHOO & BIST
    BINANCE --> QUOTEBUS
    YAHOO --> QUOTEBUS
    BIST --> QUOTEBUS
    SIGGEN --> DECISION --> SIGNALBUS

    RUNNER --> ENGINE
    ENGINE --> PORTFOLIO_QE
    ENGINE --> STRATEGIES
    WFA & OPTIMIZER & MONTECARLO --> ENGINE

    CACHE --> SQLITE
    HISTSTORE --> PARQUET
    ARCHIVE --> SQLITE
    PAPERDB --> SQLITE
    MALICACHE --> SQLITE
    CHREPO -.-> CLICKHOUSE
    MYSQLREPO -.-> MYSQL
    REDISCACHE -.-> REDIS

    BINANCE --> BINANCE_EXT
    YAHOO & BIST --> YFINANCE
    LIVE_FEED --> PROVIDER_ROUTER --> YFINANCE & BORSAPY & BINANCE_EXT
```

---

## 2. Backend Sınıf Diyagramı

```mermaid
classDiagram
    class FastAPI_App {
        +lifespan()
        +create_app() FastAPI
        +APIKeyMiddleware
        +CORSMiddleware
    }

    class QuoteBus {
        -_subs: list~_Subscription~
        +subscribe(symbol) AsyncGenerator
        +publish(symbol, data)
    }

    class SignalBus {
        -_subs: list~_Subscription~
        +subscribe() AsyncGenerator
        +publish(signal)
    }

    class WorkerSupervisor {
        -_workers: list~AsyncWorker~
        +start()
        +stop()
        +health() dict
    }

    class AsyncWorker {
        <<abstract>>
        +name: str
        +run()
        +stop()
    }

    class BinanceKlineWorker {
        -symbols: list~str~
        +run()
    }

    class YahooPoller {
        -symbols: list~str~
        -interval_s: int
        +run()
    }

    class BistStockPoller {
        +run()
    }

    class SignalGenerator {
        -config: SignalGeneratorConfig
        +generate(symbol, bars) list~Signal~
        +evaluate_rules() list
    }

    class SignalGeneratorConfig {
        +consensus_threshold: int
        +min_strength: int
        +signal_types: list~str~
    }

    class OHLCVCache {
        -db_path: Path
        +read(symbol, interval, start, end) list~Bar~
        +write(symbol, interval, bars)
        +stats() CacheStats
    }

    class HistoricalStore {
        -data_dir: Path
        +read(symbol, interval) DataFrame
    }

    class SpikeFilter {
        +filter_bars(bars, symbol) tuple
    }

    class MarketRepository {
        <<abstract>>
        +get_bars(symbol, interval, start, end)*
        +save_bars(symbol, interval, bars)*
    }

    class ClickHouseMarketRepository {
        -url: str
        +get_bars()
        +save_bars()
    }

    class LegacyFileMarketRepository {
        +get_bars()
        +save_bars()
    }

    class MySQLMetadataRepository {
        -url: str
        +connect()
        +list_instruments() list
        +get_inventory() dict
    }

    class RedisMarketCache {
        -url: str
        +get_quote(symbol) dict
        +set_quote(symbol, data, ttl)
    }

    class BacktestArchive {
        -db_path: Path
        +save(result) str
        +load(id) BacktestResult
        +list() list
    }

    class PaperExecutor {
        -db: PaperDB
        +execute(signal)
        +get_portfolio(strategy_id) dict
    }

    class PaperDB {
        -db_path: Path
        +create_wallet(strategy_id)
        +record_trade(wallet_id, trade)
        +get_equity(wallet_id) list
    }

    class APIKeyMiddleware {
        +EXEMPT_PATHS: frozenset
        +dispatch(request, call_next) Response
    }

    class FinancialAnalysisService {
        -provider: FinancialAnalysisProvider
        -cache: FinancialAnalysisCache
        +get_reports(symbol) FinancialAnalysisResponse
        +get_events(symbol) list
        +get_metric_history(symbol) list
    }

    class FinancialAnalysisProvider {
        <<Protocol>>
        +fetch_reports(symbol)*
        +fetch_events(symbol)*
    }

    class MockFinancialAnalysisProvider {
        +fetch_reports(symbol)
        +fetch_events(symbol)
    }

    WorkerSupervisor "1" *-- "many" AsyncWorker
    AsyncWorker <|-- BinanceKlineWorker
    AsyncWorker <|-- YahooPoller
    YahooPoller <|-- BistStockPoller

    MarketRepository <|-- ClickHouseMarketRepository
    MarketRepository <|-- LegacyFileMarketRepository

    FinancialAnalysisProvider <|.. MockFinancialAnalysisProvider
    FinancialAnalysisService --> FinancialAnalysisProvider

    PaperExecutor --> PaperDB
    SignalGenerator --> SignalGeneratorConfig

    FastAPI_App --> QuoteBus
    FastAPI_App --> SignalBus
    FastAPI_App --> WorkerSupervisor
    FastAPI_App --> SignalGenerator
    FastAPI_App --> OHLCVCache
    FastAPI_App --> HistoricalStore
    FastAPI_App --> BacktestArchive
    FastAPI_App --> PaperExecutor
    FastAPI_App --> FinancialAnalysisService
    FastAPI_App --> APIKeyMiddleware
```

---

## 3. quant_engine Sınıf Diyagramı

```mermaid
classDiagram
    class BacktestEngine {
        -config: BacktestConfig
        +run(symbol, bars, strategy) BacktestResult
        +_simulate()
    }

    class BacktestConfig {
        +initial_capital: float
        +commission_rate: float
        +slippage_bps: int
        +max_position_pct: float
    }

    class BacktestResult {
        +metrics: PerformanceMetrics
        +equity_curve: list~EquityPoint~
        +trades: list~CompletedTrade~
        +quality_warnings: list~QualityWarning~
        +wfa_report: WalkForwardReport
        +monte_carlo: MonteCarloReport
        +portfolio_lab: PortfolioLabSummary
        +lifecycle: LifecycleSummary
    }

    class Portfolio {
        +cash: float
        +positions: dict~str, Position~
        +equity_history: list~EquityPoint~
        +place_order(order) Fill
        +get_equity() float
    }

    class Position {
        +symbol: str
        +qty: float
        +avg_entry_price: float
        +unrealized_pnl() float
    }

    class Order {
        +symbol: str
        +side: OrderSide
        +qty: float
        +order_type: OrderType
        +signal_timestamp: datetime
    }

    class Fill {
        +order: Order
        +fill_price: float
        +fill_timestamp: datetime
        +commission: float
    }

    class CompletedTrade {
        +entry_fill: Fill
        +exit_fill: Fill
        +pnl: float
        +pnl_pct: float
    }

    class PerformanceMetrics {
        +total_return_pct: float
        +cagr: float
        +sharpe_ratio: float
        +sortino_ratio: float
        +max_drawdown_pct: float
        +win_rate: float
        +profit_factor: float
        +total_trades: int
    }

    class BaseStrategy {
        <<abstract>>
        +name: str
        +params: StrategyParams
        +generate_signals(data, bar_index, portfolio)*
        +as_signal_func() Callable
    }

    class SmaCrossover { +fast_period +slow_period }
    class RsiReversion { +rsi_period +oversold +overbought }
    class BollingerReversion { +period +std_dev }
    class BuyAndHold { }
    class DonchianBreakout { +period }
    class MacdDivergence { +fast +slow +signal }
    class Supertrend { +period +multiplier }
    class MeanReversionVwap { +threshold }
    class LightgbmProbability { +model_path }

    class StrategyRegistry {
        -_registry: dict~str, type~
        +register(name, cls)
        +get(name) type
        +list() list~str~
    }

    class StrategyStore {
        -db_path: Path
        +save(record) str
        +load(id) StrategyRecord
        +list() list~StrategyRecord~
    }

    class StrategyRecord {
        +id: str
        +name: str
        +blueprint_id: str
        +params: dict
        +spec: StrategySpec
        +paper_activation: PaperActivation
    }

    class StrategyPreset {
        +id: str
        +name: str
        +blueprint_id: str
        +default_params: dict
        +description: str
    }

    class WalkForwardAnalysis {
        -engine: BacktestEngine
        -config: WalkForwardConfig
        +run(symbol, bars, strategy) WalkForwardReport
    }

    class WalkForwardReport {
        +windows: list~WalkForwardWindowResult~
        +avg_oos_sharpe: float
        +stability_score: float
    }

    class GridSearchOptimizer {
        -engine: BacktestEngine
        +run(param_grid) OptimizationResult
    }

    class OptimizationResult {
        +best_params: dict
        +best_sharpe: float
        +heatmap: dict
        +stable_region: dict
    }

    class MonteCarloReport {
        +n_simulations: int
        +p05_return: float
        +p95_return: float
        +p05_max_dd: float
        +median_return: float
    }

    class BaseProvider {
        <<abstract>>
        +fetch_bars(request) FetchResult*
        +capabilities() ProviderCapabilities
    }

    class YFinanceProvider {
        +fetch_bars(request) FetchResult
    }

    class BinanceProvider {
        +fetch_bars(request) FetchResult
        +fetch_ws_kline(symbol)
    }

    class ProviderRouter {
        -providers: list~BaseProvider~
        +route(symbol, interval) BaseProvider
        +fetch(symbol, interval, start, end) DataFrame
    }

    class LiveDataService {
        -router: ProviderRouter
        +fetch_candles(symbol, interval, limit) list~Bar~
        +get_symbol_info(symbol) SymbolSpec
    }

    class DataValidator {
        +validate(df) ValidationResult
        +auto_fix(df) DataFrame
    }

    class ValidationResult {
        +score: int
        +errors: list~str~
        +warnings: list~str~
        +checks_passed: int
    }

    BacktestEngine --> BacktestConfig
    BacktestEngine --> Portfolio
    BacktestEngine --> BaseStrategy
    BacktestEngine --> DataValidator
    Portfolio "1" *-- "many" Position
    Portfolio --> Order
    Order --> Fill
    Fill --> CompletedTrade
    BacktestResult --> PerformanceMetrics
    BacktestResult --> WalkForwardReport
    BacktestResult --> MonteCarloReport

    BaseStrategy <|-- SmaCrossover
    BaseStrategy <|-- RsiReversion
    BaseStrategy <|-- BollingerReversion
    BaseStrategy <|-- BuyAndHold
    BaseStrategy <|-- DonchianBreakout
    BaseStrategy <|-- MacdDivergence
    BaseStrategy <|-- Supertrend
    BaseStrategy <|-- MeanReversionVwap
    BaseStrategy <|-- LightgbmProbability

    StrategyRegistry --> BaseStrategy
    StrategyStore --> StrategyRecord

    WalkForwardAnalysis --> BacktestEngine
    GridSearchOptimizer --> BacktestEngine

    BaseProvider <|-- YFinanceProvider
    BaseProvider <|-- BinanceProvider
    ProviderRouter "1" *-- "many" BaseProvider
    LiveDataService --> ProviderRouter
    DataValidator --> ValidationResult
```

---

## 4. Frontend Bileşen Diyagramı

```mermaid
classDiagram
    class App {
        -activeTab: AppTab
        -layout: LayoutMode
        +switchTab(tab)
        +handleKeyboard(e)
        +bootstrap()
    }

    class MultiChartLayout {
        -panes: ChartPane[]
        -layout: '1x1'|'1x2'|'2x1'|'2x2'
        -syncLocks: SyncState
        +setLayout(mode)
        +addPane()
        +syncRange(range)
    }

    class ChartPanel {
        -chart: IChartApi
        -series: ICandlestickSeriesApi
        -symbol: string
        -timeframe: Timeframe
        -indicators: IndicatorSet
        -drawings: Drawing[]
        +loadSymbol(symbol, tf)
        +addIndicator(type, params)
        +setScale(mode)
        +exportPng()
    }

    class DrawingManager {
        -drawings: DrawingObject[]
        +addTrendline(p1, p2)
        +addFibonacci(high, low)
        +addRegression(bars)
        +hitTest(x, y) Drawing
        +serialize() string
    }

    class StrategyPanel {
        -blueprint: StrategyBlueprint
        -result: BacktestResult
        -view: 'form'|'result'|'optimize'|'system'
        +runBacktest(req)
        +runOptimize(req)
        +showWFA()
        +showMonteCarlo()
        +showPortfolioLab()
        +exportPack()
        +importPack()
    }

    class PortfolioPanel {
        -wallets: PaperWallet[]
        -equityChart: Chart
        +loadPortfolio()
        +showEquityCurve(strategyId)
        +showMetrics()
    }

    class SignalFeed {
        -ws: WebSocket
        -signals: Signal[]
        +connect()
        +onSignal(s: Signal)
        +showToast(s)
        +filterBySymbol(sym)
    }

    class Screener {
        -results: ScreenerResult[]
        -filters: ScreenerFilter[]
        +scan(filters)
        +sortBy(col)
        +openInChart(symbol)
    }

    class Sidebar {
        -symbols: SymbolInfo[]
        -activeSymbol: string
        -activeTimeframe: Timeframe
        +search(query)
        +selectSymbol(sym)
        +lazyLoad()
    }

    class EgitimlerPanel {
        -articles: Article[]
        -activeCategory: string
        +search(query)
        +openArticle(id)
        +addIndicatorToChart(name)
        +openBacktestPreset(id)
    }

    class MaliAnalizPanel {
        -universe: SymbolInfo[]
        -activeSymbol: string
        -tab: 'reports'|'events'|'metrics'
        +loadUniverse()
        +selectSymbol(sym)
        +openInChart(sym)
    }

    class DataEngine {
        -cache: Map~string, OHLCV[]~
        -baseUrl: string
        +fetchCandles(symbol, tf, limit) OHLCV[]
        +getSymbolInfo(symbol) SymbolInfo
        +invalidate(symbol)
    }

    class QuoteStream {
        -ws: WebSocket
        -subscriptions: Map
        +subscribe(symbol, cb)
        +unsubscribe(symbol)
        +reconnect()
    }

    class HistoricalLoader {
        -dataEngine: DataEngine
        +loadInitial(symbol, tf) OHLCV[]
        +loadMore(symbol, tf, before) OHLCV[]
    }

    class AnomalyFilter {
        +filter(bars: OHLCV[]) OHLCV[]
        +detectSpike(bar, prev) boolean
    }

    class PortfolioEngine {
        +calcMetrics(trades) PortfolioStats
        +calcEquity(trades, capital) EquityPoint[]
    }

    App "1" *-- "1" MultiChartLayout
    App "1" *-- "1" Sidebar
    App "1" *-- "1" StrategyPanel
    App "1" *-- "1" PortfolioPanel
    App "1" *-- "1" SignalFeed
    App "1" *-- "1" Screener
    App "1" *-- "1" EgitimlerPanel
    App "1" *-- "1" MaliAnalizPanel

    MultiChartLayout "1" *-- "1..4" ChartPanel
    ChartPanel "1" *-- "1" DrawingManager
    ChartPanel --> DataEngine
    ChartPanel --> AnomalyFilter

    StrategyPanel --> DataEngine
    PortfolioPanel --> PortfolioEngine
    SignalFeed --> QuoteStream
    DataEngine --> HistoricalLoader
    DataEngine --> QuoteStream
```

---

## 5. Veri Akış Diyagramı

```mermaid
graph LR
    subgraph SOURCES["Harici Kaynaklar"]
        B["Binance\nWebSocket"]
        Y["yfinance\nREST"]
    end

    subgraph WORKERS["Workers (lifespan)"]
        BW["BinanceKlineWorker\n60s × 10 kripto"]
        YW["YahooPoller\n60s × FX/Emtia/Endeks"]
        BISTW["BistStockPoller\n60s × 98 BIST hisse"]
    end

    subgraph FILTER["Kalite Filtresi"]
        SF["SpikeFilter\n(IQR + hacim)"]
    end

    subgraph STORAGE["Depolama"]
        SQLITE["SQLite\nOHLCV cache"]
        PARQUET["Parquet\nSoğuk arşiv"]
        CH["ClickHouse\n(hedef)"]
    end

    subgraph API["FastAPI Endpoints"]
        V2["/api/v2/candles\n(cache-aside)"]
        WS_Q["/ws/quotes\n(fan-out)"]
        WS_S["/ws/signals\n(fan-out)"]
        BT["/api/backtest/run"]
        PAPER["/api/paper/*"]
    end

    subgraph ENGINE["Motorlar"]
        SIGGEN["SignalGenerator\n(8 kural tipi)"]
        BKTEST["BacktestEngine\n(lookahead-free)"]
        PE["PaperExecutor"]
    end

    subgraph FE["Frontend"]
        DC["DataEngine\n(REST cache)"]
        QS["QuoteStream\n(WS)"]
        CP["ChartPanel"]
        SP["StrategyPanel"]
        SIG["SignalFeed"]
        PP["PortfolioPanel"]
    end

    B --> BW --> SF --> SQLITE
    B --> BW --> SF --> QuoteBus["QuoteBus"]
    Y --> YW --> SF --> SQLITE
    Y --> YW --> SF --> QuoteBus
    Y --> BISTW --> SF --> SQLITE
    Y --> BISTW --> SF --> QuoteBus

    QuoteBus --> WS_Q
    SQLITE --> V2
    PARQUET -.->|fallback| V2
    CH -.->|hedef| V2

    SQLITE --> SIGGEN --> SignalBus["SignalBus"] --> WS_S
    SIGGEN --> PE --> PAPERDB["PaperDB\n(SQLite)"]

    V2 --> DC --> CP
    WS_Q --> QS --> CP
    WS_S --> SIG

    SP -->|POST| BT --> BKTEST --> SP
    PP -->|GET| PAPER --> PAPERDB --> PP
```

---

## 6. Altyapı ve Docker Diyagramı

```mermaid
graph TB
    subgraph INTERNET["İnternet"]
        USER["Kullanıcı\n(HTTPS:443)"]
        TELBOT["Telegram Bot API"]
    end

    subgraph DOCKER["Docker Compose — infra/docker-compose.prod.yml"]
        NGINX["nginx:alpine\nport 80/443\ndocker/nginx.conf"]

        subgraph APP["Uygulama Servisleri"]
            FRONTEND["frontend\n(node:20 → nginx:alpine)\ndocker/Dockerfile.frontend"]
            API["api\n(python:3.11-slim)\ndocker/Dockerfile.api\nport 8000"]
            WORKERS["workers\n(python:3.11-slim)\ndocker/Dockerfile.workers"]
            NOTIFIER["notifier\n(python:3.11-slim)\ndocker/Dockerfile.notifier"]
        end

        subgraph DATABASES["Veritabanları (internal network)"]
            CH_PROD["ClickHouse 24.3\nport expose:8123,9000\nvolume: clickhouse_data"]
            MYSQL_PROD["MySQL 8.0\nport expose:3306\nvolume: mysql_data"]
            REDIS_PROD["Redis 7\nport expose:6379\nvolume: redis_data"]
        end

        subgraph VOLUMES["Volumes"]
            VOL_CH["clickhouse_data"]
            VOL_MY["mysql_data"]
            VOL_RE["redis_data"]
            VOL_LOG["app_logs"]
        end
    end

    subgraph DEVDB["Geliştirme DB — infra/docker-compose.dev.yml"]
        CH_DEV["ClickHouse (dev)\nport 8123:8123"]
        MYSQL_DEV["MySQL (dev)\nport 3306:3306"]
        REDIS_DEV["Redis (dev)\nport 6379:6379"]
    end

    subgraph MONITOR["İzleme — infra/docker-compose.monitor.yml"]
        PROMETHEUS["Prometheus\nport 9090"]
        GRAFANA["Grafana\nport 3000"]
    end

    USER -->|HTTPS| NGINX
    NGINX -->|static| FRONTEND
    NGINX -->|/api/*| API
    NGINX -->|/ws/*| API
    TELBOT <-->|Bot API| NOTIFIER

    API -->|internal| CH_PROD & MYSQL_PROD & REDIS_PROD
    WORKERS -->|internal| CH_PROD & MYSQL_PROD & REDIS_PROD

    CH_PROD --- VOL_CH
    MYSQL_PROD --- VOL_MY
    REDIS_PROD --- VOL_RE
    API --- VOL_LOG

    API -->|/metrics| PROMETHEUS --> GRAFANA
```

---

## 7. Veritabanı Şema Diyagramı

```mermaid
erDiagram
    %% ── ClickHouse ──────────────────────────────────────
    MARKET_BARS {
        String symbol PK
        String timeframe PK
        DateTime timestamp PK
        Float64 open
        Float64 high
        Float64 low
        Float64 close
        Float64 volume
        String source
        UInt8 is_derived
        DateTime inserted_at
    }

    DATA_QUALITY_EVENTS {
        UUID id PK
        String symbol
        String timeframe
        DateTime bar_timestamp
        String event_type
        String description
        DateTime created_at
    }

    %% ── MySQL ───────────────────────────────────────────
    INSTRUMENTS {
        Int id PK
        String symbol UK
        String name
        String asset_class
        String market
        String provider_symbol
        Boolean is_active
        DateTime created_at
    }

    PROVIDERS {
        Int id PK
        String name UK
        String base_url
        Boolean is_active
        JSON capabilities
    }

    DATA_INVENTORY {
        Int id PK
        Int instrument_id FK
        String timeframe
        DateTime first_bar
        DateTime last_bar
        BigInt row_count
        Float miss_rate
        UInt8 is_derived
        DateTime updated_at
    }

    RETENTION_POLICY {
        Int id PK
        String market
        String asset_class
        String timeframe
        Int keep_days
    }

    %% ── SQLite (aktif) ──────────────────────────────────
    OHLCV_CACHE {
        TEXT symbol PK
        TEXT interval PK
        INTEGER ts PK
        REAL open
        REAL high
        REAL low
        REAL close
        REAL volume
    }

    PAPER_WALLETS {
        TEXT id PK
        TEXT strategy_id
        REAL initial_capital
        REAL cash
        REAL equity
        TEXT status
        DATETIME created_at
    }

    PAPER_TRADES {
        TEXT id PK
        TEXT wallet_id FK
        TEXT symbol
        TEXT side
        REAL qty
        REAL price
        REAL commission
        DATETIME fill_at
    }

    BACKTEST_RESULTS {
        TEXT id PK
        TEXT strategy_id
        TEXT symbol
        TEXT interval
        TEXT params_json
        TEXT metrics_json
        TEXT equity_json
        DATETIME created_at
    }

    STRATEGIES {
        TEXT id PK
        TEXT name
        TEXT blueprint_id
        TEXT params_json
        TEXT spec_json
        DATETIME created_at
    }

    INSTRUMENTS ||--o{ DATA_INVENTORY : "has"
    PAPER_WALLETS ||--o{ PAPER_TRADES : "contains"
    MARKET_BARS ||--o{ DATA_QUALITY_EVENTS : "generates"
```

---

## 8. AI Ekosistemi Diyagramı

```mermaid
graph TB
    subgraph CLAUDE_CODE["Claude Code Ekosistemi (.claude/)"]
        subgraph HOOKS["Hooks"]
            H1["SessionStart\ncheck-services.sh\n(gateway + plan durumu)"]
            H2["Stop\nauto-recap.sh\n(session-recap.md güncelle)"]
        end

        subgraph SKILLS["Skills — 20 adet (.claude/skills/)"]
            SK1["health-check\nrun-backtest\nbacktest-expert"]
            SK2["morning-briefing\nrisk-manager\nposition-sizer"]
            SK3["paper-trade-status\nsignal-postmortem\nscenario-analyzer"]
            SK4["data-inventory-check\ndata-retention-guardian\ndata-architecture-auditor"]
            SK5["repo-cleanup-auditor\nborfin-integration-auditor\nproduction-package-auditor"]
            SK6["deployment-readiness-check\ndeploy-stack\nsession-recap"]
        end

        subgraph AGENTS["Sub-Agents — 12 adet (.claude/agents/)"]
            AG1["backend-builder\nfrontend-builder\ndata-architect"]
            AG2["backtest-runner\nquant-researcher\ndata-validator"]
            AG3["devops-engineer\nrelease-janitor\ncode-reviewer"]
            AG4["robot-executor\ndata-platform-mentor\n(+ .agents/ duplikasyonu)"]
        end

        subgraph MCP["MCP Araçları (.mcp.json)"]
            MCP1["borsa-mcp\n(28 tool: BIST, KAP,\nEVDS, Kripto, FX)"]
            MCP2["tradingview-mcp\n(Screener, Teknik Analiz,\nBitcoin Pulse)"]
        end

        MEMORY[".claude/memory/\nsession-recap.md\nuser_*.md\nfeedback_*.md"]
    end

    subgraph CODEX["OpenAI/Codex Ekosistemi (.agents/)"]
        AG_ALT["backend-builder, quant-researcher\ndata-architect, devops-engineer\ndata-platform-mentor, vb."]
    end

    H1 --> MCP1
    H1 --> MCP2
    SK1 & SK2 --> MCP1
    SK3 & SK4 --> MCP2
    AGENTS --> SKILLS
    H2 --> MEMORY
```
