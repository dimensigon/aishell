# Phase 4 Day 1 Analysis - High-Priority Test Failures

**Generated**: October 29, 2025
**Sprint**: Phase 4 - Day 1 Target Systems
**Analyst**: Code Analyzer Agent
**Test Run**: npm test @ 12:10 UTC

---

## Executive Summary

**Day 1 Focus**: Two critical systems requiring immediate attention:
1. **Error Handler Mocks** (37 failing tests) - CRITICAL
2. **Backup CLI** (18+ failing tests) - HIGH PRIORITY

**Total Impact**: 55+ failing tests
**Estimated Fix Time**: 6-8 hours
**Risk Level**: HIGH (core functionality broken)

---

## System 1: Error Handler Mocks (CRITICAL)

### Overview
- **File**: `/home/claude/AIShell/aishell/tests/unit/error-handler.test.ts`
- **Failed Tests**: 37/37 (100% failure rate)
- **Impact**: CRITICAL - All error handler tests failing
- **Root Cause**: Test expects different MCPErrorHandler interface than implemented

### Exact Failures

#### Failure Pattern 1: Missing Methods (35 tests)
**Error**: `TypeError: errorHandler.<method> is not a function`

**Missing Methods**:
1. `classify(error)` - 8 tests failing
2. `executeWithRetry(operation)` - 5 tests failing
3. `getSuggestions(mcpError)` - 4 tests failing
4. `formatError(error, context?)` - 4 tests failing
5. `track(error, context?)` - 4 tests failing
6. `getStats()` - 4 tests failing
7. `resetStats()` - 1 test failing
8. `addCustomHandler(errorType, handler)` - 2 tests failing
9. `handle(error)` - 2 tests failing
10. `getErrorChain(error)` - 1 test failing
11. `getAggregatedErrors()` - 3 tests failing

#### Failure Pattern 2: Wrong Constructor Signature
**Current Implementation** (`/home/claude/AIShell/aishell/src/mcp/error-handler.ts`):
```typescript
// No constructor options - extends EventEmitter
export class MCPErrorHandler extends EventEmitter<ErrorHandlerEvents> {
  private errorHistory: ErrorEvent[] = [];
  private maxHistorySize = 100;
}
```

**Test Expects**:
```typescript
errorHandler = new MCPErrorHandler({
  maxRetries: 3,
  retryDelay: 100,
  backoffMultiplier: 2,
});
```

### Root Cause Analysis

#### Issue 1: Interface Mismatch
The test file expects a **test-oriented error handler** with methods for:
- Error classification by type
- Retry logic execution
- Error statistics tracking
- Custom error handlers
- Error formatting and sanitization

The implementation provides an **event-driven error handler** with:
- Error event emission
- Recovery strategy determination
- Error history tracking
- Severity classification

#### Issue 2: Test File Defines Own Types
Lines 467-483 in test file:
```typescript
export enum ErrorCode {
  CONNECTION_ERROR = 'CONNECTION_ERROR',
  TIMEOUT = 'TIMEOUT',
  PARSE_ERROR = 'PARSE_ERROR',
  AUTH_ERROR = 'AUTH_ERROR',
  PERMISSION_DENIED = 'PERMISSION_DENIED',
  NOT_FOUND = 'NOT_FOUND',
  RATE_LIMIT = 'RATE_LIMIT',
  UNKNOWN = 'UNKNOWN',
}

export interface MCPError extends Error {
  code: ErrorCode;
  retryable: boolean;
  cause?: Error;
  context?: Record<string, any>;
}
```

These types should be in `/home/claude/AIShell/aishell/src/mcp/types.ts` but are missing.

### Dependency Chain

**Must be fixed in this order**:
1. **First**: Define ErrorCode enum in `/home/claude/AIShell/aishell/src/mcp/types.ts`
2. **Second**: Extend MCPError interface to include `retryable` property
3. **Third**: Implement missing methods in MCPErrorHandler class
4. **Fourth**: Add constructor options support

### Detailed Fix Requirements

