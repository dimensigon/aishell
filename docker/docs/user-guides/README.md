# AI-Shell Database Testing - User Guides

Welcome to the AI-Shell Database Integration Testing user documentation!

## 📚 Available Guides

### 1. [Quick Start Guide](QUICK_START_GUIDE.md)
**⏱️ 5 minutes** - Get from zero to running tests

Perfect for:
- First-time users
- Quick environment setup
- Daily testing workflow

**What you'll learn:**
- Verify prerequisites
- Start all services
- Run your first tests
- View results in admin UIs

[**→ Start Here**](QUICK_START_GUIDE.md)

---

### 2. [Complete User Guide](DATABASE_TESTING_USER_GUIDE.md)
**⏱️ 30 minutes** - Comprehensive documentation

Perfect for:
- Understanding all commands
- Learning workflows
- Troubleshooting issues
- Advanced usage patterns

**What's covered:**
- All available commands with outputs
- 5 complete user workflows
- Troubleshooting 10+ common issues
- Individual database testing
- Admin UI usage
- Environment variables
- Parallel test execution

[**→ Read Full Guide**](DATABASE_TESTING_USER_GUIDE.md)

---

### 3. [Visual Command Reference](VISUAL_COMMAND_REFERENCE.md)
**⏱️ As needed** - Visual command examples

Perfect for:
- Seeing expected outputs
- Understanding test flow
- Diagnosing failures
- Performance analysis

**What's included:**
- Flow diagrams for all operations
- Test execution timeline
- Results breakdown with charts
- Container status visualization
- Performance metrics
- Animated command sequences
- Error state visualizations

[**→ Browse Visual Reference**](VISUAL_COMMAND_REFERENCE.md)

---

## 🎯 Quick Navigation by Use Case

### I want to...

#### Get Started Quickly
→ [Quick Start Guide](QUICK_START_GUIDE.md)

