import { pageShell, showInlineMessage } from './pageUtils.js';

export function renderVerifyEmailPage(container: HTMLElement): void {
  const token = new URLSearchParams(window.location.search).get('token') || '';
  container.innerHTML = pageShell('E-posta Doğrulama', `
    <section class="auth-public-card">
      <h1>E-posta adresinizi doğrulayın</h1>
      <p>Bağlantı otomatik kontrol ediliyor. Gerekirse doğrulama e-postasını yeniden gönderebilirsiniz.</p>
      <div id="verify-alert" hidden></div>
      <button id="verify-btn" class="btn btn-warning w-100">Doğrula</button>
      <button id="resend-btn" class="btn btn-outline-warning w-100 mt-2">Yeniden Gönder</button>
    </section>`);

  const alert = container.querySelector<HTMLElement>('#verify-alert')!;
  const verify = async () => {
    if (!token) {
      showInlineMessage(alert, 'Doğrulama tokenı bulunamadı.', 'danger');
      return;
    }
    const res = await fetch('/api/auth/verify-email', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token }),
    });
    showInlineMessage(alert, res.ok ? 'E-posta doğrulandı. Giriş yapabilirsiniz.' : 'Token geçersiz veya süresi dolmuş.', res.ok ? 'success' : 'danger');
  };
  container.querySelector('#verify-btn')?.addEventListener('click', () => void verify());
  container.querySelector('#resend-btn')?.addEventListener('click', async () => {
    const res = await fetch('/api/auth/resend-verification', { method: 'POST', credentials: 'include' });
    showInlineMessage(alert, res.ok ? 'Doğrulama e-postası gönderildi.' : 'Yeniden gönderim için giriş yapmalısınız.', res.ok ? 'success' : 'danger');
  });
  void verify();
}
