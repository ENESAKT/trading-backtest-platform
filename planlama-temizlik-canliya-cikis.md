# Repo Temizligi ve Canliya Cikis Plani

> Tarih: 2026-05-02
> Durum: Yeni uretim hazirlik fazi.
> Hedef: Projeyi gereksiz dosyalardan arindirip hafif, denetlenebilir ve
> sunucuda calisabilir hale getirmek.

---

## 1. Kesin Kararlar

| Konu | Karar |
|---|---|
| `artifacts/` | Production'a girmez, git'e girmez |
| Borfin OCR/frame/video | Urune entegre edildiyse repo disi arsive tasinir veya silinir |
| Borfin icerigi | Birebir metin, ekran, formül, marka dili olarak urune giremez |
| `data/cache`, `data/bist`, lokal SQLite | Production image'a girmez; volume veya dis veri deposu |
| `.venv`, `.venv_pdf` | Production image'a girmez |
| `node_modules` | Production image'a girmez; build stage icinde uretilir |
| Docker image | Sadece gerekli kod, config ve build ciktisi |
| Canli ortam | `docker-compose.prod.yml` + nginx + domain + TLS + volume + backup |
| Temizlik | Silmeden once entegrasyon ve geri donus ihtiyaci kontrol edilir |

Mevcut repo tarama snapshot'i:

| Alan | Yaklasik boyut | Yorum |
|---|---:|---|
| `artifacts/` | 1.1 GB | En buyuk siskinlik, Borfin OCR/frame/video ciktilari |
| `piyasapilot-v2/` | 94 MB | Buyuk kisim `node_modules` |
| `data/` | 33 MB | Lokal cache, SQLite, Parquet |
| `backend/` | 1.1 MB | Kod boyutu saglikli |
| `quant_engine/` | 1.6 MB | Kod boyutu saglikli |
| `.claude/` | 332 KB | Agent/skill/hook dosyalari makul |

`git ls-files` taramasinda veri/artifact tarafinda gorunen ana dosya:

```text
data/workspaces/workspace.json
```

Bu dosyanin tracked kalip kalmayacagi ayrica degerlendirilecek. Kisisel
workspace state ise git disina alinmali; varsayilan demo workspace ise kucuk
ve kontrollu kalabilir.

---

## 2. Temizlik Hedefi

Canliya cikmadan once su hedeflere ulasilacak:

- Git calisma agacinda artifact, cache, local DB, video frame, OCR dump kalmayacak.
- Docker build context gereksiz 1 GB dosya tasimayacak.
- Backend image icinde `.venv`, `artifacts`, `data/cache`, `data/bist`,
  `node_modules` olmayacak.
- Frontend image icinde kaynak kod ve build tool yerine sadece `dist/` servis
  edilecek.
- Borfin'den gelen bilgi urune ozgun icerik ve plan maddesi olarak entegre
  olduysa ham kanit dosyalari repo icinde tutulmayacak.
- Silinen her sey tekrar uretilebilir veya repo disi arsivde tutulabilir
  olacak.

---

## 3. Borfin ve Egitim Entegrasyon Denetimi

### 3.1 Denetlenecek Kaynaklar

Mevcut Borfin/OCR izleri:

```text
artifacts/borfin_teknik_analiz_yasar_ocr
artifacts/borfin_ileri_teknik_analiz_yasar_ocr
artifacts/borfin_yatirimci_psikolojisi_ocr
artifacts/borfin_sistem_trading_fuat_ocr
artifacts/borfin_indikator_ocr
artifacts/borfin_vob_yasar_ocr
artifacts/borfin_vadeli_trade_bolgun_ocr
artifacts/borfin_frames
artifacts/borfin_ocr
artifacts/borfin_sistem_trading_fuat_docs_text
```

Bu klasorler uygulama runtime'i icin gerekli degildir.

### 3.2 Uygunluk Kurallari

Uygulamaya girebilir:

- Kavramin PiyasaPilot'a ozgu anlatimi.
- PiyasaPilot workflow'una donusturulmus egitim maddesi.
- Telifsiz, ozgun, yeniden yazilmis strateji fikri.
- Kaynak guven notu: `source_method`, `source_confidence`, `needs_audio_transcript`.

Uygulamaya giremez:

- Borfin ekran goruntusu.
- Video frame.
- Slayt metni.
- Yardimci dosya metni.
- Birebir formül/metin.
- Borfin marka dili.
- Platform ekran tasariminin kopyasi.

### 3.3 Entegrasyon Tamamlandi Sayma Kriteri

Bir Borfin artifact klasoru ancak su kontrol tamamlanirsa repo icinden
kaldirilabilir:

- [ ] Ilgili OCR raporundaki urune alinacak fikirler `planlama-egitimler.md`,
  `planlama-backtest.md`, `planlama-grafik.md` veya ilgili plana islenmis.
