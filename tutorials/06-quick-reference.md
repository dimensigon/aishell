# AIShell Quick Reference Guide

**Fast lookup for common AIShell operations, patterns, and configurations**

---

## 1. Agent Development Cheat Sheet

### Basic Agent Structure
```python
from src.core.base_agent import BaseAgent
from src.core.tool_registry import ToolRegistry

class MyAgent(BaseAgent):
    def __init__(self, llm_config: dict, tool_registry: ToolRegistry):
        super().__init__(name="my_agent", llm_config=llm_config)
        self.tool_registry = tool_registry

    async def process_task(self, task: str, context: dict) -> dict:
        tools = self.tool_registry.get_tools_for_category("my_category")
        result = await self._call_llm(task, tools, context)
        return result
```

### Agent Configuration Quick Start
```python
agent_config = {
    "name": "my_agent",
    "description": "Brief description",
    "capabilities": ["cap1", "cap2"],
    "max_retries": 3,
    "timeout": 30,
    "llm_config": {
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000
    }
}
```

### Common Agent Patterns

| Pattern | Code Snippet | Use Case |
|---------|--------------|----------|
| **Tool Execution** | `result = await self.execute_tool("tool_name", params)` | Execute registered tools |
| **Error Handling** | `try/except` with `self.logger.error()` | Graceful failure |
| **State Save** | `await self.save_checkpoint(state)` | Persist progress |
| **State Load** | `state = await self.load_checkpoint(checkpoint_id)` | Resume work |
| **Tool Discovery** | `tools = self.tool_registry.get_tools_by_tag("search")` | Find relevant tools |
| **Async Loop** | `async for item in stream: await process(item)` | Stream processing |

### Agent Lifecycle Hooks
```python
async def on_start(self):
    """Called when agent starts"""
    await self.initialize_resources()

async def on_task_start(self, task: str):
    """Called before each task"""
    self.current_task = task

async def on_task_complete(self, result: dict):
    """Called after task completes"""
    await self.save_result(result)

async def on_error(self, error: Exception):
    """Called on error"""
    await self.handle_error(error)

async def on_shutdown(self):
    """Called on agent shutdown"""
    await self.cleanup_resources()
```

---

## 2. Tool Registry Quick Reference

### Tool Registration One-Liners
```python
# Register a function as a tool
@tool_registry.register(category="search", tags=["web", "api"])
def search_web(query: str) -> dict:
    return {"results": [...]}

# Register with full metadata
tool_registry.register_tool(
    name="my_tool",
    function=my_function,
    description="Tool description",
    category="data_processing",
    tags=["transform", "clean"],
    risk_level="low",
    requires_approval=False
)

# Bulk register from module
tool_registry.register_from_module(my_tools_module, category="custom")
```

### Tool Discovery Quick Lookups
```python
# Get tools by category
tools = tool_registry.get_tools_for_category("file_operations")

# Get tools by tag
tools = tool_registry.get_tools_by_tag("database")

# Get all safe tools (no approval needed)
tools = tool_registry.get_safe_tools()

# Search tools by description
tools = tool_registry.search_tools("file upload")

# Get tool metadata
metadata = tool_registry.get_tool_metadata("tool_name")
```

### Tool Categories & Common Tags

| Category | Common Tags | Example Tools |
|----------|-------------|---------------|
| `file_operations` | `read`, `write`, `delete` | read_file, write_file, delete_file |
| `web_operations` | `http`, `api`, `scrape` | fetch_url, post_data, scrape_page |
| `data_processing` | `transform`, `clean`, `validate` | parse_json, validate_schema |
| `code_execution` | `python`, `shell`, `eval` | run_python, execute_shell |
| `database` | `query`, `insert`, `update` | run_query, insert_record |
| `external_api` | `api`, `service`, `integration` | call_api, webhook_trigger |

---

## 3. Safety System Quick Guide

### Risk Levels

| Level | Auto-Approve | Use Cases | Examples |
|-------|--------------|-----------|----------|
| `SAFE` | Yes | Read-only operations | read_file, list_directory |
| `LOW` | Yes (config) | Minor modifications | create_folder, append_log |
| `MEDIUM` | Prompt user | Data changes | write_file, update_database |
| `HIGH` | Prompt user | System changes | execute_shell, install_package |
| `CRITICAL` | Always prompt | Destructive ops | delete_database, rm_rf |

