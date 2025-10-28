/**
 * Query Explainer - Database Query Execution Plan Analysis
 *
 * Provides detailed query execution plan analysis, performance insights,
 * and optimization suggestions for database queries.
 */

import { DatabaseConnectionManager } from './database-manager';
import { ErrorHandler } from '../core/error-handler';

/**
 * Query execution plan node
 */
export interface ExecutionPlanNode {
  nodeType: string;
  operation: string;
  table?: string;
  indexName?: string;
  cost: number;
  rows: number;
  children?: ExecutionPlanNode[];
  filters?: string[];
  joinType?: string;
  scanType?: 'sequential' | 'index' | 'bitmap' | 'full';
}

/**
 * Performance bottleneck identification
 */
export interface Bottleneck {
  type: 'sequential_scan' | 'missing_index' | 'inefficient_join' | 'large_result_set' | 'nested_loop' | 'sort' | 'temp_table';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  location: string;
  estimatedImpact: string;
  recommendation: string;
}

/**
 * Optimization suggestion
 */
export interface OptimizationSuggestion {
  type: 'index' | 'rewrite' | 'schema' | 'configuration';
  priority: 'low' | 'medium' | 'high';
  title: string;
  description: string;
  sqlExample?: string;
  estimatedImprovement: string;
}

/**
 * Complete query explanation result
 */
export interface ExplanationResult {
  query: string;
  database: string;
  databaseType: string;
  executionPlan: ExecutionPlanNode;
  estimatedCost: number;
  estimatedRows: number;
  estimatedTime: string;
  actualTime?: string;
  bottlenecks: Bottleneck[];
  suggestions: OptimizationSuggestion[];
  visualPlan: string;
  metrics: {
    indexUsage: number;
    tableScans: number;
    joins: number;
    sorts: number;
    tempTables: number;
  };
  permissions: {
    hasPermission: boolean;
    requiredPermissions: string[];
    missingPermissions?: string[];
  };
}

/**
 * Query Explainer - Analyzes database query execution plans
 */
export class QueryExplainer {
  constructor(
    private connectionManager: DatabaseConnectionManager,
    private errorHandler: ErrorHandler
  ) {}

  /**
   * Explain query execution plan with comprehensive analysis
   */
  async explain(
    query: string,
    database?: string,
    format: 'text' | 'json' = 'text'
  ): Promise<ExplanationResult> {
    const wrappedFn = this.errorHandler.wrap(
      async () => {
        const connection = this.connectionManager.getActive();
        if (!connection) {
          throw new Error('No active database connection');
        }

        const dbType = connection.type;
        const dbName = database || connection.database || 'default';

        // Get execution plan based on database type
        let executionPlan: ExecutionPlanNode;
        let estimatedCost = 0;
        let estimatedRows = 0;

        switch (dbType) {
          case 'postgresql':
            ({ executionPlan, estimatedCost, estimatedRows } = await this.explainPostgreSQL(query));
            break;
          case 'mysql':
            ({ executionPlan, estimatedCost, estimatedRows } = await this.explainMySQL(query));
            break;
          case 'sqlite':
            ({ executionPlan, estimatedCost, estimatedRows } = await this.explainSQLite(query));
            break;
          default:
            throw new Error(`Unsupported database type: ${dbType}`);
        }

        // Analyze execution plan
        const bottlenecks = this.identifyBottlenecks(executionPlan);
        const suggestions = this.generateSuggestions(executionPlan, bottlenecks);
        const metrics = this.calculateMetrics(executionPlan);
        const visualPlan = this.generateVisualPlan(executionPlan);
        const permissions = await this.checkPermissions(query);

        // Estimate execution time
        const estimatedTime = this.estimateExecutionTime(estimatedCost, estimatedRows);

        return {
          query,
          database: dbName,
          databaseType: dbType,
          executionPlan,
          estimatedCost,
          estimatedRows,
          estimatedTime,
          bottlenecks,
          suggestions,
          visualPlan,
          metrics,
          permissions
        };
      },
      {
        operation: 'explain',
        component: 'QueryExplainer'
      }
    );

    const result = await wrappedFn();
    if (!result) {
      throw new Error('Query explanation failed');
    }
    return result;
  }

