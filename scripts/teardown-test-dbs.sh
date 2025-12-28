#!/bin/bash
#
# Teardown Test Databases for AI-Shell Integration Tests
#
# This script stops and removes all test database containers.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Print functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_info "Stopping test databases..."

# Stop and remove containers
docker compose -f docker-compose.test.yml down

if [ $? -eq 0 ]; then
    print_success "Test database containers stopped and removed"
else
    print_info "No containers to stop"
fi

# Optional: Remove volumes if --volumes flag is passed
if [ "$1" = "--volumes" ] || [ "$1" = "-v" ]; then
    print_info "Removing volumes..."
    docker compose -f docker-compose.test.yml down -v
    print_success "Volumes removed"
fi

print_success "Test database teardown complete"
