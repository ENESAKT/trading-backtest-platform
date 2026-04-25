import type { OHLCV, IndicatorSet } from '../types.js';
import { EMA } from './ema.js';
import { SMA } from './sma.js';
import { RSI } from './rsi.js';
import { MACD } from './macd.js';
import { BollingerBands } from './bollinger.js';
import { ATR } from './atr.js';
import { VWAP } from './vwap.js';
import { Stochastic } from './stochastic.js';

export { EMA, SMA, RSI, MACD, BollingerBands, ATR, VWAP, Stochastic };

/**
 * Compute the full indicator set for a candle array.
 * Skips computation if insufficient data.
 */
export function computeIndicators(candles: OHLCV[]): IndicatorSet {
  if (candles.length < 2) return {};

  const closes = candles.map(c => c.close);

  return {
    rsi:        RSI(closes, 14),
    macd:       MACD(closes, 12, 26, 9),
    bb:         BollingerBands(closes, 20, 2),
    ema9:       EMA(closes, 9),
    ema21:      EMA(closes, 21),
    ema50:      EMA(closes, 50),
    sma20:      SMA(closes, 20),
    atr:        ATR(candles, 14),
    vwap:       VWAP(candles),
    stochastic: Stochastic(candles, 14, 3),
  };
}

/**
 * Get the last valid (non-NaN) value from an array.
 */
export function lastValid(arr: number[] | undefined): number | null {
  if (!arr) return null;
  for (let i = arr.length - 1; i >= 0; i--) {
    if (!isNaN(arr[i]!)) return arr[i]!;
  }
  return null;
}
