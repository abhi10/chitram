# Secrets Management

This document explains how to manage secrets for Chitram deployment.

## Overview

Secrets are managed through environment variables, loaded from a `.env.production` file that is **never committed to version control**.

## Quick Start

```bash
# 1. Navigate to deploy directory
cd deploy

# 2. Copy the template
cp .env.production.example .env.production

# 3. Generate secure values (see below)

# 4. Edit .env.production with your values
nano .env.production

# 5. Deploy
docker compose --env-file .env.production up -d
```

## Generating Secure Secrets

### Using OpenSSL (Recommended)

```bash
# For passwords (32 bytes, base64 encoded)
openssl rand -base64 32

# For JWT secret (64 bytes, base64 encoded)
openssl rand -base64 64
```

### Using Python

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Quick Generation Script

Run this to generate all secrets at once:

```bash
echo "# Generated Secrets - $(date)"
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)"
echo "MINIO_ROOT_PASSWORD=$(openssl rand -base64 32)"
echo "MINIO_SECRET_KEY=$(openssl rand -base64 32)"
echo "REDIS_PASSWORD=$(openssl rand -base64 32)"
echo "JWT_SECRET_KEY=$(openssl rand -base64 64)"
```

## Required Secrets

| Secret | Description | Minimum Length |
|--------|-------------|----------------|
| `POSTGRES_PASSWORD` | Database password | 32 chars |
| `MINIO_ROOT_PASSWORD` | MinIO admin password | 32 chars |
| `MINIO_SECRET_KEY` | MinIO access secret | 32 chars |
| `REDIS_PASSWORD` | Redis password (optional) | 32 chars |
| `JWT_SECRET_KEY` | Token signing key | 64 chars |

## Environment Variables Reference

### Application

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode (NEVER in production) |
| `DOMAIN` | `localhost` | Domain for SSL certificate |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `chitram` | Database username |
| `POSTGRES_PASSWORD` | - | Database password |
| `POSTGRES_DB` | `chitram` | Database name |
| `DATABASE_URL` | - | Full connection string |

### Object Storage (MinIO)

| Variable | Default | Description |
|----------|---------|-------------|
| `MINIO_ROOT_USER` | `minioadmin` | MinIO admin username |
| `MINIO_ROOT_PASSWORD` | - | MinIO admin password |
| `MINIO_ACCESS_KEY` | - | App access key |
| `MINIO_SECRET_KEY` | - | App secret key |
| `MINIO_BUCKET` | `images` | Bucket name |
| `MINIO_ENDPOINT` | `minio:9000` | Internal endpoint |
| `MINIO_SECURE` | `false` | Use HTTPS (internal) |

### Cache (Redis)

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | `redis` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_PASSWORD` | - | Redis password (optional) |
| `CACHE_ENABLED` | `true` | Enable caching |
| `CACHE_TTL_SECONDS` | `3600` | Cache TTL |
| `CACHE_KEY_PREFIX` | `chitram` | Key namespace |

### Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | - | Token signing secret |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token lifetime (24h) |

### Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |
| `RATE_LIMIT_PER_MINUTE` | `30` | Requests per minute |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Window size |

### Upload Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `UPLOAD_CONCURRENCY_LIMIT` | `10` | Max concurrent uploads |
| `MAX_FILE_SIZE_BYTES` | `5242880` | Max file size (5MB) |

## GitHub Actions Secrets

For CI/CD deployment, add these secrets to your GitHub repository:

| Secret | Description |
|--------|-------------|
| `DROPLET_HOST` | Server IP or hostname |
| `DROPLET_USER` | SSH username |
| `DROPLET_SSH_KEY` | Private SSH key (full content) |
| `PRODUCTION_ENV` | Contents of .env.production file |

### Adding Secrets to GitHub

1. Go to Repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each secret with its value

## Security Best Practices

### DO

- Generate unique secrets for each environment
- Use strong, random values (32+ characters)
- Rotate secrets periodically (every 90 days)
- Use different secrets for staging vs production
- Store backup of secrets in a password manager

### DON'T

- Commit `.env.production` to git
- Reuse secrets across environments
- Share secrets via chat/email
- Use predictable patterns
- Log secret values

## Rotating Secrets

### Database Password

```bash
# 1. Generate new password
NEW_PASS=$(openssl rand -base64 32)

# 2. Connect to postgres and change password
docker compose exec postgres psql -U chitram -c "ALTER USER chitram PASSWORD '$NEW_PASS';"

# 3. Update .env.production with new password

# 4. Restart app
docker compose --env-file .env.production up -d app
```

### JWT Secret

Changing JWT secret will invalidate all existing tokens (users must re-login):

```bash
# 1. Generate new secret
NEW_JWT=$(openssl rand -base64 64)

# 2. Update .env.production

# 3. Restart app
docker compose --env-file .env.production up -d app
```

## Troubleshooting

### "Permission denied" on .env.production

```bash
chmod 600 .env.production
```

### Secret not being read

1. Check file exists: `ls -la .env.production`
2. Check syntax: no spaces around `=`
3. Check quoting: use quotes for values with special characters

### Database connection failed after password change

Ensure `DATABASE_URL` uses the same password as `POSTGRES_PASSWORD`:

```bash
# These must match:
POSTGRES_PASSWORD=mysecretpass
DATABASE_URL=postgresql+asyncpg://chitram:mysecretpass@postgres:5432/chitram
```
