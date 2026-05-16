import Chart from 'chart.js/auto';
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

interface EquityPoint {
  id: number;
  strategy_id: string;
  ts: string;
  total_equity: number;
  cash: number;
  positions_value: number;
}

// ─── PortfolioPanel v2 ────────────────────────────────────────────────────────

export class PortfolioPanel {
  private container: HTMLElement;
  private pollTimer: ReturnType<typeof setInterval> | null = null;
  private wallets: PaperWallet[] = [];
  private trades: PaperTrade[] = [];
  private equityChart: Chart | null = null;
  private drawdownChart: Chart | null = null;
  private selectedStrategy = '';

  constructor(container: HTMLElement, _engine: unknown) {
    this.container = container;
    this.render();
    this.startPolling();
  }

  setCurrentPrice(_symbol: string, _price: number): void {
    // Fiyat güncellemeleri gelecekte unrealized PnL için kullanılacak
  }

  destroy(): void {
    if (this.pollTimer !== null) clearInterval(this.pollTimer);
    this.equityChart?.destroy();
    this.drawdownChart?.destroy();
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
        fetch('/api/paper/trades?limit=100'),
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
      this.renderMetrics();
      this.renderTrades();

      // Equity curve varsa seçili strateji için yükle
      if (this.selectedStrategy || this.wallets.length > 0) {
        const sid = this.selectedStrategy || this.wallets[0]?.strategy_id || '';
        if (sid) await this.fetchEquityCurve(sid);
      }
    } catch {
      // ağ hatası — sessizce geç
    }
  }

  private async fetchEquityCurve(strategyId: string): Promise<void> {
    try {
      const res = await fetch(`/api/paper/equity?strategy_id=${encodeURIComponent(strategyId)}&limit=200`);
      if (!res.ok) return;
      const data = await res.json() as { equity_curve: EquityPoint[] };
      this.renderEquityCurve(data.equity_curve ?? []);
    } catch {
      // sessizce geç
    }
  }

  /** Tema uyumlu onay diyaloğu — window.confirm() yerine kullanılır */
  private showConfirm(message: string, onConfirm: () => void): void {
    let dlg = document.getElementById('portfolio-confirm-dialog') as HTMLDialogElement | null;
    if (!dlg) {
      dlg = document.createElement('dialog');
      dlg.id = 'portfolio-confirm-dialog';
      dlg.innerHTML = `
        <div class="confirm-dialog-body">
          <p class="confirm-msg"></p>
          <div class="confirm-actions">
            <button class="btn-sm btn-secondary confirm-cancel">Vazgeç</button>
            <button class="btn-sm btn-danger confirm-ok">Onayla</button>
          </div>
        </div>
      `;
      document.body.appendChild(dlg);
      dlg.querySelector('.confirm-cancel')?.addEventListener('click', () => dlg!.close());
    }
    (dlg.querySelector('.confirm-msg') as HTMLElement).textContent = message;
    const okBtn = dlg.querySelector('.confirm-ok') as HTMLElement;
    const newOk = okBtn.cloneNode(true) as HTMLElement;
    okBtn.parentNode!.replaceChild(newOk, okBtn);
    newOk.addEventListener('click', () => { dlg!.close(); onConfirm(); }, { once: true });
    dlg.showModal();
  }

  private async resetWallet(strategyId: string): Promise<void> {
    this.showConfirm(
      `${strategyId} paper cüzdanı sıfırlansın mı? Bu işlem sadece sanal/paper kayıtlarını etkiler, gerçek piyasaya emir göndermez.`,
      async () => {
        await fetch(`/api/paper/reset/${encodeURIComponent(strategyId)}`, { method: 'POST' });
        void this.fetchAndRender();
      }
    );
  }

  private async haltWallet(strategyId: string): Promise<void> {
    this.showConfirm(
      `${strategyId} paper cüzdanı dondurulsun mu? Yeni sanal emir üretimi durur.`,
      async () => {
        await fetch(`/api/paper/halt/${encodeURIComponent(strategyId)}`, { method: 'POST' });
        void this.fetchAndRender();
      }
    );
  }

  private async resumeWallet(strategyId: string): Promise<void> {
    await fetch(`/api/paper/resume/${encodeURIComponent(strategyId)}`, { method: 'POST' });
    void this.fetchAndRender();
  }

  // ─── Metrik hesaplama ───────────────────────────────────────────────────

  private computeMetrics(): {
    totalEquity: number;
    totalPnl: number;
    totalPnlPct: number;
    winRate: number;
    totalCompleted: number;
    winners: number;
    profitFactor: number;
    avgPnl: number;
    maxDrawdown: number;
  } {
    const totalCapital = this.wallets.reduce((s, w) => s + w.initial_capital, 0);
    const totalCash = this.wallets.reduce((s, w) => s + w.cash, 0);
    const totalEquity = totalCash; // open positions not tracked client-side
    const totalPnl = totalCapital > 0 ? totalEquity - totalCapital : 0;
    const totalPnlPct = totalCapital > 0 ? (totalPnl / totalCapital) * 100 : 0;

    const completed = this.trades.filter(t => t.closed_at !== null && t.pnl !== null);
    const winners = completed.filter(t => (t.pnl ?? 0) > 0);
    const winRate = completed.length > 0 ? (winners.length / completed.length) * 100 : 0;

    let grossProfit = 0;
    let grossLoss = 0;
    for (const t of completed) {
      const p = t.pnl ?? 0;
      if (p > 0) grossProfit += p;
      else grossLoss += Math.abs(p);
    }
    const profitFactor = grossLoss > 0 ? grossProfit / grossLoss : (grossProfit > 0 ? Infinity : 0);
    const avgPnl = completed.length > 0 ? completed.reduce((s, t) => s + (t.pnl ?? 0), 0) / completed.length : 0;

    // Max drawdown from daily losses
    const maxDrawdown = Math.max(0, ...this.wallets.map(w => Math.abs(w.daily_loss) / w.initial_capital * 100));

    return {
      totalEquity, totalPnl, totalPnlPct, winRate,
      totalCompleted: completed.length, winners: winners.length,
      profitFactor, avgPnl, maxDrawdown,
    };
  }

  // ─── Render ──────────────────────────────────────────────────────────────

  private render(): void {
    this.container.innerHTML = `
      <div class="portfolio-wrap">
        <div class="paper-mode-banner">KAĞIT İŞLEM MODU - Bu emirler gerçek piyasaya gönderilmemektedir. Cüzdan sonuçları test/paper işlem kayıtlarından hesaplanır.</div>

        <!-- Metrics Summary -->
        <div class="paper-metrics-summary" id="paper-metrics-summary"></div>

        <!-- Wallets -->
        <div class="paper-section">
          <h2 class="paper-title">${TR.WALLETS}</h2>
          <div id="paper-wallets" class="paper-wallets-grid"></div>
        </div>

        <!-- Charts Row -->
        <div class="paper-charts-row">
          <div class="panel-section paper-chart-half">
            <h3>${TR.EQUITY_CURVE}</h3>
            <div class="paper-chart-wrap"><canvas id="paper-equity-canvas"></canvas></div>
          </div>
          <div class="panel-section paper-chart-half">
            <h3>Drawdown</h3>
            <div class="paper-chart-wrap"><canvas id="paper-drawdown-canvas"></canvas></div>
          </div>
        </div>

        <!-- Trade History -->
        <div class="paper-section">
          <div class="panel-title-row">
            <h2 class="paper-title">${TR.TRADE_HISTORY}</h2>
            <button class="btn-sm" id="export-trades-btn" title="İşlemleri CSV olarak indir">⤓ CSV</button>
          </div>
          <div id="paper-trades"></div>
        </div>

      </div>
    `;

    this.renderWallets();
    this.renderMetrics();
    this.renderTrades();

    const exportBtn = this.container.querySelector<HTMLButtonElement>('#export-trades-btn');
    if (exportBtn) {
      exportBtn.addEventListener('click', () => {
        const sid = this.selectedStrategy || this.wallets[0]?.strategy_id || '';
        const url = sid
          ? `/api/paper/trades/export?strategy_id=${encodeURIComponent(sid)}`
          : '/api/paper/trades/export';
        window.open(url, '_blank');
      });
    }
  }

  private renderMetrics(): void {
    const el = this.container.querySelector('#paper-metrics-summary');
    if (!el) return;

    const m = this.computeMetrics();

    const card = (label: string, value: string, cls = '') =>
      `<div class="summary-card"><div class="sc-label">${label}</div><div class="sc-value ${cls}">${value}</div></div>`;

    el.innerHTML = [
      card(TR.EQUITY, formatCurrency(m.totalEquity), ''),
      card(TR.TOTAL_PNL, formatCurrency(m.totalPnl), m.totalPnl >= 0 ? 'pos' : 'neg'),
      card(TR.WIN_RATE, m.totalCompleted > 0 ? `${formatPct(m.winRate)} (${m.winners}/${m.totalCompleted})` : '—'),
      card(TR.PROFIT_FACTOR, isFinite(m.profitFactor) ? formatNumber(m.profitFactor, 2) : '∞', m.profitFactor >= 1 ? 'pos' : 'neg'),
      card(TR.MAX_DRAWDOWN, formatPct(-m.maxDrawdown), 'neg'),
      card('Ort. K/Z', formatCurrency(m.avgPnl), m.avgPnl >= 0 ? 'pos' : 'neg'),
    ].join('');
  }

  private renderWallets(): void {
    const el = this.container.querySelector('#paper-wallets');
    if (!el) return;

    if (this.wallets.length === 0) {
      el.innerHTML = `<div class="empty-state">${TR.NO_WALLETS}</div>`;
      return;
    }

    el.innerHTML = this.wallets.map(w => this.walletCardHTML(w)).join('');

    // Butonlar
    el.querySelectorAll<HTMLButtonElement>('.btn-reset-wallet').forEach(btn => {
      btn.addEventListener('click', () => void this.resetWallet(btn.dataset['strategyId']!));
    });
    el.querySelectorAll<HTMLButtonElement>('.btn-halt-wallet').forEach(btn => {
      btn.addEventListener('click', () => void this.haltWallet(btn.dataset['strategyId']!));
    });
    el.querySelectorAll<HTMLButtonElement>('.btn-resume-wallet').forEach(btn => {
      btn.addEventListener('click', () => void this.resumeWallet(btn.dataset['strategyId']!));
    });
    // Equity curve seçimi
    el.querySelectorAll<HTMLElement>('.wallet-card').forEach(card => {
      card.addEventListener('click', () => {
        const sid = card.dataset['strategyId'];
        if (sid) {
          this.selectedStrategy = sid;
          el.querySelectorAll('.wallet-card').forEach(c => c.classList.remove('selected'));
          card.classList.add('selected');
          void this.fetchEquityCurve(sid);
        }
      });
    });
  }

  private walletCardHTML(w: PaperWallet): string {
    const pnl = w.cash - w.initial_capital;
    const pnlPct = (pnl / w.initial_capital) * 100;
    const haltedBadge = w.is_halted
      ? `<span class="wallet-halted-badge">${TR.WALLET_HALTED}</span>`
      : '';
    const dailyLoss = w.daily_loss;
    // Yüzde hesabı yönlü olmalı: negatif kayıp, pozitif kazanç
    const dailyLossPct = (dailyLoss / w.initial_capital) * 100;
    const isSelected = w.strategy_id === this.selectedStrategy;

    return `
      <div class="wallet-card ${w.is_halted ? 'wallet-halted' : ''} ${isSelected ? 'selected' : ''}" data-strategy-id="${w.strategy_id}">
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
            <span class="wm-value ${dailyLoss >= 0 ? 'pos' : 'neg'}">${formatCurrency(dailyLoss)} (${formatPct(dailyLossPct)})</span>
          </div>
        </div>
        <div class="wallet-actions">
          ${w.is_halted
            ? `<button class="btn-sm btn-secondary btn-resume-wallet" data-strategy-id="${w.strategy_id}">Devam Et</button>`
            : `<button class="btn-sm btn-danger btn-halt-wallet" data-strategy-id="${w.strategy_id}">Dondur</button>`
          }
          <button class="btn-sm btn-secondary btn-reset-wallet" data-strategy-id="${w.strategy_id}">${TR.RESET_WALLET}</button>
        </div>
      </div>
    `;
  }

  // ─── Equity Curve + Drawdown Charts ──────────────────────────────────────

  private renderEquityCurve(points: EquityPoint[]): void {
    if (points.length === 0) return;

    const labels = points.map(p => {
      const d = new Date(p.ts);
      return d.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
    });
    const equityData = points.map(p => p.total_equity);

    // Drawdown hesapla
    let peak = equityData[0]!;
    const drawdownData = equityData.map(eq => {
      if (eq > peak) peak = eq;
      return peak > 0 ? ((eq - peak) / peak) * 100 : 0;
    });

    // Equity Chart
    const eqCanvas = this.container.querySelector<HTMLCanvasElement>('#paper-equity-canvas');
    if (eqCanvas) {
      if (this.equityChart) {
        this.equityChart.data.labels = labels;
        this.equityChart.data.datasets[0]!.data = equityData;
        this.equityChart.update('none');
      } else {
        this.equityChart = new Chart(eqCanvas, {
          type: 'line',
          data: {
            labels,
            datasets: [{
              label: TR.EQUITY_CURVE,
              data: equityData,
              borderColor: '#3fb950',
              backgroundColor: '#3fb95015',
              borderWidth: 2,
              pointRadius: 0,
              fill: true,
              tension: 0.1,
            }],
          },
          options: {
            animation: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { display: false },
              y: {
                ticks: { color: '#8b949e', font: { size: 10 } },
                grid: { color: '#21262d' },
              },
            },
            responsive: true,
            maintainAspectRatio: false,
          },
        });
      }
    }

    // Drawdown Chart
    const ddCanvas = this.container.querySelector<HTMLCanvasElement>('#paper-drawdown-canvas');
    if (ddCanvas) {
      if (this.drawdownChart) {
        this.drawdownChart.data.labels = labels;
        this.drawdownChart.data.datasets[0]!.data = drawdownData;
        this.drawdownChart.update('none');
      } else {
        this.drawdownChart = new Chart(ddCanvas, {
          type: 'line',
          data: {
            labels,
            datasets: [{
              label: 'Drawdown %',
              data: drawdownData,
              borderColor: '#f85149',
              backgroundColor: '#f8514915',
              borderWidth: 2,
              pointRadius: 0,
              fill: true,
              tension: 0.1,
            }],
          },
          options: {
            animation: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { display: false },
              y: {
                ticks: { color: '#8b949e', font: { size: 10 }, callback: v => `${v}%` },
                grid: { color: '#21262d' },
                max: 0,
              },
            },
            responsive: true,
            maintainAspectRatio: false,
          },
        });
      }
    }
  }

  // ─── Trade History ──────────────────────────────────────────────────────

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
