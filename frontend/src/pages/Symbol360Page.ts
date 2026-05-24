/**
 * Symbol 360 — Sembol detay sayfası (v2 — sekme mimarisi).
 * Route: /terminal/symbol/:market/:symbol
 *
 * Sekmeler:
 *  1. Genel Bakış   — fiyat, hacim, temel veriler, son haberler özeti
 *  2. Teknikler     — osilatörler, hareketli ortalamalar, pivot seviyeleri
 *  3. Finansallar   — gelir tablosu, bilanço (BIST)
 *  4. Haberler      — son 20 haber
 */

// ─── Yardımcılar ─────────────────────────────────────────────────────────────

function esc(s: unknown): string {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function fmtNum(v: number | null | undefined, d = 2): string {
  if (v == null || isNaN(v)) return '—';
  return v.toLocaleString('tr-TR', { minimumFractionDigits: d, maximumFractionDigits: d });
}

function fmtPct(v: number | null | undefined, d = 2): string {
  if (v == null || isNaN(v)) return '—';
  return (v >= 0 ? '+' : '') + fmtNum(v, d) + '%';
}

function timeAgo(iso: string | null | undefined): string {
  if (!iso) return '';
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60)    return `${Math.round(diff)}s`;
  if (diff < 3600)  return `${Math.round(diff / 60)}dk`;
  if (diff < 86400) return `${Math.round(diff / 3600)}sa`;
  return `${Math.round(diff / 86400)}g`;
}

function signalTR(s: string | null | undefined): string {
  switch ((s ?? '').toLowerCase()) {
    case 'buy':        return 'AL';
    case 'sell':       return 'SAT';
    case 'oversold':   return 'AŞIRI SATIM';
    case 'overbought': return 'AŞIRI ALIM';
    default:           return 'NÖTR';
  }
}

function signalCls(s: string | null | undefined): string {
  switch ((s ?? '').toLowerCase()) {
    case 'buy': case 'oversold':   return 'pos';
    case 'sell': case 'overbought': return 'neg';
    default:                        return 'neu';
  }
}

// ─── CSS ─────────────────────────────────────────────────────────────────────

