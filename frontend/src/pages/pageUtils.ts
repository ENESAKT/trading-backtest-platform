import { auth } from '../auth/AuthManager.js';
import { i18n } from '../i18n/index.js';

export function pageShell(title: string, body: string, active = ''): string {
  const isLoggedIn = !!auth.user;
  const nextLang = i18n.current() === 'tr' ? 'en' : 'tr';
  const navLinks = isLoggedIn
    ? `<a href="/app">${i18n.t('NAV_TERMINAL')}</a>
       <a class="btn btn-outline-warning btn-sm" href="/settings">${i18n.t('NAV_SETTINGS')}</a>`
    : `<a href="/login">${i18n.t('NAV_LOGIN')}</a>
       <a class="btn btn-warning btn-sm" href="/register">${i18n.t('NAV_REGISTER')}</a>`;

  return `
    <div class="public-page">
      <header class="public-nav">
        <a class="public-brand" href="/">
          <span class="logo-mark">P</span><strong>PiyasaPilot</strong>
        </a>
        <nav>
          <a class="${active === 'pricing' ? 'active' : ''}" href="/pricing">${i18n.t('NAV_PRICING')}</a>
          ${navLinks}
          <button class="lang-switch" type="button" data-lang-switch="${nextLang}" aria-label="Change language">${nextLang.toUpperCase()}</button>
        </nav>
      </header>
      <main class="public-main" aria-label="${escapeHtml(title)}">${body}</main>
      <footer class="public-footer">
        <div class="footer-legal-links">
          <a href="/legal/terms">${i18n.t('LEGAL_TERMS')}</a>
          <a href="/legal/privacy">${i18n.t('LEGAL_PRIVACY')}</a>
          <a href="/legal/cookies">${i18n.t('LEGAL_COOKIES')}</a>
          <a href="/legal/info">${i18n.t('LEGAL_INFO')}</a>
        </div>
        <p class="risk-disclaimer">${i18n.t('PUBLIC_RISK_DISCLAIMER')}</p>
        <!-- TTK m.39/2 + TKHK m.48 — İşletmeci bilgileri canlı yayın öncesinde doldurulmalıdır -->
        <p class="footer-company-info">
          PiyasaPilot &mdash;
          <span id="footer-company-name">[İşletmeci/Şirket Adı]</span> &middot;
          <span id="footer-company-address">[Adres]</span> &middot;
          <span id="footer-company-tax">[Vergi Dairesi / VKN veya TC Kimlik No]</span> &middot;
          <a href="mailto:destek@piyasapilot.com">destek@piyasapilot.com</a>
        </p>
      </footer>
    </div>`;
}

export function bindPublicPageControls(container: HTMLElement): void {
  container.querySelectorAll<HTMLButtonElement>('[data-lang-switch]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const lang = btn.dataset['langSwitch'] === 'en' ? 'en' : 'tr';
      i18n.setLang(lang);
      window.location.reload();
    });
  });
}

export function escapeHtml(value: unknown): string {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export async function requireAuth(container: HTMLElement): Promise<boolean> {
  await auth.init();
  if (!auth.user) {
    container.innerHTML = simpleState('Oturum gerekli', 'Bu sayfaya devam etmek için giriş yapmalısınız.', '/login', 'Giriş Yap');
    return false;
  }
  return true;
}

export function simpleState(title: string, text: string, href: string, cta: string): string {
  return pageShell(title, `
    <section class="public-state">
      <h1>${escapeHtml(title)}</h1>
      <p>${escapeHtml(text)}</p>
      <a class="btn btn-warning" href="${href}">${escapeHtml(cta)}</a>
    </section>`);
}

export function showInlineMessage(el: HTMLElement, message: string, kind: 'success' | 'danger' | 'info' = 'info'): void {
  el.className = `alert alert-${kind}`;
  el.textContent = message;
  el.hidden = false;
}
