# PiyasaPilot — YAPILANLAR

> Son güncelleme: 2026-05-16 · Branch: `codex/financials-ui-api-v1`
> Toplam: 151 görev tamamlandı

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

- [x] Domain/nginx prod konfigürasyonu `piyasapilotu.com` için güncellendi
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
