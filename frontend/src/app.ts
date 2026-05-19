import type { Timeframe, DataUpdateEvent, PriceUpdateEvent, SymbolInfo } from './types.js';
import type { LayoutMode } from './components/MultiChartLayout.js';
import type { MaliAnalizPanel as MaliAnalizPanelInstance } from './components/MaliAnalizPanel.js';
import type { NewsPanel as NewsPanelInstance } from './components/NewsPanel.js';
import 'bootstrap/dist/css/bootstrap.min.css';
import '../style.css';
import { mountCookieBanner } from './components/CookieBanner.js';
import { installErrorBoundary } from './core/ErrorBoundary.js';
import { analytics } from './core/Analytics.js';
import { i18n } from './i18n/index.js';
import { auth } from './auth/AuthManager.js';
import { planGate, type Feature } from './auth/PlanGate.js';
// Error monitoring removed

i18n.init();
installErrorBoundary();
mountCookieBanner();
const publicPath = window.location.pathname.replace(/\/+$/, '') || '/';
analytics.track('page_view', { path: publicPath });

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch((err) => {
      console.warn('Service worker kaydedilemedi:', err);
    });
  });
}

// ─── Public auth pages ───────────────────────────────────────────────────────


type PublicRenderer = (container: HTMLElement) => void | Promise<void>;
const publicRoutes: Record<string, () => Promise<PublicRenderer>> = {
  '/landing': async () => (await import('./pages/LandingPage.js')).renderLandingPage,
  '/login': async () => (await import('./auth/LoginPage.js')).renderLoginPage,
  '/register': async () => (await import('./auth/RegisterPage.js')).renderRegisterPage,
  '/pricing': async () => (await import('./pages/PricingPage.js')).renderPricingPage,
  '/waitlist': async () => (await import('./pages/WaitlistPage.js')).renderWaitlistPage,
  '/changelog': async () => (await import('./pages/ChangelogPage.js')).renderChangelogPage,
  '/forgot-password': async () => (await import('./pages/ForgotPasswordPage.js')).renderForgotPasswordPage,
  '/reset-password': async () => (await import('./pages/ForgotPasswordPage.js')).renderResetPasswordPage,
  '/verify-email': async () => (await import('./pages/VerifyEmailPage.js')).renderVerifyEmailPage,
  '/onboarding': async () => (await import('./pages/OnboardingPage.js')).renderOnboardingPage,
  '/payment/success': async () => (await import('./pages/PaymentSuccessPage.js')).renderPaymentSuccessPage,
  '/settings': async () => (await import('./pages/SettingsPage.js')).renderSettingsPage,
  '/admin': async () => (await import('./pages/admin/AdminPanel.js')).renderAdminPanel,
  '/legal/terms': async () => (await import('./pages/legal/TermsPage.js')).renderTermsPage,
  '/legal/privacy': async () => (await import('./pages/legal/PrivacyPage.js')).renderPrivacyPage,
  '/legal/cookies': async () => (await import('./pages/legal/CookiesPage.js')).renderCookiesPage,
};
const loadPublicRenderer = publicRoutes[publicPath];
const loadDynamicPublicRenderer = publicPath.startsWith('/shared/')
  ? async () => (await import('./pages/SharedBacktestPage.js')).renderSharedBacktestPage
  : publicPath.startsWith('/terminal/symbol/')
    ? async () => (await import('./pages/Symbol360Page.js')).renderSymbol360Page
    : null;