#### Fix 1: Update MCP Types (15 minutes)
**File**: `/home/claude/AIShell/aishell/src/mcp/types.ts`
**Location**: After line 70

**Add**:
```typescript
/**
 * Error Code Enumeration
 */
export enum ErrorCode {
  CONNECTION_ERROR = 'CONNECTION_ERROR',
  TIMEOUT = 'TIMEOUT',
  PARSE_ERROR = 'PARSE_ERROR',
  AUTH_ERROR = 'AUTH_ERROR',
  PERMISSION_DENIED = 'PERMISSION_DENIED',
  NOT_FOUND = 'NOT_FOUND',
  RATE_LIMIT = 'RATE_LIMIT',
  UNKNOWN = 'UNKNOWN',
  SERVER_ERROR = 'SERVER_ERROR',
  INTERNAL_ERROR = 'INTERNAL_ERROR',
  METHOD_NOT_FOUND = 'METHOD_NOT_FOUND',
  RESOURCE_NOT_FOUND = 'RESOURCE_NOT_FOUND',
}
```

**Modify** (line 66-70):
```typescript
export interface MCPError {
  code: number | string;  // Support both numeric and string codes
  message: string;
  data?: unknown;
  retryable?: boolean;    // ADD THIS
  cause?: Error;          // ADD THIS
  context?: Record<string, any>;  // ADD THIS
}
```

#### Fix 2: Implement Missing Methods (2-3 hours)
**File**: `/home/claude/AIShell/aishell/src/mcp/error-handler.ts`
**Location**: Add after line 400

**Required Method Implementations**:

