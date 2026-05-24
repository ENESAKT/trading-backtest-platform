"""BIST lisanslı feed ve FX/emtia için public veri sağlayıcı.

BIST fiyat/grafik verisi lisanslı HTTP feed yapılandırılmadan açılmaz.
FX/emtia sembolleri için Yahoo Finance best-effort public okuma korunur.
"""

from __future__ import annotations

from typing import Any

from quant_engine.data.market_data import (
    MarketDataHealth,
    MarketDataProviderType,
    MarketDataResult,
    MarketDataStatus,
    utc_iso,
)
from quant_engine.data.providers.http_ohlcv import (
    configured_header,
    configured_template,
    fetch_http_ohlcv,
)

try:
    from backend.data.symbols import BIST_STOCKS
except Exception:  # pragma: no cover - provider tek başına da import edilebilsin
    BIST_STOCKS = ()

_BIST_CODES = {item.replace(".IS", "") for item in BIST_STOCKS}


class BistMarketDataProvider:
    name = "bist_license_pending"
    source = "BIST lisanslı veri sağlayıcı bağlantısı bekleniyor"
    yf_name = "yfinance_public"
    yf_source = "Yahoo Finance (FX/emtia best-effort public)"
    http_name = "bist_http"

    _INTERVAL_MAP: dict[str, tuple[str, str]] = {
        "1m": ("1m", "1d"),
        "5m": ("5m", "5d"),
        "15m": ("15m", "5d"),
        "30m": ("30m", "1mo"),
        "1h": ("60m", "1mo"),
        "4h": ("1d", "3mo"),
        "1d": ("1d", "1y"),
        "1w": ("1wk", "5y"),
    }

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.last_success_at: str | None = None
        self.last_error: str | None = None

    @staticmethod
    def _source_symbol(symbol: str) -> tuple[str, str, str]:
        clean = symbol.strip().upper().replace(" ", "")
        if clean in {"XU100", "^XU100", "BIST100"}:
            return "XU100", "XU100.IS", "BIST 100"
        if clean.endswith("=X"):
            return clean, clean, clean.replace("=X", "")
        if clean.endswith("=F"):
            return clean, clean, clean.replace("=F", "")
        if clean.endswith(".IS"):
            canonical = clean
            display = clean[:-3]
            return canonical, clean, display
        if clean in _BIST_CODES:
            return f"{clean}.IS", f"{clean}.IS", clean
        if clean.isalpha():
            return clean, clean, clean
        canonical = clean
        return f"{canonical}.IS", f"{canonical}.IS", canonical

    @staticmethod
    def _market_for_source(source_symbol: str) -> str:
        if source_symbol.endswith("=X"):
            return "fx"
        if source_symbol.endswith("=F"):
            return "commodity"
        if not source_symbol.endswith(".IS"):
            return "us_equity"
        return "bist"

    def _load_history(self, source_symbol: str, yf_interval: str, yf_period: str) -> Any:
        import yfinance as yf

        ticker = yf.Ticker(source_symbol)
        try:
            return ticker.history(
                period=yf_period,
                interval=yf_interval,
                timeout=self.timeout,
            )
        except TypeError:
            return ticker.history(period=yf_period, interval=yf_interval)

    def _fetch_configured_http(
        self,
        canonical: str,
        timeframe: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        template = configured_template("BIST_HTTP_URL_TEMPLATE")
        if not template:
            return []
        return fetch_http_ohlcv(
            template,
            canonical,
            timeframe,
            limit,
            self.timeout,
            configured_header("BIST_HTTP_AUTH_HEADER"),
        )

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> MarketDataResult:
        canonical, source_symbol, display = self._source_symbol(symbol)
        market = self._market_for_source(source_symbol)
        yf_interval, yf_period = self._INTERVAL_MAP.get(timeframe, ("15m", "5d"))
        timestamp = utc_iso()
        http_template = configured_template("BIST_HTTP_URL_TEMPLATE")

        if http_template:
            try:
                bars = self._fetch_configured_http(canonical, timeframe, limit)
            except Exception as exc:  # noqa: BLE001
                self.last_error = f"{type(exc).__name__}: {exc}"
                bars = []
            if bars:
                self.last_success_at = timestamp
                self.last_error = None
                return MarketDataResult(
                    symbol=canonical,
                    market=market,
                    timeframe=timeframe,
                    data=bars,
                    source="Configured BIST HTTP feed",
                    is_real=True,
                    status=MarketDataStatus.OK,
                    timestamp=timestamp,
                    provider_name=self.http_name,
                    display_name=display,
                )

        if market == "bist":
            if http_template:
                self.last_error = self.last_error or "BIST HTTP feed veri döndürmedi."
                return MarketDataResult(
                    symbol=canonical,
                    market=market,
                    timeframe=timeframe,
                    data=[],
                    source="Configured BIST HTTP feed",
                    is_real=False,
                    status=MarketDataStatus.NO_DATA,
                    timestamp=timestamp,
                    error=self.last_error,
                    provider_name=self.http_name,
                    display_name=display,
                )
            self.last_error = (
                "BIST verileri lisanslı veri sağlayıcı bağlantısı tamamlanana kadar kapalıdır."
            )
            return MarketDataResult(
                symbol=canonical,
                market=market,
                timeframe=timeframe,
                data=[],
                source=self.source,
                is_real=False,
                status=MarketDataStatus.NOT_CONFIGURED,
                timestamp=timestamp,
                error=self.last_error,
                provider_name=self.name,
                display_name=display,
            )

        try:
            frame = self._load_history(source_symbol, yf_interval, yf_period)
        except Exception as exc:  # noqa: BLE001
            self.last_error = f"{type(exc).__name__}: {exc}"
            return MarketDataResult(
                symbol=canonical,
                market=market,
                timeframe=timeframe,
                data=[],
                source=self.yf_source,
                is_real=False,
                status=MarketDataStatus.ERROR,
                timestamp=timestamp,
                error="Public yfinance veri sağlayıcı hatası.",
                provider_name=self.yf_name,
                display_name=display,
            )

        if frame is None or getattr(frame, "empty", True):
            self.last_error = f"{display} için veri bulunamadı."
            return MarketDataResult(
                symbol=canonical,
                market=market,
                timeframe=timeframe,
                data=[],
                source=self.yf_source,
                is_real=False,
                status=MarketDataStatus.NO_DATA,
                timestamp=timestamp,
                error=self.last_error,
                provider_name=self.yf_name,
                display_name=display,
            )

        frame = frame.reset_index().tail(max(1, int(limit)))
        time_col = "Datetime" if "Datetime" in frame.columns else "Date"
        bars: list[dict[str, Any]] = []
        for _, row in frame.iterrows():
            close = row.get("Close")
            if close is None or close != close:
                continue
            open_price = row.get("Open")
            high = row.get("High")
            low = row.get("Low")
            ts_value = row[time_col]
            if hasattr(ts_value, "to_pydatetime"):
                ts_value = ts_value.to_pydatetime()
            if hasattr(ts_value, "timestamp"):
                if ts_value.tzinfo is None:
                    import datetime as dt

                    ts_value = ts_value.replace(tzinfo=dt.timezone.utc)
                ts = int(ts_value.timestamp())
            else:
                ts = int(ts_value)
            bars.append({
                "time": ts,
                "open": float(open_price if open_price == open_price else close),
                "high": float(high if high == high else close),
                "low": float(low if low == low else close),
                "close": float(close),
                "volume": float(row.get("Volume") or 0),
            })

        if not bars:
            self.last_error = f"{display} için geçerli fiyat satırı yok."
            return MarketDataResult(
                symbol=canonical,
                market=market,
                timeframe=timeframe,
                data=[],
                source=self.yf_source,
                is_real=False,
                status=MarketDataStatus.NO_DATA,
                timestamp=timestamp,
                error=self.last_error,
                provider_name=self.yf_name,
                display_name=display,
            )

        self.last_success_at = timestamp
        self.last_error = None
        return MarketDataResult(
            symbol=canonical,
            market=market,
            timeframe=timeframe,
            data=bars,
            source=self.yf_source,
            is_real=False,
            status=MarketDataStatus.OK,
            timestamp=timestamp,
            provider_name=self.yf_name,
            display_name=display,
        )

    def health(self) -> MarketDataHealth:
        http_configured = bool(configured_template("BIST_HTTP_URL_TEMPLATE"))
        last_error = self.last_error
        if not http_configured and not last_error:
            last_error = "BIST lisanslı veri sağlayıcı bağlantısı bekleniyor."
        return MarketDataHealth(
            provider_name=self.http_name if http_configured else self.name,
            provider_type=MarketDataProviderType.BIST,
            active=http_configured,
            configured=http_configured,
            is_real=http_configured,
            supported_markets=["bist", "fx", "commodity", "us_equity"],
            last_success_at=self.last_success_at,
            last_error=last_error,
            source="Configured BIST HTTP feed" if http_configured else self.source,
        )
