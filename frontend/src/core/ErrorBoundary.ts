export function installErrorBoundary(): void {
  const show = () => document.getElementById('app-error-banner')?.classList.remove('hidden');
  window.addEventListener('error', (event) => {
    console.error('Unhandled error:', event.error);
    show();
  });
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise:', event.reason);
    show();
  });
}
