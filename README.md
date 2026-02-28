# Telegram-to-Max Crossposting SaaS

Multi-tenant SaaS application for forwarding posts from Telegram channels to Max messenger.

Live: https://crossposter.aiengineerhelper.com/

## Features

- **Bilingual interface** (Russian / English) with auto-detection and manual switcher
- Built-in setup guide (`/docs`) with step-by-step instructions
- User registration with email verification (Cloudflare Turnstile captcha)
- Multiple Telegram channel connections per user
- Configurable Max bot credentials per user
- Automatic webhook setup for Telegram channels
- Daily post limits per connection
- Post history with success/failure tracking
- Encrypted token storage

## Contact

Telegram: [@alex_444](https://t.me/alex_444)

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: React + TypeScript + Material UI (Vite)
- **Database**: PostgreSQL 17 with async SQLAlchemy
- **Reverse Proxy**: Traefik v3.3 with file-based routing
- **TLS**: Let's Encrypt certificates terminated on monitoring nginx
- **Deployment**: Docker Compose

## Quick Start (Development)

```bash
cp .env.example .env
# Edit .env with your values

# Start all services
docker compose up

# Or run individually:
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
cd frontend && npm install && npm run dev
```

## Production Deployment

### Prerequisites

- Server with Docker Engine 29+ and Docker Compose v2
- Domain pointing to the server (e.g., via Cloudflare DNS)
- Ports 80 and 443 open

### Architecture

```
Internet -> Cloudflare (public TLS) -> Server
                                         |
                                    Traefik v3.3
                                    (file provider)
                                    port 80 -> 443
                                         |
                        +----------------+----------------+
                        |                                 |
                   /api, /auth,                          /
                   /webhook, /health                (catch-all)
                        |                                 |
                   Backend                          Frontend
                   (FastAPI)                        (nginx)
                   port 8000                        port 80
                        |
                   PostgreSQL
                   port 5432
```

Traefik runs as a **shared reverse proxy** in a separate `~/traefik/` directory, using a
file-based provider for routing. This allows multiple sites to share one Traefik instance.
Reference configs are in `traefik/` in this repo.

### Setup Steps

1. **Install Docker** (if not already):
   ```bash
   curl -fsSL https://get.docker.com | sudo sh
   sudo usermod -aG docker $USER
   # Log out and back in
   ```

2. **Set up shared Traefik** (one-time, serves all sites):
   ```bash
   mkdir -p ~/traefik/dynamic ~/traefik/certs
   # Copy traefik/docker-compose.yml from this repo to ~/traefik/
   # Copy traefik/dynamic/crossposting.yml to ~/traefik/dynamic/
   # Add TLS certs to ~/traefik/certs/ (self-signed or Cloudflare Origin CA)
   cd ~/traefik && docker compose up -d
   ```

3. **Clone the app**:
   ```bash
   cd ~ && git clone https://github.com/YOUR_USERNAME/crossposting-telegram-to-max-saas.git
   cd ~/crossposting-telegram-to-max-saas
   ```

4. **Create `.env`** with real values:
   ```bash
   cp .env.example .env
   nano .env
   ```
   Generate secrets:
   ```bash
   python3 -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_hex(32))"
   python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(64))"
   python3 -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_hex(32))"
   ```
   **Important**: The password in `DATABASE_URL` must match `POSTGRES_PASSWORD`.

5. **Deploy**:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

6. **Verify**:
   ```bash
   # 3 containers running (backend, frontend, postgres)
   docker compose -f docker-compose.prod.yml ps

   # Health check
   curl -sf https://crossposter.aiengineerhelper.com/health
   # Expected: {"status":"healthy"}
   ```

### CI/CD (GitHub Actions)

After the first manual deploy, subsequent deploys are automated. Push to `main` triggers `.github/workflows/deploy.yml` which SSHs into the server, runs `git pull`, and rebuilds containers.

Required GitHub secrets (only 3):
| Secret | Description |
|--------|-------------|
| `SSH_PRIVATE_KEY` | SSH key with access to the server |
| `SERVER_IP` | Server IP address |
| `DEPLOY_USER` | SSH username (e.g., `claude-developer`) |

The workflow does **not** touch `.env`, certs, or Traefik — those are managed manually on the server.

### Frontend Deploy (Monitoring Server)

Frontend static files are also auto-deployed to the monitoring server for
`crossposter.aiengineerhelper.com` via
`.github/workflows/deploy-frontend-monitoring.yml`.

What this workflow does on each push to `main`:

1. Builds `frontend/` (`npm ci && npm run build`)
2. Uploads files to monitoring server
3. Replaces `/var/www/crossposter` contents
4. Applies dedicated crossposter nginx config on monitoring server
5. Ensures Let's Encrypt certificate for `crossposter.aiengineerhelper.com`
6. Verifies HTTPS response for host `crossposter.aiengineerhelper.com`

Required secrets:

| Secret | Description |
|--------|-------------|
| `MONITORING_SERVER_HOST` | Monitoring server host/IP (e.g. `45.151.30.146`) |
| `MONITORING_SERVER_USER` | SSH username on monitoring server (e.g. `user1`) |
| `MONITORING_SERVER_SSH_KEY` | Private SSH key with sudo access for `/var/www/crossposter` |

### DNS Setup

- Add A record: `crossposter` -> monitoring server IP (`45.151.30.146`) as DNS-only

### Key Files

| File | Purpose |
|------|---------|
| `docker-compose.prod.yml` | Production service definitions |
| `traefik/` | Reference Traefik configs (copy to `~/traefik/` on server) |
| `.env` | Environment variables (secrets, not committed) |
| `.env.example` | Template for `.env` |
| `frontend/Dockerfile` | Frontend build (bakes `VITE_API_URL` and `VITE_TURNSTILE_SITE_KEY` at build time) |
| `backend/Dockerfile` | Backend container |

### Environment Variables

See [`.env.example`](.env.example) for the full list. Key variables:

| Variable | Description |
|----------|-------------|
| `POSTGRES_PASSWORD` | Database password (must match in `DATABASE_URL`) |
| `JWT_SECRET_KEY` | JWT signing key (64+ hex chars) |
| `ENCRYPTION_KEY` | AES encryption key for bot tokens (32+ hex chars) |
| `CLOUDFLARE_TURNSTILE_SECRET` | Turnstile captcha server key (set via `.env`) |
| `CLOUDFLARE_TURNSTILE_SITE_KEY` | Turnstile captcha client key (baked into frontend at build time, rebuild frontend to change) |
| `FRONTEND_URL` | Public URL (e.g., `https://crossposter.aiengineerhelper.com`) |
| `WEBHOOK_BASE_URL` | Same as FRONTEND_URL (Telegram webhook target) |

### Troubleshooting

**Backend crash-loops with validation errors**
- Check `docker logs crossposter-backend`. Usually means `.env` has empty/missing values.
- `JWT_SECRET_KEY` and `ENCRYPTION_KEY` must be 32+ characters.

**Traefik returns 404**
- Verify `~/traefik/dynamic/crossposting.yml` exists and has correct domain.
- Check `docker logs traefik` for config errors.
- Ensure the `traefik-public` network exists: `docker network ls | grep traefik-public`.

**Blank page in browser (HTML loads but nothing renders)**
- Hard refresh (`Ctrl+Shift+R`) to clear cached old JS bundle.
- Verify `VITE_API_URL` was set at frontend build time: check the JS bundle for your domain.

**Changing Turnstile or API URL**
- Frontend builds require `--build-arg` for `VITE_API_URL` and `VITE_TURNSTILE_SITE_KEY`.
- Example: `docker compose -f docker-compose.prod.yml build --build-arg VITE_TURNSTILE_SITE_KEY=newkey frontend`

**Traefik "client version too old" error**
- This happens with Docker provider on Docker Engine 29+. The file-based provider
  (used in this setup) avoids this issue entirely.

## API Endpoints

- Frontend: `https://YOUR_DOMAIN/`
- API Docs: `https://YOUR_DOMAIN/api/docs`
- Health: `https://YOUR_DOMAIN/health`
- Traefik Dashboard: `http://SERVER_IP:8080` (not exposed publicly)

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/         # FastAPI routes
│   │   ├── database/    # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── i18n/        # Internationalization (RU/EN translations)
│   │   ├── pages/       # Route pages
│   │   └── services/    # API client (axios)
│   ├── Dockerfile       # Multi-stage build with VITE_API_URL
│   └── nginx.conf       # SPA routing config
├── traefik/
│   ├── docker-compose.yml       # Shared Traefik (copy to ~/traefik/)
│   └── dynamic/
│       └── crossposting.yml     # Routing rules for this app
├── scripts/
│   └── deploy.sh            # Deployment helper script
├── docker-compose.yml       # Development stack
├── docker-compose.prod.yml  # Production stack (no Traefik)
├── .env.example             # Environment template
└── tests/                   # Automated tests
```

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
