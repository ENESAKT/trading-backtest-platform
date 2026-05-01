# Eğitimler Sekmesi — Plan

> Durum: Eğitimler sekmesi altyapısı ve E-Faz 2A ilk 10 indikatör makalesi tamamlandı.
> Kaynak: BORFİN eğitim arşivi (26 kurs, 825 video; 9 kurs/469 video OCR ile incelendi, 17 kurs/356 video bekliyor).
> Tarih: 2026-05-01

---

## 1. Hedef

PiyasaPilot içinde "Eğitimler" sekmesi: BORFİN video arşivinden çıkarılan kavramlar, PiyasaPilot'a özgü blog makaleleri olarak yayınlanır. Her makale grafiğe, backtest preset'ine veya strateji labına doğrudan köprü içerir.

Kural: Eğitim videoları referans alınır; eğitimlerdeki formüller, ekranlar, marka dili birebir kopyalanmaz. Makaleler PiyasaPilot'a özgün iş akışını anlatır.

---

## 2. Sekme Mimarisi

```
Eğitimler Sekmesi (klavye: 6)
├── Sol Panel
│   ├── Arama barı
│   └── Kategoriler
│       ├── İndikatörler       (20 makale)
│       ├── Formasyonlar       (12 makale)
│       ├── Sistem & Backtest  (10 makale)
│       ├── VIOP & Vadeli       (8 makale)
│       └── Psikoloji & Disiplin (7 makale)
└── Sağ Panel
    ├── Makale içeriği (markdown render)
    └── Alt: Köprü aksiyonları
```

---

## 3. Teknik Mimari

### 3.1 Yeni Dosyalar
```
piyasapilot-v2/src/content/egitimler/
  ├── indikatorler/
  │   ├── bollinger-bandi.md
  │   ├── rsi.md
  │   └── ...
  ├── formasyonlar/
  ├── sistem-backtest/
  ├── viop-vadeli/
  └── psikoloji-disiplin/

piyasapilot-v2/src/components/EgitimlerPanel.ts    ← ana panel
piyasapilot-v2/src/components/egitimler/
  ├── KategoriSidebar.ts
  ├── MakaleGorsel.ts
  └── KopruAksiyonlari.ts
```

### 3.2 Markdown Frontmatter Yapısı
Her makalede zorunlu alanlar:
```yaml
---
title: Bollinger Bandı
slug: bollinger-bandi
category: indikatorler
tags: [volatilite, bant, BB, mean-reversion]
difficulty: başlangıç        # başlangıç | orta | ileri
indicator_key: BB            # ChartPanel indikatör ID'si (köprü için)
related_strategies:          # StrategyPanel preset ID'leri
  - bollinger_bounce
  - bollinger_breakout
source_courses:              # kaynak BORFİN kurslar
  - fuat_akman_indikator
  - yasar_erdinc_teknik
source_method: frame_ocr     # frame_ocr | transcript | manual_review | external_verification
source_confidence: high      # high | medium | low
needs_audio_transcript: true # konuşma ağırlıklı kurslarda true
risk_warnings:               # öne çıkarılacak uyarılar
  - repaint_riski
  - gecikme
copy_policy: original_piyasapilot_content
---
```

### 3.3 İçerik Güvenliği

- Borfin videosu, slaytı, ekran görüntüsü, formülü veya yardımcı dosya metni birebir kopyalanmaz.
- Yazılar PiyasaPilot'a özgü örnek, sentetik grafik ve telifsiz açıklamayla yazılır.
- OCR-only kaynaklarda konuşmada kalıp ekranda görünmeyen detaylar eksik olabilir; bu durum frontmatter'da işaretlenir.
- Dış kaynak yalnızca kavram doğrulama ve güncel tanım için kullanılır; Borfin'in yerini almaz.

