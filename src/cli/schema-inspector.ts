/**
 * Schema Inspector
 * Inspects database schema using natural language and SQL introspection
 */

import { DatabaseConnectionManager, DatabaseType } from './db-connection-manager';
import { LLMMCPBridge } from '../llm/mcp-bridge';
import { ErrorHandler } from '../core/error-handler';
import { TableInfo, ColumnInfo, Relationship } from './nl-query-translator';

/**
 * Schema Inspector
 */
export class SchemaInspector {
  constructor(
    private connectionManager: DatabaseConnectionManager,
    private llmBridge: LLMMCPBridge,
    private errorHandler: ErrorHandler
  ) {}

  /**
   * Explore tables using natural language query
   */
  async exploreTables(nlQuery: string): Promise<TableInfo[]> {
    return this.errorHandler.wrap(
      async () => {
        // Get all tables first
        const allTables = await this.getAllTables();

        // Use LLM to filter and find relevant tables
        const prompt = `Given the following database tables, which tables are relevant to this query: "${nlQuery}"?

Available Tables:
${allTables.map((t) => `- ${t.name}${t.description ? `: ${t.description}` : ''}`).join('\n')}

Return a JSON array of relevant table names: ["table1", "table2", ...]`;

        const response = await this.llmBridge.generate({
          messages: [
            {
              role: 'system',
              content: 'You are a database expert helping users find relevant tables.'
            },
            {
              role: 'user',
              content: prompt
            }
          ],
          enableTools: false
        });

        // Parse table names from response
        const tableNames = this.parseTableNames(response.content);

        // Get detailed info for relevant tables
        const relevantTables: TableInfo[] = [];
        for (const name of tableNames) {
          const table = await this.describeTable(name);
          if (table) {
            relevantTables.push(table);
          }
        }

        return relevantTables;
      },
      {
        operation: 'exploreTables',
        component: 'SchemaInspector'
      }
    )();
  }

  /**
   * Describe table structure
   */
  async describeTable(tableName: string): Promise<TableInfo | null> {
    return this.errorHandler.wrap(
      async () => {
        const connection = this.connectionManager.getActive();

        if (!connection) {
          throw new Error('No active connection');
        }

        switch (connection.type) {
          case DatabaseType.POSTGRESQL:
            return await this.describePostgreSQLTable(tableName);

          case DatabaseType.MYSQL:
            return await this.describeMySQLTable(tableName);

          case DatabaseType.SQLITE:
            return await this.describeSQLiteTable(tableName);

          default:
            throw new Error(`Unsupported database type: ${connection.type}`);
        }
      },
      {
        operation: 'describeTable',
        component: 'SchemaInspector'
      }
    )();
  }

  /**
   * Describe PostgreSQL table
   */
  private async describePostgreSQLTable(tableName: string): Promise<TableInfo> {
    const sql = `
      SELECT
        c.column_name,
        c.data_type,
        c.is_nullable,
        c.column_default,
        pgd.description
      FROM information_schema.columns c
      LEFT JOIN pg_catalog.pg_statio_all_tables st ON c.table_name = st.relname
      LEFT JOIN pg_catalog.pg_description pgd ON pgd.objoid = st.relid AND pgd.objsubid = c.ordinal_position
      WHERE c.table_name = $1
      ORDER BY c.ordinal_position;
    `;

    const rows = await this.connectionManager.executeQuery(sql, [tableName]);

    const columns: ColumnInfo[] = rows.map((row) => ({
      name: row.column_name,
      type: row.data_type,
      nullable: row.is_nullable === 'YES',
      defaultValue: row.column_default,
      description: row.description
    }));

    // Get primary key
    const pkSql = `
      SELECT a.attname
      FROM pg_index i
      JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
      WHERE i.indrelid = $1::regclass AND i.indisprimary;
    `;

    const pkRows = await this.connectionManager.executeQuery(pkSql, [tableName]);
    const primaryKey = pkRows.map((row) => row.attname);

    return {
      name: tableName,
      columns,
      primaryKey: primaryKey.length > 0 ? primaryKey : undefined
    };
  }

