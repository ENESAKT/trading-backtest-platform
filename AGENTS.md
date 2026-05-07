# Agent Rehberi

CLAUDE.md kuralları burada da geçerlidir.

## Router Kuralı
Gelen istek kategorisi:
- `backtest` → strateji çalıştırma, parametre optimizasyonu → agents/backtest.md
- `data`     → veri çekme, temizleme, provider → agents/data.md
- `risk`     → drawdown, VaR, pozisyon boyutu → agents/risk.md
- `report`   → sonuç birleştirme, özet → agents/report.md
- `general`  → yukarıdakilere girmeyen → sadece CLAUDE.md ile devam

## Routing Kuralları
1. Router olarak Haiku kullan, Sonnet değil.
2. Her agent yalnızca kendi agents/X.md dosyasını okur.
3. Agent'lar birbirini doğrudan çağırmaz. Router yönlendirir.
4. Çıktı tam context değil, kısa özet olarak iletilir.
