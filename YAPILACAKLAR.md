# PiyasaPilot — Yapılacaklar, Sunucu Çıkış ve Güvenlik Planı

> Tarih: 2026-05-05
> Blokör = yapılmadan sunucuya çıkılmaz. Önemli = çıkılır ama risk taşır.

---

## KURAL — Otonom Planlama Sistemi

> **Bu dosyayı her oturum sonunda güncelle.**

1. **Tik sistemi:** Her maddenin başında `- [ ]` (bekliyor) veya `- [x]` (tamamlandı) işareti var.
2. **Tamamlanınca:** İşareti `- [x]` yap ve maddeyi `YAPILANLAR.md`'nin ilgili bölümüne taşı.
3. **İlerleme tablosunu güncelle:** Aşağıdaki Bölüm 0'daki tabloda tamamlanan madde sayısını ve ağırlıklı % değerini güncelle.
4. **Kural ihlali:** Hiçbir madde `- [x]` yapılmadan YAPILANLAR'a taşınmaz; hiçbir madde buradan silinmez, sadece taşınır.

---

## 0. Genel İlerleme Tablosu

| Alan | Ağırlık | Tamamlanan | Kalan | % |
|------|--------:|:----------:|:-----:|--:|
| Dosya yapısı ve planlama sistemi | 5% | 5/5 | 0 | **100%** |
| Docker konsolidasyonu | 5% | 5/5 | 0 | **100%** |
| TLS / HTTPS | 15% | 0/4 | 4 | 0% |
| CORS production kısıtlaması | 10% | 0/1 | 1 | 0% |
| DB port güvenliği (prod) | 5% | 1/3 | 2 | 33% |
| nginx güvenlik header'ları | 8% | 0/1 | 1 | 0% |
| Rate limiting | 7% | 0/1 | 1 | 0% |
| WebSocket kimlik doğrulaması | 5% | 0/1 | 1 | 0% |
| API_KEY production zorunlu | 5% | 0/1 | 1 | 0% |
| MySQL / ClickHouse / Redis API entegrasyonu | 20% | 0/6 | 6 | 0% |
| Sunucuya çıkış (deploy runbook) | 5% | 0/7 | 7 | 0% |
| Backup otomasyonu | 3% | 0/2 | 2 | 0% |
| Mali Analiz gerçek veri | 5% | 0/5 | 5 | 0% |
| Borfin kursları (OCR) | 2% | 0/5 | 5 | 0% |
| **TOPLAM** | **100%** | | | **~10%** |

---

## 1. Gerçek Durum: Nerede Duruyoruz?

| Alan | Plan | Kod |
|------|------|-----|
| ClickHouse/MySQL/Redis infra dosyaları | ✅ Hazır | ✅ SQL şemalar, compose var |
| ClickHouse/MySQL/Redis API bağlantısı | ✅ Planlandı | ❌ Bağlanmadı |
| TLS / HTTPS | ✅ Planlandı | ❌ nginx HTTP-only |
| CORS production kısıtlaması | ✅ Planlandı | ❌ Hâlâ `["*"]` |
| Rate limiting | Planlanmadı | ❌ Yok |
| WebSocket auth | Planlanmadı | ❌ WS API key bypass ediyor |
| nginx güvenlik header'ları | Planlanmadı | ❌ Yok |
| Mali Analiz gerçek veri | ✅ Planlandı | ❌ Metadata-only |
| MySQL entegrasyonu (API) | ✅ Planlandı | ❌ Kod var, bağlı değil |
| Backup otomasyonu | ✅ Planlandı | ❌ `make backup-now` boş |
| DB portları prod compose | ✅ Planlandı | ✅ expose/internal (düzeltildi) |

---

## 2. Sunucuya Çıkış — Blokör Maddeler

### 2.1 TLS / HTTPS

- [ ] Sunucuda certbot kur (`sudo apt install certbot python3-certbot-nginx`)
- [ ] Domain için sertifika al (`sudo certbot certonly --standalone -d ornekdomain.com`)
- [ ] `docker/nginx.conf`'a HTTPS server block ekle (şablon aşağıda)
- [ ] `infra/docker-compose.prod.yml`'de certbot volume'larını aktifleştir

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

- [ ] `backend/api/main.py:369` satırını düzelt: `allow_origins=["*"]` → env'den oku

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

- [ ] `.env.production` dosyasını tüm alanlarla doldur

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

- [ ] `docker/nginx.conf`'a güvenlik header'larını ekle

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

