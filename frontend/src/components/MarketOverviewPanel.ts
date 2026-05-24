/**
 * MarketOverviewPanel — Piyasa genel görünümü ve rejim skoru paneli.
 *
 * API:
 *   GET /api/market/overview  — fiyat özeti (BIST, döviz, kripto, emtia, global)
 *   GET /api/market/regime    — piyasa rejim skoru (0–100)
 *
 * Her 60 saniyede bir otomatik yenileme.
 */

const REFRESH_MS = 60_000;

// ─── Tipler ──────────────────────────────────────────────────────────────────

interface MarketEntry {
  symbol: string;
  label: string;
  last: number | null;
  change_pct: number | null;
  quality: string;
  message?: string;
}

interface OverviewData {
  bist:        MarketEntry[];
  forex:       MarketEntry[];
  crypto:      MarketEntry[];
  commodities: MarketEntry[];
  global:      MarketEntry[];
  fetched_at:  string;
}

interface RegimeData {
  score:      number;
  regime:     string;
  regime_en:  string;
  benchmark:  string;
  components: Record<string, number>;
  details:    Record<string, unknown>;
  max_score:  number;
  fetched_at: string;
  disclaimer: string;
}

// ─── Yardımcı ────────────────────────────────────────────────────────────────

function esc(s: unknown): string {
  return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function fmtN(v: number | null | undefined, d = 2): string {
  if (v == null || isNaN(v)) return '—';
  return v.toLocaleString('tr-TR', { minimumFractionDigits: d, maximumFractionDigits: d });
}

function fmtP(v: number | null | undefined): string {
  if (v == null || isNaN(v)) return '—';
  return (v >= 0 ? '+' : '') + fmtN(v, 2) + '%';
}

// ─── CSS ─────────────────────────────────────────────────────────────────────

const CSS = `
<style>
.mov-wrap {
  max-width: 1100px; margin: 0 auto;
  padding: 16px 14px 60px;
  color: var(--text, #94A3B8);
  font-family: var(--font, system-ui, sans-serif);
  font-size: 13px;
}
/* ── Header ── */
.mov-header {
  display: flex; align-items: center; gap: 10px; margin-bottom: 18px;
}
.mov-header h2 { font-size: 18px; font-weight: 700; color: var(--text-bold, #F8FAFC); margin: 0; }
.mov-refresh-btn {
  margin-left: auto; padding: 4px 12px; font-size: 12px; border-radius: 6px;
  background: none; border: 1px solid var(--border, rgba(255,255,255,.15));
  color: var(--text-dim); cursor: pointer;
}
.mov-refresh-btn:hover { color: var(--text); }
.mov-last-update { font-size: 10px; color: var(--text-dim); }
/* ── Rejim skoru ── */
.mov-regime-card {
  background: var(--panel, #131722);
  border: 1px solid var(--border, rgba(255,255,255,.08));
  border-radius: 12px; padding: 16px 20px; margin-bottom: 18px;
  display: flex; align-items: center; gap: 20px; flex-wrap: wrap;
}
.mov-regime-score-ring {
  width: 72px; height: 72px; flex-shrink: 0;
}
.mov-regime-info { flex: 1; min-width: 160px; }
.mov-regime-label {
  font-size: 17px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em;
}
.mov-regime-bench { font-size: 11px; color: var(--text-dim); margin-top: 2px; }
.mov-regime-components { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
.mov-comp-pill {
  padding: 2px 9px; border-radius: 20px; font-size: 10px; font-weight: 600;
  background: rgba(255,255,255,.06); color: var(--text-dim);
}
.mov-regime-disclaimer {
  font-size: 10px; color: var(--text-dim); margin-top: 10px; line-height: 1.4;
  padding: 6px 10px; background: rgba(239,68,68,.05); border-radius: 6px;
}
/* ── Progress bar ── */
.mov-regime-bar-wrap {
  flex: 1; min-width: 200px;
}
.mov-regime-bar-track {
  height: 8px; border-radius: 4px; background: rgba(255,255,255,.08); position: relative;
}
.mov-regime-bar-fill {
  height: 8px; border-radius: 4px; position: absolute; left: 0; top: 0;
  transition: width .4s ease;
}
.mov-regime-bar-labels {
  display: flex; justify-content: space-between; font-size: 10px;
  color: var(--text-dim); margin-top: 4px;
}
/* ── Gruplar ── */
.mov-groups { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.mov-group-card {
  background: var(--panel, #131722);
  border: 1px solid var(--border, rgba(255,255,255,.08));
  border-radius: 10px; padding: 12px 14px;
}
.mov-group-card h3 {
  font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: .06em;
  color: var(--text-dim); margin: 0 0 10px;
}
/* ── Fiyat satırı ── */
.mov-entry {
  display: flex; align-items: baseline; justify-content: space-between;
  padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,.03);
}
.mov-entry:last-child { border-bottom: none; }
.mov-entry-label { color: var(--text, #94A3B8); font-size: 12px; flex: 1; }
.mov-entry-price { font-weight: 500; color: var(--text-bold, #F8FAFC); text-align: right; font-size: 13px; }
.mov-entry-chg   { font-size: 12px; min-width: 60px; text-align: right; }
.mov-entry-chg.pos { color: var(--green, #10B981); }
.mov-entry-chg.neg { color: var(--red, #EF4444); }
.mov-entry-chg.neu { color: var(--text-dim, #64748B); }
.mov-quality-stale { opacity: .5; }
.mov-msg { font-size: 11px; color: var(--text-dim); font-style: italic; padding: 4px 0; }
/* ── Loading / error ── */
.mov-loading { padding: 40px; text-align: center; color: var(--text-dim); }
.mov-error   { padding: 40px; text-align: center; color: var(--red, #EF4444); }
</style>`;

// ─── Component ───────────────────────────────────────────────────────────────

export class MarketOverviewPanel {
  private container: HTMLElement;
  private refreshTimer: ReturnType<typeof setInterval> | null = null;
  private overview: OverviewData | null = null;
  private regime: RegimeData | null = null;
  private loading = true;

  constructor(container: HTMLElement) {
    this.container = container;
    this.container.innerHTML = `${CSS}<div class="mov-wrap"><div class="mov-loading">Yükleniyor…</div></div>`;
    void this.fetchAll();
    this.refreshTimer = setInterval(() => void this.fetchAll(), REFRESH_MS);
  }

  destroy(): void {
    if (this.refreshTimer !== null) clearInterval(this.refreshTimer);
  }

  // ─── Veri çekimi ─────────────────────────────────────────────────────────

  private async fetchAll(): Promise<void> {
    try {
      const [ovRes, rgRes] = await Promise.allSettled([
        fetch('/api/market/overview'),
        fetch('/api/market/regime'),
      ]);
      if (ovRes.status === 'fulfilled' && ovRes.value.ok) {
        this.overview = await ovRes.value.json() as OverviewData;
      }
      if (rgRes.status === 'fulfilled' && rgRes.value.ok) {
        this.regime = await rgRes.value.json() as RegimeData;
      }
      this.loading = false;
      this.render();
    } catch {
      this.loading = false;
      this.render();
    }
  }

  // ─── Render ──────────────────────────────────────────────────────────────

  private render(): void {
    const wrap = this.container.querySelector('.mov-wrap') ?? (() => {
      const d = document.createElement('div');
      d.className = 'mov-wrap';
      this.container.innerHTML = CSS;
      this.container.appendChild(d);
      return d;
    })();

    if (this.loading) {
      wrap.innerHTML = '<div class="mov-loading">Yükleniyor…</div>';
      return;
    }

    const ts = this.overview?.fetched_at
      ? new Date(this.overview.fetched_at).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      : '—';

    wrap.innerHTML = `
      <!-- Header -->
      <div class="mov-header">
        <h2>Piyasa Genel Görünümü</h2>
        <span class="mov-last-update">Son güncelleme: ${ts}</span>
        <button class="mov-refresh-btn" id="mov-refresh">↺ Yenile</button>
      </div>

      <!-- Rejim Skoru -->
      ${this.regimeHTML()}

      <!-- Fiyat Grupları -->
      <div class="mov-groups">
        ${this.groupHTML('BIST', this.overview?.bist ?? [])}
        ${this.groupHTML('Döviz', this.overview?.forex ?? [])}
        ${this.groupHTML('Kripto', this.overview?.crypto ?? [])}
        ${this.groupHTML('Emtia', this.overview?.commodities ?? [])}
        ${this.groupHTML('Küresel', this.overview?.global ?? [])}
      </div>

      <div style="font-size:10px;color:var(--text-dim);margin-top:14px;line-height:1.5">
        ⚠️ Veriler gecikmeli olabilir. Yatırım tavsiyesi değildir. Borsada işlem yapmadan önce lisanslı aracı kuruluşa danışınız.
      </div>`;

    wrap.querySelector('#mov-refresh')?.addEventListener('click', () => void this.fetchAll());
  }

  // ─── Rejim HTML ──────────────────────────────────────────────────────────

  private regimeHTML(): string {
    if (!this.regime) {
      return `<div class="mov-regime-card">
        <span style="color:var(--text-dim);font-size:12px">Rejim skoru alınamadı.</span>
      </div>`;
    }
    const r = this.regime;
    const score = r.score;
    const color = score >= 70 ? '#10B981' : score >= 55 ? '#34D399' : score >= 45 ? '#F59E0B' : score >= 30 ? '#F97316' : '#EF4444';
    const regimeTR: Record<string, string> = {
      strong_bull: 'Güçlü Yükseliş',
      bull:        'Yükseliş',
      sideways:    'Yatay',
      bear:        'Düşüş',
      strong_bear: 'Güçlü Düşüş',
    };
    const label = regimeTR[r.regime_en] ?? r.regime;

    // SVG ring
    const R = 30; const circ = 2 * Math.PI * R;
    const dash = (score / 100) * circ;
    const ring = `
      <svg viewBox="0 0 72 72" class="mov-regime-score-ring">
        <circle cx="36" cy="36" r="${R}" fill="none" stroke="rgba(255,255,255,.08)" stroke-width="8"/>
        <circle cx="36" cy="36" r="${R}" fill="none" stroke="${color}" stroke-width="8"
          stroke-dasharray="${dash.toFixed(1)} ${circ.toFixed(1)}"
          stroke-linecap="round" transform="rotate(-90 36 36)"/>
        <text x="36" y="40" text-anchor="middle" font-size="16" font-weight="700" fill="${color}">${score}</text>
      </svg>`;

    const compPills = Object.entries(r.components).map(([k, v]) => {
      const labels: Record<string, string> = {
        rsi: 'RSI', ema_trend: 'EMA200', ema_50_trend: 'EMA50',
        volatility: 'Volat.', momentum: 'Mom.',
      };
      return `<span class="mov-comp-pill">${labels[k] ?? k}: ${v}</span>`;
    }).join('');

    const details = r.details as Record<string, unknown>;

    return `
      <div class="mov-regime-card">
        ${ring}
        <div class="mov-regime-info">
          <div class="mov-regime-label" style="color:${color}">${esc(label)}</div>
          <div class="mov-regime-bench">Benchmark: ${esc(r.benchmark)} · Skor: ${score}/100</div>
          ${details['rsi_14'] ? `<div style="font-size:11px;color:var(--text-dim);margin-top:3px">RSI: ${details['rsi_14']} · ${details['above_ema200'] ? 'EMA200 üstünde ✓' : 'EMA200 altında ✗'}${details['momentum_20d_pct'] != null ? ` · 20g Mom: ${String(details['momentum_20d_pct'])}%` : ''}</div>` : ''}
          <div class="mov-regime-components">${compPills}</div>
        </div>
        <div class="mov-regime-bar-wrap">
          <div class="mov-regime-bar-track">
            <div class="mov-regime-bar-fill" style="width:${score}%;background:${color}"></div>
          </div>
          <div class="mov-regime-bar-labels">
            <span>Güçlü Düşüş</span><span>Yatay</span><span>Güçlü Yükseliş</span>
          </div>
        </div>
        <div class="mov-regime-disclaimer" style="width:100%">${esc(r.disclaimer)}</div>
      </div>`;
  }

  // ─── Grup HTML ───────────────────────────────────────────────────────────

  private groupHTML(title: string, entries: MarketEntry[]): string {
    if (entries.length === 0) return '';
    const rows = entries.map(e => {
      if (e.message && e.last == null) {
        return `<div class="mov-entry">
          <span class="mov-entry-label">${esc(e.label)}</span>
          <span class="mov-msg">${esc(e.message)}</span>
        </div>`;
      }
      const chgCls = e.change_pct == null ? 'neu' : e.change_pct >= 0 ? 'pos' : 'neg';
      const staleCls = e.quality === 'stale' ? 'mov-quality-stale' : '';
      return `
        <div class="mov-entry ${staleCls}">
          <span class="mov-entry-label">${esc(e.label)}</span>
          <span class="mov-entry-price">${fmtN(e.last)}</span>
          <span class="mov-entry-chg ${chgCls}">${fmtP(e.change_pct)}</span>
        </div>`;
    }).join('');

    return `
      <div class="mov-group-card">
        <h3>${esc(title)}</h3>
        ${rows}
      </div>`;
  }
}
