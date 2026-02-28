#!/usr/bin/env bash
set -euo pipefail

if ! command -v certbot >/dev/null 2>&1; then
  apt-get update -y
  apt-get install -y certbot
fi

mkdir -p /var/www/letsencrypt
systemctl enable --now certbot.timer

EMAIL="${LETSENCRYPT_EMAIL:-}"
EMAIL_ARGS=()
if [ -n "${EMAIL}" ]; then
  EMAIL_ARGS=(--email "${EMAIL}")
else
  EMAIL_ARGS=(--register-unsafely-without-email)
fi

CERT_NAME="crossposter.aiengineerhelper.com"
CERT_PATH="/etc/letsencrypt/live/${CERT_NAME}/fullchain.pem"

if [ ! -f "${CERT_PATH}" ]; then
  certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --keep-until-expiring \
    --preferred-challenges http \
    --pre-hook "systemctl stop nginx" \
    --post-hook "systemctl start nginx" \
    --cert-name "${CERT_NAME}" \
    "${EMAIL_ARGS[@]}" \
    -d "${CERT_NAME}"
fi

certbot renew \
  --quiet \
  --pre-hook "systemctl stop nginx" \
  --post-hook "systemctl start nginx"
