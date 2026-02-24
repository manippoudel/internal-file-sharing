#!/bin/bash
# Stop development services for Internal File Sharing System

set -e  # Exit on error

echo "================================================"
echo "  Stopping Internal File Sharing System"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Stop backend
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        echo -e "${GREEN}✓ Backend stopped${NC}"
    else
        echo -e "${YELLOW}Backend not running${NC}"
    fi
    rm .backend.pid
else
    echo "Stopping any running uvicorn processes..."
    pkill -f "uvicorn app.main:app" 2>/dev/null || echo -e "${YELLOW}No backend process found${NC}"
fi

# Stop frontend
if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        echo -e "${GREEN}✓ Frontend stopped${NC}"
    else
        echo -e "${YELLOW}Frontend not running${NC}"
    fi
    rm .frontend.pid
else
    echo "Stopping any running vite processes..."
    pkill -f "vite" 2>/dev/null || echo -e "${YELLOW}No frontend process found${NC}"
fi

# Stop database
echo "Stopping PostgreSQL database..."
docker-compose down
echo -e "${GREEN}✓ Database stopped${NC}"

echo ""
echo -e "${GREEN}All services stopped successfully!${NC}"