  /**
   * Describe MySQL table
   */
  private async describeMySQLTable(tableName: string): Promise<TableInfo> {
    const sql = 'DESCRIBE ??';
    const rows = await this.connectionManager.executeQuery(sql, [tableName]);

    const columns: ColumnInfo[] = rows.map((row: any) => ({
      name: row.Field,
      type: row.Type,
      nullable: row.Null === 'YES',
      defaultValue: row.Default
    }));

    const primaryKey = rows
      .filter((row: any) => row.Key === 'PRI')
      .map((row: any) => row.Field);

    return {
      name: tableName,
      columns,
      primaryKey: primaryKey.length > 0 ? primaryKey : undefined
    };
  }

  /**
   * Describe SQLite table
   */
  private async describeSQLiteTable(tableName: string): Promise<TableInfo> {
    const sql = `PRAGMA table_info(${tableName})`;
    const rows = await this.connectionManager.executeQuery(sql);

    const columns: ColumnInfo[] = rows.map((row: any) => ({
      name: row.name,
      type: row.type,
      nullable: row.notnull === 0,
      defaultValue: row.dflt_value
    }));

    const primaryKey = rows
      .filter((row: any) => row.pk > 0)
      .map((row: any) => row.name);

    return {
      name: tableName,
      columns,
      primaryKey: primaryKey.length > 0 ? primaryKey : undefined
    };
  }

  /**
   * Find relationships for a table
   */
  async findRelationships(tableName: string): Promise<Relationship[]> {
    return this.errorHandler.wrap(
      async () => {
        const connection = this.connectionManager.getActive();

        if (!connection) {
          throw new Error('No active connection');
        }

        switch (connection.type) {
          case DatabaseType.POSTGRESQL:
            return await this.findPostgreSQLRelationships(tableName);

          case DatabaseType.MYSQL:
            return await this.findMySQLRelationships(tableName);

          case DatabaseType.SQLITE:
            return await this.findSQLiteRelationships(tableName);

          default:
            throw new Error(`Unsupported database type: ${connection.type}`);
        }
      },
      {
        operation: 'findRelationships',
        component: 'SchemaInspector'
      }
    )();
  }

  /**
   * Find PostgreSQL foreign key relationships
   */
  private async findPostgreSQLRelationships(tableName: string): Promise<Relationship[]> {
    const sql = `
      SELECT
        tc.table_name AS from_table,
        kcu.column_name AS from_column,
        ccu.table_name AS to_table,
        ccu.column_name AS to_column
      FROM information_schema.table_constraints AS tc
      JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
      JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
      WHERE tc.constraint_type = 'FOREIGN KEY'
        AND (tc.table_name = $1 OR ccu.table_name = $1);
    `;

    const rows = await this.connectionManager.executeQuery(sql, [tableName]);

    return rows.map((row) => ({
      fromTable: row.from_table,
      fromColumn: row.from_column,
      toTable: row.to_table,
      toColumn: row.to_column,
      type: 'one-to-many' as const
    }));
  }

  /**
   * Find MySQL foreign key relationships
   */
  private async findMySQLRelationships(tableName: string): Promise<Relationship[]> {
    const connection = this.connectionManager.getActive();
    if (!connection) throw new Error('No active connection');

    const sql = `
      SELECT
        TABLE_NAME AS from_table,
        COLUMN_NAME AS from_column,
        REFERENCED_TABLE_NAME AS to_table,
        REFERENCED_COLUMN_NAME AS to_column
      FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
      WHERE REFERENCED_TABLE_NAME IS NOT NULL
        AND (TABLE_NAME = ? OR REFERENCED_TABLE_NAME = ?)
        AND TABLE_SCHEMA = ?;
    `;

    const rows = await this.connectionManager.executeQuery(sql, [
      tableName,
      tableName,
      connection.config.database
    ]);

    return rows.map((row: any) => ({
      fromTable: row.from_table,
      fromColumn: row.from_column,
      toTable: row.to_table,
      toColumn: row.to_column,
      type: 'one-to-many' as const
    }));
  }

