# BIST/VIOP Veri Platformu Plani

> Tarih: 2026-05-02
> Durum: Yeni ana veri fazi. Bu dokuman uygulanmadan once `genelplanlama.md` ve
> `planlama.md` okunur.
> Hedef: BIST/VIOP icin hizli, tasarruflu, denetlenebilir ve sunucuda
> calisabilir piyasa veri platformu.

---

## 1. Kesin Kararlar

Bu dokumandaki kararlar uygulama sirasinda tekrar tartisilmaz; ancak Enes yeni
karar verirse bu dosya guncellenir.

| Konu | Karar |
|---|---|
| Ilk piyasa kapsami | Once BIST 100 + VIOP, sonra tum BIST, sonra diger piyasalar |
| Ana veri tabani | ClickHouse |
| Operasyonel SQL | MySQL |
| Sicak cache / pub-sub / lock | Redis |
| Lokal yedek ve fallback | Parquet/DuckDB + mevcut SQLite cache |
| BIST hisse `1m` saklama | Sadece son 1 yil |
| VIOP `1m` saklama | 10 yil |
| BIST ust timeframe saklama | `5m`, `15m`, `30m`, `1h`, `4h`, `1d`, `1w`, `1mo`, `1y` icin 10 yil |
| Sahte veri | Yasak |
| Gunlukten dakika uretimi | Yasak |
| Dakikadan ust timeframe uretimi | Serbest ve tercih edilir |
| Veri raporu | Her sembol/timeframe icin satir, tarih araligi, boyut, eksik oran |

Mevcut lokal durum, planin baslangic snapshot'i:

| Depo | Durum |
|---|---|
| `data/bist` Parquet | 30 sembol, 85.944 gunluk bar |
| Parquet tarih araligi | Cogunlukla 2015-01-01 -> 2026-04-30 |
| `data/cache/ohlcv.sqlite3` | 41.244 bar, 51 sembol |
| `data/` toplam boyut | Yaklasik 33 MB |

Bu mevcut veri uretim ortami icin degerlidir; ama production ana sorgu deposu
ClickHouse olacaktir.

---

## 2. Sistem Hedefi

PiyasaPilot su sorulara hizli ve net cevap verebilmelidir:

- THYAO icin `1d`, `1h`, `15m`, `5m`, `1m` veriden ne kadar var?
- BIST 100 icinde hangi hisselerde 10 yillik `15m` veri eksik?
- VIOP ana kontratlarinda 10 yillik `1m` veri tam mi?
- Hangi veri raw, hangi veri daha kucuk timeframe'den turetildi?
- Hangi veri lisans/provider eksigi yuzunden alinamadi?
- Hangi market/timeframe disk alanini sisiriyor?
- Backtest, screener ve grafik ayni dogruluk kaynagindan mi okuyor?

Bu nedenle platform sadece "veri yazan" bir sistem olmayacak; ayni zamanda
veriyi olcen, eksigini gosteren, retention uygulayan ve README'ye rapor
ureten bir sistem olacak.

---

## 3. Veri Kapsami

### 3.1 V1 Piyasa Kapsami

| Faz | Kapsam | Not |
|---|---|---|
| V1-A | BIST 100 hisse | Hisse OHLCV ve kurumsal aksiyonlar |
| V1-B | VIOP oncelikli kontratlar | BIST 30 yakin vade, aktif kontrat ve rollover |
| V1-C | BIST endeksler | XU030, XU100 ve kullanilan ana endeksler |
| V2 | Tum BIST | BIST 100 tamamlandiktan sonra |
| V3 | Kripto/ABD/FX/emtia | Mevcut provider router korunarak genisleme |

### 3.2 Veri Tipleri

| Veri tipi | V1 durumu | Depo |
|---|---|---|
| OHLCV bar | Ana kapsam | ClickHouse |
| Sembol metadata | Ana kapsam | MySQL |
| VIOP kontrat/vade | Ana kapsam | MySQL |
| Rollover bilgisi | Ana kapsam | MySQL |
| Kurumsal aksiyon | Ana kapsam | MySQL + ClickHouse snapshot |
| Finansal tablo/oran | V1-B/V1-C ile baglanir | MySQL + ClickHouse snapshot |
| Tick data | Kapsam disi | Gelecek faz |
| Order book / Level 2 | Kapsam disi | Gelecek faz, lisans gerekir |

