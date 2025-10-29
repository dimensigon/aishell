import nodemailer, { Transporter, SendMailOptions } from 'nodemailer';
import { EventEmitter } from 'events';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as crypto from 'crypto';

/**
 * Email Notification System for AI-Shell
 * Provides comprehensive email delivery with templates, queuing, and retry logic
 */

// ============================================================================
// Types and Interfaces
// ============================================================================

export interface SMTPConfig {
  host: string;
  port: number;
  secure: boolean;
  auth: {
    user: string;
    pass: string;
  };
  pool?: boolean;
  maxConnections?: number;
  maxMessages?: number;
  rateDelta?: number;
  rateLimit?: number;
}

export interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  htmlBody: string;
  textBody: string;
  severity?: AlertSeverity;
  category: EmailCategory;
  variables: string[];
}

export type AlertSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';

export type EmailCategory =
  | 'query_failure'
  | 'security_violation'
  | 'backup_completion'
  | 'performance_degradation'
  | 'system_health'
  | 'custom';

export interface Recipient {
  email: string;
  name?: string;
  groups: string[];
  enabled: boolean;
  preferences?: {
    severity?: AlertSeverity[];
    categories?: EmailCategory[];
    quietHours?: { start: string; end: string };
  };
}

export interface EmailAttachment {
  filename: string;
  path?: string;
  content?: Buffer | string;
  contentType?: string;
  encoding?: string;
}

export interface EmailMessage {
  id: string;
  to: string[];
  cc?: string[];
  bcc?: string[];
  subject: string;
  html: string;
  text: string;
  attachments?: EmailAttachment[];
  templateId?: string;
  severity: AlertSeverity;
  category: EmailCategory;
  priority?: 'high' | 'normal' | 'low';
  metadata?: Record<string, any>;
  createdAt: Date;
  scheduledFor?: Date;
}

export interface EmailQueueItem {
  message: EmailMessage;
  attempts: number;
  lastAttempt?: Date;
  error?: string;
  status: 'pending' | 'sending' | 'sent' | 'failed' | 'cancelled';
}

export interface EmailStats {
  sent: number;
  failed: number;
  pending: number;
  queued: number;
  lastSent?: Date;
  lastError?: string;
}

export interface EmailNotificationConfig {
  smtp: SMTPConfig;
  fromAddress: string;
  fromName: string;
  replyTo?: string;
  templatesDir: string;
  queueDir: string;
  maxRetries: number;
  retryDelayMs: number;
  batchSize: number;
  rateLimitPerMinute: number;
  enableBatching: boolean;
  batchWindowMs: number;
}

// ============================================================================
// Default Email Templates
// ============================================================================

