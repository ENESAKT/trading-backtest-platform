# Mali Analiz Sekmesi — Plan

> Tarih: 2026-05-03
> Durum: Metadata/API/UI v1 tamam. Gercek KAP/provider baglantisi,
> finansal tablo store'u ve oran motoru icin `genelplanlama.md`,
> `planlama.md` ve ozellikle `planlama-veri-platformu.md` izlenir.
> Hedef: Veri platformu oturduktan sonra BIST sirketleri icin KAP tabanli,
> Fastweb mantigina yakin ama PiyasaPilot'a ozgu mali analiz modulu kurmak.

---

## 1. Kesin Kararlar

Bu kararlar uygulama sirasinda tekrar tartisilmaz; Enes yeni karar verirse
once bu dosya guncellenir.

| Konu | Karar |
|---|---|
| Uygulama sirasi | Once veri platformu, sonra mali analiz |
| Ana veri omurgasi | `planlama-veri-platformu.md`: ClickHouse + MySQL + Redis |
| Ilk mali analiz kapsami | BIST 30 |
| Sonraki kapsam | BIST 100, sonra tum BIST |
| Finansal veri kaynagi | KAP oncelikli |
| Fastweb/Borfin rolu | Ekran kopyasi degil; analiz ihtiyac listesi ve egitim referansi |
| Ham Borfin gorselleri | Urune ve production image'a girmez |
| Ham Borfin metni | Birebir urune girmez |
| Veri gecmisi | Son 10 yil |
| Donem yapisi | Ceyreklik + yillik |
| Statik BIST 30 listesi | Plana gomulmez; merkezi sembol kaynagindan veya provider metadata'dan uretilir |
| Sahte veri | Yasak |
| Tavsiye dili | Al/sat tavsiyesi uretilmez; analiz ve risk uyarisi uretilir |

Mali analiz icin mevcut `backend/mali_analiz` katmani silinmeyecek. Ancak
SQLite/mock odakli v1 iskeleti, yeni veri platformu tamamlandiktan sonra
ClickHouse/MySQL repository yapisina baglanacak.

---

## 0. 2026-05-03 Uygulama Notu

Metadata-only Mali Analiz v1 eklendi. Bu katman kullaniciya bos ama
profesyonel kontratlar sunar; sahte finansal tablo, rasgele oran veya tavsiye
uretmez.

- [x] Sembol normalize davranisi: trim, uppercase, `.IS` temizleme ve bos sembolde `ValueError`
- [x] `MockFinancialAnalysisProvider` sirket adini statik metadata fallback'inden alir
- [x] Warning metni: "Finansal tablo verisi henüz bağlı değil."
- [x] `GET /api/mali-analiz/universe?scope=bist30`
- [x] `GET /api/mali-analiz/{symbol}/reports`
- [x] `GET /api/mali-analiz/{symbol}/events`
- [x] `GET /api/mali-analiz/{symbol}/metric-history`
- [x] Frontend: tabbed Mali Analiz UI, empty state, source status ve universe sidebar
- [ ] Gercek KAP finansal rapor provider'i
- [ ] Finansal tablo normalize store'u
- [ ] Gercek oran ve metrik gecmisi hesaplama

---

## 2. Neden Bekliyor?

Mali analiz tek basina bir ekran degil; dogru calismasi icin gercek finansal
veri omurgasinin netlesmesi gerekir. UI/API kabugu metadata-only olarak hazir,
ancak asagidaki sorular gercek veri fazinin kabul kapisidir.

Gereken temel cevaplar:

- Finansal tablo verisi hangi resmi kaynaktan geldi?
- Hangi donemler eksik?
- Hangi veri KAP raw, hangi veri normalize edilmis?
- Hangi rapor konsolide, hangisi konsolide olmayan?
- Hangi sirket banka/sigorta/sanayi sinifinda?
- 10 yillik veri kapsami her hisse icin yuzde kac?
- Finansal tablo, fiyat ve kurumsal aksiyon verisi ayni sembol metadata'sina mi bagli?
- Backtest, grafik, screener ve mali analiz ayni sembol evrenini mi kullaniyor?