if (loadPublicRenderer || loadDynamicPublicRenderer) {
  document.getElementById('market-ticker')?.remove();
  document.getElementById('topbar')?.remove();
  document.getElementById('theme-panel')?.remove();
  document.getElementById('app-layout')?.remove();
  const authRoot = document.createElement('main');
  authRoot.id = 'auth-root';
  document.body.appendChild(authRoot);
  await auth.init(); // Initialize auth for public header logic
  const renderer = await (loadPublicRenderer || loadDynamicPublicRenderer)!();
  await renderer(authRoot);
  const { bindPublicPageControls } = await import('./pages/pageUtils.js');
  bindPublicPageControls(authRoot);
} else {

const [
  { dataEngine },
  { PortfolioEngine },
  { MultiChartLayout },
  { Sidebar },
  { PortfolioPanel },
  { StrategyPanel },
  { Screener },
  { SignalFeed },
  { EgitimlerPanel },
  { MaliAnalizPanel },
  { NewsPanel },
  { TR, formatAgo },
  { loadHistorical },
] = await Promise.all([
  import('./core/DataEngine.js'),
  import('./core/PortfolioEngine.js'),
  import('./components/MultiChartLayout.js'),
  import('./components/Sidebar.js'),
  import('./components/PortfolioPanel.js'),
  import('./components/StrategyPanel.js'),
  import('./components/Screener.js'),
  import('./components/SignalFeed.js'),
  import('./components/EgitimlerPanel.js'),
  import('./components/MaliAnalizPanel.js'),
  import('./components/NewsPanel.js'),
  import('./constants/tr.js'),
  import('./core/HistoricalLoader.js'),
]);

// ─── Auth init + User Menu ───────────────────────────────────────────────────

await auth.init();

function mountUserMenu(): void {
  const guestEl   = document.getElementById('user-menu-guest') as HTMLElement;
  const loggedEl  = document.getElementById('user-menu-loggedin') as HTMLElement;
  const avatarBtn = document.getElementById('user-avatar-btn') as HTMLButtonElement;
  const dropdown  = document.getElementById('user-dropdown') as HTMLElement;
  const initialsEl = document.getElementById('user-avatar-initials') as HTMLElement;
  const nameEl    = document.getElementById('user-display-name') as HTMLElement;
  const emailEl   = document.getElementById('user-dropdown-email') as HTMLElement;
  const planBadge = document.getElementById('user-plan-badge') as HTMLElement;
  const logoutBtn = document.getElementById('logout-btn') as HTMLButtonElement;

  function render(): void {
    const user = auth.user;
    if (!user) {
      guestEl.hidden  = false;
      loggedEl.hidden = true;
      return;
    }
    guestEl.hidden  = true;
    loggedEl.hidden = false;

    const name = user.display_name || user.email.split('@')[0] || '?';
    const initials = name.slice(0, 2).toUpperCase();
    initialsEl.textContent = initials;
    nameEl.textContent     = name;
    emailEl.textContent    = user.email;
    planBadge.textContent  = user.role.toUpperCase();
    planBadge.dataset['plan'] = user.role;
  }

  // avatar toggle
  avatarBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    const open = !dropdown.hidden;
    dropdown.hidden = open;
    avatarBtn.setAttribute('aria-expanded', String(!open));
  });

  // close on outside click
  document.addEventListener('click', () => {
    if (!dropdown.hidden) {
      dropdown.hidden = true;
      avatarBtn?.setAttribute('aria-expanded', 'false');
    }
  });
  dropdown?.addEventListener('click', (e) => e.stopPropagation());

  // logout
  logoutBtn?.addEventListener('click', async () => {
    logoutBtn.textContent = 'Çıkış yapılıyor…';
    logoutBtn.setAttribute('disabled', 'true');
    await auth.logout();
  });

  // re-render when auth changes
  auth.onChange(render);
  render();
}
mountUserMenu();

// ─── App shell elements ───────────────────────────────────────────────────────

const sidebarEl    = document.getElementById('sidebar')!;
const mainEl       = document.getElementById('main-content')!;
const statusBadge  = document.getElementById('status-badge')!;
const lastUpdateEl = document.getElementById('last-update')!;
const symbolTitle  = document.getElementById('symbol-title')!;
const themePanelToggle = document.getElementById('theme-panel-toggle') as HTMLButtonElement | null;
const themePanel = document.getElementById('theme-panel') as HTMLElement | null;
const themePanelClose = document.getElementById('theme-panel-close') as HTMLButtonElement | null;
const tabBtns      = document.querySelectorAll<HTMLElement>('[data-tab]');
const LS_LAST_TAB  = 'piyasapilot_last_tab';
const LS_THEME     = 'piyasapilot_theme';
const LS_ACCENT    = 'piyasapilot_accent';
type AppTab = 'chart' | 'portfolio' | 'strategy' | 'screener' | 'signals' | 'education' | 'financials' | 'news';
const TABS: AppTab[] = ['chart', 'portfolio', 'strategy', 'screener', 'signals', 'education', 'financials', 'news'];
type RequiredTier = 'free' | 'pro' | 'ultra';
interface TabGate {
  feature: Feature;
  title: string;
  description: string;
  requiredTier: RequiredTier;
}

