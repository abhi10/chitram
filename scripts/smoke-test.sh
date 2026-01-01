#!/bin/bash
# smoke-test.sh - Quick API smoke test (upload → get → delete)
# Usage: ./scripts/smoke-test.sh [base_url]
#
# This script tests the full image lifecycle:
# 1. Creates a test image
# 2. Uploads it via API
# 3. Retrieves metadata
# 4. Downloads the file
# 5. Deletes the image
# 6. Verifies deletion

set -e

BASE_URL="${1:-http://localhost:8000}"

echo "========================================="
echo "  API Smoke Test"
echo "========================================="
echo "Base URL: $BASE_URL"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Temp directory for test files
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Create a simple test JPEG using Python/Pillow
echo -n "Creating test image... "
cd "$(dirname "$0")/../backend"
uv run python -c "
from PIL import Image
import io

# Create a simple red square image
img = Image.new('RGB', (100, 100), color='red')
img.save('$TEMP_DIR/test-image.jpg', 'JPEG')
print('OK')
"

# Step 1: Health check
echo -n "1. Health check... "
HEALTH=$(curl -sf "$BASE_URL/health")
if echo "$HEALTH" | grep -q '"status":"healthy"'; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    echo "$HEALTH"
    exit 1
fi

# Step 2: Upload image
echo -n "2. Upload image... "
UPLOAD_RESPONSE=$(curl -sf -X POST "$BASE_URL/api/v1/images/upload" \
    -F "file=@$TEMP_DIR/test-image.jpg")

IMAGE_ID=$(echo "$UPLOAD_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
if [ -n "$IMAGE_ID" ]; then
    echo -e "${GREEN}OK${NC} (id: $IMAGE_ID)"
else
    echo -e "${RED}FAILED${NC}"
    echo "$UPLOAD_RESPONSE"
    exit 1
fi

# Step 3: Get metadata
echo -n "3. Get metadata... "
METADATA=$(curl -sf "$BASE_URL/api/v1/images/$IMAGE_ID")
if echo "$METADATA" | grep -q "\"id\":\"$IMAGE_ID\""; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
    echo "$METADATA"
    exit 1
fi

# Step 4: Download file
echo -n "4. Download file... "
HTTP_CODE=$(curl -sf -o "$TEMP_DIR/downloaded.jpg" -w "%{http_code}" "$BASE_URL/api/v1/images/$IMAGE_ID/file")
if [ "$HTTP_CODE" = "200" ] && [ -f "$TEMP_DIR/downloaded.jpg" ]; then
    ORIG_SIZE=$(stat -f%z "$TEMP_DIR/test-image.jpg" 2>/dev/null || stat -c%s "$TEMP_DIR/test-image.jpg")
    DOWN_SIZE=$(stat -f%z "$TEMP_DIR/downloaded.jpg" 2>/dev/null || stat -c%s "$TEMP_DIR/downloaded.jpg")
    if [ "$ORIG_SIZE" = "$DOWN_SIZE" ]; then
        echo -e "${GREEN}OK${NC} (size matches: $ORIG_SIZE bytes)"
    else
        echo -e "${YELLOW}WARN${NC} (size mismatch: orig=$ORIG_SIZE, downloaded=$DOWN_SIZE)"
    fi
else
    echo -e "${RED}FAILED${NC} (HTTP $HTTP_CODE)"
    exit 1
fi

# Step 5: Delete image
echo -n "5. Delete image... "
HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" -X DELETE "$BASE_URL/api/v1/images/$IMAGE_ID")
if [ "$HTTP_CODE" = "204" ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC} (HTTP $HTTP_CODE)"
    exit 1
fi

# Step 6: Verify deletion (should return 404)
echo -n "6. Verify deletion... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/images/$IMAGE_ID")
if [ "$HTTP_CODE" = "404" ]; then
    echo -e "${GREEN}OK${NC} (404 as expected)"
else
    echo -e "${RED}FAILED${NC} (expected 404, got $HTTP_CODE)"
    exit 1
fi

echo ""
echo "========================================="
echo -e "  ${GREEN}All smoke tests passed!${NC}"
echo "========================================="
