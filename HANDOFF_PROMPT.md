# Quant Engine — Devir Teslim Promptu

Bu prompt, projeyi devralan yapay zekaya verilecek. Aşağıdaki tüm bilgiler doğrulanmış ve günceldir.

---

## SEN KİMSİN VE NE YAPIYORSUN

Sen bu projede üst düzey senior software architect, quant/backtest engine developer ve finansal veri altyapısı uzmanı gibi davranacaksın.

Proje amacı: BIST/VİOP için veri toplayabilen, geçmiş veriyi güvenilir şekilde saklayan, strateji/backtest çalıştıran, ileride Matriks/Borsa İstanbul/Foreks gibi veri sağlayıcıları bağlanabilecek, grafik/matrix/raporlama arayüzüne büyüyebilecek profesyonel bir quant backtest platformu geliştirmek.

**Proje dizini:** `/Users/enes/AgentWorkspace/Backtest`
**Sanal ortam:** `.venv` (Python 3.11.15, Homebrew)
**Aktivasyon:** `source .venv/bin/activate`

---

## ÇALIŞMA KURALLARI (MUTLAKA UYGULANACAK)

1. **Dil:** Tüm iletişim, açıklamalar, dokümantasyon TÜRKÇE. Kod isimlendirmeleri (değişken, fonksiyon, sınıf) İNGİLİZCE.
2. Her aşama başlamadan önce kısa plan çıkar.
3. Her dosya değişikliğinden sonra ne yaptığını açıkla.
4. Bir maddeyi ancak gerçekten test ettiysen `[x]` yap. Test edilmediyse `[ ]` veya `[!]` bırak.
5. Asla "tamamlandı" deme, önce doğrula (pytest, ruff, compileall).
6. Hataları saklama; kırılan, eksik kalan, riskli olan her şeyi açıkça yaz.
7. Kullanıcının mevcut değişikliklerini silme veya geri alma.
8. UI'dan önce motorun doğruluğunu güvenceye al.
9. Her değişiklik sonunda `ogrenilenler.md` dosyasına öğrenilen dersleri ekle (append, silme).
10. Her mantıksal bütünlük tamamlandığında `git add -A && git commit -m "..."` yap. Commit mesajları TÜRKÇE açıklamalı.
11. Her cevap sonunda durum raporu ver (aşağıdaki formatta).

**Durum raporu formatı:**
```
## Durum
- Aşama:
- Tamamlananlar:
- Değişen dosyalar:
- Çalıştırılan testler:
- Test sonucu:
- Kalan riskler:
- Sonraki önerilen adım:
```

---

## PROJENİN MEVCUT DURUMU

### Tamamlanan Aşamalar

