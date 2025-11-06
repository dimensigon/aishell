#!/usr/bin/env node

/**
 * Slack Integration for AI-Shell
 *
 * Provides comprehensive Slack notification capabilities including:
 * - Slack Web API integration with bot tokens
 * - Webhook fallback for simple notifications
 * - Rich message formatting with Block Kit
 * - Alert severity-based formatting (colors, emojis)
 * - Channel routing by alert type
 * - Interactive buttons for quick actions
 * - Thread support for related alerts
 * - User mentions and @channel notifications
 * - Slash command support for AI-Shell operations
 *
 * @module notification-slack
 */

import { WebClient, ChatPostMessageArguments, Block, KnownBlock } from '@slack/web-api';
import * as fs from 'fs/promises';
import * as fsSync from 'fs';
import * as path from 'path';
import axios, { AxiosInstance } from 'axios';
import * as crypto from 'crypto';

// ============================================================================
// Types and Interfaces
// ============================================================================

export interface SlackConfig {
  token?: string;
  webhookUrl?: string;
  defaultChannel?: string;
  enableThreads?: boolean;
  enableInteractive?: boolean;
  channelRouting?: {
    [alertType: string]: string;
  };
  rateLimiting?: {
    maxMessagesPerMinute?: number;
    burstSize?: number;
  };
  mentions?: {
    criticalAlerts?: string[];
    securityAlerts?: string[];
  };
}

export interface SlackMessage {
  channel: string;
  text: string;
  blocks?: (Block | KnownBlock)[];
  thread_ts?: string;
  attachments?: SlackAttachment[];
  username?: string;
  icon_emoji?: string;
  icon_url?: string;
  mrkdwn?: boolean;
}

export interface SlackAttachment {
  color?: string;
  pretext?: string;
  text?: string;
  fields?: SlackField[];
  footer?: string;
  footer_icon?: string;
  ts?: number;
  actions?: SlackAction[];
}

export interface SlackField {
  title: string;
  value: string;
  short?: boolean;
}

export interface SlackAction {
  type: string;
  text: string;
  url?: string;
  value?: string;
  style?: 'default' | 'primary' | 'danger';
}

export interface AlertMessage {
  type: 'query' | 'security' | 'performance' | 'backup' | 'health' | 'system';
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  title: string;
  description: string;
  details?: Record<string, any>;
  timestamp?: number;
  source?: string;
  threadId?: string;
}

export interface InteractiveAction {
  type: 'button' | 'select' | 'overflow';
  actionId: string;
  text: string;
  value?: string;
  style?: 'primary' | 'danger';
  url?: string;
  confirm?: {
    title: string;
    text: string;
    confirm: string;
    deny: string;
  };
}

// ============================================================================
// Slack Integration Client
// ============================================================================

export class SlackIntegration {
  private client: WebClient | null = null;
  private webhookClient: AxiosInstance;
  private config: SlackConfig;
  private configPath: string;
  private rateLimiter: RateLimiter;
  private threadMap: Map<string, string> = new Map();

