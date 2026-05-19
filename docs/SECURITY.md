# PiyasaPilot — Güvenlik Denetim Raporu

> Tarih: 2026-05-19  
> Kapsam: Tüm codebase (backend, frontend, infra, docker, env)  
> Durum: Kritik bulgular düzeltildi; aşağıdaki orta/düşük bulgular için eylem adımları belirtildi.

---

## Özet

| Seviye   | Bulgu sayısı | Düzeltildi |
|----------|-------------|------------|
| KRİTİK   | 2           | 2 ✅       |
| YÜKSEK   | 3           | 3 ✅       |
| ORTA     | 5           | 3 ✅ / 2 ⚠️ |
| DÜŞÜK    | 3           | 1 ✅ / 2 ⚠️ |

---

## 1. KRİTİK

### C-1 — Varsayılan JWT Secret (jwt_utils.py)

**Dosya:** `backend/auth/jwt_utils.py`

```python
SECRET_KEY = os.environ.get("JWT_SECRET", "CHANGE_ME_IN_PRODUCTION_MIN_64_CHARS")
```

`JWT_SECRET` ortam değişkeni set edilmemişse tüm tokenlar tahmin edilebilir sabit bir key ile imzalanır. Bu durum saldırganın herhangi bir kullanıcının token'ını sahte olarak üretmesine izin verir.

**Düzeltme:** Uygulama başlangıcında `JWT_SECRET` yoksa `ValueError` fırlat.

```python
SECRET_KEY = os.environ.get("JWT_SECRET") or ""
if not SECRET_KEY:
    raise ValueError(
        "[FATAL] JWT_SECRET ortam değişkeni tanımlı değil. "
        "Üretim: openssl rand -hex 64"
    )
```

**Durum:** ✅ `backend/auth/jwt_utils.py` düzeltildi (bu rapor oluşturulurken).

---

### C-2 — XSS: SettingsPage user_agent / ip_address (innerHTML)

**Dosya:** `frontend/src/pages/SettingsPage.ts`, satır 57

```typescript
list.innerHTML = (body.data?.sessions || []).map((s) =>
  `<div>${s.user_agent || '...'}<small>${s.ip_address || ''}</small></div>`
).join('');
```

`user_agent` ve `ip_address` sunucudan gelen ham string değerlerdir. Kötü niyetli bir kullanıcı özel bir User-Agent string'i ile oturum açarsa (`<img src=x onerror=alert(1)>` gibi) ve başka bir admin bu sayfayı açarsa XSS tetiklenir.

**Düzeltme:** Her iki değer de `esc()` yardımcısından geçirilmeli.

**Durum:** ✅ `frontend/src/pages/SettingsPage.ts` düzeltildi (bu rapor oluşturulurken).

---

## 2. YÜKSEK

### H-1 — API Şeması Production'da Açık (/docs, /redoc, /openapi.json)

**Dosya:** `backend/middleware/api_key_auth.py`, satır 23

```python
EXEMPT_PATHS = frozenset({"/api/health", "/docs", "/openapi.json", "/redoc"})
```

`/docs` ve `/redoc` endpointleri API key doğrulamasından muaf. Bu durum tüm endpoint listesini, parametre şemalarını ve model yapılarını yetkisiz kişilere ifşa eder.

**Düzeltme:** Production'da (`APP_ENV=production`) bu yolları muafiyet listesinden çıkar. nginx seviyesinde de `/docs` ve `/redoc`'u 403 ile engelle.

**Durum:** ✅ `backend/middleware/api_key_auth.py` düzeltildi — `APP_ENV` kontrolü eklendi.

---

### H-2 — Eksik Content-Security-Policy (nginx)

**Dosya:** `docker/nginx.prod.conf`

Mevcut güvenlik headerları:
- `X-Frame-Options: SAMEORIGIN` ✅
- `X-Content-Type-Options: nosniff` ✅
- `Strict-Transport-Security` ✅

**Eksik:** `Content-Security-Policy` başlığı yok. Bu durum XSS saldırılarının etkisini önemli ölçüde artırır.

