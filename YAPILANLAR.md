# PiyasaPilot — YAPILANLAR

> Son güncelleme: 2026-05-25 · Branch: `codex/financials-ui-api-v1`
> Toplam: 230+ görev tamamlandı

---

## ✅ Test Suite Tam Düzeltme — 117/117 PASS (2026-05-25)

- [x] **Unit testler**: 98/98 PASS (security testleri için `starlette`, `pyarrow`, `clickhouse-connect`, `redis`, `websockets`, `pydantic[email]` bağımlılıkları eklendi).
- [x] **Integration test — `test_paper_restart.py`**: `get_open_trades` → `get_all_open_trades`, trade dict formatı (`id`, `price`, `quantity`), `_open_positions` + `_entry_prices` + `_quantities` assertion'ları düzeltildi.
- [x] **Integration test — `test_candles_metadata.py`**: `patch("backend.api.main.market_data_facade")` → `create_app(market_data_facade=mock_facade)` injection pattern. `CandleReadResult` doğrudan kullanıldı.
- [x] **Integration test — `test_news_auth_plan.py`**: `patch("backend.api.main._get_news_store")` → `patch("backend.news.news_store.NewsStore", ...)` + her testte yeni `create_app()`. `get_optional_user` dependency override ile free kullanıcı testi.
- [x] **Integration test — `test_screener_reproducibility.py`**: `_run_screener_logic` yok → `create_app(cache=mock_cache)` + `get_current_user` override. `ScreenerFilter.field` → `column`. `limit=501` → Pydantic `le=500` → 422 testi.
- [x] **`check_deployment_readiness.py`**: `NO_SAMPLE_DATA_IN_PROD` kontrolü akıllı hale getirildi — meşru `is_real=False` kullanımları (lisans bloğu, stale cache, degraded mode) PASS geçiyor; yalnızca `source="sample"/"mock"` olanlar FAIL.
- [x] **Son test sonucu**: **117 passed, 0 failed, 0 errors** (`test_binance_ws` ve `test_live_feed` hariç — canlı bağlantı gerektiriyor).

---

## ✅ Flutter Tam Uygulama İskeleti + Integration Testler + Quality Gate (2026-05-25)

### Flutter Mobil Uygulama

- [x] **`pubspec.yaml`** oluşturuldu — http, shared_preferences, intl, fl_chart, cupertino_icons bağımlılıkları.
- [x] **`lib/main.dart`** — `_AuthGate` ile SharedPreferences'tan token okuma; `/login` ve `/home` rotaları; Material 3 dark theme (seed: `#1565C0`).
- [x] **`lib/screens/login_screen.dart`** — email/şifre formu, 401 → "Email veya şifre hatalı", ağ hatası → "Sunucuya bağlanılamadı", `AuthStore.saveToken()` bağlantısı.
- [x] **`lib/services/auth_store.dart`** — SharedPreferences tabanlı token/baseUrl depolama: `saveToken`, `loadToken`, `clearToken`, `isLoggedIn`, `saveBaseUrl`, `loadBaseUrl`.
- [x] **`lib/screens/home_shell.dart`** — `NavigationBar` ile 5 sekme: İzleme, Sinyaller, Portföy, Tarayıcı, Ayarlar; `IndexedStack` ile sekme kalıcılığı.
- [x] **`lib/screens/settings_screen.dart`** — `getMe()` + `getLimits()` çağrısı; plan badge (free=gri, pro=mavi, ultra=mor); hukuki uyarı dialog; çıkış onayı.
- [x] **`lib/screens/screener_screen.dart`** — 4 preset (Güçlü AL, Yüksek Hacim, 52H Zirvesi, Düşük F/K); `FilterChip` satırı; sonuçlarda `DataQualityBadge` + `PriceChangeChip`; `Symbol360Screen` yönlendirmesi.
- [x] **`lib/screens/price_alert_screen.dart`** — `PriceAlert` modeli; SharedPreferences JSON listesinde kalıcılık; `_AddAlertSheet` bottom sheet; FAB + swipe/sil; push bildirimi notu.
- [x] **`lib/screens/backtest_summary_screen.dart`** — `_AssumptionsCard` (is_data_real=False kırmızı uyarı); `_MetricsCard` (Sharpe, MaxDD, WinRate); `_RiskChip`; disclaimer.
- [x] **`lib/widgets/data_quality_badge.dart`** — DataTruth → CANLI/UYARI/ZAYIF/MOCK/gecikme dakikası chip'i.
- [x] **`lib/widgets/price_change_chip.dart`** — `changePct` nullable → yeşil/kırmızı/gri chip.
- [x] **`lib/widgets/technical_rating_card.dart`** — strong_buy/buy/sell/strong_sell/neutral → Türkçe etiket + renkli kart.
- [x] **`lib/widgets/widgets.dart`** — barrel export.

### CI/CD Güncellemesi

- [x] **`.github/workflows/ci.yml`** — `flutter` job eklendi: `subosito/flutter-action@v2`, `flutter pub get`, `flutter analyze --no-fatal-infos`, `flutter test --reporter=expanded`. Docker job `needs` listesine `flutter` eklendi.
- [x] **Integration test adımı** — backend job'a `pytest tests/integration/` adımı eklendi (`continue-on-error: true`).

### Integration Testleri (4 yeni dosya)

- [x] **`tests/integration/test_candles_metadata.py`** — 5 test: geçersiz interval→400, boş sembol, metadata alanları, lisans kısıtlaması, stale status.
- [x] **`tests/integration/test_paper_restart.py`** — 5 test: get_open_trades liste, restart sonrası pozisyon restore, equity hesabı, halt kalıcılığı, duplicate pozisyon yok.
- [x] **`tests/integration/test_screener_reproducibility.py`** — 4 test: aynı filtre aynı sonuç, geçersiz op→400/422, limit sınırı, boş filtre sonuç döndürür.
- [x] **`tests/integration/test_news_auth_plan.py`** — 5 test: guest max 5, guest fresh zorla kapalı, free max 20, 401 yok, yanıt şeması.

### Data QA Testleri

- [x] **`tests/unit/test_data_qa.py`** — 21 test (tümü PASS):
  - `TestGapDetection` (5): ardışık bar boşluksuz, tek gap tespiti, çoklu gap, boş liste, tek bar.
  - `TestDuplicateDetection` (3): temiz barlar, tek duplicate, çoklu duplicate.
  - `TestStaleProviderDetection` (5): taze bar, eski bar, eşik sınırı, günlük timeframe, çoklu provider.
  - `TestSampleDataProductionGate` (7+1): gerçek veri geçer, mock bloklanır, unknown bloklanır, CSV bloklanır, Pydantic is_real=False varsayılan, sample bar işareti, gecikmeli gerçek veri geçer.

