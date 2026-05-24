"""
corporate_action.py — Kurumsal aksiyon tespiti ve veri düzeltme standardı.

Desteklenen olay tipleri:
  dividend       — Temettü (nakit)
  rights_issue   — Bedelli sermaye artırımı
  bonus_issue    — Bedelsiz sermaye artırımı (hisse bölünmesi benzeri)
  split          — Hisse bölünmesi (stock split)
  reverse_split  — Ters bölünme (reverse split)
  merger         — Birleşme / devralma
  delisting      — Borsa kaydının silinmesi

Kullanım:
    from backend.backtest.corporate_action import CorporateActionChecker, CorporateAction

    checker = CorporateActionChecker()
    actions = checker.detect_from_price_series(closes, dates)
    report = checker.check_adjustment_status(symbol, series_type="raw")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any


class ActionType(str, Enum):
    DIVIDEND      = "dividend"
    RIGHTS_ISSUE  = "rights_issue"
    BONUS_ISSUE   = "bonus_issue"
    SPLIT         = "split"
    REVERSE_SPLIT = "reverse_split"
    MERGER        = "merger"
    DELISTING     = "delisting"
    UNKNOWN       = "unknown"


@dataclass
class CorporateAction:
    """Tek bir kurumsal aksiyon kaydı."""
    symbol:       str
    action_type:  ActionType
    ex_date:      date | None          # Ex-dividend / ex-right tarihi
    ratio:        float | None = None  # Bölünme oranı, temettü yüzdesi vb.
    amount:       float | None = None  # Nakit temettü tutarı (TL/hisse)
    description:  str = ""
    source:       str = "detected"    # "kap", "yahoo", "detected", "manual"
    confidence:   float = 1.0         # 0..1 — tespit güven skoru

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol":      self.symbol,
            "action_type": self.action_type.value,
            "ex_date":     self.ex_date.isoformat() if self.ex_date else None,
            "ratio":       self.ratio,
            "amount":      self.amount,
            "description": self.description,
            "source":      self.source,
            "confidence":  self.confidence,
        }


@dataclass
class AdjustmentStatus:
    """Fiyat serisinin düzeltilmiş / ham durumu raporu."""
    symbol:                str
    series_type:           str             # "raw" veya "adjusted"
    detected_actions:      list[CorporateAction] = field(default_factory=list)
    has_unadjusted_splits: bool = False    # Ham veride bölünme var mı?
    has_unadjusted_divs:   bool = False    # Ham veride temettü düşümü görünüyor mu?
    long_term_warning:     bool = False    # 1 yıldan uzun ham seri → uyarı
    warnings:              list[str] = field(default_factory=list)
    recommendations:       list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol":                self.symbol,
            "series_type":           self.series_type,
            "detected_actions":      [a.to_dict() for a in self.detected_actions],
            "has_unadjusted_splits": self.has_unadjusted_splits,
            "has_unadjusted_divs":   self.has_unadjusted_divs,
            "long_term_warning":     self.long_term_warning,
            "warnings":              self.warnings,
            "recommendations":       self.recommendations,
        }


# ─── Tespit ──────────────────────────────────────────────────────────────────

# Hisse bölünmesi için günlük fiyat düşüşü eşiği (yaklaşık)
_SPLIT_DROP_THRESHOLD = 0.40   # Bir günde %40+ düşüş → split şüphesi
_DIV_DROP_MIN_PCT     = 0.01   # %1 altı düşüş temettü değil (gürültü)
_DIV_DROP_MAX_PCT     = 0.10   # %10 üstü düşüş temettü değil (split şüphesi)


class CorporateActionChecker:
    """Fiyat serisinden kurumsal aksiyon tespit eder ve uyarı üretir."""

    def detect_from_price_series(
        self,
        closes: list[float],
        dates: list[date | str | None] | None = None,
        symbol: str = "UNKNOWN",
    ) -> list[CorporateAction]:
        """
        Kapanış fiyatlarından olası kurumsal aksiyonları tespit eder.

        Çalışma prensibi:
          - Ardışık barlar arasında büyük fiyat düşüşü → split veya temettü.
          - %40+ düşüş → split şüphesi.
          - %1–%10 düşüş → temettü şüphesi.
        """
        actions: list[CorporateAction] = []
        if len(closes) < 2:
            return actions

        for i in range(1, len(closes)):
            prev = closes[i - 1]
            curr = closes[i]
            if prev <= 0 or curr <= 0:
                continue

            change_pct = (curr - prev) / prev
            ex_date_raw = dates[i] if dates and i < len(dates) else None
            ex_date = _parse_date(ex_date_raw)

            if change_pct <= -_SPLIT_DROP_THRESHOLD:
                # Büyük düşüş → split veya reverse split
                ratio = prev / curr if curr > 0 else None
                actions.append(CorporateAction(
                    symbol=symbol,
                    action_type=ActionType.SPLIT,
                    ex_date=ex_date,
                    ratio=round(ratio, 4) if ratio else None,
                    description=f"Olası bölünme: {change_pct*100:.1f}% düşüş ({prev:.2f}→{curr:.2f})",
                    source="detected",
                    confidence=0.80 if abs(change_pct) > 0.45 else 0.60,
                ))

            elif -_DIV_DROP_MAX_PCT <= change_pct <= -_DIV_DROP_MIN_PCT:
                # Orta düşüş → temettü şüphesi
                div_amount = abs(curr - prev)
                actions.append(CorporateAction(
                    symbol=symbol,
                    action_type=ActionType.DIVIDEND,
                    ex_date=ex_date,
                    amount=round(div_amount, 4),
                    description=f"Olası temettü düşümü: {change_pct*100:.1f}% ({prev:.2f}→{curr:.2f})",
                    source="detected",
                    confidence=0.50,
                ))

        return actions

    def check_adjustment_status(
        self,
        symbol: str,
        closes: list[float],
        dates: list[date | str | None] | None = None,
        series_type: str = "unknown",
        period_days: int | None = None,
    ) -> AdjustmentStatus:
        """
        Fiyat serisinin ham mı düzeltilmiş mi olduğunu değerlendiren rapor üretir.

        Kabul kriterleri:
          - Ham seri + bölünme tespiti → has_unadjusted_splits = True, uzun dönem uyarısı
          - Ham seri + 1 yıldan uzun periyot → uyarı
          - Düzeltilmiş seri + bölünme yok → temiz

        Args:
            symbol: Sembol kodu.
            closes: Kapanış fiyatları.
            series_type: "raw" | "adjusted" | "unknown"
            period_days: Periyot uzunluğu (gün). Belirtilmezse len(closes) kullanılır.
        """
        detected = self.detect_from_price_series(closes, dates, symbol=symbol)
        splits   = [a for a in detected if a.action_type == ActionType.SPLIT]
        dividends = [a for a in detected if a.action_type == ActionType.DIVIDEND]

        warnings: list[str] = []
        recommendations: list[str] = []
        days = period_days if period_days is not None else len(closes)

        has_unadjusted_splits = bool(splits) and series_type != "adjusted"
        has_unadjusted_divs   = bool(dividends) and series_type != "adjusted"
        long_term_warning     = days > 252 and series_type == "raw"

        if series_type == "unknown":
            warnings.append(
                "Fiyat serisi ham (raw) mı, düzeltilmiş (adjusted) mi olduğu bilinmiyor. "
                "Backtest raporu veri kaynağını açıkça belirtmeli."
            )
            recommendations.append(
                "Veri sağlayıcıdan 'adjusted close' kullanın veya seri tipini belgeleyin."
            )

        if has_unadjusted_splits:
            for sp in splits:
                warnings.append(
                    f"Muhtemel bölünme ({sp.ex_date}) ham seride düzeltilmemiş görünüyor. "
                    f"Backtest sonuçları yanıltıcı olabilir. (Güven: {sp.confidence:.0%})"
                )
            recommendations.append(
                "Split-adjusted fiyat serisi kullanın ya da backtest başlangıç tarihini "
                "son bölünme sonrasına alın."
            )

        if has_unadjusted_divs:
            warnings.append(
                f"{len(dividends)} olası temettü düşümü tespit edildi. "
                "Ham fiyat serisiyle backtest performansı gerçek getirileri yansıtmıyor."
            )
            recommendations.append(
                "Toplam getiri (total return) veya temettü-adjusted seri kullanın."
            )

        if long_term_warning:
            warnings.append(
                f"Ham fiyat serisi {days} bar içeriyor (>252). "
                "Uzun dönem backtestlerde düzeltilmemiş seri ciddi sapmalara yol açar."
            )

        if not warnings and series_type == "adjusted":
            recommendations.append("Düzeltilmiş seri — kurumsal aksiyon etkisi normalleştirilmiş.")

        return AdjustmentStatus(
            symbol=symbol,
            series_type=series_type,
            detected_actions=detected,
            has_unadjusted_splits=has_unadjusted_splits,
            has_unadjusted_divs=has_unadjusted_divs,
            long_term_warning=long_term_warning,
            warnings=warnings,
            recommendations=recommendations,
        )

    @staticmethod
    def annotate_report(
        report: dict[str, Any],
        adjustment_status: AdjustmentStatus,
    ) -> dict[str, Any]:
        """
        Backtest rapor dict'ine corporate action bilgisini ekler.
        Mevcut warnings listesini genişletir; corporate_action anahtarı ekler.
        """
        report = dict(report)
        ca_dict = adjustment_status.to_dict()
        report["corporate_action"] = ca_dict

        # Uyarıları mevcut warnings listesine ekle
        existing_warnings: list[dict[str, Any]] = report.get("warnings", [])
        for w in adjustment_status.warnings:
            existing_warnings.append({
                "code": "CORPORATE_ACTION",
                "severity": "high" if adjustment_status.has_unadjusted_splits else "medium",
                "message": w,
            })
        report["warnings"] = existing_warnings
        return report


# ─── Yardımcı ────────────────────────────────────────────────────────────────

def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


# Singleton
corporate_action_checker = CorporateActionChecker()
