/**
 * MaliAnalizPanel — BIST finansal analiz paneli.
 * Veri: borsapy → MySQL. Sekmeler: Özet | BIST 30 | Bilanço | Gelir | Nakit | Oranlar | Grafikler
 */

import Chart from 'chart.js/auto';
import { createChart, ColorType, LineStyle } from 'lightweight-charts';
import type { IChartApi, ISeriesApi, UTCTimestamp } from 'lightweight-charts';

type TabId = 'summary' | 'comparison' | 'balance' | 'income' | 'cashflow' | 'ratios' | 'charts' | 'events' | 'reports';
type FinancialChartTarget = 'balance' | 'income' | 'cashflow' | 'ratios';

interface FetchStatus { status: string; last_period?: string; fetched_at?: string; periods_fetched?: number }
interface UniverseSymbol { symbol: string; name: string; fetch_status: FetchStatus }
interface Alert { id: number; symbol: string; alert_type: string; title: string; body: string; severity: string; period: string; metric_key: string; metric_value: number; created_at: string; is_read: boolean }
interface RatioRow { key: string; name: string; value: number | null; unit: string; category: string; period: string }
interface TableRow { row_index: number; label: string; values: Record<string, number | null> }
interface ComparisonRatioValue { value: number | null; unit: string }
interface ComparisonSymbol { symbol: string; name: string; period: string; ratios: Record<string, ComparisonRatioValue>; has_data: boolean }
interface ComparisonKeyMeta { label: string; unit: string }
interface ComparisonResponse { comparison_keys: string[]; key_meta: Record<string, ComparisonKeyMeta>; symbols: ComparisonSymbol[]; source: string }
interface ChartPoint { period: string; time: string; value: number }
interface ChartDataResponse { symbol: string; metrics: Record<string, ChartPoint[]>; source: string }
interface FinancialChartDef {
  key: string;
  title: string;
  unit: string;
  type: 'bar' | 'line';
  target: FinancialChartTarget;
}

const API = '/api/mali-analiz';
const ICON_CHART = '<svg class="icon-svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>';
const ICON_REFRESH = '<svg class="icon-svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 0 1-15.5 6.3L3 16"/><path d="M3 21v-5h5"/><path d="M3 12A9 9 0 0 1 18.5 5.7L21 8"/><path d="M21 3v5h-5"/></svg>';

const SEVERITY_BADGE: Record<string, string> = {
  danger: 'badge-danger', warning: 'badge-warning', success: 'badge-success', info: 'badge-info',
};

const CATEGORY_LABEL: Record<string, string> = {
  deger: 'Değerleme', karlilik: 'Karlılık', buyume: 'Büyüme',
  borc: 'Borç / Kaldıraç', nakit: 'Nakit Akışı', likidite: 'Likidite',
};

function fmt(val: number | null, unit = 'x', decimals = 2): string {
  if (val === null || val === undefined) return '—';
  if (unit === '%') return `${val.toFixed(decimals)}%`;
  if (unit === 'TRY') return fmtBig(val);
  return `${val.toFixed(decimals)}${unit === 'x' ? 'x' : ''}`;
}

function fmtBig(v: number): string {
  const abs = Math.abs(v);
  const sign = v < 0 ? '-' : '';
  if (abs >= 1e12) return `${sign}${(abs / 1e12).toFixed(2)} T`;
  if (abs >= 1e9)  return `${sign}${(abs / 1e9).toFixed(2)} Mr`;
  if (abs >= 1e6)  return `${sign}${(abs / 1e6).toFixed(1)} Mn`;
  return `${sign}${abs.toLocaleString('tr-TR')}`;
}

function colorClass(val: number | null, unit: string, key: string): string {
  if (val === null || !key) return '';
  if (['net_borc_ebitda', 'borc_ozkaynak'].includes(key)) {
    return val > 3 ? 'val-danger' : val > 1.5 ? 'val-warn' : 'val-good';
  }
  if (unit === '%' || key.includes('buyume') || key.includes('marji') || key === 'roe' || key === 'roa') {
    return val > 15 ? 'val-good' : val > 0 ? 'val-neutral' : 'val-danger';
  }
  if (key === 'fk') return val < 6 ? 'val-good' : val < 15 ? 'val-neutral' : 'val-warn';
  if (key === 'pd_dd') return val < 1 ? 'val-good' : val < 3 ? 'val-neutral' : 'val-warn';
  if (key === 'ev_ebitda') return val < 5 ? 'val-good' : val < 12 ? 'val-neutral' : 'val-warn';
  if (key === 'cari_oran') return val > 2 ? 'val-good' : val > 1 ? 'val-neutral' : 'val-danger';
  if (key === 'faiz_karsilama') return val > 3 ? 'val-good' : val > 1 ? 'val-neutral' : 'val-danger';
  return '';
}

function deltaArrow(curr: number | null, prev: number | null): string {
  if (curr === null || prev === null || prev === 0) return '';
  const pct = ((curr - prev) / Math.abs(prev)) * 100;
  const cls = pct >= 0 ? 'delta-up' : 'delta-down';
  return ` <span class="${cls}">${pct >= 0 ? '▲' : '▼'}${Math.abs(pct).toFixed(1)}%</span>`;
}

// Normalize a raw API ratio record to internal RatioRow format
function toRatioRow(r: Record<string, unknown>): RatioRow {
  return {
    key:    (r.ratio_key ?? r.key ?? '') as string,
    name:   (r.ratio_name ?? r.name ?? '') as string,
    value:  r.value as number | null,
    unit:   (r.unit ?? 'x') as string,
    category: (r.category ?? '') as string,
    period: (r.period ?? '') as string,
  };
}

export class MaliAnalizPanel {
  private container: HTMLElement;
  private activeTab: TabId = 'summary';
  private currentSymbol = 'THYAO';
  private universe: UniverseSymbol[] = [];
  private _universeLoaded = false;
  private universeQuery = '';
  private refreshing = false;
  private comparisonSortKey = 'symbol';
  private comparisonSortAsc = true;
  private _loadSeq = 0; // incremented on each loadTab call; used to discard stale responses

  // Per-(symbol,tab) data cache — cleared when switching to a NEW symbol
  // Key: `${symbol}:${tab}`, Value: the raw API response
  private _cache = new Map<string, unknown>();

  // DOM refs
  private titleEl!: HTMLElement;
  private tabsEl!: HTMLElement;
  private bodyEl!: HTMLElement;
  private statusBadgeEl!: HTMLElement;
  private refreshBtnEl!: HTMLButtonElement;
  private refreshAllBtnEl!: HTMLButtonElement;
  private chartBtnEl!: HTMLButtonElement;

  private _charts: IChartApi[] = [];
  private _chartByKey = new Map<string, IChartApi>();
  private _chartResizeObserver: ResizeObserver | null = null;
  private _waterfallChart: Chart | null = null;
  private _expandedCharts = new Set<string>();

  private readonly _handleThemeChange = (): void => {
    if (this.activeTab === 'charts') this.loadTab();
  };

  constructor(container: HTMLElement) {
    this.container = container;
    this.render();
    this.loadUniverse().then(() => this.autoFetchIfNeeded());
    this.loadTab();
    window.addEventListener('piyasapilot:theme-change', this._handleThemeChange);
  }

  destroy(): void {
    window.removeEventListener('piyasapilot:theme-change', this._handleThemeChange);
    this._destroyCharts();
  }

  // ── Layout ─────────────────────────────────────────────────────────────────

