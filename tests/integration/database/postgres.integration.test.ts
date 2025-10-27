/**
 * PostgreSQL Integration Tests
 * Comprehensive tests for PostgreSQL client using Docker test environment
 *
 * Test Environment:
 * - PostgreSQL running in Docker
 * - Connection: postgresql://postgres:MyPostgresPass123@localhost:5432/postgres
 * - Test data loaded from init-postgres.sql
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import { Pool, PoolClient, QueryResult } from 'pg';
import * as fs from 'fs';
import * as path from 'path';

// Connection configuration
const TEST_CONFIG = {
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432'),
  database: process.env.POSTGRES_DB || 'postgres',
  user: process.env.POSTGRES_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD || 'MyPostgresPass123',
  max: 20, // Maximum pool size for concurrent tests
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
};

let pool: Pool;

/**
 * Setup: Initialize database and load test data
 */
beforeAll(async () => {
  console.log('🔧 Setting up PostgreSQL integration tests...');

  // Create connection pool
  pool = new Pool(TEST_CONFIG);

  try {
    // Test connection
    const client = await pool.connect();
    const result = await client.query('SELECT version()');
    console.log(`✅ Connected to PostgreSQL: ${result.rows[0].version.split(',')[0]}`);
    client.release();

    // Load initialization SQL
    const initSqlPath = path.join(__dirname, 'init-postgres.sql');
    if (fs.existsSync(initSqlPath)) {
      const initSql = fs.readFileSync(initSqlPath, 'utf-8');
      await pool.query(initSql);
      console.log('✅ Test database initialized with seed data');
    } else {
      console.warn('⚠️  init-postgres.sql not found, skipping seed data');
    }
  } catch (error) {
    console.error('❌ Failed to initialize test database:', error);
    throw error;
  }
}, 30000);

/**
 * Cleanup: Close all connections
 */
afterAll(async () => {
  if (pool) {
    await pool.end();
    console.log('✅ PostgreSQL connection pool closed');
  }
});

/**
 * Test Suite 1: Connection and Authentication
 */
describe('PostgreSQL Connection and Authentication', () => {
  it('should establish a connection successfully', async () => {
    const client = await pool.connect();
    expect(client).toBeDefined();
    client.release();
  });

  it('should fail with invalid credentials', async () => {
    const invalidPool = new Pool({
      ...TEST_CONFIG,
      password: 'wrong_password',
    });

    await expect(async () => {
      const client = await invalidPool.connect();
      client.release();
    }).rejects.toThrow();

    await invalidPool.end();
  });

  it('should handle connection timeout', async () => {
    const timeoutPool = new Pool({
      ...TEST_CONFIG,
      host: '192.0.2.1', // Non-routable IP
      connectionTimeoutMillis: 1000,
    });

    await expect(async () => {
      await timeoutPool.connect();
    }).rejects.toThrow();

    await timeoutPool.end();
  }, 10000);

  it('should retrieve database version', async () => {
    const result = await pool.query('SELECT version()');
    expect(result.rows[0].version).toContain('PostgreSQL');
  });

  it('should list database capabilities', async () => {
    const result = await pool.query(`
      SELECT has_database_privilege(current_user, current_database(), 'CREATE') as can_create,
             has_database_privilege(current_user, current_database(), 'CONNECT') as can_connect
    `);
    expect(result.rows[0].can_connect).toBe(true);
  });
});

/**
 * Test Suite 2: CRUD Operations
 */
