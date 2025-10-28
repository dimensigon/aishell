/**
 * Database Connection Examples
 * Demonstrates how to use the DatabaseConnectionManager programmatically
 */

import { DatabaseConnectionManager, DatabaseType, ConnectionConfig } from '../src/cli/database-manager';
import { StateManager } from '../src/core/state-manager';

// ============================================================================
// Example 1: Basic PostgreSQL Connection
// ============================================================================

async function example1_basicPostgreSQL() {
  const manager = new DatabaseConnectionManager(new StateManager());

  // Connect using connection config
  await manager.connect({
    name: 'my-postgres',
    type: DatabaseType.POSTGRESQL,
    host: 'localhost',
    port: 5432,
    database: 'myapp',
    username: 'postgres',
    password: 'secret',
    poolSize: 20
  });

  // Execute a query
  const users = await manager.executeQuery('SELECT * FROM users LIMIT 10');
  console.log(`Found ${users.length} users`);

  // Cleanup
  await manager.disconnect('my-postgres');
}

// ============================================================================
// Example 2: Connection String Parsing
// ============================================================================

async function example2_connectionStringParsing() {
  const manager = new DatabaseConnectionManager(new StateManager());

  // Parse connection string
  const parsed = DatabaseConnectionManager.parseConnectionString(
    'postgresql://user:pass@prod-db.example.com:5432/production?ssl=true'
  );

  console.log('Parsed connection:', {
    type: parsed.type,
    host: parsed.host,
    port: parsed.port,
    database: parsed.database,
    ssl: parsed.ssl
  });

  // Connect using parsed config
  await manager.connect({
    ...parsed as ConnectionConfig,
    name: 'production'
  });

  await manager.disconnect('production');
}

// ============================================================================
// Example 3: Multiple Database Connections
// ============================================================================

async function example3_multipleConnections() {
  const manager = new DatabaseConnectionManager(new StateManager());

  // Connect to multiple databases
  await manager.connect({
    name: 'postgres-prod',
    type: DatabaseType.POSTGRESQL,
    connectionString: 'postgresql://localhost:5432/prod'
  });

  await manager.connect({
    name: 'mongo-analytics',
    type: DatabaseType.MONGODB,
    connectionString: 'mongodb://localhost:27017/analytics'
  });

  await manager.connect({
    name: 'redis-cache',
    type: DatabaseType.REDIS,
    connectionString: 'redis://localhost:6379'
  });

  // List all connections
  const connections = manager.listConnections();
  console.log(`Total connections: ${connections.length}`);
  connections.forEach(conn => {
    console.log(`- ${conn.name} (${conn.type}) - Active: ${conn.isActive}`);
  });

  // Switch active connection
  await manager.switchActive('mongo-analytics');
  console.log('Switched to MongoDB');

  // Get statistics
  const stats = manager.getStatistics();
  console.log('Statistics:', stats);

  // Cleanup
  await manager.disconnectAll();
}

// ============================================================================
// Example 4: Health Checking
// ============================================================================

async function example4_healthChecking() {
  const manager = new DatabaseConnectionManager(new StateManager());

  await manager.connect({
    name: 'test-db',
    type: DatabaseType.SQLITE,
    database: ':memory:'
  });

  // Perform health check
  const health = await manager.healthCheck('test-db');

  if (health.healthy) {
    console.log(`Connection healthy! Latency: ${health.latency}ms`);
  } else {
    console.error(`Connection unhealthy: ${health.error}`);
  }

  await manager.disconnect('test-db');
}

// ============================================================================
// Example 5: Event Handling
// ============================================================================

async function example5_eventHandling() {
  const manager = new DatabaseConnectionManager(new StateManager());

  // Set up event listeners
  manager.on('connected', (name) => {
    console.log(`✅ Connected: ${name}`);
  });

  manager.on('disconnected', (name) => {
    console.log(`❌ Disconnected: ${name}`);
  });

  manager.on('activeChanged', (name) => {
    console.log(`🔄 Active connection changed to: ${name}`);
  });

  manager.on('healthCheckFailed', (name, error) => {
    console.error(`⚠️  Health check failed for ${name}: ${error.message}`);
  });

  manager.on('reconnecting', (name) => {
    console.log(`🔌 Reconnecting: ${name}`);
  });

  manager.on('reconnected', (name) => {
    console.log(`✅ Reconnected: ${name}`);
  });

  // Connect and trigger events
  await manager.connect({
    name: 'event-test',
    type: DatabaseType.SQLITE,
    database: ':memory:'
  });

  await manager.switchActive('event-test');
  await manager.disconnect('event-test');
}

