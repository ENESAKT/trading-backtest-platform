#!/bin/bash
# .claude/hooks/persist-agent-output.sh
# SubagentStop hook — agent çıktısını logla

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/.claude/agent-logs"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
AGENT_NAME="${CLAUDE_AGENT_NAME:-unknown}"
LOG_FILE="$LOG_DIR/${AGENT_NAME}_${TIMESTAMP}.log"

# stdin'den agent çıktısını oku (varsa)
if [ ! -t 0 ]; then
  cat > "$LOG_FILE"
  echo "📋 Agent çıktısı kaydedildi: $LOG_FILE"
fi
