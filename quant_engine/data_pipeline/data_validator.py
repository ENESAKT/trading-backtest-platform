"""
Quant Engine — Veri Kalite Kontrolü (Data Validator)

Çekilen verilerin güvenilirliğini doğrular.
Backtest sonuçlarının doğruluğu, veri kalitesine doğrudan bağlıdır.

Düzeltmeler (Aşama 5):
    - Duplicate kontrolü symbol + timestamp üzerinden
    - OHLC kontrolleri sertleştirildi
    - ValidationResult kalite skoru eklendi
    - Kritik hata varsa backtest engellenebilir
    - Split/temettü fiyat kopması uyarısı
    - Required columns: date/timestamp, OHLCV, symbol

Kontroller:
    1. Zorunlu sütun kontrolü (date, OHLCV, symbol)
    2. Boşluk (gap) tespiti
    3. Outlier / split / temettü tespiti
    4. Tarih sıralaması
    5. Negatif/sıfır fiyat kontrolü
    6. NaN fiyat kontrolü
    7. Negatif volume kontrolü
    8. OHLC tam tutarlılık kontrolü
    9. Symbol + timestamp duplicate kontrolü
    10. Kalite skoru (0-100)
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
    checks_passed: int = 0
    checks_total: int = 0

    @property
    def quality_score(self) -> float:
        """
        Veri kalite skoru (0-100).

        100 = tüm kontroller geçti
        0 = tüm kontroller başarısız
        """
        if self.checks_total == 0:
            return 0.0
        base = (
            self.checks_passed / self.checks_total
        ) * 100
        # Her error skoru %10 düşürür
        penalty = len(self.errors) * 10
        # Her warning skoru %2 düşürür
        penalty += len(self.warnings) * 2
        return max(0.0, min(100.0, base - penalty))

    @property
    def can_run_backtest(self) -> bool:
        """Backtest çalıştırılabilir mi?"""
        return self.is_valid and len(self.errors) == 0

    def add_warning(self, msg: str):
        self.warnings.append(msg)
        logger.warning(f"⚠️ {self.symbol}: {msg}")

    def add_error(self, msg: str):
        self.errors.append(msg)
        self.is_valid = False
        logger.error(f"❌ {self.symbol}: {msg}")

    def _pass_check(self):
        self.checks_passed += 1
        self.checks_total += 1

    def _fail_check(self):
        self.checks_total += 1

    def summary(self) -> str:
        status = (
            "✅ GEÇER" if self.is_valid else "❌ BAŞARISIZ"
        )
        return (
            f"{self.symbol}: {status} | "
            f"{self.total_rows} satır | "
            f"{len(self.warnings)} uyarı | "
            f"{len(self.errors)} hata | "
            f"Kalite: {self.quality_score:.0f}/100"
        )


class DataValidator:
    """
    Finansal veri doğrulayıcı.

    Çekilen OHLCV verilerini çeşitli kurallara göre doğrular.
    Hatalı veriler backtest sonuçlarını tamamen yanıltabilir.
    """

    # Zorunlu sütunlar
    REQUIRED_COLUMNS = {
        "date",
        "open",
        "high",
        "low",
        "close",
    }
    RECOMMENDED_COLUMNS = {"volume", "symbol"}

    def __init__(
        self,
        max_daily_change_pct: float = 20.0,
        max_gap_days: int = 10,
        min_rows: int = 20,
        max_ffill_limit: int = 3,
    ):
        """
        Args:
            max_daily_change_pct: Maks. günlük değişim %
            max_gap_days: Kabul edilebilir maks. takvim günü
            min_rows: Minimum satır sayısı eşiği
            max_ffill_limit: auto_fix'te maks. forward fill
        """
        self.max_daily_change_pct = max_daily_change_pct
        self.max_gap_days = max_gap_days
        self.min_rows = min_rows
        self.max_ffill_limit = max_ffill_limit

    def validate(
        self, df: pd.DataFrame, symbol: str = "UNKNOWN"
    ) -> ValidationResult:
        """
        DataFrame'i tüm kurallara göre doğrula.

        Args:
            df: Doğrulanacak OHLCV verisi
            symbol: Sembol adı (loglama için)

        Returns:
            ValidationResult: Doğrulama sonucu
        """
        result = ValidationResult(
            symbol=symbol, total_rows=len(df)
        )

        if df.empty:
            result.add_error("DataFrame boş!")
            return result

        if len(df) < self.min_rows:
            result.add_warning(
                f"Çok az veri: {len(df)} satır "
                f"(min: {self.min_rows})"
            )

        # Tüm kontrolleri çalıştır
        self._check_required_columns(df, result)
        self._check_recommended_columns(df, result)
        self._check_date_order(df, result)
        self._check_duplicates(df, result)
        self._check_nan_prices(df, result)
        self._check_price_validity(df, result)
        self._check_ohlc_consistency(df, result)
        self._check_volume(df, result)
        self._check_outliers(df, result)
        self._check_gaps(df, result)

        logger.info(result.summary())
        return result

    def _check_required_columns(
        self, df: pd.DataFrame, result: ValidationResult
    ):
        """Zorunlu sütunların varlığını kontrol et."""
        missing = self.REQUIRED_COLUMNS - set(
            df.columns
        )
        if missing:
            result.add_error(
                f"Eksik zorunlu sütunlar: {missing}"
            )
            result._fail_check()
        else:
            result._pass_check()

    def _check_recommended_columns(
        self, df: pd.DataFrame, result: ValidationResult
    ):
        """Önerilen sütunların varlığını kontrol et."""
        missing = self.RECOMMENDED_COLUMNS - set(
            df.columns
        )
        if missing:
            result.add_warning(
                f"Önerilen sütunlar eksik: {missing}"
            )
            result._fail_check()
        else:
            result._pass_check()

    def _check_date_order(
        self, df: pd.DataFrame, result: ValidationResult
    ):
        """Tarihlerin kronolojik sırada olduğunu doğrula."""
        if "date" not in df.columns:
            return
        dates = pd.to_datetime(df["date"])
        if not dates.is_monotonic_increasing:
            result.add_warning(
                "Tarihler kronolojik sırada değil!"
            )
            result._fail_check()
        else:
            result._pass_check()

    def _check_duplicates(
        self, df: pd.DataFrame, result: ValidationResult
    ):
        """Symbol + timestamp üzerinden duplicate kontrol."""
        if "date" not in df.columns:
            return

        # Symbol varsa symbol+date, yoksa sadece date
        subset = ["date"]
        if "symbol" in df.columns:
            subset = ["date", "symbol"]

        dupes = df.duplicated(
            subset=subset, keep=False
        ).sum()
        if dupes > 0:
            result.add_warning(
                f"{dupes} tekrarlayan kayıt bulundu "
                f"({'+'.join(subset)} bazında)"
            )
            result._fail_check()
        else:
            result._pass_check()

    def _check_nan_prices(
        self, df: pd.DataFrame, result: ValidationResult
    ):
        """NaN fiyatları tespit et."""
        price_cols = [
            c
            for c in ["open", "high", "low", "close"]
            if c in df.columns
        ]
        has_nan = False
        for col in price_cols:
            nan_count = df[col].isna().sum()
            if nan_count > 0:
                result.add_error(
                    f"'{col}' sütununda {nan_count} "
                    f"NaN değer tespit edildi"
                )
                has_nan = True

        if has_nan:
            result._fail_check()
        else:
            result._pass_check()

    def _check_price_validity(
        self, df: pd.DataFrame, result: ValidationResult
    ):
        """Negatif veya sıfır fiyatları tespit et."""
        price_cols = [
            c
            for c in ["open", "high", "low", "close"]
            if c in df.columns
        ]
        has_invalid = False
        for col in price_cols:
            valid_mask = df[col].notna()
            invalid = (df.loc[valid_mask, col] <= 0).sum()
            if invalid > 0:
                result.add_error(
                    f"'{col}' sütununda {invalid} "
                    f"geçersiz fiyat (≤0)"
                )
                has_invalid = True

        if has_invalid:
            result._fail_check()
        else:
            result._pass_check()

    def _check_ohlc_consistency(
        self, df: pd.DataFrame, result: ValidationResult
    ):
        """Tam OHLC mantıksal tutarlılık kontrolü.

        Kurallar:
        - High >= Low
        - High >= Open
        - High >= Close
        - Low <= Open
        - Low <= Close
        """
        required = ["open", "high", "low", "close"]
        if not all(c in df.columns for c in required):
            return

        valid = df[required].dropna()
        if valid.empty:
            return

        has_error = False

        high_low = (valid["high"] < valid["low"]).sum()
        if high_low > 0:
            result.add_error(
                f"{high_low} satırda High < Low "
                f"(OHLC tutarsız)"
            )
            has_error = True

        high_open = (
            valid["high"] < valid["open"]
        ).sum()
        if high_open > 0:
            result.add_warning(
                f"{high_open} satırda High < Open"
            )

        high_close = (
            valid["high"] < valid["close"]
        ).sum()
        if high_close > 0:
            result.add_warning(
                f"{high_close} satırda High < Close"
            )

        low_open = (valid["low"] > valid["open"]).sum()
        if low_open > 0:
            result.add_warning(
                f"{low_open} satırda Low > Open"
            )

        low_close = (
            valid["low"] > valid["close"]
        ).sum()
        if low_close > 0:
            result.add_warning(
                f"{low_close} satırda Low > Close"
            )

        if has_error:
            result._fail_check()
        else:
            result._pass_check()

    def _check_volume(
        self, df: pd.DataFrame, result: ValidationResult
    ):
        """Volume tutarlılığını kontrol et."""
        if "volume" not in df.columns:
            return

        has_error = False

        neg_vol = (df["volume"] < 0).sum()
        if neg_vol > 0:
            result.add_error(
                f"{neg_vol} satırda negatif volume "
                f"tespit edildi"
            )
            has_error = True

        zero_vol = (df["volume"] == 0).sum()
        pct = (zero_vol / len(df)) * 100
        if pct > 10:
            result.add_warning(
                f"Yüksek sıfır-volume oranı: "
                f"{pct:.1f}% ({zero_vol} gün)"
            )

        if has_error:
            result._fail_check()
        else:
            result._pass_check()

    def _check_outliers(
        self, df: pd.DataFrame, result: ValidationResult
    ):
        """Anormal fiyat hareketlerini ve olası split/temettüyü tespit et."""
        if "close" not in df.columns or len(df) < 2:
            return

        returns = df["close"].pct_change().abs() * 100
        outliers = returns[
            returns > self.max_daily_change_pct
        ]

        if len(outliers) > 0:
            # %50+ değişim → olası split/temettü
            extreme = returns[returns > 50]
            if len(extreme) > 0:
                result.add_warning(
                    f"{len(extreme)} günde %50'den fazla "
                    f"değişim. Olası hisse bölünmesi veya "
                    f"temettü düzeltmesi kontrol edilmeli!"
                )

            result.add_warning(
                f"{len(outliers)} günde "
                f"%{self.max_daily_change_pct}'den fazla "
                f"değişim. Olası split/temettü veya veri "
                f"hatası!"
            )
            result._fail_check()
        else:
            result._pass_check()

    def _check_gaps(
        self, df: pd.DataFrame, result: ValidationResult
    ):
        """İşlem günü boşluklarını tespit et."""
        if "date" not in df.columns or len(df) < 2:
            return

        dates = pd.to_datetime(df["date"])
        gaps = dates.diff().dt.days
        large_gaps = gaps[gaps > self.max_gap_days]

        if len(large_gaps) > 0:
            result.add_warning(
                f"{len(large_gaps)} büyük boşluk "
                f"(>{self.max_gap_days} gün)"
            )
            result._fail_check()
        else:
            result._pass_check()

    def validate_bulk(
        self, data: dict[str, pd.DataFrame]
    ) -> dict[str, ValidationResult]:
        """Birden fazla sembolü toplu doğrula."""
        results = {}
        for symbol, df in data.items():
            results[symbol] = self.validate(df, symbol)

        valid = sum(
            1 for r in results.values() if r.is_valid
        )
        logger.info(
            f"📋 Toplu doğrulama: {valid}/{len(results)} "
            f"geçerli"
        )

        return results

    @staticmethod
    def auto_fix(
        df: pd.DataFrame,
        max_ffill_limit: int = 3,
    ) -> pd.DataFrame:
        """
        Otomatik düzeltilebilecek sorunları düzelt.

        - Tekrarlayan tarihleri temizle
        - Tarihleri sırala
        - NaN fiyatları sınırlı forward-fill ile doldur
        """
        if df.empty:
            return df

        fixed = df.copy()

        # Tekrarları temizle
        if "date" in fixed.columns:
            subset = ["date"]
            if "symbol" in fixed.columns:
                subset.append("symbol")
            fixed = fixed.drop_duplicates(
                subset=subset, keep="last"
            )
            fixed = fixed.sort_values(
                "date"
            ).reset_index(drop=True)

        # NaN fiyatları sınırlı forward-fill
        price_cols = [
            c
            for c in ["open", "high", "low", "close"]
            if c in fixed.columns
        ]
        fixed[price_cols] = fixed[price_cols].ffill(
            limit=max_ffill_limit
        )

        # Volume NaN'ları 0 yap
        if "volume" in fixed.columns:
            fixed["volume"] = (
                fixed["volume"].fillna(0).astype("int64")
            )

        return fixed