### Safety Check Quick Patterns
```python
from src.core.safety_manager import SafetyManager, RiskLevel

# Check if operation is safe
is_safe = await safety_manager.check_operation(
    operation="delete_file",
    params={"path": "/data/temp.txt"},
    context={"user": "admin"}
)

# Request approval for risky operation
approved = await safety_manager.request_approval(
    operation="execute_shell",
    risk_level=RiskLevel.HIGH,
    details="Running system update"
)

# Validate tool execution
validation = safety_manager.validate_tool_execution(
    tool_name="my_tool",
    parameters={"param": "value"}
)
```

### Safety Configuration Template
```yaml
safety:
  auto_approve_low_risk: true
  require_approval_threshold: "medium"
  blocked_operations:
    - "rm -rf /"
    - "DROP DATABASE"
  allowed_patterns:
    - "*.py"
    - "data/*.json"
  sandbox_mode: false
  approval_timeout: 60
```

---

## 4. Health Checks Cheat Sheet

### Common Health Check Patterns
```python
from src.core.health_monitor import HealthCheck, HealthStatus

# Basic health check
class MyHealthCheck(HealthCheck):
    async def check(self) -> HealthStatus:
        try:
            # Perform check
            result = await self.verify_service()
            return HealthStatus.HEALTHY if result else HealthStatus.DEGRADED
        except Exception:
            return HealthStatus.UNHEALTHY

# Register health check
health_monitor.register_check("my_service", MyHealthCheck(), interval=30)
```

### Health Status Quick Reference

| Status | Meaning | Action |
|--------|---------|--------|
| `HEALTHY` | All systems operational | Continue |
| `DEGRADED` | Partial functionality | Log warning |
| `UNHEALTHY` | Service down | Alert + Attempt recovery |
| `UNKNOWN` | Cannot determine | Investigate |

### Built-in Health Checks
```python
# Check database connection
health_monitor.check_database()

# Check API endpoint availability
health_monitor.check_endpoint("https://api.example.com/health")

# Check file system space
health_monitor.check_disk_space(min_free_gb=10)

# Check memory usage
health_monitor.check_memory(max_usage_percent=80)

# Get overall health
status = await health_monitor.get_overall_health()
```

### Health Monitor Configuration
```yaml
health_checks:
  enabled: true
  check_interval: 30
  checks:
    - name: "database"
      type: "database"
      connection_string: "${DB_URL}"
      timeout: 5
    - name: "api"
      type: "http"
      url: "https://api.example.com/health"
      expected_status: 200
    - name: "disk_space"
      type: "disk"
      min_free_gb: 10
```

---

## 5. State Management Quick Reference

### Checkpoint Operations
```python
# Save checkpoint
checkpoint_id = await agent.save_checkpoint({
    "step": 3,
    "data": processed_data,
    "metadata": {"timestamp": time.time()}
})

# Load checkpoint
state = await agent.load_checkpoint(checkpoint_id)

# List checkpoints
checkpoints = await agent.list_checkpoints(limit=10)

# Delete old checkpoints
await agent.cleanup_checkpoints(older_than_days=7)
```

### State Persistence Patterns

| Pattern | Code | Use Case |
|---------|------|----------|
| **Auto-save** | `@checkpoint_after` decorator | Save after each step |
| **Manual save** | `await save_checkpoint(state)` | Save at specific points |
| **Incremental** | Save only changed data | Large state objects |
| **Versioned** | Include version in metadata | Schema migrations |

### Recovery Patterns
```python
# Try to resume from last checkpoint
async def resume_or_start(agent, task):
    checkpoints = await agent.list_checkpoints()
    if checkpoints:
        latest = checkpoints[0]
        state = await agent.load_checkpoint(latest.id)
        return await agent.resume_from_state(state)
    else:
        return await agent.start_fresh(task)

# Fallback chain
async def resilient_execute(agent, task):
    try:
        return await agent.execute(task)
    except Exception as e:
        if checkpoint := await agent.get_last_checkpoint():
            return await agent.retry_from_checkpoint(checkpoint)
        raise
```

### State Storage Configuration
```yaml
state_management:
  backend: "filesystem"  # or "redis", "s3"
  checkpoint_dir: "./checkpoints"
  auto_save: true
  save_interval: 60
  max_checkpoints: 50
  compression: true
```

---

## 6. Common Patterns

### Agent Composition Pattern
```python
class OrchestratorAgent(BaseAgent):
    def __init__(self, sub_agents: list[BaseAgent]):
        self.sub_agents = {agent.name: agent for agent in sub_agents}

    async def delegate_task(self, task: str) -> dict:
        # Route to appropriate sub-agent
        agent = self.select_agent(task)
        return await agent.process_task(task, {})
```

