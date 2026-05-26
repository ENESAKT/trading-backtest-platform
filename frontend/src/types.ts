// ─── Asset & Market Types ─────────────────────────────────────────────────────

export type AssetType = 'equity' | 'fx' | 'crypto' | 'commodity' | 'derivative';
export type Timeframe = '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d' | '1w';
export type ChartType = 'candlestick' | 'line' | 'bar';
export type ChartDataRenderReason = 'initial' | 'symbol' | 'timeframe' | 'append';
export type ChartDataStatus = 'idle' | 'loading' | 'ready' | 'empty' | 'error';
export type ConnectionStatus = 'live' | 'delayed' | 'offline';

export interface ChartViewOptions {
  reason?: ChartDataRenderReason;
  symbol?: string;
  currency?: string;
  timeframe?: Timeframe;
  preserveTimeRange?: boolean;
  status?: ChartDataStatus;
  message?: string;
}

// ─── OHLCV ────────────────────────────────────────────────────────────────────

export interface OHLCV {
  time: number;    // Unix timestamp in seconds
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// ─── Symbol Master ────────────────────────────────────────────────────────────

export interface SymbolInfo {
  symbol: string;        // Exchange symbol (e.g. THYAO.IS, BTCUSDT, USDTRY=X)
  name: string;          // Human-readable display name
  assetType: AssetType;
  group: string;         // e.g. 'BIST 30', 'Kripto', 'Döviz / Emtia'
  currency: string;      // e.g. 'TRY', 'USD', 'USDT'
}

// ─── Indicators ───────────────────────────────────────────────────────────────

export interface MACDResult {
  macd: number[];
  signal: number[];
  histogram: number[];
}

export interface BollingerResult {
  upper: number[];
  mid: number[];
  lower: number[];
}

export interface StochasticResult {
  k: number[];
  d: number[];
}

export interface IndicatorSet {
  rsi?: number[];
  macd?: MACDResult;
  bb?: BollingerResult;
  ema9?: number[];
  ema21?: number[];
  ema50?: number[];
  sma20?: number[];
  atr?: number[];
  vwap?: number[];
  stochastic?: StochasticResult;
  kairi?: number[];
  most?: number[];
  mostEma?: number[];
  bbWidth?: number[];
  gmma?: { [key: string]: Array<{ time: number; value: number }> };
}

// ─── Strategy & Signals ───────────────────────────────────────────────────────

export interface Signal {
  type: 'BUY' | 'SELL' | 'SHORT' | 'COVER' | 'HOLD';
  reason: string;
  price: number;
  timestamp: number;
  strength: number;   // 1–10
  quantity?: number;
  bar_index?: number;
  pnl?: number | null;
  equity?: number | null;
  open_position?: boolean;
  trade_role?: 'entry' | 'exit';
  trade_side?: 'LONG' | 'SHORT';
  entry_time?: number;
  exit_time?: number;
  entry_price?: number;
  exit_price?: number;
  net_pnl?: number;
  return_pct?: number;
  stop_price?: number;
  take_profit_price?: number;
  risk_reward?: number;
}

// Backend ``POST /api/backtest/run`` payload — Sprint 3.4'te frontend
// doğrudan API'den dönen JSON'u tüketir (eski TS-içi backtest sökündü).

export interface BacktestMetrics {
  initial_capital?: number;
  final_equity: number;
  net_pnl?: number;
  total_return_pct: number;
  annualized_return_pct?: number;
  max_drawdown_pct: number;
  total_trades: number;
  total_commission: number;
  total_slippage?: number;
  sharpe_ratio: number;
  win_rate: number;
  profit_factor?: number;
  best_trade?: number;
  worst_trade?: number;
  avg_win?: number;
  avg_loss?: number;
  benchmark_return_pct?: number;
  has_open_position: boolean;
}

export interface EquityPoint {
  time: number;            // unix saniye
  bar_index: number;
  cash: number;
  position_value: number;
  total_equity: number;
  drawdown: number;
  drawdown_pct?: number;
}

export interface BacktestTrade {
  symbol: string;
  side?: 'LONG' | 'SHORT';
  entry_type?: 'BUY' | 'SHORT';
  exit_type?: 'SELL' | 'COVER';
  entry_time: number;
  exit_time: number;
  entry_price: number;
  exit_price: number;
  quantity: number;
  net_pnl: number;
  return_pct: number;
  is_winner: boolean;
  commission?: number;
  slippage_cost?: number;
  entry_bar_index?: number;
  exit_bar_index?: number;
}

export interface QualityWarning {
  code: string;
  severity: "high" | "medium" | "low";
  message: string;
}

export interface WalkForwardWindowReport {
  window: {
    index: number;
    in_sample_start: number;
    in_sample_end: number;
    out_of_sample_start: number;
    out_of_sample_end: number;
  };
  selected_params: Record<string, unknown>;
  in_sample_score: number;
  out_of_sample_return_pct: number;
  walk_forward_efficiency: number;
  passed: boolean;
  warnings: string[];
}

export interface WalkForwardReport {
  windows: WalkForwardWindowReport[];
  total_oos_return_pct: number;
  walk_forward_efficiency: number;
  passed: boolean;
  warnings: string[];
}

export interface MonteCarloReport {
  median_final_equity: number;
  p05_final_equity: number;
  p95_final_equity: number;
  probability_of_loss: number;
  median_max_drawdown_pct: number;
  p95_max_drawdown_pct: number;
  sample_simulations?: number[][];
  warnings: string[];
}

export interface PortfolioLabSummary {
  metrics: {
    total_return_pct: number;
    max_drawdown_pct: number;
    profit_factor: number;
    sharpe_like: number;
    worst_period_pct: number;
    monthly_returns: Record<string, number>;
  };
  strategy_count: number;
  warnings: string[];
}

export interface PaperOperationSummary {
  mode: string;
  real_order_enabled: boolean;
  preflight: {
    checklist: Record<string, boolean>;
    ready_to_start: boolean;
    warnings: string[];
  };
  last_signal: Signal | null;
  warnings: string[];
}

export interface LifecycleRiskCard {
  type: string;
  severity: string;
  title: string;
  description: string;
}

export interface LifecycleSummary {
  state: string;
  next_step: string;
  risk_cards: LifecycleRiskCard[];
  postmortem_ready: boolean;
}

export interface StrategySpec {
  name?: string;
  note?: string;
  rules: {
    long_entry?: string;
    long_exit?: string;
    short_entry?: string;
    short_exit?: string;
  };
  risk?: {
    stop_loss_pct?: number;
    take_profit_pct?: number;
    trailing_stop_pct?: number;
    time_stop_bars?: number;
  };
}

export interface BacktestResult {
  run_id?: string;
  title?: string;
  generated_at?: string;
  symbol: string;
  interval: string;
  last_price?: number;
  strategy_id: string;
  strategy_name?: string;
  params: Record<string, unknown>;
  strategy_spec?: StrategySpec | null;
  capital: number;
  lookback_bars: number;
  source_mode?: string;
  date_range?: {
    start?: number | null;
    end?: number | null;
    start_iso?: string;
    end_iso?: string;
  };
  data_source?: {
    source?: string;
    provider_name?: string;
    is_real?: boolean;
    status?: string;
    data_coverage_pct?: number;
    bar_count?: number;
  };
  summary_text?: string;
  assumptions?: Record<string, unknown>;
  warnings?: QualityWarning[];
  quality_score?: number;
  walk_forward_report?: WalkForwardReport;
  monte_carlo_report?: MonteCarloReport;
  portfolio_lab_summary?: PortfolioLabSummary;
  paper_operation_summary?: PaperOperationSummary;
  lifecycle_summary?: LifecycleSummary;
  metrics: BacktestMetrics;
  equity_curve: EquityPoint[];
  trades: BacktestTrade[];
  signals: Signal[];
}

export interface StrategyBlueprint {
  id: string;
  label: string;
  description: string;
  default_params: Record<string, unknown>;
  schema: Array<{
    key: string;
    label: string;
    type: string;
    default: unknown;
    min?: number;
    max?: number;
    step?: number;
    help?: string;
  }>;
}

export interface StrategyPreset {
  id: string;
  label: string;
  category: string;
  expected_market: string;
  suggested_timeframes: string[];
  min_bars: number;
  suggested_stop_pct: number;
  suggested_take_profit_pct: number;
  repaint_risk: string;
  liquidity_need: string;
  description: string;
  strategy_spec?: StrategySpec;
}

// ─── Portfolio ────────────────────────────────────────────────────────────────

export interface Position {
  symbol: string;
  quantity: number;
  avgCost: number;
  currentPrice: number;
  pnl: number;
  pnlPct: number;
}

export interface Trade {
  id: string;
  type: 'BUY' | 'SELL';
  symbol: string;
  quantity: number;
  price: number;
  timestamp: number;
  total: number;
}

export interface Portfolio {
  balance: number;                      // initial balance
  cash: number;
  positions: Record<string, Position>;
  history: Trade[];
}

export interface PortfolioStats {
  totalValue: number;
  totalPnL: number;
  totalPnLPct: number;
  winRate: number;
  openPositions: number;
}

// ─── Screener ─────────────────────────────────────────────────────────────────

export interface ScreenerResult {
  symbol: string;
  name: string;
  price: number;
  changePct: number;
  rsi: number;
  emaSignal: 'Yükseliş' | 'Düşüş' | 'Nötr';
  bbPosition: 'Alt Band' | 'Üst Band' | 'Orta' | 'Normal';
  volumeAlert: boolean;
  alerts: string[];
  volumeAvg20d?: number;       // Son 20 günlük ortalama hacim
  distFrom52wHigh?: number;    // 52h zirvesine mesafe (%)
}

export type ScreenerFilter =
  | 'rsi_oversold'
  | 'rsi_overbought'
  | 'ema_bullish'
  | 'bb_lower'
  | 'high_volume';

// ─── Data Engine Events ───────────────────────────────────────────────────────

export interface DataUpdateEvent {
  symbol: string;
  candles: OHLCV[];
  status: ConnectionStatus;
  lastUpdate: number;
}

export interface PriceUpdateEvent {
  symbol: string;
  price: number;
  changePct: number;
  timestamp: number;
}

// ─── Cache ────────────────────────────────────────────────────────────────────

export interface CacheEntry {
  data: OHLCV[];
  timestamp: number;
  symbol: string;
  timeframe: Timeframe;
}

// ─── Anomaly Filter Config ────────────────────────────────────────────────────

export interface AnomalyConfig {
  maxReturn: number;      // max allowed single-bar return (0.05 = 5%)
  zThreshold: number;     // z-score threshold for flagging
  iqrMultiplier: number;  // IQR multiplier (default 3)
}

// ─── G8: Chart Template ───────────────────────────────────────────────────────

export interface ChartTemplate {
  name: string;
  chartType: ChartType;
  activeIndicators: string[];
  indicatorParams: Record<string, any>;
  scaleMode: 'linear' | 'log' | 'percent';
  showPreviousClose: boolean;
  showPnlOverlay: boolean;
  showRiskLines: boolean;
  showBistLimits: boolean;
  theme?: {
    bg: string;
    gridColor: string;
    textColor: string;
  };
}

// ─── G9: Chart Event Marker ───────────────────────────────────────────────────

export type ChartEventType = 'haber' | 'kap' | 'bilanco' | 'temettu' | 'sermaye';

export interface ChartEvent {
  id: string;
  type: ChartEventType;
  time: number;           // unix timestamp seconds
  title: string;
  summary: string;
  source: string;
  symbol: string;
}

// ─── G10: Advanced Drawing Tool Types ─────────────────────────────────────────

export type AdvancedDrawingTool = 'fibonacci' | 'fibonacci_ext' | 'regression' | 'renko';

// ─── Mali Analiz (Financial Analysis) ─────────────────────────────────────────

export interface FinancialRatio {
  name: string;
  value: number | null;
  format?: 'pct' | 'num' | 'currency';
}

export interface FinancialStatementRow {
  label: string;
  values: (number | null)[]; // One value per period
}

export interface FinancialStatement {
  title: string;
  rows: FinancialStatementRow[];
}

export interface SourceStatus {
  source: string;
  status: string;
  fetched_at: string | null;
  cache_hit: boolean;
  stale: boolean;
  error: string | null;
}

export interface MaliAnalizResponse {
  symbol: string;
  company_name: string | null;
  periods: string[]; // e.g. ["2023 Q1", "2023 Q2", "2023 Q3", "2023 Q4"]
  source_status: SourceStatus;
  financial_statements: FinancialStatement[]; // balance sheet, income statement
  ratios: FinancialRatio[];
  warnings: string[];
}

export interface FinancialUniverseItem {
  symbol: string;
  ticker: string;
  name: string;
}

export interface FinancialUniverseResponse {
  scope: string;
  symbols: FinancialUniverseItem[];
  source_status: {
    source: string;
    status: string;
  };
}

export interface ShowToastFunction {
  (message: string, type?: 'success' | 'error' | 'warn' | 'info'): void;
}

// ─── DataTruth Kontratı (Bölüm 18.2) ────────────────────────────────────────

export type DataSourceType =
  | 'licensed'
  | 'exchange_public'
  | 'broker'
  | 'cache'
  | 'imported_csv'
  | 'sample'
  | 'unknown';

export type DataQualityStatus = 'ok' | 'warning' | 'blocked' | 'unknown';

/**
 * Her veri yanıtına eklenen kalite ve soy ağacı (lineage) bilgisi.
 * Backend'deki DataTruth Pydantic modeliyle birebir eşleşir.
 */
export interface DataTruth {
  // Kimlik
  symbol:    string;
  market:    string;
  timeframe: string;

