#!/bin/bash

# AI-Shell CLI Integration Test Suite
# Tests all CLI commands against live Docker containers

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
LOG_FILE="/home/claude/AIShell/aishell/tests/integration/test-results-$(date +%Y%m%d-%H%M%S).log"
mkdir -p "$(dirname "$LOG_FILE")"

# Database connection strings
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/postgres"
export MYSQL_URL="mysql://root:root@localhost:3306/mysql"
export MONGODB_URL="mongodb://localhost:27017/test"
export REDIS_URL="redis://localhost:6379"
export ORACLE_URL="oracle://system:oracle@localhost:1521/FREE"

# CLI path
CLI_PATH="/home/claude/AIShell/aishell/bin/run.js"
NODE_CMD="node"

# Test result tracking
log_test() {
    local category=$1
    local command=$2
    local status=$3
    local duration=$4
    local message=$5

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ "$status" == "PASS" ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo -e "${GREEN}✓${NC} [$category] $command - ${duration}ms" | tee -a "$LOG_FILE"
        TEST_RESULTS+=("PASS|$category|$command|$duration|$message")
    elif [ "$status" == "SKIP" ]; then
        SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
        echo -e "${YELLOW}○${NC} [$category] $command - SKIPPED: $message" | tee -a "$LOG_FILE"
        TEST_RESULTS+=("SKIP|$category|$command|0|$message")
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo -e "${RED}✗${NC} [$category] $command - FAILED: $message" | tee -a "$LOG_FILE"
        TEST_RESULTS+=("FAIL|$category|$command|0|$message")
        FAILED_COMMANDS+=("$category: $command - $message")
    fi
}

# Run test with timeout and error handling
run_test() {
    local category=$1
    local description=$2
    shift 2
    local cmd="$@"

    echo -e "\n${BLUE}Testing:${NC} $description" | tee -a "$LOG_FILE"
    echo "Command: $cmd" >> "$LOG_FILE"

    local start_time=$(date +%s%3N)
    local output
    local exit_code

    # Run command with timeout
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
        PERFORMANCE_METRICS+=("$category|$description|$duration")
        return 0
    elif [ $exit_code -eq 124 ]; then
        log_test "$category" "$description" "FAIL" "0" "Timeout (30s)"
        return 1
    else
        log_test "$category" "$description" "FAIL" "0" "Exit code: $exit_code"
        return 1
    fi
}

