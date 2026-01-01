#!/bin/bash
# validate-env.sh - Verify all services are running correctly
# Usage: ./scripts/validate-env.sh

set -e

echo "========================================="
echo "  Environment Validation"
echo "========================================="
echo ""

PASS=0
FAIL=0

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

check() {
    local name="$1"
    local cmd="$2"

    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name${NC}"
        ((PASS++))
    else
        echo -e "${RED}❌ $name${NC}"
        ((FAIL++))
    fi
}

echo "Checking services..."
echo ""

# Check PostgreSQL
check "PostgreSQL" "pg_isready -h postgres -U app -d imagehost"

# Check MinIO health
check "MinIO Health" "curl -sf http://minio:9000/minio/health/live"

# Check MinIO connectivity (can list buckets)
check "MinIO Connection" "cd backend && uv run python -c \"from minio import Minio; c = Minio('minio:9000', access_key='minioadmin', secret_key='minioadmin', secure=False); c.list_buckets()\""

# Check images bucket exists
check "MinIO Bucket 'images'" "cd backend && uv run python -c \"from minio import Minio; c = Minio('minio:9000', access_key='minioadmin', secret_key='minioadmin', secure=False); assert c.bucket_exists('images')\""

# Check .env file exists
check ".env file exists" "test -f backend/.env"

# Check Python dependencies
check "Python dependencies" "cd backend && uv run python -c 'import fastapi, sqlalchemy, minio, PIL'"

# Check Alembic migrations
check "Database migrations" "cd backend && uv run alembic current"

echo ""
echo "========================================="
echo "  Results: $PASS passed, $FAIL failed"
echo "========================================="

if [ $FAIL -gt 0 ]; then
    echo ""
    echo "Some checks failed. Run troubleshooting commands:"
    echo "  docker-compose -f .devcontainer/docker-compose.yml ps"
    echo "  docker-compose -f .devcontainer/docker-compose.yml logs"
    exit 1
fi

echo ""
echo "All checks passed! Environment is ready."