### 3.4 Her Makale Zorunlu Bölümleri
1. **Nedir?** — kavram tanımı (2-3 cümle)
2. **Nasıl hesaplanır?** — formül (PiyasaPilot DSL ile göster)
3. **Nasıl okunur?** — sinyaller, bölgeler, yorumlama
4. **Kullanım örnekleri** — gerçek piyasa senaryosu (sentetik grafik)
5. **Tuzaklar ve riskler** — overfit, repaint, gecikme, yanlış sinyal
6. **PiyasaPilot'ta kullan** — köprü aksiyonları

### 3.5 Köprü Aksiyonları (Her Makalede)
```typescript
// Örnek: Bollinger makalesindeki butonlar
[Grafiğe Ekle]        → ChartPanel.addIndicator('BB', {period:20, std:2})
[Backtest Preset'i Dene] → StrategyPanel.loadPreset('bollinger_bounce')
[Tarayıcıda Ara]      → Screener.setFilter({indicator:'BB', condition:'...'})
```

### 3.6 Arama
- Client-side fuzzy search: `fuse.js`
- Arama alanları: title, tags, content keywords
- Türkçe karakter normalizasyonu (ı→i, ş→s vb.)

---

## 4. Borfin Uygunluk Denetimi

| İçerik Grubu | Karar | Not |
|---|---|---|
| İndikatörler | Uygun | Fuat Akman ve Yaşar Erdinç OCR raporlarında güçlü kanıt var |
| Formasyonlar | Uygun | OBO, üçgen, bayrak, elmas, fincan-kulp, çanak, gap ve Fibonacci görünür OCR kanıtı taşıyor |
| Sistem & Backtest | Uygun | Kıvanç Özbilgiç ve Fuat Akman Sistem Trading raporları doğrudan ürünle örtüşüyor |
| VIOP & Vadeli | Uygun ama uyarılı | Gerçek veri/kontrat varsayımı yoksa sadece eğitim ve risk bilgisi olarak kalır |
| Psikoloji & Disiplin | Uygun | Paper journal, postmortem ve risk freni fikirlerine dönüştürülebilir |
| Mali analiz yazıları | Beklemeli | İlgili 151 videoluk ön okuma yapılmadan Eğitimler v1'e alınmayacak |
| Opsiyon/Varant/Swap | Beklemeli | 33 video okunmadan yalnızca gelecek kapsam notu olarak kalacak |

## 5. Makale Listesi (Öncelik Sırasıyla)

### Kategori 1: İndikatörler (20 makale)

| # | Başlık | Kaynak Kurs | İndikatör Key | Zorluk |
|---|--------|-------------|---------------|--------|
| 1 | Bollinger Bandı | Fuat Akman İndikatör | BB | Başlangıç |
| 2 | RSI — Göreceli Güç Endeksi | Fuat Akman İndikatör | RSI | Başlangıç |
| 3 | MACD | Fuat Akman İndikatör | MACD | Orta |
| 4 | Hareketli Ortalamalar: SMA ve EMA | Kıvanç HO + Fuat Akman | EMA, SMA | Başlangıç |
| 5 | ATR — Ortalama Gerçek Aralık | Fuat Akman İndikatör | ATR | Orta |
| 6 | Stochastic Osilatörü | Fuat Akman İndikatör | STOCH | Orta |
| 7 | ADX / ADXR — Yön Hareketi | Fuat Akman İndikatör | ADX | Orta |
| 8 | OBV — On-Balance Volume | Fuat Akman İndikatör | OBV | Orta |
| 9 | Ichimoku Bulutu | Fuat Akman İndikatör | ICHI | İleri |
| 10 | Parabolic SAR | Fuat Akman İndikatör | PSAR | Başlangıç |
| 11 | CCI — Emtia Kanal Endeksi | Fuat Akman İndikatör | CCI | Orta |
| 12 | MFI — Para Akış Endeksi | Fuat Akman İndikatör | MFI | Orta |
| 13 | MOST — Moving Stop Loss | Fuat Akman İndikatör | MOST | İleri |
| 14 | Chaikin Money Flow | Fuat Akman İndikatör | CMF | Orta |
| 15 | Williams %R | Fuat Akman İndikatör | WILLR | Orta |
| 16 | Volume Price Trend ve Volume Oscillator | Fuat Akman İndikatör | VPT, VOSC | Orta |
| 17 | Hacim Analizi | Fuat Akman İndikatör | VOL | Başlangıç |
| 18 | İleri HO Türleri: DEMA, TEMA, HMA, T3 | Kıvanç HO | DEMA vd. | İleri |
| 19 | ZigZag | Fuat Akman İndikatör | ZIGZAG | Orta |
| 20 | Heiken Ashi | Fuat Akman İndikatör | HA | Orta |

