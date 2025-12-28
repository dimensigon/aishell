#!/bin/bash

# AI-Shell Docker Database Integration Test
# Tests database connectivity using docker exec commands

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Test results
declare -a TEST_RESULTS
declare -a FAILED_COMMANDS
declare -a PERFORMANCE_METRICS

# Logging
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="/home/claude/AIShell/aishell/tests/integration/test-${TIMESTAMP}.log"
RESULTS_JSON="/home/claude/AIShell/aishell/tests/integration/test-results.json"

mkdir -p "$(dirname "$LOG_FILE")"

# Test tracking
log_test() {
    local category=$1
    local description=$2
    local status=$3
    local duration=$4
    local message=$5

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ "$status" == "PASS" ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo -e "${GREEN}✓${NC} [$category] $description (${duration}ms)" | tee -a "$LOG_FILE"
        TEST_RESULTS+=("PASS|$category|$description|$duration|$message")
        PERFORMANCE_METRICS+=("$category|$description|$duration")
    elif [ "$status" == "SKIP" ]; then
        SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
        echo -e "${YELLOW}○${NC} [$category] $description - SKIPPED: $message" | tee -a "$LOG_FILE"
        TEST_RESULTS+=("SKIP|$category|$description|0|$message")
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo -e "${RED}✗${NC} [$category] $description - FAILED: $message" | tee -a "$LOG_FILE"
        TEST_RESULTS+=("FAIL|$category|$description|0|$message")
        FAILED_COMMANDS+=("$category: $description - $message")
    fi
}

