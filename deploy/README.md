# Chitram Deployment

This directory contains all configuration needed to deploy Chitram.

## Directory Structure

```
deploy/
├── README.md                    # This file
├── .env.production.example      # Environment template (copy to .env.production)
├── docker-compose.yml           # Production compose with Caddy
├── docker-compose.local.yml     # Local override (exposes ports, no Caddy)
└── Caddyfile                    # Reverse proxy configuration
```

## Quick Start

### Local Development/Testing

```bash
cd deploy

# Start with local overrides (exposes all ports, no SSL)
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d

# Access:
# - Web UI:        http://localhost:8000
# - API Docs:      http://localhost:8000/docs
# - MinIO Console: http://localhost:9003 (minioadmin/minioadmin)
# - PostgreSQL:    localhost:5433
# - Redis:         localhost:6380
```

### Production Deployment

```bash
cd deploy

# 1. Create production environment file
cp .env.production.example .env.production

# 2. Edit with secure values (see SECRETS.md)
nano .env.production

# 3. Start production stack
docker compose --env-file .env.production up -d

# Access:
# - Web UI: https://your-domain.com
# - Health: https://your-domain.com/health
```

## Configuration

### Environment Variables

See [.env.production.example](.env.production.example) for all available options.

Key configurations:

| Variable | Description | Required |
|----------|-------------|----------|
| `DOMAIN` | Your domain for SSL | Yes (production) |
| `POSTGRES_PASSWORD` | Database password | Yes |
| `JWT_SECRET_KEY` | Auth token secret | Yes |
| `MINIO_SECRET_KEY` | Object storage secret | Yes |

### Generating Secrets

```bash
# Generate a secure password
openssl rand -base64 32

# Generate JWT secret
openssl rand -base64 64
```

## Common Commands

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f app
docker compose logs -f caddy
```

### Restart Services

```bash
# Restart all
docker compose --env-file .env.production restart

# Restart specific service
docker compose --env-file .env.production restart app
```

### Update Application

```bash
# Pull latest and rebuild
docker compose --env-file .env.production build app
docker compose --env-file .env.production up -d app
```

### Database Operations

```bash
# Access PostgreSQL
docker compose exec postgres psql -U chitram

# Backup database
docker compose exec postgres pg_dump -U chitram chitram > backup.sql

# Restore database
cat backup.sql | docker compose exec -T postgres psql -U chitram chitram
```

### Stop Everything

```bash
# Stop containers (keeps data)
docker compose down

# Stop and remove all data (DESTRUCTIVE)
docker compose down -v
```

## Architecture

```
Internet
    │
    ▼
┌─────────────────┐
│  Caddy (443)    │  ← SSL termination, reverse proxy
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  App (8000)     │  ← FastAPI application
└────────┬────────┘
         │
    ┌────┼────┐
    ▼    ▼    ▼
┌──────┐ ┌──────┐ ┌──────┐
│Postgres│ │MinIO │ │Redis │
│(5432) │ │(9000)│ │(6379)│
└──────┘ └──────┘ └──────┘
```

## Troubleshooting

### SSL Certificate Issues

```bash
# Check Caddy logs
docker compose logs caddy

# Force certificate renewal
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

### App Not Starting

```bash
# Check app logs
docker compose logs app

# Verify health
curl http://localhost:8000/health
```

### Database Connection Failed

1. Check PostgreSQL is running: `docker compose ps postgres`
2. Verify password matches in `DATABASE_URL` and `POSTGRES_PASSWORD`
3. Check logs: `docker compose logs postgres`

## Documentation

- [SECRETS.md](../docs/deployment/SECRETS.md) - Secret management guide
- [DEPLOYMENT_STRATEGY.md](../docs/deployment/DEPLOYMENT_STRATEGY.md) - Full deployment plan
