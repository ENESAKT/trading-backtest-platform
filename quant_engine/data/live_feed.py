"""
PiyasaPilot canlı veri servis katmanı.

Bu modül yalnızca public/read-only piyasa verisi okur. API anahtarı, hesap bilgisi
veya emir gönderimi kullanmaz. Veri sağlayıcı hata verirse sahte veri üretmez;
üst katmana açık bir "Bağlantı Hatası" cevabı döndürür.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from quant_engine.data.provider_router import ProviderRouter
from quant_engine.workspace.json_store import WorkspaceJsonStore


@dataclass(frozen=True)
class DataMetadata:
    """Bir veri çekme işleminin izlenebilir metadata kaydı."""

    symbol: str
    normalized_symbol: str
    provider: str
    source: str
    fetched_at: str
    last_bar_at: str | None
    status: str
    read_only: bool = True
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SymbolSpec:
    """Frontend ve provider arasında kullanılan sembol çözümleme bilgisi."""

    symbol: str
    display_name: str
    provider: str
    source_symbol: str
    source: str
    market: str


DEFAULT_DASHBOARD_SYMBOLS: tuple[str, ...] = ("XU100", "USDTRY", "BTCUSDT", "XAUUSD")

_KNOWN_SYMBOLS: dict[str, SymbolSpec] = {
    "XU100": SymbolSpec(
        symbol="XU100",
        display_name="BIST 100",
        provider="yfinance",
        source_symbol="XU100.IS",
        source="Yahoo Finance",
        market="bist",
    ),
    "USDTRY": SymbolSpec(
        symbol="USDTRY",
        display_name="USD/TRY",
        provider="yfinance",
        source_symbol="USDTRY=X",
        source="Yahoo Finance",
        market="forex",
    ),
    "XAUUSD": SymbolSpec(
        symbol="XAUUSD",
        display_name="Altın Ons",
        provider="yfinance",
        source_symbol="GC=F",
        source="Yahoo Finance",
        market="commodity",
    ),
    "BTCUSDT": SymbolSpec(
        symbol="BTCUSDT",
        display_name="BTC/USDT",
        provider="ccxt",
        source_symbol="BTC/USDT",
        source="Binance Public API",
        market="crypto",
    ),
}


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC).replace(microsecond=0)


def iso_utc(value: dt.datetime | None = None) -> str:
    return (value or utc_now()).astimezone(dt.UTC).replace(microsecond=0).isoformat()


def normalize_symbol(symbol: str) -> str:
    """Kullanıcı sembolünü kanonik forma getir."""
    return (
        symbol.upper()
        .strip()
        .replace(" ", "")
        .replace("/", "")
        .replace("-", "")
        .replace(".IS", "")
    )


def _to_unix_seconds(value: Any) -> int:
    timestamp = value
    if hasattr(timestamp, "to_pydatetime"):
        timestamp = timestamp.to_pydatetime()
    if isinstance(timestamp, dt.date) and not isinstance(timestamp, dt.datetime):
        timestamp = dt.datetime.combine(timestamp, dt.time.min)
    if isinstance(timestamp, dt.datetime):
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=dt.UTC)
        else:
            timestamp = timestamp.astimezone(dt.UTC)
        return int(timestamp.timestamp())
    return int(timestamp)


def _to_iso_datetime(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime()
    if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
        value = dt.datetime.combine(value, dt.time.min)
    if isinstance(value, dt.datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=dt.UTC)
        else:
            value = value.astimezone(dt.UTC)
        return value.replace(microsecond=0).isoformat()
    return None


def resolve_symbol(symbol: str) -> SymbolSpec:
    """Sembolün hangi public provider ile okunacağını belirle."""
    clean = normalize_symbol(symbol)
    if clean in _KNOWN_SYMBOLS:
        return _KNOWN_SYMBOLS[clean]

    # USDT ile biten sembolleri Binance public market-data üzerinden oku.
    if clean.endswith("USDT") and len(clean) > 4:
        base = clean[:-4]
        return SymbolSpec(
            symbol=clean,
            display_name=f"{base}/USDT",
            provider="ccxt",
            source_symbol=f"{base}/USDT",
            source="Binance Public API",
            market="crypto",
        )

    # TL döviz çiftleri ve altın/emtia dışındaki semboller Yahoo tarafında denenir.
    if clean.endswith("TRY") and len(clean) == 6:
        return SymbolSpec(
            symbol=clean,
            display_name=f"{clean[:3]}/{clean[3:]}",
            provider="yfinance",
            source_symbol=f"{clean}=X",
            source="Yahoo Finance",
            market="forex",
        )

    return SymbolSpec(
        symbol=clean,
        display_name=clean,
        provider="yfinance",
        source_symbol=f"{clean}.IS",
        source="Yahoo Finance",
        market="bist",
    )


class LiveDataService:
    """ccxt ve yfinance ile read-only canlı/güncel veri sağlayan servis."""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self._ccxt_exchange = None
        self._provider_router = ProviderRouter()

    def fetch_chart(self, symbol: str, limit: int = 180) -> dict[str, Any]:
        spec = resolve_symbol(symbol)
        safe_limit = max(20, min(int(limit), 500))
        try:
            if spec.provider == "ccxt":
                return self._fetch_crypto_chart(spec, safe_limit)
            return self._fetch_yfinance_chart(spec, safe_limit)
        except Exception as exc:  # veri gelmezse sahte veri üretme
            return self._error_payload(spec, str(exc))

    def fetch_default_dashboard(self) -> dict[str, Any]:
        return {
            "symbols": [self.fetch_chart(symbol) for symbol in DEFAULT_DASHBOARD_SYMBOLS],
            "metadata": {
                "read_only": True,
                "fetched_at": iso_utc(),
                "message": "Varsayılan dashboard sembolleri gerçek veri sağlayıcılardan okunur.",
            },
        }

    _SUPPORTED_INTERVALS: tuple[str, ...] = (
        "1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w",
    )

    _CCXT_INTERVAL_MAP: dict[str, str] = {
        "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
        "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1w",
    }

    _YF_INTERVAL_MAP: dict[str, tuple[str, str]] = {
        "1m":  ("1m",  "1d"),
        "5m":  ("5m",  "5d"),
        "15m": ("15m", "5d"),
        "30m": ("30m", "1mo"),
        "1h":  ("60m", "1mo"),
        "4h":  ("1d",  "3mo"),
        "1d":  ("1d",  "1y"),
        "1w":  ("1wk", "5y"),
    }

    @staticmethod
    def _resolve_v2(raw_symbol: str) -> SymbolSpec:
        """Frontend'in ham (Yahoo / Binance native) sembolünü provider'a yönlendir.

        ``resolve_symbol`` v1 dashboard içindir ve normalize edip kanonik
        forma çevirir; v2 endpoint frontend'in gönderdiği native suffix'li
        sembolü ('THYAO.IS', 'USDTRY=X', 'GC=F', 'AAPL', 'BTCUSDT') olduğu
        gibi alır ve yine yfinance/ccxt'ye verir.
        """
        s = raw_symbol.strip().upper()
        if not s:
            raise ValueError("symbol_required")

        if s in ("XU100", "^XU100", "BIST100"):
            return SymbolSpec(
                symbol="XU100", display_name="BIST 100",
                provider="yfinance", source_symbol="XU100.IS",
                source="Yahoo Finance", market="bist",
            )

        # Crypto: *USDT (7+ char, alphanumeric, no Yahoo suffix)
        if (
            s.endswith("USDT")
            and len(s) >= 7
            and "=" not in s
            and "." not in s
            and s.replace("USDT", "").isalnum()
        ):
            base = s[:-4]
            return SymbolSpec(
                symbol=s, display_name=f"{base}/USDT",
                provider="ccxt", source_symbol=f"{base}/USDT",
                source="Binance Public API", market="crypto",
            )

        if (
            s.startswith("VIOP:")
            or s.startswith("F_")
            or s.startswith("O_")
            or s.startswith("VIP-")
            or s.startswith("VIOP_")
        ):
            return SymbolSpec(
                symbol=s, display_name=s.replace("VIOP:", ""),
                provider="viop", source_symbol=s,
                source="Borsa İstanbul VİOP lisanslı/veri sağlayıcı bağlantısı yok",
                market="viop",
            )

        if s.endswith("=X"):
            return SymbolSpec(
                symbol=s, display_name=s.replace("=X", ""),
                provider="yfinance", source_symbol=s,
                source="Yahoo Finance", market="fx",
            )

        if s.endswith("=F"):
            return SymbolSpec(
                symbol=s, display_name=s.replace("=F", ""),
                provider="yfinance", source_symbol=s,
                source="Yahoo Finance", market="commodity",
            )

        if s.endswith(".IS"):
            return SymbolSpec(
                symbol=s, display_name=s.replace(".IS", ""),
                provider="yfinance", source_symbol=s,
                source="Yahoo Finance", market="bist",
            )

        # US equity (suffix'siz, native yfinance — örn AAPL, MSFT, BRK-B)
        return SymbolSpec(
            symbol=s, display_name=s,
            provider="yfinance", source_symbol=s,
            source="Yahoo Finance", market="us_equity",
        )

    def fetch_candles(
        self, symbol: str, interval: str = "15m", limit: int = 500
    ) -> dict[str, Any]:
        """v2 endpoint için sembol/interval bazlı OHLCV döndürür.

        v1 ``fetch_chart`` sadece BIST için 5m hardcoded barlar veriyordu;
        bu method timeframe seçimi destekler ve frontend'in tarayıcıdan
        Binance/Yahoo'ya doğrudan çıkmasını gerektirmez.
        """
        if not symbol or not str(symbol).strip():
            return {
                "status": "error",
                "message": "Sembol zorunludur.",
                "bars": [],
                "quote": None,
                "metadata": {"error": "symbol_required", "read_only": True},
            }

        if interval not in self._SUPPORTED_INTERVALS:
            return {
                "status": "error",
                "message": f"Geçersiz interval: {interval}",
                "bars": [],
                "quote": None,
                "metadata": {
                    "error": "invalid_interval",
                    "read_only": True,
                    "supported": list(self._SUPPORTED_INTERVALS),
                },
            }

        try:
            safe_limit = int(limit)
        except (TypeError, ValueError):
            safe_limit = 500
        safe_limit = max(20, min(safe_limit, 1000))

        try:
            spec = self._resolve_v2(symbol)
        except ValueError:
            return {
                "status": "error",
                "message": "Sembol zorunludur.",
                "bars": [],
                "quote": None,
                "metadata": {"error": "symbol_required", "read_only": True},
            }

        try:
            result = self._provider_router.fetch_candles(
                spec.symbol,
                timeframe=interval,
                limit=safe_limit,
            )
            return result.to_legacy_payload()
        except Exception as exc:
            return self._error_payload(spec, str(exc))

    def provider_health(self) -> dict[str, Any]:
        """Veri sağlayıcı sağlık bilgisini API için JSON'a hazır döndür."""
        return {
            "status": "ok",
            "fetched_at": iso_utc(),
            "providers": [h.to_dict() for h in self._provider_router.health()],
        }

    def _fetch_crypto_candles(
        self, spec: SymbolSpec, interval: str, limit: int
    ) -> dict[str, Any]:
        exchange = self._get_ccxt_exchange()
        tf = self._CCXT_INTERVAL_MAP[interval]
        ohlcv = exchange.fetch_ohlcv(spec.source_symbol, timeframe=tf, limit=limit)
        if not ohlcv:
            return self._error_payload(
                spec, "Bağlantı Hatası: Binance public veri boş döndü."
            )

        ticker = exchange.fetch_ticker(spec.source_symbol)
        bars = [
            {
                "time": int(row[0] / 1000),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
            }
            for row in ohlcv
        ]
        last_bar_time = dt.datetime.fromtimestamp(bars[-1]["time"], tz=dt.UTC)
        last_price = ticker.get("last") or bars[-1]["close"]
        fetched_at = iso_utc()
        metadata = DataMetadata(
            symbol=spec.symbol,
            normalized_symbol=spec.symbol,
            provider="ccxt",
            source=spec.source,
            fetched_at=fetched_at,
            last_bar_at=iso_utc(last_bar_time),
            status="live",
        )
        return {
            "symbol": spec.symbol,
            "display_name": spec.display_name,
            "market": spec.market,
            "interval": interval,
            "status": "ok",
            "message": "",
            "bars": bars,
            "quote": {
                "last": float(last_price) if last_price is not None else bars[-1]["close"],
                "timestamp": fetched_at,
            },
            "metadata": metadata.to_dict(),
        }

    def _fetch_yfinance_candles(
        self, spec: SymbolSpec, interval: str, limit: int
    ) -> dict[str, Any]:
        import yfinance as yf

        yf_interval, yf_range = self._YF_INTERVAL_MAP[interval]
        ticker = yf.Ticker(spec.source_symbol)
        try:
            frame = ticker.history(
                period=yf_range, interval=yf_interval, timeout=self.timeout
            )
        except TypeError:
            frame = ticker.history(period=yf_range, interval=yf_interval)

        if frame.empty:
            return self._error_payload(
                spec, f"Bağlantı Hatası: {spec.display_name} için veri alınamadı."
            )

        frame = frame.reset_index().tail(limit)
        time_column = "Datetime" if "Datetime" in frame.columns else "Date"
        bars: list[dict[str, float | int]] = []
        for _, row in frame.iterrows():
            close = row.get("Close")
            open_price = row.get("Open")
            high = row.get("High")
            low = row.get("Low")
            if close is None or str(close) == "nan":
                continue
            bars.append(
                {
                    "time": _to_unix_seconds(row[time_column]),
                    "open": float(open_price if open_price == open_price else close),
                    "high": float(high if high == high else close),
                    "low": float(low if low == low else close),
                    "close": float(close),
                    "volume": float(row.get("Volume") or 0),
                }
            )

        if not bars:
            return self._error_payload(
                spec, f"Bağlantı Hatası: {spec.display_name} için geçerli fiyat satırı yok."
            )

        last_bar_at = _to_iso_datetime(frame.iloc[-1][time_column])
        fetched_at = iso_utc()
        metadata = DataMetadata(
            symbol=spec.symbol,
            normalized_symbol=spec.symbol,
            provider="yfinance",
            source=spec.source,
            fetched_at=fetched_at,
            last_bar_at=last_bar_at,
            status="live",
        )
        return {
            "symbol": spec.symbol,
            "display_name": spec.display_name,
            "market": spec.market,
            "interval": interval,
            "status": "ok",
            "message": "",
            "bars": bars,
            "quote": {
                "last": bars[-1]["close"],
                "timestamp": fetched_at,
            },
            "metadata": metadata.to_dict(),
        }

    def _get_ccxt_exchange(self):
        if self._ccxt_exchange is None:
            import ccxt

            self._ccxt_exchange = ccxt.binance(
                {
                    "enableRateLimit": True,
                    "timeout": self.timeout * 1000,
                    "options": {"defaultType": "spot"},
                }
            )
        return self._ccxt_exchange

    def _fetch_crypto_chart(self, spec: SymbolSpec, limit: int) -> dict[str, Any]:
        exchange = self._get_ccxt_exchange()
        ohlcv = exchange.fetch_ohlcv(spec.source_symbol, timeframe="1m", limit=limit)
        if not ohlcv:
            return self._error_payload(spec, "Bağlantı Hatası: Binance public veri boş döndü.")

        ticker = exchange.fetch_ticker(spec.source_symbol)
        bars = [
            {
                "time": int(row[0] / 1000),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
            }
            for row in ohlcv
        ]
        last_bar_time = dt.datetime.fromtimestamp(bars[-1]["time"], tz=dt.UTC)
        last_price = ticker.get("last") or bars[-1]["close"]
        fetched_at = iso_utc()
        metadata = DataMetadata(
            symbol=spec.symbol,
            normalized_symbol=spec.symbol,
            provider="ccxt",
            source=spec.source,
            fetched_at=fetched_at,
            last_bar_at=iso_utc(last_bar_time),
            status="live",
        )
        return {
            "symbol": spec.symbol,
            "display_name": spec.display_name,
            "market": spec.market,
            "status": "ok",
            "message": "",
            "bars": bars,
            "quote": {
                "last": float(last_price) if last_price is not None else bars[-1]["close"],
                "timestamp": fetched_at,
            },
            "metadata": metadata.to_dict(),
        }

    def _fetch_yfinance_chart(self, spec: SymbolSpec, limit: int) -> dict[str, Any]:
        import yfinance as yf

        ticker = yf.Ticker(spec.source_symbol)
        try:
            frame = ticker.history(period="5d", interval="5m", timeout=self.timeout)
        except TypeError:
            frame = ticker.history(period="5d", interval="5m")

        if frame.empty:
            try:
                frame = ticker.history(period="1mo", interval="1d", timeout=self.timeout)
            except TypeError:
                frame = ticker.history(period="1mo", interval="1d")

        if frame.empty:
            message = f"Bağlantı Hatası: {spec.display_name} için veri alınamadı."
            return self._error_payload(spec, message)

        frame = frame.reset_index().tail(limit)
        time_column = "Datetime" if "Datetime" in frame.columns else "Date"
        bars: list[dict[str, float | int]] = []
        for _, row in frame.iterrows():
            close = row.get("Close")
            open_price = row.get("Open")
            high = row.get("High")
            low = row.get("Low")
            if close is None or str(close) == "nan":
                continue
            bars.append(
                {
                    "time": _to_unix_seconds(row[time_column]),
                    "open": float(open_price if open_price == open_price else close),
                    "high": float(high if high == high else close),
                    "low": float(low if low == low else close),
                    "close": float(close),
                    "volume": float(row.get("Volume") or 0),
                }
            )

        if not bars:
            message = f"Bağlantı Hatası: {spec.display_name} için geçerli fiyat satırı yok."
            return self._error_payload(spec, message)

        last_bar_at = _to_iso_datetime(frame.iloc[-1][time_column])
        fetched_at = iso_utc()
        metadata = DataMetadata(
            symbol=spec.symbol,
            normalized_symbol=spec.symbol,
            provider="yfinance",
            source=spec.source,
            fetched_at=fetched_at,
            last_bar_at=last_bar_at,
            status="live",
        )
        return {
            "symbol": spec.symbol,
            "display_name": spec.display_name,
            "market": spec.market,
            "status": "ok",
            "message": "",
            "bars": bars,
            "quote": {
                "last": bars[-1]["close"],
                "timestamp": fetched_at,
            },
            "metadata": metadata.to_dict(),
        }

    def _error_payload(self, spec: SymbolSpec, error: str) -> dict[str, Any]:
        metadata = DataMetadata(
            symbol=spec.symbol,
            normalized_symbol=spec.symbol,
            provider=spec.provider,
            source=spec.source,
            fetched_at=iso_utc(),
            last_bar_at=None,
            status="error",
            error=error or "Bağlantı Hatası",
        )
        return {
            "symbol": spec.symbol,
            "display_name": spec.display_name,
            "market": spec.market,
            "status": "error",
            "message": "Bağlantı Hatası",
            "bars": [],
            "quote": None,
            "metadata": metadata.to_dict(),
        }


