# AIShell Coding Standards & Conventions

**Project:** AIShell
**Version:** 1.0.0
**Last Updated:** 2025-10-25

---

## Table of Contents

1. [TypeScript Standards](#typescript-standards)
2. [Python Standards](#python-standards)
3. [File Organization](#file-organization)
4. [Naming Conventions](#naming-conventions)
5. [Error Handling](#error-handling)
6. [Testing Standards](#testing-standards)
7. [Documentation Standards](#documentation-standards)
8. [Git Commit Standards](#git-commit-standards)

---

## 1. TypeScript Standards

### 1.1 General Rules

```typescript
// ✅ ALWAYS use strict TypeScript configuration
{
  "strict": true,
  "noUnusedLocals": true,
  "noUnusedParameters": true,
  "noImplicitReturns": true,
  "noFallthroughCasesInSwitch": true
}

// ✅ ALWAYS provide explicit return types
async function fetchData(): Promise<Data> {
  // Implementation
}

// ❌ NEVER use 'any' without justification
function process(data: any) { } // BAD

// ✅ Use 'unknown' when type is truly unknown
function process(data: unknown) {
  if (typeof data === 'string') {
    // Type narrowing
  }
}
```

### 1.2 Async/Await

```typescript
// ✅ ALWAYS handle async errors
async function executeCommand(): Promise<void> {
  try {
    await someAsyncOperation();
  } catch (error) {
    logger.error('Operation failed', error);
    throw new CommandError('Execution failed', error);
  }
}

// ✅ ALWAYS await promises (no floating promises)
await client.connect(); // ✅
client.connect(); // ❌ ESLint will error

// ✅ Use Promise.all for parallel operations
const [users, orders] = await Promise.all([
  fetchUsers(),
  fetchOrders()
]);

// ❌ Don't await in sequence unnecessarily
const users = await fetchUsers(); // ❌
const orders = await fetchOrders(); // Sequential, could be parallel
```

### 1.3 Class Design

```typescript
// ✅ Use dependency injection
class CommandProcessor {
  constructor(
    private readonly config: ShellConfig,
    private readonly logger: Logger
  ) {}
}

// ✅ Use readonly for properties that don't change
class MCPClient {
  private readonly connections = new Map<string, Connection>();
}

// ✅ Use private/protected/public modifiers explicitly
class BaseAgent {
  private state: AgentState;
  protected config: AgentConfig;
  public async run(): Promise<TaskResult> { }
}

// ✅ Prefer composition over inheritance
class EnhancedProcessor {
  constructor(
    private baseProcessor: CommandProcessor,
    private enhancer: Enhancer
  ) {}
}
```

### 1.4 Interface Design

```typescript
// ✅ Use 'I' prefix for interfaces
interface ILLMProvider {
  generate(options: GenerateOptions): Promise<LLMResponse>;
}

// ✅ Use type aliases for unions and complex types
type CommandHandler = (context: CommandContext) => Promise<CommandResult>;
type ConnectionState = 'connected' | 'disconnected' | 'error';

// ✅ Use discriminated unions for variants
type MCPMessage =
  | { type: 'request'; id: number; method: string; }
  | { type: 'response'; id: number; result: unknown; }
  | { type: 'notification'; method: string; };
```

### 1.5 Error Handling

```typescript
// ✅ Create custom error classes
export class MCPConnectionError extends Error {
  constructor(
    message: string,
    public readonly serverName: string,
    public readonly cause?: Error
  ) {
    super(message);
    this.name = 'MCPConnectionError';
  }
}

// ✅ Use error boundaries in async code
async function safeExecute<T>(fn: () => Promise<T>): Promise<T | null> {
  try {
    return await fn();
  } catch (error) {
    logger.error('Execution failed', error);
    return null;
  }
}

// ✅ Provide context in errors
throw new Error(`Failed to connect to ${serverName}: ${error.message}`);
```

### 1.6 Event Emitters

```typescript
// ✅ Define event types
interface MCPClientEvents {
  connected: (serverName: string) => void;
  disconnected: (serverName: string, error?: Error) => void;
  error: (serverName: string, error: Error) => void;
}

// ✅ Extend typed EventEmitter
class MCPClient extends EventEmitter<MCPClientEvents> {
  connect(): void {
    this.emit('connected', 'server-1');
  }
}

// ✅ Remove listeners to prevent memory leaks
const handler = (name: string) => console.log(name);
client.on('connected', handler);
// Later...
client.off('connected', handler);
```

---

## 2. Python Standards

### 2.1 General Rules

```python
# ✅ ALWAYS use type hints
async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
    """Plan task execution."""
    pass

# ✅ Use dataclasses for data structures
from dataclasses import dataclass

@dataclass
class AgentConfig:
    agent_id: str
    agent_type: str
    capabilities: List[AgentCapability]

# ✅ Use ABC for interfaces
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
        """Create execution plan."""
        pass

# ✅ Use Enum for constants
from enum import Enum

class AgentState(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
```

### 2.2 Async/Await

```python
# ✅ Use async/await consistently
async def execute_task(self, task: TaskContext) -> TaskResult:
    try:
        plan = await self.plan(task)
        result = await self.execute_plan(plan)
        return result
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        raise

# ✅ Use asyncio.gather for parallel operations
results = await asyncio.gather(
    fetch_users(),
    fetch_orders(),
    return_exceptions=True
)

# ✅ Use async context managers
async with database.transaction() as tx:
    await tx.execute(query)
    await tx.commit()
```

### 2.3 Error Handling

```python
# ✅ Create custom exception classes
class AgentExecutionError(Exception):
    """Exception raised during agent execution."""
    def __init__(self, message: str, agent_id: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.agent_id = agent_id
        self.cause = cause

# ✅ Use try/except with specific exceptions
try:
    result = await self.execute_step(step)
except ConnectionError as e:
    logger.error(f"Database connection failed: {e}")
    raise AgentExecutionError("Connection failed", self.agent_id, e)
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise

# ✅ Use context managers for cleanup
from contextlib import asynccontextmanager

@asynccontextmanager
async def agent_execution_context(agent: BaseAgent):
    try:
        agent.state = AgentState.EXECUTING
        yield agent
    finally:
        agent.state = AgentState.IDLE
```

### 2.4 Documentation

```python
# ✅ Use comprehensive docstrings
def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate safety of planned step.

    Args:
        step: Step definition containing tool name and parameters

    Returns:
        Validation result dictionary with keys:
        - requires_approval: Boolean indicating if approval needed
        - safe: Boolean indicating if step is safe
        - risk_level: String indicating risk level
        - risks: List of identified risks (optional)

    Raises:
        ValueError: If step definition is invalid

    Example:
        >>> validation = agent.validate_safety({
        ...     'tool': 'backup_database',
        ...     'params': {'database': 'prod'}
        ... })
        >>> print(validation['safe'])
        True
    """
    pass
```

---

## 3. File Organization

### 3.1 TypeScript File Structure

```typescript
/**
 * Module description
 * Brief explanation of what this module does
 */

// 1. External imports (third-party)
import { EventEmitter } from 'eventemitter3';
import axios from 'axios';

// 2. Internal imports (project)
import { MCPClient } from './client';
import { Logger } from '../utils/logger';

// 3. Type definitions
interface Config {
  // ...
}

// 4. Constants
const DEFAULT_TIMEOUT = 30000;

// 5. Classes/Functions
export class MyClass {
  // ...
}

// 6. Exports
export { MyClass, Config };
```

### 3.2 Python File Structure

```python
"""
Module description.

Brief explanation of what this module does.
"""

# 1. Standard library imports
import asyncio
from typing import Dict, Any, List
from dataclasses import dataclass
from abc import ABC, abstractmethod

# 2. Third-party imports
import anthropic
from fastapi import FastAPI

# 3. Local imports
from .base import BaseAgent
from ..tools import ToolRegistry

# 4. Constants
DEFAULT_TIMEOUT = 30

# 5. Type definitions
@dataclass
class Config:
    pass

# 6. Classes/Functions
class MyClass(BaseAgent):
    pass

# 7. Module-level code
if __name__ == '__main__':
    pass
```

### 3.3 Directory Structure

```
module-name/
├── __init__.py          # Public API exports
├── base.py              # Base classes and interfaces
├── types.py             # Type definitions
├── manager.py           # Main implementation
├── utils.py             # Utility functions
├── constants.py         # Constants
└── exceptions.py        # Custom exceptions
```

---

## 4. Naming Conventions

### 4.1 TypeScript

```typescript
// Classes: PascalCase
class MCPClient { }
class CommandProcessor { }

// Interfaces: PascalCase with 'I' prefix
interface ILLMProvider { }
interface IMCPClient { }

// Functions: camelCase
function executeCommand() { }
async function fetchData() { }

// Variables: camelCase
const serverConfig = { };
let isConnected = false;

// Constants: UPPER_SNAKE_CASE
const MCP_PROTOCOL_VERSION = '2024-11-05';
const MAX_RETRIES = 3;

// Private members: prefix with _
class MyClass {
  private _internalState: State;
  private _helper(): void { }
}

// Type aliases: PascalCase
type CommandHandler = (ctx: Context) => Promise<Result>;
type ConnectionState = 'connected' | 'disconnected';

// Enums: PascalCase for name, UPPER_SNAKE_CASE for values
enum ConnectionState {
  CONNECTED = 'CONNECTED',
  DISCONNECTED = 'DISCONNECTED'
}
```

### 4.2 Python

```python
# Classes: PascalCase
class MCPClient:
    pass

class CommandProcessor:
    pass

# Functions: snake_case
def execute_command():
    pass

async def fetch_data():
    pass

# Variables: snake_case
server_config = {}
is_connected = False

# Constants: UPPER_SNAKE_CASE
MCP_PROTOCOL_VERSION = '2024-11-05'
MAX_RETRIES = 3

# Private members: prefix with _
class MyClass:
    def __init__(self):
        self._internal_state = None

    def _helper(self):
        pass

# Module-level private: prefix with _
_internal_cache = {}

def _internal_helper():
    pass
```

---

## 5. Error Handling

### 5.1 Error Hierarchies

```typescript
// TypeScript
export class AIShellError extends Error { }
export class MCPError extends AIShellError { }
export class MCPConnectionError extends MCPError { }
export class MCPTimeoutError extends MCPError { }

export class CommandError extends AIShellError { }
export class CommandExecutionError extends CommandError { }
export class CommandParseError extends CommandError { }
```

```python
# Python
class AIShellError(Exception):
    """Base exception for AIShell."""
    pass

class MCPError(AIShellError):
    """Base exception for MCP operations."""
    pass

class MCPConnectionError(MCPError):
    """Connection error."""
    pass

class MCPTimeoutError(MCPError):
    """Timeout error."""
    pass
```

### 5.2 Error Context

```typescript
// ✅ Provide rich error context
throw new MCPConnectionError(
  `Failed to connect to MCP server "${serverName}": ${error.message}`,
  serverName,
  error
);

// ✅ Log before throwing
logger.error('MCP connection failed', {
  serverName,
  error: error.message,
  stack: error.stack
});
throw new MCPConnectionError(/* ... */);
```

---

## 6. Testing Standards

### 6.1 Test Structure

```typescript
// TypeScript (Jest)
describe('MCPClient', () => {
  let client: MCPClient;
  let mockServer: MockMCPServer;

  beforeEach(() => {
    mockServer = createMockMCPServer();
    client = new MCPClient({
      servers: [mockServer.config]
    });
  });

  afterEach(async () => {
    await client.disconnect();
    mockServer.close();
  });

  describe('connect()', () => {
    it('should connect to server successfully', async () => {
      await client.connect('test-server');
      expect(client.getConnectionState('test-server'))
        .toBe(ConnectionState.CONNECTED);
    });

    it('should handle connection errors', async () => {
      mockServer.failNextConnection();
      await expect(client.connect('test-server'))
        .rejects.toThrow(MCPConnectionError);
    });
  });
});
```

```python
# Python (pytest)
import pytest
from aishell.agents import BaseAgent
from aishell.agents.base import TaskContext

@pytest.fixture
def agent():
    """Create test agent."""
    return TestAgent(agent_id='test')

@pytest.fixture
def task_context():
    """Create test task context."""
    return TaskContext(
        task_id='test-task',
        task_description='Test task',
        input_data={}
    )

class TestBaseAgent:
    """Test suite for BaseAgent."""

    async def test_run_success(self, agent, task_context):
        """Test successful task execution."""
        result = await agent.run(task_context)
        assert result.status == 'success'
        assert result.task_id == 'test-task'

    async def test_run_failure(self, agent, task_context):
        """Test task execution failure."""
        agent.fail_next_step()
        result = await agent.run(task_context)
        assert result.status == 'failure'
        assert result.error is not None
```

### 6.2 Test Coverage

```bash
# Aim for >80% coverage
# Critical paths should have 100% coverage

# TypeScript
npm run test:coverage

# Python
pytest --cov=src --cov-report=html
```

---

## 7. Documentation Standards

### 7.1 Code Comments

```typescript
// ✅ Use JSDoc for public APIs
/**
 * Connect to MCP server
 *
 * @param serverName - Name of the server to connect to
 * @param options - Connection options
 * @returns Promise that resolves when connected
 * @throws {MCPConnectionError} If connection fails
 *
 * @example
 * ```typescript
 * await client.connect('db-server');
 * ```
 */
async connect(serverName: string, options?: ConnectionOptions): Promise<void> {
  // Implementation
}

// ✅ Comment complex logic
// Calculate exponential backoff delay
// Formula: initialDelay * (backoffMultiplier ^ attemptNumber)
const delay = this.config.initialDelay *
  Math.pow(this.config.backoffMultiplier, this.reconnectAttempts);

// ❌ Don't comment obvious code
// Set name to 'test'
const name = 'test'; // BAD
```

### 7.2 README Structure

```markdown
# Module Name

Brief description

## Installation

```bash
npm install
```

## Usage

```typescript
// Example code
```

## API Reference

### Class: ClassName

Description

#### Methods

- `methodName(param: Type): ReturnType` - Description

## Testing

```bash
npm test
```

## License

MIT
```

---

## 8. Git Commit Standards

### 8.1 Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 8.2 Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build process or auxiliary tool changes

### 8.3 Examples

```
feat(mcp): add automatic reconnection support

Implement exponential backoff reconnection strategy for MCP
client connections. Reconnection is configurable per server.

Closes #123

---

fix(cli): handle SIGTERM gracefully

Ensure all pending commands complete before shutdown when
receiving SIGTERM signal.

---

docs(agents): add BaseAgent usage examples

Add comprehensive examples showing how to implement custom
agents using the BaseAgent abstract class.
```

---

## 9. Code Review Checklist

### 9.1 Before Submitting PR

- [ ] Code follows style guide
- [ ] All tests pass
- [ ] Coverage is >80%
- [ ] Documentation is updated
- [ ] No console.log statements
- [ ] Error handling is comprehensive
- [ ] Type safety is maintained
- [ ] No any types without justification
- [ ] Commit messages follow conventions

### 9.2 Reviewer Checklist

- [ ] Code is clear and maintainable
- [ ] Design is appropriate
- [ ] Tests cover edge cases
- [ ] Error messages are helpful
- [ ] Performance is acceptable
- [ ] Security considerations addressed
- [ ] Documentation is clear

---

**End of Coding Standards**

*Follow these standards for consistent, maintainable code*
