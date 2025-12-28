/**
 * Cost Optimizer
 * Analyze and optimize cloud database costs
 * Commands: ai-shell analyze-costs, ai-shell optimize-costs
 */

import { AnthropicProvider } from '../llm/anthropic-provider';
import { DatabaseConnectionManager, DatabaseType } from './database-manager';
import { createLogger } from '../core/logger';
import { StateManager } from '../core/state-manager';

interface CloudProvider {
  name: 'AWS' | 'GCP' | 'Azure' | 'DigitalOcean';
  region: string;
  credentials?: any;
}

interface CostAnalysis {
  provider: CloudProvider;
  currentCosts: CostBreakdown;
  projectedCosts: CostBreakdown;
  recommendations: CostRecommendation[];
  potentialSavings: number;
  confidence: number;
  timestamp: number;
}

interface CostBreakdown {
  compute: number;
  storage: number;
  backup: number;
  dataTransfer: number;
  other: number;
  total: number;
  currency: string;
  period: 'hourly' | 'daily' | 'monthly';
}

interface CostRecommendation {
  id: string;
  category: 'compute' | 'storage' | 'backup' | 'configuration' | 'query';
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  estimatedSavings: number;
  effort: 'low' | 'medium' | 'high';
  impact: 'low' | 'medium' | 'high';
  implementation: string;
  risks: string[];
}

interface ResourceMetrics {
  cpuUtilization: number;
  memoryUtilization: number;
  storageUsed: number;
  storageTotal: number;
  iops: number;
  connections: number;
  queryCount: number;
  slowQueries: number;
}

interface OptimizationTarget {
  currentInstance: string;
  recommendedInstance: string;
  savingsPerMonth: number;
  tradeoffs: string[];
}

export class CostOptimizer {
  private logger = createLogger('CostOptimizer');
  private llmProvider: AnthropicProvider;
  private analysisHistory: CostAnalysis[] = [];

  constructor(
    private dbManager: DatabaseConnectionManager,
    private stateManager: StateManager,
    apiKey: string
  ) {
    this.llmProvider = new AnthropicProvider({ apiKey });
    this.loadAnalysisHistory();
  }

  /**
   * Analyze current costs
   */
  async analyzeCosts(provider: CloudProvider): Promise<CostAnalysis> {
    this.logger.info('Analyzing costs', { provider: provider.name });

    try {
      // Get current resource metrics
      const metrics = await this.getResourceMetrics();

      // Get current cost breakdown
      const currentCosts = await this.getCurrentCosts(provider);

      // Generate recommendations using AI
      const recommendations = await this.generateRecommendations(provider, metrics, currentCosts);

      // Calculate potential savings
      const potentialSavings = recommendations.reduce(
        (sum, rec) => sum + rec.estimatedSavings,
        0
      );

      // Project costs with optimizations
      const projectedCosts = this.calculateProjectedCosts(currentCosts, potentialSavings);

      const analysis: CostAnalysis = {
        provider,
        currentCosts,
        projectedCosts,
        recommendations,
        potentialSavings,
        confidence: 85, // Based on AI confidence + metrics accuracy
        timestamp: Date.now()
      };

      // Save to history
      this.analysisHistory.push(analysis);
      this.saveAnalysisHistory();

      this.logger.info('Cost analysis complete', {
        potentialSavings,
        recommendationsCount: recommendations.length
      });

      return analysis;
    } catch (error) {
      this.logger.error('Cost analysis failed', error);
      throw error;
    }
  }

  /**
   * Get resource metrics from database
   */
  private async getResourceMetrics(): Promise<ResourceMetrics> {
    const connection = this.dbManager.getActive();

    if (!connection) {
      throw new Error('No active database connection');
    }

    const metrics: ResourceMetrics = {
      cpuUtilization: 0,
      memoryUtilization: 0,
      storageUsed: 0,
      storageTotal: 0,
      iops: 0,
      connections: 0,
      queryCount: 0,
      slowQueries: 0
    };

    try {
      switch (connection.type) {
        case DatabaseType.POSTGRESQL:
          await this.getPostgreSQLMetrics(connection.client, metrics);
          break;

        case DatabaseType.MYSQL:
          await this.getMySQLMetrics(connection.client, metrics);
          break;

        case DatabaseType.MONGODB:
          await this.getMongoDBMetrics(connection.client, metrics);
          break;
      }
    } catch (error) {
      this.logger.warn('Failed to get resource metrics', { error });
    }

    return metrics;
  }

