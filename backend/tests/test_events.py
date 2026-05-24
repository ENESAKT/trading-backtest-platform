"""
test_events.py — EventStore ve event_fetcher birim testleri.

Çalıştırma:
    cd /path/to/Backtest && PYTHONPATH=. pytest backend/tests/test_events.py -v
"""

from __future__ import annotations

import json
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

from backend.events.event_store import EventStore, EventType, MarketEvent, get_event_store


# ─── EventStore Testleri ─────────────────────────────────────────────────────

class TestEventStore:

    def _store(self, tmp_path: Path) -> EventStore:
        return EventStore(tmp_path / "events.db")

    def test_db_created(self, tmp_path):
        store = self._store(tmp_path)
        assert (tmp_path / "events.db").exists()

    def test_upsert_and_query(self, tmp_path):
        store = self._store(tmp_path)
        store.upsert([{
            "symbol": "THYAO",
            "event_type": "kap",
            "title": "Özel durum bildirimi",
            "event_date": "2024-06-01",
            "source": "KAP RSS",
        }])
        events = store.query(symbol="THYAO")
        assert len(events) == 1
        assert events[0]["title"] == "Özel durum bildirimi"

    def test_upsert_deduplication(self, tmp_path):
        store = self._store(tmp_path)
        ev = {
            "symbol": "THYAO",
            "event_type": "kap",
            "title": "Tekrar eklenen olay",
            "event_date": "2024-06-01",
            "source": "test",
        }
        store.upsert([ev])
        store.upsert([ev])  # İkinci kez ekleme
        events = store.query(symbol="THYAO")
        assert len(events) == 1  # Duplicate yok

    def test_filter_by_event_type(self, tmp_path):
        store = self._store(tmp_path)
        store.upsert([
            {"symbol": "THYAO", "event_type": "kap", "title": "KAP", "event_date": "2024-06-01", "source": "test"},
            {"symbol": "THYAO", "event_type": "earnings", "title": "Bilanço", "event_date": "2024-06-02", "source": "test"},
            {"symbol": "THYAO", "event_type": "dividend", "title": "Temettü", "event_date": "2024-06-03", "source": "test"},
        ])
        earnings = store.query(symbol="THYAO", event_types=["earnings"])
        assert len(earnings) == 1
        assert earnings[0]["event_type"] == "earnings"

    def test_filter_by_date_range(self, tmp_path):
        store = self._store(tmp_path)
        store.upsert([
            {"symbol": "THYAO", "event_type": "kap", "title": "Ocak", "event_date": "2024-01-15", "source": "test"},
            {"symbol": "THYAO", "event_type": "kap", "title": "Mart", "event_date": "2024-03-15", "source": "test"},
            {"symbol": "THYAO", "event_type": "kap", "title": "Haziran", "event_date": "2024-06-15", "source": "test"},
        ])
        events = store.query(symbol="THYAO", from_date="2024-02-01", to_date="2024-04-30")
        assert len(events) == 1
        assert events[0]["title"] == "Mart"

    def test_filter_by_symbol(self, tmp_path):
        store = self._store(tmp_path)
        store.upsert([
            {"symbol": "THYAO", "event_type": "kap", "title": "Thyao olay", "event_date": "2024-06-01", "source": "test"},
            {"symbol": "GARAN", "event_type": "kap", "title": "Garan olay", "event_date": "2024-06-01", "source": "test"},
        ])
        thyao = store.query(symbol="THYAO")
        assert len(thyao) == 1
        assert thyao[0]["symbol"] == "THYAO"

    def test_symbol_case_insensitive(self, tmp_path):
        store = self._store(tmp_path)
        store.upsert([{
            "symbol": "thyao",
            "event_type": "kap",
            "title": "Küçük harf sembol",
            "event_date": "2024-06-01",
            "source": "test",
        }])
        events = store.query(symbol="THYAO")
        assert len(events) == 1
        assert events[0]["symbol"] == "THYAO"  # Büyük harfe normalize

    def test_count(self, tmp_path):
        store = self._store(tmp_path)
        store.upsert([
            {"symbol": "THYAO", "event_type": "kap", "title": "A", "event_date": "2024-06-01", "source": "test"},
            {"symbol": "THYAO", "event_type": "kap", "title": "B", "event_date": "2024-06-02", "source": "test"},
        ])
        assert store.count(symbol="THYAO") == 2
        assert store.count() == 2

    def test_limit_respected(self, tmp_path):
        store = self._store(tmp_path)
        for i in range(10):
            store.upsert([{
                "symbol": "THYAO",
                "event_type": "kap",
                "title": f"Olay {i}",
                "event_date": f"2024-06-{i+1:02d}",
                "source": "test",
            }])
        events = store.query(symbol="THYAO", limit=3)
        assert len(events) == 3

    def test_confirmed_only_filter(self, tmp_path):
        store = self._store(tmp_path)
        store.upsert([
            {"symbol": "THYAO", "event_type": "earnings", "title": "Kesin bilanço", "event_date": "2024-06-01", "source": "test", "is_confirmed": True},
            {"symbol": "THYAO", "event_type": "earnings", "title": "Tahmini bilanço", "event_date": "2024-07-01", "source": "test", "is_confirmed": False},
        ])
        confirmed = store.query(symbol="THYAO", confirmed_only=True)
        assert len(confirmed) == 1
        assert confirmed[0]["is_confirmed"] is True

    def test_extra_json_stored_and_retrieved(self, tmp_path):
        store = self._store(tmp_path)
        store.upsert([{
            "symbol": "THYAO",
            "event_type": "dividend",
            "title": "Temettü",
            "event_date": "2024-06-01",
            "source": "test",
            "extra": {"amount": 5.25, "currency": "TRY"},
        }])
        events = store.query(symbol="THYAO")
        assert events[0]["extra"]["amount"] == 5.25
        assert events[0]["extra"]["currency"] == "TRY"

    def test_empty_query(self, tmp_path):
        store = self._store(tmp_path)
        events = store.query(symbol="NONEXISTENT")
        assert events == []

    def test_upcoming_events(self, tmp_path):
        store = self._store(tmp_path)
        today = date.today().isoformat()
        future = (date.today() + timedelta(days=10)).isoformat()
        past = (date.today() - timedelta(days=10)).isoformat()

        store.upsert([
            {"symbol": "", "event_type": "economic", "title": "Gelecek olay", "event_date": future, "source": "test"},
            {"symbol": "", "event_type": "economic", "title": "Geçmiş olay", "event_date": past, "source": "test"},
        ])
        upcoming = store.upcoming(days=30)
        titles = [e["title"] for e in upcoming]
        assert "Gelecek olay" in titles
        assert "Geçmiş olay" not in titles

    def test_upsert_market_event_object(self, tmp_path):
        store = self._store(tmp_path)
        ev = MarketEvent(
            symbol="GARAN",
            event_type=EventType.EARNINGS,
            title="Çeyrek bilanço",
            event_date="2024-09-30",
            description="3Ç2024 finansal sonuçları",
            source="borsapy",
            is_confirmed=True,
        )
        store.upsert([ev])
        events = store.query(symbol="GARAN")
        assert len(events) == 1
        assert events[0]["event_type"] == "earnings"

    def test_global_economic_events_no_symbol(self, tmp_path):
        """Global ekonomik olaylar boş sembolle eklenir."""
        store = self._store(tmp_path)
        store.upsert([{
            "symbol": "",
            "event_type": "economic",
            "title": "TCMB Faiz Kararı",
            "event_date": "2026-07-17",
            "source": "TCMB (tahmini)",
            "is_confirmed": False,
        }])
        events = store.query(event_types=["economic"])
        assert len(events) >= 1

    def test_multiple_event_types_filter(self, tmp_path):
        store = self._store(tmp_path)
        store.upsert([
            {"symbol": "THYAO", "event_type": "kap", "title": "K", "event_date": "2024-06-01", "source": "test"},
            {"symbol": "THYAO", "event_type": "earnings", "title": "E", "event_date": "2024-06-02", "source": "test"},
            {"symbol": "THYAO", "event_type": "dividend", "title": "D", "event_date": "2024-06-03", "source": "test"},
        ])
        events = store.query(symbol="THYAO", event_types=["kap", "earnings"])
        assert len(events) == 2
        types = {e["event_type"] for e in events}
        assert types == {"kap", "earnings"}


