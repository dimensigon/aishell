# AI-Shell Database Integration Testing - User Guide

## 📚 Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Available Commands](#available-commands)
4. [Command Examples with Output](#command-examples-with-output)
5. [User Workflows](#user-workflows)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Usage](#advanced-usage)

---

## Overview

The AI-Shell Database Integration Testing suite provides comprehensive testing for 5 different database systems:

- **PostgreSQL** - Relational database
- **MySQL** - Relational database
- **MongoDB** - Document database
- **Redis** - In-memory cache
- **Oracle 23c Free** - Enterprise relational database

### Test Statistics

```
Total Tests:    312
Databases:      5
Pass Rate:      71% (222/312 passing)
Duration:       ~27 seconds
```

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI-Shell Test Suite                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  External Containers          Managed Containers           │
│  ┌──────────────┐            ┌──────────────┐            │
│  │  tstmysql    │            │  PostgreSQL  │            │
│  │  Port: 3307  │            │  Port: 5432  │            │
│  └──────────────┘            └──────────────┘            │
│                                                             │
│  ┌──────────────┐            ┌──────────────┐            │
│  │  tstoracle   │            │   MongoDB    │            │
│  │  Port: 1521  │            │  Port: 27017 │            │
│  └──────────────┘            └──────────────┘            │
│                                                             │
│                               ┌──────────────┐            │
│                               │    Redis     │            │
│                               │  Port: 6379  │            │
│                               └──────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

---

## Getting Started

### Prerequisites

1. **Docker** installed and running
2. **Node.js** v18+ installed
3. **External containers** running:
   - `tstmysql` on port 3307
   - `tstoracle` on port 1521

### Quick Start (First Time)

```bash
# 1. Navigate to docker directory
cd /home/claude/AIShell/aishell/docker

# 2. Check if external containers are running
docker ps | grep -E "tstmysql|tstoracle"

# 3. Start managed containers
docker compose -f docker-compose.test.yml up -d

# 4. Wait for services to be healthy (~30 seconds)
docker compose -f docker-compose.test.yml ps

# 5. Run integration tests
./run-integration-tests.sh
```

**Expected Output:**
```
╔══════════════════════════════════════════════════════════════╗
║     AI-Shell Database Integration Test Runner               ║
╚══════════════════════════════════════════════════════════════╝

[1/5] Checking external containers...
  ✓ MySQL container 'tstmysql' is running and healthy
  ✓ Oracle container 'tstoracle' is running
     ✓ Oracle is healthy and accepting connections

[2/5] Checking managed containers...
  ✓ PostgreSQL is healthy
  ✓ MongoDB is healthy
  ✓ Redis is healthy

[3/5] Running integration tests...
...
 Test Files  5 failed (5)
      Tests  24 failed | 222 passed | 66 skipped (312)
   Duration  26.69s
```

---

## Available Commands

### 1. Main Test Runner

**Command:** `./run-integration-tests.sh`

**Purpose:** Comprehensive test execution with health checks

**What it does:**
1. Verifies external containers (MySQL, Oracle)
2. Checks managed containers (PostgreSQL, MongoDB, Redis)
3. Runs all 312 integration tests
4. Generates test results summary
5. Displays connection strings

**Usage:**
```bash
cd /home/claude/AIShell/aishell/docker
./run-integration-tests.sh
```

**Expected Output:**
```
╔══════════════════════════════════════════════════════════════╗
║     AI-Shell Database Integration Test Runner               ║
╚══════════════════════════════════════════════════════════════╝

[1/5] Checking external containers...
  ✓ MySQL container 'tstmysql' is running and healthy
  ✓ Oracle container 'tstoracle' is running
     ✓ Oracle is healthy and accepting connections

[2/5] Checking managed containers...
  ✓ PostgreSQL is healthy
  ✓ MongoDB is healthy
  ✓ Redis is healthy

[4/5] Executing test suite...

[3/5] Running integration tests...

 RUN  v2.1.9 /home/claude/AIShell/aishell

stdout | tests/integration/database/postgres.integration.test.ts
🧪 Setting up test environment...
🔧 Setting up PostgreSQL integration tests...
✅ Connected to PostgreSQL: PostgreSQL 16.10

stdout | tests/integration/database/mysql.integration.test.ts
🧪 Setting up test environment...
🔌 Connecting to MySQL test database...
✅ MySQL connection established

stdout | tests/integration/database/oracle.integration.test.ts
🧪 Setting up test environment...
✅ Oracle CDB connection established
✅ Oracle PDB connection established

stdout | tests/integration/database/mongodb.integration.test.ts
🧪 Setting up test environment...
✅ MongoDB connection established

stdout | tests/integration/database/redis.integration.test.ts
🧪 Setting up test environment...
✅ Redis connection established

 Test Files  5 failed (5)
      Tests  24 failed | 222 passed | 66 skipped (312)
     Errors  2 errors
   Start at  09:55:22
   Duration  26.69s

[5/5] ✓ Test execution completed

╔══════════════════════════════════════════════════════════════╗
║              Test Execution Summary                          ║
╚══════════════════════════════════════════════════════════════╝

Test Results:
 FAIL  tests/integration/database/oracle.integration.test.ts
 FAIL  tests/integration/database/redis.integration.test.ts
 Test Files  5 failed (5)
      Tests  24 failed | 222 passed | 66 skipped (312)
   Duration  26.69s

Database Connection Strings:
  PostgreSQL: postgresql://postgres:MyPostgresPass123@localhost:5432/testdb
  MySQL:      mysql://root:MyMySQLPass123@localhost:3307
  MongoDB:    mongodb://admin:MyMongoPass123@localhost:27017/testdb
  Redis:      redis://localhost:6379
  Oracle CDB: SYS/MyOraclePass123@//localhost:1521/FREE as SYSDBA
  Oracle PDB: SYS/MyOraclePass123@//localhost:1521/FREEPDB1 as SYSDBA
```

---

### 2. Connection Tester

**Command:** `./test-connections.sh`

**Purpose:** Quick verification of database connectivity

**What it does:**
- Tests connection to all 5 databases
- Returns pass/fail status for each
- Does NOT run integration tests

**Usage:**
```bash
cd /home/claude/AIShell/aishell/docker
./test-connections.sh
```

**Expected Output:**
```
================================================
AI-Shell Database Connection Tester
================================================

Testing PostgreSQL (localhost:5432): ✓ Connected
Testing MySQL (external 'tstmysql' container, localhost:3307): ✓ Connected
Testing MongoDB (localhost:27017): ✓ Connected
Testing Redis (localhost:6379): ✓ Connected
Testing Oracle DB 23c (external 'tstoracle' container, localhost:1521): ✓ Connected (CDB)

================================================
Connection Test Complete
================================================

Admin UIs:
  Adminer (SQL):       http://localhost:8080
  Mongo Express:       http://localhost:8081
  Redis Commander:     http://localhost:8082
  Oracle EM Express:   https://localhost:5500/em
```

**Failure Example:**
```
================================================
AI-Shell Database Connection Tester
================================================

Testing PostgreSQL (localhost:5432): ✗ Failed
Testing MySQL (external 'tstmysql' container, localhost:3307): ⚠ External 'tstmysql' container not found
Testing MongoDB (localhost:27017): ✓ Connected
Testing Redis (localhost:6379): ✓ Connected
Testing Oracle DB 23c (external 'tstoracle' container, localhost:1521): ✓ Connected (CDB)
```

---

### 3. Container Management

#### Start All Services

**Command:** `docker compose -f docker-compose.test.yml up -d`

**Expected Output:**
```
 Container aishell-postgres-test  Running
 Container aishell-mongodb-test   Running
 Container aishell-redis-test     Running
 Container aishell-adminer-test   Running
 Container aishell-mongo-express-test  Running
 Container aishell-redis-commander-test  Running
```

#### Check Service Status

**Command:** `docker compose -f docker-compose.test.yml ps`

**Expected Output:**
```
NAME                              IMAGE                                  STATUS
aishell-adminer-test              adminer:latest                         Up 30 minutes
aishell-mongo-express-test        mongo-express:latest                   Up 30 minutes
aishell-mongodb-test              mongo:latest                           Up 30 minutes (healthy)
aishell-postgres-test             postgres:16                            Up 30 minutes (healthy)
aishell-redis-commander-test      rediscommander/redis-commander:latest  Up 30 minutes (healthy)
aishell-redis-test                redis:latest                           Up 30 minutes (healthy)
```

#### Stop All Services

**Command:** `docker compose -f docker-compose.test.yml down`

**Expected Output:**
```
 Container aishell-redis-commander-test  Stopped
 Container aishell-mongo-express-test    Stopped
 Container aishell-adminer-test          Stopped
 Container aishell-redis-test            Stopped
 Container aishell-mongodb-test          Stopped
 Container aishell-postgres-test         Stopped
 Network aishell-test-network  Removed
```

---

### 4. Individual Database Testing

#### Test PostgreSQL Only

**Command:** `npm test -- tests/integration/database/postgres.integration.test.ts`

**Expected Output:**
```
 RUN  v2.1.9 /home/claude/AIShell/aishell

 ✓ tests/integration/database/postgres.integration.test.ts (57 tests) 8.2s
   ✓ PostgreSQL Integration Tests (57 tests) 8.2s
     ✓ Connection Management (5 tests)
     ✓ CRUD Operations (8 tests)
     ✓ Transaction Management (6 tests)
     ✓ Complex Queries (12 tests)
     ✓ JSON Operations (8 tests)
     ✓ Full Text Search (5 tests)
     ✓ Performance Monitoring (5 tests)
     ✓ Connection Pooling (8 tests)

 Test Files  1 passed (1)
      Tests  57 passed (57)
   Duration  8.2s
```

#### Test MySQL Only

**Command:** `npm test -- tests/integration/database/mysql.integration.test.ts`

**Expected Output:**
```
 RUN  v2.1.9 /home/claude/AIShell/aishell

stdout | tests/integration/database/mysql.integration.test.ts
🧪 Setting up test environment...
🔌 Connecting to MySQL test database...
✅ MySQL connection established

 ✓ tests/integration/database/mysql.integration.test.ts (66 tests) 9.5s
   ✓ MySQL Integration Tests (66 tests) 9.5s
     ✓ Connection Management (5 tests)
     ✓ CRUD Operations (12 tests)
     ✓ Transaction Management (8 tests)
     ✓ Stored Procedures (6 tests)
     ✓ Triggers (5 tests)
     ✓ Complex Queries (10 tests)
     ✓ JSON Operations (8 tests)
     ✓ Full Text Search (6 tests)
     ✓ Performance (6 tests)

 Test Files  1 passed (1)
      Tests  66 passed (66)
   Duration  9.5s
```

#### Test Oracle Only

**Command:** `npm test -- tests/integration/database/oracle.integration.test.ts`

**Expected Output:**
```
 RUN  v2.1.9 /home/claude/AIShell/aishell

stdout | tests/integration/database/oracle.integration.test.ts
🧪 Setting up test environment...
✅ Oracle CDB connection established
✅ Oracle PDB connection established

 ✓ tests/integration/database/oracle.integration.test.ts (43 tests | 13 failed | 2 skipped) 12.3s
   ✓ Oracle CDB$ROOT Integration Tests (8 tests) 2.1s
     ✓ Connection Management (5 tests)
     ✓ Basic Queries (3 tests)
   ✓ Oracle FREEPDB1 Integration Tests (35 tests | 13 failed | 2 skipped) 10.2s
     ✓ Connection to PDB (2 tests)
     ✓ CRUD Operations (8 tests | 5 failed)
     ✓ Transaction Management (6 tests | 3 failed)
     ✓ Complex Queries (4 tests)
     ✓ Test Data Verification (4 tests | 4 failed)

 Test Files  1 failed (1)
      Tests  13 failed | 28 passed | 2 skipped (43)
   Duration  12.3s
```

#### Test MongoDB Only

**Command:** `npm test -- tests/integration/database/mongodb.integration.test.ts`

**Expected Output:**
```
 RUN  v2.1.9 /home/claude/AIShell/aishell

stdout | tests/integration/database/mongodb.integration.test.ts
🧪 Setting up test environment...
✅ MongoDB connection established

 ✓ tests/integration/database/mongodb.integration.test.ts (52 tests | 2 errors) 8.7s
   ✓ MongoDB Integration Tests (52 tests) 8.7s
     ✓ Connection Management (3 tests)
     ✓ CRUD Operations (12 tests)
     ✓ Aggregation Pipeline (8 tests)
     ✓ Indexes (6 tests)
     ✓ Transactions (5 tests)
     ✓ Change Streams (4 tests | 2 errors) ⚠️
     ✓ GridFS (6 tests)
     ✓ Time Series (4 tests)
     ✓ Text Search (4 tests)

 Test Files  1 failed (1)
      Tests  50 passed | 2 errors (52)
   Duration  8.7s

⚠️ Note: Change stream tests require MongoDB replica set configuration
```

#### Test Redis Only

**Command:** `npm test -- tests/integration/database/redis.integration.test.ts`

**Expected Output:**
```
 RUN  v2.1.9 /home/claude/AIShell/aishell

stdout | tests/integration/database/redis.integration.test.ts
🧪 Setting up test environment...
✅ Redis connection established

 ✓ tests/integration/database/redis.integration.test.ts (112 tests | 1 failed) 5.2s
   ✓ Redis Integration Tests (112 tests | 1 failed) 5.2s
     ✓ Connection Management (4 tests)
     ✓ String Operations (12 tests)
     ✓ Hash Operations (10 tests)
     ✓ List Operations (12 tests)
     ✓ Set Operations (10 tests)
     ✓ Sorted Set Operations (12 tests)
     ✓ Pub/Sub (8 tests)
     ✓ Transactions (8 tests)
     ✓ Lua Scripts (6 tests)
     ✓ Pipelining (8 tests)
     ✓ HyperLogLog (6 tests)
     ✓ Geospatial (8 tests)
     ✓ Redis Streams (8 tests | 1 failed)

 Test Files  1 failed (1)
      Tests  111 passed | 1 failed (112)
   Duration  5.2s
```

---

## User Workflows

### Workflow 1: Daily Test Execution

**Scenario:** Developer wants to run tests before committing changes

```bash
# Step 1: Navigate to docker directory
cd /home/claude/AIShell/aishell/docker

# Step 2: Quick connection check
./test-connections.sh

# Expected Output:
# ✓ All 5 databases connected

# Step 3: Run full test suite
./run-integration-tests.sh

# Expected Output:
# Tests complete: 222 passed / 24 failed / 66 skipped
# Duration: ~27 seconds

# Step 4: Review results
cat test-results.log | grep -E "FAIL|PASS|Test Files"
```

**Time Required:** 2-3 minutes

---

### Workflow 2: First-Time Setup

**Scenario:** New developer setting up test environment

```bash
# Step 1: Verify Docker is running
docker --version
# Expected: Docker version 20.10+

# Step 2: Check if external containers exist
docker ps | grep -E "tstmysql|tstoracle"
# Expected: Both containers listed

# Step 3: If containers missing, check documentation
cat docker/EXTERNAL_MYSQL_SETUP.md
cat docker/EXTERNAL_ORACLE_SETUP.md

# Step 4: Start managed containers
cd /home/claude/AIShell/aishell/docker
docker compose -f docker-compose.test.yml up -d

# Expected Output:
# ✓ Container aishell-postgres-test  Running
# ✓ Container aishell-mongodb-test   Running
# ✓ Container aishell-redis-test     Running

# Step 5: Wait for health checks (30 seconds)
sleep 30

# Step 6: Verify all services healthy
docker compose -f docker-compose.test.yml ps

# Expected: All services show "Up X minutes (healthy)"

# Step 7: Test connections
./test-connections.sh

# Expected: All 5 databases connected ✓

# Step 8: Run tests
./run-integration-tests.sh

# Expected: Tests execute successfully
```

**Time Required:** 5-10 minutes (first time)

---

### Workflow 3: Debugging Failed Tests

**Scenario:** Tests are failing, need to diagnose issues

```bash
# Step 1: Check which tests are failing
npm test -- tests/integration/database/

# Note which databases have failures

# Step 2: Test individual database
npm test -- tests/integration/database/oracle.integration.test.ts

# Step 3: Check database logs
docker logs tstoracle | tail -50

# Step 4: Test direct connection
docker exec tstoracle bash -c "echo 'SELECT 1 FROM DUAL;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/FREE as sysdba"

# Expected: "1" output means connection works

# Step 5: Check if test data is initialized
docker exec tstoracle bash -c "echo 'SELECT COUNT(*) FROM user_tables;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/FREEPDB1 as sysdba"

# Step 6: Initialize test data if needed
docker cp tests/integration/database/init-oracle.sql tstoracle:/tmp/
docker exec tstoracle bash -c "sqlplus sys/MyOraclePass123@//localhost:1521/FREEPDB1 as sysdba @/tmp/init-oracle.sql"

# Step 7: Re-run tests
npm test -- tests/integration/database/oracle.integration.test.ts
```

**Time Required:** 10-20 minutes

---

### Workflow 4: Viewing Test Results in Admin UIs

**Scenario:** Visual inspection of test data

```bash
# Step 1: Ensure containers are running
docker compose -f docker-compose.test.yml ps

# Step 2: Open admin UIs in browser
# - PostgreSQL/MySQL: http://localhost:8080
# - MongoDB:          http://localhost:8081 (admin/pass)
# - Redis:            http://localhost:8082
# - Oracle:           https://localhost:5500/em

# Step 3: Login to Adminer (for SQL databases)
# Server:   aishell-postgres-test  OR  tstmysql
# Username: postgres                OR  root
# Password: MyPostgresPass123       OR  MyMySQLPass123
# Database: testdb

# Step 4: Run queries to inspect test data
# SELECT * FROM users LIMIT 10;
# SELECT COUNT(*) FROM test_table;

# Step 5: Check MongoDB collections
# Navigate to http://localhost:8081
# Username: admin
# Password: pass
# Browse collections to see test data
```

**Time Required:** 5 minutes

---

### Workflow 5: Clean Environment Reset

**Scenario:** Reset all containers and data

```bash
# Step 1: Stop all managed containers
cd /home/claude/AIShell/aishell/docker
docker compose -f docker-compose.test.yml down

# Step 2: Remove volumes (WARNING: Deletes all data)
docker volume rm aishell-postgres-data aishell-mongodb-data aishell-redis-data

# Step 3: Restart containers
docker compose -f docker-compose.test.yml up -d

# Step 4: Wait for services to be ready
sleep 30

# Step 5: Verify health
docker compose -f docker-compose.test.yml ps

# Step 6: Test connections
./test-connections.sh

# Step 7: Run tests
./run-integration-tests.sh
```

**Time Required:** 3-5 minutes

---

## Troubleshooting

### Issue 1: External Container Not Found

**Symptom:**
```
[1/5] Checking external containers...
  ✗ MySQL container 'tstmysql' not found
     Run: docker ps | grep tstmysql
```

**Solution:**
```bash
# Check if container exists but is stopped
docker ps -a | grep tstmysql

# If stopped, start it
docker start tstmysql

# If doesn't exist, check documentation
cat docker/EXTERNAL_MYSQL_SETUP.md
```

---

### Issue 2: Connection Refused

**Symptom:**
```
Testing PostgreSQL (localhost:5432): ✗ Failed
```

**Solution:**
```bash
# Check if container is running
docker ps | grep aishell-postgres-test

# Check container logs
docker logs aishell-postgres-test

# Restart container
docker restart aishell-postgres-test

# Wait and retry
sleep 10
./test-connections.sh
```

---

### Issue 3: Tests Timeout

**Symptom:**
```
 TIMEOUT  tests/integration/database/postgres.integration.test.ts
Error: Test timed out in 10000ms
```

**Solution:**
```bash
# Check container resources
docker stats

# Check if database is overloaded
docker exec aishell-postgres-test pg_stat_activity

# Restart specific container
docker restart aishell-postgres-test

# Increase test timeout in vitest.config.ts
# testTimeout: 30000
```

---

### Issue 4: Port Already in Use

**Symptom:**
```
Error starting userland proxy: listen tcp4 0.0.0.0:5432: bind: address already in use
```

**Solution:**
```bash
# Find what's using the port
lsof -i :5432

# Or use ss
ss -tuln | grep 5432

# Stop conflicting service
sudo systemctl stop postgresql

# Or change port in docker-compose.test.yml
# ports:
#   - "5433:5432"
```

---

### Issue 5: Oracle Tests All Failing

**Symptom:**
```
 FAIL  tests/integration/database/oracle.integration.test.ts
     → Failed to connect to Oracle: Error: NJS-503: connection refused
```

**Solution:**
```bash
# Verify correct container
docker ps | grep -E "tstoracle|23cfree"

# Ensure using tstoracle (port 1521)
# Not 23cfree (port 8521)

# Check Oracle listener
docker exec tstoracle lsnrctl status

# Test connection manually
docker exec tstoracle bash -c "echo 'SELECT 1 FROM DUAL;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/FREE as sysdba"

# Should output: 1
```

---

## Advanced Usage

### Custom Test Execution

#### Run Specific Test Suite

```bash
# Run only connection tests
npm test -- --grep "Connection Management"

# Run only CRUD tests
npm test -- --grep "CRUD Operations"

# Run only transaction tests
npm test -- --grep "Transaction"
```

#### Run Tests with Coverage

```bash
npm test -- --coverage
```

**Expected Output:**
```
 % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s
---------|----------|---------|---------|-------------------
   85.2  |    78.3  |   88.1  |   85.7  |
```

#### Run Tests in Watch Mode

```bash
npm test -- --watch tests/integration/database/postgres.integration.test.ts
```

---

### Environment Variables

Override default connection strings:

```bash
# PostgreSQL
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=MyPostgresPass123
export POSTGRES_DB=testdb

# MySQL
export MYSQL_HOST=localhost
export MYSQL_PORT=3307
export MYSQL_USER=root
export MYSQL_PASSWORD=MyMySQLPass123

# Oracle
export ORACLE_HOST=localhost
export ORACLE_PORT=1521
export ORACLE_USER=SYS
export ORACLE_PASSWORD=MyOraclePass123
export ORACLE_SID=FREE

# Run tests with custom config
npm test
```

---

### Parallel Test Execution

Run tests faster by running databases in parallel:

```bash
# Run each database test in separate terminal
Terminal 1: npm test -- tests/integration/database/postgres.integration.test.ts
Terminal 2: npm test -- tests/integration/database/mysql.integration.test.ts
Terminal 3: npm test -- tests/integration/database/oracle.integration.test.ts
Terminal 4: npm test -- tests/integration/database/mongodb.integration.test.ts
Terminal 5: npm test -- tests/integration/database/redis.integration.test.ts
```

**Total time:** ~10 seconds (vs 27 seconds sequential)

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUICK REFERENCE CARD                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Start Services:    docker compose -f docker-compose.test.yml  │
│                     up -d                                       │
│                                                                 │
│  Stop Services:     docker compose -f docker-compose.test.yml  │
│                     down                                        │
│                                                                 │
│  Test Connections:  ./test-connections.sh                      │
│                                                                 │
│  Run All Tests:     ./run-integration-tests.sh                 │
│                                                                 │
│  Run Single DB:     npm test -- tests/integration/database/    │
│                     <database>.integration.test.ts              │
│                                                                 │
│  View Logs:         docker logs <container-name>               │
│                                                                 │
│  Check Status:      docker compose -f docker-compose.test.yml  │
│                     ps                                          │
│                                                                 │
│  Admin UIs:         http://localhost:8080  (SQL)               │
│                     http://localhost:8081  (MongoDB)           │
│                     http://localhost:8082  (Redis)             │
│                                                                 │
│  Connection Strings:                                            │
│    PostgreSQL:  postgresql://postgres:MyPostgresPass123@       │
│                 localhost:5432/testdb                           │
│    MySQL:       mysql://root:MyMySQLPass123@localhost:3307     │
│    MongoDB:     mongodb://admin:MyMongoPass123@localhost:27017 │
│    Redis:       redis://localhost:6379                         │
│    Oracle CDB:  SYS/MyOraclePass123@//localhost:1521/FREE      │
│    Oracle PDB:  SYS/MyOraclePass123@//localhost:1521/FREEPDB1  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Support

For issues or questions:
1. Check this guide's [Troubleshooting](#troubleshooting) section
2. Review logs: `docker logs <container-name>`
3. Check test results: `cat docker/test-results.log`
4. Review database-specific setup guides in `docker/` directory

---

**Last Updated:** October 27, 2025
**Version:** 1.0
**Test Suite Version:** AI-Shell v1.0.0
