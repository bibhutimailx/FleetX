#!/bin/bash

# Fleet Management System - Quick Start Script

set -e

echo "🚛 Fleet Management System - Quick Start"
echo "========================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker and try again."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ Created .env file. Please edit it with your WHILSEYE API credentials and other settings."
    echo "⚠️  You need to configure the following variables in .env:"
    echo "   - WHILSEYE_USERNAME"
    echo "   - WHILSEYE_PASSWORD"
    echo "   - WHILSEYE_API_KEY"
    echo "   - SLACK_WEBHOOK_URL (optional)"
    echo "   - FCM_SERVICE_ACCOUNT_KEY (optional)"
    echo ""
    read -p "Press Enter to continue after editing .env file..."
fi

# Create logs directory
mkdir -p logs

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting Fleet Management System..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

# Check backend
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is running"
else
    echo "❌ Backend health check failed"
    echo "📋 Backend logs:"
    docker-compose logs backend | tail -10
fi

# Check frontend
if curl -f http://localhost/ > /dev/null 2>&1; then
    echo "✅ Frontend is running"
else
    echo "❌ Frontend health check failed"
    echo "📋 Frontend logs:"
    docker-compose logs frontend | tail -10
fi

# Check database
if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ Database is running"
else
    echo "❌ Database health check failed"
    echo "📋 Database logs:"
    docker-compose logs postgres | tail -10
fi

echo ""
echo "🎉 Fleet Management System is ready!"
echo ""
echo "📍 Access the application:"
echo "   Web App:     http://localhost/"
echo "   API Docs:    http://localhost:8000/docs"
echo "   Health:      http://localhost:8000/health"
echo ""
echo "📊 Useful commands:"
echo "   View logs:   docker-compose logs -f"
echo "   Stop:        docker-compose down"
echo "   Restart:     docker-compose restart"
echo ""
echo "🛠️  Development:"
echo "   Backend:     make backend"
echo "   Frontend:    make frontend"
echo "   Dev mode:    make dev"
echo ""

# Show running containers
echo "🐳 Running containers:"
docker-compose ps

