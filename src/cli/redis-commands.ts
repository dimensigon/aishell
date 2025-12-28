/**
 * Redis CLI Commands Registration
 * Registers all Redis-related commands with the Commander program
 */

import { Command } from 'commander';
import chalk from 'chalk';
import { RedisCLI } from './redis-cli';
import { createLogger } from '../core/logger';

const logger = createLogger('RedisCommands');

/**
 * Register all Redis commands
 */
export function registerRedisCommands(program: Command, getRedisCLI: () => RedisCLI): void {
  // Redis connect command
  program
    .command('redis connect <connection-string>')
    .description('Connect to a Redis server')
    .option('-n, --name <name>', 'Connection name (default: "default")')
    .option('--db <number>', 'Database number (default: 0)', '0')
    .option('--tls', 'Use TLS/SSL connection')
    .option('--cluster', 'Connect to Redis cluster')
    .addHelpText('after', `
${chalk.bold('Connection String Formats:')}
  redis://localhost:6379
  redis://username:password@localhost:6379
  redis://localhost:6379/2 (with database selection)
  rediss://localhost:6380 (TLS)

${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell redis connect redis://localhost:6379
  ${chalk.dim('$')} ai-shell redis connect redis://user:pass@host:6379 --name production
  ${chalk.dim('$')} ai-shell redis connect redis://localhost:6379 --db 1
  ${chalk.dim('$')} ai-shell redis connect rediss://localhost:6380 --tls
  ${chalk.dim('$')} ai-shell redis connect redis://localhost:6379 --cluster
`)
    .action(async (connectionString: string, options) => {
      try {
        const cli = getRedisCLI();
        await cli.connect(connectionString, {
          name: options.name,
          db: parseInt(options.db),
          tls: options.tls,
          cluster: options.cluster
        });
        console.log(chalk.green(`✓ Connected to Redis: ${options.name || 'default'}\n`));
      } catch (error) {
        logger.error('Connection failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Redis disconnect command
  program
    .command('redis disconnect [name]')
    .description('Disconnect from a Redis server')
    .option('--all', 'Disconnect all connections')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell redis disconnect
  ${chalk.dim('$')} ai-shell redis disconnect production
  ${chalk.dim('$')} ai-shell redis disconnect --all
`)
    .action(async (name: string | undefined, options) => {
      try {
        const cli = getRedisCLI();
        if (options.all) {
          await cli.disconnectAll();
          console.log(chalk.green('✓ Disconnected all connections\n'));
        } else {
          await cli.disconnect(name);
          console.log(chalk.green(`✓ Disconnected: ${name || 'default'}\n`));
        }
      } catch (error) {
        logger.error('Disconnection failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Redis get command
  program
    .command('redis get <key>')
    .description('Get the value of a key')
    .option('-c, --connection <name>', 'Connection name')
    .option('-f, --format <type>', 'Output format (json, raw)', 'raw')
    .option('--type', 'Show key type')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell redis get user:1001
  ${chalk.dim('$')} ai-shell redis get session:abc123 --format json
  ${chalk.dim('$')} ai-shell redis get mykey --type
  ${chalk.dim('$')} ai-shell redis get mykey --connection production
`)
    .action(async (key: string, options) => {
      try {
        const cli = getRedisCLI();
        const result = await cli.get(key, {
          connection: options.connection,
          showType: options.type
        });

        if (options.format === 'json') {
          console.log(JSON.stringify(result, null, 2));
        } else {
          cli.displayValue(key, result);
        }
      } catch (error) {
        logger.error('GET failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Redis set command
  program
    .command('redis set <key> <value>')
    .description('Set the string value of a key')
    .option('-c, --connection <name>', 'Connection name')
    .option('--ex <seconds>', 'Set expiration in seconds', parseInt)
    .option('--px <milliseconds>', 'Set expiration in milliseconds', parseInt)
    .option('--nx', 'Only set if key does not exist')
    .option('--xx', 'Only set if key already exists')
    .option('--keepttl', 'Retain the time to live associated with the key')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell redis set mykey "Hello World"
  ${chalk.dim('$')} ai-shell redis set session:abc123 "user_data" --ex 3600
  ${chalk.dim('$')} ai-shell redis set counter 0 --nx
  ${chalk.dim('$')} ai-shell redis set existing_key "new_value" --xx --keepttl
`)
    .action(async (key: string, value: string, options) => {
      try {
        const cli = getRedisCLI();
        const result = await cli.set(key, value, {
          connection: options.connection,
          ex: options.ex,
          px: options.px,
          nx: options.nx,
          xx: options.xx,
          keepttl: options.keepttl
        });

        console.log(chalk.green(`✓ ${result.message}\n`));
      } catch (error) {
        logger.error('SET failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Redis keys command
  program
    .command('redis keys <pattern>')
    .description('Find all keys matching a pattern')
    .option('-c, --connection <name>', 'Connection name')
    .option('--limit <n>', 'Limit number of results', parseInt)
    .option('--scan', 'Use SCAN instead of KEYS (safer for production)')
    .option('-f, --format <type>', 'Output format (table, json, list)', 'list')
    .addHelpText('after', `
${chalk.bold('Pattern Syntax:')}
  * - matches any characters
  ? - matches single character
  [abc] - matches a, b, or c
  [^abc] - matches any character except a, b, c

${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell redis keys "user:*"
  ${chalk.dim('$')} ai-shell redis keys "session:*" --scan
  ${chalk.dim('$')} ai-shell redis keys "*" --limit 100 --format table
  ${chalk.dim('$')} ai-shell redis keys "cache:???" --format json
`)
    .action(async (pattern: string, options) => {
      try {
        const cli = getRedisCLI();
        const result = await cli.keys(pattern, {
          connection: options.connection,
          limit: options.limit,
          useScan: options.scan
        });

        if (options.format === 'json') {
          console.log(JSON.stringify(result, null, 2));
        } else if (options.format === 'table') {
          cli.displayKeysTable(result.keys);
        } else {
          cli.displayKeysList(result.keys);
        }
      } catch (error) {
        logger.error('KEYS failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Redis info command
  program
    .command('redis info [section]')
    .description('Get information and statistics about the server')
    .option('-c, --connection <name>', 'Connection name')
    .option('-f, --format <type>', 'Output format (table, json)', 'table')
    .addHelpText('after', `
${chalk.bold('Sections:')}
  server     - General information about the Redis server
  clients    - Client connections section
  memory     - Memory consumption related information
  persistence - RDB and AOF related information
  stats      - General statistics
  replication - Master/replica replication information
  cpu        - CPU consumption statistics
  keyspace   - Database related statistics
  cluster    - Redis Cluster section
  all        - Return all sections (default)

${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell redis info
  ${chalk.dim('$')} ai-shell redis info memory
  ${chalk.dim('$')} ai-shell redis info stats --format json
  ${chalk.dim('$')} ai-shell redis info --connection production
`)
    .action(async (section: string | undefined, options) => {
      try {
        const cli = getRedisCLI();
        const result = await cli.info(section, {
          connection: options.connection
        });

        if (options.format === 'json') {
          console.log(JSON.stringify(result, null, 2));
        } else {
          cli.displayInfo(result);
        }
      } catch (error) {
        logger.error('INFO failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Redis flush command
  program
    .command('redis flush [db]')
    .description('Flush (delete) all keys in database')
    .option('-c, --connection <name>', 'Connection name')
    .option('--all', 'Flush all databases (FLUSHALL)')
    .option('--async', 'Flush asynchronously')
    .option('--force', 'Skip confirmation prompt')
    .addHelpText('after', `
${chalk.bold('⚠ WARNING:')} This command permanently deletes data!

${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell redis flush --force
  ${chalk.dim('$')} ai-shell redis flush 0 --async --force
  ${chalk.dim('$')} ai-shell redis flush --all --force
`)
    .action(async (db: string | undefined, options) => {
      try {
        if (!options.force) {
          console.log(chalk.red('\n⚠ This will permanently delete all keys!'));
          console.log(chalk.yellow('Use --force to confirm\n'));
          process.exit(1);
        }

        const cli = getRedisCLI();
        const result = await cli.flush({
          connection: options.connection,
          db: db ? parseInt(db) : undefined,
          all: options.all,
          async: options.async
        });

        console.log(chalk.green(`✓ ${result.message}\n`));
        console.log(chalk.dim(`  Deleted ${result.deletedKeys || 'all'} keys`));
        console.log('');
      } catch (error) {
        logger.error('FLUSH failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Redis monitor command
  program
    .command('redis monitor')
    .description('Monitor Redis commands in real-time')
    .option('-c, --connection <name>', 'Connection name')
    .option('--duration <seconds>', 'Monitor duration in seconds', parseInt)
    .option('--filter <pattern>', 'Filter commands by pattern')
    .option('--output <file>', 'Save output to file')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell redis monitor
  ${chalk.dim('$')} ai-shell redis monitor --duration 60
  ${chalk.dim('$')} ai-shell redis monitor --filter "GET*"
  ${chalk.dim('$')} ai-shell redis monitor --output redis-monitor.log

${chalk.bold('Note:')} Press Ctrl+C to stop monitoring
`)
    .action(async (options) => {
      try {
        const cli = getRedisCLI();
        await cli.monitor({
          connection: options.connection,
          duration: options.duration,
          filter: options.filter,
          output: options.output
        });
      } catch (error) {
        logger.error('MONITOR failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  // Additional utility commands
  program
    .command('redis ttl <key>')
    .description('Get the time to live for a key')
    .option('-c, --connection <name>', 'Connection name')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell redis ttl session:abc123
  ${chalk.dim('$')} ai-shell redis ttl mykey --connection production
`)
    .action(async (key: string, options) => {
      try {
        const cli = getRedisCLI();
        const result = await cli.ttl(key, {
          connection: options.connection
        });

        cli.displayTTL(key, result);
      } catch (error) {
        logger.error('TTL failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  program
    .command('redis expire <key> <seconds>')
    .description('Set a timeout on a key')
    .option('-c, --connection <name>', 'Connection name')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell redis expire session:abc123 3600
  ${chalk.dim('$')} ai-shell redis expire mykey 60 --connection production
`)
    .action(async (key: string, seconds: string, options) => {
      try {
        const cli = getRedisCLI();
        const result = await cli.expire(key, parseInt(seconds), {
          connection: options.connection
        });

        console.log(chalk.green(`✓ ${result.message}\n`));
      } catch (error) {
        logger.error('EXPIRE failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  program
    .command('redis del <keys...>')
    .description('Delete one or more keys')
    .option('-c, --connection <name>', 'Connection name')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell redis del mykey
  ${chalk.dim('$')} ai-shell redis del key1 key2 key3
  ${chalk.dim('$')} ai-shell redis del session:* --connection production
`)
    .action(async (keys: string[], options) => {
      try {
        const cli = getRedisCLI();
        const result = await cli.del(keys, {
          connection: options.connection
        });

        console.log(chalk.green(`✓ Deleted ${result.deletedCount} key(s)\n`));
      } catch (error) {
        logger.error('DEL failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });

  program
    .command('redis type <key>')
    .description('Determine the type of a key')
    .option('-c, --connection <name>', 'Connection name')
    .addHelpText('after', `
${chalk.bold('Examples:')}
  ${chalk.dim('$')} ai-shell redis type mykey
  ${chalk.dim('$')} ai-shell redis type user:1001 --connection production
`)
    .action(async (key: string, options) => {
      try {
        const cli = getRedisCLI();
        const result = await cli.type(key, {
          connection: options.connection
        });

        console.log(`\nKey: ${chalk.bold(key)}`);
        console.log(`Type: ${chalk.cyan(result.type)}\n`);
      } catch (error) {
        logger.error('TYPE failed', error);
        console.error(chalk.red(`Error: ${error instanceof Error ? error.message : String(error)}`));
        process.exit(1);
      }
    });
}