- [ ] `requirements.txt`'e `slowapi` ekle ve `main.py`'e entegre et

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

- [ ] WS endpoint'lerine query param token doğrulaması ekle

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

- [ ] `backend/env_validator.py`'e production kontrolü ekle

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
| ClickHouse | `backend/data/repositories/clickhouse_repository.py` | Yazıldı ❌ bağlanmadı |
| MySQL | `backend/data/repositories/mysql_metadata_repository.py` | Yazıldı ❌ bağlanmadı |
| Redis | `backend/data/repositories/redis_market_cache.py` | Yazıldı ❌ bağlanmadı |

### 4.2 Entegrasyon Sırası

- [ ] Adım 1 — Dev DB'leri başlat: `cd infra && docker compose -f docker-compose.dev.yml up -d`
- [ ] Adım 2 — MySQL migration'larını çalıştır (001→004 sıralı)
- [ ] Adım 3 — ClickHouse init SQL'lerini doğrula (001→002)
- [ ] Adım 4 — `main.py` lifespan'ine MySQL/ClickHouse/Redis bağlantılarını ekle
- [ ] Adım 5 — `/api/v2/candles` endpoint'ini Redis → ClickHouse → SQLite fallback zinciriyle güncelle
- [ ] Adım 6 — `STRICT_ENV_VALIDATION=1` ile tüm URL'leri zorunlu hale getir

---

## 5. Sunucuya Çıkış — Adım Adım Runbook

- [ ] `make test` yeşil
- [ ] `make lint` yeşil
- [ ] `make production-package-check` temiz
- [ ] `make borfin-integration-check` temiz
- [ ] CORS kısıtlaması yapıldı
- [ ] nginx güvenlik header'ları eklendi
- [ ] `.env.production` tüm alanlarla dolu

Sunucu kurulumu:
- [ ] Docker + Docker Compose kurulumu (`sudo apt install docker.io docker-compose-plugin`)
- [ ] Repo clone: `git clone ... && cd piyasapilot`
- [ ] `.env.production` oluştur ve doldur
- [ ] Build: `cd infra && docker compose -f docker-compose.prod.yml build`
- [ ] DB'leri başlat ve migration bekle (30s)
- [ ] Tüm servisleri başlat: `docker compose -f docker-compose.prod.yml up -d`
- [ ] TLS kur: `sudo certbot certonly --standalone -d ornekdomain.com`

---

## 6. Backup Otomasyonu

- [ ] `Makefile`'da `backup-now` hedefini MySQL dump + ClickHouse snapshot ile doldur
- [ ] Periyodik backup için cron veya Docker restart policy ekle

```bash
# MySQL dump
docker compose -f infra/docker-compose.prod.yml exec mysql \
  mysqldump -u piyasapilot -p piyasapilot > backups/mysql_$(date +%Y%m%d).sql.gz
```

---

## 7. Mali Analiz — Kalan İşler

- [ ] KAP finansal rapor provider implementasyonu (bağımlılık: ClickHouse/MySQL entegrasyonu)
- [ ] Finansal tablo normalize store (bilanço, GK, nakit akış)
- [ ] Oran motoru (F/K, PD/DD, ROE, brüt marj, borç oranı)
- [ ] BIST 100'e genişleme
- [ ] Borfin mali analiz kurslarının OCR ile okunması

---

## 8. Borfin Kalan İçerikler

| Kurs | Video | Öncelik |
|------|------:|---------|
| CAHİT YILMAZ Mali Analiz Teknikleri | 87 | 1 — mali analiz için zorunlu |
| TEMEL ANALİZ — DR. YAŞAR ERDİNÇ | 29 | 1 |
| ÜZEYİR DOĞAN Temel Analiz | 15 | 1 |
| Firma Değerleme | 33 | 1 |
| Opsiyon / Varant / Swap | 33 | 2 |

- [ ] CAHİT YILMAZ Mali Analiz Teknikleri — OCR tamamla
- [ ] TEMEL ANALİZ — DR. YAŞAR ERDİNÇ — OCR tamamla
- [ ] ÜZEYİR DOĞAN Temel Analiz — OCR tamamla
- [ ] Firma Değerleme — OCR tamamla
- [ ] Opsiyon/Varant/Swap kursları — OCR tamamla

---

## 9. Mentor Agent Konumu

- [ ] `data-platform-mentor` agent tanımını `.claude/agents/` altına da ekle (şu an sadece `.agents/` altında)
- [ ] `.claude/skills/` ve `.agents/skills/` duplikasyonunu çöz — tek kaynak belirle

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
