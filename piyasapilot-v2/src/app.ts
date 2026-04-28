import type { Timeframe, DataUpdateEvent, PriceUpdateEvent } from './types.js';
import { dataEngine } from './core/DataEngine.js';
import { PortfolioEngine } from './core/PortfolioEngine.js';
import { ChartPanel } from './components/ChartPanel.js';
import { Sidebar } from './components/Sidebar.js';
import { PortfolioPanel } from './components/PortfolioPanel.js';
import { StrategyPanel } from './components/StrategyPanel.js';
import { Screener } from './components/Screener.js';
import { TR, formatAgo } from './constants/tr.js';

// ─── App shell elements ───────────────────────────────────────────────────────

const sidebarEl    = document.getElementById('sidebar')!;
const mainEl       = document.getElementById('main-content')!;
const statusBadge  = document.getElementById('status-badge')!;
const lastUpdateEl = document.getElementById('last-update')!;
const symbolTitle  = document.getElementById('symbol-title')!;
const tabBtns      = document.querySelectorAll<HTMLElement>('[data-tab]');

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

// ─── Component instances ──────────────────────────────────────────────────────

const portfolioEngine = new PortfolioEngine();
const sidebar         = new Sidebar(sidebarEl);
const chartPanel      = new ChartPanel(chartEl);
const portfolioPanel  = new PortfolioPanel(portfolioEl, portfolioEngine);
const strategyPanel   = new StrategyPanel(strategyEl);
// Screener is self-contained; reference kept to prevent GC
const _screener = new Screener(screenerEl, () => dataEngine.getAllCached());
void _screener;

// ─── Tab routing ──────────────────────────────────────────────────────────────

function showTab(tab: string): void {
  tabBtns.forEach(btn => btn.classList.toggle('active', btn.dataset['tab'] === tab));
  chartEl.style.display     = tab === 'chart'     ? 'flex' : 'none';
  portfolioEl.style.display = tab === 'portfolio' ? 'flex' : 'none';
  strategyEl.style.display  = tab === 'strategy'  ? 'flex' : 'none';
  screenerEl.style.display  = tab === 'screener'  ? 'flex' : 'none';

  // Trigger backtest when strategy tab becomes visible
  if (tab === 'strategy' && dataEngine.getActiveCandles().length > 0) {
    strategyPanel.setCandles(
      dataEngine.getActiveCandles(),
      dataEngine.getActiveSymbol().symbol,
      dataEngine.getActiveTimeframe(),
    );
  }
}

tabBtns.forEach(btn => {
  btn.addEventListener('click', () => showTab(btn.dataset['tab']!));
});

// Default tab
showTab('chart');

// ─── Keyboard shortcuts (1–4 = tabs, F = fullscreen) ─────────────────────────

document.addEventListener('keydown', (e) => {
  if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
  switch (e.key) {
    case '1': showTab('chart');     break;
    case '2': showTab('portfolio'); break;
    case '3': showTab('strategy');  break;
    case '4': showTab('screener');  break;
    // 'F' and timeframe shortcuts are handled within ChartPanel
  }
});

// ─── Timeframe change from ChartPanel ─────────────────────────────────────────

chartEl.addEventListener('timeframeChange', (e) => {
  const tf = (e as CustomEvent<Timeframe>).detail;
  dataEngine.setTimeframe(tf);
});

// ─── Symbol selection from Sidebar ───────────────────────────────────────────

sidebar.onSymbolSelect(async (info) => {
  symbolTitle.textContent = `${info.name} (${info.symbol})`;
  sidebar.setActiveSymbol(info.symbol);
  // Sembol değişti — eski stratejinin marker'ları yeni mum grafiğinde
  // saçma duracak, yeni veri gelene kadar temizle.
  chartPanel.clearSignals();
  await dataEngine.setActiveSymbol(info);
});

// Strateji panelinin ürettiği BUY/SELL sinyallerini chart üstünde marker
// olarak çiz. Aktif tab strategy değil olsa bile pipeline bağlı kalır;
// kullanıcı chart sekmesindeyken de stratejinin işaretlerini görür.
strategyPanel.onSignalsUpdate(signals => chartPanel.setSignals(signals));

// ─── Data Engine events ───────────────────────────────────────────────────────

dataEngine.onDataUpdate((evt: DataUpdateEvent) => {
  if (evt.candles.length === 0) return;

  chartPanel.setData(evt.candles);

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
console.info('PiyasaPilot v2.0 başlatıldı');
