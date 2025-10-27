# Oracle Integration Tests - Quick Start Guide

## TL;DR - Get Running in 5 Minutes

```bash
# 1. Start Oracle Database
docker run -d --name oracle-free -p 1521:1521 -e ORACLE_PWD=MyOraclePass123 \
  container-registry.oracle.com/database/free:latest

# 2. Wait for ready (5-10 min)
docker logs -f oracle-free  # Look for "DATABASE IS READY TO USE"

# 3. Install Oracle client
npm install oracledb --save-dev

# 4. Initialize test data
cd tests/integration/database
./init-oracle-docker.sh

# 5. Run tests
npm test test-oracle-integration.ts
```

## What Gets Tested

### Core Database Operations
- ✅ Connections to CDB$ROOT and FREEPDB1
- ✅ CRUD: INSERT, SELECT, UPDATE, DELETE
- ✅ Transactions: COMMIT, ROLLBACK
- ✅ Bulk operations (100+ rows)

### Oracle-Specific Features
- ✅ Stored procedures with OUT parameters
- ✅ Functions returning values
- ✅ Sequences (NEXTVAL, CURRVAL)
- ✅ Triggers (auto-increment, timestamps)
- ✅ Packages (employee_pkg)

### Advanced Queries
- ✅ JOINs (INNER, LEFT, RIGHT)
- ✅ Subqueries (scalar, correlated)
- ✅ Common Table Expressions (CTEs)
- ✅ Aggregations (GROUP BY, HAVING)
- ✅ Window functions

### Quality Assurance
- ✅ Error handling (constraints, syntax errors)
- ✅ Connection pooling and recovery
- ✅ Performance testing (EXPLAIN PLAN)
- ✅ 60+ individual test cases

## Test Data Schema

```
employees (6 records)
  ├── John Smith - Senior Engineer
  ├── Sarah Johnson - Software Engineer
  ├── Michael Williams - Sales Manager
  ├── Emily Davis - Marketing Specialist
  ├── David Brown - Junior Developer
  └── Lisa Anderson - HR Manager

departments (4 records)
  ├── Engineering ($5M budget)
  ├── Sales ($3M budget)
  ├── Marketing ($2M budget)
  └── HR ($1.5M budget)

projects (3 records)
  ├── Cloud Migration
  ├── Mobile App Development
  └── Q4 Sales Campaign

employee_projects
  └── 6 project assignments
```

## Connection Strings

### CDB$ROOT (Container Database)
```typescript
{
  user: 'SYS',
  password: 'MyOraclePass123',
  connectString: 'localhost:1521/free',
  privilege: oracledb.SYSDBA
}
```

### FREEPDB1 (Pluggable Database)
```typescript
{
  user: 'SYS',
  password: 'MyOraclePass123',
  connectString: 'localhost:1521/freepdb1',
  privilege: oracledb.SYSDBA
}
```

### Test User (created by init script)
```typescript
{
  user: 'test_user',
  password: 'TestPass123',
  connectString: 'localhost:1521/freepdb1'
}
```

## Common Issues & Solutions

### "Cannot locate Oracle Client library"

**Linux:**
```bash
export LD_LIBRARY_PATH=/opt/oracle/instantclient_21_12:$LD_LIBRARY_PATH
```

**macOS:**
```bash
export DYLD_LIBRARY_PATH=/usr/local/lib:$DYLD_LIBRARY_PATH
```

### "TNS:no listener"

```bash
# Check if Oracle is running
docker ps | grep oracle

# Check listener
docker exec oracle-free lsnrctl status

# Restart container
docker restart oracle-free
```

### "Database not ready"

```bash
# Monitor startup (can take 5-10 minutes first time)
docker logs -f oracle-free

# Look for this message:
# "DATABASE IS READY TO USE"
```

### Tests failing with "table does not exist"

```bash
# Reinitialize test data
./init-oracle-docker.sh

# Or manually:
docker cp init-oracle.sql oracle-free:/tmp/
docker exec oracle-free sqlplus sys/MyOraclePass123@FREEPDB1 as sysdba @/tmp/init-oracle.sql
```

## Manual Testing / Exploration

```bash
# Connect as SYS
docker exec -it oracle-free sqlplus sys/MyOraclePass123@FREEPDB1 as sysdba

# Connect as test_user
docker exec -it oracle-free sqlplus test_user/TestPass123@FREEPDB1

# Sample queries to try:
SELECT * FROM test_user.employees;
SELECT * FROM test_user.v_employee_details;
SELECT test_user.get_full_name(1001) FROM DUAL;

# Call stored procedure
DECLARE
  v_new_salary NUMBER;
BEGIN
  test_user.give_raise(1001, 10, v_new_salary);
  DBMS_OUTPUT.PUT_LINE('New salary: ' || v_new_salary);
END;
/
```

## Running Specific Test Suites

```bash
# Connection tests only
npm test test-oracle-integration.ts -- --grep "Connection"

# CRUD operations
npm test test-oracle-integration.ts -- --grep "CRUD"

# Stored procedures
npm test test-oracle-integration.ts -- --grep "Procedures"

# Complex queries
npm test test-oracle-integration.ts -- --grep "Complex"

# Error handling
npm test test-oracle-integration.ts -- --grep "Error"
```

## Test Coverage Report

```bash
# Generate coverage report
npm run test:coverage test-oracle-integration.ts

# View coverage in browser
npm run test:ui
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Setup Oracle
  run: |
    docker run -d --name oracle-free -p 1521:1521 \
      -e ORACLE_PWD=MyOraclePass123 \
      container-registry.oracle.com/database/free:latest

- name: Wait for Oracle
  run: |
    timeout 600 bash -c 'until docker logs oracle-free 2>&1 | grep -q "DATABASE IS READY"; do sleep 5; done'

- name: Initialize test data
  run: ./tests/integration/database/init-oracle-docker.sh

- name: Run tests
  run: npm test test-oracle-integration.ts
```

## Performance Considerations

- First container start: **5-10 minutes** (downloads image, initializes DB)
- Subsequent starts: **30-60 seconds**
- Test execution: **30-60 seconds** (60+ tests)
- Test data initialization: **10-20 seconds**

## Cleanup

```bash
# Stop Oracle container
docker stop oracle-free

# Remove container (keeps image)
docker rm oracle-free

# Remove container and data
docker rm -f oracle-free

# Remove image (saves ~3GB)
docker rmi container-registry.oracle.com/database/free:latest
```

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `test-oracle-integration.ts` | 929 | Test suite |
| `init-oracle.sql` | 413 | Test data |
| `init-oracle-docker.sh` | 99 | Init script |
| `README.md` | 250+ | Docs (Oracle section) |

## Next Steps

1. Review test coverage: `npm run test:coverage`
2. Explore test data: Connect via `sqlplus`
3. Add custom tests for your use cases
4. Integrate into CI/CD pipeline
5. Monitor performance metrics

## Resources

- [Oracle Database Free Docs](https://www.oracle.com/database/free/)
- [node-oracledb Docs](https://oracle.github.io/node-oracledb/)
- [Oracle SQL Reference](https://docs.oracle.com/en/database/oracle/oracle-database/23/sqlrf/)
- [Test Suite README](./README.md) - Full documentation

## Support

For issues or questions:
1. Check the [README.md](./README.md) for detailed troubleshooting
2. Review Docker logs: `docker logs oracle-free`
3. Verify Oracle client installation
4. Check test data initialization

---

**Happy Testing!** 🎉
