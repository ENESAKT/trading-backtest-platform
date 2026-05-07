import type { OHLCV } from '../types.js';

/**
 * Average True Range (Wilder smoothing).
 * TR = max(H−L, |H−prevC|, |L−prevC|)
 */
export function ATR(candles: OHLCV[], period = 14): number[] {
  if (candles.length < period + 1) return new Array(candles.length).fill(NaN);

  const result = new Array<number>(candles.length).fill(NaN);

  // TR for each bar
  const tr: number[] = [NaN];
  for (let i = 1; i < candles.length; i++) {
    const c = candles[i]!;
    const prevClose = candles[i - 1]!.close;
    tr.push(Math.max(
      c.high - c.low,
      Math.abs(c.high - prevClose),
      Math.abs(c.low  - prevClose)
    ));
  }

  // Seed ATR = SMA of first `period` TRs (starting at index 1)
  let atr = 0;
  for (let i = 1; i <= period; i++) atr += tr[i]!;
  atr /= period;
  result[period] = atr;

  // Wilder smoothing
  for (let i = period + 1; i < candles.length; i++) {
    atr = (atr * (period - 1) + tr[i]!) / period;
    result[i] = atr;
  }

  return result;
}
