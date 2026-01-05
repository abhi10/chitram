# Deployment Retrospective: Phase 4 Production Deploy

**Date:** January 2025
**Environment:** DigitalOcean Droplet (Ubuntu 22.04, 2 vCPU, 2GB RAM)
**Outcome:** Successful deployment to http://157.230.139.161

---

## Executive Summary

The Phase 4 deployment encountered 8 significant issues during the manual droplet setup and CD pipeline configuration. All issues were resolved, and the application is now running in production with automated deployments and scheduled backups.

**Time Impact:** Issues added approximately 3-4 hours to the deployment process.

---

## Issues Encountered

### 1. MinIO Credential Mismatch

| Category | Details |
|----------|---------|
| **Symptom** | App container in restart loop; logs showed `SignatureDoesNotMatch` error |
| **Root Cause** | `.env.production` had different values for `MINIO_ROOT_PASSWORD` and `MINIO_SECRET_KEY` |
| **Why It Happened** | Template had placeholder values; user generated separate passwords for each field |
| **Fix** | Set both to the same value, then reset MinIO volume: `docker volume rm chitram-minio-data` |
| **Prevention** | Add validation comment in `.env.production.example` noting these must match |

**Error Log:**
```
minio  | API: SYSTEM()
minio  | Time: ...
minio  | Error: SignatureDoesNotMatch: The request signature we calculated does not match
```

---

### 2. SQLite/aiosqlite Missing in CD Build Verification

| Category | Details |
|----------|---------|
| **Symptom** | CD pipeline failed at "Verify image runs" step |
| **Root Cause** | Production Docker image excludes dev dependencies (`uv sync --no-dev`); aiosqlite is dev-only |
| **Why It Happened** | CD verification step used SQLite for quick test, but SQLite driver wasn't in prod image |
| **Fix** | Changed CD to use PostgreSQL container for verification instead of SQLite |
| **Prevention** | CD verification should mirror production environment exactly |

**Error Log:**
```
ModuleNotFoundError: No module named 'aiosqlite'
```

**Before:**
```yaml
docker run -d --name test-app \
  -e DATABASE_URL=sqlite+aiosqlite:///test.db \
  ...
```

**After:**
```yaml
docker run -d --name test-postgres ...
docker run -d --name test-app \
  --link test-postgres:postgres \
  -e DATABASE_URL=postgresql+asyncpg://test:test@postgres:5432/test \
  ...
```

---

### 3. SSH Key Passphrase Protected

| Category | Details |
|----------|---------|
| **Symptom** | CD pipeline failed with SSH authentication error |
| **Root Cause** | GitHub Secrets contained a passphrase-protected SSH key |
| **Why It Happened** | User's default SSH key had a passphrase; CI/CD requires non-interactive authentication |
| **Fix** | Generated new passphrase-free key: `ssh-keygen -t ed25519 -f ~/.ssh/chitram_deploy -N ""` |
| **Prevention** | Document that deploy keys must be passphrase-free |

**Commands to fix:**
```bash
# Generate passphrase-free key
ssh-keygen -t ed25519 -C "chitram-deploy" -f ~/.ssh/chitram_deploy -N ""

# Add to droplet
cat ~/.ssh/chitram_deploy.pub >> ~/.ssh/authorized_keys

# Update GitHub Secret DROPLET_SSH_KEY with private key content
cat ~/.ssh/chitram_deploy
```

---

### 4. Sudo Requires Password in CD

| Category | Details |
|----------|---------|
| **Symptom** | CD deploy step hung, then timed out |
| **Root Cause** | Deploy script uses `sudo` but non-interactive SSH can't provide password |
| **Why It Happened** | Non-root user `chitram` was created following security best practices, but passwordless sudo wasn't configured |
| **Fix** | Added passwordless sudo for chitram user |
| **Prevention** | Include in DROPLET_SETUP.md as required step for CD |

**Command:**
```bash
echo "chitram ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/chitram
```

---

### 5. Backup Script Container Status Check

| Category | Details |
|----------|---------|
| **Symptom** | `backup.sh` reported "PostgreSQL container is not running" when it was running |
| **Root Cause** | Script grepped for "running" but `docker compose ps` shows "Up" |
| **Why It Happened** | Docker Compose output format varies; script assumed specific format |
| **Fix** | Changed grep pattern from `grep -q "running"` to `grep -qE "(running|Up)"` |
| **Prevention** | Test scripts against actual docker compose output on target environment |

**Before:**
```bash
if ! docker compose ps postgres | grep -q "running"; then
```

**After:**
```bash
if ! docker compose ps postgres | grep -qE "(running|Up)"; then
```

---

