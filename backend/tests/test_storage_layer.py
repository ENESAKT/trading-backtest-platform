"""
test_storage_layer.py — StorageLayerGuard ve ProviderFailover birim testleri.

Çalıştırma:
    cd backend && python -m pytest tests/test_storage_layer.py -v
"""

from __future__ import annotations

import pytest
import asyncio

from backend.data.storage_layer_guard import (
    StorageLayerGuard,
    StorageLayerViolation,
    StorageKind,
)
from backend.data.repositories.provider_failover import (
    ProviderFailover,
    ProviderFailoverRegistry,
    ProviderResult,
    PRICE_DIFF_THRESHOLD_PCT,
    TIMESTAMP_DIFF_THRESHOLD_S,
)


# ─── StorageLayerGuard Testleri ──────────────────────────────────────────────

class TestStorageLayerGuard:

    def test_clickhouse_allowed_for_ohlcv(self):
        """OHLCV yazımı ClickHouse'a izinli."""
        StorageLayerGuard.assert_clickhouse("ohlcv_write", "test")  # exception fırlatmamalı

    def test_clickhouse_allowed_for_timeseries(self):
        StorageLayerGuard.assert_clickhouse("timeseries_write", "test")

    def test_mysql_allowed_for_user(self):
        """Kullanıcı verisi MySQL'e izinli."""
        StorageLayerGuard.assert_mysql("user_write", "test")

    def test_mysql_allowed_for_alarm(self):
        StorageLayerGuard.assert_mysql("alarm_write", "test")

    def test_redis_allowed_for_hot_cache(self):
        """Sıcak cache Redis'e izinli."""
        StorageLayerGuard.assert_redis("hot_cache_write", "test")

    def test_redis_allowed_for_pubsub(self):
        StorageLayerGuard.assert_redis("pubsub_publish", "test")

    # ── İhlal testleri ──────────────────────────────────────────────────────

    def test_timeseries_in_mysql_raises(self):
        """Zaman serisi MySQL'e yazılırsa ihlal."""
        with pytest.raises(StorageLayerViolation):
            StorageLayerGuard.assert_no_timeseries_in_mysql("test_timeseries_in_mysql")

    def test_user_in_clickhouse_raises(self):
        """Kullanıcı verisi ClickHouse'a yazılırsa ihlal."""
        with pytest.raises(StorageLayerViolation):
            StorageLayerGuard.assert_no_user_in_clickhouse("test_user_in_clickhouse")

    def test_permanent_redis_raises(self):
        """Redis kalıcı truth source olarak kullanılırsa ihlal."""
        with pytest.raises(StorageLayerViolation):
            StorageLayerGuard.assert_no_permanent_redis("test_permanent_redis")

    def test_mysql_for_ohlcv_raises(self):
        """OHLCV MySQL'e yazılamaz."""
        with pytest.raises(StorageLayerViolation):
            StorageLayerGuard.assert_mysql("ohlcv_write", "test_mysql_ohlcv")

    def test_clickhouse_for_user_raises(self):
        """Kullanıcı ClickHouse'a yazılamaz."""
        with pytest.raises(StorageLayerViolation):
            StorageLayerGuard.assert_clickhouse("user_write", "test_clickhouse_user")

    def test_redis_for_ohlcv_raises(self):
        """OHLCV (kalıcı write) Redis'e yazılamaz."""
        with pytest.raises(StorageLayerViolation):
            StorageLayerGuard.assert_redis("ohlcv_write", "test_redis_ohlcv")

    def test_is_allowed_true(self):
        assert StorageLayerGuard.is_allowed("clickhouse", "timeseries_write") is True
        assert StorageLayerGuard.is_allowed("mysql", "user_write") is True
        assert StorageLayerGuard.is_allowed("redis", "hot_cache_write") is True

    def test_is_allowed_false(self):
        assert StorageLayerGuard.is_allowed("mysql", "timeseries_write") is False
        assert StorageLayerGuard.is_allowed("clickhouse", "user_write") is False
        assert StorageLayerGuard.is_allowed("redis", "user_write") is False

    def test_policy_summary_returns_dict(self):
        summary = StorageLayerGuard.policy_summary()
        assert isinstance(summary, dict)
        assert "ohlcv_write" in summary
        assert "user_write" in summary
        assert "hot_cache_write" in summary
        # OHLCV sadece clickhouse
        assert summary["ohlcv_write"] == ["clickhouse"]
        # user_write sadece mysql
        assert summary["user_write"] == ["mysql"]

    def test_unknown_category_does_not_raise(self):
        """Bilinmeyen kategori uyarı verir ama ihlal fırlatmaz."""
        result = StorageLayerGuard.is_allowed("clickhouse", "bilinmeyen_kategori_xyz")
        assert result is True  # tanımsız = serbest

    def test_assert_allowed_with_storage_kind_enum(self):
        """StorageKind enum ile de çalışır."""
        StorageLayerGuard.assert_allowed(StorageKind.CLICKHOUSE, "ohlcv_write", "enum_test")

    def test_violation_message_contains_context(self):
        """İhlal mesajı bağlamı içermeli."""
        context = "benim_test_fonksiyonum"
        try:
            StorageLayerGuard.assert_mysql("ohlcv_write", context)
            pytest.fail("İhlal fırlatılmadı")
        except StorageLayerViolation as exc:
            assert context in str(exc)


