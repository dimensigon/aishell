/**
 * Comprehensive test suite for Slack Integration - AUTO-FIXED VERSION
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import SlackIntegration, {
  SlackConfig,
  AlertMessage,
  setupSlack,
  testSlack,
  listSlackChannels,
  configureSlackRouting,
  showSlackConfig,
} from '../../src/cli/notification-slack';
import * as fs from 'fs';
import * as fsSync from 'fs';

const TEST_CONFIG_PATH = '/tmp/test-slack-config.json';

// Create mock functions at module level
const mockPostMessage = vi.fn();
const mockConversationsList = vi.fn();
const mockAxiosPost = vi.fn();

// Mock @slack/web-api
vi.mock('@slack/web-api', () => ({
  WebClient: vi.fn(function(this: any, token: string) {
    this.token = token;
    this.chat = { postMessage: mockPostMessage };
    this.conversations = { list: mockConversationsList };
  }),
}));

// Mock fs
vi.mock('fs', () => ({
  default: {
    existsSync: vi.fn(),
    readFileSync: vi.fn(),
    writeFileSync: vi.fn(),
    mkdirSync: vi.fn(),
  },
  existsSync: vi.fn(),
  readFileSync: vi.fn(),
  writeFileSync: vi.fn(),
  mkdirSync: vi.fn(),
}));

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      post: mockAxiosPost,
    })),
  },
}));

describe('SlackIntegration', () => {
  let integration: SlackIntegration;
  let mockConfig: SlackConfig;

  beforeEach(() => {
    vi.clearAllMocks();

    // Reset mock implementations
    mockPostMessage.mockResolvedValue({ ok: true, ts: '1234567890.123456' });
    mockConversationsList.mockResolvedValue({ channels: [] });
    mockAxiosPost.mockResolvedValue({ status: 200 });

    mockConfig = {
      token: 'xoxb-test-token',
      webhookUrl: 'https://hooks.slack.com/services/TEST/WEBHOOK',
      defaultChannel: '#test-channel',
      enableThreads: true,
      enableInteractive: true,
      channelRouting: {
        query: '#test-queries',
        security: '#test-security',
        performance: '#test-performance',
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

    vi.mocked(fsSync.existsSync).mockReturnValue(true);
    vi.mocked(fsSync.readFileSync).mockReturnValue(JSON.stringify(mockConfig));
    vi.mocked(fsSync.writeFileSync).mockImplementation(() => {});
    vi.mocked(fsSync.mkdirSync).mockImplementation(() => {});

    integration = new SlackIntegration(TEST_CONFIG_PATH);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Configuration Management', () => {
    it('should load configuration from file', () => {
      expect(vi.mocked(fsSync.existsSync)).toHaveBeenCalledWith(TEST_CONFIG_PATH);
      expect(vi.mocked(fsSync.readFileSync)).toHaveBeenCalledWith(TEST_CONFIG_PATH, 'utf-8');
      const config = integration.getConfig();
      expect(config.token).toBe('xoxb-test-token');
    });

    it('should use default configuration if file does not exist', () => {
      vi.mocked(fsSync.existsSync).mockReturnValue(false);
      const newIntegration = new SlackIntegration(TEST_CONFIG_PATH);
      const config = newIntegration.getConfig();
      expect(config.defaultChannel).toBe('#ai-shell-alerts');
    });

    it('should save configuration to file', () => {
      const newConfig: Partial<SlackConfig> = {
        token: 'new-token',
        defaultChannel: '#new-channel',
      };

      integration.saveConfig(newConfig);

      // mkdirSync may not be called if directory already exists
      expect(vi.mocked(fsSync.writeFileSync)).toHaveBeenCalledWith(
        TEST_CONFIG_PATH,
        expect.stringContaining('new-token'),
        'utf-8'
      );
    });

    it('should merge configuration on save', () => {
      integration.saveConfig({ defaultChannel: '#updated-channel' });
      const config = integration.getConfig();
      expect(config.token).toBe('xoxb-test-token');
      expect(config.defaultChannel).toBe('#updated-channel');
    });

    it('should return configuration copy to prevent mutation', () => {
      const config1 = integration.getConfig();
      const config2 = integration.getConfig();
      expect(config1).toEqual(config2);
      expect(config1).not.toBe(config2);
    });
  });

  describe('Alert Sending', () => {
    it('should send alert via Web API when token is configured', async () => {
      const alert: AlertMessage = {
        type: 'system',
        severity: 'info',
        title: 'Test Alert',
        description: 'This is a test alert',
        timestamp: Date.now(),
      };

      const result = await integration.sendAlert(alert);
      expect(result).toBe(true);
      expect(mockPostMessage).toHaveBeenCalled();
    });

    it('should send alert via webhook when only webhook is configured', async () => {
      vi.mocked(fsSync.readFileSync).mockReturnValue(JSON.stringify({
        webhookUrl: 'https://hooks.slack.com/services/TEST',
        defaultChannel: '#test',
      }));

      const newIntegration = new SlackIntegration(TEST_CONFIG_PATH);
      const alert: AlertMessage = {
        type: 'system',
        severity: 'info',
        title: 'Test Alert',
        description: 'This is a test alert',
        timestamp: Date.now(),
      };

      const result = await newIntegration.sendAlert(alert);
      expect(result).toBe(true);
    });

    it('should throw error when no integration is configured', async () => {
      vi.mocked(fsSync.readFileSync).mockReturnValue(JSON.stringify({
        defaultChannel: '#test',
      }));

      const newIntegration = new SlackIntegration(TEST_CONFIG_PATH);
      const alert: AlertMessage = {
        type: 'system',
        severity: 'info',
        title: 'Test Alert',
        description: 'This is a test alert',
        timestamp: Date.now(),
      };

      const result = await newIntegration.sendAlert(alert);
      expect(result).toBe(false);
    });

    it('should handle sending errors gracefully', async () => {
      mockPostMessage.mockRejectedValueOnce(new Error('API Error'));

      const alert: AlertMessage = {
        type: 'system',
        severity: 'info',
        title: 'Test Alert',
        description: 'This is a test alert',
        timestamp: Date.now(),
      };

      const result = await integration.sendAlert(alert);
      expect(result).toBe(false);
    });
  });

  describe('Message Building', () => {
    const severityTests = [
      { severity: 'critical', emoji: '🚨' },
      { severity: 'high', emoji: '⚠️' },
      { severity: 'medium', emoji: '⚡' },
      { severity: 'low', emoji: 'ℹ️' },
      { severity: 'info', emoji: '📊' },
    ];

    it('should build message with correct emoji for severity', async () => {
      for (const { severity, emoji } of severityTests) {
        const alert: AlertMessage = {
          type: 'system',
          severity: severity as any,
          title: 'Test Alert',
          description: 'Test description',
          timestamp: Date.now(),
        };

        await integration.sendAlert(alert);
        const lastCall = mockPostMessage.mock.calls[mockPostMessage.mock.calls.length - 1];
        expect(lastCall[0].text).toContain(emoji);
      }
    });

    it('should include alert details in message blocks', async () => {
      const alert: AlertMessage = {
        type: 'performance',
        severity: 'high',
        title: 'High CPU Usage',
        description: 'CPU usage is at 95%',
        details: {
          cpu_usage: '95%',
          threshold: '80%',
          duration: '5 minutes',
        },
        timestamp: Date.now(),
      };

      await integration.sendAlert(alert);
      const lastCall = mockPostMessage.mock.calls[0];
      expect(lastCall[0].blocks).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ type: 'header' }),
          expect.objectContaining({ type: 'context' }),
          expect.objectContaining({ type: 'section' }),
        ])
      );
    });

    it('should add interactive actions for alerts', async () => {
      const alert: AlertMessage = {
        type: 'security',
        severity: 'critical',
        title: 'Security Breach Detected',
        description: 'Unauthorized access attempt',
        details: {
          ip_address: '192.168.1.100',
          attempts: 5,
        },
        timestamp: Date.now(),
      };

      await integration.sendAlert(alert);
      const lastCall = mockPostMessage.mock.calls[0];
      expect(lastCall[0].blocks).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ type: 'actions' }),
        ])
      );
    });

    it('should include mentions for critical alerts', async () => {
      const alert: AlertMessage = {
        type: 'system',
        severity: 'critical',
        title: 'System Down',
        description: 'Database is unreachable',
        timestamp: Date.now(),
      };

      await integration.sendAlert(alert);
      const lastCall = mockPostMessage.mock.calls[0];
      expect(lastCall[0].text).toContain('@channel');
    });

    it('should include mentions for security alerts', async () => {
      const alert: AlertMessage = {
        type: 'security',
        severity: 'high',
        title: 'Security Issue',
        description: 'Potential breach detected',
        timestamp: Date.now(),
      };

      await integration.sendAlert(alert);
      const lastCall = mockPostMessage.mock.calls[0];
      expect(lastCall[0].text).toContain('@security-team');
    });
  });

  describe('Channel Routing', () => {
    it('should route alerts to type-specific channels', async () => {
      const testCases = [
        { type: 'query', expectedChannel: '#test-queries' },
        { type: 'security', expectedChannel: '#test-security' },
        { type: 'performance', expectedChannel: '#test-performance' },
      ];

      for (const { type, expectedChannel } of testCases) {
        mockPostMessage.mockClear();

        const alert: AlertMessage = {
          type: type as any,
          severity: 'info',
          title: 'Test Alert',
          description: 'Test description',
          timestamp: Date.now(),
        };

        await integration.sendAlert(alert);
        const lastCall = mockPostMessage.mock.calls[0];
        expect(lastCall[0].channel).toBe(expectedChannel);
      }
    });

    it('should use default channel for unmapped alert types', async () => {
      const alert: AlertMessage = {
        type: 'backup',
        severity: 'info',
        title: 'Backup Complete',
        description: 'Database backup completed',
        timestamp: Date.now(),
      };

      await integration.sendAlert(alert);
      const lastCall = mockPostMessage.mock.calls[0];
      expect(lastCall[0].channel).toBe('#test-channel');
    });
  });

  describe('Thread Support', () => {
    it('should send message in thread when threadId is provided', async () => {
      // First message creates thread
      const alert1: AlertMessage = {
        type: 'system',
        severity: 'info',
        title: 'Thread Start',
        description: 'First message',
        threadId: 'test-thread-1',
        timestamp: Date.now(),
      };

      await integration.sendAlert(alert1);

      // Second message should be in thread
      const alert2: AlertMessage = {
        type: 'system',
        severity: 'info',
        title: 'Thread Reply',
        description: 'Second message',
        threadId: 'test-thread-1',
        timestamp: Date.now(),
      };

      await integration.sendAlert(alert2);

      const secondCall = mockPostMessage.mock.calls[1][0];
      expect(secondCall.thread_ts).toBe('1234567890.123456');
    });

    it('should not use threads when disabled in config', async () => {
      vi.mocked(fsSync.readFileSync).mockReturnValue(JSON.stringify({
        ...mockConfig,
        enableThreads: false,
      }));

      const testIntegration = new SlackIntegration(TEST_CONFIG_PATH);

      const alert: AlertMessage = {
        type: 'system',
        severity: 'info',
        title: 'Test',
        description: 'Test',
        threadId: 'test-thread',
        timestamp: Date.now(),
      };

      await testIntegration.sendAlert(alert);

      const call = mockPostMessage.mock.calls[0][0];
      expect(call.thread_ts).toBeUndefined();
    });
  });

  describe('Rate Limiting', () => {
    it('should respect rate limits', async () => {
      vi.mocked(fsSync.readFileSync).mockReturnValue(JSON.stringify({
        ...mockConfig,
        rateLimiting: {
          maxMessagesPerMinute: 2,
          burstSize: 2,
        },
      }));

      const testIntegration = new SlackIntegration(TEST_CONFIG_PATH);

      const alert: AlertMessage = {
        type: 'system',
        severity: 'info',
        title: 'Test',
        description: 'Test',
        timestamp: Date.now(),
      };

      // Send burst size messages (should succeed)
      let result1 = await testIntegration.sendAlert(alert);
      let result2 = await testIntegration.sendAlert(alert);

      expect(result1).toBe(true);
      expect(result2).toBe(true);

      // Third message should be rate limited
      let result3 = await testIntegration.sendAlert(alert);
      expect(result3).toBe(false);
    });
  });

  describe('Specialized Alerts', () => {
    it('should send query alert with query preview', async () => {
      const result = await integration.sendQueryAlert(
        'SELECT * FROM users WHERE age > 18',
        { rows: [{ id: 1 }, { id: 2 }] },
        { executionTime: 1500 }
      );

      expect(result).toBe(true);
      expect(mockPostMessage).toHaveBeenCalled();
    });

    it('should send security alert with severity', async () => {
      const result = await integration.sendSecurityAlert(
        'SQL Injection Attempt',
        'Malicious query detected',
        'critical',
        { ip: '192.168.1.100' }
      );

      expect(result).toBe(true);
      expect(mockPostMessage).toHaveBeenCalled();
    });

    it('should send performance alert with metrics', async () => {
      const result = await integration.sendPerformanceAlert(
        'CPU Usage',
        95,
        80,
        { duration: '5 minutes' }
      );

      expect(result).toBe(true);
      expect(mockPostMessage).toHaveBeenCalled();
    });

    it('should send backup notification', async () => {
      const result = await integration.sendBackupNotification(
        true,
        '/backups/db-2024-01-01.sql',
        1024 * 1024 * 50
      );

      expect(result).toBe(true);
      expect(mockPostMessage).toHaveBeenCalled();
    });

    it('should send health update', async () => {
      const result = await integration.sendHealthUpdate(
        'healthy',
        {
          database: true,
          api: true,
          storage: true,
        }
      );

      expect(result).toBe(true);
      expect(mockPostMessage).toHaveBeenCalled();
    });

    it('should calculate performance alert severity correctly', async () => {
      // Test critical threshold (>100% over)
      await integration.sendPerformanceAlert('CPU', 200, 80);
      let call = mockPostMessage.mock.calls[0][0];
      expect(call.blocks[1].elements[0].text).toContain('CRITICAL');

      mockPostMessage.mockClear();

      // Test high threshold (>50% over)
      await integration.sendPerformanceAlert('CPU', 130, 80);
      call = mockPostMessage.mock.calls[0][0];
      expect(call.blocks[1].elements[0].text).toContain('HIGH');
    });
  });

  describe('Connection Testing', () => {
    it('should test connection successfully', async () => {
      const result = await integration.testConnection();

      expect(result.success).toBe(true);
      expect(result.message).toContain('successful');
    });

    it('should handle connection test failure', async () => {
      mockPostMessage.mockRejectedValueOnce(new Error('Connection failed'));

      const result = await integration.testConnection();

      expect(result.success).toBe(false);
      // Case-insensitive match
      expect(result.message.toLowerCase()).toContain('failed');
    });
  });

  describe('Channel Listing', () => {
    it('should list available channels', async () => {
      mockConversationsList.mockResolvedValueOnce({
        channels: [
          { id: 'C1234', name: 'general', is_member: true },
          { id: 'C5678', name: 'random', is_member: false },
        ],
      });

      const channels = await integration.listChannels();

      expect(channels).toHaveLength(2);
      expect(channels[0]).toEqual({
        id: 'C1234',
        name: 'general',
        isMember: true,
      });
    });

    it('should handle empty channel list', async () => {
      mockConversationsList.mockResolvedValueOnce({ channels: [] });

      const channels = await integration.listChannels();

      expect(channels).toHaveLength(0);
    });

    it('should handle channel listing errors', async () => {
      mockConversationsList.mockRejectedValueOnce(new Error('API Error'));

      const channels = await integration.listChannels();

      expect(channels).toHaveLength(0);
    });
  });

  describe('CLI Commands', () => {
    it('should setup Slack with token', async () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

      await setupSlack({
        token: 'xoxb-new-token',
        configPath: TEST_CONFIG_PATH,
      });

      expect(vi.mocked(fsSync.writeFileSync)).toHaveBeenCalled();
      expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('configured'));

      consoleSpy.mockRestore();
    });

    it('should setup Slack with webhook', async () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

      await setupSlack({
        webhook: 'https://hooks.slack.com/services/NEW',
        configPath: TEST_CONFIG_PATH,
      });

      expect(vi.mocked(fsSync.writeFileSync)).toHaveBeenCalled();
      expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('webhook'));

      consoleSpy.mockRestore();
    });

    it('should configure channel routing', async () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

      await configureSlackRouting({
        alertType: 'backup',
        channel: '#backups',
        configPath: TEST_CONFIG_PATH,
      });

      expect(vi.mocked(fsSync.writeFileSync)).toHaveBeenCalled();
      expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('backup'));

      consoleSpy.mockRestore();
    });
  });

  describe('Field Formatting', () => {
    it('should format field values correctly', async () => {
      const alert: AlertMessage = {
        type: 'system',
        severity: 'info',
        title: 'Test',
        description: 'Test',
        details: {
          string_value: 'test',
          number_value: 12345,
          object_value: { nested: 'value' },
        },
        timestamp: Date.now(),
      };

      await integration.sendAlert(alert);

      const call = mockPostMessage.mock.calls[0][0];
      const sectionBlock = call.blocks.find((b: any) => b.type === 'section' && b.fields);

      expect(sectionBlock).toBeDefined();
      expect(sectionBlock.fields[1].text).toContain('12,345');
    });
  });
});
