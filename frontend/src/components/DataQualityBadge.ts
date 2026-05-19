/**
 * DataQualityBadge — veri kalitesini tek bakışta gösteren rozet bileşeni.
 *
 * Durumlar:
 *   ok        → yeşil   "Canlı" veya "Gerçek Veri"
 *   warning   → sarı    "Gecikmeli" veya "Güvenilmez"
 *   blocked   → kırmızı "Bloklandı"
 *   unknown   → gri     "Bilinmiyor"
 *   demo      → mor     "Demo"
 *   cache     → mavi    "Cache"
 *   licensed  → teal    "Lisanslı"
 *
 * Kullanım:
 *   const badge = new DataQualityBadge(containerEl);
 *   badge.update(dataTruth);
 *
 *   // veya basit string ile:
 *   badge.setStatus('warning', 'Gecikmeli 15dk');
 */

import type { DataTruth, DataQualityStatus } from '../types.js';

export type BadgeVariant =
  | 'ok'
  | 'warning'
  | 'blocked'
  | 'unknown'
  | 'demo'
  | 'cache'
  | 'licensed';

interface BadgeConfig {
  label:   string;
  icon:    string;   // unicode veya kısa metin
  cssClass: string;
}

const BADGE_CONFIG: Record<BadgeVariant, BadgeConfig> = {
  ok:       { label: 'Gerçek Veri',  icon: '●', cssClass: 'dqb-ok'       },
  warning:  { label: 'Uyarı',        icon: '▲', cssClass: 'dqb-warning'  },
  blocked:  { label: 'Bloklandı',    icon: '✕', cssClass: 'dqb-blocked'  },
  unknown:  { label: 'Bilinmiyor',   icon: '?', cssClass: 'dqb-unknown'  },
  demo:     { label: 'Demo',         icon: '◆', cssClass: 'dqb-demo'     },
  cache:    { label: 'Cache',        icon: '⟳', cssClass: 'dqb-cache'    },
  licensed: { label: 'Lisanslı',     icon: '✓', cssClass: 'dqb-licensed' },
};

function qualityToVariant(truth: DataTruth): BadgeVariant {
  if (truth.source_type === 'sample') return 'demo';
  if (truth.source_type === 'cache')  return 'cache';
  if (truth.source_type === 'licensed') return 'licensed';
  const qs = truth.quality_status as DataQualityStatus;
  if (qs === 'ok')      return truth.is_live ? 'ok' : 'ok';
  if (qs === 'warning') return 'warning';
  if (qs === 'blocked') return 'blocked';
  return 'unknown';
}

function buildTooltip(truth: DataTruth): string {
  const lines: string[] = [];
  lines.push(`Sembol: ${truth.symbol} (${truth.timeframe})`);
  lines.push(`Sağlayıcı: ${truth.provider}`);
  if (truth.is_delayed) lines.push(`Gecikme: ${truth.delay_minutes} dakika`);
  if (truth.coverage_pct > 0) lines.push(`Kapsam: %${truth.coverage_pct.toFixed(1)}`);
  if (truth.gap_count > 0)    lines.push(`Boşluk sayısı: ${truth.gap_count}`);
  if (truth.is_derived)       lines.push(`Türetildi: ${truth.source_timeframe}'dan`);
  if (truth.license_note)     lines.push(`Lisans: ${truth.license_note}`);
  if (truth.warnings.length)  lines.push(`Uyarı: ${truth.warnings.join(' | ')}`);
  if (truth.fetched_at)       lines.push(`Güncelleme: ${new Date(truth.fetched_at).toLocaleTimeString('tr-TR')}`);
  return lines.join('\n');
}

export class DataQualityBadge {
  private el: HTMLElement;
  private drawerEl: HTMLElement | null = null;

  constructor(container: HTMLElement, opts: { showDrawer?: boolean } = {}) {
    this.el = document.createElement('span');
    this.el.className = 'dqb dqb-unknown';
    this.el.setAttribute('role', 'status');
    this.el.setAttribute('aria-label', 'Veri kalitesi: bilinmiyor');
    container.appendChild(this.el);

    if (opts.showDrawer) {
      this.drawerEl = document.createElement('div');
      this.drawerEl.className = 'dqb-drawer';
      this.drawerEl.hidden = true;
      container.appendChild(this.drawerEl);

      this.el.style.cursor = 'pointer';
      this.el.addEventListener('click', (e) => {
        e.stopPropagation();
        if (this.drawerEl) {
          this.drawerEl.hidden = !this.drawerEl.hidden;
        }
      });
      document.addEventListener('click', () => {
        if (this.drawerEl) this.drawerEl.hidden = true;
      });
    }
  }

  /** DataTruth nesnesinden rozeti güncelle. */
  update(truth: DataTruth): void {
    const variant = qualityToVariant(truth);
    const cfg     = BADGE_CONFIG[variant];

    // Eski CSS sınıflarını temizle
    this.el.className = `dqb ${cfg.cssClass}`;
    this.el.textContent = `${cfg.icon} ${cfg.label}`;
    this.el.title = buildTooltip(truth);
    this.el.setAttribute('aria-label', `Veri kalitesi: ${cfg.label}`);

    if (this.drawerEl) {
      this.drawerEl.innerHTML = this._buildDrawerHtml(truth);
    }
  }

