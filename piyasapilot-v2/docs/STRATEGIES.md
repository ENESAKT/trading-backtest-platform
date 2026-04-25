# Trading Strategies Reference

Three strategies are implemented in `src/strategies/`. Each exports `generateSignals()` for live signal generation and a `backtest()` function for historical performance evaluation.

---

## Strategy 1: Trend Following (Trend Takip)

**File:** [src/strategies/TrendFollowing.ts](../src/strategies/TrendFollowing.ts)

### Logic

**Entry (BUY):**
- EMA9 crosses **above** EMA21 (golden cross on short-term MAs)
- RSI > 50 (momentum confirmation — buyers in control)
- Close > EMA50 (long-term uptrend filter)
- All 3 conditions must be true simultaneously

**Exit (SELL):**
- EMA9 crosses **below** EMA21 (death cross), OR
- RSI < 45 (momentum weakening)

**Signal Strength (1–10):**
```
distPct = (close − EMA50) / EMA50 × 100
strength = min(10, max(1, round(distPct / 0.5)))
```
Higher strength = price further above EMA50 = stronger trend.

### Best Market Conditions
- Trending markets with clear directional bias
- Works best on daily/weekly timeframes
- Avoid during sideways/ranging markets (whipsaws)

### Backtest Methodology
- Initial capital: 10.000 units
- Each BUY uses 100% of available cash
- Each SELL closes the entire position
- Metrics: annualized Sharpe, equity-curve max drawdown

---

## Strategy 2: Mean Reversion (Ortalamaya Dönüş)

**File:** [src/strategies/MeanReversion.ts](../src/strategies/MeanReversion.ts)

### Logic

**Entry LONG (BUY):**
- Close ≤ BB Lower × 1.01 (within 1% of lower band)
- RSI < 35 (oversold confirmation)

**Entry SHORT signal (SELL):**
- Close ≥ BB Upper × 0.99 (within 1% of upper band)
- RSI > 65 (overbought confirmation)

**Exit:**
- Price crosses above (or returns to) BB Midline (SMA20)
- Also exits on opposite band touch

**Signal Strength (1–10):**
```
Long strength  = min(10, round((35 − RSI) / 2))
Short strength = min(10, round((RSI − 65) / 2))
```

### Best Market Conditions
- Ranging / sideways markets
- High-volatility instruments where price oscillates around mean
- Avoid in strong trending markets (price can ride band for extended periods)

### Risk Note
Mean reversion trades can have extended drawdowns when trends persist. Always use with appropriate position sizing.

---

## Strategy 3: Breakout Detector (Kırılım)

**File:** [src/strategies/BreakoutDetector.ts](../src/strategies/BreakoutDetector.ts)

### Logic

**Consolidation Detection:**
```
ATR[i] < avg_ATR(20) × 0.7
```
Identifies periods where volatility has compressed below 70% of its 20-period average — classic pre-breakout setup.

**Entry (BUY) — all conditions required:**
1. Current bar is in consolidation (ATR < threshold)
2. Close > max(High[i-1 to i-N]) — breaks above N-day (20) high
3. Volume > avgVolume(20) × 1.5 — volume surge confirms breakout

**Exit:**
- Stop-loss: price falls below the breakout candle's low
- No fixed take-profit (ride the trend)

**Signal Strength (1–10):**
```
strength = min(10, round((volume/avgVolume − 1) × 3))
```
Higher volume ratio = stronger conviction breakout.

### Best Market Conditions
- After extended consolidation periods
- Works well on individual stocks, crypto pairs
- Volume surge is essential — avoid low-volume breakouts (false breakouts)

---

## Backtest Engine

**File:** [src/strategies/TrendFollowing.ts](../src/strategies/TrendFollowing.ts) — `runBacktest()` function

### Methodology

```typescript
// Position sizing: 100% of available capital per trade
const qty = cash / candle.close;

// Metrics computed at end of simulation:
totalReturn  = (finalValue − INITIAL_CASH) / INITIAL_CASH × 100
winRate      = wins / totalTrades × 100
profitFactor = grossProfit / |grossLoss|
maxDrawdown  = max peak-to-trough % decline
sharpeRatio  = (mean_daily_return / std_daily_return) × √252
```

### Sharpe Ratio Note
Computed on the equity curve daily returns. Annualized by √252. A ratio > 1.0 is generally considered good; > 2.0 is excellent.

### Max Drawdown
Computed as the maximum percentage decline from any peak to the subsequent trough. Lower is better. Drawdowns > 30% indicate significant risk.

---

## Risk Management Guidelines

1. **Position sizing**: The backtest uses 100% capital allocation for simplicity. In practice, risk 1–2% of capital per trade.
2. **Stop losses**: Only Breakout strategy uses explicit stop-loss. Add stops to other strategies before live trading.
3. **Slippage**: Backtest assumes fills at close price. Real fills will differ, especially in illiquid markets.
4. **Overfitting**: Strategies use standard parameters — no optimization against the test data set. Beware of curve-fitting when adjusting parameters.
5. **Paper trading**: All signals and backtest results are for educational purposes. Use the Portfolio panel for paper trading practice before real markets.
