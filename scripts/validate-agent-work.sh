#!/bin/bash

# Validate Agent Work Script
# Tests specific areas modified by each agent

LOG_DIR="/home/claude/AIShell/aishell/tests/logs"
mkdir -p "$LOG_DIR"

echo "=== Agent Work Validation ==="
echo "Started at: $(date)"
echo ""

# Function to run specific test suite
run_suite() {
    local suite_name=$1
    local test_pattern=$2
    local expected_count=$3

    echo "--- Testing: $suite_name ---"
    npm test -- "$test_pattern" 2>&1 | tee "$LOG_DIR/agent-$suite_name.log"

    # Extract results
    PASSING=$(grep "Tests" "$LOG_DIR/agent-$suite_name.log" | grep -oP '\d+ passed' | grep -oP '\d+' || echo "0")
    FAILING=$(grep "Tests" "$LOG_DIR/agent-$suite_name.log" | grep -oP '\d+ failed' | grep -oP '\d+' || echo "0")

    echo "Results: $PASSING passed, $FAILING failed (Expected: +$expected_count)"
    echo ""

    return $FAILING
}

# Backend Dev 1: OptimizationCLI
echo "=== Backend Dev 1: OptimizationCLI ===" | tee -a "$LOG_DIR/agent-validation.log"
run_suite "optimization-cli" "tests/cli/optimization-cli.test.ts" 80
OPTIMIZATION_FAILED=$?

# Backend Dev 2: Database Configuration
echo "=== Backend Dev 2: Database Configuration ===" | tee -a "$LOG_DIR/agent-validation.log"
run_suite "postgres-integration" "tests/integration/postgres.test.ts" 150
DB_FAILED=$?

# Backend Dev 3: Phase 2 CLI
echo "=== Backend Dev 3: Phase 2 CLI ===" | tee -a "$LOG_DIR/agent-validation.log"
run_suite "feature-commands" "tests/cli/feature-commands.test.ts" 20
CLI_FAILED=$?

# Performance Analyzer: Run all tests and measure time
echo "=== Performance Analyzer: Execution Time ===" | tee -a "$LOG_DIR/agent-validation.log"
echo "Running full test suite to measure performance..."
time npm test 2>&1 | tee "$LOG_DIR/agent-performance.log"

# Extract execution time
EXEC_TIME=$(grep "Duration" "$LOG_DIR/agent-performance.log" | grep -oP '[\d.]+s' | head -1)
echo "Execution time: $EXEC_TIME (Baseline: 75.71s)" | tee -a "$LOG_DIR/agent-validation.log"
echo ""

# Summary
echo "=== Validation Summary ===" | tee -a "$LOG_DIR/agent-validation.log"
echo "OptimizationCLI: $OPTIMIZATION_FAILED failures"
echo "Database Config: $DB_FAILED failures"
echo "Phase 2 CLI: $CLI_FAILED failures"
echo "Performance: $EXEC_TIME"
echo ""

# Check for regressions
echo "=== Regression Check ===" | tee -a "$LOG_DIR/agent-validation.log"
TOTAL_PASSING=$(grep "Tests" "$LOG_DIR/agent-performance.log" | grep -oP '\d+ passed' | grep -oP '\d+' || echo "0")
BASELINE_PASSING=980

if [ "$TOTAL_PASSING" -lt "$BASELINE_PASSING" ]; then
    echo "REGRESSION DETECTED: $TOTAL_PASSING < $BASELINE_PASSING" | tee -a "$LOG_DIR/agent-validation.log"
    exit 1
else
    IMPROVEMENT=$((TOTAL_PASSING - BASELINE_PASSING))
    echo "Progress: +$IMPROVEMENT tests (Total: $TOTAL_PASSING/1600)" | tee -a "$LOG_DIR/agent-validation.log"
fi

echo ""
echo "Validation completed at: $(date)"
