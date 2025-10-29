/**
 * Command Registry - Central registry for all CLI commands
 *
 * This module provides:
 * - Centralized command metadata for all 105+ commands
 * - Command categorization and organization
 * - Enhanced help text generation
 * - Command discovery and search
 * - Phase-based command organization
 */

import { Command } from 'commander';

/**
 * Command metadata structure
 */
export interface CommandMetadata {
  name: string;
  description: string;
  aliases?: string[];
  category: CommandCategory;
  phase: 1 | 2 | 3;
  sprint?: number;
  usage?: string;
  examples?: string[];
  options?: CommandOption[];
  subcommands?: string[];
}

/**
 * Command option metadata
 */
export interface CommandOption {
  flags: string;
  description: string;
  defaultValue?: string;
}

/**
 * Command categories
 */
export enum CommandCategory {
  // Phase 1
  QUERY_OPTIMIZATION = 'Query Optimization',
  HEALTH_MONITORING = 'Health & Monitoring',
  BACKUP_RECOVERY = 'Backup & Recovery',

  // Phase 2
  DATABASE_OPERATIONS = 'Database Operations',
  SECURITY = 'Security & Permissions',
  MIGRATION = 'Migration & Schema',

  // Integration
  INTEGRATION = 'Integration',
  AUTONOMOUS = 'Autonomous Operations',

  // Utility
  CONNECTION = 'Connection Management',
  CONTEXT = 'Context Management',
  UTILITY = 'Utilities'
}

/**
 * Phase-based command organization
 */
export interface PhaseCommands {
  phase: number;
  name: string;
  description: string;
  commandCount: number;
  categories: CommandCategory[];
}

/**
 * Central command registry
 */
export class CommandRegistry {
  private commands: Map<string, CommandMetadata> = new Map();

  constructor() {
    this.registerAllCommands();
  }

  /**
   * Register all commands
   */
  private registerAllCommands(): void {
    // Phase 1: Core Operations (25 commands)
    this.registerPhase1Commands();

    // Phase 2: Advanced Features (60+ commands)
    this.registerPhase2Commands();

    // Phase 3: Analysis & Optimization (20+ commands)
    this.registerPhase3Commands();
  }