**Düzeltme:** nginx.prod.conf'a eklenecek CSP:
```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' wss://$host; frame-ancestors 'none';" always;
```

**Durum:** ✅ `docker/nginx.prod.conf` düzeltildi.

---

### H-3 — Timing Attack: API Key Karşılaştırması

**Dosya:** `backend/middleware/api_key_auth.py`, satır 52  
**Dosya:** `backend/api/main.py`, satır 129 (`_require_ws_token`)

```python
if provided_key != api_key:          # sabit-zaman değil
    ...
token == api_key                     # WS için de aynı sorun
```

`!=` ve `==` operatörleri ilk farklı karakter bulunduğunda durur. Yanıt süresi ölçülerek API key tahmin edilebilir (timing attack).

**Düzeltme:** `hmac.compare_digest` kullan.

```python
import hmac
if not hmac.compare_digest(provided_key, api_key):
    ...
```

**Durum:** ✅ Her iki dosyada da düzeltildi.

---

## 3. ORTA

### M-1 — Cookie SameSite=Lax (CSRF Riski)

**Dosya:** `backend/auth/cookie_utils.py`

```python
response.set_cookie(..., samesite="lax")
```

`samesite="lax"` CSRF saldırılarına karşı kısmi koruma sağlar; GET isteklerinden gelen cross-site çerezlere izin verir. `strict` değeri daha güvenlidir.

**Öneri:** Auth tokenları için `samesite="strict"` kullan. Frontend'de cross-site navigasyon gerekliyse OAuth redirect flow ayrıca değerlendirilmeli.

**Durum:** ⚠️ Değiştirilmedi — Google OAuth yönlendirme akışı `strict` cookie'yi engelleyebileceğinden dikkatli inceleme gerekir. Teknik borç olarak kayıt altına alındı.

---

### M-2 — nginx Seviyesinde Rate Limiting Yok

**Dosya:** `docker/nginx.prod.conf`

slowapi backend tarafında rate limiting sağlıyor (`/api/backtest`, `/api/screener` vb.) ancak nginx seviyesinde hiçbir limit yok. Bu durum uygulamayı:
- Login endpoint brute-force saldırılarına
- Aşırı WebSocket bağlantısı oluşturma saldırılarına

karşı savunmasız bırakır.

**Düzeltme:**
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;
limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;

location /api/auth/ {
    limit_req zone=auth burst=10 nodelay;
    ...
}
location /api/ {
    limit_req zone=api burst=20 nodelay;
    ...
}
```

**Durum:** ✅ `docker/nginx.prod.conf`'a eklendi.

---

### M-3 — /status Endpointi Herkese Açık

**Dosya:** `docker/nginx.prod.conf`

nginx'in `/status` (stub_status) sayfası public'e açık. Worker sayısı, aktif bağlantı vs. bilgiler saldırgana keşif için yardımcı olur.

**Düzeltme:**
```nginx
location /status {
    stub_status;
    allow 127.0.0.1;
    deny all;
}
```

**Durum:** ✅ Düzeltildi.

---

### M-4 — WebSocket Token: URL Query Parametresi

**Dosya:** `backend/api/main.py`, `_require_ws_token()`

```python
token = ws.query_params.get("token", "")
return token == api_key
```

API key URL query string'inde gönderiliyor (`?token=...`). Bu değer:
- Server loglarında görünür
- Browser geçmişinde kalır
- Referrer header'ında sızabilir

**Öneri:** WebSocket'te token gönderimi için `Sec-WebSocket-Protocol` header'ı veya bağlantı sonrası ilk mesaj authentication pattern'ı kullanılmalı. Kısa vadeli önlem olarak nginx log formatında query string maskelenebilir.

**Durum:** ⚠️ Değiştirilmedi — WS protokol değişikliği frontend yeniden yazımı gerektirir. Teknik borç.

---

### M-5 — MaliAnalizPanel Hata Mesajları innerHTML'de

**Dosya:** `frontend/src/components/MaliAnalizPanel.ts`, birden fazla satır

```typescript
this.bodyEl.innerHTML = `<div class="ma-error">Özet yüklenemedi: ${e}</div>`;
```

`${e}` yakalanmış JavaScript hata nesnesidir. `Error.message` genellikle güvenlidir ancak bazı sunucu yanıtlarından gelen mesajlar `<script>` içerebilir.

**Düzeltme:** Hata mesajlarını `textContent` ile yaz veya `esc()` kullan.

**Durum:** ✅ Düzeltildi.

---

## 4. DÜŞÜK

### L-1 — Redis Şifre Koruması Yok

**Dosya:** `infra/docker-compose.prod.yml`

Redis container'ı şifresiz çalışıyor. Yalnızca iç Docker network'ten erişilebilir (port dışa açılmıyor) bu nedenle risk düşük; ancak "defense in depth" ilkesi gereği şifre eklenmeli.

**Düzeltme:**
```yaml
redis:
  command: redis-server --requirepass ${REDIS_PASSWORD:?}
