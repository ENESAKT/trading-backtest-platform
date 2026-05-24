#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────
#  PiyasaPilot — Geliştirme Sunucusu Başlatıcı
#  Kullanım: ./start.sh
# ─────────────────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Renkler
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${GREEN}🚀 PiyasaPilot başlatılıyor...${NC}"

# ── 1. Python kontrolü ───────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo -e "${RED}❌ python3 bulunamadı. Python 3.10+ kurun.${NC}"; exit 1
fi
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "   Python $PYTHON_VERSION ✓"

# ── 2. Bağımlılık kontrolü ───────────────────────────────
echo -e "\n${YELLOW}📦 Python bağımlılıkları kontrol ediliyor...${NC}"
if [ -f requirements.txt ]; then
  pip install -r requirements.txt -q --no-warn-script-location 2>/dev/null || true
fi

# ── 3. Ortam değişkenleri ────────────────────────────────
if [ -f .env ]; then
  echo -e "   .env dosyası yüklendi ✓"
  set -a; source .env; set +a
else
  echo -e "${YELLOW}   ⚠️  .env dosyası bulunamadı — varsayılan (geliştirme) ayarları kullanılıyor.${NC}"
fi

# ── 4. Veritabanı / klasör hazırlığı ─────────────────────
mkdir -p db data/cache data/workspaces data/backtest_archive data/strategies logs

# ── 5. Frontend dist kontrolü ────────────────────────────
FRONTEND_DIST="$SCRIPT_DIR/frontend/dist"
if [ ! -f "$FRONTEND_DIST/index.html" ]; then
  echo -e "\n${YELLOW}🔨 Frontend build ediliyor...${NC}"
  cd frontend
  npm install --silent
  npm run build
  cd ..
  echo -e "   Frontend build tamamlandı ✓"
else
  echo -e "   Frontend dist mevcut ✓"
fi

# ── 6. Backend başlat ────────────────────────────────────
BACKEND_PORT="${BACKEND_PORT:-8000}"
echo -e "\n${GREEN}🌐 Backend başlatılıyor — http://localhost:${BACKEND_PORT}${NC}"
echo -e "   Durdurmak için Ctrl+C\n"

PYTHONPATH="$SCRIPT_DIR" python3 -m uvicorn backend.api.main:app \
  --host 0.0.0.0 \
  --port "$BACKEND_PORT" \
  --reload \
  --log-level info
