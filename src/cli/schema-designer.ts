/**
 * Schema Designer
 * AI-assisted interactive schema design with migration generation
 * Commands: ai-shell design-schema, ai-shell validate-schema <file>
 */

import { AnthropicProvider } from '../llm/anthropic-provider';
import { DatabaseConnectionManager, DatabaseType } from './database-manager';
import { createLogger } from '../core/logger';
import { StateManager } from '../core/state-manager';
import * as fs from 'fs/promises';
import inquirer from 'inquirer';

interface SchemaDefinition {
  name: string;
  tables: TableDefinition[];
  relationships: Relationship[];
  indexes: IndexDefinition[];
  constraints: ConstraintDefinition[];
}

interface TableDefinition {
  name: string;
  columns: ColumnDefinition[];
  primaryKey: string[];
  comment?: string;
}

interface ColumnDefinition {
  name: string;
  type: string;
  nullable: boolean;
  default?: any;
  unique?: boolean;
  autoIncrement?: boolean;
  comment?: string;
}

interface Relationship {
  name: string;
  fromTable: string;
  toTable: string;
  fromColumn: string;
  toColumn: string;
  type: 'one-to-one' | 'one-to-many' | 'many-to-many';
  onDelete?: 'CASCADE' | 'SET NULL' | 'RESTRICT';
  onUpdate?: 'CASCADE' | 'SET NULL' | 'RESTRICT';
}

interface IndexDefinition {
  name: string;
  table: string;
  columns: string[];
  unique?: boolean;
  type?: 'btree' | 'hash' | 'gin' | 'gist';
}

interface ConstraintDefinition {
  name: string;
  table: string;
  type: 'check' | 'unique' | 'foreign_key';
  definition: string;
}

interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  suggestions: string[];
}

export class SchemaDesigner {
  private logger = createLogger('SchemaDesigner');
  private llmProvider: AnthropicProvider;

  constructor(
    private dbManager: DatabaseConnectionManager,
    private _stateManager: StateManager,
    apiKey: string
  ) {
    this.llmProvider = new AnthropicProvider({ apiKey });
  }

  /**
   * Interactive schema design
   */
  async designSchema(): Promise<SchemaDefinition> {
    this.logger.info('Starting interactive schema design');

    console.log('\n🎨 AI-Powered Schema Designer\n');

    // Get schema requirements from user
    const answers = await inquirer.prompt([
      {
        type: 'input',
        name: 'schemaName',
        message: 'Schema name:',
        validate: (input) => (input.trim() ? true : 'Schema name is required')
      },
      {
        type: 'input',
        name: 'description',
        message: 'Describe your schema (what data will it store?):'
      },
      {
        type: 'list',
        name: 'databaseType',
        message: 'Target database type:',
        choices: ['PostgreSQL', 'MySQL', 'SQLite', 'MongoDB']
      }
    ]);

    // Generate schema using AI
    const schema = await this.generateSchemaWithAI(
      answers.description,
      answers.databaseType.toLowerCase() as DatabaseType
    );

    schema.name = answers.schemaName;

    // Refine with user
    await this.refineSchema(schema);

    // Validate
    const validation = await this.validateSchema(schema);
    if (!validation.valid) {
      console.log('\n⚠️  Validation Issues:');
      validation.errors.forEach((err) => console.log(`   ❌ ${err}`));
    }

    // Save schema
    await this.saveSchema(schema);

    console.log('\n✅ Schema design complete!');

    return schema;
  }

  /**
   * Generate schema using AI
   */
  private async generateSchemaWithAI(
    description: string,
    databaseType: DatabaseType
  ): Promise<SchemaDefinition> {
    this.logger.info('Generating schema with AI', { databaseType });

    const prompt = this.buildSchemaPrompt(description, databaseType);

    const response = await this.llmProvider.generate({
      messages: [{ role: 'user', content: prompt }],
      maxTokens: 4096,
      temperature: 0.3
    });

    return this.parseSchemaResponse(response.content);
  }

