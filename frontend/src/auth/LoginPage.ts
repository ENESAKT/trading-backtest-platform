/**
 * LoginPage — /login ekranı (split-screen layout)
 */

import { auth } from './AuthManager.js';
import { analytics } from '../core/Analytics.js';
import { i18n } from '../i18n/index.js';

const DEMO_BARS = [18,24,21,29,34,31,38,43,39,46,52,48,57,61,58,66,70,64,73,78,75,82,88,84,91,96,93,101,108,104];

function buildDemoChart(): string {
  const pts = DEMO_BARS.map((v, i) => `${(i / (DEMO_BARS.length - 1)) * 100},${110 - v}`).join(' ');
  return `
  <div class="auth-demo-chart">
    <div class="auth-demo-chart-head">
      <strong>THYAO.IS</strong><span>+12.4%</span>
    </div>
    <svg viewBox="0 0 100 80" style="width:100%;height:72px;display:block;background:var(--panel)" aria-hidden="true">
      <polyline points="${pts}" fill="none" stroke="var(--amber)" stroke-width="2.5" vector-effect="non-scaling-stroke"/>
      <line x1="0" y1="55" x2="100" y2="55" stroke="var(--border)" stroke-width="1"/>
    </svg>
  </div>`;
}

export function renderLoginPage(container: HTMLElement): void {
  const nextLang = i18n.current() === 'tr' ? 'en' : 'tr';

  container.innerHTML = `
<div class="auth-split">
  <!-- ── Sol: Marka Paneli ── -->
  <aside class="auth-brand-panel">
    <div class="auth-brand-logo">
      <span class="logo-mark" aria-hidden="true">P</span>
      PiyasaPilot
    </div>

    <div>
      <h1 class="auth-brand-headline">
        BIST için<br><em>profesyonel</em><br>analiz platformu
      </h1>
      <p class="auth-brand-tagline">
        Backtest, teknik analiz ve KAP haberleri tek ekranda.
        Gerçek zamanlı verilerle stratejini test et.
      </p>

      ${buildDemoChart()}

      <ul class="auth-features">
        <li><span><strong>Ücretsiz başla</strong> — kredi kartı gerekmez</span></li>
        <li><span><strong>BIST30 + BIST100</strong> hisseleri ve göstergeler</span></li>
        <li><span><strong>Günde 10 backtest</strong> ücretsiz planda dahil</span></li>
        <li><span><strong>KAP haberleri</strong> ve mali analiz tek ekranda</span></li>
        <li><span><strong>Pro &amp; Ultra</strong> ile sınırsız erişim</span></li>
      </ul>
    </div>

    <p class="auth-brand-footer">
      © 2025 PiyasaPilot — Eğitim amaçlı, yatırım tavsiyesi değildir.
    </p>
  </aside>

  <!-- ── Sağ: Form Paneli ── -->
  <main class="auth-form-panel">
    <div class="auth-form-inner">
      <div class="auth-top-bar">
        <a href="/" class="auth-exit-link" style="font-size:13px">← Ana Sayfa</a>
        <button class="lang-switch" type="button" id="auth-lang-switch" aria-label="Change language">${nextLang.toUpperCase()}</button>
      </div>

      <div class="auth-form-header">
        <div class="auth-free-badge">● Ücretsiz plan mevcut</div>
        <h2>${i18n.t('AUTH_LOGIN_TITLE')}</h2>
        <p>Hesabına giriş yap veya <a href="/register" style="color:var(--amber)">ücretsiz kayıt ol</a></p>
      </div>

      <div id="login-alert" class="alert alert-danger d-none" role="alert"></div>

      <form id="login-form" novalidate>
        <div class="mb-3">
          <label for="login-email" class="form-label">${i18n.t('AUTH_EMAIL')}</label>
          <input
            id="login-email"
            type="email"
            class="form-control"
            placeholder="ornek@mail.com"
            autocomplete="email"
            required
          />
        </div>

        <div class="mb-3">
          <label for="login-password" class="form-label d-flex justify-content-between align-items-center">
            <span>${i18n.t('AUTH_PASSWORD')}</span>
            <a href="/forgot-password" class="auth-pw-hint" style="font-size:11px">${i18n.t('AUTH_FORGOT_PASSWORD')}</a>
          </label>
          <div class="input-group">
            <input
              id="login-password"
              type="password"
              class="form-control"
              placeholder="••••••••"
              autocomplete="current-password"
              required
            />
            <button class="btn btn-outline-secondary" type="button" id="toggle-password" aria-label="${i18n.t('AUTH_TOGGLE_PASSWORD')}">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
          </div>
        </div>

        <div class="mb-3" id="totp-row">
          <label for="login-totp" class="form-label">${i18n.t('AUTH_TOTP')} <span class="auth-pw-hint">(opsiyonel)</span></label>
          <input id="login-totp" type="text" inputmode="numeric" class="form-control" placeholder="123456" autocomplete="one-time-code" maxlength="6" />
        </div>

        <button id="login-btn" type="submit" class="btn btn-warning w-100 fw-semibold mb-3" style="padding:11px">
          ${i18n.t('AUTH_LOGIN_SUBMIT')}
        </button>
      </form>

      <div class="auth-divider">veya</div>

      <button type="button" class="auth-guest-btn" id="guest-btn">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        Misafir olarak devam et (kayıt gerekmez)
      </button>

      <p class="auth-switch-link">
        ${i18n.t('AUTH_NO_ACCOUNT')}
        <a href="/register">${i18n.t('AUTH_SIGNUP_LINK')}</a>
      </p>
    </div>
  </main>
</div>`;

  // Dil geçiş
  container.querySelector<HTMLButtonElement>('#auth-lang-switch')?.addEventListener('click', () => {
    i18n.setLang(nextLang);
    window.location.reload();
  });

  // Şifre toggle
  const toggleBtn = container.querySelector<HTMLButtonElement>('#toggle-password');
  const pwInput   = container.querySelector<HTMLInputElement>('#login-password');
  toggleBtn?.addEventListener('click', () => {
    if (!pwInput) return;
    pwInput.type = pwInput.type === 'password' ? 'text' : 'password';
  });

  // Misafir girişi
  container.querySelector<HTMLButtonElement>('#guest-btn')?.addEventListener('click', () => {
    analytics.track('guest_continue_clicked');
    window.location.href = '/app';
  });

  // Form submit
  const form  = container.querySelector<HTMLFormElement>('#login-form')!;
  const alert = container.querySelector<HTMLDivElement>('#login-alert')!;
  const btn   = container.querySelector<HTMLButtonElement>('#login-btn')!;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email    = (container.querySelector<HTMLInputElement>('#login-email')!).value.trim();
    const password = pwInput!.value;
    const totp     = (container.querySelector<HTMLInputElement>('#login-totp')!).value.trim();

    if (!email || !password) {
      _showAlert(alert, i18n.t('AUTH_LOGIN_REQUIRED'));
      return;
    }

    btn.disabled = true;
    btn.textContent = i18n.t('AUTH_LOGIN_LOADING');
    _hideAlert(alert);

    const result = await auth.login(email, password, totp);

    if (result.ok) {
      analytics.track('login_completed', { method: 'email' });
      const user = auth.user;
      const dest = user?.settings.onboarding_done === false ? '/onboarding' : '/app';
      window.location.href = dest;
    } else {
      _showAlert(alert, result.error ?? i18n.t('AUTH_LOGIN_FAILED'));
      btn.disabled = false;
      btn.textContent = i18n.t('AUTH_LOGIN_SUBMIT');
    }
  });
}

function _showAlert(el: HTMLElement, msg: string): void {
  el.textContent = msg;
  el.classList.remove('d-none');
}
function _hideAlert(el: HTMLElement): void {
  el.classList.add('d-none');
}
