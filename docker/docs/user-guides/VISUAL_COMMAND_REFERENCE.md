# Visual Command Reference - AI-Shell Database Testing

## 🎨 Visual Command Flow Diagrams

### Complete Test Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                    USER EXECUTES: ./run-integration-tests.sh            │
│                                                                         │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
         ┌───────────────────────────────────────────────┐
         │   [1/5] Check External Containers             │
         ├───────────────────────────────────────────────┤
         │   ✓ tstmysql (port 3307)                      │
         │     - mysqladmin ping test                    │
         │   ✓ tstoracle (port 1521)                     │
         │     - SELECT 1 FROM DUAL test                 │
         └─────────────────┬─────────────────────────────┘
                           │
                           ▼
         ┌───────────────────────────────────────────────┐
         │   [2/5] Check Managed Containers              │
         ├───────────────────────────────────────────────┤
         │   ✓ PostgreSQL (port 5432)                    │
         │     - pg_isready test                         │
         │   ✓ MongoDB (port 27017)                      │
         │     - db.adminCommand('ping') test            │
         │   ✓ Redis (port 6379)                         │
         │     - redis-cli ping test                     │
         └─────────────────┬─────────────────────────────┘
                           │
                           ▼
         ┌───────────────────────────────────────────────┐
         │   [3/5] Run Integration Tests                 │
         ├───────────────────────────────────────────────┤
         │   Execute: npm test -- tests/integration/     │
         │            database/*.integration.test.ts     │
         │                                               │
         │   ┌─────────────────────────────────────┐    │
         │   │  Test Execution (Parallel)          │    │
         │   ├─────────────────────────────────────┤    │
         │   │  ┌────────────┐  ┌────────────┐    │    │
         │   │  │ PostgreSQL │  │   MySQL    │    │    │
         │   │  │ 57 tests   │  │ 66 tests   │    │    │
         │   │  └────────────┘  └────────────┘    │    │
         │   │  ┌────────────┐  ┌────────────┐    │    │
         │   │  │   Oracle   │  │  MongoDB   │    │    │
         │   │  │ 43 tests   │  │ 52 tests   │    │    │
         │   │  └────────────┘  └────────────┘    │    │
         │   │  ┌────────────┐                    │    │
         │   │  │   Redis    │                    │    │
         │   │  │ 112 tests  │                    │    │
         │   │  └────────────┘                    │    │
         │   └─────────────────────────────────────┘    │
         └─────────────────┬─────────────────────────────┘
                           │
                           ▼
         ┌───────────────────────────────────────────────┐
         │   [4/5] Generate Results                      │
         ├───────────────────────────────────────────────┤
         │   Write: docker/test-results.log              │
         │   Parse: Test statistics                      │
         │   Format: Summary output                      │
         └─────────────────┬─────────────────────────────┘
                           │
                           ▼
         ┌───────────────────────────────────────────────┐
         │   [5/5] Display Summary                       │
         ├───────────────────────────────────────────────┤
         │   ╔════════════════════════════════════════╗  │
         │   ║   Test Execution Summary              ║  │
         │   ╚════════════════════════════════════════╝  │
         │                                               │
         │   Test Files:  5 failed (5)                   │
         │   Tests:       24 failed | 222 passed         │
         │   Duration:    26.69s                         │
         │                                               │
         │   Connection Strings:                         │
         │   - PostgreSQL: postgresql://...              │
         │   - MySQL:      mysql://...                   │
         │   - MongoDB:    mongodb://...                 │
         │   - Redis:      redis://...                   │
         │   - Oracle:     SYS/...@//localhost:1521/FREE │
         └───────────────────────────────────────────────┘
```

---

## 📊 Test Execution Timeline

```
Time (seconds)
0s                    10s                   20s                   27s
├──────────────────────┼──────────────────────┼──────────────────────┤
│                      │                      │                      │
│  ┌─────────────┐    │  ┌─────────────┐    │  ┌─────────────┐    │
│  │ PostgreSQL  │────┼──│   (tests)   │────┼──│  Complete   │    │
│  │ Setup       │    │  │  8.2s       │    │  │             │    │
│  └─────────────┘    │  └─────────────┘    │  └─────────────┘    │
│                      │                      │                      │
│  ┌─────────────┐    │  ┌─────────────┐    │  ┌─────────────┐    │
│  │ MySQL       │────┼──│   (tests)   │────┼──│  Complete   │    │
│  │ Setup       │    │  │  9.5s       │    │  │             │    │
│  └─────────────┘    │  └─────────────┘    │  └─────────────┘    │
│                      │                      │                      │
│  ┌─────────────┐    │  ┌─────────────┐    │  ┌─────────────┐    │
│  │ Oracle      │────┼──│   (tests)   │────┼──│  Complete   │    │
│  │ Setup       │    │  │  12.3s      │    │  │             │    │
│  └─────────────┘    │  └─────────────┘    │  └─────────────┘    │
│                      │                      │                      │
│  ┌─────────────┐    │  ┌─────────────┐    │  ┌─────────────┐    │
│  │ MongoDB     │────┼──│   (tests)   │────┼──│  Complete   │    │
│  │ Setup       │    │  │  8.7s       │    │  │             │    │
│  └─────────────┘    │  └─────────────┘    │  └─────────────┘    │
│                      │                      │                      │
│  ┌─────────────┐    │  ┌─────────────┐    │  ┌─────────────┐    │
│  │ Redis       │────┼──│   (tests)   │────┼──│  Complete   │    │
│  │ Setup       │    │  │  5.2s       │    │  │             │    │
│  └─────────────┘    │  └─────────────┘    │  └─────────────┘    │
│                      │                      │                      │
└──────────────────────┴──────────────────────┴──────────────────────┘
   Health Checks        Test Execution        Results & Cleanup
   (2-3s)               (44s total)           (1s)
```

---

## 🗂️ Test Results Breakdown

```
┌─────────────────────────────────────────────────────────────────┐
│                     TEST RESULTS DASHBOARD                      │
│                        (312 Total Tests)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ███████████████████████████████████████████████ 71.2% Passed  │
│  ████████                                         7.7% Failed  │
│  █████████████████████                           21.1% Skipped │
│                                                                 │
│  Detailed Breakdown by Database:                               │
│                                                                 │
│  PostgreSQL (57 tests)                                          │
│  ████████████████████████████████████████████████ 96.5% ✓      │
│  ██                                               3.5% ✗        │
│  Tests: 55 passed, 2 failed                                    │
│  Time: 8.2s                                                    │
│                                                                 │
│  MySQL (66 tests)                                               │
│  ███████████████████████████████████████████████ 100% ✓        │
│  Tests: 66 passed, 0 failed                                    │
│  Time: 9.5s                                                    │
│                                                                 │
│  Oracle (43 tests)                                              │
│  ████████████████████████████████                69.8% ✓        │
│  ████████████                                    30.2% ✗        │
│  Tests: 30 passed, 13 failed, 2 skipped                        │
│  Time: 12.3s                                                   │
│                                                                 │
│  MongoDB (52 tests)                                             │
│  ████████████████████████████████████████████    96.2% ✓        │
│  ██                                               3.8% ✗        │
│  Tests: 50 passed, 2 failed                                    │
│  Time: 8.7s                                                    │
│                                                                 │
│  Redis (112 tests)                                              │
│  ████████████████████████████████████████████    99.1% ✓        │
│  █                                                0.9% ✗        │
│  Tests: 111 passed, 1 failed                                   │
│  Time: 5.2s                                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Connection Testing Flow

```
        ./test-connections.sh
                │
                ├─────────────────┬──────────────────┬─────────────┬─────────┐
                │                 │                  │             │         │
                ▼                 ▼                  ▼             ▼         ▼
        ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  ┌─────┐  ┌────────┐
        │  PostgreSQL  │  │    MySQL     │  │   MongoDB   │  │Redis│  │ Oracle │
        │              │  │              │  │             │  │     │  │        │
        │ pg_isready   │  │ mysqladmin   │  │ mongosh     │  │PING │  │ sqlplus│
        │              │  │ ping         │  │ ping        │  │     │  │ DUAL   │
        └──────┬───────┘  └──────┬───────┘  └──────┬──────┘  └──┬──┘  └───┬────┘
               │                 │                  │            │         │
               ▼                 ▼                  ▼            ▼         ▼
           ┌───────┐        ┌───────┐         ┌───────┐    ┌───────┐  ┌───────┐
           │   ✓   │        │   ✓   │         │   ✓   │    │   ✓   │  │   ✓   │
           │Success│        │Success│         │Success│    │Success│  │Success│
           └───────┘        └───────┘         └───────┘    └───────┘  └───────┘
               │                 │                  │            │         │
               └─────────────────┴──────────────────┴────────────┴─────────┘
                                         │
                                         ▼
                         ╔═══════════════════════════════╗
                         ║ All Connections Successful ✓  ║
                         ╚═══════════════════════════════╝
```

---

## 🎯 Individual Test Command Examples

### Example 1: PostgreSQL Tests

**Command:**
```bash
npm test -- tests/integration/database/postgres.integration.test.ts
```

**Visual Output:**
```
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Test Execution                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Setup Phase (2.1s)                                             │
│  ├─ Connect to database          ✓  0.5s                        │
│  ├─ Initialize test data          ✓  1.0s                        │
│  └─ Verify schema                ✓  0.6s                        │
│                                                                 │
│  Test Suites                                                    │
│  ├─ Connection Management        ✓  5/5 tests   0.8s            │
│  │  ├─ should connect            ✓  0.1s                        │
│  │  ├─ should execute query      ✓  0.2s                        │
│  │  ├─ should get version        ✓  0.1s                        │
│  │  ├─ should handle pool        ✓  0.2s                        │
│  │  └─ should disconnect         ✓  0.2s                        │
│  │                                                               │
│  ├─ CRUD Operations              ✓  8/8 tests   1.2s            │
│  │  ├─ should INSERT             ✓  0.2s                        │
│  │  ├─ should SELECT             ✓  0.1s                        │
│  │  ├─ should UPDATE             ✓  0.2s                        │
│  │  ├─ should DELETE             ✓  0.2s                        │
│  │  ├─ should handle NULL        ✓  0.1s                        │
│  │  ├─ should handle strings     ✓  0.1s                        │
│  │  ├─ should handle dates       ✓  0.2s                        │
│  │  └─ should bulk insert        ✓  0.1s                        │
│  │                                                               │
│  ├─ Transaction Management       ✓  6/6 tests   1.0s            │
│  ├─ Complex Queries              ✓ 12/12 tests  1.8s            │
│  ├─ JSON Operations              ✓  8/8 tests   0.9s            │
│  ├─ Full Text Search             ✓  5/5 tests   0.7s            │
│  ├─ Performance Monitoring       ✓  5/5 tests   0.6s            │
│  └─ Connection Pooling           ✓  8/8 tests   1.2s            │
│                                                                 │
│  Teardown Phase (0.5s)                                          │
│  ├─ Clean up test data           ✓  0.3s                        │
│  └─ Close connections            ✓  0.2s                        │
│                                                                 │
│  ═══════════════════════════════════════════════════════════   │
│  Results:  57 tests passed                                      │
│  Duration: 8.2 seconds                                          │
│  Status:   ✓ SUCCESS                                            │
│  ═══════════════════════════════════════════════════════════   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Example 2: Oracle Tests (with failures)

**Command:**
```bash
npm test -- tests/integration/database/oracle.integration.test.ts
```

**Visual Output:**
```
┌─────────────────────────────────────────────────────────────────┐
│                    Oracle Test Execution                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Setup Phase (3.2s)                                             │
│  ├─ Connect to CDB               ✓  1.0s                        │
│  ├─ Connect to PDB               ✓  1.2s                        │
│  └─ Verify connections           ✓  1.0s                        │
│                                                                 │
│  CDB$ROOT Tests                                                 │
│  ├─ Connection Management        ✓  5/5 tests   1.2s            │
│  └─ Basic Queries                ✓  3/3 tests   0.9s            │
│                                                                 │
│  FREEPDB1 Tests                                                 │
│  ├─ Connection to PDB            ✓  2/2 tests   0.5s            │
│  │                                                               │
│  ├─ CRUD Operations              ✗  3/8 tests   2.1s            │
│  │  ├─ should INSERT             ✓  0.3s                        │
│  │  ├─ should SELECT             ✓  0.2s                        │
│  │  ├─ should UPDATE             ✗  0.4s  ← Table not found    │
│  │  ├─ should DELETE             ✗  0.3s  ← Table not found    │
│  │  ├─ should bulk insert        ✗  0.4s  ← Table not found    │
│  │  ├─ should handle constraints ✓  0.2s                        │
│  │  ├─ should use sequences      ✗  0.1s  ← Sequence missing   │
│  │  └─ should use triggers       ✗  0.2s  ← Trigger missing    │
│  │                                                               │
│  ├─ Transaction Management       ✗  3/6 tests   1.8s            │
│  ├─ Complex Queries              ✓  4/4 tests   1.5s            │
│  ├─ Stored Procedures           Skip 2/2 tests  0.0s            │
│  │                                                               │
│  └─ Test Data Verification       ✗  0/4 tests   1.0s            │
│     ├─ should verify employees   ✗  0.3s  ← No test data       │
│     ├─ should verify departments ✗  0.2s  ← No test data       │
│     ├─ should verify projects    ✗  0.3s  ← No test data       │
│     └─ should verify assignments ✗  0.2s  ← No test data       │
│                                                                 │
│  Teardown Phase (0.8s)                                          │
│                                                                 │
│  ═══════════════════════════════════════════════════════════   │
│  Results:  30 passed, 13 failed, 2 skipped                      │
│  Duration: 12.3 seconds                                         │
│  Status:   ✗ PARTIAL FAILURE                                    │
│  ═══════════════════════════════════════════════════════════   │
│                                                                 │
│  ⚠️  Issue Detected: Test data not initialized                  │
│  💡 Solution: Run init-oracle.sql script                        │
│      docker cp init-oracle.sql tstoracle:/tmp/                 │
│      docker exec tstoracle sqlplus sys/...@FREEPDB1 as sysdba  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎨 Container Status Visualization

**Command:** `docker compose -f docker-compose.test.yml ps`

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Container Status Dashboard                      │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Database Containers                                                   │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Name: aishell-postgres-test                                 │    │
│  │  Image: postgres:16                                          │    │
│  │  Status: Up 45 minutes (healthy) 🟢                          │    │
│  │  Port: 0.0.0.0:5432->5432/tcp                                │    │
│  │  Health: ✓ Accepting connections                             │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Name: aishell-mongodb-test                                  │    │
│  │  Image: mongo:latest                                         │    │
│  │  Status: Up 45 minutes (healthy) 🟢                          │    │
│  │  Port: 0.0.0.0:27017->27017/tcp                              │    │
│  │  Health: ✓ Responding to pings                               │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Name: aishell-redis-test                                    │    │
│  │  Image: redis:latest                                         │    │
│  │  Status: Up 45 minutes (healthy) 🟢                          │    │
│  │  Port: 0.0.0.0:6379->6379/tcp                                │    │
│  │  Health: ✓ PONG response                                     │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                        │
│  Admin UI Containers                                                   │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Name: aishell-adminer-test                                  │    │
│  │  Image: adminer:latest                                       │    │
│  │  Status: Up 45 minutes 🟢                                    │    │
│  │  Port: 0.0.0.0:8080->8080/tcp                                │    │
│  │  Access: http://localhost:8080                               │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Name: aishell-mongo-express-test                            │    │
│  │  Image: mongo-express:latest                                 │    │
│  │  Status: Up 45 minutes 🟢                                    │    │
│  │  Port: 0.0.0.0:8081->8081/tcp                                │    │
│  │  Access: http://localhost:8081                               │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Name: aishell-redis-commander-test                          │    │
│  │  Image: rediscommander/redis-commander:latest                │    │
│  │  Status: Up 45 minutes (healthy) 🟢                          │    │
│  │  Port: 0.0.0.0:8082->8081/tcp                                │    │
│  │  Access: http://localhost:8082                               │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                        │
│  External Containers (not managed by compose)                         │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Name: tstmysql                                              │    │
│  │  Port: 0.0.0.0:3307->3306/tcp                                │    │
│  │  Status: ✓ Running and healthy                               │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Name: tstoracle                                             │    │
│  │  Port: 0.0.0.0:1521->1521/tcp                                │    │
│  │  Status: ✓ Running and healthy                               │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘

Legend:
  🟢 Healthy    🟡 Starting    🔴 Unhealthy    ⚪ Stopped
```

---

## 📈 Performance Metrics Visualization

```
┌─────────────────────────────────────────────────────────────────┐
│                  Test Performance Dashboard                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Test Execution Time by Database                               │
│                                                                 │
│  Oracle      ████████████████████████████       12.3s          │
│  MySQL       ███████████████████████             9.5s          │
│  MongoDB     ████████████████████                8.7s          │
│  PostgreSQL  ████████████████                    8.2s          │
│  Redis       ██████████                          5.2s          │
│              └────┴────┴────┴────┴────┴────┴                   │
│              0s   2s   4s   6s   8s   10s  12s                 │
│                                                                 │
│  Total Duration: 26.69s                                         │
│  Average per DB: 8.8s                                           │
│                                                                 │
│  Tests per Second                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Overall:     11.7 tests/second                         │  │
│  │  PostgreSQL:   6.9 tests/second (57 tests / 8.2s)      │  │
│  │  MySQL:        6.9 tests/second (66 tests / 9.5s)      │  │
│  │  Oracle:       3.5 tests/second (43 tests / 12.3s)     │  │
│  │  MongoDB:      6.0 tests/second (52 tests / 8.7s)      │  │
│  │  Redis:       21.5 tests/second (112 tests / 5.2s) 🏆  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎬 Animated Command Sequences

### Starting Fresh Environment

```
Step 1: Navigate to directory
$ cd /home/claude/AIShell/aishell/docker
  ✓ Changed directory

Step 2: Start services
$ docker compose -f docker-compose.test.yml up -d
  ⏳ Creating network... done
  ⏳ Creating volumes... done
  ⏳ Starting aishell-postgres-test... done
  ⏳ Starting aishell-mongodb-test... done
  ⏳ Starting aishell-redis-test... done
  ✓ All services started

Step 3: Wait for health checks (30s)
  [████████████████████████████████████] 100%
  ✓ PostgreSQL healthy
  ✓ MongoDB healthy
  ✓ Redis healthy

Step 4: Verify connections
$ ./test-connections.sh
  ✓ PostgreSQL: Connected
  ✓ MySQL: Connected
  ✓ MongoDB: Connected
  ✓ Redis: Connected
  ✓ Oracle: Connected

Step 5: Run tests
$ ./run-integration-tests.sh
  ✓ External containers verified
  ✓ Managed containers healthy
  ⏳ Running 312 tests...
  [████████████████████████████████████] 100%
  ✓ Tests complete: 222 passed, 24 failed

Total time: ~90 seconds
```

---

## 🚨 Error State Visualizations

### Container Not Running

```
┌─────────────────────────────────────────────────────────────────┐
│                         ERROR STATE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ❌ MySQL Container Check Failed                                │
│                                                                 │
│  [1/5] Checking external containers...                          │
│    ✗ MySQL container 'tstmysql' not found                       │
│       Run: docker ps | grep tstmysql                            │
│                                                                 │
│  Visual Status:                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Expected:      Actual:                                 │  │
│  │  ┌─────────┐   ┌─────────┐                             │  │
│  │  │tstmysql │   │    ❌   │                             │  │
│  │  │   🟢    │   │         │                             │  │
│  │  └─────────┘   └─────────┘                             │  │
│  │   Running       Not Found                               │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  💡 Quick Fix:                                                  │
│     1. Check if stopped: docker ps -a | grep tstmysql          │
│     2. Start container:  docker start tstmysql                 │
│     3. Verify running:   docker ps | grep tstmysql             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Test Failures

```
┌─────────────────────────────────────────────────────────────────┐
│                    TEST FAILURE ANALYSIS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ❌ Oracle Tests: 13 failures detected                          │
│                                                                 │
│  Failure Pattern Analysis:                                      │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                                                         │  │
│  │  All failures related to: "Table not found"            │  │
│  │                                                         │  │
│  │  Failed Tests:                                          │  │
│  │  ├─ CRUD Operations        [5 failures]                │  │
│  │  ├─ Transaction Management [3 failures]                │  │
│  │  ├─ Data Verification      [4 failures]                │  │
│  │  └─ Sequences & Triggers   [1 failure]                 │  │
│  │                                                         │  │
│  │  Root Cause: Test data not initialized                 │  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  🔧 Fix Required:                                               │
│     Initialize Oracle test database with init script            │
│                                                                 │
│  📝 Commands:                                                   │
│     $ cd tests/integration/database                             │
│     $ docker cp init-oracle.sql tstoracle:/tmp/                │
│     $ docker exec tstoracle sqlplus sys/MyOraclePass123@        │
│       //localhost:1521/FREEPDB1 as sysdba @/tmp/init-oracle.sql│
│                                                                 │
│  ⏱️  Estimated fix time: 2 minutes                              │
│  📈 Expected improvement: +13 passing tests (75% → 79%)         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

This visual reference provides comprehensive command visualization, expected outputs, and troubleshooting guidance for all AI-Shell database testing operations.
