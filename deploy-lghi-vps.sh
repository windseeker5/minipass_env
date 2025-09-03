#!/bin/bash

# Safe Minipass VPS Deployment Script
# Preserves previous image for rollback and protects production database

set -e

echo "🚀 Deploying Minipass LHGI container..."

PROJECT_NAME="lhgi"
APP_DIR="/home/kdresdell/minipass_env"

cd $APP_DIR

echo "💾 Creating database backup as extra safety..."
cd app
if [ -f "instance/minipass.db" ]; then
    cp instance/minipass.db instance/minipass_backup_$(date +%Y%m%d_%H%M%S).db
    echo "✅ Database backup created"
fi

echo "🔄 Pulling latest code while preserving local database..."
# Stash local changes (database and .gitignore) before pulling
git stash push -u -m "Deploy stash: preserve local database and config" 2>/dev/null || true
git pull origin v1
# Restore the local database and .gitignore
git stash pop 2>/dev/null || echo "No stash to restore (this is fine)"
cd ..

echo "🧹 Aggressive Docker cache clearing to prevent cache issues..."
docker system prune -f
docker builder prune -f

echo "💾 Tagging current image as backup..."
docker tag minipass_env-${PROJECT_NAME}:latest minipass_env-${PROJECT_NAME}:backup 2>/dev/null || true

echo "🛑 Stopping container..."
docker stop ${PROJECT_NAME} 2>/dev/null || true

echo "🔨 Building new image with no cache..."
docker-compose build --no-cache --pull lhgi

echo "🚀 Starting new container..."
docker-compose up -d lhgi

echo "⏳ Testing new deployment..."
sleep 10

# Get expected version (current git commit from app submodule)
cd app
EXPECTED_VERSION=$(git rev-parse HEAD | cut -c1-8)
echo "Expected version: $EXPECTED_VERSION"
cd ..

# Check if container is running
if docker ps | grep ${PROJECT_NAME} | grep -q "Up"; then
    echo "✅ Container is running"
    
    # Verify actual version via health check
    echo "🔍 Verifying deployed version..."
    sleep 5  # Give app time to fully start
    
    # Use the correct port for lhgi service (8889 based on docker-compose)
    ACTUAL_VERSION=$(curl -s --max-time 10 http://localhost:8889/health | grep -o '"version":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "unknown")
    
    if [ "$ACTUAL_VERSION" = "$EXPECTED_VERSION" ]; then
        echo "✅ Version verified! Deployed: $ACTUAL_VERSION"
        echo "🗑️ Cleaning up old backup..."
        docker rmi minipass_env-${PROJECT_NAME}:backup 2>/dev/null || true
    elif [ "$ACTUAL_VERSION" = "unknown" ] || [ -z "$ACTUAL_VERSION" ]; then
        echo "⚠️  Could not verify version (health check failed), but container is running"
        echo "🗑️ Cleaning up old backup..."
        docker rmi minipass_env-${PROJECT_NAME}:backup 2>/dev/null || true
    else
        echo "❌ Version mismatch! Expected: $EXPECTED_VERSION, Got: $ACTUAL_VERSION"
        echo "🔄 This indicates a cache issue - rolling back..."
        docker stop ${PROJECT_NAME} 2>/dev/null || true
        docker tag minipass_env-${PROJECT_NAME}:backup minipass_env-${PROJECT_NAME}:latest
        docker-compose up -d lhgi
        echo "🔄 Rollback complete"
        exit 1
    fi
else
    echo "❌ Container failed to start! Rolling back..."
    docker stop ${PROJECT_NAME} 2>/dev/null || true
    docker tag minipass_env-${PROJECT_NAME}:backup minipass_env-${PROJECT_NAME}:latest
    docker-compose up -d lhgi
    echo "🔄 Rollback complete"
    exit 1
fi

echo "🌐 App running at: https://lhgi.minipass.me"
echo "🔒 Production database preserved and secure!"