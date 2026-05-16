# PiyasaPilot — Ultra Production Planı

> Son güncelleme: 2026-05-16
> Genel ilerleme: **%58 tamamlandı / %42 kaldı**
> Domain: `piyasapilotu.com` (METUnic'ten satın alındı — aktif, DNS yönetimi dahil)
> Branch: `codex/financials-ui-api-v1`
> Mobil: Flutter + Dart (MVVM / Clean Architecture)
> Bu belge, başka bir AI veya geliştirici tarafından birebir uygulanabilecek
> granülaritede yazılmıştır. Her görevin başına tamamlanınca `[x]` koy.

---

## İLERLEME PANOSU — HER OTURUMDA GÜNCELLE

> Kural: Her yeni oturum başında bu tablo okunur. Her tamamlanan iş hem burada
> tiklenir/güncellenir hem de `YAPILANLAR.md` dosyasına kısa kayıt olarak eklenir.
> Büyük başlık tamamen bitmeden ana checkbox `[x]` yapılmaz; kısmi ilerleme yüzdeyle
> gösterilir.

| Aşama | Durum | İlerleme | Kalan | Takip |
|---|:---:|---:|---:|---|
| [Bölüm 0 — Domain ve DNS](#bölüm-0--domain-ve-dns-yapılandırması) | [ ] | 35% | 65% | Domain/nginx hazır; gerçek sunucu IP, DNS ve TLS canlı doğrulama kaldı |
| [Bölüm 1 — Marka ve Domain Tutarlılığı](#bölüm-1--marka-ve-domain-tutarlılığı) | [x] | 100% | 0% | SEO/meta/domain temizliği yapıldı |
| [Bölüm 2 — Kullanıcı Rol ve Yetki Sistemi](#bölüm-2--kullanıcı-rol-ve-yetki-sistemi) | [x] | 100% | 0% | Migration 007 lokal DB'ye uygulandı; plan tabloları oluştu |
| [Bölüm 3 — Backend Auth Modülü](#bölüm-3--backend-auth-modülü) | [ ] | 80% | 20% | Register/login/me çalışıyor; trial kararı net, şifre policy eklendi; endpoint guard kapsam testi kaldı |
| [Bölüm 4 — Ekran Tasarımları](#bölüm-4--ekran-tasarımları-wireframe-düzeyinde) | [ ] | 90% | 10% | Public/auth/legal/admin/settings sayfaları QA edildi; dış entegrasyonlu uç akışlar kaldı |
| [Bölüm 5 — Ödeme Sistemi](#bölüm-5--ödeme-sistemi-stripe) | [ ] | 40% | 60% | Backend/frontend iskeleti var; canlı Stripe ürünleri ve webhook doğrulaması kaldı |
| [Bölüm 6 — Admin Yönetim Paneli](#bölüm-6--admin-yönetim-paneli) | [ ] | 75% | 25% | Panel kullanılabilir empty state, skeleton, yetki UX ve health veri kalitesiyle cilalandı; detay aksiyonları canlı API verisi bekliyor |
| [Bölüm 7 — Ödeme Sonrası ve Plan Yönetimi](#bölüm-7--ödeme-sonrası-ve-plan-yönetimi-frontend) | [ ] | 75% | 25% | Success/settings/billing portal UI profesyonel bekleme durumlarıyla tamamlandı; canlı Stripe uçtan uca test kaldı |
| [Bölüm 8 — i18n ve Hukuki Sayfalar](#bölüm-8--i18n-ve-hukuki-sayfalar) | [ ] | 82% | 18% | Public shell, landing ve pricing görünür metinleri TR/EN sözlüğe bağlandı; tüm terminal metinlerinin i18n'e taşınması kaldı |
| [Bölüm 9 — Mevcut UI Hataları](#bölüm-9--mevcut-ui-hataları) | [x] | 100% | 0% | Web UX QA blocker paketi kapandı; code splitting sonrası build uyarısı yok |
| [Bölüm 10 — Mobil Uygulama Planı](#bölüm-10--mobil-uygulama-planı-flutter) | [ ] | 10% | 90% | Mimari plan var; Flutter uygulama henüz başlamadı |
| [Bölüm 11 — ClickHouse + Veri Platformu](#bölüm-11--clickhouse--veri-platformu-tamamlama) | [ ] | 35% | 65% | Şemalar var; facade bağlantısı ve veri badge üretim entegrasyonu kaldı |
| [Bölüm 12 — CI/CD ve Deployment](#bölüm-12--cicd-ve-deployment) | [ ] | 55% | 45% | CI/migration/readiness iskeleti var; gerçek pipeline ve release pratiği kaldı |
| [Bölüm 13 — Error Tracking ve Monitoring](#bölüm-13--error-tracking-ve-monitoring) | [ ] | 55% | 45% | Sentry/Grafana iskeleti var; canlı DSN/dashboard/alert kaldı |
| [Bölüm 14 — Kabul Testi Checklist](#bölüm-14--kabul-testi-checklist) | [ ] | 65% | 35% | Frontend Playwright suite 24/24 geçti; canlı domain/Stripe/Sentry/Flutter ve backend uç kabul testleri kaldı |
| [Bölüm 15 — AWS Deployment](#bölüm-15--aws-deployment-eu-central-1-frankfurt) | [ ] | 10% | 90% | Plan hazır; canlı AWS kurulum yapılmadı |
| [Bölüm 16 — Eksik / Atlanan Teknik Maddeler](#bölüm-16--eksik--atlanan-teknik-maddeler) | [ ] | 75% | 25% | Analytics/PWA/skeleton paketi korundu; frontend E2E kontratı stabilize edildi |
| [Bölüm 17 — Proje Büyütme Yol Haritası](#bölüm-17--proje-büyütme-yol-haritası) | [ ] | 40% | 60% | Waitlist/growth sayfaları gerçekçi bekleme dili ve analytics ile kullanılabilir hale geldi; kanal/blog/komünite işleri kaldı |
| **GENEL TOPLAM** | [ ] | **58%** | **42%** | Frontend kullanıcı yüzeyi, i18n public shell, smoke QA, analytics/PWA ve E2E suite stabilize edildi; canlı dış entegrasyon ve platform işleri kaldı |

### Oturum Sonu Güncelleme Kuralları

- [x] `YAPILACAKLAR.md` en üstündeki genel yüzde güncellendi.
- [x] İlgili bölümün ilerleme yüzdesi güncellendi.
- [x] Bitmiş görevlerin başındaki checkbox `[x]` yapıldı.
- [x] Bitmiş işler `YAPILANLAR.md` içine kısa ve tarihli şekilde yazıldı.
- [x] Test/QA sonucu varsa kabul kriterinin altına yazıldı.
- [ ] Yeni hata bulunduysa ilgili bölümün altına açık görev olarak eklendi.

### Son Durum Notu — 2026-05-16

- [x] Browser QA sırasında `#app-error-banner` görünmez katman hatası bulundu ve `.hidden` CSS kuralı düzeltildi.
- [x] Web UX QA raporu oluşturuldu: `WEB_UX_TEST_RAPORU.md`.
- [x] Lokal MySQL migration runner ile `001-009` migration dosyaları uygulandı.
- [x] `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me` akışı lokal testte 200 OK döndü.
- [x] `WEB_UX_TEST_RAPORU.md` içindeki açıklar Bölüm 9 altında kapatıldı; yeni QA sonucu rapora eklendi.
- [x] Yeni kayıt olan kullanıcının otomatik `pro` trial alması ürün kararı netleştirildi: 14 günlük Pro trial kalacak; email ve OAuth kayıtlarında uygulanacak.
- [ ] Stripe canlı ürün/price id ve webhook secret ile uçtan uca ödeme testi yapılacak.
- [ ] AWS canlı deployment, DNS ve TLS doğrulaması yapılacak.
- [x] Frontend ürün yüzeyi QA paketi tamamlandı: public/protected/legal/terminal route'larında desktop ve 390px mobil smoke test yapıldı.
- [x] Analytics helper gerçek kullanıcı olaylarına bağlandı: page view, signup/login, upgrade, billing portal, waitlist ve shared 404.
- [x] PWA statik service worker eklendi; API/WS istekleri cache dışı bırakıldı.

---

## OKUMA REHBERİ

Bu planı uygulayan herkese (AI veya insan):

1. `mentorplan.md` → projenin tek başvuru kaynağı; önce bunu oku.
2. `YAPILANLAR.md` → neyin bittiğini gösterir; tekrar yapma.
3. Bu belgeyi **bölüm sırasıyla** uygula — bağımlılıklar her bölümde belirtilmiştir.
4. Dokunulmaz dosyalar:
   `quant_engine/backtest/engine.py`, `quant_engine/data/live_feed.py`,
   `quant_engine/data/providers/binance_provider.py`,
   `quant_engine/data/providers/yfinance_provider.py`
5. Her backend değişikliği sonrası: `python -m pytest -q`
6. Her frontend değişikliği sonrası: `cd frontend && npm run typecheck && npm run build`
7. Yeni Python paketi: `pip install <paket> --break-system-packages`

---

# BÖLÜM 0 — Domain ve DNS Yapılandırması

> Tahmini süre: 30 dakika (sunucu hazır olduğunda)
> Bağımlılık: Bir VPS/cloud sunucu IP adresi gerekli

## 0.1 · METUnic DNS Yönetimi — A ve CNAME Kayıtları

METUnic panelinden (Hizmetler → piyasapilotu.com → DNS ve Alan Adı Yönetimi → Yönet):

```
Kayıt Türü    Ad (Host)        Değer (Value)              TTL
──────────────────────────────────────────────────────────────
A             @                <SUNUCU_IP>                 3600
A             www              <SUNUCU_IP>                 3600
CNAME         api              piyasapilotu.com            3600
TXT           @                "v=spf1 include:_spf.google.com ~all"   (email SPF)
MX            @                aspmx.l.google.com (öncelik 1)          (Gmail için)
```

Mobil API subdomain ekle (ileride):
```
A             api-mobile       <SUNUCU_IP>                 3600
```

**Doğrulama:**
```bash
dig piyasapilotu.com A +short       # → sunucu IP
dig www.piyasapilotu.com A +short   # → sunucu IP
curl -I https://piyasapilotu.com    # → HTTP/2 200
```

---

## 0.2 · TLS Sertifikası (Certbot)

Sunucuda çalıştır:
```bash
# docker-compose.prod.yml ayağa kaldırılmadan önce, sadece nginx 80 açık
sudo certbot certonly --standalone \
  -d piyasapilotu.com \
  -d www.piyasapilotu.com \
  --email enesaktas.ce@gmail.com \
  --agree-tos --non-interactive

# Otomatik yenileme cron (60 günde bir kontrol)
echo "0 3 1,15 * * root certbot renew --quiet --deploy-hook 'docker exec piyasapilot_nginx_prod nginx -s reload'" \
  | sudo tee /etc/cron.d/certbot-renew
```

Sertifika yolu: `/etc/letsencrypt/live/piyasapilotu.com/`
Bu yol `docker/nginx.prod.conf`'ta kullanılıyor.

---

## 0.3 · `docker/nginx.prod.conf` — piyasapilotu.com ile güncelle

Dosyadaki tüm `ornekdomain.com` → `piyasapilotu.com` değiştir.

Ayrıca mobil app için `/api/v1/mobile/` proxy bloğu ekle (BÖLÜM 9'da detay):
```nginx
location /api/v1/mobile/ {
    proxy_pass http://api:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**Kabul kriteri:** `grep ornekdomain docker/nginx.prod.conf` → sıfır sonuç.

---

# BÖLÜM 1 — Marka ve Domain Tutarlılığı

> Tahmini süre: 2–3 saat | Bağımlılık: yok

## 1.1 · `frontend/index.html`

```html
<!-- ÖNCE -->
<title>PiyasaPilot v2.0</title>
<html lang="tr">

<!-- SONRA -->
<title>PiyasaPilot — Algoritmik Trading Terminali</title>
<html lang="tr" data-lang="tr">
<meta name="description"
  content="PiyasaPilot: BIST, kripto ve global piyasalar için backtest, sinyal ve portföy yönetimi.">
<meta property="og:title" content="PiyasaPilot">
<meta property="og:url" content="https://piyasapilotu.com">
<link rel="canonical" href="https://piyasapilotu.com">
```

Hardcoded ticker bloğunu (`<div id="market-ticker">`) **kaldır** — sahte veri içeriyor.

## 1.2 · `frontend/src/app.ts` satır 562

```ts
// ÖNCE
console.info('PiyasaPilot v2.0 başlatıldı — çoklu pencere layout aktif');
// SONRA
console.info('PiyasaPilot başlatıldı');
```

## 1.3 · `.env.example` — yeni değişkenler ekle

Aşağıdaki bloğu `DATABASE_URL` satırının üstüne ekle:

```env
# ─── Domain & Deployment ──────────────────────────────
PUBLIC_BASE_URL=https://piyasapilotu.com
COOKIE_DOMAIN=piyasapilotu.com
CORS_ORIGINS=https://piyasapilotu.com,https://www.piyasapilotu.com

# ─── JWT & Session ────────────────────────────────────
JWT_SECRET=EN_AZ_64_KARAKTER_RASTGELE_STRING
JWT_ALGORITHM=HS256
ACCESS_TOKEN_TTL_SECONDS=900
REFRESH_TOKEN_TTL_SECONDS=604800

# ─── Google OAuth ─────────────────────────────────────
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=https://piyasapilotu.com/api/auth/google/callback

# ─── Ödeme (Stripe) ───────────────────────────────────
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRO_PRICE_ID=
STRIPE_ULTRA_PRICE_ID=

# ─── Error Tracking ───────────────────────────────────
SENTRY_DSN=
SENTRY_ENVIRONMENT=production
```

**Kabul kriteri:** `grep "ornekdomain\|v2\.0\|piyasa pilotu" frontend/src/app.ts README.md docker/nginx.prod.conf` → sıfır sonuç.

---

# BÖLÜM 2 — Kullanıcı Rol ve Yetki Sistemi

> Proje genelindeki tek yetki tablosu. Başka bir yerde kopyalanmaz.

## 2.1 · Kullanıcı Seviyeleri (5 Katman)

```
MISAFIR (guest)
│  → Giriş yapmadan erişir
│  → Landing page, fiyatlandırma, örnek grafik (statik)
│  → Terminal'e giremez
│
ÜCRETSİZ (free)
│  → Email/Google ile kayıt
│  → Terminal'e girebilir, kısıtlı
│
PRO ($19.99/ay)
│  → Tüm terminal özellikleri
│  → Backtest Pro dahil
│
ULTRA ($49.99/ay)
│  → Pro + gerçek zamanlı lisanslı veri
│  → Sınırsız backtest + API erişimi
│
ADMİN (admin)
   → Yönetim paneline erişir
   → Tüm kullanıcıları yönetir
   → Veri kalite izleme
   → Gelir raporları
```

## 2.2 · Özellik Bazlı Erişim Tablosu (Feature Gate Matrisi)

```
ÖZELLİK                              MİSAFİR   ÜCRETSİZ   PRO      ULTRA    ADMİN
─────────────────────────────────────────────────────────────────────────────────
Landing page                           ✅        ✅         ✅       ✅       ✅
Fiyatlandırma sayfası                  ✅        ✅         ✅       ✅       ✅
Demo grafik (statik BTCUSDT)           ✅        ❌         ❌       ❌       ❌
─────────────────────────────────────────────────────────────────────────────────
Terminal girişi                        ❌        ✅         ✅       ✅       ✅
Sembol arama                           ❌        ✅(10/gün) ✅       ✅       ✅
Watchlist                              ❌        10 sembol  50 sem.  500 sem. ✅
─────────────────────────────────────────────────────────────────────────────────
Grafik (gecikmeli yfinance verisi)     ❌        ✅         ✅       ✅       ✅
Grafik (gerçek zamanlı lisanslı)       ❌        ❌         ❌       ✅       ✅
Grafik çizim araçları                  ❌        ✅         ✅       ✅       ✅
Multi-chart layout (4'lü)              ❌        ❌         ✅       ✅       ✅
Grafik şablonları kaydet               ❌        1 şablon   10 şabl. ∞       ✅
─────────────────────────────────────────────────────────────────────────────────
Backtest (temel)                       ❌        5/gün      50/gün   ∞       ✅
Backtest Pro — Walk-Forward Analysis   ❌        ❌         ✅       ✅       ✅
Backtest Pro — Monte Carlo             ❌        ❌         ✅       ✅       ✅
Backtest Pro — Heatmap Optimizasyon    ❌        ❌         ✅       ✅       ✅
Backtest Pro — Strategy Pack           ❌        ❌         ✅       ✅       ✅
Backtest Pro — Portföy Lab             ❌        ❌         ✅       ✅       ✅
─────────────────────────────────────────────────────────────────────────────────
Tarayıcı (Scanner)                     ❌        ❌         ✅       ✅       ✅
Sinyaller                              ❌        3/gün      ∞        ∞       ✅
Paper trading                          ❌        ✅(1 hesap) ✅(5)   ✅(∞)   ✅
─────────────────────────────────────────────────────────────────────────────────
Mali analiz                            ❌        BIST30     BIST100  TÜM     ✅
Haberler (KAP)                         ❌        ✅         ✅       ✅       ✅
Eğitimler                              ❌        Temel      Tümü     Tümü    ✅
─────────────────────────────────────────────────────────────────────────────────
Telegram sinyal botu                   ❌        ❌         ✅       ✅       ✅
API erişimi (REST)                     ❌        ❌         ❌       ✅       ✅
─────────────────────────────────────────────────────────────────────────────────
Yönetim paneli                         ❌        ❌         ❌       ❌       ✅
─────────────────────────────────────────────────────────────────────────────────
```

## 2.3 · MySQL Migration 007 — Auth + Abonelik Tabloları

**Dosya:** `infra/mysql/migrations/007_auth_tables.sql`

```sql
-- ─── Kullanıcılar ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    email         VARCHAR(255) NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    password_hash  VARCHAR(255),
    display_name   VARCHAR(100),
    avatar_url     VARCHAR(500),
    role           ENUM('guest','free','pro','ultra','admin') DEFAULT 'free',
    language       ENUM('tr','en') DEFAULT 'tr',
    is_active      BOOLEAN DEFAULT TRUE,
    last_login_at  DATETIME,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_email (email)
);

-- ─── Google / GitHub OAuth ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS oauth_accounts (
    id               BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id          BIGINT NOT NULL,
    provider         VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    access_token     TEXT,
    refresh_token    TEXT,
    expires_at       DATETIME,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_provider_user (provider, provider_user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─── Refresh Token Deposu ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id    BIGINT NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    user_agent VARCHAR(500),
    ip_address VARCHAR(45),
    device_name VARCHAR(100),         -- "iPhone 14", "Chrome / macOS" vb.
    expires_at DATETIME NOT NULL,
    revoked_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_rt_user_id (user_id),
    INDEX idx_rt_token_hash (token_hash),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─── Email Doğrulama ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id    BIGINT NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at DATETIME NOT NULL,
    used_at    DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_evt_token (token_hash),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─── Şifre Sıfırlama ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id    BIGINT NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at DATETIME NOT NULL,
    used_at    DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_prt_token (token_hash),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─── Kullanıcı Ayarları (JSON) ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_settings (
    user_id           BIGINT PRIMARY KEY,
    favorite_symbols  JSON,
    default_symbol    VARCHAR(50) DEFAULT 'BTCUSDT',
    default_timeframe VARCHAR(10) DEFAULT '1h',
    theme             ENUM('dark','light') DEFAULT 'dark',
    accent_color      VARCHAR(20) DEFAULT 'amber',
    notification_prefs JSON,
    dashboard_layout  JSON,
    onboarding_done   BOOLEAN DEFAULT FALSE,
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─── Abonelik Planları ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS subscription_plans (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    slug                    VARCHAR(50) NOT NULL UNIQUE,
    display_name_tr         VARCHAR(100) NOT NULL,
    display_name_en         VARCHAR(100) NOT NULL,
    price_monthly_usd       DECIMAL(10,2) DEFAULT 0,
    price_yearly_usd        DECIMAL(10,2) DEFAULT 0,
    stripe_monthly_price_id VARCHAR(100),
    stripe_yearly_price_id  VARCHAR(100),
    api_calls_per_day       INT DEFAULT 500,
    backtest_runs_per_day   INT DEFAULT 5,
    max_watchlist_symbols   INT DEFAULT 10,
    max_paper_accounts      INT DEFAULT 1,
    max_chart_templates     INT DEFAULT 1,
    real_time_data          BOOLEAN DEFAULT FALSE,
    backtest_pro_enabled    BOOLEAN DEFAULT FALSE,
    scanner_enabled         BOOLEAN DEFAULT FALSE,
    signals_per_day         INT DEFAULT 3,
    mali_analiz_scope       ENUM('none','bist30','bist100','all') DEFAULT 'bist30',
    education_full          BOOLEAN DEFAULT FALSE,
    telegram_bot            BOOLEAN DEFAULT FALSE,
    api_access              BOOLEAN DEFAULT FALSE,
    is_active               BOOLEAN DEFAULT TRUE,
    created_at              DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ─── Kullanıcı Abonelikleri ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id                    BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id               BIGINT NOT NULL,
    plan_id               INT NOT NULL,
    stripe_subscription_id VARCHAR(100),
    stripe_customer_id    VARCHAR(100),
    billing_period        ENUM('monthly','yearly') DEFAULT 'monthly',
    status                ENUM('trialing','active','cancelled','expired','past_due') DEFAULT 'active',
    trial_ends_at         DATETIME,
    current_period_start  DATETIME,
    current_period_end    DATETIME,
    cancelled_at          DATETIME,
    created_at            DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at            DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_us_user_id (user_id),
    INDEX idx_us_stripe_sub (stripe_subscription_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES subscription_plans(id)
);

-- ─── Günlük Kullanım Sayaçları ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS daily_usage (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id       BIGINT NOT NULL,
    date          DATE NOT NULL,
    api_calls     INT DEFAULT 0,
    backtest_runs INT DEFAULT 0,
    signal_views  INT DEFAULT 0,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_date (user_id, date),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─── Denetim Logu ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_log (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id    BIGINT,
    action     VARCHAR(100) NOT NULL,
    resource   VARCHAR(200),
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    metadata   JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_al_user_id (user_id),
    INDEX idx_al_action (action),
    INDEX idx_al_created_at (created_at)
);

-- ─── Başlangıç Planları ───────────────────────────────────────────────────
INSERT IGNORE INTO subscription_plans
(slug, display_name_tr, display_name_en, price_monthly_usd, price_yearly_usd,
 api_calls_per_day, backtest_runs_per_day, max_watchlist_symbols, max_paper_accounts,
 max_chart_templates, real_time_data, backtest_pro_enabled, scanner_enabled,
 signals_per_day, mali_analiz_scope, education_full, telegram_bot, api_access)
VALUES
('free',  'Ücretsiz', 'Free',       0.00,  0.00,   500,   5,  10, 1,  1, FALSE, FALSE, FALSE,  3, 'bist30',  FALSE, FALSE, FALSE),
('pro',   'Pro',      'Pro',       19.99, 199.99,  5000,  50,  50, 5, 10, FALSE, TRUE,  TRUE,  -1, 'bist100', TRUE,  TRUE,  FALSE),
('ultra', 'Ultra',    'Ultra',     49.99, 499.99, 50000,  -1, 500,-1, -1, TRUE,  TRUE,  TRUE,  -1, 'all',     TRUE,  TRUE,  TRUE);
-- Not: -1 = sınırsız
```

**Kabul kriteri:** `SHOW TABLES` → yeni 9 tablo görünüyor; `SELECT slug, price_monthly_usd FROM subscription_plans` → 3 plan listeleniyor.

---

# BÖLÜM 3 — Backend Auth Modülü

> Bağımlılık: Bölüm 2.3 tamamlanmış olmalı

## 3.1 · Yeni Modül: `backend/auth/`

```
backend/auth/
├── __init__.py
├── schemas.py          # Pydantic request/response modelleri
├── password.py         # Argon2 hash/verify
├── jwt_utils.py        # access + refresh token
├── cookie_utils.py     # Secure + HttpOnly cookie yönetimi
├── service.py          # İş mantığı (register, login, logout, vb.)
├── google_oauth.py     # Google OAuth2
├── email_sender.py     # Doğrulama/sıfırlama email'i
├── repository.py       # MySQL CRUD (users, tokens, subscriptions)
├── dependencies.py     # FastAPI Depends: get_current_user, require_role, check_feature
└── feature_gate.py     # Özellik bazlı erişim kontrolü
```

## 3.2 · `backend/auth/feature_gate.py` — Feature Gate Sistemi

Bu dosya tüm özellik kısıtlamalarının TEK kaynağıdır.

```python
"""
Feature Gate — PiyasaPilot yetki sistemi.
Tüm özellik kısıtları bu dosyadan okunur.
Yeni bir özellik eklendiğinde sadece bu dosya güncellenir.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Literal

Role = Literal['free', 'pro', 'ultra', 'admin']

@dataclass(frozen=True)
class PlanLimits:
    api_calls_per_day: int         # -1 = sınırsız
    backtest_runs_per_day: int
    max_watchlist_symbols: int
    max_paper_accounts: int
    max_chart_templates: int
    real_time_data: bool
    backtest_pro: bool             # WFA, Monte Carlo, Heatmap, Portfolio Lab, Pack
    scanner: bool
    signals_per_day: int           # -1 = sınırsız
    mali_analiz_scope: str         # 'none' | 'bist30' | 'bist100' | 'all'
    education_full: bool
    telegram_bot: bool
    api_access: bool
    multi_chart: bool              # 4'lü layout
    terminal_access: bool

PLAN_LIMITS: dict[str, PlanLimits] = {
    'free': PlanLimits(
        api_calls_per_day=500,
        backtest_runs_per_day=5,
        max_watchlist_symbols=10,
        max_paper_accounts=1,
        max_chart_templates=1,
        real_time_data=False,
        backtest_pro=False,
        scanner=False,
        signals_per_day=3,
        mali_analiz_scope='bist30',
        education_full=False,
        telegram_bot=False,
        api_access=False,
        multi_chart=False,
        terminal_access=True,
    ),
    'pro': PlanLimits(
        api_calls_per_day=5000,
        backtest_runs_per_day=50,
        max_watchlist_symbols=50,
        max_paper_accounts=5,
        max_chart_templates=10,
        real_time_data=False,
        backtest_pro=True,
        scanner=True,
        signals_per_day=-1,
        mali_analiz_scope='bist100',
        education_full=True,
        telegram_bot=True,
        api_access=False,
        multi_chart=True,
        terminal_access=True,
    ),
    'ultra': PlanLimits(
        api_calls_per_day=-1,
        backtest_runs_per_day=-1,
        max_watchlist_symbols=-1,
        max_paper_accounts=-1,
        max_chart_templates=-1,
        real_time_data=True,
        backtest_pro=True,
        scanner=True,
        signals_per_day=-1,
        mali_analiz_scope='all',
        education_full=True,
        telegram_bot=True,
        api_access=True,
        multi_chart=True,
        terminal_access=True,
    ),
    'admin': PlanLimits(
        api_calls_per_day=-1,
        backtest_runs_per_day=-1,
        max_watchlist_symbols=-1,
        max_paper_accounts=-1,
        max_chart_templates=-1,
        real_time_data=True,
        backtest_pro=True,
        scanner=True,
        signals_per_day=-1,
        mali_analiz_scope='all',
        education_full=True,
        telegram_bot=True,
        api_access=True,
        multi_chart=True,
        terminal_access=True,
    ),
}

def get_limits(role: str) -> PlanLimits:
    return PLAN_LIMITS.get(role, PLAN_LIMITS['free'])

def can_access(role: str, feature: str) -> bool:
    """Özellik erişimi sorgusu. feature: PlanLimits field adı."""
    limits = get_limits(role)
    value = getattr(limits, feature, False)
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0  # 0 = kapalı, -1 = sınırsız, >0 = kotası var
    return bool(value)
```

## 3.3 · `backend/auth/dependencies.py`

```python
from fastapi import Request, HTTPException, status, Depends
from .jwt_utils import decode_access_token
from .feature_gate import can_access, get_limits
from jose import JWTError

async def get_current_user(request: Request) -> dict:
    """Cookie'den JWT oku, doğrula, user bilgisi döndür."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(401, detail={"tr": "Giriş yapınız.", "en": "Login required."})
    try:
        return decode_access_token(token)
    except JWTError:
        raise HTTPException(401, detail={"tr": "Oturum süresi doldu.", "en": "Session expired."})

def require_role(*roles: str):
    """Belirtilen rollerden birine sahip olmayı zorunlu kılar."""
    async def checker(user=Depends(get_current_user)):
        if user.get("role") not in roles:
            raise HTTPException(403, detail={"tr": "Bu özellik planınızda yok.", "en": "Feature not in your plan."})
        return user
    return checker

def require_feature(feature: str):
    """Özellik erişimi kontrolü — planLimits üzerinden."""
    async def checker(user=Depends(get_current_user)):
        if not can_access(user.get("role", "free"), feature):
            raise HTTPException(403, detail={
                "tr": f"Bu özellik Pro veya Ultra planında mevcut.",
                "en": f"This feature requires a Pro or Ultra plan.",
                "upgrade_url": "https://piyasapilotu.com/pricing",
            })
        return user
    return checker

def require_quota(counter_field: str):
    """Günlük kota kontrolü (backtest_runs_per_day, signals_per_day, vb.)."""
    async def checker(request: Request, user=Depends(get_current_user)):
        # daily_usage tablosundan bugünkü sayacı oku
        # Kota aşıldıysa 429 fırlat
        limits = get_limits(user.get("role", "free"))
        limit_value = getattr(limits, counter_field, 0)
        if limit_value == -1:  # sınırsız
            return user
        # DB kontrolü → app.state.db_pool üzerinden
        used = await _get_daily_usage(request.app.state, user["sub"], counter_field)
        if used >= limit_value:
            raise HTTPException(429, detail={
                "tr": f"Günlük kotanız doldu. Yarın veya planı yükselterek devam edin.",
                "en": f"Daily quota exceeded. Upgrade your plan or wait until tomorrow.",
                "limit": limit_value,
                "used": used,
                "upgrade_url": "https://piyasapilotu.com/pricing",
            })
        return user
    return checker

require_admin     = require_role("admin")
require_pro       = require_role("pro", "ultra", "admin")
require_ultra     = require_role("ultra", "admin")
require_backtest_pro = require_feature("backtest_pro")
require_scanner   = require_feature("scanner")
require_realtime  = require_feature("real_time_data")
require_api_access = require_feature("api_access")
```

## 3.4 · Auth Endpoint'leri (`backend/api/auth_router.py`)

```python
# app.include_router(auth_router, prefix="/api/auth") ile main.py'e ekle

@router.post("/register")           # body: {email, password, display_name}
@router.post("/login")              # body: {email, password} → cookie set
@router.post("/logout")             # cookie temizle + token revoke
@router.post("/refresh")            # refresh cookie → yeni access token
@router.get("/me")                  # mevcut kullanıcı + plan bilgisi + kotalar
@router.patch("/me/settings")       # kullanıcı ayarları güncelle
@router.delete("/me")               # hesap sil (GDPR)
@router.get("/me/export")           # kullanıcı verisi dışa aktar (GDPR)
@router.get("/google")              # Google OAuth URL → redirect
@router.get("/google/callback")     # code exchange → cookie set → onboarding
@router.post("/verify-email")       # body: {token}
@router.post("/resend-verification")
@router.post("/forgot-password")    # body: {email}
@router.post("/reset-password")     # body: {token, new_password}
@router.get("/sessions")            # aktif oturumlar listesi
@router.delete("/sessions/{id}")    # uzaktan oturum kapat
```

Her endpoint yanıtı format:
```json
{
  "ok": true,
  "data": { ... },
  "meta": {
    "plan": "pro",
    "quotas": { "backtest_runs": {"used": 3, "limit": 50} }
  }
}
```

Hata yanıtı:
```json
{
  "ok": false,
  "error": {
    "code": "QUOTA_EXCEEDED",
    "tr": "Günlük kotanız doldu.",
    "en": "Daily quota exceeded.",
    "upgrade_url": "https://piyasapilotu.com/pricing"
  }
}
```

## 3.5 · Korunan Endpoint'lerin Güncellenmesi

`backend/api/main.py`'deki endpoint'lere `Depends` ekle:

```python
# Sadece giriş yapılmış kullanıcı (tüm planlar)
@app.get("/api/v2/candles", dependencies=[Depends(get_current_user)])

# Backtest Pro gerektiren
@app.post("/api/backtest/wfa",           dependencies=[Depends(require_backtest_pro)])
@app.post("/api/backtest/monte-carlo",   dependencies=[Depends(require_backtest_pro)])
@app.post("/api/backtest/portfolio",     dependencies=[Depends(require_backtest_pro)])

# Kota + giriş gerektiren
@app.post("/api/backtest/run",           dependencies=[Depends(require_quota("backtest_runs_per_day"))])

# Scanner — Pro+
@app.post("/api/screener/scan",          dependencies=[Depends(require_scanner)])

# API erişimi — Ultra+
@app.get("/api/v1/public/*",             dependencies=[Depends(require_api_access)])

# Admin
@app.get("/api/admin/*",                 dependencies=[Depends(require_admin)])
```

---

# BÖLÜM 4 — Ekran Tasarımları (Wireframe Düzeyinde)

> Her ekran vanilla TypeScript + Bootstrap ile yazılacak.
> Mevcut bileşen stili takip edilecek (`frontend/src/components/`).

## 4.1 · Landing Page (`frontend/src/pages/LandingPage.ts`)

**URL:** `piyasapilotu.com` (misafir kullanıcı)

```
┌────────────────────────────────────────────────────────┐
│  [PiyasaPilot Logo]          [Giriş Yap] [Ücretsiz Başla] │
├────────────────────────────────────────────────────────┤
│                                                        │
│   HERO BÖLÜM                                          │
│   "Algoritmik trading artık herkes için"               │
│   "BIST, Kripto ve Global Piyasalar"                   │
│   [Demo İzle] [Ücretsiz Başla — Kredi kartı gerekmez]  │
│                                                        │
│   [Statik demo grafik — BTCUSDT örneği, gerçek zaman  │
│    değil, sadece görsel — hardcoded 30 günlük bar]     │
│                                                        │
├────────────────────────────────────────────────────────┤
│   ÖZELLİKLER                                          │
│   [📊 Grafik Lab]  [🔬 Backtest Pro]  [📰 KAP Haberleri] │
│   [💼 Portfolio]   [🤖 Sinyaller]     [📚 Eğitimler]  │
├────────────────────────────────────────────────────────┤
│   FİYATLANDIRMA — 3 kart                             │
│   [Ücretsiz $0]  [Pro $19.99/ay]  [Ultra $49.99/ay]   │
│   Yıllık %20 indirim toggle                           │
├────────────────────────────────────────────────────────┤
│   FOOTER                                              │
│   [Kullanım Koşulları] [Gizlilik] [Çerezler]          │
│   "PiyasaPilot yatırım tavsiyesi vermez."             │
└────────────────────────────────────────────────────────┘
```

**Detaylar:**
- Navbar: `piyasapilotu.com` → logo sol, "Giriş Yap" + "Ücretsiz Başla" sağ
- Hero: Animasyonlu counter (kullanıcı sayısı, backtest sayısı — gerçek veya placeholder)
- Demo grafik: statik SVG veya lightweight-charts readonly modda, BTCUSDT son 30 gün
- Özellikler: 6 kart, her biri bir ekran görüntüsü ile
- Fiyatlandırma: 3 kolon, önerilen "Pro" sütunu highlighted
- "Yıllık öde, 2 ay bedava" toggle (aylık/yıllık)
- CTA butonları "Ücretsiz Başla" → `/register`

---

## 4.2 · Login Ekranı (`frontend/src/pages/LoginPage.ts`)

**URL:** `piyasapilotu.com/login`

```
┌─────────────────────────────────────────┐
│                                         │
│        [PiyasaPilot Logo]               │
│         Hesabınıza giriş yapın          │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  📧  E-posta adresi             │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │  🔒  Şifre              [👁]    │    │
│  └─────────────────────────────────┘    │
│                                         │
│  [Şifremi Unuttum?]        hatırlat ☑  │
│                                         │
│  [         Giriş Yap         ]          │
│                                         │
│  ─────────── veya ───────────           │
│                                         │
│  [ 🔵  Google ile Devam Et ]            │
│                                         │
│  Hesabınız yok mu? [Ücretsiz Kayıt Ol] │
│                                         │
│  [TR] [EN]   🌙/☀️ Tema               │
└─────────────────────────────────────────┘
```

**Davranışlar:**
- Email input: `type="email"`, `autocomplete="email"`
- Şifre: `type="password"`, göz ikonu ile toggle
- "Giriş Yap" → `POST /api/auth/login` → cookie set → `GET /api/auth/me` → terminal
- Google butonu → `GET /api/auth/google` → Google OAuth → callback → terminal
- Başarılı giriş: eğer `onboarding_done=false` → `/onboarding`, değilse `/app`
- Hata: email/şifre yanlış → "E-posta veya şifre hatalı." (hangi birinin yanlış olduğu söylenmez — güvenlik)
- 5 başarısız denemede 30 saniyelik cooldown

---

## 4.3 · Kayıt Ekranı (`frontend/src/pages/RegisterPage.ts`)

**URL:** `piyasapilotu.com/register`

```
┌─────────────────────────────────────────┐
│                                         │
│        [PiyasaPilot Logo]               │
│         Ücretsiz hesap oluşturun        │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │  👤  Ad Soyad                    │   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  │  📧  E-posta adresi              │   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  │  🔒  Şifre (min 8 karakter) [👁] │   │
│  └──────────────────────────────────┘   │
│  ┌──────────────────────────────────┐   │
│  │  🔒  Şifreyi Onayla         [👁] │   │
│  └──────────────────────────────────┘   │
│                                         │
│  ☑ Kullanım Koşulları'nı kabul ediyorum │
│  ☑ Gizlilik Politikası'nı okudum       │
│                                         │
│  [       Hesap Oluştur        ]         │
│                                         │
│  ─────────── veya ───────────           │
│  [ 🔵  Google ile Kayıt Ol ]            │
│                                         │
│  Hesabınız var mı? [Giriş Yapın]        │
└─────────────────────────────────────────┘
```

**Doğrulama (client-side + server-side):**
- Email: RFC 5322 formatı
- Şifre: min 8 karakter, en az 1 büyük harf, 1 rakam
- "Şifreyi Onayla" eşleşmesi
- Başarılı kayıt: "E-posta kutunuzu kontrol edin" ekranı → email doğrulama

---

## 4.4 · Email Doğrulama Bekliyor Ekranı

```
┌─────────────────────────────────────────┐
│                                         │
│        [PiyasaPilot Logo]               │
│                                         │
│           📬                            │
│   E-posta adresinizi doğrulayın         │
│                                         │
│  enes@gmail.com adresine bir bağlantı  │
│  gönderdik. Bağlantıya tıklayarak      │
│  hesabınızı etkinleştirin.             │
│                                         │
│  [Yeniden Gönder — 60s]                 │
│                                         │
│  E-posta gelmediyse spam/gereksiz      │
│  klasörünüzü kontrol edin.             │
│                                         │
└─────────────────────────────────────────┘
```

---

## 4.5 · Onboarding Ekranı (`frontend/src/pages/OnboardingPage.ts`)

**URL:** `/onboarding` — sadece `onboarding_done=false` olan kullanıcılar

```
┌─────────────────────────────────────────┐
│  PiyasaPilot'a hoş geldin, Enes! 👋     │
│                                         │
│  Adım 1 / 3: Dil Tercihiniz            │
│  ● Türkçe    ○ English                  │
│                                         │
│  Adım 2 / 3: İlk Takip Etmek İstediğiniz │
│  ○ BIST Hisseleri   ○ Kripto   ○ İkisi  │
│  Varsayılan sembol: [BTCUSDT ▾]         │
│                                         │
│  Adım 3 / 3: Tema                       │
│  ● 🌙 Koyu    ○ ☀️ Açık                 │
│  Renk: ● Amber  ○ Mavi  ○ Yeşil        │
│                                         │
│  [  Terminale Git → ]                   │
│                                         │
│  Planınız: Ücretsiz → [Pro'ya Geç]      │
└─────────────────────────────────────────┘
```

Tamamlandığında: `PATCH /api/auth/me/settings` + `onboarding_done=true` → `/app`

---

## 4.6 · Şifremi Unuttum / Sıfırlama

**Unuttum ekranı:**
```
┌─────────────────────────────────────────┐
│  Şifremi Sıfırla                        │
│                                         │
│  [ 📧  E-posta adresiniz ]              │
│  [   Sıfırlama Bağlantısı Gönder  ]     │
│                                         │
│  [← Giriş Yap]                          │
└─────────────────────────────────────────┘
```

**Sıfırlama ekranı** (token URL'sinden gelir):
```
┌─────────────────────────────────────────┐
│  Yeni şifrenizi belirleyin              │
│                                         │
│  [ 🔒 Yeni Şifre (min 8 kar.)  [👁] ]  │
│  [ 🔒 Yeni Şifreyi Onayla      [👁] ]  │
│                                         │
│  [    Şifremi Güncelle    ]             │
└─────────────────────────────────────────┘
```

---

## 4.7 · Terminal Ekranı — Kota/Plan Upgrade UI

Terminal içinde bir özellik kısıtlanmışsa:

**Ücretsiz kullanıcı Backtest Pro özelliğine tıklarsa:**
```
┌──────────────────────────────────────────┐
│  🔒 Bu özellik Pro planında              │
│                                          │
│  Walk-Forward Analysis, Monte Carlo ve   │
│  Heatmap optimizasyonu için Pro plana    │
│  geçin.                                  │
│                                          │
│  Pro: $19.99/ay  [Pro'ya Geç]           │
│                  [Kapat]                 │
└──────────────────────────────────────────┘
```

**Günlük kota dolduğunda:**
```
┌──────────────────────────────────────────┐
│  ⏰ Günlük backtest kotanız doldu        │
│                                          │
│  Bugün 5/5 backtest çalıştırdınız.      │
│  Yarın UTC 00:00'da yenilenir.           │
│                                          │
│  Pro planında 50 backtest/gün            │
│  Ultra planında sınırsız backtest        │
│                                          │
│  [Pro'ya Geç — $19.99/ay]  [Tamam]      │
└──────────────────────────────────────────┘
```

**Veri durumu badge'leri (grafik başlığının yanında):**
```
🟢 Canlı     → Lisanslı feed (Ultra)
🟡 Gecikmeli → yfinance (Free/Pro)
🔴 Çevrimdışı → Cache
```

---

# BÖLÜM 5 — Ödeme Sistemi (Stripe)

> Tahmini süre: 2 gün | Bağımlılık: Bölüm 3 tamamlanmış olmalı

## 5.1 · Stripe Kurulum Notları

1. `stripe.com` → hesap aç → API Keys → `STRIPE_SECRET_KEY` ve `STRIPE_WEBHOOK_SECRET`
2. Products oluştur:
   - "PiyasaPilot Pro Monthly" → `price_monthly_usd: 19.99`
   - "PiyasaPilot Pro Yearly" → `price_yearly_usd: 199.99`
   - "PiyasaPilot Ultra Monthly" → `49.99`
   - "PiyasaPilot Ultra Yearly" → `499.99`
3. Price ID'leri `.env.example`'a ekle

## 5.2 · Backend Ödeme Endpoint'leri

**Yeni dosya:** `backend/payments/stripe_service.py`

```python
# pip install stripe --break-system-packages
import stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class StripeService:
    async def create_checkout_session(self, user_id: int, price_id: str,
                                       billing_period: str) -> str:
        """Stripe Checkout oturumu oluştur, URL döndür."""
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer_email=user_email,
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url="https://piyasapilotu.com/payment/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="https://piyasapilotu.com/pricing",
            metadata={"user_id": str(user_id)},
        )
        return session.url

    async def handle_webhook(self, payload: bytes, sig_header: str) -> None:
        """Stripe webhook olaylarını işle."""
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
        )
        if event.type == "checkout.session.completed":
            await self._activate_subscription(event.data.object)
        elif event.type == "customer.subscription.deleted":
            await self._deactivate_subscription(event.data.object)
        elif event.type == "invoice.payment_failed":
            await self._handle_payment_failure(event.data.object)
```

**Endpoint'ler:**
```
POST /api/payments/checkout          → Stripe checkout URL üret
POST /api/payments/webhook           → Stripe webhook handler (imza doğrulamalı)
GET  /api/payments/subscription      → mevcut abonelik durumu
POST /api/payments/cancel            → aboneliği iptal et
GET  /payment/success                → ödeme sonrası yönlendirme sayfası
```

## 5.3 · Fiyatlandırma Sayfası (`frontend/src/pages/PricingPage.ts`)

```
┌───────────────────────────────────────────────────────────────┐
│                  Planınızı Seçin                              │
│                                                               │
│          [Aylık]  ⟷  [Yıllık — 2 ay BEDAVA]                  │
│                                                               │
│  ┌────────────┐   ┌────────────────────┐   ┌──────────────┐  │
│  │  Ücretsiz  │   │        PRO         │   │    ULTRA     │  │
│  │    $0      │   │   ★ $19.99/ay ★   │   │  $49.99/ay  │  │
│  │            │   │  En Popüler        │   │              │  │
│  │ ✅ Terminal │   │ ✅ Terminal        │   │ ✅ Her şey   │  │
│  │ ✅ 5 BT/gün│   │ ✅ 50 BT/gün      │   │ ✅ Sınırsız  │  │
│  │ ❌ BT Pro  │   │ ✅ Backtest Pro    │   │ ✅ Backtest  │  │
│  │ ❌ Scanner │   │ ✅ Scanner         │   │ ✅ Canlı veri│  │
│  │ ❌ Telegram│   │ ✅ Telegram Bot    │   │ ✅ API Erişim│  │
│  │ BIST30 Mali│   │ BIST100 Mali       │   │ Tüm Mali     │  │
│  │            │   │                    │   │              │  │
│  │[Ücretsiz   │   │ [Pro'ya Geç →]     │   │[Ultra Ol →]  │  │
│  │ Başla]     │   │                    │   │              │  │
│  └────────────┘   └────────────────────┘   └──────────────┘  │
│                                                               │
│  ✅ Güvenli ödeme (Stripe)  ✅ İstediğin zaman iptal         │
│  ✅ 7 gün para iade garantisi                                 │
└───────────────────────────────────────────────────────────────┘
```

---

# BÖLÜM 6 — Admin Yönetim Paneli

> URL: `piyasapilotu.com/admin` — sadece `role=admin`

## 6.1 · Yeni dosya: `frontend/src/pages/admin/AdminPanel.ts`

```
┌─────────────────────────────────────────────────────┐
│  PiyasaPilot Admin  │  [Enes A. ▾]  [Çıkış]        │
├──────────┬──────────────────────────────────────────┤
│          │                                          │
│ 📊 Özet  │  ÖZET KART DASHBOARD                    │
│ 👥 Kullanıcılar  │  [Toplam Kullanıcı: 147]         │
│ 💳 Abonelikler   │  [Pro: 43]  [Ultra: 12]          │
│ 📰 Haberler      │  [Bugünkü gelir: $847]           │
│ 🔌 Veri Kalitesi │  [Aktif oturumlar: 28]           │
│ 📋 Audit Log     │                                  │
│ ⚙️  Sistem        │                                  │
│                  │                                  │
└──────────────────────────────────────────────────────┘
```

**Admin sayfaları:**

### 6.1.1 · Kullanıcı Yönetimi

```
Arama: [          ]  Filtre: [Tüm Planlar ▾]  [Tüm Durumlar ▾]

ID    E-posta              Plan     Durum   Kayıt      Son Giriş   İşlemler
───────────────────────────────────────────────────────────────────────────
1234  enes@gmail.com       Ultra    Aktif   2026-05-10  Bugün      [↗] [✏️] [⛔]
1235  test@test.com        Free     Aktif   2026-05-14  Dün        [↗] [✏️] [⛔]
1236  banned@mail.com      Free     Banlı   2026-05-01  2026-05-01 [↗] [✏️] [✅]
```

Kullanıcı detay sayfası:
- Plan değiştir (dropdown)
- Rol değiştir (free/pro/ultra/admin)
- Hesabı banla / aktifleştir
- Tüm oturumlarını kapat
- Audit log görüntüle

**Endpoint'ler:**
```
GET    /api/admin/users              → liste (sayfalı)
GET    /api/admin/users/{id}         → detay
PATCH  /api/admin/users/{id}/role    → rol değiştir
PATCH  /api/admin/users/{id}/plan    → plan değiştir
POST   /api/admin/users/{id}/ban     → banla
POST   /api/admin/users/{id}/unban   → banı kaldır
DELETE /api/admin/users/{id}/sessions → tüm oturumları kapat
```

### 6.1.2 · Abonelik Yönetimi

```
Toplam aylık yinelenen gelir: $1,247.43
Pro aboneler: 43    Ultra aboneler: 12
Bu ay yeni: 8       Bu ay iptal: 2

[Stripe Dashboard'a Git →]
```

### 6.1.3 · Veri Kalite İzleme

```
Son 24 saat veri kalitesi:

Kaynak         Sembol    Son Bar     Gecikme   Durum
───────────────────────────────────────────────────
yfinance       THYAO     14:30       15dk      🟡 Normal
Binance WS     BTCUSDT   15:47:32    <1s       🟢 Canlı
yfinance       XU100     14:30       15dk      🟡 Normal
ClickHouse     —         —           —         🟢 Bağlı

Uyarılar:
⚠ EKGYO: 2 gap tespit edildi (09:30–10:15 arası)
```

### 6.1.4 · Audit Log Görüntüleyici

```
Filtre: [Kullanıcı ID] [Aksiyon ▾] [Tarih aralığı]

2026-05-16 15:47  user:1234  login           ip:85.105.x.x
2026-05-16 15:43  user:1235  backtest_run    symbol:THYAO
2026-05-16 15:40  admin:1    user_role_change user:1236 free→pro
```

---

# BÖLÜM 7 — Ödeme Sonrası ve Plan Yönetimi Frontend

## 7.1 · `/payment/success` sayfası

```
┌─────────────────────────────────────────┐
│                                         │
│      🎉  Pro planına hoş geldiniz!      │
│                                         │
│  Backtest Pro, Scanner ve Telegram      │
│  Bot artık aktif.                       │
│                                         │
│  [  Terminale Git  ]                    │
│                                         │
└─────────────────────────────────────────┘
```

## 7.2 · Hesap Ayarları (`/settings`)

```
┌────────────────────────────────────────────┐
│  Hesap Ayarları                            │
├────────────────────────────────────────────┤
│  👤 Profil                                 │
│     Ad: [Enes Aktaş          ]  [Kaydet]   │
│     Email: enes@gmail.com  ✅ Doğrulandı   │
│     Avatar: [Değiştir]                     │
├────────────────────────────────────────────┤
│  🔒 Güvenlik                               │
│     [Şifremi Değiştir]                     │
│     Aktif oturumlar: 2                     │
│     [Tüm Oturumları Kapat]                 │
├────────────────────────────────────────────┤
│  💳 Abonelik — PRO                         │
│     Sonraki ödeme: 2026-06-16  $19.99      │
│     [Faturalar] [Ultra'ya Geç] [İptal Et]  │
├────────────────────────────────────────────┤
│  🌍 Dil ve Bölge                           │
│     Dil: ● TR  ○ EN                        │
├────────────────────────────────────────────┤
│  🗑️  Hesabı Sil                            │
│     [Hesabımı Kalıcı Olarak Sil]           │
└────────────────────────────────────────────┘
```

---

# BÖLÜM 8 — i18n ve Hukuki Sayfalar

## 8.1 · i18n Sistemi (`frontend/src/i18n/`)

```
frontend/src/i18n/
├── index.ts     # I18nManager singleton
├── tr.ts        # Türkçe string'ler (mevcut constants/tr.ts'den taşı)
└── en.ts        # İngilizce karşılıklar
```

`I18nManager`:
- `init()` → localStorage'daki `pp_lang` → yoksa browser dili → yoksa `'tr'`
- `setLang(lang)` → modül lazy load → DOM'u güncelle
- `t(key)` → string döndür

`tr.ts`'de OLMASI GEREKEN minimum anahtar grupları:
```ts
// Auth
AUTH_LOGIN_TITLE, AUTH_REGISTER_TITLE, AUTH_EMAIL, AUTH_PASSWORD,
AUTH_FORGOT_PASSWORD, AUTH_GOOGLE_BUTTON, AUTH_NO_ACCOUNT,
AUTH_VERIFY_EMAIL_MSG, AUTH_RESET_PASSWORD_TITLE,
// Errors
ERR_INVALID_CREDENTIALS, ERR_EMAIL_TAKEN, ERR_QUOTA_EXCEEDED,
ERR_UPGRADE_REQUIRED, ERR_SESSION_EXPIRED,
// Plan
PLAN_FREE, PLAN_PRO, PLAN_ULTRA,
PLAN_UPGRADE_CTA, PLAN_FEATURE_LOCKED,
// UI
UI_LIVE, UI_DELAYED, UI_OFFLINE,
PAPER_MODE_BANNER,
RISK_DISCLAIMER,
```

## 8.2 · Hukuki Sayfalar

**Dosyalar:**
```
frontend/src/pages/legal/
├── TermsPage.ts       # /legal/terms
├── PrivacyPage.ts     # /legal/privacy
└── CookiesPage.ts     # /legal/cookies
```

**Her sayfada:**
- TR/EN içerik (i18n ile)
- "Yatırım tavsiyesi değildir" uyarısı
- Son güncelleme tarihi

**Cookie banner** (`frontend/src/components/CookieBanner.ts`):
```
┌────────────────────────────────────────────────────────────┐
│ 🍪 Bu site yalnızca oturum ve tercih çerezleri kullanır.   │
│ [Kabul Et]  [Reddet]  [Detaylar →]                        │
└────────────────────────────────────────────────────────────┘
```

**Footer risk uyarısı** (her sayfada):
```html
<p class="risk-disclaimer">
  PiyasaPilot yatırım tavsiyesi vermez. Gösterilen tüm veriler
  yalnızca bilgilendirme amaçlıdır. Gerçek emir gönderimi desteklenmez.
</p>
```

## 8.3 · Paper Mode Banner (her backtest / paper sayfasında)

```html
<div class="paper-mode-banner">
  📋 KAĞIT İŞLEM MODU — Bu emirler gerçek piyasaya gönderilmemektedir.
</div>
```

---

# BÖLÜM 9 — Mevcut UI Hataları

> Bu bölüm diğer bölümlerden bağımsız yapılabilir.

## 9.1 · Grafik: Timeframe Değişiminde Siyah Ekran

**Dosya:** `frontend/src/components/ChartPanel.ts`

Timeframe değişiminde:
1. `series.setData([])` → eski seriyi temizle ama koru
2. Loading overlay göster: `<div class="chart-loading">Yükleniyor...</div>`
3. WS bağlantısı koptuğunda: max 3 retry, exponential backoff (1s, 2s, 4s)
4. Retry sonrası hâlâ bağlanamazsa: "⚠ Bağlantı kurulamadı [Yeniden Dene]"

## 9.2 · Koyu Tema Kontrast

**Dosya:** `frontend/style.css`

```css
[data-theme="dark"] .financial-table td.muted,
[data-theme="dark"] .financial-table th {
  color: #c8cdd4; /* WCAG AA: 4.5:1 oranını karşılar */
}
```

## 9.3 · Haberler — KAP Gerçek İçerik

**Dosya:** `backend/news/kap_rss.py` (yeni)

KAP RSS: `https://www.kap.org.tr/tr/rss/` → parse → `news.sqlite3` → `/api/news?symbol=THYAO`
Boş döndüğünde: `{"items": [], "message": "Bu sembol için haber bulunamadı."}` — placeholder yasak.

## 9.4 · Strateji Çalıştır Butonu

**Dosya:** `frontend/src/components/StrategyPanel.ts`

Butonu panel header'ına taşı → loading spinner → tamamlanınca toast.

## 9.5 · Public Route ve Terminal Shell İzolasyonu — BLOCKER

**Kaynak:** `WEB_UX_TEST_RAPORU.md` — 2026-05-16 QA  
**Dosyalar:** `frontend/src/app.ts`, `frontend/index.html`, public page bileşenleri

- [x] `/`, `/pricing`, `/login`, `/register`, `/forgot-password`, `/reset-password`, `/verify-email`, `/onboarding`, `/settings`, `/admin`, `/legal/*`, `/changelog`, `/waitlist`, `/shared/*` route'larında terminal shell hiç mount edilmesin.
- [x] Public route render edildiğinde `app.ts` terminal init akışından erken çıkılsın; `Sidebar`, `MultiChartLayout`, `PortfolioPanel`, `StrategyPanel`, `SignalFeed`, websocket ve polling başlatılmasın.
- [x] Public sayfalarda `market-ticker`, `topbar`, `app-layout`, favori yıldızları, terminal tab butonları, tema paneli ve terminal toast mesajları DOM/erişilebilirlik ağacında görünmesin.
- [x] `/register` ve diğer public sayfalarda alakasız `✓ Backtest tamamlandı` toast'ı oluşmasın.
- [x] `/login` sayfasında `Giriş Yap` submit butonu tek görünür/etkileşilebilir giriş hedefi olsun; gizli `strategy-card` gibi terminal butonları locator ve screen reader hedefi olmasın.

**Kabul kriteri:**
```bash
cd frontend && npm run typecheck && npm run build
```

Playwright/Browser QA:
- `/` body text içinde `Grafik`, `Portföy`, `Strateji`, `Favoriler`, `Backtest tamamlandı` terminal artıkları bulunmamalı.
- `/login` üzerinde giriş butonu tıklaması görünür auth submit butonuna gitmeli.
- `/pricing` yalnızca fiyatlandırma/public layout içermeli.

## 9.6 · Mobil Web `/app` Kullanılabilirliği — BLOCKER

**Kaynak:** `WEB_UX_TEST_RAPORU.md` — 390x844 viewport testi  
**Dosyalar:** `frontend/style.css`, `frontend/src/app.ts`, `frontend/src/components/Sidebar.ts`, `frontend/src/components/MultiChartLayout.ts`

- [x] Mobilde sidebar varsayılan kapalı gelsin; sembol seçimi ilk render'da dev liste basmasın.
- [x] `/app` mobil ilk ekranda dev sembol listesi değil, aktif grafik veya seçili iş akışı görünsün.
- [x] Topbar sekmeleri mobilde dikey kırılmasın; yatay scroll/compact nav ile çalışsın.
- [x] `Haberler 8 99+` gibi sıkışık badge/metin görüntüsü düzeltilsin.
- [x] Multi-chart mobilde tek sütun/tek panel varsayılanına düşsün; 2x2 layout küçük ekranda zorlanmasın.

**Kabul kriteri:**
- 390x844 viewport'ta yatay overflow olmamalı.
- İlk ekranda grafik veya aktif sekme içeriği görünmeli.
- Sidebar aç/kapat akışı dokunmatik kullanımda net olmalı.

## 9.7 · Auth/Admin/Settings Route Koruması ve UX

**Dosyalar:** `frontend/src/app.ts`, `frontend/src/auth/AuthManager.ts`, `frontend/src/pages/SettingsPage.ts`, `frontend/src/pages/admin/AdminPanel.ts`, `backend/api/auth_router.py`, `backend/api/admin_router.py`

- [x] `/settings` public route gibi davranmasın; kullanıcı giriş yapmadıysa login'e veya "giriş gerekli" ekranına yönlensin.
- [x] `/admin` sadece admin kullanıcıya açılsın; yetkisiz kullanıcıya net 403/login durumu gösterilsin.
- [x] Auth gerektiren sayfalar public route listesi içinde terminal shell ile birlikte render edilmesin; protected layout ayrımı netleşsin.
- [x] Google login/register butonları entegrasyon hazır değilse gizlensin veya disabled + "yakında" durumuna alınsın; hazırsa callback ve hata akışı E2E testine eklensin.

## 9.8 · Shared Backtest 404 Empty State

**Dosya:** `frontend/src/pages/SharedBacktestPage.ts`

- [x] `/shared/{slug}` 404 döndüğünde teknik hata yerine ürün dilinde empty state göster: "Bu paylaşım bulunamadı veya süresi doldu."
- [x] Kullanıcıya net aksiyon ver: Terminale dön, fiyatlandırmayı gör, yeni backtest oluştur.
- [x] Hatalı slug, silinmiş paylaşım ve süresi dolmuş paylaşım ayrı mesajlanabiliyorsa ayrıştır.

## 9.9 · Sinyaller Boş Durum ve Veri Güven Kapısı Açıklaması

**Dosyalar:** `frontend/src/components/SignalFeed.ts`, `frontend/src/app.ts`, `backend/api/main.py`

- [x] `signals_emitted=0` ve `skipped_untrusted>0` durumunda UI sadece "Henüz sinyal yok" demesin.
- [x] Lisanslı BIST/VİOP feed bağlı olmadığı için sinyaller güven kapısında bekliyorsa bunu açıkça yaz.
- [x] Hangi kaynak eksik, hangi sembol grupları etkileniyor, kripto sinyalleri çalışıyor mu gibi kullanıcıya karar verdiren bilgi göster.
- [x] Telegram yapılandırılmamışsa "Telegram: yapılandırılmamış" yanında kurulum/ayar aksiyonu sun.

## 9.10 · Portföy Metrik Formatı ve Paper Trading Güven Dili

**Dosya:** `frontend/src/components/PortfolioPanel.ts`

- [x] `+-0,00%` formatı kaldır; standart format: `-0,00%`, `+0,00%`, `0,00%`.
- [x] Aşırı zararda görünen sanal cüzdanların demo/test/paper niteliği açık yazılsın.
- [x] `Dondur`, `Sıfırla` gibi riskli paper cüzdan aksiyonlarına onay modalı veya açıklama ekle.
- [x] Portföy ekranında gerçek emir gönderilmediği net kalmaya devam etsin; fakat kullanıcı "sistem yanlış hesaplıyor" hissine düşmesin.

## 9.11 · Haberler Sekmesi Bilgi Mimarisi

**Dosyalar:** `frontend/index.html`, `frontend/src/app.ts`, `frontend/src/components/NewsPanel.ts`

- [x] Haberler sekmesi ana nav'a net 8. sekme olarak eklensin veya ayrı bildirim merkezi olarak ayrıştırılsın.
- [x] `Haberler 8 99+` metin/badge sıkışması düzelt.
- [x] `99+` badge anlamı netleşsin: okunmamış haber mi, KAP mı, toplam haber mi?
- [x] Klavye kısayol overlay'i `8 = Haberler` ile nav gerçekliği tutarlı olsun.

## 9.12 · Mali Analiz Empty State Bağlamı

**Dosya:** `frontend/src/components/MaliAnalizPanel.ts`

- [x] BTCUSDT gibi mali analiz desteklenmeyen sembollerde "Oran verisi yok — Yenile ile veri çekin" yerine destek kapsamı açıklansın.
- [x] BIST 30/BIST 100 kapsamı, veri kaynağı ve son güncelleme durumu kullanıcıya açık gösterilsin.
- [x] "Yenile" butonu gerçekten veri çekemeyecek sembollerde yanlış beklenti yaratmasın.

## 9.13 · Buton ve Etiket Dili

**Dosyalar:** `frontend/index.html`, `frontend/src/app.ts`, ilgili componentler

- [x] `Tarayıcı` sekme adı screener için yeniden değerlendirilsin: öneri `Tarama` veya `Piyasa Tarama`.
- [x] `Ayar` butonu sadece tema paneli açıyorsa `Tema` olarak değiştirilsin; genel hesap ayarları ile karışmasın.
- [x] Icon-only butonlarda tooltip/aria-label eksikleri tamamlanmalı.

## 9.14 · Public/Terminal Code Splitting ve İlk Yük Performansı

**Dosyalar:** `frontend/src/app.ts`, Vite config gerekiyorsa ilgili config

- [x] Public sayfalar terminal chart/backtest/education bundle'ını yüklemesin.
- [x] Terminal panelleri dynamic import ile bölünsün: chart, strategy, education, financials, news.
- [x] `Chart.js` ve `lightweight-charts` public landing/auth bundle'ından ayrıştırılsın.
- [x] Build uyarısı kapatılarak değil, gerçek code splitting ile giderilsin.

**Mevcut ölçüm:**
- `dist/assets/index-*.js` yaklaşık `530.73 kB`, gzip `150.24 kB`
- Code splitting sonrası Vite 500 kB chunk uyarısı kalktı; ana `index` chunk yaklaşık 23 kB.

## 9.15 · README ve Frontend Dokümantasyon Tutarlılığı

**Dosyalar:** `README.md`, `frontend/README.md`

- [x] Kök README hızlı başlangıçta `cd piyasapilot-v2` yerine mevcut dizin olan `cd frontend` yazılsın.
- [x] `frontend/README.md` içinde "frontend doğrudan dış API kullanır, backend gerekmez" ifadesi güncel mimariyle uyumlu hale getirilsin.
- [x] Zero-demo/backend proxy veri politikası tek bir doğru açıklama ile yazılsın.
- [x] Kurulum adımları backend + frontend birlikte çalışacak şekilde doğrulansın.

## 9.16 · QA Regresyon Checklist

Bu bölümdeki işler bitmeden production kabulü yapılmaz.

- [x] `/`, `/pricing`, `/login`, `/register` public sayfalarında terminal DOM sızıntısı yok.
- [x] `/app` desktop: Grafik, Portföy, Strateji, Tarama, Sinyaller, Eğitimler, Mali Analiz, Haberler sekmeleri tek tek açılıyor.
- [x] `/app` mobile 390x844: ana içerik görünür, sidebar kapalı, yatay overflow yok.
- [x] `/shared/olmayan-slug` ürün dilinde 404 empty state gösteriyor.
- [x] `npm run typecheck` başarılı.
- [x] `npm run build` başarılı ve chunk uyarısı kabul edilebilir seviyeye indirilmiş.
- [x] `WEB_UX_TEST_RAPORU.md` içindeki her madde kapandıktan sonra rapora "çözüldü" notu veya yeni QA raporu eklenmiş.

---

## 9.17 · KRİTİK — Market Ticker Şeridi Hiç Dolmuyor

**Dosyalar:** `frontend/index.html` (satır 28–31), `frontend/src/app.ts`, `frontend/style.css`

**Sorun:** `#market-ticker` ve `#ticker-track` div'leri HTML'de var, CSS `--ticker-h: 30px` ile 30px yükseklik ayrılıyor. `app.ts` içinde `#ticker-track`'i dolduran hiçbir kod yok. Terminal açıldığında "Canlı Piyasa" yazısıyla boş karanlık şerit görünüyor; içerik 30px gereksiz aşağı itiyor.

- **Seçenek A (Alternatif, uygulanmadı):** `DataEngine.onPriceUpdate` akışından gelen fiyatları `#ticker-track` içine `<span>` olarak ekle (sembol, fiyat, % değişim). CSS animasyonu için şerit zaten hazır.
- [x] **Seçenek B (Hızlı Düzeltme):** `#market-ticker`'ı `display:none` yap; `--ticker-h: 0px` olarak sıfırla; padding hesabını güncelle.

**Kabul:** Terminal açıldığında boş şerit görünmüyor.

---

## 9.18 · KRİTİK — Grafik Paneli: Renko Butonu Disabled Ama Görünür

**Dosya:** `frontend/src/components/ChartPanel.ts` satır 528

- [x] `Rnk` (Renko) butonu disabled + soluk olarak görünüyor, "bozuk buton" izlenimi veriyor. Tamamen kaldır ya da toolbar dışında ayrı "Yakında" bölümüne taşı.

---

## 9.19 · Grafik Paneli: Klavye G Döngüsünde 2×1 Layout Atlıyor

**Dosya:** `frontend/src/app.ts` — klavye kısayolları bölümü

- [x] G tuşu döngüsünü `['1x1', '1x2', '2x2']`'dan `['1x1', '1x2', '2x1', '2x2']`'ye güncelle.
- [x] Klavye kısayol overlay'indeki açıklamayı da güncelle.

---

## 9.20 · Grafik Paneli: Şablon Boş İsimle Kaydedilebiliyor

**Dosya:** `frontend/src/components/ChartPanel.ts` — `#save-template-btn` click handler

- [x] `#new-template-name` boşken kaydet tıklanırsa kayıt yapma; input'a hata stili + "Şablon adı boş olamaz" mesajı göster.

---

## 9.21 · Grafik Paneli: Export PNG/CSV Başarı/Hata Geri Bildirimi Eksik

**Dosya:** `frontend/src/components/ChartPanel.ts` — export buton handler'ları

- [x] Export başarılıysa `✓ Grafik indirildi` toast göster.
- [x] Export başarısızsa `✗ Dışa aktarım başarısız` hata toast göster.

---

## 9.22 · Grafik Paneli: ÖK / PnL / Risk / T/T Tooltip'leri Yetersiz

**Dosya:** `frontend/src/components/ChartPanel.ts` satır 452–455

- [x] `ÖK` → title: `"Önceki Kapanış: Dünün kapanış fiyatını yatay çizgiyle gösterir"`
- [x] `PnL` → title: `"Trade K/Z Overlay: İşlem giriş/çıkış ve kâr/zarar alanlarını gösterir"`
- [x] `Risk` → title: `"Stop/Hedef Çizgileri: Stop-loss ve take-profit seviyelerini gösterir"`
- [x] `T/T` → title: `"Tavan/Taban: BIST günlük limit seviyelerini gösterir"`

---

## 9.23 · Strateji Paneli: Mode Butonu İlk Açılışta Aktif Görünmüyor

**Dosya:** `frontend/src/components/StrategyPanel.ts` — `render()` ve `syncControls()` çağrı sırası

- [x] `render()` içinde HTML yazılırken `seg-btn` butonuna `this.mode === btn.dataset.mode` koşuluyla `active` sınıfını inline ekle.
- [x] `syncControls()` çağrısını DOM hazır olduktan sonraya al.

---

## 9.24 · Strateji Paneli: Slippage Tick Input Model'e Göre Gizlenmiyor

**Dosya:** `frontend/src/components/StrategyPanel.ts`

- [x] `#bt-slippage-model` change event'inde: "Fixed BPS" seçiliyken `#bt-slippage-tick` gizle; "Fixed Tick" seçiliyken `#bt-slippage` (bps) gizle. Başlangıç durumu da buna göre set et.

---

## 9.25 · Strateji Paneli: Walk-Forward / Monte Carlo "Önce Çalıştır" Yönlendirmesi Eksik

**Dosya:** `frontend/src/components/StrategyPanel.ts` — `renderReport()` içinde `walk-forward` ve `monte-carlo` dalları

- [x] `lastResult === null` iken bu sekmelerde: `"Walk-Forward analizi için önce 'Çalıştır' butonuna basın."` mesajı + Çalıştır butonuna işaret eden ok/link göster.

---

## 9.26 · Strateji Paneli: Rapor Arşivine Silme Butonu

**Dosyalar:** `frontend/src/components/StrategyPanel.ts`, backend `DELETE /api/backtest/reports/{run_id}` (mevcut)

- [x] `#report-archive` listesindeki her kayda 🗑 silme butonu ekle.
- [x] Tıklanınca `DELETE /api/backtest/reports/{run_id}` çağır, başarılıysa listeden kaldır, toast göster.

---

## 9.27 · Strateji Paneli: Kayıtlı Strateji Silme Butonu

**Dosya:** `frontend/src/components/StrategyPanel.ts`

- [x] `#saved-strategies` listesindeki her kayda 🗑 silme butonu ekle; kayıtlı stratejiler birikmesin.

---

## 9.28 · Portföy Paneli: Günlük K/Z Yüzde Hesabı Hatalı

**Dosya:** `frontend/src/components/PortfolioPanel.ts` — `walletCardHTML()`

- [x] `dailyLoss >= 0 ? dailyLossPct : -dailyLossPct` ifadesini kaldır; `formatPct(Math.abs(dailyLoss) / w.initial_capital * 100)` kullan, sign ayrı CSS rengiyle göster.

---

## 9.29 · Portföy Paneli: window.confirm() → Uygulama Modalı

**Dosya:** `frontend/src/components/PortfolioPanel.ts` — `resetWallet()`, `haltWallet()`

- [x] `window.confirm()` yerine uygulamanın tema'sına uygun onay modal/dialog bileşeni kullan.
- [x] Onay metninde işlemin sadece paper kayıtlarını etkilediğini belirt.

---

## 9.30 · Screener: İlk Taramada Cache Boş Uyarısı

**Dosya:** `frontend/src/components/Screener.ts` — `scan()`

- [x] Cache'deki veri sayısı çok azsa tarama başlamadan uyarı göster: `"Veri yükleniyor. Bir sembol seçip birkaç saniye bekledikten sonra tekrar deneyin."`
- [x] Tarama sonucuna `"X sembol tarandı, Y sonuç bulundu"` bilgisi ekle.

---

## 9.31 · Screener: Son Tarama Zaman Damgası Eksik

**Dosya:** `frontend/src/components/Screener.ts`

- [x] Tarama tamamlandığında başlık yanına `"Son tarama: HH:MM"` timestamp'i göster.

---

## 9.32 · Haberler: Mark-as-Read Hata Sessiz Atlanıyor

**Dosya:** `frontend/src/components/NewsPanel.ts` — mark-read POST `catch`

- [x] Hata oluşursa kart `news-read` sınıfını geri al; kısa inline mesaj veya toast göster.

---

## 9.33 · Mali Analiz: BIST 30 Yenile İlerleme Göstergesi Eksik

**Dosya:** `frontend/src/components/MaliAnalizPanel.ts` — `refreshAllBtnEl` click handler

- [x] Buton metnini yenileme süreci boyunca `"⟳ Yenileniyor…"` olarak güncelle veya en azından spinner göster.
- [x] Tamamlandığında `"✓ BIST 30 güncellendi"` toast göster.

---

## 9.34 · Mali Analiz: Universe Liste Renk Noktaları Açıklaması (Legend)

**Dosya:** `frontend/src/components/MaliAnalizPanel.ts` — universe list render

- [x] Sembol listesi sidebar'ının üstüne küçük legend ekle: `● Veri var  ● Kısmi  ● Veri yok`

---

## 9.35 · Tasarım: Firefox Scrollbar Stillenmiyor

**Dosya:** `frontend/style.css` — scrollbar bölümü (satır 2318–2321)

- [x] Şunu ekle: `* { scrollbar-width: thin; scrollbar-color: var(--border2) var(--bg); }`

---

## 9.36 · Tasarım: Emoji İkonlar Platform Tutarsız → SVG Geçiş (Uzun Vadeli)

**Dosyalar:** `ChartPanel.ts`, `MultiChartLayout.ts`, `PortfolioPanel.ts`

- [x] `🗑`, `📏`, `⛶`, `📸`, `📊`, `🔗`, `⏳`, `↔️` gibi emoji'leri SVG ikon setine taşı (topbar'da zaten SVG kullanılıyor).

---

## 9.37 · Teknik: any Type Cast'ları Temizle

**Dosya:** `frontend/src/components/StrategyPanel.ts` (`qw = w as any`) ve diğerleri

- [x] `any` cast'larını kaldır; uygun interface/type tanımla.

---

## 9.38 · Teknik: Sidebar LazyLoad IntersectionObserver Memory Leak

**Dosya:** `frontend/src/components/Sidebar.ts`

- [x] `Sidebar` sınıfına `destroy()` ekle; tüm `IntersectionObserver`'ları `disconnect()` et.

---

## 9.39 · Eğitimler: Kategori Değişiminde Tam Re-Render Yerine Kısmi Güncelleme

**Dosya:** `frontend/src/components/EgitimlerPanel.ts` — kategori tıklandığında `this.render()` çağrısı

- [x] Kategori tıklandığında `this.render()` yerine `this.renderResults()` çağır; article scroll pozisyonunu koru.

---

## 9.40 · Regresyon QA — Yeni Bulgular (2026-05-16 Kapsamlı Kod Analizi)

Bu bölümdeki yeni maddeler (9.17–9.39) kapanmadan production kabulü yapılmamalı.

- [x] Market Ticker: ya dolduruluyor ya da kaldırılıyor (9.17)
- [x] Renko butonu kaldırıldı veya taşındı (9.18)
- [x] G klavye döngüsü 2×1 dahil çalışıyor (9.19)
- [x] Şablon boş isimle kaydedilemiyor (9.20)
- [x] Export PNG/CSV toast bildirimi var (9.21)
- [x] Mode butonu ilk açılışta aktif görünüyor (9.23)
- [x] Slippage Tick input model'e göre gizleniyor (9.24)
- [x] Walk-Forward/Monte Carlo boş durumda yönlendirme var (9.25)
- [x] Rapor arşivinde silme butonu çalışıyor (9.26)
- [x] Screener ilk taramada cache boş uyarısı var (9.30)
- [x] Portföy formatPct `+-` üretmiyor (9.28)
- [x] BIST 30 yenile progress göstergesi var (9.33)
- [x] Firefox scrollbar stillenmiş (9.35)

---

# BÖLÜM 10 — Mobil Uygulama Planı (Flutter)

> Bu bölümü Enes geliştiriyor.
> Stack: Flutter + Dart, MVVM + Clean Architecture
> Backend: Aynı FastAPI — ek endpoint'ler eklenecek
> Auth: Cookie yerine Bearer token (mobil)

## 10.1 · Neden Flutter Uygun?

CV'den:
- Flutter & Dart + MVVM + Clean Architecture ✅
- JWT Auth ✅ (backend aynı)
- WebSocket ✅ (canlı veri için)
- MySQL + Redis ✅ (backend katmanı aynı)
- Firebase ✅ (push notification için)

Mevcut web app **mobil için tasarlanmamış:**
- Bootstrap tablo tabanlı → küçük ekranda okunaksız
- lightweight-charts → mobile touch desteği sınırlı
- Çok sekme → mobilde navigation bar gerekiyor

**Karar:** Ayrı Flutter native app → web backend'e bağlanır.

## 10.2 · Flutter App Mimari

```
piyasapilot_mobile/
├── lib/
│   ├── main.dart
│   ├── core/
│   │   ├── di/                    # Dependency Injection (get_it veya riverpod)
│   │   ├── network/
│   │   │   ├── api_client.dart    # Dio + interceptor
│   │   │   ├── ws_client.dart     # WebSocket client
│   │   │   └── auth_interceptor.dart  # 401 → token refresh
│   │   ├── storage/
│   │   │   └── secure_storage.dart    # flutter_secure_storage
│   │   └── theme/
│   │       └── app_theme.dart
│   ├── features/
│   │   ├── auth/
│   │   │   ├── data/
│   │   │   │   ├── auth_repository_impl.dart
│   │   │   │   └── auth_remote_datasource.dart
│   │   │   ├── domain/
│   │   │   │   ├── auth_repository.dart
│   │   │   │   └── usecases/
│   │   │   └── presentation/
│   │   │       ├── login_screen.dart
│   │   │       ├── register_screen.dart
│   │   │       └── auth_viewmodel.dart
│   │   ├── chart/
│   │   │   ├── data/
│   │   │   ├── domain/
│   │   │   └── presentation/
│   │   │       ├── chart_screen.dart      # fl_chart veya custom canvas
│   │   │       └── chart_viewmodel.dart
│   │   ├── watchlist/
│   │   ├── signals/
│   │   ├── news/
│   │   ├── portfolio/
│   │   ├── backtest/              # Sadece Pro/Ultra
│   │   ├── financials/            # Mali Analiz
│   │   └── settings/
│   └── shared/
│       ├── widgets/
│       │   ├── plan_gate_widget.dart   # Kilitli özellik overlay
│       │   └── data_badge_widget.dart  # 🟢/🟡/🔴
│       └── models/
├── pubspec.yaml
├── android/
├── ios/
└── README.md
```

## 10.3 · Flutter Paket Listesi

```yaml
# pubspec.yaml
dependencies:
  flutter_secure_storage: ^9.0.0    # Token güvenli saklama
  dio: ^5.4.0                       # HTTP client + interceptor
  web_socket_channel: ^3.0.0        # WebSocket
  riverpod: ^2.5.0                  # State management (alternatif: bloc)
  go_router: ^13.0.0               # Navigation
  fl_chart: ^0.68.0                # Grafik (lightweight)
  google_sign_in: ^6.2.0           # Google OAuth
  firebase_messaging: ^15.0.0      # Push notification
  firebase_core: ^3.0.0
  intl: ^0.19.0                    # Tarih/sayı formatlama TR/EN
  shimmer: ^3.0.0                  # Loading skeleton
  cached_network_image: ^3.3.0     # Avatar cache
  share_plus: ^9.0.0               # Strateji/grafik paylaş
```

## 10.4 · Backend — Mobil İçin Ek Auth Endpoint

**Mobil Bearer token kullanır (cookie yerine):**

`backend/api/auth_router.py`'e ekle:

```python
@router.post("/mobile/login")
async def mobile_login(body: LoginRequest) -> dict:
    """
    Cookie yerine JSON body'de token döndür.
    Mobil istemciler için.
    """
    user = await auth_service.verify_credentials(body.email, body.password)
    access_token = create_access_token(user.id, user.role)
    plain_refresh, hashed_refresh = create_refresh_token()
    await auth_repo.save_refresh_token(user.id, hashed_refresh, device_name=body.device_name)
    return {
        "ok": True,
        "data": {
            "access_token": access_token,
            "refresh_token": plain_refresh,
            "token_type": "Bearer",
            "expires_in": ACCESS_TOKEN_TTL,
            "user": {...},
        }
    }

@router.post("/mobile/refresh")
async def mobile_refresh(body: RefreshRequest) -> dict:
    """Eski refresh token → yeni access + refresh token çifti (rotation)."""
    ...
```

**Mobil WS bağlantısı:** `wss://piyasapilotu.com/ws/quotes?token=<access_token>` (Bearer header WS'de çalışmaz).

## 10.5 · Flutter Ekran Listesi

```
Kimlik Doğrulama:
├── SplashScreen         → logo + token kontrolü
├── LoginScreen          → email/şifre + Google
├── RegisterScreen
├── EmailVerifyScreen
├── OnboardingScreen     → dil + ilk sembol + tema

Ana Navigasyon (Bottom Tab Bar):
├── 📊 Grafik (ChartScreen)
│    → Sembol seçici (arama modal)
│    → Timeframe seçici (H tab bar)
│    → fl_chart mum grafiği
│    → İndikatör toggle'ları
│    → Veri kaynağı badge (🟢/🟡/🔴)
├── 📋 Watchlist (WatchlistScreen)
│    → Sembol listesi + fiyat + değişim %
│    → WS ile canlı güncelleme
│    → Max sembol limiti (plan bazlı)
├── 📰 Haberler (NewsScreen)
│    → KAP haberleri + okundu işareti
├── 💼 Portföy (PortfolioScreen)
│    → Paper trading özeti
│    → P&L grafik
└── ⚙️  Ayarlar (SettingsScreen)
     → Profil, plan, dil, tema, çıkış

Ekstra (tab dışı, stack navigation):
├── SignalsScreen        → Sadece Pro+
├── BacktestScreen       → Sadece Pro+, basitleştirilmiş
├── MaliAnalizScreen     → Plan bazlı kapsam
├── PricingScreen        → Plan yükseltme
├── AdminScreen          → Sadece admin
└── LegalScreen          → Koşullar/Gizlilik
```

## 10.6 · Grafik (ChartScreen) — Teknik Detay

lightweight-charts web'de, Flutter'da yok. Alternatifler:

**Seçim: `fl_chart` (tavsiye edilir)**
- Mum grafiği: `fl_chart` doğrudan desteklemez → custom `CustomPainter` ile mum çiz
- En az: zaman ekseni, fiyat ekseni, zoom/pan (InteractiveViewer)
- İndikatör overlay: aynı CustomPainter'a çizgi olarak ekle

**Veri akışı:**
```dart
// ChartViewModel (Riverpod)
class ChartViewModel extends AsyncNotifier<ChartState> {
  late WsClient _ws;

  Future<void> loadSymbol(String symbol, String timeframe) async {
    // 1. REST → geçmiş barlar
    final bars = await _repo.getCandles(symbol, timeframe, limit: 500);
    state = AsyncData(ChartState(bars: bars, symbol: symbol));

    // 2. WS → canlı güncelleme
    _ws.connect(symbol);
    _ws.stream.listen((bar) => _appendBar(bar));
  }
}
```

## 10.7 · Feature Gate — Flutter

```dart
// shared/widgets/plan_gate_widget.dart
class PlanGateWidget extends StatelessWidget {
  final String requiredPlan;    // 'pro' | 'ultra'
  final Widget child;
  final String featureName;

  @override
  Widget build(BuildContext context) {
    final userPlan = ref.watch(authProvider).user?.plan ?? 'free';
    if (_hasAccess(userPlan, requiredPlan)) return child;

    return GestureDetector(
      onTap: () => context.go('/pricing'),
      child: Stack(children: [
        Opacity(opacity: 0.3, child: child),
        Center(child: Column(children: [
          const Icon(Icons.lock, size: 32),
          Text('$featureName için $requiredPlan planı gerekli'),
          ElevatedButton(
            onPressed: () => context.go('/pricing'),
            child: const Text('Planı Yükselt'),
          ),
        ])),
      ]),
    );
  }
}
```

## 10.8 · Push Bildirim (Firebase)

- `firebase_messaging` + `firebase_core`
- Backend'de: `backend/notifier/push_notifier.py` → Firebase Admin SDK
- Kullanım senaryoları:
  - Fiyat alarmı tetiklendiğinde
  - Backtest tamamlandığında
  - KAP özel durum açıklaması geldiğinde
  - Sinyal oluştuğunda (Pro+)

**Token kayıt endpoint'i (backend):**
```python
POST /api/mobile/push-token    # body: {fcm_token, device_name, platform}
```

## 10.9 · App Store / Play Store Hazırlık

```
Android:
├── Bundle ID: com.piyasapilot.app
├── minSdk: 23 (Android 6.0)
├── targetSdk: 34
└── Signing: keystore dosyası güvenli sakla (git'e ekleme)

iOS:
├── Bundle ID: com.piyasapilot.app
├── Min iOS: 15.0
├── Apple Developer Program: gerekli ($99/yıl)
└── Provisioning profile + signing certificate

İkon + Splash:
├── flutter_launcher_icons: ^0.13.0
├── flutter_native_splash: ^2.4.0
└── Tasarım: PiyasaPilot logosu, koyu arka plan, amber accent
```

## 10.10 · Web App Mobil Uyumluluk Değerlendirmesi

Mevcut web app **masaüstü-first** tasarlanmış. Mobil tarayıcıda açılırsa:

| Ekran | Mobil Uyumlu mu? | Not |
|-------|-----------------|-----|
| Landing page | ✅ Evet (Bootstrap) | Düzenlemeler gerekebilir |
| Login/Register | ✅ Evet | Basit form |
| Grafik | ⚠️ Kısmi | Pan/zoom touch problemli |
| Multi-chart (4'lü) | ❌ Hayır | Çok küçük |
| Backtest tablosu | ⚠️ Kısmi | Yatay scroll gerekir |
| Admin panel | ❌ Hayır | Masaüstü tasarımı |

**Sonuç:** Web app'e responsive CSS eklemek yüzeysel çözüm olur.
Native Flutter app → çok daha iyi kullanıcı deneyimi → **Flutter app tercih edilmeli.**

Web app'e minimum mobil düzeltmeleri (`frontend/style.css`):
```css
@media (max-width: 768px) {
  #sidebar { display: none; }         /* Mobilde sidebar gizle */
  #main-content { margin-left: 0; }
  .multi-chart-grid { grid-template-columns: 1fr; } /* Tek sütun */
  .financial-table { overflow-x: auto; display: block; }
}
```

---

# BÖLÜM 11 — ClickHouse + Veri Platformu Tamamlama

## 11.1 · `market_data_facade.py` → `main.py` Bağlantısı

**Dosya:** `backend/api/main.py` lifespan fonksiyonu

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # ... mevcut kodun içine ekle:
    from backend.data.repositories.market_data_facade import MarketDataFacade
    app.state.market_facade = MarketDataFacade(
        redis_url=getenv("REDIS_URL"),
        clickhouse_url=getenv("CLICKHOUSE_URL"),
        clickhouse_user=getenv("CLICKHOUSE_USER"),
        clickhouse_password=getenv("CLICKHOUSE_PASSWORD"),
    )
    yield
    # ... cleanup
```

`/api/v2/candles` handler'ında facade kullan:
```python
result = await request.app.state.market_facade.get_candles(symbol, interval, limit)
response.headers["X-Data-Source"] = result.source
```

## 11.2 · Veri Durumu Badge Frontend

```ts
// ChartPanel.ts
const source = response.headers.get("X-Data-Source") ?? "unknown";
const badge = {
  "redis": "🟢 Canlı",
  "clickhouse": "🟢 Canlı",
  "yfinance": "🟡 Gecikmeli",
  "cache-legacy": "🟡 Gecikmeli",
  "empty": "🔴 Veri Yok",
}[source] ?? "⚪ Bilinmiyor";
```

---

# BÖLÜM 12 — CI/CD ve Deployment

## 12.1 · `.github/workflows/ci.yml`

```yaml
name: CI
on:
  push: { branches: [main, develop, 'codex/*'] }
  pull_request: { branches: [main, develop] }

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt --break-system-packages
      - run: ruff check backend/ quant_engine/
      - run: python -m pytest -q

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: cd frontend && npm ci
      - run: cd frontend && npm run typecheck
      - run: cd frontend && npm run build

  docker:
    needs: [backend, frontend]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -f docker/Dockerfile.api -t piyasapilot-api:ci .
      - run: docker build -f docker/Dockerfile.frontend -t piyasapilot-frontend:ci .

  smoke:
    needs: docker
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose -f infra/docker-compose.yml up -d --wait
      - run: python scripts/check_deployment_readiness.py --base-url http://localhost:8000
      - if: always()
        run: docker compose -f infra/docker-compose.yml down -v
```

## 12.2 · Release Branch Stratejisi

```
main          → production, her merge'de v{major}.{minor}.{patch} tag
develop       → integration branch, tüm feature'lar buraya merge
feature/xxx   → tek özellik branch'i
fix/xxx       → hata düzeltme branch'i
codex/xxx     → AI oturum branch'leri (mevcut düzen)
```

Tag örneği: `git tag v1.0.0 && git push origin v1.0.0`

## 12.3 · `scripts/check_deployment_readiness.py` — Gerçek İmplementasyon

```python
#!/usr/bin/env python3
import sys, socket, ssl, subprocess, httpx, argparse

BASE_URL = "https://piyasapilotu.com"

CHECKS = [
    ("ENV_VARIABLES",    check_env_variables),
    ("DNS_RESOLUTION",   check_dns),
    ("TLS_CERTIFICATE",  check_tls),
    ("API_HEALTH",       check_api_health),
    ("METRICS",          check_metrics),
    ("WS_QUOTES",        check_ws_quotes),
    ("WS_SIGNALS",       check_ws_signals),
    ("AUTH_ENDPOINTS",   check_auth_smoke),
    ("DB_CONNECTIVITY",  check_db),
    ("MIGRATION_STATUS", check_migrations),
]

# Her check_xxx fonksiyonu (True, "açıklama") veya (False, "hata") döner
# Çıktı: PASS ✅ veya FAIL ❌

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=BASE_URL)
    args = parser.parse_args()
    results = [(name, fn(args.base_url)) for name, fn in CHECKS]
    failures = [n for n, (ok, _) in results if not ok]
    sys.exit(1 if failures else 0)
```

---

# BÖLÜM 13 — Error Tracking ve Monitoring

## 13.1 · Sentry

**Backend (`backend/api/main.py`):**
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
if dsn := getenv("SENTRY_DSN"):
    sentry_sdk.init(dsn=dsn, environment=getenv("APP_ENV", "development"),
                    integrations=[FastApiIntegration()],
                    traces_sample_rate=0.1, send_default_pii=False)
```

**Flutter:**
```dart
// pubspec.yaml
sentry_flutter: ^8.0.0

// main.dart
await SentryFlutter.init((options) {
  options.dsn = const String.fromEnvironment('SENTRY_DSN');
  options.environment = 'production';
  options.tracesSampleRate = 0.1;
}, appRunner: () => runApp(const MyApp()));
```

## 13.2 · Prometheus + Grafana (Mevcut Altyapı Üzerinde)

Mevcut `docker-compose.monitor.yml` var. Eklenecek metrikler:
- Aktif kullanıcı sayısı (per plan)
- Backtest/dakika throughput
- WS bağlantı sayısı
- Veri kaynağı hit/miss oranı
- Stripe webhook başarı/hata oranı

---

# BÖLÜM 14 — Kabul Testi Checklist

Bu kontroller tüm bölümler tamamlandıktan sonra çalıştırılır.

```
[ ] piyasapilotu.com HTTPS üzerinden açılıyor (TLS geçerli)
[ ] www.piyasapilotu.com → piyasapilotu.com'a yönleniyor (301)
[x] Misafir → landing page görüyor, terminale erişemiyor
[ ] Gmail ile kayıt → email doğrulama → onboarding → terminal
[ ] Email/şifre ile kayıt → aynı akış
[ ] Giriş yapılmış → /api/v2/candles 200, cookie Bearer ile
[ ] Giriş yapılmamış → /api/v2/candles 401
[ ] Free kullanıcı Backtest Pro özelliğine tıklar → upgrade modal
[ ] Free kullanıcı 5 backtest yapar → 6.'da 429 alıyor
[ ] Logout → cookie silindi, refresh token DB'de revoked
[ ] Pro ödeme → Stripe checkout → success → plan değişti
[x] Admin paneli → /admin sadece admin rolüyle açılıyor
[ ] Kullanıcı hesap sil → GDPR cascade temizliği
[ ] BIST hisse yükle → 🟡 Gecikmeli badge
[ ] Grafik timeframe değişiminde siyah ekran yok
[x] Koyu temada tablolar okunabilir
[x] /legal/terms açılıyor, risk uyarısı footer'da
[x] Cookie banner görünüyor
[ ] python -m pytest -q → tüm yeşil
[x] cd frontend && npm run typecheck → sıfır hata
[ ] python scripts/check_deployment_readiness.py → tüm PASS
[ ] Sentry'de test exception görünüyor
[ ] Flutter app → login → BTCUSDT grafiği yükleniyor
[ ] Flutter plan gate → Free kullanıcı Backtest ekranında kilit görüyor
```

---

# EK A — Yeni Python Paketleri

```bash
pip install argon2-cffi --break-system-packages       # Argon2 şifre hash
pip install python-jose[cryptography] --break-system-packages  # JWT
pip install httpx --break-system-packages              # Google OAuth HTTP
pip install stripe --break-system-packages             # Stripe ödeme
pip install sentry-sdk[fastapi] --break-system-packages # Hata takip
```

`requirements.txt`'e ekle.

---

# EK B — Bağımlılık Sırası

```
0. Domain DNS           → Sunucu IP hazır olduğunda
1. Marka tutarlılığı    → Hemen
2. MySQL migration 007  → Hemen (lokal geliştirme)
3. Auth backend         → 2 tamamlanınca
4. Auth frontend ekranları → 3 tamamlanınca
5. Stripe ödeme         → 3 tamamlanınca
6. Admin panel          → 3 tamamlanınca
7. i18n + hukuki        → 4 tamamlanınca
8. ClickHouse bağlantısı → Bağımsız (herhangi sırada)
9. UI hata düzeltmeleri → Bağımsız
10. CI/CD               → GitHub Actions: hemen kurulabilir
11. Flutter app         → 3 (backend mobil endpoint'leri) tamamlanınca
12. Sentry              → Deployment sırasında
13. Kabul testi         → Her şey bittikten sonra
```

---

# EK C — Flutter Geliştirme Kurulumu

```bash
# Flutter SDK kurulumu (flutter.dev/docs/get-started/install)
flutter create piyasapilot_mobile --org com.piyasapilot --platforms ios,android

cd piyasapilot_mobile

# pubspec.yaml'ı EK 10.3'teki paketlerle güncelle
flutter pub get

# Android emülatör / fiziksel cihaz
flutter run

# iOS (macOS gerekir)
cd ios && pod install && cd ..
flutter run -d iPhone

# Tip kontrolü
dart analyze

# Test
flutter test
```

**Geliştirme API URL:** `lib/core/network/api_client.dart`'ta:
```dart
const String baseUrl = String.fromEnvironment(
  'API_URL',
  defaultValue: 'http://10.0.2.2:8000',  // Android emülatör için localhost
);
// iOS simulator: 'http://localhost:8000'
// Gerçek cihaz: 'http://<bilgisayar_IP>:8000'
```

Production için: `flutter build apk --dart-define=API_URL=https://piyasapilotu.com`

---

---

# BÖLÜM 15 — AWS Deployment (eu-central-1 Frankfurt)

> AWS hesabı: enes (493309514356) · Bölge: Avrupa (Frankfurt) — eu-central-1
> Türkiye'ye yakınlık: ~25ms gecikme · TLS + Elastic IP + S3 yedek

## 15.0 · ÖNCE: Eski AWS Kaynaklarını Temizle

> Bu adım PiyasaPilot kurulumundan önce yapılmalı.
> Tahmini tasarruf: $40–60/ay (NAT Gateway, eski RDS, durmuş EC2'lar)
> Silme sırası önemli — bağımlılık hatası almamak için aşağıdaki sırayı takip et.

### 15.0.1 · Fatura Analizi — Neyin Para Yediğini Gör

```
AWS Console → Billing → Cost Explorer
  → Group by: Service
  → Son 30 gün
  → Hangi servis kaç dolar ödiyor? Not al.
```

Dikkat edilecekler:
- **NAT Gateway** → $32+/ay. Varsa hemen sil.
- **RDS/Aurora** → $15–60/ay (Aurora çok pahalı olabilir)
- **Durdurulmuş EC2** → EBS diski için hâlâ para ödenir
- **Bağlı olmayan Elastic IP** → $3.6/ay (küçük ama gereksiz)

### 15.0.2 · Silme Sırası (Bağımlılık Sırasıyla)

```
[ ] 1. App Runner → Services → her servisi seç → Actions → Delete
        URL: console.aws.amazon.com/apprunner/home?region=eu-central-1

[ ] 2. RDS / Aurora → Databases → eski DB seç → Actions → Delete
        "Create final snapshot?" → NO seç (eski proje, snapshot gereksiz)
        "I acknowledge..." → onayla → Delete
        URL: console.aws.amazon.com/rds/home?region=eu-central-1

[ ] 3. EC2 → Instances → eski instance'ları seç (running veya stopped)
        Actions → Instance State → Terminate
        NOT: "Stopped" instance EBS diski için para ödemeye devam eder!
        URL: console.aws.amazon.com/ec2/home?region=eu-central-1#Instances

[ ] 4. EC2 → Load Balancers → eski load balancer varsa → Delete
        (Application LB, Network LB, Classic LB hepsini kontrol et)

[ ] 5. VPC → NAT Gateways → eski NAT Gateway varsa → Actions → Delete
        ⚠ NAT Gateway = $32+/ay — mutlaka kontrol et!
        URL: console.aws.amazon.com/vpc/home?region=eu-central-1#NatGateways
        Silindikten sonra "Released" Elastic IP de varsa release et.

[ ] 6. EC2 → Elastic IPs → bağlı olmayan (unassociated) IP'leri seç
        Actions → Release Elastic IP addresses
        (PiyasaPilot için yeni bir tane allocate edeceğiz)

[ ] 7. EC2 → Security Groups → eski gruplara ait olanları sil
        (default grubu silme — silinemez zaten)

[ ] 8. S3 → eski proje bucket'larını bul → Empty → Delete
        (boşaltmadan silinemez)

[ ] 9. ECR → eski Docker image repository'leri varsa → Delete

[ ] 10. CloudWatch → Log Groups → eski uygulama loglarını sil
         (para almaz ama temiz olsun)
```

### 15.0.3 · Temizlik Sonrası Kontrol

```bash
# 1–2 gün bekle, Cost Explorer'da düşüş görünmeli
# Billing → Bills → Current month → sıfırlanıyor mu?

# Çalışan hiçbir şey kalmamalı:
EC2 → Instances    → hepsi "Terminated"
RDS → Databases    → boş
App Runner → Serv. → boş
VPC → NAT GW       → boş
EC2 → Elastic IPs  → boş (PiyasaPilot için yenisini alacağız)
```

### 15.0.4 · AWS Kredi Aktivitelerini de Tamamla ($80 ekstra kredi)

Temizlik sırasında şu aktiviteleri de yap:

```
[ ] "AWS Budgets kullanarak maliyet bütçesi oluştur" → $20 kredi
      Billing → Budgets → Create budget
      Tip: Cost budget → $80/ay limit → Email alert: enesaktas.ce@gmail.com

[ ] "EC2 kullanarak bir örnek başlatın" → $20 kredi
      → PiyasaPilot EC2 kurulumu (15.2) bunu otomatik tamamlar!

Toplam kazanılabilecek ek kredi: $40
Mevcut: $20 (Aurora aktivitesi tamamlandı)
Hedef: $60 toplam kredi → ~1 ay neredeyse bedava hosting
```

---

## 15.1 · Mimari Karar: Tek EC2 + Docker Compose

Başlangıç için en verimli mimari:

```
Internet
    │
    ▼
[Route 53 / METUnic DNS]
    │  A kaydı → Elastic IP
    ▼
[EC2 t3.large] — eu-central-1a
    │
    ├── nginx (80, 443) ← TLS / certbot
    ├── FastAPI API (8000, iç)
    ├── Workers (Binance WS, Yahoo, BIST)
    ├── Notifier (Telegram, email)
    ├── Frontend (Nginx static)
    ├── MySQL 8.0 (3306, iç)
    ├── ClickHouse 24.3 (8123, iç)
    └── Redis 7 (6379, iç)
         │
         ▼
    [S3 Bucket] — şifreli günlük yedek
```

**Neden RDS/ElastiCache DEĞİL (şimdilik):**
- RDS MySQL t3.micro: +$15/ay, ElastiCache t3.micro: +$13/ay → toplam +$28/ay
- Yönetim karmaşıklığı artar
- Mevcut Docker Compose setup zaten çalışıyor
- 1.000+ kullanıcıya kadar tek EC2 yeterli; o noktada RDS'e taşı

---

## 15.2 · EC2 Instance Kurulumu

### 15.2.1 · Instance Oluşturma (AWS Console)

```
AWS Console → EC2 → Launch Instance

İsim:           piyasapilot-prod
AMI:            Ubuntu Server 24.04 LTS (amd64)
Instance type:  t3.large  (2 vCPU, 8 GB RAM)
Key pair:       piyasapilot-key  → .pem dosyasını güvenli sakla
                (~/.ssh/piyasapilot-key.pem)

Storage:
  /dev/sda1    50 GB   gp3   3000 IOPS   (OS + uygulama)
  /dev/sdb    100 GB   gp3   3000 IOPS   (veri: MySQL, ClickHouse, Parquet)

Network:
  VPC:              default (veya yeni VPC)
  Subnet:           eu-central-1a
  Auto-assign IP:   Disable (Elastic IP kullanacağız)

Security Group:   piyasapilot-sg  (aşağıda detay)
```

### 15.2.2 · Elastic IP Bağla

```
EC2 → Elastic IPs → Allocate Elastic IP
  Network border group: eu-central-1
  
→ Actions → Associate
  Instance: piyasapilot-prod
  Private IP: (otomatik)
  
Not et: <ELASTIC_IP>   # METUnic DNS'e girilecek
```

### 15.2.3 · Security Group Kuralları

```
Gelen (Inbound) Kurallar:
────────────────────────────────────────────────────
Tür          Port    Kaynak          Açıklama
────────────────────────────────────────────────────
SSH          22      <Senin IP>/32   Sadece kendi IP'n
HTTP         80      0.0.0.0/0       Certbot + redirect
HTTPS        443     0.0.0.0/0       Ana trafik
────────────────────────────────────────────────────
UYARI: 8000, 3306, 8123, 6379 portları kapalı
       Bu portlar sadece iç container iletişimi için
       
Giden (Outbound):
  Tümü → 0.0.0.0/0  (dışarı çıkış serbest)
```

**SSH erişimini IP'ne kısıtla:**
```bash
# Kendi IP'ni öğren
curl -s https://checkip.amazonaws.com
# Security Group'ta SSH kaynağını: <IP>/32 yap
```

---

## 15.3 · Sunucu İlk Kurulum

SSH ile bağlan:
```bash
chmod 400 ~/.ssh/piyasapilot-key.pem
ssh -i ~/.ssh/piyasapilot-key.pem ubuntu@<ELASTIC_IP>
```

Sunucuda çalıştır:
```bash
# ─── Sistem güncelleme ────────────────────────────────
sudo apt update && sudo apt upgrade -y

# ─── Docker kurulumu ──────────────────────────────────
curl -fsSL https://get.docker.com | sudo bash
sudo usermod -aG docker ubuntu
newgrp docker   # veya yeni SSH oturumu aç

# ─── Docker Compose ───────────────────────────────────
sudo apt install -y docker-compose-plugin

# ─── Git ──────────────────────────────────────────────
sudo apt install -y git

# ─── Veri diski bağla ─────────────────────────────────
sudo mkfs -t xfs /dev/sdb
sudo mkdir -p /data
sudo mount /dev/sdb /data
# Kalıcı mount için fstab'a ekle:
echo "$(sudo blkid /dev/sdb | awk '{print $2}') /data xfs defaults 0 2" \
  | sudo tee -a /etc/fstab

# Veri klasörleri oluştur
sudo mkdir -p /data/mysql /data/clickhouse /data/redis \
              /data/app/cache /data/app/parquet /data/backups
sudo chown -R ubuntu:ubuntu /data

# ─── fail2ban (brute force koruması) ─────────────────
sudo apt install -y fail2ban
sudo systemctl enable fail2ban

# ─── UFW (ek güvenlik katmanı) ───────────────────────
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

---

## 15.4 · Repo Klonlama ve .env Hazırlama

```bash
# Sunucuda:
cd /home/ubuntu
git clone https://github.com/ENESAKT/piyasapilot.git app
# veya private repo ise:
# git clone git@github.com:ENESAKT/piyasapilot.git app

cd app

# .env.production oluştur
cp .env.example .env.production
nano .env.production   # Değerleri doldur (aşağıda liste)
```

**`.env.production`'da doldurulacak kritik değerler:**
```env
# Domain
PUBLIC_BASE_URL=https://piyasapilotu.com
COOKIE_DOMAIN=piyasapilotu.com
CORS_ORIGINS=https://piyasapilotu.com,https://www.piyasapilotu.com
APP_ENV=production

# JWT — openssl rand -base64 64 komutuyla üret
JWT_SECRET=<64_KARAKTER_RASTGELE>

# Google OAuth (console.cloud.google.com)
GOOGLE_CLIENT_ID=<...>.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=<...>
GOOGLE_REDIRECT_URI=https://piyasapilotu.com/api/auth/google/callback

# Stripe
STRIPE_SECRET_KEY=sk_live_<...>
STRIPE_WEBHOOK_SECRET=whsec_<...>

# Veritabanları (Docker iç network — localhost değil container adı)
MYSQL_URL=mysql+aiomysql://appuser:GUCLU_SIFRE@mysql:3306/metadata
DATABASE_URL=mysql+pymysql://appuser:GUCLU_SIFRE@mysql:3306/metadata
CLICKHOUSE_URL=http://default:GUCLU_SIFRE@clickhouse:8123/market_data
REDIS_URL=redis://redis:6379/0

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=enesaktas.ce@gmail.com
SMTP_PASS=<Gmail App Password>

# Sentry
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx

# STRICT mod — production'da zorunlu
STRICT_ENV_VALIDATION=1
```

---

## 15.5 · `docker/nginx.prod.conf` — Veri Dizini Override

Production'da MySQL, ClickHouse, Redis verisini `/data/` altına al.

**`infra/docker-compose.prod.yml`'deki volume path'lerini güncelle:**

```yaml
# mysql service volumes bölümünü şöyle değiştir:
volumes:
  - /data/mysql:/var/lib/mysql

# clickhouse:
volumes:
  - /data/clickhouse:/var/lib/clickhouse

# redis:
volumes:
  - /data/redis:/data

# api/workers (uygulama cache):
volumes:
  - /data/app/cache:/app/data/cache
  - /data/app/parquet:/app/data/bist
  - app_logs:/app/logs
```

---

## 15.6 · TLS Sertifikası — Certbot

```bash
# Sunucuda (docker compose başlatmadan önce):
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

# Geçici nginx durdur, standalone mod ile sertifika al
sudo certbot certonly --standalone \
  -d piyasapilotu.com \
  -d www.piyasapilotu.com \
  --email enesaktas.ce@gmail.com \
  --agree-tos --non-interactive

# Sertifika yolu:
# /etc/letsencrypt/live/piyasapilotu.com/fullchain.pem
# /etc/letsencrypt/live/piyasapilotu.com/privkey.pem

# docker-compose.prod.yml'deki certbot volume mount'u kontrol et:
# - /etc/letsencrypt:/etc/letsencrypt:ro

# Otomatik yenileme:
echo "0 3 1,15 * * root certbot renew --quiet && docker exec piyasapilot_nginx_prod nginx -s reload" \
  | sudo tee /etc/cron.d/certbot-renew
```

---

## 15.7 · Uygulamayı Başlat

```bash
cd /home/ubuntu/app

# Tüm servisleri build et ve başlat
docker compose -f infra/docker-compose.prod.yml build --no-cache
docker compose -f infra/docker-compose.prod.yml up -d

# Durum kontrolü
docker compose -f infra/docker-compose.prod.yml ps

# Log izle
docker compose -f infra/docker-compose.prod.yml logs -f api

# Migration çalıştır
docker compose -f infra/docker-compose.prod.yml exec api \
  python -c "from backend.data.repositories import run_migrations; run_migrations()"
```

**İlk başlatma sonrası smoke test:**
```bash
curl https://piyasapilotu.com/api/health
# → {"status": "ok", ...}

curl -o /dev/null -s -w "%{http_code}" https://piyasapilotu.com
# → 200
```

---

## 15.8 · METUnic DNS → Elastic IP

METUnic panelinde (DNS ve Alan Adı Yönetimi → Yönet):

```
Kayıt Türü    Host    Değer                TTL
──────────────────────────────────────────────
A             @       <ELASTIC_IP>         3600
A             www     <ELASTIC_IP>         3600
```

DNS yayılması 5–30 dakika sürer.
```bash
# Kontrol et:
dig piyasapilotu.com A +short
# → <ELASTIC_IP>
```

---

## 15.9 · S3 Yedek Bucket'ı

```bash
# AWS Console → S3 → Create Bucket
Bucket name:     piyasapilot-backups-prod
Region:          eu-central-1
Block all public access: ✅
Versioning:      Enable
Encryption:      SSE-S3 (AES-256)

# Lifecycle rule — 30 günden eski yedekleri sil:
Bucket → Management → Lifecycle → Add rule
  Rule name: delete-old-backups
  Prefix: (boş = tüm bucket)
  Transitions: Standard-IA after 7 days
  Expiration: Delete after 30 days
```

**IAM kullanıcısı (sadece S3 erişimi):**
```bash
# AWS Console → IAM → Users → Create user
Username: piyasapilot-backup-bot
Attach policy: AmazonS3FullAccess (sadece bu bucket için custom policy daha güvenli)

# Access key oluştur → .env.production'a ekle:
AWS_ACCESS_KEY_ID=<...>
AWS_SECRET_ACCESS_KEY=<...>
AWS_BACKUP_BUCKET=piyasapilot-backups-prod
AWS_REGION=eu-central-1
```

**Yedek scripti sunucuya koy:**
```bash
# Sunucuda:
pip install awscli --break-system-packages
aws configure --profile backup \
  --access-key <AWS_ACCESS_KEY_ID> \
  --secret-key <AWS_SECRET_ACCESS_KEY> \
  --region eu-central-1

# Günlük cron:
echo "0 3 * * * ubuntu /home/ubuntu/app/scripts/backup_offsite.sh >> /data/backups/backup.log 2>&1" \
  | sudo tee /etc/cron.d/piyasapilot-backup
```

---

## 15.10 · Maliyet Tahmini (Aylık)

```
Servis                    Fiyat (on-demand)   Fiyat (1yr reserved)
─────────────────────────────────────────────────────────────────
EC2 t3.large              ~$60/ay             ~$38/ay
EBS gp3 50GB (OS)         ~$4/ay              ~$4/ay
EBS gp3 100GB (veri)      ~$8/ay              ~$8/ay
Elastic IP (attached)      $0/ay               $0/ay
S3 (ilk 50GB + istekler)  ~$2/ay              ~$2/ay
Data transfer (out 10GB)  ~$1/ay              ~$1/ay
─────────────────────────────────────────────────────────────────
TOPLAM (on-demand)        ~$75/ay
TOPLAM (1yr reserved)     ~$53/ay
─────────────────────────────────────────────────────────────────
NOT: Mevcut faturanda $61 görüyorum — muhtemelen başka servisler
     çalışıyor. t3.large yerine t3.medium ($30/ay) ile başlayıp
     yük arttıkça t3.large'a geçebilirsin.
```

**Maliyet tasarrufu ipuçları:**
- EC2 için 1 yıllık reserved instance al → %35 indirim
- Spot instance KULLANMA — uygulama sürekli çalışmalı
- ClickHouse verimliyse RDS yerine EC2'de MySQL daha ucuz
- CloudWatch alarmı kur: $120/ay geçince email gönder

---

## 15.11 · CloudWatch Maliyet Alarmı

```bash
# AWS Console → CloudWatch → Alarms → Create Alarm
Metric: Billing → Total Estimated Charge → USD
Condition: Greater than $100
Notification: SNS → email → enesaktas.ce@gmail.com
```

---

## 15.12 · Güncelleme ve Deploy Süreci

```bash
# Yerel geliştirme:
git add -A && git commit -m "feat: yeni özellik"
git push origin main

# Sunucuda:
ssh -i ~/.ssh/piyasapilot-key.pem ubuntu@<ELASTIC_IP>
cd /home/ubuntu/app
git pull origin main

# Sadece API değiştiyse:
docker compose -f infra/docker-compose.prod.yml up -d --no-deps --build api

# Tüm stack yeniden build:
docker compose -f infra/docker-compose.prod.yml up -d --build

# Migration varsa:
docker compose -f infra/docker-compose.prod.yml exec api \
  python -c "from backend.data.repositories import run_migrations; run_migrations()"

# Sağlık kontrolü:
curl https://piyasapilotu.com/api/health
```

---

## 15.13 · Monitoring: CloudWatch + UptimeRobot

**UptimeRobot (ücretsiz plan — 5 dakikalık kontrol):**
```
Monitor type: HTTPS
URL: https://piyasapilotu.com/api/health
Interval: 5 minutes
Alert: email → enesaktas.ce@gmail.com
```
→ Site düştüğünde email + SMS alırsın.

**CloudWatch alarmları (AWS Console → CloudWatch):**
```
EC2 CPU > 80% for 10 minutes → Email
EC2 disk /data usage > 80%  → Email (custom metric gerekir)
```

---

## 15.14 · SSH Key Güvenliği

```bash
# Key'i güvenli sakla (buluta yükleme):
# Option 1: Mac Keychain
ssh-add --apple-use-keychain ~/.ssh/piyasapilot-key.pem

# Option 2: ~/.ssh/config ile kısayol
echo "
Host piyasapilot
  HostName <ELASTIC_IP>
  User ubuntu
  IdentityFile ~/.ssh/piyasapilot-key.pem
  ServerAliveInterval 60
" >> ~/.ssh/config

# Artık şöyle bağlanabilirsin:
ssh piyasapilot
```

---

## 15.15 · Tam Deployment Checklist

```
[ ] EC2 t3.large/t3.medium oluşturuldu (eu-central-1)
[ ] Elastic IP ayrıldı ve instance'a bağlandı
[ ] Security Group: sadece 22 (kendi IP), 80, 443 açık
[ ] Ubuntu kurulum scriptleri çalıştırıldı (Docker, fail2ban, UFW)
[ ] /dev/sdb → /data dizinine mount edildi
[ ] Repo klonlandı → /home/ubuntu/app
[ ] .env.production dolduruldu (tüm secret'lar)
[ ] docker-compose.prod.yml volume path'leri /data/ olarak güncellendi
[ ] Certbot çalıştırıldı → TLS sertifikası alındı
[ ] METUnic DNS'te A kaydı → Elastic IP girildi
[ ] DNS yayıldı (dig kontrolü)
[ ] docker compose up -d → tüm container'lar healthy
[ ] MySQL migration'lar çalıştırıldı
[ ] https://piyasapilotu.com/api/health → {"status":"ok"}
[ ] S3 backup bucket oluşturuldu
[ ] Backup cron kuruldu ve test edildi
[ ] CloudWatch maliyet alarmı ($100) kuruldu
[ ] UptimeRobot health check kuruldu
[ ] python scripts/check_deployment_readiness.py → tüm PASS
```

---

---

# BÖLÜM 16 — Eksik / Atlanan Teknik Maddeler

> Mevcut planın incelenmesinde tespit edilen boşluklar.
> Her biri uygulanmadan production'a geçilmemeli.

---

## 16.1 · Güvenlik Eksikleri

### 16.1.1 · Google OAuth CSRF Koruması (state parametresi) ✅ TAMAMLANDI

**Eksik:** `GET /api/auth/google` endpoint'i `state` parametresi üretmeli ve doğrulamalı.

```python
# google_oauth.py içine ekle
import secrets

async def get_google_auth_url(session_id: str) -> tuple[str, str]:
    state = secrets.token_urlsafe(32)
    # state'i Redis'e koy: key=f"oauth_state:{state}", TTL=600s
    await redis.set(f"oauth_state:{state}", session_id, ex=600)
    url = GOOGLE_AUTH_URL + f"&state={state}"
    return url, state

# callback'te:
async def verify_state(state: str) -> bool:
    exists = await redis.get(f"oauth_state:{state}")
    if not exists:
        return False
    await redis.delete(f"oauth_state:{state}")  # tek kullanım
    return True
```

**Kabul kriteri:** State olmadan gelen callback → 400 Bad Request.

**Durum:** `backend/auth/google_oauth.py` içinde Redis TTL'li state üretimi ve tek kullanımlık doğrulama mevcut; `auth_router.py` callback state doğrulaması yapıyor.

---

### 16.1.2 · Token Blacklist (Anlık Revoke) ✅ TAMAMLANDI

**Eksik:** Şu an refresh token sadece DB'de `revoked_at` ile işaretleniyor.
Access token 15 dakika boyunca hâlâ geçerli — admin bir kullanıcıyı banlayınca bile.

**Çözüm:** Redis'e `blocked_jti` set'i:
```python
# JWT payload'ına jti (JWT ID) ekle:
payload["jti"] = secrets.token_hex(16)

# decode_access_token'da kontrol:
jti = payload.get("jti")
if await redis.get(f"blocked_jti:{jti}"):
    raise JWTError("Token revoked")

# Revoke sırasında:
await redis.set(f"blocked_jti:{jti}", "1", ex=ACCESS_TOKEN_TTL)
```

Kullanım: admin ban, şifre değişikliği, şüpheli aktivite.

**Durum:** Access token payload'ına `jti` ekleniyor; `AuthRedisStore` blocked token kontrolü `get_current_user` içinde çalışıyor; logout/revoke akışları token engelleme kullanıyor.

---

### 16.1.3 · Şifre Gücü Doğrulama (Server-Side) ✅ TAMAMLANDI

**Eksik:** Şifre doğrulama sadece client-side (min 8 karakter).

```python
# backend/auth/password.py içine ekle
import re

def validate_password_strength(password: str) -> list[str]:
    errors = []
    if len(password) < 8:
        errors.append("En az 8 karakter olmalı")
    if not re.search(r"[A-Z]", password):
        errors.append("En az 1 büyük harf")
    if not re.search(r"\d", password):
        errors.append("En az 1 rakam")
    if password.lower() in COMMON_PASSWORDS:  # top 1000 liste
        errors.append("Bu şifre çok yaygın")
    return errors
```

**Durum:** `backend/auth/password.py` içinde policy mevcut; `POST /api/auth/register` artık server-side password strength kontrolü yapıyor.

---

### 16.1.4 · Admin için 2FA (TOTP) ✅ TAMAMLANDI

**Eksik:** Admin hesapları için iki adımlı doğrulama yok.

```python
# pip install pyotp --break-system-packages
import pyotp

# Migration 008: users tablosuna ekle:
# totp_secret VARCHAR(64), totp_enabled BOOLEAN DEFAULT FALSE

# Kurulum endpoint'i:
GET  /api/auth/2fa/setup     → QR code URL döner (Google Authenticator)
POST /api/auth/2fa/verify    → ilk kez doğrula + aktif et
POST /api/auth/2fa/disable   → deaktif et (şifre + TOTP gerekli)

# Login akışına ekle:
# 2FA aktifse → login 202 + {requires_2fa: true} döner
# Kullanıcı 6 haneyi girer → POST /api/auth/2fa/confirm → cookie set
```

**Kapsam:** Önce sadece `admin` rolü için zorunlu, diğerleri opsiyonel.

**Durum:** Migration 008 alanları, 2FA setup/verify/disable endpoint'leri ve login TOTP doğrulaması mevcut. Zorunlu admin enforcement canlı kullanıcı politikasına bağlanacaksa ayrı ürün/politika adımı olarak değerlendirilecek.

---

### 16.1.5 · Rate Limiting — Login Endpoint Brute Force ✅ TAMAMLANDI

**Eksik:** Login endpoint'inde hesap bazlı lockout yok.

```python
# Aynı email için 5 başarısız deneme → 30 dakika kilitle
# Redis: key=f"login_fail:{email}", TTL=1800s, INCR

@router.post("/login")
async def login(body: LoginRequest):
    fail_key = f"login_fail:{body.email}"
    fail_count = await redis.get(fail_key) or 0
    if int(fail_count) >= 5:
        raise HTTPException(429, detail={
            "tr": "Çok fazla başarısız deneme. 30 dakika bekleyin.",
            "en": "Too many failed attempts. Wait 30 minutes."
        })
    # ...
    if not verified:
        await redis.incr(fail_key)
        await redis.expire(fail_key, 1800)
        raise HTTPException(401, ...)
    await redis.delete(fail_key)  # başarılıda sıfırla
```

**Durum:** `POST /api/auth/login` Redis varsa email bazlı başarısız deneme sayacı tutuyor; 5 deneme sonrası 30 dakika 429 döndürüyor, başarılı girişte sayaç siliniyor.

---

### 16.1.6 · Content Security Policy — Nonce Tabanlı

**Eksik:** `nginx.prod.conf`'taki CSP `unsafe-inline` içeriyor.

```nginx
# Her istek için nonce üret (nginx + lua veya FastAPI middleware):
add_header Content-Security-Policy "
  default-src 'self';
  script-src 'self' 'nonce-$request_id' https://js.sentry-cdn.com;
  style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
  font-src 'self' https://fonts.gstatic.com;
  img-src 'self' data: https:;
  connect-src 'self' https://piyasapilotu.com wss://piyasapilotu.com
              https://*.sentry.io;
  frame-ancestors 'none';
" always;
```

---

## 16.2 · Backend Teknik Eksikler

### 16.2.1 · Veritabanı Connection Pooling

**Eksik:** `main.py`'de SQLAlchemy async engine pool ayarları yok.

```python
# backend/config.py veya main.py lifespan'e ekle
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine(
    getenv("MYSQL_URL"),
    pool_size=10,           # production'da 10 bağlantı
    max_overflow=20,        # anlık pik için +20
    pool_pre_ping=True,     # ölü bağlantıları temizle
    pool_recycle=3600,      # 1 saat sonra bağlantıyı yenile (MySQL timeout)
    echo=False,
)
AsyncSession = async_sessionmaker(engine, expire_on_commit=False)
```

---

### 16.2.2 · Stripe Webhook İdempotency

**Eksik:** Stripe aynı webhook'u birden fazla gönderebilir.

```python
# Migration 008: webhook_events tablosu ekle
CREATE TABLE IF NOT EXISTS webhook_events (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    provider    VARCHAR(50) NOT NULL DEFAULT 'stripe',
    event_id    VARCHAR(255) NOT NULL,
    event_type  VARCHAR(100) NOT NULL,
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_event_id (provider, event_id)
);

# Webhook handler'da:
async def handle_webhook(event_id: str, event_type: str, data: dict):
    try:
        await db.execute(
            "INSERT INTO webhook_events (event_id, event_type) VALUES (?, ?)",
            [event_id, event_type]
        )
    except IntegrityError:
        return  # zaten işlendi, atla
    # ... normal işlem
```

---

### 16.2.3 · Email HTML Şablonları

**Eksik:** `backend/auth/email_sender.py` düz metin gönderecek.
Profesyonel bir ürün HTML email şablonları gerektirir.

**Yeni dosya:** `backend/templates/email/`
```
backend/templates/email/
├── base.html              # header, footer, marka renkleri
├── verify_email.html      # "E-postanızı doğrulayın"
├── reset_password.html    # "Şifrenizi sıfırlayın"
├── welcome.html           # Kayıt sonrası hoş geldin
├── subscription_pro.html  # "Pro planına geçtiniz"
├── payment_failed.html    # "Ödemeniz başarısız"
└── quota_warning.html     # "Kotanızın %80'ini kullandınız"
```

**Python şablon motoru:** `jinja2` (FastAPI ile birlikte zaten geliyor).

```python
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader("backend/templates/email"))

def render_email(template_name: str, context: dict) -> str:
    return env.get_template(template_name).render(**context)
```

---

### 16.2.4 · Swagger / OpenAPI Dokümantasyonu (Ultra API Kullanıcıları)

**Eksik:** Ultra plan kullanıcıları API erişimi alıyor ama dokümantasyon yok.

```python
# main.py FastAPI init:
app = FastAPI(
    title="PiyasaPilot API",
    description="Gerçek zamanlı piyasa verisi, sinyal ve backtest API'si",
    version="1.0.0",
    docs_url="/api/docs",           # Swagger UI
    redoc_url="/api/redoc",         # ReDoc
    openapi_url="/api/openapi.json",
)
# Sadece Ultra+ erişebilir (nginx'te auth guard veya FastAPI middleware):
# GET /api/docs → require_ultra
```

**API Key Yönetimi** (Ultra kullanıcıları için):
```
GET  /api/auth/api-keys          → liste
POST /api/auth/api-keys          → yeni key oluştur (isim + TTL)
DELETE /api/auth/api-keys/{id}   → sil

Migration 008:
CREATE TABLE api_keys (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id    BIGINT NOT NULL,
    name       VARCHAR(100),
    key_hash   VARCHAR(255) NOT NULL,
    last_used  DATETIME,
    expires_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

---

### 16.2.5 · Flutter Deep Link (Email Doğrulama Mobilde)

**Eksik:** Kullanıcı maildeki linke mobil cihazdan tıklarsa web açılır, uygulama değil.

**Çözüm:**
- Email doğrulama URL'i: `https://piyasapilotu.com/verify?token=xxx`
- Bu URL hem web hem mobil için çalışmalı
- Flutter'da `app_links: ^6.0.0` paketi ile deep link yakala
- Android: `AndroidManifest.xml`'e intent filter ekle
- iOS: `apple-app-site-association` dosyası (AASA) → `piyasapilotu.com/.well-known/apple-app-site-association`

```json
// /.well-known/apple-app-site-association
{
  "applinks": {
    "apps": [],
    "details": [{
      "appID": "TEAM_ID.com.piyasapilot.app",
      "paths": ["/verify", "/reset-password", "/invite/*"]
    }]
  }
}
```

---

### 16.2.6 · VIOP Veri Modeli (Önceki Plandan Taşındı)

**Eksik:** Bölüm 15'te AWS planı var ama eski plandaki VIOP maddesi yeni plana taşınmadı.

```
infra/clickhouse/init/003_viop_contracts.sql  (yeni dosya)

CREATE TABLE IF NOT EXISTS viop_bars (
    symbol         String,
    contract_type  String,   -- F_XU030, F_USDTRY vb.
    maturity       Date,
    interval       String,
    ts             DateTime64(3, 'UTC'),
    open           Float64,
    high           Float64,
    low            Float64,
    close          Float64,
    volume         Float64,
    open_interest  Float64,
    source         String,
    is_real        Bool,
    _ingested_at   DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY (toYYYYMM(ts), contract_type)
ORDER BY (symbol, interval, ts)
TTL ts + INTERVAL 10 YEAR;
```

Rollover mantığı: yakın vadeden uzak vadeye geçiş `viop_contracts` tablosundan okunacak.

---

### 16.2.7 · Load Testing (Yük Testi)

**Eksik:** Production'a çıkmadan önce EC2 t3.large kaç eş zamanlı kullanıcıyı kaldırır bilinmiyor.

**Araç:** `k6` (JavaScript tabanlı, ücretsiz)

```bash
# scripts/load_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 50 },   // 50 kullanıcıya çık
    { duration: '1m',  target: 100 },  // 100 kullanıcıda tut
    { duration: '30s', target: 0 },    // kademeli düşür
  ],
  thresholds: {
    http_req_duration: ['p95<500'],    // %95'i 500ms altında
    http_req_failed:   ['rate<0.01'],  // %1'den az hata
  },
};

export default function () {
  const r = http.get('https://piyasapilotu.com/api/health');
  check(r, { 'status 200': (res) => res.status === 200 });
  sleep(1);
}

# Çalıştır:
k6 run scripts/load_test.js
```

**Hedef:** 100 eş zamanlı kullanıcı → p95 < 500ms, hata oranı < %1.

---

### 16.2.8 · CDN (Static Asset Hızlandırma)

**Eksik:** Frontend JS/CSS/font'lar doğrudan EC2'den servis ediliyor.

**Çözüm:** Cloudflare (ücretsiz plan yeterli):

```
1. cloudflare.com → hesap aç
2. piyasapilotu.com domainini ekle
3. METUnic'teki nameserver'ları Cloudflare'e yönelt
4. Cloudflare otomatik:
   - Static asset cache (JS, CSS, font, img)
   - DDoS koruması
   - SSL/TLS (Let's Encrypt yerine CF sertifikası)
   - Bot koruması

Cloudflare Rules:
- /api/* → cache yok (bypass)
- /ws/*  → WebSocket proxy (Enterprise gerekebilir — önce EC2 direkt dene)
- /      → 1 saatlik cache
```

**Maliyet:** Cloudflare free → $0. EC2 data transfer maliyeti düşer.

---

### 16.2.9 · Database Migration Sistemi

**Eksik:** Migration dosyaları var ama otomatik çalıştırma mekanizması yok.

```python
# scripts/run_migrations.py
import os, glob
import mysql.connector

conn = mysql.connector.connect(...)
cursor = conn.cursor()

# Hangi migration'lar uygulandı?
cursor.execute("""
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version VARCHAR(255) PRIMARY KEY,
        applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

files = sorted(glob.glob("infra/mysql/migrations/*.sql"))
for f in files:
    version = os.path.basename(f)
    cursor.execute("SELECT version FROM schema_migrations WHERE version=%s", [version])
    if cursor.fetchone():
        continue  # zaten uygulandı
    with open(f) as fp:
        cursor.execute(fp.read(), multi=True)
    cursor.execute("INSERT INTO schema_migrations (version) VALUES (%s)", [version])
    conn.commit()
    print(f"✅ {version}")
```

CI/CD pipeline'ına ve Docker startup'a ekle.

---

### 16.2.10 · Redis Session Store (Yatay Ölçekleme Hazırlığı)

**Şu an:** Access token cookie'de, refresh token MySQL'de.
**Sorun:** İleride 2. bir EC2 eklenirse her sunucu token'ı bağımsız doğrular → OK (stateless JWT).
**Ama:** Login sayacı, rate limit, OAuth state, TOTP kodu → Redis'te tutulmalı, in-memory değil.

```python
# backend/auth/redis_store.py (yeni dosya)
class AuthRedisStore:
    def __init__(self, redis_client):
        self.r = redis_client

    async def set_oauth_state(self, state: str, data: str, ttl=600):
        await self.r.set(f"oauth:{state}", data, ex=ttl)

    async def get_oauth_state(self, state: str) -> str | None:
        val = await self.r.get(f"oauth:{state}")
        await self.r.delete(f"oauth:{state}")
        return val

    async def block_token(self, jti: str, ttl: int):
        await self.r.set(f"blocked:{jti}", "1", ex=ttl)

    async def is_token_blocked(self, jti: str) -> bool:
        return await self.r.exists(f"blocked:{jti}") > 0

    async def incr_login_fail(self, email: str) -> int:
        key = f"loginfail:{email}"
        count = await self.r.incr(key)
        await self.r.expire(key, 1800)
        return count
```

---

## 16.3 · Frontend Eksikleri

### 16.3.1 · Web Analytics (Kullanıcı Davranışı)

**Eksik:** Kaç kullanıcı hangi özelliği kullanıyor? Conversion rate nedir? Bilinmiyor.

**Araç:** Plausible Analytics (GDPR uyumlu, cookie gerekmez, $9/ay) veya Umami (self-hosted, ücretsiz).

```html
<!-- index.html — sadece consent sonrası yükle -->
<script defer data-domain="piyasapilotu.com"
  src="https://plausible.io/js/script.js"></script>
```

**İzlenecek özel olaylar:**
```ts
// frontend/src/core/Analytics.ts
export const analytics = {
  track(event: string, props?: Record<string, string | number>) {
    if (typeof window.plausible === 'function') {
      window.plausible(event, { props });
    }
  }
};

// Kullanım örnekleri:
analytics.track('backtest_run', { plan: 'free', symbol: 'THYAO' });
analytics.track('upgrade_modal_shown', { from: 'backtest_pro' });
analytics.track('upgrade_clicked', { plan: 'pro' });
analytics.track('signup_completed', { method: 'google' });
```

---

### 16.3.2 · Error Boundary (Unhandled TS Exception)

**Eksik:** Herhangi bir bileşen crash ederse tüm terminal çöküyor, kullanıcı boş ekran görüyor.

```ts
// frontend/src/core/ErrorBoundary.ts
window.addEventListener('error', (e) => {
  console.error('Unhandled error:', e.error);
  // Sentry'ye gönder
  if (typeof Sentry !== 'undefined') Sentry.captureException(e.error);
  // Kullanıcıya göster
  document.getElementById('app-error-banner')?.classList.remove('hidden');
});

window.addEventListener('unhandledrejection', (e) => {
  console.error('Unhandled promise:', e.reason);
  if (typeof Sentry !== 'undefined') Sentry.captureException(e.reason);
});
```

```html
<!-- index.html'e ekle -->
<div id="app-error-banner" class="hidden app-error">
  Beklenmedik bir hata oluştu. Sayfayı yenileyiniz.
  <button onclick="location.reload()">Yenile</button>
</div>
```

---

### 16.3.3 · Skeleton Loading (Tüm Panellerde)

**Eksik:** Veriler yüklenirken paneller boş görünüyor veya spinner tek tip.

Her panel için CSS skeleton:
```css
.skeleton {
  background: linear-gradient(90deg, #1e293b 25%, #334155 50%, #1e293b 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

/* Kullanım */
.skeleton-row { height: 16px; margin: 8px 0; }
.skeleton-chart { height: 300px; }
```

---

### 16.3.4 · Offline / PWA Desteği (Opsiyonel ama Değerli)

```ts
// vite.config.ts — vite-plugin-pwa ile
import { VitePWA } from 'vite-plugin-pwa';

VitePWA({
  registerType: 'autoUpdate',
  manifest: {
    name: 'PiyasaPilot',
    short_name: 'PiyasaPilot',
    theme_color: '#0f172a',
    icons: [{ src: '/icon-192.png', sizes: '192x192', type: 'image/png' }],
  },
  workbox: {
    // API isteklerini cache'leme — sadece statik asset'ler
    globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
  },
})
```

Faydası: Kullanıcı "Ana Ekrana Ekle" yapabilir, offline'da son veriyi görebilir.

---

## 16.4 · DevOps Eksikleri

### 16.4.1 · Automated Backup Test (Restore Drill)

**Eksik:** `scripts/backup_offsite.sh` var ama yedeğin restore edilip edilmediği test edilmiyor.

```bash
# scripts/restore_drill.sh (yeni dosya)
# Her ay 1. Pazar çalıştır (cron)
# 1. S3'ten son yedeği indir
# 2. Yeni bir Docker container'da MySQL restore et
# 3. Tablo sayısını kontrol et
# 4. Başarı/hata → email gönder

set -euo pipefail
BACKUP=$(aws s3 ls s3://piyasapilot-backups-prod/ | sort | tail -1 | awk '{print $4}')
aws s3 cp "s3://piyasapilot-backups-prod/$BACKUP" /tmp/restore_test.tar.gz.gpg
gpg --decrypt --passphrase "$BACKUP_GPG_PASSPHRASE" /tmp/restore_test.tar.gz.gpg \
  | tar -xzf - -C /tmp/restore_test/
# MySQL restore kontrol...
echo "✅ Restore drill başarılı: $BACKUP"
```

---

### 16.4.2 · Docker Image Güvenlik Taraması

**Eksik:** CI'da Docker image'ların güvenlik açığı taranmıyor.

```yaml
# .github/workflows/ci.yml'a ekle:
- name: Scan Docker image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: piyasapilot-api:ci
    format: table
    exit-code: 1
    severity: CRITICAL,HIGH
```

---

### 16.4.3 · Log Rotation

**Eksik:** `/app/logs` dolabilir, sunucu disk dolar.

```yaml
# docker-compose.prod.yml'daki her servise ekle:
logging:
  driver: json-file
  options:
    max-size: "50m"
    max-file: "5"
```

---

### 16.4.4 · Healthcheck — Her Container İçin

**Eksik:** `docker-compose.prod.yml`'da container healthcheck yok.

```yaml
# API:
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s

# MySQL:
healthcheck:
  test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
  interval: 10s
  timeout: 5s
  retries: 5

# Redis:
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 10s
  timeout: 3s
  retries: 3

# ClickHouse:
healthcheck:
  test: ["CMD", "wget", "--no-verbose", "--tries=1",
         "--spider", "http://localhost:8123/ping"]
  interval: 30s
  timeout: 10s
  retries: 3
```

---

### 16.4.5 · Status Page (piyasapilotu.com/status)

**Eksik:** Sistem çöktüğünde kullanıcıların nereye bakacağı yok.

**Araç:** Statuspage.io (ücretsiz tier) veya UptimeRobot'un public status sayfası.

```
UptimeRobot → Status Pages → Create
  Name: PiyasaPilot Status
  URL: status.piyasapilotu.com
  
Monitörler ekle:
  - API Health (/api/health)
  - WebSocket Quotes (/ws/quotes)
  - Frontend (/)

DNS: status CNAME → stats.uptimerobot.com
```

---

---

# BÖLÜM 17 — Proje Büyütme Yol Haritası

> Teknik altyapı hazır olduğunda sıradaki adım: kullanıcı kazanmak ve gelir büyütmek.
> Bu bölüm 3 faza ayrılmış: Lansman → Büyüme → Ölçekleme.

---

## FAZA 0 — Lansman Öncesi (ilk kullanıcılar gelmeden)

### 17.0.1 · Waitlist Sayfası

**Neden:** Lansman öncesi email listesi oluşturmak, erken kullanıcıları tanımlamak.

**Dosya:** `frontend/src/pages/WaitlistPage.ts`

```
┌──────────────────────────────────────────┐
│  PiyasaPilot — Çok Yakında 🚀            │
│                                          │
│  BIST'in en gelişmiş algoritmik          │
│  trading terminali geliyor.              │
│                                          │
│  [ E-posta adresiniz        ]            │
│  [ Erken Erişim İstiyorum   ]            │
│                                          │
│  İlk 100 üyeye 3 ay ücretsiz Pro.       │
│                                          │
│  Şimdiye kadar 47 kişi kaydoldu.        │
└──────────────────────────────────────────┘
```

**Backend:** `POST /api/waitlist` → MySQL `waitlist` tablosu → welcome email.

---

### 17.0.2 · Referral (Davet) Sistemi

**Nasıl çalışır:**
- Her kullanıcı kayıt olunca `referral_code` üretilir (6 harf, örn. `ENES42`)
- `piyasapilotu.com/r/ENES42` linki paylaşılır
- Yeni kullanıcı bu linkten gelirse → davet eden 1 ay Pro, davet edilen 14 gün Pro deneme

```sql
-- Migration 008:
ALTER TABLE users ADD COLUMN referral_code VARCHAR(20) UNIQUE;
ALTER TABLE users ADD COLUMN referred_by BIGINT REFERENCES users(id);

CREATE TABLE referral_rewards (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    referrer_id BIGINT NOT NULL,
    referred_id BIGINT NOT NULL,
    reward_type VARCHAR(50),       -- 'pro_1month'
    granted_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Hedef:** Viral büyüme. Her kullanıcı ortalama 2 kişi davet ederse → exponential büyüme.

---

### 17.0.3 · 14 Gün Ücretsiz Pro Deneme

**Şu an:** Free plan direkt başlıyor.

**Yapılacak:** Kayıt olunca ilk 14 gün otomatik Pro:
```python
# register endpoint'te:
trial_end = datetime.now() + timedelta(days=14)
await db.insert("user_subscriptions", {
    "user_id": user.id,
    "plan_id": PRO_PLAN_ID,
    "status": "trialing",
    "trial_ends_at": trial_end,
    "current_period_end": trial_end,
})
```

Deneme biterken 3 gün önce email: "Pro planın 3 gün sonra sona eriyor →".

---

### 17.0.4 · Sosyal Paylaşım — Backtest Sonuçları

**Neden:** Kullanıcılar iyi backtest sonuçlarını paylaşırsa organik büyüme.

**Yapılacak:**
```ts
// StrategyPanel.ts'e ekle
async function shareBacktest(result: BacktestResult): Promise<void> {
  const shareUrl = await fetch('/api/backtest/share', {
    method: 'POST',
    body: JSON.stringify({ backtest_id: result.id, is_public: true })
  });
  // → https://piyasapilotu.com/shared/abc123

  // Web Share API (mobil):
  if (navigator.share) {
    navigator.share({
      title: `${result.symbol} — ${result.total_return}% getiri`,
      url: shareUrl,
    });
  } else {
    // Twitter/X linki kopyala
    navigator.clipboard.writeText(
      `https://twitter.com/intent/tweet?text=...&url=${shareUrl}`
    );
  }
}
```

**Public backtest sayfası:** `piyasapilotu.com/shared/abc123` → giriş gerektirmez, misafir görebilir.

---

## FAZA 1 — İlk Büyüme (0 → 1.000 kullanıcı)

### 17.1.1 · SEO — Landing Page + Blog

**Neden:** Türkiye'de "BIST backtest", "algoritmik trading Türkiye", "borsa sinyal" aramaları var.

**Yapılacak:**

```
Landing page SEO:
  - Title: "PiyasaPilot — BIST Algoritmik Trading Terminali"
  - Meta description: "BIST hisseleri için backtest, sinyal ve portföy yönetimi."
  - Yapısal veri (Schema.org SoftwareApplication)
  - Sitemap: /sitemap.xml
  - robots.txt

Blog (statik, SSG veya Markdown):
  - "BIST'te Algoritmik Trading Nasıl Yapılır?"
  - "Walk-Forward Analysis Nedir?"
  - "RSI ile BIST Stratejisi"
  - "Backtest Nasıl Yorumlanır?"
  → Her makale landing page'e link verir
  → Organik trafik → kayıt
```

**Araç:** Blog için Astro veya Next.js (ayrı domain: `blog.piyasapilotu.com`) veya Ghost.

---

### 17.1.2 · Telegram Kanal ve Bot

**Neden:** Türk trader topluluğu Telegram'da yoğun.

**Yapılacak:**
- `@PiyasaPilot` Telegram kanalı → günlük piyasa özeti
- Mevcut `backend/notifier/` Telegram botu kanalı da besleyecek
- Kanal açıklamasında: "Ücretsiz kayıt: piyasapilotu.com"
- Haftalık: en iyi backtestin otomatik paylaşımı

**İçerik:** PiyasaPilot'un kendi SignalGenerator'ından üretilen sinyaller → her gün kanalda yayın.

---

### 17.1.3 · Customer Support — Crisp Chat

**Eksik:** Kullanıcı sorunla karşılaştığında nereye yazacağını bilmiyor.

```html
<!-- index.html — sadece giriş yapılmış kullanıcılara göster -->
<script>
  window.$crisp = [];
  window.CRISP_WEBSITE_ID = "CRISP_ID";
  (function(){ var d=document; var s=d.createElement("script");
    s.src="https://client.crisp.chat/l.js"; s.async=1;
    d.getElementsByTagName("head")[0].appendChild(s); })();

  // Kullanıcı bilgisini otomatik doldur:
  $crisp.push(["set", "user:email", [currentUser.email]]);
  $crisp.push(["set", "user:nickname", [currentUser.displayName]]);
  $crisp.push(["set", "session:data", [[["plan", currentUser.plan]]]]);
</script>
```

**Maliyet:** Crisp ücretsiz plan (2 ajan, sınırsız konuşma).

---

### 17.1.4 · Onboarding Email Serisi (Drip Campaign)

**Araç:** Postmark veya Resend (SMTP yerine API tabanlı, daha güvenilir)

**Seri:**
```
Gün 0:  Hoş geldin + email doğrulama
Gün 1:  "İlk backtest'ini çalıştır" → terminal'e git butonu
Gün 3:  "14 günlük Pro denemin nasıl gidiyor?" → özellikler tanıt
Gün 7:  "Kullanıcılar ne diyor?" → sosyal kanıt
Gün 12: "2 gün kaldı — Pro'ya geç" → FOMO + indirim kodu
Gün 14: "Denemen sona erdi" → upgrade veya free'de kal seçimi
```

**Backend:** `backend/notifier/drip_campaign.py` (yeni dosya) → cron ile kontrol.

---

### 17.1.5 · Leaderboard (Strateji Yarışması)

**Neden:** Kullanıcıları aktif tutar, viral büyüme sağlar.

**Nasıl:**
- Kullanıcılar backtestlerini "public" yapabilir
- `/leaderboard` sayfasında: en yüksek Sharpe, en yüksek getiri, en düşük drawdown
- Aylık en iyi 3 strateji → 1 ay ücretsiz Pro

```sql
-- backtest_results tablosuna ekle:
ALTER TABLE backtest_results
  ADD COLUMN is_public BOOLEAN DEFAULT FALSE,
  ADD COLUMN public_slug VARCHAR(50) UNIQUE;
```

---

## FAZA 2 — Hızlandırma (1.000 → 10.000 kullanıcı)

### 17.2.1 · Affiliate / Partner Programı

**Nasıl:**
- Finans blog yazarları, YouTube kanalları, Telegram grup adminleri
- Affiliate link: `piyasapilotu.com?ref=PARTNER_CODE`
- Her Pro dönüşümde %20 komisyon (ilk 3 ay)

```sql
-- Migration 009:
CREATE TABLE affiliates (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id      BIGINT REFERENCES users(id),
    code         VARCHAR(50) UNIQUE,
    commission_rate DECIMAL(5,2) DEFAULT 20.00,
    total_earnings DECIMAL(10,2) DEFAULT 0,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Hedef:** 10 aktif affiliate → aylık 100 yeni Pro kullanıcı.

---

### 17.2.2 · BIST Lisanslı Veri Sağlayıcısı Anlaşması

**Neden:** Ultra plan "gerçek zamanlı lisanslı veri" vaat ediyor ama mevcut provider yfinance (gecikmeli).

**Potansiyel Sağlayıcılar (Türkiye):**
- **Matriks** (Finansinvest altyapısı) — API lisansı için iletişime geç
- **Foreks** (foreks.com) — data API programı
- **Rithmic** — VİOP için
- **Borsa Istanbul API** — resmi kanal

**Adımlar:**
1. Her sağlayıcıya mail at: "API lisansı almak istiyoruz, fiyat teklifi"
2. Test ortamı al → `backend/data/providers/licensed_provider.py`
3. `ProviderRouter`'a en yüksek önceliğe ekle

**Not:** Bu anlaşmalar olmadan Ultra plan "gerçek zamanlı" veri veremez.
Ultra planı "gerçek zamanlı" yerine "öncelikli erişim" veya "hızlandırılmış veri" olarak etiketle
— şeffaf ol, gerçek olmayan şey vaat etme.

---

### 17.2.3 · API Marketplace (Ultra Kullanıcıları)

**Neden:** Ultra kullanıcılar kendi uygulamalarına PiyasaPilot verisini çekmek isteyebilir.

**Yapılacak:**
- Swagger/OpenAPI dokümantasyonu (16.2.4'te planlandı)
- API Key yönetimi (16.2.4'te planlandı)
- Rate limit dashboard: "Bu ay X API çağrısı yaptın"
- Webhook desteği: "Sinyal oluşunca benim URL'ime POST at"

```
GET  /api/v1/candles?symbol=THYAO&interval=1h&limit=500
GET  /api/v1/signals?symbol=THYAO
GET  /api/v1/financials/{symbol}/ratios
POST /api/v1/webhooks              → webhook URL kayıt
```

---

### 17.2.4 · Discord Topluluğu

**Neden:** Aktif kullanıcı topluluğu → organik büyüme + ürün geri bildirimi.

**Kanallar:**
```
#genel-sohbet
#bist-sinyaller    ← bot otomatik paylaşır
#backtest-galeri   ← kullanıcılar paylaşır
#strateji-tarti   ← fikir alışverişi
#hata-bildirimi   ← destek
#duyurular        ← sadece admin
```

**Bot:** Discord webhook → PiyasaPilot sinyal sistemi → #bist-sinyaller kanalına otomatik post.

---

### 17.2.5 · Changelog ve "Yenilikler" Sayfası

**Neden:** Kullanıcılar neyin değiştiğini görmek ister; aktivasyon ve retention artırır.

**Araç:** `piyasapilotu.com/changelog` veya Headway (embed widget).

```
Mayıs 2026 — v1.2.0
  ✨ Backtest Pro — Monte Carlo simülasyonu eklendi
  ✨ KAP haberleri artık gerçek zamanlı
  🐛 Grafik timeframe değişiminde siyah ekran düzeltildi
  🐛 Koyu tema kontrast sorunu giderildi
```

---

### 17.2.6 · Product Hunt Lansmanı

**Strateji:** Ürün hazır olunca Product Hunt'ta lansman → global tanınırlık.

**Adımlar:**
1. `producthunt.com` → "Ship" ile ürünü kayıt et
2. Lansman günü için 50+ "upvote" taahhüdü topla (mevcut kullanıcılardan)
3. GIF/video demo hazırla (60 saniye)
4. İngilizce açıklama: "Algorithmic trading terminal for BIST & global markets"
5. Lansman günü: Salı-Perşembe, UTC 00:01'de yayınla

**Hedef:** Top 5 of the Day → +500 yeni kayıt.

---

## FAZA 3 — Ölçekleme (10.000+ kullanıcı)

### 17.3.1 · Altyapı Ölçekleme (EC2 → Load Balanced)

```
Mevcut (tek EC2):          Ölçeklenmiş:
──────────────────         ─────────────────────────────
EC2 t3.large               ALB (Application Load Balancer)
  └── Docker Compose         ├── EC2 #1 (API + Workers)
                             ├── EC2 #2 (API + Workers)
                             └── EC2 #3 (API)
                           RDS MySQL Multi-AZ
                           ElastiCache Redis Cluster
                           ClickHouse (ayrı EC2, r6i.large)
                           S3 + CloudFront (frontend CDN)
```

**Tetikleyici:** EC2 CPU > %70 kalıcı → yatay scale zamanı.

---

### 17.3.2 · Kurumsal (Enterprise) Plan

**Hedef kitle:** Aracı kurumlar, portföy yönetim şirketleri, hedge fonlar.

**Özellikler:**
- White-label seçeneği (markalamayı kaldır, kendi logon)
- SSO (SAML/LDAP entegrasyonu)
- SLA garantisi (%99.9 uptime)
- Dedicated instance (ayrı EC2, izole ortam)
- Custom API limitleri
- Faturalama: aylık fatura, banka transferi

**Fiyat:** Müzakereyle, $500+/ay.

---

### 17.3.3 · LightGBM Sinyal Sınıflandırması

**Koşul:** `scripts/ml_readiness.py` → en az 3 ay 1m OHLCV verisi mevcut olmalı.

```python
# Hazırlık kontrol:
python scripts/ml_readiness.py
# → ✅ 3 ay BIST 30 veri mevcut — LightGBM eğitimi başlatılabilir
# → ❌ Yetersiz veri (2 ay) — Ocak 2027'ye kadar bekle

# Eğitim:
python scripts/retrain_lightgbm.py \
  --symbols THYAO AKBNK GARAN SISE \
  --timeframe 15m \
  --lookback 90d
```

**Sinyal değeri:** LightGBM sinyalleri mevcut kural tabanlı sinyallerden üstün olursa
Ultra planının "AI destekli sinyal" özelliği olarak sunulur.

---

### 17.3.4 · Flutter App — Gelişmiş Özellikler (v2)

Temel Flutter app hazır olduktan sonra:

```
v2 özellikleri:
  [ ] Widget (Home Screen) → watchlist fiyatları
  [ ] Apple Watch / Wear OS → fiyat alarmı
  [ ] Biometrik kimlik doğrulama (FaceID, fingerprint)
  [ ] Offline mod → son 100 bar cache'den göster
  [ ] iPad / tablet optimizasyonu (multi-column layout)
  [ ] AR grafik (deneysel — kamera üzerinde fiyat overlay)
```

---

## 17.4 · Büyüme Metrikleri — KPI Hedefleri

```
Ay 1 (Lansman):
  Hedef: 200 kayıt, 10 Pro kullanıcı
  Metrik: Kayıt → onboarding tamamlama oranı > %60
  
Ay 3:
  Hedef: 1.000 kayıt, 50 Pro kullanıcı, $999 MRR
  Metrik: 7-gün retention > %30
  
Ay 6:
  Hedef: 3.000 kayıt, 150 Pro, 20 Ultra → $3.998 MRR
  Metrik: NPS > 40

Ay 12:
  Hedef: 10.000 kayıt, 400 Pro, 60 Ultra → $11.956 MRR
  Metrik: Churn < %5/ay
```

---

## 17.5 · "Fark Yaratan" Özellikler (Rakiplerden Ayrışma)

Matriks, TradingView ve Finnet'ten farkımız:

```
1. Backtest + Canlı Sinyal + Paper Trading → TEK EKRANDA
   TradingView: sadece grafik
   Matriks: gerçek emir, backtest yok
   PiyasaPilot: ikisinin arası → tam algoritmik workflow

2. Şeffaf Veri Durumu
   Her bar: kaynak + gecikme + kalite badge
   Kullanıcı hiç kandırılmıyor

3. Açık Eğitim İçeriği
   57 makale → backtest ile doğrudan bağlantı
   "Oku, hemen dene" → öğrenme → uygulama döngüsü

4. Türkçe-First, Global-Ready
   TR/EN tam destek
   BIST odaklı ama Kripto + ABD hissesi de var

5. Flutter Native Mobil
   TradingView mobil var ama backtestsiz
   Matriks mobil: sadece seyir
   PiyasaPilot: backtest + sinyal mobilde tam çalışır
```

---

*Bu belge PiyasaPilot production dönüşümünün tek yetkili planıdır.
Tamamlanan her görevin başına `[x]` koy.*

---

# PROJE TAMAMLANMA ANALİZİ — 2026-05-16

> Kaynak: Tam kaynak kodu analizi + `uygulama.md` + mevcut bölüm ilerleme tablosu

## Genel Değerlendirme: %58 Tamamlandı

Proje çalışan bir MVP'ye sahip ama production'a çıkabilmesi için kritik açıklar var.

## Bölüm Bazlı Gerçek Durum

| Bölüm | Beyan | Gerçek Tahmin | Açıklama |
|---|---|---|---|
| 0 — DNS / TLS | %35 | **%30** | Sunucu yok, domain elde, DNS ayarı yapılmadı |
| 1 — Marka Tutarlılığı | %100 | **%85** | Logo "Piyasa Pilotu" hâlâ yanlış; bazı eski ref var |
| 2 — Kullanıcı Rol/Yetki | %100 | **%80** | DB migration çalışıyor ama endpoint guard test edilmedi |
| 3 — Backend Auth | %70 | **%65** | Register/login çalışıyor; route koruma eksik, Google OAuth belirsiz |
| 4 — Ekran Tasarımları | %75 | **%60** | Public sayfalar var ama terminal sızması, mobil UX, boş durumlar düzeltilmedi |
| 5 — Ödeme / Stripe | %40 | **%35** | İskelet var; canlı product/price id yok, webhook doğrulanmadı |
| 6 — Admin Paneli | %40 | **%35** | Endpoint var, UI iskelet var; yetki koruması, gerçek veri eksik |
| 7 — Ödeme Sonrası / Plan | %45 | **%40** | Settings sayfası var; billing portal, abonelik yaşam döngüsü eksik |
| 8 — i18n / Hukuki | %82 | **%82** | Public shell, landing/pricing ve risk dili TR/EN sözlüğe bağlandı; terminal içi tüm metinlerin taşınması kaldı |
| 9 — UI Hataları | %100 | **%100** | WEB_UX_TEST_RAPORU blockerları ve 9.17–9.40 regresyon maddeleri frontend tarafında kapandı |
| 10 — Flutter Mobil | %10 | **%5** | Sadece plan var, tek satır kod yok |
| 11 — ClickHouse / Veri | %35 | **%30** | Şema var, facade bağlantısı ve prod entegrasyon eksik |
| 12 — CI/CD | %55 | **%45** | GitHub Actions iskelet var; gerçek deployment pipeline test edilmedi |
| 13 — Monitoring | %55 | **%40** | Sentry/Grafana iskelet var; canlı DSN/dashboard yok |
| 14 — Kabul Testi | %65 | **%65** | Frontend Playwright suite 24/24 geçti; canlı dış entegrasyon ve backend kabul testleri kaldı |
| 15 — AWS | %10 | **%5** | Plan var, kurulum yapılmadı |
| 16 — Teknik Maddeler | %75 | **%75** | Frontend analytics/PWA/skeleton/code-splitting ve E2E kontratı stabilize edildi; platform/monitoring işleri kaldı |
| 17 — Büyüme / Roadmap | %25 | **%20** | Waitlist var, referral/pazarlama yok |

## Katman Bazlı Sağlık

```
Terminal Çekirdeği (Grafik, Backtest, Strateji, Eğitimler)   ██████████░░  ~75%
Veri Altyapısı (yfinance/Binance cache, BIST poller)          ███████░░░░░  ~60%
Auth / Kullanıcı Sistemi                                       ████████░░░░  ~65%
Ödeme / Abonelik                                               ████░░░░░░░░  ~35%
UI Kalitesi / UX (tasarım, boş durumlar, mobil)               █████░░░░░░░  ~45%
Deployment / DevOps                                            ████░░░░░░░░  ~30%
Mobil Uygulama (Flutter)                                       █░░░░░░░░░░░  ~5%
```

## Production'a Çıkabilirlik

**Şu an üretim çıkışı için hazır değil.** Temel blocker'lar:

1. **Market Ticker boş** — ilk izlenim kötü (9.17)
2. **Public sayfalar terminal sızması** — güven kaybı (9.5)
3. **Admin panelinde yetki koruması yok** — güvenlik açığı (9.7)
4. **Stripe canlı ürün/price id** bağlı değil — para alınamıyor (Bölüm 5)
5. **AWS / sunucu** kurulmadı — domain canlıya çıkamıyor (Bölüm 15)
6. **Mobil web** yetersiz (Bölüm 9.6) — geniş kullanıcı kitlesini kaybettiriyor

## Önümüzdeki 4 Haftada Kapanabilecekler

Sadece web MVP için sıkı öncelik:

**Hafta 1 (Blocker'lar):**
- 9.17 Market Ticker düzelt
- 9.5 Public route izolasyonu
- 9.7 Admin/Settings route koruması
- 9.10 + 9.28 Portföy format hatası

**Hafta 2 (UX Kalitesi):**
- 9.17–9.31 arası küçük UI düzeltmeleri (grafik, strateji, screener)
- Bölüm 5: Stripe canlı ürün tanımları

**Hafta 3 (Deploy):**
- Bölüm 15: AWS EC2 + nginx kurulum
- Bölüm 0: DNS A kaydı, TLS sertifikası
- Bölüm 12: CI/CD pipeline ilk çalıştırma

**Hafta 4 (Stabilizasyon):**
- Bölüm 13: Sentry DSN bağla
- Bölüm 14: Kabul testlerini çalıştır
- İlk gerçek kullanıcı onboarding
