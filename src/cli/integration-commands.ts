/**
 * Integration Command Definitions - Sprint 5
 *
 * Command metadata, help text, and configuration for 20 integration commands
 */

import { Command } from 'commander';
import {
  slackSetup,
  slackNotify,
  slackAlert,
  slackReport,
  emailSetup,
  emailSend,
  emailAlert,
  emailReport,
  federationAdd,
  federationRemove,
  federationQuery,
  federationStatus,
  schemaDiff,
  schemaSync,
  schemaExport,
  schemaImport,
  adaStart,
  adaStop,
  adaStatus,
  adaConfigure
} from './integration-cli.js';

/**
 * Register all integration commands
 */
export function registerIntegrationCommands(program: Command): void {
  // ============================================================================
  // SLACK INTEGRATION COMMANDS
  // ============================================================================

  const slackCmd = program
    .command('slack')
    .description('Slack integration commands');

  slackCmd
    .command('setup')
    .description('Setup Slack integration with workspace credentials')
    .option('-t, --token <token>', 'Slack bot token')
    .option('-w, --workspace <id>', 'Workspace ID')
    .option('-i, --interactive', 'Interactive setup', false)
    .action(slackSetup);

  slackCmd
    .command('notify')
    .description('Send notification to Slack channel')
    .argument('<channel>', 'Channel name or ID')
    .argument('<message>', 'Message to send')
    .option('-p, --priority <level>', 'Priority level (low|normal|high)', 'normal')
    .option('-a, --attachments <json>', 'Attachments as JSON or file path')
    .option('-t, --thread <ts>', 'Thread timestamp to reply to')
    .option('-m, --mentions <users>', 'Comma-separated user IDs to mention')
    .action(slackNotify);

  slackCmd
    .command('alert')
    .description('Send alert to Slack with severity level')
    .argument('<severity>', 'Alert severity (info|warning|error|critical)')
    .argument('<message>', 'Alert message')
    .option('-c, --channel <channel>', 'Target channel')
    .option('-i, --incident <id>', 'Incident ID')
    .option('-x, --context <json>', 'Additional context as JSON')
    .action(slackAlert);

  slackCmd
    .command('report')
    .description('Generate and send report to Slack')
    .argument('<type>', 'Report type (daily|weekly|monthly|custom)')
    .option('-c, --channel <channel>', 'Target channel')
    .option('-f, --format <format>', 'Report format (summary|detailed|chart)', 'summary')
    .option('-p, --period <period>', 'Custom time period')
    .option('-m, --metrics <metrics>', 'Comma-separated metrics to include')
    .action(slackReport);

  // ============================================================================
  // EMAIL INTEGRATION COMMANDS
  // ============================================================================

  const emailCmd = program
    .command('email')
    .description('Email integration commands');

  emailCmd
    .command('setup')
    .description('Setup email integration with SMTP/provider credentials')
    .option('-p, --provider <provider>', 'Email provider (smtp|sendgrid|mailgun|ses)')
    .option('-s, --smtp <server>', 'SMTP server address')
    .option('--port <port>', 'SMTP port', parseInt)
    .option('-u, --username <username>', 'Username/API key')
    .option('--password <password>', 'Password/API secret')
    .option('-i, --interactive', 'Interactive setup', false)
    .action(emailSetup);

  emailCmd
    .command('send')
    .description('Send email with optional attachments')
    .argument('<to>', 'Recipient email(s), comma-separated')
    .argument('<subject>', 'Email subject')
    .option('-b, --body <text>', 'Email body (plain text)')
    .option('-h, --html <html>', 'Email body (HTML)')
    .option('-t, --template <name>', 'Template name to use')
    .option('-a, --attachments <files>', 'Comma-separated file paths')
    .option('--cc <emails>', 'CC recipients')
    .option('--bcc <emails>', 'BCC recipients')
    .option('-p, --priority <level>', 'Priority level (low|normal|high)', 'normal')
    .action(emailSend);

  emailCmd
    .command('alert')
    .description('Send alert email with predefined template')
    .argument('<to>', 'Recipient email(s)')
    .argument('<alert-id>', 'Alert ID')
    .option('-s, --severity <level>', 'Alert severity (info|warning|error|critical)', 'info')
    .option('-x, --context <json>', 'Additional context as JSON')
    .option('-i, --incident <id>', 'Incident ID')
    .action(emailAlert);

  emailCmd
    .command('report')
    .description('Generate and send report via email')
    .argument('<type>', 'Report type (daily|weekly|monthly|custom)')
    .argument('<to>', 'Recipient email(s)')
    .option('-f, --format <format>', 'Report format (html|pdf|csv)', 'html')
    .option('-p, --period <period>', 'Custom time period')
    .option('-m, --metrics <metrics>', 'Comma-separated metrics to include')
    .option('-a, --attachments', 'Include chart attachments', false)
    .action(emailReport);

  // ============================================================================
  // FEDERATION COMMANDS
  // ============================================================================

  const federationCmd = program
    .command('federation')
    .description('Database federation commands');

  federationCmd
    .command('add')
    .description('Add database to federation')
    .argument('<database>', 'Database name')
    .option('-t, --type <type>', 'Database type (postgresql|mysql|mongodb|redis)')
    .option('-h, --host <host>', 'Database host')
    .option('-p, --port <port>', 'Database port', parseInt)
    .option('-u, --username <username>', 'Username')
    .option('--password <password>', 'Password')
    .option('-a, --alias <alias>', 'Database alias')
    .action(federationAdd);

  federationCmd
    .command('remove')
    .description('Remove database from federation')
    .argument('<database>', 'Database name or alias')
    .option('-f, --force', 'Force removal without confirmation', false)
    .action(federationRemove);

  federationCmd
    .command('query')
    .description('Execute federated query across multiple databases')
    .argument('<sql>', 'SQL query to execute')
    .option('-d, --databases <databases>', 'Comma-separated database aliases')
    .option('-f, --format <format>', 'Output format (table|json|csv)', 'table')
    .option('-o, --output <file>', 'Save results to file')
    .option('-e, --explain', 'Show query execution plan', false)
    .action(federationQuery);

  federationCmd
    .command('status')
    .description('Show federation status and connected databases')
    .option('-d, --detailed', 'Show detailed metrics', false)
    .option('--database <database>', 'Show status for specific database')
    .action(federationStatus);

  // ============================================================================
  // SCHEMA MANAGEMENT COMMANDS
  // ============================================================================

  const schemaCmd = program
    .command('schema')
    .description('Schema management commands');

  schemaCmd
    .command('diff')
    .description('Compare schemas between two databases')
    .argument('<source>', 'Source database')
    .argument('<target>', 'Target database')
    .option('-o, --output <file>', 'Save diff to file')
    .option('-f, --format <format>', 'Output format (text|json|sql)', 'text')
    .option('--ignore-data', 'Ignore data differences', false)
    .action(schemaDiff);

  schemaCmd
    .command('sync')
    .description('Synchronize schema from source to target database')
    .argument('<source>', 'Source database')
    .argument('<target>', 'Target database')
    .option('--dry-run', 'Simulate sync without executing', false)
    .option('-f, --force', 'Skip confirmation prompt', false)
    .option('-b, --backup', 'Create backup before sync', false)
    .action(schemaSync);

  schemaCmd
    .command('export')
    .description('Export schema to file')
    .argument('<database>', 'Database name')
    .option('-o, --output <file>', 'Output file path')
    .option('-f, --format <format>', 'Export format (sql|json|yaml)', 'sql')
    .option('--include-data', 'Include table data', false)
    .option('-t, --tables <tables>', 'Comma-separated table names to export')
    .action(schemaExport);

  schemaCmd
    .command('import')
    .description('Import schema from file')
    .argument('<file>', 'Schema file to import')
    .option('-d, --database <database>', 'Target database')
    .option('-f, --format <format>', 'Schema format (sql|json|yaml)')
    .option('--dry-run', 'Validate without importing', false)
    .option('--force', 'Skip confirmation prompt', false)
    .action(schemaImport);

  // ============================================================================
  // AUTONOMOUS AGENT COMMANDS
  // ============================================================================

  const adaCmd = program
    .command('ada')
    .description('Autonomous Database Agent (ADA) commands');

  adaCmd
    .command('start')
    .description('Start autonomous database agent')
    .option('-m, --mode <mode>', 'Operation mode (monitoring|optimization|full)', 'full')
    .option('-i, --interval <seconds>', 'Check interval in seconds', parseInt, 60)
    .option('--auto-fix', 'Enable automatic fixes', true)
    .action(adaStart);

  adaCmd
    .command('stop')
    .description('Stop autonomous database agent')
    .option('-f, --force', 'Force stop without graceful shutdown', false)
    .option('-e, --export', 'Export metrics before stopping', false)
    .action(adaStop);

  adaCmd
    .command('status')
    .description('Check autonomous agent status')
    .option('-d, --detailed', 'Show detailed status and metrics', false)
    .option('-w, --watch', 'Watch mode - continuously update status', false)
    .option('-i, --interval <ms>', 'Update interval for watch mode (ms)', parseInt, 5000)
    .action(adaStatus);

  adaCmd
    .command('configure')
    .description('Configure autonomous agent settings')
    .option('-m, --mode <mode>', 'Operation mode (monitoring|optimization|full)')
    .option('-i, --interval <seconds>', 'Check interval in seconds', parseInt)
    .option('--auto-fix <boolean>', 'Enable/disable automatic fixes', (val) => val === 'true')
    .option('--alert-threshold <percent>', 'Alert threshold percentage', parseInt)
    .option('-d, --databases <databases>', 'Comma-separated database names to monitor')
    .option('--interactive', 'Interactive configuration', false)
    .action(adaConfigure);
}

