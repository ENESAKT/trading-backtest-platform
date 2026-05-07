/**
 * MaliAnalizPanel — Fastweb / Yaşar Erdinç tarzı finansal analiz paneli.
 *
 * Sekmeler: Özet + Direktifler | Bilanço | Gelir Tablosu | Nakit Akışı | Oranlar
 * Özellikler:
 *   - Startup'ta otomatik veri kontrolü
 *   - Manuel "Yenile" butonu (tek sembol veya tüm BIST 30)
 *   - Yeni açıklanan bilançolar tablosu
 *   - Direktif / uyarı kartları (yüksek borç, ucuz değerleme vb.)
 *   - Tüm tablolar: dönem × kalem pivot
 */

type TabId = 'summary' | 'balance' | 'income' | 'cashflow' | 'ratios';

interface FetchStatus { status: string; last_period?: string; fetched_at?: string; periods_fetched?: number }
interface UniverseSymbol { symbol: string; name: string; fetch_status: FetchStatus }
interface Alert { id: number; symbol: string; alert_type: string; title: string; body: string; severity: string; period: string; metric_key: string; metric_value: number; created_at: string; is_read: boolean }
interface RatioRow { key: string; name: string; value: number | null; unit: string; category: string; period: string }
interface TableRow { row_index: number; label: string; values: Record<string, number | null> }

const API = '/api/mali-analiz';

const SEVERITY_BADGE: Record<string, string> = {
  danger:  'badge-danger',
  warning: 'badge-warning',
  success: 'badge-success',
  info:    'badge-info',
};

const CATEGORY_LABEL: Record<string, string> = {
  deger:    'Değerleme',
  karlilik: 'Karlılık',
  buyume:   'Büyüme',
  borc:     'Borç / Kaldıraç',
  nakit:    'Nakit Akışı',
  likidite: 'Likidite',
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
  if (val === null) return '';
  // Borç oranları için ters renk
  if (['net_borc_ebitda', 'borc_ozkaynak'].includes(key)) {
    return val > 3 ? 'val-danger' : val > 1.5 ? 'val-warn' : 'val-good';
  }
  if (unit === '%' || key.includes('buyume') || key.includes('marji') || key === 'roe' || key === 'roa') {
    return val > 15 ? 'val-good' : val > 0 ? 'val-neutral' : 'val-danger';
  }
  if (key === 'fk') return val < 6 ? 'val-good' : val < 15 ? 'val-neutral' : 'val-warn';
  if (key === 'pd_dd') return val < 1 ? 'val-good' : val < 3 ? 'val-neutral' : 'val-warn';
  return '';
}

export class MaliAnalizPanel {
  private container: HTMLElement;
  private activeTab: TabId = 'summary';
  private currentSymbol = 'THYAO';
  private universe: UniverseSymbol[] = [];
  private universeQuery = '';
  private refreshing = false;

  // DOM refs
  private titleEl!: HTMLElement;
  private tabsEl!: HTMLElement;
  private bodyEl!: HTMLElement;
  private statusBadgeEl!: HTMLElement;
  private refreshBtnEl!: HTMLButtonElement;
  private refreshAllBtnEl!: HTMLButtonElement;

  constructor(container: HTMLElement) {
    this.container = container;
    this.render();
    this.loadUniverse();
    this.loadTab();
  }

  // ── Layout ─────────────────────────────────────────────────────────────────

