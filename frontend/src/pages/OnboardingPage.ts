import { auth } from '../auth/AuthManager.js';
import { pageShell, requireAuth, showInlineMessage } from './pageUtils.js';

export async function renderOnboardingPage(container: HTMLElement): Promise<void> {
  if (!(await requireAuth(container))) return;
  const name = auth.user?.display_name || auth.user?.email || 'PiyasaPilot kullanıcısı';
  container.innerHTML = pageShell('Onboarding', `
    <section class="onboarding-card">
      <h1>PiyasaPilot'a hoş geldin, ${name}</h1>
      <div id="onboarding-alert" hidden></div>
      <form id="onboarding-form">
        <fieldset>
          <legend>Adım 1 / 3: Dil</legend>
          <label><input type="radio" name="language" value="tr" checked /> Türkçe</label>
          <label><input type="radio" name="language" value="en" /> English</label>
        </fieldset>
        <fieldset>
          <legend>Adım 2 / 3: Piyasa</legend>
          <label><input type="radio" name="market" value="bist" /> BIST</label>
          <label><input type="radio" name="market" value="crypto" checked /> Kripto</label>
          <label><input type="radio" name="market" value="both" /> İkisi</label>
          <select class="form-select mt-2" name="default_symbol">
            <option value="BTCUSDT">BTCUSDT</option>
            <option value="THYAO.IS">THYAO.IS</option>
            <option value="ASELS.IS">ASELS.IS</option>
            <option value="XU100.IS">XU100.IS</option>
          </select>
        </fieldset>
        <fieldset>
          <legend>Adım 3 / 3: Tema</legend>
          <label><input type="radio" name="theme" value="dark" checked /> Koyu</label>
          <label><input type="radio" name="theme" value="light" /> Açık</label>
          <select class="form-select mt-2" name="accent_color">
            <option value="amber">Amber</option>
            <option value="cyan">Cyan</option>
            <option value="green">Yeşil</option>
          </select>
        </fieldset>
        <button class="btn btn-warning w-100" type="submit">Terminale Git</button>
      </form>
      <p class="plan-note">Planınız: Ücretsiz. Daha sonra Pro'ya geçebilirsiniz.</p>
    </section>`);

  const form = container.querySelector<HTMLFormElement>('#onboarding-form')!;
  const alert = container.querySelector<HTMLElement>('#onboarding-alert')!;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = new FormData(form);
    const ok = await auth.updateSettings({
      default_symbol: String(data.get('default_symbol') || 'BTCUSDT'),
      theme: data.get('theme') === 'light' ? 'light' : 'dark',
      accent_color: String(data.get('accent_color') || 'amber'),
      language: data.get('language') === 'en' ? 'en' : 'tr',
      onboarding_done: true,
    });
    if (ok) window.location.href = '/app';
    else showInlineMessage(alert, 'Ayarlar kaydedilemedi.', 'danger');
  });
}
