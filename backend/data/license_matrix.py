"""
license_matrix.py — Veri lisansı matrisi.

Her provider/piyasa/veri tipi kombinasyonu için:
  - Canlı mı, gecikmeli mi
  - Yeniden dağıtılabilir mi (redistribute)
  - Maksimum cache süresi
  - Gereken minimum kullanıcı planı
  - Hukuki not
  - Export/paylaşım kısıtı

Kabul kriterleri:
  - Lisansı olmayan veri ücretli özellik gibi paketlenemez.
  - Export/paylaşım lisans matrisine göre sınırlandırılır.
  - Herhangi bir yüzey bu modülü sorgulayarak karar verir.

Kullanım:
    from backend.data.license_matrix import license_matrix, LicenseViolation

    entry = license_matrix.get("yfinance", "BIST", "ohlcv")
    if not entry.can_redistribute:
        raise LicenseViolation("Bu veri yeniden dağıtılamaz.")

    ok = license_matrix.check_export_allowed("yfinance", "BIST", "ohlcv", user_plan="free")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

# ─── Tipler ──────────────────────────────────────────────────────────────────

Plan = Literal["guest", "free", "pro", "ultra", "admin"]
_PLAN_RANK: dict[str, int] = {"guest": 0, "free": 1, "pro": 2, "ultra": 3, "admin": 99}


class LicenseViolation(PermissionError):
    """Veri lisans ihlali."""


@dataclass(frozen=True)
class LicenseEntry:
    """Tek bir provider/piyasa/veri tipi kombinasyonunun lisans bilgisi."""
    provider: str
    market: str
    data_type: str                  # ohlcv | tick | fundamental | news | derivative

    # Veri gecikmesi
    is_live: bool = False           # True = gerçek zamanlı
    delay_minutes: int = 15         # Gecikme (dakika), is_live=True ise 0

    # Dağıtım hakları
    can_redistribute: bool = False  # Üçüncü tarafa verilebilir mi?
    can_export: bool = True         # CSV/JSON indirilebilir mi?
    can_share_backtest: bool = True # Backtest paylaşımında kullanılabilir mi?

    # Kısıtlamalar
    max_cache_seconds: int = 60     # Maksimum geçerli cache süresi (saniye)
    min_plan: Plan = "free"         # Bu veriyi görmek için gereken minimum plan
    export_min_plan: Plan = "pro"   # Export için gereken plan

    # Hukuki
    legal_note: str = ""
    source_url: str = ""

    def plan_rank(self, plan: str) -> int:
        return _PLAN_RANK.get(plan, 0)

    def is_plan_allowed(self, user_plan: str) -> bool:
        return self.plan_rank(user_plan) >= self.plan_rank(self.min_plan)

    def is_export_allowed(self, user_plan: str) -> bool:
        if not self.can_export:
            return False
        return self.plan_rank(user_plan) >= self.plan_rank(self.export_min_plan)

    def to_dict(self) -> dict:
        return {
            "provider":           self.provider,
            "market":             self.market,
            "data_type":          self.data_type,
            "is_live":            self.is_live,
            "delay_minutes":      self.delay_minutes,
            "can_redistribute":   self.can_redistribute,
            "can_export":         self.can_export,
            "can_share_backtest": self.can_share_backtest,
            "max_cache_seconds":  self.max_cache_seconds,
            "min_plan":           self.min_plan,
            "export_min_plan":    self.export_min_plan,
            "legal_note":         self.legal_note,
        }


# ─── Matris ──────────────────────────────────────────────────────────────────

# (provider, market, data_type) → LicenseEntry

_MATRIX: dict[tuple[str, str, str], LicenseEntry] = {}


def _add(*entries: LicenseEntry) -> None:
    for e in entries:
        _MATRIX[(e.provider.lower(), e.market.upper(), e.data_type.lower())] = e


# ── Yahoo Finance ─────────────────────────────────────────────────────────────
_add(
    LicenseEntry(
        provider="yfinance", market="BIST", data_type="ohlcv",
        is_live=False, delay_minutes=15,
        can_redistribute=False, can_export=True, can_share_backtest=True,
        max_cache_seconds=300,
        min_plan="free", export_min_plan="pro",
        legal_note=(
            "Yahoo Finance verisi yalnızca kişisel kullanım içindir. "
            "Yeniden dağıtım, Yahoo Finance Kullanım Koşulları'nı ihlal eder. "
            "Ticari lisans için Matriks veya Foreks API gereklidir."
        ),
        source_url="https://finance.yahoo.com/",
    ),
    LicenseEntry(
        provider="yfinance", market="CRYPTO", data_type="ohlcv",
        is_live=False, delay_minutes=0,
        can_redistribute=False, can_export=True, can_share_backtest=True,
        max_cache_seconds=60,
        min_plan="free", export_min_plan="pro",
        legal_note="Yahoo Finance kripto verisi gecikmesiz ama yeniden dağıtım yasaktır.",
    ),
    LicenseEntry(
        provider="yfinance", market="GLOBAL", data_type="ohlcv",
        is_live=False, delay_minutes=15,
        can_redistribute=False, can_export=True, can_share_backtest=True,
        max_cache_seconds=300,
        min_plan="free", export_min_plan="pro",
        legal_note="Yahoo Finance kişisel kullanım lisansı. Redistribution yasak.",
    ),
    LicenseEntry(
        provider="yfinance", market="BIST", data_type="fundamental",
        is_live=False, delay_minutes=1440,  # 1 gün
        can_redistribute=False, can_export=False, can_share_backtest=False,
        max_cache_seconds=86400,
        min_plan="free", export_min_plan="ultra",
        legal_note="Finansal tablo verisi KAP üzerinden gelir; dağıtım için KAP lisansı gerekir.",
    ),
)

# ── Binance ───────────────────────────────────────────────────────────────────
_add(
    LicenseEntry(
        provider="binance", market="CRYPTO", data_type="ohlcv",
        is_live=True, delay_minutes=0,
        can_redistribute=False, can_export=True, can_share_backtest=True,
        max_cache_seconds=30,
        min_plan="free", export_min_plan="pro",
        legal_note=(
            "Binance API verisi kişisel ve ticari olmayan kullanım için açıktır. "
            "Binance API Kullanım Koşulları: https://www.binance.com/en/terms"
        ),
        source_url="https://api.binance.com/",
    ),
    LicenseEntry(
        provider="binance", market="CRYPTO", data_type="tick",
        is_live=True, delay_minutes=0,
        can_redistribute=False, can_export=False, can_share_backtest=False,
        max_cache_seconds=5,
        min_plan="pro", export_min_plan="ultra",
        legal_note="Tick-level veri redistribution yasak; yalnızca platform içi kullanım.",
    ),
)

# ── Matriks ───────────────────────────────────────────────────────────────────
_add(
    LicenseEntry(
        provider="matriks", market="BIST", data_type="ohlcv",
        is_live=True, delay_minutes=0,
        can_redistribute=False, can_export=True, can_share_backtest=True,
        max_cache_seconds=10,
        min_plan="pro", export_min_plan="ultra",
        legal_note=(
            "Matriks BIST verisi ticari lisansa tabidir. "
            "Veri aboneliği olmadan kullanım Matriks lisans sözleşmesini ihlal eder."
        ),
        source_url="https://www.matriks.com/",
    ),
    LicenseEntry(
        provider="matriks", market="BIST", data_type="tick",
        is_live=True, delay_minutes=0,
        can_redistribute=False, can_export=False, can_share_backtest=False,
        max_cache_seconds=5,
        min_plan="ultra", export_min_plan="ultra",
        legal_note="BIST tick verisi yalnızca lisanslı aracı kuruluş sözleşmesi ile kullanılabilir.",
    ),
    LicenseEntry(
        provider="matriks", market="VIOP", data_type="ohlcv",
        is_live=True, delay_minutes=0,
        can_redistribute=False, can_export=False, can_share_backtest=False,
        max_cache_seconds=10,
        min_plan="ultra", export_min_plan="ultra",
        legal_note="VİOP veri dağıtımı için Borsa İstanbul veri lisansı zorunludur.",
    ),
)

# ── Foreks ────────────────────────────────────────────────────────────────────
_add(
    LicenseEntry(
        provider="foreks", market="BIST", data_type="ohlcv",
        is_live=True, delay_minutes=0,
        can_redistribute=False, can_export=True, can_share_backtest=True,
        max_cache_seconds=10,
        min_plan="pro", export_min_plan="ultra",
        legal_note="Foreks veri lisansı. Yeniden dağıtım yasak.",
        source_url="https://www.foreks.com/",
    ),
)

# ── KAP (Kamuyu Aydınlatma Platformu) ────────────────────────────────────────
_add(
    LicenseEntry(
        provider="kap", market="BIST", data_type="fundamental",
        is_live=False, delay_minutes=0,
        can_redistribute=True,   # KAP açık kaynak kabul edilir
        can_export=True, can_share_backtest=True,
        max_cache_seconds=3600,
        min_plan="free", export_min_plan="free",
        legal_note=(
            "KAP (kap.org.tr) verisi kamuya açıktır. "
            "Şirket finansal tabloları serbest paylaşılabilir."
        ),
        source_url="https://www.kap.org.tr/",
    ),
    LicenseEntry(
        provider="kap", market="BIST", data_type="news",
        is_live=False, delay_minutes=0,
        can_redistribute=True,
        can_export=True, can_share_backtest=True,
        max_cache_seconds=300,
        min_plan="free", export_min_plan="free",
        legal_note="KAP bildirimleri kamunun kullanımına açıktır.",
    ),
)

# ── Redis (dahili cache — lisans değil ama politika) ─────────────────────────
_add(
    LicenseEntry(
        provider="redis", market="ALL", data_type="ohlcv",
        is_live=True, delay_minutes=0,
        can_redistribute=False, can_export=False, can_share_backtest=False,
        max_cache_seconds=60,
        min_plan="free", export_min_plan="ultra",
        legal_note=(
            "Redis cache yalnızca dahili kullanım içindir. "
            "Cache'deki veri orijinal provider lisansına tabidir."
        ),
    ),
)


# ─── LicenseMatrix ───────────────────────────────────────────────────────────

class LicenseMatrix:
    """Veri lisansı matrisini sorgular."""

    def get(
        self,
        provider: str,
        market: str,
        data_type: str,
    ) -> LicenseEntry | None:
        """Tam eşleşme arar; bulamazsa None döner."""
        key = (provider.lower(), market.upper(), data_type.lower())
        return _MATRIX.get(key)

    def get_or_default(
        self,
        provider: str,
        market: str,
        data_type: str,
    ) -> LicenseEntry:
        """
        Tam eşleşme arar; bulamazsa kısıtlayıcı varsayılan döner.
        'Bilinmeyen lisans = kısıtlayıcı' prensibi uygulanır.
        """
        entry = self.get(provider, market, data_type)
        if entry:
            return entry
        # Güvenli varsayılan: redistribute yok, export yok, pro planı gerekli
        return LicenseEntry(
            provider=provider,
            market=market,
            data_type=data_type,
            is_live=False,
            delay_minutes=15,
            can_redistribute=False,
            can_export=False,
            can_share_backtest=False,
            max_cache_seconds=300,
            min_plan="pro",
            export_min_plan="ultra",
            legal_note=f"'{provider}/{market}/{data_type}' için lisans tanımlı değil — kısıtlayıcı varsayılan uygulanıyor.",
        )

    def check_export_allowed(
        self,
        provider: str,
        market: str,
        data_type: str,
        user_plan: str,
    ) -> bool:
        """Bu veri export için uygun mu?"""
        entry = self.get_or_default(provider, market, data_type)
        return entry.is_export_allowed(user_plan)

    def check_view_allowed(
        self,
        provider: str,
        market: str,
        data_type: str,
        user_plan: str,
    ) -> bool:
        """Bu veriyi görmek için plan yeterli mi?"""
        entry = self.get_or_default(provider, market, data_type)
        return entry.is_plan_allowed(user_plan)

    def assert_export(
        self,
        provider: str,
        market: str,
        data_type: str,
        user_plan: str,
    ) -> None:
        """Export uygun değilse LicenseViolation fırlatır."""
        if not self.check_export_allowed(provider, market, data_type, user_plan):
            entry = self.get_or_default(provider, market, data_type)
            raise LicenseViolation(
                f"'{provider}/{market}/{data_type}' verisi '{user_plan}' planında export edilemez. "
                f"Gereken plan: {entry.export_min_plan}. "
                f"Not: {entry.legal_note}"
            )

    def all_entries(self) -> list[LicenseEntry]:
        return list(_MATRIX.values())

    def as_dict(self) -> list[dict]:
        return [e.to_dict() for e in self.all_entries()]


# Singleton
license_matrix = LicenseMatrix()