const TAB_GATES: Partial<Record<AppTab, TabGate>> = {
  portfolio: {
    feature: 'portfolio',
    title: 'Portföy için kayıt gerekli',
    description: 'Sanal portföy ve işlem geçmişi için ücretsiz hesap oluşturun.',
    requiredTier: 'free',
  },
  strategy: {
    feature: 'backtest',
    title: 'Backtest için kayıt gerekli',
    description: 'Strateji çalıştırma ve rapor kaydetme ücretsiz hesapla açılır.',
    requiredTier: 'free',
  },
  screener: {
    feature: 'scanner',
    title: 'Tarama Pro planla açılır',
    description: 'Piyasa tarayıcı ve geniş sembol filtreleri için planınızı yükseltin.',
    requiredTier: 'pro',
  },
  signals: {
    feature: 'signals',
    title: 'Sinyaller için kayıt gerekli',
    description: 'Canlı sinyal akışı ve uyarılar ücretsiz hesapla açılır.',
    requiredTier: 'free',
  },
  financials: {
    feature: 'mali_analiz',
    title: 'Mali analiz için kayıt gerekli',
    description: 'Bilanço, oran ve şirket karşılaştırmaları ücretsiz hesapla açılır.',
    requiredTier: 'free',
  },
};

// ─── Shortcut overlay ─────────────────────────────────────────────────────────

function buildShortcutOverlay(): void {
  if (document.getElementById('shortcut-overlay')) return;
  const overlay = document.createElement('div');
  overlay.id = 'shortcut-overlay';
  overlay.className = 'shortcut-overlay hidden';
  overlay.innerHTML = `
    <div class="shortcut-modal">
      <div class="shortcut-modal-header">
        <h3>Klavye Kısayolları</h3>
        <button class="shortcut-close" id="shortcut-close">✕</button>
      </div>
      <div class="shortcut-grid">
        <div class="shortcut-section">
          <h4>Sekmeler</h4>
          <div class="shortcut-row"><kbd>1</kbd><span>Grafik</span></div>
          <div class="shortcut-row"><kbd>2</kbd><span>Portföy</span></div>
          <div class="shortcut-row"><kbd>3</kbd><span>Strateji</span></div>
          <div class="shortcut-row"><kbd>4</kbd><span>Tarama</span></div>
          <div class="shortcut-row"><kbd>5</kbd><span>Sinyaller</span></div>
          <div class="shortcut-row"><kbd>6</kbd><span>Eğitim</span></div>
          <div class="shortcut-row"><kbd>7</kbd><span>Finansallar</span></div>
          <div class="shortcut-row"><kbd>8</kbd><span>Haberler</span></div>
        </div>
        <div class="shortcut-section">
          <h4>Grafik</h4>
          <div class="shortcut-row"><kbd>G</kbd><span>Layout döngüsü (1×1 → 1×2 → 2×1 → 2×2)</span></div>
          <div class="shortcut-row"><kbd>F</kbd><span>Tam ekran</span></div>
          <div class="shortcut-row"><kbd>B</kbd><span>Bollinger Bantları</span></div>
          <div class="shortcut-row"><kbd>R</kbd><span>RSI</span></div>
        </div>
        <div class="shortcut-section">
          <h4>Genel</h4>
          <div class="shortcut-row"><kbd>?</kbd><span>Bu pencereyi aç / kapat</span></div>
          <div class="shortcut-row"><kbd>Esc</kbd><span>Kapat / İptal</span></div>
        </div>
      </div>
    </div>`;
  document.body.appendChild(overlay);
  overlay.addEventListener('click', (e) => {
    if ((e.target as HTMLElement).id === 'shortcut-overlay') toggleShortcutOverlay(false);
  });
  document.getElementById('shortcut-close')!.addEventListener('click', () => toggleShortcutOverlay(false));
}

function toggleShortcutOverlay(force?: boolean): void {
  const el = document.getElementById('shortcut-overlay');
  if (!el) return;
  const open = force !== undefined ? force : el.classList.contains('hidden');
  el.classList.toggle('hidden', !open);
}

const ACCENT_PRESETS: Record<string, Record<string, string>> = {
  amber: {
    '--amber': '#ffb020',
    '--blue': '#ffb020',
    '--yellow': '#ffb020',
    '--amber-bg': 'rgba(255, 176, 32, 0.10)',
  },
  green: {
    '--amber': '#00c875',
    '--blue': '#00c875',
    '--yellow': '#00c875',
    '--amber-bg': 'rgba(0, 200, 117, 0.10)',
  },
  cyan: {
    '--amber': '#00d4ff',
    '--blue': '#00d4ff',
    '--yellow': '#00d4ff',
    '--amber-bg': 'rgba(0, 212, 255, 0.10)',
  },
  purple: {
    '--amber': '#b78bff',
    '--blue': '#b78bff',
    '--yellow': '#b78bff',
    '--amber-bg': 'rgba(183, 139, 255, 0.10)',
  },
  red: {
    '--amber': '#ff4757',
    '--blue': '#ff4757',
    '--yellow': '#ff4757',
    '--amber-bg': 'rgba(255, 71, 87, 0.10)',
  },
};

