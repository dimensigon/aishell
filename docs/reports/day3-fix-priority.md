# Day 3: Test Failure Fix Priority List

**Generated:** 2025-10-29
**Target:** Reach 95%+ pass rate with minimal effort
**Current Pass Rate:** 91.3% (1,948/2,133 tests passing)
**Target Pass Rate:** 95.0% (2,026/2,133 tests passing)
**Tests to Fix:** 78 minimum (Strategic: 134 HIGH priority)

---

## Quick Win Summary

| Fix Order | Issue | Tests Fixed | Estimated Time | Cumulative Pass Rate |
|-----------|-------|-------------|----------------|----------------------|
| 1 | DatabaseManager State | 60+ | 4-6 hours | 94.1% |
| 2 | Prometheus Mocks | 51+ | 6-8 hours | 96.5% |
| 3 | Security RBAC Setup | 13 | 4-6 hours | 97.1% |
| 4 | CLI Wrapper Init | 10 | 4-6 hours | 97.6% |

**Total Impact:** 134 tests fixed, 18-26 hours, 97.6% pass rate achieved

---

## Priority 1: INFRASTRUCTURE FIXES (Maximum Impact)

### Fix #1: DatabaseManager State Initialization
**Impact:** 60+ tests fixed with single root cause fix
**Priority:** CRITICAL - Unblocks all migration testing
**Estimated Time:** 4-6 hours
**Difficulty:** Medium-High

#### Affected Tests (60+)
**File:** `tests/cli/migration-engine-advanced.test.ts` (39 failures)
- Migration loading from YAML
- Execution plan generation
- Risk detection
- Multi-phase migration execution
- SQL generation (ADD COLUMN, DROP COLUMN, CREATE INDEX, BACKFILL)
- Column validation
- Rollback functionality
- Migration status tracking
- Safety verification
- Migration pattern building

**File:** `tests/cli/migration-runner.test.ts` (21 failures)
- Running pending migrations
- Limited migration runs
- Skipping executed migrations
- Batch tracking
- Error handling
- Rollback operations (down, reset, fresh, redo)
- Migration status display
- Transaction management
- Migrations tracking table
- JavaScript migration execution

#### Root Cause
```
Error: TypeError: Cannot read properties of undefined (reading 'findByMetadata')
Location: DatabaseManager state initialization
```

The DatabaseManager is attempting to call `state.findByMetadata()` but the state object is undefined or not properly initialized.

#### Fix Strategy
1. **Locate the Issue:**
   ```bash
   File: /home/claude/AIShell/aishell/src/database/database-manager.ts
   Search for: "findByMetadata"
   ```

2. **Check State Initialization:**
   - Verify state object is initialized in constructor
   - Ensure state has findByMetadata method
   - Check if state is loaded before being accessed

3. **Add Test Setup:**
   ```typescript
   // In test files
   beforeEach(async () => {
     await databaseManager.initializeState();
     // or
     await databaseManager.loadState();
   });
   ```

4. **Add Defensive Code:**
   ```typescript
   // In database-manager.ts
   if (!this.state) {
     this.state = this.createDefaultState();
   }
   ```

#### Files to Modify
- `/home/claude/AIShell/aishell/src/database/database-manager.ts`
- `/home/claude/AIShell/aishell/tests/cli/migration-engine-advanced.test.ts`
- `/home/claude/AIShell/aishell/tests/cli/migration-runner.test.ts`

#### Success Criteria
- All 39 migration-engine-advanced tests pass
- All 21 migration-runner tests pass
- No state-related errors in logs

---

### Fix #2: Prometheus Metrics Mock Implementation
**Impact:** 51+ tests fixed
**Priority:** CRITICAL - Required for production monitoring
**Estimated Time:** 6-8 hours
**Difficulty:** Medium

#### Affected Tests (51)
**File:** `tests/cli/prometheus-collector.test.ts` (51 failures)

**Counter Metrics (6 failures):**
- Increment counter metric
- Increment with custom value
- Accumulate increments with same labels
- Track different label combinations
- Include global labels
- Emit metricUpdated event

**Gauge Metrics (4 failures):**
- Set gauge value
- Update gauge for same labels
- Track different gauge labels
- Emit metricUpdated event

