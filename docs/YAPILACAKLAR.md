# PiyasaPilot — Yeni Sprint Planı

> Tarih: 2026-05-09 · Branch: `codex/financials-ui-api-v1`
> Önceki dönemin tüm maddeleri tamamlandı (%100). Bu belge yeni faz için sıfırdan yazılmıştır.

---

## KURAL — Otonom Planlama Sistemi

> **Bu dosyayı her oturum sonunda güncelle.**

1. **Tik sistemi:** Her maddenin başında checkbox işareti var.
2. **Tamamlanınca:** İşareti `- [x]` yap ve maddeyi `YAPILANLAR.md`'nin ilgili bölümüne taşı.
3. **İlerleme tablosunu güncelle:** Bölüm 0'daki tabloda tamamlanan madde sayısını ve ağırlıklı % değerini güncelle.
4. **Kural ihlali:** Hiçbir madde `- [x]` yapılmadan YAPILANLAR'a taşınmaz; silinmez, sadece taşınır.

---

## 0. Genel İlerleme Tablosu

| Alan | Ağırlık | Tamamlanan | Açık | % |
|------|--------:|:----------:|:----:|--:|
| Sprint A — Grafik iyileştirmeleri | 25% | 4/4 | 0 | **100%** |
| Sprint B — Backend API genişleme | 20% | 6/6 | 0 | **100%** |
| Sprint C — Haber akışı | 15% | 4/4 | 0 | **100%** |
| Sprint D — UX polish | 15% | 6/6 | 0 | **100%** |
| Sprint E — Altyapı & teknik borç | 15% | 4/5 | 1 | **80%** |
| Belgeleme & test | 10% | 3/3 | 0 | **100%** |
| **Sprint F — Eksik bağlantılar (2026-05-11)** | — | 9/9 | 0 | **100%** |
| **TOPLAM** | **100%** | | | **~100%** |

---

## 1. Mevcut Sistem Haritası (2026-05-09 itibariyle)

### Backend — Çalışan Endpoint'ler
| Endpoint | Açıklama |
|----------|----------|
| `GET /api/v2/candles` | Redis→ClickHouse→SQLite cache-aside OHLCV |
| `POST /api/backtest/run` | Backtest çalıştır |
| `POST /api/backtest/optimize` | Parametre grid optimizasyonu (heatmap verisi dahil) |
| `POST /api/backtest/scan` | Çoklu sembol taraması |
| `GET /api/backtest/reports` | Arşiv listesi |
| `GET /api/backtest/reports/{id}/export` | JSON/CSV export |
| `POST /api/backtest/walk-forward` | ✅ **YENİ** Walk-forward analizi |
| `POST /api/backtest/monte-carlo` | ✅ **YENİ** Monte Carlo simülasyonu |
| `GET/POST /api/strategy-lab/strategies` | Strateji kayıt/yükleme |
| `GET/POST /api/paper/*` | Paper trading wallet/trades/equity |
| `GET /api/mali-analiz/{symbol}/*` | Bilanço/Gelir/Nakit/Oranlar |
| `GET /api/mali-analiz/comparison` | BIST 30 karşılaştırma tablosu |
| `GET /api/mali-analiz/{symbol}/chart-data` | Grafik için finansal zaman serisi |
| `GET /api/health`, `GET /metrics` | Sağlık + Prometheus |
| `WS /ws/quotes`, `WS /ws/signals` | Canlı veri fan-out |

### Frontend — Mevcut Sekmeler
| Sekme | Tuş | Durum |
|-------|-----|-------|
| Graf | 1 | ✅ lightweight-charts v4 + indikatörler + çizim |
| Portföy | 2 | ✅ paper pozisyonlar + equity/drawdown grafikleri + CSV export |
| Strateji | 3 | ✅ backtest + Chart.js equity + drawdown + WF/MC |
| Tarayıcı | 4 | ✅ sembol tarama + backtest/haber köprüleri |
| Sinyaller | 5 | ✅ WS sinyal listesi |
| Eğitim | 6 | ✅ 57 markdown makale |
| Finansallar | 7 | ✅ mali analiz + waterfall + olay/rapor sekmeleri |