Bu sorularin cevabi `planlama-veri-platformu.md` ile kurulacak veri
platformundan gelecek. Bu yuzden mali analiz koduna gecmeden once VDP fazlari
tamamlanacak.

---

## 3. On Kosullar

### 3.1 Veri Platformu On Kosullari

Mali analiz baslamadan once asagidakiler tamamlanmis sayilmali:

- [ ] ClickHouse, MySQL ve Redis dev compose ayaga kalkar.
- [ ] MySQL `instruments`, `providers`, `ingest_jobs`, `data_inventory`,
  `data_retention_policy` tablolarini alir.
- [ ] ClickHouse OHLCV icin ana kaynak olarak calisir.
- [ ] `/api/v2/candles` repository katmani uzerinden okur.
- [ ] Backtest runner repository katmani uzerinden okur.
- [ ] `make data-inventory` her sembol/timeframe icin rapor uretir.
- [ ] Sahte veri yasagi testlerle korunur.
- [ ] BIST 30/BIST 100 sembol evreni merkezi metadata kaynagindan okunur.

### 3.2 Temizlik ve Production On Kosullari

Mali analiz egitim ve gorsel kaynaklari kullanilacagi icin repo temizligi
kapilari da on kosuldur:

- [ ] `artifacts/` production context disinda kalir.
- [ ] Borfin OCR/frame/video dosyalari runtime bagimliligi olmaz.
- [ ] `borfin-integration-check` ham icerik kopyasi olmadigini raporlar.
- [ ] `.dockerignore` artifact, cache, local DB, `.venv`, `node_modules`
  klasorlerini dislar.
- [ ] `production-package-check` temiz rapor verir.

### 3.3 Egitim On Kosullari

Mali analiz planinin ders tarafinda acele edilmeyecek:

- [ ] Yaşar Erdinç Temel Analiz videolari OCR veya transkript ile okunur.
- [ ] Fastweb Mali Analiz Pro videolari OCR veya transkript ile okunur.
- [ ] Cahit Yilmaz Mali Analiz Teknikleri egitimi en az ana bolumler icin okunur.
- [ ] Uygulamaya alinacak kavramlar PiyasaPilot'a ozgu metne donusturulur.
- [ ] Ham ekran goruntusu, slayt metni ve marka dili urune kopyalanmaz.

---

## 4. Kapsam Fazlari

| Faz | Icerik | Sembol kapsami | Bagimlilik |
|---|---|---:|---|
| M0 | Egitim OCR ve ihtiyac cikarimi | Yok | Repo temizlik kurallari |
| M1 | KAP finansal rapor envanteri | BIST 30 | Veri platformu VDP-3/VDP-4 |
| M2 | Finansal tablo normalize etme | BIST 30 | MySQL metadata |
| M3 | Oran motoru ve 10 yillik seri | BIST 30 | KAP period store |
| M4 | Mali analiz UI v1 | BIST 30 | API kontrati |
| M5 | KAP/haber/bilanco event baglantisi | BIST 30 | Grafik Lab G9 |
| M6 | BIST 100 genisleme | BIST 100 | Inventory raporu |
| M7 | Tum BIST genisleme | Tum BIST | Provider ve lisans durumu |

Ilk calisan ekran BIST 30 ile baslar. Fakat altyapi BIST 100 ve tum BIST'e
genisleyebilecek sekilde tasarlanir.

---

## 5. Veri Kaynaklari

### 5.1 Ana Kaynak Sirasi

| Oncelik | Kaynak | Rol |
|---:|---|---|
| 1 | KAP finansal raporlar | Resmi finansal tablo ve faaliyet raporu kaynagi |
| 2 | KAP sirket genel bilgi formu | Sirket metadata, sektor, finansal ozet |
| 3 | KAP ozel durum aciklamalari | Bilanço, temettu, genel kurul, hak kullanimi, onemli haber |
| 4 | borsa-mcp / borsapy | Yardimci temel veri ve karsilastirma |
| 5 | Manuel CSV/Excel import | Provider yoksa gecici veri aktarimi |

### 5.2 Kaynak Guven Notu

Her finansal veri kaydinda su bilgiler tutulur:

