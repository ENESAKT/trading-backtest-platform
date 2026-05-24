"""
test_backtest_modules.py — slippage, corporate_action ve risk_metrics birim testleri.

Çalıştırma:
    cd /path/to/Backtest && PYTHONPATH=. pytest backend/tests/test_backtest_modules.py -v
"""

from __future__ import annotations

import math
from datetime import date

import pytest

from backend.backtest.slippage import (
    SlippageModel,
    OrderSide,
    SlippageResult,
    BISTCostResult,
    calculate_slippage,
    calculate_bist_cost,
    list_models,
)
from backend.backtest.corporate_action import (
    ActionType,
    CorporateAction,
    AdjustmentStatus,
    CorporateActionChecker,
    corporate_action_checker,
)
from backend.backtest.risk_metrics import (
    max_drawdown_duration,
    exposure_time_pct,
    annual_turnover,
    capacity_estimate_tl,
    tail_risk_score,
    statistical_note,
    wfa_overfit_analysis,
    compute_extended_metrics,
)


# ─── Slippage Testleri ────────────────────────────────────────────────────────

class TestSlippageFixedBps:
    def test_buy_increases_price(self):
        r = calculate_slippage(model="fixed_bps", side="buy", base_price=100.0, slippage_bps=10.0)
        assert r.fill_price > 100.0

    def test_sell_decreases_price(self):
        r = calculate_slippage(model="fixed_bps", side="sell", base_price=100.0, slippage_bps=10.0)
        assert r.fill_price < 100.0

    def test_bps_calculation(self):
        r = calculate_slippage(model="fixed_bps", side="buy", base_price=100.0, slippage_bps=100.0)
        assert abs(r.fill_price - 101.0) < 0.001

    def test_zero_slippage(self):
        r = calculate_slippage(model="fixed_bps", side="buy", base_price=50.0, slippage_bps=0.0)
        assert r.fill_price == pytest.approx(50.0, abs=0.001)

    def test_result_type(self):
        r = calculate_slippage(model="fixed_bps", side="buy", base_price=100.0)
        assert isinstance(r, SlippageResult)
        assert isinstance(r.warnings, list)


class TestSlippageFixedTick:
    def test_buy_adds_tick(self):
        r = calculate_slippage(model="fixed_tick", side="buy", base_price=100.0, slippage_tick=0.05)
        assert r.fill_price == pytest.approx(100.05, abs=0.0001)

    def test_sell_subtracts_tick(self):
        r = calculate_slippage(model="fixed_tick", side="sell", base_price=100.0, slippage_tick=0.05)
        assert r.fill_price == pytest.approx(99.95, abs=0.0001)


class TestSlippageSpread:
    def test_buy_at_ask(self):
        r = calculate_slippage(model="spread", side="buy", base_price=100.0, bid=99.9, ask=100.1)
        assert r.fill_price == pytest.approx(100.1, abs=0.0001)

    def test_sell_at_bid(self):
        r = calculate_slippage(model="spread", side="sell", base_price=100.0, bid=99.9, ask=100.1)
        assert r.fill_price == pytest.approx(99.9, abs=0.0001)

    def test_missing_bid_ask_fallback(self):
        r = calculate_slippage(model="spread", side="buy", base_price=100.0)
        assert r.warnings  # uyarı olmalı
        assert r.fill_price > 100.0  # fixed_bps'e düştü


class TestSlippageATR:
    def test_atr_model_buy(self):
        r = calculate_slippage(model="atr", side="buy", base_price=100.0, atr=2.0, atr_multiplier=0.25)
        assert r.fill_price == pytest.approx(100.5, abs=0.001)  # 100 + 2 * 0.25

    def test_atr_model_sell(self):
        r = calculate_slippage(model="atr", side="sell", base_price=100.0, atr=2.0, atr_multiplier=0.25)
        assert r.fill_price == pytest.approx(99.5, abs=0.001)

    def test_missing_atr_fallback(self):
        r = calculate_slippage(model="atr", side="buy", base_price=100.0, atr=None)
        assert r.warnings
        assert r.fill_price > 100.0


