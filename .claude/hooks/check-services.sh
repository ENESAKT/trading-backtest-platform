#!/bin/bash
# .claude/hooks/check-services.sh
# SessionStart hook — oturum başlarken servis durumunu kontrol et

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
echo "🔍 PiyasaPilot servis kontrolü başlatılıyor..."

# 1. Gateway health check
if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
  HEALTH=$(curl -sf http://localhost:8000/api/health)
  CACHE_ROWS=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin)['cache']['rows'])" 2>/dev/null || echo "?")
  SYMBOLS=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin)['cache']['distinct_symbols'])" 2>/dev/null || echo "?")
  echo "✅ Gateway çalışıyor — Cache: $CACHE_ROWS bar, $SYMBOLS sembol"
else
  echo "⚠️  Gateway çalışmıyor (port 8000). Başlatmak için: cd $PROJECT_ROOT && source .venv/bin/activate && uvicorn backend.api.main:app --port 8000"
fi

# 2. Son planlama durumu (YAPILACAKLAR.md üzerinden)
if [ -f "$PROJECT_ROOT/YAPILACAKLAR.md" ]; then
  DONE=$(grep -c '^\- \[x\]' "$PROJECT_ROOT/docs/planning/planlama-sprint-gecmis.md" 2>/dev/null || echo "0")
  REMAINING=$(grep -c '^\- \[ \]' "$PROJECT_ROOT/YAPILACAKLAR.md" 2>/dev/null || echo "0")
  echo "📋 Planlama: $DONE tamamlandı, $REMAINING kalan"
fi

# 3. Son commit
LAST_COMMIT=$(cd "$PROJECT_ROOT" && git log --oneline -1 2>/dev/null || echo "git yok")
echo "📝 Son commit: $LAST_COMMIT"

echo "✅ Servis kontrolü tamamlandı."
