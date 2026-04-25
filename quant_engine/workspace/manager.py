"""
Quant Engine — Trading Terminali Çalışma Alanı Yöneticisi.

Her sembol için bağımsız bir workspace config üretir. Bu katman gerçek dışı veri
üretmez; veri sağlayıcı bağlanamazsa frontend'e bekleme/hata protokolü verir.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from quant_engine.core.protocols import Market, Timeframe


@dataclass(frozen=True)
class InstrumentSpec:
    symbol_code: str
    full_name: str
    market_category: str
    market: Market
    yahoo_ticker: str
    precision: int
    supports_volume: bool = True
    supports_depth: bool = False


@dataclass(frozen=True)
class WorkspaceRequest:
    symbol_id: str
    market_type: str
    timeframe_label: str


@dataclass(frozen=True)
class WorkspaceResolution:
    workspace_id: str
    instrument: InstrumentSpec
    timeframe: Timeframe
    timeframe_label: str
    valid: bool
    warning: str = ""


BIST30_CORE_SYMBOLS: tuple[str, ...] = (
    "AKBNK",
    "ALARK",
    "ASELS",
    "ASTOR",
    "BIMAS",
    "BRSAN",
    "DOAS",
    "EKGYO",
    "ENKAI",
    "EREGL",
    "FROTO",
    "GARAN",
    "GUBRF",
    "HEKTS",
    "ISCTR",
    "KCHOL",
    "KONTR",
    "KRDMD",
    "OYAKC",
    "PETKM",
    "PGSUS",
    "SAHOL",
    "SASA",
    "SISE",
    "TCELL",
    "THYAO",
    "TOASO",
    "TRALT",
    "TUPRS",
    "YKBNK",
)


BIST_INSTRUMENTS: dict[str, str] = {
    "A1CAP": "A1 Capital Yatırım Menkul Değerler A.Ş.",
    "ADEL": "Adel Kalemcilik Ticaret ve Sanayi A.Ş.",
    "AEFES": "Anadolu Efes Biracılık ve Malt Sanayii A.Ş.",
    "AGESA": "AgeSA Hayat ve Emeklilik A.Ş.",
    "AGHOL": "AG Anadolu Grubu Holding A.Ş.",
    "AHGAZ": "Ahlatcı Doğal Gaz Dağıtım Enerji ve Yatırım A.Ş.",
    "AKBNK": "Akbank T.A.Ş.",
    "AKCNS": "Akçansa Çimento Sanayi ve Ticaret A.Ş.",
    "AKFGY": "Akfen Gayrimenkul Yatırım Ortaklığı A.Ş.",
    "AKFYE": "Akfen Yenilenebilir Enerji A.Ş.",
    "AKGRT": "Aksigorta A.Ş.",
    "AKSA": "Aksa Akrilik Kimya Sanayii A.Ş.",
    "AKSEN": "Aksa Enerji Üretim A.Ş.",
    "ALARK": "Alarko Holding A.Ş.",
    "ALBRK": "Albaraka Türk Katılım Bankası A.Ş.",
    "ALFAS": "Alfa Solar Enerji Sanayi ve Ticaret A.Ş.",
    "ANHYT": "Anadolu Hayat Emeklilik A.Ş.",
    "ANSGR": "Anadolu Anonim Türk Sigorta Şirketi",
    "ARASE": "Doğu Aras Enerji Yatırımları A.Ş.",
    "ARCLK": "Arçelik A.Ş.",
    "ARDYZ": "ARD Grup Bilişim Teknolojileri A.Ş.",
    "ASELS": "Aselsan Elektronik Sanayi ve Ticaret A.Ş.",
    "ASTOR": "Astor Enerji A.Ş.",
    "ASUZU": "Anadolu Isuzu Otomotiv Sanayi ve Ticaret A.Ş.",
    "AYDEM": "Aydem Yenilenebilir Enerji A.Ş.",
    "AYGAZ": "Aygaz A.Ş.",
    "BASGZ": "Başkent Doğalgaz Dağıtım GYO A.Ş.",
    "BERA": "Bera Holding A.Ş.",
    "BFREN": "Bosch Fren Sistemleri Sanayi ve Ticaret A.Ş.",
    "BIMAS": "BİM Birleşik Mağazalar A.Ş.",
    "BIOEN": "Biotrend Çevre ve Enerji Yatırımları A.Ş.",
    "BRISA": "Brisa Bridgestone Sabancı Lastik Sanayi ve Ticaret A.Ş.",
    "BRSAN": "Borusan Birleşik Boru Fabrikaları Sanayi ve Ticaret A.Ş.",
    "BRYAT": "Borusan Yatırım ve Pazarlama A.Ş.",
    "BSOKE": "Batısöke Söke Çimento Sanayii T.A.Ş.",
    "BTCIM": "Batıçim Batı Anadolu Çimento Sanayii A.Ş.",
    "CANTE": "Çan2 Termik A.Ş.",
    "CCOLA": "Coca-Cola İçecek A.Ş.",
    "CIMSA": "Çimsa Çimento Sanayi ve Ticaret A.Ş.",
    "CLEBI": "Çelebi Hava Servisi A.Ş.",
    "CWENE": "CW Enerji Mühendislik Ticaret ve Sanayi A.Ş.",
    "DEVA": "Deva Holding A.Ş.",
    "DOAS": "Doğuş Otomotiv Servis ve Ticaret A.Ş.",
    "DOCO": "DO & CO Aktiengesellschaft",
    "DOHOL": "Doğan Şirketler Grubu Holding A.Ş.",
    "ECILC": "EİS Eczacıbaşı İlaç, Sınai ve Finansal Yatırımlar A.Ş.",
    "ECZYT": "Eczacıbaşı Yatırım Holding Ortaklığı A.Ş.",
    "EGEEN": "Ege Endüstri ve Ticaret A.Ş.",
    "EKGYO": "Emlak Konut Gayrimenkul Yatırım Ortaklığı A.Ş.",
    "ENERY": "Enerya Enerji A.Ş.",
    "ENJSA": "Enerjisa Enerji A.Ş.",
    "ENKAI": "Enka İnşaat ve Sanayi A.Ş.",
    "EREGL": "Ereğli Demir ve Çelik Fabrikaları T.A.Ş.",
    "EUPWR": "Europower Enerji ve Otomasyon Teknolojileri Sanayi Ticaret A.Ş.",
    "FROTO": "Ford Otomotiv Sanayi A.Ş.",
    "GARAN": "Türkiye Garanti Bankası A.Ş.",
    "GESAN": "Girişim Elektrik Sanayi Taahhüt ve Ticaret A.Ş.",
    "GLYHO": "Global Yatırım Holding A.Ş.",
    "GUBRF": "Gübre Fabrikaları T.A.Ş.",
    "GWIND": "Galata Wind Enerji A.Ş.",
    "HALKB": "Türkiye Halk Bankası A.Ş.",
    "HEKTS": "Hektaş Ticaret T.A.Ş.",
    "ISCTR": "Türkiye İş Bankası A.Ş. C",
    "ISDMR": "İskenderun Demir ve Çelik A.Ş.",
    "ISFIN": "İş Finansal Kiralama A.Ş.",
    "ISGYO": "İş Gayrimenkul Yatırım Ortaklığı A.Ş.",
    "ISMEN": "İş Yatırım Menkul Değerler A.Ş.",
    "IZENR": "İzdemir Enerji Elektrik Üretim A.Ş.",
    "IZMDC": "İzmir Demir Çelik Sanayi A.Ş.",
    "KARSN": "Karsan Otomotiv Sanayii ve Ticaret A.Ş.",
    "KCAER": "Kocaer Çelik Sanayi ve Ticaret A.Ş.",
    "KCHOL": "Koç Holding A.Ş.",
    "KLSER": "Kaleseramik Çanakkale Kalebodur Seramik Sanayi A.Ş.",
    "KONTR": "Kontrolmatik Teknoloji Enerji ve Mühendislik A.Ş.",
    "KONYA": "Konya Çimento Sanayii A.Ş.",
    "KORDS": "Kordsa Teknik Tekstil A.Ş.",
    "KOZAA": "Koza Anadolu Metal Madencilik İşletmeleri A.Ş.",
    "KOZAL": "Koza Altın İşletmeleri A.Ş.",
    "KRDMA": "Kardemir Karabük Demir Çelik Sanayi ve Ticaret A.Ş. A",
    "KRDMB": "Kardemir Karabük Demir Çelik Sanayi ve Ticaret A.Ş. B",
    "KRDMD": "Kardemir Karabük Demir Çelik Sanayi ve Ticaret A.Ş. D",
    "KZBGY": "Kızılbük Gayrimenkul Yatırım Ortaklığı A.Ş.",
    "LOGO": "Logo Yazılım Sanayi ve Ticaret A.Ş.",
    "MAVI": "Mavi Giyim Sanayi ve Ticaret A.Ş.",
    "MGROS": "Migros Ticaret A.Ş.",
    "MIATK": "MİA Teknoloji A.Ş.",
    "MPARK": "MLP Sağlık Hizmetleri A.Ş.",
    "ODAS": "Odaş Elektrik Üretim Sanayi Ticaret A.Ş.",
    "OTKAR": "Otokar Otomotiv ve Savunma Sanayi A.Ş.",
    "OYAKC": "OYAK Çimento Fabrikaları A.Ş.",
    "PASEU": "Pasifik Eurasia Lojistik Dış Ticaret A.Ş.",
    "PETKM": "Petkim Petrokimya Holding A.Ş.",
    "PGSUS": "Pegasus Hava Taşımacılığı A.Ş.",
    "QUAGR": "QUA Granite Hayal Yapı ve Ürünleri Sanayi Ticaret A.Ş.",
    "SAHOL": "Hacı Ömer Sabancı Holding A.Ş.",
    "SASA": "SASA Polyester Sanayi A.Ş.",
    "SELEC": "Selçuk Ecza Deposu Ticaret ve Sanayi A.Ş.",
    "SISE": "Türkiye Şişe ve Cam Fabrikaları A.Ş.",
    "SKBNK": "Şekerbank T.A.Ş.",
    "SMRTG": "Smart Güneş Enerjisi Teknolojileri A.Ş.",
    "SOKM": "Şok Marketler Ticaret A.Ş.",
    "TABGD": "Tab Gıda Sanayi ve Ticaret A.Ş.",
    "TAVHL": "TAV Havalimanları Holding A.Ş.",
    "TCELL": "Turkcell İletişim Hizmetleri A.Ş.",
    "THYAO": "Türk Hava Yolları A.O.",
    "TKFEN": "Tekfen Holding A.Ş.",
    "TOASO": "Tofaş Türk Otomobil Fabrikası A.Ş.",
    "TRALT": "Türk Altın İşletmeleri A.Ş.",
    "TRGYO": "Torunlar Gayrimenkul Yatırım Ortaklığı A.Ş.",
    "TSKB": "Türkiye Sınai Kalkınma Bankası A.Ş.",
    "TTKOM": "Türk Telekomünikasyon A.Ş.",
    "TTRAK": "Türk Traktör ve Ziraat Makineleri A.Ş.",
    "TUPRS": "Tüpraş Türkiye Petrol Rafinerileri A.Ş.",
    "TURSG": "Türkiye Sigorta A.Ş.",
    "ULKER": "Ülker Bisküvi Sanayi A.Ş.",
    "VAKBN": "Türkiye Vakıflar Bankası T.A.O.",
    "VESTL": "Vestel Elektronik Sanayi ve Ticaret A.Ş.",
    "VESBE": "Vestel Beyaz Eşya Sanayi ve Ticaret A.Ş.",
    "YEOTK": "YEO Teknoloji Enerji ve Endüstri A.Ş.",
    "YKBNK": "Yapı ve Kredi Bankası A.Ş.",
    "ZOREN": "Zorlu Enerji Elektrik Üretim A.Ş.",
}

BIST30_INSTRUMENTS: dict[str, str] = {
    symbol: BIST_INSTRUMENTS[symbol]
    for symbol in BIST30_CORE_SYMBOLS
    if symbol in BIST_INSTRUMENTS
}

BIST_WIDE_INSTRUMENTS: dict[str, str] = dict(sorted(BIST_INSTRUMENTS.items()))

FOREX_INSTRUMENTS: dict[str, str] = {
    "USDTRY": "Amerikan Doları / Türk Lirası",
    "EURTRY": "Euro / Türk Lirası",
    "GBPTRY": "İngiliz Sterlini / Türk Lirası",
    "EURUSD": "Euro / Amerikan Doları",
    "GBPUSD": "İngiliz Sterlini / Amerikan Doları",
    "USDJPY": "Amerikan Doları / Japon Yeni",
}

COMMODITY_INSTRUMENTS: dict[str, tuple[str, str]] = {
    "XAUUSD": ("Altın Ons / ABD Doları", "GC=F"),
    "XAGUSD": ("Gümüş Ons / ABD Doları", "SI=F"),
    "BRENT": ("Brent Petrol Vadeli", "BZ=F"),
    "WTI": ("WTI Ham Petrol Vadeli", "CL=F"),
    "NGAS": ("Doğal Gaz Vadeli", "NG=F"),
}

TIMEFRAME_LABELS: dict[str, Timeframe] = {
    "1D": Timeframe.M1,
    "5D": Timeframe.M5,
    "15D": Timeframe.M15,
    "30D": Timeframe.M30,
    "1S": Timeframe.H1,
    "4S": Timeframe.H4,
    "1G": Timeframe.D1,
    "1H": Timeframe.W1,
    "1A": Timeframe.MO1,
}


def normalize_symbol(symbol_id: str) -> str:
    """Kullanıcı sembolünü kanonik forma getir."""
    return symbol_id.upper().strip().replace(" ", "").replace("/", "").replace(".IS", "")


def normalize_market_type(market_type: str) -> str:
    return market_type.upper().replace("İ", "I").replace(" ", "")


def precision_for(symbol: str, market: Market) -> int:
    """Piyasa tipine göre fiyat hassasiyeti."""
    if market == Market.BIST:
        return 2
    if market == Market.COMMODITY:
        return 2 if symbol in {"XAUUSD", "XAGUSD", "BRENT", "WTI", "NGAS"} else 4
    if symbol.endswith("JPY"):
        return 3
    if symbol.endswith("TRY"):
        return 4
    return 5


def resolve_instrument(symbol_id: str, market_type: str) -> InstrumentSpec:
    """Sembol ve piyasa tipini veri sağlayıcıya uygun varlık tanımına çevir."""
    symbol = normalize_symbol(symbol_id)
    market_key = normalize_market_type(market_type)

    if market_key.startswith("FOREX") or market_key in {"DOVIZ", "FX"}:
        name = FOREX_INSTRUMENTS.get(symbol, f"{symbol} Döviz Paritesi")
        return InstrumentSpec(
            symbol_code=symbol,
            full_name=name,
            market_category="Forex / Fiat Döviz",
            market=Market.FOREX,
            yahoo_ticker=f"{symbol}=X",
            precision=precision_for(symbol, Market.FOREX),
            supports_volume=False,
        )

    if market_key.startswith("EMTIA") or market_key.startswith("COMMODITY"):
        name, ticker = COMMODITY_INSTRUMENTS.get(symbol, (f"{symbol} Emtia", symbol))
        return InstrumentSpec(
            symbol_code=symbol,
            full_name=name,
            market_category="Emtia / Vadeli veya Spot",
            market=Market.COMMODITY,
            yahoo_ticker=ticker,
            precision=precision_for(symbol, Market.COMMODITY),
            supports_volume=True,
        )

    category = "BIST Tüm / Hisse Senedi"
    if "30" in market_key:
        category = "BIST 30 / Hisse Senedi"
    elif "100" in market_key:
        category = "BIST 100 / Hisse Senedi"
    return InstrumentSpec(
        symbol_code=symbol,
        full_name=BIST_INSTRUMENTS.get(symbol, f"{symbol} BIST Hisse Senedi"),
        market_category=category,
        market=Market.BIST,
        yahoo_ticker=f"{symbol}.IS",
        precision=2,
        supports_volume=True,
    )


def resolve_timeframe(label: str) -> Timeframe:
    key = label.upper().replace(" ", "")
    return TIMEFRAME_LABELS.get(key, Timeframe.D1)


def workspace_id_for(symbol: str, market_type: str, timeframe_label: str) -> str:
    raw = f"{normalize_market_type(market_type)}:{normalize_symbol(symbol)}:{timeframe_label}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
    return f"ws_{digest}"


def resolve_workspace(request: WorkspaceRequest) -> WorkspaceResolution:
    instrument = resolve_instrument(request.symbol_id, request.market_type)
    timeframe = resolve_timeframe(request.timeframe_label)
    workspace_id = workspace_id_for(
        instrument.symbol_code,
        request.market_type,
        request.timeframe_label,
    )
    warning = ""
    valid = True
    if instrument.market != Market.BIST and instrument.symbol_code not in {
        *FOREX_INSTRUMENTS,
        *COMMODITY_INSTRUMENTS,
    }:
        valid = False
        warning = "Geçerli piyasa veri sağlayıcı eşlemesi bulunamadı."
    return WorkspaceResolution(
        workspace_id=workspace_id,
        instrument=instrument,
        timeframe=timeframe,
        timeframe_label=request.timeframe_label,
        valid=valid,
        warning=warning,
    )


def build_workspace_config(resolution: WorkspaceResolution) -> dict[str, Any]:
    """Frontend/backend için istenen JSON konfigürasyonunu üret."""
    instrument = resolution.instrument
    data_text = "Gerçek Zamanlı OHLCV (Açılış, Yüksek, Düşük, Kapanış, Hacim)"
    if not instrument.supports_volume:
        data_text = (
            "Gerçek Zamanlı OHLC (Forex hacmi desteklenmiyorsa hacim paneli "
            "beklemeye alınır)"
        )

    warning = (
        resolution.warning
        or "Veri akışı kesilirse veya API yanıt vermezse grafiği dondur ve kullanıcıya "
        "'Bağlantı Koptu - Gerçek Veri Bekleniyor' uyarısı göster. KESİNLİKLE "
        "geçmiş veriyi kopyalayarak sahte mum üretme."
    )

    side_panel = (
        "Sembole ait anlık Alış/Satış (Bid/Ask) tahtasını derinlik verisi varsa göster; "
        "derinlik yoksa günün en düşük/yüksek, son fiyat ve veri zamanı özetini göster."
    )
    if instrument.market == Market.FOREX:
        side_panel = (
            "Forex için bid/ask ve spread önceliklidir; hacim desteklenmiyorsa hacim yerine "
            "gün içi en düşük/yüksek ve son veri zamanı göster."
        )

    return {
        "calisma_alani_kurulumu": {
            "sembol_kodu": instrument.symbol_code,
            "tam_isim": instrument.full_name,
            "piyasa_kategorisi": instrument.market_category,
            "ondalik_hassasiyet": instrument.precision,
        },
        "veri_baglanti_protokolu": {
            "talep_edilen_veri": data_text,
            "hata_yonetimi": warning,
        },
        "arayuz_bilesenleri": {
            "ana_grafik": (
                "TradingView Lightweight Charts modülünü başlat ve "
                f"'{instrument.symbol_code}' sembolüyle bağla. Workspace izolasyonu: "
                f"{resolution.workspace_id}."
            ),
            "sag_panel": side_panel,
            "strateji_durumu": (
                "Bu sembol ve workspace için önceden kaydedilmiş aktif bot/strateji varsa "
                f"yalnızca {resolution.workspace_id} anahtarı altında yükle."
            ),
        },
    }


def workspace_warning_text(resolution: WorkspaceResolution) -> str:
    if resolution.valid:
        return ""
    return resolution.warning or "Geçerli Piyasa Verisi Bulunamadı"
