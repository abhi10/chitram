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
**Priority: Critical | Effort: 2 hours**

**Goal:** Externalize all secrets from docker-compose.yml

**Tasks:**
1. Create `.env.production.example` template
2. Update `docker-compose.prod.yml` to use environment variables
3. Document required GitHub Secrets
4. Generate secure random values for production

**Files to Create/Modify:**
- `deploy/.env.production.example` (template)
- `docker-compose.prod.yml` (use ${VAR} syntax)
- `docs/deployment/SECRETS.md` (documentation)

**Secrets Required:**
| Secret | Description | How to Generate |
|--------|-------------|-----------------|
| `POSTGRES_PASSWORD` | Database password | `openssl rand -base64 32` |
| `JWT_SECRET_KEY` | Token signing key | `openssl rand -base64 64` |
| `MINIO_ACCESS_KEY` | Object storage access | `openssl rand -base64 20` |
| `MINIO_SECRET_KEY` | Object storage secret | `openssl rand -base64 40` |

---

### Phase 4B: CD Pipeline
**Priority: Critical | Effort: 3 hours**

**Goal:** Automated deployment on push to main

**Tasks:**
1. Create `.github/workflows/deploy.yml`
2. Set up SSH key authentication
3. Add deployment scripts
4. Configure GitHub Secrets for SSH access

**Workflow:**
```
Push to main → CI passes → SSH to droplet → docker-compose pull → docker-compose up -d
```

**Files to Create:**
- `.github/workflows/deploy.yml`
- `scripts/deploy.sh` (remote deployment script)

**GitHub Secrets Required:**
| Secret | Description |
|--------|-------------|
| `DROPLET_HOST` | Droplet IP or hostname |
| `DROPLET_USER` | SSH username (usually `root`) |
| `DROPLET_SSH_KEY` | Private SSH key |

---

### Phase 4C: Reverse Proxy & SSL
**Priority: High | Effort: 2 hours**

**Goal:** HTTPS with automatic certificate management

**Tasks:**
1. Add Caddy service to docker-compose
2. Create Caddyfile configuration
3. Update firewall (only expose 80/443)
4. Remove direct port exposure for internal services

**Files to Create/Modify:**
- `deploy/Caddyfile`
- `docker-compose.prod.yml` (add caddy service)

**Port Changes:**
| Service | Before | After |
|---------|--------|-------|
| App | 8000:8000 | internal only |
| PostgreSQL | 5433:5432 | internal only |
| MinIO API | 9002:9000 | internal only |
| MinIO Console | 9003:9001 | internal only |
| Redis | 6380:6379 | internal only |
| Caddy | N/A | 80:80, 443:443 |

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
**Priority: High | Effort: 3 hours**

**Goal:** Don't lose user data

**Tasks:**
1. Create database backup script (pg_dump)
2. Create MinIO backup script (mc mirror)
3. Set up cron jobs for automated backups
4. Document recovery procedures
5. Test restore process

**Backup Strategy:**
| Data | Method | Frequency | Retention |
|------|--------|-----------|-----------|
| PostgreSQL | pg_dump | Daily | 7 days |
| MinIO (images) | mc mirror | Daily | 7 days |
| Redis | Not backed up | N/A | Cache only, rebuilds |

**Files to Create:**
- `scripts/backup.sh`
- `scripts/restore.sh`
- `docs/deployment/DISASTER_RECOVERY.md`

---

### Phase 4F: Droplet Setup (Manual, One-time)
**Priority: Required | Effort: 1 hour**

**Goal:** Provision and configure the production server

**Tasks:**
1. Create DigitalOcean droplet (Ubuntu 22.04, 2GB RAM)
2. Install Docker and Docker Compose
3. Configure firewall (ufw)
4. Set up SSH key authentication
5. Configure DNS (A record pointing to droplet IP)

**Droplet Specs:**
- **Size:** Basic, 2GB RAM, 2 vCPU, 50GB SSD ($18/month)
- **Region:** Closest to target users
- **Image:** Ubuntu 22.04 LTS
- **Authentication:** SSH keys only (no password)

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

1. [ ] Phase 4A: Externalize secrets
2. [ ] Phase 4B: Create CD pipeline
3. [ ] Phase 4C: Add Caddy for SSL
4. [ ] ~~Phase 4D: Set up monitoring~~ (DESCOPED for MVP)
5. [ ] Phase 4E: Create backup scripts
6. [ ] Phase 4F: Provision droplet (manual)
7. [ ] First deployment!

---

## References

- [Caddy Documentation](https://caddyserver.com/docs/)
- [DigitalOcean Docker Guide](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04)
- [GitHub Actions SSH Deploy](https://github.com/appleboy/ssh-action)
- [Let's Encrypt](https://letsencrypt.org/)
