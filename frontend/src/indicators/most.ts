import { EMA } from './ema';
import type { OHLCV } from '../types.js';
import type { IndicatorPoint } from './kairi.js';

export function calculateMOST(data: OHLCV[], period: number = 3, percent: number = 2.0): { most: IndicatorPoint[], ema: IndicatorPoint[] } {
  if (data.length < period) return { most: [], ema: [] };
  
  const closes = data.map((d) => d.close);
  const emaArray = EMA(closes, period);
  const mostResults: IndicatorPoint[] = [];
  const emaResults: IndicatorPoint[] = [];
  const pct = percent / 100.0;
  
  let trend = 1;
  let prevMost = 0;
  
  for (let i = 0; i < data.length; i++) {
    const time = data[i].time;
    const currEma = emaArray[i];

    if (isNaN(currEma)) {
      mostResults.push({ time, value: NaN });
      emaResults.push({ time, value: NaN });
      continue;
    }
    
    // Format EMA result
    emaResults.push({ time, value: currEma });
    
    if (prevMost === 0) {
      // Initialize on first valid EMA
      trend = 1;
      prevMost = currEma * (1 - pct);
      mostResults.push({ time, value: prevMost });
      continue;
    }
    
    let currMost = 0;
    
    if (trend === 1) {
      if (currEma < prevMost) {
        trend = -1;
        currMost = currEma * (1 + pct);
      } else {
        currMost = Math.max(prevMost, currEma * (1 - pct));
      }
    } else {
      if (currEma > prevMost) {
        trend = 1;
        currMost = currEma * (1 - pct);
      } else {
        currMost = Math.min(prevMost, currEma * (1 + pct));
      }
    }
    
    prevMost = currMost;
    mostResults.push({ time, value: currMost });
  }
  
  return { most: mostResults, ema: emaResults };
}
