from __future__ import annotations

import pytest

from quant_engine.data.live_feed import (
    DataMetadata,
    LiveDataService,
    PaperTradingRecorder,
    normalize_symbol,
    resolve_symbol,
)
from quant_engine.data.market_data import MarketDataResult, MarketDataStatus


def test_normalize_symbol_removes_market_separators():
    assert normalize_symbol("btc/usdt") == "BTCUSDT"
    assert normalize_symbol(" XU100.IS ") == "XU100"


def test_resolve_symbol_routes_public_sources():
    btc = resolve_symbol("BTC/USDT")
    usdtry = resolve_symbol("USDTRY")
    thyao = resolve_symbol("THYAO")

    assert btc.provider == "ccxt"
    assert btc.source_symbol == "BTC/USDT"
    assert usdtry.provider == "yfinance"
    assert usdtry.source_symbol == "USDTRY=X"
    assert thyao.provider == "yfinance"
    assert thyao.source_symbol == "THYAO.IS"


def test_data_metadata_is_read_only_by_default():
    metadata = DataMetadata(
        symbol="BTCUSDT",
        normalized_symbol="BTCUSDT",
        provider="ccxt",
        source="Binance Public API",
        fetched_at="2026-04-25T10:00:00+00:00",
        last_bar_at="2026-04-25T09:59:00+00:00",
        status="live",
    )

    assert metadata.to_dict()["read_only"] is True


class FakeLiveDataService:
    def fetch_chart(self, symbol: str, limit: int = 40):
        return {
            "symbol": "BTCUSDT",
            "display_name": "BTC/USDT",
            "status": "ok",
            "quote": {"last": 100.0},
            "metadata": {
                "source": "Binance Public API",
                "fetched_at": "2026-04-25T10:00:00+00:00",
            },
        }


def test_paper_recorder_writes_virtual_trade_with_real_price_payload(tmp_path):
    recorder = PaperTradingRecorder(
        data_service=FakeLiveDataService(),
        workspace_path=tmp_path / "workspace.json",
    )

    trade = recorder.record_signal(
        {
            "symbol": "BTCUSDT",
            "side": "buy",
            "strategy": "Test Stratejisi",
            "bot_name": "Botum",
            "virtual_balance": "1000",
        }
    )

    assert trade["read_only"] is True
    assert trade["entry_price"] == 100.0
    assert trade["status"] == "open_virtual"


def test_paper_recorder_rejects_invalid_side(tmp_path):
    recorder = PaperTradingRecorder(
        data_service=FakeLiveDataService(),
        workspace_path=tmp_path / "workspace.json",
    )

    with pytest.raises(ValueError):
        recorder.record_signal({"symbol": "BTCUSDT", "side": "hold"})


# ── v2 fetch_candles validation & routing ──────────────────────────────────────


def test_fetch_candles_rejects_empty_symbol():
    svc = LiveDataService()
    payload = svc.fetch_candles("", interval="15m", limit=100)
    assert payload["status"] == "error"
    assert payload["bars"] == []
    assert payload["metadata"]["error"] == "symbol_required"


def test_fetch_candles_rejects_invalid_interval():
    svc = LiveDataService()
    payload = svc.fetch_candles("BTCUSDT", interval="bogus", limit=100)
    assert payload["status"] == "error"
    assert payload["bars"] == []
    assert payload["metadata"]["error"] == "invalid_interval"
    assert "15m" in payload["metadata"]["supported"]


def test_fetch_candles_clamps_below_minimum_limit(monkeypatch):
    svc = LiveDataService()
    captured: dict[str, int] = {}

    def fake_fetch(symbol, timeframe, limit):
        captured["limit"] = limit
        return MarketDataResult(
            symbol=symbol,
            market="bist",
            timeframe=timeframe,
            data=[],
            source="test",
            is_real=False,
            status=MarketDataStatus.NO_DATA,
            provider_name="test",
        )

    monkeypatch.setattr(svc._provider_router, "fetch_candles", fake_fetch)
    svc.fetch_candles("THYAO.IS", interval="15m", limit=5)
    assert captured["limit"] == 20  # min floor


def test_fetch_candles_clamps_above_maximum_limit(monkeypatch):
    svc = LiveDataService()
    captured: dict[str, int] = {}

    def fake_fetch(symbol, timeframe, limit):
        captured["limit"] = limit
        return MarketDataResult(
            symbol=symbol,
            market="bist",
            timeframe=timeframe,
            data=[],
            source="test",
            is_real=False,
            status=MarketDataStatus.NO_DATA,
            provider_name="test",
        )

    monkeypatch.setattr(svc._provider_router, "fetch_candles", fake_fetch)
    svc.fetch_candles("THYAO.IS", interval="15m", limit=99999)
    assert captured["limit"] == 1000  # max ceiling


@pytest.mark.parametrize(
    "raw,expected_provider,expected_source,expected_market",
    [
        ("BTCUSDT", "ccxt", "BTC/USDT", "crypto"),
        ("ETHUSDT", "ccxt", "ETH/USDT", "crypto"),
        ("THYAO.IS", "yfinance", "THYAO.IS", "bist"),
        ("USDTRY=X", "yfinance", "USDTRY=X", "fx"),
        ("GC=F", "yfinance", "GC=F", "commodity"),
        ("AAPL", "yfinance", "AAPL", "us_equity"),
    ],
)
def test_v2_resolve_routes_native_symbol_to_correct_provider(
    raw, expected_provider, expected_source, expected_market
):
    spec = LiveDataService._resolve_v2(raw)
    assert spec.provider == expected_provider
    assert spec.source_symbol == expected_source
    assert spec.market == expected_market


def test_v2_resolve_xu100_alias_maps_to_yfinance():
    spec = LiveDataService._resolve_v2("XU100")
    assert spec.provider == "yfinance"
    assert spec.source_symbol == "XU100.IS"
    assert spec.market == "bist"
