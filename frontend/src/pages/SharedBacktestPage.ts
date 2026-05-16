import { pageShell, escapeHtml } from './pageUtils.js';
import { analytics } from '../core/Analytics.js';

export async function renderSharedBacktestPage(container: HTMLElement): Promise<void> {
  const slug = window.location.pathname.split('/').pop() || '';
  container.innerHTML = pageShell('Paylaşılan Backtest', `
    <section class="public-state">
      <h1>Paylaşılan Backtest</h1>
      <p id="shared-status">Yükleniyor...</p>
      <div id="shared-actions" class="public-actions" hidden>
        <a class="btn btn-warning" href="/app">Terminale Git</a>
        <a class="btn btn-outline-warning" href="/pricing">Planları İncele</a>
      </div>
      <pre id="shared-data" class="shared-json"></pre>
    </section>`);
  const status = container.querySelector<HTMLElement>('#shared-status')!;
  const out = container.querySelector<HTMLElement>('#shared-data')!;
  const actions = container.querySelector<HTMLElement>('#shared-actions')!;
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
    analytics.track('shared_backtest_not_found', { slug });
    status.textContent = err instanceof Error
      ? 'Bu paylaşım bulunamadı veya süresi doldu.'
      : 'Paylaşım yüklenemedi.';
    actions.hidden = false;
    out.textContent = '';
  }
}
