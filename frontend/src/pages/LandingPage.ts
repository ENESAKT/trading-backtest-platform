import { pageShell } from './pageUtils.js';
import { analytics } from '../core/Analytics.js';
import { i18n } from '../i18n/index.js';

const demoBars = [18, 24, 21, 29, 34, 31, 38, 43, 39, 46, 52, 48, 57, 61, 58, 66, 70, 64, 73, 78, 75, 82, 88, 84, 91, 96, 93, 101, 108, 104];

export function renderLandingPage(container: HTMLElement): void {
  const points = demoBars.map((v, i) => `${(i / (demoBars.length - 1)) * 100},${110 - v}`).join(' ');
  container.innerHTML = pageShell('PiyasaPilot', `
    <section class="landing-hero">
      <div class="hero-copy">
        <p class="eyebrow">${i18n.t('LANDING_EYEBROW')}</p>
        <h1>${i18n.t('LANDING_TITLE')}</h1>
        <p>${i18n.t('LANDING_SUBTITLE')}</p>
        <div class="hero-actions">
          <a class="btn btn-warning" href="/register" data-analytics="landing_signup_clicked">${i18n.t('LANDING_CTA_PRIMARY')}</a>
          <a class="btn btn-outline-warning" href="/pricing" data-analytics="landing_pricing_clicked">${i18n.t('LANDING_CTA_SECONDARY')}</a>
        </div>
        <div class="hero-counters">
          <span><b>57</b> ${i18n.t('LANDING_COUNTER_EDUCATION')}</span>
          <span><b>9</b> ${i18n.t('LANDING_COUNTER_STRATEGIES')}</span>
          <span><b>0</b> ${i18n.t('LANDING_COUNTER_REAL_ORDERS')}</span>
        </div>
      </div>
      <div class="demo-terminal" aria-label="${i18n.t('LANDING_DEMO_LABEL')}">
        <div class="demo-head"><strong>BTCUSDT</strong><span>${i18n.t('LANDING_DEMO_BADGE')}</span></div>
        <svg viewBox="0 0 100 120" role="img" aria-label="30 günlük örnek fiyat çizgisi">
          <polyline points="${points}" fill="none" stroke="var(--amber)" stroke-width="3" vector-effect="non-scaling-stroke"/>
          <line x1="0" y1="92" x2="100" y2="92" stroke="var(--border2)" stroke-width="1"/>
          <line x1="0" y1="55" x2="100" y2="55" stroke="var(--border2)" stroke-width="1"/>
        </svg>
      </div>
    </section>
    <section class="feature-grid">
      ${['Grafik Lab', 'Backtest Pro', 'KAP Haberleri', 'Portfolio', 'Sinyaller', 'Eğitimler'].map((name) => `
        <article class="feature-card">
          <div class="feature-shot"></div>
          <h2>${name}</h2>
          <p>${i18n.t('LANDING_FEATURE_TEXT')}</p>
        </article>`).join('')}
    </section>
    <section class="pricing-strip">
      <h2>${i18n.t('LANDING_PRICING_TITLE')}</h2>
      <div class="mini-plans">
        <a href="/register"><b>${i18n.t('PLAN_FREE')}</b><span>$0</span></a>
        <a class="featured" href="/pricing"><b>Pro</b><span>$19.99/ay</span></a>
        <a href="/pricing"><b>Ultra</b><span>$49.99/ay</span></a>
      </div>
    </section>`);

  container.querySelectorAll<HTMLElement>('[data-analytics]').forEach((el) => {
    el.addEventListener('click', () => analytics.track(el.dataset['analytics'] || 'landing_click'));
  });
}
