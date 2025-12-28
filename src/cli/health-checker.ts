/**
 * Database Health Checker
 * Comprehensive health checks and automated fixes
 */

import { EventEmitter } from 'eventemitter3';
import { StateManager } from '../core/state-manager';

/**
 * Health issue severity
 */
export type HealthSeverity = 'info' | 'warning' | 'error' | 'critical';

/**
 * Health issue
 */
export interface HealthIssue {
  id: string;
  category: string;
  severity: HealthSeverity;
  title: string;
  description: string;
  impact: string;
  detected: number;
  fixable: boolean;
  fixCommand?: string;
}

/**
 * Health report
 */
export interface HealthReport {
  timestamp: number;
  overallHealth: 'healthy' | 'warning' | 'critical';
  score: number; // 0-100
  issues: HealthIssue[];
  checks: {
    connectivity: boolean;
    diskSpace: { available: number; total: number; usage: number };
    tableBloat: Array<{ table: string; bloatPercent: number }>;
    missingIndexes: Array<{ table: string; column: string }>;
    unusedIndexes: Array<{ table: string; index: string }>;
    outdatedStats: string[];
    replicationLag?: number;
    lockContentions: number;
  };
}

/**
 * Recommendation
 */
export interface Recommendation {
  id: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  expectedImpact: string;
  command: string;
  estimatedTime: string;
  riskLevel: 'safe' | 'low' | 'medium' | 'high';
}

/**
 * Fix result
 */
export interface FixResult {
  issueId: string;
  success: boolean;
  message: string;
  error?: Error;
}

/**
 * Health checker events
 */
export interface HealthCheckerEvents {
  issueDetected: (issue: HealthIssue) => void;
  checkComplete: (report: HealthReport) => void;
  fixApplied: (result: FixResult) => void;
}

/**
 * Database Health Checker
 */
export class HealthChecker extends EventEmitter<HealthCheckerEvents> {
  private issueCounter = 0;

  constructor(private stateManager: StateManager) {
    super();
  }

  /**
   * Run comprehensive health check
   */
  async check(): Promise<HealthReport> {
    console.log('🏥 Running database health check...\n');

    const issues: HealthIssue[] = [];

    // Perform all checks
    const connectivity = await this.checkConnectivity();
    const diskSpace = await this.checkDiskSpace();
    const tableBloat = await this.checkTableBloat();
    const missingIndexes = await this.checkMissingIndexes();
    const unusedIndexes = await this.checkUnusedIndexes();
    const outdatedStats = await this.checkOutdatedStats();
    const replicationLag = await this.checkReplicationLag();
    const lockContentions = await this.checkLockContentions();

    // Connectivity check
    if (!connectivity) {
      issues.push(this.createIssue('connectivity', 'critical', 'Database Connection Failed', 'Cannot connect to database', 'All operations blocked', false));
    }

    // Disk space check
    if (diskSpace.usage > 90) {
      issues.push(this.createIssue('disk', 'critical', 'Disk Space Critical', `Disk usage at ${diskSpace.usage.toFixed(1)}%`, 'Database may become read-only', true, 'VACUUM FULL;'));
    } else if (diskSpace.usage > 80) {
      issues.push(this.createIssue('disk', 'warning', 'Disk Space Low', `Disk usage at ${diskSpace.usage.toFixed(1)}%`, 'May affect performance', true, 'VACUUM;'));
    }

    // Table bloat check
    for (const bloat of tableBloat) {
      if (bloat.bloatPercent > 50) {
        issues.push(this.createIssue('bloat', 'warning', `Table Bloat: ${bloat.table}`, `${bloat.bloatPercent.toFixed(1)}% bloat detected`, 'Wasted disk space and slower queries', true, `VACUUM FULL ${bloat.table};`));
      }
    }

    // Missing indexes check
    for (const missing of missingIndexes) {
      issues.push(this.createIssue('index', 'warning', `Missing Index: ${missing.table}.${missing.column}`, 'Foreign key without index', 'Slower JOIN operations', true, `CREATE INDEX idx_${missing.table}_${missing.column} ON ${missing.table}(${missing.column});`));
    }

    // Unused indexes check
    for (const unused of unusedIndexes) {
      issues.push(this.createIssue('index', 'info', `Unused Index: ${unused.index}`, `Index on ${unused.table} not used`, 'Wasted disk space and slower writes', true, `DROP INDEX ${unused.index};`));
    }

    // Outdated statistics check
    for (const table of outdatedStats) {
      issues.push(this.createIssue('stats', 'warning', `Outdated Statistics: ${table}`, 'Query planner may make poor decisions', 'Suboptimal query plans', true, `ANALYZE ${table};`));
    }

    // Replication lag check
    if (replicationLag !== undefined && replicationLag > 60) {
      issues.push(this.createIssue('replication', 'error', 'High Replication Lag', `${replicationLag} seconds behind primary`, 'Stale data on replicas', false));
    }

    // Lock contention check
    if (lockContentions > 10) {
      issues.push(this.createIssue('locks', 'error', 'High Lock Contention', `${lockContentions} lock waits detected`, 'Reduced concurrency and performance', false));
    }

    // Calculate overall health
    const score = this.calculateHealthScore(issues);
    const overallHealth = this.determineOverallHealth(score, issues);

    const report: HealthReport = {
      timestamp: Date.now(),
      overallHealth,
      score,
      issues,
      checks: {
        connectivity,
        diskSpace,
        tableBloat,
        missingIndexes,
        unusedIndexes,
        outdatedStats,
        replicationLag,
        lockContentions
      }
    };

    // Store report
    this.stateManager.set('health:latest', report, {
      metadata: { type: 'health-report' }
    });

    this.emit('checkComplete', report);

    // Display report
    this.displayReport(report);

    return report;
  }