  /**
   * Register Phase 1 commands
   */
  private registerPhase1Commands(): void {
    // Query Optimization (13 commands)
    this.register({
      name: 'optimize',
      description: 'Optimize a SQL query using AI analysis',
      aliases: ['opt'],
      category: CommandCategory.QUERY_OPTIMIZATION,
      phase: 1,
      usage: 'ai-shell optimize <query> [options]',
      examples: [
        'ai-shell optimize "SELECT * FROM users WHERE id > 100"',
        'ai-shell opt "SELECT u.*, o.* FROM users u JOIN orders o"'
      ]
    });

    this.register({
      name: 'analyze-slow-queries',
      description: 'Analyze and optimize slow queries from log',
      aliases: ['slow'],
      category: CommandCategory.QUERY_OPTIMIZATION,
      phase: 1
    });

    this.register({
      name: 'translate',
      description: 'Translate natural language to SQL query',
      category: CommandCategory.QUERY_OPTIMIZATION,
      phase: 1
    });

    this.register({
      name: 'optimize-all',
      description: 'Optimize all slow queries automatically',
      category: CommandCategory.QUERY_OPTIMIZATION,
      phase: 1
    });

    this.register({
      name: 'slow-queries',
      description: 'Analyze slow queries with advanced options',
      category: CommandCategory.QUERY_OPTIMIZATION,
      phase: 1
    });

    this.register({
      name: 'indexes analyze',
      description: 'Analyze indexes and provide recommendations',
      category: CommandCategory.QUERY_OPTIMIZATION,
      phase: 1
    });

    this.register({
      name: 'indexes missing',
      description: 'Detect missing indexes from query patterns',
      category: CommandCategory.QUERY_OPTIMIZATION,
      phase: 1
    });

    this.register({
      name: 'indexes recommendations',
      description: 'Get index recommendations',
      category: CommandCategory.QUERY_OPTIMIZATION,
      phase: 1
    });

    this.register({
      name: 'indexes create',
      description: 'Create a new index',
      category: CommandCategory.QUERY_OPTIMIZATION,
      phase: 1
    });

    this.register({
      name: 'indexes drop',
      description: 'Drop an existing index',
      category: CommandCategory.QUERY_OPTIMIZATION,
      phase: 1
    });

    this.register({
      name: 'indexes rebuild',
      description: 'Rebuild indexes',
      category: CommandCategory.QUERY_OPTIMIZATION,
      phase: 1
    });

    this.register({
      name: 'indexes stats',
      description: 'Show index statistics',
      category: CommandCategory.QUERY_OPTIMIZATION,
      phase: 1
    });

    this.register({
      name: 'analyze patterns',
      description: 'Analyze query patterns and identify issues',
      category: CommandCategory.QUERY_OPTIMIZATION,
      phase: 1
    });

    // Health Monitoring (5 commands)
    this.register({
      name: 'health-check',
      description: 'Perform comprehensive database health check',
      aliases: ['health'],
      category: CommandCategory.HEALTH_MONITORING,
      phase: 1
    });

    this.register({
      name: 'monitor',
      description: 'Start real-time database monitoring',
      category: CommandCategory.HEALTH_MONITORING,
      phase: 1
    });

    this.register({
      name: 'alerts setup',
      description: 'Configure health monitoring alerts',
      category: CommandCategory.HEALTH_MONITORING,
      phase: 1
    });

    this.register({
      name: 'dashboard',
      description: 'Launch interactive performance dashboard',
      category: CommandCategory.HEALTH_MONITORING,
      phase: 1
    });

    this.register({
      name: 'anomaly',
      description: 'Detect anomalies in metrics',
      category: CommandCategory.HEALTH_MONITORING,
      phase: 1
    });

    // Backup & Recovery (7 commands)
    this.register({
      name: 'backup',
      description: 'Create database backup',
      category: CommandCategory.BACKUP_RECOVERY,
      phase: 1
    });

    this.register({
      name: 'restore',
      description: 'Restore database from backup',
      category: CommandCategory.BACKUP_RECOVERY,
      phase: 1
    });

    this.register({
      name: 'backup-list',
      description: 'List all backups',
      aliases: ['backups'],
      category: CommandCategory.BACKUP_RECOVERY,
      phase: 1
    });

    this.register({
      name: 'backup create',
      description: 'Create a new database backup',
      category: CommandCategory.BACKUP_RECOVERY,
      phase: 1
    });

    this.register({
      name: 'backup restore',
      description: 'Restore from backup',
      category: CommandCategory.BACKUP_RECOVERY,
      phase: 1
    });

    this.register({
      name: 'backup list',
      description: 'List all backups',
      category: CommandCategory.BACKUP_RECOVERY,
      phase: 1
    });

    this.register({
      name: 'backup status',
      description: 'Show detailed backup status and information',
      category: CommandCategory.BACKUP_RECOVERY,
      phase: 1
    });
  }