  /** Basit string ile güncelle (DataTruth olmadan hızlı kullanım). */
  setStatus(variant: BadgeVariant, label?: string): void {
    const cfg = BADGE_CONFIG[variant];
    this.el.className = `dqb ${cfg.cssClass}`;
    this.el.textContent = `${cfg.icon} ${label ?? cfg.label}`;
    this.el.title = label ?? cfg.label;
  }

  /** Rozeti gizle. */
  hide(): void { this.el.hidden = true; }
  /** Rozeti göster. */
  show(): void { this.el.hidden = false; }

  private _buildDrawerHtml(truth: DataTruth): string {
    const rows: string[] = [];
    const row = (label: string, value: string) =>
      `<tr><td class="dqb-drawer-lbl">${label}</td><td class="dqb-drawer-val">${value}</td></tr>`;

    rows.push(row('Sembol',      `${truth.symbol}`));
    rows.push(row('Timeframe',   truth.timeframe));
    rows.push(row('Sağlayıcı',  truth.provider));
    rows.push(row('Kaynak tipi', truth.source_type));
    rows.push(row('Gerçek veri', truth.is_real ? '✓ Evet' : '✕ Hayır'));
    if (truth.is_delayed)
      rows.push(row('Gecikme', `${truth.delay_minutes} dk`));
    rows.push(row('Kapsam', `%${truth.coverage_pct.toFixed(1)}`));
    if (truth.gap_count > 0)
      rows.push(row('Boşluk', `${truth.gap_count} bar`));
    if (truth.is_derived)
      rows.push(row('Türetme', `${truth.source_timeframe} → ${truth.timeframe}`));
    if (truth.adjusted_for_splits)
      rows.push(row('Bölünme düzeltmesi', '✓'));
    if (truth.adjusted_for_dividends)
      rows.push(row('Temettü düzeltmesi', '✓'));
    if (truth.license_note)
      rows.push(row('Lisans', truth.license_note));
    if (truth.fetched_at)
      rows.push(row('Güncelleme', new Date(truth.fetched_at).toLocaleString('tr-TR')));

    const warnHtml = truth.warnings.length
      ? `<div class="dqb-drawer-warnings">${truth.warnings.map(w => `<p>⚠ ${w}</p>`).join('')}</div>`
      : '';

    return `
      <div class="dqb-drawer-header">Veri Kalitesi Detayı</div>
      <table class="dqb-drawer-table">${rows.join('')}</table>
      ${warnHtml}
    `;
  }

  /** Statik yardımcı: HTML string olarak rozet döndürür (SSR/template için). */
  static renderStatic(variant: BadgeVariant, label?: string): string {
    const cfg = BADGE_CONFIG[variant];
    const lbl = label ?? cfg.label;
    return `<span class="dqb ${cfg.cssClass}" title="${lbl}">${cfg.icon} ${lbl}</span>`;
  }
}

// ─── CSS enjeksiyonu ─────────────────────────────────────────────────────────
// Bileşen ilk kez import edildiğinde <style> etiketi eklenir.

(function injectStyles() {
  if (document.getElementById('dqb-styles')) return;
  const style = document.createElement('style');
  style.id = 'dqb-styles';
  style.textContent = `
    .dqb {
      display: inline-flex; align-items: center; gap: 4px;
      font-size: 11px; font-weight: 600; padding: 2px 8px;
      border-radius: 99px; border: 1px solid transparent;
      white-space: nowrap; line-height: 1.6; user-select: none;
    }
    .dqb-ok       { background:rgba(16,185,129,0.15); color:#34d399; border-color:rgba(16,185,129,0.3); }
    .dqb-warning  { background:rgba(245,158,11,0.15); color:#fbbf24; border-color:rgba(245,158,11,0.3); }
    .dqb-blocked  { background:rgba(239,68,68,0.15);  color:#f87171; border-color:rgba(239,68,68,0.3);  }
    .dqb-unknown  { background:rgba(107,114,128,0.15);color:#9ca3af; border-color:rgba(107,114,128,0.3);}
    .dqb-demo     { background:rgba(139,92,246,0.15); color:#a78bfa; border-color:rgba(139,92,246,0.3); }
    .dqb-cache    { background:rgba(59,130,246,0.15); color:#60a5fa; border-color:rgba(59,130,246,0.3); }
    .dqb-licensed { background:rgba(20,184,166,0.15); color:#2dd4bf; border-color:rgba(20,184,166,0.3); }

    .dqb-drawer {
      position: absolute; z-index: 200; min-width: 280px;
      background: var(--panel-bg, #161b26);
      border: 1px solid var(--border, #2a3347);
      border-radius: 8px; padding: 12px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.4);
      font-size: 12px;
    }
    .dqb-drawer-header {
      font-weight: 600; color: var(--text-bold, #e2e8f0);
      margin-bottom: 8px; padding-bottom: 6px;
      border-bottom: 1px solid var(--border, #2a3347);
    }
    .dqb-drawer-table { width: 100%; border-collapse: collapse; }
    .dqb-drawer-lbl   { color: var(--text-dim, #6b7280); padding: 3px 8px 3px 0; }
    .dqb-drawer-val   { color: var(--text, #cbd5e1); text-align: right; padding: 3px 0; }
    .dqb-drawer-warnings { margin-top: 8px; }
    .dqb-drawer-warnings p {
      font-size: 11px; color: #fbbf24; margin: 3px 0; line-height: 1.4;
    }
  `;
  document.head.appendChild(style);
})();