  private render(): void {
    this.container.innerHTML = `
      <div class="ma-root">
        <div class="ma-sidebar" id="ma-sidebar">
          <div class="ma-sidebar-search">
            <input type="text" placeholder="Sembol ara…" id="ma-sym-search" />
          </div>
          <div class="ma-universe-list" id="ma-universe-list">
            <div class="ma-loading">Yükleniyor…</div>
          </div>
        </div>
        <div class="ma-main">
          <div class="ma-topbar">
            <div class="ma-symbol-title" id="ma-title">
              <span class="ma-sym-code">${this.currentSymbol}</span>
            </div>
            <div class="ma-topbar-actions">
              <span class="ma-status-badge" id="ma-status-badge"></span>
              <button class="btn-sm btn-primary" id="ma-refresh-btn" title="Seçili sembolü güncelle">⟳ Yenile</button>
              <button class="btn-sm btn-ghost" id="ma-refresh-all-btn" title="Tüm BIST 30'u güncelle">⟳ BIST 30</button>
            </div>
          </div>
          <div class="ma-tabs" id="ma-tabs">
            <button class="ma-tab active" data-tab="summary">Özet</button>
            <button class="ma-tab" data-tab="balance">Bilanço</button>
            <button class="ma-tab" data-tab="income">Gelir</button>
            <button class="ma-tab" data-tab="cashflow">Nakit</button>
            <button class="ma-tab" data-tab="ratios">Oranlar</button>
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

    this.tabsEl.addEventListener('click', (e) => {
      const btn = (e.target as HTMLElement).closest('.ma-tab') as HTMLElement | null;
      if (!btn) return;
      const tab = btn.dataset.tab as TabId;
      if (tab) this.switchTab(tab);
    });

    this.refreshBtnEl.addEventListener('click', () => this.refreshSymbol());
    this.refreshAllBtnEl.addEventListener('click', () => this.refreshAll());

    const searchInput = this.container.querySelector('#ma-sym-search') as HTMLInputElement;
    searchInput.addEventListener('input', () => {
      this.universeQuery = searchInput.value.toLowerCase();
      this.renderUniverseList();
    });
  }

  // ── Universe sidebar ───────────────────────────────────────────────────────

  private async loadUniverse(): Promise<void> {
    try {
      const resp = await fetch(`${API}/universe?scope=bist30`);
      const data = await resp.json();
      this.universe = data.symbols || [];
      this.renderUniverseList();
    } catch {
      this.universe = [];
    }
  }

  private renderUniverseList(): void {
    const list = this.container.querySelector('#ma-universe-list')!;
    const filtered = this.universe.filter(s =>
      s.symbol.toLowerCase().includes(this.universeQuery) ||
      s.name.toLowerCase().includes(this.universeQuery)
    );
    if (!filtered.length) {
      list.innerHTML = '<div class="ma-empty">Sonuç yok</div>';
      return;
    }
    list.innerHTML = filtered.map(s => {
      const fs = s.fetch_status;
      const dot = fs.status === 'ok' ? '●' : fs.status === 'no_data' ? '○' : '◐';
      const dotCls = fs.status === 'ok' ? 'dot-ok' : fs.status === 'no_data' ? 'dot-empty' : 'dot-partial';
      const active = s.symbol === this.currentSymbol ? ' active' : '';
      return `<div class="ma-sym-item${active}" data-symbol="${s.symbol}">
        <span class="ma-sym-dot ${dotCls}">${dot}</span>
        <div class="ma-sym-info">
          <span class="ma-sym-code">${s.symbol}</span>
          <span class="ma-sym-name">${s.name}</span>
        </div>
        <span class="ma-sym-period">${fs.last_period || '—'}</span>
      </div>`;
    }).join('');

    list.querySelectorAll('.ma-sym-item').forEach(el => {
      el.addEventListener('click', () => {
        const sym = (el as HTMLElement).dataset.symbol!;
        this.selectSymbol(sym);
      });
    });
  }

  // ── Symbol selection ────────────────────────────────────────────────────────

  private selectSymbol(symbol: string): void {
    this.currentSymbol = symbol;
    this.titleEl.innerHTML = `<span class="ma-sym-code">${symbol}</span>
      <span class="ma-sym-fullname">${this.universe.find(s => s.symbol === symbol)?.name || ''}</span>`;
    this.renderUniverseList();
    this.loadTab();
  }

  /** Dışarıdan (örn. grafik panelinden) sembol yüklemek için public API. */
  loadData(symbol: string): void {
    this.selectSymbol(symbol);
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
    this.bodyEl.innerHTML = '<div class="ma-loading">Yükleniyor…</div>';
    switch (this.activeTab) {
      case 'summary':   this.loadSummary();   break;
      case 'balance':   this.loadStatement('balance-sheet', 'Bilanço');       break;
      case 'income':    this.loadStatement('income-stmt',   'Gelir Tablosu'); break;
      case 'cashflow':  this.loadStatement('cashflow',      'Nakit Akışı');   break;
      case 'ratios':    this.loadRatios();    break;
    }
  }

  // ── Özet sekme ─────────────────────────────────────────────────────────────

  private async loadSummary(): Promise<void> {
    try {
      const [summaryResp, alertsResp] = await Promise.all([
        fetch(`${API}/${this.currentSymbol}/summary`),
        fetch(`${API}/alerts?limit=30`),
      ]);
      const summary = await summaryResp.json();
      const alertsData = await alertsResp.json();
      const allAlerts: Alert[] = alertsData.alerts || [];

      const status = this.universe.find(s => s.symbol === this.currentSymbol)?.fetch_status;
      this.updateStatusBadge(status);

      this.bodyEl.innerHTML = `
        ${this.renderKeyRatiosBar(summary.key_ratios || [])}
        ${this.renderAlertsSection(summary.alerts || [], 'Bu Sembol Direktifleri')}
        ${this.renderNewDisclosuresTable(allAlerts)}
      `;

      this.bodyEl.querySelectorAll('.btn-mark-read').forEach(btn => {
        btn.addEventListener('click', () => {
          const ids = JSON.parse((btn as HTMLElement).dataset.ids || '[]');
          this.markRead(ids);
        });
      });
    } catch (e) {
      this.bodyEl.innerHTML = `<div class="ma-error">Özet yüklenemedi: ${e}</div>`;
    }
  }

  private renderKeyRatiosBar(ratios: RatioRow[]): string {
    if (!ratios.length) return '<div class="ma-empty-block">Oran verisi yok — önce "Yenile" butonuna basın.</div>';
    const cards = ratios.map(r => {
      const cls = colorClass(r.value, r.unit, r.key);
      return `<div class="ma-kpi-card">
        <div class="ma-kpi-name">${r.name}</div>
        <div class="ma-kpi-val ${cls}">${fmt(r.value, r.unit)}</div>
        <div class="ma-kpi-period">${r.period}</div>
      </div>`;
    }).join('');
    return `<div class="ma-kpi-bar">${cards}</div>`;
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

  private renderNewDisclosuresTable(alerts: Alert[]): string {
    const disclosures = alerts.filter(a => a.alert_type === 'new_period');
    const title = 'Son Açıklanan Bilançolar (BIST 30)';
    if (!disclosures.length) return `<div class="ma-section"><div class="ma-section-title">${title}</div><div class="ma-empty">Henüz veri çekilmedi.</div></div>`;

    const unreadIds = disclosures.filter(a => !a.is_read).map(a => a.id);
    const markBtn = unreadIds.length
      ? `<button class="btn-sm btn-ghost btn-mark-read" data-ids='${JSON.stringify(unreadIds)}'>Tümünü okundu işaretle</button>`
      : '';

    const rows = disclosures.map(a => `
      <tr class="${a.is_read ? '' : 'row-unread'}">
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

  // ── Tablo sekmeleri (bilanço / gelir / nakit) ──────────────────────────────

  private async loadStatement(endpoint: string, title: string): Promise<void> {
    try {
      const resp = await fetch(`${API}/${this.currentSymbol}/${endpoint}?limit=12`);
      const data = await resp.json();
      const periods: string[] = data.periods || [];
      const rows: TableRow[] = data.rows || [];

      if (!rows.length) {
        this.bodyEl.innerHTML = '<div class="ma-empty-block">Veri bulunamadı — "Yenile" ile veriyi çekin.</div>';
        return;
      }

      const headerCells = periods.map(p => `<th>${p}</th>`).join('');
      const bodyRows = rows.map(r => {
        const valueCells = periods.map(p => {
          const v = r.values[p];
          return `<td class="ma-num">${v !== null && v !== undefined ? fmtBig(v) : '—'}</td>`;
        }).join('');
        return `<tr><td class="ma-label">${r.label}</td>${valueCells}</tr>`;
      }).join('');

      this.bodyEl.innerHTML = `
        <div class="ma-table-header">
          <span class="ma-table-title">${title}</span>
          <span class="ma-table-source">Kaynak: borsapy / isyatirim</span>
        </div>
        <div class="ma-table-wrap">
          <table class="ma-table ma-financial-table">
            <thead><tr><th>Kalem</th>${headerCells}</tr></thead>
            <tbody>${bodyRows}</tbody>
          </table>
        </div>`;
    } catch (e) {
      this.bodyEl.innerHTML = `<div class="ma-error">Veri yüklenemedi: ${e}</div>`;
    }
  }

  // ── Oranlar sekme ───────────────────────────────────────────────────────────

  private async loadRatios(): Promise<void> {
    try {
      const resp = await fetch(`${API}/${this.currentSymbol}/ratios?limit=8`);
      const data = await resp.json();
      const ratios: RatioRow[] = data.ratios || [];
      const periods: string[] = data.periods || [];

      if (!ratios.length) {
        this.bodyEl.innerHTML = '<div class="ma-empty-block">Oran verisi yok — "Yenile" ile hesaplatın.</div>';
        return;
      }

      // Kategorilere göre grupla
      const byCategory: Record<string, RatioRow[]> = {};
      for (const r of ratios) {
        const cat = r.category || 'diger';
        if (!byCategory[cat]) byCategory[cat] = [];
        byCategory[cat].push(r);
      }

      // Dönem × oran pivot
      const ratiosByKey: Record<string, Record<string, RatioRow>> = {};
      const allKeys: string[] = [];
      for (const r of ratios) {
        if (!ratiosByKey[r.key]) { ratiosByKey[r.key] = {}; allKeys.push(r.key); }
        ratiosByKey[r.key][r.period] = r;
      }
      const uniqueKeys = [...new Set(allKeys)];

      const headerCells = periods.map(p => `<th>${p}</th>`).join('');
      const catOrder = ['deger', 'karlilik', 'buyume', 'borc', 'nakit', 'likidite'];
      let html = `
        <div class="ma-table-header">
          <span class="ma-table-title">Finansal Oranlar — ${this.currentSymbol}</span>
          <span class="ma-table-source">Son ${periods.length} çeyrek</span>
        </div>
        <div class="ma-table-wrap">
          <table class="ma-table ma-ratio-table">
            <thead><tr><th>Oran</th>${headerCells}</tr></thead>
            <tbody>`;

      const renderedCats = new Set<string>();
      for (const cat of catOrder) {
        const keysInCat = uniqueKeys.filter(k => ratiosByKey[k][periods[0]]?.category === cat);
        if (!keysInCat.length) continue;
        if (!renderedCats.has(cat)) {
          html += `<tr class="ma-ratio-cat-row"><td colspan="${periods.length + 1}">${CATEGORY_LABEL[cat] || cat}</td></tr>`;
          renderedCats.add(cat);
        }
        for (const key of keysInCat) {
          const sample = ratiosByKey[key][periods[0]];
          const cells = periods.map(p => {
            const r = ratiosByKey[key]?.[p];
            if (!r) return '<td>—</td>';
            const cls = colorClass(r.value, r.unit, r.key);
            return `<td class="ma-num ${cls}">${fmt(r.value, r.unit)}</td>`;
          }).join('');
          html += `<tr><td class="ma-ratio-name">${sample?.name || key}</td>${cells}</tr>`;
        }
      }

      html += '</tbody></table></div>';
      this.bodyEl.innerHTML = html;
    } catch (e) {
      this.bodyEl.innerHTML = `<div class="ma-error">Oranlar yüklenemedi: ${e}</div>`;
    }
  }

  // ── Refresh ─────────────────────────────────────────────────────────────────

  private async refreshSymbol(): Promise<void> {
    if (this.refreshing) return;
    this.refreshing = true;
    this.refreshBtnEl.disabled = true;
    this.refreshBtnEl.textContent = '⟳ İndiriliyor…';
    this.statusBadgeEl.textContent = 'Güncelleniyor…';
    try {
      const resp = await fetch(`${API}/${this.currentSymbol}/refresh`, { method: 'POST' });
      const data = await resp.json();
      if (data.status === 'ok') {
        this.statusBadgeEl.className = 'ma-status-badge badge-success';
        this.statusBadgeEl.textContent = '✓ Güncellendi';
      } else {
        this.statusBadgeEl.className = 'ma-status-badge badge-warning';
        this.statusBadgeEl.textContent = '⚠ ' + (data.status || 'Hata');
      }
      await this.loadUniverse();
      this.loadTab();
    } catch (e) {
      this.statusBadgeEl.textContent = '✗ Hata';
    } finally {
      this.refreshing = false;
      this.refreshBtnEl.disabled = false;
      this.refreshBtnEl.textContent = '⟳ Yenile';
    }
  }

  private async refreshAll(): Promise<void> {
    if (this.refreshing) return;
    if (!confirm('Tüm BIST 30 bilançoları güncelleniyor (~5 dk). Devam edilsin mi?')) return;
    this.refreshing = true;
    this.refreshAllBtnEl.disabled = true;
    this.refreshAllBtnEl.textContent = '⟳ BIST 30 indiriliyor…';
    try {
      const resp = await fetch(`${API}/refresh`, { method: 'POST' });
      const data = await resp.json();
      alert(`BIST 30 güncellendi: ${data.ok}/${data.triggered} başarılı.`);
      await this.loadUniverse();
      this.loadTab();
    } catch {
      alert('Güncelleme başarısız.');
    } finally {
      this.refreshing = false;
      this.refreshAllBtnEl.disabled = false;
      this.refreshAllBtnEl.textContent = '⟳ BIST 30';
    }
  }

  private async markRead(ids: number[]): Promise<void> {
    if (!ids.length) return;
    await fetch(`${API}/alerts/mark-read`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids }),
    });
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
      el.textContent = '○ Veri yok';
    } else {
      el.className = 'ma-status-badge badge-info';
      el.textContent = status.last_period || status.status;
    }
  }
}
