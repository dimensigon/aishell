/**
 * Query Federation
 * Execute queries across multiple databases with AI-powered planning
 * Commands: ai-shell federate "<query>", ai-shell join <db1> <db2>
 */

import { AnthropicProvider } from '../llm/anthropic-provider';
import { DatabaseConnectionManager, DatabaseType } from './database-manager';
import { createLogger } from '../core/logger';
import { StateManager } from '../core/state-manager';

interface FederatedQuery {
  query: string;
  databases: string[];
  executionPlan: QueryPlan;
  results?: any[];
  duration?: number;
}

interface QueryPlan {
  steps: QueryStep[];
  estimatedCost: number;
  parallelizable: boolean;
}

interface QueryStep {
  id: string;
  database: string;
  query: string;
  dependencies: string[];
  operation: 'fetch' | 'join' | 'aggregate' | 'transform';
}

interface JoinConfig {
  leftDb: string;
  rightDb: string;
  leftTable: string;
  rightTable: string;
  joinKey: string;
  joinType: 'inner' | 'left' | 'right' | 'full';
}

export class QueryFederation {
  private logger = createLogger('QueryFederation');
  private llmProvider: AnthropicProvider;
  private queryCache = new Map<string, any[]>();

  constructor(
    private dbManager: DatabaseConnectionManager,
    private _stateManager: StateManager,
    apiKey: string
  ) {
    this.llmProvider = new AnthropicProvider({ apiKey });
  }

  /**
   * Execute federated query
   */
  async executeFederatedQuery(query: string, databases: string[]): Promise<FederatedQuery> {
    this.logger.info('Executing federated query', {
      databases,
      queryLength: query.length
    });

    const startTime = Date.now();

    try {
      // Generate execution plan using AI
      const executionPlan = await this.generateExecutionPlan(query, databases);

      // Execute plan
      const results = await this.executePlan(executionPlan);

      const federatedQuery: FederatedQuery = {
        query,
        databases,
        executionPlan,
        results,
        duration: Date.now() - startTime
      };

      this.logger.info('Federated query completed', {
        duration: federatedQuery.duration,
        resultCount: results.length
      });

      return federatedQuery;
    } catch (error) {
      this.logger.error('Federated query failed', error);
      throw new Error(
        `Federated query failed: ${error instanceof Error ? error.message : String(error)}`
      );
    }
  }

  /**
   * Generate execution plan using AI
   */
  private async generateExecutionPlan(query: string, databases: string[]): Promise<QueryPlan> {
    // Get schema information for each database
    const schemas = await Promise.all(
      databases.map((db) => this.getSchemaInfo(db))
    );

    const prompt = this.buildPlanningPrompt(query, databases, schemas);

    const response = await this.llmProvider.generate({
      messages: [{ role: 'user', content: prompt }],
      maxTokens: 4096,
      temperature: 0.3
    });

    return this.parsePlanResponse(response.content);
  }

  /**
   * Build planning prompt for Claude
   */
  private buildPlanningPrompt(
    query: string,
    databases: string[],
    schemas: any[]
  ): string {
    return `You are a distributed database query planner. Create an execution plan for a federated query.

Available Databases:
${databases.map((db, idx) => `${db}: ${JSON.stringify(schemas[idx], null, 2)}`).join('\n\n')}

Federated Query:
\`\`\`sql
${query}
\`\`\`

Create an execution plan that:
1. Breaks down the query into steps that can be executed on individual databases
2. Identifies data that needs to be fetched from each database
3. Plans joins and aggregations that need to happen after fetching
4. Optimizes for parallelization where possible
5. Minimizes data transfer between databases

Return a JSON execution plan with this structure:
{
  "steps": [
    {
      "id": "step1",
      "database": "db1",
      "query": "SELECT ...",
      "dependencies": [],
      "operation": "fetch"
    },
    ...
  ],
  "estimatedCost": 100,
  "parallelizable": true
}`;
  }

