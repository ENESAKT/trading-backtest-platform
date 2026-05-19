import { pageShell } from '../pageUtils.js';

export function renderCookiesPage(container: HTMLElement): void {
  container.innerHTML = pageShell('Çerez Politikası', `
    <article class="legal-page">
      <h1>Çerez Politikası</h1>
      <p>Son güncelleme: 2026-05-16</p>
      <h2>Zorunlu çerezler</h2>
      <p>Oturum, güvenlik ve tercih yönetimi için zorunlu çerezler kullanılır.</p>
      <h2>Tercih çerezleri</h2>
      <p>Tema, dil ve görünüm tercihleri tarayıcıda saklanabilir.</p>
      <h2>Analitik</h2>
      <p>Analitik entegrasyonu eklenirse kullanıcıya açık şekilde bildirilecektir.</p>
    </article>`);
}
