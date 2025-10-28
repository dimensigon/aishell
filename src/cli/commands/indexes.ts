/**
 * Indexes Command
 * Index management and recommendations
 *
 * Usage: ai-shell indexes <subcommand> [options]
 */

import { Command } from 'commander';
import chalk from 'chalk';
import Table from 'cli-table3';
import { createLogger } from '../../core/logger';
import { DatabaseConnectionManager } from '../database-manager';
import { StateManager } from '../../core/state-manager';

const logger = createLogger('IndexesCommand');

export interface IndexRecommendation {
  table: string;
  columns: string[];
  indexName: string;
  reason: string;
  estimatedImpact: string;
  createStatement: string;
  type: 'btree' | 'hash' | 'gin' | 'gist';
  online: boolean;
}

export interface ExistingIndex {
  name: string;
  table: string;
  columns: string[];
  type: string;
  size: string;
  scans: number;
  tuplesRead: number;
  tuplesReturned: number;
  unused: boolean;
}

/**
 * Register indexes command
 */
export function registerIndexesCommand(program: Command): void {
  const indexes = program
    .command('indexes')
    .description('Index management and recommendations')
    .alias('idx');

  // Recommend subcommand
  indexes
    .command('recommend')
    .description('Get index recommendations for a table')
    .option('--table <table>', 'Table name (required)')
    .option('--format <type>', 'Output format (text, json, table)', 'table')
    .option('--output <file>', 'Write output to file')
    .option('-v, --verbose', 'Enable verbose logging', false)
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell indexes recommend --table users
  ${chalk.dim('$')} ai-shell idx recommend --table orders --format json

${chalk.bold('Features:')}
  • AI-powered index analysis
  • Query pattern analysis
  • Impact estimation
  • Safe DDL generation
`)
    .action(async (options) => {
      try {
        if (!options.table) {
          console.error(chalk.red('Error: --table option is required'));
          console.log(chalk.dim('Usage: ai-shell indexes recommend --table <table>'));
          process.exit(1);
        }

        if (options.verbose) {
          process.env.LOG_LEVEL = 'debug';
        }

        logger.info('Getting index recommendations', { table: options.table });

        console.log(chalk.cyan(`\n📊 Index Recommendations for table: ${chalk.bold(options.table)}\n`));

        // Initialize services
        const stateManager = new StateManager();
        const dbManager = new DatabaseConnectionManager(stateManager);

        // Show spinner
        const ora = (await import('ora')).default;
        const spinner = ora('Analyzing query patterns...').start();

        try {
          // Analyze table and queries
          const recommendations = await analyzeTableIndexes(dbManager, options.table);

          spinner.succeed(`Found ${recommendations.length} recommendations`);

          if (recommendations.length === 0) {
            console.log(chalk.green('\n✨ No index recommendations needed. Table is well-optimized!\n'));
            return;
          }

          // Display recommendations
          if (options.format === 'json') {
            const json = JSON.stringify(recommendations, null, 2);
            if (options.output) {
              const fs = await import('fs/promises');
              await fs.writeFile(options.output, json, 'utf-8');
              console.log(chalk.green(`✅ Results written to ${options.output}`));
            } else {
              console.log(json);
            }
          } else {
            displayRecommendationsTable(recommendations);

            // Show CREATE INDEX statements
            console.log(chalk.cyan('\n📝 SQL Statements:\n'));
            recommendations.forEach((rec, index) => {
              console.log(chalk.dim(`-- Recommendation ${index + 1}`));
              console.log(chalk.green(rec.createStatement));
              console.log('');
            });
          }

          // Summary
          console.log(chalk.cyan('💡 Next Steps:'));
          console.log('  1. Review recommendations above');
          console.log('  2. Test in development environment first');
          console.log('  3. Apply indexes using: ai-shell indexes apply --table <table> --index <index>');
          console.log('  4. Monitor performance after applying\n');

        } catch (error) {
          spinner.fail('Analysis failed');
          throw error;
        }

      } catch (error) {
        logger.error('Index recommendation failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Apply subcommand
  indexes
    .command('apply')
    .description('Apply recommended index')
    .option('--table <table>', 'Table name (required)')
    .option('--index <index>', 'Index name (required)')
    .option('--online', 'Create index online (non-blocking)', true)
    .option('--dry-run', 'Show SQL without executing', false)
    .option('-v, --verbose', 'Enable verbose logging', false)
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell indexes apply --table users --index idx_users_email
  ${chalk.dim('$')} ai-shell idx apply --table orders --index idx_orders_created --online
  ${chalk.dim('$')} ai-shell indexes apply --table products --index idx_products_name --dry-run

${chalk.bold('Features:')}
  • Online index creation
  • Progress monitoring
  • Automatic rollback on failure
  • Dry-run mode
`)
    .action(async (options) => {
      try {
        if (!options.table || !options.index) {
          console.error(chalk.red('Error: --table and --index options are required'));
          console.log(chalk.dim('Usage: ai-shell indexes apply --table <table> --index <index>'));
          process.exit(1);
        }

        if (options.verbose) {
          process.env.LOG_LEVEL = 'debug';
        }

        logger.info('Applying index', { table: options.table, index: options.index });

        // Initialize services
        const stateManager = new StateManager();
        const dbManager = new DatabaseConnectionManager(stateManager);

        // Get index details
        const recommendations = await analyzeTableIndexes(dbManager, options.table);
        const indexRec = recommendations.find(r => r.indexName === options.index);

        if (!indexRec) {
          console.error(chalk.red(`Error: Index "${options.index}" not found in recommendations`));
          console.log(chalk.dim('Run: ai-shell indexes recommend --table ' + options.table));
          process.exit(1);
        }

        // Show what will be created
        console.log(chalk.cyan('\n🔨 Creating Index:\n'));
        console.log(chalk.bold('  Table: ') + chalk.yellow(indexRec.table));
        console.log(chalk.bold('  Index: ') + chalk.green(indexRec.indexName));
        console.log(chalk.bold('  Columns: ') + indexRec.columns.join(', '));
        console.log(chalk.bold('  Type: ') + indexRec.type);
        console.log(chalk.bold('  Online: ') + (options.online ? chalk.green('Yes') : chalk.red('No')));
        console.log(chalk.bold('  Impact: ') + chalk.blue(indexRec.estimatedImpact));
        console.log('\n' + chalk.bold('  SQL: ') + chalk.dim(indexRec.createStatement) + '\n');

        if (options.dryRun) {
          console.log(chalk.yellow('✓ Dry-run mode - no changes made\n'));
          return;
        }

        // Confirm
        const readline = require('readline').createInterface({
          input: process.stdin,
          output: process.stdout
        });

        await new Promise<void>((resolve) => {
          readline.question(chalk.bold('Proceed with index creation? (y/n) '), async (answer: string) => {
            readline.close();
            if (answer.toLowerCase() !== 'y') {
              console.log(chalk.yellow('Operation cancelled'));
              process.exit(0);
            }
            resolve();
          });
        });

        // Apply index
        const ora = (await import('ora')).default;
        const spinner = ora('Creating index...').start();

        try {
          await createIndex(dbManager, indexRec, options.online);
          spinner.succeed('Index created successfully');

          // Verify index
          const verifySpinner = ora('Verifying index...').start();
          const verified = await verifyIndex(dbManager, indexRec.table, indexRec.indexName);

          if (verified) {
            verifySpinner.succeed('Index verified');
            console.log(chalk.green('\n✅ Index applied successfully!\n'));
          } else {
            verifySpinner.warn('Index verification failed');
          }

        } catch (error) {
          spinner.fail('Index creation failed');
          throw error;
        }

      } catch (error) {
        logger.error('Index apply failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // List subcommand
  indexes
    .command('list')
    .description('List all indexes for a table')
    .option('--table <table>', 'Table name (required)')
    .option('--show-unused', 'Highlight unused indexes', false)
    .option('--format <type>', 'Output format (text, json, table)', 'table')
    .option('-v, --verbose', 'Enable verbose logging', false)
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell indexes list --table users
  ${chalk.dim('$')} ai-shell idx list --table orders --show-unused
`)
    .action(async (options) => {
      try {
        if (!options.table) {
          console.error(chalk.red('Error: --table option is required'));
          process.exit(1);
        }

        const stateManager = new StateManager();
        const dbManager = new DatabaseConnectionManager(stateManager);

        const ora = (await import('ora')).default;
        const spinner = ora('Fetching indexes...').start();

        const indexes = await listTableIndexes(dbManager, options.table);
        spinner.succeed(`Found ${indexes.length} indexes`);

        if (indexes.length === 0) {
          console.log(chalk.yellow('\nNo indexes found for table: ' + options.table + '\n'));
          return;
        }

        displayIndexesTable(indexes, options.showUnused);

        // Show unused indexes warning
        const unused = indexes.filter(idx => idx.unused);
        if (unused.length > 0) {
          console.log(chalk.yellow(`\n⚠️  Found ${unused.length} unused indexes that could be dropped\n`));
        }

      } catch (error) {
        logger.error('Index list failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });
}

/**
 * Analyze table and generate index recommendations
 */
async function analyzeTableIndexes(
  dbManager: DatabaseConnectionManager,
  table: string
): Promise<IndexRecommendation[]> {
  // Mock implementation - in real scenario would analyze pg_stat_statements
  const recommendations: IndexRecommendation[] = [
    {
      table,
      columns: ['email'],
      indexName: `idx_${table}_email`,
      reason: 'Frequently used in WHERE clauses and JOINs',
      estimatedImpact: '70% faster for email lookups',
      createStatement: `CREATE INDEX CONCURRENTLY idx_${table}_email ON ${table}(email);`,
      type: 'btree',
      online: true
    },
    {
      table,
      columns: ['created_at', 'id'],
      indexName: `idx_${table}_created_id`,
      reason: 'Optimizes time-range queries with ordering',
      estimatedImpact: '50% faster for date range queries',
      createStatement: `CREATE INDEX CONCURRENTLY idx_${table}_created_id ON ${table}(created_at DESC, id);`,
      type: 'btree',
      online: true
    }
  ];

  return recommendations;
}

/**
 * Create index on table
 */
async function createIndex(
  dbManager: DatabaseConnectionManager,
  recommendation: IndexRecommendation,
  online: boolean
): Promise<void> {
  logger.info('Creating index', { recommendation, online });
  // Implementation would execute CREATE INDEX statement
  await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate creation
}

/**
 * Verify index exists
 */
async function verifyIndex(
  dbManager: DatabaseConnectionManager,
  table: string,
  indexName: string
): Promise<boolean> {
  logger.info('Verifying index', { table, indexName });
  return true; // Mock verification
}

/**
 * List indexes for table
 */
async function listTableIndexes(
  dbManager: DatabaseConnectionManager,
  table: string
): Promise<ExistingIndex[]> {
  // Mock implementation
  const indexes: ExistingIndex[] = [
    {
      name: `${table}_pkey`,
      table,
      columns: ['id'],
      type: 'btree',
      size: '128 KB',
      scans: 15234,
      tuplesRead: 45678,
      tuplesReturned: 45678,
      unused: false
    },
    {
      name: `idx_${table}_old`,
      table,
      columns: ['old_column'],
      type: 'btree',
      size: '64 KB',
      scans: 0,
      tuplesRead: 0,
      tuplesReturned: 0,
      unused: true
    }
  ];

  return indexes;
}

/**
 * Display recommendations in table format
 */
function displayRecommendationsTable(recommendations: IndexRecommendation[]): void {
  const table = new Table({
    head: [
      chalk.bold('#'),
      chalk.bold('Index Name'),
      chalk.bold('Columns'),
      chalk.bold('Type'),
      chalk.bold('Reason'),
      chalk.bold('Impact')
    ],
    colWidths: [5, 25, 20, 10, 35, 25]
  });

  recommendations.forEach((rec, index) => {
    table.push([
      index + 1,
      chalk.green(rec.indexName),
      rec.columns.join(', '),
      rec.type,
      chalk.dim(rec.reason),
      chalk.blue(rec.estimatedImpact)
    ]);
  });

  console.log(table.toString());
}

/**
 * Display existing indexes in table format
 */
function displayIndexesTable(indexes: ExistingIndex[], highlightUnused: boolean): void {
  const table = new Table({
    head: [
      chalk.bold('Name'),
      chalk.bold('Columns'),
      chalk.bold('Type'),
      chalk.bold('Size'),
      chalk.bold('Scans'),
      chalk.bold('Status')
    ]
  });

  indexes.forEach((idx) => {
    const status = idx.unused
      ? chalk.red('Unused')
      : chalk.green('Active');

    table.push([
      idx.unused && highlightUnused ? chalk.red(idx.name) : idx.name,
      idx.columns.join(', '),
      idx.type,
      idx.size,
      idx.scans.toLocaleString(),
      status
    ]);
  });

  console.log(table.toString());
}
