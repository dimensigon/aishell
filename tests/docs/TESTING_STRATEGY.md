# AI-Shell Testing Strategy

## Overview

This document outlines the comprehensive testing strategy for AI-Shell, covering unit tests, integration tests, performance tests, and edge case scenarios.

## Testing Framework

- **Framework**: Vitest (modern, fast, compatible with Jest)
- **Coverage Tool**: V8
- **Mocking**: Vitest's built-in mocking utilities
- **Target Coverage**: 90%+ across all metrics

## Test Organization

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── queue.test.ts       # AsyncCommandQueue tests
│   ├── processor.test.ts   # CommandProcessor tests
│   ├── mcp.test.ts         # MCP client tests
│   ├── llm.test.ts         # LLM provider tests
│   ├── context.test.ts     # Context management tests
│   ├── cli.test.ts         # CLI interface tests
│   ├── error-handler.test.ts    # Error handling tests
│   ├── resource-manager.test.ts # Resource management tests
│   └── context-adapter.test.ts  # Context adapter tests
├── integration/             # Integration tests
│   └── workflow.test.ts    # End-to-end workflow tests
├── mocks/                   # Mock implementations
│   ├── mockMCPServer.ts    # Mock MCP server
│   └── mockLLMProvider.ts  # Mock LLM provider
├── utils/                   # Test utilities
│   └── testHelpers.ts      # Helper functions
├── docs/                    # Test documentation
│   └── TESTING_STRATEGY.md # This file
├── setup.ts                 # Global test setup
└── vitest.config.ts         # Vitest configuration
```

## Coverage Targets

| Metric     | Target | Current |
|-----------|--------|---------|
| Lines     | 90%    | TBD     |
| Functions | 90%    | TBD     |
| Branches  | 85%    | TBD     |
| Statements| 90%    | TBD     |

## Test Categories

### 1. Unit Tests

#### AsyncCommandQueue (`queue.test.ts`)
- **Basic Operations**: Enqueue, dequeue, priority ordering
- **Concurrency Control**: Parallel execution, concurrency limits
- **Rate Limiting**: Commands per second enforcement
- **Error Handling**: Failed commands, parsing errors
- **Queue Management**: Clear, drain, status reporting
- **Events**: Command lifecycle events
- **Edge Cases**: Empty commands, rapid enqueues, long wait times

**Key Test Scenarios:**
- ✓ Respect concurrency limits (max 2 concurrent)
- ✓ Priority ordering (high → medium → low)
- ✓ Rate limiting (5 commands/sec)
- ✓ Queue full rejection
- ✓ Continue after errors
- ✓ Event emissions

#### CommandProcessor (`processor.test.ts`)
- **Command Parsing**: Quote handling, argument splitting
- **Built-in Commands**: cd, history, help, config, clear
- **Command Execution**: stdout/stderr capture, exit codes
- **Timeout Handling**: Long-running command termination
- **History Management**: Track, clear, size limits
- **Environment**: Working directory, env variables
- **Error Cases**: Invalid commands, permissions

**Key Test Scenarios:**
- ✓ Parse complex shell commands
- ✓ Handle quoted arguments with spaces
- ✓ Execute with timeout (500ms)
- ✓ Respect max history size (3 entries)
- ✓ Built-in cd, history, help commands
- ✓ Capture stdout and stderr

#### Error Handler (`error-handler.test.ts`)
- **Error Classification**: Connection, timeout, auth, parse
- **Retry Logic**: Exponential backoff, max retries
- **Error Recovery**: Suggestions, auto-recovery
- **Circuit Breaker**: Threshold-based, timeout reset
- **Error Tracking**: Frequency, aggregation, stats
- **Custom Handlers**: Pluggable error handling

**Key Test Scenarios:**
- ✓ Classify errors correctly (8 types)
- ✓ Retry retryable errors (3 attempts)
- ✓ Exponential backoff (100ms × 2^n)
- ✓ Circuit breaker opens after 3 failures
- ✓ Sanitize sensitive data in errors
- ✓ Provide recovery suggestions

#### Resource Manager (`resource-manager.test.ts`)
- **Registration**: Add, update, batch register
- **Retrieval**: By URI, by type, search
- **Caching**: TTL, eviction, invalidation
- **Watching**: Change notifications, multiple watchers
- **Validation**: URI format, MIME types, size limits
- **Dependencies**: Tracking, resolution, circular detection
- **Metadata**: Access tracking, timestamps

**Key Test Scenarios:**
- ✓ Register and retrieve resources
- ✓ Cache with TTL (100ms expiry)
- ✓ Evict old entries (LRU, size 3)
- ✓ Notify watchers on changes
- ✓ Validate MIME types and URIs
- ✓ Detect circular dependencies
- ✓ Track access counts

#### Context Adapter (`context-adapter.test.ts`)
- **Transformation**: JSON, Binary, MessagePack formats
- **Compression**: Large context compression/decompression
- **Validation**: Schema, size limits, sanitization
- **Merging**: Deep merge, array strategies
- **Diffing**: Change detection, apply diffs
- **Versioning**: Save, restore, history limits
- **Serialization**: Handle special types, circular refs
- **Filtering**: Sensitive data, custom filters
- **Cloning**: Deep clone, clone with modifications

**Key Test Scenarios:**
- ✓ Round-trip transformation (all formats)
- ✓ Compress large contexts (10KB → smaller)
- ✓ Detect added/changed/removed fields
- ✓ Version history (limit 3)
- ✓ Filter sensitive fields (password, apiKey)
- ✓ Handle circular references
- ✓ Deep clone with modifications

### 2. Integration Tests

#### Workflow Tests (`workflow.test.ts`)
- **Connection Workflow**: Parse → Connect → Query
- **Natural Language**: Intent → SQL → Execute
- **Anonymization**: Detect → Anonymize → De-anonymize
- **Multi-Database**: Multiple connections, switching
- **History & Replay**: Record, replay commands
- **Error Recovery**: SQL errors, reconnection
- **Performance**: Query tracking, metrics
- **Auto-completion**: Schema-aware suggestions
- **Transactions**: Begin, commit, rollback

**Key Test Scenarios:**
- ✓ Complete connection workflow
- ✓ NL to SQL conversion and execution
- ✓ Sensitive data anonymization
- ✓ Multiple DB connections
- ✓ Command history and replay
- ✓ Auto-reconnect on disconnect
- ✓ Transaction lifecycle

### 3. Mock Implementations

#### MockMCPServer (`mockMCPServer.ts`)
- Simulates PostgreSQL and Oracle databases
- Handles SELECT, INSERT, UPDATE, DELETE
- Transaction support (BEGIN, COMMIT, ROLLBACK)
- Connection pooling simulation
- Error injection for testing

#### MockLLMProvider (`mockLLMProvider.ts`)
- Intent analysis (query, create, update, delete)
- SQL generation from natural language
- Text embeddings (deterministic mock)
- Pseudo-anonymization/de-anonymization
- Code completion suggestions
- SQL validation and error correction

## Test Execution

### Run All Tests
```bash
npm test
```

### Run with Coverage
```bash
npm test -- --coverage
```

### Run Specific Test File
```bash
npm test tests/unit/queue.test.ts
```

### Run in Watch Mode
```bash
npm test -- --watch
```

### Run with UI
```bash
npm test -- --ui
```

## Performance Testing

### Benchmarks
- **Queue throughput**: 100 commands/sec
- **Transformation speed**: <1s for 10k items
- **Cache hit rate**: >80%
- **Concurrent operations**: 5 parallel streams

### Load Tests
```typescript
// 20 rapid sequential enqueues
for (let i = 0; i < 20; i++) {
  queue.enqueue(`command-${i}`, context);
}