// ============================================================================
// Example 6: Test Connection Before Saving
// ============================================================================

async function example6_testConnection() {
  const manager = new DatabaseConnectionManager(new StateManager());

  const testConfig: ConnectionConfig = {
    name: 'test-connection',
    type: DatabaseType.POSTGRESQL,
    host: 'prod-db.example.com',
    port: 5432,
    database: 'production',
    username: 'app_user',
    password: 'secret',
    ssl: true
  };

  // Test without saving
  const result = await manager.testConnection(testConfig);

  if (result.healthy) {
    console.log('✅ Connection test successful!');
    console.log(`   Latency: ${result.latency}ms`);

    // Now save it
    await manager.connect(testConfig);
    console.log('Connection saved');
  } else {
    console.error('❌ Connection test failed:', result.error);
  }

  // Verify no connections saved from failed test
  const connections = manager.listConnections();
  console.log(`Connections saved: ${connections.length}`);
}

// ============================================================================
// Example 7: Redis Connection with Configuration
// ============================================================================

async function example7_redisConnection() {
  const manager = new DatabaseConnectionManager(new StateManager());

  await manager.connect({
    name: 'redis-prod',
    type: DatabaseType.REDIS,
    host: 'redis.example.com',
    port: 6380,
    password: 'redis-secret',
    ssl: true,
    options: {
      db: 0,
      retryStrategy: (times: number) => Math.min(times * 50, 2000),
      maxRetriesPerRequest: 5
    }
  });

  // Get Redis client from connection
  const connection = manager.getConnection('redis-prod');
  if (connection) {
    // Redis client is available as connection.client
    // Can be used for Redis-specific operations
    console.log('Redis connection ready');
  }

  await manager.disconnect('redis-prod');
}

// ============================================================================
// Example 8: MongoDB Connection
// ============================================================================

async function example8_mongoDBConnection() {
  const manager = new DatabaseConnectionManager(new StateManager());

  await manager.connect({
    name: 'mongo-app',
    type: DatabaseType.MONGODB,
    connectionString: 'mongodb+srv://cluster.mongodb.net/myapp',
    username: 'app_user',
    password: 'mongo-secret',
    poolSize: 15,
    options: {
      retryWrites: true,
      retryReads: true,
      serverSelectionTimeoutMS: 5000
    }
  });

  const connection = manager.getConnection('mongo-app');
  if (connection) {
    // MongoDB client is available
    console.log('MongoDB connection ready');
  }

  await manager.disconnect('mongo-app');
}

// ============================================================================
// Example 9: SQLite In-Memory Database
// ============================================================================

async function example9_sqliteInMemory() {
  const manager = new DatabaseConnectionManager(new StateManager());

  // Create in-memory database
  await manager.connect({
    name: 'temp-db',
    type: DatabaseType.SQLITE,
    database: ':memory:'
  });

  // Create table and insert data
  await manager.executeQuery(`
    CREATE TABLE users (
      id INTEGER PRIMARY KEY,
      name TEXT NOT NULL,
      email TEXT UNIQUE
    )
  `);

  await manager.executeQuery(
    'INSERT INTO users (name, email) VALUES (?, ?)',
    ['John Doe', 'john@example.com']
  );

  // Query data
  const users = await manager.executeQuery('SELECT * FROM users');
  console.log('Users:', users);

  await manager.disconnect('temp-db');
}

// ============================================================================
// Example 10: Error Handling
// ============================================================================

async function example10_errorHandling() {
  const manager = new DatabaseConnectionManager(new StateManager());

  try {
    // Attempt to connect to invalid host
    await manager.connect({
      name: 'bad-connection',
      type: DatabaseType.POSTGRESQL,
      host: 'invalid-host-12345',
      port: 5432,
      database: 'test',
      username: 'user',
      password: 'pass'
    });
  } catch (error) {
    console.error('Expected error:', error instanceof Error ? error.message : error);
  }

  try {
    // Attempt to switch to non-existent connection
    await manager.switchActive('non-existent');
  } catch (error) {
    console.error('Expected error:', error instanceof Error ? error.message : error);
  }

  // Graceful disconnect of non-existent connection (no error)
  await manager.disconnect('non-existent');
  console.log('Graceful disconnect completed');
}

