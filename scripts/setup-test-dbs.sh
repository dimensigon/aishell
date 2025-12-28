#!/bin/bash
#
# Setup Test Databases for AI-Shell Integration Tests
#
# This script starts all test database containers and waits for them to be ready.
# Uses Docker Compose with tmpfs volumes for fast test execution.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Print functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not available"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

print_info "Starting test databases..."

# Start containers using Docker Compose
docker compose -f docker-compose.test.yml up -d

if [ $? -ne 0 ]; then
    print_error "Failed to start test database containers"
    exit 1
fi

print_success "Test database containers started"

# Wait for databases to be ready
print_info "Waiting for databases to be ready..."

# Function to wait for a container to be healthy
wait_for_healthy() {
    local container_name=$1
    local max_wait=60
    local count=0

    while [ $count -lt $max_wait ]; do
        if docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null | grep -q "healthy"; then
            return 0
        fi
        sleep 1
        count=$((count + 1))
        echo -n "."
    done
    echo ""
    return 1
}

# Wait for PostgreSQL
print_info "Waiting for PostgreSQL..."
if wait_for_healthy "aishell_test_postgres"; then
    print_success "PostgreSQL is ready"

    # Load initialization script if it exists
    if [ -f "tests/integration/database/init-postgres.sql" ]; then
        print_info "Loading PostgreSQL test data..."
        docker exec -i aishell_test_postgres psql -U postgres -d postgres < tests/integration/database/init-postgres.sql 2>&1 | grep -v "NOTICE" || true
        print_success "PostgreSQL test data loaded"
    fi
else
    print_error "PostgreSQL failed to start"
fi

# Wait for MongoDB
print_info "Waiting for MongoDB..."
if wait_for_healthy "aishell_test_mongodb"; then
    print_success "MongoDB is ready"

    # Load initialization script if it exists
    if [ -f "tests/integration/database/init-mongo.js" ]; then
        print_info "Loading MongoDB test data..."
        docker exec -i aishell_test_mongodb mongosh -u admin -p MyMongoPass123 --authenticationDatabase admin test_integration_db < tests/integration/database/init-mongo.js >/dev/null 2>&1 || true
        print_success "MongoDB test data loaded"
    fi
else
    print_error "MongoDB failed to start"
fi

# Wait for MySQL
print_info "Waiting for MySQL..."
if wait_for_healthy "aishell_test_mysql"; then
    print_success "MySQL is ready"

    # Load initialization script if it exists
    if [ -f "tests/integration/database/init-mysql.sql" ]; then
        print_info "Loading MySQL test data..."
        docker exec -i aishell_test_mysql mysql -uroot -pMyMySQLPass123 test_db < tests/integration/database/init-mysql.sql 2>&1 | grep -v "Warning" || true
        print_success "MySQL test data loaded"
    fi
else
    print_error "MySQL failed to start"
fi

# Wait for Redis
print_info "Waiting for Redis..."
if wait_for_healthy "aishell_test_redis"; then
    print_success "Redis is ready"
else
    print_error "Redis failed to start"
fi

echo ""
print_success "All test databases are ready!"
echo ""
echo "Connection strings:"
echo "  PostgreSQL: postgresql://postgres:MyPostgresPass123@localhost:5432/postgres"
echo "  MongoDB:    mongodb://admin:MyMongoPass123@localhost:27017/test_integration_db?authSource=admin"
echo "  MySQL:      mysql://root:MyMySQLPass123@localhost:3306/test_db"
echo "  Redis:      redis://localhost:6379"
echo ""
echo "Run tests with: npm test tests/integration/"
