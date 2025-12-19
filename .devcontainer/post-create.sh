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
echo "📍 Phase 1 Lean - Local Storage Only"
echo ""
echo "📍 Services:"
echo "   FastAPI:        http://localhost:8000"
echo "   API Docs:       http://localhost:8000/docs"
echo "   PostgreSQL:     localhost:5432"
echo ""
echo "🚀 Start the app:"
echo "   cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0"
echo ""
echo "📝 Note: MinIO removed in Phase 1 Lean (ADR-0008)"
echo "         Will be restored in Phase 2"
echo ""
