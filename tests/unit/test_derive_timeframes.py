"""Unit testler: Timeframe türetme motoru (DerivedTimeframeBuilder).

Bölüm 18.14 — risk bazlı test kapsamı: timeframe derivation.

Test senaryoları:
  - Geçerli türetme yönleri (1m → 5m, 1m → 1h, 1d → 1w, vb.)
  - Yasak yönler (büyük → küçük) kesinlikle reddedilmeli
  - OHLCV birleşimi doğruluğu
  - Boş kaynak set → 0 bar üretilmeli
  - Bilinmeyen hedef timeframe → ValueError
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from backend.data.ingest.dependency_graph import can_derive
from backend.data.ingest.derive_timeframes import DerivedTimeframeBuilder
from backend.data.schemas.market import MarketBar


# ─── Yardımcı: Sahte Bar Üretici ─────────────────────────────────────────────

def _make_bar(
    ts: str,
    open_: float,
    high: float,
    low: float,
    close: float,
    volume: float = 1000.0,
    market: str = "TEST",
    symbol: str = "AAAA",
    timeframe: str = "1m",
) -> MarketBar:
    return MarketBar(
        market=market,
        symbol=symbol,
        instrument_type="stock",
        timeframe=timeframe,
        ts=datetime.fromisoformat(ts).replace(tzinfo=timezone.utc),
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
        source="test",
    )


# ─── can_derive() bağımsız testleri ──────────────────────────────────────────

class TestCanDerive:
    def test_valid_1m_to_5m(self):
        assert can_derive("1m", "5m") is True

    def test_valid_1m_to_1h(self):
        assert can_derive("1m", "1h") is True

    def test_valid_1d_to_1w(self):
        assert can_derive("1d", "1w") is True

    def test_valid_1d_to_1mo(self):
        assert can_derive("1d", "1mo") is True

    def test_forbidden_1h_to_1m(self):
        """Büyükten küçüğe türetme kesinlikle yasak."""
        assert can_derive("1h", "1m") is False

    def test_forbidden_1d_to_5m(self):
        assert can_derive("1d", "5m") is False

    def test_forbidden_1w_to_1d(self):
        assert can_derive("1w", "1d") is False

    def test_same_timeframe(self):
        """Aynı timeframe → türetme anlamsız, False beklenir."""
        assert can_derive("1d", "1d") is False


# ─── DerivedTimeframeBuilder testleri ────────────────────────────────────────

@pytest.mark.asyncio
class TestDerivedTimeframeBuilder:

    async def test_raises_on_forbidden_direction(self):
        """Büyük → küçük türetmede ValueError fırlatılmalı."""
        repo = MagicMock()
        builder = DerivedTimeframeBuilder(repo)
        with pytest.raises(ValueError, match="Yasak türetme"):
            await builder.derive("TEST", "AAAA", source_tf="1h", target_tf="1m")

    async def test_raises_on_unknown_target_timeframe(self):
        """can_derive geçse de _TF_TO_PANDAS_FREQ'de olmayan timeframe → ValueError.

        dependency_graph GRAPH_NODES içinde olmayan hedef için can_derive=False
        döner ve "Yasak türetme" hatası gelir. Bu da ValueError olduğundan test
        geçerli; match ifadesini geniş tutuyoruz.
        """
        repo = MagicMock()
        builder = DerivedTimeframeBuilder(repo)
        # "3m" GRAPH_NODES'ta yok → can_derive False → ValueError
        with pytest.raises(ValueError):
            await builder.derive("TEST", "AAAA", source_tf="1m", target_tf="3m")

    async def test_empty_source_returns_zero(self):
        """Kaynak bar yoksa 0 dönmeli; insert_bars çağrılmamalı."""
        repo = AsyncMock()
        repo.get_bars = AsyncMock(return_value=[])
        repo.insert_bars = AsyncMock(return_value=0)
        builder = DerivedTimeframeBuilder(repo)

        result = await builder.derive("TEST", "AAAA", source_tf="1m", target_tf="5m")

        assert result == 0
        repo.insert_bars.assert_not_called()

    async def test_ohlcv_aggregation_correct(self):
        """5 adet 1m bar → 1 adet 5m bar; OHLCV birleşimi doğru olmalı."""
        bars = [
            _make_bar("2026-01-01T09:30:00", open_=100, high=105, low=99,  close=103, volume=200),
            _make_bar("2026-01-01T09:31:00", open_=103, high=107, low=102, close=106, volume=300),
            _make_bar("2026-01-01T09:32:00", open_=106, high=108, low=104, close=104, volume=150),
            _make_bar("2026-01-01T09:33:00", open_=104, high=106, low=101, close=102, volume=250),
            _make_bar("2026-01-01T09:34:00", open_=102, high=103, low=100, close=101, volume=100),
        ]

        repo = AsyncMock()
        repo.get_bars = AsyncMock(return_value=bars)
        inserted_bars: list[MarketBar] = []

        async def capture_insert(b):
            inserted_bars.extend(b)
            return len(b)

        repo.insert_bars = capture_insert
        builder = DerivedTimeframeBuilder(repo)

        result = await builder.derive("TEST", "AAAA", source_tf="1m", target_tf="5m")

        assert result == 1
        assert len(inserted_bars) == 1
        bar = inserted_bars[0]

        # open = ilk barın open
        assert bar.open == pytest.approx(100.0)
        # high = max(105, 107, 108, 106, 103)
        assert bar.high == pytest.approx(108.0)
        # low = min(99, 102, 104, 101, 100)
        assert bar.low == pytest.approx(99.0)
        # close = son barın close
        assert bar.close == pytest.approx(101.0)
        # volume = toplam
        assert bar.volume == pytest.approx(1000.0)

        # Türetme meta
        assert bar.is_derived is True
        assert bar.source_timeframe == "1m"
        assert bar.timeframe == "5m"

    async def test_derived_bars_have_job_id(self):
        """Üretilen her bar aynı ingest_job_id'ye sahip olmalı."""
        bars = [
            _make_bar("2026-01-01T00:00:00", 100, 105, 98, 103),
            _make_bar("2026-01-01T01:00:00", 103, 110, 101, 108),
        ]

        repo = AsyncMock()
        repo.get_bars = AsyncMock(return_value=bars)
        inserted_bars: list[MarketBar] = []

        async def capture_insert(b):
            inserted_bars.extend(b)
            return len(b)

        repo.insert_bars = capture_insert
        builder = DerivedTimeframeBuilder(repo)
        await builder.derive("TEST", "AAAA", source_tf="1m", target_tf="4h")

        job_ids = {b.ingest_job_id for b in inserted_bars}
        assert len(job_ids) == 1   # tek job_id
        assert None not in job_ids  # None olmamalı
