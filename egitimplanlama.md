# Egitim Planlama ve Borfin Okuma Sureci

> Bu dosya egitim arsivini okuma, kanit toplama ve urun fikrine donusturme
> surecini yonetir. Urune girecek secilmis backlog maddeleri `planlama.md`
> icinde tutulur.

## 1. Kaynak ve Ilke

- Ana kaynak klasor: `/Users/enes/Documents/Ders videoları/BORFİN`
- Bulunan kapsam: 26 egitim klasoru, 825 video.
- Mevcut derin OCR kapsami: `KIVANÇ ÖZBİLGİÇ  Algo Trade` ve `KIVANÇ ÖZBİLGİÇ Hareketli Ortalamalarla Algo Trade`; toplam 37 video.
- Mevcut ham rapor: `artifacts/borfin_ocr/ocr_report.md`.
- Kural: Video icerigi dosya adindan tahmin edilmeyecek; ses transkripti, kare OCR'i veya manuel kare incelemesiyle dogrulanacak.
- Kural: Borfin, Matriks, TradingView, Active Charts ya da egitimlerdeki metin/formul/dosya icerikleri birebir kopyalanmayacak; PiyasaPilot'a ozgu ozgun urun fikrine donusturulecek.

## 2. Arac Durumu

- `swiftc`: var; macOS AVFoundation/Vision OCR hatti calistirilabilir.
- `ffmpeg` / `ffprobe`: bulunamadi.
- `whisper` / `faster_whisper`: Python ortaminda bulunamadi.
- Varsayilan yontem: once mevcut OCR raporlarini kullan, yeni kurslarda macOS frame OCR ile basla, ses agirlikli videolar icin yerel transkripsiyon bagimliligi eklenene kadar "konusma icerigi eksik olabilir" notu dus.

## 3. Kurs Envanteri ve Oncelik

| Kurs | Video | Oncelik | PiyasaPilot baglantisi |
|---|---:|---:|---|
| İleri Düzey Teknik Analiz Eğitimi DR. YAŞAR ERDİNÇ | 133 | 1 | Teknik analiz lab, formasyon, trend, sistem fikri |
| FUAT AKMAN Sistem Trading ve Araçları Eğitimi | 76 | 1 | Kural kurucu, system tester, rapor okuma, explorer mantigi |
| TEKNİK ANALİZ DR. YAŞAR ERDİNÇ | 74 | 1 | Baslangic teknik analiz, grafik okuma, uygulama akisi |
| İndikatörlerin Seçimi ve Kullanımı FUAT AKMAN | 67 | 1 | Indikator merkezi, kategori, parametre, sinyal riski |
| VOB DR. YAŞAR ERDİNÇ | 49 | 1 | VIOP/VOB, vadeli backtest varsayimlari |
| KIVANÇ ÖZBİLGİÇ  Algo Trade | 22 | 1 | Strateji lifecycle, backtest, optimizasyon, WFA, Monte Carlo |
| KIVANÇ ÖZBİLGİÇ Hareketli Ortalamalarla Algo Trade | 15 | 1 | Hareketli ortalama stratejileri, period/vade uyumu |
| Vadeli Trade Öğreniyorum DOÇ.DR. EVREN BOLGÜN | 14 | 2 | VIOP/vadeli urun bilgisi, risk varsayimlari |
| Opsiyon / Varant / Swap-Forward egitimleri | 33 | 2 | Turev urun uyarilari, kapsam disi/gelecek moduller |
| Yatırımcı Psikolojisi ve Beynin Zaaflarını Yenmek | 19 | 2 | Disiplin, stop, postmortem, davranissal risk |
| Temel analiz, mali analiz, platform egitimleri | 318 | 3 | Hisse secimi, finansal analiz, ileri donem veri modeli |

## 4. Urune Deger Filtresi

Her video veya konu su sorularla degerlendirilir:

- PiyasaPilot'un ana konusu olan grafik, teknik analiz, backtest, strateji, risk veya paper trading akisini guclendiriyor mu?
- Kullanici icin fark yaratan bir is akisi uretiyor mu, yoksa sadece bilgi notu mu?
- Test edilebilir mi: unit, integration, E2E veya kabul senaryosu yazilabilir mi?
- Veri kalitesi, repaint, overfit, slippage, VIOP vade/kontrat gibi riskleri daha gorunur kiliyor mu?
- Mevcut mimariye uyuyor mu: StrategySpec, indikator merkezi, grafik paneli, backtest raporu, paper robot veya tarayiciya baglanabiliyor mu?

Sadece bu filtreden gecen maddeler `planlama.md` icine urun backlog'u olarak tasinir.

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

## 6. Checkpoint ve GitHub Akisi

