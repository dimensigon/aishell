/**
 * Mock Database Connection Manager for tests
 */

import { vi } from 'vitest';

export class DatabaseConnectionManager {
  private connections = new Map();

  constructor(public stateManager: any) {}

  getConnection(name: string) {
    return this.connections.get(name) || {
      database: name,
      connected: true,
      type: 'postgresql'
    };
  }

  addConnection(config: any) {
    this.connections.set(config.name, config);
  }

  removeConnection(name: string) {
    this.connections.delete(name);
  }

  listConnections() {
    return Array.from(this.connections.values());
  }
}