### Retry Pattern
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def resilient_operation(agent, params):
    return await agent.execute(params)
```

### Circuit Breaker Pattern
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failures = 0
        self.threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    async def call(self, func, *args, **kwargs):
        if self.state == "open":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
```

### Streaming Response Pattern
```python
async def stream_processing(agent, data_stream):
    async for chunk in data_stream:
        processed = await agent.process_chunk(chunk)
        yield processed
```

### Parallel Execution Pattern
```python
import asyncio

async def parallel_agent_execution(agents, tasks):
    results = await asyncio.gather(*[
        agent.process_task(task, {})
        for agent, task in zip(agents, tasks)
    ])
    return results
```

---

## 7. CLI Commands

### Main Commands
```bash
# Start AIShell
python -m src.main

# Run specific agent
python -m src.main --agent research_agent --task "analyze codebase"

# Start in interactive mode
python -m src.main --interactive

# Load configuration
python -m src.main --config config/production.yaml

# Enable debug mode
python -m src.main --debug --log-level DEBUG
```

### Tool Management
```bash
# List all tools
aishell tools list

# Search tools
aishell tools search "file"

# Show tool details
aishell tools info file_reader

# Test a tool
aishell tools test file_reader --params '{"path": "test.txt"}'

# Validate tool registry
aishell tools validate
```

### Agent Operations
```bash
# List available agents
aishell agents list

# Create new agent from template
aishell agents create --name my_agent --template basic

# Run agent on task
aishell agents run research_agent --task "Find API endpoints"

# Show agent capabilities
aishell agents info research_agent
```

### State & Checkpoints
```bash
# List checkpoints
aishell checkpoints list

# Restore from checkpoint
aishell checkpoints restore <checkpoint_id>

# Clean old checkpoints
aishell checkpoints clean --older-than 7d

# Export checkpoint
aishell checkpoints export <checkpoint_id> --output backup.json
```

### Health & Monitoring
```bash
# Check system health
aishell health check

# Monitor in real-time
aishell health monitor --interval 5

# Show health history
aishell health history --last 24h
```

---

## 8. Configuration Templates

### Minimal Agent Config
```yaml
agent:
  name: "my_agent"
  type: "basic"
  llm:
    model: "gpt-4"
    temperature: 0.7
  tools:
    categories: ["file_operations", "web_operations"]
```

### Full Production Config
```yaml
agent:
  name: "production_agent"
  type: "advanced"
  description: "Production-ready agent"

llm:
  model: "gpt-4-turbo"
  temperature: 0.7
  max_tokens: 4000
  timeout: 30

tools:
  registry_path: "./tools"
  categories: ["all"]
  auto_load: true

safety:
  enabled: true
  auto_approve_low_risk: true
  require_approval: ["high", "critical"]
  sandbox_mode: false

state:
  backend: "redis"
  auto_save: true
  checkpoint_interval: 60

health:
  enabled: true
  check_interval: 30
  checks:
    - type: "database"
      connection: "${DB_URL}"
    - type: "memory"
      max_usage_percent: 80

logging:
  level: "INFO"
  format: "json"
  output: "logs/agent.log"
```

### Docker Compose Config
```yaml
version: '3.8'
services:
  aishell:
    image: aishell:latest
    environment:
      - CONFIG_PATH=/config/agent.yaml
      - LOG_LEVEL=INFO
    volumes:
      - ./config:/config
      - ./data:/data
      - ./logs:/logs
    ports:
      - "8000:8000"
```

---

## 9. Error Messages & Quick Fixes

| Error | Cause | Quick Fix |
|-------|-------|-----------|
| `ToolNotFoundError` | Tool not registered | Check `tool_registry.list_tools()` |
| `SafetyCheckFailed` | Operation blocked by safety | Reduce risk level or approve manually |
| `CheckpointLoadError` | Corrupted checkpoint | Delete checkpoint, start fresh |
| `LLMTimeoutError` | API call took too long | Increase `timeout` in config |
| `MemoryExceededError` | Agent used too much RAM | Reduce batch size or enable streaming |
| `ConfigValidationError` | Invalid YAML/JSON | Validate with `yamllint` or `jsonlint` |
| `ToolExecutionError` | Tool failed | Check tool logs, validate parameters |
| `HealthCheckFailed` | Service unavailable | Check service status, restart if needed |
| `RateLimitExceeded` | Too many API calls | Add backoff, reduce frequency |
| `PermissionDenied` | File/resource access denied | Check file permissions, user roles |

