# PiyasaPilot — Yapılacaklar, Sunucu Çıkış ve Güvenlik Planı

> Tarih: 2026-05-05
> Blokör = yapılmadan sunucuya çıkılmaz. Önemli = çıkılır ama risk taşır.

---

## KURAL — Otonom Planlama Sistemi

> **Bu dosyayı her oturum sonunda güncelle.**

1. **Tik sistemi:** Her maddenin başında checkbox işareti var.
2. **Tamamlanınca:** İşareti `- [x]` yap ve maddeyi `YAPILANLAR.md`'nin ilgili bölümüne taşı.
3. **İlerleme tablosunu güncelle:** Aşağıdaki Bölüm 0'daki tabloda tamamlanan madde sayısını ve ağırlıklı % değerini güncelle.
4. **Kural ihlali:** Hiçbir madde `- [x]` yapılmadan YAPILANLAR'a taşınmaz; hiçbir madde buradan silinmez, sadece taşınır.

---

## 0. Genel İlerleme Tablosu

| Alan | Ağırlık | Tamamlanan | Açık | % |
|------|--------:|:----------:|:-----:|--:|
| Dosya yapısı ve planlama sistemi | 5% | 5/5 | 0 | **100%** |
| Docker konsolidasyonu | 5% | 5/5 | 0 | **100%** |
| TLS / HTTPS | 15% | 4/4 | 0 | **100%** |
| CORS production kısıtlaması | 10% | 1/1 | 0 | **100%** |
| DB port güvenliği (prod) | 5% | 3/3 | 0 | **100%** |
| nginx güvenlik header'ları | 8% | 1/1 | 0 | **100%** |
| Rate limiting | 7% | 1/1 | 0 | **100%** |
| WebSocket kimlik doğrulaması | 5% | 1/1 | 0 | **100%** |
| API_KEY production zorunlu | 5% | 1/1 | 0 | **100%** |
| MySQL / ClickHouse / Redis API entegrasyonu | 20% | 6/6 | 0 | **100%** |
| Sunucuya çıkış (deploy runbook) | 5% | 7/7 | 0 | **100%** |
| Backup otomasyonu | 3% | 2/2 | 0 | **100%** |
| Mali Analiz gerçek veri | 5% | 5/5 | 0 | **100%** |
| Borfin kursları (OCR) | 2% | 5/5 | 0 | **100%** |
| **TOPLAM** | **100%** | | | **100%** |

---

## 1. Gerçek Durum: Nerede Duruyoruz?

| Alan | Plan | Kod |
|------|------|-----|
| ClickHouse/MySQL/Redis infra dosyaları | ✅ Hazır | ✅ SQL şemalar, compose var |
| ClickHouse/MySQL/Redis API bağlantısı | ✅ Planlandı | ✅ Redis → ClickHouse → provider/SQLite zinciri bağlı |
| TLS / HTTPS | ✅ Planlandı | ✅ certbot volume + HTTPS örnek conf + `make tls-setup` hazır |
| CORS production kısıtlaması | ✅ Planlandı | ✅ `CORS_ORIGINS` env'den okunuyor |
| Rate limiting | ✅ Planlandı | ✅ `slowapi` ile `/api/backtest/run` 30/dk |
| WebSocket auth | ✅ Planlandı | ✅ `/ws/quotes` ve `/ws/signals` token kontrol ediyor |
| nginx güvenlik header'ları | ✅ Planlandı | ✅ `docker/nginx.conf` içinde |
| Mali Analiz gerçek veri | ✅ Planlandı | ✅ KAP provider arayüzü + normalize store + oran motoru bağlı |
| MySQL entegrasyonu (API) | ✅ Planlandı | ✅ Migration 001→005 ve financial repository hazır |
| Backup otomasyonu | ✅ Planlandı | ✅ `make backup-now` MySQL dump + ClickHouse backup çalıştırıyor |
| DB portları prod compose | ✅ Planlandı | ✅ expose/internal (düzeltildi) |

---

## 2. Sunucuya Çıkış — Blokör Maddeler

### 2.1 TLS / HTTPS

- [x] Sunucuda certbot kur (`sudo apt install certbot python3-certbot-nginx`)
- [x] Domain için sertifika al (`sudo certbot certonly --standalone -d ornekdomain.com`)
- [x] `docker/nginx.conf`'a HTTPS server block ekle (şablon aşağıda)
- [x] `infra/docker-compose.prod.yml`'de certbot volume'larını aktifleştir

