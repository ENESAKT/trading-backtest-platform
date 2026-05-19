import { pageShell } from './pageUtils.js';
import { analytics } from '../core/Analytics.js';
import { i18n } from '../i18n/index.js';

const DEMO_BARS = [18,24,21,29,34,31,38,43,39,46,52,48,57,61,58,66,70,64,73,78,75,82,88,84,91,96,93,101,108,104];

const FEATURES = [
  {
    icon: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" stroke-width="1.8"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>`,
    title: 'Teknik Grafik',
    desc: 'RSI, MACD, Bollinger, EMA/SMA ve 20+ göstergeyle profesyonel analiz. Mum, çizgi ve alan grafikleri.',
    badge: 'Ücretsiz',
  },
  {
    icon: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
    title: 'Backtest Pro',
    desc: 'Stratejini geçmiş veride test et. Al/sat noktaları, kar/zarar çizgileri ve performans metrikleri.',
    badge: 'Ücretsiz — günde 10',
  },
  {
    icon: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" stroke-width="1.8"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>`,
    title: 'KAP Haberleri',
    desc: 'Gerçek zamanlı KAP açıklamaları, finansal raporlar ve şirket haberleri doğrudan grafik panelinde.',
    badge: 'Ücretsiz',
  },
  {
    icon: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" stroke-width="1.8"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
    title: 'Mali Analiz',
    desc: 'Bilanço, gelir tablosu, nakit akışı ve KAP finansal verileri. Şirket şirket karşılaştırma.',
    badge: 'Ücretsiz',
  },
  {
    icon: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" stroke-width="1.8"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`,
    title: 'Sinyal Akışı',
    desc: 'Stratejilerden otomatik üretilen al/sat sinyalleri, WebSocket ile anlık iletim.',
    badge: 'Pro',
  },
  {
    icon: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" stroke-width="1.8"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>`,
    title: 'Eğitimler',
    desc: '57 eğitim içeriği: teknik analiz temelleri, strateji geliştirme ve risk yönetimi.',
    badge: 'Ücretsiz',
  },
];

