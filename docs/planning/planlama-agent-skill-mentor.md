# Agent, Skill ve Mentor Plani

> Tarih: 2026-05-02
> Durum: Veri platformu, repo temizligi ve canliya cikis fazlarini denetleyecek
> yardimci agent/skill plani.
> Hedef: Baska bir yapay zeka bu projeye girdiginde neyi nasil kontrol
> edecegini sasirmasin; Enes de sistemi adim adim ogrensin.

---

## 1. Kesin Kararlar

| Konu | Karar |
|---|---|
| Skill dili | Kisa, gorev odakli, token tasarruflu |
| Detayli bilgi | `references/` dosyalarinda tutulur |
| Deterministik kontrol | Script ile yapilir |
| Mentor agent | Turkce anlatir, uygulama oncesi ogretir |
| Denetim agent'lari | Kod yazmadan once plan ve politika kontrol eder |
| Skill'ler | Repo icinde `.claude/skills/` altinda planlanir |
| Agent'lar | `.claude/agents/` altinda planlanir |

Skill'ler uzun ders kitabi olmayacak. `SKILL.md` sadece ne zaman tetiklenecegini
ve hangi script/reference dosyasina bakilacagini soyler. Bu, token harcamasini
azaltir.

---

## 2. Neden Bu Katman Gerekli?

Bu projede riskli alanlar var:

- Cok buyuk veri setleri.
- ClickHouse/MySQL/Redis rol karismasi.
- BIST `1m` retention politikasinin unutulmasi.
- VIOP `1m` 10 yil hedefinin bozulmasi.
- Borfin artifact'lerinin yanlislikla urune veya production image'a girmesi.
- Docker image'in `.venv`, `node_modules`, `artifacts` ile sismesi.
- Sunucuya cikarken env, TLS, backup veya WebSocket proxy ayarinin unutulmasi.
- Baska bir AI'nin eski SQLite/Parquet planini tek dogruluk kaynagi sanmasi.

Bu nedenle agent ve skill katmani "hatirlatma" degil, aktif denetim
mekanizmasi olacak.

---

## 3. Skill Tasarim Standardi

Her yeni skill su yapida olacak:

```text
.claude/skills/<skill-name>/
  SKILL.md
  scripts/
    <deterministic_check>.py
  references/
    <policy-or-schema>.md
```

`SKILL.md` siniri:

- 150-250 satiri gecmemeli.
- Sema tamami SKILL.md'ye gomulmemeli.
- Uzun SQL, tablo listesi, policy detaylari reference dosyasina konmali.
- Tekrarlanabilir raporlar script ile uretilmeli.

Ornek `SKILL.md` mantigi:

```markdown
---
name: data-inventory-check
description: Use when checking BIST/VIOP symbol-timeframe coverage, row counts, first/last dates, retention status, or README data inventory accuracy.
---

# Workflow

1. Read `planlama-veri-platformu.md` section 4 and 11.
2. Run `scripts/check_inventory.py`.
3. Compare output with README/docs inventory.
4. Report missing, partial, license_required, retention_trimmed statuses.
```

---

## 4. Yeni Skill'ler

### 4.1 `data-architecture-auditor`

Amac:

- Veri mimarisinde ClickHouse/MySQL/Redis rollerinin dogru ayrildigini kontrol eder.
- OHLCV barlarin MySQL'e, metadata'nin ClickHouse'a yanlis yazilmasini engeller.
- `/api/v2/candles`, backtest ve screener'in dogru repository katmanindan okudugunu denetler.

Tetiklenme:

- Veri mimarisi degisiyorsa.
- ClickHouse/MySQL/Redis dosyalari ekleniyorsa.
- `/api/v2/candles` veya backtest veri okuma yolu degisiyorsa.

Kontrol listesi:

- [ ] `market_bars` ClickHouse'ta.
- [ ] `instruments`, `providers`, `ingest_jobs`, `data_inventory` MySQL'de.
- [ ] Redis sadece sicak cache/pub-sub/lock icin.
- [ ] SQLite/Parquet sadece fallback veya lokal yedek.
- [ ] Response metadata `source`, `is_real`, `is_derived`, `quality_status` iceriyor.

