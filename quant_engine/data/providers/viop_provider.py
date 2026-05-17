"""VİOP veri sağlayıcı.

Lisanslı/resmi VIOP_HTTP_URL_TEMPLATE yapılandırılmışsa o endpoint kullanılır.
Yapılandırılmamışsa, VİOP kontratının dayanak varlığından proxy OHLCV verisi
döndürülür (is_real=False, kaynak açıkça belirtilir).

Proxy eşlemeleri:
    Endeks vadeli  → XU100.IS  (Yahoo Finance BIST 100)
    Kur vadeli     → USDTRY=X / EURTRY=X (Yahoo FX)
    Altın vadeli   → GC=F (Yahoo Gold)
    Brent vadeli   → BZ=F (Yahoo Brent)
    Hisse vadeli   → <HİSSE>.IS (Yahoo BIST hissesi)
"""

from __future__ import annotations

import datetime as dt
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

# ─── Dayanak Varlık Eşleme Tablosu ────────────────────────────────────────────
# VİOP sembol → Yahoo Finance dayanak sembolü
_PROXY_UNDERLYING: dict[str, str] = {
    # Endeks vadeli
    "VIOP:XU030": "XU100.IS",
    "VIOP:XU100": "XU100.IS",
    "F_XU030": "XU100.IS",
    "F_XU100": "XU100.IS",
    "VIOP_XU030": "XU100.IS",
    "VIOP_XU100": "XU100.IS",
    # Döviz vadeli
    "VIOP:USDTRY": "USDTRY=X",
    "F_USDTRY": "USDTRY=X",
    "VIOP:EURTRY": "EURTRY=X",
    "F_EURTRY": "EURTRY=X",
    "VIOP:GBPTRY": "GBPTRY=X",
    "F_GBPTRY": "GBPTRY=X",
    # Altın / Emtia vadeli
    "VIOP:XAUTRY": "GC=F",
    "F_XAUTRY": "GC=F",
    "VIOP:XAGUSD": "SI=F",
    "F_XAGUSD": "SI=F",
    "VIOP:BRENT": "BZ=F",
    "F_BRENT": "BZ=F",
    "VIOP:WTI": "CL=F",
    "F_WTI": "CL=F",
    # Hisse vadeli (BIST Büyük Cap)
    "F_GARAN": "GARAN.IS",
    "F_THYAO": "THYAO.IS",
    "F_AKBNK": "AKBNK.IS",
    "F_EREGL": "EREGL.IS",
    "F_SISE": "SISE.IS",
    "F_KCHOL": "KCHOL.IS",
    "F_TUPRS": "TUPRS.IS",
    "F_ISCTR": "ISCTR.IS",
    "F_TCELL": "TCELL.IS",
    "F_BIMAS": "BIMAS.IS",
    "F_PGSUS": "PGSUS.IS",
    "F_FROTO": "FROTO.IS",
    "F_ASELS": "ASELS.IS",
    "F_TOASO": "TOASO.IS",
    "F_KOZAL": "KOZAL.IS",
    "F_SAHOL": "SAHOL.IS",
    "F_VESTL": "VESTL.IS",
    "F_HALKB": "HALKB.IS",
    "F_VAKBN": "VAKBN.IS",
    "F_ARCLK": "ARCLK.IS",
    "F_EKGYO": "EKGYO.IS",
    "F_YKBNK": "YKBNK.IS",
    "F_DOHOL": "DOHOL.IS",
    "F_TAVHL": "TAVHL.IS",
    "F_KONTR": "KONTR.IS",
    "F_SOKM":  "SOKM.IS",
    "F_MGROS": "MGROS.IS",
    "F_ULKER": "ULKER.IS",
    "F_PETKM": "PETKM.IS",
    "F_ENKAI": "ENKAI.IS",
}

# Interval → (yfinance interval, yfinance period) eşlemesi
_INTERVAL_MAP: dict[str, tuple[str, str]] = {
    "1m":  ("1m",  "1d"),
    "5m":  ("5m",  "5d"),
    "15m": ("15m", "5d"),
    "30m": ("30m", "1mo"),
    "1h":  ("60m", "1mo"),
    "4h":  ("1d",  "3mo"),
    "1d":  ("1d",  "1y"),
    "1w":  ("1wk", "5y"),
}