const CSS = `
<style>
/* ── Layout ── */
.s360-wrap {
  max-width: 1140px;
  margin: 0 auto;
  padding: 18px 16px 80px;
  color: var(--text, #94A3B8);
  font-family: var(--font, system-ui, sans-serif);
  font-size: 13px;
}
/* ── Back button ── */
.s360-back {
  display: inline-flex; align-items: center; gap: 5px;
  color: var(--text-dim, #64748B); font-size: 13px;
  text-decoration: none; margin-bottom: 14px;
  cursor: pointer; background: none; border: none; padding: 0;
}
.s360-back:hover { color: var(--text, #94A3B8); }
/* ── Header ── */
.s360-header {
  display: flex; align-items: baseline; gap: 12px;
  flex-wrap: wrap; margin-bottom: 20px;
}
.s360-symbol { font-size: 26px; font-weight: 700; color: var(--text-bold, #F8FAFC); }
.s360-name   { font-size: 13px; color: var(--text-dim, #64748B); }
.s360-price  { font-size: 24px; font-weight: 600; color: var(--text-bold, #F8FAFC); margin-left: auto; }
.s360-chg    { font-size: 14px; }
.s360-chg.pos { color: var(--green, #10B981); }
.s360-chg.neg { color: var(--red, #EF4444); }
/* ── Tabs ── */
.s360-tabs {
  display: flex; gap: 2px; border-bottom: 1px solid var(--border, rgba(255,255,255,.08));
  margin-bottom: 20px;
}
.s360-tab {
  padding: 9px 18px; font-size: 13px; font-weight: 500;
  color: var(--text-dim, #64748B);
  background: none; border: none; border-bottom: 2px solid transparent;
  cursor: pointer; margin-bottom: -1px;
  transition: color .15s, border-color .15s;
}
.s360-tab:hover    { color: var(--text, #94A3B8); }
.s360-tab.active   { color: var(--blue, #3B82F6); border-bottom-color: var(--blue, #3B82F6); }
/* ── Cards / grid ── */
.s360-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
  gap: 12px; margin-bottom: 16px;
}
.s360-card {
  background: var(--panel, #131722);
  border: 1px solid var(--border, rgba(255,255,255,.08));
  border-radius: 10px; padding: 14px 16px;
}
.s360-card h3 {
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: .06em; color: var(--text-dim, #64748B);
  margin: 0 0 10px;
}
/* ── Key-value rows ── */
.s360-kv { display: flex; justify-content: space-between; margin-bottom: 6px; align-items: center; }
.s360-kv:last-child { margin-bottom: 0; }
.s360-kv .lbl { color: var(--text, #94A3B8); }
.s360-kv .val { font-weight: 500; color: var(--text-bold, #F8FAFC); }
.s360-kv .val.pos { color: var(--green, #10B981); }
.s360-kv .val.neg { color: var(--red, #EF4444); }
.s360-kv .val.na  { color: var(--text-dim, #64748B); font-style: italic; }
/* ── Signal badge ── */
.sig-badge {
  display: inline-block; padding: 2px 9px; border-radius: 20px;
  font-size: 11px; font-weight: 600;
}
.sig-badge.pos { background: rgba(16,185,129,.15); color: #10B981; }
.sig-badge.neg { background: rgba(239,68,68,.15);  color: #EF4444; }
.sig-badge.neu { background: rgba(148,163,184,.1); color: #94A3B8; }
/* ── Overall rating block ── */
.s360-overall {
  display: flex; align-items: center; gap: 16px;
  background: var(--panel, #131722);
  border: 1px solid var(--border, rgba(255,255,255,.08));
  border-radius: 10px; padding: 14px 20px; margin-bottom: 16px;
}
.s360-overall .ov-label { font-size: 12px; color: var(--text-dim); }
.s360-overall .ov-sig {
  font-size: 20px; font-weight: 700; letter-spacing: .02em;
}
.s360-overall .ov-sig.pos { color: var(--green, #10B981); }
.s360-overall .ov-sig.neg { color: var(--red, #EF4444); }
.s360-overall .ov-sig.neu { color: var(--text-dim, #64748B); }
.s360-overall .ov-counts { font-size: 12px; color: var(--text-dim); display: flex; gap: 12px; }
.s360-overall .ov-counts span.buy  { color: var(--green, #10B981); }
.s360-overall .ov-counts span.sell { color: var(--red, #EF4444); }
/* ── Tech table ── */
.tech-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.tech-table th {
  text-align: left; font-size: 10px; font-weight: 600; text-transform: uppercase;
  letter-spacing: .06em; color: var(--text-dim); padding: 0 8px 6px 0;
  border-bottom: 1px solid var(--border, rgba(255,255,255,.08));
}
.tech-table td { padding: 6px 8px 6px 0; border-bottom: 1px solid rgba(255,255,255,.03); }
.tech-table tr:last-child td { border-bottom: none; }
.tech-table .tname { color: var(--text, #94A3B8); }
.tech-table .tval  { color: var(--text-bold, #F8FAFC); font-weight: 500; text-align: right; }
.tech-table .tsig  { text-align: right; }
/* ── Pivot table ── */
.pivot-wrap { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px; }
.pivot-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.pivot-table th {
  text-align: left; font-size: 10px; font-weight: 600; text-transform: uppercase;
  letter-spacing: .06em; color: var(--text-dim); padding: 0 0 6px;
  border-bottom: 1px solid var(--border, rgba(255,255,255,.08));
}
.pivot-table td { padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,.03); color: var(--text); }
.pivot-table td:last-child { text-align: right; color: var(--text-bold, #F8FAFC); font-weight: 500; }
.pivot-table .pp-row td { color: var(--blue, #3B82F6); font-weight: 600; }
.pivot-table .res-row td:first-child { color: var(--red, #EF4444); }
.pivot-table .sup-row td:first-child { color: var(--green, #10B981); }
/* ── News ── */
.s360-news-item {
  padding: 10px 0;
  border-bottom: 1px solid var(--border, rgba(255,255,255,.06));
}
.s360-news-item:last-child { border-bottom: none; }
.s360-news-item a { color: var(--text-bold, #F8FAFC); text-decoration: none; }
.s360-news-item a:hover { text-decoration: underline; }
.s360-news-meta { font-size: 11px; color: var(--text-dim, #64748B); margin-top: 3px; }
/* ── Similar chips ── */
.s360-similar { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
.s360-sim-chip {
  background: var(--border, rgba(255,255,255,.06)); border-radius: 6px;
  padding: 5px 12px; font-size: 12px; cursor: pointer;
  color: var(--text, #94A3B8); border: none;
}
.s360-sim-chip:hover { background: rgba(59,130,246,.15); color: var(--blue, #3B82F6); }
/* ── States ── */
.s360-loading { color: var(--text-dim); padding: 40px; text-align: center; }
.s360-error   { color: var(--red, #EF4444); padding: 40px; text-align: center; }
.s360-na-msg  { font-size: 12px; color: var(--text-dim); padding: 12px 0; }
/* ── Section title ── */
.sec-title {
  font-size: 11px; font-weight: 600; text-transform: uppercase;
  letter-spacing: .06em; color: var(--text-dim); margin: 18px 0 8px;
}
</style>
`;

