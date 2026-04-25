"""
Quant Engine — BIST Calendar Unit Testleri

Test edilen:
- İşlem günleri (hafta içi, tatil değil)
- Hafta sonu kontrolü
- Resmi tatil kontrolü
- Dini tatil kontrolü
- next_trading_day / previous_trading_day
- trading_days_between
- Seans saatleri
- Yarım gün kontrolü
"""

import datetime as dt

import pytest

from quant_engine.data.calendar import BISTCalendar


@pytest.fixture
def calendar():
    return BISTCalendar()


class TestTradingDays:
    """İşlem günü kontrolleri."""

    def test_weekday_is_trading_day(self, calendar):
        """Normal hafta içi işlem günü."""
        # 2024-01-02 Salı
        assert calendar.is_trading_day(
            dt.date(2024, 1, 2)
        ) is True

    def test_saturday_not_trading(self, calendar):
        """Cumartesi işlem günü değil."""
        # 2024-01-06 Cumartesi
        assert calendar.is_trading_day(
            dt.date(2024, 1, 6)
        ) is False

    def test_sunday_not_trading(self, calendar):
        """Pazar işlem günü değil."""
        # 2024-01-07 Pazar
        assert calendar.is_trading_day(
            dt.date(2024, 1, 7)
        ) is False

    def test_new_year_not_trading(self, calendar):
        """1 Ocak Yılbaşı tatili."""
        assert calendar.is_trading_day(
            dt.date(2024, 1, 1)
        ) is False

    def test_april_23_not_trading(self, calendar):
        """23 Nisan tatili."""
        assert calendar.is_trading_day(
            dt.date(2024, 4, 23)
        ) is False

    def test_may_1_not_trading(self, calendar):
        """1 Mayıs İşçi Bayramı."""
        assert calendar.is_trading_day(
            dt.date(2024, 5, 1)
        ) is False

    def test_victory_day_not_trading(self, calendar):
        """30 Ağustos Zafer Bayramı."""
        assert calendar.is_trading_day(
            dt.date(2024, 8, 30)
        ) is False

    def test_republic_day_not_trading(self, calendar):
        """29 Ekim Cumhuriyet Bayramı."""
        assert calendar.is_trading_day(
            dt.date(2024, 10, 29)
        ) is False


class TestReligiousHolidays:
    """Dini tatil kontrolleri."""

    def test_ramadan_2024_not_trading(self, calendar):
        """Ramazan Bayramı 2024 tatil."""
        assert calendar.is_trading_day(
            dt.date(2024, 4, 10)
        ) is False
        assert calendar.is_trading_day(
            dt.date(2024, 4, 11)
        ) is False

    def test_eid_al_adha_2024_not_trading(self, calendar):
        """Kurban Bayramı 2024 tatil."""
        assert calendar.is_trading_day(
            dt.date(2024, 6, 17)
        ) is False


class TestNavigationMethods:
    """next/previous trading day testleri."""

    def test_next_trading_day_from_friday(self, calendar):
        """Cuma'dan sonraki işlem günü Pazartesi."""
        # 2024-01-05 Cuma → 2024-01-08 Pazartesi
        result = calendar.next_trading_day(
            dt.date(2024, 1, 5)
        )
        assert result == dt.date(2024, 1, 8)

    def test_next_trading_day_skips_holiday(self, calendar):
        """Tatil gününü atlama."""
        # 2024-04-22 Pazartesi → 23 Nisan tatil →
        # 2024-04-24 Çarşamba
        result = calendar.next_trading_day(
            dt.date(2024, 4, 22)
        )
        assert result == dt.date(2024, 4, 24)

    def test_previous_trading_day(self, calendar):
        """Pazartesi'den önceki işlem günü Cuma."""
        # 2024-01-08 Pazartesi → 2024-01-05 Cuma
        result = calendar.previous_trading_day(
            dt.date(2024, 1, 8)
        )
        assert result == dt.date(2024, 1, 5)

    def test_next_n_trading_days(self, calendar):
        """3 işlem günü ileri."""
        result = calendar.next_trading_day(
            dt.date(2024, 1, 2), offset=3
        )
        assert result == dt.date(2024, 1, 5)

    def test_trading_days_between(self, calendar):
        """Bir haftalık işlem günleri."""
        days = calendar.trading_days_between(
            dt.date(2024, 1, 2),  # Salı
            dt.date(2024, 1, 8),  # Pazartesi
        )
        # Salı, Çarşamba, Perşembe, Cuma, Pazartesi = 5
        assert len(days) == 5

    def test_trading_days_between_empty(self, calendar):
        """Hafta sonu aralığı boş."""
        days = calendar.trading_days_between(
            dt.date(2024, 1, 6),  # Cumartesi
            dt.date(2024, 1, 7),  # Pazar
        )
        assert len(days) == 0


class TestHalfDays:
    """Yarım gün testleri."""

    def test_republic_day_eve_is_half(self, calendar):
        """28 Ekim Cumhuriyet arefesi yarım gün."""
        assert calendar.is_half_day(
            dt.date(2024, 10, 28)
        ) is True

    def test_normal_day_not_half(self, calendar):
        """Normal gün yarım gün değil."""
        assert calendar.is_half_day(
            dt.date(2024, 1, 15)
        ) is False

    def test_half_day_session_times(self, calendar):
        """Yarım gün seans saatleri."""
        times = calendar.get_session_times(
            dt.date(2024, 10, 28)
        )
        assert times["close"] == "13:00"


class TestSessionTimes:
    """Seans saatleri testleri."""

    def test_normal_session(self, calendar):
        """Normal gün seans saatleri."""
        times = calendar.get_session_times(
            dt.date(2024, 1, 15)
        )
        assert times["open"] == "10:00"
        assert times["close"] == "18:00"
        assert times["lunch_start"] == "12:30"
        assert times["lunch_end"] == "14:00"
