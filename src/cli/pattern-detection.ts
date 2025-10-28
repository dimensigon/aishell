/**
 * Advanced Pattern Detection System
 * ML-based query analysis with clustering, anomaly detection, and security monitoring
 *
 * Features:
 * - Query pattern recognition using clustering
 * - Anomaly detection for unusual queries
 * - Performance pattern analysis
 * - Security pattern detection (SQL injection, suspicious behavior)
 * - Usage pattern insights (peak hours, common operations)
 * - Automatic recommendation generation
 * - Pattern learning from query history
 * - Integration with Claude AI for advanced analysis
 */

import { EventEmitter } from 'eventemitter3';
import { StateManager } from '../core/state-manager';
import { AnthropicProvider } from '../llm/anthropic-provider';
import { QueryLogger, QueryLog } from './query-logger';
import { createLogger } from '../core/logger';

/**
 * Pattern detection configuration
 */
export interface PatternDetectionConfig {
  minSamplesForPattern?: number;
  anomalyThreshold?: number;
  clusteringEpsilon?: number;
  securityScanEnabled?: boolean;
  learningEnabled?: boolean;
  aiAnalysisEnabled?: boolean;
}

/**
 * Query pattern types
 */
export enum PatternType {
  STRUCTURAL = 'structural',
  TEMPORAL = 'temporal',
  PERFORMANCE = 'performance',
  SECURITY = 'security',
  USAGE = 'usage',
  ANOMALY = 'anomaly'
}

/**
 * Pattern cluster
 */
export interface PatternCluster {
  id: string;
  type: PatternType;
  queries: string[];
  centroid: QueryFeatures;
  frequency: number;
  avgPerformance: number;
  firstSeen: number;
  lastSeen: number;
  characteristics: string[];
  recommendations?: string[];
}

/**
 * Query features for ML analysis
 */
export interface QueryFeatures {
  length: number;
  complexity: number;
  joinCount: number;
  subqueryCount: number;
  whereClauseCount: number;
  aggregateCount: number;
  tableCount: number;
  selectStarUsed: boolean;
  hasIndex: boolean;
  hasDistinct: boolean;
  hasUnion: boolean;
  hasGroupBy: boolean;
  hasOrderBy: boolean;
  hasLimit: boolean;
  avgExecutionTime: number;
  executionVariance: number;
  errorRate: number;
}

/**
 * Anomaly detection result
 */
export interface Anomaly {
  query: string;
  timestamp: number;
  anomalyScore: number;
  reasons: string[];
  severity: 'low' | 'medium' | 'high' | 'critical';
  type: 'performance' | 'security' | 'structural' | 'behavioral';
  recommendation?: string;
}

/**
 * Security threat
 */
export interface SecurityThreat {
  query: string;
  timestamp: number;
  threatType: 'sql_injection' | 'data_exfiltration' | 'privilege_escalation' | 'dos_attempt';
  confidence: number;
  indicators: string[];
  recommendation: string;
}

/**
 * Performance pattern
 */
export interface PerformancePattern {
  description: string;
  queriesAffected: number;
  avgImpact: number;
  trend: 'improving' | 'degrading' | 'stable';
  recommendations: string[];
  examples: string[];
}

/**
 * Usage pattern
 */
export interface UsagePattern {
  peakHours: Array<{ hour: number; count: number; avgDuration: number }>;
  commonOperations: Array<{ operation: string; count: number; percentage: number }>;
  userBehavior: {
    averageSessionLength: number;
    queriesPerSession: number;
    preferredQueryTypes: string[];
  };
  accessPatterns: Array<{ table: string; accessCount: number; operations: string[] }>;
}

/**
 * Pattern insights
 */
export interface PatternInsights {
  summary: {
    totalPatterns: number;
    clustersFound: number;
    anomaliesDetected: number;
    securityThreats: number;
    performanceIssues: number;
  };
  patterns: PatternCluster[];
  anomalies: Anomaly[];
  securityThreats: SecurityThreat[];
  performancePatterns: PerformancePattern[];
  usagePatterns: UsagePattern;
  recommendations: string[];
  confidence: number;
  analysisTimestamp: number;
}

/**
 * Pattern export data
 */
export interface PatternExport {
  version: string;
  exportDate: number;
  metadata: {
    totalQueries: number;
    dateRange: { start: number; end: number };
    analysisConfig: PatternDetectionConfig;
  };
  patterns: PatternCluster[];
  anomalies: Anomaly[];
  insights: PatternInsights;
  mlModel?: {
    clusters: any[];
    parameters: Record<string, any>;
  };
}

/**
 * Pattern detection events
 */
export interface PatternDetectionEvents {
  patternDiscovered: (pattern: PatternCluster) => void;
  anomalyDetected: (anomaly: Anomaly) => void;
  securityThreat: (threat: SecurityThreat) => void;
  analysisComplete: (insights: PatternInsights) => void;
}

/**
 * Advanced Pattern Detection System
 */
export class PatternDetector extends EventEmitter<PatternDetectionEvents> {
  private logger = createLogger('PatternDetector');
  private clusters: Map<string, PatternCluster> = new Map();
  private anomalyHistory: Anomaly[] = [];
  private securityThreats: SecurityThreat[] = [];
  private llmProvider?: AnthropicProvider;
  private learningModel: Map<string, number> = new Map();

  constructor(
    private stateManager: StateManager,
    private queryLogger: QueryLogger,
    private config: PatternDetectionConfig = {},
    apiKey?: string
  ) {
    super();

    // Set defaults
    this.config = {
      minSamplesForPattern: 5,
      anomalyThreshold: 0.7,
      clusteringEpsilon: 0.3,
      securityScanEnabled: true,
      learningEnabled: true,
      aiAnalysisEnabled: !!apiKey,
      ...config
    };

    if (apiKey && this.config.aiAnalysisEnabled) {
      this.llmProvider = new AnthropicProvider({ apiKey });
    }

    this.loadState();
  }

