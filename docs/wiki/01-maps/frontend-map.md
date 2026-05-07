# Frontend Map

## Purpose

Frontend, Vite tabanlı TypeScript SPA olarak canlı piyasa, grafik, strateji,
portföy ve eğitim panellerini gösterir.

## Source Files

- `frontend/src/app.ts`
- `frontend/src/components/`
- `frontend/src/core/`
- `frontend/src/indicators/`
- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/design-reference/backtest/`

## Current Facts

- Eski klasör adı `piyasapilot-v2/`; güncel klasör `frontend/`.
- Production build komutu `cd frontend && npx vite build`.
- Docker nginx servisi `frontend/dist` çıktısını servis eder.
- Frontend dosyaları mimari taşıma sırasında içerik olarak değiştirilmemelidir.
- Enes'in yeni tasarım prototipi `frontend/design-reference/backtest/` altında
  referans olarak korunur; aktif shell bu tasarım dilinden ticker, amber vurgu,
  terminal topbar ve keskin panel stilini alır.

## Related

- [[backend-map]]
- [[../04-modules/deployment]]
