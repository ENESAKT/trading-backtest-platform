import Chart from 'chart.js/auto';
import type {
  BacktestResult,
  BacktestTrade,
  OHLCV,
  Signal,
  StrategyBlueprint,
  StrategyPreset,
  StrategySpec,
  SymbolInfo,
  Timeframe,
} from '../types.js';
import {
  TR,
  formatCurrency,
  formatDateTime,
  formatNumber,
  formatPct,
} from '../constants/tr.js';
import { ALL_SYMBOLS, DEFAULT_SYMBOL, resolveSymbol } from '../constants/symbols.js';

const BACKTEST_RUN_ENDPOINT = '/api/backtest/run';
const BACKTEST_STRATEGIES_ENDPOINT = '/api/backtest/strategies';
const BACKTEST_REPORTS_ENDPOINT = '/api/backtest/reports';
const BACKTEST_OPTIMIZE_ENDPOINT = '/api/backtest/optimize';
const BACKTEST_SCAN_ENDPOINT = '/api/backtest/scan';
const STRATEGY_STORE_ENDPOINT = '/api/strategy-lab/strategies';
const BACKTEST_TIMEOUT_MS = 30_000;
const MIN_BARS_FOR_RUN = 50;

type SignalsListener = (signals: Signal[]) => void;
type FocusListener = (timestamp: number) => void;
type SymbolSelectListener = (info: SymbolInfo) => void;
type StrategyMode = 'blueprint' | 'spec' | 'preset';
type ReportTab = 'summary' | 'trades' | 'performance' | 'system' | 'warnings';

interface SavedStrategy {
  id: number;
  name: string;
  symbol: string;
  timeframe: string;
  notes: string;
  created_at: string;
  strategy_spec?: StrategySpec | null;
  settings?: Record<string, unknown>;
}

interface ReportSummary {
  id: string;
  created_at: string;
  symbol: string;
  interval: string;
  strategy_name: string;
  final_equity: number;
  return_pct: number;
}

interface OptimizationRow {
  params: Record<string, unknown>;
  metrics: BacktestResult['metrics'];
  score: number;
  warnings: string[];
}

interface OptimizationStabilityReport {
  param_keys: string[];
  best_params: Record<string, unknown>;
  stable_score: number;
  metric_value: number;
  global_max: number;
  warnings: string[];
}

interface ScanRow {
  symbol: string;
  last_price?: number;
  last_signal?: Signal | null;
  total_return_pct: number;
  max_drawdown_pct: number;
  total_trades: number;
  score: number;
}

const DEFAULT_STRATEGIES: StrategyBlueprint[] = [
  {
    id: 'sma_crossover',
    label: 'SMA Crossover',
    description: 'Çift hareketli ortalama kesişimi.',
    default_params: { fast_period: 10, slow_period: 30 },
    schema: [],
  },
  {
    id: 'rsi_reversion',
    label: 'RSI Mean-Reversion',
    description: 'Aşırı bölgeden ortalamaya dönüş.',
    default_params: { rsi_period: 14, oversold: 30, overbought: 70 },
    schema: [],
  },
  {
    id: 'buy_and_hold',
    label: 'Buy & Hold',
    description: 'Pasif kıyas.',
    default_params: {},
    schema: [],
  },
  {
    id: 'bollinger_reversion',
    label: 'Bollinger Bands Reversion',
    description: 'Bant dışına taşan fiyatın orta banda dönüşü.',
    default_params: { period: 20, std_dev: 2 },
    schema: [],
  },
  {
    id: 'macd_divergence',
    label: 'MACD Kesişimi',
    description: 'MACD histogramı sıfır çizgisini geçtiğinde işlem.',
    default_params: { fast_period: 12, slow_period: 26, signal_period: 9 },
    schema: [],
  },
  {
    id: 'supertrend',
    label: 'Supertrend',
    description: 'ATR tabanlı trend yönü.',
    default_params: { period: 10, multiplier: 3 },
    schema: [],
  },
];

const EXAMPLES: Record<string, Partial<StrategySpec>> = {
  rsiTrend: {
    name: 'RSI + EMA Trend',
    rules: {
      long_entry: 'CROSS_UP(RSI(C,14), 30) AND C > EMA(C,200)',
      long_exit: 'RSI(C,14) > 70 OR C < EMA(C,50)',
      short_entry: '',
      short_exit: '',
    },
    risk: { stop_loss_pct: 3, take_profit_pct: 8, trailing_stop_pct: 5 },
  },
  emaCross: {
    name: 'EMA 50/200',
    rules: {
      long_entry: 'CROSS_UP(EMA(C,50), EMA(C,200))',
      long_exit: 'CROSS_DOWN(EMA(C,50), EMA(C,200))',
      short_entry: 'CROSS_DOWN(EMA(C,50), EMA(C,200))',
      short_exit: 'CROSS_UP(EMA(C,50), EMA(C,200))',
    },
    risk: { stop_loss_pct: 3, take_profit_pct: 8, trailing_stop_pct: 5 },
  },
  shortRsi: {
    name: 'Short RSI Dönüş',
    rules: {
      long_entry: '',
      long_exit: '',
      short_entry: 'C < EMA(C,200) AND CROSS_DOWN(RSI(C,14), 70)',
      short_exit: 'RSI(C,14) < 40 OR C > EMA(C,50)',
    },
    risk: { stop_loss_pct: 3, take_profit_pct: 8, trailing_stop_pct: 5 },
  },
};

export class StrategyPanel {
  private container: HTMLElement;
  private mode: StrategyMode = 'spec';
  private reportTab: ReportTab = 'summary';
  private blueprints: StrategyBlueprint[] = DEFAULT_STRATEGIES;
  private presets: StrategyPreset[] = [];
  private activeStrategy = 'sma_crossover';
  private candles: OHLCV[] = [];
  private activeSymbol = DEFAULT_SYMBOL.symbol;
  private activeInterval: Timeframe = '1d';
  private equityChart: Chart | null = null;
  private signalListeners: Set<SignalsListener> = new Set();
  private focusListeners: Set<FocusListener> = new Set();
  private symbolSelectListeners: Set<SymbolSelectListener> = new Set();
  private lastSignals: Signal[] = [];
  private lastRunKey = '';
  private runInFlight = false;
  private rerunRequested = false;
  private lastResult: BacktestResult | null = null;
  private savedStrategies: SavedStrategy[] = [];
  private reportSummaries: ReportSummary[] = [];
  private optimizationRows: OptimizationRow[] = [];
  private optimizationStability: OptimizationStabilityReport | null = null;
  private scanRows: ScanRow[] = [];

  constructor(container: HTMLElement) {
    this.container = container;
    this.render();
    void this.loadBlueprints();
    void this.loadSavedStrategies();
    void this.loadReports();
  }

  setCandles(candles: OHLCV[], symbol?: string, interval?: Timeframe): void {
    this.candles = candles;
    if (symbol) this.activeSymbol = symbol;
    if (interval) this.activeInterval = interval;

    const key = `${this.activeSymbol}|${this.activeInterval}|${this.mode}|${this.activeStrategy}`;
    if (key === this.lastRunKey) return;
    this.lastRunKey = key;
    void this.runAnalysis();
  }

  onSignalsUpdate(listener: SignalsListener): () => void {
    this.signalListeners.add(listener);
    listener(this.lastSignals);
    return () => this.signalListeners.delete(listener);
  }

  onFocusTime(listener: FocusListener): () => void {
    this.focusListeners.add(listener);
    return () => this.focusListeners.delete(listener);
  }

  onSymbolSelect(listener: SymbolSelectListener): () => void {
    this.symbolSelectListeners.add(listener);
    return () => this.symbolSelectListeners.delete(listener);
  }

  openBlueprint(strategyId: string): void {
    if (!strategyId.trim()) return;
    if (!this.blueprints.some(strategy => strategy.id === strategyId)) {
      this.showError(`${strategyId} preset'i bu oturumda yüklenmedi.`);
      return;
    }
    this.mode = 'blueprint';
    this.activeStrategy = strategyId;
    this.renderStrategyCards();
    this.syncControls();
    this.lastRunKey = '';
    void this.runAnalysis();
  }

  private emitSignals(signals: Signal[]): void {
    this.lastSignals = signals;
    this.signalListeners.forEach(l => l(signals));
  }