  /**
   * Find SQLite foreign key relationships
   */
  private async findSQLiteRelationships(tableName: string): Promise<Relationship[]> {
    const sql = `PRAGMA foreign_key_list(${tableName})`;
    const rows = await this.connectionManager.executeQuery(sql);

    return rows.map((row: any) => ({
      fromTable: tableName,
      fromColumn: row.from,
      toTable: row.table,
      toColumn: row.to,
      type: 'one-to-many' as const
    }));
  }

  /**
   * Search for columns matching a keyword
   */
  async searchColumns(keyword: string): Promise<ColumnInfo[]> {
    return this.errorHandler.wrap(
      async () => {
        const tables = await this.getAllTables();
        const matchingColumns: ColumnInfo[] = [];

        for (const table of tables) {
          for (const column of table.columns) {
            if (
              column.name.toLowerCase().includes(keyword.toLowerCase()) ||
              column.description?.toLowerCase().includes(keyword.toLowerCase())
            ) {
              matchingColumns.push({
                ...column,
                description: `${table.name}.${column.name}${
                  column.description ? `: ${column.description}` : ''
                }`
              });
            }
          }
        }

        return matchingColumns;
      },
      {
        operation: 'searchColumns',
        component: 'SchemaInspector'
      }
    )();
  }

  /**
   * Get all tables in database
   */
  async getAllTables(): Promise<TableInfo[]> {
    const connection = this.connectionManager.getActive();

    if (!connection) {
      throw new Error('No active connection');
    }

    let tableNames: string[] = [];

    switch (connection.type) {
      case DatabaseType.POSTGRESQL:
        const pgRows = await this.connectionManager.executeQuery(
          "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        );
        tableNames = pgRows.map((row: any) => row.tablename);
        break;

      case DatabaseType.MYSQL:
        const mysqlRows = await this.connectionManager.executeQuery('SHOW TABLES');
        const key = Object.keys(mysqlRows[0])[0];
        tableNames = mysqlRows.map((row: any) => row[key]);
        break;

      case DatabaseType.SQLITE:
        const sqliteRows = await this.connectionManager.executeQuery(
          "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        );
        tableNames = sqliteRows.map((row: any) => row.name);
        break;

      default:
        throw new Error(`Unsupported database type: ${connection.type}`);
    }

    // Get detailed info for each table
    const tables: TableInfo[] = [];
    for (const name of tableNames) {
      const table = await this.describeTable(name);
      if (table) {
        tables.push(table);
      }
    }

    return tables;
  }

  /**
   * Parse table names from LLM response
   */
  private parseTableNames(content: string): string[] {
    try {
      // Try to parse as JSON array
      const jsonMatch = content.match(/\[[\s\S]*?\]/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }

      // Fallback: extract table names from text
      const lines = content.split('\n');
      return lines
        .filter((line) => line.match(/^-\s+\w+/) || line.match(/^\d+\.\s+\w+/))
        .map((line) => line.replace(/^-\s+|\d+\.\s+/, '').trim())
        .filter((name) => name.length > 0);
    } catch (error) {
      return [];
    }
  }

  /**
   * Generate schema diagram (Mermaid format)
   */
  async generateSchemaDiagram(): Promise<string> {
    const tables = await this.getAllTables();
    const relationships: Relationship[] = [];

    // Collect all relationships
    for (const table of tables) {
      const rels = await this.findRelationships(table.name);
      relationships.push(...rels);
    }

    // Generate Mermaid ERD
    let diagram = 'erDiagram\n';

    // Add tables
    for (const table of tables) {
      diagram += `  ${table.name} {\n`;
      for (const column of table.columns) {
        const pk = table.primaryKey?.includes(column.name) ? 'PK' : '';
        diagram += `    ${column.type} ${column.name} ${pk}\n`;
      }
      diagram += '  }\n';
    }

    // Add relationships
    for (const rel of relationships) {
      diagram += `  ${rel.fromTable} ||--o{ ${rel.toTable} : "${rel.fromColumn}"\n`;
    }

    return diagram;
  }
}
