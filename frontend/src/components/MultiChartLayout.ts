import type { OHLCV, SymbolInfo, Timeframe, Signal, ChartDataRenderReason } from '../types.js';
import { ChartPanel } from './ChartPanel.js';
import { loadHistorical } from '../core/HistoricalLoader.js';
import { QuoteStream, type QuoteMessage } from '../core/QuoteStream.js';
import { ALL_SYMBOLS, DEFAULT_SYMBOL } from '../constants/symbols.js';
import { TR } from '../constants/tr.js';

// ─── Layout Presets ────────────────────────────────────────────────────────────

export type LayoutMode = '1x1' | '1x2' | '2x1' | '2x2';

interface LayoutConfig {
  cols: number;
  rows: number;
  label: string;
  icon: string;
}

const LAYOUTS: Record<LayoutMode, LayoutConfig> = {
  '1x1': { cols: 1, rows: 1, label: 'Tek',   icon: '⬜' },
  '1x2': { cols: 2, rows: 1, label: '1×2',   icon: '⬜⬜' },
  '2x1': { cols: 1, rows: 2, label: '2×1',   icon: '⏹' },
  '2x2': { cols: 2, rows: 2, label: '2×2',   icon: '⊞' },
};



// ─── ChartPane — her pencere kendi verisini yönetir ──────────────────────────

interface ChartPaneState {
  id: number;
  symbol: SymbolInfo;
  timeframe: Timeframe;
  candles: OHLCV[];
  chartPanel: ChartPanel;
  containerEl: HTMLElement;
  quoteStream: QuoteStream | null;
  quoteUnsub: (() => void) | null;
  loading: boolean;
  loadVersion: number;
}

// ─── MultiChartLayout ─────────────────────────────────────────────────────────

type SymbolChangeListener = (paneId: number, info: SymbolInfo) => void;
type ActivePaneListener = (paneId: number) => void;

export class MultiChartLayout {
  private container: HTMLElement;
  private gridEl!: HTMLElement;
  private controlsEl!: HTMLElement;
  private panes: ChartPaneState[] = [];
  private layout: LayoutMode = '1x1';
  private nextPaneId = 1;
  private activePaneId = 1;

  private symbolChangeListeners = new Set<SymbolChangeListener>();
  private activePaneListeners = new Set<ActivePaneListener>();

  constructor(container: HTMLElement) {
    this.container = container;
    this.buildDOM();
    this.addPane(DEFAULT_SYMBOL);
    this.updateGrid();
  }

  // ─── Public API ───────────────────────────────────────────────────────

  getActivePane(): ChartPaneState | undefined {
    return this.panes.find(p => p.id === this.activePaneId);
  }

  getActivePaneChart(): ChartPanel | undefined {
    return this.getActivePane()?.chartPanel;
  }

  setLayout(mode: LayoutMode): void {
    if (mode === this.layout) return;
    this.layout = mode;

    const cfg = LAYOUTS[mode];
    const targetCount = cfg.cols * cfg.rows;

    // Pencere sayısını layout'a uyarla
    while (this.panes.length < targetCount) {
      this.addPane(this.pickNextSymbol());
    }
    while (this.panes.length > targetCount) {
      this.removeLastPane();
    }

    this.updateControlsActive();
    this.updateGrid();
    
    // Resize delay'ini kısa tutarak canvas'ların doğru çizilmesini sağla
    setTimeout(() => {
      this.panes.forEach(p => p.chartPanel.resizeCharts());
    }, 50);
  }

  getLayout(): LayoutMode {
    return this.layout;
  }

  /** Aktif pane'e sinyal marker'ları ayarla */
  setSignals(signals: Signal[]): void {
    this.getActivePane()?.chartPanel.setSignals(signals);
  }

  clearSignals(): void {
    this.panes.forEach(p => p.chartPanel.clearSignals());
  }

  focusActivePaneTime(timestamp: number): void {
    this.getActivePane()?.chartPanel.focusTime(timestamp);
  }

  setActivePaneIndicator(indicator: string, active = true): void {
    this.getActivePane()?.chartPanel.setIndicatorActive(indicator, active);
  }

  onSymbolChange(listener: SymbolChangeListener): () => void {
    this.symbolChangeListeners.add(listener);
    return () => this.symbolChangeListeners.delete(listener);
  }

  onActivePaneChange(listener: ActivePaneListener): () => void {
    this.activePaneListeners.add(listener);
    return () => this.activePaneListeners.delete(listener);
  }

