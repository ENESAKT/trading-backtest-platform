import { auth } from '../auth/AuthManager.js';

export function pageShell(title: string, body: string, active = ''): string {
  return `
    <div class="public-page">
      <header class="public-nav">
        <a class="public-brand" href="/">
          <span class="logo-mark">P</span><strong>PiyasaPilot</strong>
        </a>
        <nav>
          <a class="${active === 'pricing' ? 'active' : ''}" href="/pricing">Fiyatlandırma</a>
          <a href="/login">Giriş Yap</a>
          <a class="btn btn-warning btn-sm" href="/register">Ücretsiz Başla</a>
        </nav>
      </header>
      <main class="public-main" aria-label="${escapeHtml(title)}">${body}</main>
      <footer class="public-footer">
        <a href="/legal/terms">Kullanım Koşulları</a>
        <a href="/legal/privacy">Gizlilik</a>
        <a href="/legal/cookies">Çerezler</a>
        <p class="risk-disclaimer">PiyasaPilot yatırım tavsiyesi vermez. Gösterilen tüm veriler yalnızca bilgilendirme amaçlıdır. Gerçek emir gönderimi desteklenmez.</p>
      </footer>
    </div>`;
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
