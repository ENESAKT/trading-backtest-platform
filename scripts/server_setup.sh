#!/usr/bin/env bash
set -euo pipefail

echo "Starting server setup..."

# 1. Update and install packages
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y docker.io docker-compose-plugin git certbot python3-certbot-nginx

# 2. Add current user to docker group
sudo usermod -aG docker $USER || true

# 3. Clone or pull repo
INSTALL_DIR="/opt/piyasapilot"
if [ -d "$INSTALL_DIR" ]; then
  echo "Directory $INSTALL_DIR exists. Pulling latest changes..."
  cd "$INSTALL_DIR"
  sudo git pull origin main
else
  echo "Cloning repository..."
  sudo git clone https://github.com/USERNAME/piyasapilot.git "$INSTALL_DIR"
  cd "$INSTALL_DIR"
fi

sudo chown -R $USER:$USER "$INSTALL_DIR"

# 4. Create .env from .env.example
if [ ! -f "$INSTALL_DIR/.env" ]; then
  echo "Creating .env file from .env.example..."
  cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
  echo "Please edit $INSTALL_DIR/.env with actual values."
fi

# 5. Configure systemd service
# NOT: Type=simple + foreground compose kullanıyoruz (oneshot değil).
# Bu sayede systemd container'ları gerçek anlamda takip eder ve
# herhangi bir crash'te Restart=always devreye girer.
SERVICE_FILE="/etc/systemd/system/piyasapilot.service"
sudo bash -c "cat > $SERVICE_FILE" << EOF
[Unit]
Description=PiyasaPilot Docker Compose Service
Documentation=https://piyasapilotu.com
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
# İlk başlatma: image'ları build et, sonra foreground'da çalıştır
ExecStartPre=/usr/bin/docker compose -f infra/docker-compose.prod.yml pull --quiet
ExecStart=/usr/bin/docker compose -f infra/docker-compose.prod.yml up --remove-orphans
ExecStop=/usr/bin/docker compose -f infra/docker-compose.prod.yml down --timeout 30
# Herhangi bir çöküşte 30 saniye bekleyip yeniden başlat
Restart=always
RestartSec=30
# Başlangıç için 5 dakika süre tanı (image pull + DB health check)
TimeoutStartSec=300
TimeoutStopSec=60
# Loglar journald'a gider: journalctl -u piyasapilot -f
StandardOutput=journal
StandardError=journal
SyslogIdentifier=piyasapilot

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable piyasapilot.service

# 5b. Watchdog — her 5 dakikada bir container durumunu kontrol et,
#     unhealthy veya exited varsa stack'i yeniden başlat.
WATCHDOG_FILE="/usr/local/bin/piyasapilot_watchdog.sh"
sudo bash -c "cat > $WATCHDOG_FILE" << 'WEOF'
#!/usr/bin/env bash
# PiyasaPilot Watchdog — systemd servis sağlıklıysa çıkar, değilse restart atar.
set -euo pipefail

COMPOSE_FILE="/opt/piyasapilot/infra/docker-compose.prod.yml"
LOG_TAG="piyasapilot-watchdog"

# Kritik container'lar (workers opsiyonel, bu 4'ü zorunlu)
CRITICAL=("piyasapilot_nginx_prod" "piyasapilot_api_prod" "pp_mysql_prod" "pp_redis_prod")

needs_restart=0
for cname in "${CRITICAL[@]}"; do
  status=$(docker inspect --format '{{.State.Status}}' "$cname" 2>/dev/null || echo "missing")
  health=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$cname" 2>/dev/null || echo "missing")

  if [[ "$status" != "running" ]]; then
    logger -t "$LOG_TAG" "UYARI: $cname durumu '$status' — restart başlatılıyor"
    needs_restart=1
    break
  fi
  if [[ "$health" == "unhealthy" ]]; then
    logger -t "$LOG_TAG" "UYARI: $cname unhealthy — restart başlatılıyor"
    needs_restart=1
    break
  fi
done

if [[ $needs_restart -eq 1 ]]; then
  logger -t "$LOG_TAG" "Stack yeniden başlatılıyor..."
  systemctl restart piyasapilot || true
fi
WEOF
sudo chmod +x "$WATCHDOG_FILE"

# Watchdog systemd timer (cron'dan daha güvenilir)
sudo bash -c "cat > /etc/systemd/system/piyasapilot-watchdog.service" << EOF
[Unit]
Description=PiyasaPilot Watchdog — container sağlık kontrolü
After=piyasapilot.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/piyasapilot_watchdog.sh
EOF

sudo bash -c "cat > /etc/systemd/system/piyasapilot-watchdog.timer" << EOF
[Unit]
Description=PiyasaPilot Watchdog — her 5 dakikada çalış
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
sudo systemctl start piyasapilot-watchdog.timer || true

# 6. Configure UFW
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
echo "y" | sudo ufw enable

# 7. Run certbot
# Note: Ensure DNS points to this server's IP before running certbot
sudo certbot --nginx -n --agree-tos -m admin@piyasapilotu.com -d piyasapilotu.com -d www.piyasapilotu.com || true

# 8. Add backup cron job
CRON_JOB="0 3 * * * $INSTALL_DIR/scripts/backup.sh >> /var/log/piyasapilot_backup.log 2>&1"
(crontab -l 2>/dev/null | grep -v "$INSTALL_DIR/scripts/backup.sh" ; echo "$CRON_JOB") | crontab -

echo "Server setup completed successfully!"
echo "Please remember to:"
echo "1. Log out and back in for docker group changes to take effect."
echo "2. Edit $INSTALL_DIR/.env with your production secrets."
echo "3. Run 'sudo systemctl start piyasapilot.service' to start the application."
