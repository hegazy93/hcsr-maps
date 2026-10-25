#!/usr/bin/env bash
# One-time setup on a fresh Ubuntu 22.04/24.04 server. Run from the unzipped folder:
#   sudo bash deploy/install.sh
set -euo pipefail
APP_DIR=/opt/hcsr_maps
apt-get update
apt-get install -y python3-venv python3-pip nginx certbot python3-certbot-nginx
id hcsr >/dev/null 2>&1 || useradd --system --create-home --shell /usr/sbin/nologin hcsr
mkdir -p "$APP_DIR"
cp -r ./* ./.streamlit "$APP_DIR"/
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"
chown -R hcsr:hcsr "$APP_DIR"
cp "$APP_DIR/deploy/hcsr-maps.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now hcsr-maps
cp "$APP_DIR/deploy/nginx-hcsr-maps.conf" /etc/nginx/sites-available/hcsr-maps
ln -sf /etc/nginx/sites-available/hcsr-maps /etc/nginx/sites-enabled/hcsr-maps
nginx -t && systemctl reload nginx
echo "Done. Point the DNS record maps.hcsr-eg.org to this server, then run:"
echo "  sudo certbot --nginx -d maps.hcsr-eg.org"
