import type { ScreenerResult, ScreenerFilter, OHLCV } from '../types.js';
import { computeIndicators, lastValid } from '../indicators/index.js';
import { TR, formatNumber, formatPct } from '../constants/tr.js';
import { ALL_SYMBOLS } from '../constants/symbols.js';
import { SMA } from '../indicators/index.js';

const ICON_CHART = '<svg class="icon-svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>';
const ICON_NEWS = '<svg class="icon-svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 22h16a2 2 0 0 0 2-2V4H2v16a2 2 0 0 0 2 2z"/><path d="M8 8h8"/><path d="M8 12h8"/><path d="M8 16h5"/></svg>';
const ICON_PLAY = '<svg class="icon-svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>';

// ─── Screener ─────────────────────────────────────────────────────────────────

type SortCol = 'symbol' | 'price' | 'changePct' | 'rsi' | 'emaSignal' | 'bbPosition' | 'volumeAvg20d' | 'distFrom52wHigh';
type SortDir = 'asc' | 'desc';

export class Screener {
  private container: HTMLElement;
  private activeFilters = new Set<ScreenerFilter>();
  private results: ScreenerResult[] = [];
  private getCache: () => Map<string, OHLCV[]>;
  private sortCol: SortCol = 'changePct';
  private sortDir: SortDir = 'desc';

  constructor(container: HTMLElement, getCache: () => Map<string, OHLCV[]>) {
    this.container = container;
    this.getCache  = getCache;
    this.render();
  }

  // ─── Render ──────────────────────────────────────────────────────────────

  private render(): void {
    this.container.innerHTML = `
      <div class="screener-wrap">
        <div class="screener-header">
          <h2>${TR.SCREENER_TITLE}</h2>
          <div class="filter-bar">
            ${this.filterButtonsHTML()}
            <button class="btn-primary scan-btn" id="scan-btn">${TR.SCAN}</button>
          </div>
        </div>
        <div id="screener-results"></div>
      </div>
    `;

    this.bindFilters();
  }

  private filterButtonsHTML(): string {
    const filters: { id: ScreenerFilter; label: string }[] = [
      { id: 'rsi_oversold',   label: TR.RSI_OVERSOLD   },
      { id: 'rsi_overbought', label: TR.RSI_OVERBOUGHT  },
      { id: 'ema_bullish',    label: TR.EMA_BULLISH     },
      { id: 'bb_lower',       label: TR.BB_LOWER        },
      { id: 'high_volume',    label: TR.HIGH_VOLUME     },
    ];

    return filters.map(f => `
      <button class="filter-btn" data-filter="${f.id}">${f.label}</button>
    `).join('');
  }

