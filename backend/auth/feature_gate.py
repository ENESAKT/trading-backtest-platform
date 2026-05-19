"""
Feature Gate — PiyasaPilot yetki sistemi.
==========================================
Tüm özellik kısıtları bu dosyadan okunur.
Yeni bir özellik eklendiğinde SADECE bu dosya güncellenir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Role = Literal["free", "pro", "ultra", "admin"]


@dataclass(frozen=True)
class PlanLimits:
    api_calls_per_day: int          # -1 = sınırsız
    backtest_runs_per_day: int      # -1 = sınırsız
    max_watchlist_symbols: int      # -1 = sınırsız
    max_paper_accounts: int         # -1 = sınırsız
    max_chart_templates: int        # -1 = sınırsız
    max_saved_strategies: int       # -1 = sınırsız (free: 3)
    signals_per_day: int            # -1 = sınırsız
    real_time_data: bool
    backtest_pro: bool              # WFA, Monte Carlo, Heatmap, Portfolio Lab
    scanner: bool
    paper_trading: bool             # Paper trading erişimi
    mali_analiz_scope: str          # 'none' | 'bist30' | 'bist100' | 'all'
    education_full: bool
    telegram_bot: bool
    api_access: bool
    multi_chart: bool               # 4'lü layout
    terminal_access: bool


PLAN_LIMITS: dict[str, PlanLimits] = {
    "free": PlanLimits(
        api_calls_per_day=500,
        backtest_runs_per_day=5,
        max_watchlist_symbols=10,
        max_paper_accounts=0,
        max_chart_templates=1,
        max_saved_strategies=3,
        signals_per_day=3,
        real_time_data=False,
        backtest_pro=False,
        scanner=False,
        paper_trading=False,
        mali_analiz_scope="bist30",
        education_full=False,
        telegram_bot=False,
        api_access=False,
        multi_chart=False,
        terminal_access=True,
    ),
    "pro": PlanLimits(
        api_calls_per_day=5000,
        backtest_runs_per_day=-1,
        max_watchlist_symbols=50,
        max_paper_accounts=5,
        max_chart_templates=10,
        max_saved_strategies=-1,
        signals_per_day=-1,
        real_time_data=False,
        backtest_pro=True,
        scanner=True,
        paper_trading=True,
        mali_analiz_scope="bist100",
        education_full=True,
        telegram_bot=True,
        api_access=False,
        multi_chart=True,
        terminal_access=True,
    ),
    "ultra": PlanLimits(
        api_calls_per_day=-1,
        backtest_runs_per_day=-1,
        max_watchlist_symbols=-1,
        max_paper_accounts=-1,
        max_chart_templates=-1,
        max_saved_strategies=-1,
        signals_per_day=-1,
        real_time_data=True,
        backtest_pro=True,
        scanner=True,
        paper_trading=True,
        mali_analiz_scope="all",
        education_full=True,
        telegram_bot=True,
        api_access=True,
        multi_chart=True,
        terminal_access=True,
    ),
    "admin": PlanLimits(
        api_calls_per_day=-1,
        backtest_runs_per_day=-1,
        max_watchlist_symbols=-1,
        max_paper_accounts=-1,
        max_chart_templates=-1,
        max_saved_strategies=-1,
        signals_per_day=-1,
        real_time_data=True,
        backtest_pro=True,
        scanner=True,
        paper_trading=True,
        mali_analiz_scope="all",
        education_full=True,
        telegram_bot=True,
        api_access=True,
        multi_chart=True,
        terminal_access=True,
    ),
}


def get_limits(role: str) -> PlanLimits:
    """Rol için PlanLimits döndür. Bilinmeyen rol → free limitleri."""
    return PLAN_LIMITS.get(role, PLAN_LIMITS["free"])


def can_access(role: str, feature: str) -> bool:
    """
    Özellik erişim sorgusu.

    feature: PlanLimits field adı
    - bool field  → True/False
    - int field   → -1 veya >0 = erişim var, 0 = erişim yok
    - str field   → 'none' dışı = erişim var
    """
    limits = get_limits(role)
    value = getattr(limits, feature, False)
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0       # 0 = kapalı, -1 = sınırsız, >0 = kotası var
    if isinstance(value, str):
        return value != "none"
    return bool(value)


def get_quota(role: str, field: str) -> int:
    """Belirli bir kota alanının değerini döndür. -1 = sınırsız."""
    limits = get_limits(role)
    return getattr(limits, field, 0)
