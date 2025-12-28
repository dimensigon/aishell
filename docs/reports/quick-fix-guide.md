# Quick Fix Guide - TypeScript Errors

This guide provides immediate fixes for the remaining 71 TypeScript errors.

## Priority 1: Database Connection Type Guards (33 errors)

### Problem
Union types `Pool | MongoClient | Redis | Database` don't have a discriminant field, causing property access errors.

### Solution: Add Type Guard Utilities

Create `/home/claude/AIShell/aishell/src/cli/utils/db-type-guards.ts`:

```typescript
import { Pool as PgPool } from 'pg';
import { Pool as MySQLPool } from 'mysql2/promise';
import { MongoClient } from 'mongodb';
import { Redis } from 'ioredis';
import { Database as SQLiteDB } from 'sqlite3';

export type DatabaseConnection = PgPool | MySQLPool | MongoClient | Redis | SQLiteDB;

export function isPostgresPool(conn: DatabaseConnection): conn is PgPool {
  return 'query' in conn && 'connect' in conn && !('db' in conn);
}

export function isMySQLPool(conn: DatabaseConnection): conn is MySQLPool {
  return 'query' in conn && 'execute' in conn;
}

export function isMongoClient(conn: DatabaseConnection): conn is MongoClient {
  return 'db' in conn && 'topology' in conn;
}

export function isRedisClient(conn: DatabaseConnection): conn is Redis {
  return 'get' in conn && 'set' in conn && 'options' in conn;
}

export function isSQLiteDB(conn: DatabaseConnection): conn is SQLiteDB {
  return 'all' in conn && 'run' in conn && !('query' in conn);
}
```

### Usage Example

**Before (Error):**
```typescript
const result = await connection.query('SELECT * FROM users');
// Error: Property 'query' does not exist on type 'Pool | MongoClient | Redis | Database'
```

**After (Fixed):**
```typescript
import { isPostgresPool, isMySQLPool, isMongoClient, isSQLiteDB } from './utils/db-type-guards';

if (isPostgresPool(connection) || isMySQLPool(connection)) {
  const result = await connection.query('SELECT * FROM users');
} else if (isMongoClient(connection)) {
  const result = await connection.db().collection('users').find().toArray();
} else if (isSQLiteDB(connection)) {
  const result = await new Promise((resolve, reject) => {
    connection.all('SELECT * FROM users', (err, rows) => {
      if (err) reject(err);
      else resolve(rows);
    });
  });
}
```

### Files to Update

1. **src/cli/backup-system.ts** (7 errors, lines 87, 95, 120, 131, 138, 165, 225)
2. **src/cli/query-federation.ts** (5 errors)
3. **src/cli/query-optimizer.ts** (5 errors)
4. **src/cli/sql-explainer.ts** (8 errors)
5. **src/cli/migration-tester.ts** (4 errors)
6. **src/cli/monitoring-cli.ts** (4 errors)

---

## Priority 2: Undefined Value Handling (11 errors)

### Problem: `string | undefined` not assignable to `string`

### Fix Pattern 1: Add Null Check
```typescript
// Before (Error)
function processPath(path: string | undefined) {
  fs.writeFile(path, data); // Error: Argument of type 'string | undefined' not assignable
}

// After (Fixed)
function processPath(path: string | undefined) {
  if (!path) {
    throw new Error('Path is required');
  }
  fs.writeFile(path, data); // OK: path is string
}
```

### Fix Pattern 2: Use Default Value
```typescript
// Before (Error)
const config = options.config; // string | undefined
loadConfig(config); // Error

// After (Fixed)
const config = options.config || '/default/config.json';
loadConfig(config); // OK
```

### Fix Pattern 3: Use Non-Null Assertion (only if guaranteed)
```typescript
// Use only when you're certain value exists
const config = options.config!;
loadConfig(config); // OK but risky
```

### Files to Fix

