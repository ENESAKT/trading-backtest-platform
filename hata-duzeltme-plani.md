# Hata Düzeltme Planı — PiyasaPilot v2.1

> **Amaç:** Kullanıcı tarafından raporlanan 4 ana hatanın sistematik izlenmesi ve düzeltilmesi.
> **Oluşturulma:** 2026-05-02

---

## Hata Özet Tablosu

| # | Başlık | Öncelik | Dosyalar | Durum |
|---|--------|---------|----------|-------|
| H1 | Sol Menü Toggle + State Hatası + Renk Mantığı | 🔴 Yüksek | `Sidebar.ts`, `app.ts`, `style.css` | ✅ Tamamlandı |
| H2 | Göstergeler Dropdown + Favori Pinleme | 🟡 Orta | `ChartPanel.ts`, `style.css` | ✅ Tamamlandı |
| H3 | Tam Ekran + Kompakt Floating Toolbar | 🟡 Orta | `ChartPanel.ts`, `style.css` | ✅ Tamamlandı |
| H4 | Çoklu Sembol Dual Y-Axis Ölçekleme | 🔴 Yüksek | `ChartPanel.ts`, `MultiChartLayout.ts` | ✅ Tamamlandı |

---

## H1 — Sol Menü (Sembol Listesi) Davranışı ve State Yönetimi

### H1.1 — Toggle (Açılır/Kapanır Panel)

**Problem:** Sidebar paneli sabit genişlikte duruyor, grafiğe odaklanmak için kapatılamıyor.

**Çözüm:**
- `Sidebar.ts` → `render()` içine `.sidebar-header`'a toggle butonu eklenmeli
- `app.ts` → Sidebar toggle event'ini dinleyip sidebar container'ına `collapsed` class'ı toggle etmeli
- `style.css` → `.sidebar.collapsed` durumunda `--sidebar-w: 0px` + `display: none` uygulanmalı
- Buton ikonu: `«` (açıkken) / `»` (kapalıyken)
- `localStorage` ile toggle state kalıcı tutulmalı

**Kabul Kriteri:** ✅ Toggle butonuna tıklanınca sidebar gizlenir/gösterilir. Grafik alanı tam genişliğe yayılır.

### H1.2 — Liste State Hatası (Fiyat Ezilmesi)

**Problem:** Bir hisse seçildiğinde sidebar'daki tüm hisselerin fiyat/yüzde verileri seçilen hissenin değerleriyle değişiyor.

**Kök Neden Analizi:**
- `Sidebar.ts` → `refreshTicker()` metodu `[data-symbol="..."]` ile doğru elementi buluyor ✅
- `DataEngine.ts` → `onPriceUpdate` event'i tetiklendiğinde `app.ts`'teki handler `sidebar.updateTicker(evt.symbol, evt.price, evt.changePct)` çağırıyor
- **Gerçek sorun:** `DataEngine` polling veya WS callback'inde tüm cache'li sembollere aynı fiyat yayınlanıyor olabilir, VEYA `renderGroups()` çağrıldığında eski ticker cache'i doğru okunmuyor

**Çözüm:**
1. `DataEngine.ts` ve `PollingManager.ts` → price update yayınlama mantığını kontrol et ve sadece ilgili sembolün verisini yayınladığından emin ol
2. `Sidebar.ts` → `refreshTicker()` sadece `data-symbol` eşleşen DOM elemanını güncellemeli (mevcut kod doğru görünüyor)
3. Eğer sorun DOM yeniden render'da ise, `applySearch("")` → `renderGroups()` sonrası `priceTickers` cache'ten güncelleme tetiklenmeli

**Kabul Kriteri:** ✅ Hisse seçildiğinde sadece seçili hissenin rengi değişir, diğer hisselerin fiyat/yüzde değerleri bağımsız kalır.

### H1.3 — Koşullu Renklendirme (0.00% Sarı)

**Problem:** %0.00 değişim gösteren hisseler yeşil renkte gösteriliyor, oysa nötr/yüklenmemiş olmalı.

**Kök Neden:**
- `Sidebar.ts` satır 159: `changePct >= 0 ? 'pos' : 'neg'` → 0 dahil yeşil (pos) sınıfı alıyor
- `Sidebar.ts` satır 247: `changePct >= 0 ? 'pos' : 'neg'` → aynı hata refreshTicker'da da var

**Çözüm:**
- 3 durumlu renk mantığı: `> 0 → 'pos'`, `< 0 → 'neg'`, `=== 0 → 'neutral'`
- `style.css` → `.neutral { color: var(--yellow); }` CSS kuralı eklenmeli
- Hem `createSymbolItem()` hem `refreshTicker()` güncellenmeli

