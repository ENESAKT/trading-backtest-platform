"""KAP-compatible financial analysis provider.

This provider intentionally depends on an environment URL template instead of
hard-coding a private or unstable endpoint. The expected response is normalized
by ``normalize_provider_response`` in the service layer.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

from backend.mali_analiz.service import FinancialProviderResult


class KapFinancialAnalysisProvider:
    source = "kap"

    def __init__(self, url_template: str | None = None, timeout: float = 10.0) -> None:
        self.url_template = url_template or os.environ.get("KAP_FINANCIAL_URL_TEMPLATE", "")
        self.timeout = timeout

    def fetch(self, symbol: str) -> FinancialProviderResult:
        if not self.url_template:
            return FinancialProviderResult(
                payload={
                    "symbol": symbol,
                    "source": self.source,
                    "source_status": {
                        "source": self.source,
                        "status": "not_configured",
                    },
                    "warnings": ["KAP_FINANCIAL_URL_TEMPLATE tanımlı değil."],
                },
                source=self.source,
                status="not_configured",
                fetched_at=datetime.now(timezone.utc),
            )

        url = self.url_template.format(symbol=quote(symbol), ticker=quote(f"{symbol}.IS"))
        headers = {"Accept": "application/json", "User-Agent": "PiyasaPilot/2.0"}
        token = os.environ.get("KAP_FINANCIAL_AUTH_HEADER", "")
        if token:
            key, _, value = token.partition(":")
            if key and value:
                headers[key.strip()] = value.strip()

        with urlopen(Request(url, headers=headers), timeout=self.timeout) as response:
            raw = response.read().decode("utf-8")
        payload: dict[str, Any] = json.loads(raw)
        payload.setdefault("symbol", symbol)
        payload.setdefault("source", self.source)
        return FinancialProviderResult(
            payload=payload,
            source=self.source,
            status="ok",
            fetched_at=datetime.now(timezone.utc),
        )
