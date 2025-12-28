#!/bin/bash

# MCP Integration Test Runner
# This script starts Docker containers and runs all integration tests

set -e

echo "========================================="
echo "MCP Integration Test Suite"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to check if Docker is running
check_docker() {
    echo -e "${YELLOW}Checking Docker...${NC}"
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}Error: Docker is not running${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker is running${NC}"
}

# Function to start Docker containers
start_containers() {
    echo -e "${YELLOW}Starting Docker containers...${NC}"

    # Create temporary docker-compose file
    cat > docker-compose.test.yml <<EOF
version: '3.8'

services:
  postgresql:
    image: postgres:15-alpine
    container_name: mcp-test-postgres
    environment:
      POSTGRES_PASSWORD: MyPostgresPass123
      POSTGRES_DB: test_integration_db
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5
    volumes:
      - postgres-data:/var/lib/postgresql/data

  mysql:
    image: mysql:8.0
    container_name: mcp-test-mysql
    environment:
      MYSQL_ROOT_PASSWORD: MyMySQLPass123
      MYSQL_DATABASE: test_integration_db
    ports:
      - "3306:3306"
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 5s
      timeout: 3s
      retries: 5
    volumes:
      - mysql-data:/var/lib/mysql

  mongodb:
    image: mongo:7.0
    container_name: mcp-test-mongodb
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: MyMongoPass123
      MONGO_INITDB_DATABASE: test_integration_db
    ports:
      - "27017:27017"
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 5s
      timeout: 3s
      retries: 5
    volumes:
      - mongodb-data:/data/db

  redis:
    image: redis:7-alpine
    container_name: mcp-test-redis
    command: redis-server --requirepass MyRedisPass123
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    volumes:
      - redis-data:/data

volumes:
  postgres-data:
  mysql-data:
  mongodb-data:
  redis-data:
EOF

    # Start containers
    docker-compose -f docker-compose.test.yml up -d

    echo -e "${YELLOW}Waiting for containers to be healthy...${NC}"

    # Wait for all containers to be healthy
    max_wait=60
    elapsed=0

    while [ $elapsed -lt $max_wait ]; do
        healthy_count=0

        for container in mcp-test-postgres mcp-test-mysql mcp-test-mongodb mcp-test-redis; do
            health=$(docker inspect --format='{{.State.Health.Status}}' $container 2>/dev/null || echo "starting")
            if [ "$health" = "healthy" ]; then
                ((healthy_count++))
            fi
        done

        if [ $healthy_count -eq 4 ]; then
            echo -e "${GREEN}✓ All containers are healthy${NC}"
            break
        fi

        echo "Waiting for containers... ($elapsed/$max_wait seconds)"
        sleep 2
        ((elapsed+=2))
    done

    if [ $elapsed -ge $max_wait ]; then
        echo -e "${RED}Error: Containers failed to become healthy${NC}"
        docker-compose -f docker-compose.test.yml logs
        exit 1
    fi
}

# Function to run tests
run_tests() {
    echo -e "${YELLOW}Running integration tests...${NC}"

    # Install dependencies if needed
    if ! python3 -c "import pytest" 2>/dev/null; then
        echo "Installing test dependencies..."
        pip install pytest pytest-asyncio psycopg pymongo redis motor aiosqlite mysql-connector-python pyyaml
    fi

    # Run tests with coverage
    python3 -m pytest \
        tests/integration/mcp/ \
        -v \
        --tb=short \
        --color=yes \
        --cov=src/mcp \
        --cov-report=term-missing \
        --cov-report=html:htmlcov \
        --cov-report=xml:coverage.xml

    test_result=$?

    if [ $test_result -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed!${NC}"
    else
        echo -e "${RED}✗ Some tests failed${NC}"
    fi

    return $test_result
}

# Function to generate test report
generate_report() {
    echo -e "${YELLOW}Generating test report...${NC}"

    if [ -f htmlcov/index.html ]; then
        echo -e "${GREEN}✓ Coverage report generated: htmlcov/index.html${NC}"
    fi

    if [ -f coverage.xml ]; then
        echo -e "${GREEN}✓ Coverage XML generated: coverage.xml${NC}"
    fi
}

# Function to cleanup
cleanup() {
    echo -e "${YELLOW}Cleaning up...${NC}"

    if [ -f docker-compose.test.yml ]; then
        docker-compose -f docker-compose.test.yml down -v
        rm docker-compose.test.yml
    fi

    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    check_docker
    start_containers

    if run_tests; then
        generate_report
        echo -e "${GREEN}=========================================${NC}"
        echo -e "${GREEN}Integration tests completed successfully!${NC}"
        echo -e "${GREEN}=========================================${NC}"
        exit 0
    else
        echo -e "${RED}=========================================${NC}"
        echo -e "${RED}Integration tests failed!${NC}"
        echo -e "${RED}=========================================${NC}"
        exit 1
    fi
}

# Parse command line arguments
SKIP_DOCKER=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        --help)
            echo "Usage: ./run_tests.sh [options]"
            echo ""
            echo "Options:"
            echo "  --skip-docker    Skip Docker container startup (use existing containers)"
            echo "  --help           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [ "$SKIP_DOCKER" = true ]; then
    echo -e "${YELLOW}Skipping Docker startup (using existing containers)${NC}"
    run_tests
    generate_report
else
    main
fi
