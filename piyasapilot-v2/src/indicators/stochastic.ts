import type { OHLCV, StochasticResult } from '../types.js';
import { SMA } from './sma.js';

/**
 * Stochastic Oscillator.
 * %K[i] = 100 × (C - Lowest Low[k]) / (Highest High[k] - Lowest Low[k])
 * %D    = SMA(%K, d)
 */
export function Stochastic(
  candles: OHLCV[],
  kPeriod = 14,
  dPeriod = 3
): StochasticResult {
  const k = new Array<number>(candles.length).fill(NaN);

  for (let i = kPeriod - 1; i < candles.length; i++) {
    const slice = candles.slice(i - kPeriod + 1, i + 1);
    const lowestLow  = Math.min(...slice.map(c => c.low));
    const highestHigh = Math.max(...slice.map(c => c.high));
    const range = highestHigh - lowestLow;

    k[i] = range === 0 ? 50 : 100 * (candles[i]!.close - lowestLow) / range;
  }

  const d = SMA(k.map(v => isNaN(v) ? 0 : v), dPeriod);
  // Restore NaN for indices where %K is NaN
  const dClean = d.map((v, i) => isNaN(k[i]!) ? NaN : v);

  return { k, d: dClean };
}
