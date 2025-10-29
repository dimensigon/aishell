/**
 * Integration CLI - Sprint 5
 *
 * Implements 20 integration and enterprise commands:
 * - Slack Integration (4 commands)
 * - Email Integration (4 commands)
 * - Federation (4 commands)
 * - Schema Management (4 commands)
 * - Autonomous Agent (4 commands)
 */

import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import Table from 'cli-table3';
import inquirer from 'inquirer';
import { SlackClient } from '../integrations/slack-client.js';
import { EmailClient } from '../integrations/email-client.js';
import { FederationEngine } from '../federation/federation-engine.js';
import { SchemaManager } from '../schema/schema-manager.js';
import { ADAAgent } from '../agents/ada-agent.js';
import { Logger } from '../utils/logger.js';
import * as fs from 'fs/promises';
import * as path from 'path';

const logger = new Logger('IntegrationCLI');

// Singleton instances
let slackClient: SlackClient | null = null;
let emailClient: EmailClient | null = null;
let federationEngine: FederationEngine | null = null;
let schemaManager: SchemaManager | null = null;
let adaAgent: ADAAgent | null = null;

/**
 * Initialize Slack client
 */
async function getSlackClient(): Promise<SlackClient> {
  if (!slackClient) {
    slackClient = new SlackClient();
    await slackClient.initialize();
  }
  return slackClient;
}

/**
 * Initialize Email client
 */
async function getEmailClient(): Promise<EmailClient> {
  if (!emailClient) {
    emailClient = new EmailClient();
    await emailClient.initialize();
  }
  return emailClient;
}

/**
 * Initialize Federation engine
 */
async function getFederationEngine(): Promise<FederationEngine> {
  if (!federationEngine) {
    federationEngine = new FederationEngine();
    await federationEngine.initialize();
  }
  return federationEngine;
}

/**
 * Initialize Schema manager
 */
async function getSchemaManager(): Promise<SchemaManager> {
  if (!schemaManager) {
    schemaManager = new SchemaManager();
    await schemaManager.initialize();
  }
  return schemaManager;
}

/**
 * Initialize ADA agent
 */
async function getADAAgent(): Promise<ADAAgent> {
  if (!adaAgent) {
    adaAgent = new ADAAgent();
    await adaAgent.initialize();
  }
  return adaAgent;
}

// ============================================================================
// SLACK INTEGRATION COMMANDS (4 commands)
// ============================================================================

/**
 * Command: ai-shell slack setup
 * Setup Slack integration with workspace credentials
 */
export async function slackSetup(options: {
  token?: string;
  workspace?: string;
  interactive?: boolean;
}): Promise<void> {
  const spinner = ora('Setting up Slack integration').start();

  try {
    const client = await getSlackClient();

    let config: any = {};

    if (options.interactive) {
      // Interactive setup
      const answers = await inquirer.prompt([
        {
          type: 'input',
          name: 'token',
          message: 'Enter Slack Bot Token (xoxb-...):',
          validate: (input: string) => input.startsWith('xoxb-') || 'Token must start with xoxb-'
        },
        {
          type: 'input',
          name: 'workspace',
          message: 'Enter Workspace ID:',
          validate: (input: string) => input.length > 0 || 'Workspace ID is required'
        },
        {
          type: 'input',
          name: 'defaultChannel',
          message: 'Enter default channel (optional):',
        },
        {
          type: 'confirm',
          name: 'enableAlerts',
          message: 'Enable automatic alerts?',
          default: true
        }
      ]);
      config = answers;
    } else {
      // Non-interactive setup
      if (!options.token || !options.workspace) {
        spinner.fail('Token and workspace are required for non-interactive setup');
        process.exit(1);
      }
      config = {
        token: options.token,
        workspace: options.workspace,
        enableAlerts: true
      };
    }

    // Setup Slack integration
    await client.setup(config);

    // Test connection
    const testResult = await client.testConnection();

    if (testResult.success) {
      spinner.succeed('Slack integration setup successfully');
      console.log(chalk.green('\n✓ Connected to workspace:'), testResult.workspace);
      console.log(chalk.green('✓ Bot name:'), testResult.botName);
      console.log(chalk.green('✓ Available channels:'), testResult.channels.length);

      // Save configuration
      await client.saveConfig();
      logger.info('Slack configuration saved');
    } else {
      spinner.fail(`Failed to connect: ${testResult.error}`);
      process.exit(1);
    }

  } catch (error) {
    spinner.fail('Failed to setup Slack integration');
    logger.error('Slack setup error:', error);
    throw error;
  }
}

/**
 * Command: ai-shell slack notify <channel> <message>
 * Send notification to Slack channel
 */
export async function slackNotify(
  channel: string,
  message: string,
  options: {
    priority?: 'low' | 'normal' | 'high';
    attachments?: string;
    thread?: string;
    mentions?: string;
  }
): Promise<void> {
  const spinner = ora(`Sending notification to ${channel}`).start();

  try {
    const client = await getSlackClient();

    // Parse attachments if provided
    let attachmentData = null;
    if (options.attachments) {
      try {
        attachmentData = JSON.parse(options.attachments);
      } catch {
        // Treat as file path
        const fileContent = await fs.readFile(options.attachments, 'utf-8');
        attachmentData = JSON.parse(fileContent);
      }
    }

    // Parse mentions
    const mentions = options.mentions ? options.mentions.split(',') : [];

    // Send notification
    const result = await client.sendMessage({
      channel,
      message,
      priority: options.priority || 'normal',
      attachments: attachmentData,
      threadTs: options.thread,
      mentions
    });

    if (result.success) {
      spinner.succeed(`Notification sent to ${channel}`);
      console.log(chalk.green('\n✓ Message ID:'), result.messageId);
      console.log(chalk.green('✓ Timestamp:'), result.timestamp);
      if (result.permalink) {
        console.log(chalk.green('✓ Link:'), result.permalink);
      }
    } else {
      spinner.fail(`Failed to send notification: ${result.error}`);
      process.exit(1);
    }

  } catch (error) {
    spinner.fail('Failed to send Slack notification');
    logger.error('Slack notify error:', error);
    throw error;
  }
}

