/**
 * Test Setup and Global Configuration
 * Runs before all test suites
 */

import { beforeAll, afterAll, beforeEach, afterEach } from 'vitest';

// Global test timeout
const GLOBAL_TIMEOUT = 30000;

// Setup before all tests
beforeAll(async () => {
  // Set environment to test
  process.env.NODE_ENV = 'test';
  process.env.LOG_LEVEL = 'error';

  // Initialize test database connections if needed
  console.log('🧪 Setting up test environment...');
});

// Cleanup after all tests
afterAll(async () => {
  // Close database connections
  // Clean up test resources
  console.log('✅ Test environment cleanup complete');
});

// Reset state before each test
beforeEach(() => {
  // Clear any test state
  jest.clearAllMocks?.();
});

// Cleanup after each test
afterEach(() => {
  // Reset modules if needed
  jest.resetModules?.();
});

// Global error handler for unhandled rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection in tests:', reason);
  throw reason;
});

// Extend global timeout for slower tests
jest?.setTimeout?.(GLOBAL_TIMEOUT);
