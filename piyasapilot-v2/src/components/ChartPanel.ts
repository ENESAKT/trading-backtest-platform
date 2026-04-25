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
} from 'lightweight-charts';
import type { OHLCV, Timeframe, ChartType, IndicatorSet } from '../types.js';
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

  private activeIndicators: Set<string> = new Set(['bb', 'ema', 'vwap', 'rsi', 'macd', 'vol']);
  private candles: OHLCV[] = [];
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
    this.container.style.cssText = 'display:flex;flex-direction:column;height:100%;background:' + C.bg;

    // Controls bar
    const controls = document.createElement('div');
    controls.className = 'chart-controls';
    controls.innerHTML = this.controlsHTML();
    this.container.appendChild(controls);

    // Crosshair info overlay
    this.infoEl = document.createElement('div');
    this.infoEl.className = 'chart-info-overlay';
    this.container.appendChild(this.infoEl);

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
    });
    this.lineSeries = this.mainChart.addLineSeries({ color: C.blue, lineWidth: 2, visible: false });
    this.barSeries  = this.mainChart.addBarSeries({ upColor: C.green, downColor: C.red, visible: false });

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

  setData(candles: OHLCV[]): void {
    if (candles.length === 0) return;
    this.candles = candles;

    const cData = candles.map(c => ({
      time: c.time as UTCTimestamp,
      open: c.open, high: c.high, low: c.low, close: c.close,
    }));

    this.candleSeries.setData(cData as CandlestickData[]);
    this.lineSeries.setData(candles.map(c => ({ time: c.time as UTCTimestamp, value: c.close })) as LineData[]);
    this.barSeries.setData(cData as BarData[]);

    this.renderVolume(candles);
    this.renderIndicators(candles);

    this.mainChart.timeScale().fitContent();
  }

  updateLastCandle(candle: OHLCV): void {
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
    this.candleSeries.applyOptions({ visible: type === 'candlestick' });
    this.lineSeries.applyOptions({ visible: type === 'line' });
    this.barSeries.applyOptions({ visible: type === 'bar' });
  }

  // ─── Crosshair info overlay ────────────────────────────────────────────

  private updateInfoOverlay(c: OHLCV, inds: IndicatorSet, i: number): void {
    const rsi   = lastValid(inds.rsi?.slice(0, i + 1)) ?? null;
    const macd  = inds.macd?.macd[i];
    const ema9  = inds.ema9?.[i];
    const ema21 = inds.ema21?.[i];

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
