#!/bin/bash
# Main startup script for Internal File Sharing System
# Provides options for different startup modes

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

clear
echo "================================================"
echo "  Internal File Sharing System"
echo "  Startup Script"
echo "================================================"
echo ""
echo "Choose how you want to run the application:"
echo ""
echo -e "${BLUE}1)${NC} Docker Mode (Recommended)"
echo "   Everything runs in containers"
echo "   Easiest setup, most reliable"
echo ""
echo -e "${BLUE}2)${NC} Development Mode"
echo "   Database in Docker, Backend and Frontend local"
echo "   Good for development/debugging"
echo ""
echo -e "${BLUE}3)${NC} Stop All Services"
echo "   Stop running services"
echo ""
echo -e "${BLUE}4)${NC} Exit"
echo ""

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo -e "${GREEN}Starting in Docker mode...${NC}"
        echo ""
        ./start-docker.sh
        ;;
    2)
        echo ""
        echo -e "${GREEN}Starting in Development mode...${NC}"
        echo ""
        ./start-dev.sh
        ;;
    3)
        echo ""
        echo -e "${YELLOW}Stopping all services...${NC}"
        echo ""
        ./stop-dev.sh
        docker-compose down
        echo ""
        echo -e "${GREEN}All services stopped${NC}"
        ;;
    4)
        echo ""
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo ""
        echo -e "${RED}Invalid choice. Please run the script again.${NC}"
        exit 1
        ;;
esac
