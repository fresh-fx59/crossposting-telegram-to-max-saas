# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-tenant SaaS for crossposting from Telegram channels to Max messenger. Users register, configure their Telegram bot + Max credentials, and the system forwards posts automatically via webhooks.

Live at: https://crossposter.aiengineerhelper.com/

## Tech Stack

- **Backend**: FastAPI (Python 3.11) with async SQLAlchemy + PostgreSQL 17
- **Frontend**: React 18 + TypeScript + Material UI, built with Vite
- **Reverse Proxy**: Traefik v3.3 with file-based provider (not Docker provider)
- **Deployment**: Docker Compose on Ubuntu server behind Cloudflare

## Development

```bash
cp .env.example .env
docker compose up
# Backend: http://localhost:8000, Frontend: http://localhost:3000
```

## Production Deployment

Deployment path: `~/crossposting-telegram-to-max-saas/`

Traefik runs as a shared reverse proxy in `~/traefik/` (separate from the app). The `traefik/` directory in this repo contains reference configs the user copies to the server once.

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Key production files (not in git): `.env` (secrets).
Key production files (in git): `docker-compose.prod.yml`, `traefik/` (reference Traefik configs).

CI/CD: GitHub Actions (`.github/workflows/deploy.yml`) does `git pull` + `docker compose up --build`. Only needs 3 secrets: `SSH_PRIVATE_KEY`, `SERVER_IP`, `DEPLOY_USER`.

## Architecture

**Traefik routing** (defined in `traefik/dynamic/crossposting.yml`, deployed to `~/traefik/dynamic/`):
- `/api/*`, `/auth/*`, `/webhook/*`, `/health` → backend (FastAPI on port 8000)
- `/` (catch-all, priority 1) → frontend (nginx on port 80)

**Frontend build**: `VITE_API_URL` is baked at Docker build time via `ARG` in `frontend/Dockerfile`. The API client (`frontend/src/services/api.ts`) uses this as the axios `baseURL`.

**Backend config**: Pydantic Settings loads from `.env` file. `JWT_SECRET_KEY` and `ENCRYPTION_KEY` have `min_length=32` validation.

## Data Model

- **User**: email, hashed_password, connections_limit, daily_posts_limit
- **TelegramConnection**: user_id, telegram_channel_id, bot_token (encrypted), webhook_secret, webhook_url
- **MaxChannel**: user_id, bot_token (encrypted), chat_id, name — each Max channel stores its own bot credentials
- **Connection** (Link): user_id, telegram_connection_id (FK), max_channel_id (FK), name — links a Telegram source to a Max destination
- **Post**: connection_id, telegram_message_id, max_message_id, content_type, status, error_message

Users can have multiple Telegram channels and multiple Max channels. Connections (links) map any Telegram channel to any Max channel.

## API Routes

- `/auth/*` — registration, login, logout, email verification, password reset
- `/api/connections/telegram` — CRUD for Telegram channel connections
- `/api/connections/max` — CRUD for Max channels + test endpoint
- `/api/connections` — CRUD for links (Telegram → Max) + test endpoint
- `/webhook/telegram/{secret}` — incoming Telegram webhook handler

## Frontend Pages

- `/` — Landing page
- `/docs` — Setup guide (public, no auth required)
- `/login`, `/register`, `/verify-email` — Auth pages
- `/dashboard` — Main page with 3 sections: Telegram Channels, Max Channels, Links
- `/connections/:id` — Connection detail with post history
- `/account` — Account info and logout