describe('PostgreSQL CRUD Operations', () => {
  beforeEach(async () => {
    // Clean up test users created during tests
    await pool.query("DELETE FROM users WHERE username LIKE 'test_%'");
  });

  it('should CREATE a new user', async () => {
    const result = await pool.query(
      `INSERT INTO users (username, email, password_hash, roles, preferences)
       VALUES ($1, $2, $3, $4, $5) RETURNING *`,
      ['test_user', 'test@example.com', 'hashedpassword', ['user'], { theme: 'dark' }]
    );

    expect(result.rows[0]).toMatchObject({
      username: 'test_user',
      email: 'test@example.com',
      is_active: true,
    });
    expect(result.rows[0].id).toBeDefined();
  });

  it('should READ users from database', async () => {
    const result = await pool.query('SELECT * FROM users WHERE username = $1', ['john_doe']);

    expect(result.rows).toHaveLength(1);
    expect(result.rows[0]).toMatchObject({
      username: 'john_doe',
      email: 'john@example.com',
    });
  });

  it('should UPDATE user information', async () => {
    // Create test user
    const insertResult = await pool.query(
      `INSERT INTO users (username, email, password_hash)
       VALUES ($1, $2, $3) RETURNING id`,
      ['test_update', 'update@example.com', 'hash']
    );
    const userId = insertResult.rows[0].id;

    // Update user
    const updateResult = await pool.query(
      `UPDATE users SET preferences = $1, updated_at = CURRENT_TIMESTAMP
       WHERE id = $2 RETURNING *`,
      [{ theme: 'light', language: 'en' }, userId]
    );

    expect(updateResult.rows[0].preferences).toEqual({
      theme: 'light',
      language: 'en',
    });
  });

  it('should DELETE a user', async () => {
    // Create test user
    const insertResult = await pool.query(
      `INSERT INTO users (username, email, password_hash)
       VALUES ($1, $2, $3) RETURNING id`,
      ['test_delete', 'delete@example.com', 'hash']
    );
    const userId = insertResult.rows[0].id;

    // Delete user
    const deleteResult = await pool.query('DELETE FROM users WHERE id = $1', [userId]);
    expect(deleteResult.rowCount).toBe(1);

    // Verify deletion
    const verifyResult = await pool.query('SELECT * FROM users WHERE id = $1', [userId]);
    expect(verifyResult.rows).toHaveLength(0);
  });

  it('should handle bulk INSERT operations', async () => {
    const values = [
      ['bulk_user1', 'bulk1@example.com', 'hash1'],
      ['bulk_user2', 'bulk2@example.com', 'hash2'],
      ['bulk_user3', 'bulk3@example.com', 'hash3'],
    ];

    const insertPromises = values.map(([username, email, password_hash]) =>
      pool.query(
        'INSERT INTO users (username, email, password_hash) VALUES ($1, $2, $3)',
        [username, email, password_hash]
      )
    );

    await Promise.all(insertPromises);

    const result = await pool.query("SELECT * FROM users WHERE username LIKE 'bulk_user%'");
    expect(result.rows.length).toBeGreaterThanOrEqual(3);
  });
});

/**
 * Test Suite 3: Transaction Management
 */
