# AI-Shell Docker Test Environment

Comprehensive Docker Compose configuration for AI-Shell testing with all required databases.

## 📦 Included Services

| Service | Version | Port(s) | Purpose |
|---------|---------|---------|---------|
| **MongoDB** | Latest | 27017 | Document database with authentication |
| **Redis** | Latest | 6379 | In-memory cache and message broker |
| **PostgreSQL** | 16 | 5432 | Relational database |
| **MySQL** | 8 | 3307 | Relational database (non-standard port) |
| **Oracle DB** | 23c Free | 1521, 5500 | Enterprise database (CDB + PDB) |
| **Adminer** | Latest | 8080 | SQL database admin UI |
| **Mongo Express** | Latest | 8081 | MongoDB admin UI |
| **Redis Commander** | Latest | 8082 | Redis admin UI |

## 🚀 Quick Start

### 1. Prerequisites

- Docker Engine 20.10+ or Docker Desktop
- Docker Compose 2.0+
- At least 8GB RAM available for containers
- At least 20GB disk space

### 2. Start All Services

```bash
cd /home/claude/AIShell/aishell/docker

# Start all services
docker compose -f docker-compose.test.yml --env-file .env.test up -d

# Or start specific services
docker compose -f docker-compose.test.yml --env-file .env.test up -d postgres mysql redis
```

### 3. Check Service Health

```bash
# Check all container status
docker compose -f docker-compose.test.yml ps

# Check service health
docker compose -f docker-compose.test.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# View logs
docker compose -f docker-compose.test.yml logs -f

# View logs for specific service
docker compose -f docker-compose.test.yml logs -f postgres
```

### 4. Wait for Services to be Ready

```bash
# Wait for all services to be healthy (may take 2-3 minutes for Oracle)
docker compose -f docker-compose.test.yml ps

# Test connections
docker exec aishell-postgres-test pg_isready -U postgres
docker exec aishell-mysql-test mysqladmin ping -h localhost -u root -pMyMySQLPass123
docker exec aishell-mongodb-test mongosh --eval "db.adminCommand('ping')"
docker exec aishell-redis-test redis-cli ping
```

## 🔐 Database Credentials

### MongoDB
```bash
Host:     localhost:27017
Username: admin
Password: MyMongoPass123
Database: testdb

# Connection String
mongodb://admin:MyMongoPass123@localhost:27017/testdb?authSource=admin

# CLI Connection
mongosh "mongodb://admin:MyMongoPass123@localhost:27017/testdb?authSource=admin"
```

### Redis
```bash
Host: localhost:6379
Auth: None (no password required)

# Connection String
redis://localhost:6379

# CLI Connection
redis-cli -h localhost -p 6379
```

### PostgreSQL
```bash
Host:     localhost:5432
Username: postgres
Password: MyPostgresPass123
Database: testdb

# Connection String
postgresql://postgres:MyPostgresPass123@localhost:5432/testdb

# CLI Connection
psql -h localhost -U postgres -d testdb
# Password: MyPostgresPass123
```

### MySQL
```bash
Host:     localhost:3307  # Note: Non-standard port!
Username: root
Password: MyMySQLPass123
Database: testdb

# Connection String
mysql://root:MyMySQLPass123@localhost:3307/testdb

# CLI Connection
mysql -h localhost -P 3307 -u root -pMyMySQLPass123 testdb
```

### Oracle Database 23c Free
```bash
# Container Database (CDB)
Host:     localhost:1521
SID:      FREE
Username: SYS
Password: MyOraclePass123
Role:     SYSDBA

# Pluggable Database (PDB)
Host:     localhost:1521
Service:  FREEPDB1
Username: SYSTEM
Password: MyOraclePass123

# Connection Strings
CDB: SYS/MyOraclePass123@//localhost:1521/FREE as sysdba
PDB: SYSTEM/MyOraclePass123@//localhost:1521/FREEPDB1

# SQL*Plus Connection (CDB)
sqlplus sys/MyOraclePass123@//localhost:1521/FREE as sysdba

# SQL*Plus Connection (PDB)
sqlplus system/MyOraclePass123@//localhost:1521/FREEPDB1
```

## 🌐 Admin Web Interfaces

