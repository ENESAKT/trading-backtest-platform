# PLANLAMA — PiyasaPilot Trading Terminali (Ana Index)

> Bu dosya index'tir. Sıra ve öncelik için önce `genelplanlama.md`, kodlama için ilgili alt plan dosyasını oku.
> Tarih: 2026-05-03 · Branch: codex/financials-ui-api-v1

---

## 0. Canlı Hata Denetimi — 2026-05-19

> Kaynak: Chrome canlı QA + repo/deploy dosya kontrolü.
> İncelenen canlı yüzeyler: `https://piyasapilotu.com`, `https://www.piyasapilotu.com/?tab=chart&symbol=BTCUSDT`, `/login`, sekme geçişleri, sembol arama/değiştirme, haberler.
> İlgili commit notu: `84ad71a fix: production kritik hatalar — domain, CORS, cookie ve SSL düzeltmeleri`.
> 2026-05-19 uygulama durumu: canonical domain `piyasapilotu.com` olarak kilitlendi; production SPA fallback, browser/API auth ayrımı, rate limit, URL sync, certbot reload ve eksik canlı çıkış plan dosyası kod/doküman tarafında düzeltildi. Canlı sunucuya deploy edilen commit/image bu çalışma alanından doğrulanamadığı için canlı kabul testi deploy sonrası tekrar koşulacak.

### 0.1 Önceden Tespit Edilip 84ad71a ile Düzeltilen/Kısmen Düzeltilenler

- [x] Domain tutarsızlığı için `docker/nginx.prod.conf`, `docker/nginx.bootstrap.conf`, `.env.production.example` içinde `piyasapilotu.com` yönüne düzeltme yapılmış.
- [x] Cookie auth için `backend/api/main.py` CORS ayarına `allow_credentials=True` eklenmiş.
- [x] Admin paneli ve auth akışları için `allow_methods` listesine `PUT`, `PATCH`, `DELETE` eklenmiş.
- [x] `COOKIE_DOMAIN=piyasapilotu.com` `.env.production.example` içine eklenmiş.
- [x] Nginx container healthcheck HTTPS yerine container içi HTTP `/api/health` kontrolüne alınmış.
- [x] `certbot` servisi `infra/docker-compose.prod.yml` içine eklenmiş.
- [x] `docker/Dockerfile.api` içine `--proxy-headers --forwarded-allow-ips=*` eklenmiş.

### 0.2 Chrome Canlı QA Bulguları

#### P0 — Canlı Ürün Bloklayıcılar

- [x] **Yeni canonical domain canlıda sağlıklı açılmıyor.**
  - Chrome ile `https://piyasapilotu.com` açıldığında `ERR_BLOCKED_BY_CLIENT` görüldü.
  - Buna karşılık çalışan terminal sekmeleri hâlâ `https://www.piyasapilotu.com/?tab=chart&symbol=BTCUSDT` üzerinde.
  - Repo tarafında nginx/env yeni `piyasapilotu.com` derken, canlı yüzey ve birçok kaynak hâlâ `piyasapilotu.com` kullanıyor. Bu haliyle kullanıcı, arama motoru, OAuth, Stripe ve cookie domainleri aynı gerçeğe bakmıyor.
  - Durum: repo ve statik/doküman referansları `piyasapilotu.com` yönüne süpürüldü; canlı DNS/deploy görüntüsü deploy sonrası doğrulanacak.

- [x] **Frontend üretim container'ı SPA route fallback vermiyor; `/login` ve benzeri public route'lar 404.**
  - Chrome'da `https://www.piyasapilotu.com/login` sonucu: `404 Not Found nginx/1.31.0`.
  - Kök neden: `docker/Dockerfile.frontend` sadece `dist` kopyalıyor ve nginx default config ile çalışıyor; `docker/nginx-frontend.conf` içindeki `try_files $uri $uri/ /index.html;` production image'a kopyalanmıyor.
  - Etki: `Giriş Yap`, `Ücretsiz Kayıt`, `Planlar`, `Ayarlar`, email verification/reset linkleri ve doğrudan paylaşılan public route'lar kırılıyor.
  - Durum: production frontend image artık `docker/nginx-frontend.conf` kopyalıyor.

