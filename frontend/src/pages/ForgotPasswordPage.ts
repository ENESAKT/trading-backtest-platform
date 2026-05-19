import { pageShell, showInlineMessage } from './pageUtils.js';

export function renderForgotPasswordPage(container: HTMLElement): void {
  container.innerHTML = pageShell('Şifremi Sıfırla', `
    <section class="auth-public-card">
      <h1>Şifremi Sıfırla</h1>
      <p>E-posta adresinizi yazın, sıfırlama bağlantısını gönderelim.</p>
      <div id="forgot-alert" hidden></div>
      <form id="forgot-form">
        <label>E-posta</label>
        <input class="form-control" type="email" autocomplete="email" required />
        <button class="btn btn-warning w-100 mt-3" type="submit">Sıfırlama Bağlantısı Gönder</button>
      </form>
      <a class="back-link" href="/login">Giriş Yap</a>
    </section>`);

  const form = container.querySelector<HTMLFormElement>('#forgot-form')!;
  const alert = container.querySelector<HTMLElement>('#forgot-alert')!;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = form.querySelector<HTMLInputElement>('input')!.value.trim();
    const res = await fetch('/api/auth/forgot-password', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    showInlineMessage(alert, res.ok ? 'Bağlantı gönderildi. Gelen kutunuzu kontrol edin.' : 'İşlem tamamlanamadı.', res.ok ? 'success' : 'danger');
  });
}

export function renderResetPasswordPage(container: HTMLElement): void {
  const token = new URLSearchParams(window.location.search).get('token') || '';
  container.innerHTML = pageShell('Yeni Şifre', `
    <section class="auth-public-card">
      <h1>Yeni şifrenizi belirleyin</h1>
      <div id="reset-alert" hidden></div>
      <form id="reset-form">
        <label>Yeni Şifre</label>
        <input class="form-control" name="password" type="password" autocomplete="new-password" required />
        <label class="mt-3">Yeni Şifreyi Onayla</label>
        <input class="form-control" name="password2" type="password" autocomplete="new-password" required />
        <button class="btn btn-warning w-100 mt-3" type="submit">Şifremi Güncelle</button>
      </form>
    </section>`);
  const form = container.querySelector<HTMLFormElement>('#reset-form')!;
  const alert = container.querySelector<HTMLElement>('#reset-alert')!;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const p1 = (new FormData(form).get('password') || '').toString();
    const p2 = (new FormData(form).get('password2') || '').toString();
    if (p1 !== p2) {
      showInlineMessage(alert, 'Şifreler eşleşmiyor.', 'danger');
      return;
    }
    const res = await fetch('/api/auth/reset-password', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, new_password: p1 }),
    });
    showInlineMessage(alert, res.ok ? 'Şifreniz güncellendi. Giriş yapabilirsiniz.' : 'Token geçersiz veya süresi dolmuş.', res.ok ? 'success' : 'danger');
  });
}