# Run test
run_test() {
    local category=$1
    local description=$2
    local cmd=$3

    echo -e "\n${BLUE}Testing:${NC} $description" | tee -a "$LOG_FILE"

    local start_time=$(date +%s%3N)
    local output
    local exit_code

    if output=$(timeout 30s bash -c "$cmd" 2>&1); then
        exit_code=0
    else
        exit_code=$?
    fi

    local end_time=$(date +%s%3N)
    local duration=$((end_time - start_time))

    if [ $exit_code -eq 0 ]; then
        log_test "$category" "$description" "PASS" "$duration" "Success"
        return 0
    else
        log_test "$category" "$description" "FAIL" "0" "Exit code: $exit_code"
        return 1
    fi
}

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  AI-Shell Docker Integration Test Suite${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "Start time: $(date)" | tee -a "$LOG_FILE"
echo -e "Log file: $LOG_FILE\n"

#=============================================================================
# CONTAINER STATUS
#=============================================================================
echo -e "\n${BLUE}Checking Docker containers...${NC}"

POSTGRES_CONTAINER=$(docker ps --filter "name=tstpostgres" --format "{{.Names}}" | head -1)
MYSQL_CONTAINER=$(docker ps --filter "name=aishell_test_mysql" --format "{{.Names}}" | head -1)
MONGODB_CONTAINER=$(docker ps --filter "name=aishell_test_mongodb" --format "{{.Names}}" | head -1)
REDIS_CONTAINER=$(docker ps --filter "name=aishell_test_redis" --format "{{.Names}}" | head -1)
ORACLE_CONTAINER=$(docker ps --filter "name=tstoracle" --filter "health=healthy" --format "{{.Names}}" | head -1)

echo "PostgreSQL: ${POSTGRES_CONTAINER:-Not found}"
echo "MySQL:      ${MYSQL_CONTAINER:-Not found}"
echo "MongoDB:    ${MONGODB_CONTAINER:-Not found}"
echo "Redis:      ${REDIS_CONTAINER:-Not found}"
echo "Oracle:     ${ORACLE_CONTAINER:-Not found}"

#=============================================================================
# POSTGRESQL TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  PostgreSQL Tests${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

if [ -n "$POSTGRES_CONTAINER" ]; then
    run_test "PostgreSQL" "Connection test" \
        "docker exec $POSTGRES_CONTAINER psql -U postgres -d postgres -c 'SELECT 1' -t"

    run_test "PostgreSQL" "Version query" \
        "docker exec $POSTGRES_CONTAINER psql -U postgres -d postgres -c 'SELECT version()' -t"

    run_test "PostgreSQL" "List databases" \
        "docker exec $POSTGRES_CONTAINER psql -U postgres -d postgres -c 'SELECT datname FROM pg_database LIMIT 5' -t"

    run_test "PostgreSQL" "Table count" \
        "docker exec $POSTGRES_CONTAINER psql -U postgres -d postgres -c \"SELECT COUNT(*) FROM pg_tables WHERE schemaname='public'\" -t"

    run_test "PostgreSQL" "Active connections" \
        "docker exec $POSTGRES_CONTAINER psql -U postgres -d postgres -c 'SELECT COUNT(*) FROM pg_stat_activity' -t"

    run_test "PostgreSQL" "Create test table" \
        "docker exec $POSTGRES_CONTAINER psql -U postgres -d postgres -c 'CREATE TABLE IF NOT EXISTS integration_test (id SERIAL PRIMARY KEY, data TEXT, created_at TIMESTAMP DEFAULT NOW())' -t"

    run_test "PostgreSQL" "Insert test data" \
        "docker exec $POSTGRES_CONTAINER psql -U postgres -d postgres -c \"INSERT INTO integration_test (data) VALUES ('docker_test')\" -t"

    run_test "PostgreSQL" "Query test data" \
        "docker exec $POSTGRES_CONTAINER psql -U postgres -d postgres -c 'SELECT COUNT(*) FROM integration_test' -t"

    run_test "PostgreSQL" "EXPLAIN query" \
        "docker exec $POSTGRES_CONTAINER psql -U postgres -d postgres -c 'EXPLAIN SELECT * FROM pg_database' -t"

    run_test "PostgreSQL" "Database size" \
        "docker exec $POSTGRES_CONTAINER psql -U postgres -d postgres -c 'SELECT pg_size_pretty(pg_database_size(current_database()))' -t"
else
    log_test "PostgreSQL" "All tests" "SKIP" "0" "Container not running"
fi

#=============================================================================
# MYSQL TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  MySQL Tests${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

if [ -n "$MYSQL_CONTAINER" ]; then
    run_test "MySQL" "Connection test" \
        "docker exec $MYSQL_CONTAINER mysql -u root -proot -e 'SELECT 1'"

    run_test "MySQL" "Version query" \
        "docker exec $MYSQL_CONTAINER mysql -u root -proot -e 'SELECT VERSION()'"

    run_test "MySQL" "List databases" \
        "docker exec $MYSQL_CONTAINER mysql -u root -proot -e 'SHOW DATABASES'"

    run_test "MySQL" "Status check" \
        "docker exec $MYSQL_CONTAINER mysql -u root -proot -e 'SHOW STATUS LIKE \"Uptime\"'"

    run_test "MySQL" "Create test table" \
        "docker exec $MYSQL_CONTAINER mysql -u root -proot mysql -e 'CREATE TABLE IF NOT EXISTS integration_test (id INT AUTO_INCREMENT PRIMARY KEY, data VARCHAR(255), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'"

    run_test "MySQL" "Insert test data" \
        "docker exec $MYSQL_CONTAINER mysql -u root -proot mysql -e \"INSERT INTO integration_test (data) VALUES ('docker_test')\""

    run_test "MySQL" "Query test data" \
        "docker exec $MYSQL_CONTAINER mysql -u root -proot mysql -e 'SELECT COUNT(*) FROM integration_test'"

    run_test "MySQL" "EXPLAIN query" \
        "docker exec $MYSQL_CONTAINER mysql -u root -proot mysql -e 'EXPLAIN SELECT * FROM user LIMIT 1'"

    run_test "MySQL" "Variables check" \
        "docker exec $MYSQL_CONTAINER mysql -u root -proot -e 'SHOW VARIABLES LIKE \"max_connections\"'"
else
    log_test "MySQL" "All tests" "SKIP" "0" "Container not running"
fi

#=============================================================================
# MONGODB TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  MongoDB Tests${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

if [ -n "$MONGODB_CONTAINER" ]; then
    run_test "MongoDB" "Connection test" \
        "docker exec $MONGODB_CONTAINER mongosh --eval 'db.runCommand({ping: 1})' --quiet"

    run_test "MongoDB" "Version query" \
        "docker exec $MONGODB_CONTAINER mongosh --eval 'db.version()' --quiet"

    run_test "MongoDB" "List databases" \
        "docker exec $MONGODB_CONTAINER mongosh --eval 'db.adminCommand({listDatabases: 1})' --quiet"

    run_test "MongoDB" "Server status" \
        "docker exec $MONGODB_CONTAINER mongosh --eval 'db.serverStatus().host' --quiet"

    run_test "MongoDB" "Insert test document" \
        "docker exec $MONGODB_CONTAINER mongosh test --eval 'db.integration_test.insertOne({test: \"docker\", timestamp: new Date()})' --quiet"

    run_test "MongoDB" "Query test collection" \
        "docker exec $MONGODB_CONTAINER mongosh test --eval 'db.integration_test.find().limit(1)' --quiet"

    run_test "MongoDB" "Count documents" \
        "docker exec $MONGODB_CONTAINER mongosh test --eval 'db.integration_test.countDocuments()' --quiet"

    run_test "MongoDB" "Create index" \
        "docker exec $MONGODB_CONTAINER mongosh test --eval 'db.integration_test.createIndex({timestamp: 1})' --quiet"

    run_test "MongoDB" "List collections" \
        "docker exec $MONGODB_CONTAINER mongosh test --eval 'db.getCollectionNames()' --quiet"
else
    log_test "MongoDB" "All tests" "SKIP" "0" "Container not running"
fi

#=============================================================================
# REDIS TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Redis Tests${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

if [ -n "$REDIS_CONTAINER" ]; then
    run_test "Redis" "PING test" \
        "docker exec $REDIS_CONTAINER redis-cli PING"

    run_test "Redis" "INFO server" \
        "docker exec $REDIS_CONTAINER redis-cli INFO server | head -10"

    run_test "Redis" "SET key" \
        "docker exec $REDIS_CONTAINER redis-cli SET docker_test_key 'integration_test_value'"

    run_test "Redis" "GET key" \
        "docker exec $REDIS_CONTAINER redis-cli GET docker_test_key"

    run_test "Redis" "INCR counter" \
        "docker exec $REDIS_CONTAINER redis-cli INCR test_counter"

    run_test "Redis" "HSET hash" \
        "docker exec $REDIS_CONTAINER redis-cli HSET test_hash field1 value1"

    run_test "Redis" "HGET hash" \
        "docker exec $REDIS_CONTAINER redis-cli HGET test_hash field1"

    run_test "Redis" "DBSIZE" \
        "docker exec $REDIS_CONTAINER redis-cli DBSIZE"

    run_test "Redis" "Memory stats" \
        "docker exec $REDIS_CONTAINER redis-cli INFO memory | grep used_memory_human"
else
    log_test "Redis" "All tests" "SKIP" "0" "Container not running"
fi

#=============================================================================
# ORACLE TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Oracle Tests${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

if [ -n "$ORACLE_CONTAINER" ]; then
    run_test "Oracle" "Connection test" \
        "docker exec $ORACLE_CONTAINER sqlplus -S system/oracle@FREE <<< 'SELECT 1 FROM DUAL;'"

    run_test "Oracle" "Version query" \
        "docker exec $ORACLE_CONTAINER sqlplus -S system/oracle@FREE <<< 'SELECT BANNER FROM V\$VERSION;'"

    run_test "Oracle" "List tables" \
        "docker exec $ORACLE_CONTAINER sqlplus -S system/oracle@FREE <<< 'SELECT COUNT(*) FROM USER_TABLES;'"
else
    log_test "Oracle" "All tests" "SKIP" "0" "Container not healthy"
fi

#=============================================================================
# CROSS-DATABASE TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Cross-Database Tests${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Count running databases
RUNNING_DBS=0
[ -n "$POSTGRES_CONTAINER" ] && RUNNING_DBS=$((RUNNING_DBS + 1))
[ -n "$MYSQL_CONTAINER" ] && RUNNING_DBS=$((RUNNING_DBS + 1))
[ -n "$MONGODB_CONTAINER" ] && RUNNING_DBS=$((RUNNING_DBS + 1))
[ -n "$REDIS_CONTAINER" ] && RUNNING_DBS=$((RUNNING_DBS + 1))
[ -n "$ORACLE_CONTAINER" ] && RUNNING_DBS=$((RUNNING_DBS + 1))

if [ $RUNNING_DBS -gt 1 ]; then
    log_test "Cross-DB" "Multiple databases active" "PASS" "0" "$RUNNING_DBS databases running"

    # Test concurrent operations
    if [ -n "$POSTGRES_CONTAINER" ] && [ -n "$MYSQL_CONTAINER" ]; then
        run_test "Cross-DB" "Concurrent queries" \
            "(docker exec $POSTGRES_CONTAINER psql -U postgres -c 'SELECT 1' -t &); (docker exec $MYSQL_CONTAINER mysql -u root -proot -e 'SELECT 1' &); wait"
    fi
else
    log_test "Cross-DB" "Multiple databases active" "FAIL" "0" "Only $RUNNING_DBS database running"
fi

#=============================================================================
# PERFORMANCE TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Performance Tests${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

if [ -n "$POSTGRES_CONTAINER" ]; then
    run_test "Performance" "PostgreSQL bulk insert" \
        "docker exec $POSTGRES_CONTAINER psql -U postgres -d postgres -c \"INSERT INTO integration_test (data) SELECT 'bulk_' || generate_series(1, 100)\" -t"

    run_test "Performance" "PostgreSQL large query" \
        "docker exec $POSTGRES_CONTAINER psql -U postgres -d postgres -c 'SELECT * FROM pg_class LIMIT 100' -t >/dev/null"
fi

if [ -n "$REDIS_CONTAINER" ]; then
    run_test "Performance" "Redis bulk operations" \
        "for i in {1..100}; do docker exec $REDIS_CONTAINER redis-cli SET perf_\$i value_\$i >/dev/null; done"
fi

#=============================================================================
# SUMMARY
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

SUCCESS_RATE=0
if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$(awk "BEGIN {printf \"%.2f\", ($PASSED_TESTS / $TOTAL_TESTS) * 100}")
fi

echo -e "\nTotal Tests:    $TOTAL_TESTS"
echo -e "${GREEN}Passed:${NC}         $PASSED_TESTS"
echo -e "${RED}Failed:${NC}         $FAILED_TESTS"
echo -e "${YELLOW}Skipped:${NC}        $SKIPPED_TESTS"
echo -e "${BLUE}Success Rate:${NC}   ${SUCCESS_RATE}%"

if [ ${#FAILED_COMMANDS[@]} -gt 0 ]; then
    echo -e "\n${RED}Failed Tests:${NC}"
    for failed in "${FAILED_COMMANDS[@]}"; do
        echo -e "  ${RED}•${NC} $failed"
    done
fi

if [ ${#PERFORMANCE_METRICS[@]} -gt 0 ]; then
    echo -e "\n${BLUE}Performance Metrics (Top 10 slowest):${NC}"
    printf '%s\n' "${PERFORMANCE_METRICS[@]}" | sort -t'|' -k3 -n -r | head -10 | while IFS='|' read -r category desc duration; do
        echo -e "  ${duration}ms - [$category] $desc"
    done
fi

# Export to JSON
echo "{" > "$RESULTS_JSON"
echo "  \"summary\": {" >> "$RESULTS_JSON"
echo "    \"total\": $TOTAL_TESTS," >> "$RESULTS_JSON"
echo "    \"passed\": $PASSED_TESTS," >> "$RESULTS_JSON"
echo "    \"failed\": $FAILED_TESTS," >> "$RESULTS_JSON"
echo "    \"skipped\": $SKIPPED_TESTS," >> "$RESULTS_JSON"
echo "    \"successRate\": $SUCCESS_RATE," >> "$RESULTS_JSON"
echo "    \"runningDatabases\": $RUNNING_DBS," >> "$RESULTS_JSON"
echo "    \"timestamp\": \"$(date -Iseconds)\"" >> "$RESULTS_JSON"
echo "  }," >> "$RESULTS_JSON"
echo "  \"results\": [" >> "$RESULTS_JSON"

first=true
for result in "${TEST_RESULTS[@]}"; do
    IFS='|' read -r status category command duration message <<< "$result"
    [ "$first" = true ] && first=false || echo "," >> "$RESULTS_JSON"
    message_escaped=$(echo "$message" | sed 's/"/\\"/g')
    echo "    {" >> "$RESULTS_JSON"
    echo "      \"status\": \"$status\"," >> "$RESULTS_JSON"
    echo "      \"category\": \"$category\"," >> "$RESULTS_JSON"
    echo "      \"command\": \"$command\"," >> "$RESULTS_JSON"
    echo "      \"duration\": $duration," >> "$RESULTS_JSON"
    echo "      \"message\": \"$message_escaped\"" >> "$RESULTS_JSON"
    echo -n "    }" >> "$RESULTS_JSON"
done

echo "" >> "$RESULTS_JSON"
echo "  ]" >> "$RESULTS_JSON"
echo "}" >> "$RESULTS_JSON"

echo -e "\nEnd time: $(date)"
echo -e "Full log: $LOG_FILE"
echo -e "JSON results: $RESULTS_JSON"

# Exit based on success rate
if [ $FAILED_TESTS -eq 0 ] && [ $PASSED_TESTS -gt 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}"
    exit 0
elif [ "$SUCCESS_RATE" \< "80.00" ]; then
    echo -e "\n${RED}✗ Success rate below 80%${NC}"
    exit 1
else
    echo -e "\n${YELLOW}⚠ Some tests failed but success rate is acceptable${NC}"
    exit 0
fi
