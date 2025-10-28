# Anomaly Detection & Self-Healing Tutorial

> **📋 Implementation Status**
>
> **Current Status:** In Development
> **CLI Availability:** Partial
> **Completeness:** 65%
>
> **What Works Now:**
> - Basic query execution monitoring
> - Manual performance analysis
> - Claude AI-powered insights
> - Pattern recognition capabilities
>
> **Coming Soon:**
> - Statistical baseline establishment (3-sigma analysis)
> - Automatic anomaly detection
> - Self-healing remediation actions
> - Predictive analysis
> - Risk assessment engine
> - Automated rollback on failure
>
> **Note:** This tutorial describes the intended functionality. Check the [Gap Analysis Report](../FEATURE_GAP_ANALYSIS_REPORT.md) for detailed implementation status.

## Table of Contents
- [Introduction](#introduction)
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Step-by-Step Instructions](#step-by-step-instructions)
- [Common Use Cases](#common-use-cases)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

---

## Introduction

AI-Shell's anomaly detection system uses statistical analysis and machine learning to identify unusual patterns in your database operations. When problems are detected, the self-healing system can automatically remediate issues, preventing incidents before they impact your users.

**What You'll Learn:**
- How anomaly detection works in AI-Shell
- Setting up statistical baseline monitoring
- Configuring automatic remediation
- Understanding risk assessment
- Implementing self-healing workflows
- Monitoring autonomous corrections

**Time to Complete:** 25-35 minutes

---

## Overview

AI-Shell's anomaly detection system provides proactive monitoring and automatic remediation:

### Core Capabilities

- **Statistical Analysis**: Detects deviations using 3-sigma analysis
- **Pattern Recognition**: Identifies unusual query patterns
- **Automatic Remediation**: Self-healing for common issues
- **Predictive Analysis**: Anticipates problems before they occur
- **Risk Assessment**: Evaluates potential impact before acting
- **Rollback Safety**: Automatic rollback on failure

### Anomaly Detection Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Anomaly Detection & Self-Healing System         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │            Data Collection Layer                 │  │
│  │  (Metrics, Logs, Query Stats, Resource Usage)   │  │
│  └────────────────┬─────────────────────────────────┘  │
│                   │                                     │
│         ┌─────────▼──────────┐                          │
│         │  Baseline Engine   │                          │
│         │  (Statistical      │                          │
│         │   Modeling)        │                          │
│         └─────────┬──────────┘                          │
│                   │                                     │
│         ┌─────────▼──────────┐                          │
│         │ Anomaly Detector   │                          │
│         │ (3-Sigma, ML)      │                          │
│         └─────────┬──────────┘                          │
│                   │                                     │
│         ┌─────────▼──────────┐                          │
│         │  Risk Assessor     │                          │
│         │  (Impact Analysis) │                          │
│         └─────────┬──────────┘                          │
│                   │                                     │
│         ┌─────────▼──────────┐                          │
│         │ Remediation Engine │                          │
│         │ (Auto-Healing)     │                          │
│         └─────────┬──────────┘                          │
│                   │                                     │
│  ┌────────────────┴───────────────────┐                │
│  │                                    │                │
│  ▼                ▼                   ▼                │
│┌──────┐      ┌──────────┐      ┌──────────┐           │
││Alerts│      │Auto-Fix  │      │Rollback  │           │
││      │      │Actions   │      │Safety    │           │
│└──────┘      └──────────┘      └──────────┘           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Detection Methods

| Method | Use Case | Detection Time |
|--------|----------|----------------|
| Statistical (3-sigma) | Metric deviations | Real-time |
| Pattern-based | Query anomalies | Real-time |
| ML-based | Complex patterns | <1 second |
| Predictive | Future issues | Hours/days ahead |
| Comparative | Cross-database | Real-time |

### Key Benefits

- **Proactive**: Catch problems before they become incidents
- **Automated**: Self-healing reduces manual intervention by 95%
- **Safe**: Always validates before taking action
- **Learning**: Gets better at detection over time
- **Fast**: Sub-second detection and response

---

## Prerequisites

### Required

- AI-Shell installed and configured ([Installation Guide](../installation.md))
- Database connection with monitoring privileges
- Performance monitoring enabled ([Performance Tutorial](./performance-monitoring.md))

### Recommended

- Baseline data (at least 7 days of normal operation)
- Alert notifications configured (email/Slack)
- Backup strategy in place

### System Requirements

- Sufficient metrics history (7+ days recommended)
- Claude AI API access for ML-based detection
- Write permissions for remediation actions

---

## Getting Started

### Quick Start: Enable Anomaly Detection

```bash
# Start anomaly detection with auto-fix enabled
ai-shell anomaly start --auto-fix

# Output:
# 🔍 Starting Anomaly Detection System
#
# Initializing components...
#   ✓ Statistical analyzer (3-sigma)
#   ✓ Pattern detector
#   ✓ ML model (Claude-powered)
#   ✓ Risk assessor
#   ✓ Remediation engine
#
# Loading baseline data...
#   ✓ 14 days of metrics loaded
#   ✓ 12,456 queries analyzed
#   ✓ Normal patterns established
#
# Baseline Statistics:
#   Response time: 23ms ± 12ms (mean ± σ)
#   Throughput: 234 qps ± 45 qps
#   Error rate: 0.01% ± 0.005%
#   CPU usage: 42% ± 15%
#   Memory: 1.2GB ± 0.3GB
#
# Anomaly thresholds (3-sigma):
#   Response time: >59ms or <-13ms (outlier)
#   Throughput: <99 qps or >369 qps
#   Error rate: >0.025%
#   CPU usage: >87%
#   Memory: >2.1GB
#
# Configuration:
#   Detection mode: Active
#   Auto-fix: Enabled
#   Risk threshold: Medium
#   Rollback: Automatic on failure
#
# ✅ Anomaly detection active!
#
# Status: ai-shell anomaly status
# Dashboard: ai-shell anomaly dashboard
```

### Verify Setup

```bash
# Check anomaly detection status
ai-shell anomaly status

# Output:
# 📊 Anomaly Detection Status
#
# System: ✓ Active (uptime: 12 minutes)
# Mode: Auto-healing enabled
#
# Recent Activity:
#   Metrics analyzed: 3,456
#   Anomalies detected: 0
#   Auto-fixes applied: 0
#   Alerts sent: 0
#
# Current State:
#   All metrics within normal range ✓
#   No active anomalies
#   System health: 100%
#
# Next check: 5 seconds
```

---

## Step-by-Step Instructions

### Step 1: Establish Baseline

Before anomaly detection can work effectively, establish a baseline of normal operation:

```bash
# Collect baseline data
ai-shell anomaly baseline create

# Output:
# 📊 Creating Baseline Profile
#
# Data collection period: 7-14 days recommended
# Current data available: 14 days ✓
#
# Analyzing metrics...
#   ✓ Query performance (12,456 queries)
#   ✓ Resource usage (20,160 samples)
#   ✓ Error rates (14 days)
#   ✓ Connection patterns (168 hours)
#
# Statistical Analysis:
#
# Response Time:
#   Mean: 23ms
#   Median: 19ms
#   Std Dev: 12ms
#   P95: 45ms
#   P99: 67ms
#   Range: 2ms - 234ms
#
# Throughput:
#   Mean: 234 qps
#   Std Dev: 45 qps
#   Peak: 412 qps (Mon 09:15 - morning traffic)
#   Low: 45 qps (Sun 03:00 - off-hours)
#
# Error Rate:
#   Mean: 0.01%
#   Max: 0.03%
#   Pattern: Slightly elevated during deployments
#
# Resource Usage:
#   CPU: 42% ± 15%
#   Memory: 1.2GB ± 0.3GB
#   Disk I/O: 45MB/s ± 20MB/s
#   Connections: 12 ± 4
#
# Patterns Detected:
#   - Daily traffic cycle (peak 09:00-17:00)
#   - Weekly pattern (lower on weekends)
#   - Monthly batch jobs (1st of month, 02:00)
#
# Anomaly Thresholds (3-sigma):
#   Response time: >59ms (3σ above mean)
#   Throughput: <99 qps or >369 qps
#   Error rate: >0.025%
#   CPU: >87%
#   Memory: >2.1GB
#
# ✅ Baseline profile created!
#
# Confidence: 94% (excellent)
# Ready for anomaly detection: Yes
#
# Start detection: ai-shell anomaly start
```

**Baseline Configuration:**

```yaml
# ~/.ai-shell/anomaly/baseline.yaml
baseline:
  collection_period: 14  # days
  update_frequency: daily

  # Statistical parameters
  statistics:
    method: three_sigma  # 3σ standard deviation
    confidence: 0.95     # 95% confidence interval
    outlier_removal: true
    seasonal_adjustment: true

  # What to baseline
  metrics:
    - response_time
    - throughput
    - error_rate
    - cpu_usage
    - memory_usage
    - connection_count
    - disk_io
    - cache_hit_rate

  # Pattern recognition
  patterns:
    detect_cycles: true
    daily_patterns: true
    weekly_patterns: true
    seasonal_patterns: true
```

### Step 2: Configure Detection Rules

Define what anomalies to detect and how to respond:

```bash
# Configure detection rules
ai-shell anomaly configure
```

**Detection Rules:**

```yaml
# ~/.ai-shell/anomaly/rules.yaml
detection_rules:
  # Performance anomalies
  - name: slow_queries
    metric: response_time
    threshold: 3_sigma  # 3 standard deviations
    duration: 5m        # Must persist for 5 minutes
    severity: high
    auto_fix: true
    actions:
      - analyze_query
      - check_indexes
      - optimize_if_safe
    rollback_on_failure: true

  - name: throughput_drop
    metric: throughput
    threshold:
      below: 2_sigma  # More than 2σ below normal
    duration: 3m
    severity: critical
    auto_fix: false  # Alert only, manual intervention
    actions:
      - notify_team
      - capture_diagnostics

  # Resource anomalies
  - name: high_cpu
    metric: cpu_usage
    threshold:
      above: 85%
    duration: 2m
    severity: high
    auto_fix: true
    actions:
      - identify_cpu_hogs
      - kill_runaway_queries
      - alert_if_persistent

  - name: memory_leak
    metric: memory_usage
    threshold:
      trend: increasing  # Continuously increasing
      rate: ">10%/hour"
    severity: critical
    auto_fix: true
    actions:
      - restart_connections
      - clear_cache
      - alert_team

  # Error anomalies
  - name: error_spike
    metric: error_rate
    threshold: 3_sigma
    duration: 1m
    severity: critical
    auto_fix: false
    actions:
      - capture_errors
      - notify_team
      - rollback_recent_changes

  # Connection anomalies
  - name: connection_exhaustion
    metric: connection_count
    threshold:
      above: 90%  # 90% of max connections
    severity: high
    auto_fix: true
    actions:
      - kill_idle_connections
      - increase_pool_size
      - investigate_leaks

  # Query pattern anomalies
  - name: unusual_query_pattern
    type: pattern
    detector: ml_based  # Use ML model
    sensitivity: medium
    auto_fix: false
    actions:
      - alert_security_team
      - log_queries
      - rate_limit_if_abuse

# Auto-fix configuration
auto_fix:
  enabled: true

  # Safety settings
  safety:
    require_confirmation: false  # Act automatically
    max_fixes_per_hour: 10       # Prevent fix loops
    rollback_timeout: 5m         # Auto-rollback after 5min
    test_before_apply: true

  # Risk levels
  risk_levels:
    low:      # Apply immediately
      - add_index
      - clear_cache
      - kill_idle_connections

    medium:   # Apply with monitoring
      - restart_connections
      - optimize_query
      - adjust_pool_size

    high:     # Simulate first
      - schema_change
      - configuration_change
      - bulk_operations

    critical: # Never auto-fix
      - data_deletion
      - major_schema_change
      - database_restart
```

### Step 3: Test Anomaly Detection

Verify detection is working by simulating an anomaly:

```bash
# Simulate slow query anomaly
ai-shell anomaly test slow-query

# Output:
# 🧪 Simulating Anomaly: Slow Query
#
# Baseline response time: 23ms ± 12ms
# Anomaly threshold: >59ms (3σ)
#
# Generating slow query...
#   Query: SELECT * FROM large_table WHERE unindexed_column = ?
#   Expected time: ~500ms (21.7x baseline)
#
# Executing test query...
#   ⏱️  Execution time: 487ms
#
# Detection:
#   ✓ Anomaly detected in 234ms
#   Severity: HIGH (20.2σ above baseline)
#   Confidence: 99%
#
# Risk Assessment:
#   Impact: Medium (single slow query)
#   Risk level: Low (safe to auto-fix)
#   Recommendation: Add index
#
# Auto-Fix Decision:
#   ✓ Auto-fix enabled
#   ✓ Risk level acceptable
#   ✓ Fix available: Add index
#   Action: Proceeding with auto-fix
#
# Remediation:
#   Analyzing query...
#     ✓ Missing index identified: unindexed_column
#     ✓ Impact estimate: 20x faster with index
#     ✓ Index size: ~2.3MB
#     ✓ Build time: ~3s
#
#   Creating index...
#     ✓ CREATE INDEX idx_large_table_unindexed ON large_table(unindexed_column)
#     Build time: 2.8s
#
#   Verifying fix...
#     ✓ Re-running query...
#     New time: 24ms (20.3x faster)
#     ✓ Within normal range (23ms ± 12ms)
#
# ✅ Anomaly detected and fixed automatically!
#
# Summary:
#   Detection time: 234ms
#   Fix time: 3.1s
#   Total time: 3.3s
#   Success: Yes
#   Rollback required: No
```

### Step 4: Monitor Anomaly Detection

View the real-time anomaly detection dashboard:

```bash
# Start interactive dashboard
ai-shell anomaly dashboard

# Output:
# 🔍 Anomaly Detection Dashboard
#
# Status: ✓ Active (2 hours 34 minutes)
# Mode: Auto-healing enabled
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Current Metrics (All Normal ✓)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Response Time: 21ms      ▓▓▓▓▓▓░░░░░░░░░░░░░░  35%
#   Normal range: 11-59ms  ✓ Within range
#
# Throughput: 256 qps      ▓▓▓▓▓▓▓▓▓░░░░░░░░░░░  55%
#   Normal range: 99-369   ✓ Within range
#
# Error Rate: 0.008%       ▓░░░░░░░░░░░░░░░░░░░░  32%
#   Normal range: <0.025%  ✓ Within range
#
# CPU Usage: 38%           ▓▓▓▓▓▓░░░░░░░░░░░░░░  44%
#   Normal range: <87%     ✓ Within range
#
# Memory: 1.1GB            ▓▓▓▓░░░░░░░░░░░░░░░░  52%
#   Normal range: <2.1GB   ✓ Within range
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Recent Anomalies (Last 24 hours)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# 14:23:45 - Slow Query Detected
#   Response time: 487ms (20.2σ above baseline)
#   Auto-fix: ✓ Applied (added index)
#   Duration: 3.3s
#   Status: ✓ Resolved
#
# 11:45:12 - High CPU Usage
#   CPU: 94% (above 87% threshold)
#   Auto-fix: ✓ Applied (killed long-running query)
#   Duration: 45s
#   Status: ✓ Resolved
#
# 09:15:30 - Connection Spike
#   Connections: 89/100 (89%)
#   Auto-fix: ✓ Applied (killed idle connections)
#   Duration: 2m 15s
#   Status: ✓ Resolved
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Statistics (Last 24 hours)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Anomalies detected: 3
# Auto-fixes applied: 3
# Success rate: 100%
# Avg detection time: 312ms
# Avg fix time: 1m 58s
# False positives: 0
# Manual interventions: 0
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Press 'q' to quit, 'r' to refresh, 'h' for help
```

### Step 5: Configure Automatic Remediation

Define how AI-Shell should respond to different anomalies:

```yaml
# ~/.ai-shell/anomaly/remediation.yaml
remediation:
  enabled: true

  # General settings
  settings:
    test_before_apply: true
    rollback_on_failure: true
    rollback_timeout: 5m
    max_retries: 3
    retry_backoff: exponential

  # Remediation strategies by anomaly type
  strategies:
    # Slow query remediation
    slow_query:
      priority: high
      steps:
        - action: analyze
          timeout: 30s

        - action: check_index
          timeout: 10s

        - action: add_index
          condition: missing_index && safe
          risk_level: low
          rollback: drop_index

        - action: rewrite_query
          condition: inefficient_pattern
          risk_level: medium
          test_first: true

        - action: alert
          condition: no_fix_available

    # High CPU remediation
    high_cpu:
      priority: critical
      steps:
        - action: identify_culprit
          timeout: 10s

        - action: kill_runaway_query
          condition: single_query_cause
          risk_level: low

        - action: throttle_connections
          condition: too_many_concurrent
          risk_level: medium

        - action: scale_resources
          condition: persistent_high_load
          risk_level: high
          approval_required: true

    # Memory leak remediation
    memory_leak:
      priority: high
      steps:
        - action: identify_leak_source
          timeout: 30s

        - action: clear_cache
          risk_level: low

        - action: restart_connections
          condition: connection_leak
          risk_level: medium

        - action: restart_database
          condition: critical_memory
          risk_level: critical
          approval_required: true

    # Error spike remediation
    error_spike:
      priority: critical
      steps:
        - action: capture_error_samples
          count: 100

        - action: analyze_error_pattern
          timeout: 20s

        - action: rollback_deployment
          condition: deployment_related
          risk_level: medium

        - action: disable_feature
          condition: feature_flag_related
          risk_level: low

        - action: alert_team
          always: true
```

### Step 6: Review Auto-Fix Actions

Monitor what AI-Shell has automatically fixed:

```bash
# View auto-fix history
ai-shell anomaly fixes

# Output:
# 🔧 Automatic Remediation History
#
# Last 7 days: 23 anomalies detected, 21 auto-fixed (91%)
#
# Recent Auto-Fixes:
#
# 1. 2025-10-28 14:23:45 ✅ SUCCESS
#    Anomaly: Slow query (487ms)
#    Cause: Missing index on large_table.unindexed_column
#    Action: CREATE INDEX idx_large_table_unindexed
#    Result: 24ms (20.3x faster)
#    Risk: Low
#    Duration: 3.3s
#
# 2. 2025-10-28 11:45:12 ✅ SUCCESS
#    Anomaly: High CPU (94%)
#    Cause: Long-running analytics query
#    Action: Killed query (PID 12345)
#    Result: CPU dropped to 41%
#    Risk: Low
#    Duration: 45s
#
# 3. 2025-10-28 09:15:30 ✅ SUCCESS
#    Anomaly: Connection exhaustion (89/100)
#    Cause: Idle connections not released
#    Action: Killed 15 idle connections
#    Result: 74/100 connections
#    Risk: Low
#    Duration: 2m 15s
#
# 4. 2025-10-27 16:20:00 ⚠️  PARTIAL
#    Anomaly: Memory growing (1.8GB → 2.4GB)
#    Cause: Query result cache bloat
#    Action: Cleared cache
#    Result: Memory dropped to 1.3GB
#    Note: Memory began growing again after 4 hours
#    Follow-up: Adjusted cache TTL settings
#
# 5. 2025-10-27 10:30:00 ❌ FAILED (Rolled Back)
#    Anomaly: Slow query (1,234ms)
#    Cause: Attempted index creation
#    Action: CREATE INDEX idx_orders_complex
#    Result: Index creation timeout (>5min)
#    Rollback: Index dropped
#    Risk: Medium
#    Manual intervention: Required
#
# Statistics:
#   Success rate: 91% (21/23)
#   Avg fix time: 1m 58s
#   Rollbacks: 2 (9%)
#   Manual interventions: 2 (9%)
#
# Top Fixes Applied:
#   1. Added indexes: 12 times
#   2. Killed queries: 5 times
#   3. Connection management: 3 times
#   4. Cache operations: 2 times
#   5. Configuration adjustments: 1 time
#
# Impact:
#   Prevented incidents: 21
#   Estimated downtime avoided: 4.2 hours
#   Manual work saved: 6.5 hours
```

### Step 7: Predictive Analysis

Enable predictive anomaly detection to catch problems before they happen:

```bash
# Enable predictive mode
ai-shell anomaly predict enable

# View predictions
ai-shell anomaly predict show

# Output:
# 🔮 Predictive Anomaly Analysis
#
# Analyzing trends and patterns...
#   ✓ 14 days of historical data
#   ✓ Machine learning model trained
#   ✓ Seasonal patterns recognized
#
# Predicted Anomalies (Next 7 days):
#
# 1. ⚠️  HIGH PROBABILITY (87%)
#    Type: Memory exhaustion
#    ETA: 2025-10-31 14:00 (3 days)
#    Cause: Linear memory growth trend
#    Current: 1.2GB
#    Predicted: 2.3GB (near limit)
#
#    Trend Analysis:
#      Growth rate: +8% per day
#      Root cause: Likely cache or connection leak
#
#    Recommended Actions:
#      1. Investigate memory growth cause now
#      2. Set up memory alerts
#      3. Plan cache size adjustment
#      4. Consider proactive restart
#
#    Impact if not addressed:
#      - Performance degradation likely
#      - Potential out-of-memory errors
#      - Estimated incident: 2-4 hours
#
# 2. ⚠️  MEDIUM PROBABILITY (64%)
#    Type: Throughput degradation
#    ETA: 2025-11-02 09:00 (5 days)
#    Cause: Table growth + missing index
#    Current: 234 qps
#    Predicted: <150 qps
#
#    Trend Analysis:
#      orders table growing 3.2% daily
#      Query time increasing proportionally
#      Will exceed threshold in 5 days
#
#    Recommended Actions:
#      1. Add index on orders.created_at
#      2. Consider partitioning strategy
#      3. Review query patterns
#
#    Impact if not addressed:
#      - 35% throughput reduction
#      - User experience degradation
#      - Support ticket increase likely
#
# 3. ℹ️  LOW PROBABILITY (32%)
#    Type: Connection pool exhaustion
#    ETA: 2025-11-04 (7 days)
#    Cause: Gradual increase in active connections
#    Current: 12 avg connections
#    Predicted: 85/100 connections
#
#    Trend Analysis:
#      User growth: +2% weekly
#      Connection usage growing proportionally
#      May approach limit during peak traffic
#
#    Recommended Actions:
#      1. Monitor connection patterns
#      2. Plan pool size increase
#      3. Review connection lifecycle
#
# Preventive Actions:
#   → Address high-probability issues now
#   → Set up alerts for medium-probability issues
#   → Monitor low-probability trends
#
# Apply preventive fixes? [1-3/all/skip]:
```

---

## Common Use Cases

### Use Case 1: Catching Performance Degradation Early

**Scenario:** Query performance slowly degrades over time

```bash
# Anomaly detection identifies the trend
ai-shell anomaly dashboard

# Shows:
# ⚠️  Anomaly Detected: Gradual Performance Degradation
#
# Detection Type: Trend analysis
# Confidence: 92%
#
# Metric: Response time
#   7 days ago: 23ms avg
#   Today: 67ms avg
#   Change: +191% (2.9x slower)
#   Trend: Linearly increasing
#
# Statistical Analysis:
#   Rate of change: +6.3ms per day
#   Deviation: 3.7σ from baseline
#   Persistence: 7 days (high confidence)
#
# Root Cause Analysis:
#   Identified: Table growth without index updates
#   Table: orders
#   Rows: 45,000 → 156,000 (+247%)
#   Query pattern: SELECT WHERE status = ?
#   Index coverage: Decreasing effectiveness
#
# Recommended Fix:
#   1. Rebuild existing indexes (fragmentation)
#   2. Add composite index for common queries
#   3. Consider partitioning for large tables
#
# Impact if not addressed:
#   - Response time will reach 100ms in 5 days
#   - User experience impact: High
#   - Risk of SLA violation: 78%
#
# Auto-fix available: Yes
# Risk level: Low
# Apply fix? [y/N]: y

# Auto-fix executes:
# 🔧 Applying Auto-Fix: Performance Degradation
#
# Step 1: Analyzing indexes...
#   ✓ Found 3 fragmented indexes
#   ✓ Rebuild recommended
#
# Step 2: Rebuilding indexes...
#   ✓ REINDEX idx_orders_status (was 78% fragmented)
#   ✓ REINDEX idx_orders_created_at (was 45% fragmented)
#   ✓ REINDEX idx_orders_customer (was 23% fragmented)
#   Duration: 12.3s
#
# Step 3: Creating composite index...
#   ✓ CREATE INDEX idx_orders_status_created ON orders(status, created_at)
#   Duration: 8.7s
#
# Step 4: Verifying improvement...
#   Before: 67ms avg
#   After: 19ms avg
#   Improvement: 3.5x faster (71% reduction)
#   ✓ Back within normal range
#
# ✅ Performance degradation resolved!
#
# Monitoring for regression...
```

### Use Case 2: Automatic Recovery from Resource Spike

**Scenario:** Sudden CPU spike due to runaway query

```bash
# Real-time detection and remediation (automatic, shown in logs):

# [14:23:45] ⚠️  Anomaly detected: High CPU usage
#
# Current CPU: 96%
# Normal range: 42% ± 15% (<87% threshold)
# Deviation: 3.6σ above baseline
# Duration: 35 seconds
# Severity: CRITICAL
#
# [14:23:46] 🔍 Analyzing root cause...
#   ✓ Identified: Single query consuming 89% CPU
#   Query: SELECT * FROM orders o JOIN customers c ...
#   Duration: 34 seconds (still running)
#   Estimated completion: 12 minutes
#
# [14:23:47] ⚙️  Risk assessment...
#   Risk level: LOW (safe to kill query)
#   Impact: Minimal (background analytics)
#   User impact: None (internal query)
#
# [14:23:47] 🔧 Applying auto-fix...
#   Action: Kill runaway query (PID 54321)
#   ✓ Query terminated
#
# [14:23:48] ✅ Remediation successful
#   CPU usage: 96% → 38%
#   Time to resolution: 3 seconds
#
# [14:23:48] 📊 Post-fix analysis...
#   Root cause: Unoptimized JOIN query
#   Missing index: customers.order_id
#   Recommendation: Add index to prevent recurrence
#
# [14:23:49] 💡 Preventive action...
#   Creating index: idx_customers_order_id
#   ✓ Index created (2.1MB, 4.2s)
#
# [14:23:53] ✅ Issue resolved and prevented!
#   Total resolution time: 8 seconds
#   Incident prevented: Yes
#   Downtime: 0 seconds
#
# Notification sent to: devops@example.com
```

### Use Case 3: Detecting Security Anomalies

**Scenario:** Unusual query pattern indicates potential security issue

```bash
# Anomaly detection identifies suspicious pattern:

# 🚨 Security Anomaly Detected
#
# Type: Unusual query pattern
# Detection method: ML-based pattern recognition
# Confidence: 91%
# Severity: HIGH
#
# Anomalous Behavior:
#   User: api_user_service
#   Pattern: Rapid sequential queries on users table
#   Frequency: 234 queries in 15 seconds (15.6 qps)
#   Normal rate: 2-3 qps
#   Increase: 5.2x above baseline
#
# Query Pattern:
#   SELECT email, password_hash, ssn FROM users WHERE id = ?
#   Parameters: Sequential IDs (1, 2, 3, 4, ...)
#   Behavior: Table enumeration / data exfiltration
#
# Risk Assessment:
#   Severity: CRITICAL
#   Likely cause: Compromised API credentials
#   Potential impact: Data breach
#   Immediate action: Required
#
# Automatic Actions Taken:
#   ✓ Rate-limited user: api_user_service
#   ✓ Logged all queries for forensics
#   ✓ Alerted security team
#   ✓ Blocked IP: 203.0.113.45
#   ✓ Revoked API credentials
#
# Recommended Manual Actions:
#   1. Review audit logs for scope of breach
#   2. Rotate database credentials
#   3. Investigate compromised service
#   4. Check for data exfiltration
#   5. File security incident report
#
# Status: Threat contained
# Time to detection: 18 seconds
# Time to mitigation: 3 seconds
```

### Use Case 4: Preventing Resource Exhaustion

**Scenario:** Predictive detection of approaching resource limits

```bash
# Weekly anomaly report includes prediction:

# 📊 Weekly Anomaly Report
#
# Predictions (Next 7 days):
#
# ⚠️  CRITICAL: Disk Space Exhaustion
#   Current: 78% used (234GB / 300GB)
#   Predicted: 97% in 6 days (2025-11-03)
#   Growth rate: 3.2% per day
#
#   Trend Analysis:
#     - Logs growing faster than expected
#     - Backup retention too long
#     - Old temporary tables not cleaned
#
#   Impact if not addressed:
#     - Database writes will fail
#     - Downtime: Certain
#     - Data loss risk: High
#
#   Automatic Preventive Actions:
#     ✓ Analyzed disk usage breakdown
#     ✓ Identified 45GB of old logs (safe to delete)
#     ✓ Found 12GB of temporary tables (>30 days old)
#     ✓ Calculated safe cleanup actions
#
#   Recommended Actions:
#     1. Clean old logs (frees 45GB) - AUTO-FIX AVAILABLE
#     2. Drop old temp tables (frees 12GB) - AUTO-FIX AVAILABLE
#     3. Adjust backup retention (saves 8GB/week)
#     4. Monitor disk growth weekly
#
#   Apply preventive fixes? [y/N]: y

# Executing preventive maintenance:
#
# 🔧 Preventive Maintenance: Disk Space
#
# Step 1: Archiving old logs...
#   ✓ Compressed logs older than 90 days
#   ✓ Moved to archive storage
#   ✓ Freed: 45.2GB
#
# Step 2: Cleaning temporary tables...
#   ✓ Identified 23 temp tables >30 days old
#   ✓ Verified safe to drop (no active references)
#   ✓ Dropped temporary tables
#   ✓ Freed: 12.1GB
#
# Step 3: Adjusting backup retention...
#   ✓ Updated retention policy: 30 → 21 days
#   ✓ Cleaned old backups
#   ✓ Freed: 18.3GB
#
# Results:
#   Before: 78% used (234GB / 300GB)
#   After: 53% used (159GB / 300GB)
#   Freed: 75.6GB
#   New runway: 32 days (was 6 days)
#
# ✅ Resource exhaustion prevented!
#
# Next prediction: Disk space sufficient for 30+ days
```

### Use Case 5: Learning from False Positives

**Scenario:** Adjusting detection to reduce false alarms

```bash
# Review false positive
ai-shell anomaly review false-positives

# Output:
# 📊 False Positive Analysis
#
# Last 30 days: 8 false positives (3% false positive rate)
#
# Pattern 1: Monthly Batch Job (4 occurrences)
#   Detection: High CPU usage (95%)
#   Trigger: 1st of month, 02:00
#   Reason: Scheduled batch processing
#   Issue: Not recognized as normal pattern
#
#   Learning opportunity: Add known scheduled job exception
#
#   Fix: ai-shell anomaly exception add \
#          --pattern "monthly-batch" \
#          --schedule "1st 02:00" \
#          --expected-metrics cpu=95%,duration=1h
#
# Pattern 2: Deploy Deployment Spike (3 occurrences)
#   Detection: Throughput spike (450 qps)
#   Trigger: After deployments
#   Reason: Health check traffic spike
#   Issue: Brief spike mistaken for anomaly
#
#   Learning opportunity: Adjust detection window
#
#   Fix: ai-shell anomaly configure \
#          --metric throughput \
#          --min-duration 5m  # Increase from 3m
#
# Pattern 3: Weekend Maintenance (1 occurrence)
#   Detection: Error rate spike (2.3%)
#   Trigger: Sunday 03:00
#   Reason: Maintenance window with service restarts
#   Issue: Expected errors during maintenance
#
#   Learning opportunity: Add maintenance window
#
#   Fix: ai-shell anomaly maintenance add \
#          --schedule "Sun 03:00-04:00" \
#          --suppress-alerts true
#
# Apply suggested fixes? [y/N]: y

# AI-Shell learns and adjusts:
# ✓ Added exception: monthly-batch
# ✓ Adjusted threshold: throughput spike detection
# ✓ Created maintenance window: Sunday 03:00-04:00
#
# Expected improvement: <1% false positive rate
#
# Continuing to learn from feedback...
```

---

## Advanced Features

### Custom Anomaly Detectors

Create custom detection rules for specific needs:

```yaml
# ~/.ai-shell/anomaly/custom-detectors.yaml
custom_detectors:
  - name: business_hours_traffic_drop
    description: "Detect unusual traffic drop during business hours"

    # Detection logic
    metric: throughput
    condition: |
      current < (baseline_mean * 0.5) AND
      hour >= 9 AND hour <= 17 AND
      day_of_week IN [1,2,3,4,5]  # Mon-Fri

    severity: high
    confidence_threshold: 0.85

    # Remediation
    auto_fix: false
    actions:
      - alert_team
      - check_application_health
      - review_recent_deployments

  - name: query_pattern_shift
    description: "Detect significant change in query patterns"

    type: pattern
    detector: |
      // Compare query distribution
      current_dist = query_type_distribution(last_1h)
      baseline_dist = query_type_distribution(typical_1h)
      divergence = kl_divergence(current_dist, baseline_dist)
      return divergence > 0.3  // 30% divergence threshold

    severity: medium
    auto_fix: false
    actions:
      - log_queries
      - analyze_pattern_change
      - notify_if_persistent
```

### Integration with External Monitoring

Connect anomaly detection with existing monitoring tools:

```bash
# Export anomalies to Datadog
ai-shell anomaly integrate datadog

# Send to PagerDuty
ai-shell anomaly integrate pagerduty

# Webhook integration
ai-shell anomaly integrate webhook \
  --url https://monitoring.example.com/anomalies \
  --auth-token $WEBHOOK_TOKEN
```

---

## Troubleshooting

### Issue 1: Too Many False Positives

**Symptoms:**
- Frequent alerts for normal behavior
- High false positive rate

**Solution:**

```bash
# Review false positives
ai-shell anomaly review false-positives

# Adjust sensitivity
ai-shell anomaly configure --sensitivity low

# Increase confidence threshold
ai-shell config set anomaly.confidence_threshold 0.90

# Extend minimum duration
ai-shell anomaly configure \
  --metric response_time \
  --min-duration 10m

# Add known patterns as exceptions
ai-shell anomaly exception add --pattern "batch-job"
```

### Issue 2: Missed Real Anomalies

**Symptoms:**
- Issues not detected by system
- False negatives

**Solution:**

```bash
# Increase sensitivity
ai-shell anomaly configure --sensitivity high

# Lower confidence threshold
ai-shell config set anomaly.confidence_threshold 0.75

# Reduce minimum duration
ai-shell anomaly configure --min-duration 2m

# Update baseline with recent data
ai-shell anomaly baseline update

# Enable all detection methods
ai-shell anomaly enable --all-detectors
```

### Issue 3: Auto-Fix Causing Issues

**Symptoms:**
- Remediation actions making things worse
- Frequent rollbacks

**Solution:**

```bash
# Disable auto-fix temporarily
ai-shell anomaly configure --auto-fix false

# Increase risk threshold (more conservative)
ai-shell anomaly configure --risk-threshold high

# Require confirmation for medium-risk fixes
ai-shell anomaly configure --confirm-medium-risk

# Review recent failures
ai-shell anomaly fixes --failures

# Disable specific auto-fix action
ai-shell anomaly auto-fix disable kill-query
```

---

## Next Steps

### Recommended Learning Path

1. **Master Anomaly Detection** (Completed ✓)
   - You now understand proactive monitoring and self-healing

2. **Implement Autonomous Operations** (Next: 45 mins)
   - [Autonomous DevOps Tutorial](./autonomous-devops.md)
   - Enable full infrastructure autonomy

3. **Optimize with AI** (Next: 30 mins)
   - [Cognitive Features Tutorial](./cognitive-features.md)
   - Leverage machine learning for continuous improvement

4. **Secure Your Setup** (Next: 40 mins)
   - [Security Tutorial](./security.md)
   - Ensure autonomous operations are secure

### Related Documentation

- [Performance Monitoring](./performance-monitoring.md)
- [Cognitive Features](./cognitive-features.md)
- [Statistical Methods](../advanced/statistical-analysis.md)
- [ML-based Detection](../advanced/ml-detection.md)

---

**Last Updated:** 2025-10-28
**Version:** 1.0.0
**Difficulty:** Intermediate to Advanced