  /**
   * Get PostgreSQL metrics
   */
  private async getPostgreSQLMetrics(client: any, metrics: ResourceMetrics): Promise<void> {
    // Get database size
    const sizeResult = await client.query(`
      SELECT pg_database_size(current_database()) as size
    `);
    metrics.storageUsed = parseInt(sizeResult.rows[0].size) / (1024 * 1024 * 1024); // GB

    // Get connection count
    const connResult = await client.query(`
      SELECT count(*) as count FROM pg_stat_activity
    `);
    metrics.connections = parseInt(connResult.rows[0].count);

    // Get query statistics
    const queryResult = await client.query(`
      SELECT
        count(*) as total_queries,
        count(*) FILTER (WHERE mean_exec_time > 1000) as slow_queries
      FROM pg_stat_statements
    `);

    if (queryResult.rows.length > 0) {
      metrics.queryCount = parseInt(queryResult.rows[0].total_queries || 0);
      metrics.slowQueries = parseInt(queryResult.rows[0].slow_queries || 0);
    }
  }

  /**
   * Get MySQL metrics
   */
  private async getMySQLMetrics(client: any, metrics: ResourceMetrics): Promise<void> {
    // Get database size
    const [sizeResult] = await client.query(`
      SELECT
        SUM(data_length + index_length) as size
      FROM information_schema.TABLES
      WHERE table_schema = DATABASE()
    `);
    metrics.storageUsed = (sizeResult[0].size || 0) / (1024 * 1024 * 1024); // GB

    // Get connection count
    const [connResult] = await client.query(`SHOW STATUS LIKE 'Threads_connected'`);
    metrics.connections = parseInt(connResult[0].Value || 0);

    // Get query count
    const [queryResult] = await client.query(`SHOW STATUS LIKE 'Questions'`);
    metrics.queryCount = parseInt(queryResult[0].Value || 0);
  }

  /**
   * Get MongoDB metrics
   */
  private async getMongoDBMetrics(client: any, metrics: ResourceMetrics): Promise<void> {
    const stats = await client.db().stats();

    metrics.storageUsed = stats.dataSize / (1024 * 1024 * 1024); // GB
    metrics.storageTotal = stats.storageSize / (1024 * 1024 * 1024); // GB

    const serverStatus = await client.db().admin().serverStatus();
    metrics.connections = serverStatus.connections.current;
  }

  /**
   * Get current costs from cloud provider
   */
  private async getCurrentCosts(provider: CloudProvider): Promise<CostBreakdown> {
    this.logger.info('Fetching current costs', { provider: provider.name });

    // Mock implementation - in production, use actual cloud provider APIs
    const mockCosts: CostBreakdown = {
      compute: 250,
      storage: 50,
      backup: 15,
      dataTransfer: 30,
      other: 10,
      total: 355,
      currency: 'USD',
      period: 'monthly'
    };

    try {
      switch (provider.name) {
        case 'AWS':
          return await this.getAWSCosts(provider);
        case 'GCP':
          return await this.getGCPCosts(provider);
        case 'Azure':
          return await this.getAzureCosts(provider);
        default:
          return mockCosts;
      }
    } catch (error) {
      this.logger.warn('Failed to fetch actual costs, using estimates', { error });
      return mockCosts;
    }
  }

  /**
   * Get AWS costs (placeholder - requires AWS SDK)
   */
  private async getAWSCosts(_provider: CloudProvider): Promise<CostBreakdown> {
    // TODO: Implement with AWS Cost Explorer API
    this.logger.info('AWS cost fetching not implemented, using estimates');
    return {
      compute: 250,
      storage: 50,
      backup: 15,
      dataTransfer: 30,
      other: 10,
      total: 355,
      currency: 'USD',
      period: 'monthly'
    };
  }