Tick ve order book v1'de alinmayacak. Bunlar eklenirse veri TB seviyesine
cikabilir ve ayri plan gerekir.

---

## 4. Timeframe ve Retention Politikasi

### 4.1 Saklama Tablosu

| Market | Varlik tipi | Timeframe | Saklama | Gerekce |
|---|---|---|---|---|
| BIST | Hisse | `1m` | 1 yil | Disk tasarrufu, son donem intraday analiz |
| BIST | Hisse | `5m`, `15m`, `30m` | 10 yil | Intraday backtest icin dengeli boyut |
| BIST | Hisse | `1h`, `4h` | 10 yil | Orta vade strateji ve grafik |
| BIST | Hisse | `1d`, `1w`, `1mo`, `1y` | 10 yil | Ana tarihsel analiz |
| VIOP | Kontrat | `1m` | 10 yil | VIOP oncelikli ve intraday davranis kritik |
| VIOP | Kontrat | `5m` ve ustu | 10 yil | `1m` kaynakli rollup |

### 4.2 Turetme Kurallari

Dogru turetme:

```text
1m -> 5m -> 15m -> 30m -> 1h -> 4h -> 1d -> 1w -> 1mo -> 1y
```

Alternatif dogru turetme:

```text
5m -> 15m -> 30m -> 1h -> 4h -> 1d -> 1w -> 1mo -> 1y
1d -> 1w -> 1mo -> 1y
```

Yasak turetme:

```text
1d -> 1h
1d -> 15m
1d -> 1m
1w -> 1d
1mo -> 1d
```

Yani sistem buyuk timeframe'den kucuk timeframe uretmez. Bunu yaparsa sahte
veri uretmis olur.

### 4.3 Raw ve Derived Ayrimi

Her bar satiri su iki soruya cevap vermeli:

- Bu veri provider'dan raw mi geldi?
- Yoksa baska timeframe'den mi uretildi?

Bu nedenle bar tablosunda asagidaki alanlar zorunludur:

```text
source
source_timeframe
is_derived
quality_status
ingested_at
```

Ornek:

```text
THYAO 15m 2018-01-02 10:15 is_derived=true source_timeframe=5m
F_XU030 1m 2018-01-02 10:01 is_derived=false source_timeframe=1m
```

---

## 5. ClickHouse Tasarimi

### 5.1 Ana Tablo

```sql
CREATE TABLE market_bars
(
    market LowCardinality(String),
    symbol String,
    instrument_type LowCardinality(String),
    timeframe LowCardinality(String),
    ts DateTime64(3, 'UTC'),
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume Float64,
    source LowCardinality(String),
    source_timeframe LowCardinality(String),
    is_derived UInt8,
    quality_status LowCardinality(String),
    ingest_job_id String,
    ingested_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree
PARTITION BY (market, timeframe, toYYYYMM(ts))
ORDER BY (market, symbol, timeframe, ts);
```

Karar gerekcesi:

- `market` ve `timeframe` partition'da oldugu icin BIST `1m` retention kolay
  uygulanir.
- `toYYYYMM(ts)` aylik partition verir; cok ince partition ile part sayisi
  patlatilmaz.
- `ORDER BY (market, symbol, timeframe, ts)` tek sembol/timeframe sorgularini
  hizlandirir.

### 5.2 Data Inventory Tablosu

ClickHouse veya MySQL tarafinda tutulabilir; operasyonel durum oldugu icin
ana kaynak MySQL olacaktir.

```text
data_inventory
- market
- symbol
- instrument_type
- timeframe
- row_count
- first_ts
- last_ts
- target_start_ts
- target_end_ts
- coverage_pct
- storage_bytes
- raw_row_count
- derived_row_count
- status
- source
- last_checked_at
- notes
```

`status` izin verilen degerler:

```text
raw_available
derived_available
partial
missing
provider_limit
license_required
not_configured
provider_failed
retention_trimmed
```

### 5.3 Quality Events

```text
data_quality_events
- id
- market
- symbol
- timeframe
- event_type
- start_ts
- end_ts
- severity
- details_json
- detected_at
```

