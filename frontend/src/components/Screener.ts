import type { ScreenerResult, ScreenerFilter, OHLCV } from '../types.js';
import { computeIndicators, lastValid } from '../indicators/index.js';
import { TR, formatNumber, formatPct } from '../constants/tr.js';
import { ALL_SYMBOLS } from '../constants/symbols.js';
import { SMA } from '../indicators/index.js';

// ─── Screener ─────────────────────────────────────────────────────────────────

type SortCol = 'symbol' | 'price' | 'changePct' | 'rsi' | 'emaSignal' | 'bbPosition';
type SortDir = 'asc' | 'desc';

export class Screener {
  private container: HTMLElement;
  private activeFilters = new Set<ScreenerFilter>();
  private results: ScreenerResult[] = [];
  private runMeta: { run_id: string; filters_hash: string; data_snapshot_hash: string; created_at: string } | null = null;
  private emptyMessage: string = TR.NO_RESULTS;
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
    this.emptyMessage = TR.NO_RESULTS;

    await new Promise(resolve => requestAnimationFrame(resolve));

    try {
      const backendResult = await this.scanBackend();
      if (backendResult) {
        this.results = backendResult;
      } else {
        const cache = this.getCache();
        this.results = [];
        this.runMeta = null;

        for (const symInfo of ALL_SYMBOLS) {
          const candles = cache.get(symInfo.symbol);
          if (!candles || candles.length < 30) continue;

          const result = this.analyzeSymbol(symInfo.symbol, symInfo.name, candles);
          if (this.passesFilters(result)) {
            this.results.push(result);
          }
        }
      }

      this.renderResults();
    } finally {
      scanBtn.disabled = false;
      scanBtn.textContent = TR.SCAN;
    }
  }

  private backendFilters(): Array<{ column: string; op: string; value: number | string }> {
    const filters: Array<{ column: string; op: string; value: number | string }> = [];
    for (const f of this.activeFilters) {
      if (f === 'rsi_oversold') filters.push({ column: 'rsi_14', op: 'lt', value: 30 });
      if (f === 'rsi_overbought') filters.push({ column: 'rsi_14', op: 'gt', value: 70 });
      if (f === 'high_volume') filters.push({ column: 'volume', op: 'gt', value: 0 });
    }
    return filters;
  }

  private async scanBackend(): Promise<ScreenerResult[] | null> {
    try {
      const res = await fetch('/api/screener/run', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          market: 'CRYPTO',
          universe: 'CRYPTO',
          filters: this.backendFilters(),
          columns: ['symbol', 'last_price', 'change_pct', 'rsi_14', 'volume', 'volume_avg_20d'],
          sort_by: 'volume',
          sort_dir: 'desc',
          limit: 100,
        }),
      });
      if (res.status === 401 || res.status === 403) {
        this.runMeta = null;
        this.emptyMessage = 'Tarayıcı için giriş yapmanız veya planınızı yükseltmeniz gerekiyor.';
        return [];
      }
      if (!res.ok) return null;
      const data = await res.json() as {
        run_id: string;
        created_at: string;
        filters_hash: string;
        data_snapshot_hash: string;
        rows?: Array<{
          symbol: string;
          name?: string;
          last_price?: number | null;
          change_pct?: number | null;
          rsi_14?: number | null;
          volume?: number | null;
          volume_avg_20d?: number | null;
          distance_from_52w_high?: number | null;
        }>;
      };
      this.runMeta = {
        run_id: data.run_id,
        created_at: data.created_at,
        filters_hash: data.filters_hash,
        data_snapshot_hash: data.data_snapshot_hash,
      };
      return (data.rows ?? []).map(row => ({
        symbol: row.symbol,
        name: row.name ?? row.symbol,
        price: row.last_price ?? 0,
        changePct: row.change_pct ?? 0,
        rsi: row.rsi_14 ?? 50,
        emaSignal: 'Nötr',
        bbPosition: 'Normal',
        volumeAlert: Boolean(row.volume && row.volume_avg_20d && row.volume > row.volume_avg_20d * 1.5),
        alerts: [],
        volumeAvg20d: row.volume_avg_20d ?? undefined,
        distFrom52wHigh: row.distance_from_52w_high ?? undefined,
      }));
    } catch {
      return null;
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

  private sortResults(): ScreenerResult[] {
    const dir = this.sortDir === 'asc' ? 1 : -1;
    return [...this.results].sort((a, b) => {
      switch (this.sortCol) {
        case 'symbol':    return dir * a.symbol.localeCompare(b.symbol);
        case 'price':     return dir * (a.price - b.price);
        case 'changePct': return dir * (a.changePct - b.changePct);
        case 'rsi':       return dir * (a.rsi - b.rsi);
        case 'emaSignal': return dir * a.emaSignal.localeCompare(b.emaSignal);
        case 'bbPosition':return dir * a.bbPosition.localeCompare(b.bbPosition);
        default:          return 0;
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
      el.innerHTML = `<div class="empty-state">${this.emptyMessage}</div>`;
      return;
    }

    const sorted = this.sortResults();

    const meta = this.runMeta
      ? `<div class="screener-run-meta">Run ${this.runMeta.run_id.slice(0, 8)} · filtre ${this.runMeta.filters_hash.slice(0, 8)} · snapshot ${this.runMeta.data_snapshot_hash.slice(0, 8)}</div>`
      : '<div class="screener-run-meta">Local cache taraması · backend snapshot yok</div>';

    el.innerHTML = `
      <div class="screener-count">${this.results.length} sembol bulundu</div>
      ${meta}
      <table class="data-table screener-table">
        <thead>
          <tr>
            ${this.thHTML('symbol', TR.SYMBOL)}
            ${this.thHTML('price', TR.PRICE)}
            ${this.thHTML('changePct', TR.CHANGE_PCT)}
            ${this.thHTML('rsi', 'RSI')}
            ${this.thHTML('emaSignal', TR.EMA_SIGNAL)}
            ${this.thHTML('bbPosition', TR.BB_POSITION)}
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
        <td class="screener-actions">
          <button class="btn-sm screener-chart" data-chart="${r.symbol}" title="Grafikte aç">📈</button>
          <button class="btn-sm screener-backtest" data-backtest="${r.symbol}" title="Bu sembolü backtest için aç">▶ BT</button>
        </td>
      </tr>
    `;
  }
}
