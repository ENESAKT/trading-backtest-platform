type OAuthProvider = {
  id: string;
  label: string;
  url: string;
};

const PROVIDER_ICONS: Record<string, string> = {
  google: `
    <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#4285F4" d="M44.5 20H24v8.5h11.7C34.3 33.9 29.7 37 24 37c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.1 0 5.9 1.1 8.1 2.9l6-6C34.6 5.1 29.6 3 24 3 12.4 3 3 12.4 3 24s9.4 21 21 21c10.9 0 20-8 20-21 0-1.4-.1-2.7-.5-4z"/>
    </svg>`,
  github: `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 .5A11.5 11.5 0 0 0 8.36 22.9c.58.11.79-.25.79-.56v-2.02c-3.22.7-3.9-1.39-3.9-1.39-.53-1.34-1.29-1.7-1.29-1.7-1.05-.72.08-.71.08-.71 1.17.08 1.78 1.2 1.78 1.2 1.03 1.77 2.71 1.26 3.37.96.1-.75.4-1.26.73-1.55-2.57-.29-5.28-1.29-5.28-5.73 0-1.27.45-2.3 1.2-3.11-.12-.29-.52-1.47.11-3.07 0 0 .98-.31 3.18 1.19A11.08 11.08 0 0 1 12 6.02c.98 0 1.96.13 2.88.39 2.2-1.5 3.17-1.19 3.17-1.19.64 1.6.24 2.78.12 3.07.75.81 1.2 1.84 1.2 3.11 0 4.45-2.71 5.43-5.29 5.72.42.36.79 1.08.79 2.18v3.04c0 .31.21.68.8.56A11.5 11.5 0 0 0 12 .5Z"/>
    </svg>`,
};

function providerAction(provider: OAuthProvider, mode: 'login' | 'register'): string {
  if (provider.id === 'google') return mode === 'login' ? 'Google ile Devam Et' : 'Google ile Kayıt Ol';
  if (provider.id === 'github') return mode === 'login' ? 'GitHub ile Devam Et' : 'GitHub ile Kayıt Ol';
  return `${provider.label} ile Devam Et`;
}

export async function renderOAuthButtons(container: HTMLElement, mode: 'login' | 'register'): Promise<void> {
  const root = container.querySelector<HTMLElement>('[data-oauth-buttons]');
  if (!root) return;

  try {
    const res = await fetch('/api/auth/oauth/providers', { credentials: 'include' });
    if (!res.ok) throw new Error('oauth providers unavailable');
    const payload = await res.json();
    const providers = (payload?.data?.providers ?? []) as OAuthProvider[];
    if (providers.length === 0) {
      root.innerHTML = '';
      root.classList.add('d-none');
      return;
    }

    root.classList.remove('d-none');
    root.innerHTML = `
      <div class="text-center text-muted small mb-3">--- veya ---</div>
      ${providers.map((provider) => `
        <a
          href="${provider.url}"
          class="btn btn-outline-secondary w-100 d-flex align-items-center justify-content-center gap-2 mb-2"
        >
          ${PROVIDER_ICONS[provider.id] ?? ''}
          ${providerAction(provider, mode)}
        </a>
      `).join('')}
    `;
  } catch {
    root.innerHTML = '';
    root.classList.add('d-none');
  }
}
