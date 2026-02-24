#!/bin/bash
# View logs for Internal File Sharing System

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

clear
echo "================================================"
echo "  Internal File Sharing System - View Logs"
echo "================================================"
echo ""
echo "Choose which logs to view:"
echo ""
echo -e "${BLUE}1)${NC} All logs (Docker)"
echo -e "${BLUE}2)${NC} Backend logs only"
echo -e "${BLUE}3)${NC} Frontend logs only"
echo -e "${BLUE}4)${NC} Database logs only"
echo -e "${BLUE}5)${NC} Development logs (local files)"
echo -e "${BLUE}6)${NC} Exit"
echo ""

read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        echo ""
        echo -e "${GREEN}Viewing all Docker logs (Ctrl+C to exit)...${NC}"
        echo ""
        docker-compose logs -f --tail=100
        ;;
    2)
        echo ""
        echo -e "${GREEN}Viewing backend logs (Ctrl+C to exit)...${NC}"
        echo ""
        if [ -f "logs/backend.log" ]; then
            tail -f logs/backend.log
        else
            docker-compose logs -f backend --tail=100
        fi
        ;;
    3)
        echo ""
        echo -e "${GREEN}Viewing frontend logs (Ctrl+C to exit)...${NC}"
        echo ""
        if [ -f "logs/frontend.log" ]; then
            tail -f logs/frontend.log
        else
            docker-compose logs -f frontend --tail=100
        fi
        ;;
    4)
        echo ""
        echo -e "${GREEN}Viewing database logs (Ctrl+C to exit)...${NC}"
        echo ""
        docker-compose logs -f postgres --tail=100
        ;;
    5)
        echo ""
        echo -e "${GREEN}Viewing development logs (Ctrl+C to exit)...${NC}"
        echo ""
        if [ -f "logs/backend.log" ] && [ -f "logs/frontend.log" ]; then
            tail -f logs/backend.log logs/frontend.log
        else
            echo -e "${YELLOW}No development logs found. Are you running in development mode?${NC}"
            echo "Logs are in: logs/backend.log and logs/frontend.log"
        fi
        ;;
    6)
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
