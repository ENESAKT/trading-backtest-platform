from __future__ import annotations

import pytest

from quant_engine.data.live_feed import (
    DataMetadata,
    PaperTradingRecorder,
    normalize_symbol,
    resolve_symbol,
)


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
