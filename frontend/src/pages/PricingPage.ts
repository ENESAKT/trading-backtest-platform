import { auth } from '../auth/AuthManager.js';
import { analytics } from '../core/Analytics.js';
import { i18n } from '../i18n/index.js';
import { pageShell, showInlineMessage } from './pageUtils.js';

const plans = [
  { slug: 'free', name: 'Ücretsiz', monthly: '$0', yearly: '$0', cta: 'Ücretsiz Başla', features: ['Terminal', '5 backtest/gün', 'BIST30 mali analiz', '1 paper hesap'] },
  { slug: 'pro', name: 'Pro', monthly: '$19.99/ay', yearly: '$199.99/yıl', cta: "Pro'ya Geç", features: ['50 backtest/gün', 'Backtest Pro', 'Scanner', 'Telegram Bot', 'BIST100 mali analiz'] },
  // P0.4 FIX: "Canlı veri" yerine güvenli dil — BIST/VİOP lisansı tamamlanana kadar
  { slug: 'ultra', name: 'Ultra', monthly: '$49.99/ay', yearly: '$499.99/yıl', cta: 'Ultra Ol', features: ['Sınırsız backtest', 'Öncelikli veri akışı¹', 'API erişimi', 'Tüm mali analiz', 'Sınırsız watchlist'] },
];

export function renderPricingPage(container: HTMLElement): void {
  container.innerHTML = pageShell('Fiyatlandırma', `
    <section class="pricing-page">
      <h1>${i18n.t('PRICING_TITLE')}</h1>
      <div class="billing-toggle" role="group" aria-label="${i18n.t('PRICING_BILLING_LABEL')}">
        <button class="active" data-billing="monthly">${i18n.t('PRICING_MONTHLY')}</button>
        <button data-billing="yearly">${i18n.t('PRICING_YEARLY')}</button>
      </div>
      <div id="pricing-alert" hidden></div>
      <div class="pricing-grid">
        ${plans.map((plan) => `
          <article class="pricing-card ${plan.slug === 'pro' ? 'featured' : ''}">
            <h2>${plan.name}</h2>
            <p class="price" data-monthly="${plan.monthly}" data-yearly="${plan.yearly}">${plan.monthly}</p>
            <ul>${plan.features.map((f) => `<li>${f}</li>`).join('')}</ul>
            <button class="btn ${plan.slug === 'free' ? 'btn-outline-warning' : 'btn-warning'} w-100" data-plan="${plan.slug}">${plan.cta}</button>
          </article>`).join('')}
      </div>
      <p class="trust-line">${i18n.t('PRICING_TRUST')}</p>
    </section>`, 'pricing');

  let billing = 'monthly';
  container.querySelectorAll<HTMLButtonElement>('[data-billing]').forEach((btn) => {
    btn.addEventListener('click', () => {
      billing = btn.dataset['billing'] || 'monthly';
      container.querySelectorAll('[data-billing]').forEach((b) => b.classList.toggle('active', b === btn));
      container.querySelectorAll<HTMLElement>('.price').forEach((price) => {
        price.textContent = price.dataset[billing] || '';
      });
    });
  });

  container.querySelectorAll<HTMLButtonElement>('[data-plan]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const plan = btn.dataset['plan'] || 'free';
      analytics.track('upgrade_clicked', { plan, billing });
      if (plan === 'free') {
        window.location.href = '/register';
        return;
      }
      await auth.init();
      if (!auth.user) {
        window.location.href = `/login?next=/pricing&plan=${plan}`;
        return;
      }
      btn.disabled = true;
      btn.textContent = i18n.t('PRICING_STRIPE_OPENING');
      const alert = container.querySelector<HTMLElement>('#pricing-alert')!;
      try {
        const res = await fetch('/api/payments/checkout', {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ plan, billing_period: billing }),
        });
        const body = await res.json();
        const detail = i18n.current() === 'en' ? body.detail?.en : body.detail?.tr;
        if (!res.ok || !body.data?.checkout_url) throw new Error(detail || i18n.t('PRICING_CHECKOUT_ERROR'));
        window.location.href = body.data.checkout_url;
      } catch (err) {
        showInlineMessage(alert, err instanceof Error ? err.message : i18n.t('PRICING_CHECKOUT_ERROR'), 'danger');
        btn.disabled = false;
        btn.textContent = plan === 'pro' ? "Pro'ya Geç" : 'Ultra Ol';
      }
    });
  });
}
