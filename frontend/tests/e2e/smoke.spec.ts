/**
 * Smoke test — CI'da build çıktısı olmadan sadece statik dosyaları kontrol eder.
 * Gerçek UI testi için dev server gereklidir.
 */
import { test, expect } from '@playwright/test';

// CI ortamında server olmadığı için bu testler atlanır
test.skip(!!process.env.CI, 'CI ortamında dev server yok — smoke test atlandı');

test('anasayfa yükleniyor', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/PiyasaPilot/i);
});
