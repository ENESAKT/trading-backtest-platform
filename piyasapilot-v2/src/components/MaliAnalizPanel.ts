import { TR, formatNumber, formatPct } from '../constants/tr.js';
import type { MaliAnalizResponse } from '../types.js';

type MaliTabId = 'summary' | 'statements' | 'ratios' | 'metric-history' | 'source';

export class MaliAnalizPanel {
  private container: HTMLElement;
  private currentSymbol: string = 'THYAO.IS';
  private data: MaliAnalizResponse | null = null;
  private isLoading: boolean = false;
  private errorMessage: string | null = null;
  private activeTab: MaliTabId = 'summary';

  private headerEl!: HTMLElement;
  private titleEl!: HTMLElement;
  private contentEl!: HTMLElement;
  private searchInput!: HTMLInputElement;

  constructor(container: HTMLElement) {
    this.container = container;
    this.renderLayout();
    this.bindEvents();
    this.loadData(this.currentSymbol);
  }

  private renderLayout(): void {
    this.container.innerHTML = '';
    
    // Header
    this.headerEl = document.createElement('div');
    this.headerEl.className = 'mali-analiz-header';

    this.titleEl = document.createElement('div');
    this.titleEl.className = 'mali-title-block';
    this.titleEl.innerHTML = `
      <div class="mali-title-main">Mali Analiz</div>
      <div class="mali-title-sub">THYAO</div>
    `;
    
    this.searchInput = document.createElement('input');
    this.searchInput.type = 'text';
    this.searchInput.placeholder = TR.FIN_SEARCH_PLACEHOLDER;
    this.searchInput.className = 'mali-search-input';
    this.searchInput.value = this.currentSymbol;

    const searchBtn = document.createElement('button');
    searchBtn.className = 'btn';
    searchBtn.textContent = 'Ara';
    searchBtn.addEventListener('click', () => {
      const val = this.searchInput.value.trim().toUpperCase();
      if (val) this.loadData(val);
    });

    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'mali-header-actions';
    
    const openChartBtn = document.createElement('button');
    openChartBtn.className = 'btn btn-outline';
    openChartBtn.textContent = TR.FIN_OPEN_CHART;
    openChartBtn.addEventListener('click', () => {
      this.container.dispatchEvent(new CustomEvent('openSymbolOnChart', {
        bubbles: true,
        detail: { symbol: this.currentSymbol }
      }));
    });

    const addBacktestBtn = document.createElement('button');
    addBacktestBtn.className = 'btn btn-outline';
    addBacktestBtn.textContent = TR.FIN_ADD_BACKTEST;
    addBacktestBtn.addEventListener('click', () => {
      this.container.dispatchEvent(new CustomEvent('addSymbolToBacktest', {
        bubbles: true,
        detail: { symbol: this.currentSymbol }
      }));
    });

    const searchGroup = document.createElement('div');
    searchGroup.className = 'mali-search-group';
    searchGroup.appendChild(this.searchInput);
    searchGroup.appendChild(searchBtn);

    actionsDiv.appendChild(openChartBtn);
    actionsDiv.appendChild(addBacktestBtn);

    this.headerEl.appendChild(this.titleEl);
    this.headerEl.appendChild(searchGroup);
    this.headerEl.appendChild(actionsDiv);

    // Content
    this.contentEl = document.createElement('div');
    this.contentEl.className = 'mali-analiz-content';

    this.container.appendChild(this.headerEl);
    this.container.appendChild(this.contentEl);
  }