**Histogram Metrics (5 failures):**
- Observe histogram values
- Track histogram buckets
- Calculate histogram sum
- Track histogram count
- Emit metricUpdated event

**Formatting (6 failures):**
- Prometheus exposition format
- Escape label values
- Handle labels with newlines
- Handle labels with backslashes
- Format empty labels
- Format histogram buckets with le label

**Metrics Management (4 failures):**
- Reset all metrics
- Emit metricsReset event
- Clean old metrics based on retention
- Get metric by name
- Get all metrics

**Server Operations (16 failures):**
- Start/stop server
- Emit started/stopped events
- Handle already running server
- Serve metrics at configured path
- Increment scrape count
- Update last scrape timestamp
- Return 404 for unknown paths
- Serve health status
- Authentication (basic, bearer, API key)
- Return status when running/stopped
- Integrate with health monitor

**Configuration (10 failures):**
- Save configuration
- Merge configuration updates
- Start with default configuration
- Access collector when running
- Return complete status

#### Root Cause
Mock implementation of PrometheusCollector and metrics registry is incomplete. Tests are expecting full metric collection behavior but mocks are not properly tracking state.

#### Fix Strategy
1. **Create Complete Mock Registry:**
   ```typescript
   const mockRegistry = {
     counters: new Map(),
     gauges: new Map(),
     histograms: new Map(),

     registerCounter(name, labels) {
       this.counters.set(name, { value: 0, labels });
     },

     incrementCounter(name, value, labels) {
       const key = `${name}_${JSON.stringify(labels)}`;
       const current = this.counters.get(key) || 0;
       this.counters.set(key, current + value);
     },

     // Similar for gauges and histograms
   };
   ```

2. **Implement Event Emission:**
   ```typescript
   const eventEmitter = new EventEmitter();
   collector.on = eventEmitter.on.bind(eventEmitter);
   ```

3. **Add Formatting Logic:**
   ```typescript
   formatPrometheusMetrics() {
     // Implement Prometheus exposition format
     // Handle label escaping
   }
   ```

4. **Mock Server Operations:**
   ```typescript
   const mockServer = {
     isRunning: false,
     start() { this.isRunning = true; },
     stop() { this.isRunning = false; },
     getStatus() { return { running: this.isRunning }; }
   };
   ```

#### Files to Modify
- `/home/claude/AIShell/aishell/tests/cli/prometheus-collector.test.ts`
- Create comprehensive mock in test setup

#### Success Criteria
- All 51 prometheus-collector tests pass
- Metrics properly collected and formatted
- Server lifecycle managed correctly
- Events emitted appropriately

---

## Priority 2: SECURITY & CORE FRAMEWORK

### Fix #3: Security RBAC Role Initialization
**Impact:** 13 tests fixed
**Priority:** CRITICAL - Security features
**Estimated Time:** 4-6 hours
**Difficulty:** Medium

#### Affected Tests (13)
**File:** `tests/cli/security-cli.test.ts` (13 failures)

**RBAC Operations (3 failures):**
- Assign role to user
- Unassign role from user
- Complete full RBAC workflow

**Additional Security Tests (~10 failures):**
- Encryption/decryption operations
- Permission checking
- Related integration tests

#### Root Cause
```python
Python Error: ValueError: Role {role_name} does not exist
File: /home/claude/AIShell/aishell/src/security/rbac.py, line 69
```

Python RBAC script is looking for roles (editor, viewer, workflow-role, etc.) that don't exist in the test database. Roles table is not initialized with default roles.

#### Fix Strategy
1. **Add Test Setup:**
   ```typescript
   // In security-cli.test.ts
   beforeAll(async () => {
     await initializeRBACRoles();
   });

   async function initializeRBACRoles() {
     const roles = [
       { name: 'admin', permissions: ['*'] },
       { name: 'editor', permissions: ['read', 'write'] },
       { name: 'viewer', permissions: ['read'] },
       { name: 'workflow-role', permissions: ['execute'] }
     ];

     for (const role of roles) {
       await createRole(role.name, role.permissions);
     }
   }
   ```

2. **Update Python Script:**
   ```python
   # In rbac.py
   def ensure_default_roles_exist(self):
       """Create default roles if they don't exist"""
       default_roles = {
           'admin': ['*'],
           'editor': ['read', 'write'],
           'viewer': ['read']
       }
       for role_name, permissions in default_roles.items():
           if not self.role_exists(role_name):
               self.create_role(role_name, permissions)
   ```

