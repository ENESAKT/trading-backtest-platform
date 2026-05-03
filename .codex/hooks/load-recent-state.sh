#!/bin/bash
# .claude/hooks/load-recent-state.sh
# UserPromptSubmit hook — son session recap'i yükle

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RECAP="$PROJECT_ROOT/.claude/memory/session-recap.md"

if [ -f "$RECAP" ]; then
  # Son güncelleme zamanını kontrol et
  if [ "$(uname)" = "Darwin" ]; then
    MTIME=$(stat -f %m "$RECAP" 2>/dev/null || echo "0")
  else
    MTIME=$(stat -c %Y "$RECAP" 2>/dev/null || echo "0")
  fi
  NOW=$(date +%s)
  AGE=$(( NOW - MTIME ))
  
  if [ $AGE -lt 86400 ]; then
    echo "📖 Son 24 saat içinde güncellenen session-recap.md bulundu."
    head -50 "$RECAP"
  fi
fi
