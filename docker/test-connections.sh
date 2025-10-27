#!/bin/bash

# AI-Shell Database Connection Tester
# Tests connectivity to all configured databases

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "AI-Shell Database Connection Tester"
echo "================================================"
echo ""

# Function to test connection
test_connection() {
    local service=$1
    local command=$2
    local description=$3

    echo -n "Testing $description: "
    if eval "$command" &>/dev/null; then
        echo -e "${GREEN}✓ Connected${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi
}

# Check if Docker Compose is running
if ! docker compose -f docker-compose.test.yml ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠ Warning: Services may not be running${NC}"
    echo "Start services with: docker compose -f docker-compose.test.yml up -d"
    echo ""
fi

# Test PostgreSQL
test_connection "postgres" \
    "docker exec aishell-postgres-test pg_isready -U postgres" \
    "PostgreSQL (localhost:5432)"

# Test MySQL (external container)
echo -n "Testing MySQL (external 'tstmysql' container, localhost:3307): "
if docker ps --format '{{.Names}}' | grep -q "^tstmysql$"; then
    if docker exec tstmysql mysqladmin ping -h localhost -u root -pMyMySQLPass123 &>/dev/null; then
        echo -e "${GREEN}✓ Connected${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠ External 'tstmysql' container not found${NC}"
fi

# Test MongoDB
test_connection "mongodb" \
    "docker exec aishell-mongodb-test mongosh --quiet --eval 'db.adminCommand({ping:1}).ok' 2>/dev/null | grep -q 1" \
    "MongoDB (localhost:27017)"

# Test Redis
test_connection "redis" \
    "docker exec aishell-redis-test redis-cli ping | grep -q PONG" \
    "Redis (localhost:6379)"

# Test Oracle (external container 'tstoracle')
echo -n "Testing Oracle DB 23c (external 'tstoracle' container, localhost:1521): "
if docker ps --format '{{.Names}}' | grep -q "^tstoracle$"; then
    if docker exec tstoracle bash -c "echo 'SELECT 1 FROM DUAL;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/FREE as sysdba 2>/dev/null" | grep -q "1"; then
        echo -e "${GREEN}✓ Connected (CDB)${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠ External 'tstoracle' container not found${NC}"
fi

echo ""
echo "================================================"
echo "Connection Test Complete"
echo "================================================"
echo ""
echo "Admin UIs:"
echo "  Adminer (SQL):       http://localhost:8080"
echo "  Mongo Express:       http://localhost:8081"
echo "  Redis Commander:     http://localhost:8082"
echo "  Oracle EM Express:   https://localhost:5500/em"
echo ""