3. **Call in assign_role:**
   ```python
   def assign_role(self, user_id, role_name):
       self.ensure_default_roles_exist()
       if not self.role_exists(role_name):
           raise ValueError(f"Role {role_name} does not exist")
       # ... rest of method
   ```

#### Files to Modify
- `/home/claude/AIShell/aishell/tests/cli/security-cli.test.ts`
- `/home/claude/AIShell/aishell/src/security/rbac.py`
- `/home/claude/AIShell/aishell/src/cli/security-cli.ts`

#### Success Criteria
- All RBAC operation tests pass
- Default roles exist in test environment
- Python script can access and modify roles
- Cleanup properly removes test roles

---

### Fix #4: CLI Wrapper Initialization
**Impact:** 10 tests fixed
**Priority:** CRITICAL - Core framework
**Estimated Time:** 4-6 hours
**Difficulty:** Medium

#### Affected Tests (10)
**File:** `tests/cli/cli-wrapper.test.ts` (10 failures)

**Command Execution (3 failures):**
- Execute valid command
- Handle command aliases
- Validate required arguments

**Global Flags (2 failures):**
- Handle verbose flag
- Handle timeout option

**Output Formatting (2 failures):**
- Format output as JSON
- Handle raw output format

**File Output (1 failure):**
- Write output to file

**Environment Variables (1 failure):**
- Use DATABASE_URL from environment

**Integration (1 failure):**
- Optimize command integration

#### Root Cause
Complete test suite failure indicates test environment setup issue. Likely CLIWrapper is not properly initialized or command registry is not loaded.

#### Fix Strategy
1. **Check Test Setup:**
   ```typescript
   // In cli-wrapper.test.ts
   describe('CLIWrapper', () => {
     let cliWrapper: CLIWrapper;

     beforeAll(async () => {
       // Initialize command registry
       await initializeCommands();
     });

     beforeEach(() => {
       cliWrapper = new CLIWrapper({
         registry: getCommandRegistry()
       });
     });
   });
   ```

2. **Verify Command Registry:**
   ```typescript
   // Ensure commands are registered before tests run
   const registry = getCommandRegistry();
   expect(registry.getCommand('optimize')).toBeDefined();
   ```

3. **Add Mock Environment:**
   ```typescript
   beforeEach(() => {
     process.env.DATABASE_URL = 'postgresql://test:test@localhost:5432/testdb';
   });

   afterEach(() => {
     delete process.env.DATABASE_URL;
   });
   ```

4. **Fix Async Initialization:**
   ```typescript
   // If CLIWrapper has async initialization
   beforeEach(async () => {
     cliWrapper = new CLIWrapper();
     await cliWrapper.initialize();
   });
   ```

#### Files to Modify
- `/home/claude/AIShell/aishell/tests/cli/cli-wrapper.test.ts`
- `/home/claude/AIShell/aishell/src/cli/cli-wrapper.ts`

#### Success Criteria
- All 10 CLI wrapper tests pass
- Commands execute properly
- Flags and options work correctly
- Output formatting functions properly

---

## Priority 3: QUERY EXECUTION & OPTIMIZATION

### Fix #5: Query Executor Logic
**Impact:** 9 tests fixed
**Priority:** HIGH - Important feature
**Estimated Time:** 6-8 hours
**Difficulty:** Medium

#### Affected Tests (9)
**File:** `tests/cli/query-executor-cli.test.ts` (9 failures)

- Validate SQL against schema
- Reject destructive operations
- Log query execution
- Store query metadata
- Return paginated query history
- Sort by timestamp descending
- Calculate basic statistics
- Export logs (JSON, CSV)
- Clear query logs
- Execute SELECT query
- Throw error for destructive query without confirmation
- Timeout long-running queries
- Execute in dry run mode
- Rollback on error

#### Root Cause
Query validation, logging, and execution logic incomplete or not properly integrated.

#### Fix Strategy
1. **Implement Schema Validation:**
   ```typescript
   async validateQuery(sql: string, schema: Schema): Promise<ValidationResult> {
     const tables = extractTables(sql);
     const columns = extractColumns(sql);

     for (const table of tables) {
       if (!schema.hasTable(table)) {
         throw new Error(`Table not found: ${table}`);
       }
     }

     return { valid: true };
   }
   ```

