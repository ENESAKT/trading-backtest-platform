"""KAP RSS fetcher.

Primary RSS: https://www.kap.org.tr/tr/rss/
Returns only real items from the feed; no placeholders are generated.
"""

from __future__ import annotations

import datetime as dt
import logging
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

_logger = logging.getLogger(__name__)
KAP_RSS_URL = "https://www.kap.org.tr/tr/rss/"


def fetch_kap_rss(symbol: str | None = None, limit: int = 40) -> list[dict[str, Any]]:
    sym = (symbol or "").upper().replace(".IS", "")
    try:
        resp = httpx.get(KAP_RSS_URL, timeout=8.0, follow_redirects=True)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as exc:  # noqa: BLE001
        _logger.debug("[kap-rss] RSS okunamadı: %s", exc)
        return []

    items: list[dict[str, Any]] = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        pub_raw = (item.findtext("pubDate") or "").strip()
        if not title:
            continue
        haystack = f"{title} {desc}".upper()
        if sym and sym not in haystack:
            continue
        published_at = None
        if pub_raw:
            try:
                published_at = parsedate_to_datetime(pub_raw).astimezone(dt.UTC).isoformat()
            except Exception:
                published_at = None
        items.append({
            "symbol": sym or _infer_symbol(title),
            "headline": title[:500],
            "body": desc[:2000],
            "source": "KAP RSS",
            "published_at": published_at,
            "url": link or None,
        })
        if len(items) >= limit:
            break
    return items


def _infer_symbol(title: str) -> str:
    token = title.split()[0].strip(":-()[]").upper()
    return token if token.isalnum() and 2 <= len(token) <= 8 else "KAP"
