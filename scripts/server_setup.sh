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
SERVICE_FILE="/etc/systemd/system/piyasapilot.service"
sudo bash -c "cat > $SERVICE_FILE" << EOF
[Unit]
Description=PiyasaPilot Docker Compose Service
Requires=docker.service
After=docker.service network.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/docker compose -f docker/docker-compose.prod.yml up -d --build
ExecStop=/usr/bin/docker compose -f docker/docker-compose.prod.yml down
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable piyasapilot.service

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
