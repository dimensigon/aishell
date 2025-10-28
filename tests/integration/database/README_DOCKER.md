# AI-Shell Database Docker Compose Guide

Complete Docker environment for testing all AI-Shell supported databases.

## 📦 Available Databases

### Core Databases (docker-compose.yml)
- **PostgreSQL 16** - Advanced relational database
- **MongoDB 7.0** - Document-oriented NoSQL database
- **MySQL 8.0** - Popular relational database
- **Redis 7.2** - In-memory data store
- **SQLite** - File-based database (no container needed)

### Optional Databases (docker-compose.full.yml)
- **Neo4j 5** - Graph database
- **Cassandra 4.1** - Wide-column NoSQL database
- **Oracle XE 21c** - Oracle Database Express Edition

### Management UIs (docker-compose.full.yml --profile ui)
- **pgAdmin** - PostgreSQL management (port 8084)
- **Mongo Express** - MongoDB management (port 8082)
- **phpMyAdmin** - MySQL management (port 8083)
- **Redis Commander** - Redis management (port 8081)

## 🚀 Quick Start

### 1. Start Core Databases

```bash
# Start all core databases
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop all databases
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### 2. Start with Management UIs

```bash
# Using docker-compose.full.yml with UI profile
docker-compose -f docker-compose.full.yml --profile ui up -d

# Access UIs:
# - pgAdmin: http://localhost:8084 (admin@aishell.com / admin123)
# - Mongo Express: http://localhost:8082 (admin / admin123)
# - phpMyAdmin: http://localhost:8083 (root / MyMySQLPass123)
# - Redis Commander: http://localhost:8081
```

### 3. Start with Optional Databases

```bash
# Start core + optional databases (without UIs)
docker-compose -f docker-compose.full.yml --profile optional up -d

# Start everything (core + optional + UIs)
docker-compose -f docker-compose.full.yml --profile optional --profile ui up -d
```

### 4. Individual Database Management

```bash
# Start specific database
docker-compose up -d postgres
docker-compose up -d mongodb
docker-compose up -d mysql
docker-compose up -d redis

# Stop specific database
docker-compose stop postgres

# Restart specific database
docker-compose restart mysql

# View logs for specific database
docker-compose logs -f postgres
```

## 🔌 Connection Strings

### PostgreSQL
```bash
# Standard connection
postgresql://postgres:MyPostgresPass123@localhost:5432/postgres

# With connection pool
postgresql://postgres:MyPostgresPass123@localhost:5432/postgres?max_connections=20

# Docker container to container
postgresql://postgres:MyPostgresPass123@postgres:5432/postgres
```

### MongoDB
```bash
# Standard connection
mongodb://admin:MyMongoPass123@localhost:27017/test_integration_db?authSource=admin

# Docker container to container
mongodb://admin:MyMongoPass123@mongodb:27017/test_integration_db?authSource=admin
```

### MySQL
```bash
# Standard connection
mysql://testuser:testpass@localhost:3306/test_integration_db

# Root user
mysql://root:MyMySQLPass123@localhost:3306/test_integration_db

# Docker container to container
mysql://testuser:testpass@mysql:3306/test_integration_db
```

### Redis
```bash
# Standard connection
redis://:MyRedisPass123@localhost:6379/0

# Docker container to container
redis://:MyRedisPass123@redis:6379/0
```

### SQLite
```bash
# File path (no container)
./test_integration.db
```

### Neo4j (Optional)
```bash
# Bolt protocol
bolt://neo4j:MyNeo4jPass123@localhost:7687

# HTTP
http://neo4j:MyNeo4jPass123@localhost:7474

# Web UI
http://localhost:7474/browser/
```

### Oracle (Optional)
```bash
# Connection string
testuser/testpass@localhost:1521/TESTDB