# ─── ProviderFailover Testleri ───────────────────────────────────────────────

class TestProviderFailover:

    def _make_bars(self, close: float = 100.0, volume: float = 1000.0, ts: float = 1_700_000_000.0) -> list[dict]:
        return [{"time": ts * 1000, "open": close, "high": close, "low": close, "close": close, "volume": volume}]

    def test_primary_success_returns_primary(self):
        """Birincil başarılıysa o kullanılır."""
        bars = self._make_bars()

        async def primary(sym, itv, lim):
            return bars

        fo = ProviderFailover("primary", "fallback", primary_fn=primary)
        result = asyncio.get_event_loop().run_until_complete(
            fo.fetch_with_failover("BTCUSDT", "1h", 5)
        )
        assert result.source == "primary"
        assert result.source_switched is False
        assert result.bars == bars

    def test_primary_fails_uses_fallback(self):
        """Birincil başarısız olunca yedek devreye girer."""
        fallback_bars = self._make_bars(close=200.0)

        async def bad_primary(sym, itv, lim):
            raise ConnectionError("timeout")

        async def good_fallback(sym, itv, lim):
            return fallback_bars

        fo = ProviderFailover("primary", "fallback", primary_fn=bad_primary, fallback_fn=good_fallback)
        result = asyncio.get_event_loop().run_until_complete(
            fo.fetch_with_failover("BTCUSDT", "1h", 5)
        )
        assert result.source == "fallback"
        assert result.source_switched is True
        assert result.switched_from == "primary"
        assert "timeout" in (result.switch_reason or "")
        assert result.bars == fallback_bars

    def test_primary_empty_uses_fallback(self):
        """Birincil boş liste dönerse yedek devreye girer."""
        fallback_bars = self._make_bars()

        async def empty_primary(sym, itv, lim):
            return []

        async def good_fallback(sym, itv, lim):
            return fallback_bars

        fo = ProviderFailover("primary", "fallback", primary_fn=empty_primary, fallback_fn=good_fallback)
        result = asyncio.get_event_loop().run_until_complete(
            fo.fetch_with_failover("BTCUSDT", "1h", 5)
        )
        assert result.source_switched is True
        assert result.bars == fallback_bars

    def test_both_fail_returns_empty(self):
        """Her iki provider başarısız olursa boş sonuç döner."""
        async def bad(sym, itv, lim):
            raise RuntimeError("no data")

        fo = ProviderFailover("p", "f", primary_fn=bad, fallback_fn=bad)
        result = asyncio.get_event_loop().run_until_complete(
            fo.fetch_with_failover("BTCUSDT", "1h", 5)
        )
        assert result.bars == []
        assert result.source == "none"

    def test_no_alert_when_prices_match(self):
        """Fiyatlar yakınsa uyarı üretilmez."""
        bars1 = self._make_bars(close=100.0)
        bars2 = self._make_bars(close=100.1)

        async def prim(sym, itv, lim):
            return bars1

        async def fall(sym, itv, lim):
            return bars2

        fo = ProviderFailover("p1", "p2", primary_fn=prim, fallback_fn=fall)
        result = asyncio.get_event_loop().run_until_complete(
            fo.fetch_with_failover("BTCUSDT", "1h", 5)
        )
        assert result.comparison is not None
        assert not result.comparison.has_price_alert

    def test_price_alert_when_diff_exceeds_threshold(self):
        """Fiyat farkı eşiği aşınca uyarı üretilir."""
        bars1 = self._make_bars(close=100.0)
        bars2 = self._make_bars(close=100.0 * (1 + PRICE_DIFF_THRESHOLD_PCT / 100 + 0.01))

        async def prim(sym, itv, lim):
            return bars1

        async def fall(sym, itv, lim):
            return bars2

        fo = ProviderFailover("p1", "p2", primary_fn=prim, fallback_fn=fall)
        result = asyncio.get_event_loop().run_until_complete(
            fo.fetch_with_failover("BTCUSDT", "1h", 5)
        )
        assert result.comparison is not None
        assert result.comparison.has_price_alert

    def test_timestamp_alert_when_diff_large(self):
        """Timestamp farkı eşiği aşınca uyarı üretilir."""
        ts1 = 1_700_000_000.0
        ts2 = ts1 + TIMESTAMP_DIFF_THRESHOLD_S + 60
        bars1 = self._make_bars(ts=ts1)
        bars2 = self._make_bars(ts=ts2)

        async def prim(sym, itv, lim):
            return bars1

        async def fall(sym, itv, lim):
            return bars2

        fo = ProviderFailover("p1", "p2", primary_fn=prim, fallback_fn=fall)
        result = asyncio.get_event_loop().run_until_complete(
            fo.fetch_with_failover("BTCUSDT", "1h", 5)
        )
        assert result.comparison is not None
        assert result.comparison.has_timestamp_alert

    def test_comparison_to_dict(self):
        """Karşılaştırma dict'e dönüştürülebilir."""
        bars1 = self._make_bars(close=100.0)
        bars2 = self._make_bars(close=102.0)

        async def prim(sym, itv, lim):
            return bars1

        async def fall(sym, itv, lim):
            return bars2

        fo = ProviderFailover("p1", "p2", primary_fn=prim, fallback_fn=fall)
        result = asyncio.get_event_loop().run_until_complete(
            fo.fetch_with_failover("BTCUSDT", "1h", 5)
        )
        assert result.comparison is not None
        d = result.comparison.to_dict()
        assert "price_diff_pct" in d
        assert d["primary_provider"] == "p1"
        assert d["secondary_provider"] == "p2"


class TestProviderFailoverRegistry:

    def test_registry_routes_to_registered_failover(self):
        bars = [{"time": 1, "close": 100.0}]

        async def fn(sym, itv, lim):
            return bars

        fo = ProviderFailover("a", "b", primary_fn=fn)
        reg = ProviderFailoverRegistry()
        reg.register("BTCUSDT", fo)
        result = asyncio.get_event_loop().run_until_complete(
            reg.fetch("BTCUSDT", "1h", 5)
        )
        assert result.bars == bars

    def test_registry_uses_default_when_no_match(self):
        bars = [{"time": 1, "close": 50.0}]

        async def fn(sym, itv, lim):
            return bars

        fo = ProviderFailover("default_p", "default_f", primary_fn=fn)
        reg = ProviderFailoverRegistry()
        reg.set_default(fo)
        result = asyncio.get_event_loop().run_until_complete(
            reg.fetch("UNKNOWN_SYM", "1d", 5)
        )
        assert result.bars == bars

    def test_registry_returns_empty_without_failover(self):
        reg = ProviderFailoverRegistry()
        result = asyncio.get_event_loop().run_until_complete(
            reg.fetch("XYZ", "1h", 5)
        )
        assert result.bars == []
        assert result.source == "none"
