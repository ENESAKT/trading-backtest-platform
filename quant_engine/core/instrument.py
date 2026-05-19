"""
Quant Engine — Enstrüman Modelleri

Hisse senedi ve vadeli işlem kontratları için enstrüman tanımları.
Core katmanında olduğu için dış bağımlılık yok.
"""

from __future__ import annotations

from dataclasses import dataclass

from quant_engine.core.protocols import AssetClass, Market


@dataclass(frozen=True)
class Instrument:
    """Temel enstrüman modeli."""
    symbol: str
    name: str = ""
    market: Market = Market.BIST
    asset_class: AssetClass = AssetClass.EQUITY
    currency: str = "TRY"

    def __str__(self) -> str:
        return f"{self.symbol} ({self.market.value})"


@dataclass(frozen=True)
class EquityInstrument(Instrument):
    """BIST hisse senedi."""
    lot_size: int = 1
    tick_size: float = 0.01
    isin: str = ""
    sector: str = ""

    def __post_init__(self):
        # frozen=True olduğu için object.__setattr__ kullan
        if not self.name:
            object.__setattr__(self, "name", self.symbol)


@dataclass(frozen=True)
class FuturesInstrument(Instrument):
    """VİOP vadeli işlem kontratı."""
    asset_class: AssetClass = AssetClass.FUTURES
    market: Market = Market.VIOP
    contract_multiplier: float = 1.0
    tick_size: float = 0.01
    tick_value: float = 0.0
    lot_size: int = 1
    expiry: str = ""  # "2024-08" formatında
    underlying: str = ""  # Dayanak varlık sembolü

    @property
    def contract_code(self) -> str:
        """Kontrat kodu: F_XU030_2408"""
        if self.expiry:
            return f"{self.symbol}_{self.expiry.replace('-', '')}"
        return self.symbol
