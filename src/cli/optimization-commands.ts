/**
 * Optimization CLI Commands Registration
 * Registers all optimization-related commands with the Commander program
 */

import { Command } from 'commander';
import chalk from 'chalk';
import { OptimizationCLI } from './optimization-cli';
import { createLogger } from '../core/logger';

const logger = createLogger('OptimizationCommands');

/**
 * Register all optimization commands
 */
export function registerOptimizationCommands(program: Command, getOptimizationCLI: () => OptimizationCLI): void {
  // Extended Optimization Commands
  program
    .command('optimize-all')
    .description('Optimize all slow queries automatically')
    .option('--threshold <ms>', 'Only optimize queries slower than threshold', '1000')
    .option('--auto-apply', 'Apply all recommendations automatically')
    .option('--report <file>', 'Save optimization report to file')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell optimize-all
  ${chalk.dim('$')} ai-shell optimize-all --threshold 500 --auto-apply
  ${chalk.dim('$')} ai-shell optimize-all --report optimization-report.json
`)
    .action(async (options) => {
      try {
        const cli = getOptimizationCLI();
        await cli.analyzeSlowQueries({
          threshold: parseInt(options.threshold),
          autoFix: options.autoApply,
          export: options.report
        });
      } catch (error) {
        logger.error('Optimization failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  program
    .command('slow-queries')
    .description('Analyze slow queries with advanced options')
    .option('-t, --threshold <ms>', 'Minimum query time (default: 1000ms)', '1000')
    .option('-l, --limit <n>', 'Show top N slowest queries', '10')
    .option('--last <period>', 'Time period (e.g., 24h, 7d, 30d)')
    .option('--auto-fix', 'Automatically optimize slow queries')
    .option('--export <file>', 'Export results to file')
    .option('-f, --format <type>', 'Output format (json, table, csv)', 'table')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell slow-queries
  ${chalk.dim('$')} ai-shell slow-queries --threshold 500 --limit 20
  ${chalk.dim('$')} ai-shell slow-queries --last 7d --auto-fix
  ${chalk.dim('$')} ai-shell slow-queries --export slow-queries.json --format json
`)
    .action(async (options) => {
      try {
        const cli = getOptimizationCLI();
        await cli.analyzeSlowQueries({
          threshold: parseInt(options.threshold),
          limit: parseInt(options.limit),
          last: options.last,
          autoFix: options.autoFix,
          export: options.export,
          format: options.format
        });
      } catch (error) {
        logger.error('Slow query analysis failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Index Management Commands
  program
    .command('indexes analyze')
    .description('Analyze indexes and provide recommendations')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell indexes analyze
`)
    .action(async () => {
      try {
        const cli = getOptimizationCLI();
        await cli.analyzeIndexes();
      } catch (error) {
        logger.error('Index analysis failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  program
    .command('indexes recommendations')
    .description('Get index recommendations')
    .option('--apply', 'Apply recommended indexes automatically')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell indexes recommendations
  ${chalk.dim('$')} ai-shell indexes recommendations --apply
`)
    .action(async (options) => {
      try {
        const cli = getOptimizationCLI();
        await cli.getIndexRecommendations(options.apply);
      } catch (error) {
        logger.error('Index recommendations failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  program
    .command('indexes create <name> <table> <columns...>')
    .description('Create a new index')
    .option('--online', 'Create index online without locking table')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell indexes create idx_users_email users email
  ${chalk.dim('$')} ai-shell indexes create idx_orders_date orders created_at --online
`)
    .action(async (name: string, table: string, columns: string[], options) => {
      try {
        const cli = getOptimizationCLI();
        await cli.createIndex(name, table, columns, options.online);
      } catch (error) {
        logger.error('Index creation failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  program
    .command('indexes drop <name>')
    .description('Drop an existing index')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell indexes drop idx_users_email
`)
    .action(async (name: string) => {
      try {
        const cli = getOptimizationCLI();
        await cli.dropIndex(name);
      } catch (error) {
        logger.error('Index drop failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  program
    .command('indexes rebuild')
    .description('Rebuild indexes')
    .option('--all', 'Rebuild all indexes')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell indexes rebuild
  ${chalk.dim('$')} ai-shell indexes rebuild --all
`)
    .action(async (options) => {
      try {
        const cli = getOptimizationCLI();
        await cli.rebuildIndexes(options.all);
      } catch (error) {
        logger.error('Index rebuild failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  program
    .command('indexes stats')
    .description('Show index statistics')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell indexes stats
`)
    .action(async () => {
      try {
        const cli = getOptimizationCLI();
        await cli.getIndexStats();
      } catch (error) {
        logger.error('Index stats failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Pattern Analysis Commands
  program
    .command('analyze patterns')
    .description('Analyze query patterns and identify issues')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell analyze patterns
`)
    .action(async () => {
      try {
        const cli = getOptimizationCLI();
        await cli.analyzePatterns();
      } catch (error) {
        logger.error('Pattern analysis failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  program
    .command('analyze workload')
    .description('Analyze database workload')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell analyze workload
`)
    .action(async () => {
      try {
        const cli = getOptimizationCLI();
        await cli.analyzeWorkload();
      } catch (error) {
        logger.error('Workload analysis failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  program
    .command('analyze bottlenecks')
    .description('Identify performance bottlenecks')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell analyze bottlenecks
`)
    .action(async () => {
      try {
        const cli = getOptimizationCLI();
        await cli.analyzeBottlenecks();
      } catch (error) {
        logger.error('Bottleneck analysis failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  program
    .command('analyze recommendations')
    .description('Get optimization recommendations')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell analyze recommendations
`)
    .action(async () => {
      try {
        const cli = getOptimizationCLI();
        await cli.getRecommendations();
      } catch (error) {
        logger.error('Recommendations failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Auto-Optimization Commands
  program
    .command('auto-optimize enable')
    .description('Enable automatic query optimization')
    .option('--threshold <ms>', 'Optimization threshold in ms', '1000')
    .option('--max-per-day <n>', 'Max optimizations per day', '10')
    .option('--no-approval', 'Skip approval requirement')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell auto-optimize enable
  ${chalk.dim('$')} ai-shell auto-optimize enable --threshold 500 --max-per-day 20
`)
    .action(async (options) => {
      try {
        const cli = getOptimizationCLI();
        await cli.enableAutoOptimization({
          thresholdMs: parseInt(options.threshold),
          maxOptimizationsPerDay: parseInt(options.maxPerDay),
          requireApproval: options.approval !== false
        });
      } catch (error) {
        logger.error('Auto-optimize enable failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  program
    .command('auto-optimize disable')
    .description('Disable automatic query optimization')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell auto-optimize disable
`)
    .action(async () => {
      try {
        const cli = getOptimizationCLI();
        await cli.disableAutoOptimization();
      } catch (error) {
        logger.error('Auto-optimize disable failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  program
    .command('auto-optimize status')
    .description('Show auto-optimization status')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell auto-optimize status
`)
    .action(async () => {
      try {
        const cli = getOptimizationCLI();
        await cli.getAutoOptimizationStatus();
      } catch (error) {
        logger.error('Auto-optimize status failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  program
    .command('auto-optimize configure')
    .description('Configure auto-optimization settings')
    .option('--threshold <ms>', 'Optimization threshold in ms')
    .option('--max-per-day <n>', 'Max optimizations per day')
    .option('--require-approval', 'Require approval for optimizations')
    .option('--allow-index-creation', 'Allow automatic index creation')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell auto-optimize configure --threshold 500
  ${chalk.dim('$')} ai-shell auto-optimize configure --require-approval --allow-index-creation
`)
    .action(async (options) => {
      try {
        const cli = getOptimizationCLI();
        const config: any = {};
        if (options.threshold) config.thresholdMs = parseInt(options.threshold);
        if (options.maxPerDay) config.maxOptimizationsPerDay = parseInt(options.maxPerDay);
        if (options.requireApproval !== undefined) config.requireApproval = options.requireApproval;
        if (options.allowIndexCreation !== undefined) config.indexCreationAllowed = options.allowIndexCreation;
        await cli.configureAutoOptimization(config);
      } catch (error) {
        logger.error('Auto-optimize configuration failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });
}
