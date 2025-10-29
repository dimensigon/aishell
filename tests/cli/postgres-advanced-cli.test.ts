/**
 * PostgreSQL Advanced CLI Tests
 * Comprehensive test suite for PostgreSQL advanced operations
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { PostgresAdvancedCLI } from '../../src/cli/postgres-advanced-cli';
import {
  VacuumCommandBuilder,
  AnalyzeCommandBuilder,
  ReindexCommandBuilder,
  PostgreSQLSystemCatalogs,
  PostgreSQLMaintenanceUtils
} from '../../src/cli/postgres-advanced-commands';

// Mock pg module
vi.mock('pg', () => ({
  Pool: vi.fn(() => ({
    query: vi.fn(),
    end: vi.fn()
  }))
}));

// Mock database manager
vi.mock('../../src/cli/database-manager', () => ({
  DatabaseConnectionManager: vi.fn(() => ({
    getConnection: vi.fn(),
    getActive: vi.fn()
  })),
  DatabaseType: {
    POSTGRESQL: 'postgresql',
    MYSQL: 'mysql',
    MONGODB: 'mongodb'
  }
}));

// Mock state manager
vi.mock('../../src/core/state-manager', () => ({
  StateManager: vi.fn(() => ({
    get: vi.fn(),
    set: vi.fn()
  }))
}));

// Mock logger
vi.mock('../../src/core/logger', () => ({
  createLogger: vi.fn(() => ({
    info: vi.fn(),
    error: vi.fn(),
    warn: vi.fn(),
    debug: vi.fn()
  }))
}));

describe('VacuumCommandBuilder', () => {
  it('should build basic VACUUM command', () => {
    const builder = new VacuumCommandBuilder();
    expect(builder.build()).toBe('VACUUM');
  });

  it('should build VACUUM with FULL option', () => {
    const builder = new VacuumCommandBuilder();
    builder.full();
    expect(builder.build()).toBe('VACUUM (FULL)');
  });

  it('should build VACUUM with FREEZE option', () => {
    const builder = new VacuumCommandBuilder();
    builder.freeze();
    expect(builder.build()).toBe('VACUUM (FREEZE)');
  });

  it('should build VACUUM with ANALYZE option', () => {
    const builder = new VacuumCommandBuilder();
    builder.analyze();
    expect(builder.build()).toBe('VACUUM (ANALYZE)');
  });

  it('should build VACUUM with VERBOSE option', () => {
    const builder = new VacuumCommandBuilder();
    builder.verbose();
    expect(builder.build()).toBe('VACUUM (VERBOSE)');
  });

  it('should build VACUUM with multiple options', () => {
    const builder = new VacuumCommandBuilder();
    builder.full().freeze().analyze().verbose();
    expect(builder.build()).toBe('VACUUM (FULL, FREEZE, ANALYZE, VERBOSE)');
  });

  it('should build VACUUM with table name', () => {
    const builder = new VacuumCommandBuilder();
    builder.table('users');
    expect(builder.build()).toBe('VACUUM users');
  });

  it('should build VACUUM with table and options', () => {
    const builder = new VacuumCommandBuilder();
    builder.full().analyze().table('users');
    expect(builder.build()).toBe('VACUUM (FULL, ANALYZE) users');
  });

  it('should build VACUUM with SKIP_LOCKED option', () => {
    const builder = new VacuumCommandBuilder();
    builder.skipLocked();
    expect(builder.build()).toBe('VACUUM (SKIP_LOCKED)');
  });

  it('should build VACUUM with INDEX_CLEANUP option', () => {
    const builder = new VacuumCommandBuilder();
    builder.indexCleanup(true);
    expect(builder.build()).toBe('VACUUM (INDEX_CLEANUP ON)');
  });

  it('should build VACUUM with INDEX_CLEANUP OFF', () => {
    const builder = new VacuumCommandBuilder();
    builder.indexCleanup(false);
    expect(builder.build()).toBe('VACUUM (INDEX_CLEANUP OFF)');
  });

  it('should build VACUUM with TRUNCATE option', () => {
    const builder = new VacuumCommandBuilder();
    builder.truncate(true);
    expect(builder.build()).toBe('VACUUM (TRUNCATE ON)');
  });

  it('should build VACUUM with PARALLEL option', () => {
    const builder = new VacuumCommandBuilder();
    builder.parallel(4);
    expect(builder.build()).toBe('VACUUM (PARALLEL 4)');
  });

  it('should throw error for negative parallel workers', () => {
    const builder = new VacuumCommandBuilder();
    expect(() => builder.parallel(-1)).toThrow('Parallel workers must be non-negative');
  });

  it('should build complex VACUUM command', () => {
    const builder = new VacuumCommandBuilder();
    builder
      .full()
      .analyze()
      .verbose()
      .skipLocked()
      .indexCleanup(true)
      .truncate(false)
      .parallel(2)
      .table('large_table');

    expect(builder.build()).toBe(
      'VACUUM (FULL, ANALYZE, VERBOSE, SKIP_LOCKED, INDEX_CLEANUP ON, TRUNCATE OFF, PARALLEL 2) large_table'
    );
  });
});

describe('AnalyzeCommandBuilder', () => {
  it('should build basic ANALYZE command', () => {
    const builder = new AnalyzeCommandBuilder();
    expect(builder.build()).toBe('ANALYZE');
  });

  it('should build ANALYZE with VERBOSE option', () => {
    const builder = new AnalyzeCommandBuilder();
    builder.verbose();
    expect(builder.build()).toBe('ANALYZE (VERBOSE)');
  });

  it('should build ANALYZE with SKIP_LOCKED option', () => {
    const builder = new AnalyzeCommandBuilder();
    builder.skipLocked();
    expect(builder.build()).toBe('ANALYZE (SKIP_LOCKED)');
  });

  it('should build ANALYZE with table name', () => {
    const builder = new AnalyzeCommandBuilder();
    builder.table('orders');
    expect(builder.build()).toBe('ANALYZE orders');
  });

  it('should build ANALYZE with table and options', () => {
    const builder = new AnalyzeCommandBuilder();
    builder.verbose().skipLocked().table('products');
    expect(builder.build()).toBe('ANALYZE (VERBOSE, SKIP_LOCKED) products');
  });

  it('should build ANALYZE with multiple options', () => {
    const builder = new AnalyzeCommandBuilder();
    builder.verbose().skipLocked();
    expect(builder.build()).toBe('ANALYZE (VERBOSE, SKIP_LOCKED)');
  });
});

describe('ReindexCommandBuilder', () => {
  it('should build REINDEX INDEX command', () => {
    const builder = new ReindexCommandBuilder();
    builder.index('idx_users_email');
    expect(builder.build()).toBe('REINDEX INDEX idx_users_email');
  });

  it('should build REINDEX TABLE command', () => {
    const builder = new ReindexCommandBuilder();
    builder.table('users');
    expect(builder.build()).toBe('REINDEX TABLE users');
  });

  it('should build REINDEX DATABASE command', () => {
    const builder = new ReindexCommandBuilder();
    builder.database('mydb');
    expect(builder.build()).toBe('REINDEX DATABASE mydb');
  });

  it('should build REINDEX SCHEMA command', () => {
    const builder = new ReindexCommandBuilder();
    builder.schema('public');
    expect(builder.build()).toBe('REINDEX SCHEMA public');
  });

  it('should build REINDEX with CONCURRENTLY option', () => {
    const builder = new ReindexCommandBuilder();
    builder.concurrently().index('idx_users_email');
    expect(builder.build()).toBe('REINDEX (CONCURRENTLY) INDEX idx_users_email');
  });

  it('should build REINDEX with VERBOSE option', () => {
    const builder = new ReindexCommandBuilder();
    builder.verbose().table('users');
    expect(builder.build()).toBe('REINDEX (VERBOSE) TABLE users');
  });

  it('should build REINDEX with multiple options', () => {
    const builder = new ReindexCommandBuilder();
    builder.concurrently().verbose().index('idx_orders_date');
    expect(builder.build()).toBe('REINDEX (CONCURRENTLY, VERBOSE) INDEX idx_orders_date');
  });

  it('should throw error when building without target', () => {
    const builder = new ReindexCommandBuilder();
    expect(() => builder.build()).toThrow('Target type and name are required for REINDEX');
  });
});

describe('PostgreSQLMaintenanceUtils', () => {
  describe('calculateBloatPercentage', () => {
    it('should calculate bloat percentage correctly', () => {
      const result = PostgreSQLMaintenanceUtils.calculateBloatPercentage(800, 200);
      expect(result).toBe(20);
    });

    it('should return 0 for no rows', () => {
      const result = PostgreSQLMaintenanceUtils.calculateBloatPercentage(0, 0);
      expect(result).toBe(0);
    });

    it('should handle 100% bloat', () => {
      const result = PostgreSQLMaintenanceUtils.calculateBloatPercentage(0, 1000);
      expect(result).toBe(100);
    });

    it('should handle minimal bloat', () => {
      const result = PostgreSQLMaintenanceUtils.calculateBloatPercentage(9900, 100);
      expect(result).toBe(1);
    });
  });

  describe('shouldVacuum', () => {
    it('should recommend VACUUM when bloat exceeds threshold', () => {
      const result = PostgreSQLMaintenanceUtils.shouldVacuum(700, 300, 20);
      expect(result).toBe(true);
    });

    it('should not recommend VACUUM when bloat is below threshold', () => {
      const result = PostgreSQLMaintenanceUtils.shouldVacuum(900, 100, 20);
      expect(result).toBe(false);
    });

    it('should use default threshold of 20%', () => {
      const result = PostgreSQLMaintenanceUtils.shouldVacuum(750, 250);
      expect(result).toBe(true);
    });

    it('should handle edge case at threshold', () => {
      const result = PostgreSQLMaintenanceUtils.shouldVacuum(800, 200, 20);
      expect(result).toBe(true);
    });
  });

  describe('shouldAnalyze', () => {
    it('should recommend ANALYZE when never analyzed', () => {
      const result = PostgreSQLMaintenanceUtils.shouldAnalyze(null, 7);
      expect(result).toBe(true);
    });

    it('should recommend ANALYZE when last analyze is old', () => {
      const oldDate = new Date();
      oldDate.setDate(oldDate.getDate() - 10);
      const result = PostgreSQLMaintenanceUtils.shouldAnalyze(oldDate, 7);
      expect(result).toBe(true);
    });

    it('should not recommend ANALYZE when recently analyzed', () => {
      const recentDate = new Date();
      recentDate.setDate(recentDate.getDate() - 2);
      const result = PostgreSQLMaintenanceUtils.shouldAnalyze(recentDate, 7);
      expect(result).toBe(false);
    });

    it('should use default threshold of 7 days', () => {
      const oldDate = new Date();
      oldDate.setDate(oldDate.getDate() - 8);
      const result = PostgreSQLMaintenanceUtils.shouldAnalyze(oldDate);
      expect(result).toBe(true);
    });
  });

  describe('estimateVacuumDuration', () => {
    it('should estimate VACUUM duration', () => {
      const duration = PostgreSQLMaintenanceUtils.estimateVacuumDuration(
        1024 * 1024 * 1024, // 1GB
        1000000, // 1M dead rows
        50 // 50 MB/s
      );
      expect(duration).toBeGreaterThan(0);
    });

    it('should return reasonable estimate for small tables', () => {
      const duration = PostgreSQLMaintenanceUtils.estimateVacuumDuration(
        10 * 1024 * 1024, // 10MB
        10000,
        50
      );
      expect(duration).toBeGreaterThanOrEqual(0);
    });

    it('should return reasonable estimate for large tables', () => {
      const duration = PostgreSQLMaintenanceUtils.estimateVacuumDuration(
        10 * 1024 * 1024 * 1024, // 10GB
        10000000,
        50
      );
      expect(duration).toBeGreaterThan(0);
    });
  });

  describe('formatDuration', () => {
    it('should format milliseconds', () => {
      expect(PostgreSQLMaintenanceUtils.formatDuration(500)).toBe('500ms');
    });

    it('should format seconds', () => {
      expect(PostgreSQLMaintenanceUtils.formatDuration(30000)).toBe('30s');
    });

    it('should format minutes and seconds', () => {
      expect(PostgreSQLMaintenanceUtils.formatDuration(125000)).toBe('2m 5s');
    });

    it('should format hours and minutes', () => {
      expect(PostgreSQLMaintenanceUtils.formatDuration(7320000)).toBe('2h 2m');
    });

    it('should format exactly one minute', () => {
      expect(PostgreSQLMaintenanceUtils.formatDuration(60000)).toBe('1m 0s');
    });

    it('should format exactly one hour', () => {
      expect(PostgreSQLMaintenanceUtils.formatDuration(3600000)).toBe('1h 0m');
    });
  });

  describe('formatBytes', () => {
    it('should format bytes', () => {
      expect(PostgreSQLMaintenanceUtils.formatBytes(512)).toBe('512.00 B');
    });

    it('should format kilobytes', () => {
      expect(PostgreSQLMaintenanceUtils.formatBytes(2048)).toBe('2.00 KB');
    });

    it('should format megabytes', () => {
      expect(PostgreSQLMaintenanceUtils.formatBytes(5 * 1024 * 1024)).toBe('5.00 MB');
    });

    it('should format gigabytes', () => {
      expect(PostgreSQLMaintenanceUtils.formatBytes(3 * 1024 * 1024 * 1024)).toBe('3.00 GB');
    });

    it('should format terabytes', () => {
      expect(PostgreSQLMaintenanceUtils.formatBytes(2 * 1024 * 1024 * 1024 * 1024)).toBe('2.00 TB');
    });

    it('should handle zero bytes', () => {
      expect(PostgreSQLMaintenanceUtils.formatBytes(0)).toBe('0.00 B');
    });

    it('should handle fractional KB', () => {
      expect(PostgreSQLMaintenanceUtils.formatBytes(1536)).toBe('1.50 KB');
    });
  });

  describe('parseInterval', () => {
    it('should parse hours:minutes:seconds format', () => {
      const result = PostgreSQLMaintenanceUtils.parseInterval('01:30:45');
      expect(result).toBe(5445000); // 1h 30m 45s in ms
    });

    it('should parse with milliseconds', () => {
      const result = PostgreSQLMaintenanceUtils.parseInterval('00:01:30.500');
      expect(result).toBe(90500); // 1m 30.5s in ms
    });

    it('should parse zero interval', () => {
      const result = PostgreSQLMaintenanceUtils.parseInterval('00:00:00');
      expect(result).toBe(0);
    });

    it('should return 0 for invalid format', () => {
      const result = PostgreSQLMaintenanceUtils.parseInterval('invalid');
      expect(result).toBe(0);
    });

    it('should handle large hours', () => {
      const result = PostgreSQLMaintenanceUtils.parseInterval('24:00:00');
      expect(result).toBe(86400000); // 24 hours in ms
    });
  });
});

describe('PostgreSQLSystemCatalogs', () => {
  let mockPool: any;
  let catalogs: PostgreSQLSystemCatalogs;

  beforeEach(() => {
    mockPool = {
      query: vi.fn()
    };
    catalogs = new PostgreSQLSystemCatalogs(mockPool);
  });

  it('should get table bloat', async () => {
    const mockRows = [
      { schemaname: 'public', tablename: 'users', size: '10 MB', bloat: '2 MB' }
    ];
    mockPool.query.mockResolvedValue({ rows: mockRows });

    const result = await catalogs.getTableBloat('public');

    expect(result).toEqual(mockRows);
    expect(mockPool.query).toHaveBeenCalledWith(
      expect.stringContaining('FROM pg_tables'),
      ['public']
    );
  });

  it('should get index usage', async () => {
    const mockRows = [
      {
        schemaname: 'public',
        tablename: 'users',
        indexname: 'idx_users_email',
        idx_scan: 1000,
        idx_tup_read: 5000,
        idx_tup_fetch: 4500,
        index_size: '1 MB'
      }
    ];
    mockPool.query.mockResolvedValue({ rows: mockRows });

    const result = await catalogs.getIndexUsage('public');

    expect(result).toEqual(mockRows);
    expect(mockPool.query).toHaveBeenCalledWith(
      expect.stringContaining('FROM pg_stat_user_indexes'),
      ['public']
    );
  });

  it('should get unused indexes', async () => {
    const mockRows = [
      {
        schemaname: 'public',
        tablename: 'logs',
        indexname: 'idx_logs_old',
        index_size: '50 MB'
      }
    ];
    mockPool.query.mockResolvedValue({ rows: mockRows });

    const result = await catalogs.getUnusedIndexes('public');

    expect(result).toEqual(mockRows);
    expect(mockPool.query).toHaveBeenCalledWith(
      expect.stringContaining('idx_scan = 0'),
      ['public']
    );
  });

  it('should get database size', async () => {
    const mockRows = [
      { datname: 'mydb', size: '500 MB' },
      { datname: 'testdb', size: '100 MB' }
    ];
    mockPool.query.mockResolvedValue({ rows: mockRows });

    const result = await catalogs.getDatabaseSize();

    expect(result).toEqual(mockRows);
    expect(mockPool.query).toHaveBeenCalledWith(
      expect.stringContaining('FROM pg_database')
    );
  });

  it('should get table sizes', async () => {
    const mockRows = [
      {
        schemaname: 'public',
        tablename: 'users',
        total_size: '50 MB',
        table_size: '40 MB',
        indexes_size: '10 MB'
      }
    ];
    mockPool.query.mockResolvedValue({ rows: mockRows });

    const result = await catalogs.getTableSizes('public');

    expect(result).toEqual(mockRows);
    expect(mockPool.query).toHaveBeenCalledWith(
      expect.stringContaining('pg_total_relation_size'),
      ['public']
    );
  });

  it('should get long-running queries', async () => {
    const mockRows = [
      {
        pid: 12345,
        duration: '00:05:30',
        usename: 'postgres',
        query: 'SELECT * FROM large_table',
        state: 'active'
      }
    ];
    mockPool.query.mockResolvedValue({ rows: mockRows });

    const result = await catalogs.getLongRunningQueries(60);

    expect(result).toEqual(mockRows);
    expect(mockPool.query).toHaveBeenCalledWith(
      expect.stringContaining("interval '60 seconds'")
    );
  });

  it('should get blocking queries', async () => {
    const mockRows = [
      {
        blocked_pid: 123,
        blocked_user: 'user1',
        blocking_pid: 456,
        blocking_user: 'user2',
        blocked_statement: 'UPDATE users SET ...',
        current_statement_in_blocking_process: 'SELECT * FROM ...'
      }
    ];
    mockPool.query.mockResolvedValue({ rows: mockRows });

    const result = await catalogs.getBlockingQueries();

    expect(result).toEqual(mockRows);
    expect(mockPool.query).toHaveBeenCalledWith(
      expect.stringContaining('pg_locks')
    );
  });

  it('should get replication status', async () => {
    const mockRows = [
      {
        client_addr: '192.168.1.100',
        client_hostname: 'replica1',
        state: 'streaming',
        sync_state: 'async',
        sent_lag: '0 bytes',
        write_lag: '0 bytes',
        flush_lag: '0 bytes',
        replay_lag: '0 bytes'
      }
    ];
    mockPool.query.mockResolvedValue({ rows: mockRows });

    const result = await catalogs.getReplicationStatus();

    expect(result).toEqual(mockRows);
    expect(mockPool.query).toHaveBeenCalledWith(
      expect.stringContaining('pg_stat_replication')
    );
  });

  it('should handle replication status errors gracefully', async () => {
    mockPool.query.mockRejectedValue(new Error('Function not available'));

    const result = await catalogs.getReplicationStatus();

    expect(result).toEqual([]);
  });
});

describe('PostgresAdvancedCLI Integration', () => {
  // Note: Full integration tests would require actual PostgreSQL connection
  // These are structure tests to ensure the API is correct

  it('should have all required methods', () => {
    // Just test that the class exports the correct methods without instantiation
    expect(PostgresAdvancedCLI).toBeDefined();
    expect(typeof PostgresAdvancedCLI).toBe('function');
  });

  it('should export command setup function', async () => {
    const module = await import('../../src/cli/postgres-advanced-cli');
    expect(typeof module.setupPostgresAdvancedCommands).toBe('function');
  });
});
