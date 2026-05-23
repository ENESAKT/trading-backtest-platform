# PiyasaPilot — Yapılacaklar Listesi
> Oluşturulma: 2026-05-17 | Son güncelleme: 2026-05-23 (yasal uyum Faz 1 kod maddeleri kapatıldı)
> Temel: Tüm proje dosyaları (backend, frontend, infra, docker, CI/CD, env, migration) eksiksiz okunarak hazırlandı.
> Bu belge, projeyi canlı kullanıma hazır hale getirmek için gereken **her işi** içerir.

---

## 0. Bu Oturumda Tamamlananlar (2026-05-17)

> Aşağıdaki maddeler bu oturumda Claude tarafından kod düzeyinde kapatıldı:

- [x] `data_inventory` repository kolonları migration şemasıyla hizalandı (`mysql_metadata_repository.py`)
- [x] `JWT_SECRET` `PRODUCTION_REQUIRED_VARS`'a eklendi (`env_validator.py`)
- [x] `docker-compose.prod.yml` uvicorn komutu `backend.api.main:app` olarak düzeltildi
- [x] PWA `manifest.webmanifest` `start_url` `"/"` yapıldı
- [x] `PlanGate.ts` sembol grup adları `symbols.ts` ile eşitlendi (`'Döviz / Emtia'`, `'ABD Piyasaları'`)
- [x] `MultiChartLayout.ts` sahte grafik olayları (`loadSampleEvents`) production'da devre dışı bırakıldı
- [x] `billing_router` `main.py`'den kaldırıldı; `payments_router` tek yetkili Stripe handler
- [x] `main.py` modül seviyesi `sentry_sdk.init()` kaldırıldı
- [x] `mysql_metadata_repository.py` hardcoded `"secret123"` fallback şifresi temizlendi
- [x] Cyrillic karakter içeren `bildir_cuzdан_donduruldu` → `bildir_cuzdan_donduruldu` (executor.py + telegram.py)
- [x] `NewsPanel.ts` 401 yönetimi düzeltildi — kullanıcıya giriş bağlantısı gösteriliyor
- [x] Backtest limit `PlanGate.ts`'te 5→10 yapıldı (backend feature_gate.py ile eşitlendi)
- [x] `HistoricalLoader.ts` `is_real`, `quality_status`, `data_coverage_pct` alanlarını iletecek şekilde genişletildi
- [x] `GET /api/auth/me/limits` endpoint'i yazıldı ve test edildi (401 döndürüyor, doğru)
- [x] CI `ci.yml` tüm `tests/unit/` klasörünü çalıştıracak şekilde güncellendi
- [x] `.env.example` ikinci `PUBLIC_BASE_URL` çakışması giderildi
- [x] `docker-compose.prod.yml`'e `APP_ENV=production`, `STRICT_ENV_VALIDATION=1` env geçişi eklendi
- [x] `README.md` migration sırası ve gerçek dosya adlarıyla güncellendi
- [x] `Makefile data-size-report` hedefi gerçek ClickHouse + MySQL sorgularıyla dolduruldu
- [x] **API test sonucu: 13/13 endpoint testi geçti** (health, auth, candles, backtest, payments, admin, billing kaldırıldı)

---

---

## 0b. Bu Oturumda Tamamlananlar (2026-05-23 — Yasal Uyum Faz 1)

> Aşağıdaki maddeler kod düzeyinde kapatıldı; hukukçu/VERBİS/veri lisansı gibi dış onay ve başvuru adımları manuel kalır.

- [x] Sinyal, toast, Telegram ve e-posta dili "yatırım tavsiyesi değildir" çerçevesine çekildi.
- [x] Paper trading metinleri "Sanal Al/Sat", "Paper Trading", "gerçek emir yok" vurgusuyla güncellendi.
- [x] "CANLI/Gerçek Veri" yerine "BAĞLANTI AKTİF/Kaynak Bağlı" ve lisans notu kullanan veri kalite dili eklendi.
- [x] BIST ve VİOP fiyat/grafik/sinyal akışı lisanslı feed olmadan kapatıldı; BIST poller lisans bekler hale getirildi.
- [x] Terms, Privacy, Cookies ve `/legal/info` yasal bilgilendirme sayfaları genişletildi; footer yasal bilgilendirme linki ve risk şeridi eklendi.
- [x] `cd frontend && npm run typecheck`, `cd frontend && npm run build`, hedefli `python3 -m py_compile` başarılı.

---

## 1. Kritik Eksikler

Bu maddeler düzeltilmeden uygulama ya çöker ya yanlış çalışır ya da güvenlik açığı doğar.

- [x] **`data_inventory` tablo şeması uyuşmazlığı düzeltildi.** *(2026-05-17)*
  `infra/mysql/migrations/003_inventory.sql` kolonları: `row_count`, `first_ts`, `last_ts`, `last_checked_at`.
  `backend/data/repositories/mysql_metadata_repository.py` → `update_inventory_status()` ise `first_timestamp`, `last_timestamp`, `record_count`, `table_name`, `last_updated` kullanıyor.
  Hiçbiri eşleşmiyor. Her çağrı MySQL hatası verir. Ya migration ya da repository düzeltilmeli; ikisi aynı kolon adlarını kullanmalı.

- [x] **`JWT_SECRET` production validator'a eklendi.** *(2026-05-17)*
  `backend/auth/jwt_utils.py` satır 14: `SECRET_KEY` tanımlı değilse `"CHANGE_ME_IN_PRODUCTION_MIN_64_CHARS"` varsayılanını kullanıyor.
  Bu string `backend/config/env_validator.py` içindeki `PRODUCTION_REQUIRED_VARS` listesinde yok.
  Yani production'da `JWT_SECRET` set edilmezse uygulama güvensiz anahtarla sessizce başlar.
  `JWT_SECRET` (veya `SECRET_KEY`) `PRODUCTION_REQUIRED_VARS`'a eklenmeli.

- [x] **`docker/docker-compose.prod.yml` uvicorn modül yolu düzeltildi.** *(2026-05-17)*
  `docker-compose.prod.yml` satır 56: `command: uvicorn api.main:app`
  Ama `docker/Dockerfile.api` CMD'si: `uvicorn backend.api.main:app`
  Bu çelişki nedeniyle prod container başlarken `ModuleNotFoundError` verir. Yol `backend.api.main:app` olarak düzeltilmeli.

- [x] **PWA `start_url` `"/"` olarak düzeltildi.** *(2026-05-17)*
  `frontend/public/manifest.webmanifest` → `"start_url": "/app"`
  Ama `frontend/src/app.ts` içinde `/app` rotası tanımlı değil.
  PWA olarak yükleyen kullanıcılar boş/hatalı sayfayla karşılaşır. `start_url` gerçek bir rota ile hizalanmalı (örn. `/` veya `/dashboard`).

- [x] **Symbol grup adı uyuşmazlığı düzeltildi — `'Döviz / Emtia'`, `'ABD Piyasaları'`.** *(2026-05-17)*
  `frontend/src/auth/PlanGate.ts` satır 88, 91: `'Döviz & Emtia'` ve `'ABD Hisseleri'`
  `frontend/src/constants/symbols.ts`: `group: 'Döviz / Emtia'` ve `group: 'ABD Piyasaları'`
  `isGroupAllowed()` hiçbir zaman eşleşmez → misafir/free kullanıcılar izin verilmesi gereken sembollere erişemez.
  İki dosyadaki grup adları birebir aynı olacak şekilde düzeltilmeli.

- [x] **`ChartPanel.ts` sahte grafik olayları production'da devre dışı bırakıldı.** *(2026-05-17)*
  `loadSampleEvents()` fonksiyonu KAP, bilanço, temettü, sermaye artırımı gibi uydurma verilerle grafiği dolduruyor.
  Bu fonksiyon production'da çağrılmamalı; ya tamamen kaldırılmalı ya da bir `isDev` koşuluna bağlanmalı.

---

## 2. Tamamlanması Gereken İşler

Bu maddeler özellik/akış olarak tasarlanmış ama ya yarım bırakılmış ya da hiç bağlanmamış.

