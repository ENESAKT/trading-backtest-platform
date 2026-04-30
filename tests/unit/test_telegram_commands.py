from __future__ import annotations

import pytest

from backend.notifier import telegram_commands as commands


def _real_payload(symbol: str = "THYAO.IS", bars: int = 40) -> dict:
    rows = [
        {
            "time": 1_700_000_000 + i * 900,
            "open": 100.0 + i,
            "high": 101.0 + i,
            "low": 99.0 + i,
            "close": 100.5 + i,
            "volume": 1000.0,
        }
        for i in range(bars)
    ]
    return {
        "symbol": symbol,
        "display_name": symbol.replace(".IS", ""),
        "market": "bist",
        "interval": "15m",
        "status": "ok",
        "bars": rows,
        "quote": {"last": rows[-1]["close"]},
        "metadata": {
            "source": "Yahoo Finance (BIST best-effort public)",
            "is_real": True,
            "status": "ok",
            "provider_name": "bist_yfinance",
        },
    }


@pytest.mark.asyncio
async def test_cmd_fiyat_uses_real_provider_payload(monkeypatch):
    async def fake_api_get(path: str, timeout: float = 8.0):
        assert path.startswith("/api/v2/candles?symbol=THYAO")
        return _real_payload()

    monkeypatch.setattr(commands, "_api_get", fake_api_get)
    reply = await commands.cmd_fiyat("THYAO")
    assert "THYAO" in reply
    assert "Gerçek veri" in reply


@pytest.mark.asyncio
async def test_cmd_sinyal_blocks_untrusted_payload(monkeypatch):
    payload = _real_payload()
    payload["metadata"]["is_real"] = False

    async def fake_api_get(path: str, timeout: float = 8.0):
        return payload

    monkeypatch.setattr(commands, "_api_get", fake_api_get)
    reply = await commands.cmd_sinyal("THYAO")
    assert "sinyal üretilmedi" in reply


@pytest.mark.asyncio
async def test_cmd_sinyal_accepts_real_payload(monkeypatch):
    async def fake_api_get(path: str, timeout: float = 8.0):
        return _real_payload(bars=220)

    monkeypatch.setattr(commands, "_api_get", fake_api_get)
    reply = await commands.cmd_sinyal("THYAO")
    assert "Yatırım tavsiyesi değildir" in reply