- [ ] Frontend egitim markdownlarinda birebir kopya yok.
- [ ] Kodda Borfin asset path'i yok.
- [ ] README veya docs icinde Borfin ham dosyasina runtime bagimliligi yok.
- [ ] Gerekirse ham artifact repo disi arsive tasindi.

### 3.4 Arama Komutlari

```bash
rg -n "BORF|Borfin|borfin|Borf" README.md docs planlama*.md genelplanlama.md egitimplanlama.md piyasapilot-v2/src backend quant_engine
find artifacts -maxdepth 2 -type d -print
find artifacts -type f -size +1M -print
```

---

## 4. Repo Boyutu ve Dosya Siniflandirma

### 4.1 Production'a Girecekler

```text
backend/
quant_engine/
piyasapilot-v2/src/
piyasapilot-v2/package.json
piyasapilot-v2/package-lock.json
piyasapilot-v2/vite.config.ts
piyasapilot-v2/tsconfig.json
infra/
docker/
docs/
.claude/agents/
.claude/skills/
.claude/commands/
README.md
Makefile
requirements.txt
pyproject.toml
Dockerfile.api
Dockerfile.workers
Dockerfile.notifier
nginx.conf
```

### 4.2 Git Disi Kalacaklar

```text
artifacts/
data/cache/
data/bist/
data/viop/
data/runtime/
data/strategy_lab/*.sqlite3
logs/
.venv/
.venv_pdf/
piyasapilot-v2/node_modules/
piyasapilot-v2/test-results/
piyasapilot-v2/playwright-report/
.claude/agent-logs/
.env
```

### 4.3 Ozel Karar Gerektirenler

| Dosya | Karar |
|---|---|
| `data/workspaces/workspace.json` | Demo/default workspace ise kalabilir; kisisel runtime state ise git disina alinacak |
| `matriks.md` | `.gitignore` icinde, repo disi referans kabul edilir |
| `egitimplanlama.md` | Plan/kanıt ozeti olarak kalir, ham artifact yerine hafif referans |
| `PROJE_DURUM_OZET.md`, `ROADMAP.md` | Tarihsel snapshot, ana karar kaynagi degil |

---

## 5. Docker ve Build Context

### 5.1 `.dockerignore`

Kok dizinde `.dockerignore` olacak. Asgari icerik:

```text
.git
.venv
.venv_pdf
__pycache__
*.pyc
.env
artifacts
data/cache
data/bist
data/viop
data/runtime
data/strategy_lab/*.sqlite3
logs
piyasapilot-v2/node_modules
piyasapilot-v2/test-results
piyasapilot-v2/playwright-report
.claude/agent-logs
```

### 5.2 Backend Image

Backend image icinde olmayacak:

- Lokal veri dosyalari.
- OCR artifact.
- Python sanal ortam kopyasi.
- Node modulleri.
- Test reportlari.

Backend image icinde olacak:

- `backend/`
- `quant_engine/`
- `requirements.txt`
- gerekli config dosyalari.

### 5.3 Frontend Image

Multi-stage build:

```text
node builder
  -> npm ci
  -> npm run build

nginx runtime
  -> sadece dist/
```

Runtime image icinde `src/`, `node_modules`, Playwright raporlari olmayacak.

---

## 6. Canliya Cikis Mimarisi

Production servisleri:

```text
nginx
api
ingestor
scheduler
notifier
clickhouse
mysql
redis
backup
```

### 6.1 Nginx

Nginx gorevleri:

- Domain'den gelen HTTP/HTTPS trafigini karsilar.
- Frontend static dosyalarini sunar.
- `/api/*` isteklerini FastAPI'ye yollar.
- `/ws/*` WebSocket proxy yapar.
- TLS sonlandirma yapar.

Zorunlu ayarlar:

```text
proxy_http_version 1.1
proxy_set_header Upgrade $http_upgrade
proxy_set_header Connection "upgrade"
proxy_set_header Host $host
```

### 6.2 Volume Plani

```text
clickhouse_data
mysql_data
redis_data
backups
app_logs
```

Veri image icine gomulmeyecek; volume veya dis servis kullanilacak.

### 6.3 Environment

`.env.production` alanlari:

```text
APP_ENV=production
PUBLIC_BASE_URL=https://domain
DATABASE_URL=mysql://...
CLICKHOUSE_URL=http://clickhouse:8123
REDIS_URL=redis://redis:6379/0
BIST_HTTP_URL_TEMPLATE=
VIOP_HTTP_URL_TEMPLATE=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
SMTP_HOST=
SMTP_USER=
SMTP_PASSWORD=
```

Secret'lar loglanmayacak ve endpoint'lerde maskelenecek.

---

## 7. Backup ve Geri Donus

### 7.1 Backup Kapsami

| Kaynak | Siklus | Not |
|---|---|---|
| MySQL | Gunluk | Metadata, job, strateji/paper kayitlari |
| ClickHouse | Gunluk/haftalik | Piyasa barlari ve kalite eventleri |
| Redis | Opsiyonel | Sicak cache oldugu icin kritik degil |
| Parquet cold archive | Haftalik/aylik | Uzun vadeli tasinabilir yedek |
| `.env.production` | Manuel guvenli saklama | Git'e girmez |

