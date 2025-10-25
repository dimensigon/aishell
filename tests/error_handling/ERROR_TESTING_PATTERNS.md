# Error Handling and Edge Case Testing Patterns

## Overview

Comprehensive test suite for error handling, edge cases, and chaos engineering scenarios across all AIShell modules.

**Created:** 2025-10-12
**Coverage Target:** 90%+ error path coverage
**Test Files:** 7 comprehensive test modules

## Test Suite Structure

### 1. Exception Handling Tests (`test_exception_handling.py`)

**Focus:** All exception types and error paths across modules

**Test Categories:**
- **AIShellCore Exceptions:**
  - Double initialization warnings
  - Shutdown before initialization
  - Module registration errors (missing name, duplicates)
  - Module unregistration/retrieval errors
  - Nested exception handling

- **Event Bus Exceptions:**
  - Start/stop lifecycle errors
  - Queue overflow handling
  - Critical event guarantees
  - Handler exceptions during processing
  - Events with no subscribers

- **LLM Manager Exceptions:**
  - Operations before initialization
  - Unknown provider types
  - Provider initialization failures
  - LLM generation failures
  - Invalid JSON responses
  - Query explanation/optimization failures

- **Security Error Handler:**
  - Sensitive keyword sanitization
  - Production vs debug mode behavior
  - Security error logging
  - Decorator exception handling (sync/async)

**Key Patterns:**
```python
# Test all error paths
with pytest.raises(ExpectedException, match="pattern"):
    operation_that_should_fail()

# Test graceful degradation
try:
    risky_operation()
except Exception:
    fallback_operation()
```

### 2. Timeout Tests (`test_timeouts.py`)

**Focus:** Operation timeouts and timeout recovery

**Test Categories:**
- **Event Bus Timeouts:**
  - Queue get timeout on empty queue
  - Slow handler timeouts
  - Critical events waiting for handlers
  - Handler timeout not blocking queue
  - Stop with pending events

- **LLM Timeouts:**
  - Generation timeouts
  - Blocking call timeouts
  - Embedding generation timeouts

- **Async Operation Timeouts:**
  - asyncio.wait_for timeouts
  - Task cancellation on timeout
  - Multiple concurrent timeouts
  - Timeout recovery
  - Cleanup on timeout

- **Deadline Timeouts:**
  - Deadline exceeded errors
  - Multiple operations within deadline
  - Graceful timeout degradation

- **Resource Timeouts:**
  - Lock acquisition timeouts
  - Semaphore timeouts
  - Queue put/get timeouts

**Key Patterns:**
```python
# Timeout with cleanup
with pytest.raises(asyncio.TimeoutError):
    await asyncio.wait_for(slow_operation(), timeout=0.1)

# Graceful degradation
for attempt in range(max_retries):
    try:
        await asyncio.wait_for(operation(), timeout=get_timeout(attempt))
        break
    except asyncio.TimeoutError:
        if attempt == max_retries - 1:
            return partial_results()
```

### 3. Network Failure Tests (`test_network_failures.py`)

**Focus:** Network errors and recovery strategies

**Test Categories:**
- **Connection Failures:**
  - Connection refused
  - DNS resolution failures
  - Network unreachable
  - Connection timeouts
  - Read timeouts

- **HTTP Errors:**
  - All status codes (400, 401, 403, 404, 500, 502, 503, 504)
  - Rate limiting (429)

- **Retry Logic:**
  - Retry on connection errors
  - Exponential backoff
  - Max retries exceeded
  - Circuit breaker pattern

- **Network Partitioning:**
  - Partial network failures
  - Split-brain scenarios

- **Graceful Degradation:**
  - Fallback to cache
  - Degraded mode operation
  - Partial results on timeout

- **Socket Errors:**
  - Connection refused
  - Socket timeout
  - Broken pipe
  - Connection reset by peer

**Key Patterns:**
```python
# Exponential backoff retry
for attempt in range(max_retries):
    try:
        return await operation()
    except ConnectionError:
        if attempt == max_retries - 1:
            raise
        delay = base_delay * (2 ** attempt)
        await asyncio.sleep(delay)

# Circuit breaker
if circuit_open:
    raise Exception("Circuit breaker open")
if failures >= threshold:
    circuit_open = True
```

### 4. Data Corruption Tests (`test_data_corruption.py`)

