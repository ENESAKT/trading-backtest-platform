import {
  EDUCATION_ARTICLES,
  EDUCATION_CATEGORIES,
  type EducationArticle,
  type EducationCategory,
  categoryLabel,
  renderMarkdown,
  searchEducationArticles,
} from '../content/egitimler/index.js';

interface EducationPanelHandlers {
  onOpenChartIndicator?: (indicator: string) => void;
  onOpenStrategy?: (strategyId: string) => void;
}

const SOURCE_LABELS: Record<string, string> = {
  fuat_akman_indikator: 'Fuat Akman - İndikatörler',
  fuat_sistem_trading: 'Fuat Akman - Sistem Trading',
  kivanc_hareketli_ortalamalar: 'Kıvanç Özbilgiç - Hareketli Ortalamalar',
  kivanc_algo_trade: 'Kıvanç Özbilgiç - Algo Trade',
  yasar_teknik_analiz: 'Yaşar Erdinç - Teknik Analiz',
  yasar_vob: 'Yaşar Erdinç - VOB',
  bolgun_vadeli_trade: 'Evren Bolgün - Vadeli Trade',
  yatirimci_psikolojisi: 'Yaşar Erdinç - Yatırımcı Psikolojisi',
};

const CONFIDENCE_LABELS: Record<string, string> = {
  high: 'yüksek',
  medium: 'orta',
  low: 'düşük',
};

const METHOD_LABELS: Record<string, string> = {
  frame_ocr: 'kare OCR',
  transcript: 'transkript',
  manual_review: 'manuel inceleme',
  external_verification: 'dış doğrulama',
};

export class EgitimlerPanel {
  private container: HTMLElement;
  private handlers: EducationPanelHandlers;
  private query = '';
  private category: EducationCategory | 'all' = 'all';
  private selectedSlug = EDUCATION_ARTICLES[0]?.slug ?? '';

  constructor(container: HTMLElement, handlers: EducationPanelHandlers = {}) {
    this.container = container;
    this.handlers = handlers;
    this.render();
    this.bindEvents();
  }

  private get filteredArticles(): EducationArticle[] {
    return searchEducationArticles(this.query, this.category);
  }

  private get selectedArticle(): EducationArticle | undefined {
    const filtered = this.filteredArticles;
    return filtered.find(article => article.slug === this.selectedSlug)
      ?? filtered[0]
      ?? EDUCATION_ARTICLES.find(article => article.slug === this.selectedSlug)
      ?? EDUCATION_ARTICLES[0];
  }

  private render(): void {
    const selected = this.selectedArticle;
    const list = this.filteredArticles;
    this.container.innerHTML = `
      <div class="education-wrap">
        <aside class="education-sidebar">
          <div class="education-toolbar">
            <input
              id="education-search"
              class="search-input"
              type="search"
              value="${this.escapeAttr(this.query)}"
              placeholder="Makale ara..."
              autocomplete="off"
            >
          </div>
          <div class="education-categories">
            ${EDUCATION_CATEGORIES.map(item => `
              <button class="education-category${item.id === this.category ? ' active' : ''}" data-education-category="${item.id}">
                <span>${this.escape(item.label)}</span>
                <b>${this.countForCategory(item.id)}</b>
              </button>
            `).join('')}
          </div>
          <div class="education-list" id="education-list">
            ${list.length ? list.map(article => this.articleRow(article, article.slug === selected?.slug)).join('') : '<div class="empty-state">Aramayla eşleşen makale yok</div>'}
          </div>
        </aside>
        <article class="education-article" id="education-article">
          ${selected ? this.articleHTML(selected) : '<div class="empty-state">Henüz makale yok</div>'}
        </article>
      </div>
    `;
  }

  private bindEvents(): void {
    this.container.addEventListener('input', (evt) => {
      const target = evt.target;
      if (!(target instanceof HTMLInputElement) || target.id !== 'education-search') return;
      this.query = target.value;
      this.renderResults();
    });

    this.container.addEventListener('click', (evt) => {
      const target = evt.target as HTMLElement;

      const categoryBtn = target.closest<HTMLElement>('[data-education-category]');
      if (categoryBtn) {
        this.category = categoryBtn.dataset['educationCategory'] as EducationCategory | 'all';
        this.render();
        return;
      }

      const articleBtn = target.closest<HTMLElement>('[data-education-slug]');
      if (articleBtn) {
        this.selectedSlug = articleBtn.dataset['educationSlug'] || this.selectedSlug;
        this.renderResults();
        return;
      }

      const chartBtn = target.closest<HTMLElement>('[data-chart-indicator]');
      if (chartBtn) {
        this.handlers.onOpenChartIndicator?.(chartBtn.dataset['chartIndicator'] || '');
        return;
      }

      const strategyBtn = target.closest<HTMLElement>('[data-strategy-id]');
      if (strategyBtn) {
        this.handlers.onOpenStrategy?.(strategyBtn.dataset['strategyId'] || '');
      }
    });
  }

