/**
 * Mock MCP Server for Testing
 * Provides simulated database responses for testing
 */

export class MockMCPServer {
  private connections: Map<string, any> = new Map();
  private databases: Map<string, any> = new Map();
  private queryResults: Map<string, any> = new Map();

  constructor() {
    this.initializeMockData();
  }

  private initializeMockData(): void {
    // Mock PostgreSQL database
    this.databases.set('postgresql', {
      name: 'testdb',
      schema: 'public',
      tables: [
        {
          name: 'users',
          columns: [
            { name: 'id', type: 'integer', primary: true },
            { name: 'email', type: 'varchar', nullable: false },
            { name: 'name', type: 'varchar', nullable: true },
            { name: 'created_at', type: 'timestamp', nullable: false },
            { name: 'active', type: 'boolean', nullable: false },
          ],
          rows: [
            { id: 1, email: 'user1@test.com', name: 'User One', created_at: new Date('2024-01-01'), active: true },
            { id: 2, email: 'user2@test.com', name: 'User Two', created_at: new Date('2024-01-15'), active: true },
            { id: 3, email: 'user3@test.com', name: 'User Three', created_at: new Date('2024-02-01'), active: false },
          ],
        },
        {
          name: 'orders',
          columns: [
            { name: 'id', type: 'integer', primary: true },
            { name: 'user_id', type: 'integer', nullable: false },
            { name: 'amount', type: 'decimal', nullable: false },
            { name: 'status', type: 'varchar', nullable: false },
            { name: 'created_at', type: 'timestamp', nullable: false },
          ],
          rows: [
            { id: 1, user_id: 1, amount: 99.99, status: 'completed', created_at: new Date('2024-01-05') },
            { id: 2, user_id: 1, amount: 149.99, status: 'pending', created_at: new Date('2024-02-01') },
            { id: 3, user_id: 2, amount: 79.99, status: 'completed', created_at: new Date('2024-01-20') },
          ],
        },
      ],
    });

    // Mock Oracle database
    this.databases.set('oracle', {
      name: 'ORCL',
      schema: 'SYSTEM',
      objects: [
        { object_name: 'EMPLOYEES', object_type: 'TABLE' },
        { object_name: 'DEPARTMENTS', object_type: 'TABLE' },
        { object_name: 'EMP_PKG', object_type: 'PACKAGE' },
        { object_name: 'SALARY_VIEW', object_type: 'VIEW' },
      ],
    });

    // Mock query patterns
    this.queryResults.set('SELECT 1', [{ '?column?': 1 }]);
    this.queryResults.set('SHOW TABLES', [
      { table_name: 'users' },
      { table_name: 'orders' },
    ]);
  }

  async connect(credentials: {
    type: string;
    host: string;
    port: number;
    database?: string;
    service?: string;
    user: string;
    password: string;
  }): Promise<{ connectionId: string; success: boolean }> {
    if (credentials.host === 'invalid-host') {
      throw new Error('Connection refused: host not found');
    }

    if (credentials.password === 'wrongpass') {
      throw new Error('Authentication failed');
    }

    const connectionId = `${credentials.type}-${Date.now()}`;
    this.connections.set(connectionId, {
      ...credentials,
      connected: true,
      timestamp: Date.now(),
    });

    return { connectionId, success: true };
  }

  async disconnect(connectionId: string): Promise<void> {
    this.connections.delete(connectionId);
  }

  async executeQuery(
    connectionId: string,
    sql: string,
    params?: any[]
  ): Promise<{ rows: any[]; rowCount: number; fields?: any[] }> {
    const connection = this.connections.get(connectionId);

    if (!connection) {
      throw new Error('Connection not found');
    }

    // Simulate SQL parsing and execution
    const normalizedSQL = sql.trim().toUpperCase();

    // Handle specific query patterns
    if (this.queryResults.has(sql)) {
      const rows = this.queryResults.get(sql);
      return { rows, rowCount: rows.length };
    }

    // Handle SELECT queries
    if (normalizedSQL.startsWith('SELECT')) {
      return this.handleSelectQuery(connection.type, sql, params);
    }

    // Handle INSERT queries
    if (normalizedSQL.startsWith('INSERT')) {
      return this.handleInsertQuery(connection.type, sql, params);
    }

    // Handle UPDATE queries
    if (normalizedSQL.startsWith('UPDATE')) {
      return this.handleUpdateQuery(connection.type, sql, params);
    }

    // Handle DELETE queries
    if (normalizedSQL.startsWith('DELETE')) {
      return this.handleDeleteQuery(connection.type, sql, params);
    }

    // Handle DDL
    if (normalizedSQL.startsWith('CREATE') || normalizedSQL.startsWith('ALTER')) {
      return { rows: [], rowCount: 0 };
    }

    // Handle transactions
    if (['BEGIN', 'COMMIT', 'ROLLBACK'].includes(normalizedSQL)) {
      return { rows: [], rowCount: 0 };
    }

    // Invalid SQL
    throw new Error(`Syntax error in SQL: ${sql}`);
  }