// ─── Entry point ─────────────────────────────────────────────────────────────

export async function renderSymbol360Page(container: HTMLElement): Promise<void> {
  const parts  = window.location.pathname.split('/').filter(Boolean);
  const market = (parts[2] ?? 'BIST').toUpperCase();
  const symbol = (parts[3] ?? '').toUpperCase();

  if (!symbol) {
    container.innerHTML = `${CSS}<div class="s360-wrap"><div class="s360-error">Geçersiz sembol.</div></div>`;
    return;
  }

  container.innerHTML = `${CSS}<div class="s360-wrap"><div class="s360-loading">Yükleniyor…</div></div>`;
  const wrap = container.querySelector<HTMLElement>('.s360-wrap')!;

  // Geri butonu
  const backBtn = document.createElement('button');
  backBtn.className = 's360-back';
  backBtn.innerHTML = '← Geri';
  backBtn.addEventListener('click', () => history.back());

  wrap.innerHTML = '';
  wrap.appendChild(backBtn);

  // Paralel veri çekimi
  const [priceRes, newsRes, techRes, finRes] = await Promise.allSettled([
    fetch(`/api/quote?symbol=${encodeURIComponent(symbol)}&market=${encodeURIComponent(market)}`),
    fetch(`/api/news?symbol=${encodeURIComponent(symbol)}&limit=20`),
    fetch(`/api/technical/summary?symbol=${encodeURIComponent(symbol)}&market=${encodeURIComponent(market)}&timeframe=1d`),
    fetch(`/api/financials?symbol=${encodeURIComponent(symbol)}&market=${encodeURIComponent(market)}`),
  ]);

  // ── Fiyat verisi ─────────────────────────────────────────────────────────
  let lastPrice: number | null = null;
  let changePct: number | null = null;
  let volume: number | null    = null;
  let symbolName = symbol;
  let marketCap: number | null = null;

  if (priceRes.status === 'fulfilled' && priceRes.value.ok) {
    try {
      const d = await priceRes.value.json() as Record<string, unknown>;
      lastPrice  = (d['last_price'] as number) ?? null;
      changePct  = (d['change_pct'] as number) ?? null;
      volume     = (d['volume']     as number) ?? null;
      marketCap  = (d['market_cap'] as number) ?? null;
      symbolName = (d['name']       as string) || symbol;
    } catch { /* use defaults */ }
  }

  // ── Header ──────────────────────────────────────────────────────────────
  const chgCls = changePct == null ? '' : changePct >= 0 ? 'pos' : 'neg';
  const header = document.createElement('div');
  header.className = 's360-header';
  header.innerHTML = `
    <span class="s360-symbol">${esc(symbol)}</span>
    ${symbolName !== symbol ? `<span class="s360-name">${esc(symbolName)}</span>` : ''}
    <span class="s360-price">${lastPrice != null ? fmtNum(lastPrice) : '—'} <small style="font-size:14px;color:var(--text-dim)">TRY</small></span>
    <span class="s360-chg ${chgCls}">${fmtPct(changePct)}</span>
  `;
  wrap.appendChild(header);

  // ── Teknik veri ─────────────────────────────────────────────────────────
  type TechData = Record<string, unknown> | null;
  let tech: TechData = null;
  if (techRes.status === 'fulfilled' && techRes.value.ok) {
    try { tech = await techRes.value.json() as TechData; } catch { /* null */ }
  }

  // ── Haberler verisi ──────────────────────────────────────────────────────
  type NewsItem = Record<string, unknown>;
  let newsItems: NewsItem[] = [];
  if (newsRes.status === 'fulfilled' && newsRes.value.ok) {
    try {
      const nd = await newsRes.value.json() as { news?: NewsItem[] };
      newsItems = nd.news ?? [];
    } catch { /* empty */ }
  }

  // ── Finansal veri ───────────────────────────────────────────────────────
  type FinData = Record<string, unknown> | null;
  let finData: FinData = null;
  if (finRes.status === 'fulfilled' && finRes.value.ok) {
    try { finData = await finRes.value.json() as FinData; } catch { /* null */ }
  }

  // ── Sekmeler ─────────────────────────────────────────────────────────────
  const tabsEl = document.createElement('div');
  tabsEl.className = 's360-tabs';
  const TAB_NAMES = ['Genel Bakış', 'Teknikler', 'Finansallar', 'Haberler'];
  TAB_NAMES.forEach((name, i) => {
    const btn = document.createElement('button');
    btn.className = `s360-tab${i === 0 ? ' active' : ''}`;
    btn.textContent = name;
    btn.addEventListener('click', () => {
      tabsEl.querySelectorAll('.s360-tab').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      tabPanels.forEach((p, j) => { p.style.display = j === i ? '' : 'none'; });
    });
    tabsEl.appendChild(btn);
  });
  wrap.appendChild(tabsEl);

  const tabPanels: HTMLElement[] = TAB_NAMES.map((_, i) => {
    const div = document.createElement('div');
    div.style.display = i === 0 ? '' : 'none';
    wrap.appendChild(div);
    return div;
  });

  // ════════════════════════════════════════════════════════════════════════
  // SEKME 0 — Genel Bakış
  // ════════════════════════════════════════════════════════════════════════
  renderGenelBakis(tabPanels[0], {
    symbol, market, symbolName,
    lastPrice, changePct, volume, marketCap,
    tech, newsItems,
  });

  // ════════════════════════════════════════════════════════════════════════
  // SEKME 1 — Teknikler
  // ════════════════════════════════════════════════════════════════════════
  renderTeknikler(tabPanels[1], tech);

  // ════════════════════════════════════════════════════════════════════════
  // SEKME 2 — Finansallar
  // ════════════════════════════════════════════════════════════════════════
  renderFinansallar(tabPanels[2], finData, market);

  // ════════════════════════════════════════════════════════════════════════
  // SEKME 3 — Haberler
  // ════════════════════════════════════════════════════════════════════════
  renderHaberler(tabPanels[3], newsItems);
}