  private render(): void {
    this.container.innerHTML = `
      <div class="ma-root">
        <div class="ma-sidebar" id="ma-sidebar">
          <div class="ma-sidebar-search">
            <input type="text" placeholder="Sembol ara…" id="ma-sym-search" class="mali-search-input" />
          </div>
          <div class="ma-dot-legend" title="Veri durumu göstergesi">
            <span class="ma-sym-dot dot-ok">●</span> Tam veri
            <span class="ma-sym-dot dot-partial">●</span> Kısmi
            <span class="ma-sym-dot dot-empty">●</span> Veri yok
          </div>
          <div class="ma-universe-list" id="ma-universe-list">
            <div class="ma-loading">Yükleniyor…</div>
          </div>
        </div>
        <div class="ma-main">
          <div class="ma-topbar">
            <div class="ma-symbol-title" id="ma-title">
              <span class="ma-sym-code">${this.currentSymbol}</span>
              <span class="ma-sym-fullname">BIST şirket finansalları · BIST 30/BIST 100 kapsamı · Kaynak: borsapy/İş Yatırım</span>
            </div>
            <div class="ma-topbar-actions">
              <span class="ma-status-badge" id="ma-status-badge"></span>
              <button class="btn-sm btn-ghost" id="ma-chart-btn" title="Bu sembolü grafik panelinde aç">${ICON_CHART} Grafik</button>
              <button class="btn-sm btn-primary" id="ma-refresh-btn" title="Seçili sembolü güncelle">${ICON_REFRESH} Yenile</button>
              <button class="btn-sm btn-ghost" id="ma-refresh-all-btn" title="Tüm BIST 30'u güncelle">${ICON_REFRESH} BIST 30</button>
            </div>
          </div>
          <div class="ma-tabs" id="ma-tabs">
            <button class="ma-tab active" data-tab="summary">Özet</button>
            <button class="ma-tab" data-tab="comparison">BIST 30</button>
            <button class="ma-tab" data-tab="balance">Bilanço</button>
            <button class="ma-tab" data-tab="income">Gelir</button>
            <button class="ma-tab" data-tab="cashflow">Nakit</button>
            <button class="ma-tab" data-tab="ratios">Oranlar</button>
            <button class="ma-tab" data-tab="charts">Grafikler</button>
            <button class="ma-tab" data-tab="events">Olaylar</button>
            <button class="ma-tab" data-tab="reports">Raporlar</button>
          </div>
          <div class="ma-body" id="ma-body">
            <div class="ma-loading">Veriler yükleniyor…</div>
          </div>
        </div>
      </div>`;

    this.titleEl         = this.container.querySelector('#ma-title')!;
    this.tabsEl          = this.container.querySelector('#ma-tabs')!;
    this.bodyEl          = this.container.querySelector('#ma-body')!;
    this.statusBadgeEl   = this.container.querySelector('#ma-status-badge')!;
    this.refreshBtnEl    = this.container.querySelector('#ma-refresh-btn')!;
    this.refreshAllBtnEl = this.container.querySelector('#ma-refresh-all-btn')!;
    this.chartBtnEl      = this.container.querySelector('#ma-chart-btn')!;

    this.tabsEl.addEventListener('click', (e) => {
      const btn = (e.target as HTMLElement).closest('.ma-tab') as HTMLElement | null;
      if (!btn) return;
      const tab = btn.dataset.tab as TabId;
      if (tab) this.switchTab(tab);
    });

    this.refreshBtnEl.addEventListener('click', () => this.refreshSymbol());
    this.refreshAllBtnEl.addEventListener('click', () => this.refreshAll());
    this.chartBtnEl.addEventListener('click', () => this.openOnChart(this.currentSymbol));

    const searchInput = this.container.querySelector('#ma-sym-search') as HTMLInputElement;
    searchInput.addEventListener('input', () => {
      this.universeQuery = searchInput.value.toLowerCase();
      this.renderUniverseList();
    });
    searchInput.addEventListener('keydown', (e) => {
      if (e.key !== 'Enter') return;
      const query = searchInput.value.trim().toUpperCase();
      if (!query) return;
      const match = this.universe.find(s => s.symbol.toUpperCase() === query)
        || this.universe.find(s => s.symbol.toUpperCase().startsWith(query))
        || this.universe.find(s => s.name.toUpperCase().includes(query));
      this.selectSymbol(match?.symbol || query);
    });
  }

  // ── Cache helpers ─────────────────────────────────────────────────────────

  private cacheKey(tab: TabId): string { return `${this.currentSymbol}:${tab}`; }

  private getCached<T>(tab: TabId): T | null {
    const v = this._cache.get(this.cacheKey(tab));
    return v !== undefined ? (v as T) : null;
  }

  private setCache(tab: TabId, data: unknown): void {
    this._cache.set(this.cacheKey(tab), data);
  }

  private invalidateSymbol(symbol: string): void {
    for (const k of [...this._cache.keys()]) {
      if (k.startsWith(`${symbol}:`)) this._cache.delete(k);
    }
  }

  // ── Universe sidebar ───────────────────────────────────────────────────────

  private async loadUniverse(): Promise<void> {
    try {
      const resp = await fetch(`${API}/universe?scope=bist30`);
      const data = await resp.json();
      this.universe = data.symbols || [];
      this._universeLoaded = true;
      this.renderUniverseList();
    } catch {
      this.universe = [];
      this._universeLoaded = true;
    }
  }

  private renderUniverseList(): void {
    const list = this.container.querySelector('#ma-universe-list')!;
    if (!this._universeLoaded) {
      list.innerHTML = '<div class="ma-loading">Yükleniyor…</div>';
      return;
    }
    const filtered = this.universe.filter(s =>
      s.symbol.toLowerCase().includes(this.universeQuery) ||
      s.name.toLowerCase().includes(this.universeQuery)
    );
    if (!filtered.length) {
      list.innerHTML = `<div class="ma-empty">${this.universeQuery ? 'Sonuç yok' : 'Liste boş'}</div>`;
      return;
    }
    list.innerHTML = filtered.map(s => {
      const fs = s.fetch_status;
      const dotCls = fs.status === 'ok' ? 'dot-ok' : fs.status === 'no_data' ? 'dot-empty' : 'dot-partial';
      const active = s.symbol === this.currentSymbol ? ' active' : '';
      return `<div class="ma-sym-item${active}" data-symbol="${s.symbol}">
        <span class="ma-sym-dot ${dotCls}">●</span>
        <div class="ma-sym-info">
          <span class="ma-sym-code">${s.symbol}</span>
          <span class="ma-sym-name">${s.name}</span>
        </div>
        <div class="ma-sym-right">
          <span class="ma-sym-period">${fs.last_period || '—'}</span>
          <button class="ma-sym-chart-btn" data-chart-sym="${s.symbol}" title="Grafikte aç">${ICON_CHART}</button>
        </div>
      </div>`;
    }).join('');

    list.querySelectorAll('.ma-sym-item').forEach(el => {
      el.addEventListener('click', (e) => {
        // "📈 Grafikte aç" butonuna tıklandıysa finansal veri yerine grafik aç
        const chartBtn = (e.target as HTMLElement).closest('.ma-sym-chart-btn') as HTMLElement | null;
        if (chartBtn) {
          e.stopPropagation();
          this.openOnChart(chartBtn.dataset.chartSym!);
          return;
        }
        const sym = (el as HTMLElement).dataset.symbol!;
        this.selectSymbol(sym);
      });
    });
  }

  // ── Auto-fetch ─────────────────────────────────────────────────────────────

  private async autoFetchIfNeeded(): Promise<void> {
    const sym = this.universe.find(s => s.symbol === this.currentSymbol);
    if (sym && sym.fetch_status.status === 'no_data') {
      this.statusBadgeEl.className = 'ma-status-badge badge-info';
      this.statusBadgeEl.textContent = '↓ Veri çekiliyor…';
      await this.doRefreshSymbol(this.currentSymbol, false);
      await this.loadUniverse();
      this.loadTab();
    }
  }

  // ── Symbol selection ────────────────────────────────────────────────────────