**Focus:** Data corruption detection and recovery

**Test Categories:**
- **JSON Corruption:**
  - Invalid syntax
  - Truncated files
  - Null bytes
  - Invalid encoding
  - Malformed recovery
  - Nested corruption

- **Pickle Corruption:**
  - Corrupted data
  - Protocol version mismatch
  - Modified class definitions

- **File Corruption:**
  - Empty files
  - Binary instead of text
  - Truncated writes
  - Control characters
  - Broken symlinks

- **Data Validation:**
  - Checksum mismatches
  - Schema validation
  - Missing required fields
  - Type corruption
  - Circular references

- **Recovery Mechanisms:**
  - Backup file recovery
  - Incremental backups
  - Transaction log replay
  - Partial data recovery
  - Data repair attempts

- **Database Corruption:**
  - Corrupted SQLite databases
  - Concurrent write corruption

**Key Patterns:**
```python
# Backup recovery
try:
    data = load_main_file()
except CorruptionError:
    if backup_exists():
        data = load_backup()
        restore_main_file(data)

# Checksum validation
actual = hashlib.sha256(data).hexdigest()
if actual != expected:
    raise CorruptionError("Checksum mismatch")
```

### 5. Resource Exhaustion Tests (`test_resource_exhaustion.py`)

**Focus:** Resource limits and exhaustion scenarios

**Test Categories:**
- **Memory Exhaustion:**
  - Large allocations
  - Memory leak detection
  - Recursive depth exhaustion
  - Generator efficiency
  - Circular reference cleanup
  - Memory limits

- **File Descriptor Exhaustion:**
  - Descriptor leaks
  - Context manager prevention
  - Maximum open files
  - Async file management

- **Connection Pool Exhaustion:**
  - Pool limits
  - Connection leaks
  - Timeout on exhaustion
  - Error handling

- **Disk Space Exhaustion:**
  - Disk full errors
  - Large file writes
  - Available space checks
  - Temp file cleanup
  - Atomic write failures

- **Thread/Task Pool Exhaustion:**
  - Task semaphore limits
  - Queue overflow
  - Worker pool exhaustion
  - Asyncio task limits

- **Buffer Overflow:**
  - String buffers
  - Bytearray overflow
  - Fixed-size buffers
  - Queue size limits

- **Resource Cleanup:**
  - Context managers
  - Finally blocks
  - Weakref cleanup

**Key Patterns:**
```python
# Semaphore limiting
semaphore = asyncio.Semaphore(max_concurrent)

async with semaphore:
    await resource_intensive_operation()

# Resource cleanup
try:
    resource = acquire()
    use(resource)
finally:
    release(resource)
```

### 6. Race Condition Tests (`test_race_conditions.py`)

**Focus:** Concurrent access and synchronization issues

**Test Categories:**
- **Basic Races:**
  - Counter race conditions
  - Counter with proper locking
  - Async race conditions
  - Async with locks

- **Check-Then-Act Races:**
  - File existence checks
  - Dictionary check-then-act
  - Proper synchronization

- **Deadlocks:**
  - Simple deadlock detection
  - Async deadlock avoidance
  - Ordered lock acquisition

- **Data Races:**
  - List append races
  - Concurrent dict modification
  - Concurrent read-write

- **Lost Update Problem:**
  - Lost update races
  - Prevention with locks

- **Event Bus Races:**
  - Subscribe during publish
  - Unsubscribe during dispatch

- **Concurrent Initialization:**
  - Double initialization
  - Lazy initialization races
  - Lazy init with locks

- **Concurrent Modification:**
  - Dict modification during iteration
  - List modification during iteration
  - Concurrent collection access

- **Memory Visibility:**
  - Volatile variable simulation
  - Async memory visibility

**Key Patterns:**
```python
# Prevent race with lock
async with lock:
    if condition_check():
        modify_state()

# Ordered lock acquisition (prevent deadlock)
locks_sorted = sorted([lock1, lock2], key=id)
for lock in locks_sorted:
    await lock.acquire()
```

### 7. Edge Case Tests (`test_edge_cases.py`)

**Focus:** Boundary conditions and unusual inputs

**Test Categories:**
- **Null and Empty:**
  - None values
  - Empty strings
  - Empty collections
  - None in event data
  - Empty LLM inputs