// Large context transformation
const largeContext = {
  largeArray: Array(10000).fill(0).map((_, i) => ({ id: i }))
};
```

## Edge Cases & Boundary Conditions

### Queue
- Empty command strings
- Maximum queue size (100)
- Very long queue times
- Rapid sequential enqueues (20+)
- Priority edge cases

### Processor
- Commands with special characters
- Very long output (100+ lines)
- Timeout boundary (500ms)
- Unclosed quotes
- Non-existent directories

### Error Handler
- Null/undefined errors
- Errors without messages
- Very long error messages (10k chars)
- Circular references in context

### Resource Manager
- Resources at size limit (1MB)
- Cache full (3 items)
- Circular dependencies
- Invalid MIME types
- Malformed URIs

### Context Adapter
- Large contexts (2MB+)
- Circular references
- Malformed JSON
- Corrupted binary data
- Invalid schema types

## Continuous Testing

### Pre-commit Hooks
```json
{
  "husky": {
    "hooks": {
      "pre-commit": "npm test && npm run typecheck"
    }
  }
}
```

### CI/CD Pipeline
1. Install dependencies
2. Run linter
3. Run type checker
4. Run all tests with coverage
5. Upload coverage reports
6. Fail if coverage < 90%

## Test Maintenance

### Adding New Tests
1. Follow existing patterns in test files
2. Use descriptive test names
3. Test success and failure paths
4. Include edge cases
5. Add comments for complex scenarios
6. Update this documentation

### Updating Tests
1. Keep tests synchronized with code changes
2. Maintain backwards compatibility
3. Update coverage targets if needed
4. Review and refactor flaky tests

## Best Practices

### 1. Test Structure (AAA Pattern)
```typescript
it('should handle timeout', async () => {
  // Arrange
  const processor = new CommandProcessor({ timeout: 500 });

  // Act
  const result = processor.execute(longCommand);

  // Assert
  await expect(result).rejects.toThrow('timeout');
});
```

### 2. Mock External Dependencies
```typescript
const mockClient = vi.fn();
mockClient.connect.mockResolvedValue({ success: true });
```

### 3. Use Descriptive Names
```typescript
// Good
it('should retry connection errors with exponential backoff')

// Bad
it('test retry')
```

### 4. Test One Thing
Each test should verify one specific behavior.

### 5. Avoid Test Interdependence
Tests should be able to run in any order.

### 6. Use beforeEach/afterEach
Clean up state between tests.

### 7. Test Async Code Properly
```typescript
// Use async/await
await expect(asyncFn()).rejects.toThrow();

// Or return promises
return expect(asyncFn()).resolves.toBe(value);
```

## Coverage Reports

### Generate HTML Report
```bash
npm test -- --coverage
open coverage/index.html
```

### View Coverage by File
```bash
npm test -- --coverage --reporter=text
```

## Known Issues & Limitations

1. **Jest not installed**: Project uses Vitest but package.json references Jest
2. **Timeout tests**: May be flaky on slow systems
3. **File system tests**: Depend on OS-specific behavior

## Future Improvements

1. Add E2E tests with real databases
2. Performance regression testing
3. Security vulnerability scanning
4. Mutation testing
5. Visual regression testing (for CLI output)
6. Accessibility testing

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [Testing Best Practices](https://github.com/goldbergyoni/javascript-testing-best-practices)
- [Jest Matchers Reference](https://jestjs.io/docs/expect)

---

**Last Updated**: 2025-10-26
**Coverage Target**: 90%+
**Test Count**: 200+ tests
**Execution Time**: <30s for full suite