### Kategori 2: Formasyonlar (12 makale)

| # | Başlık | Kaynak Kurs | Zorluk |
|---|--------|-------------|--------|
| 21 | Omuz-Baş-Omuz (OBO) | Yaşar Erdinç Teknik + İleri | Orta |
| 22 | Çift Tepe ve Çift Dip | Yaşar Erdinç Teknik | Başlangıç |
| 23 | Üçgen Formasyonları | Yaşar Erdinç Teknik | Orta |
| 24 | Bayrak ve Flama | Yaşar Erdinç Teknik | Orta |
| 25 | Fincan-Kulp | Yaşar Erdinç İleri | Orta |
| 26 | Elmas Formasyonu | Yaşar Erdinç İleri | İleri |
| 27 | Gap Türleri | Yaşar Erdinç Teknik | Başlangıç |
| 28 | Destek ve Direnç | Yaşar Erdinç Teknik | Başlangıç |
| 29 | Trend Çizgileri ve Kanallar | Yaşar Erdinç Teknik | Başlangıç |
| 30 | Mum Formasyonları | Yaşar Erdinç Teknik | Orta |
| 31 | Fibonacci Düzeltme Seviyeleri | Yaşar Erdinç İleri | Orta |
| 32 | Fibonacci Extension ve Fan | Yaşar Erdinç İleri | İleri |

### Kategori 3: Sistem & Backtest (10 makale)

| # | Başlık | Kaynak Kurs | Zorluk |
|---|--------|-------------|--------|
| 33 | Algoritmik Trade Nedir? | Kıvanç Algo Trade | Başlangıç |
| 34 | Strateji Kategorileri: Trend, Momentum, Mean Reversion | Kıvanç Algo Trade | Orta |
| 35 | Backtest Nasıl Yapılır? | Kıvanç + Fuat Akman | Orta |
| 36 | Backtest Tuzakları: Overfit, Lookahead, Data Bias | Kıvanç + Fuat Akman | Orta |
| 37 | Komisyon ve Slippage Etkisi | Kıvanç + Fuat Akman | Orta |
| 38 | Optimizasyon ve Walk-Forward Analiz | Kıvanç Algo Trade | İleri |
| 39 | Monte Carlo Simülasyonu | Kıvanç Algo Trade | İleri |
| 40 | Sistem Kalite Metrikleri: Sharpe, PF, Max DD | Kıvanç + Fuat Akman | Orta |
| 41 | Portföy Çeşitlendirme | Kıvanç Algo Trade | İleri |
| 42 | Paper Trading ve Robot | Kıvanç Algo Trade | Orta |

### Kategori 4: VIOP & Vadeli (8 makale)

| # | Başlık | Kaynak Kurs | Zorluk |
|---|--------|-------------|--------|
| 43 | VIOP Nedir? Temel Kavramlar | VOB Yaşar + Vadeli Bolgün | Başlangıç |
| 44 | Kontrat Özellikleri ve Vade | VOB Yaşar | Orta |
| 45 | Teminat ve Kaldıraç | VOB Yaşar | Orta |
| 46 | Rollover ve Sürekli Kontrat | VOB Yaşar | İleri |
| 47 | Teorik Fiyat ve Baz | VOB Yaşar | İleri |
| 48 | VIOP'ta Backtest Varsayımları | VOB Yaşar | İleri |
| 49 | Hedge, Spekülatif ve Arbitraj | VOB Yaşar + Vadeli Bolgün | Orta |
| 50 | Kurumsal Aksiyonlar ve Kontrat Uyarlaması | VOB Yaşar | İleri |

