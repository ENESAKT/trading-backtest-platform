import type { OHLCV, IndicatorSet } from '../types.js';
import { EMA } from './ema.js';
import { SMA } from './sma.js';
import { RSI } from './rsi.js';
import { MACD } from './macd.js';
import { BollingerBands } from './bollinger.js';
import { ATR } from './atr.js';
import { VWAP } from './vwap.js';
import { Stochastic } from './stochastic.js';
import { calculateKairi } from './kairi.js';
import { calculateMOST } from './most.js';
import { calculateBBWidth, calculateGMMA, type GMMAResult } from './ma.js';

export { EMA, SMA, RSI, MACD, BollingerBands, ATR, VWAP, Stochastic, calculateKairi, calculateMOST, calculateBBWidth, calculateGMMA };

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
  kairiPeriod?: number;
  mostPeriod?: number;
  mostPercent?: number;
  gmma?: boolean;
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
  const kairiPeriod = options.kairiPeriod ?? 14;
  const mostPeriod = options.mostPeriod ?? 3;
  const mostPercent = options.mostPercent ?? 2.0;

  // We map the array of plain numbers mostly, but kairi/most need object format or mapped mapping.
  // The types say mostly number[] for basic ones but we format them.
  // Let's adapt kairi and others inside computeIndicators if needed, or pass them back raw.
  // Currently, `candles` has `close` field as well which is needed for most/kairi
  const kairiData = calculateKairi(candles, kairiPeriod);
  // Extact just the values to match the number[] signature if IndicatorSet uses number[]
  const kairiArray = kairiData.map((d) => d.value ?? NaN);

  const mostData = calculateMOST(candles, mostPeriod, mostPercent);
  const mostArray = mostData.most.map((d) => d.value ?? NaN);
  const mostEmaArray = mostData.ema.map((d) => d.value ?? NaN);

  const bbWidthData = calculateBBWidth(candles, bbPeriod, bbStdDev);
  const bbWidthArray = bbWidthData.map((d) => d.value ?? NaN);

  // GMMA requires an object returning multiple series.
  // We'll leave it out of standard IndicatorSet for now and let ChartPanel handle it manually if selected.
  // Although, if options.gmma is true, we should compute and attach it.
  
  let gmmaData: GMMAResult | undefined = undefined;
  if (options.gmma) {
    gmmaData = calculateGMMA(candles);
  }

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
    kairi:      kairiArray,
    most:       mostArray,
    mostEma:    mostEmaArray,
    bbWidth:    bbWidthArray,
    ...(gmmaData ? { gmma: gmmaData } : {})
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
