# AI-Shell Hands-On Tutorial - Part 1: Getting Started & Database Basics

**Level:** Beginner
**Duration:** 30-45 minutes
**Prerequisites:** Basic Python knowledge, access to a database (PostgreSQL, MySQL, or Oracle)

---

## Table of Contents
1. [Installation and Setup](#installation-and-setup)
2. [Database Connections](#database-connections)
3. [Basic Query Execution](#basic-query-execution)
4. [Health Checks](#health-checks)
5. [Connection Management](#connection-management)
6. [Error Handling](#error-handling)
7. [Validation Checkpoints](#validation-checkpoints)
8. [Troubleshooting](#troubleshooting)

---

## 1. Installation and Setup

### Step 1.1: Install AI-Shell

```bash
# Install from PyPI (recommended)
pip install ai-shell

# Or install from source
git clone https://github.com/yourusername/ai-shell.git
cd ai-shell
pip install -e .
```

**Expected Output:**
```
Successfully installed ai-shell-2.0.0
Successfully installed sqlalchemy-2.0.23 asyncpg-0.29.0 ...
```

### Step 1.2: Verify Installation

```bash
# Check version
ai-shell --version

# Check available commands
ai-shell --help
```

**Expected Output:**
```
AI-Shell version 2.0.0
Usage: ai-shell [OPTIONS] COMMAND [ARGS]...

Commands:
  connect    Connect to database
  query      Execute queries
  health     Check database health
  ...
```

### Step 1.3: Set Up Configuration

Create a configuration file at `~/.ai-shell/config.yaml`:

```yaml
# Default database settings
default_database: postgres

# Database connections
databases:
  postgres:
    type: postgresql
    host: localhost
    port: 5432
    database: demo_db
    username: demo_user
    password: ${POSTGRES_PASSWORD}  # Use environment variable

  mysql:
    type: mysql
    host: localhost
    port: 3306
    database: demo_db
    username: demo_user
    password: ${MYSQL_PASSWORD}

# Logging
logging:
  level: INFO
  file: ~/.ai-shell/logs/ai-shell.log

# Security
security:
  enable_rbac: true
  audit_log: true
  max_query_time: 30
```

### Step 1.4: Set Environment Variables

```bash
# Linux/Mac
export POSTGRES_PASSWORD="your_secure_password"
export MYSQL_PASSWORD="your_mysql_password"

# Windows
set POSTGRES_PASSWORD=your_secure_password
set MYSQL_PASSWORD=your_mysql_password
```

### ✅ Checkpoint 1: Verify Setup
```bash
# Test configuration load
ai-shell config validate

# Expected: "Configuration valid ✓"
```

---

## 2. Database Connections

### Step 2.1: Connect to PostgreSQL

**Example 1: Basic Connection**

```python
from ai_shell import DatabaseConnector

# Initialize connector
connector = DatabaseConnector(
    db_type="postgresql",
    host="localhost",
    port=5432,
    database="demo_db",
    username="demo_user",
    password="your_password"
)

# Connect
await connector.connect()
print(f"Connected: {connector.is_connected()}")
```

**Expected Output:**
```
Connecting to PostgreSQL database...
Connection established successfully
Connected: True
```

**Example 2: Connection with Connection Pool**

```python
from ai_shell import DatabaseConnector

# Connect with pool settings
connector = DatabaseConnector(
    db_type="postgresql",
    host="localhost",
    database="demo_db",
    username="demo_user",
    password="your_password",
    pool_size=10,
    max_overflow=20,
    pool_timeout=30
)

await connector.connect()

# Check pool status
pool_status = await connector.get_pool_status()
print(f"Pool size: {pool_status['size']}")
print(f"Active connections: {pool_status['active']}")
print(f"Idle connections: {pool_status['idle']}")
```

**Expected Output:**
```
Pool size: 10
Active connections: 1
Idle connections: 9
```

### Step 2.2: Connect to MySQL

```python
from ai_shell import DatabaseConnector

# MySQL connection
mysql_connector = DatabaseConnector(
    db_type="mysql",
    host="localhost",
    port=3306,
    database="demo_db",
    username="demo_user",
    password="your_password",
    charset="utf8mb4"
)

await mysql_connector.connect()
print(f"MySQL Connected: {mysql_connector.is_connected()}")
```

**Expected Output:**
```
Connecting to MySQL database...
Connection established successfully
MySQL Connected: True
```

### Step 2.3: Connect to Oracle

```python
from ai_shell import DatabaseConnector

# Oracle connection
oracle_connector = DatabaseConnector(
    db_type="oracle",
    host="localhost",
    port=1521,
    service_name="XEPDB1",  # Or use sid="XE"
    username="demo_user",
    password="your_password"
)

await oracle_connector.connect()
print(f"Oracle Connected: {oracle_connector.is_connected()}")
```

**Expected Output:**
```
Connecting to Oracle database...
Connection established successfully
Oracle Connected: True
```

### Step 2.4: Connection String Method

```python
from ai_shell import DatabaseConnector

# Using connection strings
postgres_url = "postgresql://demo_user:password@localhost:5432/demo_db"
connector = DatabaseConnector.from_url(postgres_url)
await connector.connect()

mysql_url = "mysql://demo_user:password@localhost:3306/demo_db"
mysql_conn = DatabaseConnector.from_url(mysql_url)
await mysql_conn.connect()
```

### ✅ Checkpoint 2: Verify Connections
```python
# Test all connections
connectors = {
    "PostgreSQL": postgres_connector,
    "MySQL": mysql_connector,
    "Oracle": oracle_connector
}

for name, conn in connectors.items():
    status = "✓" if conn.is_connected() else "✗"
    print(f"{name}: {status}")
```

**Expected Output:**
```
PostgreSQL: ✓
MySQL: ✓
Oracle: ✓
```

---

## 3. Basic Query Execution

### Step 3.1: Simple SELECT Query

```python
from ai_shell import QueryExecutor

# Initialize executor
executor = QueryExecutor(connector)

# Execute simple query
result = await executor.execute(
    "SELECT * FROM users LIMIT 5"
)

print(f"Rows returned: {len(result.rows)}")
print(f"Columns: {result.columns}")
print(f"Execution time: {result.execution_time}ms")

# Display results
for row in result.rows:
    print(row)
```

**Expected Output:**
```
Rows returned: 5
Columns: ['id', 'name', 'email', 'created_at']
Execution time: 23ms

{'id': 1, 'name': 'John Doe', 'email': 'john@example.com', 'created_at': '2024-01-15'}
{'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com', 'created_at': '2024-01-16'}
...
```

### Step 3.2: Parameterized Queries

```python
# Safe parameterized query
query = "SELECT * FROM users WHERE email = :email"
params = {"email": "john@example.com"}

result = await executor.execute(query, params)

print(f"Found {len(result.rows)} user(s)")
for row in result.rows:
    print(f"User: {row['name']}, Email: {row['email']}")
```

**Expected Output:**
```
Found 1 user(s)
User: John Doe, Email: john@example.com
```

### Step 3.3: INSERT Operations

```python
# Insert new user
insert_query = """
INSERT INTO users (name, email, created_at)
VALUES (:name, :email, :created_at)
RETURNING id
"""

params = {
    "name": "Alice Johnson",
    "email": "alice@example.com",
    "created_at": "2024-10-11"
}

result = await executor.execute(insert_query, params)
new_id = result.rows[0]['id']
print(f"New user created with ID: {new_id}")
```

**Expected Output:**
```
New user created with ID: 123
```

### Step 3.4: UPDATE Operations

```python
# Update user email
update_query = """
UPDATE users
SET email = :new_email
WHERE id = :user_id
"""

params = {
    "new_email": "alice.j@example.com",
    "user_id": 123
}

result = await executor.execute(update_query, params)
print(f"Rows updated: {result.row_count}")
```

**Expected Output:**
```
Rows updated: 1
```

### Step 3.5: Batch Operations

```python
# Batch insert
users_data = [
    {"name": "Bob Wilson", "email": "bob@example.com"},
    {"name": "Carol White", "email": "carol@example.com"},
    {"name": "David Brown", "email": "david@example.com"}
]

insert_query = "INSERT INTO users (name, email) VALUES (:name, :email)"

result = await executor.execute_batch(insert_query, users_data)
print(f"Inserted {result.row_count} users")
```

**Expected Output:**
```
Inserted 3 users
```

### ✅ Checkpoint 3: Verify Query Execution
```python
# Verify all operations worked
verify_query = "SELECT COUNT(*) as total FROM users"
result = await executor.execute(verify_query)
print(f"Total users in database: {result.rows[0]['total']}")

# Expected: At least 8 users (5 original + 3 new)
```

---

## 4. Health Checks

### Step 4.1: Basic Health Check

```python
from ai_shell import HealthCheck

# Initialize health checker
health = HealthCheck(connector)

# Run basic health check
status = await health.check()

print(f"Database Status: {status.status}")  # healthy, degraded, unhealthy
print(f"Response Time: {status.response_time}ms")
print(f"Connection Pool: {status.pool_status}")
```

**Expected Output:**
```
Database Status: healthy
Response Time: 12ms
Connection Pool: {'active': 2, 'idle': 8, 'total': 10}
```

### Step 4.2: Comprehensive Health Check

```python
# Detailed health check with all metrics
status = await health.check_comprehensive()

print("Health Check Results:")
print(f"  Status: {status.status}")
print(f"  Database Version: {status.db_version}")
print(f"  Uptime: {status.uptime}")
print(f"  Active Connections: {status.active_connections}")
print(f"  Max Connections: {status.max_connections}")
print(f"  Database Size: {status.database_size}")
print(f"  Cache Hit Ratio: {status.cache_hit_ratio}%")
```

**Expected Output:**
```
Health Check Results:
  Status: healthy
  Database Version: PostgreSQL 14.5
  Uptime: 15 days, 3:24:15
  Active Connections: 12
  Max Connections: 100
  Database Size: 2.5 GB
  Cache Hit Ratio: 98.7%
```

### Step 4.3: Continuous Health Monitoring

```python
import asyncio

# Monitor health every 30 seconds
async def monitor_health():
    while True:
        status = await health.check()

        if status.status == "healthy":
            print(f"✓ Healthy - Response: {status.response_time}ms")
        elif status.status == "degraded":
            print(f"⚠ Degraded - Response: {status.response_time}ms")
        else:
            print(f"✗ Unhealthy - Response: {status.response_time}ms")

        await asyncio.sleep(30)

# Run monitor
await monitor_health()
```

**Expected Output:**
```
✓ Healthy - Response: 11ms
✓ Healthy - Response: 13ms
✓ Healthy - Response: 12ms
...
```

### Step 4.4: Health Check with Alerts

```python
# Set up health check with thresholds
health = HealthCheck(
    connector,
    response_time_threshold=100,  # ms
    connection_threshold=80,  # % of max
    cache_hit_threshold=90  # %
)

status = await health.check_with_alerts()

if status.alerts:
    print("⚠ Alerts detected:")
    for alert in status.alerts:
        print(f"  - {alert.severity}: {alert.message}")
else:
    print("✓ All metrics within normal range")
```

**Expected Output:**
```
✓ All metrics within normal range
```

### ✅ Checkpoint 4: Verify Health Checks
```python
# Run all health checks
results = {
    "basic": await health.check(),
    "comprehensive": await health.check_comprehensive(),
    "with_alerts": await health.check_with_alerts()
}

all_healthy = all(r.status == "healthy" for r in results.values())
print(f"All checks passed: {all_healthy}")
```

---

## 5. Connection Management

### Step 5.1: Connection Pooling

```python
from ai_shell import ConnectionPool

# Create connection pool
pool = ConnectionPool(
    db_type="postgresql",
    host="localhost",
    database="demo_db",
    username="demo_user",
    password="your_password",
    min_size=5,
    max_size=20
)

await pool.initialize()

# Get connection from pool
async with pool.acquire() as conn:
    result = await conn.execute("SELECT * FROM users LIMIT 5")
    print(f"Rows: {len(result.rows)}")

# Connection automatically returned to pool

print(f"Pool status: {await pool.get_status()}")
```

**Expected Output:**
```
Rows: 5
Pool status: {'size': 20, 'available': 19, 'in_use': 1}
```

### Step 5.2: Transaction Management

```python
from ai_shell import Transaction

# Start transaction
async with Transaction(connector) as tx:
    # Execute multiple queries in transaction
    await tx.execute(
        "INSERT INTO accounts (user_id, balance) VALUES (:user_id, :balance)",
        {"user_id": 1, "balance": 1000.00}
    )

    await tx.execute(
        "INSERT INTO transactions (account_id, amount, type) VALUES (:account_id, :amount, :type)",
        {"account_id": 1, "amount": 1000.00, "type": "deposit"}
    )

    # Transaction commits automatically if no errors
    print("Transaction committed")

# If error occurs, transaction rolls back automatically
```

**Expected Output:**
```
Transaction started
Transaction committed
```

### Step 5.3: Connection Retry Logic

```python
from ai_shell import DatabaseConnector
from ai_shell.exceptions import ConnectionError
import asyncio

# Connection with retry
connector = DatabaseConnector(
    db_type="postgresql",
    host="localhost",
    database="demo_db",
    username="demo_user",
    password="your_password",
    max_retries=3,
    retry_delay=2  # seconds
)

try:
    await connector.connect_with_retry()
    print("Connected successfully")
except ConnectionError as e:
    print(f"Failed to connect after retries: {e}")
```

**Expected Output:**
```
Attempt 1: Connecting...
Connected successfully
```

### Step 5.4: Connection Lifecycle Management

```python
# Context manager for automatic cleanup
async with DatabaseConnector.from_url(db_url) as conn:
    # Connection opened
    result = await conn.execute("SELECT 1")
    print(f"Query result: {result.rows[0]}")
    # Connection automatically closed on exit

print("Connection closed and cleaned up")
```

**Expected Output:**
```
Query result: {'?column?': 1}
Connection closed and cleaned up
```

### ✅ Checkpoint 5: Verify Connection Management
```python
# Test pool efficiency
import time

start = time.time()

# Execute 100 queries with pooling
tasks = []
for i in range(100):
    task = executor.execute("SELECT 1")
    tasks.append(task)

results = await asyncio.gather(*tasks)
elapsed = time.time() - start

print(f"100 queries executed in {elapsed:.2f}s")
print(f"Average: {elapsed*10:.2f}ms per query")
```

---

## 6. Error Handling

### Step 6.1: Connection Errors

```python
from ai_shell.exceptions import ConnectionError, AuthenticationError

try:
    connector = DatabaseConnector(
        db_type="postgresql",
        host="invalid-host",
        database="demo_db",
        username="demo_user",
        password="wrong_password"
    )
    await connector.connect()
except ConnectionError as e:
    print(f"Connection failed: {e}")
    print(f"Error code: {e.error_code}")
    print(f"Suggestion: {e.suggestion}")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
```

**Expected Output:**
```
Connection failed: Could not connect to database
Error code: CONNECTION_REFUSED
Suggestion: Check if database server is running and accessible
```

### Step 6.2: Query Errors

```python
from ai_shell.exceptions import QueryError, SyntaxError

try:
    # Invalid SQL syntax
    result = await executor.execute("SELCT * FROM users")
except SyntaxError as e:
    print(f"SQL Syntax Error: {e}")
    print(f"Position: {e.position}")
    print(f"Suggestion: {e.suggestion}")

try:
    # Table doesn't exist
    result = await executor.execute("SELECT * FROM non_existent_table")
except QueryError as e:
    print(f"Query Error: {e}")
    print(f"Query: {e.query}")
```

**Expected Output:**
```
SQL Syntax Error: syntax error at or near "SELCT"
Position: 0
Suggestion: Did you mean 'SELECT'?
```

### Step 6.3: Timeout Handling

```python
from ai_shell.exceptions import TimeoutError

try:
    # Set query timeout
    executor.set_timeout(5)  # 5 seconds

    # Long-running query
    result = await executor.execute("""
        SELECT pg_sleep(10);  -- Sleeps for 10 seconds
    """)
except TimeoutError as e:
    print(f"Query timed out: {e}")
    print(f"Timeout limit: {e.timeout_seconds}s")
    print(f"Elapsed: {e.elapsed_time}s")
```

**Expected Output:**
```
Query timed out: Query execution exceeded timeout limit
Timeout limit: 5s
Elapsed: 5.01s
```

### Step 6.4: Transaction Errors with Rollback

```python
from ai_shell import Transaction
from ai_shell.exceptions import TransactionError

try:
    async with Transaction(connector) as tx:
        await tx.execute(
            "INSERT INTO accounts (user_id, balance) VALUES (1, 500)"
        )

        # This will fail - duplicate key
        await tx.execute(
            "INSERT INTO accounts (user_id, balance) VALUES (1, 500)"
        )
except TransactionError as e:
    print(f"Transaction failed and rolled back: {e}")
    print("All changes reverted")
```

**Expected Output:**
```
Transaction failed and rolled back: duplicate key value violates unique constraint
All changes reverted
```

### Step 6.5: Graceful Error Recovery

```python
from ai_shell import ErrorHandler

# Set up error handler
handler = ErrorHandler()

@handler.with_retry(max_attempts=3, backoff=2)
async def execute_with_retry(query):
    return await executor.execute(query)

# Execute with automatic retry
try:
    result = await execute_with_retry("SELECT * FROM users")
    print(f"Success: {len(result.rows)} rows")
except Exception as e:
    print(f"Failed after 3 attempts: {e}")
```

**Expected Output:**
```
Success: 5 rows
```

### ✅ Checkpoint 6: Verify Error Handling
```python
# Test error handling scenarios
error_tests = {
    "connection": test_connection_error,
    "syntax": test_syntax_error,
    "timeout": test_timeout_error,
    "transaction": test_transaction_error
}

for name, test in error_tests.items():
    try:
        await test()
        print(f"✓ {name} error handled correctly")
    except Exception as e:
        print(f"✗ {name} error handling failed: {e}")
```

---

## 7. Validation Checkpoints

### Complete Setup Validation

```python
from ai_shell import SystemValidator

# Run complete validation
validator = SystemValidator()
results = await validator.validate_all()

print("\n=== AI-Shell Setup Validation ===\n")

for check, status in results.items():
    icon = "✓" if status.passed else "✗"
    print(f"{icon} {check}: {status.message}")
    if not status.passed:
        print(f"   Fix: {status.suggestion}")

print(f"\nOverall Status: {'PASS' if results.all_passed() else 'FAIL'}")
```

**Expected Output:**
```
=== AI-Shell Setup Validation ===

✓ Installation: AI-Shell 2.0.0 installed
✓ Configuration: Config file valid
✓ Database Connection: Connected to PostgreSQL
✓ Query Execution: Queries executing successfully
✓ Health Checks: Database healthy
✓ Connection Pool: Pool operating normally
✓ Error Handling: Error handlers configured

Overall Status: PASS
```

---

## 8. Troubleshooting

### Common Issues and Solutions

#### Issue 1: Cannot Connect to Database

**Symptoms:**
```
ConnectionError: Could not connect to database
```

**Solutions:**
```bash
# Check if database is running
sudo systemctl status postgresql

# Check connection details
psql -h localhost -U demo_user -d demo_db

# Verify firewall settings
sudo ufw status

# Check PostgreSQL config
sudo cat /etc/postgresql/14/main/postgresql.conf | grep listen_addresses
```

#### Issue 2: Authentication Failed

**Symptoms:**
```
AuthenticationError: password authentication failed
```

**Solutions:**
```bash
# Reset password
sudo -u postgres psql
ALTER USER demo_user WITH PASSWORD 'new_password';

# Check pg_hba.conf
sudo cat /etc/postgresql/14/main/pg_hba.conf

# Should have line like:
# host    all    all    127.0.0.1/32    md5
```

#### Issue 3: Module Not Found

**Symptoms:**
```
ModuleNotFoundError: No module named 'ai_shell'
```

**Solutions:**
```bash
# Reinstall AI-Shell
pip uninstall ai-shell
pip install ai-shell

# Check Python path
python -c "import sys; print(sys.path)"

# Verify installation
pip show ai-shell
```

#### Issue 4: Slow Query Performance

**Symptoms:**
```
Query execution time: 5000ms
```

**Solutions:**
```python
# Enable query analysis
executor.enable_explain = True
result = await executor.execute("SELECT * FROM large_table")

# Check execution plan
print(result.explain_plan)

# Add indexes
await executor.execute("""
    CREATE INDEX idx_users_email ON users(email)
""")
```

#### Issue 5: Connection Pool Exhausted

**Symptoms:**
```
PoolError: Connection pool exhausted
```

**Solutions:**
```python
# Increase pool size
pool = ConnectionPool(
    max_size=50,  # Increase from 20
    max_overflow=30
)

# Check for connection leaks
status = await pool.get_status()
print(f"Stale connections: {status['stale']}")

# Close idle connections
await pool.cleanup_idle(timeout=300)
```

---

## Next Steps

Congratulations! You've completed Part 1 of the AI-Shell tutorial. You now know how to:

- ✓ Install and configure AI-Shell
- ✓ Connect to multiple database types
- ✓ Execute basic queries safely
- ✓ Monitor database health
- ✓ Manage connections efficiently
- ✓ Handle errors gracefully

**Continue to Part 2:** [NLP & Query Features](HANDS_ON_PART2_QUERIES.md) to learn:
- Natural language to SQL conversion
- Query optimization techniques
- Performance monitoring
- Advanced query patterns

---

## Quick Reference

### Essential Commands

```python
# Connect to database
connector = DatabaseConnector.from_url(db_url)
await connector.connect()

# Execute query
executor = QueryExecutor(connector)
result = await executor.execute(query, params)

# Health check
health = HealthCheck(connector)
status = await health.check()

# Transaction
async with Transaction(connector) as tx:
    await tx.execute(query)

# Close connection
await connector.close()
```

### Useful Snippets

```python
# Connection string formats
postgresql_url = "postgresql://user:pass@host:5432/db"
mysql_url = "mysql://user:pass@host:3306/db"
oracle_url = "oracle://user:pass@host:1521/service"

# Check if connected
if connector.is_connected():
    print("Connected")

# Get database info
info = await connector.get_database_info()
print(f"DB: {info['name']}, Version: {info['version']}")
```

---

## Resources

- **Documentation:** https://ai-shell.readthedocs.io
- **GitHub:** https://github.com/yourusername/ai-shell
- **Support:** support@ai-shell.io
- **Community:** https://discord.gg/ai-shell

---

**Time to Complete:** 30-45 minutes
**Difficulty:** Beginner
**Next Tutorial:** Part 2 - NLP & Query Features