  // Kaynak
  provider:    string;
  source_type: DataSourceType;

  // Gerçeklik
  is_real:       boolean;
  is_live:       boolean;
  is_delayed:    boolean;
  delay_minutes: number;

  // Zaman
  fetched_at?:        string;
  first_bar_ts?:      string;
  last_bar_ts?:       string;
  last_provider_ts?:  string;
  staleness_seconds:  number;

  // Kalite
  quality_status:  DataQualityStatus;
  coverage_pct:    number;
  gap_count:       number;
  duplicate_count: number;
  outlier_count:   number;

  // Düzeltme
  adjusted_for_splits:    boolean;
  adjusted_for_dividends: boolean;

  // Türetme
  is_derived:        boolean;
  source_timeframe:  string;
  derivation_method: string;

  // Lisans / uyarı
  license_note: string;
  warnings:     string[];
}

export type NotificationType = 'success' | 'error' | 'warn' | 'info';

declare global {
  interface Window {
    showToast?: (message: string, type?: NotificationType) => void;
  }
}

// ─── Screener Kontratı (Bölüm 18.14) ─────────────────────────────────────────

export type ScreenerOperator = 'gt' | 'gte' | 'lt' | 'lte' | 'eq' | 'neq' | 'in' | 'not_in';

/** API v2 screener filtresi — eski ScreenerFilter (legacy preset tipi) ile karışmamalı */
export interface ScreenerFilterRule {
  field:    string;
  operator: ScreenerOperator;
  value:    unknown;
}

export interface ScreenerSort {
  field:     string;
  direction: 'asc' | 'desc';
}

export interface ScreenerRunRequest {
  market?:        string;
  universe?:      string[];
  filters?:       ScreenerFilterRule[];
  columns?:       string[];
  sort?:          ScreenerSort;
  limit?:         number;
  snapshot_time?: string;
}

export interface ScreenerRow {
  symbol:         string;
  name?:          string;
  market:         string;
  sector?:        string;
  last_price?:    number;
  change_pct_1d?: number;
  volume?:        number;
  market_cap?:    number;
  quality_badge:  string;
  columns:        Record<string, unknown>;
}

export interface ScreenerRunResponse {
  run_id:              string;
  created_at:          string;
  filters_hash:        string;
  data_snapshot_hash:  string;
  market:              string;
  total_count:         number;
  rows:                ScreenerRow[];
  data_truth?:         DataTruth;
  warnings:            string[];
}

// ─── Symbol Snapshot (Bölüm 18.14) ───────────────────────────────────────────

export type SessionStatus = 'open' | 'closed' | 'pre' | 'post' | 'unknown';

export interface SymbolSnapshot {
  symbol:           string;
  market:           string;
  name?:            string;
  sector?:          string;
  instrument_type?: string;