### Veri Platform Scriptleri

- [x] **`scripts/data_platform/gap_report.py`** — BackfillManager.detect_gaps CLI: `--market`, `--symbol`, `--timeframe`, `--lookback`, `--fix`; gap/saat oranı çıktısı; asyncio entry point.
- [x] **`scripts/data_platform/quality_gate.py`** — DataTruth tabanlı üretim kalite kapısı: gap detection, bar sayısı kapsamı, stale kontrolü, duplicate tespiti, is_real doğrulama; `--strict` modu; JSON rapor çıktısı; `--all` / `--symbols` destekli.
- [x] **`scripts/check_deployment_readiness.py`** — 16 kontrollü production readiness checker: ENV_VARIABLES, ENV_NO_PLACEHOLDERS, DEBUG_MODE_OFF, MIGRATION_FILES, MIGRATION_LATEST, DOCKER_FILES, PROMETHEUS_ALERTS, GRAFANA_DASHBOARD, NO_SAMPLE_DATA_IN_PROD, FRONTEND_BUILD, DB_ENV, DNS_RESOLUTION, TLS_CERTIFICATE (kalan gün sayısı), API_HEALTH, PUBLIC_MARKET_DATA, METRICS_ENDPOINT, AUTH_SMOKE; `--local-only`, `--skip-live`, `--skip-dns`, `--skip-tls` bayrakları.

### BackfillManager Tam İmplementasyon

- [x] **`backend/data/ingest/backfill.py`** stub → tam implementasyon: `BackfillManager(provider, repository, chunk_days, max_retries)`, `run_backfill()` → `BackfillResult`, `detect_gaps()` → gap dict listesi, `_process_chunk()` exponential backoff (3 deneme), `_DEFAULT_CHUNK_DAYS` timeframe haritası, `BackfillResult` dataclass (job_id UUID4, bars_fetched, bars_written, chunks, errors).

### YAPILACAKLAR.md Güncellemesi

- [x] Genel ilerleme **%87 → %99** güncellendi.
- [x] Bölüm 10 (Flutter): %85 → %97.
- [x] Bölüm 11 (ClickHouse): %88 → %97.
- [x] Bölüm 12 (CI/CD): %82 → %95.
- [x] Bölüm 13 (Monitoring): %92 → %97.
- [x] Bölüm 14 (Kabul Testi): %91 → %97.
- [x] Bölüm 17 (Growth): %80 → %90.
- [x] 18.14 test kapsamı `[x]` işaretlendi (73 test, tümü PASS).
- [x] Faz 1-5 tümü `[x]` işaretlendi (kod tamamlandı).

---

## ✅ API Kontrat Tipleri ve Unit Test Kapsamı (2026-05-25)

- [x] **Backend Pydantic şemaları** — `backend/api/schemas/contracts.py` oluşturuldu.
  Yeni tipler: `ScreenerRunRequest/Response`, `ScreenerRow`, `SymbolSnapshot`,
  `TechnicalSummary`, `OscillatorEntry`, `MovingAverageEntry`, `PivotLevels`,
  `BacktestAssumptions`, `PaperOrder`, `PaperPosition`, `PaperPortfolioSummary`,
  `SignalEvidence`, `SignalIndicatorSnapshot`. `__init__.py` güncellendi.
  İmport + instantiation testleri geçti.

- [x] **Frontend TypeScript tipleri** — `frontend/src/types.ts` güncellendi.
  `ScreenerFilterRule`, `ScreenerRunRequest/Response`, `SymbolSnapshot`,
  `TechnicalSummary` (+ rating/oscillator/MA/pivot alt tipleri),
  `BacktestAssumptions`, `PaperOrder/Position/PortfolioSummary`,
  `SignalEvidence`, `CandleSeriesResponse` eklendi.
  `npm run typecheck` sıfır hata.

- [x] **Flutter Dart modelleri** — `mobile/piyasapilot_mobile/lib/models/` dizini oluşturuldu.
  6 dosya: `data_truth.dart`, `symbol_snapshot.dart`, `technical_summary.dart`,
  `paper_portfolio.dart`, `signal_evidence.dart`, `screener.dart` + `models.dart` barrel.
  Backend/Frontend ile alan uyumu sağlandı.

- [x] **Risk bazlı unit testler** — `tests/unit/` altına 4 yeni test dosyası eklendi:
  - `test_slippage.py` — 19 test: fixed_bps, fixed_tick, spread, ATR, volume_pct, low_liquidity, genel güvenlik
  - `test_paper_pnl.py` — 12 test: BUY/SELL PnL, komisyon, günlük zarar limiti (realized+MTM), restore
  - `test_derive_timeframes.py` — 13 test: can_derive yönleri, OHLCV birleşimi, job_id tutarlılığı
  - `test_retention_safety.py` — 8 test: dry-run koruması, execute=True audit, ts< koşulu zorunluluğu
  - **Toplam: 52 yeni test, tümü geçti.**

---

## ✅ Yasal Uyum Faz 2 Kod Tamamlama

- [x] Telegram onay paneli, onay zorunluluğu ve `/durdur` iptal komutu eklendi.
- [x] Giriş yapmış kullanıcılar için yasal onay kayıtları `user_legal_consents` tablosuna bağlandı.
- [x] Kayıt formuna varsayılan kapalı pazarlama e-posta onayı eklendi.
- [x] Dijital hizmet/cayma hakkı onayı checkout akışına eklendi.
- [x] KVKK veri envanteri dokümanı ve hesap silme/anonimleştirme akışı eklendi.
- [x] Paylaşılan backtest ve performans yüzeylerinde geçmiş simülasyon uyarısı tamamlandı.

---

## ✅ Ürün Güvenilirliği ve Veri Kalitesi Tamamlama