- [x] **Tarayıcıdan gelen API istekleri `APIKeyMiddleware` yüzünden 401/429'a düşüyor.**
  - Grafik açılışında canlı hata: `Bağlantı Hatası: backend HTTP 401`, tekrar denemelerde `backend HTTP 429`.
  - Console uyarıları: `Favori fiyatı yüklenemedi: VAKBN.IS/AKBNK.IS/ASELS.IS/ARCLK.IS/THYAO.IS`.
  - Kök neden: `backend/middleware/api_key_auth.py`, `API_KEY` varsa tüm `/api/*` ve `/metrics` isteklerinde `X-API-Key` istiyor. Frontend `fetch('/api/v2/candles')`, `fetch('/api/news')`, `fetch('/api/auth/login')` gibi çağrılarda bu header'ı göndermiyor. Browser'a gerçek `API_KEY` koymak güvenli değil.
  - Etki: grafik verisi, favori fiyatları, haberler, auth/login/register ve plan limitleri canlıda güvenilir çalışmaz.
  - Durum: `API_KEY` artık varsayılan olarak yalnızca `API_KEY_PROTECTED_PATHS=/metrics` için zorunlu; browser-facing `/api/*` JWT/cookie/feature gate kontratına bırakıldı.

- [x] **Nginx rate limit canlı kullanım için çok düşük/yanlış katmanda tetikleniyor.**
  - `/api/` için `60r/m`, `burst=30`; frontend ilk yüklemede auth/me, news badge, favori fiyatları, ana grafik, sinyal/notifier durumları gibi çok sayıda istek atıyor.
  - API key 401 döngüsüyle birleşince kullanıcı birkaç denemede `HTTP 429` görüyor.
  - Etki: gerçek hata 401 iken kullanıcı 429 görmeye başlıyor; hata ayıklama ve UX karışıyor.
  - Durum: genel API limiti ve burst canlı ilk yüklemeyi kaldıracak şekilde yükseltildi; auth limiti ayrı ve daha sıkı kaldı.

#### P1 — Kritik UX ve State Hataları

- [x] **Grafik ilk açılışta boş kalıyor.**
  - Görsel durum: üstte `BAĞLANTI YOK`, chart alanında `Bağlantı hatası`, `Bağlantı Hatası: backend HTTP 401/429`, `Yeniden Dene`.
  - Etki: ana ürün vaadi olan terminal/grafik canlıda ilk ekranda kullanılamıyor.
  - Durum: 401/429 üreten API key/rate limit kökü kod tarafında düzeltildi; canlı veri cevabı deploy sonrası doğrulanacak.

- [x] **Haberler sekmesi canlıda yüklenemiyor.**
  - Chrome'da `Haberler` sekmesi: `Haberler yüklenemedi`, `Beklenmedik bir hata oluştu (HTTP 429)`.
  - Muhtemel kök neden: aynı API key/rate limit sorunu; backend auth/plan gate ile frontend guest gösterimi ayrıca hizalanmalı.
  - Durum: aynı 401/429 kökü giderildi; Chrome QA'da tekrar kontrol edilecek.

- [x] **Sembol değişince UI güncelleniyor ama URL stale kalıyor.**
  - `THYAO` seçildikten sonra UI başlığı `Türk Hava Yolları (THYAO.IS)` ve select değeri `THYAO.IS` oldu.
  - URL hâlâ `?tab=chart&symbol=BTCUSDT` kaldı.
  - Kök neden adayı: `openSymbol()` sonrası `history.replaceState` çağrısı yok; URL sync yalnızca `showTab()` içinde yapılıyor.
  - Etki: refresh/deep-link/paylaşım eski sembole döner.
  - Durum: `openSymbol()`, tab geçişi ve timeframe değişimi tek `syncUrlState()` helper'ına bağlandı.

- [x] **Kilitli sekmelerde plan gate modalı açılıyor ama modal aksiyonları kırık route'a gidiyor.**
  - Portföy/Tarama/Mali Analiz için kayıt/plan modalı görünüyor.
  - Modal içindeki `Ücretsiz Kayıt Ol` route'u production fallback hatası yüzünden `/register` 404'e düşer.
  - Durum: production fallback düzeltildi; route davranışı Chrome QA ile kontrol edilecek.

- [x] **Zaman dilimi butonları hata durumunda güvenilir state göstermiyor.**
  - `1D`, `5D`, `1H` tıklamalarından sonra aktif buton `1G` kaldı ve chart yine backend hata durumunda kaldı.
  - API düzeltildikten sonra ayrıca doğrulanmalı; şu an veri yükleme hatası gerçek timeframe davranışını maskeleyebilir.
  - Durum: timeframe değeri URL/data engine ile senkronlanıyor; canlı veriyle son kontrol Chrome QA'da yapılacak.