```typescript
/**
 * Error Handler Configuration
 */
export interface ErrorHandlerConfig {
  maxRetries?: number;
  retryDelay?: number;
  backoffMultiplier?: number;
  verbose?: boolean;
  circuitBreaker?: {
    enabled: boolean;
    threshold: number;
    timeout: number;
  };
}

/**
 * Error Statistics
 */
export interface ErrorStats {
  totalErrors: number;
  errorsByType: Record<string, number>;
  errorsByServer: Record<string, number>;
}

export class MCPErrorHandler extends EventEmitter<ErrorHandlerEvents> {
  private errorHistory: ErrorEvent[] = [];
  private maxHistorySize = 100;
  private config: ErrorHandlerConfig;
  private stats: ErrorStats;
  private customHandlers: Map<string, (error: Error) => Error>;
  private circuitState: 'closed' | 'open' | 'half-open' = 'closed';
  private circuitFailureCount = 0;
  private circuitLastFailure = 0;

  constructor(config: ErrorHandlerConfig = {}) {
    super();
    this.config = {
      maxRetries: 3,
      retryDelay: 100,
      backoffMultiplier: 2,
      verbose: false,
      ...config,
    };
    this.stats = {
      totalErrors: 0,
      errorsByType: {},
      errorsByServer: {},
    };
    this.customHandlers = new Map();
  }

  /**
   * Classify error into MCP error type
   */
  classify(error: Error | null | undefined): MCPError {
    if (!error) {
      return {
        code: ErrorCode.UNKNOWN,
        message: 'Unknown error',
        retryable: false,
      };
    }

    const message = error.message || 'No error message';
    const lowerMessage = message.toLowerCase();

    let code: string;
    let retryable: boolean;

    // Connection errors
    if (lowerMessage.includes('connection') || lowerMessage.includes('econnrefused')) {
      code = ErrorCode.CONNECTION_ERROR;
      retryable = true;
    }
    // Timeout errors
    else if (lowerMessage.includes('timeout')) {
      code = ErrorCode.TIMEOUT;
      retryable = true;
    }
    // Parse errors
    else if (error instanceof SyntaxError || lowerMessage.includes('parse')) {
      code = ErrorCode.PARSE_ERROR;
      retryable = false;
    }
    // Authentication errors
    else if (lowerMessage.includes('auth') || lowerMessage.includes('unauthorized')) {
      code = ErrorCode.AUTH_ERROR;
      retryable = false;
    }
    // Permission errors
    else if (lowerMessage.includes('permission') || lowerMessage.includes('forbidden')) {
      code = ErrorCode.PERMISSION_DENIED;
      retryable = false;
    }
    // Not found errors
    else if (lowerMessage.includes('not found') || lowerMessage.includes('404')) {
      code = ErrorCode.NOT_FOUND;
      retryable = false;
    }
    // Rate limit errors
    else if (lowerMessage.includes('rate limit') || lowerMessage.includes('too many')) {
      code = ErrorCode.RATE_LIMIT;
      retryable = true;
    }
    // Default
    else {
      code = ErrorCode.UNKNOWN;
      retryable = false;
    }

    return {
      code,
      message,
      retryable,
      cause: (error as any).cause,
      data: (error as any).data,
    };
  }

  /**
   * Execute operation with retry logic
   */
  async executeWithRetry<T>(
    operation: () => Promise<T>,
    options?: Partial<ErrorHandlerConfig>
  ): Promise<T> {
    const config = { ...this.config, ...options };

    // Circuit breaker check
    if (this.config.circuitBreaker?.enabled && this.circuitState === 'open') {
      const timeSinceLastFailure = Date.now() - this.circuitLastFailure;
      if (timeSinceLastFailure < (this.config.circuitBreaker.timeout || 1000)) {
        throw new Error('Circuit breaker is open');
      }
      this.circuitState = 'half-open';
    }

    let lastError: Error | null = null;
    const maxRetries = config.maxRetries || 3;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        // Apply delay for retries
        if (attempt > 0) {
          const delay = (config.retryDelay || 100) * Math.pow(config.backoffMultiplier || 2, attempt - 1);
          await this.sleep(delay);
        }

        const result = await operation();

        // Success - reset circuit breaker
        if (this.config.circuitBreaker?.enabled) {
          this.circuitState = 'closed';
          this.circuitFailureCount = 0;
        }

        return result;
      } catch (error) {
        lastError = error as Error;
        const mcpError = this.classify(lastError);

        // Don't retry non-retryable errors
        if (!mcpError.retryable || attempt === maxRetries) {
          // Update circuit breaker on failure
          if (this.config.circuitBreaker?.enabled) {
            this.circuitFailureCount++;
            this.circuitLastFailure = Date.now();
            if (this.circuitFailureCount >= (this.config.circuitBreaker.threshold || 3)) {
              this.circuitState = 'open';
            }
          }
          break;
        }
      }
    }

    throw lastError || new Error('Operation failed');
  }

  /**
   * Get recovery suggestions for error
   */
  getSuggestions(mcpError: MCPError): string[] {
    const suggestions: string[] = [];

    switch (mcpError.code) {
      case ErrorCode.CONNECTION_ERROR:
        suggestions.push('Check network connectivity');
        suggestions.push('Verify server is running');
        suggestions.push('Check firewall settings');
        break;
      case ErrorCode.TIMEOUT:
        suggestions.push('Increase timeout value');
        suggestions.push('Check server responsiveness');
        suggestions.push('Verify network latency');
        break;
      case ErrorCode.AUTH_ERROR:
        suggestions.push('Verify credentials');
        suggestions.push('Check API key');
        suggestions.push('Ensure authentication token is valid');
        break;
      case ErrorCode.RATE_LIMIT:
        suggestions.push('Reduce request frequency');
        suggestions.push('Implement rate limiting');
        suggestions.push('Wait before retrying');
        break;
      case ErrorCode.PERMISSION_DENIED:
        suggestions.push('Check user permissions');
        suggestions.push('Verify access rights');
        suggestions.push('Contact administrator');
        break;
      case ErrorCode.NOT_FOUND:
        suggestions.push('Verify resource exists');
        suggestions.push('Check resource path');
        suggestions.push('Ensure resource ID is correct');
        break;
    }

    return suggestions;
  }

  /**
   * Format error with context
   */
  formatError(error: Error, context?: Record<string, any>): string {
    const mcpError = this.classify(error);
    let formatted = `[${mcpError.code}] ${mcpError.message}`;

    if (context) {
      try {
        const contextStr = JSON.stringify(context, null, 2);
        formatted += `\nContext: ${contextStr}`;
      } catch (e) {
        formatted += '\nContext: [Circular reference detected]';
      }
    }

    if (this.config.verbose && error.stack) {
      formatted += `\nStack trace:\n${error.stack}`;
    }

    // Sanitize sensitive information
    formatted = formatted.replace(/sk-ant-api03-[a-zA-Z0-9]+/g, '[REDACTED]');
    formatted = formatted.replace(/password[:\s]+[^\s,]+/gi, 'password: [REDACTED]');
    formatted = formatted.replace(/token[:\s]+[^\s,]+/gi, 'token: [REDACTED]');

    // Truncate if too long
    if (formatted.length > 1000) {
      formatted = formatted.substring(0, 997) + '...';
    }

    return formatted;
  }

  /**
   * Track error occurrence
   */
  track(error: Error, context?: { server?: string }): void {
    this.stats.totalErrors++;

    const mcpError = this.classify(error);
    const errorType = String(mcpError.code);

    this.stats.errorsByType[errorType] = (this.stats.errorsByType[errorType] || 0) + 1;

    if (context?.server) {
      this.stats.errorsByServer[context.server] =
        (this.stats.errorsByServer[context.server] || 0) + 1;
    }
  }

  /**
   * Get error statistics
   */
  getStats(): ErrorStats {
    return { ...this.stats };
  }

  /**
   * Reset error statistics
   */
  resetStats(): void {
    this.stats = {
      totalErrors: 0,
      errorsByType: {},
      errorsByServer: {},
    };
  }

  /**
   * Add custom error handler
   */
  addCustomHandler(errorType: string, handler: (error: Error) => Error): void {
    this.customHandlers.set(errorType, handler);
  }

  /**
   * Handle error with custom handler if available
   */
  handle(error: Error): Error {
    const mcpError = this.classify(error);
    const handler = this.customHandlers.get(String(mcpError.code));

    if (handler) {
      return handler(error);
    }

    return error;
  }

  /**
   * Get error chain (cause chain)
   */
  getErrorChain(error: Error): Error[] {
    const chain: Error[] = [];
    let current: Error | undefined = error;

    while (current) {
      chain.push(current);
      current = (current as any).cause;
    }

    return chain;
  }

  /**
   * Get aggregated error information
   */
  getAggregatedErrors(): Array<{ message: string; count: number; code: string }> {
    const aggregated = new Map<string, { message: string; count: number; code: string }>();

    for (const [code, count] of Object.entries(this.stats.errorsByType)) {
      aggregated.set(code, {
        message: `Error type: ${code}`,
        count,
        code,
      });
    }

    return Array.from(aggregated.values()).sort((a, b) => b.count - a.count);
  }

  // Keep existing methods...
}
```

