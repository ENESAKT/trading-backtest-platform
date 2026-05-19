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
    ? `<span style="color:var(--green);font-weight:600">● Aktif</span>`
    : `<span style="color:var(--red);font-weight:600">● Pasif</span>`;

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

      <div style="margin-bottom:12px">
        <label style="font-size:11px;color:var(--text);display:block;margin-bottom:4px">Rol Değiştir</label>
        <div style="display:flex;gap:6px;flex-wrap:wrap">
          ${['free','pro','ultra','admin'].map(r =>
            `<button class="btn btn-sm ${r === u.role ? 'btn-warning' : 'btn-outline-secondary'}"
              data-action="role" data-role="${r}" data-uid="${u.id}">${r.toUpperCase()}</button>`
          ).join('')}
        </div>
      </div>

      <table class="admin-modal-table">
        <tr><td>Kullanıcı ID</td><td>${u.id}</td></tr>
        <tr><td>Ad Soyad</td><td>${u.full_name ?? '—'}</td></tr>
        <tr><td>Kayıt tarihi</td><td>${created}</td></tr>
        <tr><td>Son giriş</td><td>${lastLogin}</td></tr>
        <tr><td>E-posta doğrulama</td><td>${u.email_verified ? '✓ Doğrulandı' : '✗ Bekliyor'}</td></tr>
        <tr><td>2FA</td><td>${u.totp_enabled ? '✓ Aktif' : '—'}</td></tr>
        <tr><td>Stripe ID</td><td style="font-family:var(--font-mono);font-size:11px">${u.stripe_customer_id ?? '—'}</td></tr>
        <tr><td>API erişimi</td><td>${u.api_access ? '✓ Açık' : '—'}</td></tr>
      </table>
      <div class="admin-modal-actions">
        ${u.is_active
          ? `<button class="btn btn-sm btn-outline-secondary" data-action="deactivate" data-uid="${u.id}">Pasifleştir</button>`
          : `<button class="btn btn-sm btn-warning" data-action="activate" data-uid="${u.id}">Aktifleştir</button>`}
        <button class="btn btn-sm btn-outline-secondary" data-action="revoke-sessions" data-uid="${u.id}">Oturumları Kapat</button>
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
    const uid = btn.dataset['uid'];

    if (action === 'close') { modal.close(); return; }

    if (action === 'role') {
      const role = btn.dataset['role'];
      fetch(`/api/admin/users/${uid}/role`, {
        method: 'PATCH', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role }),
      })
        .then(r => r.ok ? r.json() : Promise.reject(r.status))
        .then(() => { window.showToast?.(`Rol ${role?.toUpperCase()} olarak güncellendi.`, 'success'); modal.close(); })
        .catch(() => window.showToast?.('Rol güncellenemedi.', 'error'));
      return;
    }

    if (action === 'activate' || action === 'deactivate') {
      const endpoint = action === 'deactivate' ? 'ban' : 'unban';
      fetch(`/api/admin/users/${uid}/${endpoint}`, { method: 'POST', credentials: 'include' })
        .then(r => r.ok ? r.json() : Promise.reject(r.status))
        .then(() => { window.showToast?.(`Kullanıcı ${action === 'activate' ? 'aktifleştirildi' : 'pasifleştirildi'}.`, 'success'); modal.close(); })
        .catch(() => window.showToast?.('İşlem başarısız.', 'error'));
      return;
    }

    if (action === 'revoke-sessions') {
      fetch(`/api/admin/users/${uid}/sessions`, { method: 'DELETE', credentials: 'include' })
        .then(r => r.ok ? r.json() : Promise.reject(r.status))
        .then(() => { window.showToast?.('Tüm oturumlar kapatıldı.', 'success'); modal.close(); })
        .catch(() => window.showToast?.('Oturum kapatma başarısız.', 'error'));
    }
  });

  modal.addEventListener('close', () => modal.remove());
}

