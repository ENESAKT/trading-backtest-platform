import Chart from 'chart.js/auto';
import type { PortfolioEngine } from '../core/PortfolioEngine.js';
import { TR, formatNumber, formatCurrency, formatPct, formatDateTime } from '../constants/tr.js';
import { ALL_SYMBOLS } from '../constants/symbols.js';

// ─── PortfolioPanel ───────────────────────────────────────────────────────────

export class PortfolioPanel {
  private container: HTMLElement;
  private engine: PortfolioEngine;
  private pieChart: Chart | null = null;
  private currentPrice = 0;
  private currentSymbol = '';

  constructor(container: HTMLElement, engine: PortfolioEngine) {
    this.container = container;
    this.engine    = engine;
    engine.onChange(() => this.refresh());
    this.render();
  }

  // ─── Called when active symbol / price changes ────────────────────────

  setCurrentPrice(symbol: string, price: number): void {
    this.currentSymbol = symbol;
    this.currentPrice  = price;
    const priceInput = this.container.querySelector<HTMLInputElement>('#trade-price');
    if (priceInput && !priceInput.dataset['userEdited']) {
      priceInput.placeholder = `${TR.MARKET_PRICE}: ${formatNumber(price)}`;
    }
  }

  // ─── Render ──────────────────────────────────────────────────────────────

  private render(): void {
    this.container.innerHTML = `
      <div class="portfolio-wrap">

        <!-- Summary Cards -->
        <div class="summary-cards" id="summary-cards"></div>

        <div class="portfolio-body">
          <!-- Left: Positions + Trade Form -->
          <div class="portfolio-left">
            <div class="panel-section">
              <h3>${TR.POSITIONS}</h3>
              <div id="positions-table"></div>
            </div>
            <div class="panel-section">
              <h3>${TR.TRADE_FORM}</h3>
              ${this.tradeFormHTML()}
            </div>
            <div class="panel-section">
              <h3>${TR.TRADE_HISTORY}</h3>
              <div id="trade-history"></div>
            </div>
          </div>

          <!-- Right: Pie chart -->
          <div class="portfolio-right">
            <div class="panel-section">
              <h3>${TR.PORTFOLIO_ALLOCATION}</h3>
              <div class="pie-wrap"><canvas id="portfolio-pie"></canvas></div>
            </div>
          </div>
        </div>

      </div>
    `;

    this.bindTradeForm();
    this.refresh();
  }

  private tradeFormHTML(): string {
    return `
      <div class="trade-form">
        <div class="form-row">
          <label>${TR.SYMBOL}</label>
          <input type="text" id="trade-symbol" list="symbol-datalist" placeholder="BTCUSDT" />
          <datalist id="symbol-datalist">
            ${ALL_SYMBOLS.map(s => `<option value="${s.symbol}">${s.name}</option>`).join('')}
          </datalist>
        </div>
        <div class="form-row">
          <label>${TR.TYPE}</label>
          <div class="toggle-group">
            <button class="toggle-btn active" data-trade-type="BUY">${TR.BUY}</button>
            <button class="toggle-btn" data-trade-type="SELL">${TR.SELL}</button>
          </div>
        </div>
        <div class="form-row">
          <label>${TR.QUANTITY}</label>
          <input type="number" id="trade-qty" min="0.0001" step="0.0001" placeholder="0" />
        </div>
        <div class="form-row">
          <label>${TR.PRICE}</label>
          <input type="number" id="trade-price" min="0" step="any" placeholder="${TR.MARKET_PRICE}" />
        </div>
        <div id="trade-error" class="trade-error"></div>
        <button class="btn-primary" id="trade-execute">${TR.EXECUTE}</button>
      </div>
    `;
  }

  // ─── Trade form binding ─────────────────────────────────────────────────

