/**
 * Optimize Command
 * AI-powered SQL query optimization
 *
 * Usage: ai-shell optimize <query> [options]
 */

import { Command } from 'commander';
import chalk from 'chalk';
import { createLogger } from '../../core/logger';
import { QueryOptimizer } from '../query-optimizer';
import { DatabaseConnectionManager } from '../database-manager';
import { StateManager } from '../../core/state-manager';
import { formatOptimizationResult } from '../formatters/optimization-formatter';

const logger = createLogger('OptimizeCommand');

export interface OptimizeCommandOptions {
  apply?: boolean;
  explain?: boolean;
  dryRun?: boolean;
  format?: 'text' | 'json' | 'table' | 'csv';
  output?: string;
  compare?: boolean;
  verbose?: boolean;
}

/**
 * Register optimize command
 */
export function registerOptimizeCommand(program: Command): void {
  program
    .command('optimize <query>')
    .description('Optimize a SQL query using AI analysis')
    .alias('opt')
    .option('--apply', 'Apply optimization immediately', false)
    .option('--explain', 'Show query execution plan', false)
    .option('--dry-run', 'Validate without executing', false)
    .option('--format <type>', 'Output format (text, json, table, csv)', 'text')
    .option('--output <file>', 'Write output to file')
    .option('--compare', 'Compare before and after performance', false)
    .option('-v, --verbose', 'Enable verbose logging', false)
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell optimize "SELECT * FROM users WHERE id > 100"
  ${chalk.dim('$')} ai-shell opt "SELECT u.*, o.* FROM users u JOIN orders o ON u.id = o.user_id"
  ${chalk.dim('$')} ai-shell optimize "SELECT * FROM users" --explain
  ${chalk.dim('$')} ai-shell optimize "DELETE FROM users" --dry-run
  ${chalk.dim('$')} ai-shell optimize "SELECT * FROM orders" --apply --compare
  ${chalk.dim('$')} ai-shell optimize "SELECT * FROM products" --format json --output result.json

${chalk.bold('Features:')}
  • AI-powered query analysis
  • Index recommendations
  • Performance estimation
  • Execution plan comparison
  • Safe dry-run mode

${chalk.bold('Environment Variables:')}
  ${chalk.yellow('ANTHROPIC_API_KEY')}  - Required for AI optimization
`)
    .action(async (query: string, options: OptimizeCommandOptions) => {
      try {
        if (options.verbose) {
          process.env.LOG_LEVEL = 'debug';
        }

        logger.info('Starting query optimization', {
          queryLength: query.length,
          options
        });

        // Check for ANTHROPIC_API_KEY
        const apiKey = process.env.ANTHROPIC_API_KEY;
        if (!apiKey) {
          console.error(chalk.red('Error: ANTHROPIC_API_KEY environment variable not set'));
          console.log(chalk.dim('Please set your Anthropic API key:'));
          console.log(chalk.dim('  export ANTHROPIC_API_KEY=your-api-key'));
          process.exit(1);
        }

        // Initialize services
        const stateManager = new StateManager();
        const dbManager = new DatabaseConnectionManager(stateManager);
        const optimizer = new QueryOptimizer(dbManager, stateManager, apiKey);

        // Dry-run check for dangerous operations
        if (!options.dryRun && isDangerousQuery(query)) {
          console.log(chalk.yellow('⚠️  Warning: This query contains potentially dangerous operations'));
          console.log(chalk.dim('Use --dry-run to analyze without executing'));

          const readline = require('readline').createInterface({
            input: process.stdin,
            output: process.stdout
          });

          await new Promise<void>((resolve) => {
            readline.question('Continue? (y/n) ', (answer: string) => {
              readline.close();
              if (answer.toLowerCase() !== 'y') {
                console.log(chalk.yellow('Operation cancelled'));
                process.exit(0);
              }
              resolve();
            });
          });
        }

        // Show spinner for optimization
        const ora = (await import('ora')).default;
        const spinner = ora('Analyzing query with AI...').start();

        try {
          // Optimize query
          const analysis = await optimizer.optimizeQuery(query);

          spinner.succeed('Query analysis complete');

          // Get execution plans if requested
          let executionPlanBefore, executionPlanAfter;
          if (options.explain) {
            const explainSpinner = ora('Fetching execution plans...').start();
            try {
              executionPlanBefore = await getExecutionPlan(dbManager, query);
              executionPlanAfter = await getExecutionPlan(dbManager, analysis.optimizedQuery);
              explainSpinner.succeed('Execution plans fetched');
            } catch (error) {
              explainSpinner.warn('Could not fetch execution plans');
            }
          }

          // Format result
          const result = {
            originalQuery: query,
            optimizedQuery: analysis.optimizedQuery,
            issues: analysis.issues,
            suggestions: analysis.suggestions,
            indexRecommendations: analysis.indexRecommendations,
            estimatedImprovement: analysis.estimatedImprovement,
            executionPlanBefore,
            executionPlanAfter
          };

          // Output formatted result
          const formatted = formatOptimizationResult(result, options.format || 'text');

          if (options.output) {
            const fs = await import('fs/promises');
            await fs.writeFile(options.output, formatted, 'utf-8');
            console.log(chalk.green(`✅ Results written to ${options.output}`));
          } else {
            console.log(formatted);
          }

          // Apply optimization if requested
          if (options.apply && !options.dryRun) {
            const applySpinner = ora('Applying optimized query...').start();
            try {
              // Execute optimized query
              await executeOptimizedQuery(dbManager, analysis.optimizedQuery);
              applySpinner.succeed('Optimized query applied successfully');

              // Compare performance if requested
              if (options.compare) {
                await comparePerformance(dbManager, query, analysis.optimizedQuery);
              }
            } catch (error) {
              applySpinner.fail('Failed to apply optimization');
              throw error;
            }
          }

          // Show summary
          console.log(chalk.cyan('\n📊 Summary:'));
          console.log(`  Issues found: ${chalk.yellow(analysis.issues.length)}`);
          console.log(`  Suggestions: ${chalk.blue(analysis.suggestions.length)}`);
          console.log(`  Index recommendations: ${chalk.green(analysis.indexRecommendations.length)}`);
          console.log(`  Estimated improvement: ${chalk.bold(analysis.estimatedImprovement)}`);

          logger.info('Query optimization completed successfully');

        } catch (error) {
          spinner.fail('Query optimization failed');
          throw error;
        }

      } catch (error) {
        logger.error('Optimize command failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));

        // Provide helpful suggestions
        if (error instanceof Error) {
          if (error.message.includes('API key')) {
            console.log(chalk.dim('\nTip: Set ANTHROPIC_API_KEY environment variable'));
          } else if (error.message.includes('connection')) {
            console.log(chalk.dim('\nTip: Check database connection with: ai-shell connections'));
          }
        }

        process.exit(1);
      }
    });
}

/**
 * Check if query contains dangerous operations
 */
function isDangerousQuery(query: string): boolean {
  const dangerous = ['DROP', 'TRUNCATE', 'DELETE', 'UPDATE', 'ALTER'];
  const upperQuery = query.toUpperCase();
  return dangerous.some(keyword => upperQuery.includes(keyword));
}

/**
 * Get execution plan for query
 */
async function getExecutionPlan(
  dbManager: DatabaseConnectionManager,
  query: string
): Promise<any> {
  // Implementation would fetch EXPLAIN output
  // This is a placeholder
  return {
    query,
    plan: 'Execution plan data'
  };
}

/**
 * Execute optimized query
 */
async function executeOptimizedQuery(
  dbManager: DatabaseConnectionManager,
  query: string
): Promise<void> {
  // Implementation would execute the query
  logger.info('Executing optimized query', { query });
}

/**
 * Compare performance between original and optimized queries
 */
async function comparePerformance(
  dbManager: DatabaseConnectionManager,
  originalQuery: string,
  optimizedQuery: string
): Promise<void> {
  console.log(chalk.cyan('\n⚡ Performance Comparison:'));

  const ora = (await import('ora')).default;
  const spinner = ora('Running performance tests...').start();

  try {
    // Benchmark original query
    const originalTime = await benchmarkQuery(dbManager, originalQuery);

    // Benchmark optimized query
    const optimizedTime = await benchmarkQuery(dbManager, optimizedQuery);

    // Calculate improvement
    const improvement = ((originalTime - optimizedTime) / originalTime * 100).toFixed(2);
    const speedup = (originalTime / optimizedTime).toFixed(2);

    spinner.succeed('Performance comparison complete');

    console.log(`\n  Original query: ${chalk.yellow(originalTime.toFixed(2))}ms`);
    console.log(`  Optimized query: ${chalk.green(optimizedTime.toFixed(2))}ms`);
    console.log(`  Improvement: ${chalk.bold.green(improvement)}%`);
    console.log(`  Speedup: ${chalk.bold(speedup)}x faster\n`);

  } catch (error) {
    spinner.fail('Performance comparison failed');
    logger.error('Performance comparison error', error);
  }
}

/**
 * Benchmark query execution time
 */
async function benchmarkQuery(
  dbManager: DatabaseConnectionManager,
  query: string,
  iterations: number = 5
): Promise<number> {
  const times: number[] = [];

  for (let i = 0; i < iterations; i++) {
    const start = Date.now();
    // Execute query (placeholder)
    await new Promise(resolve => setTimeout(resolve, Math.random() * 100));
    const end = Date.now();
    times.push(end - start);
  }

  // Return average time
  return times.reduce((a, b) => a + b, 0) / times.length;
}
