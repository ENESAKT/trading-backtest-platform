export class KopruAksiyonlari {
  private container: HTMLElement;

  constructor(container: HTMLElement) {
    this.container = container;
  }

  public render(indicatorKey?: string, presetId?: string, screenerFilter?: any) {
    let html = '<div class="kopru-aksiyonlari">';
    html += "<h4>PiyasaPilot'ta Kullan</h4>";
    html += '<div class="kopru-btn-group">';
    
    if (indicatorKey) {
      html += `<button class="action-btn chart-add-btn" data-indicator="${indicatorKey}">[Grafiğe Ekle]</button>`;
    }
    
    if (presetId) {
      html += `<button class="action-btn strategy-preset-btn" data-preset="${presetId}">[Backtest Preset'i Dene]</button>`;
    }
    
    if (screenerFilter) {
      html += `<button class="action-btn screener-btn" data-screener='${JSON.stringify(screenerFilter)}'>[Tarayıcıda Ara]</button>`;
    }
    
    if (!indicatorKey && !presetId && !screenerFilter) {
       html += '<span class="text-muted">Bu konu için doğrudan köprü bulunmuyor.</span>';
    }

    html += '</div></div>';
    this.container.innerHTML = html;
    this.bindEvents();
  }

  private bindEvents() {
    // These dispatch custom events that app.ts or MultiChartLayout can catch
    const chartBtns = this.container.querySelectorAll('.chart-add-btn');
    chartBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const indicator = (e.target as HTMLElement).dataset.indicator;
        if (indicator) {
            this.container.dispatchEvent(new CustomEvent('egitimlerBridge:addIndicator', {
                detail: { indicator },
                bubbles: true
            }));
        }
      });
    });

    const strategyBtns = this.container.querySelectorAll('.strategy-preset-btn');
    strategyBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const preset = (e.target as HTMLElement).dataset.preset;
        if (preset) {
            this.container.dispatchEvent(new CustomEvent('egitimlerBridge:loadPreset', {
                detail: { preset },
                bubbles: true
            }));
        }
      });
    });
    
    const screenerBtns = this.container.querySelectorAll('.screener-btn');
    screenerBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const filterStr = (e.target as HTMLElement).dataset.screener;
        if (filterStr) {
            try {
                const filter = JSON.parse(filterStr);
                this.container.dispatchEvent(new CustomEvent('egitimlerBridge:setScreenerFilter', {
                    detail: { filter },
                    bubbles: true
                }));
            } catch(err) {
                console.error("Invalid screener filter JSON");
            }
        }
      });
    });
  }
}