  constructor(configPath?: string) {
    this.configPath = configPath || path.join(process.cwd(), '.aishell', 'slack-config.json');
    this.config = this.loadConfig();
    this.webhookClient = axios.create({
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Initialize rate limiter
    const maxRate = this.config.rateLimiting?.maxMessagesPerMinute || 60;
    const burst = this.config.rateLimiting?.burstSize || 10;
    this.rateLimiter = new RateLimiter(maxRate, burst);

    // Initialize Slack Web API client if token provided
    if (this.config.token) {
      this.client = new WebClient(this.config.token);
    }
  }

  /**
   * Load Slack configuration from disk
   */
  private loadConfig(): SlackConfig {
    try {
      if (fsSync.existsSync(this.configPath)) {
        const data = fsSync.readFileSync(this.configPath, 'utf-8');
        return JSON.parse(data);
      }
    } catch (error) {
      console.warn('Failed to load Slack config:', error);
    }

    return {
      defaultChannel: '#ai-shell-alerts',
      enableThreads: true,
      enableInteractive: true,
      channelRouting: {
        query: '#ai-shell-queries',
        security: '#ai-shell-security',
        performance: '#ai-shell-performance',
        backup: '#ai-shell-backups',
        health: '#ai-shell-health',
        system: '#ai-shell-system',
      },
      rateLimiting: {
        maxMessagesPerMinute: 60,
        burstSize: 10,
      },
      mentions: {
        criticalAlerts: ['@channel'],
        securityAlerts: ['@security-team'],
      },
    };
  }

  /**
   * Save Slack configuration to disk
   */
  public saveConfig(config: Partial<SlackConfig>): void {
    this.config = { ...this.config, ...config };
    const dir = path.dirname(this.configPath);
    if (!fsSync.existsSync(dir)) {
      fsSync.mkdirSync(dir, { recursive: true });
    }
    fsSync.writeFileSync(this.configPath, JSON.stringify(this.config, null, 2), 'utf-8');

    // Reinitialize client if token changed
    if (config.token) {
      this.client = new WebClient(config.token);
    }
  }

  /**
   * Get current configuration
   */
  public getConfig(): SlackConfig {
    return { ...this.config };
  }

  /**
   * Send alert message to Slack
   */
  public async sendAlert(alert: AlertMessage): Promise<boolean> {
    try {
      // Check rate limiting
      if (!this.rateLimiter.tryConsume()) {
        console.warn('Rate limit exceeded, dropping message');
        return false;
      }

      // Determine channel
      const channel = this.resolveChannel(alert.type);

      // Build message
      const message = this.buildAlertMessage(alert, channel);

      // Send via Web API or webhook
      let result: any;
      if (this.client) {
        result = await this.sendViaWebAPI(message);
      } else if (this.config.webhookUrl) {
        result = await this.sendViaWebhook(message);
      } else {
        throw new Error('No Slack integration configured (token or webhook required)');
      }

      // Store thread_ts for future messages
      if (alert.threadId && result.ts) {
        this.threadMap.set(alert.threadId, result.ts);
      }

      return true;
    } catch (error) {
      console.error('Failed to send Slack alert:', error);
      return false;
    }
  }

  /**
   * Send message via Slack Web API
   */
  private async sendViaWebAPI(message: SlackMessage): Promise<any> {
    if (!this.client) {
      throw new Error('Slack Web API client not initialized');
    }

    const args: ChatPostMessageArguments = {
      channel: message.channel,
      text: message.text,
      blocks: message.blocks,
      thread_ts: message.thread_ts,
      username: message.username,
      icon_emoji: message.icon_emoji,
      icon_url: message.icon_url,
    };

    const result = await this.client.chat.postMessage(args);
    return result;
  }

  /**
   * Send message via webhook (fallback)
   */
  private async sendViaWebhook(message: SlackMessage): Promise<any> {
    if (!this.config.webhookUrl) {
      throw new Error('Webhook URL not configured');
    }

    const payload = {
      text: message.text,
      blocks: message.blocks,
      username: message.username,
      icon_emoji: message.icon_emoji,
      icon_url: message.icon_url,
    };

    const response = await this.webhookClient.post(this.config.webhookUrl, payload);
    return { ok: response.status === 200 };
  }

  /**
   * Build Slack message from alert
   */
  private buildAlertMessage(alert: AlertMessage, channel: string): SlackMessage {
    const emoji = this.getSeverityEmoji(alert.severity);
    const color = this.getSeverityColor(alert.severity);
    const timestamp = alert.timestamp || Date.now();

    // Build blocks for rich formatting
    const blocks: KnownBlock[] = [];

    // Header block
    blocks.push({
      type: 'header',
      text: {
        type: 'plain_text',
        text: `${emoji} ${alert.title}`,
        emoji: true,
      },
    });

    // Context block (type and severity)
    blocks.push({
      type: 'context',
      elements: [
        {
          type: 'mrkdwn',
          text: `*Type:* ${alert.type} | *Severity:* ${alert.severity.toUpperCase()} | *Source:* ${alert.source || 'AI-Shell'}`,
        },
      ],
    });

    // Description section
    blocks.push({
      type: 'section',
      text: {
        type: 'mrkdwn',
        text: alert.description,
      },
    });

    // Details section (if provided)
    if (alert.details && Object.keys(alert.details).length > 0) {
      const fields: any[] = [];
      for (const [key, value] of Object.entries(alert.details)) {
        fields.push({
          type: 'mrkdwn',
          text: `*${this.formatFieldName(key)}:*\n${this.formatFieldValue(value)}`,
        });
      }

      blocks.push({
        type: 'section',
        fields: fields.slice(0, 10), // Slack limits to 10 fields
      });
    }

    // Divider
    blocks.push({
      type: 'divider',
    });

    // Add interactive actions
    if (this.config.enableInteractive) {
      const actions = this.buildActions(alert);
      if (actions.length > 0) {
        blocks.push({
          type: 'actions',
          elements: actions as any,
        });
      }
    }

    // Add mentions for critical/security alerts
    let text = `${emoji} ${alert.title}`;
    if (alert.severity === 'critical' && this.config.mentions?.criticalAlerts) {
      text = `${this.config.mentions.criticalAlerts.join(' ')} ${text}`;
    } else if (alert.type === 'security' && this.config.mentions?.securityAlerts) {
      text = `${this.config.mentions.securityAlerts.join(' ')} ${text}`;
    }

    // Get thread_ts if part of existing thread
    let thread_ts: string | undefined;
    if (this.config.enableThreads && alert.threadId) {
      thread_ts = this.threadMap.get(alert.threadId);
    }

    return {
      channel,
      text,
      blocks,
      thread_ts,
      username: 'AI-Shell Monitor',
      icon_emoji: ':robot_face:',
    };
  }

  /**
   * Build interactive actions for alert
   */
  private buildActions(alert: AlertMessage): any[] {
    const actions: any[] = [];

    // Acknowledge button
    actions.push({
      type: 'button',
      text: {
        type: 'plain_text',
        text: 'Acknowledge',
        emoji: true,
      },
      action_id: 'acknowledge_alert',
      value: JSON.stringify({ alertType: alert.type, timestamp: alert.timestamp }),
      style: 'primary',
    });

    // View Details button
    if (alert.details) {
      actions.push({
        type: 'button',
        text: {
          type: 'plain_text',
          text: 'View Details',
          emoji: true,
        },
        action_id: 'view_details',
        value: JSON.stringify({ alertType: alert.type, timestamp: alert.timestamp }),
      });
    }

    // Type-specific actions
    if (alert.type === 'query' && alert.details?.query) {
      actions.push({
        type: 'button',
        text: {
          type: 'plain_text',
          text: 'Run Query',
          emoji: true,
        },
        action_id: 'run_query',
        value: alert.details.query,
      });
    }

    if (alert.type === 'security' && alert.severity === 'critical') {
      actions.push({
        type: 'button',
        text: {
          type: 'plain_text',
          text: 'Investigate',
          emoji: true,
        },
        action_id: 'investigate_security',
        value: JSON.stringify({ alertType: alert.type, timestamp: alert.timestamp }),
        style: 'danger',
      });
    }

    return actions;
  }

  /**
   * Resolve channel based on alert type
   */
  private resolveChannel(alertType: string): string {
    if (this.config.channelRouting && this.config.channelRouting[alertType]) {
      return this.config.channelRouting[alertType];
    }
    return this.config.defaultChannel || '#ai-shell-alerts';
  }

  /**
   * Get emoji for severity level
   */
  private getSeverityEmoji(severity: string): string {
    const emojiMap: Record<string, string> = {
      critical: '🚨',
      high: '⚠️',
      medium: '⚡',
      low: 'ℹ️',
      info: '📊',
    };
    return emojiMap[severity] || '📋';
  }

  /**
   * Get color for severity level
   */
  private getSeverityColor(severity: string): string {
    const colorMap: Record<string, string> = {
      critical: '#FF0000',
      high: '#FF6B00',
      medium: '#FFB900',
      low: '#00B7FF',
      info: '#00D084',
    };
    return colorMap[severity] || '#CCCCCC';
  }

  /**
   * Format field name for display
   */
  private formatFieldName(name: string): string {
    return name
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (l) => l.toUpperCase());
  }

  /**
   * Format field value for display
   */
  private formatFieldValue(value: any): string {
    if (typeof value === 'object') {
      return '```' + JSON.stringify(value, null, 2) + '```';
    }
    if (typeof value === 'number') {
      return value.toLocaleString();
    }
    return String(value);
  }

  /**
   * Test Slack integration
   */
  public async testConnection(): Promise<{ success: boolean; message: string }> {
    try {
      const testAlert: AlertMessage = {
        type: 'system',
        severity: 'info',
        title: 'Slack Integration Test',
        description: 'This is a test message from AI-Shell to verify Slack integration is working correctly.',
        details: {
          timestamp: new Date().toISOString(),
          version: '1.0.0',
          status: 'operational',
        },
        timestamp: Date.now(),
        source: 'AI-Shell Test',
      };

      const success = await this.sendAlert(testAlert);

      if (success) {
        return {
          success: true,
          message: 'Slack integration test successful! Check your configured channel for the test message.',
        };
      } else {
        return {
          success: false,
          message: 'Failed to send test message to Slack.',
        };
      }
    } catch (error) {
      return {
        success: false,
        message: `Slack test failed: ${error instanceof Error ? error.message : String(error)}`,
      };
    }
  }

  /**
   * List available channels
   */
  public async listChannels(): Promise<Array<{ id: string; name: string; isMember: boolean }>> {
    if (!this.client) {
      throw new Error('Slack Web API client not initialized');
    }

    try {
      const result = await this.client.conversations.list({
        types: 'public_channel,private_channel',
        exclude_archived: true,
      });

      if (!result.channels) {
        return [];
      }

      return result.channels.map((channel: any) => ({
        id: channel.id,
        name: channel.name,
        isMember: channel.is_member || false,
      }));
    } catch (error) {
      console.error('Failed to list Slack channels:', error);
      return [];
    }
  }

  /**
   * Send query alert
   */
  public async sendQueryAlert(query: string, result: any, metrics?: any): Promise<boolean> {
    const alert: AlertMessage = {
      type: 'query',
      severity: metrics?.executionTime > 5000 ? 'medium' : 'low',
      title: 'Query Executed',
      description: `AI-Shell query completed with ${result.rows?.length || 0} results.`,
      details: {
        query: query.length > 200 ? query.substring(0, 200) + '...' : query,
        rows_returned: result.rows?.length || 0,
        execution_time: metrics?.executionTime ? `${metrics.executionTime}ms` : 'N/A',
        timestamp: new Date().toISOString(),
      },
      timestamp: Date.now(),
    };

    return this.sendAlert(alert);
  }

  /**
   * Send security alert
   */
  public async sendSecurityAlert(
    title: string,
    description: string,
    severity: 'critical' | 'high' | 'medium' | 'low',
    details?: Record<string, any>
  ): Promise<boolean> {
    const alert: AlertMessage = {
      type: 'security',
      severity,
      title,
      description,
      details: {
        ...details,
        timestamp: new Date().toISOString(),
        action_required: severity === 'critical' || severity === 'high',
      },
      timestamp: Date.now(),
    };

    return this.sendAlert(alert);
  }

  /**
   * Send performance alert
   */
  public async sendPerformanceAlert(
    metric: string,
    value: number,
    threshold: number,
    details?: Record<string, any>
  ): Promise<boolean> {
    const percentOver = ((value - threshold) / threshold) * 100;
    const severity: AlertMessage['severity'] = percentOver > 100 ? 'critical' : percentOver > 50 ? 'high' : 'medium';

    const alert: AlertMessage = {
      type: 'performance',
      severity,
      title: `Performance Alert: ${metric}`,
      description: `${metric} is ${percentOver.toFixed(1)}% over threshold (${value} vs ${threshold})`,
      details: {
        metric,
        current_value: value,
        threshold,
        percent_over: `${percentOver.toFixed(1)}%`,
        ...details,
      },
      timestamp: Date.now(),
    };

    return this.sendAlert(alert);
  }

  /**
   * Send backup notification
   */
  public async sendBackupNotification(
    success: boolean,
    backupPath: string,
    size?: number,
    details?: Record<string, any>
  ): Promise<boolean> {
    const alert: AlertMessage = {
      type: 'backup',
      severity: success ? 'info' : 'high',
      title: success ? 'Backup Completed' : 'Backup Failed',
      description: success
        ? `Database backup completed successfully.`
        : `Database backup failed. Manual intervention required.`,
      details: {
        backup_path: backupPath,
        backup_size: size ? `${(size / 1024 / 1024).toFixed(2)} MB` : 'N/A',
        status: success ? 'success' : 'failed',
        ...details,
      },
      timestamp: Date.now(),
    };

    return this.sendAlert(alert);
  }

  /**
   * Send health update
   */
  public async sendHealthUpdate(
    status: 'healthy' | 'degraded' | 'unhealthy',
    checks: Record<string, boolean>,
    details?: Record<string, any>
  ): Promise<boolean> {
    const severity: AlertMessage['severity'] = status === 'healthy' ? 'info' : status === 'degraded' ? 'medium' : 'high';

    const passedChecks = Object.values(checks).filter(Boolean).length;
    const totalChecks = Object.values(checks).length;

    const alert: AlertMessage = {
      type: 'health',
      severity,
      title: `System Health: ${status.toUpperCase()}`,
      description: `Health check completed: ${passedChecks}/${totalChecks} checks passed.`,
      details: {
        status,
        checks_passed: `${passedChecks}/${totalChecks}`,
        ...checks,
        ...details,
      },
      timestamp: Date.now(),
    };

    return this.sendAlert(alert);
  }
}

// ============================================================================
// Rate Limiter
// ============================================================================

class RateLimiter {
  private tokens: number;
  private lastRefill: number;
  private readonly maxTokens: number;
  private readonly refillRate: number; // tokens per second