  /**
   * Format explanation result for display
   */
  formatExplanation(result: ExplanationResult, format: 'text' | 'json'): string {
    if (format === 'json') {
      return JSON.stringify(result, null, 2);
    }

    // Text format
    const lines: string[] = [];

    lines.push('═══════════════════════════════════════════════════════════════');
    lines.push('                    QUERY EXECUTION PLAN                      ');
    lines.push('═══════════════════════════════════════════════════════════════');
    lines.push('');
    lines.push(`Database: ${result.database} (${result.databaseType})`);
    lines.push('');
    lines.push('Query:');
    lines.push('───────────────────────────────────────────────────────────────');
    lines.push(result.query);
    lines.push('───────────────────────────────────────────────────────────────');
    lines.push('');

    // Execution metrics
    lines.push('Execution Metrics:');
    lines.push('───────────────────────────────────────────────────────────────');
    lines.push(`  Estimated Cost:     ${result.estimatedCost.toFixed(2)}`);
    lines.push(`  Estimated Rows:     ${result.estimatedRows.toLocaleString()}`);
    lines.push(`  Estimated Time:     ${result.estimatedTime}`);
    if (result.actualTime) {
      lines.push(`  Actual Time:        ${result.actualTime}`);
    }
    lines.push('');

    // Plan metrics
    lines.push('Plan Analysis:');
    lines.push('───────────────────────────────────────────────────────────────');
    lines.push(`  Index Scans:        ${result.metrics.indexUsage}`);
    lines.push(`  Table Scans:        ${result.metrics.tableScans}`);
    lines.push(`  Joins:              ${result.metrics.joins}`);
    lines.push(`  Sorts:              ${result.metrics.sorts}`);
    lines.push(`  Temp Tables:        ${result.metrics.tempTables}`);
    lines.push('');

    // Visual execution plan
    lines.push('Visual Execution Plan:');
    lines.push('───────────────────────────────────────────────────────────────');
    lines.push(result.visualPlan);
    lines.push('');

    // Bottlenecks
    if (result.bottlenecks.length > 0) {
      lines.push('⚠️  Performance Bottlenecks:');
      lines.push('───────────────────────────────────────────────────────────────');
      result.bottlenecks.forEach((bottleneck, idx) => {
        const severity = this.getSeverityIcon(bottleneck.severity);
        lines.push(`${idx + 1}. ${severity} ${bottleneck.description}`);
        lines.push(`   Type:        ${bottleneck.type}`);
        lines.push(`   Severity:    ${bottleneck.severity.toUpperCase()}`);
        lines.push(`   Location:    ${bottleneck.location}`);
        lines.push(`   Impact:      ${bottleneck.estimatedImpact}`);
        lines.push(`   Fix:         ${bottleneck.recommendation}`);
        lines.push('');
      });
    }

    // Optimization suggestions
    if (result.suggestions.length > 0) {
      lines.push('💡 Optimization Suggestions:');
      lines.push('───────────────────────────────────────────────────────────────');
      result.suggestions.forEach((suggestion, idx) => {
        const priority = this.getPriorityIcon(suggestion.priority);
        lines.push(`${idx + 1}. ${priority} ${suggestion.title}`);
        lines.push(`   Type:        ${suggestion.type}`);
        lines.push(`   Priority:    ${suggestion.priority.toUpperCase()}`);
        lines.push(`   Description: ${suggestion.description}`);
        lines.push(`   Improvement: ${suggestion.estimatedImprovement}`);
        if (suggestion.sqlExample) {
          lines.push(`   Example SQL: ${suggestion.sqlExample}`);
        }
        lines.push('');
      });
    }

    // Permissions
    lines.push('Permissions Check:');
    lines.push('───────────────────────────────────────────────────────────────');
    if (result.permissions.hasPermission) {
      lines.push('  ✓ All required permissions granted');
    } else {
      lines.push('  ✗ Missing permissions detected:');
      result.permissions.missingPermissions?.forEach((perm) => {
        lines.push(`    - ${perm}`);
      });
    }
    lines.push('');

    lines.push('═══════════════════════════════════════════════════════════════');

    return lines.join('\n');
  }

