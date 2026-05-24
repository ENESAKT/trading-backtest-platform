"""
Merkezi veri sabitleri — tüm backend modülleri buradan import eder.
Timeframe etiketleri burada tanımlanır; endpoint, worker ve test dosyaları
bu listeyi kullanmalı, hardcoded string kullanmamalıdır.
"""
from __future__ import annotations

# ─── Geçerli timeframe etiketleri (canonical, küçük harf) ──────────────────
# Sıra: en küçük → en büyük
VALID_INTERVALS: tuple[str, ...] = (
    "1m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "1d",
    "1w",
    "1mo",
)

VALID_INTERVALS_SET: frozenset[str] = frozenset(VALID_INTERVALS)

# Türkçe görüntü etiketleri (kullanıcı yüzeyi)
TF_DISPLAY_TR: dict[str, str] = {
    "1m":  "1dk",
    "5m":  "5dk",
    "15m": "15dk",
    "30m": "30dk",
    "1h":  "1s",
    "2h":  "2s",
    "4h":  "4s",
    "1d":  "1g",
    "1w":  "1hf",
    "1mo": "1ay",
}

# İngilizce görüntü etiketleri (API dokümantasyonu, log)
TF_DISPLAY_EN: dict[str, str] = {
    "1m":  "1 min",
    "5m":  "5 min",
    "15m": "15 min",
    "30m": "30 min",
    "1h":  "1 hour",
    "2h":  "2 hours",
    "4h":  "4 hours",
    "1d":  "1 day",
    "1w":  "1 week",
    "1mo": "1 month",
}

# Timeframe → saniye
TF_SECONDS: dict[str, int] = {
    "1m":  60,
    "5m":  300,
    "15m": 900,
    "30m": 1_800,
    "1h":  3_600,
    "2h":  7_200,
    "4h":  14_400,
    "1d":  86_400,
    "1w":  604_800,
    "1mo": 2_592_000,  # ~30 gün
}

# Timeframe → minimum bar sayısı (güvenilir indikatör hesabı için)
TF_MIN_BARS: dict[str, int] = {
    "1m":  200,
    "5m":  200,
    "15m": 200,
    "30m": 150,
    "1h":  120,
    "2h":  100,
    "4h":  100,
    "1d":  60,
    "1w":  52,
    "1mo": 24,
}

# Küçük → büyük türetme izin matrisi (derive_timeframes.py için)
# Anahtar: kaynak TF, Değer: bu kaynaktan türetilebilecek TF listesi
DERIVATION_ALLOWED: dict[str, list[str]] = {
    "1m":  ["5m", "15m", "30m", "1h", "2h", "4h", "1d", "1w", "1mo"],
    "5m":  ["15m", "30m", "1h", "2h", "4h", "1d", "1w", "1mo"],
    "15m": ["30m", "1h", "2h", "4h", "1d", "1w", "1mo"],
    "30m": ["1h", "2h", "4h", "1d", "1w", "1mo"],
    "1h":  ["2h", "4h", "1d", "1w", "1mo"],
    "2h":  ["4h", "1d", "1w", "1mo"],
    "4h":  ["1d", "1w", "1mo"],
    "1d":  ["1w", "1mo"],
    "1w":  ["1mo"],
}


def validate_interval(interval: str) -> str:
    """
    Verilen interval'i kontrol eder; geçersizse ValueError fırlatır.
    Geçerliyse normalize edilmiş (küçük harf) halini döner.
    """
    normalized = interval.strip().lower()
    if normalized not in VALID_INTERVALS_SET:
        raise ValueError(
            f"Geçersiz timeframe: '{interval}'. "
            f"İzin verilenler: {', '.join(VALID_INTERVALS)}"
        )
    return normalized


def tf_display(interval: str, lang: str = "tr") -> str:
    """Timeframe'in kullanıcı dostu görüntü etiketini döner."""
    normalized = interval.strip().lower()
    if lang == "tr":
        return TF_DISPLAY_TR.get(normalized, normalized)
    return TF_DISPLAY_EN.get(normalized, normalized)


def can_derive(source_tf: str, target_tf: str) -> bool:
    """Kaynak TF'den hedef TF türetilebilir mi?"""
    source = source_tf.strip().lower()
    target = target_tf.strip().lower()
    allowed = DERIVATION_ALLOWED.get(source, [])
    return target in allowed
