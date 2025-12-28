#!/bin/bash

# Check for Flaky Tests
# Runs failing tests multiple times to identify intermittent failures

LOG_DIR="/home/claude/AIShell/aishell/tests/logs"
mkdir -p "$LOG_DIR"

echo "=== Flaky Test Detection ==="
echo "Started at: $(date)"
echo ""

# Run tests 3 times to check for flakiness
RUNS=3
FLAKY_LOG="$LOG_DIR/flaky-tests.log"

echo "Running test suite $RUNS times to detect flakiness..." | tee "$FLAKY_LOG"
echo ""

for i in $(seq 1 $RUNS); do
    echo "--- Run $i/$RUNS ---" | tee -a "$FLAKY_LOG"
    npm test 2>&1 | tee "$LOG_DIR/flaky-run-$i.log"

    # Extract failed tests
    grep "FAIL" "$LOG_DIR/flaky-run-$i.log" | grep -oP 'tests/.*\.test\.ts' | sort > "$LOG_DIR/failed-run-$i.txt"

    echo "Run $i: $(wc -l < "$LOG_DIR/failed-run-$i.txt") failures" | tee -a "$FLAKY_LOG"
    echo ""
done

# Find tests that failed in some runs but not others (flaky)
echo "=== Analyzing Flakiness ===" | tee -a "$FLAKY_LOG"

# Create combined list of all failures
cat "$LOG_DIR"/failed-run-*.txt | sort | uniq > "$LOG_DIR/all-failures.txt"

# Check which tests don't fail consistently
while read -r test; do
    COUNT=$(grep -c "$test" "$LOG_DIR"/failed-run-*.txt)

    if [ "$COUNT" -gt 0 ] && [ "$COUNT" -lt "$RUNS" ]; then
        echo "FLAKY: $test (failed $COUNT/$RUNS runs)" | tee -a "$FLAKY_LOG"
    fi
done < "$LOG_DIR/all-failures.txt"

echo ""
echo "Flaky test detection completed at: $(date)"
echo "Results saved to: $FLAKY_LOG"
