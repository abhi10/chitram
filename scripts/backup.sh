#!/bin/bash
# Chitram Backup Script
# ====================
#
# Creates backups of PostgreSQL database and MinIO objects.
# Run from the deploy/ directory or set DEPLOY_DIR environment variable.
#
# Usage:
#   ./scripts/backup.sh                    # Full backup (DB + MinIO)
#   ./scripts/backup.sh --db-only          # Database only
#   ./scripts/backup.sh --minio-only       # MinIO objects only
#   ./scripts/backup.sh --list             # List existing backups
#   ./scripts/backup.sh --cleanup          # Remove backups older than RETENTION_DAYS
#
# Environment Variables:
#   DEPLOY_DIR        - Path to deploy directory (default: ../deploy relative to script)
#   BACKUP_DIR        - Where to store backups (default: /opt/chitram-backups)
#   RETENTION_DAYS    - Days to keep backups (default: 7)
#   COMPOSE_FILE      - Docker compose file (default: docker-compose.yml)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="${DEPLOY_DIR:-$SCRIPT_DIR/../deploy}"
BACKUP_DIR="${BACKUP_DIR:-/opt/chitram-backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

print_step() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

show_help() {
    echo "Chitram Backup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --db-only      Backup database only"
    echo "  --minio-only   Backup MinIO objects only"
    echo "  --list         List existing backups"
    echo "  --cleanup      Remove old backups (older than $RETENTION_DAYS days)"
    echo "  --help         Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  BACKUP_DIR       Backup location (default: /opt/chitram-backups)"
    echo "  RETENTION_DAYS   Days to keep backups (default: 7)"
    echo ""
}

list_backups() {
    print_step "Existing backups in $BACKUP_DIR"

    if [[ ! -d "$BACKUP_DIR" ]]; then
        print_warning "Backup directory does not exist"
        return
    fi

    echo ""
    echo "Database backups:"
    ls -lh "$BACKUP_DIR"/db-*.sql.gz 2>/dev/null || echo "  (none)"

    echo ""
    echo "MinIO backups:"
    ls -lhd "$BACKUP_DIR"/minio-* 2>/dev/null || echo "  (none)"

    echo ""
    echo "Disk usage:"
    du -sh "$BACKUP_DIR" 2>/dev/null || echo "  N/A"
}

cleanup_old_backups() {
    print_step "Cleaning up backups older than $RETENTION_DAYS days"

    if [[ ! -d "$BACKUP_DIR" ]]; then
        print_warning "Backup directory does not exist"
        return
    fi

    # Find and remove old database backups
    OLD_DB_BACKUPS=$(find "$BACKUP_DIR" -name "db-*.sql.gz" -mtime +$RETENTION_DAYS 2>/dev/null || true)
    if [[ -n "$OLD_DB_BACKUPS" ]]; then
        echo "$OLD_DB_BACKUPS" | xargs rm -f
        print_success "Removed old database backups"
    fi

    # Find and remove old MinIO backups
    OLD_MINIO_BACKUPS=$(find "$BACKUP_DIR" -maxdepth 1 -name "minio-*" -type d -mtime +$RETENTION_DAYS 2>/dev/null || true)
    if [[ -n "$OLD_MINIO_BACKUPS" ]]; then
        echo "$OLD_MINIO_BACKUPS" | xargs rm -rf
        print_success "Removed old MinIO backups"
    fi

    print_success "Cleanup complete"
}

backup_database() {
    print_step "Backing up PostgreSQL database..."

    # Create backup directory
    mkdir -p "$BACKUP_DIR"

    BACKUP_FILE="$BACKUP_DIR/db-$TIMESTAMP.sql.gz"

    # Get database credentials from environment or use defaults
    cd "$DEPLOY_DIR"

    # Check if postgres container is running
    if ! docker compose -f "$COMPOSE_FILE" ps postgres | grep -q "running"; then
        print_error "PostgreSQL container is not running"
        return 1
    fi

    # Perform backup using pg_dump
    docker compose -f "$COMPOSE_FILE" exec -T postgres \
        pg_dump -U "${POSTGRES_USER:-chitram}" "${POSTGRES_DB:-chitram}" \
        | gzip > "$BACKUP_FILE"

    # Verify backup
    if [[ -s "$BACKUP_FILE" ]]; then
        BACKUP_SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
        print_success "Database backup created: $BACKUP_FILE ($BACKUP_SIZE)"
    else
        print_error "Database backup failed - file is empty"
        rm -f "$BACKUP_FILE"
        return 1
    fi
}

backup_minio() {
    print_step "Backing up MinIO objects..."

    # Create backup directory
    mkdir -p "$BACKUP_DIR"

    MINIO_BACKUP_DIR="$BACKUP_DIR/minio-$TIMESTAMP"
    mkdir -p "$MINIO_BACKUP_DIR"

    cd "$DEPLOY_DIR"

    # Check if minio container is running
    if ! docker compose -f "$COMPOSE_FILE" ps minio | grep -q "running"; then
        print_error "MinIO container is not running"
        return 1
    fi

    # Get MinIO credentials
    MINIO_ACCESS="${MINIO_ACCESS_KEY:-minioadmin}"
    MINIO_SECRET="${MINIO_SECRET_KEY:-minioadmin}"
    MINIO_BUCKET="${MINIO_BUCKET:-images}"

    # Use mc (MinIO Client) inside a container to mirror the bucket
    docker run --rm \
        --network "${COMPOSE_PROJECT_NAME:-deploy}_chitram-network" \
        -v "$MINIO_BACKUP_DIR:/backup" \
        minio/mc:latest \
        /bin/sh -c "
            mc alias set chitram http://minio:9000 $MINIO_ACCESS $MINIO_SECRET --api S3v4 &&
            mc mirror chitram/$MINIO_BUCKET /backup/$MINIO_BUCKET
        " 2>/dev/null

    # Verify backup
    OBJECT_COUNT=$(find "$MINIO_BACKUP_DIR" -type f 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$OBJECT_COUNT" -gt 0 ]]; then
        BACKUP_SIZE=$(du -sh "$MINIO_BACKUP_DIR" | awk '{print $1}')
        print_success "MinIO backup created: $MINIO_BACKUP_DIR ($OBJECT_COUNT files, $BACKUP_SIZE)"
    else
        print_warning "MinIO backup created but no files found (bucket may be empty)"
    fi
}

# Parse arguments
DB_ONLY=false
MINIO_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --db-only)
            DB_ONLY=true
            shift
            ;;
        --minio-only)
            MINIO_ONLY=true
            shift
            ;;
        --list)
            list_backups
            exit 0
            ;;
        --cleanup)
            cleanup_old_backups
            exit 0
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
echo "=========================================="
echo "  Chitram Backup - $TIMESTAMP"
echo "=========================================="
echo ""
echo "Backup directory: $BACKUP_DIR"
echo "Retention: $RETENTION_DAYS days"

# Verify deploy directory exists
if [[ ! -f "$DEPLOY_DIR/$COMPOSE_FILE" ]]; then
    print_error "Cannot find $COMPOSE_FILE in $DEPLOY_DIR"
    exit 1
fi

# Run backups
if [[ "$MINIO_ONLY" == "true" ]]; then
    backup_minio
elif [[ "$DB_ONLY" == "true" ]]; then
    backup_database
else
    backup_database
    backup_minio
fi

echo ""
echo "=========================================="
print_success "Backup complete!"
echo "=========================================="
echo ""
echo "To restore, use: ./scripts/restore.sh <backup-timestamp>"