### Kategori 5: Psikoloji & Disiplin (7 makale)

| # | Başlık | Kaynak Kurs | Zorluk |
|---|--------|-------------|--------|
| 51 | Yatırımcı Hataları ve Bilişsel Yanlılıklar | Psikoloji | Başlangıç |
| 52 | Stop-Loss Koyamamak: Kayıptan Kaçınma | Psikoloji | Orta |
| 53 | Overtrading ve Gürültü Trading | Psikoloji | Orta |
| 54 | Strateji Disiplini ve Postmortem | Psikoloji | Orta |
| 55 | Kayıp Serisi Yönetimi | Psikoloji | Orta |
| 56 | Aktif vs Pasif Yatırım | Psikoloji | Başlangıç |
| 57 | İşlem Öncesi Planlama | Psikoloji | Orta |

**Toplam: 57 makale**

---

## 6. İçerik Üretim Akışı

Her makale için:
1. Kaynak kurs OCR raporu okunur (`artifacts/borfin_*/ocr_report.md`)
2. OCR kanıtı yeterli değilse konu `source_confidence: low` olur veya beklemeye alınır
3. Dış kaynak araştırması yalnızca kavram doğrulama ve güncel bilgi için yapılır
4. Telifsiz görsel veya PiyasaPilot sentetik grafik üretilir
5. Makale PiyasaPilot'a özgü iş akışıyla yazılır
6. Frontmatter doldurulur, köprüler tanımlanır
7. `src/content/egitimler/{kategori}/{slug}.md` olarak kaydedilir

**Görsel kaynakları (öncelik sırası):**
- Wikimedia Commons (Creative Commons lisanslı)
- PiyasaPilot kendi grafiğinden sentetik ekran görüntüsü
- İnternet üzerindeki genel domain görseller

---

## 7. Uygulama Adımları (Öncelik Sırası)

### E-Faz 1: Altyapı (kod, içerik yok)
- [x] E1: `src/content/egitimler/` klasör yapısı
- [x] E2: `EgitimlerPanel.ts` iskelet (render yok, sadece şablon)
- [x] E3: `marked` kütüphanesi + frontmatter parser kurulumu
- [x] E4: `fuse.js` arama kurulumu
- [x] E5: `app.ts`'e Eğitimler sekmesi + klavye `6`

### E-Faz 2A: İlk 10 makale (İndikatörler)
- [x] E6: Bollinger Bandı makalesi + köprü testi
- [x] E7: RSI makalesi
- [x] E8: MACD makalesi
- [x] E9: SMA/EMA makalesi
- [x] E10: ATR makalesi
- [x] E11: Stochastic makalesi
- [x] E12: ADX makalesi
- [x] E13: OBV makalesi
- [x] E14: Parabolic SAR makalesi
- [x] E15: Ichimoku makalesi

### E-Faz 2B: Kalan 10 indikatör makalesi
- [ ] E16–E25: CCI, MFI, MOST, CMF, Williams %R, VPT/VOSC, Hacim, ileri HO, ZigZag, Heiken Ashi

### E-Faz 3: Formasyonlar (12 makale)
- [ ] E26–E37: Formasyon makaleleri (OBO, Çift Tepe, Üçgen vb.)

### E-Faz 4: Sistem & Backtest (10 makale)
- [ ] E38–E47: Sistem trading ve backtest makaleleri

### E-Faz 5: VIOP & Vadeli (8 makale)
- [ ] E48–E55: VIOP makaleleri

### E-Faz 6: Psikoloji & Disiplin (7 makale)
- [ ] E56–E62: Psikoloji makaleleri

---

## 8. Test ve Kabul Kriterleri

- [ ] E2E: Eğitimler sekmesi açılır, kategori listesi görünür
- [ ] E2E: "Bollinger" aranır, makale listelenir ve açılır
- [ ] E2E: "Grafiğe Ekle" tıklanır, BB grafiğe eklenir
- [ ] E2E: "Backtest Preset'ini Dene" tıklanır, StrategyPanel açılır
- [ ] E2E: Klavye `6` ile sekmeye geçilir
- [ ] E2E: Mevcut grafik/backtest durumu sekme geçişinde korunur
- [ ] Unit: Frontmatter parse doğru çalışır
- [ ] Unit: Türkçe arama (ı, ş, ç vb.) doğru eşleşir

