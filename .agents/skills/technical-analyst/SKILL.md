# Technical Analyst

> Adapted from tradermonty/Codex-trading-skills

Teknik analiz tabanlı piyasa yorumu ve sinyal üret.

## Analiz Katmanları

1. **Trend Analizi:**
   - EMA(20/50/200) yön ve çakışma durumu
   - ADX trend gücü (>25 trend, <20 range)
   - Ichimoku Cloud (opsiyonel)

2. **Momentum:**
   - RSI(14): aşırı alım (>70), aşırı satım (<30), diverjans
   - MACD: sinyal çizgisi kesişimi, histogram trendi
   - Stochastic: %K/%D çakışması

3. **Volatilite:**
   - Bollinger Bandwidth: sıkışma (düşük → kırılım beklentisi)
   - ATR(14): volatilite seviyesi, stop-loss mesafesi
   - Keltner Channel squeeze

4. **Hacim:**
   - Hacim ortalaması karşılaştırması
   - OBV (On-Balance Volume) trendi
   - Hacim spike'ları

## PiyasaPilot İndikatörleri

Mevcut: EMA, SMA, RSI, MACD, BB, ATR, VWAP, Stochastic
Konum: `piyasapilot-v2/src/indicators/`

## Çıktı

Her sembol için: trend yönü, momentum durumu, volatilite seviyesi, hacim profili, genel yorum.
