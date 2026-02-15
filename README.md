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
#### Setup Steps

1. **Install Docker and Docker Compose** (if not already installed):
   ```bash
   sudo apt update && sudo apt upgrade -y
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo apt install docker-compose -y
   docker --version  # Should show 29.2.1+
   docker-compose --version  # Should show 1.29.2+
   ```

2. **Clone or deploy** repository to your server:
   ```bash
   mkdir -p ~/apps && cd ~/apps
   # Option A: git clone
   git clone https://github.com/YOUR_USERNAME/crossposting-telegram-to-max-saas.git
   cd crossposting-telegram-to-max-saas
   # Option B: Transfer via tar
   tar -czf - . | ssh root@server-ip "
     mkdir -p ~/apps/crossposting && cd ~/apps/crossposting && tar -xzf -
   "
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   nano .env
   ```
   Generate secure values:
   ```bash
   POSTGRES_PASSWORD=$(openssl rand -base64 32)
   JWT_SECRET_KEY=$(openssl rand -base64 48)
   ENCRYPTION_KEY=$(openssl rand -base64 32)
   ```
   Update all required variables (see Environment Variables section below).

4. **Create SSL certificates**:
   - For testing (self-signed):
     ```bash
     mkdir -p certs
     openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
       -keyout certs/key.pem -out certs/cert.pem \
       -subj "/CN=your-domain.com"
     ```
   - For production: Disable Cloudflare proxy, Let's Encrypt will auto-issue

5. **CRITICAL: Fix backend code bug** (before building):
   ```bash
   cd backend
   sed -i 's/await send_verification_email/send_verification_email/g' app/api/auth.py
   sed -i 's/await send_password_reset_email/send_password_reset_email/g' app/api/auth.py
   ```
   **Note:** `send_verification_email()` and `send_password_reset_email()` are NOT async functions but were being awaited.

6. **Update domain and configuration**:
   - Edit `docker-compose.prod.yml`
   - Replace `telegram-crossposting-saas.aiengineerhelper.com` with your domain in all Traefik labels
   - Update `TRAEFIK_ACME_EMAIL` to your email
   - Add `DOCKER_API_VERSION: 1.53` to traefik environment to prevent Docker connection errors

7. **Configure DNS** (if using Cloudflare):
   - For self-signed certs: Set SSL/TLS mode to "Flexible"
   - For Let's Encrypt: Disable Cloudflare proxy (gray cloud)

8. **Deploy**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

9. **Verify deployment**:
   ```bash
   # Check containers are running (should show 4)
   docker ps --filter "name=crossposter"

   # Test health endpoint
   curl -s -H 'Host:your-domain.com' http://localhost/health
   # Expected: {"status":"healthy"}

   # Test registration
   curl -X POST https://your-domain.com/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"testpass","captcha_token":"fake"}'
   ```

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

**Issue: Traefik "client version 1.24 is too old" error**
- Symptom: `Provider connection error: client version 1.24 is too old. Minimum supported API version is 1.44`
- Cause: Traefik container cannot communicate with Docker daemon
- Fix: Add `DOCKER_API_VERSION` environment variable to traefik service:
  ```yaml
  traefik:
    environment:
      - DOCKER_API_VERSION=1.53
  ```

**Issue: Backend Internal Server Error "object dict can't be used in 'await' expression"**
- Symptom: Registration endpoint fails with 500 error
- Cause: `send_verification_email()` and `send_password_reset_email()` are not async functions but being awaited
- Fix: Before building, edit `backend/app/api/auth.py`:
  ```bash
  sed -i 's/await send_verification_email/send_verification_email/g' backend/app/api/auth.py
  sed -i 's/await send_password_reset_email/send_password_reset_email/g' backend/app/api/auth.py
  ```

**Issue: Cloudflare Error 526 "Invalid SSL certificate"**
- Symptom: Cloudflare rejects connection to origin due to invalid SSL certificate
- Causes:
  - Using self-signed certificates with Cloudflare "Full" or "Full (strict)" SSL mode
  - Origin doesn't have trusted certificate
- Fixes:
  1. Set Cloudflare SSL/TLS mode to "Flexible" (allows HTTP from origin)
  2. Or disable Cloudflare proxy (gray cloud) and use direct A record
  3. Or use Let's Encrypt for trusted certificates (requires DNS-only mode)

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