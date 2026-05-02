export class MakaleGorsel {
  // Placeholder class for article visualization / markdown rendering logic if needed,
  // or simple wrapper to display loaded markdown content cleanly.
  private container: HTMLElement;

  constructor(container: HTMLElement) {
      this.container = container;
  }

  public render(htmlContent: string) {
      this.container.innerHTML = `<div class="makale-icerik markdown-body">${htmlContent}</div>`;
  }

  public showLoading() {
      this.container.innerHTML = `<div class="loading-spinner">Makale yükleniyor...</div>`;
  }
  
  public showError(msg: string) {
      this.container.innerHTML = `<div class="error-msg">${msg}</div>`;
  }
}
