# Indicators Reference

All indicators are pure functions located in `src/indicators/`. They accept typed arrays, handle NaN/edge cases internally, and return NaN for positions with insufficient data.

---

## EMA — Exponential Moving Average

**File:** [src/indicators/ema.ts](../src/indicators/ema.ts)

**Formula:**
```
k = 2 / (period + 1)
EMA[i] = close[i] × k + EMA[i-1] × (1 - k)
```
Seeded with SMA of the first `period` bars.

**Parameters:**
- `closes: number[]` — closing price array
- `period: number` — smoothing period

**Instances used:**
- EMA(9)  — fast trend line, yellow
- EMA(21) — mid trend line, orange
- EMA(50) — slow trend filter, blue

**Interpretation:**
- EMA9 > EMA21 → short-term bullish momentum
- Price > EMA50 → long-term uptrend filter

---

## SMA — Simple Moving Average

**File:** [src/indicators/sma.ts](../src/indicators/sma.ts)

**Formula:**
```
SMA[i] = (close[i] + close[i-1] + ... + close[i-period+1]) / period
```
Uses a sliding window sum for O(n) performance.

**Parameters:**
- `closes: number[]`
- `period: number`

**Instances used:**
- SMA(20) — Bollinger Bands midline, screener volume average baseline

---

## RSI — Relative Strength Index

**File:** [src/indicators/rsi.ts](../src/indicators/rsi.ts)

**Formula:**
```
Δ   = close[i] − close[i-1]
Gain = max(Δ, 0)
Loss = max(−Δ, 0)

Wilder smoothing:
  AvgGain[i] = (AvgGain[i-1] × (period-1) + Gain[i]) / period
  AvgLoss[i] = (AvgLoss[i-1] × (period-1) + Loss[i]) / period

RS  = AvgGain / AvgLoss
RSI = 100 − (100 / (1 + RS))
```

**Parameters:** `closes: number[]`, `period = 14`

**Interpretation:**
- RSI < 30 → oversold (potential buy)
- RSI > 70 → overbought (potential sell)
- RSI > 50 → bullish momentum confirmation

---

## MACD — Moving Average Convergence Divergence

**File:** [src/indicators/macd.ts](../src/indicators/macd.ts)

**Formula:**
```
MACD Line   = EMA(fast) − EMA(slow)
Signal Line = EMA(MACD, signal)
Histogram   = MACD Line − Signal Line
```

**Parameters:** `closes: number[]`, `fast=12`, `slow=26`, `signal=9`

**Returns:** `{ macd: number[], signal: number[], histogram: number[] }`

**Interpretation:**
- MACD > Signal → bullish crossover
- Histogram > 0 → momentum increasing
- Histogram shrinking from peak → momentum fading

---

## Bollinger Bands

**File:** [src/indicators/bollinger.ts](../src/indicators/bollinger.ts)

**Formula:**
```
Mid   = SMA(period)
StdDev = √( Σ(close[i] − Mid)² / period )
Upper = Mid + multiplier × StdDev
Lower = Mid − multiplier × StdDev
```

**Parameters:** `closes: number[]`, `period=20`, `stdDevMult=2`

**Returns:** `{ upper: number[], mid: number[], lower: number[] }`

**Interpretation:**
- Price at lower band + RSI < 30 → mean reversion buy
- Price at upper band + RSI > 70 → mean reversion sell
- Narrow bands (low ATR) → consolidation before breakout

---

## ATR — Average True Range

**File:** [src/indicators/atr.ts](../src/indicators/atr.ts)

**Formula:**
```
TR[i] = max(
  High[i] − Low[i],
  |High[i] − Close[i-1]|,
  |Low[i]  − Close[i-1]|
)
ATR[i] = (ATR[i-1] × (period-1) + TR[i]) / period   (Wilder)
```

**Parameters:** `candles: OHLCV[]`, `period=14`

**Interpretation:**
- High ATR → high volatility / active market
- ATR < 0.7 × 20-period average → consolidation (Breakout filter)
- Used for stop-loss sizing

---

## VWAP — Volume Weighted Average Price

**File:** [src/indicators/vwap.ts](../src/indicators/vwap.ts)

**Formula:**
```
TP[i]   = (High[i] + Low[i] + Close[i]) / 3
VWAP[i] = Σ(TP × Volume) / Σ(Volume)   [resets each new day]
```

**Parameters:** `candles: OHLCV[]`

**Interpretation:**
- Price > VWAP → buyers in control for the session
- Price < VWAP → sellers in control
- Institutional reference level for intraday

---

## Stochastic Oscillator

**File:** [src/indicators/stochastic.ts](../src/indicators/stochastic.ts)

**Formula:**
```
%K[i] = 100 × (Close[i] − Lowest Low[k]) / (Highest High[k] − Lowest Low[k])
%D[i] = SMA(%K, d)
```

**Parameters:** `candles: OHLCV[]`, `kPeriod=14`, `dPeriod=3`

**Returns:** `{ k: number[], d: number[] }`

**Interpretation:**
- %K < 20 → oversold
- %K > 80 → overbought
- %K crosses above %D → bullish signal
- %K crosses below %D → bearish signal

---

## computeIndicators()

**File:** [src/indicators/index.ts](../src/indicators/index.ts)

Convenience function that computes the full `IndicatorSet` in a single call:

```typescript
const inds = computeIndicators(candles);
// inds.rsi, inds.macd, inds.bb, inds.ema9, inds.ema21,
// inds.ema50, inds.sma20, inds.atr, inds.vwap, inds.stochastic
```

Used by ChartPanel, StrategyPanel, and Screener.
