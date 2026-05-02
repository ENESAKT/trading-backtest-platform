# BIST/VIOP Veri Mimarisi

Bu belge `planlama-veri-platformu.md` doğrultusunda oluşturulmuş, PiyasaPilot veri mimarisinin detaylarını tanımlar.

## Temel Veri Kaynakları ve Depoları

| Katman | Veritabanı | Sorumluluk |
| --- | --- | --- |
| Tarihsel Bar Verisi | ClickHouse | OHLCV barları (raw & derived), hızlı okuma, backtest, screener |
| Operasyonel Metadata | MySQL | Semboller, sözleşmeler (VIOP), ingestion logları, inventory ve provider durumları |
| Sıcak Cache / PubSub | Redis | Canlı veri feed'i, yayın, lock yönetimi, WS son fiyat bellek erişimi |
| Lokal Fallback | Parquet / SQLite | Geliştirme, kısa okumalar ve yedekleme (eski yapıdan bırakıldı) |

## Saklama (Retention) ve Zaman Dilimleri (Timeframes)

- **BIST Hisse Dakikalık (`1m`):** Yalnızca son 1 yıl. Diskte gereksiz yük olmasını önlemek içindir.
- **BIST Hisse Diğer Zaman Dilimleri (`5m`, `15m`...):** Maksimum 10 yıl. `1m` verisinden veya provider'dan türetilebilir.
- **VIOP Dakikalık (`1m`):** Maksimum 10 yıl saklanır (öncelikli ve önemli olduğu için).
- **Kurallar:** 
  - Kesinlikle günlük (`1d`) veriden dakikalık (`1m`) sahte veri üretilmez. 
  - Sadece düşük zaman dilimlerinden yüksek zaman dilimleri türetilir (Örn `1m -> 5m -> 15m`).
  - Uygulama, kaynak (source) ve türetilmiş (derived) verileri birbirinden net şekilde ayırır.

## Dependency Graph Temsili

Türetme akışı: `1m -> 5m -> 15m -> 30m -> 1h -> 4h -> 1d -> 1w -> 1mo -> 1y`

## ClickHouse Schema Özeti
Ana bar deposu `market_bars` tablosu şöyledir:
- Partitioning: `market, timeframe, toYYYYMM(ts)`
- Sıralama: `ORDER BY (market, symbol, timeframe, ts)`
Bu yapı sayesinde retention politikaları partition bazlı yürütülebilir ve ay düzeyinde temizlik yapılabilir.

Bu dosya yeni eklentilerle birlikte güncellenecektir.