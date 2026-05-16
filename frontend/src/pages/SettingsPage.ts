import { auth } from '../auth/AuthManager.js';
import { analytics } from '../core/Analytics.js';
import { pageShell, requireAuth, showInlineMessage } from './pageUtils.js';

export async function renderSettingsPage(container: HTMLElement): Promise<void> {
  if (!(await requireAuth(container))) return;
  const user = auth.user!;
  container.innerHTML = pageShell('Hesap Ayarları', `
    <section class="settings-page">
      <h1>Hesap Ayarları</h1>
      <div id="settings-alert" hidden></div>
      <div class="settings-grid">
        <article>
          <h2>Profil</h2>
          <p>${user.email} ${user.email_verified ? 'Doğrulandı' : 'Doğrulama bekliyor'}</p>
          <label>Varsayılan sembol</label>
          <input id="settings-symbol" class="form-control" value="${user.settings.default_symbol}" />
          <button id="settings-save" class="btn btn-warning mt-3">Kaydet</button>
        </article>
        <article>
          <h2>Güvenlik</h2>
          <button id="settings-sessions" class="btn btn-outline-warning">Aktif Oturumları Yenile</button>
          <div id="sessions-list" class="sessions-list"></div>
        </article>
        <article>
          <h2>Abonelik</h2>
          <p>Plan: <strong>${user.role.toUpperCase()}</strong></p>
          <div id="subscription-state" class="empty-panel">Abonelik durumu yükleniyor...</div>
          <button id="billing-portal" class="btn btn-outline-warning">Faturalar ve İptal</button>
          <a class="btn btn-warning" href="/pricing">Planı Yükselt</a>
        </article>
        <article>
          <h2>Dil ve Bölge</h2>
          <select id="settings-lang" class="form-select">
            <option value="tr" ${user.language === 'tr' ? 'selected' : ''}>Türkçe</option>
            <option value="en" ${user.language === 'en' ? 'selected' : ''}>English</option>
          </select>
        </article>
      </div>
    </section>`);

  const alert = container.querySelector<HTMLElement>('#settings-alert')!;
  void loadSubscriptionState(container);
  container.querySelector('#settings-save')?.addEventListener('click', async () => {
    const ok = await auth.updateSettings({
      default_symbol: container.querySelector<HTMLInputElement>('#settings-symbol')!.value.trim(),
      language: container.querySelector<HTMLSelectElement>('#settings-lang')!.value === 'en' ? 'en' : 'tr',
    });
    showInlineMessage(alert, ok ? 'Ayarlar kaydedildi.' : 'Ayarlar kaydedilemedi.', ok ? 'success' : 'danger');
  });

  container.querySelector('#settings-sessions')?.addEventListener('click', async () => {
    const res = await fetch('/api/auth/sessions', { credentials: 'include' });
    const body = await res.json();
    const list = container.querySelector<HTMLElement>('#sessions-list')!;
    list.innerHTML = (body.data?.sessions || []).map((s: Record<string, string>) => `<div>${s.user_agent || 'Bilinmeyen cihaz'}<small>${s.ip_address || ''}</small></div>`).join('') || '<p>Aktif oturum bulunamadı.</p>';
  });

  container.querySelector('#billing-portal')?.addEventListener('click', async () => {
    analytics.track('billing_portal_clicked', { plan: user.role });
    const res = await fetch('/api/payments/portal', { method: 'POST', credentials: 'include' });
    const body = await res.json();
    if (res.ok && body.data?.portal_url) window.location.href = body.data.portal_url;
    else showInlineMessage(alert, body.detail?.tr || 'Faturalama portalı şu an bağlı değil. Stripe canlı portal ayarları tamamlandığında buradan faturalar ve iptal işlemleri açılır.', 'danger');
  });
}

async function loadSubscriptionState(container: HTMLElement): Promise<void> {
  const target = container.querySelector<HTMLElement>('#subscription-state');
  if (!target) return;
  try {
    const res = await fetch('/api/payments/subscription', { credentials: 'include' });
    const body = await res.json();
    if (!res.ok || !body.data) throw new Error('Abonelik bilgisi yok.');
    const sub = body.data as Record<string, string | number | null>;
    target.innerHTML = `
      <strong>${String(sub['status'] || 'aktif değil')}</strong>
      <small>${sub['current_period_end'] ? `Sonraki dönem: ${String(sub['current_period_end'])}` : 'Canlı Stripe aboneliği bulunamadı.'}</small>`;
  } catch {
    target.innerHTML = '<strong>Billing entegrasyonu beklemede</strong><small>Plan bilgisi hesabınızdan okunur; fatura portalı canlı Stripe ayarları sonrası açılır.</small>';
  }
}