```

`.env.production`'a `REDIS_PASSWORD` ekle; `REDIS_URL`'i güncelle.

**Durum:** ⚠️ Değiştirilmedi — `REDIS_URL` değişikliği tüm servisleri etkiler; ayrı sprint olarak planlandı.

---

### L-2 — Sentry send_default_pii=False ✅

**Dosya:** `backend/api/main.py`

```python
sentry_sdk.init(..., send_default_pii=False)
```

PII (kişisel tanımlayıcı bilgi) Sentry'ye gönderilmiyor. ✅ Mevcut durum doğru.

---

### L-3 — Docker Compose: Veritabanları Dışa Expose Edilmiyor ✅

**Dosya:** `infra/docker-compose.prod.yml`

MySQL, ClickHouse ve Redis `expose` kullanıyor (`ports` değil). Bu portlar host'a bağlanmıyor, yalnızca iç Docker network'ten erişilebilir. ✅ Doğru yapılandırma.

---

## 5. Pozitif Bulgular (İyi Yapılmış)

| Alan | Durum |
|------|-------|
| Argon2id parola hashleme (time=2, mem=64MB) | ✅ |
| JTI tabanlı token iptal (Redis blocklist) | ✅ |
| HttpOnly + Secure çerez (production) | ✅ |
| HSTS (max-age=31536000, includeSubDomains) | ✅ |
| TLS 1.2/1.3 — zayıf cipher'lar devre dışı | ✅ |
| Tüm SQL sorguları parameterized (SQL injection yok) | ✅ |
| Docker: sadece 80/443 dışarı açık | ✅ |
| Sentry PII gönderimi kapalı | ✅ |
| CORS env tabanlı, wildcard `*` yok | ✅ |
| Ortak şifre blocklist (password.py) | ✅ |
| Stripe webhook signature doğrulaması | ✅ |

---

## 6. Canlıya Almadan Önce Zorunlu Eylemler

Aşağıdaki adımlar tamamlanmadan production'a çıkılmamalıdır:

1. **`JWT_SECRET`** — `openssl rand -hex 64` ile üret, `.env.production`'a ekle.  
2. **`API_KEY`** — `openssl rand -hex 32` ile üret, `.env.production`'a ekle.  
3. **Tüm `BURAYA_YAZ` değişkenleri** doldurulmalı: `grep "BURAYA_YAZ" .env.production`  
4. **Sentry DSN** — production environment tag'i ile yapılandır.  
5. **Stripe webhook secret** — production endpoint URL'i Stripe Dashboard'a tanımla.

---

## 7. Önerilen İzleme

- Login başarısız denemelerini Redis counter'da say; 5 başarısız giriş → geçici IP engeli (15 dk).
- `/api/backtest` ve `/api/screener` endpoint'leri için slowapi limit loglarını Sentry'ye yönlendir.
- nginx access log'unu `combined` formatında tut; 4xx/5xx oranı %5'i geçerse alarm.
- MySQL kullanıcısı yalnızca gerekli tablolara erişmeli (`GRANT SELECT, INSERT, UPDATE, DELETE ON metadata.* TO 'appuser'@'%'` — root yetkisi olmamalı).

---

*Bu rapor PiyasaPilot v1.0 canlıya alma öncesi güvenlik denetimi kapsamında hazırlanmıştır.*
