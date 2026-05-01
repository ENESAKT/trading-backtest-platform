# Egitim Planlama ve Borfin Okuma Sureci

> Bu dosya egitim arsivini okuma, kanit toplama ve urun fikrine donusturme
> surecini yonetir. Urune girecek secilmis backlog maddeleri `planlama-egitimler.md`
> ve `planlama-backtest.md` icinde tutulur.

## 1. Kaynak ve Ilke

- Ana kaynak klasor: `/Users/enes/Documents/Ders videoları/BORFİN`
- Bulunan kapsam: 26 egitim klasoru, 825 video.
- Mevcut derin OCR kapsami: 9 kurs tamamlandi (bkz. Bolum 3 Kurs Envanteri).
- Ham raporlar: `artifacts/borfin_*/ocr_report.md`.
- Kural: Video icerigi dosya adindan tahmin edilmeyecek; ses transkripti, kare OCR'i veya manuel kare incelemesiyle dogrulanacak.
- Kural: Borfin, Matriks, TradingView, Active Charts ya da egitimlerdeki metin/formul/dosya icerikleri birebir kopyalanmayacak; PiyasaPilot'a ozgu ozgun urun fikrine donusturulecek.

## 2. Arac Durumu

- `swiftc`: var; macOS AVFoundation/Vision OCR hatti calistirilabilir.
- `ffmpeg` / `ffprobe`: bulunamadi.
- `whisper` / `faster_whisper`: Python ortaminda bulunamadi.
- Varsayilan yontem: once mevcut OCR raporlarini kullan, yeni kurslarda macOS frame OCR ile basla, ses agirlikli videolar icin yerel transkripsiyon bagimliligi eklenene kadar "konusma icerigi eksik olabilir" notu dus.

## 3. Kurs Envanteri ve Oncelik

| Kurs | Video | Oncelik | Durum | PiyasaPilot baglantisi |
|---|---:|---:|---|---|
| İleri Düzey Teknik Analiz — DR. YAŞAR ERDİNÇ | 133 | 1 | OCR tamamlandı | Teknik analiz lab, formasyon, trend, sistem |
| FUAT AKMAN Sistem Trading ve Araçları | 76 | 1 | OCR tamamlandı | DSL, system tester, rapor, explorer |
| TEKNİK ANALİZ — DR. YAŞAR ERDİNÇ | 74 | 1 | OCR tamamlandı | Grafik okuma, uygulama akışı |
| İndikatörlerin Seçimi ve Kullanımı — FUAT AKMAN | 67 | 1 | OCR tamamlandı | İndikatör merkezi, kategori, parametre |
| VOB — DR. YAŞAR ERDİNÇ | 49 | 1 | OCR tamamlandı | VIOP/VOB, vadeli backtest varsayımları |
| KIVANÇ ÖZBİLGİÇ — Algo Trade | 22 | 1 | OCR tamamlandı | Strateji lifecycle, backtest, WFA, Monte Carlo |
| KIVANÇ ÖZBİLGİÇ — Hareketli Ortalamalarla Algo Trade | 15 | 1 | OCR tamamlandı | HO stratejileri, period/vade uyumu |
| Vadeli Trade Öğreniyorum — DOÇ.DR. EVREN BOLGÜN | 14 | 2 | OCR tamamlandı | VIOP/vadeli ürün bilgisi |
| Yatırımcı Psikolojisi ve Beynin Zaaflarını Yenmek | 19 | 2 | OCR tamamlandı | Disiplin, stop, postmortem, davranışsal risk |
| Opsiyon Trade Öğreniyorum — DOÇ.DR. EVREN BOLGÜN | 13 | 2 | Bekliyor | Opsiyon kavramları ve risk uyarıları |
| DOÇ.DR. EVREN BOLGÜN Varant Trade Öğreniyorum | 10 | 2 | Bekliyor | Varant risk uyarıları |
| Swap-Forward Trade — DOÇ.DR. EVREN BOLGÜN | 10 | 2 | Bekliyor | Forward/swap kavramları |
| CAHİT YILMAZ Mali Analiz Teknikleri | 87 | 1 | Bekliyor | Mali analiz sekmesi için ana kaynak |
| TEMEL ANALİZ — DR. YAŞAR ERDİNÇ | 29 | 1 | Bekliyor | Temel analiz kavramları |
| ÜZEYİR DOĞAN Temel Analiz ile Hisse Seçimi | 15 | 1 | Bekliyor | Hisse seçimi ve değerleme |
| Firma Değerleme ve Finansal Risk Analizi Platformu | 33 | 1 | Bekliyor | Değerleme ve finansal risk |
| Fastweb Mali Analiz Pro Eğitimi | 16 | 2 | Bekliyor | Mali analiz ekran ihtiyaçları |
| Finnet 2000+ Eğitimi | 15 | 3 | Bekliyor | Platform iş akışı, kısıtlı kullanım |
| Finnet Teknik Analist 4.0 Eğitimi | 24 | 3 | Bekliyor | Platform iş akışı, kısıtlı kullanım |
| Teknik Analizde Ortalamaların Kullanımı — FUAT AKMAN | 29 | 2 | Bekliyor | HO/ortalama içeriklerini güçlendirme |
| Tahvil Expert Eğitimi | 7 | 3 | Bekliyor | Tahvil/verim eğrisi gelecek modül |
| Haber Expert Eğitimi | 10 | 3 | Bekliyor | Haber/KAP/event marker fikirleri |
| Hisse Expert Eğitimi | 13 | 3 | Bekliyor | Hisse tarama/platform ihtiyacı |
| QueenStocks Professional Eğitimi | 20 | 3 | Bekliyor | Platform iş akışı, kısıtlı kullanım |
| Stockeys Pro Eğitimi | 16 | 3 | Bekliyor | Platform iş akışı, kısıtlı kullanım |
| Fonbul+ Eğitimi | 9 | 3 | Bekliyor | Fon/portföy gelecek modül |

