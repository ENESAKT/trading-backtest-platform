import type { OHLCV, IndicatorSet, Signal, BacktestResult, EquityPoint } from '../types.js';
import { computeIndicators, lastValid } from '../indicators/index.js';

const INITIAL_CASH = 10_000;

export const TrendFollowingMeta = {
  id:          'trend',
  nameKey:     'STRATEGY_TREND',
  descKey:     'STRATEGY_DESC_TREND',
} as const;

/**
 * Entry: EMA9 crosses above EMA21 AND RSI > 50 AND close > EMA50
 * Exit:  EMA9 crosses below EMA21 OR RSI < 45
 * Signal strength: distance of close from EMA50 (capped 1–10)
 */
export function generateTrendSignals(candles: OHLCV[], inds: IndicatorSet): Signal[] {
  const signals: Signal[] = [];
  const n = candles.length;
  if (n < 52) return signals;

  const { ema9, ema21, ema50, rsi } = inds;
  if (!ema9 || !ema21 || !ema50 || !rsi) return signals;

  for (let i = 1; i < n; i++) {
    const e9  = ema9[i],  e9p  = ema9[i - 1];
    const e21 = ema21[i], e21p = ema21[i - 1];
    const e50 = ema50[i];
    const rs  = rsi[i];
    const close = candles[i]!.close;

    if (!e9 || !e9p || !e21 || !e21p || !e50 || !rs) continue;
    if (isNaN(e9) || isNaN(e21) || isNaN(e50) || isNaN(rs)) continue;

    const crossedUp   = e9p <= e21p && e9 > e21;
    const crossedDown = e9p >= e21p && e9 < e21;

    if (crossedUp && rs > 50 && close > e50) {
      const distPct = ((close - e50) / e50) * 100;
      const strength = Math.min(10, Math.max(1, Math.round(distPct / 0.5)));
      signals.push({
        type: 'BUY',
        reason: `EMA9 EMA21'in üzerine çıktı | RSI: ${rs.toFixed(1)} | Fiyat EMA50 üzerinde`,
        price: close,
        timestamp: candles[i]!.time,
        strength,
      });
    } else if (crossedDown || rs < 45) {
      signals.push({
        type: 'SELL',
        reason: crossedDown
          ? `EMA9 EMA21'in altına indi`
          : `RSI zayıfladı (${rs.toFixed(1)} < 45)`,
        price: close,
        timestamp: candles[i]!.time,
        strength: 5,
      });
    }
  }

  // Return only last 20 signals
  return signals.slice(-20);
}

export function backtestTrend(candles: OHLCV[]): BacktestResult {
  const inds = computeIndicators(candles);
  return runBacktest(candles, inds, (c, i, ind) => {
    const e9 = ind.ema9, e21 = ind.ema21, e50 = ind.ema50, rs = ind.rsi;
    if (!e9 || !e21 || !e50 || !rs) return null;

    const e9v  = e9[i],  e9p  = e9[i - 1];
    const e21v = e21[i], e21p = e21[i - 1];
    const e50v = e50[i], rsv  = rs[i];
    if (!e9v || !e9p || !e21v || !e21p || !e50v || !rsv) return null;
    if (isNaN(e9v) || isNaN(e21v) || isNaN(e50v) || isNaN(rsv)) return null;

    const crossedUp   = e9p <= e21p && e9v > e21v;
    const crossedDown = e9p >= e21p && e9v < e21v;
    const close = c.close;

    if (crossedUp && rsv > 50 && close > e50v) return 'BUY';
    if (crossedDown || rsv < 45) return 'SELL';
    return null;
  });
}

// ─── Generic backtester ───────────────────────────────────────────────────────

type SignalFn = (
  c: OHLCV,
  i: number,
  inds: IndicatorSet
) => 'BUY' | 'SELL' | null;

export function runBacktest(
  candles: OHLCV[],
  inds: IndicatorSet,
  signalFn: SignalFn
): BacktestResult {
  let cash = INITIAL_CASH;
  let position = 0;
  let entryPrice = 0;
  const equity: EquityPoint[] = [];
  const tradePnLs: number[] = [];

  for (let i = 1; i < candles.length; i++) {
    const c = candles[i]!;
    const signal = signalFn(c, i, inds);

    if (signal === 'BUY' && position === 0 && cash > 0) {
      const qty  = cash / c.close;
      position   = qty;
      entryPrice = c.close;
      cash       = 0;
    } else if (signal === 'SELL' && position > 0) {
      const proceeds = position * c.close;
      const pnl      = proceeds - position * entryPrice;
      tradePnLs.push(pnl);
      cash     = proceeds;
      position = 0;
    }

    const totalValue = cash + position * c.close;
    equity.push({ time: c.time, value: totalValue });
  }

  // Close any open position at end
  if (position > 0 && candles.length > 0) {
    const last = candles[candles.length - 1]!;
    const proceeds = position * last.close;
    tradePnLs.push(proceeds - position * entryPrice);
    cash = proceeds;
  }

  const finalValue   = cash;
  const totalReturn  = ((finalValue - INITIAL_CASH) / INITIAL_CASH) * 100;
  const wins         = tradePnLs.filter(p => p > 0).length;
  const winRate      = tradePnLs.length > 0 ? (wins / tradePnLs.length) * 100 : 0;
  const grossProfit  = tradePnLs.filter(p => p > 0).reduce((a, b) => a + b, 0);
  const grossLoss    = Math.abs(tradePnLs.filter(p => p < 0).reduce((a, b) => a + b, 0));
  const profitFactor = grossLoss > 0 ? grossProfit / grossLoss : grossProfit > 0 ? 999 : 0;
  const maxDrawdown  = computeMaxDrawdown(equity.map(e => e.value));
  const sharpe       = computeSharpe(equity.map(e => e.value));

  return {
    totalReturn,
    sharpeRatio: sharpe,
    maxDrawdown,
    winRate,
    totalTrades: tradePnLs.length,
    profitFactor,
    equityCurve: equity,
  };
}

function computeMaxDrawdown(values: number[]): number {
  let peak = values[0] ?? 0;
  let maxDD = 0;
  for (const v of values) {
    if (v > peak) peak = v;
    const dd = peak > 0 ? ((peak - v) / peak) * 100 : 0;
    if (dd > maxDD) maxDD = dd;
  }
  return maxDD;
}

function computeSharpe(values: number[]): number {
  if (values.length < 2) return 0;
  const returns: number[] = [];
  for (let i = 1; i < values.length; i++) {
    const prev = values[i - 1]!;
    returns.push(prev !== 0 ? (values[i]! - prev) / prev : 0);
  }
  const mu  = returns.reduce((a, b) => a + b, 0) / returns.length;
  const sd  = Math.sqrt(returns.reduce((a, r) => a + (r - mu) ** 2, 0) / returns.length);
  return sd > 0 ? (mu / sd) * Math.sqrt(252) : 0;
}

// Exported so other strategies can reuse
export { computeMaxDrawdown, computeSharpe, lastValid };