#### Understand All Commands
→ [User Guide - Available Commands](DATABASE_TESTING_USER_GUIDE.md#available-commands)

#### See Expected Outputs
→ [Visual Command Reference](VISUAL_COMMAND_REFERENCE.md)

#### Fix a Problem
→ [User Guide - Troubleshooting](DATABASE_TESTING_USER_GUIDE.md#troubleshooting)

#### Run Tests for One Database
→ [User Guide - Individual Database Testing](DATABASE_TESTING_USER_GUIDE.md#4-individual-database-testing)

#### View Test Data
→ [User Guide - Workflow 4](DATABASE_TESTING_USER_GUIDE.md#workflow-4-viewing-test-results-in-admin-uis)

#### Improve Test Pass Rate
→ [Quick Start - Improve Pass Rate](QUICK_START_GUIDE.md#improve-test-pass-rate)

#### Debug Failed Tests
→ [User Guide - Workflow 3](DATABASE_TESTING_USER_GUIDE.md#workflow-3-debugging-failed-tests)

#### Reset Environment
→ [User Guide - Workflow 5](DATABASE_TESTING_USER_GUIDE.md#workflow-5-clean-environment-reset)

---

## 📊 Current Test Statistics

```
┌────────────────────────────────────────┐
│        Test Suite Overview             │
├────────────────────────────────────────┤
│  Total Tests:     312                  │
│  Databases:       5                    │
│  Pass Rate:       71% (222/312)        │
│  Duration:        ~27 seconds          │
│                                        │
│  Database Breakdown:                   │
│  ├─ PostgreSQL:   57 tests (96% pass) │
│  ├─ MySQL:        66 tests (100% pass)│
│  ├─ Oracle:       43 tests (70% pass) │
│  ├─ MongoDB:      52 tests (96% pass) │
│  └─ Redis:       112 tests (99% pass) │
└────────────────────────────────────────┘
```

---

## 🗺️ System Architecture

```
┌─────────────────────────────────────────────────────┐
│               AI-Shell Test Environment             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  External Containers      Managed Containers       │
│  ┌────────────┐          ┌────────────┐          │
│  │  tstmysql  │          │ PostgreSQL │          │
│  │ Port: 3307 │          │ Port: 5432 │          │
│  └────────────┘          └────────────┘          │
│                                                     │
│  ┌────────────┐          ┌────────────┐          │
│  │ tstoracle  │          │  MongoDB   │          │
│  │ Port: 1521 │          │ Port:27017 │          │
│  └────────────┘          └────────────┘          │
│                                                     │
│                          ┌────────────┐          │
│                          │   Redis    │          │
│                          │ Port: 6379 │          │
│                          └────────────┘          │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Command Reference

```bash
# Start everything
cd /home/claude/AIShell/aishell/docker
docker compose -f docker-compose.test.yml up -d
./run-integration-tests.sh

# Test individual database
npm test -- tests/integration/database/postgres.integration.test.ts

# Check connections
./test-connections.sh

# View status
docker compose -f docker-compose.test.yml ps

# Stop everything
docker compose -f docker-compose.test.yml down
```

---

## 🎨 Admin UI Access

Once services are running, access these admin interfaces:

| Service | URL | Credentials | Purpose |
|---------|-----|-------------|---------|
| **Adminer** | http://localhost:8080 | See guide | SQL databases (PostgreSQL, MySQL) |
| **Mongo Express** | http://localhost:8081 | admin/pass | MongoDB management |
| **Redis Commander** | http://localhost:8082 | None | Redis key browser |
| **Oracle EM Express** | https://localhost:5500/em | sys/MyOraclePass123 | Oracle database |

---

## 📖 Additional Documentation

### Database-Specific Setup Guides

Located in `/home/claude/AIShell/aishell/docker/`:

- **EXTERNAL_MYSQL_SETUP.md** - MySQL container setup and configuration
- **EXTERNAL_ORACLE_SETUP.md** - Oracle 23c Free setup and configuration
- **docker-compose.test.yml** - Container definitions
- **.env.test** - Environment variables

### Test Files

Located in `/home/claude/AIShell/aishell/tests/integration/database/`:

- **postgres.integration.test.ts** - PostgreSQL tests (57 tests)
- **mysql.integration.test.ts** - MySQL tests (66 tests)
- **oracle.integration.test.ts** - Oracle tests (43 tests)
- **mongodb.integration.test.ts** - MongoDB tests (52 tests)
- **redis.integration.test.ts** - Redis tests (112 tests)

---

## 🆘 Getting Help

### Common Issues

1. **Container not found** → [User Guide - Troubleshooting Issue 1](DATABASE_TESTING_USER_GUIDE.md#issue-1-external-container-not-found)
2. **Connection refused** → [User Guide - Troubleshooting Issue 2](DATABASE_TESTING_USER_GUIDE.md#issue-2-connection-refused)
3. **Tests timeout** → [User Guide - Troubleshooting Issue 3](DATABASE_TESTING_USER_GUIDE.md#issue-3-tests-timeout)
4. **Port in use** → [User Guide - Troubleshooting Issue 4](DATABASE_TESTING_USER_GUIDE.md#issue-4-port-already-in-use)
5. **Oracle not ready** → [User Guide - Troubleshooting Issue 5](DATABASE_TESTING_USER_GUIDE.md#issue-5-oracle-tests-all-failing)

### Where to Look

1. **Check logs**: `docker logs <container-name>`
2. **Test results**: `cat docker/test-results.log`
3. **Connection test**: `./test-connections.sh`
4. **Container status**: `docker compose -f docker-compose.test.yml ps`

---

## 🎓 Learning Path

### Beginner
1. ✅ Complete [Quick Start Guide](QUICK_START_GUIDE.md)
2. 📖 Read [User Guide - Getting Started](DATABASE_TESTING_USER_GUIDE.md#getting-started)
3. 👀 Browse [Visual Command Reference](VISUAL_COMMAND_REFERENCE.md)

### Intermediate
1. 🔍 Study [User Guide - Available Commands](DATABASE_TESTING_USER_GUIDE.md#available-commands)
2. 🎯 Practice [User Workflows](DATABASE_TESTING_USER_GUIDE.md#user-workflows)
3. 🔧 Learn [Troubleshooting](DATABASE_TESTING_USER_GUIDE.md#troubleshooting)

### Advanced
1. ⚡ Master [Advanced Usage](DATABASE_TESTING_USER_GUIDE.md#advanced-usage)
2. 📊 Analyze [Performance Metrics](VISUAL_COMMAND_REFERENCE.md#-performance-metrics-visualization)
3. 🚀 Optimize [Parallel Testing](DATABASE_TESTING_USER_GUIDE.md#parallel-test-execution)

---

## 📝 Document Versions

| Document | Version | Last Updated |
|----------|---------|--------------|
| Quick Start Guide | 1.0 | Oct 27, 2025 |
| User Guide | 1.0 | Oct 27, 2025 |
| Visual Reference | 1.0 | Oct 27, 2025 |
| README | 1.0 | Oct 27, 2025 |

---

## 🎯 Success Criteria

After reading these guides, you should be able to:

- ✅ Start all test services in under 2 minutes
- ✅ Run complete test suite (312 tests)
- ✅ Test individual databases
- ✅ Diagnose and fix common issues
- ✅ View test data in admin UIs
- ✅ Understand test results and metrics
- ✅ Reset environment when needed

---

**Ready to start?** → [Begin with Quick Start Guide](QUICK_START_GUIDE.md)

**Need help?** → [See Troubleshooting](DATABASE_TESTING_USER_GUIDE.md#troubleshooting)

**Want examples?** → [Browse Visual Reference](VISUAL_COMMAND_REFERENCE.md)

---

*Last Updated: October 27, 2025*
*AI-Shell Database Testing Suite v1.0.0*