# JDBC
jdbc:oracle:thin:@localhost:1521/TESTDB
```

## 🛠️ Database Management Commands

### PostgreSQL
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres

# Run SQL file
docker-compose exec -T postgres psql -U postgres < your-script.sql

# Backup database
docker-compose exec -T postgres pg_dump -U postgres postgres > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres < backup.sql

# List databases
docker-compose exec postgres psql -U postgres -c "\l"

# List tables
docker-compose exec postgres psql -U postgres -d postgres -c "\dt"
```

### MongoDB
```bash
# Connect to MongoDB
docker-compose exec mongodb mongosh -u admin -p MyMongoPass123 --authenticationDatabase admin

# Run JavaScript file
docker-compose exec -T mongodb mongosh -u admin -p MyMongoPass123 --authenticationDatabase admin < your-script.js

# Backup database
docker-compose exec mongodb mongodump -u admin -p MyMongoPass123 --authenticationDatabase admin --out /backup

# Restore database
docker-compose exec mongodb mongorestore -u admin -p MyMongoPass123 --authenticationDatabase admin /backup

# List databases
docker-compose exec mongodb mongosh -u admin -p MyMongoPass123 --authenticationDatabase admin --eval "db.adminCommand('listDatabases')"
```

### MySQL
```bash
# Connect to MySQL
docker-compose exec mysql mysql -u root -pMyMySQLPass123

# Run SQL file
docker-compose exec -T mysql mysql -u root -pMyMySQLPass123 test_integration_db < your-script.sql

# Backup database
docker-compose exec mysql mysqldump -u root -pMyMySQLPass123 test_integration_db > backup.sql

# Restore database
docker-compose exec -T mysql mysql -u root -pMyMySQLPass123 test_integration_db < backup.sql

# List databases
docker-compose exec mysql mysql -u root -pMyMySQLPass123 -e "SHOW DATABASES;"

# List tables
docker-compose exec mysql mysql -u root -pMyMySQLPass123 -e "USE test_integration_db; SHOW TABLES;"
```

### Redis
```bash
# Connect to Redis
docker-compose exec redis redis-cli -a MyRedisPass123

# Monitor commands
docker-compose exec redis redis-cli -a MyRedisPass123 MONITOR

# Get info
docker-compose exec redis redis-cli -a MyRedisPass123 INFO

# Flush all data (CAREFUL!)
docker-compose exec redis redis-cli -a MyRedisPass123 FLUSHALL

# List all keys
docker-compose exec redis redis-cli -a MyRedisPass123 KEYS "*"
```

## 🔍 Health Checks

```bash
# Check all services health
docker-compose ps

# Detailed health status
docker inspect --format='{{json .State.Health}}' test_postgres | jq
docker inspect --format='{{json .State.Health}}' test_mongodb | jq
docker inspect --format='{{json .State.Health}}' test_mysql | jq
docker inspect --format='{{json .State.Health}}' test_redis | jq

# Wait for all services to be healthy
docker-compose up -d && \
  while [ "$(docker-compose ps -q | xargs docker inspect --format='{{.State.Health.Status}}' | grep -v healthy | wc -l)" != "0" ]; do \
    echo "Waiting for services to be healthy..."; \
    sleep 2; \
  done && \
  echo "All services are healthy!"
```

## 📊 Data Volumes

### List Volumes
```bash
docker volume ls | grep aishell
```

### Volume Locations
- **PostgreSQL**: `aishell_postgres_test_data`
- **MongoDB**: `aishell_mongodb_test_data`
- **MySQL**: `aishell_mysql_test_data`
- **Redis**: `aishell_redis_test_data`
- **Neo4j**: `aishell_neo4j_test_data`
- **Cassandra**: `aishell_cassandra_test_data`
- **Oracle**: `aishell_oracle_test_data`

### Volume Management
```bash
# Inspect volume
docker volume inspect aishell_postgres_test_data

# Backup volume
docker run --rm -v aishell_postgres_test_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volume
docker run --rm -v aishell_postgres_test_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data

# Remove all volumes (CAREFUL!)
docker-compose down -v
```

## 🧪 Running Tests

