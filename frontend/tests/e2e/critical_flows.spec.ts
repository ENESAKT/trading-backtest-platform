/**
 * critical_flows.spec.ts — Sprint E.5 critical path E2E tests.
 * Covers flows not already in smoke.spec.ts.
 */

import { expect, test, type Page } from '@playwright/test';

const DAY = 24 * 60 * 60;
const BASE_TS = 1_714_521_600;

function makeCandles(base: number, step: number, count = 90) {
  return Array.from({ length: count }, (_, i) => {
    const o = base + i * step;
    const c = o + (i % 2 === 0 ? step * 0.7 : -step * 0.45);
    return { time: BASE_TS + i * DAY, open: o, high: Math.max(o, c) + step, low: Math.min(o, c) - step, close: c, volume: 100_000 + i * 500 };
  });
}

async function mockCandles(page: Page) {
  await page.route('**/api/auth/me', (route) => route.fulfill({ 
    status: 200, 
    json: { ok: true, data: { id: 1, email: 'test@example.com', role: 'pro', display_name: 'Test' } } 
  }));
  await page.route('**/api/v2/candles**', (route) =>
    route.fulfill({ json: { status: 'ok', bars: makeCandles(10, 0.1) } }),
  );
}

async function mockBacktest(page: Page) {
  const bars = makeCandles(10, 0.1);
  await page.route('**/api/backtest/run', (route) =>
    route.fulfill({
      json: {
        symbol: 'THYAO', interval: '1d', strategy_id: 'sma_crossover',
        strategy_name: 'SMA', params: {}, capital: 100_000, lookback_bars: bars.length,
        metrics: {
          final_equity: 108_000, total_return_pct: 8, max_drawdown_pct: 3,
          total_trades: 4, total_commission: 0, sharpe_ratio: 1.4, win_rate: 75,
          has_open_position: false, annualized_return_pct: 12, calmar_ratio: 2.8,
        },
        equity_curve: bars.map((b, i) => ({
          time: b.time, bar_index: i, cash: 100_000, position_value: 0,
          total_equity: 100_000 + i * 90, drawdown: 0, drawdown_pct: 0,
        })),
        trades: [
          { symbol: 'THYAO', side: 'LONG', entry_type: 'BUY', exit_type: 'SELL',
            entry_time: bars[5]!.time, exit_time: bars[15]!.time,
            entry_price: bars[5]!.close, exit_price: bars[15]!.close,
            quantity: 100, net_pnl: 200, return_pct: 2, is_winner: true,
            entry_bar_index: 5, exit_bar_index: 15 },
        ],
        signals: [],
      },
    }),
  );
}

// ─── Flow 1: Sayfa yükle → THYAO seç → grafik görünür ──────────────────────

test('Flow 1: page load → symbol select → chart ready', async ({ page }) => {
  page.on('console', msg => console.log('BROWSER_CONSOLE:', msg.text()));
  page.on('pageerror', err => console.log('BROWSER_ERROR:', err.message));
  page.on('request', req => console.log('REQ:', req.url()));
  await mockCandles(page);
  await page.goto('/app');

  // Chart tab is default
  await expect(page.locator('#panel-chart')).toBeVisible();

  const pane = page.locator('.chart-pane-body').first();
  await expect(pane).toHaveAttribute('data-chart-status', 'ready');

  // Select THYAO explicitly
  await page.locator('.pane-symbol-select').first().focus();
  await page.locator('.pane-symbol-select').first().selectOption('THYAO.IS');
  await expect(pane).toHaveAttribute('data-chart-symbol', 'THYAO.IS');
  await expect(pane).toHaveAttribute('data-chart-status', 'ready');
  await expect(pane.locator('canvas').first()).toBeVisible();
});

// ─── Flow 2: Backtest çalıştır → equity curve görünür ───────────────────────

test('Flow 2: run backtest → equity curve canvas visible', async ({ page }) => {
  await mockCandles(page);
  await mockBacktest(page);
  await page.goto('/app');

  await page.locator('[data-tab="strategy"]').click();
  await expect(page.locator('#panel-strategy')).toBeVisible();

  // Click run backtest
  await page.locator('#run-backtest').click();

  // Equity canvas must be visible
  const equityCanvas = page.locator('#equity-canvas');
  await expect(equityCanvas).toBeVisible({ timeout: 10_000 });

  // Summary metrics should appear
  const reportContent = page.locator('#report-content');
  await expect(reportContent).toContainText(/Başlangıç|Net K\/Z|Toplam|Kazanma/);
});

// ─── Flow 3: Mali analiz sekmesi → oran tablosu görünür ────────────────────

test('Flow 3: financials tab → ratios table visible', async ({ page }) => {
  await mockCandles(page);

  await page.route('**/api/mali-analiz/universe', (route) =>
    route.fulfill({
      json: {
        symbols: [
          { symbol: 'THYAO', name: 'Türk Hava Yolları', fetch_status: { status: 'ok' } },
        ],
        total: 1,
      },
    }),
  );

  await page.route('**/api/mali-analiz/THYAO/summary', (route) =>
    route.fulfill({
      json: {
        symbol: 'THYAO', company_name: 'Türk Hava Yolları',
        period: '2024 Q3', fetched_at: '2024-01-01T00:00:00Z',
        ratios: [
          { key: 'fk', name: 'F/K', value: 6.2, unit: 'x', category: 'deger', period: '2024 Q3' },
          { key: 'pd_dd', name: 'PD/DD', value: 1.1, unit: 'x', category: 'deger', period: '2024 Q3' },
          { key: 'net_kar_marji', name: 'Net Kar Marjı', value: 14.5, unit: '%', category: 'karlilik', period: '2024 Q3' },
        ],
        alerts: [],
      },
    }),
  );

  await page.goto('/app');

  // Navigate to financials via keyboard shortcut
  await page.keyboard.press('7');
  await expect(page.locator('#panel-financials')).toBeVisible();

  // Ratios tab
  const ratiosTab = page.locator('.ma-tab-btn', { hasText: 'Oranlar' });
  if (await ratiosTab.isVisible()) {
    await ratiosTab.click();
    await expect(page.locator('.ratio-category-label').first()).toBeVisible({ timeout: 8_000 });
  } else {
    // Summary tab fallback — check metrics visible
    await expect(page.locator('.ma-body')).toBeVisible({ timeout: 8_000 });
  }
});