---

## 9. Bölüm 21 — Eğitim Özellik Radar'ı (Mevcut Plan, Korunuyor)

> Bu bölüm planlama.md Bölüm 21'den taşındı. Blog makaleleri bu radar'daki özelliklere köprülenecek.

### 21.2 İndikatör Merkezi v2
- [ ] İndikatörler kategoriye ayrılacak: trend, momentum, volatilite/bant, hacim, yön-güç
- [ ] Her indikatör kartında: kullanım amacı, gecikme/repaint riski, önerilen veri uzunluğu
- [ ] Aynı indikatörün birden fazla instance'ı desteklenecek
- [ ] Parametre değişimi rapora kaydedilecek
- [ ] Test: E2E'de Bollinger grafiğe eklenir, parametre değiştirilir, aynı ayarlar backtest preset'ine taşınır

### 21.3 Teknik Analiz Uygulama Labı
- [ ] Çizimlerden türetilen olaylar: trend kırılımı, yatay destek teması, formasyon teyidi
- [ ] Analiz checklist: trend yönü, destek/direnç, hacim teyidi, risk/ödül, stop seviyesi
- [ ] "Analizi strateji fikrine çevir" akışı
- [ ] Test: destek çizgisi → alarm taslağı → backtest kural adayı

### 21.4 Sistem Trading Labı
- [ ] Kural debug paneli: her bar için giriş/çıkış koşulu true/false
- [ ] Explorer mantığı StrategySpec tarayıcıya bağlantısı
- [ ] Backtest kalite kapıları: min işlem sayısı, parametre sayısı, out-of-sample durumu
- [ ] Test: StrategySpec koşulu tarayıcıda sembol listesi üretir

### 21.5 VIOP Labı
- [ ] Kontrat türü, vade geçişi, teminat varsayımı, tick size zorunlu alanlar
- [ ] Lisanslı veri yoksa `not_configured` + uyarı
- [ ] Rollover v1: uyarı ve manuel varsayım
- [ ] Test: VİOP sembolünde backtest, varsayım eksikse "paper'a al" pasif

### 21.6 Eğitim Bağlantılı UX
- [ ] Eğitimler sekmesinde arama
- [ ] Konu sayfası: grafikte göster, strateji preset, backtest metrikler
- [ ] Her konu sayfasında "bu bilgi nerede yanıltır?" uyarı alanı
- [ ] Test: Bollinger aranır → grafiğe eklenir → backtest preset açılır

### 21.7 Borfin Özellik Backlog'u (Eğitim→Ürün)
- [ ] İndikatör Taksonomi Motoru (kategorili, metadata'lı)
- [ ] Bollinger Eğitimden Grafiğe Akışı
- [ ] İndikatörden StrategySpec'e Sihirbaz (Bollinger, ADX, RSI şablonları)
- [ ] Formasyon Workbench (OBO, üçgen, bayrak için boyun/kırılım/hedef)
- [ ] Güvenli Gösterge Geliştirme Sandbox'ı
- [ ] Sistem Kataloğu ve Kural Ailesi Haritası
- [ ] StrategySpec Fonksiyon Sözlüğü
- [ ] No-Lookahead Kural Doğrulayıcı
- [ ] Stop-Hedef-Vade Kilidi
- [ ] Kayıp Serisi Mola Kuralı
- [ ] Postmortem ve Davranış Etiketi
- [ ] Sıklık ve Gürültü Filtresi
- [ ] Pasif Benchmark Disiplini

---

## 10. Kapsam Dışı (v1'de Yok)

- Video oynatıcı entegrasyonu
- Kullanıcı yorum/not sistemi
- İçerik versiyonlama UI
- Çok dilli destek
- Sosyal paylaşım
