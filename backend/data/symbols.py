"""Worker'lar için varsayılan sembol kayıt defteri (Sprint 1).

Sprint 2'de Market Explorer tam BIST 100 + büyük kripto + tüm FX/emtia
ekleyecek; bu modül foundation seti olarak küçük ama temsili bir liste sunar.
Frontend ham (native) sembol formatı kullanılır → cache key = bu string.
"""

from __future__ import annotations

# Binance WS kline stream'ine subscribe edilecek kripto pariteleri.
# Frontend ``BTCUSDT`` formatıyla gönderir, /api/v2/candles aynı string ile
# yazar; worker da aynı kanonik form kullanmalı.
CRYPTO_WS_SYMBOLS: tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
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

# BIST hisseler (yfinance .IS suffix). Sprint 2'de tam BIST 100'e genişler.
BIST_STOCKS: tuple[str, ...] = (
    "THYAO.IS",
    "GARAN.IS",
    "AKBNK.IS",
    "ASELS.IS",
    "EREGL.IS",
    "TUPRS.IS",
    "BIMAS.IS",
    "KCHOL.IS",
    "SISE.IS",
    "FROTO.IS",
)

# Worker varsayılan timeframe'i — cache cache-aside ile aynı interval.
DEFAULT_INTERVAL: str = "15m"