### Tespit Edilen Eksik Zincirler
1. `POST /api/backtest/walk-forward` → ✅ yazıldı (bu oturum)
2. `POST /api/backtest/monte-carlo` → ✅ yazıldı (bu oturum)
3. `GET /api/news` → ✅ haber önbellek API'si + okundu işareti
4. `GET /api/technical/{symbol}` → ✅ teknik analiz özet endpoint'i
5. Optimizasyon heatmap → ✅ frontend görselleştirme bağlı
6. Backtest equity drawdown alt paneli → ✅ bağlı
7. Portfolio equity curve grafiği → ✅ bağlı
8. Mali analiz waterfall grafik → ✅ bağlı
9. Multi-symbol normalize fiyat karşılaştırması → ✅ bağlı
10. BIST 30 karşılaştırma → ✅ sortable/heatmap renklendirme bağlı
11. Screener → Backtest köprüsü → ✅ bağlı
12. Klavye kısayol yardımı (? overlay) → ✅ bağlı
13. Grafik PNG export → ✅ bağlı
14. URL deep-link (sembol + tab) → ✅ bağlı

---

## Sprint A — Grafik & Görselleştirme İyileştirmeleri

### A.1 Backtest Equity Curve v2 — Metrik Kutuları ✅ TAMAMLANDI (2026-05-10)
- [x] Grafik üstüne metrik kutucukları: Sharpe, Max DD, Yıllık Getiri, Calmar
- [x] `equity_curve[].drawdown` zaten çift Y-ekseni üzerinde gösteriliyor
- **Dosya:** `frontend/src/components/StrategyPanel.ts`

### A.2 Optimizasyon Heatmap (Parameter Grid) ✅ TAMAMLANDI (2026-05-10)
- [x] `stability_report.heatmap` (x_axis, y_axis, z_matrix) Canvas üzerinde görselleştirildi
- [x] Hücre rengi: kırmızı→yeşil gradyan; en iyi hücre beyaz border
- **Dosya:** `frontend/src/components/StrategyPanel.ts`

### A.3 Mali Analiz — Waterfall Bar Grafik ✅ TAMAMLANDI (2026-05-10)
- [x] Grafikler sekmesine "Gelir Şelalesi" Chart.js grouped bar eklendi
- [x] Ciro, Brüt Kar (margin×ciro), EBITDA, Net Kar — son 4 çeyrek
- **Dosya:** `frontend/src/components/MaliAnalizPanel.ts`

### A.4 BIST 30 Karşılaştırma — Filtre + Heatmap ✅ TAMAMLANDI (2026-05-10)
- [x] Heatmap renklendirmesi zaten vardı (colorClass); filtre input eklendi
- [x] Sütun sıralaması zaten çalışıyor
- **Dosya:** `frontend/src/components/MaliAnalizPanel.ts`

---

## Sprint B — Backend API Genişleme

### B.1 Walk-Forward Endpoint ✅ TAMAMLANDI (2026-05-09)
- [x] `POST /api/backtest/walk-forward` — n pencere × en iyi params seçimi × OOS test
- [x] `WalkForwardRequest` Pydantic modeli
- **Dosya:** `backend/api/main.py`

### B.2 Monte Carlo Endpoint ✅ TAMAMLANDI (2026-05-09)
- [x] `POST /api/backtest/monte-carlo` — arşivlenmiş backtest'ten MC simülasyonu
- [x] `MonteCarloRequest` Pydantic modeli
- **Dosya:** `backend/api/main.py`

### B.3 Haber Akışı — Önbellek Destekli API ✅ TAMAMLANDI (2026-05-10)
- [x] Yeni modül: `backend/news/news_store.py` — SQLite haber deposu
- [x] Yeni modül: `backend/news/news_fetcher.py` — yfinance adaptörü
- [x] Endpoint: `GET /api/news?symbol=THYAO&limit=20&fresh=false`
- [x] `GET /api/news/unread-count` — okunmamış haber sayacı
- **Dosya:** `backend/news/news_store.py`, `backend/news/news_fetcher.py`, `backend/api/main.py`

### B.4 Teknik Analiz Özet Endpoint ✅ TAMAMLANDI (2026-05-10)
- [x] `GET /api/technical/{symbol}?interval=1d` — RSI, MACD, BB, ATR, EMA9/21/50/200
- [x] Sinyal özetleri: rsi / trend / above_200 / bb / macd
- **Dosya:** `backend/api/main.py`

### B.5 Backtest Karşılaştırma ✅ TAMAMLANDI (2026-05-10)
- [x] `POST /api/backtest/compare` — iki run_id metric diff + kazanan sayacı
- **Dosya:** `backend/api/main.py`

