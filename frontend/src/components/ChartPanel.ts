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
import type { OHLCV, Timeframe, ChartType, IndicatorSet, Signal, ChartDataStatus, ChartViewOptions, ChartTemplate, ChartEvent, ChartEventType } from '../types.js';
import { computeIndicators, lastValid, type IndicatorCalculationOptions } from '../indicators/index.js';
import { TR, formatNumber, formatDateTime } from '../constants/tr.js';
import { ALL_SYMBOLS } from '../constants/symbols.js';
import { DrawingManager } from './DrawingManager.js';

// ─── Theme constants ──────────────────────────────────────────────────────────

const C = {
  bg:       '#0B0E14',
  panel:    '#131722',
  border:   'rgba(255, 255, 255, 0.08)',
  borderSolid: '#222834',
  text:     '#94A3B8',
  textBold: '#F8FAFC',
  green:    '#10B981',
  red:      '#EF4444',
  blue:     '#3B82F6',
  purple:   '#A855F7',
  yellow:   '#F59E0B',
  orange:   '#F97316',
};

const COMPARE_COLOR = '#F2B84B';
const COMPARE_DOWN_COLOR = '#C084FC';

function cssVar(name: string, fallback: string): string {
  if (typeof window === 'undefined') return fallback;
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;
}

function chartThemeColors(): typeof C {
  return {
    ...C,
    bg: cssVar('--bg', C.bg),
    panel: cssVar('--panel', C.panel),
    border: cssVar('--border', C.border),
    borderSolid: cssVar('--border2', C.borderSolid),
    text: cssVar('--text', C.text),
    textBold: cssVar('--text-bold', C.textBold),
    green: cssVar('--green', C.green),
    red: cssVar('--red', C.red),
    blue: cssVar('--blue', C.blue),
    purple: cssVar('--purple', C.purple),
    yellow: cssVar('--yellow', C.yellow),
    orange: cssVar('--orange', C.orange),
  };
}

