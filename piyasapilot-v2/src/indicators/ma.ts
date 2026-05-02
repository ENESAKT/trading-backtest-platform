import { EMA } from './ema';
import { BollingerBands } from './bollinger';

export function calculateBBWidth(data: any[], period: number = 20, multiplier: number = 2): any[] {
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

export function calculateGMMA(data: any[]): { 
  short_3: any[], short_5: any[], short_8: any[], short_10: any[], short_12: any[], short_15: any[],
  long_30: any[], long_35: any[], long_40: any[], long_45: any[], long_50: any[], long_60: any[] 
} {
  const short_periods = [3, 5, 8, 10, 12, 15];
  const long_periods = [30, 35, 40, 45, 50, 60];
  
  const closes = data.map(d => d.close);
  const result: any = {};
  
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
