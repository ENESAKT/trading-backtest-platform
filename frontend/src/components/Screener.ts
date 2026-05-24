/**
 * Screener — Teknik & temel veri tabanlı sembol tarayıcı (v2).
 *
 * Yenilikler:
 *  - Evren seçici (BIST30 / BIST100 / Kripto / Tümü)
 *  - Kolon seti sekmeleri (Teknik / Performans / Değerleme / Tümü)
 *  - Sıralanabilir, pinlenebilir, gizlenebilir kolonlar
 *  - Düzenlenebilir filtre chip'leri (kolon + operatör + değer)
 *  - Backend preset'lerinden hızlı tarama
 *  - CSV dışa aktarma
 */

import type { ScreenerResult, ScreenerFilter, OHLCV } from '../types.js';
import { computeIndicators, lastValid, SMA } from '../indicators/index.js';
import { TR, formatNumber, formatPct } from '../constants/tr.js';
import { ALL_SYMBOLS } from '../constants/symbols.js';

// ─── Tipler ──────────────────────────────────────────────────────────────────

type Universe = 'BIST30' | 'BIST100' | 'CRYPTO' | 'ALL';
type ColSet   = 'technical' | 'performance' | 'valuation' | 'all';

interface ColDef {
  key: string;
  label: string;
  sets: ColSet[];   // hangi kolon setlerinde görünür
  align?: 'left' | 'right';
  fmt?: (v: unknown, row: BackendRow) => string;
  cls?: (v: unknown, row: BackendRow) => string;
}

interface BackendRow {
  symbol: string;
  name?: string;
  last_price?: number | null;
  change_pct?: number | null;
  volume?: number | null;
  volume_avg_20d?: number | null;
  distance_from_52w_high?: number | null;
  rsi_14?: number | null;
  market_cap?: number | null;
  pe_ratio?: number | null;
  sector?: string;
}

interface CustomFilter {
  id:     string;
  column: string;
  op:     string;
  value:  number | string;
}

// ─── Kolon tanımları ─────────────────────────────────────────────────────────

const fmtN = (v: unknown, d = 2) => {
  const n = typeof v === 'number' ? v : parseFloat(String(v ?? ''));
  if (isNaN(n)) return '—';
  return n.toLocaleString('tr-TR', { minimumFractionDigits: d, maximumFractionDigits: d });
};
const fmtP = (v: unknown, d = 2) => {
  const n = typeof v === 'number' ? v : parseFloat(String(v ?? ''));
  if (isNaN(n)) return '—';
  return (n >= 0 ? '+' : '') + fmtN(n, d) + '%';
};
const chgCls = (v: unknown) => {
  const n = typeof v === 'number' ? v : parseFloat(String(v ?? ''));
  return isNaN(n) ? '' : n >= 0 ? 'pos' : 'neg';
};
const rsiCls = (v: unknown) => {
  const n = typeof v === 'number' ? v : parseFloat(String(v ?? ''));
  return isNaN(n) ? '' : n < 30 ? 'pos' : n > 70 ? 'neg' : '';
};

const ALL_COLS: ColDef[] = [
  { key: 'symbol',   label: 'Sembol',    sets: ['technical','performance','valuation','all'], align: 'left', fmt: v => String(v ?? '—') },
  { key: 'name',     label: 'İsim',      sets: ['all'], align: 'left', fmt: v => String(v ?? '—') },
  { key: 'last_price', label: 'Fiyat',  sets: ['technical','performance','valuation','all'], align: 'right', fmt: v => fmtN(v) },
  { key: 'change_pct', label: 'Değ %',  sets: ['technical','performance','valuation','all'], align: 'right', fmt: v => fmtP(v), cls: chgCls },
  { key: 'rsi_14',   label: 'RSI 14',    sets: ['technical','all'], align: 'right', fmt: v => fmtN(v, 1), cls: rsiCls },
  { key: 'volume',   label: 'Hacim',     sets: ['technical','performance','all'], align: 'right', fmt: v => fmtN(v, 0) },
  { key: 'volume_avg_20d', label: 'Ort.Hacim(20g)', sets: ['technical','performance','all'], align: 'right', fmt: v => fmtN(v, 0) },
  { key: 'distance_from_52w_high', label: '52h. Zirveden', sets: ['performance','all'], align: 'right', fmt: v => fmtP(v), cls: chgCls },
  { key: 'market_cap', label: 'Piy.Değ.', sets: ['valuation','all'], align: 'right', fmt: v => fmtN(v, 0) },
  { key: 'pe_ratio', label: 'F/K',       sets: ['valuation','all'], align: 'right', fmt: v => fmtN(v) },
  { key: 'sector',   label: 'Sektör',    sets: ['valuation','all'], align: 'left',  fmt: v => String(v ?? '—') },
];

