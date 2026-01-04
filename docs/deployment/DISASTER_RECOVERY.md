# Disaster Recovery Guide

This document describes backup and recovery procedures for Chitram.

## Backup Strategy

| Data | Method | Frequency | Retention | Location |
|------|--------|-----------|-----------|----------|
| PostgreSQL | pg_dump | Daily | 7 days | /opt/chitram-backups |
| MinIO (images) | mc mirror | Daily | 7 days | /opt/chitram-backups |
| Redis | N/A | N/A | N/A | Cache only, rebuilds |

## Quick Commands

```bash
# Create backup
./scripts/backup.sh

# List backups
./scripts/backup.sh --list

# Restore from backup
./scripts/restore.sh 20240115-143022

# Clean old backups
./scripts/backup.sh --cleanup
```

## Backup Scripts

### Creating Backups

```bash
# Full backup (database + MinIO)
./scripts/backup.sh

# Database only
./scripts/backup.sh --db-only

# MinIO only
./scripts/backup.sh --minio-only
```

Backups are stored in `/opt/chitram-backups/` with timestamped filenames:
- Database: `db-YYYYMMDD-HHMMSS.sql.gz`
- MinIO: `minio-YYYYMMDD-HHMMSS/`

### Automated Backups (Cron)

Add to crontab on the production server:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/chitram/scripts/backup.sh >> /var/log/chitram-backup.log 2>&1

# Add weekly cleanup on Sunday at 3 AM
0 3 * * 0 /opt/chitram/scripts/backup.sh --cleanup >> /var/log/chitram-backup.log 2>&1
```

### Restoring from Backup

```bash
# List available backups
./scripts/restore.sh --list

# Full restore
./scripts/restore.sh 20240115-143022

# Database only
./scripts/restore.sh 20240115-143022 --db-only

# MinIO only
./scripts/restore.sh 20240115-143022 --minio-only

# Skip confirmation prompt
./scripts/restore.sh 20240115-143022 --force
```

## Recovery Scenarios

### Scenario 1: Application Crash (Container Died)

**Symptoms:** App returns 502/503 errors, health check fails

**Recovery:**
```bash
cd /opt/chitram/deploy

# Check container status
docker compose ps

# Restart failed container
docker compose restart app

# Check logs
docker compose logs app --tail=50

# If still failing, recreate container
docker compose up -d app --force-recreate
```

### Scenario 2: Database Corruption

**Symptoms:** API errors, data inconsistencies

**Recovery:**
```bash
cd /opt/chitram

# Stop the application
docker compose -f deploy/docker-compose.yml stop app

# List available backups
./scripts/restore.sh --list

# Restore database from latest backup
./scripts/restore.sh YYYYMMDD-HHMMSS --db-only

# Restart application
docker compose -f deploy/docker-compose.yml start app

# Verify
curl http://localhost:8000/health
```

### Scenario 3: Image Storage Corruption

**Symptoms:** Images return 404, thumbnails missing

**Recovery:**
```bash
cd /opt/chitram

# Restore MinIO objects
./scripts/restore.sh YYYYMMDD-HHMMSS --minio-only

# Clear Redis cache (thumbnails will regenerate)
docker compose -f deploy/docker-compose.yml exec redis redis-cli FLUSHALL

# Verify
curl http://localhost:8000/health
```

### Scenario 4: Full Server Failure

**Symptoms:** Server unreachable, all services down

**Recovery Steps:**

1. **Provision new droplet** (see [DROPLET_SETUP.md](DROPLET_SETUP.md))

2. **Copy backup files** from off-site storage to new server:
   ```bash
   scp -r backups/ root@new-server:/opt/chitram-backups/
   ```

3. **Deploy application:**
   ```bash
   # Clone repository
   git clone https://github.com/abhi10/chitram.git /opt/chitram
   cd /opt/chitram/deploy

   # Create .env.production (use same secrets as before)
   cp .env.production.example .env.production
   nano .env.production

   # Start services
   docker compose --env-file .env.production up -d
   ```

4. **Restore data:**
   ```bash
   cd /opt/chitram
   ./scripts/restore.sh YYYYMMDD-HHMMSS
   ```

5. **Update DNS** to point to new server IP

6. **Verify:**
   ```bash
   curl https://your-domain.com/health
   ```

### Scenario 5: Accidental Data Deletion

**Symptoms:** User reports missing images

**Recovery:**
```bash
# If recent (within cache TTL), data might still be in cache
# Otherwise, restore from backup

cd /opt/chitram

# Check what backups are available
./scripts/restore.sh --list

# For partial restore, you may need to:
# 1. Create a temporary database
# 2. Restore backup to temp DB
# 3. Copy specific records back to production

# For full restore:
./scripts/restore.sh YYYYMMDD-HHMMSS
```

## Off-Site Backup

For additional safety, sync backups to external storage:

### Option 1: DigitalOcean Spaces (S3-compatible)

```bash
# Install s3cmd
apt install s3cmd

# Configure
s3cmd --configure

# Sync backups daily (add to cron)
s3cmd sync /opt/chitram-backups/ s3://your-backup-bucket/chitram/
```

### Option 2: rsync to another server

```bash
# Add to cron
rsync -avz /opt/chitram-backups/ backup-user@backup-server:/backups/chitram/
```

## Testing Backups

Regularly verify backups work:

```bash
# 1. Create a test backup
./scripts/backup.sh

# 2. Start a separate test environment
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d

# 3. Restore to test environment
BACKUP_DIR=/opt/chitram-backups ./scripts/restore.sh YYYYMMDD-HHMMSS --force

# 4. Verify data
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/images  # Should show restored images

# 5. Clean up test environment
docker compose -f docker-compose.yml -f docker-compose.local.yml down -v
```

## Contact & Escalation

If you cannot recover from a disaster:

1. Check application logs: `docker compose logs`
2. Check system logs: `journalctl -xe`
3. Review this document for applicable scenarios
4. If data is unrecoverable, restore from the most recent backup

## Recovery Time Objectives

| Component | RTO (Recovery Time) | RPO (Data Loss) |
|-----------|---------------------|-----------------|
| Application | < 5 minutes | 0 |
| Database | < 15 minutes | Up to 24 hours |
| Images | < 30 minutes | Up to 24 hours |
| Full system | < 1 hour | Up to 24 hours |

RTO assumes backups are available and accessible.
RPO is based on daily backup schedule.