function isAppTab(value: string | null | undefined): value is AppTab {
  return !!value && TABS.includes(value as AppTab);
}

function applyTabLocks(): void {
  document.querySelectorAll<HTMLElement>('[data-tab]').forEach((btn) => {
    const tab = btn.dataset['tab'];
    if (!isAppTab(tab)) return;

    const gate = TAB_GATES[tab];
    const locked = Boolean(gate && !planGate.canAccess(gate.feature));
    btn.classList.toggle('locked', locked);

    if (locked && gate) {
      btn.title = `${gate.title}: ${gate.description}`;
      if (!btn.querySelector('.tab-lock')) {
        btn.insertAdjacentHTML('beforeend', `
          <span class="tab-lock" aria-hidden="true">
            <svg class="icon-svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="10" rx="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
          </span>
        `);
      }
      return;
    }

    btn.removeAttribute('title');
    btn.querySelector('.tab-lock')?.remove();
  });
}

function canOpenSymbol(info: SymbolInfo): boolean {
  if (planGate.isGroupAllowed(info.group)) return true;
  planGate.showPlanGate({
    title: `${info.symbol.replace('.IS', '')} kilitli`,
    description: 'Misafir erişiminde yalnızca seçili piyasa grupları açıktır. Bu sembol için ücretsiz kayıt olun veya planınızı yükseltin.',
    requiredTier: 'free',
  });
  return false;
}

function applyTheme(theme: string, accent: string): void {
  const normalizedTheme = theme === 'light' ? 'light' : 'dark';
  const normalizedAccent = ACCENT_PRESETS[accent] ? accent : 'amber';
  document.documentElement.dataset['theme'] = normalizedTheme;
  const preset = ACCENT_PRESETS[normalizedAccent]!;
  Object.entries(preset).forEach(([key, value]) => {
    document.documentElement.style.setProperty(key, value);
  });
  document.querySelectorAll<HTMLButtonElement>('[data-theme-choice]').forEach((btn) => {
    const isActive = btn.dataset['themeChoice'] === normalizedTheme;
    btn.classList.toggle('active', isActive);
    btn.classList.toggle('btn-warning', isActive);
    btn.classList.toggle('btn-outline-secondary', !isActive);
  });
  document.querySelectorAll<HTMLButtonElement>('[data-accent-choice]').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset['accentChoice'] === normalizedAccent);
  });
  window.dispatchEvent(new CustomEvent('piyasapilot:theme-change', {
    detail: { theme: normalizedTheme, accent: normalizedAccent },
  }));
}

function initThemePanel(): void {
  const savedTheme = localStorage.getItem(LS_THEME) || 'dark';
  const savedAccent = localStorage.getItem(LS_ACCENT) || 'amber';
  applyTheme(savedTheme, savedAccent);

  themePanelToggle?.addEventListener('click', () => {
    if (!themePanel) return;
    const isOpen = !themePanel.hidden;
    themePanel.hidden = isOpen;
    themePanelToggle.classList.toggle('active', !isOpen);
    themePanelToggle.setAttribute('aria-expanded', String(!isOpen));
  });

  themePanelClose?.addEventListener('click', () => {
    if (!themePanel) return;
    themePanel.hidden = true;
    themePanelToggle?.classList.remove('active');
    themePanelToggle?.setAttribute('aria-expanded', 'false');
  });

  document.querySelectorAll<HTMLButtonElement>('[data-theme-choice]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const theme = btn.dataset['themeChoice'] || 'dark';
      const accent = localStorage.getItem(LS_ACCENT) || 'amber';
      localStorage.setItem(LS_THEME, theme);
      applyTheme(theme, accent);
    });
  });

  document.querySelectorAll<HTMLButtonElement>('[data-accent-choice]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const accent = btn.dataset['accentChoice'] || 'amber';
      const theme = localStorage.getItem(LS_THEME) || 'dark';
      localStorage.setItem(LS_ACCENT, accent);
      applyTheme(theme, accent);
    });
  });
}

initThemePanel();

// ─── Mobile sidebar drawer ────────────────────────────────────────────────────
function initMobileSidebar(): void {
  const btn      = document.getElementById('mobile-sidebar-btn') as HTMLButtonElement | null;
  const sidebar  = document.getElementById('sidebar');
  const backdrop = document.getElementById('sidebar-backdrop');
  if (!btn || !sidebar || !backdrop) return;

  const open = (): void => {
    sidebar.classList.add('mobile-open');
    backdrop.classList.add('visible');
    btn.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
  };
  const close = (): void => {
    sidebar.classList.remove('mobile-open');
    backdrop.classList.remove('visible');
    btn.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  };

  btn.addEventListener('click', () => {
    sidebar.classList.contains('mobile-open') ? close() : open();
  });
  backdrop.addEventListener('click', close);

  // Sembol seçilince drawer'ı kapat (mobilde)
  sidebar.addEventListener('click', (e) => {
    const target = e.target as HTMLElement;
    if (target.closest('.sym-row, .sym-item, [data-symbol]')) {
      close();
    }
  });

  // Ekran genişlediğinde otomatik kapat
  const mq = window.matchMedia('(max-width: 768px)');
  mq.addEventListener('change', (ev) => { if (!ev.matches) close(); });
}

