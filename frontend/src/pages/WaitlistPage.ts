import { pageShell, showInlineMessage } from './pageUtils.js';
import { analytics } from '../core/Analytics.js';

export function renderWaitlistPage(container: HTMLElement): void {
  container.innerHTML = pageShell('Waitlist', `
    <section class="auth-public-card">
      <h1>PiyasaPilot çok yakında</h1>
      <p>BIST'in gelişmiş algoritmik trading terminali için erken erişim listesine katılın. İlk 100 üyeye 3 ay ücretsiz Pro.</p>
      <div id="waitlist-alert" hidden></div>
      <form id="waitlist-form">
        <label>E-posta</label>
        <input class="form-control" type="email" autocomplete="email" required />
        <button class="btn btn-warning w-100 mt-3" type="submit">Erken Erişim İstiyorum</button>
      </form>
      <p id="waitlist-count" class="plan-note"></p>
    </section>`);
  const form = container.querySelector<HTMLFormElement>('#waitlist-form')!;
  const alert = container.querySelector<HTMLElement>('#waitlist-alert')!;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = form.querySelector<HTMLInputElement>('input')!.value.trim();
    const res = await fetch('/api/waitlist', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, source: 'waitlist_page' }),
    });
    const body = await res.json();
    if (res.ok) {
      analytics.track('waitlist_joined', { source: 'waitlist_page' });
      showInlineMessage(alert, 'Listeye eklendiniz. Teşekkürler.', 'success');
      container.querySelector('#waitlist-count')!.textContent = `${body.data?.count || 1} kişi kaydoldu.`;
    } else {
      showInlineMessage(alert, body.detail?.tr || 'Erken erişim servisi şu an hazır değil. E-posta listeniz canlı backend bağlandığında alınacak.', 'danger');
    }
  });
}
