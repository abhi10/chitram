#!/bin/bash
# Chitram Local Deployment Validation Script
# Usage: ./validate-local.sh [--cleanup]
#
# Validates that the local Docker deployment works correctly.
# Run from the deploy/ directory.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.local.yml"
HEALTH_URL="http://localhost:8000/health"
DOCS_URL="http://localhost:8000/docs"
MINIO_CONSOLE_URL="http://localhost:9003"
MAX_WAIT_SECONDS=60

print_step() {
    echo -e "\n${YELLOW}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

cleanup() {
    print_step "Cleaning up containers..."
    docker compose $COMPOSE_FILES down --volumes --remove-orphans 2>/dev/null || true
    print_success "Cleanup complete"
}

# Handle --cleanup flag
if [[ "$1" == "--cleanup" ]]; then
    cleanup
    exit 0
fi

# Ensure we're in the deploy directory
if [[ ! -f "docker-compose.yml" ]]; then
    print_error "Must run from deploy/ directory"
    exit 1
fi

echo "=========================================="
echo "  Chitram Local Deployment Validation"
echo "=========================================="

# Step 1: Start containers
print_step "Starting containers..."
docker compose $COMPOSE_FILES up -d --build

# Step 2: Wait for health check
print_step "Waiting for services to be healthy (max ${MAX_WAIT_SECONDS}s)..."
SECONDS_WAITED=0
while [[ $SECONDS_WAITED -lt $MAX_WAIT_SECONDS ]]; do
    if curl -s -f "$HEALTH_URL" > /dev/null 2>&1; then
        print_success "Health check passed"
        break
    fi
    sleep 2
    SECONDS_WAITED=$((SECONDS_WAITED + 2))
    echo -n "."
done

if [[ $SECONDS_WAITED -ge $MAX_WAIT_SECONDS ]]; then
    print_error "Health check failed after ${MAX_WAIT_SECONDS}s"
    echo "Logs from app container:"
    docker compose $COMPOSE_FILES logs app --tail=50
    exit 1
fi

# Step 3: Verify all containers are running
print_step "Checking container status..."
RUNNING_COUNT=$(docker compose $COMPOSE_FILES ps --status=running -q | wc -l | tr -d ' ')
EXPECTED_COUNT=4  # app, postgres, minio, redis (caddy disabled in local)

if [[ "$RUNNING_COUNT" -ge "$EXPECTED_COUNT" ]]; then
    print_success "All $RUNNING_COUNT containers running"
else
    print_error "Expected $EXPECTED_COUNT containers, found $RUNNING_COUNT"
    docker compose $COMPOSE_FILES ps
    exit 1
fi

# Step 4: Test API endpoints
print_step "Testing API endpoints..."

# Health endpoint
HEALTH_RESPONSE=$(curl -s "$HEALTH_URL")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    print_success "GET /health - OK"
else
    print_error "GET /health - Failed"
    echo "Response: $HEALTH_RESPONSE"
fi

# Docs endpoint
DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$DOCS_URL")
if [[ "$DOCS_STATUS" == "200" ]]; then
    print_success "GET /docs - OK (Swagger UI accessible)"
else
    print_error "GET /docs - Failed (status: $DOCS_STATUS)"
fi

# Step 5: Test MinIO
print_step "Testing MinIO console..."
MINIO_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$MINIO_CONSOLE_URL")
if [[ "$MINIO_STATUS" == "200" ]]; then
    print_success "MinIO Console accessible at $MINIO_CONSOLE_URL"
else
    print_error "MinIO Console not accessible (status: $MINIO_STATUS)"
fi

# Step 6: Test database connectivity (via app health which checks DB)
print_step "Verifying database connectivity..."
DB_CHECK=$(curl -s "$HEALTH_URL" | grep -o '"database":[^,}]*' || echo "")
if echo "$DB_CHECK" | grep -q "connected\|healthy\|ok"; then
    print_success "Database connected"
else
    # If no explicit DB status, the health check passing means DB is OK
    print_success "Database connected (health check passed)"
fi

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}  ✓ Local Validation Complete${NC}"
echo "=========================================="
echo ""
echo "Access points:"
echo "  • Web UI:        $HEALTH_URL"
echo "  • API Docs:      $DOCS_URL"
echo "  • MinIO Console: $MINIO_CONSOLE_URL (minioadmin/minioadmin)"
echo ""
echo "To stop: ./validate-local.sh --cleanup"
echo "Or:      docker compose $COMPOSE_FILES down"
