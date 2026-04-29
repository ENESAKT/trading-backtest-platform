# Skills

Bu klasor projeye ozel skill'ler icindir. Su an aktif skill yoktur.

Guvenli varsayilan:

- Skill'ler otomatik preload edilmez.
- Skill body kisa tutulur; buyuk referans dosyalari context'e otomatik
  yuklenmez.
- `Bash`, test, build, WebSearch ve external API kullanimi acik onay gerektirir.
- Skill commit, push, PR, merge veya auto-merge yapmaz.
- Trading/news skill'leri genis web aramasi yapmadan once kapsam sorar.

## Frontmatter sablonu

```yaml
---
name: skill-adi
description: Dar kapsamli tetikleme aciklamasi.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob
model: inherit
---
```

`disable-model-invocation: true` tercih edilir; boylece skill otomatik degil,
kullanici istegiyle kullanilir.

## Ertelenen sprint fikri

Eski plan 15 skill oneriyordu. Kurulum yapilacaksa once 2-3 kucuk skill ile
basla:

- `safe-status`
- `targeted-review`
- `handoff-summary`

`market-news-analyst`, `morning-briefing`, `scenario-analyzer`, `run-backtest`
gibi token veya shell tuketimi yuksek skill'ler onaysiz aktif edilmez.
