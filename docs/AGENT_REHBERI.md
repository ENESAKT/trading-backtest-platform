# PiyasaPilot Agent Rehberi

## Genel Bakış

PiyasaPilot 8 sub-agent ile çalışır. Her agent belirli bir görev alanına odaklanır ve Claude Code oturumunda `@agent-adı` ile çağrılabilir.

## Agent Listesi

| Agent | Model | Görev | Çağrı |
|-------|-------|-------|-------|
| `data-validator` | Haiku | IQR spike testi, OHLCV doğrulama, cache tutarlılığı | `@data-validator cache'teki son verileri doğrula` |
| `quant-researcher` | Sonnet | Yeni strateji fikirleri, parametre tarama, literatür | `@quant-researcher momentum tabanlı yeni strateji öner` |
| `backtest-runner` | Haiku | Backtest çalıştır, sonuç raporla | `@backtest-runner THYAO.IS sma_crossover` |
| `frontend-builder` | Sonnet | TS/Vite/lightweight-charts geliştirme | `@frontend-builder Screener'a yeni filtre ekle` |
| `backend-builder` | Sonnet | FastAPI/SQLite/worker geliştirme | `@backend-builder yeni worker ekle` |
| `robot-executor` | Haiku | Paper trading izleme, risk analizi | `@robot-executor açık pozisyonları raporla` |
| `code-reviewer` | Sonnet | Kod kalitesi, test kapsamı, mimari uyumluluk | `@code-reviewer son commit'i incele` |
| `devops-engineer` | Haiku | Docker, healthcheck, deployment | `@devops-engineer servisleri kontrol et` |

## Model Seçimi Mantığı

- **Haiku** → Basit, tekrarlı görevler (doğrulama, raporlama, healthcheck)
- **Sonnet** → Karmaşık, yaratıcı görevler (strateji tasarımı, kod geliştirme)

## Agent Dosya Yapısı

Her agent `.claude/agents/[agent-adı].md` dosyasında tanımlıdır:

```yaml
---
description: "Agent açıklaması"
model: haiku | sonnet
tools:
  - Read
  - Write
  - Bash(komut)
---

# Agent Adı

## Görevlerin
[Detaylı görev listesi]

## Proje Bağlamı
[İlgili dosyalar ve yapılar]

## Çıktı Formatı
[Beklenen rapor formatı]
```

## Örnek Kullanım Senaryoları

### Sabah Rutin
```
@backtest-runner BIST 30'daki tüm hisseleri sma_crossover ile test et
@robot-executor paper trading durumunu raporla
```

### Yeni Strateji Geliştirme
```
@quant-researcher Ichimoku Cloud tabanlı strateji öner
@frontend-builder StrategyPanel'e yeni strateji kartı ekle
@backend-builder blueprint'e yeni strateji ekle
@code-reviewer tüm değişiklikleri incele
```

### Hata Ayıklama
```
@data-validator THYAO.IS verisinde spike var mı kontrol et
@devops-engineer API healthcheck sonuçlarını göster
```
