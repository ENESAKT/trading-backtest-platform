import {
  createChart,
  CrosshairMode,
  ColorType,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
  type CandlestickData,
  type LineData,
  type HistogramData,
  type BarData,
  type SeriesMarker,
  type IPriceLine,
  type Range,
  type Time,
  LineStyle,
  PriceScaleMode,
} from 'lightweight-charts';
import type { OHLCV, Timeframe, ChartType, IndicatorSet, Signal, ChartDataStatus, ChartViewOptions } from '../types.js';
import { computeIndicators, lastValid, type IndicatorCalculationOptions } from '../indicators/index.js';
import { TR, formatNumber, formatDateTime } from '../constants/tr.js';
import { DrawingManager } from './DrawingManager.js';

// ─── Theme constants ──────────────────────────────────────────────────────────

const C = {
  bg:       '#0d1117',
  panel:    '#161b22',
  border:   '#21262d',
  text:     '#8b949e',
  textBold: '#c9d1d9',
  green:    '#3fb950',
  red:      '#f85149',
  blue:     '#58a6ff',
  purple:   '#bc8cff',
  yellow:   '#d29922',
  orange:   '#e3b341',
};

const CHART_OPTIONS = {
  layout:     { background: { type: ColorType.Solid, color: C.bg }, textColor: C.text },
  grid:       { vertLines: { color: C.border }, horzLines: { color: C.border } },
  crosshair:  { mode: CrosshairMode.Normal },
  timeScale:  { borderColor: C.border, timeVisible: true, secondsVisible: false },
  rightPriceScale: { borderColor: C.border },
  handleScroll: { mouseWheel: true, pressedMouseMove: true },
  handleScale:  { axisPressedMouseMove: true, mouseWheel: true, pinch: true },
};

type MainPriceSeries = ISeriesApi<'Candlestick'> | ISeriesApi<'Line'> | ISeriesApi<'Bar'>;
type ChartScaleMode = 'linear' | 'log' | 'percent';
type IndicatorCategory = 'trend' | 'momentum' | 'volatility' | 'volume';

interface IndicatorDefinition {
  key: string;
  label: string;
  category: IndicatorCategory;
  region: 'overlay' | 'panel';
  description: string;
  params?: Array<{
    key: keyof IndicatorCalculationOptions;
    label: string;
    min: number;
    max: number;
    step: number;
  }>;
}

interface PairedTradeOverlay {
  side: 'LONG' | 'SHORT';
  entryTime: number;
  exitTime: number;
  entryPrice: number;
  exitPrice: number;
  quantity?: number;
  netPnl: number;
  returnPct: number;
}

const PRICE_SHIFT_RESET_RATIO = 2.5;
const LS_ACTIVE_INDICATORS = 'piyasapilot_active_indicators';
const LS_INDICATOR_PARAMS = 'piyasapilot_indicator_params';
const LS_FAVORITE_INDICATORS = 'piyasapilot_favorite_indicators';
const DEFAULT_ACTIVE_INDICATORS = ['bb', 'ema', 'vwap', 'rsi', 'macd', 'vol'];
const DEFAULT_INDICATOR_PARAMS: Required<IndicatorCalculationOptions> = {
  rsiPeriod: 14,
  macdFastPeriod: 12,
  macdSlowPeriod: 26,
  macdSignalPeriod: 9,
  bbPeriod: 20,
  bbStdDev: 2,
  emaFastPeriod: 9,
  emaMidPeriod: 21,
  emaSlowPeriod: 50,
  atrPeriod: 14,
  stochasticKPeriod: 14,
  stochasticDPeriod: 3,
};
const INDICATOR_CATEGORIES: Array<{ id: IndicatorCategory | 'all'; label: string }> = [
  { id: 'all', label: 'Tümü' },
  { id: 'trend', label: 'Trend' },
  { id: 'momentum', label: 'Momentum' },
  { id: 'volatility', label: 'Volatilite' },
  { id: 'volume', label: 'Hacim' },
];
const INDICATOR_DEFS: IndicatorDefinition[] = [
  {
    key: 'bb',
    label: 'Bollinger Bands',
    category: 'volatility',
    region: 'overlay',
    description: 'Ortalama ve volatilite bandı.',
    params: [
      { key: 'bbPeriod', label: 'Periyot', min: 5, max: 100, step: 1 },
      { key: 'bbStdDev', label: 'Std', min: 0.5, max: 5, step: 0.1 },
    ],
  },
  { key: 'ema', label: 'EMA Seti', category: 'trend', region: 'overlay', description: '9/21/50 üstel ortalama seti.' },
  { key: 'vwap', label: 'VWAP', category: 'volume', region: 'overlay', description: 'Hacim ağırlıklı ortalama fiyat.' },
  {
    key: 'rsi',
    label: 'RSI',
    category: 'momentum',
    region: 'panel',
    description: 'Aşırı alım/satım momentum göstergesi.',
    params: [{ key: 'rsiPeriod', label: 'Periyot', min: 2, max: 100, step: 1 }],
  },
  {
    key: 'macd',
    label: 'MACD',
    category: 'momentum',
    region: 'panel',
    description: 'Trend momentum kesişimleri.',
    params: [
      { key: 'macdFastPeriod', label: 'Hızlı', min: 2, max: 80, step: 1 },
      { key: 'macdSlowPeriod', label: 'Yavaş', min: 3, max: 120, step: 1 },
      { key: 'macdSignalPeriod', label: 'Sinyal', min: 2, max: 50, step: 1 },
    ],
  },
  { key: 'vol', label: 'Hacim', category: 'volume', region: 'panel', description: 'Mum hacmi histogramı.' },
  {
    key: 'atr',
    label: 'ATR',
    category: 'volatility',
    region: 'panel',
    description: 'Ortalama gerçek aralık.',
    params: [{ key: 'atrPeriod', label: 'Periyot', min: 2, max: 100, step: 1 }],
  },
  {
    key: 'stoch',
    label: 'Stochastic',
    category: 'momentum',
    region: 'panel',
    description: '%K ve %D osilatörü.',
    params: [
      { key: 'stochasticKPeriod', label: '%K', min: 2, max: 100, step: 1 },
      { key: 'stochasticDPeriod', label: '%D', min: 1, max: 30, step: 1 },
    ],
  },
];
const INDICATOR_GROUPS: Array<{ id: string; label: string; keys: string[] }> = [
  { id: 'trend', label: 'Trend Seti', keys: ['ema', 'vwap', 'macd'] },
  { id: 'mean-reversion', label: 'Mean Reversion', keys: ['bb', 'rsi', 'stoch'] },
  { id: 'momentum', label: 'Momentum', keys: ['rsi', 'macd', 'stoch', 'atr'] },
];

// ─── ChartPanel ───────────────────────────────────────────────────────────────

export class ChartPanel {
  private container: HTMLElement;

  // Sub-containers for each chart row
  private mainEl!:   HTMLElement;
  private volEl!:    HTMLElement;
  private rsiEl!:    HTMLElement;
  private macdEl!:   HTMLElement;
  private atrEl!:    HTMLElement;
  private stochEl!:  HTMLElement;

  // Chart instances
  private mainChart!:  IChartApi;
  private volChart!:   IChartApi;
  private rsiChart!:   IChartApi;
  private macdChart!:  IChartApi;
  private atrChart!:   IChartApi;
  private stochChart!: IChartApi;

  // Series references
  private candleSeries!:  ISeriesApi<'Candlestick'>;
  private lineSeries!:    ISeriesApi<'Line'>;
  private barSeries!:     ISeriesApi<'Bar'>;
  private volSeries!:     ISeriesApi<'Histogram'>;
  private rsiSeries!:     ISeriesApi<'Line'>;
  private macdLineSeries!:   ISeriesApi<'Line'>;
  private macdSigSeries!:    ISeriesApi<'Line'>;
  private macdHistSeries!:   ISeriesApi<'Histogram'>;
  private atrSeries!:        ISeriesApi<'Line'>;
  private stochKSeries!:     ISeriesApi<'Line'>;
  private stochDSeries!:     ISeriesApi<'Line'>;

  // Overlay indicator series (on main chart)
  private bbUpperSeries!: ISeriesApi<'Line'>;
  private bbMidSeries!:   ISeriesApi<'Line'>;
  private bbLowerSeries!: ISeriesApi<'Line'>;
  private ema9Series!:    ISeriesApi<'Line'>;
  private ema21Series!:   ISeriesApi<'Line'>;
  private ema50Series!:   ISeriesApi<'Line'>;
  private vwapSeries!:    ISeriesApi<'Line'>;

  // Crosshair info overlay
  private infoEl!: HTMLElement;
  private stateEl!: HTMLElement;
  private indicatorCenterEl!: HTMLElement;

