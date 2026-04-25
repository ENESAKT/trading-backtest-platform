import Chart from 'chart.js/auto';
import type { OHLCV, Signal, BacktestResult } from '../types.js';
import type { StrategyId } from '../strategies/index.js';
import { generateSignals, runBacktestById } from '../strategies/index.js';
import { computeIndicators } from '../indicators/index.js';
import { TR, formatNumber, formatPct, formatDateTime } from '../constants/tr.js';

interface StrategyCard {
  id: StrategyId;
  nameKey: string;
  descKey: string;
}

const STRATEGIES: StrategyCard[] = [
  { id: 'trend',    nameKey: 'STRATEGY_TREND',    descKey: 'STRATEGY_DESC_TREND'    },
  { id: 'mean',     nameKey: 'STRATEGY_MEAN',     descKey: 'STRATEGY_DESC_MEAN'     },
  { id: 'breakout', nameKey: 'STRATEGY_BREAKOUT', descKey: 'STRATEGY_DESC_BREAKOUT' },
];

// ─── StrategyPanel ────────────────────────────────────────────────────────────

export class StrategyPanel {
  private container: HTMLElement;
  private activeStrategy: StrategyId = 'trend';
  private candles: OHLCV[] = [];
  private equityChart: Chart | null = null;

  constructor(container: HTMLElement) {
    this.container = container;
    this.render();
  }

  // ─── Data update ────────────────────────────────────────────────────────

  setCandles(candles: OHLCV[]): void {
    this.candles = candles;
    this.runAnalysis();
  }

  // ─── Render ─────────────────────────────────────────────────────────────

  private render(): void {
    this.container.innerHTML = `
      <div class="strategy-wrap">

        <!-- Strategy selector cards -->
        <div class="strategy-cards" id="strategy-cards">
          ${STRATEGIES.map(s => this.strategyCardHTML(s)).join('')}
        </div>

        <!-- Metrics + Signals -->
        <div class="strategy-body">
          <div class="strategy-left">
            <div class="panel-section">
              <h3 id="metrics-title">${TR[STRATEGIES[0]!.nameKey as keyof typeof TR]} — ${TR.RETURN}</h3>
              <div id="backtest-metrics" class="metrics-grid"></div>
            </div>
            <div class="panel-section">
              <h3>${TR.SIGNALS}</h3>
              <div id="signals-list"></div>
            </div>
          </div>
          <div class="strategy-right">
            <div class="panel-section">
              <h3>${TR.EQUITY_CURVE}</h3>
              <div class="equity-wrap"><canvas id="equity-canvas"></canvas></div>
            </div>
          </div>
        </div>

      </div>
    `;

    this.bindCards();
  }

  private strategyCardHTML(s: StrategyCard): string {
    return `
      <div class="strategy-card${s.id === this.activeStrategy ? ' active' : ''}" data-strategy="${s.id}">
        <div class="sc-name">${TR[s.nameKey as keyof typeof TR]}</div>
        <div class="sc-desc">${TR[s.descKey as keyof typeof TR]}</div>
      </div>
    `;
  }

  private bindCards(): void {
    const cardsEl = this.container.querySelector('#strategy-cards')!;
    cardsEl.addEventListener('click', (e) => {
      const card = (e.target as HTMLElement).closest<HTMLElement>('[data-strategy]');
      if (!card) return;
      this.activeStrategy = card.dataset['strategy'] as StrategyId;
      cardsEl.querySelectorAll('.strategy-card').forEach(c =>
        c.classList.toggle('active', (c as HTMLElement).dataset['strategy'] === this.activeStrategy)
      );
      this.runAnalysis();
    });
  }

  // ─── Analysis ───────────────────────────────────────────────────────────

  private runAnalysis(): void {
    if (this.candles.length < 30) {
      this.showEmpty();
      return;
    }

    const metricsEl = this.container.querySelector('#backtest-metrics');
    if (metricsEl) metricsEl.innerHTML = `<div class="loading">${TR.RUNNING_BACKTEST}</div>`;

    // Defer to next tick to allow loading state to render
    requestAnimationFrame(() => {
      try {
        const inds    = computeIndicators(this.candles);
        const signals = generateSignals(this.activeStrategy, this.candles, inds);
        const result  = runBacktestById(this.activeStrategy, this.candles);

        this.renderMetrics(result);
        this.renderSignals(signals);
        this.renderEquityCurve(result);
      } catch {
        this.showEmpty();
      }
    });
  }