def _get_proxy_symbol(viop_symbol: str) -> str | None:
    """VİOP sembolünü dayanak Yahoo Finance sembolüne çevir.

    Önce tam eşleşme tabloya bakılır; yoksa F_XXX formatı için
    XXX.IS BIST hissesi olarak denenir.
    """
    clean = viop_symbol.strip().upper().replace(" ", "")
    if clean in _PROXY_UNDERLYING:
        return _PROXY_UNDERLYING[clean]
    # Prefix temizlenmiş hisse kodu denemesi: F_THYAO → THYAO.IS
    if clean.startswith("F_"):
        underlying = clean[2:] + ".IS"
        return underlying
    if clean.startswith("O_"):
        # Opsiyon kontratı için dayanak hisse
        underlying = clean[2:].split("_")[0] + ".IS"
        return underlying
    if clean.startswith("VIOP:"):
        underlying = clean[5:]
        # VIOP:THYAO → THYAO.IS gibi
        if underlying.isalpha() and 3 <= len(underlying) <= 6:
            return f"{underlying}.IS"
    return None


def _load_yfinance_history(source_symbol: str, yf_interval: str, yf_period: str, timeout: int) -> Any:
    """yfinance'tan tarihsel veri yükle."""
    import yfinance as yf

    ticker = yf.Ticker(source_symbol)
    try:
        return ticker.history(period=yf_period, interval=yf_interval, timeout=timeout)
    except TypeError:
        return ticker.history(period=yf_period, interval=yf_interval)


def _frame_to_bars(frame: Any, limit: int) -> list[dict[str, Any]]:
    """DataFrame'i bar listesine çevir (NaN satırları atla)."""
    frame = frame.reset_index().tail(max(1, int(limit)))
    time_col = "Datetime" if "Datetime" in frame.columns else "Date"
    bars: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        close = row.get("Close")
        if close is None or close != close:  # NaN kontrolü
            continue
        open_price = row.get("Open")
        high = row.get("High")
        low = row.get("Low")
        ts_value = row[time_col]
        if hasattr(ts_value, "to_pydatetime"):
            ts_value = ts_value.to_pydatetime()
        if hasattr(ts_value, "timestamp"):
            if ts_value.tzinfo is None:
                ts_value = ts_value.replace(tzinfo=dt.timezone.utc)
            ts = int(ts_value.timestamp())
        else:
            ts = int(ts_value)
        bars.append({
            "time": ts,
            "open":   float(open_price if open_price == open_price else close),
            "high":   float(high if high == high else close),
            "low":    float(low if low == low else close),
            "close":  float(close),
            "volume": float(row.get("Volume") or 0),
        })
    return bars


