# Telegram-to-Max Crossposting SaaS

Multi-tenant SaaS application for forwarding posts from Telegram channels to Max messenger.

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
- **Frontend**: React + TypeScript + Material UI
- **Database**: PostgreSQL with async SQLAlchemy
- **Deployment**: Docker + Docker Compose + Traefik (reverse proxy)
- **SSL/TLS**: Let's Encrypt with ACME challenge

## Quick Start

### Development

```bash
# Copy environment variables
cp .env.example .env

# Start all services
docker-compose up

# Start backend only
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend only
cd frontend
npm install
npm run dev

# Run tests
python tests/run_tests.py
```

### Production Deployment

#### Prerequisites

- Server with Docker and Docker Compose installed
- Domain name pointing to your server's IP address
- Ports 80 and 443 open on your server
- Email configured for Let's Encrypt notifications

#### Setup Steps

1. **Clone the repository** on your server:
   ```bash
   git clone https://github.com/YOUR_USERNAME/crossposting-telegram-to-max-saas.git
   cd crossposting-telegram-to-max-saas
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   nano .env
   ```
   Update all required variables (see Environment Variables section below).

3. **Update domain in configuration**:
   - Edit `docker-compose.prod.yml`
   - Replace `telegram-crossposting-saas.aiengineerhelper.com` with your domain in all Traefik labels
   - Update `TRAEFIK_ACME_EMAIL` to your email

4. **Deploy**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

5. **Verify deployment**:
   ```bash
   # Check containers are running
   docker ps --filter "name=crossposter"

   # Check Traefik dashboard
   curl http://YOUR_SERVER_IP:8080/api/http/routers

   # Test the site
   curl -H "Host:YOUR_DOMAIN.com" http://YOUR_SERVER_IP/
   ```

#### Troubleshooting Production Deployment

**Issue: 404 errors on HTTPS, HTTP works**
- Symptom: `curl http://server/` works, `curl https://domain.com/` returns 404
- Cause: Traefik routers configured for HTTP only, not HTTPS
- Fix: Ensure all router entrypoints use `websecure`, not `web`, and include TLS cert resolver

**Issue: Traefik logs show "too many services" error**
- Symptom: Traefik refuses to start routers
- Cause: Multiple service labels using same name without explicit service reference
- Fix: Add `traefik.http.routers.NAME.service=SERVICENAME` to each router

**Issue: Traefik logs show parsing errors for Host()**
- Symptom: `expected operand, found '/'` on domain parsing
- Cause: Missing backticks around domain name
- Fix: Use `Host(\`your-domain.com\`)` with backticks

**Issue: Deployment fails on GitHub Actions**
- Symptom: SSH authentication failed with exit code 255
- Cause: SSH keys not properly configured between GitHub Actions and server
- Fix: Add SSH private key to GitHub Actions secrets and public key to server's `~/.ssh/authorized_keys`

## Environment Variables

See [`.env.example`](.env.example) for all required configuration.

Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - Secret for JWT tokens (32+ chars)
- `SMTP_HOST/USER/PASSWORD` - Email configuration
- `CLOUDFLARE_TURNSTILE_SECRET` - Captcha secret
- `ENCRYPTION_KEY` - Key for token encryption (32 bytes)
- `FRONTEND_URL` - Your application's frontend URL
- `WEBHOOK_BASE_URL` - Base URL for Telegram webhooks

## Production Architecture

```
Internet
   │
   ▼
┌─────────────────────────────────────────┐
│         Traefik v3.0               │
│  (SSL Termination + Routing)         │
│                                   │
│  • HTTP (port 80)  ►► HTTPS (443) │
│  • Let's Encrypt Certificates         │
└─────────────┬───────────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌─────────┐       ┌──────────────┐
│ Frontend │       │   Backend    │
│ (nginx)  │       │  (FastAPI)   │
└─────────┘       └──────┬───────┘
                          │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
      ┌──────────┐  ┌───────────┐  ┌──────────┐
      │PostgreSQL │  │Telegram   │  │  Max     │
      │          │  │Webhooks   │  │  API     │
      └──────────┘  └───────────┘  └──────────┘
```

### Traefik Configuration (Production)

The production setup uses Traefik with the following key configurations:

- **Entry Points**:
  - `web` (port 80) - Redirects to HTTPS automatically
  - `websecure` (port 443) - Handles HTTPS traffic with SSL

- **Certificate Resolution**:
  - Uses Let's Encrypt with ACME TLS challenge
  - Certs stored in `traefik-letsencrypt` volume

- **Router Rules**:
  - Frontend: `Host(\`your-domain.com\`)`
  - Backend API: `Host(\`your-domain.com\`) && PathPrefix(\`/api\`)`
  - Backend Auth: `Host(\`your-domain.com\`) && PathPrefix(\`/auth\`)`
  - Backend Webhook: `Host(\`your-domain.com\`) && PathPrefix(\`/webhook\`)`
  - Health: `Host(\`your-domain.com\`) && PathPrefix(\`/health\`)`

**Important**: All routers use `websecure` entrypoint and include `tls.certresolver=mytlschallenge` label.

## API Documentation

Once running, visit:
- Frontend: https://YOUR_DOMAIN.com/
- API Docs: https://YOUR_DOMAIN.com/api/docs
- Health: https://YOUR_DOMAIN.com/health
- Traefik Dashboard: http://YOUR_SERVER_IP:8080 (do not expose publicly)

## User Flow

1. Sign up (email/password + captcha)
2. Verify email via link
3. Log in
4. Add Max credentials (bot token, chat ID)
5. Add Telegram channel (channel name, bot token) → Webhook auto-set
6. Create connection (link Telegram → Max)
7. Post to Telegram → Appears in Max

## Testing

See [tests/README.md](tests/README.md) for detailed test documentation.

### Production Test Checklist

Before going live, verify:
- [ ] All 4 containers running (traefik, frontend, backend, postgres)
- [ ] HTTPS works: `curl https://YOUR_DOMAIN.com/` returns 200
- [ ] HTTP redirects to HTTPS: `curl -L http://YOUR_DOMAIN.com/` follows HTTPS
- [ ] API accessible: `curl https://YOUR_DOMAIN.com/api/health` returns 200
- [ ] SSL certificate valid: Check browser lock icon
- [ ] User registration works (test with real email)
- [ ] Email verification flow works

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/       - FastAPI routes
│   │   ├── database/   - SQLAlchemy models
│   │   ├── schemas/    - Pydantic schemas
│   │   └── services/   - Business logic
├── frontend/
│   ├── nginx.conf      - Production nginx config
│   ├── Dockerfile      - Production build
│   └── src/
│       ├── components/ - React components
│       ├── pages/      - Route components
│       └── services/   - API client
├── docker-compose.yml              - Development stack
├── docker-compose.prod.yml         - Production stack (Traefik)
├── .env.example                  - Environment template
└── tests/                        - Automated tests with mocks
```

## Security Notes

- All API tokens (Telegram, Max) are encrypted at rest using AES-256-GCM
- JWT tokens expire after 24 hours by default
- HTTPS is enforced via Traefik redirect
- Rate limiting implemented on critical endpoints
- SQL injection protection via SQLAlchemy parameterized queries
- XSS protection via React's built-in escaping

## License

MIT