Olay tipleri:

```text
gap
duplicate
outlier
negative_price
zero_volume_warning
split_suspected
timezone_mismatch
rollover_gap
provider_conflict
```

---

## 6. MySQL Tasarimi

MySQL piyasa barlarini tutmaz. MySQL operasyonel ve iliskisel bilgiyi tutar.

### 6.1 Tablolar

```text
instruments
- id
- market
- symbol
- display_symbol
- instrument_type
- isin
- company_name
- sector
- exchange
- currency
- is_active
- first_seen_at
- delisted_at
```

```text
viop_contracts
- id
- contract_symbol
- underlying_symbol
- contract_type
- maturity
- active_from
- active_to
- rollover_group
- previous_contract_symbol
- next_contract_symbol
- multiplier
- tick_size
- currency
```

```text
providers
- id
- name
- provider_type
- is_configured
- is_licensed
- supports_bist
- supports_viop
- supports_intraday
- max_history_days_json
- notes
```

```text
ingest_jobs
- id
- job_type
- market
- symbol
- timeframe
- target_start_ts
- target_end_ts
- status
- attempt_count
- rows_read
- rows_written
- started_at
- finished_at
- error_message
```

```text
data_retention_policy
- id
- market
- instrument_type
- timeframe
- retention_days
- keep_raw
- keep_derived
- archive_before_delete
```

```text
corporate_actions
- id
- symbol
- action_type
- ex_date
- payable_date
- ratio
- cash_amount
- currency
- source
- notes
```

### 6.2 MySQL Kullanilmamasi Gereken Yerler

MySQL asagidaki isler icin kullanilmayacak:

- 100 milyonlarca OHLCV bar sorgusu
- Intraday backtest ana veri taramasi
- Buyuk screener zaman serisi hesaplari
- WebSocket son fiyat cache'i

Bu isler ClickHouse veya Redis tarafina aittir.

---

## 7. Redis Tasarimi

Redis tarihsel veri tabani degildir. Sadece sicak veri ve koordinasyon icin
kullanilir.

Ana key'ler:

```text
quote:{market}:{symbol}:{timeframe}
cache:candles:{symbol}:{timeframe}:{start}:{end}:{limit}
lock:ingest:{provider}:{symbol}:{timeframe}
ws:quotes
ws:signals
health:service:{name}
```

TTL kurallari:

| Key | TTL |
|---|---:|
| `quote:*` | 1-3 gun |
| `cache:candles:*` | 30-300 saniye |
| `lock:ingest:*` | job timeout + guvenlik payi |
| `health:*` | 60-180 saniye |

Redis'e 10 yillik veri yazilmaz.

---

## 8. Dosya Yapisi

Uygulama dosya yapisi hedefi:

```text
backend/
  data/
    repositories/
      market_repository.py
      clickhouse_repository.py
      legacy_cache_repository.py
      mysql_metadata_repository.py
      redis_market_cache.py

    ingest/
      backfill.py
      delta.py
      derive_timeframes.py
      retention.py
      inventory.py
      quality.py
      dependency_graph.py
      jobs.py

    providers/
      bist_http.py
      viop_http.py
      yfinance_dev.py
      financials.py

    schemas/
      market.py
      instruments.py
      inventory.py
      provider_status.py

infra/
  docker-compose.dev.yml
  docker-compose.prod.yml
  clickhouse/
    init/
      001_market_bars.sql
      002_quality_events.sql
    config/
  mysql/
    migrations/
      001_instruments.sql
      002_providers.sql
      003_inventory.sql
      004_retention.sql
  nginx/
    default.conf

docs/
  VERI_MIMARISI.md
  VERI_KATALOGU.md
  BACKFILL_RUNBOOK.md
  DEPLOYMENT.md
```

Mevcut dosyalarla uyum:

- `backend/data/cache.py` hemen silinmeyecek; legacy fallback kalacak.
- `backend/data/historical_store.py` ClickHouse repository'ye baglanacak.
- `quant_engine/data_pipeline/storage_manager.py` Parquet yedek/fallback olarak kalacak.
- `/api/v2/candles` response formati korunacak.

---

## 9. Data Flow

