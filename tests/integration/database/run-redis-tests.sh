#!/bin/bash

# Redis Integration Test Runner Script
# Manages Docker environment and executes Redis integration tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.redis.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_message "$RED" "❌ Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_message "$GREEN" "✅ Docker is running"
}

# Start Redis container
start_redis() {
    print_message "$BLUE" "🚀 Starting Redis container..."

    docker-compose -f "$COMPOSE_FILE" up -d redis

    print_message "$YELLOW" "⏳ Waiting for Redis to be healthy..."

    # Wait for Redis to be healthy (max 30 seconds)
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if docker-compose -f "$COMPOSE_FILE" ps | grep -q "healthy"; then
            print_message "$GREEN" "✅ Redis is healthy and ready"
            return 0
        fi

        attempt=$((attempt + 1))
        echo -n "."
        sleep 1
    done

    print_message "$RED" "❌ Redis failed to become healthy after 30 seconds"
    docker-compose -f "$COMPOSE_FILE" logs redis
    exit 1
}

# Stop Redis container
stop_redis() {
    print_message "$BLUE" "🛑 Stopping Redis container..."
    docker-compose -f "$COMPOSE_FILE" down
    print_message "$GREEN" "✅ Redis container stopped"
}

# Run tests
run_tests() {
    local test_pattern=${1:-""}

    print_message "$BLUE" "🧪 Running Redis integration tests..."

    cd "$SCRIPT_DIR/../../.."  # Go to project root

    if [ -z "$test_pattern" ]; then
        npm test tests/integration/database/test-redis-integration.ts
    else
        npm test tests/integration/database/test-redis-integration.ts -- -t "$test_pattern"
    fi

    local test_exit_code=$?

    if [ $test_exit_code -eq 0 ]; then
        print_message "$GREEN" "✅ All tests passed!"
    else
        print_message "$RED" "❌ Tests failed with exit code $test_exit_code"
    fi

    return $test_exit_code
}

# Show usage
show_usage() {
    cat <<EOF
Usage: $0 [COMMAND] [OPTIONS]

Commands:
    start           Start Redis container
    stop            Stop Redis container
    test            Run all tests (starts Redis if needed)
    test [PATTERN]  Run tests matching pattern
    restart         Restart Redis container
    logs            Show Redis container logs
    cli             Connect to Redis CLI
    status          Check Redis container status
    clean           Stop and remove all containers and volumes
    ui              Start Redis Commander UI
    help            Show this help message

Examples:
    $0 test                      # Run all tests
    $0 test "String Operations"  # Run specific test suite
    $0 start                     # Start Redis only
    $0 logs                      # View Redis logs
    $0 cli                       # Connect to Redis CLI
    $0 ui                        # Start Redis with web UI

EOF
}

# Main script logic
main() {
    local command=${1:-"test"}
    shift || true

    case "$command" in
        start)
            check_docker
            start_redis
            ;;

        stop)
            stop_redis
            ;;

        test)
            check_docker
            start_redis
            run_tests "$@"
            local exit_code=$?
            # Don't stop Redis to allow inspection
            print_message "$YELLOW" "ℹ️  Redis container is still running. Use '$0 stop' to stop it."
            exit $exit_code
            ;;

        restart)
            check_docker
            print_message "$BLUE" "🔄 Restarting Redis container..."
            stop_redis
            start_redis
            ;;

        logs)
            docker-compose -f "$COMPOSE_FILE" logs -f redis
            ;;

        cli)
            print_message "$BLUE" "🔌 Connecting to Redis CLI..."
            print_message "$YELLOW" "ℹ️  Type 'exit' to quit. Try: SELECT 15; KEYS *"
            docker exec -it redis-test-integration redis-cli
            ;;

        status)
            print_message "$BLUE" "📊 Redis container status:"
            docker-compose -f "$COMPOSE_FILE" ps
            echo ""
            print_message "$BLUE" "Redis info:"
            docker exec redis-test-integration redis-cli INFO server | grep -E "redis_version|uptime_in_seconds|connected_clients"
            ;;

        clean)
            print_message "$YELLOW" "⚠️  This will remove all Redis test containers and volumes"
            read -p "Are you sure? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                docker-compose -f "$COMPOSE_FILE" down -v
                print_message "$GREEN" "✅ Cleaned up Redis test environment"
            else
                print_message "$BLUE" "Cancelled"
            fi
            ;;

        ui)
            check_docker
            print_message "$BLUE" "🚀 Starting Redis with Commander UI..."
            docker-compose -f "$COMPOSE_FILE" --profile ui up -d
            print_message "$YELLOW" "⏳ Waiting for services to start..."
            sleep 5
            print_message "$GREEN" "✅ Redis Commander UI available at: http://localhost:8081"
            print_message "$YELLOW" "ℹ️  Use '$0 stop' to stop all services"
            ;;

        help|--help|-h)
            show_usage
            ;;

        *)
            print_message "$RED" "❌ Unknown command: $command"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main with all arguments
main "$@"