  private activeIndicators: Set<string> = new Set(DEFAULT_ACTIVE_INDICATORS);
  private favoriteIndicators: Set<string> = new Set();
  private indicatorParams: Required<IndicatorCalculationOptions> = { ...DEFAULT_INDICATOR_PARAMS };
  private indicatorPanelOpen = false;
  private indicatorQuery = '';
  private indicatorCategory: IndicatorCategory | 'all' = 'all';
  private candles: OHLCV[] = [];
  private markerSignals: Signal[] = [];
  private chartType: ChartType = 'candlestick';
  private scaleMode: ChartScaleMode = 'linear';
  private percentBaseTime: number | null = null;
  private percentBaseClose: number | null = null;
  private unitLabel = '';
  private autoPriceScale = true;
  private showPreviousClose = true;
  private lastMedianPrice: number | null = null;
  private lastSymbol = '';
  private lastTimeframe: Timeframe | null = null;
  private dataStatus: ChartDataStatus = 'idle';
  private lastPriceLine: IPriceLine | null = null;
  private previousCloseLine: IPriceLine | null = null;
  private priceLineSeries: MainPriceSeries | null = null;
  private tradeOverlaySeries: Array<ISeriesApi<'Line'>> = [];
  private pnlPriceLines: Array<{ series: MainPriceSeries; line: IPriceLine }> = [];
  private showPnlOverlay = true;
  private showRiskLines = true;
  private showBistLimits = true;
  private isFullscreen = false;
  private resizeObserver!: ResizeObserver;
  private drawingManager!: DrawingManager;

  constructor(container: HTMLElement) {
    this.container = container;
    this.loadIndicatorPrefs();
    this.buildDOM();
    this.initCharts();
    this.renderIndicatorCenter();
    this.bindIndicatorCenter();
    this.bindFullscreen();
    this.bindResize();
    this.bindKeyboard();
  }

  // ─── DOM scaffolding ────────────────────────────────────────────────────

  private buildDOM(): void {
    this.container.innerHTML = '';
    this.container.style.cssText = 'display:flex;flex-direction:column;height:100%;position:relative;background:' + C.bg;

    // Controls bar
    const controls = document.createElement('div');
    controls.className = 'chart-controls';
    controls.innerHTML = this.controlsHTML() + this.drawingToolbarHTML();
    this.container.appendChild(controls);

    // Crosshair info overlay
    this.infoEl = document.createElement('div');
    this.infoEl.className = 'chart-info-overlay';
    this.infoEl.style.display = 'none';
    this.container.appendChild(this.infoEl);

    this.stateEl = document.createElement('div');
    this.stateEl.className = 'chart-state-overlay';
    this.stateEl.style.display = 'none';
    this.container.appendChild(this.stateEl);

    this.indicatorCenterEl = document.createElement('div');
    this.indicatorCenterEl.className = 'indicator-center';
    this.indicatorCenterEl.hidden = true;
    this.container.appendChild(this.indicatorCenterEl);

    // Chart rows
    this.mainEl  = this.addChartRow('50%');
    this.volEl   = this.addChartRow('9%');
    this.rsiEl   = this.addChartRow('11%');
    this.macdEl  = this.addChartRow('11%');
    this.atrEl   = this.addChartRow('9%');
    this.stochEl = this.addChartRow('10%');

    this.bindControls(controls);
  }

  private addChartRow(height: string): HTMLElement {
    const el = document.createElement('div');
    el.style.cssText = `flex:0 0 ${height};min-height:40px;position:relative;`;
    this.container.appendChild(el);
    return el;
  }

  private controlsHTML(): string {
    const tfLabels: Record<Timeframe, string> = {
      '1m': TR.TF_1M, '5m': TR.TF_5M, '15m': TR.TF_15M, '30m': TR.TF_30M,
      '1h': TR.TF_1H, '4h': TR.TF_4H, '1d': TR.TF_1D, '1w': TR.TF_1W,
    };
    const tfs = Object.entries(tfLabels)
      .map(([val, label]) => `<button class="ctrl-btn tf-btn${val === '1d' ? ' active' : ''}" data-tf="${val}">${label}</button>`)
      .join('');

    return `
      <div class="ctrl-group">
        <span class="ctrl-label">${TR.TIMEFRAME}</span>
        ${tfs}
      </div>
      <div class="ctrl-group">
        <span class="ctrl-label">${TR.CHART_TYPE}</span>
        <button class="ctrl-btn type-btn active" data-type="candlestick">${TR.CANDLE}</button>
        <button class="ctrl-btn type-btn" data-type="line">${TR.LINE}</button>
        <button class="ctrl-btn type-btn" data-type="bar">${TR.BAR}</button>
      </div>
      <div class="ctrl-group">
        <span class="ctrl-label">${TR.INDICATORS}</span>
        <button class="ctrl-btn indicator-center-btn" id="indicator-center-btn" title="İndikatör merkezi">Merkez</button>
        ${INDICATOR_DEFS.map(def => `
          <button class="ctrl-btn ind-btn${this.activeIndicators.has(def.key) ? ' active' : ''}" data-ind="${def.key}">${def.key === 'stoch' ? 'STOCH' : def.key.toUpperCase()}</button>
        `).join('')}
      </div>
      <div class="ctrl-group">
        <span class="ctrl-label">Ölçek</span>
        <button class="ctrl-btn scale-mode-btn active" data-scale-mode="linear" title="Lineer fiyat ölçeği">Lin</button>
        <button class="ctrl-btn scale-mode-btn" data-scale-mode="log" title="Logaritmik fiyat ölçeği">Log</button>
        <button class="ctrl-btn scale-mode-btn" data-scale-mode="percent" title="Yüzdesel değişim ölçeği">%</button>
        <button class="ctrl-btn scale-base-btn" id="scale-base-btn" title="Yüzdesel baz noktasını görünür ilk bara al">Baz</button>
        <span class="unit-badge" id="chart-unit-badge"></span>
        <button class="ctrl-btn scale-auto-btn active" id="auto-price-btn" title="Otomatik fiyat ölçeği">Oto</button>
        <button class="ctrl-btn scale-reset-btn" id="price-reset-btn" title="Fiyatı yeniden ortala">⟲</button>
        <button class="ctrl-btn prev-close-btn active" id="prev-close-btn" title="Önceki kapanış çizgisi">ÖK</button>
      </div>
      <div class="ctrl-group">
        <span class="ctrl-label">K/Z</span>
        <button class="ctrl-btn pnl-toggle-btn active" id="pnl-overlay-btn" title="Trade bağlantıları ve PnL çizgileri">PnL</button>
        <button class="ctrl-btn pnl-toggle-btn active" id="risk-line-btn" title="Stop ve hedef çizgileri">Risk</button>
        <button class="ctrl-btn pnl-toggle-btn active" id="bist-limit-btn" title="BIST tavan/taban referansı">T/T</button>
      </div>
      <div class="ctrl-group ml-auto">
        <button class="ctrl-btn" id="fullscreen-btn" title="${TR.FULLSCREEN} (F)">⛶</button>
      </div>
    `;
  }

  private drawingToolbarHTML(): string {
    return `
      <div class="ctrl-group">
        <span class="ctrl-label">Çizim</span>
        <button class="ctrl-btn drawing-tool-btn" data-drawing-tool="trendline" title="Trend Çizgisi">⟋</button>
        <button class="ctrl-btn drawing-tool-btn" data-drawing-tool="hline" title="Yatay Çizgi">―</button>
        <button class="ctrl-btn drawing-tool-btn" data-drawing-tool="vline" title="Dikey Çizgi">│</button>
        <button class="ctrl-btn drawing-tool-btn" data-drawing-tool="measure" title="Ölçüm Aracı">📏</button>
        <button class="ctrl-btn drawing-clear-btn" id="drawing-clear-btn" title="Tüm çizimleri sil">🗑</button>
      </div>
    `;
  }

  private bindControls(controls: HTMLElement): void {
    controls.addEventListener('click', (e) => {
      const btn = (e.target as HTMLElement).closest('button');
      if (!btn) return;

      // Timeframe
      if (btn.classList.contains('tf-btn')) {
        controls.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.container.dispatchEvent(new CustomEvent('timeframeChange', {
          detail: btn.dataset['tf'] as Timeframe, bubbles: true,
        }));
      }

      // Chart type
      if (btn.classList.contains('type-btn')) {
        controls.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.setChartType(btn.dataset['type'] as ChartType);
      }

      // Indicator toggle
      if (btn.classList.contains('ind-btn')) {
        const ind = btn.dataset['ind']!;
        if (this.activeIndicators.has(ind)) {
          this.activeIndicators.delete(ind);
          btn.classList.remove('active');
        } else {
          this.activeIndicators.add(ind);
          btn.classList.add('active');
        }
        this.saveIndicatorPrefs();
        this.renderIndicatorCenter();
        this.updateIndicatorVisibility();
      }

      if (btn.id === 'indicator-center-btn') {
        this.indicatorPanelOpen = !this.indicatorPanelOpen;
        this.renderIndicatorCenter();
      }

      // Scale mode
      if (btn.classList.contains('scale-mode-btn')) {
        this.setScaleMode((btn.dataset['scaleMode'] ?? 'linear') as ChartScaleMode);
      }

      if (btn.id === 'scale-base-btn') {
        this.setPercentageBaseFromVisibleStart();
      }

      // Price scale / reference lines
      if (btn.id === 'auto-price-btn') {
        this.autoPriceScale = !this.autoPriceScale;
        btn.classList.toggle('active', this.autoPriceScale);
        if (this.autoPriceScale) this.resetPriceScales();
      }

      if (btn.id === 'price-reset-btn') {
        this.autoPriceScale = true;
        controls.querySelector('#auto-price-btn')?.classList.add('active');
        this.resetPriceScales();
      }

      if (btn.id === 'prev-close-btn') {
        this.showPreviousClose = !this.showPreviousClose;
        btn.classList.toggle('active', this.showPreviousClose);
        this.updateReferenceLines();
      }

      if (btn.id === 'pnl-overlay-btn') {
        this.showPnlOverlay = !this.showPnlOverlay;
        btn.classList.toggle('active', this.showPnlOverlay);
        this.renderPnlOverlays(this.markerSignals);
      }

      if (btn.id === 'risk-line-btn') {
        this.showRiskLines = !this.showRiskLines;
        btn.classList.toggle('active', this.showRiskLines);
        this.renderPnlOverlays(this.markerSignals);
      }

      if (btn.id === 'bist-limit-btn') {
        this.showBistLimits = !this.showBistLimits;
        btn.classList.toggle('active', this.showBistLimits);
        this.renderPnlOverlays(this.markerSignals);
      }

      // Fullscreen
      if (btn.id === 'fullscreen-btn') {
        this.toggleFullscreen();
      }
    });
  }

