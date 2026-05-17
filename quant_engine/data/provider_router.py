"""Piyasa sembolünü uygun gerçek veri sağlayıcıya yönlendir."""

from __future__ import annotations

from typing import Any

from quant_engine.data.market_data import MarketDataHealth, MarketDataResult
from quant_engine.data.providers.bist_provider import BistMarketDataProvider
from quant_engine.data.providers.crypto_provider import CryptoMarketDataProvider
from quant_engine.data.providers.viop_provider import ViopMarketDataProvider

# ABD büyük-cap hisseleri — is_bist_symbol()'un yanlışlıkla BIST sanmasını önler.
# Bu liste, 2-6 harf olan saf alfa kodlarını kapsar.
_US_EQUITY_TICKERS: frozenset[str] = frozenset({
    # Mega-cap tech
    "AAPL", "MSFT", "NVDA", "GOOGL", "GOOG", "AMZN", "META", "TSLA",
    "AVGO", "ORCL", "ADBE", "CRM", "INTC", "AMD", "QCOM", "TXN",
    "AMAT", "MU", "LRCX", "KLAC", "SNPS", "CDNS", "MRVL",
    # Finance
    "BRK", "JPM", "BAC", "WFC", "GS", "MS", "BLK", "C", "USB",
    "AXP", "COF", "SCHW", "ICE", "CME", "CB", "MMC",
    # Health
    "LLY", "JNJ", "UNH", "PFE", "ABBV", "MRK", "TMO", "ABT",
    "DHR", "BMY", "AMGN", "GILD", "ISRG", "MDT", "SYK",
    # Consumer
    "WMT", "HD", "COST", "PG", "KO", "PEP", "MCD", "SBUX",
    "NKE", "TGT", "LOW", "EL", "CL", "KMB",
    # Industrial / Energy
    "XOM", "CVX", "COP", "EOG", "SLB", "PXD",
    "BA", "CAT", "GE", "HON", "MMM", "RTX", "LMT", "NOC",
    "UPS", "FDX", "DE", "EMR",
    # Other
    "V", "MA", "PYPL", "NFLX", "DIS", "CMCSA", "T", "VZ",
    "NEE", "DUK", "SO", "D", "AEP", "EXC",
    "SPY", "QQQ", "IWM", "DIA", "GLD", "SLV", "USO",
})


class ProviderRouter:
    def __init__(
        self,
        bist_provider: BistMarketDataProvider | None = None,
        viop_provider: ViopMarketDataProvider | None = None,
        crypto_provider: CryptoMarketDataProvider | None = None,
    ):
        self.bist_provider = bist_provider or BistMarketDataProvider()
        self.viop_provider = viop_provider or ViopMarketDataProvider()
        self.crypto_provider = crypto_provider or CryptoMarketDataProvider()

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        return symbol.strip().upper().replace(" ", "")

    @classmethod
    def is_crypto_symbol(cls, symbol: str) -> bool:
        clean = cls.normalize_symbol(symbol).replace("/", "").replace("-", "")
        return clean.endswith("USDT") and len(clean) >= 7 and "=" not in clean

    @classmethod
    def is_viop_symbol(cls, symbol: str) -> bool:
        clean = cls.normalize_symbol(symbol)
        return (
            clean.startswith("VIOP:")
            or clean.startswith("F_")
            or clean.startswith("O_")
            or clean.startswith("VIP-")
            or clean.startswith("VIOP_")
        )

    @classmethod
    def is_bist_symbol(cls, symbol: str) -> bool:
        clean = cls.normalize_symbol(symbol)
        if clean in {"XU100", "^XU100", "BIST100"}:
            return True
        if clean.endswith(".IS"):
            return True
        if clean.endswith("=X") or clean.endswith("=F"):
            return True
        # Saf alfa kodu (2-6 harf) → BIST hissesi kabul et,
        # ama bilinen ABD hisselerini dışla
        if clean.isalpha() and 2 <= len(clean) <= 6:
            return clean not in _US_EQUITY_TICKERS
        return False

    def provider_for_symbol(self, symbol: str) -> Any:
        if self.is_viop_symbol(symbol):
            return self.viop_provider
        if self.is_crypto_symbol(symbol):
            return self.crypto_provider
        if self.is_bist_symbol(symbol):
            return self.bist_provider
        return self.bist_provider

    def fetch_candles(
        self,
        symbol: str,
        timeframe: str = "15m",
        limit: int = 500,
    ) -> MarketDataResult:
        provider = self.provider_for_symbol(symbol)
        return provider.fetch_ohlcv(symbol, timeframe, limit)

    def health(self) -> list[MarketDataHealth]:
        return [
            self.bist_provider.health(),
            self.viop_provider.health(),
            self.crypto_provider.health(),
        ]
