#!/usr/bin/env node

/**
 * AI-Shell CLI - Database Management Tool with AI Integration
 *
 * Main entry point integrating all 10 feature modules:
 * - Query Optimizer (Phase 1)
 * - Health Monitor (Phase 1)
 * - Backup System (Phase 1)
 * - Query Federation (Phase 2)
 * - Schema Designer (Phase 2)
 * - Query Cache (Phase 2)
 * - Migration Tester (Phase 3)
 * - SQL Explainer (Phase 3)
 * - Schema Diff (Phase 3)
 * - Cost Optimizer (Phase 3)
 */

import { Command } from 'commander';
import chalk from 'chalk';
import { FeatureCommands } from './feature-commands';
import { CLIWrapper, CLIOptions } from './cli-wrapper';
import { createLogger } from '../core/logger';
import { OptimizationCLI } from './optimization-cli';
import { registerOptimizationCommands } from './optimization-commands';
import { ContextManager } from './context-manager';
import { setupBackupCommands } from './backup-cli';
import { createSSOCLI } from './sso-cli';

const logger = createLogger('CLI');
const program = new Command();
const contextManager = new ContextManager();

// SSO CLI instance
let ssoCli: ReturnType<typeof createSSOCLI> | null = null;
function getSSOCLI() {
  if (!ssoCli) {
    ssoCli = createSSOCLI();
  }
  return ssoCli;
}

// Lazy-load features to avoid initialization at module load time
let features: FeatureCommands | null = null;
function getFeatures(): FeatureCommands {
  if (!features) {
    features = new FeatureCommands();
  }
  return features;
}

// Optimization CLI instance
let optimizationCli: OptimizationCLI | null = null;
function getOptimizationCLI(): OptimizationCLI {
  if (!optimizationCli) {
    optimizationCli = new OptimizationCLI();
  }
  return optimizationCli;
}

// CLI Wrapper instance for enhanced command execution
let cliWrapper: CLIWrapper | null = null;
function getCLIWrapper(): CLIWrapper {
  if (!cliWrapper) {
    cliWrapper = new CLIWrapper();
  }
  return cliWrapper;
}

// CLI metadata
program
  .name('ai-shell')
  .version('1.0.0')
  .description(chalk.bold('AI-Powered Database Management CLI'))
  .addHelpText('before', `
╔═══════════════════════════════════════════════════════╗
║  ${chalk.cyan.bold('🤖 AI-Shell')} - Database Management with AI         ║
║  Intelligent query optimization, monitoring & more   ║
╚═══════════════════════════════════════════════════════╝
  `)
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell optimize "SELECT * FROM users WHERE active = true"
  ${chalk.dim('$')} ai-shell monitor --interval 10000
  ${chalk.dim('$')} ai-shell backup --connection production
  ${chalk.dim('$')} ai-shell federate "SELECT * FROM db1.users JOIN db2.orders" --databases db1,db2
  ${chalk.dim('$')} ai-shell explain "SELECT * FROM users WHERE id > 100"

${chalk.bold('Environment Variables:')}
  ${chalk.yellow('ANTHROPIC_API_KEY')}  - Required for AI features
  ${chalk.yellow('DATABASE_URL')}       - Default database connection
  ${chalk.yellow('REDIS_URL')}          - For query caching

${chalk.bold('Documentation:')}
  Visit: https://github.com/yourusername/ai-shell