/**
 * Command: ai-shell slack alert <severity> <message>
 * Send alert to Slack with severity level
 */
export async function slackAlert(
  severity: 'info' | 'warning' | 'error' | 'critical',
  message: string,
  options: {
    channel?: string;
    incident?: string;
    context?: string;
  }
): Promise<void> {
  const spinner = ora(`Sending ${severity} alert to Slack`).start();

  try {
    const client = await getSlackClient();

    // Parse context if provided
    let contextData = null;
    if (options.context) {
      try {
        contextData = JSON.parse(options.context);
      } catch {
        contextData = { details: options.context };
      }
    }

    // Send alert
    const result = await client.sendAlert({
      severity,
      message,
      channel: options.channel,
      incidentId: options.incident,
      context: contextData,
      timestamp: new Date().toISOString()
    });

    if (result.success) {
      spinner.succeed(`${severity.toUpperCase()} alert sent`);
      console.log(chalk.green('\n✓ Alert ID:'), result.alertId);
      console.log(chalk.green('✓ Channel:'), result.channel);
      console.log(chalk.green('✓ Notified users:'), result.notifiedUsers.length);

      if (result.incidentCreated) {
        console.log(chalk.yellow('\n⚠ Incident created:'), result.incidentId);
      }
    } else {
      spinner.fail(`Failed to send alert: ${result.error}`);
      process.exit(1);
    }

  } catch (error) {
    spinner.fail('Failed to send Slack alert');
    logger.error('Slack alert error:', error);
    throw error;
  }
}

/**
 * Command: ai-shell slack report <type>
 * Generate and send report to Slack
 */
export async function slackReport(
  type: 'daily' | 'weekly' | 'monthly' | 'custom',
  options: {
    channel?: string;
    format?: 'summary' | 'detailed' | 'chart';
    period?: string;
    metrics?: string;
  }
): Promise<void> {
  const spinner = ora(`Generating ${type} report for Slack`).start();

  try {
    const client = await getSlackClient();

    // Parse metrics filter
    const metricsFilter = options.metrics ? options.metrics.split(',') : undefined;

    // Generate report
    spinner.text = 'Generating report data...';
    const report = await client.generateReport({
      type,
      format: options.format || 'summary',
      period: options.period,
      metrics: metricsFilter
    });

    // Send report
    spinner.text = 'Sending report to Slack...';
    const result = await client.sendReport({
      channel: options.channel,
      report,
      format: options.format || 'summary'
    });

    if (result.success) {
      spinner.succeed(`${type} report sent to Slack`);
      console.log(chalk.green('\n✓ Report ID:'), result.reportId);
      console.log(chalk.green('✓ Channel:'), result.channel);
      console.log(chalk.green('✓ Metrics included:'), report.metrics.length);
      console.log(chalk.green('✓ Period:'), report.period);

      // Display summary
      console.log(chalk.cyan('\nReport Summary:'));
      const table = new Table({
        head: ['Metric', 'Value', 'Change'],
        style: { head: ['cyan'] }
      });

      report.summary.forEach((item: any) => {
        const change = item.change > 0
          ? chalk.green(`+${item.change}%`)
          : item.change < 0
          ? chalk.red(`${item.change}%`)
          : chalk.gray('0%');

        table.push([item.metric, item.value, change]);
      });

      console.log(table.toString());
    } else {
      spinner.fail(`Failed to send report: ${result.error}`);
      process.exit(1);
    }

  } catch (error) {
    spinner.fail('Failed to generate Slack report');
    logger.error('Slack report error:', error);
    throw error;
  }
}

// ============================================================================
// EMAIL INTEGRATION COMMANDS (4 commands)
// ============================================================================

/**
 * Command: ai-shell email setup
 * Setup email integration with SMTP/provider credentials
 */
