"""Worker'lar için varsayılan sembol kayıt defteri (Sprint 1).

Sprint 2'de Market Explorer tam BIST 100 + büyük kripto + tüm FX/emtia
ekleyecek; bu modül foundation seti olarak küçük ama temsili bir liste sunar.
Frontend ham (native) sembol formatı kullanılır → cache key = bu string.
"""

from __future__ import annotations

# Binance WS kline stream'ine subscribe edilecek kripto pariteleri.
# Frontend ``BTCUSDT`` formatıyla gönderir, /api/v2/candles aynı string ile
# yazar; worker da aynı kanonik form kullanmalı.
# Frontend ``constants/symbols.ts::CRYPTO_SYMBOLS`` ile birebir senkron —
# QuoteStream tüm 10 paritede live update versin.
CRYPTO_WS_SYMBOLS: tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "AVAXUSDT",
    "DOTUSDT",
    "ADAUSDT",
    "DOGEUSDT",
    "MATICUSDT",
)

# yfinance üzerinden çekilen BIST endeks + FX + emtia.
# /api/v2/candles ``_resolve_v2`` ile aynı kanonik form (XU100 → XU100.IS).
YAHOO_INDEX_FX_COMMODITY: tuple[str, ...] = (
    "XU100",      # BIST 100 endeks
    "USDTRY=X",   # USD/TRY
    "EURTRY=X",   # EUR/TRY
    "GC=F",       # Altın futures
    "CL=F",       # Brent petrol futures
    "SI=F",       # Gümüş futures
)

# BIST hisseler (yfinance .IS suffix). Frontend ``BIST30`` listesiyle birebir
# senkron; arka plan ısıtması için worker bu seti 60s'de bir tarar (~30 req/dk,
# yfinance limiti 60/dk altında). Tam BIST 100 worker setine geçiş Sprint 2.7
# yfinance batch download eklenince yapılacak; o zamana kadar BIST 100'ün
# kalan ~50 sembolü ``/api/v2/candles`` üzerinden on-demand cache miss ile
# çekilir.
BIST_STOCKS: tuple[str, ...] = (
    "AKBNK.IS",   # Akbank
    "ARCLK.IS",   # Arçelik
    "ASELS.IS",   # Aselsan
    "BIMAS.IS",   # BİM
    "DOHOL.IS",   # Doğan Holding
    "EKGYO.IS",   # Emlak Konut GYO
    "ENKAI.IS",   # Enka İnşaat
    "EREGL.IS",   # Ereğli Demir Çelik
    "FROTO.IS",   # Ford Otosan
    "GARAN.IS",   # Garanti BBVA
    "HALKB.IS",   # Halkbank
    "ISCTR.IS",   # İş Bankası C
    "KCHOL.IS",   # Koç Holding
    "KOZAL.IS",   # Koza Altın
    "KRDMD.IS",   # Kardemir D
    "MAVI.IS",    # Mavi Giyim
    "PETKM.IS",   # Petkim
    "PGSUS.IS",   # Pegasus
    "SAHOL.IS",   # Sabancı Holding
    "SASA.IS",    # SASA Polyester
    "SISE.IS",    # Şişe Cam
    "TAVHL.IS",   # TAV
    "TCELL.IS",   # Turkcell
    "THYAO.IS",   # Türk Hava Yolları
    "TOASO.IS",   # Tofaş
    "TTKOM.IS",   # Türk Telekom
    "TUPRS.IS",   # Tüpraş
    "VAKBN.IS",   # Vakıfbank
    "VESTL.IS",   # Vestel
    "YKBNK.IS",   # Yapı Kredi
)

# Worker varsayılan timeframe'i — cache cache-aside ile aynı interval.
DEFAULT_INTERVAL: str = "15m"
