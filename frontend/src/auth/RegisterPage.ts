/**
 * RegisterPage — /register ekranı
 */

import { auth } from './AuthManager.js';
import { analytics } from '../core/Analytics.js';
import { i18n } from '../i18n/index.js';

export function renderRegisterPage(container: HTMLElement): void {
  const nextLang = i18n.current() === 'tr' ? 'en' : 'tr';
  container.innerHTML = `
<div class="auth-page d-flex align-items-center justify-content-center min-vh-100">
  <div class="auth-card card shadow-lg p-4" style="width:100%;max-width:440px">
    <div class="auth-card-top">
      <a class="auth-exit-link" href="/app">← Terminale dön</a>
      <button class="lang-switch" type="button" id="auth-lang-switch" aria-label="Change language">${nextLang.toUpperCase()}</button>
    </div>

    <div class="text-center mb-4">
      <div class="auth-logo mb-2">
        <span class="logo-mark">P</span><strong>PiyasaPilot</strong>
      </div>
      <h5 class="mb-0">${i18n.t('AUTH_REGISTER_TITLE')}</h5>
      <small class="text-muted">${i18n.t('AUTH_CARD_NOT_REQUIRED')}</small>
    </div>

    <div id="reg-alert" class="alert alert-danger d-none" role="alert"></div>
    <div id="reg-success" class="alert alert-success d-none" role="alert"></div>

    <form id="register-form" novalidate>
      <div class="mb-3">
        <label for="reg-name" class="form-label">${i18n.t('AUTH_NAME')}</label>
        <input
          id="reg-name"
          type="text"
          class="form-control"
          placeholder="Enes Aktaş"
          autocomplete="name"
          required
        />
      </div>

      <div class="mb-3">
        <label for="reg-email" class="form-label">${i18n.t('AUTH_EMAIL')}</label>
        <input
          id="reg-email"
          type="email"
          class="form-control"
          placeholder="ornek@mail.com"
          autocomplete="email"
          required
        />
      </div>

      <div class="mb-3">
        <label for="reg-password" class="form-label">${i18n.t('AUTH_PASSWORD')}</label>
        <div class="input-group">
          <input
            id="reg-password"
            type="password"
            class="form-control"
            placeholder="${i18n.t('AUTH_PASSWORD_PLACEHOLDER')}"
            autocomplete="new-password"
            required
          />
          <button class="btn btn-outline-secondary" type="button" id="toggle-pw1" tabindex="-1">👁</button>
        </div>
        <div id="pw-strength" class="mt-1 small"></div>
      </div>

      <div class="mb-3">
        <label for="reg-password2" class="form-label">${i18n.t('AUTH_CONFIRM_PASSWORD')}</label>
        <div class="input-group">
          <input
            id="reg-password2"
            type="password"
            class="form-control"
            placeholder="••••••••"
            autocomplete="new-password"
            required
          />
          <button class="btn btn-outline-secondary" type="button" id="toggle-pw2" tabindex="-1">👁</button>
        </div>
      </div>

      <div class="mb-3">
        <div class="form-check">
          <input id="reg-terms" class="form-check-input" type="checkbox" required />
          <label class="form-check-label small" for="reg-terms">
            <a href="/legal/terms" target="_blank" class="text-muted">${i18n.t('LEGAL_TERMS')}</a> · ${i18n.t('AUTH_TERMS_ACCEPT')}
          </label>
        </div>
        <div class="form-check mt-1">
          <input id="reg-privacy" class="form-check-input" type="checkbox" required />
          <label class="form-check-label small" for="reg-privacy">
            <a href="/legal/privacy" target="_blank" class="text-muted">${i18n.t('LEGAL_PRIVACY')}</a> · ${i18n.t('AUTH_PRIVACY_ACCEPT')}
          </label>
        </div>
      </div>

      <button id="reg-btn" type="submit" class="btn btn-warning w-100 fw-semibold mb-3">
        ${i18n.t('AUTH_REGISTER_SUBMIT')}
      </button>
    </form>

    <div class="text-center text-muted small mb-3">─── ${i18n.t('AUTH_OR')} ───</div>

    <button
      type="button"
      class="btn btn-outline-secondary w-100 d-flex align-items-center justify-content-center gap-2 mb-3"
      disabled
      title="${i18n.t('AUTH_GOOGLE_SOON_TITLE')}"
    >
      <svg width="18" height="18" viewBox="0 0 48 48">
        <path fill="#4285F4" d="M44.5 20H24v8.5h11.7C34.3 33.9 29.7 37 24 37c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.1 0 5.9 1.1 8.1 2.9l6-6C34.6 5.1 29.6 3 24 3 12.4 3 3 12.4 3 24s9.4 21 21 21c10.9 0 20-8 20-21 0-1.4-.1-2.7-.5-4z"/>
      </svg>
      ${i18n.t('AUTH_GOOGLE_REGISTER_SOON')}
    </button>

    <p class="text-center small text-muted mb-0">
      ${i18n.t('AUTH_HAS_ACCOUNT')}
      <a href="/login" class="text-warning text-decoration-none fw-semibold">${i18n.t('AUTH_SIGNIN_LINK')}</a>
    </p>
    <p class="text-center small mt-2 mb-0">
      <a href="/" class="auth-secondary-link">Ana sayfaya git</a>
    </p>
  </div>
</div>`;

  container.querySelector<HTMLButtonElement>('#auth-lang-switch')?.addEventListener('click', () => {
    i18n.setLang(nextLang);
    window.location.reload();
  });

  // Şifre toggle
  _setupToggle(container, '#toggle-pw1', '#reg-password');
  _setupToggle(container, '#toggle-pw2', '#reg-password2');

  // Şifre gücü göstergesi
  const pw1 = container.querySelector<HTMLInputElement>('#reg-password')!;
  const pwStrength = container.querySelector<HTMLDivElement>('#pw-strength')!;
  pw1.addEventListener('input', () => {
    const v = pw1.value;
    let score = 0;
    if (v.length >= 8)                score++;
    if (/[A-Z]/.test(v))              score++;
    if (/\d/.test(v))                 score++;
    if (/[^A-Za-z0-9]/.test(v))       score++;
    const labels = ['', i18n.t('AUTH_PASSWORD_WEAK'), i18n.t('AUTH_PASSWORD_MEDIUM'), i18n.t('AUTH_PASSWORD_GOOD'), i18n.t('AUTH_PASSWORD_STRONG')];
    const colors = ['', 'text-danger', 'text-warning', 'text-info', 'text-success'];
    pwStrength.textContent  = score > 0 ? `${i18n.t('AUTH_PASSWORD_STRENGTH_PREFIX')}: ${labels[score]}` : '';
    pwStrength.className    = `mt-1 small ${colors[score] || ''}`;
  });

  const alert   = container.querySelector<HTMLDivElement>('#reg-alert')!;
  const success = container.querySelector<HTMLDivElement>('#reg-success')!;
  const btn     = container.querySelector<HTMLButtonElement>('#reg-btn')!;
  const form    = container.querySelector<HTMLFormElement>('#register-form')!;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    _hideEl(alert);
    _hideEl(success);

    const name   = (container.querySelector<HTMLInputElement>('#reg-name')!).value.trim();
    const email  = (container.querySelector<HTMLInputElement>('#reg-email')!).value.trim();
    const pw1Val = pw1.value;
    const pw2Val = (container.querySelector<HTMLInputElement>('#reg-password2')!).value;
    const terms  = (container.querySelector<HTMLInputElement>('#reg-terms')!).checked;
    const priv   = (container.querySelector<HTMLInputElement>('#reg-privacy')!).checked;

    if (!name || !email || !pw1Val || !pw2Val) {
      _showAlert(alert, i18n.t('AUTH_REQUIRED_FIELDS'));
      return;
    }
    if (pw1Val !== pw2Val) {
      _showAlert(alert, i18n.t('AUTH_PASSWORD_MISMATCH'));
      return;
    }
    if (!terms || !priv) {
      _showAlert(alert, i18n.t('AUTH_LEGAL_REQUIRED'));
      return;
    }

    btn.disabled = true;
    btn.textContent = i18n.t('AUTH_REGISTER_LOADING');

    const result = await auth.register(email, pw1Val, name);
    if (result.ok) {
      analytics.track('signup_completed', { method: 'email' });
      form.classList.add('d-none');
      success.textContent = i18n.t('AUTH_VERIFY_SENT');
      success.classList.remove('d-none');
    } else {
      _showAlert(alert, result.error ?? i18n.t('AUTH_REGISTER_FAILED'));
      btn.disabled = false;
      btn.textContent = i18n.t('AUTH_REGISTER_SUBMIT');
    }
  });
}

function _setupToggle(container: HTMLElement, btnSel: string, inputSel: string): void {
  const btn   = container.querySelector<HTMLButtonElement>(btnSel);
  const input = container.querySelector<HTMLInputElement>(inputSel);
  btn?.addEventListener('click', () => {
    if (!input) return;
    input.type = input.type === 'password' ? 'text' : 'password';
  });
}

function _showAlert(el: HTMLElement, msg: string): void {
  el.textContent = msg;
  el.classList.remove('d-none');
}
function _hideEl(el: HTMLElement): void {
  el.classList.add('d-none');
}
