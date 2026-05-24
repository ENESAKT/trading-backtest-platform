/**
 * CommandPalette — Cmd+K / Ctrl+K ile açılan hızlı arama ve komut paleti.
 *
 * Özellikler:
 *  - Sembol arama (SymbolUniverse)
 *  - Komut arama (sekme geçişleri, eylemler)
 *  - Son kullanılan semboller (localStorage)
 *  - Ok tuşları + Enter ile klavye gezintisi
 *  - Escape ile kapat
 */

import type { SymbolInfo } from '../types.js';
import { symbolUniverse } from '../core/SymbolUniverse.js';

// ─── Tipler ──────────────────────────────────────────────────────────────────

type ResultKind = 'symbol' | 'command' | 'recent';

interface PaletteResult {
  kind: ResultKind;
  id: string;
  label: string;
  sublabel?: string;
  icon: string;
  action: () => void;
}

// ─── Sabitler ────────────────────────────────────────────────────────────────

const LS_RECENT = 'pp_recent_symbols';
const MAX_RECENT = 10;
const MAX_RESULTS = 12;

// ─── CSS ─────────────────────────────────────────────────────────────────────

const CSS = `
<style id="cp-styles">
.cp-backdrop {
  position: fixed; inset: 0; z-index: 9000;
  background: rgba(0,0,0,.55); backdrop-filter: blur(3px);
  display: flex; align-items: flex-start; justify-content: center;
  padding-top: 12vh;
  opacity: 0; transition: opacity .15s ease;
  pointer-events: none;
}
.cp-backdrop.cp-open {
  opacity: 1; pointer-events: auto;
}
.cp-modal {
  background: var(--bg-panel, #1a1f2e);
  border: 1px solid var(--border, rgba(255,255,255,.12));
  border-radius: 14px;
  width: min(560px, calc(100vw - 32px));
  box-shadow: 0 24px 64px rgba(0,0,0,.55);
  overflow: hidden;
  transform: translateY(-8px) scale(.98);
  transition: transform .15s ease;
}
.cp-backdrop.cp-open .cp-modal {
  transform: none;
}
/* ── Input ── */
.cp-input-wrap {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 16px; border-bottom: 1px solid var(--border, rgba(255,255,255,.08));
}
.cp-search-icon {
  color: var(--text-dim, #64748B); flex-shrink: 0;
}
.cp-input {
  flex: 1; background: none; border: none; outline: none;
  font-size: 16px; color: var(--text-bold, #F8FAFC);
  caret-color: var(--accent, #ffb020);
}
.cp-input::placeholder { color: var(--text-dim, #64748B); }
.cp-clear-btn {
  padding: 2px 6px; border-radius: 5px; background: none;
  border: none; color: var(--text-dim); cursor: pointer; font-size: 16px;
  line-height: 1; display: none;
}
.cp-clear-btn.visible { display: block; }
/* ── Results ── */
.cp-results { max-height: 380px; overflow-y: auto; }
.cp-results:empty::after {
  content: 'Sonuç bulunamadı';
  display: block; padding: 24px; text-align: center;
  color: var(--text-dim); font-size: 13px;
}
.cp-section-label {
  padding: 8px 16px 4px; font-size: 10px; font-weight: 700;
  letter-spacing: .08em; text-transform: uppercase;
  color: var(--text-dim, #64748B);
}
.cp-item {
  display: flex; align-items: center; gap: 12px;
  padding: 9px 16px; cursor: pointer;
  border-radius: 0; transition: background .08s;
}
.cp-item:hover, .cp-item.cp-selected {
  background: var(--hover-bg, rgba(255,255,255,.06));
}
.cp-item.cp-selected {
  background: rgba(255, 176, 32, .08);
  outline: none;
}
.cp-item-icon {
  width: 32px; height: 32px; border-radius: 8px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px;
  background: rgba(255,255,255,.06);
}
.cp-item-icon.kind-symbol  { background: rgba(16, 185, 129, .12); color: #10B981; }
.cp-item-icon.kind-recent  { background: rgba(99, 179, 237, .12); color: #63B3ED; }
.cp-item-icon.kind-command { background: rgba(139, 92, 246, .12); color: #8B5CF6; }
.cp-item-text { flex: 1; min-width: 0; }
.cp-item-label {
  font-size: 13px; font-weight: 500; color: var(--text-bold, #F8FAFC);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.cp-item-label mark {
  background: none; color: var(--accent, #ffb020); font-weight: 700;
}
.cp-item-sub {
  font-size: 11px; color: var(--text-dim, #64748B);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.cp-item-badge {
  font-size: 10px; padding: 2px 7px; border-radius: 4px;
  background: rgba(255,255,255,.06); color: var(--text-dim);
  flex-shrink: 0; font-weight: 600;
}
/* ── Footer ── */
.cp-footer {
  padding: 8px 16px; border-top: 1px solid var(--border, rgba(255,255,255,.06));
  display: flex; gap: 14px; align-items: center;
  font-size: 10px; color: var(--text-dim, #64748B);
}
.cp-footer kbd {
  padding: 1px 5px; border-radius: 4px; font-size: 10px;
  background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.12);
  color: var(--text-dim); font-family: inherit;
}
</style>`;

