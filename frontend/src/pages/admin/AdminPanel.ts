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
  const render = async (tab: string) => {
    content.innerHTML = '<div class="skeleton-wrap"><div class="skeleton skeleton-title"></div><div class="skeleton skeleton-row"></div><div class="skeleton skeleton-row"></div></div>';
    try {
      if (tab === 'overview') {
        const res = await fetch('/api/admin/overview', { credentials: 'include' });
        const data = await res.json();
        const stats = data.data || {};
        content.innerHTML = `<h1>Özet</h1><div class="metric-grid"><span>Toplam kullanıcı<b>${stats.users_total ?? '-'}</b></span><span>Pro<b>${stats.pro_users ?? '-'}</b></span><span>Ultra<b>${stats.ultra_users ?? '-'}</b></span><span>Aktif oturum<b>${stats.active_sessions ?? '-'}</b></span></div>`;
      } else if (tab === 'users') {
        const res = await fetch('/api/admin/users?limit=50', { credentials: 'include' });
        const data = await res.json();
        const users = data.data?.users || [];
        const rows = users.length
          ? users.map((u: any) => `<tr><td>${u.id}</td><td>${u.email}</td><td><span class="badge ${u.role}">${u.role.toUpperCase()}</span></td><td>${u.is_active ? 'Aktif' : 'Pasif'}</td><td><button class="btn btn-sm btn-outline-secondary" onclick="alert('Detay yapım aşamasında')">Detay</button></td></tr>`).join('')
          : '<tr><td colspan="5">Kullanıcı bulunamadı.</td></tr>';
        content.innerHTML = `<h1>Kullanıcı Yönetimi</h1><div class="admin-toolbar"><input class="form-control" placeholder="E-posta ara" /><select class="form-select"><option>Tüm Planlar</option><option>Free</option><option>Pro</option><option>Ultra</option></select></div><table><thead><tr><th>ID</th><th>E-posta</th><th>Plan</th><th>Durum</th><th>İşlem</th></tr></thead><tbody>${rows}</tbody></table>`;
      } else if (tab === 'audit') {
        const res = await fetch('/api/admin/audit-log?limit=50', { credentials: 'include' });
        const data = await res.json();
        const events = data.data?.events || [];
        const rows = events.length
          ? events.map((e: any) => `<tr><td>${e.created_at}</td><td>${e.user_id || '-'}</td><td>${e.action}</td><td>${e.resource || '-'}</td></tr>`).join('')
          : '<tr><td colspan="4">Denetim kaydı bulunamadı.</td></tr>';
        content.innerHTML = `<h1>Audit Log</h1><table><thead><tr><th>Tarih</th><th>User ID</th><th>Aksiyon</th><th>Kaynak</th></tr></thead><tbody>${rows}</tbody></table>`;
      } else if (tab === 'subscriptions') {
        const res = await fetch('/api/admin/subscriptions?limit=50', { credentials: 'include' });
        const data = await res.json();
        const subs = data.data?.subscriptions || [];
        const rows = subs.length
          ? subs.map((s: any) => `<tr><td>${s.email}</td><td>${s.plan}</td><td>${s.billing_period}</td><td>${s.status}</td><td>${s.current_period_end || '-'}</td></tr>`).join('')
          : '<tr><td colspan="5">Canlı veya trial abonelik kaydı bulunamadı.</td></tr>';
        content.innerHTML = `<h1>Abonelikler</h1><table><thead><tr><th>E-posta</th><th>Plan</th><th>Dönem</th><th>Durum</th><th>Bitiş</th></tr></thead><tbody>${rows}</tbody></table><a class="btn btn-outline-warning" href="https://dashboard.stripe.com" target="_blank" rel="noreferrer">Stripe Dashboard</a>`;
      } else if (tab === 'data') {
        const res = await fetch('/api/health');
        const data = await res.json();
        content.innerHTML = `<h1>Veri Kalitesi</h1><table><tbody><tr><td>API</td><td>${data.status || 'ok'}</td></tr><tr><td>Detay</td><td>Kaynak gecikmesi ve gap metrikleri admin kalite endpointi bağlandığında gösterilecek.</td></tr></tbody></table>`;
      }
    } catch (e) {
      content.innerHTML = '<div class="empty-panel"><strong>Veri yüklenemedi</strong><small>Yetkiniz reddedilmiş olabilir veya ilgili admin endpointi henüz canlı değildir.</small></div>';
    }
  };
  void render('overview');
  container.querySelectorAll<HTMLButtonElement>('[data-admin-tab]').forEach((btn) => {
    btn.addEventListener('click', () => {
      container.querySelectorAll('[data-admin-tab]').forEach((b) => b.classList.toggle('active', b === btn));
      void render(btn.dataset['adminTab'] || 'overview');
    });
  });
}
