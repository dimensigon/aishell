/**
 * MongoDB CLI Commands Registration
 * Registers all MongoDB-specific commands with Commander
 */

import { Command } from 'commander';
import { StateManager } from '../core/state-manager';
import { MongoDBCLI } from './mongodb-cli';
import chalk from 'chalk';

/**
 * Register MongoDB commands
 */
export function registerMongoDBCommands(program: Command, stateManager: StateManager): void {
  const mongoCLI = new MongoDBCLI(stateManager);

  const mongoCommand = program
    .command('mongo')
    .description('MongoDB-specific database commands');

  // mongo connect
  mongoCommand
    .command('connect <connection-string>')
    .description('Connect to MongoDB database')
    .option('-n, --name <name>', 'Connection name')
    .action(async (connectionString: string, options: { name?: string }) => {
      try {
        await mongoCLI.connect(connectionString, options.name);
      } catch (error) {
        console.error(
          chalk.red('\n✗ Error:'),
          error instanceof Error ? error.message : String(error)
        );
        process.exit(1);
      }
    });

  // mongo disconnect
  mongoCommand
    .command('disconnect [name]')
    .description('Disconnect from MongoDB database')
    .action(async (name?: string) => {
      try {
        await mongoCLI.disconnect(name);
      } catch (error) {
        console.error(
          chalk.red('\n✗ Error:'),
          error instanceof Error ? error.message : String(error)
        );
        process.exit(1);
      }
    });

  // mongo query
  mongoCommand
    .command('query <filter>')
    .description('Query MongoDB collection')
    .requiredOption('-c, --collection <name>', 'Collection name')
    .option('-p, --projection <fields>', 'Projection fields (JSON)')
    .option('-s, --sort <fields>', 'Sort fields (JSON)')
    .option('-l, --limit <n>', 'Limit results', parseInt)
    .option('--skip <n>', 'Skip results', parseInt)
    .option('-f, --format <format>', 'Output format (table or json)', 'table')
    .action(
      async (
        filter: string,
        options: {
          collection: string;
          projection?: string;
          sort?: string;
          limit?: number;
          skip?: number;
          format: 'table' | 'json';
        }
      ) => {
        try {
          const results = await mongoCLI.query({
            collection: options.collection,
            filter,
            projection: options.projection,
            sort: options.sort,
            limit: options.limit,
            skip: options.skip,
          });

          mongoCLI.formatResults(results, options.format);
        } catch (error) {
          console.error(
            chalk.red('\n✗ Error:'),
            error instanceof Error ? error.message : String(error)
          );
          process.exit(1);
        }
      }
    );

  // mongo aggregate
  mongoCommand
    .command('aggregate <pipeline>')
    .description('Execute aggregation pipeline')
    .requiredOption('-c, --collection <name>', 'Collection name')
    .option('-f, --format <format>', 'Output format (table or json)', 'table')
    .option('--explain', 'Show execution plan')
    .action(
      async (
        pipeline: string,
        options: {
          collection: string;
          format: 'table' | 'json';
          explain?: boolean;
        }
      ) => {
        try {
          const results = await mongoCLI.aggregate({
            collection: options.collection,
            pipeline,
            explain: options.explain,
          });

          if (!options.explain) {
            mongoCLI.formatResults(results, options.format);
          }
        } catch (error) {
          console.error(
            chalk.red('\n✗ Error:'),
            error instanceof Error ? error.message : String(error)
          );
          process.exit(1);
        }
      }
    );

  // mongo collections
  mongoCommand
    .command('collections [database]')
    .description('List all collections in database')
    .action(async (database?: string) => {
      try {
        const collections = await mongoCLI.listCollections(database);

        console.log(chalk.cyan('\n📦 Collections:\n'));

        if (collections.length === 0) {
          console.log(chalk.yellow('  No collections found\n'));
          return;
        }

        collections.forEach((coll, i) => {
          console.log(`  ${i + 1}. ${coll}`);
        });

        console.log(chalk.gray(`\n${collections.length} collection(s) total\n`));
      } catch (error) {
        console.error(
          chalk.red('\n✗ Error:'),
          error instanceof Error ? error.message : String(error)
        );
        process.exit(1);
      }
    });

  // mongo indexes
  mongoCommand
    .command('indexes <collection>')
    .description('List indexes for a collection')
    .option('-f, --format <format>', 'Output format (table or json)', 'table')
    .action(
      async (
        collection: string,
        options: {
          format: 'table' | 'json';
        }
      ) => {
        try {
          const indexes = await mongoCLI.listIndexes(collection);

          if (options.format === 'json') {
            console.log('\n' + JSON.stringify(indexes, null, 2) + '\n');
            return;
          }

          console.log(chalk.cyan(`\n📊 Indexes for ${collection}:\n`));

          indexes.forEach((index, i) => {
            const keys = Object.entries(index.key)
              .map(([k, v]) => `${k}:${v}`)
              .join(', ');

            console.log(`${i + 1}. ${chalk.bold(index.name)}`);
            console.log(`   Keys: ${keys}`);

            if (index.unique) {
              console.log(`   ${chalk.green('Unique')}`);
            }

            if (index.sparse) {
              console.log(`   ${chalk.yellow('Sparse')}`);
            }

            if (index.expireAfterSeconds) {
              console.log(`   TTL: ${index.expireAfterSeconds}s`);
            }

            console.log();
          });

          console.log(chalk.gray(`${indexes.length} index(es) total\n`));
        } catch (error) {
          console.error(
            chalk.red('\n✗ Error:'),
            error instanceof Error ? error.message : String(error)
          );
          process.exit(1);
        }
      }
    );

  // mongo import
  mongoCommand
    .command('import <file>')
    .description('Import data into collection')
    .requiredOption('-c, --collection <name>', 'Collection name')
    .option('-f, --format <format>', 'File format (json or csv)', 'json')
    .option('--drop', 'Drop collection before import')
    .action(
      async (
        file: string,
        options: {
          collection: string;
          format: 'json' | 'csv';
          drop?: boolean;
        }
      ) => {
        try {
          await mongoCLI.import({
            collection: options.collection,
            file,
            format: options.format,
            dropCollection: options.drop,
          });
        } catch (error) {
          console.error(
            chalk.red('\n✗ Error:'),
            error instanceof Error ? error.message : String(error)
          );
          process.exit(1);
        }
      }
    );

  // mongo export
  mongoCommand
    .command('export <collection>')
    .description('Export collection data')
    .requiredOption('-o, --output <file>', 'Output file path')
    .option('-f, --format <format>', 'Export format (json or csv)', 'json')
    .option('--filter <filter>', 'Filter query (JSON)')
    .option('-l, --limit <n>', 'Limit results', parseInt)
    .action(
      async (
        collection: string,
        options: {
          output: string;
          format: 'json' | 'csv';
          filter?: string;
          limit?: number;
        }
      ) => {
        try {
          await mongoCLI.export({
            collection,
            output: options.output,
            format: options.format,
            filter: options.filter,
            limit: options.limit,
          });
        } catch (error) {
          console.error(
            chalk.red('\n✗ Error:'),
            error instanceof Error ? error.message : String(error)
          );
          process.exit(1);
        }
      }
    );

  // mongo connections
  mongoCommand
    .command('connections')
    .description('List MongoDB connections')
    .action(() => {
      try {
        const connections = mongoCLI.listConnections();

        if (connections.length === 0) {
          console.log(chalk.yellow('\n⚠ No active MongoDB connections\n'));
          return;
        }

        console.log(chalk.cyan('\n🔗 MongoDB Connections:\n'));

        connections.forEach((conn, i) => {
          const active = conn.isActive ? chalk.green('✓ Active') : chalk.gray('Inactive');
          const uptime = Math.floor((Date.now() - conn.connectedAt) / 1000);

          console.log(`${i + 1}. ${chalk.bold(conn.name)} ${active}`);
          console.log(`   Database: ${conn.database || 'N/A'}`);
          console.log(`   Connected: ${uptime}s ago`);
          console.log();
        });
      } catch (error) {
        console.error(
          chalk.red('\n✗ Error:'),
          error instanceof Error ? error.message : String(error)
        );
        process.exit(1);
      }
    });

  // mongo stats
  mongoCommand
    .command('stats [name]')
    .description('Show connection statistics')
    .action(async (name?: string) => {
      try {
        const stats = await mongoCLI.getConnectionStats(name);

        console.log(chalk.cyan('\n📊 MongoDB Statistics:\n'));
        console.log(`Connection: ${chalk.bold(stats.name)}`);
        console.log(`Uptime: ${stats.uptime}s`);
        console.log();
        console.log(chalk.bold('Connections:'));
        console.log(`  Current: ${stats.connections.current}`);
        console.log(`  Available: ${stats.connections.available}`);
        console.log();
        console.log(chalk.bold('Operations:'));
        console.log(`  Insert: ${stats.opcounters.insert}`);
        console.log(`  Query: ${stats.opcounters.query}`);
        console.log(`  Update: ${stats.opcounters.update}`);
        console.log(`  Delete: ${stats.opcounters.delete}`);
        console.log();
        console.log(chalk.bold('Memory:'));
        console.log(`  Resident: ${stats.memory.resident} MB`);
        console.log(`  Virtual: ${stats.memory.virtual} MB`);
        console.log();
      } catch (error) {
        console.error(
          chalk.red('\n✗ Error:'),
          error instanceof Error ? error.message : String(error)
        );
        process.exit(1);
      }
    });
}
