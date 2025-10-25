/**
 * Test Helper Utilities
 * Common utilities for testing AI-Shell components
 */

export class TestHelpers {
  /**
   * Wait for a condition to be true
   */
  static async waitFor(
    condition: () => boolean | Promise<boolean>,
    timeout: number = 5000,
    interval: number = 100
  ): Promise<void> {
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      if (await condition()) {
        return;
      }
      await this.sleep(interval);
    }

    throw new Error(`Timeout waiting for condition after ${timeout}ms`);
  }

  /**
   * Sleep for specified milliseconds
   */
  static async sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Generate random test data
   */
  static generateTestData(type: string, count: number = 10): any[] {
    switch (type) {
      case 'users':
        return Array.from({ length: count }, (_, i) => ({
          id: i + 1,
          email: `user${i + 1}@test.com`,
          name: `Test User ${i + 1}`,
          created_at: new Date(Date.now() - Math.random() * 86400000 * 30),
          active: Math.random() > 0.3,
        }));

      case 'orders':
        return Array.from({ length: count }, (_, i) => ({
          id: i + 1,
          user_id: Math.floor(Math.random() * 10) + 1,
          amount: Math.random() * 1000,
          status: ['pending', 'completed', 'cancelled'][Math.floor(Math.random() * 3)],
          created_at: new Date(Date.now() - Math.random() * 86400000 * 7),
        }));

      default:
        return [];
    }
  }

  /**
   * Create mock database connection
   */
  static createMockConnection(type: 'postgresql' | 'oracle' = 'postgresql'): any {
    return {
      type,
      connected: true,
      query: async (sql: string, params?: any[]) => ({
        rows: [],
        rowCount: 0,
      }),
      execute: async (sql: string) => ({ success: true }),
      close: async () => {},
    };
  }

  /**
   * Assert async throws
   */
  static async assertThrows(
    fn: () => Promise<any>,
    expectedError?: string | RegExp
  ): Promise<void> {
    try {
      await fn();
      throw new Error('Expected function to throw, but it did not');
    } catch (error: any) {
      if (expectedError) {
        if (typeof expectedError === 'string') {
          if (!error.message.includes(expectedError)) {
            throw new Error(
              `Expected error message to include "${expectedError}", but got "${error.message}"`
            );
          }
        } else if (expectedError instanceof RegExp) {
          if (!expectedError.test(error.message)) {
            throw new Error(
              `Expected error message to match ${expectedError}, but got "${error.message}"`
            );
          }
        }
      }
    }
  }

  /**
   * Deep clone object
   */
  static deepClone<T>(obj: T): T {
    return JSON.parse(JSON.stringify(obj));
  }

  /**
   * Compare objects for equality
   */
  static deepEqual(a: any, b: any): boolean {
    return JSON.stringify(a) === JSON.stringify(b);
  }

  /**
   * Measure execution time
   */
  static async measureTime<T>(fn: () => Promise<T>): Promise<{ result: T; time: number }> {
    const start = performance.now();
    const result = await fn();
    const time = performance.now() - start;
    return { result, time };
  }

  /**
   * Create test timeout
   */
  static timeout(ms: number): Promise<never> {
    return new Promise((_, reject) =>
      setTimeout(() => reject(new Error(`Timeout after ${ms}ms`)), ms)
    );
  }

  /**
   * Run with timeout
   */
  static async withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
    return Promise.race([promise, this.timeout(ms)]);
  }
}

/**
 * Test Data Fixtures
 */
export class TestFixtures {
  static readonly VALID_SQL_QUERIES = [
    'SELECT * FROM users',
    'SELECT COUNT(*) FROM orders',
    'SELECT u.name, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.name',
    'INSERT INTO users (email, name) VALUES ($1, $2) RETURNING id',
    'UPDATE users SET active = true WHERE id = $1',
    'DELETE FROM sessions WHERE created_at < NOW() - INTERVAL \'7 days\'',
  ];

  static readonly INVALID_SQL_QUERIES = [
    'SELCT * FROM users', // typo
    'SELECT * FORM users', // typo
    'UPDATE users SET active = true', // missing WHERE
    'DELETE FROM users', // missing WHERE
    'INSERT INTO users (email) VALUES', // incomplete
  ];

  static readonly NATURAL_LANGUAGE_QUERIES = [
    { nl: 'show me all users', sql: 'SELECT * FROM users' },
    { nl: 'find active users', sql: 'SELECT * FROM users WHERE active = true' },
    { nl: 'count total orders', sql: 'SELECT COUNT(*) FROM orders' },
    { nl: 'get users created last week', sql: "SELECT * FROM users WHERE created_at >= NOW() - INTERVAL '7 days'" },
  ];

  static readonly SENSITIVE_DATA = [
    {
      original: 'Connect to admin@company.com with password Secret123',
      anonymized: 'Connect to <EMAIL_0> with password <PASSWORD_0>',
      mapping: {
        '<EMAIL_0>': 'admin@company.com',
        '<PASSWORD_0>': 'Secret123',
      },
    },
    {
      original: 'Server: 192.168.1.100, User: dbadmin',
      anonymized: 'Server: <IP_0>, User: <USERNAME_0>',
      mapping: {
        '<IP_0>': '192.168.1.100',
        '<USERNAME_0>': 'dbadmin',
      },
    },
  ];
}

/**
 * Performance Test Utilities
 */
export class PerformanceTestHelpers {
  static async benchmarkFunction(
    fn: () => Promise<any>,
    iterations: number = 100
  ): Promise<{
    average: number;
    min: number;
    max: number;
    median: number;
    p95: number;
    p99: number;
  }> {
    const times: number[] = [];

    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      await fn();
      times.push(performance.now() - start);
    }

    times.sort((a, b) => a - b);

    return {
      average: times.reduce((a, b) => a + b, 0) / times.length,
      min: times[0],
      max: times[times.length - 1],
      median: times[Math.floor(times.length / 2)],
      p95: times[Math.floor(times.length * 0.95)],
      p99: times[Math.floor(times.length * 0.99)],
    };
  }

  static async stressTest(
    fn: () => Promise<any>,
    concurrency: number = 10,
    duration: number = 5000
  ): Promise<{
    totalRequests: number;
    successfulRequests: number;
    failedRequests: number;
    requestsPerSecond: number;
  }> {
    const startTime = Date.now();
    let totalRequests = 0;
    let successfulRequests = 0;
    let failedRequests = 0;

    const runWorker = async () => {
      while (Date.now() - startTime < duration) {
        try {
          await fn();
          successfulRequests++;
        } catch (error) {
          failedRequests++;
        }
        totalRequests++;
      }
    };

    await Promise.all(Array.from({ length: concurrency }, runWorker));

    const durationSeconds = (Date.now() - startTime) / 1000;

    return {
      totalRequests,
      successfulRequests,
      failedRequests,
      requestsPerSecond: totalRequests / durationSeconds,
    };
  }
}

export default TestHelpers;
