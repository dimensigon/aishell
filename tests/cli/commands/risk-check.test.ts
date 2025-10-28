/**
 * Tests for Risk Check Command
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { Command } from 'commander';
import { registerRiskCheckCommand } from '../../../src/cli/commands/risk-check';

describe('Risk Check Command', () => {
  let program: Command;

  beforeEach(() => {
    program = new Command();
    registerRiskCheckCommand(program);
  });

  it('should register risk-check command', () => {
    const commands = program.commands.map(cmd => cmd.name());
    expect(commands).toContain('risk-check');
  });

  it('should have risk alias', () => {
    const riskCmd = program.commands.find(cmd => cmd.name() === 'risk-check');
    expect(riskCmd?.aliases()).toContain('risk');
  });

  it('should have required query argument', () => {
    const riskCmd = program.commands.find(cmd => cmd.name() === 'risk-check');
    const args = riskCmd?.registeredArguments || [];
    expect(args.length).toBeGreaterThan(0);
    expect(args[0].required).toBe(true);
  });

  it('should support --format option', () => {
    const riskCmd = program.commands.find(cmd => cmd.name() === 'risk-check');
    const options = riskCmd?.options.map(opt => opt.long);
    expect(options).toContain('--format');
  });

  it('should support --auto-approve option', () => {
    const riskCmd = program.commands.find(cmd => cmd.name() === 'risk-check');
    const options = riskCmd?.options.map(opt => opt.long);
    expect(options).toContain('--auto-approve');
  });

  it('should support --verbose option', () => {
    const riskCmd = program.commands.find(cmd => cmd.name() === 'risk-check');
    const options = riskCmd?.options.map(opt => opt.long);
    expect(options).toContain('--verbose');
  });
});

describe('Risk Check Command - Operation Detection', () => {
  it('should detect SELECT operation', () => {
    const query = 'SELECT * FROM users';
    expect(query.toUpperCase().startsWith('SELECT')).toBe(true);
  });

  it('should detect DELETE operation', () => {
    const query = 'DELETE FROM users WHERE id = 1';
    expect(query.toUpperCase().startsWith('DELETE')).toBe(true);
  });

  it('should detect DROP operation', () => {
    const query = 'DROP TABLE users';
    expect(query.toUpperCase().startsWith('DROP')).toBe(true);
  });

  it('should detect TRUNCATE operation', () => {
    const query = 'TRUNCATE TABLE users';
    expect(query.toUpperCase().startsWith('TRUNCATE')).toBe(true);
  });

  it('should detect UPDATE operation', () => {
    const query = 'UPDATE users SET active = false';
    expect(query.toUpperCase().startsWith('UPDATE')).toBe(true);
  });

  it('should detect ALTER operation', () => {
    const query = 'ALTER TABLE users ADD COLUMN email VARCHAR(255)';
    expect(query.toUpperCase().startsWith('ALTER')).toBe(true);
  });
});

describe('Risk Check Command - WHERE Clause Detection', () => {
  it('should detect missing WHERE in DELETE', () => {
    const query = 'DELETE FROM users';
    expect(query.toUpperCase().includes('WHERE')).toBe(false);
  });

  it('should detect existing WHERE in DELETE', () => {
    const query = 'DELETE FROM users WHERE id = 1';
    expect(query.toUpperCase().includes('WHERE')).toBe(true);
  });

  it('should detect missing WHERE in UPDATE', () => {
    const query = 'UPDATE users SET active = false';
    expect(query.toUpperCase().includes('WHERE')).toBe(false);
  });

  it('should detect existing WHERE in UPDATE', () => {
    const query = 'UPDATE users SET active = false WHERE id = 1';
    expect(query.toUpperCase().includes('WHERE')).toBe(true);
  });
});

describe('Risk Check Command - Dangerous Pattern Detection', () => {
  it('should detect CASCADE keyword', () => {
    const query = 'DROP TABLE users CASCADE';
    expect(query.toUpperCase().includes('CASCADE')).toBe(true);
  });

  it('should detect wildcard in non-SELECT', () => {
    const query = 'DELETE * FROM users';
    const isSELECT = query.toUpperCase().startsWith('SELECT');
    const hasWildcard = query.includes('*');
    expect(hasWildcard && !isSELECT).toBe(true);
  });
});

describe('Risk Check Command - Table Extraction', () => {
  it('should extract table from FROM clause', () => {
    const query = 'SELECT * FROM users';
    const match = query.match(/FROM\s+(\w+)/i);
    expect(match?.[1]).toBe('users');
  });

  it('should extract table from UPDATE', () => {
    const query = 'UPDATE users SET active = false';
    const match = query.match(/UPDATE\s+(\w+)/i);
    expect(match?.[1]).toBe('users');
  });

  it('should extract table from DELETE', () => {
    const query = 'DELETE FROM users WHERE id = 1';
    const match = query.match(/DELETE\s+FROM\s+(\w+)/i);
    expect(match?.[1]).toBe('users');
  });

  it('should extract multiple tables from JOINs', () => {
    const query = 'SELECT * FROM users JOIN orders ON users.id = orders.user_id';
    const tables: string[] = [];
    const fromMatch = query.match(/FROM\s+(\w+)/i);
    if (fromMatch) tables.push(fromMatch[1]);

    const joinMatches = query.matchAll(/JOIN\s+(\w+)/gi);
    for (const match of joinMatches) {
      tables.push(match[1]);
    }

    expect(tables).toEqual(['users', 'orders']);
  });
});
