from __future__ import annotations

from urllib.parse import parse_qs, urlsplit

import pytest

from quant_engine.data.providers.http_ohlcv import _validated_url
from quant_engine.data_pipeline.storage_manager import StorageManager


def test_ohlcv_url_keeps_configured_origin() -> None:
    url = _validated_url(
        "https://data.example.com/v1/{symbol}?interval={interval}&limit={limit}",
        "THYAO",
        "15m",
        100,
    )

    parsed = urlsplit(url)
    assert parsed.hostname == "data.example.com"
    assert set(parse_qs(parsed.query)) == {"interval", "limit"}
    assert ".." not in url


@pytest.mark.parametrize(
    "template",
    [
        "http://data.example.com/v1/{symbol}",
        "https://{symbol}.example.com/v1/bars",
        "https://127.0.0.1/v1/{symbol}",
        "https://user:password@data.example.com/v1/{symbol}",
    ],
)
def test_ohlcv_url_rejects_unsafe_origins(template: str) -> None:
    with pytest.raises(ValueError):
        _validated_url(template, "THYAO", "1d", 10)


@pytest.mark.parametrize("symbol", ["../escape", "THYAO/../../admin", "THYAO?next=admin"])
def test_ohlcv_url_rejects_unsafe_symbols(symbol: str) -> None:
    with pytest.raises(ValueError):
        _validated_url("https://data.example.com/v1/{symbol}", symbol, "1d", 10)


def test_storage_paths_cannot_escape_data_directory(tmp_path) -> None:
    with StorageManager(data_dir=str(tmp_path)) as storage:
        valid = storage._symbol_path("thyao", "bist")
        assert valid.is_relative_to((tmp_path / "bist").resolve())

        for symbol in ("../escape", "THYAO/../../escape", "THYAO\nforged"):
            with pytest.raises(ValueError):
                storage._symbol_path(symbol, "bist")

        with pytest.raises(ValueError):
            storage._symbol_path("THYAO", "unknown")