### 6. Scripts Folder Not Deployed

| Category | Details |
|----------|---------|
| **Symptom** | Backup cron job failed; `/opt/chitram/scripts/backup.sh` not found |
| **Root Cause** | CD workflow tar command didn't include `scripts/` directory |
| **Why It Happened** | Original CD was written before backup scripts existed (Phase 4E) |
| **Fix** | Added `scripts/` to the tar archive in CD workflow |
| **Prevention** | Review CD package contents when adding new directories |

**Before:**
```yaml
tar -czvf deploy-package.tar.gz \
  backend/ \
  deploy/docker-compose.yml \
  deploy/Caddyfile
```

**After:**
```yaml
tar -czvf deploy-package.tar.gz \
  backend/ \
  deploy/docker-compose.yml \
  deploy/docker-compose.local.yml \
  deploy/Caddyfile \
  scripts/
```

---

### 7. Health Check Port Mismatch

| Category | Details |
|----------|---------|
| **Symptom** | CD reported deployment failed even though app was running |
| **Root Cause** | Health check used `localhost:8000` but app port only exposed internally via Docker network |
| **Why It Happened** | Port 8000 is internal; Caddy exposes on port 80 |
| **Fix** | Changed health checks to use `localhost/health` (port 80) |
| **Prevention** | Document that external access is via Caddy (80/443), not direct app port |

**Before:**
```bash
curl -sf http://localhost:8000/health
```

**After:**
```bash
curl -sf http://localhost/health
```

---

### 8. Caddy HTTPS Redirect with IP Address

| Category | Details |
|----------|---------|
| **Symptom** | Accessing `http://<IP>` redirected to `https://localhost/` which returned 404 |
| **Root Cause** | Caddyfile configured with `{$DOMAIN:localhost}` - designed for domain names with auto-HTTPS |
| **Why It Happened** | Caddy auto-provisions HTTPS for domains; IP addresses don't get certificates, causing fallback to localhost |
| **Fix** | Created HTTP-only Caddyfile on droplet for IP-only access |
| **Prevention** | Document IP-only configuration in troubleshooting; consider environment-aware Caddyfile |

**Additional Issue:** Browser cached the HTTPS redirect (HSTS), requiring incognito window to access.

**HTTP-only Caddyfile:**
```
:80 {
    reverse_proxy app:8000
    encode gzip zstd
    header {
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
        -Server
    }
    log {
        output stdout
        format json
        level INFO
    }
}
```

---

## Summary of Fixes Applied

| File | Change |
|------|--------|
| `.github/workflows/cd.yml` | Use PostgreSQL for image verification |
| `.github/workflows/cd.yml` | Include `scripts/` in deployment package |
| `.github/workflows/cd.yml` | Health checks use port 80 (Caddy) |
| `scripts/backup.sh` | grep pattern handles "Up" and "running" |
| `docs/deployment/DROPLET_SETUP.md` | Added IP-only Caddyfile guide |
| Droplet: `/etc/sudoers.d/chitram` | Passwordless sudo for deploy user |
| Droplet: `~/.ssh/authorized_keys` | Added passphrase-free deploy key |
| Droplet: `/opt/chitram/deploy/Caddyfile` | HTTP-only config for IP access |

---

## Lessons Learned

### 1. Environment Parity
CD verification should exactly mirror production environment. Using SQLite as a shortcut exposed a dependency gap.

### 2. Credential Validation
Environment templates should include validation comments and examples showing when values must match.

### 3. CI/CD Authentication
Deploy keys must be passphrase-free. Document this requirement prominently.

### 4. Docker Output Parsing
Don't assume Docker CLI output format. Use flexible patterns or Docker inspect/API for reliable status checks.

### 5. Network Architecture Awareness
Understand which ports are internal vs external. Document the request flow: Client -> Caddy (80/443) -> App (8000).

### 6. Deployment Package Completeness
Review CD package contents after adding new directories or scripts to the repository.

### 7. Domain vs IP Access
Caddy's automatic HTTPS is great for domains but requires manual configuration for IP-only access.

---

## Recommendations for Future Deployments

1. **Pre-deployment Checklist:** Create a validation script that checks:
   - Environment variable consistency (matching credentials)
   - Required directories exist
   - SSH key is passphrase-free
   - Sudo access configured

2. **Staging Environment:** Consider a staging droplet to catch CD issues before production.

3. **Domain Setup Early:** Configure domain and DNS before deployment to avoid IP-only workarounds.

4. **Monitoring:** Add uptime monitoring (e.g., UptimeRobot) to detect issues between deployments.

5. **Runbook:** Convert this retro into a runbook with quick-fix commands for common issues.
