#!/bin/bash
# cleanup-test-data.sh - Clear MinIO bucket and reset database
# Usage: ./scripts/cleanup-test-data.sh [--db-only|--storage-only]
#
# Options:
#   --db-only       Only reset the database
#   --storage-only  Only clear MinIO bucket
#   (no options)    Clean both

set -e

cd "$(dirname "$0")/../backend"

echo "========================================="
echo "  Cleanup Test Data"
echo "========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

CLEAN_DB=true
CLEAN_STORAGE=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --db-only)
            CLEAN_STORAGE=false
            shift
            ;;
        --storage-only)
            CLEAN_DB=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--db-only|--storage-only]"
            exit 1
            ;;
    esac
done

# Clean MinIO bucket
if [ "$CLEAN_STORAGE" = true ]; then
    echo "Clearing MinIO bucket..."
    uv run python -c "
from minio import Minio

client = Minio(
    'minio:9000',
    access_key='minioadmin',
    secret_key='minioadmin',
    secure=False
)

bucket = 'images'
count = 0

if client.bucket_exists(bucket):
    for obj in client.list_objects(bucket, recursive=True):
        client.remove_object(bucket, obj.object_name)
        print(f'  Deleted: {obj.object_name}')
        count += 1

if count > 0:
    print(f'Cleared {count} objects from bucket')
else:
    print('Bucket was already empty')
"
    echo -e "${GREEN}MinIO bucket cleared${NC}"
    echo ""
fi

# Reset database
if [ "$CLEAN_DB" = true ]; then
    echo "Resetting database..."
    echo "  Running: alembic downgrade base"
    uv run alembic downgrade base 2>/dev/null || echo -e "${YELLOW}  (No migrations to downgrade)${NC}"
    echo "  Running: alembic upgrade head"
    uv run alembic upgrade head
    echo -e "${GREEN}Database reset complete${NC}"
    echo ""
fi

echo "========================================="
echo -e "  ${GREEN}Cleanup complete!${NC}"
echo "========================================="