/**
 * Command metadata for documentation and help
 */
export const integrationCommandMetadata = {
  slack: {
    category: 'Integration',
    commands: [
      {
        name: 'setup',
        description: 'Setup Slack integration with workspace credentials',
        usage: 'ai-shell slack setup [options]',
        examples: [
          'ai-shell slack setup --interactive',
          'ai-shell slack setup --token xoxb-xxx --workspace W123'
        ]
      },
      {
        name: 'notify',
        description: 'Send notification to Slack channel',
        usage: 'ai-shell slack notify <channel> <message> [options]',
        examples: [
          'ai-shell slack notify #alerts "Deployment completed"',
          'ai-shell slack notify C123 "Build failed" --priority high'
        ]
      },
      {
        name: 'alert',
        description: 'Send alert to Slack with severity level',
        usage: 'ai-shell slack alert <severity> <message> [options]',
        examples: [
          'ai-shell slack alert warning "High CPU usage detected"',
          'ai-shell slack alert critical "Database connection failed" --incident INC-123'
        ]
      },
      {
        name: 'report',
        description: 'Generate and send report to Slack',
        usage: 'ai-shell slack report <type> [options]',
        examples: [
          'ai-shell slack report daily --channel #reports',
          'ai-shell slack report weekly --format detailed --metrics cpu,memory'
        ]
      }
    ]
  },

  email: {
    category: 'Integration',
    commands: [
      {
        name: 'setup',
        description: 'Setup email integration with SMTP/provider credentials',
        usage: 'ai-shell email setup [options]',
        examples: [
          'ai-shell email setup --interactive',
          'ai-shell email setup --provider smtp --smtp smtp.gmail.com --port 587'
        ]
      },
      {
        name: 'send',
        description: 'Send email with optional attachments',
        usage: 'ai-shell email send <to> <subject> [options]',
        examples: [
          'ai-shell email send user@example.com "Report" --body "Daily report attached"',
          'ai-shell email send team@company.com "Alert" --template alert-template'
        ]
      },
      {
        name: 'alert',
        description: 'Send alert email with predefined template',
        usage: 'ai-shell email alert <to> <alert-id> [options]',
        examples: [
          'ai-shell email alert ops@company.com ALERT-123 --severity critical',
          'ai-shell email alert team@company.com ALERT-456 --incident INC-789'
        ]
      },
      {
        name: 'report',
        description: 'Generate and send report via email',
        usage: 'ai-shell email report <type> <to> [options]',
        examples: [
          'ai-shell email report daily admin@company.com --format pdf',
          'ai-shell email report weekly team@company.com --metrics cpu,memory,disk'
        ]
      }
    ]
  },

  federation: {
    category: 'Database',
    commands: [
      {
        name: 'add',
        description: 'Add database to federation',
        usage: 'ai-shell federation add <database> [options]',
        examples: [
          'ai-shell federation add mydb --type postgresql --host localhost',
          'ai-shell federation add analytics --type mysql --alias analytics-db'
        ]
      },
      {
        name: 'remove',
        description: 'Remove database from federation',
        usage: 'ai-shell federation remove <database> [options]',
        examples: [
          'ai-shell federation remove mydb',
          'ai-shell federation remove olddb --force'
        ]
      },
      {
        name: 'query',
        description: 'Execute federated query across multiple databases',
        usage: 'ai-shell federation query <sql> [options]',
        examples: [
          'ai-shell federation query "SELECT * FROM users LIMIT 10"',
          'ai-shell federation query "SELECT * FROM orders" --databases db1,db2 --format json'
        ]
      },
      {
        name: 'status',
        description: 'Show federation status and connected databases',
        usage: 'ai-shell federation status [options]',
        examples: [
          'ai-shell federation status',
          'ai-shell federation status --detailed --database mydb'
        ]
      }
    ]
  },

  schema: {
    category: 'Database',
    commands: [
      {
        name: 'diff',
        description: 'Compare schemas between two databases',
        usage: 'ai-shell schema diff <source> <target> [options]',
        examples: [
          'ai-shell schema diff prod staging',
          'ai-shell schema diff db1 db2 --format sql --output migration.sql'
        ]
      },
      {
        name: 'sync',
        description: 'Synchronize schema from source to target database',
        usage: 'ai-shell schema sync <source> <target> [options]',
        examples: [
          'ai-shell schema sync prod staging --dry-run',
          'ai-shell schema sync master replica --backup --force'
        ]
      },
      {
        name: 'export',
        description: 'Export schema to file',
        usage: 'ai-shell schema export <database> [options]',
        examples: [
          'ai-shell schema export mydb --format sql',
          'ai-shell schema export prod --include-data --tables users,orders'
        ]
      },
      {
        name: 'import',
        description: 'Import schema from file',
        usage: 'ai-shell schema import <file> [options]',
        examples: [
          'ai-shell schema import schema.sql --database mydb',
          'ai-shell schema import backup.json --dry-run'
        ]
      }
    ]
  },

  ada: {
    category: 'Autonomous',
    commands: [
      {
        name: 'start',
        description: 'Start autonomous database agent',
        usage: 'ai-shell ada start [options]',
        examples: [
          'ai-shell ada start',
          'ai-shell ada start --mode monitoring --interval 30'
        ]
      },
      {
        name: 'stop',
        description: 'Stop autonomous database agent',
        usage: 'ai-shell ada stop [options]',
        examples: [
          'ai-shell ada stop',
          'ai-shell ada stop --export --force'
        ]
      },
      {
        name: 'status',
        description: 'Check autonomous agent status',
        usage: 'ai-shell ada status [options]',
        examples: [
          'ai-shell ada status',
          'ai-shell ada status --detailed --watch'
        ]
      },
      {
        name: 'configure',
        description: 'Configure autonomous agent settings',
        usage: 'ai-shell ada configure [options]',
        examples: [
          'ai-shell ada configure --interactive',
          'ai-shell ada configure --mode full --interval 60 --auto-fix true'
        ]
      }
    ]
  }
};

/**
 * Get help text for a specific command group
 */
export function getCommandGroupHelp(group: keyof typeof integrationCommandMetadata): string {
  const metadata = integrationCommandMetadata[group];
  if (!metadata) {
    return 'Unknown command group';
  }

  let help = `\n${group.toUpperCase()} COMMANDS (${metadata.category})\n`;
  help += '='.repeat(60) + '\n\n';

  metadata.commands.forEach(cmd => {
    help += `${cmd.name}\n`;
    help += `  ${cmd.description}\n`;
    help += `  Usage: ${cmd.usage}\n`;
    help += `  Examples:\n`;
    cmd.examples.forEach(ex => {
      help += `    ${ex}\n`;
    });
    help += '\n';
  });

  return help;
}

export default {
  registerIntegrationCommands,
  integrationCommandMetadata,
  getCommandGroupHelp
};