  /**
   * Explain query for PostgreSQL
   */
  private async explainPostgreSQL(query: string): Promise<{
    executionPlan: ExecutionPlanNode;
    estimatedCost: number;
    estimatedRows: number;
  }> {
    const explainQuery = `EXPLAIN (FORMAT JSON, VERBOSE, BUFFERS) ${query}`;
    const result = await this.connectionManager.executeQuery(explainQuery);

    if (!result || result.length === 0) {
      throw new Error('Failed to get execution plan');
    }

    const plan = result[0]['QUERY PLAN']?.[0] || result[0];
    const rootPlan = plan.Plan || plan;

    return {
      executionPlan: this.parsePostgreSQLPlan(rootPlan),
      estimatedCost: rootPlan['Total Cost'] || 0,
      estimatedRows: rootPlan['Plan Rows'] || 0
    };
  }

  /**
   * Parse PostgreSQL execution plan node
   */
  private parsePostgreSQLPlan(node: any): ExecutionPlanNode {
    const planNode: ExecutionPlanNode = {
      nodeType: node['Node Type'] || 'Unknown',
      operation: node['Node Type'] || 'Unknown',
      cost: node['Total Cost'] || 0,
      rows: node['Plan Rows'] || 0,
      scanType: this.determineScanType(node['Node Type'])
    };

    if (node['Relation Name']) {
      planNode.table = node['Relation Name'];
    }

    if (node['Index Name']) {
      planNode.indexName = node['Index Name'];
    }

    if (node['Join Type']) {
      planNode.joinType = node['Join Type'];
    }

    if (node['Filter']) {
      planNode.filters = [node['Filter']];
    }

    if (node.Plans && node.Plans.length > 0) {
      planNode.children = node.Plans.map((child: any) => this.parsePostgreSQLPlan(child));
    }

    return planNode;
  }

  /**
   * Explain query for MySQL
   */
  private async explainMySQL(query: string): Promise<{
    executionPlan: ExecutionPlanNode;
    estimatedCost: number;
    estimatedRows: number;
  }> {
    const explainQuery = `EXPLAIN FORMAT=JSON ${query}`;
    const result = await this.connectionManager.executeQuery(explainQuery);

    if (!result || result.length === 0) {
      throw new Error('Failed to get execution plan');
    }

    const planData = typeof result[0].EXPLAIN === 'string'
      ? JSON.parse(result[0].EXPLAIN)
      : result[0].EXPLAIN;

    const rootPlan = planData.query_block || planData;

    return {
      executionPlan: this.parseMySQLPlan(rootPlan),
      estimatedCost: rootPlan.cost_info?.query_cost || 0,
      estimatedRows: rootPlan.cost_info?.estimated_rows || 0
    };
  }

  /**
   * Parse MySQL execution plan node
   */
  private parseMySQLPlan(node: any): ExecutionPlanNode {
    const planNode: ExecutionPlanNode = {
      nodeType: node.table?.access_type || node.operation || 'Unknown',
      operation: node.operation || node.table?.access_type || 'Unknown',
      cost: node.cost_info?.read_cost || node.cost_info?.query_cost || 0,
      rows: node.cost_info?.estimated_rows || node.rows_examined_per_scan || 0,
      scanType: this.determineScanType(node.table?.access_type)
    };

    if (node.table?.table_name) {
      planNode.table = node.table.table_name;
    }

    if (node.table?.key) {
      planNode.indexName = node.table.key;
    }

    if (node.nested_loop || node.table) {
      planNode.children = [];
      if (node.nested_loop) {
        node.nested_loop.forEach((child: any) => {
          planNode.children!.push(this.parseMySQLPlan(child));
        });
      }
    }

    return planNode;
  }

