#!/bin/bash

# MCP Integration Test Verification Script
# Verifies test suite meets all requirements

set -e

echo "========================================="
echo "MCP Integration Test Verification"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Counters
total_checks=0
passed_checks=0

# Function to check test count in file
check_test_count() {
    local file=$1
    local min_tests=$2
    local name=$3

    total_checks=$((total_checks + 1))

    if [ ! -f "$file" ]; then
        echo -e "${RED}✗ $name: File not found${NC}"
        return 1
    fi

    local count=$(grep -c "def test_" "$file")

    if [ $count -ge $min_tests ]; then
        echo -e "${GREEN}✓ $name: $count tests (target: ${min_tests}+)${NC}"
        passed_checks=$((passed_checks + 1))
        return 0
    else
        echo -e "${RED}✗ $name: Only $count tests (target: ${min_tests}+)${NC}"
        return 1
    fi
}

# Function to check file exists
check_file_exists() {
    local file=$1
    local name=$2

    total_checks=$((total_checks + 1))

    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $name exists${NC}"
        passed_checks=$((passed_checks + 1))
        return 0
    else
        echo -e "${RED}✗ $name not found${NC}"
        return 1
    fi
}

# Function to check executable
check_executable() {
    local file=$1
    local name=$2

    total_checks=$((total_checks + 1))

    if [ -x "$file" ]; then
        echo -e "${GREEN}✓ $name is executable${NC}"
        passed_checks=$((passed_checks + 1))
        return 0
    else
        echo -e "${RED}✗ $name is not executable${NC}"
        return 1
    fi
}

echo -e "${BLUE}=== Checking Test Files ===${NC}"

check_test_count "test_postgresql_integration.py" 40 "PostgreSQL tests"
check_test_count "test_mysql_integration.py" 35 "MySQL tests"
check_test_count "test_mongodb_integration.py" 35 "MongoDB tests"
check_test_count "test_redis_integration.py" 40 "Redis tests"
check_test_count "test_sqlite_integration.py" 25 "SQLite tests"
check_test_count "test_manager_integration.py" 30 "Connection Manager tests"
check_test_count "test_docker_integration.py" 20 "Docker integration tests"
check_test_count "test_mcp_performance.py" 25 "Performance tests"

echo ""
echo -e "${BLUE}=== Checking Infrastructure Files ===${NC}"

check_file_exists "config.py" "Configuration file"
check_file_exists "conftest.py" "Pytest fixtures"
check_file_exists "__init__.py" "Package init"

echo ""
echo -e "${BLUE}=== Checking Scripts ===${NC}"

check_file_exists "run_tests.sh" "Test runner script"
check_executable "run_tests.sh" "Test runner"
check_file_exists "cleanup.sh" "Cleanup script"
check_executable "cleanup.sh" "Cleanup script"

echo ""
echo -e "${BLUE}=== Checking Documentation ===${NC}"

check_file_exists "README.md" "Test documentation"
check_file_exists "../../docs/mcp-integration-tests-summary.md" "Summary document"

echo ""
echo -e "${BLUE}=== Checking CI/CD ===${NC}"

check_file_exists "../../../.github/workflows/mcp-integration-tests.yml" "GitHub Actions workflow"

echo ""
echo -e "${BLUE}=== Test Count Summary ===${NC}"

total_tests=$(find . -name "test_*.py" -type f | xargs grep -c "def test_" | awk -F: '{sum+=$2} END {print sum}')

echo "Total tests found: $total_tests"

if [ $total_tests -ge 250 ]; then
    echo -e "${GREEN}✓ Test count meets requirement (250+)${NC}"
    passed_checks=$((passed_checks + 1))
else
    echo -e "${RED}✗ Test count below requirement (found: $total_tests, required: 250+)${NC}"
fi

total_checks=$((total_checks + 1))

echo ""
echo -e "${BLUE}=== Verification Summary ===${NC}"

echo "Checks passed: $passed_checks / $total_checks"

if [ $passed_checks -eq $total_checks ]; then
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}All verification checks passed!${NC}"
    echo -e "${GREEN}=========================================${NC}"
    exit 0
else
    echo -e "${RED}=========================================${NC}"
    echo -e "${RED}Some verification checks failed${NC}"
    echo -e "${RED}=========================================${NC}"
    exit 1
fi
