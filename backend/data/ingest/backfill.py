"""Backfill Manager — Bölüm 11

Geçmiş veri eksiklerini tespit eder, sağlayıcıdan chunk'lar hâlinde çeker
ve ClickHouse deposuna yazar.

Temel özellikler:
- Gap detection: depodaki en son bar'dan bugüne kadar olan boşluğu hesaplar.
- Chunk-based fetch: büyük tarih aralıklarını yapılandırılabilir parçalara böler.
- Retry with backoff: geçici sağlayıcı hatalarında üstel geri-çekilme uygular.
- Audit log: her backfill çalışması için benzersiz job_id, başlangıç/bitiş zaman
  damgası, işlenen bar sayısı ve hata bilgisi kaydedilir.
- Dry-run modu: execute=False (varsayılan) yalnızca plan raporlar, veri yazmaz.
- Idempotent: aynı zaman aralığını iki kez çalıştırmak duplicate oluşturmaz
  (repository upsert kullanır).
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Protocol, Sequence

logger = logging.getLogger(__name__)

# ─── Yapılandırma ────────────────────────────────────────────────────────────

# Varsayılan chunk boyutu (gün)
_DEFAULT_CHUNK_DAYS: Dict[str, int] = {
    "1m":  1,
    "5m":  3,
    "15m": 7,
    "30m": 14,
    "1h":  30,
    "4h":  90,
    "1d":  365,
    "1w":  730,
    "1mo": 1825,
    "1y":  3650,
}

MAX_RETRIES = 3
BASE_RETRY_DELAY_SEC = 2.0


# ─── Protokoller (duck typing) ────────────────────────────────────────────────

class BarProvider(Protocol):
    """Sağlayıcı arayüzü — gerçek implementasyon dışarıdan enjekte edilir."""

    async def fetch_bars(
        self,
        market: str,
        symbol: str,
        timeframe: str,
        start_ts: datetime,
        end_ts: datetime,
    ) -> List[Any]: ...


class BarRepository(Protocol):
    """Depo arayüzü."""

    async def get_latest_ts(
        self,
        market: str,
        symbol: str,
        timeframe: str,
    ) -> Optional[datetime]: ...

    async def upsert_bars(self, bars: Sequence[Any]) -> int: ...


# ─── Sonuç tipleri ────────────────────────────────────────────────────────────

@dataclass
class ChunkResult:
    start_ts: datetime
    end_ts: datetime
    bars_fetched: int
    bars_written: int
    error: Optional[str] = None


@dataclass
class BackfillResult:
    job_id: str
    market: str
    symbol: str
    timeframe: str
    start_ts: datetime
    end_ts: datetime
    dry_run: bool
    total_bars_fetched: int = 0
    total_bars_written: int = 0
    chunks: List[ChunkResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        dur = (
            f"{(self.finished_at - self.started_at).total_seconds():.1f}s"
            if self.finished_at and self.started_at
            else "?"
        )
        return (
            f"BackfillResult job={self.job_id} "
            f"{self.market}/{self.symbol}/{self.timeframe} "
            f"fetched={self.total_bars_fetched} written={self.total_bars_written} "
            f"chunks={len(self.chunks)} errors={len(self.errors)} dur={dur} "
            f"dry_run={self.dry_run}"
        )


# ─── Ana sınıf ────────────────────────────────────────────────────────────────

class BackfillManager:
    """Geçmiş veri eksiklerini giderir.

    Args:
        provider:    Veri sağlayıcı (BarProvider protokolü).
        repository:  Veri deposu (BarRepository protokolü).
        chunk_days:  Timeframe → chunk boyutu (gün) sözlüğü.
                     Belirtilmezse _DEFAULT_CHUNK_DAYS kullanılır.
        max_retries: Geçici hatalar için maksimum deneme sayısı.
    """

    def __init__(
        self,
        provider: Any,
        repository: Any,
        chunk_days: Optional[Dict[str, int]] = None,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        self.provider = provider
        self.repository = repository
        self._chunk_days = chunk_days or _DEFAULT_CHUNK_DAYS
        self._max_retries = max_retries

    # ─── Public API ──────────────────────────────────────────────────────────

    async def run_backfill(
        self,
        market: str,
        symbol: str,
        timeframe: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        execute: bool = False,
    ) -> BackfillResult:
        """Backfill çalıştır.

        Args:
            market:     Piyasa kodu (örn. "BIST", "VIOP").
            symbol:     Sembol (örn. "THYAO").
            timeframe:  Zaman dilimi (örn. "1d", "1h").
            start_date: ISO 8601 tarih dizisi (örn. "2024-01-01").
                        None ise depodaki en son bar'dan başlar.
            end_date:   ISO 8601 tarih dizisi. None ise bugün (UTC).
            execute:    True ise veri yazar; False (varsayılan) dry-run modudur.

        Returns:
            BackfillResult: İş özeti.
        """
        job_id = str(uuid.uuid4())
        now_utc = datetime.now(timezone.utc)

        # Tarih aralığını belirle
        end_ts = _parse_date(end_date) if end_date else now_utc
        if start_date:
            start_ts = _parse_date(start_date)
        else:
            latest = await self.repository.get_latest_ts(market, symbol, timeframe)
            start_ts = (latest + timedelta(seconds=1)) if latest else (now_utc - timedelta(days=30))

        result = BackfillResult(
            job_id=job_id,
            market=market,
            symbol=symbol,
            timeframe=timeframe,
            start_ts=start_ts,
            end_ts=end_ts,
            dry_run=not execute,
            started_at=now_utc,
        )

        logger.info(
            "Backfill başlatıldı job_id=%s %s/%s/%s %s → %s dry_run=%s",
            job_id, market, symbol, timeframe,
            start_ts.isoformat(), end_ts.isoformat(), not execute,
        )

        if start_ts >= end_ts:
            logger.info("Backfill atlandı: start_ts >= end_ts (veri güncel). job_id=%s", job_id)
            result.finished_at = datetime.now(timezone.utc)
            return result

        # Chunk'lara böl ve işle
        chunks = list(_split_chunks(start_ts, end_ts, self._chunk_days.get(timeframe, 30)))
        for chunk_start, chunk_end in chunks:
            chunk_result = await self._process_chunk(
                market=market,
                symbol=symbol,
                timeframe=timeframe,
                start_ts=chunk_start,
                end_ts=chunk_end,
                execute=execute,
            )
            result.chunks.append(chunk_result)
            result.total_bars_fetched += chunk_result.bars_fetched
            result.total_bars_written += chunk_result.bars_written
            if chunk_result.error:
                result.errors.append(chunk_result.error)

        result.finished_at = datetime.now(timezone.utc)
        logger.info(result.summary())
        return result

    async def detect_gaps(
        self,
        market: str,
        symbol: str,
        timeframe: str,
        lookback_days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Depodaki bar boşluklarını tespit eder.

        Returns:
            Boşluk listesi: [{"start": datetime, "end": datetime, "gap_seconds": int}]
        """
        end_ts = datetime.now(timezone.utc)
        start_ts = end_ts - timedelta(days=lookback_days)

        try:
            bars = await self.repository.get_bars(
                market=market,
                symbol=symbol,
                timeframe=timeframe,
                start_ts=start_ts,
                end_ts=end_ts,
                limit=100_000,
            )
        except AttributeError:
            # repository.get_bars mevcut değilse boş döndür
            logger.warning("repository.get_bars() bulunamadı, gap detection atlandı.")
            return []

        if len(bars) < 2:
            return []

        expected_delta = _timeframe_to_seconds(timeframe)
        if expected_delta <= 0:
            return []

        gaps: List[Dict[str, Any]] = []
        # bars ts'e göre sıralı varsayılır
        for i in range(1, len(bars)):
            prev_ts = getattr(bars[i - 1], "ts", None)
            curr_ts = getattr(bars[i], "ts", None)
            if prev_ts is None or curr_ts is None:
                continue
            delta = (curr_ts - prev_ts).total_seconds()
            if delta > expected_delta * 1.5:  # %50 tolerans
                gaps.append({
                    "start": prev_ts,
                    "end": curr_ts,
                    "gap_seconds": int(delta),
                    "expected_seconds": expected_delta,
                })

        logger.info(
            "Gap detection: %s/%s/%s → %d boşluk bulundu (lookback=%d gün)",
            market, symbol, timeframe, len(gaps), lookback_days,
        )
        return gaps

    # ─── Private ─────────────────────────────────────────────────────────────

    async def _process_chunk(
        self,
        market: str,
        symbol: str,
        timeframe: str,
        start_ts: datetime,
        end_ts: datetime,
        execute: bool,
    ) -> ChunkResult:
        """Tek bir zaman aralığını sağlayıcıdan çekip depoya yazar."""
        bars_fetched = 0
        bars_written = 0
        error: Optional[str] = None

        for attempt in range(1, self._max_retries + 1):
            try:
                bars = await self.provider.fetch_bars(
                    market=market,
                    symbol=symbol,
                    timeframe=timeframe,
                    start_ts=start_ts,
                    end_ts=end_ts,
                )
                bars_fetched = len(bars)

                if execute and bars:
                    bars_written = await self.repository.upsert_bars(bars)
                elif not execute and bars:
                    bars_written = 0  # dry-run: saymaz

                error = None
                break  # başarılı

            except Exception as exc:
                error = str(exc)
                if attempt < self._max_retries:
                    delay = BASE_RETRY_DELAY_SEC * (2 ** (attempt - 1))
                    logger.warning(
                        "Chunk hatası (deneme %d/%d): %s → %s | %s | %.1fs bekle",
                        attempt, self._max_retries,
                        start_ts.isoformat(), end_ts.isoformat(), exc, delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "Chunk başarısız (tüm denemeler tükendi): %s → %s | %s",
                        start_ts.isoformat(), end_ts.isoformat(), exc,
                    )

        return ChunkResult(
            start_ts=start_ts,
            end_ts=end_ts,
            bars_fetched=bars_fetched,
            bars_written=bars_written,
            error=error,
        )


# ─── Yardımcı fonksiyonlar ───────────────────────────────────────────────────

def _parse_date(date_str: str) -> datetime:
    """ISO 8601 tarih dizisini UTC datetime'a çevirir."""
    dt = datetime.fromisoformat(date_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _split_chunks(
    start: datetime,
    end: datetime,
    chunk_days: int,
) -> List[tuple[datetime, datetime]]:
    """Tarih aralığını chunk_days günlük parçalara böler."""
    chunks: List[tuple[datetime, datetime]] = []
    current = start
    delta = timedelta(days=max(1, chunk_days))
    while current < end:
        chunk_end = min(current + delta, end)
        chunks.append((current, chunk_end))
        current = chunk_end
    return chunks


_TF_SECONDS: Dict[str, int] = {
    "1m":  60,
    "5m":  300,
    "15m": 900,
    "30m": 1800,
    "1h":  3600,
    "4h":  14400,
    "1d":  86400,
    "1w":  604800,
    "1mo": 2592000,
    "1y":  31536000,
}


def _timeframe_to_seconds(timeframe: str) -> int:
    return _TF_SECONDS.get(timeframe, 0)