```text
source
source_url
kap_disclosure_id
report_type
period
period_type
is_consolidated
currency
unit
raw_payload_hash
normalized_at
quality_status
```

`quality_status` izin verilen degerler:

```text
ok
partial
missing_period
parse_failed
provider_failed
manual_import
needs_review
restated
```

---

## 6. Veri Modeli Hedefi

Mali analiz verisi OHLCV gibi tek buyuk bar tablosuna yazilmaz. Finansal veri
iliskisel ve donemsel oldugu icin ana operasyonel kaynak MySQL olur; zaman
serisi ve karsilastirma snapshot'lari gerekiyorsa ClickHouse'a kopyalanabilir.

### 6.1 MySQL Tablolari

```text
financial_reports
- id
- symbol
- kap_disclosure_id
- report_type
- period
- period_type
- fiscal_year
- fiscal_quarter
- is_consolidated
- currency
- unit
- source_url
- published_at
- received_at
- status
- notes
```

```text
financial_statement_items
- id
- report_id
- symbol
- statement_type
- item_code
- item_label
- item_group
- period
- value
- currency
- unit
- is_derived
- source
```

```text
financial_ratios
- id
- symbol
- period
- period_type
- ratio_key
- ratio_label
- ratio_group
- value
- format
- formula_version
- quality_status
```

```text
financial_kap_events
- id
- symbol
- kap_disclosure_id
- event_type
- title
- published_at
- source_url
- summary
- linked_report_id
```

```text
financial_education_refs
- id
- topic_key
- title
- source_course
- source_method
- confidence
- notes
- artifact_path
- runtime_visible
```

### 6.2 ClickHouse Snapshotlari

ClickHouse ana finansal tablo kaynagi olmak zorunda degildir. Ancak screener ve
uzun donem karsilastirma icin su snapshot mantigi kullanilabilir:

```text
financial_metric_series
- symbol
- metric_key
- period
- period_type
- value
- quality_status
- source
- normalized_at
```

Bu tablo yalnizca hizli filtreleme ve grafik icindir. Resmi detay MySQL ve KAP
referansi uzerinden izlenir.

---

## 7. API Kontrati

Mevcut endpoint korunur ama yeni veri omurgasina gore genisletilir.

### 7.1 Endpointler

```text
GET /api/mali-analiz/universe?scope=bist30
  -> BIST 30 sirket listesi, sektor, son veri durumu, son rapor tarihi

GET /api/mali-analiz/{symbol}?years=10&period=quarterly
  -> Sirket ozeti, finansal tablolar, oranlar, grafik serileri, kaynak durumu

GET /api/mali-analiz/{symbol}/reports
  -> KAP finansal rapor listesi

GET /api/mali-analiz/{symbol}/events
  -> KAP haberleri, bilanco aciklamalari, temettu ve hak kullanimi olaylari

GET /api/mali-analiz/{symbol}/metric-history?metric=net_income&period=quarterly
  -> Tek metrik icin 10 yillik seri

GET /api/mali-analiz/education
  -> Mali analiz egitim referanslari ve PiyasaPilot'a ozgu aciklamalar
```

### 7.2 Response Metadata

Her response su kaynak durumunu tasir:

```json
{
  "source": "kap",
  "status": "ok",
  "coverage_pct": 96.4,
  "first_period": "2016-Q1",
  "last_period": "2026-Q1",
  "period_count": 41,
  "missing_periods": [],
  "cache_hit": false,
  "stale": false,
  "warnings": []
}
```

### 7.3 Hata Davranisi

- Provider hatasi UI'yi dusurmez.
- Cache varsa stale olarak doner.
- Eksik donemler `missing_periods` icinde gosterilir.
- KAP raporu parse edilemezse veri uydurulmaz.
- HTTP 200 icinde `partial` durum donulebilir; altyapi hatasi ayrica 5xx olur.

---

## 8. Analiz Icerigi

### 8.1 Sirket Ozeti

- Sirket adi
- Sembol
- Sektor
- Pazar
- Son fiyat
- Piyasa degeri
- Son finansal rapor tarihi
- Son KAP bildirimi
- Finansal veri kapsami
- Konsolide/konsolide olmayan uyarisi