export async function emailSetup(options: {
  provider?: string;
  smtp?: string;
  port?: number;
  username?: string;
  password?: string;
  interactive?: boolean;
}): Promise<void> {
  const spinner = ora('Setting up email integration').start();

  try {
    const client = await getEmailClient();

    let config: any = {};

    if (options.interactive) {
      // Interactive setup
      const answers = await inquirer.prompt([
        {
          type: 'list',
          name: 'provider',
          message: 'Select email provider:',
          choices: ['smtp', 'sendgrid', 'mailgun', 'ses', 'custom']
        },
        {
          type: 'input',
          name: 'smtp',
          message: 'SMTP server:',
          when: (answers) => answers.provider === 'smtp' || answers.provider === 'custom'
        },
        {
          type: 'number',
          name: 'port',
          message: 'SMTP port:',
          default: 587,
          when: (answers) => answers.provider === 'smtp' || answers.provider === 'custom'
        },
        {
          type: 'input',
          name: 'username',
          message: 'Username/API Key:',
          validate: (input: string) => input.length > 0 || 'Username is required'
        },
        {
          type: 'password',
          name: 'password',
          message: 'Password/API Secret:',
          validate: (input: string) => input.length > 0 || 'Password is required'
        },
        {
          type: 'input',
          name: 'fromEmail',
          message: 'From email address:',
          validate: (input: string) => input.includes('@') || 'Valid email is required'
        },
        {
          type: 'input',
          name: 'fromName',
          message: 'From name:',
          default: 'AI-Shell'
        }
      ]);
      config = answers;
    } else {
      // Non-interactive setup
      config = {
        provider: options.provider || 'smtp',
        smtp: options.smtp,
        port: options.port || 587,
        username: options.username,
        password: options.password
      };
    }

    // Setup email integration
    await client.setup(config);

    // Test connection
    spinner.text = 'Testing email connection...';
    const testResult = await client.testConnection();

    if (testResult.success) {
      spinner.succeed('Email integration setup successfully');
      console.log(chalk.green('\n✓ Provider:'), testResult.provider);
      console.log(chalk.green('✓ From email:'), testResult.fromEmail);
      console.log(chalk.green('✓ Status:'), testResult.status);

      // Save configuration
      await client.saveConfig();
      logger.info('Email configuration saved');
    } else {
      spinner.fail(`Failed to connect: ${testResult.error}`);
      process.exit(1);
    }

  } catch (error) {
    spinner.fail('Failed to setup email integration');
    logger.error('Email setup error:', error);
    throw error;
  }
}

/**
 * Command: ai-shell email send <to> <subject>
 * Send email with optional attachments
 */
export async function emailSend(
  to: string,
  subject: string,
  options: {
    body?: string;
    html?: string;
    template?: string;
    attachments?: string;
    cc?: string;
    bcc?: string;
    priority?: 'low' | 'normal' | 'high';
  }
): Promise<void> {
  const spinner = ora(`Sending email to ${to}`).start();

  try {
    const client = await getEmailClient();

    // Determine email body
    let body = options.body;
    let html = options.html;

    if (options.template) {
      // Load and render template
      spinner.text = 'Rendering email template...';
      const templateData = await client.renderTemplate(options.template);
      html = templateData.html;
      body = templateData.text;
    }

    if (!body && !html) {
      spinner.fail('Email body or HTML is required');
      process.exit(1);
    }

    // Parse attachments
    let attachments = [];
    if (options.attachments) {
      const attachmentPaths = options.attachments.split(',');
      for (const attachmentPath of attachmentPaths) {
        const content = await fs.readFile(attachmentPath.trim());
        attachments.push({
          filename: path.basename(attachmentPath),
          content
        });
      }
    }

    // Parse recipients
    const toAddresses = to.split(',');
    const ccAddresses = options.cc ? options.cc.split(',') : [];
    const bccAddresses = options.bcc ? options.bcc.split(',') : [];

    // Send email
    const result = await client.sendEmail({
      to: toAddresses,
      cc: ccAddresses,
      bcc: bccAddresses,
      subject,
      text: body,
      html,
      attachments,
      priority: options.priority || 'normal'
    });

    if (result.success) {
      spinner.succeed(`Email sent to ${to}`);
      console.log(chalk.green('\n✓ Message ID:'), result.messageId);
      console.log(chalk.green('✓ Recipients:'), result.accepted.length);
      console.log(chalk.green('✓ Timestamp:'), new Date().toISOString());

      if (result.rejected.length > 0) {
        console.log(chalk.yellow('\n⚠ Rejected:'), result.rejected.join(', '));
      }
    } else {
      spinner.fail(`Failed to send email: ${result.error}`);
      process.exit(1);
    }

  } catch (error) {
    spinner.fail('Failed to send email');
    logger.error('Email send error:', error);
    throw error;
  }
}

/**
 * Command: ai-shell email alert <to> <alert-id>
 * Send alert email with predefined template
 */
export async function emailAlert(
  to: string,
  alertId: string,
  options: {
    severity?: 'info' | 'warning' | 'error' | 'critical';
    context?: string;
    incident?: string;
  }
): Promise<void> {
  const spinner = ora(`Sending alert email to ${to}`).start();

  try {
    const client = await getEmailClient();

    // Parse context
    let contextData = null;
    if (options.context) {
      try {
        contextData = JSON.parse(options.context);
      } catch {
        contextData = { details: options.context };
      }
    }

    // Send alert email
    const result = await client.sendAlert({
      to: to.split(','),
      alertId,
      severity: options.severity || 'info',
      context: contextData,
      incidentId: options.incident,
      timestamp: new Date().toISOString()
    });

    if (result.success) {
      spinner.succeed(`Alert email sent to ${to}`);
      console.log(chalk.green('\n✓ Alert ID:'), alertId);
      console.log(chalk.green('✓ Severity:'), options.severity || 'info');
      console.log(chalk.green('✓ Recipients:'), result.recipients.length);
      console.log(chalk.green('✓ Message ID:'), result.messageId);
    } else {
      spinner.fail(`Failed to send alert: ${result.error}`);
      process.exit(1);
    }

  } catch (error) {
    spinner.fail('Failed to send alert email');
    logger.error('Email alert error:', error);
    throw error;
  }
}

/**
 * Command: ai-shell email report <type> <to>
 * Generate and send report via email
 */