export function renderLandingPage(container: HTMLElement): void {
  const points = DEMO_BARS.map((v, i) => `${(i / (DEMO_BARS.length - 1)) * 100},${110 - v}`).join(' ');

  container.innerHTML = pageShell('PiyasaPilot', `
    <!-- ── HERO ── -->
    <section class="landing-hero">
      <div class="hero-copy">
        <p class="eyebrow">${i18n.t('LANDING_EYEBROW')}</p>
        <h1>${i18n.t('LANDING_TITLE')}</h1>
        <p>${i18n.t('LANDING_SUBTITLE')}</p>
        <div class="hero-actions">
          <a class="btn btn-warning" href="/register" data-analytics="landing_signup_clicked" style="padding:12px 24px;font-size:15px">
            Ücretsiz Başla →
          </a>
          <a class="btn btn-outline-warning" href="/login" data-analytics="landing_login_clicked" style="padding:12px 20px">
            Giriş Yap
          </a>
        </div>
        <div style="margin-top:14px;display:flex;align-items:center;gap:16px;flex-wrap:wrap">
          <span style="color:var(--text-dim);font-size:12px">✓ Kredi kartı gerekmez</span>
          <span style="color:var(--text-dim);font-size:12px">✓ 2 dakikada kurulum</span>
          <span style="color:var(--text-dim);font-size:12px">✓ Günde 10 backtest ücretsiz</span>
        </div>
        <div class="hero-counters">
          <span><b>57</b> ${i18n.t('LANDING_COUNTER_EDUCATION')}</span>
          <span><b>9</b> ${i18n.t('LANDING_COUNTER_STRATEGIES')}</span>
          <span><b>62</b> Sembol</span>
          <span><b>0</b> ${i18n.t('LANDING_COUNTER_REAL_ORDERS')}</span>
        </div>
      </div>
      <div class="demo-terminal" aria-label="${i18n.t('LANDING_DEMO_LABEL')}">
        <div class="demo-head">
          <strong>THYAO.IS</strong>
          <span style="background:rgba(0,200,117,0.12);color:var(--green);padding:2px 8px;border-radius:3px;font-size:11px">+12.4%</span>
        </div>
        <svg viewBox="0 0 100 120" role="img" aria-label="Örnek fiyat çizgisi">
          <polyline points="${points}" fill="none" stroke="var(--amber)" stroke-width="3" vector-effect="non-scaling-stroke"/>
          <circle cx="96" cy="${110 - 104}" r="3" fill="var(--amber)"/>
          <line x1="0" y1="92" x2="100" y2="92" stroke="var(--border2)" stroke-width="1"/>
          <line x1="0" y1="55" x2="100" y2="55" stroke="var(--border2)" stroke-width="1"/>
        </svg>
        <div style="display:flex;gap:12px;margin-top:8px;font-size:11px">
          <span style="color:var(--green)">▲ Al: 45.20</span>
          <span style="color:var(--red)">▼ Sat: 52.80</span>
          <span style="color:var(--text-dim)">Kar: +16.8%</span>
        </div>
      </div>
    </section>

    <!-- ── FREE TIER BANNER ── -->
    <section class="landing-free-banner">
      <div class="landing-free-inner">
        <div>
          <div style="font-family:var(--font-sans);font-size:17px;font-weight:700;color:var(--text-bold);margin-bottom:4px">
            Ücretsiz planla çok şey yapabilirsin
          </div>
          <div style="color:var(--text);font-size:13px">
            Kayıt olmadan da bazı özelliklere eriş — hesap açınca daha fazlası açılır.
          </div>
        </div>
        <div style="display:flex;gap:20px;flex-wrap:wrap;align-items:center">
          ${[['BIST30 &amp; BIST100 grafikleri'],['Günde 10 backtest'],['KAP haberleri'],['9 strateji şablonu']].map(([t]) => `
            <span style="display:flex;align-items:center;gap:5px;font-size:12px;color:var(--text)">
              <span style="color:var(--green)">✓</span>${t}
            </span>`).join('')}
        </div>
        <a href="/register" class="btn btn-warning" style="white-space:nowrap;flex-shrink:0" data-analytics="landing_free_banner_clicked">
          Ücretsiz Başla
        </a>
      </div>
    </section>

    <!-- ── FEATURES ── -->
    <section style="margin-top:48px">
      <h2 style="font-family:var(--font-sans);font-size:24px;font-weight:700;color:var(--text-bold);margin-bottom:6px">
        Her şey tek platformda
      </h2>
      <p style="color:var(--text);margin-bottom:24px;font-size:14px">
        BIST yatırımcısının ihtiyaç duyduğu tüm araçlar
      </p>
      <div class="feature-grid">
        ${FEATURES.map(f => `
        <article class="feature-card landing-feature-card">
          <div class="landing-feature-icon">${f.icon}</div>
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
            <h2>${f.title}</h2>
            <span class="landing-feature-badge ${f.badge === 'Pro' ? 'pro' : ''}">${f.badge}</span>
          </div>
          <p>${f.desc}</p>
        </article>`).join('')}
      </div>
    </section>

    <!-- ── PRICING STRIP ── -->
    <section class="pricing-strip">
      <h2>${i18n.t('LANDING_PRICING_TITLE')}</h2>
      <div class="mini-plans">
        <a href="/register?plan=free">
          <div>
            <b>${i18n.t('PLAN_FREE')}</b>
            <div style="font-size:11px;color:var(--text);margin-top:2px">Temel özellikler · $0</div>
          </div>
          <span style="color:var(--green)">Ücretsiz</span>
        </a>
        <a class="featured" href="/pricing">
          <div>
            <b>Pro</b>
            <div style="font-size:11px;color:var(--text);margin-top:2px">Profesyonel araçlar</div>
          </div>
          <span>$19.99/ay</span>
        </a>
        <a href="/pricing">
          <div>
            <b>Ultra</b>
            <div style="font-size:11px;color:var(--text);margin-top:2px">Sınırsız erişim</div>
          </div>
          <span>$49.99/ay</span>
        </a>
      </div>
      <div style="text-align:center;margin-top:16px">
        <a href="/pricing" style="color:var(--amber);font-size:13px">Tüm plan özelliklerini karşılaştır →</a>
      </div>
    </section>
  `);

  container.querySelectorAll<HTMLElement>('[data-analytics]').forEach((el) => {
    el.addEventListener('click', () => analytics.track(el.dataset['analytics'] || 'landing_click'));
  });
}
