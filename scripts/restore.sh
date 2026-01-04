#!/bin/bash
# Chitram Restore Script
# ======================
#
# Restores PostgreSQL database and/or MinIO objects from backup.
#
# Usage:
#   ./scripts/restore.sh <timestamp>              # Full restore (DB + MinIO)
#   ./scripts/restore.sh <timestamp> --db-only    # Database only
#   ./scripts/restore.sh <timestamp> --minio-only # MinIO objects only
#   ./scripts/restore.sh --list                   # List available backups
#
# Example:
#   ./scripts/restore.sh 20240115-143022
#
# Environment Variables:
#   DEPLOY_DIR        - Path to deploy directory
#   BACKUP_DIR        - Where backups are stored (default: /opt/chitram-backups)

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
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

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
    echo "Chitram Restore Script"
    echo ""
    echo "Usage: $0 <timestamp> [OPTIONS]"
    echo ""
    echo "Arguments:"
    echo "  timestamp      Backup timestamp (e.g., 20240115-143022)"
    echo ""
    echo "Options:"
    echo "  --db-only      Restore database only"
    echo "  --minio-only   Restore MinIO objects only"
    echo "  --list         List available backups"
    echo "  --force        Skip confirmation prompt"
    echo "  --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --list                    # List available backups"
    echo "  $0 20240115-143022           # Restore from specific backup"
    echo "  $0 20240115-143022 --db-only # Restore database only"
    echo ""
}

list_backups() {
    print_step "Available backups in $BACKUP_DIR"

    if [[ ! -d "$BACKUP_DIR" ]]; then
        print_warning "Backup directory does not exist"
        return
    fi

    echo ""
    echo "Timestamps with database backups:"
    ls "$BACKUP_DIR"/db-*.sql.gz 2>/dev/null | sed 's/.*db-\(.*\)\.sql\.gz/  \1/' || echo "  (none)"

    echo ""
    echo "Timestamps with MinIO backups:"
    ls -d "$BACKUP_DIR"/minio-* 2>/dev/null | sed 's/.*minio-/  /' || echo "  (none)"
}

restore_database() {
    local TIMESTAMP=$1

    print_step "Restoring PostgreSQL database from backup..."

    DB_BACKUP_FILE="$BACKUP_DIR/db-$TIMESTAMP.sql.gz"

    if [[ ! -f "$DB_BACKUP_FILE" ]]; then
        print_error "Database backup not found: $DB_BACKUP_FILE"
        return 1
    fi

    cd "$DEPLOY_DIR"

    # Check if postgres container is running
    if ! docker compose -f "$COMPOSE_FILE" ps postgres | grep -q "running"; then
        print_error "PostgreSQL container is not running"
        return 1
    fi

    BACKUP_SIZE=$(ls -lh "$DB_BACKUP_FILE" | awk '{print $5}')
    echo "Backup file: $DB_BACKUP_FILE ($BACKUP_SIZE)"

    # Restore database
    # First, drop existing connections and recreate database
    print_step "Dropping existing database and restoring..."

    docker compose -f "$COMPOSE_FILE" exec -T postgres \
        psql -U "${POSTGRES_USER:-chitram}" -d postgres -c "
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = '${POSTGRES_DB:-chitram}' AND pid <> pg_backend_pid();
        " 2>/dev/null || true

    docker compose -f "$COMPOSE_FILE" exec -T postgres \
        psql -U "${POSTGRES_USER:-chitram}" -d postgres -c "
            DROP DATABASE IF EXISTS ${POSTGRES_DB:-chitram};
            CREATE DATABASE ${POSTGRES_DB:-chitram};
        "

    # Restore from backup
    gunzip -c "$DB_BACKUP_FILE" | docker compose -f "$COMPOSE_FILE" exec -T postgres \
        psql -U "${POSTGRES_USER:-chitram}" "${POSTGRES_DB:-chitram}"

    print_success "Database restored successfully"
}

restore_minio() {
    local TIMESTAMP=$1

    print_step "Restoring MinIO objects from backup..."

    MINIO_BACKUP_DIR="$BACKUP_DIR/minio-$TIMESTAMP"

    if [[ ! -d "$MINIO_BACKUP_DIR" ]]; then
        print_error "MinIO backup not found: $MINIO_BACKUP_DIR"
        return 1
    fi

    cd "$DEPLOY_DIR"

    # Check if minio container is running
    if ! docker compose -f "$COMPOSE_FILE" ps minio | grep -q "running"; then
        print_error "MinIO container is not running"
        return 1
    fi

    BACKUP_SIZE=$(du -sh "$MINIO_BACKUP_DIR" | awk '{print $1}')
    OBJECT_COUNT=$(find "$MINIO_BACKUP_DIR" -type f | wc -l | tr -d ' ')
    echo "Backup directory: $MINIO_BACKUP_DIR ($OBJECT_COUNT files, $BACKUP_SIZE)"

    # Get MinIO credentials
    MINIO_ACCESS="${MINIO_ACCESS_KEY:-minioadmin}"
    MINIO_SECRET="${MINIO_SECRET_KEY:-minioadmin}"
    MINIO_BUCKET="${MINIO_BUCKET:-images}"

    # Use mc (MinIO Client) to restore objects
    docker run --rm \
        --network "${COMPOSE_PROJECT_NAME:-deploy}_chitram-network" \
        -v "$MINIO_BACKUP_DIR:/backup:ro" \
        minio/mc:latest \
        /bin/sh -c "
            mc alias set chitram http://minio:9000 $MINIO_ACCESS $MINIO_SECRET --api S3v4 &&
            mc mb chitram/$MINIO_BUCKET --ignore-existing &&
            mc mirror /backup/$MINIO_BUCKET chitram/$MINIO_BUCKET --overwrite
        " 2>/dev/null

    print_success "MinIO objects restored successfully"
}

# Parse arguments
TIMESTAMP=""
DB_ONLY=false
MINIO_ONLY=false
FORCE=false

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
        --force)
            FORCE=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        -*)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
        *)
            if [[ -z "$TIMESTAMP" ]]; then
                TIMESTAMP=$1
            else
                print_error "Unexpected argument: $1"
                show_help
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate timestamp
if [[ -z "$TIMESTAMP" ]]; then
    print_error "Timestamp is required"
    echo ""
    show_help
    exit 1
fi

# Verify deploy directory exists
if [[ ! -f "$DEPLOY_DIR/$COMPOSE_FILE" ]]; then
    print_error "Cannot find $COMPOSE_FILE in $DEPLOY_DIR"
    exit 1
fi

# Main execution
echo "=========================================="
echo "  Chitram Restore - $TIMESTAMP"
echo "=========================================="
echo ""
echo "Backup directory: $BACKUP_DIR"

# Confirmation prompt
if [[ "$FORCE" != "true" ]]; then
    echo ""
    print_warning "WARNING: This will overwrite existing data!"
    echo ""
    read -p "Are you sure you want to restore from backup $TIMESTAMP? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Restore cancelled."
        exit 0
    fi
fi

# Run restores
if [[ "$MINIO_ONLY" == "true" ]]; then
    restore_minio "$TIMESTAMP"
elif [[ "$DB_ONLY" == "true" ]]; then
    restore_database "$TIMESTAMP"
else
    restore_database "$TIMESTAMP"
    restore_minio "$TIMESTAMP"
fi

echo ""
echo "=========================================="
print_success "Restore complete!"
echo "=========================================="
echo ""
echo "Verify the application is working correctly:"
echo "  curl http://localhost:8000/health"
