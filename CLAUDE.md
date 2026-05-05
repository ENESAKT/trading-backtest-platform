# Backtest + PiyasaPilot - Claude Calisma Rehberi

> Bu dosya yeni Claude Code oturumunda otomatik yuklenir. Varsayilan mod
> guvenlidir: once plan, sonra kullanici onayi, sonra sinirli uygulama.

## Proje Ozeti

`/Users/enes/AgentWorkspace/Backtest` Python backend (`quant_engine/`,
`backend/`) ve TypeScript/Vite SPA (`piyasapilot-v2/`) iceren trading terminali
reposudur.

## Language and Reuse Memory

- Internal agent instructions, reusable skill docs, and reusable error/solution
  entries are written in English.
- User-facing chat with Enes must be Turkish unless Enes explicitly asks for
  another language.
- For local video content reading, use
  `/Users/enes/.codex/skills/local-video-content-reader`.
- Before debugging a recurring or specific error, search
  `/Users/enes/.codex/skills/solution-history/references/solution-log.md`.
- If a new reusable fix is discovered and verified, append an English entry to
  that solution log.
- Do not record secrets, tokens, private credentials, or huge logs in solution
  history.

Aktif servisler:

- FastAPI gateway: `backend/api/main.py`, yerelde port 8000.
- Frontend: `piyasapilot-v2`, yerelde port 5173.
- Backtest motoru: `quant_engine/backtest/engine.py`.
- Sinyal pipeline: `backend/api/signal_bus.py`, `backend/signals/generator.py`,
  `/ws/signals`.

## Guvenli Varsayilanlar

1. Sonnet kullan. Opus ve xhigh yalnizca Enes acikca isterse kullanilir.
2. Once en fazla 3 ilgili dosya oku ve kisa plan yaz.
3. Kod yazmadan, test/build calistirmadan, commit/PR/push/merge yapmadan once
   Enes'ten acik onay al.
4. Otomatik ilerleme, otomatik PR, otomatik merge ve auto-merge yok.
5. Uzun sureli shell, watcher, dev server, package install ve full test suite
   onaysiz calistirilmaz.
6. Yalnizca is icin gerekli dosyalari oku. Buyuk klasor ve dosyalardan uzak dur:
   `node_modules`, `.git`, `dist`, `build`, `.next`, `venv`, `.venv`,
   `__pycache__`, `vendor`, `.pytest_cache`, SQLite/DB dosyalari, lock dosyalari.
7. Mevcut kullanici degisikliklerini geri alma. Dirty worktree varsa once durumu
   raporla.

## Yeni Oturum Baslangici

Varsayilan ilk adimlar:

1. `git status --short --branch` ile calisma durumunu ozetle.
2. Kullanici istegine gore en fazla 3 dosya sec ve nedenini yaz.
3. Plan ver; uygulama icin onay bekle.

`docs/planning/planlama.md`, `docs/planning/genelplanlama.md` ve diger alt plan
dosyalari yalnizca gerekli oldugunda okunur. Her oturumda otomatik olarak buyuk
plan dosyalari okunmaz. Aktif referans: `YAPILANLAR.md` (envanter) ve
`YAPILACAKLAR.md` (kalan isler + guvenlik + deploy).

## Test ve Build Politikasi

Test/build komutlari referans amaclidir; otomatik calistirilmaz:

- Python hedefli test: `python -m pytest <hedef-test> -q`
- Python full suite: `python -m pytest tests/ -q`
- TS typecheck: `cd piyasapilot-v2 && npm run typecheck`
- Frontend build: `cd piyasapilot-v2 && npm run build`

Full suite, build, dev server ve watcher icin Enes'ten ayrica onay al.

## Git ve PR Politikasi

- Commit, push, PR acma, merge ve auto-merge icin her seferinde acik onay gerekir.
- `git reset`, `git checkout`, `git clean`, force push ve destructive islemler
  onaysiz kullanilmaz.
- PR body ve commit mesaji hazirlanabilir, ancak Enes onaylamadan uygulanmaz.

## Claude Ekosistemi Politikasi

- Agent, skill, hook, MCP ve slash command kurulumlari varsayilan olarak kapali
  dusunulur.
- Yeni agent/skill/hook/MCP eklenirse minimum yetkiyle, Sonnet/Haiku seviyesinde
  ve otomatik test/commit/PR/merge yapmayacak sekilde tasarlanir.
- `SessionStart`, `UserPromptSubmit`, `PostToolUse`, `Stop`, `SubagentStop`
  hook'lari onaysiz aktif edilmez.

## Dokunma Listesi

Bu dosyalara degismeden once ekstra dikkat et ve kapsam disi refaktor yapma:

- `quant_engine/backtest/engine.py`
- `quant_engine/data/providers/binance_provider.py`
- `quant_engine/data/providers/yfinance_provider.py`
- `quant_engine/data/live_feed.py`
