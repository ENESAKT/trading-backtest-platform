import type { SymbolInfo } from '../types.js';
import { TR, formatNumber, formatPct } from '../constants/tr.js';
import {
  BIST30, BIST100_EXTRA, US_SYMBOLS, CRYPTO_SYMBOLS, FX_COMMODITY_SYMBOLS,
  VIOP_SYMBOLS, ALL_SYMBOLS,
} from '../constants/symbols.js';

const LS_LAST_SYMBOL = 'piyasapilot_last_symbol';

type SymbolSelectListener = (info: SymbolInfo) => void;

interface GroupDef {
  label: string;
  flag: string;
  symbols: SymbolInfo[];
}

const GROUPS: GroupDef[] = [
  { label: TR.BIST30,        flag: '🇹🇷', symbols: BIST30          },
  { label: TR.BIST100,       flag: '🇹🇷', symbols: BIST100_EXTRA   },
  { label: TR.US_MARKETS,    flag: '🇺🇸', symbols: US_SYMBOLS      },
  { label: TR.CRYPTO,        flag: '₿',   symbols: CRYPTO_SYMBOLS  },
  { label: TR.FX_COMMODITY,  flag: '💱',  symbols: FX_COMMODITY_SYMBOLS },
  { label: 'VİOP',           flag: 'Vi',  symbols: VIOP_SYMBOLS    },
];

// ─── Sidebar ──────────────────────────────────────────────────────────────────

export class Sidebar {
  private container: HTMLElement;
  private listeners: Set<SymbolSelectListener> = new Set();
  private searchInput!: HTMLInputElement;
  private listEl!: HTMLElement;
  private activeSymbol = '';
  private priceTickers = new Map<string, { price: number; changePct: number }>();
  private collapsedGroups = new Set<string>();

  constructor(container: HTMLElement) {
    this.container = container;
    this.render();
    this.bindSearch();
    this.restoreLastSymbol();
  }

  // ─── Public API ──────────────────────────────────────────────────────────

