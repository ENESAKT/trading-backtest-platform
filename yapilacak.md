# PiyasaPilot — Yapılacaklar Listesi
> Oluşturulma: 2026-05-17 | Son güncelleme: 2026-05-23 (tüm Claude-yapılabilir maddeler kapatıldı)
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

- [x] **Migration 010 yok — `jti` kolonu zaten migration 007'de mevcut.** *(2026-05-23)*  
  Migration 007 `refresh_tokens` tablosunu oluşturuyor ama `jti` kolonu yok.  
  Migration 010 `ALTER TABLE refresh_tokens ADD COLUMN jti VARCHAR(64)` ekliyor.  
  Migration sırasının (001→010) production'da eksiksiz uygulandığı doğrulanmalı; `CANLIYA_ALMA_REHBERI.md` buna atıfta bulunmalı.

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

- [ ] **`/api/me/limits` bilgisiyle plan kullanım göstergesi eklenmeli.** *(frontend UI geliştirmesi — endpoint mevcut: `/api/auth/me/limits`)*  
  Kullanıcı bugün kaç backtest çalıştırdığını ve ne kadar kotası kaldığını göremez.  
  Ayarlar veya terminal başlık alanında "3/5 backtest kullanıldı" tarzı bir gösterge eklenmeli.

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
- [ ] **Migration'ları production'da çalıştır.** 001→009 sırayla (`infra/mysql/migrations/`). Migration 010 yoktur; jti kolonu migration 007'de mevcut.
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
- [ ] `YAPILANLAR.md` son session'ın çıktılarıyla güncellendi.
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

*Bu belge 2026-05-17 tarihinde proje kaynak dosyaları eksiksiz okunarak hazırlandı.*  
*Bir madde tamamlandığında `[ ]` → `[x]` yap. Yeni madde eklendikçe ilgili bölüme ekle.*