  /**
   * Register Phase 2 commands
   */
  private registerPhase2Commands(): void {
    // Database Operations - Sprint 2 (32 commands)
    // MySQL commands (8)
    this.register({ name: 'mysql connect', description: 'Connect to MySQL database', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'mysql disconnect', description: 'Disconnect from MySQL database', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'mysql query', description: 'Execute SQL query', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'mysql status', description: 'Show MySQL connection status and statistics', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'mysql tables', description: 'List tables in database', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'mysql describe', description: 'Show table structure and indexes', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'mysql import', description: 'Import data from file (SQL, CSV, JSON)', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'mysql export', description: 'Export table data to file', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });

    // MongoDB commands (10)
    this.register({ name: 'mongo connect', description: 'Connect to MongoDB database', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'mongo disconnect', description: 'Disconnect from MongoDB database', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'mongo query', description: 'Query MongoDB collection', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'mongo aggregate', description: 'Execute aggregation pipeline', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'mongo collections', description: 'List all collections in database', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'mongo indexes', description: 'List indexes for a collection', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'mongo import', description: 'Import data into collection', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'mongo export', description: 'Export collection data', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'mongo connections', description: 'List MongoDB connections', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'mongo stats', description: 'Show connection statistics', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });

    // Redis commands (14)
    this.register({ name: 'redis connect', description: 'Connect to a Redis server', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'redis disconnect', description: 'Disconnect from a Redis server', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'redis get', description: 'Get the value of a key', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'redis set', description: 'Set the string value of a key', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'redis keys', description: 'Find all keys matching a pattern', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'redis info', description: 'Get information and statistics about the server', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'redis flush', description: 'Flush (delete) all keys in database', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'redis monitor', description: 'Monitor Redis commands in real-time', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'redis ttl', description: 'Get the time to live for a key', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'redis expire', description: 'Set a timeout on a key', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'redis del', description: 'Delete one or more keys', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });
    this.register({ name: 'redis type', description: 'Determine the type of a key', category: CommandCategory.DATABASE_OPERATIONS, phase: 2, sprint: 2 });

    // Backup commands - Sprint 3 (10 commands)
    this.register({ name: 'backup schedule', description: 'Schedule automated backups', category: CommandCategory.BACKUP_RECOVERY, phase: 2, sprint: 3 });
    this.register({ name: 'backup verify', description: 'Verify backup integrity', category: CommandCategory.BACKUP_RECOVERY, phase: 2, sprint: 3 });
    this.register({ name: 'backup delete', description: 'Delete a backup', category: CommandCategory.BACKUP_RECOVERY, phase: 2, sprint: 3 });
    this.register({ name: 'backup export', description: 'Export backup to external location', category: CommandCategory.BACKUP_RECOVERY, phase: 2, sprint: 3 });
    this.register({ name: 'backup import', description: 'Import backup from external location', category: CommandCategory.BACKUP_RECOVERY, phase: 2, sprint: 3 });
    this.register({ name: 'backup config', description: 'Show or edit backup configuration', category: CommandCategory.BACKUP_RECOVERY, phase: 2, sprint: 3 });

    // Migration commands - Sprint 3 (8 commands)
    this.register({ name: 'migration create', description: 'Create new migration file', category: CommandCategory.MIGRATION, phase: 2, sprint: 3 });
    this.register({ name: 'migration up', description: 'Run pending migrations', category: CommandCategory.MIGRATION, phase: 2, sprint: 3 });
    this.register({ name: 'migration down', description: 'Rollback migrations', category: CommandCategory.MIGRATION, phase: 2, sprint: 3 });
    this.register({ name: 'migration status', description: 'Show migration state', category: CommandCategory.MIGRATION, phase: 2, sprint: 3 });
    this.register({ name: 'migration rollback', description: 'Rollback last migration', category: CommandCategory.MIGRATION, phase: 2, sprint: 3 });
    this.register({ name: 'migration reset', description: 'Rollback all migrations', category: CommandCategory.MIGRATION, phase: 2, sprint: 3 });
    this.register({ name: 'migration fresh', description: 'Drop all and re-run', category: CommandCategory.MIGRATION, phase: 2, sprint: 3 });
    this.register({ name: 'migration redo', description: 'Rollback and re-run last', category: CommandCategory.MIGRATION, phase: 2, sprint: 3 });

    // Security commands - Sprint 3 (7 commands)
    this.register({ name: 'vault-add', description: 'Add credential to secure vault', category: CommandCategory.SECURITY, phase: 2, sprint: 3 });
    this.register({ name: 'vault-list', description: 'List all vault entries', category: CommandCategory.SECURITY, phase: 2, sprint: 3 });
    this.register({ name: 'vault-get', description: 'Get specific vault entry', category: CommandCategory.SECURITY, phase: 2, sprint: 3 });
    this.register({ name: 'vault-delete', description: 'Delete vault entry', category: CommandCategory.SECURITY, phase: 2, sprint: 3 });
    this.register({ name: 'permissions-grant', description: 'Grant permission to role for a resource', category: CommandCategory.SECURITY, phase: 2, sprint: 3 });
    this.register({ name: 'permissions-revoke', description: 'Revoke permission from role for a resource', category: CommandCategory.SECURITY, phase: 2, sprint: 3 });
    this.register({ name: 'audit-log', description: 'Show audit log entries', category: CommandCategory.SECURITY, phase: 2, sprint: 3 });

    // Monitoring commands - Sprint 4 (15 commands)
    this.register({ name: 'health', description: 'Perform database health check', category: CommandCategory.HEALTH_MONITORING, phase: 2, sprint: 4 });
    this.register({ name: 'monitor start', description: 'Start real-time monitoring', category: CommandCategory.HEALTH_MONITORING, phase: 2, sprint: 4 });
    this.register({ name: 'monitor stop', description: 'Stop monitoring', category: CommandCategory.HEALTH_MONITORING, phase: 2, sprint: 4 });
    this.register({ name: 'metrics show', description: 'Show current metrics', category: CommandCategory.HEALTH_MONITORING, phase: 2, sprint: 4 });
    this.register({ name: 'metrics export', description: 'Export metrics in various formats', category: CommandCategory.HEALTH_MONITORING, phase: 2, sprint: 4 });
    this.register({ name: 'alerts setup', description: 'Configure alert settings', category: CommandCategory.HEALTH_MONITORING, phase: 2, sprint: 4 });
    this.register({ name: 'alerts list', description: 'List active alerts', category: CommandCategory.HEALTH_MONITORING, phase: 2, sprint: 4 });
    this.register({ name: 'alerts test', description: 'Test alert notification', category: CommandCategory.HEALTH_MONITORING, phase: 2, sprint: 4 });
    this.register({ name: 'performance analyze', description: 'Analyze system performance', category: CommandCategory.HEALTH_MONITORING, phase: 2, sprint: 4 });
    this.register({ name: 'performance report', description: 'Generate performance report', category: CommandCategory.HEALTH_MONITORING, phase: 2, sprint: 4 });
    this.register({ name: 'grafana setup', description: 'Configure Grafana connection', category: CommandCategory.HEALTH_MONITORING, phase: 2, sprint: 4 });
    this.register({ name: 'grafana deploy-dashboards', description: 'Deploy all dashboards to Grafana', category: CommandCategory.HEALTH_MONITORING, phase: 2, sprint: 4 });
    this.register({ name: 'prometheus', description: 'Configure Prometheus integration', category: CommandCategory.HEALTH_MONITORING, phase: 2, sprint: 4 });

    // Integration commands - Sprint 5 (20 commands)
    this.register({ name: 'slack setup', description: 'Setup Slack integration', category: CommandCategory.INTEGRATION, phase: 2, sprint: 5 });
    this.register({ name: 'slack notify', description: 'Send notification to Slack channel', category: CommandCategory.INTEGRATION, phase: 2, sprint: 5 });
    this.register({ name: 'slack alert', description: 'Send alert to Slack with severity level', category: CommandCategory.INTEGRATION, phase: 2, sprint: 5 });
    this.register({ name: 'slack report', description: 'Generate and send report to Slack', category: CommandCategory.INTEGRATION, phase: 2, sprint: 5 });
    this.register({ name: 'email setup', description: 'Setup email integration', category: CommandCategory.INTEGRATION, phase: 2, sprint: 5 });
    this.register({ name: 'email send', description: 'Send email with optional attachments', category: CommandCategory.INTEGRATION, phase: 2, sprint: 5 });
    this.register({ name: 'email alert', description: 'Send alert email with predefined template', category: CommandCategory.INTEGRATION, phase: 2, sprint: 5 });
    this.register({ name: 'email report', description: 'Generate and send report via email', category: CommandCategory.INTEGRATION, phase: 2, sprint: 5 });
    this.register({ name: 'federation add', description: 'Add database to federation', category: CommandCategory.INTEGRATION, phase: 2, sprint: 5 });
    this.register({ name: 'federation remove', description: 'Remove database from federation', category: CommandCategory.INTEGRATION, phase: 2, sprint: 5 });
    this.register({ name: 'federation query', description: 'Execute federated query across multiple databases', category: CommandCategory.INTEGRATION, phase: 2, sprint: 5 });
    this.register({ name: 'federation status', description: 'Show federation status and connected databases', category: CommandCategory.INTEGRATION, phase: 2, sprint: 5 });
    this.register({ name: 'schema diff', description: 'Compare schemas between two databases', category: CommandCategory.MIGRATION, phase: 2, sprint: 5 });
    this.register({ name: 'schema sync', description: 'Synchronize schema from source to target database', category: CommandCategory.MIGRATION, phase: 2, sprint: 5 });
    this.register({ name: 'schema export', description: 'Export schema to file', category: CommandCategory.MIGRATION, phase: 2, sprint: 5 });
    this.register({ name: 'schema import', description: 'Import schema from file', category: CommandCategory.MIGRATION, phase: 2, sprint: 5 });
    this.register({ name: 'ada start', description: 'Start autonomous database agent', category: CommandCategory.AUTONOMOUS, phase: 2, sprint: 5 });
    this.register({ name: 'ada stop', description: 'Stop autonomous database agent', category: CommandCategory.AUTONOMOUS, phase: 2, sprint: 5 });
    this.register({ name: 'ada status', description: 'Check autonomous agent status', category: CommandCategory.AUTONOMOUS, phase: 2, sprint: 5 });
    this.register({ name: 'ada configure', description: 'Configure autonomous agent settings', category: CommandCategory.AUTONOMOUS, phase: 2, sprint: 5 });
  }

