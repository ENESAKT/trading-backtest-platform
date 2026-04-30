#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if command -v uvx >/dev/null 2>&1; then
  exec uvx "$@"
fi

if [ -x "$ROOT_DIR/.venv/bin/uvx" ]; then
  exec "$ROOT_DIR/.venv/bin/uvx" "$@"
fi

if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
  "$ROOT_DIR/.venv/bin/python" -m pip install -q uv
  exec "$ROOT_DIR/.venv/bin/uvx" "$@"
fi

echo "uvx bulunamadı. Önce 'python3.11 -m venv .venv && .venv/bin/python -m pip install uv' çalıştırın." >&2
exit 127