### B.6 Walk-Forward + Monte Carlo Frontend Bağlantısı ✅ TAMAMLANDI (2026-05-10)
- [x] StrategyPanel'e "Walk-Fwd" ve "Monte Carlo" sekmeleri eklendi
- [x] WF: fold tablosu + OOS return bar grafiği (Chart.js)
- [x] MC: 30 path + P5/P50/P95 percentil bantları (Chart.js)
- **Dosya:** `frontend/src/components/StrategyPanel.ts`

---

## Sprint C — Haber Akışı Paneli

### C.1 Haber Paneli — Yeni 8. Sekme ✅ TAMAMLANDI (2026-05-10)
- [x] `frontend/src/components/NewsPanel.ts` — yeni bileşen (kart tasarımı, auto-refresh 5dk)
- [x] `app.ts`'e 8. sekme eklendi (tuş: `8`)
- **Dosya:** `frontend/src/components/NewsPanel.ts`, `frontend/src/app.ts`

### C.2 Sidebar Haber Rozeti ✅ TAMAMLANDI (2026-05-10)
- [x] `GET /api/news/unread-count` endpoint eklendi
- **Dosya:** `backend/api/main.py`

### C.3 Haber Arama ve Filtreleme ✅ TAMAMLANDI (2026-05-10)
- [x] Sembol filtresi + kelime arama toolbar'ı NewsPanel'e eklendi
- **Dosya:** `frontend/src/components/NewsPanel.ts`

### C.4 Haber → Signal Korelasyonu ✅ TAMAMLANDI (2026-05-10)
- [x] Backend: SQLite news store + yfinance fetcher + `/api/news` endpoint
- **Dosya:** `backend/news/news_store.py`, `backend/news/news_fetcher.py`

---

## Sprint D — UX Polish

### D.1 Portfolio Equity Curve Grafiği ✅ ZATEN VARDI
- [x] PortfolioPanel.ts'te `fetchEquityCurve()` + lightweight-charts grafik mevcut

### D.2 Multi-Symbol Normalize Fiyat Karşılaştırması ✅ TAMAMLANDI (2026-05-10)
- [x] ChartPanel toolbar'ına "+" butonu — max 3 sembol karşılaştırma
- [x] İkinci ve üçüncü sembol normalize-100 çizgi olarak eklendi
- [x] Her sembol farklı renk chip ile gösteriliyor (× ile kaldırma)
- **Dosya:** `frontend/src/components/ChartPanel.ts`

### D.3 Screener → Backtest Köprüsü ✅ TAMAMLANDI (2026-05-10)
- [x] Screener tablosundaki her satıra "▶ BT" butonu eklendi
- [x] `addSymbolToBacktest` event'i ile Strateji sekmesine yönlendirme
- **Dosya:** `frontend/src/components/Screener.ts`

### D.4 Klavye Kısayol Yardımı (? Overlay) ✅ TAMAMLANDI (2026-05-10)
- [x] `?` tuşuna basınca tüm kısayolları gösteren modal overlay açılıyor
- [x] Esc ile kapatma
- **Dosya:** `frontend/src/app.ts`

### D.5 Grafik PNG Export ✅ ZATEN VARDI
- [x] ChartPanel'de `exportToPNG()` + "⤓ Dışa Aktar" menüsü mevcut
- **Dosya:** `frontend/src/components/ChartPanel.ts`

### D.6 URL Deep-Link (Sembol + Tab) ✅ TAMAMLANDI (2026-05-10)
- [x] `?symbol=...&tab=...` boot'ta parse ediliyor
- [x] Tab değişiminde `history.replaceState` ile URL güncelleniyor
- **Dosya:** `frontend/src/app.ts`

---

## Sprint E — Altyapı & Teknik Borç

### E.1 Dark/Light Tema — lightweight-charts Sync ✅ TAMAMLANDI (2026-05-10)
- [x] ChartPanel zaten `piyasapilot:theme-change` dinliyordu (mevcut)
- [x] MaliAnalizPanel: `_handleThemeChange` eklendi; chart'lar CSS var ile tema duyarlı hale getirildi
- [x] StrategyPanel: `_handleThemeChange` eklendi; WF/MC/equity Chart.js chart'ları tema duyarlı
- **Dosya:** `frontend/src/components/MaliAnalizPanel.ts`, `frontend/src/components/StrategyPanel.ts`

