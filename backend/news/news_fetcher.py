"""Haber çekici — borsapy (KAP bildirimleri) birincil kaynak.

borsapy.Ticker.news, KAP bildirim başlıklarını ve URL'lerini döndürür.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any

_logger = logging.getLogger(__name__)


def fetch_news_for_symbol(symbol: str, limit: int = 20) -> list[dict[str, Any]]:
    """Sembol için haber listesi çek. Boş liste dönerse veri yok."""
    items = _fetch_kap_rss(symbol, limit)
    if not items:
        items = _fetch_borsapy(symbol, limit)
    if not items:
        items = _fetch_yfinance(symbol, limit)
    # Drop empty-headline items before storing
    return [i for i in items if (i.get("headline") or "").strip()]


def _fetch_kap_rss(symbol: str, limit: int) -> list[dict[str, Any]]:
    try:
        from backend.news.kap_rss import fetch_kap_rss
        return fetch_kap_rss(symbol, limit)
    except Exception as exc:  # noqa: BLE001
        _logger.debug("[news_fetcher] KAP RSS hatası (%s): %s", symbol, exc)
        return []


def _fetch_borsapy(symbol: str, limit: int) -> list[dict[str, Any]]:
    """borsapy üzerinden KAP bildirimlerini çek."""
    try:
        import borsapy  # type: ignore[import-untyped]

        sym = symbol.upper().replace(".IS", "")
        ticker = borsapy.Ticker(sym)
        df = ticker.news  # DataFrame: Date, Title, URL
        if df is None or df.empty:
            return []

        results: list[dict[str, Any]] = []
        for _, row in df.head(limit).iterrows():
            title = str(row.get("Title") or "").strip()
            if not title:
                continue
            date_raw = str(row.get("Date") or "")
            pub_iso: str | None = None
            if date_raw:
                try:
                    pub_iso = dt.datetime.strptime(date_raw, "%d.%m.%Y %H:%M:%S").isoformat()
                except Exception:
                    pass
            results.append({
                "symbol":       sym,
                "headline":     title[:500],
                "body":         "",
                "source":       "KAP (kap.org.tr)",
                "published_at": pub_iso,
                "url":          str(row.get("URL") or "") or None,
            })
        return results
    except Exception as exc:  # noqa: BLE001
        _logger.debug("[news_fetcher] borsapy hatası (%s): %s", symbol, exc)
        return []


def _fetch_yfinance(symbol: str, limit: int) -> list[dict[str, Any]]:
    try:
        import yfinance as yf  # type: ignore[import-untyped]
        ticker_sym = f"{symbol}.IS" if not symbol.endswith(".IS") and len(symbol) <= 7 else symbol
        ticker = yf.Ticker(ticker_sym)
        raw = ticker.news or []
        results: list[dict[str, Any]] = []
        for item in raw[:limit]:
            title = (item.get("title") or "").strip()
            if not title:
                continue
            pub = item.get("providerPublishTime") or item.get("publishedAt")
            pub_iso: str | None = None
            if pub:
                try:
                    pub_iso = dt.datetime.fromtimestamp(int(pub), tz=dt.UTC).isoformat()
                except Exception:
                    pass
            results.append({
                "symbol":       symbol.upper(),
                "headline":     title[:500],
                "body":         (item.get("summary") or "")[:2000],
                "source":       item.get("publisher", "yfinance"),
                "published_at": pub_iso,
                "url":          item.get("link") or item.get("url"),
            })
        return results
    except Exception as exc:  # noqa: BLE001
        _logger.warning("[news_fetcher] yfinance hatası (%s): %s", symbol, exc)
        return []
