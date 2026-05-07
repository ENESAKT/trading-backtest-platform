/** Simple Moving Average. */
export function SMA(closes: number[], period: number): number[] {
  if (closes.length < period) return new Array(closes.length).fill(NaN);

  const result = new Array<number>(closes.length).fill(NaN);
  let windowSum = 0;

  for (let i = 0; i < closes.length; i++) {
    windowSum += closes[i]!;
    if (i >= period) windowSum -= closes[i - period]!;
    if (i >= period - 1) result[i] = windowSum / period;
  }

  return result;
}
