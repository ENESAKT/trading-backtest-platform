# PiyasaPilot Canlıya Çıkış (Deployment) Rehberi

Bu dosya uygulamanın Production ortamına alınması için gerekli adımları içermektedir.

## 1. Ön Gereksinimler

- Sunucuda `Docker` ve `Docker Compose` kurulu olmalı.
- Domain DNS kayıtları sunucu IP'sine yönlendirilmiş olmalı.
- Git, sunucu ortamında yapılandırılmış olmalıdır.
- Production compose her zaman `--env-file ../.env.production` ile çalıştırılmalıdır; aksi halde veritabanları güvenli olmayan default değerlere düşebilir veya compose başlamaz.

## 2. İlk Kurulum ve Repo Çekme

Sunucu üzerinde projeyi clone'layın:
```bash
git clone https://github.com/ENESAKT/trading-backtest-platform.git piyasapilot
cd piyasapilot
```

AWS EC2'de ek EBS volume kullanılıyorsa Docker verisini bu diske taşıyın:
```bash
sudo bash scripts/deployment/setup_ec2_data_volume.sh
```

## 3. Environment (Çevre Değişkenleri) Yapılandırması

Config dosyasını `.env.production` adıyla oluşturun. Bu dosya kesinlikle git üzerinde saklanmamalıdır!

```bash
cp .env.production.example .env.production
nano .env.production
```

Mutlaka doldurulması gereken veya değiştirilmesi gereken alanlar:
- `APP_ENV=production`
- `PUBLIC_BASE_URL=https://<domain_adresiniz>`
- `CLICKHOUSE_USER` / `CLICKHOUSE_PASSWORD`
- `MYSQL_ROOT_PASSWORD` / `MYSQL_USER` / `MYSQL_PASSWORD`
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`
- (Diğer tüm provider API keyleri)

## 4. Servisleri Başlatma

İlk TLS sertifikası alınmadan önce HTTP-only bootstrap nginx ile servisleri kaldırın:

```bash
cd infra
NGINX_CONF=../docker/nginx.bootstrap.conf docker compose --env-file ../.env.production -f docker-compose.prod.yml build
NGINX_CONF=../docker/nginx.bootstrap.conf docker compose --env-file ../.env.production -f docker-compose.prod.yml up -d
```

DNS A kayıtları bu sunucunun Elastic IP adresine yönlendikten sonra TLS sertifikasını alın:

```bash
cd ..
DOMAIN=piyasapilotu.com EMAIL=admin@piyasapilotu.com bash scripts/deployment/setup_tls.sh
```

Sertifika oluştuktan sonra production TLS nginx konfigürasyonuna geçin:

```bash
cd infra
docker compose --env-file ../.env.production -f docker-compose.prod.yml up -d nginx
```

## 5. Sağlık ve Veritabanı Kontrolü

Sistem ayağa kalktıktan sonra veri platformunun (ClickHouse ve MySQL) doğru çalıştığından emin olmak için health check scriptini çalıştırın:

```bash
docker compose --env-file ../.env.production -f docker-compose.prod.yml exec api python /app/scripts/data_platform/health_check.py
```

## 6. SSL/TLS ve Domain Ayarı

Nginx production konfigürasyonu TLS sertifikası bekler. İlk kurulumda önce `docker/nginx.bootstrap.conf` kullanılmalı, sonra `scripts/deployment/setup_tls.sh` ile sertifika `infra/certbot/conf` altına yazdırılmalıdır.

```bash
DOMAIN=piyasapilotu.com EMAIL=admin@piyasapilotu.com bash scripts/deployment/setup_tls.sh
```

Nginx servisini yeniden başlatın:
```bash
docker compose --env-file ../.env.production -f docker-compose.prod.yml restart nginx
```

## 7. Yedekleme Geri Dönüş (Rollback) ve Backup (Yedekleme)

### Backup Senaryosu
- MySQL log ve metadata barındırdığından periyodik olarak dump alınmalı.
- ClickHouse data dosyaları yedeklenebilir.

### Rollback (Bir Önceki Sürüme Dönüş)
İşler ters giderse:
1. İlgili `docker compose --env-file ../.env.production -f docker-compose.prod.yml down` komutunu çalıştırın.
2. Git üzerinden çalışan önceki stabil commit'e checkout olun: `git checkout <hash>`
3. Yeniden build edip kaldırın:
   ```bash
   docker compose --env-file ../.env.production -f docker-compose.prod.yml build
   docker compose --env-file ../.env.production -f docker-compose.prod.yml up -d
   ```

## 8. Kontrol Komutları

Sunucudaki güncel durumu Makefile komutları ile gözlemleyebilirsiniz (lokalde olduğu gibi).
`repo-cleanup-report` veya `borfin-integration-check` çalıştırarak kod tabanında kaçak/boyutlu dosya olup olmadığını sürekli doğrulayabilirsiniz.

---

## 🚨 Canlıya Almadan Önce Doldurulması Zorunlu Env Değişkenleri

`.env.production` dosyasındaki aşağıdaki değişkenler `BURAYA_YAZ` olarak bırakılmıştır.
**Bu değişkenler doldurulmadan uygulama güvenli şekilde başlatılamaz.**

### Kritik (Uygulama başlamaz veya güvensiz çalışır)

| Değişken | Açıklama | Nasıl Üretilir |
|---|---|---|
| `API_KEY` | Backend dahili API kimlik doğrulama anahtarı | `openssl rand -hex 32` |
| `JWT_SECRET` | JWT token imzalama anahtarı | `openssl rand -hex 32` |
| `MYSQL_PASSWORD` | MySQL uygulama kullanıcısı şifresi | Güçlü rastgele şifre belirleyin |
| `MYSQL_ROOT_PASSWORD` | MySQL root şifresi | Güçlü rastgele şifre belirleyin |
| `DATABASE_URL` | SQLAlchemy bağlantı URL'si (`mysql+pymysql://...`) | `MYSQL_PASSWORD` ile güncelle |
| `MYSQL_URL` | Async MySQL bağlantı URL'si (`mysql+aiomysql://...`) | `MYSQL_PASSWORD` ile güncelle |

