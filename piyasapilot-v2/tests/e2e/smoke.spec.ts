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
