#!/bin/bash

# Quick Test Summary Script
# Provides instant snapshot of test status

echo "=== Test Coverage Summary ==="
echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Run tests quickly with minimal output
npm test 2>&1 | tee /tmp/test-summary.log > /dev/null

# Extract key metrics
TOTAL=1600
PASSING=$(grep "Tests" /tmp/test-summary.log | grep -oP '\d+ passed' | grep -oP '\d+' || echo "0")
FAILING=$(grep "Tests" /tmp/test-summary.log | grep -oP '\d+ failed' | grep -oP '\d+' || echo "0")
SKIPPED=$(grep "Tests" /tmp/test-summary.log | grep -oP '\d+ skipped' | grep -oP '\d+' || echo "0")

PERCENTAGE=$(echo "scale=2; $PASSING * 100 / $TOTAL" | bc)
TARGET=1520
NEEDED=$((TARGET - PASSING))

# Display results
echo "Overall Progress:"
echo "  Tests Passing:  $PASSING / $TOTAL ($PERCENTAGE%)"
echo "  Tests Failing:  $FAILING"
echo "  Tests Skipped:  $SKIPPED"
echo ""
echo "Goal Progress:"
echo "  Current:  $PERCENTAGE%"
echo "  Target:   95.00%"
echo "  Gap:      $NEEDED tests needed"
echo ""

# Progress bar
FILLED=$((PASSING * 50 / TOTAL))
EMPTY=$((50 - FILLED))
printf "Progress: ["
printf "%${FILLED}s" | tr ' ' '='
printf ">"
printf "%${EMPTY}s" | tr ' ' ' '
printf "] $PERCENTAGE%%\n"
echo ""

# Test files status
FILES_PASSING=$(grep "Test Files" /tmp/test-summary.log | grep -oP '\d+ passed' | grep -oP '\d+' || echo "0")
FILES_FAILING=$(grep "Test Files" /tmp/test-summary.log | grep -oP '\d+ failed' | grep -oP '\d+' || echo "0")

echo "Test Files:"
echo "  Passing: $FILES_PASSING"
echo "  Failing: $FILES_FAILING"
echo ""

# Execution time
DURATION=$(grep "Duration" /tmp/test-summary.log | grep -oP '[\d.]+s' | head -1)
echo "Execution Time: $DURATION (Baseline: 75.71s)"
echo ""

# Agent-specific breakdowns
echo "=== Agent-Specific Status ==="
echo ""

# OptimizationCLI
echo "Backend Dev 1: OptimizationCLI"
if [ -f "tests/cli/optimization-cli.test.ts" ]; then
    OPT_STATUS=$(npm test -- tests/cli/optimization-cli.test.ts 2>&1 | grep "Tests" || echo "Not run")
    echo "  Status: $OPT_STATUS"
else
    echo "  Status: Not implemented yet"
fi
echo ""

# Database configs
echo "Backend Dev 2: Database Configuration"
if [ -f "tests/integration/postgres.test.ts" ]; then
    DB_STATUS=$(npm test -- tests/integration/postgres.test.ts 2>&1 | grep "Tests" || echo "Not run")
    echo "  Status: $DB_STATUS"
else
    echo "  Status: Tests exist, checking results..."
fi
echo ""

# Feature commands
echo "Backend Dev 3: Phase 2 CLI Commands"
if [ -f "tests/cli/feature-commands.test.ts" ]; then
    CLI_STATUS=$(npm test -- tests/cli/feature-commands.test.ts 2>&1 | grep "Tests" || echo "Not run")
    echo "  Status: $CLI_STATUS"
else
    echo "  Status: Tests exist, checking results..."
fi
echo ""

echo "=== Monitoring Status ==="
if pgrep -f "test-monitor.sh" > /dev/null; then
    echo "  Continuous monitoring: ACTIVE"
    echo "  Monitor PID: $(pgrep -f test-monitor.sh)"
    echo "  Log file: tests/logs/test-monitor.log"
else
    echo "  Continuous monitoring: INACTIVE"
fi
echo ""

# Recent activity
if [ -f "tests/logs/progress-tracking.csv" ]; then
    LAST_RUN=$(tail -1 tests/logs/progress-tracking.csv | cut -d',' -f1)
    echo "  Last monitoring run: $LAST_RUN"
fi