class TestSlippageVolumePct:
    def test_small_order_low_impact(self):
        r = calculate_slippage(
            model="volume_pct", side="buy", base_price=100.0,
            order_size=1_000, avg_daily_volume_tl=1_000_000,
            slippage_bps=5.0,
        )
        assert r.fill_price > 100.0

    def test_large_order_warning(self):
        r = calculate_slippage(
            model="volume_pct", side="buy", base_price=100.0,
            order_size=60_000, avg_daily_volume_tl=1_000_000,
            slippage_bps=5.0,
        )
        assert any("hacim" in w.lower() or "piyasa" in w.lower() for w in r.warnings)

    def test_zero_volume_fallback(self):
        r = calculate_slippage(model="volume_pct", side="buy", base_price=100.0, avg_daily_volume_tl=0.0)
        assert r.warnings


class TestSlippageGapOpen:
    def test_gap_adds_extra(self):
        r = calculate_slippage(
            model="gap_open", side="buy", base_price=102.0,
            prev_close=100.0, open_price=102.0, slippage_bps=5.0,
        )
        # %2 gap → ek bps var
        assert r.slippage_bps > 5.0

    def test_large_gap_warning(self):
        r = calculate_slippage(
            model="gap_open", side="buy", base_price=105.0,
            prev_close=100.0, open_price=105.0,
        )
        assert r.warnings

    def test_missing_prev_close_fallback(self):
        r = calculate_slippage(model="gap_open", side="buy", base_price=100.0)
        assert r.warnings


class TestSlippageLowLiquidity:
    def test_high_liquidity_no_penalty(self):
        r = calculate_slippage(
            model="low_liquidity", side="buy", base_price=100.0,
            slippage_bps=5.0, liquidity_score=0.9, low_liquidity_threshold=0.3,
        )
        assert not r.warnings

    def test_low_liquidity_adds_penalty(self):
        r = calculate_slippage(
            model="low_liquidity", side="buy", base_price=100.0,
            slippage_bps=5.0, liquidity_score=0.1, low_liquidity_threshold=0.3,
            low_liquidity_penalty_bps=50.0,
        )
        assert r.slippage_bps > 5.0
        assert r.warnings


class TestBISTCost:
    def test_basic_cost(self):
        result = calculate_bist_cost(price=100.0, quantity=100, side="buy")
        assert isinstance(result, BISTCostResult)
        assert result.commission_tl > 0
        assert result.bsmv_tl > 0
        assert result.total_cost_tl > 0

    def test_effective_bps_positive(self):
        result = calculate_bist_cost(price=100.0, quantity=100, side="buy")
        assert result.effective_bps > 0

    def test_tavan_warning(self):
        result = calculate_bist_cost(
            price=112.0, quantity=1, side="buy", prev_close=100.0
        )
        assert result.hit_limit is True
        assert result.warnings

    def test_taban_warning(self):
        result = calculate_bist_cost(
            price=88.0, quantity=1, side="sell", prev_close=100.0
        )
        assert result.hit_limit is True

    def test_no_limit_hit(self):
        result = calculate_bist_cost(
            price=105.0, quantity=1, side="buy", prev_close=100.0
        )
        assert result.hit_limit is False


class TestListModels:
    def test_returns_list(self):
        models = list_models()
        assert isinstance(models, list)
        assert len(models) == 7

    def test_has_required_keys(self):
        for m in list_models():
            assert "id" in m and "label" in m and "description" in m

    def test_model_ids_are_valid(self):
        ids = {m["id"] for m in list_models()}
        assert "fixed_bps" in ids
        assert "volume_pct" in ids


# ─── Corporate Action Testleri ───────────────────────────────────────────────