// ─── CommandPalette ───────────────────────────────────────────────────────────

export class CommandPalette {
  private backdrop!: HTMLElement;
  private input!: HTMLInputElement;
  private resultsEl!: HTMLElement;
  private clearBtn!: HTMLButtonElement;

  private results: PaletteResult[] = [];
  private selectedIdx = -1;
  private isOpen = false;

  /** Komutlar — app.ts tarafından inject edilir. */
  private commands: PaletteResult[] = [];

  /** Sembol seçilince çağrılır. */
  private onSymbolSelectCb: ((info: SymbolInfo) => void) | null = null;

  constructor() {
    this._buildDOM();
    this._bindKeys();
  }

  // ─── Public API ──────────────────────────────────────────────────────────

  /** Uygulama komutlarını yükle (tab geçişleri, özel eylemler). */
  setCommands(cmds: Array<{ id: string; label: string; sublabel?: string; icon: string; action: () => void }>): void {
    this.commands = cmds.map(c => ({ ...c, kind: 'command' as const }));
  }

  /** Sembol seçimi callback'i */
  onSymbolSelect(cb: (info: SymbolInfo) => void): void {
    this.onSymbolSelectCb = cb;
  }

  open(): void {
    if (this.isOpen) return;
    this.isOpen = true;
    this.backdrop.classList.add('cp-open');
    this.input.value = '';
    this.clearBtn.classList.remove('visible');
    this._search('');
    requestAnimationFrame(() => this.input.focus());
  }

  close(): void {
    if (!this.isOpen) return;
    this.isOpen = false;
    this.backdrop.classList.remove('cp-open');
    this.input.blur();
  }

  toggle(): void {
    this.isOpen ? this.close() : this.open();
  }

  // ─── Recent Symbols ───────────────────────────────────────────────────────

  static getRecent(): string[] {
    try {
      return JSON.parse(localStorage.getItem(LS_RECENT) || '[]') as string[];
    } catch { return []; }
  }

  static addRecent(symbol: string): void {
    const list = CommandPalette.getRecent().filter(s => s !== symbol);
    list.unshift(symbol);
    localStorage.setItem(LS_RECENT, JSON.stringify(list.slice(0, MAX_RECENT)));
  }

  // ─── DOM Build ────────────────────────────────────────────────────────────