  last_price?:      number;
  prev_close?:      number;
  change_pct_1d?:   number;
  high_52w?:        number;
  low_52w?:         number;

  session_status:   SessionStatus;
  last_bar_ts?:     string;

  data_truth?:      DataTruth;

  pe_ratio?:        number;
  pb_ratio?:        number;
  market_cap?:      number;
  eps_ttm?:         number;
  dividend_yield?:  number;

  warnings:         string[];
}

// ─── Technical Summary (Bölüm 18.14) ─────────────────────────────────────────

export type TechnicalRating = 'strong_buy' | 'buy' | 'neutral' | 'sell' | 'strong_sell' | 'unknown';
export type MAType = 'ema' | 'sma' | 'wma' | 'vwma' | 'hull' | 'ichimoku';
export type MASignal = 'above' | 'below' | 'unknown';
export type PivotMethod = 'classic' | 'fibonacci' | 'camarilla' | 'woodie' | 'demark';

export interface OscillatorEntry {
  name:            string;
  value?:          number;
  signal:          'buy' | 'sell' | 'neutral' | 'unknown';
  threshold_low?:  number;
  threshold_high?: number;
  description:     string;
}

export interface MovingAverageEntry {
  name:          string;
  period:        number;
  ma_type:       MAType;
  value?:        number;
  signal:        MASignal;
  distance_pct?: number;
}

export interface PivotLevels {
  method: PivotMethod;
  period: string;
  r3?: number; r2?: number; r1?: number;
  pp?: number;
  s1?: number; s2?: number; s3?: number;
}

export interface TechnicalSummary {
  symbol:    string;
  market:    string;
  timeframe: string;

