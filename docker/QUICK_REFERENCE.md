# AI-Shell Docker Test Environment - Quick Reference

## 🚀 Quick Start

```bash
cd /home/claude/AIShell/aishell/docker

# Start all services
./start.sh up

# Test connections
./test-connections.sh

# View status
./start.sh status
```

## 🔌 Connection Strings

### PostgreSQL
```bash
# Connection String
postgresql://postgres:MyPostgresPass123@localhost:5432/testdb

# CLI
psql -h localhost -U postgres -d testdb
# Password: MyPostgresPass123

# Node.js
const { Client } = require('pg');
const client = new Client({
  host: 'localhost',
  port: 5432,
  user: 'postgres',
  password: 'MyPostgresPass123',
  database: 'testdb'
});
```

### MySQL
```bash
# Connection String
mysql://root:MyMySQLPass123@localhost:3307/testdb

# CLI
mysql -h localhost -P 3307 -u root -pMyMySQLPass123 testdb

# Node.js
const mysql = require('mysql2');
const connection = mysql.createConnection({
  host: 'localhost',
  port: 3307,
  user: 'root',
  password: 'MyMySQLPass123',
  database: 'testdb'
});
```

### MongoDB
```bash
# Connection String
mongodb://admin:MyMongoPass123@localhost:27017/testdb?authSource=admin

# CLI
mongosh "mongodb://admin:MyMongoPass123@localhost:27017/testdb?authSource=admin"

# Node.js
const { MongoClient } = require('mongodb');
const client = new MongoClient('mongodb://admin:MyMongoPass123@localhost:27017/testdb?authSource=admin');
```

### Redis
```bash
# Connection String
redis://localhost:6379

# CLI
redis-cli -h localhost -p 6379

# Node.js
const redis = require('redis');
const client = redis.createClient({
  host: 'localhost',
  port: 6379
});
```

### Oracle Database 23c
```bash
# CDB Connection String
SYS/MyOraclePass123@//localhost:1521/FREE as sysdba

# PDB Connection String
SYSTEM/MyOraclePass123@//localhost:1521/FREEPDB1

# SQL*Plus (CDB)
sqlplus sys/MyOraclePass123@//localhost:1521/FREE as sysdba

# SQL*Plus (PDB)
sqlplus system/MyOraclePass123@//localhost:1521/FREEPDB1

# Node.js (using oracledb)
const oracledb = require('oracledb');
const connection = await oracledb.getConnection({
  user: 'system',
  password: 'MyOraclePass123',
  connectString: 'localhost:1521/FREEPDB1'
});
```

## 🌐 Admin Web Interfaces

| Service | URL | Credentials |
|---------|-----|-------------|
| **Adminer** (SQL) | http://localhost:8080 | See database credentials above |
| **Mongo Express** | http://localhost:8081 | admin / pass |
| **Redis Commander** | http://localhost:8082 | No auth required |
| **Oracle EM Express** | https://localhost:5500/em | SYS / MyOraclePass123 |

## 📊 Port Mapping

| Service | Container Port | Host Port |
|---------|---------------|-----------|
| PostgreSQL | 5432 | 5432 |
| MySQL | 3306 | **3307** ⚠️ |
| MongoDB | 27017 | 27017 |
| Redis | 6379 | 6379 |
| Oracle TNS | 1521 | 1521 |
| Oracle EM | 5500 | 5500 |
| Adminer | 8080 | 8080 |
| Mongo Express | 8081 | 8081 |
| Redis Commander | 8081 | 8082 |

⚠️ **Note**: MySQL uses port **3307** on the host to avoid conflicts with local installations.

## 🛠️ Common Commands

```bash
# Start specific services
./start.sh up postgres mysql redis

# Stop all services
./start.sh down

# Restart a service
./start.sh restart postgres

# View logs (live)
./start.sh logs postgres

# View all logs
./start.sh logs

# Check service status
./start.sh status

# Clean everything (WARNING: deletes data)
./start.sh clean

# Test connections
./test-connections.sh
```

## 🐳 Docker Commands

```bash
# Execute command in container
docker exec -it aishell-postgres-test psql -U postgres -d testdb
docker exec -it aishell-mysql-test mysql -u root -pMyMySQLPass123 testdb
docker exec -it aishell-mongodb-test mongosh -u admin -p MyMongoPass123 --authenticationDatabase admin
docker exec -it aishell-redis-test redis-cli
docker exec -it aishell-oracle-test sqlplus sys/MyOraclePass123@//localhost:1521/FREE as sysdba

# Shell access
docker exec -it aishell-postgres-test bash
docker exec -it aishell-mysql-test bash
docker exec -it aishell-mongodb-test bash

# View container logs
docker logs -f aishell-postgres-test
docker logs -f aishell-mysql-test
docker logs -f aishell-oracle-test

# Inspect container
docker inspect aishell-postgres-test

# Check resource usage
docker stats
```

