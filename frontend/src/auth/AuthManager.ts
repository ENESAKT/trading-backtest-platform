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

type ErrorPayload = {
  ok?: unknown;
  data?: unknown;
  detail?: unknown;
  error?: unknown;
  message?: unknown;
  tr?: unknown;
  en?: unknown;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

async function readJson(res: Response): Promise<ErrorPayload> {
  try {
    return await res.json() as ErrorPayload;
  } catch {
    return {};
  }
}

function cleanValidationMessage(message: string): string {
  return message.replace(/^Value error,\s*/i, '').trim();
}

function formatValidationItem(item: unknown): string {
  if (!isRecord(item)) return '';

  const rawMsg = typeof item['msg'] === 'string' ? item['msg'] : '';
  const msg = cleanValidationMessage(rawMsg);
  const loc = Array.isArray(item['loc']) ? item['loc'].map(String) : [];
  const field = loc[loc.length - 1] ?? '';

  if (field === 'email') return 'Geçerli bir e-posta adresi girin.';
  if (field === 'password' && msg) return msg;
  if (field === 'display_name' && msg) return msg;
  if (msg.toLowerCase() === 'field required') return 'Zorunlu alanları doldurun.';
  return msg;
}

function formatAuthError(body: ErrorPayload, fallback: string): string {
  const detail = body.detail ?? body.error ?? body.message ?? body;

  if (typeof detail === 'string') return detail;

  if (Array.isArray(detail)) {
    const messages = detail.map(formatValidationItem).filter(Boolean);
    return messages.length ? messages.join(' ') : fallback;
  }

  if (isRecord(detail)) {
    if (typeof detail['tr'] === 'string') return detail['tr'];
    if (typeof detail['message'] === 'string') return detail['message'];
    if (typeof detail['en'] === 'string') return detail['en'];
    if (Array.isArray(detail['detail'])) {
      const messages = detail['detail'].map(formatValidationItem).filter(Boolean);
      return messages.length ? messages.join(' ') : fallback;
    }
  }

  return fallback;
}

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
    const body = await readJson(res);
    if (res.ok && body.ok) {
      this._setUser(body.data as AuthUser);
      return { ok: true };
    }
    return { ok: false, error: formatAuthError(body, 'Giriş başarısız.') };
  }

  async register(
    email: string,
    password: string,
    display_name: string,
    marketing_consent = false,
    terms_accepted = false,
    privacy_accepted = false,
  ): Promise<{ ok: boolean; error?: string }> {
    const res = await fetch(`${API_BASE}/register`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        password,
        display_name,
        marketing_consent,
        terms_accepted,
        privacy_accepted,
      }),
    });
    const body = await readJson(res);
    if (res.ok && body.ok) return { ok: true };
    return { ok: false, error: formatAuthError(body, 'Kayıt başarısız.') };
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
