/**
 * LoginPage — /login ekranı
 * Vanilla TS + Bootstrap, mevcut tema değişkenleri kullanılır.
 */

import { auth } from './AuthManager.js';
import { bindAuthPageDismiss } from './authPageDismiss.js';
import { renderOAuthButtons } from './OAuthButtons.js';

export function renderLoginPage(container: HTMLElement): void {
  container.innerHTML = `
<div class="auth-page d-flex align-items-center justify-content-center min-vh-100">
  <div class="auth-card card shadow-lg p-4" style="width:100%;max-width:440px">

    <div class="text-center mb-4">
      <div class="auth-logo mb-2">
        <span class="logo-mark">P</span><strong>Piyasa Pilotu</strong>
      </div>
      <h5 class="mb-0">Hesabınıza giriş yapın</h5>
    </div>

    <div id="login-alert" class="alert alert-danger d-none" role="alert"></div>

    <form id="login-form" novalidate>
      <div class="mb-3">
        <label for="login-email" class="form-label">E-posta</label>
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
        <label for="login-password" class="form-label d-flex justify-content-between">
          <span>Şifre</span>
          <a href="/forgot-password" class="small text-muted">Şifremi Unuttum</a>
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
          <button
            class="btn btn-outline-secondary"
            type="button"
            id="toggle-password"
            tabindex="-1"
            aria-label="Şifreyi göster/gizle"
          >👁</button>
        </div>
      </div>

      <div class="mb-3">
        <label for="login-totp" class="form-label">2FA Kodu (varsa)</label>
        <input id="login-totp" type="text" inputmode="numeric" class="form-control" placeholder="123456" autocomplete="one-time-code" />
      </div>
      <button
        id="login-btn"
        type="submit"
        class="btn btn-warning w-100 fw-semibold mb-3"
      >Giriş Yap</button>
    </form>

    <div data-oauth-buttons class="mb-3"></div>

    <p class="text-center small text-muted mb-0">
      Hesabınız yok mu?
      <a href="/register" class="text-warning text-decoration-none fw-semibold">Ücretsiz Kayıt Ol</a>
    </p>
  </div>
</div>`;

  bindAuthPageDismiss(container);
  void renderOAuthButtons(container, 'login');

  // Şifre görünürlük toggle
  const toggleBtn = container.querySelector<HTMLButtonElement>('#toggle-password');
  const pwInput   = container.querySelector<HTMLInputElement>('#login-password');
  toggleBtn?.addEventListener('click', () => {
    if (!pwInput) return;
    pwInput.type = pwInput.type === 'password' ? 'text' : 'password';
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
      _showAlert(alert, 'E-posta ve şifre zorunludur.');
      return;
    }
    if (!_isEmail(email)) {
      _showAlert(alert, 'E-posta alanına geçerli bir e-posta adresi yazın.');
      return;
    }

    btn.disabled = true;
    btn.textContent = 'Giriş yapılıyor…';
    _hideAlert(alert);

    const result = await auth.login(email, password, totp);

    if (result.ok) {
      const user = auth.user;
      const dest = user?.settings.onboarding_done === false ? '/onboarding' : '/app';
      window.location.href = dest;
    } else {
      _showAlert(alert, result.error ?? 'Giriş başarısız.');
      btn.disabled = false;
      btn.textContent = 'Giriş Yap';
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
function _isEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}
