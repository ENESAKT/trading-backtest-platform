import type { Timeframe, DataUpdateEvent, PriceUpdateEvent, SymbolInfo } from './types.js';
import 'bootstrap/dist/css/bootstrap.min.css';
import '../style.css';
import { dataEngine } from './core/DataEngine.js';
import { PortfolioEngine } from './core/PortfolioEngine.js';
import { MultiChartLayout, type LayoutMode } from './components/MultiChartLayout.js';
import { Sidebar } from './components/Sidebar.js';
import { PortfolioPanel } from './components/PortfolioPanel.js';
import { StrategyPanel } from './components/StrategyPanel.js';
import { Screener } from './components/Screener.js';
import { SignalFeed } from './components/SignalFeed.js';
import { EgitimlerPanel } from './components/EgitimlerPanel.js';
import { MaliAnalizPanel } from './components/MaliAnalizPanel.js';
import { TR, formatAgo } from './constants/tr.js';
import { loadHistorical } from './core/HistoricalLoader.js';

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
type AppTab = 'chart' | 'portfolio' | 'strategy' | 'screener' | 'signals' | 'education' | 'financials';
const TABS: AppTab[] = ['chart', 'portfolio', 'strategy', 'screener', 'signals', 'education', 'financials'];

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

function isAppTab(value: string | null): value is AppTab {
  return !!value && TABS.includes(value as AppTab);
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
let maliAnalizPanel: MaliAnalizPanel | null = null;
function getMaliAnalizPanel(): MaliAnalizPanel {
  if (!maliAnalizPanel) {
    maliAnalizPanel = new MaliAnalizPanel(financialsEl);
  }
  return maliAnalizPanel;
}
// Screener is self-contained; reference kept to prevent GC
const _screener = new Screener(screenerEl, () => dataEngine.getAllCached());
void _screener;
// SignalFeed connects on instantiation; reference kept to prevent GC
const _signalFeed = new SignalFeed(signalsEl);
void _signalFeed;

async function openSymbol(info: SymbolInfo): Promise<void> {
  symbolTitle.textContent = `${info.name} (${info.symbol})`;
  sidebar.setActiveSymbol(info.symbol);
  multiChart.clearSignals();
  await multiChart.setActivePaneSymbol(info);
  await dataEngine.setActiveSymbol(info);
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

function showTab(tab: string, persist = true): void {
  if (!isAppTab(tab)) tab = 'chart';
  document.querySelectorAll<HTMLElement>('[data-tab]').forEach(btn => btn.classList.toggle('active', btn.dataset['tab'] === tab));
  chartEl.style.display     = tab === 'chart'     ? 'flex' : 'none';
  portfolioEl.style.display = tab === 'portfolio' ? 'flex' : 'none';
  strategyEl.style.display  = tab === 'strategy'  ? 'flex' : 'none';
  screenerEl.style.display  = tab === 'screener'  ? 'flex' : 'none';
  signalsEl.style.display   = tab === 'signals'   ? 'flex' : 'none';
  educationEl.style.display = tab === 'education' ? 'flex' : 'none';
  financialsEl.style.display= tab === 'financials'? 'flex' : 'none';
  if (tab === 'financials') getMaliAnalizPanel(); // Trigger load if switching to financials
  if (persist) localStorage.setItem(LS_LAST_TAB, tab);

  // Trigger backtest when strategy tab becomes visible
  if (tab === 'strategy' && multiChart.getActivePaneCandles().length > 0) {
    strategyPanel.setCandles(
      multiChart.getActivePaneCandles(),
      multiChart.getActivePaneSymbol().symbol,
      multiChart.getActivePaneTimeframe(),
    );
  }
}

tabBtns.forEach(btn => {
  btn.addEventListener('click', () => showTab(btn.dataset['tab']!));
});

const savedLastTab = localStorage.getItem(LS_LAST_TAB);
const initialTab: AppTab = isAppTab(savedLastTab) ? savedLastTab : 'chart';
showTab(initialTab, false);

// ─── Keyboard shortcuts (1–7 = tabs, F = fullscreen, G = cycle layout) ──────

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
    case 'g':
    case 'G': {
      // Layout döngüsü: 1x1 → 1x2 → 2x2 → 1x1
      const cycle: LayoutMode[] = ['1x1', '1x2', '2x2'];
      const current = multiChart.getLayout();
      const idx = cycle.indexOf(current);
      const next = cycle[(idx + 1) % cycle.length]!;
      multiChart.setLayout(next);
      break;
    }
    // 'F' and timeframe shortcuts are handled within ChartPanel
  }
});

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
console.info('PiyasaPilot v2.0 başlatıldı — çoklu pencere layout aktif');