`docker/nginx.conf`'a eklenecek:
```nginx
server {
    listen 443 ssl http2;
    server_name ornekdomain.com;
    ssl_certificate     /etc/letsencrypt/live/ornekdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ornekdomain.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    # ... mevcut location blokları buraya taşınır
}
server {
    listen 80;
    server_name ornekdomain.com;
    return 301 https://$host$request_uri;
}
```

---

### 2.2 CORS — Wildcard Yasağı

- [x] `backend/api/main.py` CORS ayarını env'den oku

```python
_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")]
allow_origins=_origins
```

`.env.production`'a ekle:
```
CORS_ORIGINS=https://ornekdomain.com,https://www.ornekdomain.com
```

---

### 2.3 `.env.production` Zorunlu Alanlar

- [x] `.env.production` dosyasını tüm alanlarla doldur

```env
APP_ENV=production
PUBLIC_BASE_URL=https://ornekdomain.com
CORS_ORIGINS=https://ornekdomain.com
API_KEY=<güçlü_rastgele_key>
CLICKHOUSE_URL=http://clickhouse:8123/piyasapilot
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=<şifre>
DATABASE_URL=mysql+pymysql://piyasapilot:<şifre>@mysql:3306/piyasapilot
MYSQL_ROOT_PASSWORD=<şifre>
MYSQL_USER=piyasapilot
MYSQL_PASSWORD=<şifre>
REDIS_URL=redis://redis:6379/0
TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_CHAT_ID=<id>
SMTP_HOST=smtp.gmail.com
SMTP_USER=<email>
SMTP_PASS=<app_password>
STRICT_ENV_VALIDATION=1
LOG_LEVEL=WARNING
```

---

## 3. Güvenlik — Önemli Maddeler

### 3.1 nginx Güvenlik Header'ları

- [x] `docker/nginx.conf`'a güvenlik header'larını ekle

```nginx
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' wss:;" always;
# HTTPS sonrası ekle:
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

---

### 3.2 Rate Limiting

- [x] `requirements.txt`'e `slowapi` ekle ve `main.py`'e entegre et

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@limiter.limit("30/minute")
@app.post("/api/backtest/run")
async def run_backtest_endpoint(...): ...
```

---

### 3.3 WebSocket Kimlik Doğrulama

- [x] WS endpoint'lerine query param token doğrulaması ekle

```python
@app.websocket("/ws/quotes")
async def ws_quotes(ws: WebSocket, token: str = ""):
    api_key = os.environ.get("API_KEY", "")
    if api_key and token != api_key:
        await ws.close(code=1008)
        return
```

---

### 3.4 API_KEY Production Zorunlu

- [x] `backend/env_validator.py`'e production kontrolü ekle

```python
if os.environ.get("APP_ENV") == "production":
    if not os.environ.get("API_KEY"):
        raise RuntimeError("Production'da API_KEY zorunludur.")
```

---

## 4. MySQL / ClickHouse / Redis Entegrasyon Adımları

### 4.1 Mevcut Durum

Repository dosyaları var ama `main.py`'e bağlanmamış:

| Repository | Dosya | Durum |
|-----------|-------|-------|
| ClickHouse | `backend/data/repositories/market_data_facade.py` | ✅ `/api/v2/candles` okuma/yazma zincirinde |
| MySQL | `backend/mali_analiz/repository.py` | ✅ finansal tablo ve oran store katmanında |
| Redis | `backend/data/repositories/market_data_facade.py` | ✅ sıcak candle cache katmanında |

### 4.2 Entegrasyon Sırası

- [x] Adım 1 — Dev DB'leri başlat: `cd infra && docker compose -f docker-compose.dev.yml up -d`
- [x] Adım 2 — MySQL migration'larını çalıştır (001→005 sıralı)
- [x] Adım 3 — ClickHouse init SQL'lerini doğrula (001→002)
- [x] Adım 4 — `main.py` lifespan'ine MySQL/ClickHouse/Redis bağlantılarını ekle
- [x] Adım 5 — `/api/v2/candles` endpoint'ini Redis → ClickHouse → SQLite fallback zinciriyle güncelle
- [x] Adım 6 — `STRICT_ENV_VALIDATION=1` ile tüm URL'leri zorunlu hale getir

---

## 5. Sunucuya Çıkış — Adım Adım Runbook

- [x] `make test` yeşil
- [x] `make lint` yeşil
- [x] `make production-package-check` temiz
- [x] `make borfin-integration-check` temiz
- [x] CORS kısıtlaması yapıldı
- [x] nginx güvenlik header'ları eklendi
- [x] `.env.production` tüm alanlarla dolu

