import { pageShell, showInlineMessage } from './pageUtils.js';
import { analytics } from '../core/Analytics.js';
import { i18n } from '../i18n/index.js';

export function renderWaitlistPage(container: HTMLElement): void {
  container.innerHTML = pageShell('Waitlist', `
    <section class="auth-public-card">
      <h1>${i18n.t('WAITLIST_TITLE')}</h1>
      <p>${i18n.t('WAITLIST_COPY')}</p>
      <div id="waitlist-alert" hidden></div>
      <form id="waitlist-form">
        <label>${i18n.t('WAITLIST_EMAIL')}</label>
        <input class="form-control" type="email" autocomplete="email" required />
        <button class="btn btn-warning w-100 mt-3" type="submit">${i18n.t('WAITLIST_CTA')}</button>
      </form>
      <p id="waitlist-count" class="plan-note"></p>
    </section>`);
  const form = container.querySelector<HTMLFormElement>('#waitlist-form')!;
  const alert = container.querySelector<HTMLElement>('#waitlist-alert')!;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = form.querySelector<HTMLInputElement>('input')!.value.trim();
    try {
      const res = await fetch('/api/waitlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, source: 'waitlist_page' }),
      });
      const body = await res.json();
      if (!res.ok) {
        const detail = i18n.current() === 'en' ? body.detail?.en : body.detail?.tr;
        throw new Error(detail || i18n.t('WAITLIST_ERROR'));
      }
      analytics.track('waitlist_joined', { source: 'waitlist_page' });
      showInlineMessage(alert, i18n.t('WAITLIST_SUCCESS'), 'success');
      container.querySelector('#waitlist-count')!.textContent = `${body.data?.count || 1} ${i18n.t('WAITLIST_COUNT')}`;
    } catch (err) {
      showInlineMessage(alert, err instanceof Error ? err.message : i18n.t('WAITLIST_ERROR'), 'danger');
    }
  });
}
