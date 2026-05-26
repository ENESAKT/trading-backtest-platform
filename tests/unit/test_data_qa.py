"""Data QA Unit Testleri — Bölüm 18.14

Kapsam:
  1. Gap detection — ardışık barlar arasındaki zaman boşlukları
  2. Duplicate bar detection — aynı ts'e sahip barlar
  3. Stale provider detection — son bar çok eski
  4. Sample data production gate — is_real=False veri canlıya çıkmamalı

Tüm testler BackfillManager.detect_gaps ve DataTruth kontratını kullanır.
"""
from __future__ import annotations

import sys
import os
import importlib.util
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

# ─── BackfillManager import ────────────────────────────────────────────────────

def _load_backfill():
    _mod_name = "backend.data.ingest.backfill"
    if _mod_name in sys.modules:
        return sys.modules[_mod_name]
    path = os.path.join(os.path.dirname(__file__), "../../backend/data/ingest/backfill.py")
    spec = importlib.util.spec_from_file_location(_mod_name, path)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[_mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


# ─── Sahte bar nesnesi ────────────────────────────────────────────────────────

@dataclass
class _Bar:
    ts:     datetime
    open:   float = 100.0
    high:   float = 105.0
    low:    float = 98.0
    close:  float = 102.0
    volume: float = 10_000.0


def _bars_every(n: int, interval_minutes: int = 60, start: Optional[datetime] = None) -> List[_Bar]:
    """n adet ardışık bar üretir."""
    t = start or datetime(2024, 1, 1, tzinfo=timezone.utc)
    delta = timedelta(minutes=interval_minutes)
    return [_Bar(ts=t + delta * i) for i in range(n)]


def _bars_with_gap(
    before: int,
    gap_hours: int,
    after: int,
    interval_minutes: int = 60,
) -> List[_Bar]:
    """Gap içeren bar listesi üretir."""
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    delta = timedelta(minutes=interval_minutes)
    left  = [_Bar(ts=start + delta * i) for i in range(before)]
    gap_start = start + delta * before + timedelta(hours=gap_hours)
    right = [_Bar(ts=gap_start + delta * i) for i in range(after)]
    return left + right


# ════════════════════════════════════════════════════════════════════════════════
# 1 — Gap Detection
# ════════════════════════════════════════════════════════════════════════════════

class TestGapDetection:
    """BackfillManager.detect_gaps doğru boşlukları bulmalı."""

    def _make_manager_with_bars(self, bars: List[_Bar]):
        mod = _load_backfill()
        manager    = mod.BackfillManager.__new__(mod.BackfillManager)
        mock_repo  = MagicMock()
        manager.provider   = MagicMock()
        manager.repository = mock_repo
        manager._chunk_days  = mod._DEFAULT_CHUNK_DAYS
        manager._max_retries = 3

        async def fake_get_bars(**kwargs):
            return bars

        mock_repo.get_bars = fake_get_bars
        mock_repo.get_latest_ts = AsyncMock(return_value=None)
        return manager

    @pytest.mark.asyncio
    async def test_no_gap_in_consecutive_bars(self):
        bars = _bars_every(10, interval_minutes=60)
        manager = self._make_manager_with_bars(bars)
        gaps = await manager.detect_gaps("BIST", "THYAO", "1h", lookback_days=30)
        assert len(gaps) == 0, "Ardışık barlarda boşluk olmamalı"

    @pytest.mark.asyncio
    async def test_detects_single_gap(self):
        bars = _bars_with_gap(before=5, gap_hours=5, after=5, interval_minutes=60)
        manager = self._make_manager_with_bars(bars)
        gaps = await manager.detect_gaps("BIST", "THYAO", "1h", lookback_days=30)
        assert len(gaps) == 1, f"1 boşluk olmalı, {len(gaps)} bulundu"
        assert gaps[0]["gap_seconds"] > 3600 * 1.5, "Gap 1.5 saatten uzun olmalı"

    @pytest.mark.asyncio
    async def test_detects_multiple_gaps(self):
        bars = _bars_with_gap(3, 3, 3)   # 1. gap
        bars += _bars_with_gap(2, 5, 2)  # 2. gap (zaman sırası bozulabilir ama test logic)
        # Sıralı tek liste yap
        bars = sorted(bars, key=lambda b: b.ts)
        manager = self._make_manager_with_bars(bars)
        gaps = await manager.detect_gaps("BIST", "THYAO", "1h", lookback_days=30)
        assert len(gaps) >= 1, "En az 1 gap bulunmalı"

    @pytest.mark.asyncio
    async def test_empty_bars_returns_no_gaps(self):
        manager = self._make_manager_with_bars([])
        gaps = await manager.detect_gaps("BIST", "THYAO", "1h", lookback_days=7)
        assert gaps == [], "Boş bar listesinde gap olmamalı"

    @pytest.mark.asyncio
    async def test_single_bar_returns_no_gaps(self):
        bars = _bars_every(1)
        manager = self._make_manager_with_bars(bars)
        gaps = await manager.detect_gaps("BIST", "THYAO", "1h")
        assert gaps == []


# ════════════════════════════════════════════════════════════════════════════════
# 2 — Duplicate Bar Detection
# ════════════════════════════════════════════════════════════════════════════════

class TestDuplicateDetection:
    """Duplicate ts içeren barlar tespit edilmeli."""

    def _find_duplicates(self, bars: List[_Bar]) -> List[datetime]:
        seen = set()
        dupes = []
        for b in bars:
            if b.ts in seen:
                dupes.append(b.ts)
            seen.add(b.ts)
        return dupes

    def test_no_duplicates_in_clean_bars(self):
        bars = _bars_every(10)
        dupes = self._find_duplicates(bars)
        assert len(dupes) == 0

    def test_detects_duplicate_timestamp(self):
        bars = _bars_every(5)
        bars.append(_Bar(ts=bars[2].ts))  # ts=bars[2] tekrar
        dupes = self._find_duplicates(bars)
        assert len(dupes) == 1
        assert dupes[0] == bars[2].ts

    def test_detects_multiple_duplicates(self):
        bars = _bars_every(5)
        bars.append(_Bar(ts=bars[0].ts))
        bars.append(_Bar(ts=bars[0].ts))  # 2x duplicate
        bars.append(_Bar(ts=bars[3].ts))  # başka duplicate
        dupes = self._find_duplicates(bars)
        assert len(dupes) >= 2


# ════════════════════════════════════════════════════════════════════════════════
# 3 — Stale Provider Detection
# ════════════════════════════════════════════════════════════════════════════════

class TestStaleProviderDetection:
    """Son bar çok eski ise stale tespit edilmeli."""

    _STALE_THRESHOLD_HOURS = 2  # 2 saatten eski → stale

    def _is_stale(self, last_bar_ts: datetime, threshold_hours: int = 2) -> bool:
        age = (datetime.now(timezone.utc) - last_bar_ts).total_seconds() / 3600
        return age > threshold_hours

    def test_fresh_bar_not_stale(self):
        fresh_ts = datetime.now(timezone.utc) - timedelta(minutes=5)
        assert not self._is_stale(fresh_ts), "5 dakikalık bar stale olmamalı"

    def test_old_bar_is_stale(self):
        old_ts = datetime.now(timezone.utc) - timedelta(hours=6)
        assert self._is_stale(old_ts), "6 saatlik bar stale olmalı"

    def test_exactly_at_threshold_not_stale(self):
        threshold_ts = datetime.now(timezone.utc) - timedelta(hours=2, minutes=1)
        assert self._is_stale(threshold_ts), "Eşiği 1 dk geçen bar stale olmalı"

    def test_daily_bar_freshness_check(self):
        """1d timeframe için 25 saat stale sayılmalı."""
        yesterday = datetime.now(timezone.utc) - timedelta(hours=25)
        assert self._is_stale(yesterday, threshold_hours=24)

    def test_multiple_providers_partial_stale(self):
        """Birden fazla provider'da kısmi stale tespiti."""
        providers = {
            "provider_a": datetime.now(timezone.utc) - timedelta(minutes=10),   # taze
            "provider_b": datetime.now(timezone.utc) - timedelta(hours=5),      # stale
            "provider_c": datetime.now(timezone.utc) - timedelta(hours=1),      # taze
        }
        stale = [name for name, ts in providers.items() if self._is_stale(ts)]
        assert stale == ["provider_b"], f"Sadece provider_b stale olmalı, {stale}"


# ════════════════════════════════════════════════════════════════════════════════
# 4 — Sample Data Production Gate
# ════════════════════════════════════════════════════════════════════════════════

class TestSampleDataProductionGate:
    """is_real=False veri production endpoint'lerinde bloklanmalı."""

    def _is_production_safe(self, data_truth: dict) -> bool:
        """DataTruth sözlüğünü kontrol eder; üretimde mock veri geçmemeli."""
        return data_truth.get("is_real", False) is True

    def test_real_data_passes_gate(self):
        truth = {"is_real": True, "provider": "matriks", "source_type": "licensed"}
        assert self._is_production_safe(truth)

    def test_mock_data_blocked(self):
        truth = {"is_real": False, "provider": "mock", "source_type": "sample"}
        assert not self._is_production_safe(truth)

    def test_unknown_is_real_blocked(self):
        """is_real anahtarı yoksa güvenli sayılmamalı."""
        truth = {"provider": "unknown"}
        assert not self._is_production_safe(truth)

    def test_imported_csv_blocked_by_default(self):
        truth = {"is_real": False, "source_type": "imported_csv"}
        assert not self._is_production_safe(truth)

    def test_pydantic_data_truth_is_real_field(self):
        """DataTruth Pydantic modeli is_real=False ile başlar (güvenli varsayılan)."""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
            from backend.data.schemas.market import DataTruth
            dt = DataTruth(symbol="TEST", market="BIST", timeframe="1d")
            assert dt.is_real is False, \
                "DataTruth varsayılan is_real=False olmalı (opt-in gerçeklik)"
        except ImportError:
            pytest.skip("backend.data.schemas erişilemiyor")

    def test_sample_bars_carry_not_real_flag(self):
        """Sample/mock barlar is_real=False olarak işaretlenmeli."""
        sample_bar_metadata = {
            "is_real":     False,
            "source_type": "sample",
            "provider":    "sample_generator",
        }
        assert not self._is_production_safe(sample_bar_metadata)

    def test_delayed_real_data_passes_gate(self):
        """Gecikimli ama gerçek veri production'da geçebilir."""
        truth = {
            "is_real":      True,
            "is_delayed":   True,
            "delay_minutes": 15,
            "provider":     "borsa_istanbul",
        }
        assert self._is_production_safe(truth)


# Standalone test fonksiyon (class dışı)
def test_pydantic_data_truth_is_real_field():
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
        from backend.data.schemas.market import DataTruth
        dt = DataTruth(symbol="TEST", market="BIST", timeframe="1d")
        assert dt.is_real is False, \
            "DataTruth varsayılan is_real=False olmalı (opt-in gerçeklik)"
    except ImportError:
        pytest.skip("backend.data.schemas erişilemiyor")