  /**
   * Explain query for SQLite
   */
  private async explainSQLite(query: string): Promise<{
    executionPlan: ExecutionPlanNode;
    estimatedCost: number;
    estimatedRows: number;
  }> {
    const explainQuery = `EXPLAIN QUERY PLAN ${query}`;
    const result = await this.connectionManager.executeQuery(explainQuery);

    if (!result || result.length === 0) {
      throw new Error('Failed to get execution plan');
    }

    // SQLite returns a simpler plan structure
    const rootNode: ExecutionPlanNode = {
      nodeType: 'Query Plan',
      operation: 'Query Plan',
      cost: 0,
      rows: 0,
      children: []
    };

    result.forEach((row: any) => {
      const detail = row.detail || row.notused || '';
      rootNode.children!.push({
        nodeType: this.parseSQLiteOperation(detail),
        operation: detail,
        cost: 0,
        rows: 0,
        scanType: this.determineScanTypeFromDetail(detail)
      });
    });

    return {
      executionPlan: rootNode,
      estimatedCost: 0, // SQLite doesn't provide cost estimates
      estimatedRows: 0
    };
  }

  /**
   * Parse SQLite operation from detail string
   */
  private parseSQLiteOperation(detail: string): string {
    if (detail.includes('SCAN')) return 'Scan';
    if (detail.includes('SEARCH')) return 'Index Search';
    if (detail.includes('USE TEMP')) return 'Temp B-Tree';
    return 'Unknown';
  }

  /**
   * Determine scan type from node type
   */
  private determineScanType(nodeType?: string): 'sequential' | 'index' | 'bitmap' | 'full' {
    if (!nodeType) return 'sequential';

    const lower = nodeType.toLowerCase();
    if (lower.includes('index') || lower.includes('idx')) return 'index';
    if (lower.includes('bitmap')) return 'bitmap';
    if (lower.includes('seq') || lower.includes('full')) return 'sequential';
    return 'sequential';
  }

  /**
   * Determine scan type from SQLite detail
   */
  private determineScanTypeFromDetail(detail: string): 'sequential' | 'index' | 'bitmap' | 'full' {
    if (detail.includes('INDEX')) return 'index';
    if (detail.includes('SCAN')) return 'sequential';
    return 'sequential';
  }

  /**
   * Identify performance bottlenecks
   */
  private identifyBottlenecks(plan: ExecutionPlanNode): Bottleneck[] {
    const bottlenecks: Bottleneck[] = [];

    const traverse = (node: ExecutionPlanNode, path: string = 'Root') => {
      // Sequential scans on large tables
      if (node.scanType === 'sequential' && node.rows > 1000) {
        bottlenecks.push({
          type: 'sequential_scan',
          severity: node.rows > 100000 ? 'critical' : node.rows > 10000 ? 'high' : 'medium',
          description: `Sequential scan on ${node.table || 'table'} examining ${node.rows.toLocaleString()} rows`,
          location: path,
          estimatedImpact: `${node.rows > 100000 ? 'Very High' : node.rows > 10000 ? 'High' : 'Medium'} - Full table scan without index`,
          recommendation: `Consider adding an index on the columns used in WHERE/JOIN clauses for ${node.table || 'this table'}`
        });
      }

      // Missing index usage
      if (node.operation.toLowerCase().includes('scan') && !node.indexName && node.table) {
        bottlenecks.push({
          type: 'missing_index',
          severity: 'medium',
          description: `Table scan on ${node.table} without index usage`,
          location: path,
          estimatedImpact: 'Medium - Query may slow down as table grows',
          recommendation: `Create an index on frequently queried columns in ${node.table}`
        });
      }

      // Nested loop joins with high row count
      const isNestedLoop = node.joinType?.toLowerCase().includes('nested') ||
                          node.nodeType?.toLowerCase().includes('nested loop');
      if (isNestedLoop && node.rows > 1000) {
        bottlenecks.push({
          type: 'nested_loop',
          severity: 'high',
          description: `Nested loop join processing ${node.rows.toLocaleString()} rows`,
          location: path,
          estimatedImpact: 'High - Nested loops are inefficient for large datasets',
          recommendation: 'Consider adding indexes on join columns or rewriting query to use hash/merge join'
        });
      }

      // Large result sets
      if (node.rows > 1000000) {
        bottlenecks.push({
          type: 'large_result_set',
          severity: 'high',
          description: `Operation producing ${node.rows.toLocaleString()} rows`,
          location: path,
          estimatedImpact: 'High - Large result set may cause memory issues',
          recommendation: 'Add LIMIT clause, add filters to reduce result set, or implement pagination'
        });
      }

      // Sorts on large datasets
      if (node.operation.toLowerCase().includes('sort') && node.rows > 100000) {
        bottlenecks.push({
          type: 'sort',
          severity: 'high',
          description: `Sorting ${node.rows.toLocaleString()} rows`,
          location: path,
          estimatedImpact: 'High - Sorting large datasets is memory and CPU intensive',
          recommendation: 'Consider adding an index on ORDER BY columns to avoid explicit sort'
        });
      }

      // Recurse into children
      if (node.children) {
        node.children.forEach((child, idx) => {
          traverse(child, `${path} → ${child.operation}[${idx}]`);
        });
      }
    };

    traverse(plan);
    return bottlenecks;
  }