  private emitFocus(timestamp: number): void {
    this.focusListeners.forEach(l => l(timestamp));
  }

  private emitSymbolSelect(symbol: string): void {
    const info = resolveSymbol(symbol);
    if (!info) {
      this.showError(`${symbol} sembol listesinde bulunamadı.`);
      return;
    }
    this.symbolSelectListeners.forEach(l => l(info));
  }

  private async loadBlueprints(): Promise<void> {
    try {
      const resp = await fetch(BACKTEST_STRATEGIES_ENDPOINT);
      if (!resp.ok) return;
      const body = await resp.json() as {
        strategies?: StrategyBlueprint[];
        presets?: StrategyPreset[];
      };
      let changed = false;
      if (body.strategies?.length) {
        this.blueprints = body.strategies;
        changed = true;
      }
      if (body.presets?.length) {
        this.presets = body.presets;
        changed = true;
      }
      if (changed) {
        this.renderStrategyCards();
      }
    } catch {
      // Static fallback stays in place.
    }
  }

  private async loadSavedStrategies(): Promise<void> {
    try {
      const resp = await fetch(STRATEGY_STORE_ENDPOINT);
      if (!resp.ok) return;
      const body = await resp.json() as { strategies?: SavedStrategy[] };
      this.savedStrategies = body.strategies ?? [];
      this.renderSavedStrategies();
    } catch {
      // Optional panel remains empty.
    }
  }

  private async loadReports(): Promise<void> {
    try {
      const resp = await fetch(`${BACKTEST_REPORTS_ENDPOINT}?limit=8`);
      if (!resp.ok) return;
      const body = await resp.json() as { reports?: ReportSummary[] };
      this.reportSummaries = body.reports ?? [];
      this.renderReportArchive();
    } catch {
      // Optional panel remains empty.
    }
  }

  private render(): void {
    this.container.innerHTML = `
      <div class="strategy-wrap">
        <div class="strategy-topline">
          <div class="segmented">
            <button class="seg-btn" data-mode="spec">Kural Lab</button>
            <button class="seg-btn" data-mode="preset">Katalog (Hazır)</button>
            <button class="seg-btn" data-mode="blueprint">Eski Blueprintler</button>
          </div>
          <div class="topline-actions">
            <button class="btn-secondary" id="save-strategy">Kaydet</button>
            <button class="btn-secondary" id="activate-paper">Paper'a Al</button>
            <button class="btn-primary" id="run-backtest">Çalıştır</button>
          </div>
        </div>

        <div class="strategy-controls">
          <label>Sembol<input id="bt-symbol" type="text" readonly></label>
          <label>Periyot<select id="bt-interval">
            ${['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'].map(tf =>
              `<option value="${tf}">${tf}</option>`
            ).join('')}
          </select></label>
          <label>Başlangıç<input id="bt-start" type="date"></label>
          <label>Bitiş<input id="bt-end" type="date"></label>
          <label>Sermaye<input id="bt-capital" type="number" min="1000" step="1000" value="100000"></label>
          <label>Komisyon %<input id="bt-commission" type="number" min="0" max="10" step="0.01" value="0.10"></label>
          <label>Slippage Modeli<select id="bt-slippage-model">
            <option value="fixed_bps">Fixed BPS</option>
            <option value="fixed_tick">Fixed Tick</option>
          </select></label>
          <label>Slippage bps<input id="bt-slippage" type="number" min="0" max="500" step="1" value="5"></label>
          <label>Slippage Tick<input id="bt-slippage-tick" type="number" min="0" step="0.01" value="0.01"></label>
          <label>Likidite %<input id="bt-volume-limit-pct" type="number" min="0" max="100" step="1" value="5"></label>
          <label>Likidite Penceresi<input id="bt-volume-window" type="number" min="1" max="100" step="1" value="5"></label>
          <label>Pozisyon %<input id="bt-maxpos" type="number" min="1" max="100" step="1" value="20"></label>
          <label>Kaynak<select id="bt-source">
            <option value="cache_only">Cache</option>
            <option value="cache_then_provider">Cache + Provider</option>
            <option value="csv_import">CSV</option>
          </select></label>
          <label class="check-label"><input id="bt-allow-short" type="checkbox"> Short</label>
        </div>

        <div class="csv-import" id="csv-import" hidden>
          <textarea id="csv-text" spellcheck="false" placeholder="time,open,high,low,close,volume"></textarea>
        </div>

        <div id="blueprint-editor" class="strategy-editor"></div>
        <div id="preset-cards" class="strategy-editor"></div>
        <div id="spec-editor" class="strategy-editor"></div>

        <div class="lab-secondary">
          <div class="lab-panel">
            <div class="panel-title-row">
              <h3>Kayıtlı Stratejiler</h3>
              <button class="btn-sm" id="refresh-saved">Yenile</button>
            </div>
            <div id="saved-strategies" class="compact-list"></div>
          </div>
          <div class="lab-panel">
            <div class="panel-title-row">
              <h3>Rapor Arşivi</h3>
              <button class="btn-sm" id="refresh-reports">Yenile</button>
            </div>
            <div id="report-archive" class="compact-list"></div>
          </div>
          <div class="lab-panel">
            <h3>Parametre Deneyi</h3>
            <div class="optimizer-grid">
              <label>Hızlı EMA<input id="opt-fast" type="text" value="10,20,30,50"></label>
              <label>Yavaş EMA<input id="opt-slow" type="text" value="100,150,200"></label>
              <button class="btn-secondary" id="run-optimizer">Dene</button>
              <button class="btn-secondary" id="export-optimizer">CSV</button>
            </div>
            <div id="optimizer-results" class="compact-list"></div>
          </div>
          <div class="lab-panel">
            <h3>Piyasa Taraması</h3>
            <div class="optimizer-grid">
              <label>Liste<select id="scan-group">
                <option value="Kripto">Kripto</option>
                <option value="BIST 30">BIST 30</option>
                <option value="BIST 100">BIST 100</option>
                <option value="ABD Piyasaları">ABD</option>
                <option value="Döviz / Emtia">FX/Emtia</option>
                <option value="Özel">Özel</option>
              </select></label>
              <label>Adet<input id="scan-limit" type="number" min="1" max="80" value="20"></label>
              <label>Özel<input id="scan-custom" type="text" placeholder="BTCUSDT,ETHUSDT"></label>
              <button class="btn-secondary" id="run-scan">Tara</button>
            </div>
            <div id="scan-results" class="compact-list"></div>
          </div>
        </div>

        <div class="strategy-body">
          <div class="strategy-left">
            <div class="panel-section">
              <div class="report-tabs">
                ${this.reportTabButton('summary', 'Özet')}
                ${this.reportTabButton('trades', 'İşlemler')}
                ${this.reportTabButton('performance', 'Performans')}
                ${this.reportTabButton('system', 'Sistem')}
                ${this.reportTabButton('warnings', 'Veri')}
              </div>
              <div id="report-content"></div>
            </div>
          </div>
          <div class="strategy-right">
            <div class="panel-section">
              <div class="panel-title-row">
                <h3>${TR.EQUITY_CURVE}</h3>
                <div class="export-actions">
                  <button class="btn-sm" data-export="json">JSON</button>
                  <button class="btn-sm" data-export="trades_csv">İşlem CSV</button>
                  <button class="btn-sm" data-export="equity_csv">Equity CSV</button>
                </div>
              </div>
              <div class="equity-wrap"><canvas id="equity-canvas"></canvas></div>
            </div>
            <div class="panel-section">
              <h3>${TR.SIGNALS}</h3>
              <div id="signals-list"></div>
            </div>
          </div>
        </div>
      </div>
    `;

    this.renderStrategyCards();
    this.renderSpecEditor(EXAMPLES.emaCross);
    this.syncControls();
    this.bindEvents();
    this.showEmpty();
  }

  private reportTabButton(tab: ReportTab, label: string): string {
    return `<button class="report-tab${tab === this.reportTab ? ' active' : ''}" data-report-tab="${tab}">${label}</button>`;
  }

