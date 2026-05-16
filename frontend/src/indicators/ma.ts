import { EMA } from './ema';
import { BollingerBands } from './bollinger';
import type { OHLCV } from '../types.js';
import type { IndicatorPoint } from './kairi.js';

export type GMMAResult = Record<string, IndicatorPoint[]>;

export function calculateBBWidth(data: OHLCV[], period: number = 20, multiplier: number = 2): IndicatorPoint[] {
  if (data.length < period) return [];
  
  const closes = data.map(d => d.close);
  const bb = BollingerBands(closes, period, multiplier);
  const results = [];
  
  for (let i = 0; i < data.length; i++) {
    const time = data[i].time;
    const mid = bb.mid[i];
    const upper = bb.upper[i];
    const lower = bb.lower[i];
    
    if (isNaN(mid) || isNaN(upper) || isNaN(lower) || mid === 0) {
      results.push({ time, value: NaN });
    } else {
      results.push({ time, value: (upper - lower) / mid });
    }
  }
  
  return results;
}

export function calculateGMMA(data: OHLCV[]): GMMAResult {
  const short_periods = [3, 5, 8, 10, 12, 15];
  const long_periods = [30, 35, 40, 45, 50, 60];
  
  const closes = data.map(d => d.close);
  const result: GMMAResult = {};
  
  const all_periods = [...short_periods, ...long_periods];
  for (const p of all_periods) {
    const prefix = short_periods.includes(p) ? 'short' : 'long';
    const emaArray = EMA(closes, p);
    
    const formatted = [];
    for (let i = 0; i < data.length; i++) {
      formatted.push({
        time: data[i].time,
        value: emaArray[i]
      });
    }
    
    result[`${prefix}_${p}`] = formatted;
  }
  
  return result;
}