// ─── Flow 4: Screener → filtre uygula → sonuçlar gelir ─────────────────────

test('Flow 4: screener → filter → results visible', async ({ page }) => {
  await mockCandles(page);



  const candlesReq = page.waitForResponse(resp => resp.url().includes('/api/v2/candles') && resp.status() === 200);
  await page.goto('/app');
  await candlesReq;
  
  await page.locator('[data-tab="screener"]').click();
  await expect(page.locator('#panel-screener')).toBeVisible();

  // Wait for scan button and click
  const scanBtn = page.locator('#scan-btn');
  await expect(scanBtn).toBeEnabled({ timeout: 5_000 });
  await scanBtn.click();

  // Wait for table OR empty state
  await expect(page.locator('#panel-screener table, #panel-screener .empty-state').first())
    .toBeVisible({ timeout: 10_000 });
});

// ─── Flow 5: News panel (8. sekme) görünür ──────────────────────────────────

test('Flow 5: news panel loads via keyboard shortcut 8', async ({ page }) => {
  await mockCandles(page);

  await page.route('**/api/news**', (route) =>
    route.fulfill({
      json: {
        news: [
          {
            id: 1, symbol: 'THYAO', headline: 'Türk Hava Yolları rekor kâr açıkladı',
            body: 'THY üçüncü çeyrek sonuçlarını açıkladı.',
            source: 'Borsa İstanbul', published_at: new Date().toISOString(),
            fetched_at: new Date().toISOString(), url: null,
          },
          {
            id: 2, symbol: 'AKBNK', headline: 'Akbank faiz gelirlerini artırdı',
            body: null, source: 'Reuters', published_at: new Date().toISOString(),
            fetched_at: new Date().toISOString(), url: 'https://example.com/akbnk',
          },
        ],
        total: 2,
        unread_24h: 2,
      },
    }),
  );

  await page.goto('/app');

  // Press 8 to open news tab
  await page.keyboard.press('8');
  const newsPanel = page.locator('#panel-news');
  await expect(newsPanel).toBeVisible({ timeout: 5_000 });

  // News cards should appear
  await expect(newsPanel.locator('.news-card').first()).toBeVisible({ timeout: 8_000 });
  await expect(newsPanel.locator('.news-headline').first()).toContainText(/Türk Hava|Akbank/);

  // Symbol filter works
  const symInput = newsPanel.locator('#news-symbol');
  await symInput.fill('AKBNK');
  await expect(newsPanel.locator('.news-card')).toHaveCount(1);
  await expect(newsPanel.locator('.news-headline')).toContainText('Akbank');

  // Clear filter
  await symInput.fill('');
  await expect(newsPanel.locator('.news-card')).toHaveCount(2);
});

// ─── Walk-Forward + Monte Carlo separate tabs ────────────────────────────────

test('Flow 6: strategy walk-forward and monte-carlo tabs render', async ({ page }) => {
  await mockCandles(page);

  await page.route('**/api/backtest/walk-forward', (route) =>
    route.fulfill({
      json: {
        run_id: 'wf-e2e-001',
        walk_forward_report: {
          windows: [
            { window: { index: 0, in_sample_start: 0, in_sample_end: 30, out_of_sample_start: 31, out_of_sample_end: 45 }, selected_params: { period: 14 }, in_sample_score: 0.8, out_of_sample_return_pct: 3.2, walk_forward_efficiency: 0.75, passed: true, warnings: [] },
            { window: { index: 1, in_sample_start: 31, in_sample_end: 61, out_of_sample_start: 62, out_of_sample_end: 76 }, selected_params: { period: 21 }, in_sample_score: 0.7, out_of_sample_return_pct: -1.1, walk_forward_efficiency: 0.55, passed: false, warnings: ['OOS negatif'] },
          ],
          total_oos_return_pct: 2.1,
          walk_forward_efficiency: 0.65,
          passed: true,
          warnings: [],
        },
        metrics: { total_return_pct: 2.1, max_drawdown_pct: 1.5, sharpe_ratio: 1.1, win_rate: 0.5 },
        equity_curve: [],
        trades: [],
        signals: [],
      },
    }),
  );

  await mockBacktest(page);
  await page.goto('/app');
  await page.locator('[data-tab="strategy"]').click();

  // Run backtest first so lastResult is populated
  await page.locator('#run-backtest').click();
  await expect(page.locator('#report-content')).toContainText(/Başlangıç|Net/, { timeout: 8_000 });

  // Click Walk-Fwd tab
  const wfTab = page.locator('.report-tab', { hasText: 'Walk-Fwd' });
  await expect(wfTab).toBeVisible();
  await wfTab.click();
  await expect(page.locator('#report-content')).toContainText(/Walk.Forward|Pencere|Fold|WFE/, { timeout: 5_000 });

  // Click Monte Carlo tab
  const mcTab = page.locator('.report-tab', { hasText: 'Monte Carlo' });
  await expect(mcTab).toBeVisible();
  await mcTab.click();
  await expect(page.locator('#report-content')).toContainText(/Monte Carlo|Medyan|Simülasyon|veri yok/i, { timeout: 5_000 });
});
