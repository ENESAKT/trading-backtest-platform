import { TR, formatNumber, formatPct } from '../constants/tr.js';
import type { MaliAnalizResponse } from '../types.js';

export class MaliAnalizPanel {
  private container: HTMLElement;
  private currentSymbol: string = 'THYAO.IS';
  private data: MaliAnalizResponse | null = null;
  private isLoading: boolean = false;

  private headerEl!: HTMLElement;
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
    this.renderContent();

    try {
      const response = await fetch(`/api/mali-analiz/${symbol}`);
      if (!response.ok) {
        throw new Error('API Hatası');
      }
      this.data = await response.json();
    } catch (err) {
      console.warn('Mali Analiz fetch hatası:', err);
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
      this.renderContent();
    }
  }

  private renderContent(): void {
    this.contentEl.innerHTML = '';

    if (this.isLoading) {
      this.contentEl.innerHTML = `<div class="mali-loading"><div class="spinner"></div> ${TR.LOADING}</div>`;
      return;
    }

    if (!this.data || this.data.source_status.status === 'empty' || (this.data.source_status.status === 'error' && this.data.financial_statements.length === 0)) {
      const msg = this.data?.warnings?.[0] || TR.FIN_NO_DATA;
      this.contentEl.innerHTML = `
        <div class="mali-empty-state">
          <div class="empty-icon">📊</div>
          <p>${msg}</p>
        </div>
      `;
      return;
    }

    // Render Summary Card
    const summaryCard = document.createElement('div');
    summaryCard.className = 'mali-card summary-card';
    
    const statusLabels: Record<string, string> = {
      connected: TR.FIN_SOURCE_CONNECTED,
      mock: TR.FIN_SOURCE_MOCK,
      error: TR.FIN_SOURCE_ERROR,
      empty: TR.FIN_SOURCE_EMPTY,
    };
    const sourceStatusStr = this.data.source_status.status;
    const sourceText = statusLabels[sourceStatusStr] || sourceStatusStr;

    let summaryHtml = `
      <div class="summary-header">
        <div class="summary-title-row">
          <h2>${this.data.company_name || this.data.symbol}</h2>
          <span class="mali-symbol-badge">${this.data.symbol}</span>
          <span class="badge status-${sourceStatusStr}">${sourceText}</span>
        </div>
      </div>
      <div class="summary-grid">
    `;

    // Take top ratios for summary
    const sumRatios = this.data.ratios.slice(0, 6);
    for (const r of sumRatios) {
      summaryHtml += `
        <div class="ratio-box">
          <div class="ratio-label">${r.name}</div>
          <div class="ratio-value">${this.formatValue(r.value, r.format)}</div>
        </div>
      `;
    }
    summaryHtml += `</div>`;
    
    if (this.data.warnings && this.data.warnings.length > 0) {
      summaryHtml += `<div class="mali-warnings">
        ${this.data.warnings.map(w => `<span class="warning-item">⚠️ ${w}</span>`).join('')}
      </div>`;
    }
    
    summaryCard.innerHTML = summaryHtml;
    this.contentEl.appendChild(summaryCard);

    // Main Layout: Left (Statements) - Right (Ratios)
    const mainRow = document.createElement('div');
    mainRow.className = 'mali-main-row';

    const leftCol = document.createElement('div');
    leftCol.className = 'mali-left-col';

    const rightCol = document.createElement('div');
    rightCol.className = 'mali-right-col';

    // Financial Statements
    for (const stmt of this.data.financial_statements) {
      const stmtCard = document.createElement('div');
      stmtCard.className = 'mali-card stmt-card';
      stmtCard.innerHTML = `<h3>${stmt.title}</h3>`;
      
      const tableWrapper = document.createElement('div');
      tableWrapper.className = 'mali-table-wrapper';
      
      const table = document.createElement('table');
      table.className = 'mali-table stmt-table';
      
      let thead = `<thead><tr><th>Kalem</th>`;
      for (const p of this.data.periods) {
        thead += `<th>${p}</th>`;
      }
      thead += `</tr></thead>`;
      
      let tbody = `<tbody>`;
      for (const row of stmt.rows) {
        tbody += `<tr><td>${row.label}</td>`;
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

    // Ratios Table (Right)
    if (this.data.ratios.length > 0) {
      const ratiosCard = document.createElement('div');
      ratiosCard.className = 'mali-card ratios-card';
      ratiosCard.innerHTML = `<h3>${TR.FIN_RATIOS}</h3>`;
      
      const table = document.createElement('table');
      table.className = 'mali-table';
      let tHtml = `<thead><tr><th>Oran</th><th>Değer</th></tr></thead><tbody>`;
      for (const r of this.data.ratios) {
        tHtml += `<tr><td>${r.name}</td><td class="val-num">${this.formatValue(r.value, r.format)}</td></tr>`;
      }
      tHtml += `</tbody>`;
      table.innerHTML = tHtml;
      ratiosCard.appendChild(table);
      rightCol.appendChild(ratiosCard);
    }

    mainRow.appendChild(leftCol);
    mainRow.appendChild(rightCol);
    this.contentEl.appendChild(mainRow);
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
