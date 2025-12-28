#!/bin/bash

# AI-Shell Docker Test Environment - Quick Start Script

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}AI-Shell Docker Test Environment${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    echo "Please start Docker and try again"
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker Compose is not available${NC}"
    echo "Please install Docker Compose v2.0+ and try again"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Parse command line arguments
COMMAND=${1:-up}
SERVICES=${2:-}

case $COMMAND in
    up|start)
        echo -e "${GREEN}Starting all services...${NC}"
        echo ""

        if [ -n "$SERVICES" ]; then
            docker compose -f docker-compose.test.yml --env-file .env.test up -d $SERVICES
        else
            docker compose -f docker-compose.test.yml --env-file .env.test up -d
        fi

        echo ""
        echo -e "${GREEN}Services started successfully!${NC}"
        echo ""
        echo -e "${YELLOW}Note: Oracle DB may take 2-3 minutes to initialize on first start${NC}"
        echo ""
        echo "Check status with: ./start.sh status"
        echo "Test connections with: ./test-connections.sh"
        ;;

    down|stop)
        echo -e "${YELLOW}Stopping all services...${NC}"
        docker compose -f docker-compose.test.yml down
        echo -e "${GREEN}Services stopped${NC}"
        ;;

    restart)
        echo -e "${YELLOW}Restarting services...${NC}"
        if [ -n "$SERVICES" ]; then
            docker compose -f docker-compose.test.yml restart $SERVICES
        else
            docker compose -f docker-compose.test.yml restart
        fi
        echo -e "${GREEN}Services restarted${NC}"
        ;;

    status|ps)
        echo -e "${BLUE}Service Status:${NC}"
        echo ""
        docker compose -f docker-compose.test.yml ps
        ;;

    logs)
        if [ -n "$SERVICES" ]; then
            docker compose -f docker-compose.test.yml logs -f $SERVICES
        else
            docker compose -f docker-compose.test.yml logs -f
        fi
        ;;

    test)
        echo -e "${BLUE}Testing database connections...${NC}"
        echo ""
        bash test-connections.sh
        ;;

    clean)
        echo -e "${RED}WARNING: This will remove all containers and volumes!${NC}"
        echo -e "${RED}All database data will be lost!${NC}"
        echo ""
        read -p "Are you sure? (yes/no): " -r
        if [[ $REPLY == "yes" ]]; then
            echo -e "${YELLOW}Removing all services and volumes...${NC}"
            docker compose -f docker-compose.test.yml down -v --remove-orphans
            echo -e "${GREEN}Cleanup complete${NC}"
        else
            echo "Cleanup cancelled"
        fi
        ;;

    help|--help|-h)
        echo "Usage: ./start.sh [command] [services]"
        echo ""
        echo "Commands:"
        echo "  up, start        Start all services (default)"
        echo "  down, stop       Stop all services"
        echo "  restart          Restart services"
        echo "  status, ps       Show service status"
        echo "  logs             Show service logs (use Ctrl+C to exit)"
        echo "  test             Test database connections"
        echo "  clean            Remove all containers and volumes (WARNING: deletes data)"
        echo "  help             Show this help message"
        echo ""
        echo "Services:"
        echo "  postgres         PostgreSQL 16"
        echo "  mysql            MySQL 8"
        echo "  mongodb          MongoDB"
        echo "  redis            Redis"
        echo "  oracle           Oracle DB 23c Free"
        echo "  adminer          SQL database admin UI"
        echo "  mongo-express    MongoDB admin UI"
        echo "  redis-commander  Redis admin UI"
        echo ""
        echo "Examples:"
        echo "  ./start.sh up                    # Start all services"
        echo "  ./start.sh up postgres mysql     # Start only PostgreSQL and MySQL"
        echo "  ./start.sh logs postgres         # View PostgreSQL logs"
        echo "  ./start.sh restart redis         # Restart Redis"
        echo "  ./start.sh test                  # Test all connections"
        echo ""
        echo "Admin UIs (after services are started):"
        echo "  Adminer:         http://localhost:8080"
        echo "  Mongo Express:   http://localhost:8081"
        echo "  Redis Commander: http://localhost:8082"
        echo "  Oracle EM:       https://localhost:5500/em"
        ;;

    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        echo "Use './start.sh help' for usage information"
        exit 1
        ;;
esac
