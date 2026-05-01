import { expect, test, type Page } from '@playwright/test';

const tabs = ['chart', 'portfolio', 'strategy', 'screener', 'signals'] as const;
const day = 24 * 60 * 60;
const startTs = 1_714_521_600;

function makeCandles(base: number, step: number, count = 90) {
  return Array.from({ length: count }, (_, i) => {
    const drift = i * step;
    const open = base + drift;
    const close = open + (i % 2 === 0 ? step * 0.7 : -step * 0.45);
    const high = Math.max(open, close) + Math.abs(step) * 1.6;
    const low = Math.min(open, close) - Math.abs(step) * 1.4;
    return {
      time: startTs + i * day,
      open,
      high,
      low,
      close,
      volume: 120_000 + i * 1_000,
    };
  });
}

async function mockCandles(page: Page) {
  await page.route('**/api/v2/candles**', async (route) => {
    const url = new URL(route.request().url());
    const symbol = url.searchParams.get('symbol') ?? '';

    if (symbol === 'USDTRY=X') {
      await route.fulfill({ json: { status: 'ok', bars: [] } });
      return;
    }
    if (symbol === 'VIOP:USDTRY') {
      await route.fulfill({ status: 503, json: { status: 'error', message: 'E2E provider kapalı' } });
      return;
    }

    const bars = symbol === 'BTCUSDT'
      ? makeCandles(980, 5.5)
      : makeCandles(10, 0.08);
    await route.fulfill({ json: { status: 'ok', bars } });
  });
}

async function chartColorPixels(page: Page) {
  return page.evaluate(() => {
    const canvases = Array.from(document.querySelectorAll<HTMLCanvasElement>('.chart-pane-body canvas'));
    let count = 0;
    for (const canvas of canvases) {
      const ctx = canvas.getContext('2d');
      if (!ctx || canvas.width === 0 || canvas.height === 0) continue;
      const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
      for (let i = 0; i < data.length; i += 16) {
        const r = data[i] ?? 0;
        const g = data[i + 1] ?? 0;
        const b = data[i + 2] ?? 0;
        const a = data[i + 3] ?? 0;
        if (a > 0 && ((g > 120 && r < 120) || (r > 145 && g < 120) || (b > 145 && r < 150))) {
          count += 1;
        }
      }
    }
    return count;
  });
}

test('PiyasaPilot shell loads all primary tabs', async ({ page }) => {
  await page.goto('/');

  await expect(page.locator('.logo')).toHaveText('PiyasaPilot');
  await expect(page.locator('#status-badge')).toBeVisible();
  await expect(page.locator('#start-tab-select')).toBeVisible();

  for (const tab of tabs) {
    await page.locator(`[data-tab="${tab}"]`).click();
    await expect(page.locator(`#panel-${tab}`)).toBeVisible();
  }

  await expect(page.locator('#tg-status')).toBeVisible();
  await expect(page.locator('#tg-save-prefs')).toBeVisible();
});

test('start tab preference is persisted', async ({ page }) => {
  await page.goto('/');
  await page.locator('#start-tab-select').selectOption('signals');
  await page.reload();

  await expect(page.locator('#panel-signals')).toBeVisible();
  await expect(page.locator('#start-tab-select')).toHaveValue('signals');
});

test('mobile viewport keeps the primary shell usable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');

  await expect(page.locator('.logo')).toHaveText('PiyasaPilot');
  await expect(page.locator('#status-badge')).toBeVisible();
  await page.locator('[data-tab="signals"]').click();
  await expect(page.locator('#panel-signals')).toBeVisible();

  const fitsViewport = await page.evaluate(
    () => document.documentElement.scrollWidth <= window.innerWidth + 1,
  );
  expect(fitsViewport).toBeTruthy();
});