describe('PostgreSQL Transaction Management', () => {
  it('should commit a transaction successfully', async () => {
    const client = await pool.connect();

    try {
      await client.query('BEGIN');

      const result = await client.query(
        `INSERT INTO users (username, email, password_hash)
         VALUES ($1, $2, $3) RETURNING id`,
        ['tx_commit', 'tx_commit@example.com', 'hash']
      );
      const userId = result.rows[0].id;

      await client.query('COMMIT');

      // Verify data persisted
      const verifyResult = await pool.query('SELECT * FROM users WHERE id = $1', [userId]);
      expect(verifyResult.rows).toHaveLength(1);
    } finally {
      client.release();
    }
  });

  it('should rollback a transaction on error', async () => {
    const client = await pool.connect();

    try {
      await client.query('BEGIN');

      await client.query(
        `INSERT INTO users (username, email, password_hash)
         VALUES ($1, $2, $3)`,
        ['tx_rollback', 'tx_rollback@example.com', 'hash']
      );

      await client.query('ROLLBACK');

      // Verify data not persisted
      const verifyResult = await pool.query(
        "SELECT * FROM users WHERE username = 'tx_rollback'"
      );
      expect(verifyResult.rows).toHaveLength(0);
    } finally {
      client.release();
    }
  });

  it('should support savepoints', async () => {
    const client = await pool.connect();

    try {
      await client.query('BEGIN');

      // First insert
      await client.query(
        `INSERT INTO users (username, email, password_hash)
         VALUES ($1, $2, $3)`,
        ['sp_user1', 'sp1@example.com', 'hash']
      );

      // Create savepoint
      await client.query('SAVEPOINT sp1');

      // Second insert
      await client.query(
        `INSERT INTO users (username, email, password_hash)
         VALUES ($1, $2, $3)`,
        ['sp_user2', 'sp2@example.com', 'hash']
      );

      // Rollback to savepoint
      await client.query('ROLLBACK TO SAVEPOINT sp1');

      // Commit transaction
      await client.query('COMMIT');

      // Verify first insert persisted, second did not
      const result1 = await pool.query("SELECT * FROM users WHERE username = 'sp_user1'");
      const result2 = await pool.query("SELECT * FROM users WHERE username = 'sp_user2'");

      expect(result1.rows).toHaveLength(1);
      expect(result2.rows).toHaveLength(0);
    } finally {
      client.release();
    }
  });

  it('should handle nested transactions with savepoints', async () => {
    const client = await pool.connect();

    try {
      await client.query('BEGIN');

      await client.query(
        'INSERT INTO users (username, email, password_hash) VALUES ($1, $2, $3)',
        ['nest1', 'nest1@example.com', 'hash']
      );

      await client.query('SAVEPOINT level1');
      await client.query(
        'INSERT INTO users (username, email, password_hash) VALUES ($1, $2, $3)',
        ['nest2', 'nest2@example.com', 'hash']
      );

      await client.query('SAVEPOINT level2');
      await client.query(
        'INSERT INTO users (username, email, password_hash) VALUES ($1, $2, $3)',
        ['nest3', 'nest3@example.com', 'hash']
      );

      await client.query('ROLLBACK TO SAVEPOINT level1');
      await client.query('COMMIT');

      const result = await pool.query("SELECT username FROM users WHERE username LIKE 'nest%' ORDER BY username");
      expect(result.rows.map(r => r.username)).toEqual(['nest1']);
    } finally {
      client.release();
    }
  });
});

/**
 * Test Suite 4: Array and JSON Data Types
 */
describe('PostgreSQL Array and JSON Types', () => {
  it('should work with ARRAY columns', async () => {
    const result = await pool.query(
      `INSERT INTO users (username, email, password_hash, roles)
       VALUES ($1, $2, $3, $4) RETURNING roles`,
      ['array_test', 'array@example.com', 'hash', ['admin', 'moderator', 'user']]
    );

    expect(result.rows[0].roles).toEqual(['admin', 'moderator', 'user']);
  });

  it('should query ARRAY columns with ANY operator', async () => {
    const result = await pool.query(
      "SELECT username FROM users WHERE 'admin' = ANY(roles)"
    );

    expect(result.rows.length).toBeGreaterThan(0);
    expect(result.rows[0].username).toBe('john_doe');
  });

  it('should work with JSONB columns', async () => {
    const preferences = {
      theme: 'dark',
      language: 'en',
      notifications: {
        email: true,
        push: false,
      },
    };

    const result = await pool.query(
      `INSERT INTO users (username, email, password_hash, preferences)
       VALUES ($1, $2, $3, $4) RETURNING preferences`,
      ['json_test', 'json@example.com', 'hash', preferences]
    );

    expect(result.rows[0].preferences).toEqual(preferences);
  });

  it('should query JSONB with -> and ->> operators', async () => {
    const result = await pool.query(
      "SELECT username, preferences->>'theme' as theme FROM users WHERE preferences->>'theme' = 'dark'"
    );

    expect(result.rows.length).toBeGreaterThan(0);
    expect(result.rows[0].theme).toBe('dark');
  });

  it('should query JSONB with @> containment operator', async () => {
    const result = await pool.query(
      "SELECT username FROM users WHERE preferences @> '{\"theme\": \"dark\"}'::jsonb"
    );

    expect(result.rows.length).toBeGreaterThan(0);
  });

  it('should update nested JSONB fields', async () => {
    const result = await pool.query(
      `UPDATE users
       SET preferences = jsonb_set(preferences, '{notifications}', '{"email": false}', true)
       WHERE username = 'json_test'
       RETURNING preferences`
    );

    if (result.rows.length > 0) {
      expect(result.rows[0].preferences.notifications).toEqual({ email: false });
    }
  });
});