### 9.1 Backfill Flow

```text
Ingest job
  -> provider capability kontrolu
  -> veri cek
  -> normalize et
  -> kalite kontrol
  -> ClickHouse market_bars yaz
  -> inventory guncelle
  -> gerekirse timeframe turet
  -> quality event yaz
```

### 9.2 Gunluk Delta Flow

```text
Scheduler
  -> aktif sembol/timeframe listesi
  -> son timestamp oku
  -> eksik araligi cek
  -> ClickHouse append
  -> Redis son quote guncelle
  -> inventory guncelle
```

### 9.3 API Okuma Flow

```text
/api/v2/candles
  -> Redis kisa cache
  -> ClickHouse raw/derived
  -> legacy Parquet/SQLite fallback
  -> provider fallback sadece izinliyse
  -> metadata ile response
```

Response metadata zorunlu alanlari:

```json
{
  "source": "clickhouse",
  "is_real": true,
  "is_derived": false,
  "source_timeframe": "15m",
  "quality_status": "ok",
  "coverage_pct": 98.7
}
```

---

## 10. Timeframe Dependency Graph

Timeframe turetme iliskisi graph olarak modellenir.

Node'lar:

```text
1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1mo, 1y
```

Edge'ler:

```text
1m -> 5m
5m -> 15m
15m -> 30m
30m -> 1h
1h -> 4h
4h -> 1d
1d -> 1w
1w -> 1mo
1mo -> 1y
```

Graph kurallari:

- Edge sadece kucuk timeframe'den buyuk timeframe'e gider.
- Ters edge yasaktir.
- Bir timeframe uretilmeden once kaynak node coverage kontrol edilir.
- Kaynak coverage dusukse hedef `partial` isaretlenir.
- BIST `1m` silinmeden once bagli ust timeframe'lerin son durumuna bakilir.

Bu graph hem veri isleme hem mentor egitimi icin kullanilacak.

---

## 11. README Raporu

README veya `docs/VERI_KATALOGU.md` icinde otomatik guncellenebilir rapor
olacak.

Ornek tablo:

```text
Sembol | Market | TF  | Satir | Ilk Tarih | Son Tarih | Hedef | Kapsam | Boyut | Durum
THYAO  | BIST   | 1m  | 95k   | 2025-05-02 | 2026-05-02 | 1Y  | 100% | 20MB | raw_available
THYAO  | BIST   | 15m | 95k   | 2016-05-02 | 2026-05-02 | 10Y | 98%  | 18MB | derived_available
THYAO  | BIST   | 1d  | 2.5k  | 2016-05-02 | 2026-05-02 | 10Y | 100% | 1MB  | raw_available
F_XU030| VIOP   | 1m  | ...   | 2016-05-02 | 2026-05-02 | 10Y | ...  | ...  | raw_available
```

Komutlar:

```bash
make data-inventory
make data-inventory-symbol SYMBOL=THYAO
make data-size-report
make data-gaps
make derive-timeframes
make retention-cleanup
make backfill-bist100
make backfill-viop
```

---

## 12. Uygulama Sprintleri

### VDP-0 Plan ve guvenlik kilitleri

- [x] Bu dosya `planlama.md` ve `genelplanlama.md` index'lerine baglanir.
- [x] `docs/VERI_MIMARISI.md` taslagi bu plandan uretilir.
- [x] `docs/VERI_KATALOGU.md` rapor formatini tanimlar.
- [x] Sahte veri yasagi test kabul kriterlerine eklenir.

### VDP-1 Altyapi servisleri

- [x] `infra/docker-compose.dev.yml` ClickHouse, MySQL, Redis ile gelir.
- [x] Healthcheck'ler eklenir.
- [x] `.env.example` veritabani URL'lerini icerir.
- [x] Python bagimliliklari eklenir: ClickHouse client, MySQL client, Redis client.

### VDP-2 Sema ve migration

- [x] ClickHouse `market_bars` tablosu eklenir.
- [x] ClickHouse `data_quality_events` tablosu eklenir.
- [x] MySQL `instruments`, `providers`, `ingest_jobs`, `data_inventory`,
  `data_retention_policy`, `viop_contracts` tablolarini alir.
- [x] Migration calistirma komutu eklenir.

