import type { Timeframe, DataUpdateEvent, PriceUpdateEvent, SymbolInfo } from './types.js';
import { dataEngine } from './core/DataEngine.js';
import { PortfolioEngine } from './core/PortfolioEngine.js';
import { MultiChartLayout, type LayoutMode } from './components/MultiChartLayout.js';
import { Sidebar } from './components/Sidebar.js';
import { PortfolioPanel } from './components/PortfolioPanel.js';
import { StrategyPanel } from './components/StrategyPanel.js';
import { Screener } from './components/Screener.js';
import { SignalFeed } from './components/SignalFeed.js';
import { EgitimlerPanel } from './components/EgitimlerPanel.js';
import { TR, formatAgo } from './constants/tr.js';

// ─── App shell elements ───────────────────────────────────────────────────────

const sidebarEl    = document.getElementById('sidebar')!;
const mainEl       = document.getElementById('main-content')!;
const statusBadge  = document.getElementById('status-badge')!;
const lastUpdateEl = document.getElementById('last-update')!;
const symbolTitle  = document.getElementById('symbol-title')!;
const tabBtns      = document.querySelectorAll<HTMLElement>('[data-tab]');
const topbarRight  = document.querySelector<HTMLElement>('.topbar-right')!;
const LS_START_TAB = 'piyasapilot_start_tab';
const LS_LAST_TAB  = 'piyasapilot_last_tab';
type AppTab = 'chart' | 'portfolio' | 'strategy' | 'screener' | 'signals' | 'education';
const TABS: AppTab[] = ['chart', 'portfolio', 'strategy', 'screener', 'signals', 'education'];

function isAppTab(value: string | null): value is AppTab {
  return !!value && TABS.includes(value as AppTab);
}

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

const startTabSelect = document.createElement('select');
startTabSelect.id = 'start-tab-select';
startTabSelect.className = 'start-tab-select';
startTabSelect.title = 'Açılış ekranı';
startTabSelect.innerHTML = `
  <option value="chart">Açılış: Grafik</option>
  <option value="portfolio">Açılış: Portföy</option>
  <option value="strategy">Açılış: Strateji</option>
  <option value="screener">Açılış: Tarayıcı</option>
  <option value="signals">Açılış: Sinyaller</option>
  <option value="education">Açılış: Eğitimler</option>
`;
topbarRight.prepend(startTabSelect);

// ─── Component instances ──────────────────────────────────────────────────────

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
  },
});
void educationPanel;
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

// ─── Tab routing ──────────────────────────────────────────────────────────────

function showTab(tab: string, persist = true): void {
  if (!isAppTab(tab)) tab = 'chart';
  tabBtns.forEach(btn => btn.classList.toggle('active', btn.dataset['tab'] === tab));
  chartEl.style.display     = tab === 'chart'     ? 'flex' : 'none';
  portfolioEl.style.display = tab === 'portfolio' ? 'flex' : 'none';
  strategyEl.style.display  = tab === 'strategy'  ? 'flex' : 'none';
  screenerEl.style.display  = tab === 'screener'  ? 'flex' : 'none';
  signalsEl.style.display   = tab === 'signals'   ? 'flex' : 'none';
  educationEl.style.display = tab === 'education' ? 'flex' : 'none';
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

startTabSelect.addEventListener('change', () => {
  const tab = startTabSelect.value;
  if (!isAppTab(tab)) return;
  localStorage.setItem(LS_START_TAB, tab);
  showTab(tab);
});

const savedStartTab = localStorage.getItem(LS_START_TAB);
const savedLastTab = localStorage.getItem(LS_LAST_TAB);
const initialTab: AppTab = isAppTab(savedStartTab)
  ? savedStartTab
  : isAppTab(savedLastTab)
    ? savedLastTab
    : 'chart';
startTabSelect.value = initialTab;
showTab(initialTab, false);

// ─── Keyboard shortcuts (1–6 = tabs, F = fullscreen, G = cycle layout) ──────

document.addEventListener('keydown', (e) => {
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLSelectElement) return;
  switch (e.key) {
    case '1': showTab('chart');     break;
    case '2': showTab('portfolio'); break;
    case '3': showTab('strategy');  break;
    case '4': showTab('screener');  break;
    case '5': showTab('signals');   break;
    case '6': showTab('education'); break;
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

// ─── Timeframe change from active ChartPanel ─────────────────────────────────

chartEl.addEventListener('timeframeChange', (e) => {
  const tf = (e as CustomEvent<Timeframe>).detail;
  multiChart.setActivePaneTimeframe(tf);
  // Ana DataEngine'i de güncelle (sidebar ticker'lar için)
  dataEngine.setTimeframe(tf);
});

// ─── Symbol selection from Sidebar ───────────────────────────────────────────

sidebar.onSymbolSelect(openSymbol);

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