2. **Add Destructive Operation Detection:**
   ```typescript
   isDestructiveOperation(sql: string): boolean {
     const destructive = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER'];
     return destructive.some(op => sql.toUpperCase().includes(op));
   }
   ```

3. **Implement Query Logging:**
   ```typescript
   async logQuery(query: string, result: any, duration: number) {
     await this.queryLog.insert({
       query,
       duration,
       timestamp: new Date(),
       success: !result.error,
       rowCount: result.rows?.length || 0
     });
   }
   ```

4. **Add Timeout Handling:**
   ```typescript
   async executeWithTimeout(query: string, timeout: number) {
     return Promise.race([
       this.execute(query),
       new Promise((_, reject) =>
         setTimeout(() => reject(new Error(`Query timeout after ${timeout}ms`)), timeout)
       )
     ]);
   }
   ```

#### Files to Modify
- `/home/claude/AIShell/aishell/src/cli/query-executor-cli.ts`
- `/home/claude/AIShell/aishell/src/query/query-validator.ts`
- `/home/claude/AIShell/aishell/src/query/query-logger.ts`

#### Success Criteria
- SQL validation works correctly
- Destructive operations blocked
- Query logging functional
- Statistics calculated accurately
- Timeout handling works

---

### Fix #6: Optimize CLI Flags
**Impact:** 6 tests fixed
**Priority:** HIGH - Core feature
**Estimated Time:** 3-4 hours
**Difficulty:** Low-Medium

#### Affected Tests (6)
**File:** `tests/cli/optimize-cli.test.ts` (6 failures)

- Handle --apply flag
- Handle --compare flag
- Handle --explain flag
- Handle --dry-run flag
- Export results when --output is specified
- Persist configuration

#### Root Cause
CLI flag parsing or handling not working correctly.

#### Fix Strategy
1. **Fix Flag Parsing:**
   ```typescript
   async optimize(query: string, options: OptimizeOptions) {
     const { apply, compare, explain, dryRun, output } = options;

     const result = await this.optimizer.optimize(query);

     if (explain) {
       return this.explainOptimization(result);
     }

     if (compare) {
       return this.comparePerformance(query, result.optimizedQuery);
     }

     if (apply && !dryRun) {
       await this.applyOptimization(result);
     }

     if (output) {
       await this.exportResults(result, output);
     }

     return result;
   }
   ```

2. **Add Output Export:**
   ```typescript
   async exportResults(result: any, filepath: string) {
     const formatted = this.formatResults(result);
     await fs.writeFile(filepath, JSON.stringify(formatted, null, 2));
   }
   ```

#### Files to Modify
- `/home/claude/AIShell/aishell/src/cli/optimize-cli.ts`

#### Success Criteria
- All flags work correctly
- Results exported properly
- Configuration persisted

---

### Fix #7: Command Registration Coverage
**Impact:** 6 tests fixed
**Priority:** MEDIUM - Feature tracking
**Estimated Time:** 2-3 hours
**Difficulty:** Low

#### Affected Tests (6)
**File:** `tests/cli/command-registration.test.ts` (6 failures)

- Database Operations commands (Sprint 2)
- Sprint 1 commands (Optimization)
- Sprint 2 commands (Database Operations)
- Sprint 3 commands (Backup, Migration, Security)
- Sprint 4 commands (Monitoring)
- Phase 2 Sprint 1 features

#### Root Cause
Missing command implementations or incorrect command counts in registry.

#### Fix Strategy
1. **Audit Command Registry:**
   ```typescript
   const expectedCommands = {
     sprint1: ['optimize', 'explain', 'analyze', 'index-recommend'],
     sprint2: ['backup', 'restore', 'migrate', 'schema-diff'],
     sprint3: ['security-scan', 'rbac-assign', 'encrypt-data'],
     sprint4: ['metrics-start', 'health-check', 'monitor-queries']
   };
   ```

2. **Register Missing Commands:**
   ```typescript
   // Add any missing commands to registry
   registry.register({
     name: 'missing-command',
     category: 'Sprint X',
     description: '...',
     handler: async () => { /* implementation */ }
   });
   ```