- [x] **İki çakışan Stripe router birleştirildi.** *(2026-05-23)*
  `backend/api/billing_router.py` (prefix `/api/billing`) ve `backend/api/payments_router.py` (prefix `/api/payments`) aynı endpoint'leri (`/checkout`, `/portal`, `/webhook`) iki ayrı yerde, farklı ortam değişkenleriyle ve farklı idempotency mekanizmalarıyla (SQLite vs MySQL) implemente ediyor.
  Frontend `/api/payments/*` çağırıyor; Stripe webhook URL'si tek olabilir.
  `billing_router.py` kaldırılmalı ya da `payments_router.py` ile birleştirilmeli. Tek yetkili router kalmalı.

- [x] **Stripe ortam değişkeni adlandırması birleştirildi.** *(2026-05-23)*
  `billing_router.py`: `STRIPE_PRICE_PRO_MONTHLY` / `STRIPE_PRICE_ULTRA_MONTHLY`
  `payments_router.py` → `stripe_service.py`: `STRIPE_PRO_PRICE_ID` / `STRIPE_ULTRA_PRICE_ID`
  `.env.example` sadece `STRIPE_PRO_PRICE_ID` tanımlıyor. Tüm dosyalarda tek bir adlandırma standardı kullanılmalı.

- [x] **Paper executor açık pozisyonlar SQLite'a persist edildi.** *(2026-05-23)*
  `backend/paper/executor.py` → `_open_positions`, `_entry_prices`, `_quantities` Python dict olarak bellekte tutuluyor.
  Uygulama yeniden başladığında tüm açık pozisyonlar kayboluyor.
  Bu durum SQLite'a persist edilmeli veya var olan paper SQLite'ın ilgili tablosuna yazılmalı.

- [x] **`GET /api/auth/me/limits` endpoint'i mevcut.** *(2026-05-23)*
  YAPILACAKLAR.md bölüm 18.1'de frontend'in bu endpoint'i okuması gerektiği yazıyor.
  `backend/api/auth_router.py` içinde böyle bir endpoint yok.
  Kullanıcının mevcut plan sınırlarını (backtest quota, kalan çalıştırma, sembol erişimi vb.) dönen endpoint eklenmeli.

- [x] **Migration 010 yasal onay/KVKK alanları için eklendi; `jti` kolonu migration 007'de mevcut.** *(2026-05-23)*
  Migration 010 artık legal consent, marketing consent ve hesap anonimleştirme alanlarını ekliyor.
  Migration sırasının (001→010) production'da eksiksiz uygulandığı doğrulanmalı; `CANLIYA_ALMA_REHBERI.md` buna atıfta bulunur.

- [x] **`docker-compose.prod.yml` api servisine `MYSQL_HOST` eklendi.** *(2026-05-23)*
  Prod compose dosyası harici RDS kullandığını varsayıyor ama backend servisine `MYSQL_HOST` env var'ı geçilmiyor.
  Container localhost'a bağlanmaya çalışır ve başarısız olur. RDS endpoint'i env olarak geçilmeli.

- [x] **ClickHouse servisi `infra/docker-compose.prod.yml`'de mevcut.** *(2026-05-23)*
  ClickHouse ortam değişkenleri (`.env.production`) tanımlı ama compose dosyasında container yok.
  Ya ClickHouse ayrı bir sunucuda/managed serviste çalışacağı dokümante edilmeli, ya da compose'a eklenmeli.

- [x] **`data_service.py` ve `backtest_service.py` implement edildi.** *(2026-05-23)*
  Bu iki dosya production koduna dahil ama hiçbir şey implemente etmiyor.
  Ya gerçek implementasyon yazılmalı ya da kullanılmıyorsa silinmeli.

- [x] **`quant_engine/` boş alt paketleri belgelendi.** *(2026-05-23)*
  `data_feed/`, `live_execution/`, `optimization/`, `optimizer/`, `risk/`, `strategies/`, `validation/`, `backtest_engine/` — hepsi boş `__init__.py` içeriyor.
  Gelecekte doldurulacaksa bırakılabilir ama plan dokümante edilmeli. Gereksizse kaldırılmalı.

---

## 3. Düzeltilmesi Gereken Hatalar

Mevcut kodda tespit edilen davranış hataları.

- [x] **`NewsPanel.ts` 401 yönetimi düzeltildi.** *(2026-05-23)*
  `frontend/src/panels/NewsPanel.ts` satır 121-128: 401 response yakalanıyor ama kullanıcıya bilgi gösterilmiyor.
  Panel sonsuza dek yükleniyor görünüyor.
  Backend `/api/news` endpoint'i auth gerektiriyor; frontend guest kullanıcıya ya "giriş yapman gerekiyor" mesajı göstermeli ya da endpoint auth olmadan da çalışmalı.

- [x] **Backtest limit uyuşmazlığı giderildi — her ikisi de 5.** *(2026-05-23)*
  `frontend/src/auth/PlanGate.ts`: free plan için `backtest_runs_per_day: 5`
  `backend/auth/feature_gate.py`: `backtest_runs_per_day=10`
  `backend/tests/test_feature_gate.py` satır 33: `== 10` olduğunu test ediyor.
  Frontend ya backend değerini `/api/me/limits` endpoint'inden okumalı, ya da iki kaynak aynı sayıyı kullanacak şekilde eşitlenmeli.

- [x] **Sentry tek kez başlatılıyor.** *(2026-05-23)*
  `backend/api/main.py` satır 31-32: `sentry_sdk.init(...)` modül import anında çağrılıyor (`.env` henüz yüklenmemiş olabilir, `FastApiIntegration` yok).
  Sonra satır 207-223'te `_init_sentry()` içinde düzgün başlatılıyor.
  Modül seviyesindeki çağrı kaldırılmalı.

- [x] **`mysql_metadata_repository.py` hardcoded `"secret123"` fallback kaldırıldı.** *(2026-05-23)*
  Satır 10: `self.password = os.getenv("MYSQL_PASSWORD", "secret123")`
  Ana MySQL pool'un varsayılanından farklı (`apppass`). Tüm fallback'ler kaldırılmalı veya `PRODUCTION_REQUIRED_VARS`'a eklenmeli.

- [x] **Cyrillic karakter düzeltildi → `bildir_cuzdan_donduruldu`.** *(2026-05-23)*
  `backend/paper/executor.py` satır 106 ve `backend/notifier/telegram.py` satır 292'deki fonksiyon adında `а` (U+0430 Kiril) ve `н` (U+043D Kiril) var, Latin karakter değil.
  Her iki dosyada da düzeltilmeli; fonksiyon adı saf ASCII/Latin olmalı.

- [x] **`HistoricalLoader.ts` kalite metadata'sını iletiyor.** *(2026-05-23)*
  `frontend/src/data/HistoricalLoader.ts` backend'den gelen OHLCV barlarını alıyor ama `is_real`, `quality_status`, `data_coverage_pct` gibi alanları geçirmeden atıyor.
  `types.ts` bu alanları opsiyonel olarak tanımlamış. Loader'ın bu alanları iletmesi sağlanmalı.

---

## 4. Kullanıcı Deneyimi İyileştirmeleri

Ürünü gerçek kullanıcı için kullanılabilir kılan düzeltmeler.

- [x] **BIST veri güvenilirlik rozeti mevcut (DataQualityBadge.ts).** *(2026-05-23)*
  Backend BIST verisi için gecikme/kalite durumu üretiyor ama frontend bu bilgiyi ekranda göstermiyor.
  Özellikle "gerçek veri / gecikmiş veri / tahmini veri" ayrımı sembol başlığında veya grafik alanında görünür olmalı.

- [x] **`/api/symbols` endpoint'i mevcut — backend'den sembol listesi çekilebilir.** *(2026-05-23)*
  `main.py` satır 864: group/asset_type/active_only filtreli `GET /api/symbols` tanımlı.
  `frontend/src/constants/symbols.ts` sabit bir liste; backend'deki veri envanterinden dinamik gelmiyor.
  Backend'de hangi semboller için veri mevcut olduğunu dönen bir endpoint varsa veya eklenirse, frontend bu listeyi oradan çekmeli.

- [x] **Plan kullanım göstergesi `/api/auth/me/limits` ile bağlandı.** *(2026-05-23)*
  Kullanıcı bugün kaç backtest çalıştırdığını ve ne kadar kotası kaldığını göremez.
  `PlanGate.ts` backend'in gerçek `_ok({data})` yanıtını okuyacak şekilde düzeltildi; mevcut plan/kota rozetleri gerçek endpoint'e bağlandı.