  onSymbolSelect(listener: SymbolSelectListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  updateTicker(symbol: string, price: number, changePct: number): void {
    this.priceTickers.set(symbol, { price, changePct });
    this.refreshTicker(symbol, price, changePct);
  }

  setActiveSymbol(symbol: string): void {
    this.activeSymbol = symbol;
    this.container.querySelectorAll('.sym-item').forEach(el => {
      el.classList.toggle('active', (el as HTMLElement).dataset['symbol'] === symbol);
    });
  }

  // ─── Render ──────────────────────────────────────────────────────────────

  private render(): void {
    this.container.innerHTML = `
      <div class="sidebar-header">
        <span class="sidebar-title">${TR.APP_NAME}</span>
      </div>
      <div class="sidebar-search">
        <input type="text" placeholder="${TR.SEARCH_PLACEHOLDER}" class="search-input" />
      </div>
      <div class="symbol-list"></div>
    `;

    this.searchInput = this.container.querySelector('.search-input')!;
    this.listEl = this.container.querySelector('.symbol-list')!;

    this.renderGroups(GROUPS);
  }

  private renderGroups(groups: GroupDef[]): void {
    this.listEl.innerHTML = '';
    groups.forEach(g => this.renderGroup(g));
  }

  private renderGroup(g: GroupDef): void {
    const isCollapsed = this.collapsedGroups.has(g.label);

    const groupEl = document.createElement('div');
    groupEl.className = 'sym-group';

    const header = document.createElement('div');
    header.className = 'sym-group-header';
    header.innerHTML = `
      <span class="group-flag">${g.flag}</span>
      <span class="group-label">${g.label}</span>
      <span class="group-chevron">${isCollapsed ? '▶' : '▼'}</span>
    `;
    header.addEventListener('click', () => this.toggleGroup(g.label, header, itemsEl));
    groupEl.appendChild(header);

    const itemsEl = document.createElement('div');
    itemsEl.className = 'sym-items';
    itemsEl.style.display = isCollapsed ? 'none' : '';

    g.symbols.forEach(s => {
      const item = this.createSymbolItem(s);
      itemsEl.appendChild(item);
    });

    groupEl.appendChild(itemsEl);
    this.listEl.appendChild(groupEl);
  }

  private createSymbolItem(s: SymbolInfo): HTMLElement {
    const ticker = this.priceTickers.get(s.symbol);
    const changePct = ticker?.changePct ?? 0;
    const price = ticker?.price ?? null;

    const el = document.createElement('div');
    el.className = `sym-item${this.activeSymbol === s.symbol ? ' active' : ''}`;
    el.dataset['symbol'] = s.symbol;
    el.innerHTML = `
      <div class="sym-main">
        <span class="sym-ticker">${s.symbol.replace('.IS', '').replace('=X', '').replace('=F', '')}</span>
        <span class="sym-name">${s.name}</span>
      </div>
      <div class="sym-meta">
        <span class="sym-price">${price != null ? formatNumber(price, 2) : '—'}</span>
        <span class="sym-change ${changePct >= 0 ? 'pos' : 'neg'}">${formatPct(changePct)}</span>
      </div>
    `;
    el.addEventListener('click', () => this.selectSymbol(s));
    return el;
  }

  private toggleGroup(label: string, header: HTMLElement, itemsEl: HTMLElement): void {
    if (this.collapsedGroups.has(label)) {
      this.collapsedGroups.delete(label);
      itemsEl.style.display = '';
      header.querySelector('.group-chevron')!.textContent = '▼';
    } else {
      this.collapsedGroups.add(label);
      itemsEl.style.display = 'none';
      header.querySelector('.group-chevron')!.textContent = '▶';
    }
  }

  // ─── Selection ───────────────────────────────────────────────────────────

  private selectSymbol(info: SymbolInfo): void {
    this.activeSymbol = info.symbol;
    this.container.querySelectorAll('.sym-item').forEach(el => {
      el.classList.toggle('active', (el as HTMLElement).dataset['symbol'] === info.symbol);
    });
    localStorage.setItem(LS_LAST_SYMBOL, info.symbol);
    this.listeners.forEach(l => l(info));
  }

  private restoreLastSymbol(): void {
    const last = localStorage.getItem(LS_LAST_SYMBOL);
    if (last) {
      const info = ALL_SYMBOLS.find(s => s.symbol === last);
      if (info) {
        setTimeout(() => this.selectSymbol(info), 0);
      }
    } else {
      // Default: BTCUSDT
      const def = CRYPTO_SYMBOLS[0]!;
      setTimeout(() => this.selectSymbol(def), 0);
    }
  }

  // ─── Search ──────────────────────────────────────────────────────────────

  private bindSearch(): void {
    let debounce: ReturnType<typeof setTimeout>;
    this.searchInput.addEventListener('input', () => {
      clearTimeout(debounce);
      debounce = setTimeout(() => this.applySearch(this.searchInput.value.trim()), 300);
    });
  }

  private applySearch(query: string): void {
    if (!query) {
      this.renderGroups(GROUPS);
      return;
    }

    const q = query.toLowerCase();
    const matched = ALL_SYMBOLS.filter(
      s => s.symbol.toLowerCase().includes(q) || s.name.toLowerCase().includes(q)
    );

    this.listEl.innerHTML = '';
    if (matched.length === 0) {
      this.listEl.innerHTML = `<div class="no-results">${TR.SYMBOL_NOT_FOUND}</div>`;
      return;
    }

    matched.forEach(s => {
      const item = this.createSymbolItem(s);
      this.listEl.appendChild(item);
    });
  }

  // ─── Ticker refresh ──────────────────────────────────────────────────────

  private refreshTicker(symbol: string, price: number, changePct: number): void {
    const el = this.container.querySelector(`[data-symbol="${symbol}"]`);
    if (!el) return;

    const priceEl   = el.querySelector('.sym-price');
    const changeEl  = el.querySelector('.sym-change');
    if (priceEl)  priceEl.textContent  = formatNumber(price, 2);
    if (changeEl) {
      changeEl.textContent = formatPct(changePct);
      changeEl.className = `sym-change ${changePct >= 0 ? 'pos' : 'neg'}`;
    }
  }
}
