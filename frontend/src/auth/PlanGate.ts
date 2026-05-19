/**
 * PlanGate — Freemium erişim kontrolü.
 *
 * Katmanlar:
 *  guest  → BIST30 grafik, 0 backtest, temel özellikler
 *  free   → BIST30 + BIST100, günde 5 backtest
 *  pro    → Tüm semboller, günde 50 backtest, gelişmiş özellikler
 *  ultra  → Her şey sınırsız
 *  admin  → Her şey sınırsız
 */

import { auth } from './AuthManager.js';

// ─── Günlük limit sayacı (localStorage) ─────────────────────────────────────

const LS_BACKTEST_KEY = 'pp_bt_count';   // { date: 'YYYY-MM-DD', count: number }

function todayKey(): string {
  return new Date().toISOString().slice(0, 10);
}

function getBacktestUsage(): { date: string; count: number } {
  try {
    const raw = localStorage.getItem(LS_BACKTEST_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as { date: string; count: number };
      if (parsed.date === todayKey()) return parsed;
    }
  } catch { /* ignore */ }
  return { date: todayKey(), count: 0 };
}

function incrementBacktestUsage(): void {
  const usage = getBacktestUsage();
  usage.count += 1;
  localStorage.setItem(LS_BACKTEST_KEY, JSON.stringify(usage));
}

// ─── Tier helpers ────────────────────────────────────────────────────────────

type Tier = 'guest' | 'free' | 'pro' | 'ultra' | 'admin';

function currentTier(): Tier {
  const user = auth.user;
  if (!user) return 'guest';
  return user.role as Tier;
}

// ─── Backtest limitleri ──────────────────────────────────────────────────────

// Limitler backend/auth/feature_gate.py ile senkron tutulmalı
const BACKTEST_LIMITS: Record<Tier, number> = {
  guest: 0,
  free:  5,   // feature_gate.py: backtest_runs_per_day=5
  pro:   50,
  ultra: Infinity,
  admin: Infinity,
};

export function getBacktestLimit(): number {
  return BACKTEST_LIMITS[currentTier()];
}

export function getRemainingBacktests(): number {
  const limit = getBacktestLimit();
  if (limit === Infinity) return Infinity;
  const used = getBacktestUsage().count;
  return Math.max(0, limit - used);
}

/**
 * Backtest çalıştırılabilir mi?
 * Evet ise usage'ı artırır ve true döner.
 * Hayır ise false döner (artırmaz).
 */
export function consumeBacktest(): boolean {
  const remaining = getRemainingBacktests();
  if (remaining <= 0) return false;
  incrementBacktestUsage();
  return true;
}

// ─── Sembol grup izinleri ────────────────────────────────────────────────────

/** Hangi sembol gruplarına erişim var? */
export function allowedSymbolGroups(): Set<string> {
  const tier = currentTier();
  if (tier === 'guest') {
    // Grup adları symbols.ts ile birebir eşleşmeli
    return new Set(['BIST 30', 'Kripto', 'Döviz / Emtia']);
  }
  if (tier === 'free') {
    return new Set(['BIST 30', 'BIST 100', 'Kripto', 'Döviz / Emtia', 'VİOP', 'ABD Piyasaları']);
  }
  // pro / ultra / admin → sınırsız
  return new Set(['*']);
}

export function isGroupAllowed(groupLabel: string): boolean {
  const allowed = allowedSymbolGroups();
  if (allowed.has('*')) return true;
  return allowed.has(groupLabel);
}

// ─── Plan Gate Modal ─────────────────────────────────────────────────────────

export interface GateOptions {
  title: string;
  description: string;
  requiredTier: 'free' | 'pro' | 'ultra';
}

/**
 * Kullanıcıya yükseltme modalı göster.
 * Kapatıldığında resolve eder.
 */
export function showPlanGate(opts: GateOptions): void {
  // Mevcut bir modal varsa kaldır
  document.getElementById('plan-gate-overlay')?.remove();

  const tier = currentTier();
  const isGuest = tier === 'guest';

  const primaryHref = isGuest ? '/register' : '/pricing';
  const primaryLabel = isGuest ? 'Ücretsiz Kayıt Ol' : 'Planları İncele';

  const overlay = document.createElement('div');
  overlay.id = 'plan-gate-overlay';
  overlay.className = 'plan-gate-overlay';
  overlay.innerHTML = `
    <div class="plan-gate-modal" role="dialog" aria-modal="true" aria-labelledby="pgate-title">
      <div class="plan-gate-icon">🔒</div>
      <div class="plan-gate-title" id="pgate-title">${_esc(opts.title)}</div>
      <div class="plan-gate-desc">${_esc(opts.description)}</div>
      <div class="plan-gate-actions">
        <a href="${primaryHref}" class="btn btn-warning">${primaryLabel}</a>
        <button class="btn btn-outline-secondary" id="pgate-close">Kapat</button>
      </div>
    </div>`;

  document.body.appendChild(overlay);

  const close = (): void => overlay.remove();
  overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
  overlay.querySelector('#pgate-close')?.addEventListener('click', close);
}

function _esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ─── Özellik kontrolü ────────────────────────────────────────────────────────

export type Feature =
  | 'backtest'
  | 'scanner'
  | 'signals'
  | 'portfolio'
  | 'mali_analiz'
  | 'multi_chart'
  | 'news'
  | 'education';

const FEATURE_MIN_TIER: Record<Feature, Tier> = {
  backtest:    'free',
  scanner:     'pro',
  signals:     'free',
  portfolio:   'free',
  mali_analiz: 'free',
  multi_chart: 'pro',
  news:        'guest',   // herkes görebilir
  education:   'guest',   // herkes görebilir
};

const TIER_ORDER: Tier[] = ['guest', 'free', 'pro', 'ultra', 'admin'];

function tierRank(t: Tier): number {
  return TIER_ORDER.indexOf(t);
}

export function canAccess(feature: Feature): boolean {
  const required = FEATURE_MIN_TIER[feature];
  const current  = currentTier();
  return tierRank(current) >= tierRank(required);
}

// ─── Dinamik limit yükleme (API) ─────────────────────────────────────────────

export interface ApiLimits {
  role: string;
  limits: {
    backtest_runs_per_day: number;
    screener_runs_per_day: number;
    watchlist_symbols: number;
    news_access: boolean;
    signals_access: boolean;
    paper_trading: boolean;
  };
}

/**
 * /api/me/limits endpoint'inden kullanıcı limitlerini çeker.
 *
 * Kullanım:
 *   const apiLimits = await fetchLimits();
 *   if (apiLimits) {
 *     const btLimit = apiLimits.limits.backtest_runs_per_day;
 *   }
 *
 * TODO: Bu fonksiyonun döndürdüğü değeri BACKTEST_LIMITS gibi statik
 *       nesnelerin yerine kullanacak bir mekanizma eklenmeli.
 *       Şu an BACKTEST_LIMITS hâlâ statik değerlere dayanmaktadır.
 */
export async function fetchLimits(): Promise<ApiLimits | null> {
  try {
    const res = await fetch('/api/me/limits');
    if (!res.ok) return null;
    return await res.json() as ApiLimits;
  } catch {
    return null;
  }
}

// ─── Singleton export ────────────────────────────────────────────────────────
export const planGate = {
  currentTier,
  getBacktestLimit,
  getRemainingBacktests,
  consumeBacktest,
  allowedSymbolGroups,
  isGroupAllowed,
  canAccess,
  showPlanGate,
  fetchLimits,
};
