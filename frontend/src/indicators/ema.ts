/**
 * Exponential Moving Average.
 * Seeded with SMA for the first `period` values.
 */
export function EMA(closes: number[], period: number): number[] {
  if (closes.length < period) return new Array(closes.length).fill(NaN);

  const k = 2 / (period + 1);
  const result = new Array<number>(closes.length).fill(NaN);

  // Seed: SMA of first `period` bars
  let seed = 0;
  for (let i = 0; i < period; i++) seed += closes[i]!;
  result[period - 1] = seed / period;

  for (let i = period; i < closes.length; i++) {
    result[i] = closes[i]! * k + result[i - 1]! * (1 - k);
  }

  return result;
}