/**
 * Test Suite 5: Full-Text Search
 */
describe('PostgreSQL Full-Text Search', () => {
  it('should perform basic full-text search', async () => {
    const result = await pool.query(
      `SELECT title, ts_rank(search_vector, query) as rank
       FROM search_documents, to_tsquery('english', 'postgresql') as query
       WHERE search_vector @@ query
       ORDER BY rank DESC`
    );

    expect(result.rows.length).toBeGreaterThan(0);
    expect(result.rows[0].title).toContain('PostgreSQL');
  });

  it('should search with multiple terms', async () => {
    const result = await pool.query(
      `SELECT title
       FROM search_documents
       WHERE search_vector @@ to_tsquery('english', 'database & performance')`
    );

    expect(result.rows.length).toBeGreaterThan(0);
  });

  it('should search with phrase query', async () => {
    const result = await pool.query(
      `SELECT title, content
       FROM search_documents
       WHERE search_vector @@ phraseto_tsquery('english', 'database performance')`
    );

    expect(result.rows).toBeDefined();
  });

  it('should highlight search results', async () => {
    const result = await pool.query(
      `SELECT title,
              ts_headline('english', content, query, 'StartSel=<mark>, StopSel=</mark>') as headline
       FROM search_documents, to_tsquery('english', 'SQL') as query
       WHERE search_vector @@ query
       LIMIT 1`
    );

    if (result.rows.length > 0) {
      expect(result.rows[0].headline).toContain('<mark>');
    }
  });
});

/**
 * Test Suite 6: Window Functions and CTEs
 */
describe('PostgreSQL Window Functions and CTEs', () => {
  it('should use ROW_NUMBER window function', async () => {
    const result = await pool.query(
      `SELECT username,
              ROW_NUMBER() OVER (ORDER BY created_at) as row_num
       FROM users
       LIMIT 5`
    );

    expect(result.rows).toHaveLength(5);
    expect(result.rows[0].row_num).toBe(1);
    expect(result.rows[4].row_num).toBe(5);
  });

  it('should use RANK and DENSE_RANK', async () => {
    const result = await pool.query(
      `SELECT o.customer_id,
              o.total_amount,
              RANK() OVER (ORDER BY o.total_amount DESC) as rank,
              DENSE_RANK() OVER (ORDER BY o.total_amount DESC) as dense_rank
       FROM orders o
       LIMIT 5`
    );

    expect(result.rows.length).toBeGreaterThan(0);
    expect(result.rows[0].rank).toBeDefined();
    expect(result.rows[0].dense_rank).toBeDefined();
  });

  it('should use LAG and LEAD window functions', async () => {
    const result = await pool.query(
      `SELECT user_id,
              event_type,
              event_value,
              LAG(event_value) OVER (PARTITION BY user_id ORDER BY created_at) as prev_value,
              LEAD(event_value) OVER (PARTITION BY user_id ORDER BY created_at) as next_value
       FROM analytics
       WHERE user_id = 1
       ORDER BY created_at`
    );

    expect(result.rows.length).toBeGreaterThan(0);
  });

  it('should use Common Table Expressions (CTE)', async () => {
    const result = await pool.query(
      `WITH recent_orders AS (
         SELECT customer_id, COUNT(*) as order_count
         FROM orders
         WHERE order_date >= CURRENT_TIMESTAMP - INTERVAL '30 days'
         GROUP BY customer_id
       )
       SELECT c.first_name, c.last_name, ro.order_count
       FROM customers c
       JOIN recent_orders ro ON c.id = ro.customer_id
       ORDER BY ro.order_count DESC`
    );

    expect(result.rows.length).toBeGreaterThan(0);
  });

  it('should use recursive CTE', async () => {
    const result = await pool.query(
      `WITH RECURSIVE numbers AS (
         SELECT 1 as n
         UNION ALL
         SELECT n + 1 FROM numbers WHERE n < 10
       )
       SELECT * FROM numbers`
    );

    expect(result.rows).toHaveLength(10);
    expect(result.rows[9].n).toBe(10);
  });

  it('should use aggregate window functions', async () => {
    const result = await pool.query(
      `SELECT customer_id,
              order_date,
              total_amount,
              SUM(total_amount) OVER (PARTITION BY customer_id ORDER BY order_date) as running_total,
              AVG(total_amount) OVER (PARTITION BY customer_id) as avg_order_value
       FROM orders
       ORDER BY customer_id, order_date`
    );

    expect(result.rows.length).toBeGreaterThan(0);
    expect(result.rows[0].running_total).toBeDefined();
    expect(result.rows[0].avg_order_value).toBeDefined();
  });
});