  /**
   * Register Phase 3 commands
   */
  private registerPhase3Commands(): void {
    // Connection Management
    this.register({ name: 'connect', description: 'Connect to a database', category: CommandCategory.CONNECTION, phase: 3 });
    this.register({ name: 'disconnect', description: 'Disconnect from database', category: CommandCategory.CONNECTION, phase: 3 });
    this.register({ name: 'connections', description: 'List active database connections', aliases: ['conns'], category: CommandCategory.CONNECTION, phase: 3 });
    this.register({ name: 'use', description: 'Switch active database connection', category: CommandCategory.CONNECTION, phase: 3 });

    // Context Management
    this.register({ name: 'context save', description: 'Save current context', category: CommandCategory.CONTEXT, phase: 3 });
    this.register({ name: 'context load', description: 'Load saved context', category: CommandCategory.CONTEXT, phase: 3 });
    this.register({ name: 'context list', description: 'List all saved contexts', category: CommandCategory.CONTEXT, phase: 3 });
    this.register({ name: 'context delete', description: 'Delete saved context', category: CommandCategory.CONTEXT, phase: 3 });
    this.register({ name: 'context export', description: 'Export context to file', category: CommandCategory.CONTEXT, phase: 3 });
    this.register({ name: 'context import', description: 'Import context from file', category: CommandCategory.CONTEXT, phase: 3 });

    // Utilities
    this.register({ name: 'interactive', description: 'Start interactive mode (REPL)', aliases: ['i'], category: CommandCategory.UTILITY, phase: 3 });
    this.register({ name: 'features', description: 'List all available features', category: CommandCategory.UTILITY, phase: 3 });
    this.register({ name: 'examples', description: 'Show usage examples', category: CommandCategory.UTILITY, phase: 3 });
  }

