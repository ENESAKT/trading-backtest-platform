from __future__ import annotations

from quant_engine.strategy.persistence import StrategyStore


def test_strategy_store_is_append_only_for_same_name(tmp_path):
    store = StrategyStore(tmp_path / "strategies.sqlite3")

    first = store.save_strategy(
        name="THYAO planı",
        base_strategy="SMA Kesişimi",
        params={"fast_period": 10, "slow_period": 30},
        indicators=["SMA 20", "RSI 14"],
        symbol="THYAO",
        market="bist",
        timeframe="Günlük",
        notes="ilk sürüm",
    )
    second = store.save_strategy(
        name="THYAO planı",
        base_strategy="SMA Kesişimi",
        params={"fast_period": 20, "slow_period": 50},
        indicators=["SMA 50", "MACD"],
        symbol="THYAO",
        market="bist",
        timeframe="Günlük",
        notes="ikinci sürüm",
    )

    records = store.list_strategies()

    assert first.id != second.id
    assert len(records) == 2
    assert {record.checksum for record in records}
    assert store.get_strategy(first.id).params["fast_period"] == 10
    assert store.get_strategy(second.id).params["fast_period"] == 20


def test_strategy_store_rejects_empty_name(tmp_path):
    store = StrategyStore(tmp_path / "strategies.sqlite3")

    try:
        store.save_strategy(
            name=" ",
            base_strategy="RSI Dönüşü",
            params={},
            indicators=[],
            symbol="BTCUSDT",
            market="crypto",
            timeframe="Günlük",
        )
    except ValueError as exc:
        assert "boş olamaz" in str(exc)
    else:
        raise AssertionError("Boş strateji adı reddedilmeliydi")