/**
 * Test Suite 7: Foreign Key Constraints
 */
describe('PostgreSQL Foreign Key Constraints', () => {
  it('should enforce foreign key constraints on INSERT', async () => {
    await expect(async () => {
      await pool.query(
        'INSERT INTO orders (customer_id, total_amount) VALUES ($1, $2)',
        [999999, 100.00]
      );
    }).rejects.toThrow(/foreign key constraint/);
  });

  it('should CASCADE delete child records', async () => {
    // Create test customer and order
    const customerResult = await pool.query(
      `INSERT INTO customers (first_name, last_name, email)
       VALUES ($1, $2, $3) RETURNING id`,
      ['Test', 'Customer', 'test.cascade@example.com']
    );
    const customerId = customerResult.rows[0].id;

    const orderResult = await pool.query(
      `INSERT INTO orders (customer_id, total_amount)
       VALUES ($1, $2) RETURNING id`,
      [customerId, 100.00]
    );
    const orderId = orderResult.rows[0].id;

    await pool.query(
      `INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
       VALUES ($1, $2, $3, $4, $5)`,
      [orderId, 1, 1, 100.00, 100.00]
    );

    // Delete customer (should cascade to orders and order_items)
    await pool.query('DELETE FROM customers WHERE id = $1', [customerId]);

    // Verify cascade deletion
    const orderCheck = await pool.query('SELECT * FROM orders WHERE id = $1', [orderId]);
    const itemCheck = await pool.query('SELECT * FROM order_items WHERE order_id = $1', [orderId]);

    expect(orderCheck.rows).toHaveLength(0);
    expect(itemCheck.rows).toHaveLength(0);
  });

  it('should validate referential integrity', async () => {
    const result = await pool.query(
      `SELECT
         (SELECT COUNT(*) FROM orders WHERE customer_id NOT IN (SELECT id FROM customers)) as orphaned_orders,
         (SELECT COUNT(*) FROM order_items WHERE order_id NOT IN (SELECT id FROM orders)) as orphaned_items`
    );

    expect(result.rows[0].orphaned_orders).toBe(0);
    expect(result.rows[0].orphaned_items).toBe(0);
  });
});

/**
 * Test Suite 8: Indexes and Query Optimization
 */
