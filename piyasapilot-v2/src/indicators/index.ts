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

export interface IndicatorCalculationOptions {
  rsiPeriod?: number;
  macdFastPeriod?: number;
  macdSlowPeriod?: number;
  macdSignalPeriod?: number;
  bbPeriod?: number;
  bbStdDev?: number;
  emaFastPeriod?: number;
  emaMidPeriod?: number;
  emaSlowPeriod?: number;
  atrPeriod?: number;
  stochasticKPeriod?: number;
  stochasticDPeriod?: number;
}

/**
 * Compute the full indicator set for a candle array.
 * Skips computation if insufficient data.
 */
export function computeIndicators(
  candles: OHLCV[],
  options: IndicatorCalculationOptions = {},
): IndicatorSet {
  if (candles.length < 2) return {};

  const closes = candles.map(c => c.close);
  const rsiPeriod = options.rsiPeriod ?? 14;
  const macdFastPeriod = options.macdFastPeriod ?? 12;
  const macdSlowPeriod = options.macdSlowPeriod ?? 26;
  const macdSignalPeriod = options.macdSignalPeriod ?? 9;
  const bbPeriod = options.bbPeriod ?? 20;
  const bbStdDev = options.bbStdDev ?? 2;
  const emaFastPeriod = options.emaFastPeriod ?? 9;
  const emaMidPeriod = options.emaMidPeriod ?? 21;
  const emaSlowPeriod = options.emaSlowPeriod ?? 50;
  const atrPeriod = options.atrPeriod ?? 14;
  const stochasticKPeriod = options.stochasticKPeriod ?? 14;
  const stochasticDPeriod = options.stochasticDPeriod ?? 3;

  return {
    rsi:        RSI(closes, rsiPeriod),
    macd:       MACD(closes, macdFastPeriod, macdSlowPeriod, macdSignalPeriod),
    bb:         BollingerBands(closes, bbPeriod, bbStdDev),
    ema9:       EMA(closes, emaFastPeriod),
    ema21:      EMA(closes, emaMidPeriod),
    ema50:      EMA(closes, emaSlowPeriod),
    sma20:      SMA(closes, 20),
    atr:        ATR(candles, atrPeriod),
    vwap:       VWAP(candles),
    stochastic: Stochastic(candles, stochasticKPeriod, stochasticDPeriod),
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