// ─── Screener sınıfı ─────────────────────────────────────────────────────────

export class Screener {
  private container: HTMLElement;
  private getCache: () => Map<string, OHLCV[]>;

  private universe: Universe = 'BIST100';
  private colSet: ColSet     = 'technical';
  private sortCol            = 'change_pct';
  private sortDir: 'asc' | 'desc' = 'desc';

  // Eski chip filtreler (hızlı butonlar)
  private quickFilters = new Set<ScreenerFilter>();
  // Özel filtreler (kullanıcı eklediği)
  private customFilters: CustomFilter[] = [];

  private rows: BackendRow[]     = [];
  private presets: unknown[]     = [];
  private isScanning             = false;
  private runMeta: Record<string, string> | null = null;
  private emptyMsg: string        = TR.NO_RESULTS;

  constructor(container: HTMLElement, getCache: () => Map<string, OHLCV[]>) {
    this.container = container;
    this.getCache  = getCache;
    this.loadPresets().then(() => this.render());
  }

  // ─── Preset yükleme ────────────────────────────────────────────────────────

  private async loadPresets(): Promise<void> {
    try {
      const res = await fetch('/api/screener/presets');
      if (res.ok) {
        const d = await res.json() as { presets?: unknown[] };
        this.presets = d.presets ?? [];
      }
    } catch { /* offline */ }
  }

  // ─── Ana render ────────────────────────────────────────────────────────────

