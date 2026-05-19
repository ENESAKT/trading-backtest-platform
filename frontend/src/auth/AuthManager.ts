/**
 * AuthManager — PiyasaPilot oturum yöneticisi.
 *
 * Sorumluluklar:
 *  - /api/auth/me isteğiyle mevcut kullanıcıyı yükle
 *  - Kullanıcı bilgisini belleğe sakla (localStorage'a token yazma)
 *  - Çıkış yap / token yenile
 *  - Plan limiti sorgu yardımcıları
 */

export interface PlanInfo {
  slug: string;
  backtest_pro: boolean;
  scanner: boolean;
  real_time_data: boolean;
  mali_analiz_scope: string;
  multi_chart: boolean;
  api_access: boolean;
  max_watchlist_symbols: number;
  backtest_runs_per_day: number;
  api_calls_per_day: number;
}

export interface UserSettings {
  default_symbol: string;
  default_timeframe: string;
  theme: 'dark' | 'light';
  accent_color: string;
  onboarding_done: boolean;
  language: 'tr' | 'en';
}

export interface AuthUser {
  id: number;
  email: string;
  email_verified: boolean;
  display_name: string | null;
  avatar_url: string | null;
  role: 'free' | 'pro' | 'ultra' | 'admin';
  language: 'tr' | 'en';
  plan: PlanInfo;
  settings: UserSettings;
}

type AuthListener = (user: AuthUser | null) => void;

const API_BASE = '/api/auth';

class AuthManager {
  private _user: AuthUser | null = null;
  private _listeners: AuthListener[] = [];
  private _initialized = false;

  // ── Kullanıcı Bilgisi ────────────────────────────────────────────────

  get user(): AuthUser | null { return this._user; }
  get isLoggedIn(): boolean   { return this._user !== null; }
  get role(): string          { return this._user?.role ?? 'guest'; }

  /** Plan erişim kontrolü */
  can(feature: keyof PlanInfo): boolean {
    const plan = this._user?.plan;
    if (!plan) return false;
    const val = plan[feature];
    if (typeof val === 'boolean') return val;
    if (typeof val === 'number')  return val !== 0;
    if (typeof val === 'string')  return val !== 'none';
    return false;
  }

  isAdmin():  boolean { return this.role === 'admin'; }
  isPro():    boolean { return ['pro', 'ultra', 'admin'].includes(this.role); }
  isUltra():  boolean { return ['ultra', 'admin'].includes(this.role); }

  // ── Başlatma ─────────────────────────────────────────────────────────

  async init(): Promise<void> {
    if (this._initialized) return;
    this._initialized = true;
    await this._fetchMe();
  }

  private async _fetchMe(): Promise<void> {
    try {
      const res = await fetch(`${API_BASE}/me`, { credentials: 'include' });
      if (res.ok) {
        const body = await res.json();
        this._setUser(body.data as AuthUser);
      } else {
        this._setUser(null);
      }
    } catch {
      this._setUser(null);
    }
  }

  // ── Giriş / Kayıt ────────────────────────────────────────────────────

  async login(email: string, password: string, totp_code?: string): Promise<{ ok: boolean; error?: string }> {
    const res = await fetch(`${API_BASE}/login`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, totp_code: totp_code || undefined }),
    });
    const body = await res.json();
    if (res.ok && body.ok) {
      this._setUser(body.data as AuthUser);
      return { ok: true };
    }
    return { ok: false, error: body.detail?.tr ?? body.detail ?? 'Giriş başarısız.' };
  }

  async register(
    email: string,
    password: string,
    display_name: string,
  ): Promise<{ ok: boolean; error?: string }> {
    const res = await fetch(`${API_BASE}/register`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, display_name }),
    });
    const body = await res.json();
    if (res.ok && body.ok) return { ok: true };
    // Validation hatalarını birleştir
    if (res.status === 422 && body.detail) {
      const msgs: string[] = [];
      if (Array.isArray(body.detail)) {
        body.detail.forEach((d: { msg?: string }) => msgs.push(d.msg ?? ''));
      } else {
        msgs.push(body.detail?.tr ?? body.detail);
      }
      return { ok: false, error: msgs.join(' ') };
    }
    return { ok: false, error: body.detail?.tr ?? body.detail ?? 'Kayıt başarısız.' };
  }

  async logout(): Promise<void> {
    try {
      await fetch(`${API_BASE}/logout`, { method: 'POST', credentials: 'include' });
    } catch { /* ignore */ }
    this._setUser(null);
    window.location.href = '/';
  }

  async refreshToken(): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/refresh`, { method: 'POST', credentials: 'include' });
      if (res.ok) {
        await this._fetchMe();
        return true;
      }
    } catch { /* ignore */ }
    this._setUser(null);
    return false;
  }

  // ── Ayarlar ──────────────────────────────────────────────────────────

  async updateSettings(settings: Partial<UserSettings>): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/me/settings`, {
        method: 'PATCH',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      if (res.ok) {
        await this._fetchMe();
        return true;
      }
    } catch { /* ignore */ }
    return false;
  }

  // ── Listener Sistemi ─────────────────────────────────────────────────

  onChange(listener: AuthListener): () => void {
    this._listeners.push(listener);
    return () => {
      this._listeners = this._listeners.filter(l => l !== listener);
    };
  }

  private _setUser(user: AuthUser | null): void {
    this._user = user;
    this._listeners.forEach(l => l(user));
  }
}

// Singleton export
export const auth = new AuthManager();
