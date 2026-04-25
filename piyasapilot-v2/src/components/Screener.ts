import type { ScreenerResult, ScreenerFilter, OHLCV } from '../types.js';
import { computeIndicators, lastValid } from '../indicators/index.js';
import { TR, formatNumber, formatPct } from '../constants/tr.js';
import { ALL_SYMBOLS } from '../constants/symbols.js';
import { SMA } from '../indicators/index.js';

// ─── Screener ─────────────────────────────────────────────────────────────────

export class Screener {
  private container: HTMLElement;
  private activeFilters = new Set<ScreenerFilter>();
  private results: ScreenerResult[] = [];
  private getCache: () => Map<string, OHLCV[]>;

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

  private renderResults(): void {
    const el = this.container.querySelector('#screener-results')!;

    if (this.results.length === 0) {
      el.innerHTML = `<div class="empty-state">${TR.NO_RESULTS}</div>`;
      return;
    }

    el.innerHTML = `
      <div class="screener-count">${this.results.length} sembol bulundu</div>
      <table class="data-table screener-table">
        <thead>
          <tr>
            <th>${TR.SYMBOL}</th>
            <th>${TR.PRICE}</th>
            <th>${TR.CHANGE_PCT}</th>
            <th>RSI</th>
            <th>${TR.EMA_SIGNAL}</th>
            <th>${TR.BB_POSITION}</th>
            <th>${TR.VOLUME_ALERT}</th>
            <th>${TR.ALERTS}</th>
          </tr>
        </thead>
        <tbody>
          ${this.results.map(r => this.rowHTML(r)).join('')}
        </tbody>
      </table>
    `;
  }

  private rowHTML(r: ScreenerResult): string {
    const rsiCls = r.rsi < 30 ? 'pos' : r.rsi > 70 ? 'neg' : '';
    const emaCls = r.emaSignal === 'Yükseliş' ? 'pos' : r.emaSignal === 'Düşüş' ? 'neg' : '';
    const bbCls  = r.bbPosition === 'Alt Band' ? 'pos' : r.bbPosition === 'Üst Band' ? 'neg' : '';

    return `
      <tr>
        <td class="sym-cell">${r.symbol}</td>
        <td>${formatNumber(r.price)}</td>
        <td class="${r.changePct >= 0 ? 'pos' : 'neg'}">${formatPct(r.changePct)}</td>
        <td class="${rsiCls}">${formatNumber(r.rsi, 1)}</td>
        <td class="${emaCls}">${r.emaSignal}</td>
        <td class="${bbCls}">${r.bbPosition}</td>
        <td>${r.volumeAlert ? '⚡' : '—'}</td>
        <td class="alerts-cell">${r.alerts.slice(0, 3).map(a => `<span class="alert-tag">${a}</span>`).join('')}</td>
      </tr>
    `;
  }
}
