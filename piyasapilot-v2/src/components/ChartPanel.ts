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
} from 'lightweight-charts';
import type { OHLCV, Timeframe, ChartType, IndicatorSet, Signal, ChartDataStatus, ChartViewOptions } from '../types.js';
import { computeIndicators, lastValid } from '../indicators/index.js';
import { TR, formatNumber, formatDateTime } from '../constants/tr.js';

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

const PRICE_SHIFT_RESET_RATIO = 2.5;

// ─── ChartPanel ───────────────────────────────────────────────────────────────

export class ChartPanel {
  private container: HTMLElement;

  // Sub-containers for each chart row
  private mainEl!:   HTMLElement;
  private volEl!:    HTMLElement;
  private rsiEl!:    HTMLElement;
  private macdEl!:   HTMLElement;

  // Chart instances
  private mainChart!:  IChartApi;
  private volChart!:   IChartApi;
  private rsiChart!:   IChartApi;
  private macdChart!:  IChartApi;

  // Series references
  private candleSeries!:  ISeriesApi<'Candlestick'>;
  private lineSeries!:    ISeriesApi<'Line'>;
  private barSeries!:     ISeriesApi<'Bar'>;
  private volSeries!:     ISeriesApi<'Histogram'>;
  private rsiSeries!:     ISeriesApi<'Line'>;
  private macdLineSeries!:   ISeriesApi<'Line'>;
  private macdSigSeries!:    ISeriesApi<'Line'>;
  private macdHistSeries!:   ISeriesApi<'Histogram'>;

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

  private activeIndicators: Set<string> = new Set(['bb', 'ema', 'vwap', 'rsi', 'macd', 'vol']);
  private candles: OHLCV[] = [];
  private markerSignals: Signal[] = [];
  private chartType: ChartType = 'candlestick';
  private autoPriceScale = true;
  private showPreviousClose = true;
  private lastMedianPrice: number | null = null;
  private lastSymbol = '';
  private lastTimeframe: Timeframe | null = null;
  private dataStatus: ChartDataStatus = 'idle';
  private lastPriceLine: IPriceLine | null = null;
  private previousCloseLine: IPriceLine | null = null;
  private priceLineSeries: MainPriceSeries | null = null;
  private isFullscreen = false;
  private resizeObserver!: ResizeObserver;