export async function emailReport(
  type: 'daily' | 'weekly' | 'monthly' | 'custom',
  to: string,
  options: {
    format?: 'html' | 'pdf' | 'csv';
    period?: string;
    metrics?: string;
    attachments?: boolean;
  }
): Promise<void> {
  const spinner = ora(`Generating ${type} report for email`).start();

  try {
    const client = await getEmailClient();

    // Parse metrics filter
    const metricsFilter = options.metrics ? options.metrics.split(',') : undefined;

    // Generate report
    spinner.text = 'Generating report data...';
    const report = await client.generateReport({
      type,
      format: options.format || 'html',
      period: options.period,
      metrics: metricsFilter,
      includeCharts: options.attachments
    });

    // Send report email
    spinner.text = 'Sending report email...';
    const result = await client.sendReport({
      to: to.split(','),
      report,
      format: options.format || 'html',
      attachments: options.attachments
    });

    if (result.success) {
      spinner.succeed(`${type} report sent to ${to}`);
      console.log(chalk.green('\n✓ Report ID:'), result.reportId);
      console.log(chalk.green('✓ Recipients:'), result.recipients.length);
      console.log(chalk.green('✓ Format:'), options.format || 'html');
      console.log(chalk.green('✓ Metrics:'), report.metrics.length);

      if (options.attachments) {
        console.log(chalk.green('✓ Attachments:'), result.attachments.length);
      }
    } else {
      spinner.fail(`Failed to send report: ${result.error}`);
      process.exit(1);
    }

  } catch (error) {
    spinner.fail('Failed to send email report');
    logger.error('Email report error:', error);
    throw error;
  }
}

// ============================================================================
// FEDERATION COMMANDS (4 commands)
// ============================================================================

/**
 * Command: ai-shell federation add <database>
 * Add database to federation
 */
export async function federationAdd(
  database: string,
  options: {
    type?: 'postgresql' | 'mysql' | 'mongodb' | 'redis';
    host?: string;
    port?: number;
    username?: string;
    password?: string;
    alias?: string;
  }
): Promise<void> {
  const spinner = ora(`Adding ${database} to federation`).start();

  try {
    const engine = await getFederationEngine();

    // Add database to federation
    const result = await engine.addDatabase({
      name: database,
      type: options.type || 'postgresql',
      host: options.host || 'localhost',
      port: options.port,
      username: options.username,
      password: options.password,
      alias: options.alias || database
    });

    if (result.success) {
      spinner.succeed(`Database ${database} added to federation`);
      console.log(chalk.green('\n✓ Federation ID:'), result.federationId);
      console.log(chalk.green('✓ Database alias:'), result.alias);
      console.log(chalk.green('✓ Type:'), result.type);
      console.log(chalk.green('✓ Status:'), result.status);
      console.log(chalk.green('✓ Schemas discovered:'), result.schemas.length);
    } else {
      spinner.fail(`Failed to add database: ${result.error}`);
      process.exit(1);
    }

  } catch (error) {
    spinner.fail('Failed to add database to federation');
    logger.error('Federation add error:', error);
    throw error;
  }
}

/**
 * Command: ai-shell federation remove <database>
 * Remove database from federation
 */
export async function federationRemove(
  database: string,
  options: {
    force?: boolean;
  }
): Promise<void> {
  const spinner = ora(`Removing ${database} from federation`).start();

  try {
    const engine = await getFederationEngine();

    // Confirm removal if not forced
    if (!options.force) {
      const { confirm } = await inquirer.prompt([
        {
          type: 'confirm',
          name: 'confirm',
          message: `Are you sure you want to remove ${database} from federation?`,
          default: false
        }
      ]);

      if (!confirm) {
        spinner.info('Operation cancelled');
        return;
      }
    }

    // Remove database
    const result = await engine.removeDatabase(database);

    if (result.success) {
      spinner.succeed(`Database ${database} removed from federation`);
      console.log(chalk.green('\n✓ Database removed:'), database);
      console.log(chalk.green('✓ Connections closed:'), result.connectionsClosed);
      console.log(chalk.green('✓ Cached queries cleared:'), result.cacheCleared);
    } else {
      spinner.fail(`Failed to remove database: ${result.error}`);
      process.exit(1);
    }

  } catch (error) {
    spinner.fail('Failed to remove database from federation');
    logger.error('Federation remove error:', error);
    throw error;
  }
}

/**
 * Command: ai-shell federation query <sql>
 * Execute federated query across multiple databases
 */
export async function federationQuery(
  sql: string,
  options: {
    databases?: string;
    format?: 'table' | 'json' | 'csv';
    output?: string;
    explain?: boolean;
  }
): Promise<void> {
  const spinner = ora('Executing federated query').start();

  try {
    const engine = await getFederationEngine();

    // Parse target databases
    const targetDatabases = options.databases
      ? options.databases.split(',')
      : undefined;

    // Execute query
    const result = await engine.executeQuery({
      sql,
      databases: targetDatabases,
      explain: options.explain
    });

    if (result.success) {
      spinner.succeed('Federated query executed successfully');

      if (options.explain) {
        console.log(chalk.cyan('\nQuery Execution Plan:'));
        console.log(result.executionPlan);
      }

      console.log(chalk.green('\n✓ Databases queried:'), result.databasesQueried);
      console.log(chalk.green('✓ Rows returned:'), result.rowCount);
      console.log(chalk.green('✓ Execution time:'), `${result.executionTime}ms`);

      // Format and display results
      const format = options.format || 'table';

      if (format === 'table') {
        if (result.rows.length > 0) {
          const table = new Table({
            head: Object.keys(result.rows[0]),
            style: { head: ['cyan'] }
          });

          result.rows.forEach((row: any) => {
            table.push(Object.values(row));
          });

          console.log('\n' + table.toString());
        }
      } else if (format === 'json') {
        console.log(JSON.stringify(result.rows, null, 2));
      } else if (format === 'csv') {
        if (result.rows.length > 0) {
          const headers = Object.keys(result.rows[0]).join(',');
          const rows = result.rows.map((row: any) =>
            Object.values(row).join(',')
          ).join('\n');
          console.log(headers + '\n' + rows);
        }
      }

      // Save to file if output specified
      if (options.output) {
        await fs.writeFile(options.output, JSON.stringify(result.rows, null, 2));
        console.log(chalk.green('\n✓ Results saved to:'), options.output);
      }

    } else {
      spinner.fail(`Query failed: ${result.error}`);
      process.exit(1);
    }

  } catch (error) {
    spinner.fail('Failed to execute federated query');
    logger.error('Federation query error:', error);
    throw error;
  }
}

