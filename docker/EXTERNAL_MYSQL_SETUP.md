# External MySQL Container Setup

## Overview

The AI-Shell test environment connects to an **external MySQL container** named `mysql` that should already be running on your system.

## Required MySQL Container Specifications

### Container Details
- **Container Name**: `mysql` (exactly)
- **Image**: `mysql:8` (or compatible)
- **Root Password**: `MyMySQLPass123`
- **Port Mapping**: `3307:3306` (host:container)

### Connection String
```
mysql://root:MyMySQLPass123@localhost:3307
```

## Verify Existing MySQL Container

Check if the MySQL container is already running:

```bash
# Check if container exists and is running
docker ps | grep mysql

# Should show something like:
# CONTAINER ID   IMAGE     PORTS                    NAMES
# abc123def456   mysql:8   0.0.0.0:3307->3306/tcp   mysql
```

## Connect to External MySQL Container

```bash
# Method 1: Using docker exec
docker exec -it mysql mysql -u root -pMyMySQLPass123

# Method 2: Using mysql client on host
mysql -h localhost -P 3307 -u root -pMyMySQLPass123

# Method 3: Using connection string
mysql mysql://root:MyMySQLPass123@localhost:3307
```

## Initialize Test Database (Optional)

If the external MySQL container doesn't have test data, you can initialize it:

```bash
# Copy init script to container
docker cp ./init-scripts/mysql/01-init.sql mysql:/tmp/

# Execute initialization script
docker exec -i mysql mysql -u root -pMyMySQLPass123 < ./init-scripts/mysql/01-init.sql

# Or directly from host
mysql -h localhost -P 3307 -u root -pMyMySQLPass123 < ./init-scripts/mysql/01-init.sql
```

## Test Connection

```bash
# Quick connection test
docker exec mysql mysqladmin ping -h localhost -u root -pMyMySQLPass123

# Expected output: mysqld is alive
```

## If MySQL Container Doesn't Exist

If you need to create the MySQL container:

```bash
docker run -d \
  --name mysql \
  -e MYSQL_ROOT_PASSWORD=MyMySQLPass123 \
  -e MYSQL_DATABASE=testdb \
  -p 3307:3306 \
  mysql:8
```

Wait for MySQL to be ready (30-60 seconds):

```bash
# Watch logs until you see "ready for connections"
docker logs -f mysql
```

## Network Considerations

### Option 1: External Container on Same Host
The MySQL container is accessible via `localhost:3307` from the host machine.

### Option 2: Connect to External Container via Docker Network
If you want the AI-Shell test containers to communicate with the external MySQL container:

```bash
# Connect external mysql container to the test network
docker network connect aishell-test-network mysql

# Now internal services can use: mysql://root:MyMySQLPass123@mysql:3306
```

## Troubleshooting

### Container Not Found
```bash
# List all containers (including stopped)
docker ps -a | grep mysql

# If stopped, start it
docker start mysql
```

### Port Already in Use
```bash
# Check what's using port 3307
lsof -i :3307

# If another process is using it, stop that process or use a different port
```

### Connection Refused
```bash
# Check if MySQL is listening
docker exec mysql mysqladmin ping -u root -pMyMySQLPass123

# Check MySQL logs
docker logs mysql
```

### Permission Denied
```bash
# Ensure root password is correct
docker exec mysql mysql -u root -pMyMySQLPass123 -e "SELECT 1"

# If needed, reset the password
docker exec mysql mysql -u root -pMyMySQLPass123 -e "ALTER USER 'root'@'%' IDENTIFIED BY 'MyMySQLPass123';"
```

## Integration with AI-Shell Tests

The AI-Shell integration tests will connect to the external MySQL container using:

```typescript
// Connection configuration in tests
const mysqlConfig = {
  host: 'localhost',
  port: 3307,
  user: 'root',
  password: 'MyMySQLPass123',
  database: 'testdb'
};
```

## Health Checks

The external MySQL container should respond to health checks:

```bash
# Manual health check
docker exec mysql mysqladmin ping -u root -pMyMySQLPass123

# Check from host
mysqladmin ping -h localhost -P 3307 -u root -pMyMySQLPass123
```

## Security Note

⚠️ **This configuration is for testing purposes only!**

- Simple password for development convenience
- Root access enabled
- No SSL/TLS encryption
- Port exposed to host

For production environments, use:
- Strong, random passwords
- Limited user privileges
- SSL/TLS encryption
- Firewall restrictions
- Secrets management

## Summary

The AI-Shell test environment expects an **external MySQL container** to exist with:
- Container name: `mysql`
- Root password: `MyMySQLPass123`
- Port: `3307` (host) → `3306` (container)
- Connection: `mysql://root:MyMySQLPass123@localhost:3307`

Ensure this container is running before executing AI-Shell database integration tests.
