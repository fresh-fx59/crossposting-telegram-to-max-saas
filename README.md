# Telegram-to-Max Crossposting SaaS

Multi-tenant SaaS application for forwarding posts from Telegram channels to Max messenger.

Live: https://crossposter.aiengineerhelper.com/

## Features

- User registration with email verification (Cloudflare Turnstile captcha)
- Multiple Telegram channel connections per user
- Configurable Max bot credentials per user
- Automatic webhook setup for Telegram channels
- Daily post limits per connection
- Post history with success/failure tracking
- Encrypted token storage

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: React + TypeScript + Material UI (Vite)
- **Database**: PostgreSQL 17 with async SQLAlchemy
- **Reverse Proxy**: Traefik v3.3 with file-based routing
- **TLS**: Self-signed certs behind Cloudflare (Cloudflare handles public TLS)
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

Traefik uses a **file-based provider** (`config/traefik-dynamic.yml`) for routing rules
and TLS certificates. This avoids Docker API version incompatibilities that occur with the
Docker provider on newer Docker Engine versions (29+).

### Setup Steps

1. **Install Docker** (if not already):
   ```bash
   curl -fsSL https://get.docker.com | sudo sh
   sudo usermod -aG docker $USER
   # Log out and back in
   ```

2. **Clone and configure**:
   ```bash
   mkdir -p ~/apps/crossposting && cd ~/apps/crossposting
   git clone https://github.com/YOUR_USERNAME/crossposting-telegram-to-max-saas.git .
   ```

3. **Create `.env`** with real values:
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

4. **Create TLS certificates** in `certs/`:
   ```bash
   mkdir -p certs
   # Option A: Self-signed (works with Cloudflare Full mode)
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout certs/key.pem -out certs/cert.pem \
     -subj "/CN=crossposter.aiengineerhelper.com"

   # Option B: Cloudflare Origin CA (recommended)
   # Download from Cloudflare dashboard -> SSL/TLS -> Origin Server
   ```

5. **Update domain** in `config/traefik-dynamic.yml`:
   Replace `crossposter.aiengineerhelper.com` with your domain in all router rules.

6. **Deploy**:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

7. **Verify**:
   ```bash
   # All 4 containers running
   docker compose -f docker-compose.prod.yml ps

   # Health check
   curl -sk -H "Host: crossposter.aiengineerhelper.com" https://localhost/health
   # Expected: {"status":"healthy"}

   # Frontend loads
   curl -s https://crossposter.aiengineerhelper.com/ | head -5
   ```

### DNS / Cloudflare Setup

- Add A record: `crossposter` -> your server IP (Proxied)
- SSL/TLS mode: **Full** (not Full Strict, since we use self-signed origin certs)

### Key Files

| File | Purpose |
|------|---------|
| `docker-compose.prod.yml` | Production service definitions |
| `config/traefik-dynamic.yml` | Traefik routing rules and TLS certs |
| `.env` | Environment variables (secrets, not committed) |
| `.env.example` | Template for `.env` |
| `certs/cert.pem`, `certs/key.pem` | TLS certificates (not committed) |
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
- Verify `config/traefik-dynamic.yml` exists and has correct domain.
- Check `docker logs crossposter-traefik` for config errors.

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
│   │   ├── pages/       # Route pages
│   │   └── services/    # API client (axios)
│   ├── Dockerfile       # Multi-stage build with VITE_API_URL
│   └── nginx.conf       # SPA routing config
├── config/
│   └── traefik-dynamic.yml  # Routing rules + TLS config
├── scripts/
│   └── deploy.sh            # Deployment helper script
├── docker-compose.yml       # Development stack
├── docker-compose.prod.yml  # Production stack (Traefik)
├── .env.example             # Environment template
└── tests/                   # Automated tests
```

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