## 📦 Volume Management

```bash
# List volumes
docker volume ls | grep aishell

# Backup PostgreSQL data
docker run --rm -v aishell-postgres-data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/postgres-backup-$(date +%Y%m%d).tar.gz /data

# Backup MySQL data
docker run --rm -v aishell-mysql-data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/mysql-backup-$(date +%Y%m%d).tar.gz /data

# Backup MongoDB data
docker run --rm -v aishell-mongodb-data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/mongodb-backup-$(date +%Y%m%d).tar.gz /data

# Remove all volumes (WARNING: deletes all data)
docker volume rm aishell-postgres-data aishell-mysql-data aishell-mongodb-data aishell-redis-data aishell-oracle-data
```

## 🧪 Sample Queries

### PostgreSQL
```sql
-- List tables
\dt test_schema.*

-- Query users
SELECT * FROM test_schema.users LIMIT 5;

-- Query products by category
SELECT name, price, stock_quantity
FROM test_schema.products
WHERE category = 'Electronics';
```

### MySQL
```sql
-- List tables
SHOW TABLES;

-- Query users
SELECT * FROM users LIMIT 5;

-- Query products by category
SELECT name, price, stock_quantity
FROM products
WHERE category = 'Electronics';

-- Call stored procedure
CALL get_user_orders(1);
```

### MongoDB
```javascript
// List collections
show collections

// Query users
db.users.find().limit(5)

// Query products by category
db.products.find({ category: 'Electronics' })

// Aggregate orders by user
db.orders.aggregate([
  { $group: { _id: '$userId', totalSpent: { $sum: '$totalAmount' } } }
])
```

### Redis
```bash
# Set a key
SET mykey "Hello World"

# Get a key
GET mykey

# List all keys
KEYS *

# Set with expiration
SETEX session:123 3600 "user_data"

# Hash operations
HSET user:1 name "John" email "john@example.com"
HGETALL user:1
```

### Oracle
```sql
-- List tables
SELECT table_name FROM user_tables;

-- Query users
SELECT * FROM SYSTEM.users WHERE ROWNUM <= 5;

-- Query products by category
SELECT name, price, stock_quantity
FROM SYSTEM.products
WHERE category = 'Electronics';

-- Call stored procedure
DECLARE
  v_cursor SYS_REFCURSOR;
BEGIN
  SYSTEM.get_user_orders(1, v_cursor);
END;
/
```

## 🐛 Troubleshooting

### Services won't start
```bash
# Check Docker is running
docker info

# Check logs
./start.sh logs

# Check ports aren't in use
netstat -an | grep -E "5432|3307|27017|6379|1521"
```

### Oracle taking too long
```bash
# Oracle DB requires 2-3 minutes on first start
# Check progress:
docker logs -f aishell-oracle-test

# Look for: "DATABASE IS READY TO USE!"
```

### Connection refused
```bash
# Wait for service to be healthy
docker compose -f docker-compose.test.yml ps

# Test specific service
docker exec aishell-postgres-test pg_isready -U postgres
docker exec aishell-mysql-test mysqladmin ping
docker exec aishell-mongodb-test mongosh --eval "db.adminCommand('ping')"
docker exec aishell-redis-test redis-cli ping
```

### Out of memory
```bash
# Check resource usage
docker stats

# Increase Docker memory limit:
# Docker Desktop → Settings → Resources → Memory → Set to 8GB+
```

### Clean start
```bash
# Remove everything and start fresh
./start.sh clean
./start.sh up
```

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [MySQL Documentation](https://dev.mysql.com/doc/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [Redis Documentation](https://redis.io/documentation)
- [Oracle Database Free Documentation](https://docs.oracle.com/en/database/oracle/oracle-database/)

## ⚠️ Security Warning

**This configuration is for TESTING ONLY!**
- Uses hardcoded passwords
- No SSL/TLS encryption
- Admin interfaces without authentication
- Not suitable for production use

For production environments:
1. Use strong, unique passwords
2. Enable SSL/TLS
3. Restrict network access
4. Use secrets management
5. Enable database auditing
6. Regular security updates
