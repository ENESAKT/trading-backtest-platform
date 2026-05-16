import { auth } from '../../auth/AuthManager.js';
import { pageShell, requireAuth } from '../pageUtils.js';

// ─── Kullanıcı Detay Modal ────────────────────────────────────────────────────
function showUserDetailModal(userId: string, users: any[]): void {
  const u = users.find((x: any) => String(x.id) === String(userId));
  if (!u) { window.showToast?.('Kullanıcı verisi bulunamadı.', 'warn'); return; }

  const existing = document.getElementById('admin-user-modal');
  if (existing) existing.remove();

  const modal = document.createElement('dialog');
  modal.id = 'admin-user-modal';
  modal.className = 'admin-modal';

  const created = u.created_at
    ? new Date(u.created_at).toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric' })
    : '—';
  const lastLogin = u.last_login_at
    ? new Date(u.last_login_at).toLocaleString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
    : '—';
  const planBadge = `<span class="badge ${u.role}">${(u.role ?? 'free').toUpperCase()}</span>`;
  const statusBadge = u.is_active
    ? `<span style="color:var(--pos);font-weight:600">● Aktif</span>`
    : `<span style="color:var(--neg);font-weight:600">● Pasif</span>`;

  modal.innerHTML = `
    <div class="admin-modal-inner">
      <div class="admin-modal-header">
        <div class="admin-modal-avatar">${(u.email?.[0] ?? '?').toUpperCase()}</div>
        <div>
          <div class="admin-modal-email">${u.email ?? '—'}</div>
          <div class="admin-modal-meta">${planBadge} ${statusBadge}</div>
        </div>
        <button class="admin-modal-close" type="button" aria-label="Kapat">✕</button>
      </div>
      <table class="admin-modal-table">
        <tr><td>Kullanıcı ID</td><td>${u.id}</td></tr>
        <tr><td>Ad Soyad</td><td>${u.full_name ?? '—'}</td></tr>
        <tr><td>Kayıt tarihi</td><td>${created}</td></tr>
        <tr><td>Son giriş</td><td>${lastLogin}</td></tr>
        <tr><td>E-posta doğrulama</td><td>${u.email_verified ? '✓ Doğrulandı' : '✗ Bekliyor'}</td></tr>
        <tr><td>2FA</td><td>${u.totp_enabled ? '✓ Aktif' : '—'}</td></tr>
        <tr><td>Stripe ID</td><td>${u.stripe_customer_id ?? '—'}</td></tr>
        <tr><td>API erişimi</td><td>${u.api_access ? '✓ Açık' : '—'}</td></tr>
      </table>
      <div class="admin-modal-actions">
        ${u.is_active
          ? `<button class="btn btn-sm btn-outline-secondary" data-action="deactivate" data-uid="${u.id}">Pasifleştir</button>`
          : `<button class="btn btn-sm btn-warning" data-action="activate" data-uid="${u.id}">Aktifleştir</button>`}
        <button class="btn btn-sm btn-outline-secondary" data-action="close">Kapat</button>
      </div>
    </div>`;

  document.body.appendChild(modal);
  modal.showModal();

  modal.addEventListener('click', (e) => {
    const target = e.target as HTMLElement;
    const btn = target.closest<HTMLButtonElement>('button[data-action]');
    if (!btn) { if (e.target === modal) modal.close(); return; }

    const action = btn.dataset['action'];
    if (action === 'close') { modal.close(); return; }

    if (action === 'activate' || action === 'deactivate') {
      const uid = btn.dataset['uid'];
      const body = JSON.stringify({ is_active: action === 'activate' });
      fetch(`/api/admin/users/${uid}/status`, {
        method: 'PATCH', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body,
      })
        .then(r => r.ok ? r.json() : Promise.reject(r.status))
        .then(() => {
          window.showToast?.(`Kullanıcı ${action === 'activate' ? 'aktifleştirildi' : 'pasifleştirildi'}.`, 'success');
          modal.close();
        })
        .catch(() => window.showToast?.('İşlem başarısız. Endpoint canlı olmayabilir.', 'error'));
    }
  });

  modal.addEventListener('close', () => modal.remove());
}

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
        const users: any[] = data.data?.users || [];
        const rows = users.length
          ? users.map((u: any) => `<tr><td>${u.id}</td><td>${u.email}</td><td><span class="badge ${u.role}">${u.role.toUpperCase()}</span></td><td>${u.is_active ? 'Aktif' : 'Pasif'}</td><td><button class="btn btn-sm btn-outline-secondary" data-user-detail="${u.id}">Detay</button></td></tr>`).join('')
          : '<tr><td colspan="5">Kullanıcı bulunamadı.</td></tr>';
        content.innerHTML = `<h1>Kullanıcı Yönetimi</h1><div class="admin-toolbar"><input class="form-control" placeholder="E-posta ara" /><select class="form-select"><option>Tüm Planlar</option><option>Free</option><option>Pro</option><option>Ultra</option></select></div><table><thead><tr><th>ID</th><th>E-posta</th><th>Plan</th><th>Durum</th><th>İşlem</th></tr></thead><tbody>${rows}</tbody></table>`;
        content.querySelectorAll<HTMLButtonElement>('[data-user-detail]').forEach((btn) => {
          btn.addEventListener('click', () => {
            showUserDetailModal(btn.dataset['userDetail'] ?? '', users);
          });
        });
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