  // ─── Chart initialization ───────────────────────────────────────────────

  private initCharts(): void {
    this.mainChart = createChart(this.mainEl, { ...CHART_OPTIONS, height: this.mainEl.clientHeight || 300 });
    this.volChart  = createChart(this.volEl,  { ...CHART_OPTIONS, height: this.volEl.clientHeight  || 60, rightPriceScale: { visible: false }, timeScale: { visible: false } });
    this.rsiChart  = createChart(this.rsiEl,  { ...CHART_OPTIONS, height: this.rsiEl.clientHeight  || 80, rightPriceScale: { scaleMargins: { top: 0.1, bottom: 0.1 } }, timeScale: { visible: false } });
    this.macdChart = createChart(this.macdEl, { ...CHART_OPTIONS, height: this.macdEl.clientHeight || 80, rightPriceScale: { scaleMargins: { top: 0.1, bottom: 0.1 } }, timeScale: { visible: false } });
    this.atrChart  = createChart(this.atrEl,  { ...CHART_OPTIONS, height: this.atrEl.clientHeight  || 60, rightPriceScale: { scaleMargins: { top: 0.1, bottom: 0.1 } }, timeScale: { visible: false } });
    this.stochChart = createChart(this.stochEl, { ...CHART_OPTIONS, height: this.stochEl.clientHeight || 70, rightPriceScale: { scaleMargins: { top: 0.1, bottom: 0.1 } }, timeScale: { visible: false } });

    // Main series (initially candlestick)
    this.candleSeries = this.mainChart.addCandlestickSeries({
      upColor:   C.green, downColor: C.red,
      borderUpColor: C.green, borderDownColor: C.red,
      wickUpColor:   C.green, wickDownColor:   C.red,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    this.lineSeries = this.mainChart.addLineSeries({ color: C.blue, lineWidth: 2, visible: false, priceLineVisible: false, lastValueVisible: false });
    this.barSeries  = this.mainChart.addBarSeries({ upColor: C.green, downColor: C.red, visible: false, priceLineVisible: false, lastValueVisible: false });

    // Overlay indicators on main chart
    this.bbUpperSeries = this.mainChart.addLineSeries({ color: C.purple + '80', lineWidth: 1, lineStyle: 2 });
    this.bbMidSeries   = this.mainChart.addLineSeries({ color: C.purple + 'a0', lineWidth: 1 });
    this.bbLowerSeries = this.mainChart.addLineSeries({ color: C.purple + '80', lineWidth: 1, lineStyle: 2 });
    this.ema9Series    = this.mainChart.addLineSeries({ color: C.yellow,  lineWidth: 1 });
    this.ema21Series   = this.mainChart.addLineSeries({ color: C.orange,  lineWidth: 1 });
    this.ema50Series   = this.mainChart.addLineSeries({ color: C.blue,    lineWidth: 1 });
    this.vwapSeries    = this.mainChart.addLineSeries({ color: C.green,   lineWidth: 1, lineStyle: 3 });

    // Volume
    this.volSeries = this.volChart.addHistogramSeries({ priceFormat: { type: 'volume' }, priceScaleId: '' });

    // RSI
    this.rsiSeries = this.rsiChart.addLineSeries({ color: C.purple, lineWidth: 2 });

    // MACD
    this.macdLineSeries  = this.macdChart.addLineSeries({ color: C.blue,  lineWidth: 1 });
    this.macdSigSeries   = this.macdChart.addLineSeries({ color: C.orange, lineWidth: 1 });
    this.macdHistSeries  = this.macdChart.addHistogramSeries({ priceScaleId: '' });
    this.atrSeries       = this.atrChart.addLineSeries({ color: C.yellow, lineWidth: 1 });
    this.stochKSeries    = this.stochChart.addLineSeries({ color: C.blue, lineWidth: 1 });
    this.stochDSeries    = this.stochChart.addLineSeries({ color: C.orange, lineWidth: 1 });
    this.addLevelLine(this.rsiSeries, 30, C.green, '30');
    this.addLevelLine(this.rsiSeries, 70, C.red, '70');
    this.addLevelLine(this.stochKSeries, 20, C.green, '20');
    this.addLevelLine(this.stochKSeries, 80, C.red, '80');

    // Sync time scales
    this.syncTimeScales();

    // Crosshair overlay
    this.mainChart.subscribeCrosshairMove(param => {
      if (!param.time || !this.candles.length) {
        this.infoEl.style.display = 'none';
        return;
      }
      const ts = param.time as number;
      const c = this.candles.find(x => x.time === ts);
      if (!c) return;

      const inds = computeIndicators(this.candles, this.indicatorParams);
      const i = this.candles.indexOf(c);
      this.updateInfoOverlay(c, inds, i);
    });

    this.mainChart.subscribeClick(param => {
      if (this.scaleMode !== 'percent' || param.time == null) return;
      this.setPercentageBase(Number(param.time));
    });

    this.applyScaleMode();
    this.updateIndicatorVisibility();

    // G5: Drawing Manager
    this.drawingManager = new DrawingManager(this.mainChart, this.mainEl);
    this.drawingManager.setMainSeries(this.candleSeries);
    this.drawingManager.onDrawingChange((count) => {
      this.container.dataset['drawingCount'] = String(count);
    });
    const ctrlsEl = this.container.querySelector('.chart-controls') as HTMLElement;
    if (ctrlsEl) this.drawingManager.bindToolbar(ctrlsEl);
  }

  private addLevelLine(series: ISeriesApi<'Line'>, price: number, color: string, title: string): void {
    series.createPriceLine({
      price,
      color: `${color}80`,
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      axisLabelVisible: true,
      title,
      axisLabelColor: C.border,
      axisLabelTextColor: C.textBold,
    });
  }

  // ─── Time scale sync ────────────────────────────────────────────────────

  private syncTimeScales(): void {
    const charts = [this.mainChart, this.volChart, this.rsiChart, this.macdChart, this.atrChart, this.stochChart];
    charts.forEach((chart, idx) => {
      chart.timeScale().subscribeVisibleLogicalRangeChange(range => {
        if (!range) return;
        charts.forEach((c, j) => {
          if (j !== idx) c.timeScale().setVisibleLogicalRange(range);
        });
      });
    });
  }

  // ─── Data rendering ─────────────────────────────────────────────────────

  setData(candles: OHLCV[], options: ChartViewOptions = {}): void {
    const reason = options.reason ?? 'initial';
    const status = options.status ?? (candles.length > 0 ? 'ready' : 'empty');
    const savedVisibleRange = options.preserveTimeRange
      ? this.mainChart.timeScale().getVisibleRange()
      : null;

    this.lastSymbol = options.symbol ?? this.lastSymbol;
    this.lastTimeframe = options.timeframe ?? this.lastTimeframe;
    this.unitLabel = options.currency ?? this.inferUnit(this.lastSymbol);
    this.container.dataset['chartSymbol'] = this.lastSymbol;
    this.container.dataset['chartCurrency'] = this.unitLabel;
    if (this.lastTimeframe) this.container.dataset['chartTimeframe'] = this.lastTimeframe;

    // G5: Update drawing context on symbol/timeframe change
    if (this.drawingManager && this.lastSymbol && this.lastTimeframe) {
      this.drawingManager.setMainSeries(this.activeMainSeries());
      this.drawingManager.setContext(this.lastSymbol, this.lastTimeframe);
      this.container.dataset['drawingCount'] = String(this.drawingManager.getDrawingCount());
    }
    this.updateUnitBadge();

    if (candles.length === 0 || status !== 'ready') {
      this.clearChartData();
      this.setStatusOverlay(status, options.message);
      return;
    }

    const currentMedian = this.medianClose(candles);
    const shouldResetPrice = this.shouldResetPriceScale(reason, currentMedian, options.preserveTimeRange);

    this.candles = candles;
    this.ensurePercentBase(candles);
    this.dataStatus = 'ready';
    this.hideStatus();

    const cData = this.chartCandles(candles);

    this.candleSeries.setData(cData);
    this.lineSeries.setData(this.chartLineData(candles));
    this.barSeries.setData(cData as BarData[]);

    this.renderVolume(candles);
    this.renderIndicators(candles);
    this.updateReferenceLines();
    this.renderPnlOverlays(this.markerSignals);

    if (options.preserveTimeRange && savedVisibleRange) {
      this.restoreVisibleRange(savedVisibleRange);
    } else if (reason !== 'append') {
      this.mainChart.timeScale().fitContent();
    }

    if (shouldResetPrice) {
      this.resetPriceScales();
    }
    this.lastMedianPrice = currentMedian;
  }

  setStatus(status: ChartDataStatus, message?: string): void {
    this.setData([], { status, message });
  }

  private clearChartData(): void {
    this.clearPnlOverlays();
    this.candles = [];
    this.markerSignals = [];
    this.candleSeries.setData([] as CandlestickData[]);
    this.lineSeries.setData([] as LineData[]);
    this.barSeries.setData([] as BarData[]);
    this.volSeries.setData([] as HistogramData[]);
    this.bbUpperSeries.setData([] as LineData[]);
    this.bbMidSeries.setData([] as LineData[]);
    this.bbLowerSeries.setData([] as LineData[]);
    this.ema9Series.setData([] as LineData[]);
    this.ema21Series.setData([] as LineData[]);
    this.ema50Series.setData([] as LineData[]);
    this.vwapSeries.setData([] as LineData[]);
    this.rsiSeries.setData([] as LineData[]);
    this.macdLineSeries.setData([] as LineData[]);
    this.macdSigSeries.setData([] as LineData[]);
    this.macdHistSeries.setData([] as HistogramData[]);
    this.atrSeries.setData([] as LineData[]);
    this.stochKSeries.setData([] as LineData[]);
    this.stochDSeries.setData([] as LineData[]);
    this.candleSeries.setMarkers([]);
    this.infoEl.style.display = 'none';
    this.clearReferenceLines();
    this.lastMedianPrice = null;
    this.container.dataset['lastPrice'] = '';
    this.container.dataset['percentBaseTime'] = '';
    this.container.dataset['percentBaseClose'] = '';
    this.container.dataset['percentLastChange'] = '';
    this.container.dataset['chartStatus'] = this.dataStatus;
  }

  private setStatusOverlay(status: ChartDataStatus, message?: string): void {
    this.dataStatus = status;
    this.container.dataset['chartStatus'] = status;

    if (status === 'idle' || status === 'ready') {
      this.hideStatus();
      return;
    }

    const label =
      status === 'loading' ? TR.LOADING
        : status === 'empty' ? TR.NO_DATA
          : status === 'error' ? TR.CONNECTION_ERROR
            : TR.WAITING_DATA;
    const detail = message && message !== label ? `<small>${this.escapeHtml(message)}</small>` : '';
    this.stateEl.className = `chart-state-overlay state-${status}`;
    this.stateEl.innerHTML = `<strong>${label}</strong>${detail}`;
    this.stateEl.style.display = 'flex';
  }

  private hideStatus(): void {
    this.stateEl.style.display = 'none';
    this.stateEl.innerHTML = '';
    this.container.dataset['chartStatus'] = this.dataStatus;
  }

  private medianClose(candles: OHLCV[]): number | null {
    const values = candles
      .map(c => c.close)
      .filter(v => Number.isFinite(v) && v > 0)
      .sort((a, b) => a - b);
    if (values.length === 0) return null;
    const mid = Math.floor(values.length / 2);
    return values.length % 2 === 0
      ? (values[mid - 1]! + values[mid]!) / 2
      : values[mid]!;
  }

  private shouldResetPriceScale(
    reason: ChartViewOptions['reason'],
    currentMedian: number | null,
    preserveTimeRange?: boolean,
  ): boolean {
    if (!this.autoPriceScale) return false;
    if (reason === 'append') return false;
    if (reason === 'symbol' || reason === 'initial') return true;
    if (!currentMedian || !this.lastMedianPrice) return !preserveTimeRange;
    const ratio = currentMedian / this.lastMedianPrice;
    return ratio >= PRICE_SHIFT_RESET_RATIO || ratio <= 1 / PRICE_SHIFT_RESET_RATIO;
  }

  private restoreVisibleRange(range: Range<Time>): void {
    [this.mainChart, this.volChart, this.rsiChart, this.macdChart, this.atrChart, this.stochChart].forEach(chart => {
      try {
        chart.timeScale().setVisibleRange(range);
      } catch {
        // Farklı timeframe'lerde range dışarı taşarsa sessizce yeni veriye sığdır.
      }
    });
  }

  private resetPriceScales(): void {
    this.applyScaleMode();
    const mainMargins = { top: 0.08, bottom: 0.14 };
    const lowerMargins = { top: 0.1, bottom: 0.1 };
    const scaleUpdates: Array<() => void> = [
      () => this.mainChart.priceScale('right').applyOptions({ autoScale: true, scaleMargins: mainMargins }),
      () => this.candleSeries.priceScale().applyOptions({ autoScale: true, scaleMargins: mainMargins }),
      () => this.lineSeries.priceScale().applyOptions({ autoScale: true, scaleMargins: mainMargins }),
      () => this.barSeries.priceScale().applyOptions({ autoScale: true, scaleMargins: mainMargins }),
      () => this.volSeries.priceScale().applyOptions({ autoScale: true }),
      () => this.rsiChart.priceScale('right').applyOptions({ autoScale: true, scaleMargins: lowerMargins }),
      () => this.macdChart.priceScale('right').applyOptions({ autoScale: true, scaleMargins: lowerMargins }),
      () => this.rsiSeries.priceScale().applyOptions({ autoScale: true, scaleMargins: lowerMargins }),
      () => this.macdLineSeries.priceScale().applyOptions({ autoScale: true, scaleMargins: lowerMargins }),
      () => this.macdHistSeries.priceScale().applyOptions({ autoScale: true, scaleMargins: lowerMargins }),
      () => this.atrChart.priceScale('right').applyOptions({ autoScale: true, scaleMargins: lowerMargins }),
      () => this.atrSeries.priceScale().applyOptions({ autoScale: true, scaleMargins: lowerMargins }),
      () => this.stochChart.priceScale('right').applyOptions({ autoScale: true, scaleMargins: lowerMargins }),
      () => this.stochKSeries.priceScale().applyOptions({ autoScale: true, scaleMargins: lowerMargins }),
      () => this.stochDSeries.priceScale().applyOptions({ autoScale: true, scaleMargins: lowerMargins }),
    ];
    for (const update of scaleUpdates) {
      try {
        update();
      } catch {
        // Bazı overlay scale'leri görünmez olabilir; kalan scale'ler yine resetlenir.
      }
    }
    this.container.dataset['priceScaleResetAt'] = String(Date.now());
  }

  private activeMainSeries(): MainPriceSeries {
    if (this.chartType === 'line') return this.lineSeries;
    if (this.chartType === 'bar') return this.barSeries;
    return this.candleSeries;
  }

  private clearReferenceLines(): void {
    if (!this.priceLineSeries) return;
    if (this.lastPriceLine) this.priceLineSeries.removePriceLine(this.lastPriceLine);
    if (this.previousCloseLine) this.priceLineSeries.removePriceLine(this.previousCloseLine);
    this.lastPriceLine = null;
    this.previousCloseLine = null;
    this.priceLineSeries = null;
  }

  private clearPnlOverlays(): void {
    for (const series of this.tradeOverlaySeries) {
      try {
        this.mainChart.removeSeries(series);
      } catch {
        // Series daha önce grafik tarafından kaldırılmışsa kalan overlay'ler temizlenir.
      }
    }
    this.tradeOverlaySeries = [];

    for (const item of this.pnlPriceLines) {
      try {
        item.series.removePriceLine(item.line);
      } catch {
        // Aktif fiyat serisi değişmiş olabilir; sessizce devam et.
      }
    }
    this.pnlPriceLines = [];
  }

  private updateReferenceLines(): void {
    this.clearReferenceLines();
    const last = this.candles[this.candles.length - 1];
    if (!last) return;

    const series = this.activeMainSeries();
    this.priceLineSeries = series;
    const lastColor = this.chartType === 'line'
      ? C.blue
      : last.close >= last.open ? C.green : C.red;
    this.lastPriceLine = series.createPriceLine({
      id: 'last-price',
      price: this.displayPrice(last.close),
      color: lastColor,
      lineWidth: 1,
      lineStyle: LineStyle.Solid,
      axisLabelVisible: true,
      title: this.scaleMode === 'percent' ? 'Son %' : 'Son',
      axisLabelColor: lastColor,
      axisLabelTextColor: C.bg,
    });
    this.container.dataset['lastPrice'] = String(last.close);
    const base = this.currentPercentBase();
    this.container.dataset['percentBaseTime'] = base ? String(base.time) : '';
    this.container.dataset['percentBaseClose'] = base ? String(base.close) : '';
    this.container.dataset['percentLastChange'] = base ? String(this.percentChange(last.close, base.close)) : '';

    const prev = this.candles[this.candles.length - 2];
    if (this.showPreviousClose && prev) {
      this.previousCloseLine = series.createPriceLine({
        id: 'previous-close',
        price: this.displayPrice(prev.close),
        color: C.text,
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
        axisLabelVisible: true,
        title: this.scaleMode === 'percent' ? 'ÖK %' : 'ÖK',
        axisLabelColor: C.border,
        axisLabelTextColor: C.textBold,
      });
    }
  }

  private renderPnlOverlays(signals: Signal[]): void {
    this.clearPnlOverlays();
    this.container.dataset['pnlClosedCount'] = '0';
    this.container.dataset['pnlLastClosedPct'] = '';
    this.container.dataset['pnlLastClosedValue'] = '';
    this.container.dataset['pnlOpenPct'] = '';
    this.container.dataset['pnlOpenValue'] = '';
    this.container.dataset['pnlRiskReward'] = '';
    this.container.dataset['bistLimitStatus'] = 'off';

    if (!this.showPnlOverlay || this.candles.length === 0) {
      return;
    }

    const trades = this.closedTradeOverlays(signals);
    this.container.dataset['pnlClosedCount'] = String(trades.length);
    const lastClosed = trades.length ? trades[trades.length - 1] : undefined;
    if (lastClosed) {
      this.container.dataset['pnlLastClosedPct'] = String(lastClosed.returnPct);
      this.container.dataset['pnlLastClosedValue'] = String(lastClosed.netPnl);
    }

    for (const trade of trades.slice(-30)) {
      this.drawTradeConnection(trade);
    }

    const openSignal = this.openPositionSignal(signals);
    if (openSignal) {
      this.drawOpenPositionLines(openSignal);
    }

    if (this.showBistLimits) {
      this.drawBistLimitLines();
    }
  }

  private closedTradeOverlays(signals: Signal[]): PairedTradeOverlay[] {
    const enriched = signals
      .filter(signal => signal.trade_role === 'exit'
        && signal.entry_time != null
        && signal.exit_time != null
        && signal.entry_price != null
        && signal.exit_price != null)
      .map(signal => ({
        side: signal.trade_side ?? (signal.type === 'COVER' ? 'SHORT' : 'LONG'),
        entryTime: signal.entry_time!,
        exitTime: signal.exit_time!,
        entryPrice: signal.entry_price!,
        exitPrice: signal.exit_price!,
        quantity: signal.quantity,
        netPnl: signal.net_pnl ?? signal.pnl ?? 0,
        returnPct: signal.return_pct ?? this.tradeReturnPct(
          signal.trade_side ?? (signal.type === 'COVER' ? 'SHORT' : 'LONG'),
          signal.entry_price!,
          signal.exit_price!,
        ),
      } satisfies PairedTradeOverlay));

    if (enriched.length) return enriched.sort((a, b) => a.exitTime - b.exitTime);

    const paired: PairedTradeOverlay[] = [];
    const stack: Signal[] = [];
    for (const signal of signals) {
      if (signal.type === 'BUY' || signal.type === 'SHORT') {
        stack.push(signal);
      }
      if (signal.type === 'SELL' || signal.type === 'COVER') {
        const entryType = signal.type === 'COVER' ? 'SHORT' : 'BUY';
        let entryIdx = -1;
        for (let i = stack.length - 1; i >= 0; i--) {
          if (stack[i]?.type === entryType) {
            entryIdx = i;
            break;
          }
        }
        const entry = entryIdx >= 0 ? stack.splice(entryIdx, 1)[0] : undefined;
        if (!entry) continue;
        const side = entry.type === 'SHORT' ? 'SHORT' : 'LONG';
        paired.push({
          side,
          entryTime: entry.timestamp,
          exitTime: signal.timestamp,
          entryPrice: entry.price,
          exitPrice: signal.price,
          quantity: signal.quantity ?? entry.quantity,
          netPnl: signal.pnl ?? 0,
          returnPct: this.tradeReturnPct(side, entry.price, signal.price),
        });
      }
    }
    return paired.sort((a, b) => a.exitTime - b.exitTime);
  }

  private drawTradeConnection(trade: PairedTradeOverlay): void {
    const positive = trade.netPnl >= 0;
    const series = this.mainChart.addLineSeries({
      color: positive ? `${C.green}cc` : `${C.red}cc`,
      lineWidth: 2,
      lineStyle: LineStyle.Solid,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    series.setData([
      { time: trade.entryTime as UTCTimestamp, value: this.displayPrice(trade.entryPrice) },
      { time: trade.exitTime as UTCTimestamp, value: this.displayPrice(trade.exitPrice) },
    ]);
    this.tradeOverlaySeries.push(series);
  }

  private openPositionSignal(signals: Signal[]): Signal | undefined {
    return [...signals]
      .reverse()
      .find(signal => signal.open_position && (signal.type === 'BUY' || signal.type === 'SHORT'));
  }

  private drawOpenPositionLines(signal: Signal): void {
    const last = this.candles[this.candles.length - 1];
    if (!last) return;
    const entry = signal.entry_price ?? signal.price;
    const side = signal.trade_side ?? (signal.type === 'SHORT' ? 'SHORT' : 'LONG');
    const qty = signal.quantity ?? 0;
    const openPct = this.tradeReturnPct(side, entry, last.close);
    const openValue = qty > 0
      ? (side === 'SHORT' ? (entry - last.close) : (last.close - entry)) * qty
      : 0;
    const lineTitle = `Maliyet ${openPct >= 0 ? '+' : ''}${formatNumber(openPct, 1)}%`;
    const series = this.activeMainSeries();

    this.addOverlayPriceLine(series, entry, openPct >= 0 ? C.green : C.red, lineTitle, true);
    this.container.dataset['pnlOpenPct'] = String(openPct);
    this.container.dataset['pnlOpenValue'] = String(openValue);

    if (this.showRiskLines) {
      if (signal.stop_price) {
        this.addOverlayPriceLine(series, signal.stop_price, C.red, 'Stop', false);
      }
      if (signal.take_profit_price) {
        this.addOverlayPriceLine(series, signal.take_profit_price, C.green, 'Hedef', false);
      }
      if (signal.risk_reward) {
        this.container.dataset['pnlRiskReward'] = String(signal.risk_reward);
      }
    }
  }

  private drawBistLimitLines(): void {
    if (!this.lastSymbol.endsWith('.IS')) return;
    const prev = this.candles[this.candles.length - 2];
    if (!prev || prev.close <= 0) {
      this.container.dataset['bistLimitStatus'] = 'passive';
      return;
    }
    const series = this.activeMainSeries();
    this.addOverlayPriceLine(series, prev.close * 1.10, C.text, 'Tavan', false);
    this.addOverlayPriceLine(series, prev.close * 0.90, C.text, 'Taban', false);
    this.container.dataset['bistLimitStatus'] = 'active';
  }

  private addOverlayPriceLine(
    series: MainPriceSeries,
    price: number,
    color: string,
    title: string,
    strong: boolean,
  ): void {
    const line = series.createPriceLine({
      price: this.displayPrice(price),
      color,
      lineWidth: strong ? 2 : 1,
      lineStyle: strong ? LineStyle.Solid : LineStyle.Dashed,
      axisLabelVisible: true,
      title,
      axisLabelColor: strong ? color : C.border,
      axisLabelTextColor: strong ? C.bg : C.textBold,
    });
    this.pnlPriceLines.push({ series, line });
  }

  private tradeReturnPct(side: 'LONG' | 'SHORT', entry: number, exit: number): number {
    if (!Number.isFinite(entry) || entry <= 0 || !Number.isFinite(exit)) return 0;
    return side === 'SHORT'
      ? ((entry - exit) / entry) * 100
      : ((exit - entry) / entry) * 100;
  }

  private escapeHtml(value: string): string {
    return value
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  // ─── Backtest / strateji sinyallerini mum üstünde göster ─────────────────
  // ▲ yeşil = AL, ▼ kırmızı = SAT, ▼ turuncu = SHORT, ▲ mavi = COVER.
  // Sembol ya da timeframe değişince çağrı tarafı `clearSignals()` etmeli.

  setSignals(signals: Signal[]): void {
    this.markerSignals = signals;
    const markers: SeriesMarker<UTCTimestamp>[] = signals
      .filter(s => ['BUY', 'SELL', 'SHORT', 'COVER'].includes(s.type))
      .map(s => {
        const cfg = {
          BUY:   { position: 'belowBar', color: C.green,  shape: 'arrowUp',   label: 'AL' },
          SELL:  { position: 'aboveBar', color: C.red,    shape: 'arrowDown', label: 'SAT' },
          SHORT: { position: 'aboveBar', color: C.orange, shape: 'arrowDown', label: 'SHORT' },
          COVER: { position: 'belowBar', color: C.blue,   shape: 'arrowUp',   label: 'COVER' },
          HOLD:  { position: 'belowBar', color: C.text,   shape: 'circle',    label: 'BEKLE' },
        }[s.type];
        return {
          time: s.timestamp as UTCTimestamp,
          position: cfg.position as SeriesMarker<UTCTimestamp>['position'],
          color: cfg.color,
          shape: cfg.shape as SeriesMarker<UTCTimestamp>['shape'],
          text: `${s.open_position ? 'AÇIK ' : ''}${cfg.label} ${formatNumber(s.price)}${s.return_pct != null ? ` ${s.return_pct >= 0 ? '+' : ''}${formatNumber(s.return_pct, 1)}%` : ''}`,
        };
      });
    this.candleSeries.setMarkers(markers);
    this.renderPnlOverlays(signals);
  }

  clearSignals(): void {
    this.markerSignals = [];
    this.candleSeries.setMarkers([]);
    this.clearPnlOverlays();
  }

  focusTime(timestamp: number): void {
    if (this.candles.length === 0) return;
    const idx = this.candles.findIndex(c => c.time >= timestamp);
    const center = idx >= 0 ? idx : this.candles.length - 1;
    const fromIdx = Math.max(0, center - 20);
    const toIdx = Math.min(this.candles.length - 1, center + 20);
    const range = {
      from: this.candles[fromIdx]!.time as UTCTimestamp,
      to: this.candles[toIdx]!.time as UTCTimestamp,
    };
    [this.mainChart, this.volChart, this.rsiChart, this.macdChart, this.atrChart, this.stochChart].forEach(chart => {
      chart.timeScale().setVisibleRange(range);
    });
  }

  updateLastCandle(candle: OHLCV): void {
    if (this.candles.length === 0) {
      this.setData([candle], { reason: 'append', preserveTimeRange: true });
      return;
    }
    const idx = this.candles.findIndex(c => c.time === candle.time);
    if (idx >= 0) {
      this.candles[idx] = candle;
    } else {
      this.candles = [...this.candles, candle];
    }

    this.ensurePercentBase(this.candles);
    const data = this.chartCandle(candle);
    this.candleSeries.update(data);
    this.lineSeries.update({ time: candle.time as UTCTimestamp, value: this.displayPrice(candle.close) } as LineData);
    this.barSeries.update(data as BarData);

    const vol: HistogramData = {
      time: candle.time as UTCTimestamp,
      value: candle.volume,
      color: candle.close >= candle.open ? C.green + '90' : C.red + '90',
    };
    this.volSeries.update(vol);
    this.dataStatus = 'ready';
    this.hideStatus();
    this.updateReferenceLines();
    this.renderPnlOverlays(this.markerSignals);
  }

  private renderVolume(candles: OHLCV[]): void {
    const data: HistogramData[] = candles.map(c => ({
      time: c.time as UTCTimestamp,
      value: c.volume,
      color: c.close >= c.open ? C.green + '90' : C.red + '90',
    }));
    this.volSeries.setData(data);
  }

  private renderIndicators(candles: OHLCV[]): void {
    const inds = computeIndicators(candles, this.indicatorParams);
    const times = candles.map(c => c.time as UTCTimestamp);

    const lineData = (arr: number[] | undefined, normalize = false): LineData[] =>
      arr
        ? arr.map((v, i) => ({
          time: times[i]!,
          value: normalize ? this.displayPrice(v) : v,
        })).filter(d => !isNaN(d.value)) as LineData[]
        : [];

    this.bbUpperSeries.setData(lineData(inds.bb?.upper, true));
    this.bbMidSeries.setData(lineData(inds.bb?.mid, true));
    this.bbLowerSeries.setData(lineData(inds.bb?.lower, true));
    this.ema9Series.setData(lineData(inds.ema9, true));
    this.ema21Series.setData(lineData(inds.ema21, true));
    this.ema50Series.setData(lineData(inds.ema50, true));
    this.vwapSeries.setData(lineData(inds.vwap, true));

    this.rsiSeries.setData(lineData(inds.rsi));
    this.atrSeries.setData(lineData(inds.atr));
    this.stochKSeries.setData(lineData(inds.stochastic?.k));
    this.stochDSeries.setData(lineData(inds.stochastic?.d));

    if (inds.macd) {
      this.macdLineSeries.setData(lineData(inds.macd.macd));
      this.macdSigSeries.setData(lineData(inds.macd.signal));

      const histData: HistogramData[] = inds.macd.histogram
        .map((v, i) => ({ time: times[i]!, value: v, color: v >= 0 ? C.green + '99' : C.red + '99' }))
        .filter(d => !isNaN(d.value)) as HistogramData[];
      this.macdHistSeries.setData(histData);
    }

    this.updateIndicatorVisibility();
  }

  private setScaleMode(mode: ChartScaleMode): void {
    if (!['linear', 'log', 'percent'].includes(mode)) return;
    if (mode === this.scaleMode) return;

    this.scaleMode = mode;
    this.ensurePercentBase(this.candles);
    this.applyScaleMode();
    this.updateScaleButtons();
    this.updateUnitBadge();
    this.rerenderPriceData();
    this.resetPriceScales();
  }

  private applyScaleMode(): void {
    const mode = this.scaleMode === 'log'
      ? PriceScaleMode.Logarithmic
      : PriceScaleMode.Normal;
    const updates: Array<() => void> = [
      () => this.mainChart.priceScale('right').applyOptions({ mode }),
      () => this.candleSeries.priceScale().applyOptions({ mode }),
      () => this.lineSeries.priceScale().applyOptions({ mode }),
      () => this.barSeries.priceScale().applyOptions({ mode }),
      () => this.bbUpperSeries.priceScale().applyOptions({ mode }),
      () => this.bbMidSeries.priceScale().applyOptions({ mode }),
      () => this.bbLowerSeries.priceScale().applyOptions({ mode }),
      () => this.ema9Series.priceScale().applyOptions({ mode }),
      () => this.ema21Series.priceScale().applyOptions({ mode }),
      () => this.ema50Series.priceScale().applyOptions({ mode }),
      () => this.vwapSeries.priceScale().applyOptions({ mode }),
    ];
    for (const update of updates) {
      try {
        update();
      } catch {
        // Overlay scale hazır değilse kalan scale'ler uygulanmaya devam eder.
      }
    }
    this.container.dataset['chartScaleMode'] = this.scaleMode;
  }

  private updateScaleButtons(): void {
    this.container.querySelectorAll<HTMLElement>('.scale-mode-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset['scaleMode'] === this.scaleMode);
    });
    const baseBtn = this.container.querySelector<HTMLElement>('#scale-base-btn');
    baseBtn?.classList.toggle('active', this.scaleMode === 'percent');
  }

  private updateUnitBadge(): void {
    const badge = this.container.querySelector<HTMLElement>('#chart-unit-badge');
    if (!badge) return;
    badge.textContent = this.scaleMode === 'percent' ? '%' : this.unitLabel;
  }

  private inferUnit(symbol: string): string {
    if (symbol.endsWith('.IS')) return 'TRY';
    if (symbol.endsWith('USDT')) return 'USDT';
    if (symbol.includes('USD') || symbol.endsWith('=X')) return 'USD';
    return '';
  }

  private ensurePercentBase(candles: OHLCV[]): void {
    if (!candles.length) {
      this.percentBaseTime = null;
      this.percentBaseClose = null;
      return;
    }
    const current = this.currentPercentBase(candles);
    if (current) {
      this.percentBaseTime = current.time;
      this.percentBaseClose = current.close;
      return;
    }
    const first = candles.find(c => Number.isFinite(c.close) && c.close > 0) ?? candles[0]!;
    this.percentBaseTime = first.time;
    this.percentBaseClose = first.close;
  }

  private currentPercentBase(candles = this.candles): OHLCV | null {
    if (!candles.length) return null;
    const byTime = this.percentBaseTime == null
      ? undefined
      : candles.find(c => c.time === this.percentBaseTime && c.close > 0);
    if (byTime) return byTime;
    return candles.find(c => Number.isFinite(c.close) && c.close > 0) ?? null;
  }

  private setPercentageBase(time: number): void {
    const candle = this.candles.find(c => c.time === time);
    if (!candle || candle.close <= 0) return;
    this.percentBaseTime = candle.time;
    this.percentBaseClose = candle.close;
    this.rerenderPriceData();
    this.resetPriceScales();
  }

  private setPercentageBaseFromVisibleStart(): void {
    if (this.scaleMode !== 'percent') {
      this.setScaleMode('percent');
      return;
    }
    const range = this.mainChart.timeScale().getVisibleLogicalRange();
    const idx = range ? Math.max(0, Math.floor(range.from)) : 0;
    const candle = this.candles[Math.min(idx, this.candles.length - 1)];
    if (candle) this.setPercentageBase(candle.time);
  }

  private rerenderPriceData(): void {
    if (!this.candles.length || this.dataStatus !== 'ready') return;
    const savedVisibleRange = this.mainChart.timeScale().getVisibleRange();
    this.candleSeries.setData(this.chartCandles(this.candles));
    this.lineSeries.setData(this.chartLineData(this.candles));
    this.barSeries.setData(this.chartCandles(this.candles) as BarData[]);
    this.renderIndicators(this.candles);
    this.updateReferenceLines();
    this.renderPnlOverlays(this.markerSignals);
    if (savedVisibleRange) this.restoreVisibleRange(savedVisibleRange);
    this.updateUnitBadge();
  }

  private chartCandles(candles: OHLCV[]): CandlestickData[] {
    return candles.map(c => this.chartCandle(c));
  }

  private chartCandle(candle: OHLCV): CandlestickData {
    return {
      time: candle.time as UTCTimestamp,
      open: this.displayPrice(candle.open),
      high: this.displayPrice(candle.high),
      low: this.displayPrice(candle.low),
      close: this.displayPrice(candle.close),
    };
  }

  private chartLineData(candles: OHLCV[]): LineData[] {
    return candles.map(c => ({
      time: c.time as UTCTimestamp,
      value: this.displayPrice(c.close),
    }));
  }

  private displayPrice(value: number): number {
    if (this.scaleMode !== 'percent') return value;
    const base = this.percentBaseClose ?? this.currentPercentBase()?.close;
    return base && base > 0 ? this.percentChange(value, base) : value;
  }

  private percentChange(value: number, base: number): number {
    if (!Number.isFinite(value) || !Number.isFinite(base) || base <= 0) return NaN;
    return ((value / base) - 1) * 100;
  }

  private loadIndicatorPrefs(): void {
    try {
      const active = JSON.parse(localStorage.getItem(LS_ACTIVE_INDICATORS) || '[]') as string[];
      if (Array.isArray(active) && active.length) {
        const valid = active.map(key => this.normalizeIndicatorKey(key)).filter(Boolean);
        if (valid.length) this.activeIndicators = new Set(valid);
      }

      const params = JSON.parse(localStorage.getItem(LS_INDICATOR_PARAMS) || '{}') as Record<string, number>;
      this.indicatorParams = {
        ...DEFAULT_INDICATOR_PARAMS,
        ...Object.fromEntries(
          Object.entries(params).filter(([, value]) => Number.isFinite(value)),
        ),
      };

      const favorites = JSON.parse(localStorage.getItem(LS_FAVORITE_INDICATORS) || '[]') as string[];
      this.favoriteIndicators = new Set(favorites.map(key => this.normalizeIndicatorKey(key)).filter(Boolean));
    } catch {
      this.activeIndicators = new Set(DEFAULT_ACTIVE_INDICATORS);
      this.indicatorParams = { ...DEFAULT_INDICATOR_PARAMS };
      this.favoriteIndicators = new Set();
    }
  }

  private saveIndicatorPrefs(): void {
    localStorage.setItem(LS_ACTIVE_INDICATORS, JSON.stringify(Array.from(this.activeIndicators)));
    localStorage.setItem(LS_INDICATOR_PARAMS, JSON.stringify(this.indicatorParams));
    localStorage.setItem(LS_FAVORITE_INDICATORS, JSON.stringify(Array.from(this.favoriteIndicators)));
  }

  private bindIndicatorCenter(): void {
    this.indicatorCenterEl.addEventListener('input', (evt) => {
      const target = evt.target;
      if (target instanceof HTMLInputElement && target.id === 'indicator-search') {
        this.indicatorQuery = target.value;
        this.renderIndicatorCenter();
        return;
      }

      if (target instanceof HTMLInputElement && target.dataset['indicatorParam']) {
        const key = target.dataset['indicatorParam'] as keyof IndicatorCalculationOptions;
        const value = Number(target.value);
        if (!Number.isFinite(value)) return;
        this.indicatorParams[key] = value;
        this.saveIndicatorPrefs();
        this.renderIndicators(this.candles);
        this.updateIndicatorVisibility();
      }
    });

    this.indicatorCenterEl.addEventListener('click', (evt) => {
      const target = evt.target as HTMLElement;
      const closeBtn = target.closest<HTMLElement>('[data-indicator-close]');
      if (closeBtn) {
        this.indicatorPanelOpen = false;
        this.renderIndicatorCenter();
        return;
      }

      const categoryBtn = target.closest<HTMLElement>('[data-indicator-category]');
      if (categoryBtn) {
        this.indicatorCategory = categoryBtn.dataset['indicatorCategory'] as IndicatorCategory | 'all';
        this.renderIndicatorCenter();
        return;
      }

      const groupBtn = target.closest<HTMLElement>('[data-indicator-group]');
      if (groupBtn) {
        const group = INDICATOR_GROUPS.find(item => item.id === groupBtn.dataset['indicatorGroup']);
        if (!group) return;
        group.keys.forEach(key => this.activeIndicators.add(key));
        this.saveIndicatorPrefs();
        this.updateIndicatorButtons();
        this.updateIndicatorVisibility();
        this.renderIndicatorCenter();
        return;
      }

      const toggleBtn = target.closest<HTMLElement>('[data-indicator-toggle]');
      if (toggleBtn) {
        const key = this.normalizeIndicatorKey(toggleBtn.dataset['indicatorToggle'] || '');
        if (!key) return;
        if (this.activeIndicators.has(key)) this.activeIndicators.delete(key);
        else this.activeIndicators.add(key);
        this.saveIndicatorPrefs();
        this.updateIndicatorButtons();
        this.updateIndicatorVisibility();
        this.renderIndicatorCenter();
        return;
      }

      const favoriteBtn = target.closest<HTMLElement>('[data-indicator-favorite]');
      if (favoriteBtn) {
        const key = this.normalizeIndicatorKey(favoriteBtn.dataset['indicatorFavorite'] || '');
        if (!key) return;
        if (this.favoriteIndicators.has(key)) this.favoriteIndicators.delete(key);
        else this.favoriteIndicators.add(key);
        this.saveIndicatorPrefs();
        this.renderIndicatorCenter();
      }
    });
  }

  private renderIndicatorCenter(): void {
    if (!this.indicatorCenterEl) return;
    this.indicatorCenterEl.hidden = !this.indicatorPanelOpen;
    this.container.querySelector('#indicator-center-btn')?.classList.toggle('active', this.indicatorPanelOpen);
    if (!this.indicatorPanelOpen) {
      this.indicatorCenterEl.innerHTML = '';
      return;
    }

    const query = this.indicatorQuery.trim().toLocaleLowerCase('tr-TR');
    const defs = INDICATOR_DEFS.filter(def => {
      const categoryOk = this.indicatorCategory === 'all' || def.category === this.indicatorCategory;
      const queryOk = !query || [def.key, def.label, def.description].join(' ').toLocaleLowerCase('tr-TR').includes(query);
      return categoryOk && queryOk;
    });
    const activeDefs = INDICATOR_DEFS.filter(def => this.activeIndicators.has(def.key));

    this.indicatorCenterEl.innerHTML = `
      <div class="indicator-center-head">
        <div>
          <b>İndikatörler</b>
          <span>${activeDefs.length} aktif</span>
        </div>
        <button class="ctrl-btn" data-indicator-close title="Kapat">×</button>
      </div>
      <input id="indicator-search" class="indicator-search" type="search" value="${this.escapeHtml(this.indicatorQuery)}" placeholder="Ara: ATR, Stochastic, RSI" autocomplete="off">
      <div class="indicator-category-row">
        ${INDICATOR_CATEGORIES.map(category => `
          <button class="ctrl-btn indicator-category${category.id === this.indicatorCategory ? ' active' : ''}" data-indicator-category="${category.id}">
            ${category.label}
          </button>
        `).join('')}
      </div>
      <div class="indicator-group-row">
        ${INDICATOR_GROUPS.map(group => `
          <button class="ctrl-btn" data-indicator-group="${group.id}">${group.label}</button>
        `).join('')}
      </div>
      <div class="indicator-active-list">
        ${activeDefs.map(def => `<span>${def.label}</span>`).join('') || '<span>Aktif indikatör yok</span>'}
      </div>
      <div class="indicator-def-list">
        ${defs.map(def => this.indicatorDefinitionHTML(def)).join('') || '<div class="empty-state">Eşleşen indikatör yok</div>'}
      </div>
    `;
    const search = this.indicatorCenterEl.querySelector<HTMLInputElement>('#indicator-search');
    search?.focus();
  }

  private indicatorDefinitionHTML(def: IndicatorDefinition): string {
    const active = this.activeIndicators.has(def.key);
    const favorite = this.favoriteIndicators.has(def.key);
    return `
      <section class="indicator-def${active ? ' active' : ''}">
        <div class="indicator-def-main">
          <button class="indicator-fav${favorite ? ' active' : ''}" data-indicator-favorite="${def.key}" title="Favori">${favorite ? '★' : '☆'}</button>
          <div>
            <b>${def.label}</b>
            <span>${this.indicatorCategoryLabel(def.category)} · ${def.region === 'overlay' ? 'Ana grafik' : 'Alt panel'}</span>
            <small>${def.description}</small>
          </div>
          <button class="ctrl-btn" data-indicator-toggle="${def.key}">${active ? 'Kapat' : 'Ekle'}</button>
        </div>
        ${def.params?.length ? `
          <div class="indicator-param-grid">
            ${def.params.map(param => `
              <label>${param.label}
                <input
                  type="number"
                  min="${param.min}"
                  max="${param.max}"
                  step="${param.step}"
                  value="${this.indicatorParams[param.key]}"
                  data-indicator-param="${param.key}"
                >
              </label>
            `).join('')}
          </div>
        ` : ''}
      </section>
    `;
  }

  private indicatorCategoryLabel(category: IndicatorCategory): string {
    return INDICATOR_CATEGORIES.find(item => item.id === category)?.label ?? category;
  }

  private updateIndicatorVisibility(): void {
    const has = (k: string) => this.activeIndicators.has(k);
    const bb = has('bb');
    const ema = has('ema');
    this.bbUpperSeries.applyOptions({ visible: bb });
    this.bbMidSeries.applyOptions({ visible: bb });
    this.bbLowerSeries.applyOptions({ visible: bb });
    this.ema9Series.applyOptions({ visible: ema });
    this.ema21Series.applyOptions({ visible: ema });
    this.ema50Series.applyOptions({ visible: ema });
    this.vwapSeries.applyOptions({ visible: has('vwap') });
    this.rsiEl.style.display  = has('rsi')  ? '' : 'none';
    this.macdEl.style.display = has('macd') ? '' : 'none';
    this.volEl.style.display  = has('vol')  ? '' : 'none';
    this.atrEl.style.display  = has('atr')  ? '' : 'none';
    this.stochEl.style.display = has('stoch') ? '' : 'none';
    this.container.dataset['activeIndicators'] = Array.from(this.activeIndicators).sort().join(',');
    this.container.dataset['indicatorAtrPeriod'] = String(this.indicatorParams.atrPeriod);
    this.container.dataset['indicatorStochK'] = String(this.indicatorParams.stochasticKPeriod);
    this.container.dataset['indicatorStochD'] = String(this.indicatorParams.stochasticDPeriod);
    this.resizeCharts();
  }

  setIndicatorActive(indicator: string, active = true): void {
    const key = this.normalizeIndicatorKey(indicator);
    if (!key) return;
    if (active) this.activeIndicators.add(key);
    else this.activeIndicators.delete(key);
    this.saveIndicatorPrefs();
    this.updateIndicatorButtons();
    this.renderIndicatorCenter();
    this.updateIndicatorVisibility();
  }

  private normalizeIndicatorKey(indicator: string): string {
    const key = indicator.trim().toLowerCase();
    const aliases: Record<string, string> = {
      bollinger: 'bb',
      bollinger_bands: 'bb',
      'bollinger-bands': 'bb',
      sma: 'ema',
      ma: 'ema',
      stochastic: 'stoch',
    };
    const normalized = aliases[key] ?? key;
    return ['bb', 'ema', 'vwap', 'rsi', 'macd', 'vol', 'atr', 'stoch'].includes(normalized)
      ? normalized
      : '';
  }

  private updateIndicatorButtons(): void {
    this.container.querySelectorAll<HTMLElement>('.ind-btn').forEach(btn => {
      const ind = btn.dataset['ind'];
      btn.classList.toggle('active', !!ind && this.activeIndicators.has(ind));
    });
  }

  // ─── Chart type switching ───────────────────────────────────────────────

  setChartType(type: ChartType): void {
    this.chartType = type;
    this.candleSeries.applyOptions({ visible: type === 'candlestick' });
    this.lineSeries.applyOptions({ visible: type === 'line' });
    this.barSeries.applyOptions({ visible: type === 'bar' });
    this.updateReferenceLines();
  }

  // ─── Crosshair info overlay ────────────────────────────────────────────

  private updateInfoOverlay(c: OHLCV, inds: IndicatorSet, i: number): void {
    const rsi   = lastValid(inds.rsi?.slice(0, i + 1)) ?? null;
    const macd  = inds.macd?.macd[i];
    const ema9  = inds.ema9?.[i];
    const ema21 = inds.ema21?.[i];
    const atr   = inds.atr?.[i];
    const marker = this.markerSignals.find(s => s.timestamp === c.time);
    const base = this.currentPercentBase();
    const basePct = base ? this.percentChange(c.close, base.close) : null;
    const prev = i > 0 ? this.candles[i - 1] : null;
    const prevPct = prev ? this.percentChange(c.close, prev.close) : null;

    const fmt = (v: number | null | undefined) => v != null && !isNaN(v) ? formatNumber(v, 2) : '—';
    const fmtPct = (v: number | null | undefined) => v != null && !isNaN(v) ? `${v >= 0 ? '+' : ''}${formatNumber(v, 2)}%` : '—';

    this.infoEl.style.display = 'block';
    this.infoEl.innerHTML = `
      <div class="ci-row"><span>O</span><b style="color:${C.textBold}">${fmt(c.open)}</b></div>
      <div class="ci-row"><span>H</span><b style="color:${C.green}">${fmt(c.high)}</b></div>
      <div class="ci-row"><span>L</span><b style="color:${C.red}">${fmt(c.low)}</b></div>
      <div class="ci-row"><span>C</span><b style="color:${c.close >= c.open ? C.green : C.red}">${fmt(c.close)}</b></div>
      <div class="ci-row"><span>V</span><b>${fmt(c.volume)}</b></div>
      ${this.scaleMode === 'percent' ? `<div class="ci-row"><span>Baz%</span><b style="color:${(basePct ?? 0) >= 0 ? C.green : C.red}">${fmtPct(basePct)}</b></div>` : ''}
      ${this.scaleMode === 'percent' ? `<div class="ci-row"><span>ÖK%</span><b>${fmtPct(prevPct)}</b></div>` : ''}
      ${rsi   != null ? `<div class="ci-row"><span>RSI</span><b style="color:${C.purple}">${formatNumber(rsi, 1)}</b></div>` : ''}
      ${macd  != null && !isNaN(macd) ? `<div class="ci-row"><span>MACD</span><b style="color:${C.blue}">${fmt(macd)}</b></div>` : ''}
      ${ema9  != null && !isNaN(ema9)  ? `<div class="ci-row"><span>EMA9</span><b style="color:${C.yellow}">${fmt(ema9)}</b></div>` : ''}
      ${ema21 != null && !isNaN(ema21) ? `<div class="ci-row"><span>EMA21</span><b style="color:${C.orange}">${fmt(ema21)}</b></div>` : ''}
      ${atr   != null && !isNaN(atr)   ? `<div class="ci-row"><span>ATR</span><b style="color:${C.yellow}">${fmt(atr)}</b></div>` : ''}
      ${marker ? `
        <div class="ci-signal">
          <b>${marker.type}</b> ${fmt(marker.price)}
          ${marker.quantity ? `<span>Adet ${formatNumber(marker.quantity, 0)}</span>` : ''}
          ${marker.entry_price != null ? `<span>Giriş ${fmt(marker.entry_price)}</span>` : ''}
          ${marker.exit_price != null ? `<span>Çıkış ${fmt(marker.exit_price)}</span>` : ''}
          ${marker.return_pct != null ? `<span class="${marker.return_pct >= 0 ? 'pos' : 'neg'}">Getiri ${fmtPct(marker.return_pct)}</span>` : ''}
          ${marker.pnl != null ? `<span class="${marker.pnl >= 0 ? 'pos' : 'neg'}">Net K/Z ${formatNumber(marker.pnl, 2)}</span>` : ''}
          ${marker.equity != null ? `<span>Equity ${formatNumber(marker.equity, 2)}</span>` : ''}
          ${marker.risk_reward != null ? `<span>R/R ${formatNumber(marker.risk_reward, 2)}</span>` : ''}
          <small>${marker.reason}</small>
        </div>
      ` : ''}
      <div class="ci-time">${formatDateTime(c.time)}</div>
    `;
  }

  // ─── Fullscreen ─────────────────────────────────────────────────────────

  private bindFullscreen(): void {
    document.addEventListener('fullscreenchange', () => this.onFullscreenChange());
  }

  toggleFullscreen(): void {
    if (!document.fullscreenElement) {
      this.container.requestFullscreen().catch(() => {
        // Fallback: CSS fullscreen
        this.container.classList.add('css-fullscreen');
        this.isFullscreen = true;
        this.resizeCharts();
      });
    } else {
      document.exitFullscreen();
    }
  }

  private onFullscreenChange(): void {
    if (document.fullscreenElement === this.container) {
      this.isFullscreen = true;
    } else {
      this.isFullscreen = false;
      this.container.classList.remove('css-fullscreen');
    }
    this.resizeCharts();
  }

  private bindKeyboard(): void {
    document.addEventListener('keydown', (e) => {
      if (e.key === 'f' || e.key === 'F') this.toggleFullscreen();
      if (e.key === 'Escape' && this.isFullscreen) {
        if (!document.fullscreenElement) {
          this.container.classList.remove('css-fullscreen');
          this.isFullscreen = false;
          this.resizeCharts();
        }
      }
    });
  }

  // ─── Responsive resize ──────────────────────────────────────────────────

  private bindResize(): void {
    let timer: ReturnType<typeof setTimeout>;
    this.resizeObserver = new ResizeObserver(() => {
      clearTimeout(timer);
      timer = setTimeout(() => this.resizeCharts(), 150);
    });
    this.resizeObserver.observe(this.container);
  }

  private resizeCharts(): void {
    const w = this.isFullscreen ? window.innerWidth  : this.container.offsetWidth;
    const h = this.isFullscreen ? window.innerHeight : this.container.offsetHeight;

    const controlsH = (this.container.querySelector('.chart-controls') as HTMLElement)?.offsetHeight ?? 40;
    const available = h - controlsH;

    const mainH  = Math.floor(available * 0.50);
    const volH   = Math.floor(available * 0.09);
    const rsiH   = Math.floor(available * 0.11);
    const macdH  = Math.floor(available * 0.11);
    const atrH   = Math.floor(available * 0.09);
    const stochH = Math.floor(available * 0.10);

    this.mainChart.resize(w, mainH);
    this.volChart.resize(w, volH);
    this.rsiChart.resize(w, rsiH);
    this.macdChart.resize(w, macdH);
    this.atrChart.resize(w, atrH);
    this.stochChart.resize(w, stochH);
  }

  // ─── Cleanup ─────────────────────────────────────────────────────────────

  destroy(): void {
    this.drawingManager?.destroy();
    this.resizeObserver.disconnect();
    this.mainChart.remove();
    this.volChart.remove();
    this.rsiChart.remove();
    this.macdChart.remove();
    this.atrChart.remove();
    this.stochChart.remove();
  }
}
