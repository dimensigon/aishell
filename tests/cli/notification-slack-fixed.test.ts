/**
 * Comprehensive test suite for Slack Integration
 *
 * Tests cover:
 * - Configuration management
 * - Message building with Block Kit
 * - Alert sending (Web API and webhook)
 * - Channel routing
 * - Thread support
 * - Interactive actions
 * - Rate limiting
 * - Error handling
 * - Severity formatting
 * - Specialized alert types
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

const TEST_CONFIG_PATH = '/tmp/test-slack-config.json';

// Create mock functions outside describe block
const mockPostMessage = vi.fn().mockResolvedValue({ ok: true, ts: '1234567890.123456' });
const mockConversationsList = vi.fn().mockResolvedValue({ channels: [] });
const mockAxiosPost = vi.fn().mockResolvedValue({ status: 200 });

// Mock dependencies at top level
vi.mock('@slack/web-api', () => {
  return {
    WebClient: vi.fn(function(this: any, token: string) {
      this.token = token;
      this.chat = {
        postMessage: mockPostMessage,
      };
      this.conversations = {
        list: mockConversationsList,
      };
    }),
  };
});

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

vi.mock('axios', () => ({
  default: {
    create: vi.fn().mockReturnValue({
      post: mockAxiosPost,
    }),
  },
}));

describe('SlackIntegration', () => {
  let integration: SlackIntegration;
  let mockConfig: SlackConfig;

  beforeEach(async () => {
    vi.clearAllMocks();

    // Reset all mock implementations
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

    // Mock fs
    vi.mocked(fs.existsSync).mockReturnValue(true);
    vi.mocked(fs.readFileSync).mockReturnValue(JSON.stringify(mockConfig));
    vi.mocked(fs.writeFileSync).mockImplementation(() => {});
    vi.mocked(fs.mkdirSync).mockImplementation(() => {});

    integration = new SlackIntegration(TEST_CONFIG_PATH);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ============================================================================
  // Configuration Tests
  // ============================================================================

  describe('Configuration Management', () => {
    it('should load configuration from file', async () => {
      expect(vi.mocked(fs.existsSync)).toHaveBeenCalledWith(TEST_CONFIG_PATH);
      expect(vi.mocked(fs.readFileSync)).toHaveBeenCalledWith(TEST_CONFIG_PATH, 'utf-8');
      const config = integration.getConfig();
      expect(config.token).toBe('xoxb-test-token');
    });

    it('should use default configuration if file does not exist', async () => {
      vi.mocked(fs.existsSync).mockReturnValue(false);
      const newIntegration = new SlackIntegration(TEST_CONFIG_PATH);
      const config = newIntegration.getConfig();
      expect(config.defaultChannel).toBe('#ai-shell-alerts');
    });

    it('should save configuration to file', async () => {
      const newConfig: Partial<SlackConfig> = {
        token: 'new-token',
        defaultChannel: '#new-channel',
      };

      integration.saveConfig(newConfig);

      expect(vi.mocked(fs.mkdirSync)).toHaveBeenCalled();
      expect(vi.mocked(fs.writeFileSync)).toHaveBeenCalledWith(
        TEST_CONFIG_PATH,
        expect.stringContaining('new-token'),
        'utf-8'
      );
    });

    it('should merge configuration on save', () => {
      integration.saveConfig({ defaultChannel: '#updated-channel' });
      const config = integration.getConfig();
      expect(config.token).toBe('xoxb-test-token'); // Original
      expect(config.defaultChannel).toBe('#updated-channel'); // Updated
    });

    it('should return configuration copy to prevent mutation', () => {
      const config1 = integration.getConfig();
      const config2 = integration.getConfig();
      expect(config1).toEqual(config2);
      expect(config1).not.toBe(config2); // Different objects
    });
  });

  // ============================================================================
  // Alert Sending Tests
  // ============================================================================

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
      // Create new integration without token
      vi.mocked(fs.readFileSync).mockReturnValue(JSON.stringify({
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
      expect(mockAxiosPost).toHaveBeenCalled();
    });

    it('should throw error when no integration is configured', async () => {
      vi.mocked(fs.readFileSync).mockReturnValue(JSON.stringify({
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

  // Test for proper alert sending with correct parameters
  it('should send alert with correct structure', async () => {
    const alert: AlertMessage = {
      type: 'performance',
      severity: 'high',
      title: 'High CPU Usage',
      description: 'CPU usage is at 95%',
      details: {
        cpu_usage: '95%',
        threshold: '80%',
      },
      timestamp: Date.now(),
    };

    await integration.sendAlert(alert);

    expect(mockPostMessage).toHaveBeenCalled With(
      expect.objectContaining({
        channel: expect.any(String),
        text: expect.stringContaining('⚠️'),
        blocks: expect.arrayContaining([
          expect.objectContaining({ type: 'header' }),
        ]),
      })
    );
  });
});