Kaynak:

- `planlama-veri-platformu.md`
- `references/data-storage-roles.md`
- `scripts/audit_data_architecture.py`

### 4.2 `data-inventory-check`

Amac:

- Her sembol/timeframe icin veri sayisi, ilk-son tarih, boyut ve kapsam durumunu raporlar.
- README ve `docs/VERI_KATALOGU.md` icindeki veri tablosunun guncel olup olmadigini kontrol eder.

Tetiklenme:

- Backfill sonrasi.
- Veri depolama degisimi sonrasi.
- README veri bolumu guncellenecegi zaman.

Kontrol listesi:

- [ ] BIST 100 sembolleri listeleniyor.
- [ ] VIOP oncelikli kontratlar listeleniyor.
- [ ] `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`, `1w`, `1mo`, `1y` gorunuyor.
- [ ] `raw_available`, `derived_available`, `partial`, `missing`, `license_required` ayrimi var.
- [ ] BIST `1m` hedefi 1 yil, VIOP `1m` hedefi 10 yil olarak hesaplanir.

Kaynak:

- `planlama-veri-platformu.md`
- `scripts/check_data_inventory.py`

### 4.3 `data-retention-guardian`

Amac:

- Retention politikasinin bozulmasini engeller.
- BIST hisse `1m` verisi 1 yildan eski tutuluyorsa uyarir.
- VIOP `1m` verisinin 10 yil hedefini korur.
- Silmeden once ust timeframe'lerin uretildigini kontrol eder.

Tetiklenme:

- `retention.py`, ClickHouse TTL veya cleanup job degisiyorsa.
- Backfill/derive akisi degisiyorsa.
- Disk boyutu azaltma isi yapiliyorsa.

Kontrol listesi:

- [ ] BIST hisse `1m` retention 365 gun.
- [ ] VIOP `1m` retention 10 yil.
- [ ] BIST `1m` silinmeden once `5m/15m/30m/1h/4h/1d/1w/1mo/1y` durumu kontrol edilir.
- [ ] Gunlukten dakikalik veri uretimi yok.
- [ ] Cleanup raporu `data_inventory` gunceller.

Kaynak:

- `planlama-veri-platformu.md`
- `references/retention-policy.md`
- `scripts/check_retention.py`

### 4.4 `timeframe-derivation-check`

Amac:

- Timeframe graph ve rollup zincirini denetler.
- Yanlis yonde veri turetimini engeller.

Tetiklenme:

- `derive_timeframes.py` veya `dependency_graph.py` degisiyorsa.
- Yeni timeframe ekleniyorsa.
- Backtest/grafik yeni timeframe okumaya basliyorsa.

Kontrol listesi:

- [ ] Edge'ler sadece kucuk timeframe'den buyuge.
- [ ] `1d -> 1m` gibi ters uretim yasak.
- [ ] `is_derived` ve `source_timeframe` dogru yaziliyor.
- [ ] Partial kaynak, partial hedef olarak isaretleniyor.

Kaynak:

- `planlama-veri-platformu.md` bolum 10
- `scripts/check_timeframe_graph.py`

### 4.5 `repo-cleanup-auditor`

Amac:

- Buyuk dosyalari, artifact'leri, local DB'leri, tracked runtime dosyalarini bulur.
- Temizlik oncesi neyin silinebilir, neyin arşivlenebilir, neyin korunacak oldugunu raporlar.

Tetiklenme:

- Canliya cikis oncesi.
- Build context buyudugunde.
- Borfin/artifact temizligi yapilacaginda.

Kontrol listesi:

- [ ] `artifacts/` production context'te yok.
- [ ] `data/cache`, `data/bist`, local SQLite image'a girmiyor.
- [ ] `.venv`, `.venv_pdf`, `node_modules` image'a girmiyor.
- [ ] `git ls-files` artifact/cache dosyasi gostermiyor veya istisna listesinde.
- [ ] Silinecek dosyalar onceden raporlandi.

Kaynak:

- `planlama-temizlik-canliya-cikis.md`
- `scripts/scan_repo_weight.py`

### 4.6 `borfin-integration-auditor`

Amac:

