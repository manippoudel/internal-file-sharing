#!/bin/bash
# Internal File Sharing System — single management script

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# ─── Shared setup ────────────────────────────────────────────────────────────

check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}Error: Docker is not running. Please start Docker first.${NC}"
        exit 1
    fi
}

setup_env() {
    if [ ! -f "backend/.env" ]; then
        echo -e "${YELLOW}backend/.env not found — copying from .env.example...${NC}"
        if [ -f "backend/.env.example" ]; then
            cp backend/.env.example backend/.env
            echo -e "${GREEN}Created backend/.env${NC}"
        else
            echo -e "${RED}Error: backend/.env.example not found. Create backend/.env manually.${NC}"
            exit 1
        fi
    fi
}

setup_dirs() {
    mkdir -p data/active data/deleted data/temp data/backups data/logs
    chmod -R 755 data/ 2>/dev/null || true
    echo -e "${GREEN}✓ Data directories ready${NC}"
}

wait_for_db() {
    echo "Waiting for database to be ready..."
    until docker-compose exec -T postgres pg_isready -U fileuser > /dev/null 2>&1; do
        echo "  Waiting for PostgreSQL..."
        sleep 2
    done
    echo -e "${GREEN}✓ Database ready${NC}"
}

run_migrations() {
    echo "Running database migrations..."
    docker-compose exec backend alembic upgrade head && \
        echo -e "${GREEN}✓ Migrations complete${NC}" || \
        echo -e "${YELLOW}Warning: Migration may have failed — check: docker-compose logs backend${NC}"
}

print_urls() {
    echo ""
    echo "================================================"
    echo -e "${GREEN}✓ All services running!${NC}"
    echo "================================================"
    echo ""
    echo "  Frontend:  http://localhost:5173"
    echo "  Backend:   http://localhost:8000"
    echo "  API Docs:  http://localhost:8000/docs"
    echo ""
    echo -e "${YELLOW}First time? Create the admin user:${NC}"
    echo "  docker-compose exec backend python create_admin.py"
    echo ""
    docker-compose ps
}

# ─── Actions ─────────────────────────────────────────────────────────────────

cmd_start() {
    local build_flag="${1:-}"
    echo "================================================"
    echo "  Internal File Sharing System — Starting"
    echo "================================================"
    echo ""
    check_docker
    setup_env
    setup_dirs
    echo ""
    if [ "$build_flag" = "--build" ]; then
        echo "Building and starting all services..."
        docker-compose up -d --build
    else
        echo "Starting all services (hot-reload via volumes)..."
        docker-compose up -d
    fi
    echo ""
    wait_for_db
    echo ""
    run_migrations
    print_urls
}

cmd_stop() {
    echo "================================================"
    echo "  Internal File Sharing System — Stopping"
    echo "================================================"
    echo ""
    check_docker
    docker-compose down
    rm -f .backend.pid .frontend.pid
    echo ""
    echo -e "${GREEN}✓ All services stopped${NC}"
    echo ""
    echo -e "${YELLOW}To also remove the database volume (full reset):${NC}"
    echo "  docker-compose down -v"
}

cmd_logs() {
    check_docker
    clear
    echo "================================================"
    echo "  Internal File Sharing System — Logs"
    echo "================================================"
    echo ""
    echo -e "${BLUE}1)${NC} All services"
    echo -e "${BLUE}2)${NC} Backend"
    echo -e "${BLUE}3)${NC} Frontend"
    echo -e "${BLUE}4)${NC} Database"
    echo -e "${BLUE}5)${NC} Back"
    echo ""
    read -p "Choice (1-5): " log_choice
    case $log_choice in
        1) docker-compose logs -f --tail=100 ;;
        2) docker-compose logs -f backend --tail=100 ;;
        3) docker-compose logs -f frontend --tail=100 ;;
        4) docker-compose logs -f postgres --tail=100 ;;
        5) return ;;
        *) echo -e "${RED}Invalid choice${NC}" ;;
    esac
}

# ─── CLI mode (non-interactive) ───────────────────────────────────────────────

case "${1:-}" in
    start)   cmd_start ;;
    build)   cmd_start --build ;;
    stop)    cmd_stop ;;
    logs)    docker-compose logs -f --tail=100 ;;
    "")      : ;;  # fall through to interactive menu
    *)
        echo "Usage: $0 [start|build|stop|logs]"
        echo ""
        echo "  start   Start all services with hot-reload (no rebuild)"
        echo "  build   Rebuild images then start (use after deps change)"
        echo "  stop    Stop all services"
        echo "  logs    Tail all logs"
        exit 1
        ;;
esac

# If a CLI arg was given, we're done
[ -n "${1:-}" ] && exit 0

# ─── Interactive menu ─────────────────────────────────────────────────────────

while true; do
    clear
    echo "================================================"
    echo "  Internal File Sharing System"
    echo "================================================"
    echo ""
    echo -e "${BLUE}1)${NC} Start          hot-reload, no rebuild (daily dev)"
    echo -e "${BLUE}2)${NC} Fresh Build    rebuild images (after deps/Dockerfile change)"
    echo -e "${BLUE}3)${NC} Stop"
    echo -e "${BLUE}4)${NC} Logs"
    echo -e "${BLUE}5)${NC} Exit"
    echo ""
    read -p "Choice (1-5): " choice
    case $choice in
        1) cmd_start ;;
        2) cmd_start --build ;;
        3) cmd_stop ;;
        4) cmd_logs ;;
        5) echo ""; echo "Exiting..."; exit 0 ;;
        *) echo -e "${RED}Invalid choice${NC}"; sleep 1 ;;
    esac
    echo ""
    read -p "Press Enter to return to menu..." _
done
