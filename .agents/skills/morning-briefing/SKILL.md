# Morning Briefing

Her sabah BIST 100 piyasa özeti ve 3 odak hisse belirle.

## Kullanım

Sabah piyasa açılmadan önce çağrılır. Teknik analiz tabanlı günlük brifing oluşturur.

## Adımlar

1. **Piyasa Tarama:** BIST 100 sembollerini tara
   ```bash
   # Son fiyat ve RSI değerlerini çek
   for symbol in THYAO.IS GARAN.IS AKBNK.IS EREGL.IS SAHOL.IS; do
     curl -sf "http://localhost:8000/api/v2/candles?symbol=$symbol&interval=15m&limit=100" | \
       python3 -c "import sys,json; d=json.load(sys.stdin); bars=d.get('bars',[]); print(f'{d[\"symbol\"]}: {bars[-1][\"close\"] if bars else \"?\"}')"
   done
   ```

2. **Tüm Stratejiler ile Sinyal Tarama:** Her BIST 30 hissesini 8 strateji üzerinde koş
   ```bash
   curl -X POST http://localhost:8000/api/backtest/run \
     -H "Content-Type: application/json" \
     -d '{"symbol":"THYAO.IS","strategy_id":"sma_crossover","lookback_bars":200}'
   ```

3. **Odak 3 Hisse Seçimi:**
   - En çok AL sinyali alan 3 hisse
   - RSI aşırı satım bölgesindeki hisseler
   - Hacim anomalisi gösteren hisseler

4. **Brifing Oluştur:**
   - Genel piyasa trendi (XU100 yönü)
   - 3 odak hisse detaylı analizi
   - Risk uyarıları

## Çıktı Formatı

```markdown
# 🌅 Sabah Brifing — [tarih]

## Piyasa Genel Görünüm
- XU100: [son fiyat] ([değişim %])
- USDTRY: [son fiyat]
- BTC: [son fiyat]
- Trend: [yükseliş/düşüş/yatay]

## 🎯 Odak 3 Hisse

### 1. THYAO.IS — Türk Hava Yolları
- Fiyat: ₺XXX | RSI: XX | Strateji konsensüsü: 6/8 AL
- [Kısa teknik yorum]

### 2. ...

## ⚠️ Risk Uyarıları
- [varsa]
```
