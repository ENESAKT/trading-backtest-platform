"""Timeframe türetme motoru — küçük timeframe'lerden büyük olanlar üretilir.

Kural:
- Yalnızca küçük → büyük türetme yapılır (1m → 5m, 1d → 1w vb.).
- Büyük → küçük türetme kesinlikle yasak.
- Her türetilmiş bar is_derived=True, source_timeframe=<kaynak_tf> ile kaydedilir.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import List

from backend.data.ingest.dependency_graph import can_derive
from backend.data.schemas.market import MarketBar

logger = logging.getLogger(__name__)

# Timeframe → pandas resample frekansı
_TF_TO_PANDAS_FREQ: dict[str, str] = {
    "5m":  "5min",
    "15m": "15min",
    "30m": "30min",
    "1h":  "1h",
    "4h":  "4h",
    "1d":  "1D",
    "1w":  "1W",
    "1mo": "1ME",
    "1y":  "1YE",
}


class DerivedTimeframeBuilder:
    def __init__(self, repository) -> None:
        self.repository = repository

    async def derive(
        self,
        market: str,
        symbol: str,
        source_tf: str,
        target_tf: str,
        instrument_type: str = "stock",
        start_ts: datetime | None = None,
        end_ts: datetime | None = None,
        limit: int = 5000,
    ) -> int:
        """Kaynak timeframe barlarından hedef timeframe'i türet.

        Returns:
            Oluşturulan bar sayısı.

        Raises:
            ValueError: Yasak türetme yönü veya bilinmeyen timeframe.
        """
        if not can_derive(source_tf, target_tf):
            raise ValueError(
                f"Yasak türetme: {source_tf} → {target_tf}. "
                "Yalnızca küçük → büyük timeframe türetmeye izin verilir."
            )

        freq = _TF_TO_PANDAS_FREQ.get(target_tf)
        if freq is None:
            raise ValueError(f"Bilinmeyen hedef timeframe: {target_tf}")

        # Kaynak barları getir
        source_bars = await self.repository.get_bars(
            market=market,
            symbol=symbol,
            timeframe=source_tf,
            start_ts=start_ts,
            end_ts=end_ts,
            limit=limit,
        )

        if not source_bars:
            logger.warning(
                "Türetme atlandı: %s %s %s → kaynak bar bulunamadı.", market, symbol, source_tf
            )
            return 0

        try:
            import pandas as pd
        except ImportError as exc:
            raise RuntimeError("pandas kurulu değil; türetme çalışamaz.") from exc

        # DataFrame'e çevir
        df = pd.DataFrame([
            {
                "ts":     b.ts,
                "open":   b.open,
                "high":   b.high,
                "low":    b.low,
                "close":  b.close,
                "volume": b.volume,
            }
            for b in source_bars
        ])
        df["ts"] = pd.to_datetime(df["ts"], utc=True)
        df = df.set_index("ts").sort_index()

        # OHLCV resample: open=first, high=max, low=min, close=last, volume=sum
        resampled = df.resample(freq, label="left", closed="left").agg({
            "open":   "first",
            "high":   "max",
            "low":    "min",
            "close":  "last",
            "volume": "sum",
        }).dropna(subset=["open", "close"])

        if resampled.empty:
            logger.info("Türetme sonuç sıfır: %s %s %s → %s", market, symbol, source_tf, target_tf)
            return 0

        now = datetime.now(timezone.utc)
        job_id = str(uuid.uuid4())

        derived_bars: List[MarketBar] = [
            MarketBar(
                market=market,
                symbol=symbol,
                instrument_type=instrument_type,
                timeframe=target_tf,
                ts=row_ts.to_pydatetime(),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
                source="derived",
                source_timeframe=source_tf,
                is_derived=True,
                quality_status="ok",
                ingest_job_id=job_id,
                ingested_at=now,
            )
            for row_ts, row in resampled.iterrows()
        ]

        inserted = await self.repository.insert_bars(derived_bars)
        logger.info(
            "Türetme tamamlandı: %s %s %s → %s | %d bar eklendi.",
            market, symbol, source_tf, target_tf, inserted,
        )
        return inserted