  constructor(maxPerMinute: number, burstSize: number) {
    this.maxTokens = burstSize;
    this.tokens = burstSize;
    this.refillRate = maxPerMinute / 60; // convert to per second
    this.lastRefill = Date.now();
  }

  public tryConsume(): boolean {
    this.refill();

    if (this.tokens >= 1) {
      this.tokens -= 1;
      return true;
    }

    return false;
  }

  private refill(): void {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000; // seconds
    const tokensToAdd = elapsed * this.refillRate;

    this.tokens = Math.min(this.maxTokens, this.tokens + tokensToAdd);
    this.lastRefill = now;
  }
}

// ============================================================================
// CLI Commands
// ============================================================================

/**
 * Setup Slack integration
 */
export async function setupSlack(options: {
  token?: string;
  webhook?: string;
  channel?: string;
  configPath?: string;
}): Promise<void> {
  const integration = new SlackIntegration(options.configPath);

  const config: Partial<SlackConfig> = {};

  if (options.token) {
    config.token = options.token;
    console.log('✓ Slack bot token configured');
  }

  if (options.webhook) {
    config.webhookUrl = options.webhook;
    console.log('✓ Slack webhook URL configured');
  }

  if (options.channel) {
    config.defaultChannel = options.channel;
    console.log(`✓ Default channel set to: ${options.channel}`);
  }

  if (Object.keys(config).length === 0) {
    console.error('❌ No configuration provided. Use --token, --webhook, or --channel');
    process.exit(1);
  }

  integration.saveConfig(config);
  console.log('\n✓ Slack integration configured successfully!');
  console.log(`Config saved to: ${options.configPath || path.join(process.cwd(), '.aishell', 'slack-config.json')}`);
}

/**
 * Test Slack connection
 */
export async function testSlack(configPath?: string): Promise<void> {
  const integration = new SlackIntegration(configPath);
  console.log('Testing Slack integration...\n');

  const result = await integration.testConnection();

  if (result.success) {
    console.log('✓', result.message);
  } else {
    console.error('❌', result.message);
    process.exit(1);
  }
}

/**
 * List Slack channels
 */
export async function listSlackChannels(configPath?: string): Promise<void> {
  const integration = new SlackIntegration(configPath);
  console.log('Fetching Slack channels...\n');

  try {
    const channels = await integration.listChannels();

    if (channels.length === 0) {
      console.log('No channels found. Make sure your bot token has the necessary permissions.');
      return;
    }

    console.log(`Found ${channels.length} channels:\n`);

    const memberChannels = channels.filter((c) => c.isMember);
    const otherChannels = channels.filter((c) => !c.isMember);

    if (memberChannels.length > 0) {
      console.log('Channels (Bot is a member):');
      memberChannels.forEach((channel) => {
        console.log(`  - #${channel.name} (${channel.id})`);
      });
      console.log();
    }

    if (otherChannels.length > 0) {
      console.log('Other channels:');
      otherChannels.forEach((channel) => {
        console.log(`  - #${channel.name} (${channel.id})`);
      });
    }
  } catch (error) {
    console.error('❌ Failed to list channels:', error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

/**
 * Configure Slack channel routing
 */
export async function configureSlackRouting(options: {
  alertType: string;
  channel: string;
  configPath?: string;
}): Promise<void> {
  const integration = new SlackIntegration(options.configPath);
  const currentConfig = integration.getConfig();

  const channelRouting = currentConfig.channelRouting || {};
  channelRouting[options.alertType] = options.channel;

  integration.saveConfig({ channelRouting });

  console.log(`✓ Alert type '${options.alertType}' will now route to channel: ${options.channel}`);
}

/**
 * Show current Slack configuration
 */
export async function showSlackConfig(configPath?: string): Promise<void> {
  const integration = new SlackIntegration(configPath);
  const config = integration.getConfig();

  console.log('Current Slack Configuration:\n');
  console.log('Token configured:', config.token ? '✓ Yes' : '✗ No');
  console.log('Webhook configured:', config.webhookUrl ? '✓ Yes' : '✗ No');
  console.log('Default channel:', config.defaultChannel || 'Not set');
  console.log('Threads enabled:', config.enableThreads ? '✓ Yes' : '✗ No');
  console.log('Interactive buttons enabled:', config.enableInteractive ? '✓ Yes' : '✗ No');

  if (config.channelRouting && Object.keys(config.channelRouting).length > 0) {
    console.log('\nChannel Routing:');
    for (const [alertType, channel] of Object.entries(config.channelRouting)) {
      console.log(`  ${alertType}: ${channel}`);
    }
  }

  if (config.rateLimiting) {
    console.log('\nRate Limiting:');
    console.log(`  Max messages/minute: ${config.rateLimiting.maxMessagesPerMinute || 'Default'}`);
    console.log(`  Burst size: ${config.rateLimiting.burstSize || 'Default'}`);
  }

  if (config.mentions) {
    console.log('\nMentions:');
    if (config.mentions.criticalAlerts) {
      console.log(`  Critical alerts: ${config.mentions.criticalAlerts.join(', ')}`);
    }
    if (config.mentions.securityAlerts) {
      console.log(`  Security alerts: ${config.mentions.securityAlerts.join(', ')}`);
    }
  }
}

// ============================================================================
// Main CLI
// ============================================================================

if (require.main === module) {
  const args = process.argv.slice(2);
  const command = args[0];

  switch (command) {
    case 'setup':
      setupSlack({
        token: args.includes('--token') ? args[args.indexOf('--token') + 1] : undefined,
        webhook: args.includes('--webhook') ? args[args.indexOf('--webhook') + 1] : undefined,
        channel: args.includes('--channel') ? args[args.indexOf('--channel') + 1] : undefined,
      });
      break;

    case 'test':
      testSlack();
      break;

    case 'channels':
      listSlackChannels();
      break;

    case 'configure':
      if (args.includes('--route')) {
        const alertType = args[args.indexOf('--route') + 1];
        const channel = args[args.indexOf('--channel') + 1];
        configureSlackRouting({ alertType, channel });
      } else {
        showSlackConfig();
      }
      break;

    default:
      console.log('AI-Shell Slack Integration\n');
      console.log('Usage:');
      console.log('  notification-slack setup --token <token> --webhook <url> --channel <channel>');
      console.log('  notification-slack test');
      console.log('  notification-slack channels');
      console.log('  notification-slack configure --route <alert-type> --channel <channel>');
      console.log('  notification-slack configure (show current config)');
  }
}

export default SlackIntegration;