**Tamamlanan:** 9 kurs, 469 video (%57) · **Bekleyen:** 17 kurs, 356 video (%43)

## 4. Urune Deger Filtresi

Her video veya konu su sorularla degerlendirilir:

- PiyasaPilot'un ana konusu olan grafik, teknik analiz, backtest, strateji, risk veya paper trading akisini guclendiriyor mu?
- Kullanici icin fark yaratan bir is akisi uretiyor mu, yoksa sadece bilgi notu mu?
- Test edilebilir mi: unit, integration, E2E veya kabul senaryosu yazilabilir mi?
- Veri kalitesi, repaint, overfit, slippage, VIOP vade/kontrat gibi riskleri daha gorunur kiliyor mu?
- Mevcut mimariye uyuyor mu: StrategySpec, indikator merkezi, grafik paneli, backtest raporu, paper robot veya tarayiciya baglanabiliyor mu?

Sadece bu filtreden gecen maddeler ilgili planlama dosyasina tasinir.

## 5. Okuma Ciktisi Formati

Her derin okuma kaydi su alanlarla yazilir:

- Kaynak kurs ve video.
- Okuma yontemi: transkript, OCR, manuel kare veya hibrit.
- Gozlenen icerik: slayt/platform/formul/rapor ekrani kanitlari.
- PiyasaPilot'a donusen fikir.
- Kullanici problemi.
- Uygulama noktasi: frontend, backend, StrategySpec, backtest, data, paper, docs.
- Test/kabul senaryosu.
- Guven notu: yuksek, orta, dusuk.

## 6. Checkpoint ve Commit Akisi

- Branch: `codex/education-feature-planning`.
- [x] Commit 1: `egitimplanlama.md` iskeleti ve Borfin okuma sureci.
- [x] Commit 2: `planlama.md` egitim kaynakli fark yaratan ozellik radar'i.
- [x] Commit 3: Algo Trade + Hareketli Ortalamalar OCR'ina dayali secilmis ozellikler.
- [x] Commit 4: Indikator ve teknik analiz OCR/transkriptlerinden secilmis ozellikler.
- [x] Commit 5a: Fuat Akman Sistem Trading OCR ve yardimci dokumanlara dayali secilmis ozellikler.
- [x] Commit 5b: VİOP/Vadeli egitimlerinin OCR ciktilarindan secilen ozellikler.
- [x] Commit 5c: Yatirimci Psikolojisi OCR ciktisindan secilen davranissal risk ozellikleri.
- [x] Commit 6: Planlama dosyalari yeniden yapilandirildi (planlama.md bolundü, yeni dosyalar olusturuldu).
- [x] Commit 7+: Uygulama gelistirmeleri — Egitimler sekmesi altyapisi.
- [x] Commit 8+: Blog makaleleri — Indikatorler kategori (20 makale).
- [x] Commit 9+: Blog makaleleri — Formasyonlar kategori.
- [ ] Commit 10+: Mali Analiz sekmesi backend + frontend.