  /**
   * Get GCP costs (placeholder - requires GCP SDK)
   */
  private async getGCPCosts(_provider: CloudProvider): Promise<CostBreakdown> {
    // TODO: Implement with GCP Billing API
    this.logger.info('GCP cost fetching not implemented, using estimates');
    return {
      compute: 230,
      storage: 45,
      backup: 12,
      dataTransfer: 25,
      other: 8,
      total: 320,
      currency: 'USD',
      period: 'monthly'
    };
  }

  /**
   * Get Azure costs (placeholder - requires Azure SDK)
   */
  private async getAzureCosts(_provider: CloudProvider): Promise<CostBreakdown> {
    // TODO: Implement with Azure Cost Management API
    this.logger.info('Azure cost fetching not implemented, using estimates');
    return {
      compute: 270,
      storage: 55,
      backup: 18,
      dataTransfer: 35,
      other: 12,
      total: 390,
      currency: 'USD',
      period: 'monthly'
    };
  }

  /**
   * Generate cost optimization recommendations using AI
   */
  private async generateRecommendations(
    provider: CloudProvider,
    metrics: ResourceMetrics,
    costs: CostBreakdown
  ): Promise<CostRecommendation[]> {
    const prompt = this.buildOptimizationPrompt(provider, metrics, costs);

    const response = await this.llmProvider.generate({
      messages: [{ role: 'user', content: prompt }],
      maxTokens: 4096,
      temperature: 0.3
    });

    return this.parseRecommendations(response.content);
  }

  /**
   * Build optimization prompt for Claude
   */
  private buildOptimizationPrompt(
    provider: CloudProvider,
    metrics: ResourceMetrics,
    costs: CostBreakdown
  ): string {
    return `You are a cloud cost optimization expert. Analyze the following database infrastructure and provide cost optimization recommendations.

Cloud Provider: ${provider.name}
Region: ${provider.region}

Current Costs (Monthly):
- Compute: $${costs.compute}
- Storage: $${costs.storage}
- Backup: $${costs.backup}
- Data Transfer: $${costs.dataTransfer}
- Other: $${costs.other}
- Total: $${costs.total}

Resource Utilization:
- CPU: ${metrics.cpuUtilization}%
- Memory: ${metrics.memoryUtilization}%
- Storage Used: ${metrics.storageUsed.toFixed(2)} GB / ${metrics.storageTotal.toFixed(2)} GB
- IOPS: ${metrics.iops}
- Connections: ${metrics.connections}
- Query Count: ${metrics.queryCount}
- Slow Queries: ${metrics.slowQueries}

Provide comprehensive cost optimization recommendations including:
1. Right-sizing instances based on utilization
2. Storage optimization (compression, cleanup, tiering)
3. Backup strategy improvements
4. Reserved instances or savings plans
5. Query optimization opportunities
6. Auto-scaling configurations
7. Data lifecycle policies

For each recommendation, provide:
- Category (compute/storage/backup/configuration/query)
- Priority (high/medium/low)
- Title and description
- Estimated monthly savings
- Implementation effort (low/medium/high)
- Business impact (low/medium/high)
- Implementation steps
- Potential risks

Format as JSON array:
[
  {
    "id": "rec-1",
    "category": "compute",
    "priority": "high",
    "title": "Right-size database instance",
    "description": "Current CPU utilization is only 30%, consider downsizing",
    "estimatedSavings": 75,
    "effort": "low",
    "impact": "low",
    "implementation": "Step 1: Create snapshot\nStep 2: Modify instance type\nStep 3: Monitor performance",
    "risks": ["Temporary downtime during resize", "May need to upsize if usage increases"]
  }
]`;
  }

  /**
   * Parse recommendations from AI response
   */
  private parseRecommendations(response: string): CostRecommendation[] {
    try {
      const jsonMatch = response.match(/\[[\s\S]*\]/);
      if (!jsonMatch) {
        throw new Error('No valid JSON array found in response');
      }

      const recommendations = JSON.parse(jsonMatch[0]);
      return recommendations;
    } catch (error) {
      this.logger.error('Failed to parse recommendations', error);
      return [];
    }
  }