  private selectSymbol(symbol: string): void {
    if (symbol === this.currentSymbol) return;
    this.currentSymbol = symbol;
    const info = this.universe.find(s => s.symbol === symbol);
    this.titleEl.innerHTML = `<span class="ma-sym-code">${symbol}</span>
      <span class="ma-sym-fullname">${info?.name || ''}</span>`;
    this.renderUniverseList();
    const fs = info?.fetch_status;
    this.updateStatusBadge(fs);
    if (fs && fs.status === 'no_data') {
      this.statusBadgeEl.className = 'ma-status-badge badge-info';
      this.statusBadgeEl.textContent = '↓ Veri çekiliyor…';
      this.doRefreshSymbol(symbol, false).then(() => {
        this.invalidateSymbol(symbol);
        this.loadUniverse().then(() => this.loadTab());
      });
    } else {
      this.loadTab();
    }
  }

  loadData(symbol: string): void {
    if (this._universeLoaded && this.universe.length > 0 && !this.universe.some(s => s.symbol === symbol)) {
      this.showUnsupportedSymbol(symbol);
      return;
    }
    this.selectSymbol(symbol);
  }

  private showUnsupportedSymbol(symbol: string): void {
    this.currentSymbol = symbol;
    this.titleEl.innerHTML = `<span class="ma-sym-code">${symbol}</span>
      <span class="ma-sym-fullname">Mali analiz kapsamı dışında</span>`;
    this.statusBadgeEl.className = 'ma-status-badge badge-empty';
    this.statusBadgeEl.textContent = 'Kapsam dışı';
    this.bodyEl.innerHTML = `
      <div class="ma-empty-block">
        Mali analiz şu anda BIST şirket finansalları için kullanılabilir. ${symbol} için bilanço/oran verisi beklenmez.
        Sol listeden BIST 30/BIST 100 sembolü seçin veya grafikte fiyat analizine devam edin.
      </div>`;
  }

  private openOnChart(symbol: string): void {
    window.dispatchEvent(new CustomEvent('openSymbolOnChart', { detail: { symbol } }));
  }

  // ── Tab switching ───────────────────────────────────────────────────────────

  private switchTab(tab: TabId): void {
    this.activeTab = tab;
    this.tabsEl.querySelectorAll('.ma-tab').forEach(b =>
      b.classList.toggle('active', (b as HTMLElement).dataset.tab === tab)
    );
    this.loadTab();
  }

  private loadTab(): void {
    this._destroyCharts();
    this._loadSeq++; // invalidate any in-flight requests
    this.bodyEl.innerHTML = '<div class="ma-loading">Yükleniyor…</div>';
    switch (this.activeTab) {
      case 'summary':    this.loadSummary();   break;
      case 'comparison': this.loadComparison(); break;
      case 'balance':    this.loadStatement('balance-sheet', 'Bilanço');       break;
      case 'income':     this.loadStatement('income-stmt',   'Gelir Tablosu'); break;
      case 'cashflow':   this.loadStatement('cashflow',      'Nakit Akışı');   break;
      case 'ratios':     this.loadRatios();       break;
      case 'charts':     this.loadCharts();       break;
      case 'events':     this.loadEvents();       break;
      case 'reports':    this.loadMaliReports();  break;
    }
  }

  private _destroyCharts(): void {
    this._chartResizeObserver?.disconnect();
    this._chartResizeObserver = null;
    this._charts.forEach(c => { try { c.remove(); } catch { /* ignore */ } });
    this._charts = [];
    this._chartByKey.clear();
    this._waterfallChart?.destroy();
    this._waterfallChart = null;
  }

  // ── Özet sekme ─────────────────────────────────────────────────────────────

  private async loadSummary(): Promise<void> {
    const sym = this.currentSymbol;
    const seq = this._loadSeq;
    try {
      let cached = this.getCached<{ summary: unknown; alerts: Alert[] }>('summary');
      if (!cached) {
        const [sResp, aResp] = await Promise.all([
          fetch(`${API}/${sym}/summary`),
          fetch(`${API}/alerts?limit=30`),
        ]);
        if (this._loadSeq !== seq) return; // symbol/tab changed while fetching
        const rawSummary = await sResp.json() as Record<string, unknown>;
        const summary = (rawSummary.summary && typeof rawSummary.summary === 'object')
          ? rawSummary.summary
          : rawSummary;
        const alertsData = await aResp.json();
        if (this._loadSeq !== seq) return;
        cached = { summary, alerts: alertsData.alerts || [] };
        this.setCache('summary', cached);
      }

      if (this._loadSeq !== seq) return;
      const { summary, alerts: allAlerts } = cached as { summary: Record<string, unknown>; alerts: Alert[] };

      // Only show error badge if data is actually absent; successful render clears stale errors
      const fetchStatus = this.universe.find(s => s.symbol === sym)?.fetch_status;
      const keyRatiosSource = (summary.key_ratios as Record<string, unknown>[] | undefined)
        ?? (summary.ratios as Record<string, unknown>[] | undefined)
        ?? [];
      const keyRatios: RatioRow[] = keyRatiosSource.map(toRatioRow);
      if (keyRatios.length > 0) {
        // Data loaded successfully — show green badge regardless of cached fetch_status
        this.statusBadgeEl.className = 'ma-status-badge badge-success';
        this.statusBadgeEl.textContent = `✓ ${fetchStatus?.last_period || 'Veri mevcut'} · ${fetchStatus?.periods_fetched ?? ''} dönem`.trim().replace(/· $/, '');
      } else {
        this.updateStatusBadge(fetchStatus);
      }

      this.bodyEl.innerHTML = `
        <div class="summary-header">
          <div class="summary-title-row">
            <h2>${String(summary.company_name || sym)}</h2>
            <span class="mali-symbol-badge">${sym}</span>
          </div>
        </div>
        ${this.renderKeyRatiosBar(keyRatios)}
        ${this.renderSummaryWarnings((summary.warnings as unknown[]) || [])}
        ${this.renderAlertsSection((summary.alerts as Alert[]) || [], 'Bu Sembol Direktifleri')}
        ${this.renderDisclosuresTable(allAlerts)}
      `;

      this.bodyEl.querySelectorAll('.btn-mark-read').forEach(btn => {
        btn.addEventListener('click', () => {
          const ids = JSON.parse((btn as HTMLElement).dataset.ids || '[]');
          this.markRead(ids);
        });
      });
      this.bodyEl.querySelectorAll<HTMLElement>('[data-disclosure-symbol]').forEach(row => {
        row.addEventListener('click', () => {
          const symbol = row.dataset.disclosureSymbol;
          if (!symbol) return;
          this.selectSymbol(symbol);
          this.switchTab('balance');
        });
      });
    } catch (e) {
      if (this._loadSeq !== seq) return;
      this.bodyEl.innerHTML = `<div class="ma-error">Özet yüklenemedi: ${e}</div>`;
    }
  }

  private renderKeyRatiosBar(ratios: RatioRow[]): string {
    if (!ratios.length) return '<div class="ma-empty-block">Oran verisi yok. BIST şirketleri için "Yenile" ile kaynak kontrolü yapılabilir; kripto/FX sembollerinde mali oran beklenmez.</div>';
    const cards = ratios.map(r => {
      const cls = colorClass(r.value, r.unit, r.key);
      return `<div class="ma-kpi-card ratio-box">
        <div class="ma-kpi-name">${r.name}</div>
        <div class="ma-kpi-val ${cls}">${fmt(r.value, r.unit)}</div>
        <div class="ma-kpi-period">${r.period}</div>
      </div>`;
    }).join('');
    return `<div class="ma-kpi-bar">${cards}</div>`;
  }

  private renderSummaryWarnings(warnings: unknown[]): string {
    if (!warnings.length) return '';
    const items = warnings
      .map(w => `<div class="warning-item">${String(w)}</div>`)
      .join('');
    return `<div class="warning-list">${items}</div>`;
  }