initMobileSidebar();

// ─── Panel containers ─────────────────────────────────────────────────────────

function createPanel(id: string): HTMLElement {
  const el = document.createElement('div');
  el.id = id;
  el.className = 'tab-panel';
  el.style.display = 'none';
  mainEl.appendChild(el);
  return el;
}

const chartEl     = createPanel('panel-chart');
const portfolioEl = createPanel('panel-portfolio');
const strategyEl  = createPanel('panel-strategy');
const screenerEl  = createPanel('panel-screener');
const signalsEl   = createPanel('panel-signals');
const educationEl = createPanel('panel-education');
const financialsEl= createPanel('panel-financials');
const newsEl      = createPanel('panel-news');

// Inject Financials tab button if not exists
let financialsBtn = document.querySelector('[data-tab="financials"]');
if (!financialsBtn) {
  const tabsContainer = document.querySelector('.topbar-tabs');
  if (tabsContainer) {
    const btn = document.createElement('button');
    btn.dataset.tab = 'financials';
    btn.className = 'tab-btn';
    btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg><span>${TR.FINANCIALS}</span><span class="shortcut">7</span>`;
    const educationBtn = tabsContainer.querySelector('[data-tab="education"]');
    educationBtn?.after(btn);
    // Re-bind click event to new button
    btn.addEventListener('click', () => showTab('financials'));
  }
}

// Inject News tab button if not exists
if (!document.querySelector('[data-tab="news"]')) {
  const tabsContainer = document.querySelector('.topbar-tabs');
  if (tabsContainer) {
    const btn = document.createElement('button');
    btn.dataset.tab = 'news';
    btn.className = 'tab-btn';
    btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 20H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h10l6 6v8a2 2 0 0 1-2 2z"/><polyline points="17 1 17 7 23 7"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg><span>Haberler</span><span class="shortcut">8</span><span class="tab-news-badge" id="tab-news-badge" hidden></span>`;
    tabsContainer.appendChild(btn);
    btn.addEventListener('click', () => showTab('news'));
  }
}

applyTabLocks();
auth.onChange(applyTabLocks);

async function refreshNewsBadge(): Promise<void> {
  try {
    const res = await fetch('/api/news/unread-count');
    if (!res.ok) return;
    const data = await res.json() as { count: number };
    const badge = document.getElementById('tab-news-badge');
    if (!badge) return;
    if (data.count > 0) {
      badge.textContent = data.count > 99 ? '99+' : String(data.count);
      badge.title = `${data.count} okunmamış haber`;
      badge.hidden = false;
    } else {
      badge.hidden = true;
    }
  } catch { /* ignore */ }
}
void refreshNewsBadge();
setInterval(() => void refreshNewsBadge(), 60_000);

const portfolioEngine = new PortfolioEngine();
const sidebar         = new Sidebar(sidebarEl);
const multiChart      = new MultiChartLayout(chartEl);
const portfolioPanel  = new PortfolioPanel(portfolioEl, portfolioEngine);
const strategyPanel   = new StrategyPanel(strategyEl);
const educationPanel  = new EgitimlerPanel(educationEl, {
  onOpenChartIndicator: (indicator) => {
    showTab('chart');
    multiChart.setActivePaneIndicator(indicator, true);
  },
  onOpenStrategy: (strategyId) => {
    showTab('strategy');
    strategyPanel.openBlueprint(strategyId);
  }
});
void educationPanel;
let maliAnalizPanel: MaliAnalizPanelInstance | null = null;
function getMaliAnalizPanel(): MaliAnalizPanelInstance {
  if (!maliAnalizPanel) {
    maliAnalizPanel = new MaliAnalizPanel(financialsEl);
  }
  return maliAnalizPanel;
}
let newsPanelInstance: NewsPanelInstance | null = null;
function getNewsPanel(): NewsPanelInstance {
  if (!newsPanelInstance) {
    newsPanelInstance = new NewsPanel(newsEl);
  }
  return newsPanelInstance;
}
// Screener is self-contained; reference kept to prevent GC
const _screener = new Screener(screenerEl, () => dataEngine.getAllCached());
void _screener;
// SignalFeed connects on instantiation; reference kept to prevent GC
const _signalFeed = new SignalFeed(signalsEl);
void _signalFeed;

