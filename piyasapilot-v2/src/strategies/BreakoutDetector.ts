import type { OHLCV, IndicatorSet, Signal, BacktestResult } from '../types.js';
import { computeIndicators } from '../indicators/index.js';
import { runBacktest } from './TrendFollowing.js';
import { SMA } from '../indicators/index.js';

export const BreakoutMeta = {
  id:      'breakout',
  nameKey: 'STRATEGY_BREAKOUT',
  descKey: 'STRATEGY_DESC_BREAKOUT',
} as const;

const CONSOLIDATION_PERIOD = 20;
const BREAKOUT_LOOKBACK    = 20;
const ATR_THRESHOLD        = 0.7;
const VOLUME_THRESHOLD     = 1.5;

/**
 * Consolidation: ATR < 20-period ATR average × 0.7
 * Entry: price breaks above N-day high with volume > 1.5× avg volume
 * Stop:  below breakout candle low
 */
export function generateBreakoutSignals(candles: OHLCV[], inds: IndicatorSet): Signal[] {
  const signals: Signal[] = [];
  const n = candles.length;
  if (n < BREAKOUT_LOOKBACK + CONSOLIDATION_PERIOD) return signals;

  const { atr } = inds;
  if (!atr) return signals;

  const volumes = candles.map(c => c.volume);
  const avgVol = SMA(volumes, CONSOLIDATION_PERIOD);

  const avgATR = SMA(atr.map(v => isNaN(v) ? 0 : v), CONSOLIDATION_PERIOD);

  for (let i = BREAKOUT_LOOKBACK; i < n; i++) {
    const c    = candles[i]!;
    const atrV = atr[i];
    const avgA = avgATR[i];
    const avgV = avgVol[i];

    if (!atrV || !avgA || !avgV || isNaN(atrV) || isNaN(avgA)) continue;

    // Consolidation check
    const isConsolidating = atrV < avgA * ATR_THRESHOLD;
    if (!isConsolidating) continue;

    // N-day high
    const lookback = candles.slice(i - BREAKOUT_LOOKBACK, i);
    const nDayHigh = Math.max(...lookback.map(c => c.high));

    // Breakout: close above N-day high + volume surge
    if (c.close > nDayHigh && c.volume > avgV * VOLUME_THRESHOLD) {
      const stopLoss = c.low;
      signals.push({
        type: 'BUY',
        reason: `${BREAKOUT_LOOKBACK}G yüksek kırıldı (${nDayHigh.toFixed(2)}) | Hacim: ${(c.volume / avgV).toFixed(1)}× ort. | Stop: ${stopLoss.toFixed(2)}`,
        price: c.close,
        timestamp: c.time,
        strength: Math.min(10, Math.round((c.volume / avgV - 1) * 3)),
      });
    }
  }

  return signals.slice(-20);
}

export function backtestBreakout(candles: OHLCV[]): BacktestResult {
  const inds = computeIndicators(candles);
  const volumes = candles.map(c => c.volume);
  const avgVol  = SMA(volumes, CONSOLIDATION_PERIOD);
  const avgATR  = SMA((inds.atr ?? []).map(v => isNaN(v) ? 0 : v), CONSOLIDATION_PERIOD);

  let stopLoss = 0;

  return runBacktest(candles, inds, (c, i, ind) => {
    const { atr } = ind;
    if (!atr || i < BREAKOUT_LOOKBACK) return null;

    const atrV = atr[i];
    const avgA = avgATR[i];
    const avgV = avgVol[i];

    if (!atrV || !avgA || !avgV || isNaN(atrV) || isNaN(avgA)) return null;

    const isConsolidating = atrV < avgA * ATR_THRESHOLD;

    if (isConsolidating) {
      const lookback = candles.slice(i - BREAKOUT_LOOKBACK, i);
      const nDayHigh = Math.max(...lookback.map(x => x.high));

      if (c.close > nDayHigh && c.volume > avgV * VOLUME_THRESHOLD) {
        stopLoss = c.low;
        return 'BUY';
      }
    }

    // Stop-loss exit
    if (stopLoss > 0 && c.close < stopLoss) {
      stopLoss = 0;
      return 'SELL';
    }

    return null;
  });
}