  private renderAlertsSection(alerts: Alert[], title: string): string {
    if (!alerts.length) return `<div class="ma-section"><div class="ma-section-title">${title}</div><div class="ma-empty">Direktif yok.</div></div>`;
    const items = alerts.map(a => `
      <div class="ma-alert-card ${a.severity}">
        <div class="ma-alert-head">
          <span class="ma-alert-badge ${SEVERITY_BADGE[a.severity] || 'badge-info'}">${a.severity.toUpperCase()}</span>
          <span class="ma-alert-title">${a.title}</span>
          <span class="ma-alert-period">${a.period || ''}</span>
        </div>
        <div class="ma-alert-body">${a.body}</div>
      </div>`).join('');
    return `<div class="ma-section"><div class="ma-section-title">${title}</div>${items}</div>`;
  }

  private renderDisclosuresTable(alerts: Alert[]): string {
    const disc = alerts.filter(a => a.alert_type === 'new_period');
    const title = 'Son Açıklanan Bilançolar (BIST 30)';
    if (!disc.length) return `<div class="ma-section"><div class="ma-section-title">${title}</div><div class="ma-empty">Henüz veri yok.</div></div>`;
    const unreadIds = disc.filter(a => !a.is_read).map(a => a.id);
    const markBtn = unreadIds.length
      ? `<button class="btn-sm btn-ghost btn-mark-read" data-ids='${JSON.stringify(unreadIds)}'>Tümünü okundu işaretle</button>`
      : '';
    const rows = disc.map(a => `
      <tr class="${a.is_read ? '' : 'row-unread'} ma-clickable-row" data-disclosure-symbol="${a.symbol}" title="${a.symbol} bilançosuna git">
        <td><strong>${a.symbol}</strong></td>
        <td>${a.period || '—'}</td>
        <td class="ma-alert-body-small">${a.body}</td>
        <td>${a.created_at ? new Date(a.created_at).toLocaleDateString('tr-TR') : '—'}</td>
      </tr>`).join('');
    return `<div class="ma-section">
      <div class="ma-section-title">${title} ${markBtn}</div>
      <div class="ma-table-wrap">
        <table class="ma-table">
          <thead><tr><th>Sembol</th><th>Dönem</th><th>Özet</th><th>Tarih</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>`;
  }

  // ── BIST 30 Karşılaştırma ─────────────────────────────────────────────────

  private async loadComparison(): Promise<void> {
    const seq = this._loadSeq;
    try {
      let data = this.getCached<ComparisonResponse>('comparison');
      if (!data) {
        const resp = await fetch(`${API}/comparison`);
        if (this._loadSeq !== seq) return;
        data = await resp.json() as ComparisonResponse;
        if (this._loadSeq !== seq) return;
        this.setCache('comparison', data);
      }
      if (this._loadSeq !== seq) return;
      this.renderComparisonTable(data);
    } catch (e) {
      if (this._loadSeq !== seq) return;
      this.bodyEl.innerHTML = `<div class="ma-error">Karşılaştırma yüklenemedi: ${e}</div>`;
    }
  }

  private renderComparisonTable(data: ComparisonResponse): void {
    const { comparison_keys, key_meta, symbols } = data;
    const hasData = symbols.filter(s => s.has_data);
    const noData  = symbols.filter(s => !s.has_data);

    if (!hasData.length) {
      this.bodyEl.innerHTML = `<div class="ma-empty-block">
        Henüz hiçbir sembol için veri çekilmedi.<br>
        Sol taraftan sembol seçip "Yenile" ile veri çekin,<br>
        veya "⟳ BIST 30" ile tümünü güncelleyin.
      </div>`;
      return;
    }

    const sorted = [...hasData].sort((a, b) => {
      if (this.comparisonSortKey === 'symbol') {
        return this.comparisonSortAsc
          ? a.symbol.localeCompare(b.symbol)
          : b.symbol.localeCompare(a.symbol);
      }
      const va = a.ratios[this.comparisonSortKey]?.value ?? null;
      const vb = b.ratios[this.comparisonSortKey]?.value ?? null;
      if (va === null && vb === null) return 0;
      if (va === null) return 1;
      if (vb === null) return -1;
      return this.comparisonSortAsc ? va - vb : vb - va;
    });

    const arr = (k: string) => this.comparisonSortKey !== k ? '' : (this.comparisonSortAsc ? ' ▲' : ' ▼');
    const headerCells = comparison_keys.map(k => {
      const m = key_meta[k];
      return `<th class="ma-cmp-sortable" data-sort="${k}">${m?.label || k}${arr(k)}</th>`;
    }).join('');

    const bodyRows = sorted.map(s => {
      const isActive = s.symbol === this.currentSymbol ? ' class="ma-cmp-row-active"' : '';
      const cells = comparison_keys.map(k => {
        const r = s.ratios[k];
        if (!r || r.value === null) return '<td class="ma-num">—</td>';
        const cls = colorClass(r.value, r.unit, k);
        return `<td class="ma-num ${cls}">${fmt(r.value, r.unit)}</td>`;
      }).join('');
      return `<tr${isActive} data-symbol="${s.symbol}" title="${s.name} finansal verilerini göster">
        <td class="ma-cmp-symbol">
          <strong>${s.symbol}</strong>
          <span class="ma-cmp-name">${s.name}</span>
          <button class="ma-cmp-chart-btn" data-chart-sym="${s.symbol}" title="Grafikte aç">${ICON_CHART}</button>
        </td>
        <td class="ma-cmp-period">${s.period}</td>
        ${cells}
      </tr>`;
    }).join('');

    const noDataNote = noData.length
      ? `<div class="ma-cmp-nodata">Veri yok (BDDK/format): ${noData.map(s => s.symbol).join(', ')}</div>`
      : '';

    this.bodyEl.innerHTML = `
      <div class="ma-table-header">
        <span class="ma-table-title">BIST 30 Finansal Karşılaştırma — ${hasData.length} şirket</span>
        <span class="ma-table-source">Sütun başlığına tıkla: sırala · Satıra tıkla: sembol seç</span>
      </div>
      <div class="ma-cmp-filter-row">
        <input type="text" id="ma-cmp-filter" class="ma-cmp-filter-input" placeholder="Şirket veya sembol ara…" />
      </div>
      ${noDataNote}
      <div class="ma-table-wrap" id="ma-cmp-table-wrap">
        <table class="ma-table ma-cmp-table">
          <thead>
            <tr>
              <th class="ma-cmp-sortable" data-sort="symbol">Şirket${arr('symbol')}</th>
              <th>Dönem</th>
              ${headerCells}
            </tr>
          </thead>
          <tbody>${bodyRows}</tbody>
        </table>
      </div>`;

    this.bodyEl.querySelectorAll('.ma-cmp-sortable').forEach(th => {
      th.addEventListener('click', () => {
        const key = (th as HTMLElement).dataset.sort!;
        this.comparisonSortKey === key
          ? (this.comparisonSortAsc = !this.comparisonSortAsc)
          : (this.comparisonSortKey = key, this.comparisonSortAsc = true);
        this.renderComparisonTable(data);
      });
    });

    // Filter input — live row filtering without re-fetching
    const filterInput = this.bodyEl.querySelector<HTMLInputElement>('#ma-cmp-filter');
    filterInput?.addEventListener('input', () => {
      const q = filterInput.value.toLowerCase();
      const wrap = this.bodyEl.querySelector<HTMLElement>('#ma-cmp-table-wrap');
      wrap?.querySelectorAll<HTMLTableRowElement>('tbody tr[data-symbol]').forEach(row => {
        const sym = (row.dataset['symbol'] ?? '').toLowerCase();
        const name = (row.querySelector('.ma-cmp-name')?.textContent ?? '').toLowerCase();
        row.style.display = !q || sym.includes(q) || name.includes(q) ? '' : 'none';
      });
    });

    this.bodyEl.querySelectorAll('tr[data-symbol]').forEach(row => {
      row.addEventListener('click', (e) => {
        const chartBtn = (e.target as HTMLElement).closest('.ma-cmp-chart-btn') as HTMLElement | null;
        if (chartBtn) {
          e.stopPropagation();
          this.openOnChart(chartBtn.dataset.chartSym!);
          return;
        }
        this.selectSymbol((row as HTMLElement).dataset.symbol!);
        this.switchTab('summary');
      });
    });
  }