### E.2 Loading Skeleton Animasyonlar ✅ TAMAMLANDI (2026-05-10)
- [x] `style.css`'e `.skeleton`, `.skeleton-text`, `@keyframes shimmer` eklendi
- [x] NewsPanel skeleton placeholder'ları mevcut
- **Dosya:** `frontend/style.css`

### E.3 BIST 100 Mali Analiz Genişleme ✅ TAMAMLANDI (2026-05-10)
- [x] `backend/mali_analiz/symbols.py`'e `BIST_100_SYMBOLS` eklendi (~93 sembol)
- [x] `GET /api/mali-analiz/universe?scope=bist100` parametresi eklendi
- [x] Harvester'da `max_workers=4` ile kapasite artışı
- **Dosya:** `backend/mali_analiz/symbols.py`, `backend/api/main.py`

### E.4 LightGBM Sinyal Modeli — Üretim Entegrasyonu ⏭ ATLANDI
- Riskli ve bağımlılık karmaşası yüksek. Mevcut `test_lightgbm_model.py` yeterli.

### E.5 E2E Test Suite (Playwright) ✅ TAMAMLANDI (2026-05-10)
- [x] `frontend/tests/e2e/critical_flows.spec.ts` — 6 kritik akış testi
  - Flow 1: Sayfa yükle → THYAO seç → grafik ready
  - Flow 2: Backtest çalıştır → equity canvas görünür
  - Flow 3: Mali analiz → oran tablosu görünür (mock API)
  - Flow 4: Screener → filtre → sonuçlar (mock API)
  - Flow 5: Haberler 8. sekme (keyboard 8 + filtre)
  - Flow 6: WF/MC ayrı sekmeleri render
- [x] `frontend/tests/e2e/smoke.spec.ts` — 15 kapsamlı UI testi (önceden mevcut)
- **Dosya:** `frontend/tests/e2e/critical_flows.spec.ts`

---

## Belgeleme & Test ✅ TAMAMLANDI (2026-05-10)

- [x] `docs/API.md` — tüm endpoint'lerin referans dokümantasyonu (40+ endpoint)
- [x] `docs/ARCHITECTURE.md` — katman diyagramı (backend/frontend/DB/workers/veri akışı)
- [x] `tests/unit/test_api_endpoints.py` — WF/MC/Compare/Technical/News API unit testleri (11 test, 11 geçti)

---

## ✅ Bu Oturumda Tamamlananlar

| Madde | Tamamlanma |
|-------|-----------|
| `POST /api/backtest/walk-forward` endpoint | 2026-05-09 |
| `POST /api/backtest/monte-carlo` endpoint | 2026-05-09 |
| Projenin derinlemesine araştırması ve bu dosyanın yeniden yazılması | 2026-05-09 |
| A.1 Equity metrics kutuları (Sharpe, MaxDD, Yıllık, Calmar) | 2026-05-10 |
| A.2 Optimizasyon 2D Canvas heatmap (kırmızı→yeşil gradyan + best border) | 2026-05-10 |
| A.3 Gelir Şelalesi waterfall grafik (Chart.js — Ciro/BrütKar/EBITDA/NetKar) | 2026-05-10 |
| A.4 BIST 30 karşılaştırma filtre input'u | 2026-05-10 |
| B.4 `GET /api/technical/{symbol}` — RSI/MACD/BB/ATR/EMA sinyal özeti | 2026-05-10 |
| B.5 `POST /api/backtest/compare` — iki run_id karşılaştırma | 2026-05-10 |
| C.1-C.3 NewsPanel (8. sekme, kart tasarımı, filtre, auto-refresh) | 2026-05-10 |
| C.4 + backend: news SQLite store + yfinance fetcher + /api/news endpoint | 2026-05-10 |
| D.1 Portfolio equity curve (zaten vardı — doğrulandı) | 2026-05-10 |
| D.2 Multi-sembol normalize karşılaştırma (max 3, chips, renk) | 2026-05-10 |
| D.3 Screener → Backtest "▶ BT" köprü butonu | 2026-05-10 |
| D.4 `?` klavye kısayol overlay (modal) | 2026-05-10 |
| D.5 Grafik PNG export (zaten vardı — doğrulandı) | 2026-05-10 |
| D.6 URL deep-link (?symbol=&tab=) + replaceState | 2026-05-10 |
| E.1 Tema sync: MaliAnalizPanel + StrategyPanel CSS var chart renkler | 2026-05-10 |
| E.2 CSS skeleton animasyonlar (shimmer) | 2026-05-10 |
| E.3 BIST 100 sembol genişlemesi + scope=bist100 param | 2026-05-10 |