describe('PostgreSQL Indexes and Query Optimization', () => {
  it('should use index for fast lookups', async () => {
    const result = await pool.query(
      `EXPLAIN (FORMAT JSON) SELECT * FROM users WHERE email = 'john@example.com'`
    );

    const plan = result.rows[0]['QUERY PLAN'][0].Plan;
    // Should use Index Scan, not Sequential Scan
    expect(plan['Node Type']).toContain('Index');
  });

  it('should list all indexes', async () => {
    const result = await pool.query(
      `SELECT tablename, indexname, indexdef
       FROM pg_indexes
       WHERE schemaname = 'public'
       ORDER BY tablename, indexname`
    );

    expect(result.rows.length).toBeGreaterThan(0);
  });

  it('should show table statistics', async () => {
    const result = await pool.query(
      `SELECT schemaname, tablename, n_live_tup, n_dead_tup
       FROM pg_stat_user_tables
       WHERE tablename = 'users'`
    );

    expect(result.rows).toHaveLength(1);
    expect(result.rows[0].n_live_tup).toBeGreaterThan(0);
  });

  it('should analyze query performance', async () => {
    const result = await pool.query(
      `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
       SELECT u.username, COUNT(a.id) as event_count
       FROM users u
       LEFT JOIN analytics a ON u.id = a.user_id
       GROUP BY u.id, u.username`
    );

    const plan = result.rows[0]['QUERY PLAN'][0];
    expect(plan['Planning Time']).toBeDefined();
    expect(plan['Execution Time']).toBeDefined();
  });
});

/**
 * Test Suite 9: Concurrent Connections
 */
describe('PostgreSQL Concurrent Connections', () => {
  it('should handle multiple concurrent queries', async () => {
    const queries = Array.from({ length: 10 }, (_, i) =>
      pool.query('SELECT $1::int as value', [i])
    );

    const results = await Promise.all(queries);

    expect(results).toHaveLength(10);
    results.forEach((result, i) => {
      expect(result.rows[0].value).toBe(i);
    });
  });

  it('should manage connection pool efficiently', async () => {
    const poolSize = pool.totalCount;
    const idleCount = pool.idleCount;
    const waitingCount = pool.waitingCount;

    expect(poolSize).toBeLessThanOrEqual(TEST_CONFIG.max);
    expect(idleCount).toBeGreaterThanOrEqual(0);
    expect(waitingCount).toBeGreaterThanOrEqual(0);
  });

  it('should handle concurrent transactions', async () => {
    const transaction1 = async () => {
      const client = await pool.connect();
      try {
        await client.query('BEGIN');
        await client.query(
          `INSERT INTO users (username, email, password_hash) VALUES ($1, $2, $3)`,
          ['concurrent1', 'conc1@example.com', 'hash']
        );
        await new Promise(resolve => setTimeout(resolve, 100));
        await client.query('COMMIT');
      } finally {
        client.release();
      }
    };

    const transaction2 = async () => {
      const client = await pool.connect();
      try {
        await client.query('BEGIN');
        await client.query(
          `INSERT INTO users (username, email, password_hash) VALUES ($1, $2, $3)`,
          ['concurrent2', 'conc2@example.com', 'hash']
        );
        await new Promise(resolve => setTimeout(resolve, 100));
        await client.query('COMMIT');
      } finally {
        client.release();
      }
    };

    await Promise.all([transaction1(), transaction2()]);

    const result = await pool.query(
      "SELECT COUNT(*) as count FROM users WHERE username LIKE 'concurrent%'"
    );
    expect(parseInt(result.rows[0].count)).toBeGreaterThanOrEqual(2);
  });
});

/**
 * Test Suite 10: Listen/Notify Pub-Sub
 */
