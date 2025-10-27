/**
 * Natural Language Query Translator
 * Converts natural language queries to SQL using LLM
 */

import { LLMMCPBridge } from '../llm/mcp-bridge';
import { ErrorHandler } from '../core/error-handler';

/**
 * Translation result
 */
export interface TranslationResult {
  sql: string;
  explanation: string;
  confidence: number;
  warnings: string[];
}

/**
 * Schema information
 */
export interface SchemaInfo {
  tables: TableInfo[];
  relationships: Relationship[];
}

/**
 * Table information
 */
export interface TableInfo {
  name: string;
  columns: ColumnInfo[];
  primaryKey?: string[];
  description?: string;
}

/**
 * Column information
 */
export interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
  defaultValue?: any;
  description?: string;
}

/**
 * Relationship information
 */
export interface Relationship {
  fromTable: string;
  fromColumn: string;
  toTable: string;
  toColumn: string;
  type: 'one-to-one' | 'one-to-many' | 'many-to-many';
}

/**
 * Natural Language Query Translator
 */
export class NLQueryTranslator {
  constructor(
    private llmBridge: LLMMCPBridge,
    private errorHandler: ErrorHandler
  ) {}

  /**
   * Translate natural language to SQL
   */
  async translate(
    naturalLanguage: string,
    schema: SchemaInfo,
    databaseType: string = 'postgresql'
  ): Promise<TranslationResult> {
    const wrappedFn = this.errorHandler.wrap(
      async () => {
        // Build schema context
        const schemaContext = this.buildSchemaContext(schema);

        // Create prompt for LLM
        const prompt = this.buildTranslationPrompt(
          naturalLanguage,
          schemaContext,
          databaseType
        );

        // Generate SQL using LLM
        const response = await this.llmBridge.generate({
          messages: [
            {
              role: 'system',
              content: this.getSystemPrompt(databaseType)
            },
            {
              role: 'user',
              content: prompt
            }
          ],
          enableTools: false
        });

        // Parse response
        const result = this.parseTranslationResponse(response.content);

        // Validate SQL
        this.validateSQL(result.sql, schema);

        return result;
      },
      {
        operation: 'translate',
        component: 'NLQueryTranslator'
      }
    );

    const result = await wrappedFn();
    if (!result) {
      throw new Error('Translation failed');
    }
    return result;
  }

  /**
   * Explain SQL query in natural language
   */
  async explain(sql: string, schema?: SchemaInfo): Promise<string> {
    const wrappedFn = this.errorHandler.wrap(
      async () => {
        const schemaContext = schema ? this.buildSchemaContext(schema) : '';

        const prompt = `Explain the following SQL query in simple natural language:

SQL Query:
\`\`\`sql
${sql}
\`\`\`

${schemaContext ? `Schema Context:\n${schemaContext}\n` : ''}

Provide a clear, concise explanation of what this query does.`;

        const response = await this.llmBridge.generate({
          messages: [
            {
              role: 'system',
              content: 'You are a SQL expert who explains queries in simple terms.'
            },
            {
              role: 'user',
              content: prompt
            }
          ],
          enableTools: false
        });

        return response.content.trim();
      },
      {
        operation: 'explain',
        component: 'NLQueryTranslator'
      }
    );

    const result = await wrappedFn();
    return result || 'Failed to explain query';
  }