  /**
   * Analyze patterns from query history
   */
  async analyze(options: { period?: number; types?: PatternType[] } = {}): Promise<PatternInsights> {
    this.logger.info('Starting pattern analysis', options);

    const period = options.period || 7; // days
    const since = Date.now() - period * 24 * 60 * 60 * 1000;

    // Get query logs
    const history = await this.queryLogger.getHistory(10000);
    const recentLogs = history.logs.filter(log => log.timestamp >= since);

    if (recentLogs.length === 0) {
      this.logger.warn('No query logs found for analysis');
      return this.getEmptyInsights();
    }

    this.logger.info(`Analyzing ${recentLogs.length} queries from last ${period} days`);

    // Extract features from queries
    const features = recentLogs.map(log => this.extractFeatures(log));

    // Perform clustering
    const clusters = await this.performClustering(features, recentLogs);

    // Detect anomalies
    const anomalies = await this.detectAnomalies(recentLogs, clusters);

    // Detect security threats
    const threats = this.config.securityScanEnabled
      ? await this.detectSecurityThreats(recentLogs)
      : [];

    // Analyze performance patterns
    const performancePatterns = await this.analyzePerformancePatterns(recentLogs);

    // Analyze usage patterns
    const usagePatterns = await this.analyzeUsagePatterns(recentLogs);

    // Generate recommendations using AI
    const recommendations = this.config.aiAnalysisEnabled
      ? await this.generateRecommendations(clusters, anomalies, threats)
      : this.generateBasicRecommendations(clusters, anomalies);

    // Build insights
    const insights: PatternInsights = {
      summary: {
        totalPatterns: clusters.length,
        clustersFound: clusters.length,
        anomaliesDetected: anomalies.length,
        securityThreats: threats.length,
        performanceIssues: performancePatterns.filter(p => p.trend === 'degrading').length
      },
      patterns: clusters,
      anomalies,
      securityThreats: threats,
      performancePatterns,
      usagePatterns,
      recommendations,
      confidence: this.calculateConfidence(recentLogs.length, clusters.length),
      analysisTimestamp: Date.now()
    };

    // Emit events
    this.emit('analysisComplete', insights);

    // Store in state
    this.stateManager.set('pattern-insights:latest', insights, {
      metadata: { type: 'pattern-insights' }
    });

    // Learn from patterns if enabled
    if (this.config.learningEnabled) {
      await this.updateLearningModel(clusters, anomalies);
    }

    this.logger.info('Pattern analysis complete', {
      patterns: clusters.length,
      anomalies: anomalies.length,
      threats: threats.length
    });

    return insights;
  }

  /**
   * Generate pattern report
   */
  async report(options: {
    type?: PatternType;
    format?: 'summary' | 'detailed' | 'technical';
    includeRecommendations?: boolean;
  } = {}): Promise<string> {
    const insights = this.stateManager.get('pattern-insights:latest') as PatternInsights;

    if (!insights) {
      return 'No pattern analysis available. Run "patterns analyze" first.';
    }

    const format = options.format || 'summary';
    const includeRec = options.includeRecommendations !== false;

    let report = '';

    // Header
    report += '═══════════════════════════════════════════════════════════\n';
    report += '           PATTERN DETECTION ANALYSIS REPORT\n';
    report += '═══════════════════════════════════════════════════════════\n\n';
    report += `Analysis Date: ${new Date(insights.analysisTimestamp).toISOString()}\n`;
    report += `Confidence Level: ${(insights.confidence * 100).toFixed(1)}%\n\n`;

    // Summary
    report += '📊 SUMMARY\n';
    report += '─────────────────────────────────────────────────────────\n';
    report += `Total Patterns: ${insights.summary.totalPatterns}\n`;
    report += `Clusters Found: ${insights.summary.clustersFound}\n`;
    report += `Anomalies Detected: ${insights.summary.anomaliesDetected}\n`;
    report += `Security Threats: ${insights.summary.securityThreats}\n`;
    report += `Performance Issues: ${insights.summary.performanceIssues}\n\n`;

    // Filter by type if specified
    const patterns = options.type
      ? insights.patterns.filter(p => p.type === options.type)
      : insights.patterns;

    // Patterns
    if (patterns.length > 0) {
      report += '🔍 DISCOVERED PATTERNS\n';
      report += '─────────────────────────────────────────────────────────\n';

      for (const pattern of patterns.slice(0, format === 'summary' ? 5 : 20)) {
        report += `\n[${pattern.type.toUpperCase()}] ${pattern.id}\n`;
        report += `  Frequency: ${pattern.frequency} queries\n`;
        report += `  Avg Performance: ${pattern.avgPerformance.toFixed(2)}ms\n`;
        report += `  Characteristics: ${pattern.characteristics.join(', ')}\n`;

        if (format !== 'summary' && pattern.recommendations) {
          report += `  Recommendations:\n`;
          pattern.recommendations.forEach(rec => {
            report += `    • ${rec}\n`;
          });
        }
      }
      report += '\n';
    }

    // Anomalies
    if (insights.anomalies.length > 0) {
      report += '⚠️  ANOMALIES DETECTED\n';
      report += '─────────────────────────────────────────────────────────\n';

      const sortedAnomalies = [...insights.anomalies]
        .sort((a, b) => b.anomalyScore - a.anomalyScore)
        .slice(0, format === 'summary' ? 3 : 10);

      for (const anomaly of sortedAnomalies) {
        report += `\n[${anomaly.severity.toUpperCase()}] ${anomaly.type}\n`;
        report += `  Score: ${anomaly.anomalyScore.toFixed(2)}\n`;
        report += `  Query: ${anomaly.query.substring(0, 80)}...\n`;
        report += `  Reasons: ${anomaly.reasons.join(', ')}\n`;

        if (anomaly.recommendation) {
          report += `  ➜ ${anomaly.recommendation}\n`;
        }
      }
      report += '\n';
    }

    // Security Threats
    if (insights.securityThreats.length > 0) {
      report += '🔒 SECURITY THREATS\n';
      report += '─────────────────────────────────────────────────────────\n';

      for (const threat of insights.securityThreats.slice(0, format === 'summary' ? 3 : 10)) {
        report += `\n[${threat.threatType.toUpperCase()}] Confidence: ${(threat.confidence * 100).toFixed(1)}%\n`;
        report += `  Indicators: ${threat.indicators.join(', ')}\n`;
        report += `  ➜ ${threat.recommendation}\n`;
      }
      report += '\n';
    }

    // Performance Patterns
    if (insights.performancePatterns.length > 0 && format !== 'summary') {
      report += '⚡ PERFORMANCE PATTERNS\n';
      report += '─────────────────────────────────────────────────────────\n';

      for (const perf of insights.performancePatterns) {
        report += `\n${perf.description}\n`;
        report += `  Trend: ${perf.trend.toUpperCase()}\n`;
        report += `  Queries Affected: ${perf.queriesAffected}\n`;
        report += `  Avg Impact: ${perf.avgImpact.toFixed(2)}ms\n`;

        if (perf.recommendations.length > 0) {
          report += `  Recommendations:\n`;
          perf.recommendations.forEach(rec => {
            report += `    • ${rec}\n`;
          });
        }
      }
      report += '\n';
    }

    // Usage Patterns
    if (format !== 'summary') {
      report += '📈 USAGE PATTERNS\n';
      report += '─────────────────────────────────────────────────────────\n';
      report += `Peak Hours: ${insights.usagePatterns.peakHours.slice(0, 3).map(h => `${h.hour}:00 (${h.count} queries)`).join(', ')}\n`;
      report += `Common Operations: ${insights.usagePatterns.commonOperations.slice(0, 3).map(o => `${o.operation} (${o.percentage.toFixed(1)}%)`).join(', ')}\n`;
      report += `Avg Session Length: ${insights.usagePatterns.userBehavior.averageSessionLength.toFixed(1)}min\n`;
      report += `Queries per Session: ${insights.usagePatterns.userBehavior.queriesPerSession.toFixed(1)}\n\n`;
    }

    // Recommendations
    if (includeRec && insights.recommendations.length > 0) {
      report += '💡 RECOMMENDATIONS\n';
      report += '─────────────────────────────────────────────────────────\n';
      insights.recommendations.forEach((rec, idx) => {
        report += `${idx + 1}. ${rec}\n`;
      });
      report += '\n';
    }

    report += '═══════════════════════════════════════════════════════════\n';

    return report;
  }