  private render(): void {
    this.container.innerHTML = `
<style>
.scr-wrap { display:flex; flex-direction:column; gap:0; height:100%; }
/* ── Toolbar ── */
.scr-toolbar {
  display:flex; flex-wrap:wrap; align-items:center; gap:8px;
  padding:10px 14px; border-bottom:1px solid var(--border,rgba(255,255,255,.08));
}
.scr-universe-btns { display:flex; gap:4px; }
.scr-uni-btn {
  padding:4px 12px; font-size:12px; border-radius:20px;
  border:1px solid var(--border,rgba(255,255,255,.12));
  background:none; color:var(--text-dim,#64748B); cursor:pointer;
}
.scr-uni-btn.active {
  background:var(--blue,#3B82F6); color:#fff; border-color:var(--blue,#3B82F6);
}
.scr-divider { width:1px; height:20px; background:var(--border,rgba(255,255,255,.1)); }
.scr-scan-btn {
  padding:5px 16px; font-size:13px; font-weight:600; border-radius:6px;
  background:var(--blue,#3B82F6); color:#fff; border:none; cursor:pointer;
}
.scr-scan-btn:disabled { opacity:.5; cursor:not-allowed; }
.scr-export-btn {
  padding:4px 12px; font-size:12px; border-radius:6px;
  background:none; border:1px solid var(--border,rgba(255,255,255,.15));
  color:var(--text-dim); cursor:pointer; margin-left:auto;
}
.scr-export-btn:hover { color:var(--text,#94A3B8); }
/* ── Quick filters ── */
.scr-quick-filters {
  display:flex; flex-wrap:wrap; gap:6px;
  padding:8px 14px; border-bottom:1px solid var(--border,rgba(255,255,255,.06));
}
.scr-quick-label { font-size:11px; color:var(--text-dim); line-height:26px; }
.filter-btn {
  padding:3px 11px; font-size:12px; border-radius:20px;
  border:1px solid var(--border,rgba(255,255,255,.12));
  background:none; color:var(--text-dim,#64748B); cursor:pointer;
}
.filter-btn.active {
  background:rgba(59,130,246,.2); color:var(--blue,#3B82F6);
  border-color:var(--blue,#3B82F6);
}
/* ── Custom filters ── */
.scr-custom-filters {
  padding:6px 14px 8px; border-bottom:1px solid var(--border,rgba(255,255,255,.06));
  display:flex; flex-wrap:wrap; gap:6px; align-items:center;
}
.scr-filter-chip {
  display:inline-flex; align-items:center; gap:4px;
  padding:2px 8px; border-radius:20px; font-size:11px;
  background:rgba(59,130,246,.12); border:1px solid rgba(59,130,246,.3);
  color:var(--text,#94A3B8);
}
.scr-filter-chip .rm { cursor:pointer; color:var(--red,#EF4444); font-weight:700; margin-left:2px; }
.scr-add-filter-btn {
  padding:2px 10px; font-size:11px; border-radius:20px;
  border:1px dashed var(--border,rgba(255,255,255,.2));
  background:none; color:var(--text-dim); cursor:pointer;
}
.scr-add-filter-btn:hover { border-color:var(--blue,#3B82F6); color:var(--blue,#3B82F6); }
/* ── Filter modal ── */
.scr-filter-modal {
  position:fixed; inset:0; background:rgba(0,0,0,.6); z-index:900;
  display:flex; align-items:center; justify-content:center;
}
.scr-filter-modal-box {
  background:var(--panel,#1E293B); border:1px solid var(--border,rgba(255,255,255,.12));
  border-radius:12px; padding:20px 24px; min-width:320px; max-width:400px;
}
.scr-filter-modal-box h4 { margin:0 0 14px; font-size:14px; color:var(--text-bold,#F8FAFC); }
.scr-filter-modal-box select, .scr-filter-modal-box input {
  width:100%; padding:6px 10px; border-radius:6px; font-size:13px; margin-bottom:10px;
  background:var(--bg,#0F172A); border:1px solid var(--border,rgba(255,255,255,.15));
  color:var(--text-bold,#F8FAFC);
}
.scr-modal-btns { display:flex; gap:8px; justify-content:flex-end; margin-top:4px; }
.scr-modal-ok { padding:5px 16px; border-radius:6px; background:var(--blue,#3B82F6); color:#fff; border:none; cursor:pointer; }
.scr-modal-cancel { padding:5px 14px; border-radius:6px; background:none; border:1px solid var(--border); color:var(--text-dim); cursor:pointer; }
/* ── Column sets ── */
.scr-colset-bar {
  display:flex; gap:2px; padding:0 14px;
  border-bottom:1px solid var(--border,rgba(255,255,255,.08));
}
.scr-colset-tab {
  padding:7px 14px; font-size:12px; font-weight:500;
  color:var(--text-dim,#64748B); background:none;
  border:none; border-bottom:2px solid transparent;
  cursor:pointer; margin-bottom:-1px;
}
.scr-colset-tab.active { color:var(--blue,#3B82F6); border-bottom-color:var(--blue,#3B82F6); }
/* ── Preset pills ── */
.scr-presets { display:flex; gap:6px; flex-wrap:wrap; padding:8px 14px 0; }
.scr-preset-btn {
  padding:3px 11px; font-size:11px; border-radius:20px;
  border:1px solid var(--border,rgba(255,255,255,.12));
  background:none; color:var(--text-dim); cursor:pointer;
}
.scr-preset-btn:hover { border-color:var(--blue,#3B82F6); color:var(--blue,#3B82F6); }
/* ── Results area ── */
.scr-results { flex:1; overflow:auto; padding:10px 14px; }
.scr-meta { font-size:11px; color:var(--text-dim); margin-bottom:8px; }
.scr-count { font-size:12px; color:var(--text-dim); margin-bottom:4px; }
.data-table { width:100%; border-collapse:collapse; font-size:12px; }
.data-table th {
  padding:6px 10px; text-align:right; font-size:10px; font-weight:600;
  text-transform:uppercase; letter-spacing:.05em; color:var(--text-dim);
  border-bottom:1px solid var(--border,rgba(255,255,255,.08));
  white-space:nowrap; cursor:pointer; user-select:none;
}
.data-table th.left { text-align:left; }
.data-table th.sort-active { color:var(--blue,#3B82F6); }
.data-table td { padding:6px 10px; text-align:right; border-bottom:1px solid rgba(255,255,255,.03); }
.data-table td.left { text-align:left; }
.data-table tr:hover td { background:rgba(255,255,255,.025); cursor:pointer; }
.data-table .pos { color:var(--green,#10B981); }
.data-table .neg { color:var(--red,#EF4444); }
.data-table .sym-cell { font-weight:600; color:var(--text-bold,#F8FAFC); }
.scr-actions { display:flex; gap:4px; justify-content:flex-end; }
.btn-sm {
  padding:2px 8px; font-size:11px; border-radius:4px; border:none; cursor:pointer;
  background:rgba(255,255,255,.06); color:var(--text-dim);
}
.btn-sm:hover { background:rgba(59,130,246,.2); color:var(--blue,#3B82F6); }
.empty-state { padding:40px; text-align:center; color:var(--text-dim); }
.alert-tag {
  display:inline-block; padding:1px 6px; border-radius:10px; font-size:10px;
  background:rgba(59,130,246,.12); color:var(--blue,#3B82F6); margin-right:2px;
}
</style>

<div class="scr-wrap">
  <!-- Toolbar -->
  <div class="scr-toolbar">
    <div class="scr-universe-btns">
      ${(['BIST30','BIST100','CRYPTO','ALL'] as Universe[]).map(u =>
        `<button class="scr-uni-btn${u === this.universe ? ' active' : ''}" data-universe="${u}">
          ${u === 'ALL' ? 'Tümü' : u}
        </button>`).join('')}
    </div>
    <div class="scr-divider"></div>
    <button class="scr-scan-btn" id="scan-btn">🔍 Tara</button>
    <button class="scr-export-btn" id="export-btn">↓ CSV</button>
  </div>

  <!-- Hızlı filtreler -->
  <div class="scr-quick-filters">
    <span class="scr-quick-label">Hızlı:</span>
    ${this.quickFilterBtns()}
  </div>

  <!-- Özel filtreler -->
  <div class="scr-custom-filters" id="custom-filters-row">
    ${this.customFilterChips()}
    <button class="scr-add-filter-btn" id="add-filter-btn">+ Filtre Ekle</button>
  </div>

  <!-- Preset'ler -->
  ${this.presets.length ? `<div class="scr-presets">${this.presetPills()}</div>` : ''}

  <!-- Kolon seti sekmeleri -->
  <div class="scr-colset-bar">
    ${(['technical','performance','valuation','all'] as ColSet[]).map(s =>
      `<button class="scr-colset-tab${s === this.colSet ? ' active' : ''}" data-colset="${s}">
        ${{ technical:'Teknik', performance:'Performans', valuation:'Değerleme', all:'Tümü' }[s]}
      </button>`).join('')}
  </div>

  <!-- Sonuçlar -->
  <div class="scr-results" id="screener-results">
    <div class="empty-state">Evren ve filtrelerinizi seçip <strong>Tara</strong> butonuna tıklayın.</div>
  </div>
</div>`;

    this.bindEvents();
  }

