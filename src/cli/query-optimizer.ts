/**
 * AI Query Optimizer
 * Analyzes and optimizes SQL queries using Claude AI
 * Commands: ai-shell optimize <query>, ai-shell analyze-slow-queries
 */

import { AnthropicProvider } from '../llm/anthropic-provider';
import { DatabaseConnectionManager, DatabaseType } from './database-manager';
import { createLogger } from '../core/logger';
import { StateManager } from '../core/state-manager';

interface QueryAnalysis {
  query: string;
  issues: string[];
  suggestions: string[];
  optimizedQuery: string;
  indexRecommendations: string[];
  estimatedImprovement: string;
  executionPlan?: any;
}

interface SlowQuery {
  query: string;
  executionTime: number;
  frequency: number;
  lastExecuted: number;
}

export class QueryOptimizer {
  private logger = createLogger('QueryOptimizer');
  private llmProvider: AnthropicProvider;
  private slowQueryLog = new Map<string, SlowQuery>();

  constructor(
    private dbManager: DatabaseConnectionManager,
    private stateManager: StateManager,
    apiKey: string
  ) {
    this.llmProvider = new AnthropicProvider({ apiKey });
    this.loadSlowQueryLog();
  }

  /**
   * Optimize a SQL query using AI analysis
   */
  async optimizeQuery(query: string): Promise<QueryAnalysis> {
    this.logger.info('Optimizing query', { queryLength: query.length });

    try {
      // Get execution plan from database
      const executionPlan = await this.getExecutionPlan(query);

      // Analyze with Claude
      const prompt = this.buildOptimizationPrompt(query, executionPlan);
      const response = await this.llmProvider.generate({
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ],
        maxTokens: 4096,
        temperature: 0.3
      });

      // Parse AI response
      const analysis = this.parseOptimizationResponse(response.content, query);

      // Store analysis in state
      this.stateManager.set(`query-analysis:${Date.now()}`, analysis, {
        metadata: { type: 'query-optimization' }
      });

      this.logger.info('Query optimization complete', {
        issuesFound: analysis.issues.length,
        suggestionsCount: analysis.suggestions.length
      });

      return analysis;
    } catch (error) {
      this.logger.error('Failed to optimize query', error);
      throw new Error(
        `Query optimization failed: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Analyze slow queries from log
   */
  async analyzeSlowQueries(threshold: number = 1000): Promise<QueryAnalysis[]> {
    this.logger.info('Analyzing slow queries', { threshold, count: this.slowQueryLog.size });

    const slowQueries = Array.from(this.slowQueryLog.values())
      .filter((q) => q.executionTime >= threshold)
      .sort((a, b) => b.executionTime - a.executionTime)
      .slice(0, 10); // Top 10 slow queries

    const analyses: QueryAnalysis[] = [];

    for (const slowQuery of slowQueries) {
      try {
        const analysis = await this.optimizeQuery(slowQuery.query);
        analyses.push(analysis);
      } catch (error) {
        this.logger.error('Failed to analyze slow query', error, {
          query: slowQuery.query.substring(0, 100)
        });
      }
    }

    return analyses;
  }

  /**
   * Log query execution for slow query detection
   */
  logQuery(query: string, executionTime: number): void {
    const normalizedQuery = this.normalizeQuery(query);

    if (this.slowQueryLog.has(normalizedQuery)) {
      const existing = this.slowQueryLog.get(normalizedQuery)!;
      existing.frequency++;
      existing.executionTime = Math.max(existing.executionTime, executionTime);
      existing.lastExecuted = Date.now();
    } else {
      this.slowQueryLog.set(normalizedQuery, {
        query,
        executionTime,
        frequency: 1,
        lastExecuted: Date.now()
      });
    }

    // Persist to state
    this.saveSlowQueryLog();
  }

  /**
   * Get execution plan from database
   */
  private async getExecutionPlan(query: string): Promise<any> {
    const connection = this.dbManager.getActive();

    if (!connection) {
      return null;
    }

    try {
      switch (connection.type) {
        case DatabaseType.POSTGRESQL:
          const pgResult = await connection.client.query(`EXPLAIN (FORMAT JSON) ${query}`);
          return pgResult.rows[0]['QUERY PLAN'];

        case DatabaseType.MYSQL:
          const [mysqlResult] = await connection.client.query(`EXPLAIN FORMAT=JSON ${query}`);
          return mysqlResult;

        case DatabaseType.SQLITE:
          return new Promise((resolve, reject) => {
            connection.client.all(`EXPLAIN QUERY PLAN ${query}`, (err: Error, rows: any) => {
              if (err) reject(err);
              else resolve(rows);
            });
          });

        default:
          return null;
      }
    } catch (error) {
      this.logger.warn('Failed to get execution plan', { error });
      return null;
    }
  }

  /**
   * Build optimization prompt for Claude
   */
  private buildOptimizationPrompt(query: string, executionPlan: any): string {
    const connection = this.dbManager.getActive();
    const dbType = connection?.type || 'unknown';

    return `You are a database optimization expert. Analyze the following SQL query and provide optimization recommendations.

Database Type: ${dbType}
Query:
\`\`\`sql
${query}
\`\`\`

${executionPlan ? `Execution Plan:\n\`\`\`json\n${JSON.stringify(executionPlan, null, 2)}\n\`\`\`` : ''}

Please provide:
1. A list of issues or inefficiencies in the query
2. Specific optimization suggestions
3. An optimized version of the query
4. Index recommendations to improve performance
5. Estimated improvement (e.g., "50% faster", "Reduces full table scan")

Format your response as JSON with the following structure:
{
  "issues": ["issue1", "issue2", ...],
  "suggestions": ["suggestion1", "suggestion2", ...],
  "optimizedQuery": "OPTIMIZED SQL HERE",
  "indexRecommendations": ["CREATE INDEX ...", ...],
  "estimatedImprovement": "description of expected improvement"
}`;
  }

  /**
   * Parse Claude's optimization response
   */
  private parseOptimizationResponse(response: string, originalQuery: string): QueryAnalysis {
    try {
      // Extract JSON from response
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        throw new Error('No valid JSON found in response');
      }

      const parsed = JSON.parse(jsonMatch[0]);

      return {
        query: originalQuery,
        issues: parsed.issues || [],
        suggestions: parsed.suggestions || [],
        optimizedQuery: parsed.optimizedQuery || originalQuery,
        indexRecommendations: parsed.indexRecommendations || [],
        estimatedImprovement: parsed.estimatedImprovement || 'Unknown'
      };
    } catch (error) {
      this.logger.error('Failed to parse optimization response', error);

      // Fallback to basic analysis
      return {
        query: originalQuery,
        issues: ['Unable to analyze query automatically'],
        suggestions: [response],
        optimizedQuery: originalQuery,
        indexRecommendations: [],
        estimatedImprovement: 'Manual review required'
      };
    }
  }

  /**
   * Normalize query for deduplication
   */
  private normalizeQuery(query: string): string {
    return query
      .replace(/\s+/g, ' ')
      .replace(/\d+/g, '?')
      .replace(/'[^']*'/g, '?')
      .trim()
      .toLowerCase();
  }

  /**
   * Get slow query statistics
   */
  getSlowQueryStats(): {
    totalQueries: number;
    slowQueries: number;
    avgExecutionTime: number;
    topSlowQueries: SlowQuery[];
  } {
    const queries = Array.from(this.slowQueryLog.values());
    const slowQueries = queries.filter((q) => q.executionTime >= 1000);

    const avgExecutionTime =
      queries.reduce((sum, q) => sum + q.executionTime, 0) / queries.length || 0;

    const topSlowQueries = queries
      .sort((a, b) => b.executionTime - a.executionTime)
      .slice(0, 10);

    return {
      totalQueries: queries.length,
      slowQueries: slowQueries.length,
      avgExecutionTime,
      topSlowQueries
    };
  }

  /**
   * Clear slow query log
   */
  clearSlowQueryLog(): void {
    this.slowQueryLog.clear();
    this.saveSlowQueryLog();
    this.logger.info('Slow query log cleared');
  }

  /**
   * Export slow queries to file
   */
  exportSlowQueries(): SlowQuery[] {
    return Array.from(this.slowQueryLog.values());
  }

  /**
   * Load slow query log from state
   */
  private loadSlowQueryLog(): void {
    try {
      const stored = this.stateManager.get('slow-query-log');
      if (stored && Array.isArray(stored)) {
        stored.forEach((item: any) => {
          this.slowQueryLog.set(this.normalizeQuery(item.query), item);
        });
        this.logger.info('Loaded slow query log', { count: this.slowQueryLog.size });
      }
    } catch (error) {
      this.logger.warn('Failed to load slow query log', { error });
    }
  }

  /**
   * Save slow query log to state
   */
  private saveSlowQueryLog(): void {
    try {
      const queries = Array.from(this.slowQueryLog.values());
      this.stateManager.set('slow-query-log', queries, {
        metadata: { type: 'slow-query-log' }
      });
    } catch (error) {
      this.logger.warn('Failed to save slow query log', { error });
    }
  }

  /**
   * Auto-optimize query with confirmation
   */
  async autoOptimize(query: string, autoApply: boolean = false): Promise<string> {
    const analysis = await this.optimizeQuery(query);

    if (autoApply && analysis.optimizedQuery !== query) {
      this.logger.info('Auto-applying optimized query');
      return analysis.optimizedQuery;
    }

    return analysis.optimizedQuery;
  }
}
