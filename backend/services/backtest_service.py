"""BacktestService — backtest çalıştırma servis katmanı.

backend.backtest.runner üzerinden quant_engine'i çalıştırır.
Bu sınıf dependency injection ile test edilebilir hale getirir.
"""

from __future__ import annotations

import logging

from backend.api.schemas import BacktestRequest, BacktestResponse

_logger = logging.getLogger(__name__)


class BacktestService:
    """Orchestrates backtest execution via quant_engine."""

    async def run(self, req: BacktestRequest) -> BacktestResponse:
        """Backtest çalıştır ve sonuçları BacktestResponse olarak döndür.

        Args:
            req: Strateji, sembol, zaman aralığı ve parametreler.

        Returns:
            Sharpe, Sortino, max DD, win rate gibi özet metrikler.

        Raises:
            ValueError: Geçersiz strateji veya sembol.
            RuntimeError: Veri çekme veya hesaplama hatası.
        """
        from backend.backtest.runner import run_backtest_request

        _logger.info(
            "[BacktestService] Başlatıldı: symbol=%s timeframe=%s start=%s end=%s",
            req.symbol, req.timeframe, req.start, req.end,
        )
        try:
            result = await run_backtest_request(req)
            return BacktestResponse(
                strategy=req.strategy,
                symbol=req.symbol,
                sharpe=result.get("sharpe"),
                sortino=result.get("sortino"),
                max_dd=result.get("max_dd"),
                total_trades=result.get("total_trades"),
                win_rate=result.get("win_rate"),
                period_start=req.start,
                period_end=req.end,
            )
        except Exception as exc:
            _logger.error("[BacktestService] run() hata: %s", exc)
            raise
