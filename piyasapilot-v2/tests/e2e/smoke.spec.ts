import { expect, test } from '@playwright/test';

const tabs = ['chart', 'portfolio', 'strategy', 'screener', 'signals'] as const;

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
