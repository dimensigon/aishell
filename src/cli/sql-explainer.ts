/**
 * SQL Explainer
 * Translate SQL to English and vice versa using Claude AI
 * Commands: ai-shell explain "<sql>", ai-shell translate "<natural-language>"
 */

import { AnthropicProvider } from '../llm/anthropic-provider';
import { DatabaseConnectionManager, DatabaseType } from './database-manager';
import { createLogger } from '../core/logger';
import { StateManager } from '../core/state-manager';

interface Explanation {
  query: string;
  explanation: string;
  breakdown: QueryBreakdown;
  complexity: 'simple' | 'medium' | 'complex';
  estimatedPerformance: string;
  suggestions?: string[];
}

interface QueryBreakdown {
  operation: string;
  tables: string[];
  columns: string[];
  joins: JoinInfo[];
  filters: string[];
  aggregations: string[];
  ordering: string[];
}

interface JoinInfo {
  type: string;
  leftTable: string;
  rightTable: string;
  condition: string;
}

interface Translation {
  naturalLanguage: string;
  sql: string;
  confidence: number;
  alternatives: string[];
  explanation: string;
}

export class SQLExplainer {
  private logger = createLogger('SQLExplainer');
  private llmProvider: AnthropicProvider;
  private explanationCache = new Map<string, Explanation>();

  constructor(
    private dbManager: DatabaseConnectionManager,
    private _stateManager: StateManager,
    apiKey: string
  ) {
    this.llmProvider = new AnthropicProvider({ apiKey });
  }