  private handleSelectQuery(dbType: string, sql: string, params?: any[]): any {
    const db = this.databases.get(dbType);

    if (!db) {
      throw new Error('Database not configured');
    }

    // Simple pattern matching for common queries
    if (sql.includes('FROM users')) {
      const usersTable = db.tables?.find((t: any) => t.name === 'users');
      let rows = usersTable?.rows || [];

      // Apply LIMIT
      const limitMatch = sql.match(/LIMIT\s+(\d+)/i);
      if (limitMatch) {
        rows = rows.slice(0, parseInt(limitMatch[1]));
      }

      // Apply WHERE conditions (simple)
      if (sql.includes('WHERE')) {
        if (sql.includes('active = true')) {
          rows = rows.filter((r: any) => r.active === true);
        }
        if (sql.includes('id = ')) {
          const idMatch = sql.match(/id\s*=\s*(\d+|\$1)/);
          if (idMatch) {
            const id = params?.[0] || parseInt(idMatch[1]);
            rows = rows.filter((r: any) => r.id === id);
          }
        }
      }

      return { rows, rowCount: rows.length };
    }

    if (sql.includes('FROM orders')) {
      const ordersTable = db.tables?.find((t: any) => t.name === 'orders');
      return { rows: ordersTable?.rows || [], rowCount: ordersTable?.rows?.length || 0 };
    }

    // Oracle-specific
    if (sql.includes('all_objects') || sql.includes('all_tables')) {
      return { rows: db.objects || [], rowCount: db.objects?.length || 0 };
    }

    // Generic response for unmatched queries
    return { rows: [], rowCount: 0 };
  }

  private handleInsertQuery(dbType: string, sql: string, params?: any[]): any {
    // Simulate INSERT success
    const returningMatch = sql.match(/RETURNING\s+(\w+)/i);

    if (returningMatch) {
      return {
        rows: [{ [returningMatch[1]]: Math.floor(Math.random() * 1000) }],
        rowCount: 1,
      };
    }

    return { rows: [], rowCount: 1 };
  }

  private handleUpdateQuery(dbType: string, sql: string, params?: any[]): any {
    // Simulate UPDATE success
    return { rows: [], rowCount: 1 };
  }

  private handleDeleteQuery(dbType: string, sql: string, params?: any[]): any {
    // Simulate DELETE success
    return { rows: [], rowCount: 1 };
  }

  async queryUserObjects(
    connectionId: string
  ): Promise<Array<{ object_name: string; object_type: string }>> {
    const connection = this.connections.get(connectionId);

    if (!connection) {
      throw new Error('Connection not found');
    }

    const db = this.databases.get(connection.type);

    if (connection.type === 'oracle') {
      return db.objects || [];
    }

    if (connection.type === 'postgresql') {
      return db.tables?.map((t: any) => ({
        object_name: t.name,
        object_type: 'TABLE',
      })) || [];
    }

    return [];
  }

  async getTableSchema(
    connectionId: string,
    tableName: string
  ): Promise<any[]> {
    const connection = this.connections.get(connectionId);

    if (!connection) {
      throw new Error('Connection not found');
    }

    const db = this.databases.get(connection.type);
    const table = db.tables?.find((t: any) => t.name === tableName);

    return table?.columns || [];
  }

  listConnections(): Array<{ id: string; type: string; database: string }> {
    return Array.from(this.connections.entries()).map(([id, conn]) => ({
      id,
      type: conn.type,
      database: conn.database || conn.service,
    }));
  }

  simulateDisconnect(connectionId: string): void {
    const connection = this.connections.get(connectionId);
    if (connection) {
      connection.connected = false;
    }
  }

  simulateReconnect(connectionId: string): void {
    const connection = this.connections.get(connectionId);
    if (connection) {
      connection.connected = true;
    }
  }
}

export default MockMCPServer;
