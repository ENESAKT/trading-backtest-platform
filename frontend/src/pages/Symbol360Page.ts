/**
 * Symbol 360 — Sembol detay sayfası.
 * Route: /terminal/symbol/:market/:symbol
 *
 * Gösterilen veriler:
 *  - Fiyat özeti (son kapanış, günlük değişim, hacim)
 *  - Temel veriler (F/K, PD/DD, temettü verimi) — backend'de varsa
 *  - Son 5 haber
 *  - Teknik özet (RSI / MACD / Bollinger durumu)
 *  - Benzer hisseler (aynı sektör / indeks içinden)
 */

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
  const s = (v >= 0 ? '+' : '') + fmtNum(v, d) + '%';
  return s;
}

function timeAgo(iso: string | null | undefined): string {
  if (!iso) return '';
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return `${Math.round(diff)}s`;
  if (diff < 3600) return `${Math.round(diff / 60)}dk`;
  if (diff < 86400) return `${Math.round(diff / 3600)}sa`;
  return `${Math.round(diff / 86400)}g`;
}

// ─── CSS (inline, tema değişkenlerini kullanıyor) ────────────────────────────

const CSS = `
<style>
.s360-wrap {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px 16px 60px;
  color: var(--text, #94A3B8);
  font-family: var(--font, system-ui, sans-serif);
}
.s360-back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-dim, #64748B);
  font-size: 13px;
  text-decoration: none;
  margin-bottom: 16px;
  cursor: pointer;
  background: none;
  border: none;
  padding: 0;
}
.s360-back:hover { color: var(--text, #94A3B8); }
.s360-header {
  display: flex;
  align-items: baseline;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}
.s360-symbol {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-bold, #F8FAFC);
}
.s360-name { font-size: 14px; color: var(--text-dim, #64748B); }
.s360-price {
  font-size: 26px;
  font-weight: 600;
  color: var(--text-bold, #F8FAFC);
}
.s360-chg { font-size: 15px; }
.s360-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
  margin-bottom: 22px;
}
.s360-card {
  background: var(--panel, #131722);
  border: 1px solid var(--border, rgba(255,255,255,.08));
  border-radius: 10px;
  padding: 16px 18px;
}
.s360-card h3 {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--text-dim, #64748B);
  margin: 0 0 12px;
}
.s360-kv { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 7px; }
.s360-kv:last-child { margin-bottom: 0; }
.s360-kv .label { color: var(--text, #94A3B8); }
.s360-kv .val { font-weight: 500; color: var(--text-bold, #F8FAFC); }
.s360-kv .val.pos { color: var(--green, #10B981); }
.s360-kv .val.neg { color: var(--red, #EF4444); }
.s360-kv .val.na  { color: var(--text-dim, #64748B); font-style: italic; }
.s360-news-item {
  padding: 10px 0;
  border-bottom: 1px solid var(--border, rgba(255,255,255,.06));
  font-size: 13px;
}
.s360-news-item:last-child { border-bottom: none; }
.s360-news-item a { color: var(--text-bold, #F8FAFC); text-decoration: none; }
.s360-news-item a:hover { text-decoration: underline; }
.s360-news-meta { font-size: 11px; color: var(--text-dim, #64748B); margin-top: 3px; }
.s360-tech-signal {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}
.s360-tech-signal.AL { background: rgba(16,185,129,.15); color: #10B981; }
.s360-tech-signal.SAT { background: rgba(239,68,68,.15); color: #EF4444; }
.s360-tech-signal.NÖTR { background: rgba(148,163,184,.12); color: #94A3B8; }
.s360-similar { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
.s360-sim-chip {
  background: var(--border, rgba(255,255,255,.06));
  border-radius: 6px;
  padding: 5px 12px;
  font-size: 12px;
  cursor: pointer;
  color: var(--text, #94A3B8);
  border: none;
}
.s360-sim-chip:hover { background: rgba(59,130,246,.15); color: var(--blue, #3B82F6); }
.s360-loading { color: var(--text-dim, #64748B); padding: 40px; text-align: center; }
.s360-error  { color: var(--red, #EF4444); padding: 40px; text-align: center; }
</style>
`;

// ─── Entry point ─────────────────────────────────────────────────────────────