  /**
   * Build schema context string
   */
  private buildSchemaContext(schema: SchemaInfo): string {
    const tables = schema.tables.map((table) => {
      const columns = table.columns
        .map((col) => {
          const nullable = col.nullable ? 'NULL' : 'NOT NULL';
          return `  - ${col.name} (${col.type}) ${nullable}${
            col.description ? ` // ${col.description}` : ''
          }`;
        })
        .join('\n');

      const pk = table.primaryKey
        ? `  Primary Key: ${table.primaryKey.join(', ')}`
        : '';

      return `Table: ${table.name}${table.description ? ` // ${table.description}` : ''}
${columns}
${pk}`;
    });

    const relationships = schema.relationships.length > 0
      ? `\nRelationships:
${schema.relationships
  .map(
    (rel) =>
      `  ${rel.fromTable}.${rel.fromColumn} -> ${rel.toTable}.${rel.toColumn} (${rel.type})`
  )
  .join('\n')}`
      : '';

    return tables.join('\n\n') + relationships;
  }

  /**
   * Build translation prompt
   */
  private buildTranslationPrompt(
    naturalLanguage: string,
    schemaContext: string,
    databaseType: string
  ): string {
    return `Convert the following natural language query to ${databaseType.toUpperCase()} SQL.

Natural Language Query:
"${naturalLanguage}"

Database Schema:
${schemaContext}

Requirements:
1. Generate syntactically correct ${databaseType.toUpperCase()} SQL
2. Use appropriate JOINs based on relationships
3. Include WHERE clauses for filtering
4. Add appropriate ORDER BY and LIMIT if implied
5. Use table aliases for readability
6. Optimize for performance

Response Format (JSON):
{
  "sql": "SELECT ... FROM ...",
  "explanation": "This query...",
  "confidence": 0.95,
  "warnings": ["Potential performance issue with full table scan"]
}

Provide the SQL query and explanation.`;
  }

  /**
   * Get system prompt for SQL generation
   */
  private getSystemPrompt(databaseType: string): string {
    return `You are an expert ${databaseType.toUpperCase()} database engineer. Your job is to convert natural language queries into optimized, secure SQL queries.

Key Guidelines:
- Always use parameterized queries (use $1, $2, etc. for PostgreSQL, ? for MySQL)
- Never use string concatenation for user input
- Prefer JOINs over subqueries when possible
- Use appropriate indexes (assume they exist on primary and foreign keys)
- Add LIMIT clauses to prevent huge result sets when appropriate
- Validate all table and column names against the schema
- Use proper quoting for identifiers if needed
- Consider SQL injection prevention
- Flag potentially destructive operations (DELETE, DROP, TRUNCATE)
- Suggest indexes if query performance might be poor

Always respond in valid JSON format with sql, explanation, confidence, and warnings fields.`;
  }

  /**
   * Parse LLM translation response
   */
  private parseTranslationResponse(content: string): TranslationResult {
    try {
      // Try to extract JSON from response
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const parsed = JSON.parse(jsonMatch[0]);
        return {
          sql: parsed.sql || '',
          explanation: parsed.explanation || '',
          confidence: parsed.confidence || 0.5,
          warnings: parsed.warnings || []
        };
      }

      // Fallback: try to extract SQL from code blocks
      const sqlMatch = content.match(/```sql\n([\s\S]*?)\n```/);
      if (sqlMatch) {
        return {
          sql: sqlMatch[1].trim(),
          explanation: content.replace(/```sql\n[\s\S]*?\n```/, '').trim(),
          confidence: 0.7,
          warnings: []
        };
      }

      // Last resort: assume entire content is SQL
      return {
        sql: content.trim(),
        explanation: 'Auto-generated SQL',
        confidence: 0.5,
        warnings: ['Could not parse structured response']
      };
    } catch (error) {
      throw new Error(`Failed to parse translation response: ${error}`);
    }
  }

  /**
   * Validate SQL against schema
   */
  private validateSQL(sql: string, schema: SchemaInfo): void {
    const sqlLower = sql.toLowerCase();

    // Check for destructive operations
    const destructiveOps = ['drop', 'truncate', 'delete'];
    for (const op of destructiveOps) {
      if (sqlLower.includes(op)) {
        throw new Error(`Destructive operation detected: ${op.toUpperCase()}`);
      }
    }

    // Extract table names from SQL
    const tablePattern = /(?:from|join)\s+([a-z_][a-z0-9_]*)/gi;
    const matches = sql.matchAll(tablePattern);

    const validTables = new Set(schema.tables.map((t) => t.name.toLowerCase()));

    for (const match of matches) {
      const tableName = match[1].toLowerCase();
      if (!validTables.has(tableName)) {
        throw new Error(`Table not found in schema: ${tableName}`);
      }
    }
  }

  /**
   * Optimize SQL query
   */
  async optimizeSQL(sql: string, schema?: SchemaInfo): Promise<string> {
    const wrappedFn = this.errorHandler.wrap(
      async () => {
        const schemaContext = schema ? this.buildSchemaContext(schema) : '';

        const prompt = `Optimize the following SQL query for performance:

SQL Query:
\`\`\`sql
${sql}
\`\`\`

${schemaContext ? `Schema Context:\n${schemaContext}\n` : ''}

Provide an optimized version of the query with explanations of improvements.`;

        const response = await this.llmBridge.generate({
          messages: [
            {
              role: 'system',
              content: 'You are a SQL performance optimization expert.'
            },
            {
              role: 'user',
              content: prompt
            }
          ],
          enableTools: false
        });

        // Extract optimized SQL from response
        const sqlMatch = response.content.match(/```sql\n([\s\S]*?)\n```/);
        return sqlMatch ? sqlMatch[1].trim() : sql;
      },
      {
        operation: 'optimizeSQL',
        component: 'NLQueryTranslator'
      }
    );

    const result = await wrappedFn();
    return result || sql;
  }

  /**
   * Suggest queries based on schema
   */
  async suggestQueries(schema: SchemaInfo, context?: string): Promise<string[]> {
    const wrappedFn = this.errorHandler.wrap(
      async () => {
        const schemaContext = this.buildSchemaContext(schema);

        const prompt = `Based on the following database schema, suggest 5 useful SQL queries that would provide valuable insights:

Database Schema:
${schemaContext}

${context ? `Context: ${context}\n` : ''}

Provide natural language descriptions of queries that would be useful for this database.`;

        const response = await this.llmBridge.generate({
          messages: [
            {
              role: 'system',
              content: 'You are a data analyst suggesting useful database queries.'
            },
            {
              role: 'user',
              content: prompt
            }
          ],
          enableTools: false
        });

        // Parse suggestions from response
        const lines = response.content.split('\n');
        return lines
          .filter((line) => line.match(/^\d+\.|^-/))
          .map((line) => line.replace(/^\d+\.\s*|-\s*/, '').trim())
          .filter((line) => line.length > 0);
      },
      {
        operation: 'suggestQueries',
        component: 'NLQueryTranslator'
      }
    );

    const result = await wrappedFn();
    return result || [];
  }
}
