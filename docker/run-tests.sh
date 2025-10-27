#!/bin/bash

# AI-Shell Docker Test Environment - Automated Test Runner
# This script starts services, waits for health, runs tests, and reports results

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
MAX_WAIT_TIME=180  # Maximum seconds to wait for services
HEALTH_CHECK_INTERVAL=5  # Seconds between health checks
VERBOSE=${VERBOSE:-0}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if service is healthy
check_service_health() {
    local service=$1
    local check_command=$2

    if [ $VERBOSE -eq 1 ]; then
        print_info "Checking $service..."
    fi

    if eval "$check_command" &>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to wait for all services to be healthy
wait_for_services() {
    print_info "Waiting for services to become healthy (max ${MAX_WAIT_TIME}s)..."

    local elapsed=0
    local all_healthy=0

    while [ $elapsed -lt $MAX_WAIT_TIME ]; do
        all_healthy=1

        # Check PostgreSQL
        if ! check_service_health "PostgreSQL" \
            "docker exec aishell-postgres-test pg_isready -U postgres"; then
            all_healthy=0
            [ $VERBOSE -eq 1 ] && print_warning "PostgreSQL not ready yet"
        fi

        # Check MySQL
        if ! check_service_health "MySQL" \
            "docker exec aishell-mysql-test mysqladmin ping -h localhost -u root -pMyMySQLPass123"; then
            all_healthy=0
            [ $VERBOSE -eq 1 ] && print_warning "MySQL not ready yet"
        fi

        # Check MongoDB
        if ! check_service_health "MongoDB" \
            "docker exec aishell-mongodb-test mongosh --quiet --eval 'db.adminCommand({ping:1}).ok' 2>/dev/null | grep -q 1"; then
            all_healthy=0
            [ $VERBOSE -eq 1 ] && print_warning "MongoDB not ready yet"
        fi

        # Check Redis
        if ! check_service_health "Redis" \
            "docker exec aishell-redis-test redis-cli ping | grep -q PONG"; then
            all_healthy=0
            [ $VERBOSE -eq 1 ] && print_warning "Redis not ready yet"
        fi

        # Check Oracle (optional, can take longer)
        if docker ps --format '{{.Names}}' | grep -q aishell-oracle-test; then
            if ! check_service_health "Oracle" \
                "docker exec aishell-oracle-test sqlplus -s sys/MyOraclePass123@//localhost:1521/FREE as sysdba <<< 'SELECT 1 FROM DUAL;' 2>/dev/null | grep -q 1"; then
                [ $VERBOSE -eq 1 ] && print_warning "Oracle not ready yet (this can take 2-3 minutes)"
                # Don't fail on Oracle, it takes longer
            fi
        fi

        if [ $all_healthy -eq 1 ]; then
            print_success "All services are healthy!"
            return 0
        fi

        sleep $HEALTH_CHECK_INTERVAL
        elapsed=$((elapsed + HEALTH_CHECK_INTERVAL))

        if [ $VERBOSE -eq 0 ]; then
            echo -n "."
        fi
    done

    echo ""
    print_error "Services did not become healthy within ${MAX_WAIT_TIME} seconds"
    return 1
}

# Main execution
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}AI-Shell Docker Test Environment - Test Runner${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running"
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version > /dev/null 2>&1; then
    print_error "Docker Compose is not available"
    exit 1
fi

# Start services
print_info "Starting Docker services..."
docker compose -f docker-compose.test.yml --env-file .env.test up -d

if [ $? -ne 0 ]; then
    print_error "Failed to start services"
    exit 1
fi

print_success "Services started"
echo ""

# Wait for services to be healthy
if ! wait_for_services; then
    print_error "Service health check failed"
    print_info "Showing service status:"
    docker compose -f docker-compose.test.yml ps
    print_info "Showing recent logs:"
    docker compose -f docker-compose.test.yml logs --tail=50
    exit 1
fi

echo ""
print_success "All services are ready!"
echo ""

# Run connection tests
print_info "Running connection tests..."
echo ""

if bash test-connections.sh; then
    print_success "All connection tests passed!"
else
    print_warning "Some connection tests failed"
fi

echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Test Environment Summary${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Show service status
print_info "Service Status:"
docker compose -f docker-compose.test.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
print_success "Test environment is ready!"
echo ""
echo "Connection information:"
echo "  PostgreSQL:  postgresql://postgres:MyPostgresPass123@localhost:5432/testdb"
echo "  MySQL:       mysql://root:MyMySQLPass123@localhost:3307/testdb"
echo "  MongoDB:     mongodb://admin:MyMongoPass123@localhost:27017/testdb?authSource=admin"
echo "  Redis:       redis://localhost:6379"
echo "  Oracle CDB:  SYS/MyOraclePass123@//localhost:1521/FREE as sysdba"
echo "  Oracle PDB:  SYSTEM/MyOraclePass123@//localhost:1521/FREEPDB1"
echo ""
echo "Admin UIs:"
echo "  Adminer:         http://localhost:8080"
echo "  Mongo Express:   http://localhost:8081 (admin/pass)"
echo "  Redis Commander: http://localhost:8082"
echo ""
echo "To stop services: ./start.sh down"
echo "To view logs:     ./start.sh logs [service]"
echo "To clean up:      ./start.sh clean"
echo ""
