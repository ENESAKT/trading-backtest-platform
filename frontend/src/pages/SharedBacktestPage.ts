import { pageShell, escapeHtml } from './pageUtils.js';

export async function renderSharedBacktestPage(container: HTMLElement): Promise<void> {
  const slug = window.location.pathname.split('/').pop() || '';
  container.innerHTML = pageShell('Paylaşılan Backtest', `
    <section class="public-state">
      <h1>Paylaşılan Backtest</h1>
      <p id="shared-status">Yükleniyor...</p>
      <pre id="shared-data" class="shared-json"></pre>
    </section>`);
  const status = container.querySelector<HTMLElement>('#shared-status')!;
  const out = container.querySelector<HTMLElement>('#shared-data')!;
  try {
    const shareRes = await fetch(`/api/shared/${encodeURIComponent(slug)}`);
    const shareBody = await shareRes.json();
    const runId = shareBody.data?.run_id;
    if (!shareRes.ok || !runId) throw new Error('Paylaşım bulunamadı.');
    const reportRes = await fetch(`/api/backtest/reports/${encodeURIComponent(runId)}`);
    const report = await reportRes.json();
    status.textContent = `Run ID: ${runId}`;
    out.textContent = escapeHtml(JSON.stringify(report, null, 2));
  } catch (err) {
    status.textContent = err instanceof Error ? err.message : 'Paylaşım yüklenemedi.';
  }
}