// ============================================================================
// Example 11: Connection Statistics and Monitoring
// ============================================================================

async function example11_monitoringStatistics() {
  const manager = new DatabaseConnectionManager(new StateManager());

  // Create multiple connections
  await manager.connect({
    name: 'db1',
    type: DatabaseType.SQLITE,
    database: ':memory:'
  });

  await manager.connect({
    name: 'db2',
    type: DatabaseType.SQLITE,
    database: ':memory:'
  });

  await manager.connect({
    name: 'db3',
    type: DatabaseType.SQLITE,
    database: ':memory:'
  });

  // Run health checks
  console.log('\nHealth Check Results:');
  for (const conn of manager.listConnections()) {
    const health = await manager.healthCheck(conn.name);
    console.log(`- ${conn.name}: ${health.healthy ? '✅' : '❌'} (${health.latency}ms)`);
  }

  // Get statistics
  const stats = manager.getStatistics();
  console.log('\nConnection Statistics:');
  console.log(`  Total: ${stats.totalConnections}`);
  console.log(`  Healthy: ${stats.healthyConnections}`);
  console.log(`  Active: ${stats.activeConnection}`);
  console.log('  By Type:', stats.connectionsByType);

  await manager.disconnectAll();
}

// ============================================================================
// Example 12: Advanced MySQL Configuration
// ============================================================================

async function example12_advancedMySQLConfig() {
  const manager = new DatabaseConnectionManager(new StateManager());

  await manager.connect({
    name: 'mysql-prod',
    type: DatabaseType.MYSQL,
    host: 'mysql.example.com',
    port: 3306,
    database: 'production',
    username: 'app_user',
    password: 'mysql-secret',
    ssl: true,
    poolSize: 25,
    options: {
      waitForConnections: true,
      queueLimit: 0,
      enableKeepAlive: true,
      keepAliveInitialDelay: 0
    }
  });

  // Execute query with parameters
  const results = await manager.executeQuery(
    'SELECT * FROM users WHERE status = ? AND created_at > ?',
    ['active', new Date('2024-01-01')]
  );

  console.log(`Found ${results.length} active users`);

  await manager.disconnect('mysql-prod');
}

// ============================================================================
// Main execution
// ============================================================================

async function main() {
  console.log('='.repeat(80));
  console.log('Database Connection Manager Examples');
  console.log('='.repeat(80));

  const examples = [
    { name: 'Basic PostgreSQL Connection', fn: example1_basicPostgreSQL },
    { name: 'Connection String Parsing', fn: example2_connectionStringParsing },
    { name: 'Multiple Database Connections', fn: example3_multipleConnections },
    { name: 'Health Checking', fn: example4_healthChecking },
    { name: 'Event Handling', fn: example5_eventHandling },
    { name: 'Test Connection', fn: example6_testConnection },
    { name: 'Redis Connection', fn: example7_redisConnection },
    { name: 'MongoDB Connection', fn: example8_mongoDBConnection },
    { name: 'SQLite In-Memory', fn: example9_sqliteInMemory },
    { name: 'Error Handling', fn: example10_errorHandling },
    { name: 'Monitoring & Statistics', fn: example11_monitoringStatistics },
    { name: 'Advanced MySQL Config', fn: example12_advancedMySQLConfig }
  ];

  for (const example of examples) {
    console.log(`\n${'='.repeat(80)}`);
    console.log(`Example: ${example.name}`);
    console.log('='.repeat(80));

    try {
      await example.fn();
      console.log('✅ Example completed successfully');
    } catch (error) {
      console.error('❌ Example failed:', error);
    }
  }

  console.log(`\n${'='.repeat(80)}`);
  console.log('All examples completed!');
  console.log('='.repeat(80));
}

// Run examples if executed directly
if (require.main === module) {
  main().catch(console.error);
}

export {
  example1_basicPostgreSQL,
  example2_connectionStringParsing,
  example3_multipleConnections,
  example4_healthChecking,
  example5_eventHandling,
  example6_testConnection,
  example7_redisConnection,
  example8_mongoDBConnection,
  example9_sqliteInMemory,
  example10_errorHandling,
  example11_monitoringStatistics,
  example12_advancedMySQLConfig
};
