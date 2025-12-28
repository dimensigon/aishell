/**
 * Integration CLI Tests - Sprint 5
 *
 * Comprehensive test suite for 20 integration commands
 * 4 tests per command = 80+ total tests
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
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
} from '../../src/cli/integration-cli.js';
import { SlackClient } from '../../src/integrations/slack-client.js';
import { EmailClient } from '../../src/integrations/email-client.js';
import { FederationEngine } from '../../src/federation/federation-engine.js';
import { SchemaManager } from '../../src/schema/schema-manager.js';
import { ADAAgent } from '../../src/agents/ada-agent.js';
import * as fs from 'fs/promises';

// Mock dependencies
vi.mock('../../src/integrations/slack-client.js');
vi.mock('../../src/integrations/email-client.js');
vi.mock('../../src/federation/federation-engine.js');
vi.mock('../../src/schema/schema-manager.js');
vi.mock('../../src/agents/ada-agent.js');
vi.mock('fs/promises');
vi.mock('ora', () => ({
  default: vi.fn(() => ({
    start: vi.fn().mockReturnThis(),
    succeed: vi.fn().mockReturnThis(),
    fail: vi.fn().mockReturnThis(),
    stop: vi.fn().mockReturnThis(),
    text: ''
  }))
}));
vi.mock('inquirer', () => ({
  default: {
    prompt: vi.fn()
  }
}));

describe('Integration CLI - Sprint 5', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ==========================================================================
  // SLACK INTEGRATION COMMANDS (16 tests)
  // ==========================================================================

  describe('Slack Integration Commands', () => {
    describe('slack setup', () => {
      it('should setup Slack integration with non-interactive mode', async () => {
        const mockClient = {
          initialize: vi.fn(),
          setup: vi.fn(),
          testConnection: vi.fn().mockResolvedValue({
            success: true,
            workspace: 'test-workspace',
            botName: 'ai-shell-bot',
            channels: ['general', 'alerts']
          }),
          saveConfig: vi.fn()
        };
        vi.mocked(SlackClient).mockImplementation(() => mockClient as any);

        await slackSetup({
          token: 'xoxb-test-token',
          workspace: 'W123',
          interactive: false
        });

        expect(mockClient.setup).toHaveBeenCalledWith({
          token: 'xoxb-test-token',
          workspace: 'W123',
          enableAlerts: true
        });
        expect(mockClient.testConnection).toHaveBeenCalled();
        expect(mockClient.saveConfig).toHaveBeenCalled();
      });

      it('should handle setup with interactive mode', async () => {
        const inquirer = await import('inquirer');
        vi.mocked(inquirer.default.prompt).mockResolvedValue({
          token: 'xoxb-interactive',
          workspace: 'W456',
          defaultChannel: '#general',
          enableAlerts: true
        });

        const mockClient = {
          initialize: vi.fn(),
          setup: vi.fn(),
          testConnection: vi.fn().mockResolvedValue({
            success: true,
            workspace: 'test-workspace',
            botName: 'ai-shell-bot',
            channels: []
          }),
          saveConfig: vi.fn()
        };
        vi.mocked(SlackClient).mockImplementation(() => mockClient as any);

        await slackSetup({ interactive: true });

        expect(inquirer.default.prompt).toHaveBeenCalled();
        expect(mockClient.setup).toHaveBeenCalled();
      });

      it('should handle connection test failure', async () => {
        const mockClient = {
          initialize: vi.fn(),
          setup: vi.fn(),
          testConnection: vi.fn().mockResolvedValue({
            success: false,
            error: 'Invalid token'
          }),
          saveConfig: vi.fn()
        };
        vi.mocked(SlackClient).mockImplementation(() => mockClient as any);

        await expect(slackSetup({
          token: 'invalid-token',
          workspace: 'W123'
        })).rejects.toThrow();
      });

      it('should validate required parameters in non-interactive mode', async () => {
        await expect(slackSetup({
          interactive: false
        })).rejects.toThrow();
      });
    });

    describe('slack notify', () => {
      it('should send notification to channel', async () => {
        const mockClient = {
          initialize: vi.fn(),
          sendMessage: vi.fn().mockResolvedValue({
            success: true,
            messageId: 'msg-123',
            timestamp: '1234567890.123456',
            permalink: 'https://slack.com/archives/C123/p1234567890123456'
          })
        };
        vi.mocked(SlackClient).mockImplementation(() => mockClient as any);

        await slackNotify('#alerts', 'Test notification', {
          priority: 'high'
        });

        expect(mockClient.sendMessage).toHaveBeenCalledWith({
          channel: '#alerts',
          message: 'Test notification',
          priority: 'high',
          attachments: null,
          threadTs: undefined,
          mentions: []
        });
      });

      it('should handle attachments from JSON string', async () => {
        const mockClient = {
          initialize: vi.fn(),
          sendMessage: vi.fn().mockResolvedValue({
            success: true,
            messageId: 'msg-456',
            timestamp: '1234567890.123456'
          })
        };
        vi.mocked(SlackClient).mockImplementation(() => mockClient as any);

        const attachments = JSON.stringify([{ text: 'Attachment' }]);
        await slackNotify('#general', 'Message with attachment', {
          attachments
        });

        expect(mockClient.sendMessage).toHaveBeenCalledWith(
          expect.objectContaining({
            attachments: [{ text: 'Attachment' }]
          })
        );
      });

      it('should handle mentions', async () => {
        const mockClient = {
          initialize: vi.fn(),
          sendMessage: vi.fn().mockResolvedValue({
            success: true,
            messageId: 'msg-789',
            timestamp: '1234567890.123456'
          })
        };
        vi.mocked(SlackClient).mockImplementation(() => mockClient as any);

        await slackNotify('#team', 'Important update', {
          mentions: 'U123,U456'
        });

        expect(mockClient.sendMessage).toHaveBeenCalledWith(
          expect.objectContaining({
            mentions: ['U123', 'U456']
          })
        );
      });

      it('should handle send failure', async () => {
        const mockClient = {
          initialize: vi.fn(),
          sendMessage: vi.fn().mockResolvedValue({
            success: false,
            error: 'Channel not found'
          })
        };
        vi.mocked(SlackClient).mockImplementation(() => mockClient as any);

        await expect(slackNotify('#nonexistent', 'Test')).rejects.toThrow();
      });
    });

    describe('slack alert', () => {
      it('should send alert with severity', async () => {
        const mockClient = {
          initialize: vi.fn(),
          sendAlert: vi.fn().mockResolvedValue({
            success: true,
            alertId: 'alert-123',
            channel: '#alerts',
            notifiedUsers: ['U123', 'U456'],
            incidentCreated: false
          })
        };
        vi.mocked(SlackClient).mockImplementation(() => mockClient as any);

        await slackAlert('critical', 'Database connection lost', {
          channel: '#ops'
        });

        expect(mockClient.sendAlert).toHaveBeenCalledWith({
          severity: 'critical',
          message: 'Database connection lost',
          channel: '#ops',
          incidentId: undefined,
          context: null,
          timestamp: expect.any(String)
        });
      });

      it('should handle context data', async () => {
        const mockClient = {
          initialize: vi.fn(),
          sendAlert: vi.fn().mockResolvedValue({
            success: true,
            alertId: 'alert-456',
            channel: '#alerts',
            notifiedUsers: []
          })
        };
        vi.mocked(SlackClient).mockImplementation(() => mockClient as any);

        const context = JSON.stringify({ cpu: '95%', memory: '89%' });
        await slackAlert('warning', 'High resource usage', { context });

        expect(mockClient.sendAlert).toHaveBeenCalledWith(
          expect.objectContaining({
            context: { cpu: '95%', memory: '89%' }
          })
        );
      });

      it('should create incident when specified', async () => {
        const mockClient = {
          initialize: vi.fn(),
          sendAlert: vi.fn().mockResolvedValue({
            success: true,
            alertId: 'alert-789',
            channel: '#incidents',
            notifiedUsers: ['U123'],
            incidentCreated: true,
            incidentId: 'INC-001'
          })
        };
        vi.mocked(SlackClient).mockImplementation(() => mockClient as any);

        await slackAlert('critical', 'Service outage', {
          incident: 'INC-001'
        });

        expect(mockClient.sendAlert).toHaveBeenCalledWith(
          expect.objectContaining({
            incidentId: 'INC-001'
          })
        );
      });

      it('should handle alert send failure', async () => {
        const mockClient = {
          initialize: vi.fn(),
          sendAlert: vi.fn().mockResolvedValue({
            success: false,
            error: 'Permission denied'
          })
        };
        vi.mocked(SlackClient).mockImplementation(() => mockClient as any);

        await expect(slackAlert('info', 'Test alert')).rejects.toThrow();
      });
    });

    describe('slack report', () => {
      it('should generate and send daily report', async () => {
        const mockClient = {
          initialize: vi.fn(),
          generateReport: vi.fn().mockResolvedValue({
            metrics: ['cpu', 'memory'],
            period: 'last 24 hours',
            summary: [
              { metric: 'CPU', value: '45%', change: 5 },
              { metric: 'Memory', value: '67%', change: -3 }
            ]
          }),
          sendReport: vi.fn().mockResolvedValue({
            success: true,
            reportId: 'report-123',
            channel: '#reports'
          })
        };
        vi.mocked(SlackClient).mockImplementation(() => mockClient as any);

        await slackReport('daily', { channel: '#reports' });

        expect(mockClient.generateReport).toHaveBeenCalledWith({
          type: 'daily',
          format: 'summary',
          period: undefined,
          metrics: undefined
        });
        expect(mockClient.sendReport).toHaveBeenCalled();
      });

      it('should filter metrics', async () => {
        const mockClient = {
          initialize: vi.fn(),
          generateReport: vi.fn().mockResolvedValue({
            metrics: ['cpu', 'memory'],
            period: 'weekly',
            summary: []
          }),
          sendReport: vi.fn().mockResolvedValue({
            success: true,
            reportId: 'report-456',
            channel: '#metrics'
          })
        };
        vi.mocked(SlackClient).mockImplementation(() => mockClient as any);

        await slackReport('weekly', {
          metrics: 'cpu,memory,disk',
          format: 'detailed'
        });

        expect(mockClient.generateReport).toHaveBeenCalledWith({
          type: 'weekly',
          format: 'detailed',
          period: undefined,
          metrics: ['cpu', 'memory', 'disk']
        });
      });

      it('should use custom period', async () => {
        const mockClient = {
          initialize: vi.fn(),
          generateReport: vi.fn().mockResolvedValue({
            metrics: [],
            period: '2024-01-01 to 2024-01-31',
            summary: []
          }),
          sendReport: vi.fn().mockResolvedValue({
            success: true,
            reportId: 'report-789',
            channel: '#custom'
          })
        };
        vi.mocked(SlackClient).mockImplementation(() => mockClient as any);

        await slackReport('custom', {
          period: '2024-01-01,2024-01-31'
        });

        expect(mockClient.generateReport).toHaveBeenCalledWith(
          expect.objectContaining({
            period: '2024-01-01,2024-01-31'
          })
        );
      });

      it('should handle report send failure', async () => {
        const mockClient = {
          initialize: vi.fn(),
          generateReport: vi.fn().mockResolvedValue({
            metrics: [],
            period: 'daily',
            summary: []
          }),
          sendReport: vi.fn().mockResolvedValue({
            success: false,
            error: 'Channel not found'
          })
        };
        vi.mocked(SlackClient).mockImplementation(() => mockClient as any);

        await expect(slackReport('daily')).rejects.toThrow();
      });
    });
  });

  // ==========================================================================
  // EMAIL INTEGRATION COMMANDS (16 tests)
  // ==========================================================================

  describe('Email Integration Commands', () => {
    describe('email setup', () => {
      it('should setup email with SMTP configuration', async () => {
        const mockClient = {
          initialize: vi.fn(),
          setup: vi.fn(),
          testConnection: vi.fn().mockResolvedValue({
            success: true,
            provider: 'smtp',
            fromEmail: 'bot@example.com',
            status: 'connected'
          }),
          saveConfig: vi.fn()
        };
        vi.mocked(EmailClient).mockImplementation(() => mockClient as any);

        await emailSetup({
          provider: 'smtp',
          smtp: 'smtp.gmail.com',
          port: 587,
          username: 'user@gmail.com',
          password: 'password'
        });

        expect(mockClient.setup).toHaveBeenCalledWith({
          provider: 'smtp',
          smtp: 'smtp.gmail.com',
          port: 587,
          username: 'user@gmail.com',
          password: 'password'
        });
        expect(mockClient.testConnection).toHaveBeenCalled();
      });

      it('should handle interactive setup', async () => {
        const inquirer = await import('inquirer');
        vi.mocked(inquirer.default.prompt).mockResolvedValue({
          provider: 'sendgrid',
          username: 'apikey',
          password: 'SG.xxx',
          fromEmail: 'noreply@example.com',
          fromName: 'AI-Shell'
        });

        const mockClient = {
          initialize: vi.fn(),
          setup: vi.fn(),
          testConnection: vi.fn().mockResolvedValue({
            success: true,
            provider: 'sendgrid',
            fromEmail: 'noreply@example.com',
            status: 'connected'
          }),
          saveConfig: vi.fn()
        };
        vi.mocked(EmailClient).mockImplementation(() => mockClient as any);

        await emailSetup({ interactive: true });

        expect(inquirer.default.prompt).toHaveBeenCalled();
        expect(mockClient.setup).toHaveBeenCalled();
      });

      it('should handle connection test failure', async () => {
        const mockClient = {
          initialize: vi.fn(),
          setup: vi.fn(),
          testConnection: vi.fn().mockResolvedValue({
            success: false,
            error: 'Authentication failed'
          }),
          saveConfig: vi.fn()
        };
        vi.mocked(EmailClient).mockImplementation(() => mockClient as any);

        await expect(emailSetup({
          provider: 'smtp',
          smtp: 'invalid.server.com'
        })).rejects.toThrow();
      });

      it('should support different providers', async () => {
        const mockClient = {
          initialize: vi.fn(),
          setup: vi.fn(),
          testConnection: vi.fn().mockResolvedValue({
            success: true,
            provider: 'mailgun',
            fromEmail: 'bot@mailgun.com',
            status: 'connected'
          }),
          saveConfig: vi.fn()
        };
        vi.mocked(EmailClient).mockImplementation(() => mockClient as any);

        await emailSetup({
          provider: 'mailgun',
          username: 'api',
          password: 'key-xxx'
        });

        expect(mockClient.setup).toHaveBeenCalledWith(
          expect.objectContaining({
            provider: 'mailgun'
          })
        );
      });
    });

    describe('email send', () => {
      it('should send email with plain text body', async () => {
        const mockClient = {
          initialize: vi.fn(),
          sendEmail: vi.fn().mockResolvedValue({
            success: true,
            messageId: '<msg-123@example.com>',
            accepted: ['user@example.com'],
            rejected: []
          })
        };
        vi.mocked(EmailClient).mockImplementation(() => mockClient as any);

        await emailSend('user@example.com', 'Test Subject', {
          body: 'Test email body'
        });

        expect(mockClient.sendEmail).toHaveBeenCalledWith({
          to: ['user@example.com'],
          cc: [],
          bcc: [],
          subject: 'Test Subject',
          text: 'Test email body',
          html: undefined,
          attachments: [],
          priority: 'normal'
        });
      });

      it('should send email with HTML body', async () => {
        const mockClient = {
          initialize: vi.fn(),
          sendEmail: vi.fn().mockResolvedValue({
            success: true,
            messageId: '<msg-456@example.com>',
            accepted: ['user@example.com'],
            rejected: []
          })
        };
        vi.mocked(EmailClient).mockImplementation(() => mockClient as any);

        await emailSend('user@example.com', 'HTML Email', {
          html: '<h1>Test</h1>'
        });

        expect(mockClient.sendEmail).toHaveBeenCalledWith(
          expect.objectContaining({
            html: '<h1>Test</h1>'
          })
        );
      });

      it('should handle attachments', async () => {
        vi.mocked(fs.readFile).mockResolvedValue(Buffer.from('file content'));

        const mockClient = {
          initialize: vi.fn(),
          sendEmail: vi.fn().mockResolvedValue({
            success: true,
            messageId: '<msg-789@example.com>',
            accepted: ['user@example.com'],
            rejected: []
          })
        };
        vi.mocked(EmailClient).mockImplementation(() => mockClient as any);

        await emailSend('user@example.com', 'With Attachment', {
          body: 'See attachment',
          attachments: '/path/to/file.pdf'
        });

        expect(fs.readFile).toHaveBeenCalledWith('/path/to/file.pdf');
        expect(mockClient.sendEmail).toHaveBeenCalledWith(
          expect.objectContaining({
            attachments: expect.arrayContaining([
              expect.objectContaining({
                filename: 'file.pdf'
              })
            ])
          })
        );
      });

      it('should handle CC and BCC recipients', async () => {
        const mockClient = {
          initialize: vi.fn(),
          sendEmail: vi.fn().mockResolvedValue({
            success: true,
            messageId: '<msg-101@example.com>',
            accepted: ['to@example.com', 'cc@example.com'],
            rejected: []
          })
        };
        vi.mocked(EmailClient).mockImplementation(() => mockClient as any);

        await emailSend('to@example.com', 'Multi Recipients', {
          body: 'Test',
          cc: 'cc@example.com',
          bcc: 'bcc@example.com'
        });

        expect(mockClient.sendEmail).toHaveBeenCalledWith(
          expect.objectContaining({
            cc: ['cc@example.com'],
            bcc: ['bcc@example.com']
          })
        );
      });
    });

    describe('email alert', () => {
      it('should send alert email', async () => {
        const mockClient = {
          initialize: vi.fn(),
          sendAlert: vi.fn().mockResolvedValue({
            success: true,
            messageId: '<alert-123@example.com>',
            recipients: ['ops@example.com']
          })
        };
        vi.mocked(EmailClient).mockImplementation(() => mockClient as any);

        await emailAlert('ops@example.com', 'ALERT-001', {
          severity: 'critical'
        });

        expect(mockClient.sendAlert).toHaveBeenCalledWith({
          to: ['ops@example.com'],
          alertId: 'ALERT-001',
          severity: 'critical',
          context: null,
          incidentId: undefined,
          timestamp: expect.any(String)
        });
      });

      it('should handle context data', async () => {
        const mockClient = {
          initialize: vi.fn(),
          sendAlert: vi.fn().mockResolvedValue({
            success: true,
            messageId: '<alert-456@example.com>',
            recipients: ['team@example.com']
          })
        };
        vi.mocked(EmailClient).mockImplementation(() => mockClient as any);

        const context = JSON.stringify({ server: 'prod-01', load: '95%' });
        await emailAlert('team@example.com', 'ALERT-002', {
          severity: 'warning',
          context
        });

        expect(mockClient.sendAlert).toHaveBeenCalledWith(
          expect.objectContaining({
            context: { server: 'prod-01', load: '95%' }
          })
        );
      });

      it('should link to incident', async () => {
        const mockClient = {
          initialize: vi.fn(),
          sendAlert: vi.fn().mockResolvedValue({
            success: true,
            messageId: '<alert-789@example.com>',
            recipients: ['oncall@example.com']
          })
        };
        vi.mocked(EmailClient).mockImplementation(() => mockClient as any);

        await emailAlert('oncall@example.com', 'ALERT-003', {
          severity: 'critical',
          incident: 'INC-123'
        });

        expect(mockClient.sendAlert).toHaveBeenCalledWith(
          expect.objectContaining({
            incidentId: 'INC-123'
          })
        );
      });

      it('should handle send failure', async () => {
        const mockClient = {
          initialize: vi.fn(),
          sendAlert: vi.fn().mockResolvedValue({
            success: false,
            error: 'Recipient not found'
          })
        };
        vi.mocked(EmailClient).mockImplementation(() => mockClient as any);

        await expect(emailAlert('invalid@example.com', 'ALERT-004'))
          .rejects.toThrow();
      });
    });

    describe('email report', () => {
      it('should generate and send HTML report', async () => {
        const mockClient = {
          initialize: vi.fn(),
          generateReport: vi.fn().mockResolvedValue({
            metrics: ['cpu', 'memory'],
            data: {}
          }),
          sendReport: vi.fn().mockResolvedValue({
            success: true,
            reportId: 'report-123',
            recipients: ['admin@example.com']
          })
        };
        vi.mocked(EmailClient).mockImplementation(() => mockClient as any);

        await emailReport('daily', 'admin@example.com', {
          format: 'html'
        });

        expect(mockClient.generateReport).toHaveBeenCalledWith({
          type: 'daily',
          format: 'html',
          period: undefined,
          metrics: undefined,
          includeCharts: false
        });
        expect(mockClient.sendReport).toHaveBeenCalled();
      });

      it('should generate PDF report', async () => {
        const mockClient = {
          initialize: vi.fn(),
          generateReport: vi.fn().mockResolvedValue({
            metrics: ['performance'],
            data: {}
          }),
          sendReport: vi.fn().mockResolvedValue({
            success: true,
            reportId: 'report-456',
            recipients: ['manager@example.com']
          })
        };
        vi.mocked(EmailClient).mockImplementation(() => mockClient as any);

        await emailReport('weekly', 'manager@example.com', {
          format: 'pdf'
        });

        expect(mockClient.generateReport).toHaveBeenCalledWith(
          expect.objectContaining({
            format: 'pdf'
          })
        );
      });

      it('should include attachments', async () => {
        const mockClient = {
          initialize: vi.fn(),
          generateReport: vi.fn().mockResolvedValue({
            metrics: ['sales'],
            data: {}
          }),
          sendReport: vi.fn().mockResolvedValue({
            success: true,
            reportId: 'report-789',
            recipients: ['team@example.com'],
            attachments: ['chart1.png', 'chart2.png']
          })
        };
        vi.mocked(EmailClient).mockImplementation(() => mockClient as any);

        await emailReport('monthly', 'team@example.com', {
          attachments: true
        });

        expect(mockClient.sendReport).toHaveBeenCalledWith(
          expect.objectContaining({
            attachments: true
          })
        );
      });

      it('should handle report send failure', async () => {
        const mockClient = {
          initialize: vi.fn(),
          generateReport: vi.fn().mockResolvedValue({
            metrics: [],
            data: {}
          }),
          sendReport: vi.fn().mockResolvedValue({
            success: false,
            error: 'Report generation failed'
          })
        };
        vi.mocked(EmailClient).mockImplementation(() => mockClient as any);

        await expect(emailReport('daily', 'user@example.com'))
          .rejects.toThrow();
      });
    });
  });

  // ==========================================================================
  // FEDERATION COMMANDS (16 tests)
  // ==========================================================================

  describe('Federation Commands', () => {
    describe('federation add', () => {
      it('should add PostgreSQL database to federation', async () => {
        const mockEngine = {
          initialize: vi.fn(),
          addDatabase: vi.fn().mockResolvedValue({
            success: true,
            federationId: 'fed-123',
            alias: 'mydb',
            type: 'postgresql',
            status: 'connected',
            schemas: ['public', 'app']
          })
        };
        vi.mocked(FederationEngine).mockImplementation(() => mockEngine as any);

        await federationAdd('mydb', {
          type: 'postgresql',
          host: 'localhost',
          port: 5432
        });

        expect(mockEngine.addDatabase).toHaveBeenCalledWith({
          name: 'mydb',
          type: 'postgresql',
          host: 'localhost',
          port: 5432,
          username: undefined,
          password: undefined,
          alias: 'mydb'
        });
      });

      it('should add MySQL database with custom alias', async () => {
        const mockEngine = {
          initialize: vi.fn(),
          addDatabase: vi.fn().mockResolvedValue({
            success: true,
            federationId: 'fed-456',
            alias: 'analytics',
            type: 'mysql',
            status: 'connected',
            schemas: ['analytics_db']
          })
        };
        vi.mocked(FederationEngine).mockImplementation(() => mockEngine as any);

        await federationAdd('analytics_db', {
          type: 'mysql',
          alias: 'analytics'
        });

        expect(mockEngine.addDatabase).toHaveBeenCalledWith(
          expect.objectContaining({
            alias: 'analytics'
          })
        );
      });

      it('should handle connection failure', async () => {
        const mockEngine = {
          initialize: vi.fn(),
          addDatabase: vi.fn().mockResolvedValue({
            success: false,
            error: 'Connection refused'
          })
        };
        vi.mocked(FederationEngine).mockImplementation(() => mockEngine as any);

        await expect(federationAdd('unreachable', {
          type: 'postgresql'
        })).rejects.toThrow();
      });

      it('should add MongoDB to federation', async () => {
        const mockEngine = {
          initialize: vi.fn(),
          addDatabase: vi.fn().mockResolvedValue({
            success: true,
            federationId: 'fed-789',
            alias: 'documents',
            type: 'mongodb',
            status: 'connected',
            schemas: ['admin', 'local', 'documents']
          })
        };
        vi.mocked(FederationEngine).mockImplementation(() => mockEngine as any);

        await federationAdd('documents', {
          type: 'mongodb',
          host: 'mongo.example.com'
        });

        expect(mockEngine.addDatabase).toHaveBeenCalledWith(
          expect.objectContaining({
            type: 'mongodb'
          })
        );
      });
    });

    describe('federation remove', () => {
      it('should remove database with confirmation', async () => {
        const inquirer = await import('inquirer');
        vi.mocked(inquirer.default.prompt).mockResolvedValue({
          confirm: true
        });

        const mockEngine = {
          initialize: vi.fn(),
          removeDatabase: vi.fn().mockResolvedValue({
            success: true,
            connectionsClosed: 5,
            cacheCleared: 123
          })
        };
        vi.mocked(FederationEngine).mockImplementation(() => mockEngine as any);

        await federationRemove('olddb', { force: false });

        expect(inquirer.default.prompt).toHaveBeenCalled();
        expect(mockEngine.removeDatabase).toHaveBeenCalledWith('olddb');
      });

      it('should remove database with force flag', async () => {
        const mockEngine = {
          initialize: vi.fn(),
          removeDatabase: vi.fn().mockResolvedValue({
            success: true,
            connectionsClosed: 3,
            cacheCleared: 45
          })
        };
        vi.mocked(FederationEngine).mockImplementation(() => mockEngine as any);

        await federationRemove('testdb', { force: true });

        expect(mockEngine.removeDatabase).toHaveBeenCalledWith('testdb');
      });

      it('should handle removal failure', async () => {
        const mockEngine = {
          initialize: vi.fn(),
          removeDatabase: vi.fn().mockResolvedValue({
            success: false,
            error: 'Database not found in federation'
          })
        };
        vi.mocked(FederationEngine).mockImplementation(() => mockEngine as any);

        await expect(federationRemove('nonexistent', { force: true }))
          .rejects.toThrow();
      });

      it('should cancel removal on user decline', async () => {
        const inquirer = await import('inquirer');
        vi.mocked(inquirer.default.prompt).mockResolvedValue({
          confirm: false
        });

        const mockEngine = {
          initialize: vi.fn(),
          removeDatabase: vi.fn()
        };
        vi.mocked(FederationEngine).mockImplementation(() => mockEngine as any);

        await federationRemove('keepdb', { force: false });

        expect(mockEngine.removeDatabase).not.toHaveBeenCalled();
      });
    });

    describe('federation query', () => {
      it('should execute federated query', async () => {
        const mockEngine = {
          initialize: vi.fn(),
          executeQuery: vi.fn().mockResolvedValue({
            success: true,
            databasesQueried: 2,
            rowCount: 10,
            executionTime: 45,
            rows: [
              { id: 1, name: 'Test' },
              { id: 2, name: 'Data' }
            ]
          })
        };
        vi.mocked(FederationEngine).mockImplementation(() => mockEngine as any);

        await federationQuery('SELECT * FROM users LIMIT 10', {});

        expect(mockEngine.executeQuery).toHaveBeenCalledWith({
          sql: 'SELECT * FROM users LIMIT 10',
          databases: undefined,
          explain: false
        });
      });

      it('should query specific databases', async () => {
        const mockEngine = {
          initialize: vi.fn(),
          executeQuery: vi.fn().mockResolvedValue({
            success: true,
            databasesQueried: 2,
            rowCount: 5,
            executionTime: 30,
            rows: []
          })
        };
        vi.mocked(FederationEngine).mockImplementation(() => mockEngine as any);

        await federationQuery('SELECT COUNT(*) FROM orders', {
          databases: 'db1,db2'
        });

        expect(mockEngine.executeQuery).toHaveBeenCalledWith({
          sql: 'SELECT COUNT(*) FROM orders',
          databases: ['db1', 'db2'],
          explain: false
        });
      });

      it('should show execution plan with explain', async () => {
        const mockEngine = {
          initialize: vi.fn(),
          executeQuery: vi.fn().mockResolvedValue({
            success: true,
            databasesQueried: 1,
            rowCount: 0,
            executionTime: 15,
            rows: [],
            executionPlan: 'Seq Scan on users...'
          })
        };
        vi.mocked(FederationEngine).mockImplementation(() => mockEngine as any);

        await federationQuery('SELECT * FROM users', {
          explain: true
        });

        expect(mockEngine.executeQuery).toHaveBeenCalledWith(
          expect.objectContaining({
            explain: true
          })
        );
      });

      it('should save results to file', async () => {
        const mockEngine = {
          initialize: vi.fn(),
          executeQuery: vi.fn().mockResolvedValue({
            success: true,
            databasesQueried: 1,
            rowCount: 3,
            executionTime: 20,
            rows: [{ id: 1 }, { id: 2 }, { id: 3 }]
          })
        };
        vi.mocked(FederationEngine).mockImplementation(() => mockEngine as any);
        vi.mocked(fs.writeFile).mockResolvedValue(undefined);

        await federationQuery('SELECT * FROM items', {
          output: '/tmp/results.json'
        });

        expect(fs.writeFile).toHaveBeenCalledWith(
          '/tmp/results.json',
          expect.any(String)
        );
      });
    });

    describe('federation status', () => {
      it('should show basic federation status', async () => {
        const mockEngine = {
          initialize: vi.fn(),
          getStatus: vi.fn().mockResolvedValue({
            status: 'healthy',
            totalDatabases: 3,
            activeConnections: 3,
            cachedQueries: 45,
            databases: [
              {
                alias: 'db1',
                type: 'postgresql',
                status: 'connected',
                schemas: ['public'],
                lastQuery: '2024-01-15 10:30:00'
              }
            ],
            metrics: {
              totalQueries: 150,
              avgExecutionTime: 25,
              cacheHitRate: 85,
              dataTransferred: '1.2 GB'
            }
          })
        };
        vi.mocked(FederationEngine).mockImplementation(() => mockEngine as any);

        await federationStatus({});

        expect(mockEngine.getStatus).toHaveBeenCalledWith(undefined);
      });

      it('should show detailed metrics', async () => {
        const mockEngine = {
          initialize: vi.fn(),
          getStatus: vi.fn().mockResolvedValue({
            status: 'healthy',
            totalDatabases: 2,
            activeConnections: 2,
            cachedQueries: 20,
            databases: [],
            metrics: {
              totalQueries: 100,
              avgExecutionTime: 30,
              cacheHitRate: 90,
              dataTransferred: '500 MB'
            }
          })
        };
        vi.mocked(FederationEngine).mockImplementation(() => mockEngine as any);

        await federationStatus({ detailed: true });

        expect(mockEngine.getStatus).toHaveBeenCalled();
      });

      it('should show status for specific database', async () => {
        const mockEngine = {
          initialize: vi.fn(),
          getStatus: vi.fn().mockResolvedValue({
            status: 'healthy',
            totalDatabases: 1,
            activeConnections: 1,
            cachedQueries: 10,
            databases: [
              {
                alias: 'mydb',
                type: 'postgresql',
                status: 'connected',
                schemas: ['public', 'app'],
                lastQuery: '2024-01-15 11:00:00'
              }
            ],
            metrics: {}
          })
        };
        vi.mocked(FederationEngine).mockImplementation(() => mockEngine as any);

        await federationStatus({ database: 'mydb' });

        expect(mockEngine.getStatus).toHaveBeenCalledWith('mydb');
      });

      it('should handle disconnected databases', async () => {
        const mockEngine = {
          initialize: vi.fn(),
          getStatus: vi.fn().mockResolvedValue({
            status: 'degraded',
            totalDatabases: 2,
            activeConnections: 1,
            cachedQueries: 5,
            databases: [
              {
                alias: 'db1',
                type: 'postgresql',
                status: 'connected',
                schemas: ['public'],
                lastQuery: 'now'
              },
              {
                alias: 'db2',
                type: 'mysql',
                status: 'disconnected',
                schemas: [],
                lastQuery: 'never'
              }
            ],
            metrics: {}
          })
        };
        vi.mocked(FederationEngine).mockImplementation(() => mockEngine as any);

        await federationStatus({});

        expect(mockEngine.getStatus).toHaveBeenCalled();
      });
    });
  });

  // ==========================================================================
  // SCHEMA MANAGEMENT COMMANDS (16 tests)
  // ==========================================================================

  describe('Schema Management Commands', () => {
    describe('schema diff', () => {
      it('should compare schemas and show differences', async () => {
        const mockManager = {
          initialize: vi.fn(),
          comparSchemas: vi.fn().mockResolvedValue({
            tablesAdded: ['new_table'],
            tablesRemoved: ['old_table'],
            tablesModified: [
              {
                name: 'users',
                changes: [
                  { description: 'Added column: email' }
                ]
              }
            ],
            columnsChanged: 5,
            indexesChanged: 2,
            isEmpty: false
          })
        };
        vi.mocked(SchemaManager).mockImplementation(() => mockManager as any);

        await schemaDiff('source_db', 'target_db', {});

        expect(mockManager.comparSchemas).toHaveBeenCalledWith(
          'source_db',
          'target_db',
          { ignoreData: undefined }
        );
      });

      it('should generate migration SQL', async () => {
        const mockManager = {
          initialize: vi.fn(),
          comparSchemas: vi.fn().mockResolvedValue({
            tablesAdded: [],
            tablesRemoved: [],
            tablesModified: [],
            columnsChanged: 0,
            indexesChanged: 0,
            isEmpty: true
          }),
          generateMigrationSql: vi.fn().mockResolvedValue(
            'ALTER TABLE users ADD COLUMN email VARCHAR(255);'
          )
        };
        vi.mocked(SchemaManager).mockImplementation(() => mockManager as any);

        await schemaDiff('db1', 'db2', {
          format: 'sql'
        });

        expect(mockManager.generateMigrationSql).toHaveBeenCalled();
      });

      it('should save diff to file', async () => {
        const mockManager = {
          initialize: vi.fn(),
          comparSchemas: vi.fn().mockResolvedValue({
            tablesAdded: ['table1'],
            tablesRemoved: [],
            tablesModified: [],
            columnsChanged: 0,
            indexesChanged: 0,
            isEmpty: false
          }),
          generateMigrationSql: vi.fn().mockResolvedValue('CREATE TABLE table1;'),
          formatDiffAsText: vi.fn().mockReturnValue('Text diff output')
        };
        vi.mocked(SchemaManager).mockImplementation(() => mockManager as any);
        vi.mocked(fs.writeFile).mockResolvedValue(undefined);

        await schemaDiff('db1', 'db2', {
          output: '/tmp/diff.txt',
          format: 'text'
        });

        expect(fs.writeFile).toHaveBeenCalled();
      });

      it('should ignore data differences', async () => {
        const mockManager = {
          initialize: vi.fn(),
          comparSchemas: vi.fn().mockResolvedValue({
            tablesAdded: [],
            tablesRemoved: [],
            tablesModified: [],
            columnsChanged: 0,
            indexesChanged: 0,
            isEmpty: true
          })
        };
        vi.mocked(SchemaManager).mockImplementation(() => mockManager as any);

        await schemaDiff('db1', 'db2', {
          ignoreData: true
        });

        expect(mockManager.comparSchemas).toHaveBeenCalledWith(
          'db1',
          'db2',
          { ignoreData: true }
        );
      });
    });

    describe('schema sync', () => {
      it('should sync schema with dry-run', async () => {
        const mockManager = {
          initialize: vi.fn(),
          comparSchemas: vi.fn().mockResolvedValue({
            isEmpty: false
          }),
          syncSchemas: vi.fn().mockResolvedValue({
            success: true,
            changesApplied: 5,
            statementsExecuted: 10,
            executionTime: 150,
            statements: [
              'ALTER TABLE users ADD COLUMN email VARCHAR(255);'
            ],
            warnings: []
          })
        };
        vi.mocked(SchemaManager).mockImplementation(() => mockManager as any);

        await schemaSync('source', 'target', {
          dryRun: true
        });

        expect(mockManager.syncSchemas).toHaveBeenCalledWith(
          'source',
          'target',
          { dryRun: true }
        );
      });

      it('should create backup before sync', async () => {
        const inquirer = await import('inquirer');
        vi.mocked(inquirer.default.prompt).mockResolvedValue({
          confirm: true
        });

        const mockManager = {
          initialize: vi.fn(),
          comparSchemas: vi.fn().mockResolvedValue({
            isEmpty: false
          }),
          createBackup: vi.fn().mockResolvedValue({
            path: '/backups/target-2024-01-15.sql'
          }),
          syncSchemas: vi.fn().mockResolvedValue({
            success: true,
            changesApplied: 3,
            statementsExecuted: 5,
            executionTime: 100,
            warnings: []
          })
        };
        vi.mocked(SchemaManager).mockImplementation(() => mockManager as any);

        await schemaSync('source', 'target', {
          backup: true,
          force: false
        });

        expect(mockManager.createBackup).toHaveBeenCalledWith('target');
        expect(mockManager.syncSchemas).toHaveBeenCalled();
      });

      it('should skip confirmation with force flag', async () => {
        const mockManager = {
          initialize: vi.fn(),
          comparSchemas: vi.fn().mockResolvedValue({
            isEmpty: false
          }),
          syncSchemas: vi.fn().mockResolvedValue({
            success: true,
            changesApplied: 2,
            statementsExecuted: 4,
            executionTime: 80,
            warnings: []
          })
        };
        vi.mocked(SchemaManager).mockImplementation(() => mockManager as any);

        await schemaSync('source', 'target', {
          force: true
        });

        expect(mockManager.syncSchemas).toHaveBeenCalled();
      });

      it('should handle sync failure', async () => {
        const mockManager = {
          initialize: vi.fn(),
          comparSchemas: vi.fn().mockResolvedValue({
            isEmpty: false
          }),
          syncSchemas: vi.fn().mockResolvedValue({
            success: false,
            error: 'Permission denied on target database'
          })
        };
        vi.mocked(SchemaManager).mockImplementation(() => mockManager as any);

        await expect(schemaSync('source', 'target', {
          force: true
        })).rejects.toThrow();
      });
    });

    describe('schema export', () => {
      it('should export schema to SQL file', async () => {
        const mockManager = {
          initialize: vi.fn(),
          exportSchema: vi.fn().mockResolvedValue({
            content: 'CREATE TABLE users(...);',
            format: 'sql',
            tables: ['users', 'orders'],
            rowCount: 0
          })
        };
        vi.mocked(SchemaManager).mockImplementation(() => mockManager as any);
        vi.mocked(fs.writeFile).mockResolvedValue(undefined);

        await schemaExport('mydb', {
          format: 'sql'
        });

        expect(mockManager.exportSchema).toHaveBeenCalledWith(
          'mydb',
          {
            format: 'sql',
            includeData: undefined,
            tables: undefined
          }
        );
        expect(fs.writeFile).toHaveBeenCalled();
      });

      it('should export with data', async () => {
        const mockManager = {
          initialize: vi.fn(),
          exportSchema: vi.fn().mockResolvedValue({
            content: 'CREATE TABLE...\nINSERT INTO...',
            format: 'sql',
            tables: ['users'],
            rowCount: 100
          })
        };
        vi.mocked(SchemaManager).mockImplementation(() => mockManager as any);
        vi.mocked(fs.writeFile).mockResolvedValue(undefined);

        await schemaExport('mydb', {
          includeData: true
        });

        expect(mockManager.exportSchema).toHaveBeenCalledWith(
          'mydb',
          expect.objectContaining({
            includeData: true
          })
        );
      });

      it('should export specific tables', async () => {
        const mockManager = {
          initialize: vi.fn(),
          exportSchema: vi.fn().mockResolvedValue({
            content: 'CREATE TABLE users(...);',
            format: 'json',
            tables: ['users', 'orders'],
            rowCount: 0
          })
        };
        vi.mocked(SchemaManager).mockImplementation(() => mockManager as any);
        vi.mocked(fs.writeFile).mockResolvedValue(undefined);

        await schemaExport('mydb', {
          tables: 'users,orders',
          format: 'json'
        });

        expect(mockManager.exportSchema).toHaveBeenCalledWith(
          'mydb',
          expect.objectContaining({
            tables: ['users', 'orders']
          })
        );
      });

      it('should use custom output path', async () => {
        const mockManager = {
          initialize: vi.fn(),
          exportSchema: vi.fn().mockResolvedValue({
            content: 'schema content',
            format: 'sql',
            tables: [],
            rowCount: 0
          })
        };
        vi.mocked(SchemaManager).mockImplementation(() => mockManager as any);
        vi.mocked(fs.writeFile).mockResolvedValue(undefined);

        await schemaExport('mydb', {
          output: '/custom/path/schema.sql'
        });

        expect(fs.writeFile).toHaveBeenCalledWith(
          '/custom/path/schema.sql',
          expect.any(String)
        );
      });
    });

    describe('schema import', () => {
      it('should import schema from SQL file', async () => {
        vi.mocked(fs.readFile).mockResolvedValue('CREATE TABLE users(...);');

        const mockManager = {
          initialize: vi.fn(),
          importSchema: vi.fn().mockResolvedValue({
            success: true,
            tablesCreated: 2,
            statementsExecuted: 5,
            executionTime: 120,
            dataImported: false,
            warnings: []
          })
        };
        vi.mocked(SchemaManager).mockImplementation(() => mockManager as any);

        await schemaImport('/path/to/schema.sql', {
          database: 'mydb',
          force: true
        });

        expect(fs.readFile).toHaveBeenCalledWith('/path/to/schema.sql', 'utf-8');
        expect(mockManager.importSchema).toHaveBeenCalledWith(
          'CREATE TABLE users(...);',
          {
            database: 'mydb',
            format: 'sql',
            dryRun: undefined
          }
        );
      });

      it('should validate with dry-run', async () => {
        vi.mocked(fs.readFile).mockResolvedValue('{}');

        const mockManager = {
          initialize: vi.fn(),
          importSchema: vi.fn().mockResolvedValue({
            success: true,
            tablesCreated: 0,
            statementsExecuted: 0,
            executionTime: 10,
            dataImported: false,
            warnings: ['Dry run - no changes made']
          })
        };
        vi.mocked(SchemaManager).mockImplementation(() => mockManager as any);

        await schemaImport('/path/to/schema.json', {
          dryRun: true
        });

        expect(mockManager.importSchema).toHaveBeenCalledWith(
          '{}',
          expect.objectContaining({
            dryRun: true
          })
        );
      });

      it('should confirm before import', async () => {
        vi.mocked(fs.readFile).mockResolvedValue('schema content');

        const inquirer = await import('inquirer');
        vi.mocked(inquirer.default.prompt).mockResolvedValue({
          confirm: true
        });

        const mockManager = {
          initialize: vi.fn(),
          importSchema: vi.fn().mockResolvedValue({
            success: true,
            tablesCreated: 3,
            statementsExecuted: 7,
            executionTime: 200,
            dataImported: false,
            warnings: []
          })
        };
        vi.mocked(SchemaManager).mockImplementation(() => mockManager as any);

        await schemaImport('/path/to/schema.sql', {
          force: false
        });

        expect(inquirer.default.prompt).toHaveBeenCalled();
        expect(mockManager.importSchema).toHaveBeenCalled();
      });

      it('should handle import failure', async () => {
        vi.mocked(fs.readFile).mockResolvedValue('invalid schema');

        const mockManager = {
          initialize: vi.fn(),
          importSchema: vi.fn().mockResolvedValue({
            success: false,
            error: 'Syntax error in schema'
          })
        };
        vi.mocked(SchemaManager).mockImplementation(() => mockManager as any);

        await expect(schemaImport('/path/to/bad.sql', {
          force: true
        })).rejects.toThrow();
      });
    });
  });

  // ==========================================================================
  // AUTONOMOUS AGENT COMMANDS (16 tests)
  // ==========================================================================

  describe('Autonomous Agent Commands', () => {
    describe('ada start', () => {
      it('should start ADA in full mode', async () => {
        const mockAgent = {
          initialize: vi.fn(),
          start: vi.fn().mockResolvedValue({
            success: true,
            agentId: 'ada-001',
            mode: 'full',
            checkInterval: 60000,
            autoFix: true,
            databases: ['db1', 'db2'],
            capabilities: [
              'Performance Monitoring',
              'Index Optimization',
              'Query Optimization'
            ]
          })
        };
        vi.mocked(ADAAgent).mockImplementation(() => mockAgent as any);

        await adaStart({});

        expect(mockAgent.start).toHaveBeenCalledWith({
          mode: 'full',
          checkInterval: 60000,
          autoFix: true
        });
      });

      it('should start ADA in monitoring mode', async () => {
        const mockAgent = {
          initialize: vi.fn(),
          start: vi.fn().mockResolvedValue({
            success: true,
            agentId: 'ada-002',
            mode: 'monitoring',
            checkInterval: 30000,
            autoFix: false,
            databases: ['db1'],
            capabilities: ['Performance Monitoring']
          })
        };
        vi.mocked(ADAAgent).mockImplementation(() => mockAgent as any);

        await adaStart({
          mode: 'monitoring',
          interval: 30,
          autoFix: false
        });

        expect(mockAgent.start).toHaveBeenCalledWith({
          mode: 'monitoring',
          checkInterval: 30000,
          autoFix: false
        });
      });

      it('should start ADA with custom interval', async () => {
        const mockAgent = {
          initialize: vi.fn(),
          start: vi.fn().mockResolvedValue({
            success: true,
            agentId: 'ada-003',
            mode: 'optimization',
            checkInterval: 120000,
            autoFix: true,
            databases: [],
            capabilities: ['Index Optimization']
          })
        };
        vi.mocked(ADAAgent).mockImplementation(() => mockAgent as any);

        await adaStart({
          mode: 'optimization',
          interval: 120
        });

        expect(mockAgent.start).toHaveBeenCalledWith(
          expect.objectContaining({
            checkInterval: 120000
          })
        );
      });

      it('should handle start failure', async () => {
        const mockAgent = {
          initialize: vi.fn(),
          start: vi.fn().mockResolvedValue({
            success: false,
            error: 'Agent already running'
          })
        };
        vi.mocked(ADAAgent).mockImplementation(() => mockAgent as any);

        await expect(adaStart({})).rejects.toThrow();
      });
    });

    describe('ada stop', () => {
      it('should stop ADA gracefully', async () => {
        const mockAgent = {
          initialize: vi.fn(),
          stop: vi.fn().mockResolvedValue({
            success: true,
            runtime: '2 hours 15 minutes',
            checksPerformed: 135,
            issuesDetected: 12,
            fixesApplied: 8
          })
        };
        vi.mocked(ADAAgent).mockImplementation(() => mockAgent as any);

        await adaStop({});

        expect(mockAgent.stop).toHaveBeenCalledWith({
          force: undefined,
          exportMetrics: undefined
        });
      });

      it('should force stop ADA', async () => {
        const mockAgent = {
          initialize: vi.fn(),
          stop: vi.fn().mockResolvedValue({
            success: true,
            runtime: '30 minutes',
            checksPerformed: 30,
            issuesDetected: 5,
            fixesApplied: 3
          })
        };
        vi.mocked(ADAAgent).mockImplementation(() => mockAgent as any);

        await adaStop({
          force: true
        });

        expect(mockAgent.stop).toHaveBeenCalledWith(
          expect.objectContaining({
            force: true
          })
        );
      });

      it('should export metrics on stop', async () => {
        const mockAgent = {
          initialize: vi.fn(),
          stop: vi.fn().mockResolvedValue({
            success: true,
            runtime: '1 hour',
            checksPerformed: 60,
            issuesDetected: 8,
            fixesApplied: 5,
            metricsExported: true,
            metricsPath: '/var/log/ada/metrics-2024-01-15.json'
          })
        };
        vi.mocked(ADAAgent).mockImplementation(() => mockAgent as any);

        await adaStop({
          export: true
        });

        expect(mockAgent.stop).toHaveBeenCalledWith(
          expect.objectContaining({
            exportMetrics: true
          })
        );
      });

      it('should handle stop failure', async () => {
        const mockAgent = {
          initialize: vi.fn(),
          stop: vi.fn().mockResolvedValue({
            success: false,
            error: 'Agent not running'
          })
        };
        vi.mocked(ADAAgent).mockImplementation(() => mockAgent as any);

        await expect(adaStop({})).rejects.toThrow();
      });
    });

    describe('ada status', () => {
      it('should show basic ADA status', async () => {
        const mockAgent = {
          initialize: vi.fn(),
          getStatus: vi.fn().mockResolvedValue({
            running: true,
            mode: 'full',
            uptime: '3 hours 45 minutes',
            nextCheck: 'in 2 minutes',
            databases: ['db1', 'db2', 'db3'],
            recentActivity: [],
            metrics: {},
            currentIssues: []
          })
        };
        vi.mocked(ADAAgent).mockImplementation(() => mockAgent as any);

        await adaStatus({});

        expect(mockAgent.getStatus).toHaveBeenCalled();
      });

      it('should show detailed status with metrics', async () => {
        const mockAgent = {
          initialize: vi.fn(),
          getStatus: vi.fn().mockResolvedValue({
            running: true,
            mode: 'full',
            uptime: '1 day 5 hours',
            nextCheck: 'in 30 seconds',
            databases: ['db1'],
            recentActivity: [
              {
                timestamp: '2024-01-15 10:00:00',
                type: 'optimization',
                description: 'Created index on users.email',
                success: true
              }
            ],
            metrics: {
              checksPerformed: 500,
              issuesDetected: 45,
              fixesApplied: 32,
              successRate: 95,
              avgResponseTime: 120
            },
            currentIssues: []
          })
        };
        vi.mocked(ADAAgent).mockImplementation(() => mockAgent as any);

        await adaStatus({
          detailed: true
        });

        expect(mockAgent.getStatus).toHaveBeenCalled();
      });

      it('should show current issues', async () => {
        const mockAgent = {
          initialize: vi.fn(),
          getStatus: vi.fn().mockResolvedValue({
            running: true,
            mode: 'monitoring',
            uptime: '2 hours',
            nextCheck: 'in 1 minute',
            databases: ['db1'],
            recentActivity: [],
            metrics: {},
            currentIssues: [
              {
                description: 'High CPU usage detected',
                database: 'db1',
                severity: 'warning'
              },
              {
                description: 'Slow query detected',
                database: 'db1',
                severity: 'info'
              }
            ]
          })
        };
        vi.mocked(ADAAgent).mockImplementation(() => mockAgent as any);

        await adaStatus({});

        expect(mockAgent.getStatus).toHaveBeenCalled();
      });

      it('should handle stopped agent status', async () => {
        const mockAgent = {
          initialize: vi.fn(),
          getStatus: vi.fn().mockResolvedValue({
            running: false
          })
        };
        vi.mocked(ADAAgent).mockImplementation(() => mockAgent as any);

        await adaStatus({});

        expect(mockAgent.getStatus).toHaveBeenCalled();
      });
    });

    describe('ada configure', () => {
      it('should configure ADA with non-interactive options', async () => {
        const mockAgent = {
          initialize: vi.fn(),
          configure: vi.fn().mockResolvedValue({
            success: true,
            config: {
              mode: 'full',
              interval: 60,
              autoFix: true,
              alertThreshold: 80,
              databases: ['db1', 'db2']
            }
          }),
          saveConfig: vi.fn()
        };
        vi.mocked(ADAAgent).mockImplementation(() => mockAgent as any);

        await adaConfigure({
          mode: 'full',
          interval: 60,
          autoFix: true,
          alertThreshold: 80
        });

        expect(mockAgent.configure).toHaveBeenCalledWith({
          mode: 'full',
          interval: 60,
          autoFix: true,
          alertThreshold: 80,
          databases: undefined
        });
        expect(mockAgent.saveConfig).toHaveBeenCalled();
      });

      it('should handle interactive configuration', async () => {
        const inquirer = await import('inquirer');
        vi.mocked(inquirer.default.prompt).mockResolvedValue({
          mode: 'monitoring',
          interval: 30,
          autoFix: false,
          alertThreshold: 90,
          enabledCapabilities: ['Performance Monitoring', 'Deadlock Detection']
        });

        const mockAgent = {
          initialize: vi.fn(),
          configure: vi.fn().mockResolvedValue({
            success: true,
            config: {
              mode: 'monitoring',
              interval: 30,
              autoFix: false,
              alertThreshold: 90,
              databases: [],
              enabledCapabilities: ['Performance Monitoring', 'Deadlock Detection']
            }
          }),
          saveConfig: vi.fn()
        };
        vi.mocked(ADAAgent).mockImplementation(() => mockAgent as any);

        await adaConfigure({
          interactive: true
        });

        expect(inquirer.default.prompt).toHaveBeenCalled();
        expect(mockAgent.configure).toHaveBeenCalled();
      });

      it('should configure specific databases', async () => {
        const mockAgent = {
          initialize: vi.fn(),
          configure: vi.fn().mockResolvedValue({
            success: true,
            config: {
              mode: 'full',
              interval: 60,
              autoFix: true,
              alertThreshold: 80,
              databases: ['prod', 'staging']
            }
          }),
          saveConfig: vi.fn()
        };
        vi.mocked(ADAAgent).mockImplementation(() => mockAgent as any);

        await adaConfigure({
          databases: 'prod,staging'
        });

        expect(mockAgent.configure).toHaveBeenCalledWith(
          expect.objectContaining({
            databases: ['prod', 'staging']
          })
        );
      });

      it('should handle configuration failure', async () => {
        const mockAgent = {
          initialize: vi.fn(),
          configure: vi.fn().mockResolvedValue({
            success: false,
            error: 'Invalid configuration'
          }),
          saveConfig: vi.fn()
        };
        vi.mocked(ADAAgent).mockImplementation(() => mockAgent as any);

        await expect(adaConfigure({
          interval: -1
        })).rejects.toThrow();
      });
    });
  });
});
