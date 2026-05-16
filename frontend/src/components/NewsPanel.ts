/**
 * NewsPanel — Haber akışı paneli (8. sekme).
 * Veri: GET /api/news  |  Otomatik yenileme: her 5 dakika
 */

interface NewsItem {
  id: number;
  symbol: string;
  headline: string;
  body: string | null;
  source: string | null;
  published_at: string | null;
  fetched_at: string;
  url: string | null;
  is_read: number;
}

const REFRESH_MS = 5 * 60 * 1000;

function timeAgo(iso: string | null): string {
  if (!iso) return '';
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return `${Math.round(diff)}s`;
  if (diff < 3600) return `${Math.round(diff / 60)}dk`;
  if (diff < 86400) return `${Math.round(diff / 3600)}sa`;
  return `${Math.round(diff / 86400)}g`;
}

export class NewsPanel {
  private container: HTMLElement;
  private items: NewsItem[] = [];
  private filterText = '';
  private filterSymbol = '';
  private refreshTimer: ReturnType<typeof setInterval> | null = null;
  private loading = false;
  private readIds = new Set<number>();

  constructor(container: HTMLElement) {
    this.container = container;
    this.render();
    window.addEventListener('piyasapilot:news-filter-symbol', this.handleSymbolFilter);
    void this.load(false);
    this.refreshTimer = setInterval(() => void this.load(true), REFRESH_MS);
  }

  destroy(): void {
    if (this.refreshTimer !== null) clearInterval(this.refreshTimer);
    window.removeEventListener('piyasapilot:news-filter-symbol', this.handleSymbolFilter);
  }

  private handleSymbolFilter = (event: Event): void => {
    const detail = (event as CustomEvent<{ symbol?: string }>).detail;
    const symbol = detail?.symbol?.toUpperCase().trim();
    if (!symbol) return;
    this.filterSymbol = symbol;
    const input = this.container.querySelector<HTMLInputElement>('#news-symbol');
    if (input) input.value = symbol;
    void this.load(true);
  };

  // ── Layout ──────────────────────────────────────────────────────────────────

