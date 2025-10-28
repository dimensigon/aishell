#!/bin/bash

# Continuous Test Monitoring Script
# Runs tests every 15 minutes and tracks progress

LOG_DIR="/home/claude/AIShell/aishell/tests/logs"
REPORT_FILE="/home/claude/AIShell/aishell/docs/reports/coverage-tracking-live.md"
MONITOR_LOG="$LOG_DIR/test-monitor.log"

# Ensure directories exist
mkdir -p "$LOG_DIR"

echo "=== Starting Continuous Test Monitor ===" | tee -a "$MONITOR_LOG"
echo "Started at: $(date)" | tee -a "$MONITOR_LOG"
echo "Interval: 15 minutes" | tee -a "$MONITOR_LOG"
echo "" | tee -a "$MONITOR_LOG"

# Function to run tests and extract stats
run_tests() {
    echo "=== Test Run at $(date) ===" | tee -a "$MONITOR_LOG"

    # Run tests and capture output
    npm test 2>&1 | tee "$LOG_DIR/latest-run.log"

    # Extract statistics
    PASSING=$(grep "Tests" "$LOG_DIR/latest-run.log" | grep -oP '\d+ passed' | grep -oP '\d+' || echo "0")
    FAILING=$(grep "Tests" "$LOG_DIR/latest-run.log" | grep -oP '\d+ failed' | grep -oP '\d+' || echo "0")
    SKIPPED=$(grep "Tests" "$LOG_DIR/latest-run.log" | grep -oP '\d+ skipped' | grep -oP '\d+' || echo "0")
    TOTAL=1600

    # Calculate percentage
    PERCENTAGE=$(echo "scale=2; $PASSING * 100 / $TOTAL" | bc)

    # Log results
    echo "Results: $PASSING passed, $FAILING failed, $SKIPPED skipped ($PERCENTAGE%)" | tee -a "$MONITOR_LOG"
    echo "" | tee -a "$MONITOR_LOG"

    # Update tracking file
    echo "$(date '+%Y-%m-%d %H:%M:%S'),$PASSING,$FAILING,$SKIPPED,$PERCENTAGE" >> "$LOG_DIR/progress-tracking.csv"
}

# Initialize CSV if it doesn't exist
if [ ! -f "$LOG_DIR/progress-tracking.csv" ]; then
    echo "timestamp,passing,failing,skipped,percentage" > "$LOG_DIR/progress-tracking.csv"
fi

# Run initial test
run_tests

# Monitor loop - run every 15 minutes
COUNTER=0
while true; do
    sleep 900  # 15 minutes

    COUNTER=$((COUNTER + 1))
    echo "--- Run #$COUNTER ---" | tee -a "$MONITOR_LOG"
    run_tests

    # Generate 30-minute report every 2 runs
    if [ $((COUNTER % 2)) -eq 0 ]; then
        echo "Generating 30-minute progress report..." | tee -a "$MONITOR_LOG"
        node /home/claude/AIShell/aishell/scripts/generate-progress-report.js
    fi
done