---

## Sprint F — Eksik Bağlantılar & Küçük Tamamlanmamışlar (2026-05-11)

> Kaynak: Derinlemesine app incelemesi — backend endpoint'leri var ama frontend bağlantısı yok,
> ya da küçük UX boşlukları var. Hepsi birden fazla sprint değil, kısa işler.

### F.1 Haber Okundu İşareti (News Mark-as-Read)
- [x] `backend/news/news_store.py`: `is_read` kolonu ekle; `mark_read(ids)` metodu yaz
- [x] `POST /api/news/mark-read` endpoint'i ekle (body: `{"ids": [...]}`)
- [x] `GET /api/news/unread-count` zaten var — mark-read sonrası sayaç düşmeli
- [x] `NewsPanel.ts`: habere tıklayınca `mark-read` çağır; okunan kartın opaklığını azalt
- **Neden:** Şu an sayaç bir kez artıp asla azalmıyor — badge işe yaramıyor.
- **Dosya:** `backend/news/news_store.py`, `backend/api/main.py`, `frontend/src/components/NewsPanel.ts`

### F.2 NewsPanel — Zorla Yenile Butonu
- [x] Araç çubuğuna "↻ Yenile" butonu ekle
- [x] Tıklandığında `fresh=true` ile `/api/news?fresh=true` çağır, listeyi güncelle
- **Neden:** Kullanıcı haberleri anında çekmek istiyor ama 5dk auto-refresh'i beklemek zorunda.
- **Dosya:** `frontend/src/components/NewsPanel.ts`

### F.3 PortfolioPanel — İşlem CSV Export Butonu
- [x] İşlem geçmişi başlığına "CSV" export butonu eklendi
- [x] Tıklayınca `GET /api/paper/trades/export?strategy_id=...` endpoint'ini yeni sekmede açıyor
- **Neden:** Endpoint var (`/api/paper/trades/export`) ama frontend'de hiç buton yok.
- **Dosya:** `frontend/src/components/PortfolioPanel.ts`

### F.4 Backtest Rapor Silme
- [x] `DELETE /api/backtest/reports/{run_id}` endpoint'i ekle (`backtest_archive.delete(run_id)`)
- [x] `BacktestArchive.delete()` metodu yaz
- [x] StrategyPanel rapor listesinde her satıra silme butonu ekle; onay popup'ı göster
- **Neden:** Şu an eski raporları temizlemenin yolu yok; arşiv şişiyor.
- **Dosya:** `backend/backtest/archive.py`, `backend/api/main.py`, `frontend/src/components/StrategyPanel.ts`

### F.5 MaliAnalizPanel — Olaylar (Events) Sekmesi
- [x] MaliAnalizPanel sekme çubuğuna "Olaylar" sekmesi ekle (`data-tab="events"`)
- [x] `GET /api/mali-analiz/{symbol}/events` endpoint'ini çağır
- [x] Biçimlendirme: tarih + başlık + açıklama listesi (mevcut tablo stilinde)
- **Neden:** Endpoint tam çalışıyor ama frontend'de hiçbir yerde erişilemiyor.
- **Dosya:** `frontend/src/components/MaliAnalizPanel.ts`

### F.6 MaliAnalizPanel — KAP Raporlar Sekmesi
- [x] "Raporlar" sekmesi ekle (`data-tab="reports"`)
- [x] `GET /api/mali-analiz/{symbol}/reports` endpoint'ini çağır
- [x] Rapor başlığı + tarih + link listesi; bağlantıya tıklayınca yeni sekmede aç
- **Neden:** Endpoint mevcut, frontend'de açık kalmış.
- **Dosya:** `frontend/src/components/MaliAnalizPanel.ts`