#### P2 — Güvenilirlik/Doküman Borçları

- [x] **Eski domain referansları çok yaygın.**
  - Kod ve statik dosyalarda hâlâ `piyasapilotu.com` geçen kritik yerler var: `frontend/index.html`, `frontend/public/robots.txt`, `frontend/public/sitemap.xml`, `backend/api/auth_router.py`, `backend/api/billing_router.py`, `backend/payments/stripe_service.py`, `backend/auth/email_sender.py`, `backend/auth/google_oauth.py`, `scripts/check_deployment_readiness.py`, `scripts/load_test.js`, `mobile/...`, `docs/DEPLOYMENT.md`, `CANLIYA_ALMA_REHBERI.md`, `YAPILACAKLAR.md`.
  - Etki: SEO canonical, sitemap, email linkleri, Google OAuth redirect URI, Stripe callback ve mobil build birbirinden kopabilir.
  - Durum: aktif kod, public asset, script, mobile README ve deployment doküman referansları `piyasapilotu.com` yönüne güncellendi; eski domain yalnızca geçmiş bulgu notlarında tutuluyor.

- [x] **`docs/DEPLOYMENT.md` hâlâ eski domainle TLS komutu gösteriyor.**
  - `DOMAIN=piyasapilotu.com EMAIL=admin@piyasapilotu.com bash scripts/deployment/setup_tls.sh`.
  - Yeni domain kararı kesinleşmeden bu rehberle deploy yapmak tekrar yanlış sertifika/domain üretebilir.
  - Durum: deployment rehberi ve ilgili script notları `piyasapilotu.com` yönüne güncellendi.

- [x] **Certbot yenileme var ama nginx reload/deploy hook net değil.**
  - `certbot renew` 12 saatte bir çalışır; fakat sertifika yenilendikten sonra nginx'in yeni sertifikayı ne zaman okuyacağı belirtilmemiş.
  - Kabul kriteri: yenileme sonrası nginx reload mekanizması netleştirilmeli.
  - Durum: production nginx container'ı periyodik reload yapacak şekilde ayarlandı.

- [x] **`planlama-temizlik-canliya-cikis.md` ana planlarda referanslı ama repo içinde bulunamadı.**
  - `docs/planning/genelplanlama.md` ve bu index dosyası bu dosyayı aktif plan olarak gösteriyor.
  - Etki: yeni oturum/agent yanlış veya eksik plan dosyasına yönlenir.
  - Durum: `docs/planning/planlama-temizlik-canliya-cikis.md` oluşturuldu.

- [ ] **`.env.production` artık git dışı olmalı ama deploy süreci bunu güvenli üretmeli.**
  - Çalışma ağacında `.env.production` silinmiş/staged görünüyor; `.gitignore` içinde ignore edilmiş.
  - Bu doğru yönde olabilir, fakat sunucuda `.env.production` dosyasının nasıl yaratıldığı ve doğrulandığı runbook'ta kesin olmalı.

### 0.3 Yerel Doğrulama

- [x] `frontend` typecheck çalıştı: `npm run typecheck` başarılı.
- [x] `frontend` production build çalıştı: `npm run build` başarılı.
- [x] Security unit testi sanal ortamla çalıştı: `.venv/bin/python -m pytest tests/unit/test_security.py -q` → `14 passed`.
- [x] Yerel Chrome QA çalıştı: grafik `HTTP 401/429` göstermeden açıldı, `/login` `/register` `/pricing` `/settings` `/legal/privacy` route'ları 404 vermedi, `THYAO.IS` sembolü URL'de korundu, Haberler auth state'i `Giriş gerekli` olarak göründü, kilitli tab modalı `/register` linki verdi, arka planda Backtest modalı açılmadı, timeframe trigger etiketi aktif timeframe ile güncellendi.
- [x] Deployment compose config doğrulandı: `API_KEY_PROTECTED_PATHS=/metrics` ve `REQUIRE_WS_API_KEY=0` API/worker container ortamına taşınıyor.
- [ ] Global `python` ve sistem `python3` ortamı pytest için hazır değil: `python` yok, sistem `python3` içinde `pytest` yok. Test komutlarında `.venv/bin/python` standardize edilmeli.

### 0.4 Yapılacaklar — Uygulama Sırası

