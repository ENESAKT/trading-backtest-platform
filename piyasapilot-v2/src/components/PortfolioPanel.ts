import type { PortfolioEngine } from '../core/PortfolioEngine.js';
import { TR, formatNumber, formatCurrency, formatPct, formatDateTime } from '../constants/tr.js';

const POLL_INTERVAL_MS = 5_000;

interface PaperWallet {
  strategy_id: string;
  cash: number;
  initial_capital: number;
  daily_loss: number;
  daily_reset_date: string;
  is_halted: number;
}

interface PaperTrade {
  id: number;
  strategy_id: string;
  symbol: string;
  side: string;
  price: number;
  quantity: number;
  commission: number;
  pnl: number | null;
  opened_at: string;
  closed_at: string | null;
  reason: string;
}

// ─── PortfolioPanel ───────────────────────────────────────────────────────────

export class PortfolioPanel {
  private container: HTMLElement;
  private engine: PortfolioEngine;
  private pollTimer: ReturnType<typeof setInterval> | null = null;
  private wallets: PaperWallet[] = [];
  private trades: PaperTrade[] = [];
  private currentSymbol = '';
  private currentPrice = 0;

  constructor(container: HTMLElement, engine: PortfolioEngine) {
    this.container = container;
    this.engine = engine;
    this.render();
    this.startPolling();
  }

  setCurrentPrice(symbol: string, price: number): void {
    this.currentSymbol = symbol;
    this.currentPrice = price;
  }

  destroy(): void {
    if (this.pollTimer !== null) clearInterval(this.pollTimer);
  }

  // ─── Polling ─────────────────────────────────────────────────────────────

  private startPolling(): void {
    void this.fetchAndRender();
    this.pollTimer = setInterval(() => void this.fetchAndRender(), POLL_INTERVAL_MS);
  }

  private async fetchAndRender(): Promise<void> {
    try {
      const [walletsRes, tradesRes] = await Promise.all([
        fetch('/api/paper/wallets'),
        fetch('/api/paper/trades?limit=50'),
      ]);
      if (walletsRes.ok) {
        const data = await walletsRes.json() as { wallets: PaperWallet[] };
        this.wallets = data.wallets ?? [];
      }
      if (tradesRes.ok) {
        const data = await tradesRes.json() as { trades: PaperTrade[] };
        this.trades = data.trades ?? [];
      }
      this.renderWallets();
      this.renderTrades();
    } catch {
      // ağ hatası — sessizce geç, bir sonraki poll'da tekrar dener
    }
  }

  private async resetWallet(strategyId: string): Promise<void> {
    await fetch(`/api/paper/reset/${encodeURIComponent(strategyId)}`, { method: 'POST' });
    void this.fetchAndRender();
  }

  // ─── Render ──────────────────────────────────────────────────────────────

  private render(): void {
    this.container.innerHTML = `
      <div class="portfolio-wrap">

        <!-- Paper Trading Section -->
        <div class="paper-section">
          <h2 class="paper-title">${TR.WALLETS}</h2>
          <div id="paper-wallets" class="paper-wallets-grid"></div>
        </div>

        <div class="paper-section">
          <h2 class="paper-title">${TR.TRADE_HISTORY}</h2>
          <div id="paper-trades"></div>
        </div>

      </div>
    `;

    this.renderWallets();
    this.renderTrades();
  }

  private renderWallets(): void {
    const el = this.container.querySelector('#paper-wallets');
    if (!el) return;

    if (this.wallets.length === 0) {
      el.innerHTML = `<div class="empty-state">${TR.NO_WALLETS}</div>`;
      return;
    }

    el.innerHTML = this.wallets.map(w => this.walletCardHTML(w)).join('');

    el.querySelectorAll<HTMLButtonElement>('.btn-reset-wallet').forEach(btn => {
      btn.addEventListener('click', () => {
        const sid = btn.dataset['strategyId']!;
        void this.resetWallet(sid);
      });
    });
  }

  private walletCardHTML(w: PaperWallet): string {
    const equity = w.cash;  // open positions not tracked in-memory on frontend
    const pnl = equity - w.initial_capital;
    const pnlPct = (pnl / w.initial_capital) * 100;
    const haltedBadge = w.is_halted
      ? `<span class="wallet-halted-badge">${TR.WALLET_HALTED}</span>`
      : '';
    const dailyLoss = w.daily_loss;
    const dailyLossPct = (Math.abs(dailyLoss) / w.initial_capital) * 100;

    return `
      <div class="wallet-card ${w.is_halted ? 'wallet-halted' : ''}">
        <div class="wallet-header">
          <span class="wallet-strategy">${w.strategy_id}</span>
          ${haltedBadge}
        </div>
        <div class="wallet-metrics">
          <div class="wm-item">
            <span class="wm-label">${TR.CASH}</span>
            <span class="wm-value">${formatCurrency(w.cash)}</span>
          </div>
          <div class="wm-item">
            <span class="wm-label">${TR.TOTAL_PNL}</span>
            <span class="wm-value ${pnl >= 0 ? 'pos' : 'neg'}">${formatCurrency(pnl)} (${formatPct(pnlPct)})</span>
          </div>
          <div class="wm-item">
            <span class="wm-label">${TR.DAILY_PNL}</span>
            <span class="wm-value ${dailyLoss >= 0 ? '' : 'neg'}">${formatCurrency(dailyLoss)} (${formatPct(-dailyLossPct)})</span>
          </div>
        </div>
        <button class="btn-sm btn-secondary btn-reset-wallet" data-strategy-id="${w.strategy_id}">${TR.RESET_WALLET}</button>
      </div>
    `;
  }

  private renderTrades(): void {
    const el = this.container.querySelector('#paper-trades');
    if (!el) return;

    if (this.trades.length === 0) {
      el.innerHTML = `<div class="empty-state">${TR.NO_TRADES}</div>`;
      return;
    }

    el.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>${TR.DATE}</th>
            <th>${TR.STRATEGY}</th>
            <th>${TR.SYMBOL}</th>
            <th>${TR.TYPE}</th>
            <th>${TR.PRICE}</th>
            <th>${TR.QUANTITY}</th>
            <th>${TR.PNL}</th>
          </tr>
        </thead>
        <tbody>
          ${this.trades.map(t => this.tradeRowHTML(t)).join('')}
        </tbody>
      </table>
    `;
  }

  private tradeRowHTML(t: PaperTrade): string {
    const ts = new Date(t.opened_at).getTime() / 1000;
    const pnlCell = t.pnl !== null
      ? `<td class="${t.pnl >= 0 ? 'pos' : 'neg'}">${formatNumber(t.pnl)}</td>`
      : '<td class="text-dim">—</td>';

    return `
      <tr>
        <td>${formatDateTime(ts)}</td>
        <td class="text-dim" style="font-size:10px">${t.strategy_id}</td>
        <td class="sym-cell">${t.symbol}</td>
        <td class="${t.side === 'BUY' ? 'pos' : 'neg'}">${t.side === 'BUY' ? TR.BUY : TR.SELL}</td>
        <td>${formatNumber(t.price, 4)}</td>
        <td>${formatNumber(t.quantity, 4)}</td>
        ${pnlCell}
      </tr>
    `;
  }
}
