# Mali Analiz Sekmesi — Plan

> Durum: Taslak. Kodlama başlamadan önce BORFİN temel/mali analiz eğitimleri okunacak.
> Bağlı eğitim: BORFİN Temel Analiz + Mali Analiz + Platform eğitimleri (17 bekleyen kurs içinden öncelikli alt küme).
> Tarih: 2026-05-01

---

## 1. Hedef

Kullanıcı bir BIST hissesi seçince; bilanço, gelir tablosu, nakit akış tablosu ve finansal oranlar tek sayfada FastWeb tarzı görünsün. İleride haber/KAP ve grafik köprüsüyle birleşecek.

---

## 2. Kapsam (Faz Sırası)

| Faz | İçerik | Sembol Sayısı |
|-----|--------|---------------|
| M-Faz 1 | BIST 30 | 30 |
| M-Faz 2 | BIST 100 | 100 |
| M-Faz 3 | Tüm BIST | ~500+ |

---

## 3. Sembol Evreni Kararı

Statik BIST 30 listesi bu plandan çıkarıldı. İlk sürümde semboller uygulamadaki merkezi sembol kaynağından veya sağlayıcıdan alınacak; elle yazılmış liste kullanılmayacak. Böylece endeks değişimleri ve eski semboller plana gömülmez.

---

## 4. Her Hisse Sayfası İçeriği

### 4.1 Özet Kart (üst)
- Şirket adı, sektör, piyasa değeri
- Son fiyat, günlük değişim
- PE oranı, PD/DD, temettü verimi
- Piyasa değeri / defter değeri

### 4.2 Bilanço Sekmesi
- Son 4 çeyrek veya son 4 yıl (toggle)
- Varlıklar: dönen + duran
- Yükümlülükler: kısa vade + uzun vade
- Özsermaye
- Net borç / FAVÖK

### 4.3 Gelir Tablosu Sekmesi
- Net satışlar (ciro)
- Brüt kar ve brüt marj %
- FAVÖK ve FAVÖK marjı %
- Net kar ve net kar marjı %
- Hisse başına kazanç (HBK)

### 4.4 Nakit Akış Sekmesi
- Operasyonel nakit akışı
- Yatırım nakit akışı
- Finansman nakit akışı
- Serbest nakit akışı

### 4.5 Finansal Oranlar Sekmesi

| Kategori | Oranlar |
|----------|---------|
| Likidite | Cari oran, asit-test, nakit oranı |
| Karlılık | ROE, ROA, ROIC, brüt/net marj |
| Verimlilik | Varlık devir, alacak devir, stok devir |
| Kaldıraç | Borç/özsermaye, net borç/FAVÖK, faiz karşılama |
| Değerleme | PE, PD/DD, FD/FAVÖK, FD/Satışlar |

