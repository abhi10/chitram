# Chitram Deployment Strategy

## Overview

This document outlines the deployment strategy for Chitram, the image hosting application. The goal is to deploy to a single DigitalOcean droplet with CI/CD automation, SSL, monitoring, and backup capabilities.

**Target Cost: ~$18-24/month** for beta deployment.

---

## Architecture

```
                                    DigitalOcean Droplet ($18/month)
                                    ┌─────────────────────────────────────┐
[Users] ──HTTPS──> [Caddy] ──────> │  ┌─────────────────────────────┐   │
                   (SSL/Proxy)      │  │     FastAPI App (8000)      │   │
                                    │  │     - Web UI                │   │
[GitHub] ──push──> [Actions] ─SSH─> │  │     - REST API              │   │
                                    │  └─────────────────────────────┘   │
                                    │              │                     │
                                    │  ┌───────────┼───────────┐         │
                                    │  │           │           │         │
                                    │  ▼           ▼           ▼         │
                                    │ PostgreSQL  MinIO      Redis       │
                                    │ (5432)     (9000)     (6379)       │
                                    │                                    │
                                    │ [Docker Compose orchestrates all]  │
                                    └─────────────────────────────────────┘
```

---

## What is Caddy and Why Do We Need It?

### What is Caddy?

Caddy is a modern, open-source web server written in Go. It's an alternative to nginx/Apache with a focus on simplicity and automatic HTTPS.

### Why Caddy Over nginx?