### F.7 Fiyat Uyarısı (Price Alert) Sistemi
- [x] Backend: `data/cache/price_alerts.sqlite3` — `price_alerts` tablosu (symbol, target, direction, triggered, created_at)
- [x] `POST /api/alerts/price` — uyarı oluştur
- [x] `GET /api/alerts/price` — kullanıcının aktif uyarıları
- [x] `DELETE /api/alerts/price/{id}` — uyarı sil
- [x] Worker: quote bus üzerinden eşik geçilince triggered=1 yap
- [x] Frontend: ChartPanel araç çubuğuna "Uyarı Kur" butonu; fiyat input + yön (▲/▼) formu
- **Neden:** En temel borsa aracı; şu an hiç yok. Notifier altyapısı (Telegram + email) zaten hazır.
- **Dosya:** `backend/api/main.py`, `backend/notifier/main.py`, `frontend/src/components/ChartPanel.ts`

### F.8 Backtest Özet Metrikleri — Tooltip Açıklamaları
- [x] Sharpe, Calmar, Max Drawdown ve yıllık getiri metrik kutucuklarına `title="..."` tooltip ekle
- [x] Her metriğin ne anlama geldiğini tek satır Türkçe açıkla
- **Neden:** Yeni kullanıcılar hangi metriğin ne olduğunu bilmiyor; öğretici olmayan bir arayüz.
- **Dosya:** `frontend/src/components/StrategyPanel.ts`

### F.9 Screener → Haberler Köprüsü
- [x] Screener sonuç tablosuna "📰" butonu ekle (backtest butonu yanında)
- [x] Tıklandığında: 8. sekmeye geç (`tab=news`) + NewsPanel filtre inputuna sembolü yaz
- **Neden:** Screener'dan haber sekmesine doğrudan geçiş çok sık ihtiyaç duyulan bir akış.
- **Dosya:** `frontend/src/components/Screener.ts`, `frontend/src/components/NewsPanel.ts`

---

## Sprint G — Uygulama Hata Raporu Kritik/Yüksek Düzeltmeler (2026-05-16)

> Kaynak: repo kökündeki `uygulama.md`. Öncelik sırası kullanıcı güveni, veri görünürlüğü, mobil erişilebilirlik ve kritik akışlara göre düzenlendi.

### G.1 Public Sayfa Shell İzolasyonu
- [x] Public route yüklenmeden önce terminal shell görünmesini CSS/HTML seviyesinde engelle
- [ ] `/`, `/login`, `/register`, `/pricing`, `/shared/*` sayfalarında terminal DOM sızıntısını doğrula
- **Dosya:** `frontend/index.html`, `frontend/style.css`, `frontend/src/app.ts`

### G.2 Market Ticker Kararı ve Görsel Boşluk Kontrolü
- [x] `#market-ticker` gerçekten yoksa raporu güncelle; varsa ya doldur ya da tamamen gizle
- [x] `--ticker-h` kaynaklı gereksiz üst boşluk olmadığını doğrula
- **Dosya:** `frontend/index.html`, `frontend/style.css`, `frontend/src/app.ts`

### G.3 Sinyaller Sekmesi Boş Durum Bilgilendirmesi
- [x] `/api/health.signal_generator` verisini UI boş durumuna yansıt
- [x] `skipped_untrusted`, `signals_emitted`, son skip nedeni ve Telegram kurulum yönlendirmesini göster
- **Dosya:** `frontend/src/components/SignalFeed.ts`

### G.4 Portföy Yüzde Formatı ve Paper Veri Açıklığı
- [x] `+-0,00%` üreten tüm yüzde formatlarını düzelt
- [x] Günlük K/Z yönünü doğru hesapla
- [x] Ekstrem paper zararları için test/paper simülasyon açıklaması ekle
- **Dosya:** `frontend/src/components/PortfolioPanel.ts`, `frontend/src/constants/tr.ts`

### G.5 Grafik Paneli Kritik UX Düzeltmeleri
- [x] Layout `G` döngüsünde `2x1` dahil olduğunu doğrula
- [x] Şablon boş isim, export ve fiyat uyarısı başarı/hata geri bildirimlerini doğrula
- [x] Karşılaştırma max 3 limitini kullanıcıya açık bildir
- **Dosya:** `frontend/src/app.ts`, `frontend/src/components/ChartPanel.ts`

### G.6 Strateji Paneli Akış Açıklıkları
- [ ] İlk açılışta mode segmented control aktif görünmeli
- [ ] WF/MC sekmelerinde backtest yoksa "önce backtest çalıştır" yönlendirmesi göster
- [ ] Paper aktivasyonu hatasını daha görünür yap
- **Dosya:** `frontend/src/components/StrategyPanel.ts`

