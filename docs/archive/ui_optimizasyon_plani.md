# PiyasaPilot UI/UX Optimizasyon Planı

Kullanıcının geri bildirimi ve tarayıcıdaki ekran görüntüsü (`click_feedback_1777716897021.png`) incelendiğinde, grafik arayüzünün mevcut haliyle "kullanışsız" olduğu görülmüştür. Temel sorunlar:
1.  **Araç Çubuğu Aşırı Yüklü:** Dikeyde 4-5 satıra yayılan `chart-controls` alanı, grafik (canvas) alanını ezmektedir. Özellikle çoklu pencere düzenine geçildiğinde grafik boyutu neredeyse sıfıra inmektedir. `ctrl-group`'lar sığmadığı için alt satıra geçmektedir (flex-wrap).
2.  **Karşılaştırma ve Araçlar Menüsü:** Karşılaştırma butonları ve giriş alanları çok yer kaplamaktadır. Bu özellikler ve göstergeler menüsü optimize edilmelidir.
3.  **İndikatör Butonları ve Badge:** "Göstergeler" dropdown menüsünün tasarımı ve pinlenen indikatör chip'leri araç çubuğunun dikeyde şişmesine neden olmaktadır.
4.  **Tam Ekran Floating Toolbar:** Tam ekran moduna geçildiğinde gizlenen araç çubuğunun tetikleyici (`hover`) yapısı ve görünümü beklendiği gibi kompakt ve düzenli çalışmamaktadır.

## Aksiyon Planı

### Adım 1: Araç Çubuğunu Tek Satıra (veya Çok İnce İki Satıra) İndirme
-   [x] `style.css` içindeki `.chart-controls` sınıfı güncellendi. Kaydırmalı toolbar yerine gruplu, okunabilir ve hover ile aşağı açılan araç alanı kullanılıyor.
-   [x] `ChartPanel.ts` içindeki `controlsHTML` kompakt hale getirildi. Zaman, gösterge, ölçek, karşılaştırma, çizim ve çıktı kontrolleri ayrı gruplarda toplandı.
-   [x] "Karşılaştır", "Ölçek", "Zaman Dilimi" gibi metin etiketleri (`ctrl-label`) kaldırıldı.

### Adım 2: Çoklu Grafik Düzeninde "Yükleniyor..." Takılmasını Giderme
-   [x] `MultiChartLayout.ts` layout değişiminden sonra tüm panelleri yeniden boyutlandırıyor.
-   [x] Karşılaştırma verisi yüklenirken ana grafiğin status'ü artık `loading` durumuna çekilmiyor; mevcut mumlar korunuyor.

### Adım 3: İndikatör Dropdown ve Kompakt Pinlerin Düzenlenmesi
-   [x] İndikatörler "Gösterge / ƒx" grubu altında toplandı; detay liste hover ile aşağı açılıyor ve tıklama mantığı düzeltildi.
-   [x] Aktif indikatörler toolbar'dan çıkarılıp grafiğin sol üstünde kompakt lejant olarak gösteriliyor.
-   [x] Eski test/klavye alışkanlığı bozulmasın diye hızlı indikatör butonları çok kompakt bir şerit olarak korundu.

### Adım 4: Tam Ekran Floating Menü Düzeltmesi
-   [x] Tam ekran modunda araç çubuğu floating/compact moda geçiyor; event satırı gizleniyor ve grafik yüksekliği toolbar yüksekliğini düşmeden hesaplanıyor.
-   [x] Native fullscreen başarısız olursa CSS fullscreen fallback'i de aynı toolbar davranışını kullanıyor.

## Doğrulama

- `npm run typecheck`
- `npm run build`
- `npx playwright test tests/e2e/smoke.spec.ts` -> 18/18 passed