// ─── Yardımcılar ─────────────────────────────────────────────────────────────
function fmt(d: string | null): string {
  if (!d) return '—';
  return new Date(d).toLocaleString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function pct(v: number): string {
  const c = v >= 0 ? 'var(--green)' : 'var(--red)';
  return `<span style="color:${c}">${v >= 0 ? '+' : ''}${v.toFixed(2)}%</span>`;
}

function roleBadge(role: string): string {
  const colors: Record<string, string> = { free: 'var(--text)', pro: 'var(--amber)', ultra: 'var(--cyan)', admin: 'var(--red)' };
  return `<span style="color:${colors[role] ?? 'var(--text)'};font-weight:600">${role.toUpperCase()}</span>`;
}

const SKELETON = '<div class="skeleton-wrap"><div class="skeleton skeleton-title"></div><div class="skeleton skeleton-row"></div><div class="skeleton skeleton-row"></div><div class="skeleton skeleton-row"></div></div>';

// ─── Tab Renderers ────────────────────────────────────────────────────────────
async function renderOverview(content: HTMLElement): Promise<void> {
  content.innerHTML = SKELETON;
  try {
    const res = await fetch('/api/admin/overview', { credentials: 'include' });
    const data = await res.json();
    const s = data.data || {};
    content.innerHTML = `
      <h1>Özet</h1>
      <div class="metric-grid">
        <span>Toplam Kullanıcı<b>${s.users_total ?? '-'}</b></span>
        <span>Aktif Kullanıcı<b>${s.active_users ?? '-'}</b></span>
        <span>Pro<b>${s.pro_users ?? '-'}</b></span>
        <span>Ultra<b>${s.ultra_users ?? '-'}</b></span>
        <span>Aktif Oturum<b>${s.active_sessions ?? '-'}</b></span>
        <span>Abonelik (aktif)<b>${s.subscriptions_active ?? '-'}</b></span>
        <span>Gecikmeli Ödeme<b style="color:var(--red)">${s.subscriptions_past_due ?? '-'}</b></span>
      </div>
      <h1 style="margin-top:24px">Kullanım (Son 30 Gün)</h1>
      <div id="admin-usage-table">Yükleniyor...</div>`;
    _loadUsageTable(content.querySelector<HTMLElement>('#admin-usage-table')!);
  } catch {
    content.innerHTML = _errHtml();
  }
}

async function _loadUsageTable(el: HTMLElement): Promise<void> {
  try {
    const res = await fetch('/api/admin/usage-stats?days=30', { credentials: 'include' });
    const data = await res.json();
    const stats: any[] = data.data?.stats || [];
    if (!stats.length) { el.innerHTML = '<p style="color:var(--text-dim)">Kullanım verisi bulunamadı.</p>'; return; }
    el.innerHTML = `<table>
      <thead><tr><th>E-posta</th><th>Plan</th><th>Backtest (30g)</th><th>API (30g)</th><th>Son Aktif</th></tr></thead>
      <tbody>${stats.map(s => `
        <tr>
          <td>${s.email}</td>
          <td>${roleBadge(s.role)}</td>
          <td>${s.total_backtests}</td>
          <td>${s.total_api_calls}</td>
          <td>${s.last_active ? new Date(s.last_active).toLocaleDateString('tr-TR') : '—'}</td>
        </tr>`).join('')}
      </tbody></table>`;
  } catch {
    el.innerHTML = '<p style="color:var(--text-dim)">Kullanım verisi yüklenemedi.</p>';
  }
}

async function renderUsers(content: HTMLElement): Promise<void> {
  content.innerHTML = SKELETON;
  try {
    const res = await fetch('/api/admin/users?limit=50', { credentials: 'include' });
    const data = await res.json();
    const users: any[] = data.data?.users || [];
    const rows = users.length
      ? users.map((u: any) => `
        <tr>
          <td style="font-size:11px;color:var(--text-dim)">${u.id}</td>
          <td>${u.email}</td>
          <td>${roleBadge(u.role)}</td>
          <td>${u.is_active ? '<span style="color:var(--green)">● Aktif</span>' : '<span style="color:var(--red)">● Pasif</span>'}</td>
          <td>${u.last_login_at ? new Date(u.last_login_at).toLocaleDateString('tr-TR') : '—'}</td>
          <td><button class="btn btn-sm btn-outline-secondary" data-user-detail="${u.id}">Detay</button></td>
        </tr>`).join('')
      : '<tr><td colspan="6">Kullanıcı bulunamadı.</td></tr>';
    content.innerHTML = `
      <h1>Kullanıcı Yönetimi</h1>
      <div class="admin-toolbar">
        <input class="form-control" id="admin-user-search" placeholder="E-posta ara..." style="max-width:260px"/>
        <select class="form-select" id="admin-role-filter" style="max-width:160px">
          <option value="">Tüm Planlar</option>
          <option>free</option><option>pro</option><option>ultra</option><option>admin</option>
        </select>
        <span style="margin-left:auto;color:var(--text-dim);font-size:12px">${users.length} kullanıcı</span>
      </div>
      <table id="admin-users-table">
        <thead><tr><th>ID</th><th>E-posta</th><th>Plan</th><th>Durum</th><th>Son Giriş</th><th>İşlem</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
    content.querySelectorAll<HTMLButtonElement>('[data-user-detail]').forEach((btn) => {
      btn.addEventListener('click', () => showUserDetailModal(btn.dataset['userDetail'] ?? '', users));
    });
    // Arama
    const searchInput = content.querySelector<HTMLInputElement>('#admin-user-search');
    const roleFilter = content.querySelector<HTMLSelectElement>('#admin-role-filter');
    const tbody = content.querySelector<HTMLElement>('#admin-users-table tbody');
    const filterRows = () => {
      const q = searchInput?.value.toLowerCase() ?? '';
      const role = roleFilter?.value ?? '';
      tbody?.querySelectorAll('tr').forEach((tr) => {
        const email = tr.querySelector('td:nth-child(2)')?.textContent?.toLowerCase() ?? '';
        const r = tr.querySelector('td:nth-child(3)')?.textContent?.toLowerCase() ?? '';
        tr.hidden = (!!q && !email.includes(q)) || (!!role && !r.includes(role));
      });
    };
    searchInput?.addEventListener('input', filterRows);
    roleFilter?.addEventListener('change', filterRows);
  } catch {
    content.innerHTML = _errHtml();
  }
}

async function renderBacktestHistory(content: HTMLElement): Promise<void> {
  content.innerHTML = SKELETON;
  try {
    const res = await fetch('/api/admin/backtest-history?limit=100', { credentials: 'include' });
    const data = await res.json();
    const runs: any[] = data.data?.runs || [];
    const rows = runs.length
      ? runs.map((r: any) => `
        <tr>
          <td style="font-size:11px;color:var(--text-dim);max-width:100px;overflow:hidden;text-overflow:ellipsis">${r.id?.slice(0, 8)}...</td>
          <td>${r.user_email ?? '<span style="color:var(--text-dim)">misafir</span>'}</td>
          <td><strong>${r.symbol}</strong></td>
          <td>${r.strategy_name}</td>
          <td>${r.interval}</td>
          <td>${pct(r.return_pct ?? 0)}</td>
          <td style="font-size:11px">${r.created_at ? new Date(r.created_at).toLocaleString('tr-TR', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' }) : '—'}</td>
        </tr>`).join('')
      : '<tr><td colspan="7">Backtest geçmişi bulunamadı.</td></tr>';
    content.innerHTML = `
      <h1>Backtest Geçmişi</h1>
      <div class="admin-toolbar">
        <input class="form-control" id="bt-search" placeholder="E-posta veya sembol ara..." style="max-width:280px"/>
        <span style="margin-left:auto;color:var(--text-dim);font-size:12px">${runs.length} kayıt</span>
      </div>
      <table id="bt-table">
        <thead><tr><th>Run ID</th><th>Kullanıcı</th><th>Sembol</th><th>Strateji</th><th>TF</th><th>Getiri</th><th>Tarih</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
    const btSearch = content.querySelector<HTMLInputElement>('#bt-search');
    const btTbody = content.querySelector<HTMLElement>('#bt-table tbody');
    btSearch?.addEventListener('input', () => {
      const q = btSearch.value.toLowerCase();
      btTbody?.querySelectorAll('tr').forEach((tr) => {
        tr.hidden = !!q && !tr.textContent?.toLowerCase().includes(q);
      });
    });
  } catch {
    content.innerHTML = _errHtml();
  }
}

async function renderPlanMatrix(content: HTMLElement): Promise<void> {
  content.innerHTML = SKELETON;
  try {
    const res = await fetch('/api/admin/plan-matrix', { credentials: 'include' });
    const data = await res.json();
    const matrix = data.data?.matrix || {};
    const plans = Object.keys(matrix);
    const features: Record<string, string> = {
      backtest_per_day: 'Günlük Backtest',
      symbols: 'Semboller',
      api_access: 'API Erişimi',
      signals: 'Sinyal/Gün',
      real_time: 'Gerçek Zamanlı',
    };
    content.innerHTML = `
      <h1>Plan Yetki Matrisi</h1>
      <p style="color:var(--text);font-size:13px;margin-bottom:16px">Her planın hangi özelliklere erişimi olduğu</p>
      <table class="plan-matrix-table">
        <thead>
          <tr>
            <th>Özellik</th>
            ${plans.map(p => `<th style="text-align:center">${roleBadge(p)}</th>`).join('')}
          </tr>
        </thead>
        <tbody>
          ${Object.entries(features).map(([key, label]) => `
          <tr>
            <td>${label}</td>
            ${plans.map(p => {
              const v = matrix[p]?.[key];
              let display: string;
              if (typeof v === 'boolean') display = v ? '✓' : '✗';
              else if (v === -1) display = '∞';
              else display = String(v ?? '—');
              const color = v === true || v === -1 ? 'var(--green)' : v === false ? 'var(--text-dim)' : 'var(--text-bold)';
              return `<td style="text-align:center;color:${color};font-weight:600">${display}</td>`;
            }).join('')}
          </tr>`).join('')}
        </tbody>
      </table>`;
  } catch {
    content.innerHTML = _errHtml();
  }
}

async function renderSubscriptions(content: HTMLElement): Promise<void> {
  content.innerHTML = SKELETON;
  try {
    const res = await fetch('/api/admin/subscriptions?limit=50', { credentials: 'include' });
    const data = await res.json();
    const subs: any[] = data.data?.subscriptions || [];
    const rows = subs.length
      ? subs.map((s: any) => `
        <tr>
          <td>${s.email}</td>
          <td>${roleBadge(s.plan)}</td>
          <td>${s.billing_period}</td>
          <td><span style="color:${s.status === 'active' ? 'var(--green)' : 'var(--amber)'}">${s.status}</span></td>
          <td>${s.current_period_end ? new Date(s.current_period_end).toLocaleDateString('tr-TR') : '—'}</td>
        </tr>`).join('')
      : '<tr><td colspan="5">Aktif abonelik bulunamadı.</td></tr>';
    content.innerHTML = `
      <h1>Abonelikler</h1>
      <table>
        <thead><tr><th>E-posta</th><th>Plan</th><th>Dönem</th><th>Durum</th><th>Bitiş</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <div style="margin-top:16px">
        <a class="btn btn-outline-warning" href="https://dashboard.stripe.com" target="_blank" rel="noreferrer" style="font-size:13px">
          Stripe Dashboard →
        </a>
      </div>`;
  } catch {
    content.innerHTML = _errHtml();
  }
}

async function renderAuditLog(content: HTMLElement): Promise<void> {
  content.innerHTML = SKELETON;
  try {
    const res = await fetch('/api/admin/audit-log?limit=100', { credentials: 'include' });
    const data = await res.json();
    const events: any[] = data.data?.events || [];
    const ACTION_LABELS: Record<string, string> = {
      login: 'Giriş',
      logout: 'Çıkış',
      register: 'Kayıt',
      user_role_change: 'Rol Değişikliği',
      password_reset: 'Şifre Sıfırlama',
      email_verify: 'E-posta Doğrulama',
    };
    const rows = events.length
      ? events.map((e: any) => `
        <tr>
          <td style="font-size:11px">${fmt(e.created_at)}</td>
          <td style="font-size:11px;color:var(--text-dim)">${e.user_id || '—'}</td>
          <td><span style="color:var(--amber)">${ACTION_LABELS[e.action] ?? e.action}</span></td>
          <td style="font-size:11px;color:var(--text-dim)">${e.resource || '—'}</td>
          <td style="font-size:11px;color:var(--text-dim)">${e.ip_address || '—'}</td>
        </tr>`).join('')
      : '<tr><td colspan="5">Denetim kaydı bulunamadı.</td></tr>';
    content.innerHTML = `
      <h1>Audit Log</h1>
      <div class="admin-toolbar">
        <input class="form-control" id="audit-search" placeholder="Aksiyon veya kullanıcı ara..." style="max-width:260px"/>
      </div>
      <table id="audit-table">
        <thead><tr><th>Tarih</th><th>User ID</th><th>Aksiyon</th><th>Kaynak</th><th>IP</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
    const auditSearch = content.querySelector<HTMLInputElement>('#audit-search');
    const auditTbody = content.querySelector<HTMLElement>('#audit-table tbody');
    auditSearch?.addEventListener('input', () => {
      const q = auditSearch.value.toLowerCase();
      auditTbody?.querySelectorAll('tr').forEach(tr => {
        tr.hidden = !!q && !tr.textContent?.toLowerCase().includes(q);
      });
    });
  } catch {
    content.innerHTML = _errHtml();
  }
}

function _errHtml(): string {
  return '<div class="empty-panel"><strong>Veri yüklenemedi</strong><small>Yetkiniz reddedilmiş olabilir veya ilgili endpoint henüz canlı değildir.</small></div>';
}

// ─── Ana Render ───────────────────────────────────────────────────────────────
export async function renderAdminPanel(container: HTMLElement): Promise<void> {
  if (!(await requireAuth(container))) return;
  if (!auth.isAdmin()) {
    container.innerHTML = pageShell('Yetki Yok', `
      <section class="public-state">
        <h1>Yetki yok</h1>
        <p>Admin paneli yalnızca admin rolüyle açılır.</p>
        <a class="btn btn-warning" href="/app">Terminale Dön</a>
      </section>`);
    return;
  }

  container.innerHTML = pageShell('Admin', `
    <section class="admin-panel">
      <aside>
        <div style="font-family:var(--font-sans);font-size:14px;font-weight:700;color:var(--text-bold);padding:4px 0 16px">
          <span style="color:var(--amber)">P</span> PiyasaPilot Admin
        </div>
        <button data-admin-tab="overview" class="active">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
          Özet
        </button>
        <button data-admin-tab="users">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          Kullanıcılar
        </button>
        <button data-admin-tab="backtests">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          Backtest Geçmişi
        </button>
        <button data-admin-tab="plan-matrix">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
          Yetki Matrisi
        </button>
        <button data-admin-tab="subscriptions">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
          Abonelikler
        </button>
        <button data-admin-tab="audit">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          Audit Log
        </button>
      </aside>
      <div class="admin-content" id="admin-content"></div>
    </section>`);

  const content = container.querySelector<HTMLElement>('#admin-content')!;

  const RENDERERS: Record<string, (c: HTMLElement) => Promise<void>> = {
    overview:     renderOverview,
    users:        renderUsers,
    backtests:    renderBacktestHistory,
    'plan-matrix': renderPlanMatrix,
    subscriptions: renderSubscriptions,
    audit:        renderAuditLog,
  };

  const render = async (tab: string) => {
    const fn = RENDERERS[tab];
    if (fn) await fn(content);
  };

  void render('overview');

  container.querySelectorAll<HTMLButtonElement>('[data-admin-tab]').forEach((btn) => {
    btn.addEventListener('click', () => {
      container.querySelectorAll('[data-admin-tab]').forEach((b) => b.classList.toggle('active', b === btn));
      void render(btn.dataset['adminTab'] || 'overview');
    });
  });
}
