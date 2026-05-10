"""Haber çekici — borsapy/tradingview MCP veya yfinance fallback.

MCP araçları ağ bağlantısı gerektirdiğinden API sunucusundan doğrudan çağrılamaz.
Bu modül HTTP yoluyla borsa-mcp /get_news endpoint'ini dener;
başarısız olursa yfinance üzerinden ticker news'ını çeker.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any

_logger = logging.getLogger(__name__)


def fetch_news_for_symbol(symbol: str, limit: int = 20) -> list[dict[str, Any]]:
    """Sembol için haber listesi çek. Boş liste dönerse veri yok."""
    items = _fetch_yfinance(symbol, limit)
    return items


def _fetch_yfinance(symbol: str, limit: int) -> list[dict[str, Any]]:
    try:
        import yfinance as yf  # type: ignore[import-untyped]
        ticker_sym = f"{symbol}.IS" if not symbol.endswith(".IS") and len(symbol) <= 7 else symbol
        ticker = yf.Ticker(ticker_sym)
        raw = ticker.news or []
        results: list[dict[str, Any]] = []
        for item in raw[:limit]:
            pub = item.get("providerPublishTime") or item.get("publishedAt")
            pub_iso: str | None = None
            if pub:
                try:
                    pub_iso = dt.datetime.fromtimestamp(int(pub), tz=dt.UTC).isoformat()
                except Exception:
                    pass
            results.append({
                "symbol":       symbol.upper(),
                "headline":     item.get("title", "")[:500],
                "body":         (item.get("summary") or "")[:2000],
                "source":       item.get("publisher", "yfinance"),
                "published_at": pub_iso,
                "url":          item.get("link") or item.get("url"),
            })
        return results
    except Exception as exc:  # noqa: BLE001
        _logger.warning("[news_fetcher] yfinance hatası (%s): %s", symbol, exc)
        return []
