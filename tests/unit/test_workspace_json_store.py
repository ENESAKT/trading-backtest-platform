from __future__ import annotations

import json

from quant_engine.workspace.json_store import (
    WorkspaceJsonStore,
    validate_workspace_document,
)


def test_workspace_json_store_creates_default_document(tmp_path):
    path = tmp_path / "workspace.json"
    store = WorkspaceJsonStore(path)

    document = store.load()

    assert path.exists()
    assert validate_workspace_document(document) == []
    assert {source["provider"] for source in document["api_sources"]} >= {
        "yfinance",
        "binance",
    }


def test_workspace_json_store_upserts_sources_and_symbol_groups(tmp_path):
    store = WorkspaceJsonStore(tmp_path / "workspace.json")

    store.upsert_api_source(
        name="Matriks Test",
        provider="matriks",
        base_url="wss://example.test",
        auth_type="api_key",
        enabled=False,
        notes="credential gerektirir",
    )
    document = store.upsert_symbol_group(
        name="Kripto Liderleri",
        market="crypto",
        symbols=["BTCUSDT", "ETHUSDT", "BTCUSDT"],
    )
    document = store.upsert_dataset(
        name="Kripto Günlük",
        source="Binance Spot",
        market="crypto",
        timeframe="1d",
        layer="raw",
        symbols=["BTCUSDT", "ETHUSDT"],
    )

    assert any(source["name"] == "Matriks Test" for source in document["api_sources"])
    group = next(item for item in document["symbol_groups"] if item["name"] == "Kripto Liderleri")
    assert group["symbols"] == ["BTCUSDT", "ETHUSDT"]
    dataset = next(item for item in document["datasets"] if item["name"] == "Kripto Günlük")
    assert dataset["source"] == "Binance Spot"


def test_workspace_json_store_recovers_invalid_json(tmp_path):
    path = tmp_path / "workspace.json"
    path.write_text("{bad", encoding="utf-8")
    store = WorkspaceJsonStore(path)

    document = store.load()

    assert validate_workspace_document(document) == []
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == 1