#### Fix 3: Update Test Imports (5 minutes)
**File**: `/home/claude/AIShell/aishell/tests/unit/error-handler.test.ts`
**Location**: Line 8

**Change from**:
```typescript
import { MCPError, ErrorCode } from '../../src/mcp/types';
```

**To**:
```typescript
import { MCPError } from '../../src/mcp/types';
import { ErrorCode } from '../../src/mcp/types';
```

**Remove** lines 467-484 (duplicate type definitions)

### Testing Verification

After fixes, run:
```bash
npm test -- tests/unit/error-handler.test.ts
```

**Expected outcome**: All 37 tests pass

### Risk Assessment

**Risk Level**: HIGH
- Error handling is core infrastructure
- Affects all MCP operations
- Test coverage is comprehensive (37 tests)
- Implementation mismatch could indicate design issue

**Mitigation**:
- Implement methods incrementally
- Test after each method addition
- Ensure backward compatibility with existing code
- Review other files using MCPErrorHandler

---

## System 2: Backup CLI (HIGH PRIORITY)

### Overview
- **File**: `/home/claude/AIShell/aishell/src/cli/backup-cli.ts`
- **Test File**: `/home/claude/AIShell/aishell/tests/cli/backup-commands.test.ts`
- **Failed Tests**: 18+ tests
- **Impact**: HIGH - All backup/restore operations broken
- **Root Cause**: Database connection mocking issues and null safety

