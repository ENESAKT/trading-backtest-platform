import { pageShell } from './pageUtils.js';
import { analytics } from '../core/Analytics.js';
import { i18n } from '../i18n/index.js';

export function renderPaymentSuccessPage(container: HTMLElement): void {
  analytics.track('payment_success_viewed');
  container.innerHTML = pageShell(i18n.t('PAYMENT_SUCCESS_TITLE'), `
    <section class="public-state">
      <h1>${i18n.t('PAYMENT_SUCCESS_HEADING')}</h1>
      <p>${i18n.t('PAYMENT_SUCCESS_COPY')}</p>
      <a class="btn btn-warning" href="/app">${i18n.t('NAV_TERMINAL')}</a>
      <a class="btn btn-outline-warning" href="/settings">${i18n.t('SETTINGS_TITLE')}</a>
    </section>`);
}