  private _buildDOM(): void {
    // Inject CSS once
    if (!document.getElementById('cp-styles')) {
      document.head.insertAdjacentHTML('beforeend', CSS);
    }

    this.backdrop = document.createElement('div');
    this.backdrop.className = 'cp-backdrop';
    this.backdrop.setAttribute('role', 'dialog');
    this.backdrop.setAttribute('aria-label', 'Komut Paleti');
    this.backdrop.setAttribute('aria-modal', 'true');

    this.backdrop.innerHTML = `
      <div class="cp-modal" role="combobox" aria-expanded="true" aria-haspopup="listbox">
        <div class="cp-input-wrap">
          <svg class="cp-search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          <input class="cp-input" type="text" placeholder="Sembol veya komut ara…"
                 autocomplete="off" autocorrect="off" spellcheck="false"
                 role="searchbox" aria-label="Arama"/>
          <button class="cp-clear-btn" aria-label="Temizle" tabindex="-1">✕</button>
        </div>
        <div class="cp-results" role="listbox" aria-label="Sonuçlar"></div>
        <div class="cp-footer">
          <span><kbd>↑</kbd><kbd>↓</kbd> Gezin</span>
          <span><kbd>↵</kbd> Seç</span>
          <span><kbd>Esc</kbd> Kapat</span>
        </div>
      </div>`;

    this.input     = this.backdrop.querySelector('.cp-input')!;
    this.resultsEl = this.backdrop.querySelector('.cp-results')!;
    this.clearBtn  = this.backdrop.querySelector('.cp-clear-btn')!;

    document.body.appendChild(this.backdrop);

    // Backdrop click
    this.backdrop.addEventListener('click', (e) => {
      if (e.target === this.backdrop) this.close();
    });

    // Input events
    this.input.addEventListener('input', () => {
      const q = this.input.value;
      this.clearBtn.classList.toggle('visible', q.length > 0);
      void this._search(q);
    });

    this.clearBtn.addEventListener('click', () => {
      this.input.value = '';
      this.clearBtn.classList.remove('visible');
      void this._search('');
      this.input.focus();
    });
  }

  // ─── Keyboard ─────────────────────────────────────────────────────────────

