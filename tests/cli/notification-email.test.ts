import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  EmailNotificationService,
  getEmailService,
  resetEmailService,
  SMTPConfig,
  EmailMessage,
  EmailTemplate,
  Recipient,
  AlertSeverity,
  EmailCategory
} from '../../src/cli/notification-email';
import nodemailer from 'nodemailer';

// Mock nodemailer
vi.mock('nodemailer', () => ({
  default: {
    createTransport: vi.fn(() => ({
      verify: vi.fn().mockResolvedValue(true),
      sendMail: vi.fn().mockResolvedValue({ messageId: 'test-message-id' }),
      close: vi.fn()
    }))
  }
}));

describe('EmailNotificationService', () => {
  let emailService: EmailNotificationService;
  const testConfig: Partial<SMTPConfig> = {
    host: 'smtp.test.com',
    port: 587,
    secure: false,
    auth: {
      user: 'test@test.com',
      pass: 'testpass'
    }
  };

  beforeEach(() => {
    resetEmailService();
    emailService = new EmailNotificationService({
      smtp: testConfig as SMTPConfig,
      fromAddress: 'test@aishell.com',
      fromName: 'Test AI-Shell',
      enableBatching: false
    });
  });

  afterEach(async () => {
    await emailService.shutdown();
    resetEmailService();
  });

  describe('Initialization', () => {
    it('should create email service instance', () => {
      expect(emailService).toBeDefined();
      expect(emailService).toBeInstanceOf(EmailNotificationService);
    });

    it('should initialize SMTP connection', async () => {
      await emailService.initialize();
      expect(nodemailer.createTransport).toHaveBeenCalled();
    });

    it('should emit initialized event', async () => {
      const initSpy = vi.fn();
      emailService.on('initialized', initSpy);
      await emailService.initialize();
      expect(initSpy).toHaveBeenCalled();
    });

    it('should handle initialization errors', async () => {
      const mockTransport = {
        verify: vi.fn().mockRejectedValue(new Error('Connection failed'))
      };
      vi.mocked(nodemailer.createTransport).mockReturnValue(mockTransport as any);

      await expect(emailService.initialize()).rejects.toThrow('Failed to initialize email service');
    });

    it('should merge configuration correctly', () => {
      const service = new EmailNotificationService({
        fromAddress: 'custom@test.com'
      });
      expect(service['config'].fromAddress).toBe('custom@test.com');
    });
  });

  describe('Template Management', () => {
    it('should load default templates', () => {
      const templates = emailService.listTemplates();
      expect(templates.length).toBeGreaterThan(0);
      expect(templates.some(t => t.id === 'query_failure')).toBe(true);
      expect(templates.some(t => t.id === 'security_violation')).toBe(true);
      expect(templates.some(t => t.id === 'backup_completion')).toBe(true);
    });

    it('should add custom template', async () => {
      const customTemplate: EmailTemplate = {
        id: 'custom_test',
        name: 'Custom Test',
        subject: 'Test: {{title}}',
        htmlBody: '<html><body>{{content}}</body></html>',
        textBody: '{{content}}',
        category: 'custom',
        variables: ['title', 'content']
      };

      await emailService.addTemplate(customTemplate);
      const template = emailService.getTemplate('custom_test');
      expect(template).toEqual(customTemplate);
    });

    it('should remove custom template', async () => {
      const customTemplate: EmailTemplate = {
        id: 'custom_remove',
        name: 'Custom Remove',
        subject: 'Test',
        htmlBody: 'Test',
        textBody: 'Test',
        category: 'custom',
        variables: []
      };

      await emailService.addTemplate(customTemplate);
      await emailService.removeTemplate('custom_remove');
      expect(emailService.getTemplate('custom_remove')).toBeUndefined();
    });

    it('should not allow removing default templates', async () => {
      await expect(emailService.removeTemplate('query_failure')).rejects.toThrow('Cannot remove default template');
    });

    it('should list all templates', () => {
      const templates = emailService.listTemplates();
      expect(Array.isArray(templates)).toBe(true);
      expect(templates.length).toBeGreaterThan(0);
    });
  });

  describe('Template Rendering', () => {
    it('should render simple variables', () => {
      const template = '{{name}} - {{age}}';
      const rendered = emailService['renderTemplate'](template, { name: 'John', age: 30 });
      expect(rendered).toBe('John - 30');
    });

    it('should render conditional blocks', () => {
      const template = '{{#if show}}Visible{{/if}}';
      const renderedTrue = emailService['renderTemplate'](template, { show: true });
      const renderedFalse = emailService['renderTemplate'](template, { show: false });
      expect(renderedTrue).toBe('Visible');
      expect(renderedFalse).toBe('');
    });

    it('should render loops', () => {
      const template = '{{#each items}}{{this}}, {{/each}}';
      const rendered = emailService['renderTemplate'](template, { items: ['a', 'b', 'c'] });
      expect(rendered).toBe('a, b, c, ');
    });

    it('should handle missing variables gracefully', () => {
      const template = '{{existing}} - {{missing}}';
      const rendered = emailService['renderTemplate'](template, { existing: 'value' });
      expect(rendered).toBe('value - ');
    });

    it('should render complex nested templates', () => {
      const template = '{{#if user}}Hello {{user.name}}!{{/if}}';
      const rendered = emailService['renderTemplate'](template, {
        user: { name: 'Alice' }
      });
      expect(rendered).toContain('Alice');
    });
  });

  describe('Email Sending', () => {
    beforeEach(async () => {
      await emailService.initialize();
    });

    it('should send test email', async () => {
      const result = await emailService.sendTestEmail('test@example.com');
      expect(result).toBe(true);
    });

    it('should send email using template', async () => {
      const messageId = await emailService.sendTemplateEmail(
        'query_failure',
        'user@example.com',
        {
          severity: 'high',
          queryName: 'test_query',
          database: 'testdb',
          timestamp: new Date().toISOString(),
          error: 'Test error',
          query: 'SELECT * FROM test'
        }
      );

      expect(messageId).toBeDefined();
      expect(typeof messageId).toBe('string');
    });

    it('should throw error for non-existent template', async () => {
      await expect(
        emailService.sendTemplateEmail('non_existent', 'test@test.com', {})
      ).rejects.toThrow('Template not found');
    });

    it('should support multiple recipients', async () => {
      const messageId = await emailService.sendTemplateEmail(
        'system_health',
        ['user1@test.com', 'user2@test.com'],
        {
          date: new Date().toISOString(),
          overallStatus: 'Healthy',
          uptime: '24h',
          queriesExecuted: 1000,
          successRate: 99.5,
          avgResponseTime: 50,
          activeConnections: 10,
          recentAlerts: []
        }
      );

      expect(messageId).toBeDefined();
    });

    it('should support CC and BCC', async () => {
      const messageId = await emailService.sendTemplateEmail(
        'backup_completion',
        'primary@test.com',
        {
          database: 'testdb',
          status: 'Success',
          startTime: '10:00',
          endTime: '10:30',
          duration: '30min',
          backupSize: '100MB',
          location: '/backups/test.sql',
          statusColor: '#4caf50'
        },
        {
          cc: ['manager@test.com'],
          bcc: ['audit@test.com']
        }
      );

      expect(messageId).toBeDefined();
    });

    it('should handle email attachments', async () => {
      const messageId = await emailService.sendTemplateEmail(
        'custom',
        'user@test.com',
        {
          subject: 'Test with attachment',
          body: 'See attached file'
        },
        {
          attachments: [
            {
              filename: 'report.txt',
              content: 'Test report content'
            }
          ]
        }
      );

      expect(messageId).toBeDefined();
    });

    it('should set email priority', async () => {
      const messageId = await emailService.sendTemplateEmail(
        'security_violation',
        'security@test.com',
        {
          violationType: 'Unauthorized Access',
          user: 'testuser',
          ipAddress: '192.168.1.1',
          timestamp: new Date().toISOString(),
          details: 'Multiple failed login attempts',
          action: 'Account locked'
        },
        {
          priority: 'high'
        }
      );

      expect(messageId).toBeDefined();
    });
  });

  describe('Email Queue', () => {
    it('should queue email for later sending', async () => {
      const message: EmailMessage = {
        id: 'test-id',
        to: ['test@test.com'],
        subject: 'Test',
        html: '<p>Test</p>',
        text: 'Test',
        severity: 'info',
        category: 'custom',
        createdAt: new Date()
      };

      const messageId = await emailService.queueEmail(message);
      expect(messageId).toBe('test-id');

      const stats = emailService.getStats();
      expect(stats.queued).toBeGreaterThan(0);
    });

    it('should process queue', async () => {
      await emailService.initialize();

      const queuedSpy = vi.fn();
      const sentSpy = vi.fn();

      emailService.on('queued', queuedSpy);
      emailService.on('sent', sentSpy);

      await emailService.sendTemplateEmail('custom', 'test@test.com', {
        subject: 'Test',
        body: 'Test body'
      });

      expect(queuedSpy).toHaveBeenCalled();

      // Wait for queue processing
      await new Promise(resolve => setTimeout(resolve, 6000));

      expect(sentSpy).toHaveBeenCalled();
    });

    it('should get queue status', async () => {
      await emailService.queueEmail({
        id: 'queue-test',
        to: ['test@test.com'],
        subject: 'Test',
        html: 'Test',
        text: 'Test',
        severity: 'info',
        category: 'custom',
        createdAt: new Date()
      });

      const status = await emailService.getQueueStatus();
      expect(Array.isArray(status)).toBe(true);
      expect(status.length).toBeGreaterThan(0);
    });

    it('should handle failed emails with retry', async () => {
      const mockTransport = {
        verify: vi.fn().mockResolvedValue(true),
        sendMail: vi.fn()
          .mockRejectedValueOnce(new Error('Temporary failure'))
          .mockResolvedValueOnce({ messageId: 'success' }),
        close: vi.fn()
      };
      vi.mocked(nodemailer.createTransport).mockReturnValue(mockTransport as any);

      await emailService.initialize();

      const retrySpy = vi.fn();
      emailService.on('retry', retrySpy);

      await emailService.sendTemplateEmail('custom', 'test@test.com', {
        subject: 'Test',
        body: 'Test'
      });

      // Wait for retry
      await new Promise(resolve => setTimeout(resolve, 10000));

      expect(retrySpy).toHaveBeenCalled();
    });

    it('should mark email as failed after max retries', async () => {
      const mockTransport = {
        verify: vi.fn().mockResolvedValue(true),
        sendMail: vi.fn().mockRejectedValue(new Error('Permanent failure')),
        close: vi.fn()
      };
      vi.mocked(nodemailer.createTransport).mockReturnValue(mockTransport as any);

      const service = new EmailNotificationService({
        smtp: testConfig as SMTPConfig,
        maxRetries: 2,
        retryDelayMs: 100
      });

      await service.initialize();

      const failedSpy = vi.fn();
      service.on('failed', failedSpy);

      await service.sendTemplateEmail('custom', 'test@test.com', {
        subject: 'Test',
        body: 'Test'
      });

      // Wait for all retries
      await new Promise(resolve => setTimeout(resolve, 1000));

      expect(failedSpy).toHaveBeenCalled();

      await service.shutdown();
    });
  });

  describe('Batching', () => {
    it('should batch emails when enabled', async () => {
      const service = new EmailNotificationService({
        smtp: testConfig as SMTPConfig,
        enableBatching: true,
        batchSize: 3,
        batchWindowMs: 1000
      });

      await service.initialize();

      const batchSpy = vi.fn();
      service.on('batch_processed', batchSpy);

      // Queue multiple emails
      await service.sendTemplateEmail('custom', 'user1@test.com', { subject: 'Test 1', body: 'Test' });
      await service.sendTemplateEmail('custom', 'user2@test.com', { subject: 'Test 2', body: 'Test' });
      await service.sendTemplateEmail('custom', 'user3@test.com', { subject: 'Test 3', body: 'Test' });

      // Wait for batch processing
      await new Promise(resolve => setTimeout(resolve, 2000));

      expect(batchSpy).toHaveBeenCalled();

      await service.shutdown();
    });

    it('should process batch immediately when full', async () => {
      const service = new EmailNotificationService({
        smtp: testConfig as SMTPConfig,
        enableBatching: true,
        batchSize: 2
      });

      await service.initialize();

      const batchSpy = vi.fn();
      service.on('batch_processed', batchSpy);

      await service.sendTemplateEmail('custom', 'user1@test.com', { subject: 'Test 1', body: 'Test' });
      await service.sendTemplateEmail('custom', 'user2@test.com', { subject: 'Test 2', body: 'Test' });

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(batchSpy).toHaveBeenCalled();

      await service.shutdown();
    });
  });

  describe('Rate Limiting', () => {
    it('should respect rate limits', async () => {
      const service = new EmailNotificationService({
        smtp: testConfig as SMTPConfig,
        rateLimitPerMinute: 2
      });

      await service.initialize();

      const start = Date.now();

      // Send 3 emails (should throttle the 3rd)
      await service.sendTemplateEmail('custom', 'test1@test.com', { subject: 'Test', body: 'Test' });
      await service.sendTemplateEmail('custom', 'test2@test.com', { subject: 'Test', body: 'Test' });
      await service.sendTemplateEmail('custom', 'test3@test.com', { subject: 'Test', body: 'Test' });

      const elapsed = Date.now() - start;

      // Third email should be delayed
      expect(elapsed).toBeGreaterThan(100);

      await service.shutdown();
    }, 10000);
  });

  describe('Recipient Management', () => {
    it('should add recipient', async () => {
      const recipient: Omit<Recipient, 'enabled'> = {
        email: 'user@test.com',
        name: 'Test User',
        groups: ['developers']
      };

      await emailService.addRecipient(recipient);
      const recipients = await emailService.listRecipients();

      expect(recipients.some(r => r.email === 'user@test.com')).toBe(true);
    });

    it('should remove recipient', async () => {
      await emailService.addRecipient({
        email: 'remove@test.com',
        groups: ['test']
      });

      await emailService.removeRecipient('remove@test.com');
      const recipients = await emailService.listRecipients();

      expect(recipients.some(r => r.email === 'remove@test.com')).toBe(false);
    });

    it('should get recipients by group', async () => {
      await emailService.addRecipient({
        email: 'dev1@test.com',
        groups: ['developers', 'admins']
      });
      await emailService.addRecipient({
        email: 'dev2@test.com',
        groups: ['developers']
      });
      await emailService.addRecipient({
        email: 'manager@test.com',
        groups: ['managers']
      });

      const devs = await emailService.getRecipientsByGroup('developers');
      expect(devs.length).toBe(2);
    });

    it('should filter recipients by preferences', async () => {
      await emailService.addRecipient({
        email: 'critical@test.com',
        groups: ['alerts'],
        preferences: {
          severity: ['critical', 'high']
        }
      });

      const recipients = await emailService.listRecipients();
      const criticalRecipient = recipients.find(r => r.email === 'critical@test.com');

      expect(criticalRecipient?.preferences?.severity).toContain('critical');
    });

    it('should list all recipients', async () => {
      await emailService.addRecipient({ email: 'user1@test.com', groups: ['group1'] });
      await emailService.addRecipient({ email: 'user2@test.com', groups: ['group2'] });

      const recipients = await emailService.listRecipients();
      expect(recipients.length).toBeGreaterThanOrEqual(2);
    });

    it('should filter recipients by group', async () => {
      await emailService.addRecipient({ email: 'dev@test.com', groups: ['developers'] });
      await emailService.addRecipient({ email: 'ops@test.com', groups: ['operations'] });

      const devRecipients = await emailService.listRecipients('developers');
      expect(devRecipients.every(r => r.groups.includes('developers'))).toBe(true);
    });
  });

  describe('Statistics', () => {
    it('should track statistics', async () => {
      await emailService.initialize();

      const initialStats = emailService.getStats();
      expect(initialStats.sent).toBe(0);

      await emailService.sendTemplateEmail('custom', 'test@test.com', {
        subject: 'Test',
        body: 'Test'
      });

      // Wait for processing
      await new Promise(resolve => setTimeout(resolve, 6000));

      const stats = emailService.getStats();
      expect(stats.queued).toBeGreaterThan(0);
    });

    it('should track last sent time', async () => {
      await emailService.initialize();

      await emailService.sendTemplateEmail('custom', 'test@test.com', {
        subject: 'Test',
        body: 'Test'
      });

      await new Promise(resolve => setTimeout(resolve, 6000));

      const stats = emailService.getStats();
      expect(stats.lastSent).toBeDefined();
    });

    it('should track failed emails', async () => {
      const mockTransport = {
        verify: vi.fn().mockResolvedValue(true),
        sendMail: vi.fn().mockRejectedValue(new Error('Failed')),
        close: vi.fn()
      };
      vi.mocked(nodemailer.createTransport).mockReturnValue(mockTransport as any);

      const service = new EmailNotificationService({
        smtp: testConfig as SMTPConfig,
        maxRetries: 1
      });

      await service.initialize();

      await service.sendTemplateEmail('custom', 'test@test.com', {
        subject: 'Test',
        body: 'Test'
      });

      await new Promise(resolve => setTimeout(resolve, 7000));

      const stats = service.getStats();
      expect(stats.lastError).toBeDefined();

      await service.shutdown();
    });
  });

  describe('Predefined Templates', () => {
    it('should render query failure template', async () => {
      await emailService.initialize();

      const messageId = await emailService.sendTemplateEmail(
        'query_failure',
        'dba@test.com',
        {
          severity: 'high',
          queryName: 'monthly_report',
          database: 'production',
          timestamp: new Date().toISOString(),
          error: 'Connection timeout',
          query: 'SELECT * FROM large_table'
        }
      );

      expect(messageId).toBeDefined();
    });

    it('should render security violation template', async () => {
      await emailService.initialize();

      const messageId = await emailService.sendTemplateEmail(
        'security_violation',
        'security@test.com',
        {
          violationType: 'SQL Injection Attempt',
          user: 'anonymous',
          ipAddress: '192.168.1.100',
          timestamp: new Date().toISOString(),
          details: 'Malicious SQL detected in query',
          action: 'Request blocked and logged'
        }
      );

      expect(messageId).toBeDefined();
    });

    it('should render backup completion template', async () => {
      await emailService.initialize();

      const messageId = await emailService.sendTemplateEmail(
        'backup_completion',
        'admin@test.com',
        {
          database: 'production',
          status: 'Success',
          startTime: '02:00:00',
          endTime: '02:45:30',
          duration: '45m 30s',
          backupSize: '2.3 GB',
          location: '/backups/prod-2024-01-15.sql.gz',
          compression: 'gzip',
          statusColor: '#4caf50'
        }
      );

      expect(messageId).toBeDefined();
    });

    it('should render performance degradation template', async () => {
      await emailService.initialize();

      const messageId = await emailService.sendTemplateEmail(
        'performance_degradation',
        'ops@test.com',
        {
          metricName: 'Query Response Time',
          database: 'production',
          severity: 'medium',
          currentValue: '2500ms',
          threshold: '1000ms',
          timestamp: new Date().toISOString(),
          impact: 'Slow query performance affecting user experience',
          recommendations: [
            'Add index on frequently queried columns',
            'Review and optimize slow queries',
            'Consider query caching'
          ],
          historicalData: 'Avg: 850ms, P95: 1200ms, P99: 2100ms'
        }
      );

      expect(messageId).toBeDefined();
    });

    it('should render system health template', async () => {
      await emailService.initialize();

      const messageId = await emailService.sendTemplateEmail(
        'system_health',
        'team@test.com',
        {
          date: new Date().toLocaleDateString(),
          overallStatus: 'Healthy',
          uptime: '99.98%',
          queriesExecuted: '1,234,567',
          successRate: '99.95',
          avgResponseTime: '145',
          activeConnections: '42',
          recentAlerts: [
            'Disk usage at 75% on server-1',
            'Slow query detected at 14:32'
          ]
        }
      );

      expect(messageId).toBeDefined();
    });
  });

  describe('Singleton Instance', () => {
    it('should return same instance', () => {
      const instance1 = getEmailService();
      const instance2 = getEmailService();
      expect(instance1).toBe(instance2);
    });

    it('should reset singleton instance', () => {
      const instance1 = getEmailService();
      resetEmailService();
      const instance2 = getEmailService();
      expect(instance1).not.toBe(instance2);
    });

    it('should initialize with custom config', () => {
      const instance = getEmailService({
        fromAddress: 'custom@test.com'
      });
      expect(instance['config'].fromAddress).toBe('custom@test.com');
    });
  });

  describe('Shutdown', () => {
    it('should shutdown gracefully', async () => {
      await emailService.initialize();

      const shutdownSpy = vi.fn();
      emailService.on('shutdown', shutdownSpy);

      await emailService.shutdown();

      expect(shutdownSpy).toHaveBeenCalled();
    });

    it('should process remaining emails before shutdown', async () => {
      await emailService.initialize();

      await emailService.sendTemplateEmail('custom', 'test@test.com', {
        subject: 'Test',
        body: 'Test'
      });

      await emailService.shutdown();

      const stats = emailService.getStats();
      // Queue should be empty or emails should be marked as failed
      expect(stats.pending).toBe(0);
    });
  });

  describe('Error Handling', () => {
    it('should emit error events', async () => {
      const errorSpy = vi.fn();
      emailService.on('error', errorSpy);

      const mockTransport = {
        verify: vi.fn().mockRejectedValue(new Error('SMTP error'))
      };
      vi.mocked(nodemailer.createTransport).mockReturnValue(mockTransport as any);

      await expect(emailService.initialize()).rejects.toThrow();
      expect(errorSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'initialization'
        })
      );
    });

    it('should handle missing transporter gracefully', async () => {
      const message: EmailMessage = {
        id: 'test',
        to: ['test@test.com'],
        subject: 'Test',
        html: 'Test',
        text: 'Test',
        severity: 'info',
        category: 'custom',
        createdAt: new Date()
      };

      // Don't initialize, try to send
      await expect(emailService['sendEmail'](message)).rejects.toThrow('Email service not initialized');
    });
  });
});