# Skip test with reason
skip_test() {
    local category=$1
    local description=$2
    local reason=$3

    log_test "$category" "$description" "SKIP" "0" "$reason"
}

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  AI-Shell CLI Integration Test Suite${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "Start time: $(date)" | tee -a "$LOG_FILE"
echo -e "Log file: $LOG_FILE\n"

# Verify containers are running
echo -e "\n${BLUE}Verifying Docker containers...${NC}"
docker ps --filter "name=aishell_test" --filter "name=tst" --format "{{.Names}}: {{.Status}}" | tee -a "$LOG_FILE"

#=============================================================================
# POSTGRESQL TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  PostgreSQL CLI Commands${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Test PostgreSQL connection
run_test "PostgreSQL" "Connect to PostgreSQL" \
    "$NODE_CMD $CLI_PATH db connect postgres --host localhost --port 5432 --user postgres --password postgres --database postgres"

# Test PostgreSQL query
run_test "PostgreSQL" "Execute simple query" \
    "$NODE_CMD $CLI_PATH db query postgres \"SELECT version()\" --format json"

# Test PostgreSQL table listing
run_test "PostgreSQL" "List tables" \
    "$NODE_CMD $CLI_PATH db query postgres \"SELECT tablename FROM pg_tables WHERE schemaname='public' LIMIT 5\" --format json"

# Test PostgreSQL explain
run_test "PostgreSQL" "Explain query plan" \
    "$NODE_CMD $CLI_PATH db explain postgres \"SELECT * FROM pg_database\""

# Test PostgreSQL health check
run_test "PostgreSQL" "Health check" \
    "$NODE_CMD $CLI_PATH db health postgres"

# Test PostgreSQL metrics
run_test "PostgreSQL" "Database metrics" \
    "$NODE_CMD $CLI_PATH db metrics postgres --format json"

# Test PostgreSQL optimize
run_test "PostgreSQL" "Optimize suggestions" \
    "$NODE_CMD $CLI_PATH db optimize postgres \"SELECT * FROM pg_database WHERE datname = 'postgres'\""

# Test PostgreSQL backup list
run_test "PostgreSQL" "List backups" \
    "$NODE_CMD $CLI_PATH db backup list postgres"

#=============================================================================
# MYSQL TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  MySQL CLI Commands${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Test MySQL connection
run_test "MySQL" "Connect to MySQL" \
    "$NODE_CMD $CLI_PATH db connect mysql --host localhost --port 3306 --user root --password root --database mysql"

# Test MySQL query
run_test "MySQL" "Execute simple query" \
    "$NODE_CMD $CLI_PATH db query mysql \"SELECT VERSION()\" --format json"

# Test MySQL table listing
run_test "MySQL" "List tables" \
    "$NODE_CMD $CLI_PATH db query mysql \"SHOW TABLES\" --format json"

# Test MySQL explain
run_test "MySQL" "Explain query plan" \
    "$NODE_CMD $CLI_PATH db explain mysql \"SELECT * FROM user LIMIT 1\""

# Test MySQL health check
run_test "MySQL" "Health check" \
    "$NODE_CMD $CLI_PATH db health mysql"

# Test MySQL metrics
run_test "MySQL" "Database metrics" \
    "$NODE_CMD $CLI_PATH db metrics mysql --format json"

#=============================================================================
# MONGODB TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  MongoDB CLI Commands${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Test MongoDB connection
run_test "MongoDB" "Connect to MongoDB" \
    "$NODE_CMD $CLI_PATH db connect mongodb --host localhost --port 27017 --database test"

# Test MongoDB query (create test collection first)
run_test "MongoDB" "Insert test document" \
    "$NODE_CMD $CLI_PATH db query mongodb \"db.test_collection.insertOne({name: 'test', timestamp: new Date()})\" --format json"

# Test MongoDB find
run_test "MongoDB" "Find documents" \
    "$NODE_CMD $CLI_PATH db query mongodb \"db.test_collection.find().limit(5)\" --format json"

# Test MongoDB collections
run_test "MongoDB" "List collections" \
    "$NODE_CMD $CLI_PATH db query mongodb \"db.getCollectionNames()\" --format json"

# Test MongoDB health check
run_test "MongoDB" "Health check" \
    "$NODE_CMD $CLI_PATH db health mongodb"

# Test MongoDB metrics
run_test "MongoDB" "Database metrics" \
    "$NODE_CMD $CLI_PATH db metrics mongodb --format json"

#=============================================================================
# REDIS TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Redis CLI Commands${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Test Redis connection
run_test "Redis" "Connect to Redis" \
    "$NODE_CMD $CLI_PATH db connect redis --host localhost --port 6379"

# Test Redis SET
run_test "Redis" "SET key-value" \
    "$NODE_CMD $CLI_PATH db query redis \"SET test_key 'integration_test_value'\""

# Test Redis GET
run_test "Redis" "GET key-value" \
    "$NODE_CMD $CLI_PATH db query redis \"GET test_key\""

# Test Redis INFO
run_test "Redis" "Get server info" \
    "$NODE_CMD $CLI_PATH db query redis \"INFO server\" --format json"

# Test Redis health check
run_test "Redis" "Health check" \
    "$NODE_CMD $CLI_PATH db health redis"

# Test Redis metrics
run_test "Redis" "Database metrics" \
    "$NODE_CMD $CLI_PATH db metrics redis --format json"

#=============================================================================
# CROSS-DATABASE TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Cross-Database & Monitoring${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Test list all connections
run_test "Cross-DB" "List all connections" \
    "$NODE_CMD $CLI_PATH db list"

# Test disconnect
run_test "Cross-DB" "Disconnect from database" \
    "$NODE_CMD $CLI_PATH db disconnect postgres"

# Test monitoring commands
run_test "Monitoring" "Database status overview" \
    "$NODE_CMD $CLI_PATH db status"

#=============================================================================
# ORACLE TESTS (if available)
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Oracle CLI Commands${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Check if Oracle container is healthy
if docker ps --filter "name=tstoracle" --filter "health=healthy" | grep -q tstoracle; then
    run_test "Oracle" "Connect to Oracle" \
        "$NODE_CMD $CLI_PATH db connect oracle --host localhost --port 1521 --user system --password oracle --database FREE"

    run_test "Oracle" "Execute simple query" \
        "$NODE_CMD $CLI_PATH db query oracle \"SELECT * FROM DUAL\" --format json"

    run_test "Oracle" "Health check" \
        "$NODE_CMD $CLI_PATH db health oracle"
else
    skip_test "Oracle" "Connect to Oracle" "Container not healthy"
    skip_test "Oracle" "Execute simple query" "Container not healthy"
    skip_test "Oracle" "Health check" "Container not healthy"
fi

#=============================================================================
# ADVANCED FEATURE TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Advanced Features${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Test query optimization
run_test "Advanced" "Query optimization analysis" \
    "$NODE_CMD $CLI_PATH db optimize postgres \"SELECT * FROM pg_database\""

# Test backup creation (if supported)
run_test "Advanced" "Create backup" \
    "$NODE_CMD $CLI_PATH db backup create postgres --output /tmp/test-backup-$(date +%s).sql" || true

# Test export functionality
run_test "Advanced" "Export query results" \
    "$NODE_CMD $CLI_PATH db query postgres \"SELECT datname, datdba FROM pg_database LIMIT 3\" --format csv --output /tmp/export-test.csv"

#=============================================================================
# PERFORMANCE TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Performance Tests${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Test concurrent queries
run_test "Performance" "Concurrent query execution" \
    "for i in {1..3}; do ($NODE_CMD $CLI_PATH db query postgres \"SELECT \$i\" --format json &); done; wait"

# Test large result set handling
run_test "Performance" "Large result set query" \
    "$NODE_CMD $CLI_PATH db query postgres \"SELECT * FROM pg_class LIMIT 100\" --format json"

#=============================================================================
# ERROR HANDLING TESTS
#=============================================================================
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Error Handling${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# Test invalid connection
if ! $NODE_CMD $CLI_PATH db connect postgres --host localhost --port 9999 --user invalid --password invalid --database invalid 2>&1 | grep -qi "error"; then
    log_test "Error Handling" "Invalid connection handling" "FAIL" "0" "Should fail gracefully"
else
    log_test "Error Handling" "Invalid connection handling" "PASS" "0" "Failed gracefully as expected"
fi

# Test invalid query
if ! $NODE_CMD $CLI_PATH db query postgres "INVALID SQL SYNTAX HERE" 2>&1 | grep -qi "error"; then
    log_test "Error Handling" "Invalid query handling" "FAIL" "0" "Should fail gracefully"
else
    log_test "Error Handling" "Invalid query handling" "PASS" "0" "Failed gracefully as expected"
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
    echo -e "\n${RED}Failed Commands:${NC}"
    for failed in "${FAILED_COMMANDS[@]}"; do
        echo -e "  ${RED}•${NC} $failed"
    done
fi

# Performance metrics summary
if [ ${#PERFORMANCE_METRICS[@]} -gt 0 ]; then
    echo -e "\n${BLUE}Performance Metrics (Top 10 slowest):${NC}"
    printf '%s\n' "${PERFORMANCE_METRICS[@]}" | sort -t'|' -k3 -n -r | head -10 | while IFS='|' read -r category desc duration; do
        echo -e "  ${duration}ms - [$category] $desc"
    done
fi

echo -e "\nEnd time: $(date)"
echo -e "Full log: $LOG_FILE"

# Export results to JSON for report generation
RESULTS_JSON="/home/claude/AIShell/aishell/tests/integration/test-results.json"
echo "{" > "$RESULTS_JSON"
echo "  \"summary\": {" >> "$RESULTS_JSON"
echo "    \"total\": $TOTAL_TESTS," >> "$RESULTS_JSON"
echo "    \"passed\": $PASSED_TESTS," >> "$RESULTS_JSON"
echo "    \"failed\": $FAILED_TESTS," >> "$RESULTS_JSON"
echo "    \"skipped\": $SKIPPED_TESTS," >> "$RESULTS_JSON"
echo "    \"successRate\": $SUCCESS_RATE," >> "$RESULTS_JSON"
echo "    \"timestamp\": \"$(date -Iseconds)\"" >> "$RESULTS_JSON"
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
