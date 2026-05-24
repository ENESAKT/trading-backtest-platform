# PiyasaPilot — Sen Yapacaksın 🛠️

> **Bu dosya**: AI'nin yapamayacağı, gerçek hesap, para veya fiziksel erişim
> gerektiren adımların tam listesidir. Her maddeyi tamamladığında `[x]` yap.
>
> Sırayla gitmen önerilir; bağımlılıklar buna göre sıralandı.
> **Tahmini toplam süre:** 2-4 tam iş günü

---

## 0 · Uygulamayı Lokal Başlatmak

```bash
cd ~/Desktop/Backtest   # veya projenin bulunduğu dizin
chmod +x start.sh
./start.sh
```

Tarayıcında `http://localhost:8000` yükle. Hazır!

---

## 1 · Google OAuth Kurulumu

> Kullanıcıların "Google ile Giriş" yapabilmesi için.

- [ ] [Google Cloud Console](https://console.cloud.google.com/) → **Yeni Proje** oluştur: `PiyasaPilot`.
- [ ] Sol menü → **APIs & Services → OAuth consent screen**
  - User Type: **External**
  - App name: `PiyasaPilot`
  - Support email: `destek@piyasapilot.com` (veya kişisel Gmail)
  - Authorized domain: `piyasapilot.com`
- [ ] **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
  - Application type: **Web application**
  - Name: `PiyasaPilot Web`
  - Authorized JS origins:
    ```
    https://piyasapilot.com
    http://localhost:8000
    ```
  - Authorized redirect URIs:
    ```
    https://piyasapilot.com/api/auth/google/callback
    http://localhost:8000/api/auth/google/callback
    ```
- [ ] `Client ID` ve `Client Secret` değerlerini kopyala.
- [ ] `.env.production` dosyasına ekle:
  ```env
  GOOGLE_CLIENT_ID=...buraya...
  GOOGLE_CLIENT_SECRET=...buraya...
  GOOGLE_REDIRECT_URI=https://piyasapilot.com/api/auth/google/callback
  ```
- [ ] Sunucu restart sonrası `/api/auth/google` yönlendirmesini test et.
- [ ] Yeni kullanıcı → onboarding'e, mevcut kullanıcı → `/app` rotasına gidiyor mu doğrula.

---

## 2 · Stripe Canlı Ödeme Kurulumu

> Kullanıcılardan ücret almak için.

- [ ] [stripe.com](https://stripe.com) → Hesabını oluştur veya giriş yap.
- [ ] Dashboard → **Live mode**'a geç (sağ üst toggle).
- [ ] **Business profile**, vergi ve payout bilgilerini tamamla.

### Ürün ve Fiyat Oluşturma

- [ ] **Products → Add Product**: `PiyasaPilot Pro`
  - Monthly: `₺X,XX` (senin belirleyeceğin TL fiyatı) — recurring
  - Yearly: `₺X,XX` — recurring
- [ ] **Products → Add Product**: `PiyasaPilot Ultra`
  - Monthly: `₺X,XX`
  - Yearly: `₺X,XX`
- [ ] Her ürünün `Price ID` değerini (örn. `price_abc123`) not al.

### .env Değerleri

- [ ] `.env.production` dosyasına ekle:
  ```env
  STRIPE_SECRET_KEY=sk_live_...
  STRIPE_PUBLISHABLE_KEY=pk_live_...
  STRIPE_PRO_MONTHLY_PRICE_ID=price_...
  STRIPE_PRO_YEARLY_PRICE_ID=price_...
  STRIPE_ULTRA_MONTHLY_PRICE_ID=price_...
  STRIPE_ULTRA_YEARLY_PRICE_ID=price_...
  STRIPE_WEBHOOK_SECRET=whsec_...
  ```

### Webhook Kurulumu

- [ ] **Developers → Webhooks → Add endpoint**:
  ```
  https://piyasapilot.com/api/payments/webhook
  ```
- [ ] Events seç:
  - `checkout.session.completed`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.payment_failed`
- [ ] `Signing secret` → `STRIPE_WEBHOOK_SECRET` değerini al.
- [ ] **Billing → Customer portal** ayarlarını etkinleştir.

### Test

- [ ] Checkout → plan Pro'ya yükseltildi mi?
- [ ] Duplicate webhook tekrar gönderildiğinde idempotency çalışıyor mu?
- [ ] Cancel → dönem sonunda iptale düşüyor mu?
- [ ] Başarısız ödeme → UI `past_due` gösteriyor mu?

---

## 3 · AWS Production Sunucu Kurulumu

> Uygulamayı internette yayına almak için.

### Ön Hazırlık

- [ ] [AWS Console](https://console.aws.amazon.com) → Region: **eu-central-1 (Frankfurt)**
- [ ] **Billing → Cost Explorer**: Eski/gereksiz kaynakları sil.
  - NAT Gateway varsa sil (aylık ~$35 ücret)
  - Kullanılmayan EBS, EIP, RDS, ECR temizle
- [ ] **Billing → Budgets**: Aylık limit oluştur (önerim: $100)
- [ ] SSH key oluştur (Terminal'de):
  ```bash
  ssh-keygen -t ed25519 -f ~/.ssh/piyasapilot-key -C "piyasapilot-prod"
  ```
  `~/.ssh/piyasapilot-key.pub` içeriğini AWS Key Pairs'e yükle.

### Terraform ile Altyapı

- [ ] `infra/aws/variables.tf` dosyasını aç, şu değerleri doldur:
  ```hcl
  variable "key_name" { default = "piyasapilot-key" }
  variable "allowed_ssh_cidr" { default = "SENİN_IP/32" }  # whatismyip.com
  ```
- [ ] Terraform çalıştır:
  ```bash
  cd infra/aws
  terraform init
  terraform plan    # çıktıyı kontrol et
  terraform apply   # onay: yes
  ```
- [ ] Çıktıdan `elastic_ip` değerini not al.

### Sunucu Kurulumu

- [ ] SSH ile bağlan:
  ```bash
  ssh -i ~/.ssh/piyasapilot-key ubuntu@<ELASTIC_IP>
  ```
- [ ] Docker kurulumu:
  ```bash
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker ubuntu
  ```
- [ ] Veri diskini mount et:
  ```bash
  sudo mkfs.ext4 /dev/nvme1n1   # disk adını lsblk ile doğrula
  sudo mkdir -p /data
  sudo mount /dev/nvme1n1 /data
  echo '/dev/nvme1n1 /data ext4 defaults 0 2' | sudo tee -a /etc/fstab
  ```
- [ ] Klasörler oluştur:
  ```bash
  sudo mkdir -p /data/{mysql,clickhouse,redis,app/cache,app/parquet,backups}
  sudo chown -R ubuntu:ubuntu /data
  ```
- [ ] Repo'yu clone et:
  ```bash
  git clone https://github.com/SENIN_KULLANICI/piyasapilot.git /home/ubuntu/app
  ```
- [ ] `.env.production` dosyasını `/home/ubuntu/app/.env` olarak oluştur.
- [ ] Docker Compose ile başlat:
  ```bash
  cd /home/ubuntu/app
  docker compose -f infra/docker-compose.prod.yml build
  docker compose -f infra/docker-compose.prod.yml up -d
  ```
- [ ] Migration'ları uygula:
  ```bash
  docker compose exec api python -m alembic upgrade head
  # veya migration scriptiniz varsa:
  docker compose exec api python scripts/run_migrations.py
  ```
- [ ] Health check: `curl http://localhost:8000/api/health`

---

## 4 · DNS ve TLS Kurulumu

> `piyasapilot.com`'un sunucuna işaret etmesi için.

- [ ] [METUnic Panel](https://nic.metu.edu.tr) → DNS Yönetimi → `piyasapilot.com`
- [ ] DNS kayıtları ekle (TTL: 3600):
  | Type | Name | Value |
  |------|------|-------|
  | A | @ | `<ELASTIC_IP>` |
  | A | www | `<ELASTIC_IP>` |
  | A | api | `<ELASTIC_IP>` |
- [ ] DNS yayılımını doğrula (~5-30 dakika):
  ```bash
  dig piyasapilot.com A +short
  dig www.piyasapilot.com A +short
  ```
- [ ] Sunucuda port 80'nin açık olduğundan emin ol.
- [ ] TLS sertifikası al:
  ```bash
  sudo apt install certbot python3-certbot-nginx -y
  sudo certbot --nginx -d piyasapilot.com -d www.piyasapilot.com
  ```
- [ ] Auto-renew test et:
  ```bash
  sudo certbot renew --dry-run
  ```
- [ ] HTTPS çalışıyor mu: `curl -I https://piyasapilot.com`
- [ ] HTTP → HTTPS redirect çalışıyor mu: `curl -I http://piyasapilot.com`
- [ ] `www` → `@` 301 çalışıyor mu: `curl -I https://www.piyasapilot.com`

---

## 5 · Email Sağlayıcı Kurulumu

> Kullanıcılara doğrulama, şifre sıfırlama maili göndermek için.

**Öneri sırası:** [Resend](https://resend.com) (en kolay) → [Postmark](https://postmarkapp.com) → Gmail App Password

### Resend Kurulumu (Önerilen)

- [ ] resend.com → Hesap oluştur → **API Keys → Create**
- [ ] Domain doğrulama: `piyasapilot.com` → DNS kayıtlarını (SPF/DKIM) METUnic'e ekle.
- [ ] `.env.production`:
  ```env
  RESEND_API_KEY=re_...
  SMTP_FROM=noreply@piyasapilot.com
  ```
- [ ] Test maili gönder → gelen kutusuna ve spam klasörüne bak.
- [ ] Email doğrulama, şifre sıfırlama linklerinin `https://piyasapilot.com` ile açıldığını kontrol et.

---

## 6 · Sentry (Hata Takibi) Kurulumu

> Production'daki hataları anında görmek için.

- [ ] [sentry.io](https://sentry.io) → Hesap aç (ücretsiz plan yeterli başlangıç için).
- [ ] **Projects → New Project → Python (FastAPI)**: `piyasapilot-backend`
- [ ] **Projects → New Project → JavaScript**: `piyasapilot-frontend`
- [ ] `.env.production`:
  ```env
  SENTRY_DSN=https://...@sentry.io/...
  SENTRY_ENVIRONMENT=production
  ```
- [ ] Backend test: production'da bir 500 hatası tetikle, Sentry'de görünüyor mu?
- [ ] Frontend test: `throw new Error("test")` ekle, sil.

---

## 7 · Grafana + Prometheus Kurulumu

> Sistem metriklerini görmek için.

- [ ] Docker Compose'da Grafana/Prometheus container'larının çalıştığını doğrula:
  ```bash
  docker compose ps | grep -E "grafana|prometheus"
  ```
- [ ] Grafana admin şifresini değiştir: `docker compose exec grafana grafana-cli admin reset-admin-password YENİŞİFRE`
- [ ] `https://piyasapilot.com:3000` (veya iç IP) → Grafana dashboard'u aç.
- [ ] Prometheus scrape targets: `http://localhost:9090/targets` → hepsinin UP olduğunu doğrula.
- [ ] Alert kanalı ekle: Telegram bot veya email.
- [ ] Kritik alarmlar:
  - `/api/health` → status != "ok" → alarm
  - Cache rows = 0 → alarm
  - Worker failure > 5 → alarm

---

## 8 · Yedekleme (Backup) Kurulumu

> Veriyi kaybetmemek için.

- [ ] [AWS S3](https://s3.console.aws.amazon.com) → Bucket oluştur: `piyasapilot-backups-prod`
  - Region: eu-central-1
  - Versioning: etkin
  - Public access: tamamen kapalı
  - Lifecycle: 30 günden eski → sil
- [ ] IAM user oluştur: `piyasapilot-backup`
  - Policy: yalnızca bu bucket'a yazma izni
  - Access key oluştur
- [ ] `.env.production`:
  ```env
  AWS_ACCESS_KEY_ID=...
  AWS_SECRET_ACCESS_KEY=...
  AWS_BACKUP_BUCKET=piyasapilot-backups-prod
  AWS_REGION=eu-central-1
  ```
- [ ] İlk yedek al:
  ```bash
  bash scripts/backup.sh
  ```
- [ ] Cron kur (günlük gece 3):
  ```bash
  crontab -e
  # Ekle: 0 3 * * * /home/ubuntu/app/scripts/backup.sh >> /var/log/backup.log 2>&1
  ```
- [ ] Restore drill yap: `bash scripts/restore_drill.sh` — sonucu sakla.

---

## 9 · Lisanslı BIST/VİOP Veri Sağlayıcı

> Gerçek zamanlı/lisanslı Borsa İstanbul verisi için.

- [ ] **Matriks** ile görüş: [matriks.com.tr](https://matriks.com.tr) → İletişim
- [ ] **Foreks** ile görüş: [foreks.com](https://foreks.com) → API/B2B bölümü
- [ ] Lisans kapsamını yazılı netleştir:
  - Kaç kullanıcıya servis edebilirsin?
  - Veriyi kendi DB'ne kaydedebilir misin?
  - Redistribute (son kullanıcıya göstermek) izni var mı?
  - Fiyat gecikmesi: canlı mı, 15 dk mı?
- [ ] Test ortamı al (çoğunda demo vardır).
- [ ] Sağlayıcı endpoint bilgilerini `.env.production`'a ekle:
  ```env
  BIST_HTTP_URL_TEMPLATE=...
  VIOP_HTTP_URL_TEMPLATE=...
  ```
- [ ] Lisans yoksa Ultra plan metnini güncelle: "canlı veri" → "öncelikli/gecikmeli veri"

---

## 10 · Mobil Uygulama Yayın Hazırlığı

> iOS ve Android store'a çıkmak için.

### Android (Google Play)

- [ ] [play.google.com/console](https://play.google.com/console) → Hesap aç (25 USD bir kez).
- [ ] Package ID: `com.piyasapilot.app`
- [ ] Android signing keystore oluştur (kaybet = yayın biter!):
  ```bash
  keytool -genkey -v -keystore piyasapilot.jks -alias piyasapilot \
    -keyalg RSA -keysize 2048 -validity 10000
  ```
  Bu dosyayı güvenli yerde sakla (Bitwarden, 1Password, şifreli harici disk).

### iOS (App Store)

- [ ] [developer.apple.com](https://developer.apple.com) → Hesap aç (99 USD/yıl).
- [ ] Bundle ID: `com.piyasapilot.app`
- [ ] Signing certificate ve provisioning profile oluştur.

### Firebase (Push Notification)

- [ ] [Firebase Console](https://console.firebase.google.com) → Yeni proje.
- [ ] Android ve iOS uygulamalarını kaydet.
- [ ] `google-services.json` (Android) ve `GoogleService-Info.plist` (iOS) dosyalarını Flutter projesine koy.

### Görseller ve Store Metni

- [ ] App icon (1024x1024 PNG, şeffaf arka plan yok).
- [ ] Splash screen (2048x2048 PNG).
- [ ] Ekran görüntüleri: 6.7", 5.5", iPad (iOS); 6.5", 5.0" (Android).
- [ ] Store açıklaması (Türkçe + İngilizce, 4000 karakter maks).
- [ ] Privacy policy URL: `https://piyasapilot.com/gizlilik`

### Build ve Test

- [ ] Production API URL ayarla (`mobile/lib/config.dart`'ta `BASE_URL`).
- [ ] Release build al:
  ```bash
  flutter build apk --release    # Android
  flutter build ipa --release    # iOS (Mac gerektirir)
  ```
- [ ] TestFlight / Internal testing üzerinden smoke test yap.

---

## 11 · Growth ve Destek Kanalları

- [ ] Destek e-postası: `destek@piyasapilot.com` (Google Workspace veya Fastmail).
- [ ] Live chat aracı seç: [Crisp](https://crisp.chat) (ücretsiz plan var) veya [Tawk.to](https://tawk.to).
- [ ] Telegram kanalı aç: `@PiyasaPilotResmi` (karar senin).
- [ ] [Product Hunt](https://producthunt.com) → Lansman materyallerini hazırla (logo, GIF, kısa açıklama).
- [ ] Blog altyapısı: mevcut statik sayfa yeterli başlangıç için.

---

## Kontrol Paneli

| # | Görev | Tahmini Süre | Durum |
|---|-------|-------------|-------|
| 1 | Google OAuth | 30 dk | [ ] |
| 2 | Stripe Ödeme | 2-3 saat | [ ] |
| 3 | AWS EC2 Kurulumu | 3-4 saat | [ ] |
| 4 | DNS + TLS | 1 saat (+ bekleme) | [ ] |
| 5 | Email Sağlayıcı | 30 dk | [ ] |
| 6 | Sentry | 30 dk | [ ] |
| 7 | Grafana | 1 saat | [ ] |
| 8 | Yedekleme | 1 saat | [ ] |
| 9 | BIST Lisansı | 1-2 hafta (görüşme) | [ ] |
| 10 | Mobil Store | 2-3 gün | [ ] |
| 11 | Growth Kanalları | 2-3 saat | [ ] |

---

## 12 · Son Kontrol: Canlıya Almadan Önce

- [ ] `https://piyasapilot.com/api/health` → `{"status":"ok"}`
- [ ] `https://piyasapilot.com` → Login ekranı yüklüyor
- [ ] Google OAuth ile giriş yapılıyor
- [ ] Stripe test ödemesi başarılı
- [ ] Email doğrulama maili gelen kutusuna geliyor (spam değil)
- [ ] Sentry'de test hatasını görüyorum
- [ ] `curl -I https://www.piyasapilot.com` → 301 `piyasapilot.com`'a yönlendiriyor
- [ ] Certbot `sudo certbot renew --dry-run` başarılı

---

> **Not:** Herhangi bir adımda takılırsan, bu dosyanın ilgili bölümünü Cowork'a
> yapıştır — devam etmeni sağlayacak komut veya kod yazabilirim.