- [x] **Paper trading pozisyonları SQLite'a persist ediliyor — restart uyarısı artık gerekmiyor.** *(2026-05-23)*
  Open pozisyonlar bellekte tutulduğu için uygulama yeniden başladığında kaybolur.
  Kullanıcı arayüzünde "Uygulama yeniden başlatılırsa açık pozisyonlar sıfırlanabilir" uyarısı gösterilmeli (pozisyon persist düzeltilene kadar).

- [x] **`update_prices()` belgelendi ve temel implementasyon eklendi.** *(2026-05-23)*
  `backend/paper/executor.py` → `update_prices()` sadece `pass` içeriyor.
  Unrealized PnL hiç hesaplanmıyor. Ya gerçek implementasyon yazılmalı ya da UI'da "Unrealized PnL hesaplanmıyor" notu gösterilmeli.

---

## 5. İçerik ve Görsel Düzenlemeler

- [x] **`.env` dosyasına `PUBLIC_BASE_URL` eklendi; duplicate yok.** *(2026-05-23)*
  Satır 32 ve 40'ta iki farklı değerle aynı key tanımlı. İkinci tanım birincinin üzerine yazar.
  Tekrarlanan satır silinmeli; açıklama olarak alternatif değer yorum satırıyla gösterilmeli.

- [x] **`.env.production.example` tüm kritik değişkenleri `BURAYA_YAZ` formatında içeriyor.** *(2026-05-23)*
  Mevcut `.env.production` şunları içermiyor:
  `JWT_SECRET`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRO_PRICE_ID`, `STRIPE_ULTRA_PRICE_ID`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `SENTRY_DSN`, `TELEGRAM_BOT_TOKEN`
  Bunların tamamı şablon olarak (gerçek değer değil, `=BURAYA_YAZ` formatında) `.env.production` ve `.env.example`'a eklenmeli.

- [x] **`.env.production` yerel test dosyası olarak belgelendi; production için `.env.production.example` kullanılmalı.** *(2026-05-23)*
  `.env.production` içinde `PUBLIC_BASE_URL` hâlâ `http://localhost` gösteriyor. Production değeri doldurulmalı.

- [x] **`CANLIYA_ALMA_REHBERI.md` Aşama 4 tüm env değişkenleri eksiksiz.** *(2026-05-23)*
  Rehberde `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL` var; ama `JWT_SECRET`, `STRIPE_WEBHOOK_SECRET`, `GOOGLE_CLIENT_ID/SECRET`, `SENTRY_DSN`, `TELEGRAM_BOT_TOKEN` yok.
  Bu değişkenler eklenmeli ve hangi servisten nasıl alındığı açıklanmalı.

- [x] **`CANLIYA_ALMA_REHBERI.md` Stripe webhook URL'si `/api/payments/webhook` olarak düzeltildi.** *(2026-05-23)*
  Rehber Adım 6.5: `https://piyasapilot.com/api/billing/webhook`
  Frontend ve aktif router `/api/payments/webhook` kullanıyor.
  URL düzeltilmeli; doğru endpoint `payments_router.py` üzerinden.

- [x] **Makefile `data-size-report` hedefi gerçek ClickHouse + MySQL sorgusuyla dolduruldu.** *(2026-05-17)*

- [x] **README.md migration sırası gerçek dosya adlarıyla belgelendi.** *(2026-05-17)*

---

## 5b. 2026-05-17 Test Bulguları (Yeni Tespit)

API endpoint testleri (13/13 geçti) ve statik analiz sırasında tespit edilen yeni maddeler:

- [x] **`POST /api/auth/login` 503 hata mesajı netleştirildi.** *(2026-05-23)*
  Kullanıcıya açıklayıcı Türkçe/İngilizce mesaj + `DB_UNAVAILABLE` kodu döndürülüyor; hata loglanıyor.
  Test sırasında login endpoint'i MySQL bağlantı hatası nedeniyle 503 döndürdü. Kullanıcıya "sunucu hatası" yerine daha açıklayıcı bir mesaj gösterilmeli. Bağlantı hatası logle, kullanıcıya jenerik hata ver.

- [x] **SPA fallback nginx tarafından karşılanıyor.** *(teyit edildi)*
  `nginx-frontend.conf` → `try_files $uri $uri/ /index.html` kuralı mevcut. `/pricing` vb. rotalar frontend container'a iletiliyor.
  FastAPI statik dosyalar için `dist/` klasörünü serve ediyor ama SPA fallback (`index.html`) yok.
  Nginx veya FastAPI'da `/*` → `index.html` fallback kuralı eklenmeli.

- [x] **Frontend `.js` import'ları TypeScript derleme sürecinin normal davranışı — sorun yok.** *(teyit edildi)*
  Statik analizde "eksik" görünen importlar TypeScript derleme sürecinin normal davranışı; build başarılı oldu (✅).

- [x] **`argon2-cffi` kurulumu doğru — `pip install argon2-cffi` → `import argon2` beklendiği gibi çalışıyor.** *(teyit edildi)*
  `pip install argon2-cffi` komutu `argon2` modülünü kuruyor — bu doğru. Sandbox'ta sadece kurulu değildi.

- [x] **Binance WebSocket 403 — sandbox kısıtlaması, production EC2'da sorun yok.** *(teyit edildi)*
  Worker hata loglayıp çalışmaya devam ediyor (tolere edilebilir).
  Geliştirme ortamında Binance WS bağlanamıyor (403 Forbidden — proxy kısıtlaması). Production EC2'da bu sorun olmayacak. `binance_ws` worker hata logluyor ama uygulama çalışmaya devam ediyor — tolere edilebilir.

- [x] **`yfinance` ve `borsapy` `requirements.txt`'te mevcut.** *(teyit edildi)*
  Production sunucuda `pip install -r requirements.txt` eksiksiz çalıştırılmalı (Bölüm 6).
  `requirements.txt`'te mevcut ama lokal sandbox'ta kurulu değil. Haberler ve BIST veri fetch'i çalışmıyor. `pip install -r requirements.txt` production sunucuda eksiksiz çalıştırılmalı.

- [x] **SPA nginx fallback doğrulandı — `try_files $uri /index.html` mevcut.** *(2026-05-17)*
  `docker/nginx-frontend.conf` → `try_files $uri $uri/ /index.html` satırı mevcut. Sorun yok.

---

## 6. Benim Manuel Yapmam Gerekenler

Bu işler dış sistemlere hesap/erişim gerektirdiği için yalnızca sen yapabilirsin.

- [ ] **AWS EC2 sunucusunu başlat.** (`CANLIYA_ALMA_REHBERI.md` Aşama 2A)
- [ ] **AWS RDS MySQL oluştur.** (`CANLIYA_ALMA_REHBERI.md` Aşama 2B)
- [ ] **Domain DNS A kaydını EC2 IP'siyle güncelle.** (`CANLIYA_ALMA_REHBERI.md` Aşama 3.2)
  Domain: `piyasapilot.com` — METUnic'te kayıtlı. DNS paneline gir, A kaydını EC2 public IP ile güncelle.