class TestCorporateActionDetection:
    def _checker(self):
        return CorporateActionChecker()

    def test_detect_split(self):
        closes = [100.0, 50.0]  # %50 düşüş → split
        actions = self._checker().detect_from_price_series(closes, symbol="TEST")
        splits = [a for a in actions if a.action_type == ActionType.SPLIT]
        assert len(splits) == 1

    def test_detect_dividend(self):
        closes = [100.0, 95.0]  # %5 düşüş → temettü şüphesi
        actions = self._checker().detect_from_price_series(closes, symbol="TEST")
        divs = [a for a in actions if a.action_type == ActionType.DIVIDEND]
        assert len(divs) == 1

    def test_no_action_small_change(self):
        closes = [100.0, 99.5]  # %0.5 düşüş → gürültü
        actions = self._checker().detect_from_price_series(closes, symbol="TEST")
        assert len(actions) == 0

    def test_no_action_large_gain(self):
        closes = [100.0, 150.0]  # Yükseliş → aksiyon değil
        actions = self._checker().detect_from_price_series(closes, symbol="TEST")
        assert len(actions) == 0

    def test_empty_series(self):
        actions = self._checker().detect_from_price_series([])
        assert actions == []

    def test_single_bar(self):
        actions = self._checker().detect_from_price_series([100.0])
        assert actions == []

    def test_split_ratio(self):
        closes = [100.0, 25.0]  # 4:1 split
        actions = self._checker().detect_from_price_series(closes, symbol="TEST")
        splits = [a for a in actions if a.action_type == ActionType.SPLIT]
        assert splits[0].ratio == pytest.approx(4.0, abs=0.01)

    def test_date_assigned(self):
        closes = [100.0, 50.0]
        dates = [date(2024, 1, 1), date(2024, 1, 2)]
        actions = self._checker().detect_from_price_series(closes, dates=dates, symbol="TEST")
        assert actions[0].ex_date == date(2024, 1, 2)

    def test_multiple_actions(self):
        closes = [100.0, 95.0, 47.0]  # Temettü, sonra split
        actions = self._checker().detect_from_price_series(closes, symbol="TEST")
        assert len(actions) == 2


class TestAdjustmentStatus:
    def _checker(self):
        return CorporateActionChecker()

    def test_raw_with_split_warns(self):
        closes = [100.0, 50.0]
        status = self._checker().check_adjustment_status(
            "TEST", closes, series_type="raw"
        )
        assert status.has_unadjusted_splits is True
        assert status.warnings

    def test_adjusted_no_split_warning(self):
        closes = [100.0, 50.0]
        status = self._checker().check_adjustment_status(
            "TEST", closes, series_type="adjusted"
        )
        assert status.has_unadjusted_splits is False

    def test_long_term_raw_warns(self):
        closes = [100.0] * 300  # 300 bar, ham seri
        status = self._checker().check_adjustment_status(
            "TEST", closes, series_type="raw", period_days=300
        )
        assert status.long_term_warning is True

    def test_unknown_series_type_warns(self):
        status = self._checker().check_adjustment_status(
            "TEST", [100.0, 105.0], series_type="unknown"
        )
        assert any("bilinmiyor" in w.lower() or "ham" in w.lower() for w in status.warnings)

    def test_to_dict_serializable(self):
        status = self._checker().check_adjustment_status("TEST", [100.0, 95.0])
        d = status.to_dict()
        assert "symbol" in d
        assert "detected_actions" in d
        assert isinstance(d["detected_actions"], list)


class TestAnnotateReport:
    def test_annotate_adds_corporate_action_key(self):
        checker = CorporateActionChecker()
        status = checker.check_adjustment_status("TEST", [100.0, 50.0], series_type="raw")
        report = {"warnings": [], "total_return_pct": 5.0}
        annotated = checker.annotate_report(report, status)
        assert "corporate_action" in annotated

    def test_annotate_extends_warnings(self):
        checker = CorporateActionChecker()
        status = checker.check_adjustment_status("TEST", [100.0, 50.0], series_type="raw")
        report = {"warnings": [{"code": "EXISTING", "message": "mevcut"}]}
        annotated = checker.annotate_report(report, status)
        assert len(annotated["warnings"]) > 1


class TestSingletonChecker:
    def test_singleton_exists(self):
        assert corporate_action_checker is not None
        assert isinstance(corporate_action_checker, CorporateActionChecker)


# ─── Risk Metrics Testleri ────────────────────────────────────────────────────

