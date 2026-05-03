"""Mali analiz sembol normalizasyonu ve statik metadata fallback'leri."""

from __future__ import annotations


def normalize_symbol(symbol: str) -> str:
    """BIST sembolünü servis içinde kullanılan kanonik forma çevirir."""
    normalized = symbol.strip().upper()
    if normalized.endswith(".IS"):
        normalized = normalized[:-3]
    normalized = normalized.strip()
    if not normalized:
        raise ValueError("symbol boş olamaz")
    return normalized


# Sadece şirket adı metadata'sı içerir; finansal tablo veya oran verisi üretmez.
SYMBOL_METADATA: dict[str, str] = {
    "THYAO": "Türk Hava Yolları A.O.",
    "AKBNK": "Akbank T.A.Ş.",
    "ASELS": "Aselsan Elektronik Sanayi ve Ticaret A.Ş.",
    "VAKBN": "Türkiye Vakıflar Bankası T.A.O.",
    "ARCLK": "Arçelik A.Ş.",
    "GARAN": "Türkiye Garanti Bankası A.Ş.",
    "ISCTR": "Türkiye İş Bankası A.Ş.",
    "KCHOL": "Koç Holding A.Ş.",
    "SAHOL": "Hacı Ömer Sabancı Holding A.Ş.",
    "EREGL": "Ereğli Demir ve Çelik Fabrikaları T.A.Ş.",
    "BIMAS": "BİM Birleşik Mağazalar A.Ş.",
    "TUPRS": "Tüpraş Türkiye Petrol Rafinerileri A.Ş.",
}
