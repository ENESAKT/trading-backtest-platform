# Grafik Lab — Plan (Sprint G2–G10)

> Sprint G1 tamamlandı (fiyat skalası reset, son fiyat çizgisi, önceki kapanış).
> Bu dosya G2+ sprint planlarını içerir.
> Kaynak: Matriks Grafik Menüleri PDF (70 sayfa) incelendi.
> Kural: Matriks kopyalanmaz; PiyasaPilot'un TS/lightweight-charts mimarisiyle uyumlu özgün özellikler.
> Tarih: 2026-05-01

---

## Mevcut Grafik Gerçekleri

- [x] `ChartPanel.ts`: mum/bar/çizgi, hacim, RSI, MACD alt panelleri, BB/EMA/VWAP overlay
- [x] `MultiChartLayout.ts`: 1x1, 1x2, 2x1, 2x2 çoklu pencere
- [x] `indicators/`: EMA, SMA, RSI, MACD, BB, ATR, VWAP, Stochastic
- [x] Backtest/paper sinyal marker'ları
- [x] Sprint G1: sembol değişiminde fiyat skalası reset, son fiyat çizgisi, önceki kapanış çizgisi

---

## Sprint G2 — Ölçek Menüsü ve Yüzdesel Mod

- [ ] Ölçek menüsü: `Lineer`, `Logaritmik`, `Yüzdesel`
- [ ] Yüzdesel modda kullanıcı başlangıç barı seçer; o nokta %0, sonrası yüzde değişim
- [ ] Yüzdesel mod çoklu sembol karşılaştırmasında birincil kullanım
- [ ] Crosshair bilgi panelinde: önceki kapanışa, başlangıç barına yüzde fark
- [ ] TL/USD/USDT birim görünümü — ileride portföy para birimi moduna zemin
- [ ] **Kabul:** 10 TL ve 1000 TL fiyatlı iki sembol yüzdesel modda karşılaştırılır
- [ ] **Test:** Unit: yüzde normalize — başlangıç barı %0, sonraki `(close/base - 1) * 100`
- [ ] **Test:** Playwright: yüzdesel modda iki sembol aynı panelde okunabilir

---

## Sprint G3 — İndikatör Merkezi v2

- [ ] Mevcut basit butonlar yerine sağ/üst açılır "İndikatörler" paneli
- [ ] Panel: arama, kategori, favori ve aktif indikatör listesi
- [ ] Her indikatör için parametre penceresi: periyot, kaynak (`close/open/high/low/hlc3`), renk, çizgi kalınlığı, bölge, öteleme
- [ ] Aynı indikatörden birden fazla instance: EMA 9, EMA 21, EMA 50 aynı grafikte
- [ ] İndikatör bölge seçimi: ana grafik overlay, yeni alt panel, mevcut alt panel
- [ ] RSI/Stochastic'te 30/70, 20/80 alarm seviyeleri kalıcı çizgi
- [ ] İndikatör grupları: "Trend seti", "Mean reversion seti", "Momentum seti" — kaydetme + tek tıkla uygulama
- [ ] **Kabul:** ATR ve Stochastic panelden açılır, parametre değişimi grafiği yeniden hesaplar
- [ ] **Test:** E2E: indikatör parametresi değişir, seri yeniden hesaplanır, ayar yenilemeden sonra korunur

---

## Sprint G4 — Kar/Zarar Overlay'leri

- [ ] Açık paper pozisyonu grafikte: maliyet çizgisi + canlı PnL etiket
- [ ] Backtest trade'leri: giriş-çıkış bağlantı çizgileri
- [ ] Crosshair tooltip'te işlem varsa: adet, giriş/çıkış fiyatı, net PnL, yüzde getiri
- [ ] "Mesafe ölçer" aracı: giriş-stop-hedef seçilince potansiyel kar/zarar yüzdesi
- [ ] BIST tavan/taban seviyeleri çizgisi (veri yoksa pasif/gri)
- [ ] Stop-loss, take-profit ve hedef fiyat çizgileri opsiyonel overlay
- [ ] **Kabul:** Kullanıcı grafikte yüzde kar/zararını okur, panel değiştirmez
- [ ] **Test:** Unit: PnL etiketi long/short için doğru yüzde ve TL hesaplar

---

## Sprint G5 — Çizim Altyapısı

- [ ] İlk çizim seti: trend çizgisi, yatay çizgi, dikey çizgi, ray/sağa uzat, paralel, kanal, dikdörtgen, ok, not
- [ ] Ölçüm aracı: bar sayısı, süre, fiyat farkı, yüzde fark, risk/ödül oranı
- [ ] Trend çizgisi: isim, renk, kalınlık, çizgi tipi, yüzde değişim etiketi
- [ ] Çizimler sembol + timeframe + layout bağlamında saklanır; şablon çizimleri ve sembole özel çizimler ayrılır
- [ ] Çizimler pan/zoom sırasında doğru koordinatta kalır; sembol değişince yanlış sembolde görünmez
- [ ] **Kabul:** Çizilen trend, sembol değişince temizlenir; aynı sembole dönünce geri gelir
- [ ] **Test:** E2E: çizim ekle, taşı, sil, reload sonrası sembole özel çizim geri gelir
- [ ] **İkinci faz:** Fibonacci düzeltme, extension, fan, zaman bölgeleri, regresyon kanalı (Sprint G10)

---

## Sprint G6 — Çoklu Sembol Karşılaştırma