1. **src/cli/backup-system.ts:95**
   ```typescript
   // Current
   await fs.mkdir(path.dirname(destination));

   // Fix
   if (!destination) {
     throw new Error('Backup destination is required');
   }
   await fs.mkdir(path.dirname(destination));
   ```

2. **src/cli/migration-tester.ts:411**
   ```typescript
   // Current
   await fs.writeFile(reportPath, reportContent);

   // Fix
   const finalPath = reportPath || './migration-report.json';
   await fs.writeFile(finalPath, reportContent);
   ```

3. **src/cli/sso-cli.ts:416**
4. **src/cli/sso-manager.ts:558**
5. **src/mcp/database-server.ts:266**

---

## Priority 3: Unknown Type Assertions (4 errors)

### Problem: `unknown` not assignable to specific types

### Fix: Add Type Assertions

**src/cli/sso-manager.ts** (4 occurrences: lines 194, 243, 854, 902)

```typescript
// Before (Error)
logger.error('SSO error', error); // error is unknown

// After (Fixed)
logger.error('SSO error', error as LogMetadata);

// Or better, with type checking
logger.error('SSO error',
  typeof error === 'object' && error !== null ? error as LogMetadata : { message: String(error) }
);
```

---

## Priority 4: Inquirer Type Issues (8 errors)

### Problem: Inquirer question format mismatch

**Files:** src/cli/query-builder-cli.ts (lines 323, 363, 436, 637)

### Fix: Correct Question Format

```typescript
// Before (Error)
const answers = await inquirer.prompt([
  {
    type: 'checkbox',
    name: 'columns',
    message: 'Select columns',
    choices: columnNames,
    validate: (input: string[]) => input.length > 0 || 'Select at least one column'
  }
]);

// After (Fixed)
const answers = await inquirer.prompt([
  {
    type: 'checkbox',
    name: 'columns',
    message: 'Select columns',
    choices: columnNames,
    validate: (input: string[]) => {
      return input.length > 0 ? true : 'Select at least one column';
    }
  }
]);
```

---

## Priority 5: Missing Properties/Methods (11 errors)

### Issue 1: Missing getInstance method

**src/cli/monitoring-cli.ts:632**
```typescript
// Current (Error)
const stateManager = StateManager.getInstance();

// Fix - Check StateManager class definition
// If singleton pattern is intended, add:
private static instance: StateManager;
public static getInstance(): StateManager {
  if (!StateManager.instance) {
    StateManager.instance = new StateManager();
  }
  return StateManager.instance;
}
```

### Issue 2: Missing setActive method

**src/cli/monitoring-cli.ts:656**
```typescript
// Current (Error)
connectionManager.setActive(activeConnection.id);

// Fix - Use correct method name
connectionManager.setActiveConnection(activeConnection.id);
// Or add setActive method to DatabaseConnectionManager
```

### Issue 3: Missing validateQuery method

**src/cli/feature-commands.ts:76**
```typescript
// Current (Error)
const isValid = optimizer.validateQuery(query);

// Fix
const optimizationResult = optimizer.analyzeQuery(query);
const isValid = optimizationResult.isOptimizable;
```

### Issue 4: Missing explainQuery method

**src/cli/feature-commands.ts:510**
```typescript
// Current (Error)
const explanation = explainer.explainQuery(query);

// Fix - Use correct method
const explanation = await explainer.explain(query, connection);
```

### Issue 5: Incorrect argument count

**src/cli/index.ts:354**
```typescript
// Current (Error)
const cli = new OptimizationCLI(connectionManager);

// Fix
const cli = new OptimizationCLI();
// Or update constructor to accept parameter
```

**src/cli/index.ts:1810**
```typescript
// Current (Error)
getLazyCLI('optimization', optimizationCLI)

// Fix
getLazyCLI('optimization', () => optimizationCLI)
```

**src/cli/optimization-cli.ts:153**
```typescript
// Current (Error)
const result = optimizer.optimize(query);

// Fix
const result = await optimizer.optimize(query, connection);
```

---

## Priority 6: Type Mismatches (4 errors)

### Issue 1: Table type mismatch