### Exact Failures

#### Failure Pattern 1: Backup Creation (9 tests failing)
**Error**: `Database connection not found: test_db`
**Location**: `/home/claude/AIShell/aishell/src/cli/backup-cli.ts:149`

**Affected Tests**:
1. should create SQL backup successfully
2. should create JSON backup
3. should create CSV backup
4. should create incremental backup (base)
5. should create incremental backup (incremental)
6. should create backup with verification
7. should create compressed backup
8. should handle backup creation failure (expected to fail)
9. should create backup with specific tables

**Log Pattern**:
```
2025-10-29 12:11:14.579 [info]: Creating backup {"database":"test_db","name":"test_backup"}
2025-10-29 12:11:14.589 [error]: Backup creation failed {"error":{"message":"Database connection not found: test_db"}}
```

#### Failure Pattern 2: Backup Restore (6+ tests failing)
**Error**: `TypeError: Cannot read properties of undefined (reading 'find')`
**Location**: `/home/claude/AIShell/aishell/src/cli/backup-cli.ts:201`

**Code at Line 200-201**:
```typescript
const backups = await this.backupManager.listBackups();
const backup = backups.find(b => b.id === backupId);
```

**Affected Tests**:
1. should restore backup successfully
2. should perform dry-run restore
3. should restore to different database
4. should fail restore for nonexistent backup
5. should restore with specific tables
6. should restore with drop existing tables

**Root Cause**: `this.backupManager.listBackups()` returns `undefined` instead of array

### Root Cause Analysis

#### Issue 1: Database Connection Mock Missing
**Location**: `/home/claude/AIShell/aishell/src/cli/backup-cli.ts:149`

```typescript
async createBackup(database: string, name: string, options: BackupOptions): Promise<BackupResult> {
  try {
    logger.info('Creating backup', { database, name });

    // Get database connection
    const connection = this.connectionPool.get(database);
    if (!connection) {
      throw new Error(`Database connection not found: ${database}`);  // LINE 149
    }
    // ...
}
```

**Problem**: Tests don't mock `connectionPool.get()` properly

#### Issue 2: BackupManager Returns Undefined
**Location**: `/home/claude/AIShell/aishell/src/cli/backup-cli.ts:200-201`

```typescript
async restoreBackup(backupId: string, options: RestoreOptions): Promise<void> {
  try {
    logger.info('Restoring backup', { backupId, options });

    // Find backup by ID
    const backups = await this.backupManager.listBackups();  // LINE 200 - Returns undefined
    const backup = backups.find(b => b.id === backupId);     // LINE 201 - CRASH
```

**Problem**: `listBackups()` doesn't return array, should default to `[]`

### Dependency Chain

**Must be fixed in this order**:
1. **First**: Add null safety to `restoreBackup()` method (prevents crash)
2. **Second**: Fix test mocks for `connectionPool` and `backupManager`
3. **Third**: Ensure `BackupManager.listBackups()` always returns array

### Detailed Fix Requirements

#### Fix 1: Add Null Safety (10 minutes)
**File**: `/home/claude/AIShell/aishell/src/cli/backup-cli.ts`
**Location**: Lines 200-201

**Change from**:
```typescript
const backups = await this.backupManager.listBackups();
const backup = backups.find(b => b.id === backupId);
```

**Change to**:
```typescript
const backups = (await this.backupManager.listBackups()) || [];
const backup = backups.find(b => b.id === backupId);
```

#### Fix 2: Fix Test Mocks (30 minutes)
**File**: `/home/claude/AIShell/aishell/tests/cli/backup-commands.test.ts`
**Location**: Test setup (beforeEach)

**Current issue**: Tests don't properly mock:
1. `connectionPool.get(database)` - must return mock connection
2. `backupManager.listBackups()` - must return array
3. `backupManager.createBackup()` - must return success result