  private renderStrategyCards(): void {
    const elBlueprint = this.container.querySelector('#blueprint-editor');
    if (elBlueprint) {
      elBlueprint.innerHTML = `
        <div class="strategy-cards" id="strategy-cards">
          ${this.blueprints.map(s => `
            <button class="strategy-card${s.id === this.activeStrategy && this.mode === 'blueprint' ? ' active' : ''}" data-strategy="${s.id}">
              <span class="sc-name">${this.escape(s.label)}</span>
              <span class="sc-desc">${this.escape(s.description)}</span>
            </button>
          `).join('')}
        </div>
      `;
      elBlueprint.toggleAttribute('hidden', this.mode !== 'blueprint');
    }

    const elPreset = this.container.querySelector('#preset-cards');
    if (elPreset) {
      elPreset.innerHTML = `
        <div class="strategy-cards" id="strategy-cards-presets">
          ${this.presets.map(s => `
            <button class="strategy-card${s.id === this.activeStrategy && this.mode === 'preset' ? ' active' : ''}" data-strategy="${s.id}">
              <span class="sc-name">${this.escape(s.label)} <small style="opacity:0.6;font-weight:normal;">(${this.escape(s.category)})</small></span>
              <span class="sc-desc">${this.escape(s.description)}</span>
            </button>
          `).join('')}
        </div>
      `;
      elPreset.toggleAttribute('hidden', this.mode !== 'preset');
    }
  }

  private renderSpecEditor(spec?: Partial<StrategySpec>): void {
    const el = this.container.querySelector('#spec-editor');
    if (!el) return;
    const rules = spec?.rules ?? {};
    const risk = spec?.risk ?? {};
    el.innerHTML = `
      <div class="lab-grid">
        <div class="lab-main">
          <div class="lab-row">
            <label>Ad<input id="spec-name" type="text" value="${this.escapeAttr(spec?.name ?? 'EMA 50/200')}"></label>
            <label>Not<input id="spec-note" type="text" value="${this.escapeAttr(spec?.note ?? '')}"></label>
          </div>
          <div class="formula-grid">
            ${this.formulaField('long_entry', 'Long Giriş', rules.long_entry)}
            ${this.formulaField('long_exit', 'Long Çıkış', rules.long_exit)}
            ${this.formulaField('short_entry', 'Short Giriş', rules.short_entry)}
            ${this.formulaField('short_exit', 'Short Çıkış', rules.short_exit)}
          </div>
        </div>
        <div class="lab-side">
          <div class="visual-builder">
            <label>Örnek<select id="example-select">
              <option value="emaCross">EMA 50/200</option>
              <option value="rsiTrend">RSI + EMA</option>
              <option value="shortRsi">Short RSI</option>
            </select></label>
            <button class="btn-secondary" id="apply-example">Uygula</button>
          </div>
          <div class="visual-rule-builder">
            <label>Kural<select id="builder-target">
              <option value="long_entry">Long Giriş</option>
              <option value="long_exit">Long Çıkış</option>
              <option value="short_entry">Short Giriş</option>
              <option value="short_exit">Short Çıkış</option>
            </select></label>
            <label>Sol<select id="builder-left">
              <option value="EMA">EMA(C,p)</option>
              <option value="SMA">SMA(C,p)</option>
              <option value="RSI">RSI(C,p)</option>
              <option value="C">C</option>
            </select></label>
            <label>Sol p<input id="builder-left-period" type="number" value="50" min="1"></label>
            <label>Op<select id="builder-op">
              <option value="CROSS_UP">yukarı keser</option>
              <option value="CROSS_DOWN">aşağı keser</option>
              <option value=">">></option>
              <option value="<"><</option>
              <option value="ABOVE">üstünde seyreder</option>
              <option value="BELOW">altında seyreder</option>
              <option value="RISING">sürekli yükselen (Periyot: Sağ değer)</option>
              <option value="FALLING">sürekli düşen (Periyot: Sağ değer)</option>
              <option value="VOLUME_ABOVE_AVG">Hacim ort. üstü (Periyot: Sağ değer)</option>
            </select></label>
            <label>Bağ<select id="builder-join">
              <option value="OR">OR</option>
              <option value="AND">AND</option>
            </select></label>
            <label>Sağ<select id="builder-right">
              <option value="EMA">EMA(C,p)</option>
              <option value="SMA">SMA(C,p)</option>
              <option value="NUMBER">Sayı</option>
              <option value="C">C</option>
            </select></label>
            <label>Sağ p/değer<input id="builder-right-value" type="number" value="200" min="0"></label>
            <label class="check-label"><input id="builder-volume" type="checkbox"> Hacim filtresi</label>
            <button class="btn-secondary" id="add-rule-block">Kural Ekle</button>
          </div>
          <label>Stop %<input id="risk-stop" type="number" min="0" step="0.1" value="${risk.stop_loss_pct ?? 3}"></label>
          <label>Kar Al %<input id="risk-take" type="number" min="0" step="0.1" value="${risk.take_profit_pct ?? 8}"></label>
          <label>Trailing %<input id="risk-trail" type="number" min="0" step="0.1" value="${risk.trailing_stop_pct ?? 5}"></label>
          <label>Süre Stop (Bar)<input id="risk-time" type="number" min="0" step="1" value="${risk.time_stop_bars ?? 0}" title="0 = Devre dışı"></label>
        </div>
      </div>
    `;
    el.toggleAttribute('hidden', this.mode !== 'spec');
  }

  private formulaField(id: keyof StrategySpec['rules'], label: string, value = ''): string {
    return `
      <label>${label}
        <textarea id="rule-${id}" spellcheck="false">${this.escape(value)}</textarea>
      </label>
    `;
  }