  /**
   * Generate optimization suggestions
   */
  private generateSuggestions(
    plan: ExecutionPlanNode,
    bottlenecks: Bottleneck[]
  ): OptimizationSuggestion[] {
    const suggestions: OptimizationSuggestion[] = [];
    const tables = new Set<string>();

    // Collect tables from plan
    const collectTables = (node: ExecutionPlanNode) => {
      if (node.table) tables.add(node.table);
      node.children?.forEach(collectTables);
    };
    collectTables(plan);

    // Generate suggestions based on bottlenecks
    bottlenecks.forEach((bottleneck) => {
      switch (bottleneck.type) {
        case 'sequential_scan':
        case 'missing_index':
          suggestions.push({
            type: 'index',
            priority: bottleneck.severity === 'critical' ? 'high' : 'medium',
            title: 'Add indexes to improve query performance',
            description: bottleneck.recommendation,
            estimatedImprovement: bottleneck.severity === 'critical' ? '80-95%' : '50-80%'
          });
          break;

        case 'nested_loop':
          suggestions.push({
            type: 'rewrite',
            priority: 'high',
            title: 'Optimize join strategy',
            description: 'Rewrite query to use more efficient join method or add indexes on join columns',
            estimatedImprovement: '60-80%'
          });
          break;

        case 'large_result_set':
          suggestions.push({
            type: 'rewrite',
            priority: 'high',
            title: 'Reduce result set size',
            description: 'Add WHERE filters, use pagination, or implement result streaming',
            sqlExample: 'SELECT ... FROM ... WHERE ... LIMIT 100 OFFSET 0',
            estimatedImprovement: '70-90%'
          });
          break;

        case 'sort':
          suggestions.push({
            type: 'index',
            priority: 'medium',
            title: 'Add index for ORDER BY optimization',
            description: 'Create an index matching the ORDER BY clause to eliminate explicit sort',
            estimatedImprovement: '40-60%'
          });
          break;
      }
    });

    // General suggestions
    if (suggestions.length === 0) {
      suggestions.push({
        type: 'configuration',
        priority: 'low',
        title: 'Query is well optimized',
        description: 'No major performance issues detected. Consider monitoring query performance over time.',
        estimatedImprovement: 'N/A'
      });
    }

    // Deduplicate suggestions
    return Array.from(new Map(suggestions.map(s => [s.title, s])).values());
  }

  /**
   * Calculate execution plan metrics
   */
  private calculateMetrics(plan: ExecutionPlanNode): {
    indexUsage: number;
    tableScans: number;
    joins: number;
    sorts: number;
    tempTables: number;
  } {
    const metrics = {
      indexUsage: 0,
      tableScans: 0,
      joins: 0,
      sorts: 0,
      tempTables: 0
    };

    const traverse = (node: ExecutionPlanNode) => {
      if (node.scanType === 'index' || node.indexName) {
        metrics.indexUsage++;
      }

      if (node.scanType === 'sequential' || node.scanType === 'full') {
        metrics.tableScans++;
      }

      if (node.joinType || node.operation.toLowerCase().includes('join')) {
        metrics.joins++;
      }

      if (node.operation.toLowerCase().includes('sort')) {
        metrics.sorts++;
      }

      if (node.operation.toLowerCase().includes('temp') || node.operation.toLowerCase().includes('hash')) {
        metrics.tempTables++;
      }

      node.children?.forEach(traverse);
    };

    traverse(plan);
    return metrics;
  }