  private bindEvents(): void {
    this.searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const val = this.searchInput.value.trim().toUpperCase();
        if (val) this.loadData(val);
      }
    });
  }

  public async loadData(symbol: string): Promise<void> {
    this.currentSymbol = symbol;
    this.searchInput.value = symbol;
    this.isLoading = true;
    this.errorMessage = null;
    this.renderContent();

    try {
      const response = await fetch(`/api/mali-analiz/${symbol}`);
      if (!response.ok) {
        throw new Error('API Hatası');
      }
      const data = await response.json() as MaliAnalizResponse;
      this.data = data;
      this.currentSymbol = data.symbol;
      this.searchInput.value = data.symbol;
    } catch (err) {
      console.warn('Mali Analiz fetch hatası:', err);
      this.errorMessage = 'Mali analiz servisine ulaşılamadı.';
      this.data = {
        symbol: symbol,
        company_name: null,
        periods: [],
        source_status: { source: 'none', status: 'error', fetched_at: null, cache_hit: false, stale: false, error: 'Veri çekilemedi' },
        financial_statements: [],
        ratios: [],
        warnings: ['Veri çekilemedi veya API bulunamadı.']
      };
    } finally {
      this.isLoading = false;
      this.renderHeaderTitle();
      this.renderContent();
    }
  }

  private renderContent(): void {
    this.contentEl.innerHTML = '';
    this.renderHeaderTitle();

    if (this.isLoading) {
      this.contentEl.innerHTML = `<div class="mali-loading"><div class="spinner"></div> ${TR.LOADING}</div>`;
      return;
    }

    if (this.errorMessage) {
      this.contentEl.innerHTML = `
        <div class="mali-empty-state">
          <h2>Veri alınamadı</h2>
          <p>${this.escapeHtml(this.errorMessage)}</p>
        </div>
      `;
      return;
    }

    if (!this.data) return;

    const hasStatements = this.data.financial_statements.length > 0;
    const hasRatios = this.data.ratios.length > 0;
    const hasFinancialData = hasStatements || hasRatios;
    const tabs = this.renderTabs();
    this.contentEl.appendChild(tabs);

    const section = document.createElement('section');
    section.className = 'mali-section';

    if (this.activeTab === 'summary') {
      section.appendChild(this.renderSummarySection(hasFinancialData, hasRatios));
    } else if (this.activeTab === 'statements') {
      section.appendChild(hasStatements ? this.renderStatementsSection() : this.renderEmptyState('Finansal tablolar henüz bağlı değil', 'KAP finansal tablo kaynağı bağlandığında bilanço, gelir tablosu ve nakit akımı burada görünecek.'));
    } else if (this.activeTab === 'ratios') {
      section.appendChild(hasRatios ? this.renderRatiosSection() : this.renderEmptyState('Oranlar henüz hesaplanmadı', 'Finansal tablo verisi bağlandığında karlılık, likidite ve borçluluk oranları burada yer alacak.'));
    } else if (this.activeTab === 'metric-history') {
      section.appendChild(this.renderEmptyState('Metrik geçmişi henüz bağlı değil', 'Net kar, ROE veya marj gibi metriklerin dönemsel serileri finansal veri kaynağı bağlandığında görünecek.'));
    } else {
      section.appendChild(this.renderSourceSection());
    }

    this.contentEl.appendChild(section);
  }

  private renderTabs(): HTMLElement {
    const tabs = document.createElement('div');
    tabs.className = 'mali-tabs';
    const items: Array<{ id: MaliTabId; label: string }> = [
      { id: 'summary', label: 'Şirket Özeti' },
      { id: 'statements', label: 'Finansal Tablolar' },
      { id: 'ratios', label: 'Oranlar' },
      { id: 'metric-history', label: 'Metrik Geçmişi' },
      { id: 'source', label: 'Kaynak Durumu' },
    ];
    for (const item of items) {
      const button = document.createElement('button');
      button.className = `mali-tab-button${this.activeTab === item.id ? ' active' : ''}`;
      button.type = 'button';
      button.textContent = item.label;
      button.addEventListener('click', () => {
        this.activeTab = item.id;
        this.renderContent();
      });
      tabs.appendChild(button);
    }
    return tabs;
  }

  private renderSummarySection(hasFinancialData: boolean, hasRatios: boolean): HTMLElement {
    const card = document.createElement('div');
    card.className = 'mali-card summary-card';
    const sourceStatusStr = this.data!.source_status.status;
    const sourceText = this.statusText(sourceStatusStr);

    let html = `
      <div class="summary-header">
        <div class="summary-title-row">
          <h2>${this.escapeHtml(this.data!.company_name || 'Finansal veri henüz bağlı değil')}</h2>
          <span class="mali-symbol-badge">${this.escapeHtml(this.data!.symbol)}</span>
          <span class="badge status-${sourceStatusStr}">${this.escapeHtml(sourceText)}</span>
        </div>
      </div>
      <div class="mali-source-grid">
        <div><span>Sembol</span><strong>${this.escapeHtml(this.data!.symbol)}</strong></div>
        ${this.data!.company_name ? `<div><span>Şirket</span><strong>${this.escapeHtml(this.data!.company_name)}</strong></div>` : ''}
        <div><span>Kaynak</span><strong>${this.escapeHtml(this.data!.source_status.source)}</strong></div>
        <div><span>Durum</span><strong>${this.escapeHtml(sourceText)}</strong></div>
      </div>
    `;

    if (!hasFinancialData) {
      html += this.emptyStateHtml('Finansal veri henüz bağlı değil', 'Bu şirket için KAP/finansal tablo kaynağı bağlandığında oranlar, dönemler ve tablolar burada görünecek.');
    } else if (hasRatios) {
      html += `<div class="summary-grid">`;
      for (const r of this.data!.ratios.slice(0, 6)) {
        html += `
          <div class="ratio-box">
            <div class="ratio-label">${this.escapeHtml(r.name)}</div>
            <div class="ratio-value">${this.formatValue(r.value, r.format)}</div>
          </div>
        `;
      }
      html += `</div>`;
    }

    html += this.warningListHtml();
    card.innerHTML = html;
    return card;
  }

  private renderStatementsSection(): HTMLElement {
    const wrapper = document.createElement('div');
    wrapper.className = 'mali-main-row';
    const leftCol = document.createElement('div');
    leftCol.className = 'mali-left-col';

    for (const stmt of this.data!.financial_statements) {
      if (!stmt.rows.length) continue;
      const stmtCard = document.createElement('div');
      stmtCard.className = 'mali-card stmt-card';
      stmtCard.innerHTML = `<h3>${this.escapeHtml(stmt.title)}</h3>`;
      const tableWrapper = document.createElement('div');
      tableWrapper.className = 'mali-table-wrapper';
      const table = document.createElement('table');
      table.className = 'mali-table stmt-table';
      let thead = `<thead><tr><th>Kalem</th>`;
      for (const p of this.data!.periods) {
        thead += `<th>${this.escapeHtml(p)}</th>`;
      }
      thead += `</tr></thead>`;
      let tbody = `<tbody>`;
      for (const row of stmt.rows) {
        tbody += `<tr><td>${this.escapeHtml(row.label)}</td>`;
        for (const val of row.values) {
          tbody += `<td class="val-num">${this.formatCompactNumber(val)}</td>`;
        }
        tbody += `</tr>`;
      }
      tbody += `</tbody>`;
      table.innerHTML = thead + tbody;
      tableWrapper.appendChild(table);
      stmtCard.appendChild(tableWrapper);
      leftCol.appendChild(stmtCard);
    }

    wrapper.appendChild(leftCol);
    return wrapper;
  }

  private renderRatiosSection(): HTMLElement {
    const ratiosCard = document.createElement('div');
    ratiosCard.className = 'mali-card ratios-card';
    ratiosCard.innerHTML = `<h3>${TR.FIN_RATIOS}</h3>`;
    const table = document.createElement('table');
    table.className = 'mali-table';
    let html = `<thead><tr><th>Oran</th><th>Değer</th></tr></thead><tbody>`;
    for (const r of this.data!.ratios) {
      html += `<tr><td>${this.escapeHtml(r.name)}</td><td class="val-num">${this.formatValue(r.value, r.format)}</td></tr>`;
    }
    html += `</tbody>`;
    table.innerHTML = html;
    ratiosCard.appendChild(table);
    return ratiosCard;
  }

  private renderSourceSection(): HTMLElement {
    const card = document.createElement('div');
    card.className = 'mali-card';
    const status = this.data!.source_status;
    card.innerHTML = `
      <h3>Kaynak Durumu</h3>
      <div class="mali-source-grid">
        <div><span>Source</span><strong>${this.escapeHtml(status.source)}</strong></div>
        <div><span>Status</span><strong>${this.escapeHtml(status.status)}</strong></div>
        <div><span>Cache hit</span><strong>${status.cache_hit ? 'Evet' : 'Hayır'}</strong></div>
        <div><span>Stale</span><strong>${status.stale ? 'Evet' : 'Hayır'}</strong></div>
        <div><span>Error</span><strong>${this.escapeHtml(status.error || '-')}</strong></div>
      </div>
      ${this.warningListHtml()}
    `;
    return card;
  }

  private renderEmptyState(title: string, description: string): HTMLElement {
    const el = document.createElement('div');
    el.className = 'mali-card';
    el.innerHTML = this.emptyStateHtml(title, description);
    return el;
  }

  private emptyStateHtml(title: string, description: string): string {
    return `
      <div class="mali-empty-state mali-empty-state-inline">
        <h2>${this.escapeHtml(title)}</h2>
        <p>${this.escapeHtml(description)}</p>
      </div>
    `;
  }

  private warningListHtml(): string {
    if (!this.data?.warnings?.length) return '';
    return `<ul class="mali-warning-list">${this.data.warnings.map(w => `<li>${this.escapeHtml(w)}</li>`).join('')}</ul>`;
  }

  private statusText(status: string): string {
    const statusLabels: Record<string, string> = {
      connected: TR.FIN_SOURCE_CONNECTED,
      mock: TR.FIN_SOURCE_MOCK,
      error: TR.FIN_SOURCE_ERROR,
      empty: TR.FIN_SOURCE_EMPTY,
      metadata_only: 'Metadata hazır',
      not_configured: 'Kaynak bağlı değil',
    };
    return statusLabels[status] || status;
  }

  private renderHeaderTitle(): void {
    if (!this.titleEl) return;
    const symbol = this.data?.symbol || this.currentSymbol;
    const companyName = this.data?.company_name;
    this.titleEl.innerHTML = `
      <div class="mali-title-main">${this.escapeHtml(companyName || 'Mali Analiz')}</div>
      <div class="mali-title-sub">${this.escapeHtml(symbol)}</div>
    `;
  }

  private escapeHtml(value: string): string {
    return value.replace(/[&<>"']/g, (char) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;',
    }[char] || char));
  }

  private formatValue(val: number | null, format?: 'pct' | 'num' | 'currency'): string {
    if (val === null || val === undefined || isNaN(val)) return '-';
    if (format === 'pct') return formatPct(val);
    if (format === 'currency') return formatNumber(val) + ' ₺';
    return formatNumber(val);
  }

  private formatCompactNumber(val: number | null): string {
    if (val === null || val === undefined || isNaN(val)) return '-';
    if (val === 0) return '0';
    
    const absVal = Math.abs(val);
    if (absVal >= 1_000_000_000) {
      return (val / 1_000_000_000).toFixed(1) + 'B';
    }
    if (absVal >= 1_000_000) {
      return (val / 1_000_000).toFixed(1) + 'M';
    }
    if (absVal >= 1000) {
      return (val / 1000).toFixed(1) + 'K';
    }
    return formatNumber(val, 0);
  }
}