  /** Dışarıdan aktif pane'in sembolünü değiştir (sidebar'dan seçim gibi) */
  async setActivePaneSymbol(info: SymbolInfo): Promise<void> {
    const pane = this.getActivePane();
    if (!pane) return;
    await this.setPaneSymbol(pane, info);
  }

  /** Aktif pane'in timeframe'ini değiştir */
  setActivePaneTimeframe(tf: Timeframe): void {
    const pane = this.getActivePane();
    if (!pane || pane.timeframe === tf) return;
    pane.timeframe = tf;
    void this.loadPaneData(pane, 'timeframe', true);
  }

  /** Aktif pane'in mum verisini al (strateji paneli beslemek için) */
  getActivePaneCandles(): OHLCV[] {
    return this.getActivePane()?.candles ?? [];
  }

  getActivePaneSymbol(): SymbolInfo {
    return this.getActivePane()?.symbol ?? DEFAULT_SYMBOL;
  }

  getActivePaneTimeframe(): Timeframe {
    return this.getActivePane()?.timeframe ?? '1d';
  }

  // ─── DOM ──────────────────────────────────────────────────────────────

  private buildDOM(): void {
    this.container.innerHTML = '';
    this.container.style.cssText = 'display:flex;flex-direction:column;height:100%;';

    // Layout kontrol çubuğu
    this.controlsEl = document.createElement('div');
    this.controlsEl.className = 'multi-chart-controls';
    this.controlsEl.innerHTML = this.layoutControlsHTML();
    this.container.appendChild(this.controlsEl);

    // Grid container
    this.gridEl = document.createElement('div');
    this.gridEl.className = 'multi-chart-grid';
    this.container.appendChild(this.gridEl);

    this.bindLayoutControls();
  }

  private syncLocks: Record<string, boolean> = {
    symbol: true,
    timeframe: true,
    range: true,
    scale: false,
  };

  private layoutControlsHTML(): string {
    const locks = [
      { key: 'symbol',    label: TR.SYNC_SYMBOL,    icon: '🔗' },
      { key: 'timeframe', label: TR.SYNC_TIMEFRAME, icon: '⏳' },
      { key: 'range',     label: TR.SYNC_RANGE,     icon: '↔️' },
      { key: 'scale',     label: TR.SYNC_SCALE,     icon: '📏' },
    ];

    return `
      <div class="mcl-group">
        <span class="mcl-label">Düzen</span>
        ${Object.entries(LAYOUTS).map(([mode, cfg]) =>
          `<button class="ctrl-btn mcl-btn${mode === this.layout ? ' active' : ''}" data-layout="${mode}" title="${cfg.label}">${cfg.icon}</button>`
        ).join('')}
      </div>
      <div class="mcl-group">
        <span class="mcl-label">${TR.SYNC_LOCKS}</span>
        ${locks.map(l => `
          <button class="sync-lock-btn${this.syncLocks?.[l.key] ? ' active' : ''}" data-lock="${l.key}" title="${l.label}">
            <span class="lock-icon">${l.icon}</span> ${l.label}
          </button>
        `).join('')}
      </div>
    `;
  }

