"""Mali analiz sembol normalizasyonu, BIST 30 listesi ve metadata."""

from __future__ import annotations

# BIST 30 — 2026 bileşenleri (BİST tarafından güncellenir; burada statik liste)
BIST_30_SYMBOLS: list[str] = [
    "THYAO", "AKBNK", "GARAN", "ISCTR", "YKBNK",
    "VAKBN", "HALKB", "SISE",  "EREGL", "KCHOL",
    "SAHOL", "TCELL", "TUPRS", "BIMAS", "FROTO",
    "TOASO", "ARCLK", "ASELS", "EKGYO", "ENKAI",
    "TAVHL", "TTKOM", "PETKM", "SASA",  "KOZAL",
    "KRDMD", "DOHOL", "PGSUS", "VESTL", "AEFES",
]

# Bankacılık sektörü (bilanço yapısı farklı — aktif/pasif yok, mevduat/kredi var)
BANK_SYMBOLS: set[str] = {"AKBNK", "GARAN", "ISCTR", "YKBNK", "VAKBN", "HALKB", "TSKB", "ALBRK", "SKBNK"}

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
    "AKBNK": "Akbank",
    "ARCLK": "Arçelik",
    "ASELS": "Aselsan",
    "BIMAS": "BİM Mağazalar",
    "DOHOL": "Doğan Holding",
    "EREGL": "Ereğli Demir Çelik",
    "FROTO": "Ford Otosan",
    "GARAN": "Garanti BBVA",
    "HALKB": "Halkbank",
    "ISCTR": "İş Bankası C",
    "KCHOL": "Koç Holding",
    "KOZAL": "Koza Altın",
    "KRDMD": "Kardemir D",
    "MAVI": "Mavi Giyim",
    "PGSUS": "Pegasus",
    "SAHOL": "Sabancı Holding",
    "SASA": "SASA Polyester",
    "SISE": "Şişe Cam",
    "TAVHL": "TAV Havalimanları",
    "TCELL": "Turkcell",
    "THYAO": "Türk Hava Yolları",
    "TOASO": "Tofaş Otomobil",
    "TTKOM": "Türk Telekom",
    "TUPRS": "Tüpraş",
    "VAKBN": "Vakıfbank",
    "VESTL": "Vestel",
    "YKBNK": "Yapı Kredi Bankası",
    "PETKM": "Petkim",
    "EKGYO": "Emlak Konut GYO",
    "ENKAI": "Enka İnşaat",
    "AEFES": "Anadolu Efes",
    "AGHOL": "AG Anadolu Grubu",
    "AKCNS": "Akçansa Çimento",
    "AKFGY": "Akfen GYO",
    "AKFYE": "Akfen Yenilenebilir Enerji",
    "AKGRT": "Aksigorta",
    "AKSA": "Aksa Akrilik",
    "AKSEN": "Aksa Enerji",
    "ALARK": "Alarko Holding",
    "ALBRK": "Albaraka Türk",
    "ALFAS": "Alfa Solar Enerji",
    "ASTOR": "Astor Enerji",
    "ASUZU": "Anadolu Isuzu",
    "AYGAZ": "Aygaz",
    "BAGFS": "Bagfaş",
    "BERA": "Bera Holding",
    "BIENY": "Bien Yapı",
    "BRISA": "Brisa",
    "BRSAN": "Borusan Mannesmann",
    "BRYAT": "Borusan Yatırım",
    "CCOLA": "Coca-Cola İçecek",
    "CIMSA": "Çimsa",
    "CLEBI": "Çelebi Hava Servisi",
    "DOAS": "Doğuş Otomotiv",
    "ECILC": "Eczacıbaşı İlaç",
    "EGEEN": "Ege Endüstri",
    "ENJSA": "Enerjisa Enerji",
    "GENIL": "Gen İlaç",
    "GOODY": "Goodyear",
    "GUBRF": "Gübre Fabrikaları",
    "GWIND": "Galata Wind Enerji",
    "HEKTS": "Hektaş",
    "IPEKE": "İpek Doğal Enerji",
    "ISDMR": "İskenderun Demir Çelik",
    "ISMEN": "İş Yatırım",
    "IZMDC": "İzmir Demir Çelik",
    "KAREL": "Karel Elektronik",
    "KARSN": "Karsan Otomotiv",
    "KCAER": "Karsu Tekstil",
    "KMPUR": "Kimpur",
    "KONTR": "Kontrolmatik",
    "KORDS": "Kordsa",
    "KOZAA": "Koza Madencilik",
    "LOGO": "Logo Yazılım",
    "MGROS": "Migros",
    "MPARK": "MLP Sağlık (Medikal Park)",
    "NETAS": "Netaş Telekom",
    "NUHCM": "Nuh Çimento",
    "ODAS": "Odaş Elektrik",
    "OTKAR": "Otokar",
    "OYAKC": "Oyak Çimento",
    "PAPIL": "Papilon Savunma",
    "POLHO": "Polisan Holding",
    "SDTTR": "SDT Uzay Savunma",
    "SELEC": "Selçuk Ecza",
    "SKBNK": "Şekerbank",
    "SMRTG": "Smartiks Yazılım",
    "SOKM": "Şok Marketler",
    "TKFEN": "Tekfen Holding",
    "TSKB": "TSKB",
    "TTRAK": "Türk Traktör",
    "TUKAS": "Tukaş Gıda",
    "TURSG": "Türk Sigorta",
    "ULKER": "Ülker Bisküvi",
    "YATAS": "Yataş Yatak",
    "YEOTK": "Yeo Teknoloji",
    "ZOREN": "Zorlu Enerji",
}
