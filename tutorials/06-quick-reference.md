# AIShell Quick Reference Guide

**Fast lookup for common AIShell operations, patterns, and configurations**

---

## 1. Agent Development Cheat Sheet (Phase 12)

### Basic Agent Structure
```python
from src.agents.base import BaseAgent, AgentConfig, TaskContext, AgentCapability

class MyAgent(BaseAgent):
    def __init__(self, config: AgentConfig, llm_manager, tool_registry, state_manager):
        super().__init__(config, llm_manager, tool_registry, state_manager)

    async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
        """Create execution plan"""
        return [
            {'tool': 'step1', 'params': {...}, 'rationale': 'Why this step'},
            {'tool': 'step2', 'params': {...}, 'rationale': 'Why this step'}
        ]

    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute single step"""
        tool = self.tool_registry.get_tool(step['tool'])
        return await tool.execute(step['params'], context)

    def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Validate step safety"""
        return {
            'requires_approval': False,
            'safe': True,
            'risk_level': 'safe',
            'risks': [],
            'mitigations': []
        }
```

### Agent Configuration Quick Start
```python
from src.agents.base import AgentConfig, AgentCapability

agent_config = AgentConfig(
    agent_id="my_agent_001",
    agent_type="custom",
    capabilities=[
        AgentCapability.DATABASE_READ,
        AgentCapability.SCHEMA_ANALYZE
    ],
    llm_config={"model": "gpt-4", "temperature": 0.7},
    safety_level="moderate",  # 'strict', 'moderate', 'permissive'
    max_retries=3,
    timeout_seconds=300
)
```

### Phase 12 Agents Quick Reference

| Agent Type | Purpose | Key Capabilities |
|------------|---------|------------------|
| `BackupAgent` | Database backups | DATABASE_READ, BACKUP_CREATE, FILE_WRITE |
| `MigrationAgent` | Cross-DB migrations | DATABASE_READ, DATABASE_WRITE, DATABASE_DDL |
| `OptimizerAgent` | Performance optimization | SCHEMA_ANALYZE, INDEX_MANAGE, QUERY_OPTIMIZE |
| `CoordinatorAgent` | Multi-agent orchestration | COORDINATOR |
| `PerformanceAnalysisAgent` | Performance analysis | DATABASE_READ, SCHEMA_ANALYZE, QUERY_OPTIMIZE |

### Common Agent Patterns

| Pattern | Code Snippet | Use Case |
|---------|--------------|----------|
| **Run Agent** | `result = await agent.run(task_context)` | Execute full workflow |
| **Tool Execution** | `result = await tool.execute(params, context)` | Execute registered tools |
| **Error Handling** | `try/except` with checkpoint save | Graceful failure with recovery |
| **State Save** | `await state_manager.save_checkpoint(task_id, name, data)` | Persist progress |
| **State Load** | `checkpoint = await state_manager.get_checkpoint(cp_id)` | Resume work |
| **Tool Discovery** | `tools = tool_registry.find_tools(category=...)` | Find relevant tools |
| **Coordination** | `coordinator.run(workflow_task)` | Multi-agent workflows |
| **Variable Substitution** | `'${step_0.output.field}'` | Reference previous step outputs |

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

## 2. Tool Registry Quick Reference (Phase 12)

### Tool Registration with ToolDefinition
```python
from src.agents.tools.registry import ToolRegistry, ToolDefinition, ToolCategory, ToolRiskLevel
from src.agents.base import AgentCapability

# Define tool function
async def my_tool(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Tool implementation"""
    return {"result": "success"}

# Register tool
tool_registry.register_tool(ToolDefinition(
    name="my_tool",
    description="What this tool does",
    category=ToolCategory.ANALYSIS,
    risk_level=ToolRiskLevel.SAFE,
    required_capabilities=[AgentCapability.DATABASE_READ],
    parameters_schema={
        "type": "object",
        "properties": {
            "param1": {"type": "string"},
            "param2": {"type": "integer", "default": 10}
        },
        "required": ["param1"]
    },
    returns_schema={
        "type": "object",
        "properties": {
            "result": {"type": "string"}
        }
    },
    implementation=my_tool,
    requires_approval=False,
    max_execution_time=60,
    examples=[{
        "params": {"param1": "value"},
        "expected_output": {"result": "success"}
    }]
))
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

### Tool Categories & Risk Levels (Phase 12)

| Category | Risk Levels | Example Tools |
|----------|-------------|---------------|
| `ANALYSIS` | SAFE | analyze_slow_queries, identify_missing_indexes |
| `DATABASE_READ` | SAFE | count_table_rows, get_table_schema |
| `DATABASE_WRITE` | LOW-MEDIUM | update_table_statistics, insert_record |
| `DATABASE_DDL` | HIGH | create_index, alter_table, drop_table |
| `BACKUP` | LOW | backup_database_full, verify_backup |
| `MIGRATION` | MEDIUM-HIGH | execute_migration, copy_table_data |
| `OPTIMIZATION` | MEDIUM | rebuild_indexes, optimize_table |
| `FILE_OPERATIONS` | LOW-MEDIUM | read_file, write_file |

### Migration Tools (Phase 12)

| Tool | Category | Risk | Purpose |
|------|----------|------|---------|
| `analyze_schema` | ANALYSIS | SAFE | Analyze source/target schemas |
| `map_data_types` | ANALYSIS | SAFE | Map data types between databases |
| `execute_migration` | MIGRATION | HIGH | Execute actual migration |
| `validate_migration` | ANALYSIS | SAFE | Verify migration results |

### Optimization Tools (Phase 12)

| Tool | Category | Risk | Purpose |
|------|----------|------|---------|
| `analyze_slow_queries` | ANALYSIS | SAFE | Find slow queries |
| `identify_missing_indexes` | ANALYSIS | SAFE | Recommend indexes |
| `create_index` | DATABASE_DDL | MEDIUM | Create database index |
| `optimize_table_statistics` | DATABASE_WRITE | LOW | Update table statistics |
| `validate_optimization_results` | ANALYSIS | SAFE | Verify improvements |

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

## 11. UI Widgets Quick Reference (Phase 11)

### Command Preview Widget
```python
from src.ui.widgets.command_preview import CommandPreviewWidget

