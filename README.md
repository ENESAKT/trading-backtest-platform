# Quant Engine — BIST/Kripto/Emtia Trading Terminali

Gerçek veri odaklı araştırma, backtest ve trading terminali. Streamlit arayüzü
BIST, Forex, Emtia ve Kripto için piyasa özeti, bağımsız analiz pencereleri,
Workspace JSON yönetimi ve kalıcı strateji laboratuvarı sunar.

## 🏗️ Mimari

```
İnternet (yfinance / Binance) → Provider Katmanı → Validator → Backtest Motoru → Streamlit Terminal
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

# 3. Gerçek veri kontrolünü çalıştır (tek hisse)
python real_data_check.py --symbol THYAO

# 4. PiyasaPilot v2 stack'ini başlat
python live_server.py            # Backend gateway → http://localhost:8000
cd piyasapilot-v2 && npm run dev # Vite dev server → http://localhost:5173
```

## Terminal Özellikleri

- Ana dashboard: BIST 100, USD/TRY, XAU/USD, BTC/USDT ve ETH/USDT gerçek veri özeti.
- PiyasaPilot HTML paneli: BIST 100, USD/TRY, BTC/USDT ve Altın için read-only canlı grafikler.
- Bağımsız pencereler: seçilen sembol için aç/kapat yapılabilen analiz sekmeleri.
- Veri İstasyonu: API kaynakları, sembol grupları ve veri setleri için Workspace JSON.
- Strateji Laboratuvarı: SQLite append-only strateji kaydı ve geri çağırma.
- Sıfır demo veri politikası: provider veri vermezse grafik bekleme/hata durumunda kalır.
- Canlı işlem motoru kapalıdır; paper trading kayıtları yalnızca sanal işlem olarak `data/workspaces/workspace.json` içine yazılır.

## 📁 Proje Yapısı

```
quant_engine/
├── config/              # Merkezi konfigürasyon (Pydantic + TOML)
├── data_pipeline/       # Offline storage ve veri doğrulama akışı
│   ├── fetcher.py       # Yahoo Finance veri çekici
│   ├── storage_manager.py # DuckDB + Parquet depolama
│   ├── data_validator.py  # Veri kalite kontrolü
│   └── pipeline.py      # Orkestratör
├── strategy/            # Strateji framework'ü ve SQLite persistence
├── workspace/           # Workspace JSON ve çoklu piyasa sembol çözümleme
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