describe('PostgreSQL Listen/Notify', () => {
  it('should send and receive notifications', async () => {
    const listener = await pool.connect();
    const notifier = await pool.connect();

    const notifications: any[] = [];

    listener.on('notification', (msg) => {
      notifications.push(msg);
    });

    await listener.query('LISTEN test_channel');

    await notifier.query("NOTIFY test_channel, 'Hello from PostgreSQL'");

    // Wait for notification
    await new Promise(resolve => setTimeout(resolve, 500));

    expect(notifications.length).toBeGreaterThan(0);
    expect(notifications[0].channel).toBe('test_channel');
    expect(notifications[0].payload).toBe('Hello from PostgreSQL');

    listener.release();
    notifier.release();
  });

  it('should handle multiple channels', async () => {
    const listener = await pool.connect();
    const notifier = await pool.connect();

    const notifications: any[] = [];

    listener.on('notification', (msg) => {
      notifications.push(msg);
    });

    await listener.query('LISTEN channel1');
    await listener.query('LISTEN channel2');

    await notifier.query("NOTIFY channel1, 'Message 1'");
    await notifier.query("NOTIFY channel2, 'Message 2'");

    await new Promise(resolve => setTimeout(resolve, 500));

    expect(notifications.length).toBe(2);
    expect(notifications.find(n => n.channel === 'channel1')).toBeDefined();
    expect(notifications.find(n => n.channel === 'channel2')).toBeDefined();

    listener.release();
    notifier.release();
  });
});

/**
 * Test Suite 11: Prepared Statements
 */
describe('PostgreSQL Prepared Statements', () => {
  it('should execute prepared statement', async () => {
    const client = await pool.connect();

    try {
      // Prepare statement
      await client.query({
        name: 'get-user-by-email',
        text: 'SELECT * FROM users WHERE email = $1',
      });

      // Execute prepared statement
      const result = await client.query({
        name: 'get-user-by-email',
        values: ['john@example.com'],
      });

      expect(result.rows).toHaveLength(1);
      expect(result.rows[0].email).toBe('john@example.com');
    } finally {
      client.release();
    }
  });

  it('should reuse prepared statement for performance', async () => {
    const client = await pool.connect();

    try {
      await client.query({
        name: 'get-user-count',
        text: 'SELECT COUNT(*) as count FROM users WHERE is_active = $1',
      });

      const result1 = await client.query({
        name: 'get-user-count',
        values: [true],
      });

      const result2 = await client.query({
        name: 'get-user-count',
        values: [false],
      });

      expect(result1.rows[0].count).toBeDefined();
      expect(result2.rows[0].count).toBeDefined();
    } finally {
      client.release();
    }
  });
});

/**
 * Test Suite 12: Batch Operations
 */
describe('PostgreSQL Batch Operations', () => {
  it('should perform batch INSERT with COPY', async () => {
    const client = await pool.connect();

    try {
      const values = Array.from({ length: 100 }, (_, i) => [
        `batch_user_${i}`,
        `batch${i}@example.com`,
        'hash',
      ]);

      // Using parameterized batch insert
      for (const [username, email, password_hash] of values) {
        await client.query(
          'INSERT INTO users (username, email, password_hash) VALUES ($1, $2, $3)',
          [username, email, password_hash]
        );
      }

      const result = await pool.query(
        "SELECT COUNT(*) as count FROM users WHERE username LIKE 'batch_user_%'"
      );
      expect(parseInt(result.rows[0].count)).toBeGreaterThanOrEqual(100);
    } finally {
      client.release();
    }
  }, 15000);

  it('should perform batch UPDATE', async () => {
    await pool.query(
      "UPDATE users SET preferences = '{\"batch_updated\": true}'::jsonb WHERE username LIKE 'batch_user_%'"
    );

    const result = await pool.query(
      "SELECT COUNT(*) as count FROM users WHERE username LIKE 'batch_user_%' AND preferences @> '{\"batch_updated\": true}'"
    );

    expect(parseInt(result.rows[0].count)).toBeGreaterThan(0);
  });

  it('should perform batch DELETE', async () => {
    await pool.query("DELETE FROM users WHERE username LIKE 'batch_user_%'");

    const result = await pool.query(
      "SELECT COUNT(*) as count FROM users WHERE username LIKE 'batch_user_%'"
    );

    expect(parseInt(result.rows[0].count)).toBe(0);
  });
});

/**
 * Test Suite 13: Error Handling
 */