class TestMaxDrawdownDuration:
    def test_flat_curve_counts_inter_peak(self):
        # Düz seride peak-to-peak mesafesi 1 bar olarak hesaplanır
        assert max_drawdown_duration([100, 100, 100]) == 1

    def test_simple_drawdown(self):
        curve = [100, 90, 80, 100]  # peak(0) → recovery(3) = 3 bar
        assert max_drawdown_duration(curve) == 3

    def test_multiple_drawdowns(self):
        curve = [100, 90, 100, 80, 60, 100]
        # İlk segment: peak(0)→peak(2) = 2 bar
        # İkinci segment: peak(2)→peak(5) = 3 bar → max=3
        assert max_drawdown_duration(curve) == 3

    def test_never_recovers(self):
        curve = [100, 90, 80, 70]
        dur = max_drawdown_duration(curve)
        assert dur == 3

    def test_empty(self):
        assert max_drawdown_duration([]) == 0

    def test_single_bar(self):
        assert max_drawdown_duration([100.0]) == 0


class TestExposureTime:
    def test_all_in_market(self):
        assert exposure_time_pct([1, 2, 3, 4]) == 100.0

    def test_all_out(self):
        assert exposure_time_pct([0, 0, 0]) == 0.0

    def test_half_in_market(self):
        assert exposure_time_pct([1, 0, 1, 0]) == 50.0

    def test_empty(self):
        assert exposure_time_pct([]) == 0.0


class TestAnnualTurnover:
    class _FakeTrade:
        def __init__(self, entry_price, quantity):
            self.entry_price = entry_price
            self.quantity = quantity

    def test_basic_turnover(self):
        trades = [self._FakeTrade(100.0, 10)]
        to = annual_turnover(trades, capital=10_000.0, total_bars=252, bars_per_year=252)
        # 100*10 = 1000 TL hacim; 1000/10000 * 1 * 2 = 0.2
        assert to == pytest.approx(0.2, abs=0.001)

    def test_zero_capital_returns_zero(self):
        assert annual_turnover([], capital=0, total_bars=252) == 0.0

    def test_empty_trades_returns_zero(self):
        assert annual_turnover([], capital=10_000, total_bars=252) == 0.0


class TestCapacityEstimate:
    def test_no_volume_data(self):
        result = capacity_estimate_tl(None)
        assert result["available"] is False
        assert result["implied_max_capital_tl"] is None

    def test_with_volume(self):
        result = capacity_estimate_tl(avg_daily_volume_tl=1_000_000.0)
        assert result["available"] is True
        assert result["max_single_order_tl"] > 0
        assert result["implied_max_capital_tl"] is not None

    def test_volume_limit_applied(self):
        result = capacity_estimate_tl(avg_daily_volume_tl=1_000_000.0, volume_limit_pct=0.05)
        assert result["max_single_order_tl"] == pytest.approx(50_000.0, abs=1.0)

    def test_zero_volume_not_available(self):
        result = capacity_estimate_tl(0.0)
        assert result["available"] is False


