/**
 * RegisterPage — /register ekranı (split-screen layout + plan seçici)
 */

import { auth } from './AuthManager.js';
import { analytics } from '../core/Analytics.js';
import { i18n } from '../i18n/index.js';

const PLANS = [
  {
    id: 'free',
    label: 'Ücretsiz',
    price: '$0',
    features: ['BIST30 + BIST100', 'Günde 10 backtest', 'Temel göstergeler'],
    badge: '',
  },
  {
    id: 'pro',
    label: 'Pro',
    price: '$19.99/ay',
    features: ['Tüm semboller', 'Günde 50 backtest', 'Gelişmiş göstergeler', 'KAP haberleri'],
    badge: 'Popüler',
  },
  {
    id: 'ultra',
    label: 'Ultra',
    price: '$49.99/ay',
    features: ['Sınırsız backtest', 'API erişimi', 'Öncelikli destek'],
    badge: '',
  },
];

function renderPlanCards(selectedPlan: string): string {
  return `
  <div class="reg-plan-grid" role="radiogroup" aria-label="Plan seçimi">
    ${PLANS.map(p => `
    <button
      type="button"
      class="reg-plan-card${p.id === selectedPlan ? ' selected' : ''}"
      data-plan="${p.id}"
      aria-pressed="${p.id === selectedPlan}"
    >
      ${p.badge ? `<span class="reg-plan-badge">${p.badge}</span>` : ''}
      <div class="reg-plan-name">${p.label}</div>
      <div class="reg-plan-price">${p.price}</div>
      <ul class="reg-plan-features">
        ${p.features.map(f => `<li>${f}</li>`).join('')}
      </ul>
    </button>`).join('')}
  </div>`;
}

