#!/bin/bash

# Docker run script for Interior AI Service
# Usage: ./docker-run.sh [port]

set -e

# Default port
PORT=${1:-8081}
CONTAINER_NAME="interior-ai-service"

echo "🐳 Starting Interior AI Service in Docker..."
echo "📋 Port: $PORT"
echo "📁 Environment file: .env.local"

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo "❌ Error: .env.local file not found!"
    echo "   Please create .env.local with your configuration."
    exit 1
fi

# Stop and remove existing container if it exists
if docker ps -a --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "🔄 Stopping existing container..."
    docker stop $CONTAINER_NAME > /dev/null 2>&1 || true
    docker rm $CONTAINER_NAME > /dev/null 2>&1 || true
fi

# Build image if it doesn't exist
if ! docker images --format 'table {{.Repository}}:{{.Tag}}' | grep -q "^interior-ai-service:latest$"; then
    echo "🔨 Building Docker image..."
    docker build -t interior-ai-service:latest .
fi

# Run container
echo "🚀 Starting container..."
docker run -d \
    --name $CONTAINER_NAME \
    --env-file .env.local \
    -p $PORT:8080 \
    interior-ai-service:latest

echo "✅ Container started successfully!"
echo "🌐 Service available at: http://localhost:$PORT"
echo "📊 Health check: http://localhost:$PORT/health/"
echo "🔍 Readiness check: http://localhost:$PORT/health/readiness"
echo ""
echo "📝 Container logs: docker logs $CONTAINER_NAME"
echo "🛑 Stop container: docker stop $CONTAINER_NAME"
echo "🗑️  Remove container: docker rm $CONTAINER_NAME" 