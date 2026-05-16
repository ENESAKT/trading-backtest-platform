import type { SymbolInfo } from '../types.js';
import { TR, formatNumber, formatPct } from '../constants/tr.js';
import {
  BIST30, BIST100_EXTRA, US_SYMBOLS, CRYPTO_SYMBOLS, FX_COMMODITY_SYMBOLS,
  VIOP_SYMBOLS, ALL_SYMBOLS,
} from '../constants/symbols.js';
import { planGate } from '../auth/PlanGate.js';

const LS_LAST_SYMBOL = 'piyasapilot_last_symbol';
const LS_SIDEBAR_COLLAPSED = 'piyasapilot_sidebar_collapsed';
const LS_FAVORITES = 'piyasapilot_favorites';
const DEFAULT_FAVORITES = ['VAKBN.IS', 'AKBNK.IS', 'ASELS.IS', 'ARCLK.IS', 'THYAO.IS'];
const LAZY_BATCH_SIZE = 15; // Her lazy-load batch'inde gösterilecek sembol sayısı

/** Yüzde değişim için CSS sınıfı: > 0 yeşil, < 0 kırmızı, === 0 sarı */
function changeColorClass(changePct: number): string {
  if (changePct > 0) return 'pos';
  if (changePct < 0) return 'neg';
  return 'neutral';
}

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
  private collapsedGroups = new Set<string>(GROUPS.map(g => g.label));
  private isCollapsed = false;
  private toggleBtn!: HTMLElement;
  private favorites = new Set<string>();
  private _observers: IntersectionObserver[] = [];

  constructor(container: HTMLElement) {
    this.container = container;
    this.isCollapsed = localStorage.getItem(LS_SIDEBAR_COLLAPSED) === 'true';
    this.loadFavorites();
    this.render();
    this.bindSearch();
    this.applyCollapsedState();
  }

  private loadFavorites(): void {
    try {
      const stored = JSON.parse(localStorage.getItem(LS_FAVORITES) || '[]');
      if (Array.isArray(stored)) {
        this.favorites = new Set(stored);
      }
    } catch {
      this.favorites = new Set();
    }
    if (this.favorites.size === 0) {
      this.favorites = new Set(DEFAULT_FAVORITES);
      this.saveFavorites();
    }
  }

  private saveFavorites(): void {
    localStorage.setItem(LS_FAVORITES, JSON.stringify(Array.from(this.favorites)));
  }

  private toggleFavorite(symbol: string, e: Event): void {
    e.stopPropagation();
    if (this.favorites.has(symbol)) {
      this.favorites.delete(symbol);
    } else {
      this.favorites.add(symbol);
    }
    this.saveFavorites();
    this.renderGroups(GROUPS); // Re-render groups to show/hide in Favorites group
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
    localStorage.setItem(LS_LAST_SYMBOL, symbol);
    this.container.querySelectorAll('.sym-item').forEach(el => {
      el.classList.toggle('active', (el as HTMLElement).dataset['symbol'] === symbol);
    });
  }

  getFavoriteSymbols(): SymbolInfo[] {
    return Array.from(this.favorites)
      .map(sym => ALL_SYMBOLS.find(s => s.symbol === sym))
      .filter((s): s is SymbolInfo => Boolean(s));
  }

  getStartupSymbol(): SymbolInfo {
    const last = localStorage.getItem(LS_LAST_SYMBOL);
    if (last) {
      const info = ALL_SYMBOLS.find(s => s.symbol === last);
      if (info) return info;
    }
    return this.getFavoriteSymbols()[0] ?? BIST30.find(s => s.symbol === 'VAKBN.IS') ?? BIST30[0]!;
  }

  // ─── Render ──────────────────────────────────────────────────────────────

  private render(): void {
    this.container.innerHTML = `
      <div class="sidebar-header">
        <span class="sidebar-title">${TR.APP_NAME}</span>
        <button class="sidebar-toggle-btn" id="sidebar-toggle-btn" title="Paneli aç/kapat"><svg class="icon-svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg></button>
      </div>
      <div class="sidebar-search">
        <input type="text" placeholder="${TR.SEARCH_PLACEHOLDER}" class="search-input" />
      </div>
      <div class="symbol-list"></div>
    `;

    this.searchInput = this.container.querySelector('.search-input')!;
    this.listEl = this.container.querySelector('.symbol-list')!;
    this.toggleBtn = this.container.querySelector('#sidebar-toggle-btn')!;
    this.toggleBtn.addEventListener('click', () => this.toggleCollapse());

    this.renderGroups(GROUPS);
  }

  /** Sidebar'ı aç/kapat (toggle) */
  toggleCollapse(): void {
    this.isCollapsed = !this.isCollapsed;
    localStorage.setItem(LS_SIDEBAR_COLLAPSED, String(this.isCollapsed));
    this.applyCollapsedState();
  }

  /** Collapse state'ini DOM'a yansıt */
  private applyCollapsedState(): void {
    this.container.classList.toggle('collapsed', this.isCollapsed);
    if (this.toggleBtn) {
      this.toggleBtn.innerHTML = this.isCollapsed 
        ? '<svg class="icon-svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>'
        : '<svg class="icon-svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>';
    }
  }

  private renderGroups(groups: GroupDef[]): void {
    this.listEl.innerHTML = '';

    // Favoriler Grubunu oluştur
    if (this.favorites.size > 0) {
      const favSymbols: SymbolInfo[] = [];
      this.favorites.forEach(sym => {
        const info = ALL_SYMBOLS.find(s => s.symbol === sym);
        if (info) favSymbols.push(info);
      });
      if (favSymbols.length > 0) {
        this.renderGroup({ label: 'Favoriler', flag: '⭐', symbols: favSymbols });
      }
    }

    groups.forEach(g => this.renderGroup(g));
  }

  private renderGroup(g: GroupDef): void {
    const isCollapsed = this.collapsedGroups.has(g.label);
    const isLocked = !planGate.isGroupAllowed(g.label);

    const groupEl = document.createElement('div');
    groupEl.className = 'sym-group';

    const header = document.createElement('div');
    header.className = `sym-group-header${isLocked ? ' locked' : ''}`;
    header.innerHTML = `
      <span class="group-flag">${g.flag}</span>
      <span class="group-label">${g.label}</span>
      ${isLocked ? '<span class="sym-group-lock">🔒 Yükselt</span>' : `<span class="group-chevron">${isCollapsed ? '▶' : '▼'}</span>`}
    `;

    if (isLocked) {
      header.addEventListener('click', () => {
        planGate.showPlanGate({
          title: `${g.label} — Erişim Gerekli`,
          description: `${g.label} sembollerine erişmek için ücretsiz kayıt olun veya planınızı yükseltin.`,
          requiredTier: 'free',
        });
      });
    } else {
      header.addEventListener('click', () => this.toggleGroup(g.label, header, itemsEl));
    }
    groupEl.appendChild(header);

    const itemsEl = document.createElement('div');
    itemsEl.className = 'sym-items';
    // Kilitli gruplar her zaman kapalı gösterilir
    itemsEl.style.display = (isLocked || isCollapsed) ? 'none' : '';

    g.symbols.forEach((s, i) => {
      if (i < LAZY_BATCH_SIZE) {
        const item = this.createSymbolItem(s);
        itemsEl.appendChild(item);
      }
    });

    // Lazy-load: kalan sembolleri IntersectionObserver ile yükle
    if (g.symbols.length > LAZY_BATCH_SIZE) {
      const sentinel = document.createElement('div');
      sentinel.className = 'lazy-sentinel';
      sentinel.style.height = '1px';
      itemsEl.appendChild(sentinel);

      let loaded = LAZY_BATCH_SIZE;
      const observer = new IntersectionObserver((entries) => {
        if (!entries[0]?.isIntersecting) return;
        const batch = g.symbols.slice(loaded, loaded + LAZY_BATCH_SIZE);
        batch.forEach(s => {
          const item = this.createSymbolItem(s);
          itemsEl.insertBefore(item, sentinel);
        });
        loaded += batch.length;
        if (loaded >= g.symbols.length) {
          observer.disconnect();
          this._observers = this._observers.filter(o => o !== observer);
          sentinel.remove();
        }
      }, { root: this.listEl, rootMargin: '100px' });
      observer.observe(sentinel);
      this._observers.push(observer);
    }

    groupEl.appendChild(itemsEl);
    this.listEl.appendChild(groupEl);
  }

  private createSymbolItem(s: SymbolInfo): HTMLElement {
    const ticker = this.priceTickers.get(s.symbol);
    const changePct = ticker?.changePct ?? 0;
    const price = ticker?.price ?? null;
    const isFav = this.favorites.has(s.symbol);

    const el = document.createElement('div');
    el.className = `sym-item${this.activeSymbol === s.symbol ? ' active' : ''}`;
    el.dataset['symbol'] = s.symbol;
    el.innerHTML = `
      <button class="sym-fav${isFav ? ' active' : ''}" type="button" title="${isFav ? 'Favorilerden çıkar' : 'Favorilere ekle'}" aria-label="${isFav ? 'Favorilerden çıkar' : 'Favorilere ekle'}">${isFav ? '★' : '☆'}</button>
      <div class="sym-main">
        <span class="sym-ticker">${s.symbol.replace('.IS', '').replace('=X', '').replace('=F', '')}</span>
        <span class="sym-name">${s.name}</span>
      </div>
      <div class="sym-meta">
        <span class="sym-price">${price != null ? formatNumber(price, 2) : '—'}</span>
        <span class="sym-change ${changeColorClass(changePct)}">${formatPct(changePct)}</span>
      </div>
    `;
    
    const favBtn = el.querySelector('.sym-fav') as HTMLElement;
    favBtn.addEventListener('click', (e) => this.toggleFavorite(s.symbol, e));

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

  /** Tüm IntersectionObserver'ları temizler — component unmount edilirken çağrılmalı */
  destroy(): void {
    this._observers.forEach(o => o.disconnect());
    this._observers = [];
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
      changeEl.className = `sym-change ${changeColorClass(changePct)}`;
    }
  }
}
