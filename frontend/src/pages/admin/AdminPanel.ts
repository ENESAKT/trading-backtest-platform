import { auth } from '../../auth/AuthManager.js';
import { pageShell, requireAuth } from '../pageUtils.js';

export async function renderAdminPanel(container: HTMLElement): Promise<void> {
  if (!(await requireAuth(container))) return;
  if (!auth.isAdmin()) {
    container.innerHTML = pageShell('Yetki Yok', `<section class="public-state"><h1>Yetki yok</h1><p>Admin paneli yalnızca admin rolüyle açılır.</p><a class="btn btn-warning" href="/app">Terminale Dön</a></section>`);
    return;
  }
  container.innerHTML = pageShell('Admin', `
    <section class="admin-panel">
      <aside>
        <strong>PiyasaPilot Admin</strong>
        <button data-admin-tab="overview" class="active">Özet</button>
        <button data-admin-tab="users">Kullanıcılar</button>
        <button data-admin-tab="subscriptions">Abonelikler</button>
        <button data-admin-tab="data">Veri Kalitesi</button>
        <button data-admin-tab="audit">Audit Log</button>
      </aside>
      <div class="admin-content" id="admin-content"></div>
    </section>`);
  const content = container.querySelector<HTMLElement>('#admin-content')!;
  const render = (tab: string) => {
    const cards: Record<string, string> = {
      overview: '<h1>Özet</h1><div class="metric-grid"><span>Toplam kullanıcı<b>0</b></span><span>Pro<b>0</b></span><span>Ultra<b>0</b></span><span>Aktif oturum<b>0</b></span></div>',
      users: '<h1>Kullanıcı Yönetimi</h1><input class="form-control" placeholder="E-posta ara" /><table><thead><tr><th>ID</th><th>E-posta</th><th>Plan</th><th>Durum</th><th>İşlem</th></tr></thead><tbody><tr><td colspan="5">Admin API bağlandığında kullanıcılar listelenecek.</td></tr></tbody></table>',
      subscriptions: '<h1>Abonelikler</h1><p>Stripe metrikleri ve MRR burada izlenecek.</p><a class="btn btn-outline-warning" href="https://dashboard.stripe.com" target="_blank">Stripe Dashboard</a>',
      data: '<h1>Veri Kalitesi</h1><table><tbody><tr><td>ClickHouse</td><td>Bağlantı kontrolü API bağlandığında gösterilecek.</td></tr><tr><td>Redis</td><td>Cache durumu izlenecek.</td></tr></tbody></table>',
      audit: '<h1>Audit Log</h1><p>Filtrelenebilir denetim kayıtları için backend admin endpointleri bekleniyor.</p>',
    };
    content.innerHTML = cards[tab] || cards.overview;
  };
  render('overview');
  container.querySelectorAll<HTMLButtonElement>('[data-admin-tab]').forEach((btn) => {
    btn.addEventListener('click', () => {
      container.querySelectorAll('[data-admin-tab]').forEach((b) => b.classList.toggle('active', b === btn));
      render(btn.dataset['adminTab'] || 'overview');
    });
  });
}
