#!/bin/bash

# Currency Exchange Bot - Docker Deployment Script

set -e

echo "🚀 Deploying Currency Exchange Bot with Docker..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file from .env.example"
    exit 1
fi

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data receipts admin_receipts logs

# Stop existing container if running
echo "🛑 Stopping existing container..."
docker-compose down || true

# Build and start container
echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting bot container..."
docker-compose up -d

# Wait for container to start
echo "⏳ Waiting for bot to start..."
sleep 5

# Check container status
if docker-compose ps | grep -q "Up"; then
    echo "✅ Bot deployed successfully!"
    echo ""
    echo "📊 Container Status:"
    docker-compose ps
    echo ""
    echo "📝 View logs with: docker-compose logs -f"
    echo "🛑 Stop bot with: docker-compose down"
    echo "🔄 Restart bot with: docker-compose restart"
else
    echo "❌ Failed to start bot. Check logs:"
    docker-compose logs
    exit 1
fi