class TestTailRiskScore:
    def test_insufficient_data(self):
        result = tail_risk_score([1.0, 2.0])
        assert result["tail_risk_score"] == 0.0

    def test_skewness_sign(self):
        # Sağa çarpık dağılım → pozitif skewness
        returns = [1, 1, 1, 1, 1, 1, 1, 1, 1, 10]
        result = tail_risk_score(returns)
        assert result["skewness"] > 0

    def test_negative_left_tail(self):
        returns = [-10.0, -5.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        result = tail_risk_score(returns)
        assert result["left_tail_avg_pct"] < 0

    def test_score_bounded(self):
        returns = [-50.0] * 20
        result = tail_risk_score(returns)
        assert 0 <= result["tail_risk_score"] <= 100

    def test_fat_tails_detected(self):
        # Aşırı kurtosis → fat_tails = True
        returns = [-20, -20, 0, 0, 0, 0, 0, 0, 0, 20, 20] * 5
        result = tail_risk_score(returns)
        assert "fat_tails" in result


class TestStatisticalNote:
    def test_insufficient(self):
        note = statistical_note(trade_count=5, period_bars=100)
        assert note.rating == "insufficient"

    def test_weak(self):
        note = statistical_note(trade_count=15, period_bars=200)
        assert note.rating == "weak"

    def test_moderate(self):
        note = statistical_note(trade_count=50, period_bars=500)
        assert note.rating == "moderate"

    def test_strong(self):
        note = statistical_note(trade_count=200, period_bars=2000)
        assert note.rating == "strong"

    def test_to_dict_keys(self):
        note = statistical_note(10, 100)
        d = note.to_dict()
        for k in ["trade_count", "period_bars", "rating", "message"]:
            assert k in d


class TestWFAOverfitAnalysis:
    def _make_report(self, is_scores, oos_returns):
        windows = [
            {"in_sample_score": s, "out_of_sample_return_pct": o}
            for s, o in zip(is_scores, oos_returns)
        ]
        return {"windows": windows}

    def test_empty_report(self):
        result = wfa_overfit_analysis({"windows": []})
        assert result.verdict == "insufficient"

    def test_healthy(self):
        report = self._make_report([10.0, 10.0], [9.5, 10.5])
        result = wfa_overfit_analysis(report)
        assert result.verdict == "healthy"
        assert result.overfit_score < 30

    def test_moderate_overfit(self):
        report = self._make_report([10.0, 10.0], [5.0, 6.0])
        result = wfa_overfit_analysis(report)
        assert result.verdict in ("moderate", "severe")

    def test_severe_overfit(self):
        report = self._make_report([10.0, 10.0], [-2.0, -3.0])
        result = wfa_overfit_analysis(report)
        assert result.verdict == "severe"

    def test_overfit_ratio_near_one_for_healthy(self):
        report = self._make_report([10.0], [10.0])
        result = wfa_overfit_analysis(report)
        assert result.overfit_ratio == pytest.approx(1.0, abs=0.01)

    def test_to_dict_keys(self):
        report = self._make_report([10.0], [9.0])
        result = wfa_overfit_analysis(report)
        d = result.to_dict()
        for k in ["mean_is_score", "mean_oos_return_pct", "overfit_score", "verdict", "warnings"]:
            assert k in d

    def test_fold_details_populated(self):
        report = self._make_report([10.0, 8.0], [9.0, 7.5])
        result = wfa_overfit_analysis(report)
        assert len(result.fold_details) == 2
        assert result.fold_details[0]["fold"] == 1


class TestComputeExtendedMetrics:
    class _FakeTrade:
        def __init__(self, net_pnl, entry_price=100.0, quantity=10):
            self.net_pnl = net_pnl
            self.entry_price = entry_price
            self.quantity = quantity

    def test_returns_dict(self):
        trades = [self._FakeTrade(500), self._FakeTrade(-200), self._FakeTrade(300)]
        result = compute_extended_metrics(
            trades=trades,
            equity_curve=[100_000, 100_500, 100_300, 100_600],
            capital=100_000.0,
            total_bars=252,
        )
        assert isinstance(result, dict)

    def test_has_expected_keys(self):
        trades = [self._FakeTrade(500)] * 5
        result = compute_extended_metrics(
            trades=trades,
            equity_curve=[100_000] * 10,
            capital=100_000.0,
            total_bars=252,
        )
        for key in ["max_drawdown_duration_bars", "annual_turnover", "capacity", "tail_risk", "statistical_note"]:
            assert key in result

    def test_with_wfa_report(self):
        trades = [self._FakeTrade(200)] * 5
        wfa = {"windows": [{"in_sample_score": 10.0, "out_of_sample_return_pct": 9.0}]}
        result = compute_extended_metrics(
            trades=trades,
            equity_curve=[100_000] * 10,
            capital=100_000.0,
            total_bars=252,
            wfa_report=wfa,
        )
        assert "wfa_overfit" in result

    def test_no_wfa_no_overfit_key(self):
        result = compute_extended_metrics(
            trades=[],
            equity_curve=[100_000],
            capital=100_000.0,
            total_bars=0,
        )
        assert "wfa_overfit" not in result
