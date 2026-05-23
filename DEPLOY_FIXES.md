# 🔧 Hata Analizi & Deploy Rehberi

## Tespit Edilen Sorunlar ve Kök Nedenleri

### 1. ❌ /login ve /register → 404 Not Found
**Kök Neden:** Production container'lar eski image üzerinden çalışıyor.  
`nginx-frontend.conf` içinde `try_files $uri $uri/ /index.html;` kuralı **kodda mevcut ve doğru**, ancak eski container build'inde yoktu.  
**Çözüm:** Container'ları yeniden build et (aşağıya bak).

### 2. ❌ Grafik → "Bağlantı Hatası: backend HTTP 401"
**Kök Neden:** Eski backend container, `APIKeyMiddleware`'in `/api/*` bypass'ını içermiyor.  
`docker-compose.prod.yml` zaten `API_KEY_PROTECTED_PATHS: /metrics` override'ı yapıyor — ama container yeniden build edilmediği için ESKİ middleware kodu çalışıyor.  
**Çözüm:** Backend container'ı yeniden build et.

### 3. ⚠️ Topbar — tab butonları sıkışık
**Kök Neden:** CSS'de `tab-btn` padding çok genişti (14px her taraf), 8 tab + sağ taraf öğeleri topbar'a sığmıyordu.  
**Çözüm:** ✅ Bu seans içinde CSS'de düzeltildi.

---

## Bu Seansta Yapılan Kod Değişiklikleri

| Dosya | Ne Değişti |
|---|---|
| `frontend/style.css` | Tab buton padding 14px→9px, gap 8px→5px, font 13px→12px; topbar padding/gap azaltıldı; logo 16px→15px |
| `frontend/vite.config.ts` | `emptyOutDir: false` → `true` (eski build dosyaları birikiyordu) |
| `backend/api/main.py` | CORS'a `allow_credentials=True` ve `PUT/DELETE` metodları eklendi |

---

## 🚀 Production'a Deploy Komutu

```bash
cd /path/to/project/infra

# Tüm container'ları cache olmadan yeniden build et ve başlat
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Logları izle
docker-compose -f docker-compose.prod.yml logs -f api frontend nginx
```

> **Not:** `--no-cache` şart — aksi halde Docker eski layer'ları kullanır ve hatalar devam eder.

---

## Kontrol Listesi (Build Sonrası)

- [ ] `https://piyasapilotu.com/login` → Login sayfası açılıyor mu?
- [ ] `https://piyasapilotu.com/register` → Kayıt sayfası açılıyor mu?
- [ ] Ana terminal → "Bağlantı Hatası" gitmiş mi, grafik yükleniyor mu?
- [ ] Topbar sekmeleri daha ferah görünüyor mu?
