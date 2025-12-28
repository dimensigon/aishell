#!/bin/bash
#
# MongoDB Integration Test Runner
# Manages Docker container lifecycle and test execution
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="test_mongodb"
MONGO_URI="mongodb://admin:MyMongoPass123@localhost:27017"
MAX_WAIT=60  # Maximum seconds to wait for MongoDB

# Functions
print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Check if MongoDB container is running
is_container_running() {
    docker ps --filter "name=$CONTAINER_NAME" --filter "status=running" --format '{{.Names}}' | grep -q "$CONTAINER_NAME"
}

# Wait for MongoDB to be ready
wait_for_mongodb() {
    print_info "Waiting for MongoDB to be ready..."
    local elapsed=0

    while [ $elapsed -lt $MAX_WAIT ]; do
        if docker exec $CONTAINER_NAME mongosh --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; then
            print_success "MongoDB is ready!"
            return 0
        fi

        echo -n "."
        sleep 2
        elapsed=$((elapsed + 2))
    done

    print_error "MongoDB failed to start within ${MAX_WAIT} seconds"
    docker-compose -f "$SCRIPT_DIR/docker-compose.yml" logs mongodb
    return 1
}

# Start MongoDB container
start_mongodb() {
    print_header "Starting MongoDB Container"

    cd "$SCRIPT_DIR"

    if is_container_running; then
        print_warning "MongoDB container is already running"
    else
        print_info "Starting MongoDB with Docker Compose..."
        docker-compose up -d

        if [ $? -eq 0 ]; then
            print_success "Container started"
        else
            print_error "Failed to start container"
            exit 1
        fi
    fi

    wait_for_mongodb
}

# Stop MongoDB container
stop_mongodb() {
    print_header "Stopping MongoDB Container"

    cd "$SCRIPT_DIR"

    if is_container_running; then
        docker-compose down
        print_success "Container stopped"
    else
        print_warning "Container is not running"
    fi
}

# Clean up containers and volumes
cleanup() {
    print_header "Cleaning Up"

    cd "$SCRIPT_DIR"
    docker-compose down -v
    print_success "Containers and volumes removed"
}

# Show container logs
show_logs() {
    print_header "MongoDB Logs"
    cd "$SCRIPT_DIR"
    docker-compose logs mongodb
}

# Show container status
show_status() {
    print_header "Container Status"
    cd "$SCRIPT_DIR"
    docker-compose ps

    echo ""
    if is_container_running; then
        print_success "MongoDB is running"

        # Show MongoDB version and stats
        echo ""
        print_info "MongoDB Version:"
        docker exec $CONTAINER_NAME mongosh --quiet --eval "db.version()"

        echo ""
        print_info "Database Statistics:"
        docker exec $CONTAINER_NAME mongosh "$MONGO_URI/test_integration_db" --quiet --eval "
            print('Collections:', db.getCollectionNames().length);
            db.getCollectionNames().forEach(function(col) {
                print('  - ' + col + ':', db[col].countDocuments(), 'documents');
            });
        " 2>/dev/null || echo "Database not yet initialized"
    else
        print_error "MongoDB is not running"
    fi
}

# Run integration tests
run_tests() {
    print_header "Running MongoDB Integration Tests"

    cd "$PROJECT_ROOT"

    # Ensure MongoDB is running
    if ! is_container_running; then
        print_warning "MongoDB is not running. Starting container..."
        start_mongodb
    fi

    # Run tests
    print_info "Executing test suite..."
    npm run test tests/integration/database/test-mongodb-integration.ts

    TEST_EXIT_CODE=$?

    if [ $TEST_EXIT_CODE -eq 0 ]; then
        print_success "All tests passed!"
    else
        print_error "Some tests failed (exit code: $TEST_EXIT_CODE)"
    fi

    return $TEST_EXIT_CODE
}

# Run tests with coverage
run_tests_coverage() {
    print_header "Running Tests with Coverage"

    cd "$PROJECT_ROOT"

    if ! is_container_running; then
        start_mongodb
    fi

    npm run test:coverage -- tests/integration/database/test-mongodb-integration.ts
}

# Interactive shell
interactive_shell() {
    print_header "MongoDB Interactive Shell"

    if ! is_container_running; then
        print_error "MongoDB is not running. Start it with: $0 start"
        exit 1
    fi

    print_info "Connecting to MongoDB..."
    docker exec -it $CONTAINER_NAME mongosh "$MONGO_URI/test_integration_db"
}

# Show help
show_help() {
    cat << EOF
MongoDB Integration Test Runner

Usage: $0 [COMMAND]

Commands:
    start       Start MongoDB container
    stop        Stop MongoDB container
    restart     Restart MongoDB container
    cleanup     Stop container and remove volumes

    test        Run integration tests
    coverage    Run tests with coverage report

    status      Show container status
    logs        Show container logs
    shell       Open MongoDB interactive shell

    help        Show this help message

Examples:
    $0 start         # Start MongoDB container
    $0 test          # Run all integration tests
    $0 coverage      # Run tests with coverage
    $0 shell         # Open MongoDB shell
    $0 cleanup       # Clean up everything

Environment Variables:
    MONGO_URI       MongoDB connection URI (default: $MONGO_URI)
    MAX_WAIT        Maximum seconds to wait for MongoDB (default: $MAX_WAIT)

EOF
}

# Main script logic
main() {
    case "${1:-}" in
        start)
            check_docker
            start_mongodb
            show_status
            ;;
        stop)
            check_docker
            stop_mongodb
            ;;
        restart)
            check_docker
            stop_mongodb
            sleep 2
            start_mongodb
            ;;
        cleanup)
            check_docker
            cleanup
            ;;
        test)
            check_docker
            run_tests
            ;;
        coverage)
            check_docker
            run_tests_coverage
            ;;
        status)
            check_docker
            show_status
            ;;
        logs)
            check_docker
            show_logs
            ;;
        shell)
            check_docker
            interactive_shell
            ;;
        help|--help|-h)
            show_help
            ;;
        "")
            print_error "No command specified"
            echo ""
            show_help
            exit 1
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