  /**
   * Explain SQL query in plain English
   */
  async explainSQL(query: string): Promise<Explanation> {
    this.logger.info('Explaining SQL query', { queryLength: query.length });

    // Check cache
    const cached = this.explanationCache.get(query);
    if (cached) {
      this.logger.debug('Using cached explanation');
      return cached;
    }

    try {
      // Get schema context
      const schema = await this.getSchemaContext();

      // Build explanation prompt
      const prompt = this.buildExplanationPrompt(query, schema);

      // Get explanation from Claude
      const response = await this.llmProvider.generate({
        messages: [{ role: 'user', content: prompt }],
        maxTokens: 2048,
        temperature: 0.3
      });

      // Parse response
      const explanation = this.parseExplanation(query, response.content);

      // Cache explanation
      this.explanationCache.set(query, explanation);

      this.logger.info('SQL explained successfully', {
        complexity: explanation.complexity
      });

      return explanation;
    } catch (error) {
      this.logger.error('Failed to explain SQL', error);
      throw new Error(`SQL explanation failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Translate natural language to SQL
   */
  async translateToSQL(naturalLanguage: string): Promise<Translation> {
    this.logger.info('Translating natural language to SQL', {
      inputLength: naturalLanguage.length
    });

    try {
      // Get schema context
      const schema = await this.getSchemaContext();

      // Build translation prompt
      const prompt = this.buildTranslationPrompt(naturalLanguage, schema);

      // Get SQL from Claude
      const response = await this.llmProvider.generate({
        messages: [{ role: 'user', content: prompt }],
        maxTokens: 2048,
        temperature: 0.3
      });

      // Parse response
      const translation = this.parseTranslation(naturalLanguage, response.content);

      this.logger.info('Translation completed', {
        confidence: translation.confidence
      });

      return translation;
    } catch (error) {
      this.logger.error('Failed to translate to SQL', error);
      throw new Error(`Translation failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Build explanation prompt for Claude
   */
  private buildExplanationPrompt(query: string, schema: any): string {
    return `You are a SQL expert. Explain the following SQL query in plain, easy-to-understand English.

Database Schema:
${JSON.stringify(schema, null, 2)}

SQL Query:
\`\`\`sql
${query}
\`\`\`

Provide a comprehensive explanation including:
1. A clear, plain English description of what the query does
2. A breakdown of the query components (SELECT, FROM, WHERE, JOIN, etc.)
3. List of tables and columns involved
4. Any joins and their relationships
5. Filters and conditions
6. Aggregations and groupings
7. Ordering and limits
8. Query complexity (simple/medium/complex)
9. Estimated performance characteristics
10. Suggestions for improvement (if any)

Format your response as JSON:
{
  "explanation": "Plain English explanation here...",
  "breakdown": {
    "operation": "SELECT/INSERT/UPDATE/DELETE",
    "tables": ["table1", "table2"],
    "columns": ["col1", "col2"],
    "joins": [{"type": "INNER", "leftTable": "t1", "rightTable": "t2", "condition": "..."}],
    "filters": ["condition1", "condition2"],
    "aggregations": ["COUNT(*)", "SUM(amount)"],
    "ordering": ["created_at DESC"]
  },
  "complexity": "simple",
  "estimatedPerformance": "Fast - uses indexed columns",
  "suggestions": ["Add index on user_id", "Consider pagination"]
}`;
  }

  /**
   * Build translation prompt for Claude
   */
  private buildTranslationPrompt(naturalLanguage: string, schema: any): string {
    return `You are a SQL expert. Convert the following natural language request into a SQL query.

Database Schema:
${JSON.stringify(schema, null, 2)}

Natural Language Request:
"${naturalLanguage}"

Generate:
1. The most appropriate SQL query for this request
2. Alternative SQL queries (if applicable)
3. An explanation of the generated SQL
4. Confidence level (0-100)

Format your response as JSON:
{
  "sql": "SELECT * FROM users WHERE ...",
  "alternatives": [
    "SELECT user_id, name FROM users WHERE ...",
    "SELECT * FROM users INNER JOIN ..."
  ],
  "explanation": "This query retrieves...",
  "confidence": 95
}`;
  }

  /**
   * Parse explanation from AI response
   */
  private parseExplanation(query: string, response: string): Explanation {
    try {
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        throw new Error('No valid JSON found in response');
      }

      const parsed = JSON.parse(jsonMatch[0]);

      return {
        query,
        explanation: parsed.explanation || 'No explanation available',
        breakdown: parsed.breakdown || this.createEmptyBreakdown(),
        complexity: parsed.complexity || 'medium',
        estimatedPerformance: parsed.estimatedPerformance || 'Unknown',
        suggestions: parsed.suggestions
      };
    } catch (error) {
      this.logger.error('Failed to parse explanation', error);

      // Fallback to basic analysis
      return {
        query,
        explanation: response,
        breakdown: this.analyzeQueryBasic(query),
        complexity: 'medium',
        estimatedPerformance: 'Unknown'
      };
    }
  }

  /**
   * Parse translation from AI response
   */
  private parseTranslation(naturalLanguage: string, response: string): Translation {
    try {
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        throw new Error('No valid JSON found in response');
      }

      const parsed = JSON.parse(jsonMatch[0]);

      return {
        naturalLanguage,
        sql: parsed.sql || '',
        confidence: parsed.confidence || 0,
        alternatives: parsed.alternatives || [],
        explanation: parsed.explanation || ''
      };
    } catch (error) {
      this.logger.error('Failed to parse translation', error);
      throw new Error('Failed to parse translation from AI response');
    }
  }

  /**
   * Get schema context for AI
   */
  private async getSchemaContext(): Promise<any> {
    const connection = this.dbManager.getActive();

    if (!connection) {
      return { tables: [] };
    }

    try {
      switch (connection.type) {
        case DatabaseType.POSTGRESQL:
          return await this.getPostgreSQLSchema();

        case DatabaseType.MYSQL:
          return await this.getMySQLSchema();

        case DatabaseType.SQLITE:
          return await this.getSQLiteSchema();

        case DatabaseType.MONGODB:
          return await this.getMongoDBSchema();

        default:
          return { tables: [] };
      }
    } catch (error) {
      this.logger.warn('Failed to get schema context', { error });
      return { tables: [] };
    }
  }

  /**
   * Get PostgreSQL schema
   */
  private async getPostgreSQLSchema(): Promise<any> {
    const connection = this.dbManager.getActive();
    if (!connection) return { tables: [] };

    const result = await (connection.client as any).query(`
      SELECT
        t.table_name,
        c.column_name,
        c.data_type,
        c.is_nullable,
        tc.constraint_type
      FROM information_schema.tables t
      LEFT JOIN information_schema.columns c
        ON t.table_name = c.table_name
      LEFT JOIN information_schema.key_column_usage kcu
        ON c.column_name = kcu.column_name AND c.table_name = kcu.table_name
      LEFT JOIN information_schema.table_constraints tc
        ON kcu.constraint_name = tc.constraint_name
      WHERE t.table_schema = 'public'
      ORDER BY t.table_name, c.ordinal_position
    `);

    return this.formatSchemaInfo(result.rows);
  }

  /**
   * Get MySQL schema
   */
  private async getMySQLSchema(): Promise<any> {
    const connection = this.dbManager.getActive();
    if (!connection) return { tables: [] };

    const [result] = await (connection.client as any).query(`
      SELECT
        TABLE_NAME as table_name,
        COLUMN_NAME as column_name,
        DATA_TYPE as data_type,
        IS_NULLABLE as is_nullable,
        COLUMN_KEY as constraint_type
      FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE()
      ORDER BY TABLE_NAME, ORDINAL_POSITION
    `);

    return this.formatSchemaInfo(result);
  }

  /**
   * Get SQLite schema
   */
  private async getSQLiteSchema(): Promise<any> {
    const connection = this.dbManager.getActive();
    if (!connection) return { tables: [] };

    return new Promise((resolve, reject) => {
      (connection.client as any).all(
        "SELECT name FROM sqlite_master WHERE type='table'",
        (err: Error, tables: any[]) => {
          if (err) {
            reject(err);
            return;
          }

          const schema = { tables: [] as any[] };

          tables.forEach((table) => {
            (connection.client as any).all(
              `PRAGMA table_info(${table.name})`,
              (err: Error, columns: any[]) => {
                if (!err) {
                  schema.tables.push({
                    name: table.name,
                    columns: columns.map((col) => ({
                      name: col.name,
                      type: col.type,
                      nullable: !col.notnull
                    }))
                  });
                }
              }
            );
          });

          resolve(schema);
        }
      );
    });
  }

  /**
   * Get MongoDB schema
   */
  private async getMongoDBSchema(): Promise<any> {
    const connection = this.dbManager.getActive();
    if (!connection) return { collections: [] };

    const collections = await (connection.client as any).db().listCollections().toArray();

    return {
      collections: collections.map((c: any) => c.name)
    };
  }

  /**
   * Format schema information
   */
  private formatSchemaInfo(rows: any[]): any {
    const schema: any = { tables: [] };
    const tableMap = new Map<string, any>();

    rows.forEach((row) => {
      if (!tableMap.has(row.table_name)) {
        tableMap.set(row.table_name, {
          name: row.table_name,
          columns: []
        });
      }

      const table = tableMap.get(row.table_name);
      table.columns.push({
        name: row.column_name,
        type: row.data_type,
        nullable: row.is_nullable === 'YES',
        isPrimaryKey: row.constraint_type === 'PRIMARY KEY'
      });
    });

    schema.tables = Array.from(tableMap.values());
    return schema;
  }

  /**
   * Basic query analysis (fallback)
   */
  private analyzeQueryBasic(query: string): QueryBreakdown {
    const breakdown: QueryBreakdown = {
      operation: this.detectOperation(query),
      tables: this.extractTables(query),
      columns: this.extractColumns(query),
      joins: [],
      filters: this.extractFilters(query),
      aggregations: this.extractAggregations(query),
      ordering: this.extractOrdering(query)
    };

    return breakdown;
  }

  /**
   * Detect SQL operation
   */
  private detectOperation(query: string): string {
    const normalized = query.trim().toLowerCase();

    if (normalized.startsWith('select')) return 'SELECT';
    if (normalized.startsWith('insert')) return 'INSERT';
    if (normalized.startsWith('update')) return 'UPDATE';
    if (normalized.startsWith('delete')) return 'DELETE';
    if (normalized.startsWith('create')) return 'CREATE';
    if (normalized.startsWith('alter')) return 'ALTER';
    if (normalized.startsWith('drop')) return 'DROP';

    return 'UNKNOWN';
  }

  /**
   * Extract table names from query
   */
  private extractTables(query: string): string[] {
    const tables: string[] = [];

    // FROM clause
    const fromMatch = query.match(/FROM\s+(\w+)/gi);
    if (fromMatch) {
      fromMatch.forEach((m) => {
        const table = m.replace(/FROM\s+/i, '').trim();
        tables.push(table);
      });
    }

    // JOIN clauses
    const joinMatch = query.match(/JOIN\s+(\w+)/gi);
    if (joinMatch) {
      joinMatch.forEach((m) => {
        const table = m.replace(/JOIN\s+/i, '').trim();
        tables.push(table);
      });
    }

    return [...new Set(tables)];
  }

  /**
   * Extract column names from query
   */
  private extractColumns(query: string): string[] {
    const columns: string[] = [];

    // SELECT clause
    const selectMatch = query.match(/SELECT\s+(.*?)\s+FROM/is);
    if (selectMatch) {
      const columnsStr = selectMatch[1];
      if (columnsStr !== '*') {
        columnsStr.split(',').forEach((col) => {
          columns.push(col.trim());
        });
      }
    }

    return columns;
  }

  /**
   * Extract WHERE filters
   */
  private extractFilters(query: string): string[] {
    const filters: string[] = [];

    const whereMatch = query.match(/WHERE\s+(.*?)(?:GROUP BY|ORDER BY|LIMIT|$)/is);
    if (whereMatch) {
      const conditions = whereMatch[1].split(/AND|OR/i);
      conditions.forEach((cond) => {
        filters.push(cond.trim());
      });
    }

    return filters;
  }

  /**
   * Extract aggregations
   */
  private extractAggregations(query: string): string[] {
    const aggregations: string[] = [];
    const aggFunctions = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'GROUP_CONCAT'];

    aggFunctions.forEach((func) => {
      const regex = new RegExp(`${func}\\s*\\([^)]+\\)`, 'gi');
      const matches = query.match(regex);
      if (matches) {
        aggregations.push(...matches);
      }
    });

    return aggregations;
  }

