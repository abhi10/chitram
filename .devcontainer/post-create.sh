#!/bin/bash
set -e

echo "🚀 Setting up Image Hosting App development environment..."

# Detect if running in Codespaces
if [ -n "$CODESPACES" ]; then
    echo "☁️  Running in GitHub Codespaces"
fi

# Wait for PostgreSQL to be ready (with timeout)
echo "⏳ Waiting for PostgreSQL..."
RETRIES=30
until pg_isready -h postgres -U app -d imagehost > /dev/null 2>&1 || [ $RETRIES -eq 0 ]; do
    echo "   Waiting for PostgreSQL... ($RETRIES retries left)"
    RETRIES=$((RETRIES-1))
    sleep 2
done

if [ $RETRIES -eq 0 ]; then
    echo "⚠️  PostgreSQL not ready, continuing anyway..."
else
    echo "✅ PostgreSQL is ready!"
fi

# Wait for MinIO to be ready (with timeout)
echo "⏳ Waiting for MinIO..."
RETRIES=30
until curl -sf http://minio:9000/minio/health/live > /dev/null 2>&1 || [ $RETRIES -eq 0 ]; do
    echo "   Waiting for MinIO... ($RETRIES retries left)"
    RETRIES=$((RETRIES-1))
    sleep 2
done

if [ $RETRIES -eq 0 ]; then
    echo "⚠️  MinIO not ready, continuing anyway..."
else
    echo "✅ MinIO is ready!"
fi

# Create .env if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating .env file..."
    cp backend/.env.example backend/.env
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd backend
uv sync

# Run database migrations (Alembic not set up yet in Phase 1 Lean)
echo "🗄️ Running database migrations..."
uv run alembic upgrade head 2>/dev/null || echo "⚠️  Alembic not set up yet (planned for Phase 1.5)"

cd ..

echo ""
echo "========================================="
echo "✅ Development environment ready!"
echo "========================================="
echo ""
echo "📍 Phase 3 - Web UI with MinIO/Redis"
echo ""
echo "📍 Services:"
echo "   Web UI:         http://localhost:8000/"
echo "   API Docs:       http://localhost:8000/docs"
echo "   PostgreSQL:     localhost:5432"
echo "   MinIO API:      http://localhost:9000"
echo "   MinIO Console:  http://localhost:9001"
echo "   Redis:          localhost:6379"
echo ""
echo "🚀 Start the app:"
echo "   cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0"
echo ""
echo "📝 MinIO credentials: minioadmin / minioadmin"
echo ""
echo "🌐 For production Docker deployment:"
echo "   docker-compose -f docker-compose.prod.yml up --build"
echo ""