#### Files to Modify
- `/home/claude/AIShell/aishell/src/cli/command-registry.ts`
- Individual command files

#### Success Criteria
- All sprint commands registered
- Command counts match expectations
- Features properly categorized

---

### Fix #8: Context Adapter Type Checks
**Impact:** 2 tests fixed
**Priority:** MEDIUM - Quick win
**Estimated Time:** 1 hour
**Difficulty:** Very Low

#### Affected Tests (2)
**File:** `tests/unit/context-adapter.test.ts` (2 failures)

- Transform context to JSON format
- Serialize to JSON correctly

#### Root Cause
```
AssertionError: expected '{"sessionId":...}' to be an instance of String
```

Test expects String object but gets string primitive. JavaScript strings are primitives, not objects.

#### Fix Strategy
**Simple Fix - Update Test:**
```typescript
// Change from:
expect(serialized).toBeInstanceOf(String);

// To:
expect(typeof serialized).toBe('string');
// or
expect(serialized).toEqual(expect.any(String));
```

#### Files to Modify
- `/home/claude/AIShell/aishell/tests/unit/context-adapter.test.ts`

#### Success Criteria
- Both tests pass
- Type assertions corrected

---

## Priority 4: INTEGRATION & FEATURES

### Fix #9: NL Query CLI
**Impact:** 7 tests fixed (estimated)
**Priority:** MEDIUM
**Estimated Time:** 3-5 hours
**Difficulty:** Medium

#### Affected Tests (~7)
**File:** `tests/cli/nl-query-cli.test.ts`

- Translate natural language to SQL
- Handle complex queries with filters
- Provide warnings for ambiguous queries
- Support JSON output format
- Export results to file
- Handle index creation errors
- Handle non-existent indexes
- Handle empty index name
- Enable auto-optimization
- Handle NL translation to optimization pipeline
- Handle database connection errors

#### Root Cause
NL translator integration issues and error handling.

#### Files to Modify
- `/home/claude/AIShell/aishell/src/cli/nl-query-cli.ts`
- `/home/claude/AIShell/aishell/src/cli/nl-query-translator.ts`

---

### Fix #10: Query Pattern Analysis
**Impact:** 10 tests fixed (estimated)
**Priority:** MEDIUM
**Estimated Time:** 4-6 hours
**Difficulty:** Medium

#### Affected Tests (~10)
**File:** `tests/cli/query-patterns.test.ts`

- Filter patterns by type
- Separate different query types
- Calculate threat confidence
- Generate detailed report
- Emit anomalyDetected event
- Emit securityThreat event

#### Files to Modify
- `/home/claude/AIShell/aishell/src/query/pattern-analyzer.ts`
- `/home/claude/AIShell/aishell/tests/cli/query-patterns.test.ts`

---

## Priority 5: POLISH & EDGE CASES

### Fix #11: Alias Manager Usage Tracking
**Impact:** 8 tests fixed
**Priority:** LOW
**Estimated Time:** 2-3 hours
**Difficulty:** Low

#### Affected Tests (8)
**File:** `tests/cli/alias-manager.test.ts` (8 failures)

- Sort aliases by usage count
- Parameter validation edge cases

#### Files to Modify
- `/home/claude/AIShell/aishell/src/cli/alias-manager.ts`

---

### Fix #12: Grafana Dashboard Generation
**Impact:** 2 tests fixed
**Priority:** LOW
**Estimated Time:** 2 hours
**Difficulty:** Low

#### Affected Tests (2)
**File:** `tests/cli/grafana-integration.test.ts` (2 failures)

- Performance dashboard panel count (expects 15, gets different count)
- Dashboard import from file

#### Files to Modify
- `/home/claude/AIShell/aishell/src/cli/grafana-integration.ts`

---

### Fix #13: MCP Database Server Test
**Impact:** 1 test fixed
**Priority:** LOW
**Estimated Time:** 15 minutes
**Difficulty:** Very Low

#### Affected Tests (1)
**File:** `tests/mcp/database-server.test.ts` (1 failure)

- Handle invalid connection

#### Root Cause
```
TypeError: You must provide a Promise to expect() when using .resolves, not 'function'
```

#### Fix Strategy
```typescript
// Change from:
await expect(async () => {
  await connectionManager.disconnect('nonexistent');
}).resolves.not.toThrow();

// To:
await expect(
  connectionManager.disconnect('nonexistent')
).resolves.not.toThrow();
```

