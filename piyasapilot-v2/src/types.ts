// ─── Asset & Market Types ─────────────────────────────────────────────────────

export type AssetType = 'equity' | 'fx' | 'crypto' | 'commodity' | 'derivative';
export type Timeframe = '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d' | '1w';
export type ChartType = 'candlestick' | 'line' | 'bar';
export type ConnectionStatus = 'live' | 'delayed' | 'offline';

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
}

// ─── Strategy & Signals ───────────────────────────────────────────────────────

export interface Signal {
  type: 'BUY' | 'SELL' | 'HOLD';
  reason: string;
  price: number;
  timestamp: number;
  strength: number;   // 1–10
}

// Backend ``POST /api/backtest/run`` payload — Sprint 3.4'te frontend
// doğrudan API'den dönen JSON'u tüketir (eski TS-içi backtest sökündü).

export interface BacktestMetrics {
  final_equity: number;
  total_return_pct: number;
  max_drawdown_pct: number;
  total_trades: number;
  total_commission: number;
  sharpe_ratio: number;
  win_rate: number;
  has_open_position: boolean;
}

export interface EquityPoint {
  time: number;            // unix saniye
  bar_index: number;
  cash: number;
  position_value: number;
  total_equity: number;
  drawdown: number;
}

export interface BacktestTrade {
  symbol: string;
  entry_time: number;
  exit_time: number;
  entry_price: number;
  exit_price: number;
  quantity: number;
  net_pnl: number;
  return_pct: number;
  is_winner: boolean;
}

export interface BacktestResult {
  symbol: string;
  interval: string;
  strategy_id: string;
  params: Record<string, unknown>;
  capital: number;
  lookback_bars: number;
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
    type: 'int' | 'float';
    default: number;
    min?: number;
    max?: number;
    step?: number;
    help?: string;
  }>;
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