  private showEmpty(): void {
    const metricsEl = this.container.querySelector('#backtest-metrics');
    const signalsEl = this.container.querySelector('#signals-list');
    if (metricsEl) metricsEl.innerHTML = `<div class="empty-state">${TR.WAITING_DATA}</div>`;
    if (signalsEl) signalsEl.innerHTML = `<div class="empty-state">${TR.NO_SIGNALS}</div>`;
  }

  private renderMetrics(r: BacktestResult): void {
    const el = this.container.querySelector('#backtest-metrics');
    if (!el) return;

    const metric = (label: string, value: string, cls = '') =>
      `<div class="metric-card"><div class="metric-label">${label}</div><div class="metric-value ${cls}">${value}</div></div>`;

    el.innerHTML = [
      metric(TR.RETURN,       formatPct(r.totalReturn),         r.totalReturn >= 0 ? 'pos' : 'neg'),
      metric(TR.SHARPE,       formatNumber(r.sharpeRatio, 2)),
      metric(TR.MAX_DRAWDOWN, formatPct(-r.maxDrawdown),        'neg'),
      metric(TR.WIN_RATE,     formatPct(r.winRate)),
      metric(TR.TOTAL_TRADES, String(r.totalTrades)),
      metric(TR.PROFIT_FACTOR, formatNumber(r.profitFactor, 2), r.profitFactor >= 1 ? 'pos' : 'neg'),
    ].join('');
  }

  private renderSignals(signals: Signal[]): void {
    const el = this.container.querySelector('#signals-list');
    if (!el) return;

    if (signals.length === 0) {
      el.innerHTML = `<div class="empty-state">${TR.NO_SIGNALS}</div>`;
      return;
    }

    // Show last 10 signals, most recent first
    const recent = [...signals].reverse().slice(0, 10);

    el.innerHTML = recent.map(s => `
      <div class="signal-item ${s.type.toLowerCase()}">
        <div class="signal-header">
          <span class="signal-badge ${s.type === 'BUY' ? 'badge-buy' : 'badge-sell'}">
            ${s.type === 'BUY' ? TR.SIGNAL_BUY : TR.SIGNAL_SELL}
          </span>
          <span class="signal-price">${formatNumber(s.price)}</span>
          <span class="signal-time">${formatDateTime(s.timestamp)}</span>
          <div class="signal-strength" title="Güç: ${s.strength}/10">
            ${'▮'.repeat(s.strength)}${'▯'.repeat(10 - s.strength)}
          </div>
        </div>
        <div class="signal-reason">${s.reason}</div>
      </div>
    `).join('');
  }

  private renderEquityCurve(result: BacktestResult): void {
    const canvas = this.container.querySelector<HTMLCanvasElement>('#equity-canvas');
    if (!canvas || result.equityCurve.length === 0) return;

    const labels = result.equityCurve.map(p => formatDateTime(p.time));
    const data   = result.equityCurve.map(p => p.value);

    const maxStep = 200;
    const step    = Math.max(1, Math.floor(labels.length / maxStep));
    const sampledLabels = labels.filter((_, i) => i % step === 0);
    const sampledData   = data.filter((_, i) => i % step === 0);

    if (this.equityChart) {
      this.equityChart.data.labels = sampledLabels;
      this.equityChart.data.datasets[0]!.data = sampledData;
      this.equityChart.update('none');
      return;
    }

    this.equityChart = new Chart(canvas, {
      type: 'line',
      data: {
        labels: sampledLabels,
        datasets: [{
          label: TR.EQUITY_CURVE,
          data: sampledData,
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
            grid:  { color: '#21262d' },
          },
        },
        responsive: true,
        maintainAspectRatio: false,
      },
    });
  }

  // ─── Cleanup ─────────────────────────────────────────────────────────────

  destroy(): void {
    this.equityChart?.destroy();
  }
}
