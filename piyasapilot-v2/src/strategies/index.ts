export { generateTrendSignals,  backtestTrend,    TrendFollowingMeta } from './TrendFollowing.js';
export { generateMeanSignals,   backtestMean,     MeanReversionMeta  } from './MeanReversion.js';
export { generateBreakoutSignals, backtestBreakout, BreakoutMeta      } from './BreakoutDetector.js';

import type { OHLCV, IndicatorSet, Signal, BacktestResult } from '../types.js';
import { generateTrendSignals,  backtestTrend    } from './TrendFollowing.js';
import { generateMeanSignals,   backtestMean     } from './MeanReversion.js';
import { generateBreakoutSignals, backtestBreakout } from './BreakoutDetector.js';

export type StrategyId = 'trend' | 'mean' | 'breakout';

export function generateSignals(
  id: StrategyId,
  candles: OHLCV[],
  inds: IndicatorSet
): Signal[] {
  switch (id) {
    case 'trend':    return generateTrendSignals(candles, inds);
    case 'mean':     return generateMeanSignals(candles, inds);
    case 'breakout': return generateBreakoutSignals(candles, inds);
  }
}

export function runBacktestById(id: StrategyId, candles: OHLCV[]): BacktestResult {
  switch (id) {
    case 'trend':    return backtestTrend(candles);
    case 'mean':     return backtestMean(candles);
    case 'breakout': return backtestBreakout(candles);
  }
}