// ─── SEKME: Genel Bakış ───────────────────────────────────────────────────────

interface GenelBakisProps {
  symbol: string; market: string; symbolName: string;
  lastPrice: number | null; changePct: number | null;
  volume: number | null; marketCap: number | null;
  tech: Record<string, unknown> | null;
  newsItems: Record<string, unknown>[];
}

function renderGenelBakis(panel: HTMLElement, p: GenelBakisProps): void {
  const grid = document.createElement('div');
  grid.className = 's360-grid';

  // Fiyat özeti kartı
  const chgCls = p.changePct == null ? '' : p.changePct >= 0 ? 'pos' : 'neg';
  grid.appendChild(kvCard('Fiyat Özeti', [
    ['Son Fiyat',    p.lastPrice  != null ? fmtNum(p.lastPrice)  : null],
    ['Günlük Değ.',  p.changePct  != null ? fmtPct(p.changePct)  : null, chgCls || 'na'],
    ['Hacim',        p.volume     != null ? fmtNum(p.volume, 0)  : null],
    ['Piyasa Değ.',  p.marketCap  != null ? fmtNum(p.marketCap, 0) : null],
    ['Piyasa',       p.market],
  ]));

  // Temel veriler kartı (şimdilik plaeholder — harici veri gerektirir)
  grid.appendChild(kvCard('Temel Veriler', [
    ['F/K Oranı',    null, 'na'],
    ['PD/DD',        null, 'na'],
    ['Temettü Ver.', null, 'na'],
    ['Beta',         null, 'na'],
  ], 'Temel veriler harici sağlayıcı gerektirir'));

  // Teknik özet özet kartı (genel bakış için sadece genel)
  const techSumCard = document.createElement('div');
  techSumCard.className = 's360-card';
  techSumCard.innerHTML = '<h3>Teknik Özet (Günlük)</h3>';
  if (p.tech) {
    const t    = p.tech;
    const ov   = String((t['overall_rating'] as string) ?? 'neutral');
    const cnt  = (t['overall_counts'] as Record<string, number>) ?? {};
    const osc  = (t['oscillators']    as Record<string, unknown>) ?? {};
    const rsi  = (osc['rsi_14'] as Record<string, unknown>)?.['value'] as number | null;
    const macd = (osc['macd']   as Record<string, unknown>)?.['signal'] as string | null;
    const adx  = (osc['adx_14'] as Record<string, unknown>)?.['value'] as number | null;
    const ovCls = signalCls(ov);
    techSumCard.innerHTML += `
      <div class="s360-kv">
        <span class="lbl">Genel Sinyal</span>
        <span class="sig-badge ${ovCls}">${signalTR(ov)}</span>
      </div>
      <div class="s360-kv"><span class="lbl">AL / SAT / NÖTR</span>
        <span class="val">${cnt['buy'] ?? 0} / ${cnt['sell'] ?? 0} / ${cnt['neutral'] ?? 0}</span></div>
      <div class="s360-kv"><span class="lbl">RSI (14)</span>
        <span class="val ${rsi != null && rsi < 30 ? 'pos' : rsi != null && rsi > 70 ? 'neg' : ''}">${fmtNum(rsi, 1)}</span></div>
      <div class="s360-kv"><span class="lbl">MACD</span>
        <span class="sig-badge ${signalCls(macd)}">${signalTR(macd)}</span></div>
      <div class="s360-kv"><span class="lbl">ADX (14)</span>
        <span class="val">${fmtNum(adx, 1)}</span></div>
    `;
  } else {
    techSumCard.innerHTML += '<p class="s360-na-msg">Teknik veri alınamadı.</p>';
  }
  grid.appendChild(techSumCard);

  // Benzer hisseler kartı
  const simCard = document.createElement('div');
  simCard.className = 's360-card';
  simCard.innerHTML = '<h3>Benzer Hisseler</h3>';
  const similar = getSimilarSymbols(p.symbol, p.market);
  if (similar.length) {
    const simWrap = document.createElement('div');
    simWrap.className = 's360-similar';
    similar.forEach(sym => {
      const btn = document.createElement('button');
      btn.className = 's360-sim-chip';
      btn.textContent = sym;
      btn.addEventListener('click', () => {
        window.location.href = `/terminal/symbol/${p.market}/${sym}`;
      });
      simWrap.appendChild(btn);
    });
    simCard.appendChild(simWrap);
  } else {
    simCard.innerHTML += '<p class="s360-na-msg">Benzer sembol bulunamadı.</p>';
  }
  grid.appendChild(simCard);

  panel.appendChild(grid);

  // Son 3 haber özeti
  if (p.newsItems.length > 0) {
    const newsTitle = document.createElement('div');
    newsTitle.className = 'sec-title';
    newsTitle.textContent = 'Son Haberler';
    panel.appendChild(newsTitle);
    const newsCard = document.createElement('div');
    newsCard.className = 's360-card';
    p.newsItems.slice(0, 3).forEach(n => {
      const div = document.createElement('div');
      div.className = 's360-news-item';
      const url  = n['url']      as string | null;
      const head = esc(n['headline'] as string ?? 'Başlıksız');
      div.innerHTML = `
        ${url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${head}</a>` : `<span>${head}</span>`}
        <div class="s360-news-meta">${esc(n['source'] as string ?? '')} · ${timeAgo(n['published_at'] as string ?? null)}</div>`;
      newsCard.appendChild(div);
    });
    panel.appendChild(newsCard);
  }
}

// ─── SEKME: Teknikler ─────────────────────────────────────────────────────────

function renderTeknikler(panel: HTMLElement, tech: Record<string, unknown> | null): void {
  if (!tech) {
    panel.innerHTML = '<p class="s360-na-msg">Teknik veri alınamadı.</p>';
    return;
  }

  const osc = (tech['oscillators']    as Record<string, unknown>) ?? {};
  const mas = (tech['moving_averages'] as Record<string, unknown>) ?? {};
  const pvt = (tech['pivots']          as Record<string, unknown>) ?? {};
  const overall = String((tech['overall_rating']  as string) ?? 'neutral');
  const cnt     = (tech['overall_counts'] as Record<string, number>) ?? {};
  const oscRat  = (osc['rating']  as Record<string, number>) ?? {};
  const maRat   = (mas['rating']  as Record<string, number>) ?? {};

  // ── Genel sinyal ────────────────────────────────────────────────────────
  const ovEl = document.createElement('div');
  ovEl.className = 's360-overall';
  ovEl.innerHTML = `
    <div>
      <div class="ov-label">Genel Sinyal</div>
      <div class="ov-sig ${signalCls(overall)}">${signalTR(overall)}</div>
    </div>
    <div class="ov-counts">
      <span class="buy">▲ ${cnt['buy'] ?? 0} AL</span>
      <span class="sell">▼ ${cnt['sell'] ?? 0} SAT</span>
      <span>${cnt['neutral'] ?? 0} NÖTR</span>
    </div>
    <div style="margin-left:auto;font-size:11px;color:var(--text-dim)">
      Zaman: ${esc(tech['timeframe'] as string ?? '1d')} ·
      Bar: ${esc(String(tech['bars_used'] ?? '—'))}
    </div>
  `;
  panel.appendChild(ovEl);

  // ── Osilatörler ─────────────────────────────────────────────────────────
  const oscTitle = document.createElement('div');
  oscTitle.className = 'sec-title';
  oscTitle.innerHTML = `Osilatörler &nbsp;<small style="font-weight:400;text-transform:none">AL ${oscRat['buy'] ?? 0} · SAT ${oscRat['sell'] ?? 0} · NÖTR ${oscRat['neutral'] ?? 0}</small>`;
  panel.appendChild(oscTitle);

  const oscCard = document.createElement('div');
  oscCard.className = 's360-card';

  type OscRow = { name: string; value: string; signal: string | null };
  const oscRows: OscRow[] = [];

  const addOscRow = (name: string, obj: unknown, valueKey: string, sigKey = 'signal', decimals = 2) => {
    const o = obj as Record<string, unknown> | null;
    if (!o) { oscRows.push({ name, value: '—', signal: null }); return; }
    const v = o[valueKey] as number | null;
    const s = o[sigKey]   as string | null;
    oscRows.push({ name, value: v != null ? fmtNum(v, decimals) : '—', signal: s ?? null });
  };

  addOscRow('RSI (14)',          osc['rsi_14'],      'value', 'signal', 1);
  addOscRow('MACD Histogramı',   osc['macd'],        'histogram', 'signal', 4);
  addOscRow('Stochastic K',      osc['stochastic'],  'k',    'signal', 1);
  addOscRow('Bollinger Bandı',   osc['bollinger'],   'middle','signal', 2);
  addOscRow('CCI (20)',          osc['cci_20'],      'value', 'signal', 1);
  addOscRow('Momentum (10)',     osc['momentum_10'], 'value', 'signal', 4);
  addOscRow('Williams %R (14)', osc['williams_r_14'],'value', 'signal', 1);
  addOscRow('Stoch RSI K',      osc['stoch_rsi'],   'k',    'signal', 1);
  addOscRow('ADX (14)',          osc['adx_14'],      'value', 'signal', 1);

  // ATR ayrı (sinyal yok)
  const atr = osc['atr_14'] as Record<string, unknown> | null;
  oscRows.push({
    name: 'ATR (14)',
    value: atr ? `${fmtNum(atr['value'] as number | null)} (${fmtNum(atr['atr_pct'] as number | null, 2)}%)` : '—',
    signal: null,
  });

  const oscTable = buildTechTable(oscRows);
  oscCard.appendChild(oscTable);
  panel.appendChild(oscCard);

  // ── Hareketli Ortalamalar ────────────────────────────────────────────────
  const maTitle = document.createElement('div');
  maTitle.className = 'sec-title';
  maTitle.innerHTML = `Hareketli Ortalamalar &nbsp;<small style="font-weight:400;text-transform:none">AL ${maRat['buy'] ?? 0} · SAT ${maRat['sell'] ?? 0} · NÖTR ${maRat['neutral'] ?? 0}</small>`;
  panel.appendChild(maTitle);

  const maCard = document.createElement('div');
  maCard.className = 's360-card';

  type MaRow = { name: string; value: string; dist: string; signal: string | null };
  const maRows: MaRow[] = [];
  const MA_KEYS: [string, string][] = [
    ['sma_10','SMA (10)'], ['sma_20','SMA (20)'], ['sma_30','SMA (30)'],
    ['sma_50','SMA (50)'], ['sma_100','SMA (100)'], ['sma_200','SMA (200)'],
    ['ema_10','EMA (10)'], ['ema_20','EMA (20)'], ['ema_50','EMA (50)'],
    ['ema_100','EMA (100)'], ['ema_200','EMA (200)'],
    ['hma_9','HMA (9)'], ['vwma_20','VWMA (20)'],
  ];
  MA_KEYS.forEach(([key, label]) => {
    const m = mas[key] as Record<string, unknown> | null;
    if (!m) return;
    maRows.push({
      name:   label,
      value:  fmtNum(m['value'] as number | null),
      dist:   m['distance_pct'] != null ? fmtPct(m['distance_pct'] as number) : '—',
      signal: m['signal'] as string | null,
    });
  });

  // Ichimoku
  const ichi = mas['ichimoku'] as Record<string, unknown> | null;
  if (ichi) {
    const tenkan = ichi['tenkan'] as number | null;
    const kijun  = ichi['kijun']  as number | null;
    if (tenkan != null) maRows.push({ name: 'Ichimoku Tenkan', value: fmtNum(tenkan), dist: '—', signal: null });
    if (kijun  != null) maRows.push({ name: 'Ichimoku Kijun',  value: fmtNum(kijun),  dist: '—', signal: null });
  }

  const maTable = document.createElement('table');
  maTable.className = 'tech-table';
  maTable.innerHTML = `<thead><tr>
    <th>Gösterge</th><th style="text-align:right">Değer</th>
    <th style="text-align:right">Uzaklık</th><th style="text-align:right">Sinyal</th>
  </tr></thead>`;
  const maTbody = document.createElement('tbody');
  maRows.forEach(row => {
    const tr = document.createElement('tr');
    const sigCls = signalCls(row.signal);
    tr.innerHTML = `
      <td class="tname">${esc(row.name)}</td>
      <td class="tval">${esc(row.value)}</td>
      <td class="tval">${esc(row.dist)}</td>
      <td class="tsig"><span class="sig-badge ${sigCls}">${signalTR(row.signal)}</span></td>`;
    maTbody.appendChild(tr);
  });
  maTable.appendChild(maTbody);
  maCard.appendChild(maTable);
  panel.appendChild(maCard);

  // ── Pivot Seviyeleri ─────────────────────────────────────────────────────
  const pivTitle = document.createElement('div');
  pivTitle.className = 'sec-title';
  pivTitle.textContent = 'Pivot Seviyeleri';
  panel.appendChild(pivTitle);

  const pivWrap = document.createElement('div');
  pivWrap.className = 'pivot-wrap';

  const buildPivotCard = (title: string, method: Record<string, unknown> | null) => {
    const card = document.createElement('div');
    card.className = 's360-card';
    card.innerHTML = `<h3>${esc(title)}</h3>`;
    if (!method) { card.innerHTML += '<p class="s360-na-msg">Veri yok</p>'; return card; }
    const levels = (method['levels'] as Record<string, number | null>) ?? {};
    const table  = document.createElement('table');
    table.className = 'pivot-table';
    table.innerHTML = `<thead><tr><th>Seviye</th><th>Değer</th></tr></thead>`;
    const tbody = document.createElement('tbody');
    const ROWS: [string, string, string][] = [
      ['r3','R3 (3. Direnç)','res-row'],
      ['r2','R2 (2. Direnç)','res-row'],
      ['r1','R1 (1. Direnç)','res-row'],
      ['pp','PP (Pivot)','pp-row'],
      ['s1','S1 (1. Destek)','sup-row'],
      ['s2','S2 (2. Destek)','sup-row'],
      ['s3','S3 (3. Destek)','sup-row'],
    ];
    ROWS.forEach(([key, label, cls]) => {
      const val = levels[key];
      if (val == null) return;
      const tr = document.createElement('tr');
      tr.className = cls;
      tr.innerHTML = `<td>${esc(label)}</td><td>${fmtNum(val)}</td>`;
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    card.appendChild(table);
    return card;
  };

  pivWrap.appendChild(buildPivotCard('Klasik Pivot', pvt['classic'] as Record<string, unknown> | null));
  pivWrap.appendChild(buildPivotCard('Fibonacci Pivot', pvt['fibonacci'] as Record<string, unknown> | null));
  panel.appendChild(pivWrap);
}

// Osilatör tablosu yardımcısı
function buildTechTable(rows: { name: string; value: string; signal: string | null }[]): HTMLTableElement {
  const table = document.createElement('table');
  table.className = 'tech-table';
  table.innerHTML = `<thead><tr>
    <th>Gösterge</th><th style="text-align:right">Değer</th><th style="text-align:right">Sinyal</th>
  </tr></thead>`;
  const tbody = document.createElement('tbody');
  rows.forEach(row => {
    const tr  = document.createElement('tr');
    const cls = signalCls(row.signal);
    tr.innerHTML = `
      <td class="tname">${esc(row.name)}</td>
      <td class="tval">${esc(row.value)}</td>
      <td class="tsig"><span class="sig-badge ${cls}">${signalTR(row.signal)}</span></td>`;
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  return table;
}

// ─── SEKME: Finansallar ───────────────────────────────────────────────────────

function renderFinansallar(panel: HTMLElement, finData: Record<string, unknown> | null, market: string): void {
  if (market !== 'BIST') {
    panel.innerHTML = '<p class="s360-na-msg" style="padding:20px">Finansal veriler yalnızca BIST hisseleri için mevcut.</p>';
    return;
  }
  if (!finData) {
    panel.innerHTML = '<p class="s360-na-msg" style="padding:20px">Finansal veri bulunamadı veya henüz yüklenmedi.</p>';
    return;
  }

  // Temel oranlar
  const ratios = (finData['ratios'] as Record<string, unknown>) ?? {};
  const grid = document.createElement('div');
  grid.className = 's360-grid';
  grid.appendChild(kvCard('Değerleme Oranları', [
    ['F/K Oranı',         ratios['pe_ratio']        as number | null],
    ['PD/DD',             ratios['pb_ratio']         as number | null],
    ['FD/FAVÖK',          ratios['ev_ebitda']        as number | null],
    ['F/S (Fiy./Satış)',  ratios['ps_ratio']         as number | null],
    ['Temettü Verimi',    ratios['dividend_yield']   as number | null],
  ]));
  grid.appendChild(kvCard('Kârlılık', [
    ['Net Kâr Marjı',     ratios['net_margin']       as number | null],
    ['FAVÖK Marjı',       ratios['ebitda_margin']    as number | null],
    ['Öz Sermaye Kârl.',  ratios['roe']              as number | null],
    ['Aktif Kârlılığı',   ratios['roa']              as number | null],
  ]));
  panel.appendChild(grid);

  // Gelir tablosu
  const incStmt = finData['income_statement'] as Record<string, unknown>[] | null;
  if (incStmt && incStmt.length > 0) {
    const t = document.createElement('div');
    t.className = 'sec-title';
    t.textContent = 'Gelir Tablosu (Son Dönemler)';
    panel.appendChild(t);
    panel.appendChild(buildFinTable(incStmt, ['period','revenue','gross_profit','ebitda','net_income'],
      ['Dönem','Gelir','Brüt Kâr','FAVÖK','Net Kâr']));
  }

  // Bilanço
  const balance = finData['balance_sheet'] as Record<string, unknown>[] | null;
  if (balance && balance.length > 0) {
    const t = document.createElement('div');
    t.className = 'sec-title';
    t.textContent = 'Bilanço (Son Dönemler)';
    panel.appendChild(t);
    panel.appendChild(buildFinTable(balance,
      ['period','total_assets','total_liabilities','equity','net_debt'],
      ['Dönem','Toplam Varlık','Toplam Borç','Öz Sermaye','Net Borç']));
  }
}

function buildFinTable(rows: Record<string, unknown>[], keys: string[], headers: string[]): HTMLElement {
  const card = document.createElement('div');
  card.className = 's360-card';
  card.style.overflowX = 'auto';
  const table = document.createElement('table');
  table.className = 'tech-table';
  table.style.minWidth = '500px';
  const thead = document.createElement('thead');
  thead.innerHTML = '<tr>' + headers.map(h => `<th style="text-align:right">${esc(h)}</th>`).join('') + '</tr>';
  table.appendChild(thead);
  const tbody = document.createElement('tbody');
  rows.forEach(row => {
    const tr = document.createElement('tr');
    tr.innerHTML = keys.map((k, i) => {
      const val = row[k];
      const formatted = val == null ? '—'
        : i === 0 ? esc(String(val))
        : typeof val === 'number' ? fmtNum(val, 0) : esc(String(val));
      return `<td class="tval">${formatted}</td>`;
    }).join('');
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  card.appendChild(table);
  return card;
}

// ─── SEKME: Haberler ─────────────────────────────────────────────────────────

function renderHaberler(panel: HTMLElement, newsItems: Record<string, unknown>[]): void {
  const card = document.createElement('div');
  card.className = 's360-card';
  if (newsItems.length === 0) {
    card.innerHTML = '<p class="s360-na-msg">Bu sembol için haber bulunamadı.</p>';
  } else {
    newsItems.forEach(n => {
      const div = document.createElement('div');
      div.className = 's360-news-item';
      const url  = n['url']       as string | null;
      const head = esc(n['headline'] as string ?? 'Başlıksız');
      div.innerHTML = `
        ${url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${head}</a>` : `<span>${head}</span>`}
        <div class="s360-news-meta">
          ${esc(n['source'] as string ?? '')} · ${timeAgo(n['published_at'] as string ?? null)}
        </div>`;
      card.appendChild(div);
    });
  }
  panel.appendChild(card);
}

