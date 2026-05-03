# BIST/VIOP Veri Kataloğu ve Envanter Raporu

> *Bu tablo, veri sağlığı ve eksikliklerin izlenmesi için rutin scriptler tarafından güncellenmektedir.*
> *Son Güncelleme: Henüz veri dolum yapılmadı.*

| Sembol      | Market | TF  | Satır  | İlk Tarih  | Son Tarih  | Hedef | Kapsam | Boyut | Durum              |
|-------------|--------|-----|--------|------------|------------|-------|--------|-------|--------------------|
| Örn: THYAO  | BIST   | 1m  | -      | -          | -          | 1Y    | 0%     | 0 MB  | not_configured     |
| Örn: THYAO  | BIST   | 15m | -      | -          | -          | 10Y   | 0%     | 0 MB  | not_configured     |
| Örn: THYAO  | BIST   | 1d  | -      | -          | -          | 10Y   | 0%     | 0 MB  | not_configured     |
| Örn: F_XU030| VIOP   | 1m  | -      | -          | -          | 10Y   | 0%     | 0 MB  | not_configured     |

## Durum Tanımları

- **raw_available:** Provider tarafından orijinal kaynağından çekildi.
- **derived_available:** Daha küçük timeframelerden türetilerek oluşturuldu.
- **partial:** Hedef tarih aralığı tamamen dolmadı veya veri eksik.
- **missing:** Veri hiç yok.
- **provider_limit:** Veri sağlayıcı limitleri nedeniyle yeterli tarih çekilemiyor.
- **license_required:** Veriyi elde etmek için özel lisans şart.
- **not_configured:** İşlemler henüz başlamadı.
- **provider_failed:** Sağlayıcı hata veriyor.
- **retention_trimmed:** Politika gereği (örn. 1 yıllık 1m verisi) yaşlanan veriler silindi.

## Çalıştırılacak Komutlar (Tanımlanıyor)
- `make data-inventory`
- `make data-inventory-symbol SYMBOL=THYAO`
- `make data-size-report`
- `make data-gaps`
- `make derive-timeframes`
- `make retention-cleanup`
- `make backfill-bist100`
- `make backfill-viop`