/**
 * Command: ai-shell federation status
 * Show federation status and connected databases
 */
export async function federationStatus(options: {
  detailed?: boolean;
  database?: string;
}): Promise<void> {
  const spinner = ora('Fetching federation status').start();

  try {
    const engine = await getFederationEngine();

    // Get federation status
    const status = await engine.getStatus(options.database);

    spinner.succeed('Federation status retrieved');

    console.log(chalk.cyan('\nFederation Status:'));
    console.log(chalk.green('✓ Status:'), status.status);
    console.log(chalk.green('✓ Total databases:'), status.totalDatabases);
    console.log(chalk.green('✓ Active connections:'), status.activeConnections);
    console.log(chalk.green('✓ Cached queries:'), status.cachedQueries);

    // Display database details
    console.log(chalk.cyan('\nConnected Databases:'));
    const table = new Table({
      head: ['Alias', 'Type', 'Status', 'Schemas', 'Last Query'],
      style: { head: ['cyan'] }
    });

    status.databases.forEach((db: any) => {
      table.push([
        db.alias,
        db.type,
        db.status === 'connected' ? chalk.green('connected') : chalk.red('disconnected'),
        db.schemas.length,
        db.lastQuery || 'never'
      ]);
    });

    console.log(table.toString());

    if (options.detailed) {
      console.log(chalk.cyan('\nPerformance Metrics:'));
      console.log(chalk.green('✓ Total queries:'), status.metrics.totalQueries);
      console.log(chalk.green('✓ Avg execution time:'), `${status.metrics.avgExecutionTime}ms`);
      console.log(chalk.green('✓ Cache hit rate:'), `${status.metrics.cacheHitRate}%`);
      console.log(chalk.green('✓ Data transferred:'), status.metrics.dataTransferred);
    }

  } catch (error) {
    spinner.fail('Failed to fetch federation status');
    logger.error('Federation status error:', error);
    throw error;
  }
}

// ============================================================================
// SCHEMA MANAGEMENT COMMANDS (4 commands)
// ============================================================================

/**
 * Command: ai-shell schema diff <source> <target>
 * Compare schemas between two databases
 */
export async function schemaDiff(
  source: string,
  target: string,
  options: {
    output?: string;
    format?: 'text' | 'json' | 'sql';
    ignoreData?: boolean;
  }
): Promise<void> {
  const spinner = ora(`Comparing schemas: ${source} vs ${target}`).start();

  try {
    const manager = await getSchemaManager();

    // Perform schema diff
    const diff = await manager.comparSchemas(source, target, {
      ignoreData: options.ignoreData
    });

    spinner.succeed('Schema comparison completed');

    console.log(chalk.cyan('\nSchema Differences:'));
    console.log(chalk.green('✓ Tables added:'), diff.tablesAdded.length);
    console.log(chalk.green('✓ Tables removed:'), diff.tablesRemoved.length);
    console.log(chalk.green('✓ Tables modified:'), diff.tablesModified.length);
    console.log(chalk.green('✓ Columns changed:'), diff.columnsChanged);
    console.log(chalk.green('✓ Indexes changed:'), diff.indexesChanged);

    // Display detailed differences
    if (diff.tablesAdded.length > 0) {
      console.log(chalk.cyan('\nTables Added:'));
      diff.tablesAdded.forEach((table: string) => {
        console.log(chalk.green('  +'), table);
      });
    }

    if (diff.tablesRemoved.length > 0) {
      console.log(chalk.cyan('\nTables Removed:'));
      diff.tablesRemoved.forEach((table: string) => {
        console.log(chalk.red('  -'), table);
      });
    }

    if (diff.tablesModified.length > 0) {
      console.log(chalk.cyan('\nTables Modified:'));
      diff.tablesModified.forEach((table: any) => {
        console.log(chalk.yellow('  ~'), table.name);
        table.changes.forEach((change: any) => {
          console.log(chalk.gray('    -'), change.description);
        });
      });
    }

    // Generate migration SQL if requested
    const format = options.format || 'text';
    if (format === 'sql') {
      const migrationSql = await manager.generateMigrationSql(diff);
      console.log(chalk.cyan('\nMigration SQL:'));
      console.log(migrationSql);
    }

    // Save to file if output specified
    if (options.output) {
      const content = format === 'json'
        ? JSON.stringify(diff, null, 2)
        : format === 'sql'
        ? await manager.generateMigrationSql(diff)
        : manager.formatDiffAsText(diff);

      await fs.writeFile(options.output, content);
      console.log(chalk.green('\n✓ Diff saved to:'), options.output);
    }

  } catch (error) {
    spinner.fail('Failed to compare schemas');
    logger.error('Schema diff error:', error);
    throw error;
  }
}