// ─── Yardımcılar ─────────────────────────────────────────────────────────────

function kvCard(
  title: string,
  rows: Array<[string, string | number | null, string?]>,
  note?: string,
): HTMLElement {
  const card = document.createElement('div');
  card.className = 's360-card';
  card.innerHTML = `<h3>${esc(title)}</h3>`;
  rows.forEach(([label, val, cls]) => {
    const row = document.createElement('div');
    row.className = 's360-kv';
    const valCls = cls ?? (val == null ? 'na' : '');
    const valStr = val == null ? 'Veri yok'
      : typeof val === 'number' ? fmtNum(val) : esc(String(val));
    row.innerHTML = `<span class="lbl">${esc(label)}</span><span class="val ${esc(valCls)}">${valStr}</span>`;
    card.appendChild(row);
  });
  if (note) {
    const n = document.createElement('div');
    n.style.cssText = 'font-size:10px;color:var(--text-dim);margin-top:8px';
    n.textContent = note;
    card.appendChild(n);
  }
  return card;
}

/** BIST 30 içinden benzer semboller (aynı sembol hariç, ilk 6). */
function getSimilarSymbols(symbol: string, market: string): string[] {
  if (market !== 'BIST') return [];
  const BIST30 = [
    'AKBNK','ARCLK','ASELS','BIMAS','DOHOL','EKGYO','EREGL',
    'FROTO','GARAN','GUBRF','HALKB','KCHOL','KRDMD','MGROS',
    'OTKAR','PETKM','PGSUS','SAHOL','SASA','SISE','SKBNK',
    'SOKM','TAVHL','TCELL','THYAO','TKFEN','TOASO','TUPRS',
    'VAKBN','YKBNK',
  ];
  return BIST30.filter(s => s !== symbol).slice(0, 6);
}