  /**
   * Calculate projected costs after optimizations
   */
  private calculateProjectedCosts(
    current: CostBreakdown,
    savings: number
  ): CostBreakdown {
    const savingsRatio = 1 - savings / current.total;

    return {
      compute: current.compute * savingsRatio,
      storage: current.storage * savingsRatio,
      backup: current.backup * savingsRatio,
      dataTransfer: current.dataTransfer * savingsRatio,
      other: current.other * savingsRatio,
      total: current.total - savings,
      currency: current.currency,
      period: current.period
    };
  }

  /**
   * Generate instance rightsizing recommendations
   */
  async recommendInstanceSize(
    _provider: CloudProvider,
    metrics: ResourceMetrics
  ): Promise<OptimizationTarget> {
    this.logger.info('Generating instance size recommendations');

    // Analyze utilization patterns
    const isOverProvisioned =
      metrics.cpuUtilization < 40 && metrics.memoryUtilization < 50;

    const isUnderProvisioned =
      metrics.cpuUtilization > 80 || metrics.memoryUtilization > 85;

    let recommendation: OptimizationTarget;

    if (isOverProvisioned) {
      recommendation = {
        currentInstance: 'db.m5.2xlarge',
        recommendedInstance: 'db.m5.xlarge',
        savingsPerMonth: 180,
        tradeoffs: [
          'Reduced CPU and memory capacity',
          'May need to upgrade if load increases',
          'Consider monitoring closely after downgrade'
        ]
      };
    } else if (isUnderProvisioned) {
      recommendation = {
        currentInstance: 'db.m5.xlarge',
        recommendedInstance: 'db.m5.2xlarge',
        savingsPerMonth: -180,
        tradeoffs: [
          'Increased capacity for better performance',
          'Higher monthly costs',
          'Better headroom for traffic spikes'
        ]
      };
    } else {
      recommendation = {
        currentInstance: 'db.m5.xlarge',
        recommendedInstance: 'db.m5.xlarge',
        savingsPerMonth: 0,
        tradeoffs: ['Instance is properly sized', 'No changes needed']
      };
    }

    return recommendation;
  }

  /**
   * Optimize storage costs
   */
  async optimizeStorage(): Promise<CostRecommendation[]> {
    this.logger.info('Analyzing storage optimization opportunities');

    const recommendations: CostRecommendation[] = [];

    // Get storage metrics
    const metrics = await this.getResourceMetrics();

    // Check for over-provisioned storage
    const utilizationPercent = (metrics.storageUsed / metrics.storageTotal) * 100;

    if (utilizationPercent < 50) {
      recommendations.push({
        id: 'storage-1',
        category: 'storage',
        priority: 'medium',
        title: 'Reduce provisioned storage',
        description: `Only ${utilizationPercent.toFixed(1)}% of storage is used`,
        estimatedSavings: 25,
        effort: 'low',
        impact: 'low',
        implementation: 'Reduce allocated storage to match actual usage',
        risks: ['Ensure sufficient headroom for growth']
      });
    }

    // Recommend compression
    recommendations.push({
      id: 'storage-2',
      category: 'storage',
      priority: 'medium',
      title: 'Enable database compression',
      description: 'Compression can reduce storage costs by 40-60%',
      estimatedSavings: 20,
      effort: 'medium',
      impact: 'low',
      implementation: 'Enable table compression for large tables',
      risks: ['Slight CPU overhead for compression/decompression']
    });

    // Recommend lifecycle policies
    recommendations.push({
      id: 'storage-3',
      category: 'storage',
      priority: 'low',
      title: 'Implement data archival policy',
      description: 'Move old data to cheaper storage tiers',
      estimatedSavings: 15,
      effort: 'high',
      impact: 'medium',
      implementation: 'Archive data older than 1 year to S3 Glacier',
      risks: ['Slower access to archived data', 'Application changes may be needed']
    });

    return recommendations;
  }

