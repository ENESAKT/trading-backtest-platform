# PiyasaPilot Canlıya Çıkış (Deployment) Rehberi

Bu dosya uygulamanın Production ortamına alınması için gerekli adımları içermektedir.

## 1. Ön Gereksinimler

- Sunucuda `Docker` ve `Docker Compose` kurulu olmalı.
- Domain DNS kayıtları sunucu IP'sine yönlendirilmiş olmalı.
- Git, sunucu ortamında yapılandırılmış olmalıdır.

## 2. İlk Kurulum ve Repo Çekme

Sunucu üzerinde projeyi clone'layın:
```bash
git clone https://github.com/ENESAKT/Backtest.git piyasapilot
cd piyasapilot
```

## 3. Environment (Çevre Değişkenleri) Yapılandırması

Config dosyasını `.env.production` adıyla oluşturun. Bu dosya kesinlikle git üzerinde saklanmamalıdır!

```bash
cp .env.example .env.production
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

Production compose dosyası ile servisleri kaldırın:

```bash
cd infra
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

## 5. Sağlık ve Veritabanı Kontrolü

Sistem ayağa kalktıktan sonra veri platformunun (ClickHouse ve MySQL) doğru çalıştığından emin olmak için health check scriptini çalıştırın:

```bash
docker compose -f docker-compose.prod.yml exec api python /app/scripts/data_platform/health_check.py
```

## 6. SSL/TLS ve Domain Ayarı (Opsiyonel ama Önerilir)

Nginx konfigürasyonu şu an HTTP (port 80) üzerinden çalışabilmektedir. Canlı ortamda `certbot` ile Let's Encrypt kullanılarak Nginx üzerinden TLS yapılandırılması önerilir.

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d ornekdomain.com -d www.ornekdomain.com
```

Nginx servisini yeniden başlatın:
```bash
docker compose -f docker-compose.prod.yml restart nginx
```

## 7. Yedekleme Geri Dönüş (Rollback) ve Backup (Yedekleme)

### Backup Senaryosu
- MySQL log ve metadata barındırdığından periyodik olarak dump alınmalı.
- ClickHouse data dosyaları yedeklenebilir.

### Rollback (Bir Önceki Sürüme Dönüş)
İşler ters giderse:
1. İlgili `docker compose -f docker-compose.prod.yml down` komutunu çalıştırın.
2. Git üzerinden çalışan önceki stabil commit'e checkout olun: `git checkout <hash>`
3. Yeniden build edip kaldırın:
   ```bash
   docker compose -f docker-compose.prod.yml build
   docker compose -f docker-compose.prod.yml up -d
   ```

## 8. Kontrol Komutları

Sunucudaki güncel durumu Makefile komutları ile gözlemleyebilirsiniz (lokalde olduğu gibi).
`repo-cleanup-report` veya `borfin-integration-check` çalıştırarak kod tabanında kaçak/boyutlu dosya olup olmadığını sürekli doğrulayabilirsiniz.
