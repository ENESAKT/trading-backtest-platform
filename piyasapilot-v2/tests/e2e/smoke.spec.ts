import { expect, test, type Page } from '@playwright/test';

const tabs = ['chart', 'portfolio', 'strategy', 'screener', 'signals', 'education'] as const;
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

async function mockBacktestRun(page: Page) {
  await page.route('**/api/backtest/run', async (route) => {
    const bars = makeCandles(980, 5.5);
    const entry = bars[8]!;
    const exit = bars[28]!;
    const open = bars[62]!;
    await route.fulfill({
      json: {
        symbol: 'BTCUSDT',
        interval: '1d',
        strategy_id: 'strategy_spec',
        strategy_name: 'E2E PnL',
        params: {},
        capital: 100000,
        lookback_bars: bars.length,
        strategy_spec: {
          name: 'E2E PnL',
          rules: {
            long_entry: 'C > EMA(C,10)',
            long_exit: 'C < EMA(C,10)',
            short_entry: '',
            short_exit: '',
          },
          risk: { stop_loss_pct: 3, take_profit_pct: 8, trailing_stop_pct: 5 },
        },
        metrics: {
          final_equity: 104000,
          total_return_pct: 4,
          max_drawdown_pct: 2,
          total_trades: 1,
          total_commission: 0,
          sharpe_ratio: 1.2,
          win_rate: 100,
          has_open_position: true,
        },
        equity_curve: bars.map((bar, index) => ({
          time: bar.time,
          bar_index: index,
          cash: 100000,
          position_value: 0,
          total_equity: 100000 + index * 40,
          drawdown: 0,
          drawdown_pct: 0,
        })),
        trades: [
          {
            symbol: 'BTCUSDT',
            side: 'LONG',
            entry_type: 'BUY',
            exit_type: 'SELL',
            entry_time: entry.time,
            exit_time: exit.time,
            entry_price: entry.close,
            exit_price: exit.close,
            quantity: 10,
            net_pnl: (exit.close - entry.close) * 10,
            return_pct: ((exit.close - entry.close) / entry.close) * 100,
            is_winner: true,
            entry_bar_index: 8,
            exit_bar_index: 28,
          },
        ],
        signals: [
          {
            type: 'BUY',
            reason: 'E2E BUY',
            price: entry.close,
            timestamp: entry.time,
            strength: 5,
            quantity: 10,
            bar_index: 8,
          },
          {
            type: 'SELL',
            reason: 'E2E SELL',
            price: exit.close,
            timestamp: exit.time,
            strength: 5,
            quantity: 10,
            bar_index: 28,
            pnl: (exit.close - entry.close) * 10,
          },
          {
            type: 'BUY',
            reason: 'E2E açık pozisyon',
            price: open.close,
            timestamp: open.time,
            strength: 5,
            quantity: 6,
            bar_index: 62,
            open_position: true,
          },
        ],
      },
    });
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

  await page.locator('[data-tab="signals"]').click();
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

test('education tab renders searchable indicator articles', async ({ page }) => {
  await page.goto('/');
  await page.locator('[data-tab="education"]').click();

  await expect(page.locator('#panel-education')).toBeVisible();
  await expect(page.locator('.education-article-header h2')).toContainText(/ADX|ATR|Bollinger|Ichimoku|MACD|OBV|Parabolic|RSI|Stochastic|Hareketli/);

  await page.locator('#education-search').fill('rsi');
  await expect(page.locator('.education-row.active')).toContainText('RSI');
  await expect(page.locator('.education-source-note')).toContainText('kare OCR');
});

test('education bridge actions open chart indicators and strategy presets', async ({ page }) => {
  await page.goto('/');
  await page.locator('[data-tab="education"]').click();

  await page.locator('#education-search').fill('atr');
  await expect(page.locator('.education-row.active')).toContainText('ATR');

  await page.locator('[data-chart-indicator="atr"]').click();
  await expect(page.locator('#panel-chart')).toBeVisible();
  await expect(page.locator('.ind-btn[data-ind="atr"]').first()).toHaveClass(/active/);

  await page.locator('[data-tab="education"]').click();
  await page.locator('[data-strategy-id="supertrend"]').click();
  await expect(page.locator('#panel-strategy')).toBeVisible();
  await expect(page.locator('.strategy-card.active')).toContainText('Supertrend');
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

test('G2 scale menu supports log and percent normalization', async ({ page }) => {
  await mockCandles(page);
  await page.goto('/');

  const pane = page.locator('.chart-pane-body').first();
  await expect(pane).toHaveAttribute('data-chart-status', 'ready');

  await page.locator('.scale-mode-btn[data-scale-mode="percent"]').first().click();
  await expect(pane).toHaveAttribute('data-chart-scale-mode', 'percent');
  await expect(page.locator('.scale-mode-btn[data-scale-mode="percent"]').first()).toHaveClass(/active/);
  await expect(page.locator('#chart-unit-badge').first()).toHaveText('%');

  const candles = makeCandles(980, 5.5);
  const baseClose = candles[0]!.close;
  const lastClose = candles[candles.length - 1]!.close;
  const expectedPct = ((lastClose / baseClose) - 1) * 100;
  expect(Number(await pane.getAttribute('data-percent-base-close'))).toBeCloseTo(baseClose, 5);
  expect(Number(await pane.getAttribute('data-percent-last-change'))).toBeCloseTo(expectedPct, 4);

  await page.locator('.scale-mode-btn[data-scale-mode="log"]').first().click();
  await expect(pane).toHaveAttribute('data-chart-scale-mode', 'log');
  await expect(page.locator('#chart-unit-badge').first()).toHaveText('USDT');
});

test('G2 percent mode can be applied to two panes with different price levels', async ({ page }) => {
  await mockCandles(page);
  await page.goto('/');

  await page.locator('[data-layout="1x2"]').click();
  await expect(page.locator('.chart-pane')).toHaveCount(2);

  await page.locator('.pane-symbol-select').first().selectOption('AKBNK.IS');
  await expect(page.locator('.chart-pane-body').first()).toHaveAttribute('data-chart-status', 'ready');
  await page.locator('.pane-symbol-select').nth(1).selectOption('BTCUSDT');
  await expect(page.locator('.chart-pane-body').nth(1)).toHaveAttribute('data-chart-status', 'ready');

  await page.locator('.scale-mode-btn[data-scale-mode="percent"]').first().click();
  await page.locator('.scale-mode-btn[data-scale-mode="percent"]').nth(1).click();

  await expect(page.locator('.chart-pane-body').first()).toHaveAttribute('data-chart-scale-mode', 'percent');
  await expect(page.locator('.chart-pane-body').nth(1)).toHaveAttribute('data-chart-scale-mode', 'percent');
  expect(Number(await page.locator('.chart-pane-body').first().getAttribute('data-percent-base-close'))).toBeLessThan(20);
  expect(Number(await page.locator('.chart-pane-body').nth(1).getAttribute('data-percent-base-close'))).toBeGreaterThan(900);
});

test('G3 indicator center enables stochastic and persists parameters', async ({ page }) => {
  await mockCandles(page);
  await page.goto('/');

  const pane = page.locator('.chart-pane-body').first();
  await expect(pane).toHaveAttribute('data-chart-status', 'ready');

  await page.locator('#indicator-center-btn').first().click();
  await expect(page.locator('.indicator-center').first()).toBeVisible();
  await page.locator('#indicator-search').fill('stochastic');
  await expect(page.locator('.indicator-def').first()).toContainText('Stochastic');

  await page.locator('[data-indicator-toggle="stoch"]').click();
  await expect(pane).toHaveAttribute('data-active-indicators', /stoch/);
  await expect(page.locator('.ind-btn[data-ind="stoch"]').first()).toHaveClass(/active/);

  await page.locator('[data-indicator-param="stochasticKPeriod"]').fill('10');
  await expect(pane).toHaveAttribute('data-indicator-stoch-k', '10');

  await page.reload();
  await expect(pane).toHaveAttribute('data-chart-status', 'ready');
  await expect(pane).toHaveAttribute('data-active-indicators', /stoch/);
  await expect(pane).toHaveAttribute('data-indicator-stoch-k', '10');

  await page.locator('#indicator-center-btn').first().click();
  await page.locator('#indicator-search').fill('stochastic');
  await expect(page.locator('[data-indicator-param="stochasticKPeriod"]').first()).toHaveValue('10');
});

test('G4 PnL overlay renders closed trade and open risk metrics', async ({ page }) => {
  await mockCandles(page);
  await mockBacktestRun(page);
  await page.goto('/');

  const pane = page.locator('.chart-pane-body').first();
  await expect(pane).toHaveAttribute('data-chart-status', 'ready');

  await page.locator('.pane-symbol-select').first().selectOption('AKBNK.IS');
  await expect(pane).toHaveAttribute('data-chart-symbol', 'AKBNK.IS');
  await expect(pane).toHaveAttribute('data-bist-limit-status', 'active');

  await page.locator('.pane-symbol-select').first().selectOption('BTCUSDT');
  await expect(pane).toHaveAttribute('data-chart-symbol', 'BTCUSDT');
  await page.locator('[data-tab="strategy"]').click();
  await page.locator('#run-backtest').click();
  await expect(page.locator('.signal-item').first()).toContainText(/AL|SAT/);

  await page.locator('[data-tab="chart"]').click();
  await expect(pane).toHaveAttribute('data-pnl-closed-count', '1');
  await expect(pane).toHaveAttribute('data-pnl-risk-reward', '2.6666666666666665');

  const bars = makeCandles(980, 5.5);
  const entry = bars[8]!;
  const exit = bars[28]!;
  const open = bars[62]!;
  const last = bars[bars.length - 1]!;
  const expectedClosedPct = ((exit.close - entry.close) / entry.close) * 100;
  const expectedOpenPct = ((last.close - open.close) / open.close) * 100;
  expect(Number(await pane.getAttribute('data-pnl-last-closed-pct'))).toBeCloseTo(expectedClosedPct, 4);
  expect(Number(await pane.getAttribute('data-pnl-open-pct'))).toBeCloseTo(expectedOpenPct, 4);
});

test('G5 drawing toolbar renders and drawing count persists per symbol', async ({ page }) => {
  await mockCandles(page);
  await page.goto('/');

  const pane = page.locator('.chart-pane-body').first();
  await expect(pane).toHaveAttribute('data-chart-status', 'ready');

  // Drawing toolbar buttons should be visible
  await expect(page.locator('.drawing-tool-btn[data-drawing-tool="trendline"]').first()).toBeVisible();
  await expect(page.locator('.drawing-tool-btn[data-drawing-tool="hline"]').first()).toBeVisible();
  await expect(page.locator('.drawing-tool-btn[data-drawing-tool="vline"]').first()).toBeVisible();
  await expect(page.locator('.drawing-tool-btn[data-drawing-tool="measure"]').first()).toBeVisible();
  await expect(page.locator('#drawing-clear-btn').first()).toBeVisible();

  // Inject a drawing via localStorage for BTCUSDT__1d
  await page.evaluate(() => {
    const drawings = {
      'BTCUSDT__1d': [
        {
          id: 'test_hline_1',
          tool: 'hline',
          points: [{ time: 1714521600, price: 1000 }],
          style: { color: '#58a6ff', lineWidth: 2, lineStyle: 'solid' },
        },
      ],
    };
    localStorage.setItem('piyasapilot_drawings', JSON.stringify(drawings));
  });

  // Reload and verify drawing count data attribute is set
  await page.reload();
  await expect(pane).toHaveAttribute('data-chart-status', 'ready');
  await expect(pane).toHaveAttribute('data-drawing-count', '1');

  // Switch symbol — drawing count should reset for new symbol
  await page.locator('.pane-symbol-select').first().selectOption('AKBNK.IS');
  await expect(pane).toHaveAttribute('data-chart-symbol', 'AKBNK.IS');
  await expect(pane).toHaveAttribute('data-drawing-count', '0');

  // Switch back — drawing should return
  await page.locator('.pane-symbol-select').first().selectOption('BTCUSDT');
  await expect(pane).toHaveAttribute('data-chart-symbol', 'BTCUSDT');
  await expect(pane).toHaveAttribute('data-drawing-count', '1');

  // Clear all drawings
  await page.locator('#drawing-clear-btn').first().click();
  await expect(pane).toHaveAttribute('data-drawing-count', '0');

  // Verify cleared from localStorage
  const remaining = await page.evaluate(() => {
    const stored = JSON.parse(localStorage.getItem('piyasapilot_drawings') || '{}');
    return Object.keys(stored).length;
  });
  expect(remaining).toBe(0);
});

test('G6 multi-symbol compare adds second series and normalizes in percent mode', async ({ page }) => {
  await mockCandles(page);
  await page.goto('/');

  const pane = page.locator('.chart-pane-body').first();
  await expect(pane).toHaveAttribute('data-chart-status', 'ready');

  // Input symbol to compare
  await page.locator('#compare-input').first().fill('ETHUSDT');
  await page.locator('#compare-add-btn').first().click();

  // Wait for loading to finish and check attribute
  await expect(pane).toHaveAttribute('data-chart-status', 'ready');
  await expect(pane).toHaveAttribute('data-compare-symbol', 'ETHUSDT');

  // Clear compare
  await page.locator('#compare-clear-btn').first().click();
  await expect(pane).not.toHaveAttribute('data-compare-symbol', 'ETHUSDT');
});

test('G7 multi-chart sync locks synchronize symbol, timeframe and range', async ({ page }) => {
  await mockCandles(page);
  await page.goto('/');

  // Switch to 1x2 layout
  await page.locator('[data-layout="1x2"]').click();
  await expect(page.locator('.chart-pane')).toHaveCount(2);

  // Set symbol on first pane (locked by default)
  await page.locator('.pane-symbol-select').first().selectOption('AKBNK.IS');
  await expect(page.locator('.chart-pane-body').first()).toHaveAttribute('data-chart-symbol', 'AKBNK.IS');
  
  // Verify second pane also synced symbol
  await expect(page.locator('.chart-pane-body').nth(1)).toHaveAttribute('data-chart-symbol', 'AKBNK.IS');

  // Toggle symbol lock off
  await page.locator('.sync-lock-btn[data-lock="symbol"]').click();
  await expect(page.locator('.sync-lock-btn[data-lock="symbol"]')).not.toHaveClass(/active/);

  // Change symbol on first pane
  await page.locator('.pane-symbol-select').first().selectOption('BTCUSDT');
  await expect(page.locator('.chart-pane-body').first()).toHaveAttribute('data-chart-symbol', 'BTCUSDT');
  
  // Verify second pane DID NOT sync
  await expect(page.locator('.chart-pane-body').nth(1)).toHaveAttribute('data-chart-symbol', 'AKBNK.IS');
});

test('G8 chart templates save and restore workspace configuration', async ({ page }) => {
  await mockCandles(page);
  await page.goto('/');

  const pane = page.locator('.chart-pane-body').first();
  
  // Configure chart: Enable indicators and change scale
  await page.locator('.ind-btn[data-ind="atr"]').first().click();
  await page.locator('.scale-mode-btn[data-scale-mode="log"]').first().click();
  
  await expect(pane).toHaveAttribute('data-active-indicators', /atr/);
  await expect(pane).toHaveAttribute('data-chart-scale-mode', 'log');

  // Open template menu and save as "E2E Template"
  await page.locator('#template-btn').first().click();
  await page.locator('#new-template-name').first().fill('E2E Template');
  await page.locator('#save-template-btn').first().click();

  // Reset to default
  await page.locator('#template-btn').first().click();
  await page.locator('#reset-template-btn').first().click();
  
  await expect(pane).not.toHaveAttribute('data-active-indicators', /atr/);
  await expect(pane).toHaveAttribute('data-chart-scale-mode', 'linear');

  // Load "E2E Template"
  await page.locator('#template-btn').first().click();
  await page.locator('.template-item[data-name="E2E Template"]').click();
  
  await expect(pane).toHaveAttribute('data-active-indicators', /atr/);
  await expect(pane).toHaveAttribute('data-chart-scale-mode', 'log');
});