- Borfin OCR/frame/video artifact'leri urune dogru ve telifsiz sekilde
  donusmus mu kontrol eder.
- Birebir kopya, ekran goruntusu, marka dili ve telif riski arar.

Tetiklenme:

- Egitim icerigi degisiyorsa.
- `artifacts/borfin_*` temizlenecekse.
- Yeni egitim markdown'u ekleniyorsa.

Kontrol listesi:

- [ ] Frontend egitim markdownlarinda Borfin birebir metni yok.
- [ ] Borfin image/frame/video asset yok.
- [ ] Kaynak notu var ama ham dosyaya runtime bagimliligi yok.
- [ ] Ilgili fikir plan dosyasina islenmis.
- [ ] Artifact klasoru silinebilir/tasinabilir raporlandi.

Kaynak:

- `planlama-temizlik-canliya-cikis.md`
- `planlama-egitimler.md`
- `egitimplanlama.md`
- `scripts/check_borfin_integration.py`

### 4.7 `production-package-auditor`

Amac:

- Production Docker image ve build context temiz mi kontrol eder.

Tetiklenme:

- Dockerfile veya compose degisiyorsa.
- Canliya cikis oncesi.
- `.dockerignore` degisiyorsa.

Kontrol listesi:

- [ ] `.dockerignore` gerekli klasorleri disliyor.
- [ ] Backend image icinde `artifacts`, `.venv`, `node_modules`, local DB yok.
- [ ] Frontend runtime image sadece `dist/` servis ediyor.
- [ ] Build context boyutu raporlandi.

Kaynak:

- `planlama-temizlik-canliya-cikis.md`
- `scripts/check_production_package.py`

### 4.8 `deployment-readiness-check`

Amac:

- Sunucuya cikmadan once domain, nginx, TLS, volume, env, backup ve healthcheck
  durumunu kontrol eder.

Tetiklenme:

- Production deploy oncesi.
- `infra/docker-compose.prod.yml`, nginx veya env ayarlari degisiyorsa.

Kontrol listesi:

- [ ] Domain DNS hazir.
- [ ] nginx API ve WebSocket proxy hazir.
- [ ] TLS/SSL planli.
- [ ] ClickHouse/MySQL/Redis volume ayrilmis.
- [ ] Backup komutu var.
- [ ] `make prod-health` var.
- [ ] Secret'lar git'e girmiyor.

Kaynak:

- `planlama-temizlik-canliya-cikis.md`
- `docs/DEPLOYMENT.md`
- `scripts/check_deployment_readiness.py`

---

## 5. Yeni Agent'lar

### 5.1 `data-platform-mentor`

Dosya:

```text
.claude/agents/data-platform-mentor.md
```

Gorev:

- Enes'e veri platformunu Turkce ve adim adim ogretir.
- Kod yazmadan once konu anlatir.
- Kisa ders, ornek, mini kontrol sorusu modeli kullanir.
- Soyut konulari PiyasaPilot dosyalari uzerinden anlatir.

Ders basliklari:

1. Zaman serisi veri nedir?
2. OHLCV neden boyle saklanir?
3. ClickHouse neden MySQL'den farkli?
4. MySQL neden hala gerekli?
5. Redis neden tarihsel veri icin kullanilmaz?
6. Partition nedir?
7. TTL ve retention nedir?
8. Raw ve derived veri farki nedir?
9. Timeframe graph nedir?
10. VIOP rollover nedir?
11. Docker image ve volume farki nedir?
12. Domain, nginx ve TLS nasil calisir?
13. Backup ve rollback neden zorunludur?

Davranis kurallari:

- Kullaniciya Turkce cevap verir.
- Gereksiz uzun teori yazmaz.
- Her derste repo dosyalarindan ornek verir.
- Bilinmeyen yerde uydurmaz, ilgili plan dosyasina bakar.
- Uygulama oncesi ilgili skill'i onerebilir.

### 5.2 `data-architect`

Dosya:

```text
.claude/agents/data-architect.md
```

Gorev:

- Veri platformu mimari degisikliklerini planlar ve uygular.
- ClickHouse/MySQL/Redis rol ayrimina sadik kalir.
- Retention ve inventory kurallarini bozamaz.

