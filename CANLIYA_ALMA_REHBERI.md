# PiyasaPilot — Canlıya Alma Rehberi

> Bu dosya **sadece senin yapacağın adımları** içerir.  
> Her aşama bittikten sonra bana söyle, yüzdeyi güncelleyelim ve bir sonraki aşamaya geçelim.

---

## GENEL İLERLEME

```
Aşama 1 — Git & Kod          [ ] %0   ░░░░░░░░░░░░░░░░░░░░
Aşama 2 — AWS EC2 + RDS      [ ] %0   ░░░░░░░░░░░░░░░░░░░░
Aşama 3 — Domain & SSL       [ ] %0   ░░░░░░░░░░░░░░░░░░░░
Aşama 4 — Ortam Değişkenleri [ ] %0   ░░░░░░░░░░░░░░░░░░░░
Aşama 5 — İlk Deploy         [ ] %0   ░░░░░░░░░░░░░░░░░░░░
Aşama 6 — Stripe Ödeme       [ ] %0   ░░░░░░░░░░░░░░░░░░░░
Aşama 7 — BIST Verisi        [ ] %0   ░░░░░░░░░░░░░░░░░░░░
Aşama 8 — İlk Kullanıcılar   [ ] %0   ░░░░░░░░░░░░░░░░░░░░

TOPLAM İLERLEME: %0 ░░░░░░░░░░░░░░░░░░░░
```

> **⚠️ KRİTİK NOTLAR (2026-05-17 denetiminde tespit edildi):**
> - Aşama 1'e geçmeden önce kod düzeyindeki kritik hatalar giderilmeli. Detaylar: `yapilacak.md` Bölüm 1.
> - Aşama 4 `.env` değişken listesi eksikti — aşağıda tamamlandı.
> - Aşama 6 Stripe webhook URL'si yanlıştı — aşağıda düzeltildi.
> - Migration sırası (001→010) Aşama 5'e eklendi.

---

## AŞAMA 1 — Git Commit (Bilgisayarında)

> Tüm kod değişiklikleri klasörüne kaydedildi ama henüz commit edilmedi.

### Adım 1.1 — Terminal aç
Mac'te: `Cmd + Space` → "Terminal" yaz → Enter

### Adım 1.2 — Proje klasörüne git
```bash
cd /Users/enes/AgentWorkspace/Backtest
```

### Adım 1.3 — Değişiklikleri kaydet
```bash
git add .
git commit -m "feat: production-ready — tüm düzeltmeler ve geliştirmeler"
```

### Adım 1.4 — Kontrol et
```bash
git log --oneline -3
```
En üstte yeni commit görünmeli.

### Adım 1.5 — GitHub'a gönder
```bash
git push origin main
```

**✅ Bu aşama bitince bana söyle.**

---

## AŞAMA 2 — AWS Altyapı: EC2 + RDS MySQL

> Bu aşamada sunucunu (EC2) ve veritabanını (RDS MySQL) AWS'de ayağa kaldırıyoruz.
> AWS konsoluna gir: https://console.aws.amazon.com

---

### BÖLÜM A — EC2 Sunucu

#### Adım 2A.1 — EC2 panelini aç
Üst arama çubuğuna "EC2" yaz → EC2 tıkla → **Launch Instance**

#### Adım 2A.2 — Instance ayarları
- **Name:** `piyasapilot-prod`
- **AMI:** Ubuntu Server 22.04 LTS (Free tier eligible)
- **Instance type:** `t3.small` (2 vCPU, 2 GB RAM — min gereksinim)
- **Key pair:** Varsa mevcut `.pem` dosyanı seç, yoksa "Create new key pair" → `piyasapilot-key` → `.pem` formatında indir → güvenli bir yere kaydet (`~/.ssh/` klasörü ideal)

#### Adım 2A.3 — Security Group (Güvenlik Duvarı)
"Edit" tıkla, şu kuralları ekle:

| Tür | Port | Kaynak | Açıklama |
|-----|------|--------|---------|
| SSH | 22 | My IP | Sadece senin IP'n |
| HTTP | 80 | 0.0.0.0/0 | Herkes |
| HTTPS | 443 | 0.0.0.0/0 | Herkes |
| Custom TCP | 8000 | 0.0.0.0/0 | Backend (geçici test) |

Security group adını not al (örn. `sg-0abc123...`) — RDS'te kullanacaksın.

#### Adım 2A.4 — Storage
20 GB gp3 yeterli.

#### Adım 2A.5 — Launch et
"Launch Instance" tıkla. 1-2 dakika bekle, "Running" olsun.

#### Adım 2A.6 — IP adresini not al
Instances listesinde instance'ı seç → **Public IPv4 address** kopyala.
Örnek: `3.72.45.101` — bu IP'yi Aşama 3'te kullanacaksın.

#### Adım 2A.7 — PEM dosyasına izin ver ve bağlan
```bash
chmod 400 ~/.ssh/piyasapilot-key.pem
ssh -i ~/.ssh/piyasapilot-key.pem ubuntu@SUNUCU_IP
```
`ubuntu` yazarsa bağlantı başarılı.

#### Adım 2A.8 — Sunucuya Docker kur
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker ubuntu
newgrp docker
docker --version
docker compose version
```
Her ikisi de versiyon numarası göstermeli.

---

### BÖLÜM B — RDS MySQL Veritabanı

> EC2 ile aynı **Region**'da olmasına dikkat et (örn. ikisi de `eu-central-1`).

#### Adım 2B.1 — RDS panelini aç
AWS konsolda "RDS" yaz → **Create database**

#### Adım 2B.2 — Veritabanı ayarları
- **Engine:** MySQL 8.0
- **Template:** Free tier (başlangıç) veya Production
- **DB instance identifier:** `piyasapilot-db`
- **Master username:** `piyasapilot`
- **Master password:** Güçlü bir şifre yaz → **not al** (tekrar göremezsin)
- **Instance class:** `db.t3.micro` (Free tier) veya `db.t3.small`
- **Storage:** 20 GB gp2, Auto scaling açık
- **Multi-AZ:** Production için "Yes" (ücretli), başlangıç için "No"

#### Adım 2B.3 — Bağlantı ayarları
- **VPC:** EC2 ile aynı VPC olmalı (genelde default VPC)
- **Public access:** **No** (sadece EC2 üzerinden erişilecek — güvenli)
- **VPC security group:** "Create new" → isim: `piyasapilot-rds-sg`

#### Adım 2B.4 — Oluştur
"Create database" tıkla. **5-10 dakika** bekle, Status "Available" olsun.

#### Adım 2B.5 — RDS Endpoint'ini kopyala
RDS → Databases → `piyasapilot-db` tıkla → **Endpoint** kopyala.
Örnek: `piyasapilot-db.abc123.eu-central-1.rds.amazonaws.com`

#### Adım 2B.6 — RDS Security Group'a EC2 erişimi ver
AWS → Security Groups → `piyasapilot-rds-sg` seç → **Inbound rules** → Edit inbound rules:
- **Type:** MySQL/Aurora
- **Port:** 3306
- **Source:** EC2 instance'ının security group ID'si (2A.3'te not aldığın `sg-0abc123...`)

> Bu sayede sadece EC2 sunucun veritabanına bağlanabilir, dışarıdan erişilemez.

#### Adım 2B.7 — Veritabanı oluştur
EC2'ya SSH ile bağlan, MySQL client kur ve database oluştur:
```bash
# EC2 üzerinde
sudo apt install -y mysql-client