  /**
   * Build schema generation prompt
   */
  private buildSchemaPrompt(description: string, databaseType: DatabaseType): string {
    return `You are a database schema design expert. Design a comprehensive database schema based on the following requirements.

Requirements:
${description}

Target Database: ${databaseType}

Create a complete schema design that includes:
1. Well-normalized tables with appropriate columns
2. Primary keys and foreign keys
3. Indexes for commonly queried fields
4. Appropriate constraints
5. Relationships between tables

Best practices to follow:
- Use appropriate data types for each field
- Add indexes for foreign keys and commonly searched fields
- Include created_at/updated_at timestamps where relevant
- Use appropriate naming conventions (snake_case for PostgreSQL/MySQL, camelCase for MongoDB)
- Consider performance and scalability

Return your design as JSON with this structure:
{
  "name": "schema_name",
  "tables": [
    {
      "name": "table_name",
      "columns": [
        {
          "name": "id",
          "type": "integer",
          "nullable": false,
          "autoIncrement": true,
          "comment": "Primary key"
        },
        ...
      ],
      "primaryKey": ["id"],
      "comment": "Table description"
    }
  ],
  "relationships": [
    {
      "name": "fk_name",
      "fromTable": "orders",
      "toTable": "users",
      "fromColumn": "user_id",
      "toColumn": "id",
      "type": "many-to-one",
      "onDelete": "CASCADE"
    }
  ],
  "indexes": [
    {
      "name": "idx_name",
      "table": "users",
      "columns": ["email"],
      "unique": true
    }
  ],
  "constraints": []
}`;
  }

