# Aktif Geliştirme Planı — PiyasaPilot

> Sprint 0–12 tamamlandı (bkz. `planlama-sprint-gecmis.md`).
> Bu dosya aktif geliştirme sırasını ve önceliklerini gösterir.
> Tarih: 2026-05-01

---

## Geliştirme Prensibi

**Sadece ekle, bozma.** Mevcut çalışan gateway (8000), workers, BacktestEngine, paper trading ve frontend (5173) korunur. Yeni sekmeler için `app.ts`, nav ve stil katmanına kontrollü dokunmak gerekir; amaç mevcut akışı bozmadan genişletmektir.

---

## Faz 1 — Yeni Sekmeler (En Az Riskli)

Yeni dosyalar eklenir, `app.ts`'e iki sekme bağlanır. Sinyaller sekmesi `5` olarak kalır.

### 1A. Eğitimler Sekmesi

**Detay:** `planlama-egitimler.md`

| Adım | İş | Etki |
|------|----|------|
| E1 | `src/content/egitimler/` klasörü + markdown dosyaları | Sıfır |
| E2 | `EgitimlerPanel.ts` yeni component | Sıfır |
| E3 | `app.ts`'e Eğitimler sekmesi (klavye: `6`) | Çok düşük |
| E4 | Arama + kategori sidebar | Sıfır |
| E5 | "Grafiğe Ekle" köprüsü (ChartPanel event) | Düşük |
| E6 | "Backtest Preset'ini Dene" köprüsü | Düşük |
| E7 | Blog makaleleri — İndikatörler (20 makale) | Sıfır |
| E8 | Blog makaleleri — Formasyonlar (12 makale) | Sıfır |
| E9 | Blog makaleleri — Sistem & Backtest (10 makale) | Sıfır |
| E10 | Blog makaleleri — VIOP & Vadeli (8 makale) | Sıfır |
| E11 | Blog makaleleri — Psikoloji & Disiplin (7 makale) | Sıfır |

**Kabul:** E2E'de kullanıcı Bollinger arar → makale açılır → grafiğe ekler → backtest preset görür.

### 1B. Mali Analiz Sekmesi

**Detay:** `planlama-mali-analiz.md`

| Adım | İş | Etki |
|------|----|------|
| M1 | `GET /api/mali-analiz/{symbol}` yeni endpoint | Sıfır |
| M2 | borsa-mcp entegrasyonu + günlük SQLite cache | Sıfır |
| M3 | `MaliAnalizPanel.ts` yeni component | Sıfır |
| M4 | `app.ts`'e Mali Analiz sekmesi (klavye: `7`) | Çok düşük |
| M5 | BIST 30 hisse listesi + hisse detay sayfası | Sıfır |
| M6 | "Grafikte Aç" köprüsü | Düşük |
| M7 | BIST 100'e genişleme | Düşük |

**Kabul:** THYAO seçilince bilanço, gelir tablosu, finansal oranlar görünür; "Grafikte Aç" ChartPanel'i açar.

---

## Faz 2 — Grafik Lab (ChartPanel.ts'e dikkatli dokunma)

**Detay:** `planlama-grafik.md`

Sıra: G2 → G3 → G4 → G5 → G6 → G7 → G8 → G9 → G10

Her sprint öncesi mevcut Playwright testleri geçmeli. Sprint G1 zaten tamamlandı.

| Sprint | Konu | Ana Risk |
|--------|------|----------|
| G2 | Ölçek menüsü: lineer/log/yüzdesel | Orta |
| G3 | İndikatör merkezi v2, parametre penceresi | Orta |
| G4 | Kar/zarar overlay, maliyet/stop/hedef çizgileri | Orta |
| G5 | Çizim altyapısı: trend/yatay/dikey/kanal | Yüksek |
| G6 | Çoklu sembol karşılaştırma | Orta |
| G7 | Multi-chart senkron kilitleri | Orta |
| G8 | Şablonlar, kayıt, export | Düşük |
| G9 | Haber/KAP/bilanço event marker | Düşük |
| G10 | Fibonacci/regresyon/renko | Yüksek |

---

## Faz 3 — Backtest Lab (quant_engine değişiklikler)

**Detay:** `planlama-backtest.md`

Sıra: B1 → B2 → B3 → B4 → B5 → B6 → B7 → B8 → B9 → B10 → B11 → B12 → B13

Her sprint öncesi `python -m pytest tests/ -q` tüm testler geçmeli.

| Sprint | Konu | Bağımlılık |
|--------|------|------------|
| B1 | Strateji kataloğu + Borfin presetleri | Yok |
| B2 | İndikatör merkezi v2 + geniş HO kütüphanesi | B1 |
| B3 | Görsel kurucu bloklar + DSL genişletme | B2 |
| B4 | Backtest gerçekçilik: slippage, komisyon, likidite | B1 |
| B5 | Backtest kalite skoru ve tuzak uyarıları | B4 |
| B6 | Walk Forward Analysis (WFA) motoru | B5 |
| B7 | Monte Carlo simülasyonu | B5 |
| B8 | Optimizasyon v2: heatmap, stabil bölge | B6 |
| B9 | Piyasa Tarayıcı v3 | B3 |
| B10 | Portföy Lab: korelasyon, çeşitlendirme | B7 |
| B11 | Paper robot operasyon paneli | B10 |
| B12 | Strategy pack import/export | B11 |
| B13 | UI bilgi mimarisi: lifecycle, postmortem | B12 |

---

## Aktif Sprint Takibi

| Faz | Sprint | Durum |
|-----|--------|-------|
| Faz 1A | E1–E4 | Başlanacak |
| Faz 1B | Mali analiz eğitim OCR'ı | Ön koşul |
| Faz 2 | G2 | Bekliyor |
| Faz 3 | B1 | Bekliyor |

---

## Notlar

- Her sprint tamamlanınca bu dosyada ilgili satır `✅` ile işaretlenir.
- Faz 1 paralel gidebilir (Eğitimler ve Mali Analiz bağımsız).
- Faz 2 ve Faz 3 paralel gidebilir (frontend ve backend ayrı katmanlar).
- Faz 3 B6–B13 en ağır kısım; WFA ve Monte Carlo backend'de yeni modüller gerektirir.
