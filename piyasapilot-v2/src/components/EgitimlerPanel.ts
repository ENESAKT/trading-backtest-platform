import { KategoriSidebar } from './egitimler/KategoriSidebar';
import { MakaleGorsel } from './egitimler/MakaleGorsel';
import { KopruAksiyonlari } from './egitimler/KopruAksiyonlari';

export class EgitimlerPanel {
  private container: HTMLElement;
  // @ts-ignore - used for initializing HTML currently
  private sidebar: KategoriSidebar;
  private makaleGorsel: MakaleGorsel;
  private kopruAksiyonlari: KopruAksiyonlari;

  private currentCategory: string = 'indikatorler';
  private currentMakaleIdx: number = 0;

  // Mock index for now
  private makaleListesi: Record<string, {title: string, content: string, indicatorKey?: string, presetId?: string, screenerFilter?: any}[]> = {
    'indikatorler': [
      {
        title: 'Bollinger Bandı',
        content: `<h3>Bollinger Bandı</h3><p>Bollinger bantları volatilite ölçümünde kullanılır...</p>`,
        indicatorKey: 'BB',
        presetId: 'bollinger_bounce'
      },
      {
        title: 'RSI',
        content: `<h3>Göreceli Güç Endeksi (RSI)</h3><p>RSI, aşırı alım ve aşırı satım bölgelerini gösterir...</p>`,
        indicatorKey: 'RSI'
      }
    ],
    'formasyonlar': [
      {
        title: 'OBO',
        content: `<h3>Omuz Baş Omuz (OBO)</h3><p>Trend dönüş formasyonudur.</p>`
      }
    ],
    'sistem-backtest': [],
    'viop-vadeli': [],
    'psikoloji-disiplin': []
  };

  constructor(container: HTMLElement) {
    this.container = container;
    this.container.innerHTML = `
      <div class="egitimler-layout">
        <div class="egitimler-left" id="egitimler-sidebar"></div>
        <div class="egitimler-content">
          <div class="makale-list-panel"></div>
          <div class="makale-view-panel">
            <div id="makale-gorsel-container"></div>
            <div id="kopru-container"></div>
          </div>
        </div>
      </div>
    `;

    const sidebarEl = this.container.querySelector('#egitimler-sidebar') as HTMLElement;
    const gorselEl = this.container.querySelector('#makale-gorsel-container') as HTMLElement;
    const kopruEl = this.container.querySelector('#kopru-container') as HTMLElement;

    this.makaleGorsel = new MakaleGorsel(gorselEl);
    this.kopruAksiyonlari = new KopruAksiyonlari(kopruEl);

    this.sidebar = new KategoriSidebar(sidebarEl, (category) => {
      this.currentCategory = category;
      this.currentMakaleIdx = 0;
      this.renderCurrentList();
    });

    this.renderCurrentList();
  }

  private renderCurrentList() {
    const listPanel = this.container.querySelector('.makale-list-panel') as HTMLElement;
    const list = this.makaleListesi[this.currentCategory] || [];
    
    if (list.length === 0) {
      listPanel.innerHTML = '<p class="text-muted">Bu kategoride henüz içerik yok.</p>';
      this.makaleGorsel.showError('İçerik seçilmedi.');
      this.kopruAksiyonlari.render(); // empty
      return;
    }

    let html = '<ul class="makale-list">';
    list.forEach((m, idx) => {
      html += `<li class="${idx === this.currentMakaleIdx ? 'active' : ''}" data-idx="${idx}">${m.title}</li>`;
    });
    html += '</ul>';
    listPanel.innerHTML = html;

    const items = listPanel.querySelectorAll('li');
    items.forEach(li => {
      li.addEventListener('click', (e) => {
        const idx = parseInt((e.target as HTMLElement).dataset.idx || '0', 10);
        this.currentMakaleIdx = idx;
        items.forEach(i => i.classList.remove('active'));
        (e.target as HTMLElement).classList.add('active');
        this.renderCurrentMakale();
      });
    });

    this.renderCurrentMakale();
  }

  private renderCurrentMakale() {
    const list = this.makaleListesi[this.currentCategory] || [];
    if (this.currentMakaleIdx >= list.length) return;
    const makale = list[this.currentMakaleIdx];
    
    this.makaleGorsel.render(makale.content);
    this.kopruAksiyonlari.render(makale.indicatorKey, makale.presetId, makale.screenerFilter);
  }
}