  private bindTradeForm(): void {
    let selectedType: 'BUY' | 'SELL' = 'BUY';

    const typeBtns = this.container.querySelectorAll<HTMLButtonElement>('[data-trade-type]');
    typeBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        typeBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        selectedType = btn.dataset['tradeType'] as 'BUY' | 'SELL';
      });
    });

    const priceInput = this.container.querySelector<HTMLInputElement>('#trade-price')!;
    priceInput.addEventListener('focus', () => { priceInput.dataset['userEdited'] = '1'; });
    priceInput.addEventListener('blur', () => {
      if (!priceInput.value) delete priceInput.dataset['userEdited'];
    });

    const executeBtn = this.container.querySelector<HTMLButtonElement>('#trade-execute')!;
    const errorEl    = this.container.querySelector<HTMLDivElement>('#trade-error')!;

    executeBtn.addEventListener('click', () => {
      errorEl.textContent = '';

      const symInput = this.container.querySelector<HTMLInputElement>('#trade-symbol')!;
      const qtyInput = this.container.querySelector<HTMLInputElement>('#trade-qty')!;

      const symbol = (symInput.value.trim() || this.currentSymbol).toUpperCase();
      const qty    = parseFloat(qtyInput.value);
      const price  = parseFloat(priceInput.value) || this.currentPrice;

      if (!symbol)    { errorEl.textContent = TR.SYMBOL_NOT_FOUND;    return; }
      if (isNaN(qty) || qty <= 0) { errorEl.textContent = TR.INVALID_QUANTITY; return; }
      if (!price || price <= 0)   { errorEl.textContent = TR.DATA_NOT_AVAILABLE; return; }

      const result = selectedType === 'BUY'
        ? this.engine.buy(symbol, qty, price)
        : this.engine.sell(symbol, qty, price);

      if (!result.ok) {
        errorEl.textContent = TR[result.error as keyof typeof TR] as string ?? result.error ?? '';
      } else {
        qtyInput.value = '';
        priceInput.value = '';
        delete priceInput.dataset['userEdited'];
      }
    });

    // Sync symbol input with sidebar active symbol
    const symInput = this.container.querySelector<HTMLInputElement>('#trade-symbol')!;
    symInput.placeholder = this.currentSymbol || 'BTCUSDT';
  }

  // ─── Refresh (on portfolio change) ───────────────────────────────────────

  refresh(): void {
    this.renderSummary();
    this.renderPositions();
    this.renderHistory();
    this.renderPie();
  }

  private renderSummary(): void {
    const stats = this.engine.getStats();
    const el = this.container.querySelector('#summary-cards');
    if (!el) return;

    const card = (label: string, value: string, cls = '') =>
      `<div class="summary-card"><div class="sc-label">${label}</div><div class="sc-value ${cls}">${value}</div></div>`;

    el.innerHTML = [
      card(TR.TOTAL_VALUE,    formatCurrency(stats.totalValue)),
      card(TR.TOTAL_PNL,      formatCurrency(stats.totalPnL), stats.totalPnL >= 0 ? 'pos' : 'neg'),
      card(TR.CASH,           formatCurrency(this.engine.getPortfolio().cash)),
      card(TR.OPEN_POSITIONS, String(stats.openPositions)),
    ].join('');
  }

  private renderPositions(): void {
    const el = this.container.querySelector('#positions-table');
    if (!el) return;

    const positions = Object.values(this.engine.getPortfolio().positions);
    if (positions.length === 0) {
      el.innerHTML = `<div class="empty-state">${TR.NO_POSITIONS}</div>`;
      return;
    }

    el.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>${TR.SYMBOL}</th><th>${TR.QUANTITY}</th><th>${TR.AVG_COST}</th>
            <th>${TR.CURRENT_PRICE}</th><th>${TR.PNL}</th><th>${TR.PNL_PCT}</th><th></th>
          </tr>
        </thead>
        <tbody>
          ${positions.map(p => `
            <tr>
              <td class="sym-cell">${p.symbol}</td>
              <td>${formatNumber(p.quantity, 4)}</td>
              <td>${formatNumber(p.avgCost)}</td>
              <td>${formatNumber(p.currentPrice)}</td>
              <td class="${p.pnl >= 0 ? 'pos' : 'neg'}">${formatNumber(p.pnl)}</td>
              <td class="${p.pnlPct >= 0 ? 'pos' : 'neg'}">${formatPct(p.pnlPct)}</td>
              <td>
                <button class="btn-sm btn-danger close-pos" data-symbol="${p.symbol}" data-price="${p.currentPrice}">
                  ${TR.CLOSE_POSITION}
                </button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;

    el.querySelectorAll('.close-pos').forEach(btn => {
      btn.addEventListener('click', () => {
        const sym   = (btn as HTMLElement).dataset['symbol']!;
        const price = parseFloat((btn as HTMLElement).dataset['price']!);
        this.engine.closePosition(sym, price || this.currentPrice);
      });
    });
  }

  private renderHistory(): void {
    const el = this.container.querySelector('#trade-history');
    if (!el) return;

    const history = this.engine.getPortfolio().history.slice(0, 50);
    if (history.length === 0) {
      el.innerHTML = `<div class="empty-state">${TR.NO_TRADES}</div>`;
      return;
    }

    el.innerHTML = `
      <table class="data-table">
        <thead>
          <tr>
            <th>${TR.DATE}</th><th>${TR.TYPE}</th><th>${TR.SYMBOL}</th>
            <th>${TR.QUANTITY}</th><th>${TR.PRICE}</th><th>${TR.TOTAL}</th>
          </tr>
        </thead>
        <tbody>
          ${history.map(t => `
            <tr>
              <td>${formatDateTime(t.timestamp)}</td>
              <td class="${t.type === 'BUY' ? 'pos' : 'neg'}">${t.type === 'BUY' ? TR.BUY : TR.SELL}</td>
              <td class="sym-cell">${t.symbol}</td>
              <td>${formatNumber(t.quantity, 4)}</td>
              <td>${formatNumber(t.price)}</td>
              <td>${formatNumber(t.total)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  private renderPie(): void {
    const canvas = this.container.querySelector<HTMLCanvasElement>('#portfolio-pie');
    if (!canvas) return;

    const allocation = this.engine.getAllocation();
    if (allocation.length === 0) return;

    const labels = allocation.map(a => a.label);
    const data   = allocation.map(a => a.value);
    const colors = [
      '#58a6ff', '#3fb950', '#bc8cff', '#d29922', '#f85149',
      '#e3b341', '#39d353', '#6e7681', '#8b949e', '#c9d1d9',
    ];

    if (this.pieChart) {
      this.pieChart.data.labels = labels;
      this.pieChart.data.datasets[0]!.data = data;
      this.pieChart.update();
      return;
    }

    this.pieChart = new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{ data, backgroundColor: colors, borderColor: '#21262d', borderWidth: 2 }],
      },
      options: {
        plugins: {
          legend: { position: 'bottom', labels: { color: '#8b949e', font: { size: 11 } } },
        },
        cutout: '60%',
      },
    });
  }

  destroy(): void {
    this.pieChart?.destroy();
  }
}
