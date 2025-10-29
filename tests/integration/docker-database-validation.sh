#!/bin/bash

# AI-Shell Docker Database Integration Validation
# Tests database connectivity and basic operations against Docker containers

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Test results storage
declare -a TEST_RESULTS
declare -a FAILED_COMMANDS
declare -a PERFORMANCE_METRICS

# Logging
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="/home/claude/AIShell/aishell/tests/integration/validation-${TIMESTAMP}.log"
RESULTS_JSON="/home/claude/AIShell/aishell/tests/integration/validation-results.json"

mkdir -p "$(dirname "$LOG_FILE")"

# Test result tracking
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

# Run test with timeout
run_test() {
    local category=$1
    local description=$2
    local cmd=$3

    echo -e "\n${BLUE}Testing:${NC} $description" | tee -a "$LOG_FILE"
    echo "Command: $cmd" >> "$LOG_FILE"

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

    echo "Output: $output" >> "$LOG_FILE"
    echo "Exit code: $exit_code" >> "$LOG_FILE"

    if [ $exit_code -eq 0 ]; then
        log_test "$category" "$description" "PASS" "$duration" "Success"
        return 0
    elif [ $exit_code -eq 124 ]; then
        log_test "$category" "$description" "FAIL" "0" "Timeout (30s)"
        return 1
    else
        log_test "$category" "$description" "FAIL" "0" "Exit code: $exit_code - $output"
        return 1
    fi
}

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  AI-Shell Docker Database Integration Validation${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "Start time: $(date)" | tee -a "$LOG_FILE"
echo -e "Log file: $LOG_FILE\n"

#=============================================================================
# VERIFY DOCKER CONTAINERS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Docker Container Status${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

POSTGRES_RUNNING=$(docker ps --filter "name=tstpostgres" --format "{{.Names}}" | wc -l)
MYSQL_RUNNING=$(docker ps --filter "name=aishell_test_mysql" --format "{{.Names}}" | wc -l)
MONGODB_RUNNING=$(docker ps --filter "name=aishell_test_mongodb" --format "{{.Names}}" | wc -l)
REDIS_RUNNING=$(docker ps --filter "name=aishell_test_redis" --format "{{.Names}}" | wc -l)
ORACLE_RUNNING=$(docker ps --filter "name=tstoracle" --filter "health=healthy" --format "{{.Names}}" | wc -l)

echo -e "PostgreSQL: $([ $POSTGRES_RUNNING -gt 0 ] && echo "${GREEN}Running${NC}" || echo "${RED}Not Running${NC}")" | tee -a "$LOG_FILE"
echo -e "MySQL:      $([ $MYSQL_RUNNING -gt 0 ] && echo "${GREEN}Running${NC}" || echo "${RED}Not Running${NC}")" | tee -a "$LOG_FILE"
echo -e "MongoDB:    $([ $MONGODB_RUNNING -gt 0 ] && echo "${GREEN}Running${NC}" || echo "${RED}Not Running${NC}")" | tee -a "$LOG_FILE"
echo -e "Redis:      $([ $REDIS_RUNNING -gt 0 ] && echo "${GREEN}Running${NC}" || echo "${RED}Not Running${NC}")" | tee -a "$LOG_FILE"
echo -e "Oracle:     $([ $ORACLE_RUNNING -gt 0 ] && echo "${GREEN}Running & Healthy${NC}" || echo "${YELLOW}Not Healthy${NC}")" | tee -a "$LOG_FILE"

#=============================================================================
# POSTGRESQL CONNECTIVITY TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  PostgreSQL Connectivity Tests${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

if [ $POSTGRES_RUNNING -gt 0 ]; then
    run_test "PostgreSQL" "Connection test" \
        "PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d postgres -c 'SELECT 1' -t"

    run_test "PostgreSQL" "Version query" \
        "PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d postgres -c 'SELECT version()' -t"

    run_test "PostgreSQL" "List databases" \
        "PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d postgres -c '\l' -t | head -5"

    run_test "PostgreSQL" "Table count" \
        "PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d postgres -c \"SELECT COUNT(*) FROM pg_tables WHERE schemaname='public'\" -t"

    run_test "PostgreSQL" "Active connections" \
        "PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d postgres -c 'SELECT COUNT(*) FROM pg_stat_activity' -t"

    run_test "PostgreSQL" "Database size" \
        "PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d postgres -c 'SELECT pg_size_pretty(pg_database_size(current_database()))' -t"
else
    log_test "PostgreSQL" "All tests" "SKIP" "0" "Container not running"
fi

#=============================================================================
# MYSQL CONNECTIVITY TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  MySQL Connectivity Tests${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

if [ $MYSQL_RUNNING -gt 0 ]; then
    run_test "MySQL" "Connection test" \
        "mysql -h 127.0.0.1 -P 3306 -u root -proot -e 'SELECT 1' 2>/dev/null"

    run_test "MySQL" "Version query" \
        "mysql -h 127.0.0.1 -P 3306 -u root -proot -e 'SELECT VERSION()' 2>/dev/null"

    run_test "MySQL" "List databases" \
        "mysql -h 127.0.0.1 -P 3306 -u root -proot -e 'SHOW DATABASES' 2>/dev/null"

    run_test "MySQL" "Status check" \
        "mysql -h 127.0.0.1 -P 3306 -u root -proot -e 'SHOW STATUS LIKE \"Uptime\"' 2>/dev/null"

    run_test "MySQL" "Process list" \
        "mysql -h 127.0.0.1 -P 3306 -u root -proot -e 'SHOW PROCESSLIST' 2>/dev/null"

    run_test "MySQL" "Variables check" \
        "mysql -h 127.0.0.1 -P 3306 -u root -proot -e 'SHOW VARIABLES LIKE \"max_connections\"' 2>/dev/null"
else
    log_test "MySQL" "All tests" "SKIP" "0" "Container not running"
fi

#=============================================================================
# MONGODB CONNECTIVITY TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  MongoDB Connectivity Tests${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

if [ $MONGODB_RUNNING -gt 0 ]; then
    run_test "MongoDB" "Connection test" \
        "mongosh --host localhost --port 27017 --eval 'db.runCommand({ping: 1})' --quiet"

    run_test "MongoDB" "Version query" \
        "mongosh --host localhost --port 27017 --eval 'db.version()' --quiet"

    run_test "MongoDB" "List databases" \
        "mongosh --host localhost --port 27017 --eval 'db.adminCommand({listDatabases: 1})' --quiet"

    run_test "MongoDB" "Server status" \
        "mongosh --host localhost --port 27017 --eval 'db.serverStatus().host' --quiet"

    run_test "MongoDB" "Create test collection" \
        "mongosh --host localhost --port 27017 test --eval 'db.integration_test.insertOne({test: \"docker-validation\", timestamp: new Date()})' --quiet"

    run_test "MongoDB" "Query test collection" \
        "mongosh --host localhost --port 27017 test --eval 'db.integration_test.find().limit(1)' --quiet"
else
    log_test "MongoDB" "All tests" "SKIP" "0" "Container not running"
fi

#=============================================================================
# REDIS CONNECTIVITY TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Redis Connectivity Tests${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

if [ $REDIS_RUNNING -gt 0 ]; then
    run_test "Redis" "PING test" \
        "redis-cli -h localhost -p 6379 PING"

    run_test "Redis" "INFO server" \
        "redis-cli -h localhost -p 6379 INFO server | head -10"

    run_test "Redis" "SET key" \
        "redis-cli -h localhost -p 6379 SET docker_test_key 'integration_test_value'"

    run_test "Redis" "GET key" \
        "redis-cli -h localhost -p 6379 GET docker_test_key"

    run_test "Redis" "DBSIZE" \
        "redis-cli -h localhost -p 6379 DBSIZE"

    run_test "Redis" "Memory stats" \
        "redis-cli -h localhost -p 6379 INFO memory | grep used_memory_human"
else
    log_test "Redis" "All tests" "SKIP" "0" "Container not running"
fi

#=============================================================================
# ORACLE CONNECTIVITY TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Oracle Connectivity Tests${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

if [ $ORACLE_RUNNING -gt 0 ]; then
    # Oracle tests would require sqlplus - checking if available
    if command -v sqlplus &> /dev/null; then
        run_test "Oracle" "Connection test" \
            "echo 'SELECT 1 FROM DUAL;' | sqlplus -S system/oracle@localhost:1521/FREE"

        run_test "Oracle" "Version query" \
            "echo 'SELECT * FROM V\$VERSION;' | sqlplus -S system/oracle@localhost:1521/FREE"
    else
        log_test "Oracle" "All tests" "SKIP" "0" "sqlplus not available"
    fi
else
    log_test "Oracle" "All tests" "SKIP" "0" "Container not healthy"
fi

#=============================================================================
# CROSS-DATABASE TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Cross-Database Comparison${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Count running databases
RUNNING_DBS=$((POSTGRES_RUNNING + MYSQL_RUNNING + MONGODB_RUNNING + REDIS_RUNNING + ORACLE_RUNNING))

if [ $RUNNING_DBS -gt 0 ]; then
    log_test "Cross-DB" "Multiple databases running" "PASS" "0" "$RUNNING_DBS databases active"
else
    log_test "Cross-DB" "Multiple databases running" "FAIL" "0" "No databases running"
fi

# Test concurrent connections
if [ $POSTGRES_RUNNING -gt 0 ] && [ $MYSQL_RUNNING -gt 0 ]; then
    run_test "Cross-DB" "Concurrent queries (PostgreSQL + MySQL)" \
        "(PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d postgres -c 'SELECT 1' -t &); (mysql -h 127.0.0.1 -P 3306 -u root -proot -e 'SELECT 1' 2>/dev/null &); wait"
fi

#=============================================================================
# PERFORMANCE TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Performance Tests${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

if [ $POSTGRES_RUNNING -gt 0 ]; then
    run_test "Performance" "PostgreSQL query latency" \
        "PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d postgres -c 'SELECT pg_sleep(0.01)' -t"
fi

if [ $REDIS_RUNNING -gt 0 ]; then
    run_test "Performance" "Redis SET/GET latency" \
        "for i in {1..10}; do redis-cli -h localhost -p 6379 SET perf_test_\$i value_\$i > /dev/null; done"
fi

#=============================================================================
# GENERATE SUMMARY
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

# Performance metrics
if [ ${#PERFORMANCE_METRICS[@]} -gt 0 ]; then
    echo -e "\n${BLUE}Performance Metrics (Top 10 slowest):${NC}"
    printf '%s\n' "${PERFORMANCE_METRICS[@]}" | sort -t'|' -k3 -n -r | head -10 | while IFS='|' read -r category desc duration; do
        echo -e "  ${duration}ms - [$category] $desc"
    done
fi

echo -e "\nEnd time: $(date)"
echo -e "Full log: $LOG_FILE"

# Export to JSON
echo "{" > "$RESULTS_JSON"
echo "  \"summary\": {" >> "$RESULTS_JSON"
echo "    \"total\": $TOTAL_TESTS," >> "$RESULTS_JSON"
echo "    \"passed\": $PASSED_TESTS," >> "$RESULTS_JSON"
echo "    \"failed\": $FAILED_TESTS," >> "$RESULTS_JSON"
echo "    \"skipped\": $SKIPPED_TESTS," >> "$RESULTS_JSON"
echo "    \"successRate\": $SUCCESS_RATE," >> "$RESULTS_JSON"
echo "    \"timestamp\": \"$(date -Iseconds)\"," >> "$RESULTS_JSON"
echo "    \"containerStatus\": {" >> "$RESULTS_JSON"
echo "      \"postgresql\": $([ $POSTGRES_RUNNING -gt 0 ] && echo true || echo false)," >> "$RESULTS_JSON"
echo "      \"mysql\": $([ $MYSQL_RUNNING -gt 0 ] && echo true || echo false)," >> "$RESULTS_JSON"
echo "      \"mongodb\": $([ $MONGODB_RUNNING -gt 0 ] && echo true || echo false)," >> "$RESULTS_JSON"
echo "      \"redis\": $([ $REDIS_RUNNING -gt 0 ] && echo true || echo false)," >> "$RESULTS_JSON"
echo "      \"oracle\": $([ $ORACLE_RUNNING -gt 0 ] && echo true || echo false) " >> "$RESULTS_JSON"
echo "    }" >> "$RESULTS_JSON"
echo "  }," >> "$RESULTS_JSON"
echo "  \"results\": [" >> "$RESULTS_JSON"

first=true
for result in "${TEST_RESULTS[@]}"; do
    IFS='|' read -r status category command duration message <<< "$result"
    [ "$first" = true ] && first=false || echo "," >> "$RESULTS_JSON"
    echo "    {" >> "$RESULTS_JSON"
    echo "      \"status\": \"$status\"," >> "$RESULTS_JSON"
    echo "      \"category\": \"$category\"," >> "$RESULTS_JSON"
    echo "      \"command\": \"$command\"," >> "$RESULTS_JSON"
    echo "      \"duration\": $duration," >> "$RESULTS_JSON"
    echo "      \"message\": \"$message\"" >> "$RESULTS_JSON"
    echo -n "    }" >> "$RESULTS_JSON"
done

echo "" >> "$RESULTS_JSON"
echo "  ]" >> "$RESULTS_JSON"
echo "}" >> "$RESULTS_JSON"

echo -e "\n${GREEN}Results exported to: $RESULTS_JSON${NC}"

# Exit with appropriate code
if [ $FAILED_TESTS -eq 0 ]; then
    exit 0
else
    exit 1
fi