  private quickFilterBtns(): string {
    const opts: { id: ScreenerFilter; label: string }[] = [
      { id: 'rsi_oversold',   label: 'RSI Aşırı Satım (<30)' },
      { id: 'rsi_overbought', label: 'RSI Aşırı Alım (>70)'  },
      { id: 'ema_bullish',    label: 'EMA Yükseliş'          },
      { id: 'bb_lower',       label: 'BB Alt Bant'           },
      { id: 'high_volume',    label: 'Yüksek Hacim'          },
    ];
    return opts.map(f =>
      `<button class="filter-btn${this.quickFilters.has(f.id) ? ' active' : ''}" data-filter="${f.id}">${f.label}</button>`
    ).join('');
  }

  private customFilterChips(): string {
    return this.customFilters.map(f => {
      const colLabel = ALL_COLS.find(c => c.key === f.column)?.label ?? f.column;
      const opLabel  = { gt:'>',lt:'<',gte:'≥',lte:'≤',eq:'=',neq:'≠' }[f.op] ?? f.op;
      return `<span class="scr-filter-chip" data-fid="${f.id}">
        ${colLabel} ${opLabel} ${f.value}
        <span class="rm" data-remove="${f.id}">✕</span>
      </span>`;
    }).join('');
  }

  private presetPills(): string {
    return (this.presets as Array<Record<string, unknown>>).map(p =>
      `<button class="scr-preset-btn" data-preset='${JSON.stringify(p)}'>${String(p['name'] ?? '')}</button>`
    ).join('');
  }