### Ödeme Sistemi (Stripe entegrasyonu kullanılıyorsa)

| Değişken | Açıklama |
|---|---|
| `STRIPE_SECRET_KEY` | Stripe Dashboard → Developers → API Keys |
| `STRIPE_WEBHOOK_SECRET` | Stripe Dashboard → Webhooks → Signing secret |
| `STRIPE_PRO_PRICE_ID` | Pro plan aylık fiyat ID'si |
| `STRIPE_ULTRA_PRICE_ID` | Ultra plan aylık fiyat ID'si |
| `STRIPE_PRO_PRICE_ID_YEARLY` | Pro plan yıllık fiyat ID'si |
| `STRIPE_ULTRA_PRICE_ID_YEARLY` | Ultra plan yıllık fiyat ID'si |

### Google OAuth (sosyal giriş kullanılıyorsa)

| Değişken | Açıklama |
|---|---|
| `GOOGLE_CLIENT_ID` | Google Cloud Console → OAuth 2.0 Client ID |
| `GOOGLE_CLIENT_SECRET` | Google Cloud Console → OAuth 2.0 Client Secret |

### İzleme ve Bildirimler (opsiyonel ama önerilir)

| Değişken | Açıklama |
|---|---|
| `SENTRY_DSN` | Sentry projesinden alınan DSN URL'si |
| `TELEGRAM_BOT_TOKEN` | @BotFather'dan alınan bot token |
| `TELEGRAM_CHAT_ID` | Bildirimlerin gönderileceği chat ID |
| `SMTP_USER` | SMTP e-posta adresi |
| `SMTP_PASS` | SMTP uygulama şifresi |
| `NOTIFY_EMAIL_TO` | Sistem bildirimleri için alıcı e-posta |

### ClickHouse (veri katmanı)

| Değişken | Açıklama |
|---|---|
| `CLICKHOUSE_PASSWORD` | ClickHouse kullanıcı şifresi |

> **Not:** `BIST_HTTP_URL_TEMPLATE`, `BIST_HTTP_AUTH_HEADER`, `VIOP_HTTP_URL_TEMPLATE`, `VIOP_HTTP_AUTH_HEADER` boş bırakılabilir — yfinance proxy aktif olur.

### Hızlı Kontrol

```bash
# .env.production içinde hâlâ BURAYA_YAZ olan değişkenleri listele:
grep "BURAYA_YAZ" .env.production
```

Yukarıdaki komut çıktı vermiyorsa tüm zorunlu değerler doldurulmuştur.