### 7.2 Rollback

Rollback adimlari:

1. Son saglam image tag secilir.
2. `docker compose` ilgili servisleri eski image ile kaldirir.
3. MySQL migration geriye uyumlu degilse backup restore plani uygulanir.
4. ClickHouse tablo semasi breaking degilse veri korunur.
5. `make prod-health` gecmeden trafik acilmaz.

---

## 8. Kontrol Komutlari

Eklenecek Make target'lari:

```bash
make repo-cleanup-report
make borfin-integration-check
make production-package-check
make docker-context-size
make prod-health
make deployment-check
make backup-now
make logs
```

Komut amaclari:

| Komut | Amac |
|---|---|
| `repo-cleanup-report` | Buyuk dosya, tracked artifact, gereksiz cache raporu |
| `borfin-integration-check` | Borfin ham dosyasi urune bagli mi, telif riski var mi |
| `production-package-check` | `.dockerignore`, image context ve runtime dosyalari kontrolu |
| `docker-context-size` | Build context boyutunu olcer |
| `prod-health` | API, ClickHouse, MySQL, Redis, nginx saglik kontrolu |
| `deployment-check` | Domain, TLS, env, volume, backup, healthcheck kontrolu |
| `backup-now` | Manuel yedek |

---

## 9. Uygulama Sprintleri

### RCP-0 Plan baglantisi

- [x] Bu dosya `genelplanlama.md` ve `planlama.md` icine eklenir.
- [x] Aktif sprint dosyasina repo temizlik/canliya cikis fazi eklenir.

### RCP-1 Repo tarama scriptleri

- [x] Buyuk dosya raporu scripti yazilir. (scripts/deployment/repo_cleanup_report.py)
- [x] Tracked artifact raporu yazilir.
- [x] `.gitignore` ve `.dockerignore` karsilastirma raporu yazilir.
- [x] `make repo-cleanup-report` eklenir.

### RCP-2 Borfin entegrasyon denetimi

- [x] `artifacts/borfin_*` klasorleri listeleyen rapor. (scripts/deployment/borfin_check.py)
- [x] Frontend markdownlarda birebir kopya/telif riski pattern kontrolu.
- [x] Kodda artifact path kullanimi kontrolu.
- [x] Silinebilir/tasinabilir artifact raporu.

### RCP-3 Docker paket temizligi

- [x] `.dockerignore` eklenir.
- [x] Backend image build context olculur.
- [x] Frontend multi-stage build dogrulanir.
- [x] Image icinde yasak klasorler olmadigi test edilir.

### RCP-4 Production compose

- [x] `infra/docker-compose.prod.yml` yazilir.
- [x] nginx TLS ve WebSocket proxy ayari hazirlanir.
- [x] ClickHouse/MySQL/Redis volume ayrimi yapilir.
- [x] `backup` servisi veya runbook eklenir.

### RCP-5 Canliya cikis runbook

- [x] `docs/DEPLOYMENT.md` yazilir.
- [x] Domain DNS adimlari yazilir.
- [x] SSL/TLS adimlari yazilir.
- [x] Env/secret kontrolu yazilir.
- [x] Rollback proseduru yazilir.

---

## 10. Kabul Kriterleri

Repo temizligi:

- [x] `artifacts/` git'te yok, production context'te yok.
- [x] Borfin ham OCR/frame/video dosyalari runtime'a bagli degil.
- [x] `data/cache`, `data/bist`, lokal SQLite ve Parquet image'a girmiyor.
- [x] `node_modules` runtime frontend image icinde yok.
- [x] `.venv` image'a kopyalanmiyor.
- [x] `git ls-files` veri/artifact kalintisi raporu temiz veya bilincli istisna listesinde.

Production:

- [ ] `docker-compose.prod.yml` tek komutla kalkar.
- [ ] nginx frontend, API ve WebSocket'i dogru yonlendirir.
- [ ] ClickHouse, MySQL, Redis healthcheck geciyor.
- [ ] Backup komutu calisiyor.
- [ ] `make deployment-check` yesil rapor verir.

Borfin:

- [ ] Urunde Borfin birebir metni/gorseli yok.
- [ ] Egitim icerikleri PiyasaPilot'a ozgu ve telifsiz.
- [ ] Entegre edilmis artifact klasorleri silinebilir/tasinabilir diye raporlanir.

---

## 11. Asla Yapilmamasi Gerekenler

- Kullanici onayi olmadan `rm -rf artifacts` calistirma.
- Ham Borfin dosyalarini urune asset olarak koyma.
- `.env` dosyasini commit etme.
- Local SQLite/Parquet dosyalarini Docker image'a gommee.
- Production verisini git ile tasima.
- Docker image'i `.venv` veya `node_modules` kopyalayarak sisirme.
- Backtest veya veri dogrulama icin sahte veri uretme.