# RDS'e bağlan (RDS endpoint ve master şifreni yaz)
mysql -h ENDPOINT -u piyasapilot -p
```
Şifreni gir, MySQL shell'e girince:
```sql
CREATE DATABASE piyasapilot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SHOW DATABASES;
EXIT;
```
Listede `piyasapilot` görünmeli.

---

### BÖLÜM C — Redis (Önbellek)

> Strateji tarama ve oturum cache için Redis gerekiyor.
> EC2 üzerinde Docker container olarak çalıştırıyoruz — ayrı servis kurmana gerek yok.

EC2 sunucuda:
```bash
docker run -d --name redis --restart always -p 6379:6379 redis:7-alpine
docker ps | grep redis
```
"Up" görünüyorsa Redis hazır.

---

**✅ Bu aşama bitince bana söyle — hangi adımda takıldıysan da söyle.**

---

## AŞAMA 3 — Domain & SSL

> Uygulamanın bir alan adı (örn. `piyasapilot.com`) olmalı ve HTTPS çalışmalı.

### Adım 3.1 — Domain sağlayıcına gir
Namecheap, GoDaddy, Google Domains — hangisinde aldıysan oraya gir.

### Adım 3.2 — DNS A kaydı ekle
DNS yönetim panelinde iki kayıt ekle:

| Tür | Host | Değer | TTL |
|-----|------|-------|-----|
| A | `@` | `SUNUCU_IP` | 300 |
| A | `www` | `SUNUCU_IP` | 300 |

`SUNUCU_IP` = Aşama 2A.6'da aldığın EC2 IP adresi.

### Adım 3.3 — DNS yayıldı mı? (5–30 dk bekle)
Tarayıcıda: https://dnschecker.org → alan adını yaz → A kaydı her yerde EC2 IP'sini göstermeli.

### Adım 3.4 — SSL sertifikası al (EC2'da)
```bash
sudo apt install -y certbot
sudo certbot certonly --standalone -d piyasapilot.com -d www.piyasapilot.com
```
Alan adını kendininkiyle değiştir. Başarılıysa:
```
Congratulations! Your certificate and chain have been saved at:
/etc/letsencrypt/live/piyasapilot.com/fullchain.pem
```

### Adım 3.5 — Otomatik yenileme kur
```bash
sudo crontab -e
```
En alta ekle:
```
0 3 * * * certbot renew --quiet
```
`Ctrl+X` → `Y` → Enter

**✅ Bu aşama bitince bana söyle.**

---

## AŞAMA 4 — Ortam Değişkenleri (.env dosyası)

> Uygulamanın çalışması için gizli anahtarların sunucuya yazılması gerekiyor.
> **AWS RDS MySQL** kullanıyoruz — SQLite değil.

### Adım 4.1 — EC2'da proje klasörü hazırla
```bash
sudo mkdir -p /opt/piyasapilot
sudo chown ubuntu:ubuntu /opt/piyasapilot
```

### Adım 4.2 — .env dosyasını oluştur
```bash
nano /opt/piyasapilot/.env
```

### Adım 4.3 — Şu değişkenleri doldur

**Zorunlu — Genel (bunlar olmadan uygulama başlamaz):**
```env
SECRET_KEY=          # Rastgele üret: openssl rand -hex 32
JWT_SECRET=          # Ayrı üret: openssl rand -hex 64   ← ÖNEMLİ, SECRET_KEY'den farklı olmalı
FRONTEND_URL=        # https://piyasapilot.com
PUBLIC_BASE_URL=     # https://piyasapilot.com
ALLOWED_ORIGINS=     # https://piyasapilot.com,https://www.piyasapilot.com
CORS_ORIGINS=        # https://piyasapilot.com,https://www.piyasapilot.com
STRICT_ENV_VALIDATION=1
APP_ENV=production
```

**Veritabanı — AWS RDS MySQL:**
```env
MYSQL_HOST=          # Aşama 2B.5'teki RDS endpoint (örn. piyasapilot-db.abc123.eu-central-1.rds.amazonaws.com)
MYSQL_PORT=3306
MYSQL_USER=piyasapilot
MYSQL_PASSWORD=      # Aşama 2B.2'de belirlediğin master password
MYSQL_DATABASE=piyasapilot
```

**Redis (EC2'da Docker container):**
```env
REDIS_URL=redis://localhost:6379/0
```

**Google OAuth (Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client):**
```env
GOOGLE_CLIENT_ID=    # OAuth istemci ID'si
GOOGLE_CLIENT_SECRET=# OAuth istemci secret'ı
```
> Authorized redirect URI olarak şunu ekle: `https://piyasapilot.com/api/auth/google/callback`