const DEFAULT_TEMPLATES: Record<EmailCategory, EmailTemplate> = {
  query_failure: {
    id: 'query_failure',
    name: 'Query Failure Alert',
    subject: '[{{severity}}] Query Failure: {{queryName}}',
    htmlBody: `
      <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <div style="background: #f44336; color: white; padding: 20px;">
            <h1 style="margin: 0;">Query Failure Alert</h1>
          </div>
          <div style="padding: 20px;">
            <h2>Query: {{queryName}}</h2>
            <p><strong>Severity:</strong> {{severity}}</p>
            <p><strong>Database:</strong> {{database}}</p>
            <p><strong>Time:</strong> {{timestamp}}</p>
            <h3>Error Details:</h3>
            <pre style="background: #f5f5f5; padding: 10px; overflow-x: auto;">{{error}}</pre>
            <h3>Query:</h3>
            <pre style="background: #f5f5f5; padding: 10px; overflow-x: auto;">{{query}}</pre>
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
              This is an automated alert from AI-Shell
            </p>
          </div>
        </body>
      </html>
    `,
    textBody: `
Query Failure Alert

Query: {{queryName}}
Severity: {{severity}}
Database: {{database}}
Time: {{timestamp}}

Error Details:
{{error}}

Query:
{{query}}

---
This is an automated alert from AI-Shell
    `,
    severity: 'high',
    category: 'query_failure',
    variables: ['severity', 'queryName', 'database', 'timestamp', 'error', 'query']
  },
  security_violation: {
    id: 'security_violation',
    name: 'Security Violation Alert',
    subject: '[SECURITY] {{violationType}} Detected',
    htmlBody: `
      <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <div style="background: #d32f2f; color: white; padding: 20px;">
            <h1 style="margin: 0;">🔒 Security Violation Detected</h1>
          </div>
          <div style="padding: 20px; background: #ffebee;">
            <h2>{{violationType}}</h2>
            <p><strong>Severity:</strong> <span style="color: #d32f2f;">CRITICAL</span></p>
            <p><strong>User:</strong> {{user}}</p>
            <p><strong>IP Address:</strong> {{ipAddress}}</p>
            <p><strong>Time:</strong> {{timestamp}}</p>
            <h3>Details:</h3>
            <p>{{details}}</p>
            <h3>Action Taken:</h3>
            <p>{{action}}</p>
            <div style="background: #fff; border-left: 4px solid #d32f2f; padding: 10px; margin: 20px 0;">
              <strong>⚠️ Immediate action may be required</strong>
            </div>
          </div>
        </body>
      </html>
    `,
    textBody: `
🔒 SECURITY VIOLATION DETECTED

Type: {{violationType}}
Severity: CRITICAL
User: {{user}}
IP Address: {{ipAddress}}
Time: {{timestamp}}

Details:
{{details}}

Action Taken:
{{action}}

⚠️ IMMEDIATE ACTION MAY BE REQUIRED

---
This is a security alert from AI-Shell
    `,
    severity: 'critical',
    category: 'security_violation',
    variables: ['violationType', 'user', 'ipAddress', 'timestamp', 'details', 'action']
  },
  backup_completion: {
    id: 'backup_completion',
    name: 'Backup Completion Notification',
    subject: 'Backup Completed: {{database}} - {{status}}',
    htmlBody: `
      <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <div style="background: {{statusColor}}; color: white; padding: 20px;">
            <h1 style="margin: 0;">Backup {{status}}</h1>
          </div>
          <div style="padding: 20px;">
            <h2>Database: {{database}}</h2>
            <p><strong>Status:</strong> {{status}}</p>
            <p><strong>Started:</strong> {{startTime}}</p>
            <p><strong>Completed:</strong> {{endTime}}</p>
            <p><strong>Duration:</strong> {{duration}}</p>
            <p><strong>Backup Size:</strong> {{backupSize}}</p>
            <p><strong>Location:</strong> {{location}}</p>
            {{#if compression}}
            <p><strong>Compression:</strong> {{compression}}</p>
            {{/if}}
            {{#if error}}
            <div style="background: #ffebee; border-left: 4px solid #f44336; padding: 10px; margin: 10px 0;">
              <strong>Error:</strong><br>{{error}}
            </div>
            {{/if}}
          </div>
        </body>
      </html>
    `,
    textBody: `
Backup {{status}}

Database: {{database}}
Status: {{status}}
Started: {{startTime}}
Completed: {{endTime}}
Duration: {{duration}}
Backup Size: {{backupSize}}
Location: {{location}}
{{#if compression}}
Compression: {{compression}}
{{/if}}
{{#if error}}

Error:
{{error}}
{{/if}}

---
This is an automated notification from AI-Shell
    `,
    severity: 'info',
    category: 'backup_completion',
    variables: ['database', 'status', 'startTime', 'endTime', 'duration', 'backupSize', 'location', 'compression', 'error', 'statusColor']
  },
  performance_degradation: {
    id: 'performance_degradation',
    name: 'Performance Degradation Alert',
    subject: '[PERFORMANCE] {{metricName}} Alert - {{database}}',
    htmlBody: `
      <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <div style="background: #ff9800; color: white; padding: 20px;">
            <h1 style="margin: 0;">⚠️ Performance Degradation</h1>
          </div>
          <div style="padding: 20px;">
            <h2>{{metricName}}</h2>
            <p><strong>Database:</strong> {{database}}</p>
            <p><strong>Severity:</strong> {{severity}}</p>
            <p><strong>Current Value:</strong> {{currentValue}}</p>
            <p><strong>Threshold:</strong> {{threshold}}</p>
            <p><strong>Time:</strong> {{timestamp}}</p>
            <h3>Impact:</h3>
            <p>{{impact}}</p>
            <h3>Recommended Actions:</h3>
            <ul>
              {{#each recommendations}}
              <li>{{this}}</li>
              {{/each}}
            </ul>
            <h3>Historical Data:</h3>
            <pre style="background: #f5f5f5; padding: 10px;">{{historicalData}}</pre>
          </div>
        </body>
      </html>
    `,
    textBody: `
⚠️ PERFORMANCE DEGRADATION

Metric: {{metricName}}
Database: {{database}}
Severity: {{severity}}
Current Value: {{currentValue}}
Threshold: {{threshold}}
Time: {{timestamp}}

Impact:
{{impact}}

Recommended Actions:
{{#each recommendations}}
- {{this}}
{{/each}}

Historical Data:
{{historicalData}}

---
This is a performance alert from AI-Shell
    `,
    severity: 'medium',
    category: 'performance_degradation',
    variables: ['metricName', 'database', 'severity', 'currentValue', 'threshold', 'timestamp', 'impact', 'recommendations', 'historicalData']
  },
  system_health: {
    id: 'system_health',
    name: 'System Health Report',
    subject: 'AI-Shell Health Report - {{date}}',
    htmlBody: `
      <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <div style="background: #4caf50; color: white; padding: 20px;">
            <h1 style="margin: 0;">System Health Report</h1>
          </div>
          <div style="padding: 20px;">
            <p><strong>Date:</strong> {{date}}</p>
            <p><strong>Overall Status:</strong> {{overallStatus}}</p>

            <h3>System Metrics</h3>
            <table style="width: 100%; border-collapse: collapse;">
              <tr style="background: #f5f5f5;">
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Uptime</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{{uptime}}</td>
              </tr>
              <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Queries Executed</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{{queriesExecuted}}</td>
              </tr>
              <tr style="background: #f5f5f5;">
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Success Rate</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{{successRate}}%</td>
              </tr>
              <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>Avg Response Time</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">{{avgResponseTime}}ms</td>
              </tr>
            </table>

            <h3>Active Connections</h3>
            <p>{{activeConnections}}</p>

            <h3>Recent Alerts</h3>
            <ul>
              {{#each recentAlerts}}
              <li>{{this}}</li>
              {{/each}}
            </ul>
          </div>
        </body>
      </html>
    `,
    textBody: `
SYSTEM HEALTH REPORT

Date: {{date}}
Overall Status: {{overallStatus}}

System Metrics:
- Uptime: {{uptime}}
- Queries Executed: {{queriesExecuted}}
- Success Rate: {{successRate}}%
- Avg Response Time: {{avgResponseTime}}ms

Active Connections: {{activeConnections}}

Recent Alerts:
{{#each recentAlerts}}
- {{this}}
{{/each}}

---
This is an automated report from AI-Shell
    `,
    severity: 'info',
    category: 'system_health',
    variables: ['date', 'overallStatus', 'uptime', 'queriesExecuted', 'successRate', 'avgResponseTime', 'activeConnections', 'recentAlerts']
  },
  custom: {
    id: 'custom',
    name: 'Custom Email Template',
    subject: '{{subject}}',
    htmlBody: '<html><body>{{body}}</body></html>',
    textBody: '{{body}}',
    severity: 'info',
    category: 'custom',
    variables: ['subject', 'body']
  }
};