/**
 * Command: ai-shell schema sync <source> <target>
 * Synchronize schema from source to target database
 */
export async function schemaSync(
  source: string,
  target: string,
  options: {
    dryRun?: boolean;
    force?: boolean;
    backup?: boolean;
  }
): Promise<void> {
  const spinner = ora(`Synchronizing schema: ${source} → ${target}`).start();

  try {
    const manager = await getSchemaManager();

    // Perform schema diff first
    spinner.text = 'Analyzing schema differences...';
    const diff = await manager.comparSchemas(source, target);

    if (diff.isEmpty) {
      spinner.info('Schemas are already in sync');
      return;
    }

    // Confirm sync if not forced
    if (!options.force && !options.dryRun) {
      spinner.stop();
      const { confirm } = await inquirer.prompt([
        {
          type: 'confirm',
          name: 'confirm',
          message: `This will modify ${target}. Continue?`,
          default: false
        }
      ]);

      if (!confirm) {
        console.log(chalk.yellow('Operation cancelled'));
        return;
      }
      spinner.start();
    }

    // Create backup if requested
    if (options.backup && !options.dryRun) {
      spinner.text = 'Creating backup...';
      const backup = await manager.createBackup(target);
      console.log(chalk.green('\n✓ Backup created:'), backup.path);
      spinner.start();
    }

    // Perform sync
    spinner.text = `${options.dryRun ? 'Simulating' : 'Executing'} schema sync...`;
    const result = await manager.syncSchemas(source, target, {
      dryRun: options.dryRun
    });

    if (result.success) {
      spinner.succeed(`Schema sync ${options.dryRun ? 'simulated' : 'completed'} successfully`);

      console.log(chalk.green('\n✓ Changes applied:'), result.changesApplied);
      console.log(chalk.green('✓ Statements executed:'), result.statementsExecuted);
      console.log(chalk.green('✓ Execution time:'), `${result.executionTime}ms`);

      if (options.dryRun) {
        console.log(chalk.cyan('\nSQL Statements (dry run):'));
        result.statements.forEach((stmt: string, i: number) => {
          console.log(chalk.gray(`${i + 1}.`), stmt);
        });
      }

      if (result.warnings.length > 0) {
        console.log(chalk.yellow('\n⚠ Warnings:'));
        result.warnings.forEach((warning: string) => {
          console.log(chalk.yellow('  -'), warning);
        });
      }

    } else {
      spinner.fail(`Schema sync failed: ${result.error}`);
      process.exit(1);
    }

  } catch (error) {
    spinner.fail('Failed to sync schemas');
    logger.error('Schema sync error:', error);
    throw error;
  }
}

/**
 * Command: ai-shell schema export <database>
 * Export schema to file
 */
export async function schemaExport(
  database: string,
  options: {
    output?: string;
    format?: 'sql' | 'json' | 'yaml';
    includeData?: boolean;
    tables?: string;
  }
): Promise<void> {
  const spinner = ora(`Exporting schema from ${database}`).start();

  try {
    const manager = await getSchemaManager();

    // Parse tables filter
    const tablesFilter = options.tables ? options.tables.split(',') : undefined;

    // Export schema
    const schema = await manager.exportSchema(database, {
      format: options.format || 'sql',
      includeData: options.includeData,
      tables: tablesFilter
    });

    // Determine output path
    const outputPath = options.output || `schema-${database}-${Date.now()}.${options.format || 'sql'}`;

    // Write to file
    await fs.writeFile(outputPath, schema.content);

    spinner.succeed(`Schema exported from ${database}`);
    console.log(chalk.green('\n✓ Output file:'), outputPath);
    console.log(chalk.green('✓ Format:'), schema.format);
    console.log(chalk.green('✓ Tables exported:'), schema.tables.length);
    console.log(chalk.green('✓ Size:'), `${(schema.content.length / 1024).toFixed(2)} KB`);

    if (options.includeData) {
      console.log(chalk.green('✓ Rows exported:'), schema.rowCount);
    }

  } catch (error) {
    spinner.fail('Failed to export schema');
    logger.error('Schema export error:', error);
    throw error;
  }
}

/**
 * Command: ai-shell schema import <file>
 * Import schema from file
 */
export async function schemaImport(
  file: string,
  options: {
    database?: string;
    format?: 'sql' | 'json' | 'yaml';
    dryRun?: boolean;
    force?: boolean;
  }
): Promise<void> {
  const spinner = ora(`Importing schema from ${file}`).start();

  try {
    const manager = await getSchemaManager();

    // Read schema file
    const content = await fs.readFile(file, 'utf-8');

    // Detect format if not specified
    const format = options.format || path.extname(file).slice(1) as any;

    // Confirm import if not forced
    if (!options.force && !options.dryRun) {
      spinner.stop();
      const { confirm } = await inquirer.prompt([
        {
          type: 'confirm',
          name: 'confirm',
          message: `This will modify database ${options.database || 'default'}. Continue?`,
          default: false
        }
      ]);

      if (!confirm) {
        console.log(chalk.yellow('Operation cancelled'));
        return;
      }
      spinner.start();
    }

    // Import schema
    spinner.text = `${options.dryRun ? 'Validating' : 'Importing'} schema...`;
    const result = await manager.importSchema(content, {
      database: options.database,
      format,
      dryRun: options.dryRun
    });

    if (result.success) {
      spinner.succeed(`Schema ${options.dryRun ? 'validated' : 'imported'} successfully`);

      console.log(chalk.green('\n✓ Tables created:'), result.tablesCreated);
      console.log(chalk.green('✓ Statements executed:'), result.statementsExecuted);
      console.log(chalk.green('✓ Execution time:'), `${result.executionTime}ms`);

      if (result.dataImported) {
        console.log(chalk.green('✓ Rows inserted:'), result.rowsInserted);
      }

      if (result.warnings.length > 0) {
        console.log(chalk.yellow('\n⚠ Warnings:'));
        result.warnings.forEach((warning: string) => {
          console.log(chalk.yellow('  -'), warning);
        });
      }

    } else {
      spinner.fail(`Schema import failed: ${result.error}`);
      process.exit(1);
    }

  } catch (error) {
    spinner.fail('Failed to import schema');
    logger.error('Schema import error:', error);
    throw error;
  }
}