  /**
   * Generate visual ASCII execution plan
   */
  private generateVisualPlan(plan: ExecutionPlanNode, indent = 0): string {
    const lines: string[] = [];
    const prefix = '  '.repeat(indent);
    const connector = indent > 0 ? '└─ ' : '';

    // Node header
    const cost = plan.cost > 0 ? ` [cost: ${plan.cost.toFixed(2)}]` : '';
    const rows = plan.rows > 0 ? ` [rows: ${plan.rows.toLocaleString()}]` : '';
    lines.push(`${prefix}${connector}${plan.operation}${cost}${rows}`);

    // Node details
    if (plan.table) {
      lines.push(`${prefix}   Table: ${plan.table}`);
    }
    if (plan.indexName) {
      lines.push(`${prefix}   Index: ${plan.indexName} (${plan.scanType})`);
    } else if (plan.scanType) {
      lines.push(`${prefix}   Scan: ${plan.scanType}`);
    }
    if (plan.joinType) {
      lines.push(`${prefix}   Join: ${plan.joinType}`);
    }
    if (plan.filters && plan.filters.length > 0) {
      lines.push(`${prefix}   Filter: ${plan.filters.join(', ')}`);
    }

    // Children
    if (plan.children && plan.children.length > 0) {
      plan.children.forEach((child) => {
        lines.push(this.generateVisualPlan(child, indent + 1));
      });
    }

    return lines.join('\n');
  }

  /**
   * Estimate execution time from cost and rows
   */
  private estimateExecutionTime(cost: number, rows: number): string {
    // Simple heuristic: cost units roughly correspond to milliseconds
    // Adjust based on row count
    let timeMs = cost;

    if (rows > 1000000) {
      timeMs *= 1.5;
    } else if (rows > 100000) {
      timeMs *= 1.2;
    }

    if (timeMs < 1) return '< 1ms';
    if (timeMs < 1000) return `${Math.round(timeMs)}ms`;
    if (timeMs < 60000) return `${(timeMs / 1000).toFixed(2)}s`;
    return `${(timeMs / 60000).toFixed(2)}min`;
  }

  /**
   * Check query permissions
   */
  private async checkPermissions(query: string): Promise<{
    hasPermission: boolean;
    requiredPermissions: string[];
    missingPermissions?: string[];
  }> {
    const queryUpper = query.toUpperCase().trim();
    const requiredPermissions: string[] = [];

    // Determine required permissions
    if (queryUpper.startsWith('SELECT')) {
      requiredPermissions.push('SELECT');
    }
    if (queryUpper.startsWith('INSERT')) {
      requiredPermissions.push('INSERT');
    }
    if (queryUpper.startsWith('UPDATE')) {
      requiredPermissions.push('UPDATE');
    }
    if (queryUpper.startsWith('DELETE')) {
      requiredPermissions.push('DELETE');
    }
    if (queryUpper.includes('CREATE') || queryUpper.includes('ALTER') || queryUpper.includes('DROP')) {
      requiredPermissions.push('DDL');
    }

    // For now, assume all permissions are granted
    // In production, check actual database permissions
    return {
      hasPermission: true,
      requiredPermissions
    };
  }

  /**
   * Get severity icon for display
   */
  private getSeverityIcon(severity: string): string {
    switch (severity) {
      case 'critical': return '🔴';
      case 'high': return '🟠';
      case 'medium': return '🟡';
      case 'low': return '🟢';
      default: return '⚪';
    }
  }

  /**
   * Get priority icon for display
   */
  private getPriorityIcon(priority: string): string {
    switch (priority) {
      case 'high': return '🔺';
      case 'medium': return '🔸';
      case 'low': return '🔹';
      default: return '⚪';
    }
  }
}
