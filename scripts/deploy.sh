#!/bin/bash

# Deployment script for production server
# Run on the server as claude-developer user

set -e

APP_DIR="$HOME/apps/crossposting-telegram-to-max-saas"
BACKUP_DIR="$HOME/backups/crossposter"

echo "Starting deployment..."

# Create directories if they don't exist
mkdir -p "$APP_DIR"
mkdir -p "$BACKUP_DIR"

# Go to app directory
cd "$APP_DIR"

# Clone repository if not exists
if [ ! -d ".git" ]; then
    echo "Cloning repository..."
    git clone https://github.com/claude-developer/crossposting-telegram-to-max-saas.git .
else
    echo "Pulling latest changes..."
    git fetch origin
    git reset --hard origin/main
fi

# Backup postgres data before major changes (keep last 7 days)
if [ -d "$HOME/apps/crossposting-telegram-to-max-saas/postgres_backup" ]; then
    find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
fi

# Build and start services
echo "Building and starting services..."
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to be healthy
echo "Waiting for services to be ready..."
sleep 15

# Health check
if curl -f http://localhost:80/health > /dev/null 2>&1; then
    echo "Deployment successful! Health check passed."
else
    echo "Warning: Health check failed. Check logs with:"
    echo "  docker-compose -f $APP_DIR/docker-compose.prod.yml logs"
fi

echo "Deployment complete!"
echo "Check status: docker-compose -f $APP_DIR/docker-compose.prod.yml ps"
echo "View logs: docker-compose -f $APP_DIR/docker-compose.prod.yml logs -f"