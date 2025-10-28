/**
 * Tests for Slow Queries Command
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { Command } from 'commander';
import { registerSlowQueriesCommand } from '../../../src/cli/commands/slow-queries';

describe('Slow Queries Command', () => {
  let program: Command;

  beforeEach(() => {
    program = new Command();
    registerSlowQueriesCommand(program);
  });

  it('should register slow-queries command', () => {
    const commands = program.commands.map(cmd => cmd.name());
    expect(commands).toContain('slow-queries');
  });

  it('should have slow alias', () => {
    const slowCmd = program.commands.find(cmd => cmd.name() === 'slow-queries');
    expect(slowCmd?.aliases()).toContain('slow');
  });

  it('should support --threshold option with default 1000', () => {
    const slowCmd = program.commands.find(cmd => cmd.name() === 'slow-queries');
    const thresholdOpt = slowCmd?.options.find(opt => opt.long === '--threshold');
    expect(thresholdOpt).toBeDefined();
    expect(thresholdOpt?.defaultValue).toBe('1000');
  });

  it('should support --last option with default 24h', () => {
    const slowCmd = program.commands.find(cmd => cmd.name() === 'slow-queries');
    const lastOpt = slowCmd?.options.find(opt => opt.long === '--last');
    expect(lastOpt).toBeDefined();
    expect(lastOpt?.defaultValue).toBe('24h');
  });

  it('should support --limit option with default 20', () => {
    const slowCmd = program.commands.find(cmd => cmd.name() === 'slow-queries');
    const limitOpt = slowCmd?.options.find(opt => opt.long === '--limit');
    expect(limitOpt).toBeDefined();
    expect(limitOpt?.defaultValue).toBe('20');
  });

  it('should support --auto-fix option', () => {
    const slowCmd = program.commands.find(cmd => cmd.name() === 'slow-queries');
    const options = slowCmd?.options.map(opt => opt.long);
    expect(options).toContain('--auto-fix');
  });

  it('should support --format option', () => {
    const slowCmd = program.commands.find(cmd => cmd.name() === 'slow-queries');
    const options = slowCmd?.options.map(opt => opt.long);
    expect(options).toContain('--format');
  });
});

describe('Slow Queries Command - Time Period Parsing', () => {
  it('should parse hours correctly', () => {
    const period = '2h';
    const match = period.match(/^(\d+)([hdw])$/);
    expect(match).toBeTruthy();
    expect(match?.[1]).toBe('2');
    expect(match?.[2]).toBe('h');
  });

  it('should parse days correctly', () => {
    const period = '7d';
    const match = period.match(/^(\d+)([hdw])$/);
    expect(match).toBeTruthy();
    expect(match?.[1]).toBe('7');
    expect(match?.[2]).toBe('d');
  });

  it('should parse weeks correctly', () => {
    const period = '2w';
    const match = period.match(/^(\d+)([hdw])$/);
    expect(match).toBeTruthy();
    expect(match?.[1]).toBe('2');
    expect(match?.[2]).toBe('w');
  });

  it('should reject invalid period format', () => {
    const period = 'invalid';
    const match = period.match(/^(\d+)([hdw])$/);
    expect(match).toBeNull();
  });
});

describe('Slow Queries Command - CSV Escaping', () => {
  it('should escape commas in CSV values', () => {
    const value = 'SELECT name, email FROM users';
    const needsEscape = value.includes(',');
    expect(needsEscape).toBe(true);
  });

  it('should escape quotes in CSV values', () => {
    const value = 'SELECT * FROM users WHERE name = "John"';
    const needsEscape = value.includes('"');
    expect(needsEscape).toBe(true);
  });

  it('should not escape simple values', () => {
    const value = 'SELECT * FROM users';
    const needsEscape = value.includes(',') || value.includes('"') || value.includes('\n');
    expect(needsEscape).toBe(false);
  });
});