- [ ] Aynı panelde karşılaştırma sembolü ekleme (mevcut çoklu pencereden ayrı "compare overlay")
- [ ] Üç skala modu: aktif sembol skalası, her sembole ayrı skala, yüzdesel normalize
- [ ] Her sembolün renkli etiketi zaman aksı/legend üzerinde
- [ ] Tatil/gap farkları için data eşitleme: boşluk, forward-fill veya ortak takvim seçenekleri
- [ ] Fiyat oranı çok farklıysa UI yüzdesel moda yönlendirir
- [ ] **Kabul:** BIST + kripto gibi farklı takvimli semboller üst üste konunca tarih kayması sinyal üretmez
- [ ] **Test:** Playwright: iki sembol karşılaştırma modunda crosshair her ikisini gösterir

---

## Sprint G7 — Senkronize Grafikler

- [ ] Multi-chart senkron kilitleri: sembol, timeframe, zaman aralığı, crosshair, ölçek modu
- [ ] Aktif pane net vurgulanır; toolbar işlemleri aktif pane'e mi senkron gruba mı uygulanıyor belli olur
- [ ] Sembol değişiminin diğer pane'leri etkileyip etkilemeyeceği kullanıcı seçimine bağlı
- [ ] Crosshair senkronu: aynı tarihte farklı sembollerin OHLC değerleri okunabilir
- [ ] **Kabul:** 2x2 layout'ta pan/zoom sadece ilgili senkron kilidi açıksa diğer grafikleri etkiler
- [ ] **Test:** E2E: multi-pane senkron kilitleri açık/kapalı durumda doğru davranır

---

## Sprint G8 — Şablonlar, Kayıt ve Export

- [ ] Grafik ayarları paneli: tema, zemin, grid, crosshair, son fiyat çizgisi, tooltip
- [ ] Şablon sistemi: genel grafik şablonu + sembole özel kaydedilmiş grafik
- [ ] Varsayılan şablon seçme/kaydetme
- [ ] İndikatör grupları şablon içinde saklanır; çizimler sembole özel saklanır
- [ ] Export: PNG kayıt, görünümü panoya kopyala, OHLCV/indikatör CSV
- [ ] v1: localStorage/workspace JSON; v2: backend workspace persistence
- [ ] **Kabul:** Trend + indikatör görünümü kaydedilip uygulama yenilenince geri gelir
- [ ] **Test:** E2E: şablon kaydet → uygulama yenile → şablon geri gelir

---

## Sprint G9 — Haber/KAP/Bilanço Event Marker'ları

- [ ] Zaman aksında event marker: haber, KAP, bilanço, temettü, sermaye artırımı
- [ ] Marker hover tooltip: başlık, kaynak, saat, kısa özet
- [ ] Event katmanı filtrelenebilir
- [ ] Kaynaklar backend'de ayrılır: borsa-mcp KAP + haber → UI "kaynak bağlı değil" state
- [ ] **Kabul:** Event marker'lar mum/indikatörleri kapatmaz; kullanıcı tamamen gizleyebilir
- [ ] **Bağlantı:** Mali Analiz sekmesiyle köprü — bilanço tarihi tıklanınca MaliAnalizPanel açılır

---

## Sprint G10 — İleri Çizim Araçları

- [ ] Fibonacci düzeltme seviyeleri
- [ ] Fibonacci extension, fan, zaman bölgeleri
- [ ] Regresyon kanalı (lineer ve logaritmik)
- [ ] Renko araştırması: ATR bazlı ve manuel brick size
- [ ] Andrew's Pitchfork (araştırma)
- [ ] Ters grafik ve relatif grafik (deneysel mod)
- [ ] **Kapsam dışı:** 3D mum, Gann, Tirone, otomatik fibo (analiz değeri tartışmalı)
- [ ] **Test:** Her yeni grafik tipi strateji/backtest hesaplarını bozmaz; orijinal OHLCV kullanılır

---

## Test ve Kabul Kapıları (Tüm Grafik Sprintleri)

- [x] Sprint G1: sembol değişiminde grafik boş kalmaz (Playwright geçti)
- [ ] Sprint G2: yüzdesel modda iki sembol karşılaştırılabilir
- [ ] Sprint G3: indikatör parametresi değişince seri yeniden hesaplanır
- [ ] Sprint G4: PnL etiketi doğru hesaplanır
- [ ] Sprint G5: çizim kayıt/yükle döngüsü çalışır
- [ ] Sprint G6: farklı takvimli semboller tarih kaymaması
- [ ] Sprint G7: senkron kilitleri açık/kapalı davranış
- [ ] Sprint G8: şablon kaydet/yükle
- [ ] Sprint G9: event marker render, filtreleme
- [ ] Sprint G10: Fibonacci hesaplama doğruluğu

---

## Tasarım Notları

- Matriks'in yoğun masaüstü terminal mantığı referans alınır; görsel kopyası alınmaz
- PiyasaPilot'un mevcut koyu, sade, okunabilir terminal dili sürdürülür
- Toolbar ikonları: küçük, tanıdık, tooltip'li; uzun metin butonlar yerine ikon/segment
- Ayarlar ana grafik hızını bozmaz; detaylar drawer/modal ile açılır
- Boş/yanlış veri: boş ekran değil, net durum mesajı + yeniden dene aksiyonu
- Her yeni görsel özellik veri doğruluğunu korur; analiz motoru orijinal veri serisini kullanır
