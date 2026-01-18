#!/bin/bash
# Stop the development server and all services

cd "$(dirname "$0")"

echo "🛑 Stopping all services..."
docker compose -f .devcontainer/docker-compose.yml down

echo "✅ All services stopped"