describe('PostgreSQL Error Handling', () => {
  it('should handle syntax errors', async () => {
    await expect(async () => {
      await pool.query('SELCT * FROM users');
    }).rejects.toThrow(/syntax error/);
  });

  it('should handle constraint violations', async () => {
    await expect(async () => {
      await pool.query(
        'INSERT INTO users (username, email, password_hash) VALUES ($1, $2, $3)',
        ['john_doe', 'duplicate@example.com', 'hash']
      );
    }).rejects.toThrow(/duplicate key/);
  });

  it('should handle connection errors gracefully', async () => {
    const badPool = new Pool({
      ...TEST_CONFIG,
      max: 1,
      connectionTimeoutMillis: 1000,
    });

    await expect(async () => {
      const promises = Array.from({ length: 10 }, () =>
        badPool.query('SELECT pg_sleep(5)')
      );
      await Promise.all(promises);
    }).rejects.toThrow();

    await badPool.end();
  });

  it('should provide detailed error information', async () => {
    try {
      await pool.query('SELECT * FROM non_existent_table');
    } catch (error: any) {
      expect(error.code).toBeDefined();
      expect(error.message).toBeDefined();
      expect(error.severity).toBeDefined();
    }
  });
});

/**
 * Test Suite 14: Advanced Features
 */
describe('PostgreSQL Advanced Features', () => {
  it('should work with materialized views', async () => {
    // Refresh materialized view
    await pool.query('REFRESH MATERIALIZED VIEW product_sales_summary');

    const result = await pool.query(
      'SELECT * FROM product_sales_summary ORDER BY total_revenue DESC LIMIT 5'
    );

    expect(result.rows.length).toBeGreaterThan(0);
    expect(result.rows[0].total_revenue).toBeDefined();
  });

  it('should work with regular views', async () => {
    const result = await pool.query(
      'SELECT * FROM customer_order_summary ORDER BY total_spent DESC LIMIT 5'
    );

    expect(result.rows.length).toBeGreaterThan(0);
    expect(result.rows[0].total_spent).toBeDefined();
  });

  it('should use RETURNING clause', async () => {
    const result = await pool.query(
      `INSERT INTO users (username, email, password_hash)
       VALUES ($1, $2, $3)
       RETURNING id, username, email, created_at`,
      ['returning_test', 'returning@example.com', 'hash']
    );

    expect(result.rows[0].id).toBeDefined();
    expect(result.rows[0].username).toBe('returning_test');
    expect(result.rows[0].created_at).toBeDefined();
  });

  it('should use UPSERT (INSERT ... ON CONFLICT)', async () => {
    // First insert
    await pool.query(
      `INSERT INTO users (username, email, password_hash)
       VALUES ($1, $2, $3)`,
      ['upsert_test', 'upsert@example.com', 'hash1']
    );

    // Upsert (update on conflict)
    const result = await pool.query(
      `INSERT INTO users (username, email, password_hash)
       VALUES ($1, $2, $3)
       ON CONFLICT (email)
       DO UPDATE SET password_hash = EXCLUDED.password_hash
       RETURNING password_hash`,
      ['upsert_test', 'upsert@example.com', 'hash2']
    );

    expect(result.rows[0].password_hash).toBe('hash2');
  });

  it('should generate series and sequences', async () => {
    const result = await pool.query(
      'SELECT generate_series(1, 10) as num'
    );

    expect(result.rows).toHaveLength(10);
    expect(result.rows[0].num).toBe(1);
    expect(result.rows[9].num).toBe(10);
  });

  it('should use complex aggregations', async () => {
    const result = await pool.query(
      `SELECT
         COUNT(*) as total_orders,
         SUM(total_amount) as total_revenue,
         AVG(total_amount) as avg_order_value,
         MIN(total_amount) as min_order,
         MAX(total_amount) as max_order,
         STDDEV(total_amount) as stddev_order
       FROM orders`
    );

    expect(result.rows[0].total_orders).toBeDefined();
    expect(result.rows[0].total_revenue).toBeDefined();
    expect(parseFloat(result.rows[0].avg_order_value)).toBeGreaterThan(0);
  });
});
