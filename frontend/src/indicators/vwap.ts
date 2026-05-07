import type { OHLCV } from '../types.js';

/**
 * Volume Weighted Average Price (session VWAP — resets on day change).
 * TypicalPrice = (H + L + C) / 3
 * VWAP = cumsum(TP × Volume) / cumsum(Volume)
 */
export function VWAP(candles: OHLCV[]): number[] {
  const result = new Array<number>(candles.length).fill(NaN);

  let cumTPV = 0;
  let cumVol = 0;
  let prevDay = -1;

  for (let i = 0; i < candles.length; i++) {
    const c = candles[i]!;
    const day = Math.floor(c.time / 86400);

    // Reset on new session (day change)
    if (day !== prevDay) {
      cumTPV = 0;
      cumVol = 0;
      prevDay = day;
    }

    const tp = (c.high + c.low + c.close) / 3;
    cumTPV += tp * c.volume;
    cumVol += c.volume;

    result[i] = cumVol > 0 ? cumTPV / cumVol : c.close;
  }

  return result;
}
