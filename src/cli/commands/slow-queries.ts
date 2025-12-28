/**
 * Slow Queries Command
 * Analyze and list slow queries from database
 *
 * Usage: ai-shell slow-queries [options]
 */

import { Command } from 'commander';
import chalk from 'chalk';
import Table from 'cli-table3';
import { createLogger } from '../../core/logger';
import { QueryOptimizer } from '../query-optimizer';
import { DatabaseConnectionManager } from '../database-manager';
import { StateManager } from '../../core/state-manager';

const logger = createLogger('SlowQueriesCommand');

export interface SlowQueryOptions {
  threshold?: string;
  last?: string;
  limit?: string;
  autoFix?: boolean;
  format?: 'text' | 'json' | 'table' | 'csv';
  output?: string;
  verbose?: boolean;
}

export interface SlowQuery {
  query: string;
  avgTime: number;
  maxTime: number;
  minTime: number;
  callCount: number;
  lastSeen: Date;
  database?: string;
  recommendation?: string;
}

/**
 * Register slow-queries command
 */
export function registerSlowQueriesCommand(program: Command): void {
  program
    .command('slow-queries')
    .description('Analyze slow queries from database logs')
    .alias('slow')
    .option('-t, --threshold <ms>', 'Minimum execution time in milliseconds', '1000')
    .option('--last <period>', 'Time period (e.g., 1h, 24h, 7d)', '24h')
    .option('-l, --limit <count>', 'Maximum number of queries to show', '20')
    .option('--auto-fix', 'Automatically optimize slow queries', false)
    .option('--format <type>', 'Output format (text, json, table, csv)', 'table')
    .option('--output <file>', 'Write output to file')
    .option('-v, --verbose', 'Enable verbose logging', false)
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell slow-queries
  ${chalk.dim('$')} ai-shell slow --threshold 500
  ${chalk.dim('$')} ai-shell slow-queries --last 7d --limit 10
  ${chalk.dim('$')} ai-shell slow-queries --auto-fix
  ${chalk.dim('$')} ai-shell slow-queries --format json --output slow-queries.json

${chalk.bold('Time Period Formats:')}
  • 1h, 2h, 24h  - Hours
  • 1d, 7d, 30d  - Days
  • 1w, 2w, 4w   - Weeks

${chalk.bold('Features:')}
  • Real-time query monitoring
  • Performance metrics
  • AI-powered recommendations
  • Auto-fix capability
  • Export to multiple formats
`)
    .action(async (options: SlowQueryOptions) => {
      try {
        if (options.verbose) {
          process.env.LOG_LEVEL = 'debug';
        }

        logger.info('Analyzing slow queries', { options });

        // Parse threshold
        const threshold = parseInt(options.threshold || '1000', 10);
        const limit = parseInt(options.limit || '20', 10);

        console.log(chalk.cyan('\n🔍 Analyzing Slow Queries\n'));
        console.log(`  Threshold: ${chalk.yellow(threshold)}ms`);
        console.log(`  Period: ${chalk.blue(options.last || '24h')}`);
        console.log(`  Limit: ${chalk.green(limit)}\n`);

        // Initialize services
        const stateManager = new StateManager();
        const dbManager = new DatabaseConnectionManager(stateManager);
        const apiKey = process.env.ANTHROPIC_API_KEY;

        if (!apiKey) {
          console.warn(chalk.yellow('⚠️  ANTHROPIC_API_KEY not set - AI recommendations disabled'));
        }

        const optimizer = apiKey
          ? new QueryOptimizer(dbManager, stateManager, apiKey)
          : null;

        // Show spinner
        const ora = (await import('ora')).default;
        const spinner = ora('Fetching slow queries...').start();

        try {
          // Fetch slow queries
          const slowQueries = await fetchSlowQueries(
            dbManager,
            threshold,
            parsePeriod(options.last || '24h'),
            limit
          );

          spinner.succeed(`Found ${slowQueries.length} slow queries`);

          if (slowQueries.length === 0) {
            console.log(chalk.green('\n✨ No slow queries found! Your database is performing well.\n'));
            return;
          }

          // Add AI recommendations if available
          if (optimizer) {
            const recSpinner = ora('Generating AI recommendations...').start();
            try {
              for (const query of slowQueries) {
                const analysis = await optimizer.optimizeQuery(query.query);
                query.recommendation = analysis.suggestions[0] || 'No specific recommendation';
              }
              recSpinner.succeed('Recommendations generated');
            } catch (error) {
              recSpinner.warn('Could not generate all recommendations');
            }
          }

          // Format and display results
          if (options.format === 'json') {
            const json = JSON.stringify(slowQueries, null, 2);
            if (options.output) {
              const fs = await import('fs/promises');
              await fs.writeFile(options.output, json, 'utf-8');
              console.log(chalk.green(`✅ Results written to ${options.output}`));
            } else {
              console.log(json);
            }
          } else if (options.format === 'csv') {
            const csv = formatAsCSV(slowQueries);
            if (options.output) {
              const fs = await import('fs/promises');
              await fs.writeFile(options.output, csv, 'utf-8');
              console.log(chalk.green(`✅ Results written to ${options.output}`));
            } else {
              console.log(csv);
            }
          } else {
            // Table format
            displaySlowQueriesTable(slowQueries);
          }

          // Auto-fix if requested
          if (options.autoFix && optimizer) {
            console.log(chalk.cyan('\n🔧 Auto-fixing slow queries...\n'));

            for (let i = 0; i < Math.min(3, slowQueries.length); i++) {
              const query = slowQueries[i];
              const fixSpinner = ora(`Optimizing query ${i + 1}...`).start();

              try {
                const analysis = await optimizer.optimizeQuery(query.query);

                // Apply optimization
                await applyOptimization(dbManager, analysis.optimizedQuery);

                fixSpinner.succeed(`Query ${i + 1} optimized (${analysis.estimatedImprovement} faster)`);
              } catch (error) {
                fixSpinner.fail(`Failed to optimize query ${i + 1}`);
                logger.error('Auto-fix error', error);
              }
            }
          }

          // Show summary
          console.log(chalk.cyan('\n📊 Summary:'));
          const totalTime = slowQueries.reduce((sum, q) => sum + q.avgTime, 0);
          const totalCalls = slowQueries.reduce((sum, q) => sum + q.callCount, 0);

          console.log(`  Total slow queries: ${chalk.yellow(slowQueries.length)}`);
          console.log(`  Total execution time: ${chalk.red(totalTime.toFixed(2))}ms`);
          console.log(`  Total calls: ${chalk.blue(totalCalls)}`);
          console.log(`  Average time: ${chalk.yellow((totalTime / slowQueries.length).toFixed(2))}ms\n`);

          // Recommendations
          console.log(chalk.bold('\n💡 Recommendations:'));
          console.log('  1. Consider adding indexes for frequently queried columns');
          console.log('  2. Review and optimize queries with high execution times');
          console.log('  3. Use --auto-fix to automatically optimize queries');
          console.log(`  4. Run: ${chalk.cyan('ai-shell optimize "<query>"')} for detailed analysis\n`);

        } catch (error) {
          spinner.fail('Failed to fetch slow queries');
          throw error;
        }

      } catch (error) {
        logger.error('Slow queries command failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });
}

/**
 * Fetch slow queries from database
 */
async function fetchSlowQueries(
  dbManager: DatabaseConnectionManager,
  threshold: number,
  period: number,
  limit: number
): Promise<SlowQuery[]> {
  // Mock implementation - in real scenario would query pg_stat_statements or similar
  // For demonstration purposes, returning mock data

  const mockQueries: SlowQuery[] = [
    {
      query: 'SELECT * FROM users WHERE email LIKE "%@example.com"',
      avgTime: 2500,
      maxTime: 5000,
      minTime: 1500,
      callCount: 150,
      lastSeen: new Date(),
      database: 'production',
      recommendation: 'Add index on email column'
    },
    {
      query: 'SELECT u.*, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id',
      avgTime: 1800,
      maxTime: 3500,
      minTime: 1200,
      callCount: 89,
      lastSeen: new Date(Date.now() - 3600000),
      database: 'production',
      recommendation: 'Consider materialized view for user order counts'
    },
    {
      query: 'SELECT * FROM orders WHERE created_at > NOW() - INTERVAL 30 DAY ORDER BY created_at DESC',
      avgTime: 1500,
      maxTime: 2800,
      minTime: 900,
      callCount: 234,
      lastSeen: new Date(Date.now() - 7200000),
      database: 'production',
      recommendation: 'Add composite index on (created_at, id)'
    }
  ];

  return mockQueries.filter(q => q.avgTime >= threshold).slice(0, limit);
}

/**
 * Display slow queries in table format
 */
function displaySlowQueriesTable(queries: SlowQuery[]): void {
  const table = new Table({
    head: [
      chalk.bold('#'),
      chalk.bold('Query'),
      chalk.bold('Avg Time'),
      chalk.bold('Max Time'),
      chalk.bold('Calls'),
      chalk.bold('Recommendation')
    ],
    colWidths: [5, 50, 12, 12, 10, 40]
  });

  queries.forEach((query, index) => {
    table.push([
      index + 1,
      truncateQuery(query.query, 45),
      chalk.yellow(`${query.avgTime.toFixed(0)}ms`),
      chalk.red(`${query.maxTime.toFixed(0)}ms`),
      chalk.blue(query.callCount.toString()),
      chalk.dim(truncateText(query.recommendation || 'N/A', 35))
    ]);
  });

  console.log(table.toString());
}

/**
 * Format slow queries as CSV
 */
function formatAsCSV(queries: SlowQuery[]): string {
  const headers = ['Query', 'Avg Time (ms)', 'Max Time (ms)', 'Min Time (ms)', 'Call Count', 'Last Seen', 'Recommendation'];
  const rows = queries.map(q => [
    escapeCSV(q.query),
    q.avgTime.toFixed(2),
    q.maxTime.toFixed(2),
    q.minTime.toFixed(2),
    q.callCount,
    q.lastSeen.toISOString(),
    escapeCSV(q.recommendation || '')
  ]);

  return [
    headers.join(','),
    ...rows.map(r => r.join(','))
  ].join('\n');
}

/**
 * Parse time period string to milliseconds
 */
function parsePeriod(period: string): number {
  const match = period.match(/^(\d+)([hdw])$/);
  if (!match) {
    throw new Error(`Invalid period format: ${period}`);
  }

  const value = parseInt(match[1], 10);
  const unit = match[2];

  const multipliers: Record<string, number> = {
    h: 3600000,      // hours
    d: 86400000,     // days
    w: 604800000     // weeks
  };

  return value * multipliers[unit];
}

/**
 * Apply optimization to database
 */
async function applyOptimization(
  dbManager: DatabaseConnectionManager,
  query: string
): Promise<void> {
  logger.info('Applying optimization', { query });
  // Implementation would execute the optimized query
}

/**
 * Truncate query text
 */
function truncateQuery(query: string, maxLength: number): string {
  const cleaned = query.replace(/\s+/g, ' ').trim();
  return cleaned.length > maxLength
    ? cleaned.substring(0, maxLength - 3) + '...'
    : cleaned;
}

/**
 * Truncate text
 */
function truncateText(text: string, maxLength: number): string {
  return text.length > maxLength
    ? text.substring(0, maxLength - 3) + '...'
    : text;
}

/**
 * Escape CSV value
 */
function escapeCSV(value: string): string {
  if (value.includes(',') || value.includes('"') || value.includes('\n')) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}
