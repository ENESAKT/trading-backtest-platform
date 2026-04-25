"""Çoklu piyasa workspace yöneticisi testleri."""

from __future__ import annotations

from quant_engine.core.protocols import Market, Timeframe
from quant_engine.data.providers.yfinance_provider import _to_yahoo_ticker
from quant_engine.workspace.manager import (
    WorkspaceRequest,
    build_workspace_config,
    resolve_workspace,
)


def test_bist_workspace_config_uses_two_decimals_and_isolated_key():
    resolution = resolve_workspace(
        WorkspaceRequest(
            symbol_id="EREGL.IS",
            market_type="BIST100",
            timeframe_label="1G",
        )
    )
    config = build_workspace_config(resolution)

    assert resolution.workspace_id.startswith("ws_")
    assert resolution.instrument.market == Market.BIST
    assert resolution.timeframe == Timeframe.D1
    assert config["calisma_alani_kurulumu"] == {
        "sembol_kodu": "EREGL",
        "tam_isim": "Ereğli Demir ve Çelik Fabrikaları T.A.Ş.",
        "piyasa_kategorisi": "BIST 100 / Hisse Senedi",
        "ondalik_hassasiyet": 2,
    }
    assert resolution.workspace_id in config["arayuz_bilesenleri"]["ana_grafik"]


def test_forex_workspace_config_uses_forex_precision_and_no_volume_fallback():
    resolution = resolve_workspace(
        WorkspaceRequest(
            symbol_id="USD/TRY",
            market_type="Forex",
            timeframe_label="4S",
        )
    )
    config = build_workspace_config(resolution)

    assert resolution.instrument.market == Market.FOREX
    assert resolution.instrument.precision == 4
    assert resolution.timeframe == Timeframe.H4
    assert "Forex / Fiat Döviz" == config["calisma_alani_kurulumu"]["piyasa_kategorisi"]
    assert "hacmi desteklenmiyorsa" in config["veri_baglanti_protokolu"]["talep_edilen_veri"]


def test_commodity_workspace_maps_xauusd_to_real_provider_symbol():
    resolution = resolve_workspace(
        WorkspaceRequest(
            symbol_id="XAUUSD",
            market_type="Emtia",
            timeframe_label="1G",
        )
    )

    assert resolution.instrument.market == Market.COMMODITY
    assert resolution.instrument.yahoo_ticker == "GC=F"
    assert resolution.valid is True


def test_unknown_non_bist_symbol_returns_waiting_protocol_without_fake_data():
    resolution = resolve_workspace(
        WorkspaceRequest(
            symbol_id="UNKNOWNPAIR",
            market_type="Forex",
            timeframe_label="15D",
        )
    )
    config = build_workspace_config(resolution)

    assert resolution.valid is False
    assert (
        "Geçerli piyasa veri sağlayıcı eşlemesi"
        in config["veri_baglanti_protokolu"]["hata_yonetimi"]
    )
    valid_config = build_workspace_config(
        resolve_workspace(WorkspaceRequest("EREGL", "BIST100", "1G"))
    )
    assert "sahte mum" in valid_config["veri_baglanti_protokolu"]["hata_yonetimi"]


def test_yfinance_ticker_mapping_respects_market_type():
    assert _to_yahoo_ticker("EREGL", Market.BIST) == "EREGL.IS"
    assert _to_yahoo_ticker("USDTRY", Market.FOREX) == "USDTRY=X"
    assert _to_yahoo_ticker("XAUUSD", Market.COMMODITY) == "GC=F"