  constructor(container: HTMLElement) {
    this.container = container;
    this.buildDOM();
    this.initCharts();
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

    // Chart rows
    this.mainEl = this.addChartRow('60%');
    this.volEl  = this.addChartRow('12%');
    this.rsiEl  = this.addChartRow('14%');
    this.macdEl = this.addChartRow('14%');

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
        <button class="ctrl-btn ind-btn active" data-ind="bb">BB</button>
        <button class="ctrl-btn ind-btn active" data-ind="ema">EMA</button>
        <button class="ctrl-btn ind-btn active" data-ind="vwap">VWAP</button>
        <button class="ctrl-btn ind-btn active" data-ind="rsi">RSI</button>
        <button class="ctrl-btn ind-btn active" data-ind="macd">MACD</button>
      </div>
      <div class="ctrl-group">
        <span class="ctrl-label">Ölçek</span>
        <button class="ctrl-btn scale-auto-btn active" id="auto-price-btn" title="Otomatik fiyat ölçeği">Oto</button>
        <button class="ctrl-btn scale-reset-btn" id="price-reset-btn" title="Fiyatı yeniden ortala">⟲</button>
        <button class="ctrl-btn prev-close-btn active" id="prev-close-btn" title="Önceki kapanış çizgisi">ÖK</button>
      </div>
      <div class="ctrl-group ml-auto">
        <button class="ctrl-btn" id="fullscreen-btn" title="${TR.FULLSCREEN} (F)">⛶</button>
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
        this.updateIndicatorVisibility();
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

      const inds = computeIndicators(this.candles);
      const i = this.candles.indexOf(c);
      this.updateInfoOverlay(c, inds, i);
    });
  }

  // ─── Time scale sync ────────────────────────────────────────────────────

  private syncTimeScales(): void {
    const charts = [this.mainChart, this.volChart, this.rsiChart, this.macdChart];
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
    this.container.dataset['chartSymbol'] = this.lastSymbol;
    if (this.lastTimeframe) this.container.dataset['chartTimeframe'] = this.lastTimeframe;

    if (candles.length === 0 || status !== 'ready') {
      this.clearChartData();
      this.setStatusOverlay(status, options.message);
      return;
    }

    const currentMedian = this.medianClose(candles);
    const shouldResetPrice = this.shouldResetPriceScale(reason, currentMedian, options.preserveTimeRange);

    this.candles = candles;
    this.dataStatus = 'ready';
    this.hideStatus();

    const cData = candles.map(c => ({
      time: c.time as UTCTimestamp,
      open: c.open, high: c.high, low: c.low, close: c.close,
    }));

    this.candleSeries.setData(cData as CandlestickData[]);
    this.lineSeries.setData(candles.map(c => ({ time: c.time as UTCTimestamp, value: c.close })) as LineData[]);
    this.barSeries.setData(cData as BarData[]);

    this.renderVolume(candles);
    this.renderIndicators(candles);
    this.updateReferenceLines();

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
    this.candleSeries.setMarkers([]);
    this.infoEl.style.display = 'none';
    this.clearReferenceLines();
    this.lastMedianPrice = null;
    this.container.dataset['lastPrice'] = '';
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
    [this.mainChart, this.volChart, this.rsiChart, this.macdChart].forEach(chart => {
      try {
        chart.timeScale().setVisibleRange(range);
      } catch {
        // Farklı timeframe'lerde range dışarı taşarsa sessizce yeni veriye sığdır.
      }
    });
  }

  private resetPriceScales(): void {
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
      price: last.close,
      color: lastColor,
      lineWidth: 1,
      lineStyle: LineStyle.Solid,
      axisLabelVisible: true,
      title: 'Son',
      axisLabelColor: lastColor,
      axisLabelTextColor: C.bg,
    });
    this.container.dataset['lastPrice'] = String(last.close);

    const prev = this.candles[this.candles.length - 2];
    if (this.showPreviousClose && prev) {
      this.previousCloseLine = series.createPriceLine({
        id: 'previous-close',
        price: prev.close,
        color: C.text,
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
        axisLabelVisible: true,
        title: 'ÖK',
        axisLabelColor: C.border,
        axisLabelTextColor: C.textBold,
      });
    }
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
          text: `${s.open_position ? 'AÇIK ' : ''}${cfg.label} ${formatNumber(s.price)}`,
        };
      });
    this.candleSeries.setMarkers(markers);
  }

  clearSignals(): void {
    this.markerSignals = [];
    this.candleSeries.setMarkers([]);
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
    [this.mainChart, this.volChart, this.rsiChart, this.macdChart].forEach(chart => {
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

    const data = {
      time: candle.time as UTCTimestamp,
      open: candle.open, high: candle.high, low: candle.low, close: candle.close,
    };
    this.candleSeries.update(data as CandlestickData);
    this.lineSeries.update({ time: candle.time as UTCTimestamp, value: candle.close } as LineData);
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
    const inds = computeIndicators(candles);
    const times = candles.map(c => c.time as UTCTimestamp);

    const lineData = (arr: number[] | undefined): LineData[] =>
      arr
        ? arr.map((v, i) => ({ time: times[i]!, value: v })).filter(d => !isNaN(d.value)) as LineData[]
        : [];

    this.bbUpperSeries.setData(lineData(inds.bb?.upper));
    this.bbMidSeries.setData(lineData(inds.bb?.mid));
    this.bbLowerSeries.setData(lineData(inds.bb?.lower));
    this.ema9Series.setData(lineData(inds.ema9));
    this.ema21Series.setData(lineData(inds.ema21));
    this.ema50Series.setData(lineData(inds.ema50));
    this.vwapSeries.setData(lineData(inds.vwap));

    this.rsiSeries.setData(lineData(inds.rsi));

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
    const marker = this.markerSignals.find(s => s.timestamp === c.time);

    const fmt = (v: number | null | undefined) => v != null && !isNaN(v) ? formatNumber(v, 2) : '—';

    this.infoEl.style.display = 'block';
    this.infoEl.innerHTML = `
      <div class="ci-row"><span>O</span><b style="color:${C.textBold}">${fmt(c.open)}</b></div>
      <div class="ci-row"><span>H</span><b style="color:${C.green}">${fmt(c.high)}</b></div>
      <div class="ci-row"><span>L</span><b style="color:${C.red}">${fmt(c.low)}</b></div>
      <div class="ci-row"><span>C</span><b style="color:${c.close >= c.open ? C.green : C.red}">${fmt(c.close)}</b></div>
      <div class="ci-row"><span>V</span><b>${fmt(c.volume)}</b></div>
      ${rsi   != null ? `<div class="ci-row"><span>RSI</span><b style="color:${C.purple}">${formatNumber(rsi, 1)}</b></div>` : ''}
      ${macd  != null && !isNaN(macd) ? `<div class="ci-row"><span>MACD</span><b style="color:${C.blue}">${fmt(macd)}</b></div>` : ''}
      ${ema9  != null && !isNaN(ema9)  ? `<div class="ci-row"><span>EMA9</span><b style="color:${C.yellow}">${fmt(ema9)}</b></div>` : ''}
      ${ema21 != null && !isNaN(ema21) ? `<div class="ci-row"><span>EMA21</span><b style="color:${C.orange}">${fmt(ema21)}</b></div>` : ''}
      ${marker ? `
        <div class="ci-signal">
          <b>${marker.type}</b> ${fmt(marker.price)}
          ${marker.quantity ? `<span>Adet ${formatNumber(marker.quantity, 0)}</span>` : ''}
          ${marker.pnl != null ? `<span class="${marker.pnl >= 0 ? 'pos' : 'neg'}">PnL ${formatNumber(marker.pnl, 2)}</span>` : ''}
          ${marker.equity != null ? `<span>Equity ${formatNumber(marker.equity, 2)}</span>` : ''}
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

    const mainH = Math.floor(available * 0.60);
    const volH  = Math.floor(available * 0.12);
    const rsiH  = Math.floor(available * 0.14);
    const macdH = Math.floor(available * 0.14);

    this.mainChart.resize(w, mainH);
    this.volChart.resize(w, volH);
    this.rsiChart.resize(w, rsiH);
    this.macdChart.resize(w, macdH);
  }

  // ─── Cleanup ─────────────────────────────────────────────────────────────

  destroy(): void {
    this.resizeObserver.disconnect();
    this.mainChart.remove();
    this.volChart.remove();
    this.rsiChart.remove();
    this.macdChart.remove();
  }
}