  /**
   * Extract ordering
   */
  private extractOrdering(query: string): string[] {
    const ordering: string[] = [];

    const orderMatch = query.match(/ORDER BY\s+(.*?)(?:LIMIT|$)/is);
    if (orderMatch) {
      const orders = orderMatch[1].split(',');
      orders.forEach((order) => {
        ordering.push(order.trim());
      });
    }

    return ordering;
  }

  /**
   * Create empty breakdown
   */
  private createEmptyBreakdown(): QueryBreakdown {
    return {
      operation: 'UNKNOWN',
      tables: [],
      columns: [],
      joins: [],
      filters: [],
      aggregations: [],
      ordering: []
    };
  }

  /**
   * Interactive SQL learning mode
   */
  async interactiveExplain(query: string): Promise<void> {
    console.log('\n🎓 SQL Explainer - Interactive Mode\n');

    const explanation = await this.explainSQL(query);

    console.log('📝 Query:');
    console.log(query);
    console.log('\n💡 Explanation:');
    console.log(explanation.explanation);
    console.log('\n📊 Complexity:', explanation.complexity);
    console.log('⚡ Performance:', explanation.estimatedPerformance);

    if (explanation.suggestions && explanation.suggestions.length > 0) {
      console.log('\n💭 Suggestions:');
      explanation.suggestions.forEach((s, i) => {
        console.log(`   ${i + 1}. ${s}`);
      });
    }

    console.log('\n');
  }

  /**
   * Clear explanation cache
   */
  clearCache(): void {
    this.explanationCache.clear();
    this.logger.info('Explanation cache cleared');
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): { size: number; queries: string[] } {
    return {
      size: this.explanationCache.size,
      queries: Array.from(this.explanationCache.keys())
    };
  }
}