- **Boundary Values:**
  - Integer boundaries (sys.maxsize)
  - Float boundaries (inf, -inf, nan)
  - String length boundaries
  - List size boundaries
  - Event priority boundaries
  - Off-by-one errors

- **Unicode Edge Cases:**
  - Various unicode characters (ASCII, Latin, Chinese, Arabic, Emoji)
  - Zero-width characters
  - Unicode normalization
  - Invalid UTF-8
  - Surrogate pairs
  - Right-to-left text

- **Numeric Edge Cases:**
  - Division by zero
  - Negative zero
  - Floating point precision
  - Very small numbers
  - Numeric overflow

- **Collection Edge Cases:**
  - Unusual dict keys (None, 0, False, empty tuple)
  - Dict insertion order
  - Set operations
  - Nested collections
  - Circular references

- **Async Edge Cases:**
  - Empty gather
  - Gather with None
  - Zero/negative sleep
  - Cancelled tasks
  - Double await

- **Path Edge Cases:**
  - Empty path
  - Root path
  - Current/parent directory
  - Special characters

- **Error Message Edge Cases:**
  - Very long messages
  - Unicode in messages
  - Empty messages

**Key Patterns:**
```python
# Test boundary conditions
test_cases = [
    (min_value, expected_result),
    (min_value + 1, expected_result),
    (max_value - 1, expected_result),
    (max_value, expected_result),
]

for input_val, expected in test_cases:
    assert function(input_val) == expected

# Handle None/empty safely
value = input_value if input_value is not None else default_value
```

## Testing Principles

### 1. Chaos Engineering
- Test what happens when things go wrong
- Simulate real-world failures
- Verify graceful degradation

### 2. Error Path Coverage
- Every exception handler tested
- Every timeout scenario covered
- Every recovery mechanism verified

### 3. Boundary Testing
- Test at the edges of valid input
- Test one beyond the edge
- Test special values (0, None, empty, infinity)

### 4. Concurrency Testing
- Test race conditions
- Test deadlocks
- Test proper synchronization

### 5. Recovery Testing
- Test recovery from errors
- Test cleanup on failure
- Test retry mechanisms

## Usage

### Run All Error Tests
```bash
pytest tests/error_handling/ -v
```

### Run Specific Test Category
```bash
pytest tests/error_handling/test_exception_handling.py -v
pytest tests/error_handling/test_timeouts.py -v
pytest tests/error_handling/test_network_failures.py -v
pytest tests/error_handling/test_data_corruption.py -v
pytest tests/error_handling/test_resource_exhaustion.py -v
pytest tests/error_handling/test_race_conditions.py -v
pytest tests/error_handling/test_edge_cases.py -v
```

### Run Specific Test
```bash
pytest tests/error_handling/test_exception_handling.py::TestAIShellCoreExceptions::test_register_module_without_name -v
```

### Run with Coverage
```bash
pytest tests/error_handling/ --cov=src --cov-report=html
```

## Test Statistics

- **Total Test Files:** 7
- **Test Classes:** 50+
- **Individual Tests:** 200+
- **Lines of Test Code:** ~3,500
- **Coverage Focus:** Error paths and edge cases
- **Target Coverage:** 90%+ of error handling code

## Key Findings

### Common Error Patterns Found
1. Missing initialization checks
2. Resource leaks without proper cleanup
3. Race conditions in concurrent operations
4. Insufficient timeout handling
5. Poor error messages in production
6. Missing null/empty checks
7. Inadequate retry logic

### Recommended Improvements
1. Add timeout to all network operations
2. Implement circuit breaker pattern for external services
3. Add checksum validation for critical data
4. Improve concurrent access synchronization
5. Add resource tracking and leak detection
6. Implement exponential backoff for retries
7. Add comprehensive logging for debugging

## Integration with Swarm

All error testing patterns stored in swarm memory:
- Memory key: `swarm/tester/error-testing-patterns`
- Accessible to other agents for coordination
- Updated with each test run

## Future Enhancements

1. **Property-Based Testing:** Use Hypothesis for generating edge cases
2. **Fault Injection:** Automated fault injection during integration tests
3. **Performance Under Load:** Test error handling with high load
4. **Recovery Time Testing:** Measure time to recover from failures
5. **Distributed System Testing:** Test network partitions and consistency
6. **Security Testing:** SQL injection, XSS, and other security vectors