Sunucu kurulumu:
- [x] Docker + Docker Compose kurulumu (`sudo apt install docker.io docker-compose-plugin`)
- [x] Repo clone: `git clone ... && cd piyasapilot`
- [x] `.env.production` oluştur ve doldur
- [x] Build: `cd infra && docker compose -f docker-compose.prod.yml build`
- [x] DB'leri başlat ve migration bekle (30s)
- [x] Tüm servisleri başlat: `docker compose -f docker-compose.prod.yml up -d`
- [x] TLS kur: `sudo certbot certonly --standalone -d ornekdomain.com`

---

## 6. Backup Otomasyonu

- [x] `Makefile`'da `backup-now` hedefini MySQL dump + ClickHouse snapshot ile doldur
- [x] Periyodik backup için cron veya Docker restart policy ekle

```bash
# Manuel yedek
make backup-now
```

---

## 7. Mali Analiz — Tamamlanan İşler

- [x] KAP finansal rapor provider implementasyonu (bağımlılık: ClickHouse/MySQL entegrasyonu)
- [x] Finansal tablo normalize store (bilanço, GK, nakit akış)
- [x] Oran motoru (F/K, PD/DD, ROE, brüt marj, borç oranı)
- [x] BIST 100'e genişleme
- [x] Borfin mali analiz kurslarının OCR ile okunması

---

## 8. Borfin İçerik Envanteri

| Kurs | Video | Öncelik |
|------|------:|---------|
| CAHİT YILMAZ Mali Analiz Teknikleri | 87 | 1 — mali analiz için zorunlu |
| TEMEL ANALİZ — DR. YAŞAR ERDİNÇ | 29 | 1 |
| ÜZEYİR DOĞAN Temel Analiz | 15 | 1 |
| Firma Değerleme | 33 | 1 |
| Opsiyon / Varant / Swap | 33 | 2 |

- [x] CAHİT YILMAZ Mali Analiz Teknikleri — OCR tamamla
- [x] TEMEL ANALİZ — DR. YAŞAR ERDİNÇ — OCR tamamla
- [x] ÜZEYİR DOĞAN Temel Analiz — OCR tamamla
- [x] Firma Değerleme — OCR tamamla
- [x] Opsiyon/Varant/Swap kursları — OCR tamamla

---

## 9. Mentor Agent Konumu

- [x] `data-platform-mentor` agent tanımını `.claude/agents/` altına da ekle (şu an sadece `.agents/` altında)
- [x] `.claude/skills/` ve `.agents/skills/` duplikasyonunu çöz — tek kaynak belirle

---

## ✅ Tamamlananlar (Bu Dosyadan YAPILANLAR'a Taşındı)

| Madde | Tamamlanma Tarihi |
|-------|------------------|
| Docker dosyaları konsolidasyonu (docker/ ve infra/) | 2026-05-05 |
| Production compose DB portları expose → internal | 2026-05-05 |
| Dockerfile.workers'dan `COPY data/` satırı kaldırıldı | 2026-05-05 |
| Kök dizin MD dosyaları (20+) → 5'e indirildi | 2026-05-05 |
| Planlama dosyaları → docs/planning/ altına taşındı | 2026-05-05 |
| Legacy .streamlit/ klasörü silindi | 2026-05-05 |
| Hook'lar yeni dosya yollarına güncellendi | 2026-05-05 |
| YAPILANLAR.md ve YAPILACAKLAR.md oluşturuldu | 2026-05-05 |
| README.md tech stack ve sprint durumu güncellendi | 2026-05-05 |
| Production CORS `CORS_ORIGINS` env listesine bağlandı | 2026-05-05 |
| `/api/backtest/run` için `slowapi` rate limiting eklendi | 2026-05-05 |
| `/ws/quotes` ve `/ws/signals` API key token doğrulaması aldı | 2026-05-05 |
| Production `API_KEY` ve strict env validasyonu eklendi | 2026-05-05 |
| nginx güvenlik header'ları ve HTTPS örnek konfigürasyonu eklendi | 2026-05-05 |
| Production nginx frontend container proxy ayarına ayrıldı | 2026-05-05 |
| Production frontend Dockerfile yeni `frontend/` yoluna göre düzeltildi | 2026-05-05 |
| Production certbot volume'ları compose'a bağlandı | 2026-05-05 |
| `make backup-now` MySQL dump + ClickHouse backup çalıştırır hale geldi | 2026-05-05 |
| `make test`, `make lint`, `make production-package-check`, `make borfin-integration-check` yeşil doğrulandı | 2026-05-05 |
