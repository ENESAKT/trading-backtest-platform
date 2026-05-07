#!/bin/bash
# .claude/hooks/auto-recap.sh
# Stop hook — oturum sonunda otomatik özet oluştur

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RECAP="$PROJECT_ROOT/.claude/memory/session-recap.md"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Son commit'leri al (bu oturumda yapılanlar)
RECENT_COMMITS=$(cd "$PROJECT_ROOT" && git log --oneline -10 --since="6 hours ago" 2>/dev/null || echo "commit yok")

# Planlama durumu (YAPILACAKLAR.md üzerinden)
DONE=$(grep -c '\- \[x\]' "$PROJECT_ROOT/docs/planning/planlama-sprint-gecmis.md" 2>/dev/null || echo "0")
TODO=$(grep -c '\- \[ \]' "$PROJECT_ROOT/docs/YAPILACAKLAR.md" 2>/dev/null || echo "0")

cat > "$RECAP" << EOF
# Session Recap — $TIMESTAMP

## Bu Oturumda Yapılanlar

### Son Commit'ler
\`\`\`
$RECENT_COMMITS
\`\`\`

### Sprint Durumu
- Tamamlanan görev: $DONE
- Kalan görev: $TODO

### Sıradaki
- YAPILACAKLAR.md'deki blokör maddelerden devam et
EOF

echo "📝 Session recap güncellendi: $RECAP"
