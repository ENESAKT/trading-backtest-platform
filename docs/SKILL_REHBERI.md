# PiyasaPilot Skill Rehberi

Ajanların veya kullanıcıların projeyi kurallara (mimari, temizlik vb.) uygun geliştirmesini sağlayan "skill" dosyalarıdır.

| Skill Adı | Açıklama |
| --- | --- |
| `data-architecture-auditor` | Data mimarisi (ClickHouse/MySQL vs.) ihlali kontrolü yapar. |
| `data-inventory-check` | Veri envanteri tablosunu/kataloğunu doğrular. |
| `data-retention-guardian` | Retention (veri saklama süresi) kurallarının ihlal edilmesini önler. |
| `timeframe-derivation-check` | Türetilmiş zaman serisi akışlarını (örn: 1m -> 5m) test eder. |
| `repo-cleanup-auditor` | Depo dosya boyutlarını ve istenmeyen (.venv, args) klasörleri kontrol eder. |
| `borfin-integration-auditor` | Telif ve kopyalama riskine (Borfin verisi) karşı denetim yapar. |
| `production-package-auditor` | Docker paketinin içeriğini/şişkinliğini kontrol eder. |
| `deployment-readiness-check` | Canlı çıkış için `.env`, domain, TLS gibi koşulları test eder. |

Skill detayları için `.claude/skills/` dizinini inceleyebilirsiniz.

## Tek Kaynak Kuralı

- `.claude/skills/` ortak ve canonical skill kaynağıdır.
- `.agents/skills/` Codex/OpenAI uyumluluk aynasıdır; ortak skill'lerde isim ve açıklama `.claude/skills/` ile senkron tutulur.
- `source-command-*` skill'leri yalnızca Codex komut köprüsüdür ve `.agents/skills/` altında kalır.
- Yeni ortak skill eklendiğinde önce `.claude/skills/`, sonra gerekiyorsa `.agents/skills/` aynası güncellenir.
