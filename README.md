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
- **Deployment**: Docker + Docker Compose

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

### Production

```bash
# Configure your environment variables
nano .env

# Build and start
docker-compose up -d
```

## Environment Variables

See [`.env.example`](.env.example) for all required configuration.

Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - Secret for JWT tokens (32+ chars)
- `SMTP_HOST/USER/PASSWORD` - Email configuration
- `CLOUDFLARE_TURNSTILE_SECRET` - Captcha secret
- `ENCRYPTION_KEY` - Key for token encryption (32 bytes)

## API Documentation

Once running, visit:
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Browser   │────▶│   Nginx      │────▶│  FastAPI    │
│   (React)   │     │  (Proxy)     │     │  Backend    │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
                              ┌──────────────────┼──────────────────┐
                              ▼                  ▼                  ▼
                    ┌─────────────────┐  ┌─────────────┐         ┌─────────────┐
                    │  PostgreSQL     │  │  Telegram   │         │  Max API    │
                    │  (Data Store)   │  │  Webhook    │         │  (Platform  │
                    │ (Async)         │  │  (Per user) │         │   API)      │
                    └─────────────────┘  └─────────────┘         └─────────────┘
```

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

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/       - FastAPI routes
│   │   ├── database/   - SQLAlchemy models
│   │   ├── schemas/    - Pydantic schemas
│   │   └── services/   - Business logic
├── frontend/
│   └── src/
│       ├── components/ - React components
│       ├── pages/      - Route components
│       └── services/   - API client
├── nginx/              - Reverse proxy config
├── tests/              - Automated tests with mocks
└── docker-compose.yml  - Service orchestration
```

## License

MIT