  // ── Finansal tablolar (bilanço / gelir / nakit) ────────────────────────────

  private async loadStatement(endpoint: string, title: string): Promise<void> {
    const sym = this.currentSymbol;
    const seq = this._loadSeq;
    const tab = ({ 'balance-sheet': 'balance', 'income-stmt': 'income', 'cashflow': 'cashflow' } as Record<string, TabId>)[endpoint];
    try {
      let data = this.getCached<{ periods: string[]; rows: TableRow[] }>(tab);
      if (!data) {
        const resp = await fetch(`${API}/${sym}/${endpoint}?limit=12`);
        if (this._loadSeq !== seq) return;
        data = await resp.json() as { periods: string[]; rows: TableRow[] };
        if (this._loadSeq !== seq) return;
        this.setCache(tab, data);
      }
      if (this._loadSeq !== seq) return;

      const periods = data.periods || [];
      const rows = data.rows || [];

      if (!rows.length) {
        this.bodyEl.innerHTML = '<div class="ma-empty-block">Veri bulunamadı. Bu ekran BIST şirket finansalları içindir; destekli sembollerde "Yenile" ile kaynak tekrar kontrol edilir.</div>';
        return;
      }

      // Tekrarlayan "(Ara Toplam)" etiketlerini filtrele: sadece ilkini tut
      const seen = new Set<string>();
      const filtered = rows.filter(r => {
        const lbl = r.label.trim();
        if (lbl === '(Ara Toplam)' || lbl === '') {
          if (seen.has(lbl)) return false;
          seen.add(lbl);
        }
        return true;
      });

      const headerCells = periods.map(p => `<th>${p}</th>`).join('');
      const bodyRows = filtered.map(r => {
        const vals = periods.map(p => r.values[p] ?? null);
        const valueCells = vals.map((v, i) => {
          if (v === null) return '<td class="ma-num">—</td>';
          const prev = vals[i + 1] ?? null;
          return `<td class="ma-num">${fmtBig(v)}${deltaArrow(v, prev)}</td>`;
        }).join('');
        return `<tr><td class="ma-label">${r.label}</td>${valueCells}</tr>`;
      }).join('');

      this.bodyEl.innerHTML = `
        <div class="ma-table-header">
          <span class="ma-table-title">${title} — ${this.currentSymbol}</span>
          <span class="ma-table-source">Kaynak: borsapy / isyatirim.com</span>
        </div>
        <div class="ma-table-wrap">
          <table class="ma-table ma-financial-table">
            <thead><tr><th class="ma-sticky-col">Kalem</th>${headerCells}</tr></thead>
            <tbody>${bodyRows}</tbody>
          </table>
        </div>`;
    } catch (e) {
      if (this._loadSeq !== seq) return;
      this.bodyEl.innerHTML = `<div class="ma-error">Veri yüklenemedi: ${e}</div>`;
    }
  }

  // ── Oranlar ────────────────────────────────────────────────────────────────

  private async loadRatios(): Promise<void> {
    const sym = this.currentSymbol;
    const seq = this._loadSeq;
    try {
      let data = this.getCached<{ ratios: Record<string, unknown>[]; periods: string[] }>('ratios');
      if (!data) {
        const resp = await fetch(`${API}/${sym}/ratios?limit=8`);
        if (this._loadSeq !== seq) return;
        data = await resp.json() as { ratios: Record<string, unknown>[]; periods: string[] };
        if (this._loadSeq !== seq) return;
        this.setCache('ratios', data);
      }
      if (this._loadSeq !== seq) return;

      const ratios: RatioRow[] = (data.ratios || []).map(toRatioRow);
      const periods: string[] = data.periods || [];

      if (!ratios.length) {
        this.bodyEl.innerHTML = '<div class="ma-empty-block">Oran verisi yok. BIST şirketleri için "Yenile" ile hesaplama tekrar denenebilir; kapsam dışı sembollerde oran üretilmez.</div>';
        return;
      }

      const byKey: Record<string, Record<string, RatioRow>> = {};
      const allKeys: string[] = [];
      for (const r of ratios) {
        if (!byKey[r.key]) { byKey[r.key] = {}; allKeys.push(r.key); }
        byKey[r.key][r.period] = r;
      }
      const uniqueKeys = [...new Set(allKeys)];

      const catOrder = ['deger', 'karlilik', 'buyume', 'borc', 'nakit', 'likidite'];
      let html = `
        <div class="ma-table-header">
          <span class="ma-table-title">Finansal Oranlar — ${this.currentSymbol}</span>
          <span class="ma-table-source">Son ${periods.length} çeyrek · ▲/▼ dönemden döneme değişim</span>
        </div>
        <div class="ma-table-wrap">
          <table class="ma-table ma-ratio-table">
            <thead><tr><th class="ma-sticky-col">Oran</th>${periods.map(p => `<th>${p}</th>`).join('')}</tr></thead>
            <tbody>`;

      for (const cat of catOrder) {
        const keysInCat = uniqueKeys.filter(k => {
          const sample = byKey[k][periods[0]] ?? byKey[k][Object.keys(byKey[k])[0]];
          return sample?.category === cat;
        });
        if (!keysInCat.length) continue;
        html += `<tr class="ma-ratio-cat-row"><td colspan="${periods.length + 1}">${CATEGORY_LABEL[cat] || cat}</td></tr>`;
        for (const key of keysInCat) {
          const sample = byKey[key][periods[0]] ?? byKey[key][Object.keys(byKey[key])[0]];
          const cells = periods.map((p, i) => {
            const r = byKey[key]?.[p];
            if (!r) return '<td>—</td>';
            const cls = colorClass(r.value, r.unit, r.key);
            const prev = byKey[key]?.[periods[i + 1]];
            return `<td class="ma-num ${cls}">${fmt(r.value, r.unit)}${prev ? deltaArrow(r.value, prev.value) : ''}</td>`;
          }).join('');
          html += `<tr><td class="ma-ratio-name">${sample?.name || key}</td>${cells}</tr>`;
        }
      }
      html += '</tbody></table></div>';
      if (this._loadSeq !== seq) return;
      this.bodyEl.innerHTML = html;
    } catch (e) {
      if (this._loadSeq !== seq) return;
      this.bodyEl.innerHTML = `<div class="ma-error">Oranlar yüklenemedi: ${e}</div>`;
    }
  }

  // ── Grafikler ──────────────────────────────────────────────────────────────