  /**
   * Register a command
   */
  private register(metadata: CommandMetadata): void {
    this.commands.set(metadata.name, metadata);

    // Register aliases
    if (metadata.aliases) {
      metadata.aliases.forEach(alias => {
        this.commands.set(alias, { ...metadata, name: alias });
      });
    }
  }

  /**
   * Get command metadata
   */
  getCommand(name: string): CommandMetadata | undefined {
    return this.commands.get(name);
  }

  /**
   * Get all commands
   */
  getAllCommands(): CommandMetadata[] {
    const uniqueCommands = new Map<string, CommandMetadata>();

    for (const [name, metadata] of this.commands) {
      if (!metadata.aliases || !metadata.aliases.includes(name)) {
        uniqueCommands.set(metadata.name, metadata);
      }
    }

    return Array.from(uniqueCommands.values());
  }

  /**
   * Get commands by category
   */
  getCommandsByCategory(category: CommandCategory): CommandMetadata[] {
    return this.getAllCommands().filter(cmd => cmd.category === category);
  }

  /**
   * Get commands by phase
   */
  getCommandsByPhase(phase: 1 | 2 | 3): CommandMetadata[] {
    return this.getAllCommands().filter(cmd => cmd.phase === phase);
  }

  /**
   * Get command count
   */
  getCommandCount(): number {
    return this.getAllCommands().length;
  }

