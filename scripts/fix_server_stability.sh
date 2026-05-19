#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# PiyasaPilot — Sunucu Kararlılık Düzeltmesi
#
# Bu script sunucuda çalıştırılır. İki şey yapar:
#   1. Şu an down olan stack'i yeniden başlatır   (acil düzeltme)
#   2. Kalıcı systemd + watchdog kurulumunu yapar  (tekrar düşmemesi için)
#
# Kullanım:
#   ssh ubuntu@SUNUCU_IP
#   cd /opt/piyasapilot
#   bash scripts/fix_server_stability.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

INSTALL_DIR="/opt/piyasapilot"
COMPOSE_FILE="$INSTALL_DIR/infra/docker-compose.prod.yml"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PiyasaPilot — Sunucu Kararlılık Düzeltmesi"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ─── 1. MEVCUT DURUMU GÖSTER ─────────────────────────────────────────────────
echo ""
echo "▶ Mevcut container durumu:"
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "  Docker erişilemiyor!"

# ─── 2. ACİL BAŞLATMA ────────────────────────────────────────────────────────
echo ""
echo "▶ Stack yeniden başlatılıyor..."
cd "$INSTALL_DIR"
docker compose -f "$COMPOSE_FILE" up -d --remove-orphans
echo "  ✓ Container'lar başlatıldı"

# ─── 3. SYSTEMD SERVİSİNİ DÜZELT (Type=simple + foreground) ─────────────────
echo ""
echo "▶ systemd servisi düzeltiliyor (Type=oneshot → Type=simple)..."

sudo bash -c "cat > /etc/systemd/system/piyasapilot.service" << EOF
[Unit]
Description=PiyasaPilot Docker Compose Service
Documentation=https://piyasapilotu.com
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/docker compose -f infra/docker-compose.prod.yml up --remove-orphans
ExecStop=/usr/bin/docker compose -f infra/docker-compose.prod.yml down --timeout 30
Restart=always
RestartSec=30
TimeoutStartSec=300
TimeoutStopSec=60
StandardOutput=journal
StandardError=journal
SyslogIdentifier=piyasapilot

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable piyasapilot.service
echo "  ✓ systemd servisi güncellendi"

# ─── 4. WATCHDOG KURI ────────────────────────────────────────────────────────
echo ""
echo "▶ Watchdog kuruluyor (her 5 dakikada container kontrolü)..."

sudo bash -c 'cat > /usr/local/bin/piyasapilot_watchdog.sh' << 'WEOF'
#!/usr/bin/env bash
set -euo pipefail
INSTALL_DIR="/opt/piyasapilot"
LOG_TAG="piyasapilot-watchdog"
CRITICAL=("piyasapilot_nginx_prod" "piyasapilot_api_prod" "pp_mysql_prod" "pp_redis_prod")

needs_restart=0
for cname in "${CRITICAL[@]}"; do
  status=$(docker inspect --format '{{.State.Status}}' "$cname" 2>/dev/null || echo "missing")
  health=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$cname" 2>/dev/null || echo "missing")
  if [[ "$status" != "running" ]]; then
    logger -t "$LOG_TAG" "HATA: $cname => status='$status'"
    needs_restart=1; break
  fi
  if [[ "$health" == "unhealthy" ]]; then
    logger -t "$LOG_TAG" "HATA: $cname => unhealthy"
    needs_restart=1; break
  fi
done

if [[ $needs_restart -eq 1 ]]; then
  logger -t "$LOG_TAG" "Stack restart başlatılıyor..."
  cd "$INSTALL_DIR"
  docker compose -f infra/docker-compose.prod.yml up -d --remove-orphans 2>&1 | logger -t "$LOG_TAG"
fi
WEOF

sudo chmod +x /usr/local/bin/piyasapilot_watchdog.sh

sudo bash -c 'cat > /etc/systemd/system/piyasapilot-watchdog.service' << EOF
[Unit]
Description=PiyasaPilot Watchdog
After=piyasapilot.service
[Service]
Type=oneshot
ExecStart=/usr/local/bin/piyasapilot_watchdog.sh
EOF

sudo bash -c 'cat > /etc/systemd/system/piyasapilot-watchdog.timer' << EOF
[Unit]
Description=PiyasaPilot Watchdog Timer
Requires=piyasapilot-watchdog.service
[Timer]
OnBootSec=5min
OnUnitActiveSec=5min
AccuracySec=30s
[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable piyasapilot-watchdog.timer
sudo systemctl start piyasapilot-watchdog.timer
echo "  ✓ Watchdog timer aktif"

# ─── 5. SONUÇ ────────────────────────────────────────────────────────────────
echo ""
echo "▶ Son durum:"
sleep 5
docker compose -f "$COMPOSE_FILE" ps

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Düzeltme tamamlandı."
echo ""
echo "  Logları izlemek için:"
echo "    journalctl -u piyasapilot -f"
echo ""
echo "  Watchdog durumu için:"
echo "    systemctl status piyasapilot-watchdog.timer"
echo ""
echo "  Container sağlığı için:"
echo "    docker compose -f $COMPOSE_FILE ps"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
