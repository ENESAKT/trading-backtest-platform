"""Lisanslı HTTP OHLCV feed'leri için küçük adapter yardımcıları."""

from __future__ import annotations

import datetime as dt
import ipaddress
import json
import re
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from backend.config import getenv


_SYMBOL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:=-]{0,63}$")
_TIMEFRAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,15}$")


def _validated_url(
    url_template: str,
    symbol: str,
    timeframe: str,
    limit: int,
) -> str:
    """Render an OHLCV URL without allowing request data to change its origin."""
    if not _SYMBOL_PATTERN.fullmatch(symbol) or not _TIMEFRAME_PATTERN.fullmatch(timeframe):
        raise ValueError("Invalid OHLCV symbol or timeframe.")
    template_parts = urlsplit(url_template)
    if template_parts.scheme != "https" or not template_parts.hostname:
        raise ValueError("OHLCV endpoint must use HTTPS.")
    if template_parts.username or template_parts.password or template_parts.fragment:
        raise ValueError("OHLCV endpoint contains unsupported URL components.")
    if "{" in template_parts.netloc or "}" in template_parts.netloc:
        raise ValueError("OHLCV placeholders are not allowed in the URL origin.")

    host = template_parts.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost"):
        raise ValueError("Local OHLCV endpoints are not allowed.")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("Private OHLCV endpoint addresses are not allowed.")

    rendered = url_template.format(
        symbol=quote(symbol, safe=""),
        timeframe=quote(timeframe, safe=""),
        interval=quote(timeframe, safe=""),
        limit=max(1, int(limit)),
    )
    rendered_parts = urlsplit(rendered)
    if (
        rendered_parts.scheme != template_parts.scheme
        or rendered_parts.hostname != template_parts.hostname
        or rendered_parts.port != template_parts.port
        or rendered_parts.username
        or rendered_parts.password
        or rendered_parts.fragment
    ):
        raise ValueError("OHLCV request origin changed during URL rendering.")
    return urlunsplit(rendered_parts)


def configured_template(env_name: str) -> str:
    return getenv(env_name).strip()


def configured_header(env_name: str) -> tuple[str, str] | None:
    raw = getenv(env_name).strip()
    if not raw or ":" not in raw:
        return None
    key, value = raw.split(":", 1)
    key = key.strip()
    value = value.strip()
    if not key or not value:
        return None
    return key, value


def _timestamp_seconds(value: Any) -> int:
    if isinstance(value, (int, float)):
        # Millisecond epoch'leri saniyeye indir.
        return int(value // 1000 if value > 10_000_000_000 else value)
    if isinstance(value, str):
        text = value.strip()
        if text.isdigit():
            return _timestamp_seconds(int(text))
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return int(parsed.timestamp())
    raise ValueError(f"Geçersiz timestamp: {value!r}")


def normalize_ohlcv_payload(payload: Any, limit: int) -> list[dict[str, Any]]:
    rows = payload
    if isinstance(payload, dict):
        rows = payload.get("bars") or payload.get("data") or payload.get("ohlcv") or []
    if not isinstance(rows, list):
        return []

    bars: list[dict[str, Any]] = []
    for row in rows[-max(1, int(limit)):]:
        if isinstance(row, dict):
            ts = row.get("time", row.get("timestamp", row.get("date")))
            close = row.get("close", row.get("c"))
            open_price = row.get("open", row.get("o", close))
            high = row.get("high", row.get("h", close))
            low = row.get("low", row.get("l", close))
            volume = row.get("volume", row.get("v", 0))
        elif isinstance(row, list) and len(row) >= 6:
            ts, open_price, high, low, close, volume = row[:6]
        else:
            continue
        try:
            bars.append(
                {
                    "time": _timestamp_seconds(ts),
                    "open": float(open_price),
                    "high": float(high),
                    "low": float(low),
                    "close": float(close),
                    "volume": float(volume or 0),
                }
            )
        except (TypeError, ValueError):
            continue
    return bars


def fetch_http_ohlcv(
    url_template: str,
    symbol: str,
    timeframe: str,
    limit: int,
    timeout: int,
    auth_header: tuple[str, str] | None = None,
) -> list[dict[str, Any]]:
    url = _validated_url(url_template, symbol, timeframe, limit)
    headers = {"User-Agent": "PiyasaPilot/1.0"}
    if auth_header is not None:
        headers[auth_header[0]] = auth_header[1]
    req = Request(url, headers=headers)
    with urlopen(req, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return normalize_ohlcv_payload(payload, limit)