**Required mock setup**:
```typescript
beforeEach(() => {
  // Mock connection pool
  const mockConnection = {
    query: vi.fn().mockResolvedValue({ rows: [] }),
    execute: vi.fn().mockResolvedValue([[], []]),
    end: vi.fn().mockResolvedValue(undefined),
  };

  const mockConnectionPool = {
    get: vi.fn().mockReturnValue(mockConnection),
    has: vi.fn().mockReturnValue(true),
  };

  // Mock backup manager
  const mockBackups: any[] = [];
  const mockBackupManager = {
    createBackup: vi.fn().mockImplementation(async (options) => {
      const backup = {
        id: `backup-${Date.now()}`,
        database: options.database,
        name: options.name,
        status: 'success',
        timestamp: new Date(),
        size: 1024,
      };
      mockBackups.push(backup);
      return backup;
    }),
    listBackups: vi.fn().mockImplementation(async () => {
      return [...mockBackups];  // Return copy of array
    }),
    getBackup: vi.fn().mockImplementation(async (id) => {
      return mockBackups.find(b => b.id === id);
    }),
    deleteBackup: vi.fn().mockImplementation(async (id) => {
      const index = mockBackups.findIndex(b => b.id === id);
      if (index >= 0) {
        mockBackups.splice(index, 1);
      }
    }),
  };

  backupCLI = new BackupCLI({
    connectionPool: mockConnectionPool as any,
    backupManager: mockBackupManager as any,
  });
});
```

#### Fix 3: Verify BackupManager Implementation (20 minutes)
**File**: Search for BackupManager class implementation

**Check**:
1. Does `listBackups()` method exist?
2. Does it return `Promise<Backup[]>`?
3. Does it handle empty case properly?

**Expected implementation**:
```typescript
class BackupManager {
  async listBackups(): Promise<Backup[]> {
    try {
      // Get backups from storage
      const backups = await this.storage.list();
      return backups || [];  // Ensure array is returned
    } catch (error) {
      logger.error('Failed to list backups', { error });
      return [];  // Return empty array on error
    }
  }
}
```

#### Fix 4: Add Defensive Checks Throughout (30 minutes)
**File**: `/home/claude/AIShell/aishell/src/cli/backup-cli.ts`

**Add checks in all methods**:

```typescript
async createBackup(database: string, name: string, options: BackupOptions): Promise<BackupResult> {
  try {
    // Validate inputs
    if (!database || !name) {
      throw new Error('Database and name are required');
    }

    // Check connection
    if (!this.connectionPool || !this.connectionPool.has(database)) {
      throw new Error(`Database connection not found: ${database}`);
    }

    const connection = this.connectionPool.get(database);
    if (!connection) {
      throw new Error(`Failed to get database connection: ${database}`);
    }

    // Create backup
    const result = await this.backupManager.createBackup({
      database,
      name,
      ...options,
    });

    return result || { status: 'failed', error: 'No result from backup manager' };
  } catch (error) {
    logger.error('Backup creation failed', { error });
    return {
      status: 'failed',
      error: error.message,
    };
  }
}
```

### Testing Verification

After fixes, run:
```bash
npm test -- tests/cli/backup-commands.test.ts
```

**Expected outcome**: All 18+ tests pass

### Risk Assessment

**Risk Level**: HIGH
- Backup/restore is critical for data protection
- Production impact if backups fail
- Null pointer errors can cause crashes

**Mitigation**:
- Add comprehensive null checks
- Improve test mocking
- Add integration tests with real database
- Document backup requirements

---

## Implementation Strategy

### Phase 1: Immediate Fixes (2 hours)
1. Add null safety to backup-cli.ts (10 min)
2. Update MCP types with ErrorCode enum (15 min)
3. Fix test mocks for backup CLI (30 min)
4. Implement core error handler methods (60 min)

### Phase 2: Complete Implementation (3 hours)
1. Implement all error handler methods (2 hours)
2. Add circuit breaker logic (30 min)
3. Add error aggregation (30 min)

### Phase 3: Testing & Validation (1 hour)
1. Run error handler tests (10 min)
2. Run backup CLI tests (10 min)
3. Fix any remaining issues (40 min)