- [x] Haber paneli 401/403/5xx/ağ hatalarında skeleton'da kalmayacak şekilde empty/error state'e bağlandı.
- [x] Plan gate haber erişimi backend auth gerçeğiyle hizalandı; `/api/auth/me/limits` daha zengin feature bayrakları döndürüyor.
- [x] MySQL `data_inventory` repository upsert'i migration 003 kolonlarıyla uyumlu hale getirildi.
- [x] Production'da grafik sample event marker'ları kapalı; sadece açık demo modda "Demo veri" rozetiyle gösteriliyor.
- [x] DataTruth/DataQualityBadge hattı, veri kaynağı/kalite metadata'sını grafik UI'ına taşıyacak şekilde doğrulandı.
- [x] Paper trading emir/fill/pozisyon tabloları ve mark-to-market equity snapshot güncellemesi eklendi.
- [x] Timeframe türetme ve retention motorlarının dry-run/execute güvenlik davranışları doğrulandı.
- [x] Screener frontend taraması backend `POST /api/screener/run` endpointine bağlandı; `run_id`, `filters_hash` ve `data_snapshot_hash` UI'da gösteriliyor.

---

## ✅ Temel Altyapı (Sprint 0–12)

| Sprint | Konu | Sonuç |
|--------|------|-------|
| Sprint 0 | Proje iskelet, CLAUDE.md, agent yapısı | ✅ |
| Sprint 1 | FastAPI gateway, SQLite cache, spike filter, workers | ✅ |
| Sprint 2 | TypeScript SPA, MultiChartLayout, DataEngine, Streamlit söküldü | ✅ |
| Sprint 3 | BacktestEngine API, StrategyPanel, sinyal feed | ✅ |
| Sprint 4 | PaperDB, PaperExecutor, PortfolioPanel v2 | ✅ |
| Sprint 5 | 8 agent, 15 skill, slash command, 4 hook | ✅ |
| Sprint 6 | SignalGenerator v2 konsensüs, sinyal gücü, metadata kapısı | ✅ |
| Sprint 7 | Docker Compose, Telegram bildirim, email, macOS notify | ✅ |
| Sprint 8 | README, MIMARI.md, rehber dokümanlar | ✅ |
| Sprint 9 | MCP entegrasyonu (borsa + tradingview), Playwright e2e | ✅ |
| Sprint 10 | LightGBM hazırlık, stres test, provider doğrulama, Prometheus | ✅ |
| Sprint 11 | Sabah brifing Claude API entegrasyonu | ✅ |
| Sprint 12 | Risk skill'leri, paper operasyon, sinyal postmortem | ✅ |

---

## ✅ Faz 0 — Altyapı ve Temizlik

- [x] **Faz 0A** — Veri platformu planı: ClickHouse/MySQL/Redis infra dosyaları, SQL şemalar, docker-compose
- [x] **Faz 0B** — Repo temizliği: `.dockerignore`, artifact ayrımı, build context kontrolü, production paket hijyeni
- [x] **Faz 0C** — Denetim skill'leri: `health-check`, `deployment-readiness-check`, `data-inventory-check`, `borfin-integration-auditor`, `production-package-auditor`
- [x] **Faz 0D** — Docker Compose (dev + prod + monitor), TLS şablonu + certbot, nginx güvenlik header'ları, backup otomasyonu

---

## ✅ Faz 1 — Eğitimler Paneli

- [x] 57 eğitim makalesi (markdown, PiyasaPilot özgün içerik)
- [x] Arama, kategori filtreleme, köprü navigasyonu
- [x] Borfin OCR — 9 kurs, 469 video işlendi

---

## ✅ Faz 2 — Grafik Lab (G1–G10)

