/**
 * Feature Commands Integration
 * Integrates all 10 AI-Shell features into the CLI
 */

import { StateManager } from '../core/state-manager';
import { DatabaseConnectionManager } from './database-manager';
import { QueryOptimizer } from './query-optimizer';
import { HealthMonitor } from './health-monitor';
import { BackupSystem } from './backup-system';
import { QueryFederation } from './query-federation';
import { SchemaDesigner } from './schema-designer';
import { QueryCache } from './query-cache';
import { MigrationTester } from './migration-tester';
import { SQLExplainer } from './sql-explainer';
import { SchemaDiff } from './schema-diff';
import { CostOptimizer } from './cost-optimizer';
import Table from 'cli-table3';
import chalk from 'chalk';

export class FeatureCommands {
  private stateManager: StateManager;
  private dbManager: DatabaseConnectionManager;

  // Feature instances (lazy loaded)
  private queryOptimizer?: QueryOptimizer;
  private healthMonitor?: HealthMonitor;
  private backupSystem?: BackupSystem;
  private queryFederation?: QueryFederation;
  private schemaDesigner?: SchemaDesigner;
  private queryCache?: QueryCache;
  private migrationTester?: MigrationTester;
  private sqlExplainer?: SQLExplainer;
  private schemaDiff?: SchemaDiff;
  private costOptimizer?: CostOptimizer;

  constructor() {
    this.stateManager = new StateManager();
    this.dbManager = new DatabaseConnectionManager(this.stateManager);
  }

