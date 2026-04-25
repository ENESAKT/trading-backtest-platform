"""
Quant Engine — Veri Çekme Modülü (Fetcher)

İnternete bağlanan TEK modül. Yahoo Finance üzerinden BIST hisselerinin
geçmiş verilerini çeker. Delta fetch özelliği ile sadece eksik günleri indirir.

Kullanım:
    from quant_engine.data_pipeline.fetcher import BISTFetcher
    
    fetcher = BISTFetcher()
    df = fetcher.fetch_single("THYAO", start="2020-01-01")
    fetcher.fetch_watchlist()  # Tüm watchlist'i çek
"""

from __future__ import annotations

import datetime as dt
from typing import Optional

import pandas as pd
import yfinance as yf
from loguru import logger

from quant_engine.config.config_manager import get_config


class BISTFetcher:
    """
    Borsa İstanbul hisse verisi çekici.
    
    Yahoo Finance üzerinden OHLCV verisi indirir.
    Delta fetch: Yerel veri tabanındaki son tarihi kontrol edip,
    sadece eksik günleri çeker.
    """
    
    def __init__(self, storage_manager=None):
        """
        Args:
            storage_manager: Opsiyonel StorageManager instance'ı.
                             Delta fetch için gerekli.
        """
        self.config = get_config()
        self.suffix = self.config.data_pipeline.ticker_suffix
        self.default_start = self.config.data_pipeline.default_start_date
        self.storage = storage_manager
        
    def _to_yahoo_ticker(self, symbol: str) -> str:
        """BIST sembolünü Yahoo Finance formatına çevir. Örn: THYAO → THYAO.IS"""
        if not symbol.endswith(self.suffix):
            return f"{symbol}{self.suffix}"
        return symbol
    
    def _clean_symbol(self, yahoo_ticker: str) -> str:
        """Yahoo ticker'dan BIST sembolünü çıkar. Örn: THYAO.IS → THYAO"""
        return yahoo_ticker.replace(self.suffix, "")
    
    def fetch_single(
        self,
        symbol: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Tek bir hissenin geçmiş verisini çek.
        
        Args:
            symbol: BIST sembolü (örn: "THYAO")
            start: Başlangıç tarihi (YYYY-MM-DD). None ise config'den alınır.
            end: Bitiş tarihi. None ise bugün.
            interval: Zaman dilimi — "1d", "1h", "5m" vb.
            
        Returns:
            pd.DataFrame: OHLCV verisi — sütunlar:
                date, open, high, low, close, volume, symbol
        """
        yahoo_ticker = self._to_yahoo_ticker(symbol)
        clean_symbol = self._clean_symbol(yahoo_ticker)
        start = start or self.default_start
        end = end or dt.date.today().isoformat()
        
        logger.info(f"📥 Veri çekiliyor: {clean_symbol} | {start} → {end} | {interval}")
        
        try:
            ticker = yf.Ticker(yahoo_ticker)
            df = ticker.history(start=start, end=end, interval=interval)
            
            if df.empty:
                logger.warning(f"⚠️ {clean_symbol} için veri bulunamadı!")
                return pd.DataFrame()
            
            # Sütun isimlerini standartlaştır
            df = df.reset_index()
            df.columns = [c.lower().replace(" ", "_") for c in df.columns]
            
            # Gereksiz sütunları temizle
            keep_cols = ["date", "open", "high", "low", "close", "volume"]
            available_cols = [c for c in keep_cols if c in df.columns]
            df = df[available_cols].copy()
            
            # Sembol sütunu ekle
            df["symbol"] = clean_symbol
            
            # Tarih tipini düzenle
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
            
            # Volume tipini integer yap
            if "volume" in df.columns:
                df["volume"] = df["volume"].fillna(0).astype(int)
            
            logger.success(
                f"✅ {clean_symbol}: {len(df)} satır çekildi "
                f"({df['date'].min().strftime('%Y-%m-%d')} → "
                f"{df['date'].max().strftime('%Y-%m-%d')})"
            )
            
            return df
            
        except Exception as e:
            logger.error(f"❌ {clean_symbol} veri çekme hatası: {e}")
            return pd.DataFrame()
    
    def fetch_single_delta(self, symbol: str, interval: str = "1d") -> pd.DataFrame:
        """
        Delta fetch — sadece eksik günleri çek.
        
        Yerel veri tabanındaki en son tarihi kontrol eder,
        sadece o tarihten sonraki verileri indirir.
        
        Args:
            symbol: BIST sembolü
            interval: Zaman dilimi
            
        Returns:
            pd.DataFrame: Yeni eklenen veriler (boş olabilir)
        """
        if self.storage is None:
            logger.warning("Storage manager tanımlı değil, tam fetch yapılıyor.")
            return self.fetch_single(symbol, interval=interval)
        
        # Yerel veri tabanındaki en son tarihi bul
        last_date = self.storage.get_last_date(symbol)
        
        if last_date is None:
            logger.info(f"🆕 {symbol}: Yerel veri yok, tam indirme yapılıyor...")
            return self.fetch_single(symbol, interval=interval)
        
        # Son tarihten 1 gün sonrasından başla (tekrar çekmeyi önle)
        start_date = (last_date + dt.timedelta(days=1)).isoformat()
        today = dt.date.today().isoformat()
        
        if start_date >= today:
            logger.info(f"✔️ {symbol}: Veri güncel, güncelleme gerekmiyor.")
            return pd.DataFrame()
        
        logger.info(f"🔄 {symbol}: Delta fetch — {start_date} → {today}")
        return self.fetch_single(symbol, start=start_date, interval=interval)
    
    def fetch_watchlist(
        self,
        symbols: Optional[list[str]] = None,
        interval: str = "1d",
        delta: bool = True,
    ) -> dict[str, pd.DataFrame]:
        """
        Watchlist'teki tüm hisselerin verisini çek.
        
        Args:
            symbols: Sembol listesi. None ise config watchlist'i kullanılır.
            interval: Zaman dilimi
            delta: True ise sadece eksik günleri çeker
            
        Returns:
            dict[str, pd.DataFrame]: Sembol → DataFrame eşlemesi
        """
        symbols = symbols or self.config.symbols.watchlist
        results: dict[str, pd.DataFrame] = {}
        
        logger.info(f"📋 {len(symbols)} hisse için toplu veri çekme başlatılıyor...")
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"[{i}/{len(symbols)}] {symbol}")
            
            if delta:
                df = self.fetch_single_delta(symbol, interval=interval)
            else:
                df = self.fetch_single(symbol, interval=interval)
            
            if not df.empty:
                results[symbol] = df
        
        total_rows = sum(len(df) for df in results.values())
        logger.success(
            f"🎉 Toplu çekme tamamlandı: "
            f"{len(results)}/{len(symbols)} hisse, "
            f"toplam {total_rows:,} satır"
        )
        
        return results
    
    def fetch_bulk_yfinance(
        self,
        symbols: Optional[list[str]] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        yfinance.download ile toplu indirme (daha hızlı).
        
        Birden fazla hisseyi tek API çağrısı ile indirir.
        Not: Delta fetch desteklemez, tam indirme yapar.
        
        Args:
            symbols: Sembol listesi
            start: Başlangıç tarihi
            end: Bitiş tarihi
            interval: Zaman dilimi
            
        Returns:
            pd.DataFrame: Tüm hisselerin birleşik verisi
        """
        symbols = symbols or self.config.symbols.watchlist
        start = start or self.default_start
        end = end or dt.date.today().isoformat()
        
        yahoo_tickers = [self._to_yahoo_ticker(s) for s in symbols]
        
        logger.info(
            f"⚡ Toplu indirme: {len(symbols)} hisse | "
            f"{start} → {end} | {interval}"
        )
        
        try:
            raw = yf.download(
                tickers=yahoo_tickers,
                start=start,
                end=end,
                interval=interval,
                group_by="ticker",
                auto_adjust=True,
                threads=True,
            )
            
            if raw.empty:
                logger.warning("⚠️ Toplu indirme boş döndü!")
                return pd.DataFrame()
            
            # Multi-level column'ları düzle
            frames = []
            for ticker in yahoo_tickers:
                clean = self._clean_symbol(ticker)
                try:
                    if len(yahoo_tickers) == 1:
                        df = raw.copy()
                    else:
                        df = raw[ticker].copy()
                    
                    df = df.reset_index()
                    df.columns = [c.lower().replace(" ", "_") for c in df.columns]
                    df["symbol"] = clean
                    
                    keep = ["date", "open", "high", "low", "close", "volume", "symbol"]
                    available = [c for c in keep if c in df.columns]
                    df = df[available].dropna(subset=["close"])
                    
                    frames.append(df)
                except (KeyError, Exception) as e:
                    logger.warning(f"⚠️ {clean} parse hatası: {e}")
            
            if not frames:
                return pd.DataFrame()
            
            result = pd.concat(frames, ignore_index=True)
            logger.success(f"✅ Toplu indirme: {len(result):,} satır, {len(frames)} hisse")
            return result
            
        except Exception as e:
            logger.error(f"❌ Toplu indirme hatası: {e}")
            return pd.DataFrame()