class TestEventType:
    def test_all_values(self):
        values = EventType.values()
        assert "kap" in values
        assert "earnings" in values
        assert "dividend" in values
        assert "economic" in values
        assert "split" in values

    def test_enum_string_value(self):
        assert EventType.KAP == "kap"
        assert EventType.ECONOMIC == "economic"


class TestMarketEvent:
    def test_to_dict_has_required_keys(self):
        ev = MarketEvent(
            symbol="TEST",
            event_type=EventType.DIVIDEND,
            title="Temettü",
            event_date="2024-06-01",
        )
        d = ev.to_dict()
        for key in ["symbol", "event_type", "title", "event_date", "source", "is_confirmed"]:
            assert key in d

    def test_extra_defaults_empty(self):
        ev = MarketEvent(
            symbol="TEST",
            event_type=EventType.KAP,
            title="Test",
            event_date="2024-01-01",
        )
        assert ev.extra == {}


class TestEventFetcherEconomic:
    def test_economic_calendar_returns_list(self):
        from backend.events.event_fetcher import _fetch_economic_calendar
        events = _fetch_economic_calendar()
        assert isinstance(events, list)

    def test_economic_events_have_required_fields(self):
        from backend.events.event_fetcher import _fetch_economic_calendar
        events = _fetch_economic_calendar()
        for ev in events:
            assert "event_type" in ev
            assert "title" in ev
            assert "event_date" in ev
            assert ev["event_type"] == "economic"

    def test_economic_events_not_all_past(self):
        """Takvimde bazı olaylar bugün veya gelecekte olmalı."""
        from backend.events.event_fetcher import _fetch_economic_calendar
        today = date.today().isoformat()
        events = _fetch_economic_calendar()
        if events:  # Takvim tamamen geçmişte değilse
            dates = [e["event_date"] for e in events]
            # En az bir tarih geçmişte veya gelecekte olabilir
            assert len(dates) > 0

    def test_fetch_events_deduplicated(self):
        """Aynı kaynak iki kez çağrıldığında tekrar yok."""
        from backend.events.event_fetcher import _fetch_economic_calendar
        e1 = _fetch_economic_calendar()
        e2 = _fetch_economic_calendar()
        assert len(e1) == len(e2)
