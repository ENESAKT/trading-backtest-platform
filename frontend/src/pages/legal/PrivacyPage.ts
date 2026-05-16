import { pageShell } from '../pageUtils.js';

export function renderPrivacyPage(container: HTMLElement): void {
  container.innerHTML = pageShell('Gizlilik Politikası', `
    <article class="legal-page">
      <h1>Gizlilik Politikası</h1>
      <p>Son güncelleme: 2026-05-16</p>
      <h2>Toplanan bilgiler</h2>
      <p>Hesap oluşturma, oturum yönetimi, abonelik ve uygulama tercihleri için gerekli minimum bilgiler saklanır.</p>
      <h2>Ödeme</h2>
      <p>Kart bilgileri PiyasaPilot sunucularında saklanmaz; ödeme akışı Stripe tarafından yürütülür.</p>
      <h2>Güvenlik</h2>
      <p>Oturumlar HttpOnly cookie ile yönetilir; hassas tokenlar istemci depolamasına yazılmaz.</p>
    </article>`);
}
