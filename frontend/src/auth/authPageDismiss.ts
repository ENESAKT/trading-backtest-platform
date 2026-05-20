const AUTH_FALLBACK_PATH = '/landing';

function fallbackPath(): string {
  return AUTH_FALLBACK_PATH;
}

function canReturnToReferrer(): boolean {
  if (!document.referrer) return false;
  try {
    const referrer = new URL(document.referrer);
    return referrer.origin === window.location.origin && referrer.pathname !== window.location.pathname;
  } catch {
    return false;
  }
}

function dismissAuthPage(): void {
  if (canReturnToReferrer()) {
    window.history.back();
    return;
  }
  window.location.href = fallbackPath();
}

export function bindAuthPageDismiss(container: HTMLElement): void {
  const page = container.querySelector<HTMLElement>('.auth-page');
  const card = container.querySelector<HTMLElement>('.auth-card');
  if (!page || !card) return;

  page.addEventListener('click', (event) => {
    if (event.target === page) dismissAuthPage();
  });

  card.addEventListener('click', (event) => event.stopPropagation());

  const onKeyDown = (event: KeyboardEvent): void => {
    if (event.key === 'Escape') dismissAuthPage();
  };
  document.addEventListener('keydown', onKeyDown);
}
