# Araç Çubuğu (Toolbar) İleri Düzey Optimizasyon Planı

Kullanıcı geri bildirimlerine göre mevcut `ChartPanel` araç çubuğu çok kalabalık, sağa doğru taşıyor ve kullanımı zorlaştırıyor. İhtiyaç duyulan özellikler: Hover ile açılan/kapanan menüler, pinleme (sabitleme) özelliği, aktif elemanların belirgin renkle (yeşil) yanması ve genel gruplandırma.

## 1. Gruplandırma ve Dropdown Dönüşümleri
Araç çubuğundaki yığınla buton, sadece seçili olanı gösterecek şekilde "Kompakt Dropdown" (veya mega menü) yapılarına dönüştürülecek.
- **Zaman Dilimi:** `[ 1G ▾ ]` şeklinde tek buton. Tıklanınca diğer süreler açılacak.
- **Grafik Tipi:** `[ Mum ▾ ]` şeklinde tek buton. Tıklanınca Çizgi, Bar vs. açılacak.
- **Ölçek ve K/Z:** `[ ⚙️ Görünüm ▾ ]` şeklinde tek ikon. İçerisinde Lin, Log, %, Oto, PnL, Risk butonları liste halinde yer alacak.
- **Çizim Araçları:** `[ ✏️ Çizim ▾ ]` menüsü altında toplanacak.

## 2. Göstergeler (İndikatörler) Hover ve Pin Mekanizması
- **Davranış:** Araç çubuğunda veya grafik alanının hemen içinde bir `Göstergeler` bölgesi olacak. Farenin üzerine gelinmediği sürece sadece "fx (3)" gibi bir özet veya küçük ikonlar görünecek. Fare üzerine geldiğinde genişleyecek (aktif göstergelerin isimleri ve değerleri çıkacak).
- **Pinleme (Sabitleme):** Bu alanın yanında bir 📌 butonu olacak. Kullanıcı buna tıklarsa alan genişletilmiş halde "sabit" (pinned) kalacak. Fiş çekilene kadar daralmayacak.
- **Vurgu:** Seçilmiş (aktif) olan göstergeler listede yeşil (veya temanın belirgin bir rengi) ile yanacak.

## 3. Taşmayı (Overflow) Kesin Olarak Önleme
- `.chart-controls` için `flex-wrap: nowrap;` uygulanacak. Sığmayan öğelerin bozulmaması için `overflow-x: auto` ve `::-webkit-scrollbar { display: none; }` eklenecek.
- Çoklu grafik modunda bile her bir grafik paneli kendi içinde bu daraltılmış kompakt yapıyı kullanacak.

## Uygulama Adımları
1. `ChartPanel.ts` dosyasında `controlsHTML` metodunu yukarıdaki gruplara uygun HTML yapısıyla yeniden yaz.
2. `ChartPanel.ts` içindeki `bindControls` olay dinleyicilerini yeni dropdown mantığına, menülerin dışa tıklandığında kapanmasına uyumlu hale getir.
3. Göstergeler alanı için CSS (`style.css`) tarafında `hover`, `width` animasyonu (transition) ve `.pinned` class'ı mantığını kurgula. Aktif `.active` class'larına yeşil `var(--green)` rengi uygula.
4. Yeni pinleme state'i için `ChartPanel.ts` içine `isIndicatorsPinned` (boolean) state'i ekle ve butona tıklandığında bunu toggle et.