### Adminer (SQL Databases)
- URL: http://localhost:8080
- System: Select PostgreSQL/MySQL/Oracle
- Server: postgres/mysql/oracle (container name) or localhost
- Username: See credentials above
- Password: See credentials above

### Mongo Express (MongoDB)
- URL: http://localhost:8081
- Username: admin
- Password: pass

### Redis Commander (Redis)
- URL: http://localhost:8082
- No authentication required

### Oracle Enterprise Manager Express
- URL: https://localhost:5500/em
- Username: SYS
- Password: MyOraclePass123
- Container Name: FREE

## 🛠️ Management Commands

### Start Services
```bash
# All services
docker compose -f docker-compose.test.yml up -d

# Specific services
docker compose -f docker-compose.test.yml up -d postgres mysql redis

# With logs
docker compose -f docker-compose.test.yml up
```

### Stop Services
```bash
# Stop all
docker compose -f docker-compose.test.yml stop

# Stop specific service
docker compose -f docker-compose.test.yml stop postgres
```

### Restart Services
```bash
# Restart all
docker compose -f docker-compose.test.yml restart

# Restart specific
docker compose -f docker-compose.test.yml restart mysql
```

### Remove Services
```bash
# Stop and remove containers (keeps volumes)
docker compose -f docker-compose.test.yml down

# Remove containers and volumes (CAUTION: deletes all data!)
docker compose -f docker-compose.test.yml down -v

# Remove everything including networks
docker compose -f docker-compose.test.yml down -v --remove-orphans
```

### View Logs
```bash
# All services
docker compose -f docker-compose.test.yml logs -f

# Specific service
docker compose -f docker-compose.test.yml logs -f postgres

# Last 100 lines
docker compose -f docker-compose.test.yml logs --tail=100 mysql
```

### Execute Commands in Containers
```bash
# PostgreSQL
docker exec -it aishell-postgres-test psql -U postgres -d testdb

# MySQL
docker exec -it aishell-mysql-test mysql -u root -pMyMySQLPass123 testdb

# MongoDB
docker exec -it aishell-mongodb-test mongosh -u admin -p MyMongoPass123 --authenticationDatabase admin

# Redis
docker exec -it aishell-redis-test redis-cli

# Oracle
docker exec -it aishell-oracle-test sqlplus sys/MyOraclePass123@//localhost:1521/FREE as sysdba

# Bash access
docker exec -it aishell-postgres-test bash
```

## 📊 Resource Limits

Each service has resource limits configured:

| Service | CPU Limit | Memory Limit | CPU Reserved | Memory Reserved |
|---------|-----------|--------------|--------------|-----------------|
| MongoDB | 2 cores | 2GB | 0.5 cores | 512MB |
| Redis | 1 core | 1GB | 0.25 cores | 256MB |
| PostgreSQL | 2 cores | 2GB | 0.5 cores | 512MB |
| MySQL | 2 cores | 2GB | 0.5 cores | 512MB |
| Oracle | 4 cores | 4GB | 1 core | 2GB |

**Total System Requirements:**
- Minimum: 11 CPU cores, 12GB RAM
- Recommended: 16 CPU cores, 16GB RAM

## 🗂️ Data Persistence

All database data is persisted in Docker volumes:

```bash
# List volumes
docker volume ls | grep aishell

# Inspect volume
docker volume inspect aishell-postgres-data

# Backup volume
docker run --rm -v aishell-postgres-data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/postgres-backup.tar.gz /data

# Restore volume
docker run --rm -v aishell-postgres-data:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/postgres-backup.tar.gz -C /
```

## 🔧 Initialization Scripts

Place initialization scripts in the respective directories:

```
docker/init-scripts/
├── mongodb/       # JavaScript files (.js)
├── postgres/      # SQL files (.sql)
├── mysql/         # SQL files (.sql)
└── oracle/        # SQL files (.sql)
```

Scripts are executed in alphabetical order on first container startup.

### Example: PostgreSQL Init Script

Create `/home/claude/AIShell/aishell/docker/init-scripts/postgres/01-init.sql`:

```sql
-- Create test tables
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert test data
INSERT INTO users (username, email) VALUES
    ('testuser1', 'test1@example.com'),
    ('testuser2', 'test2@example.com');
```

