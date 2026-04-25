"""
Quant Engine — Veri Kalite Kontrolü (Data Validator)

Çekilen verilerin güvenilirliğini doğrular.
Backtest sonuçlarının doğruluğu, veri kalitesine doğrudan bağlıdır.

Kontroller:
    1. Boşluk (gap) tespiti — eksik işlem günleri
    2. Outlier tespiti — anormal fiyat hareketleri
    3. Tarih sıralaması — kronolojik düzen
    4. Negatif/sıfır fiyat kontrolü
    5. Volume tutarlılığı
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from loguru import logger


@dataclass
class ValidationResult:
    """Tek bir sembol için doğrulama sonucu."""
    symbol: str
    is_valid: bool = True
    total_rows: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def add_warning(self, msg: str):
        self.warnings.append(msg)
        logger.warning(f"⚠️ {self.symbol}: {msg}")

    def add_error(self, msg: str):
        self.errors.append(msg)
        self.is_valid = False
        logger.error(f"❌ {self.symbol}: {msg}")

    def summary(self) -> str:
        status = "✅ GEÇER" if self.is_valid else "❌ BAŞARISIZ"
        return (
            f"{self.symbol}: {status} | "
            f"{self.total_rows} satır | "
            f"{len(self.warnings)} uyarı | "
            f"{len(self.errors)} hata"
        )


class DataValidator:
    """
    Finansal veri doğrulayıcı.

    Çekilen OHLCV verilerini çeşitli kurallara göre doğrular.
    Hatalı veriler backtest sonuçlarını tamamen yanıltabilir.
    """

    def __init__(
        self,
        max_daily_change_pct: float = 20.0,
        max_gap_days: int = 10,
        min_rows: int = 20,
    ):
        """
        Args:
            max_daily_change_pct: Maksimum günlük değişim yüzdesi (BIST'te %20 sınırı var)
            max_gap_days: Kabul edilebilir maksimum takvim günü boşluğu
            min_rows: Minimum satır sayısı eşiği
        """
        self.max_daily_change_pct = max_daily_change_pct
        self.max_gap_days = max_gap_days
        self.min_rows = min_rows

    def validate(self, df: pd.DataFrame, symbol: str = "UNKNOWN") -> ValidationResult:
        """
        DataFrame'i tüm kurallara göre doğrula.

        Args:
            df: Doğrulanacak OHLCV verisi
            symbol: Sembol adı (loglama için)

        Returns:
            ValidationResult: Doğrulama sonucu
        """
        result = ValidationResult(symbol=symbol, total_rows=len(df))

        if df.empty:
            result.add_error("DataFrame boş!")
            return result

        if len(df) < self.min_rows:
            result.add_warning(f"Çok az veri: {len(df)} satır (min: {self.min_rows})")

        # Tüm kontrolleri çalıştır
        self._check_required_columns(df, result)
        self._check_date_order(df, result)
        self._check_duplicates(df, result)
        self._check_price_validity(df, result)
        self._check_ohlc_consistency(df, result)
        self._check_volume(df, result)
        self._check_outliers(df, result)
        self._check_gaps(df, result)

        logger.info(result.summary())
        return result

    def _check_required_columns(self, df: pd.DataFrame, result: ValidationResult):
        """Zorunlu sütunların varlığını kontrol et."""
        required = {"date", "open", "high", "low", "close"}
        missing = required - set(df.columns)
        if missing:
            result.add_error(f"Eksik sütunlar: {missing}")

    def _check_date_order(self, df: pd.DataFrame, result: ValidationResult):
        """Tarihlerin kronolojik sırada olduğunu doğrula."""
        if "date" not in df.columns:
            return
        dates = pd.to_datetime(df["date"])
        if not dates.is_monotonic_increasing:
            result.add_warning("Tarihler kronolojik sırada değil!")

    def _check_duplicates(self, df: pd.DataFrame, result: ValidationResult):
        """Tekrarlayan tarihleri tespit et."""
        if "date" not in df.columns:
            return
        dupes = df.duplicated(subset=["date"], keep=False).sum()
        if dupes > 0:
            result.add_warning(f"{dupes} tekrarlayan tarih bulundu")

    def _check_price_validity(self, df: pd.DataFrame, result: ValidationResult):
        """Negatif veya sıfır fiyatları tespit et."""
        price_cols = [c for c in ["open", "high", "low", "close"] if c in df.columns]
        for col in price_cols:
            invalid = (df[col] <= 0).sum()
            if invalid > 0:
                result.add_error(f"'{col}' sütununda {invalid} geçersiz fiyat (≤0)")

    def _check_ohlc_consistency(self, df: pd.DataFrame, result: ValidationResult):
        """OHLC mantıksal tutarlılığını kontrol et: High ≥ Low, High ≥ Open/Close."""
        if not all(c in df.columns for c in ["open", "high", "low", "close"]):
            return

        high_low = (df["high"] < df["low"]).sum()
        if high_low > 0:
            result.add_warning(f"{high_low} satırda High < Low (OHLC tutarsız)")

        high_max = (df["high"] < df[["open", "close"]].max(axis=1)).sum()
        if high_max > 0:
            result.add_warning(f"{high_max} satırda High, Open/Close'dan küçük")

    def _check_volume(self, df: pd.DataFrame, result: ValidationResult):
        """Volume tutarlılığını kontrol et."""
        if "volume" not in df.columns:
            return

        zero_vol = (df["volume"] == 0).sum()
        pct = (zero_vol / len(df)) * 100
        if pct > 10:
            result.add_warning(f"Yüksek sıfır-volume oranı: {pct:.1f}% ({zero_vol} gün)")

    def _check_outliers(self, df: pd.DataFrame, result: ValidationResult):
        """Anormal fiyat hareketlerini tespit et (BIST'te %20 sınır)."""
        if "close" not in df.columns or len(df) < 2:
            return

        returns = df["close"].pct_change().abs() * 100
        outliers = returns[returns > self.max_daily_change_pct]

        if len(outliers) > 0:
            result.add_warning(
                f"{len(outliers)} günde %{self.max_daily_change_pct}'den fazla değişim. "
                f"Olası split/temettü veya veri hatası!"
            )

    def _check_gaps(self, df: pd.DataFrame, result: ValidationResult):
        """İşlem günü boşluklarını tespit et."""
        if "date" not in df.columns or len(df) < 2:
            return

        dates = pd.to_datetime(df["date"])
        gaps = dates.diff().dt.days
        large_gaps = gaps[gaps > self.max_gap_days]

        if len(large_gaps) > 0:
            result.add_warning(
                f"{len(large_gaps)} büyük boşluk (>{self.max_gap_days} gün)"
            )

    def validate_bulk(
        self, data: dict[str, pd.DataFrame]
    ) -> dict[str, ValidationResult]:
        """Birden fazla sembolü toplu doğrula."""
        results = {}
        for symbol, df in data.items():
            results[symbol] = self.validate(df, symbol)

        valid = sum(1 for r in results.values() if r.is_valid)
        logger.info(
            f"📋 Toplu doğrulama: {valid}/{len(results)} geçerli"
        )

        return results

    @staticmethod
    def auto_fix(df: pd.DataFrame) -> pd.DataFrame:
        """
        Otomatik düzeltilebilecek sorunları düzelt.

        - Tekrarlayan tarihleri temizle
        - Tarihleri sırala
        - NaN fiyatları forward-fill ile doldur
        """
        if df.empty:
            return df

        fixed = df.copy()

        # Tekrarları temizle
        if "date" in fixed.columns:
            fixed = fixed.drop_duplicates(subset=["date"], keep="last")
            fixed = fixed.sort_values("date").reset_index(drop=True)

        # NaN fiyatları doldur (forward fill)
        price_cols = [c for c in ["open", "high", "low", "close"] if c in fixed.columns]
        fixed[price_cols] = fixed[price_cols].ffill()

        # Volume NaN'ları 0 yap
        if "volume" in fixed.columns:
            fixed["volume"] = fixed["volume"].fillna(0).astype("int64")

        return fixed