**AŞAMA 0 — Derin Denetim ✅**
- Tüm dosyalar incelendi, 18 kontrol sorusu canlı test edildi
- 45 bug kataloglandı (ID'li: REQ-1→2, PYP-1, CFG-1→6, FET-1→9, STR-1→11, VAL-1→7, PIP-1→3, DEM-1→3)
- 5 kritik bug canlı doğrulandı: Validator NaN/negatif volume/OHLC kaçırıyor, Storage geçersiz mode kabul ediyor, Config env override otomatik değil

**AŞAMA 1 — Geliştirici Altyapısı ✅**
- `requirements.txt`: pandas-ta kaldırıldı (pip'te bulunamıyor)
- `pyproject.toml`: testpaths düzeltildi, pytest markers eklendi
- `ruff`: 240 lint hatası → 0 (temiz)
- `pytest`: 0 test → 25 test, hepsi geçiyor (0.33s)
- `tests/` yapısı: `unit/`, `integration/`, `golden/`, `fixtures/` oluşturuldu
- Golden fixture: `valid_ohlcv.csv` (10 satır), `invalid_ohlcv.csv` (7 satır hatalı)
- Smoke testler: `test_config.py` (6), `test_storage.py` (9), `test_validator.py` (10)
- Bilinen bug'lar testlerde "şu anki davranışı belgeleyen assertion" olarak yazıldı

### Mevcut Dosya Yapısı (Gerçek Kod)

```
/Users/enes/AgentWorkspace/Backtest/
├── .venv/                          # Python 3.11.15 sanal ortam
├── config/settings.toml            # TOML konfigürasyon (58 satır)
├── requirements.txt                # Bağımlılıklar (pandas-ta kaldırıldı)
├── pyproject.toml                  # Proje config + ruff + pytest ayarları
├── demo.py                         # Demo script (192 satır, 3 bug)
├── planlama.md                     # Ana yol haritası (v4, ~500 satır)
├── arayuz.md                       # UI planı (v3, Matrix terminal, ~300 satır)
├── ogrenilenler.md                 # Öğrenilen dersler kaydı (~85 satır)
├── quant_engine/
│   ├── config/config_manager.py    # Pydantic+TOML config (161 satır, 6 bug)
│   ├── data_pipeline/
│   │   ├── fetcher.py              # yfinance veri çekici (281 satır, 9 bug)
│   │   ├── storage_manager.py      # DuckDB+Parquet depolama (367 satır, 11 bug)
│   │   ├── data_validator.py       # Veri doğrulayıcı (233 satır, 7 bug)
│   │   └── pipeline.py             # Orkestratör (177 satır, 3 bug)
│   ├── backtest_engine/            # BOŞ (sadece __init__.py)
│   ├── strategy/                   # BOŞ
│   ├── optimization/               # BOŞ
│   ├── reporting/                  # BOŞ
│   ├── validation/                 # BOŞ
│   ├── live_execution/             # BOŞ
│   ├── cli/                        # BOŞ
│   └── tests/                      # BOŞ (eski, kullanılmıyor)
└── tests/                          # AKTİF TEST DİZİNİ
    ├── unit/
    │   ├── test_config.py          # 6 test ✅
    │   ├── test_storage.py         # 9 test ✅
    │   └── test_validator.py       # 10 test ✅
    ├── integration/                # Henüz test yok
    ├── golden/
    │   ├── valid_ohlcv.csv         # Elle doğrulanmış 10 satır
    │   └── invalid_ohlcv.csv       # Kasıtlı hatalı 7 satır
    └── fixtures/                   # Henüz fixture yok
```

### Kurulu Paketler (Doğrulanmış)

| Paket | Sürüm | Kodda Kullanılıyor mu? |
|:---|:---|:---:|
| duckdb | 1.5.2 | ✅ |
| polars | 1.40.1 | ❌ Kurulu ama hiç kullanılmıyor! |
| pandas | 3.0.2 | ✅ (tüm pipeline) |
| yfinance | 1.3.0 | ✅ |
| pydantic | 2.13.3 | ✅ |
| pyarrow | 24.0.0 | ✅ |
| loguru | — | ✅ |
| numba | 0.65.1 | ❌ Kurulu ama kullanılmıyor |
| pytest | 9.0.3 | ✅ |
| ruff | — | ✅ |

### Bilinen Bug'lar (45 Adet, Hiçbiri Düzeltilmedi)

Detaylı tablo `planlama.md` dosyasında. En kritik olanlar:

| ID | Dosya | Sorun | Canlı Doğrulandı |
|:---|:---|:---|:---:|
| VAL-1 | data_validator.py:132 | NaN fiyatları yakalamıyor | ✅ |
| VAL-2 | data_validator.py:153 | Negatif volume yakalamıyor | ✅ |
| VAL-3 | data_validator.py:140 | low > close yakalamıyor | ✅ |
| STR-3 | storage_manager.py:93 | mode="nonsense" sessizce kabul | ✅ |
| STR-5 | storage_manager.py:216 | SQL string interpolation | ✅ |
| STR-1 | storage_manager.py:126 | Append tüm Parquet'i okuyup yazıyor | ✅ |
| CFG-1 | config_manager.py:132 | get_config() env override çağırmıyor | ✅ |
| FET-1 | fetcher.py:80 | end=today — yfinance exclusive | Kod incelemesi |
| FET-3 | fetcher.py:97 | Intraday KeyError: 'date' | Kod incelemesi |
| FET-4 | fetcher.py:255 | Bulk fetch tek sembolde kırılıyor | Kod incelemesi |

---

## SIRADA NE VAR

### AŞAMA 2 — Config Sistemi Düzeltmeleri

```
- [ ] CFG-1: get_config() içinde apply_env_overrides() çağır veya pydantic-settings'e geç
- [ ] CFG-2: Tüm modellere model_config = ConfigDict(extra="forbid") ekle
- [ ] CFG-3: Field sınırları ekle: commission_rate >= 0, max_position_pct <= 1, max_workers >= 1
- [ ] CFG-4: db_path ya kullanılsın ya config'ten çıksın
- [ ] CFG-5: data_dir proje köküne göre deterministic resolve
- [ ] CFG-6: timezone, source, timeframe, retry, timeout ayarları ekle
- [ ] Config testleri yaz veya mevcut testleri güncelle
- [ ] pytest + ruff yeşil
```

### AŞAMA 3 — Veri Sağlayıcı Mimarisi

```
- [ ] quant_engine/core/ oluştur: protocols.py, instrument.py, order.py, clock.py
- [ ] quant_engine/data/providers/ oluştur: base.py, yfinance_provider.py
- [ ] MarketDataProvider protocol, BarRequest, FetchResult, ProviderCapabilities modelleri
- [ ] Mevcut fetcher.py'ı yfinance_provider.py'a taşı + FET-1→9 bug'ları düzelt
- [ ] SymbolMaster sembol eşleme altyapısı
- [ ] Matriks/BIST stub dosyaları (boş ama interface'i implemente eden)
- [ ] Provider testleri
```

### AŞAMA 4 — Storage Mimarisi

```
- [ ] raw/clean/adjusted/features katmanları
- [ ] source/market/timeframe/symbol/year partition yapısı
- [ ] Atomic parquet write (temp → checksum → rename)
- [ ] Metadata JSON yazımı
- [ ] STR-1→11 bug'ları düzelt
- [ ] SQL allow-list ve parametre güvenliği
- [ ] Storage testleri güncelle
```

### AŞAMA 5 — Veri Doğrulama

```
- [ ] VAL-1→7 bug'ları düzelt (NaN, negatif volume, OHLC, limitli auto_fix)
- [ ] Invalid veri storage'a yazılmasın
- [ ] Test assertion'larını tersine çevir (bug düzeldikten sonra)
```

### AŞAMA 6 — BIST Calendar

```
- [ ] Europe/Istanbul timezone, UTC depolama
- [ ] is_trading_day(), next_trading_day(), trading_days_between()
- [ ] Tatiller, yarım günler, müzayede dönemleri
- [ ] Delta fetch calendar ile çalışsın
```

### AŞAMA 7 — Minimal Backtest Motoru

```
- [ ] Execution spec: bar[t].close sinyal → bar[t+1].open execute
- [ ] Order, Fill, Position, Portfolio domain nesneleri
- [ ] Commission + slippage
- [ ] Invariant: cash + position_value == total_equity her barda
- [ ] Audit trail: signal → order → fill → position → pnl
- [ ] Anti-leakage: feature_ts ≤ decision_ts < execution_ts
- [ ] Golden fixture ile elle hesaplanmış sonuç eşleşmesi
- [ ] Buy & Hold baseline
```

### AŞAMA 8-13 (Sonraki fazlar)

Detaylar `planlama.md` dosyasında. Sıra: Strategy framework → Run registry/raporlama → Optimizasyon → Streamlit MVP → Matrix terminal → Matriks/BIST entegrasyon.

---

## HEDEFMİMARİ

Mevcut yapı (`data_pipeline/` altında düz) hedef yapıya (`core/ + data/ + backtest/ + app/`) taşınacak. Detay `planlama.md` dosyasında.

**Tek yönlü bağımlılık akışı (KURAL):**
```
core ← data ← strategy ← backtest ← research ← reporting ← app/cli
Core hiçbir şeyi import etmez. App her şeyi import edebilir.
```

**Hedef veri yapısı:**
```
data/
  raw/source=yfinance/market=bist/timeframe=1d/symbol=THYAO/year=2024/part.parquet
  clean/market=bist/timeframe=1d/symbol=THYAO/year=2024/part.parquet
  adjusted/...
  features/...
artifacts/runs/<run_id>/ (config.toml, trades.parquet, equity.parquet, metrics.json, report.html)
```

---

## ÖNEMLİ DOSYALAR — MUTLAKA OKU

1. **`planlama.md`** — Tüm bug listesi (45 adet, ID'li tablolar), sprint planı, hedef mimari, protocol tanımları, veri kaynağı karşılaştırma tablosu, performans tasarımı
2. **`arayuz.md`** — 10 ekranlı Matrix terminal UI planı, Streamlit vs React faz ayrımı
3. **`ogrenilenler.md`** — Alınan mimari kararlar, veri kaynağı dersleri, kod kalitesi kuralları
4. **`config/settings.toml`** — Mevcut konfigürasyon

---

## HIZLI BAŞLANGIÇ KOMUTLARI

```bash
cd /Users/enes/AgentWorkspace/Backtest
source .venv/bin/activate

# Testleri çalıştır (25 test, hepsi geçmeli)
python -m pytest tests/ -v

# Lint kontrolü (0 hata olmalı)
python -m ruff check . --exclude=.venv

# Derleme kontrolü
python -m compileall quant_engine/ tests/ -q

# Git durumu
git log --oneline -5
```

---

## FİNANSAL DOĞRULUK KURALLARI

- Lookahead bias kesinlikle engellenecek
- Adjusted/raw veri ayrımı korunacak
- Warm-up bar olmadan sinyal üretilemeyecek
- Komisyon ve slippage olmadan sonuç "gerçekçi" diye sunulmayacak
- Benchmark olmadan strateji sonucu yorumlanmayacak
- Her backtest sonucu varsayımlarıyla birlikte saklanacak

---

## İLK GÖREVİN

1. `planlama.md`, `arayuz.md`, `ogrenilenler.md` dosyalarını oku
2. `python -m pytest tests/ -v` ve `python -m ruff check . --exclude=.venv` çalıştır — ikisi de yeşil olmalı
3. AŞAMA 2'ye başla (Config sistemi düzeltmeleri)
4. Her bug düzeltmesinden sonra ilgili testi güncelle ve pytest'in hâlâ yeşil olduğunu doğrula