  // ─── Olay bağlamaları ──────────────────────────────────────────────────────

  private bindEvents(): void {
    // Evren seçici
    this.container.querySelectorAll<HTMLButtonElement>('.scr-uni-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.universe = btn.dataset['universe'] as Universe;
        this.container.querySelectorAll('.scr-uni-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      });
    });

    // Hızlı filtreler
    this.container.querySelectorAll<HTMLButtonElement>('.filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const f = btn.dataset['filter'] as ScreenerFilter;
        if (this.quickFilters.has(f)) { this.quickFilters.delete(f); btn.classList.remove('active'); }
        else                          { this.quickFilters.add(f);    btn.classList.add('active');   }
      });
    });

    // Kolon seti sekmeleri
    this.container.querySelectorAll<HTMLButtonElement>('.scr-colset-tab').forEach(btn => {
      btn.addEventListener('click', () => {
        this.colSet = btn.dataset['colset'] as ColSet;
        this.container.querySelectorAll('.scr-colset-tab').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.renderResults();
      });
    });

    // Tara butonu
    this.container.querySelector('#scan-btn')?.addEventListener('click', () => this.scan());

    // CSV dışa aktar
    this.container.querySelector('#export-btn')?.addEventListener('click', () => this.exportCSV());

    // Filtre ekle
    this.container.querySelector('#add-filter-btn')?.addEventListener('click', () => this.showFilterModal());

    // Filtre chip kaldır (event delegation)
    this.container.querySelector('#custom-filters-row')?.addEventListener('click', (e) => {
      const rm = (e.target as HTMLElement).closest<HTMLElement>('[data-remove]');
      if (rm) {
        const id = rm.dataset['remove']!;
        this.customFilters = this.customFilters.filter(f => f.id !== id);
        this.refreshCustomFilterChips();
      }
    });

    // Preset'ler
    this.container.querySelectorAll<HTMLButtonElement>('.scr-preset-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const p = JSON.parse(btn.dataset['preset']!) as Record<string, unknown>;
        this.applyPreset(p);
      });
    });
  }

  // ─── Filtre modal ──────────────────────────────────────────────────────────

  private showFilterModal(): void {
    const modal = document.createElement('div');
    modal.className = 'scr-filter-modal';
    const colOptions = ALL_COLS
      .filter(c => !['symbol','name','sector'].includes(c.key))
      .map(c => `<option value="${c.key}">${c.label}</option>`)
      .join('');

    modal.innerHTML = `
      <div class="scr-filter-modal-box">
        <h4>Filtre Ekle</h4>
        <select id="fm-col">${colOptions}</select>
        <select id="fm-op">
          <option value="gt"> &gt; (büyüktür)</option>
          <option value="lt"> &lt; (küçüktür)</option>
          <option value="gte">≥ (büyük eşit)</option>
          <option value="lte">≤ (küçük eşit)</option>
          <option value="eq"> = (eşit)</option>
        </select>
        <input id="fm-val" type="number" placeholder="Değer" step="any">
        <div class="scr-modal-btns">
          <button class="scr-modal-cancel" id="fm-cancel">İptal</button>
          <button class="scr-modal-ok"     id="fm-ok">Ekle</button>
        </div>
      </div>`;

    document.body.appendChild(modal);

    modal.querySelector('#fm-cancel')!.addEventListener('click', () => modal.remove());
    modal.querySelector('#fm-ok')!.addEventListener('click', () => {
      const col = (modal.querySelector('#fm-col') as HTMLSelectElement).value;
      const op  = (modal.querySelector('#fm-op')  as HTMLSelectElement).value;
      const val = parseFloat((modal.querySelector('#fm-val') as HTMLInputElement).value);
      if (!isNaN(val)) {
        this.customFilters.push({ id: crypto.randomUUID(), column: col, op, value: val });
        this.refreshCustomFilterChips();
      }
      modal.remove();
    });
    modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });
  }

  private refreshCustomFilterChips(): void {
    const row = this.container.querySelector('#custom-filters-row');
    if (!row) return;
    row.innerHTML = this.customFilterChips()
      + '<button class="scr-add-filter-btn" id="add-filter-btn">+ Filtre Ekle</button>';
    row.querySelector('#add-filter-btn')?.addEventListener('click', () => this.showFilterModal());
    row.addEventListener('click', (e) => {
      const rm = (e.target as HTMLElement).closest<HTMLElement>('[data-remove]');
      if (rm) {
        this.customFilters = this.customFilters.filter(f => f.id !== rm.dataset['remove']);
        this.refreshCustomFilterChips();
      }
    });
  }

  // ─── Preset uygula ────────────────────────────────────────────────────────

  private applyPreset(p: Record<string, unknown>): void {
    if (p['universe']) this.universe = String(p['universe']) as Universe;
    if (p['sort_by'])  this.sortCol  = String(p['sort_by']);
    if (p['sort_dir']) this.sortDir  = String(p['sort_dir']) as 'asc' | 'desc';
    // Preset filtrelerini custom filtreler olarak ekle
    const pFilters = (p['filters'] as Array<Record<string, unknown>> | undefined) ?? [];
    pFilters.forEach(f => {
      this.customFilters.push({
        id: crypto.randomUUID(),
        column: String(f['column'] ?? ''),
        op:     String(f['op'] ?? 'gt'),
        value:  Number(f['value'] ?? 0),
      });
    });
    // Universe butonunu güncelle
    this.container.querySelectorAll<HTMLButtonElement>('.scr-uni-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset['universe'] === this.universe);
    });
    this.refreshCustomFilterChips();
    this.scan();
  }

  // ─── Tara ─────────────────────────────────────────────────────────────────

  async scan(): Promise<void> {
    if (this.isScanning) return;
    this.isScanning = true;

    const scanBtn = this.container.querySelector<HTMLButtonElement>('#scan-btn')!;
    const resultsEl = this.container.querySelector('#screener-results')!;
    scanBtn.disabled = true;
    scanBtn.textContent = '⏳ Taranıyor…';
    resultsEl.innerHTML = '<div class="empty-state">Taranıyor…</div>';

    try {
      const backendRows = await this.scanBackend();
      if (backendRows !== null) {
        this.rows = backendRows;
      } else {
        // Fallback: local cache
        this.rows = this.scanLocal();
        this.runMeta = null;
      }
      this.renderResults();
    } finally {
      this.isScanning = false;
      scanBtn.disabled = false;
      scanBtn.textContent = '🔍 Tara';
    }
  }

  private buildFilters(): Array<{ column: string; op: string; value: number | string }> {
    const out: Array<{ column: string; op: string; value: number | string }> = [];
    // Hızlı filtre → backend filtrelerine çevir
    for (const f of this.quickFilters) {
      if (f === 'rsi_oversold')   out.push({ column: 'rsi_14', op: 'lt', value: 30 });
      if (f === 'rsi_overbought') out.push({ column: 'rsi_14', op: 'gt', value: 70 });
      if (f === 'high_volume')    out.push({ column: 'volume', op: 'gt', value: 1 });
    }
    // Özel filtreler
    this.customFilters.forEach(f => out.push({ column: f.column, op: f.op, value: f.value }));
    return out;
  }

  private async scanBackend(): Promise<BackendRow[] | null> {
    try {
      const res = await fetch('/api/screener/run', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          market:   'BIST',
          universe: this.universe,
          filters:  this.buildFilters(),
          columns:  ['symbol','name','last_price','change_pct','volume','volume_avg_20d',
                     'distance_from_52w_high','rsi_14','market_cap','pe_ratio','sector'],
          sort_by:  this.sortCol === 'symbol' ? 'symbol' : this.sortCol,
          sort_dir: this.sortDir,
          limit:    200,
        }),
      });
      if (res.status === 401 || res.status === 403) {
        this.emptyMsg = 'Tarayıcı için giriş yapmanız gerekiyor.';
        return [];
      }
      if (!res.ok) return null;
      const data = await res.json() as {
        run_id?: string; created_at?: string;
        filters_hash?: string; data_snapshot_hash?: string;
        rows?: BackendRow[];
      };
      this.runMeta = {
        run_id:              data.run_id              ?? '',
        created_at:          data.created_at          ?? '',
        filters_hash:        data.filters_hash        ?? '',
        data_snapshot_hash:  data.data_snapshot_hash  ?? '',
      };
      return data.rows ?? [];
    } catch {
      return null;
    }
  }

  // ─── Local cache fallback ─────────────────────────────────────────────────

  private scanLocal(): BackendRow[] {
    const cache = this.getCache();
    const out: BackendRow[] = [];
    for (const symInfo of ALL_SYMBOLS) {
      const candles = cache.get(symInfo.symbol);
      if (!candles || candles.length < 30) continue;
      const inds  = computeIndicators(candles);
      const n     = candles.length;
      const last  = candles[n - 1]!;
      const prev  = candles[n - 2]!;
      const rsi   = lastValid(inds.rsi) ?? null;
      const vols  = candles.map(c => c.volume);
      const avgV  = SMA(vols, 20)[n - 1] ?? null;
      const chg   = prev.close > 0 ? ((last.close - prev.close) / prev.close) * 100 : null;
      const highs = candles.map(c => c.high);
      const h52   = Math.max(...highs);
      const dist52 = h52 > 0 ? ((last.close - h52) / h52) * 100 : null;

      const row: BackendRow = {
        symbol: symInfo.symbol,
        name:   symInfo.name,
        last_price: last.close,
        change_pct: chg,
        volume: last.volume,
        volume_avg_20d: avgV,
        distance_from_52w_high: dist52,
        rsi_14: rsi,
        market_cap: null,
        pe_ratio: null,
      };

      // Hızlı filtre kontrolü (local)
      if (this.quickFilters.size > 0) {
        let pass = false;
        if (this.quickFilters.has('rsi_oversold')   && rsi != null && rsi < 30)   pass = true;
        if (this.quickFilters.has('rsi_overbought')  && rsi != null && rsi > 70)   pass = true;
        if (this.quickFilters.has('high_volume') && last.volume > 0 && avgV != null && last.volume > avgV * 1.5) pass = true;
        if (!pass) continue;
      }
      out.push(row);
    }
    // Sırala
    out.sort((a, b) => {
      const av = a[this.sortCol as keyof BackendRow] as number | null;
      const bv = b[this.sortCol as keyof BackendRow] as number | null;
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      return this.sortDir === 'desc' ? (bv as number) - (av as number) : (av as number) - (bv as number);
    });
    return out;
  }

  // ─── Sonuç tablosu ────────────────────────────────────────────────────────

  private renderResults(): void {
    const el = this.container.querySelector('#screener-results');
    if (!el) return;

    if (this.rows.length === 0) {
      el.innerHTML = `<div class="empty-state">${this.emptyMsg}</div>`;
      return;
    }

    // Aktif kolon setine göre kolonları filtrele
    const cols = ALL_COLS.filter(c => c.sets.includes(this.colSet));

    // Sıralanmış satırlar
    const sorted = this.sortedRows();

    const metaStr = this.runMeta
      ? `Run ${this.runMeta['run_id'].slice(0,8)} · Snapshot ${this.runMeta['data_snapshot_hash'].slice(0,8)}`
      : 'Yerel cache taraması';

    el.innerHTML = `
      <div class="scr-count">${sorted.length} sembol bulundu</div>
      <div class="scr-meta">${metaStr}</div>
      <table class="data-table">
        <thead><tr>
          ${cols.map(c => this.thHTML(c)).join('')}
          <th class="left">İşlem</th>
        </tr></thead>
        <tbody>
          ${sorted.map(row => this.rowHTML(row, cols)).join('')}
        </tbody>
      </table>`;

    // Sıralama
    el.querySelectorAll<HTMLElement>('[data-sortcol]').forEach(th => {
      th.addEventListener('click', () => {
        const col = th.dataset['sortcol']!;
        if (this.sortCol === col) {
          this.sortDir = this.sortDir === 'asc' ? 'desc' : 'asc';
        } else {
          this.sortCol = col;
          this.sortDir = 'desc';
        }
        this.renderResults();
      });
    });

    // Satıra tıkla → 360 sayfası
    el.querySelectorAll<HTMLTableRowElement>('tr[data-sym]').forEach(tr => {
      tr.addEventListener('click', (e) => {
        if ((e.target as HTMLElement).closest('button')) return;
        window.location.href = `/terminal/symbol/BIST/${tr.dataset['sym']}`;
      });
    });

    // Grafik / Backtest butonları
    el.querySelectorAll<HTMLButtonElement>('.screener-chart').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        window.dispatchEvent(new CustomEvent('openSymbolOnChart', { detail: { symbol: btn.dataset['chart'] } }));
      });
    });
    el.querySelectorAll<HTMLButtonElement>('.screener-backtest').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        window.dispatchEvent(new CustomEvent('addSymbolToBacktest', { detail: { symbol: btn.dataset['backtest'] } }));
      });
    });
  }

  private thHTML(col: ColDef): string {
    const active = this.sortCol === col.key;
    const arrow  = active ? (this.sortDir === 'asc' ? ' ▲' : ' ▼') : '';
    const cls    = [col.align === 'left' ? 'left' : '', active ? 'sort-active' : ''].filter(Boolean).join(' ');
    return `<th class="${cls}" data-sortcol="${col.key}" title="Sırala: ${col.label}">${col.label}${arrow}</th>`;
  }

  private rowHTML(row: BackendRow, cols: ColDef[]): string {
    const cells = cols.map(col => {
      const rawVal = row[col.key as keyof BackendRow];
      const formatted = col.fmt ? col.fmt(rawVal, row) : String(rawVal ?? '—');
      const cls = [col.align === 'left' ? 'left' : '', col.key === 'symbol' ? 'sym-cell' : '', col.cls ? col.cls(rawVal, row) : ''].filter(Boolean).join(' ');
      return `<td class="${cls}">${formatted}</td>`;
    }).join('');

    const volBadge = row.volume && row.volume_avg_20d && row.volume > row.volume_avg_20d * 1.5
      ? '<span class="alert-tag">⚡Hacim</span>'
      : '';
    const rsiBadge = row.rsi_14 != null
      ? (row.rsi_14 < 30 ? '<span class="alert-tag">RSI↓</span>' : row.rsi_14 > 70 ? '<span class="alert-tag">RSI↑</span>' : '')
      : '';

    return `
      <tr data-sym="${row.symbol}">
        ${cells}
        <td class="left">
          <div class="scr-actions">
            ${volBadge}${rsiBadge}
            <button class="btn-sm screener-chart"    data-chart="${row.symbol}"    title="Grafikte aç">📈</button>
            <button class="btn-sm screener-backtest" data-backtest="${row.symbol}" title="Backtest">▶</button>
          </div>
        </td>
      </tr>`;
  }

  private sortedRows(): BackendRow[] {
    const dir = this.sortDir === 'asc' ? 1 : -1;
    return [...this.rows].sort((a, b) => {
      const av = a[this.sortCol as keyof BackendRow];
      const bv = b[this.sortCol as keyof BackendRow];
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === 'string' && typeof bv === 'string') return dir * av.localeCompare(bv);
      return dir * ((av as number) - (bv as number));
    });
  }

  // ─── CSV dışa aktarma ────────────────────────────────────────────────────

  private exportCSV(): void {
    if (this.rows.length === 0) return;
    const cols = ALL_COLS.filter(c => c.sets.includes(this.colSet));
    const header = cols.map(c => c.label).join(',');
    const rowsCsv = this.sortedRows().map(row =>
      cols.map(col => {
        const v = row[col.key as keyof BackendRow];
        return v == null ? '' : String(v).replace(/,/g, '.');
      }).join(',')
    ).join('\n');
    const csv = header + '\n' + rowsCsv;
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `screener_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
  }
}
