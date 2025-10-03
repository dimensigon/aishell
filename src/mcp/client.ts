/**
 * MCP Client Implementation
 * Manages connections to MCP servers with automatic reconnection and error handling
 */

import { EventEmitter } from 'eventemitter3';
import { spawn, ChildProcess } from 'child_process';
import {
  IMCPClient,
  MCPClientConfig,
  MCPServerConfig,
  ConnectionState,
  MCPMessage,
  MCPRequest,
  MCPResponse,
  MCPTool,
  MCPResource,
  MCPContext,
  MCPClientEvents,
  RequestOptions,
  ReconnectionOptions
} from './types';
import { MCPMessageBuilder } from './messages';

/**
 * Server Connection Manager
 */
class ServerConnection {
  private process: ChildProcess | null = null;
  private state: ConnectionState = ConnectionState.DISCONNECTED;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private pendingRequests = new Map<string | number, {
    resolve: (value: unknown) => void;
    reject: (error: Error) => void;
    timeout: NodeJS.Timeout;
  }>();

  constructor(
    private config: MCPServerConfig,
    private emitter: EventEmitter<MCPClientEvents>
  ) {}

  /**
   * Get current connection state
   */
  getState(): ConnectionState {
    return this.state;
  }

  /**
   * Connect to MCP server
   */
  async connect(): Promise<void> {
    if (this.state === ConnectionState.CONNECTED) {
      return;
    }

    this.setState(ConnectionState.CONNECTING);

    try {
      await this.startProcess();
      await this.initialize();
      this.setState(ConnectionState.CONNECTED);
      this.reconnectAttempts = 0;
      this.emitter.emit('connected', this.config.name);
    } catch (error) {
      this.setState(ConnectionState.ERROR);
      throw error;
    }
  }

  /**
   * Disconnect from MCP server
   */
  async disconnect(): Promise<void> {
    if (this.state === ConnectionState.DISCONNECTED) {
      return;
    }

    // Clear reconnection timer
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    // Send shutdown notification
    if (this.process && this.state === ConnectionState.CONNECTED) {
      try {
        const shutdownMsg = MCPMessageBuilder.createShutdownNotification();
        await this.sendMessage(shutdownMsg);
      } catch (error) {
        // Ignore errors during shutdown
      }
    }

    // Kill process
    if (this.process) {
      this.process.kill();
      this.process = null;
    }

    // Reject all pending requests
    this.pendingRequests.forEach(({ reject, timeout }) => {
      clearTimeout(timeout);
      reject(new Error('Connection closed'));
    });
    this.pendingRequests.clear();

    this.setState(ConnectionState.DISCONNECTED);
    this.emitter.emit('disconnected', this.config.name);
  }

  /**
   * Send request and wait for response
   */
  async request(method: string, params?: unknown, options?: RequestOptions): Promise<unknown> {
    if (this.state !== ConnectionState.CONNECTED) {
      throw new Error(`Cannot send request: connection state is ${this.state}`);
    }

    const request = MCPMessageBuilder.createRequest(method, params);
    const timeout = options?.timeout || 30000;

    return new Promise((resolve, reject) => {
      const timeoutHandle = setTimeout(() => {
        this.pendingRequests.delete(request.id!);
        reject(new Error(`Request timeout after ${timeout}ms`));
      }, timeout);

      this.pendingRequests.set(request.id!, {
        resolve,
        reject,
        timeout: timeoutHandle
      });

      this.sendMessage(request).catch((error) => {
        this.pendingRequests.delete(request.id!);
        clearTimeout(timeoutHandle);
        reject(error);
      });
    });
  }

  /**
   * Send notification (no response expected)
   */
  async notify(method: string, params?: unknown): Promise<void> {
    if (this.state !== ConnectionState.CONNECTED) {
      throw new Error(`Cannot send notification: connection state is ${this.state}`);
    }

    const notification = MCPMessageBuilder.createNotification(method, params);
    await this.sendMessage(notification);
  }

