#!/bin/bash

# AI-Shell Integration Test Runner
# Runs database integration tests with external and managed containers

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     AI-Shell Database Integration Test Runner               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Function to check external containers
check_external_containers() {
    local mysql_running=false
    local oracle_running=false

    echo -e "${BLUE}[1/5]${NC} Checking external containers..."

    # Check MySQL
    if docker ps --format '{{.Names}}' | grep -q "^tstmysql$"; then
        if docker exec tstmysql mysqladmin ping -h localhost -u root -pMyMySQLPass123 2>/dev/null | grep -q "mysqld is alive"; then
            echo -e "  ${GREEN}✓${NC} MySQL container 'tstmysql' is running and healthy"
            mysql_running=true
        else
            echo -e "  ${YELLOW}⚠${NC}  MySQL container 'tstmysql' is running but not ready"
        fi
    else
        echo -e "  ${RED}✗${NC} MySQL container 'tstmysql' not found"
        echo -e "     ${YELLOW}Run: docker ps | grep tstmysql${NC}"
    fi

    # Check Oracle
    if docker ps --format '{{.Names}}' | grep -q "^tstoracle$"; then
        echo -e "  ${GREEN}✓${NC} Oracle container 'tstoracle' is running"
        oracle_running=true
        # Quick health check (may be slow)
        if docker exec tstoracle bash -c "echo 'SELECT 1 FROM DUAL;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/FREE as sysdba 2>/dev/null" | grep -q "1" 2>/dev/null; then
            echo -e "     ${GREEN}✓${NC} Oracle is healthy and accepting connections"
        else
            echo -e "     ${YELLOW}⚠${NC}  Oracle may still be starting up (this can take 5-10 minutes)"
        fi
    else
        echo -e "  ${RED}✗${NC} Oracle container 'tstoracle' not found"
        echo -e "     ${YELLOW}Run: docker ps | grep tstoracle${NC}"
    fi

    if [ "$mysql_running" = false ] || [ "$oracle_running" = false ]; then
        echo ""
        echo -e "${RED}ERROR:${NC} Required external containers are not running"
        echo ""
        echo "Required containers:"
        echo "  - MySQL container named 'tstmysql' on port 3307"
        echo "  - Oracle container named 'tstoracle' on port 1521"
        echo ""
        echo "See documentation:"
        echo "  - docker/EXTERNAL_MYSQL_SETUP.md"
        echo "  - docker/EXTERNAL_ORACLE_SETUP.md"
        return 1
    fi

    return 0
}

# Function to check managed containers
check_managed_containers() {
    echo ""
    echo -e "${BLUE}[2/5]${NC} Checking managed containers..."

    local all_healthy=true

    # Check PostgreSQL
    if docker ps --format '{{.Names}}' | grep -q "^aishell-postgres-test$"; then
        if docker exec aishell-postgres-test pg_isready -U postgres 2>/dev/null | grep -q "accepting connections"; then
            echo -e "  ${GREEN}✓${NC} PostgreSQL is healthy"
        else
            echo -e "  ${RED}✗${NC} PostgreSQL is not ready"
            all_healthy=false
        fi
    else
        echo -e "  ${RED}✗${NC} PostgreSQL container not found"
        all_healthy=false
    fi

    # Check MongoDB
    if docker ps --format '{{.Names}}' | grep -q "^aishell-mongodb-test$"; then
        if docker exec aishell-mongodb-test mongosh --quiet --eval "db.adminCommand('ping').ok" 2>/dev/null | grep -q "1"; then
            echo -e "  ${GREEN}✓${NC} MongoDB is healthy"
        else
            echo -e "  ${RED}✗${NC} MongoDB is not ready"
            all_healthy=false
        fi
    else
        echo -e "  ${RED}✗${NC} MongoDB container not found"
        all_healthy=false
    fi

    # Check Redis
    if docker ps --format '{{.Names}}' | grep -q "^aishell-redis-test$"; then
        if docker exec aishell-redis-test redis-cli ping 2>/dev/null | grep -q "PONG"; then
            echo -e "  ${GREEN}✓${NC} Redis is healthy"
        else
            echo -e "  ${RED}✗${NC} Redis is not ready"
            all_healthy=false
        fi
    else
        echo -e "  ${RED}✗${NC} Redis container not found"
        all_healthy=false
    fi

    if [ "$all_healthy" = false ]; then
        echo ""
        echo -e "${YELLOW}WARNING:${NC} Some managed containers are not healthy"
        echo "Starting managed containers..."
        docker compose -f docker-compose.test.yml --env-file .env.test up -d
        echo "Waiting 10 seconds for services to start..."
        sleep 10
    fi

    return 0
}

# Function to run tests
run_tests() {
    echo ""
    echo -e "${BLUE}[3/5]${NC} Running integration tests..."
    echo ""

    cd ..

    # Run tests with timeout - use glob pattern to match test files
    if timeout 600 npm test -- tests/integration/database/*.integration.test.ts 2>&1 | tee docker/test-results.log; then
        return 0
    else
        return 1
    fi
}

# Function to show summary
show_summary() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              Test Execution Summary                          ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    if [ -f docker/test-results.log ]; then
        echo -e "${BLUE}Test Results:${NC}"
        grep -E "Test Files|Tests |Duration" docker/test-results.log | tail -5 || echo "No summary available"
    fi

    echo ""
}

# Main execution
main() {
    # Check external containers
    if ! check_external_containers; then
        exit 1
    fi

    # Check managed containers
    check_managed_containers

    # Run tests
    echo ""
    echo -e "${BLUE}[4/5]${NC} Executing test suite..."
    if run_tests; then
        echo ""
        echo -e "${GREEN}[5/5] ✓ All tests completed successfully!${NC}"
        test_result=0
    else
        echo ""
        echo -e "${YELLOW}[5/5] ⚠ Some tests failed or timed out${NC}"
        test_result=1
    fi

    # Show summary
    show_summary

    # Connection info
    echo ""
    echo -e "${BLUE}Database Connection Strings:${NC}"
    echo "  PostgreSQL: postgresql://postgres:MyPostgresPass123@localhost:5432/testdb"
    echo "  MySQL:      mysql://root:MyMySQLPass123@localhost:3307"
    echo "  MongoDB:    mongodb://admin:MyMongoPass123@localhost:27017/testdb"
    echo "  Redis:      redis://localhost:6379"
    echo "  Oracle CDB: SYS/MyOraclePass123@//localhost:1521/free as SYSDBA"
    echo "  Oracle PDB: SYS/MyOraclePass123@//localhost:1521/freepdb1 as SYSDBA"
    echo ""

    exit $test_result
}

# Run main function
main
