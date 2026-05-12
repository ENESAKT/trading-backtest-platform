---
name: browser-qa-tester
description: Conducts deep, pixel-perfect UI/UX testing using the browser subagent, checking for dead links, missing data, visual glitches, and rendering errors.
---

# Browser QA Tester Workflow

This skill defines the workflow for performing deep, comprehensive Quality Assurance (QA) and UI/UX testing using the `browser_subagent` tool.

## Objective
To rigorously test web interfaces by clicking every interactive element, testing edge cases, and verifying state synchronization across different components.

## Trigger
Use this skill whenever the user requests a UI check, visual inspection, or "deep test" of the frontend interface.

## Workflow Instructions

1. **Initialization:**
   - Verify that the target web application (e.g., `http://localhost:5173`) is running.
   - Prepare the `browser_subagent` tool.

2. **Subagent Task Definition (Prompt):**
   When invoking the `browser_subagent`, you MUST use a highly detailed, specific task description. Copy or adapt the following prompt for the subagent:

   > **Task:** Go to the target URL (e.g., 'http://localhost:5173') and perform a deep, pixel-perfect QA (Quality Assurance) test. Leave no unclicked pixels. Follow these specific steps:
   > 
   > 1. **Dashboard & Global Navigation:** Click all sidebar menus, top navbar icons, notification bells, and profile/settings areas. Check for broken links or unresponsive elements. Test any pagination or sorting on tables.
   > 2. **Symbol/Asset Selection:** Search and switch between multiple assets from different markets (e.g., BIST100: GARAN, THYAO; Crypto: BTCUSDT, ETHUSDT). **Crucial:** Verify if the titles, charts, and tables *actually* update to the new symbol or if they get stuck on the previous state (state synchronization).
   > 3. **Charting Component:** Click through all timeframes (1m, 5m, 1h, 1D). Verify if the chart loads or hangs on a black screen. Open the indicators menu and add at least 3 indicators (RSI, MACD, etc.). Use drawing tools (Trendline, Fibonacci) to see if they render properly.
   > 4. **Financial Analysis (Mali Analiz):** Navigate through all sub-tabs (Balance Sheet, Income Statement, Cash Flow). Check for stuck error messages (e.g., "Data Fetch Error" persisting even when data loads). Look for duplicate rows (e.g., "Other Receivables" printing twice). Find cells with NaN or massive negative unexpected values.
   > 5. **Theme & Settings:** Toggle the Dark/Light mode multiple times. Look for contrast issues (white text on a white background).
   > 6. **Error Hunting:** Though you cannot see the console log directly via visual tools, pay attention to UI error toasts, "Object Object" renders, or unresponsive "Run Strategy" buttons (check for bad DOM positioning making them unclickable).
   > 
   > **Output Requirement:** Return a highly detailed markdown report mapping every clicked element and its exact result/error.

3. **Report Generation:**
   - Wait for the subagent to finish and return its detailed findings.
   - Aggregate the findings into a clear, prioritized Markdown report (e.g., `YAPILACAKLAR.md`).
   - Group findings by: Critical Bugs (State sync, crashes), Non-functional Buttons, Rendering Issues (Duplicates, Contrast), and Missing Feedback (No loading states).

4. **Tracking:**
   - Always log the key lessons learned into `ogrenilenler.md` (or equivalent tracking file) under the appropriate UI/Frontend section.