class PaperTradingRecorder:
    """Gerçek son fiyatı kullanarak yalnızca sanal paper trade kaydı oluşturur."""

    def __init__(
        self,
        data_service: LiveDataService | None = None,
        workspace_path: str | Path = "data/workspaces/workspace.json",
    ):
        self.data_service = data_service or LiveDataService()
        self.store = WorkspaceJsonStore(workspace_path)

    def record_signal(self, payload: dict[str, Any]) -> dict[str, Any]:
        symbol = str(payload.get("symbol") or "").strip()
        side = str(payload.get("side") or "").strip().lower()
        strategy = str(payload.get("strategy") or "Manuel Paper Sinyali").strip()
        bot_name = str(payload.get("bot_name") or "").strip()
        virtual_balance = str(payload.get("virtual_balance") or "").strip()

        if not symbol:
            raise ValueError("Sembol zorunludur.")
        if side not in {"buy", "sell"}:
            raise ValueError("Sinyal yönü buy veya sell olmalıdır.")

        chart = self.data_service.fetch_chart(symbol, limit=40)
        if chart.get("status") != "ok" or not chart.get("quote"):
            error = chart.get("metadata", {}).get("error") or "Bağlantı Hatası"
            raise RuntimeError(error)

        price = chart["quote"]["last"]
        now = iso_utc()
        document = self.store.load()
        trades = list(document.get("paper_trades", []))
        trade = {
            "id": f"paper-{now.replace(':', '').replace('-', '')}",
            "mode": "paper",
            "status": "open_virtual",
            "read_only": True,
            "symbol": chart["symbol"],
            "display_name": chart["display_name"],
            "side": side,
            "strategy": strategy,
            "bot_name": bot_name,
            "virtual_balance": virtual_balance,
            "entry_price": price,
            "price_source": chart["metadata"]["source"],
            "price_fetched_at": chart["metadata"]["fetched_at"],
            "created_at": now,
            "note": (
                "Gerçek piyasa fiyatıyla oluşturulan sanal paper trade kaydıdır; "
                "canlı emir değildir."
            ),
        }
        trades.insert(0, trade)
        document["paper_trades"] = trades
        metadata = dict(document.get("data_metadata", {}))
        metadata[chart["symbol"]] = chart["metadata"]
        document["data_metadata"] = metadata
        self.store.save(document)
        return trade