### Example: MongoDB Init Script

Create `/home/claude/AIShell/aishell/docker/init-scripts/mongodb/01-init.js`:

```javascript
// Switch to testdb
db = db.getSiblingDB('testdb');

// Create collection and insert test data
db.users.insertMany([
    { username: 'testuser1', email: 'test1@example.com' },
    { username: 'testuser2', email: 'test2@example.com' }
]);

// Create index
db.users.createIndex({ username: 1 }, { unique: true });
```

## 🧪 Testing Connections

### Quick Connection Test Script

Create `/home/claude/AIShell/aishell/docker/test-connections.sh`:

```bash
#!/bin/bash

echo "Testing database connections..."

# PostgreSQL
echo -n "PostgreSQL: "
docker exec aishell-postgres-test pg_isready -U postgres && echo "✓" || echo "✗"

# MySQL
echo -n "MySQL: "
docker exec aishell-mysql-test mysqladmin ping -h localhost -u root -pMyMySQLPass123 2>/dev/null && echo "✓" || echo "✗"

# MongoDB
echo -n "MongoDB: "
docker exec aishell-mongodb-test mongosh --quiet --eval "db.adminCommand('ping').ok" 2>/dev/null | grep -q 1 && echo "✓" || echo "✗"

# Redis
echo -n "Redis: "
docker exec aishell-redis-test redis-cli ping | grep -q PONG && echo "✓" || echo "✗"

# Oracle (slower check)
echo -n "Oracle: "
docker exec aishell-oracle-test sqlplus -s sys/MyOraclePass123@//localhost:1521/FREE as sysdba <<< "SELECT 1 FROM DUAL;" 2>/dev/null | grep -q 1 && echo "✓" || echo "✗"
```

Make it executable:
```bash
chmod +x /home/claude/AIShell/aishell/docker/test-connections.sh
```

## 🐛 Troubleshooting

### Oracle Container Taking Long to Start
Oracle DB requires 2-3 minutes for initial startup. Check logs:
```bash
docker compose -f docker-compose.test.yml logs -f oracle
```

Look for: "DATABASE IS READY TO USE!"

### Port Already in Use
If ports are already in use, modify `.env.test` or docker-compose.test.yml:
```yaml
ports:
  - "5433:5432"  # Use different host port
```

### Container Fails to Start
```bash
# Check logs
docker compose -f docker-compose.test.yml logs <service-name>

# Check resource usage
docker stats

# Restart specific service
docker compose -f docker-compose.test.yml restart <service-name>
```

### Out of Memory
Reduce resource limits in docker-compose.test.yml or increase Docker memory allocation:
- Docker Desktop: Settings → Resources → Memory

### Permission Denied on Volumes
```bash
# Fix volume permissions
docker compose -f docker-compose.test.yml down
docker volume rm aishell-<service>-data
docker compose -f docker-compose.test.yml up -d
```

### Clean Start
```bash
# Remove everything and start fresh
docker compose -f docker-compose.test.yml down -v
docker compose -f docker-compose.test.yml up -d
```

## 📝 Environment Variables

Edit `/home/claude/AIShell/aishell/docker/.env.test` to customize:

```bash
# Example: Change PostgreSQL database name
POSTGRES_DB=mydb

# Example: Change Oracle password
ORACLE_PASSWORD=NewSecurePass456

# Restart services to apply changes
docker compose -f docker-compose.test.yml up -d --force-recreate
```

## 🔒 Security Notes

⚠️ **WARNING**: This configuration is for **TESTING ONLY**. Do NOT use in production!

- Default passwords are hardcoded for convenience
- No SSL/TLS encryption configured
- Admin interfaces exposed without authentication
- No firewall rules or network isolation

