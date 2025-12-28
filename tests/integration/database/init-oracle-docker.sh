#!/bin/bash
#
# Oracle Database Test Data Initialization Script
# Initializes test data in Oracle Docker container for integration tests
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQL_FILE="${SCRIPT_DIR}/init-oracle.sql"
CONTAINER_NAME="${ORACLE_CONTAINER:-oracle-free}"
ORACLE_PWD="${ORACLE_PWD:-MyOraclePass123}"
ORACLE_SERVICE="${ORACLE_SERVICE:-FREEPDB1}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Oracle Database Test Data Initialization ===${NC}"

# Check if container is running
if ! docker ps | grep -q "${CONTAINER_NAME}"; then
    echo -e "${RED}Error: Oracle container '${CONTAINER_NAME}' is not running${NC}"
    echo -e "${YELLOW}Start it with:${NC}"
    echo "  docker run -d --name ${CONTAINER_NAME} -p 1521:1521 -e ORACLE_PWD=${ORACLE_PWD} container-registry.oracle.com/database/free:latest"
    exit 1
fi

# Check if SQL file exists
if [ ! -f "${SQL_FILE}" ]; then
    echo -e "${RED}Error: SQL file not found: ${SQL_FILE}${NC}"
    exit 1
fi

# Wait for database to be ready
echo -e "${YELLOW}Checking if Oracle database is ready...${NC}"
READY=false
for i in {1..30}; do
    if docker logs "${CONTAINER_NAME}" 2>&1 | grep -q "DATABASE IS READY TO USE"; then
        READY=true
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

if [ "$READY" = false ]; then
    echo -e "${RED}Error: Oracle database is not ready yet${NC}"
    echo -e "${YELLOW}Check logs with: docker logs -f ${CONTAINER_NAME}${NC}"
    exit 1
fi

echo -e "${GREEN}Database is ready!${NC}"

# Copy SQL file to container
echo -e "${YELLOW}Copying SQL file to container...${NC}"
docker cp "${SQL_FILE}" "${CONTAINER_NAME}:/tmp/init-oracle.sql"

# Execute SQL file
echo -e "${YELLOW}Executing SQL initialization script...${NC}"
echo -e "${YELLOW}This may take a few minutes...${NC}"

docker exec -i "${CONTAINER_NAME}" sqlplus -S sys/${ORACLE_PWD}@${ORACLE_SERVICE} as sysdba @/tmp/init-oracle.sql

# Verify test data
echo -e "${YELLOW}Verifying test data...${NC}"
VERIFY_SQL="SELECT COUNT(*) FROM test_user.employees;"

RESULT=$(docker exec "${CONTAINER_NAME}" sqlplus -S sys/${ORACLE_PWD}@${ORACLE_SERVICE} as sysdba <<EOF
SET HEADING OFF
SET FEEDBACK OFF
SET PAGESIZE 0
${VERIFY_SQL}
EXIT;
EOF
)

if [ -n "$RESULT" ] && [ "$RESULT" -gt 0 ]; then
    echo -e "${GREEN}✓ Test data initialized successfully!${NC}"
    echo -e "${GREEN}  - Employees found: ${RESULT}${NC}"
else
    echo -e "${RED}✗ Test data verification failed${NC}"
    exit 1
fi

# Display summary
echo -e "\n${GREEN}=== Initialization Complete ===${NC}"
echo -e "Container: ${CONTAINER_NAME}"
echo -e "Service:   ${ORACLE_SERVICE}"
echo -e "User:      test_user"
echo -e ""
echo -e "${YELLOW}Run tests with:${NC}"
echo -e "  npm test tests/integration/database/test-oracle-integration.ts"
echo -e ""
echo -e "${YELLOW}Connect to database:${NC}"
echo -e "  docker exec -it ${CONTAINER_NAME} sqlplus test_user/TestPass123@${ORACLE_SERVICE}"
