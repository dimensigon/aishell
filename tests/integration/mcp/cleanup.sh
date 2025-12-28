#!/bin/bash

# MCP Integration Test Cleanup Script
# This script stops and removes all test containers and volumes

set -e

echo "========================================="
echo "MCP Integration Test Cleanup"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to stop and remove containers
stop_containers() {
    echo -e "${YELLOW}Stopping test containers...${NC}"

    containers="mcp-test-postgres mcp-test-mysql mcp-test-mongodb mcp-test-redis"

    for container in $containers; do
        if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
            echo "Stopping $container..."
            docker stop $container > /dev/null 2>&1 || true
            docker rm $container > /dev/null 2>&1 || true
            echo -e "${GREEN}✓ Removed $container${NC}"
        else
            echo "Container $container not found"
        fi
    done
}

# Function to remove volumes
remove_volumes() {
    echo -e "${YELLOW}Removing test volumes...${NC}"

    volumes="postgres-data mysql-data mongodb-data redis-data"

    for volume in $volumes; do
        if docker volume ls --format '{{.Name}}' | grep -q "^${volume}$"; then
            echo "Removing volume $volume..."
            docker volume rm $volume > /dev/null 2>&1 || true
            echo -e "${GREEN}✓ Removed volume $volume${NC}"
        else
            echo "Volume $volume not found"
        fi
    done
}

# Function to clean up test artifacts
cleanup_artifacts() {
    echo -e "${YELLOW}Cleaning up test artifacts...${NC}"

    # Remove coverage files
    if [ -d "htmlcov" ]; then
        rm -rf htmlcov
        echo -e "${GREEN}✓ Removed htmlcov directory${NC}"
    fi

    if [ -f "coverage.xml" ]; then
        rm coverage.xml
        echo -e "${GREEN}✓ Removed coverage.xml${NC}"
    fi

    if [ -f ".coverage" ]; then
        rm .coverage
        echo -e "${GREEN}✓ Removed .coverage${NC}"
    fi

    # Remove pytest cache
    if [ -d ".pytest_cache" ]; then
        rm -rf .pytest_cache
        echo -e "${GREEN}✓ Removed .pytest_cache${NC}"
    fi

    # Remove docker-compose file if exists
    if [ -f "docker-compose.test.yml" ]; then
        rm docker-compose.test.yml
        echo -e "${GREEN}✓ Removed docker-compose.test.yml${NC}"
    fi
}

# Function to clean up SQLite test databases
cleanup_sqlite() {
    echo -e "${YELLOW}Cleaning up SQLite test databases...${NC}"

    find /tmp -name "test*.db*" -type f -mtime -1 -delete 2>/dev/null || true

    echo -e "${GREEN}✓ Cleaned up SQLite databases${NC}"
}

# Main cleanup
main() {
    stop_containers
    remove_volumes
    cleanup_artifacts
    cleanup_sqlite

    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}Cleanup completed successfully!${NC}"
    echo -e "${GREEN}=========================================${NC}"
}

# Parse command line arguments
FULL_CLEANUP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            FULL_CLEANUP=true
            shift
            ;;
        --help)
            echo "Usage: ./cleanup.sh [options]"
            echo ""
            echo "Options:"
            echo "  --full     Perform full cleanup (including Docker images)"
            echo "  --help     Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

main

if [ "$FULL_CLEANUP" = true ]; then
    echo -e "${YELLOW}Performing full cleanup (removing Docker images)...${NC}"

    images="postgres:15-alpine mysql:8.0 mongo:7.0 redis:7-alpine"

    for image in $images; do
        if docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^${image}$"; then
            echo "Removing image $image..."
            docker rmi $image > /dev/null 2>&1 || true
            echo -e "${GREEN}✓ Removed image $image${NC}"
        fi
    done

    echo -e "${GREEN}Full cleanup completed!${NC}"
fi