# Create widget
preview = CommandPreviewWidget(id="command-preview")

# Update with command and risk
await preview.set_command(
    command="DROP TABLE users",
    risk_level="critical",
    risks=["Permanent data loss", "No rollback possible"]
)
```

### Agent Status Panel
```python
from src.ui.widgets.agent_status_panel import AgentStatusPanel

# Create panel
panel = AgentStatusPanel(id="agent-status")

# Update agent status
await panel.update_agent(
    agent_name="BackupAgent",
    status="running",
    details={'progress': 45, 'duration': 12.5}
)
```

### Dynamic Panel Layout
```python
from textual.containers import Container
from textual.widgets import Static

# Create adaptive panels
with Container(id="main-container"):
    with Container(id="output-panel", classes="adaptive-height-50"):
        yield Static("Output here")
    with Container(id="module-panel", classes="adaptive-height-30"):
        yield Static("Module status")
    with Container(id="prompt-panel", classes="adaptive-height-20"):
        yield Static("Prompt")
```

### Smart Suggestions Widget
```python
from src.ui.widgets.suggestions import SmartSuggestionsWidget

# Create suggestions widget
suggestions = SmartSuggestionsWidget(id="suggestions")

# Update with scored suggestions
await suggestions.update_suggestions([
    {'text': 'email = "user@example.com"', 'score': 0.95, 'reason': 'Most common pattern'},
    {'text': 'created_at > "2025-01-01"', 'score': 0.87, 'reason': 'Recent queries'},
    {'text': 'status = "active"', 'score': 0.82, 'reason': 'Frequent filter'}
])
```

### UI Color Codes

| Risk Level | Color | Usage |
|------------|-------|-------|
| Safe | `green` | Safe operations, success messages |
| Low | `cyan` | Low-risk operations |
| Medium | `yellow` | Moderate-risk operations |
| High | `orange` | High-risk operations |
| Critical | `red` | Destructive operations |

---

## 12. Multi-Agent Workflows (Phase 12)

### CoordinatorAgent Usage
```python
from src.agents.coordinator import CoordinatorAgent

# Create coordinator
coordinator = CoordinatorAgent(config, llm_manager, tool_registry, state_manager, agent_manager)

# Define workflow
workflow = TaskContext(
    task_id="workflow_001",
    task_description="Multi-step maintenance",
    input_data={
        'workflow_steps': [
            {'agent_type': 'performance_analysis', 'task': '...', 'dependencies': []},
            {'agent_type': 'backup', 'task': '...', 'dependencies': []},
            {'agent_type': 'optimizer', 'task': '...', 'dependencies': ['performance_analysis', 'backup']}
        ]
    }
)

# Execute
result = await coordinator.run(workflow)
```

### Sequential Workflow Pattern
```python
# Step 1: Analysis
analysis_result = await analysis_agent.run(analysis_task)

# Step 2: Use analysis results in next step
backup_task = TaskContext(
    task_id="backup_001",
    task_description="Backup before optimization",
    input_data={
        'tables': analysis_result.output_data['affected_tables']
    }
)
backup_result = await backup_agent.run(backup_task)
```

### Parallel Workflow Pattern
```python
import asyncio

# Run agents in parallel
results = await asyncio.gather(
    agent1.run(task1),
    agent2.run(task2),
    agent3.run(task3)
)
```

### Agent Communication via State
```python
# Agent A saves results
await state_manager.save_checkpoint(
    "shared_workflow",
    "agent_a_output",
    {'slow_queries': [...], 'recommendations': [...]}
)

# Agent B reads Agent A's results
checkpoint = await state_manager.get_checkpoint("shared_workflow_cp_agent_a_output")
agent_a_results = checkpoint.checkpoint_data
```

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