1. [x] **Canonical domain kararını kilitle.**
   - Ya tüm proje `piyasapilotu.com` olacak ya da `piyasapilotu.com` kalacak; ikisi birden dağınık kullanılmayacak.
   - DNS, nginx `server_name`, cert path, `.env.production`, OAuth, Stripe, email, sitemap, robots, mobil build ve dokümanlar aynı domaini göstermeli.

2. [ ] **Canlıya gerçekten hangi commitin deploy edildiğini doğrula.**
   - Sunucuda çalışan image tag/commit hash görülmeli.
   - `84ad71a` canlıda yoksa önce rebuild + redeploy yapılmalı; varsa aşağıdaki kök sorunlar düzeltilmeli.
   - Durum: bu çalışma alanından sunucu image/commit bilgisi okunamadı; deploy yetkisi olan ortamda doğrulanacak.

3. [x] **Frontend production nginx fallback düzelt.**
   - `docker/Dockerfile.frontend` içine `COPY docker/nginx-frontend.conf /etc/nginx/conf.d/default.conf` benzeri adım ekle.
   - Kabul: `/login`, `/register`, `/pricing`, `/settings`, `/legal/privacy`, `/payment/success`, `/shared/...` hard refresh ile 200 dönmeli ve SPA ilgili sayfayı render etmeli.

4. [x] **Browser-facing API auth modelini yeniden ayır.**
   - `X-API-Key` browser'a konmayacak.
   - `APIKeyMiddleware` yalnızca server-to-server/internal endpointler için kullanılacak veya public/auth/browser endpointleri muaf tutulacak.
   - `/api/auth/*` login/register/refresh/me, public market data kararı verilen `/api/v2/candles`, haber/plan limit endpointleri ve protected endpointlerin JWT cookie/role guard kontratı ayrı ayrı yazılacak.
   - Kabul: misafir kullanıcıda grafik ya bilinçli public veri döndürür ya da plan gate gösterir; 401/429 boş grafik üretmez.

5. [x] **Rate limitleri canlı davranışa göre yeniden düzenle.**
   - Auth için sıkı limit kalsın; market/news gibi çok çağrılan endpointler cache ve kullanıcı/session bazlı ayrı limit alsın.
   - Frontend ilk yüklemede favori fiyatlarını batch/debounce etmeli.
   - Kabul: ilk sayfa yüklemesi ve 5 sembol favori 429 üretmemeli.

6. [x] **Domain sweep yap.**
   - `rg "piyasapilotu|piyasapilot\\.com"` çıktısı kategori kategori temizlenecek.
   - Kod defaultları, public assets, docs, scripts ve mobile ayrı commitlerle güncellenecek.
   - Kabul: bilinçli yönlendirme notları hariç eski domain kalmayacak.

7. [x] **URL state sync düzelt.**
   - `openSymbol()` sonunda aktif tab/sembol/timeframe URL sync tek helper'a alınmalı.
   - Kabul: `THYAO` seçince URL `symbol=THYAO.IS` olur; refresh aynı sembolle açılır.

8. [x] **Haberler, Mali Analiz, Portföy, Strateji ve Tarama için gate/backend uyumunu doğrula.**
   - Frontend plan gate ile backend auth/feature gate aynı kuralları kullanmalı.
   - Kabul: kilitli feature tıklanınca modal çıkar; kayıt butonu çalışan `/register` sayfasına gider; backend aynı feature için beklenen 401/403/200 verir.
   - Durum: Chrome QA'da Haberler misafir state'i açık auth mesajı verdi; kilitli Strateji tabı modal açtı ve `/register` route'u 404 vermedi; arka planda veri güncellemesi artık Backtest modalı açmıyor.

9. [x] **Deployment rehberlerini güncelle.**
   - `docs/DEPLOYMENT.md`, `CANLIYA_ALMA_REHBERI.md`, `scripts/check_deployment_readiness.py`, `infra/aws/README.md` domain ve komutları canonical karara göre düzeltilecek.
   - Eksik `planlama-temizlik-canliya-cikis.md` referansı ya geri getirilecek ya da güncel dosya adına taşınacak.

