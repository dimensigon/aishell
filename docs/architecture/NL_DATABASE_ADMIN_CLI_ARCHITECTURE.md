# Natural Language Database Administration CLI - System Architecture

**Document Version**: 1.0.0
**Date**: 2025-10-27
**Author**: System Architect
**Status**: Design Complete

---

## Executive Summary

This document defines the architecture for a natural language-driven database administration CLI that makes database operations accessible through conversational commands. The system eliminates the need for users to write SQL or complex scripts, providing an intuitive interface for database management, querying, and administration.

### Key Value Propositions

- **Accessibility**: Database operations via natural language commands
- **Safety**: Built-in validation, confirmation, and rollback mechanisms
- **Efficiency**: Multi-database support with connection pooling
- **Intelligence**: LLM-powered query translation and optimization
- **Transparency**: Dry-run modes and query explanations

---

## Table of Contents

1. [System Overview](#system-overview)
2. [CLI Command Specification](#cli-command-specification)
3. [Architecture Components](#architecture-components)
4. [Component Interactions](#component-interactions)
5. [Data Flow Diagrams](#data-flow-diagrams)
6. [Integration Points](#integration-points)
7. [Security & Safety](#security-and-safety)
8. [Implementation Plan](#implementation-plan)
9. [Architecture Decision Records](#architecture-decision-records)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Interface Layer                       │
│  (Command Parser, Option Validator, Output Formatter)           │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────────┐
│                    Core Service Layer                            │
├──────────────────┬──────────────────┬──────────────────────────┤
│  NLQueryEngine   │  DatabaseManager │  OperationCoordinator    │
│  - Translation   │  - Connections   │  - Workflows             │
│  - Validation    │  - Pooling       │  - Orchestration         │
│  - Optimization  │  - Routing       │  - State Management      │
└──────────────────┴──────────────────┴──────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────────┐
│                    Domain Service Layer                          │
├────────────┬──────────────┬─────────────┬──────────────────────┤
│ Schema     │ Query        │ Migration   │ Performance          │
│ Inspector  │ Executor     │ Engine      │ Monitor              │
└────────────┴──────────────┴─────────────┴──────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────────┐
│                   Infrastructure Layer                           │
├──────────────────┬──────────────────┬──────────────────────────┤
│  MCP Client      │  Database        │  Storage                 │
│  (LLM Access)    │  Drivers         │  (Config, Cache)         │
└──────────────────┴──────────────────┴──────────────────────────┘
```

### Supported Databases

- **PostgreSQL** (9.6+)
- **MySQL/MariaDB** (5.7+)
- **SQLite** (3.x)
- **MongoDB** (4.0+) - NoSQL support
- **SQL Server** (2016+)
- **Oracle** (12c+) - via optional driver

---

## CLI Command Specification

### Command Hierarchy

```
ai-shell [global-options]
  ├── query        - Natural language query execution
  ├── db           - Database connection management
  ├── schema       - Schema exploration and documentation
  ├── data         - Data import/export/backup operations
  ├── migrate      - Schema migration management
  ├── perf         - Performance monitoring and analysis
  └── config       - CLI configuration and preferences
```

### 1. Query Commands

#### `ai-shell query <nl-query>`

Execute natural language queries against the active database.

**Examples**:
```bash
# Basic queries
ai-shell query "show all users"
ai-shell query "count active orders from last month"
ai-shell query "find customers in California with orders over $1000"

# With options
ai-shell query "top 10 products by revenue" --format json
ai-shell query "users created today" --explain
ai-shell query "slow running queries" --dry-run
ai-shell query "delete spam comments" --confirm
```

**Options**:
- `--format, -f <format>`: Output format (table, json, csv, yaml) [default: table]
- `--explain, -e`: Show generated SQL and execution plan
- `--dry-run, -d`: Validate without executing
- `--confirm, -c`: Require confirmation for destructive operations
- `--limit, -l <n>`: Limit result rows
- `--output, -o <file>`: Write results to file
- `--stream`: Stream large result sets

**Output**:
```
┌─────────┬──────────────────┬─────────────────────┬──────────┐
│ user_id │ username         │ email               │ status   │
├─────────┼──────────────────┼─────────────────────┼──────────┤
│ 1       │ john_doe         │ john@example.com    │ active   │
│ 2       │ jane_smith       │ jane@example.com    │ active   │
└─────────┴──────────────────┴─────────────────────┴──────────┘

✓ Query executed successfully (2 rows, 45ms)
💡 Generated SQL: SELECT user_id, username, email, status FROM users WHERE status = 'active'
```

---

### 2. Database Connection Commands

> **Note**: The `db connect` command has been deprecated. Use database-specific connection commands or the generic `connect` command instead.

#### `ai-shell connect <connection-string>`

Connect to any database using a connection string. Auto-detects database type from protocol.

**Examples**:
```bash
# Generic connection (auto-detects from protocol)
ai-shell connect postgres://user:pass@localhost:5432/mydb
ai-shell connect mysql://root:secret@localhost:3306/app
ai-shell connect mongodb://localhost:27017/mydb
ai-shell connect redis://localhost:6379

# Named connection with SSL
ai-shell connect postgresql://user:pass@prod.example.com:5432/app_db --name production --ssl
```

**Options**:
- `--name, -n <name>`: Save connection with friendly name
- `--ssl`: Enable SSL/TLS connection
- `--read-only`: Connect in read-only mode

#### Database-Specific Connection Commands

For database-specific features and options, use dedicated commands:

**PostgreSQL**:
```bash
ai-shell pg connect postgresql://user:pass@localhost:5432/mydb
ai-shell pg connect --name production --host prod.example.com --port 5432 --database app_db
```

**MySQL**:
```bash
ai-shell mysql connect mysql://root:secret@localhost:3306/app
ai-shell mysql connect --name local --host localhost --database myapp
```

**MongoDB**:
```bash
ai-shell mongo connect mongodb://localhost:27017/mydb
ai-shell mongo connect --name dev --host localhost --port 27017
```

**Redis**:
```bash
ai-shell redis connect redis://localhost:6379
ai-shell redis connect --name cache --host localhost --port 6379
```

#### `ai-shell connections`

List all saved database connections.

**Output**:
```
Active Connections:
┌──────────────┬────────────┬─────────────────────┬──────────┬──────────┐
│ Name         │ Type       │ Host                │ Database │ Status   │
├──────────────┼────────────┼─────────────────────┼──────────┼──────────┤
│ production * │ postgres   │ prod.example.com    │ app_db   │ active   │
│ staging      │ postgres   │ staging.example.com │ app_db   │ saved    │
│ cache        │ redis      │ localhost:6379      │ 0        │ saved    │
└──────────────┴────────────┴─────────────────────┴──────────┴──────────┘

* = currently active
```

#### `ai-shell use <connection-name>`

Switch to a different saved connection.

**Example**:
```bash
ai-shell use staging
✓ Switched to connection 'staging' (postgres://staging.example.com/app_db)
```

#### `ai-shell disconnect [name]`

Disconnect from current database or a specific named connection.

**Examples**:
```bash
ai-shell disconnect              # Disconnect current
ai-shell disconnect production   # Disconnect specific connection
```

---

### 3. Schema Exploration Commands

#### `ai-shell schema explore <nl-query>`

Explore database schema using natural language.

**Examples**:
```bash
ai-shell schema explore "what tables exist?"
ai-shell schema explore "show me tables related to orders"
ai-shell schema explore "which columns contain email addresses?"
ai-shell schema explore "find all foreign key relationships"
```

#### `ai-shell schema describe <table-name>`

Show detailed information about a table.

**Example**:
```bash
ai-shell schema describe users

Table: users
┌────────────────┬──────────────┬──────────┬─────────┬─────────────┐
│ Column         │ Type         │ Nullable │ Default │ Constraints │
├────────────────┼──────────────┼──────────┼─────────┼─────────────┤
│ id             │ INTEGER      │ NO       │ auto    │ PRIMARY KEY │
│ username       │ VARCHAR(50)  │ NO       │ NULL    │ UNIQUE      │
│ email          │ VARCHAR(255) │ NO       │ NULL    │ UNIQUE      │
│ password_hash  │ VARCHAR(255) │ NO       │ NULL    │             │
│ created_at     │ TIMESTAMP    │ NO       │ NOW()   │             │
│ updated_at     │ TIMESTAMP    │ YES      │ NULL    │             │
└────────────────┴──────────────┴──────────┴─────────┴─────────────┘

Indexes:
  - idx_users_username (username)
  - idx_users_email (email)

Foreign Keys:
  - None

Referenced By:
  - orders.user_id → users.id
  - sessions.user_id → users.id
```

**Options**:
- `--format, -f <format>`: Output format (table, json, yaml)
- `--full`: Include statistics and sample data

#### `ai-shell schema relationships <table-name>`

Visualize table relationships.

**Example**:
```bash
ai-shell schema relationships orders

Relationship Graph for: orders
┌──────────┐      ┌────────────┐      ┌──────────┐
│  users   │◄─────┤   orders   │─────►│ products │
└──────────┘      └────────────┘      └──────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ order_items  │
                  └──────────────┘

Direct Relationships:
  orders.user_id → users.id (many-to-one)
  orders.product_id → products.id (many-to-many via order_items)
```

#### `ai-shell schema diagram`

Generate comprehensive database schema diagram.

**Options**:
- `--format <format>`: Output format (ascii, mermaid, plantuml, svg)
- `--output, -o <file>`: Save to file

---

### 4. Data Operations Commands

#### `ai-shell data export <table-or-query>`

Export data to various formats.

**Examples**:
```bash
# Export table
ai-shell data export users --format csv --output users.csv

# Export query results
ai-shell data export "active users from last month" --format json

# Export with filters
ai-shell data export orders --where "status='completed'" --format excel
```

**Options**:
- `--format, -f <format>`: Export format (csv, json, excel, sql, parquet)
- `--output, -o <file>`: Output file path
- `--where <condition>`: SQL WHERE clause
- `--columns <cols>`: Specific columns to export
- `--compress`: Compress output (gzip)

#### `ai-shell data import <file>`

Import data from file into database.

**Examples**:
```bash
# Import CSV
ai-shell data import customers.csv --table customers

# Import with mapping
ai-shell data import data.json --table users --mapping mapping.json

# Import with transformations
ai-shell data import legacy.csv --table new_users --transform "email=LOWER(email)"
```

**Options**:
- `--table, -t <name>`: Target table
- `--create-table`: Automatically create table
- `--mapping <file>`: Column mapping configuration
- `--transform <expr>`: Transformation expressions
- `--batch-size <n>`: Batch size for inserts [default: 1000]
- `--on-conflict <action>`: Conflict resolution (skip, update, error)

#### `ai-shell data backup`

Create database backup.

**Examples**:
```bash
# Full backup
ai-shell data backup --output ./backups/production-2025-10-27.sql

# Incremental backup
ai-shell data backup --incremental --since "2025-10-26"

# Backup specific tables
ai-shell data backup --tables users,orders,products
```

**Options**:
- `--output, -o <path>`: Backup file path
- `--compress`: Compress backup
- `--incremental`: Incremental backup
- `--since <date>`: Backup changes since date
- `--tables <list>`: Backup specific tables
- `--exclude <list>`: Exclude tables
- `--encrypt`: Encrypt backup (prompts for passphrase)

#### `ai-shell data restore <backup-file>`

Restore database from backup.

**Examples**:
```bash
ai-shell data restore ./backups/production-2025-10-27.sql
ai-shell data restore backup.sql.gz --decompress
ai-shell data restore backup.sql --target staging
```

**Options**:
- `--target <connection>`: Restore to different database
- `--decompress`: Decompress before restoring
- `--decrypt`: Decrypt backup (prompts for passphrase)
- `--dry-run`: Validate backup without restoring
- `--force`: Skip confirmation prompts

---

### 5. Migration Commands

#### `ai-shell migrate plan <nl-description>`

Generate migration plan from natural language description.

**Examples**:
```bash
# Generate migration
ai-shell migrate plan "add email verification to users"

# Output:
Migration Plan: add_email_verification_to_users
Generated: 2025-10-27T05:33:00Z

-- Up Migration
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN verification_token VARCHAR(64);
CREATE INDEX idx_users_verification_token ON users(verification_token);

-- Down Migration
DROP INDEX idx_users_verification_token;
ALTER TABLE users DROP COLUMN verification_token;
ALTER TABLE users DROP COLUMN email_verified;

Save this migration? [y/N]: y
✓ Saved as migrations/20251027053300_add_email_verification_to_users.sql
```

**Options**:
- `--name <name>`: Custom migration name
- `--template <type>`: Migration template (create_table, add_column, etc.)
- `--save`: Automatically save without prompting
- `--edit`: Open in editor before saving

#### `ai-shell migrate execute <migration-file>`

Execute a migration.

**Examples**:
```bash
# Execute single migration
ai-shell migrate execute migrations/20251027053300_add_email_verification.sql

# Execute all pending
ai-shell migrate execute --pending

# Dry run
ai-shell migrate execute migration.sql --dry-run
```

**Options**:
- `--pending`: Execute all pending migrations
- `--dry-run`: Validate without executing
- `--transaction`: Wrap in transaction (default: true)
- `--force`: Skip safety checks

#### `ai-shell migrate rollback`

Rollback last migration.

**Examples**:
```bash
ai-shell migrate rollback
ai-shell migrate rollback --steps 3
ai-shell migrate rollback --to 20251027053300
```

**Options**:
- `--steps <n>`: Rollback N migrations
- `--to <version>`: Rollback to specific version
- `--dry-run`: Show what would be rolled back

#### `ai-shell migrate status`

Show migration status.

**Output**:
```
Migration Status:
┌────────────────────┬──────────────────────────────────┬────────────┐
│ Version            │ Name                             │ Status     │
├────────────────────┼──────────────────────────────────┼────────────┤
│ 20251027053300     │ add_email_verification_to_users  │ applied    │
│ 20251027054500     │ create_orders_table              │ applied    │
│ 20251027055000     │ add_indexes_to_orders            │ pending    │
└────────────────────┴──────────────────────────────────┴────────────┘

Applied: 2 | Pending: 1
```

---

### 6. Performance Monitoring Commands

#### `ai-shell perf monitor`

Real-time performance monitoring.

**Examples**:
```bash
# Monitor with default interval
ai-shell perf monitor

# Custom interval
ai-shell perf monitor --interval 5s

# Monitor specific metrics
ai-shell perf monitor --metrics queries,connections,locks
```

**Output**:
```
Database Performance Monitor (Refreshing every 5s)
Press Ctrl+C to stop

┌──────────────────────┬─────────────────┐
│ Metric               │ Current         │
├──────────────────────┼─────────────────┤
│ Active Connections   │ 42 / 100        │
│ Queries/sec          │ 1,245           │
│ Avg Query Time       │ 12.5ms          │
│ Cache Hit Rate       │ 98.2%           │
│ Active Transactions  │ 8               │
│ Waiting Queries      │ 2               │
│ Locks                │ 15              │
│ Deadlocks            │ 0               │
└──────────────────────┴─────────────────┘

Top 5 Active Queries:
1. SELECT * FROM orders WHERE... (234ms, waiting)
2. UPDATE users SET... (89ms, running)
3. SELECT COUNT(*) FROM... (45ms, running)
```

**Options**:
- `--interval <duration>`: Update interval [default: 1s]
- `--metrics <list>`: Specific metrics to monitor
- `--duration <duration>`: Auto-stop after duration
- `--alert <condition>`: Alert on conditions (e.g., "queries>1000")

#### `ai-shell perf slow-queries`

Show slow query log.

**Examples**:
```bash
ai-shell perf slow-queries
ai-shell perf slow-queries --threshold 1s
ai-shell perf slow-queries --top 20
```

**Options**:
- `--threshold <duration>`: Minimum query duration [default: 100ms]
- `--top <n>`: Show top N slowest queries [default: 10]
- `--since <time>`: Queries since timestamp
- `--analyze`: Include execution plans

#### `ai-shell perf analyze <query>`

Analyze query performance.

**Examples**:
```bash
ai-shell perf analyze "SELECT * FROM orders WHERE status = 'pending'"

Query Analysis:
───────────────────────────────────────────────────────────────
Original Query:
  SELECT * FROM orders WHERE status = 'pending'

Execution Plan:
  Seq Scan on orders (cost=0.00..1234.56 rows=1000 width=128)
    Filter: (status = 'pending')

Performance Metrics:
  Estimated Cost: 1234.56
  Estimated Rows: 1000
  Estimated Time: 45ms

Recommendations:
  ⚠️  Missing index on orders.status
  💡 Create index: CREATE INDEX idx_orders_status ON orders(status);
  ⚡ Estimated improvement: 95% faster

Optimized Query:
  -- Add this index first:
  CREATE INDEX idx_orders_status ON orders(status);

  -- Then run:
  SELECT * FROM orders WHERE status = 'pending';
```

**Options**:
- `--format <format>`: Output format (table, json, visual)
- `--suggestions`: Include optimization suggestions
- `--compare <query>`: Compare with alternative query

---

### 7. Configuration Commands

#### `ai-shell config set <key> <value>`

Set configuration option.

**Examples**:
```bash
ai-shell config set default-format json
ai-shell config set auto-confirm false
ai-shell config set max-rows 100
```

#### `ai-shell config get <key>`

Get configuration value.

#### `ai-shell config list`

List all configuration options.

---

## Architecture Components

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLI Layer                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ CommandParser │   │OptionValidator│   │ResultFormatter│
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        └───────────────────┼───────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────────┐
│                     Core Services                                │
├─────────────────┬────────────────────┬──────────────────────────┤
│                 │                    │                          │
│  NLQueryEngine  │  DatabaseManager   │  OperationCoordinator    │
│  ┌───────────┐  │  ┌──────────────┐  │  ┌────────────────────┐ │
│  │Translator │  │  │ConnectionPool│  │  │WorkflowOrchestrator│ │
│  │Validator  │  │  │ConfigManager │  │  │StateManager        │ │
│  │Optimizer  │  │  │RouterService │  │  │ErrorHandler        │ │
│  └───────────┘  │  └──────────────┘  │  └────────────────────┘ │
└─────────────────┴────────────────────┴──────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────────┐
│                     Domain Services                              │
├──────────────┬──────────────┬──────────────┬───────────────────┤
│              │              │              │                   │
│SchemaInspect.│QueryExecutor │MigrationEng. │PerformanceMonitor │
│┌───────────┐ │┌───────────┐ │┌───────────┐ │┌────────────────┐│
││Introspect.│ ││SafeExecute│ ││PlanGen.   │ ││MetricsCollector││
││Describer  │ ││ResultStr. │ ││Executor   │ ││SlowQueryLog    ││
││Visualizer │ ││Transaction│ ││Rollback   │ ││QueryAnalyzer   ││
│└───────────┘ │└───────────┘ │└───────────┘ │└────────────────┘│
└──────────────┴──────────────┴──────────────┴───────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────────┐
│                     Infrastructure                               │
├──────────────────┬──────────────────┬──────────────────────────┤
│  MCPClient       │  DatabaseDrivers │  Storage                 │
│  ┌────────────┐  │  ┌────────────┐  │  ┌────────────────────┐ │
│  │LLMProvider │  │  │PostgreSQL  │  │  │ConfigStore         │ │
│  │PromptMgr   │  │  │MySQL       │  │  │QueryCache          │ │
│  │ResponsePar.│  │  │SQLite      │  │  │MigrationHistory    │ │
│  └────────────┘  │  │MongoDB     │  │  │PerformanceMetrics  │ │
│                  │  └────────────┘  │  └────────────────────┘ │
└──────────────────┴──────────────────┴──────────────────────────┘
```

---

## Detailed Component Specifications

### 1. NLQueryEngine

**Purpose**: Convert natural language to SQL and validate queries.

**Responsibilities**:
- Natural language parsing and intent detection
- SQL query generation via LLM
- Query validation and safety checks
- Query optimization suggestions
- Context-aware translation using schema information

**Interfaces**:
```typescript
interface NLQueryEngine {
  /**
   * Translate natural language to SQL
   */
  translate(
    nlQuery: string,
    context: QueryContext
  ): Promise<TranslationResult>;

  /**
   * Validate generated SQL for safety and correctness
   */
  validate(
    sql: string,
    options: ValidationOptions
  ): Promise<ValidationResult>;

  /**
   * Optimize SQL query
   */
  optimize(
    sql: string,
    schema: SchemaInfo
  ): Promise<OptimizationResult>;

  /**
   * Explain query in natural language
   */
  explain(sql: string): Promise<string>;
}

interface TranslationResult {
  sql: string;
  confidence: number;
  warnings: string[];
  requiresConfirmation: boolean;
  explanation: string;
}

interface QueryContext {
  databaseType: DatabaseType;
  schema: SchemaInfo;
  activeTable?: string;
  userHistory: QueryHistory[];
  preferences: UserPreferences;
}
```

**Implementation Details**:
```typescript
class NLQueryEngineImpl implements NLQueryEngine {
  constructor(
    private mcpClient: MCPClient,
    private schemaInspector: SchemaInspector,
    private queryValidator: QueryValidator
  ) {}

  async translate(
    nlQuery: string,
    context: QueryContext
  ): Promise<TranslationResult> {
    // 1. Extract schema context
    const schemaContext = await this.schemaInspector.getRelevantSchema(
      nlQuery,
      context.schema
    );

    // 2. Build prompt with schema and examples
    const prompt = this.buildPrompt(nlQuery, schemaContext, context);

    // 3. Call LLM via MCP
    const llmResponse = await this.mcpClient.generateSQL({
      prompt,
      schema: schemaContext,
      databaseType: context.databaseType
    });

    // 4. Parse and validate response
    const parsed = this.parseResponse(llmResponse);

    // 5. Validate SQL
    const validation = await this.queryValidator.validate(
      parsed.sql,
      context.databaseType
    );

    // 6. Determine if confirmation required
    const requiresConfirmation = this.isDestructive(parsed.sql);

    return {
      sql: parsed.sql,
      confidence: parsed.confidence,
      warnings: validation.warnings,
      requiresConfirmation,
      explanation: parsed.explanation
    };
  }

  private buildPrompt(
    nlQuery: string,
    schema: SchemaInfo,
    context: QueryContext
  ): string {
    return `
You are a SQL expert. Convert the following natural language query to SQL.

Database Type: ${context.databaseType}
Schema Information:
${this.formatSchema(schema)}

User Query: "${nlQuery}"

Previous Queries (for context):
${this.formatHistory(context.userHistory)}

Generate a safe, optimized SQL query. Include:
1. The SQL query
2. Explanation of what the query does
3. Any assumptions made
4. Warnings if the query is potentially destructive

Response format:
{
  "sql": "SELECT ...",
  "explanation": "This query retrieves...",
  "assumptions": ["..."],
  "warnings": ["..."],
  "confidence": 0.95
}
`;
  }

  private isDestructive(sql: string): boolean {
    const destructiveKeywords = [
      'DELETE',
      'DROP',
      'TRUNCATE',
      'ALTER',
      'UPDATE'
    ];
    const upperSQL = sql.toUpperCase();
    return destructiveKeywords.some(keyword =>
      upperSQL.includes(keyword)
    );
  }
}
```

**Dependencies**:
- MCPClient (for LLM access)
- SchemaInspector (for schema context)
- QueryValidator (for safety checks)
- StateManager (for user history)

---

### 2. DatabaseManager

**Purpose**: Manage database connections, pooling, and routing.

**Responsibilities**:
- Connection lifecycle management
- Connection pooling and reuse
- Multi-database support
- Connection configuration persistence
- Health checking and reconnection

**Interfaces**:
```typescript
interface DatabaseManager {
  /**
   * Connect to database
   */
  connect(config: ConnectionConfig): Promise<Connection>;

  /**
   * Get active connection
   */
  getConnection(name?: string): Promise<Connection>;

  /**
   * List all saved connections
   */
  listConnections(): Promise<ConnectionInfo[]>;

  /**
   * Switch active connection
   */
  switchConnection(name: string): Promise<void>;

  /**
   * Disconnect from database
   */
  disconnect(name?: string): Promise<void>;

  /**
   * Remove saved connection
   */
  removeConnection(name: string): Promise<void>;

  /**
   * Test connection
   */
  testConnection(config: ConnectionConfig): Promise<TestResult>;
}

interface ConnectionConfig {
  name?: string;
  type: DatabaseType;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  ssl?: boolean;
  readOnly?: boolean;
  poolSize?: number;
  connectionTimeout?: number;
  options?: Record<string, any>;
}

interface Connection {
  id: string;
  name: string;
  type: DatabaseType;
  execute(sql: string): Promise<QueryResult>;
  transaction<T>(fn: (tx: Transaction) => Promise<T>): Promise<T>;
  close(): Promise<void>;
}
```

**Implementation Details**:
```typescript
class DatabaseManagerImpl implements DatabaseManager {
  private connections: Map<string, Connection> = new Map();
  private activeConnection: string | null = null;
  private configStore: ConfigStore;

  constructor(
    private stateManager: StateManager,
    configStore: ConfigStore
  ) {
    this.configStore = configStore;
  }

  async connect(config: ConnectionConfig): Promise<Connection> {
    // 1. Validate configuration
    this.validateConfig(config);

    // 2. Create driver instance
    const driver = this.createDriver(config);

    // 3. Establish connection with retry logic
    const connection = await this.establishConnection(driver, config);

    // 4. Save configuration if named
    if (config.name) {
      await this.configStore.saveConnection(config);
      this.connections.set(config.name, connection);
      this.activeConnection = config.name;
    }

    // 5. Update state
    await this.stateManager.setState('db.active', config.name);

    return connection;
  }

  private createDriver(config: ConnectionConfig): DatabaseDriver {
    switch (config.type) {
      case 'postgres':
        return new PostgreSQLDriver(config);
      case 'mysql':
        return new MySQLDriver(config);
      case 'sqlite':
        return new SQLiteDriver(config);
      case 'mongodb':
        return new MongoDBDriver(config);
      case 'mssql':
        return new MSSQLDriver(config);
      case 'oracle':
        return new OracleDriver(config);
      default:
        throw new Error(`Unsupported database type: ${config.type}`);
    }
  }

  private async establishConnection(
    driver: DatabaseDriver,
    config: ConnectionConfig
  ): Promise<Connection> {
    const maxRetries = 3;
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await driver.connect();
      } catch (error) {
        lastError = error as Error;
        if (attempt < maxRetries) {
          await this.delay(1000 * attempt); // Exponential backoff
        }
      }
    }

    throw new Error(
      `Failed to connect after ${maxRetries} attempts: ${lastError?.message}`
    );
  }

  async getConnection(name?: string): Promise<Connection> {
    const targetName = name || this.activeConnection;

    if (!targetName) {
      throw new Error('No active database connection');
    }

    const connection = this.connections.get(targetName);

    if (!connection) {
      throw new Error(`Connection '${targetName}' not found`);
    }

    // Health check
    await this.healthCheck(connection);

    return connection;
  }

  private async healthCheck(connection: Connection): Promise<void> {
    try {
      await connection.execute('SELECT 1');
    } catch (error) {
      // Attempt reconnection
      await this.reconnect(connection);
    }
  }
}
```

---

### 3. SchemaInspector

**Purpose**: Introspect and describe database schemas.

**Responsibilities**:
- Database metadata retrieval
- Table and column information
- Relationship discovery (foreign keys)
- Index analysis
- Schema visualization

**Interfaces**:
```typescript
interface SchemaInspector {
  /**
   * Get all tables in database
   */
  getTables(): Promise<TableInfo[]>;

  /**
   * Get detailed table information
   */
  getTableDetails(tableName: string): Promise<TableDetails>;

  /**
   * Get table relationships
   */
  getRelationships(tableName: string): Promise<Relationship[]>;

  /**
   * Get relevant schema for NL query
   */
  getRelevantSchema(
    nlQuery: string,
    fullSchema: SchemaInfo
  ): Promise<SchemaInfo>;

  /**
   * Generate schema diagram
   */
  generateDiagram(format: DiagramFormat): Promise<string>;

  /**
   * Search schema by natural language
   */
  search(query: string): Promise<SearchResult[]>;
}

interface TableInfo {
  name: string;
  schema: string;
  rowCount: number;
  sizeBytes: number;
  comment?: string;
}

interface TableDetails {
  name: string;
  columns: ColumnInfo[];
  indexes: IndexInfo[];
  foreignKeys: ForeignKeyInfo[];
  referencedBy: ForeignKeyInfo[];
  statistics: TableStatistics;
}

interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
  defaultValue?: string;
  isPrimaryKey: boolean;
  isUnique: boolean;
  comment?: string;
}
```

**Implementation Details**:
```typescript
class SchemaInspectorImpl implements SchemaInspector {
  constructor(
    private connection: Connection,
    private mcpClient: MCPClient,
    private cache: SchemaCache
  ) {}

  async getTables(): Promise<TableInfo[]> {
    // Check cache first
    const cached = await this.cache.get('tables');
    if (cached) return cached;

    // Query database information schema
    const sql = this.buildTablesQuery(this.connection.type);
    const result = await this.connection.execute(sql);

    const tables = this.parseTablesResult(result);

    // Cache for 5 minutes
    await this.cache.set('tables', tables, 300);

    return tables;
  }

  async getRelevantSchema(
    nlQuery: string,
    fullSchema: SchemaInfo
  ): Promise<SchemaInfo> {
    // Use LLM to determine relevant tables
    const relevantTables = await this.mcpClient.identifyRelevantTables({
      query: nlQuery,
      allTables: fullSchema.tables.map(t => t.name),
      relationships: fullSchema.relationships
    });

    // Filter schema to relevant tables
    return {
      tables: fullSchema.tables.filter(t =>
        relevantTables.includes(t.name)
      ),
      relationships: fullSchema.relationships.filter(r =>
        relevantTables.includes(r.fromTable) &&
        relevantTables.includes(r.toTable)
      )
    };
  }

  async search(query: string): Promise<SearchResult[]> {
    const schema = await this.getFullSchema();

    // Search in:
    // 1. Table names
    // 2. Column names
    // 3. Comments
    // 4. Index names

    const results: SearchResult[] = [];

    for (const table of schema.tables) {
      // Table name match
      if (this.fuzzyMatch(query, table.name)) {
        results.push({
          type: 'table',
          name: table.name,
          relevance: this.calculateRelevance(query, table.name)
        });
      }

      // Column matches
      for (const column of table.columns) {
        if (this.fuzzyMatch(query, column.name)) {
          results.push({
            type: 'column',
            name: `${table.name}.${column.name}`,
            relevance: this.calculateRelevance(query, column.name)
          });
        }
      }
    }

    // Sort by relevance
    return results.sort((a, b) => b.relevance - a.relevance);
  }

  private buildTablesQuery(dbType: DatabaseType): string {
    switch (dbType) {
      case 'postgres':
        return `
          SELECT
            table_name,
            table_schema,
            pg_total_relation_size(quote_ident(table_name)::regclass) as size_bytes
          FROM information_schema.tables
          WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
          ORDER BY table_name;
        `;
      case 'mysql':
        return `
          SELECT
            TABLE_NAME as table_name,
            TABLE_SCHEMA as table_schema,
            DATA_LENGTH + INDEX_LENGTH as size_bytes
          FROM information_schema.TABLES
          WHERE TABLE_SCHEMA = DATABASE()
          ORDER BY TABLE_NAME;
        `;
      // ... other database types
      default:
        throw new Error(`Unsupported database: ${dbType}`);
    }
  }
}
```

---

### 4. QueryExecutor

**Purpose**: Safely execute SQL queries with validation and error handling.

**Responsibilities**:
- Query execution with parameter binding
- Transaction management
- Result streaming for large datasets
- Query timeout handling
- Error recovery and retry logic

**Interfaces**:
```typescript
interface QueryExecutor {
  /**
   * Execute SQL query
   */
  execute(
    sql: string,
    options: ExecutionOptions
  ): Promise<QueryResult>;

  /**
   * Execute query with streaming results
   */
  executeStream(
    sql: string,
    options: ExecutionOptions
  ): AsyncIterableIterator<Row>;

  /**
   * Execute in transaction
   */
  executeTransaction(
    queries: QueryBatch
  ): Promise<BatchResult>;

  /**
   * Explain query execution plan
   */
  explain(sql: string): Promise<ExecutionPlan>;
}

interface ExecutionOptions {
  parameters?: any[];
  timeout?: number;
  maxRows?: number;
  dryRun?: boolean;
  explain?: boolean;
}

interface QueryResult {
  rows: Row[];
  rowCount: number;
  executionTimeMs: number;
  columns: ColumnMetadata[];
  warnings?: string[];
}
```

**Implementation Details**:
```typescript
class QueryExecutorImpl implements QueryExecutor {
  constructor(
    private connection: Connection,
    private errorHandler: ErrorHandler,
    private performanceMonitor: PerformanceMonitor
  ) {}

  async execute(
    sql: string,
    options: ExecutionOptions = {}
  ): Promise<QueryResult> {
    const startTime = Date.now();

    try {
      // 1. Validate SQL
      await this.validateSQL(sql);

      // 2. Apply timeout
      const timeoutMs = options.timeout || 30000;

      // 3. Execute with monitoring
      const result = await this.executeWithTimeout(
        sql,
        options.parameters,
        timeoutMs
      );

      // 4. Apply row limit
      if (options.maxRows && result.rows.length > options.maxRows) {
        result.rows = result.rows.slice(0, options.maxRows);
        result.warnings = result.warnings || [];
        result.warnings.push(
          `Result limited to ${options.maxRows} rows`
        );
      }

      // 5. Record metrics
      const executionTimeMs = Date.now() - startTime;
      await this.performanceMonitor.recordQuery({
        sql,
        executionTimeMs,
        rowCount: result.rowCount
      });

      return {
        ...result,
        executionTimeMs
      };

    } catch (error) {
      // Handle and enrich error
      throw await this.errorHandler.handleQueryError(error, sql);
    }
  }

  async *executeStream(
    sql: string,
    options: ExecutionOptions = {}
  ): AsyncIterableIterator<Row> {
    const cursor = await this.connection.cursor(sql, options.parameters);

    try {
      while (true) {
        const row = await cursor.next();
        if (!row) break;
        yield row;
      }
    } finally {
      await cursor.close();
    }
  }

  async executeTransaction(
    queries: QueryBatch
  ): Promise<BatchResult> {
    return await this.connection.transaction(async (tx) => {
      const results: QueryResult[] = [];

      for (const query of queries.queries) {
        const result = await tx.execute(query.sql, query.parameters);
        results.push(result);

        // Check if we should continue
        if (query.continueOnError === false && result.error) {
          throw result.error;
        }
      }

      return { results };
    });
  }

  private async validateSQL(sql: string): Promise<void> {
    // Basic SQL injection protection
    const dangerous = [
      /;\s*DROP\s+/i,
      /;\s*DELETE\s+FROM\s+/i,
      /;\s*TRUNCATE\s+/i,
      /UNION\s+.*SELECT/i
    ];

    for (const pattern of dangerous) {
      if (pattern.test(sql)) {
        throw new Error(
          'Query contains potentially dangerous SQL patterns. ' +
          'Use --force to override.'
        );
      }
    }
  }

  private async executeWithTimeout(
    sql: string,
    parameters: any[] | undefined,
    timeoutMs: number
  ): Promise<QueryResult> {
    return await Promise.race([
      this.connection.execute(sql, parameters),
      this.timeoutPromise(timeoutMs)
    ]);
  }

  private timeoutPromise(ms: number): Promise<never> {
    return new Promise((_, reject) =>
      setTimeout(() => reject(new Error(`Query timeout after ${ms}ms`)), ms)
    );
  }
}
```

---

### 5. MigrationEngine

**Purpose**: Manage database schema migrations.

**Responsibilities**:
- Migration plan generation from NL
- Migration execution with rollback
- Migration versioning and history
- Schema diff and comparison
- Migration validation

**Interfaces**:
```typescript
interface MigrationEngine {
  /**
   * Generate migration from natural language
   */
  plan(description: string): Promise<Migration>;

  /**
   * Execute migration
   */
  execute(migration: Migration, options: ExecutionOptions): Promise<void>;

  /**
   * Rollback migration
   */
  rollback(options: RollbackOptions): Promise<void>;

  /**
   * Get migration status
   */
  status(): Promise<MigrationStatus[]>;

  /**
   * Validate migration
   */
  validate(migration: Migration): Promise<ValidationResult>;
}

interface Migration {
  version: string;
  name: string;
  description: string;
  up: string;
  down: string;
  createdAt: Date;
}
```

---

### 6. PerformanceMonitor

**Purpose**: Monitor and analyze database performance.

**Responsibilities**:
- Real-time metrics collection
- Slow query logging
- Query execution plan analysis
- Performance recommendations
- Alert generation

**Interfaces**:
```typescript
interface PerformanceMonitor {
  /**
   * Start monitoring
   */
  startMonitoring(options: MonitoringOptions): void;

  /**
   * Stop monitoring
   */
  stopMonitoring(): void;

  /**
   * Get current metrics
   */
  getMetrics(): Promise<PerformanceMetrics>;

  /**
   * Get slow queries
   */
  getSlowQueries(threshold: number): Promise<SlowQuery[]>;

  /**
   * Analyze query performance
   */
  analyzeQuery(sql: string): Promise<QueryAnalysis>;

  /**
   * Record query execution
   */
  recordQuery(info: QueryInfo): Promise<void>;
}
```

---

## Data Flow Diagrams

### 1. Natural Language Query Flow

```
┌──────────┐
│   User   │
└────┬─────┘
     │ "show active users"
     ▼
┌─────────────────┐
│  CLI Parser     │
│  - Parse input  │
│  - Extract opts │
└────┬────────────┘
     │ {query, options}
     ▼
┌──────────────────┐
│  NLQueryEngine   │
│  - Get schema    │◄──────┐
│  - Build prompt  │       │
│  - Call LLM      │       │ schema info
└────┬─────────────┘       │
     │ SQL + explanation   │
     ▼                     │
┌──────────────────┐       │
│ QueryValidator   │       │
│ - Safety check   │       │
│ - Confirm if req │       │
└────┬─────────────┘       │
     │ validated SQL       │
     ▼                     │
┌──────────────────┐   ┌───┴─────────┐
│  QueryExecutor   │   │SchemaInspec.│
│  - Execute SQL   │   │             │
│  - Format result │   └─────────────┘
└────┬─────────────┘
     │ results
     ▼
┌──────────────────┐
│ ResultFormatter  │
│ - Format output  │
│ - Add metadata   │
└────┬─────────────┘
     │ formatted output
     ▼
┌──────────┐
│   User   │
└──────────┘
```

### 2. Database Connection Flow

```
┌──────────┐
│   User   │
└────┬─────┘
     │ connect command
     ▼
┌──────────────────┐
│ DatabaseManager  │
│ - Parse config   │
│ - Validate       │
└────┬─────────────┘
     │ connection config
     ▼
┌──────────────────┐
│  Driver Factory  │
│ - Select driver  │
│ - Create instance│
└────┬─────────────┘
     │ driver instance
     ▼
┌──────────────────┐
│ Connection Pool  │
│ - Establish conn │◄────┐ retry
│ - Health check   │─────┘ on failure
└────┬─────────────┘
     │ active connection
     ▼
┌──────────────────┐
│  ConfigStore     │
│ - Save config    │
│ - Persist state  │
└────┬─────────────┘
     │ success
     ▼
┌──────────┐
│   User   │
└──────────┘
```

### 3. Migration Execution Flow

```
┌──────────┐
│   User   │
└────┬─────┘
     │ migrate plan "add column"
     ▼
┌──────────────────┐
│ MigrationEngine  │
│ - Parse desc.    │
│ - Get schema     │◄──────┐
└────┬─────────────┘       │ current schema
     │ NL description      │
     ▼                     │
┌──────────────────┐       │
│   LLM (via MCP)  │   ┌───┴─────────┐
│ - Generate SQL   │   │SchemaInspec.│
│ - Create up/down │   └─────────────┘
└────┬─────────────┘
     │ migration plan
     ▼
┌──────────────────┐
│ MigrationValidator│
│ - Syntax check   │
│ - Safety check   │
└────┬─────────────┘
     │ validated migration
     ▼
┌──────────────────┐
│   User Review    │──► approve?
└────┬─────────────┘     │ no → cancel
     │ yes               │
     ▼                   ▼
┌──────────────────┐   Exit
│ QueryExecutor    │
│ - Begin txn      │
│ - Execute up SQL │
│ - Commit         │
└────┬─────────────┘
     │ success
     ▼
┌──────────────────┐
│ MigrationHistory │
│ - Record version │
│ - Store metadata │
└────┬─────────────┘
     │ complete
     ▼
┌──────────┐
│   User   │
└──────────┘
```

---

## Integration Points

### 1. WorkflowOrchestrator Integration

The CLI uses WorkflowOrchestrator for complex multi-step operations:

```typescript
// Example: Data import workflow
const importWorkflow = orchestrator.createWorkflow('data-import');

importWorkflow
  .step('validate-file', async (ctx) => {
    const validation = await fileValidator.validate(ctx.file);
    if (!validation.valid) throw new Error(validation.error);
    return validation;
  })
  .step('analyze-schema', async (ctx) => {
    return await schemaAnalyzer.analyze(ctx.file);
  })
  .step('create-table', async (ctx) => {
    if (ctx.options.createTable) {
      return await tableCreator.create(ctx.schema);
    }
  })
  .step('transform-data', async (ctx) => {
    return await dataTransformer.transform(
      ctx.file,
      ctx.transformations
    );
  })
  .step('import-batch', async (ctx) => {
    return await batchImporter.import(
      ctx.data,
      ctx.table,
      ctx.batchSize
    );
  })
  .step('verify-import', async (ctx) => {
    return await importVerifier.verify(ctx.table, ctx.expectedRows);
  })
  .onError(async (error, ctx) => {
    await errorHandler.handle(error);
    if (ctx.options.rollbackOnError) {
      await rollback(ctx);
    }
  });

await importWorkflow.execute(context);
```

### 2. StateManager Integration

StateManager persists CLI state across sessions:

```typescript
// Save active connection
await stateManager.setState('db.active', connectionName);

// Save query history
await stateManager.setState('query.history', queries);

// Save user preferences
await stateManager.setState('preferences', {
  defaultFormat: 'json',
  autoConfirm: false,
  maxRows: 100
});

// Restore state on CLI startup
const activeConnection = await stateManager.getState('db.active');
const queryHistory = await stateManager.getState('query.history');
```

### 3. ErrorHandler Integration

ErrorHandler provides graceful error recovery:

```typescript
try {
  await queryExecutor.execute(sql);
} catch (error) {
  const handled = await errorHandler.handle(error, {
    context: 'query-execution',
    sql,
    connection: connectionInfo
  });

  if (handled.recoverable) {
    // Suggest recovery action
    console.log(`Error: ${handled.message}`);
    console.log(`Suggestion: ${handled.suggestion}`);

    if (handled.autoRetry) {
      console.log('Retrying...');
      return await queryExecutor.execute(sql);
    }
  } else {
    // Fatal error
    throw handled.error;
  }
}
```

### 4. AsyncPipeline Integration

AsyncPipeline handles streaming large result sets:

```typescript
// Stream large query results
const pipeline = new AsyncPipeline<Row>()
  .source(async function* () {
    yield* queryExecutor.executeStream(sql);
  })
  .transform(async function* (row) {
    yield formatter.formatRow(row);
  })
  .batch(1000)
  .sink(async (batch) => {
    await outputWriter.write(batch);
  });

await pipeline.execute();
```

### 5. MCP Client Integration

MCP Client provides LLM capabilities:

```typescript
// Natural language to SQL translation
const response = await mcpClient.callTool('nl-to-sql', {
  query: nlQuery,
  schema: schemaInfo,
  databaseType: 'postgres',
  examples: queryHistory
});

// Schema exploration
const relevantTables = await mcpClient.callTool('identify-tables', {
  query: "tables related to users",
  allTables: schema.tables
});

// Query optimization
const optimized = await mcpClient.callTool('optimize-query', {
  sql: originalQuery,
  schema: schemaInfo,
  executionPlan: currentPlan
});
```

---

## Security and Safety

### 1. Query Validation

**Destructive Operation Detection**:
```typescript
const destructivePatterns = {
  DROP: /DROP\s+(TABLE|DATABASE|INDEX|VIEW)/i,
  TRUNCATE: /TRUNCATE\s+TABLE/i,
  DELETE: /DELETE\s+FROM/i,
  UPDATE: /UPDATE\s+\w+\s+SET/i,
  ALTER: /ALTER\s+TABLE/i
};

function isDestructive(sql: string): DestructiveInfo {
  for (const [type, pattern] of Object.entries(destructivePatterns)) {
    if (pattern.test(sql)) {
      return {
        isDestructive: true,
        type,
        requiresConfirmation: true,
        warningMessage: `This query will ${type} data.`
      };
    }
  }
  return { isDestructive: false };
}
```

**SQL Injection Prevention**:
```typescript
function validateSQL(sql: string): ValidationResult {
  const warnings: string[] = [];

  // Check for multiple statements
  if (sql.includes(';') && sql.split(';').length > 2) {
    warnings.push('Multiple SQL statements detected');
  }

  // Check for comments that might hide malicious code
  if (/--|\*\/|\*\*/g.test(sql)) {
    warnings.push('SQL comments detected');
  }

  // Check for union-based injection
  if (/UNION.*SELECT/i.test(sql)) {
    warnings.push('UNION SELECT detected - verify legitimacy');
  }

  return {
    valid: warnings.length === 0,
    warnings
  };
}
```

### 2. Connection Security

**SSL/TLS Enforcement**:
```typescript
interface ConnectionConfig {
  ssl?: boolean | {
    rejectUnauthorized: boolean;
    ca?: string;
    key?: string;
    cert?: string;
  };
}

// Enforce SSL for production
if (connectionName.includes('prod') && !config.ssl) {
  throw new Error('SSL required for production connections');
}
```

**Password Management**:
```typescript
// Never store passwords in plain text
async function saveConnection(config: ConnectionConfig): Promise<void> {
  const encrypted = await encryptPassword(config.password);

  await configStore.save({
    ...config,
    password: encrypted,
    passwordEncrypted: true
  });
}

// Use secure password prompts
async function promptPassword(): Promise<string> {
  return await prompt({
    type: 'password',
    message: 'Enter password:',
    mask: '*'
  });
}
```

### 3. Audit Logging

**Operation Logging**:
```typescript
interface AuditLog {
  timestamp: Date;
  user: string;
  operation: string;
  sql?: string;
  connection: string;
  success: boolean;
  duration: number;
  rowsAffected?: number;
}

async function logOperation(info: AuditLog): Promise<void> {
  await auditLogger.log({
    ...info,
    timestamp: new Date(),
    user: os.userInfo().username
  });
}
```

### 4. Read-Only Mode

```typescript
class ReadOnlyConnection implements Connection {
  async execute(sql: string): Promise<QueryResult> {
    if (this.isWriteOperation(sql)) {
      throw new Error(
        'Write operations not allowed in read-only mode'
      );
    }
    return await this.connection.execute(sql);
  }

  private isWriteOperation(sql: string): boolean {
    const writeKeywords = [
      'INSERT', 'UPDATE', 'DELETE', 'DROP',
      'CREATE', 'ALTER', 'TRUNCATE'
    ];
    const upperSQL = sql.toUpperCase();
    return writeKeywords.some(kw => upperSQL.includes(kw));
  }
}
```

### 5. Transaction Safety

```typescript
async function executeWithRollback<T>(
  fn: (tx: Transaction) => Promise<T>
): Promise<T> {
  const tx = await connection.beginTransaction();

  try {
    const result = await fn(tx);
    await tx.commit();
    return result;
  } catch (error) {
    await tx.rollback();
    throw error;
  }
}
```

---

## Implementation Plan

### Phase 1: Foundation (Weeks 1-2)

**Priority: Critical**

1. **CLI Framework Setup**
   - Command parser implementation
   - Option validation
   - Output formatter
   - Progress indicators
   - **Deliverable**: Basic CLI structure with help system

2. **DatabaseManager Implementation**
   - Connection pool
   - PostgreSQL driver integration
   - MySQL driver integration
   - Configuration storage
   - **Deliverable**: Multi-database connection management

3. **Basic Query Execution**
   - Query executor
   - Result formatting
   - Error handling
   - **Deliverable**: Raw SQL execution capability

**Success Criteria**:
- Can connect to PostgreSQL and MySQL
- Can execute basic SQL queries
- Proper error handling and reporting

---

### Phase 2: Natural Language Core (Weeks 3-4)

**Priority: Critical**

1. **NLQueryEngine Implementation**
   - MCP client integration
   - Prompt engineering for SQL generation
   - Query validation
   - Confidence scoring
   - **Deliverable**: NL to SQL translation

2. **SchemaInspector Implementation**
   - Schema introspection
   - Relevant schema extraction
   - Schema caching
   - **Deliverable**: Schema-aware query translation

3. **Query Safety System**
   - Destructive operation detection
   - Confirmation prompts
   - Dry-run mode
   - **Deliverable**: Safe NL query execution

**Success Criteria**:
- Can translate 80%+ of common queries correctly
- Properly identifies destructive operations
- Schema context improves translation accuracy

---

### Phase 3: Advanced Features (Weeks 5-6)

**Priority: High**

1. **Schema Exploration**
   - Natural language schema search
   - Table relationship visualization
   - Schema diagram generation
   - **Deliverable**: Interactive schema exploration

2. **Data Operations**
   - CSV/JSON import
   - Data export functionality
   - Backup/restore
   - **Deliverable**: Data management tools

3. **Migration System**
   - Migration plan generation
   - Migration execution
   - Rollback capability
   - Migration history tracking
   - **Deliverable**: Schema migration management

**Success Criteria**:
- Can import/export data in multiple formats
- Can generate and execute migrations safely
- Schema diagrams are accurate and useful

---

### Phase 4: Performance & Monitoring (Weeks 7-8)

**Priority: Medium**

1. **PerformanceMonitor Implementation**
   - Real-time metrics collection
   - Slow query logging
   - Query analysis
   - **Deliverable**: Performance monitoring dashboard

2. **Query Optimization**
   - Execution plan analysis
   - Index recommendations
   - Query rewriting suggestions
   - **Deliverable**: Intelligent query optimization

3. **Streaming & Large Datasets**
   - Result streaming
   - AsyncPipeline integration
   - Memory-efficient processing
   - **Deliverable**: Handle datasets of any size

**Success Criteria**:
- Can monitor database performance in real-time
- Provides actionable optimization recommendations
- Handles multi-GB result sets efficiently

---

### Phase 5: Polish & Extended Support (Weeks 9-10)

**Priority: Low**

1. **Additional Database Support**
   - SQLite driver
   - MongoDB driver (NoSQL)
   - SQL Server driver
   - **Deliverable**: Support for 5+ database types

2. **Advanced CLI Features**
   - Interactive mode
   - Command history
   - Auto-completion
   - Configuration management
   - **Deliverable**: Enhanced user experience

3. **Documentation & Examples**
   - User guide
   - API documentation
   - Example workflows
   - Video tutorials
   - **Deliverable**: Comprehensive documentation

**Success Criteria**:
- Supports 5+ major database systems
- Interactive mode improves productivity
- Documentation enables self-service adoption

---

## Architecture Decision Records

### ADR-001: LLM Provider for NL Translation

**Status**: Accepted
**Date**: 2025-10-27

**Context**:
We need to translate natural language queries to SQL. Options include:
1. Rule-based parsing
2. Local ML model
3. Cloud LLM via MCP

**Decision**:
Use Claude via MCP client for NL-to-SQL translation.

**Rationale**:
- **Accuracy**: Claude excels at code generation and structured output
- **Context**: Can provide schema information for better translations
- **Flexibility**: Handles complex queries and edge cases
- **Integration**: Already have MCP infrastructure
- **Cost**: Pay-per-use vs. hosting ML model

**Consequences**:
- Requires internet connectivity
- API costs scale with usage
- Need fallback for offline mode
- Must handle rate limiting

**Alternatives Considered**:
- Local model (Llama, CodeLlama): Lower accuracy, requires GPU
- Rule-based: Limited flexibility, high maintenance

---

### ADR-002: Connection Pool vs. Single Connection

**Status**: Accepted
**Date**: 2025-10-27

**Context**:
CLI may need to interact with multiple databases simultaneously.

**Decision**:
Implement connection pool with single active connection pattern.

**Rationale**:
- **Resource Efficiency**: Reuse connections, avoid overhead
- **Multi-DB Support**: Switch between databases easily
- **Health Checking**: Monitor connection health proactively
- **Graceful Degradation**: Reconnect on failure

**Consequences**:
- More complex connection management
- Need state persistence for active connection
- Must handle pool size limits

**Alternatives Considered**:
- Single connection: Simpler but less flexible
- Multiple active connections: Higher resource usage

---

### ADR-003: Result Streaming for Large Datasets

**Status**: Accepted
**Date**: 2025-10-27

**Context**:
Queries may return millions of rows, causing memory issues.

**Decision**:
Implement streaming result processing using AsyncIterator pattern.

**Rationale**:
- **Memory Efficiency**: Process rows incrementally
- **Responsiveness**: Show results as they arrive
- **Scalability**: Handle datasets of any size
- **Integration**: Works with AsyncPipeline

**Consequences**:
- More complex result handling
- Some operations (sorting, aggregation) require buffering
- Need proper cursor management

**Alternatives Considered**:
- Buffer all results: Simple but memory-intensive
- Pagination: Requires multiple queries

---

### ADR-004: Migration Storage Format

**Status**: Accepted
**Date**: 2025-10-27

**Context**:
Need to store migration files for version control and execution.

**Decision**:
Use versioned SQL files with up/down sections.

**Rationale**:
- **Simplicity**: Plain SQL, no DSL to learn
- **Version Control**: Works with Git
- **Portability**: Can execute outside CLI
- **Transparency**: Clear what will execute

**Format**:
```sql
-- Migration: add_email_verification_to_users
-- Version: 20251027053300
-- Description: Add email verification columns

-- Up Migration
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
-- Down Migration
ALTER TABLE users DROP COLUMN email_verified;
```

**Consequences**:
- Manual SQL editing required
- Database-specific syntax needed
- Less abstraction than ORM migrations

**Alternatives Considered**:
- JSON format: Less readable, harder to execute manually
- DSL (like Knex): Additional learning curve

---

### ADR-005: Safety Confirmation UX

**Status**: Accepted
**Date**: 2025-10-27

**Context**:
Destructive operations require user confirmation to prevent accidents.

**Decision**:
Implement multi-level confirmation based on operation severity.

**Confirmation Levels**:
1. **None**: SELECT queries
2. **Soft**: UPDATE, INSERT (show affected rows)
3. **Hard**: DELETE, TRUNCATE (require typing confirmation)
4. **Critical**: DROP (require connection name + typing "DELETE")

**Example**:
```bash
$ ai-shell query "delete all spam comments"

⚠️  DESTRUCTIVE OPERATION DETECTED
Query will DELETE data from table: comments

Generated SQL:
  DELETE FROM comments WHERE is_spam = true

Estimated affected rows: 1,247

Type 'DELETE' to confirm: DELETE
✓ Query executed (1,247 rows deleted in 234ms)
```

**Rationale**:
- **Progressive Safety**: More dangerous = more confirmation
- **Clear Communication**: Show what will happen
- **Override Available**: --force flag for automation
- **Muscle Memory Prevention**: Typing requirement prevents accidental confirms

**Consequences**:
- Extra steps for destructive operations
- Need --force flag for scripts/automation
- Must clearly communicate impact

**Alternatives Considered**:
- Always require confirmation: Too intrusive
- Never require confirmation: Too dangerous
- Yes/No prompts only: Too easy to confirm accidentally

---

## Technology Evaluation Matrix

### Database Drivers

| Driver | Pros | Cons | Score |
|--------|------|------|-------|
| **node-postgres (pg)** | Mature, well-documented, connection pooling | PostgreSQL only | 9/10 |
| **mysql2** | Fast, supports prepared statements | MySQL only | 9/10 |
| **better-sqlite3** | Synchronous API, very fast | SQLite only, Node native module | 8/10 |
| **mongodb** | Official driver, feature-complete | NoSQL different paradigm | 8/10 |
| **tedious** | SQL Server support | Complex configuration | 7/10 |

**Decision**: Use driver-specific libraries for best performance and features.

---

### CLI Framework

| Framework | Pros | Cons | Score |
|-----------|------|------|-------|
| **Commander.js** | Simple, widely used, good docs | Limited advanced features | 8/10 |
| **Yargs** | Rich features, command builder | Larger bundle size | 8/10 |
| **oclif** | Full CLI framework, plugins | Heavyweight for our needs | 7/10 |
| **Custom** | Full control, minimal deps | More development time | 6/10 |

**Decision**: Use Commander.js for simplicity and community support.

---

### Result Formatting

| Library | Pros | Cons | Score |
|---------|------|------|-------|
| **cli-table3** | Beautiful tables, customizable | Limited streaming | 9/10 |
| **chalk** | Color support, widely used | Just colors, need table lib | 8/10 |
| **ora** | Great spinners/progress | Just progress indicators | 8/10 |
| **blessed** | Full TUI framework | Overkill for CLI | 6/10 |

**Decision**: Use cli-table3 + chalk + ora for rich formatting.

---

## Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **LLM Translation Accuracy** | Medium | High | Implement confidence scoring, allow SQL editing, maintain query history for learning |
| **Connection Pool Exhaustion** | Low | Medium | Implement connection limits, health checking, automatic cleanup |
| **Large Result Set Memory** | Medium | High | Implement streaming, pagination, row limits |
| **Database-Specific SQL Syntax** | High | Medium | Abstract common patterns, maintain dialect-specific templates |
| **Security Vulnerabilities** | Medium | Critical | Implement input validation, SQL injection prevention, audit logging |

### Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Destructive Operations** | Low | Critical | Multi-level confirmations, dry-run mode, audit logging |
| **Connection Failures** | Medium | Medium | Auto-reconnect, health checking, graceful degradation |
| **Performance Degradation** | Medium | Medium | Query timeouts, resource limits, monitoring |

---

## Success Metrics

### Functionality Metrics
- **Translation Accuracy**: >80% correct SQL generation
- **Query Success Rate**: >95% successful executions
- **Response Time**: <2s for query translation
- **Database Coverage**: Support 5+ database types

### User Experience Metrics
- **Learning Curve**: Users productive in <30 minutes
- **Error Recovery**: <5% queries require manual SQL editing
- **Safety**: Zero accidental data loss incidents
- **Documentation**: >90% user questions answered by docs

### Performance Metrics
- **Memory Usage**: <100MB for typical operations
- **Large Datasets**: Handle 1M+ rows without crashes
- **Connection Overhead**: <500ms connection establishment
- **Query Throughput**: >100 queries/minute

---

## Future Enhancements

### Phase 6: AI Features (Future)
- Query optimization via RL
- Anomaly detection in query patterns
- Predictive schema changes
- Auto-indexing recommendations

### Phase 7: Collaboration (Future)
- Shared connection configurations
- Query snippet sharing
- Team query history
- Access control and audit trails

### Phase 8: Advanced Analytics (Future)
- Built-in data visualization
- Report generation
- Scheduled query execution
- Data quality checks

---

## Conclusion

This architecture provides a comprehensive foundation for building a natural language database administration CLI that is:

1. **Accessible**: Natural language interface removes SQL knowledge barrier
2. **Safe**: Multi-layered safety checks prevent accidental data loss
3. **Efficient**: Connection pooling and streaming handle scale
4. **Extensible**: Plugin architecture for new databases and features
5. **Integrated**: Leverages existing AIShell components

The phased implementation plan ensures we deliver core value early while progressively adding advanced features. The architecture is designed for maintainability, testability, and future growth.

**Next Steps**:
1. Review and approve architecture
2. Set up project structure
3. Begin Phase 1 implementation
4. Establish testing strategy
5. Create user documentation

---

**Document History**:
- 2025-10-27: Initial architecture design (v1.0.0)