### Run All Integration Tests
```bash
# Start databases
docker-compose up -d

# Wait for healthy status
sleep 10

# Run tests
npm run test:integration

# Or specific database tests
npm test -- postgres.integration.test.ts
npm test -- mongodb.integration.test.ts
npm test -- mysql.integration.test.ts
npm test -- redis.integration.test.ts
```

### Run Test Verification Script
```bash
# Create and run test verification
python3 tests/integration/database/test_docker_setup.py
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process using port
sudo lsof -i :5432  # PostgreSQL
sudo lsof -i :27017 # MongoDB
sudo lsof -i :3306  # MySQL
sudo lsof -i :6379  # Redis

# Kill process or change port in docker-compose.yml
# Example: "5433:5432" maps container port 5432 to host port 5433
```

### Container Won't Start
```bash
# View detailed logs
docker-compose logs <service-name>

# Remove and recreate container
docker-compose rm -f <service-name>
docker-compose up -d <service-name>

# Check container resources
docker stats
```

### Database Connection Issues
```bash
# Verify network
docker network inspect aishell_test_network

# Test connectivity from another container
docker run --rm --network aishell_test_network alpine ping postgres
docker run --rm --network aishell_test_network alpine ping mongodb
docker run --rm --network aishell_test_network alpine ping mysql
docker run --rm --network aishell_test_network alpine ping redis
```

### Permission Issues
```bash
# Fix volume permissions
docker-compose down
sudo chown -R $(id -u):$(id -g) ./data

# Or remove volumes and recreate
docker-compose down -v
docker-compose up -d
```

### Out of Disk Space
```bash
# Clean up Docker system
docker system df
docker system prune -a --volumes

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune
```

## 🔒 Security Notes

### ⚠️ These are TEST credentials only!

**NEVER use these passwords in production:**
- PostgreSQL: `MyPostgresPass123`
- MongoDB: `MyMongoPass123`
- MySQL: `MyMySQLPass123`
- Redis: `MyRedisPass123`

### Production Security Checklist
- [ ] Change all default passwords
- [ ] Use environment variables for credentials
- [ ] Enable SSL/TLS connections
- [ ] Configure firewall rules
- [ ] Use Docker secrets for sensitive data
- [ ] Enable authentication on all services
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Implement backup strategies

## 📈 Performance Tuning

### PostgreSQL
```yaml
# Add to postgres service in docker-compose.yml
command: >
  postgres
  -c shared_buffers=256MB
  -c max_connections=200
  -c effective_cache_size=1GB
```

### MySQL
```yaml
# Add to mysql service in docker-compose.yml
command: >
  --max_connections=200
  --innodb_buffer_pool_size=256M
  --query_cache_size=32M
```

### MongoDB
```yaml
# Add to mongodb service environment
environment:
  MONGO_INITDB_ROOT_USERNAME: admin
  MONGO_INITDB_ROOT_PASSWORD: MyMongoPass123
  wiredTigerCacheSizeGB: 1
```

### Redis
```yaml
# Add to redis command
command: >
  redis-server
  --requirepass MyRedisPass123
  --maxmemory 512mb
  --maxmemory-policy allkeys-lru
  --save 900 1
  --save 300 10
```

## 📚 Additional Resources

- [PostgreSQL Docker Documentation](https://hub.docker.com/_/postgres)
- [MongoDB Docker Documentation](https://hub.docker.com/_/mongo)
- [MySQL Docker Documentation](https://hub.docker.com/_/mysql)
- [Redis Docker Documentation](https://hub.docker.com/_/redis)
- [Neo4j Docker Documentation](https://hub.docker.com/_/neo4j)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

## 🤝 Contributing

To add a new database to the integration tests:

1. Add service to `docker-compose.full.yml`
2. Create initialization script (e.g., `init-newdb.sql`)
3. Add connection details to `.env.docker`
4. Create integration test file
5. Update this README
6. Update main `README.md` with testing instructions

## 📝 License

This configuration is part of the AI-Shell project.
