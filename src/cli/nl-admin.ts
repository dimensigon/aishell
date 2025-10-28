#!/usr/bin/env node
/**
 * Natural Language Database Admin CLI
 * Main entry point for ai-shell CLI commands
 */

import { Command } from 'commander';
import { DatabaseConnectionManager, DatabaseType, ConnectionConfig } from './database-manager';
import { NLQueryTranslator } from './nl-query-translator';
import { SchemaInspector } from './schema-inspector';
import { QueryExecutor } from './query-executor';
import { ResultFormatter, OutputFormat } from './result-formatter';
import { StateManager } from '../core/state-manager';
import { ErrorHandler } from '../core/error-handler';
import { LLMMCPBridge } from '../llm/mcp-bridge';
import { MCPClient } from '../mcp/client';
import { AnthropicProvider } from '../llm/anthropic-provider';
import inquirer from 'inquirer';
import chalk from 'chalk';

/**
 * CLI Application
 */
class NLAdminCLI {
  private program: Command;
  private stateManager: StateManager;
  private errorHandler: ErrorHandler;
  private connectionManager: DatabaseConnectionManager;
  private queryExecutor: QueryExecutor;
  private formatter: ResultFormatter;
  private llmBridge?: LLMMCPBridge;
  private translator?: NLQueryTranslator;
  private inspector?: SchemaInspector;

  constructor() {
    this.program = new Command();
    this.stateManager = new StateManager({
      persistencePath: './.ai-shell-state',
      enablePersistence: true
    });
    this.errorHandler = new ErrorHandler();
    this.connectionManager = new DatabaseConnectionManager(this.stateManager);
    this.queryExecutor = new QueryExecutor(this.connectionManager, this.errorHandler);
    this.formatter = new ResultFormatter();

    this.setupCommands();
  }

  /**
   * Initialize LLM components
   */
  private async initializeLLM(): Promise<void> {
    if (this.llmBridge) {
      return;
    }

    try {
      // Initialize MCP client and LLM provider
      const mcpClient = new MCPClient({
        servers: [],
        timeout: 30000
      });
      const llmProvider = new AnthropicProvider({
        apiKey: process.env.ANTHROPIC_API_KEY || ''
      });

      this.llmBridge = new LLMMCPBridge(llmProvider, mcpClient);
      this.translator = new NLQueryTranslator(this.llmBridge, this.errorHandler);
      this.inspector = new SchemaInspector(
        this.connectionManager,
        this.llmBridge,
        this.errorHandler
      );
    } catch (error) {
      console.error(
        chalk.red('Failed to initialize LLM components:'),
        error instanceof Error ? error.message : error
      );
      console.log(
        chalk.yellow('Some features requiring LLM will be disabled.')
      );
    }
  }

  /**
   * Setup CLI commands
   */
  private setupCommands(): void {
    this.program
      .name('ai-shell')
      .description('AI-powered natural language database administration')
      .version('1.0.0');

    // Query command
    this.program
      .command('query <nl-query>')
      .description('Execute natural language query')
      .option('-f, --format <format>', 'Output format (table, json, csv, markdown)', 'table')
      .option('-l, --limit <number>', 'Limit number of results', '100')
      .option('--dry-run', 'Show query without executing')
      .action(async (nlQuery, options) => {
        await this.handleQuery(nlQuery, options);
      });

    // Database connection commands
    const dbCommand = this.program
      .command('db')
      .description('Database connection management');

    dbCommand
      .command('connect <connection-string>')
      .description('Connect to database')
      .option('-n, --name <name>', 'Connection name', 'default')
      .option('-t, --type <type>', 'Database type (postgresql, mysql, sqlite, mongodb)', 'postgresql')
      .action(async (connectionString, options) => {
        await this.handleConnect(connectionString, options);
      });

    dbCommand
      .command('list')
      .description('List active connections')
      .action(async () => {
        await this.handleListConnections();
      });

    dbCommand
      .command('use <name>')
      .description('Switch active connection')
      .action(async (name) => {
        await this.handleUseConnection(name);
      });

    dbCommand
      .command('disconnect [name]')
      .description('Disconnect from database')
      .action(async (name) => {
        await this.handleDisconnect(name);
      });

    // Schema commands
    const schemaCommand = this.program
      .command('schema')
      .description('Database schema exploration');

    schemaCommand
      .command('explore <nl-query>')
      .description('Explore schema using natural language')
      .action(async (nlQuery) => {
        await this.handleSchemaExplore(nlQuery);
      });

    schemaCommand
      .command('describe <table>')
      .description('Describe table structure')
      .action(async (table) => {
        await this.handleSchemaDescribe(table);
      });

    schemaCommand
      .command('diagram')
      .description('Generate schema diagram')
      .action(async () => {
        await this.handleSchemaDiagram();
      });

    schemaCommand
      .command('search <keyword>')
      .description('Search for columns by keyword')
      .action(async (keyword) => {
        await this.handleSchemaSearch(keyword);
      });

    // Data commands
    const dataCommand = this.program
      .command('data')
      .description('Data management operations');

    dataCommand
      .command('export <table>')
      .description('Export table data')
      .option('-f, --format <format>', 'Output format (json, csv)', 'csv')
      .option('-o, --output <file>', 'Output file')
      .action(async (table, options) => {
        await this.handleDataExport(table, options);
      });
  }