  private bindEvents(): void {
    this.container.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      const modeBtn = target.closest<HTMLElement>('[data-mode]');
      if (modeBtn) {
        this.mode = modeBtn.dataset['mode'] as StrategyMode;
        this.lastRunKey = '';
        this.syncControls();
        void this.runAnalysis();
        return;
      }

      const card = target.closest<HTMLElement>('[data-strategy]');
      if (card) {
        this.activeStrategy = card.dataset['strategy'] || this.activeStrategy;
        this.renderStrategyCards();
        this.lastRunKey = '';
        void this.runAnalysis();
        return;
      }

      if (target.closest('#run-backtest')) {
        this.lastRunKey = '';
        void this.runAnalysis();
        return;
      }

      if (target.closest('#save-strategy')) {
        void this.saveStrategy();
        return;
      }

      if (target.closest('#activate-paper')) {
        void this.activateLastReportPaper();
        return;
      }

      if (target.closest('#refresh-saved')) {
        void this.loadSavedStrategies();
        return;
      }

      if (target.closest('#refresh-reports')) {
        void this.loadReports();
        return;
      }

      if (target.closest('#add-rule-block')) {
        this.addVisualRuleBlock();
        return;
      }

      if (target.closest('#run-optimizer')) {
        void this.runOptimizer();
        return;
      }

      if (target.closest('#export-optimizer')) {
        this.exportOptimizerCsv();
        return;
      }

      if (target.closest('#run-scan')) {
        void this.runMarketScan();
        return;
      }

      if (target.closest('#apply-example')) {
        const select = this.container.querySelector<HTMLSelectElement>('#example-select');
        const key = select?.value || 'emaCross';
        this.renderSpecEditor(EXAMPLES[key] ?? EXAMPLES.emaCross);
        this.bindSourceMode();
        return;
      }

      const reportTab = target.closest<HTMLElement>('[data-report-tab]');
      if (reportTab) {
        this.reportTab = reportTab.dataset['reportTab'] as ReportTab;
        this.renderReport();
        return;
      }

      const exportBtn = target.closest<HTMLElement>('[data-export]');
      if (exportBtn) {
        this.openExport(exportBtn.dataset['export'] || 'json');
        return;
      }

      const focusBtn = target.closest<HTMLElement>('[data-focus-time]');
      if (focusBtn) {
        this.emitFocus(Number(focusBtn.dataset['focusTime']));
        return;
      }

      const savedBtn = target.closest<HTMLElement>('[data-load-strategy]');
      if (savedBtn) {
        void this.loadSavedStrategy(Number(savedBtn.dataset['loadStrategy']));
        return;
      }

      const reportBtn = target.closest<HTMLElement>('[data-load-report]');
      if (reportBtn) {
        void this.loadArchivedReport(reportBtn.dataset['loadReport'] || '');
        return;
      }

      const rerunBtn = target.closest<HTMLElement>('[data-rerun-report]');
      if (rerunBtn) {
        void this.rerunArchivedReport(rerunBtn.dataset['rerunReport'] || '');
        return;
      }

      const optimizerBtn = target.closest<HTMLElement>('[data-apply-optimizer]');
      if (optimizerBtn) {
        void this.applyOptimizationRow(Number(optimizerBtn.dataset['applyOptimizer']));
        return;
      }

      const scanBtn = target.closest<HTMLElement>('[data-scan-symbol]');
      if (scanBtn) {
        this.emitSymbolSelect(scanBtn.dataset['scanSymbol'] || '');
      }
    });

    this.container.addEventListener('change', (e) => {
      const target = e.target as HTMLElement;
      if (target.id === 'bt-source') this.bindSourceMode();
    });
  }

  private syncControls(): void {
    this.container.querySelectorAll<HTMLElement>('[data-mode]').forEach(btn => {
      btn.classList.toggle('active', btn.dataset['mode'] === this.mode);
    });
    this.container.querySelector<HTMLElement>('#blueprint-editor')
      ?.toggleAttribute('hidden', this.mode !== 'blueprint');
    this.container.querySelector<HTMLElement>('#preset-cards')
      ?.toggleAttribute('hidden', this.mode !== 'preset');
    this.container.querySelector<HTMLElement>('#spec-editor')
      ?.toggleAttribute('hidden', this.mode !== 'spec');
    this.container.querySelectorAll<HTMLElement>('.report-tab').forEach(btn => {
      btn.classList.toggle('active', btn.dataset['reportTab'] === this.reportTab);
    });
    const symbolInput = this.container.querySelector<HTMLInputElement>('#bt-symbol');
    if (symbolInput) symbolInput.value = this.activeSymbol || '-';
    const intervalSelect = this.container.querySelector<HTMLSelectElement>('#bt-interval');
    if (intervalSelect) intervalSelect.value = this.activeInterval;
    this.bindSourceMode();
  }

  private bindSourceMode(): void {
    const source = this.value<HTMLSelectElement>('#bt-source') || 'cache_only';
    this.container.querySelector<HTMLElement>('#csv-import')?.toggleAttribute(
      'hidden',
      source !== 'csv_import',
    );
  }

  private async runAnalysis(): Promise<void> {
    this.syncControls();
    if (this.runInFlight) {
      this.rerunRequested = true;
      return;
    }
    const sourceMode = this.value<HTMLSelectElement>('#bt-source') || 'cache_only';
    const needsChartCandles = sourceMode !== 'csv_import';
    if ((needsChartCandles && this.candles.length < MIN_BARS_FOR_RUN) || !this.activeSymbol) {
      this.showEmpty();
      return;
    }

    const reportEl = this.container.querySelector('#report-content');
    if (reportEl) reportEl.innerHTML = `<div class="loading">${TR.RUNNING_BACKTEST}</div>`;

    this.runInFlight = true;
    try {
      const result = await this.fetchBacktest();
      result.signals = this.enrichSignalsWithTrades(result.signals || [], result.trades || [], result.strategy_spec?.risk);
      this.lastResult = result;
      this.renderReport();
      this.renderSignals(result.signals);
      this.renderEquityCurve(result);
      this.emitSignals(result.signals);
    } catch (err) {
      this.showError(err instanceof Error ? err.message : String(err));
    } finally {
      this.runInFlight = false;
      if (this.rerunRequested) {
        this.rerunRequested = false;
        this.lastRunKey = '';
        void this.runAnalysis();
      }
    }
  }

  private async fetchBacktest(): Promise<BacktestResult> {
    const payload = this.buildPayload();
    const resp = await fetch(BACKTEST_RUN_ENDPOINT, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(BACKTEST_TIMEOUT_MS),
    });

    if (!resp.ok) {
      let detail = `HTTP ${resp.status}`;
      try {
        const errorBody = await resp.json() as { detail?: string };
        if (errorBody.detail) detail = errorBody.detail;
      } catch {
        // HTTP status is enough.
      }
      throw new Error(detail);
    }

    return await resp.json() as BacktestResult;
  }

  private buildPayload(): Record<string, unknown> {
    const sourceMode = this.value<HTMLSelectElement>('#bt-source') || 'cache_only';
    const payload: Record<string, unknown> = {
      symbol: this.activeSymbol,
      interval: this.value<HTMLSelectElement>('#bt-interval') || this.activeInterval,
      capital: this.num('#bt-capital', 100_000),
      lookback_bars: Math.min(Math.max(this.candles.length, 50), 5000),
      start_date: this.value<HTMLInputElement>('#bt-start') || null,
      end_date: this.value<HTMLInputElement>('#bt-end') || null,
      commission_rate: this.num('#bt-commission', 0.1) / 100,
      slippage_model: this.value<HTMLSelectElement>('#bt-slippage-model') || 'fixed_bps',
      slippage_bps: this.num('#bt-slippage', 5),
      slippage_tick: this.num('#bt-slippage-tick', 0.01),
      volume_limit_pct: this.num('#bt-volume-limit-pct', 5) / 100,
      volume_window: this.num('#bt-volume-window', 5),
      max_position_pct: this.num('#bt-maxpos', 20) / 100,
      allow_short: Boolean(this.container.querySelector<HTMLInputElement>('#bt-allow-short')?.checked),
      source_mode: sourceMode,
    };

    if (sourceMode === 'csv_import') {
      payload['csv_text'] = this.container.querySelector<HTMLTextAreaElement>('#csv-text')?.value || '';
    }

    if (this.mode === 'spec') {
      payload['strategy_id'] = 'strategy_spec';
      payload['strategy_spec'] = this.buildSpec();
    } else if (this.mode === 'preset') {
      const preset = this.presets.find(p => p.id === this.activeStrategy);
      payload['strategy_id'] = 'strategy_spec';
      payload['strategy_spec'] = preset?.strategy_spec ?? this.buildSpec();
    } else {
      payload['strategy_id'] = this.activeStrategy;
      payload['params'] = {};
    }
    return payload;
  }

  private buildSpec(): StrategySpec {
    return {
      name: this.value<HTMLInputElement>('#spec-name') || 'Kural Stratejisi',
      note: this.value<HTMLInputElement>('#spec-note') || '',
      rules: {
        long_entry: this.value<HTMLTextAreaElement>('#rule-long_entry'),
        long_exit: this.value<HTMLTextAreaElement>('#rule-long_exit'),
        short_entry: this.value<HTMLTextAreaElement>('#rule-short_entry'),
        short_exit: this.value<HTMLTextAreaElement>('#rule-short_exit'),
      },
      risk: {
        stop_loss_pct: this.num('#risk-stop', 0),
        take_profit_pct: this.num('#risk-take', 0),
        trailing_stop_pct: this.num('#risk-trail', 0),
        time_stop_bars: this.num('#risk-time', 0),
      },
    };
  }

  private enrichSignalsWithTrades(
    signals: Signal[],
    trades: BacktestTrade[],
    risk?: StrategySpec['risk'],
  ): Signal[] {
    const enriched = signals.map(signal => ({ ...signal }));
    const riskSettings = risk ?? this.currentRiskSettings();

    for (const trade of trades) {
      const side = trade.side === 'SHORT' || trade.entry_type === 'SHORT' ? 'SHORT' : 'LONG';
      const entryType = side === 'SHORT' ? 'SHORT' : 'BUY';
      const exitType = side === 'SHORT' ? 'COVER' : 'SELL';
      const entry = this.findTradeSignal(enriched, trade.entry_time, entryType);
      const exit = this.findTradeSignal(enriched, trade.exit_time, exitType);

      if (entry) {
        Object.assign(entry, {
          trade_role: 'entry',
          trade_side: side,
          entry_time: trade.entry_time,
          exit_time: trade.exit_time,
          entry_price: trade.entry_price,
          exit_price: trade.exit_price,
          net_pnl: trade.net_pnl,
          return_pct: trade.return_pct,
          open_position: false,
        } satisfies Partial<Signal>);
        this.applyRiskLevels(entry, riskSettings, side, trade.entry_price);
      }

      if (exit) {
        Object.assign(exit, {
          trade_role: 'exit',
          trade_side: side,
          entry_time: trade.entry_time,
          exit_time: trade.exit_time,
          entry_price: trade.entry_price,
          exit_price: trade.exit_price,
          net_pnl: trade.net_pnl,
          return_pct: trade.return_pct,
          pnl: trade.net_pnl,
          open_position: false,
        } satisfies Partial<Signal>);
      }
    }

    for (const signal of enriched) {
      if (signal.open_position && (signal.type === 'BUY' || signal.type === 'SHORT')) {
        const side = signal.type === 'SHORT' ? 'SHORT' : 'LONG';
        signal.trade_role = 'entry';
        signal.trade_side = side;
        signal.entry_time = signal.timestamp;
        signal.entry_price = signal.price;
        this.applyRiskLevels(signal, riskSettings, side, signal.price);
      }
    }

    return enriched;
  }

  private findTradeSignal(signals: Signal[], timestamp: number, type: Signal['type']): Signal | undefined {
    return signals.find(signal => signal.timestamp === timestamp && signal.type === type)
      ?? signals.find(signal => Math.abs(signal.timestamp - timestamp) <= 1 && signal.type === type);
  }

  private currentRiskSettings(): StrategySpec['risk'] {
    return {
      stop_loss_pct: this.num('#risk-stop', 0),
      take_profit_pct: this.num('#risk-take', 0),
      trailing_stop_pct: this.num('#risk-trail', 0),
      time_stop_bars: this.num('#risk-time', 0),
    };
  }

  private applyRiskLevels(
    signal: Signal,
    risk: StrategySpec['risk'] | undefined,
    side: 'LONG' | 'SHORT',
    entryPrice: number,
  ): void {
    const stopPct = risk?.stop_loss_pct ?? 0;
    const takePct = risk?.take_profit_pct ?? 0;
    if (entryPrice <= 0) return;

    if (stopPct > 0) {
      signal.stop_price = side === 'SHORT'
        ? entryPrice * (1 + stopPct / 100)
        : entryPrice * (1 - stopPct / 100);
    }
    if (takePct > 0) {
      signal.take_profit_price = side === 'SHORT'
        ? entryPrice * (1 - takePct / 100)
        : entryPrice * (1 + takePct / 100);
    }
    if (stopPct > 0 && takePct > 0) {
      signal.risk_reward = takePct / stopPct;
    }
  }

  private async saveStrategy(): Promise<void> {
    const payload = this.buildPayload();
    const strategySpec = payload['strategy_spec'] as StrategySpec | undefined;
    const isSpecBased = this.mode === 'spec' || this.mode === 'preset';
    
    const spec = isSpecBased ? (strategySpec || this.buildSpec()) : null;
    const name = spec?.name || this.activeStrategy;
    
    const resp = await fetch(STRATEGY_STORE_ENDPOINT, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        name,
        symbol: this.activeSymbol,
        interval: this.value<HTMLSelectElement>('#bt-interval') || this.activeInterval,
        market: '',
        strategy_id: isSpecBased ? 'strategy_spec' : this.activeStrategy,
        strategy_spec: spec,
        params: {},
        settings: payload,
        source_mode: this.value<HTMLSelectElement>('#bt-source') || 'cache_only',
        notes: spec?.note || '',
      }),
    });
    if (!resp.ok) {
      this.showError(await this.errorText(resp));
      return;
    }
    await this.loadSavedStrategies();
  }

  private async activateLastReportPaper(): Promise<void> {
    if (!this.lastResult?.run_id) {
      this.showError('Paper aktivasyonu için önce backtest çalıştır.');
      return;
    }
    const resp = await fetch(`${BACKTEST_REPORTS_ENDPOINT}/${this.lastResult.run_id}/paper/activate`, {
      method: 'POST',
    });
    if (!resp.ok) {
      this.showError(await this.errorText(resp));
      return;
    }
    await this.loadSavedStrategies();
    this.renderPaperStatus('Paper aktivasyonu kaydedildi. Canlı sinyal geldiğinde sanal işlem üretir.');
  }

  private async loadSavedStrategy(id: number): Promise<void> {
    const resp = await fetch(`${STRATEGY_STORE_ENDPOINT}/${id}`);
    if (!resp.ok) {
      this.showError(await this.errorText(resp));
      return;
    }
    const record = await resp.json() as SavedStrategy;
    if (record.strategy_spec) {
      this.mode = 'spec';
      this.renderSpecEditor(record.strategy_spec);
    } else {
      this.mode = 'blueprint';
      this.activeStrategy = String(record.settings?.['strategy_id'] || this.activeStrategy);
      this.renderStrategyCards();
    }
    this.syncControls();
    this.lastRunKey = '';
  }

  private async loadArchivedReport(runId: string): Promise<void> {
    const resp = await fetch(`${BACKTEST_REPORTS_ENDPOINT}/${runId}`);
    if (!resp.ok) {
      this.showError(await this.errorText(resp));
      return;
    }
    const report = await resp.json() as BacktestResult;
    report.signals = this.enrichSignalsWithTrades(report.signals || [], report.trades || [], report.strategy_spec?.risk);
    this.lastResult = report;
    if (report.strategy_spec) {
      this.mode = 'spec';
      this.renderSpecEditor(report.strategy_spec);
    }
    this.renderReport();
    this.renderSignals(report.signals || []);
    this.renderEquityCurve(report);
    this.emitSignals(report.signals || []);
  }

  private async rerunArchivedReport(runId: string): Promise<void> {
    await this.loadArchivedReport(runId);
    this.lastRunKey = '';
    await this.runAnalysis();
  }

  private addVisualRuleBlock(): void {
    const target = this.value<HTMLSelectElement>('#builder-target') || 'long_entry';
    const left = this.builderOperand(
      this.value<HTMLSelectElement>('#builder-left'),
      this.num('#builder-left-period', 50),
    );
    const right = this.builderOperand(
      this.value<HTMLSelectElement>('#builder-right'),
      this.num('#builder-right-value', 200),
    );
    const op = this.value<HTMLSelectElement>('#builder-op') || 'CROSS_UP';
    const join = this.value<HTMLSelectElement>('#builder-join') || 'OR';
    const volume = this.container.querySelector<HTMLInputElement>('#builder-volume')?.checked;

    let expr = '';
    if (op === 'CROSS_UP' || op === 'CROSS_DOWN' || op === 'ABOVE' || op === 'BELOW') {
      expr = `${op}(${left}, ${right})`;
    } else if (op === 'RISING' || op === 'FALLING' || op === 'VOLUME_ABOVE_AVG') {
      const rightVal = this.num('#builder-right-value', 3);
      expr = `${op}(${left}, ${rightVal})`;
    } else {
      expr = `${left} ${op} ${right}`;
    }

    if (volume) expr = `${expr} AND VOLUME_ABOVE_AVG(V, 20)`;
    const textarea = this.container.querySelector<HTMLTextAreaElement>(`#rule-${target}`);
    if (!textarea) return;
    textarea.value = textarea.value.trim()
      ? `(${textarea.value.trim()}) ${join} (${expr})`
      : expr;
  }

  private builderOperand(kind: string, value: number): string {
    if (kind === 'C') return 'C';
    if (kind === 'NUMBER') return String(value);
    const period = Math.max(1, Math.round(value || 1));
    return `${kind || 'EMA'}(C,${period})`;
  }

  private async runOptimizer(): Promise<void> {
    const out = this.container.querySelector('#optimizer-results');
    if (out) out.innerHTML = `<div class="loading">Deneniyor...</div>`;
    const fast = this.csvNumbers('#opt-fast');
    const slow = this.csvNumbers('#opt-slow');
    const allowShort = Boolean(this.container.querySelector<HTMLInputElement>('#bt-allow-short')?.checked);
    const spec = this.optimizerSpec('{fast}', '{slow}', allowShort);
    const payload = {
      ...this.buildPayload(),
      strategy_id: 'strategy_spec',
      strategy_spec: spec,
      param_grid: { fast, slow },
      max_combinations: 80,
    };
    const resp = await fetch(BACKTEST_OPTIMIZE_ENDPOINT, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(BACKTEST_TIMEOUT_MS),
    });
    if (!resp.ok) {
      if (out) out.innerHTML = `<div class="empty-state error">${this.escape(await this.errorText(resp))}</div>`;
      return;
    }
    const body = await resp.json() as {
      results?: OptimizationRow[];
      stability_report?: OptimizationStabilityReport;
    };
    this.optimizationRows = body.results ?? [];
    this.optimizationStability = body.stability_report ?? null;
    this.renderOptimizerResults();
  }

  private async applyOptimizationRow(index: number): Promise<void> {
    const row = this.optimizationRows[index];
    if (!row) return;
    const fast = String(row.params['fast'] ?? 20);
    const slow = String(row.params['slow'] ?? 200);
    const allowShort = Boolean(this.container.querySelector<HTMLInputElement>('#bt-allow-short')?.checked);
    this.mode = 'spec';
    this.renderSpecEditor(this.optimizerSpec(fast, slow, allowShort));
    this.syncControls();
    this.lastRunKey = '';
    await this.runAnalysis();
  }

  private optimizerSpec(fast: string, slow: string, allowShort: boolean): StrategySpec {
    return {
      name: `Optimize EMA ${fast}/${slow}`,
      rules: {
        long_entry: `CROSS_UP(EMA(C,${fast}), EMA(C,${slow}))`,
        long_exit: `CROSS_DOWN(EMA(C,${fast}), EMA(C,${slow}))`,
        short_entry: allowShort ? `CROSS_DOWN(EMA(C,${fast}), EMA(C,${slow}))` : '',
        short_exit: allowShort ? `CROSS_UP(EMA(C,${fast}), EMA(C,${slow}))` : '',
      },
      risk: this.buildSpec().risk,
    };
  }

  private exportOptimizerCsv(): void {
    if (this.optimizationRows.length === 0) {
      this.showError('Dışa aktarılacak optimizasyon sonucu yok.');
      return;
    }
    const header = [
      'rank',
      'params',
      'score',
      'total_return_pct',
      'max_drawdown_pct',
      'profit_factor',
      'win_rate_pct',
      'total_trades',
      'warnings',
    ];
    const rows = this.optimizationRows.map((row, idx) => [
      String(idx + 1),
      JSON.stringify(row.params),
      String(row.score),
      String(row.metrics.total_return_pct),
      String(row.metrics.max_drawdown_pct),
      String(row.metrics.profit_factor),
      String(row.metrics.win_rate),
      String(row.metrics.total_trades),
      (row.warnings || []).map(w => typeof w === 'string' ? w : (w as any).message).join(' | '),
    ]);
    const csv = [header, ...rows]
      .map(cols => cols.map(col => this.csvCell(col)).join(','))
      .join('\n');
    this.openTextFile(csv, `optimizer-${this.activeSymbol || 'symbol'}.csv`, 'text/csv');
  }

  private async runMarketScan(): Promise<void> {
    const out = this.container.querySelector('#scan-results');
    if (out) out.innerHTML = `<div class="loading">Taranıyor...</div>`;
    const group = this.value<HTMLSelectElement>('#scan-group') || 'Kripto';
    const limit = this.num('#scan-limit', 20);
    const customSymbols = this.value<HTMLInputElement>('#scan-custom')
      .split(/[\s,;]+/)
      .map(s => s.trim().toUpperCase())
      .filter(Boolean);
    const symbols = customSymbols.length > 0
      ? customSymbols
      : ALL_SYMBOLS.filter(s => s.group === group).map(s => s.symbol);
    if (symbols.length === 0) {
      if (out) out.innerHTML = `<div class="empty-state error">Taranacak sembol bulunamadı.</div>`;
      return;
    }
    const payload = {
      ...this.buildPayload(),
      symbols,
      limit,
      strategy_id: this.mode === 'spec' ? 'strategy_spec' : this.activeStrategy,
      strategy_spec: this.mode === 'spec' ? this.buildSpec() : null,
    };
    const resp = await fetch(BACKTEST_SCAN_ENDPOINT, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(BACKTEST_TIMEOUT_MS),
    });
    if (!resp.ok) {
      if (out) out.innerHTML = `<div class="empty-state error">${this.escape(await this.errorText(resp))}</div>`;
      return;
    }
    const body = await resp.json() as { results?: ScanRow[] };
    this.scanRows = body.results ?? [];
    this.renderScanResults();
  }

  private renderSavedStrategies(): void {
    const el = this.container.querySelector('#saved-strategies');
    if (!el) return;
    if (this.savedStrategies.length === 0) {
      el.innerHTML = `<div class="empty-state">Kayıt yok</div>`;
      return;
    }
    el.innerHTML = this.savedStrategies.slice(0, 8).map(s => `
      <div class="compact-item">
        <div>
          <b>${this.escape(s.name)}</b>
          <span>${this.escape(s.symbol)} · ${this.escape(s.timeframe)} · ${formatDateTimeFromIso(s.created_at)}</span>
        </div>
        <button class="btn-sm" data-load-strategy="${s.id}">Aç</button>
      </div>
    `).join('');
  }

  private renderReportArchive(): void {
    const el = this.container.querySelector('#report-archive');
    if (!el) return;
    if (this.reportSummaries.length === 0) {
      el.innerHTML = `<div class="empty-state">Rapor yok</div>`;
      return;
    }
    el.innerHTML = this.reportSummaries.map(r => `
      <div class="compact-item">
        <div>
          <b>${this.escape(r.strategy_name)}</b>
          <span>${this.escape(r.symbol)} · ${formatPct(r.return_pct)} · ${formatDateTimeFromIso(r.created_at)}</span>
        </div>
        <div class="compact-actions">
          <button class="btn-sm" data-load-report="${r.id}">Aç</button>
          <button class="btn-sm" data-rerun-report="${r.id}">Tekrar</button>
        </div>
      </div>
    `).join('');
  }

  private renderOptimizerResults(): void {
    const el = this.container.querySelector('#optimizer-results');
    if (!el) return;
    if (this.optimizationRows.length === 0) {
      el.innerHTML = `<div class="empty-state">Sonuç yok</div>`;
      return;
    }
    const stability = this.optimizationStability;
    el.innerHTML = `
      ${stability ? `
        <div class="optimizer-stability">
          <div>
            <b>Stabil Bölge</b>
            <span>${this.escape(JSON.stringify(stability.best_params || {}))}</span>
          </div>
          <div>
            <b>Stabilite</b>
            <span>${formatNumber(stability.stable_score ?? 0, 2)} / Max ${formatNumber(stability.global_max ?? 0, 2)}</span>
          </div>
        </div>
      ` : ''}
      <table class="data-table mini-table">
        <thead><tr><th>Parametre</th><th>Getiri</th><th>DD</th><th>Skor</th><th></th></tr></thead>
        <tbody>
          ${this.optimizationRows.slice(0, 8).map((row, idx) => `
            <tr>
              <td>${this.escape(JSON.stringify(row.params))}</td>
              <td class="${row.metrics.total_return_pct >= 0 ? 'pos' : 'neg'}">${formatPct(row.metrics.total_return_pct)}</td>
              <td class="neg">${formatPct(-row.metrics.max_drawdown_pct)}</td>
              <td>${formatNumber(row.score, 2)}</td>
              <td><button class="btn-sm" data-apply-optimizer="${idx}">Uygula</button></td>
            </tr>
            ${row.warnings.length ? `
              <tr class="table-note"><td colspan="5">${this.escape(row.warnings.map(w => typeof w === 'string' ? w : (w as any).message).join(' · '))}</td></tr>
            ` : ''}
          `).join('')}
        </tbody>
      </table>
    `;
  }

  private renderScanResults(): void {
    const el = this.container.querySelector('#scan-results');
    if (!el) return;
    if (this.scanRows.length === 0) {
      el.innerHTML = `<div class="empty-state">Eşleşen sonuç yok</div>`;
      return;
    }
    el.innerHTML = `
      <table class="data-table mini-table">
        <thead><tr><th>Sembol</th><th>Sinyal</th><th>Getiri</th><th>İşlem</th><th></th></tr></thead>
        <tbody>
          ${this.scanRows.slice(0, 12).map(row => `
            <tr>
              <td class="sym-cell">${this.escape(row.symbol)}</td>
              <td>${row.last_signal ? this.signalLabel(row.last_signal.type) : '-'}</td>
              <td class="${row.total_return_pct >= 0 ? 'pos' : 'neg'}">${formatPct(row.total_return_pct)}</td>
              <td>${row.total_trades}</td>
              <td><button class="btn-sm" data-scan-symbol="${this.escapeAttr(row.symbol)}">Aç</button></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  private renderPaperStatus(message: string): void {
    const el = this.container.querySelector('#saved-strategies');
    if (!el) return;
    el.insertAdjacentHTML('afterbegin', `<div class="warning-item">${this.escape(message)}</div>`);
  }

  private showEmpty(): void {
    this.lastResult = null;
    const reportEl = this.container.querySelector('#report-content');
    const signalsEl = this.container.querySelector('#signals-list');
    if (reportEl) reportEl.innerHTML = `<div class="empty-state">${TR.WAITING_DATA}</div>`;
    if (signalsEl) signalsEl.innerHTML = `<div class="empty-state">${TR.NO_SIGNALS}</div>`;
    this.emitSignals([]);
  }

  private showError(message: string): void {
    const reportEl = this.container.querySelector('#report-content');
    const signalsEl = this.container.querySelector('#signals-list');
    if (reportEl) reportEl.innerHTML = `<div class="empty-state error">${this.escape(message)}</div>`;
    if (signalsEl) signalsEl.innerHTML = `<div class="empty-state">${TR.NO_SIGNALS}</div>`;
    this.emitSignals([]);
  }

  private renderReport(): void {
    this.syncControls();
    const el = this.container.querySelector('#report-content');
    const r = this.lastResult;
    if (!el || !r) return;
    if (this.reportTab === 'summary') el.innerHTML = this.summaryHTML(r);
    if (this.reportTab === 'trades') el.innerHTML = this.tradesHTML(r.trades);
    if (this.reportTab === 'performance') el.innerHTML = this.performanceHTML(r);
    if (this.reportTab === 'system') el.innerHTML = this.systemHTML(r);
    if (this.reportTab === 'warnings') el.innerHTML = this.warningsHTML(r);
  }

  private summaryHTML(r: BacktestResult): string {
    const m = r.metrics;
    return `
      <div class="metrics-grid metrics-wide">
        ${this.metric('Başlangıç', formatCurrency(m.initial_capital ?? r.capital))}
        ${this.metric('Bitiş', formatCurrency(m.final_equity), m.final_equity >= r.capital ? 'pos' : 'neg')}
        ${this.metric('Net K/Z', formatCurrency(m.net_pnl ?? (m.final_equity - r.capital)), (m.net_pnl ?? 0) >= 0 ? 'pos' : 'neg')}
        ${this.metric(TR.RETURN, formatPct(m.total_return_pct), m.total_return_pct >= 0 ? 'pos' : 'neg')}
        ${this.metric('Yıllık', formatPct(m.annualized_return_pct ?? 0), (m.annualized_return_pct ?? 0) >= 0 ? 'pos' : 'neg')}
        ${this.metric(TR.MAX_DRAWDOWN, formatPct(-m.max_drawdown_pct), 'neg')}
        ${this.metric(TR.TOTAL_TRADES, String(m.total_trades))}
        ${this.metric(TR.WIN_RATE, formatPct((m.win_rate ?? 0) * 100))}
        ${this.metric(TR.PROFIT_FACTOR, formatNumber(m.profit_factor ?? this.profitFactor(r.trades), 2))}
      </div>
      <div class="report-note">${this.escape(r.summary_text ?? '')}</div>
    `;
  }

  private performanceHTML(r: BacktestResult): string {
    const m = r.metrics;
    return `
      <div class="metrics-grid">
        ${this.metric(TR.SHARPE, formatNumber(m.sharpe_ratio, 2))}
        ${this.metric('Benchmark', formatPct(m.benchmark_return_pct ?? 0), (m.benchmark_return_pct ?? 0) >= 0 ? 'pos' : 'neg')}
        ${this.metric('Komisyon', formatCurrency(m.total_commission))}
        ${this.metric('Slippage', formatCurrency(m.total_slippage ?? 0))}
        ${this.metric('En İyi', formatCurrency(m.best_trade ?? 0), (m.best_trade ?? 0) >= 0 ? 'pos' : 'neg')}
        ${this.metric('En Kötü', formatCurrency(m.worst_trade ?? 0), 'neg')}
        ${this.metric('Ort. Kar', formatCurrency(m.avg_win ?? 0), 'pos')}
        ${this.metric('Ort. Zarar', formatCurrency(m.avg_loss ?? 0), 'neg')}
        ${this.metric('Açık Poz.', m.has_open_position ? 'Var' : 'Yok')}
      </div>
      ${this.walkForwardHTML(r)}
      ${this.monteCarloHTML(r)}
      ${this.portfolioLabHTML(r)}
    `;
  }

  private walkForwardHTML(r: BacktestResult): string {
    const report = r.walk_forward_report;
    if (!report) return '';
    const status = report.passed ? 'Geçti' : 'Geçmedi';
    return `
      <div class="report-subsection">
        <h4>Walk-Forward Analizi</h4>
        <div class="metrics-grid">
          ${this.metric('OOS Toplam', formatPct(report.total_oos_return_pct), report.total_oos_return_pct >= 0 ? 'pos' : 'neg')}
          ${this.metric('WFE', formatNumber(report.walk_forward_efficiency, 2), report.passed ? 'pos' : 'neg')}
          ${this.metric('Pencere', String(report.windows.length))}
          ${this.metric('Durum', status, report.passed ? 'pos' : 'neg')}
        </div>
        ${report.warnings?.length ? `<div class="warning-list">${report.warnings.map(w => `<div class="warning-item">${this.escape(w)}</div>`).join('')}</div>` : ''}
      </div>
    `;
  }

  private monteCarloHTML(r: BacktestResult): string {
    const report = r.monte_carlo_report;
    if (!report) return '';
    return `
      <div class="report-subsection">
        <h4>Monte Carlo Risk</h4>
        <div class="metrics-grid">
          ${this.metric('Medyan Bitiş', formatCurrency(report.median_final_equity), report.median_final_equity >= r.capital ? 'pos' : 'neg')}
          ${this.metric('%5 Senaryo', formatCurrency(report.p05_final_equity), report.p05_final_equity >= r.capital ? 'pos' : 'neg')}
          ${this.metric('%95 Senaryo', formatCurrency(report.p95_final_equity), report.p95_final_equity >= r.capital ? 'pos' : 'neg')}
          ${this.metric('Zarar Olasılığı', formatPct(report.probability_of_loss * 100), report.probability_of_loss > 0.25 ? 'neg' : 'pos')}
          ${this.metric('Medyan DD', formatPct(-report.median_max_drawdown_pct), 'neg')}
          ${this.metric('%95 DD', formatPct(-report.p95_max_drawdown_pct), 'neg')}
        </div>
        ${report.warnings?.length ? `<div class="warning-list">${report.warnings.map(w => `<div class="warning-item">${this.escape(w)}</div>`).join('')}</div>` : ''}
      </div>
    `;
  }

  private portfolioLabHTML(r: BacktestResult): string {
    const summary = r.portfolio_lab_summary;
    if (!summary) return '';
    const m = summary.metrics;
    return `
      <div class="report-subsection">
        <h4>Portföy Lab Özeti</h4>
        <div class="metrics-grid">
          ${this.metric('Strateji', String(summary.strategy_count))}
          ${this.metric('Portföy Getiri', formatPct(m.total_return_pct), m.total_return_pct >= 0 ? 'pos' : 'neg')}
          ${this.metric('Portföy DD', formatPct(-m.max_drawdown_pct), 'neg')}
          ${this.metric('PF', formatNumber(m.profit_factor, 2))}
          ${this.metric('Sharpe-like', formatNumber(m.sharpe_like, 2))}
          ${this.metric('En Kötü Dönem', formatPct(m.worst_period_pct), 'neg')}
        </div>
        ${summary.warnings?.length ? `<div class="warning-list">${summary.warnings.map(w => `<div class="warning-item">${this.escape(w)}</div>`).join('')}</div>` : ''}
      </div>
    `;
  }

  private systemHTML(r: BacktestResult): string {
    const specRules = r.strategy_spec?.rules ?? {};
    const rows = [
      ['Strateji', r.strategy_name ?? r.strategy_id],
      ['Sembol', r.symbol],
      ['Periyot', r.interval],
      ['Veri Kalitesi', r.quality_score ? `${formatNumber(r.quality_score, 0)} / 100` : '-'],
      ['Kaynak', `${r.data_source?.source ?? '-'} / ${r.data_source?.status ?? '-'}`],
      ['Kapsama', `${formatNumber(r.data_source?.data_coverage_pct ?? 0, 1)}%`],
      ['Varsayım', `${r.assumptions?.['signal_timing'] ?? ''} → ${r.assumptions?.['execution_timing'] ?? ''}`],
      ['Long Giriş', specRules.long_entry ?? '-'],
      ['Long Çıkış', specRules.long_exit ?? '-'],
      ['Short Giriş', specRules.short_entry ?? '-'],
      ['Short Çıkış', specRules.short_exit ?? '-'],
    ];
    return `<table class="data-table system-table"><tbody>${
      rows.map(([k, v]) => `<tr><th>${this.escape(String(k))}</th><td>${this.escape(String(v || '-'))}</td></tr>`).join('')
    }</tbody></table>`;
  }

  private warningsHTML(r: BacktestResult): string {
    const warnings = r.warnings ?? [];
    if (warnings.length === 0) return `<div class="empty-state">Uyarı yok</div>`;
    return `<div class="warning-list">${
      warnings.map(w => {
        if (typeof w === 'string') {
          return `<div class="warning-item">${this.escape(w)}</div>`;
        }
        const qw = w as any;
        return `<div class="warning-item warning-${qw.severity}"><b>[${this.escape(qw.code)}]</b> ${this.escape(qw.message)}</div>`;
      }).join('')
    }</div>`;
  }

  private tradesHTML(trades: BacktestTrade[]): string {
    if (trades.length === 0) return `<div class="empty-state">${TR.NO_TRADES}</div>`;
    return `
      <table class="data-table trade-table">
        <thead>
          <tr>
            <th>Yön</th><th>Giriş</th><th>Çıkış</th><th>Adet</th><th>K/Z</th><th></th>
          </tr>
        </thead>
        <tbody>
          ${trades.slice().reverse().map(t => `
            <tr>
              <td><span class="trade-side ${t.side === 'SHORT' ? 'short' : 'long'}">${t.side ?? 'LONG'}</span></td>
              <td>${formatDateTime(t.entry_time)}<br>${formatNumber(t.entry_price)}</td>
              <td>${formatDateTime(t.exit_time)}<br>${formatNumber(t.exit_price)}</td>
              <td>${formatNumber(t.quantity, 0)}</td>
              <td class="${t.net_pnl >= 0 ? 'pos' : 'neg'}">${formatCurrency(t.net_pnl)}</td>
              <td><button class="btn-sm" data-focus-time="${t.entry_time}">Göster</button></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }

  private metric(label: string, value: string, cls = ''): string {
    return `<div class="metric-card"><div class="metric-label">${label}</div><div class="metric-value ${cls}">${value}</div></div>`;
  }

  private renderSignals(signals: Signal[]): void {
    const el = this.container.querySelector('#signals-list');
    if (!el) return;
    if (signals.length === 0) {
      el.innerHTML = `<div class="empty-state">${TR.NO_SIGNALS}</div>`;
      return;
    }
    el.innerHTML = [...signals].reverse().slice(0, 16).map(s => `
      <button class="signal-item ${s.type.toLowerCase()}" data-focus-time="${s.timestamp}">
        <div class="signal-header">
          <span class="signal-badge ${this.badgeClass(s.type)}">${this.signalLabel(s.type)}</span>
          <span class="signal-price">${formatNumber(s.price)}</span>
          <span class="signal-time">${formatDateTime(s.timestamp)}</span>
        </div>
        <div class="signal-reason">${this.escape(s.reason)}</div>
      </button>
    `).join('');
  }

  private renderEquityCurve(result: BacktestResult): void {
    const canvas = this.container.querySelector<HTMLCanvasElement>('#equity-canvas');
    if (!canvas || result.equity_curve.length === 0) return;

    const labels = result.equity_curve.map(p => formatDateTime(p.time));
    const equity = result.equity_curve.map(p => p.total_equity);
    const drawdown = result.equity_curve.map(p => -(p.drawdown_pct ?? 0));
    const step = Math.max(1, Math.floor(labels.length / 220));
    const sampledLabels = labels.filter((_, i) => i % step === 0);
    const sampledEquity = equity.filter((_, i) => i % step === 0);
    const sampledDrawdown = drawdown.filter((_, i) => i % step === 0);

    const datasets = [
      {
        label: 'Equity',
        data: sampledEquity,
        borderColor: '#3fb950',
        backgroundColor: '#3fb95015',
        borderWidth: 2,
        pointRadius: 0,
        fill: true,
        tension: 0.1,
        yAxisID: 'y',
      },
      {
        label: 'Drawdown',
        data: sampledDrawdown,
        borderColor: '#f85149',
        backgroundColor: '#f8514910',
        borderWidth: 1,
        pointRadius: 0,
        fill: false,
        tension: 0.1,
        yAxisID: 'y1',
      },
    ];

    if (this.equityChart) {
      this.equityChart.data.labels = sampledLabels;
      this.equityChart.data.datasets = datasets;
      this.equityChart.update('none');
      return;
    }

    this.equityChart = new Chart(canvas, {
      type: 'line',
      data: { labels: sampledLabels, datasets },
      options: {
        animation: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { display: false },
          y: { ticks: { color: '#8b949e', font: { size: 10 } }, grid: { color: '#21262d' } },
          y1: {
            position: 'right',
            ticks: { color: '#8b949e', font: { size: 10 } },
            grid: { drawOnChartArea: false },
          },
        },
        responsive: true,
        maintainAspectRatio: false,
      },
    });
  }

  private openExport(format: string): void {
    if (!this.lastResult?.run_id) return;
    window.open(`/api/backtest/reports/${this.lastResult.run_id}/export?format=${format}`, '_blank');
  }

  private openTextFile(content: string, filename: string, mimeType: string): void {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  private csvCell(value: string): string {
    return `"${value.replace(/"/g, '""')}"`;
  }

  private profitFactor(trades: BacktestTrade[]): number {
    let gross = 0;
    let loss = 0;
    for (const t of trades) {
      if (t.net_pnl > 0) gross += t.net_pnl;
      else loss += Math.abs(t.net_pnl);
    }
    if (loss === 0) return gross > 0 ? 1_000_000 : 0;
    return gross / loss;
  }

  private signalLabel(type: Signal['type']): string {
    return ({ BUY: 'AL', SELL: 'SAT', SHORT: 'SHORT', COVER: 'COVER', HOLD: 'BEKLE' })[type];
  }

  private badgeClass(type: Signal['type']): string {
    return ({
      BUY: 'badge-buy',
      SELL: 'badge-sell',
      SHORT: 'badge-short',
      COVER: 'badge-cover',
      HOLD: '',
    })[type];
  }

  private value<T extends HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>(selector: string): string {
    return this.container.querySelector<T>(selector)?.value.trim() ?? '';
  }

  private num(selector: string, fallback: number): number {
    const raw = Number(this.value<HTMLInputElement>(selector));
    return Number.isFinite(raw) ? raw : fallback;
  }

  private csvNumbers(selector: string): number[] {
    return this.value<HTMLInputElement>(selector)
      .split(',')
      .map(v => Number(v.trim()))
      .filter(v => Number.isFinite(v) && v > 0);
  }

  private async errorText(resp: Response): Promise<string> {
    try {
      const body = await resp.json() as { detail?: string };
      return body.detail || `HTTP ${resp.status}`;
    } catch {
      return `HTTP ${resp.status}`;
    }
  }

  private escape(value: unknown): string {
    return String(value ?? '').replace(/[&<>"']/g, ch => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
    })[ch] || ch);
  }

  private escapeAttr(value: unknown): string {
    return this.escape(value).replace(/`/g, '&#96;');
  }

  destroy(): void {
    this.equityChart?.destroy();
  }
}

function formatDateTimeFromIso(value: string): string {
  const ms = Date.parse(value);
  if (!Number.isFinite(ms)) return value;
  return formatDateTime(Math.floor(ms / 1000));
}
