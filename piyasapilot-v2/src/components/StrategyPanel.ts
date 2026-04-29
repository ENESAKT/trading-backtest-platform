import Chart from 'chart.js/auto';
import type { OHLCV, Signal, BacktestResult, BacktestTrade, Timeframe } from '../types.js';
import { TR, formatNumber, formatPct, formatDateTime } from '../constants/tr.js';

// Backend ``POST /api/backtest/run`` endpoint'i. Sprint 3.4 — TS-içi
// ``runBacktestById``/``generateSignals`` sökündü; tüm metrikler ve
// equity eğrisi Python ``BacktestEngine``'den gelir, marker'lar
// signals[] üzerinden ChartPanel'e fan-out edilir.

const BACKTEST_RUN_ENDPOINT = '/api/backtest/run';
const BACKTEST_TIMEOUT_MS = 30_000;
const MIN_BARS_FOR_RUN = 50;

// Sabit liste — backend ``backend/backtest/blueprints.py`` ile birebir
// senkron. ``GET /api/backtest/strategies`` ile dinamik fetch ileride
// (parametre formu eklendiğinde) yapılır; şimdilik kart UI yeterli.
type StrategyId =
  | 'sma_crossover'
  | 'rsi_reversion'
  | 'bollinger_reversion'
  | 'buy_and_hold'
  | 'donchian_breakout'
  | 'macd_divergence'
  | 'supertrend'
  | 'mean_reversion_vwap';

interface StrategyCard {
  id: StrategyId;
  nameKey: string;
  descKey: string;
}

const STRATEGIES: StrategyCard[] = [
  { id: 'sma_crossover',       nameKey: 'STRATEGY_TREND',      descKey: 'STRATEGY_DESC_TREND'      },
  { id: 'rsi_reversion',       nameKey: 'STRATEGY_MEAN',       descKey: 'STRATEGY_DESC_MEAN'       },
  { id: 'bollinger_reversion', nameKey: 'STRATEGY_BREAKOUT',   descKey: 'STRATEGY_DESC_BREAKOUT'   },
  { id: 'donchian_breakout',   nameKey: 'STRATEGY_DONCHIAN',   descKey: 'STRATEGY_DESC_DONCHIAN'   },
  { id: 'macd_divergence',     nameKey: 'STRATEGY_MACD',       descKey: 'STRATEGY_DESC_MACD'       },
  { id: 'supertrend',          nameKey: 'STRATEGY_SUPERTREND', descKey: 'STRATEGY_DESC_SUPERTREND' },
  { id: 'mean_reversion_vwap', nameKey: 'STRATEGY_VWAP',       descKey: 'STRATEGY_DESC_VWAP'       },
];

// ─── StrategyPanel ────────────────────────────────────────────────────────────

type SignalsListener = (signals: Signal[]) => void;

export class StrategyPanel {
  private container: HTMLElement;
  private activeStrategy: StrategyId = 'sma_crossover';
  private candles: OHLCV[] = [];
  private activeSymbol = '';
  private activeInterval: Timeframe = '1d';
  private equityChart: Chart | null = null;
  private signalListeners: Set<SignalsListener> = new Set();
  private lastSignals: Signal[] = [];
  private lastRunKey = '';
  private runInFlight = false;

  constructor(container: HTMLElement) {
    this.container = container;
    this.render();
  }

  // ─── Data update ────────────────────────────────────────────────────────

  setCandles(candles: OHLCV[], symbol?: string, interval?: Timeframe): void {
    this.candles = candles;
    if (symbol)   this.activeSymbol = symbol;
    if (interval) this.activeInterval = interval;

    // Aynı sembol+strateji için tick güncellemelerinde re-run yapma —
    // backend POST'u her tick'te tetiklemek istemiyoruz.
    const key = `${this.activeSymbol}|${this.activeInterval}|${this.activeStrategy}`;
    if (key === this.lastRunKey) return;
    this.lastRunKey = key;
    void this.runAnalysis();
  }

  // ─── Sinyal yayını (chart üstünde marker çizmek için) ──────────────────

  onSignalsUpdate(listener: SignalsListener): () => void {
    this.signalListeners.add(listener);
    listener(this.lastSignals);
    return () => this.signalListeners.delete(listener);
  }