  /**
   * Get statistics
   */
  getStatistics(): {
    total: number;
    byPhase: { [phase: number]: number };
    byCategory: { [category: string]: number };
  } {
    const commands = this.getAllCommands();

    const byPhase: { [phase: number]: number } = { 1: 0, 2: 0, 3: 0 };
    const byCategory: { [category: string]: number } = {};

    commands.forEach(cmd => {
      byPhase[cmd.phase] = (byPhase[cmd.phase] || 0) + 1;
      byCategory[cmd.category] = (byCategory[cmd.category] || 0) + 1;
    });

    return {
      total: commands.length,
      byPhase,
      byCategory
    };
  }

  /**
   * Search commands
   */
  searchCommands(query: string): CommandMetadata[] {
    const lowerQuery = query.toLowerCase();
    return this.getAllCommands().filter(cmd =>
      cmd.name.toLowerCase().includes(lowerQuery) ||
      cmd.description.toLowerCase().includes(lowerQuery) ||
      cmd.category.toLowerCase().includes(lowerQuery)
    );
  }

  /**
   * Generate help text for a category
   */
  getCategoryHelp(category: CommandCategory): string {
    const commands = this.getCommandsByCategory(category);
    let help = `\n${category} Commands (${commands.length})\n`;
    help += '='.repeat(60) + '\n\n';

    commands.forEach(cmd => {
      help += `  ${cmd.name.padEnd(30)} ${cmd.description}\n`;
      if (cmd.aliases && cmd.aliases.length > 0) {
        help += `    Aliases: ${cmd.aliases.join(', ')}\n`;
      }
    });

    return help + '\n';
  }

  /**
   * Generate full help text
   */
  getFullHelp(): string {
    const stats = this.getStatistics();
    let help = '\n';
    help += '╔═══════════════════════════════════════════════════════╗\n';
    help += '║  🤖 AI-Shell - Database Management with AI           ║\n';
    help += `║  Total Commands: ${stats.total.toString().padEnd(36)} ║\n`;
    help += '╚═══════════════════════════════════════════════════════╝\n\n';

    // Group by category
    const categories = Object.values(CommandCategory);
    categories.forEach(category => {
      const commands = this.getCommandsByCategory(category);
      if (commands.length > 0) {
        help += this.getCategoryHelp(category);
      }
    });

    return help;
  }
}

// Singleton instance
export const commandRegistry = new CommandRegistry();

// Export utilities
export function getCommand(name: string): CommandMetadata | undefined {
  return commandRegistry.getCommand(name);
}

export function getAllCommands(): CommandMetadata[] {
  return commandRegistry.getAllCommands();
}

export function getCommandsByCategory(category: CommandCategory): CommandMetadata[] {
  return commandRegistry.getCommandsByCategory(category);
}

export function getCommandCount(): number {
  return commandRegistry.getCommandCount();
}

export function searchCommands(query: string): CommandMetadata[] {
  return commandRegistry.searchCommands(query);
}

export default commandRegistry;
