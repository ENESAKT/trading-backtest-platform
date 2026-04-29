# PiyasaPilot Skill Rehberi

## Genel Bakış

PiyasaPilot 15 skill ile donatılmıştır. Skill'ler Claude Code'un görev bazlı yetenek setleridir ve `.claude/skills/[skill-adı]/SKILL.md` dosyalarında tanımlıdır.

## Skill Listesi

### Projeye Özel Skill'ler (7)

| Skill | Görev | Çağrı |
|-------|-------|-------|
| `validate-spike-filter` | IQR spike filter testi | Yeni sembol eklendiğinde |
| `run-backtest` | Hızlı backtest çalıştır | `/backtest THYAO.IS sma_crossover` |
| `health-check` | Tüm servisleri kontrol et | `/durum` |
| `morning-briefing` | Sabah BIST 100 özeti + 3 odak hisse | Her sabah |
| `paper-trade-status` | Paper trading durumu | `/durum` ile birlikte |
| `deploy-stack` | Docker Compose yönetimi | `make up` / `make down` |
| `session-recap` | Oturum sonu özet | Otomatik (hook) |

### Adapted Skill'ler (8)

| Skill | Kaynak | Görev |
|-------|--------|-------|
| `backtest-expert` | tradermonty | Backtest sonuçlarını uzman analizi |
| `position-sizer` | tradermonty | Kelly/Fixed Fractional pozisyon boyutu |
| `technical-analyst` | tradermonty | 4 katmanlı teknik analiz |
| `market-news-analyst` | tradermonty | Haber sentiment analizi |
| `signal-postmortem` | tradermonty | Kapanan trade'den öğrenme |
| `strategy-pivot-designer` | tradermonty | Strateji iyileştirme önerileri |
| `scenario-analyzer` | tradermonty | Piyasa senaryosu etki analizi |
| `risk-manager` | VoltAgent | Portföy risk yönetimi |

## Slash Command'lar

| Komut | Açıklama |
|-------|----------|
| `/devam` | Son oturumdan devam et (session-recap.md yükle) |
| `/backtest <sembol> <strateji>` | Backtest çalıştır ve raporla |
| `/sinyal <sembol>` | 8 strateji konsensüs sinyal raporu |
| `/durum` | Tüm servislerin durumu |
| `/strateji-yeni [odak]` | Yeni strateji araştırması başlat |

## Hook'lar

| Event | Hook | Amaç |
|-------|------|------|
| SessionStart | `check-services.sh` | Gateway + cache + planlama durumu |
| Stop | `auto-recap.sh` | session-recap.md oluştur |
| SubagentStop | `persist-agent-output.sh` | Agent çıktısını logla |

## Yeni Skill Ekleme

1. `.claude/skills/yeni-skill/SKILL.md` dosyası oluştur
2. Dosyada görev, adımlar, referanslar ve çıktı formatını tanımla
3. İlgili agent'ın tools listesinde skill'i çağırabilecek yetkiler olmalı
