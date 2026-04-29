# Validate Spike Filter

Cache pipeline'a gelen veride IQR spike filtresi testi koş.

## Kullanım

Bu skill, yeni sembol eklendiğinde veya spike filter parametreleri değiştiğinde çağrılır.

## Adımlar

1. `backend/data/spike_filter.py` modülünü oku — `filter_bars()` fonksiyonu
2. Test verisi hazırla:
   ```python
   from backend.data.spike_filter import filter_bars
   
   # Normal veri
   bars = [{"time": i, "open": 100+i*0.1, "high": 101+i*0.1, "low": 99+i*0.1, "close": 100.5+i*0.1, "volume": 1000} for i in range(50)]
   
   # Yapay spike inject
   bars[25]["high"] = 500  # Anormal spike
   bars[25]["close"] = 450
   
   cleaned, report = filter_bars(bars)
   ```
3. Doğrulama:
   - `report.winsorized > 0` → spike tespit edildi
   - Temizlenmiş barlar IQR sınırları içinde
   - Yüksek hacimli gerçek sıçramalar korunmuş (`report.untouched_high_volume`)

## Referanslar

- Kod: `backend/data/spike_filter.py`
- Testler: `tests/unit/test_spike_filter.py`
- Mimari karar: Silme yerine Winsorize (ogrenilenler.md)