  overall_rating:        TechnicalRating;
  oscillator_rating:     TechnicalRating;
  moving_average_rating: TechnicalRating;

  oscillators:     OscillatorEntry[];
  moving_averages: MovingAverageEntry[];
  pivot_levels:    PivotLevels[];

  warmup_bars_used:    number;
  calculation_version: string;
  data_truth?:         DataTruth;
  calculated_at?:      string;

  warnings: string[];
}

// ─── Backtest Assumptions (Bölüm 18.14) ──────────────────────────────────────

export type CommissionModel = 'fixed_bps' | 'fixed_pct' | 'tiered' | 'zero';
export type SlippageModel =
  | 'fixed_bps' | 'fixed_tick' | 'spread' | 'atr'
  | 'volume_pct' | 'gap_open' | 'low_liquidity' | 'zero';
export type OrderExecutionTime = 'next_open' | 'close' | 'same_bar';

export interface BacktestAssumptions {
  data_source:         string;
  data_delay_minutes:  number;
  is_real_data:        boolean;

  commission_model:    CommissionModel;
  commission_value:    number;
  commission_note:     string;

  slippage_model:      SlippageModel;
  slippage_value:      number;
  slippage_note:       string;

  order_type:              'market' | 'limit' | 'close';
  execution_time:          OrderExecutionTime;