  private bindLayoutControls(): void {
    this.controlsEl.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      
      const layoutBtn = target.closest<HTMLElement>('[data-layout]');
      if (layoutBtn) {
        const mode = layoutBtn.dataset['layout'] as LayoutMode;
        this.setLayout(mode);
        return;
      }

      const lockBtn = target.closest<HTMLElement>('[data-lock]');
      if (lockBtn) {
        const key = lockBtn.dataset['lock']!;
        this.syncLocks[key] = !this.syncLocks[key];
        lockBtn.classList.toggle('active', this.syncLocks[key]);
        this.applyAllSyncs();
      }
    });
  }

  private applyAllSyncs(): void {
    if (this.panes.length < 2) return;
    const active = this.getActivePane();
    if (!active) return;

    if (this.syncLocks['symbol']) {
      this.panes.forEach(p => {
        if (p.id !== active.id && p.symbol.symbol !== active.symbol.symbol) {
          void this.setPaneSymbol(p, active.symbol);
        }
      });
    }

    if (this.syncLocks['timeframe']) {
      this.panes.forEach(p => {
        if (p.id !== active.id && p.timeframe !== active.timeframe) {
          p.timeframe = active.timeframe;
          void this.loadPaneData(p, 'timeframe', true);
        }
      });
    }

    if (this.syncLocks['range']) {
      const range = active.chartPanel.getVisibleLogicalRange();
      if (range) {
        this.panes.forEach(p => {
          if (p.id !== active.id) p.chartPanel.setVisibleLogicalRange(range);
        });
      }
    }
  }

  private updateControlsActive(): void {
    this.controlsEl.querySelectorAll('.mcl-btn').forEach(btn => {
      const el = btn as HTMLElement;
      el.classList.toggle('active', el.dataset['layout'] === this.layout);
    });
  }

  // ─── Grid yönetimi ────────────────────────────────────────────────────

  private updateGrid(): void {
    const cfg = LAYOUTS[this.layout];
    this.gridEl.style.cssText = `
      display: grid;
      grid-template-columns: repeat(${cfg.cols}, 1fr);
      grid-template-rows: repeat(${cfg.rows}, 1fr);
      gap: 2px;
      flex: 1;
      overflow: hidden;
      background: var(--border);
    `;

    // DOM'u sıfırla ve pane container'ları ekle
    this.gridEl.innerHTML = '';
    for (const pane of this.panes) {
      this.gridEl.appendChild(pane.containerEl);
    }
    // Resize'ı tetikle
    setTimeout(() => {
      this.panes.forEach(p => p.chartPanel.resizeCharts());
    }, 50);
  }

  // ─── Pane yönetimi ────────────────────────────────────────────────────

  private addPane(symbol: SymbolInfo): ChartPaneState {
    const id = this.nextPaneId++;

    // Pane wrapper
    const containerEl = document.createElement('div');
    containerEl.className = 'chart-pane';
    containerEl.dataset['paneId'] = String(id);

    // Header — sembol seçici + badge
    const headerEl = document.createElement('div');
    headerEl.className = 'chart-pane-header';
    headerEl.innerHTML = this.paneHeaderHTML(id, symbol);
    containerEl.appendChild(headerEl);

    // Chart container
    const chartContainer = document.createElement('div');
    chartContainer.className = 'chart-pane-body';
    containerEl.appendChild(chartContainer);

    const chartPanel = new ChartPanel(chartContainer);

    const pane: ChartPaneState = {
      id,
      symbol,
      timeframe: '1d',
      candles: [],
      chartPanel,
      containerEl,
      quoteStream: null,
      quoteUnsub: null,
      loading: false,
      loadVersion: 0,
    };

    this.panes.push(pane);

    // Sync: Range change
    chartPanel.onVisibleLogicalRangeChange((range) => {
      if (!range || !this.syncLocks['range'] || this.activePaneId !== id) return;
      this.panes.forEach(p => {
        if (p.id !== id) p.chartPanel.setVisibleLogicalRange(range);
      });
    });

    // Crosshair move sync removed due to lightweight-charts limitations.

    // Sync: Scale Mode change
    containerEl.addEventListener('scaleModeChange', (e: Event) => {
      const customEvent = e as CustomEvent<any>;
      const mode = customEvent.detail;
      if (!this.syncLocks['scale'] || this.activePaneId !== id) return;
      this.panes.forEach(p => {
        if (p.id !== id) p.chartPanel.setScaleMode(mode);
      });
    });

    // Pane'e tıklayınca aktif yap
    containerEl.addEventListener('click', (e) => {
      // Don't activate if clicking a select or button inside header
      if ((e.target as HTMLElement).closest('.pane-symbol-select')) return;
      this.setActivePane(id);
    });

    // Sembol seçici
    this.bindPaneHeader(pane, headerEl);

    // G6: Compare logic
    containerEl.addEventListener('compareRequest', (e: Event) => {
      const customEvent = e as CustomEvent<string>;
      const compareSymbolStr = customEvent.detail;
      void this.loadCompareData(pane, compareSymbolStr);
    });

    // Veri yükle
    void this.loadPaneData(pane, 'initial');

    // İlk pane ise aktif yap
    if (this.panes.length === 1) {
      this.setActivePane(id);
    }

    return pane;
  }

  private removeLastPane(): void {
    const pane = this.panes.pop();
    if (!pane) return;
    this.disconnectPane(pane);
    pane.chartPanel.destroy();
    pane.containerEl.remove();

    // Aktif pane silindiyse ilkini aktif yap
    if (pane.id === this.activePaneId && this.panes.length > 0) {
      this.setActivePane(this.panes[0]!.id);
    }
  }

  private setActivePane(id: number): void {
    if (this.activePaneId === id) return;
    this.activePaneId = id;

    this.panes.forEach(p => {
      p.containerEl.classList.toggle('active-pane', p.id === id);
    });

    this.activePaneListeners.forEach(l => l(id));
  }

  // ─── Pane header ──────────────────────────────────────────────────────

  private paneHeaderHTML(id: number, symbol: SymbolInfo): string {
    const groups = this.groupSymbols();
    return `
      <select class="pane-symbol-select" data-pane-id="${id}" title="Sembol seç">
        ${groups.map(([group, symbols]) => `
          <optgroup label="${group}">
            ${symbols.map(s =>
              `<option value="${s.symbol}"${s.symbol === symbol.symbol ? ' selected' : ''}>${s.symbol.replace('.IS', '')} — ${s.name}</option>`
            ).join('')}
          </optgroup>
        `).join('')}
      </select>
      <span class="pane-symbol-name">${symbol.name}</span>
      <span class="pane-badge" id="pane-badge-${id}"></span>
    `;
  }

  private groupSymbols(): [string, SymbolInfo[]][] {
    const groups = new Map<string, SymbolInfo[]>();
    for (const s of ALL_SYMBOLS) {
      if (!groups.has(s.group)) groups.set(s.group, []);
      groups.get(s.group)!.push(s);
    }
    return Array.from(groups.entries());
  }

  private bindPaneHeader(pane: ChartPaneState, headerEl: HTMLElement): void {
    const select = headerEl.querySelector<HTMLSelectElement>('.pane-symbol-select');
    if (!select) return;

    select.addEventListener('change', () => {
      const sym = ALL_SYMBOLS.find(s => s.symbol === select.value);
      if (sym) void this.setPaneSymbol(pane, sym);
    });
  }

  // ─── Veri yükleme ─────────────────────────────────────────────────────

  private async setPaneSymbol(pane: ChartPaneState, info: SymbolInfo): Promise<void> {
    pane.symbol = info;
    pane.candles = [];
    pane.chartPanel.clearSignals();

    // Header güncelle
    const nameEl = pane.containerEl.querySelector('.pane-symbol-name');
    if (nameEl) nameEl.textContent = info.name;

    const selectEl = pane.containerEl.querySelector<HTMLSelectElement>('.pane-symbol-select');
    if (selectEl) selectEl.value = info.symbol;

    this.symbolChangeListeners.forEach(l => l(pane.id, info));

    // Sync Symbol
    if (this.syncLocks['symbol'] && pane.id === this.activePaneId) {
      this.panes.forEach(p => {
        if (p.id !== pane.id && p.symbol.symbol !== info.symbol) {
          void this.setPaneSymbol(p, info);
        }
      });
    }

    await this.loadPaneData(pane, 'symbol', false, true);
  }

  private async loadPaneData(
    pane: ChartPaneState,
    reason: ChartDataRenderReason = 'initial',
    preserveTimeRange = false,
    force = false,
  ): Promise<void> {
    if (pane.loading && !force) return;
    const loadVersion = ++pane.loadVersion;

    // Sync Timeframe
    if (this.syncLocks['timeframe'] && pane.id === this.activePaneId && reason === 'timeframe') {
      this.panes.forEach(p => {
        if (p.id !== pane.id && p.timeframe !== pane.timeframe) {
          p.timeframe = pane.timeframe;
          void this.loadPaneData(p, 'timeframe', true);
        }
      });
    }

    pane.loading = true;

    // Eski bağlantıyı kes
    this.disconnectPane(pane);

    const symbol = pane.symbol.symbol;
    const timeframe = pane.timeframe;
    pane.chartPanel.setData([], {
      status: 'loading',
      reason,
      symbol,
      currency: pane.symbol.currency,
      timeframe,
      message: TR.LOADING,
    });

    const badgeEl = pane.containerEl.querySelector<HTMLElement>(`#pane-badge-${pane.id}`);
    if (badgeEl) {
      badgeEl.textContent = TR.CONNECTING;
      badgeEl.className = 'pane-badge status-connecting';
    }

    try {
      // 1) Tarihsel veri
      const candles = await loadHistorical(symbol, timeframe, {
        assetType: pane.symbol.assetType,
      });
      if (pane.loadVersion !== loadVersion || pane.symbol.symbol !== symbol || pane.timeframe !== timeframe) return;

      pane.candles = candles;
      pane.chartPanel.setData(candles, {
        status: 'ready',
        reason,
        symbol,
        currency: pane.symbol.currency,
        timeframe,
        preserveTimeRange,
      });

      // G9: Load sample events for the symbol
      pane.chartPanel.loadSampleEvents(symbol);

      if (badgeEl) {
        badgeEl.textContent = TR.DELAYED;
        badgeEl.className = 'pane-badge status-delayed';
      }

      // 2) Canlı akış (kripto için WS)
      if (pane.symbol.assetType === 'crypto') {
        this.connectPaneWS(pane);
      } else {
        // Non-crypto: sadece tarihsel veri; canlı güncelleme polling path üzerinden
        // yapılır (ana DataEngine'den); per-pane polling yapmıyoruz.
        if (badgeEl) {
          badgeEl.textContent = candles.length > 0 ? TR.DELAYED : TR.OFFLINE;
          badgeEl.className = candles.length > 0 ? 'pane-badge status-delayed' : 'pane-badge status-offline';
        }
      }
    } catch (err) {
      if (pane.loadVersion !== loadVersion) return;
      const message = err instanceof Error ? err.message : TR.CONNECTION_ERROR;
      const status = message.includes('Empty OHLCV') ? 'empty' : 'error';
      pane.candles = [];
      pane.chartPanel.setData([], {
        status,
        reason,
        symbol,
        currency: pane.symbol.currency,
        timeframe,
        message: status === 'empty' ? TR.NO_DATA : message,
      });
      if (badgeEl) {
        badgeEl.textContent = TR.OFFLINE;
        badgeEl.className = 'pane-badge status-offline';
      }
    } finally {
      if (pane.loadVersion === loadVersion) pane.loading = false;
    }
  }

  private async loadCompareData(pane: ChartPaneState, symbolStr: string): Promise<void> {
    const symbolInfo = ALL_SYMBOLS.find(s => s.symbol === symbolStr || s.symbol.replace('.IS', '') === symbolStr);
    if (!symbolInfo) {
      alert(TR.NO_DATA + ': ' + symbolStr);
      pane.chartPanel.clearCompare();
      return;
    }

    try {
      const candles = await loadHistorical(symbolInfo.symbol, pane.timeframe, { assetType: symbolInfo.assetType });
      pane.chartPanel.setCompareData(symbolInfo.symbol, candles);
    } catch (e) {
      alert('Hata: ' + (e as Error).message);
      pane.chartPanel.clearCompare();
    }
  }

  private connectPaneWS(pane: ChartPaneState): void {
    const qs = new QuoteStream({
      symbols: [pane.symbol.symbol],
      intervals: [pane.timeframe],
    });

    pane.quoteUnsub = qs.onBars((msg: QuoteMessage) => {
      if (msg.symbol !== pane.symbol.symbol.toUpperCase()) return;
      if (msg.interval !== pane.timeframe) return;

      for (const bar of msg.bars) {
        const idx = pane.candles.findIndex(c => c.time === bar.time);
        if (idx >= 0) {
          pane.candles[idx] = bar;
          pane.chartPanel.updateLastCandle(bar);
        } else {
          pane.candles = [...pane.candles, bar];
          pane.chartPanel.setData(pane.candles, {
            reason: 'append',
            symbol: pane.symbol.symbol,
            currency: pane.symbol.currency,
            timeframe: pane.timeframe,
            preserveTimeRange: true,
          });
        }
      }

      const badgeEl = pane.containerEl.querySelector<HTMLElement>(`#pane-badge-${pane.id}`);
      if (badgeEl) {
        badgeEl.textContent = TR.LIVE;
        badgeEl.className = 'pane-badge status-live';
      }
    });

    qs.connect();
    pane.quoteStream = qs;
  }

  private disconnectPane(pane: ChartPaneState): void {
    if (pane.quoteUnsub) {
      pane.quoteUnsub();
      pane.quoteUnsub = null;
    }
    if (pane.quoteStream) {
      pane.quoteStream.disconnect();
      pane.quoteStream = null;
    }
  }

  // ─── Yardımcılar ──────────────────────────────────────────────────────

  private pickNextSymbol(): SymbolInfo {
    // Kullanılmayan ilk sembolü seç
    const used = new Set(this.panes.map(p => p.symbol.symbol));
    const next = ALL_SYMBOLS.find(s => !used.has(s.symbol));
    return next ?? DEFAULT_SYMBOL;
  }

  // ─── Cleanup ──────────────────────────────────────────────────────────

  destroy(): void {
    for (const pane of this.panes) {
      this.disconnectPane(pane);
      pane.chartPanel.destroy();
    }
    this.panes = [];
  }
}
