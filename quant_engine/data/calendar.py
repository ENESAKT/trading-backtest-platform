"""
Quant Engine — BIST Trading Calendar

Borsa İstanbul işlem takvimi yönetimi.

Özellikler:
    - İşlem günleri, tatiller, yarım günler
    - Müzayede dönemleri
    - Europe/Istanbul timezone → UTC normalize
    - is_trading_day(), next_trading_day(), trading_days_between()

BIST Seans Saatleri (2024):
    Sürekli İşlem:  10:00 - 18:00
    Öğle Arası:     12:30 - 14:00
    Açılış Müzayede: 09:55 - 10:00
    Kapanış Müzayede: 18:00 - 18:10

Resmi Tatiller (2024-2025 bazlı, yıllık güncelleme gerekir):
    - 1 Ocak: Yılbaşı
    - 23 Nisan: Ulusal Egemenlik ve Çocuk Bayramı
    - 1 Mayıs: İşçi Bayramı
    - 19 Mayıs: Gençlik ve Spor Bayramı
    - 15 Temmuz: Demokrasi ve Milli Birlik Günü
    - 30 Ağustos: Zafer Bayramı
    - 29 Ekim: Cumhuriyet Bayramı
    - Ramazan Bayramı (3 gün, hicri takvime göre değişir)
    - Kurban Bayramı (4 gün, hicri takvime göre değişir)
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

from loguru import logger

# ---------------------------------------------------------------------------
# Sabit Tatiller (her yıl aynı tarih)
# ---------------------------------------------------------------------------

_FIXED_HOLIDAYS: list[tuple[int, int]] = [
    (1, 1),    # Yılbaşı
    (4, 23),   # Ulusal Egemenlik ve Çocuk Bayramı
    (5, 1),    # İşçi Bayramı
    (5, 19),   # Gençlik ve Spor Bayramı
    (7, 15),   # Demokrasi ve Milli Birlik Günü
    (8, 30),   # Zafer Bayramı
    (10, 29),  # Cumhuriyet Bayramı
]

# ---------------------------------------------------------------------------
# Dini Tatiller (hicri takvime göre değişir)
# Yaklaşık tarihler — her yıl ~11 gün geriye kayar
# Bu liste yıllık olarak güncellenmeli
# ---------------------------------------------------------------------------

_RELIGIOUS_HOLIDAYS: dict[int, list[dt.date]] = {
    2024: [
        # Ramazan Bayramı 2024
        dt.date(2024, 4, 10),
        dt.date(2024, 4, 11),
        dt.date(2024, 4, 12),
        # Kurban Bayramı 2024
        dt.date(2024, 6, 17),
        dt.date(2024, 6, 18),
        dt.date(2024, 6, 19),
        dt.date(2024, 6, 20),
    ],
    2025: [
        # Ramazan Bayramı 2025
        dt.date(2025, 3, 30),
        dt.date(2025, 3, 31),
        dt.date(2025, 4, 1),
        # Kurban Bayramı 2025
        dt.date(2025, 6, 6),
        dt.date(2025, 6, 7),
        dt.date(2025, 6, 8),
        dt.date(2025, 6, 9),
    ],
    2026: [
        # Ramazan Bayramı 2026 (tahmini)
        dt.date(2026, 3, 20),
        dt.date(2026, 3, 21),
        dt.date(2026, 3, 22),
        # Kurban Bayramı 2026 (tahmini)
        dt.date(2026, 5, 27),
        dt.date(2026, 5, 28),
        dt.date(2026, 5, 29),
        dt.date(2026, 5, 30),
    ],
}

# ---------------------------------------------------------------------------
# Yarım Günler (Cumhuriyet Bayramı arefesi vb.)
# ---------------------------------------------------------------------------

_HALF_DAYS: dict[int, list[dt.date]] = {
    2024: [
        dt.date(2024, 10, 28),  # Cumhuriyet arefesi
    ],
    2025: [
        dt.date(2025, 10, 28),
    ],
    2026: [
        dt.date(2026, 10, 28),
    ],
}


class BISTCalendar:
    """
    BIST işlem takvimi.

    İşlem günlerini, tatilleri ve seans saatlerini yönetir.
    """

    def __init__(self):
        self._holiday_cache: dict[int, set[dt.date]] = {}

    def _get_holidays_for_year(
        self, year: int
    ) -> set[dt.date]:
        """Bir yılın tüm tatil günlerini döndür (cache'li)."""
        if year in self._holiday_cache:
            return self._holiday_cache[year]

        holidays: set[dt.date] = set()

        # Sabit tatiller
        for month, day in _FIXED_HOLIDAYS:
            holidays.add(dt.date(year, month, day))

        # Dini tatiller
        if year in _RELIGIOUS_HOLIDAYS:
            holidays.update(_RELIGIOUS_HOLIDAYS[year])
        else:
            logger.warning(
                f"⚠️ {year} yılı dini tatilleri "
                f"tanımlı değil! Güncellenmelidir."
            )

        self._holiday_cache[year] = holidays
        return holidays

    def is_holiday(self, date: dt.date) -> bool:
        """Verilen tarih tatil mi?"""
        return date in self._get_holidays_for_year(date.year)

    def is_weekend(self, date: dt.date) -> bool:
        """Verilen tarih hafta sonu mu?"""
        return date.weekday() >= 5  # 5=Cumartesi, 6=Pazar

    def is_trading_day(self, date: dt.date) -> bool:
        """Verilen tarih işlem günü mü?"""
        if self.is_weekend(date):
            return False
        if self.is_holiday(date):
            return False
        return True

    def is_half_day(self, date: dt.date) -> bool:
        """Verilen tarih yarım gün mü?"""
        half_days = _HALF_DAYS.get(date.year, [])
        return date in half_days

    def next_trading_day(
        self, date: dt.date, offset: int = 1
    ) -> dt.date:
        """
        Sonraki N. işlem gününü bul.

        Args:
            date: Başlangıç tarihi
            offset: Kaç işlem günü ilerle (varsayılan 1)
        """
        count = 0
        current = date
        while count < offset:
            current += dt.timedelta(days=1)
            if self.is_trading_day(current):
                count += 1
        return current

    def previous_trading_day(
        self, date: dt.date, offset: int = 1
    ) -> dt.date:
        """
        Önceki N. işlem gününü bul.

        Args:
            date: Başlangıç tarihi
            offset: Kaç işlem günü gerile (varsayılan 1)
        """
        count = 0
        current = date
        while count < offset:
            current -= dt.timedelta(days=1)
            if self.is_trading_day(current):
                count += 1
        return current

    def trading_days_between(
        self,
        start: dt.date,
        end: dt.date,
    ) -> list[dt.date]:
        """
        İki tarih arasındaki işlem günlerini listele.

        Args:
            start: Başlangıç (dahil)
            end: Bitiş (dahil)

        Returns:
            list[dt.date]: İşlem günleri listesi
        """
        if start > end:
            return []

        days: list[dt.date] = []
        current = start
        while current <= end:
            if self.is_trading_day(current):
                days.append(current)
            current += dt.timedelta(days=1)
        return days

    def trading_day_count(
        self,
        start: dt.date,
        end: dt.date,
    ) -> int:
        """İki tarih arasındaki işlem günü sayısı."""
        return len(self.trading_days_between(start, end))

    def get_session_times(
        self, date: Optional[dt.date] = None
    ) -> dict[str, str]:
        """
        Seans saatlerini döndür.

        Returns:
            dict: open, close, lunch_start, lunch_end
        """
        is_half = date and self.is_half_day(date)

        return {
            "open": "10:00",
            "close": "13:00" if is_half else "18:00",
            "lunch_start": "12:30",
            "lunch_end": "13:00" if is_half else "14:00",
            "auction_open_start": "09:55",
            "auction_open_end": "10:00",
            "auction_close_start": (
                "13:00" if is_half else "18:00"
            ),
            "auction_close_end": (
                "13:10" if is_half else "18:10"
            ),
        }