// ============================================================================
// AUTONOMOUS AGENT COMMANDS (4 commands)
// ============================================================================

/**
 * Command: ai-shell ada start
 * Start autonomous database agent
 */
export async function adaStart(options: {
  mode?: 'monitoring' | 'optimization' | 'full';
  interval?: number;
  autoFix?: boolean;
}): Promise<void> {
  const spinner = ora('Starting Autonomous Database Agent (ADA)').start();

  try {
    const agent = await getADAAgent();

    // Start agent
    const result = await agent.start({
      mode: options.mode || 'full',
      checkInterval: options.interval || 60000, // 1 minute default
      autoFix: options.autoFix !== false
    });

    if (result.success) {
      spinner.succeed('ADA started successfully');

      console.log(chalk.green('\n✓ Agent ID:'), result.agentId);
      console.log(chalk.green('✓ Mode:'), result.mode);
      console.log(chalk.green('✓ Check interval:'), `${result.checkInterval / 1000}s`);
      console.log(chalk.green('✓ Auto-fix enabled:'), result.autoFix);
      console.log(chalk.green('✓ Monitoring databases:'), result.databases.length);

      console.log(chalk.cyan('\nActive Capabilities:'));
      result.capabilities.forEach((cap: string) => {
        console.log(chalk.green('  ✓'), cap);
      });

      console.log(chalk.cyan('\n💡 Use "ai-shell ada status" to monitor ADA'));
      console.log(chalk.cyan('💡 Use "ai-shell ada stop" to stop ADA'));

    } else {
      spinner.fail(`Failed to start ADA: ${result.error}`);
      process.exit(1);
    }

  } catch (error) {
    spinner.fail('Failed to start ADA');
    logger.error('ADA start error:', error);
    throw error;
  }
}

/**
 * Command: ai-shell ada stop
 * Stop autonomous database agent
 */
export async function adaStop(options: {
  force?: boolean;
  export?: boolean;
}): Promise<void> {
  const spinner = ora('Stopping Autonomous Database Agent (ADA)').start();

  try {
    const agent = await getADAAgent();

    // Stop agent
    const result = await agent.stop({
      force: options.force,
      exportMetrics: options.export
    });

    if (result.success) {
      spinner.succeed('ADA stopped successfully');

      console.log(chalk.green('\n✓ Runtime:'), result.runtime);
      console.log(chalk.green('✓ Checks performed:'), result.checksPerformed);
      console.log(chalk.green('✓ Issues detected:'), result.issuesDetected);
      console.log(chalk.green('✓ Fixes applied:'), result.fixesApplied);

      if (options.export && result.metricsExported) {
        console.log(chalk.green('\n✓ Metrics exported to:'), result.metricsPath);
      }

    } else {
      spinner.fail(`Failed to stop ADA: ${result.error}`);
      process.exit(1);
    }

  } catch (error) {
    spinner.fail('Failed to stop ADA');
    logger.error('ADA stop error:', error);
    throw error;
  }
}

/**
 * Command: ai-shell ada status
 * Check autonomous agent status
 */
