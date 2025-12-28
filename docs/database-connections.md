# Database Connection Management

AI-Shell provides a powerful database connection manager that supports multiple database types with connection pooling, health checking, and automatic reconnection.

## Supported Databases

- **PostgreSQL** - Full SQL support with connection pooling
- **MySQL** - Full SQL support with connection pooling
- **MongoDB** - NoSQL document database
- **Redis** - In-memory key-value store
- **SQLite** - Embedded file-based database

## Quick Start

### Connect to a Database

```bash
# PostgreSQL
ai-shell connect postgresql://user:password@localhost:5432/mydb --name production

# MySQL
ai-shell connect mysql://root:secret@localhost:3306/testdb --name staging

# MongoDB
ai-shell connect mongodb://localhost:27017/appdb --name mongo

# Redis
ai-shell connect redis://localhost:6379 --name cache

# SQLite
ai-shell connect sqlite:///path/to/database.db --name local
```

### Test Connection Before Saving

```bash
ai-shell connect postgresql://user:pass@localhost:5432/mydb --test
```

### List Active Connections

```bash
# Basic list
ai-shell connections

# With health checks
ai-shell connections --health

# Verbose output with statistics
ai-shell connections --verbose
```

### Switch Active Connection

```bash
ai-shell use production
```

### Disconnect

```bash
# Disconnect specific connection
ai-shell disconnect production

# Disconnect all connections
ai-shell disconnect
```

## Connection String Format

### PostgreSQL

```
postgresql://[user[:password]@][host][:port][/database][?options]
postgres://[user[:password]@][host][:port][/database][?options]
```

Examples:
```bash
postgresql://localhost/mydb
postgresql://user:pass@localhost:5432/mydb
postgresql://user:pass@localhost/mydb?ssl=true
```

### MySQL

```
mysql://[user[:password]@][host][:port][/database][?options]
```

Examples:
```bash
mysql://localhost:3306/mydb
mysql://root:password@localhost/testdb
```

### MongoDB

```
mongodb://[username:password@]host[:port][/database][?options]
mongodb+srv://[username:password@]host[/database][?options]
```

Examples:
```bash
mongodb://localhost:27017/appdb
mongodb://user:pass@localhost:27017/appdb
mongodb+srv://cluster.mongodb.net/mydb
```

### Redis

```
redis://[:password@]host[:port][/database]
rediss://[:password@]host[:port][/database]  # SSL
```

Examples:
```bash
redis://localhost:6379
redis://:password@localhost:6379/0
rediss://secure-host:6380  # SSL connection
```

### SQLite

```
sqlite://[path/to/database.db]
sqlite://:memory:  # In-memory database
```

Examples:
```bash
sqlite:///absolute/path/to/db.sqlite
sqlite://./relative/path/to/db.sqlite
sqlite://:memory:
```

## Environment Variables

Set a default database connection:

```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/mydb"
```

## Configuration File

Create `~/.ai-shell/config.yaml`:

```yaml
databases:
  production:
    type: postgresql
    host: prod-db.example.com
    port: 5432
    database: production_db
    username: app_user
    ssl: true
    poolSize: 20

  staging:
    type: mysql
    host: staging-db.example.com
    port: 3306
    database: staging_db
    username: app_user
    poolSize: 10

  cache:
    type: redis
    host: redis.example.com
    port: 6379
    database: 0
    ssl: true
```

Load connections from config:

```bash
ai-shell load-config ~/.ai-shell/config.yaml
```

## Connection Management Features

### Connection Pooling

All database connections use connection pooling for optimal performance:

- **PostgreSQL**: Default pool size of 10 connections
- **MySQL**: Default pool size of 10 connections
- **MongoDB**: Default pool size of 10 connections
- **Redis**: Connection multiplexing with automatic pipelining

Configure pool size:

```bash
ai-shell connect postgresql://localhost/mydb --name prod --pool-size 20
```

### Health Checking

Automatic health checks run every 30 seconds to ensure connection stability:

```bash
# Manual health check for all connections
ai-shell connections --health

# Check specific connection
ai-shell health-check production
```

### Automatic Reconnection

If a connection fails health check, the manager automatically attempts to reconnect:

```typescript
// The connection manager handles reconnection automatically
// You'll see events in the logs:
// "Health check failed, attempting reconnection"
// "Reconnection successful"
```

### Connection Events

Monitor connection events:

```typescript
import { DatabaseConnectionManager } from './database-manager';

const manager = new DatabaseConnectionManager(stateManager);

manager.on('connected', (name) => {
  console.log(`Connected: ${name}`);
});

manager.on('disconnected', (name) => {
  console.log(`Disconnected: ${name}`);
});

manager.on('healthCheckFailed', (name, error) => {
  console.log(`Health check failed for ${name}: ${error.message}`);
});

manager.on('reconnecting', (name) => {
  console.log(`Reconnecting: ${name}`);
});

manager.on('reconnected', (name) => {
  console.log(`Reconnected: ${name}`);
});
```

## Programmatic Usage

### TypeScript/JavaScript API

