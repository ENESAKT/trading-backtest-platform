export function mountCookieBanner(): void {
  if (localStorage.getItem('pp_cookie_choice')) return;
  const banner = document.createElement('div');
  banner.className = 'cookie-banner';
  banner.innerHTML = `
    <p>Zorunlu oturum/güvenlik çerezleri kullanılır. Analitik çerezleri için ayrı onay alınır.</p>
    <a href="/legal/cookies">Detaylar</a>
    <button class="btn btn-sm btn-outline-warning" data-cookie-choice="reject">Reddet</button>
    <button class="btn btn-sm btn-warning" data-cookie-choice="accept">Kabul Et</button>`;
  document.body.appendChild(banner);
  banner.querySelectorAll<HTMLButtonElement>('[data-cookie-choice]').forEach((btn) => {
    btn.addEventListener('click', () => {
      localStorage.setItem('pp_cookie_choice', btn.dataset['cookieChoice'] || 'accept');
      banner.remove();
    });
  });
}
