import type { BollingerResult } from '../types.js';
import { SMA } from './sma.js';

/**
 * Bollinger Bands.
 * Mid  = SMA(period)
 * Upper = Mid + stdDev × multiplier
 * Lower = Mid − stdDev × multiplier
 */
export function BollingerBands(
  closes: number[],
  period = 20,
  stdDevMult = 2
): BollingerResult {
  const mid = SMA(closes, period);
  const upper = new Array<number>(closes.length).fill(NaN);
  const lower = new Array<number>(closes.length).fill(NaN);

  for (let i = period - 1; i < closes.length; i++) {
    const slice = closes.slice(i - period + 1, i + 1);
    const mean = mid[i]!;

    const variance = slice.reduce((acc, v) => acc + (v - mean) ** 2, 0) / period;
    const sd = Math.sqrt(variance);

    upper[i] = mean + stdDevMult * sd;
    lower[i] = mean - stdDevMult * sd;
  }

  return { upper, mid, lower };
}
