import type { OHLCV, SymbolInfo, Timeframe, Signal } from '../types.js';
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

    this.updateGrid();
    this.updateControlsActive();
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
    void this.loadPaneData(pane);
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

  private layoutControlsHTML(): string {
    return `
      <div class="mcl-group">
        <span class="mcl-label">Düzen</span>
        ${Object.entries(LAYOUTS).map(([mode, cfg]) =>
          `<button class="ctrl-btn mcl-btn${mode === this.layout ? ' active' : ''}" data-layout="${mode}" title="${cfg.label}">${cfg.icon}</button>`
        ).join('')}
      </div>
    `;
  }

  private bindLayoutControls(): void {
    this.controlsEl.addEventListener('click', (e) => {
      const btn = (e.target as HTMLElement).closest<HTMLElement>('[data-layout]');
      if (!btn) return;
      const mode = btn.dataset['layout'] as LayoutMode;
      this.setLayout(mode);
    });
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
      background: #21262d;
    `;

    // DOM'u sıfırla ve pane container'ları ekle
    this.gridEl.innerHTML = '';
    for (const pane of this.panes) {
      this.gridEl.appendChild(pane.containerEl);
    }
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
    };

    this.panes.push(pane);

    // Pane'e tıklayınca aktif yap
    containerEl.addEventListener('click', () => {
      this.setActivePane(id);
    });

    // Sembol seçici
    this.bindPaneHeader(pane, headerEl);

    // Veri yükle
    void this.loadPaneData(pane);

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
    await this.loadPaneData(pane);
  }

  private async loadPaneData(pane: ChartPaneState): Promise<void> {
    if (pane.loading) return;
    pane.loading = true;

    // Eski bağlantıyı kes
    this.disconnectPane(pane);

    const badgeEl = pane.containerEl.querySelector<HTMLElement>(`#pane-badge-${pane.id}`);
    if (badgeEl) {
      badgeEl.textContent = TR.CONNECTING;
      badgeEl.className = 'pane-badge status-connecting';
    }

    try {
      // 1) Tarihsel veri
      const candles = await loadHistorical(pane.symbol.symbol, pane.timeframe, {
        assetType: pane.symbol.assetType,
      });
      pane.candles = candles;
      pane.chartPanel.setData(candles);

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
    } catch {
      if (badgeEl) {
        badgeEl.textContent = TR.OFFLINE;
        badgeEl.className = 'pane-badge status-offline';
      }
    } finally {
      pane.loading = false;
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
          pane.chartPanel.setData(pane.candles);
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