  private renderResults(): void {
    const selected = this.selectedArticle;
    const list = this.filteredArticles;
    const listEl = this.container.querySelector<HTMLElement>('#education-list');
    const articleEl = this.container.querySelector<HTMLElement>('#education-article');
    if (listEl) {
      listEl.innerHTML = list.length
        ? list.map(article => this.articleRow(article, article.slug === selected?.slug)).join('')
        : '<div class="empty-state">Aramayla eşleşen makale yok</div>';
    }
    if (articleEl) {
      articleEl.innerHTML = selected
        ? this.articleHTML(selected)
        : '<div class="empty-state">Henüz makale yok</div>';
    }
  }

  private articleRow(article: EducationArticle, active: boolean): string {
    return `
      <button class="education-row${active ? ' active' : ''}" data-education-slug="${this.escapeAttr(article.slug)}">
        <span>${this.escape(article.title)}</span>
        <small>${this.escape(categoryLabel(article.category))} · ${this.escape(article.difficulty)}</small>
      </button>
    `;
  }

  private articleHTML(article: EducationArticle): string {
    return `
      <header class="education-article-header">
        <div>
          <span class="education-kicker">${this.escape(categoryLabel(article.category))}</span>
          <h2>${this.escape(article.title)}</h2>
        </div>
        <div class="education-meta">
          <span>${this.escape(article.difficulty)}</span>
          <span>kaynak güveni: ${this.escape(CONFIDENCE_LABELS[article.source_confidence] ?? article.source_confidence)}</span>
        </div>
      </header>
      <div class="education-tags">
        ${article.tags.map(tag => `<span>${this.escape(tag)}</span>`).join('')}
      </div>
      <section class="education-source-note">
        <b>Kaynak notu</b>
        <span>${this.escape(this.sourceSummary(article))}</span>
      </section>
      <div class="education-markdown">
        ${renderMarkdown(article.content)}
      </div>
      <footer class="education-bridges">
        <div>
          <b>PiyasaPilot'ta kullan</b>
          <span>${this.escape(article.indicator_key || 'Eğitim köprüleri')}</span>
        </div>
        <div class="education-actions">
          ${this.bridgeActions(article)}
        </div>
      </footer>
    `;
  }

  private bridgeActions(article: EducationArticle): string {
    const actions: string[] = [];
    if (article.chart_indicator) {
      actions.push(`
        <button class="btn-secondary" data-chart-indicator="${this.escapeAttr(article.chart_indicator)}">
          Grafikte Aç
        </button>
      `);
    }
    for (const strategyId of article.related_strategies) {
      actions.push(`
        <button class="btn-secondary" data-strategy-id="${this.escapeAttr(strategyId)}">
          Backtest Preset'i Aç
        </button>
      `);
    }
    return actions.join('') || '<span class="education-muted">Bu makale için köprü yakında.</span>';
  }

  private sourceSummary(article: EducationArticle): string {
    const courses = article.source_courses
      .map(course => SOURCE_LABELS[course] ?? course)
      .join(', ');
    const method = METHOD_LABELS[article.source_method] ?? article.source_method;
    const audio = article.needs_audio_transcript
      ? 'Ses transkripti eksik olabilir.'
      : 'Ses transkripti ile destekli.';
    return `${courses || 'Kaynak kurs'} · ${method} · ${audio} · ${article.copy_policy}`;
  }

  private countForCategory(category: EducationCategory | 'all'): number {
    return category === 'all'
      ? EDUCATION_ARTICLES.length
      : EDUCATION_ARTICLES.filter(article => article.category === category).length;
  }

  private escape(value: unknown): string {
    return String(value ?? '').replace(/[&<>"']/g, ch => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
    })[ch] || ch);
  }

  private escapeAttr(value: unknown): string {
    return this.escape(value).replace(/`/g, '&#96;');
  }
}