  /**
   * Parse schema from AI response
   */
  private parseSchemaResponse(response: string): SchemaDefinition {
    try {
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        throw new Error('No valid JSON found in response');
      }

      const schema = JSON.parse(jsonMatch[0]);

      return {
        name: schema.name || 'untitled',
        tables: schema.tables || [],
        relationships: schema.relationships || [],
        indexes: schema.indexes || [],
        constraints: schema.constraints || []
      };
    } catch (error) {
      this.logger.error('Failed to parse schema response', error);
      throw new Error('Failed to parse schema from AI response');
    }
  }

  /**
   * Refine schema with user feedback
   */
  private async refineSchema(schema: SchemaDefinition): Promise<void> {
    console.log('\n📋 Generated Schema:');
    console.log(JSON.stringify(schema, null, 2));

    const { shouldRefine } = await inquirer.prompt([
      {
        type: 'confirm',
        name: 'shouldRefine',
        message: 'Would you like to refine this schema?',
        default: false
      }
    ]);

    if (!shouldRefine) {
      return;
    }

    const { refinements } = await inquirer.prompt([
      {
        type: 'input',
        name: 'refinements',
        message: 'What changes would you like to make?'
      }
    ]);

    if (refinements.trim()) {
      const refined = await this.refineSchemaWithAI(schema, refinements);
      Object.assign(schema, refined);

      // Ask if further refinement needed
      await this.refineSchema(schema);
    }
  }

  /**
   * Refine schema using AI
   */
  private async refineSchemaWithAI(
    schema: SchemaDefinition,
    refinements: string
  ): Promise<SchemaDefinition> {
    const prompt = `Refine the following database schema based on user feedback.

Current Schema:
${JSON.stringify(schema, null, 2)}

User Feedback:
${refinements}

Return the refined schema in the same JSON format.`;

    const response = await this.llmProvider.generate({
      messages: [{ role: 'user', content: prompt }],
      maxTokens: 4096,
      temperature: 0.3
    });

    return this.parseSchemaResponse(response.content);
  }

  /**
   * Validate schema
   */
  async validateSchema(schema: SchemaDefinition): Promise<ValidationResult> {
    this.logger.info('Validating schema', { schemaName: schema.name });

    const errors: string[] = [];
    const warnings: string[] = [];
    const suggestions: string[] = [];

    // Check for empty tables
    if (schema.tables.length === 0) {
      errors.push('Schema has no tables defined');
    }

    // Validate each table
    schema.tables.forEach((table) => {
      // Check for columns
      if (table.columns.length === 0) {
        errors.push(`Table '${table.name}' has no columns`);
      }

      // Check for primary key
      if (!table.primaryKey || table.primaryKey.length === 0) {
        warnings.push(`Table '${table.name}' has no primary key`);
      }

      // Check for timestamps
      const hasCreatedAt = table.columns.some((c) => c.name === 'created_at');
      const hasUpdatedAt = table.columns.some((c) => c.name === 'updated_at');

      if (!hasCreatedAt || !hasUpdatedAt) {
        suggestions.push(`Consider adding timestamp fields to '${table.name}'`);
      }

      // Validate columns
      table.columns.forEach((column) => {
        // Check for valid data types
        if (!column.type) {
          errors.push(`Column '${table.name}.${column.name}' has no data type`);
        }

        // Check nullable on primary key
        if (table.primaryKey.includes(column.name) && column.nullable) {
          errors.push(`Primary key column '${table.name}.${column.name}' cannot be nullable`);
        }
      });
    });

    // Validate relationships
    schema.relationships.forEach((rel) => {
      const fromTable = schema.tables.find((t) => t.name === rel.fromTable);
      const toTable = schema.tables.find((t) => t.name === rel.toTable);

      if (!fromTable) {
        errors.push(`Relationship '${rel.name}' references non-existent table '${rel.fromTable}'`);
      }

      if (!toTable) {
        errors.push(`Relationship '${rel.name}' references non-existent table '${rel.toTable}'`);
      }

      // Check if columns exist
      if (fromTable && !fromTable.columns.find((c) => c.name === rel.fromColumn)) {
        errors.push(
          `Relationship '${rel.name}' references non-existent column '${rel.fromTable}.${rel.fromColumn}'`
        );
      }

      if (toTable && !toTable.columns.find((c) => c.name === rel.toColumn)) {
        errors.push(
          `Relationship '${rel.name}' references non-existent column '${rel.toTable}.${rel.toColumn}'`
        );
      }
    });

    // Validate indexes
    schema.indexes.forEach((index) => {
      const table = schema.tables.find((t) => t.name === index.table);

      if (!table) {
        errors.push(`Index '${index.name}' references non-existent table '${index.table}'`);
      } else {
        index.columns.forEach((col) => {
          if (!table.columns.find((c) => c.name === col)) {
            errors.push(
              `Index '${index.name}' references non-existent column '${index.table}.${col}'`
            );
          }
        });
      }
    });

    // Add performance suggestions
    if (schema.relationships.length > 0) {
      suggestions.push('Consider adding indexes on foreign key columns for better performance');
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings,
      suggestions
    };
  }

  /**
   * Generate migrations from schema
   */
  async generateMigrations(
    schema: SchemaDefinition,
    databaseType: DatabaseType
  ): Promise<string> {
    this.logger.info('Generating migrations', { schemaName: schema.name, databaseType });

    let migration = '';

    switch (databaseType) {
      case DatabaseType.POSTGRESQL:
        migration = this.generatePostgreSQLMigration(schema);
        break;

      case DatabaseType.MYSQL:
        migration = this.generateMySQLMigration(schema);
        break;

      case DatabaseType.SQLITE:
        migration = this.generateSQLiteMigration(schema);
        break;

      case DatabaseType.MONGODB:
        migration = this.generateMongoDBMigration(schema);
        break;
    }

    return migration;
  }

  /**
   * Generate PostgreSQL migration
   */
  private generatePostgreSQLMigration(schema: SchemaDefinition): string {
    let sql = `-- Migration: Create ${schema.name} schema\n\n`;

    // Create tables
    schema.tables.forEach((table) => {
      sql += `CREATE TABLE ${table.name} (\n`;

      const columnDefs = table.columns.map((col) => {
        let def = `  ${col.name} ${col.type}`;

        if (col.autoIncrement) def += ' SERIAL';
        if (!col.nullable) def += ' NOT NULL';
        if (col.unique) def += ' UNIQUE';
        if (col.default !== undefined) def += ` DEFAULT ${col.default}`;

        return def;
      });

      sql += columnDefs.join(',\n');

      // Add primary key
      if (table.primaryKey.length > 0) {
        sql += `,\n  PRIMARY KEY (${table.primaryKey.join(', ')})`;
      }

      sql += '\n);\n\n';
    });

    // Create indexes
    schema.indexes.forEach((index) => {
      const unique = index.unique ? 'UNIQUE ' : '';
      sql += `CREATE ${unique}INDEX ${index.name} ON ${index.table} (${index.columns.join(', ')});\n`;
    });

    sql += '\n';

    // Add foreign keys
    schema.relationships.forEach((rel) => {
      sql += `ALTER TABLE ${rel.fromTable}\n`;
      sql += `  ADD CONSTRAINT ${rel.name}\n`;
      sql += `  FOREIGN KEY (${rel.fromColumn})\n`;
      sql += `  REFERENCES ${rel.toTable} (${rel.toColumn})`;

      if (rel.onDelete) sql += `\n  ON DELETE ${rel.onDelete}`;
      if (rel.onUpdate) sql += `\n  ON UPDATE ${rel.onUpdate}`;

      sql += ';\n\n';
    });

    return sql;
  }

  /**
   * Generate MySQL migration
   */
  private generateMySQLMigration(schema: SchemaDefinition): string {
    // Similar to PostgreSQL but with MySQL syntax
    return this.generatePostgreSQLMigration(schema).replace(/SERIAL/g, 'AUTO_INCREMENT');
  }

  /**
   * Generate SQLite migration
   */
  private generateSQLiteMigration(schema: SchemaDefinition): string {
    // Similar to PostgreSQL but with SQLite syntax limitations
    return this.generatePostgreSQLMigration(schema)
      .replace(/SERIAL/g, 'INTEGER')
      .replace(/CASCADE/g, 'NO ACTION');
  }

  /**
   * Generate MongoDB migration
   */
  private generateMongoDBMigration(schema: SchemaDefinition): string {
    let script = `// MongoDB Schema Validation for ${schema.name}\n\n`;

    schema.tables.forEach((table) => {
      script += `db.createCollection("${table.name}", {\n`;
      script += `  validator: {\n`;
      script += `    $jsonSchema: {\n`;
      script += `      bsonType: "object",\n`;
      script += `      required: [${table.columns.filter((c) => !c.nullable).map((c) => `"${c.name}"`).join(', ')}],\n`;
      script += `      properties: {\n`;

      table.columns.forEach((col) => {
        script += `        ${col.name}: { bsonType: "${this.mapToMongoType(col.type)}" },\n`;
      });

      script += `      }\n`;
      script += `    }\n`;
      script += `  }\n`;
      script += `});\n\n`;

      // Add indexes
      const tableIndexes = schema.indexes.filter((idx) => idx.table === table.name);
      tableIndexes.forEach((index) => {
        const keys = index.columns.map((col) => `${col}: 1`).join(', ');
        const unique = index.unique ? ', { unique: true }' : '';
        script += `db.${table.name}.createIndex({ ${keys} }${unique});\n`;
      });

      script += '\n';
    });

    return script;
  }

  /**
   * Map SQL type to MongoDB type
   */
  private mapToMongoType(sqlType: string): string {
    const type = sqlType.toLowerCase();

    if (type.includes('int')) return 'int';
    if (type.includes('char') || type.includes('text')) return 'string';
    if (type.includes('bool')) return 'bool';
    if (type.includes('date') || type.includes('time')) return 'date';
    if (type.includes('decimal') || type.includes('float')) return 'double';

    return 'string';
  }

  /**
   * Save schema to file
   */
  async saveSchema(schema: SchemaDefinition, filePath?: string): Promise<string> {
    const path = filePath || `./schemas/${schema.name}.json`;

    await fs.mkdir('./schemas', { recursive: true });
    await fs.writeFile(path, JSON.stringify(schema, null, 2));

    this.logger.info('Schema saved', { path });

    return path;
  }

  /**
   * Load schema from file
   */
  async loadSchema(filePath: string): Promise<SchemaDefinition> {
    const content = await fs.readFile(filePath, 'utf-8');
    const schema = JSON.parse(content);

    this.logger.info('Schema loaded', { filePath });

    return schema;
  }

  /**
   * Apply schema to database
   */
  async applySchema(schema: SchemaDefinition, connectionName?: string): Promise<void> {
    const connection = connectionName
      ? this.dbManager.getConnection(connectionName)
      : this.dbManager.getActive();

    if (!connection) {
      throw new Error('No active connection');
    }

    this.logger.info('Applying schema to database', {
      schema: schema.name,
      database: connection.config.database
    });

    // Generate migration
    const migration = await this.generateMigrations(schema, connection.type);

    // Execute migration
    const statements = migration.split(';').filter((s) => s.trim());

    for (const statement of statements) {
      try {
        await this.dbManager.executeQuery(statement);
      } catch (error) {
        this.logger.error('Failed to execute statement', error, { statement });
        throw error;
      }
    }

    this.logger.info('Schema applied successfully');
  }
}
