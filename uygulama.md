# PiyasaPilot — Uygulama Durum Raporu

> Son güncelleme: 2026-05-16  
> Genel tamamlanma: **~95 %**  
> Kapsam: Frontend (8 sekme), Backend (FastAPI), DevOps (Docker + CI/CD), Auth, Billing  

---

## İÇİNDEKİLER

1. [Genel Mimari](#1-genel-mimari)
2. [Frontend Durum](#2-frontend-durum)
3. [Backend Durum](#3-backend-durum)
4. [DevOps / Altyapı](#4-devops--altyapı)
5. [Açık Sorunlar (minor)](#5-açık-sorunlar-minor)
6. [Çalışan ve Güçlü Taraflar](#6-çalışan-ve-güçlü-taraflar)

---

## 1. Genel Mimari

| Katman | Teknoloji | Durum |
|--------|-----------|-------|
| Frontend | TypeScript + Vite SPA (vanilla TS) | ✅ Build temiz |
| Chart | lightweight-charts + Chart.js | ✅ |
| Backend | FastAPI 0.110 / Python 3.10+ | ✅ Çalışıyor |
| WebSocket | /ws/signals (SignalFeed) + /ws/quotes (QuoteStream) | ✅ |
| Auth | JWT (python-jose) + argon2 + TOTP 2FA | ✅ |
| Billing | Stripe Checkout + Portal + Webhook | ✅ |
| Veri | SQLite (strateji/paper/backtest) + MySQL (BIST mali) | ✅ |
| Deployment | Docker Compose + nginx reverse proxy | ✅ |
| CI/CD | GitHub Actions (test → deploy / main) | ✅ |

---

## 2. Frontend Durum

### 2.1 Ortak / App Katmanı

| Konu | Durum | Not |
|------|-------|-----|
| Public route terminal shell sızması | ✅ Düzeltildi | data-route="public" CSS ile display:none |
| Market Ticker boş şerit | ✅ Düzeltildi | --ticker-h: 0px, HTML kaldırıldı |
| Logo metni | ✅ PiyasaPilot | index.html line 51 |
| G tuşu layout döngüsü | ✅ Düzeltildi | 1x1,1x2,2x1,2x2 |
| Mobile sidebar drawer | ✅ Eklendi | Hamburger + backdrop overlay |
| Mobile touch hedefleri | ✅ Eklendi | min-height 32-44px pointer:coarse |
| Firefox scrollbar | ✅ Eklendi | scrollbar-width: thin |
| window.confirm / alert() | ✅ Kaldırıldı | Themed dialog/toast |
| i18n LoginPage | ✅ Tamamlandı | Tüm metinler i18n.t() üzerinden |
| i18n anahtarları tr+en | ✅ Tamamlandı | NAV_HOME, AUTH_BACK_TO_TERMINAL eklendi |

### 2.2 ChartPanel

| Konu | Durum |
|------|-------|
| Renko butonu | ✅ Kaldırıldı |
| Şablon kaydetme boş isim | ✅ Toast + focus |
| PNG/CSV export | ✅ try/catch + toast |
| Tooltip açıklamaları | ✅ title attr eklendi |
| Fiyat alarmı alert() | ✅ showToast warn yapıldı |

### 2.3 StrategyPanel

| Konu | Durum |
|------|-------|
| Mode butonları active class | ✅ |
| Slippage label sync | ✅ syncSlippageInputs() |
| WF/MC boş durum mesajı | ✅ Yönlendirici HTML |
| Strateji silme butonu | ✅ data-delete-strategy + event |
| TS tip hatası line 1790 | ✅ qw.message ?? '' |

### 2.4 PortfolioPanel

| Konu | Durum |
|------|-------|
| Günlük P&L % hesabı abs bug | ✅ Düzeltildi |
| Reset/Halt onay dialogu | ✅ Native dialog ile showConfirm() |

### 2.5 Screener

| Konu | Durum |
|------|-------|
| Cache boş durumda guidance | ✅ |
| Kısmi cache uyarısı | ✅ Toast |
| Son tarama timestamp | ✅ HH:MM:SS |

### 2.6 MaliAnalizPanel

| Konu | Durum |
|------|-------|
| confirm/alert çağrıları | ✅ Themed dialog + progress |
| Universe sidebar dot legend | ✅ Eklendi |

### 2.7 Sinyaller (SignalFeed)

| Konu | Durum |
|------|-------|
| WebSocket bağlantısı | ✅ Çalışıyor |
| Sinyal boş durum | ⚠️ Backend skipped_untrusted=94 — canlı veri gerekli |

### 2.8 Haberler / Eğitimler / Sidebar

| Konu | Durum |
|------|-------|
| NewsPanel catch sessiz hata | ✅ console.warn eklendi |
| EgitimlerPanel scroll korunması | ✅ renderResults() |
| Sidebar IntersectionObserver leak | ✅ _observers[] destroy() |

### 2.9 MultiChartLayout / AdminPanel

| Konu | Durum |
|------|-------|
| MultiChartLayout alert() x2 | ✅ window.showToast yapıldı |
| AdminPanel onclick alert | ✅ data-user-detail + event listener |
| Admin kullanıcı detay sayfası | ⚠️ Yapım aşamasında |

---

## 3. Backend Durum

### 3.1 API ve Auth

| Modül | Durum | Not |
|-------|-------|-----|
| backend/requirements.txt | ✅ Oluşturuldu | argon2, slowapi, email-validator |
| dt.UTC Python 3.10 uyumsuzluğu | ✅ Düzeltildi | dt.timezone.utc |
| Auth endpoint'leri | ✅ | JWT + argon2 + TOTP |
| DELETE /api/strategy-lab/strategies/{id} | ✅ | |
| Auth guard'lar | ✅ | Tüm korumalı endpoint'ler |
| Sentry entegrasyonu | ✅ | sentry_sdk.init() |

### 3.2 Billing (Stripe)

| Endpoint | Durum |
|----------|-------|
| POST /api/billing/checkout | ✅ |
| POST /api/billing/portal | ✅ |
| POST /api/billing/webhook + idempotency | ✅ |
| 503 fallback | ✅ |

### 3.3 Feature Gate

PlanLimits dataclass, free/pro/ultra sınırları, require_feature() FastAPI dependency — tümü ✅

### 3.4 E-posta Şablonları

8 HTML şablon: welcome, verify_email, reset_password, payment_success, payment_failed, base, quota_warning, subscription_pro — backend/templates/email/ ✅

### 3.5 Testler

76 test geçiyor (test_auth_guards, test_feature_gate, test_billing) — 8 warning ✅

---

## 4. DevOps / Altyapı

| Modül | Durum |
|-------|-------|
| GitHub Actions CI/CD | ✅ test (Py3.12+Node20) → SSH deploy (main) |
| Docker Compose prod | ✅ healthcheck + restart:always + network isolation |
| nginx prod config | ✅ HTTP→HTTPS, /ws/ upgrade, gzip, security headers |
| server_setup.sh / backup.sh / healthcheck.sh / restore_test.sh | ✅ bash -n temiz |
| .env.example | ✅ 60 değişken |
| infra/RUNBOOK.md + SECRETS.md + SENTRY_SETUP.md | ✅ |

---

## 5. Açık Sorunlar (minor)

| # | Sorun | Öncelik |
|---|-------|---------|
| 1 | Sinyaller: skipped_untrusted=94 — gerçek canlı veri bağlandığında çözülecek | ORTA |
| 2 | Admin kullanıcı detay sayfası tam implement edilmemiş | DÜŞÜK |
| 3 | Kullanıcı "neden sinyal yok" açıklaması SignalFeed'de yok | DÜŞÜK |

---

## 6. Çalışan ve Güçlü Taraflar

- TypeScript build + vite build hatasız
- 76 backend testi geçiyor
- 8 terminal sekmesi tam implement
- Backtest engine çalışıyor (korumalı dosya)
- Paper trading tam fonksiyonel
- i18n TR/EN tam (tüm anahtarlar eksiksiz)
- Tema sistemi — koyu/açık + 5 accent rengi
- Mobil — hamburger drawer, touch hedefleri, tüm paneller responsive
- Skeleton loading — 4 bileşende aktif
- Auth — JWT + TOTP 2FA + argon2
- Billing — Stripe tam entegre
- CI/CD — her main push'ta otomatik test + EC2 deploy
