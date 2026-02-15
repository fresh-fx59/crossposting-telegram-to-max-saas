#!/bin/bash

# Deployment script for production server
# Run on the server as claude-developer user
#
# Usage: bash scripts/deploy.sh

set -e

APP_DIR="$HOME/apps/crossposting"
BACKUP_DIR="$HOME/backups/crossposter"

echo "=== Starting deployment ==="

# Create directories if they don't exist
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/certs"
mkdir -p "$APP_DIR/config"
mkdir -p "$BACKUP_DIR"

# Go to app directory
cd "$APP_DIR"

# Clone repository if not exists, otherwise pull latest
if [ ! -d ".git" ]; then
    echo "Cloning repository..."
    git clone https://github.com/YOUR_USERNAME/crossposting-telegram-to-max-saas.git .
else
    echo "Pulling latest changes..."
    git fetch origin
    git reset --hard origin/main
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Create it from .env.example:"
    echo "  cp .env.example .env"
    echo "  nano .env  # Fill in real values"
    exit 1
fi

# Check if TLS certs exist
if [ ! -f "certs/cert.pem" ] || [ ! -f "certs/key.pem" ]; then
    echo "WARNING: TLS certificates not found in certs/"
    echo "Generating self-signed certificates..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout certs/key.pem -out certs/cert.pem \
        -subj "/CN=crossposter.aiengineerhelper.com" 2>/dev/null
    echo "Self-signed certs created. For production, use Cloudflare Origin CA certs."
fi

# Backup postgres data (keep last 7 days)
if docker ps --format '{{.Names}}' | grep -q crossposter-postgres; then
    echo "Backing up database..."
    docker exec crossposter-postgres pg_dump -U crossposter crossposter \
        > "$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql" 2>/dev/null || true
    find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete 2>/dev/null || true
fi

# Build and start services
echo "Building and starting services..."
docker compose -f docker-compose.prod.yml up -d --build

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Health check
echo "Running health check..."
for i in 1 2 3; do
    if curl -sf http://localhost:80/health > /dev/null 2>&1 || \
       curl -sf -H "Host: crossposter.aiengineerhelper.com" https://localhost/health > /dev/null 2>&1; then
        echo "Health check passed!"
        break
    fi
    if [ "$i" -eq 3 ]; then
        echo "WARNING: Health check failed after 3 attempts."
        echo "Check logs: docker compose -f docker-compose.prod.yml logs"
    fi
    sleep 5
done

# Show status
echo ""
echo "=== Deployment complete ==="
docker compose -f docker-compose.prod.yml ps
echo ""
echo "Useful commands:"
echo "  Logs:    docker compose -f $APP_DIR/docker-compose.prod.yml logs -f"
echo "  Status:  docker compose -f $APP_DIR/docker-compose.prod.yml ps"
echo "  Restart: docker compose -f $APP_DIR/docker-compose.prod.yml restart"
