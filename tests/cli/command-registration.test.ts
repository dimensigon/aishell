/**
 * Command Registration Integration Test
 *
 * Tests that all 105+ Phase 2 CLI commands are properly registered and accessible
 */

import { describe, it, expect, beforeAll } from 'vitest';
import { Command } from 'commander';
import { commandRegistry, CommandCategory } from '../../src/cli/command-registry';

describe('Command Registration Integration', () => {
  describe('Command Registry', () => {
    it('should have command registry initialized', () => {
      expect(commandRegistry).toBeDefined();
    });

    it('should have at least 105 commands registered', () => {
      const count = commandRegistry.getCommandCount();
      expect(count).toBeGreaterThanOrEqual(105);
    });

    it('should have commands from all three phases', () => {
      const stats = commandRegistry.getStatistics();
      expect(stats.byPhase[1]).toBeGreaterThan(0); // Phase 1
      expect(stats.byPhase[2]).toBeGreaterThan(0); // Phase 2
      expect(stats.byPhase[3]).toBeGreaterThan(0); // Phase 3
    });

    it('should have commands in all categories', () => {
      const stats = commandRegistry.getStatistics();
      const categories = Object.keys(stats.byCategory);

      // Should have at least 8 categories
      expect(categories.length).toBeGreaterThanOrEqual(8);
    });
  });

  describe('Phase 1 Commands', () => {
    it('should have Query Optimization commands registered', () => {
      const commands = commandRegistry.getCommandsByCategory(CommandCategory.QUERY_OPTIMIZATION);
      expect(commands.length).toBeGreaterThanOrEqual(13);

      // Check key commands exist
      const commandNames = commands.map(c => c.name);
      expect(commandNames).toContain('optimize');
      expect(commandNames).toContain('translate');
      expect(commandNames).toContain('analyze patterns');
    });

    it('should have Health Monitoring commands registered', () => {
      const commands = commandRegistry.getCommandsByCategory(CommandCategory.HEALTH_MONITORING);
      expect(commands.length).toBeGreaterThanOrEqual(5);

      const commandNames = commands.map(c => c.name);
      expect(commandNames).toContain('health-check');
      expect(commandNames).toContain('monitor');
      expect(commandNames).toContain('dashboard');
    });

    it('should have Backup & Recovery commands registered', () => {
      const commands = commandRegistry.getCommandsByCategory(CommandCategory.BACKUP_RECOVERY);
      expect(commands.length).toBeGreaterThanOrEqual(10);

      const commandNames = commands.map(c => c.name);
      expect(commandNames).toContain('backup');
      expect(commandNames).toContain('restore');
      expect(commandNames).toContain('backup list');
    });
  });

  describe('Phase 2 Commands', () => {
    it('should have Database Operations commands (Sprint 2)', () => {
      const commands = commandRegistry.getCommandsByCategory(CommandCategory.DATABASE_OPERATIONS);
      expect(commands.length).toBeGreaterThanOrEqual(32);

      const commandNames = commands.map(c => c.name);

      // MySQL commands (8)
      expect(commandNames).toContain('mysql connect');
      expect(commandNames).toContain('mysql query');
      expect(commandNames).toContain('mysql tables');

      // MongoDB commands (10)
      expect(commandNames).toContain('mongo connect');
      expect(commandNames).toContain('mongo query');
      expect(commandNames).toContain('mongo collections');

      // Redis commands (14)
      expect(commandNames).toContain('redis connect');
      expect(commandNames).toContain('redis get');
      expect(commandNames).toContain('redis set');
    });

    it('should have Migration commands (Sprint 3)', () => {
      const commands = commandRegistry.getCommandsByCategory(CommandCategory.MIGRATION);
      expect(commands.length).toBeGreaterThanOrEqual(12); // 8 migration + 4 schema commands

      const commandNames = commands.map(c => c.name);
      expect(commandNames).toContain('migration create');
      expect(commandNames).toContain('migration up');
      expect(commandNames).toContain('migration down');
      expect(commandNames).toContain('schema diff');
    });

    it('should have Security commands (Sprint 3)', () => {
      const commands = commandRegistry.getCommandsByCategory(CommandCategory.SECURITY);
      expect(commands.length).toBeGreaterThanOrEqual(7);

      const commandNames = commands.map(c => c.name);
      expect(commandNames).toContain('vault-add');
      expect(commandNames).toContain('vault-list');
      expect(commandNames).toContain('permissions-grant');
      expect(commandNames).toContain('audit-log');
    });

    it('should have Integration commands (Sprint 5)', () => {
      const commands = commandRegistry.getCommandsByCategory(CommandCategory.INTEGRATION);
      expect(commands.length).toBeGreaterThanOrEqual(12); // Slack, Email, Federation

      const commandNames = commands.map(c => c.name);
      expect(commandNames).toContain('slack setup');
      expect(commandNames).toContain('email send');
      expect(commandNames).toContain('federation query');
    });

    it('should have Autonomous commands (Sprint 5)', () => {
      const commands = commandRegistry.getCommandsByCategory(CommandCategory.AUTONOMOUS);
      expect(commands.length).toBeGreaterThanOrEqual(4);

      const commandNames = commands.map(c => c.name);
      expect(commandNames).toContain('ada start');
      expect(commandNames).toContain('ada stop');
      expect(commandNames).toContain('ada status');
      expect(commandNames).toContain('ada configure');
    });
  });

  describe('Phase 3 Commands', () => {
    it('should have Connection Management commands', () => {
      const commands = commandRegistry.getCommandsByCategory(CommandCategory.CONNECTION);
      expect(commands.length).toBeGreaterThanOrEqual(4);

      const commandNames = commands.map(c => c.name);
      expect(commandNames).toContain('connect');
      expect(commandNames).toContain('disconnect');
      expect(commandNames).toContain('connections');
    });

    it('should have Context Management commands', () => {
      const commands = commandRegistry.getCommandsByCategory(CommandCategory.CONTEXT);
      expect(commands.length).toBeGreaterThanOrEqual(6);

      const commandNames = commands.map(c => c.name);
      expect(commandNames).toContain('context save');
      expect(commandNames).toContain('context load');
      expect(commandNames).toContain('context list');
    });

    it('should have Utility commands', () => {
      const commands = commandRegistry.getCommandsByCategory(CommandCategory.UTILITY);
      expect(commands.length).toBeGreaterThanOrEqual(3);

      const commandNames = commands.map(c => c.name);
      expect(commandNames).toContain('interactive');
      expect(commandNames).toContain('features');
      expect(commandNames).toContain('examples');
    });
  });

  describe('Command Metadata', () => {
    it('should have complete metadata for each command', () => {
      const commands = commandRegistry.getAllCommands();

      commands.forEach(cmd => {
        expect(cmd.name).toBeDefined();
        expect(cmd.description).toBeDefined();
        expect(cmd.category).toBeDefined();
        expect(cmd.phase).toBeDefined();
        expect(cmd.phase).toBeGreaterThanOrEqual(1);
        expect(cmd.phase).toBeLessThanOrEqual(3);
      });
    });

    it('should properly handle command aliases', () => {
      const optimizeCmd = commandRegistry.getCommand('optimize');
      expect(optimizeCmd).toBeDefined();

      const optCmd = commandRegistry.getCommand('opt');
      expect(optCmd).toBeDefined();
      expect(optCmd?.name).toBe('opt'); // Alias returns with alias name
    });

    it('should support command search', () => {
      const results = commandRegistry.searchCommands('backup');
      expect(results.length).toBeGreaterThan(0);

      // All results should contain 'backup' somewhere
      results.forEach(cmd => {
        const searchable = `${cmd.name} ${cmd.description} ${cmd.category}`.toLowerCase();
        expect(searchable).toContain('backup');
      });
    });
  });

  describe('Command Statistics', () => {
    it('should provide accurate statistics', () => {
      const stats = commandRegistry.getStatistics();

      expect(stats.total).toBeGreaterThanOrEqual(105);
      expect(stats.byPhase[1] + stats.byPhase[2] + stats.byPhase[3]).toBe(stats.total);

      const categoryTotal = Object.values(stats.byCategory).reduce((sum, count) => sum + count, 0);
      expect(categoryTotal).toBe(stats.total);
    });
  });

  describe('Help Text Generation', () => {
    it('should generate category help text', () => {
      const help = commandRegistry.getCategoryHelp(CommandCategory.QUERY_OPTIMIZATION);

      expect(help).toContain('Query Optimization');
      expect(help).toContain('optimize');
      expect(help).toBeTruthy();
      expect(help.length).toBeGreaterThan(50);
    });

    it('should generate full help text', () => {
      const help = commandRegistry.getFullHelp();

      expect(help).toContain('AI-Shell');
      expect(help).toContain('Total Commands');
      expect(help.length).toBeGreaterThan(500);
    });
  });

  describe('Sprint Distribution', () => {
    it('should have Sprint 1 commands (Optimization)', () => {
      const commands = commandRegistry.getAllCommands().filter(c => c.sprint === 1);
      expect(commands.length).toBeGreaterThanOrEqual(13); // 13 optimization commands
    });

    it('should have Sprint 2 commands (Database Operations)', () => {
      const commands = commandRegistry.getAllCommands().filter(c => c.sprint === 2);
      expect(commands.length).toBeGreaterThanOrEqual(32); // MySQL + MongoDB + Redis
    });

    it('should have Sprint 3 commands (Backup, Migration, Security)', () => {
      const commands = commandRegistry.getAllCommands().filter(c => c.sprint === 3);
      expect(commands.length).toBeGreaterThanOrEqual(25); // 10 backup + 8 migration + 7 security
    });

    it('should have Sprint 4 commands (Monitoring)', () => {
      const commands = commandRegistry.getAllCommands().filter(c => c.sprint === 4);
      expect(commands.length).toBeGreaterThanOrEqual(15); // Monitoring commands
    });

    it('should have Sprint 5 commands (Integration)', () => {
      const commands = commandRegistry.getAllCommands().filter(c => c.sprint === 5);
      expect(commands.length).toBeGreaterThanOrEqual(20); // Integration + Autonomous
    });
  });

  describe('Command Naming Conventions', () => {
    it('should use consistent naming patterns', () => {
      const commands = commandRegistry.getAllCommands();

      // Commands should not have inconsistent spacing
      commands.forEach(cmd => {
        expect(cmd.name).not.toMatch(/\s{2,}/); // No double spaces
        expect(cmd.name).not.toMatch(/^\s/); // No leading spaces
        expect(cmd.name).not.toMatch(/\s$/); // No trailing spaces
      });
    });

    it('should have appropriate description lengths', () => {
      const commands = commandRegistry.getAllCommands();

      commands.forEach(cmd => {
        expect(cmd.description.length).toBeGreaterThan(10);
        expect(cmd.description.length).toBeLessThan(200);
      });
    });
  });

  describe('Command Coverage', () => {
    it('should cover all required Phase 2 Sprint 1 features', () => {
      const commands = commandRegistry.getAllCommands();
      const commandNames = commands.map(c => c.name);

      // Sprint 1 - Query Optimization (13 commands)
      const sprint1Required = [
        'optimize', 'translate', 'optimize-all', 'slow-queries',
        'indexes analyze', 'indexes missing', 'indexes recommendations',
        'indexes create', 'indexes drop', 'indexes rebuild', 'indexes stats',
        'analyze patterns', 'analyze workload'
      ];

      sprint1Required.forEach(cmdName => {
        expect(commandNames).toContain(cmdName);
      });
    });

    it('should cover all required Phase 2 Sprint 2 features', () => {
      const commands = commandRegistry.getAllCommands();
      const commandNames = commands.map(c => c.name);

      // MySQL (8)
      expect(commandNames).toContain('mysql connect');
      expect(commandNames).toContain('mysql query');

      // MongoDB (10)
      expect(commandNames).toContain('mongo connect');
      expect(commandNames).toContain('mongo query');

      // Redis (14)
      expect(commandNames).toContain('redis connect');
      expect(commandNames).toContain('redis get');
    });

    it('should cover all required Phase 2 Sprint 3 features', () => {
      const commands = commandRegistry.getAllCommands();
      const commandNames = commands.map(c => c.name);

      // Backup (6 new)
      expect(commandNames).toContain('backup schedule');
      expect(commandNames).toContain('backup verify');

      // Migration (8)
      expect(commandNames).toContain('migration create');
      expect(commandNames).toContain('migration up');

      // Security (7)
      expect(commandNames).toContain('vault-add');
      expect(commandNames).toContain('permissions-grant');
    });
  });
});