function chartOptions() {
  const theme = chartThemeColors();
  return {
    layout:     { background: { type: ColorType.Solid, color: theme.bg }, textColor: theme.text, attributionLogo: false },
    grid:       { vertLines: { color: theme.border }, horzLines: { color: theme.border } },
    crosshair:  { mode: CrosshairMode.Normal },
    timeScale:  { borderColor: theme.border, timeVisible: true, secondsVisible: false },
    rightPriceScale: { borderColor: theme.border },
    leftPriceScale: { borderColor: theme.border, visible: false },
    handleScroll: { mouseWheel: true, pressedMouseMove: true },
    handleScale:  { axisPressedMouseMove: true, mouseWheel: true, pinch: true },
  };
}

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
  kairiPeriod: 14,
  mostPeriod: 3,
  mostPercent: 2.0,
  gmma: true,
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
  {
    key: 'kairi',
    label: 'Kairi Relative Index',
    category: 'momentum',
    region: 'overlay', // or panel
    description: 'Fiyatın hareketli ortalamadan sapma yüzdesi.',
    params: [{ key: 'kairiPeriod', label: 'Periyot', min: 2, max: 100, step: 1 }],
  },
  {
    key: 'most',
    label: 'MOST',
    category: 'trend',
    region: 'overlay',
    description: 'Hareketli ortalama bazlı takip eden stop mekanizması.',
    params: [
      { key: 'mostPeriod', label: 'Periyot', min: 2, max: 100, step: 1 },
      { key: 'mostPercent', label: '% Yüzde', min: 0.1, max: 10, step: 0.1 },
    ],
  },
  {
    key: 'bbw',
    label: 'BB Width',
    category: 'volatility',
    region: 'overlay', // or panel
    description: 'Bollinger bantları daralma genişleme.',
    // params can share bb params
  },
  {
    key: 'gmma',
    label: 'Guppy MMA',
    category: 'trend',
    region: 'overlay',
    description: 'Çoklu üstel hareketli ortalama şelalesi.',
  },
];
const INDICATOR_GROUPS: Array<{ id: string; label: string; keys: string[] }> = [
  { id: 'trend', label: 'Trend Seti', keys: ['ema', 'vwap', 'macd'] },
  { id: 'mean-reversion', label: 'Mean Reversion', keys: ['bb', 'rsi', 'stoch'] },
  { id: 'momentum', label: 'Momentum', keys: ['rsi', 'macd', 'stoch', 'atr'] },
];
const EVENT_FILTER_TYPES: ChartEventType[] = ['haber', 'kap', 'bilanco', 'temettu', 'sermaye'];

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

  // Yeni indikatör serileri
  private kairiSeries?: ISeriesApi<'Line'>;
  private mostSeries?: ISeriesApi<'Line'>;
  private mostEmaSeries?: ISeriesApi<'Line'>;
  private bbwSeries?:   ISeriesApi<'Line'>;
  private gmmaSeriesDict: { [key: string]: ISeriesApi<'Line'> } = {};

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
  private handleThemeChange = (): void => this.applyThemeOptions();

  // G6: Multi-symbol comparison
  private compareSeries: any = null;
  private compareCandles: OHLCV[] = [];
  private comparePercentBaseClose: number | null = null;
  private compareSuggestionIndex = 0;

  // G9: Event markers
  private chartEvents: ChartEvent[] = [];
  private activeEventTypes: Set<ChartEventType> = new Set(EVENT_FILTER_TYPES);
  private eventTooltipEl: HTMLElement | null = null;
  private eventMarkerEls: Map<string, HTMLElement> = new Map();

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
    window.addEventListener('piyasapilot:theme-change', this.handleThemeChange);

    // G8: Load default template
    const defaultTpl = localStorage.getItem('piyasapilot_default_template');
    if (defaultTpl) {
      setTimeout(() => this.loadTemplate(defaultTpl), 0);
    }
  }

  // ─── DOM scaffolding ────────────────────────────────────────────────────

  private buildDOM(): void {
    this.container.innerHTML = '';
    this.container.style.cssText = 'display:flex;flex-direction:column;height:100%;position:relative;background:var(--bg);';

    // Controls bar
    const controls = document.createElement('div');
    controls.className = 'chart-controls';
    controls.innerHTML = this.controlsHTML();
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
    this.mainEl  = this.addChartRow('64%');
    this.volEl   = this.addChartRow('7%');
    this.rsiEl   = this.addChartRow('9%');
    this.macdEl  = this.addChartRow('9%');
    this.atrEl   = this.addChartRow('5%');
    this.stochEl = this.addChartRow('6%');

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
      <div class="tool-cluster tool-cluster-wide">
        <button class="tool-trigger" type="button"><span>Zaman</span><b>1G</b></button>
        <div class="tool-inline">
          ${tfs}
            <button class="ctrl-btn type-btn active" data-type="candlestick" title="${TR.CANDLE}">Mum</button>
            <button class="ctrl-btn type-btn" data-type="line" title="${TR.LINE}">Çizgi</button>
            <button class="ctrl-btn type-btn" data-type="bar" title="${TR.BAR}">Bar</button>
        </div>
      </div>

      <div class="tool-cluster indicator-toolbar-group">
        <button class="tool-trigger indicator-center-btn" id="indicator-center-btn" type="button" title="İndikatör merkezi"><span>Gösterge</span><b>ƒx <i id="ind-active-badge">${this.activeIndicators.size}</i></b></button>
        <div class="tool-inline" id="indicator-inline">
          ${this.quickIndicatorButtonsHTML()}
          ${this.favoritePinsHTML()}
          <button class="pin-btn" id="pin-indicators-btn" title="Açık tut (Pin)">📌</button>
        </div>
      </div>

      <div class="tool-cluster">
        <button class="tool-trigger" type="button"><span>Ölçek</span><b>Lin</b></button>
        <div class="tool-inline">
            <button class="ctrl-btn scale-mode-btn active" data-scale-mode="linear" title="Lineer">Lin</button>
            <button class="ctrl-btn scale-mode-btn" data-scale-mode="log" title="Logaritmik">Log</button>
            <button class="ctrl-btn scale-mode-btn" data-scale-mode="percent" title="Yüzdesel">%</button>
            <button class="ctrl-btn scale-base-btn" id="scale-base-btn" title="Yüzdesel Baz">Baz</button>
            <span class="unit-badge" id="chart-unit-badge"></span>
            <button class="ctrl-btn scale-auto-btn active" id="auto-price-btn" title="Oto Ölçek">Oto</button>
            <button class="ctrl-btn scale-reset-btn" id="price-reset-btn" title="Sıfırla">⟲</button>
            <button class="ctrl-btn prev-close-btn active" id="prev-close-btn" title="Önceki Kapanış">ÖK</button>
            <button class="ctrl-btn pnl-toggle-btn active" id="pnl-overlay-btn" title="Trade PnL">PnL</button>
            <button class="ctrl-btn pnl-toggle-btn active" id="risk-line-btn" title="Stop/Hedef">Risk</button>
            <button class="ctrl-btn pnl-toggle-btn active" id="bist-limit-btn" title="Tavan/Taban">T/T</button>
        </div>
      </div>

      <div class="tool-cluster compare-cluster">
        <button class="tool-trigger" type="button"><span>Karşılaştır</span><b>+ Sembol</b></button>
        <div class="tool-inline compare-inline">
          <div class="compare-search-wrap">
            <input type="text" class="search-input compare-input" id="compare-input" placeholder="+ Sembol" autocomplete="off" spellcheck="false" role="combobox" aria-expanded="false" aria-controls="compare-suggestions">
            <div class="compare-suggestions" id="compare-suggestions" role="listbox"></div>
          </div>
          <button class="ctrl-btn" id="compare-add-btn" title="Ekle/Değiştir">Ekle</button>
          <button class="ctrl-btn" id="compare-clear-btn" title="Temizle">x</button>
          <div id="compare-options" class="compare-options">
            <input type="color" id="compare-color-picker" value="${COMPARE_COLOR}" title="Renk">
            <select id="compare-type-select">
              <option value="candle" selected>Mum</option>
              <option value="line">Çizgi</option>
              <option value="area">Alan</option>
            </select>
          </div>
        </div>
      </div>

      ${this.drawingToolbarHTML()}

      ${this.eventFilterHTML()}

      <div class="tool-cluster ml-auto">
        <button class="tool-trigger" type="button"><span>Çıktı</span><b>Şablon</b></button>
        <div class="tool-inline output-inline">
          <div class="template-dropdown" id="template-dropdown">
          <button class="ctrl-btn" id="template-btn" title="${TR.TEMPLATES}">⚙ Şablonlar</button>
          <div class="template-menu" id="template-menu">
            <div class="template-input-group">
              <input type="text" id="new-template-name" placeholder="${TR.TEMPLATE_NAME}">
              <button class="btn-primary" id="save-template-btn" style="padding: 4px; font-size: 10px;">${TR.SAVE_TEMPLATE}</button>
            </div>
            <div class="template-divider"></div>
            <div id="template-list"></div>
            <div class="template-divider"></div>
            <div class="template-item" id="reset-template-btn">${TR.RESET_TEMPLATE}</div>
          </div>
        </div>

          <div class="template-dropdown" id="export-dropdown">
          <button class="ctrl-btn" id="export-btn" title="${TR.EXPORT_CHART}">⤓ Dışa Aktar</button>
          <div class="export-menu" id="export-menu">
            <div class="template-item" id="export-png-btn">📸 ${TR.EXPORT_PNG}</div>
            <div class="template-item" id="export-csv-btn">📊 ${TR.EXPORT_CSV}</div>
          </div>
          </div>
          <button class="ctrl-btn" id="fullscreen-btn" title="${TR.FULLSCREEN} (F)">⛶ Tam Ekran</button>
        </div>
      </div>
    `;
  }

  private drawingToolbarHTML(): string {
    return `
      <div class="tool-cluster">
        <button class="tool-trigger" type="button"><span>Çizim</span><b>Çizgiler</b></button>
        <div class="tool-inline">
          <button class="ctrl-btn drawing-tool-btn" data-drawing-tool="trendline" title="Trend Çizgisi">⟋</button>
          <button class="ctrl-btn drawing-tool-btn" data-drawing-tool="hline" title="Yatay Çizgi">―</button>
          <button class="ctrl-btn drawing-tool-btn" data-drawing-tool="vline" title="Dikey Çizgi">│</button>
          <button class="ctrl-btn drawing-tool-btn" data-drawing-tool="measure" title="Ölçüm Aracı">📏</button>
          <button class="ctrl-btn drawing-clear-btn" id="drawing-clear-btn" title="Tüm çizimleri sil">🗑</button>
          <button class="ctrl-btn drawing-tool-btn" data-drawing-tool="fibonacci" title="Fibonacci Düzeltme">Fib</button>
          <button class="ctrl-btn drawing-tool-btn" data-drawing-tool="fibonacci_ext" title="Fibonacci Uzantı">FibX</button>
          <button class="ctrl-btn drawing-tool-btn" data-drawing-tool="regression" title="Regresyon Kanalı">Reg</button>
          <button class="ctrl-btn drawing-tool-btn" data-drawing-tool-disabled title="Renko — Yakında" disabled style="opacity:0.4;cursor:not-allowed">Rnk</button>
        </div>
      </div>
    `;
  }

  private bindControls(controls: HTMLElement): void {
    controls.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;

      // H2: Dropdown item tıklama (gösterge aç/kapat).
      const dropdownItem = target.closest<HTMLElement>('.ind-dropdown-item');
      if (dropdownItem) {
        const ind = dropdownItem.dataset['ind']!;
        if (this.activeIndicators.has(ind)) {
          this.activeIndicators.delete(ind);
        } else {
          this.activeIndicators.add(ind);
        }
        this.saveIndicatorPrefs();
        this.updateIndicatorButtons();
        this.renderIndicatorCenter();
        this.updateIndicatorVisibility();
        return;
      }

      // Pin button logic
      const pinBtn = target.closest<HTMLElement>('#pin-indicators-btn');
      if (pinBtn) {
        const cluster = pinBtn.closest('.tool-cluster');
        if (cluster) cluster.classList.toggle('pinned');
        return;
      }

      const btn = target.closest('button') || target.closest('.template-item');
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

      // Indicator toggle (eski ind-btn ve yeni ind-fav-pin)
      if (btn.classList.contains('ind-btn') || btn.classList.contains('ind-fav-pin')) {
        const ind = btn.dataset['ind']!;
        if (this.activeIndicators.has(ind)) {
          this.activeIndicators.delete(ind);
          btn.classList.remove('active');
        } else {
          this.activeIndicators.add(ind);
          btn.classList.add('active');
        }
        this.saveIndicatorPrefs();
        this.updateIndicatorButtons();
        this.renderIndicatorCenter();
        this.updateIndicatorVisibility();
      }

      // H2: Dropdown trigger toggle
      if (btn.id === 'indicator-dropdown-trigger') {
        const menu = this.container.querySelector('#indicator-dropdown-menu');
        menu?.classList.toggle('show');
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

      // G8: Template Handlers
      if (btn.id === 'template-btn') {
        const menu = this.container.querySelector('#template-menu');
        menu?.classList.toggle('show');
        this.renderTemplateList();
      }

      if (btn.id === 'save-template-btn') {
        const input = this.container.querySelector<HTMLInputElement>('#new-template-name');
        if (input && input.value.trim()) {
          this.saveTemplate(input.value.trim());
          input.value = '';
          this.container.querySelector('#template-menu')?.classList.remove('show');
        }
      }

      if (btn.id === 'reset-template-btn') {
        this.resetTemplate();
        this.container.querySelector('#template-menu')?.classList.remove('show');
      }

      // G8: Export Handlers
      if (btn.id === 'export-btn') {
        this.container.querySelector('#export-menu')?.classList.toggle('show');
      }

      if (btn.id === 'export-png-btn') {
        this.exportToPNG();
        this.container.querySelector('#export-menu')?.classList.remove('show');
      }

      if (btn.id === 'export-csv-btn') {
        this.exportToCSV();
        this.container.querySelector('#export-menu')?.classList.remove('show');
      }

      // Compare
      if (btn.id === 'compare-add-btn') {
        this.submitCompareSymbol(controls);
      }

      if (btn.id === 'compare-clear-btn') {
        const input = controls.querySelector<HTMLInputElement>('#compare-input');
        if (input) input.value = '';
        this.hideCompareSuggestions(controls);
        this.clearCompare();
      }
    });

    this.bindCompareSearch(controls);

    const compareColorPicker = controls.querySelector<HTMLInputElement>('#compare-color-picker');
    if (compareColorPicker) {
      compareColorPicker.addEventListener('input', (e) => {
        if (this.compareSeries) {
          const color = (e.target as HTMLInputElement).value;
          const type = this.container.dataset['compareType'] || 'candle';
          if (type === 'candle') {
            this.compareSeries.applyOptions({
              upColor: `${color}cc`,
              downColor: `${COMPARE_DOWN_COLOR}99`,
              borderUpColor: color,
              borderDownColor: COMPARE_DOWN_COLOR,
              wickUpColor: color,
              wickDownColor: COMPARE_DOWN_COLOR,
            });
          } else if (type === 'area') {
            this.compareSeries.applyOptions({ lineColor: color, topColor: `${color}80`, bottomColor: `${color}00` });
          } else {
            this.compareSeries.applyOptions({ color });
          }
        }
      });
    }

    const compareTypeSelect = controls.querySelector<HTMLSelectElement>('#compare-type-select');
    if (compareTypeSelect) {
      compareTypeSelect.addEventListener('change', (e) => {
        const type = (e.target as HTMLSelectElement).value;
        this.container.dataset['compareType'] = type;
        if (this.compareCandles.length > 0 && this.container.dataset['compareSymbol']) {
          this.setCompareData(this.container.dataset['compareSymbol'], this.compareCandles);
        }
      });
    }

    // Close menus on click outside
    document.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      if (!target.closest('#template-dropdown')) {
        this.container.querySelector('#template-menu')?.classList.remove('show');
      }
      if (!target.closest('#export-dropdown')) {
        this.container.querySelector('#export-menu')?.classList.remove('show');
      }
      if (!target.closest('.compare-search-wrap')) {
        this.hideCompareSuggestions(controls);
      }
      // H2: Indicator dropdown
      if (!target.closest('#indicator-dropdown')) {
        this.container.querySelector('#indicator-dropdown-menu')?.classList.remove('show');
      }
    });

    // Template list item clicks
    this.container.querySelector('#template-list')?.addEventListener('click', (e) => {
      const item = (e.target as HTMLElement).closest<HTMLElement>('.template-item');
      if (item && item.dataset['name']) {
        this.loadTemplate(item.dataset['name']);
        this.container.querySelector('#template-menu')?.classList.remove('show');
      }
    });
  }

  private bindCompareSearch(controls: HTMLElement): void {
    const input = controls.querySelector<HTMLInputElement>('#compare-input');
    const suggestions = controls.querySelector<HTMLElement>('#compare-suggestions');
    if (!input || !suggestions) return;

    input.addEventListener('input', () => {
      this.compareSuggestionIndex = 0;
      this.renderCompareSuggestions(controls);
    });

    input.addEventListener('focus', () => {
      this.renderCompareSuggestions(controls);
    });

    input.addEventListener('keydown', (e) => {
      const items = Array.from(suggestions.querySelectorAll<HTMLElement>('.compare-suggestion'));
      if (e.key === 'ArrowDown' && items.length > 0) {
        e.preventDefault();
        this.compareSuggestionIndex = Math.min(this.compareSuggestionIndex + 1, items.length - 1);
        this.updateCompareSuggestionActive(suggestions);
        return;
      }

      if (e.key === 'ArrowUp' && items.length > 0) {
        e.preventDefault();
        this.compareSuggestionIndex = Math.max(this.compareSuggestionIndex - 1, 0);
        this.updateCompareSuggestionActive(suggestions);
        return;
      }

      if (e.key === 'Enter') {
        e.preventDefault();
        const active = items[this.compareSuggestionIndex];
        if (active?.dataset['symbol']) {
          input.value = active.dataset['symbol'];
        }
        this.submitCompareSymbol(controls);
        return;
      }

      if (e.key === 'Escape') {
        this.hideCompareSuggestions(controls);
      }
    });

    suggestions.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      const item = (e.target as HTMLElement).closest<HTMLElement>('.compare-suggestion');
      if (!item?.dataset['symbol']) return;
      input.value = item.dataset['symbol'];
      this.submitCompareSymbol(controls);
    });
  }

  private submitCompareSymbol(controls: HTMLElement): void {
    const input = controls.querySelector<HTMLInputElement>('#compare-input');
    if (!input?.value.trim()) return;
    const symbol = this.resolveCompareInput(input.value.trim());
    input.value = symbol;
    this.hideCompareSuggestions(controls);
    this.container.dispatchEvent(new CustomEvent('compareRequest', { detail: symbol, bubbles: true }));
  }

  private renderCompareSuggestions(controls: HTMLElement): void {
    const input = controls.querySelector<HTMLInputElement>('#compare-input');
    const suggestions = controls.querySelector<HTMLElement>('#compare-suggestions');
    if (!input || !suggestions) return;

    const matches = this.compareMatches(input.value);
    if (matches.length === 0) {
      this.hideCompareSuggestions(controls);
      return;
    }

    this.compareSuggestionIndex = Math.min(this.compareSuggestionIndex, matches.length - 1);
    suggestions.innerHTML = matches.map((s, index) => {
      const cleanSymbol = s.symbol.replace('.IS', '');
      return `
        <button class="compare-suggestion${index === this.compareSuggestionIndex ? ' active' : ''}" type="button" role="option" data-symbol="${this.escapeHtml(s.symbol)}" aria-selected="${index === this.compareSuggestionIndex ? 'true' : 'false'}">
          <span class="compare-suggestion-symbol">${this.escapeHtml(cleanSymbol)}</span>
          <span class="compare-suggestion-name">${this.escapeHtml(s.name)}</span>
          <span class="compare-suggestion-group">${this.escapeHtml(s.group)}</span>
        </button>
      `;
    }).join('');
    suggestions.classList.add('show');
    input.setAttribute('aria-expanded', 'true');
  }

  private hideCompareSuggestions(controls: HTMLElement): void {
    const input = controls.querySelector<HTMLInputElement>('#compare-input');
    const suggestions = controls.querySelector<HTMLElement>('#compare-suggestions');
    if (!suggestions) return;
    suggestions.classList.remove('show');
    suggestions.innerHTML = '';
    input?.setAttribute('aria-expanded', 'false');
  }

  private updateCompareSuggestionActive(suggestions: HTMLElement): void {
    suggestions.querySelectorAll<HTMLElement>('.compare-suggestion').forEach((item, index) => {
      const active = index === this.compareSuggestionIndex;
      item.classList.toggle('active', active);
      item.setAttribute('aria-selected', active ? 'true' : 'false');
      if (active) item.scrollIntoView({ block: 'nearest' });
    });
  }

  private compareMatches(query: string): typeof ALL_SYMBOLS {
    const normalizedQuery = this.normalizeCompareQuery(query);
    const candidates = normalizedQuery
      ? ALL_SYMBOLS.filter(s => {
          const symbol = this.normalizeCompareQuery(s.symbol);
          const cleanSymbol = this.normalizeCompareQuery(s.symbol.replace('.IS', ''));
          const name = this.normalizeCompareQuery(s.name);
          const group = this.normalizeCompareQuery(s.group);
          return symbol.includes(normalizedQuery)
            || cleanSymbol.includes(normalizedQuery)
            || name.includes(normalizedQuery)
            || group.includes(normalizedQuery);
        })
      : ALL_SYMBOLS;

    return candidates
      .slice()
      .sort((a, b) => this.compareMatchScore(a, normalizedQuery) - this.compareMatchScore(b, normalizedQuery))
      .slice(0, 8);
  }

  private compareMatchScore(symbolInfo: typeof ALL_SYMBOLS[number], query: string): number {
    if (!query) return symbolInfo.assetType === 'equity' ? 0 : 1;
    const symbol = this.normalizeCompareQuery(symbolInfo.symbol);
    const cleanSymbol = this.normalizeCompareQuery(symbolInfo.symbol.replace('.IS', ''));
    const name = this.normalizeCompareQuery(symbolInfo.name);
    if (cleanSymbol === query || symbol === query) return 0;
    if (cleanSymbol.startsWith(query) || symbol.startsWith(query)) return 1;
    if (name.startsWith(query)) return 2;
    if (name.includes(query)) return 3;
    return 4;
  }

  private resolveCompareInput(value: string): string {
    const normalizedValue = this.normalizeCompareQuery(value);
    const exact = ALL_SYMBOLS.find(s =>
      this.normalizeCompareQuery(s.symbol) === normalizedValue
      || this.normalizeCompareQuery(s.symbol.replace('.IS', '')) === normalizedValue
    );
    return exact?.symbol ?? value.trim().toUpperCase();
  }

  private normalizeCompareQuery(value: string): string {
    return value
      .trim()
      .toLocaleLowerCase('tr-TR')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/ı/g, 'i')
      .replace(/İ/g, 'i')
      .replace(/[^a-z0-9=.:-]/g, '');
  }

  // ─── Chart initialization ───────────────────────────────────────────────

  private initCharts(): void {
    const baseOptions = chartOptions();
    this.mainChart = createChart(this.mainEl, { ...baseOptions, height: this.mainEl.clientHeight || 300 });
    this.volChart  = createChart(this.volEl,  { ...baseOptions, height: this.volEl.clientHeight  || 60, rightPriceScale: { visible: false }, timeScale: { visible: false } });
    this.rsiChart  = createChart(this.rsiEl,  { ...baseOptions, height: this.rsiEl.clientHeight  || 80, rightPriceScale: { scaleMargins: { top: 0.1, bottom: 0.1 } }, timeScale: { visible: false } });
    this.macdChart = createChart(this.macdEl, { ...baseOptions, height: this.macdEl.clientHeight || 80, rightPriceScale: { scaleMargins: { top: 0.1, bottom: 0.1 } }, timeScale: { visible: false } });
    this.atrChart  = createChart(this.atrEl,  { ...baseOptions, height: this.atrEl.clientHeight  || 60, rightPriceScale: { scaleMargins: { top: 0.1, bottom: 0.1 } }, timeScale: { visible: false } });
    this.stochChart = createChart(this.stochEl, { ...baseOptions, height: this.stochEl.clientHeight || 70, rightPriceScale: { scaleMargins: { top: 0.1, bottom: 0.1 } }, timeScale: { visible: false } });
    this.applyThemeOptions();

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
    if (ctrlsEl) {
      this.drawingManager.bindToolbar(ctrlsEl);
      ctrlsEl.addEventListener('click', (e) => {
        const target = e.target as HTMLElement;
        if (target.closest('.drawing-tool-btn') || target.closest('#drawing-clear-btn')) {
          this.container.dataset['drawingTool'] = this.drawingManager.getTool();
        }
      });
    }

    // G9: Event marker container
    this.initEventLayer();

    this.bindEventFilterControls(ctrlsEl);

    // Reposition markers on scroll/zoom
    this.mainChart.timeScale().subscribeVisibleLogicalRangeChange(() => {
      this.repositionEventMarkers();
    });
  }

  private applyThemeOptions(): void {
    const theme = chartThemeColors();
    this.container.style.background = theme.bg;
    const themedOptions = {
      layout: { background: { type: ColorType.Solid, color: theme.bg }, textColor: theme.text, attributionLogo: false },
      grid: { vertLines: { color: theme.border }, horzLines: { color: theme.border } },
      timeScale: { borderColor: theme.border },
      rightPriceScale: { borderColor: theme.border },
      leftPriceScale: { borderColor: theme.border, visible: false },
    };
    [this.mainChart, this.volChart, this.rsiChart, this.macdChart, this.atrChart, this.stochChart]
      .forEach((chart) => chart.applyOptions(themedOptions));
  }

  private addLevelLine(series: ISeriesApi<'Line'>, price: number, color: string, title: string): void {
    series.createPriceLine({
      price,
      color: color,
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      axisLabelVisible: true,
      title,
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

    // G10: Pass candles to DrawingManager for regression channel
    this.drawingManager?.setCandles(candles);

    if (options.preserveTimeRange && savedVisibleRange) {
      this.restoreVisibleRange(savedVisibleRange);
    } else if (reason !== 'append') {
      this.mainChart.timeScale().fitContent();
    }

    if (shouldResetPrice) {
      this.resetPriceScales();
    }
    this.lastMedianPrice = currentMedian;

    // G9: Render event markers after data is loaded
    this.renderEventMarkers();
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
    this.clearCompare();
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
      // H4: Sol ekseni de resetle (karşılaştırma sembolü için)
      () => this.mainChart.priceScale('left').applyOptions({ autoScale: true, scaleMargins: mainMargins }),
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
        color: '#475569',
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
        axisLabelVisible: true,
        title: this.scaleMode === 'percent' ? 'ÖK %' : 'ÖK',
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
    this.addOverlayPriceLine(series, prev.close * 1.10, '#475569', 'Tavan', false);
    this.addOverlayPriceLine(series, prev.close * 0.90, '#475569', 'Taban', false);
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

    // Yeni indikatörleri grafik üzerindeyse updatele ya da lazy yarat
    if (this.activeIndicators.has('kairi') && inds.kairi) {
      if (!this.kairiSeries) {
        this.kairiSeries = this.mainChart.addLineSeries({ color: C.purple, lineWidth: 2, title: 'KAIRI' });
      }
      this.kairiSeries.setData(lineData(inds.kairi));
    }
    
    if (this.activeIndicators.has('most') && inds.most && inds.mostEma) {
      if (!this.mostSeries) {
        this.mostSeries = this.mainChart.addLineSeries({ color: C.green, lineWidth: 2, title: 'MOST' });
      }
      if (!this.mostEmaSeries) {
        this.mostEmaSeries = this.mainChart.addLineSeries({ color: C.blue, lineWidth: 1, lineStyle: 2, title: 'MOST EMA' });
      }
      this.mostSeries.setData(lineData(inds.most));
      this.mostEmaSeries.setData(lineData(inds.mostEma));
    }

    if (this.activeIndicators.has('bbw') && inds.bbWidth) {
      if (!this.bbwSeries) {
        this.bbwSeries = this.mainChart.addLineSeries({ color: C.yellow, lineWidth: 1, title: 'BBW' });
      }
      this.bbwSeries.setData(lineData(inds.bbWidth));
    }
    
    if (this.activeIndicators.has('gmma') && inds.gmma) {
      Object.keys(inds.gmma).forEach(key => {
        if (!this.gmmaSeriesDict[key]) {
          const isShort = key.startsWith('short');
          this.gmmaSeriesDict[key] = this.mainChart.addLineSeries({
            color: isShort ? 'rgba(59, 130, 246, 0.4)' : 'rgba(239, 68, 68, 0.4)',
            lineWidth: 1,
            title: `GMMA ${key.replace('_', ' ')}`
          });
        }
        
        const gRow = inds.gmma![key];
        if (gRow) {
          const gData = gRow.map((x: any) => ({
            time: x.time as UTCTimestamp,
            value: x.value
          })).filter(d => !isNaN(d.value)) as LineData[];
          this.gmmaSeriesDict[key].setData(gData);
        }
      });
    }

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

  public setScaleMode(mode: ChartScaleMode): void {
    if (!['linear', 'log', 'percent'].includes(mode)) return;
    if (mode === this.scaleMode) return;

    this.scaleMode = mode;
    this.ensurePercentBase(this.candles);
    this.applyScaleMode();
    this.updateScaleButtons();
    this.updateUnitBadge();
    this.rerenderPriceData();
    this.resetPriceScales();

    this.container.dispatchEvent(new CustomEvent('scaleModeChange', {
      detail: mode, bubbles: true,
    }));
  }

  private applyScaleMode(): void {
    const mode = this.scaleMode === 'log'
      ? PriceScaleMode.Logarithmic
      : PriceScaleMode.Normal;
    const updates: Array<() => void> = [
      () => this.mainChart.priceScale('right').applyOptions({ mode }),
      () => this.mainChart.priceScale('left').applyOptions({ mode }),
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
    if (this.compareSeries && this.compareCandles.length > 0) {
      this.renderCompareSeries();
    }
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
        (this.indicatorParams as any)[key] = value;
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
    
    // Yeni indikatörler main grafikte varsa opacity/visible toggles:
    this.kairiSeries?.applyOptions({ visible: has('kairi') });
    this.mostSeries?.applyOptions({ visible: has('most') });
    this.mostEmaSeries?.applyOptions({ visible: has('most') });
    this.bbwSeries?.applyOptions({ visible: has('bbw') });
    if (this.gmmaSeriesDict) {
      Object.values(this.gmmaSeriesDict).forEach(s => s.applyOptions({ visible: has('gmma') }));
    }
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
      'bb width': 'bbw',
      bbwidth: 'bbw'
    };
    const normalized = aliases[key] ?? key;
    return ['bb', 'ema', 'vwap', 'rsi', 'macd', 'vol', 'atr', 'stoch', 'kairi', 'most', 'bbw', 'gmma'].includes(normalized)
      ? normalized
      : '';
  }

  private updateIndicatorButtons(): void {
    // Dropdown item'ları güncelle
    this.container.querySelectorAll<HTMLElement>('.ind-dropdown-item').forEach(item => {
      const ind = item.dataset['ind'];
      const isActive = !!ind && this.activeIndicators.has(ind);
      item.classList.toggle('active', isActive);
      const icon = item.querySelector('.ind-dropdown-icon');
      if (icon) icon.textContent = isActive ? '✓' : '○';
    });
    // Eski ind-btn'ler için geriye uyumluluk
    this.container.querySelectorAll<HTMLElement>('.ind-btn').forEach(btn => {
      const ind = btn.dataset['ind'];
      btn.classList.toggle('active', !!ind && this.activeIndicators.has(ind));
    });
    // Badge güncelle
    const badge = this.container.querySelector('#ind-active-badge');
    if (badge) badge.textContent = String(this.activeIndicators.size);
    // Favori pin'leri ve aktif chip'leri güncelle
    this.refreshIndicatorToolbarPins();
  }

  /** H2: Favori göstergeleri toolbar'a pill olarak pinle */
  private favoritePinsHTML(): string {
    const favDefs = INDICATOR_DEFS.filter(d => this.favoriteIndicators.has(d.key));
    if (favDefs.length === 0) return '';
    return favDefs.map(def => `
      <button class="ctrl-btn ind-fav-pin${this.activeIndicators.has(def.key) ? ' active' : ''}" data-ind="${def.key}" title="${def.label} (Favori)">
        ★ ${def.key === 'stoch' ? 'STOCH' : def.key.toUpperCase()}
      </button>
    `).join('');
  }

  private quickIndicatorButtonsHTML(): string {
    return `
      <div class="indicator-quick-strip" aria-label="Hızlı indikatörler">
        ${INDICATOR_DEFS.map(def => `
          <button class="ctrl-btn ind-btn${this.activeIndicators.has(def.key) ? ' active' : ''}" data-ind="${def.key}" title="${def.label}">
            ${def.key === 'stoch' ? 'St' : def.key.toUpperCase()}
          </button>
        `).join('')}
      </div>
    `;
  }

  /** H2: Toolbar'daki favori ve aktif chip alanlarını yeniden render et */
  private refreshIndicatorToolbarPins(): void {
    const group = this.container.querySelector('.indicator-toolbar-group');
    if (!group) return;
    // Mevcut pin'leri kaldır
    group.querySelectorAll('.ind-fav-pin').forEach(el => el.remove());
    // Yeniden ekle
    const dropdown = group.querySelector('.indicator-dropdown');
    if (dropdown) {
      dropdown.insertAdjacentHTML('afterend', this.favoritePinsHTML());
    }
  }

  // ─── Chart type switching ───────────────────────────────────────────────

  setChartType(type: ChartType): void {
    this.chartType = type;
    this.candleSeries.applyOptions({ visible: type === 'candlestick' });
    this.lineSeries.applyOptions({ visible: type === 'line' });
    this.barSeries.applyOptions({ visible: type === 'bar' });
    this.updateReferenceLines();
    this.updateTypeButtons();
  }

  private updateTypeButtons(): void {
    this.container.querySelectorAll('.type-btn').forEach(btn => {
      const el = btn as HTMLElement;
      el.classList.toggle('active', el.dataset['type'] === this.chartType);
    });
  }

  // ─── G8: Template & Export Logic ────────────────────────────────────────

  getCurrentTemplate(name: string): ChartTemplate {
    return {
      name,
      chartType: this.chartType,
      activeIndicators: Array.from(this.activeIndicators),
      indicatorParams: { ...this.indicatorParams },
      scaleMode: this.scaleMode,
      showPreviousClose: this.showPreviousClose,
      showPnlOverlay: this.showPnlOverlay,
      showRiskLines: this.showRiskLines,
      showBistLimits: this.showBistLimits,
    };
  }

  applyTemplate(template: ChartTemplate): void {
    this.setChartType(template.chartType);
    this.activeIndicators = new Set(template.activeIndicators);
    this.indicatorParams = { ...DEFAULT_INDICATOR_PARAMS, ...template.indicatorParams };
    this.saveIndicatorPrefs();
    this.updateIndicatorButtons();
    this.updateIndicatorVisibility();
    this.setScaleMode(template.scaleMode);
    
    this.showPreviousClose = template.showPreviousClose;
    this.container.querySelector('#prev-close-btn')?.classList.toggle('active', this.showPreviousClose);
    
    this.showPnlOverlay = template.showPnlOverlay;
    this.container.querySelector('#pnl-overlay-btn')?.classList.toggle('active', this.showPnlOverlay);
    
    this.showRiskLines = template.showRiskLines;
    this.container.querySelector('#risk-line-btn')?.classList.toggle('active', this.showRiskLines);
    
    this.showBistLimits = template.showBistLimits;
    this.container.querySelector('#bist-limit-btn')?.classList.toggle('active', this.showBistLimits);

    this.renderIndicatorCenter();
    this.renderIndicators(this.candles);
    this.updateReferenceLines();
    this.renderPnlOverlays(this.markerSignals);
  }

  private saveTemplate(name: string): void {
    const templates = this.getSavedTemplates();
    templates[name] = this.getCurrentTemplate(name);
    localStorage.setItem('piyasapilot_chart_templates', JSON.stringify(templates));
    localStorage.setItem('piyasapilot_default_template', name);
  }

  private loadTemplate(name: string): void {
    const templates = this.getSavedTemplates();
    const template = templates[name];
    if (template) {
      this.applyTemplate(template);
      localStorage.setItem('piyasapilot_default_template', name);
    }
  }

  private getSavedTemplates(): Record<string, ChartTemplate> {
    try {
      return JSON.parse(localStorage.getItem('piyasapilot_chart_templates') || '{}');
    } catch {
      return {};
    }
  }

  private renderTemplateList(): void {
    const list = this.container.querySelector('#template-list');
    if (!list) return;
    const templates = this.getSavedTemplates();
    const defaultTpl = localStorage.getItem('piyasapilot_default_template');

    list.innerHTML = Object.keys(templates).map(name => `
      <div class="template-item" data-name="${this.escapeHtml(name)}">
        <span>${this.escapeHtml(name)}</span>
        ${name === defaultTpl ? '<small style="color:var(--blue)">★</small>' : ''}
      </div>
    `).join('') || `<div class="template-item" style="color:var(--text-dim)">${TR.NO_DATA}</div>`;
  }

  private resetTemplate(): void {
    this.applyTemplate({
      name: 'Default',
      chartType: 'candlestick',
      activeIndicators: [...DEFAULT_ACTIVE_INDICATORS],
      indicatorParams: { ...DEFAULT_INDICATOR_PARAMS },
      scaleMode: 'linear',
      showPreviousClose: true,
      showPnlOverlay: true,
      showRiskLines: true,
      showBistLimits: true,
    });
    localStorage.removeItem('piyasapilot_default_template');
  }

  exportToCSV(): void {
    if (!this.candles.length) return;
    const inds = computeIndicators(this.candles, this.indicatorParams);
    
    let csv = 'Time,Open,High,Low,Close,Volume';
    if (inds.rsi) csv += ',RSI';
    if (inds.ema9) csv += ',EMA9';
    if (inds.ema21) csv += ',EMA21';
    csv += '\n';

    this.candles.forEach((c, i) => {
      csv += `${formatDateTime(c.time)},${c.open},${c.high},${c.low},${c.close},${c.volume}`;
      if (inds.rsi) csv += `,${inds.rsi[i] ?? ''}`;
      if (inds.ema9) csv += `,${inds.ema9[i] ?? ''}`;
      if (inds.ema21) csv += `,${inds.ema21[i] ?? ''}`;
      csv += '\n';
    });

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `piyasapilot_${this.lastSymbol}_${this.lastTimeframe}_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  exportToPNG(): void {
    const canvas = this.mainChart.takeScreenshot();
    if (!canvas) {
      alert('PNG Export çalışmıyor: Canvas snapshot alınamadı.');
      return;
    }
    const a = document.createElement('a');
    a.href = canvas.toDataURL('image/png');
    a.download = `piyasapilot_${this.lastSymbol}_${Date.now()}.png`;
    a.click();
  }

  // ─── G7: Multi-chart Sync Methods ───────────────────────────────────────

  getVisibleLogicalRange() {
    return this.mainChart.timeScale().getVisibleLogicalRange();
  }

  setVisibleLogicalRange(range: any) {
    if (range) this.mainChart.timeScale().setVisibleLogicalRange(range);
  }

  onVisibleLogicalRangeChange(cb: (range: any) => void) {
    return this.mainChart.timeScale().subscribeVisibleLogicalRangeChange(cb);
  }

  onCrosshairMove(cb: (param: any) => void) {
    return this.mainChart.subscribeCrosshairMove(cb);
  }

  setCrosshair(_param: any) {
    // lightweight-charts doesn't have a direct setCrosshair, but we can sync via a "dummy" event
    // or by manually triggering the info overlay if we really need to.
    // For now, we'll rely on the fact that sync works via shared logic if possible.
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
        this.setFullscreenUi(true);
        this.resizeCharts();
      });
    } else {
      document.exitFullscreen();
    }
  }

  private onFullscreenChange(): void {
    this.setFullscreenUi(document.fullscreenElement === this.container);
    this.resizeCharts();
  }

  private setFullscreenUi(active: boolean): void {
    const controls = this.container.querySelector('.chart-controls') as HTMLElement | null;
    const eventRow = this.container.querySelector('.chart-event-controls') as HTMLElement | null;

    if (active) {
      this.isFullscreen = true;
      controls?.classList.add('fullscreen-compact');
      eventRow?.classList.add('fullscreen-hidden');
      this.addFullscreenHoverTrigger();
    } else {
      this.isFullscreen = false;
      this.container.classList.remove('css-fullscreen');
      controls?.classList.remove('fullscreen-compact', 'shown');
      eventRow?.classList.remove('fullscreen-hidden');
      this.removeFullscreenHoverTrigger();
    }
  }

  /** H3: Üst kenarda fare tetikleyicisi — toolbar'ı göster */
  private hoverTriggerEl: HTMLElement | null = null;

  private addFullscreenHoverTrigger(): void {
    this.removeFullscreenHoverTrigger();
    const trigger = document.createElement('div');
    trigger.className = 'fullscreen-hover-trigger';
    trigger.addEventListener('mouseenter', () => {
      this.container.querySelector('.chart-controls')?.classList.add('shown');
    });
    this.container.appendChild(trigger);
    this.hoverTriggerEl = trigger;

    // Toolbar'dan ayrılınca gizle
    const controls = this.container.querySelector('.chart-controls');
    controls?.addEventListener('mouseleave', () => {
      controls.classList.remove('shown');
    });
  }

  private removeFullscreenHoverTrigger(): void {
    if (this.hoverTriggerEl) {
      this.hoverTriggerEl.remove();
      this.hoverTriggerEl = null;
    }
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

  public resizeCharts(): void {
    const w = this.isFullscreen ? window.innerWidth  : this.container.offsetWidth;
    const h = this.isFullscreen ? window.innerHeight : this.container.offsetHeight;

    // H3: Fullscreen'de toolbar gizli (floating), yüksekliğini düşme
    const controlsH = this.isFullscreen
      ? 0
      : (this.container.querySelector('.chart-controls') as HTMLElement)?.offsetHeight ?? 40;
    const eventRowH = this.isFullscreen
      ? 0
      : 0;
    const available = Math.max(180, h - controlsH - eventRowH);

    const mainH  = Math.floor(available * 0.64);
    const volH   = Math.floor(available * 0.07);
    const rsiH   = Math.floor(available * 0.09);
    const macdH  = Math.floor(available * 0.09);
    const atrH   = Math.floor(available * 0.05);
    const stochH = Math.floor(available * 0.06);

    this.mainChart.resize(Math.max(1, w), Math.max(80, mainH));
    this.volChart.resize(Math.max(1, w), Math.max(28, volH));
    this.rsiChart.resize(Math.max(1, w), Math.max(32, rsiH));
    this.macdChart.resize(Math.max(1, w), Math.max(32, macdH));
    this.atrChart.resize(Math.max(1, w), Math.max(28, atrH));
    this.stochChart.resize(Math.max(1, w), Math.max(32, stochH));
  }

  // ─── Cleanup ─────────────────────────────────────────────────────────────

  destroy(): void {
    window.removeEventListener('piyasapilot:theme-change', this.handleThemeChange);
    this.drawingManager?.destroy();
    this.resizeObserver.disconnect();
    if (this.compareSeries) {
      this.mainChart.removeSeries(this.compareSeries);
    }
    this.mainChart.remove();
    this.volChart.remove();
    this.rsiChart.remove();
    this.macdChart.remove();
    this.atrChart.remove();
    this.stochChart.remove();
  }

  // ─── Compare Symbol Logic ───────────────────────────────────────────────

  setCompareData(symbol: string, candles: OHLCV[]): void {
    if (this.compareSeries) {
      this.mainChart.removeSeries(this.compareSeries);
      this.compareSeries = null;
    }
    this.compareCandles = candles;
    this.container.dataset['compareSymbol'] = symbol;

    // G6: Fiyat oran uyuşmazlığı kontrolü (Auto-Percentage Mode)
    if (this.candles.length > 0 && candles.length > 0 && this.scaleMode !== 'percent') {
      const syncMatch = candles.find(c => c.time >= this.candles[0].time) || candles[0];
      const mainPrice = this.candles[0].close;
      const compPrice = syncMatch.close;
      
      if (mainPrice > 0 && compPrice > 0) {
        const ratio = mainPrice > compPrice ? mainPrice / compPrice : compPrice / mainPrice;
        if (ratio > 3) {
          console.log(`[Chart] Fiyat farkı çok yüksek (${ratio.toFixed(1)}x). Otomatik yüzdesel moda geçiliyor.`);
          this.scaleMode = 'percent';
          // scaleMode değiştirdiğimiz için base recalculation tetiklenmeli
          this.ensurePercentBase(this.candles);
          this.updateScaleButtons();
        }
      }
    }

    const colorPicker = this.container.querySelector<HTMLInputElement>('#compare-color-picker');
    const seriesColor = colorPicker ? colorPicker.value : COMPARE_COLOR;
    const compareTypeSelect = this.container.querySelector<HTMLSelectElement>('#compare-type-select');
    const compareType = this.container.dataset['compareType'] || compareTypeSelect?.value || 'candle';
    this.container.dataset['compareType'] = compareType;

    // H2: Toolbar'da eklenen sembolü ve rengini göster
    const compareTrigger = this.container.querySelector('.compare-cluster .tool-trigger b') as HTMLElement;
    if (compareTrigger) {
      compareTrigger.textContent = symbol;
      compareTrigger.style.color = seriesColor;
    }

    if (compareType === 'candle') {
      this.compareSeries = this.mainChart.addCandlestickSeries({
        upColor: `${seriesColor}cc`,
        downColor: `${COMPARE_DOWN_COLOR}99`,
        borderUpColor: seriesColor,
        borderDownColor: COMPARE_DOWN_COLOR,
        wickUpColor: seriesColor,
        wickDownColor: COMPARE_DOWN_COLOR,
        priceScaleId: 'left',
        title: symbol,
      });
    } else if (compareType === 'area') {
      this.compareSeries = this.mainChart.addAreaSeries({
        lineColor: seriesColor,
        topColor: `${seriesColor}80`,
        bottomColor: `${seriesColor}00`,
        lineWidth: 2,
        priceScaleId: 'left',
        title: symbol,
      });
    } else {
      this.compareSeries = this.mainChart.addLineSeries({
        color: seriesColor,
        lineWidth: 2,
        priceLineVisible: true,
        lastValueVisible: true,
        crosshairMarkerVisible: true,
        title: symbol,
        priceScaleId: 'left',
      });
    }

    // H4: Sol ekseni bağımsız autoScale ile yapılandır — iki grafik birbirini ezmesin
    this.mainChart.priceScale('left').applyOptions({
      visible: true,
      autoScale: true,
      scaleMargins: { top: 0.08, bottom: 0.14 },
      borderColor: C.border,
    });
    const compareOptions = this.container.querySelector<HTMLElement>('#compare-options');
    if (compareOptions) compareOptions.style.display = 'flex';

    this.renderCompareSeries();

    this.applyScaleMode();
    this.updateUnitBadge();
  }

  private syncCompareData(mainRef: OHLCV[], compareSrc: OHLCV[]): OHLCV[] {
    if (!mainRef.length || !compareSrc.length) return [];
    
    // G6: Data Eşitleme (Tatil/Gap - Forward-fill)
    const synced: OHLCV[] = [];
    let compIdx = 0;
    let lastValidComp: OHLCV | null = null;
  
    for (const mc of mainRef) {
      while (compIdx < compareSrc.length && (compareSrc[compIdx].time as number) <= (mc.time as number)) {
        lastValidComp = compareSrc[compIdx];
        if (compareSrc[compIdx].time === mc.time) {
            compIdx++;
            break;
        }
        compIdx++;
      }
      
      if (lastValidComp) {
        synced.push({
          ...lastValidComp,
          time: mc.time
        });
      }
    }
    return synced;
  }

  private renderCompareSeries(): void {
    if (!this.compareSeries || this.compareCandles.length === 0 || this.candles.length === 0) return;

    // G6: Tatil/Gap eşitlemesi
    const syncedCompareCandles = this.syncCompareData(this.candles, this.compareCandles);

    // Determine compare base
    this.comparePercentBaseClose = null;
    if (this.scaleMode === 'percent' && this.percentBaseTime != null) {
      const baseCandle = syncedCompareCandles.find(c => c.time >= this.percentBaseTime!) || syncedCompareCandles[0];
      if (baseCandle) this.comparePercentBaseClose = baseCandle.close;
    }

    const compareType = this.container.dataset['compareType'] || 'candle';
    if (compareType === 'candle') {
      const candleData = syncedCompareCandles.map(c => {
        const base = this.comparePercentBaseClose;
        return {
          time: c.time as UTCTimestamp,
          open: base ? this.percentChange(c.open, base) : c.open,
          high: base ? this.percentChange(c.high, base) : c.high,
          low: base ? this.percentChange(c.low, base) : c.low,
          close: base ? this.percentChange(c.close, base) : c.close,
        };
      });
      this.compareSeries.setData(candleData);
      return;
    }

    const compareLineData = syncedCompareCandles.map(c => ({
      time: c.time as Time,
      value: this.scaleMode === 'percent' && this.comparePercentBaseClose
        ? this.percentChange(c.close, this.comparePercentBaseClose)
        : c.close,
    }));
    this.compareSeries.setData(compareLineData);
  }

  clearCompare(): void {
    if (this.compareSeries) {
      this.mainChart.removeSeries(this.compareSeries);
      this.compareSeries = null;
      this.mainChart.priceScale('left').applyOptions({ visible: false });
    }
    this.compareCandles = [];
    this.comparePercentBaseClose = null;
    this.container.removeAttribute('data-compare-symbol');

    const compareOptions = this.container.querySelector<HTMLElement>('#compare-options');
    if (compareOptions) compareOptions.style.display = 'none';

    // Toolbar metnini geri yükle
    const compareTrigger = this.container.querySelector('.compare-cluster .tool-trigger b') as HTMLElement;
    if (compareTrigger) {
      compareTrigger.textContent = '+ Sembol';
      compareTrigger.style.color = '';
    }

    this.applyScaleMode();
    this.updateUnitBadge();
  }

  // ─── G9: Event Marker System ─────────────────────────────────────────────

  private initEventLayer(): void {
    // Shared tooltip element (reused by all markers)
    this.eventTooltipEl = document.createElement('div');
    this.eventTooltipEl.className = 'event-tooltip';
    this.eventTooltipEl.style.display = 'none';
    this.mainEl.appendChild(this.eventTooltipEl);

    // Hide tooltip on click outside
    document.addEventListener('click', (e) => {
      if (this.eventTooltipEl && !this.eventTooltipEl.contains(e.target as Node)) {
        this.eventTooltipEl.style.display = 'none';
      }
    });
  }

  /** Load sample/mock events for current symbol. Called on symbol change. */
  loadSampleEvents(symbol: string): void {
    // Sample events – always show as "örnek olay verisi" until real backend is connected
    const base = 1_714_521_600; // 2024-05-01
    const day = 86_400;
    this.chartEvents = [
      {
        id: `${symbol}_haber_1`,
        type: 'haber',
        time: base + 5 * day,
        title: `${symbol} Kurul Kararı`,
        summary: 'Yönetim kurulu yeni yatırım planını açıkladı.',
        source: 'Reuters',
        symbol,
      },
      {
        id: `${symbol}_kap_1`,
        type: 'kap',
        time: base + 15 * day,
        title: 'KAP Bildirimi',
        summary: 'Önemli ortaklık bilgisi güncellendi.',
        source: 'KAP',
        symbol,
      },
      {
        id: `${symbol}_bilanco_1`,
        type: 'bilanco',
        time: base + 30 * day,
        title: 'Q1 2024 Bilanço',
        summary: 'Net kâr beklentilerin üzerinde geldi.',
        source: 'KAP',
        symbol,
      },
      {
        id: `${symbol}_temettu_1`,
        type: 'temettu',
        time: base + 45 * day,
        title: 'Temettü Dağıtımı',
        summary: 'Hisse başına 2.50 ₺ temettü ödendi.',
        source: 'KAP',
        symbol,
      },
      {
        id: `${symbol}_sermaye_1`,
        type: 'sermaye',
        time: base + 60 * day,
        title: 'Sermaye Artırımı',
        summary: '%20 bedelsiz hisse ihracı onaylandı.',
        source: 'KAP',
        symbol,
      },
    ];

    // Dataset attribute so tests can verify
    this.container.dataset['eventSource'] = 'sample';
    this.container.dataset['eventCount'] = String(this.chartEvents.length);
    this.renderEventMarkers();
  }

  setEventFilter(filter: ChartEventType | 'all'): void {
    this.activeEventTypes = filter === 'all'
      ? new Set(EVENT_FILTER_TYPES)
      : new Set([filter]);
    this.syncEventFilterButtons();
    this.renderEventMarkers();
  }

  private getFilteredEvents(): ChartEvent[] {
    return this.chartEvents.filter(e => this.activeEventTypes.has(e.type));
  }

  private clearEventMarkers(): void {
    this.eventMarkerEls.forEach(el => el.remove());
    this.eventMarkerEls.clear();
  }

  renderEventMarkers(): void {
    this.clearEventMarkers();
    if (!this.mainChart || this.candles.length === 0) return;

    const events = this.getFilteredEvents();
    const timeScale = this.mainChart.timeScale();

    events.forEach(ev => {
      const x = timeScale.timeToCoordinate((ev.time as unknown) as UTCTimestamp);
      if (x == null) return;

      const marker = document.createElement('div');
      marker.className = `event-marker event-marker-${ev.type}`;
      marker.dataset['eventId'] = ev.id;
      marker.dataset['eventType'] = ev.type;
      marker.title = ev.title;

      // Icon per type
      const icons: Record<string, string> = {
        haber: 'N', kap: 'K', bilanco: 'B', temettu: 'T', sermaye: 'S',
      };
      marker.textContent = icons[ev.type] ?? '●';
      marker.style.left = `${x}px`;

      // Click → show tooltip / dispatch event
      marker.addEventListener('click', (e) => {
        e.stopPropagation();
        this.showEventTooltip(ev, marker);

        if (ev.type === 'bilanco') {
          this.container.dispatchEvent(new CustomEvent('openFinancialAnalysis', {
            bubbles: true,
            detail: { symbol: ev.symbol, date: ev.time, eventId: ev.id },
          }));
        }
      });

      this.mainEl.appendChild(marker);
      this.eventMarkerEls.set(ev.id, marker);
    });
  }

  private repositionEventMarkers(): void {
    if (!this.mainChart) return;
    const timeScale = this.mainChart.timeScale();
    this.chartEvents.forEach(ev => {
      const el = this.eventMarkerEls.get(ev.id);
      if (!el) return;
      const x = timeScale.timeToCoordinate((ev.time as unknown) as UTCTimestamp);
      if (x == null) {
        el.style.display = 'none';
      } else {
        el.style.display = '';
        el.style.left = `${x}px`;
      }
    });
  }

  private showEventTooltip(ev: ChartEvent, anchorEl: HTMLElement): void {
    if (!this.eventTooltipEl) return;

    const typeLabels: Record<string, string> = {
      haber: TR.EVENT_HABER,
      kap: TR.EVENT_KAP,
      bilanco: TR.EVENT_BILANCO,
      temettu: TR.EVENT_TEMETTU,
      sermaye: TR.EVENT_SERMAYE,
    };

    const dateStr = new Date(ev.time * 1000).toLocaleDateString('tr-TR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
    });

    this.eventTooltipEl.innerHTML = `
      <div class="event-tooltip-header">
        <span class="event-badge event-badge-${ev.type}">${typeLabels[ev.type] ?? ev.type}</span>
        <button class="event-tooltip-close" title="Kapat">×</button>
      </div>
      <div class="event-tooltip-title">${ev.title}</div>
      <div class="event-tooltip-summary">${ev.summary}</div>
      <div class="event-tooltip-meta">
        <span>${TR.EVENT_DATE}: ${dateStr}</span>
        <span>${TR.EVENT_SOURCE}: ${ev.source}</span>
      </div>
      <div class="event-tooltip-notice">${TR.EVENT_SAMPLE}</div>
      ${ev.type === 'bilanco' ? `<button class="event-open-financial" data-event-id="${ev.id}">${TR.EVENT_OPEN_FINANCIAL}</button>` : ''}
    `;

    // Position tooltip near marker
    const markerRect = anchorEl.getBoundingClientRect();
    const containerRect = this.mainEl.getBoundingClientRect();
    let left = markerRect.left - containerRect.left + 10;
    const top = markerRect.bottom - containerRect.top + 4;
    // Keep in bounds
    left = Math.min(left, containerRect.width - 260);

    this.eventTooltipEl.style.left = `${left}px`;
    this.eventTooltipEl.style.top = `${top}px`;
    this.eventTooltipEl.style.display = 'block';

    // Close button
    this.eventTooltipEl.querySelector('.event-tooltip-close')?.addEventListener('click', () => {
      this.eventTooltipEl!.style.display = 'none';
    });
  }

  /** Build the G9 event filter toolbar HTML */
  eventFilterHTML(): string {
    const types: Array<{ key: ChartEventType | 'all'; label: string }> = [
      { key: 'all', label: TR.EVENT_ALL },
      ...EVENT_FILTER_TYPES.map(key => ({
        key,
        label: this.eventTypeLabel(key),
      })),
    ];

    return `
      <div class="tool-cluster event-filter-cluster">
        <button class="tool-trigger" type="button"><span>${TR.EVENTS}</span><b>Filtre</b></button>
        <div class="tool-inline event-filter-group">
        ${types.map(t => `
          <button class="ctrl-btn event-filter-btn${t.key === 'all' || this.activeEventTypes.has(t.key as ChartEventType) ? ' active' : ''}"
                  data-event-filter="${t.key}">${t.label}</button>
        `).join('')}
        <span class="event-source-badge" title="${TR.EVENT_NO_SOURCE}">⚠ ${TR.EVENT_SAMPLE}</span>
        </div>
      </div>
    `;
  }

  bindEventFilterControls(controls: HTMLElement): void {
    controls.addEventListener('click', (e) => {
      const btn = (e.target as HTMLElement).closest<HTMLElement>('.event-filter-btn');
      if (!btn) return;
      const filter = btn.dataset['eventFilter'] as ChartEventType | 'all';

      if (filter === 'all') {
        this.activeEventTypes = new Set(EVENT_FILTER_TYPES);
      } else {
        if (this.activeEventTypes.has(filter)) {
          this.activeEventTypes.delete(filter);
        } else {
          this.activeEventTypes.add(filter);
        }
      }

      this.syncEventFilterButtons();
      this.renderEventMarkers();
    });
  }

  private eventTypeLabel(type: ChartEventType): string {
    const labels: Record<ChartEventType, string> = {
      haber: TR.EVENT_HABER,
      kap: TR.EVENT_KAP,
      bilanco: TR.EVENT_BILANCO,
      temettu: TR.EVENT_TEMETTU,
      sermaye: TR.EVENT_SERMAYE,
    };
    return labels[type];
  }

  private syncEventFilterButtons(): void {
    const allActive = EVENT_FILTER_TYPES.every(type => this.activeEventTypes.has(type));
    this.container.dataset['eventFilter'] = allActive
      ? 'all'
      : Array.from(this.activeEventTypes).join(',');

    this.container.querySelectorAll<HTMLElement>('.event-filter-btn').forEach(btn => {
      const filter = btn.dataset['eventFilter'] as ChartEventType | 'all';
      btn.classList.toggle('active', filter === 'all' ? allActive : this.activeEventTypes.has(filter));
    });
  }
}