async function openSymbol(info: SymbolInfo): Promise<void> {
  if (!canOpenSymbol(info)) return;
  symbolTitle.textContent = `${info.name} (${info.symbol})`;
  sidebar.setActiveSymbol(info.symbol);
  multiChart.clearSignals();
  await multiChart.setActivePaneSymbol(info);
  await dataEngine.setActiveSymbol(info);
  // Mali Analiz senkronizasyonu — loadData non-BIST sembolleri zaten yoksayar
  if (maliAnalizPanel) maliAnalizPanel.loadData(info.symbol);
}

async function warmFavoriteTickers(skipSymbol?: string): Promise<void> {
  const favorites = sidebar.getFavoriteSymbols();
  for (const info of favorites) {
    if (info.symbol === skipSymbol) continue;
    try {
      const candles = await loadHistorical(info.symbol, '1d', {
        limit: 3,
        timeoutMs: 8_000,
        assetType: info.assetType,
      });
      const last = candles[candles.length - 1];
      if (!last) continue;
      const prev = candles[candles.length - 2]?.close ?? last.close;
      const changePct = prev !== 0 ? ((last.close - prev) / prev) * 100 : 0;
      sidebar.updateTicker(info.symbol, last.close, changePct);
      portfolioEngine.updatePrices(new Map([[info.symbol, last.close]]));
      portfolioPanel.setCurrentPrice(info.symbol, last.close);
    } catch (err) {
      console.warn('Favori fiyatı yüklenemedi:', info.symbol, err);
    }
  }
}

// ─── Tab routing ──────────────────────────────────────────────────────────────

let activeTab: AppTab | null = null;

function showTab(tab: string, persist = true): void {
  let nextTab: AppTab = isAppTab(tab) ? tab : 'chart';
  const gate = TAB_GATES[nextTab];
  if (gate && !planGate.canAccess(gate.feature)) {
    if (persist) {
      planGate.showPlanGate({
        title: gate.title,
        description: gate.description,
        requiredTier: gate.requiredTier,
      });
    }
    if (activeTab) return;
    nextTab = 'chart';
  }

  activeTab = nextTab;
  document.querySelectorAll<HTMLElement>('[data-tab]').forEach(btn => btn.classList.toggle('active', btn.dataset['tab'] === nextTab));
  chartEl.style.display     = nextTab === 'chart'     ? 'flex' : 'none';
  portfolioEl.style.display = nextTab === 'portfolio' ? 'flex' : 'none';
  strategyEl.style.display  = nextTab === 'strategy'  ? 'flex' : 'none';
  screenerEl.style.display  = nextTab === 'screener'  ? 'flex' : 'none';
  signalsEl.style.display   = nextTab === 'signals'   ? 'flex' : 'none';
  educationEl.style.display = nextTab === 'education' ? 'flex' : 'none';
  financialsEl.style.display= nextTab === 'financials'? 'flex' : 'none';
  newsEl.style.display      = nextTab === 'news'       ? 'flex' : 'none';
  if (nextTab === 'financials') {
    const panel = getMaliAnalizPanel();
    const activeSym = multiChart.getActivePaneSymbol()?.symbol;
    if (activeSym) panel.loadData(activeSym);
  }
  if (nextTab === 'news') getNewsPanel();
  if (persist) localStorage.setItem(LS_LAST_TAB, nextTab);

  // Trigger backtest when strategy tab becomes visible
  if (nextTab === 'strategy' && multiChart.getActivePaneCandles().length > 0) {
    strategyPanel.setCandles(
      multiChart.getActivePaneCandles(),
      multiChart.getActivePaneSymbol().symbol,
      multiChart.getActivePaneTimeframe(),
    );
  }

  // URL deep-link sync
  const url = new URL(window.location.href);
  url.searchParams.set('tab', nextTab);
  const sym = multiChart.getActivePaneSymbol()?.symbol;
  if (sym) url.searchParams.set('symbol', sym);
  history.replaceState(null, '', url.toString());
}

tabBtns.forEach(btn => {
  btn.addEventListener('click', () => showTab(btn.dataset['tab']!));
});

// P0.1 FIX: URL parametresi localStorage'dan ÖNCE okunmalı.
// Yoksa showTab → replaceState URL'yi güncelliyor, ardından applyUrlParams
// artık orijinal ?tab= değerini göremez.
const _bootUrlParams = new URLSearchParams(window.location.search);
const _bootUrlTab    = _bootUrlParams.get('tab');
const savedLastTab   = localStorage.getItem(LS_LAST_TAB);
const initialTab: AppTab = (_bootUrlTab && isAppTab(_bootUrlTab))
  ? _bootUrlTab
  : (isAppTab(savedLastTab) ? savedLastTab : 'chart');
