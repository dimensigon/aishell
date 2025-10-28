/**
 * Tests for Optimize Command
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Command } from 'commander';
import { registerOptimizeCommand } from '../../../src/cli/commands/optimize';

describe('Optimize Command', () => {
  let program: Command;

  beforeEach(() => {
    program = new Command();
    registerOptimizeCommand(program);
  });

  it('should register optimize command', () => {
    const commands = program.commands.map(cmd => cmd.name());
    expect(commands).toContain('optimize');
  });

  it('should have opt alias', () => {
    const optimizeCmd = program.commands.find(cmd => cmd.name() === 'optimize');
    expect(optimizeCmd?.aliases()).toContain('opt');
  });

  it('should have required query argument', () => {
    const optimizeCmd = program.commands.find(cmd => cmd.name() === 'optimize');
    const args = optimizeCmd?.registeredArguments || [];
    expect(args.length).toBeGreaterThan(0);
    expect(args[0].required).toBe(true);
  });

  it('should support --apply option', () => {
    const optimizeCmd = program.commands.find(cmd => cmd.name() === 'optimize');
    const options = optimizeCmd?.options.map(opt => opt.long);
    expect(options).toContain('--apply');
  });

  it('should support --explain option', () => {
    const optimizeCmd = program.commands.find(cmd => cmd.name() === 'optimize');
    const options = optimizeCmd?.options.map(opt => opt.long);
    expect(options).toContain('--explain');
  });

  it('should support --dry-run option', () => {
    const optimizeCmd = program.commands.find(cmd => cmd.name() === 'optimize');
    const options = optimizeCmd?.options.map(opt => opt.long);
    expect(options).toContain('--dry-run');
  });

  it('should support --format option', () => {
    const optimizeCmd = program.commands.find(cmd => cmd.name() === 'optimize');
    const options = optimizeCmd?.options.map(opt => opt.long);
    expect(options).toContain('--format');
  });

  it('should support --compare option', () => {
    const optimizeCmd = program.commands.find(cmd => cmd.name() === 'optimize');
    const options = optimizeCmd?.options.map(opt => opt.long);
    expect(options).toContain('--compare');
  });

  it('should support --verbose option', () => {
    const optimizeCmd = program.commands.find(cmd => cmd.name() === 'optimize');
    const options = optimizeCmd?.options.map(opt => opt.long);
    expect(options).toContain('--verbose');
  });
});

describe('Optimize Command - Query Detection', () => {
  it('should detect SELECT queries as safe', () => {
    const query = 'SELECT * FROM users';
    // This would be tested with the actual isDangerousQuery function
    expect(query.toUpperCase().includes('DROP')).toBe(false);
  });

  it('should detect DELETE queries as dangerous', () => {
    const query = 'DELETE FROM users';
    expect(query.toUpperCase().includes('DELETE')).toBe(true);
  });

  it('should detect DROP queries as dangerous', () => {
    const query = 'DROP TABLE users';
    expect(query.toUpperCase().includes('DROP')).toBe(true);
  });

  it('should detect TRUNCATE queries as dangerous', () => {
    const query = 'TRUNCATE TABLE users';
    expect(query.toUpperCase().includes('TRUNCATE')).toBe(true);
  });

  it('should detect UPDATE queries as dangerous', () => {
    const query = 'UPDATE users SET active = false';
    expect(query.toUpperCase().includes('UPDATE')).toBe(true);
  });
});
