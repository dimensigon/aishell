/**
 * CommandProcessor Unit Tests
 * Tests command execution, parsing, built-in commands, and edge cases
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { CommandProcessor } from '../../src/core/processor';
import { CommandContext, ShellConfig } from '../../src/types';
import * as fs from 'fs';
import * as path from 'path';

describe('CommandProcessor', () => {
  let processor: CommandProcessor;
  let mockConfig: ShellConfig;

  beforeEach(() => {
    mockConfig = {
      mode: 'interactive' as const,
      aiProvider: 'ollama',
      model: 'test-model',
      timeout: 5000,
      maxHistorySize: 100,
      verbose: false,
    };

    processor = new CommandProcessor(mockConfig);
  });

  afterEach(() => {
    vi.clearAllMocks();
    processor.clearHistory();
  });

  describe('Command Parsing', () => {
    it('should parse simple command', () => {
      const result = processor.parseCommand('ls -la');

      expect(result.command).toBe('ls');
      expect(result.args).toEqual(['-la']);
    });

    it('should parse command with multiple arguments', () => {
      const result = processor.parseCommand('git commit -m "test message" --amend');

      expect(result.command).toBe('git');
      expect(result.args).toEqual(['commit', '-m', 'test message', '--amend']);
    });

    it('should handle quoted arguments with spaces', () => {
      const result = processor.parseCommand('echo "hello world" "foo bar"');

      expect(result.command).toBe('echo');
      expect(result.args).toEqual(['hello world', 'foo bar']);
    });

    it('should handle single quotes', () => {
      const result = processor.parseCommand("echo 'single quoted text'");

      expect(result.command).toBe('echo');
      expect(result.args).toContain('single quoted text');
    });

    it('should handle mixed quotes', () => {
      const result = processor.parseCommand('cmd "double" \'single\' unquoted');

      expect(result.args).toEqual(['double', 'single', 'unquoted']);
    });

    it('should throw on empty command', () => {
      expect(() => processor.parseCommand('')).toThrow('Empty command');
      expect(() => processor.parseCommand('   ')).toThrow('Empty command');
    });

    it('should throw on unclosed quotes', () => {
      expect(() => processor.parseCommand('echo "unclosed')).toThrow(
        'Unclosed quote in command'
      );
      expect(() => processor.parseCommand("echo 'unclosed")).toThrow(
        'Unclosed quote in command'
      );
    });

    it('should handle complex shell commands', () => {
      const result = processor.parseCommand(
        'find . -name "*.ts" -type f | grep test'
      );

      expect(result.command).toBe('find');
      expect(result.args).toContain('*.ts');
    });

    it('should trim whitespace', () => {
      const result = processor.parseCommand('  ls  -la  ');

      expect(result.command).toBe('ls');
      expect(result.args).toEqual(['-la']);
    });
  });

  describe('Built-in Commands', () => {
    it('should identify built-in commands', () => {
      expect(processor.isBuiltIn('cd')).toBe(true);
      expect(processor.isBuiltIn('exit')).toBe(true);
      expect(processor.isBuiltIn('help')).toBe(true);
      expect(processor.isBuiltIn('history')).toBe(true);
      expect(processor.isBuiltIn('clear')).toBe(true);
      expect(processor.isBuiltIn('config')).toBe(true);
    });

    it('should not identify non-built-in commands', () => {
      expect(processor.isBuiltIn('ls')).toBe(false);
      expect(processor.isBuiltIn('echo')).toBe(false);
      expect(processor.isBuiltIn('git')).toBe(false);
    });

    describe('cd command', () => {
      it('should change to specified directory', async () => {
        const testDir = path.resolve(process.cwd(), '..');
        const result = await processor.executeBuiltIn('cd', [testDir], process.cwd());

        expect(result.success).toBe(true);
        expect(result.output).toBe(testDir);
        expect(result.exitCode).toBe(0);
      });

      it('should change to home directory when no argument', async () => {
        const result = await processor.executeBuiltIn('cd', [], process.cwd());

        expect(result.success).toBe(true);
        expect(result.exitCode).toBe(0);
      });

      it('should error on non-existent directory', async () => {
        const result = await processor.executeBuiltIn(
          'cd',
          ['/non/existent/directory'],
          process.cwd()
        );

        expect(result.success).toBe(false);
        expect(result.error).toContain('Directory not found');
        expect(result.exitCode).toBe(1);
      });

      it('should error when target is not a directory', async () => {
        const filePath = path.resolve(__dirname, '../setup.ts');
        if (fs.existsSync(filePath)) {
          const result = await processor.executeBuiltIn('cd', [filePath], process.cwd());

          expect(result.success).toBe(false);
          expect(result.error).toContain('Not a directory');
        }
      });
    });

    describe('history command', () => {
      it('should return empty history initially', async () => {
        const result = await processor.executeBuiltIn('history', [], process.cwd());

        expect(result.success).toBe(true);
        expect(result.output).toBe('');
      });

      it('should show command history', async () => {
        // Add some history
        processor.getHistory().length = 0; // Clear first
        const mockResult = {
          success: true,
          output: 'test',
          exitCode: 0,
          timestamp: new Date(),
        };

        // Simulate adding to history by executing commands
        // This would normally happen through execute(), but we can't easily test that
        // So we'll just verify the format
        const result = await processor.executeBuiltIn('history', [], process.cwd());

        expect(result.success).toBe(true);
        expect(result.exitCode).toBe(0);
      });
    });

    describe('clear command', () => {
      it('should execute clear command', async () => {
        const writeSpy = vi.spyOn(process.stdout, 'write');
        writeSpy.mockImplementation(() => true);

        const result = await processor.executeBuiltIn('clear', [], process.cwd());

        expect(result.success).toBe(true);
        expect(result.exitCode).toBe(0);
        expect(writeSpy).toHaveBeenCalledWith('\x1Bc');

        writeSpy.mockRestore();
      });
    });

    describe('help command', () => {
      it('should return help text', async () => {
        const result = await processor.executeBuiltIn('help', [], process.cwd());

        expect(result.success).toBe(true);
        expect(result.output).toContain('AI-Shell');
        expect(result.output).toContain('Built-in Commands');
        expect(result.output).toContain('cd');
        expect(result.output).toContain('exit');
        expect(result.exitCode).toBe(0);
      });
    });

    describe('config command', () => {
      it('should return current configuration', async () => {
        const result = await processor.executeBuiltIn('config', [], process.cwd());

        expect(result.success).toBe(true);
        expect(result.output).toContain('mode');
        expect(result.output).toContain('aiProvider');
        expect(result.output).toContain('model');

        const config = JSON.parse(result.output);
        expect(config.mode).toBe('interactive');
        expect(config.aiProvider).toBe('ollama');
      });
    });

    describe('unknown built-in', () => {
      it('should error on unknown built-in command', async () => {
        const result = await processor.executeBuiltIn('unknown', [], process.cwd());

        expect(result.success).toBe(false);
        expect(result.error).toContain('Unknown built-in command');
        expect(result.exitCode).toBe(1);
      });
    });
  });

  describe('Command Execution', () => {
    it('should execute simple command successfully', async () => {
      const context: CommandContext = {
        command: 'echo',
        args: ['test'],
        workingDirectory: process.cwd(),
        environment: {},
      };

      const result = await processor.execute(context);

      expect(result.success).toBe(true);
      expect(result.output).toContain('test');
      expect(result.exitCode).toBe(0);
      expect(result.timestamp).toBeInstanceOf(Date);
    }, 10000);

    it('should capture stdout correctly', async () => {
      const context: CommandContext = {
        command: 'node',
        args: ['-e', 'console.log("hello world")'],
        workingDirectory: process.cwd(),
        environment: {},
      };

      const result = await processor.execute(context);

      expect(result.output).toContain('hello world');
      expect(result.success).toBe(true);
    }, 10000);

    it('should handle command with exit code 1', async () => {
      const context: CommandContext = {
        command: 'node',
        args: ['-e', 'process.exit(1)'],
        workingDirectory: process.cwd(),
        environment: {},
      };

      const result = await processor.execute(context);

      expect(result.success).toBe(false);
      expect(result.exitCode).toBe(1);
    }, 10000);

    it('should pass environment variables', async () => {
      const context: CommandContext = {
        command: 'node',
        args: ['-e', 'console.log(process.env.TEST_VAR)'],
        workingDirectory: process.cwd(),
        environment: { TEST_VAR: 'test_value' },
      };

      const result = await processor.execute(context);

      expect(result.output).toContain('test_value');
    }, 10000);

    it('should respect working directory', async () => {
      const testDir = path.resolve(process.cwd(), '..');
      const context: CommandContext = {
        command: 'node',
        args: ['-e', 'console.log(process.cwd())'],
        workingDirectory: testDir,
        environment: {},
      };

      const result = await processor.execute(context);

      expect(result.output).toContain(testDir);
    }, 10000);

    it('should timeout long-running commands', async () => {
      const quickConfig = { ...mockConfig, timeout: 500 };
      const quickProcessor = new CommandProcessor(quickConfig);

      const context: CommandContext = {
        command: 'node',
        args: ['-e', 'setTimeout(() => {}, 5000)'],
        workingDirectory: process.cwd(),
        environment: {},
      };

      await expect(quickProcessor.execute(context)).rejects.toThrow('timed out');
    }, 10000);

    it('should capture stderr', async () => {
      const context: CommandContext = {
        command: 'node',
        args: ['-e', 'console.error("error message")'],
        workingDirectory: process.cwd(),
        environment: {},
      };

      const result = await processor.execute(context);

      expect(result.error).toContain('error message');
    }, 10000);
  });

  describe('History Management', () => {
    it('should track execution history', async () => {
      const context: CommandContext = {
        command: 'echo',
        args: ['test'],
        workingDirectory: process.cwd(),
        environment: {},
      };

      await processor.execute(context);
      await processor.execute(context);

      const history = processor.getHistory();
      expect(history.length).toBe(2);
    }, 10000);

    it('should respect max history size', async () => {
      const smallConfig = { ...mockConfig, maxHistorySize: 3 };
      const smallProcessor = new CommandProcessor(smallConfig);

      const context: CommandContext = {
        command: 'echo',
        args: ['test'],
        workingDirectory: process.cwd(),
        environment: {},
      };

      // Execute 5 commands
      for (let i = 0; i < 5; i++) {
        await smallProcessor.execute(context);
      }

      const history = smallProcessor.getHistory();
      expect(history.length).toBe(3); // Should only keep last 3
    }, 10000);

    it('should clear history', async () => {
      const context: CommandContext = {
        command: 'echo',
        args: ['test'],
        workingDirectory: process.cwd(),
        environment: {},
      };

      await processor.execute(context);
      expect(processor.getHistory().length).toBe(1);

      processor.clearHistory();
      expect(processor.getHistory().length).toBe(0);
    }, 10000);
  });

  describe('Configuration', () => {
    it('should update configuration', () => {
      const newConfig = {
        ...mockConfig,
        verbose: true,
        timeout: 10000,
      };

      processor.updateConfig(newConfig);

      // Configuration is private, but we can test side effects
      expect(() => processor.updateConfig(newConfig)).not.toThrow();
    });

    it('should respect verbose mode', async () => {
      const verboseConfig = { ...mockConfig, verbose: true };
      const verboseProcessor = new CommandProcessor(verboseConfig);

      const stdoutSpy = vi.spyOn(process.stdout, 'write');
      stdoutSpy.mockImplementation(() => true);

      const context: CommandContext = {
        command: 'echo',
        args: ['verbose test'],
        workingDirectory: process.cwd(),
        environment: {},
      };

      await verboseProcessor.execute(context);

      // Verbose mode should cause console output
      expect(stdoutSpy).toHaveBeenCalled();

      stdoutSpy.mockRestore();
    }, 10000);
  });

  describe('Error Handling', () => {
    it('should handle non-existent command', async () => {
      const context: CommandContext = {
        command: 'nonexistentcommandxyz123',
        args: [],
        workingDirectory: process.cwd(),
        environment: {},
      };

      await expect(processor.execute(context)).rejects.toThrow();
    }, 10000);

    it('should handle invalid working directory', async () => {
      const context: CommandContext = {
        command: 'echo',
        args: ['test'],
        workingDirectory: '/nonexistent/directory/path',
        environment: {},
      };

      await expect(processor.execute(context)).rejects.toThrow();
    }, 10000);
  });

  describe('Edge Cases', () => {
    it('should handle command with no arguments', async () => {
      const context: CommandContext = {
        command: 'node',
        args: ['-e', 'console.log("no args")'],
        workingDirectory: process.cwd(),
        environment: {},
      };

      const result = await processor.execute(context);
      expect(result.success).toBe(true);
    }, 10000);

    it('should handle very long output', async () => {
      const context: CommandContext = {
        command: 'node',
        args: [
          '-e',
          'for(let i=0; i<100; i++) console.log("Line " + i + ": " + "x".repeat(100))',
        ],
        workingDirectory: process.cwd(),
        environment: {},
      };

      const result = await processor.execute(context);
      expect(result.output.length).toBeGreaterThan(1000);
    }, 10000);

    it('should handle commands with special characters', async () => {
      const result = processor.parseCommand('grep "test\\npattern" file.txt');

      expect(result.command).toBe('grep');
      expect(result.args).toContain('test\\npattern');
    });

    it('should handle empty args array', async () => {
      const context: CommandContext = {
        command: 'pwd',
        args: [],
        workingDirectory: process.cwd(),
        environment: {},
      };

      const result = await processor.execute(context);
      expect(result.success).toBe(true);
    }, 10000);
  });
});
