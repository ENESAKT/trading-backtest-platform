"""
slippage.py — Çoklu slippage model hesaplayıcı.

Engine (`quant_engine/backtest/engine.py`) değiştirilmez; bu modül
backtest raporlama ve UI katmanında kullanıcıya gerçekçi maliyet tahmini sunar.

Desteklenen modeller:
  fixed_bps       — Sabit baz puan (mevcut varsayılan)
  fixed_tick      — Sabit tick miktar
  spread          — Alış-satış farkına dayalı
  atr             — Gün içi volatiliteye (ATR) dayalı
  volume_pct      — Hacim katılım oranına dayalı
  gap_open        — Gapping açılış fiyatına dayalı
  low_liquidity   — Düşük hacimli semboller için ceza

Her model fill_price döndürür (slippage dahil).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any


class SlippageModel(str, Enum):
    FIXED_BPS      = "fixed_bps"
    FIXED_TICK     = "fixed_tick"
    SPREAD         = "spread"
    ATR            = "atr"
    VOLUME_PCT     = "volume_pct"
    GAP_OPEN       = "gap_open"
    LOW_LIQUIDITY  = "low_liquidity"


class OrderSide(str, Enum):
    BUY  = "buy"
    SELL = "sell"


@dataclass
class SlippageResult:
    model:           SlippageModel
    fill_price:      float          # Slippage dahil gerçekleşme fiyatı
    base_price:      float          # Slippage öncesi fiyat
    slippage_amount: float          # Fiyat farkı (abs)
    slippage_bps:    float          # Baz puan olarak karşılık
    warnings:        list[str]


def calculate_slippage(
    *,
    model: str | SlippageModel,
    side: str | OrderSide,
    base_price: float,
    # Model parametreleri
    slippage_bps: float = 5.0,
    slippage_tick: float = 0.01,
    # Spread bazlı
    bid: float | None = None,
    ask: float | None = None,
    # ATR bazlı
    atr: float | None = None,
    atr_multiplier: float = 0.25,   # ATR'ın kaçta biri slippage
    # Hacim bazlı
    order_size: float = 0.0,        # TL cinsinden emir büyüklüğü
    avg_daily_volume_tl: float = 0.0,  # Ortalama günlük hacim (TL)
    volume_participation_cap: float = 0.10,  # Max piyasa katılım oranı
    # Gap bazlı
    prev_close: float | None = None,
    open_price: float | None = None,
    # Düşük likidite cezası
    liquidity_score: float = 1.0,   # 0..1 arası; 1 = tam likidite
    low_liquidity_threshold: float = 0.3,
    low_liquidity_penalty_bps: float = 50.0,
) -> SlippageResult:
    """
    Seçilen modele göre slippage hesaplar ve fill_price döndürür.

    Args:
        model: Kullanılacak slippage modeli.
        side: Alış veya satış.
        base_price: Slippage uygulanmadan önceki fiyat.
        ... (model-spesifik parametreler)

    Returns:
        SlippageResult — fill_price ve detaylar.
    """
    m = SlippageModel(model) if isinstance(model, str) else model
    s = OrderSide(side.lower()) if isinstance(side, str) else side
    sign = 1.0 if s == OrderSide.BUY else -1.0  # Alışta fiyat artar, satışta düşer
    warnings: list[str] = []

    match m:
        case SlippageModel.FIXED_BPS:
            slip_pct = slippage_bps / 10_000
            fill = base_price * (1 + sign * slip_pct)

        case SlippageModel.FIXED_TICK:
            fill = base_price + sign * slippage_tick
            fill = max(fill, 0.0001)

        case SlippageModel.SPREAD:
            if bid is None or ask is None:
                warnings.append("Spread modeli için bid/ask gerekli; fixed_bps'e düşüldü.")
                slip_pct = slippage_bps / 10_000
                fill = base_price * (1 + sign * slip_pct)
            else:
                spread = ask - bid
                mid = (ask + bid) / 2.0
                if s == OrderSide.BUY:
                    fill = ask  # Alış: ask fiyatından
                else:
                    fill = bid  # Satış: bid fiyatından
                _ = spread  # raporlamada kullanılabilir

        case SlippageModel.ATR:
            if atr is None or atr <= 0:
                warnings.append("ATR modeli için geçerli ATR değeri gerekli; fixed_bps'e düşüldü.")
                slip_pct = slippage_bps / 10_000
                fill = base_price * (1 + sign * slip_pct)
            else:
                slip_amount = atr * atr_multiplier
                fill = base_price + sign * slip_amount

        case SlippageModel.VOLUME_PCT:
            if avg_daily_volume_tl <= 0 or order_size <= 0:
                warnings.append("Hacim modeli için order_size ve avg_daily_volume_tl > 0 gerekli; fixed_bps'e düşüldü.")
                slip_pct = slippage_bps / 10_000
                fill = base_price * (1 + sign * slip_pct)
            else:
                participation = min(order_size / avg_daily_volume_tl, volume_participation_cap)
                # Piyasa etkisi: Kyle (1985) karekök modeli
                market_impact_bps = 10.0 * math.sqrt(participation * 100)
                total_bps = slippage_bps + market_impact_bps
                fill = base_price * (1 + sign * total_bps / 10_000)
                if participation > 0.05:
                    warnings.append(
                        f"Emir, günlük hacmin {participation*100:.1f}%'ini oluşturuyor. "
                        f"Yüksek piyasa etkisi: {market_impact_bps:.1f} bps."
                    )

        case SlippageModel.GAP_OPEN:
            if prev_close is None or open_price is None:
                warnings.append("Gap modeli için prev_close ve open_price gerekli; fixed_bps'e düşüldü.")
                slip_pct = slippage_bps / 10_000
                fill = base_price * (1 + sign * slip_pct)
            else:
                gap_pct = abs(open_price - prev_close) / prev_close if prev_close > 0 else 0.0
                gap_bps = gap_pct * 10_000
                total_bps = slippage_bps + gap_bps * 0.5  # Gap'in yarısı slippage
                fill = base_price * (1 + sign * total_bps / 10_000)
                if gap_pct > 0.02:
                    warnings.append(
                        f"Gap açılış tespit edildi: {gap_pct*100:.1f}%. "
                        f"Etkin slippage: {total_bps:.1f} bps."
                    )

        case SlippageModel.LOW_LIQUIDITY:
            extra_bps = 0.0
            if liquidity_score < low_liquidity_threshold:
                ratio = 1.0 - (liquidity_score / low_liquidity_threshold)
                extra_bps = low_liquidity_penalty_bps * ratio
                warnings.append(
                    f"Düşük likidite cezası: {extra_bps:.1f} ek bps (skor={liquidity_score:.2f})."
                )
            total_bps = slippage_bps + extra_bps
            fill = base_price * (1 + sign * total_bps / 10_000)

        case _:
            warnings.append(f"Bilinmeyen model '{m}'; fixed_bps kullanılıyor.")
            slip_pct = slippage_bps / 10_000
            fill = base_price * (1 + sign * slip_pct)

    fill = max(fill, 0.0001)
    slip_amount = abs(fill - base_price)
    slip_bps = (slip_amount / base_price) * 10_000 if base_price > 0 else 0.0

    return SlippageResult(
        model=m,
        fill_price=round(fill, 6),
        base_price=base_price,
        slippage_amount=round(slip_amount, 6),
        slippage_bps=round(slip_bps, 2),
        warnings=warnings,
    )


# ── BIST maliyet modeli ───────────────────────────────────────────────────────

@dataclass
class BISTCostResult:
    """BIST'e özgü toplam işlem maliyeti."""
    commission_tl:   float   # Komisyon (TL)
    bsmv_tl:         float   # Banka ve Sigorta Muameleleri Vergisi (%5 komisyon üstü)
    slippage_tl:     float   # Slippage (TL)
    total_cost_tl:   float   # Toplam maliyet (TL)
    effective_bps:   float   # Toplam efektif baz puan
    hit_limit:       bool    # Tavan/taban sınırına çarptı mı?
    warnings:        list[str]


