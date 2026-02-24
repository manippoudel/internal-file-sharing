#!/bin/bash
# Development startup script for Internal File Sharing System
# This script starts the database, backend, and frontend for local development

set -e  # Exit on error

echo "================================================"
echo "  Internal File Sharing System - Development"
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

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0
    else
        return 1
    fi
}

# Check if required ports are available
echo "Checking required ports..."
if check_port 5432; then
    echo -e "${YELLOW}Warning: Port 5432 (PostgreSQL) is already in use${NC}"
    echo "If you have a PostgreSQL container running, we'll use that."
fi

if check_port 8000; then
    echo -e "${RED}Error: Port 8000 (Backend) is already in use${NC}"
    echo "Please stop the process using port 8000 and try again."
    exit 1
fi

if check_port 5173; then
    echo -e "${RED}Error: Port 5173 (Frontend) is already in use${NC}"
    echo "Please stop the process using port 5173 and try again."
    exit 1
fi

echo -e "${GREEN}✓ All ports available${NC}"
echo ""

# Create data directories if they don't exist
echo "Setting up data directories..."
mkdir -p data/active data/deleted data/temp data/backups data/logs
chmod -R 755 data/
echo -e "${GREEN}✓ Data directories ready${NC}"
echo ""

# Start database with Docker Compose
echo "Starting PostgreSQL database..."
docker-compose up -d postgres
echo -e "${GREEN}✓ Database starting...${NC}"
echo ""

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 5

# Check if database is responding
until docker-compose exec -T postgres pg_isready -U fileuser > /dev/null 2>&1; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done
echo -e "${GREEN}✓ Database is ready${NC}"
echo ""

# Run database migrations
echo "Running database migrations..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

source venv/bin/activate

# Install dependencies if needed
if ! pip show fastapi > /dev/null 2>&1; then
    echo "Installing backend dependencies..."
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi

# Run migrations
alembic upgrade head
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database migrations complete${NC}"
else
    echo -e "${YELLOW}Warning: Migration may have failed. Continuing anyway...${NC}"
fi
cd ..
echo ""

# Check if we need to create admin user
echo "Checking for admin user..."
# This will be shown in the output after backend starts
echo ""

# Start backend in background
echo "Starting FastAPI backend..."
cd backend
source venv/bin/activate

# Kill any existing backend process
pkill -f "uvicorn app.main:app" 2>/dev/null || true

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 3

if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
else
    echo -e "${RED}Error: Backend failed to start. Check logs/backend.log${NC}"
    exit 1
fi
echo ""

# Start frontend
echo "Starting Vue.js frontend..."
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi

# Kill any existing frontend process
pkill -f "vite" 2>/dev/null || true

# Start frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "Waiting for frontend to start..."
sleep 3

if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${RED}Error: Frontend failed to start. Check logs/frontend.log${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi
echo ""

# Save PIDs for stopping later
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

echo "================================================"
echo -e "${GREEN}✓ All services started successfully!${NC}"
echo "================================================"
echo ""
echo "Services running:"
echo "  - Database:  http://localhost:5432"
echo "  - Backend:   http://localhost:8000"
echo "  - Frontend:  http://localhost:5173"
echo "  - API Docs:  http://localhost:8000/docs"
echo ""
echo "Logs:"
echo "  - Backend:   tail -f logs/backend.log"
echo "  - Frontend:  tail -f logs/frontend.log"
echo "  - Database:  docker-compose logs -f postgres"
echo ""
echo "To stop all services:"
echo "  ./stop-dev.sh"
echo ""
echo -e "${YELLOW}Note: Create an admin user if this is your first time:${NC}"
echo "  cd backend && source venv/bin/activate"
echo "  python create_admin.py"
echo ""
echo "Press Ctrl+C to view logs, or close this terminal to run in background"
echo ""

# Optionally tail logs
read -p "View logs? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    trap 'echo ""; echo "Logs stopped. Services still running."; exit 0' INT
    tail -f logs/backend.log logs/frontend.log
fi