// ============================================================================
// Email Notification Service
// ============================================================================

export class EmailNotificationService extends EventEmitter {
  private transporter: Transporter | null = null;
  private config: EmailNotificationConfig;
  private templates: Map<string, EmailTemplate> = new Map();
  private recipients: Map<string, Recipient> = new Map();
  private queue: Map<string, EmailQueueItem> = new Map();
  private batchQueue: EmailMessage[] = [];
  private stats: EmailStats = {
    sent: 0,
    failed: 0,
    pending: 0,
    queued: 0
  };
  private processing = false;
  private batchTimer: NodeJS.Timeout | null = null;
  private rateLimitTokens: number = 0;
  private lastRateLimitRefill: number = Date.now();

  constructor(config: Partial<EmailNotificationConfig> = {}) {
    super();
    this.config = this.mergeConfig(config);
    this.initializeTemplates();
    this.startQueueProcessor();
    this.startRateLimitRefill();
  }

  private mergeConfig(config: Partial<EmailNotificationConfig>): EmailNotificationConfig {
    return {
      smtp: config.smtp || {
        host: 'localhost',
        port: 587,
        secure: false,
        auth: { user: '', pass: '' },
        pool: true,
        maxConnections: 5,
        maxMessages: 100,
        rateDelta: 1000,
        rateLimit: 10
      },
      fromAddress: config.fromAddress || 'ai-shell@example.com',
      fromName: config.fromName || 'AI-Shell Notifications',
      replyTo: config.replyTo,
      templatesDir: config.templatesDir || path.join(process.cwd(), 'src/templates/email'),
      queueDir: config.queueDir || path.join(process.cwd(), '.aishell/email-queue'),
      maxRetries: config.maxRetries ?? 3,
      retryDelayMs: config.retryDelayMs ?? 5000,
      batchSize: config.batchSize ?? 10,
      rateLimitPerMinute: config.rateLimitPerMinute ?? 60,
      enableBatching: config.enableBatching ?? true,
      batchWindowMs: config.batchWindowMs ?? 30000
    };
  }

