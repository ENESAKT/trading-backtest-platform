"""
event_fetcher.py — Çoklu kaynak olay çekici.

Olay kaynakları (öncelik sırasıyla):
  1. KAP RSS  — KAP bildirimleri (kap.org.tr RSS)
  2. borsapy  — Bilanço, temettü ve kurumsal olaylar
  3. yfinance — Temel kurumsal takvim (earnings date, dividend)
  4. Statik ekonomik takvim — TCMB, TÜİK, Fed, ECB sabit tarihleri

Her kaynak başarısız olursa sessizce bir sonrakine geçilir.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any

_logger = logging.getLogger(__name__)


# ─── Ana giriş noktası ────────────────────────────────────────────────────────

def fetch_events_for_symbol(
    symbol: str,
    limit: int = 30,
    include_economic: bool = True,
) -> list[dict[str, Any]]:
    """
    Sembol için tüm kaynaklardan olay listesi çek.

    Döndürülen dict yapısı EventStore.upsert() ile uyumludur.
    """
    sym = symbol.upper().replace(".IS", "")
    events: list[dict[str, Any]] = []

    # KAP bildirimleri
    events.extend(_fetch_kap_events(sym, limit))

    # Bilanço / temettü (borsapy veya yfinance)
    events.extend(_fetch_corporate_events(sym, limit))

    # Ekonomik takvim (TCMB, TÜİK, Fed, ECB vb.)
    if include_economic:
        events.extend(_fetch_economic_calendar())

    # Tekrarları temizle (aynı başlık+tarih)
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, Any]] = []
    for ev in events:
        key = (str(ev.get("title", ""))[:80], str(ev.get("event_date", "")))
        if key not in seen:
            seen.add(key)
            unique.append(ev)

    return unique[:limit]


# ─── KAP bildirimleri ────────────────────────────────────────────────────────

def _fetch_kap_events(symbol: str, limit: int) -> list[dict[str, Any]]:
    try:
        from backend.news.kap_rss import fetch_kap_rss
        raw = fetch_kap_rss(symbol, limit=limit)
        events = []
        for item in raw:
            pub = item.get("published_at") or dt.datetime.now(tz=dt.timezone.utc).isoformat()
            events.append({
                "symbol":       item.get("symbol") or symbol,
                "event_type":   "kap",
                "title":        (item.get("headline") or "")[:500],
                "description":  (item.get("body") or "")[:2000],
                "event_date":   pub[:10],
                "event_time":   pub[11:16] if len(pub) > 10 else None,
                "source":       "KAP RSS",
                "source_url":   item.get("url"),
                "is_confirmed": True,
            })
        return events
    except Exception:
        _logger.debug("[event_fetcher] KAP RSS fetch failed")
        return []


# ─── Kurumsal olaylar (borsapy / yfinance) ───────────────────────────────────

def _fetch_corporate_events(symbol: str, limit: int) -> list[dict[str, Any]]:
    """Bilanço, temettü ve sermaye olaylarını çek."""
    events: list[dict[str, Any]] = []
    events.extend(_fetch_borsapy_events(symbol, limit))
    if not events:
        events.extend(_fetch_yfinance_events(symbol, limit))
    return events


def _fetch_borsapy_events(symbol: str, limit: int) -> list[dict[str, Any]]:
    try:
        import borsapy  # type: ignore[import-untyped]  # noqa: F401
        ticker = borsapy.Ticker(symbol)
        events: list[dict[str, Any]] = []

        # Finansallar: bilanço açıklama tarihleri
        try:
            df = ticker.financials  # DataFrame
            if df is not None and not df.empty:
                for _, row in df.head(limit).iterrows():
                    date_str = str(row.get("Date") or "").strip()[:10]
                    if not date_str:
                        continue
                    period_str = str(row.get("Period") or "")
                    events.append({
                        "symbol":       symbol,
                        "event_type":   "earnings",
                        "title":        f"Finansal sonuçlar ({period_str})" if period_str else "Finansal sonuçlar",
                        "description":  "",
                        "event_date":   date_str,
                        "source":       "borsapy",
                        "is_confirmed": True,
                    })
        except Exception:
            pass

        # Temettü bilgileri
        try:
            div_df = ticker.dividends  # DataFrame
            if div_df is not None and not div_df.empty:
                for _, row in div_df.head(limit).iterrows():
                    date_str = str(row.get("Date") or "").strip()[:10]
                    amount = row.get("Amount") or row.get("amount")
                    if not date_str:
                        continue
                    title = f"Temettü: {amount} TL/hisse" if amount else "Temettü"
                    events.append({
                        "symbol":       symbol,
                        "event_type":   "dividend",
                        "title":        title,
                        "description":  "",
                        "event_date":   date_str,
                        "source":       "borsapy",
                        "is_confirmed": True,
                        "extra":        {"amount": float(amount) if amount else None},
                    })
        except Exception:
            pass

        return events
    except Exception:
        _logger.debug("[event_fetcher] borsapy corporate-event fetch failed")
        return []


def _fetch_yfinance_events(symbol: str, limit: int) -> list[dict[str, Any]]:
    try:
        import yfinance as yf  # type: ignore[import-untyped]
        ticker_sym = f"{symbol}.IS" if not symbol.endswith(".IS") and len(symbol) <= 7 else symbol
        ticker = yf.Ticker(ticker_sym)
        events: list[dict[str, Any]] = []

        # Earnings dates
        try:
            cal = ticker.get_calendar()
            if cal and "Earnings Date" in cal:
                ed = cal["Earnings Date"]
                date_str = str(ed[0])[:10] if isinstance(ed, (list, tuple)) else str(ed)[:10]
                if date_str and len(date_str) == 10:
                    events.append({
                        "symbol":       symbol,
                        "event_type":   "earnings",
                        "title":        "Bilanço açıklama (tahmini)",
                        "description":  "",
                        "event_date":   date_str,
                        "source":       "yfinance",
                        "is_confirmed": False,
                    })
        except Exception:
            pass

        # Dividends
        try:
            divs = ticker.dividends
            if divs is not None and not divs.empty:
                for date_idx, amount in list(divs.items())[:limit]:
                    date_str = str(date_idx)[:10]
                    events.append({
                        "symbol":       symbol,
                        "event_type":   "dividend",
                        "title":        f"Temettü: {amount:.4f}",
                        "description":  "",
                        "event_date":   date_str,
                        "source":       "yfinance",
                        "is_confirmed": True,
                        "extra":        {"amount": float(amount)},
                    })
        except Exception:
            pass

        # Splits
        try:
            splits = ticker.splits
            if splits is not None and not splits.empty:
                for date_idx, ratio in list(splits.items())[:limit]:
                    date_str = str(date_idx)[:10]
                    events.append({
                        "symbol":       symbol,
                        "event_type":   "split",
                        "title":        f"Hisse bölünmesi: {ratio:.0f}:1",
                        "description":  "",
                        "event_date":   date_str,
                        "source":       "yfinance",
                        "is_confirmed": True,
                        "extra":        {"ratio": float(ratio)},
                    })
        except Exception:
            pass

        return events
    except Exception:
        _logger.debug("[event_fetcher] yfinance corporate-event fetch failed")
        return []


# ─── Ekonomik takvim ─────────────────────────────────────────────────────────

# Statik ekonomik takvim — düzenli açıklama döngüleri.
# Gerçek veri kaynağı eklenene kadar sabit tarih listesi kullanılır.
# NOT: Bu liste ürün kodu değil; gerçek API entegrasyonu Task 18.9'da netleştirilecek.

_ECONOMIC_EVENTS_2026 = [
    # TCMB Para Politikası Kararları (yaklaşık — resmi takvime göre güncellenmeli)
    {"event_type": "economic", "title": "TCMB Faiz Kararı", "event_date": "2026-01-23",
     "source": "TCMB (tahmini)", "is_confirmed": False, "extra": {"category": "monetary_policy"}},
    {"event_type": "economic", "title": "TCMB Faiz Kararı", "event_date": "2026-03-20",
     "source": "TCMB (tahmini)", "is_confirmed": False, "extra": {"category": "monetary_policy"}},
    {"event_type": "economic", "title": "TCMB Faiz Kararı", "event_date": "2026-05-22",
     "source": "TCMB (tahmini)", "is_confirmed": False, "extra": {"category": "monetary_policy"}},
    {"event_type": "economic", "title": "TCMB Faiz Kararı", "event_date": "2026-07-17",
     "source": "TCMB (tahmini)", "is_confirmed": False, "extra": {"category": "monetary_policy"}},
    {"event_type": "economic", "title": "TCMB Faiz Kararı", "event_date": "2026-09-18",
     "source": "TCMB (tahmini)", "is_confirmed": False, "extra": {"category": "monetary_policy"}},
    {"event_type": "economic", "title": "TCMB Faiz Kararı", "event_date": "2026-11-20",
     "source": "TCMB (tahmini)", "is_confirmed": False, "extra": {"category": "monetary_policy"}},

    # TÜİK TÜFE (yaklaşık — her ay 3-5. işgünü)
    {"event_type": "economic", "title": "TÜİK TÜFE Enflasyon", "event_date": "2026-02-03",
     "source": "TÜİK (tahmini)", "is_confirmed": False, "extra": {"category": "inflation"}},
    {"event_type": "economic", "title": "TÜİK TÜFE Enflasyon", "event_date": "2026-03-03",
     "source": "TÜİK (tahmini)", "is_confirmed": False, "extra": {"category": "inflation"}},
    {"event_type": "economic", "title": "TÜİK TÜFE Enflasyon", "event_date": "2026-04-03",
     "source": "TÜİK (tahmini)", "is_confirmed": False, "extra": {"category": "inflation"}},
    {"event_type": "economic", "title": "TÜİK TÜFE Enflasyon", "event_date": "2026-05-05",
     "source": "TÜİK (tahmini)", "is_confirmed": False, "extra": {"category": "inflation"}},
    {"event_type": "economic", "title": "TÜİK TÜFE Enflasyon", "event_date": "2026-06-03",
     "source": "TÜİK (tahmini)", "is_confirmed": False, "extra": {"category": "inflation"}},
    {"event_type": "economic", "title": "TÜİK TÜFE Enflasyon", "event_date": "2026-07-03",
     "source": "TÜİK (tahmini)", "is_confirmed": False, "extra": {"category": "inflation"}},

    # Fed Toplantıları (FOMC)
    {"event_type": "economic", "title": "Fed (FOMC) Faiz Kararı", "event_date": "2026-01-28",
     "source": "Fed (tahmini)", "is_confirmed": False, "extra": {"category": "monetary_policy", "region": "US"}},
    {"event_type": "economic", "title": "Fed (FOMC) Faiz Kararı", "event_date": "2026-03-18",
     "source": "Fed (tahmini)", "is_confirmed": False, "extra": {"category": "monetary_policy", "region": "US"}},
    {"event_type": "economic", "title": "Fed (FOMC) Faiz Kararı", "event_date": "2026-05-06",
     "source": "Fed (tahmini)", "is_confirmed": False, "extra": {"category": "monetary_policy", "region": "US"}},
    {"event_type": "economic", "title": "Fed (FOMC) Faiz Kararı", "event_date": "2026-06-17",
     "source": "Fed (tahmini)", "is_confirmed": False, "extra": {"category": "monetary_policy", "region": "US"}},
    {"event_type": "economic", "title": "Fed (FOMC) Faiz Kararı", "event_date": "2026-07-29",
     "source": "Fed (tahmini)", "is_confirmed": False, "extra": {"category": "monetary_policy", "region": "US"}},
    {"event_type": "economic", "title": "Fed (FOMC) Faiz Kararı", "event_date": "2026-09-16",
     "source": "Fed (tahmini)", "is_confirmed": False, "extra": {"category": "monetary_policy", "region": "US"}},
    {"event_type": "economic", "title": "Fed (FOMC) Faiz Kararı", "event_date": "2026-11-04",
     "source": "Fed (tahmini)", "is_confirmed": False, "extra": {"category": "monetary_policy", "region": "US"}},
    {"event_type": "economic", "title": "Fed (FOMC) Faiz Kararı", "event_date": "2026-12-16",
     "source": "Fed (tahmini)", "is_confirmed": False, "extra": {"category": "monetary_policy", "region": "US"}},
]


def _fetch_economic_calendar() -> list[dict[str, Any]]:
    """Statik ekonomik takvim olayları. Gelecekte gerçek API ile değiştirilecek."""
    today = dt.date.today().isoformat()
    return [
        {
            "symbol":       "",
            "event_type":   ev["event_type"],
            "title":        ev["title"],
            "description":  ev.get("description", ""),
            "event_date":   ev["event_date"],
            "source":       ev["source"],
            "source_url":   ev.get("source_url"),
            "is_confirmed": ev.get("is_confirmed", False),
            "extra":        ev.get("extra", {}),
        }
        for ev in _ECONOMIC_EVENTS_2026
        # Yalnızca henüz geçmemiş veya bugün olan olayları döndür
        if ev["event_date"] >= today[:7]  # Ay bazında kontrol (geçmiş ayları göster de)
    ]