### VDP-3 Repository katmani

- [x] `MarketRepository` interface yazilir.
- [x] `ClickHouseMarketRepository` yazilir.
- [x] `LegacyCacheRepository` mevcut SQLite/Parquet okumasini sarar.
- [x] `/api/v2/candles` repository uzerinden okur.
- [x] Backtest runner repository uzerinden okur.

### VDP-4 Inventory ve rapor

- [x] `inventory.py` ClickHouse, Parquet ve SQLite icin satir/tarih/boyut okur.
- [x] `make data-inventory` tablo uretir.
- [x] `make data-size-report` market/timeframe bazli disk kullanimini gosterir.
- [x] README veri durumu bolumu script ciktisina gore guncellenebilir hale gelir.

### VDP-5 Backfill

- [x] BIST 100 `1d` 10 yil backfill.
- [x] BIST 100 `5m/15m/30m/1h/4h` 10 yil backfill veya provider limit raporu.
- [x] BIST 100 `1m` sadece son 1 yil backfill.
- [x] VIOP `1m` 10 yil backfill.
- [x] Eksikler `data_inventory.status` alanina yazilir.

### VDP-6 Turetme ve graph

- [x] `dependency_graph.py` timeframe graph'ini tanimlar.
- [x] `derive_timeframes.py` kucuk timeframe'den buyuk timeframe uretir.
- [x] Gunlukten dakikalik uretim testle engellenir.
- [x] Derived veriler `is_derived=true` ve `source_timeframe` ile yazilir.

### VDP-7 Retention

- [x] `data_retention_policy` kurallari seed edilir.
- [x] `retention.py` BIST `1m` 1 yildan eski veriyi temizler.
- [x] Temizlik oncesi ust timeframe turetme kontrolu yapilir.
- [x] VIOP `1m` veriye 10 yil disinda cleanup uygulanmaz.

### VDP-8 Production hazirlik

- [x] `infra/docker-compose.prod.yml` eklenir.
- [x] ClickHouse/MySQL/Redis volume ayrimi yapilir.
- [x] Backup runbook yazilir.
- [x] `make prod-health` ClickHouse, MySQL, Redis, API ve inventory durumunu kontrol eder.

---

## 13. Test ve Kabul

Unit testler:

- [ ] ClickHouse repository insert/read idempotent.
- [ ] Duplicate bar iki kez yazilmaz.
- [ ] Timeframe graph ters edge kabul etmez.
- [ ] Gunlukten dakikalik uretim ValueError verir.
- [ ] BIST `1m` retention 1 yildan eski partitionlari hedefler.
- [ ] VIOP `1m` retention 10 yillik hedefi korur.

Integration testler:

- [ ] Fake provider -> backfill -> ClickHouse -> `/api/v2/candles`.
- [ ] ClickHouse bosken legacy Parquet/SQLite fallback bozulmaz.
- [ ] Inventory raporu mevcut lokal Parquet/SQLite veriyi dogru sayar.
- [ ] Backtest ClickHouse verisiyle calisir.

Kabul:

- [ ] Her sembol/timeframe icin satir, tarih araligi, boyut ve durum gorunur.
- [ ] BIST hisse `1m` 1 yildan eski tutulmaz.
- [ ] VIOP `1m` 10 yil hedefler.
- [ ] BIST ust timeframe'ler 10 yil hedefler.
- [ ] Eksik/lisans gerektiren veri acikca raporlanir.
- [ ] Sahte veri uretilmez.

---

## 14. Kaynak Notlari

- ClickHouse materialized view/rollup yaklasimi buyuk sorgularda okuma
  maliyetini azaltmak icin kullanilabilir:
  https://docs-content.clickhouse.tech/docs/en/guides/developer/cascading-materialized-views
- ClickHouse TTL eski veriyi silmek veya tasimak icin uygundur:
  https://clickhouse.com/blog/using-ttl-to-manage-data-lifecycles-in-clickhouse
- ClickHouse partition konusunda cok ince partition'dan kacinmak gerekir;
  ay bazli partition bu proje icin varsayilan kabul edilir:
  https://docs-content.clickhouse.tech/docs/en/engines/table-engines/mergetree-family/custom-partitioning-key