10. [ ] **Canlı kabul testi yapılacak.**
    - Chrome temiz profilde ve normal profilde:
      - `https://<canonical-domain>/`
      - `/login`, `/register`, `/pricing`
      - BTCUSDT grafik, THYAO grafik, timeframe değişimi
      - Haberler sekmesi
      - locked tab modal + kayıt yönlenmesi
      - mobil viewport ana akış
    - Komutlar:
      - `frontend`: `npm run typecheck`, `npm run build`
      - backend: `.venv/bin/python -m pytest tests/unit/test_security.py -q`
    - deployment: canonical domain için health, TLS, redirect ve route fallback kontrolü.
   - Durum: yerel Chrome kabul testi geçti; canlı domain üzerinde image/commit deploy edildikten sonra aynı liste tekrar koşulacak.

---

## 1. Proje Özeti

`/Users/enes/AgentWorkspace/Backtest` — Python backend (`quant_engine/`, `backend/`) ve TypeScript/Vite SPA (`piyasapilot-v2/`) içeren trading terminali.

**Hedef:** TradingView benzeri tek SPA; strateji fikri → kural → backtest → optimizasyon → paper robot zincirini tek ekranda yöneten algoritmik trade laboratuvarı.

**Durum (2026-05-03):** Veri platformu, repo temizliği/canlıya çıkış hazırlığı, denetim skill/script katmanı, Eğitimler, Grafik Lab G1-G10 ve Backtest Lab B1-B13 ürün entegrasyonu tamamlandı. Mali Analiz tarafında metadata-only API/UI v1, universe sidebar ve boş kontratlar hazır; gerçek KAP/provider bağlantısı ve finansal tablo store'u henüz bağlanmadı.

---

## 2. Çalışan Servisler

| Servis | Port | Dosya |
|--------|------|-------|
| FastAPI gateway | 8000 | `backend/api/main.py` |
| Frontend SPA | 5173 | `piyasapilot-v2/` |
| Veri workers | — | `backend/workers/` |
| Paper executor | — | `backend/paper/` |
| Notifier | — | `backend/notifier/` |
| Gelecek ClickHouse | 8123/9000 | `infra/clickhouse/` |
| Gelecek MySQL | 3306 | `infra/mysql/` |
| Gelecek Redis | 6379 | `infra/docker-compose.*.yml` |

**Dokunma listesi:** `quant_engine/backtest/engine.py`, `quant_engine/data/providers/binance_provider.py`, `quant_engine/data/providers/yfinance_provider.py`, `quant_engine/data/live_feed.py`

---

## 3. Enes'in Kesin Kararları

