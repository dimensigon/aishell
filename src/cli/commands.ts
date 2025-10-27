#!/usr/bin/env node

/**
 * AI-Shell CLI Commands
 * Performance monitoring and analytics commands
 */

import { Command } from 'commander';
import { StateManager } from '../core/state-manager';
import { PerformanceMonitor } from './performance-monitor';
import { QueryLogger } from './query-logger';
import { HealthChecker } from './health-checker';
import { DashboardUI } from './dashboard-ui';

const program = new Command();

// Initialize components
const stateManager = new StateManager({
  enablePersistence: true,
  persistencePath: './.ai-shell/state.json',
  autoSaveInterval: 5000
});

const queryLogger = new QueryLogger(stateManager, {
  slowQueryThreshold: 1000,
  persistLogs: true,
  logPath: './.ai-shell/logs'
});

const performanceMonitor = new PerformanceMonitor(stateManager);
const healthChecker = new HealthChecker(stateManager);

// Configure program
program
  .name('ai-shell')
  .description('AI-powered database management shell with performance monitoring')
  .version('1.0.0');

// Performance monitoring commands
const perfCommand = program.command('perf').description('Performance monitoring and analytics');

perfCommand
  .command('monitor')
  .description('Start real-time performance monitoring')
  .option('-i, --interval <seconds>', 'Update interval in seconds', '5')
  .option('-m, --metrics <metrics>', 'Specific metrics to show (comma-separated)')
  .option('--dashboard', 'Show visual dashboard')
  .action(async (options) => {
    try {
      const metrics = options.metrics ? options.metrics.split(',') : undefined;

      if (options.dashboard) {
        // Use blessed dashboard
        const dashboard = new DashboardUI();
        dashboard.render();

        // Update dashboard with metrics
        performanceMonitor.on('metricsUpdate', (metrics) => {
          dashboard.updateMetrics(metrics);
        });

        await performanceMonitor.monitor({
          interval: parseInt(options.interval),
          metrics
        });
      } else {
        await performanceMonitor.monitor({
          interval: parseInt(options.interval),
          metrics
        });
      }
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });

perfCommand
  .command('slow-queries')
  .description('Show slow queries')
  .option('-t, --threshold <ms>', 'Slow query threshold in milliseconds', '1000')
  .option('-l, --limit <n>', 'Number of queries to show', '10')
  .action(async (options) => {
    try {
      const threshold = parseInt(options.threshold);
      const limit = parseInt(options.limit);

      const slowQueries = await performanceMonitor.slowQueries(threshold, limit);

      if (slowQueries.length === 0) {
        console.log('✓ No slow queries found');
        return;
      }

      console.log(`\n🐌 Found ${slowQueries.length} slow queries:\n`);

      for (const query of slowQueries) {
        console.log(`⏱️  ${query.executionTime.toFixed(2)}ms (${query.frequency}x)`);
        console.log(`   ${query.query.substring(0, 80)}${query.query.length > 80 ? '...' : ''}`);

        if (query.optimizations && query.optimizations.length > 0) {
          console.log('   💡 Suggestions:');
          query.optimizations.forEach((opt) => console.log(`      - ${opt}`));
        }

        console.log();
      }
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });

perfCommand
  .command('analyze <query>')
  .description('Analyze query performance and suggest optimizations')
  .action(async (query) => {
    try {
      const analysis = await performanceMonitor.analyzeQuery(query);

      console.log('\n📊 Query Analysis:\n');
      console.log(`Query: ${analysis.query}\n`);

      console.log('Execution Plan:');
      console.log(JSON.stringify(analysis.executionPlan, null, 2));
      console.log();

      console.log(`Estimated Cost: ${analysis.estimatedCost}`);
      console.log();

      if (analysis.missingIndexes.length > 0) {
        console.log('⚠️  Missing Indexes:');
        analysis.missingIndexes.forEach((idx) => console.log(`   - ${idx}`));
        console.log();
      }

      if (analysis.optimizationSuggestions.length > 0) {
        console.log('💡 Optimization Suggestions:');
        analysis.optimizationSuggestions.forEach((sug) => console.log(`   - ${sug}`));
        console.log();
      }

      if (analysis.rewriteSuggestion) {
        console.log('✨ Suggested Rewrite:');
        console.log(`   ${analysis.rewriteSuggestion}`);
        console.log();
      }
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });

perfCommand
  .command('indexes')
  .description('Suggest missing indexes')
  .action(async () => {
    try {
      const suggestions = await performanceMonitor.indexRecommendations();

      if (suggestions.length === 0) {
        console.log('✓ No index recommendations');
        return;
      }

      console.log(`\n📊 Index Recommendations (${suggestions.length}):\n`);

      for (const suggestion of suggestions) {
        console.log(`📍 ${suggestion.table}.${suggestion.columns.join(', ')}`);
        console.log(`   Reason: ${suggestion.reason}`);
        console.log(`   Impact: ${suggestion.estimatedImprovement}`);
        console.log(`   Command: ${suggestion.createStatement}`);
        console.log();
      }
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });

perfCommand
  .command('pool')
  .description('Show connection pool statistics')
  .action(async () => {
    try {
      const stats = await performanceMonitor.connectionPool();

      console.log('\n🔗 Connection Pool Statistics:\n');
      console.log(`Total Connections: ${stats.totalConnections}`);
      console.log(`Active: ${stats.activeConnections}`);
      console.log(`Idle: ${stats.idleConnections}`);
      console.log(`Waiting Queries: ${stats.waitingQueries}`);
      console.log(`Average Wait Time: ${stats.averageWaitTime}ms`);
      console.log(`Max Wait Time: ${stats.maxWaitTime}ms`);
      console.log();
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });

// Health check commands
const healthCommand = program.command('health').description('Database health checks');

healthCommand
  .command('check')
  .description('Run comprehensive health check')
  .action(async () => {
    try {
      await healthChecker.check();
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });

healthCommand
  .command('fix')
  .description('Automatically fix health issues')
  .option('--auto', 'Auto-fix without confirmation')
  .option('--issues <ids>', 'Specific issue IDs to fix (comma-separated)')
  .action(async (options) => {
    try {
      const issueIds = options.issues ? options.issues.split(',') : undefined;
      const results = await healthChecker.autoFix(issueIds, {
        confirm: !options.auto
      });

      console.log(`\n✓ Fixed ${results.filter((r) => r.success).length} of ${results.length} issues\n`);
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });

healthCommand
  .command('recommendations')
  .description('Get actionable health recommendations')
  .action(async () => {
    try {
      const recommendations = await healthChecker.recommendations();

      if (recommendations.length === 0) {
        console.log('✓ No recommendations');
        return;
      }

      console.log(`\n💡 Health Recommendations (${recommendations.length}):\n`);

      for (const rec of recommendations) {
        const priorityIcon = {
          critical: '🔴',
          high: '🟠',
          medium: '🟡',
          low: '🔵'
        }[rec.priority];

        console.log(`${priorityIcon} [${rec.priority.toUpperCase()}] ${rec.title}`);
        console.log(`   ${rec.description}`);
        console.log(`   Impact: ${rec.expectedImpact}`);
        console.log(`   Command: ${rec.command}`);
        console.log(`   Time: ${rec.estimatedTime} | Risk: ${rec.riskLevel}`);
        console.log();
      }
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });

// Query history commands
const historyCommand = program.command('history').description('Query history and analytics');

historyCommand
  .command('list')
  .description('Show recent query history')
  .option('-l, --limit <n>', 'Number of queries to show', '20')
  .option('-o, --offset <n>', 'Offset for pagination', '0')
  .action(async (options) => {
    try {
      const limit = parseInt(options.limit);
      const offset = parseInt(options.offset);

      const history = await queryLogger.getHistory(limit, offset);

      console.log(`\n📝 Query History (${history.logs.length} of ${history.total}):\n`);

      for (const log of history.logs) {
        const time = new Date(log.timestamp).toLocaleString();
        const duration = log.duration.toFixed(2);
        const status = log.result?.error ? '❌' : '✓';

        console.log(`${status} [${time}] ${duration}ms`);
        console.log(`   ${log.query.substring(0, 80)}${log.query.length > 80 ? '...' : ''}`);

        if (log.result?.error) {
          console.log(`   Error: ${log.result.error}`);
        }

        console.log();
      }

      if (history.total > limit) {
        console.log(`Page ${history.page} of ${Math.ceil(history.total / limit)}`);
        console.log(`Use --offset ${offset + limit} for next page`);
      }
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });

historyCommand
  .command('analyze')
  .description('Analyze query patterns')
  .action(async () => {
    try {
      const analytics = await queryLogger.analyze();

      console.log('\n📊 Query Analytics:\n');
      console.log(`Total Queries: ${analytics.totalQueries}`);
      console.log(`Average Duration: ${analytics.averageDuration.toFixed(2)}ms`);
      console.log(`Error Rate: ${(analytics.errorRate * 100).toFixed(2)}%`);
      console.log(`Performance Trend: ${analytics.performanceTrend}`);
      console.log();

      if (analytics.slowestQuery) {
        console.log('🐌 Slowest Query:');
        console.log(`   ${analytics.slowestQuery.duration.toFixed(2)}ms`);
        console.log(`   ${analytics.slowestQuery.query.substring(0, 60)}...`);
        console.log();
      }

      console.log('📈 Query Type Distribution:');
      for (const [type, count] of Object.entries(analytics.queryTypeDistribution)) {
        const percent = ((count / analytics.totalQueries) * 100).toFixed(1);
        console.log(`   ${type}: ${count} (${percent}%)`);
      }
      console.log();

      if (analytics.mostFrequent.length > 0) {
        console.log('🔥 Most Frequent Queries:');
        analytics.mostFrequent.slice(0, 5).forEach((q, i) => {
          console.log(`   ${i + 1}. ${q.count}x - ${q.avgDuration.toFixed(2)}ms avg`);
          console.log(`      ${q.query.substring(0, 60)}...`);
        });
        console.log();
      }

      if (analytics.peakUsageTimes.length > 0) {
        console.log('⏰ Peak Usage Times:');
        analytics.peakUsageTimes.forEach((peak) => {
          console.log(`   ${peak.hour}:00 - ${peak.count} queries`);
        });
        console.log();
      }
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });

historyCommand
  .command('export <format> <filepath>')
  .description('Export query logs (csv or json)')
  .action(async (format, filepath) => {
    try {
      if (format !== 'csv' && format !== 'json') {
        throw new Error('Format must be "csv" or "json"');
      }

      await queryLogger.export(format as 'csv' | 'json', filepath);
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });

historyCommand
  .command('search <pattern>')
  .description('Search query logs')
  .option('-i, --ignore-case', 'Case insensitive search')
  .option('-l, --limit <n>', 'Limit results', '10')
  .action(async (pattern, options) => {
    try {
      const results = queryLogger.search(pattern, {
        caseSensitive: !options.ignoreCase,
        limit: parseInt(options.limit)
      });

      if (results.length === 0) {
        console.log('No queries found');
        return;
      }

      console.log(`\n🔍 Found ${results.length} matching queries:\n`);

      for (const log of results) {
        const time = new Date(log.timestamp).toLocaleString();
        console.log(`[${time}] ${log.duration.toFixed(2)}ms`);
        console.log(`   ${log.query}`);
        console.log();
      }
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });

historyCommand
  .command('clear')
  .description('Clear all query logs')
  .action(() => {
    try {
      const count = queryLogger.clearLogs();
      console.log(`✓ Cleared ${count} query logs`);
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });

// Dashboard command
program
  .command('dashboard')
  .description('Launch interactive performance dashboard')
  .option('-i, --interval <seconds>', 'Update interval in seconds', '5')
  .action(async (options) => {
    try {
      const dashboard = new DashboardUI({
        refreshInterval: parseInt(options.interval) * 1000
      });

      dashboard.render();

      // Update dashboard with real-time data
      performanceMonitor.on('metricsUpdate', (metrics) => {
        dashboard.updateMetrics(metrics);
      });

      performanceMonitor.on('slowQueryDetected', async () => {
        const slowQueries = await performanceMonitor.slowQueries(1000, 5);
        dashboard.updateSlowQueries(slowQueries);
      });

      // Start monitoring
      await performanceMonitor.monitor({
        interval: parseInt(options.interval)
      });
    } catch (error) {
      console.error('Error:', error instanceof Error ? error.message : String(error));
      process.exit(1);
    }
  });

// Parse arguments
if (require.main === module) {
  program.parse(process.argv);
}

export { program };