### 8.2 Finansal Tablolar

| Sekme | Ana kalemler |
|---|---|
| Bilanco | Donen varlik, duran varlik, toplam varlik, kisa vadeli yukumluluk, uzun vadeli yukumluluk, ozkaynak |
| Gelir tablosu | Hasilat, brüt kar, faaliyet kari, FAVOK, vergi oncesi kar, net kar |
| Nakit akis | Operasyonel nakit akisi, yatirim nakit akisi, finansman nakit akisi, serbest nakit akisi |
| Ozkaynak degisim | Sermaye, kar yedekleri, gecmis yil kar/zarar, donem kari |

### 8.3 Oran Gruplari

| Kategori | Oranlar |
|---|---|
| Likidite | Cari oran, asit-test, nakit oran |
| Faaliyet etkinligi | Alacak devir, stok devir, borc devir, aktif devir |
| Karlilik | Brüt marj, faaliyet marji, FAVOK marji, net marj, ROA, ROE |
| Mali yapi | Borc/ozkaynak, net borc, net borc/FAVOK, faiz karsilama |
| Buyume | Hasilat buyumesi, brüt kar buyumesi, net kar buyumesi, ozkaynak buyumesi |
| Degerleme | F/K, PD/DD, FD/FAVOK, FD/Satislar, temettu verimi |
| DuPont | Net marj, aktif devir, finansal kaldirac, ROE kirilimi |

### 8.4 Grafikler

- 10 yillik hasilat trendi
- 10 yillik net kar trendi
- Brüt/net/FAVOK marj grafigi
- Cari oran ve borc/ozkaynak grafigi
- ROE/ROA grafigi
- DuPont kirilim grafigi
- Temettu performans grafigi
- Piyasa carpanlari tarihsel bant grafigi

Grafikler uygulamanin kendi verisinden uretilir. Fastweb veya Borfin ekran
goruntusu birebir grafik olarak kullanilmaz.

---

## 9. Frontend Mimari

### 9.1 Ana Panel

`piyasapilot-v2/src/components/MaliAnalizPanel.ts` mevcut iskelet korunur ama
moduler hale getirilir.

Hedef dosya yapisi:

```text
piyasapilot-v2/src/components/mali-analiz/
  HisseListesi.ts
  SirketOzet.ts
  DonemSecici.ts
  FinansalTablo.ts
  OranTablosu.ts
  MetrikGrafik.ts
  DupontPanel.ts
  KapBildirimleri.ts
  EgitimReferanslari.ts
```

### 9.2 Layout

```text
┌────────────────────────────────────────────────────────────┐
│ Mali Analiz  [BIST30] [Ara: THYAO] [Ceyrek/Yillik] [10Y]   │
├───────────────┬────────────────────────────────────────────┤
│ BIST30 Liste  │ THYAO - Turk Hava Yollari                  │
│ AKBNK         │ Veri kapsami: 2016-Q1 -> 2026-Q1           │
│ ASELS         │ Son KAP raporu: ...                        │
│ BIMAS         │                                            │
│ THYAO ◄       │ [Ozet][Bilanco][Gelir][Nakit][Oran][KAP]   │
│ ...           │                                            │
│               │ 10 yillik grafikler + tablo + uyarilar     │
└───────────────┴────────────────────────────────────────────┘
```

### 9.3 Kopru Aksiyonlari

- "Grafikte Ac" ChartPanel'i ilgili sembole gecirir.
- "KAP Olaylarini Goster" grafik event marker katmanina baglanir.
- "Egitimde Ara" Egitimler panelinde ilgili kavrami acar.
- "Backtest'e Ekle" sadece sembol secimi yapar; mali analizden otomatik sinyal
  uretilmez.

---

## 10. Egitim ve Borfin Uygunlugu

### 10.1 Kullanilacak Egitim Kumesi

Oncelikli klasorler:

```text
/Users/enes/Documents/Ders videoları/BORFİN/TEMEL ANALİZ DR. YAŞAR ERDİNÇ
/Users/enes/Documents/Ders videoları/BORFİN/Fastweb Mali Analiz Pro Eğitimi
/Users/enes/Documents/Ders videoları/BORFİN/CAHİT YILMAZ Mali Analiz Teknikleri Eğitimi
```