### 4.6 Dönemsel Karşılaştırma
- Seçilen oran için son 8 çeyrek bar grafik
- Sektör ortalamasıyla karşılaştırma (borsa-mcp'den)

### 4.7 Köprü Aksiyonları
- "Grafikte Aç" → ChartPanel'i bu hisse ile açar
- "Eğitimde Ara" → EgitimlerPanel'de "bilanço nasıl okunur" arar
- "Backtest'e Ekle" → StrategyPanel'e bu sembolü gönderir

---

## 5. Backend Mimari

### 5.1 Yeni Endpoint
```
GET /api/mali-analiz/{symbol}
  → borsa-mcp get_financial_statements + get_financial_ratios
  → SQLite cache kontrolü (günlük TTL)
  → JSON yanıt

GET /api/mali-analiz/{symbol}/history?metric=net_kar&periods=8
  → Seçili metriğin dönemsel serisi

GET /api/mali-analiz/list
  → BIST 30 / BIST 100 hisse özet listesi (fiyat + 3 temel oran)
```

### 5.2 Cache Stratejisi
- SQLite tablosu: `mali_analiz_cache`
- Alanlar: `symbol`, `period`, `data_json`, `fetched_at`
- TTL: 24 saat (piyasa kapanışı sonrası güncelleme yeterli)
- Borsa-mcp çağrısı başarısız olursa son cache dönülür, UI "X saat önce güncellendi" gösterir

### 5.3 Veri Kaynakları (Öncelik Sırası)
1. `mcp__borsa__get_financial_statements` — bilanço + gelir tablosu
2. `mcp__borsa__get_financial_ratios` — hazır oranlar
3. `mcp__borsa__get_profile` — şirket bilgileri, sektör
4. `mcp__borsa__get_earnings` — çeyreklik kazanç geçmişi

---

## 6. Frontend Mimari

### 6.1 Yeni Dosyalar
```
piyasapilot-v2/src/components/MaliAnalizPanel.ts   ← ana panel
piyasapilot-v2/src/components/mali-analiz/
  ├── HisseListesi.ts    ← BIST 30/100 liste
  ├── OzetKart.ts        ← özet metrikler
  ├── TabloGorsel.ts     ← bilanço/gelir tablo render
  └── OranGrafik.ts      ← dönemsel bar chart
```

### 6.2 app.ts Değişimi (minimal)
```typescript
// Sadece bu satırlar eklenir:
case '7': this.showPanel('mali-analiz'); break;
// MaliAnalizPanel instance eklenir
```

### 6.3 Layout
```
┌─────────────────────────────────────────────────────┐
│  [Ara: THYAO...]     BIST 30 ▼   BIST 100 ▼         │
├──────────────┬──────────────────────────────────────┤
│  AKBNK       │  THYAO — Türk Hava Yolları            │
│  ASELS       │  ┌──────────────────────────────────┐ │
│  BIMAS  ◄    │  │ 346.50 TL  +1.2%  PE: 8.2       │ │
│  DOHOL       │  │ PD/DD: 1.4  Temettü: %3.1        │ │
│  ...         │  └──────────────────────────────────┘ │
│              │  [Bilanço][Gelir][Nakit][Oranlar]      │
│              │  ┌──────────────────────────────────┐ │
│              │  │  2022  2023  2024  2025           │ │
│              │  │  Net Kar: ...                    │ │
│              │  └──────────────────────────────────┘ │
│              │  [Grafikte Aç] [Backtest'e Ekle]       │
└──────────────┴──────────────────────────────────────┘
```

---

## 7. Test ve Kabul Kriterleri

- [ ] Unit: `/api/mali-analiz/THYAO` borsa-mcp verisini doğru parse eder
- [ ] Unit: Cache TTL çalışır; 24 saatten eski veri yenilenir
- [ ] Unit: borsa-mcp çağrısı başarısız olursa son cache dönülür, hata fırlatmaz
- [ ] Integration: BIST 30 hisselerinin tamamı için endpoint başarılı döner
- [ ] E2E: Mali Analiz sekmesi açılır, THYAO seçilir, bilanço görünür
- [ ] E2E: "Grafikte Aç" tıklanınca ChartPanel THYAO'ya geçer
- [ ] E2E: Sekmeler arası geçiş mevcut grafik/backtest durumunu bozmaz

---

## 8. Uygulama Sırası (Adım Adım)

- [ ] M1: `mali_analiz.py` backend modülü — borsa-mcp wrapper + cache
- [ ] M2: `GET /api/mali-analiz/{symbol}` endpoint + Pydantic model
- [ ] M3: SQLite `mali_analiz_cache` tablosu + TTL kontrolü
- [ ] M4: `MaliAnalizPanel.ts` iskelet — hisse listesi + sekme yapısı
- [ ] M5: Özet kart (fiyat + 4 oran)
- [ ] M6: Bilanço tablosu (4 dönem, TL)
- [ ] M7: Gelir tablosu (4 dönem, marj %)
- [ ] M8: Finansal oranlar tablosu
- [ ] M9: Dönemsel bar chart (seçili oran)
- [ ] M10: "Grafikte Aç" + "Backtest'e Ekle" köprüleri
- [ ] M11: `app.ts`'e Mali Analiz sekmesi (`7` klavye kısayolu)
- [ ] M12: BIST 100'e genişleme
- [ ] M13: Sektör karşılaştırması

---

## 9. Kapsam Dışı (v1'de Yok)

- Nakit akış tablosu analizi (v2'de)
- Şirket haberleri entegrasyonu (bkz. `planlama-grafik.md` G9)
- Tahmin/beklenti vs gerçek karşılaştırması
- Yabancı hisseler
- Otomatik alım-satım önerisi
