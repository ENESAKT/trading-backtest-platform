import type { Portfolio, Trade, PortfolioStats } from '../types.js';

const STORAGE_KEY = 'piyasapilot_portfolio';
const INITIAL_BALANCE = 100_000;

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function defaultPortfolio(): Portfolio {
  return {
    balance: INITIAL_BALANCE,
    cash: INITIAL_BALANCE,
    positions: {},
    history: [],
  };
}

// ─── PortfolioEngine ──────────────────────────────────────────────────────────

export class PortfolioEngine {
  private portfolio: Portfolio;
  private changeListeners: Set<() => void> = new Set();

  constructor() {
    this.portfolio = this.load();
  }

  // ─── Persistence ──────────────────────────────────────────────────────────

  private load(): Portfolio {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        return JSON.parse(raw) as Portfolio;
      }
    } catch {
      // corrupted storage — reset
    }
    return defaultPortfolio();
  }

  private save(): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.portfolio));
    } catch {
      // storage quota exceeded — silently ignore
    }
    this.changeListeners.forEach(l => l());
  }

  onChange(listener: () => void): () => void {
    this.changeListeners.add(listener);
    return () => this.changeListeners.delete(listener);
  }

  // ─── Trade operations ─────────────────────────────────────────────────────

  buy(symbol: string, quantity: number, price: number): { ok: boolean; error?: string } {
    if (quantity <= 0) return { ok: false, error: 'INVALID_QUANTITY' };
    if (price <= 0)    return { ok: false, error: 'INVALID_QUANTITY' };

    const total = quantity * price;
    if (total > this.portfolio.cash) {
      return { ok: false, error: 'INSUFFICIENT_CASH' };
    }

    this.portfolio.cash -= total;

    const existing = this.portfolio.positions[symbol];
    if (existing) {
      const totalQty  = existing.quantity + quantity;
      const totalCost = existing.avgCost * existing.quantity + price * quantity;
      existing.quantity = totalQty;
      existing.avgCost  = totalCost / totalQty;
      existing.currentPrice = price;
      existing.pnl    = (price - existing.avgCost) * existing.quantity;
      existing.pnlPct = ((price / existing.avgCost) - 1) * 100;
    } else {
      this.portfolio.positions[symbol] = {
        symbol,
        quantity,
        avgCost: price,
        currentPrice: price,
        pnl: 0,
        pnlPct: 0,
      };
    }

    const trade: Trade = {
      id: generateId(),
      type: 'BUY',
      symbol,
      quantity,
      price,
      timestamp: Math.floor(Date.now() / 1000),
      total,
    };
    this.portfolio.history.unshift(trade);

    this.save();
    return { ok: true };
  }

  sell(symbol: string, quantity: number, price: number): { ok: boolean; error?: string } {
    if (quantity <= 0) return { ok: false, error: 'INVALID_QUANTITY' };

    const pos = this.portfolio.positions[symbol];
    if (!pos) return { ok: false, error: 'SYMBOL_NOT_FOUND' };
    if (pos.quantity < quantity) return { ok: false, error: 'INSUFFICIENT_POSITION' };

    const total = quantity * price;
    this.portfolio.cash += total;

    pos.quantity -= quantity;
    if (pos.quantity === 0) {
      delete this.portfolio.positions[symbol];
    } else {
      pos.currentPrice = price;
      pos.pnl    = (price - pos.avgCost) * pos.quantity;
      pos.pnlPct = ((price / pos.avgCost) - 1) * 100;
    }

    const trade: Trade = {
      id: generateId(),
      type: 'SELL',
      symbol,
      quantity,
      price,
      timestamp: Math.floor(Date.now() / 1000),
      total,
    };
    this.portfolio.history.unshift(trade);

    this.save();
    return { ok: true };
  }

  closePosition(symbol: string, price: number): { ok: boolean; error?: string } {
    const pos = this.portfolio.positions[symbol];
    if (!pos) return { ok: false, error: 'SYMBOL_NOT_FOUND' };
    return this.sell(symbol, pos.quantity, price);
  }

  // ─── Price update (called on each poll cycle) ────────────────────────────

  updatePrices(priceMap: Map<string, number>): void {
    let changed = false;
    for (const [symbol, price] of priceMap) {
      const pos = this.portfolio.positions[symbol];
      if (pos) {
        pos.currentPrice = price;
        pos.pnl    = (price - pos.avgCost) * pos.quantity;
        pos.pnlPct = ((price / pos.avgCost) - 1) * 100;
        changed = true;
      }
    }
    if (changed) this.save();
  }

  // ─── Stats ───────────────────────────────────────────────────────────────

  getStats(): PortfolioStats {
    const positions = Object.values(this.portfolio.positions);
    const posValue = positions.reduce((acc, p) => acc + p.currentPrice * p.quantity, 0);
    const totalValue = this.portfolio.cash + posValue;
    const totalPnL = totalValue - this.portfolio.balance;
    const totalPnLPct = (totalPnL / this.portfolio.balance) * 100;

    const closedTrades = this.portfolio.history.filter(t => t.type === 'SELL');
    const wins = closedTrades.filter(t => {
      // look for matching BUY in history
      const buy = this.portfolio.history.find(
        h => h.type === 'BUY' && h.symbol === t.symbol && h.timestamp < t.timestamp
      );
      return buy && t.price > buy.price;
    });
    const winRate = closedTrades.length > 0
      ? (wins.length / closedTrades.length) * 100
      : 0;

    return {
      totalValue,
      totalPnL,
      totalPnLPct,
      winRate,
      openPositions: positions.length,
    };
  }

  getPortfolio(): Portfolio {
    return this.portfolio;
  }

  reset(): void {
    this.portfolio = defaultPortfolio();
    this.save();
  }

  // ─── Allocation data (for pie chart) ────────────────────────────────────

  getAllocation(): Array<{ label: string; value: number }> {
    const result: Array<{ label: string; value: number }> = [];
    const p = this.portfolio;

    if (p.cash > 0) result.push({ label: 'Nakit', value: p.cash });

    for (const pos of Object.values(p.positions)) {
      result.push({ label: pos.symbol, value: pos.currentPrice * pos.quantity });
    }

    return result;
  }
}