  corporate_action_adjusted: boolean;
  survivorship_bias_free:    boolean;
  liquidity_capacity_try?:   number;

  data_truth?: DataTruth;
  warnings:    string[];
}

// ─── Paper Trading (Bölüm 18.14) ─────────────────────────────────────────────

export type PaperOrderSide   = 'buy' | 'sell' | 'short' | 'cover';
export type PaperOrderType   = 'market' | 'limit' | 'stop';
export type PaperOrderStatus = 'pending' | 'filled' | 'cancelled' | 'rejected';

export interface PaperOrder {
  id:              number;
  strategy_id:     string;
  symbol:          string;
  side:            PaperOrderSide;
  order_type:      PaperOrderType;
  status:          PaperOrderStatus;
  quantity:        number;
  requested_price?: number;
  filled_price?:   number;
  created_at:      string;
  filled_at?:      string;
  reason:          string;
}

export interface PaperPosition {
  strategy_id:        string;
  symbol:             string;
  side:               'long' | 'short';
  quantity:           number;
  entry_price:        number;
  current_price?:     number;

  unrealized_pnl?:     number;
  unrealized_pnl_pct?: number;
  realized_pnl:        number;

  opened_at: string;
  trade_id:  number;
}

export interface PaperPortfolioSummary {
  strategy_id:     string;
  initial_capital: number;
  cash:            number;
  positions_value: number;
  total_equity:    number;
  unrealized_pnl:  number;
  realized_pnl:    number;
  daily_pnl:       number;
  daily_pnl_pct:   number;
  is_halted:       boolean;

  positions:   PaperPosition[];
  open_orders: PaperOrder[];

  as_of?: string;
}

// ─── Signal Evidence (Bölüm 18.14) ───────────────────────────────────────────

export type SignalType = 'BUY' | 'SELL' | 'SHORT' | 'COVER' | 'HOLD';

export interface SignalIndicatorSnapshot {
  name:   string;
  value?: number;
  signal: string;
  note:   string;
}

export interface SignalEvidence {
  signal_id:       string;
  strategy_id:     string;
  symbol:          string;
  market:          string;
  timeframe:       string;

  signal_type:     SignalType;
  strength:        number;
  price_at_signal: number;
  ts:              string;

  indicators:      SignalIndicatorSnapshot[];
  reason:          string;
  rule_triggered:  string;

  data_truth?: DataTruth;

  disclaimer: string;
  warnings:   string[];
}

// ─── CandleSeriesResponse (Bölüm 18.14) ──────────────────────────────────────

export interface CandleSeriesResponse {
  bars:       OHLCV[];
  data_truth: DataTruth;
  fetched_at: string;
}
