import { auth } from '../auth/AuthManager.js';
import { analytics } from '../core/Analytics.js';
import { i18n } from '../i18n/index.js';
import { pageShell, requireAuth, showInlineMessage } from './pageUtils.js';

export async function renderSettingsPage(container: HTMLElement): Promise<void> {
  if (!(await requireAuth(container))) return;
  const user = auth.user!;
  container.innerHTML = pageShell(i18n.t('SETTINGS_TITLE'), `
    <section class="settings-page">
      <h1>${i18n.t('SETTINGS_TITLE')}</h1>
      <div id="settings-alert" hidden></div>
      <div class="settings-grid">
        <article>
          <h2>${i18n.t('SETTINGS_PROFILE')}</h2>
          <p>${user.email} ${user.email_verified ? i18n.t('SETTINGS_VERIFIED') : i18n.t('SETTINGS_PENDING_VERIFY')}</p>
          <label>${i18n.t('SETTINGS_DEFAULT_SYMBOL')}</label>
          <input id="settings-symbol" class="form-control" value="${user.settings.default_symbol}" />
          <button id="settings-save" class="btn btn-warning mt-3">${i18n.t('SETTINGS_SAVE')}</button>
        </article>
        <article>
          <h2>${i18n.t('SETTINGS_SECURITY')}</h2>
          <button id="settings-sessions" class="btn btn-outline-warning">${i18n.t('SETTINGS_REFRESH_SESSIONS')}</button>
          <div id="sessions-list" class="sessions-list"></div>
        </article>
        <article>
          <h2>${i18n.t('SETTINGS_SUBSCRIPTION')}</h2>
          <p>${i18n.t('SETTINGS_PLAN')}: <strong>${user.role.toUpperCase()}</strong></p>
          <div id="subscription-state" class="empty-panel">${i18n.t('SETTINGS_SUB_LOADING')}</div>
          <button id="billing-portal" class="btn btn-outline-warning">${i18n.t('SETTINGS_BILLING_PORTAL')}</button>
          <a class="btn btn-warning" href="/pricing">${i18n.t('PLAN_UPGRADE_CTA')}</a>
        </article>
        <article>
          <h2>${i18n.t('SETTINGS_LANGUAGE_REGION')}</h2>
          <select id="settings-lang" class="form-select">
            <option value="tr" ${user.language === 'tr' ? 'selected' : ''}>Türkçe</option>
            <option value="en" ${user.language === 'en' ? 'selected' : ''}>English</option>
          </select>
        </article>
      </div>
    </section>`);

  const alert = container.querySelector<HTMLElement>('#settings-alert')!;
  void loadSubscriptionState(container);
  container.querySelector('#settings-save')?.addEventListener('click', async () => {
    const ok = await auth.updateSettings({
      default_symbol: container.querySelector<HTMLInputElement>('#settings-symbol')!.value.trim(),
      language: container.querySelector<HTMLSelectElement>('#settings-lang')!.value === 'en' ? 'en' : 'tr',
    });
    showInlineMessage(alert, ok ? i18n.t('SETTINGS_SAVE_OK') : i18n.t('SETTINGS_SAVE_FAIL'), ok ? 'success' : 'danger');
  });

  container.querySelector('#settings-sessions')?.addEventListener('click', async () => {
    const res = await fetch('/api/auth/sessions', { credentials: 'include' });
    const body = await res.json();
    const list = container.querySelector<HTMLElement>('#sessions-list')!;
    list.innerHTML = (body.data?.sessions || []).map((s: Record<string, string>) => `<div>${s.user_agent || i18n.t('SETTINGS_UNKNOWN_DEVICE')}<small>${s.ip_address || ''}</small></div>`).join('') || `<p>${i18n.t('SETTINGS_NO_SESSIONS')}</p>`;
  });

  container.querySelector('#billing-portal')?.addEventListener('click', async () => {
    analytics.track('billing_portal_clicked', { plan: user.role });
    const res = await fetch('/api/payments/portal', { method: 'POST', credentials: 'include' });
    const body = await res.json();
    if (res.ok && body.data?.portal_url) window.location.href = body.data.portal_url;
    else {
      const detail = i18n.current() === 'en' ? body.detail?.en : body.detail?.tr;
      showInlineMessage(alert, detail || i18n.t('SETTINGS_PORTAL_ERROR'), 'danger');
    }
  });
}

async function loadSubscriptionState(container: HTMLElement): Promise<void> {
  const target = container.querySelector<HTMLElement>('#subscription-state');
  if (!target) return;
  try {
    const res = await fetch('/api/payments/subscription', { credentials: 'include' });
    const body = await res.json();
    if (!res.ok || !body.data) throw new Error(i18n.t('SETTINGS_SUB_MISSING'));
    const sub = body.data as Record<string, string | number | null>;
    target.innerHTML = `
      <strong>${String(sub['status'] || i18n.t('SETTINGS_SUB_INACTIVE'))}</strong>
      <small>${sub['current_period_end'] ? `${i18n.t('SETTINGS_NEXT_PERIOD')}: ${String(sub['current_period_end'])}` : i18n.t('SETTINGS_NO_LIVE_SUB')}</small>`;
  } catch {
    target.innerHTML = `<strong>${i18n.t('SETTINGS_BILLING_WAITING')}</strong><small>${i18n.t('SETTINGS_BILLING_WAITING_COPY')}</small>`;
  }
}
