/**
 * Tests for Indexes Command
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { Command } from 'commander';
import { registerIndexesCommand } from '../../../src/cli/commands/indexes';

describe('Indexes Command', () => {
  let program: Command;

  beforeEach(() => {
    program = new Command();
    registerIndexesCommand(program);
  });

  it('should register indexes command', () => {
    const commands = program.commands.map(cmd => cmd.name());
    expect(commands).toContain('indexes');
  });

  it('should have idx alias', () => {
    const indexesCmd = program.commands.find(cmd => cmd.name() === 'indexes');
    expect(indexesCmd?.aliases()).toContain('idx');
  });

  it('should have subcommands', () => {
    const indexesCmd = program.commands.find(cmd => cmd.name() === 'indexes');
    expect(indexesCmd?.commands.length).toBeGreaterThan(0);
  });
});

describe('Indexes Command - Recommend Subcommand', () => {
  let program: Command;
  let indexesCmd: Command | undefined;

  beforeEach(() => {
    program = new Command();
    registerIndexesCommand(program);
    indexesCmd = program.commands.find(cmd => cmd.name() === 'indexes');
  });

  it('should have recommend subcommand', () => {
    const subcommands = indexesCmd?.commands.map(cmd => cmd.name());
    expect(subcommands).toContain('recommend');
  });

  it('should require --table option', () => {
    const recommendCmd = indexesCmd?.commands.find(cmd => cmd.name() === 'recommend');
    const options = recommendCmd?.options.map(opt => opt.long);
    expect(options).toContain('--table');
  });

  it('should support --format option', () => {
    const recommendCmd = indexesCmd?.commands.find(cmd => cmd.name() === 'recommend');
    const options = recommendCmd?.options.map(opt => opt.long);
    expect(options).toContain('--format');
  });

  it('should support --verbose option', () => {
    const recommendCmd = indexesCmd?.commands.find(cmd => cmd.name() === 'recommend');
    const options = recommendCmd?.options.map(opt => opt.long);
    expect(options).toContain('--verbose');
  });
});

describe('Indexes Command - Apply Subcommand', () => {
  let program: Command;
  let indexesCmd: Command | undefined;

  beforeEach(() => {
    program = new Command();
    registerIndexesCommand(program);
    indexesCmd = program.commands.find(cmd => cmd.name() === 'indexes');
  });

  it('should have apply subcommand', () => {
    const subcommands = indexesCmd?.commands.map(cmd => cmd.name());
    expect(subcommands).toContain('apply');
  });

  it('should require --table option', () => {
    const applyCmd = indexesCmd?.commands.find(cmd => cmd.name() === 'apply');
    const options = applyCmd?.options.map(opt => opt.long);
    expect(options).toContain('--table');
  });

  it('should require --index option', () => {
    const applyCmd = indexesCmd?.commands.find(cmd => cmd.name() === 'apply');
    const options = applyCmd?.options.map(opt => opt.long);
    expect(options).toContain('--index');
  });

  it('should support --online option with default true', () => {
    const applyCmd = indexesCmd?.commands.find(cmd => cmd.name() === 'apply');
    const onlineOpt = applyCmd?.options.find(opt => opt.long === '--online');
    expect(onlineOpt).toBeDefined();
    expect(onlineOpt?.defaultValue).toBe(true);
  });

  it('should support --dry-run option', () => {
    const applyCmd = indexesCmd?.commands.find(cmd => cmd.name() === 'apply');
    const options = applyCmd?.options.map(opt => opt.long);
    expect(options).toContain('--dry-run');
  });
});

describe('Indexes Command - List Subcommand', () => {
  let program: Command;
  let indexesCmd: Command | undefined;

  beforeEach(() => {
    program = new Command();
    registerIndexesCommand(program);
    indexesCmd = program.commands.find(cmd => cmd.name() === 'indexes');
  });

  it('should have list subcommand', () => {
    const subcommands = indexesCmd?.commands.map(cmd => cmd.name());
    expect(subcommands).toContain('list');
  });

  it('should require --table option', () => {
    const listCmd = indexesCmd?.commands.find(cmd => cmd.name() === 'list');
    const options = listCmd?.options.map(opt => opt.long);
    expect(options).toContain('--table');
  });

  it('should support --show-unused option', () => {
    const listCmd = indexesCmd?.commands.find(cmd => cmd.name() === 'list');
    const options = listCmd?.options.map(opt => opt.long);
    expect(options).toContain('--show-unused');
  });
});
