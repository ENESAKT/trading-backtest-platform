#!/usr/bin/env bash
set -euo pipefail

DEVICE="${DEVICE:-/dev/nvme1n1}"
MOUNT_POINT="${MOUNT_POINT:-/data}"
DOCKER_DATA_ROOT="${DOCKER_DATA_ROOT:-$MOUNT_POINT/docker}"

if [[ ! -b "$DEVICE" ]]; then
  echo "EBS device bulunamadı: $DEVICE" >&2
  echo "Mevcut diskler:" >&2
  lsblk >&2
  exit 1
fi

if ! sudo blkid "$DEVICE" >/dev/null 2>&1; then
  echo "$DEVICE formatlanıyor..."
  sudo mkfs.ext4 -F "$DEVICE"
fi

sudo mkdir -p "$MOUNT_POINT"
UUID="$(sudo blkid -s UUID -o value "$DEVICE")"
if ! grep -q "$UUID" /etc/fstab; then
  echo "UUID=$UUID $MOUNT_POINT ext4 defaults,nofail 0 2" | sudo tee -a /etc/fstab >/dev/null
fi

sudo mount "$MOUNT_POINT"
sudo mkdir -p "$DOCKER_DATA_ROOT"

sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json >/dev/null <<EOF
{
  "data-root": "$DOCKER_DATA_ROOT",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "5"
  }
}
EOF

sudo systemctl restart docker
docker info --format 'Docker data root: {{.DockerRootDir}}'
