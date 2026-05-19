/**
 * MarketOverview — Piyasa genel görünümü bileşeni.
 * Veri: GET /api/market/overview  |  Otomatik yenileme: her 2 dakika
 *
 * Gruplar: BIST endeksleri, döviz, kripto, emtia, küresel
 * Her kart: isim, fiyat, değişim yüzdesi (kırmızı/yeşil), kalite rozeti
 */

interface MarketEntry {
  symbol: string;
  label: string;
  last: number | null;
  change_pct: number | null;
  fetched_at: string | null;
  quality: 'ok' | 'stale' | 'unknown';
}

interface MarketOverviewData {
  bist: MarketEntry[];
  forex: MarketEntry[];
  crypto: MarketEntry[];
  commodities: MarketEntry[];
  global: MarketEntry[];
  fetched_at: string;
  data_note: string;
}

const REFRESH_MS = 2 * 60 * 1000;

const GROUP_LABELS: Record<string, string> = {
  bist: 'BIST Endeksleri',
  forex: 'Döviz',
  commodities: 'Emtia',
  crypto: 'Kripto',
  global: 'Küresel',
};

function formatPrice(val: number | null, symbol: string): string {
  if (val === null) return '—';
  // Crypto and forex have different decimal needs
  if (symbol.endsWith('USDT') || symbol === 'BTCUSDT' || symbol === 'ETHUSDT') {
    return val >= 1000
      ? val.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      : val.toLocaleString('tr-TR', { minimumFractionDigits: 4, maximumFractionDigits: 4 });
  }
  if (val < 1) return val.toLocaleString('tr-TR', { minimumFractionDigits: 4, maximumFractionDigits: 4 });
  if (val >= 1000) return val.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return val.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function qualityBadgeHtml(quality: MarketEntry['quality']): string {
  if (quality === 'ok') return '';
  if (quality === 'stale') return '<span class="mo-quality-badge mo-stale" title="Veri eski (>1 gün)">gecikmiş</span>';
  return '<span class="mo-quality-badge mo-unknown" title="Veri bulunamadı">bilinmiyor</span>';
}

function entryCardHtml(entry: MarketEntry): string {
  const changePct = entry.change_pct;
  let changeClass = 'mo-neutral';
  let changeText = '—';
  if (changePct !== null) {
    if (changePct > 0) { changeClass = 'mo-up'; changeText = `+${changePct.toFixed(2)}%`; }
    else if (changePct < 0) { changeClass = 'mo-down'; changeText = `${changePct.toFixed(2)}%`; }
    else { changeClass = 'mo-neutral'; changeText = '0.00%'; }
  }

  return `
    <div class="mo-card" title="${entry.symbol}">
      <div class="mo-card-header">
        <span class="mo-label">${entry.label}</span>
        ${qualityBadgeHtml(entry.quality)}
      </div>
      <div class="mo-price">${formatPrice(entry.last, entry.symbol)}</div>
      <div class="mo-change ${changeClass}">${changeText}</div>
    </div>`;
}

function groupSectionHtml(groupKey: string, entries: MarketEntry[]): string {
  if (!entries || entries.length === 0) return '';
  const label = GROUP_LABELS[groupKey] ?? groupKey;
  const cards = entries.map(entryCardHtml).join('');
  return `
    <div class="mo-group">
      <div class="mo-group-label">${label}</div>
      <div class="mo-cards">${cards}</div>
    </div>`;
}

export class MarketOverview {
  private container: HTMLElement;
  private data: MarketOverviewData | null = null;
  private loading = false;
  private refreshTimer: ReturnType<typeof setInterval> | null = null;
  private destroyed = false;

  constructor(container: HTMLElement) {
    this.container = container;
    this.injectStyles();
    this.render();
    void this.load();
    this.refreshTimer = setInterval(() => void this.load(), REFRESH_MS);
  }

  destroy(): void {
    this.destroyed = true;
    if (this.refreshTimer !== null) clearInterval(this.refreshTimer);
  }

  private httpBase(): string {
    if (typeof window === 'undefined') return 'http://127.0.0.1:8000';
    return window.location.origin.replace(/^ws/, 'http');
  }

  private async load(): Promise<void> {
    if (this.loading || this.destroyed) return;
    this.loading = true;

    try {
      const res = await fetch(`${this.httpBase()}/api/market/overview`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      this.data = (await res.json()) as MarketOverviewData;
      this.renderData();
    } catch {
      this.renderError();
    } finally {
      this.loading = false;
    }
  }

  // ── Layout ──────────────────────────────────────────────────────────────────

  private render(): void {
    this.container.innerHTML = `
      <div class="mo-wrap">
        <div class="mo-toolbar">
          <span class="mo-title">Piyasa Genel Görünümü</span>
          <button class="btn-sm mo-refresh-btn" id="mo-refresh-btn">Yenile</button>
        </div>
        <div class="mo-body" id="mo-body">
          <div class="mo-loading">Yükleniyor…</div>
        </div>
        <div class="mo-footer" id="mo-footer"></div>
      </div>`;

    const btn = this.container.querySelector<HTMLButtonElement>('#mo-refresh-btn');
    if (btn) btn.addEventListener('click', () => void this.load());
  }

  private renderData(): void {
    if (!this.data) return;
    const body = this.container.querySelector<HTMLElement>('#mo-body');
    const footer = this.container.querySelector<HTMLElement>('#mo-footer');
    if (!body) return;

    const ORDER: Array<keyof Omit<MarketOverviewData, 'fetched_at' | 'data_note'>> = [
      'bist', 'forex', 'commodities', 'crypto', 'global',
    ];

    body.innerHTML = ORDER
      .map(key => groupSectionHtml(key as string, this.data![key] as MarketEntry[]))
      .join('');

    if (footer) {
      const ts = this.data.fetched_at
        ? new Date(this.data.fetched_at).toLocaleTimeString('tr-TR')
        : '';
      footer.innerHTML = `
        <span class="mo-note">${this.data.data_note}</span>
        ${ts ? `<span class="mo-ts">Son güncelleme: ${ts}</span>` : ''}`;
    }
  }

  private renderError(): void {
    const body = this.container.querySelector<HTMLElement>('#mo-body');
    if (!body) return;
    body.innerHTML = `
      <div class="mo-error">
        <span>Piyasa verisi şu an yüklenemiyor.</span>
        <button class="btn-sm" id="mo-retry-btn">Tekrar Dene</button>
      </div>`;
    const btn = body.querySelector<HTMLButtonElement>('#mo-retry-btn');
    if (btn) btn.addEventListener('click', () => void this.load());
  }

  // ── Scoped styles ────────────────────────────────────────────────────────────

  private injectStyles(): void {
    if (document.getElementById('mo-styles')) return;
    const style = document.createElement('style');
    style.id = 'mo-styles';
    style.textContent = `
      .mo-wrap { display: flex; flex-direction: column; height: 100%; overflow-y: auto; padding: 0 0 20px; }
      .mo-toolbar { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px 6px; }
      .mo-title { font-family: var(--font-sans); font-size: 14px; font-weight: 700; color: var(--text-bold); }
      .mo-refresh-btn { margin-left: 8px; }
      .mo-body { flex: 1; padding: 4px 10px 10px; }
      .mo-loading { color: var(--text); font-size: 13px; padding: 20px; text-align: center; }
      .mo-error { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 30px; color: var(--text); font-size: 13px; }
      .mo-group { margin-bottom: 16px; }
      .mo-group-label { font-family: var(--font-sans); font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; color: var(--text-dim); margin-bottom: 6px; padding: 0 2px; }
      .mo-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 6px; }
      .mo-card { background: var(--panel); border: 1px solid var(--border); border-radius: 7px; padding: 10px 12px; transition: border-color 0.15s, transform 0.15s; cursor: default; }
      .mo-card:hover { border-color: var(--border2); transform: translateY(-1px); }
      .mo-card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 5px; gap: 4px; }
      .mo-label { font-size: 10px; color: var(--text); font-family: var(--font-sans); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .mo-price { font-size: 14px; font-weight: 700; font-family: var(--font-mono); color: var(--text-bold); margin-bottom: 3px; }
      .mo-change { font-size: 11px; font-weight: 700; font-family: var(--font-mono); }
      .mo-up { color: var(--green); }
      .mo-down { color: var(--red); }
      .mo-neutral { color: var(--text); }
      .mo-quality-badge { font-size: 8px; font-weight: 700; padding: 1px 4px; border-radius: 3px; white-space: nowrap; flex-shrink: 0; }
      .mo-stale { background: rgba(255, 176, 32, 0.15); color: var(--amber); border: 1px solid rgba(255, 176, 32, 0.35); }
      .mo-unknown { background: rgba(248, 81, 73, 0.12); color: var(--red); border: 1px solid rgba(248, 81, 73, 0.3); }
      .mo-footer { padding: 4px 14px 8px; display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; }
      .mo-note { font-size: 10px; color: var(--text-dim); font-style: italic; }
      .mo-ts { font-size: 10px; color: var(--text-dim); font-family: var(--font-mono); }
      @media (max-width: 700px) {
        .mo-cards { grid-template-columns: repeat(2, 1fr); }
      }
    `;
    document.head.appendChild(style);
  }
}