showTab(initialTab, false);

// ─── Keyboard shortcuts (1–7 = tabs, F = fullscreen, G = cycle layout, ? = help) ──────

buildShortcutOverlay();

document.addEventListener('keydown', (e) => {
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLSelectElement) return;
  switch (e.key) {
    case '1': showTab('chart');     break;
    case '2': showTab('portfolio'); break;
    case '3': showTab('strategy');  break;
    case '4': showTab('screener');  break;
    case '5': showTab('signals');   break;
    case '6': showTab('education'); break;
    case '7': showTab('financials'); break;
    case '8': showTab('news');       break;
    case '?': toggleShortcutOverlay(); break;
    case 'Escape': toggleShortcutOverlay(false); break;
    case 'g':
    case 'G': {
      // Layout döngüsü: 1x1 → 1x2 → 2x1 → 2x2 → 1x1
      const cycle: LayoutMode[] = ['1x1', '1x2', '2x1', '2x2'];
      const current = multiChart.getLayout();
      const idx = cycle.indexOf(current);
      const next = cycle[(idx + 1) % cycle.length]!;
      multiChart.setLayout(next);
      break;
    }
    // 'F' and timeframe shortcuts are handled within ChartPanel
  }
});

// ─── URL deep-link boot ───────────────────────────────────────────────────────
// Tab already applied above from URL params; here only symbol is re-applied.
(function applyUrlParams(): void {
  const params = new URLSearchParams(window.location.search);
  const symParam = params.get('symbol');
  if (symParam) {
    const info = dataEngine.getSymbolInfo(symParam) || {
      symbol: symParam, name: symParam, assetType: 'equity', group: 'BIST', currency: 'TRY',
    };
    void openSymbol(info as Parameters<typeof openSymbol>[0]);
  }
})();

// ─── Global Custom Events ─────────────────────────────────────────────────────

window.addEventListener('openSymbolOnChart', async (e: Event) => {
  const customE = e as CustomEvent<{symbol: string}>;
  if (customE.detail && customE.detail.symbol) {
    showTab('chart');
    const info = dataEngine.getSymbolInfo(customE.detail.symbol) || {
      symbol: customE.detail.symbol,
      name: customE.detail.symbol,
      assetType: 'equity',
      group: 'BIST',
      currency: 'TRY'
    };
    await openSymbol(info);
  }
});

window.addEventListener('addSymbolToBacktest', async (e: Event) => {
  const customE = e as CustomEvent<{symbol: string}>;
  if (customE.detail && customE.detail.symbol) {
    showTab('strategy');
    const info = dataEngine.getSymbolInfo(customE.detail.symbol) || {
      symbol: customE.detail.symbol,
      name: customE.detail.symbol,
      assetType: 'equity',
      group: 'BIST',
      currency: 'TRY'
    };
    await openSymbol(info);
  }
});

window.addEventListener('openNewsForSymbol', (e: Event) => {
  const customE = e as CustomEvent<{symbol: string}>;
  const symbol = customE.detail?.symbol;
  if (!symbol) return;
  showTab('news');
  window.dispatchEvent(new CustomEvent('piyasapilot:news-filter-symbol', { detail: { symbol } }));
});

window.addEventListener('openFinancialAnalysis', async (e: Event) => {
  const customE = e as CustomEvent<{symbol: string, date?: string}>;
  if (customE.detail && customE.detail.symbol) {
    showTab('financials');
    void getMaliAnalizPanel().loadData(customE.detail.symbol);
  }
});

// ─── Timeframe change from active ChartPanel ─────────────────────────────────

chartEl.addEventListener('timeframeChange', (e) => {
  const tf = (e as CustomEvent<Timeframe>).detail;
  multiChart.setActivePaneTimeframe(tf);
  // Ana DataEngine'i de güncelle (sidebar ticker'lar için)
  dataEngine.setTimeframe(tf);
});

chartEl.addEventListener('chartRetry', () => {
  const active = multiChart.getActivePaneSymbol();
  if (active) {
    void multiChart.setActivePaneSymbol(active);
  }
});

// ─── Symbol selection from Sidebar ───────────────────────────────────────────

sidebar.onSymbolSelect(openSymbol);
const startupSymbol = sidebar.getStartupSymbol();
void openSymbol(startupSymbol);
void warmFavoriteTickers(startupSymbol.symbol);