  private emitSignals(signals: Signal[]): void {
    this.lastSignals = signals;
    this.signalListeners.forEach(l => l(signals));
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
      // Strateji değişti — re-run zorla.
      this.lastRunKey = '';
      void this.runAnalysis();
    });
  }

  // ─── Analysis (backend POST) ─────────────────────────────────────────────

  private async runAnalysis(): Promise<void> {
    if (this.runInFlight) return;
    if (this.candles.length < MIN_BARS_FOR_RUN || !this.activeSymbol) {
      this.showEmpty();
      return;
    }

    const metricsEl = this.container.querySelector('#backtest-metrics');
    if (metricsEl) metricsEl.innerHTML = `<div class="loading">${TR.RUNNING_BACKTEST}</div>`;

    this.runInFlight = true;
    try {
      const result = await this.fetchBacktest();
      this.renderMetrics(result);
      this.renderSignals(result.signals);
      this.renderEquityCurve(result);
      this.emitSignals(result.signals);
    } catch (err) {
      this.showError(err instanceof Error ? err.message : String(err));
    } finally {
      this.runInFlight = false;
    }
  }

  private async fetchBacktest(): Promise<BacktestResult> {
    const resp = await fetch(BACKTEST_RUN_ENDPOINT, {
      method:  'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        symbol:        this.activeSymbol,
        interval:      this.activeInterval,
        strategy_id:   this.activeStrategy,
        params:        {},
        capital:       100_000,
        lookback_bars: Math.min(this.candles.length, 1000),
      }),
      signal: AbortSignal.timeout(BACKTEST_TIMEOUT_MS),
    });

    if (!resp.ok) {
      let detail = `HTTP ${resp.status}`;
      try {
        const errorBody = (await resp.json()) as { detail?: string };
        if (errorBody.detail) detail = errorBody.detail;
      } catch {
        // ignore — detail HTTP status'ta kalır
      }
      throw new Error(detail);
    }

    return await resp.json() as BacktestResult;
  }

  private showEmpty(): void {
    const metricsEl = this.container.querySelector('#backtest-metrics');
    const signalsEl = this.container.querySelector('#signals-list');
    if (metricsEl) metricsEl.innerHTML = `<div class="empty-state">${TR.WAITING_DATA}</div>`;
    if (signalsEl) signalsEl.innerHTML = `<div class="empty-state">${TR.NO_SIGNALS}</div>`;
    this.emitSignals([]);
  }

  private showError(message: string): void {
    const metricsEl = this.container.querySelector('#backtest-metrics');
    const signalsEl = this.container.querySelector('#signals-list');
    if (metricsEl) metricsEl.innerHTML = `<div class="empty-state error">${message}</div>`;
    if (signalsEl) signalsEl.innerHTML = `<div class="empty-state">${TR.NO_SIGNALS}</div>`;
    this.emitSignals([]);
  }

  // ─── Render: metrics / signals / equity curve ────────────────────────────

  private profitFactor(trades: BacktestTrade[]): number {
    let gross = 0;
    let loss = 0;
    for (const t of trades) {
      if (t.net_pnl > 0) gross += t.net_pnl;
      else loss += Math.abs(t.net_pnl);
    }
    if (loss === 0) return gross > 0 ? Infinity : 0;
    return gross / loss;
  }

  private renderMetrics(r: BacktestResult): void {
    const el = this.container.querySelector('#backtest-metrics');
    if (!el) return;

    const m = r.metrics;
    const pf = this.profitFactor(r.trades);

    const metric = (label: string, value: string, cls = '') =>
      `<div class="metric-card"><div class="metric-label">${label}</div><div class="metric-value ${cls}">${value}</div></div>`;

    el.innerHTML = [
      metric(TR.RETURN,       formatPct(m.total_return_pct),       m.total_return_pct >= 0 ? 'pos' : 'neg'),
      metric(TR.SHARPE,       formatNumber(m.sharpe_ratio, 2)),
      metric(TR.MAX_DRAWDOWN, formatPct(-m.max_drawdown_pct),      'neg'),
      metric(TR.WIN_RATE,     formatPct(m.win_rate)),
      metric(TR.TOTAL_TRADES, String(m.total_trades)),
      metric(TR.PROFIT_FACTOR, isFinite(pf) ? formatNumber(pf, 2) : '∞', pf >= 1 ? 'pos' : 'neg'),
    ].join('');
  }

  private renderSignals(signals: Signal[]): void {
    const el = this.container.querySelector('#signals-list');
    if (!el) return;

    if (signals.length === 0) {
      el.innerHTML = `<div class="empty-state">${TR.NO_SIGNALS}</div>`;
      return;
    }

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
    if (!canvas || result.equity_curve.length === 0) return;

    const labels = result.equity_curve.map(p => formatDateTime(p.time));
    const data   = result.equity_curve.map(p => p.total_equity);

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