### 10.2 Uygulamaya Girebilir

- PiyasaPilot'a ozgu anlatim.
- Kavram ozeti.
- Analiz checklist'i.
- Kaynak guven notu.
- Uygulama tarafindan yeniden uretilmis grafik.
- Telifsiz ve ozgun UI metni.

### 10.3 Uygulamaya Giremez

- Borfin ekran goruntusu.
- Fastweb/Finnet platform ekraninin birebir kopyasi.
- Video frame.
- Slayt metni.
- Birebir formül/metin.
- Marka dili.
- Ham OCR raporu.

### 10.4 Artifact Kurali

OCR ve frame ciktilari yalnizca lokal arastirma kaniti olarak tutulur.
Production paketine girmez. Bir artifact klasoru temizlenmeden once
`borfin-integration-check` raporu uretilir.

---

## 11. Backend Uygulama Sirası

### M0 — Bekleme ve Plan Kilidi

- [ ] Bu dosya `genelplanlama.md` ve `planlama.md` ile uyumlu tutulur.
- [ ] Mali analiz "veri platformu sonrasi" olarak isaretlenir.
- [ ] Eski SQLite-only plan kararlarindan vazgecildigi not edilir.

### M1 — Finansal Veri Repository Tasarimi

- [ ] `backend/mali_analiz` mevcut modelleri incelenir.
- [ ] MySQL finansal tablo repository interface'i tasarlanir.
- [ ] KAP provider interface'i tasarlanir.
- [ ] Legacy mock provider sadece test icin kalir.

### M2 — KAP Rapor Envanteri

- [ ] BIST 30 sirketleri icin son 10 yil KAP raporlari listelenir.
- [ ] Raporlar `financial_reports` tablosuna yazilir.
- [ ] Eksik raporlar `quality_status=missing_period` veya `parse_failed`
  olarak raporlanir.

### M3 — Finansal Tablo Normalize Etme

- [ ] Bilanco, gelir tablosu ve nakit akis kalemleri ortak item key'lere
  normalize edilir.
- [ ] Banka/sigorta/sanayi tablo farklari ayrilir.
- [ ] Konsolide ve konsolide olmayan veri karistirilmaz.
- [ ] Enflasyon muhasebesi ve yeniden duzenlenmis veri uyarilari tasinir.

### M4 — Oran Motoru

- [ ] Likidite, faaliyet, karlilik, mali yapi, buyume, degerleme ve DuPont
  oranlari hesaplanir.
- [ ] Eksik kalemlerde oran uydurulmaz.
- [ ] Formul versiyonu response ve DB kaydinda tutulur.

### M5 — API Genisletme

- [ ] `GET /api/mali-analiz/universe` eklenir.
- [ ] `GET /api/mali-analiz/{symbol}` 10 yillik response'a genisler.
- [ ] `GET /api/mali-analiz/{symbol}/reports` eklenir.
- [ ] `GET /api/mali-analiz/{symbol}/events` eklenir.
- [ ] `GET /api/mali-analiz/{symbol}/metric-history` eklenir.

---

## 12. Frontend Uygulama Sirası

### MF1 — Panel Iskeleti

- [ ] Mevcut `MaliAnalizPanel.ts` korunarak sol liste + sag detay yapisina
  gecilir.
- [ ] BIST30 universe endpoint'inden gelir.
- [ ] Arama ve sembol secimi mevcut app event yapisini bozmaz.

### MF2 — Finansal Tablo Ekrani

- [ ] Donem secici: ceyreklik/yillik.
- [ ] Yil araligi: varsayilan 10 yil.
- [ ] Tablo kolonlari mobil ve desktop'ta tasmayacak sekilde tasarlanir.

### MF3 — Oran ve Grafik Ekrani

- [ ] Oranlar kategori bazli gorunur.
- [ ] Secilen metrik icin 10 yillik grafik cizilir.
- [ ] Eksik veri ve partial durumlari UI'da gorunur.

### MF4 — KAP ve Egitim Baglantilari

