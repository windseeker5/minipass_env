#!/bin/bash

# Safe Minipass VPS Deployment Script
# Preserves previous image for rollback

set -e

echo "🚀 Deploying Minipass LHGI container..."

PROJECT_NAME="lhgi"
APP_DIR="/root/minipass_env"

cd $APP_DIR

echo "🔄 Pulling latest code..."
git pull origin v1

echo "💾 Tagging current image as backup..."
docker tag ${PROJECT_NAME}-web:latest ${PROJECT_NAME}-web:backup 2>/dev/null || true

echo "🛑 Stopping container..."
docker stop ${PROJECT_NAME}-web-1 2>/dev/null || true

echo "🔨 Building new image..."
docker-compose build --no-cache web

echo "🚀 Starting new container..."
docker-compose up -d web

echo "⏳ Testing new deployment..."
sleep 10

# Get expected version (current git commit)
EXPECTED_VERSION=$(git rev-parse HEAD | cut -c1-8)
echo "Expected version: $EXPECTED_VERSION"

# Check if container is running
if docker ps | grep ${PROJECT_NAME}-web-1 | grep -q "Up"; then
    echo "✓ Container is running"
    
    # Verify actual version via health check
    echo "🔍 Verifying deployed version..."
    sleep 5  # Give app time to fully start
    
    ACTUAL_VERSION=$(curl -s --max-time 10 http://localhost:5000/health | grep -o '"version":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "unknown")
    
    if [ "$ACTUAL_VERSION" = "$EXPECTED_VERSION" ]; then
        echo "✅ Version verified! Deployed: $ACTUAL_VERSION"
        echo "🗑️ Cleaning up old backup..."
        docker rmi ${PROJECT_NAME}-web:backup 2>/dev/null || true
    elif [ "$ACTUAL_VERSION" = "unknown" ]; then
        echo "⚠️  Could not verify version (health check failed), but container is running"
        echo "🗑️ Cleaning up old backup..."
        docker rmi ${PROJECT_NAME}-web:backup 2>/dev/null || true
    else
        echo "❌ Version mismatch! Expected: $EXPECTED_VERSION, Got: $ACTUAL_VERSION"
        echo "🔄 This indicates a cache issue - rolling back..."
        docker stop ${PROJECT_NAME}-web-1 2>/dev/null || true
        docker tag ${PROJECT_NAME}-web:backup ${PROJECT_NAME}-web:latest
        docker-compose up -d web
        echo "🔄 Rollback complete"
        exit 1
    fi
else
    echo "❌ Container failed to start! Rolling back..."
    docker stop ${PROJECT_NAME}-web-1 2>/dev/null || true
    docker tag ${PROJECT_NAME}-web:backup ${PROJECT_NAME}-web:latest
    docker-compose up -d web
    echo "🔄 Rollback complete"
    exit 1
fi

echo "🌐 App running at: http://YOUR_VPS_IP:5000"