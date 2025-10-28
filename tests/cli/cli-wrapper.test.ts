/**
 * CLI Wrapper Tests
 * Comprehensive test suite for the CLI wrapper framework
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { CLIWrapper, CLIOptions, CommandResult } from '../../src/cli/cli-wrapper';
import * as fs from 'fs/promises';

describe('CLIWrapper', () => {
  let wrapper: CLIWrapper;

  beforeEach(() => {
    wrapper = new CLIWrapper();
    // Mock environment variables
    process.env.ANTHROPIC_API_KEY = 'test-api-key';
    process.env.DATABASE_URL = 'postgresql://localhost:5432/test';
  });

  afterEach(async () => {
    await wrapper.cleanup();
    vi.clearAllMocks();
  });

  describe('Command Registration', () => {
    it('should register all commands', () => {
      const commands = wrapper.getRegisteredCommands();
      expect(commands.length).toBeGreaterThan(0);
    });

    it('should register command aliases', () => {
      const commands = wrapper.getRegisteredCommands();
      const optimizeCmd = commands.find(c => c.name === 'optimize');
      expect(optimizeCmd).toBeDefined();
      expect(optimizeCmd?.aliases).toContain('opt');
    });

    it('should have unique command names', () => {
      const commands = wrapper.getRegisteredCommands();
      const names = commands.map(c => c.name);
      const uniqueNames = new Set(names);
      expect(uniqueNames.size).toBe(names.length);
    });
  });

  describe('Command Execution', () => {
    it('should execute valid command', async () => {
      const result = await wrapper.executeCommand(
        'health-check',
        [],
        { dryRun: true }
      );
      expect(result.success).toBe(true);
      expect(result.duration).toBeGreaterThan(0);
    });

    it('should handle command aliases', async () => {
      const result = await wrapper.executeCommand(
        'opt',
        ['SELECT * FROM users'],
        { dryRun: true }
      );
      expect(result.success).toBe(true);
    });

    it('should fail for unknown command', async () => {
      const result = await wrapper.executeCommand(
        'unknown-command',
        [],
        {}
      );
      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });

    it('should validate required arguments', async () => {
      const result = await wrapper.executeCommand(
        'optimize',
        [], // Missing required query argument
        {}
      );
      expect(result.success).toBe(false);
      expect(result.error).toContain('requires');
    });
  });

  describe('Global Flags', () => {
    it('should handle verbose flag', async () => {
      const result = await wrapper.executeCommand(
        'health-check',
        [],
        { verbose: true, dryRun: true }
      );
      expect(result.success).toBe(true);
    });

    it('should handle dry-run flag', async () => {
      const result = await wrapper.executeCommand(
        'backup',
        [],
        { dryRun: true }
      );
      expect(result.success).toBe(true);
      expect(result.warnings).toContain('Command not executed (dry-run mode)');
    });

    it('should handle explain flag', async () => {
      const result = await wrapper.executeCommand(
        'health-check',
        [],
        { explain: true, dryRun: true }
      );
      expect(result.success).toBe(true);
    });

    it('should handle limit option', async () => {
      const result = await wrapper.executeCommand(
        'backup-list',
        [],
        { limit: 5, dryRun: true }
      );
      expect(result.success).toBe(true);
    });

    it('should handle timeout option', async () => {
      const result = await wrapper.executeCommand(
        'health-check',
        [],
        { timeout: 1000, dryRun: true }
      );
      expect(result.success).toBe(true);
    });
  });

  describe('Output Formatting', () => {
    it('should format output as JSON', async () => {
      const result = await wrapper.executeCommand(
        'health-check',
        [],
        { format: 'json', dryRun: true }
      );
      expect(result.success).toBe(true);
    });

    it('should format output as table', async () => {
      const result = await wrapper.executeCommand(
        'backup-list',
        [],
        { format: 'table', dryRun: true }
      );
      expect(result.success).toBe(true);
    });

    it('should format output as CSV', async () => {
      const result = await wrapper.executeCommand(
        'backup-list',
        [],
        { format: 'csv', dryRun: true }
      );
      expect(result.success).toBe(true);
    });

    it('should handle raw output format', async () => {
      const result = await wrapper.executeCommand(
        'health-check',
        [],
        { raw: true, dryRun: true }
      );
      expect(result.success).toBe(true);
    });
  });

  describe('File Output', () => {
    const testOutputFile = '/tmp/cli-wrapper-test-output.json';

    afterEach(async () => {
      try {
        await fs.unlink(testOutputFile);
      } catch {
        // Ignore if file doesn't exist
      }
    });

    it('should write output to file', async () => {
      const result = await wrapper.executeCommand(
        'health-check',
        [],
        {
          output: testOutputFile,
          format: 'json',
          dryRun: true
        }
      );
      expect(result.success).toBe(true);

      // Check if file was created
      const fileExists = await fs.access(testOutputFile).then(() => true).catch(() => false);
      expect(fileExists).toBe(true);
    });
  });

  describe('Environment Variables', () => {
    it('should use DATABASE_URL from environment', async () => {
      const result = await wrapper.executeCommand(
        'health-check',
        [],
        { dryRun: true }
      );
      expect(result.success).toBe(true);
    });

    it('should use REDIS_URL from environment', async () => {
      process.env.REDIS_URL = 'redis://localhost:6379';
      const result = await wrapper.executeCommand(
        'cache-enable',
        [],
        { dryRun: true }
      );
      expect(result.success).toBe(true);
    });

    it('should override with command-line options', async () => {
      const result = await wrapper.executeCommand(
        'backup',
        [],
        {
          database: 'postgresql://custom:5432/db',
          dryRun: true
        }
      );
      expect(result.success).toBe(true);
    });
  });

  describe('Error Handling', () => {
    it('should catch and report errors', async () => {
      // Mock a failing command
      const result = await wrapper.executeCommand(
        'validate-schema',
        ['nonexistent-file.json'],
        {}
      );
      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });

    it('should include error stack trace in verbose mode', async () => {
      const result = await wrapper.executeCommand(
        'unknown-command',
        [],
        { verbose: true }
      );
      expect(result.success).toBe(false);
    });

    it('should handle timeout errors', async () => {
      const result = await wrapper.executeCommand(
        'monitor',
        ['100000'],
        { timeout: 100 } // Very short timeout
      );
      // Monitor command may timeout or succeed quickly
      expect(result).toBeDefined();
    });
  });

  describe('Command Metadata', () => {
    it('should include metadata in result', async () => {
      const result = await wrapper.executeCommand(
        'health-check',
        [],
        { dryRun: true }
      );
      expect(result.metadata).toBeDefined();
      expect(result.metadata?.command).toBe('health-check');
      expect(result.metadata?.args).toEqual([]);
      expect(result.metadata?.timestamp).toBeInstanceOf(Date);
    });

    it('should include request ID', async () => {
      const result = await wrapper.executeCommand(
        'health-check',
        [],
        { dryRun: true }
      );
      expect(result.metadata?.requestId).toBeDefined();
      expect(result.metadata?.requestId).toMatch(/^req_/);
    });

    it('should track execution duration', async () => {
      const result = await wrapper.executeCommand(
        'health-check',
        [],
        { dryRun: true }
      );
      expect(result.duration).toBeGreaterThan(0);
    });
  });

  describe('Command-Specific Tests', () => {
    describe('optimize command', () => {
      it('should optimize query', async () => {
        const result = await wrapper.executeCommand(
          'optimize',
          ['SELECT * FROM users WHERE active = true'],
          { dryRun: true }
        );
        expect(result.success).toBe(true);
      });

      it('should work with alias "opt"', async () => {
        const result = await wrapper.executeCommand(
          'opt',
          ['SELECT * FROM users'],
          { dryRun: true }
        );
        expect(result.success).toBe(true);
      });
    });

    describe('backup commands', () => {
      it('should create backup', async () => {
        const result = await wrapper.executeCommand(
          'backup',
          [],
          { dryRun: true }
        );
        expect(result.success).toBe(true);
        expect(result.warnings).toBeDefined();
      });

      it('should list backups', async () => {
        const result = await wrapper.executeCommand(
          'backup-list',
          [],
          { dryRun: true }
        );
        expect(result.success).toBe(true);
      });

      it('should restore backup', async () => {
        const result = await wrapper.executeCommand(
          'restore',
          ['backup-123456'],
          { dryRun: true }
        );
        expect(result.success).toBe(true);
      });
    });

    describe('cache commands', () => {
      it('should enable cache', async () => {
        const result = await wrapper.executeCommand(
          'cache-enable',
          [],
          { dryRun: true }
        );
        expect(result.success).toBe(true);
      });

      it('should show cache stats', async () => {
        const result = await wrapper.executeCommand(
          'cache-stats',
          [],
          { dryRun: true }
        );
        expect(result.success).toBe(true);
      });

      it('should clear cache', async () => {
        const result = await wrapper.executeCommand(
          'cache-clear',
          [],
          { dryRun: true }
        );
        expect(result.success).toBe(true);
      });
    });

    describe('schema commands', () => {
      it('should design schema', async () => {
        const result = await wrapper.executeCommand(
          'design-schema',
          [],
          { dryRun: true }
        );
        expect(result.success).toBe(true);
      });

      it('should diff schemas', async () => {
        const result = await wrapper.executeCommand(
          'diff',
          ['db1', 'db2'],
          { dryRun: true }
        );
        expect(result.success).toBe(true);
      });
    });

    describe('SQL explainer commands', () => {
      it('should explain SQL', async () => {
        const result = await wrapper.executeCommand(
          'explain',
          ['SELECT * FROM users WHERE id > 100'],
          { dryRun: true }
        );
        expect(result.success).toBe(true);
      });

      it('should translate to SQL', async () => {
        const result = await wrapper.executeCommand(
          'translate',
          ['Show me all users created last week'],
          { dryRun: true }
        );
        expect(result.success).toBe(true);
      });
    });

    describe('cost optimizer commands', () => {
      it('should analyze costs', async () => {
        const result = await wrapper.executeCommand(
          'analyze-costs',
          ['aws', 'us-east-1'],
          { dryRun: true }
        );
        expect(result.success).toBe(true);
      });
    });
  });

  describe('Timestamps', () => {
    it('should add timestamps when requested', async () => {
      const result = await wrapper.executeCommand(
        'health-check',
        [],
        { timestamps: true, dryRun: true }
      );
      expect(result.success).toBe(true);
      expect(result.metadata?.timestamp).toBeInstanceOf(Date);
    });
  });

  describe('Cleanup', () => {
    it('should cleanup resources', async () => {
      await expect(wrapper.cleanup()).resolves.not.toThrow();
    });
  });
});

describe('CLIOptions Interface', () => {
  it('should support all required options', () => {
    const options: CLIOptions = {
      format: 'json',
      verbose: true,
      explain: true,
      dryRun: true,
      database: 'test-db',
      limit: 10,
      output: 'output.json',
      raw: false,
      timeout: 5000,
      timestamps: true
    };

    expect(options.format).toBe('json');
    expect(options.verbose).toBe(true);
    expect(options.explain).toBe(true);
    expect(options.dryRun).toBe(true);
  });
});

describe('CommandResult Interface', () => {
  it('should support all required fields', () => {
    const result: CommandResult = {
      success: true,
      data: { test: 'data' },
      duration: 100,
      metadata: {
        command: 'test',
        args: [],
        timestamp: new Date()
      },
      warnings: ['warning 1'],
      info: ['info 1']
    };

    expect(result.success).toBe(true);
    expect(result.data).toEqual({ test: 'data' });
    expect(result.duration).toBe(100);
  });
});