  private async loadCharts(): Promise<void> {
    const sym = this.currentSymbol;
    const seq = this._loadSeq;
    try {
      let data = this.getCached<ChartDataResponse>('charts');
      if (!data) {
        const resp = await fetch(`${API}/${sym}/chart-data?limit=20`);
        if (this._loadSeq !== seq) return;
        data = await resp.json() as ChartDataResponse;
        if (this._loadSeq !== seq) return;
        this.setCache('charts', data);
      }
      if (this._loadSeq !== seq) return;

      const m = data.metrics || {};

      const CHART_DEFS: FinancialChartDef[] = [
        { key: 'revenue',         title: 'Ciro (Satış Gelirleri)',   unit: 'TRY', type: 'bar',  target: 'income'  },
        { key: 'net_income',      title: 'Net Kar',                  unit: 'TRY', type: 'bar',  target: 'income'  },
        { key: 'ebitda',          title: 'EBITDA',                   unit: 'TRY', type: 'bar',  target: 'income'  },
        { key: 'net_kar_marji',   title: 'Net Kar Marjı',            unit: '%',   type: 'line', target: 'income'  },
        { key: 'brut_kar_marji',  title: 'Brüt Kar Marjı',           unit: '%',   type: 'line', target: 'income'  },
        { key: 'ebitda_marji',    title: 'EBITDA Marjı',             unit: '%',   type: 'line', target: 'income'  },
        { key: 'roe',             title: 'ROE (Özkaynak Karlılığı)', unit: '%',   type: 'line', target: 'ratios'  },
        { key: 'roa',             title: 'ROA (Aktif Karlılık)',      unit: '%',   type: 'line', target: 'ratios'  },
        { key: 'ciro_buyume',     title: 'Ciro Büyümesi (YoY)',       unit: '%',   type: 'bar',  target: 'income'  },
        { key: 'net_kar_buyume',  title: 'Net Kar Büyümesi (YoY)',    unit: '%',   type: 'bar',  target: 'income'  },
        { key: 'net_borc_ebitda', title: 'Net Borç / EBITDA',         unit: 'x',   type: 'line', target: 'balance' },
        { key: 'borc_ozkaynak',   title: 'Borç / Özkaynak',          unit: 'x',   type: 'line', target: 'balance' },
        { key: 'cari_oran',       title: 'Cari Oran',                 unit: 'x',   type: 'line', target: 'balance' },
        { key: 'fcf_marji',       title: 'FCF Marjı',                 unit: '%',   type: 'line', target: 'cashflow' },
      ];

      const active = CHART_DEFS.filter(d => (m[d.key] || []).length > 0);

      if (!active.length) {
        this.bodyEl.innerHTML = '<div class="ma-empty-block">Grafik verisi yok — önce "Yenile" ile veri çekin.</div>';
        return;
      }

      this.bodyEl.innerHTML = `
        <div class="ma-chart-grid">
          ${active.map(d => `
            <div class="ma-chart-block${this._expandedCharts.has(d.key) ? ' is-expanded' : ''}" data-chart-key="${d.key}">
              <div class="ma-chart-head">
                <div class="ma-chart-title">${d.title}</div>
                <div class="ma-chart-actions">
                  <button class="ma-chart-action" data-chart-expand="${d.key}" title="${this._expandedCharts.has(d.key) ? 'Grafiği küçült' : 'Grafiği büyüt'}">${this._expandedCharts.has(d.key) ? '↙' : '↗'}</button>
                  <button class="ma-chart-action" data-chart-target="${d.target}" title="${this.targetLabel(d.target)} sekmesine git">${this.targetLabel(d.target)}</button>
                </div>
              </div>
              <div class="ma-chart-canvas" id="ma-chart-${d.key}" style="position:relative"></div>
            </div>`).join('')}
        </div>`;

      this.bindChartActions();

      const css = (v: string, fb: string) => getComputedStyle(document.documentElement).getPropertyValue(v).trim() || fb;
      const chartTheme = {
        layout: { background: { type: ColorType.Solid, color: css('--bg', '#12141f') }, textColor: css('--text', '#c4c9d6') },
        grid: { vertLines: { color: css('--border', '#1e2130') }, horzLines: { color: css('--border', '#1e2130') } },
        rightPriceScale: { borderColor: css('--border2', '#2a2d3e') },
        timeScale: { borderColor: css('--border2', '#2a2d3e'), timeVisible: false },
      };
      const bgColor = css('--bg', '#12141f');

      for (const def of active) {
        const el = this.bodyEl.querySelector(`#ma-chart-${def.key}`) as HTMLElement;
        if (!el) continue;

        const chart = createChart(el, {
          ...chartTheme,
          width: el.clientWidth || 340,
          height: this.chartHeightFor(def.key),
          handleScroll: false,
          handleScale: false,
        });
        this._charts.push(chart);
        this._chartByKey.set(def.key, chart);

        const points = (m[def.key] || [])
          .filter((p: ChartPoint) => p.value !== null && p.value !== undefined)
          .map((p: ChartPoint) => ({ time: p.time as unknown as UTCTimestamp, value: p.value }));

        if (def.type === 'bar') {
          const series = chart.addHistogramSeries({
            color: '#3a86ff',
            priceFormat: { type: 'custom', formatter: (v: number) => _fmtChartVal(v, def.unit) },
          }) as ISeriesApi<'Histogram'>;
          series.setData(points.map(p => ({
            time: p.time,
            value: p.value,
            color: p.value >= 0 ? '#26c97e' : '#ef4444',
          })));
        } else {
          const series = chart.addLineSeries({
            color: def.key.includes('borc') ? '#ef4444' : '#3a86ff',
            lineWidth: 2,
            lineStyle: LineStyle.Solid,
            priceFormat: { type: 'custom', formatter: (v: number) => _fmtChartVal(v, def.unit) },
          }) as ISeriesApi<'Line'>;
          series.setData(points);
        }

        chart.timeScale().fitContent();
        this.hideChartAttribution(el, bgColor);
      }

      this.observeChartResize();

      // ── Waterfall (Gelir Şelale) ─────────────────────────────────────────────
      this.renderWaterfall(m);

    } catch (e) {
      if (this._loadSeq !== seq) return;
      this.bodyEl.innerHTML = `<div class="ma-error">Grafikler yüklenemedi: ${e}</div>`;
    }
  }