**src/cli/integration-cli.ts:853**
```typescript
// Current (Error)
table.push([
  'Status',
  connection.isActive ? chalk.green('Active') : chalk.gray('Inactive')
]);

// Fix - Ensure all rows have same structure
table.push([
  ['Status'],
  [connection.isActive ? chalk.green('Active') : chalk.gray('Inactive')]
]);

// Or flatten nested arrays
table.push([
  'Status',
  String(connection.isActive ? chalk.green('Active') : chalk.gray('Inactive'))
]);
```

### Issue 2: Wrong result type

**src/cli/optimization-cli.ts:661**
```typescript
// Current (Error)
displayOptimizationResult(translationResult); // TranslationResult not OptimizationResult

// Fix
const optimizationResult: OptimizationResult = {
  originalQuery: translationResult.naturalLanguage,
  optimizedQuery: translationResult.sql,
  improvementPercent: 0,
  estimatedTimeSavings: 0,
  recommendations: ['Query translated from natural language'],
  explanation: translationResult.explanation
};
displayOptimizationResult(optimizationResult);
```

### Issue 3: Undefined assignment

**src/cli/mongodb-cli.ts:239**
```typescript
// Current (Error)
let authSource: string | null = options.authSource;

// Fix
let authSource: string | null = options.authSource ?? null;
```

### Issue 4: Block array type

**src/cli/notification-slack.ts:256**
```typescript
// Current (Error)
const blocks: (Block | KnownBlock)[] = buildBlocks();

// Fix
const blocks: (Block | KnownBlock)[] = buildBlocks() || [];
```

---

## Priority 7: Other Issues (6 errors)

### Missing Initializer (TS2564)

**src/cli/migration-dsl.ts:74**
```typescript
// Current (Error)
private currentPhase: string;

// Fix
private currentPhase: string = 'initial';
// Or in constructor
constructor() {
  this.currentPhase = 'initial';
}
```

### Duplicate Identifier (TS2552, TS2576, TS2614)

These require checking for duplicate declarations in the same scope.

**src/cli/sso-manager.ts** - Check for:
- Duplicate variable names
- Duplicate function names
- Conflicting imports

---

## Quick Command Reference

```bash
# Check TypeScript errors
npm run typecheck 2>&1 | grep "error TS"

# Count errors by type
npm run typecheck 2>&1 | grep "error TS" | sed 's/.*error //' | cut -d: -f1 | sort | uniq -c

# Check specific file
npx tsc --noEmit src/cli/backup-system.ts

# Run tests
npm test

# Run specific test file
npm test tests/unit/queue.test.ts

# Check test coverage
npm run test:coverage
```

---

## Estimated Fix Times

| Priority | Issue | Files | Errors | Time |
|----------|-------|-------|--------|------|
| P1 | Database type guards | 6 | 33 | 3-4h |
| P2 | Undefined handling | 5 | 11 | 1-2h |
| P3 | Unknown assertions | 1 | 4 | 30m |
| P4 | Inquirer types | 1 | 8 | 1h |
| P5 | Missing methods | 4 | 11 | 2h |
| P6 | Type mismatches | 4 | 4 | 1h |
| P7 | Other | 1 | 6 | 30m |
| **Total** | | **22** | **77** | **9-11h** |

---

## Testing After Fixes

After fixing TypeScript errors, verify:

1. **TypeScript Compilation**
   ```bash
   npm run build
   ```

2. **Run All Tests**
   ```bash
   npm test
   ```

3. **Check ESLint** (after fixing plugin)
   ```bash
   npm run lint
   ```

4. **Verify No Regressions**
   ```bash
   npm run typecheck
   # Should show 0 errors
   ```

---

## Success Criteria

✅ TypeScript errors: 71 → 0
✅ Build succeeds without warnings
✅ All tests pass
✅ ESLint shows no errors
✅ Code quality: 8.7/10 → 9.0/10

---

**Created:** 2025-10-29
**Last Updated:** 2025-10-29
**Status:** Ready for implementation