test('signal history survives reload from localStorage', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('piyasapilot_start_tab', 'signals');
    localStorage.setItem('piyasapilot_signal_history', JSON.stringify([
      {
        type: 'signal',
        symbol: 'BTCUSDT',
        signal_type: 'STRONG_BUY',
        price: 50000,
        strategy_id: '_consensus',
        reason: 'E2E kalıcılık sinyali',
        strength: 9,
        interval: '15m',
        ts: '2026-04-30T09:00:00Z',
        metadata: { consensus_ratio: 0.75, lgbm_prob: 0.73 },
      },
    ]));
  });

  await page.goto('/');
  await expect(page.locator('#panel-signals')).toBeVisible();
  await expect(page.locator('.signal-symbol')).toHaveText('BTCUSDT');
  await expect(page.locator('.signal-consensus')).toContainText('LGBM: 73%');

  await page.reload();
  await expect(page.locator('.signal-symbol')).toHaveText('BTCUSDT');
});

test('G1 keeps candles visible across low/high/low symbol price scale resets', async ({ page }) => {
  await mockCandles(page);
  await page.goto('/');

  const pane = page.locator('.chart-pane-body').first();
  await expect(pane).toHaveAttribute('data-chart-status', 'ready');

  await page.locator('.pane-symbol-select').first().selectOption('AKBNK.IS');
  await expect(pane).toHaveAttribute('data-chart-symbol', 'AKBNK.IS');
  await expect(pane).toHaveAttribute('data-chart-status', 'ready');
  const lowReset = Number(await pane.getAttribute('data-price-scale-reset-at'));
  await expect(pane).toHaveAttribute('data-last-price', /1[67]\./);
  await expect.poll(() => chartColorPixels(page)).toBeGreaterThan(250);

  await page.locator('.pane-symbol-select').first().selectOption('BTCUSDT');
  await expect(pane).toHaveAttribute('data-chart-symbol', 'BTCUSDT');
  await expect(pane).toHaveAttribute('data-chart-status', 'ready');
  const highReset = Number(await pane.getAttribute('data-price-scale-reset-at'));
  await expect(pane).toHaveAttribute('data-last-price', /14[0-9]{2}\./);
  expect(highReset).toBeGreaterThan(lowReset);
  await expect.poll(() => chartColorPixels(page)).toBeGreaterThan(250);

  await page.locator('.pane-symbol-select').first().selectOption('AKBNK.IS');
  await expect(pane).toHaveAttribute('data-chart-symbol', 'AKBNK.IS');
  await expect(pane).toHaveAttribute('data-chart-status', 'ready');
  const backReset = Number(await pane.getAttribute('data-price-scale-reset-at'));
  await expect(pane).toHaveAttribute('data-last-price', /1[67]\./);
  expect(backReset).toBeGreaterThan(highReset);
  await expect.poll(() => chartColorPixels(page)).toBeGreaterThan(250);
});

test('G1 clears stale candles and shows empty/error chart states', async ({ page }) => {
  await mockCandles(page);
  await page.goto('/');

  const pane = page.locator('.chart-pane-body').first();
  await expect(pane).toHaveAttribute('data-chart-status', 'ready');
  await expect.poll(() => chartColorPixels(page)).toBeGreaterThan(250);
  const readyPixels = await chartColorPixels(page);

  await page.locator('.pane-symbol-select').first().selectOption('USDTRY=X');
  await expect(pane).toHaveAttribute('data-chart-status', 'empty');
  await expect(page.locator('.chart-state-overlay').first()).toContainText('Veri yok');
  await expect(pane).toHaveAttribute('data-last-price', '');
  expect(await chartColorPixels(page)).toBeLessThan(readyPixels);

  await page.locator('.pane-symbol-select').first().selectOption('VIOP:USDTRY');
  await expect(pane).toHaveAttribute('data-chart-status', 'error');
  await expect(page.locator('.chart-state-overlay').first()).toContainText('Bağlantı hatası');
  await expect(page.locator('.chart-state-overlay').first()).toContainText('backend HTTP 503');
});
