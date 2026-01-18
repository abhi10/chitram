#!/bin/bash
# Start the development server using Docker Compose

set -e

echo "🐳 Starting Chitram development server with Docker..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "   Please start Docker Desktop and try again"
    exit 1
fi

# Navigate to project root
cd "$(dirname "$0")"

# Start all services (app will auto-start the server)
echo "📦 Starting services (PostgreSQL, MinIO, Redis, App)..."
docker compose -f .devcontainer/docker-compose.yml -f docker-compose.dev.yml up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 8

# Show service status
echo ""
echo "✅ Services started:"
docker compose -f .devcontainer/docker-compose.yml ps

echo ""
echo "🚀 Development server is running!"
echo ""
echo "   📱 App:            http://localhost:8000"
echo "   📊 MinIO Console:  http://localhost:9001 (minioadmin/minioadmin)"
echo "   📖 API Docs:       http://localhost:8000/docs"
echo ""
echo "💡 View logs:        docker compose -f .devcontainer/docker-compose.yml logs -f app"
echo "🛑 Stop server:      docker compose -f .devcontainer/docker-compose.yml down"
echo ""
