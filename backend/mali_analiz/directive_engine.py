"""Direktif ve uyarı motoru — Fastweb tarzı özet yorum üretir.

Her sembol için:
  - Yeni çeyrek bildirimi
  - Önemli metrik eşik aşımları (yüksek borç, düşük değerleme vb.)
  - Trend değişimleri
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from backend.mali_analiz.borsapy_provider import FinancialSnapshot
from backend.mali_analiz.ratio_engine import PeriodRatios

_log = logging.getLogger(__name__)


@dataclass
class Alert:
    alert_type: str           # new_period | metric_warning | metric_highlight | trend
    title: str
    body: str
    severity: str             # info | success | warning | danger
    period: str | None
    metric_key: str | None
    metric_value: float | None


def generate_directives(
    snap: FinancialSnapshot,
    period_ratios: list[PeriodRatios],
) -> list[Alert]:
    """Tek sembol için direktif listesi üretir."""
    alerts: list[Alert] = []

    if not period_ratios:
        return alerts

    latest = period_ratios[0]
    r = latest.ratios

    # ── Yeni çeyrek bildirimi ──────────────────────────────────────
    if snap.periods_quarterly:
        period_str = snap.periods_quarterly[0]
        alerts.append(Alert(
            alert_type="new_period",
            title=f"{snap.symbol} — {period_str} bilançosu mevcut",
            body=_build_summary(snap, r),
            severity="info",
            period=period_str,
            metric_key=None,
            metric_value=None,
        ))

    # ── Değerleme uyarıları ────────────────────────────────────────
    pd_dd = r.get("pd_dd")
    if pd_dd is not None:
        if 0 < pd_dd < 1:
            alerts.append(Alert(
                alert_type="metric_highlight",
                title=f"{snap.symbol} defter değerinin altında işlem görüyor",
                body=f"PD/DD = {pd_dd:.2f}x — piyasa değeri özkaynakların altında.",
                severity="success",
                period=latest.period,
                metric_key="pd_dd",
                metric_value=pd_dd,
            ))

    fk = r.get("fk")
    if fk is not None and 0 < fk < 5:
        alerts.append(Alert(
            alert_type="metric_highlight",
            title=f"{snap.symbol} düşük F/K oranı",
            body=f"F/K = {fk:.1f}x — tarihsel BIST ortalamasının (12-15x) çok altında.",
            severity="success",
            period=latest.period,
            metric_key="fk",
            metric_value=fk,
        ))

    # ── Borç uyarıları ────────────────────────────────────────────
    net_borc_ebitda = r.get("net_borc_ebitda")
    if net_borc_ebitda is not None:
        if net_borc_ebitda > 5:
            alerts.append(Alert(
                alert_type="metric_warning",
                title=f"{snap.symbol} çok yüksek kaldıraç",
                body=f"Net Borç/EBITDA = {net_borc_ebitda:.1f}x — kritik eşik (>5x).",
                severity="danger",
                period=latest.period,
                metric_key="net_borc_ebitda",
                metric_value=net_borc_ebitda,
            ))
        elif net_borc_ebitda > 3:
            alerts.append(Alert(
                alert_type="metric_warning",
                title=f"{snap.symbol} yüksek borç yükü",
                body=f"Net Borç/EBITDA = {net_borc_ebitda:.1f}x — dikkat eşiği (>3x).",
                severity="warning",
                period=latest.period,
                metric_key="net_borc_ebitda",
                metric_value=net_borc_ebitda,
            ))

    # ── Karlılık uyarıları ─────────────────────────────────────────
    net_kar_marji = r.get("net_kar_marji")
    if net_kar_marji is not None and net_kar_marji < 0:
        alerts.append(Alert(
            alert_type="metric_warning",
            title=f"{snap.symbol} zarar ediyor",
            body=f"Net Kar Marjı = {net_kar_marji:.1f}% — son çeyrekte zarar.",
            severity="danger",
            period=latest.period,
            metric_key="net_kar_marji",
            metric_value=net_kar_marji,
        ))

    # ── Büyüme uyarıları ──────────────────────────────────────────
    ciro_buyume = r.get("ciro_buyume")
    if ciro_buyume is not None:
        if ciro_buyume >= 30:
            alerts.append(Alert(
                alert_type="metric_highlight",
                title=f"{snap.symbol} güçlü ciro büyümesi",
                body=f"Ciro YoY büyümesi = %{ciro_buyume:.0f}.",
                severity="success",
                period=latest.period,
                metric_key="ciro_buyume",
                metric_value=ciro_buyume,
            ))
        elif ciro_buyume < -10:
            alerts.append(Alert(
                alert_type="metric_warning",
                title=f"{snap.symbol} ciro daralıyor",
                body=f"Ciro YoY değişimi = %{ciro_buyume:.0f}.",
                severity="warning",
                period=latest.period,
                metric_key="ciro_buyume",
                metric_value=ciro_buyume,
            ))

    # ── ROE trendi (son 4 çeyrek) ──────────────────────────────────
    if len(period_ratios) >= 4:
        roe_values = [pr.ratios.get("roe") for pr in period_ratios[:4]]
        roe_valid = [v for v in roe_values if v is not None]
        if len(roe_valid) >= 3:
            # Sürekli düşüş kontrolü
            if all(roe_valid[i] > roe_valid[i + 1] for i in range(len(roe_valid) - 1)):
                alerts.append(Alert(
                    alert_type="trend",
                    title=f"{snap.symbol} ROE son {len(roe_valid)} çeyrekte geriledi",
                    body=f"ROE trendi: {' → '.join(f'%{v:.0f}' for v in roe_valid)}",
                    severity="warning",
                    period=latest.period,
                    metric_key="roe",
                    metric_value=roe_valid[0],
                ))

    return alerts


def _build_summary(snap: FinancialSnapshot, r: dict) -> str:
    """Kısa özet metni oluşturur."""
    parts = []
    if r.get("net_kar_marji") is not None:
        parts.append(f"Net Kar Marjı: %{r['net_kar_marji']:.1f}")
    if r.get("roe") is not None:
        parts.append(f"ROE: %{r['roe']:.1f}")
    if r.get("ciro_buyume") is not None:
        parts.append(f"Ciro YoY: %{r['ciro_buyume']:.0f}")
    if r.get("net_borc_ebitda") is not None:
        parts.append(f"Net Borç/EBITDA: {r['net_borc_ebitda']:.1f}x")
    return " | ".join(parts) if parts else "Özet hesaplanamadı."
