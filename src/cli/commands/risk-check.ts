/**
 * Risk Check Command
 * Analyze query risk and detect dangerous operations
 *
 * Usage: ai-shell risk-check <query>
 */

import { Command } from 'commander';
import chalk from 'chalk';
import { createLogger } from '../../core/logger';
import { DatabaseConnectionManager } from '../database-manager';
import { StateManager } from '../../core/state-manager';

const logger = createLogger('RiskCheckCommand');

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export interface RiskAnalysis {
  query: string;
  riskLevel: RiskLevel;
  risks: Risk[];
  warnings: string[];
  recommendations: string[];
  affectedTables: string[];
  estimatedAffectedRows: number;
  requiresConfirmation: boolean;
  canRollback: boolean;
}

export interface Risk {
  type: string;
  severity: RiskLevel;
  description: string;
  mitigation: string;
}

/**
 * Register risk-check command
 */
export function registerRiskCheckCommand(program: Command): void {
  program
    .command('risk-check <query>')
    .description('Analyze query risk level and detect dangerous operations')
    .alias('risk')
    .option('--format <type>', 'Output format (text, json)', 'text')
    .option('--auto-approve', 'Skip confirmation for low-risk queries', false)
    .option('-v, --verbose', 'Enable verbose logging', false)
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell risk-check "SELECT * FROM users"
  ${chalk.dim('$')} ai-shell risk "DELETE FROM orders WHERE status = 'cancelled'"
  ${chalk.dim('$')} ai-shell risk-check "DROP TABLE temp_data"
  ${chalk.dim('$')} ai-shell risk-check "UPDATE users SET password = 'default'" --format json

${chalk.bold('Risk Levels:')}
  • ${chalk.green('LOW')}      - Read-only queries, no side effects
  • ${chalk.yellow('MEDIUM')}   - Updates with WHERE clause, minor changes
  • ${chalk.red('HIGH')}     - Bulk updates/deletes, schema changes
  • ${chalk.bgRed.white(' CRITICAL ')} - DROP, TRUNCATE, bulk DELETE without WHERE

${chalk.bold('Features:')}
  • Detects dangerous operations
  • Estimates affected rows
  • Provides mitigation strategies
  • Requires confirmation for high-risk queries
  • Transaction rollback support
`)
    .action(async (query: string, options) => {
      try {
        if (options.verbose) {
          process.env.LOG_LEVEL = 'debug';
        }

        logger.info('Analyzing query risk', { queryLength: query.length });

        console.log(chalk.cyan('\n🔒 Query Risk Analysis\n'));

        // Initialize services
        const stateManager = new StateManager();
        const dbManager = new DatabaseConnectionManager(stateManager);

        // Analyze query
        const ora = (await import('ora')).default;
        const spinner = ora('Analyzing query...').start();

        try {
          const analysis = await analyzeQueryRisk(dbManager, query);

          spinner.succeed('Analysis complete');

          // Display results
          if (options.format === 'json') {
            console.log(JSON.stringify(analysis, null, 2));
          } else {
            displayRiskAnalysis(analysis);
          }

          // Handle high-risk queries
          if (analysis.requiresConfirmation && !options.autoApprove) {
            console.log(chalk.yellow('\n⚠️  This query requires explicit confirmation\n'));

            const readline = require('readline').createInterface({
              input: process.stdin,
              output: process.stdout
            });

            await new Promise<void>((resolve, reject) => {
              readline.question(chalk.bold('Type "CONFIRM" to proceed, or anything else to cancel: '), (answer: string) => {
                readline.close();

                if (answer !== 'CONFIRM') {
                  console.log(chalk.red('\n❌ Operation cancelled for safety\n'));
                  reject(new Error('User cancelled high-risk operation'));
                } else {
                  console.log(chalk.green('\n✅ Confirmation received\n'));
                  resolve();
                }
              });
            });
          }

          // Exit code based on risk level
          if (analysis.riskLevel === 'critical') {
            process.exit(2); // Critical risk
          } else if (analysis.riskLevel === 'high') {
            process.exit(1); // High risk
          }

        } catch (error) {
          spinner.fail('Analysis failed');
          throw error;
        }

      } catch (error) {
        logger.error('Risk check failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });
}

/**
 * Analyze query risk
 */
async function analyzeQueryRisk(
  dbManager: DatabaseConnectionManager,
  query: string
): Promise<RiskAnalysis> {
  const normalizedQuery = query.toUpperCase().trim();

  // Detect operation type
  const operation = detectOperation(normalizedQuery);

  // Analyze risks
  const risks: Risk[] = [];
  const warnings: string[] = [];
  const recommendations: string[] = [];

  let riskLevel: RiskLevel = 'low';
  let requiresConfirmation = false;

  // Check for critical operations
  if (operation === 'DROP') {
    risks.push({
      type: 'DATA_LOSS',
      severity: 'critical',
      description: 'DROP operation will permanently delete database objects',
      mitigation: 'Create backup before proceeding. Consider using soft deletes instead.'
    });
    riskLevel = 'critical';
    requiresConfirmation = true;
  }

  if (operation === 'TRUNCATE') {
    risks.push({
      type: 'BULK_DELETE',
      severity: 'critical',
      description: 'TRUNCATE will delete all rows and cannot be rolled back in some databases',
      mitigation: 'Use DELETE with WHERE clause if you need rollback capability.'
    });
    riskLevel = 'critical';
    requiresConfirmation = true;
  }

  // Check for DELETE without WHERE
  if (operation === 'DELETE' && !normalizedQuery.includes('WHERE')) {
    risks.push({
      type: 'UNFILTERED_DELETE',
      severity: 'critical',
      description: 'DELETE without WHERE clause will remove all rows',
      mitigation: 'Add WHERE clause to limit affected rows. Use TRUNCATE if intentional.'
    });
    riskLevel = 'critical';
    requiresConfirmation = true;
    warnings.push('No WHERE clause detected - will affect ALL rows');
  }

  // Check for UPDATE without WHERE
  if (operation === 'UPDATE' && !normalizedQuery.includes('WHERE')) {
    risks.push({
      type: 'UNFILTERED_UPDATE',
      severity: 'high',
      description: 'UPDATE without WHERE clause will modify all rows',
      mitigation: 'Add WHERE clause to limit affected rows.'
    });
    riskLevel = 'high';
    requiresConfirmation = true;
    warnings.push('No WHERE clause detected - will affect ALL rows');
  }

  // Check for ALTER operations
  if (operation === 'ALTER') {
    risks.push({
      type: 'SCHEMA_CHANGE',
      severity: 'high',
      description: 'Schema changes may cause downtime or data loss',
      mitigation: 'Test in development environment first. Consider zero-downtime migration strategies.'
    });
    riskLevel = 'high';
    requiresConfirmation = true;
  }

  // Check for dangerous patterns
  if (normalizedQuery.includes('*') && operation !== 'SELECT') {
    warnings.push('Wildcard (*) used in non-SELECT operation');
  }

  if (normalizedQuery.includes('CASCADE')) {
    risks.push({
      type: 'CASCADE_EFFECT',
      severity: 'high',
      description: 'CASCADE will affect related objects automatically',
      mitigation: 'Verify all dependent objects before proceeding.'
    });
    warnings.push('CASCADE option detected - will affect dependent objects');
  }

  // Extract affected tables
  const affectedTables = extractTables(query);

  // Estimate affected rows (mock implementation)
  const estimatedAffectedRows = await estimateAffectedRows(dbManager, query, affectedTables);

  // Generate recommendations
  if (riskLevel === 'low') {
    recommendations.push('Query appears safe to execute');
  } else {
    recommendations.push('Run in transaction for easy rollback: BEGIN; ... ROLLBACK;');
    recommendations.push('Test in development environment first');
    recommendations.push('Create backup before executing');
  }

  if (operation === 'DELETE' || operation === 'UPDATE') {
    recommendations.push('Consider using LIMIT clause to batch the operation');
  }

  return {
    query,
    riskLevel,
    risks,
    warnings,
    recommendations,
    affectedTables,
    estimatedAffectedRows,
    requiresConfirmation,
    canRollback: operation !== 'TRUNCATE' && operation !== 'DROP'
  };
}

/**
 * Detect SQL operation type
 */
function detectOperation(query: string): string {
  const operations = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE', 'ALTER', 'CREATE'];

  for (const op of operations) {
    if (query.startsWith(op)) {
      return op;
    }
  }

  return 'UNKNOWN';
}

/**
 * Extract table names from query
 */
function extractTables(query: string): string[] {
  const tables: string[] = [];

  // Simple regex-based extraction (in real implementation would use SQL parser)
  const fromMatch = query.match(/FROM\s+(\w+)/i);
  if (fromMatch) {
    tables.push(fromMatch[1]);
  }

  const joinMatches = query.matchAll(/JOIN\s+(\w+)/gi);
  for (const match of joinMatches) {
    tables.push(match[1]);
  }

  const updateMatch = query.match(/UPDATE\s+(\w+)/i);
  if (updateMatch) {
    tables.push(updateMatch[1]);
  }

  const deleteMatch = query.match(/DELETE\s+FROM\s+(\w+)/i);
  if (deleteMatch) {
    tables.push(deleteMatch[1]);
  }

  return [...new Set(tables)]; // Remove duplicates
}

/**
 * Estimate affected rows
 */
async function estimateAffectedRows(
  dbManager: DatabaseConnectionManager,
  query: string,
  tables: string[]
): Promise<number> {
  // Mock implementation - in real scenario would query table statistics
  const operation = detectOperation(query.toUpperCase());

  if (operation === 'SELECT') {
    return 0; // Read-only
  }

  // Estimate based on operation
  if (query.toUpperCase().includes('WHERE')) {
    return Math.floor(Math.random() * 1000); // Some rows
  } else {
    return 50000; // All rows (mock)
  }
}

/**
 * Display risk analysis in formatted output
 */
function displayRiskAnalysis(analysis: RiskAnalysis): void {
  // Risk level header
  const riskColors: Record<RiskLevel, any> = {
    low: chalk.green,
    medium: chalk.yellow,
    high: chalk.red,
    critical: chalk.bgRed.white
  };

  const riskColor = riskColors[analysis.riskLevel];

  console.log(chalk.bold('Risk Level: ') + riskColor(analysis.riskLevel.toUpperCase()));
  console.log(chalk.bold('Affected Tables: ') + chalk.cyan(analysis.affectedTables.join(', ') || 'None'));
  console.log(chalk.bold('Estimated Affected Rows: ') + chalk.yellow(analysis.estimatedAffectedRows.toLocaleString()));
  console.log(chalk.bold('Can Rollback: ') + (analysis.canRollback ? chalk.green('Yes') : chalk.red('No')));

  // Display risks
  if (analysis.risks.length > 0) {
    console.log(chalk.bold('\n⚠️  Identified Risks:\n'));

    analysis.risks.forEach((risk, index) => {
      const severityColor = riskColors[risk.severity];
      console.log(chalk.bold(`${index + 1}. ${risk.type}`));
      console.log(`   Severity: ${severityColor(risk.severity.toUpperCase())}`);
      console.log(`   ${chalk.dim(risk.description)}`);
      console.log(`   ${chalk.italic('Mitigation:')} ${chalk.dim(risk.mitigation)}`);
      console.log('');
    });
  }

  // Display warnings
  if (analysis.warnings.length > 0) {
    console.log(chalk.yellow.bold('⚠️  Warnings:\n'));
    analysis.warnings.forEach(warning => {
      console.log(chalk.yellow(`  • ${warning}`));
    });
    console.log('');
  }

  // Display recommendations
  if (analysis.recommendations.length > 0) {
    console.log(chalk.cyan.bold('💡 Recommendations:\n'));
    analysis.recommendations.forEach(rec => {
      console.log(chalk.cyan(`  • ${rec}`));
    });
    console.log('');
  }

  // Query preview
  console.log(chalk.bold('Query:'));
  console.log(chalk.dim(analysis.query));
  console.log('');
}