| Feature | Caddy | nginx |
|---------|-------|-------|
| **Automatic HTTPS** | ✅ Built-in (Let's Encrypt) | ❌ Manual certbot setup |
| **Configuration** | 5-10 lines | 50+ lines |
| **Certificate Renewal** | Automatic | Cron job required |
| **Zero-downtime reload** | ✅ Built-in | ✅ With signals |
| **Learning curve** | Low | Medium |
| **Performance** | Excellent | Excellent |

### What Caddy Does For Us

1. **SSL/TLS Termination** - Handles HTTPS, encrypts traffic between users and server
2. **Automatic Certificates** - Gets and renews Let's Encrypt certificates automatically
3. **Reverse Proxy** - Routes requests to our FastAPI app on port 8000
4. **Security Headers** - Adds HSTS, X-Frame-Options, etc.
5. **Compression** - Gzip/Brotli compression for faster responses

### Example Caddyfile (Our Config)

```caddyfile
chitram.example.com {
    reverse_proxy app:8000

    # Optional: Rate limiting at edge
    # Optional: Basic auth for admin routes
}
```

That's it. Caddy handles:
- Getting SSL certificate from Let's Encrypt
- Redirecting HTTP → HTTPS
- Renewing certificates before expiry
- Proxying to our app

### Without Caddy (Why We Need a Reverse Proxy)

If we exposed FastAPI directly:
- ❌ No HTTPS (browsers show "Not Secure")
- ❌ Port 8000 exposed (non-standard, looks unprofessional)
- ❌ No protection against slowloris/DDoS at edge
- ❌ No request buffering (large uploads could block workers)

---

## Implementation Phases

### Phase 4A: Security & Secrets (Pre-requisite)
**Priority: Critical | Effort: 2 hours | Status: COMPLETE**

**Goal:** Externalize all secrets from docker-compose.yml

**Files Created:**
- `deploy/.env.production.example` - Environment template
- `deploy/docker-compose.yml` - Production compose with env vars
- `deploy/docker-compose.local.yml` - Local development override
- `deploy/Caddyfile` - Reverse proxy configuration
- `deploy/validate-local.sh` - Automated validation script
- `docs/deployment/SECRETS.md` - Secrets documentation

**How to Test Phase 4A:**
```bash
cd deploy
./validate-local.sh           # Automated: starts containers, health checks
./validate-local.sh --cleanup # Stop and clean up
```

**Secrets Required:**
| Secret | Description | How to Generate |
|--------|-------------|-----------------|
| `POSTGRES_PASSWORD` | Database password | `openssl rand -base64 32` |
| `JWT_SECRET_KEY` | Token signing key | `openssl rand -base64 64` |
| `MINIO_ACCESS_KEY` | Object storage access | `openssl rand -base64 20` |
| `MINIO_SECRET_KEY` | Object storage secret | `openssl rand -base64 40` |

---

### Phase 4B: CD Pipeline
**Priority: Critical | Effort: 3 hours | Status: COMPLETE**

**Goal:** Automated deployment on push to main with mandatory pre-deploy testing

**Pipeline Steps:**
```
Push to main
    │
    ▼
┌─────────────────────────────────────────┐
│  Step 1: Pre-Deploy Tests               │
│  - Run full test suite (postgres,       │
│    redis, minio)                        │
│  - Must pass before deployment          │
└─────────────────────────────────────────┘
    │ ✓ Pass
    ▼
┌─────────────────────────────────────────┐
│  Step 2: Build Docker Image             │
│  - Build and tag image                  │
│  - Verify image starts successfully     │
└─────────────────────────────────────────┘
    │ ✓ Pass
    ▼
┌─────────────────────────────────────────┐
│  Step 3: Deploy to Production           │
│  - SSH to droplet                       │
│  - Backup current deployment            │
│  - Deploy new version                   │
│  - Health check verification            │
│  - Auto-rollback on failure             │
└─────────────────────────────────────────┘
```

**Files Created:**
- `.github/workflows/cd.yml` - Full CD pipeline with tests

**Testing Strategy:**
| Step | What's Tested | Failure Action |
|------|---------------|----------------|
| Pre-Deploy Tests | Full pytest suite with real services | Block deployment |
| Build | Docker image builds and starts | Block deployment |
| Deploy | Health check on production | Auto-rollback |

**GitHub Secrets Required:**
| Secret | Description |
|--------|-------------|
| `DROPLET_HOST` | Droplet IP or hostname |
| `DROPLET_USER` | SSH username (usually `root`) |
| `DROPLET_SSH_KEY` | Private SSH key |

**How to Test Phase 4B:**
1. Verify workflow syntax: Push branch, check Actions tab for errors
2. Without droplet: Tests and build steps will run, deploy will fail (expected)
3. With droplet: Full pipeline including deployment and health check

---

### Phase 4C: Reverse Proxy & SSL
**Priority: High | Effort: 2 hours | Status: COMPLETE (included in Phase 4A)**

**Goal:** HTTPS with automatic certificate management

> **Note:** Caddy configuration was included in Phase 4A implementation.

**Files Created (in Phase 4A):**
- `deploy/Caddyfile` - Automatic HTTPS, security headers, compression
- `deploy/docker-compose.yml` - Includes Caddy service

**Port Exposure (Production):**
| Service | Exposed | Access |
|---------|---------|--------|
| Caddy | 80:80, 443:443 | Public (SSL termination) |
| App | internal only | Via Caddy reverse proxy |
| PostgreSQL | internal only | Container network |
| MinIO | internal only | Container network |
| Redis | internal only | Container network |

**How to Test Phase 4C:**
1. Local (no SSL): `./validate-local.sh` - uses docker-compose.local.yml
2. Production: Deploy to droplet with domain → verify https:// works

---

### Phase 4D: Monitoring & Alerting
**Priority: Low | Status: DESCOPED for MVP**

> **Note:** Monitoring is descoped for initial deployment. The `/health` endpoint exists for manual checks. External monitoring (UptimeRobot, Betterstack) can be added post-launch if needed.

**Future Tasks (when revisited):**
- Set up external uptime monitoring
- Configure Slack/email notifications
- Add log rotation

---

### Phase 4E: Backup & Recovery
**Priority: High | Effort: 3 hours | Status: COMPLETE**

**Goal:** Don't lose user data

**Files Created:**
- `scripts/backup.sh` - Backup PostgreSQL and MinIO
- `scripts/restore.sh` - Restore from backup
- `docs/deployment/DISASTER_RECOVERY.md` - Recovery procedures

**Backup Strategy:**
| Data | Method | Frequency | Retention |
|------|--------|-----------|-----------|
| PostgreSQL | pg_dump | Daily | 7 days |
| MinIO (images) | mc mirror | Daily | 7 days |
| Redis | Not backed up | N/A | Cache only, rebuilds |

**Usage:**
```bash
# Create backup
./scripts/backup.sh

# List backups
./scripts/backup.sh --list

# Restore
./scripts/restore.sh YYYYMMDD-HHMMSS

# Cleanup old backups
./scripts/backup.sh --cleanup
```

**How to Test Phase 4E:**
1. Run backup script: `./scripts/backup.sh`
2. Verify backup files in `/opt/chitram-backups/`
3. Run restore: `./scripts/restore.sh <timestamp>`
4. Verify data restored correctly

---

### Phase 4F: Droplet Setup (Manual, One-time)
**Priority: Required | Effort: 1 hour | Status: COMPLETE (Documentation Ready)**

**Goal:** Provision and configure the production server

**Documentation Created:**
- `docs/deployment/DROPLET_SETUP.md` - Complete step-by-step guide

**Droplet Specs:**
- **Size:** Basic, 2GB RAM, 2 vCPU, 50GB SSD ($18/month)
- **Region:** Closest to target users
- **Image:** Ubuntu 22.04 LTS
- **Authentication:** SSH keys only (no password)

**Setup Steps (see DROPLET_SETUP.md for details):**
1. Create DigitalOcean droplet
2. Configure firewall (ufw: 22, 80, 443)
3. Install Docker and Docker Compose
4. Configure DNS (optional, for SSL)
5. Deploy application
6. Configure GitHub Secrets for CD
7. Set up automated backups

**How to Test Phase 4F:**
1. SSH to droplet: `ssh root@<droplet-ip>`
2. Verify Docker: `docker --version && docker compose version`
3. Verify firewall: `sudo ufw status`
4. Verify health: `curl http://localhost:8000/health`
5. Trigger CD pipeline from GitHub

---

## File Structure After Implementation

```
chitram/
├── .github/
│   └── workflows/
│       ├── ci.yml              # Existing: lint, test
│       └── deploy.yml          # NEW: CD pipeline
├── deploy/
│   ├── .env.production.example # NEW: Secrets template
│   ├── Caddyfile               # NEW: Reverse proxy config
│   └── docker-compose.prod.yml # MOVED & UPDATED
├── scripts/
│   ├── backup.sh               # NEW: Backup automation
│   ├── restore.sh              # NEW: Recovery script
│   └── deploy.sh               # NEW: Remote deploy script
├── docs/
│   └── deployment/
│       ├── DEPLOYMENT_STRATEGY.md  # This file
│       ├── SECRETS.md              # NEW: Secrets documentation
│       ├── DROPLET_SETUP.md        # NEW: Server setup guide
│       └── DISASTER_RECOVERY.md    # NEW: Recovery procedures
└── docker-compose.prod.yml     # UPDATE: Use env vars, add Caddy
```

---

## Cost Summary

| Component | Monthly Cost |
|-----------|--------------|
| DigitalOcean Droplet (2GB) | $18 |
| Domain (optional) | ~$1 (annual) |
| SSL Certificate | Free (Let's Encrypt) |
| Monitoring | Free (UptimeRobot) |
| **Total** | **~$18-20/month** |

---

## Migration Path (When to Scale)

| Trigger | Action | New Cost |
|---------|--------|----------|
| Storage > 40GB | Add DigitalOcean Volume | +$10/month |
| High DB load | Managed PostgreSQL | +$15/month |
| Traffic spikes | Upgrade droplet (4GB) | +$6/month |
| Need redundancy | Add load balancer + 2nd droplet | +$30/month |

---

## Next Steps

1. [x] Phase 4A: Externalize secrets
2. [x] Phase 4B: Create CD pipeline
3. [x] Phase 4C: Add Caddy for SSL (included in 4A)
4. [ ] ~~Phase 4D: Set up monitoring~~ (DESCOPED for MVP)
5. [x] Phase 4E: Create backup scripts
6. [x] Phase 4F: Droplet setup documentation
7. [ ] First deployment!

---

## References

- [Caddy Documentation](https://caddyserver.com/docs/)
- [DigitalOcean Docker Guide](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04)
- [GitHub Actions SSH Deploy](https://github.com/appleboy/ssh-action)
- [Let's Encrypt](https://letsencrypt.org/)
