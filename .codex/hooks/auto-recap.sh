#!/bin/bash
# .claude/hooks/auto-recap.sh
# Stop hook — oturum sonunda otomatik özet oluştur

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RECAP="$PROJECT_ROOT/.claude/memory/session-recap.md"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Son commit'leri al (bu oturumda yapılanlar)
RECENT_COMMITS=$(cd "$PROJECT_ROOT" && git log --oneline -10 --since="6 hours ago" 2>/dev/null || echo "commit yok")

# Planlama durumu
DONE=$(grep -c '\- \[x\]' "$PROJECT_ROOT/planlama.md" 2>/dev/null || echo "0")
TODO=$(grep -c '\- \[ \]' "$PROJECT_ROOT/planlama.md" 2>/dev/null || echo "0")

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
- planlama.md'deki ilk açık (\`- [ ]\`) tick'ten devam et
EOF

echo "📝 Session recap güncellendi: $RECAP"
