# Portfolio Engine Reference

The paper trading system is implemented in `src/core/PortfolioEngine.ts` and `src/components/PortfolioPanel.ts`.

---

## Paper Trading Rules

1. **Virtual capital only** — no real money is involved. Starting balance: **₺100.000**.
2. **Market orders only** — fills execute at the price entered (or last known price).
3. **No leverage** — positions are fully cash-funded.
4. **No short selling** — only long positions supported.
5. **No commissions** — fills are cost-free for simplicity.
6. **Fractional shares allowed** — useful for crypto (e.g., 0.001 BTC).

---

## localStorage Schema

The portfolio state is persisted to `localStorage` under the key `piyasapilot_portfolio`.

### Portfolio Object

```typescript
interface Portfolio {
  balance: number;                      // Initial balance (100000)
  cash: number;                         // Available cash
  positions: Record<string, Position>;  // Open positions keyed by symbol
  history: Trade[];                     // All trade records (newest first)
}
```

### Position Object

```typescript
interface Position {
  symbol:       string;  // e.g. "BTCUSDT"
  quantity:     number;  // Number of units held
  avgCost:      number;  // Average cost per unit (₺)
  currentPrice: number;  // Last known price
  pnl:          number;  // Unrealized PnL in currency
  pnlPct:       number;  // Unrealized PnL in percent
}
```

### Trade Object

```typescript
interface Trade {
  id:        string;          // Random unique ID
  type:      'BUY' | 'SELL'; // Trade direction
  symbol:    string;          // Asset symbol
  quantity:  number;          // Units traded
  price:     number;          // Execution price
  timestamp: number;          // Unix timestamp (seconds)
  total:     number;          // quantity × price
}
```

---

## PnL Calculation Methodology

### Average Cost (on BUY)

When buying additional units in an existing position, the average cost is recalculated:
```
newQty     = oldQty + buyQty
newAvgCost = (oldAvgCost × oldQty + buyPrice × buyQty) / newQty
```

### Unrealized PnL (updated on each price tick)

```
PnL     = (currentPrice − avgCost) × quantity
PnL%    = (currentPrice / avgCost − 1) × 100
```

### Total Portfolio Value

```
totalValue = cash + Σ(position.currentPrice × position.quantity)
totalPnL   = totalValue − initialBalance
totalPnL%  = totalPnL / initialBalance × 100
```

### Win Rate (for closed trades)

A closed trade is counted as a WIN if the SELL price is higher than the matched BUY price:
```
winRate = wins / totalClosedTrades × 100
```

The matching algorithm finds the most recent BUY for the same symbol with an earlier timestamp.

---

## Usage Notes

### Resetting the Portfolio

The portfolio can be reset to initial state by calling `engine.reset()`. This clears all positions and history and restores the 100.000 ₺ cash balance.

### Data Persistence

- Portfolio is saved on every state change (buy, sell, price update).
- Data survives page refreshes and browser restarts.
- If localStorage is corrupted or unavailable, the engine silently initializes with default values.

### Price Updates

`updatePrices(priceMap: Map<string, number>)` is called on every data poll cycle:
- Updates `currentPrice` for all open positions matching the map.
- Recalculates `pnl` and `pnlPct` for each affected position.
- Saves to localStorage only if at least one position was updated.

### Allocation Chart

`getAllocation()` returns an array of `{ label, value }` objects:
- One entry per open position (label = symbol, value = market value)
- One entry for cash
- Used to render the doughnut chart in PortfolioPanel
