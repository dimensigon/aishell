# AI-Shell Test Suite

Comprehensive test suite for AI-Shell components with unit tests, integration tests, and mock providers.

## Test Structure

```
tests/
├── unit/               # Unit tests for individual components
│   ├── cli.test.ts    # CLI command processing tests
│   ├── mcp.test.ts    # MCP client integration tests
│   ├── llm.test.ts    # LLM provider interface tests
│   └── context.test.ts # Context management tests
├── integration/        # End-to-end integration tests
│   └── workflow.test.ts
├── mocks/             # Mock implementations
│   ├── mockMCPServer.ts
│   └── mockLLMProvider.ts
├── fixtures/          # Test data and fixtures
├── utils/             # Test utilities and helpers
├── jest.config.js     # Jest configuration
├── vitest.config.ts   # Vitest configuration
├── setup.ts           # Global test setup
└── package.json       # Test dependencies
```

## Running Tests

### Vitest (Recommended)

```bash
# Run all tests
npm run test

# Run with watch mode
npm run test:watch

# Run with UI
npm run test:ui

# Run unit tests only
npm run test:unit

# Run integration tests only
npm run test:integration

# Generate coverage report
npm run test:coverage
```

### Jest

```bash
# Run Jest tests
npm run test:jest
```

## Test Coverage

The test suite maintains high coverage standards:

- **Statements**: >80%
- **Branches**: >75%
- **Functions**: >80%
- **Lines**: >80%

### Coverage Reports

Coverage reports are generated in the `coverage/` directory:

- `coverage/index.html` - Interactive HTML report
- `coverage/lcov.info` - LCOV format for CI/CD
- `coverage/coverage-summary.json` - JSON summary

## Test Categories

### Unit Tests

#### CLI Tests (`unit/cli.test.ts`)
- Command parsing and validation
- Argument handling
- Command execution
- History management
- Auto-completion

#### MCP Tests (`unit/mcp.test.ts`)
- Database connection management
- Query execution
- Oracle/PostgreSQL clients
- Error handling
- Performance optimization

#### LLM Tests (`unit/llm.test.ts`)
- Intent analysis
- Text embedding
- Pseudo-anonymization
- Code completion
- Natural language to SQL

#### Context Tests (`unit/context.test.ts`)
- Session management
- Context state
- Variable management
- Persistence
- Serialization

### Integration Tests

#### Workflow Tests (`integration/workflow.test.ts`)
- Database connection workflow
- Natural language query workflow
- Data anonymization workflow
- Multi-database workflow
- Command history and replay
- Error recovery
- Performance monitoring
- Auto-completion
- Transaction handling

## Mock Providers

### MockMCPServer

Simulates database responses for testing:

```typescript
import { MockMCPServer } from './mocks/mockMCPServer';

const server = new MockMCPServer();
const connection = await server.connect({
  type: 'postgresql',
  host: 'localhost',
  port: 5432,
  database: 'testdb',
  user: 'testuser',
  password: 'testpass',
});

const result = await server.executeQuery(
  connection.connectionId,
  'SELECT * FROM users'
);
```

### MockLLMProvider

Simulates LLM responses without external API calls:

```typescript
import { MockLLMProvider } from './mocks/mockLLMProvider';

const llm = new MockLLMProvider();
const intent = await llm.analyzeIntent('show me all users', {});
const sql = await llm.generateSQL('find active users', {});
const completions = await llm.getCompletions('SEL', { tables: ['users'] });
```

## Writing New Tests

### Unit Test Template

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest';

describe('Component Name', () => {
  let component: any;
  let mockDependency: any;

  beforeEach(() => {
    mockDependency = {
      method: vi.fn(),
    };
    component = new Component(mockDependency);
  });

  describe('Feature Group', () => {
    it('should perform expected behavior', async () => {
      mockDependency.method.mockResolvedValue({ success: true });

      const result = await component.doSomething();

      expect(result.success).toBe(true);
      expect(mockDependency.method).toHaveBeenCalled();
    });
  });
});
```

### Integration Test Template

```typescript
import { describe, it, expect, beforeAll, afterAll } from 'vitest';

describe('Workflow Name', () => {
  let context: any;

  beforeAll(async () => {
    context = await setupTestEnvironment();
  });

  afterAll(async () => {
    await cleanupTestEnvironment(context);
  });

  it('should complete full workflow', async () => {
    const result = await executeWorkflow(context);
    expect(result.success).toBe(true);
  });
});
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run Tests
  run: npm test

- name: Generate Coverage
  run: npm run test:coverage

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage/lcov.info
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Mocking**: Mock external dependencies
3. **Clarity**: Use descriptive test names
4. **Coverage**: Aim for >80% coverage
5. **Performance**: Keep tests fast (<100ms for unit tests)
6. **Cleanup**: Always cleanup resources in afterEach/afterAll

## Debugging Tests

### VS Code Configuration

```json
{
  "type": "node",
  "request": "launch",
  "name": "Vitest Debug",
  "runtimeExecutable": "npm",
  "runtimeArgs": ["run", "test"],
  "console": "integratedTerminal",
  "internalConsoleOptions": "neverOpen"
}
```

### Debugging Tips

- Use `test.only()` to run single tests
- Add `console.log()` for quick debugging
- Use VS Code debugger with breakpoints
- Check mock call arguments with `mockFn.mock.calls`

## Contributing

When adding new features:

1. Write tests first (TDD)
2. Ensure >80% coverage
3. Update this README if needed
4. Run full test suite before committing
5. Add integration tests for new workflows