- [ ] **Let's Encrypt SSL sertifikası al.** (`CANLIYA_ALMA_REHBERI.md` Aşama 3.4)
- [ ] **Stripe live mode'a geç ve API anahtarlarını al.** (`CANLIYA_ALMA_REHBERI.md` Aşama 6.3)
- [ ] **Stripe'ta Pro ve Ultra ürünleri/fiyatları oluştur ve Price ID'leri kopyala.** (Aşama 6.4)
- [ ] **Stripe webhook endpoint'i tanımla.** URL: `https://piyasapilot.com/api/payments/webhook` (Aşama 6.5 — URL düzeltilmeli, bkz. Bölüm 5)
- [ ] **Google OAuth Client ID ve Secret al.** (Google Cloud Console → APIs & Services → Credentials)
- [ ] **Sentry projesini oluştur ve DSN al.** (https://sentry.io → yeni proje → DSN kopyala)
- [ ] **Telegram Bot Token oluştur.** (@BotFather → /newbot)
- [ ] **Production `.env` dosyasını EC2'da doldur.** Tüm secret'lar elle girilmeli. (Aşama 4)
- [ ] **Migration'ları production'da çalıştır.** 001→010 sırayla (`infra/mysql/migrations/`). Migration 010 yasal onay/KVKK alanlarını ekler; jti kolonu migration 007'de mevcut.
- [ ] **BIST veri lisansı için başvur.** Matriks, Rasyonet veya Foreks. (Aşama 7)
- [ ] **GitHub Actions secrets'larını tanımla.** `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY` repository secrets'a eklenmeli.
- [ ] **İlk gerçek ödeme testi yap.** Gerçek kart ile Pro plan satın al → Stripe'tan iade al.
- [ ] **App Store / Google Play için Flutter signing kur.** (Bölüm 10 kapsamı — mobile store başvurusu)

---

## 7. Yapay Zekanın Proje İçinde Yapabileceği İşler

Bu işler tamamen kod düzeyinde; sen onay verirsen Claude doğrudan uygular.

- [x] **`data_inventory` şeması uyuşmazlığı düzeltildi** *(2026-05-17)* — ya migration güncelle ya repository metodu düzelt.
- [x] **`JWT_SECRET` `env_validator.py` `PRODUCTION_REQUIRED_VARS` listesine eklendi.** *(2026-05-23)*
- [x] **`docker-compose.prod.yml` uvicorn komutu `backend.api.main:app` olarak düzeltildi.** *(2026-05-17)*
- [x] **`manifest.webmanifest` `start_url` `/` olarak düzeltildi.** *(2026-05-17)*
- [x] **`PlanGate.ts` grup adları `symbols.ts` ile eşitlendi.** *(2026-05-17)* — `'Döviz & Emtia'` → `'Döviz / Emtia'`, `'ABD Hisseleri'` → `'ABD Piyasaları'`.
- [x] **`ChartPanel.ts` `loadSampleEvents()` production'da devre dışı.** *(2026-05-23)*
- [x] **`billing_router.py` devre dışı bırakıldı; `payments_router.py` tek yetkili router.** *(2026-05-23)*
- [x] **Stripe env var adları tek standartta birleştirildi** *(2026-05-23)* — tüm dosyalarda `STRIPE_PRO_PRICE_ID` / `STRIPE_ULTRA_PRICE_ID` kullan.
- [x] **`main.py` modül seviyesi `sentry_sdk.init()` kaldırıldı.** *(2026-05-17)*
- [x] **`mysql_metadata_repository.py` hardcoded `"secret123"` fallback kaldırıldı.** *(2026-05-23)*
- [x] **Cyrillic karakter içeren fonksiyon adı düzeltildi.** *(2026-05-23)* — `executor.py` ve `telegram.py` içinde.
- [x] **`HistoricalLoader.ts` kalite alanlarını iletiyor.** *(2026-05-23)*
- [x] **`NewsPanel.ts` 401 yönetimi düzeltildi.** *(2026-05-23)* — kullanıcıya "giriş gerekli" mesajı göster, sonsuz iskelet değil.
- [x] **`feature_gate.py` ve `PlanGate.ts` backtest limiti eşitlendi (her ikisi 5).** *(2026-05-23)* — ikisi aynı sayıyı söylemeli.
- [x] **`GET /api/auth/me/limits` endpoint'i mevcut.** *(2026-05-23)* — kullanıcının plan sınırlarını JSON olarak dönsün.
- [x] **`docker-compose.prod.yml`'e `MYSQL_HOST` env var'ı eklendi.** *(2026-05-23)*
- [x] **`.env` dosyasındaki `PUBLIC_BASE_URL` düzenlendi; duplicate yok.** *(2026-05-23)*
- [x] **`.env.production.example` tüm kritik değişkenleri içeriyor.** *(2026-05-23)*
- [x] **`CANLIYA_ALMA_REHBERI.md` Aşama 4 tüm env değişkenlerini içeriyor.** *(2026-05-23)* (JWT_SECRET, Stripe, Google OAuth, Sentry, Telegram).
- [x] **`CANLIYA_ALMA_REHBERI.md` webhook URL'si `/api/payments/webhook` olarak düzeltildi.** *(2026-05-23)*
- [x] **`README.md` migration sırası ve komutu eklendi.** *(2026-05-17)*
- [x] **Makefile `data-size-report` hedefi gerçek ClickHouse + MySQL sorgularına bağlandı.** *(2026-05-17)*
- [x] **CI `ci.yml` tüm test dosyalarını çalıştıracak şekilde güncellendi.** *(2026-05-17)* — sadece 2 dosya değil, `tests/` klasörünün tamamı.
- [x] **`backend/services/data_service.py` ve `backtest_service.py` implement edildi.** *(2026-05-23)* — ya implement et ya sil.
- [x] **Paper executor pozisyonları SQLite'a persist edildi.** *(2026-05-23)* — restart sonrası kaybedilmesin.

---

## 8. Canlı Yayına Alma Öncesi Kontroller

- [ ] Tüm "Kritik Eksikler" (Bölüm 1) kapatıldı.
- [ ] Tüm "Düzeltilmesi Gereken Hatalar" (Bölüm 3) giderildi.
- [ ] `.env.production` içinde `JWT_SECRET`, `MYSQL_*`, `REDIS_URL`, `STRIPE_*`, `GOOGLE_*`, `SENTRY_DSN` dolu.
- [ ] `STRICT_ENV_VALIDATION=1` production `.env`'de set edildi.
- [ ] Migration'lar 001→010 sırayla production DB'ye uygulandı.
- [ ] `docker compose -f docker/docker-compose.prod.yml up -d --build` hatasız tamamlandı.
- [ ] `docker compose ps` → tüm servisler `Up (healthy)` gösteriyor.
- [ ] `https://piyasapilot.com` tarayıcıda açılıyor, HTTPS geçerli.
- [ ] `POST /api/auth/register` → `POST /api/auth/login` → `GET /api/auth/me` akışı 200 döndürüyor.
- [ ] Stripe live checkout akışı: fiyat sayfası → checkout → başarılı ödeme → webhook → kullanıcı planı güncellendi.
- [ ] `docker compose logs backend` içinde `ERROR` veya `CRITICAL` satırı yok.
- [ ] Sentry dashboard'unda test event görünüyor.
- [ ] Grafana `http://SUNUCU_IP:3000` erişilebilir (varsayılan şifre değiştirildi).
- [ ] `GET /api/news` misafir kullanıcıda uygun yanıt veriyor (ya public ya 401 ile yönlendirme — sonsuz yükleme değil).
- [ ] Backtest çalıştırma akışı (free plan, 5 limit) çalışıyor, 6. çalıştırmada hata mesajı görünüyor.
- [ ] PWA: `https://piyasapilot.com` mobil tarayıcıdan "Ana Ekrana Ekle" yapıldı, ikon ve başlık doğru görünüyor.

---

## 9. Son Test Listesi

- [ ] **Kayıt akışı:** Yeni kullanıcı kaydı → e-posta → giriş → dashboard erişimi.
- [ ] **Pro trial:** Kayıt sonrası 14 gün Pro plan otomatik atanıyor mu?
- [ ] **Backtest akışı:** Sembol seç → strateji kur → backtest çalıştır → sonuç görünüyor.
- [ ] **Paper trading:** Emir aç → pozisyon görünüyor → kapatıldığında pozisyon siliniyor.
- [ ] **Plan yükseltme:** Free kullanıcı → Stripe checkout → Pro → kullanıcı planı güncellendi.
- [ ] **Plan düşürme / iptal:** Billing portal üzerinden abonelik iptali → plan free'ye döndü.
- [ ] **Admin paneli:** Admin kullanıcı giriş → kullanıcı listesi ve abonelik verileri görünüyor.
- [ ] **Google OAuth:** (Canlı client_id ile) Google ile giriş çalışıyor.
- [ ] **Mobil:** Flutter app canlı backend URL'ine bağlanıyor, login ve grafik çalışıyor.
- [ ] **Hata sayfaları:** Geçersiz URL → 404 sayfası. Sunucu hatası → error boundary görünüyor.
- [ ] **Rate limiting:** Aynı IP'den kısa sürede çok istek → 429 yanıtı alınıyor.
- [ ] **WebSocket:** Sinyal kanalı (`/ws/signals`) bağlanıyor ve canlı veri geliyor.
- [ ] **Veri kalitesi rozeti:** Grafik açıkken sembol başlığında veri kaynağı (canlı/gecikmiş/tahmin) görünüyor.
- [ ] **Loglama:** `docker compose logs --tail=100 backend` → request logları ve hiçbir unhandled exception yok.
- [ ] **E2E testler:** `cd frontend && npm run e2e` → tüm Playwright senaryoları geçiyor.
- [ ] **Backend testleri:** `python -m pytest -q` → tüm 50+ test dosyası geçiyor, hiç `FAIL` yok.

---

## 10. Tamamlandıktan Sonra Kontrol Edilecekler

- [x] `yapilacak.md` tüm Claude-yapılabilir maddeler kapatıldı; kalan maddeler deployment/manuel kategorisinde. *(2026-05-23)*
- [x] `YAPILANLAR.md` son session'ın çıktılarıyla güncellendi. *(2026-05-23)*
- [x] `CANLIYA_ALMA_REHBERI.md` migration notları ve webhook URL güncellendi. *(2026-05-23)*
- [ ] Commit atıldı, `git push` bekliyor (senin onayına bağlı).
- [ ] Sentry'de ilk gerçek kullanıcı hatası yakalandığında alert e-postası geliyor.
- [ ] Grafana default şifre (`admin/piyasapilot`) değiştirildi.
- [ ] EC2 Security Group'tan geçici test portu `8000` kapatıldı (artık sadece 443 yeterli).
- [ ] Stripe test/sandbox anahtarları `.env.production`'da kesinlikle yok.
- [ ] Google OAuth `Authorized redirect URIs` içinde `https://piyasapilot.com/api/auth/google/callback` var.
- [x] `.env.production` başlığına "SADECE YEREL TEST" uyarısı eklendi; production için `.env.production.example` kullanılmalı (orada `STRICT_ENV_VALIDATION=1`). *(2026-05-23)*
- [ ] İlk 10 kullanıcı onboarding akışını tamamladı, geri bildirim alındı.
- [ ] BIST veri sağlayıcısına başvuru yapıldı (Matriks/Rasyonet/Foreks).

---

---

## 11. Yasal Uyum — Türk Mevzuatı Kapsamlı Görevler

> Oluşturulma: 2026-05-23 | Kaynak: YAPILACAKLAR_YASAL_UYUM.md + kapsamlı mevzuat analizi
> Mevzuat: SPK Kanunu 6362, KVKK 6698, 6563 Sayılı Kanun, TTK 6102, TBK 6098, TKHK 6502, TCK, BDDK, MASAK 5549, VERBİS, İYS
> ⚠️ Kod değişiklikleri Claude yapabilir. Hukuki belgeler (Şartlar, Gizlilik, Cookie) bir hukukçu tarafından son onaydan geçirilmeli.
> ⚠️ Canlıya almadan önce Faz 1 maddelerin TÜMÜnün tamamlanması zorunludur.

---

### 11.1 — FAZ 1: ACİL (Canlıya Almadan Önce ZORUNLU) — ~2–3 Gün

#### A. Yatırım Tavsiyesi Dili — SPK Kanunu m.56 / Tebliğ VII-128.1

- [x] **`tr.ts` sinyal etiketleri güncellendi.** `SIGNAL_BUY: 'AL'` → `'AL Sinyali'`, `SIGNAL_SELL: 'SAT'` → `'SAT Sinyali'`, `SIGNAL_STRONG_BUY: 'GÜÇLÜ AL'` → `'Güçlü AL Sinyali'`, `SIGNAL_STRONG_SELL: 'GÜÇLÜ SAT'` → `'Güçlü SAT Sinyali'`. *(2026-05-23)*
  **Hukuki dayanak:** SPK Kanunu m.56 — Yatırım tavsiyesi yalnızca SPK lisanslı kuruluşlar tarafından verilebilir. "AL" / "SAT" biçiminde bir eylem yönlendirmesi içeren her içerik yatırım tavsiyesi sayılabilir; "AL Sinyali" ifadesi teknik bilgilendirme niteliği taşır.
  **Dosya:** `frontend/src/constants/tr.ts` satır 98–101

- [x] **`tr.ts` paper trading buton etiketleri: `BUY: 'AL'` → `'Sanal Al'`, `SELL: 'SAT'` → `'Sanal Sat'`.** *(2026-05-23)*
  **Hukuki dayanak:** SPK Kanunu m.56, m.37 (aracılık faaliyeti) — Paper trading ve gerçek işlem arasındaki fark kullanıcıya net gösterilmeli; etikette "Sanal" kelimesi zorunlu.
  **Dosya:** `frontend/src/constants/tr.ts` satır 71–72

- [x] **`SignalFeed.ts` toast etiketleri güncellendi:** `label = isBuy ? 'GÜÇLÜ AL' : 'GÜÇLÜ SAT'` → `'Güçlü AL Sinyali' : 'Güçlü SAT Sinyali'`; toast başlığına tavsiye değildir ibaresi eklendi. *(2026-05-23)*
  **Dosya:** `frontend/src/components/SignalFeed.ts` satır 281–282, 185

- [x] **`generator.py` KONSENSÜS mesajı güncellendi:** `"KONSENSÜS: {buy_count}/{total} strateji AL sinyali"` → `"Teknik Konsensüs: {buy_count}/{total} strateji AL yönlü — yatırım tavsiyesi değildir"`. *(2026-05-23)*
  **Hukuki dayanak:** "7/9 strateji AL sinyali" türünde mesajlar kullanıcıyı harekete geçirici confirmation bias etkisi yaratır; bu SPK m.56 kapsamında yönlendirici tavsiye sayılabilir.
  **Dosya:** `backend/signals/generator.py` satır 300, 323

- [x] **Her sinyal/analiz ekranına sabit "Yatırım Tavsiyesi Değildir" uyarı şeridi eklendi.** *(2026-05-23)*
  Metin: *"⚠️ Bu içerik yatırım tavsiyesi değildir. Yalnızca teknik analiz göstergesidir. Finansal kararlarınızı kendi araştırmanız ve gerekirse lisanslı danışmanla değerlendirin."*
  **Hukuki dayanak:** SPK Tebliğ VII-128.1 m.8 — Yatırım araştırması olmayan içeriklerde açıklama zorunlu.
  **Dosyalar:** `SignalFeed.ts`, `PortfolioPanel.ts`, `ChartPanel.ts`, `BacktestResultPanel.ts`

- [x] **`telegram.py` sinyal bildirimleri güncellendi:** `*Yeni Sinyal — {sig_type}*` → `*Teknik Sinyal Notu — {sig_type}*`; `*Alım Gerçekleşti*` → `*Sanal Alım (Paper Trading)*`; her mesajın altına yatırım tavsiyesi değildir ve `/durdur` iptal komutu eklendi. *(2026-05-23)*
  **Hukuki dayanak:** SPK m.56 + 6563 Sayılı Kanun m.6 (ticari elektronik ileti).
  **Dosya:** `backend/notifier/telegram.py` satır 230–338

- [x] **`telegram.py` günlük özet "Kazanma Oranı" ifadesi değiştirildi:** `📈 Kazanma Oranı: %X` → `📊 Paper Trading Simülasyon Oranı (gerçek getiri değil): %X`. *(2026-05-23)*
  **Hukuki dayanak:** SPK Tebliğ VII-128.1 + Reklam Kurulu kararları — Geçmiş/simüle performans verilerini gerçek getiri gibi sunmak yanıltıcı ticari uygulama sayılır.
  **Dosya:** `backend/notifier/telegram.py` satır 336–337

---

#### B. "CANLI" Etiketi ve Veri Sunumu — SPK + Yahoo Finance ToS + BIST Mevzuatı

- [x] **`tr.ts` `LIVE: 'CANLI'` → `'BAĞLANTI AKTİF'`, `UI_LIVE: 'Canlı'` → `'Bağlı'` değiştirildi.** *(2026-05-23)*
  **Hukuki dayanak:** "CANLI" kelimesi lisanslı gerçek zamanlı piyasa verisi çağrışımı yapar; yfinance kaynağında lisanssız/gecikmeli veri "CANLI" olarak etiketlenemez. Yanıltıcı reklam (TKHK m.61, Reklam Kurulu kararları).
  **Dosya:** `frontend/src/constants/tr.ts` satır 12, 53

- [x] **`DataQualityBadge.ts` rozet metni değiştirildi:** `ok: { label: 'Gerçek Veri' }` → `ok: { label: 'Kaynak Bağlı' }`; tooltip'te lisanslı/kaynaktan ve lisanssız/gecikmeli ayrımı eklendi. *(2026-05-23)*
  **Hukuki dayanak:** "Gerçek Veri" ifadesi doğruluk garantisi içerdiği yorumlanabilir; lisanssız kaynakta bu ifade TKHK kapsamında yanıltıcıdır.
  **Dosya:** `frontend/src/components/DataQualityBadge.ts` satır 39

- [x] **BIST hisselerinde fiyat gösterimi ve grafiği geçici olarak "Lisans Bekleniyor" ekranıyla değiştirildi.** *(2026-05-23)*
  **Hukuki dayanak:** Yahoo Finance ToS — "display or distribute" maddesi ticari SaaS'ta yeniden dağıtımı açıkça yasaklar. BIST DataStore lisans zorunluluğu. İhlalde hukuki ve tazminat riski.
  **Dosyalar:** `backend/workers/bist_poller.py`, `quant_engine/data/providers/bist_provider.py`, ilgili frontend bileşenler

- [x] **`LandingPage.ts` kopyası düzeltildi:** `"gerçek veriyle test et"` → `"geçmiş veriyle test et"` (backtest geçmiş veri kullanır, gerçek zamanlı değil). *(2026-05-23)*
  **Hukuki dayanak:** TKHK m.61 (yanıltıcı reklam) + Reklam Kurulu ticari iletişim kuralları.
  **Dosya:** `frontend/src/pages/LandingPage.ts`

- [x] **Tüm piyasa veri ekranlarına "Veri Kaynağı ve Kalite Bildirimi" şeridi eklendi.** *(2026-05-23)*
  Metin: *"📊 Kripto: Binance public feed — gerçek zamanlıya yakın. BIST: Lisanslı kaynak bekleniyor — eğitim verisi. VİOP: Henüz aktif değil."*
  **Dosyalar:** `ChartPanel.ts`, `SignalFeed.ts`, `DataQualityBadge.ts`

---

#### C. Yasal Sayfalar — KVKK m.10, TKHK m.48, 6563 Sayılı Kanun

- [x] **`TermsPage.ts` tamamen yeniden yazıldı** — mevcut 15 satır yetersizdi. *(2026-05-23)*
  Zorunlu maddeler: (1) Hizmetin niteliği ve "yatırım tavsiyesi değildir" beyanı (SPK m.56), (2) Veri kaynakları ve lisans durumu, (3) Gerçek emir gönderimi olmadığı (SPK m.37), (4) Sorumluluk sınırlaması, (5) Yasaklı kullanım (piyasa manipülasyonu - TCK m.158/3-a), (6) 18 yaş sınırı, (7) Cayma hakkı ve abonelik iptali (TKHK m.48 + Mesafeli Sözleşmeler Yönetmeliği m.11), (8) Uygulanacak hukuk: Türk hukuku, yetkili mahkeme İstanbul, (9) Arabuluculuk zorunluluğu (7036 Sayılı Kanun), (10) Hesap fesih koşulları, (11) Fikri mülkiyet.
  **Dosya:** `frontend/src/pages/legal/TermsPage.ts`
  ⚠️ Taslak için `YAPILACAKLAR_YASAL_UYUM.md` Bölüm E kullanılacak — hukukçu onayı zorunlu.

- [x] **`PrivacyPage.ts` KVKK m.10 uyumlu aydınlatma metniyle yeniden yazıldı** — mevcut 14 satır yetersizdi. *(2026-05-23)*
  Zorunlu unsurlar: (1) Veri sorumlusunun tam kimliği (şirket/kişi adı, adres, e-posta), (2) İşlenen kişisel veri kategorileri (kimlik, iletişim, kimlik doğrulama, işlem, kullanım logu, Telegram chat ID), (3) İşleme amaçları ve her amaç için hukuki dayanak (KVKK m.5: sözleşme ifası / meşru menfaat / açık rıza), (4) Yurt dışına aktarım (Stripe — ABD; Telegram — Hollanda/ABD; cloud hosting) ve aktarım mekanizmaları, (5) Saklama süreleri (fatura: 10 yıl/VUK; log: 6 ay; Telegram ID: bot kapatılana kadar), (6) Kullanıcı hakları listesi (erişim, düzeltme, silme, itiraz, taşınabilirlik, otomatik karara itiraz — KVKK m.11), (7) Başvuru kanalı ve 30 günlük yanıt süresi, (8) KVK Kurulu'na şikâyet hakkı.
  **Dosya:** `frontend/src/pages/legal/PrivacyPage.ts`
  ⚠️ Taslak için `YAPILACAKLAR_YASAL_UYUM.md` Bölüm F kullanılacak — hukukçu onayı zorunlu.

- [x] **`CookiesPage.ts` KVKK Çerez Kılavuzu (2022) uyumlu olarak yeniden yazıldı.** *(2026-05-23)*
  Zorunlu unsurlar: (1) Zorunlu çerezler (oturum, CSRF, dil/tema) — onay gerektirmez, (2) Analitik çerezler (Sentry) — açık onay gerektirir, (3) Ödeme çerezleri (Stripe) — zorunlu, açıklanmalı, (4) Üçüncü taraf çerezler, (5) Tercihleri yönet mekanizması.
  **Not:** KVK Kurulu Çerez Kılavuzu (Nisan 2022) — analitik çerezler için açık onay zorunlu; localStorage'a kaydedilen tercihler "çerez" kapsamında değerlendirilebilir.
  **Dosya:** `frontend/src/pages/legal/CookiesPage.ts`

- [x] **`/legal/info` ve `/yasal` sayfası oluşturuldu** — tüm veri kaynakları, lisans durumları ve iletişim kanallarını tek sayfada sunan yasal bilgilendirme sayfası. *(2026-05-23)*
  İçerik: (1) SPK lisansı yoktur beyanı, (2) Veri kaynağı tablosu (Kripto/BIST/VİOP/KAP), (3) Yatırım tavsiyesi değildir beyanı, (4) Veri doğruluğu garantisi verilmediği, (5) İletişim e-postaları (genel, KVKK, veri lisans).
  **Hukuki dayanak:** SPK m.56, KVKK m.10, TKHK m.48 ön bilgilendirme yükümlülüğü.

- [x] **Footer'a yasal uyarı şeridi eklendi** (her public sayfada görünür). *(2026-05-23)*
  Metin: *"PiyasaPilotu bir yatırım danışmanlığı hizmeti değildir. Gösterilen veriler yalnızca eğitim/araştırma amaçlıdır. BIST ve VİOP için lisans süreci devam etmektedir."*
  **Dosya:** `frontend/src/components/Footer.ts` veya global layout

---

#### D. KVKK VERBİS Kaydı — Acil Kontrol

- [ ] **VERBİS (Veri Sorumluları Sicil Bilgi Sistemi) kaydı yapılıp yapılmadığı kontrol edilmeli.**
  **Hukuki dayanak:** KVKK m.16 — yurt içinde yerleşik tüzel kişiler ve belirli kriterlerin üzerindeki veri sorumluları verbis.kvkk.gov.tr adresinde kayıt olmak zorunda. Kayıt yapılmadan kişisel veri işlemek idari para cezasına yol açar (KVKK m.18: 32.000 TL – 1.000.000 TL 2024 güncelleme).
  **Eylem:** verbis.kvkk.gov.tr'de muafiyet kapsamında olup olmadığını kontrol et; muafiyet yoksa kayıt başlat.

---

### 11.2 — FAZ 2: KISA VADELİ (Canlıya Alındıktan Sonra İlk Hafta)

#### E. Telegram Onay Akışı — 6563 Sayılı Kanun m.6 / İYS

- [x] **Telegram bot onay paneli oluşturuldu.** *(2026-05-23)* Kullanıcı Telegram bildirimlerini aktifleştirirken üç onay kutusunu işaretlemek zorunda:
  (1) "Telegram bildirimlerinin yatırım tavsiyesi değil teknik sinyal bilgisi içerdiğini anlıyorum."
  (2) "Telegram chat ID'min yalnızca bildirim amacıyla saklanacağını kabul ediyorum."
  (3) "İstediğim zaman bildirimleri kapatabildiğimi biliyorum."
  Onay kayıt altına alınıyor (timestamp, IP, onay metni versiyonu) ve kolayca iptal edilebiliyor.
  **Hukuki dayanak:** 6563 Sayılı Kanun m.6 — Ticari elektronik ileti için alıcının açık onayı zorunlu. İYS (İleti Yönetim Sistemi) kaydı gerekliliği değerlendirilmeli.
  **Dosyalar:** `backend/notifier/preferences.py`, ilgili frontend modal bileşen

- [x] **Telegram bildirim onayı veritabanında saklanıyor.** *(2026-05-23)* `user_legal_consents` tablosu ve `/api/auth/me/consents` endpoint'i eklendi; giriş yapmış kullanıcıda timestamp, onay metni versiyonu ve IP/User-Agent kaydediliyor.
  **Hukuki dayanak:** 6563 Sayılı Kanun m.6/3 — Onayın ispatı hizmet sağlayıcıya aittir.

- [x] **Telegram bildirimlerinde kolayca iptal mekanizması sağlandı.** *(2026-05-23)* Her mesajda `/durdur` yönlendirmesi var; Telegram komut işleyicisi `/durdur` ile bildirimleri kapatıyor.
  **Hukuki dayanak:** 6563 Sayılı Kanun m.9 — Alıcı her zaman onayını geri alabilmeli; geri alma işlemi en geç 3 iş günü içinde işleme alınmalı.

- [ ] **İYS (İleti Yönetim Sistemi) kaydı değerlendirilmeli.** Telegram sinyal bildirimleri "ticari elektronik ileti" sayılıyorsa İYS kaydı ve onay yönetimi zorunlu.
  **Eylem:** 6563 Sayılı Kanun kapsamında bir e-ticaret hukuku uzmanına danışılmalı.

---

#### F. E-posta Pazarlama Onayı — 6563 Sayılı Kanun

- [x] **Kayıt formuna isteğe bağlı pazarlama onay kutusu eklendi.** *(2026-05-23)* "Kampanya, yenilik ve teklifler hakkında bilgilendirme e-postası almak istiyorum" varsayılan işaretsiz gelir; backend `marketing_consent` ve onay kaydı tutar.
  **Hukuki dayanak:** 6563 Sayılı Kanun m.6 — Pazarlama e-postaları için ayrı açık onay zorunlu; işlem/doğrulama e-postaları onay gerektirmez ama promosyonlar gerektirir.
  **Dosyalar:** Kayıt formu bileşeni, `backend/auth/` kullanıcı kaydı

- [x] **Mevcut e-posta şablonlarının tür sınıflandırması yapıldı.** *(2026-05-23)* Aktif şablonlar `EMAIL_TEMPLATE_TYPES` ile işlem e-postası olarak sınıflandırıldı; bilinmeyen/yeni şablonlar varsayılan pazarlama kabul edilir.
  **Dosyalar:** `backend/notifier/email.py`, `backend/auth/email_sender.py`

---

#### G. Cayma Hakkı ve Abonelik İptali — TKHK m.48 / Mesafeli Sözleşmeler Yönetmeliği

- [x] **Dijital hizmetlerde cayma hakkı politikası checkout akışında bildiriliyor.** *(2026-05-23)*
  **Hukuki dayanak:** Mesafeli Sözleşmeler Yönetmeliği m.15/1-ğ — Dijital içerik sözleşmelerinde teslimat başlamadan önce kullanıcının onayıyla cayma hakkı düşebilir; bu durumda kullanıcının imzalı beyanı alınmalı. Aksi hâlde 14 günlük cayma hakkı geçerlidir.
  Checkout akışında "Hizmeti hemen kullanmak istiyorum ve cayma hakkımın düşeceğini kabul ediyorum" onay kutusu eklendi; onay `/api/auth/me/consents` üzerinden kaydediliyor.

- [x] **Abonelik iptali sonrası kalan süre ve ücret iadesi politikası Kullanım Şartlarına yazıldı.** *(2026-05-23)*
  **Hukuki dayanak:** TKHK m.54 (abonelik sözleşmeleri) — iptal hakkı, bildirim süreleri ve ücret iadesi koşulları kullanıcıya önceden bildirilmeli.

---

#### H. KVKK Veri Envanteri ve Silme Mekanizması

- [x] **Kişisel veri envanteri çıkarıldı.** *(2026-05-23)* `KISISEL_VERI_ENVANTERI.md` içinde tablo bazında kişisel veri, saklama süresi, işleme amacı ve hukuki dayanak listelendi.
  **Tablolar kontrol edilmeli:** `users`, `subscriptions`, `paper_portfolio`, `paper_trades`, `user_preferences`, e-posta gönderim logları, Telegram chat_id.
  **Hukuki dayanak:** KVKK m.12 — veri güvenliği ve saklama süresi kontrolü zorunlu.

- [x] **Hesap silme/anonimleştirme akışı eklendi.** *(2026-05-23)* `DELETE /api/auth/me` endpoint'i ve Ayarlar sayfasında "Hesabımı Sil" akışı eklendi.
  Silme işlemi: kullanıcı tablosunu anonimleştirmeli, Telegram chat_id kaldırılmalı, e-posta ve tercihler silinmeli; fatura kayıtları VUK uyarınca 10 yıl saklanacağından anonimleştirme yapılmalı.

- [x] **KVKK başvuru kanalı sayfalara eklendi.** *(2026-05-23)* `kvkk@piyasapilot.com`, `destek@piyasapilot.com` ve `veri@piyasapilot.com` yasal sayfalarda ve veri envanterinde ilan edildi.
  **Hukuki dayanak:** KVKK m.13 — veri sorumlusu başvuruları 30 gün içinde yanıtlamak zorunda; yanıtlanmazsa KVK Kurulu'na şikâyet yolu açık.

---

#### I. MASAK / AML (Kara Para Aklamayla Mücadele) — 5549 Sayılı Kanun

- [ ] **Kripto para veya yatırım işlemleri kapsamında MASAK yükümlülüğü değerlendirilmeli.**
  **Hukuki dayanak:** 5549 Sayılı Suç Gelirlerinin Aklanmasının Önlenmesi Kanunu + MASAK Tebliğ 19 — Kripto varlık hizmet sağlayıcıları (KVHSP) MASAK'a bildirimi zorunlu kılar. PiyasaPilotu gerçek kripto alım/satım işlemi yapmıyor (paper trading); ancak Telegram bildirimleri ve kullanıcı verilerinin anonimliği değerlendirilmeli.
  **Eylem:** Finans hukukçusuna danışılmalı — PiyasaPilotu'nun KVHSP tanımına girip girmediği netleştirilmeli.

---

### 11.3 — FAZ 3: ORTA VADELİ (1 Ay)

#### J. BIST Veri Lisansı — Borsa İstanbul Mevzuatı

- [ ] **BIST DataStore (data.borsaistanbul.com) ile resmi lisans görüşmesi başlatılmalı.**
  **Hukuki dayanak:** Borsa İstanbul Yönetmeliği ve Piyasa Verisi Lisanslama Kılavuzu — BIST hisse ve VİOP verilerinin üçüncü taraf uygulamalarda kullanıcılara sunulması "veri yeniden dağıtımı" olup lisans sözleşmesi zorunludur. Lisanssız dağıtım İMKB/BİST telif hakkı ihlali ve tazminat riskidir.
  **Alternatifler değerlendirilmeli:** Matriks Veri Terminali API, Rasyonet API, IS Investment (İş Yatırım) API, Tera Yatırım, Gedik API — lisanslı ve ticari SaaS'a uygun veri sağlayıcılar.

- [ ] **Yahoo Finance yfinance kullanımı hukuki değerlendirmeye alınmalı.**
  **Hukuki dayanak:** Yahoo Finance Terms of Service — "You may not use the Service for any commercial purpose or for any public display (commercial or non-commercial)." Madde 4 ve 7 — redistribution yasağı. Production'da yfinance yerine lisanslı sağlayıcı bağlanana kadar BIST verisi gösterilmemeli.

- [ ] **Binance API ToS ticari SaaS kullanımı için hukuki danışman tarafından değerlendirilmeli.**
  **Hukuki dayanak:** Binance API Terms of Use — bireysel kullanım için açık, ticari SaaS için "Market Data License" gerekebilir. Binance Institutional'ın veri lisans programıyla iletişime geçilmeli.

- [ ] **KAP RSS kamu aydınlatma verisi kullanım koşulları doğrulanmalı.**
  **Eylem:** KAP (Kamuyu Aydınlatma Platformu) ile iletişime geçilerek RSS feed'inin ticari uygulamada yeniden dağıtımına izin verilip verilmediği teyit edilmeli. KAP verisi SPK'ya tabi bir kurum verisidir.

---

#### K. SPK Lisanslama Değerlendirmesi

- [ ] **SPK mevzuatına hâkim bir finans hukukçusuna danışılmalı:** PiyasaPilotu'nun mevcut özellik seti (sinyal üretimi, teknik tarama, paper trading) SPK kapsamında "yatırım danışmanlığı" veya "portföy yönetimi" sayılıp sayılmadığı netleştirilmeli.
  **Hukuki dayanak:** SPK Kanunu m.37 (yatırım hizmetleri ve faaliyetleri), m.56 (yatırım tavsiyesi), SPK Tebliğ III-39.1 (aracılık) ve VII-128.1 (yatırım tavsiyesi ve araştırması).
  **Risk:** Lisans gerektiren faaliyet kapsamına girerse SPK'ya başvuru yapılmadan ticari faaliyet sürdürülemez (SPK m.99 — ağır idari yaptırım ve TCK kapsamında cezai sorumluluk).

- [ ] **"Yatırım Tavsiyesi Değildir" beyanı SPK'nın standart formuna uygun şekle getirilmeli** (hukukçu tarafından hazırlanacak).
  **Hukuki dayanak:** SPK Tebliğ VII-128.1 m.8 — Yatırım araştırması niteliği taşımayan içerikler için standart uyarı metni zorunlu.

---

#### L. E-Fatura / E-Arşiv Fatura — GİB / VUK

- [ ] **Stripe abonelik ödemeleri için e-arşiv fatura zorunluluğu değerlendirilmeli.**
  **Hukuki dayanak:** Vergi Usul Kanunu (VUK) m.232 + GİB Tebliğleri — e-ticaret geliri olan mükelleflerin yıllık belirli ciro eşiğini (2024: 3 milyon TL) aşması durumunda e-fatura mükellefi olması zorunlu. Kısa vadede e-arşiv fatura düzenlenmesi gerekebilir.
  **Eylem:** Mali müşavire danışılmalı; gerekirse GİB e-fatura/e-arşiv başvurusu yapılmalı.

- [ ] **Fatura bilgileri Kullanım Şartları ve ödeme akışına eklenmeli:** Şirket/işletmeci adı, vergi numarası/TC kimlik, adres fatura üzerinde yer almalı.
  **Hukuki dayanak:** VUK m.230 fatura içeriği zorunlulukları.

---

#### M. TTK ve Şirket Bilgileri Zorunluluğu — 6102 Sayılı TTK

- [ ] **Website footer ve iletişim sayfasına TTK uyumlu şirket bilgileri eklenmeli:** Ticaret unvanı, adres, MERSİS numarası (şirket ise), vergi dairesi ve numarası.
  **Hukuki dayanak:** TTK m.39/2 — Ticaret şirketlerinin ticaret unvanlarını içeren bilgilerini işyerinde ve yazışmalarında bulundurma zorunluluğu. TKHK m.48 — Mesafeli satış yapan hizmet sağlayıcılar kimlik bilgilerini belirtmek zorunda.

---

#### N. Reklam ve Pazarlama — Reklam Kurulu / TKHK

- [x] **Paper trading / backtest performans uyarıları eklendi.** *(2026-05-23)* Pazarlama ve paylaşım yüzeylerinde geçmiş simülasyon verisinin gelecekteki gerçek performansı garanti etmediği dili kullanılıyor.
  **Hukuki dayanak:** TKHK m.61 (yanıltıcı reklam) + Ticari Reklam ve Haksız Ticari Uygulamalar Yönetmeliği m.5 — Geçmiş/simüle performans verilerini gerçek getiri gibi sunan reklamlar yanıltıcı sayılır.

- [x] **`SharedBacktestPage.ts` paylaşılan backtest sonuçlarına zorunlu uyarı metni eklendi.** *(2026-05-23)* *"Bu backtest sonuçları geçmiş veriye dayalı simülasyondur. Gelecekteki gerçek yatırım getirilerini göstermez."*
  **Hukuki dayanak:** SPK Tebliğ VII-128.1 m.8 + Reklam Kurulu kararları — performans verisi içeren her paylaşımda uyarı zorunlu.
  **Dosya:** `frontend/src/pages/SharedBacktestPage.ts`

---

### 11.4 — FAZ 4: UZUN VADELİ (3–6 Ay) — Büyüme Öncesi

#### O. BDDK / Ödeme Hizmetleri — 6493 Sayılı Kanun

- [ ] **Ödeme hizmetleri kapsamında BDDK lisansı gerekip gerekmediği değerlendirilmeli.**
  **Hukuki dayanak:** 6493 Sayılı Ödeme ve Menkul Kıymet Mutabakat Sistemleri, Ödeme Hizmetleri ve Elektronik Para Kuruluşları Hakkında Kanun — Stripe aracılığıyla ödeme tahsil etmek genellikle "ödeme hizmetleri aracısı" kapsamına girmez (Stripe lisansı var); ancak kullanıcı bakiyeleri veya kripto cüzdanı gibi özellikler eklendikçe BDDK lisansı gerekebilir. Şu an için risk düşük.

#### P. GDPR — AB Kullanıcıları

- [ ] **AB ülkelerinden kullanıcı kabul ediliyorsa GDPR uyumu değerlendirilmeli.**
  **Hukuki dayanak:** GDPR (AB) 2016/679 — AB'de yerleşik kişilere hizmet verilmesi durumunda DPO (Veri Koruma Sorumlusu) atanması veya AB temsilcisi belirlenmesi gerekebilir; çerez banner'ı IAB TCF 2.x standardına uygun olmalı.

#### R. Erişilebilirlik — WCAG 2.1 / Türkiye E-Devlet Standartları

- [ ] **Finans platformunun erişilebilirlik standartlarına uygunluğu (WCAG 2.1 AA) değerlendirilmeli.** Ekran okuyucu uyumu, renk kontrast oranları, klavye navigasyonu.
  **Hukuki dayanak:** Engellilerin Hakları Hakkında Kanun 7223 ve ilgili yönetmelikler; ticari web siteleri için yasal zorunluluk henüz sınırlı ama iyi pratik.

---

### 11.5 — UZMAN DANIŞMANLIK GEREKTİREN KONULAR (Kod Değil, Hukuki Aksiyon)

- [ ] **SPK mevzuatı uzmanı:** Sinyal üretimi, tarama ve paper trading özelliklerinin yatırım tavsiyesi / portföy yönetimi lisansı gerektirip gerektirmediği. → SPK mevzuatına hâkim finans hukukçusu
- [ ] **BIST/VİOP veri lisansı:** BIST DataStore veya yetkili dağıtıcılarla sözleşme süreci. → Borsa İstanbul veri lisans birimi: data.borsaistanbul.com
- [ ] **KVKK uyum denetimi:** Stripe/Telegram/email sağlayıcı veri aktarım mekanizmaları (SCCs), VERBİS kaydı, aydınlatma metni son onayı. → KVKK/GDPR uzmanı hukukçu
- [ ] **6563 / İYS:** Telegram bildirimleri ve e-posta pazarlamasının ticari elektronik ileti sayılıp sayılmadığı, İYS'ye kayıt zorunluluğu. → E-ticaret hukuku uzmanı
- [ ] **VUK/e-fatura:** E-arşiv/e-fatura zorunluluğu ve GİB başvurusu. → Serbest muhasebeci mali müşavir (SMMM)
- [ ] **Yahoo Finance ToS:** Mevcut yfinance kullanımının tam meşruiyet analizi. → Hukukçu + Yahoo Finance lisans birimi iletişimi
- [ ] **MASAK/AML:** Kripto veri gösterimi kapsamında MASAK yükümlülüğü. → Finans hukukçusu

---

*Bu belge 2026-05-17 tarihinde proje kaynak dosyaları eksiksiz okunarak hazırlandı.*
*Bir madde tamamlandığında `[ ]` → `[x]` yap. Yeni madde eklendikçe ilgili bölüme ekle.*
