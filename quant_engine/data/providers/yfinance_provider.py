"""
Quant Engine — Yahoo Finance Veri Sağlayıcı

Eski fetcher.py'dan dönüştürülmüş, MarketDataProvider protocol'ünü
implemente eden yfinance tabanlı veri sağlayıcı.

Düzeltilen bug'lar:
    FET-1: end=today → end=tomorrow (yfinance exclusive)
    FET-3: Intraday KeyError: 'date' düzeltildi (Datetime index)
    FET-4: Bulk fetch tek sembolde kırılma düzeltildi
    FET-5: tz_localize(None) yerine tz_convert(UTC) sonra tz strip
    FET-6: Timeout parametresi eklendi
    FET-7: Retry mekanizması BaseProvider'dan miras
    FET-8: Boş sonuç için daha iyi hata mesajı
    FET-9: Rate limiting eklendi

Kullanım:
    from quant_engine.data.providers.yfinance_provider import (
        YFinanceProvider,
    )

    provider = YFinanceProvider()
    result = provider.fetch_bars(BarRequest(symbol="THYAO"))
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

import pandas as pd
import yfinance as yf
from loguru import logger

from quant_engine.config.config_manager import get_config
from quant_engine.core.protocols import (
    BarRequest,
    FetchResult,
    Market,
    ProviderCapabilities,
    Timeframe,
)
from quant_engine.data.providers.base import BaseProvider

# Yahoo Finance'ın BIST için kullandığı suffix
_BIST_SUFFIX = ".IS"

# SymbolMaster — kanonical sembol → yahoo sembol eşlemesi.
# Canlı/gün sonu gerçek veri yoksa üst katman sahte veriye düşmez.
_SYMBOL_MAP: dict[str, str] = {
    "USDTRY": "USDTRY=X",
    "EURTRY": "EURTRY=X",
    "GBPTRY": "GBPTRY=X",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "XAUUSD": "GC=F",
    "XAGUSD": "SI=F",
    "BRENT": "BZ=F",
    "WTI": "CL=F",
    "NGAS": "NG=F",
}


def _to_yahoo_ticker(symbol: str, market: Market = Market.BIST) -> str:
    """Sembolü Yahoo Finance formatına çevir."""
    symbol = symbol.upper().replace("/", "").strip()
    # Özel eşleme varsa kullan
    if symbol in _SYMBOL_MAP:
        return _SYMBOL_MAP[symbol]
    if market in {Market.FOREX, Market.COMMODITY}:
        return symbol
    # Yoksa suffix ekle
    if not symbol.endswith(_BIST_SUFFIX):
        return f"{symbol}{_BIST_SUFFIX}"
    return symbol


def _clean_symbol(yahoo_ticker: str, requested_symbol: str | None = None) -> str:
    """Yahoo ticker'dan kullanıcı sembolünü çıkar."""
    if requested_symbol:
        return requested_symbol.upper().replace("/", "").replace(_BIST_SUFFIX, "")
    return yahoo_ticker.replace(_BIST_SUFFIX, "")