- [x] Frontend: TS terminali ana arayüz (Streamlit Sprint 2.8'de söküldü)
- [x] Backend rolling cache: SQLite/Parquet, kayar pencere
- [x] Sembol kapsamı: BIST 100 + 20 kripto + FX/emtia (~130 sembol)
- [x] Always-on: Docker Compose (lokal Mac, taşınabilir)
- [x] Backtest motoru: Python BacktestEngine tek kaynak; TS sadece görüntüler
- [x] AI sinyal: kural motoru (8 tip) + Claude API sabah brifing + LightGBM (≥3 ay cache)
- [x] Paper trading: strateji-bazlı izole sandık (10.000 TL), günlük %5 DD limiti
- [x] Bildirim: Telegram + Email + In-app + macOS desktop
- [x] Gerçek emir gönderimi kapsam dışı
- [x] Eğitim içerikleri: telifsiz, PiyasaPilot'a özgü iş akışına dönüştürülecek
- [x] Yeni veri hedefi: önce BIST 100 + VIOP; sonra tüm BIST; sonra diğer piyasalar
- [x] Production veri omurgası: ClickHouse + MySQL + Redis
- [x] BIST hisse `1m` veri yalnızca son 1 yıl tutulacak
- [x] VIOP `1m` veri 10 yıl hedefleyecek
- [x] BIST hisse `5m` ve üstü timeframe'ler 10 yıl hedefleyecek
- [x] Günlükten dakikalık sahte veri üretilmeyecek
- [x] Borfin OCR/frame/video artifact'leri production paketine girmeyecek
- [x] Veri/deploy/repo temizliği için kontrol skill'leri ve mentor agent planlanacak

---

## 4. Mimari (Tek Cümle Özetler)

- **Mevcut Veri:** Worker → SpikeFilter → SQLite/Parquet cache → FastAPI → REST/WS → TS DataEngine → ChartPanel
- **Hedef Veri:** Provider/Ingestor → Validate/Quality → ClickHouse `market_bars` → Repository → API/Backtest/Screener; MySQL metadata/job/inventory, Redis quote/cache/lock/pub-sub
- **Backtest:** StrategyPanel → POST /api/backtest/run → BacktestEngine → sonuç → Chart.js
- **Sinyal:** Bar kapanışı → DecisionEngine → /ws/signals → SignalFeed + Notifier
- **Paper:** /ws/signals → PaperExecutor → SQLite → PnL → PortfolioPanel
- **Production:** nginx → frontend/API/WS; Docker Compose prod → api/ingestor/scheduler/clickhouse/mysql/redis/backup

---

## 5. Dosya Haritası

| Dosya | İçerik |
|-------|--------|
| `YAPILANLAR.md` | Teknik envanter — tüm yapılanlar, modüller, teknolojiler |
| `YAPILACAKLAR.md` | Kalan işler, sunucu çıkış, güvenlik, MySQL entegrasyon adımları |
| `genelplanlama.md` | Tek yürütme haritası ve uygulama sırası |
| `planlama.md` | Bu index |
| `planlama-sprint-gecmis.md` | Sprint 0–12 arşiv (tamamlananlar, referans) |
| `planlama-sprint-aktif.md` | Aktif geliştirme fazları ve sıraları |
| `planlama-veri-platformu.md` | BIST/VIOP veri platformu, ClickHouse/MySQL/Redis, retention, inventory |
| `planlama-agent-skill-mentor.md` | Veri/deploy/temizlik skill'leri ve mentor/data/release agent planı |
| `planlama-mali-analiz.md` | Mali Analiz sekmesi planı |
| `egitimplanlama.md` | BORFİN kurs okuma süreci ve OCR kayıtları |
| `docs/DEPLOYMENT.md` | Sunucu kurulum rehberi (adım adım) |
| `docs/archive/` | Tarihsel snapshot'lar (ROADMAP, ILERLEME, PROJE_DURUM_OZET) |

---

## 6. Geliştirme Faz Sırası

```
Faz 0 — Veri platformu ve production hazırlığı
  ├── Veri platformu → planlama-veri-platformu.md
  ├── Repo temizlik/canlıya çıkış → planlama-temizlik-canliya-cikis.md
  └── Denetim skill'leri + mentor agent → planlama-agent-skill-mentor.md

Faz 1 — Eğitim kaynak modeli ve yeni sekmeler
  ├── Eğitimler sekmesi  → planlama-egitimler.md (klavye: 6)
  └── Mali Analiz metadata/API/UI v1 → planlama-mali-analiz.md (klavye: 7)

Faz 2 — Grafik iyileştirmeleri (ChartPanel.ts'e dikkatli dokunma)
  └── Sprint G2–G10 → planlama-grafik.md

Faz 3 — Strateji Lab ürün entegrasyonu (quant_engine + StrategySpec değişiklikler)
  └── Sprint B1–B13 → planlama-backtest.md

Faz 4 — Mali Analiz gerçek veri fazı
  └── KAP/provider + finansal tablo store'u → planlama-mali-analiz.md
```

---

## 7. Veri Sağlayıcı Özeti

| Sembol | Birincil | İkincil |
|--------|----------|---------|
| BIST hisse | borsapy | yfinance `.IS` |
| BIST endeks | yfinance | borsapy |
| Kripto | Binance REST+WS | ccxt |
| Forex/Emtia | yfinance | borsapy |
| Fundamentals | borsa-mcp | borsapy |

Cache: Worker 60s'de bir çağırır → SQLite INSERT OR IGNORE → zamanla 1 ay+ birikir.

Yeni veri platformu hedefi:

| Katman | Sorumluluk |
|--------|------------|
| ClickHouse | OHLCV, raw/derived bar, hızlı backtest/screener |
| MySQL | Sembol, VIOP kontrat, provider, ingest job, data inventory, retention policy |
| Redis | Son quote, kısa candle cache, WebSocket pub/sub, ingest lock |
| Parquet/DuckDB | Lokal yedek, cold archive, fallback |

Retention özeti:

| Market | Timeframe | Saklama |
|--------|-----------|---------|
| BIST hisse | `1m` | 1 yıl |
| BIST hisse | `5m` ve üstü | 10 yıl |
| VIOP | `1m` ve üstü | 10 yıl |

---

## 8. Kaynak Linkler

- [saidsurucu/borsa-mcp](https://github.com/saidsurucu/borsa-mcp)
- [atilaahmettaner/tradingview-mcp](https://github.com/atilaahmettaner/tradingview-mcp)
- [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents)
- [tradermonty/claude-trading-skills](https://github.com/tradermonty/claude-trading-skills)