// Aktif pane değiştiğinde sembol başlığını güncelle
multiChart.onActivePaneChange(() => {
  const sym = multiChart.getActivePaneSymbol();
  symbolTitle.textContent = `${sym.name} (${sym.symbol})`;
  sidebar.setActiveSymbol(sym.symbol);

  // Strateji panelini yeni pane'in verisiyle güncelle
  const candles = multiChart.getActivePaneCandles();
  if (candles.length > 0) {
    strategyPanel.setCandles(candles, sym.symbol, multiChart.getActivePaneTimeframe());
  }
});

// Pane'de sembol değiştiğinde strateji panelini güncelle
multiChart.onSymbolChange((_paneId, info) => {
  const activePane = multiChart.getActivePane();
  if (activePane && activePane.symbol.symbol === info.symbol) {
    symbolTitle.textContent = `${info.name} (${info.symbol})`;
    sidebar.setActiveSymbol(info.symbol);
  }
});

// Strateji panelinin ürettiği marker'ları aktif pane'in chart'ına çiz.
strategyPanel.onSignalsUpdate(signals => multiChart.setSignals(signals));
strategyPanel.onFocusTime(timestamp => {
  showTab('chart');
  multiChart.focusActivePaneTime(timestamp);
});
strategyPanel.onSymbolSelect(info => {
  showTab('chart');
  void openSymbol(info);
});

// ─── Data Engine events (sidebar ticker + portfolio + screener) ──────────────

dataEngine.onDataUpdate((evt: DataUpdateEvent) => {
  if (evt.candles.length === 0) return;

  // Strateji panelini her zaman besle — chart sekmesindeyken de
  // marker'lar görünür kalsın diye signal pipeline bağlı tutulur.
  strategyPanel.setCandles(evt.candles, evt.symbol, dataEngine.getActiveTimeframe());

  // Update portfolio prices
  const priceMap = new Map<string, number>();
  const last = evt.candles[evt.candles.length - 1]!;
  priceMap.set(evt.symbol, last.close);
  portfolioEngine.updatePrices(priceMap);
  portfolioPanel.setCurrentPrice(evt.symbol, last.close);
});

dataEngine.onPriceUpdate((evt: PriceUpdateEvent) => {
  sidebar.updateTicker(evt.symbol, evt.price, evt.changePct);

  // Update portfolio price map
  const priceMap = new Map([[evt.symbol, evt.price]]);
  portfolioEngine.updatePrices(priceMap);
  portfolioPanel.setCurrentPrice(evt.symbol, evt.price);
});

dataEngine.onStatusChange((status) => {
  const labels: Record<string, string> = {
    live:       TR.LIVE,
    delayed:    TR.DELAYED,
    offline:    TR.OFFLINE,
    connecting: TR.CONNECTING,
  };
  statusBadge.textContent  = labels[status] ?? status;
  statusBadge.className    = `status-badge status-${status}`;
});

window.addEventListener('piyasapilot:data-source', (event) => {
  const source = String((event as CustomEvent<{ source?: string }>).detail?.source || 'unknown');
  const badge: Record<string, { text: string; cls: string }> = {
    redis: { text: 'CANLI', cls: 'status-live' },
    clickhouse: { text: 'CANLI', cls: 'status-live' },
    yfinance: { text: 'GECİKMELİ', cls: 'status-delayed' },
    local_parquet: { text: 'GECİKMELİ', cls: 'status-delayed' },
    'cache-legacy': { text: 'CACHE', cls: 'status-offline' },
    empty: { text: 'VERİ YOK', cls: 'status-offline' },
  };
  const state = badge[source] || { text: 'BİLİNMİYOR', cls: 'status-offline' };
  statusBadge.textContent = state.text;
  statusBadge.className = `status-badge ${state.cls}`;
});

// ─── "Last updated" counter (ticks every second) ──────────────────────────────

setInterval(() => {
  const lastUp = dataEngine.getLastUpdate();
  if (lastUp === 0) {
    lastUpdateEl.textContent = '';
    return;
  }
  const secs = (Date.now() - lastUp) / 1000;
  lastUpdateEl.textContent = `${TR.LAST_UPDATE}: ${formatAgo(secs)}`;
  lastUpdateEl.className = secs < 30 ? 'upd-green' : secs < 60 ? 'upd-yellow' : 'upd-red';
}, 1_000);

// ─── Boot ─────────────────────────────────────────────────────────────────────

// Sidebar will trigger setActiveSymbol from restoreLastSymbol() internally.
// If nothing is in localStorage the default symbol (BTCUSDT) fires automatically.
console.info('PiyasaPilot başlatıldı');
}