### Phase 4: Code Review (1 hour)
1. Review all changes
2. Check for edge cases
3. Update documentation
4. Commit changes

---

## Code Examples for Coder Agents

### Example 1: Error Handler Constructor
```typescript
// Add to /home/claude/AIShell/aishell/src/mcp/error-handler.ts
constructor(config: ErrorHandlerConfig = {}) {
  super();
  this.config = {
    maxRetries: 3,
    retryDelay: 100,
    backoffMultiplier: 2,
    verbose: false,
    ...config,
  };
  this.stats = {
    totalErrors: 0,
    errorsByType: {},
    errorsByServer: {},
  };
  this.customHandlers = new Map();
}
```

### Example 2: Backup CLI Null Safety
```typescript
// Update /home/claude/AIShell/aishell/src/cli/backup-cli.ts:200
async restoreBackup(backupId: string, options: RestoreOptions): Promise<void> {
  try {
    logger.info('Restoring backup', { backupId, options });

    // Find backup by ID with null safety
    const backups = (await this.backupManager.listBackups()) || [];
    const backup = backups.find(b => b.id === backupId);

    if (!backup) {
      throw new Error(`Backup not found: ${backupId}`);
    }

    // Continue with restore...
  } catch (error) {
    logger.error('Restore failed', { error });
    throw error;
  }
}
```

### Example 3: Test Mock Setup
```typescript
// Update tests/cli/backup-commands.test.ts
beforeEach(() => {
  mockBackups = [];

  mockBackupManager = {
    listBackups: vi.fn().mockResolvedValue([]),
    createBackup: vi.fn().mockImplementation(async (opts) => {
      const backup = {
        id: `backup-${Date.now()}`,
        ...opts,
        status: 'success',
      };
      mockBackups.push(backup);
      return backup;
    }),
  };

  mockConnectionPool = {
    get: vi.fn().mockReturnValue(mockConnection),
    has: vi.fn().mockReturnValue(true),
  };
});
```

---

## Success Criteria

### Error Handler System
- [ ] All 37 tests pass
- [ ] ErrorCode enum defined in types.ts
- [ ] MCPError interface extended with retryable
- [ ] All 11 methods implemented
- [ ] Circuit breaker working
- [ ] Error aggregation working

### Backup CLI System
- [ ] All 18+ tests pass
- [ ] No null pointer exceptions
- [ ] Backup creation works with mocks
- [ ] Backup restore works with mocks
- [ ] listBackups() always returns array
- [ ] Error handling is robust

---

## File Reference

### Files to Modify
1. `/home/claude/AIShell/aishell/src/mcp/types.ts` - Add ErrorCode enum
2. `/home/claude/AIShell/aishell/src/mcp/error-handler.ts` - Implement methods
3. `/home/claude/AIShell/aishell/src/cli/backup-cli.ts` - Add null safety
4. `/home/claude/AIShell/aishell/tests/unit/error-handler.test.ts` - Remove duplicate types
5. `/home/claude/AIShell/aishell/tests/cli/backup-commands.test.ts` - Fix mocks

### Files to Review
1. Search for BackupManager implementation
2. Check connectionPool implementation
3. Review other files using MCPErrorHandler

---

## Estimated Timeline

| Task | Time | Priority |
|------|------|----------|
| Error Handler Types | 15 min | P0 |
| Null Safety Fixes | 10 min | P0 |
| Test Mock Setup | 30 min | P0 |
| Core Error Methods | 2 hours | P0 |
| Circuit Breaker | 30 min | P1 |
| Error Aggregation | 30 min | P1 |
| Testing & Validation | 1 hour | P0 |
| Code Review | 1 hour | P1 |
| **Total** | **6-8 hours** | - |

---

## Next Steps for Coder Agents

1. **Read this analysis completely**
2. **Start with Error Handler Types** (lowest risk)
3. **Add null safety to backup-cli.ts** (prevents crashes)
4. **Implement error handler methods** (core functionality)
5. **Fix test mocks** (enable testing)
6. **Run tests iteratively** (validate progress)
7. **Report blockers immediately**

---

**Report Complete**
**Ready for Agent Execution**