def calculate_bist_cost(
    *,
    price: float,
    quantity: int,
    side: str | OrderSide,
    commission_rate: float = 0.001,         # %0.10 standart
    bsmv_rate: float = 0.05,               # %5 komisyon üstü
    slippage_bps: float = 5.0,
    slippage_model: str = "fixed_bps",
    prev_close: float | None = None,        # Tavan/taban hesabı için
    atr: float | None = None,
    avg_daily_volume_tl: float = 0.0,
    order_size_tl: float | None = None,
) -> BISTCostResult:
    """
    BIST işlem maliyetini hesapla: komisyon + BSMV + slippage.

    Tavan/taban kontrolü: önceki kapanışın ±%10'u dışındaki emirler
    uyarı alır (limit fiyat aşımı riski).
    """
    warnings: list[str] = []
    s = OrderSide(side.lower()) if isinstance(side, str) else side

    # Slippage
    slip_result = calculate_slippage(
        model=slippage_model,
        side=s,
        base_price=price,
        slippage_bps=slippage_bps,
        atr=atr,
        order_size=order_size_tl or price * quantity,
        avg_daily_volume_tl=avg_daily_volume_tl,
    )
    fill_price = slip_result.fill_price
    slippage_tl = slip_result.slippage_amount * quantity
    warnings.extend(slip_result.warnings)

    # Komisyon
    commission_tl = fill_price * quantity * commission_rate
    bsmv_tl = commission_tl * bsmv_rate

    # Tavan/taban kontrolü
    hit_limit = False
    if prev_close and prev_close > 0:
        upper_limit = prev_close * 1.10
        lower_limit = prev_close * 0.90
        if fill_price > upper_limit:
            hit_limit = True
            warnings.append(
                f"Tavan: {fill_price:.2f} > {upper_limit:.2f} (önceki kapanış {prev_close:.2f} + %10). "
                "Emir reddedilebilir."
            )
        elif fill_price < lower_limit:
            hit_limit = True
            warnings.append(
                f"Taban: {fill_price:.2f} < {lower_limit:.2f} (önceki kapanış {prev_close:.2f} - %10). "
                "Emir reddedilebilir."
            )

    trade_value = fill_price * quantity
    total_cost_tl = commission_tl + bsmv_tl + slippage_tl
    effective_bps = (total_cost_tl / trade_value * 10_000) if trade_value > 0 else 0.0

    return BISTCostResult(
        commission_tl=round(commission_tl, 4),
        bsmv_tl=round(bsmv_tl, 4),
        slippage_tl=round(slippage_tl, 4),
        total_cost_tl=round(total_cost_tl, 4),
        effective_bps=round(effective_bps, 2),
        hit_limit=hit_limit,
        warnings=warnings,
    )


def list_models() -> list[dict[str, str]]:
    """Desteklenen modelleri açıklama ile döndürür."""
    return [
        {"id": "fixed_bps",     "label": "Sabit BPS",            "description": "Sabit baz puan slippage (varsayılan)"},
        {"id": "fixed_tick",    "label": "Sabit Tick",            "description": "Sabit tick aralığı"},
        {"id": "spread",        "label": "Alış-Satış Farkı",      "description": "Bid/ask spread'ine dayalı"},
        {"id": "atr",           "label": "ATR Bazlı",             "description": "Gün içi volatiliteye dayalı (ATR * çarpan)"},
        {"id": "volume_pct",    "label": "Hacim Katılım",         "description": "Piyasa etkisi (Kyle karekök modeli)"},
        {"id": "gap_open",      "label": "Gap Açılış",            "description": "Seans boşluğundan kaynaklanan slippage"},
        {"id": "low_liquidity", "label": "Düşük Likidite Cezası", "description": "Likidite skoru düşükse ek maliyet"},
    ]