export function renderRegisterPage(container: HTMLElement): void {
  const nextLang = i18n.current() === 'tr' ? 'en' : 'tr';
  let selectedPlan = 'free';

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
        Hemen <em>ücretsiz</em><br>hesap aç
      </h1>
      <p class="auth-brand-tagline">
        Kredi kartı gerekmez. 2 dakikada kurulum.
        Ücretsiz planda bile güçlü analiz araçlarına eriş.
      </p>

      <ul class="auth-features">
        <li><span><strong>BIST30 &amp; BIST100</strong> grafik ve göstergeleri</span></li>
        <li><span><strong>Günde 10 backtest</strong> ücretsiz planda dahil</span></li>
        <li><span><strong>9 strateji şablonu</strong> hazır kullanım</span></li>
        <li><span><strong>KAP haberleri</strong> gerçek zamanlı takip</span></li>
        <li><span>İstediğin zaman <strong>Pro/Ultra'ya yükselt</strong></span></li>
      </ul>
    </div>

    <div class="auth-brand-trust">
      <p class="auth-brand-footer">
        Verilerini asla üçüncü taraflarla paylaşmıyoruz.
      </p>
      <p class="auth-brand-footer" style="margin-top:4px">
        © 2025 PiyasaPilot — Yatırım tavsiyesi değildir.
      </p>
    </div>
  </aside>

  <!-- ── Sağ: Form Paneli ── -->
  <main class="auth-form-panel">
    <div class="auth-form-inner">
      <div class="auth-top-bar">
        <a href="/" class="auth-exit-link" style="font-size:13px">← Ana Sayfa</a>
        <button class="lang-switch" type="button" id="auth-lang-switch" aria-label="Change language">${nextLang.toUpperCase()}</button>
      </div>

      <div class="auth-form-header">
        <div class="auth-free-badge">● Ücretsiz başla — kredi kartı gerekmez</div>
        <h2>${i18n.t('AUTH_REGISTER_TITLE')}</h2>
        <p>Plan seç, bilgilerini gir, hemen kullanmaya başla</p>
      </div>

      <div id="reg-alert" class="alert alert-danger d-none" role="alert"></div>
      <div id="reg-success" class="alert alert-success d-none" role="alert"></div>

      <!-- Plan seçici -->
      <div id="plan-picker-wrapper" style="margin-bottom:20px">
        <div class="form-label" style="margin-bottom:8px">Planı seç</div>
        ${renderPlanCards(selectedPlan)}
      </div>

      <form id="register-form" novalidate>
        <div class="mb-3">
          <label for="reg-name" class="form-label">${i18n.t('AUTH_NAME')}</label>
          <input
            id="reg-name"
            type="text"
            class="form-control"
            placeholder="Adın Soyadın"
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
              placeholder="En az 8 karakter"
              autocomplete="new-password"
              required
            />
            <button class="btn btn-outline-secondary" type="button" id="toggle-pw1" aria-label="${i18n.t('AUTH_TOGGLE_PASSWORD')}">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
          </div>
          <div id="pw-strength" class="auth-pw-hint mt-1"></div>
        </div>

        <div class="mb-3">
          <label for="reg-password2" class="form-label">${i18n.t('AUTH_CONFIRM_PASSWORD')}</label>
          <div class="input-group">
            <input
              id="reg-password2"
              type="password"
              class="form-control"
              placeholder="Şifreni tekrar gir"
              autocomplete="new-password"
              required
            />
            <button class="btn btn-outline-secondary" type="button" id="toggle-pw2" aria-label="${i18n.t('AUTH_TOGGLE_PASSWORD')}">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
          </div>
        </div>

        <div class="mb-3">
          <div class="form-check">
            <input id="reg-terms" class="form-check-input" type="checkbox" required />
            <label class="form-check-label" for="reg-terms">
              <a href="/legal/terms" target="_blank" style="color:var(--amber)">${i18n.t('LEGAL_TERMS')}</a>'ni okudum ve kabul ediyorum
            </label>
          </div>
          <div class="form-check mt-1">
            <input id="reg-privacy" class="form-check-input" type="checkbox" required />
            <label class="form-check-label" for="reg-privacy">
              <a href="/legal/privacy" target="_blank" style="color:var(--amber)">${i18n.t('LEGAL_PRIVACY')}</a>'ni kabul ediyorum
            </label>
          </div>
        </div>

        <button id="reg-btn" type="submit" class="btn btn-warning w-100 fw-semibold mb-2" style="padding:11px">
          ${i18n.t('AUTH_REGISTER_SUBMIT')}
        </button>
        <p style="text-align:center;font-size:11px;color:var(--text-dim);margin-bottom:0">
          Kaydolarak ücretsiz plana başlarsın. İstediğin zaman yükseltebilirsin.
        </p>
      </form>

      <p class="auth-switch-link">
        ${i18n.t('AUTH_HAS_ACCOUNT')}
        <a href="/login">${i18n.t('AUTH_SIGNIN_LINK')}</a>
      </p>
    </div>
  </main>
</div>`;

  // Dil geçiş
  container.querySelector<HTMLButtonElement>('#auth-lang-switch')?.addEventListener('click', () => {
    i18n.setLang(nextLang);
    window.location.reload();
  });

  // Plan seçici
  container.querySelectorAll<HTMLButtonElement>('.reg-plan-card').forEach(btn => {
    btn.addEventListener('click', () => {
      selectedPlan = btn.dataset['plan'] ?? 'free';
      container.querySelectorAll('.reg-plan-card').forEach(c => {
        c.classList.toggle('selected', c === btn);
        c.setAttribute('aria-pressed', String(c === btn));
      });
    });
  });

  // Şifre toggle
  _setupToggle(container, '#toggle-pw1', '#reg-password');
  _setupToggle(container, '#toggle-pw2', '#reg-password2');

  // Şifre gücü
  const pw1 = container.querySelector<HTMLInputElement>('#reg-password')!;
  const pwStrength = container.querySelector<HTMLDivElement>('#pw-strength')!;
  pw1.addEventListener('input', () => {
    const v = pw1.value;
    let score = 0;
    if (v.length >= 8)              score++;
    if (/[A-Z]/.test(v))            score++;
    if (/\d/.test(v))               score++;
    if (/[^A-Za-z0-9]/.test(v))     score++;
    const labels = ['', 'Zayıf', 'Orta', 'İyi', 'Güçlü'];
    const colors = ['', 'color:var(--red)', 'color:var(--amber)', 'color:var(--cyan)', 'color:var(--green)'];
    pwStrength.innerHTML = score > 0
      ? `<span style="${colors[score]}">Şifre gücü: ${labels[score]}</span>`
      : '';
  });

  const alertEl  = container.querySelector<HTMLDivElement>('#reg-alert')!;
  const successEl = container.querySelector<HTMLDivElement>('#reg-success')!;
  const btn      = container.querySelector<HTMLButtonElement>('#reg-btn')!;
  const form     = container.querySelector<HTMLFormElement>('#register-form')!;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    _hideEl(alertEl);
    _hideEl(successEl);

    const name   = (container.querySelector<HTMLInputElement>('#reg-name')!).value.trim();
    const email  = (container.querySelector<HTMLInputElement>('#reg-email')!).value.trim();
    const pw1Val = pw1.value;
    const pw2Val = (container.querySelector<HTMLInputElement>('#reg-password2')!).value;
    const terms  = (container.querySelector<HTMLInputElement>('#reg-terms')!).checked;
    const priv   = (container.querySelector<HTMLInputElement>('#reg-privacy')!).checked;

    if (!name || !email || !pw1Val || !pw2Val) {
      _showAlert(alertEl, i18n.t('AUTH_REQUIRED_FIELDS'));
      return;
    }
    if (pw1Val !== pw2Val) {
      _showAlert(alertEl, i18n.t('AUTH_PASSWORD_MISMATCH'));
      return;
    }
    if (!terms || !priv) {
      _showAlert(alertEl, i18n.t('AUTH_LEGAL_REQUIRED'));
      return;
    }

    btn.disabled = true;
    btn.textContent = i18n.t('AUTH_REGISTER_LOADING');

    const result = await auth.register(email, pw1Val, name);
    if (result.ok) {
      analytics.track('signup_completed', { method: 'email', plan: selectedPlan });
      form.closest<HTMLElement>('#register-form')?.classList.add('d-none');
      container.querySelector<HTMLElement>('#plan-picker-wrapper')?.classList.add('d-none');
      successEl.innerHTML = `
        <strong>Hesabın oluşturuldu!</strong><br>
        ${i18n.t('AUTH_VERIFY_SENT')}<br>
        <a href="/login" style="color:var(--amber);font-weight:600">Giriş yap →</a>`;
      successEl.classList.remove('d-none');
    } else {
      _showAlert(alertEl, result.error ?? i18n.t('AUTH_REGISTER_FAILED'));
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