  /**
   * Generate actionable recommendations
   */
  async recommendations(): Promise<Recommendation[]> {
    const report = this.stateManager.get<HealthReport>('health:latest');
    if (!report) {
      throw new Error('No health report available. Run health check first.');
    }

    const recommendations: Recommendation[] = [];

    // Generate recommendations from issues
    for (const issue of report.issues) {
      if (issue.fixable && issue.fixCommand) {
        recommendations.push({
          id: issue.id,
          priority: this.severityToPriority(issue.severity),
          title: `Fix: ${issue.title}`,
          description: issue.description,
          expectedImpact: issue.impact,
          command: issue.fixCommand,
          estimatedTime: this.estimateFixTime(issue),
          riskLevel: this.estimateRiskLevel(issue)
        });
      }
    }

    // Sort by priority
    const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
    recommendations.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);

    return recommendations;
  }

  /**
   * Automatically fix issues
   */
  async autoFix(issueIds?: string[], options: { confirm?: boolean } = {}): Promise<FixResult[]> {
    const report = this.stateManager.get<HealthReport>('health:latest');
    if (!report) {
      throw new Error('No health report available. Run health check first.');
    }

    const issuesToFix = issueIds
      ? report.issues.filter((issue) => issueIds.includes(issue.id))
      : report.issues.filter((issue) => issue.fixable);

    if (issuesToFix.length === 0) {
      console.log('✓ No fixable issues found');
      return [];
    }

    console.log(`\n🔧 Fixing ${issuesToFix.length} issue(s)...\n`);

    const results: FixResult[] = [];

    for (const issue of issuesToFix) {
      // Show confirmation if needed
      if (options.confirm && this.estimateRiskLevel(issue) !== 'safe') {
        console.log(`\n⚠️  ${issue.title}`);
        console.log(`   Command: ${issue.fixCommand}`);
        console.log(`   Risk: ${this.estimateRiskLevel(issue)}`);
        // In real implementation, use inquirer for confirmation
        console.log('   Skipping (confirmation required)');
        continue;
      }

      const result = await this.applyFix(issue);
      results.push(result);

      if (result.success) {
        console.log(`✓ ${result.message}`);
      } else {
        console.log(`✗ ${result.message}`);
      }
    }

    return results;
  }

  /**
   * Apply a fix for an issue
   */
  private async applyFix(issue: HealthIssue): Promise<FixResult> {
    try {
      if (!issue.fixCommand) {
        throw new Error('No fix command available');
      }

      // In real implementation, execute the fix command
      console.log(`Executing: ${issue.fixCommand}`);

      // Simulate fix execution
      await new Promise((resolve) => setTimeout(resolve, 100));

      const result: FixResult = {
        issueId: issue.id,
        success: true,
        message: `Fixed: ${issue.title}`
      };

      this.emit('fixApplied', result);
      return result;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      return {
        issueId: issue.id,
        success: false,
        message: `Failed to fix ${issue.title}`,
        error: err
      };
    }
  }

  // Health check methods

  private async checkConnectivity(): Promise<boolean> {
    // Mock implementation
    return true;
  }

  private async checkDiskSpace(): Promise<{ available: number; total: number; usage: number }> {
    // Mock implementation
    const total = 100 * 1024 * 1024 * 1024; // 100 GB
    const available = 20 * 1024 * 1024 * 1024; // 20 GB
    return {
      total,
      available,
      usage: ((total - available) / total) * 100
    };
  }

  private async checkTableBloat(): Promise<Array<{ table: string; bloatPercent: number }>> {
    // Mock implementation
    return [
      { table: 'users', bloatPercent: 25 },
      { table: 'sessions', bloatPercent: 60 }
    ];
  }

  private async checkMissingIndexes(): Promise<Array<{ table: string; column: string }>> {
    // Mock implementation
    return [
      { table: 'orders', column: 'user_id' },
      { table: 'posts', column: 'author_id' }
    ];
  }

  private async checkUnusedIndexes(): Promise<Array<{ table: string; index: string }>> {
    // Mock implementation
    return [{ table: 'logs', index: 'idx_logs_old_field' }];
  }

  private async checkOutdatedStats(): Promise<string[]> {
    // Mock implementation
    return ['users', 'products'];
  }

  private async checkReplicationLag(): Promise<number | undefined> {
    // Mock implementation - return undefined if not applicable
    return undefined;
  }

  private async checkLockContentions(): Promise<number> {
    // Mock implementation
    return 3;
  }

  // Helper methods

  private createIssue(
    category: string,
    severity: HealthSeverity,
    title: string,
    description: string,
    impact: string,
    fixable: boolean,
    fixCommand?: string
  ): HealthIssue {
    const issue: HealthIssue = {
      id: `issue_${++this.issueCounter}`,
      category,
      severity,
      title,
      description,
      impact,
      detected: Date.now(),
      fixable,
      fixCommand
    };

    this.emit('issueDetected', issue);
    return issue;
  }

  private calculateHealthScore(issues: HealthIssue[]): number {
    let score = 100;

    for (const issue of issues) {
      switch (issue.severity) {
        case 'critical':
          score -= 25;
          break;
        case 'error':
          score -= 15;
          break;
        case 'warning':
          score -= 5;
          break;
        case 'info':
          score -= 1;
          break;
      }
    }

    return Math.max(0, score);
  }

  private determineOverallHealth(score: number, issues: HealthIssue[]): 'healthy' | 'warning' | 'critical' {
    const hasCritical = issues.some((i) => i.severity === 'critical');
    if (hasCritical || score < 50) return 'critical';
    if (score < 80) return 'warning';
    return 'healthy';
  }

  private severityToPriority(severity: HealthSeverity): 'low' | 'medium' | 'high' | 'critical' {
    switch (severity) {
      case 'critical':
        return 'critical';
      case 'error':
        return 'high';
      case 'warning':
        return 'medium';
      case 'info':
        return 'low';
    }
  }

  private estimateFixTime(issue: HealthIssue): string {
    if (issue.category === 'index') return '< 1 minute';
    if (issue.category === 'stats') return '< 5 minutes';
    if (issue.category === 'bloat') return '10-30 minutes';
    return '< 10 minutes';
  }

  private estimateRiskLevel(issue: HealthIssue): 'safe' | 'low' | 'medium' | 'high' {
    if (issue.category === 'stats') return 'safe';
    if (issue.category === 'index' && issue.fixCommand?.includes('CREATE')) return 'safe';
    if (issue.category === 'index' && issue.fixCommand?.includes('DROP')) return 'low';
    if (issue.fixCommand?.includes('VACUUM FULL')) return 'medium';
    return 'low';
  }

  private displayReport(report: HealthReport): void {
    console.log('═══════════════════════════════════════════════════════════');
    console.log('                   HEALTH REPORT');
    console.log('═══════════════════════════════════════════════════════════\n');

    // Overall health
    const healthIcon = {
      healthy: '✓',
      warning: '⚠️',
      critical: '✗'
    }[report.overallHealth];

    console.log(`${healthIcon} Overall Health: ${report.overallHealth.toUpperCase()}`);
    console.log(`   Health Score: ${report.score}/100\n`);

    // Issues by severity
    const critical = report.issues.filter((i) => i.severity === 'critical');
    const errors = report.issues.filter((i) => i.severity === 'error');
    const warnings = report.issues.filter((i) => i.severity === 'warning');
    const info = report.issues.filter((i) => i.severity === 'info');

    if (critical.length > 0) {
      console.log(`🔴 Critical Issues: ${critical.length}`);
      critical.forEach((issue) => console.log(`   - ${issue.title}`));
      console.log();
    }

    if (errors.length > 0) {
      console.log(`🟠 Errors: ${errors.length}`);
      errors.forEach((issue) => console.log(`   - ${issue.title}`));
      console.log();
    }

    if (warnings.length > 0) {
      console.log(`🟡 Warnings: ${warnings.length}`);
      warnings.forEach((issue) => console.log(`   - ${issue.title}`));
      console.log();
    }

    if (info.length > 0) {
      console.log(`🔵 Info: ${info.length}`);
      info.forEach((issue) => console.log(`   - ${issue.title}`));
      console.log();
    }

    // Quick stats
    console.log('Quick Stats:');
    console.log(`   Disk Usage: ${report.checks.diskSpace.usage.toFixed(1)}%`);
    console.log(`   Lock Contentions: ${report.checks.lockContentions}`);
    console.log(`   Missing Indexes: ${report.checks.missingIndexes.length}`);
    console.log(`   Unused Indexes: ${report.checks.unusedIndexes.length}`);

    console.log('\n═══════════════════════════════════════════════════════════');

    // Actionable suggestions
    const fixable = report.issues.filter((i) => i.fixable);
    if (fixable.length > 0) {
      console.log(`\n💡 ${fixable.length} issue(s) can be auto-fixed`);
      console.log('   Run: ai-shell health fix --auto\n');
    }
  }
}