  private bindFilters(): void {
    this.container.querySelectorAll<HTMLButtonElement>('.filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const filter = btn.dataset['filter'] as ScreenerFilter;
        if (this.activeFilters.has(filter)) {
          this.activeFilters.delete(filter);
          btn.classList.remove('active');
        } else {
          this.activeFilters.add(filter);
          btn.classList.add('active');
        }
      });
    });

    const scanBtn = this.container.querySelector<HTMLButtonElement>('#scan-btn')!;
    scanBtn.addEventListener('click', () => this.scan());
  }

  // ─── Scan ────────────────────────────────────────────────────────────────

  async scan(): Promise<void> {
    const scanBtn = this.container.querySelector<HTMLButtonElement>('#scan-btn')!;
    const resultsEl = this.container.querySelector('#screener-results')!;

    scanBtn.disabled = true;
    scanBtn.textContent = TR.SCANNING;
    resultsEl.innerHTML = `<div class="loading">${TR.SCANNING}</div>`;

    await new Promise(resolve => requestAnimationFrame(resolve));

    try {
      const cache = this.getCache();
      this.results = [];

      const totalSymbols = ALL_SYMBOLS.length;
      let cachedCount = 0;
      for (const symInfo of ALL_SYMBOLS) {
        const candles = cache.get(symInfo.symbol);
        if (candles && candles.length >= 30) cachedCount++;
      }

      if (cachedCount === 0) {
        resultsEl.innerHTML = `
          <div class="empty-state">
            <div class="empty-icon">⚠️</div>
            <div class="empty-title">Veri henüz hazır değil</div>
            <div class="empty-desc">Cache boş görünüyor. Uygulama arka planda veri yüklüyor olabilir. Birkaç saniye bekleyip tekrar deneyin. Sembol grafikleri ziyaret etmek cache'i hızlandırır.</div>
          </div>
        `;
        return;
      }

      if (cachedCount < totalSymbols * 0.5) {
        resultsEl.innerHTML = `<div class="screener-cache-warn">⚠️ ${cachedCount}/${totalSymbols} sembol cache'de — bazı sonuçlar eksik olabilir. Sonuçlar kısmi gösteriliyor.</div>`;
      }

      for (const symInfo of ALL_SYMBOLS) {
        const candles = cache.get(symInfo.symbol);
        if (!candles || candles.length < 30) continue;

        const result = this.analyzeSymbol(symInfo.symbol, symInfo.name, candles);
        if (this.passesFilters(result)) {
          this.results.push(result);
        }
      }

      this.renderResults();
    } finally {
      scanBtn.disabled = false;
      scanBtn.textContent = TR.SCAN;
    }
  }

  // ─── Analysis ────────────────────────────────────────────────────────────

  private analyzeSymbol(symbol: string, name: string, candles: OHLCV[]): ScreenerResult {
    const inds = computeIndicators(candles);
    const n    = candles.length;
    const last = candles[n - 1]!;
    const prev = candles[n - 2]!;

    const rsi   = lastValid(inds.rsi)   ?? 50;
    const ema9  = lastValid(inds.ema9)  ?? last.close;
    const ema21 = lastValid(inds.ema21) ?? last.close;
    const bbU   = inds.bb?.upper[n - 1];
    const bbM   = inds.bb?.mid[n - 1];
    const bbL   = inds.bb?.lower[n - 1];
    const vols  = candles.map(c => c.volume);
    const avgVolArr = SMA(vols, 20);
    const avgVol = avgVolArr[n - 1] ?? 0;

    const changePct = prev.close !== 0
      ? ((last.close - prev.close) / prev.close) * 100
      : 0;

    // EMA signal
    let emaSignal: ScreenerResult['emaSignal'] = 'Nötr';
    if (!isNaN(ema9) && !isNaN(ema21)) {
      if (ema9 > ema21) emaSignal = 'Yükseliş';
      else if (ema9 < ema21) emaSignal = 'Düşüş';
    }

    // BB position
    let bbPosition: ScreenerResult['bbPosition'] = 'Normal';
    if (bbL && bbU && bbM && !isNaN(bbL)) {
      if (last.close <= bbL * 1.01) bbPosition = 'Alt Band';
      else if (last.close >= bbU * 0.99) bbPosition = 'Üst Band';
      else if (Math.abs(last.close - bbM) / bbM < 0.005) bbPosition = 'Orta';
    }

    // Volume alert
    const volumeAlert = avgVol > 0 && last.volume > avgVol * 1.5;

    // Volume avg 20d
    const volumeAvg20d = avgVol > 0 ? avgVol : undefined;

    // 52-haftalık zirveye mesafe
    const highs = candles.map(c => c.high);
    const high52w = highs.length > 0 ? Math.max(...highs) : 0;
    const distFrom52wHigh = high52w > 0
      ? Math.round(((last.close - high52w) / high52w) * 10000) / 100
      : undefined;

    // Alerts list
    const alerts: string[] = [];
    if (rsi < 30)  alerts.push(TR.RSI_OVERSOLD);
    if (rsi > 70)  alerts.push(TR.RSI_OVERBOUGHT);
    if (emaSignal === 'Yükseliş') alerts.push(TR.EMA_BULLISH);
    if (bbPosition === 'Alt Band') alerts.push(TR.BB_LOWER);
    if (volumeAlert) alerts.push(TR.HIGH_VOLUME);

    return {
      symbol,
      name,
      price: last.close,
      changePct,
      rsi,
      emaSignal,
      bbPosition,
      volumeAlert,
      alerts,
      volumeAvg20d,
      distFrom52wHigh,
    };
  }

  private passesFilters(r: ScreenerResult): boolean {
    if (this.activeFilters.size === 0) return true; // no filter = show all scanned

    for (const f of this.activeFilters) {
      switch (f) {
        case 'rsi_oversold':   if (r.rsi < 30)                   return true; break;
        case 'rsi_overbought': if (r.rsi > 70)                   return true; break;
        case 'ema_bullish':    if (r.emaSignal === 'Yükseliş')   return true; break;
        case 'bb_lower':       if (r.bbPosition === 'Alt Band')  return true; break;
        case 'high_volume':    if (r.volumeAlert)                return true; break;
      }
    }
    return false;
  }

  // ─── Results table ───────────────────────────────────────────────────────

  private sortResults(): ScreenerResult[] {
    const dir = this.sortDir === 'asc' ? 1 : -1;
    const numSort = (a: number | undefined, b: number | undefined) =>
      ((a ?? -Infinity) - (b ?? -Infinity)) * dir;
    return [...this.results].sort((a, b) => {
      switch (this.sortCol) {
        case 'symbol':          return dir * a.symbol.localeCompare(b.symbol);
        case 'price':           return dir * (a.price - b.price);
        case 'changePct':       return dir * (a.changePct - b.changePct);
        case 'rsi':             return dir * (a.rsi - b.rsi);
        case 'emaSignal':       return dir * a.emaSignal.localeCompare(b.emaSignal);
        case 'bbPosition':      return dir * a.bbPosition.localeCompare(b.bbPosition);
        case 'volumeAvg20d':    return numSort(a.volumeAvg20d, b.volumeAvg20d);
        case 'distFrom52wHigh': return numSort(a.distFrom52wHigh, b.distFrom52wHigh);
        default:                return 0;
      }
    });
  }

  private thHTML(col: SortCol, label: string): string {
    const active = this.sortCol === col;
    const arrow = active ? (this.sortDir === 'asc' ? ' ▲' : ' ▼') : '';
    return `<th class="sortable-th${active ? ' sort-active' : ''}" data-sort="${col}">${label}${arrow}</th>`;
  }

  private renderResults(): void {
    const el = this.container.querySelector('#screener-results')!;

    if (this.results.length === 0) {
      el.innerHTML = `<div class="empty-state">${TR.NO_RESULTS}</div>`;
      return;
    }

    const sorted = this.sortResults();

    const nowStr = new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    el.innerHTML = `
      <div class="screener-count">${this.results.length} sembol bulundu <span class="screener-scan-time">— Son tarama: ${nowStr}</span></div>
      <table class="data-table screener-table">
        <thead>
          <tr>
            ${this.thHTML('symbol', TR.SYMBOL)}
            ${this.thHTML('price', TR.PRICE)}
            ${this.thHTML('changePct', TR.CHANGE_PCT)}
            ${this.thHTML('rsi', 'RSI')}
            ${this.thHTML('emaSignal', TR.EMA_SIGNAL)}
            ${this.thHTML('bbPosition', TR.BB_POSITION)}
            ${this.thHTML('volumeAvg20d', 'Hac.Ort.20')}
            ${this.thHTML('distFrom52wHigh', '52h Zirve%')}
            <th>${TR.VOLUME_ALERT}</th>
            <th>${TR.ALERTS}</th>
            <th>İşlem</th>
          </tr>
        </thead>
        <tbody>
          ${sorted.map(r => this.rowHTML(r)).join('')}
        </tbody>
      </table>
    `;

    el.querySelectorAll<HTMLElement>('.sortable-th').forEach(th => {
      th.style.cursor = 'pointer';
      th.addEventListener('click', () => {
        const col = th.dataset['sort'] as SortCol;
        if (this.sortCol === col) {
          this.sortDir = this.sortDir === 'asc' ? 'desc' : 'asc';
        } else {
          this.sortCol = col;
          this.sortDir = 'desc';
        }
        this.renderResults();
      });
    });

    el.querySelectorAll<HTMLButtonElement>('.screener-backtest').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const symbol = btn.dataset['backtest']!;
        window.dispatchEvent(new CustomEvent('addSymbolToBacktest', { detail: { symbol } }));
      });
    });

    el.querySelectorAll<HTMLButtonElement>('.screener-chart').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const symbol = btn.dataset['chart']!;
        window.dispatchEvent(new CustomEvent('openSymbolOnChart', { detail: { symbol } }));
      });
    });

    el.querySelectorAll<HTMLButtonElement>('.screener-news').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const symbol = btn.dataset['news']!;
        window.dispatchEvent(new CustomEvent('openNewsForSymbol', { detail: { symbol } }));
      });
    });
  }

  private rowHTML(r: ScreenerResult): string {
    const rsiCls = r.rsi < 30 ? 'pos' : r.rsi > 70 ? 'neg' : '';
    const emaCls = r.emaSignal === 'Yükseliş' ? 'pos' : r.emaSignal === 'Düşüş' ? 'neg' : '';
    const bbCls  = r.bbPosition === 'Alt Band' ? 'pos' : r.bbPosition === 'Üst Band' ? 'neg' : '';

    const fmtVol = (v?: number) => v != null ? formatNumber(v, 0) : '—';
    const fmtDist = (v?: number) => v != null
      ? `<span class="${v >= 0 ? 'pos' : 'neg'}">${v.toFixed(1)}%</span>`
      : '—';
    return `
      <tr>
        <td class="sym-cell">${r.symbol}</td>
        <td>${formatNumber(r.price)}</td>
        <td class="${r.changePct >= 0 ? 'pos' : 'neg'}">${formatPct(r.changePct)}</td>
        <td class="${rsiCls}">${formatNumber(r.rsi, 1)}</td>
        <td class="${emaCls}">${r.emaSignal}</td>
        <td class="${bbCls}">${r.bbPosition}</td>
        <td style="font-size:11px;color:var(--text-dim)">${fmtVol(r.volumeAvg20d)}</td>
        <td>${fmtDist(r.distFrom52wHigh)}</td>
        <td>${r.volumeAlert ? '⚡' : '—'}</td>
        <td class="alerts-cell">${r.alerts.slice(0, 3).map(a => `<span class="alert-tag">${a}</span>`).join('')}</td>
        <td class="screener-actions">
          <button class="btn-sm screener-chart" data-chart="${r.symbol}" title="Grafikte aç">${ICON_CHART}</button>
          <button class="btn-sm screener-backtest" data-backtest="${r.symbol}" title="Bu sembolü backtest için aç">${ICON_PLAY} BT</button>
          <button class="btn-sm screener-news" data-news="${r.symbol}" title="Bu sembolün haberlerini aç">${ICON_NEWS}</button>
        </td>
      </tr>
    `;
  }
}
