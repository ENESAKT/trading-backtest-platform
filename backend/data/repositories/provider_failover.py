"""
provider_failover.py — Provider karşılaştırma ve otomatik failover sistemi.

İki provider'dan aynı sembol/timeframe verisi çekildiğinde:
  - Son bar fiyatı, hacim ve timestamp farkları hesaplanır.
  - Fark belirlenen eşiği aştığında kalite olayı üretilir.
  - Birincil provider başarısız olursa yedek provider otomatik devreye girer.
  - Provider değişimi asla sessiz olmaz — her geçiş loglanır ve UI'ya iletilir.

Kullanım:
    from backend.data.repositories.provider_failover import ProviderFailover, ProviderResult

    failover = ProviderFailover(primary="yfinance", fallback="binance")
    result = await failover.fetch_with_failover(symbol="BTCUSDT", interval="1h", limit=200)
    # result.source_switched == True ise UI'da göster
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

_logger = logging.getLogger(__name__)

# ─── Eşikler ─────────────────────────────────────────────────────────────────

# Close fiyat farkı yüzdesi — bu değerin üstündeyse kalite uyarısı
PRICE_DIFF_THRESHOLD_PCT = 0.5

# Timestamp farkı (saniye) — bu değerin üstündeyse uyarı
TIMESTAMP_DIFF_THRESHOLD_S = 300  # 5 dakika

# Hacim farkı yüzdesi
VOLUME_DIFF_THRESHOLD_PCT = 20.0

# ─── Veri tipleri ────────────────────────────────────────────────────────────


@dataclass
class ProviderBar:
    """Tek bir provider'dan gelen son bar özeti."""
    provider: str
    symbol: str
    interval: str
    close: float
    volume: float
    timestamp_s: float   # Unix timestamp (saniye)
    raw_bars: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ProviderComparison:
    """İki provider arasındaki fark raporu."""
    primary: ProviderBar
    secondary: ProviderBar
    price_diff_pct: float
    volume_diff_pct: float
    timestamp_diff_s: float
    has_price_alert: bool
    has_volume_alert: bool
    has_timestamp_alert: bool

    @property
    def has_any_alert(self) -> bool:
        return self.has_price_alert or self.has_volume_alert or self.has_timestamp_alert

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_provider":   self.primary.provider,
            "secondary_provider": self.secondary.provider,
            "symbol":             self.primary.symbol,
            "interval":           self.primary.interval,
            "price_diff_pct":     round(self.price_diff_pct, 4),
            "volume_diff_pct":    round(self.volume_diff_pct, 4),
            "timestamp_diff_s":   round(self.timestamp_diff_s, 1),
            "has_price_alert":    self.has_price_alert,
            "has_volume_alert":   self.has_volume_alert,
            "has_timestamp_alert": self.has_timestamp_alert,
        }


@dataclass
class ProviderResult:
    """Failover sonucunda dönen veri paketi."""
    bars: list[dict[str, Any]]
    source: str                         # Kullanılan provider adı
    source_switched: bool = False       # Yedek devreye girdi mi?
    switched_from: str | None = None    # Başarısız birincil provider
    switch_reason: str | None = None    # Neden geçildi?
    comparison: ProviderComparison | None = None  # Karşılaştırma varsa


# ─── ProviderFailover ────────────────────────────────────────────────────────

FetchFn = Callable[[str, str, int], Awaitable[list[dict[str, Any]] | None]]