class YFinanceProvider(BaseProvider):
    """
    Yahoo Finance veri sağlayıcı.

    Ücretsiz, internet bağlantısı gerektirir.
    BIST günlük/haftalık verisi için kullanılır.
    Intraday verisi son 7 gün ile sınırlı.
    """

    def __init__(
        self,
        retry_count: int | None = None,
        retry_delay: float | None = None,
        timeout: float | None = None,
    ):
        config = get_config()
        super().__init__(
            retry_count=(
                retry_count
                if retry_count is not None
                else config.data_pipeline.retry_count
            ),
            retry_delay=(
                retry_delay
                if retry_delay is not None
                else config.data_pipeline.retry_delay_seconds
            ),
            timeout=(
                timeout
                if timeout is not None
                else config.data_pipeline.request_timeout_seconds
            ),
        )
        self._config = config

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            name="yfinance",
            supported_markets=[Market.BIST, Market.FOREX, Market.COMMODITY],
            supported_timeframes=[
                Timeframe.M1,
                Timeframe.M5,
                Timeframe.M15,
                Timeframe.M30,
                Timeframe.H1,
                Timeframe.D1,
                Timeframe.W1,
                Timeframe.MO1,
            ],
            supports_intraday=True,
            supports_live=False,
            max_history_days=None,
            rate_limit_per_minute=60,
        )

    def _fetch_bars_impl(
        self, request: BarRequest
    ) -> FetchResult:
        """Yahoo Finance'tan bar verisi çek."""
        yahoo_ticker = _to_yahoo_ticker(request.symbol, request.market)
        clean_sym = _clean_symbol(yahoo_ticker, request.symbol)

        start_str = (
            request.start.isoformat()
            if request.start
            else self._config.data_pipeline.default_start_date
        )

        # FET-1 FIX: yfinance end parametresi exclusive
        # end=today derseniz bugünün verisi gelmez
        # Bu yüzden end = yarın olarak ayarlıyoruz
        if request.end:
            end_date = request.end + dt.timedelta(days=1)
        else:
            end_date = dt.date.today() + dt.timedelta(days=1)
        end_str = end_date.isoformat()

        interval = request.timeframe.value

        logger.info(
            f"📥 {clean_sym}: {start_str} → "
            f"{request.end or 'bugün'} | {interval}"
        )

        try:
            ticker = yf.Ticker(yahoo_ticker)
            df = ticker.history(
                start=start_str,
                end=end_str,
                interval=interval,
                timeout=self.timeout,
            )

            if df.empty:
                return FetchResult(
                    symbol=clean_sym,
                    data=pd.DataFrame(),
                    source="yfinance",
                    errors=[
                        f"{clean_sym} için veri bulunamadı "
                        f"({start_str} → {end_str})"
                    ],
                )

            # Sütun isimlerini standartlaştır
            df = df.reset_index()
            df.columns = [
                c.lower().replace(" ", "_")
                for c in df.columns
            ]

            # FET-3 FIX: Intraday veride index adı
            # 'Datetime' olabiliyor, 'Date' değil
            if "datetime" in df.columns and "date" not in df.columns:
                df = df.rename(columns={"datetime": "date"})

            # Gereksiz sütunları temizle
            keep_cols = [
                "date", "open", "high", "low",
                "close", "volume",
            ]
            available_cols = [
                c for c in keep_cols if c in df.columns
            ]
            df = df[available_cols].copy()

            # Sembol sütunu ekle
            df["symbol"] = clean_sym

            # FET-5 FIX: Timezone güvenli dönüşüm
            # tz_localize(None) yerine UTC'ye çevir, sonra
            # tz bilgisini kaldır (naive UTC olarak sakla)
            if "date" in df.columns:
                dates = pd.to_datetime(df["date"])
                if dates.dt.tz is not None:
                    dates = dates.dt.tz_convert("UTC")
                df["date"] = dates.dt.tz_localize(None)

            # Volume tipini integer yap
            if "volume" in df.columns:
                df["volume"] = (
                    df["volume"].fillna(0).astype("int64")
                )

            # NaN fiyat satırlarını logla (silmiyoruz —
            # validator'ın işi)
            warnings: list[str] = []
            price_cols = [
                c for c in ["open", "high", "low", "close"]
                if c in df.columns
            ]
            nan_count = df[price_cols].isna().any(axis=1).sum()
            if nan_count > 0:
                warnings.append(
                    f"{nan_count} satırda NaN fiyat tespit "
                    f"edildi"
                )

            logger.success(
                f"✅ {clean_sym}: {len(df)} satır "
                f"({df['date'].min():%Y-%m-%d} → "
                f"{df['date'].max():%Y-%m-%d})"
            )

            return FetchResult(
                symbol=clean_sym,
                data=df,
                source="yfinance",
                warnings=warnings,
            )

        except Exception as e:
            logger.error(
                f"❌ {clean_sym} veri çekme hatası: {e}"
            )
            return FetchResult(
                symbol=clean_sym,
                data=pd.DataFrame(),
                source="yfinance",
                errors=[str(e)],
            )

    def fetch_bulk(
        self,
        symbols: list[str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        interval: str = "1d",
    ) -> dict[str, FetchResult]:
        """
        Birden fazla sembolü toplu çek.

        FET-4 FIX: Tek sembolde kırılma düzeltildi.

        Args:
            symbols: Sembol listesi
            start: Başlangıç tarihi
            end: Bitiş tarihi
            interval: Zaman dilimi

        Returns:
            dict[str, FetchResult]: Sembol → sonuç
        """
        results: dict[str, FetchResult] = {}

        yahoo_tickers = [_to_yahoo_ticker(s) for s in symbols]
        start = (
            start
            or self._config.data_pipeline.default_start_date
        )

        # FET-1 FIX: end exclusive
        if end:
            end_date = (
                dt.date.fromisoformat(end)
                + dt.timedelta(days=1)
            )
            end_str = end_date.isoformat()
        else:
            end_str = (
                dt.date.today() + dt.timedelta(days=1)
            ).isoformat()

        logger.info(
            f"⚡ Toplu indirme: {len(symbols)} hisse | "
            f"{start} → {end or 'bugün'} | {interval}"
        )

        try:
            raw = yf.download(
                tickers=yahoo_tickers,
                start=start,
                end=end_str,
                interval=interval,
                group_by="ticker",
                auto_adjust=True,
                threads=True,
                timeout=self.timeout,
            )

            if raw.empty:
                for s in symbols:
                    results[s] = FetchResult(
                        symbol=s,
                        data=pd.DataFrame(),
                        source="yfinance",
                        errors=["Toplu indirme boş döndü"],
                    )
                return results

            for ticker in yahoo_tickers:
                clean = _clean_symbol(ticker)
                try:
                    # FET-4 FIX: Tek sembolde multi-level
                    # column yok
                    if len(yahoo_tickers) == 1:
                        df = raw.copy()
                    else:
                        df = raw[ticker].copy()

                    df = df.reset_index()
                    df.columns = [
                        c.lower().replace(" ", "_")
                        for c in df.columns
                    ]

                    # FET-3 FIX: intraday datetime
                    if (
                        "datetime" in df.columns
                        and "date" not in df.columns
                    ):
                        df = df.rename(
                            columns={"datetime": "date"}
                        )

                    df["symbol"] = clean

                    keep = [
                        "date", "open", "high", "low",
                        "close", "volume", "symbol",
                    ]
                    available = [
                        c for c in keep if c in df.columns
                    ]
                    df = df[available].dropna(subset=["close"])

                    results[clean] = FetchResult(
                        symbol=clean,
                        data=df,
                        source="yfinance",
                    )
                except (KeyError, Exception) as e:
                    logger.warning(
                        f"⚠️ {clean} parse hatası: {e}"
                    )
                    results[clean] = FetchResult(
                        symbol=clean,
                        data=pd.DataFrame(),
                        source="yfinance",
                        errors=[str(e)],
                    )

        except Exception as e:
            logger.error(f"❌ Toplu indirme hatası: {e}")
            for s in symbols:
                results[s] = FetchResult(
                    symbol=s,
                    data=pd.DataFrame(),
                    source="yfinance",
                    errors=[str(e)],
                )

        successful = sum(
            1 for r in results.values() if r.success
        )
        logger.info(
            f"📊 Toplu sonuç: {successful}/"
            f"{len(symbols)} başarılı"
        )

        return results

    def health_check(self) -> bool:
        """Yahoo Finance erişilebilir mi?"""
        try:
            t = yf.Ticker("THYAO.IS")
            info = t.fast_info
            return hasattr(info, "last_price")
        except Exception:
            return False
