# 🚀 Quant Engine — VİOP/BIST Algoritmik Trading & Backtest Motoru

Apple Silicon üzerinde maksimum performansla çalışan, internet bağımsız (offline-first) algoritmik trading ve yüksek hızlı backtest motoru.

## 🏗️ Mimari

```
İnternet (yfinance) → Data Pipeline → Parquet Dosyaları → DuckDB Sorguları → Backtest Motoru
                         (Tek bağlantı noktası)         (Soğuk depolama)    (Sıcak okuma)
```

## 📦 Tech Stack

| Bileşen | Teknoloji | Neden |
|:---|:---|:---|
| Dil | Python 3.11+ | Vektörel hesaplama ekosistemi |
| DataFrame | Polars + Pandas | Çok çekirdekli hız + ekosistem uyumu |
| Veritabanı | DuckDB + Parquet | Embedded, sıfır bakım, columnar |
| JIT | Numba | Kritik döngülerde C-seviyesi hız |
| Config | Pydantic + TOML | Tip-güvenli konfigürasyon |
| Raporlama | Plotly + Jinja2 | İnteraktif HTML raporlar |
| Optimizasyon | Optuna | Bayesian parametre arama |
| CLI | Typer | Modern komut satırı arayüzü |

## 🚀 Hızlı Başlangıç

```bash
# 1. Sanal ortamı oluştur ve aktive et
python3.11 -m venv .venv
source .venv/bin/activate

# 2. Bağımlılıkları yükle
pip install -r requirements.txt

# 3. Demo'yu çalıştır (tek hisse)
python demo.py --symbol THYAO

# 4. Tam pipeline demo'su (3 hisse)
python demo.py --full
```

## 📁 Proje Yapısı

```
quant_engine/
├── config/              # Merkezi konfigürasyon (Pydantic + TOML)
├── data_pipeline/       # İnternete bağlanan tek modül
│   ├── fetcher.py       # Yahoo Finance veri çekici
│   ├── storage_manager.py # DuckDB + Parquet depolama
│   ├── data_validator.py  # Veri kalite kontrolü
│   └── pipeline.py      # Orkestratör
├── strategy/            # Strateji framework'ü
├── backtest_engine/     # Vektörel backtest motoru
├── optimization/        # Parametre optimizasyonu
├── validation/          # Backtest doğrulama
├── reporting/           # Raporlama ve görselleştirme
├── live_execution/      # Canlı trading (gelecek)
└── cli/                 # Komut satırı arayüzü
```

## 📊 Geliştirme Durumu

- ✅ Faz 1: Temel Altyapı (Config + Data Pipeline)
- ⬜ Faz 2: Backtest Motoru
- ⬜ Faz 3: Optimizasyon & Doğrulama
- ⬜ Faz 4: Canlı Trading