  private initializeTemplates(): void {
    // Load default templates
    Object.values(DEFAULT_TEMPLATES).forEach(template => {
      this.templates.set(template.id, template);
    });
  }

  /**
   * Initialize SMTP connection
   */
  async initialize(): Promise<void> {
    try {
      this.transporter = nodemailer.createTransport(this.config.smtp);

      // Verify connection
      await this.transporter.verify();

      this.emit('initialized', { timestamp: new Date() });
    } catch (error) {
      const errorMessage = `Failed to initialize email service: ${error instanceof Error ? error.message : 'Unknown error'}`;
      this.emit('error', { type: 'initialization', error });
      throw new Error(errorMessage);
    }
  }

  /**
   * Setup email configuration
   */
  async setupEmail(smtpConfig: Partial<SMTPConfig>): Promise<void> {
    this.config.smtp = { ...this.config.smtp, ...smtpConfig };
    await this.initialize();
  }

  /**
   * Send test email
   */
  async sendTestEmail(to: string): Promise<boolean> {
    const message: EmailMessage = {
      id: crypto.randomUUID(),
      to: [to],
      subject: 'AI-Shell Email Test',
      html: `
        <html>
          <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #2196f3; color: white; padding: 20px;">
              <h1>Email Configuration Test</h1>
            </div>
            <div style="padding: 20px;">
              <p>This is a test email from AI-Shell Email Notification System.</p>
              <p><strong>Configuration:</strong></p>
              <ul>
                <li>SMTP Host: ${this.config.smtp.host}</li>
                <li>SMTP Port: ${this.config.smtp.port}</li>
                <li>Secure: ${this.config.smtp.secure}</li>
                <li>From: ${this.config.fromAddress}</li>
              </ul>
              <p>If you received this email, your email configuration is working correctly!</p>
              <p style="color: #666; font-size: 12px; margin-top: 30px;">
                Sent at: ${new Date().toISOString()}
              </p>
            </div>
          </body>
        </html>
      `,
      text: `
Email Configuration Test

This is a test email from AI-Shell Email Notification System.

Configuration:
- SMTP Host: ${this.config.smtp.host}
- SMTP Port: ${this.config.smtp.port}
- Secure: ${this.config.smtp.secure}
- From: ${this.config.fromAddress}

If you received this email, your email configuration is working correctly!

Sent at: ${new Date().toISOString()}
      `,
      severity: 'info',
      category: 'custom',
      createdAt: new Date()
    };

    try {
      await this.sendEmail(message);
      return true;
    } catch (error) {
      this.emit('error', { type: 'test_email', error });
      return false;
    }
  }