export async function adaStatus(options: {
  detailed?: boolean;
  watch?: boolean;
  interval?: number;
}): Promise<void> {
  const displayStatus = async () => {
    try {
      const agent = await getADAAgent();
      const status = await agent.getStatus();

      console.clear();
      console.log(chalk.cyan.bold('╔════════════════════════════════════════╗'));
      console.log(chalk.cyan.bold('║  Autonomous Database Agent (ADA)       ║'));
      console.log(chalk.cyan.bold('╚════════════════════════════════════════╝\n'));

      // Status overview
      const statusColor = status.running ? chalk.green : chalk.red;
      console.log(chalk.cyan('Status:'), statusColor(status.running ? 'RUNNING' : 'STOPPED'));

      if (status.running) {
        console.log(chalk.cyan('Mode:'), status.mode);
        console.log(chalk.cyan('Uptime:'), status.uptime);
        console.log(chalk.cyan('Next check:'), status.nextCheck);
        console.log(chalk.cyan('Databases monitored:'), status.databases.length);
      }

      // Recent activity
      if (status.running && options.detailed) {
        console.log(chalk.cyan('\nRecent Activity:'));
        const activityTable = new Table({
          head: ['Timestamp', 'Type', 'Description', 'Status'],
          style: { head: ['cyan'] }
        });

        status.recentActivity.forEach((activity: any) => {
          const statusIcon = activity.success ? chalk.green('✓') : chalk.red('✗');
          activityTable.push([
            activity.timestamp,
            activity.type,
            activity.description,
            statusIcon
          ]);
        });

        console.log(activityTable.toString());

        // Performance metrics
        console.log(chalk.cyan('\nPerformance Metrics:'));
        console.log(chalk.green('✓ Checks performed:'), status.metrics.checksPerformed);
        console.log(chalk.green('✓ Issues detected:'), status.metrics.issuesDetected);
        console.log(chalk.green('✓ Fixes applied:'), status.metrics.fixesApplied);
        console.log(chalk.green('✓ Success rate:'), `${status.metrics.successRate}%`);
        console.log(chalk.green('✓ Avg response time:'), `${status.metrics.avgResponseTime}ms`);
      }

      // Current issues
      if (status.running && status.currentIssues.length > 0) {
        console.log(chalk.yellow('\n⚠ Current Issues:'));
        status.currentIssues.forEach((issue: any) => {
          console.log(chalk.yellow('  •'), issue.description);
          console.log(chalk.gray('    Database:'), issue.database);
          console.log(chalk.gray('    Severity:'), issue.severity);
        });
      }

    } catch (error) {
      console.error(chalk.red('Error fetching ADA status:'), error);
    }
  };

  if (options.watch) {
    // Watch mode - continuously update
    const interval = options.interval || 5000; // 5 seconds default
    console.log(chalk.cyan(`Watching ADA status (updating every ${interval / 1000}s)...\n`));
    console.log(chalk.gray('Press Ctrl+C to exit\n'));

    await displayStatus();
    setInterval(displayStatus, interval);
  } else {
    // Single status check
    const spinner = ora('Fetching ADA status').start();
    spinner.stop();
    await displayStatus();
  }
}

/**
 * Command: ai-shell ada configure
 * Configure autonomous agent settings
 */
export async function adaConfigure(options: {
  mode?: 'monitoring' | 'optimization' | 'full';
  interval?: number;
  autoFix?: boolean;
  alertThreshold?: number;
  databases?: string;
  interactive?: boolean;
}): Promise<void> {
  const spinner = ora('Configuring Autonomous Database Agent').start();

  try {
    const agent = await getADAAgent();

    let config: any = {};

    if (options.interactive) {
      spinner.stop();
      // Interactive configuration
      const answers = await inquirer.prompt([
        {
          type: 'list',
          name: 'mode',
          message: 'Select ADA operation mode:',
          choices: [
            { name: 'Monitoring only', value: 'monitoring' },
            { name: 'Optimization only', value: 'optimization' },
            { name: 'Full autonomous (monitoring + optimization)', value: 'full' }
          ],
          default: 'full'
        },
        {
          type: 'number',
          name: 'interval',
          message: 'Check interval (seconds):',
          default: 60
        },
        {
          type: 'confirm',
          name: 'autoFix',
          message: 'Enable automatic fixes?',
          default: true
        },
        {
          type: 'number',
          name: 'alertThreshold',
          message: 'Alert threshold (0-100):',
          default: 80
        },
        {
          type: 'checkbox',
          name: 'enabledCapabilities',
          message: 'Select enabled capabilities:',
          choices: [
            'Performance Monitoring',
            'Index Optimization',
            'Query Optimization',
            'Connection Pool Management',
            'Deadlock Detection',
            'Storage Optimization',
            'Backup Verification',
            'Security Auditing'
          ]
        }
      ]);
      config = answers;
      spinner.start();
    } else {
      // Non-interactive configuration
      config = {
        mode: options.mode,
        interval: options.interval,
        autoFix: options.autoFix,
        alertThreshold: options.alertThreshold,
        databases: options.databases ? options.databases.split(',') : undefined
      };
    }

    // Apply configuration
    const result = await agent.configure(config);

    if (result.success) {
      spinner.succeed('ADA configured successfully');

      console.log(chalk.green('\n✓ Configuration updated'));
      console.log(chalk.cyan('\nCurrent Settings:'));
      console.log(chalk.green('  Mode:'), result.config.mode);
      console.log(chalk.green('  Check interval:'), `${result.config.interval}s`);
      console.log(chalk.green('  Auto-fix:'), result.config.autoFix ? 'enabled' : 'disabled');
      console.log(chalk.green('  Alert threshold:'), `${result.config.alertThreshold}%`);
      console.log(chalk.green('  Monitored databases:'), result.config.databases.length);

      if (result.config.enabledCapabilities) {
        console.log(chalk.cyan('\nEnabled Capabilities:'));
        result.config.enabledCapabilities.forEach((cap: string) => {
          console.log(chalk.green('  ✓'), cap);
        });
      }

      // Save configuration
      await agent.saveConfig();
      console.log(chalk.green('\n✓ Configuration saved'));

    } else {
      spinner.fail(`Failed to configure ADA: ${result.error}`);
      process.exit(1);
    }

  } catch (error) {
    spinner.fail('Failed to configure ADA');
    logger.error('ADA configure error:', error);
    throw error;
  }
}

// ============================================================================
// EXPORT CLI FUNCTIONS
// ============================================================================

export default {
  // Slack
  slackSetup,
  slackNotify,
  slackAlert,
  slackReport,

  // Email
  emailSetup,
  emailSend,
  emailAlert,
  emailReport,

  // Federation
  federationAdd,
  federationRemove,
  federationQuery,
  federationStatus,

  // Schema Management
  schemaDiff,
  schemaSync,
  schemaExport,
  schemaImport,

  // Autonomous Agent
  adaStart,
  adaStop,
  adaStatus,
  adaConfigure
};