  private _bindKeys(): void {
    document.addEventListener('keydown', (e) => {
      // Cmd+K / Ctrl+K
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        this.toggle();
        return;
      }

      if (!this.isOpen) return;

      switch (e.key) {
        case 'Escape':
          e.stopPropagation();
          this.close();
          break;
        case 'ArrowDown':
          e.preventDefault();
          this._moveSelection(1);
          break;
        case 'ArrowUp':
          e.preventDefault();
          this._moveSelection(-1);
          break;
        case 'Enter':
          e.preventDefault();
          this._selectCurrent();
          break;
      }
    });
  }

  private _moveSelection(delta: number): void {
    const max = this.results.length;
    if (max === 0) return;
    this.selectedIdx = (this.selectedIdx + delta + max) % max;
    this._renderResults();
    this.resultsEl.querySelector('.cp-selected')?.scrollIntoView({ block: 'nearest' });
  }

  private _selectCurrent(): void {
    const result = this.results[this.selectedIdx];
    if (!result) return;
    this._executeResult(result);
  }

  private _executeResult(result: PaletteResult): void {
    result.action();
    this.close();
  }

  // ─── Search ───────────────────────────────────────────────────────────────

  private async _search(query: string): Promise<void> {
    const q = query.trim().toLowerCase();
    this.selectedIdx = q ? 0 : -1;

    if (!q) {
      // Empty state: show recent + top commands
      await this._buildEmptyResults();
    } else {
      await this._buildQueryResults(q);
    }
    this._renderResults();
  }

  private async _buildEmptyResults(): Promise<void> {
    const recentSymbols = CommandPalette.getRecent();
    const results: PaletteResult[] = [];

    // Recent symbols
    if (recentSymbols.length > 0) {
      const allSymbols = await symbolUniverse.all().catch((): SymbolInfo[] => []);
      const symbolMap = new Map<string, SymbolInfo>(allSymbols.map(s => [s.symbol, s] as [string, SymbolInfo]));
      for (const sym of recentSymbols.slice(0, 6)) {
        const fallback: SymbolInfo = { symbol: sym, name: sym, assetType: 'equity', group: 'BIST', currency: 'TRY' };
        const resolved: SymbolInfo = symbolMap.get(sym) ?? fallback;
        results.push({
          kind: 'recent',
          id: `recent:${sym}`,
          label: sym,
          sublabel: resolved.name,
          icon: '🕐',
          action: () => this._openSymbol(resolved),
        });
      }
    }

    // Top commands
    for (const cmd of this.commands.slice(0, 5)) {
      results.push(cmd);
    }

    this.results = results.slice(0, MAX_RESULTS);
  }

  private async _buildQueryResults(q: string): Promise<void> {
    const results: PaletteResult[] = [];

    // Symbol search
    const allSymbols = await symbolUniverse.all().catch((): SymbolInfo[] => []);
    const symMatches = allSymbols
      .filter(s =>
        s.symbol.toLowerCase().includes(q) ||
        s.name.toLowerCase().includes(q)
      )
      .sort((a, b) => {
        // Exact symbol start first
        const aExact = a.symbol.toLowerCase().startsWith(q) ? 0 : 1;
        const bExact = b.symbol.toLowerCase().startsWith(q) ? 0 : 1;
        return aExact - bExact || a.symbol.localeCompare(b.symbol);
      })
      .slice(0, 8);

    for (const sym of symMatches) {
      results.push({
        kind: 'symbol',
        id: `sym:${sym.symbol}`,
        label: sym.symbol,
        sublabel: sym.name,
        icon: this._symbolIcon(sym),
        action: () => this._openSymbol(sym),
      });
    }

    // Command search
    const cmdMatches = this.commands.filter(c =>
      c.label.toLowerCase().includes(q) ||
      (c.sublabel?.toLowerCase().includes(q) ?? false)
    );
    for (const cmd of cmdMatches.slice(0, 4)) {
      results.push(cmd);
    }

    this.results = results.slice(0, MAX_RESULTS);
    if (this.results.length > 0) this.selectedIdx = 0;
  }

  private _symbolIcon(info: SymbolInfo): string {
    if (info.group?.startsWith('Kripto') || info.assetType === 'crypto') return '₿';
    if (info.group?.startsWith('BIST') || info.group === 'BIST') return '🏛';
    if (info.assetType === 'commodity') return '🏷';
    if (info.group === 'Endeks') return '📊';
    if (info.assetType === 'fx') return '💱';
    return '📈';
  }

  private _openSymbol(info: SymbolInfo): void {
    CommandPalette.addRecent(info.symbol);
    if (this.onSymbolSelectCb) {
      this.onSymbolSelectCb(info);
    } else {
      window.dispatchEvent(new CustomEvent('openSymbolOnChart', { detail: { symbol: info.symbol } }));
    }
  }

  // ─── Render ───────────────────────────────────────────────────────────────

  private _renderResults(): void {
    if (this.results.length === 0) {
      this.resultsEl.innerHTML = '';
      return;
    }

    const q = this.input.value.trim();
    const groups: Partial<Record<ResultKind, PaletteResult[]>> = {};
    for (const r of this.results) {
      (groups[r.kind] ??= []).push(r);
    }

    const sectionLabel: Record<ResultKind, string> = {
      recent: 'Son Kullanılanlar',
      symbol: 'Semboller',
      command: 'Komutlar',
    };

    let html = '';
    for (const kind of ['recent', 'symbol', 'command'] as ResultKind[]) {
      const items = groups[kind];
      if (!items?.length) continue;
      html += `<div class="cp-section-label">${sectionLabel[kind]}</div>`;
      for (const item of items) {
        const idx = this.results.indexOf(item);
        const sel = idx === this.selectedIdx ? ' cp-selected' : '';
        const labelHtml = q ? this._highlight(item.label, q) : this._esc(item.label);
        const subHtml = item.sublabel ? this._esc(item.sublabel) : '';
        html += `
          <div class="cp-item${sel}" data-idx="${idx}" role="option" aria-selected="${idx === this.selectedIdx}">
            <div class="cp-item-icon kind-${kind}">${this._esc(item.icon)}</div>
            <div class="cp-item-text">
              <div class="cp-item-label">${labelHtml}</div>
              ${subHtml ? `<div class="cp-item-sub">${subHtml}</div>` : ''}
            </div>
            ${kind !== 'command' ? `<span class="cp-item-badge">${this._esc(kind === 'recent' ? 'son' : 'sembol')}</span>` : ''}
          </div>`;
      }
    }

    this.resultsEl.innerHTML = html;

    // Click handlers
    this.resultsEl.querySelectorAll<HTMLElement>('.cp-item').forEach(el => {
      el.addEventListener('click', () => {
        const idx = Number(el.dataset['idx']);
        const result = this.results[idx];
        if (result) this._executeResult(result);
      });
    });
  }

  private _highlight(text: string, query: string): string {
    const escaped = this._esc(text);
    const qEsc = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return escaped.replace(new RegExp(`(${qEsc})`, 'gi'), '<mark>$1</mark>');
  }

  private _esc(s: string): string {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
}
