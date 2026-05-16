/**
 * LoginPage — /login ekranı
 * Vanilla TS + Bootstrap, mevcut tema değişkenleri kullanılır.
 */

import { auth } from './AuthManager.js';
import { analytics } from '../core/Analytics.js';

export function renderLoginPage(container: HTMLElement): void {
  container.innerHTML = `
<div class="auth-page d-flex align-items-center justify-content-center min-vh-100">
  <div class="auth-card card shadow-lg p-4" style="width:100%;max-width:440px">

    <div class="text-center mb-4">
      <div class="auth-logo mb-2">
        <span class="logo-mark">P</span><strong>PiyasaPilot</strong>
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

    <div class="text-center text-muted small mb-3">─── veya ───</div>

    <button
      type="button"
      class="btn btn-outline-secondary w-100 d-flex align-items-center justify-content-center gap-2 mb-3"
      disabled
      title="Google OAuth canlı anahtarları tanımlandıktan sonra açılacak"
    >
      <svg width="18" height="18" viewBox="0 0 48 48">
        <path fill="#4285F4" d="M44.5 20H24v8.5h11.7C34.3 33.9 29.7 37 24 37c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.1 0 5.9 1.1 8.1 2.9l6-6C34.6 5.1 29.6 3 24 3 12.4 3 3 12.4 3 24s9.4 21 21 21c10.9 0 20-8 20-21 0-1.4-.1-2.7-.5-4z"/>
      </svg>
      Google ile Devam Et — yakında
    </button>

    <p class="text-center small text-muted mb-0">
      Hesabınız yok mu?
      <a href="/register" class="text-warning text-decoration-none fw-semibold">Ücretsiz Kayıt Ol</a>
    </p>
  </div>
</div>`;

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

    btn.disabled = true;
    btn.textContent = 'Giriş yapılıyor…';
    _hideAlert(alert);

    const result = await auth.login(email, password, totp);

    if (result.ok) {
      analytics.track('login_completed', { method: 'email' });
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
