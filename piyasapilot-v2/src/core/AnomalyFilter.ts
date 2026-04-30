import type { OHLCV, AssetType, AnomalyConfig } from '../types.js';

// ─── Per-asset anomaly configuration ─────────────────────────────────────────

const ASSET_CONFIG: Record<AssetType, AnomalyConfig> = {
  fx:        { maxReturn: 0.05,  zThreshold: 3.5, iqrMultiplier: 3 },
  equity:    { maxReturn: 0.08,  zThreshold: 3.5, iqrMultiplier: 3 },
  crypto:    { maxReturn: 0.15,  zThreshold: 4.0, iqrMultiplier: 3 },
  commodity: { maxReturn: 0.08,  zThreshold: 3.5, iqrMultiplier: 3 },
  derivative:{ maxReturn: 0.10,  zThreshold: 3.5, iqrMultiplier: 3 },
};

// ─── Statistical helpers ──────────────────────────────────────────────────────

function percentile(sorted: number[], p: number): number {
  const idx = (p / 100) * (sorted.length - 1);
  const lo = Math.floor(idx);
  const hi = Math.ceil(idx);
  if (lo === hi) return sorted[lo]!;
  return sorted[lo]! + (sorted[hi]! - sorted[lo]!) * (idx - lo);
}

function mean(arr: number[]): number {
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}

function stdDev(arr: number[], mu: number): number {
  const variance = arr.reduce((acc, v) => acc + (v - mu) ** 2, 0) / arr.length;
  return Math.sqrt(variance);
}

function linearInterpolate(prev: number, next: number, ratio: number): number {
  return prev + (next - prev) * ratio;
}

// ─── Return series computation ────────────────────────────────────────────────

function computeReturns(candles: OHLCV[]): number[] {
  const returns: number[] = [0]; // first bar return = 0
  for (let i = 1; i < candles.length; i++) {
    const prev = candles[i - 1]!.close;
    const curr = candles[i]!.close;
    returns.push(prev === 0 ? 0 : curr / prev - 1);
  }
  return returns;
}

// ─── Anomaly detection flags ──────────────────────────────────────────────────

function detectAnomalies(
  returns: number[],
  candles: OHLCV[],
  cfg: AnomalyConfig
): boolean[] {
  const flags = new Array<boolean>(returns.length).fill(false);

  // IQR filter on non-zero returns
  const nonZero = returns.filter(r => r !== 0);
  if (nonZero.length < 4) return flags;

  const sorted = [...nonZero].sort((a, b) => a - b);
  const q1 = percentile(sorted, 25);
  const q3 = percentile(sorted, 75);
  const iqr = q3 - q1;
  const lowerFence = q1 - cfg.iqrMultiplier * iqr;
  const upperFence = q3 + cfg.iqrMultiplier * iqr;

  // Z-score filter
  const mu = mean(nonZero);
  const sd = stdDev(nonZero, mu);

  for (let i = 1; i < returns.length; i++) {
    const r = returns[i]!;
    const absR = Math.abs(r);

    // Hard cap: single-bar return exceeds asset-type maximum
    if (absR > cfg.maxReturn) {
      flags[i] = true;
      continue;
    }

    // IQR fence check
    if (r < lowerFence || r > upperFence) {
      flags[i] = true;
      continue;
    }

    // Z-score check (cross-confirm with IQR to avoid false positives on thin markets)
    if (sd > 0) {
      const z = Math.abs((r - mu) / sd);
      if (z > cfg.zThreshold) {
        flags[i] = true;
        continue;
      }
    }

    // Zero-volume candle: suspect data quality, winsorize to neighbor
    if (candles[i]!.volume === 0 && i > 0 && i < candles.length - 1) {
      const prevVol = candles[i - 1]!.volume;
      const nextVol = candles[i + 1]?.volume ?? 0;
      if (prevVol > 0 && nextVol > 0 && absR > 0.001) {
        flags[i] = true;
      }
    }
  }

  return flags;
}

// ─── Winsorization via linear interpolation ───────────────────────────────────

function repairCandle(
  candles: OHLCV[],
  idx: number
): OHLCV {
  const prev = candles[idx - 1];
  const next = candles[idx + 1];
  const current = candles[idx]!;

  if (!prev && !next) return current;

  if (!prev && next) {
    return { ...current, open: next.open, high: next.high, low: next.low, close: next.close };
  }

  if (!next && prev) {
    return { ...current, open: prev.open, high: prev.high, low: prev.low, close: prev.close };
  }

  // Linear interpolation between prev and next (midpoint repair)
  const ratio = 0.5;
  return {
    time:   current.time,
    open:   linearInterpolate(prev!.close, next!.open, ratio),
    high:   linearInterpolate(prev!.high,  next!.high,  ratio),
    low:    linearInterpolate(prev!.low,   next!.low,   ratio),
    close:  linearInterpolate(prev!.close, next!.close, ratio),
    volume: linearInterpolate(prev!.volume, next!.volume, ratio),
  };
}

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Cleans raw OHLCV data by detecting price spikes via IQR + Z-Score hybrid
 * and repairing flagged candles via linear interpolation.
 */
export function filterAnomalies(candles: OHLCV[], assetType: AssetType): OHLCV[] {
  if (candles.length < 5) return candles;

  const cfg = ASSET_CONFIG[assetType];
  const returns = computeReturns(candles);
  const flags = detectAnomalies(returns, candles, cfg);

  const result: OHLCV[] = [...candles];

  for (let i = 0; i < flags.length; i++) {
    if (flags[i]) {
      result[i] = repairCandle(result, i);
    }
  }

  return result;
}

/**
 * Returns the count of anomalous candles found in a dataset (for diagnostics).
 */
export function countAnomalies(candles: OHLCV[], assetType: AssetType): number {
  if (candles.length < 5) return 0;
  const cfg = ASSET_CONFIG[assetType];
  const returns = computeReturns(candles);
  const flags = detectAnomalies(returns, candles, cfg);
  return flags.filter(Boolean).length;
}