- Branch: `codex/education-feature-planning`.
- Commit 1: `egitimplanlama.md` iskeleti ve Borfin okuma sureci.
- Commit 2: `planlama.md` egitim kaynakli fark yaratan ozellik radar'i.
- Commit 3: Algo Trade + Hareketli Ortalamalar OCR'ina dayali secilmis ozellikler.
- Commit 4: Indikator ve teknik analiz OCR/transkriptlerinden secilmis ozellikler.
- Commit 5: VIOP/Vadeli ve Sistem Trading OCR/transkriptlerinden secilmis ozellikler.
- Her commit path bazli veya hunk bazli stage edilecek; mevcut kullanici degisiklikleri ezilmeyecek.
- Her commit sonrasi `git push` yapilacak; geri donus icin commit gecmisi kucuk tutulacak.

## 7. Ilk Derin Okuma Durumu

Kaynak: `artifacts/borfin_ocr/ocr_report.md`.

Okunan kurslar:

- `KIVANÇ ÖZBİLGİÇ  Algo Trade`: algoritmik trade tanimi, sistem olusturma, momentum/trend/mean reversion/firsat stratejileri, indikator kullanimi, bilimsel yontem, backtest, optimizasyon, komisyon/slipaj, walk-forward, Monte Carlo, portfoy cesitlendirme, robot kurma ve veri aktarimi.
- `KIVANÇ ÖZBİLGİÇ Hareketli Ortalamalarla Algo Trade`: hareketli ortalama turleri, period/vade secimi, kesişim/fiyat-HO/HO siralama stratejileri, Matriks ve TradingView paylasim mantigi.

Bu iki kursun urun backlog'u `planlama.md` icinde Borfin master planina ek olarak "egitim kaynakli fark radar'i" altinda secilmis ozelliklere donusturulecek.

## 8. Siradaki Okuma Dilimleri

- Dilim A: `İndikatörlerin Seçimi ve Kullanımı FUAT AKMAN`
  - Durum: ilk OCR turu tamamlandi.
  - Kayit: `artifacts/borfin_indikator_ocr/ocr_report.md`.
  - Kapsam: 67 video, 1004 OCR satiri, icerige ek olarak 3 `.doc` ve 1 `.xls` yardimci dosyasi incelendi.
  - Yontem: macOS Vision frame OCR + yardimci dosya metin cikarimi. Ses transkripti yok; konusmada kalip ekranda gorunmeyen detaylar eksik olabilir.
  - Gozlem: Bollinger, ADX/ADXR, ATR, CCI, CMO, Chaikin/CMF, DEMA, DPO, DI/DX, Heiken Ashi, Ichimoku, MACD, MFI, Momentum, MOST, OBV/OBVx, Parabolic SAR, RSI/RMI, Stochastic ailesi, TRIX, VHF, Volume indikatörleri, Williams, ZigZag ve bant/yön/güç/hacim ayrimlari ekranda goruldu.
  - Urune donusen ana fikir: indikator katalogu kategori, parametre, grafik yerlesimi, risk uyarisi ve stratejiye cevir aksiyonlariyla tasarlanacak.
- Dilim B: `TEKNİK ANALİZ DR. YAŞAR ERDİNÇ` ve `İleri Düzey Teknik Analiz Eğitimi DR. YAŞAR ERDİNÇ`
  - Durum: temel teknik analiz kursu icin ilk OCR turu tamamlandi; ileri duzey teknik analiz bekliyor.
  - Kayit: `artifacts/borfin_teknik_analiz_yasar_ocr/ocr_report.md`.
  - Kapsam: 74 video, 1613 OCR satiri, 92 slaytlik `.pptx` yardimci sunum ve `ACTIVE_CHARTS_TANITIM.docx` incelendi.
  - Yontem: macOS Vision frame OCR + yardimci dosya metin cikarimi. Ses transkripti yok; konusmada kalip ekranda gorunmeyen detaylar eksik olabilir.
  - Gozlem: teknik analiz varsayimlari, trend/kanal cizimleri, mum stratejisi, strateji kriterleri, Fibonacci geri donus/fan/zaman/yay/quadrant/hiz direnc, OBO, ucgen/bayrak/elmas/cift tepe-dip/fincan/canak formasyonlari, gap turleri, gostergelerde aykirilik, TKE/gosterge gelistirme ve strateji uygulama dosyasi ekranda goruldu.
  - Urune donusen ana fikir: teknik analiz cizimleri, formasyonlari ve disiplin/journal akisi alarm, StrategySpec taslagi, backtest ve paper takip akislariyla birlestirilecek.
- Dilim C: `FUAT AKMAN Sistem Trading ve Araçları Eğitimi`
  - Cikti: sistem tester mantigi, formulle kural kurma, explorer, rapor okuma ve debug paneli.
- Dilim D: `VOB DR. YAŞAR ERDİNÇ` ve `Vadeli Trade Öğreniyorum`
  - Cikti: VIOP/vadeli backtest varsayimlari, kontrat/vade/teminat/slippage/rollover kontrol listesi.
- Dilim E: yatırım psikolojisi
  - Cikti: strateji disiplini, stop/postmortem, paper robot davranissal risk uyarilari.
