/**
 * Unit Tests for MCP Server Discovery
 */

import { MCPServerDiscovery, DiscoveredServer, ServerCapabilities, DiscoveryConfig } from '../../src/mcp/discovery';
import { ConnectionState } from '../../src/mcp/types';
import * as dgram from 'dgram';
import { EventEmitter } from 'events';

// Mock dgram
jest.mock('dgram');

describe('MCPServerDiscovery', () => {
  let discovery: MCPServerDiscovery;
  let mockSocket: any;

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();

    // Create mock socket
    mockSocket = new EventEmitter();
    mockSocket.bind = jest.fn((port: number, callback: () => void) => {
      setTimeout(callback, 0);
    });
    mockSocket.send = jest.fn((buffer: Buffer, offset: number, length: number, port: number, address: string, callback: (error?: Error) => void) => {
      setTimeout(() => callback(), 0);
    });
    mockSocket.close = jest.fn((callback: () => void) => {
      setTimeout(callback, 0);
    });
    mockSocket.addMembership = jest.fn();
    mockSocket.setMulticastTTL = jest.fn();
    mockSocket.setMulticastLoopback = jest.fn();

    (dgram.createSocket as jest.Mock).mockReturnValue(mockSocket);
  });

  afterEach(async () => {
    if (discovery) {
      await discovery.stop();
    }
  });

  describe('Construction', () => {
    it('should create discovery instance with default config', () => {
      discovery = new MCPServerDiscovery();
      expect(discovery).toBeInstanceOf(MCPServerDiscovery);
    });

    it('should create discovery instance with custom config', () => {
      const config: DiscoveryConfig = {
        multicastAddress: '239.1.1.1',
        port: 4000,
        discoveryInterval: 10000,
        timeout: 30000,
        autoConnect: false
      };

      discovery = new MCPServerDiscovery(config);
      expect(discovery).toBeInstanceOf(MCPServerDiscovery);
    });
  });

  describe('Start and Stop', () => {
    it('should start discovery successfully', async () => {
      discovery = new MCPServerDiscovery();

      const startedHandler = jest.fn();
      discovery.on('discoveryStarted', startedHandler);

      await discovery.start();

      expect(mockSocket.bind).toHaveBeenCalled();
      expect(mockSocket.addMembership).toHaveBeenCalled();
      expect(startedHandler).toHaveBeenCalled();
    });

    it('should throw error if starting when already running', async () => {
      discovery = new MCPServerDiscovery();
      await discovery.start();

      await expect(discovery.start()).rejects.toThrow('Discovery already running');
    });

    it('should stop discovery successfully', async () => {
      discovery = new MCPServerDiscovery();
      await discovery.start();

      const stoppedHandler = jest.fn();
      discovery.on('discoveryStopped', stoppedHandler);

      await discovery.stop();

      expect(mockSocket.close).toHaveBeenCalled();
      expect(stoppedHandler).toHaveBeenCalled();
    });

    it('should handle stop when not running', async () => {
      discovery = new MCPServerDiscovery();
      await expect(discovery.stop()).resolves.not.toThrow();
    });

    it('should retry on failure when retryOnFailure is enabled', async () => {
      const config: DiscoveryConfig = {
        retryOnFailure: true,
        maxRetries: 2
      };

      discovery = new MCPServerDiscovery(config);

      // Make first attempt fail
      mockSocket.bind = jest.fn((port: number, callback: () => void) => {
        setTimeout(() => mockSocket.emit('error', new Error('Bind failed')), 0);
      });

      const errorHandler = jest.fn();
      discovery.on('discoveryError', errorHandler);

      await expect(discovery.start()).rejects.toThrow();
      expect(errorHandler).toHaveBeenCalled();
    });
  });

  describe('Server Discovery', () => {
    beforeEach(async () => {
      discovery = new MCPServerDiscovery({ autoConnect: false });
      await discovery.start();
    });

    it('should discover and register new server', (done) => {
      const testServer: DiscoveredServer = {
        id: 'test-server-1',
        name: 'Test Server',
        host: '192.168.1.100',
        port: 8080,
        protocol: 'websocket',
        capabilities: {
          tools: ['query', 'execute'],
          version: '1.0.0'
        },
        discoveredAt: Date.now(),
        lastSeenAt: Date.now()
      };

      discovery.on('serverDiscovered', (server) => {
        expect(server.id).toBe(testServer.id);
        expect(server.name).toBe(testServer.name);
        expect(server.host).toBe('192.168.1.100');
        done();
      });

      // Simulate incoming discovery message
      const message = {
        type: 'ANNOUNCE',
        serverId: testServer.id,
        serverName: testServer.name,
        host: testServer.host,
        port: testServer.port,
        protocol: testServer.protocol,
        capabilities: testServer.capabilities,
        timestamp: Date.now()
      };

      mockSocket.emit('message', Buffer.from(JSON.stringify(message)), {
        address: '192.168.1.100',
        port: 8080
      });
    });

    it('should update existing server', (done) => {
      const serverId = 'test-server-1';
      let updateCount = 0;

      discovery.on('serverDiscovered', () => {
        updateCount++;
      });

      discovery.on('serverUpdated', (server) => {
        expect(server.id).toBe(serverId);
        expect(updateCount).toBe(1);
        done();
      });

      // First discovery
      const message1 = {
        type: 'ANNOUNCE',
        serverId,
        serverName: 'Test Server',
        host: '192.168.1.100',
        port: 8080,
        protocol: 'websocket' as const,
        capabilities: { tools: ['query'] },
        timestamp: Date.now()
      };

      mockSocket.emit('message', Buffer.from(JSON.stringify(message1)), {
        address: '192.168.1.100',
        port: 8080
      });

      // Wait a bit, then send update
      setTimeout(() => {
        const message2 = {
          ...message1,
          capabilities: { tools: ['query', 'execute'] },
          timestamp: Date.now()
        };

        mockSocket.emit('message', Buffer.from(JSON.stringify(message2)), {
          address: '192.168.1.100',
          port: 8080
        });
      }, 100);
    });

    it('should handle server goodbye message', (done) => {
      const serverId = 'test-server-1';

      discovery.on('serverDiscovered', () => {
        // Send goodbye
        const goodbyeMessage = {
          type: 'GOODBYE',
          serverId,
          serverName: 'Test Server',
          host: '192.168.1.100',
          port: 8080,
          protocol: 'websocket' as const,
          capabilities: {},
          timestamp: Date.now()
        };

        mockSocket.emit('message', Buffer.from(JSON.stringify(goodbyeMessage)), {
          address: '192.168.1.100',
          port: 8080
        });
      });

      discovery.on('serverLost', (lostServerId) => {
        expect(lostServerId).toBe(serverId);
        done();
      });

      // Announce server
      const announceMessage = {
        type: 'ANNOUNCE',
        serverId,
        serverName: 'Test Server',
        host: '192.168.1.100',
        port: 8080,
        protocol: 'websocket' as const,
        capabilities: { tools: ['query'] },
        timestamp: Date.now()
      };

      mockSocket.emit('message', Buffer.from(JSON.stringify(announceMessage)), {
        address: '192.168.1.100',
        port: 8080
      });
    });

    it('should ignore invalid messages', () => {
      const errorHandler = jest.fn();
      discovery.on('discoveryError', errorHandler);

      // Invalid JSON
      mockSocket.emit('message', Buffer.from('invalid json'), {
        address: '192.168.1.100',
        port: 8080
      });

      // Missing required fields
      mockSocket.emit('message', Buffer.from(JSON.stringify({ type: 'ANNOUNCE' })), {
        address: '192.168.1.100',
        port: 8080
      });

      expect(errorHandler).not.toHaveBeenCalled();
    });

    it('should ignore messages from self', () => {
      const discoveredHandler = jest.fn();
      discovery.on('serverDiscovered', discoveredHandler);

      const message = {
        type: 'ANNOUNCE',
        serverId: 'client',
        serverName: 'ai-shell-client',
        host: '0.0.0.0',
        port: 0,
        protocol: 'stdio' as const,
        capabilities: {},
        timestamp: Date.now()
      };

      mockSocket.emit('message', Buffer.from(JSON.stringify(message)), {
        address: '127.0.0.1',
        port: 3749
      });

      expect(discoveredHandler).not.toHaveBeenCalled();
    });
  });

  describe('Server Registry', () => {
    beforeEach(async () => {
      discovery = new MCPServerDiscovery({ autoConnect: false });
      await discovery.start();
    });

    it('should return all discovered servers', (done) => {
      const message = {
        type: 'ANNOUNCE',
        serverId: 'test-server-1',
        serverName: 'Test Server',
        host: '192.168.1.100',
        port: 8080,
        protocol: 'websocket' as const,
        capabilities: { tools: ['query'] },
        timestamp: Date.now()
      };

      discovery.on('serverDiscovered', () => {
        const servers = discovery.getDiscoveredServers();
        expect(servers).toHaveLength(1);
        expect(servers[0].id).toBe('test-server-1');
        done();
      });

      mockSocket.emit('message', Buffer.from(JSON.stringify(message)), {
        address: '192.168.1.100',
        port: 8080
      });
    });

    it('should get server by ID', (done) => {
      const serverId = 'test-server-1';
      const message = {
        type: 'ANNOUNCE',
        serverId,
        serverName: 'Test Server',
        host: '192.168.1.100',
        port: 8080,
        protocol: 'websocket' as const,
        capabilities: { tools: ['query'] },
        timestamp: Date.now()
      };

      discovery.on('serverDiscovered', () => {
        const server = discovery.getServer(serverId);
        expect(server).toBeDefined();
        expect(server?.id).toBe(serverId);
        done();
      });

      mockSocket.emit('message', Buffer.from(JSON.stringify(message)), {
        address: '192.168.1.100',
        port: 8080
      });
    });

    it('should return undefined for non-existent server', () => {
      const server = discovery.getServer('non-existent');
      expect(server).toBeUndefined();
    });

    it('should get servers by capability', (done) => {
      const messages = [
        {
          type: 'ANNOUNCE',
          serverId: 'server-1',
          serverName: 'Server 1',
          host: '192.168.1.100',
          port: 8080,
          protocol: 'websocket' as const,
          capabilities: { tools: ['query', 'execute'] },
          timestamp: Date.now()
        },
        {
          type: 'ANNOUNCE',
          serverId: 'server-2',
          serverName: 'Server 2',
          host: '192.168.1.101',
          port: 8081,
          protocol: 'websocket' as const,
          capabilities: { tools: ['analyze'] },
          timestamp: Date.now()
        }
      ];

      let discoveredCount = 0;
      discovery.on('serverDiscovered', () => {
        discoveredCount++;
        if (discoveredCount === 2) {
          const serversWithQuery = discovery.getServersByCapability('query');
          expect(serversWithQuery).toHaveLength(1);
          expect(serversWithQuery[0].id).toBe('server-1');
          done();
        }
      });

      messages.forEach((msg, i) => {
        mockSocket.emit('message', Buffer.from(JSON.stringify(msg)), {
          address: msg.host,
          port: msg.port
        });
      });
    });

    it('should remove server from registry', (done) => {
      const serverId = 'test-server-1';
      const message = {
        type: 'ANNOUNCE',
        serverId,
        serverName: 'Test Server',
        host: '192.168.1.100',
        port: 8080,
        protocol: 'websocket' as const,
        capabilities: { tools: ['query'] },
        timestamp: Date.now()
      };

      discovery.on('serverDiscovered', () => {
        discovery.removeServer(serverId);
        const server = discovery.getServer(serverId);
        expect(server).toBeUndefined();
        done();
      });

      mockSocket.emit('message', Buffer.from(JSON.stringify(message)), {
        address: '192.168.1.100',
        port: 8080
      });
    });
  });

  describe('Scanning', () => {
    beforeEach(async () => {
      discovery = new MCPServerDiscovery({ autoConnect: false });
      await discovery.start();
    });

    it('should perform manual scan', async () => {
      const scanPromise = discovery.scan();

      // Simulate server response during scan
      setTimeout(() => {
        const message = {
          type: 'RESPONSE',
          serverId: 'test-server-1',
          serverName: 'Test Server',
          host: '192.168.1.100',
          port: 8080,
          protocol: 'websocket' as const,
          capabilities: { tools: ['query'] },
          timestamp: Date.now()
        };

        mockSocket.emit('message', Buffer.from(JSON.stringify(message)), {
          address: '192.168.1.100',
          port: 8080
        });
      }, 100);

      const servers = await scanPromise;
      expect(Array.isArray(servers)).toBe(true);
    });

    it('should throw error when scanning without starting', async () => {
      const newDiscovery = new MCPServerDiscovery();
      await expect(newDiscovery.scan()).rejects.toThrow('Discovery not running');
    });
  });

  describe('Connection State', () => {
    beforeEach(async () => {
      discovery = new MCPServerDiscovery({ autoConnect: false });
      await discovery.start();
    });

    it('should return DISCONNECTED for unknown server', () => {
      const state = discovery.getConnectionState('unknown-server');
      expect(state).toBe(ConnectionState.DISCONNECTED);
    });

    it('should track connection state', (done) => {
      const serverId = 'test-server-1';
      const message = {
        type: 'ANNOUNCE',
        serverId,
        serverName: 'Test Server',
        host: '192.168.1.100',
        port: 8080,
        protocol: 'websocket' as const,
        capabilities: { tools: ['query'] },
        timestamp: Date.now()
      };

      discovery.on('serverDiscovered', () => {
        const state = discovery.getConnectionState(serverId);
        expect(state).toBe(ConnectionState.DISCONNECTED);
        done();
      });

      mockSocket.emit('message', Buffer.from(JSON.stringify(message)), {
        address: '192.168.1.100',
        port: 8080
      });
    });
  });

  describe('Statistics', () => {
    beforeEach(async () => {
      discovery = new MCPServerDiscovery({ autoConnect: false });
      await discovery.start();
    });

    it('should return correct statistics', (done) => {
      const messages = [
        {
          type: 'ANNOUNCE',
          serverId: 'server-1',
          serverName: 'Server 1',
          host: '192.168.1.100',
          port: 8080,
          protocol: 'websocket' as const,
          capabilities: { tools: ['query'] },
          timestamp: Date.now()
        },
        {
          type: 'ANNOUNCE',
          serverId: 'server-2',
          serverName: 'Server 2',
          host: '192.168.1.101',
          port: 8081,
          protocol: 'websocket' as const,
          capabilities: { tools: ['analyze'] },
          timestamp: Date.now()
        }
      ];

      let discoveredCount = 0;
      discovery.on('serverDiscovered', () => {
        discoveredCount++;
        if (discoveredCount === 2) {
          const stats = discovery.getStatistics();
          expect(stats.totalServers).toBe(2);
          expect(stats.disconnectedServers).toBe(2);
          expect(stats.connectedServers).toBe(0);
          done();
        }
      });

      messages.forEach((msg) => {
        mockSocket.emit('message', Buffer.from(JSON.stringify(msg)), {
          address: msg.host,
          port: msg.port
        });
      });
    });

    it('should return zero statistics when no servers discovered', () => {
      const stats = discovery.getStatistics();
      expect(stats.totalServers).toBe(0);
      expect(stats.connectedServers).toBe(0);
      expect(stats.disconnectedServers).toBe(0);
      expect(stats.errorServers).toBe(0);
    });
  });

  describe('Capability Filtering', () => {
    it('should filter servers by capability', (done) => {
      discovery = new MCPServerDiscovery({
        autoConnect: false,
        capabilityFilter: ['execute']
      });

      discovery.start().then(() => {
        const discoveredHandler = jest.fn();
        discovery.on('serverDiscovered', discoveredHandler);

        // Server without filtered capability
        const message1 = {
          type: 'ANNOUNCE',
          serverId: 'server-1',
          serverName: 'Server 1',
          host: '192.168.1.100',
          port: 8080,
          protocol: 'websocket' as const,
          capabilities: { tools: ['query'] },
          timestamp: Date.now()
        };

        // Server with filtered capability
        const message2 = {
          type: 'ANNOUNCE',
          serverId: 'server-2',
          serverName: 'Server 2',
          host: '192.168.1.101',
          port: 8081,
          protocol: 'websocket' as const,
          capabilities: { tools: ['execute'] },
          timestamp: Date.now()
        };

        mockSocket.emit('message', Buffer.from(JSON.stringify(message1)), {
          address: '192.168.1.100',
          port: 8080
        });

        mockSocket.emit('message', Buffer.from(JSON.stringify(message2)), {
          address: '192.168.1.101',
          port: 8081
        });

        setTimeout(() => {
          expect(discoveredHandler).toHaveBeenCalledTimes(1);
          const servers = discovery.getDiscoveredServers();
          expect(servers).toHaveLength(1);
          expect(servers[0].id).toBe('server-2');
          done();
        }, 100);
      });
    });
  });
});