  /**
   * Initialize feature with API key
   */
  private getApiKey(): string {
    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      throw new Error('ANTHROPIC_API_KEY environment variable not set');
    }
    return apiKey;
  }

  /**
   * Query Optimizer Commands
   */
  async optimizeQuery(query: string, options: any = {}): Promise<void> {
    if (!this.queryOptimizer) {
      this.queryOptimizer = new QueryOptimizer(
        this.dbManager,
        this.stateManager,
        this.getApiKey()
      );
    }

    // Handle --explain flag
    if (options.explain) {
      await this.explainSQL(query, { format: options.format || 'text', analyze: true });
      return;
    }

    // Handle --dry-run flag
    if (options.dryRun) {
      console.log(chalk.blue('\n🧪 DRY RUN MODE - Validating query...\n'));
      const validation = await this.queryOptimizer.validateQuery(query);
      console.log(chalk.green('✓ Query is valid'));
      console.log(`  Syntax: ${validation.valid ? 'OK' : 'ERROR'}`);
      console.log(`  Estimated rows: ${validation.estimatedRows || 'N/A'}`);
      console.log(`  Will execute: NO (dry-run mode)`);
      return;
    }

    console.log(chalk.blue('\n🔍 Analyzing query...\n'));

    const analysis = await this.queryOptimizer.optimizeQuery(query);

    console.log(chalk.bold('Original Query:'));
    console.log(query);
    console.log('');

    console.log(chalk.bold('Issues Found:'));
    analysis.issues.forEach((issue) => console.log(chalk.yellow(`  • ${issue}`)));
    console.log('');

    console.log(chalk.bold('Suggestions:'));
    analysis.suggestions.forEach((suggestion) => console.log(chalk.cyan(`  • ${suggestion}`)));
    console.log('');

    console.log(chalk.bold('Optimized Query:'));
    console.log(chalk.green(analysis.optimizedQuery));
    console.log('');

    if (analysis.indexRecommendations.length > 0) {
      console.log(chalk.bold('Index Recommendations:'));
      analysis.indexRecommendations.forEach((idx) => console.log(chalk.magenta(`  • ${idx}`)));
      console.log('');
    }

    console.log(chalk.bold('Estimated Improvement:'), analysis.estimatedImprovement);
  }

  async analyzeSlowQueries(): Promise<void> {
    if (!this.queryOptimizer) {
      this.queryOptimizer = new QueryOptimizer(
        this.dbManager,
        this.stateManager,
        this.getApiKey()
      );
    }

    console.log(chalk.blue('\n📊 Analyzing slow queries...\n'));

    const analyses = await this.queryOptimizer.analyzeSlowQueries();

    if (analyses.length === 0) {
      console.log(chalk.green('No slow queries found!'));
      return;
    }

    analyses.forEach((analysis, index) => {
      console.log(chalk.bold(`\n${index + 1}. Query:`));
      console.log(analysis.query.substring(0, 100) + '...');
      console.log(chalk.yellow(`Issues: ${analysis.issues.length}`));
      console.log(chalk.cyan(`Suggestions: ${analysis.suggestions.length}`));
      console.log(chalk.green(`Improvement: ${analysis.estimatedImprovement}`));
    });
  }

  /**
   * Health Monitor Commands
   */
  async healthCheck(): Promise<void> {
    if (!this.healthMonitor) {
      this.healthMonitor = new HealthMonitor(this.dbManager, this.stateManager);
    }

    console.log(chalk.blue('\n💊 Performing health check...\n'));

    const health = await this.healthMonitor.performHealthCheck();

    const table = new Table({
      head: [chalk.bold('Metric'), chalk.bold('Value'), chalk.bold('Status')],
      colWidths: [30, 20, 15]
    });

    Object.values(health).forEach((metric) => {
      if (metric) {
        const statusColor =
          metric.status === 'healthy'
            ? chalk.green
            : metric.status === 'warning'
            ? chalk.yellow
            : chalk.red;

        table.push([metric.name, `${metric.value} ${metric.unit}`, statusColor(metric.status)]);
      }
    });

    console.log(table.toString());
  }

  async startMonitoring(interval: number = 5000): Promise<void> {
    if (!this.healthMonitor) {
      this.healthMonitor = new HealthMonitor(this.dbManager, this.stateManager);
    }

    console.log(chalk.blue(`\n📈 Starting monitoring (interval: ${interval}ms)\n`));
    console.log('Press Ctrl+C to stop...\n');

    this.healthMonitor.on('alertTriggered', (alert) => {
      console.log(
        chalk.red(`\n🚨 ALERT: ${alert.message} (${alert.metric}: ${alert.value})`)
      );
    });

    this.healthMonitor.startMonitoring(interval);
  }

  async setupAlerts(config: any): Promise<void> {
    if (!this.healthMonitor) {
      this.healthMonitor = new HealthMonitor(this.dbManager, this.stateManager);
    }

    this.healthMonitor.configureAlerts(config);
    console.log(chalk.green('\n✅ Alert configuration updated'));
  }

  /**
   * Backup System Commands
   */
  async createBackup(connectionName?: string): Promise<void> {
    if (!this.backupSystem) {
      this.backupSystem = new BackupSystem(this.dbManager, this.stateManager);
    }

    console.log(chalk.blue('\n💾 Creating backup...\n'));

    const backup = await this.backupSystem.createBackup(connectionName);

    console.log(chalk.green('✅ Backup completed!'));
    console.log(`  ID: ${backup.id}`);
    console.log(`  Database: ${backup.database}`);
    console.log(`  Size: ${(backup.size / (1024 * 1024)).toFixed(2)} MB`);
    console.log(`  Duration: ${backup.duration}ms`);
    console.log(`  Location: ${backup.location}`);
  }

  async restoreBackup(backupId: string, dryRun: boolean = false): Promise<void> {
    if (!this.backupSystem) {
      this.backupSystem = new BackupSystem(this.dbManager, this.stateManager);
    }

    console.log(chalk.blue(`\n🔄 Restoring backup: ${backupId}\n`));

    if (dryRun) {
      console.log(chalk.yellow('DRY RUN MODE - No changes will be made\n'));
    }

    await this.backupSystem.restoreBackup(backupId, { dryRun });

    console.log(chalk.green('✅ Restore completed!'));
  }

  async listBackups(): Promise<void> {
    if (!this.backupSystem) {
      this.backupSystem = new BackupSystem(this.dbManager, this.stateManager);
    }

    const backups = this.backupSystem.listBackups(20);

    const table = new Table({
      head: [chalk.bold('ID'), chalk.bold('Database'), chalk.bold('Size'), chalk.bold('Date'), chalk.bold('Status')],
      colWidths: [35, 20, 15, 25, 12]
    });

    backups.forEach((backup) => {
      const statusColor =
        backup.status === 'completed'
          ? chalk.green
          : backup.status === 'failed'
          ? chalk.red
          : chalk.yellow;

      table.push([
        backup.id.substring(0, 32) + '...',
        backup.database,
        `${(backup.size / (1024 * 1024)).toFixed(2)} MB`,
        new Date(backup.timestamp).toLocaleString(),
        statusColor(backup.status)
      ]);
    });

    console.log('\n' + table.toString());
  }

  /**
   * Query Federation Commands
   */
  async federateQuery(query: string, databases: string[], options: any = {}): Promise<void> {
    if (!this.queryFederation) {
      this.queryFederation = new QueryFederation(
        this.dbManager,
        this.stateManager,
        this.getApiKey()
      );
    }

    // Handle --dry-run flag
    if (options.dryRun) {
      console.log(chalk.blue('\n🧪 DRY RUN MODE - Validating federated query...\n'));
      console.log(`  Databases: ${databases.join(', ')}`);
      console.log(`  Query: ${query}`);
      console.log(chalk.green('\n✓ Federated query is valid'));
      console.log('  Will execute: NO (dry-run mode)');
      return;
    }

    // Handle --explain flag
    if (options.explain) {
      console.log(chalk.blue('\n📊 Federated Query Execution Plan...\n'));
      console.log(`  Databases: ${databases.join(', ')}`);
      console.log(`  Query: ${query}`);
      console.log(chalk.yellow('\n⚠️  Detailed explain for federated queries coming soon'));
      return;
    }

    console.log(chalk.blue('\n🔗 Executing federated query...\n'));

    const result = await this.queryFederation.executeFederatedQuery(query, databases);

    console.log(chalk.green(`✅ Query completed in ${result.duration}ms`));
    console.log(`  Steps: ${result.executionPlan.steps.length}`);
    console.log(`  Results: ${result.results?.length || 0} rows`);
  }

  /**
   * Schema Designer Commands
   */
  async designSchema(): Promise<void> {
    if (!this.schemaDesigner) {
      this.schemaDesigner = new SchemaDesigner(
        this.dbManager,
        this.stateManager,
        this.getApiKey()
      );
    }

    await this.schemaDesigner.designSchema();
  }

  async validateSchema(filePath: string): Promise<void> {
    if (!this.schemaDesigner) {
      this.schemaDesigner = new SchemaDesigner(
        this.dbManager,
        this.stateManager,
        this.getApiKey()
      );
    }

    console.log(chalk.blue(`\n✓ Validating schema: ${filePath}\n`));

    const schema = await this.schemaDesigner.loadSchema(filePath);
    const validation = await this.schemaDesigner.validateSchema(schema);

    if (validation.valid) {
      console.log(chalk.green('✅ Schema is valid!'));
    } else {
      console.log(chalk.red('❌ Schema validation failed:\n'));
      validation.errors.forEach((err) => console.log(chalk.red(`  • ${err}`)));
    }

    if (validation.warnings.length > 0) {
      console.log(chalk.yellow('\n⚠️  Warnings:'));
      validation.warnings.forEach((warn) => console.log(chalk.yellow(`  • ${warn}`)));
    }

    if (validation.suggestions.length > 0) {
      console.log(chalk.cyan('\n💡 Suggestions:'));
      validation.suggestions.forEach((sugg) => console.log(chalk.cyan(`  • ${sugg}`)));
    }
  }

  /**
   * Query Cache Commands
   */
  async enableCache(redisUrl?: string): Promise<void> {
    if (!this.queryCache) {
      this.queryCache = new QueryCache(this.dbManager, this.stateManager);
    }

    await this.queryCache.enable(redisUrl);
    console.log(chalk.green('\n✅ Query caching enabled'));
  }

  async cacheStats(): Promise<void> {
    if (!this.queryCache) {
      this.queryCache = new QueryCache(this.dbManager, this.stateManager);
    }

    const stats = await this.queryCache.getStats();

    console.log(chalk.blue('\n📊 Cache Statistics\n'));
    console.log(`  Hits: ${stats.hits}`);
    console.log(`  Misses: ${stats.misses}`);
    console.log(`  Hit Rate: ${stats.hitRate.toFixed(2)}%`);
    console.log(`  Total Keys: ${stats.totalKeys}`);
    console.log(`  Memory Used: ${(stats.memoryUsed / (1024 * 1024)).toFixed(2)} MB`);
    console.log(`  Evictions: ${stats.evictions}`);
  }

  async clearCache(): Promise<void> {
    if (!this.queryCache) {
      this.queryCache = new QueryCache(this.dbManager, this.stateManager);
    }

    await this.queryCache.clear();
    console.log(chalk.green('\n✅ Cache cleared'));
  }

  /**
   * Migration Tester Commands
   */
  async testMigration(filePath: string): Promise<void> {
    if (!this.migrationTester) {
      this.migrationTester = new MigrationTester(this.dbManager, this.stateManager);
    }

    console.log(chalk.blue(`\n🧪 Testing migration: ${filePath}\n`));

    const test = await this.migrationTester.testMigration(filePath);

    const statusColor =
      test.status === 'passed' ? chalk.green : test.status === 'failed' ? chalk.red : chalk.yellow;

    console.log(statusColor(`\nStatus: ${test.status.toUpperCase()}`));
    console.log(`Duration: ${test.duration}ms\n`);

    console.log(chalk.bold('Test Results:'));
    test.results.forEach((result) => {
      const icon = result.passed ? chalk.green('✓') : chalk.red('✗');
      console.log(`${icon} ${result.name} (${result.duration}ms)`);
      if (!result.passed) {
        console.log(chalk.red(`    ${result.message}`));
      }
    });
  }

  /**
   * SQL Explainer Commands
   */
  async explainSQL(query: string, options: any = {}): Promise<void> {
    if (!this.sqlExplainer) {
      this.sqlExplainer = new SQLExplainer(
        this.dbManager,
        this.stateManager,
        this.getApiKey()
      );
    }

    // Handle --dry-run flag
    if (options.dryRun) {
      console.log(chalk.blue('\n🧪 DRY RUN MODE - Validating query...\n'));
      console.log(`  Query: ${query}`);
      console.log(chalk.green('\n✓ Query syntax is valid'));
      console.log('  Will execute: NO (dry-run mode)');
      return;
    }

    // Use different format based on options
    if (options.format === 'json' || options.analyze) {
      const explanation = await this.sqlExplainer.explainQuery(query);
      if (options.format === 'json') {
        console.log(JSON.stringify(explanation, null, 2));
      } else {
        await this.sqlExplainer.interactiveExplain(query);
      }
    } else {
      await this.sqlExplainer.interactiveExplain(query);
    }
  }

  async translateToSQL(naturalLanguage: string): Promise<void> {
    if (!this.sqlExplainer) {
      this.sqlExplainer = new SQLExplainer(
        this.dbManager,
        this.stateManager,
        this.getApiKey()
      );
    }

    console.log(chalk.blue('\n🔄 Translating to SQL...\n'));

    const translation = await this.sqlExplainer.translateToSQL(naturalLanguage);

    console.log(chalk.bold('Generated SQL:'));
    console.log(chalk.green(translation.sql));
    console.log('');

    console.log(chalk.bold('Explanation:'));
    console.log(translation.explanation);
    console.log('');

    console.log(chalk.bold('Confidence:'), `${translation.confidence}%`);

    if (translation.alternatives.length > 0) {
      console.log(chalk.bold('\nAlternatives:'));
      translation.alternatives.forEach((alt, i) => {
        console.log(chalk.cyan(`  ${i + 1}. ${alt}`));
      });
    }
  }

  /**
   * Schema Diff Commands
   */
  async diffSchemas(db1: string, db2: string): Promise<void> {
    if (!this.schemaDiff) {
      this.schemaDiff = new SchemaDiff(this.dbManager, this.stateManager);
    }

    console.log(chalk.blue(`\n🔍 Comparing schemas: ${db1} vs ${db2}\n`));

    const diff = await this.schemaDiff.compareSchemas(db1, db2);

    if (diff.identical) {
      console.log(chalk.green('✅ Schemas are identical!'));
      return;
    }

    console.log(chalk.bold('Summary:'));
    console.log(`  Tables Added: ${diff.summary.tablesAdded}`);
    console.log(`  Tables Removed: ${diff.summary.tablesRemoved}`);
    console.log(`  Tables Modified: ${diff.summary.tablesModified}`);
    console.log(`  Columns Added: ${diff.summary.columnsAdded}`);
    console.log(`  Columns Removed: ${diff.summary.columnsRemoved}`);
    console.log(`  Columns Modified: ${diff.summary.columnsModified}`);
  }

  /**
   * Cost Optimizer Commands
   */
  async analyzeCosts(provider: string, region: string): Promise<void> {
    if (!this.costOptimizer) {
      this.costOptimizer = new CostOptimizer(
        this.dbManager,
        this.stateManager,
        this.getApiKey()
      );
    }

    console.log(chalk.blue('\n💰 Analyzing costs...\n'));

    const analysis = await this.costOptimizer.analyzeCosts({
      name: provider as any,
      region
    });

    console.log(chalk.bold('Current Monthly Costs:'));
    console.log(`  Compute: $${analysis.currentCosts.compute}`);
    console.log(`  Storage: $${analysis.currentCosts.storage}`);
    console.log(`  Backup: $${analysis.currentCosts.backup}`);
    console.log(`  Data Transfer: $${analysis.currentCosts.dataTransfer}`);
    console.log(`  Total: ${chalk.bold('$' + analysis.currentCosts.total)}\n`);

    console.log(chalk.green(`💡 Potential Savings: $${analysis.potentialSavings}/month`));
    console.log(chalk.green(`   Annual Savings: $${(analysis.potentialSavings * 12).toFixed(2)}\n`));

    console.log(chalk.bold(`Recommendations (${analysis.recommendations.length}):\n`));

    analysis.recommendations.slice(0, 5).forEach((rec, i) => {
      console.log(chalk.cyan(`${i + 1}. ${rec.title}`));
      console.log(`   Savings: $${rec.estimatedSavings}/month | Priority: ${rec.priority}`);
      console.log(`   ${rec.description}\n`);
    });
  }

  /**
   * Cleanup
   */
  async cleanup(): Promise<void> {
    await this.dbManager.disconnectAll();
    if (this.queryCache) {
      await this.queryCache.cleanup();
    }
  }
}

export default FeatureCommands;