Sahip oldugu alanlar:

```text
backend/data/repositories/
backend/data/ingest/
infra/clickhouse/
infra/mysql/
docs/VERI_MIMARISI.md
docs/VERI_KATALOGU.md
```

Kural:

- `quant_engine/backtest/engine.py` gibi cekirdek motor dosyalarina dokunmadan
  once gerekce yazmali.
- Legacy SQLite/Parquet fallback'i bir anda sokmemeli.

### 5.3 `release-janitor`

Dosya:

```text
.claude/agents/release-janitor.md
```

Gorev:

- Canliya cikis oncesi repo temizligi, artifact temizligi, Docker context ve
  deployment checklist'ini yonetir.

Sahip oldugu alanlar:

```text
.dockerignore
infra/
docs/DEPLOYMENT.md
planlama-temizlik-canliya-cikis.md
Makefile
```

Kural:

- Silme islemi yapmadan once rapor uretir.
- Kullanici onayi olmadan ham artifact silmez.
- Secret dosyalarini okumaz/yazmaz.

---

## 6. Komutlar

Yeni slash command veya Make target fikirleri:

```text
/mentor-veri
/veri-envanter
/repo-temizlik
/canli-kontrol
```

Make target'lari:

```bash
make data-inventory
make data-size-report
make data-gaps
make retention-check
make repo-cleanup-report
make borfin-integration-check
make production-package-check
make deployment-check
```

---

## 7. Uygulama Sirası

### ASM-0 Plan baglama

- [x] Bu dosya `planlama.md` ve `genelplanlama.md` icine eklenir.
- [x] `docs/AGENT_REHBERI.md` yeni agent'lari listeler.
- [x] `docs/SKILL_REHBERI.md` yeni skill'leri listeler.

### ASM-1 Skill iskeletleri

- [x] `data-architecture-auditor`
- [x] `data-inventory-check`
- [x] `data-retention-guardian`
- [x] `timeframe-derivation-check`
- [x] `repo-cleanup-auditor`
- [x] `borfin-integration-auditor`
- [x] `production-package-auditor`
- [x] `deployment-readiness-check`

### ASM-2 Script iskeletleri

- [x] `scripts/check_data_inventory.py`
- [x] `scripts/check_retention.py`
- [x] `scripts/check_timeframe_graph.py`
- [x] `scripts/scan_repo_weight.py`
- [x] `scripts/check_borfin_integration.py`
- [x] `scripts/check_production_package.py`
- [x] `scripts/check_deployment_readiness.py`

### ASM-3 Agent iskeletleri

- [x] `.claude/agents/data-platform-mentor.md`
- [x] `.claude/agents/data-architect.md`
- [x] `.claude/agents/release-janitor.md`

### ASM-4 Dokuman baglantilari

- [x] `docs/AGENT_REHBERI.md` guncellenir.
- [x] `docs/SKILL_REHBERI.md` guncellenir.
- [x] README komut listesine yeni denetim komutlari eklenir.

---

## 8. Kabul Kriterleri

- [ ] Skill'ler uzun ve token yutan dokumanlara donusmez.
- [ ] Her skill'in net tetiklenme alani vardir.
- [ ] Her kritik kontrol script ile tekrar calistirilabilir.
- [ ] Mentor agent Enes'e Turkce, basamakli ve repo baglamli ogretir.
- [ ] Data architect veri politikalarini bozamaz.
- [ ] Release janitor silmeden once rapor uretir.
- [ ] Yeni agent/skill listesi `docs/AGENT_REHBERI.md` ve `docs/SKILL_REHBERI.md` icinde gorunur.

---

## 9. Asla Yapilmamasi Gerekenler

- Skill icine uzun SQL dump veya buyuk rapor gommek.
- Mentor agent'i uygulama agent'i gibi kullanmak.
- Denetim scripti yerine elle tahmine dayali karar vermek.
- Release janitor'a kullanici onayi olmadan dosya sildirmek.
- Borfin artifact'lerini "kaynak lazim olur" diye production context'te tutmak.
- Agent'lara secret okuma/yazma gorevi vermek.