  /**
   * Learn from query patterns
   */
  async learn(): Promise<void> {
    this.logger.info('Starting pattern learning');

    const insights = this.stateManager.get('pattern-insights:latest') as PatternInsights;

    if (!insights) {
      throw new Error('No pattern insights available. Run analysis first.');
    }

    // Update learning model
    for (const pattern of insights.patterns) {
      const key = this.getPatternSignature(pattern);
      const currentWeight = this.learningModel.get(key) || 0;
      this.learningModel.set(key, currentWeight + pattern.frequency);
    }

    // Learn from anomalies
    for (const anomaly of insights.anomalies) {
      const key = `anomaly:${anomaly.type}:${this.hashQuery(anomaly.query)}`;
      const currentWeight = this.learningModel.get(key) || 0;
      this.learningModel.set(key, currentWeight + anomaly.anomalyScore);
    }

    // Train AI model if available
    if (this.llmProvider && this.config.aiAnalysisEnabled) {
      await this.trainAIModel(insights);
    }

    // Save learning state
    this.saveState();

    this.logger.info('Pattern learning complete', {
      patternsLearned: this.learningModel.size
    });
  }

  /**
   * Export patterns to file
   */
  async export(filepath: string, format: 'json' | 'csv' = 'json'): Promise<void> {
    const insights = this.stateManager.get('pattern-insights:latest') as PatternInsights;

    if (!insights) {
      throw new Error('No pattern insights available. Run analysis first.');
    }

    const history = await this.queryLogger.getHistory(10000);

    const exportData: PatternExport = {
      version: '1.0.0',
      exportDate: Date.now(),
      metadata: {
        totalQueries: history.total,
        dateRange: {
          start: history.logs[history.logs.length - 1]?.timestamp || 0,
          end: history.logs[0]?.timestamp || 0
        },
        analysisConfig: this.config
      },
      patterns: insights.patterns,
      anomalies: insights.anomalies,
      insights,
      mlModel: {
        clusters: Array.from(this.clusters.values()),
        parameters: Object.fromEntries(this.learningModel.entries())
      }
    };

    const fs = await import('fs/promises');
    const path = await import('path');

    await fs.mkdir(path.dirname(filepath), { recursive: true });

    if (format === 'json') {
      await fs.writeFile(filepath, JSON.stringify(exportData, null, 2), 'utf-8');
    } else {
      // CSV export
      const csvContent = this.convertToCSV(exportData);
      await fs.writeFile(filepath, csvContent, 'utf-8');
    }

    this.logger.info('Patterns exported', { filepath, format });
  }

  /**
   * Get pattern insights
   */
  async getInsights(): Promise<PatternInsights> {
    const insights = this.stateManager.get('pattern-insights:latest') as PatternInsights;

    if (!insights) {
      throw new Error('No pattern insights available. Run analysis first.');
    }

    return insights;
  }

  /**
   * Clear pattern data
   */
  clearPatterns(): void {
    this.clusters.clear();
    this.anomalyHistory = [];
    this.securityThreats = [];
    this.learningModel.clear();
    this.stateManager.delete('pattern-insights:latest');
    this.saveState();
    this.logger.info('Pattern data cleared');
  }

  // Private Methods

