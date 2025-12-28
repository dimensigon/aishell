# 🏥 AIShell Health Check System - Hands-On Tutorial

**Master the art of system health monitoring with async health checks**

---

## 📚 Table of Contents

1. [Introduction](#1-introduction)
2. [Quick Start](#2-quick-start)
3. [Built-in Health Checks](#3-built-in-health-checks)
4. [Creating Custom Checks](#4-creating-custom-checks)
5. [Async vs Sync Checks](#5-async-vs-sync-checks)
6. [Timeout Configuration](#6-timeout-configuration)
7. [Integration Examples](#7-integration-examples)
8. [Troubleshooting](#8-troubleshooting)
9. [Performance Tips](#9-performance-tips)
10. [Advanced Examples](#10-advanced-examples)

---

## 1. Introduction

### What are Health Checks?

Health checks are diagnostic tests that verify your system's components are functioning correctly. They're essential for:

- **🚀 Startup validation** - Ensure all dependencies are ready before accepting requests
- **🔍 Proactive monitoring** - Detect issues before they impact users
- **📊 System observability** - Get real-time insights into component status
- **⚡ Fast failure detection** - Identify problems in < 2 seconds

### Why Use AIShell's Health Check System?

✅ **Parallel Execution** - All checks run concurrently for speed
✅ **Timeout Protection** - No single check can hang the system
✅ **Async-First Design** - Non-blocking for high performance
✅ **Extensible** - Easy to add custom checks
✅ **Built-in Checks** - LLM, Database, Filesystem, and Memory checks included

---

## 2. Quick Start

### 🚀 5-Minute Example

Let's run your first health check in just a few lines of code!

```python
import asyncio
from src.core.health_checks import run_health_checks

async def main():
    # Run all built-in health checks
    results = await run_health_checks()

    # Display results
    for result in results:
        status_emoji = "✅" if result.status.value == "pass" else "❌"
        print(f"{status_emoji} {result.name}: {result.message} ({result.duration:.2f}s)")

if __name__ == "__main__":
    asyncio.run(main())
```

**Expected Output:**

```
✅ llm_availability: LLM API key configured (0.01s)
✅ database_connectivity: Database connectivity OK (0.02s)
✅ filesystem_access: File system read/write OK (0.01s)
✅ memory_usage: Memory OK (45.2% used, 8.3GB available) (0.00s)
```

### 💡 Try It Yourself

**Exercise 1:** Copy the code above into a file called `test_health.py` and run it:

```bash
cd /home/claude/AIShell
python test_health.py
```

**What to expect:** You should see 4 health checks complete in under 0.1 seconds total!

---

## 3. Built-in Health Checks

AIShell includes 4 pre-configured health checks that run automatically:

### 🤖 LLM Availability Check

**What it does:** Verifies that an LLM API key is configured in your environment.

**Checks for:**
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`

**Timeout:** 2 seconds

**Example Result:**

```python
HealthCheckResult(
    name='llm_availability',
    status=HealthStatus.PASS,
    message='LLM API key configured',
    duration=0.01
)
```

---

### 💾 Database Connectivity Check

**What it does:** Tests if SQLite database operations work correctly.

**Test:** Creates in-memory database, executes `SELECT 1`, verifies result.

**Timeout:** 3 seconds

**Example Result:**

```python
HealthCheckResult(
    name='database_connectivity',
    status=HealthStatus.PASS,
    message='Database connectivity OK',
    duration=0.02
)
```

---

### 📁 Filesystem Access Check

**What it does:** Verifies read/write access to temporary storage.

**Test:** Creates a temporary file, writes data, reads it back.

**Timeout:** 2 seconds

**Example Result:**

```python
HealthCheckResult(
    name='filesystem_access',
    status=HealthStatus.PASS,
    message='File system read/write OK',
    duration=0.01
)
```

---

### 🧠 Memory Usage Check

**What it does:** Monitors system memory availability using `psutil`.

**Status Levels:**
- **PASS** - Memory usage < 80%
- **WARN** - Memory usage 80-90%
- **FAIL** - Memory usage > 90%

**Timeout:** 1 second

**Example Results:**

```python
# Healthy system
HealthCheckResult(
    name='memory_usage',
    status=HealthStatus.PASS,
    message='Memory OK (45.2% used, 8.3GB available)',
    duration=0.00
)

# Warning state
HealthCheckResult(
    name='memory_usage',
    status=HealthStatus.WARN,
    message='Memory high (85.1% used, 2.1GB available)',
    duration=0.00
)
```

---

## 4. Creating Custom Checks

### 📝 Basic Custom Check

Let's create a simple check to verify API endpoint availability:

```python
from src.core.health_checks import HealthCheckRunner, HealthCheck, HealthStatus

def check_api_endpoint():
    """Check if API endpoint is reachable."""
    try:
        import requests
        response = requests.get("https://api.example.com/health", timeout=2)
        if response.status_code == 200:
            return HealthStatus.PASS, "API endpoint is healthy"
        else:
            return HealthStatus.FAIL, f"API returned {response.status_code}"
    except Exception as e:
        return HealthStatus.FAIL, f"API unreachable: {str(e)}"

# Register the check
runner = HealthCheckRunner()
runner.register_check(HealthCheck(
    name="api_endpoint",
    description="External API Availability",
    check_function=check_api_endpoint,
    is_async=False,
    timeout=5.0
))

# Run all checks
import asyncio
results = asyncio.run(runner.run_all_checks())
```

### 🎯 Step-by-Step Guide

**Step 1: Define Your Check Function**

```python
def my_custom_check():
    # Your check logic here
    if condition_ok:
        return HealthStatus.PASS, "Everything is good"
    else:
        return HealthStatus.FAIL, "Something went wrong"
```

**Step 2: Create HealthCheck Object**

```python
check = HealthCheck(
    name="my_custom_check",           # Unique identifier
    description="What this checks",   # Human-readable description
    check_function=my_custom_check,   # Your function
    is_async=False,                   # True if async function
    timeout=3.0                       # Max execution time in seconds
)
```

**Step 3: Register with Runner**

```python
runner = HealthCheckRunner()
runner.register_check(check)
```

**Step 4: Run Checks**

```python
results = await runner.run_all_checks()
```

### 💡 Try It Yourself

**Exercise 2:** Create a check that verifies a specific directory exists:

```python
from pathlib import Path
from src.core.health_checks import HealthCheckRunner, HealthCheck, HealthStatus

def check_data_directory():
    """Check if data directory exists and is writable."""
    data_dir = Path("/home/claude/AIShell/data")

    if not data_dir.exists():
        return HealthStatus.FAIL, "Data directory does not exist"

    if not data_dir.is_dir():
        return HealthStatus.FAIL, "Data path is not a directory"

    # Test write access
    test_file = data_dir / ".write_test"
    try:
        test_file.touch()
        test_file.unlink()
        return HealthStatus.PASS, "Data directory is accessible"
    except:
        return HealthStatus.WARN, "Data directory is read-only"

# TODO: Register and run this check!
```

---

## 5. Async vs Sync Checks

### 🔄 When to Use Each

| Use **Sync** Checks When... | Use **Async** Checks When... |
|------------------------------|------------------------------|
| Simple CPU-bound operations  | I/O-bound operations (network, disk) |
| Quick local validations      | Database queries |
| File system checks           | HTTP requests |
| Memory/CPU monitoring        | External API calls |

### Sync Check Example

```python
def sync_config_check():
    """Synchronous check - runs in thread pool."""
    import os
    config_file = "/home/claude/AIShell/config.yaml"

    if os.path.exists(config_file):
        return HealthStatus.PASS, "Config file found"
    else:
        return HealthStatus.FAIL, "Config file missing"

runner.register_check(HealthCheck(
    name="config_file",
    description="Configuration File",
    check_function=sync_config_check,
    is_async=False,  # ← Will run in thread pool
    timeout=1.0
))
```

### Async Check Example

```python
import aiohttp

async def async_service_check():
    """Asynchronous check - truly non-blocking."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8000/health") as response:
                if response.status == 200:
                    return HealthStatus.PASS, "Service is responding"
                else:
                    return HealthStatus.FAIL, f"Service returned {response.status}"
        except Exception as e:
            return HealthStatus.FAIL, f"Service unreachable: {str(e)}"

runner.register_check(HealthCheck(
    name="microservice_health",
    description="Internal Microservice",
    check_function=async_service_check,
    is_async=True,  # ← Runs natively in event loop
    timeout=3.0
))
```

### ⚡ Performance Comparison

```python
import time
import asyncio
from src.core.health_checks import HealthCheckRunner, HealthCheck, HealthStatus

# Slow sync check (blocks for 2 seconds)
def slow_sync_check():
    time.sleep(2)
    return HealthStatus.PASS, "Slow sync check complete"

# Slow async check (awaits for 2 seconds)
async def slow_async_check():
    await asyncio.sleep(2)
    return HealthStatus.PASS, "Slow async check complete"

runner = HealthCheckRunner()

# Register 3 slow sync checks
for i in range(3):
    runner.register_check(HealthCheck(
        name=f"sync_check_{i}",
        description=f"Sync Check {i}",
        check_function=slow_sync_check,
        is_async=False,
        timeout=5.0
    ))

# Register 3 slow async checks
for i in range(3):
    runner.register_check(HealthCheck(
        name=f"async_check_{i}",
        description=f"Async Check {i}",
        check_function=slow_async_check,
        is_async=True,
        timeout=5.0
    ))

# Run all 6 checks in parallel
start = time.perf_counter()
results = await runner.run_all_checks()
duration = time.perf_counter() - start

print(f"Total time for 6 checks: {duration:.2f}s")
# Output: ~2.0s (all run in parallel!)
```

### 💡 Key Takeaway

> **Both sync and async checks run in parallel!** Sync checks use `asyncio.to_thread()` to avoid blocking. The total time is determined by the slowest check, not the sum of all checks.

---

## 6. Timeout Configuration

### ⏱️ Why Timeouts Matter

Without timeouts, a single hanging check could stall your entire startup sequence. AIShell's health check system ensures **no check can block indefinitely**.

### Default Timeouts

```python
# Built-in check timeouts
{
    'llm_availability': 2.0,      # Fast environment check
    'database_connectivity': 3.0,  # Database operations can be slower
    'filesystem_access': 2.0,      # Should be very fast
    'memory_usage': 1.0            # Instant system call
}
```

### Setting Custom Timeouts

```python
# Generous timeout for external API
runner.register_check(HealthCheck(
    name="external_api",
    description="Third-party API",
    check_function=check_external_api,
    is_async=True,
    timeout=10.0  # ← 10 seconds max
))

# Strict timeout for local check
runner.register_check(HealthCheck(
    name="local_cache",
    description="Redis Cache",
    check_function=check_redis,
    is_async=True,
    timeout=0.5  # ← Must respond in 500ms
))
```

### Handling Timeout Errors

When a check times out, you get a clear error result:

```python
HealthCheckResult(
    name='slow_check',
    status=HealthStatus.FAIL,
    message='Timeout after 3.0s',
    duration=3.0
)
```

### Best Practices

| Check Type | Recommended Timeout | Rationale |
|------------|---------------------|-----------|
| Local file operations | 1-2 seconds | Should be near-instant |
| Database queries | 3-5 seconds | Allows for connection setup |
| HTTP health endpoints | 5-10 seconds | Network latency + processing |
| External APIs | 10-15 seconds | May have rate limiting |
| Complex validations | 5-10 seconds | Depends on computation |

### 💡 Try It Yourself

**Exercise 3:** Create a check with a timeout that triggers:

```python
import asyncio
from src.core.health_checks import HealthCheckRunner, HealthCheck

async def slow_check():
    """This will timeout!"""
    await asyncio.sleep(10)  # Sleeps for 10 seconds
    return HealthStatus.PASS, "Finally done"

runner = HealthCheckRunner()
runner.register_check(HealthCheck(
    name="timeout_test",
    description="Intentionally Slow Check",
    check_function=slow_check,
    is_async=True,
    timeout=2.0  # ← Will timeout after 2 seconds
))

results = await runner.run_all_checks()
for r in results:
    print(f"{r.name}: {r.message}")
    # Output: timeout_test: Timeout after 2.0s
```

---

## 7. Integration Examples

### 🚀 Startup Script Integration

**Scenario:** Run health checks before starting your application.

```python
#!/usr/bin/env python3
"""Application startup script with health checks."""

import asyncio
import sys
import logging
from src.core.health_checks import run_health_checks, HealthStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def startup():
    """Application startup with health validation."""

    print("🏥 Running system health checks...")
    results = await run_health_checks()

    # Check if all tests passed
    failed_checks = [r for r in results if r.status == HealthStatus.FAIL]
    warning_checks = [r for r in results if r.status == HealthStatus.WARN]

    # Display results
    for result in results:
        emoji = {"pass": "✅", "warn": "⚠️", "fail": "❌"}[result.status.value]
        print(f"{emoji} {result.description}: {result.message}")

    # Handle failures
    if failed_checks:
        logger.error(f"❌ {len(failed_checks)} health check(s) failed!")
        for check in failed_checks:
            logger.error(f"  - {check.name}: {check.message}")
        sys.exit(1)

    # Handle warnings
    if warning_checks:
        logger.warning(f"⚠️  {len(warning_checks)} health check(s) raised warnings")
        for check in warning_checks:
            logger.warning(f"  - {check.name}: {check.message}")

    # All good - start application
    logger.info("✅ All health checks passed! Starting application...")

    # Your application startup code here
    from src.ui.app_enhanced import EnhancedAIShellApp
    app = EnhancedAIShellApp()
    await app.run_async()

if __name__ == "__main__":
    asyncio.run(startup())
```

### 🎭 Matrix Startup Screen Integration

**Scenario:** Display health checks in a fancy Matrix-style UI.

```python
from textual.app import App
from textual.widgets import Static, Label
from src.core.health_checks import HealthCheckRunner, HealthStatus
import asyncio

class MatrixHealthScreen(App):
    """Matrix-style health check display."""

    async def on_mount(self):
        """Run health checks when screen mounts."""
        container = await self.mount(Static(id="health-container"))

        runner = HealthCheckRunner()

        # Run checks with live updates
        for check_name in runner.list_checks():
            # Show "checking..." message
            label = Label(f"⏳ {check_name}: Checking...")
            await container.mount(label)

            # Run single check
            check = runner.get_check(check_name)
            result = await runner._run_single_check(check)

            # Update with result
            emoji = {"pass": "✅", "warn": "⚠️", "fail": "❌"}[result.status.value]
            label.update(f"{emoji} {check_name}: {result.message}")

            await asyncio.sleep(0.2)  # Dramatic pause

        # Transition to main app after 1 second
        await asyncio.sleep(1)
        await self.exit()

if __name__ == "__main__":
    MatrixHealthScreen().run()
```

### 📊 Monitoring Dashboard Integration

**Scenario:** Periodic health checks for system monitoring.

```python
import asyncio
from datetime import datetime
from src.core.health_checks import run_health_checks, HealthStatus

async def health_monitor(interval_seconds=60):
    """Continuously monitor system health."""

    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n📊 Health Check Report - {timestamp}")
        print("=" * 60)

        results = await run_health_checks()

        # Categorize results
        passed = sum(1 for r in results if r.status == HealthStatus.PASS)
        warned = sum(1 for r in results if r.status == HealthStatus.WARN)
        failed = sum(1 for r in results if r.status == HealthStatus.FAIL)

        # Summary
        print(f"✅ Passed: {passed} | ⚠️  Warnings: {warned} | ❌ Failed: {failed}")
        print()

        # Details
        for result in results:
            emoji = {"pass": "✅", "warn": "⚠️", "fail": "❌"}[result.status.value]
            print(f"{emoji} {result.name:25} {result.message:40} ({result.duration:.3f}s)")

        # Alert on failures
        if failed > 0:
            print("\n🚨 ALERT: System health degraded!")
            # Send notification, page oncall, etc.

        # Wait for next check
        await asyncio.sleep(interval_seconds)

# Run monitor
asyncio.run(health_monitor(interval_seconds=30))
```

### 💡 Try It Yourself

**Exercise 4:** Create a simple HTTP health endpoint:

```python
from aiohttp import web
from src.core.health_checks import run_health_checks, HealthStatus

async def health_endpoint(request):
    """HTTP endpoint for health checks."""
    results = await run_health_checks()

    # Determine overall status
    if any(r.status == HealthStatus.FAIL for r in results):
        status_code = 503  # Service Unavailable
        overall = "unhealthy"
    elif any(r.status == HealthStatus.WARN for r in results):
        status_code = 200
        overall = "degraded"
    else:
        status_code = 200
        overall = "healthy"

    # Build response
    response_data = {
        "status": overall,
        "checks": [
            {
                "name": r.name,
                "status": r.status.value,
                "message": r.message,
                "duration_ms": round(r.duration * 1000, 2)
            }
            for r in results
        ]
    }

    return web.json_response(response_data, status=status_code)

# Create web app
app = web.Application()
app.router.add_get('/health', health_endpoint)

# Run server
web.run_app(app, port=8080)

# Test: curl http://localhost:8080/health
```

---

## 8. Troubleshooting

### ❌ Common Issues and Solutions

#### Issue 1: "No health checks registered"

**Symptom:**
```python
WARNING - No health checks registered
# Returns empty list []
```

**Cause:** Creating `HealthCheckRunner()` without auto-registering built-ins.

**Solution:**
```python
# The runner auto-registers built-in checks in __init__
runner = HealthCheckRunner()  # ✅ Built-ins are registered

# If you disabled built-ins somehow, re-register:
runner._register_builtin_checks()
```

---

#### Issue 2: Check Always Times Out

**Symptom:**
```
❌ my_check: Timeout after 5.0s
```

**Cause:** Check function is too slow or blocking.

**Solution:**

```python
# ❌ WRONG - Blocking sync operation
def bad_check():
    time.sleep(10)  # Too slow!
    return HealthStatus.PASS, "Done"

# ✅ CORRECT - Use async with proper timeout
async def good_check():
    await asyncio.sleep(2)  # Non-blocking
    return HealthStatus.PASS, "Done"

runner.register_check(HealthCheck(
    name="good_check",
    description="Fast Check",
    check_function=good_check,
    is_async=True,
    timeout=5.0  # Plenty of time
))
```

---

#### Issue 3: Check Raises Exception

**Symptom:**
```
❌ database_check: Error: connection refused
```

**Cause:** Unhandled exception in check function.

**Solution:**

```python
# ✅ Handle exceptions gracefully
def robust_check():
    try:
        # Risky operation
        conn = connect_to_database()
        return HealthStatus.PASS, "Connected"
    except ConnectionError as e:
        return HealthStatus.FAIL, f"Connection failed: {e}"
    except Exception as e:
        return HealthStatus.WARN, f"Unexpected error: {e}"
```

---

#### Issue 4: Async Check Not Working

**Symptom:**
```
TypeError: object NoneType can't be used in 'await' expression
```

**Cause:** Forgot to mark check as async.

**Solution:**

```python
# ❌ WRONG
async def my_async_check():
    await something()
    return HealthStatus.PASS, "OK"

runner.register_check(HealthCheck(
    name="async_check",
    check_function=my_async_check,
    is_async=False  # ← WRONG! Should be True
))

# ✅ CORRECT
runner.register_check(HealthCheck(
    name="async_check",
    check_function=my_async_check,
    is_async=True  # ← Correct
))
```

---

#### Issue 5: Duplicate Check Name

**Symptom:**
```
ValueError: Health check 'my_check' is already registered
```

**Cause:** Trying to register a check with a name that already exists.

**Solution:**

```python
# Option 1: Use unique names
runner.register_check(HealthCheck(name="my_check_v1", ...))
runner.register_check(HealthCheck(name="my_check_v2", ...))

# Option 2: Unregister old check first
runner.unregister_check("my_check")
runner.register_check(HealthCheck(name="my_check", ...))

# Option 3: Check if exists before registering
if "my_check" not in runner.list_checks():
    runner.register_check(HealthCheck(name="my_check", ...))
```

---

### 🔍 Debug Mode

Enable detailed logging to troubleshoot issues:

```python
import logging

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Now run health checks
results = await run_health_checks()

# Output will include:
# DEBUG - Registered health check: llm_availability
# DEBUG - Running health check: llm_availability
# INFO - Completed 4 health checks in 0.12s
```

---

## 9. Performance Tips

### ⚡ Optimization Strategies

#### 1. Parallel Execution (Built-in!)

The system automatically runs all checks in parallel. No configuration needed!

```python
# These 10 checks all run simultaneously
for i in range(10):
    runner.register_check(HealthCheck(
        name=f"check_{i}",
        check_function=slow_check,
        is_async=True,
        timeout=5.0
    ))

# Total time = slowest check, not sum of all checks!
results = await runner.run_all_checks()
```

#### 2. Set Appropriate Timeouts

```python
# ❌ TOO GENEROUS - Wastes time on hung checks
timeout=30.0

# ✅ JUST RIGHT - Fails fast
timeout=3.0
```

#### 3. Use Async for I/O Operations

```python
# ❌ SLOW - Blocks thread pool
def sync_network_check():
    response = requests.get("http://api.example.com")
    return HealthStatus.PASS, "OK"

# ✅ FAST - Non-blocking
async def async_network_check():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://api.example.com") as response:
            return HealthStatus.PASS, "OK"
```

#### 4. Cache Expensive Checks

```python
from functools import lru_cache
import time

@lru_cache(maxsize=1)
def expensive_computation():
    """Cache result for 60 seconds."""
    # Expensive operation
    time.sleep(5)
    return "computed_value"

def cached_check():
    """Reuses cached value if available."""
    result = expensive_computation()
    return HealthStatus.PASS, f"Result: {result}"

# First call: 5 seconds
# Subsequent calls: instant!
```

#### 5. Skip Unnecessary Checks

```python
import os

# Only check external API in production
if os.environ.get("ENV") == "production":
    runner.register_check(HealthCheck(
        name="external_api",
        check_function=check_external_api,
        is_async=True,
        timeout=10.0
    ))
```

### 📊 Performance Benchmarks

**Scenario:** 10 health checks with varying execution times

| Setup | Total Time | Notes |
|-------|------------|-------|
| All sync (serial) | ~30 seconds | Each blocks for 3s |
| All sync (parallel) | ~3 seconds | Runs in thread pool |
| All async (parallel) | ~3 seconds | True async execution |
| Mixed async/sync | ~3 seconds | Best of both worlds |

**Key Insight:** Parallel execution reduces total time to the duration of the slowest check!

### 💡 Try It Yourself

**Exercise 5:** Benchmark different approaches:

```python
import time
import asyncio
from src.core.health_checks import HealthCheckRunner, HealthCheck, HealthStatus

# Slow check (simulates database query)
def slow_check():
    time.sleep(1)
    return HealthStatus.PASS, "OK"

# Create 5 instances
runner = HealthCheckRunner()
for i in range(5):
    runner.register_check(HealthCheck(
        name=f"slow_check_{i}",
        check_function=slow_check,
        is_async=False,
        timeout=3.0
    ))

# Measure execution time
start = time.perf_counter()
results = await runner.run_all_checks()
duration = time.perf_counter() - start

print(f"5 checks completed in: {duration:.2f}s")
# Expected: ~1.0s (parallel execution!)

# Without parallelization, this would take 5 seconds
```

---

## 10. Advanced Examples

### 🚀 Example 1: Cascading Health Checks

**Scenario:** Some checks depend on others passing first.

```python
from src.core.health_checks import HealthCheckRunner, HealthCheck, HealthStatus
import asyncio

class CascadingHealthChecker:
    """Run health checks in dependency order."""

    def __init__(self):
        self.runner = HealthCheckRunner()
        self.results = {}

    async def check_with_dependencies(self, check_name, dependencies):
        """Run check only if dependencies pass."""

        # Check dependencies first
        for dep in dependencies:
            if dep not in self.results:
                # Run dependency
                dep_check = self.runner.get_check(dep)
                self.results[dep] = await self.runner._run_single_check(dep_check)

            # If dependency failed, skip this check
            if self.results[dep].status == HealthStatus.FAIL:
                return HealthCheckResult(
                    name=check_name,
                    status=HealthStatus.FAIL,
                    message=f"Dependency '{dep}' failed",
                    duration=0.0
                )

        # All dependencies passed, run this check
        check = self.runner.get_check(check_name)
        result = await self.runner._run_single_check(check)
        self.results[check_name] = result
        return result

# Example usage
checker = CascadingHealthChecker()

# Database check depends on network
await checker.check_with_dependencies("database", ["network"])

# API check depends on both database and network
await checker.check_with_dependencies("api", ["database", "network"])
```

---

### 🔄 Example 2: Retry Logic

**Scenario:** Retry flaky checks before failing.

```python
import asyncio
from src.core.health_checks import HealthCheckRunner, HealthCheck, HealthStatus

async def check_with_retry(check_func, max_retries=3, delay=1.0):
    """Retry check up to max_retries times."""

    for attempt in range(max_retries):
        try:
            result = await check_func() if asyncio.iscoroutinefunction(check_func) else check_func()

            # If it's a tuple, parse it
            if isinstance(result, tuple):
                status, message = result
                if status == HealthStatus.PASS:
                    return status, f"{message} (attempt {attempt + 1})"

            # Retry on non-PASS results
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)

        except Exception as e:
            if attempt == max_retries - 1:
                return HealthStatus.FAIL, f"Failed after {max_retries} attempts: {e}"
            await asyncio.sleep(delay)

    return HealthStatus.FAIL, f"Failed after {max_retries} attempts"

# Wrapper function for flaky check
async def flaky_api_check():
    """Simulates a flaky external API."""
    import random
    if random.random() < 0.7:  # 70% failure rate
        return HealthStatus.FAIL, "API unavailable"
    return HealthStatus.PASS, "API healthy"

async def robust_api_check():
    """Check with retry logic."""
    return await check_with_retry(flaky_api_check, max_retries=3, delay=0.5)

# Register the robust check
runner = HealthCheckRunner()
runner.register_check(HealthCheck(
    name="robust_api",
    check_function=robust_api_check,
    is_async=True,
    timeout=5.0
))
```

---

### 📊 Example 3: Health Check Metrics Collection

**Scenario:** Track health check performance over time.

```python
from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime
import statistics

@dataclass
class HealthMetrics:
    """Aggregate metrics for health checks."""
    check_name: str
    executions: int = 0
    total_duration: float = 0.0
    pass_count: int = 0
    warn_count: int = 0
    fail_count: int = 0
    durations: List[float] = field(default_factory=list)

    def record(self, result):
        """Record a health check result."""
        self.executions += 1
        self.total_duration += result.duration
        self.durations.append(result.duration)

        if result.status == HealthStatus.PASS:
            self.pass_count += 1
        elif result.status == HealthStatus.WARN:
            self.warn_count += 1
        else:
            self.fail_count += 1

    @property
    def avg_duration(self):
        return self.total_duration / self.executions if self.executions > 0 else 0

    @property
    def success_rate(self):
        return (self.pass_count / self.executions * 100) if self.executions > 0 else 0

    @property
    def p95_duration(self):
        if not self.durations:
            return 0
        sorted_durations = sorted(self.durations)
        idx = int(len(sorted_durations) * 0.95)
        return sorted_durations[idx]

class MetricsCollector:
    """Collect and analyze health check metrics."""

    def __init__(self):
        self.metrics: Dict[str, HealthMetrics] = {}

    async def run_and_record(self, runner: HealthCheckRunner):
        """Run checks and record metrics."""
        results = await runner.run_all_checks()

        for result in results:
            if result.name not in self.metrics:
                self.metrics[result.name] = HealthMetrics(result.name)
            self.metrics[result.name].record(result)

        return results

    def print_report(self):
        """Print metrics report."""
        print("\n📊 Health Check Metrics Report")
        print("=" * 80)

        for name, metrics in self.metrics.items():
            print(f"\n{name}:")
            print(f"  Executions: {metrics.executions}")
            print(f"  Success Rate: {metrics.success_rate:.1f}%")
            print(f"  Avg Duration: {metrics.avg_duration * 1000:.2f}ms")
            print(f"  P95 Duration: {metrics.p95_duration * 1000:.2f}ms")
            print(f"  Pass/Warn/Fail: {metrics.pass_count}/{metrics.warn_count}/{metrics.fail_count}")

# Usage
collector = MetricsCollector()
runner = HealthCheckRunner()

# Run checks 100 times
for i in range(100):
    await collector.run_and_record(runner)
    await asyncio.sleep(1)

# Print report
collector.print_report()
```

---

### 🎨 Example 4: Custom Status Levels

**Scenario:** Add custom status levels beyond PASS/WARN/FAIL.

```python
from enum import Enum
from dataclasses import dataclass

class ExtendedHealthStatus(Enum):
    """Extended status levels."""
    OPTIMAL = "optimal"      # Better than PASS
    PASS = "pass"
    DEGRADED = "degraded"    # Between WARN and PASS
    WARN = "warn"
    CRITICAL = "critical"    # Between WARN and FAIL
    FAIL = "fail"
    UNKNOWN = "unknown"      # Cannot determine status

@dataclass
class ExtendedHealthCheckResult:
    """Health check result with extended status."""
    name: str
    status: ExtendedHealthStatus
    message: str
    duration: float
    metrics: dict = None  # Additional metrics

def check_response_time():
    """Check API response time with granular status."""
    import time
    import random

    start = time.perf_counter()
    # Simulate API call
    time.sleep(random.uniform(0.1, 2.0))
    response_time = time.perf_counter() - start

    # Granular status based on response time
    if response_time < 0.5:
        status = ExtendedHealthStatus.OPTIMAL
        message = f"Excellent response time: {response_time:.3f}s"
    elif response_time < 1.0:
        status = ExtendedHealthStatus.PASS
        message = f"Good response time: {response_time:.3f}s"
    elif response_time < 1.5:
        status = ExtendedHealthStatus.DEGRADED
        message = f"Degraded response time: {response_time:.3f}s"
    elif response_time < 2.0:
        status = ExtendedHealthStatus.WARN
        message = f"Slow response time: {response_time:.3f}s"
    else:
        status = ExtendedHealthStatus.CRITICAL
        message = f"Critical response time: {response_time:.3f}s"

    return ExtendedHealthCheckResult(
        name="api_response_time",
        status=status,
        message=message,
        duration=response_time,
        metrics={"response_time_ms": response_time * 1000}
    )

# Run the check
result = check_response_time()
print(f"{result.name}: {result.status.value} - {result.message}")
```

---

### 🌐 Example 5: Distributed Health Checks

**Scenario:** Aggregate health from multiple services.

```python
import aiohttp
import asyncio
from typing import List, Dict

class DistributedHealthChecker:
    """Check health across multiple services."""

    def __init__(self, service_urls: List[str]):
        self.service_urls = service_urls

    async def check_service(self, url: str) -> Dict:
        """Check health of a single service."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/health", timeout=5) as response:
                    data = await response.json()
                    return {
                        "url": url,
                        "status": "healthy" if response.status == 200 else "unhealthy",
                        "response_time": response.headers.get("X-Response-Time", "unknown"),
                        "checks": data.get("checks", [])
                    }
        except Exception as e:
            return {
                "url": url,
                "status": "unreachable",
                "error": str(e)
            }

    async def check_all_services(self) -> List[Dict]:
        """Check all services in parallel."""
        tasks = [self.check_service(url) for url in self.service_urls]
        return await asyncio.gather(*tasks)

    async def aggregate_health(self) -> Dict:
        """Get overall system health."""
        service_healths = await self.check_all_services()

        healthy = sum(1 for s in service_healths if s["status"] == "healthy")
        total = len(service_healths)

        if healthy == total:
            overall = "healthy"
        elif healthy > total / 2:
            overall = "degraded"
        else:
            overall = "unhealthy"

        return {
            "overall_status": overall,
            "healthy_services": healthy,
            "total_services": total,
            "services": service_healths
        }

# Usage
checker = DistributedHealthChecker([
    "http://api.example.com",
    "http://auth.example.com",
    "http://db.example.com"
])

health = await checker.aggregate_health()
print(f"System Status: {health['overall_status']}")
print(f"Healthy: {health['healthy_services']}/{health['total_services']}")
```

---

## 🎯 Final Exercise: Build Your Own Health Check System

**Challenge:** Create a comprehensive health check system for a web application.

**Requirements:**
1. ✅ Check database connectivity (PostgreSQL)
2. ✅ Check Redis cache availability
3. ✅ Check external API dependencies
4. ✅ Check disk space (warn if < 10GB free)
5. ✅ Check SSL certificate expiry (warn if < 30 days)
6. ✅ Implement retry logic for flaky checks
7. ✅ Collect and display metrics
8. ✅ Create HTTP endpoint for monitoring

**Starter Template:**

```python
import asyncio
from src.core.health_checks import HealthCheckRunner, HealthCheck, HealthStatus

# TODO: Implement these checks
def check_postgres():
    pass

async def check_redis():
    pass

async def check_external_api():
    pass

def check_disk_space():
    pass

def check_ssl_cert():
    pass

# TODO: Register all checks
runner = HealthCheckRunner()
# Your code here...

# TODO: Run checks and display results
results = await runner.run_all_checks()
# Your code here...
```

**Bonus Points:**
- Add Prometheus metrics export
- Implement custom alerting rules
- Create a dashboard with live updates
- Support graceful degradation

---

## 📚 Additional Resources

### Documentation
- **Architecture Docs:** `/home/claude/AIShell/docs/architecture/phase11-implementation-summary.md`
- **Source Code:** `/home/claude/AIShell/src/core/health_checks.py`
- **Tests:** `/home/claude/AIShell/tests/core/test_health_checks.py`

### Related Tutorials
- **02-async-patterns-tutorial.md** - Advanced async programming
- **03-textual-ui-tutorial.md** - Building TUI applications
- **04-performance-optimization-tutorial.md** - System performance tuning

### External Resources
- [Python asyncio documentation](https://docs.python.org/3/library/asyncio.html)
- [Textual framework docs](https://textual.textualize.io/)
- [Health check best practices](https://microservices.io/patterns/observability/health-check-api.html)

---

## 🏆 Summary

**You've learned:**
- ✅ What health checks are and why they matter
- ✅ How to use built-in checks (LLM, Database, Filesystem, Memory)
- ✅ Creating custom sync and async health checks
- ✅ Configuring timeouts and handling errors
- ✅ Integrating health checks into startup scripts and UIs
- ✅ Troubleshooting common issues
- ✅ Performance optimization techniques
- ✅ Advanced patterns (retry logic, metrics, distributed checks)

**Key Takeaways:**
- 🚀 All checks run in parallel for maximum speed
- ⏱️ Timeouts prevent hanging operations
- 🔄 Both sync and async functions are supported
- 📊 Built-in checks cover common requirements
- 🎯 Easy to extend with custom checks

**Next Steps:**
1. Experiment with the example code
2. Build health checks for your own services
3. Integrate into your application's startup sequence
4. Set up monitoring and alerting
5. Contribute improvements back to AIShell!

---

**Happy Health Checking! 🏥✨**

*Tutorial Version: 1.0 | Last Updated: 2025-10-05*