`);

// Global options
program
  .option('-v, --verbose', 'Enable verbose logging')
  .option('-j, --json', 'Output results in JSON format')
  .option('-c, --config <path>', 'Path to configuration file')
  .option('-f, --format <type>', 'Output format (json, table, csv)', 'table')
  .option('--explain', 'Show AI explanation of what will happen')
  .option('--dry-run', 'Simulate command without making changes')
  .option('--output <file>', 'Write output to file')
  .option('--limit <count>', 'Limit results count', parseInt)
  .option('--timeout <ms>', 'Command timeout in milliseconds', parseInt)
  .option('--timestamps', 'Show timestamps in output')
  .hook('preAction', (thisCommand) => {
    const opts = thisCommand.opts();
    if (opts.verbose) {
      process.env.LOG_LEVEL = 'debug';
      logger.info('Verbose mode enabled');
    }
    if (opts.config) {
      logger.info('Using config file', { path: opts.config });
    }
  });

// ============================================================================
// PHASE 1 COMMANDS - Core Database Operations
// ============================================================================

const phase1 = program
  .command('phase1')
  .description(chalk.cyan('Phase 1 Commands - Core Operations'));

phase1
  .command('info')
  .description('Show Phase 1 features')
  .action(() => {
    console.log(chalk.cyan.bold('\n📋 Phase 1 Features:\n'));
    console.log('  1. Query Optimizer - AI-powered SQL optimization');
    console.log('  2. Health Monitor - Real-time database monitoring');
    console.log('  3. Backup System - Automated backup and recovery\n');
  });

// Query Optimizer Commands
program
  .command('optimize <query>')
  .description('Optimize a SQL query using AI analysis')
  .alias('opt')
  .option('--explain', 'Show query execution plan')
  .option('--dry-run', 'Validate without executing')
  .option('--format <type>', 'Output format (text, json)', 'text')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell optimize "SELECT * FROM users WHERE id > 100"
  ${chalk.dim('$')} ai-shell opt "SELECT u.*, o.* FROM users u JOIN orders o ON u.id = o.user_id"
  ${chalk.dim('$')} ai-shell optimize "SELECT * FROM users" --explain
  ${chalk.dim('$')} ai-shell optimize "DELETE FROM users" --dry-run
`)
  .action(async (query: string, options) => {
    try {
      await getFeatures().optimizeQuery(query, options);
    } catch (error) {
      logger.error('Optimization failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

program
  .command('analyze-slow-queries')
  .description('Analyze and optimize slow queries from log')
  .alias('slow')
  .option('-t, --threshold <ms>', 'Minimum execution time in ms', '1000')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell analyze-slow-queries
  ${chalk.dim('$')} ai-shell slow --threshold 500
`)
  .action(async (options) => {
    try {
      await getFeatures().analyzeSlowQueries();
    } catch (error) {
      logger.error('Analysis failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

// Health Monitor Commands
program
  .command('health-check')
  .description('Perform comprehensive database health check')
  .alias('health')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell health-check
  ${chalk.dim('$')} ai-shell health --json
`)
  .action(async () => {
    try {
      await getFeatures().healthCheck();
    } catch (error) {
      logger.error('Health check failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

program
  .command('monitor')
  .description('Start real-time database monitoring')
  .option('-i, --interval <ms>', 'Monitoring interval in milliseconds', '5000')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell monitor
  ${chalk.dim('$')} ai-shell monitor --interval 10000
  ${chalk.dim('$')} ai-shell monitor -i 3000
`)
  .action(async (options) => {
    try {
      const interval = parseInt(options.interval);
      await getFeatures().startMonitoring(interval);
    } catch (error) {
      logger.error('Monitoring failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

program
  .command('alerts setup')
  .description('Configure health monitoring alerts')
  .option('-s, --slack <webhook>', 'Slack webhook URL')
  .option('-e, --email <addresses>', 'Email addresses (comma-separated)')
  .option('-w, --webhook <url>', 'Custom webhook URL')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell alerts setup --slack https://hooks.slack.com/...
  ${chalk.dim('$')} ai-shell alerts setup --email admin@company.com,ops@company.com
`)
  .action(async (options) => {
    try {
      const config = {
        enabled: true,
        channels: {
          slack: options.slack ? { webhookUrl: options.slack, enabled: true } : undefined,
          email: options.email ? { to: options.email.split(','), enabled: true } : undefined,
          webhook: options.webhook ? { url: options.webhook, enabled: true } : undefined
        }
      };
      await getFeatures().setupAlerts(config);
    } catch (error) {
      logger.error('Alert setup failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

// Backup System Commands
program
  .command('backup')
  .description('Create database backup')
  .option('-c, --connection <name>', 'Connection name (uses active if not specified)')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell backup
  ${chalk.dim('$')} ai-shell backup --connection production
  ${chalk.dim('$')} ai-shell backup -c staging
`)
  .action(async (options) => {
    try {
      await getFeatures().createBackup(options.connection);
    } catch (error) {
      logger.error('Backup failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

program
  .command('restore <backup-id>')
  .description('Restore database from backup')
  .option('-d, --dry-run', 'Simulate restore without making changes')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell restore backup-1234567890
  ${chalk.dim('$')} ai-shell restore backup-1234567890 --dry-run
`)
  .action(async (backupId: string, options) => {
    try {
      await getFeatures().restoreBackup(backupId, options.dryRun);
    } catch (error) {
      logger.error('Restore failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

program
  .command('backup-list')
  .description('List all backups')
  .alias('backups')
  .option('-l, --limit <count>', 'Maximum number of backups to show', '20')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell backup-list
  ${chalk.dim('$')} ai-shell backups --limit 10
`)
  .action(async (options) => {
    try {
      await getFeatures().listBackups();
    } catch (error) {
      logger.error('Failed to list backups', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

// ============================================================================
// PHASE 2 COMMANDS - Advanced Features
// ============================================================================

// Import Phase 2 command modules
import { registerOptimizeCommand } from './commands/optimize';
import { registerSlowQueriesCommand } from './commands/slow-queries';
import { registerIndexesCommand } from './commands/indexes';
import { registerRiskCheckCommand } from './commands/risk-check';

// Register Phase 2 Query Optimization commands
registerOptimizeCommand(program);
registerSlowQueriesCommand(program);
registerIndexesCommand(program);
registerRiskCheckCommand(program);

const phase2 = program
  .command('phase2')
  .description(chalk.cyan('Phase 2 Commands - Advanced Features'));

phase2
  .command('info')
  .description('Show Phase 2 features')
  .action(() => {
    console.log(chalk.cyan.bold('\n📋 Phase 2 Features:\n'));
    console.log('  4. Query Optimization - AI-powered optimization suite');
    console.log('  5. Slow Query Analysis - Performance monitoring');
    console.log('  6. Index Management - Smart index recommendations');
    console.log('  7. Risk Analysis - Query safety checks');
    console.log('  8. Query Federation - Cross-database queries');
    console.log('  9. Schema Designer - AI-powered schema design');
    console.log(' 10. Query Cache - Redis-based caching\n');
  });

// Query Federation Commands
program
  .command('federate <query>')
  .description('Execute query across multiple databases')
  .alias('fed')
  .option('-d, --databases <list>', 'Comma-separated list of database names')
  .requiredOption('-d, --databases <list>', 'Databases to query (required)')
  .option('--explain', 'Show execution plan for federated query')
  .option('--dry-run', 'Validate without executing')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell federate "SELECT * FROM users" --databases db1,db2,db3
  ${chalk.dim('$')} ai-shell fed "SELECT u.*, o.* FROM users u JOIN orders o" -d production,analytics
  ${chalk.dim('$')} ai-shell federate "SELECT * FROM users" -d db1,db2 --explain
  ${chalk.dim('$')} ai-shell federate "DELETE FROM users" -d db1,db2 --dry-run
`)
  .action(async (query: string, options) => {
    try {
      const databases = options.databases.split(',').map((s: string) => s.trim());
      await getFeatures().federateQuery(query, databases, options);
    } catch (error) {
      logger.error('Federation failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

program
  .command('join <db1> <db2>')
  .description('Execute cross-database join')
  .option('-l, --left-table <table>', 'Left table name')
  .option('-r, --right-table <table>', 'Right table name')
  .option('-k, --key <column>', 'Join key column')
  .option('-t, --type <type>', 'Join type (inner, left, right, full)', 'inner')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell join db1 db2 --left-table users --right-table orders --key user_id
`)
  .action(async (db1: string, db2: string, options) => {
    try {
      console.log(chalk.yellow('Join operation requires additional implementation'));
    } catch (error) {
      logger.error('Join failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

// Schema Designer Commands
program
  .command('design-schema')
  .description('Interactive schema design with AI assistance')
  .alias('design')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell design-schema
  ${chalk.dim('$')} ai-shell design
`)
  .action(async () => {
    try {
      await getFeatures().designSchema();
    } catch (error) {
      logger.error('Schema design failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

program
  .command('validate-schema <file>')
  .description('Validate schema definition file')
  .alias('validate')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell validate-schema schema.json
  ${chalk.dim('$')} ai-shell validate ./schemas/users.json
`)
  .action(async (file: string) => {
    try {
      await getFeatures().validateSchema(file);
    } catch (error) {
      logger.error('Schema validation failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

// Query Cache Commands
program
  .command('cache enable')
  .description('Enable query caching')
  .option('-r, --redis <url>', 'Redis connection URL')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell cache enable
  ${chalk.dim('$')} ai-shell cache enable --redis redis://localhost:6379
`)
  .action(async (options) => {
    try {
      await getFeatures().enableCache(options.redis);
    } catch (error) {
      logger.error('Cache enable failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

program
  .command('cache stats')
  .description('Show cache statistics')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell cache stats
  ${chalk.dim('$')} ai-shell cache stats --json
`)
  .action(async () => {
    try {
      await getFeatures().cacheStats();
    } catch (error) {
      logger.error('Failed to get cache stats', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

program
  .command('cache clear')
  .description('Clear all cached queries')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell cache clear
`)
  .action(async () => {
    try {
      await getFeatures().clearCache();
    } catch (error) {
      logger.error('Cache clear failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

// ============================================================================
// PHASE 3 COMMANDS - Advanced Analysis
// ============================================================================

const phase3 = program
  .command('phase3')
  .description(chalk.cyan('Phase 3 Commands - Advanced Analysis'));

phase3
  .command('info')
  .description('Show Phase 3 features')
  .action(() => {
    console.log(chalk.cyan.bold('\n📋 Phase 3 Features:\n'));
    console.log('  7. Migration Tester - Test migrations before deployment');
    console.log('  8. SQL Explainer - Natural language SQL explanations');
    console.log('  9. Schema Diff - Compare database schemas');
    console.log(' 10. Cost Optimizer - Cloud cost optimization\n');
  });

// Migration Tester Commands
program
  .command('test-migration <file>')
  .description('Test migration file in isolated environment')
  .alias('test-mig')
  .option('-c, --connection <name>', 'Connection to test against')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell test-migration migrations/001_add_users.sql
  ${chalk.dim('$')} ai-shell test-mig ./migrations/002_alter_orders.sql
`)
  .action(async (file: string, options) => {
    try {
      await getFeatures().testMigration(file);
    } catch (error) {
      logger.error('Migration test failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

program
  .command('validate-migration <file>')
  .description('Validate migration syntax and safety')
  .alias('check-mig')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell validate-migration migrations/001_add_users.sql
`)
  .action(async (file: string) => {
    console.log(chalk.yellow('Migration validation feature coming soon'));
  });

// SQL Explainer Commands
program
  .command('explain <query>')
  .description('Get AI-powered explanation of SQL query')
  .alias('exp')
  .option('--format <type>', 'Output format (text, json)', 'text')
  .option('--analyze', 'Include performance analysis')
  .option('--dry-run', 'Validate query without execution')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell explain "SELECT * FROM users WHERE created_at > NOW() - INTERVAL 7 DAY"
  ${chalk.dim('$')} ai-shell exp "SELECT u.*, COUNT(o.id) FROM users u LEFT JOIN orders o GROUP BY u.id"
  ${chalk.dim('$')} ai-shell explain "SELECT * FROM users" --format json
  ${chalk.dim('$')} ai-shell explain "UPDATE users SET active = false" --dry-run
`)
  .action(async (query: string, options) => {
    try {
      await getFeatures().explainSQL(query, options);
    } catch (error) {
      logger.error('Explanation failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

program
  .command('translate <natural-language>')
  .description('Convert natural language to SQL')
  .alias('nl2sql')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell translate "Show me all users created in the last week"
  ${chalk.dim('$')} ai-shell nl2sql "Count orders by user for active users"
`)
  .action(async (naturalLanguage: string) => {
    try {
      await getFeatures().translateToSQL(naturalLanguage);
    } catch (error) {
      logger.error('Translation failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

// Schema Diff Commands
program
  .command('diff <db1> <db2>')
  .description('Compare schemas between two databases')
  .option('-o, --output <file>', 'Output diff to file')
  .option('-f, --format <type>', 'Output format (text, json, sql)', 'text')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell diff production staging
  ${chalk.dim('$')} ai-shell diff db1 db2 --output schema-diff.json --format json
`)
  .action(async (db1: string, db2: string, options) => {
    try {
      await getFeatures().diffSchemas(db1, db2);
    } catch (error) {
      logger.error('Schema diff failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

program
  .command('sync-schema <source> <target>')
  .description('Generate SQL to sync schemas')
  .option('-d, --dry-run', 'Show SQL without executing')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell sync-schema production staging --dry-run
  ${chalk.dim('$')} ai-shell sync-schema db1 db2
`)
  .action(async (source: string, target: string, options) => {
    console.log(chalk.yellow('Schema sync feature coming soon'));
  });

// Cost Optimizer Commands
program
  .command('analyze-costs <provider> <region>')
  .description('Analyze database costs and get optimization recommendations')
  .alias('costs')
  .option('-d, --detailed', 'Show detailed breakdown')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell analyze-costs aws us-east-1
  ${chalk.dim('$')} ai-shell costs gcp us-central1 --detailed
  ${chalk.dim('$')} ai-shell analyze-costs azure eastus
`)
  .action(async (provider: string, region: string, options) => {
    try {
      await getFeatures().analyzeCosts(provider, region);
    } catch (error) {
      logger.error('Cost analysis failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

program
  .command('optimize-costs')
  .description('Get AI-powered cost optimization recommendations')
  .alias('save-money')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell optimize-costs
  ${chalk.dim('$')} ai-shell save-money
`)
  .action(async () => {
    console.log(chalk.yellow('Cost optimization recommendations feature coming soon'));
  });

// ============================================================================
// DATABASE CONNECTION COMMANDS
// ============================================================================

program
  .command('connect <connection-string>')
  .description('Connect to a database (postgresql://, mysql://, mongodb://, redis://)')
  .option('--name <name>', 'Connection name (default: auto-generated)')
  .option('--test', 'Test connection only without saving')
  .option('--set-active', 'Set as active connection', true)
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell connect postgresql://user:pass@localhost:5432/mydb --name production
  ${chalk.dim('$')} ai-shell connect mysql://root:secret@localhost:3306/testdb
  ${chalk.dim('$')} ai-shell connect mongodb://localhost:27017/appdb --name mongo
  ${chalk.dim('$')} ai-shell connect redis://localhost:6379 --name cache
  ${chalk.dim('$')} ai-shell connect postgresql://localhost/mydb --test

${chalk.bold('Supported Protocols:')}
  • postgresql:// or postgres://
  • mysql://
  • mongodb:// or mongodb+srv://
  • redis:// or rediss:// (SSL)
  • sqlite://path/to/db.sqlite

${chalk.bold('Environment Variable:')}
  Set DATABASE_URL to use as default connection
`)
  .action(async (connectionString: string, options) => {
    try {
      const { DatabaseConnectionManager } = await import('./database-manager');
      const { StateManager } = await import('../core/state-manager');
      const dbManager = new DatabaseConnectionManager(new StateManager());

      // Parse connection string
      const parsed = DatabaseConnectionManager.parseConnectionString(connectionString);

      // Generate name if not provided
      const name = options.name || `${parsed.type}-${Date.now()}`;

      const config = {
        ...parsed,
        name,
        connectionString
      };

      if (options.test) {
        console.log(chalk.blue('\n🔍 Testing connection...\n'));
        const result = await dbManager.testConnection(config as any);

        if (result.healthy) {
          console.log(chalk.green('✅ Connection successful!'));
          console.log(`   Latency: ${result.latency}ms`);
        } else {
          console.log(chalk.red('❌ Connection failed:'));
          console.log(`   ${result.error}`);
          process.exit(1);
        }
      } else {
        console.log(chalk.blue('\n🔌 Connecting to database...\n'));
        const connection = await dbManager.connect(config as any);

        console.log(chalk.green('✅ Connected successfully!'));
        console.log(`   Name: ${name}`);
        console.log(`   Type: ${connection.type}`);
        console.log(`   Database: ${config.database || 'N/A'}`);
        console.log(`   Host: ${config.host || 'N/A'}`);

        if (options.setActive) {
          await dbManager.switchActive(name);
          console.log(chalk.cyan('\n   Set as active connection'));
        }
      }
    } catch (error) {
      logger.error('Connection failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

program
  .command('disconnect [name]')
  .description('Disconnect from database (disconnect all if no name provided)')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell disconnect production
  ${chalk.dim('$')} ai-shell disconnect           ${chalk.dim('# Disconnect all')}
`)
  .action(async (name?: string) => {
    try {
      const { DatabaseConnectionManager } = await import('./database-manager');
      const { StateManager } = await import('../core/state-manager');
      const dbManager = new DatabaseConnectionManager(new StateManager());

      if (name) {
        console.log(chalk.blue(`\n🔌 Disconnecting from: ${name}\n`));
        await dbManager.disconnect(name);
        console.log(chalk.green('✅ Disconnected successfully'));
      } else {
        console.log(chalk.blue('\n🔌 Disconnecting all connections...\n'));
        await dbManager.disconnectAll();
        console.log(chalk.green('✅ All connections disconnected'));
      }
    } catch (error) {
      logger.error('Disconnect failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

program
  .command('connections')
  .description('List active database connections')
  .alias('conns')
  .option('--verbose', 'Show detailed connection information')
  .option('--health', 'Run health checks on all connections')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell connections
  ${chalk.dim('$')} ai-shell conns --verbose
  ${chalk.dim('$')} ai-shell connections --health
`)
  .action(async (options) => {
    try {
      const { DatabaseConnectionManager } = await import('./database-manager');
      const { StateManager } = await import('../core/state-manager');
      const dbManager = new DatabaseConnectionManager(new StateManager());

      const connections = dbManager.listConnections();

      if (connections.length === 0) {
        console.log(chalk.yellow('\nNo active connections'));
        console.log(chalk.dim('Use: ai-shell connect <connection-string> to create a connection\n'));
        return;
      }

      console.log(chalk.blue(`\n📊 Active Connections (${connections.length})\n`));

      if (options.health) {
        console.log(chalk.dim('Running health checks...\n'));
      }

      const Table = (await import('cli-table3')).default;
      const table = new Table({
        head: [
          chalk.bold('Name'),
          chalk.bold('Type'),
          chalk.bold('Database'),
          chalk.bold('Host:Port'),
          chalk.bold('Active'),
          ...(options.health ? [chalk.bold('Health')] : [])
        ],
        colWidths: [20, 15, 20, 25, 10, ...(options.health ? [15] : [])]
      });

      for (const conn of connections) {
        let healthStatus = '';

        if (options.health) {
          const health = await dbManager.healthCheck(conn.name);
          healthStatus = health.healthy
            ? chalk.green(`✓ ${health.latency}ms`)
            : chalk.red(`✗ ${health.error?.substring(0, 20) || 'Failed'}`);
        }

        table.push([
          conn.name,
          conn.type,
          conn.database || 'N/A',
          conn.host ? `${conn.host}:${conn.port || 'default'}` : 'N/A',
          conn.isActive ? chalk.green('✓') : '',
          ...(options.health ? [healthStatus] : [])
        ]);
      }

      console.log(table.toString());

      if (options.verbose) {
        const stats = dbManager.getStatistics();
        console.log(chalk.bold('\nStatistics:'));
        console.log(`  Total Connections: ${stats.totalConnections}`);
        console.log(`  Healthy Connections: ${stats.healthyConnections}`);
        console.log(`  Active: ${stats.activeConnection || 'None'}`);
        console.log(chalk.bold('\nBy Type:'));
        Object.entries(stats.connectionsByType).forEach(([type, count]) => {
          console.log(`  ${type}: ${count}`);
        });
      }

      console.log('');
    } catch (error) {
      logger.error('Failed to list connections', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

program
  .command('use <connection-name>')
  .description('Switch active database connection')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell use production
  ${chalk.dim('$')} ai-shell use staging
`)
  .action(async (connectionName: string) => {
    try {
      const { DatabaseConnectionManager } = await import('./database-manager');
      const { StateManager } = await import('../core/state-manager');
      const dbManager = new DatabaseConnectionManager(new StateManager());

      await dbManager.switchActive(connectionName);
      console.log(chalk.green(`\n✅ Active connection switched to: ${connectionName}\n`));
    } catch (error) {
      logger.error('Switch failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

// ============================================================================
// OPTIMIZATION COMMANDS (Extended Features)
// ============================================================================
registerOptimizationCommands(program, getOptimizationCLI);

// ============================================================================
// SECURITY COMMANDS
// ============================================================================

// Vault Commands
program
  .command('vault-add <name> <value>')
  .description('Add credential to secure vault')
  .option('--encrypt', 'Encrypt the value')
  .action(async (name: string, value: string, options) => {
    try {
      const { SecurityCLI } = await import('./security-cli');
      const securityCLI = new SecurityCLI();
      await securityCLI.addVaultEntry(name, value, options);
    } catch (error) {
      logger.error('Vault add failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

program
  .command('vault-list')
  .description('List all vault entries')
  .option('--show-passwords', 'Show actual passwords')
  .option('--format <type>', 'Output format (json, table)', 'table')
  .action(async (options) => {
    try {
      const { SecurityCLI } = await import('./security-cli');
      const securityCLI = new SecurityCLI();
      await securityCLI.listVaultEntries(options);
    } catch (error) {
      logger.error('Vault list failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

program
  .command('audit-show')
  .description('Show audit log entries')
  .option('--limit <n>', 'Limit entries', '100')
  .option('--user <user>', 'Filter by user')
  .action(async (options) => {
    try {
      const { SecurityCLI } = await import('./security-cli');
      const securityCLI = new SecurityCLI();
      await securityCLI.showAuditLog({
        limit: parseInt(options.limit),
        user: options.user
      });
    } catch (error) {
      logger.error('Audit show failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

program
  .command('security-scan')
  .description('Run security scan')
  .option('--deep', 'Deep scan')
  .action(async (options) => {
    try {
      const { SecurityCLI } = await import('./security-cli');
      const securityCLI = new SecurityCLI();
      await securityCLI.runSecurityScan({ deep: options.deep });
    } catch (error) {
      logger.error('Security scan failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

// ============================================================================
// UTILITY COMMANDS
// ============================================================================

program
  .command('interactive')
  .description('Start interactive mode (REPL)')
  .alias('i')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell interactive
  ${chalk.dim('$')} ai-shell i
`)
  .action(async () => {
    console.log(chalk.cyan.bold('\n🤖 Starting AI-Shell Interactive Mode...\n'));
    console.log(chalk.yellow('Interactive mode not yet implemented'));
    console.log('For now, use individual commands like:');
    console.log('  ai-shell optimize <query>');
    console.log('  ai-shell monitor');
    console.log('  ai-shell backup\n');
  });

program
  .command('features')
  .description('List all available features')
  .action(() => {
    console.log(chalk.cyan.bold('\n📋 AI-Shell Features (10 Total)\n'));

    console.log(chalk.bold('Phase 1 - Core Operations:'));
    console.log('  1. ✓ Query Optimizer      - AI-powered SQL optimization');
    console.log('  2. ✓ Health Monitor       - Real-time database monitoring');
    console.log('  3. ✓ Backup System        - Automated backup and recovery\n');

    console.log(chalk.bold('Phase 2 - Advanced Features:'));
    console.log('  4. ✓ Query Federation     - Cross-database queries');
    console.log('  5. ✓ Schema Designer      - AI-powered schema design');
    console.log('  6. ✓ Query Cache          - Redis-based query caching\n');

    console.log(chalk.bold('Phase 3 - Advanced Analysis:'));
    console.log('  7. ✓ Migration Tester     - Test migrations safely');
    console.log('  8. ✓ SQL Explainer        - Natural language explanations');
    console.log('  9. ✓ Schema Diff          - Compare database schemas');
    console.log(' 10. ✓ Cost Optimizer       - Cloud cost optimization\n');
  });

program
  .command('examples')
  .description('Show usage examples')
  .action(() => {
    console.log(chalk.cyan.bold('\n📚 AI-Shell Examples\n'));

    console.log(chalk.bold('Query Optimization:'));
    console.log('  ai-shell optimize "SELECT * FROM users WHERE active = true"');
    console.log('  ai-shell analyze-slow-queries --threshold 500\n');

    console.log(chalk.bold('Health Monitoring:'));
    console.log('  ai-shell health-check');
    console.log('  ai-shell monitor --interval 10000');
    console.log('  ai-shell alerts setup --slack https://hooks.slack.com/...\n');

    console.log(chalk.bold('Backup & Recovery:'));
    console.log('  ai-shell backup --connection production');
    console.log('  ai-shell restore backup-1234567890');
    console.log('  ai-shell backup-list\n');

    console.log(chalk.bold('Advanced Features:'));
    console.log('  ai-shell federate "SELECT * FROM users" --databases db1,db2');
    console.log('  ai-shell design-schema');
    console.log('  ai-shell cache enable --redis redis://localhost:6379\n');

    console.log(chalk.bold('Analysis & Optimization:'));
    console.log('  ai-shell explain "SELECT u.*, COUNT(o.id) FROM users u..."');
    console.log('  ai-shell translate "Show all users created last week"');
    console.log('  ai-shell diff production staging');
    console.log('  ai-shell analyze-costs aws us-east-1\n');

    console.log(chalk.bold('Global Flags (use with any command):'));
    console.log('  --format json       Output in JSON format');
    console.log('  --format csv        Output in CSV format');
    console.log('  --verbose          Enable verbose logging');
    console.log('  --explain          Show AI explanation before execution');
    console.log('  --dry-run          Simulate without making changes');
    console.log('  --output file.json Write output to file');
    console.log('  --limit 10         Limit results to 10 items');
    console.log('  --timestamps       Show timestamps in output\n');

    console.log(chalk.bold('CLI Wrapper Examples:'));
    console.log('  ai-shell optimize "SELECT * FROM users" --format json --output result.json');
    console.log('  ai-shell backup --explain --dry-run');
    console.log('  ai-shell health-check --format csv --output health.csv');
    console.log('  ai-shell backup-list --limit 5 --timestamps\n');
  });

program
  .command('wrapper-demo')
  .description('Demonstrate CLI wrapper capabilities')
  .action(async () => {
    console.log(chalk.cyan.bold('\n🚀 CLI Wrapper Framework Demo\n'));

    const wrapper = getCLIWrapper();
    const commands = wrapper.getRegisteredCommands();

    console.log(chalk.bold(`Total Commands: ${commands.length}\n`));

    console.log(chalk.bold('Available Commands:\n'));
    commands.forEach(cmd => {
      console.log(chalk.green(`  ${cmd.name.padEnd(20)}`), chalk.dim(`- ${cmd.description}`));
      if (cmd.aliases.length > 0) {
        console.log(chalk.dim(`    Aliases: ${cmd.aliases.join(', ')}`));
      }
    });

    console.log(chalk.bold('\n\nKey Features:\n'));
    console.log('  ✓ Command routing and execution');
    console.log('  ✓ Multiple output formats (JSON, table, CSV)');
    console.log('  ✓ Global flags (--format, --verbose, --explain, --dry-run)');
    console.log('  ✓ Environment variable integration');
    console.log('  ✓ Timeout handling');
    console.log('  ✓ Comprehensive error handling');
    console.log('  ✓ File output support');
    console.log('  ✓ Command aliases\n');
  });

// ============================================================================
// CONTEXT MANAGEMENT COMMANDS
// ============================================================================

const contextCmd = program
  .command('context')
  .description('Manage query contexts and configurations');

contextCmd
  .command('save <name>')
  .description('Save current context')
  .option('-d, --description <text>', 'Context description')
  .option('--include-history', 'Include query history')
  .option('--include-aliases', 'Include aliases')
  .option('--include-config', 'Include configuration')
  .option('--include-variables', 'Include variables')
  .option('--include-connections', 'Include connection info')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell context save my-project --description "Production context"
  ${chalk.dim('$')} ai-shell context save dev-env --include-history --include-config
  ${chalk.dim('$')} ai-shell context save prod --include-all
`)
  .action(async (name: string, options) => {
    try {
      await contextManager.initialize();
      await contextManager.saveContext(name, {
        description: options.description,
        includeHistory: options.includeHistory,
        includeAliases: options.includeAliases,
        includeConfig: options.includeConfig,
        includeVariables: options.includeVariables,
        includeConnections: options.includeConnections
      });
      console.log(chalk.green(`\n✅ Context "${name}" saved successfully\n`));
    } catch (error) {
      logger.error('Context save failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

contextCmd
  .command('load <name>')
  .description('Load saved context')
  .option('--merge', 'Merge with current context')
  .option('--overwrite', 'Overwrite current context (default)')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell context load my-project
  ${chalk.dim('$')} ai-shell context load dev-env --merge
`)
  .action(async (name: string, options) => {
    try {
      await contextManager.initialize();
      await contextManager.loadContext(name, options.merge || false);
      console.log(chalk.green(`\n✅ Context "${name}" loaded successfully\n`));
    } catch (error) {
      logger.error('Context load failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

contextCmd
  .command('list')
  .description('List all saved contexts')
  .option('-v, --verbose', 'Show detailed information')
  .option('-f, --format <type>', 'Output format (table, json)', 'table')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell context list
  ${chalk.dim('$')} ai-shell context list --verbose
  ${chalk.dim('$')} ai-shell context list --format json
`)
  .action(async (options) => {
    try {
      await contextManager.initialize();
      const contexts = await contextManager.listContexts(options.verbose);

      if (options.format === 'json') {
        console.log(JSON.stringify(contexts, null, 2));
      } else {
        console.log(chalk.cyan.bold('\n📋 Saved Contexts\n'));
        if (contexts.length === 0) {
          console.log(chalk.yellow('No contexts saved yet\n'));
        } else {
          contexts.forEach(ctx => {
            console.log(chalk.bold(ctx.name));
            if (ctx.description) {
              console.log(chalk.dim(`  ${ctx.description}`));
            }
            console.log(chalk.dim(`  Created: ${ctx.createdAt.toLocaleString()}`));
            console.log(chalk.dim(`  Updated: ${ctx.updatedAt.toLocaleString()}`));
            if (options.verbose) {
              console.log(chalk.dim(`  Size: ${(ctx.size / 1024).toFixed(2)} KB`));
              if (ctx.queryCount !== undefined) {
                console.log(chalk.dim(`  Queries: ${ctx.queryCount}`));
              }
              if (ctx.aliasCount !== undefined) {
                console.log(chalk.dim(`  Aliases: ${ctx.aliasCount}`));
              }
            }
            console.log('');
          });
        }
      }
    } catch (error) {
      logger.error('Context list failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

contextCmd
  .command('delete <name>')
  .description('Delete saved context')
  .option('--force', 'Force deletion even if current context')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell context delete old-project
  ${chalk.dim('$')} ai-shell context delete test --force
`)
  .action(async (name: string, options) => {
    try {
      await contextManager.initialize();
      await contextManager.deleteContext(name, options.force);
      console.log(chalk.green(`\n✅ Context "${name}" deleted successfully\n`));
    } catch (error) {
      logger.error('Context delete failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

contextCmd
  .command('export <name> <file>')
  .description('Export context to file')
  .option('-f, --format <type>', 'Export format (json, yaml)', 'json')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell context export my-project context.json
  ${chalk.dim('$')} ai-shell context export prod context.yaml --format yaml
`)
  .action(async (name: string, file: string, options) => {
    try {
      await contextManager.initialize();
      await contextManager.exportContext(name, file, options.format);
      console.log(chalk.green(`\n✅ Context exported to "${file}"\n`));
    } catch (error) {
      logger.error('Context export failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

contextCmd
  .command('import <file>')
  .description('Import context from file')
  .option('-n, --name <name>', 'Import with new name')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell context import context.json
  ${chalk.dim('$')} ai-shell context import backup.yaml --name restored
`)
  .action(async (file: string, options) => {
    try {
      await contextManager.initialize();
      await contextManager.importContext(file, options.name);
      console.log(chalk.green(`\n✅ Context imported from "${file}"\n`));
    } catch (error) {
      logger.error('Context import failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

contextCmd
  .command('show [name]')
  .description('Show context details')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell context show
  ${chalk.dim('$')} ai-shell context show my-project
`)
  .action(async (name?: string) => {
    try {
      await contextManager.initialize();
      const context = await contextManager.showContext(name);
      console.log(chalk.cyan.bold('\n📄 Context Details\n'));
      console.log(chalk.bold('Name:'), context.name);
      if (context.description) {
        console.log(chalk.bold('Description:'), context.description);
      }
      console.log(chalk.bold('Created:'), context.createdAt.toLocaleString());
      console.log(chalk.bold('Updated:'), context.updatedAt.toLocaleString());
      if (context.database) {
        console.log(chalk.bold('Database:'), context.database);
      }
      console.log(chalk.bold('Query History:'), (context.queryHistory?.length || 0), 'entries');
      console.log(chalk.bold('Aliases:'), Object.keys(context.aliases || {}).length);
      console.log(chalk.bold('Configuration:'), Object.keys(context.configuration || {}).length, 'settings');
      console.log(chalk.bold('Variables:'), Object.keys(context.variables || {}).length);
      console.log('');
    } catch (error) {
      logger.error('Context show failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

contextCmd
  .command('diff <context1> <context2>')
  .description('Compare two contexts')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell context diff production staging
  ${chalk.dim('$')} ai-shell context diff v1 v2
`)
  .action(async (context1: string, context2: string) => {
    try {
      await contextManager.initialize();
      const diff = await contextManager.diffContexts(context1, context2);
      console.log(chalk.cyan.bold('\n🔍 Context Comparison\n'));
      console.log(chalk.bold(`${context1} vs ${context2}\n`));

      if (diff.differences.database) {
        console.log(chalk.yellow('Database:'));
        console.log(`  ${context1}: ${diff.differences.database.context1}`);
        console.log(`  ${context2}: ${diff.differences.database.context2}\n`);
      }

      if (diff.differences.aliases) {
        const { added, removed, modified } = diff.differences.aliases;
        if (added.length || removed.length || modified.length) {
          console.log(chalk.yellow('Aliases:'));
          if (added.length) console.log(chalk.green(`  Added: ${added.join(', ')}`));
          if (removed.length) console.log(chalk.red(`  Removed: ${removed.join(', ')}`));
          if (modified.length) {
            console.log(chalk.blue('  Modified:'));
            modified.forEach(m => console.log(`    ${m.key}: "${m.value1}" → "${m.value2}"`));
          }
          console.log('');
        }
      }

      if (diff.differences.configuration) {
        const { added, removed, modified } = diff.differences.configuration;
        if (added.length || removed.length || modified.length) {
          console.log(chalk.yellow('Configuration:'));
          if (added.length) console.log(chalk.green(`  Added: ${added.join(', ')}`));
          if (removed.length) console.log(chalk.red(`  Removed: ${removed.join(', ')}`));
          if (modified.length) console.log(chalk.blue(`  Modified: ${modified.length} settings`));
          console.log('');
        }
      }

      if (diff.differences.historyCount) {
        console.log(chalk.yellow('Query History:'));
        console.log(`  ${context1}: ${diff.differences.historyCount.context1} queries`);
        console.log(`  ${context2}: ${diff.differences.historyCount.context2} queries\n`);
      }
    } catch (error) {
      logger.error('Context diff failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

contextCmd
  .command('current')
  .description('Show current active context')
  .action(async () => {
    try {
      await contextManager.initialize();
      const context = await contextManager.getCurrentContext();
      if (!context) {
        console.log(chalk.yellow('\nNo active context\n'));
      } else {
        console.log(chalk.cyan.bold('\n📌 Current Context\n'));
        console.log(chalk.bold('Name:'), context.name);
        if (context.description) {
          console.log(chalk.bold('Description:'), context.description);
        }
        if (context.database) {
          console.log(chalk.bold('Database:'), context.database);
        }
        console.log('');
      }
    } catch (error) {
      logger.error('Get current context failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

// ============================================================================
// SESSION MANAGEMENT COMMANDS
// ============================================================================

const sessionCmd = program
  .command('session')
  .description('Manage query sessions');

sessionCmd
  .command('start <name>')
  .description('Start a new session')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell session start debug-session
  ${chalk.dim('$')} ai-shell session start production-analysis
`)
  .action(async (name: string) => {
    try {
      await contextManager.initialize();
      const sessionId = await contextManager.startSession(name);
      console.log(chalk.green(`\n✅ Session "${name}" started`));
      console.log(chalk.dim(`Session ID: ${sessionId}\n`));
    } catch (error) {
      logger.error('Session start failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

sessionCmd
  .command('end')
  .description('End current session')
  .action(async () => {
    try {
      await contextManager.initialize();
      await contextManager.endSession();
      console.log(chalk.green('\n✅ Session ended successfully\n'));
    } catch (error) {
      logger.error('Session end failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

sessionCmd
  .command('list')
  .description('List all sessions')
  .option('-f, --format <type>', 'Output format (table, json)', 'table')
  .action(async (options) => {
    try {
      await contextManager.initialize();
      const sessions = await contextManager.listSessions();

      if (options.format === 'json') {
        console.log(JSON.stringify(sessions, null, 2));
      } else {
        console.log(chalk.cyan.bold('\n📋 Sessions\n'));
        if (sessions.length === 0) {
          console.log(chalk.yellow('No sessions found\n'));
        } else {
          sessions.forEach(session => {
            console.log(chalk.bold(session.name), chalk.dim(`(${session.id})`));
            console.log(chalk.dim(`  Started: ${session.startTime.toLocaleString()}`));
            if (session.endTime) {
              console.log(chalk.dim(`  Ended: ${session.endTime.toLocaleString()}`));
            } else {
              console.log(chalk.green('  Status: Active'));
            }
            if (session.statistics) {
              console.log(chalk.dim(`  Queries: ${session.statistics.queriesExecuted}`));
              console.log(chalk.dim(`  Success Rate: ${session.statistics.successRate.toFixed(1)}%`));
            }
            console.log('');
          });
        }
      }
    } catch (error) {
      logger.error('Session list failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

sessionCmd
  .command('restore <name>')
  .description('Restore a previous session')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell session restore debug-session
  ${chalk.dim('$')} ai-shell session restore session_1234567890_abc
`)
  .action(async (name: string) => {
    try {
      await contextManager.initialize();
      await contextManager.restoreSession(name);
      console.log(chalk.green(`\n✅ Session "${name}" restored\n`));
    } catch (error) {
      logger.error('Session restore failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

sessionCmd
  .command('export <name> <file>')
  .description('Export session to file')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell session export my-session session.json
`)
  .action(async (name: string, file: string) => {
    try {
      await contextManager.initialize();
      await contextManager.exportSession(name, file);
      console.log(chalk.green(`\n✅ Session exported to "${file}"\n`));
    } catch (error) {
      logger.error('Session export failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

// ============================================================================
// ERROR HANDLING & CLEANUP
// ============================================================================

// Global error handler
process.on('uncaughtException', (error) => {
  logger.error('Uncaught exception', error);
  console.error(chalk.red('Fatal error:'), error.message);
  process.exit(1);
});

process.on('unhandledRejection', (reason) => {
  logger.error('Unhandled rejection', reason instanceof Error ? reason : new Error(String(reason)));
  console.error(chalk.red('Unhandled promise rejection:'), reason);
  process.exit(1);
});

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log(chalk.yellow('\n\n⏹️  Shutting down gracefully...'));
  try {
    if (features) {
      await features.cleanup();
    }
    if (cliWrapper) {
      await cliWrapper.cleanup();
    }
    if (ssoCli) {
      await ssoCli.cleanup();
    }
    console.log(chalk.green('✅ Cleanup complete'));
    process.exit(0);
  } catch (error) {
    console.error(chalk.red('Cleanup failed:'), error);
    process.exit(1);
  }
});

process.on('SIGTERM', async () => {
  console.log(chalk.yellow('\n⏹️  Received SIGTERM, shutting down...'));
  try {
    if (features) {
      await features.cleanup();
    }
    if (cliWrapper) {
      await cliWrapper.cleanup();
    }
    if (ssoCli) {
      await ssoCli.cleanup();
    }
    process.exit(0);
  } catch (error) {
    console.error(chalk.red('Cleanup failed:'), error);
    process.exit(1);
  }
});

// ============================================================================
// REGISTER ADDITIONAL COMMANDS
// ============================================================================

// Register backup CLI commands
setupBackupCommands(program);

// Register optimization commands (if available)
if (typeof registerOptimizationCommands === 'function') {
  registerOptimizationCommands(program, getOptimizationCLI());
}

// ============================================================================
// SSO COMMANDS
// ============================================================================

const ssoCommand = program
  .command('sso')
  .description('Single Sign-On (SSO) management');

ssoCommand
  .command('configure <provider>')
  .description('Configure SSO provider')
  .option('--template <type>', 'Use provider template (okta, auth0, azure-ad, google, generic)')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell sso configure okta-prod --template okta
  ${chalk.dim('$')} ai-shell sso configure auth0-prod --template auth0
  ${chalk.dim('$')} ai-shell sso configure custom-provider
`)
  .action(async (provider: string, options: { template?: string }) => {
    try {
      const cli = getSSOCLI();
      await cli.initialize();
      await cli.configure(provider, options.template);
    } catch (error) {
      logger.error('SSO configure failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

ssoCommand
  .command('login [provider]')
  .description('Authenticate with SSO provider')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell sso login
  ${chalk.dim('$')} ai-shell sso login okta-prod
`)
  .action(async (provider?: string) => {
    try {
      const cli = getSSOCLI();
      await cli.initialize();
      await cli.login(provider);
    } catch (error) {
      logger.error('SSO login failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

ssoCommand
  .command('logout')
  .description('End SSO session')
  .addHelpText('after', `
${chalk.bold('Example:')}
  ${chalk.dim('$')} ai-shell sso logout
`)
  .action(async () => {
    try {
      const cli = getSSOCLI();
      await cli.initialize();
      await cli.logout();
      await cli.cleanup();
    } catch (error) {
      logger.error('SSO logout failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

ssoCommand
  .command('status')
  .description('Show current SSO status')
  .addHelpText('after', `
${chalk.bold('Example:')}
  ${chalk.dim('$')} ai-shell sso status
`)
  .action(async () => {
    try {
      const cli = getSSOCLI();
      await cli.initialize();
      await cli.status();
    } catch (error) {
      logger.error('SSO status failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

ssoCommand
  .command('refresh-token [session-id]')
  .description('Refresh access token')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell sso refresh-token
  ${chalk.dim('$')} ai-shell sso refresh-token abc123xyz789
`)
  .action(async (sessionId?: string) => {
    try {
      const cli = getSSOCLI();
      await cli.initialize();
      await cli.refreshToken(sessionId);
    } catch (error) {
      logger.error('SSO refresh-token failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

ssoCommand
  .command('map-roles')
  .description('Configure role mappings')
  .addHelpText('after', `
${chalk.bold('Example:')}
  ${chalk.dim('$')} ai-shell sso map-roles
`)
  .action(async () => {
    try {
      const cli = getSSOCLI();
      await cli.initialize();
      await cli.mapRoles();
    } catch (error) {
      logger.error('SSO map-roles failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

ssoCommand
  .command('list-providers')
  .description('List all configured SSO providers')
  .alias('providers')
  .addHelpText('after', `
${chalk.bold('Example:')}
  ${chalk.dim('$')} ai-shell sso list-providers
  ${chalk.dim('$')} ai-shell sso providers
`)
  .action(async () => {
    try {
      const cli = getSSOCLI();
      await cli.initialize();
      await cli.listProviders();
    } catch (error) {
      logger.error('SSO list-providers failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

ssoCommand
  .command('show-config <provider>')
  .description('Show provider configuration')
  .addHelpText('after', `
${chalk.bold('Example:')}
  ${chalk.dim('$')} ai-shell sso show-config okta-prod
`)
  .action(async (provider: string) => {
    try {
      const cli = getSSOCLI();
      await cli.initialize();
      await cli.showProviderConfig(provider);
    } catch (error) {
      logger.error('SSO show-config failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

ssoCommand
  .command('remove-provider <provider>')
  .description('Remove SSO provider')
  .addHelpText('after', `
${chalk.bold('Example:')}
  ${chalk.dim('$')} ai-shell sso remove-provider okta-old
`)
  .action(async (provider: string) => {
    try {
      const cli = getSSOCLI();
      await cli.initialize();
      await cli.removeProvider(provider);
    } catch (error) {
      logger.error('SSO remove-provider failed', error);
      console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
      process.exit(1);
    }
  });

// ============================================================================
// MAIN EXECUTION
// ============================================================================

async function main() {
  try {
    await program.parseAsync(process.argv);
  } catch (error) {
    logger.error('CLI execution failed', error);
    console.error(chalk.red('Error:'), error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

// Execute CLI
if (require.main === module) {
  main();
}

export { program };