```typescript
import { DatabaseConnectionManager, DatabaseType } from './database-manager';
import { StateManager } from '../core/state-manager';

const manager = new DatabaseConnectionManager(new StateManager());

// Connect
const connection = await manager.connect({
  name: 'my-db',
  type: DatabaseType.POSTGRESQL,
  host: 'localhost',
  port: 5432,
  database: 'mydb',
  username: 'user',
  password: 'pass',
  poolSize: 15
});

// Execute queries
const results = await manager.executeQuery(
  'SELECT * FROM users WHERE active = $1',
  [true]
);

// Health check
const health = await manager.healthCheck('my-db');
console.log(`Healthy: ${health.healthy}, Latency: ${health.latency}ms`);

// Get statistics
const stats = manager.getStatistics();
console.log(`Total connections: ${stats.totalConnections}`);
console.log(`Healthy connections: ${stats.healthyConnections}`);

// Disconnect
await manager.disconnect('my-db');
```

### Parse Connection Strings

```typescript
const parsed = DatabaseConnectionManager.parseConnectionString(
  'postgresql://user:pass@localhost:5432/mydb'
);

console.log(parsed);
// {
//   type: 'postgresql',
//   host: 'localhost',
//   port: 5432,
//   database: 'mydb',
//   username: 'user',
//   password: 'pass',
//   connectionString: '...'
// }
```

## Best Practices

### 1. Use Named Connections

Always use meaningful names for connections:

```bash
ai-shell connect postgresql://localhost/mydb --name production
ai-shell connect postgresql://localhost/testdb --name staging
```

### 2. Test Connections First

Test connections before saving them:

```bash
ai-shell connect postgresql://user:pass@host/db --test
```

### 3. Use Environment Variables

Store sensitive credentials in environment variables:

```bash
export DB_PASSWORD="secret"
ai-shell connect postgresql://user:$DB_PASSWORD@localhost/mydb
```

### 4. Monitor Health

Regularly check connection health:

```bash
ai-shell connections --health
```

### 5. Clean Up Connections

Disconnect unused connections:

```bash
ai-shell disconnect staging
```

## Security Considerations

### Password Storage

Passwords are **never** stored in the state file. You must provide credentials:

1. Via connection string at connect time
2. Via environment variables
3. Via config file (with restricted permissions)

### Config File Permissions

Secure your config file:

```bash
chmod 600 ~/.ai-shell/config.yaml
```

### SSL/TLS Connections

Use SSL for production databases:

```bash
# PostgreSQL with SSL
ai-shell connect postgresql://host/db?ssl=true

# Redis with SSL
ai-shell connect rediss://host:6380

# MongoDB with SSL
ai-shell connect mongodb+srv://cluster.mongodb.net/db
```

## Troubleshooting

### Connection Refused

```
Error: connect ECONNREFUSED 127.0.0.1:5432
```

**Solutions:**
- Verify database server is running
- Check firewall rules
- Verify host and port are correct

### Authentication Failed

```
Error: authentication failed for user "myuser"
```

**Solutions:**
- Verify username and password
- Check database user permissions
- For PostgreSQL, check `pg_hba.conf`

### Health Check Failures

```
Health check failed: timeout
```

**Solutions:**
- Check network connectivity
- Increase timeout settings
- Verify database isn't overloaded

### Pool Exhaustion

```
Error: connection pool exhausted
```

**Solutions:**
- Increase pool size
- Check for connection leaks
- Ensure connections are released after use

## Examples

### Multi-Database Workflow

```bash
# Connect to multiple databases
ai-shell connect postgresql://localhost/prod --name prod-db
ai-shell connect mongodb://localhost/analytics --name analytics-db
ai-shell connect redis://localhost:6379 --name cache-db

# List all connections
ai-shell connections --verbose

# Switch between databases
ai-shell use prod-db
ai-shell optimize "SELECT * FROM users"

ai-shell use analytics-db
# Work with MongoDB

ai-shell use cache-db
# Work with Redis
```

### Health Monitoring

```bash
# Set up monitoring script
while true; do
  ai-shell connections --health
  sleep 60
done
```

### Backup Across Databases

```bash
# Backup production
ai-shell use prod-db
ai-shell backup --connection prod-db

# Backup staging
ai-shell use staging-db
ai-shell backup --connection staging-db

# List all backups
ai-shell backup-list
```

## Advanced Topics

### Custom Health Check Intervals

Configure in TypeScript:

```typescript
// Change health check interval to 60 seconds
manager['healthCheckIntervalMs'] = 60000;
```

### Connection Lifecycle Hooks

```typescript
manager.on('connected', async (name) => {
  // Run setup queries
  const conn = manager.getConnection(name);
  // Set timezone, session variables, etc.
});
```

### Dynamic Connection Management

```typescript
// Load connections from API
const connections = await fetchConnectionsFromAPI();

for (const config of connections) {
  await manager.connect(config);
}
```

## See Also

- [Query Optimization](./query-optimization.md)
- [Backup System](./backup-system.md)
- [Health Monitoring](./health-monitoring.md)
- [Security Best Practices](./security.md)
