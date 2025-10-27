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
import { createLogger } from '../core/logger';

const logger = createLogger('CLI');
const program = new Command();

// Lazy-load features to avoid initialization at module load time
let features: FeatureCommands | null = null;
function getFeatures(): FeatureCommands {
  if (!features) {
    features = new FeatureCommands();
  }
  return features;
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
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell optimize "SELECT * FROM users WHERE id > 100"
  ${chalk.dim('$')} ai-shell opt "SELECT u.*, o.* FROM users u JOIN orders o ON u.id = o.user_id"
`)
  .action(async (query: string) => {
    try {
      await getFeatures().optimizeQuery(query);
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

const phase2 = program
  .command('phase2')
  .description(chalk.cyan('Phase 2 Commands - Advanced Features'));

phase2
  .command('info')
  .description('Show Phase 2 features')
  .action(() => {
    console.log(chalk.cyan.bold('\n📋 Phase 2 Features:\n'));
    console.log('  4. Query Federation - Cross-database queries');
    console.log('  5. Schema Designer - AI-powered schema design');
    console.log('  6. Query Cache - Redis-based caching\n');
  });

// Query Federation Commands
program
  .command('federate <query>')
  .description('Execute query across multiple databases')
  .alias('fed')
  .option('-d, --databases <list>', 'Comma-separated list of database names')
  .requiredOption('-d, --databases <list>', 'Databases to query (required)')
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell federate "SELECT * FROM users" --databases db1,db2,db3
  ${chalk.dim('$')} ai-shell fed "SELECT u.*, o.* FROM users u JOIN orders o" -d production,analytics
`)
  .action(async (query: string, options) => {
    try {
      const databases = options.databases.split(',').map((s: string) => s.trim());
      await getFeatures().federateQuery(query, databases);
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
  .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell explain "SELECT * FROM users WHERE created_at > NOW() - INTERVAL 7 DAY"
  ${chalk.dim('$')} ai-shell exp "SELECT u.*, COUNT(o.id) FROM users u LEFT JOIN orders o GROUP BY u.id"
`)
  .action(async (query: string) => {
    try {
      await getFeatures().explainSQL(query);
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
    await getFeatures().cleanup();
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
    await getFeatures().cleanup();
    process.exit(0);
  } catch (error) {
    console.error(chalk.red('Cleanup failed:'), error);
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
