# Backtest — Claude Çalışma Rehberi

## Proje
`/Users/enes/AgentWorkspace/Backtest` — Python backend + TypeScript/Vite SPA.
- FastAPI: `backend/api/main.py` port 8000
- Frontend: `frontend/` port 5173
- Backtest: `quant_engine/backtest/engine.py`
- Sinyal: `backend/signals/signal_bus.py` → `/ws/signals`

## Dil Kuralı
Agent talimatları İngilizce. Enes ile sohbet Türkçe.

## Güvenli Varsayılanlar
- Model: Sonnet. Opus/xhigh yalnızca Enes isterse.
- İlk adım: `git status --short --branch` → max 3 dosya oku → plan yaz → onay al.
- Kod yazma, test/build, push/PR/merge için açık onay şart.
- Commit otomatiktir (aşağıdaki "Otonom Commit Kuralı" bölümüne bak).
- Otomatik ilerleme, auto-merge yok.
- Okuma yasağı: `node_modules .git dist build .next venv __pycache__ vendor .pytest_cache`

## Dokunma Listesi
- `quant_engine/backtest/engine.py`
- `quant_engine/data/providers/binance_provider.py`
- `quant_engine/data/providers/yfinance_provider.py`
- `quant_engine/data/live_feed.py`

## Paylaşılan Hafıza
- Solution log: `/Users/enes/.codex/skills/solution-history/references/solution-log.md`
- Hata ayıklamadan önce log'u ara. Yeni çözüm bulunursa İngilizce ekle.
- Gizli bilgi, token, büyük log kaydetme.

## Test Komutları (onaysız çalıştırma)
- `python -m pytest <hedef> -q`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`

## Otonom Commit Kuralı
Her mantıksal iş birimi tamamlandığında (özellik ekleme, hata düzeltme, refactor, doküman güncelleme vb.) **onay beklemeden** otonom olarak:
1. `git add .` ile tüm değişiklikleri sahneye al.
2. `git commit -m "<prefix>: <Türkçe açıklama>"` ile commit at.
   - Prefix örnekleri: `feat`, `fix`, `chore`, `refactor`, `docs`, `test`
   - Açıklama Türkçe ve anlaşılır olmalı.
3. **Push yapmadan** dur — push için açık onay gerekir.
4. Cevabının sonuna kısa not düş: "✅ Commit edildi."
