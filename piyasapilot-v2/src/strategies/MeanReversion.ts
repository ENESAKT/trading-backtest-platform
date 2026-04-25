import type { OHLCV, IndicatorSet, Signal, BacktestResult } from '../types.js';
import { computeIndicators } from '../indicators/index.js';
import { runBacktest } from './TrendFollowing.js';

export const MeanReversionMeta = {
  id:      'mean',
  nameKey: 'STRATEGY_MEAN',
  descKey: 'STRATEGY_DESC_MEAN',
} as const;

/**
 * Entry long:  price touches BB lower AND RSI < 35
 * Entry short: price touches BB upper AND RSI > 65
 * Exit:        price returns to BB midline (SMA20)
 */
export function generateMeanSignals(candles: OHLCV[], inds: IndicatorSet): Signal[] {
  const signals: Signal[] = [];
  const n = candles.length;
  if (n < 22) return signals;

  const { bb, rsi } = inds;
  if (!bb || !rsi) return signals;

  for (let i = 1; i < n; i++) {
    const close  = candles[i]!.close;
    const upper  = bb.upper[i];
    const mid    = bb.mid[i];
    const lower  = bb.lower[i];
    const rs     = rsi[i];

    if (!upper || !mid || !lower || !rs) continue;
    if (isNaN(upper) || isNaN(mid) || isNaN(lower) || isNaN(rs)) continue;

    const nearLower = lower > 0 && close <= lower * 1.01;
    const nearUpper = upper > 0 && close >= upper * 0.99;

    if (nearLower && rs < 35) {
      signals.push({
        type: 'BUY',
        reason: `Alt BB bandına dokunuş | RSI aşırı satım (${rs.toFixed(1)})`,
        price: close,
        timestamp: candles[i]!.time,
        strength: Math.min(10, Math.round((35 - rs) / 2)),
      });
    } else if (nearUpper && rs > 65) {
      signals.push({
        type: 'SELL',
        reason: `Üst BB bandına dokunuş | RSI aşırı alım (${rs.toFixed(1)})`,
        price: close,
        timestamp: candles[i]!.time,
        strength: Math.min(10, Math.round((rs - 65) / 2)),
      });
    } else {
      // Exit: price returns to midline
      const prevClose = candles[i - 1]!.close;
      const crossedMid = (prevClose < mid && close >= mid) || (prevClose > mid && close <= mid);
      if (crossedMid) {
        signals.push({
          type: 'SELL',
          reason: `Fiyat orta banda döndü (SMA20: ${mid.toFixed(2)})`,
          price: close,
          timestamp: candles[i]!.time,
          strength: 3,
        });
      }
    }
  }

  return signals.slice(-20);
}

export function backtestMean(candles: OHLCV[]): BacktestResult {
  const inds = computeIndicators(candles);
  let inPosition = false;
  let posType: 'long' | 'short' = 'long';

  return runBacktest(candles, inds, (c, i, ind) => {
    const { bb, rsi } = ind;
    if (!bb || !rsi) return null;

    const close = c.close;
    const upper = bb.upper[i];
    const mid   = bb.mid[i];
    const lower = bb.lower[i];
    const rs    = rsi[i];

    if (!upper || !mid || !lower || !rs || isNaN(upper)) return null;

    if (!inPosition) {
      if (close <= lower * 1.01 && rs < 35) {
        inPosition = true;
        posType = 'long';
        return 'BUY';
      }
    } else {
      // Exit long when price returns to midline
      const prevClose = candles[i - 1]?.close ?? close;
      if (posType === 'long' && prevClose < mid && close >= mid) {
        inPosition = false;
        return 'SELL';
      }
      // Force exit on upper band touch
      if (close >= upper * 0.99 && rs > 65) {
        inPosition = false;
        return 'SELL';
      }
    }

    return null;
  });
}