## 7. Tamamlanan Kurs Okuma Kayitlari

### Dilim 7 — Kıvanç Özbilgiç (İlk OCR Turu)

Kaynak: `artifacts/borfin_ocr/ocr_report.md`.
Kapsam: 37 video, 2 kurs.
Yontem: macOS Vision frame OCR. Ses transkripti yok.

Gozlem:
- **Algo Trade:** algoritmik trade tanimi, momentum/trend/mean reversion/firsat stratejileri, indikator kullanimi, bilimsel yontem, backtest, optimizasyon, komisyon/slipaj, walk-forward, Monte Carlo, portfoy cesitlendirme, robot kurma ve veri aktarimi.
- **Hareketli Ortalamalar:** HO turleri, period/vade secimi, kesisim/fiyat-HO/HO siralama stratejileri, paylasim mantigi.

### Dilim A — Fuat Akman İndikatörler

Kaynak: `artifacts/borfin_indikator_ocr/ocr_report.md`.
Kapsam: 67 video, 1004 OCR satiri, 3 `.doc` + 1 `.xls` yardimci dosya.
Yontem: macOS Vision frame OCR + yardimci dosya metin cikarimi.

Gozlem: Bollinger, ADX/ADXR, ATR, CCI, CMO, Chaikin/CMF, DEMA, DPO, DI/DX, Heiken Ashi, Ichimoku, MACD, MFI, Momentum, MOST, OBV/OBVx, Parabolic SAR, RSI/RMI, Stochastic ailesi, TRIX, VHF, Volume indikatörleri, Williams, ZigZag ve bant/yön/güç/hacim ayrimlari ekranda goruldu.

### Dilim B — Yaşar Erdinç Teknik Analiz + İleri Düzey

Kaynak: `artifacts/borfin_teknik_analiz_yasar_ocr/ocr_report.md` + `artifacts/borfin_ileri_teknik_analiz_yasar_ocr/ocr_report.md`.
Kapsam: 207 video, 3169 OCR satiri, 92 slaytlik `.pptx`, `ACTIVE_CHARTS_TANITIM.docx`, `tumformuller.doc`, `tradesistemmakro2.xls` + 52 `.mst` sistem dosyasi zip envanteri.
Yontem: macOS Vision frame OCR + yardimci dosya metin cikarimi.

Gozlem: teknik analiz varsayimlari, trend/kanal cizimleri, mum stratejisi, strateji kriterleri, Fibonacci geri donus/fan/zaman/yay/quadrant/hiz direnc, OBO, ucgen/bayrak/elmas/cift tepe-dip/fincan/canak formasyonlari, gap turleri, gostergelerde aykirilik, TKE/gosterge gelistirme, Indicator Builder, System Tester, Explorer, Expert Advisor, optimizasyon parametreleri, sistem sonucu metrikleri goruldu.

### Dilim C — Fuat Akman Sistem Trading

Kaynak: `artifacts/borfin_sistem_trading_fuat_ocr/ocr_report.md` + `artifacts/borfin_sistem_trading_fuat_docs_text/`.
Kapsam: 76 video, 1102 OCR satiri, 19 `.doc` yardimci dosya.
Yontem: macOS Vision frame OCR + yardimci `.doc` metin cikarimi.

Gozlem: Indicator Builder fonksiyon ailesi, `ref`/`cross`/`barssince`/`valuewhen`/`highest`/`lowest`/`security data` seri fonksiyonlari, System Tester AL/SAT/aciga sat/acik pozisyon kapat bolumleri, simulasyon ayarlari, optimizasyon degiskenleri, sonuc raporu, Explorer kolon/filtreleri, Expert Advisor alarm ekranlari ve 18 ornek sistem dosyasi goruldu.

### Dilim D — VOB Yaşar Erdinç + Vadeli Trade Bolgün

Kaynak: `artifacts/borfin_vob_yasar_ocr/ocr_report.md` + `artifacts/borfin_vadeli_trade_bolgun_ocr/ocr_report.md`.
Kapsam: 63 video, 1263 OCR satiri.
Yontem: macOS Vision frame OCR.