- [ ] KAP raporlari ve haberleri ayri sekmede listelenir.
- [ ] Egitim referanslari ham Borfin gorseli olmadan gosterilir.
- [ ] Grafik event marker baglantisi G9 tamamlaninca aktif edilir.

---

## 13. Test ve Kabul Kriterleri

### Unit Testler

- [ ] KAP provider bos veri donunce kontrollu `partial` response olusur.
- [ ] Finansal tablo item normalize fonksiyonu bilanco/gelir/nakit akis
  kalemlerini dogru ayirir.
- [ ] Oran motoru sifira bolme yapmaz.
- [ ] Eksik kalemlerde oran uydurmaz.
- [ ] Konsolide/konsolide olmayan donemler karistirilmaz.
- [ ] Banka ve sanayi sirketleri ayni oran setine zorlanmaz.

### Integration Testler

- [ ] BIST30 universe endpoint'i 30 sirket ve veri durumu dondurur.
- [ ] `GET /api/mali-analiz/THYAO?years=10&period=quarterly` schema olarak
  eksiksiz doner.
- [ ] Provider hatasinda stale cache veya partial status UI'yi bozmaz.
- [ ] KAP rapor listesi finansal rapor ve ozel durum aciklamasini ayirir.
- [ ] ClickHouse/MySQL/legacy fallback veri platformu testleri yesil kalir.

### Frontend Testler

- [ ] Mali Analiz sekmesi acilir.
- [ ] BIST30 listesi gorunur.
- [ ] THYAO secilince ozet, tablo ve oranlar gorunur.
- [ ] Donem secici ceyreklik/yillik arasinda gecis yapar.
- [ ] Eksik veri uyarisi profesyonel sekilde gorunur.
- [ ] "Grafikte Ac" ChartPanel'i ilgili sembole gecirir.

---

## 14. Kabul Kapilari

Mali analiz sprintine baslamak icin:

- [ ] Veri platformu VDP-0 -> VDP-4 tamam.
- [ ] Repository katmani `/api/v2/candles` ve backtest icin calisiyor.
- [ ] Data inventory raporu var.
- [ ] Repo temizlik raporu artifact ve local DB risklerini gosteriyor.
- [ ] Borfin entegrasyon denetimi ham icerik kopyasi olmadigini dogruluyor.

Mali analiz v1 tamam sayilmak icin:

- [ ] BIST30 icin 10 yillik donemsel veri kapsami raporlanir.
- [ ] En az bilanco, gelir tablosu, nakit akis ve ana oranlar gorunur.
- [ ] Eksik veya parse edilemeyen veri acikca belirtilir.
- [ ] KAP rapor linki veya kaynak referansi response icinde vardir.
- [ ] UI mevcut grafik, backtest, egitim ve sinyal sekmelerini bozmaz.

---

## 15. Kapsam Disi

V1'de olmayacaklar:

- Otomatik al/sat tavsiyesi.
- Hedef fiyat tavsiyesi.
- Araci kurum raporu veya tahmin konsensusu.
- Yabanci hisse finansallari.
- Tum BIST otomatik tarama.
- Fastweb ekraninin birebir kopyasi.
- Borfin ders gorsellerinin production asset olarak kullanimi.

Sonraki fazlara kalacaklar:

- Sektor ortalamasi ve peer comparison.
- Degerleme senaryo motoru.
- Fiyat tahmini simülasyonu.
- Portfoy icinde temel analiz skoru.
- KAP event marker ile fiyat etkisi analizi.

---

## 16. Asla Yapilmamasi Gerekenler

- Veri platformu tamamlanmadan mali analiz kodunu buyutmek.
- KAP raporu parse edilemedi diye veri uydurmak.
- Gunluk finansal veriden ceyreklik veri uretmis gibi davranmak.
- Borfin/Fastweb ekran goruntusunu urune koymak.
- Ham OCR raporunu kullaniciya ders icerigi diye sunmak.
- Statik BIST30 listesini plana veya koda kalici dogruluk kaynagi gibi gommek.
- MySQL'i buyuk OHLCV zaman serisi deposu gibi kullanmak.
- Redis'e tarihsel finansal veri yazmak.
- Al/sat tavsiyesi dili kullanmak.
