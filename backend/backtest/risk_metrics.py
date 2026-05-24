"""
risk_metrics.py — Genişletilmiş risk metrikleri.

Runner'daki temel metriklere ek olarak:
  - Drawdown duration (max çöküş süresi — bar/gün)
  - Exposure time (piyasada olma oranı)
  - Turnover (yıllık devir hızı)
  - Capacity estimate (kapasite tahmini — TL)
  - Tail risk (kuyruk riski skoru)
  - Statistical power (istatistiksel yeterlilik notu)
  - WFA overfit skoru (train/test performans sapması)

Ayrıca WFA raporuna açık overfit uyarısı ekler:
  - IS (in-sample) ortalama skoru >> OOS (out-of-sample) ortalama → overfit
  - Overfit skoru: IS/OOS oranı → 1'e ne kadar yakın, o kadar sağlıklı.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any


# ─── Drawdown Süresi ──────────────────────────────────────────────────────────

def max_drawdown_duration(equity_curve: list[float]) -> int:
    """
    Maksimum drawdown süresini bar/periyot sayısı olarak hesaplar.
    Peak'ten yeni peak'e kadar geçen en uzun süre.
    """
    if len(equity_curve) < 2:
        return 0
    max_dur = 0
    peak_idx = 0
    peak_val = equity_curve[0]
    current_dd_start = 0

    for i, val in enumerate(equity_curve):
        if val >= peak_val:
            if current_dd_start < i:
                dur = i - current_dd_start
                max_dur = max(max_dur, dur)
            peak_val = val
            peak_idx = i
            current_dd_start = i

    # Seri hâlâ çöküşteyse son segmenti de say
    if current_dd_start < len(equity_curve) - 1:
        dur = len(equity_curve) - 1 - current_dd_start
        max_dur = max(max_dur, dur)

    return max_dur


# ─── Exposure Time ────────────────────────────────────────────────────────────

def exposure_time_pct(positions: list[float | int]) -> float:
    """
    Piyasada olma oranı (0–100%).
    positions: Her bar için pozisyon büyüklüğü listesi (0 = dışarıda).
    """
    if not positions:
        return 0.0
    in_market = sum(1 for p in positions if p != 0)
    return round(in_market / len(positions) * 100, 2)


# ─── Turnover ─────────────────────────────────────────────────────────────────

def annual_turnover(
    trades: list[Any],
    capital: float,
    total_bars: int,
    bars_per_year: int = 252,
) -> float:
    """
    Yıllık devir hızı = (toplam işlem hacmi / kapital) * (bars_per_year / total_bars).
    """
    if not trades or capital <= 0 or total_bars <= 0:
        return 0.0
    total_volume = sum(
        abs(float(getattr(t, "entry_price", 0)) * float(getattr(t, "quantity", 0)))
        for t in trades
    )
    annualization = bars_per_year / total_bars
    return round((total_volume / capital) * annualization * 2, 4)  # x2: giriş + çıkış


# ─── Capacity Estimate ────────────────────────────────────────────────────────

def capacity_estimate_tl(
    avg_daily_volume_tl: float | None,
    volume_limit_pct: float = 0.05,
    max_position_pct: float = 0.20,
    capital: float = 100_000.0,
) -> dict[str, Any]:
    """
    Strateji kapasitesi tahmini (TL).

    Hacim yoksa uyarı, var ise:
      max_order_size = günlük hacim * volume_limit_pct
      implied_capital = max_order_size / max_position_pct
    """
    if not avg_daily_volume_tl or avg_daily_volume_tl <= 0:
        return {
            "available": False,
            "implied_max_capital_tl": None,
            "max_single_order_tl": None,
            "warning": "Ortalama hacim verisi eksik — kapasite tahmini yapılamadı.",
        }

    max_order_tl = avg_daily_volume_tl * volume_limit_pct
    implied_capital = max_order_tl / max_position_pct if max_position_pct > 0 else None

    return {
        "available":               True,
        "implied_max_capital_tl":  round(implied_capital, 0) if implied_capital else None,
        "max_single_order_tl":     round(max_order_tl, 0),
        "avg_daily_volume_tl":     round(avg_daily_volume_tl, 0),
        "volume_limit_pct":        volume_limit_pct,
        "warning": (
            f"Kapasite tahmini: günlük hacmin %{volume_limit_pct*100:.0f}'ini aşmayın. "
            f"İzin verilen tek emir ≈ {max_order_tl:,.0f} TL."
        ) if implied_capital and implied_capital < capital * 5 else None,
    }


# ─── Tail Risk ────────────────────────────────────────────────────────────────

def tail_risk_score(
    returns_pct: list[float],
    tail_quantile: float = 0.05,
) -> dict[str, float]:
    """
    Kuyruk riski metrikleri.
    returns_pct: İşlem bazında getiri yüzdeleri listesi.
    """
    if len(returns_pct) < 5:
        return {"tail_risk_score": 0.0, "left_tail_avg_pct": 0.0, "skewness": 0.0, "kurtosis": 0.0}

    sorted_ret = sorted(returns_pct)
    cutoff_idx = max(0, int(len(sorted_ret) * tail_quantile) - 1)
    left_tail = sorted_ret[: cutoff_idx + 1]
    left_tail_avg = statistics.mean(left_tail) if left_tail else 0.0

    mean = statistics.mean(returns_pct)
    std = statistics.pstdev(returns_pct)

    # Momentler
    n = len(returns_pct)
    skewness = 0.0
    kurtosis = 0.0
    if std > 0:
        skewness = sum((r - mean) ** 3 for r in returns_pct) / (n * std**3)
        kurtosis = sum((r - mean) ** 4 for r in returns_pct) / (n * std**4) - 3  # excess

    # Kuyruk riski skoru: abs(left_tail_avg) normalize edilmiş (0 = az, 100 = çok kötü)
    score = min(100.0, abs(left_tail_avg) * 10)

    return {
        "tail_risk_score":  round(score, 2),
        "left_tail_avg_pct": round(left_tail_avg, 4),
        "skewness":         round(skewness, 4),
        "excess_kurtosis":  round(kurtosis, 4),
        "fat_tails":        kurtosis > 1.0,
    }


# ─── Statistical Power ────────────────────────────────────────────────────────

@dataclass
class StatisticalNote:
    """Backtest istatistiksel yeterlilik notu."""
    trade_count: int
    period_bars: int
    rating: str        # "strong" | "moderate" | "weak" | "insufficient"
    message: str
    min_trades_recommended: int = 30

    def to_dict(self) -> dict[str, Any]:
        return {
            "trade_count":              self.trade_count,
            "period_bars":              self.period_bars,
            "rating":                   self.rating,
            "message":                  self.message,
            "min_trades_recommended":   self.min_trades_recommended,
        }


def statistical_note(trade_count: int, period_bars: int) -> StatisticalNote:
    """İşlem sayısına ve periyot uzunluğuna göre istatistiksel yeterlilik notunu döndürür."""
    if trade_count < 10:
        return StatisticalNote(
            trade_count=trade_count, period_bars=period_bars,
            rating="insufficient",
            message=(
                f"Yalnızca {trade_count} işlem var. Sonuçlar istatistiksel olarak anlamsız. "
                "En az 30 işlem önerilir."
            ),
        )
    if trade_count < 30:
        return StatisticalNote(
            trade_count=trade_count, period_bars=period_bars,
            rating="weak",
            message=(
                f"{trade_count} işlem — sonuçlar istatistiksel olarak zayıf. "
                "Şans ve gerçek performans ayrımı güç."
            ),
        )
    if trade_count < 100:
        return StatisticalNote(
            trade_count=trade_count, period_bars=period_bars,
            rating="moderate",
            message=f"{trade_count} işlem — makul istatistiksel güç. "
                    "Uzun vadeli doğrulama önerilir.",
        )
    return StatisticalNote(
        trade_count=trade_count, period_bars=period_bars,
        rating="strong",
        message=f"{trade_count} işlem — güçlü istatistiksel temel.",
    )


# ─── WFA Overfit Analizi ─────────────────────────────────────────────────────

@dataclass
class WFAOverfitReport:
    """WFA overfit analizi."""
    mean_is_score:          float        # Ortalama in-sample skor
    mean_oos_return_pct:    float        # Ortalama out-of-sample getiri
    overfit_ratio:          float        # IS/OOS oranı (1'e yakın = sağlıklı)
    overfit_score:          float        # 0=yok, 100=tam overfit
    verdict:                str          # "healthy" | "moderate" | "severe"
    warnings:               list[str] = field(default_factory=list)
    fold_details:           list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mean_is_score":       self.mean_is_score,
            "mean_oos_return_pct": self.mean_oos_return_pct,
            "overfit_ratio":       self.overfit_ratio,
            "overfit_score":       self.overfit_score,
            "verdict":             self.verdict,
            "warnings":            self.warnings,
            "fold_details":        self.fold_details,
        }


def wfa_overfit_analysis(wfa_report: dict[str, Any]) -> WFAOverfitReport:
    """
    WFA raporundan overfit skoru hesaplar.

    Overfit kriter:
      - IS ortalama >> OOS ortalama → overfit
      - overfit_ratio = mean_oos / mean_is (ideal: ~1.0)
      - overfit_score = max(0, (1 - overfit_ratio) * 100)
    """
    windows = wfa_report.get("windows", [])
    is_scores    = [w.get("in_sample_score", 0.0) for w in windows]
    oos_returns  = [w.get("out_of_sample_return_pct", 0.0) for w in windows]
    warnings: list[str] = []

    if not windows:
        return WFAOverfitReport(
            mean_is_score=0.0, mean_oos_return_pct=0.0,
            overfit_ratio=0.0, overfit_score=0.0, verdict="insufficient",
            warnings=["WFA penceresi yok — overfit analizi yapılamadı."],
        )

    mean_is  = statistics.mean(is_scores) if is_scores else 0.0
    mean_oos = statistics.mean(oos_returns) if oos_returns else 0.0

    # Oran hesabı — IS sıfıra yakınsa bölme yapma
    if abs(mean_is) < 1e-6:
        ratio = 1.0 if abs(mean_oos) < 1e-6 else 0.0
    else:
        ratio = mean_oos / mean_is

    # Overfit skoru: ratio ne kadar küçükse (negatifse de dahil) o kadar overfit
    raw_score = max(0.0, (1.0 - ratio) * 100)
    score = min(100.0, raw_score)

    if ratio < 0:
        verdict = "severe"
        warnings.append(
            f"AĞIR OVERFIT: IS ortalama skor={mean_is:.2f}%, OOS ortalama={mean_oos:.2f}%. "
            "OOS negatif — strateji eğitim verisine aşırı uyum sağlamış."
        )
    elif score > 60:
        verdict = "severe"
        warnings.append(
            f"AĞIR OVERFIT (skor={score:.0f}/100): IS={mean_is:.2f}% >> OOS={mean_oos:.2f}%. "
            "Parametre sayısını azaltın veya daha uzun OOS periyodu kullanın."
        )
    elif score > 30:
        verdict = "moderate"
        warnings.append(
            f"ORTA OVERFIT (skor={score:.0f}/100): IS={mean_is:.2f}% > OOS={mean_oos:.2f}%. "
            "WFA doğrulaması daha fazla fold ile tekrarlanmalı."
        )
    else:
        verdict = "healthy"

    fold_details = [
        {
            "fold":             i + 1,
            "is_score":         round(is_scores[i], 4),
            "oos_return_pct":   round(oos_returns[i], 4),
            "fold_ratio":       round(oos_returns[i] / is_scores[i], 4) if abs(is_scores[i]) > 1e-6 else None,
        }
        for i in range(len(windows))
    ]

    return WFAOverfitReport(
        mean_is_score=round(mean_is, 4),
        mean_oos_return_pct=round(mean_oos, 4),
        overfit_ratio=round(ratio, 4),
        overfit_score=round(score, 2),
        verdict=verdict,
        warnings=warnings,
        fold_details=fold_details,
    )


# ─── Tümleşik Metrik Hesaplayıcı ─────────────────────────────────────────────

def compute_extended_metrics(
    *,
    trades: list[Any],
    equity_curve: list[float],
    positions: list[float] | None = None,
    capital: float = 100_000.0,
    total_bars: int = 0,
    avg_daily_volume_tl: float | None = None,
    volume_limit_pct: float = 0.05,
    max_position_pct: float = 0.20,
    bars_per_year: int = 252,
    wfa_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Tek çağrıyla tüm genişletilmiş metrikleri döndür.
    Runner tarafından çağrılır; standart metrik dict'ine merge edilir.
    """
    trade_returns = [
        float(getattr(t, "net_pnl", 0.0)) / capital * 100
        for t in trades
        if capital > 0
    ]

    result: dict[str, Any] = {}

    # Drawdown süresi
    result["max_drawdown_duration_bars"] = max_drawdown_duration(equity_curve)

    # Exposure time
    if positions is not None:
        result["exposure_time_pct"] = exposure_time_pct(positions)
    else:
        # Pozisyon listesi yoksa trade'lerden yaklaşık hesap
        if total_bars > 0 and trades:
            total_holding = sum(
                int(getattr(t, "exit_bar", total_bars) - getattr(t, "entry_bar", 0))
                for t in trades
                if hasattr(t, "exit_bar") and hasattr(t, "entry_bar")
            )
            result["exposure_time_pct"] = round(total_holding / total_bars * 100, 2)

    # Turnover
    result["annual_turnover"] = annual_turnover(trades, capital, total_bars, bars_per_year)

    # Kapasite tahmini
    result["capacity"] = capacity_estimate_tl(
        avg_daily_volume_tl,
        volume_limit_pct=volume_limit_pct,
        max_position_pct=max_position_pct,
        capital=capital,
    )

    # Kuyruk riski
    result["tail_risk"] = tail_risk_score(trade_returns)

    # İstatistiksel not
    result["statistical_note"] = statistical_note(
        trade_count=len(trades),
        period_bars=total_bars,
    ).to_dict()

    # WFA overfit analizi
    if wfa_report:
        overfit = wfa_overfit_analysis(wfa_report)
        result["wfa_overfit"] = overfit.to_dict()

    return result
