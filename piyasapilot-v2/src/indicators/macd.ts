import type { MACDResult } from '../types.js';
import { EMA } from './ema.js';

/**
 * MACD = EMA(fast) − EMA(slow)
 * Signal = EMA(MACD, signal)
 * Histogram = MACD − Signal
 */
export function MACD(
  closes: number[],
  fast = 12,
  slow = 26,
  signal = 9
): MACDResult {
  const emaFast = EMA(closes, fast);
  const emaSlow = EMA(closes, slow);

  const macdLine: number[] = closes.map((_, i) => {
    const f = emaFast[i];
    const s = emaSlow[i];
    return f !== undefined && s !== undefined && !isNaN(f) && !isNaN(s)
      ? f - s
      : NaN;
  });

  // Signal: EMA of the MACD line (skip NaN prefix)
  const validStart = macdLine.findIndex(v => !isNaN(v));
  const signalLine = new Array<number>(closes.length).fill(NaN);

  if (validStart >= 0) {
    const validMacd = macdLine.slice(validStart);
    const emaSignal = EMA(validMacd, signal);
    for (let i = 0; i < emaSignal.length; i++) {
      signalLine[validStart + i] = emaSignal[i]!;
    }
  }

  const histogram: number[] = macdLine.map((m, i) => {
    const s = signalLine[i]!;
    return isNaN(m) || isNaN(s) ? NaN : m - s;
  });

  return { macd: macdLine, signal: signalLine, histogram };
}