  /**
   * Extract ML features from query log
   */
  private extractFeatures(log: QueryLog): QueryFeatures {
    const query = log.query.toLowerCase();

    return {
      length: query.length,
      complexity: this.calculateComplexity(query),
      joinCount: (query.match(/\bjoin\b/g) || []).length,
      subqueryCount: (query.match(/\(select\b/g) || []).length,
      whereClauseCount: (query.match(/\bwhere\b/g) || []).length,
      aggregateCount: (query.match(/\b(count|sum|avg|min|max)\b/g) || []).length,
      tableCount: this.estimateTableCount(query),
      selectStarUsed: query.includes('select *'),
      hasIndex: query.includes('index'),
      hasDistinct: query.includes('distinct'),
      hasUnion: query.includes('union'),
      hasGroupBy: query.includes('group by'),
      hasOrderBy: query.includes('order by'),
      hasLimit: query.includes('limit'),
      avgExecutionTime: log.duration,
      executionVariance: 0, // Calculated from multiple executions
      errorRate: log.result?.error ? 1 : 0
    };
  }

  /**
   * Calculate query complexity score
   */
  private calculateComplexity(query: string): number {
    let score = 0;

    // Base complexity from length
    score += Math.min(query.length / 100, 10);

    // Join complexity
    score += (query.match(/\bjoin\b/g) || []).length * 2;

    // Subquery complexity
    score += (query.match(/\(select\b/g) || []).length * 3;

    // Aggregate complexity
    score += (query.match(/\b(count|sum|avg|min|max)\b/g) || []).length;

    // Union complexity
    score += (query.match(/\bunion\b/g) || []).length * 2;

    return score;
  }

  /**
   * Estimate table count in query
   */
  private estimateTableCount(query: string): number {
    const fromMatch = query.match(/\bfrom\s+(\w+)/g);
    const joinMatch = query.match(/\bjoin\s+(\w+)/g);

    return (fromMatch?.length || 0) + (joinMatch?.length || 0);
  }

  /**
   * Perform DBSCAN clustering on query features
   */
  private async performClustering(
    features: QueryFeatures[],
    logs: QueryLog[]
  ): Promise<PatternCluster[]> {
    const epsilon = this.config.clusteringEpsilon!;
    const minSamples = this.config.minSamplesForPattern!;

    const clusters: PatternCluster[] = [];
    const visited = new Set<number>();
    const clustered = new Set<number>();

    for (let i = 0; i < features.length; i++) {
      if (visited.has(i)) continue;

      visited.add(i);
      const neighbors = this.getNeighbors(i, features, epsilon);

      if (neighbors.length < minSamples) continue;

      // Create new cluster
      const clusterQueries: string[] = [];
      const clusterIndices: number[] = [];

      const expandCluster = (pointIdx: number) => {
        if (clustered.has(pointIdx)) return;

        clustered.add(pointIdx);
        clusterQueries.push(logs[pointIdx].query);
        clusterIndices.push(pointIdx);

        const pointNeighbors = this.getNeighbors(pointIdx, features, epsilon);

        for (const neighborIdx of pointNeighbors) {
          if (!visited.has(neighborIdx)) {
            visited.add(neighborIdx);
            if (pointNeighbors.length >= minSamples) {
              expandCluster(neighborIdx);
            }
          }
        }
      };

      expandCluster(i);

      if (clusterQueries.length >= minSamples) {
        const centroid = this.calculateCentroid(clusterIndices.map(idx => features[idx]));
        const type = this.classifyPatternType(centroid, clusterQueries);

        const cluster: PatternCluster = {
          id: `cluster_${clusters.length + 1}`,
          type,
          queries: clusterQueries,
          centroid,
          frequency: clusterQueries.length,
          avgPerformance: clusterIndices.reduce((sum, idx) => sum + logs[idx].duration, 0) / clusterIndices.length,
          firstSeen: Math.min(...clusterIndices.map(idx => logs[idx].timestamp)),
          lastSeen: Math.max(...clusterIndices.map(idx => logs[idx].timestamp)),
          characteristics: this.extractCharacteristics(centroid, clusterQueries)
        };

        clusters.push(cluster);
        this.clusters.set(cluster.id, cluster);
        this.emit('patternDiscovered', cluster);
      }
    }

    this.logger.info(`Clustering complete: ${clusters.length} clusters found`);
    return clusters;
  }

  /**
   * Get neighbors within epsilon distance
   */
  private getNeighbors(index: number, features: QueryFeatures[], epsilon: number): number[] {
    const neighbors: number[] = [];

    for (let i = 0; i < features.length; i++) {
      if (i === index) continue;

      const distance = this.calculateDistance(features[index], features[i]);
      if (distance <= epsilon) {
        neighbors.push(i);
      }
    }

    return neighbors;
  }

  /**
   * Calculate distance between two feature vectors
   */
  private calculateDistance(f1: QueryFeatures, f2: QueryFeatures): number {
    // Normalized Euclidean distance
    const weights = {
      complexity: 0.3,
      joinCount: 0.2,
      subqueryCount: 0.2,
      avgExecutionTime: 0.15,
      tableCount: 0.15
    };

    let distance = 0;

    distance += weights.complexity * Math.pow((f1.complexity - f2.complexity) / 100, 2);
    distance += weights.joinCount * Math.pow(f1.joinCount - f2.joinCount, 2);
    distance += weights.subqueryCount * Math.pow(f1.subqueryCount - f2.subqueryCount, 2);
    distance += weights.avgExecutionTime * Math.pow((f1.avgExecutionTime - f2.avgExecutionTime) / 1000, 2);
    distance += weights.tableCount * Math.pow(f1.tableCount - f2.tableCount, 2);

    return Math.sqrt(distance);
  }

  /**
   * Calculate cluster centroid
   */
  private calculateCentroid(features: QueryFeatures[]): QueryFeatures {
    const n = features.length;

    return {
      length: features.reduce((sum, f) => sum + f.length, 0) / n,
      complexity: features.reduce((sum, f) => sum + f.complexity, 0) / n,
      joinCount: features.reduce((sum, f) => sum + f.joinCount, 0) / n,
      subqueryCount: features.reduce((sum, f) => sum + f.subqueryCount, 0) / n,
      whereClauseCount: features.reduce((sum, f) => sum + f.whereClauseCount, 0) / n,
      aggregateCount: features.reduce((sum, f) => sum + f.aggregateCount, 0) / n,
      tableCount: features.reduce((sum, f) => sum + f.tableCount, 0) / n,
      selectStarUsed: features.filter(f => f.selectStarUsed).length > n / 2,
      hasIndex: features.filter(f => f.hasIndex).length > n / 2,
      hasDistinct: features.filter(f => f.hasDistinct).length > n / 2,
      hasUnion: features.filter(f => f.hasUnion).length > n / 2,
      hasGroupBy: features.filter(f => f.hasGroupBy).length > n / 2,
      hasOrderBy: features.filter(f => f.hasOrderBy).length > n / 2,
      hasLimit: features.filter(f => f.hasLimit).length > n / 2,
      avgExecutionTime: features.reduce((sum, f) => sum + f.avgExecutionTime, 0) / n,
      executionVariance: this.calculateVariance(features.map(f => f.avgExecutionTime)),
      errorRate: features.reduce((sum, f) => sum + f.errorRate, 0) / n
    };
  }

  /**
   * Calculate variance
   */
  private calculateVariance(values: number[]): number {
    const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
    return values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
  }

  /**
   * Classify pattern type based on features
   */
  private classifyPatternType(centroid: QueryFeatures, queries: string[]): PatternType {
    // High complexity suggests structural pattern
    if (centroid.complexity > 20 || centroid.subqueryCount > 2) {
      return PatternType.STRUCTURAL;
    }

    // High execution time suggests performance pattern
    if (centroid.avgExecutionTime > 1000) {
      return PatternType.PERFORMANCE;
    }

    // High error rate suggests anomaly
    if (centroid.errorRate > 0.5) {
      return PatternType.ANOMALY;
    }

    // Default to usage pattern
    return PatternType.USAGE;
  }

  /**
   * Extract pattern characteristics
   */
  private extractCharacteristics(centroid: QueryFeatures, queries: string[]): string[] {
    const chars: string[] = [];

    if (centroid.complexity > 15) chars.push('High complexity');
    if (centroid.joinCount > 2) chars.push('Multiple joins');
    if (centroid.subqueryCount > 0) chars.push('Contains subqueries');
    if (centroid.selectStarUsed) chars.push('Uses SELECT *');
    if (centroid.avgExecutionTime > 500) chars.push('Slow execution');
    if (centroid.hasGroupBy) chars.push('Aggregation query');
    if (centroid.errorRate > 0) chars.push('Has errors');

    return chars;
  }

  /**
   * Detect anomalies using isolation forest-like approach
   */
  private async detectAnomalies(
    logs: QueryLog[],
    clusters: PatternCluster[]
  ): Promise<Anomaly[]> {
    const anomalies: Anomaly[] = [];
    const threshold = this.config.anomalyThreshold!;

    for (const log of logs) {
      const features = this.extractFeatures(log);
      const anomalyScore = this.calculateAnomalyScore(features, clusters);

      if (anomalyScore >= threshold) {
        const anomaly: Anomaly = {
          query: log.query,
          timestamp: log.timestamp,
          anomalyScore,
          reasons: this.identifyAnomalyReasons(features, clusters),
          severity: this.calculateSeverity(anomalyScore),
          type: this.classifyAnomalyType(features, log),
          recommendation: await this.getAnomalyRecommendation(log.query, features)
        };

        anomalies.push(anomaly);
        this.anomalyHistory.push(anomaly);
        this.emit('anomalyDetected', anomaly);
      }
    }

    this.logger.info(`Anomaly detection complete: ${anomalies.length} anomalies found`);
    return anomalies;
  }

  /**
   * Calculate anomaly score
   */
  private calculateAnomalyScore(features: QueryFeatures, clusters: PatternCluster[]): number {
    if (clusters.length === 0) return 0;

    // Calculate minimum distance to any cluster
    const distances = clusters.map(cluster =>
      this.calculateDistance(features, cluster.centroid)
    );

    const minDistance = Math.min(...distances);

    // Normalize to 0-1 range
    return Math.min(minDistance / 2, 1);
  }

  /**
   * Identify anomaly reasons
   */
  private identifyAnomalyReasons(features: QueryFeatures, clusters: PatternCluster[]): string[] {
    const reasons: string[] = [];

    if (features.complexity > 50) reasons.push('Extremely high complexity');
    if (features.avgExecutionTime > 5000) reasons.push('Very slow execution');
    if (features.joinCount > 5) reasons.push('Excessive joins');
    if (features.subqueryCount > 3) reasons.push('Multiple nested subqueries');
    if (features.errorRate > 0.8) reasons.push('High error rate');

    // Check if far from all clusters
    const avgDistance = clusters.reduce((sum, c) =>
      sum + this.calculateDistance(features, c.centroid), 0
    ) / clusters.length;

    if (avgDistance > 1) reasons.push('Unusual query pattern');

    return reasons.length > 0 ? reasons : ['Deviates from normal patterns'];
  }

  /**
   * Calculate severity level
   */
  private calculateSeverity(score: number): 'low' | 'medium' | 'high' | 'critical' {
    if (score >= 0.9) return 'critical';
    if (score >= 0.8) return 'high';
    if (score >= 0.7) return 'medium';
    return 'low';
  }

  /**
   * Classify anomaly type
   */
  private classifyAnomalyType(
    features: QueryFeatures,
    log: QueryLog
  ): 'performance' | 'security' | 'structural' | 'behavioral' {
    if (features.avgExecutionTime > 3000) return 'performance';
    if (this.hasSecurityIndicators(log.query)) return 'security';
    if (features.complexity > 40) return 'structural';
    return 'behavioral';
  }

  /**
   * Check for security indicators
   */
  private hasSecurityIndicators(query: string): boolean {
    const lowerQuery = query.toLowerCase();

    const indicators = [
      /union.*select/,
      /;\s*drop/,
      /;\s*delete/,
      /exec\s*\(/,
      /sleep\s*\(/,
      /benchmark\s*\(/,
      /or\s+1\s*=\s*1/,
      /'\s*or\s*'.*'\s*=\s*'/
    ];

    return indicators.some(pattern => pattern.test(lowerQuery));
  }

  /**
   * Get anomaly recommendation
   */
  private async getAnomalyRecommendation(query: string, features: QueryFeatures): Promise<string> {
    if (this.llmProvider && this.config.aiAnalysisEnabled) {
      try {
        const response = await this.llmProvider.generate({
          messages: [{
            role: 'user',
            content: `Analyze this anomalous SQL query and provide a brief recommendation:\n\n${query}\n\nComplexity: ${features.complexity}, Execution time: ${features.avgExecutionTime}ms`
          }],
          maxTokens: 200,
          temperature: 0.3
        });

        return response.content.trim();
      } catch (error) {
        this.logger.error('Failed to get AI recommendation', error);
      }
    }

    return 'Review query for potential optimization or security issues';
  }

  /**
   * Detect security threats
   */
  private async detectSecurityThreats(logs: QueryLog[]): Promise<SecurityThreat[]> {
    const threats: SecurityThreat[] = [];

    for (const log of logs) {
      const threat = this.analyzeSecurity(log);
      if (threat) {
        threats.push(threat);
        this.securityThreats.push(threat);
        this.emit('securityThreat', threat);
      }
    }

    this.logger.info(`Security scan complete: ${threats.length} threats found`);
    return threats;
  }

  /**
   * Analyze query for security threats
   */
  private analyzeSecurity(log: QueryLog): SecurityThreat | null {
    const query = log.query.toLowerCase();

    // SQL injection patterns
    if (this.detectSQLInjection(query)) {
      return {
        query: log.query,
        timestamp: log.timestamp,
        threatType: 'sql_injection',
        confidence: 0.85,
        indicators: this.getSQLInjectionIndicators(query),
        recommendation: 'Use parameterized queries and input validation'
      };
    }

    // Data exfiltration patterns
    if (this.detectDataExfiltration(query)) {
      return {
        query: log.query,
        timestamp: log.timestamp,
        threatType: 'data_exfiltration',
        confidence: 0.75,
        indicators: ['Large SELECT query', 'No WHERE clause'],
        recommendation: 'Review query necessity and implement result limits'
      };
    }

    // Privilege escalation
    if (this.detectPrivilegeEscalation(query)) {
      return {
        query: log.query,
        timestamp: log.timestamp,
        threatType: 'privilege_escalation',
        confidence: 0.9,
        indicators: ['GRANT statement', 'User modification'],
        recommendation: 'Audit user permissions and restrict admin operations'
      };
    }

    // DoS attempt
    if (this.detectDoSAttempt(query)) {
      return {
        query: log.query,
        timestamp: log.timestamp,
        threatType: 'dos_attempt',
        confidence: 0.7,
        indicators: ['Resource-intensive operation', 'No limits'],
        recommendation: 'Implement query timeout and resource limits'
      };
    }

    return null;
  }

  /**
   * Detect SQL injection
   */
  private detectSQLInjection(query: string): boolean {
    const patterns = [
      /union.*select/,
      /;\s*drop/,
      /;\s*delete\s+from/,
      /exec\s*\(/,
      /or\s+['"]?\d+['"]?\s*=\s*['"]?\d+['"]?/,
      /'\s*or\s*'.*'\s*=\s*'/,
      /--\s*$/,
      /\/\*.*\*\//
    ];

    return patterns.some(p => p.test(query));
  }

  /**
   * Get SQL injection indicators
   */
  private getSQLInjectionIndicators(query: string): string[] {
    const indicators: string[] = [];

    if (/union.*select/.test(query)) indicators.push('UNION injection');
    if (/;\s*drop/.test(query)) indicators.push('SQL command stacking');
    if (/or\s+\d+\s*=\s*\d+/.test(query)) indicators.push('Tautology');
    if (/--\s*$/.test(query)) indicators.push('Comment injection');

    return indicators;
  }

  /**
   * Detect data exfiltration
   */
  private detectDataExfiltration(query: string): boolean {
    return (
      query.includes('select *') &&
      !query.includes('where') &&
      !query.includes('limit')
    );
  }

  /**
   * Detect privilege escalation
   */
  private detectPrivilegeEscalation(query: string): boolean {
    return (
      query.includes('grant') ||
      query.includes('revoke') ||
      (query.includes('update') && query.includes('user'))
    );
  }

  /**
   * Detect DoS attempt
   */
  private detectDoSAttempt(query: string): boolean {
    return (
      /sleep\s*\(/.test(query) ||
      /benchmark\s*\(/.test(query) ||
      (query.includes('cartesian') && !query.includes('limit'))
    );
  }

  /**
   * Analyze performance patterns
   */
  private async analyzePerformancePatterns(logs: QueryLog[]): Promise<PerformancePattern[]> {
    const patterns: PerformancePattern[] = [];

    // Slow query pattern
    const slowQueries = logs.filter(log => log.duration > 1000);
    if (slowQueries.length > 5) {
      patterns.push({
        description: 'Recurring slow query pattern detected',
        queriesAffected: slowQueries.length,
        avgImpact: slowQueries.reduce((sum, q) => sum + q.duration, 0) / slowQueries.length,
        trend: this.calculatePerformanceTrend(slowQueries),
        recommendations: [
          'Add appropriate indexes',
          'Review query complexity',
          'Consider query optimization'
        ],
        examples: slowQueries.slice(0, 3).map(q => q.query.substring(0, 100))
      });
    }

    // Missing index pattern
    const noIndexQueries = logs.filter(log =>
      log.query.toLowerCase().includes('where') &&
      !log.query.toLowerCase().includes('index')
    );
    if (noIndexQueries.length > 10) {
      patterns.push({
        description: 'Queries without index utilization',
        queriesAffected: noIndexQueries.length,
        avgImpact: noIndexQueries.reduce((sum, q) => sum + q.duration, 0) / noIndexQueries.length,
        trend: 'stable',
        recommendations: [
          'Analyze query execution plans',
          'Create indexes on frequently queried columns'
        ],
        examples: noIndexQueries.slice(0, 3).map(q => q.query.substring(0, 100))
      });
    }

    return patterns;
  }

  /**
   * Calculate performance trend
   */
  private calculatePerformanceTrend(logs: QueryLog[]): 'improving' | 'degrading' | 'stable' {
    if (logs.length < 10) return 'stable';

    const sorted = [...logs].sort((a, b) => a.timestamp - b.timestamp);
    const mid = Math.floor(sorted.length / 2);

    const firstHalf = sorted.slice(0, mid);
    const secondHalf = sorted.slice(mid);

    const avgFirst = firstHalf.reduce((sum, l) => sum + l.duration, 0) / firstHalf.length;
    const avgSecond = secondHalf.reduce((sum, l) => sum + l.duration, 0) / secondHalf.length;

    const change = ((avgSecond - avgFirst) / avgFirst) * 100;

    if (change < -10) return 'improving';
    if (change > 10) return 'degrading';
    return 'stable';
  }

  /**
   * Analyze usage patterns
   */
  private async analyzeUsagePatterns(logs: QueryLog[]): Promise<UsagePattern> {
    // Peak hours
    const hourCounts = new Map<number, { count: number; totalDuration: number }>();
    for (const log of logs) {
      const hour = new Date(log.timestamp).getHours();
      const existing = hourCounts.get(hour) || { count: 0, totalDuration: 0 };
      existing.count++;
      existing.totalDuration += log.duration;
      hourCounts.set(hour, existing);
    }

    const peakHours = Array.from(hourCounts.entries())
      .map(([hour, stats]) => ({
        hour,
        count: stats.count,
        avgDuration: stats.totalDuration / stats.count
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

    // Common operations
    const operations = new Map<string, number>();
    for (const log of logs) {
      const op = this.getOperationType(log.query);
      operations.set(op, (operations.get(op) || 0) + 1);
    }

    const totalOps = logs.length;
    const commonOperations = Array.from(operations.entries())
      .map(([operation, count]) => ({
        operation,
        count,
        percentage: (count / totalOps) * 100
      }))
      .sort((a, b) => b.count - a.count);

    // User behavior (simplified)
    const avgSessionLength = 30; // minutes
    const queriesPerSession = logs.length / Math.max(1, logs.length / 50);

    const preferredQueryTypes = commonOperations.slice(0, 3).map(o => o.operation);

    // Access patterns
    const accessPatterns: Array<{ table: string; accessCount: number; operations: string[] }> = [];

    return {
      peakHours,
      commonOperations,
      userBehavior: {
        averageSessionLength: avgSessionLength,
        queriesPerSession,
        preferredQueryTypes
      },
      accessPatterns
    };
  }

  /**
   * Get operation type from query
   */
  private getOperationType(query: string): string {
    const normalized = query.trim().toLowerCase();

    if (normalized.startsWith('select')) return 'SELECT';
    if (normalized.startsWith('insert')) return 'INSERT';
    if (normalized.startsWith('update')) return 'UPDATE';
    if (normalized.startsWith('delete')) return 'DELETE';
    if (normalized.startsWith('create')) return 'CREATE';
    if (normalized.startsWith('alter')) return 'ALTER';
    if (normalized.startsWith('drop')) return 'DROP';

    return 'OTHER';
  }

  /**
   * Generate recommendations using AI
   */
  private async generateRecommendations(
    clusters: PatternCluster[],
    anomalies: Anomaly[],
    threats: SecurityThreat[]
  ): Promise<string[]> {
    if (!this.llmProvider) {
      return this.generateBasicRecommendations(clusters, anomalies);
    }

    try {
      const summary = {
        totalPatterns: clusters.length,
        anomalies: anomalies.length,
        securityThreats: threats.length,
        performanceIssues: clusters.filter(c => c.avgPerformance > 1000).length
      };

      const response = await this.llmProvider.generate({
        messages: [{
          role: 'user',
          content: `As a database expert, analyze these patterns and provide 5-7 actionable recommendations:

Patterns found: ${summary.totalPatterns}
Anomalies: ${summary.anomalies}
Security threats: ${summary.securityThreats}
Performance issues: ${summary.performanceIssues}

Top pattern characteristics:
${clusters.slice(0, 3).map(c => `- ${c.type}: ${c.characteristics.join(', ')}`).join('\n')}

Provide specific, actionable recommendations as a numbered list.`
        }],
        maxTokens: 800,
        temperature: 0.4
      });

      const recommendations = response.content
        .split('\n')
        .filter(line => /^\d+\./.test(line.trim()))
        .map(line => line.replace(/^\d+\.\s*/, '').trim())
        .filter(rec => rec.length > 0);

      return recommendations;
    } catch (error) {
      this.logger.error('Failed to generate AI recommendations', error);
      return this.generateBasicRecommendations(clusters, anomalies);
    }
  }

  /**
   * Generate basic recommendations
   */
  private generateBasicRecommendations(
    clusters: PatternCluster[],
    anomalies: Anomaly[]
  ): string[] {
    const recommendations: string[] = [];

    if (clusters.length > 0) {
      const slowClusters = clusters.filter(c => c.avgPerformance > 1000);
      if (slowClusters.length > 0) {
        recommendations.push('Optimize slow query patterns with indexes and query rewrites');
      }

      const complexClusters = clusters.filter(c =>
        c.characteristics.includes('High complexity')
      );
      if (complexClusters.length > 0) {
        recommendations.push('Simplify complex queries by breaking them into smaller operations');
      }
    }

    if (anomalies.length > 0) {
      const criticalAnomalies = anomalies.filter(a => a.severity === 'critical');
      if (criticalAnomalies.length > 0) {
        recommendations.push('Investigate critical anomalies for potential security issues');
      }
    }

    recommendations.push('Regularly monitor query patterns for performance degradation');
    recommendations.push('Implement query result caching for frequently executed queries');

    return recommendations;
  }

  /**
   * Update learning model from patterns
   */
  private async updateLearningModel(
    clusters: PatternCluster[],
    anomalies: Anomaly[]
  ): Promise<void> {
    try {
      // Update learning model
      for (const pattern of clusters) {
        const key = this.getPatternSignature(pattern);
        const currentWeight = this.learningModel.get(key) || 0;
        this.learningModel.set(key, currentWeight + pattern.frequency);
      }

      // Learn from anomalies
      for (const anomaly of anomalies) {
        const key = `anomaly:${anomaly.type}:${this.hashQuery(anomaly.query)}`;
        const currentWeight = this.learningModel.get(key) || 0;
        this.learningModel.set(key, currentWeight + anomaly.anomalyScore);
      }

      this.logger.debug('Learning model updated', {
        patternsLearned: this.learningModel.size
      });
    } catch (error) {
      this.logger.error('Failed to update learning model', error);
    }
  }

  /**
   * Train AI model from patterns
   */
  private async trainAIModel(insights: PatternInsights): Promise<void> {
    if (!this.llmProvider) return;

    try {
      // Create training summary
      const trainingSummary = {
        patterns: insights.patterns.map(p => ({
          type: p.type,
          characteristics: p.characteristics,
          frequency: p.frequency
        })),
        anomalies: insights.anomalies.map(a => ({
          type: a.type,
          severity: a.severity,
          reasons: a.reasons
        }))
      };

      // Store training data
      this.stateManager.set('ai-training:patterns', trainingSummary, {
        metadata: { type: 'ai-training' }
      });

      this.logger.info('AI model training data prepared');
    } catch (error) {
      this.logger.error('Failed to train AI model', error);
    }
  }

  /**
   * Get pattern signature for learning
   */
  private getPatternSignature(pattern: PatternCluster): string {
    return `${pattern.type}:${pattern.characteristics.join(':')}`;
  }

  /**
   * Hash query for learning
   */
  private hashQuery(query: string): string {
    // Simple hash function
    let hash = 0;
    for (let i = 0; i < query.length; i++) {
      const char = query.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString(36);
  }

  /**
   * Calculate confidence level
   */
  private calculateConfidence(sampleSize: number, clustersFound: number): number {
    if (sampleSize < 10) return 0.3;
    if (sampleSize < 50) return 0.5;
    if (sampleSize < 100) return 0.7;

    const clusterQuality = Math.min(clustersFound / 10, 1);
    return 0.7 + clusterQuality * 0.3;
  }

  /**
   * Convert to CSV format
   */
  private convertToCSV(exportData: PatternExport): string {
    const lines: string[] = [];

    // Header
    lines.push('Type,ID,Frequency,AvgPerformance,Characteristics');

    // Patterns
    for (const pattern of exportData.patterns) {
      lines.push([
        pattern.type,
        pattern.id,
        pattern.frequency.toString(),
        pattern.avgPerformance.toFixed(2),
        `"${pattern.characteristics.join('; ')}"`
      ].join(','));
    }

    return lines.join('\n');
  }

  /**
   * Get empty insights
   */
  private getEmptyInsights(): PatternInsights {
    return {
      summary: {
        totalPatterns: 0,
        clustersFound: 0,
        anomaliesDetected: 0,
        securityThreats: 0,
        performanceIssues: 0
      },
      patterns: [],
      anomalies: [],
      securityThreats: [],
      performancePatterns: [],
      usagePatterns: {
        peakHours: [],
        commonOperations: [],
        userBehavior: {
          averageSessionLength: 0,
          queriesPerSession: 0,
          preferredQueryTypes: []
        },
        accessPatterns: []
      },
      recommendations: ['Not enough data for analysis'],
      confidence: 0,
      analysisTimestamp: Date.now()
    };
  }

  /**
   * Load state from storage
   */
  private loadState(): void {
    try {
      const storedClusters = this.stateManager.get('pattern-clusters');
      if (storedClusters && Array.isArray(storedClusters)) {
        storedClusters.forEach((cluster: PatternCluster) => {
          this.clusters.set(cluster.id, cluster);
        });
      }

      const storedAnomalies = this.stateManager.get('pattern-anomalies');
      if (storedAnomalies && Array.isArray(storedAnomalies)) {
        this.anomalyHistory = storedAnomalies;
      }

      const storedThreats = this.stateManager.get('pattern-threats');
      if (storedThreats && Array.isArray(storedThreats)) {
        this.securityThreats = storedThreats;
      }

      const storedModel = this.stateManager.get('pattern-learning-model');
      if (storedModel) {
        this.learningModel = new Map(Object.entries(storedModel));
      }

      this.logger.info('Pattern detection state loaded');
    } catch (error) {
      this.logger.warn('Failed to load pattern detection state', { error });
    }
  }

  /**
   * Save state to storage
   */
  private saveState(): void {
    try {
      this.stateManager.set('pattern-clusters', Array.from(this.clusters.values()), {
        metadata: { type: 'pattern-clusters' }
      });

      this.stateManager.set('pattern-anomalies', this.anomalyHistory, {
        metadata: { type: 'pattern-anomalies' }
      });

      this.stateManager.set('pattern-threats', this.securityThreats, {
        metadata: { type: 'pattern-threats' }
      });

      this.stateManager.set('pattern-learning-model', Object.fromEntries(this.learningModel), {
        metadata: { type: 'pattern-learning' }
      });

      this.logger.info('Pattern detection state saved');
    } catch (error) {
      this.logger.warn('Failed to save pattern detection state', { error });
    }
  }
}