**Stripe (Aşama 6'dan sonra doldur):**
```env
STRIPE_SECRET_KEY=   # sk_live_...
STRIPE_PUBLISHABLE_KEY=# pk_live_...
STRIPE_WEBHOOK_SECRET=# whsec_... (Aşama 6.5'ten)
STRIPE_PRO_PRICE_ID= # price_... (Pro aylık — Aşama 6.4'ten)
STRIPE_ULTRA_PRICE_ID=# price_... (Ultra aylık — Aşama 6.4'ten)
```

**E-posta:**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=eposta@gmail.com
SMTP_PASS=           # Gmail "App Password" (normal şifre değil!)
EMAIL_FROM=PiyasaPilot <eposta@gmail.com>
```
> Gmail App Password: Google Hesabı → Güvenlik → 2 Adımlı Doğrulama (açık olmalı) → "Uygulama şifreleri" → "Mail" → şifre oluştur

**Sentry (ücretsiz plan yeterli — https://sentry.io → yeni proje → DSN kopyala):**
```env
SENTRY_DSN=          # https://...@sentry.io/...
```

**Telegram Bildirim (opsiyonel — @BotFather → /newbot):**
```env
TELEGRAM_BOT_TOKEN=  # 123456:ABC-DEF...
TELEGRAM_CHAT_ID=    # Bildirimlerin gideceği chat/kanal ID'si
```

### Adım 4.4 — SECRET_KEY üret ve doldur
EC2'da yeni terminal penceresinde:
```bash
openssl rand -hex 32
```
Çıkan değeri `SECRET_KEY=` satırına yapıştır.

### Adım 4.5 — Kaydet
`Ctrl+X` → `Y` → Enter

**✅ Bu aşama bitince bana söyle.**

---

## AŞAMA 5 — İlk Deploy

> Kod sunucuya çekilecek, Docker ile ayağa kalkacak, veritabanı tabloları oluşacak.

### Adım 5.1 — Repoyu EC2'ya çek
```bash
cd /opt
git clone https://github.com/ENESAKT/piyasapilot.git
cd piyasapilot
```
> Eğer repo private ise, GitHub token ile clone et:
> GitHub → Settings → Developer settings → Personal access tokens → token oluştur  
> `git clone https://TOKEN@github.com/ENESAKT/piyasapilot.git`

### Adım 5.2 — .env dosyasını yerleştir
```bash
# .env'i /opt/piyasapilot/.env konumuna oluşturduysan zaten doğru yerde
ls -la /opt/piyasapilot/.env
```

### Adım 5.3 — Veritabanı tablolarını oluştur (Migration sırası kritik!)
```bash
cd /opt/piyasapilot
# Migration'lar 001'den 009'a kadar sırayla uygulanmalı:
docker compose -f docker/docker-compose.prod.yml run --rm backend python -m alembic upgrade head
```
> Eğer alembic kullanmıyorsan SQL migration dosyalarını elle uygula:
> ```bash
> for i in 001 002 003 004 005 006 007 008 009; do
>   mysql -h ENDPOINT -u piyasapilot -p piyasapilot < infra/mysql/migrations/${i}_*.sql
> done
> ```
>
> **Not:** Mevcut migration'lar 001–009 arasındadır (010 yoktur).
> `jti` kolonu zaten migration 007 (`007_auth_tables.sql`) içinde `refresh_tokens` tablosuna dahildir.
> Token blocklist için migration 007'nin uygulandığından emin ol.

### Adım 5.4 — Uygulamayı başlat
```bash
docker compose -f docker/docker-compose.prod.yml up -d --build
```
İlk seferinde 3-5 dakika sürebilir.

### Adım 5.5 — Durumu kontrol et
```bash
docker compose -f docker/docker-compose.prod.yml ps
```
Tüm servisler `Up (healthy)` olmalı.

### Adım 5.6 — Tarayıcıda aç
`https://piyasapilot.com` adresine git. PiyasaPilot açılıyorsa 🎉

### Adım 5.7 — Hata varsa log'a bak
```bash
docker compose -f docker/docker-compose.prod.yml logs --tail=50 backend
```

**✅ Bu aşama bitince bana söyle.**

---

## AŞAMA 6 — Stripe Ödeme Sistemi

> Pro ve Ultra plan satışı için Stripe canlı moda geçilmesi gerekiyor.

### Adım 6.1 — Stripe'a giriş yap
https://dashboard.stripe.com

### Adım 6.2 — Canlı moda geç
Sağ üstte **"Test mode"** yazıyorsa → toggle ile **Live mode**'a geç.

### Adım 6.3 — API anahtarlarını al
Sol menü → Developers → API keys:
- **Publishable key** (`pk_live_...`) → kopyala
- **Secret key** (`sk_live_...`) → kopyala

### Adım 6.4 — Ürünleri oluştur
Sol menü → Product catalog → **+ Add product**

**Pro Plan:**
- Ad: `Pro` | Fiyatlandırma: Recurring
- Aylık: ₺299/mo → **Price ID** kopyala (`price_...`)
- Yıllık: ₺2990/yr → **Price ID** kopyala

**Ultra Plan:**
- Ad: `Ultra`
- Aylık: ₺599/mo → **Price ID** kopyala
- Yıllık: ₺5990/yr → **Price ID** kopyala

### Adım 6.5 — Webhook kur
Sol menü → Developers → Webhooks → **+ Add endpoint**:
- **URL:** `https://piyasapilot.com/api/payments/webhook`  ← **DİKKAT:** `/api/billing/webhook` değil, `/api/payments/webhook`
- **Events:** `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`
- **Webhook signing secret** (`whsec_...`) → kopyala

### Adım 6.6 — .env'e ekle
```bash
nano /opt/piyasapilot/.env
```
En alta:
```env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRO_PRICE_ID=price_...        # Pro aylık Price ID
STRIPE_ULTRA_PRICE_ID=price_...      # Ultra aylık Price ID
```
> **Not:** Aşama 4'te zaten Stripe değişkenlerini eklemiş olabilirsin. Eğer öyleyse güncelle, tekrar ekleme.

### Adım 6.7 — Backend'i yeniden başlat
```bash
cd /opt/piyasapilot
docker compose -f docker/docker-compose.prod.yml restart backend
```

### Adım 6.8 — Test et
`/pricing` sayfasına git → bir plan seç → Stripe ödeme sayfası açılmalı.

**✅ Bu aşama bitince bana söyle.**

---

## AŞAMA 7 — BIST Veri Lisansı

> Kripto ve ABD hisse verileri zaten çalışıyor. BIST anlık veri için Türk veri sağlayıcısı gerekiyor.

### Seçenek A — Matriks (Önerilen)
https://www.matriksbilgi.com.tr → iletişim formu → "Algoritmik trading platformu için anlık BIST veri API'si"

### Seçenek B — Rasyonet
https://www.rasyonet.com → kurumsal veri API teklifi

### Seçenek C — Foreks
https://www.foreks.com → kurumsal anlık veri API

### Adım 7.1 — Başvur
E-posta veya form ile başvur. Genellikle 2-5 iş günü yanıt.

### Adım 7.2 — API belgelerini paylaş
Erişim gelince API belgelerini bana ilet — entegrasyonu birlikte yaparız.

**✅ Bu aşama bitince bana söyle.**

---

## AŞAMA 8 — İlk Kullanıcılar

> Altyapı hazır, ödeme çalışıyor. Kullanıcı zamanı.

### Adım 8.1 — Waitlist e-postalarını gönder
Waitlist'tekilere "platform açıldı" maili at.

### Adım 8.2 — PWA testi (Telefon)
Telefonundan `https://piyasapilot.com` aç:
- **iOS:** Alt menü → "Paylaş" → "Ana Ekrana Ekle"
- **Android:** Sağ üst 3 nokta → "Ana ekrana ekle"

Uygulama gibi açılmalı, adres çubuğu görünmemeli.

### Adım 8.3 — İlk gerçek ödemeyi test et
Gerçek Pro plan satın al → Stripe'tan iade al. Akış: ödeme → webhook → kullanıcı planı güncelleme → e-posta bildirimi.

### Adım 8.4 — MySQL verilerini doğrula
```bash
mysql -h ENDPOINT -u piyasapilot -p piyasapilot
```
```sql
SELECT COUNT(*) FROM users;
SELECT id, email, plan FROM users ORDER BY created_at DESC LIMIT 5;
```

### Adım 8.5 — Geri bildirim topla
İlk 10 kullanıcıdan yazılı geri bildirim al.

**✅ Bu aşama bitince bana söyle — uygulama tam canlıda!**

---

## HIZLI REFERANS

| Şey | Nerede |
|-----|--------|
| EC2 IP | AWS → EC2 → Instances → Public IPv4 |
| RDS Endpoint | AWS → RDS → Databases → piyasapilot-db |
| SSL sertifikası | `/etc/letsencrypt/live/piyasapilot.com/` |
| Proje klasörü | `/opt/piyasapilot/` |
| .env dosyası | `/opt/piyasapilot/.env` |
| Loglar | `docker compose -f docker/docker-compose.prod.yml logs --tail=100 backend` |
| Yeniden başlat | `docker compose -f docker/docker-compose.prod.yml restart backend` |
| DB bağlantısı | `mysql -h ENDPOINT -u piyasapilot -p piyasapilot` |
| Redis kontrol | `docker exec -it redis redis-cli ping` → `PONG` gelmeli |

---

## NOTLAR

- Her aşama bittikten sonra bana söyle, bu dosyayı güncelleyelim ve yüzdeyi ilerletelim.
- Bir adımda takılırsan direkt bana sor, birlikte çözeriz.
- **Sıra önemli:** EC2 hazır olmadan RDS güvenlik grubu ayarlanamaz; RDS olmadan .env doldurulamaz; .env olmadan deploy başlamaz.

---

---

## GÜVENLİK SON KONTROL LİSTESİ (Canlıya Almadan Önce)

- [ ] `JWT_SECRET` `.env`'de dolu ve `SECRET_KEY`'den farklı (min 64 karakter).
- [ ] `STRICT_ENV_VALIDATION=1` set edildi.
- [ ] EC2 Security Group'ta port `8000` kapalı (sadece 80 ve 443 açık).
- [ ] Grafana default şifresi (`admin/piyasapilot`) değiştirildi.
- [ ] `.env` dosyası git'e commit edilmedi (`git status` ile kontrol et).
- [ ] Stripe test anahtarları (`sk_test_...`) production `.env`'de yok — sadece `sk_live_...` var.
- [ ] Google OAuth Authorized redirect URI: `https://piyasapilot.com/api/auth/google/callback` eklendi.
- [ ] Webhook URL Stripe'ta `https://piyasapilot.com/api/payments/webhook` olarak kayıtlı.

---

*Son güncelleme: 2026-05-17 — Aşama 0/8 tamamlandı (%0) | Rehber kritik düzeltmelerle güncellendi.*
