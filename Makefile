# Fleet Management System Makefile

.PHONY: help build up down logs clean test dev prod backend frontend db-migrate db-reset

# Default target
help:
	@echo "Fleet Management System Commands:"
	@echo "  build       - Build all Docker images"
	@echo "  up          - Start all services (production)"
	@echo "  dev         - Start development environment"
	@echo "  down        - Stop all services"
	@echo "  logs        - View logs for all services"
	@echo "  clean       - Clean up Docker resources"
	@echo "  test        - Run tests"
	@echo "  backend     - Start backend only"
	@echo "  frontend    - Start frontend only"
	@echo "  db-migrate  - Run database migrations"
	@echo "  db-reset    - Reset database"

# Build all images
build:
	docker-compose build

# Start production environment
up:
	docker-compose up -d

# Start development environment
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Stop all services
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Clean up Docker resources
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Run tests
test:
	docker-compose exec backend python -m pytest tests/ -v
	docker-compose exec frontend npm test -- --watchAll=false

# Start backend only
backend:
	docker-compose up -d postgres redis
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend only
frontend:
	cd frontend && npm start

# Database migrations
db-migrate:
	docker-compose exec backend alembic upgrade head

# Reset database
db-reset:
	docker-compose down -v postgres
	docker-compose up -d postgres
	sleep 10
	docker-compose exec backend alembic upgrade head

# Setup environment
setup:
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "Created .env file from template. Please edit it with your configuration."; \
	fi

# Install dependencies locally
install:
	cd backend && pip install -r ../requirements.txt
	cd frontend && npm install

# Run linting
lint:
	cd backend && flake8 app/
	cd frontend && npm run lint

# Production deployment with SSL
prod-ssl:
	@echo "Setting up production with SSL..."
	docker-compose -f docker-compose.yml -f docker-compose.ssl.yml up -d

# Health check
health:
	@echo "Checking service health..."
	@curl -f http://localhost:8000/health || echo "Backend health check failed"
	@curl -f http://localhost/ || echo "Frontend health check failed"

# Backup database
backup:
	@echo "Creating database backup..."
	docker-compose exec postgres pg_dump -U postgres fleet_management > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Restore database
restore:
	@echo "Restoring database from backup..."
	@read -p "Enter backup file path: " backup_file; \
	docker-compose exec -T postgres psql -U postgres fleet_management < $$backup_file

