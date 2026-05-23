/**
 * RegisterPage — /register ekranı
 */

import { auth } from './AuthManager.js';
import { bindAuthPageDismiss } from './authPageDismiss.js';
import { renderOAuthButtons } from './OAuthButtons.js';

export function renderRegisterPage(container: HTMLElement): void {
  container.innerHTML = `
<div class="auth-page d-flex align-items-center justify-content-center min-vh-100">
  <div class="auth-card card shadow-lg p-4" style="width:100%;max-width:440px">

    <div class="text-center mb-4">
      <div class="auth-logo mb-2">
        <span class="logo-mark">P</span><strong>Piyasa Pilotu</strong>
      </div>
      <h5 class="mb-0">Ücretsiz hesap oluşturun</h5>
      <small class="text-muted">Kredi kartı gerekmez</small>
    </div>

    <div id="reg-alert" class="alert alert-danger d-none" role="alert"></div>
    <div id="reg-success" class="alert alert-success d-none" role="alert"></div>

    <form id="register-form" novalidate>
      <div class="mb-3">
        <label for="reg-name" class="form-label">Ad Soyad</label>
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
        <label for="reg-email" class="form-label">E-posta</label>
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
        <label for="reg-password" class="form-label">Şifre</label>
        <div class="input-group">
          <input
            id="reg-password"
            type="password"
            class="form-control"
            placeholder="Min 8 karakter, 1 büyük harf, 1 rakam"
            autocomplete="new-password"
            required
          />
          <button class="btn btn-outline-secondary" type="button" id="toggle-pw1" tabindex="-1">👁</button>
        </div>
        <div id="pw-strength" class="mt-1 small"></div>
      </div>

      <div class="mb-3">
        <label for="reg-password2" class="form-label">Şifreyi Onayla</label>
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
            <a href="/legal/terms" target="_blank" class="text-muted">Kullanım Koşulları</a>'nı okudum ve kabul ediyorum
          </label>
        </div>
        <div class="form-check mt-1">
          <input id="reg-privacy" class="form-check-input" type="checkbox" required />
          <label class="form-check-label small" for="reg-privacy">
            <a href="/legal/privacy" target="_blank" class="text-muted">Gizlilik Politikası</a>'nı okudum
          </label>
        </div>
      </div>

      <button id="reg-btn" type="submit" class="btn btn-warning w-100 fw-semibold mb-3">
        Hesap Oluştur
      </button>
    </form>

    <div data-oauth-buttons class="mb-3"></div>

    <p class="text-center small text-muted mb-0">
      Hesabınız var mı?
      <a href="/login" class="text-warning text-decoration-none fw-semibold">Giriş Yapın</a>
    </p>
  </div>
</div>`;

  bindAuthPageDismiss(container);
  void renderOAuthButtons(container, 'register');

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
    const labels = ['', 'Zayıf', 'Orta', 'İyi', 'Güçlü'];
    const colors = ['', 'text-danger', 'text-warning', 'text-info', 'text-success'];
    pwStrength.textContent  = score > 0 ? `Şifre: ${labels[score]}` : '';
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
      _showAlert(alert, 'Tüm alanlar zorunludur.');
      return;
    }
    if (!_isEmail(email)) {
      _showAlert(alert, 'E-posta alanına geçerli bir e-posta adresi yazın.');
      return;
    }
    if (pw1Val !== pw2Val) {
      _showAlert(alert, 'Şifreler eşleşmiyor.');
      return;
    }
    if (!terms || !priv) {
      _showAlert(alert, 'Kullanım koşullarını ve gizlilik politikasını onaylamanız gerekiyor.');
      return;
    }

    btn.disabled = true;
    btn.textContent = 'Hesap oluşturuluyor…';

    const result = await auth.register(email, pw1Val, name);
    if (result.ok) {
      form.classList.add('d-none');
      success.textContent = '📬 E-posta kutunuzu kontrol edin. Doğrulama bağlantısı gönderildi.';
      success.classList.remove('d-none');
    } else {
      _showAlert(alert, result.error ?? 'Kayıt başarısız.');
      btn.disabled = false;
      btn.textContent = 'Hesap Oluştur';
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
function _isEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}
