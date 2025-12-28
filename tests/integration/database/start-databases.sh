#!/bin/bash
#
# AI-Shell Database Integration Environment - Quick Start Script
#
# This script helps you quickly start and verify all database containers
# for AI-Shell integration testing.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Print functions
print_header() {
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        echo "Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker is installed: $(docker --version)"
}

# Check if Docker Compose is installed
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    print_success "Docker Compose is installed: $(docker-compose --version)"
}

# Wait for service to be healthy
wait_for_healthy() {
    local container_name=$1
    local max_wait=60
    local count=0

    print_info "Waiting for $container_name to be healthy..."

    while [ $count -lt $max_wait ]; do
        status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "no healthcheck")

        if [ "$status" = "healthy" ]; then
            print_success "$container_name is healthy"
            return 0
        fi

        if [ "$status" = "no healthcheck" ]; then
            # Container doesn't have healthcheck, check if it's running
            if docker ps --filter "name=$container_name" --format '{{.Names}}' | grep -q "$container_name"; then
                print_warning "$container_name is running (no healthcheck)"
                return 0
            fi
        fi

        sleep 2
        count=$((count + 2))
        echo -n "."
    done

    echo ""
    print_error "$container_name failed to become healthy after ${max_wait}s"
    return 1
}

# Main function
main() {
    print_header "AI-Shell Database Integration Environment"

    # Change to script directory
    cd "$SCRIPT_DIR"

    # Step 1: Check prerequisites
    print_header "Step 1: Checking Prerequisites"
    check_docker
    check_docker_compose

    # Step 2: Parse arguments
    COMPOSE_FILE="docker-compose.yml"
    PROFILES=""
    VERIFY=true

    while [[ $# -gt 0 ]]; do
        case $1 in
            --full)
                COMPOSE_FILE="docker-compose.full.yml"
                shift
                ;;
            --ui)
                PROFILES="--profile ui"
                shift
                ;;
            --optional)
                PROFILES="${PROFILES} --profile optional"
                shift
                ;;
            --no-verify)
                VERIFY=false
                shift
                ;;
            --stop)
                print_header "Stopping All Containers"
                docker-compose -f docker-compose.yml down
                [ -f docker-compose.full.yml ] && docker-compose -f docker-compose.full.yml down
                print_success "All containers stopped"
                exit 0
                ;;
            --clean)
                print_header "Stopping All Containers and Removing Volumes"
                print_warning "This will DELETE all data in the database volumes!"
                read -p "Are you sure? (yes/no): " confirm
                if [ "$confirm" = "yes" ]; then
                    docker-compose -f docker-compose.yml down -v
                    [ -f docker-compose.full.yml ] && docker-compose -f docker-compose.full.yml down -v
                    print_success "All containers and volumes removed"
                else
                    print_info "Cancelled"
                fi
                exit 0
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --full          Use docker-compose.full.yml (includes optional databases)"
                echo "  --ui            Start with management UIs (pgAdmin, Mongo Express, etc.)"
                echo "  --optional      Include optional databases (Neo4j, Cassandra, Oracle)"
                echo "  --no-verify     Skip connection verification"
                echo "  --stop          Stop all running containers"
                echo "  --clean         Stop containers and remove all volumes (DELETES DATA)"
                echo "  --help, -h      Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0                          # Start core databases"
                echo "  $0 --full --ui              # Start all databases with UIs"
                echo "  $0 --full --optional --ui   # Start everything"
                echo "  $0 --stop                   # Stop all containers"
                echo "  $0 --clean                  # Clean up everything"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    # Step 3: Start containers
    print_header "Step 2: Starting Database Containers"
    print_info "Using compose file: $COMPOSE_FILE"
    [ -n "$PROFILES" ] && print_info "Profiles: $PROFILES"

    docker-compose -f "$COMPOSE_FILE" $PROFILES up -d

    if [ $? -ne 0 ]; then
        print_error "Failed to start containers"
        exit 1
    fi

    print_success "Containers started successfully"

    # Step 4: Wait for containers to be healthy
    print_header "Step 3: Waiting for Containers to be Healthy"

    # Core databases
    wait_for_healthy "test_postgres" || true
    wait_for_healthy "test_mongodb" || true
    wait_for_healthy "test_mysql" || true
    wait_for_healthy "test_redis" || true

    # Optional databases (if using full compose file)
    if [ "$COMPOSE_FILE" = "docker-compose.full.yml" ] && [[ "$PROFILES" =~ "optional" ]]; then
        wait_for_healthy "test_neo4j" || true
        wait_for_healthy "test_cassandra" || true
        wait_for_healthy "test_oracle" || true
    fi

    # Step 5: Verify connections
    if [ "$VERIFY" = true ]; then
        print_header "Step 4: Verifying Connections"

        if command -v python3 &> /dev/null; then
            python3 test_docker_setup.py
        else
            print_warning "Python3 not found, skipping automated verification"
            print_info "You can manually verify containers with: docker-compose ps"
        fi
    fi

    # Step 6: Display connection information
    print_header "Setup Complete!"

    echo -e "\n${GREEN}Connection Strings:${NC}"
    echo "  PostgreSQL: postgresql://postgres:MyPostgresPass123@localhost:5432/postgres"
    echo "  MongoDB:    mongodb://admin:MyMongoPass123@localhost:27017/test_integration_db?authSource=admin"
    echo "  MySQL:      mysql://testuser:testpass@localhost:3306/test_integration_db"
    echo "  Redis:      redis://:MyRedisPass123@localhost:6379/0"

    if [[ "$PROFILES" =~ "ui" ]]; then
        echo -e "\n${GREEN}Management UIs:${NC}"
        echo "  pgAdmin:        http://localhost:8084 (admin@aishell.com / admin123)"
        echo "  Mongo Express:  http://localhost:8082 (admin / admin123)"
        echo "  phpMyAdmin:     http://localhost:8083 (root / MyMySQLPass123)"
        echo "  Redis Commander: http://localhost:8081"
    fi

    echo -e "\n${GREEN}Useful Commands:${NC}"
    echo "  docker-compose ps              # View container status"
    echo "  docker-compose logs -f         # View logs"
    echo "  docker-compose stop            # Stop containers"
    echo "  docker-compose down            # Stop and remove containers"
    echo "  docker-compose down -v         # Stop, remove containers and volumes"
    echo "  ./start-databases.sh --stop    # Stop all containers"
    echo "  ./start-databases.sh --clean   # Clean up everything"

    print_success "\nYour database environment is ready for testing!"
}

# Run main function
main "$@"