  /**
   * Handle query command
   */
  private async handleQuery(nlQuery: string, options: any): Promise<void> {
    try {
      await this.initializeLLM();

      if (!this.translator) {
        throw new Error('LLM translation not available');
      }

      console.log(chalk.blue('Translating natural language query...'));

      // Get schema info
      const connection = this.connectionManager.getActive();
      if (!connection) {
        throw new Error('No active database connection. Use "ai-shell db connect" first.');
      }

      // Get schema
      const tables = await this.inspector!.getAllTables();
      const schema = { tables, relationships: [] };

      // Translate query
      const translation = await this.translator.translate(
        nlQuery,
        schema,
        connection.type
      );

      console.log(chalk.green('Generated SQL:'));
      console.log(chalk.gray(translation.sql));
      console.log(chalk.gray(`\nExplanation: ${translation.explanation}`));
      console.log(chalk.gray(`Confidence: ${(translation.confidence * 100).toFixed(0)}%`));

      if (translation.warnings.length > 0) {
        console.log(chalk.yellow('\nWarnings:'));
        translation.warnings.forEach((w) => console.log(chalk.yellow(`  - ${w}`)));
      }

      // Execute if not dry run
      if (!options.dryRun) {
        const confirm = await inquirer.prompt([
          {
            type: 'confirm',
            name: 'execute',
            message: 'Execute this query?',
            default: true
          }
        ]);

        if (confirm.execute) {
          console.log(chalk.blue('\nExecuting query...'));

          const result = await this.queryExecutor.execute(translation.sql, {
            maxRows: parseInt(options.limit)
          });

          // Format and display results
          const formatted = this.formatter.format(
            result.rows,
            options.format as OutputFormat
          );
          console.log('\n' + formatted);

          console.log('\n' + this.formatter.formatExecutionSummary(result));
        }
      }
    } catch (error) {
      console.error(this.formatter.formatError(error as Error));
      process.exit(1);
    }
  }

  /**
   * Handle connect command
   */
  private async handleConnect(connectionString: string, options: any): Promise<void> {
    try {
      console.log(chalk.blue(`Connecting to ${options.type} database...`));

      const config: ConnectionConfig = {
        name: options.name,
        type: options.type as DatabaseType,
        connectionString,
        database: '' // Will be parsed from connection string
      };

      await this.connectionManager.connect(config);

      console.log(this.formatter.formatSuccess(`Connected to ${options.name}`));
    } catch (error) {
      console.error(this.formatter.formatError(error as Error));
      process.exit(1);
    }
  }

  /**
   * Handle list connections command
   */
  private async handleListConnections(): Promise<void> {
    try {
      const connections = this.connectionManager.listConnections();

      if (connections.length === 0) {
        console.log(chalk.yellow('No active connections'));
        return;
      }

      const formatted = this.formatter.format(
        connections.map((conn) => ({
          Name: conn.name,
          Type: conn.type,
          Database: conn.database,
          Host: conn.host || 'N/A',
          Active: conn.isActive ? '✓' : ''
        })),
        OutputFormat.TABLE
      );

      console.log(formatted);
    } catch (error) {
      console.error(this.formatter.formatError(error as Error));
      process.exit(1);
    }
  }

  /**
   * Handle use connection command
   */
  private async handleUseConnection(name: string): Promise<void> {
    try {
      await this.connectionManager.switchActive(name);
      console.log(this.formatter.formatSuccess(`Switched to connection: ${name}`));
    } catch (error) {
      console.error(this.formatter.formatError(error as Error));
      process.exit(1);
    }
  }

  /**
   * Handle disconnect command
   */
  private async handleDisconnect(name?: string): Promise<void> {
    try {
      if (name) {
        await this.connectionManager.disconnect(name);
        console.log(this.formatter.formatSuccess(`Disconnected from ${name}`));
      } else {
        await this.connectionManager.disconnectAll();
        console.log(this.formatter.formatSuccess('Disconnected from all databases'));
      }
    } catch (error) {
      console.error(this.formatter.formatError(error as Error));
      process.exit(1);
    }
  }