  /**
   * Send email using template
   */
  async sendTemplateEmail(
    templateId: string,
    to: string | string[],
    variables: Record<string, any>,
    options?: {
      cc?: string[];
      bcc?: string[];
      attachments?: EmailAttachment[];
      priority?: 'high' | 'normal' | 'low';
    }
  ): Promise<string> {
    const template = this.templates.get(templateId);
    if (!template) {
      throw new Error(`Template not found: ${templateId}`);
    }

    // Render template
    const subject = this.renderTemplate(template.subject, variables);
    const html = this.renderTemplate(template.htmlBody, variables);
    const text = this.renderTemplate(template.textBody, variables);

    const message: EmailMessage = {
      id: crypto.randomUUID(),
      to: Array.isArray(to) ? to : [to],
      cc: options?.cc,
      bcc: options?.bcc,
      subject,
      html,
      text,
      attachments: options?.attachments,
      templateId,
      severity: template.severity || 'info',
      category: template.category,
      priority: options?.priority || 'normal',
      metadata: variables,
      createdAt: new Date()
    };

    return this.queueEmail(message);
  }

  /**
   * Simple template rendering (supports {{variable}}, nested {{obj.prop}}, and {{#if}})
   */
  private renderTemplate(template: string, variables: Record<string, any>): string {
    let rendered = template;

    // Handle conditionals {{#if variable}}...{{/if}}
    rendered = rendered.replace(/\{\{#if\s+(\w+)\}\}(.*?)\{\{\/if\}\}/gs, (match, key, content) => {
      return variables[key] ? content : '';
    });

    // Handle loops {{#each array}}...{{/each}}
    rendered = rendered.replace(/\{\{#each\s+(\w+)\}\}(.*?)\{\{\/each\}\}/gs, (match, key, content) => {
      const array = variables[key];
      if (!Array.isArray(array)) return '';
      return array.map(item => {
        if (typeof item === 'object') {
          return this.renderTemplate(content, item);
        }
        return content.replace(/{{this}}/g, String(item));
      }).join('');
    });

    // Replace nested variables (e.g., {{user.name}})
    rendered = rendered.replace(/\{\{([\w.]+)\}\}/g, (match, path) => {
      const parts = path.split('.');
      let value: any = variables;

      for (const part of parts) {
        if (value && typeof value === 'object' && part in value) {
          value = value[part];
        } else {
          // Variable not found, return empty string
          return '';
        }
      }

      return String(value ?? '');
    });

    return rendered;
  }

  /**
   * Queue email for sending
   */
  async queueEmail(message: EmailMessage): Promise<string> {
    const queueItem: EmailQueueItem = {
      message,
      attempts: 0,
      status: 'pending'
    };

    this.queue.set(message.id, queueItem);
    this.stats.queued++;

    // Add to batch queue if batching is enabled
    if (this.config.enableBatching) {
      this.batchQueue.push(message);
      this.scheduleBatchProcessing();
    }

    this.emit('queued', { messageId: message.id, message });

    // Save to disk
    await this.persistQueue();

    return message.id;
  }

  /**
   * Send email immediately
   */
  private async sendEmail(message: EmailMessage): Promise<void> {
    if (!this.transporter) {
      throw new Error('Email service not initialized');
    }

    // Check rate limit
    await this.waitForRateLimit();

    const mailOptions: SendMailOptions = {
      from: `${this.config.fromName} <${this.config.fromAddress}>`,
      to: message.to.join(', '),
      cc: message.cc?.join(', '),
      bcc: message.bcc?.join(', '),
      replyTo: this.config.replyTo,
      subject: message.subject,
      html: message.html,
      text: message.text,
      attachments: message.attachments,
      priority: message.priority || 'normal'
    };

    await this.transporter.sendMail(mailOptions);
    this.stats.sent++;
    this.stats.lastSent = new Date();
  }

  /**
   * Process email queue
   */
  private async processQueue(): Promise<void> {
    if (this.processing) return;
    this.processing = true;

    try {
      const pendingItems = Array.from(this.queue.values())
        .filter(item => item.status === 'pending')
        .slice(0, this.config.batchSize);

      for (const item of pendingItems) {
        try {
          item.status = 'sending';
          await this.sendEmail(item.message);
          item.status = 'sent';
          this.queue.delete(item.message.id);
          this.emit('sent', { messageId: item.message.id });
        } catch (error) {
          item.attempts++;
          item.lastAttempt = new Date();
          item.error = error instanceof Error ? error.message : 'Unknown error';

          if (item.attempts >= this.config.maxRetries) {
            item.status = 'failed';
            this.stats.failed++;
            this.stats.lastError = item.error;
            this.emit('failed', { messageId: item.message.id, error: item.error });
          } else {
            item.status = 'pending';
            // Exponential backoff
            const delay = this.config.retryDelayMs * Math.pow(2, item.attempts - 1);
            setTimeout(() => {
              this.emit('retry', { messageId: item.message.id, attempt: item.attempts });
            }, delay);
          }
        }
      }
    } finally {
      this.processing = false;
    }
  }

  /**
   * Start queue processor
   */
  private startQueueProcessor(): void {
    setInterval(() => {
      this.processQueue();
    }, 5000); // Process every 5 seconds
  }

  /**
   * Schedule batch processing
   */
  private scheduleBatchProcessing(): void {
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
    }

    this.batchTimer = setTimeout(() => {
      this.processBatch();
    }, this.config.batchWindowMs);

    // Process immediately if batch is full
    if (this.batchQueue.length >= this.config.batchSize) {
      this.processBatch();
    }
  }

  /**
   * Process batch of emails
   */
  private async processBatch(): Promise<void> {
    if (this.batchQueue.length === 0) return;

    const batch = this.batchQueue.splice(0, this.config.batchSize);

    for (const message of batch) {
      const queueItem = this.queue.get(message.id);
      if (queueItem) {
        queueItem.status = 'pending';
      }
    }

    this.emit('batch_processed', { count: batch.length });
    await this.processQueue();
  }

  /**
   * Rate limiting
   */
  private async waitForRateLimit(): Promise<void> {
    while (this.rateLimitTokens <= 0) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    this.rateLimitTokens--;
  }

  private startRateLimitRefill(): void {
    // Initialize with full token bucket
    this.rateLimitTokens = this.config.rateLimitPerMinute;

    setInterval(() => {
      const now = Date.now();
      const elapsed = now - this.lastRateLimitRefill;
      const tokensToAdd = Math.floor((elapsed / 60000) * this.config.rateLimitPerMinute);

      if (tokensToAdd > 0) {
        this.rateLimitTokens = Math.min(
          this.rateLimitTokens + tokensToAdd,
          this.config.rateLimitPerMinute
        );
        this.lastRateLimitRefill = now;
      }
    }, 1000);
  }

  /**
   * Recipient management
   */
  async addRecipient(recipient: Omit<Recipient, 'enabled'>): Promise<void> {
    this.recipients.set(recipient.email, { ...recipient, enabled: true });
    await this.persistRecipients();
  }

  async removeRecipient(email: string): Promise<void> {
    this.recipients.delete(email);
    await this.persistRecipients();
  }

  async getRecipientsByGroup(group: string): Promise<Recipient[]> {
    return Array.from(this.recipients.values())
      .filter(r => r.groups.includes(group) && r.enabled);
  }

  async listRecipients(filterGroup?: string): Promise<Recipient[]> {
    const recipients = Array.from(this.recipients.values());
    if (filterGroup) {
      return recipients.filter(r => r.groups.includes(filterGroup));
    }
    return recipients;
  }

  /**
   * Template management
   */
  async addTemplate(template: EmailTemplate): Promise<void> {
    this.templates.set(template.id, template);
    await this.persistTemplates();
  }

  async removeTemplate(templateId: string): Promise<void> {
    if (DEFAULT_TEMPLATES[templateId as EmailCategory]) {
      throw new Error('Cannot remove default template');
    }
    this.templates.delete(templateId);
    await this.persistTemplates();
  }

  listTemplates(): EmailTemplate[] {
    return Array.from(this.templates.values());
  }

  getTemplate(templateId: string): EmailTemplate | undefined {
    return this.templates.get(templateId);
  }

  /**
   * Statistics and monitoring
   */
  getStats(): EmailStats {
    return {
      ...this.stats,
      pending: Array.from(this.queue.values()).filter(i => i.status === 'pending').length,
      queued: this.queue.size
    };
  }

  async getQueueStatus(): Promise<EmailQueueItem[]> {
    return Array.from(this.queue.values());
  }

  /**
   * Persistence
   */
  private async persistQueue(): Promise<void> {
    try {
      await fs.mkdir(this.config.queueDir, { recursive: true });
      const queueFile = path.join(this.config.queueDir, 'queue.json');
      const data = JSON.stringify(Array.from(this.queue.entries()), null, 2);
      await fs.writeFile(queueFile, data, 'utf-8');
    } catch (error) {
      this.emit('error', { type: 'persist_queue', error });
    }
  }

  private async loadQueue(): Promise<void> {
    try {
      const queueFile = path.join(this.config.queueDir, 'queue.json');
      const data = await fs.readFile(queueFile, 'utf-8');
      const entries = JSON.parse(data);
      this.queue = new Map(entries);
    } catch (error) {
      // Queue file doesn't exist or is invalid, start fresh
      this.queue = new Map();
    }
  }

  private async persistRecipients(): Promise<void> {
    try {
      await fs.mkdir(this.config.queueDir, { recursive: true });
      const recipientsFile = path.join(this.config.queueDir, 'recipients.json');
      const data = JSON.stringify(Array.from(this.recipients.entries()), null, 2);
      await fs.writeFile(recipientsFile, data, 'utf-8');
    } catch (error) {
      this.emit('error', { type: 'persist_recipients', error });
    }
  }

  private async persistTemplates(): Promise<void> {
    try {
      await fs.mkdir(this.config.templatesDir, { recursive: true });
      const templatesFile = path.join(this.config.templatesDir, 'custom-templates.json');
      const customTemplates = Array.from(this.templates.entries())
        .filter(([id]) => !DEFAULT_TEMPLATES[id as EmailCategory]);
      const data = JSON.stringify(customTemplates, null, 2);
      await fs.writeFile(templatesFile, data, 'utf-8');
    } catch (error) {
      this.emit('error', { type: 'persist_templates', error });
    }
  }

  /**
   * Cleanup
   */
  async shutdown(): Promise<void> {
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
    }

    // Process remaining batch
    await this.processBatch();

    // Wait for queue to empty or timeout after 2 seconds
    const shutdownTimeout = Date.now() + 2000;
    while (this.queue.size > 0 && this.processing && Date.now() < shutdownTimeout) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    // Close transporter
    if (this.transporter && typeof this.transporter.close === 'function') {
      this.transporter.close();
    }

    this.emit('shutdown', { timestamp: new Date() });
  }
}

// ============================================================================
// Export singleton instance
// ============================================================================

let emailService: EmailNotificationService | null = null;

export function getEmailService(config?: Partial<EmailNotificationConfig>): EmailNotificationService {
  if (!emailService) {
    emailService = new EmailNotificationService(config);
  }
  return emailService;
}

export function resetEmailService(): void {
  if (emailService) {
    emailService.shutdown();
    emailService = null;
  }
}
