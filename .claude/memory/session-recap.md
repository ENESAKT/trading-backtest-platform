# Session Recap — 2026-05-12

## Son Commit'ler
```
676364c feat: haber KAP kaynağı, okundu işareti, fiyat uyarısı, CSV export, favicon
227c0ed fix: Olaylar/Raporlar sekmeleri ve çapraz panel senkronizasyonu
d78fe24 fix: Mali Analiz başlık/race-condition, arama flash, grafik spinner, strateji toast
```

## YAPILACAKLAR.md — Tamamlananlar
- ✅ BTCUSDT başlık takılma (universe-gated loadData)
- ✅ "Sonuç yok" flash (_universeLoaded guard)
- ✅ "Veri çekilemedi" asılı kalma (keyRatios check)
- ✅ Grafik siyah ekran (chart-spin spinner CSS)
- ✅ Backtest toast + loading (StrategyPanel)
- ✅ Olaylar (Events) tab çalışmıyor + dedup
- ✅ Raporlar (Reports) boş sayfa — API format fix
- ✅ Çapraz panel senkronizasyonu (openSymbol → maliAnalizPanel.loadData)
- ✅ Haberler boş — borsapy KAP kaynağı + is_read/mark_read
- ✅ Fiyat uyarısı modal (ChartPanel)
- ✅ İşlem geçmişi CSV export (PortfolioPanel)
- ✅ Favicon 404 giderildi

## Kalan / Düşük Öncelik
- Telegram setup wizard (UI sihirbazı)
