#!/bin/bash

# Production Deployment Script for LangExtract
set -e

echo "🚀 Starting production deployment..."

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    echo "❌ Error: .env.prod file not found!"
    echo "Please copy env.prod to .env.prod and fill in your production values."
    exit 1
fi

# Load production environment variables
export $(cat .env.prod | grep -v '^#' | xargs)

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs

# Build and start production containers
echo "🔨 Building production containers..."
docker-compose -f docker-compose.prod.yml build --no-cache

echo "🔄 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

echo "🚀 Starting production containers..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for health check
echo "⏳ Waiting for service to be healthy..."
sleep 10

# Check health
echo "🏥 Checking service health..."
if curl -f http://localhost:8000/health/ > /dev/null 2>&1; then
    echo "✅ Service is healthy!"
    echo "🌐 LangExtract is running on http://localhost:8000"
    echo "📊 Health check: http://localhost:8000/health/"
    echo "🔍 API status: http://localhost:8000/api/status/"
else
    echo "❌ Service health check failed!"
    echo "📋 Container logs:"
    docker-compose -f docker-compose.prod.yml logs web
    exit 1
fi

echo "🎉 Production deployment completed successfully!"