  /**
   * Handle schema explore command
   */
  private async handleSchemaExplore(nlQuery: string): Promise<void> {
    try {
      await this.initializeLLM();

      if (!this.inspector) {
        throw new Error('Schema inspector not available');
      }

      console.log(chalk.blue('Exploring schema...'));

      const tables = await this.inspector.exploreTables(nlQuery);

      if (tables.length === 0) {
        console.log(chalk.yellow('No tables found matching your query'));
        return;
      }

      for (const table of tables) {
        console.log(chalk.green(`\nTable: ${table.name}`));

        const formatted = this.formatter.format(
          table.columns.map((col) => ({
            Column: col.name,
            Type: col.type,
            Nullable: col.nullable ? 'YES' : 'NO',
            Description: col.description || ''
          })),
          OutputFormat.TABLE
        );

        console.log(formatted);

        if (table.primaryKey) {
          console.log(chalk.gray(`Primary Key: ${table.primaryKey.join(', ')}`));
        }
      }
    } catch (error) {
      console.error(this.formatter.formatError(error as Error));
      process.exit(1);
    }
  }

  /**
   * Handle schema describe command
   */
  private async handleSchemaDescribe(tableName: string): Promise<void> {
    try {
      await this.initializeLLM();

      if (!this.inspector) {
        throw new Error('Schema inspector not available');
      }

      const table = await this.inspector.describeTable(tableName);

      if (!table) {
        console.log(chalk.yellow(`Table not found: ${tableName}`));
        return;
      }

      console.log(chalk.green(`\nTable: ${table.name}`));

      const formatted = this.formatter.format(
        table.columns.map((col) => ({
          Column: col.name,
          Type: col.type,
          Nullable: col.nullable ? 'YES' : 'NO',
          Default: col.defaultValue || '',
          Description: col.description || ''
        })),
        OutputFormat.TABLE
      );

      console.log(formatted);

      if (table.primaryKey) {
        console.log(chalk.gray(`\nPrimary Key: ${table.primaryKey.join(', ')}`));
      }

      // Show relationships
      const relationships = await this.inspector.findRelationships(tableName);
      if (relationships.length > 0) {
        console.log(chalk.cyan('\nRelationships:'));
        relationships.forEach((rel) => {
          console.log(
            chalk.gray(`  ${rel.fromTable}.${rel.fromColumn} → ${rel.toTable}.${rel.toColumn}`)
          );
        });
      }
    } catch (error) {
      console.error(this.formatter.formatError(error as Error));
      process.exit(1);
    }
  }

  /**
   * Handle schema diagram command
   */
  private async handleSchemaDiagram(): Promise<void> {
    try {
      await this.initializeLLM();

      if (!this.inspector) {
        throw new Error('Schema inspector not available');
      }

      console.log(chalk.blue('Generating schema diagram...'));

      const diagram = await this.inspector.generateSchemaDiagram();

      console.log(chalk.green('\nMermaid ERD:'));
      console.log(diagram);
      console.log(
        chalk.gray(
          '\nCopy the diagram above and paste it into https://mermaid.live to visualize'
        )
      );
    } catch (error) {
      console.error(this.formatter.formatError(error as Error));
      process.exit(1);
    }
  }

  /**
   * Handle schema search command
   */
  private async handleSchemaSearch(keyword: string): Promise<void> {
    try {
      await this.initializeLLM();

      if (!this.inspector) {
        throw new Error('Schema inspector not available');
      }

      console.log(chalk.blue(`Searching for columns matching "${keyword}"...`));

      const columns = await this.inspector.searchColumns(keyword);

      if (columns.length === 0) {
        console.log(chalk.yellow('No columns found'));
        return;
      }

      const formatted = this.formatter.format(
        columns.map((col) => ({
          Location: col.description,
          Type: col.type,
          Nullable: col.nullable ? 'YES' : 'NO'
        })),
        OutputFormat.TABLE
      );

      console.log(formatted);
    } catch (error) {
      console.error(this.formatter.formatError(error as Error));
      process.exit(1);
    }
  }

  /**
   * Handle data export command
   */
  private async handleDataExport(tableName: string, options: any): Promise<void> {
    try {
      console.log(chalk.blue(`Exporting data from ${tableName}...`));

      const sql = `SELECT * FROM ${tableName}`;
      const result = await this.queryExecutor.execute(sql);

      const format = options.format === 'json' ? OutputFormat.JSON : OutputFormat.CSV;
      const formatted = this.formatter.format(result.rows, format);

      if (options.output) {
        const fs = await import('fs/promises');
        await fs.writeFile(options.output, formatted);
        console.log(this.formatter.formatSuccess(`Data exported to ${options.output}`));
      } else {
        console.log(formatted);
      }
    } catch (error) {
      console.error(this.formatter.formatError(error as Error));
      process.exit(1);
    }
  }

  /**
   * Run CLI
   */
  async run(args: string[]): Promise<void> {
    try {
      await this.program.parseAsync(args);
    } catch (error) {
      console.error(this.formatter.formatError(error as Error));
      process.exit(1);
    }
  }
}

// Run CLI
const cli = new NLAdminCLI();
cli.run(process.argv);