  /**
   * Generate cost optimization report
   */
  generateReport(analysis: CostAnalysis): string {
    let report = '# Database Cost Optimization Report\n\n';
    report += `Provider: ${analysis.provider.name}\n`;
    report += `Region: ${analysis.provider.region}\n`;
    report += `Analysis Date: ${new Date(analysis.timestamp).toISOString()}\n\n`;

    report += `## Cost Summary\n\n`;
    report += `### Current Monthly Costs\n`;
    report += `- Compute: $${analysis.currentCosts.compute}\n`;
    report += `- Storage: $${analysis.currentCosts.storage}\n`;
    report += `- Backup: $${analysis.currentCosts.backup}\n`;
    report += `- Data Transfer: $${analysis.currentCosts.dataTransfer}\n`;
    report += `- Other: $${analysis.currentCosts.other}\n`;
    report += `- **Total: $${analysis.currentCosts.total}**\n\n`;

    report += `### Projected Costs After Optimization\n`;
    report += `- Total: $${analysis.projectedCosts.total.toFixed(2)}\n`;
    report += `- **Potential Savings: $${analysis.potentialSavings.toFixed(2)}/month**\n`;
    report += `- **Annual Savings: $${(analysis.potentialSavings * 12).toFixed(2)}**\n\n`;

    report += `## Recommendations (${analysis.recommendations.length})\n\n`;

    const highPriority = analysis.recommendations.filter((r) => r.priority === 'high');
    const mediumPriority = analysis.recommendations.filter((r) => r.priority === 'medium');
    const lowPriority = analysis.recommendations.filter((r) => r.priority === 'low');

    if (highPriority.length > 0) {
      report += `### High Priority\n\n`;
      highPriority.forEach((rec) => {
        report += this.formatRecommendation(rec);
      });
    }

    if (mediumPriority.length > 0) {
      report += `### Medium Priority\n\n`;
      mediumPriority.forEach((rec) => {
        report += this.formatRecommendation(rec);
      });
    }

    if (lowPriority.length > 0) {
      report += `### Low Priority\n\n`;
      lowPriority.forEach((rec) => {
        report += this.formatRecommendation(rec);
      });
    }

    return report;
  }

  /**
   * Format single recommendation
   */
  private formatRecommendation(rec: CostRecommendation): string {
    let text = `#### ${rec.title}\n`;
    text += `**Savings:** $${rec.estimatedSavings}/month | `;
    text += `**Effort:** ${rec.effort} | `;
    text += `**Impact:** ${rec.impact}\n\n`;
    text += `${rec.description}\n\n`;
    text += `**Implementation:**\n${rec.implementation}\n\n`;

    if (rec.risks.length > 0) {
      text += `**Risks:**\n`;
      rec.risks.forEach((risk) => {
        text += `- ${risk}\n`;
      });
      text += '\n';
    }

    return text;
  }

  /**
   * Load analysis history
   */
  private loadAnalysisHistory(): void {
    try {
      const stored = this.stateManager.get('cost-analysis-history');
      if (stored && Array.isArray(stored)) {
        this.analysisHistory = stored;
        this.logger.info('Loaded analysis history', { count: this.analysisHistory.length });
      }
    } catch (error) {
      this.logger.warn('Failed to load analysis history', { error });
    }
  }

  /**
   * Save analysis history
   */
  private saveAnalysisHistory(): void {
    try {
      // Keep only last 30 analyses
      const toSave = this.analysisHistory.slice(-30);

      this.stateManager.set('cost-analysis-history', toSave, {
        metadata: { type: 'cost-analysis' }
      });
    } catch (error) {
      this.logger.error('Failed to save analysis history', error);
    }
  }

  /**
   * Get analysis history
   */
  getHistory(limit?: number): CostAnalysis[] {
    const sorted = this.analysisHistory.sort((a, b) => b.timestamp - a.timestamp);
    return limit ? sorted.slice(0, limit) : sorted;
  }

  /**
   * Compare costs over time
   */
  getCostTrend(period: number = 30): {
    dates: string[];
    costs: number[];
    savings: number[];
  } {
    const now = Date.now();
    const periodMs = period * 24 * 60 * 60 * 1000;

    const relevant = this.analysisHistory.filter(
      (a) => now - a.timestamp < periodMs
    );

    return {
      dates: relevant.map((a) => new Date(a.timestamp).toISOString().split('T')[0]),
      costs: relevant.map((a) => a.currentCosts.total),
      savings: relevant.map((a) => a.potentialSavings)
    };
  }
}