  /**
   * Parse execution plan from AI response
   */
  private parsePlanResponse(response: string): QueryPlan {
    try {
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        throw new Error('No valid JSON found in response');
      }

      const plan = JSON.parse(jsonMatch[0]);

      return {
        steps: plan.steps || [],
        estimatedCost: plan.estimatedCost || 0,
        parallelizable: plan.parallelizable || false
      };
    } catch (error) {
      this.logger.error('Failed to parse execution plan', error);
      throw new Error('Failed to parse execution plan from AI response');
    }
  }

  /**
   * Execute query plan
   */
  private async executePlan(plan: QueryPlan): Promise<any[]> {
    const results = new Map<string, any[]>();

    // Execute steps respecting dependencies
    const executed = new Set<string>();

    while (executed.size < plan.steps.length) {
      // Find steps that can be executed (all dependencies met)
      const ready = plan.steps.filter(
        (step) =>
          !executed.has(step.id) &&
          step.dependencies.every((dep) => executed.has(dep))
      );

      if (ready.length === 0) {
        throw new Error('Circular dependency or invalid plan');
      }

      // Execute ready steps in parallel
      const stepResults = await Promise.all(
        ready.map((step) => this.executeStep(step, results))
      );

      ready.forEach((step, idx) => {
        results.set(step.id, stepResults[idx]);
        executed.add(step.id);
      });
    }

    // Return final results (last step)
    const finalStep = plan.steps[plan.steps.length - 1];
    return results.get(finalStep.id) || [];
  }

  /**
   * Execute single step
   */
  private async executeStep(
    step: QueryStep,
    intermediateResults: Map<string, any[]>
  ): Promise<any[]> {
    this.logger.debug('Executing step', { stepId: step.id, operation: step.operation });

    try {
      switch (step.operation) {
        case 'fetch':
          return await this.executeFetch(step);

        case 'join':
          return await this.executeJoin(step, intermediateResults);

        case 'aggregate':
          return await this.executeAggregate(step, intermediateResults);

        case 'transform':
          return await this.executeTransform(step, intermediateResults);

        default:
          throw new Error(`Unknown operation: ${step.operation}`);
      }
    } catch (error) {
      this.logger.error('Step execution failed', error, { stepId: step.id });
      throw error;
    }
  }

  /**
   * Execute fetch operation
   */
  private async executeFetch(step: QueryStep): Promise<any[]> {
    const connection = this.dbManager.getConnection(step.database);

    if (!connection) {
      throw new Error(`Connection not found: ${step.database}`);
    }

    // Check cache
    const cacheKey = `${step.database}:${step.query}`;
    const cached = this.queryCache.get(cacheKey);
    if (cached) {
      this.logger.debug('Using cached results', { stepId: step.id });
      return cached;
    }

    const results = await this.dbManager.executeQuery(step.query);

    // Cache results
    this.queryCache.set(cacheKey, results);

    return results;
  }

  /**
   * Execute join operation
   */
  private async executeJoin(
    step: QueryStep,
    intermediateResults: Map<string, any[]>
  ): Promise<any[]> {
    // Parse join configuration from query
    const joinConfig = this.parseJoinConfig(step.query);

    const leftData = intermediateResults.get(step.dependencies[0]) || [];
    const rightData = intermediateResults.get(step.dependencies[1]) || [];

    return this.performJoin(leftData, rightData, joinConfig);
  }

  /**
   * Execute aggregate operation
   */
  private async executeAggregate(
    step: QueryStep,
    intermediateResults: Map<string, any[]>
  ): Promise<any[]> {
    const inputData = intermediateResults.get(step.dependencies[0]) || [];

    // Simple aggregation implementation
    // For production, use a library like lodash or sql.js
    return inputData;
  }

  /**
   * Execute transform operation
   */
  private async executeTransform(
    step: QueryStep,
    intermediateResults: Map<string, any[]>
  ): Promise<any[]> {
    const inputData = intermediateResults.get(step.dependencies[0]) || [];

    // Apply transformations
    return inputData;
  }

  /**
   * Perform in-memory join
   */
  private performJoin(
    leftData: any[],
    rightData: any[],
    config: JoinConfig
  ): any[] {
    const results: any[] = [];

    // Create index for right data
    const rightIndex = new Map<any, any[]>();
    rightData.forEach((row) => {
      const key = row[config.joinKey];
      if (!rightIndex.has(key)) {
        rightIndex.set(key, []);
      }
      rightIndex.get(key)!.push(row);
    });

    // Perform join
    leftData.forEach((leftRow) => {
      const key = leftRow[config.joinKey];
      const matchingRows = rightIndex.get(key) || [];

      if (matchingRows.length > 0) {
        matchingRows.forEach((rightRow) => {
          results.push({ ...leftRow, ...rightRow });
        });
      } else if (config.joinType === 'left' || config.joinType === 'full') {
        results.push(leftRow);
      }
    });

    // Full outer join - add unmatched right rows
    if (config.joinType === 'full') {
      const matchedKeys = new Set(leftData.map((row) => row[config.joinKey]));
      rightData.forEach((rightRow) => {
        if (!matchedKeys.has(rightRow[config.joinKey])) {
          results.push(rightRow);
        }
      });
    }

    return results;
  }

  /**
   * Parse join configuration from query
   */
  private parseJoinConfig(query: string): JoinConfig {
    // Simplified parser - for production, use a SQL parser library
    const joinMatch = query.match(
      /JOIN\s+(\w+)\s+ON\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)/i
    );

    if (!joinMatch) {
      throw new Error('Invalid join syntax');
    }

    return {
      leftDb: 'left',
      rightDb: 'right',
      leftTable: joinMatch[2],
      rightTable: joinMatch[4],
      joinKey: joinMatch[3],
      joinType: 'inner'
    };
  }

  /**
   * Get schema information for database
   */
  private async getSchemaInfo(database: string): Promise<any> {
    const connection = this.dbManager.getConnection(database);

    if (!connection) {
      return {};
    }

    try {
      switch (connection.type) {
        case DatabaseType.POSTGRESQL:
          const pgResult = await connection.client.query(`
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
          `);
          return this.formatSchemaInfo(pgResult.rows);

        case DatabaseType.MYSQL:
          const [mysqlResult] = await connection.client.query(`
            SELECT TABLE_NAME as table_name, COLUMN_NAME as column_name, DATA_TYPE as data_type
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
          `);
          return this.formatSchemaInfo(mysqlResult);

        case DatabaseType.MONGODB:
          // MongoDB is schemaless, return collection names
          const collections = await connection.client.db().listCollections().toArray();
          return { collections: collections.map((c: any) => c.name) };

        default:
          return {};
      }
    } catch (error) {
      this.logger.warn('Failed to get schema info', { database, error });
      return {};
    }
  }

  /**
   * Format schema information
   */
  private formatSchemaInfo(rows: any[]): any {
    const schema: any = {};

    rows.forEach((row) => {
      if (!schema[row.table_name]) {
        schema[row.table_name] = [];
      }
      schema[row.table_name].push({
        name: row.column_name,
        type: row.data_type
      });
    });

    return schema;
  }

  /**
   * Execute cross-database join
   */
  async executeCrossDatabaseJoin(config: JoinConfig): Promise<any[]> {
    this.logger.info('Executing cross-database join', config);

    // Fetch data from both databases
    const leftData = await this.fetchTableData(config.leftDb, config.leftTable);
    const rightData = await this.fetchTableData(config.rightDb, config.rightTable);

    // Perform join
    return this.performJoin(leftData, rightData, config);
  }

  /**
   * Fetch table data
   */
  private async fetchTableData(database: string, table: string): Promise<any[]> {
    const query = `SELECT * FROM ${table}`;
    const connection = this.dbManager.getConnection(database);

    if (!connection) {
      throw new Error(`Connection not found: ${database}`);
    }

    // Set active connection temporarily
    const originalActive = this.dbManager.getActive();
    await this.dbManager.switchActive(database);

    try {
      const results = await this.dbManager.executeQuery(query);
      return results;
    } finally {
      // Restore original active connection
      if (originalActive) {
        await this.dbManager.switchActive(originalActive.config.name);
      }
    }
  }

  /**
   * Clear query cache
   */
  clearCache(): void {
    this.queryCache.clear();
    this.logger.info('Query cache cleared');
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.queryCache.size,
      keys: Array.from(this.queryCache.keys())
    };
  }
}