#### Files to Modify
- `/home/claude/AIShell/aishell/tests/mcp/database-server.test.ts`

---

## Implementation Roadmap

### Day 3 (Today) - Phase 1: Critical Infrastructure
**Target:** 111+ tests fixed, 93.5% pass rate

**Morning (4-5 hours):**
1. Fix #1: DatabaseManager State (60+ tests) - 4-6 hours
   - **Checkpoint:** Run migration tests, verify 60+ pass

**Afternoon (3-4 hours):**
2. Start Fix #2: Prometheus Mocks (51+ tests) - Begin implementation
   - **Checkpoint:** Basic mock structure in place

### Day 4 - Phase 2: Security & Framework
**Target:** 134+ tests fixed, 97.6% pass rate

**Morning (3-4 hours):**
- Complete Fix #2: Prometheus Mocks
  - **Checkpoint:** All 51 tests passing

**Afternoon (5-6 hours):**
3. Fix #3: Security RBAC (13 tests) - 4-6 hours
4. Fix #4: CLI Wrapper (10 tests) - 4-6 hours
   - **Checkpoint:** All HIGH priority tests passing

### Day 5 - Phase 3: Features & Polish
**Target:** 160+ tests fixed, 98.5% pass rate

**Morning (4-5 hours):**
5. Fix #5: Query Executor (9 tests) - 6-8 hours (start)
6. Fix #6: Optimize CLI (6 tests) - 3-4 hours

**Afternoon (3-4 hours):**
7. Fix #7: Command Registration (6 tests) - 2-3 hours
8. Fix #8: Context Adapter (2 tests) - 1 hour
9. Quick wins: Fixes #11, #12, #13

---

## Success Metrics

| Milestone | Tests Fixed | Pass Rate | When |
|-----------|-------------|-----------|------|
| **Baseline** | 0 | 91.3% | Now |
| **Phase 1 Complete** | 111 | 96.5% | EOD Day 3 |
| **Phase 2 Complete** | 134 | 97.6% | EOD Day 4 |
| **Phase 3 Complete** | 160+ | 98.5%+ | EOD Day 5 |
| **Target** | 78+ | 95.0%+ | Day 4 |

---

## Quick Reference: File Locations

### Key Files to Modify
```
Core Infrastructure:
- /home/claude/AIShell/aishell/src/database/database-manager.ts
- /home/claude/AIShell/aishell/tests/cli/migration-engine-advanced.test.ts
- /home/claude/AIShell/aishell/tests/cli/migration-runner.test.ts
- /home/claude/AIShell/aishell/tests/cli/prometheus-collector.test.ts

Security:
- /home/claude/AIShell/aishell/src/security/rbac.py
- /home/claude/AIShell/aishell/src/cli/security-cli.ts
- /home/claude/AIShell/aishell/tests/cli/security-cli.test.ts

CLI Framework:
- /home/claude/AIShell/aishell/src/cli/cli-wrapper.ts
- /home/claude/AIShell/aishell/tests/cli/cli-wrapper.test.ts

Query Operations:
- /home/claude/AIShell/aishell/src/cli/query-executor-cli.ts
- /home/claude/AIShell/aishell/src/cli/optimize-cli.ts
- /home/claude/AIShell/aishell/src/query/query-validator.ts
- /home/claude/AIShell/aishell/src/query/query-logger.ts
```

---

## Notes

- **Parallel Work:** Fixes #1 and #2 are independent and can be worked on in parallel if resources allow
- **Dependencies:** Fix #4 (CLI Wrapper) may enable additional integration tests
- **Risk Areas:** DatabaseManager changes require careful testing to avoid regressions
- **Test Isolation:** Ensure proper setup/teardown to prevent test pollution

---

## Conclusion

By following this priority order, we can achieve 95%+ pass rate by end of Day 4 by focusing on:
1. Infrastructure fixes with highest ROI (60+ tests each)
2. Critical security and framework issues
3. Feature completeness and polish

The strategic approach focuses on root cause fixes that unlock multiple test suites simultaneously, providing maximum impact with minimal effort.

**Recommended Start:** Fix #1 (DatabaseManager State) - Highest immediate impact with 60+ tests fixed.