export async function renderSymbol360Page(container: HTMLElement): Promise<void> {
  // /terminal/symbol/:market/:symbol
  const parts = window.location.pathname.split('/').filter(Boolean);
  // parts: ['terminal','symbol','BIST','THYAO']
  const market = (parts[2] ?? 'BIST').toUpperCase();
  const symbol = (parts[3] ?? '').toUpperCase();

  if (!symbol) {
    container.innerHTML = `${CSS}<div class="s360-wrap"><div class="s360-error">Geçersiz sembol.</div></div>`;
    return;
  }

  container.innerHTML = `${CSS}<div class="s360-wrap"><div class="s360-loading">Yükleniyor…</div></div>`;
  const wrap = container.querySelector('.s360-wrap')!;

  // Geri butonu
  const backBtn = document.createElement('button');
  backBtn.className = 's360-back';
  backBtn.innerHTML = '← Geri';
  backBtn.addEventListener('click', () => history.back());

  wrap.innerHTML = '';
  wrap.appendChild(backBtn);

  // Tüm fetch işlemleri paralel
  const [priceRes, newsRes, techRes] = await Promise.allSettled([
    fetch(`/api/quote?symbol=${encodeURIComponent(symbol)}&market=${encodeURIComponent(market)}`),
    fetch(`/api/news?symbol=${encodeURIComponent(symbol)}&limit=5`),
    fetch(`/api/technical/summary?symbol=${encodeURIComponent(symbol)}&market=${encodeURIComponent(market)}&timeframe=1d`),
  ]);

  // ── Header ───────────────────────────────────────────────────────────────

  let lastPrice: number | null = null;
  let changePct: number | null = null;
  let volume: number | null = null;
  let symbolName = symbol;

  if (priceRes.status === 'fulfilled' && priceRes.value.ok) {
    try {
      const d = await priceRes.value.json() as Record<string, unknown>;
      lastPrice  = (d['last_price'] as number) ?? null;
      changePct  = (d['change_pct'] as number) ?? null;
      volume     = (d['volume'] as number) ?? null;
      symbolName = (d['name'] as string) || symbol;
    } catch { /* header will show dashes */ }
  }

  const chgCls = changePct == null ? '' : changePct >= 0 ? 'pos' : 'neg';
  const header = document.createElement('div');
  header.className = 's360-header';
  header.innerHTML = `
    <span class="s360-symbol">${esc(symbol)}</span>
    <span class="s360-name">${esc(symbolName !== symbol ? symbolName : '')}</span>
    <span class="s360-price">${lastPrice != null ? fmtNum(lastPrice) : '—'}</span>
    <span class="s360-chg ${chgCls}">${fmtPct(changePct)}</span>
  `;
  wrap.appendChild(header);

  // ── Grid ─────────────────────────────────────────────────────────────────

  const grid = document.createElement('div');
  grid.className = 's360-grid';

  // Fiyat özeti kartı
  grid.appendChild(makeCard('Fiyat Özeti', [
    ['Son Fiyat',   lastPrice != null ? fmtNum(lastPrice) : null],
    ['Günlük Değ.', changePct != null ? fmtPct(changePct) : null, chgCls],
    ['Hacim',       volume != null ? fmtNum(volume, 0) : null],
    ['Piyasa',      market],
  ]));

  // Temel veriler (şimdilik placeholder — harici veri gerektiriyor)
  grid.appendChild(makeCard('Temel Veriler', [
    ['F/K Oranı',    null, 'na'],
    ['PD/DD',        null, 'na'],
    ['Temettü Ver.', null, 'na'],
  ], 'Temel veriler henüz bağlı değil'));

  // Teknik özet kartı
  const techCard = document.createElement('div');
  techCard.className = 's360-card';
  techCard.innerHTML = '<h3>Teknik Özet</h3>';
  if (techRes.status === 'fulfilled' && techRes.value.ok) {
    try {
      const t = await techRes.value.json() as Record<string, unknown>;
      const rating = String(t['overall_rating'] ?? 'NÖTR').toUpperCase();
      const rsi    = t['rsi_14'] as number | null;
      const macdSig = t['macd_signal'] as string | null;
      const bbStat  = t['bb_status'] as string | null;
      techCard.innerHTML += `
        <div class="s360-kv"><span class="label">Genel Sinyal</span>
          <span class="s360-tech-signal ${esc(rating)}">${esc(rating)}</span></div>
        <div class="s360-kv"><span class="label">RSI (14)</span>
          <span class="val ${rsi != null && rsi < 30 ? 'pos' : rsi != null && rsi > 70 ? 'neg' : ''}">${fmtNum(rsi, 1)}</span></div>
        <div class="s360-kv"><span class="label">MACD Sinyal</span>
          <span class="val">${esc(macdSig ?? '—')}</span></div>
        <div class="s360-kv"><span class="label">Bollinger</span>
          <span class="val">${esc(bbStat ?? '—')}</span></div>
      `;
    } catch {
      techCard.innerHTML += '<div style="font-size:12px;color:var(--text-dim)">Teknik veri alınamadı.</div>';
    }
  } else {
    techCard.innerHTML += '<div style="font-size:12px;color:var(--text-dim)">Teknik veri mevcut değil.</div>';
  }
  grid.appendChild(techCard);

  // Benzer hisseler (aynı ülke indeksi içinden)
  const simCard = document.createElement('div');
  simCard.className = 's360-card';
  simCard.innerHTML = '<h3>Benzer Hisseler</h3>';
  const similar = getSimilarSymbols(symbol, market);
  if (similar.length > 0) {
    const simWrap = document.createElement('div');
    simWrap.className = 's360-similar';
    similar.forEach(sym => {
      const btn = document.createElement('button');
      btn.className = 's360-sim-chip';
      btn.textContent = sym;
      btn.addEventListener('click', () => {
        window.location.href = `/terminal/symbol/${market}/${sym}`;
      });
      simWrap.appendChild(btn);
    });
    simCard.appendChild(simWrap);
  } else {
    simCard.innerHTML += '<div style="font-size:12px;color:var(--text-dim)">Benzer sembol bulunamadı.</div>';
  }
  grid.appendChild(simCard);

  wrap.appendChild(grid);

  // ── Son 5 haber ──────────────────────────────────────────────────────────

  const newsCard = document.createElement('div');
  newsCard.className = 's360-card';
  newsCard.style.gridColumn = '1 / -1';
  newsCard.innerHTML = '<h3>Son Haberler</h3>';

  if (newsRes.status === 'fulfilled' && newsRes.value.ok) {
    try {
      const nd = await newsRes.value.json() as { news?: Array<Record<string, unknown>> };
      const items = nd.news?.slice(0, 5) ?? [];
      if (items.length === 0) {
        newsCard.innerHTML += '<div style="font-size:12px;color:var(--text-dim)">Bu sembol için haber bulunamadı.</div>';
      } else {
        items.forEach(n => {
          const div = document.createElement('div');
          div.className = 's360-news-item';
          const url  = n['url'] as string | null;
          const head = esc(n['headline'] as string ?? 'Başlıksız');
          div.innerHTML = `
            ${url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${head}</a>` : `<span>${head}</span>`}
            <div class="s360-news-meta">
              ${esc(n['source'] as string ?? '')} · ${timeAgo(n['published_at'] as string ?? null)}
            </div>`;
          newsCard.appendChild(div);
        });
      }
    } catch {
      newsCard.innerHTML += '<div style="font-size:12px;color:var(--text-dim)">Haberler yüklenemedi.</div>';
    }
  } else if (newsRes.status === 'fulfilled' && newsRes.value.status === 401) {
    newsCard.innerHTML += '<div style="font-size:12px;color:var(--text-dim)">Haberleri görmek için giriş yapın.</div>';
  } else {
    newsCard.innerHTML += '<div style="font-size:12px;color:var(--text-dim)">Haberler mevcut değil.</div>';
  }

  wrap.appendChild(newsCard);
}

// ─── Yardımcılar ─────────────────────────────────────────────────────────────

function makeCard(
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
    row.innerHTML = `<span class="label">${esc(label)}</span><span class="val ${esc(valCls)}">${esc(val ?? 'Veri yok')}</span>`;
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

/** BIST 30 sembolleri içinden aynı sembolü hariç tut, ilk 6'yı döndür. */
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