  private render(): void {
    this.container.innerHTML = `
      <div class="news-wrap">
        <div class="news-toolbar">
          <input type="text" id="news-keyword" class="news-filter-input" placeholder="Anahtar kelime ara…" />
          <input type="text" id="news-symbol" class="news-filter-input" style="max-width:110px" placeholder="Sembol (THYAO)" />
          <button class="btn-sm news-refresh-btn" id="news-refresh-btn">⟳ Yenile</button>
        </div>
        <div class="news-list" id="news-list">
          <div class="skeleton-wrap">
            ${Array.from({ length: 5 }).map(() => `
              <div class="news-card">
                <div class="skeleton skeleton-text" style="width:40%"></div>
                <div class="skeleton skeleton-text" style="width:90%"></div>
                <div class="skeleton skeleton-text" style="width:70%"></div>
              </div>`).join('')}
          </div>
        </div>
      </div>`;

    const kwInput  = this.container.querySelector<HTMLInputElement>('#news-keyword')!;
    const symInput = this.container.querySelector<HTMLInputElement>('#news-symbol')!;
    const refreshBtn = this.container.querySelector<HTMLButtonElement>('#news-refresh-btn')!;

    kwInput.addEventListener('input', () => {
      this.filterText = kwInput.value.toLowerCase();
      this.renderList();
    });
    symInput.addEventListener('input', () => {
      this.filterSymbol = symInput.value.toUpperCase().trim();
      this.renderList();
    });
    symInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') void this.load(true);
    });
    refreshBtn.addEventListener('click', () => void this.load(true));
  }

  // ── Data ─────────────────────────────────────────────────────────────────────

  private async load(fresh: boolean): Promise<void> {
    if (this.loading) return;
    this.loading = true;
    const btn = this.container.querySelector<HTMLButtonElement>('#news-refresh-btn');
    if (btn) btn.disabled = true;

    try {
      const sym = this.filterSymbol || '';
      const params = new URLSearchParams({ limit: '40' });
      if (sym) params.set('symbol', sym);
      if (fresh) params.set('fresh', 'true');
      const res = await fetch(`/api/news?${params}`);
      if (res.ok) {
        const data = await res.json() as { news: NewsItem[] };
        this.items = data.news ?? [];
        this.renderList();
      }
    } catch {
      // network error — show cached
    } finally {
      this.loading = false;
      if (btn) btn.disabled = false;
    }
  }

  // ── Render list ───────────────────────────────────────────────────────────────

  private renderList(): void {
    const el = this.container.querySelector('#news-list')!;
    const filtered = this.items.filter(n => {
      if (this.filterSymbol && n.symbol !== this.filterSymbol) return false;
      if (this.filterText) {
        const hay = `${n.headline} ${n.body ?? ''} ${n.source ?? ''}`.toLowerCase();
        if (!hay.includes(this.filterText)) return false;
      }
      return true;
    });

    if (!filtered.length) {
      el.innerHTML = `<div class="news-empty">${this.items.length ? 'Eşleşen haber yok' : 'Henüz haber yok — ⟳ Yenile'}</div>`;
      return;
    }

    el.innerHTML = filtered.map(n => this.cardHTML(n)).join('');

    el.querySelectorAll<HTMLElement>('.news-card').forEach(card => {
      card.addEventListener('click', () => {
        const idStr = card.dataset['id'];
        const id = idStr ? parseInt(idStr, 10) : NaN;
        if (!isNaN(id) && !this.readIds.has(id)) {
          this.readIds.add(id);
          card.classList.add('news-read');
          void fetch('/api/news/mark-read', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids: [id] }),
          }).then((r) => {
            if (!r.ok) throw new Error(`mark-read ${r.status}`);
            return r.json();
          }).then((res: unknown) => {
            const d = res as { unread?: number } | null;
            if (d) this.updateBadge(d.unread ?? 0);
          }).catch((err: unknown) => {
            this.readIds.delete(id);
            card.classList.remove('news-read');
            card.insertAdjacentHTML('beforeend', '<div class="news-inline-error">Okundu bilgisi kaydedilemedi.</div>');
            console.warn('[NewsPanel] mark-read failed:', err);
          });
        }
        const sym = card.dataset['symbol'];
        if (sym) window.dispatchEvent(new CustomEvent('openSymbolOnChart', { detail: { symbol: sym } }));
        const url = card.dataset['url'];
        if (url) window.open(url, '_blank', 'noopener');
      });
    });
  }

  private updateBadge(count: number): void {
    const badge = document.getElementById('tab-news-badge');
    if (!badge) return;
    if (count > 0) {
      badge.textContent = String(count > 99 ? '99+' : count);
      badge.hidden = false;
    } else {
      badge.hidden = true;
    }
  }

  private cardHTML(n: NewsItem): string {
    const ago = timeAgo(n.published_at ?? n.fetched_at);
    const src = n.source ? this.esc(n.source) : 'Haber';
    const sym = this.esc(n.symbol);
    const url = n.url ? ` data-url="${this.esc(n.url)}"` : '';
    const isRead = n.is_read || this.readIds.has(n.id);
    const readCls = isRead ? ' news-read' : '';
    return `
      <div class="news-card${readCls}" data-id="${n.id}" data-symbol="${sym}"${url}>
        <div class="news-card-header">
          <span class="news-source">${src}</span>
          ${ago ? `<span class="news-time">${ago} önce</span>` : ''}
          <span class="news-sym-tag">${sym}</span>
        </div>
        <div class="news-headline">${this.esc(n.headline)}</div>
        ${n.body ? `<div class="news-body">${this.esc(n.body)}</div>` : ''}
      </div>`;
  }

  private esc(s: string): string {
    return s.replace(/[&<>"']/g, c =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] ?? c);
  }
}
