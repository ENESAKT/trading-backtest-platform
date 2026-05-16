import { pageShell } from './pageUtils.js';
import { analytics } from '../core/Analytics.js';

export function renderPaymentSuccessPage(container: HTMLElement): void {
  analytics.track('payment_success_viewed');
  container.innerHTML = pageShell('Ödeme Başarılı', `
    <section class="public-state">
      <h1>Pro planına hoş geldiniz</h1>
      <p>Backtest Pro, Scanner ve Telegram Bot özellikleri hesabınızda aktif hale gelir. Stripe webhook birkaç saniye içinde planı günceller.</p>
      <a class="btn btn-warning" href="/app">Terminale Git</a>
      <a class="btn btn-outline-warning" href="/settings">Hesap Ayarları</a>
    </section>`);
}