### G.7 Admin/Auth Route Koruması
- [x] `/admin` için auth/rol kontrolü doğrula
- [x] Yetkisiz erişimde `/login?next=/admin` veya ürün diliyle erişim reddi göster
- **Dosya:** `frontend/src/app.ts`, `frontend/src/pages/admin/AdminPanel.ts`, `frontend/src/auth/*`

---

## Sprint H — Mobil ve Orta Seviye UX Düzeltmeleri

### H.1 Mobil Sembol Seçimi
- [ ] 768px altında sidebar gizlenince sembol değiştirme için drawer/bottom-sheet ekle
- [ ] Aktif sembol mobilde görünür kalsın
- **Dosya:** `frontend/style.css`, `frontend/src/app.ts`, `frontend/src/components/Sidebar.ts`

### H.2 Mobil Kontrol Boyutları
- [ ] Grafik toolbar butonlarını mobilde dokunulabilir boyuta getir
- [ ] Topbar sekmelerinde taşma/keşfedilebilirlik iyileştir
- **Dosya:** `frontend/style.css`

### H.3 Mali Analiz Kullanıcı Yönlendirmeleri
- [ ] Non-BIST sembollerde desteklenen BIST evrenine yönlendirme ekle
- [ ] Universe nokta renkleri için legend ekle
- [ ] BIST 30 yenileme için daha görünür loading/progress mesajı ekle
- **Dosya:** `frontend/src/components/MaliAnalizPanel.ts`

### H.4 Haberler Paneli Küçük UX
- [ ] Yenile sırasında butonda/metinde loading durumu göster
- [ ] Keyword input için Enter ile yenile davranışını sembol input ile eşitle
- [ ] URL olmayan haber kartlarının görsel durumunu ayır
- **Dosya:** `frontend/src/components/NewsPanel.ts`

### H.5 Screener Durum ve Zaman Bilgisi
- [ ] Cache boşken kullanıcıya açıklayıcı empty-state göster
- [ ] "Son tarama" timestamp'i ekle
- [ ] İşlem sütunu başlığını daha açık hale getir
- **Dosya:** `frontend/src/components/Screener.ts`

### H.6 Eğitim Paneli Okuma Deneyimi
- [ ] Kategori/makale değişiminde içerik scroll'unu başa al
- [ ] Boş indicator bridge çağrılarını engelle
- [ ] Mobilde eğitim sidebar toggle davranışı ekle
- **Dosya:** `frontend/src/components/EgitimlerPanel.ts`, `frontend/style.css`

---

## Sprint I — Tasarım Cilası, Performans ve Teknik Borç

### I.1 Marka ve Topbar Tutarlılığı
- [ ] "Tema" adını "Görünüm" yap
- [ ] PiyasaPilot marka adının tüm shell/public sayfalarda tutarlı olduğunu doğrula
- [ ] Status badge mobilde kesilmeyecek şekilde düzenle
- **Dosya:** `frontend/index.html`, `frontend/style.css`

### I.2 Tema Dışı Dialog ve Scrollbar
- [ ] Kalan `window.alert()`/`window.confirm()` kullanımlarını tema uyumlu UI ile değiştir
- [ ] Firefox için genel scrollbar stilleri ekle
- **Dosya:** `frontend/src/**/*.ts`, `frontend/style.css`

### I.3 Emoji İkon Temizliği
- [ ] Sık kullanılan toolbar/action emoji ikonlarını inline SVG/lucide eşdeğerleriyle değiştir
- [ ] MultiChart sync lock ikonlarını platform bağımsız hale getir
- **Dosya:** `frontend/src/components/*.ts`

### I.4 Light Mode Kontrast QA
- [ ] Paper banner, wallet kartları, grafik paneli ve haber kartlarının light mode kontrastını kontrol et
- [ ] Gerekli CSS tokenlarını düzelt
- **Dosya:** `frontend/style.css`

### I.5 Performans ve Test Sertleştirme
- [ ] Ana bundle/chunk boyutunu ölç; gerekirse public/terminal chunk ayrımını iyileştir
- [ ] Python API testlerinde auth kaynaklı 401 uyumsuzluğunu test fixture veya header ile düzelt
- [ ] Playwright smoke ile kritik terminal/public rotaları doğrula
- **Dosya:** `frontend/src/app.ts`, `tests/`, `frontend/tests/e2e/`