### Common Error Patterns
```python
# Handle tool errors gracefully
try:
    result = await tool_registry.execute("my_tool", params)
except ToolNotFoundError:
    # Fall back to alternative
    result = await tool_registry.execute("backup_tool", params)
except ToolExecutionError as e:
    # Log and retry with different params
    logger.error(f"Tool failed: {e}")
    result = await retry_with_backoff(tool, params)

# Handle LLM errors
try:
    response = await agent.call_llm(prompt)
except LLMTimeoutError:
    # Use cached response or shorter prompt
    response = cache.get(prompt) or await agent.call_llm(short_prompt)
```

---

## 10. API Reference

### Core Classes

#### BaseAgent
```python
class BaseAgent:
    async def process_task(task: str, context: dict) -> dict
    async def execute_tool(tool_name: str, params: dict) -> Any
    async def save_checkpoint(state: dict) -> str
    async def load_checkpoint(checkpoint_id: str) -> dict
    def register_tool(tool: callable, metadata: dict) -> None
```

#### ToolRegistry
```python
class ToolRegistry:
    def register_tool(name: str, function: callable, **metadata) -> None
    def get_tool(name: str) -> Tool
    def get_tools_for_category(category: str) -> list[Tool]
    def get_tools_by_tag(tag: str) -> list[Tool]
    def search_tools(query: str) -> list[Tool]
    def execute_tool(name: str, params: dict) -> Any
```

#### SafetyManager
```python
class SafetyManager:
    async def check_operation(operation: str, params: dict, context: dict) -> bool
    async def request_approval(operation: str, risk_level: RiskLevel, details: str) -> bool
    def validate_tool_execution(tool_name: str, parameters: dict) -> ValidationResult
    def set_risk_level(operation: str, level: RiskLevel) -> None
```

#### HealthMonitor
```python
class HealthMonitor:
    def register_check(name: str, check: HealthCheck, interval: int) -> None
    async def run_check(name: str) -> HealthStatus
    async def get_overall_health() -> HealthStatus
    def get_check_history(name: str, limit: int) -> list[HealthResult]
```

### Key Methods Quick Reference

| Class | Method | Returns | Purpose |
|-------|--------|---------|---------|
| BaseAgent | `process_task()` | dict | Execute main task |
| BaseAgent | `execute_tool()` | Any | Run registered tool |
| ToolRegistry | `register_tool()` | None | Add new tool |
| ToolRegistry | `search_tools()` | list | Find tools by query |
| SafetyManager | `check_operation()` | bool | Validate safety |
| HealthMonitor | `run_check()` | HealthStatus | Execute health check |

---

## Decision Trees

### When to Use Which Agent Pattern?

```
Need to process tasks?
├─ Single responsibility? → Use BaseAgent
├─ Multiple specialized tasks? → Use specialized agents
├─ Need coordination? → Use OrchestratorAgent
└─ Complex workflow? → Use WorkflowAgent
```

### Which State Backend?

```
State persistence needed?
├─ Small state, local only? → filesystem
├─ Shared across instances? → redis
├─ Long-term storage? → database
└─ Cloud deployment? → s3/blob storage
```

### Tool Registration Strategy?

```
Adding tools?
├─ Single tool? → @register decorator
├─ Multiple tools? → register_from_module()
├─ Dynamic tools? → register_tool() at runtime
└─ External tools? → create ToolAdapter
```

---

## Keyboard Shortcuts (Interactive Mode)

| Shortcut | Action |
|----------|--------|
| `Ctrl+C` | Interrupt current operation |
| `Ctrl+D` | Exit interactive mode |
| `↑/↓` | Navigate command history |
| `Tab` | Auto-complete commands |
| `Ctrl+L` | Clear screen |
| `Ctrl+R` | Search command history |

---

## Performance Tips

### Quick Optimizations
- Use async operations for I/O
- Batch tool executions when possible
- Cache LLM responses for repeated queries
- Enable compression for large checkpoints
- Use streaming for large datasets
- Set appropriate timeouts
- Limit concurrent operations

### Resource Limits
```yaml
resources:
  max_memory_mb: 2048
  max_concurrent_tasks: 10
  max_tool_execution_time: 30
  llm_rate_limit: 60  # requests per minute
```

---

**Last Updated:** 2025-10-05
**Version:** AIShell 1.0
**For detailed documentation, see:** `/home/claude/AIShell/docs/`
