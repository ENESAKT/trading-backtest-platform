"""
Quant Engine — Veri Kalite Kontrolü (Data Validator)

Çekilen verilerin güvenilirliğini doğrular.
Backtest sonuçlarının doğruluğu, veri kalitesine doğrudan bağlıdır.

Düzeltilen bug'lar:
    VAL-1: NaN fiyatları artık yakalanıyor
    VAL-2: Negatif volume artık yakalanıyor
    VAL-3: low > close artık yakalanıyor (tam OHLC tutarlılık)
    VAL-4: auto_fix sınırlandırıldı (max_ffill_limit eklendi)

Kontroller:
    1. Boşluk (gap) tespiti — eksik işlem günleri
    2. Outlier tespiti — anormal fiyat hareketleri
    3. Tarih sıralaması — kronolojik düzen
    4. Negatif/sıfır fiyat kontrolü
    5. NaN fiyat kontrolü (VAL-1)
    6. Negatif volume kontrolü (VAL-2)
    7. OHLC tam tutarlılık kontrolü (VAL-3)
    8. Volume tutarlılığı
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
        max_ffill_limit: int = 3,
    ):
        """
        Args:
            max_daily_change_pct: Maks. günlük değişim %
            max_gap_days: Kabul edilebilir maks. takvim günü
            min_rows: Minimum satır sayısı eşiği
            max_ffill_limit: auto_fix'te maks. forward fill satır
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
        self._check_date_order(df, result)
        self._check_duplicates(df, result)
        self._check_nan_prices(df, result)       # VAL-1 FIX
        self._check_price_validity(df, result)
        self._check_ohlc_consistency(df, result)  # VAL-3 FIX
        self._check_volume(df, result)            # VAL-2 FIX
        self._check_outliers(df, result)
        self._check_gaps(df, result)

        logger.info(result.summary())
        return result

    def _check_required_columns(
        self, df: pd.DataFrame, result: ValidationResult
    ):
        """Zorunlu sütunların varlığını kontrol et."""
        required = {"date", "open", "high", "low", "close"}
        missing = required - set(df.columns)
        if missing:
            result.add_error(f"Eksik sütunlar: {missing}")

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

    def _check_duplicates(
        self, df: pd.DataFrame, result: ValidationResult
    ):
        """Tekrarlayan tarihleri tespit et."""
        if "date" not in df.columns:
            return
        dupes = df.duplicated(
            subset=["date"], keep=False
        ).sum()
        if dupes > 0:
            result.add_warning(
                f"{dupes} tekrarlayan tarih bulundu"
            )

    def _check_nan_prices(
        self, df: pd.DataFrame, result: ValidationResult
    ):
        """VAL-1 FIX: NaN fiyatları tespit et."""
        price_cols = [
            c for c in ["open", "high", "low", "close"]
            if c in df.columns
        ]
        for col in price_cols:
            nan_count = df[col].isna().sum()
            if nan_count > 0:
                result.add_error(
                    f"'{col}' sütununda {nan_count} "
                    f"NaN değer tespit edildi"
                )

    def _check_price_validity(
        self, df: pd.DataFrame, result: ValidationResult
    ):
        """Negatif veya sıfır fiyatları tespit et."""
        price_cols = [
            c for c in ["open", "high", "low", "close"]
            if c in df.columns
        ]
        for col in price_cols:
            # NaN olmayan değerlerde kontrol yap
            valid_mask = df[col].notna()
            invalid = (df.loc[valid_mask, col] <= 0).sum()
            if invalid > 0:
                result.add_error(
                    f"'{col}' sütununda {invalid} "
                    f"geçersiz fiyat (≤0)"
                )

    def _check_ohlc_consistency(
        self, df: pd.DataFrame, result: ValidationResult
    ):
        """VAL-3 FIX: Tam OHLC mantıksal tutarlılık kontrolü.

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

        # NaN satırları atla
        valid = df[required].dropna()
        if valid.empty:
            return

        high_low = (valid["high"] < valid["low"]).sum()
        if high_low > 0:
            result.add_error(
                f"{high_low} satırda High < Low "
                f"(OHLC tutarsız)"
            )

        high_open = (valid["high"] < valid["open"]).sum()
        if high_open > 0:
            result.add_warning(
                f"{high_open} satırda High < Open"
            )

        high_close = (valid["high"] < valid["close"]).sum()
        if high_close > 0:
            result.add_warning(
                f"{high_close} satırda High < Close"
            )

        low_open = (valid["low"] > valid["open"]).sum()
        if low_open > 0:
            result.add_warning(
                f"{low_open} satırda Low > Open"
            )

        # VAL-3 FIX: low > close artık yakalanıyor
        low_close = (valid["low"] > valid["close"]).sum()
        if low_close > 0:
            result.add_warning(
                f"{low_close} satırda Low > Close"
            )

    def _check_volume(
        self, df: pd.DataFrame, result: ValidationResult
    ):
        """VAL-2 FIX: Volume tutarlılığını kontrol et.

        Artık negatif volume da yakalanıyor.
        """
        if "volume" not in df.columns:
            return

        # VAL-2 FIX: Negatif volume kontrolü
        neg_vol = (df["volume"] < 0).sum()
        if neg_vol > 0:
            result.add_error(
                f"{neg_vol} satırda negatif volume "
                f"tespit edildi"
            )

        zero_vol = (df["volume"] == 0).sum()
        pct = (zero_vol / len(df)) * 100
        if pct > 10:
            result.add_warning(
                f"Yüksek sıfır-volume oranı: "
                f"{pct:.1f}% ({zero_vol} gün)"
            )

    def _check_outliers(
        self, df: pd.DataFrame, result: ValidationResult
    ):
        """Anormal fiyat hareketlerini tespit et."""
        if "close" not in df.columns or len(df) < 2:
            return

        returns = df["close"].pct_change().abs() * 100
        outliers = returns[
            returns > self.max_daily_change_pct
        ]

        if len(outliers) > 0:
            result.add_warning(
                f"{len(outliers)} günde "
                f"%{self.max_daily_change_pct}'den fazla "
                f"değişim. Olası split/temettü veya veri "
                f"hatası!"
            )

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

        VAL-4 FIX: forward-fill artık sınırlı.

        - Tekrarlayan tarihleri temizle
        - Tarihleri sırala
        - NaN fiyatları sınırlı forward-fill ile doldur
        """
        if df.empty:
            return df

        fixed = df.copy()

        # Tekrarları temizle
        if "date" in fixed.columns:
            fixed = fixed.drop_duplicates(
                subset=["date"], keep="last"
            )
            fixed = fixed.sort_values("date").reset_index(
                drop=True
            )

        # VAL-4 FIX: NaN fiyatları sınırlı forward-fill
        price_cols = [
            c for c in ["open", "high", "low", "close"]
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