For production:
1. Use strong, unique passwords
2. Enable SSL/TLS for all connections
3. Restrict network access
4. Use secrets management (Docker secrets, Vault, etc.)
5. Enable database auditing
6. Regular security updates

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [MySQL Docker Hub](https://hub.docker.com/_/mysql)
- [MongoDB Docker Hub](https://hub.docker.com/_/mongo)
- [Redis Docker Hub](https://hub.docker.com/_/redis)
- [Oracle Database Free](https://www.oracle.com/database/free/)

## 🤝 Support

For issues specific to AI-Shell, please check the main project documentation or open an issue on the repository.

## 🧪 Automated Test Runner Scripts

The Docker environment includes comprehensive test automation scripts for CI/CD integration.

### Available Scripts

#### test-runner.sh
Main test orchestration script that manages the complete test lifecycle.

```bash
# Run full test suite
./test-runner.sh
```

**Features:**
- Validates Docker environment
- Starts Docker Compose services
- Waits for services to become healthy
- Executes test suite with coverage
- Collects results and logs
- Performs cleanup
- Returns proper exit codes

**Configuration:**
- `MAX_WAIT_TIME=120` - Maximum seconds to wait for services
- `HEALTH_CHECK_INTERVAL=5` - Seconds between health checks
- `TEST_TIMEOUT=600` - Maximum test execution time (seconds)

**Output:**
- `test-results/` - Test results, coverage, and logs
- `test-results/test-summary.txt` - Execution summary
- `test-results/docker-containers.log` - Container logs

#### health-check.sh
Verifies the health of all database services.

```bash
# Verbose health check
./health-check.sh

# Quiet mode (only show errors)
./health-check.sh --quiet

# Show help
./health-check.sh --help
```

**Checks Performed:**
- Container status verification
- Connection testing
- Authentication verification
- Basic query execution
- Service-specific health checks

**Exit Codes:**
- `0` - All services healthy
- `1` - One or more services unhealthy

#### cleanup.sh
Comprehensive cleanup of Docker resources and test data.

```bash
# Basic cleanup
./cleanup.sh

# Force cleanup (no prompts, remove test data)
./cleanup.sh --force

# Also remove Docker images
./cleanup.sh --remove-images

# Full system prune (removes ALL unused Docker resources)
./cleanup.sh --prune

# Complete cleanup
./cleanup.sh --all
```

**Options:**
- `--force, -f` - No prompts, remove test-results directory
- `--remove-images, -i` - Remove Docker images used by services
- `--prune, -p` - Prune entire Docker system
- `--all, -a` - Equivalent to `--force --remove-images --prune`

### GitHub Actions Integration

The project includes `.github/workflows/database-tests.yml` for automated CI/CD testing.

**Features:**
- Runs on push to main/develop/feature branches
- Tests on Node.js 18.x and 20.x
- Parallel execution for faster feedback
- Automatic cleanup after tests
- Coverage reporting to Codecov
- Test result artifacts (7 day retention)

**Environment Variables:**
- `NODE_ENV=test`
- `CI=true`
- `DATABASE_TEST_MODE=docker`

### Development Workflow

#### Local Testing

```bash
# 1. Start services and run tests
cd docker
./test-runner.sh

# 2. If tests fail, check health
./health-check.sh

# 3. View container logs
docker compose -f docker-compose.test.yml logs [service-name]

# 4. Run specific tests
npm run test -- --testPathPattern=database

# 5. Cleanup when done
./cleanup.sh --force
```

#### Debugging Failed Tests

```bash
# Start services manually
docker compose -f docker-compose.test.yml up -d

# Check health
./health-check.sh

# Run tests with verbose output
npm run test -- --verbose --runInBand

# Check specific service logs
docker compose -f docker-compose.test.yml logs postgres

# Cleanup
./cleanup.sh
```

### Test Results

After running tests, results are available in:

```
test-results/
├── test-output.log           # Raw test output
├── coverage/                 # Coverage reports
│   ├── lcov.info
│   ├── coverage-summary.json
│   └── html/                # HTML coverage report
├── docker-containers.log     # Container logs
└── test-summary.txt         # Execution summary
```

### Performance Optimization

#### Faster Test Execution

```bash
# Use parallel test execution
npm run test -- --maxWorkers=4

# Cache Docker images
docker compose -f docker-compose.test.yml pull

# Use tmpfs for databases (Linux)
# Add to docker-compose.test.yml:
tmpfs:
  - /var/lib/postgresql/data
```

#### Reduce CI/CD Time

- Cache npm dependencies
- Pre-pull Docker images
- Use matrix strategy sparingly
- Run tests only on relevant changes
- Use Docker layer caching

## 📄 License

This configuration is part of the AI-Shell project. See main project LICENSE for details.
