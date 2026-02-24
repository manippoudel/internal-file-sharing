#!/bin/bash
# Start all services using Docker Compose
# This runs everything in containers (easiest method)

set -e  # Exit on error

echo "================================================"
echo "  Internal File Sharing System - Docker Mode"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if .env exists in backend
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}Warning: backend/.env not found. Copying from .env.example...${NC}"
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
        echo -e "${GREEN}Created backend/.env from .env.example${NC}"
    else
        echo -e "${RED}Error: backend/.env.example not found. Please create backend/.env manually.${NC}"
        exit 1
    fi
fi

# Create data directories if they don't exist
echo "Setting up data directories..."
mkdir -p data/active data/deleted data/temp data/backups data/logs

# Try to set permissions, but don't fail if some directories are owned by docker
chmod -R 755 data/ 2>/dev/null || {
    echo -e "${YELLOW}Note: Some directories may have different permissions (owned by Docker)${NC}"
    # At least ensure the main directories exist and are writable
    chmod 755 data/ 2>/dev/null || true
}

echo -e "${GREEN}✓ Data directories ready${NC}"
echo ""

# Build and start all services
echo "Starting all services with Docker Compose..."
docker-compose up -d --build

# Wait for services to be ready
echo ""
echo "Waiting for services to start..."
sleep 5

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Services started successfully!${NC}"
else
    echo -e "${RED}Error: Some services failed to start${NC}"
    docker-compose ps
    exit 1
fi

echo ""
echo "Waiting for database to be ready..."
until docker-compose exec -T postgres pg_isready -U fileuser > /dev/null 2>&1; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done
echo -e "${GREEN}✓ Database is ready${NC}"

# Run database migrations
echo ""
echo "Running database migrations..."
docker-compose exec backend alembic upgrade head
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database migrations complete${NC}"
else
    echo -e "${YELLOW}Warning: Migration may have failed${NC}"
fi

echo ""
echo "================================================"
echo -e "${GREEN}✓ All services running in Docker!${NC}"
echo "================================================"
echo ""
echo "Services running:"
echo "  - Database:  http://localhost:5432"
echo "  - Backend:   http://localhost:8000"
echo "  - Frontend:  http://localhost:5173"
echo "  - API Docs:  http://localhost:8000/docs"
echo ""
echo "View logs:"
echo "  docker-compose logs -f"
echo ""
echo "Stop all services:"
echo "  docker-compose down"
echo ""
echo "Stop and remove volumes (clean reset):"
echo "  docker-compose down -v"
echo ""
echo -e "${YELLOW}Note: Create an admin user if this is your first time:${NC}"
echo "  docker-compose exec backend python create_admin.py"
echo ""
echo -e "${YELLOW}Admin credentials are set in backend/.env:${NC}"
echo "  ADMIN_EMAIL=admin@internal-file-sharing.local"
echo "  ADMIN_PASSWORD=Admin@123456"
echo ""
echo "Container status:"
docker-compose ps
