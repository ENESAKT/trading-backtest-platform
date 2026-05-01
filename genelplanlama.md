# GENEL PLANLAMA — PiyasaPilot Yürütme Haritası

> Tek yürütme rehberi. Yeni bir ajan veya yeni oturum önce burayı, sonra ilgili alt planı okur.
> Tarih: 2026-05-01 · Branch: `codex/education-feature-planning`

---

## 1. Doğruluk Kaynağı

| Öncelik | Dosya | Rol |
|---:|---|---|
| 1 | `genelplanlama.md` | Hangi sırayla ilerleyeceğimizi söyler |
| 2 | `planlama.md` | Plan dosyalarının index'i |
| 3 | `planlama-sprint-aktif.md` | Aktif fazların kısa takip tablosu |
| 4 | `planlama-egitimler.md` | Eğitimler sekmesi ve makale planı |
| 5 | `egitimplanlama.md` | BORFİN okuma kanıtları ve kurs envanteri |
| 6 | `planlama-backtest.md`, `planlama-grafik.md`, `planlama-mali-analiz.md` | Alan planları |

`ROADMAP.md`, `ILERLEME.md` ve `PROJE_DURUM_OZET.md` tarihsel snapshot kabul edilir; güncel sprint kararı için kullanılmaz.

---

## 2. Borfin İçerik Uygunluk Kararı

BORFİN arşivi ürün için uygun, ama doğrudan içerik kaynağı değil; kavram ve iş akışı kaynağıdır.

| Alan | Karar | Gerekçe |
|---|---|---|
| Eğitimler sekmesi | Uygun | Kavramlar özgün PiyasaPilot makalelerine dönüştürülebilir |
| Grafik Lab | Uygun | Trend, kanal, Fibonacci, formasyon ve gösterge kavramları grafik araçlarına bağlanabilir |
| Backtest Lab | Çok uygun | Algo trade, WFA, Monte Carlo, System Tester, Explorer ve rapor kavramları ürün çekirdeğiyle örtüşüyor |
| VIOP/Vadeli | Uygun ama kapılı | Veri/lisans/kontrat varsayımları olmadan gerçek işlem veya paper aksiyonu açılmamalı |
| Mali Analiz | Beklemeli | İlgili temel/mali analiz kursları henüz OCR ile okunmadı; plan şimdilik taslak |
| Opsiyon/Varant/Swap | Beklemeli | 33 video okunmadan yalnızca gelecek modül ve risk uyarısı seviyesinde kalmalı |
| Platform eğitimleri | Kısıtlı | Finnet/Fastweb/Stockeys gibi ürün ekranları kopyalanmaz; sadece ihtiyaç listesi çıkarılır |

Yasaklar: Borfin ekran görüntüsü, marka dili, uzun metin, telifli formül, yardımcı dosya içeriği ve kurs slaytları birebir ürüne taşınmaz.

---

## 3. Borfin Okuma Durumu

Toplam arşiv: 26 kurs klasörü, 825 video.

| Durum | Kurs | Video | Not |
|---|---:|---:|---|
| Tamamlandı | 9 | 469 | Frame OCR + bazı yardımcı dosya metinleri |
| Bekliyor | 17 | 356 | Önce finansal analiz ve opsiyon/varant/swap dilimleri okunacak |

Okuma yöntemi şu an ses transkripti değil, macOS AVFoundation + Vision frame OCR. Bu nedenle ekranda görünmeyen konuşma detayları eksik olabilir. İçerik makalelerine `source_confidence`, `source_method` ve `needs_audio_transcript` alanları konacak.

---

## 4. Uygulama Sırası

### 0. Git ve repo hijyeni

- [x] `artifacts/` git dışına alınacak.
- [x] Yerel SQLite çalışma veritabanları git dışına alınacak.
- [x] Tracked olan `data/strategy_lab/strategies.sqlite3` index'ten çıkarıldı; lokal dosya olarak korunuyor.
- [ ] Commitler path bazlı yapılacak; artifact, cache, lokal DB ve kişisel memory dosyaları commitlenmeyecek.

### 1. Eğitim kaynak modelini sabitle

- [ ] `planlama-egitimler.md` içindeki makale listesi OCR kanıtı ve güven notuyla eşleşecek.
- [ ] Her makale frontmatter'ına kaynak kurs, yöntem ve güven alanı eklenecek.
- [x] Borfin OCR'da açık kanıtı olmayan `VWAP` başlığı Eğitimler v1 listesinden çıkarıldı; yerine OCR'da görülen hacim indikatörleri kullanıldı.

### 2. Eğitimler sekmesi altyapısı

- [ ] Klavye sırası korunacak: Sinyaller `5`, Eğitimler `6`, Mali Analiz `7`.
- [x] `EgitimlerPanel.ts` ve içerik klasörleri eklenecek.
- [x] İlk sürümde güvenli markdown render, kategori, arama ve köprü aksiyonları olacak.
- [x] İlk içerik dalgası: Bollinger, RSI, MACD, SMA/EMA, ATR.

### 3. Grafik ve eğitim köprüleri

- [ ] Eğitim makalesinden grafiğe indikatör ekleme.
- [ ] Formasyon/Fibonacci yazılarından ilgili çizim aracına köprü.
- [ ] Risk uyarısı: gecikme, repaint, yanlış teyit, düşük hacim.

### 4. Backtest Lab düzeltme

- [x] `planlama-backtest.md` mevcut yapılmış altyapı ve kalan işler diye ayrıldı.
- [ ] StrategySpec/short/report archive/CSV/optimizer gibi mevcut işler tekrar yapılacak gibi gösterilmeyecek.
- [ ] Kalan ağır işler: WFA modülü, Monte Carlo, kalite skoru, stabil optimizasyon, portföy lab.

### 5. Mali Analiz önce okuma, sonra kod

- [ ] Cahit Yılmaz Mali Analiz Teknikleri, Temel Analiz, Üzeyir Doğan, Firma Değerleme ve Fastweb/Finnet eğitimleri önce OCR'dan geçirilecek.
- [ ] Sonra `planlama-mali-analiz.md` oran seti, veri şeması ve API kontratı yeniden netleştirilecek.
- [ ] BIST 30 listesi statik yazılmayacak; uygulamadaki sembol kaynağı veya sağlayıcıdan üretilecek.

### 6. VIOP ve türevler

- [ ] Vadeli/VOB planı sadece gerçek veri/kontrat varsayımı kapılarıyla ilerleyecek.
- [ ] Opsiyon/Varant/Swap kursları okunduktan sonra eğitim makalelerine ve risk uyarılarına bağlanacak.

---

## 5. Kabul Kapıları

- Plan değişikliği: ilgili `.md` dosyasında durum ve kaynak notu güncellenir.
- Kod değişikliği: en dar ilgili test çalıştırılır.
- Frontend değişikliği: ilgili E2E veya en azından build kontrolü yapılır.
- Eğitim içeriği: Borfin'den birebir kopya yok, kaynak yöntemi ve güven notu var.
- Git: artifact/cache/sqlite yok; commit tek konuya ait; push sonrası branch durumu temiz veya bilinçli artıklarla raporlanır.
