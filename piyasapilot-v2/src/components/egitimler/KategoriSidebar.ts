export class KategoriSidebar {
  private container: HTMLElement;
  private onSelect: (category: string) => void;

  constructor(container: HTMLElement, onSelect: (category: string) => void) {
    this.container = container;
    this.onSelect = onSelect;
    this.render();
    this.bindEvents();
  }

  private render() {
    this.container.innerHTML = `
      <div class="kategori-sidebar">
        <h3>Eğitim Kategorileri</h3>
        <ul class="kategori-list">
          <li data-category="indikatorler" class="active">İndikatörler (20)</li>
          <li data-category="formasyonlar">Formasyonlar (12)</li>
          <li data-category="sistem-backtest">Sistem & Backtest (10)</li>
          <li data-category="viop-vadeli">VİOP & Vadeli (8)</li>
          <li data-category="psikoloji-disiplin">Psikoloji & Disiplin (7)</li>
        </ul>
      </div>
    `;
  }

  private bindEvents() {
    const items = this.container.querySelectorAll('.kategori-list li');
    items.forEach(item => {
      item.addEventListener('click', (e) => {
        items.forEach(i => i.classList.remove('active'));
        const target = e.target as HTMLElement;
        target.classList.add('active');
        this.onSelect(target.dataset.category || 'indikatorler');
      });
    });
  }
}