class ProviderFailover:
    """
    İki provider'ı karşılaştırır ve birincil başarısız olursa yedek kullanır.

    Args:
        primary:   Birincil provider adı (yfinance, binance, redis, vb.)
        fallback:  Yedek provider adı
        primary_fn:  Birincil fetch fonksiyonu: async (symbol, interval, limit) -> bars | None
        fallback_fn: Yedek fetch fonksiyonu

    Fetch fonksiyonları boş liste veya None döndürürse provider başarısız sayılır.
    """

    def __init__(
        self,
        primary: str,
        fallback: str,
        primary_fn: FetchFn | None = None,
        fallback_fn: FetchFn | None = None,
    ) -> None:
        self.primary = primary
        self.fallback = fallback
        self._primary_fn = primary_fn
        self._fallback_fn = fallback_fn

    def set_primary_fn(self, fn: FetchFn) -> None:
        self._primary_fn = fn

    def set_fallback_fn(self, fn: FetchFn) -> None:
        self._fallback_fn = fn

    # ─── Ana metot ───────────────────────────────────────────────────────────

    async def fetch_with_failover(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
    ) -> ProviderResult:
        """
        Birincil provider'dan veri çekmeyi dener; başarısız olursa yedek kullanır.
        Her iki sağlıklıysa karşılaştırma da yapılır.
        """
        primary_bars: list[dict[str, Any]] | None = None
        primary_error: str | None = None

        # ── Birincil dene ────────────────────────────────────────────────────
        if self._primary_fn:
            try:
                primary_bars = await self._primary_fn(symbol, interval, limit)
            except Exception as exc:
                primary_error = str(exc)
                _logger.warning(
                    "[ProviderFailover] Birincil provider '%s' başarısız: %s | %s/%s",
                    self.primary, exc, symbol, interval,
                )

        if primary_bars:
            # ── Karşılaştırma (isteğe bağlı, hata olsa da devam et) ─────────
            comparison = None
            if self._fallback_fn:
                try:
                    fallback_bars = await self._fallback_fn(symbol, interval, min(limit, 5))
                    if fallback_bars:
                        comparison = self._compare(symbol, interval, primary_bars, fallback_bars)
                        if comparison.has_any_alert:
                            self._emit_quality_event(comparison)
                except Exception as exc:
                    _logger.debug("[ProviderFailover] Karşılaştırma yedek çekimi başarısız: %s", exc)

            return ProviderResult(
                bars=primary_bars,
                source=self.primary,
                source_switched=False,
                comparison=comparison,
            )

        # ── Yedek devreye gir ────────────────────────────────────────────────
        if self._fallback_fn:
            try:
                fallback_bars = await self._fallback_fn(symbol, interval, limit)
                if fallback_bars:
                    reason = primary_error or "birincil provider boş yanıt döndürdü"
                    _logger.warning(
                        "[ProviderFailover] Yedek '%s' devreye girdi. Sebep: %s | %s/%s",
                        self.fallback, reason, symbol, interval,
                    )
                    return ProviderResult(
                        bars=fallback_bars,
                        source=self.fallback,
                        source_switched=True,
                        switched_from=self.primary,
                        switch_reason=reason,
                    )
            except Exception as exc:
                _logger.error(
                    "[ProviderFailover] Yedek provider '%s' de başarısız: %s | %s/%s",
                    self.fallback, exc, symbol, interval,
                )

        # ── Her iki provider başarısız ────────────────────────────────────────
        _logger.error(
            "[ProviderFailover] Tüm provider'lar başarısız: primary=%s fallback=%s | %s/%s",
            self.primary, self.fallback, symbol, interval,
        )
        return ProviderResult(bars=[], source="none", source_switched=False)

    # ─── Karşılaştırma ───────────────────────────────────────────────────────

    def _compare(
        self,
        symbol: str,
        interval: str,
        primary_bars: list[dict[str, Any]],
        secondary_bars: list[dict[str, Any]],
    ) -> ProviderComparison:
        p_last = primary_bars[-1]
        s_last = secondary_bars[-1]

        p_close  = float(p_last.get("close", 0) or 0)
        s_close  = float(s_last.get("close", 0) or 0)
        p_volume = float(p_last.get("volume", 0) or 0)
        s_volume = float(s_last.get("volume", 0) or 0)
        p_time   = self._to_unix_s(p_last.get("time") or p_last.get("ts") or p_last.get("timestamp"))
        s_time   = self._to_unix_s(s_last.get("time") or s_last.get("ts") or s_last.get("timestamp"))

        ref_price  = (p_close + s_close) / 2 or 1.0
        ref_volume = (p_volume + s_volume) / 2 or 1.0

        price_diff_pct   = abs(p_close - s_close) / ref_price * 100
        volume_diff_pct  = abs(p_volume - s_volume) / ref_volume * 100
        timestamp_diff_s = abs((p_time or 0) - (s_time or 0))

        p_bar = ProviderBar(
            provider=self.primary, symbol=symbol, interval=interval,
            close=p_close, volume=p_volume, timestamp_s=p_time or 0,
            raw_bars=primary_bars,
        )
        s_bar = ProviderBar(
            provider=self.fallback, symbol=symbol, interval=interval,
            close=s_close, volume=s_volume, timestamp_s=s_time or 0,
            raw_bars=secondary_bars,
        )

        return ProviderComparison(
            primary=p_bar,
            secondary=s_bar,
            price_diff_pct=price_diff_pct,
            volume_diff_pct=volume_diff_pct,
            timestamp_diff_s=timestamp_diff_s,
            has_price_alert=price_diff_pct > PRICE_DIFF_THRESHOLD_PCT,
            has_volume_alert=volume_diff_pct > VOLUME_DIFF_THRESHOLD_PCT,
            has_timestamp_alert=timestamp_diff_s > TIMESTAMP_DIFF_THRESHOLD_S,
        )

    @staticmethod
    def _to_unix_s(value: Any) -> float | None:
        if value is None:
            return None
        try:
            v = float(value)
            # Milisaniye mi?
            if v > 9_999_999_999:
                return v / 1000.0
            return v
        except (TypeError, ValueError):
            return None

    def _emit_quality_event(self, cmp: ProviderComparison) -> None:
        """Kalite olayını loglar (ve gelecekte ClickHouse'a yazılabilir)."""
        _logger.warning(
            "[ProviderFailover] Kalite uyarısı! %s/%s | fiyat_fark=%.2f%% hacim_fark=%.2f%% ts_fark=%.0fs "
            "| birincil=%s yedek=%s",
            cmp.primary.symbol, cmp.primary.interval,
            cmp.price_diff_pct, cmp.volume_diff_pct, cmp.timestamp_diff_s,
            self.primary, self.fallback,
        )


# ─── Global registry ─────────────────────────────────────────────────────────

class ProviderFailoverRegistry:
    """
    Birden fazla sembol/market için ProviderFailover instance'larını yönetir.

    Kullanım:
        registry = ProviderFailoverRegistry()
        registry.register("BTCUSDT", ProviderFailover("binance", "yfinance", ...))
        result = await registry.fetch("BTCUSDT", "1h", 200)
    """

    def __init__(self) -> None:
        self._registry: dict[str, ProviderFailover] = {}
        self._default: ProviderFailover | None = None

    def register(self, key: str, failover: ProviderFailover) -> None:
        self._registry[key] = failover

    def set_default(self, failover: ProviderFailover) -> None:
        self._default = failover

    def get(self, key: str) -> ProviderFailover | None:
        return self._registry.get(key) or self._default

    async def fetch(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
        *,
        key: str | None = None,
    ) -> ProviderResult:
        fo = self.get(key or symbol)
        if fo is None:
            _logger.warning("[ProviderFailoverRegistry] '%s' için kayıtlı failover yok", key or symbol)
            return ProviderResult(bars=[], source="none", source_switched=False)
        return await fo.fetch_with_failover(symbol, interval, limit)


# Singleton
provider_failover_registry = ProviderFailoverRegistry()
