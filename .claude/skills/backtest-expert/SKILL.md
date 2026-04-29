# Backtest Expert

> Adapted from tradermonty/claude-trading-skills

Backtest sonuçlarını uzman olarak analiz et ve yorumla.

## Yetkinlik

- Equity curve şekil analizi (uptrend, drawdown dönemleri, platolar)
- Risk-adjusted return metrikleri (Sharpe, Sortino, Calmar)
- Trade dağılımı analizi (win streak, loss streak, trade süresi)
- Overfitting sinyalleri tespit et (in-sample vs out-of-sample)
- Walk-forward optimizasyon önerileri

## Analiz Çerçevesi

1. **Temel Metrikler:** Total return, max DD, win rate, profit factor
2. **İleri Düzey:** Sharpe ratio, MAR ratio, recovery factor
3. **Dağılım:** Trade PnL histogram, kazanan/kaybeden ortalama büyüklük
4. **Robustness:** Farklı piyasa rejimlerinde performans
5. **Uyarılar:** Curve fitting, data snooping, survivorship bias riskleri

## PiyasaPilot Entegrasyonu

- API: `POST /api/backtest/run` → sonuçlar `metrics`, `equity_curve`, `trades`, `signals`
- Blueprint'ler: `GET /api/backtest/strategies`
- Cache: `backend/data/cache.py` → OHLCVCache
