import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    include: ['**/*.test.ts', '**/*.test.tsx', '**/*.spec.ts'],
    exclude: ['node_modules/**', 'coverage-reports/**'],
    globals: true,
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage-reports',
      include: ['../src/**/*.ts'],
      lines: 80,
      functions: 80,
      branches: 75,
      statements: 80,
    },
    testTimeout: 10000,
    setupFiles: ['./setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '../src'),
      '@tests': path.resolve(__dirname, '.'),
    },
  },
});
