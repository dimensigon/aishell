/**
 * Test setup for backup tests
 * Provides mock implementations for database and file system operations
 */

import { vi } from 'vitest';

// Export mock factory functions
export function createMockDatabaseManager() {
  return {
    getConnection: vi.fn((dbName: string) => ({
      database: dbName,
      connected: true,
      type: 'postgresql'
    })),
    addConnection: vi.fn(),
    removeConnection: vi.fn(),
    listConnections: vi.fn(() => [])
  };
}

export function createMockBackupManager() {
  return {
    createBackup: vi.fn(),
    restoreBackup: vi.fn(),
    listBackups: vi.fn(() => Promise.resolve([])),
    verifyBackup: vi.fn(() => Promise.resolve(true)),
    shutdown: vi.fn()
  };
}

export function createMockStateManager() {
  const state = new Map();
  return {
    get: vi.fn((key: string) => state.get(key)),
    set: vi.fn((key: string, value: any) => state.set(key, value)),
    delete: vi.fn((key: string) => state.delete(key)),
    clear: vi.fn(() => state.clear())
  };
}

export function setupFileMocks() {
  return {
    access: vi.fn(),
    stat: vi.fn(() => Promise.resolve({ size: 1024 })),
    mkdir: vi.fn(),
    rm: vi.fn(),
    readdir: vi.fn(() => Promise.resolve([])),
    readFile: vi.fn(),
    writeFile: vi.fn(),
    unlink: vi.fn(),
    copyFile: vi.fn()
  };
}