Gozlem: VOB30 teminat/pozisyon/kaldirac tablolari, strateji unsurlari, uzun vadeli long/short ve TKE/HO/MACD odakli VOB stratejileri, futures/forward/swap/opsiyon ayrimi, hedge/spekulasyon/arbitraj rolleri, BIST30 kontrat ozellikleri, VIOP endeks/pay kontrat ekranlari, uzlasma/teorik fiyat/acik pozisyon kolonlari, temettu ve ozsermaye hali uyarlamalari goruldu.

### Dilim E — Yatırımcı Psikolojisi

Kaynak: `artifacts/borfin_yatirimci_psikolojisi_ocr/ocr_report.md`.
Kapsam: 19 video, 397 OCR satiri.
Yontem: macOS Vision frame OCR.

Gozlem: etkin pazar hipotezi, davranissal finans, prospect teorisi, cognitive dissonance, yatirimci hatalari, stres altinda karar, on lob/amigdala catismasi, strateji secimi, hedef getiri, vade, stop-loss, satamama, alirken/satarken bakis hatasi ve disiplin konulari goruldu.

## 8. Bekleyen Okuma Dilimleri

### Dilim F — Opsiyon / Varant / Swap-Forward (33 video, Öncelik 2)

- **Durum:** Okunmadı.
- **Yontem:** macOS Vision frame OCR planlanıyor.
- **Hedef:** Bu kursun içerikleri birebir ürüne taşınmayacak. Yalnızca PiyasaPilot'un VIOP backtest varsayımları, risk uyarıları ve eğitim drawer'ı için gerekli kavramlar süzülecek.
- **Beklenen çıktı:**
  - Opsiyon temel kavramları: prim, kullanım fiyatı, vade, delta/gamma/theta uyarıları
  - Varant risk uyarıları (likidite, yayıcı fiyatlaması, son tarih)
  - Swap/Forward: forward fiyat, taşıma maliyeti — vadeli backtest varsayımına giriş
  - Blog makalesi: "Opsiyon ve Varant Nedir? VIOP'tan Farkı"
- **Önce okunacak, sonra seçim yapılacak:**
  - Bu kurs çıktısı `planlama-egitimler.md` Kategori 4 (VIOP & Vadeli) ile birleştirilecek

### Dilim G — Temel Analiz + Mali Analiz Ön Okuma (151 video, Öncelik 1)

- **Durum:** Okunmadı. **Yüksek önceliğe alındı** (Mali Analiz sekmesi için kritik).
- **Yontem:** macOS Vision frame OCR + yardimci dosya taraması.
- **Hedef:** Mali Analiz sekmesi için bilanço, gelir tablosu, finansal oran kavramları ve nasıl okunur bilgisi çıkarılacak.
- **İlk okunacak kurslar:** Cahit Yılmaz Mali Analiz Teknikleri (87), Temel Analiz Dr. Yaşar Erdinç (29), Üzeyir Doğan Temel Analiz ile Hisse Seçimi (15), Fastweb Mali Analiz Pro (16), Firma Değerleme ve Finansal Risk Analizi Platformu'ndan mali analizle ilgili ilk 4 video.
- **Beklenen çıktı:**
  - Bilanço nasıl okunur (varlıklar, yükümlülükler, özsermaye)
  - Gelir tablosu metrikleri (ciro, brüt kar, FAVÖK, net kar, marjlar)
  - Finansal oranlar kategorisi (likidite, karlılık, verimlilik, kaldıraç, değerleme)
  - Temel analiz vs teknik analiz ayrımı
  - Blog makaleleri: "Bilanço Nasıl Okunur?", "Finansal Oranlar Rehberi", "PE Oranı Nedir?"
  - Mali analiz sekmesi içerik yapısı bu dilimden beslenecek
- **Not:** Tüm bekleyen finans/platform kapsamı 323 videodur. Önce 151 videoluk mali analiz çekirdeği okunacak; platform eğitimleri daha sonra sadece ürün ihtiyacı çıkarmak için kullanılacak.

## 9. Genel Notlar ve Uyarılar

- Tüm dilimler için "ses transkripti yok; konuşmada kalıp ekranda görünmeyen detaylar eksik olabilir" uyarısı geçerli.
- Kıvanç Özbilgiç kursları konuşma ağırlıklıdır; OCR güven notu "orta" kabul edilir.
- Matriks/Active Charts formülleri birebir taşınmaz; PiyasaPilot DSL'ine dönüştürülür.
- Her dilim tamamlanınca `planlama-egitimler.md` veya `planlama-backtest.md`'ye ilgili maddeler eklenir.
