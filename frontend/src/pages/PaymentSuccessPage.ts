import { pageShell } from './pageUtils.js';
import { analytics } from '../core/Analytics.js';
import { i18n } from '../i18n/index.js';
import { auth } from '../auth/AuthManager.js';

// P0.3 FIX: session_id veya giriş olmadan kesin başarı dili gösterme.
// Durum → kullanıcıya dürüst bağlam ver.
export async function renderPaymentSuccessPage(container: HTMLElement): Promise<void> {
  const params = new URLSearchParams(window.location.search);
  const sessionId = params.get('session_id');
  await auth.init();
  const isLoggedIn = !!auth.user;

  analytics.track('payment_success_viewed', { has_session: sessionId ? 1 : 0, logged_in: isLoggedIn ? 1 : 0 });

  let heading: string;
  let body: string;
  let actions: string;

  if (!isLoggedIn) {
    // Giriş yoksa kullanıcı kimin aboneliğini gördüğünü bilemeyiz
    heading = 'Ödeme Doğrulama';
    body = 'Ödeme durumunuzu görmek için lütfen giriş yapın. Aboneliğiniz aktifleştirildiyse hesabınızda görünecektir.';
    actions = `<a class="btn btn-warning" href="/login?next=/settings">${i18n.t('AUTH_LOGIN_SUBMIT')}</a>`;
  } else if (!sessionId) {
    // Giriş var ama session_id yok — bu sayfaya doğrudan gelinmiş
    heading = 'Ödeme Durumu';
    body = 'Bu sayfaya geçerli bir ödeme oturumu olmadan ulaşıldı. Mevcut planınızı aşağıdan kontrol edebilirsiniz.';
    actions = `
      <a class="btn btn-warning" href="/settings">${i18n.t('SETTINGS_TITLE')}</a>
      <a class="btn btn-outline-warning" href="/pricing">${i18n.t('PRICING_TITLE') || 'Fiyatlandırma'}</a>`;
  } else {
    // session_id var → webhook birkaç saniye içinde planı güncelleyecek
    heading = i18n.t('PAYMENT_SUCCESS_HEADING');
    body = 'Ödemeniz alındı. Plan güncellemeniz birkaç saniye içinde aktif hale gelecektir. '
         + 'Henüz görünmüyorsa sayfayı yenileyin veya destek ile iletişime geçin.';
    actions = `
      <a class="btn btn-warning" href="/app">${i18n.t('NAV_TERMINAL')}</a>
      <a class="btn btn-outline-warning" href="/settings">${i18n.t('SETTINGS_TITLE')}</a>`;
  }

  container.innerHTML = pageShell(i18n.t('PAYMENT_SUCCESS_TITLE'), `
    <section class="public-state">
      <h1>${heading}</h1>
      <p>${body}</p>
      <div class="public-state-actions">${actions}</div>
    </section>`);
}