  private bindChartActions(): void {
    this.bodyEl.querySelectorAll<HTMLButtonElement>('[data-chart-expand]').forEach(btn => {
      btn.addEventListener('click', () => {
        const key = btn.dataset.chartExpand;
        if (!key) return;
        if (this._expandedCharts.has(key)) this._expandedCharts.delete(key);
        else this._expandedCharts.add(key);
        this.loadCharts();
      });
    });

    this.bodyEl.querySelectorAll<HTMLButtonElement>('[data-chart-target]').forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.dataset.chartTarget as FinancialChartTarget | undefined;
        if (tab) this.switchTab(tab);
      });
    });
  }

  private chartHeightFor(key: string): number {
    return this._expandedCharts.has(key) ? 340 : 220;
  }

  private targetLabel(target: FinancialChartTarget): string {
    return ({ balance: 'Bilanço', income: 'Gelir', cashflow: 'Nakit', ratios: 'Oranlar' })[target];
  }

  private observeChartResize(): void {
    this._chartResizeObserver?.disconnect();
    this._chartResizeObserver = new ResizeObserver(entries => {
      for (const entry of entries) {
        const el = entry.target as HTMLElement;
        const key = el.id.replace('ma-chart-', '');
        const chart = this._chartByKey.get(key);
        if (!chart) continue;
        chart.resize(Math.max(260, Math.floor(entry.contentRect.width)), this.chartHeightFor(key));
        chart.timeScale().fitContent();
      }
    });

    this.bodyEl.querySelectorAll<HTMLElement>('.ma-chart-canvas').forEach(el => {
      this._chartResizeObserver?.observe(el);
    });
  }

  private hideChartAttribution(el: HTMLElement, bgColor: string): void {
    const hide = () => {
      el.querySelectorAll<HTMLElement>(
        'a[href*="tradingview"], a[href*="lightweight-charts"], [aria-label*="TradingView"], a[class*="tv-"], div[class*="logo"], span[class*="logo"]'
      ).forEach(node => {
        node.style.display = 'none';
        node.style.pointerEvents = 'none';
      });
    };
    hide();
    requestAnimationFrame(hide);

    const mask = document.createElement('div');
    mask.className = 'ma-chart-attribution-mask';
    mask.style.background = bgColor;
    el.appendChild(mask);
  }

  private renderWaterfall(m: Record<string, ChartPoint[]>): void {
    const revenue = m['revenue'] ?? [];
    const netIncome = m['net_income'] ?? [];
    const brutMarji = m['brut_kar_marji'] ?? [];
    const ebitdaMarji = m['ebitda_marji'] ?? [];

    // Align periods — use revenue periods as reference
    const revByPeriod: Record<string, number> = {};
    revenue.forEach(p => { revByPeriod[p.period] = p.value; });
    const niByPeriod: Record<string, number> = {};
    netIncome.forEach(p => { niByPeriod[p.period] = p.value; });
    const bmByPeriod: Record<string, number> = {};
    brutMarji.forEach(p => { bmByPeriod[p.period] = p.value; });
    const emByPeriod: Record<string, number> = {};
    ebitdaMarji.forEach(p => { emByPeriod[p.period] = p.value; });

    const periods = Object.keys(revByPeriod).sort().slice(-4);
    if (periods.length < 2) return;

    const labels = periods;
    const revVals  = periods.map(p => revByPeriod[p] ?? 0);
    const gpVals   = periods.map(p => revByPeriod[p] != null && bmByPeriod[p] != null ? revByPeriod[p] * bmByPeriod[p] / 100 : 0);
    const ebitdaVals = periods.map(p => revByPeriod[p] != null && emByPeriod[p] != null ? revByPeriod[p] * emByPeriod[p] / 100 : 0);
    const niVals   = periods.map(p => niByPeriod[p] ?? 0);

    const wfSection = document.createElement('div');
    wfSection.className = `ma-chart-block ma-chart-block-wide${this._expandedCharts.has('waterfall') ? ' is-expanded' : ''}`;
    wfSection.innerHTML = `
      <div class="ma-chart-head">
        <div class="ma-chart-title">Gelir Şelalesi — Son ${periods.length} Dönem</div>
        <div class="ma-chart-actions">
          <button class="ma-chart-action" id="ma-waterfall-expand" title="${this._expandedCharts.has('waterfall') ? 'Grafiği küçült' : 'Grafiği büyüt'}">${this._expandedCharts.has('waterfall') ? '↙' : '↗'}</button>
          <button class="ma-chart-action" id="ma-waterfall-income" title="Gelir tablosu sekmesine git">Gelir</button>
        </div>
      </div>
      <div class="ma-waterfall-canvas-wrap"><canvas id="ma-waterfall-canvas"></canvas></div>`;
    this.bodyEl.appendChild(wfSection);
    wfSection.querySelector<HTMLButtonElement>('#ma-waterfall-expand')?.addEventListener('click', () => {
      if (this._expandedCharts.has('waterfall')) this._expandedCharts.delete('waterfall');
      else this._expandedCharts.add('waterfall');
      this.loadCharts();
    });
    wfSection.querySelector<HTMLButtonElement>('#ma-waterfall-income')?.addEventListener('click', () => this.switchTab('income'));

    const canvas = wfSection.querySelector<HTMLCanvasElement>('#ma-waterfall-canvas')!;
    const wfCss = (v: string, fb: string) => getComputedStyle(document.documentElement).getPropertyValue(v).trim() || fb;
    const tickColor = wfCss('--text', '#8b949e');
    const gridColor = wfCss('--border', '#21262d');
    this._waterfallChart?.destroy();
    this._waterfallChart = new Chart(canvas, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label: 'Ciro',     data: revVals,   backgroundColor: '#3a86ff88' },
          { label: 'Brüt Kar', data: gpVals,    backgroundColor: '#26c97e88' },
          { label: 'EBITDA',   data: ebitdaVals, backgroundColor: '#ffb02088' },
          { label: 'Net Kar',  data: niVals,    backgroundColor: niVals.map(v => v >= 0 ? '#26c97e' : '#ef4444') },
        ],
      },
      options: {
        animation: false,
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { color: tickColor, boxWidth: 10, font: { size: 11 } } },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const v = ctx.raw as number;
                return ` ${ctx.dataset.label}: ${fmtBig(v)}`;
              },
            },
          },
        },
        scales: {
          x: { ticks: { color: tickColor, font: { size: 10 } }, grid: { color: gridColor } },
          y: {
            ticks: { color: tickColor, font: { size: 10 }, callback: (v) => fmtBig(Number(v)) },
            grid: { color: gridColor },
          },
        },
      },
    });
  }

  // ── Olaylar (Events) sekmesi ────────────────────────────────────────────────

  private async loadEvents(): Promise<void> {
    const sym = this.currentSymbol;
    const seq = this._loadSeq;
    try {
      let data = this.getCached<{ events: Record<string, unknown>[]; source: string }>('events');
      if (!data) {
        const resp = await fetch(`${API}/${sym}/events`);
        if (this._loadSeq !== seq) return;
        data = await resp.json() as { events: Record<string, unknown>[]; source: string };
        if (this._loadSeq !== seq) return;
        this.setCache('events', data);
      }
      if (this._loadSeq !== seq) return;
      const events = data.events || [];
      if (!events.length) {
        this.bodyEl.innerHTML = '<div class="ma-empty-block">Olay/uyarı kaydı bulunamadı. "Yenile" ile veri çekin.</div>';
        return;
      }
      const unreadIds = events.filter(e => !e.is_read).map(e => Number(e.id)).filter(Boolean);
      const markBtn = unreadIds.length
        ? `<button class="btn-sm btn-ghost ma-events-mark-all" data-ids='${JSON.stringify(unreadIds)}'>Tümünü okundu işaretle (${unreadIds.length})</button>`
        : '';
      const rows = events.map(e => {
        const id = Number(e.id) || 0;
        const title = String(e.title || e.alert_type || '');
        const body = String(e.body || e.description || '');
        const period = String(e.period || '');
        const severity = String(e.severity || 'info');
        const badge = SEVERITY_BADGE[severity] || 'badge-info';
        const date = String(e.created_at || e.published_at || '');
        const dateStr = date ? new Date(date).toLocaleDateString('tr-TR') : '';
        const isRead = e.is_read ? ' ma-event-read' : '';
        return `<div class="ma-event-row${isRead}" data-event-id="${id}">
          <div class="ma-event-header">
            <span class="badge ${badge}">${this.escHtml(severity.toUpperCase())}</span>
            <span class="ma-event-title">${this.escHtml(title)}</span>
            ${period ? `<span class="ma-event-period">${this.escHtml(period)}</span>` : ''}
            ${dateStr ? `<span class="ma-event-date">${dateStr}</span>` : ''}
          </div>
          ${body ? `<div class="ma-event-body">${this.escHtml(body)}</div>` : ''}
        </div>`;
      }).join('');
      if (this._loadSeq !== seq) return;
      this.bodyEl.innerHTML = `
        <div class="ma-events-header">${markBtn}</div>
        <div class="ma-events-list">${rows}</div>`;
      if (markBtn) {
        this.bodyEl.querySelector<HTMLButtonElement>('.ma-events-mark-all')?.addEventListener('click', (btn) => {
          const ids = JSON.parse((btn.currentTarget as HTMLElement).dataset.ids || '[]') as number[];
          this.markRead(ids);
        });
      }
    } catch (e) {
      if (this._loadSeq !== seq) return;
      this.bodyEl.innerHTML = `<div class="ma-error">Veri yüklenemedi: ${e}</div>`;
    }
  }

  // ── KAP Raporlar sekmesi ────────────────────────────────────────────────────

  private async loadMaliReports(): Promise<void> {
    const sym = this.currentSymbol;
    const seq = this._loadSeq;
    try {
      let data = this.getCached<{ reports: Record<string, unknown>[]; source: string }>('reports');
      if (!data) {
        const resp = await fetch(`${API}/${sym}/reports`);
        if (this._loadSeq !== seq) return;
        data = await resp.json() as { reports: Record<string, unknown>[]; source: string };
        if (this._loadSeq !== seq) return;
        this.setCache('reports', data);
      }
      if (this._loadSeq !== seq) return;
      const reports = data.reports || [];
      if (!reports.length) {
        this.bodyEl.innerHTML = '<div class="ma-empty-block">KAP raporu bulunamadı.</div>';
        return;
      }
      const rows = reports.map(r => {
        const title = String(r.title || r.headline || '');
        const url = String(r.url || r.link || '');
        const period = String(r.period || '');
        const date = String(r.published_at || r.date || '');
        const metaStr = date ? new Date(date).toLocaleDateString('tr-TR') : period;
        const src = String(r.source || '');
        const linkHtml = url
          ? `<a class="ma-report-link" href="${this.escAttr(url)}" target="_blank" rel="noopener">Görüntüle ↗</a>`
          : '';
        return `<div class="ma-report-row">
          <div class="ma-report-meta">
            ${metaStr ? `<span class="ma-event-period">${this.escHtml(metaStr)}</span>` : ''}
            ${src ? `<span class="ma-event-date">${this.escHtml(src)}</span>` : ''}
          </div>
          <div class="ma-report-title">${this.escHtml(title)}</div>
          ${linkHtml}
        </div>`;
      }).join('');
      if (this._loadSeq !== seq) return;
      this.bodyEl.innerHTML = `<div class="ma-reports-list">${rows}</div>`;
    } catch (e) {
      if (this._loadSeq !== seq) return;
      this.bodyEl.innerHTML = `<div class="ma-error">Veri yüklenemedi: ${e}</div>`;
    }
  }

  private escHtml(s: string): string {
    return s.replace(/[&<>"']/g, c =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] ?? c);
  }

  private escAttr(s: string): string {
    return s.replace(/[&"]/g, c => ({ '&': '&amp;', '"': '&quot;' })[c] ?? c);
  }

  // ── Refresh ─────────────────────────────────────────────────────────────────

  private async refreshSymbol(): Promise<void> {
    if (this.refreshing) return;
    this.refreshing = true;
    this.refreshBtnEl.disabled = true;
    this.refreshBtnEl.innerHTML = `${ICON_REFRESH} İndiriliyor...`;
    this.invalidateSymbol(this.currentSymbol);
    await this.doRefreshSymbol(this.currentSymbol, true);
    this.refreshing = false;
    this.refreshBtnEl.disabled = false;
    this.refreshBtnEl.innerHTML = `${ICON_REFRESH} Yenile`;
  }

  private async doRefreshSymbol(symbol: string, updateBadge: boolean): Promise<void> {
    if (updateBadge) {
      this.statusBadgeEl.className = 'ma-status-badge badge-info';
      this.statusBadgeEl.textContent = 'Güncelleniyor…';
    }
    try {
      const resp = await fetch(`${API}/${symbol}/refresh`, { method: 'POST' });
      const data = await resp.json();
      if (updateBadge) {
        if (data.status === 'ok') {
          this.statusBadgeEl.className = 'ma-status-badge badge-success';
          this.statusBadgeEl.textContent = '✓ Güncellendi';
        } else {
          this.statusBadgeEl.className = 'ma-status-badge badge-warning';
          const errText = typeof data.status === 'string' && data.status.startsWith('error')
            ? 'Veri çekilemedi — Yenile ile tekrar dene'
            : (data.status || 'Hata');
          this.statusBadgeEl.textContent = '⚠ ' + errText;
        }
        await this.loadUniverse();
        this.loadTab();
      }
    } catch {
      if (updateBadge) this.statusBadgeEl.textContent = '✗ Hata';
    }
  }

  private _toast(msg: string, type: 'success' | 'error' | 'info' = 'info'): void {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      document.body.appendChild(container);
    }
    const t = document.createElement('div');
    t.className = `toast toast-${type}`;
    t.textContent = msg;
    container.appendChild(t);
    setTimeout(() => t.remove(), 4000);
  }

  private async refreshAll(): Promise<void> {
    if (this.refreshing) return;
    // Tema uyumlu onay — dialog kullan
    const confirmed = await new Promise<boolean>(resolve => {
      let dlg = document.getElementById('mali-confirm-dialog') as HTMLDialogElement | null;
      if (!dlg) {
        dlg = document.createElement('dialog');
        dlg.id = 'mali-confirm-dialog';
        dlg.innerHTML = `
          <div class="confirm-dialog-body">
            <p class="confirm-msg"></p>
            <div class="confirm-actions">
              <button class="btn-sm btn-secondary confirm-cancel">Vazgeç</button>
              <button class="btn-sm btn-primary confirm-ok">Başlat</button>
            </div>
          </div>`;
        document.body.appendChild(dlg);
        dlg.querySelector('.confirm-cancel')?.addEventListener('click', () => { dlg!.close(); resolve(false); });
      }
      (dlg.querySelector('.confirm-msg') as HTMLElement).textContent =
        'Tüm BIST 30 bilançoları güncelleniyor (~5-10 dk). Başlatılsın mı?';
      const okBtn = dlg.querySelector('.confirm-ok') as HTMLElement;
      const newOk = okBtn.cloneNode(true) as HTMLElement;
      okBtn.parentNode!.replaceChild(newOk, okBtn);
      newOk.addEventListener('click', () => { dlg!.close(); resolve(true); }, { once: true });
      dlg.showModal();
    });
    if (!confirmed) return;

    this.refreshing = true;
    this.refreshAllBtnEl.disabled = true;

    // Progress göstergesi
    let progress = 0;
    const progressInterval = setInterval(() => {
      progress = Math.min(progress + 3, 90);
      this.refreshAllBtnEl.innerHTML = `${ICON_REFRESH} BIST 30 %${progress}`;
    }, 2000);

    try {
      const resp = await fetch(`${API}/refresh`, { method: 'POST' });
      const data = await resp.json();
      this._cache.clear();
      this._toast(`BIST 30 güncellendi: ${data.ok}/${data.triggered} başarılı.`, 'success');
      await this.loadUniverse();
      this.loadTab();
    } catch {
      this._toast('Güncelleme başarısız.', 'error');
    } finally {
      clearInterval(progressInterval);
      this.refreshing = false;
      this.refreshAllBtnEl.disabled = false;
      this.refreshAllBtnEl.innerHTML = `${ICON_REFRESH} BIST 30`;
    }
  }

  private async markRead(ids: number[]): Promise<void> {
    if (!ids.length) return;
    await fetch(`${API}/alerts/mark-read`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids }),
    });
    this.invalidateSymbol(this.currentSymbol);
    this.setCache('comparison', null);
    this.loadTab();
  }

  private updateStatusBadge(status: FetchStatus | undefined): void {
    if (!status) return;
    const el = this.statusBadgeEl;
    if (status.status === 'ok') {
      el.className = 'ma-status-badge badge-success';
      el.textContent = `✓ ${status.last_period || ''} · ${status.periods_fetched || 0} dönem`;
    } else if (status.status === 'no_data') {
      el.className = 'ma-status-badge badge-warning';
      el.textContent = '○ Veri yok — Yenile';
    } else if (status.status === 'error' || (typeof status.status === 'string' && status.status.startsWith('error'))) {
      el.className = 'ma-status-badge badge-danger';
      el.textContent = '✗ Veri çekilemedi — Yenile';
    } else {
      el.className = 'ma-status-badge badge-info';
      el.textContent = status.last_period || status.status;
    }
  }
}

function _fmtChartVal(v: number, unit: string): string {
  if (unit === '%') return `${v.toFixed(1)}%`;
  if (unit === 'x')  return `${v.toFixed(2)}x`;
  const abs = Math.abs(v);
  const sign = v < 0 ? '-' : '';
  if (abs >= 1e9)  return `${sign}${(abs / 1e9).toFixed(1)}Mr`;
  if (abs >= 1e6)  return `${sign}${(abs / 1e6).toFixed(0)}Mn`;
  return `${sign}${abs.toFixed(0)}`;
}
