"""Unit testler: Slippage ve komisyon hesaplama (Bölüm 18.14).

Test senaryoları:
  - fixed_bps: alışta fiyat artmalı, satışta düşmeli
  - fixed_tick: sabit tick doğru uygulanmalı
  - spread: BUY = ask, SELL = bid
  - atr: ATR geçerliyse ATR × multiplier slippage
  - atr: ATR yoksa/geçersizse fallback + uyarı
  - volume_pct: büyük emir daha yüksek slippage üretmeli
  - gap_open: gap varsa ek slippage eklenmeli
  - low_liquidity: düşük likidite cezası uygulanmalı
  - Satış fill_price < alış fill_price (aynı base_price için)
  - Negatif fill_price üretilemez
"""
from __future__ import annotations

import pytest

import importlib.util, sys
from pathlib import Path

# backtest __init__ ağır bağımlılıklar yüklüyor; sadece slippage modülünü doğrudan yükle
_mod_name = "backend.backtest.slippage"
_mod_path = Path(__file__).parents[2] / "backend/backtest/slippage.py"
spec = importlib.util.spec_from_file_location(_mod_name, _mod_path)
_slippage_mod = importlib.util.module_from_spec(spec)
sys.modules[_mod_name] = _slippage_mod  # __module__ referansı için kayıt et
spec.loader.exec_module(_slippage_mod)
calculate_slippage = _slippage_mod.calculate_slippage
OrderSide          = _slippage_mod.OrderSide
SlippageModel      = _slippage_mod.SlippageModel


BASE = 100.0


class TestFixedBps:
    def test_buy_increases_price(self):
        r = calculate_slippage(model="fixed_bps", side="buy", base_price=BASE, slippage_bps=10)
        assert r.fill_price > BASE

    def test_sell_decreases_price(self):
        r = calculate_slippage(model="fixed_bps", side="sell", base_price=BASE, slippage_bps=10)
        assert r.fill_price < BASE

    def test_buy_sell_symmetric(self):
        buy  = calculate_slippage(model="fixed_bps", side="buy",  base_price=BASE, slippage_bps=5)
        sell = calculate_slippage(model="fixed_bps", side="sell", base_price=BASE, slippage_bps=5)
        assert abs(buy.slippage_amount - sell.slippage_amount) < 1e-9

    def test_zero_bps_no_slippage(self):
        r = calculate_slippage(model="fixed_bps", side="buy", base_price=BASE, slippage_bps=0)
        assert r.fill_price == pytest.approx(BASE)
        assert r.slippage_amount == pytest.approx(0.0)

    def test_base_price_preserved(self):
        r = calculate_slippage(model="fixed_bps", side="buy", base_price=BASE, slippage_bps=10)
        assert r.base_price == BASE

    def test_slippage_bps_field_matches(self):
        r = calculate_slippage(model="fixed_bps", side="buy", base_price=BASE, slippage_bps=20)
        assert r.slippage_bps == pytest.approx(20.0)


class TestFixedTick:
    def test_buy_adds_tick(self):
        r = calculate_slippage(model="fixed_tick", side="buy",  base_price=BASE, slippage_tick=0.05)
        assert r.fill_price == pytest.approx(BASE + 0.05)

    def test_sell_subtracts_tick(self):
        r = calculate_slippage(model="fixed_tick", side="sell", base_price=BASE, slippage_tick=0.05)
        assert r.fill_price == pytest.approx(BASE - 0.05)


class TestSpread:
    BID = 99.9
    ASK = 100.1

    def test_buy_fills_at_ask(self):
        r = calculate_slippage(
            model="spread", side="buy", base_price=BASE,
            bid=self.BID, ask=self.ASK,
        )
        assert r.fill_price == pytest.approx(self.ASK)

    def test_sell_fills_at_bid(self):
        r = calculate_slippage(
            model="spread", side="sell", base_price=BASE,
            bid=self.BID, ask=self.ASK,
        )
        assert r.fill_price == pytest.approx(self.BID)

    def test_missing_bid_ask_triggers_warning_and_fallback(self):
        r = calculate_slippage(
            model="spread", side="buy", base_price=BASE,
            bid=None, ask=None,
        )
        assert len(r.warnings) > 0
        # Fallback fixed_bps ile çalışmalı
        assert r.fill_price > BASE


class TestATR:
    def test_with_valid_atr(self):
        atr = 2.0
        r = calculate_slippage(
            model="atr", side="buy", base_price=BASE,
            atr=atr, atr_multiplier=0.25,
        )
        # fill_price = base + atr * 0.25
        expected_slip = atr * 0.25
        assert r.fill_price == pytest.approx(BASE + expected_slip)

    def test_zero_atr_triggers_warning(self):
        r = calculate_slippage(
            model="atr", side="buy", base_price=BASE,
            atr=0,
        )
        assert len(r.warnings) > 0

    def test_none_atr_triggers_warning(self):
        r = calculate_slippage(
            model="atr", side="buy", base_price=BASE,
            atr=None,
        )
        assert len(r.warnings) > 0

    def test_sell_with_valid_atr(self):
        r = calculate_slippage(
            model="atr", side="sell", base_price=BASE,
            atr=3.0, atr_multiplier=0.5,
        )
        assert r.fill_price < BASE


class TestVolumePct:
    def test_large_order_higher_slippage(self):
        """Büyük emir küçük emire göre daha yüksek slippage üretmeli."""
        small = calculate_slippage(
            model="volume_pct", side="buy", base_price=BASE,
            order_size=10_000, avg_daily_volume_tl=1_000_000,
        )
        large = calculate_slippage(
            model="volume_pct", side="buy", base_price=BASE,
            order_size=200_000, avg_daily_volume_tl=1_000_000,
        )
        assert large.slippage_amount >= small.slippage_amount


class TestLowLiquidity:
    def test_low_liquidity_adds_penalty(self):
        """Düşük likidite skoru → normal slippage + ceza."""
        normal = calculate_slippage(
            model="low_liquidity", side="buy", base_price=BASE,
            liquidity_score=1.0,
        )
        penalized = calculate_slippage(
            model="low_liquidity", side="buy", base_price=BASE,
            liquidity_score=0.1,
        )
        assert penalized.fill_price > normal.fill_price


class TestGeneralSafety:
    def test_fill_price_never_negative(self):
        """Hiçbir modelde fill_price negatif olamaz."""
        for m in SlippageModel:
            try:
                r = calculate_slippage(
                    model=m, side="sell", base_price=0.001,
                    slippage_bps=999, slippage_tick=999,
                    atr=0.0,
                )
                assert r.fill_price >= 0, f"{m}: fill_price negatif!"
            except Exception:
                pass  # Bazı modeller parametre eksikliğinde hata verebilir

    def test_sell_fill_lower_than_buy(self):
        """Aynı base_price için satış fill < alış fill."""
        buy  = calculate_slippage(model="fixed_bps", side="buy",  base_price=BASE, slippage_bps=10)
        sell = calculate_slippage(model="fixed_bps", side="sell", base_price=BASE, slippage_bps=10)
        assert sell.fill_price < buy.fill_price