class ViopMarketDataProvider:
    name = "viop_proxy"
    source = "Yahoo Finance dayanak varlık proxy (gerçek VİOP akışı değil)"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.last_success_at: str | None = None
        self.last_error: str | None = None

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> MarketDataResult:
        clean = symbol.strip().upper().replace(" ", "")
        timestamp = utc_iso()

        # ── 1. Lisanslı HTTP feed öncelikli ─────────────────────────────────
        template = configured_template("VIOP_HTTP_URL_TEMPLATE")
        if template:
            try:
                bars = fetch_http_ohlcv(
                    template,
                    clean,
                    timeframe,
                    limit,
                    self.timeout,
                    configured_header("VIOP_HTTP_AUTH_HEADER"),
                )
            except Exception as exc:  # noqa: BLE001
                self.last_error = f"{type(exc).__name__}: {exc}"
                bars = []
            if bars:
                self.last_success_at = timestamp
                self.last_error = None
                return MarketDataResult(
                    symbol=clean,
                    market="viop",
                    timeframe=timeframe,
                    data=bars,
                    source="Configured VİOP HTTP feed",
                    is_real=True,
                    status=MarketDataStatus.OK,
                    timestamp=timestamp,
                    provider_name="viop_http",
                    display_name=clean,
                )
            self.last_error = self.last_error or "VİOP HTTP feed veri döndürmedi."

        # ── 2. Proxy: dayanak Yahoo Finance varlığı ──────────────────────────
        proxy_sym = _get_proxy_symbol(clean)
        if proxy_sym:
            yf_interval, yf_period = _INTERVAL_MAP.get(timeframe, ("15m", "5d"))
            try:
                frame = _load_yfinance_history(proxy_sym, yf_interval, yf_period, self.timeout)
            except Exception as exc:  # noqa: BLE001
                self.last_error = f"Proxy yüklenemedi ({proxy_sym}): {type(exc).__name__}: {exc}"
                return MarketDataResult(
                    symbol=clean,
                    market="viop",
                    timeframe=timeframe,
                    data=[],
                    source=self.source,
                    is_real=False,
                    status=MarketDataStatus.ERROR,
                    timestamp=timestamp,
                    error=self.last_error,
                    provider_name=self.name,
                    display_name=clean,
                )

            if frame is None or getattr(frame, "empty", True):
                self.last_error = f"Proxy veri yok: {proxy_sym}"
                return MarketDataResult(
                    symbol=clean,
                    market="viop",
                    timeframe=timeframe,
                    data=[],
                    source=self.source,
                    is_real=False,
                    status=MarketDataStatus.NO_DATA,
                    timestamp=timestamp,
                    error=self.last_error,
                    provider_name=self.name,
                    display_name=clean,
                )

            bars = _frame_to_bars(frame, limit)
            if not bars:
                self.last_error = f"Proxy çerçeve boş: {proxy_sym}"
                return MarketDataResult(
                    symbol=clean,
                    market="viop",
                    timeframe=timeframe,
                    data=[],
                    source=self.source,
                    is_real=False,
                    status=MarketDataStatus.NO_DATA,
                    timestamp=timestamp,
                    error=self.last_error,
                    provider_name=self.name,
                    display_name=clean,
                )

            self.last_success_at = timestamp
            self.last_error = None
            proxy_source = (
                f"Yahoo Finance proxy → {proxy_sym} "
                f"(gerçek VİOP akışı değil, dayanak varlık)"
            )
            return MarketDataResult(
                symbol=clean,
                market="viop",
                timeframe=timeframe,
                data=bars,
                source=proxy_source,
                is_real=False,
                status=MarketDataStatus.OK,
                timestamp=timestamp,
                provider_name=self.name,
                display_name=f"{clean} (proxy: {proxy_sym})",
            )

        # ── 3. Eşleşme yok, yapılandırılmamış ───────────────────────────────
        return MarketDataResult(
            symbol=clean,
            market="viop",
            timeframe=timeframe,
            data=[],
            source=self.source,
            is_real=False,
            status=MarketDataStatus.NOT_CONFIGURED,
            timestamp=timestamp,
            error=(
                f"'{clean}' için VİOP proxy eşlemesi bulunamadı. "
                "VIOP_HTTP_URL_TEMPLATE env değişkenini ayarlayın veya "
                "F_<HİSSE> / VIOP:<HİSSE> formatı kullanın."
            ),
            provider_name=self.name,
            display_name=clean,
        )

    def health(self) -> MarketDataHealth:
        http_configured = bool(configured_template("VIOP_HTTP_URL_TEMPLATE"))
        if http_configured:
            return MarketDataHealth(
                provider_name="viop_http",
                provider_type=MarketDataProviderType.VIOP,
                active=True,
                configured=True,
                is_real=True,
                supported_markets=["viop"],
                last_success_at=self.last_success_at,
                last_error=self.last_error,
                source="Configured VİOP HTTP feed",
            )
        return MarketDataHealth(
            provider_name=self.name,
            provider_type=MarketDataProviderType.VIOP,
            active=True,          # proxy her zaman aktif
            configured=False,     # lisanslı feed yok
            is_real=False,
            supported_markets=["viop"],
            last_success_at=self.last_success_at,
            last_error=self.last_error,
            source=self.source,
        )