**Kabul Kriteri:** ✅ 0.00% olan hisseler sarı renkte görünür.

---

## H2 — Göstergeler (Indicators) Yönetimi

### H2.1 — Kompakt Gösterge Dropdown

**Problem:** Üst toolbar'da gösterge butonları çok yer kaplıyor, kompakt bir dropdown gerekli.

**Çözüm:**
- `ChartPanel.ts` → `controlsHTML()` içindeki mevcut ind-btn satırlarını bir dropdown container'a sar
- Dropdown trigger: "Göstergeler ▾" butonu
- Açıldığında mevcut gösterge seçenekleri kompakt listede görünsün
- Aktif gösterge sayısı badge olarak gösterilsin

### H2.2 — Favori Gösterge Pinleme

**Problem:** Favoriye alınan göstergeler toolbar'a pinlenmiyor, aktif göstergeler hızlı erişilemez durumda.

**Çözüm:**
- Favori göstergeler (yıldızlanmış) toolbar'da mini pill butonlar olarak gösterilsin
- Aktif göstergeler toolbar'da kompakt badge/chip şeklinde görünsün
- Chip'e tıklayınca parametre ayar popup'ı açılsın

**Kabul Kriteri:** ✅ Yıldızlanan göstergeler toolbar'da pinli görünür. Aktif göstergeler kompakt chip olarak erişilebilir.

---

## H3 — Tam Ekran ve Kompakt Araç Çubuğu

### H3.1 — Fullscreen Modu

**Mevcut Durum:** `ChartPanel.ts` satır 1991-2012 → Fullscreen zaten var, `F` tuşu ile çalışıyor. `toggleFullscreen()` native `requestFullscreen()` ve CSS fallback kullanıyor.

**Eksik:** Tam ekrandayken toolbar gizlenip kompakt menüye dönüşmüyor.

### H3.2 — Floating Kompakt Toolbar

**Problem:** Tam ekrandayken geniş toolbar grafiğin üstünde yer kaplıyor.

**Çözüm:**
- `ChartPanel.ts` → `onFullscreenChange()` içinde `.chart-controls`'a `fullscreen-compact` class'ı toggle et
- `style.css` → `.fullscreen-compact` durumunda:
  - `position: absolute; top: 0; left: 0; right: 0; z-index: 100;`
  - `opacity: 0; transform: translateY(-100%);` (gizli)
  - `:hover` veya `.shown` → `opacity: 1; transform: translateY(0);`
  - `backdrop-filter: blur(12px); background: rgba(11, 14, 20, 0.9);`
- Üst 40px alanına fare gelince toolbar kayarak açılsın

**Kabul Kriteri:** ✅ Tam ekranda toolbar otomatik gizlenir, fare üst kenara gelince açılır.

---

## H4 — Çoklu Sembol (Dual Y-Axis) Ölçekleme

### Mevcut Durum
`ChartPanel.ts` satır 2078-2162 → `setCompareData()` zaten `priceScaleId: 'left'` kullanıyor ve Dual Y-Axis mantığı implemente edilmiş.

**Mevcut sorunlar:**
1. Sol eksen (`left`) visible yapılıyor ama `autoScale` ve `scaleMargins` ayarlanmıyor
2. `resetPriceScales()` sadece `right` ekseni resetliyor, `left` ekseni yok sayıyor
3. Percent modunda karşılaştırma verisi doğru normalize edilmiyor olabilir

**Çözüm:**
- `setCompareData()` → Sol eksen `autoScale: true` ve `scaleMargins` ile ayarlanmalı
- `resetPriceScales()` → Sol eksen de resetlenmeli
- Sol eksene stil verilmeli (renk, border, text)
- Her iki grafik bağımsız auto-scale yapmalı

**Kabul Kriteri:** ✅ İki farklı fiyat skalasındaki semboller (ör: BIMAS + AKBNK) üst üste ama bağımsız ölçeklenmiş şekilde görünür. Sol ve sağ eksenler doğru fiyat aralığını gösterir.

---

## Uygulama Sırası

```
1. H1 (Sidebar) → En çok kullanıcıyı etkileyen state hatası
2. H4 (Dual Y-Axis) → Fonksiyonel bozukluk
3. H3 (Fullscreen Toolbar) → UX iyileştirmesi
4. H2 (Gösterge Dropdown) → UX iyileştirmesi
```

---

## Not

Her hata düzeltmesinden sonra bu dosyadaki ilgili satırdaki durum `✅ Tamamlandı` olarak güncellenecek ve kısa bir açıklama eklenecektir.
