/**
 * MCP Client Implementation
 * Manages connections to MCP servers with automatic reconnection and error handling
 */

import { EventEmitter } from 'eventemitter3';
import { spawn, ChildProcess, SpawnOptions } from 'child_process';
import {
  IMCPClient,
  MCPClientConfig,
  MCPServerConfig,
  ConnectionState,
  MCPMessage,
  MCPResponse,
  MCPTool,
  MCPResource,
  MCPContext,
  MCPClientEvents,
  RequestOptions
} from './types';
import { MCPMessageBuilder } from './messages';
import { createLogger, securityLogger } from '../core/logger';

/**
 * Resource limits and monitoring for plugin processes
 */
interface ResourceMonitoring {
  startTime: number;
  cpuUsage: number;
  memoryUsage: number;
  lastCheck: number;
}

/**
 * Sandboxing configuration constants
 */
const SANDBOX_CONFIG = {
  MAX_BUFFER: 10 * 1024 * 1024, // 10MB output buffer limit
  PROCESS_TIMEOUT: 300000, // 5 minutes max runtime
  MEMORY_LIMIT: 512 * 1024 * 1024, // 512MB memory limit
  CPU_THRESHOLD: 80, // 80% CPU usage threshold
  MONITORING_INTERVAL: 5000, // Check resources every 5 seconds
  // Safe environment variables whitelist
  SAFE_ENV_VARS: [
    'PATH',
    'HOME',
    'USER',
    'NODE_ENV',
    'LANG',
    'LC_ALL',
    'TZ',
    'TMPDIR',
    'TEMP',
    'TMP'
  ]
} as const;

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
  private resourceMonitoring: ResourceMonitoring | null = null;
  private monitoringInterval: NodeJS.Timeout | null = null;
  private processTimeout: NodeJS.Timeout | null = null;
  private logger = createLogger('ServerConnection');

  constructor(
    private config: MCPServerConfig,
    private emitter: EventEmitter<MCPClientEvents>
  ) {
    this.logger = createLogger('ServerConnection', { server: config.name });
  }

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

    // Clear all timers
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }

    if (this.processTimeout) {
      clearTimeout(this.processTimeout);
      this.processTimeout = null;
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

    // Clear resource monitoring
    this.resourceMonitoring = null;

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
   * Create sandboxed spawn options with security restrictions
   */
  private createSandboxedSpawnOptions(): SpawnOptions {
    // Filter environment variables - only allow safe ones
    const safeEnv: Record<string, string> = {};

    // Add whitelisted system env vars
    SANDBOX_CONFIG.SAFE_ENV_VARS.forEach((key) => {
      if (process.env[key]) {
        safeEnv[key] = process.env[key]!;
      }
    });

    // Add plugin-specific env vars from config (but sanitize them)
    if (this.config.env) {
      Object.entries(this.config.env).forEach(([key, value]) => {
        // Prevent override of sensitive vars and only allow alphanumeric keys
        if (!/^[A-Z_][A-Z0-9_]*$/i.test(key)) {
          securityLogger.warn('Blocked invalid environment variable key', {
            key,
            server: this.config.name
          });
          return;
        }
        // Prevent passing secrets or tokens
        if (key.toLowerCase().includes('secret') ||
            key.toLowerCase().includes('token') ||
            key.toLowerCase().includes('password') ||
            key.toLowerCase().includes('key')) {
          securityLogger.warn('Blocked potentially sensitive environment variable', {
            key,
            server: this.config.name
          });
          return;
        }
        safeEnv[key] = value;
      });
    }

    const spawnOptions: SpawnOptions = {
      env: safeEnv,
      stdio: ['pipe', 'pipe', 'pipe'],
      detached: false, // Ensure process is in same group for cleanup
      shell: false, // Never use shell to prevent command injection
      windowsHide: true, // Hide console window on Windows
      timeout: SANDBOX_CONFIG.PROCESS_TIMEOUT,
    };

    // Add uid/gid isolation on Unix systems (if running as root)
    if (process.platform !== 'win32' && process.getuid && process.getgid) {
      const uid = process.getuid();

      // Only set if we're not already non-root
      if (uid === 0) {
        // Run as nobody user (typically uid 65534)
        spawnOptions.uid = 65534;
        spawnOptions.gid = 65534;
        securityLogger.info('Running plugin as nobody user', {
          server: this.config.name,
          uid: 65534,
          gid: 65534
        });
      }
    }

    return spawnOptions;
  }

  /**
   * Initialize resource monitoring for the plugin process
   */
  private initializeResourceMonitoring(): void {
    this.resourceMonitoring = {
      startTime: Date.now(),
      cpuUsage: 0,
      memoryUsage: 0,
      lastCheck: Date.now()
    };

    // Set up periodic resource monitoring
    this.monitoringInterval = setInterval(() => {
      this.checkResourceLimits();
    }, SANDBOX_CONFIG.MONITORING_INTERVAL);

    // Set up process timeout
    this.processTimeout = setTimeout(() => {
      securityLogger.error('Plugin exceeded max runtime', {
        server: this.config.name,
        maxRuntime: SANDBOX_CONFIG.PROCESS_TIMEOUT
      });
      this.terminateProcess('timeout');
    }, SANDBOX_CONFIG.PROCESS_TIMEOUT);

    this.logger.debug('Resource monitoring initialized', {
      server: this.config.name,
      maxRuntime: SANDBOX_CONFIG.PROCESS_TIMEOUT,
      monitoringInterval: SANDBOX_CONFIG.MONITORING_INTERVAL
    });
  }

  /**
   * Check and enforce resource limits
   */
  private checkResourceLimits(): void {
    if (!this.process || !this.process.pid || !this.resourceMonitoring) {
      return;
    }

    try {
      // On Unix systems, we can read /proc/<pid>/stat for resource usage
      // For cross-platform compatibility, we'll track runtime and monitor basic metrics
      const runtime = Date.now() - this.resourceMonitoring.startTime;

      // Check if process is still alive
      try {
        process.kill(this.process.pid, 0); // Signal 0 checks if process exists
      } catch (error) {
        // Process doesn't exist
        this.logger.warn('Plugin process no longer exists', {
          server: this.config.name,
          pid: this.process.pid
        });
        return;
      }

      // Note: ChildProcess doesn't expose memory/CPU directly
      // In production, you'd want to use platform-specific tools like:
      // - ps/pidstat on Linux
      // - tasklist on Windows
      // - or libraries like pidusage
      // For now, we'll track runtime and output size as basic security measures

      // The timeout will handle excessive runtime
      // The output buffer check handles excessive output
      // Additional monitoring can be added via external tools

      this.resourceMonitoring.lastCheck = Date.now();

      // Log periodic status for audit
      if (runtime % 30000 === 0) { // Every 30 seconds
        this.logger.debug('Plugin runtime status', {
          server: this.config.name,
          runtime: runtime / 1000,
          pid: this.process.pid
        });
      }
    } catch (error) {
      this.logger.error('Error checking resource limits', error, {
        server: this.config.name
      });
    }
  }

  /**
   * Terminate plugin process for security violation
   */
  private terminateProcess(reason: string): void {
    securityLogger.error('Terminating plugin due to security violation', {
      server: this.config.name,
      reason,
      pid: this.process?.pid
    });

    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }

    if (this.processTimeout) {
      clearTimeout(this.processTimeout);
      this.processTimeout = null;
    }

    if (this.process) {
      this.process.kill('SIGKILL'); // Force kill for security violations
      this.process = null;
    }

    this.handleError(new Error(`Plugin terminated due to ${reason}`));
  }

  /**
   * Start MCP server process with sandboxing and security restrictions
   */
  private async startProcess(): Promise<void> {
    return new Promise((resolve, reject) => {
      // Log plugin spawn for security audit
      securityLogger.info('Spawning MCP plugin', {
        server: this.config.name,
        command: this.config.command,
        args: this.config.args
      });

      // Create sandboxed spawn options
      const spawnOptions = this.createSandboxedSpawnOptions();

      this.process = spawn(this.config.command, this.config.args, spawnOptions);

      // Initialize resource monitoring
      this.initializeResourceMonitoring();

      let buffer = '';
      let outputSize = 0; // Track total output size

      this.process.stdout?.on('data', (data) => {
        // Check output buffer size for security
        outputSize += data.length;
        if (outputSize > SANDBOX_CONFIG.MAX_BUFFER) {
          securityLogger.error('Plugin exceeded output buffer limit', {
            server: this.config.name,
            outputSize,
            maxBuffer: SANDBOX_CONFIG.MAX_BUFFER
          });
          this.terminateProcess('output_buffer_exceeded');
          return;
        }

        buffer += data.toString();
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        lines.forEach((line) => {
          if (line.trim()) {
            try {
              const message = MCPMessageBuilder.parseMessage(line);
              this.handleMessage(message);
            } catch (error) {
              this.logger.error('Failed to parse MCP message', error, {
                server: this.config.name,
                line
              });
            }
          }
        });
      });

      this.process.stderr?.on('data', (data) => {
        // Also track stderr for buffer limits
        outputSize += data.length;
        if (outputSize > SANDBOX_CONFIG.MAX_BUFFER) {
          securityLogger.error('Plugin exceeded output buffer limit (stderr)', {
            server: this.config.name,
            outputSize,
            maxBuffer: SANDBOX_CONFIG.MAX_BUFFER
          });
          this.terminateProcess('output_buffer_exceeded');
          return;
        }
        this.logger.error('Plugin stderr output', undefined, {
          server: this.config.name,
          output: data.toString()
        });
      });

      this.process.on('error', (error) => {
        this.logger.error('Plugin process error', error, {
          server: this.config.name
        });
        this.handleError(error);
        reject(error);
      });

      this.process.on('exit', (code, signal) => {
        this.logger.info('Plugin process exited', {
          server: this.config.name,
          exitCode: code,
          signal
        });

        // Clean up monitoring
        if (this.monitoringInterval) {
          clearInterval(this.monitoringInterval);
          this.monitoringInterval = null;
        }
        if (this.processTimeout) {
          clearTimeout(this.processTimeout);
          this.processTimeout = null;
        }

        if (this.state === ConnectionState.CONNECTING) {
          reject(new Error(`Process exited with code ${code} during connection`));
        } else if (this.state === ConnectionState.CONNECTED) {
          this.handleDisconnection();
        }
      });

      // Resolve after process starts
      setTimeout(() => {
        if (this.process && this.process.pid) {
          this.logger.info('Plugin started successfully', {
            server: this.config.name,
            pid: this.process.pid
          });
          resolve();
        } else {
          reject(new Error('Failed to start plugin process'));
        }
      }, 100);
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

    await this.request(initRequest.method!, initRequest.params);

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
        this.logger.error('Reconnection attempt failed', error, {
          server: this.config.name,
          attempt: this.reconnectAttempts,
          nextDelay: delay
        });
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
  private logger = createLogger('MCPClient');

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
          this.logger.error('Failed to list tools', error, { server: name });
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
          this.logger.error('Failed to list resources', error, { server: name });
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
            this.logger.error('Failed to sync context', error, { server: name });
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