  /**
   * Start MCP server process
   */
  private async startProcess(): Promise<void> {
    return new Promise((resolve, reject) => {
      const env = {
        ...process.env,
        ...(this.config.env || {})
      };

      this.process = spawn(this.config.command, this.config.args, {
        env,
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let buffer = '';

      this.process.stdout?.on('data', (data) => {
        buffer += data.toString();
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        lines.forEach((line) => {
          if (line.trim()) {
            try {
              const message = MCPMessageBuilder.parseMessage(line);
              this.handleMessage(message);
            } catch (error) {
              console.error(`Failed to parse message: ${error}`);
            }
          }
        });
      });

      this.process.stderr?.on('data', (data) => {
        console.error(`[${this.config.name}] ${data.toString()}`);
      });

      this.process.on('error', (error) => {
        this.handleError(error);
        reject(error);
      });

      this.process.on('exit', (code) => {
        if (this.state === ConnectionState.CONNECTING) {
          reject(new Error(`Process exited with code ${code} during connection`));
        } else if (this.state === ConnectionState.CONNECTED) {
          this.handleDisconnection();
        }
      });

      // Resolve after process starts
      setTimeout(() => resolve(), 100);
    });
  }

  /**
   * Initialize MCP connection
   */
  private async initialize(): Promise<void> {
    const initRequest = MCPMessageBuilder.createInitializeRequest({
      name: 'ai-shell',
      version: '1.0.0'
    });

    const response = await this.request(initRequest.method!, initRequest.params);

    // Send initialized notification
    const initializedNotification = MCPMessageBuilder.createNotification('initialized');
    await this.sendMessage(initializedNotification);
  }

  /**
   * Send message to server
   */
  private async sendMessage(message: MCPMessage): Promise<void> {
    if (!this.process || !this.process.stdin) {
      throw new Error('Process not available');
    }

    const json = MCPMessageBuilder.serializeMessage(message);
    return new Promise((resolve, reject) => {
      this.process!.stdin!.write(json + '\n', (error) => {
        if (error) {
          reject(error);
        } else {
          resolve();
        }
      });
    });
  }

  /**
   * Handle incoming message
   */
  private handleMessage(message: MCPMessage): void {
    this.emitter.emit('message', this.config.name, message);

    if (MCPMessageBuilder.isResponse(message)) {
      const response = message as MCPResponse;
      const pending = this.pendingRequests.get(response.id);

      if (pending) {
        clearTimeout(pending.timeout);
        this.pendingRequests.delete(response.id);

        if (response.error) {
          pending.reject(new Error(response.error.message));
        } else {
          pending.resolve(response.result);
        }
      }
    }
  }

  /**
   * Handle connection error
   */
  private handleError(error: Error): void {
    this.emitter.emit('error', this.config.name, error);
    this.setState(ConnectionState.ERROR);
  }

  /**
   * Handle disconnection with reconnection logic
   */
  private handleDisconnection(error?: Error): void {
    this.emitter.emit('disconnected', this.config.name, error);
    this.setState(ConnectionState.DISCONNECTED);

    // Attempt reconnection if enabled
    const reconnectConfig = this.config.reconnect;
    if (reconnectConfig?.enabled && this.reconnectAttempts < reconnectConfig.maxAttempts) {
      this.attemptReconnection();
    }
  }

  /**
   * Attempt reconnection with exponential backoff
   */
  private attemptReconnection(): void {
    const reconnectConfig = this.config.reconnect!;
    this.reconnectAttempts++;

    const delay = reconnectConfig.delayMs *
      Math.pow(reconnectConfig.backoffMultiplier, this.reconnectAttempts - 1);

    this.setState(ConnectionState.RECONNECTING);
    this.emitter.emit('reconnecting', this.config.name, this.reconnectAttempts);

    this.reconnectTimer = setTimeout(() => {
      this.connect().catch((error) => {
        console.error(`Reconnection attempt ${this.reconnectAttempts} failed:`, error);
      });
    }, delay);
  }

  /**
   * Set connection state
   */
  private setState(state: ConnectionState): void {
    if (this.state !== state) {
      this.state = state;
      this.emitter.emit('stateChange', this.config.name, state);
    }
  }
}

/**
 * MCP Client
 */
export class MCPClient extends EventEmitter<MCPClientEvents> implements IMCPClient {
  private connections = new Map<string, ServerConnection>();
  private context: MCPContext | null = null;
  private contextSyncInterval: NodeJS.Timeout | null = null;

  constructor(private config: MCPClientConfig) {
    super();
    this.initializeConnections();
  }

  /**
   * Initialize server connections
   */
  private initializeConnections(): void {
    this.config.servers.forEach((serverConfig) => {
      const connection = new ServerConnection(serverConfig, this);
      this.connections.set(serverConfig.name, connection);
    });
  }

  /**
   * Connect to MCP server(s)
   */
  async connect(serverName?: string): Promise<void> {
    if (serverName) {
      const connection = this.connections.get(serverName);
      if (!connection) {
        throw new Error(`Server not found: ${serverName}`);
      }
      await connection.connect();
    } else {
      // Connect to all servers
      await Promise.all(
        Array.from(this.connections.values()).map((conn) => conn.connect())
      );
    }

    // Start context synchronization
    if (this.config.contextSyncInterval && !this.contextSyncInterval) {
      this.startContextSync();
    }
  }

  /**
   * Disconnect from MCP server(s)
   */
  async disconnect(serverName?: string): Promise<void> {
    if (this.contextSyncInterval) {
      clearInterval(this.contextSyncInterval);
      this.contextSyncInterval = null;
    }

    if (serverName) {
      const connection = this.connections.get(serverName);
      if (connection) {
        await connection.disconnect();
      }
    } else {
      await Promise.all(
        Array.from(this.connections.values()).map((conn) => conn.disconnect())
      );
    }
  }

  /**
   * Send request to server
   */
  async request(
    serverName: string,
    method: string,
    params?: unknown,
    options?: RequestOptions
  ): Promise<unknown> {
    const connection = this.connections.get(serverName);
    if (!connection) {
      throw new Error(`Server not found: ${serverName}`);
    }

    return connection.request(method, params, options);
  }

  /**
   * Send notification to server
   */
  async notify(serverName: string, method: string, params?: unknown): Promise<void> {
    const connection = this.connections.get(serverName);
    if (!connection) {
      throw new Error(`Server not found: ${serverName}`);
    }

    return connection.notify(method, params);
  }

  /**
   * Get connection state
   */
  getConnectionState(serverName: string): ConnectionState {
    const connection = this.connections.get(serverName);
    if (!connection) {
      return ConnectionState.DISCONNECTED;
    }
    return connection.getState();
  }

  /**
   * List available tools
   */
  async listTools(serverName?: string): Promise<MCPTool[]> {
    const servers = serverName
      ? [serverName]
      : Array.from(this.connections.keys());

    const toolLists = await Promise.all(
      servers.map(async (name) => {
        try {
          const result = await this.request(name, 'tools/list');
          return (result as { tools: MCPTool[] }).tools || [];
        } catch (error) {
          console.error(`Failed to list tools from ${name}:`, error);
          return [];
        }
      })
    );

    return toolLists.flat();
  }

  /**
   * List available resources
   */
  async listResources(serverName?: string): Promise<MCPResource[]> {
    const servers = serverName
      ? [serverName]
      : Array.from(this.connections.keys());

    const resourceLists = await Promise.all(
      servers.map(async (name) => {
        try {
          const result = await this.request(name, 'resources/list');
          return (result as { resources: MCPResource[] }).resources || [];
        } catch (error) {
          console.error(`Failed to list resources from ${name}:`, error);
          return [];
        }
      })
    );

    return resourceLists.flat();
  }

  /**
   * Synchronize context across all servers
   */
  async syncContext(context: MCPContext): Promise<void> {
    this.context = context;

    const syncPromises = Array.from(this.connections.entries()).map(
      async ([name, connection]) => {
        if (connection.getState() === ConnectionState.CONNECTED) {
          try {
            await connection.notify('context/update', { context });
          } catch (error) {
            console.error(`Failed to sync context to ${name}:`, error);
          }
        }
      }
    );

    await Promise.all(syncPromises);
    this.emit('contextSync', context);
  }

  /**
   * Start automatic context synchronization
   */
  private startContextSync(): void {
    this.contextSyncInterval = setInterval(async () => {
      if (this.context) {
        await this.syncContext({
          ...this.context,
          timestamp: Date.now()
        });
      }
    }, this.config.contextSyncInterval!);
  }

  /**
   * Get all connected servers
   */
  getConnectedServers(): string[] {
    return Array.from(this.connections.entries())
      .filter(([_, conn]) => conn.getState() === ConnectionState.CONNECTED)
      .map(([name]) => name);
  }

  /**
   * Get server configuration
   */
  getServerConfig(serverName: string): MCPServerConfig | undefined {
    return this.config.servers.find((s) => s.name === serverName);
  }
}