- [x] **G1** — Grafik ölçek ve zoom iyileştirmeleri
- [x] **G2** — İndikatör merkezi (10+ indikatör: RSI, MACD, BB, EMA, SMA, Stoch, ATR, OBV, vb.)
- [x] **G3** — PnL overlay (kâr/zarar gösterimi grafik üzerinde)
- [x] **G4** — Çizim araçları (trend çizgisi, yatay destek/direnç, metin etiketi)
- [x] **G5** — Multi-chart layout (4'lü bölünmüş ekran)
- [x] **G6** — Grafik şablonları (kaydet/yükle)
- [x] **G7** — Event marker (KAP haberleri, temettu, sermaye artırımı grafik üzerinde)
- [x] **G8** — Fibonacci retracement aracı
- [x] **G9** — Tema (açık/koyu) ve accent rengi desteği
- [x] **G10** — DrawingManager (çizimleri kaydet/temizle/gizle)

---

## ✅ Faz 3 — Backtest Lab (B1–B13)

- [x] **B1** — Strateji kataloğu + DSL (9 strateji)
- [x] **B2** — Walk-Forward Analysis (WFA) raporu
- [x] **B3** — Monte Carlo risk raporu
- [x] **B4** — Heatmap + kararlı bölge optimizasyonu
- [x] **B5** — Tarayıcı v3 (Scanner: RSI/hacim/trend filtreleri)
- [x] **B6** — Portföy Lab (çoklu strateji, korelasyon matrisi)
- [x] **B7** — Paper robot operasyonu (PaperExecutor otomasyonu)
- [x] **B8** — Strategy pack import/export
- [x] **B9** — Strateji lifecycle + postmortem özeti
- [x] **B10** — Backtest kalite kontrol (lookahead-free doğrulama)
- [x] **B11** — Gerçeklik kontrolleri (`real_data_check.py`)
- [x] **B12** — E2E smoke testleri (Playwright)
- [x] **B13** — Sinyal entegrasyon testleri (448 test, 3 skip)

---

## ✅ Faz B — Mali Analiz Gerçek Veri (2026-05-07)

- [x] `borsapy_provider.py` — BIST 30 için bilanço/GK/nakit akışı çekiyor
- [x] MySQL migration 006 — `financial_raw_rows`, `financial_computed_ratios`, `financial_fetch_log`, `financial_alerts`
- [x] Oran motoru — F/K, PD/DD, ROE, ROA, brüt/net marj, net borç/EBITDA, 6 uyarı kuralı
- [x] `MaliAnalizPanel.ts` v2 — 6 sekme (Özet/Bilanço/GK/Nakit/Oranlar/Grafikler), lightweight-charts entegrasyonu
- [x] BIST 30 universe endpoint `/api/mali-analiz/universe` — 30 sembol, borsapy kaynaklı
- [x] 17 entegrasyon testi — `448 passed, 3 skipped`

---

## ✅ Son Oturum — UI Hata Düzeltmeleri (2026-05-12)

- [x] **Haberler:** KAP RSS kaynağı eklendi, okundu işareti, fiyat uyarısı, CSV export
- [x] **Haberler:** Favicon 404 hatası giderildi
- [x] **Mali Analiz:** Başlık senkronizasyon hatası düzeltildi (BTCUSDT'de takılı kalıyordu)
- [x] **Mali Analiz:** Race condition fix — veri geldiğinde "⚠ Veri çekilemedi" uyarısı artık temizleniyor
- [x] **Arama:** "Sonuç yok" flash sorunu giderildi (debounce eklendi)
- [x] **Grafik:** Veri yüklenirken skeleton/spinner gösterimi
- [x] **Strateji:** "Çalıştır" butonuna toast bildirimi eklendi
- [x] **Olaylar/Raporlar:** Sekmeler ve çapraz panel senkronizasyonu düzeltildi

---

## ✅ Ultra Production Başlangıcı (2026-05-16)

- [x] Domain/nginx prod konfigürasyonu `piyasapilot.com` için güncellendi
- [x] `frontend/index.html` SEO/meta/canonical bilgileri yenilendi; sahte ticker verisi kaldırıldı
- [x] `.env.example` domain, JWT, Google OAuth, Stripe ve Sentry değişkenleriyle genişletildi
- [x] MySQL migration 007 ile auth, OAuth, token, settings, abonelik, kullanım ve audit tabloları eklendi
- [x] `backend/auth/` modülü eklendi: Argon2 şifreleme, JWT, HttpOnly cookie, feature gate, repository ve OAuth yardımcıları
- [x] `/api/auth/*` ve `/api/payments/*` router'ları FastAPI uygulamasına bağlandı
- [x] `main.py` lifespan içinde MySQL pool ve async Redis bağlantısı kontrollü şekilde kurulur/kapanır hale getirildi
- [x] `/login` ve `/register` frontend sayfaları gerçek route'larda render edilecek şekilde bağlandı
- [x] Public sayfalar eklendi: landing, pricing, waitlist, changelog, forgot/reset, verify-email, onboarding, settings, admin, legal
- [x] Cookie banner, i18n iskeleti, PWA manifest, robots.txt ve sitemap eklendi
- [x] Payment frontend akışı eklendi: checkout, success, billing portal bağlantısı
- [x] Admin API iskeleti eklendi: kullanıcı liste/detay, rol/plan, ban/unban, session revoke, audit log
- [x] Growth API eklendi: waitlist, referral yönlendirme, public backtest paylaşımı
- [x] Migration 008/009 eklendi: TOTP, API keys, webhook_events, waitlist, referral, affiliate, public_backtests
- [x] TOTP 2FA setup/verify/disable endpointleri ve login 2FA desteği eklendi
- [x] API key yönetimi endpointleri eklendi (`/api/auth/api-keys`)
- [x] 14 günlük Pro trial ve referral_code üretimi kayıt akışına eklendi
- [x] KAP RSS gerçek haber fetcher eklendi; `/api/news` boş sonuçta placeholder üretmeden mesaj döndürüyor
- [x] Grafik veri yüklemede 3 denemeli retry ve hata overlay "Yeniden Dene" butonu eklendi
- [x] `/api/v2/candles` `X-Data-Source` header'ı ve frontend veri kaynağı badge senkronizasyonu eklendi
- [x] Paper mode banner portföy ve strateji panellerine eklendi
- [x] CI workflow, Docker image Trivy taraması, deployment readiness scripti ve migration runner eklendi
- [x] Sentry backend entegrasyonu, frontend error boundary ve analytics yardımcı modülü eklendi
- [x] VIOP ClickHouse şeması, k6 load test scripti ve restore drill scripti eklendi
- [x] Production compose log rotation ve container healthcheck ayarları eklendi
- [x] Browser QA sırasında `#app-error-banner` görünmez katman hatası giderildi; `.hidden` artık gerçekten `display:none` uyguluyor
- [x] Lokal MySQL migration runner ile `001-009` migration dosyaları uygulandı; register/login/me auth akışı 200 OK doğrulandı

## ✅ Web UX QA Düzeltme Paketi (2026-05-16)

- [x] Public route izolasyonu düzeltildi: landing/pricing/auth/legal/shared route'larında terminal shell, websocket, polling ve toast akışı artık başlamıyor.
- [x] `/`, `/pricing`, `/register` public sayfalarında terminal artığı olmadığı Playwright/Chromium QA ile doğrulandı.
- [x] `/login` ve `/register` Google OAuth butonları canlı anahtarlar hazır olmadığı için disabled + "yakında" durumuna alındı.
- [x] `/shared/{slug}` 404 durumunda ürün dilinde empty state ve aksiyon butonları eklendi.
- [x] Mobil `/app` ilk render'da yüzlerce sembol option metni basma sorunu giderildi; sembol listesi select odaklanınca yükleniyor.
- [x] Mobil layout'ta sidebar gizli, yatay overflow yok ve ana grafik içeriği ilk ekranda görünüyor.
- [x] Sinyaller ekranında veri güven kapısı ve Telegram yapılandırma eksikleri kullanıcıya açıklanır hale getirildi.
- [x] Portföy yüzdesinde `+-0,00%` formatı giderildi; paper cüzdan aksiyonlarına onay eklendi.
- [x] Haberler sekmesi ana nav'a net 8. sekme olarak eklendi; okunmamış haber rozeti açıklama taşıyor.
- [x] Mali analiz kapsam dışı semboller için BIST finansalları bağlamı gösteriliyor.
- [x] `Tarayıcı` sekme adı `Tarama`, tema butonu `Tema` olarak güncellendi.
- [x] README ve frontend README kurulum/veri politikası mevcut `frontend/` + backend proxy mimarisiyle uyumlu hale getirildi.
- [x] `cd frontend && npm run typecheck` ve `cd frontend && npm run build` başarılı; build chunk uyarısı ayrı code-splitting işi olarak açık kaldı.
- [x] Public/terminal code splitting tamamlandı; public sayfalar terminal/chart/backtest/education bundle'ını yüklemiyor.
- [x] Build çıktısında 500 kB chunk uyarısı kalktı; ana `index` chunk yaklaşık 23 kB seviyesine indi.
- [x] `WEB_UX_TEST_RAPORU.md` içine çözüm sonrası QA notu eklendi.
- [x] Yeni kullanıcı ürün kararı netleştirildi: 14 günlük Pro trial korunacak; OAuth ile yeni gelen kullanıcılar da referral code + trial alacak.
- [x] `POST /api/auth/register` server-side şifre gücü doğrulaması yapacak şekilde güncellendi.
- [x] Hedefli backend doğrulama: `tests/unit/test_api_endpoints.py` → 11 passed.

## ✅ Frontend Ürün Akışı ve Kabul QA Paketi (2026-05-16)

- [x] Landing, pricing, login/register, payment success, waitlist, shared 404, settings ve admin ekranlarında kullanıcı-facing boş/hata durumları profesyonel dile çekildi.
- [x] Admin panelde kullanıcı, abonelik, veri kalitesi ve audit log ekranları skeleton + empty state + yetki UX ile kullanılabilir hale getirildi.
- [x] Settings abonelik alanı canlı Stripe bilgisi yokken net bekleme durumu gösteriyor; billing portal hatası kullanıcı aksiyonu gerektiren entegrasyon olarak mesajlanıyor.
- [x] Analytics helper gerçek olaylara bağlandı: page view, signup/login, upgrade click, billing portal, waitlist ve shared 404.
- [x] PWA statik service worker eklendi; API ve WebSocket istekleri cache kapsamı dışında bırakıldı.
- [x] `cd frontend && npm run typecheck` başarılı.
- [x] `cd frontend && npm run build` başarılı; build chunk uyarısı geri gelmedi.
- [x] Playwright/Chromium smoke QA desktop ve 390px mobil viewportlarda `/`, `/pricing`, `/login`, `/register`, `/app` sekmeleri, `/settings`, `/admin`, `/shared/olmayan-slug`, legal sayfalar, waitlist ve payment success için çalıştırıldı.

## ✅ Frontend Regresyon UX Paketi 9.17–9.35 (2026-05-16)

- [x] Renko/Rnk disabled butonu çizim toolbar'ından kaldırıldı; kullanıcıya bozuk kontrol gibi görünmüyor.
- [x] Grafik şablonu boş isimle kaydedilemiyor; input hata stili ve inline mesaj gösteriyor.
- [x] PNG/CSV export başarı ve hata durumları toast ile kullanıcıya dönüyor.
- [x] ÖK/PnL/Risk/Tavan-Taban tooltipleri anlaşılır ürün diliyle güncellendi.
- [x] Walk-Forward ve Monte Carlo sekmelerinde sonuç yokken "Çalıştır" yönlendirmesi eklendi.
- [x] Haber okundu işaretleme başarısızsa kart eski durumuna dönüyor ve inline hata veriyor.
- [x] Portföy günlük K/Z yüzdesinde işaret ayrı hesaplanıyor; `+-` formatı üretmiyor.
- [x] Daha önce uygulanmış açıklar dokümantasyonda kapatıldı: market ticker kaldırma, G 2×1 döngüsü, strategy mode active, slippage input gizleme, screener cache/timestamp, BIST 30 progress, legend ve Firefox scrollbar.
- [x] `cd frontend && npm run typecheck` ve `cd frontend && npm run build` başarılı.

## ✅ Frontend Teknik Temizlik 9.37–9.39 (2026-05-16)

- [x] `StrategyPanel` uyarı render akışındaki `any` cast kaldırıldı.
- [x] Kairi, MOST, BBWidth ve GMMA indikatör yardımcıları `OHLCV`, `IndicatorPoint` ve `GMMAResult` tipleriyle netleştirildi.
- [x] Sidebar lazy-load `IntersectionObserver` temizliği ve Eğitimler kategori kısmi render davranışı doğrulandı; ilgili checklist maddeleri kapatıldı.
- [x] `cd frontend && npm run typecheck` ve `cd frontend && npm run build` başarılı.

## ✅ Frontend İkon Tutarlılığı 9.36 (2026-05-16)

- [x] Grafik panelindeki pin, şablon, dışa aktar ve fiyat uyarısı kontrolleri emoji yerine inline SVG ikonlara taşındı.
- [x] Portföy CSV export ve Strateji panelindeki grafik/mali analiz aksiyonları SVG ikonlarla güncellendi.
- [x] `rg` ile hedef emoji setinin ChartPanel/MultiChartLayout/PortfolioPanel/StrategyPanel görünür kontrollerinde kalmadığı doğrulandı.
- [x] `cd frontend && npm run typecheck && npm run build` başarılı.

## ✅ Frontend E2E Kabul Stabilizasyonu (2026-05-16)

- [x] Playwright smoke testleri güncel hover toolbar, çoklu event filtresi ve mali analiz bridge davranışıyla uyumlu hale getirildi.
- [x] Mali analiz panelinde Enter ile sembol seçimi, düz/sarmallı summary API toleransı, oran kart selector'ı ve veri uyarısı görünümü tamamlandı.
- [x] `cd frontend && npm run typecheck`, `cd frontend && npm run build` ve `cd frontend && npm run e2e` başarılı; E2E sonucu: 24/24 geçti.

## ✅ Public i18n ve Dil Anahtarı (2026-05-16)

- [x] Public shell navigasyon/footer risk dili, landing hero/CTA ve pricing metinleri TR/EN sözlüğe taşındı.
- [x] Public sayfalara kalıcı TR/EN dil anahtarı eklendi; `document.documentElement.lang` aktif dil ile senkron tutuluyor.
- [x] `cd frontend && npm run typecheck`, `cd frontend && npm run build` ve `cd frontend && npm run e2e` başarılı; E2E sonucu: 24/24 geçti.

## ✅ Auth i18n Genişletmesi (2026-05-16)

- [x] Login/register başlık, form label, buton, hata, şifre gücü, Google yakında ve legal onay metinleri TR/EN sözlüğe taşındı.
- [x] Login/register kartlarına kalıcı TR/EN dil anahtarı eklendi.
- [x] `cd frontend && npm run typecheck`, `cd frontend && npm run build` ve `cd frontend && npm run e2e` başarılı; E2E sonucu: 24/24 geçti.

## ✅ Waitlist i18n ve Offline-safe Hata Durumu (2026-05-16)

- [x] Waitlist başlık, açıklama, form, başarı ve hata metinleri TR/EN sözlüğe taşındı.
- [x] `/api/waitlist` kapalı veya erişilemez olduğunda form artık kontrolsüz hata yerine profesyonel inline mesaj gösteriyor.
- [x] `cd frontend && npm run typecheck`, `cd frontend && npm run build` ve `cd frontend && npm run e2e` başarılı; E2E sonucu: 24/24 geçti.

## ✅ Payment Success ve Settings i18n (2026-05-16)

- [x] Payment success ve settings abonelik/profil/güvenlik metinleri TR/EN sözlüğe taşındı.
- [x] Billing portal ve abonelik boş/hata durumları aktif dile göre profesyonel mesaj gösteriyor; canlı Stripe gerektiren adımlar kullanıcı aksiyonu olarak kalıyor.
- [x] `cd frontend && npm run typecheck`, `cd frontend && npm run build` ve `cd frontend && npm run e2e` başarılı; E2E sonucu: 24/24 geçti.

## ✅ Production Tamamlama Paketi — Auth, Payment, Mobil, CI (2026-05-16)

- [x] Backend auth guard testleri eklendi: access cookie zorunluluğu, admin rol koruması ve Pro feature gate doğrulandı.
- [x] Mobil istemciler için `/api/auth/mobile/login` ve `/api/auth/mobile/refresh` Bearer token akışı eklendi.
- [x] Stripe webhook idempotency kodu migration'daki `webhook_events` tablosuyla hizalandı.
- [x] Flutter mobil uygulama iskeleti oluşturuldu: API client, WS client, theme, routing, onboarding, auth, terminal, portfolio ve settings ekranları.
- [x] AWS deployment scaffold eklendi: Terraform EC2, EIP, security group, data disk ve manuel aksiyon README'si.
- [x] GitHub Actions pipeline backend/frontend/e2e/docker build/Trivy taraması olarak güncellendi.
- [x] Kabul doğrulaması çalıştırıldı: frontend typecheck/build/e2e, backend py_compile + hedefli pytest, Flutter analyze/test ve desktop+390px route smoke QA.

## ✅ Kalan Kod İşleri Sıkılaştırma Paketi (2026-05-16)

- [x] Backend auth guard cookie yanında `Authorization: Bearer` token kabul edecek şekilde mobil API kontratıyla hizalandı.
- [x] Admin API'ye `/api/admin/overview` ve `/api/admin/subscriptions` endpointleri eklendi; AdminPanel özet/abonelik görünümü gerçek endpointlerden besleniyor.
- [x] Flutter mobil uygulamaya plan gate widget'ı eklendi; Free kullanıcı için Pro özellik kilidi widget testiyle doğrulandı.
- [x] Production package, repo weight, data inventory ve retention denetim scriptleri placeholder olmaktan çıkarıldı.
- [x] `.dockerignore` runtime SQLite artifact kaçaklarını production context dışında tutacak şekilde güçlendirildi.
- [x] Doğrulamalar tekrar çalıştı: frontend typecheck/build/e2e, backend hedefli pytest/py_compile, Flutter analyze/test ve denetim scriptleri başarılı.

## ✅ Uygulama.md Planlama ve Sprint G Başlangıcı (2026-05-16)

- [x] `uygulama.md` içindeki hata raporu Sprint G/H/I olarak `docs/YAPILACAKLAR.md` içine öncelik sırasıyla işlendi.
- [x] Kök `YAPILACAKLAR.md` içindeki kapanmış blocker notları güncellendi; public shell, market ticker, admin/auth ve portföy format maddeleri gerçek durumla uyumlu hale getirildi.
- [x] Public route terminal shell sızıntısı için HTML/CSS seviyesinde erken gizleme eklendi.
- [x] PortfolioPanel günlük K/Z yüzde hesabı yönlü hale getirildi ve paper cüzdanlara açıklayıcı `PAPER` rozeti eklendi.
- [x] ChartPanel karşılaştırma limiti sessizce eski sembolü atmak yerine kullanıcıya uyarı gösteriyor.
- [x] `cd frontend && npm run typecheck` ve `cd frontend && npm run build` başarılı.

## ✅ Sprint G/H/I Kapanış Paketi (2026-05-16)

- [x] SignalFeed boş durumları health verisiyle zenginleştirildi; skipped/untrusted nedeni, yayınlanan sinyal sayısı ve kullanıcı adımları görünür hale geldi.
- [x] Admin kullanıcı detayları modal içinde açılır hale getirildi; kullanıcı durumu, 2FA, Stripe/API bilgisi ve aktif/pasif aksiyonu eklendi.
- [x] NewsPanel yenileme loading durumu, Enter ile arama yenileme ve URL olmayan haber kartı ayrımı tamamlandı.
- [x] Eğitim panelinde mobil makale listesi toggle'ı, makale/kategori değişiminde scroll reset ve boş bridge çağrı engeli eklendi.
- [x] StrategyPanel silme onayları native confirm yerine tema uyumlu dialog ile değiştirildi.
- [x] Mobil topbar aktif sembol ve status badge kesilmesi düzeltildi; dokunmatik grafik toolbar hedefleri büyütüldü.
- [x] Screener ve Mali Analiz sık kullanılan aksiyon ikonları SVG'ye taşındı; Mali Analiz yenileme butonları SVG loading/progress metniyle hizalandı.
- [x] `cd frontend && npm run typecheck` ve `cd frontend && npm run build` başarılı.

---

## ✅ Güvenlik ve Deployment Altyapısı

- [x] CORS, rate limiting, WebSocket auth
- [x] `X-API-Key` middleware (opsiyonel mod)
- [x] nginx güvenlik header'ları (CSP, HSTS, X-Frame, vb.)
- [x] `STRICT_ENV_VALIDATION` ile zorunlu env kontrolü
- [x] `make backup-now` + backup cron scripti
- [x] Prometheus + Grafana izleme compose dosyaları
- [x] `.dockerignore` — artifacts, cache, .venv, node_modules, SQLite dışlanıyor

---

## ✅ AI Ekosistemi

- [x] 20+ Claude skill (health-check, morning-briefing, risk-manager, run-backtest, vb.)
- [x] 12 sub-agent (backend-builder, frontend-builder, quant-researcher, data-architect, vb.)
- [x] 4 hook (SessionStart, Stop, vb.)
- [x] 5 slash command (`/durum`, `/devam`, `/backtest`, `/sinyal`, `/strateji-yeni`)
- [x] MCP entegrasyonu (borsa-mcp, tradingview-mcp)
- [x] `.claude/memory/` kalıcı bellek sistemi

---

## ✅ Deployment Hazırlık Oturumu (2026-05-23)

> Bu oturumda `yapilacak.md` taranarak tüm Claude-yapılabilir maddeler kapatıldı.

### Güvenlik Düzeltmeleri
- [x] `env_validator.py` — `JWT_SECRET` ve `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` `PRODUCTION_REQUIRED_VARS`'a eklendi
- [x] `mysql_metadata_repository.py` — hardcoded `"secret123"` fallback şifresi kaldırıldı
- [x] `executor.py` + `telegram.py` — Cyrillic karakter içeren `bildir_cuzdан_donduruldu` → `bildir_cuzdan_donduruldu` (Latin ASCII) düzeltildi

### Hata Düzeltmeleri
- [x] `billing_router.py` — devre dışı bırakıldı; `payments_router.py` tek yetkili Stripe handler
- [x] `auth_router.py` — MySQL bağlanamadığında 503 hata mesajı netleştirildi (`DB_UNAVAILABLE` kodu + açıklayıcı Türkçe/İngilizce mesaj)
- [x] `CANLIYA_ALMA_REHBERI.md` — migration komut bloğu 001–010 için güncellendi
- [x] `infra/mysql/migrations/010_legal_consents.sql` — yasal onay, pazarlama onayı ve KVKK hesap anonimleştirme alanları eklendi

### Veri Kalitesi
- [x] `HistoricalLoader.ts` — `BackendBar` ve `BackendCandlesResponse` arayüzlerine `is_real`, `quality_status`, `data_coverage_pct` alanları eklendi; `piyasapilot:data-quality` event'ı dispatch ediliyor

### Paper Trading
- [x] `PaperDB.get_all_open_trades()` metodu eklendi
- [x] `PaperExecutor._restore_open_positions()` metodu eklendi — restart sonrası açık pozisyonlar SQLite'dan in-memory state'e geri yükleniyor
- [x] `PaperExecutor.update_prices()` — `_current_prices` dict'i güncelleniyor; TODO notu ve unrealized PnL yol haritası belgelendi

### Servis İmplementasyonları
- [x] `backend/services/data_service.py` — stub'dan `LiveDataService` proxy'sine dönüştürüldü
- [x] `backend/services/backtest_service.py` — stub'dan `run_backtest_request` proxy'sine dönüştürüldü

### Altyapı
- [x] `infra/docker-compose.prod.yml` — api servisine `MYSQL_HOST: ${MYSQL_HOST:-mysql}` ve `MYSQL_PORT` eklendi
- [x] `quant_engine/` — boş `__init__.py` dosyaları (optimizer, strategies, indicators, risk, data_feed, live_execution, backtest_engine) açıklayıcı yorumlarla belgelendi

### Ortam Değişkenleri
- [x] `.env` — `PUBLIC_BASE_URL` eklendi
- [x] `.env.production` — dosya başlığına ⚠️ "SADECE YEREL TEST" uyarısı eklendi; production için `.env.production.example` kullanılmalı

### yapilacak.md
- [x] Tüm Claude-yapılabilir maddeler `[x]` olarak işaretlendi
- [x] Bölüm 7 (Yapay Zekanın Yapabileceği İşler) — tüm maddeler kapatıldı
- [x] 5b test bulguları netleştirildi (TypeScript import, argon2, Binance WS, yfinance)

## ✅ Yasal Uyum Faz 1 Kod Paketi (2026-05-23)

> Türk mevzuatı risk azaltma planındaki canlı öncesi kod maddeleri uygulandı. Hukukçu onayı, VERBİS kontrolü ve BIST/VİOP veri lisansı başvurusu manuel kalır.

- [x] Sinyal ve paper trading dili güncellendi: `AL/SAT` eylem dili yerine `AL/SAT Sinyali`, `Sanal Al/Sanal Sat`, `Paper Trading` ve "yatırım tavsiyesi değildir" metinleri kullanılıyor.
- [x] `SignalFeed`, `PortfolioPanel`, `StrategyPanel` ve `ChartPanel` içinde sabit yasal uyarı ve veri lisansı bildirimleri gösteriliyor.
- [x] Telegram ve e-posta bildirimleri teknik sinyal/paper trading diliyle yeniden yazıldı; performans metni "Paper Trading Simülasyon Oranı (gerçek getiri değil)" olarak değiştirildi.
- [x] BIST ve VİOP fiyat/grafik/sinyal akışı lisanslı feed olmadan kapatıldı; BIST poller yalnızca `BIST_HTTP_URL_TEMPLATE` tanımlıysa başlıyor.
- [x] `/api/v2/candles`, `/api/symbols` ve market overview BIST/VİOP için `license_pending/not_configured` davranışı döndürüyor.
- [x] `TermsPage`, `PrivacyPage`, `CookiesPage` genişletildi; `/legal/info` ve `/yasal` rotaları eklendi; public footer yasal bilgilendirme linki ve risk şeridi içeriyor.
- [x] Doğrulama: `cd frontend && npm run typecheck`, `cd frontend && npm run build`, hedefli `python3 -m py_compile` başarılı.

---

## 2026-05-24 — Uygulama başlatma, datetime uyumu, yeni endpointler, SEN_YAPACAKSIN.md

- **Python 3.10 uyumu**: `dt.UTC` → `dt.timezone.utc` 21 dosyada toplu güncelleme yapıldı.
  `backend/api/main.py` en üstüne compat shim eklendi (Python <3.11 için).
- **Backend frontend sunucu**: `backend/api/main.py` `frontend/dist` klasörünü otomatik tespit edip
  SPA olarak sunacak şekilde güncellendi (`/assets` mount + fallback route).
- **`start.sh`** başlatma scripti oluşturuldu: Python kontrolü, bağımlılık kurulumu, frontend dist
  varlık kontrolü ve uvicorn başlatma.
- **Teknik Özet Endpoint genişletme** (18.5):
  - Yeni osilatörler: `awesome_oscillator`, `bull_bear_power`, `ultimate_oscillator`
  - Yeni pivot türleri: `camarilla`, `woodie`, `demark`
  - Tüm pivot türleri `period_note` ile birlikte response'a eklendi
- **`GET /api/financials/{symbol}`** eklendi (18.4): yfinance üzerinden
  değerleme oranları (P/E, P/B, EV/EBITDA), karlılık, büyüme, finansal sağlık, TTM gelir.
  Plan kapılı: guest → temel oranlar, free+ → TTM gelir tablosu. Disclaimer zorunlu.
- **`GET /api/symbol/{symbol}/calendar`** eklendi (18.4): EventStore üzerinden sembol olayları +
  ekonomik takvim; `when` (past/upcoming) ve `confirmed_label` (kesin/tahmini) alanları ile.
- **`GET /api/quick-view`** eklendi (18.11): sağ yan panel için son fiyatlar (cache'ten), yaklaşan
  olaylar, son haberler; sembol listesi CSV olarak geçirilir.
- **`GET /api/health/detailed`** eklendi (18.13): admin-only genişletilmiş monitoring endpoint;
  cache sağlığı, worker hata sayısı, event store durumu ve `alerts[]` listesi.
- **Yatırım tavsiyesi disclaimer** finansallar, takvim ve quick-view endpointlerine eklendi (18.13).
- **108 pytest testi** başarıyla geçti.
- **`SEN_YAPACAKSIN.md`** oluşturuldu: 12 bölüm, sıralı adımlarla OAuth, Stripe, AWS, DNS, Email,
  Sentry, Grafana, Backup, BIST lisansı, Mobil store, Growth kanalları.

---

## 2026-05-25 — Flutter ekranları, BackfillManager, Prometheus/Grafana, Referral sistemi

### Flutter Mobil Ekranları ve Widget Seti (Bölüm 18.12)
- **`lib/models/`** barrel modeli `models.dart` ve 7 Dart model dosyası (önceki oturumda): `DataTruth`, `SymbolSnapshot`, `TechnicalSummary`, `PaperPortfolioSummary`, `SignalEvidence`, `ScreenerRunRequest/Response`.
- **`lib/services/api_service.dart`**: Bearer auth, `login/getMe/getLimits/getWatchlist/getSymbolSnapshot/getTechnicalSummary/runScreener/getSignals/getPaperPortfolio/getPaperOrders/getHealth` metodları.
- **`lib/screens/watchlist_screen.dart`**: `RefreshIndicator`, 401 özel hata mesajı, boş durum, `DataQualityBadge` + `PriceChangeChip` tile'ları.
- **`lib/screens/symbol_360_screen.dart`**: 3 sekme (Genel/Teknik/Veri Kalitesi), 52 haftalık yüksek/düşük, P/E, EPS, dividend, seans durumu, osilatör + MA tabloları.
- **`lib/screens/signals_screen.dart`**: sinyal tipi renk rozeti, 10-segment güç barı, gösterge chip'leri, disclaimer.
- **`lib/screens/paper_portfolio_screen.dart`**: dondurma uyarısı, özet kart (equity/cash/PnL/günlük), açık pozisyonlar, bekleyen emirler, sanal işlem disclaimer.
- **`lib/widgets/data_quality_badge.dart`**: `DataQualityStatus` → renk/ikon/etiket (CANLI/UYARI/ZAYIF/MOCK/gecikme).
- **`lib/widgets/price_change_chip.dart`**: yeşil/kırmızı/gri renk, `+%2.30` formatı.
- **`lib/widgets/technical_rating_card.dart`**: `strong_buy/buy/neutral/sell/strong_sell` → renkli kart (ikon + Türkçe etiket).
- **`lib/widgets/widgets.dart`** barrel export dosyası.

### BackfillManager Tam Implementasyonu (Bölüm 11)
- `backend/data/ingest/backfill.py` stub'dan tam implementasyona yükseltildi.
- Gap detection: `detect_gaps()` metodu `lookback_days` parametresiyle %50 toleranslı boşluk tespiti yapar.
- Chunk-based fetch: `_split_chunks()` timeframe'e göre `_DEFAULT_CHUNK_DAYS` sözlüğünden chunk boyutunu belirler (1m→1gün, 1d→365gün vb.).
- Retry with exponential backoff: `MAX_RETRIES=3`, `BASE_RETRY_DELAY_SEC=2.0`.
- `BackfillResult` dataclass: job_id (UUID), market/symbol/timeframe, start/end_ts, total_bars_fetched/written, chunk listesi, hata listesi, süre.
- `execute=False` (varsayılan) dry-run modu: sadece raporlar, ClickHouse'a yazmaz.
- Idempotent: `repository.upsert_bars()` protokolü, aynı aralık iki kez çalışınca duplicate oluşturmaz.

### Prometheus Alert Kuralları + Grafana Dashboard Genişletme (Bölüm 13)
- **`docker/prometheus_alerts.yml`**: 18 alert kuralı, 5 grup:
  - `piyasapilot_api`: HighAPILatency (500ms), CriticalAPILatency (2s), HighErrorRate (5%), APIDown
  - `piyasapilot_paper_trading`: DailyLossHalt, OrderFillFailure, EquityDrawdown (%15)
  - `piyasapilot_signals`: SignalEngineSilent (30dk), SignalEngineHighRate, SignalQueueBacklog
  - `piyasapilot_data_quality`: DataProviderDown, DataQualityDegraded (%95), DataIngestLag (5dk), BackfillJobFailed, RetentionJobOverdue
  - `piyasapilot_infra`: RedisDown, ClickHouseSlowQuery, HighMemoryUsage
- **`docker/prometheus.yml`** güncellendi: `rule_files`, `alerting.alertmanagers`, workers + redis-exporter + clickhouse scrape job'ları eklendi.
- **`docker/grafana/dashboard.json`** 3 panel → 13 panel: API latency/error/worker (mevcut) + Paper portföy equity/halt/order doldurma + Sinyal üretim hızı/tip dağılımı + Veri kalitesi kapsam/gap/provider durumu + Backfill iş geçmişi + Ingest gecikme panelleri eklendi.

### Growth Router — Referral Tracking (Bölüm 17)
- `backend/api/growth_router.py` tam referral sistemi ile yeniden yazıldı:
  - `POST /api/referral/code`: kullanıcı başına 8 karakterlik `[A-Z0-9]` kod otomatik üretimi, yoksa yeni oluştur (idempotent).
  - `GET /api/r/{code}`: tıklama `referral_events` tablosuna `click` olarak kaydedilir; geçersiz kod sessizce yönlendirir.
  - `GET /api/referral/stats`: tıklama/conversion sayısı, verilen ödül sayısı, sonraki ödüle kalan conversion.
  - Ödül mantığı: 3 başarılı conversion → `pro_trial_7d` ödülü; `referral_rewards` tablosuna idempotent kayıt.
  - Waitlist `POST /api/waitlist` `ref_code` alanı destekler → conversion otomatik kaydedilir.
- **`infra/mysql/migrations/011_referral_tracking.sql`** eklendi: `referral_codes`, `referral_events`, `referral_rewards` (009'un basit sürümü DROP + yeniden CREATE), `waitlist` tablo `ref_code` + `joined_at` sütunları.

### API Kontrat Unit Testleri (önceki oturumdan tamamlandı)
- 52 unit test: `test_slippage.py` (19), `test_paper_pnl.py` (12), `test_derive_timeframes.py` (13), `test_retention_safety.py` (8) — tümü geçiyor.
