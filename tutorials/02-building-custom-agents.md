# Building Custom AI Agents: A Comprehensive Hands-On Tutorial

## Table of Contents

1. [Introduction](#1-introduction)
2. [Agent Architecture](#2-agent-architecture)
3. [Quick Start: Your First Agent in 10 Minutes](#3-quick-start-your-first-agent-in-10-minutes)
4. [Planning Logic](#4-planning-logic)
5. [Execution Steps](#5-execution-steps)
6. [Safety Validation](#6-safety-validation)
7. [Tool Integration](#7-tool-integration)
8. [State Management](#8-state-management)
9. [Complete Example: DatabaseMaintenanceAgent](#9-complete-example-databasemaintenanceagent)
10. [Testing Your Agent](#10-testing-your-agent)
11. [Deployment Best Practices](#11-deployment-best-practices)
12. [Advanced Patterns](#12-advanced-patterns)
13. [Debugging Techniques](#13-debugging-techniques)
14. [Performance Optimization](#14-performance-optimization)
15. [Security Best Practices](#15-security-best-practices)
16. [Common Pitfalls](#16-common-pitfalls)

---

## 1. Introduction

### What Are AI Agents?

AI agents in AIShell are autonomous, intelligent entities that can:

- **Plan**: Break down complex tasks into executable steps
- **Execute**: Run operations using validated tools from the tool registry
- **Validate**: Ensure safety before each operation
- **Recover**: Save checkpoints and recover from failures
- **Learn**: Use LLM reasoning to adapt to different scenarios

### Key Capabilities

1. **Multi-Step Workflows**: Execute complex operations spanning multiple steps
2. **Tool-Based Execution**: Use pre-validated tools rather than arbitrary code
3. **Safety Controls**: Multi-layer safety with approval workflows
4. **State Persistence**: Checkpoint and recovery for long-running tasks
5. **LLM Integration**: Intelligent planning and reasoning capabilities

### When to Use Agents

Use AI agents when you need:

- Autonomous database operations (backups, migrations, optimization)
- Multi-step workflows with dependencies
- Operations requiring intelligent decision-making
- Safety-critical operations with approval workflows
- Long-running tasks with recovery capability

---

## 2. Agent Architecture

### Core Components

Every agent in AIShell inherits from `BaseAgent` and consists of:

```
┌─────────────────────────────────────────┐
│            BaseAgent                    │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Core Components                  │ │
│  │  • Agent Configuration            │ │
│  │  • LLM Manager (reasoning)        │ │
│  │  • Tool Registry (execution)      │ │
│  │  • State Manager (checkpoints)    │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Abstract Methods (YOU IMPLEMENT) │ │
│  │  • plan()          - Planning     │ │
│  │  • execute_step()  - Execution    │ │
│  │  • validate_safety() - Validation │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Built-in Functionality           │ │
│  │  • run()          - Main loop     │ │
│  │  • State management               │ │
│  │  • Approval handling              │ │
│  │  • Result aggregation             │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Agent States

Agents transition through these states during execution:

```python
class AgentState(Enum):
    IDLE = "idle"                      # Ready but not executing
    PLANNING = "planning"              # Creating execution plan
    EXECUTING = "executing"            # Running planned steps
    WAITING_APPROVAL = "waiting_approval"  # Waiting for user approval
    PAUSED = "paused"                  # Temporarily paused
    COMPLETED = "completed"            # Successfully completed
    FAILED = "failed"                  # Execution failed
```

### Data Structures

#### AgentConfig

Configuration for your agent instance:

```python
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class AgentConfig:
    agent_id: str                      # Unique identifier
    agent_type: str                    # Type (e.g., 'backup', 'migration')
    capabilities: List[AgentCapability] # What the agent can do
    llm_config: Dict[str, Any]         # LLM settings
    safety_level: str                  # 'strict', 'moderate', 'permissive'
    max_retries: int = 3               # Retry attempts
    timeout_seconds: int = 300         # Execution timeout
```

#### TaskContext

Context provided when executing a task:

```python
@dataclass
class TaskContext:
    task_id: str                       # Unique task identifier
    task_description: str              # Natural language description
    input_data: Dict[str, Any]         # Input parameters
    database_config: Optional[Dict[str, Any]] = None  # DB connection info
    workflow_id: Optional[str] = None  # Parent workflow
    parent_task_id: Optional[str] = None  # Parent task
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata
```

#### TaskResult

Result returned after task execution:

```python
@dataclass
class TaskResult:
    task_id: str                       # Task identifier
    agent_id: str                      # Agent that executed the task
    status: str                        # 'success', 'failure', 'requires_approval'
    output_data: Dict[str, Any]        # Results and outputs
    actions_taken: List[Dict[str, Any]] # List of executed actions
    reasoning: str                     # Natural language explanation
    execution_time: float              # Total execution time
    checkpoints: List[str]             # Checkpoint IDs created
    error: Optional[str] = None        # Error message if failed
```

### Agent Capabilities

Define what your agent can do:

```python
class AgentCapability(Enum):
    DATABASE_READ = "database_read"
    DATABASE_WRITE = "database_write"
    DATABASE_DDL = "database_ddl"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"
    SCHEMA_ANALYZE = "schema_analyze"
    SCHEMA_MODIFY = "schema_modify"
    QUERY_OPTIMIZE = "query_optimize"
    INDEX_MANAGE = "index_manage"
```

---

## 3. Quick Start: Your First Agent in 10 Minutes

Let's build a simple `LogCleanupAgent` that cleans old log entries from a database.

### Step 1: Create the Agent File

Create `src/agents/log_cleanup.py`:

```python
from typing import Dict, Any, List
from .base import BaseAgent, AgentConfig, TaskContext, AgentCapability


class LogCleanupAgent(BaseAgent):
    """
    Simple agent that cleans old log entries from database

    Capabilities:
    - Analyze log table size
    - Delete old logs based on retention period
    - Verify cleanup results
    """

    async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
        """
        Create execution plan for log cleanup

        Steps:
        1. Check log table size
        2. Delete old logs
        3. Verify results
        """
        retention_days = task.input_data.get('retention_days', 30)
        table_name = task.input_data.get('table_name', 'logs')

        plan = [
            {
                'tool': 'count_table_rows',
                'params': {'table': table_name},
                'rationale': 'Check current log count before cleanup'
            },
            {
                'tool': 'delete_old_records',
                'params': {
                    'table': table_name,
                    'date_column': 'created_at',
                    'retention_days': retention_days
                },
                'rationale': f'Delete logs older than {retention_days} days'
            },
            {
                'tool': 'count_table_rows',
                'params': {'table': table_name},
                'rationale': 'Verify cleanup by checking new row count'
            }
        ]

        return plan

    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single step using tool registry
        """
        tool_name = step['tool']
        params = step['params']

        # Get tool from registry
        tool = self.tool_registry.get_tool(tool_name)

        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found in registry")

        # Build execution context
        context = {
            'agent_id': self.config.agent_id,
            'task_id': self.current_task.task_id if self.current_task else None,
            'database_config': self.current_task.database_config if self.current_task else None,
            'llm_manager': self.llm_manager
        }

        # Execute tool
        result = await tool.execute(params, context)

        return result

    def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate safety of each step
        """
        tool_name = step['tool']

        # Read operations are safe
        if tool_name == 'count_table_rows':
            return {
                'requires_approval': False,
                'safe': True,
                'risk_level': 'safe',
                'risks': [],
                'mitigations': []
            }

        # Delete operations are medium risk
        if tool_name == 'delete_old_records':
            retention_days = step['params'].get('retention_days', 30)

            validation = {
                'requires_approval': False,
                'safe': True,
                'risk_level': 'medium',
                'risks': ['Permanent deletion of log records'],
                'mitigations': [f'Only deleting logs older than {retention_days} days']
            }

            # Require approval if deleting recent logs
            if retention_days < 7:
                validation['requires_approval'] = True
                validation['risks'].append('Deleting very recent logs (<7 days)')

            # Strict safety level requires approval for all deletes
            if self.config.safety_level == 'strict':
                validation['requires_approval'] = True

            return validation

        # Unknown operations require approval
        return {
            'requires_approval': True,
            'safe': False,
            'risk_level': 'unknown',
            'risks': ['Unknown operation type'],
            'mitigations': ['Manual review required']
        }
```

### Step 2: Register Your Agent

Add to `src/agents/manager.py`:

```python
def _register_default_agents(self):
    from src.agents.log_cleanup import LogCleanupAgent

    self.register_agent_class("log_cleanup", LogCleanupAgent)
```

### Step 3: Use Your Agent

```python
from src.agents.orchestrator import WorkflowOrchestrator, WorkflowConfig

# Configure the agent
config = WorkflowConfig(
    workflow_id="cleanup_001",
    workflow_name="Log Cleanup",
    description="Clean old log entries",
    agent_type="log_cleanup",
    input_data={
        'table_name': 'logs',
        'retention_days': 30
    },
    database_config={
        'database': 'production',
        'host': 'localhost'
    }
)

# Execute
orchestrator = WorkflowOrchestrator(agent_manager, state_manager, approval_system)
result = await orchestrator.execute_workflow(config)

print(f"Status: {result.status}")
print(f"Reasoning: {result.reasoning}")
```

**Congratulations!** You've built your first AI agent in under 10 minutes.

---

## 4. Planning Logic

The `plan()` method is where your agent's intelligence lives. It converts a high-level task into concrete steps.

### Planning Strategies

#### 1. Static Planning

Fixed sequence of steps:

```python
async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
    """Simple static plan - same steps every time"""
    return [
        {'tool': 'step_1', 'params': {...}},
        {'tool': 'step_2', 'params': {...}},
        {'tool': 'step_3', 'params': {...}}
    ]
```

#### 2. Conditional Planning

Steps vary based on input:

```python
async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
    """Conditional plan - adapts to input"""
    plan = []

    backup_type = task.input_data.get('backup_type', 'full')

    if backup_type == 'full':
        plan.extend([
            {'tool': 'calculate_backup_size', 'params': {...}},
            {'tool': 'backup_database_full', 'params': {...}},
            {'tool': 'validate_backup', 'params': {...}}
        ])
    elif backup_type == 'incremental':
        plan.extend([
            {'tool': 'find_last_backup', 'params': {...}},
            {'tool': 'backup_database_incremental', 'params': {...}},
            {'tool': 'validate_backup', 'params': {...}}
        ])

    # Add cleanup if requested
    if task.input_data.get('cleanup_old', False):
        plan.append({
            'tool': 'cleanup_old_backups',
            'params': {'retention_days': task.input_data.get('retention_days', 30)}
        })

    return plan
```

#### 3. LLM-Powered Planning

Let the LLM create the plan:

```python
async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
    """LLM-powered dynamic planning"""

    # Get available tools for this agent's capabilities
    available_tools = self.tool_registry.find_tools(
        capabilities=self.config.capabilities
    )

    # Format tools for LLM
    tools_description = self._format_tools_for_llm(available_tools)

    # Create planning prompt
    prompt = f"""
You are a database optimization agent. Create a step-by-step execution plan.

Task: {task.task_description}
Input Data: {task.input_data}

Available Tools:
{tools_description}

Return a JSON array of steps:
[
    {{
        "tool": "tool_name",
        "params": {{"param1": "value1"}},
        "rationale": "Why this step is needed"
    }}
]

Requirements:
- Use only the listed tools
- Each step must have clear parameters
- Explain the rationale for each step
- Consider dependencies between steps
- Prioritize safety
"""

    # Get LLM response
    response = await self.llm_manager.generate(prompt, max_tokens=1000)

    # Parse and validate plan
    import json
    plan = json.loads(response)

    return plan

def _format_tools_for_llm(self, tools: List[ToolDefinition]) -> str:
    """Format tool descriptions for LLM prompt"""
    descriptions = []
    for tool in tools:
        desc = f"""
Tool: {tool.name}
Description: {tool.description}
Parameters: {json.dumps(tool.parameters_schema, indent=2)}
Risk Level: {tool.risk_level.value}
"""
        descriptions.append(desc)
    return "\n".join(descriptions)
```

### Step Parameters and Variable Substitution

Reference outputs from previous steps:

```python
plan = [
    {
        'tool': 'backup_database',
        'params': {'database': 'prod', 'destination': '/backups'}
    },
    {
        'tool': 'validate_backup',
        'params': {
            # Reference output from step 0 (the backup step)
            'backup_path': '${step_0.output.backup_path}'
        }
    }
]
```

### Planning Best Practices

1. **Start with validation**: Verify preconditions before proceeding
2. **Include cleanup**: Plan for cleanup even if errors occur
3. **Add verification**: Verify results after critical operations
4. **Consider dependencies**: Order steps correctly
5. **Plan for rollback**: Include rollback steps for critical operations
6. **Add rationale**: Explain why each step is needed

---

## 5. Execution Steps

The `execute_step()` method runs a single planned step using the tool registry.

### Basic Execution Pattern

```python
async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a single step using tool registry

    Args:
        step: Step definition from plan() containing:
              - tool: Tool name
              - params: Tool parameters
              - rationale: Why this step is needed (optional)

    Returns:
        Dict containing step results
    """
    tool_name = step['tool']
    params = step['params']

    # Get tool from registry
    tool = self.tool_registry.get_tool(tool_name)

    if not tool:
        raise ValueError(f"Tool '{tool_name}' not found in registry")

    # Build execution context
    context = {
        'agent_id': self.config.agent_id,
        'task_id': self.current_task.task_id if self.current_task else None,
        'database_config': self.current_task.database_config if self.current_task else None,
        'llm_manager': self.llm_manager
    }

    # Execute tool
    result = await tool.execute(params, context)

    return result
```

### Advanced Execution with Error Handling

```python
async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute step with retry logic and error handling
    """
    tool_name = step['tool']
    params = step['params']
    max_retries = self.config.max_retries

    # Get tool
    tool = self.tool_registry.get_tool(tool_name)
    if not tool:
        raise ValueError(f"Tool '{tool_name}' not found")

    # Build context
    context = {
        'agent_id': self.config.agent_id,
        'task_id': self.current_task.task_id if self.current_task else None,
        'database_config': self.current_task.database_config if self.current_task else None,
        'llm_manager': self.llm_manager,
        'database_module': self.database_module  # If your agent needs direct DB access
    }

    # Execute with retries
    last_error = None
    for attempt in range(max_retries):
        try:
            result = await tool.execute(params, context)

            # Log success
            await self.state_manager.log_event(
                self.current_task.task_id,
                'step_executed',
                {
                    'step': step,
                    'result': result,
                    'attempt': attempt + 1
                }
            )

            return result

        except Exception as e:
            last_error = e

            # Log failure
            await self.state_manager.log_event(
                self.current_task.task_id,
                'step_failed',
                {
                    'step': step,
                    'error': str(e),
                    'attempt': attempt + 1
                }
            )

            # Retry for transient errors
            if attempt < max_retries - 1 and self._is_retryable_error(e):
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                break

    # All retries failed
    raise Exception(f"Step failed after {max_retries} attempts: {last_error}")

def _is_retryable_error(self, error: Exception) -> bool:
    """Determine if error is transient and worth retrying"""
    retryable_errors = [
        'connection timeout',
        'network error',
        'temporary failure'
    ]
    error_msg = str(error).lower()
    return any(err in error_msg for err in retryable_errors)
```

### Variable Substitution in Parameters

```python
async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
    """Execute step with variable substitution"""

    # Substitute variables from previous steps
    params = self._substitute_variables(step['params'])

    # ... rest of execution logic

def _substitute_variables(self, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Substitute variable references like '${step_0.output.backup_path}'
    """
    import re

    substituted = {}
    variable_pattern = re.compile(r'\$\{step_(\d+)\.output\.([a-zA-Z_][a-zA-Z0-9_]*)\}')

    for key, value in params.items():
        if isinstance(value, str):
            match = variable_pattern.match(value)
            if match:
                step_index = int(match.group(1))
                output_key = match.group(2)

                # Get value from previous step's result
                if step_index < len(self.execution_history):
                    prev_result = self.execution_history[step_index]
                    substituted[key] = prev_result.get(output_key)
                else:
                    raise ValueError(f"Cannot reference step {step_index} - not executed yet")
            else:
                substituted[key] = value
        else:
            substituted[key] = value

    return substituted
```

---

## 6. Safety Validation

The `validate_safety()` method assesses risk before executing each step.

### Basic Safety Validation

```python
def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate safety of planned step

    Returns:
        {
            'requires_approval': bool,
            'safe': bool,
            'risk_level': str,
            'risks': List[str],
            'mitigations': List[str]
        }
    """
    tool_name = step['tool']
    params = step['params']

    # Get tool definition to check risk level
    tool = self.tool_registry.get_tool(tool_name)

    # Default validation
    validation = {
        'requires_approval': False,
        'safe': True,
        'risk_level': 'safe',
        'risks': [],
        'mitigations': []
    }

    # Categorize by tool risk level
    if tool.risk_level == ToolRiskLevel.SAFE:
        return validation

    elif tool.risk_level == ToolRiskLevel.LOW:
        validation['risk_level'] = 'low'
        validation['risks'] = ['Minor side effects possible']
        return validation

    elif tool.risk_level == ToolRiskLevel.MEDIUM:
        validation['risk_level'] = 'medium'
        validation['risks'] = ['Moderate data modification']

        # Require approval in strict mode
        if self.config.safety_level == 'strict':
            validation['requires_approval'] = True

        return validation

    elif tool.risk_level in [ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL]:
        validation['risk_level'] = tool.risk_level.value
        validation['requires_approval'] = True
        validation['risks'] = ['Potentially destructive operation']
        validation['mitigations'] = ['Backup should be created first']

        return validation

    # Unknown - require approval
    return {
        'requires_approval': True,
        'safe': False,
        'risk_level': 'unknown',
        'risks': ['Unknown operation'],
        'mitigations': ['Manual review required']
    }
```

### Advanced Safety Validation

```python
def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
    """Advanced safety validation with multiple factors"""

    tool_name = step['tool']
    params = step['params']
    tool = self.tool_registry.get_tool(tool_name)

    # Start with base validation
    validation = {
        'requires_approval': tool.requires_approval,
        'safe': True,
        'risk_level': tool.risk_level.value,
        'risks': [],
        'mitigations': []
    }

    # Check safety level compatibility
    if self.config.safety_level == 'strict':
        # Strict mode: approve anything medium or higher
        if tool.risk_level in [ToolRiskLevel.MEDIUM, ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL]:
            validation['requires_approval'] = True

    elif self.config.safety_level == 'moderate':
        # Moderate mode: approve high and critical
        if tool.risk_level in [ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL]:
            validation['requires_approval'] = True

    # Special checks for specific operations

    # 1. Database write operations
    if tool.category == ToolCategory.DATABASE_WRITE:
        validation['risks'].append('Data modification operation')
        validation['mitigations'].append('Changes can be rolled back')

    # 2. DDL operations (schema changes)
    if tool.category == ToolCategory.DATABASE_DDL:
        validation['risks'].append('Schema modification - affects all users')
        validation['mitigations'].append('Backup created before execution')
        validation['mitigations'].append('Rollback script generated')
        validation['requires_approval'] = True  # Always require approval

    # 3. Large table operations
    if 'table' in params:
        table_size = self._estimate_table_size(params['table'])
        if table_size > 1000000:  # 1M rows
            validation['risks'].append(f'Operating on large table ({table_size} rows)')
            validation['mitigations'].append('Progress will be monitored')
            validation['requires_approval'] = True

    # 4. Production database operations
    if self.current_task.database_config:
        db_name = self.current_task.database_config.get('database', '')
        if 'prod' in db_name.lower() or 'production' in db_name.lower():
            validation['risks'].append('Operating on production database')
            validation['requires_approval'] = True

    # 5. Time-based restrictions
    if self._is_business_hours() and tool.risk_level == ToolRiskLevel.CRITICAL:
        validation['risks'].append('Critical operation during business hours')
        validation['requires_approval'] = True

    # 6. Destructive operations
    destructive_tools = ['drop_table', 'truncate_table', 'delete_database']
    if tool_name in destructive_tools:
        validation['risk_level'] = 'critical'
        validation['requires_approval'] = True
        validation['risks'].append('DESTRUCTIVE OPERATION - Cannot be undone')

    return validation

def _estimate_table_size(self, table_name: str) -> int:
    """Estimate table size (rows) - implement based on your needs"""
    # This would query the database for table statistics
    # Placeholder implementation
    return 0

def _is_business_hours(self) -> bool:
    """Check if current time is during business hours"""
    from datetime import datetime
    now = datetime.now()
    # Business hours: 9 AM - 5 PM, Monday-Friday
    return (9 <= now.hour < 17) and (now.weekday() < 5)
```

### Custom Safety Constraints

```python
class SafetyConstraint:
    """Base class for safety constraints"""

    def validate(self, step: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Return True if constraint is satisfied"""
        pass

    def get_violation_message(self) -> str:
        """Return message explaining constraint violation"""
        pass

class MaxTableSizeConstraint(SafetyConstraint):
    """Prevent operations on tables exceeding size limit"""

    def __init__(self, max_rows: int = 1000000):
        self.max_rows = max_rows

    def validate(self, step: Dict[str, Any], context: Dict[str, Any]) -> bool:
        table = step['params'].get('table')
        if table:
            table_size = context.get('table_sizes', {}).get(table, 0)
            return table_size <= self.max_rows
        return True

    def get_violation_message(self) -> str:
        return f"Table exceeds maximum size of {self.max_rows} rows"

# Use in validate_safety()
def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
    # ... normal validation

    # Apply custom constraints
    constraints = [
        MaxTableSizeConstraint(max_rows=5000000),
        ProductionHoursConstraint(),
        BackupRequiredConstraint()
    ]

    context = {
        'table_sizes': self._get_table_sizes(),
        'database': self.current_task.database_config
    }

    for constraint in constraints:
        if not constraint.validate(step, context):
            validation['requires_approval'] = True
            validation['risks'].append(constraint.get_violation_message())

    return validation
```

---

## 7. Tool Integration

Tools are the building blocks your agent uses to perform actual work.

### Understanding the Tool Registry

The tool registry is a central catalog of validated, safe operations:

```python
# Get a specific tool
tool = self.tool_registry.get_tool("backup_database_full")

# Find tools by category
backup_tools = self.tool_registry.find_tools(
    category=ToolCategory.BACKUP
)

# Find tools by risk level
safe_tools = self.tool_registry.find_tools(
    max_risk=ToolRiskLevel.LOW
)

# Find tools by capabilities
tools = self.tool_registry.find_tools(
    capabilities=[AgentCapability.DATABASE_READ]
)
```

### Tool Definition Structure

```python
@dataclass
class ToolDefinition:
    name: str                          # Tool identifier
    description: str                   # What the tool does
    category: ToolCategory             # Tool category
    risk_level: ToolRiskLevel          # Risk assessment
    required_capabilities: List[AgentCapability]  # Required agent capabilities
    parameters_schema: Dict[str, Any]  # JSON schema for parameters
    returns_schema: Dict[str, Any]     # JSON schema for return values
    implementation: Callable           # Actual implementation function
    requires_approval: bool            # Whether approval is needed
    max_execution_time: int            # Timeout in seconds
    rate_limit: Optional[int] = None   # Calls per minute
    examples: List[Dict[str, Any]]     # Example usage
```

### Creating Custom Tools

```python
# src/agents/tools/custom_tools.py

async def analyze_table_fragmentation(
    params: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze table fragmentation and recommend optimization

    Parameters:
        table: Table name to analyze
        database: Database name

    Returns:
        fragmentation_percent: Percentage of fragmentation
        recommendation: Optimization recommendation
        estimated_benefit: Estimated space savings
    """
    table = params['table']
    database = params['database']

    # Access database module from context
    database_module = context.get('database_module')

    # Execute analysis query
    result = database_module.execute_sql(
        sql=f"""
            SELECT
                table_name,
                data_length,
                index_length,
                data_free,
                (data_free / (data_length + index_length)) * 100 as fragmentation
            FROM information_schema.tables
            WHERE table_schema = '{database}'
            AND table_name = '{table}'
        """
    )

    fragmentation = result['fragmentation']

    # Determine recommendation
    if fragmentation > 20:
        recommendation = f"OPTIMIZE TABLE {table}"
        estimated_benefit = f"{result['data_free']} bytes"
    else:
        recommendation = "No optimization needed"
        estimated_benefit = "0 bytes"

    return {
        'fragmentation_percent': fragmentation,
        'recommendation': recommendation,
        'estimated_benefit': estimated_benefit,
        'table_stats': result
    }


# Register the tool
def register_custom_tools(registry: ToolRegistry):
    registry.register_tool(ToolDefinition(
        name="analyze_table_fragmentation",
        description="Analyze table fragmentation and provide optimization recommendations",
        category=ToolCategory.ANALYSIS,
        risk_level=ToolRiskLevel.SAFE,
        required_capabilities=[
            AgentCapability.DATABASE_READ,
            AgentCapability.SCHEMA_ANALYZE
        ],
        parameters_schema={
            "type": "object",
            "properties": {
                "table": {"type": "string", "description": "Table name"},
                "database": {"type": "string", "description": "Database name"}
            },
            "required": ["table", "database"]
        },
        returns_schema={
            "type": "object",
            "properties": {
                "fragmentation_percent": {"type": "number"},
                "recommendation": {"type": "string"},
                "estimated_benefit": {"type": "string"},
                "table_stats": {"type": "object"}
            }
        },
        implementation=analyze_table_fragmentation,
        requires_approval=False,
        max_execution_time=60,
        examples=[{
            "params": {"table": "users", "database": "production"},
            "expected_output": {
                "fragmentation_percent": 15.5,
                "recommendation": "No optimization needed",
                "estimated_benefit": "0 bytes"
            }
        }]
    ))
```

### Using Tools in Your Agent

```python
async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
    """Execute step using tools"""

    tool_name = step['tool']
    params = step['params']

    # Get and validate tool
    tool = self.tool_registry.get_tool(tool_name)
    if not tool:
        raise ValueError(f"Tool not found: {tool_name}")

    # Check agent has required capabilities
    missing_capabilities = [
        cap for cap in tool.required_capabilities
        if cap not in self.config.capabilities
    ]
    if missing_capabilities:
        raise ValueError(
            f"Agent lacks required capabilities: {missing_capabilities}"
        )

    # Build context with all dependencies
    context = {
        'agent_id': self.config.agent_id,
        'task_id': self.current_task.task_id if self.current_task else None,
        'database_config': self.current_task.database_config if self.current_task else None,
        'llm_manager': self.llm_manager,
        'database_module': self.database_module,  # If needed
        'file_manager': self.file_manager,  # If needed
    }

    # Execute tool
    result = await tool.execute(params, context)

    return result
```

---

## 8. State Management

State management enables checkpointing, recovery, and audit logging.

### Checkpoint Creation

```python
async def run(self, task: TaskContext) -> TaskResult:
    """Main execution loop with checkpointing"""

    self.current_task = task
    self.state = AgentState.PLANNING

    # Create plan
    plan = await self.plan(task)

    # Save checkpoint after planning
    await self.state_manager.save_checkpoint(
        task.task_id,
        "plan_created",
        {
            'plan': plan,
            'agent_config': self.config.__dict__,
            'timestamp': datetime.utcnow().isoformat()
        }
    )

    # Execute steps
    self.state = AgentState.EXECUTING
    actions_taken = []

    for i, step in enumerate(plan):
        # Execute step
        result = await self.execute_step(step)
        actions_taken.append({
            'step_index': i,
            'step': step,
            'result': result
        })

        # Checkpoint after each step
        await self.state_manager.save_checkpoint(
            task.task_id,
            f"step_{i}_completed",
            {
                'step': step,
                'result': result,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

    # Final checkpoint
    await self.state_manager.save_checkpoint(
        task.task_id,
        "workflow_completed",
        {
            'status': 'success',
            'actions_taken': actions_taken,
            'timestamp': datetime.utcnow().isoformat()
        }
    )
```

### Recovery from Checkpoints

```python
async def recover_from_checkpoint(self, task_id: str) -> TaskResult:
    """
    Recover failed workflow from last checkpoint
    """
    # Get latest checkpoint
    checkpoint = await self.state_manager.get_latest_checkpoint(task_id)

    if not checkpoint:
        raise ValueError(f"No checkpoints found for task {task_id}")

    # Determine where to resume
    if checkpoint.checkpoint_name == "plan_created":
        # Resume from beginning of execution
        plan = checkpoint.checkpoint_data['plan']
        start_index = 0

    elif checkpoint.checkpoint_name.startswith("step_"):
        # Resume from next step
        completed_step = int(checkpoint.checkpoint_name.split('_')[1])
        plan_checkpoint = await self.state_manager.get_checkpoint(
            f"{task_id}_cp_1"  # The plan checkpoint
        )
        plan = plan_checkpoint.checkpoint_data['plan']
        start_index = completed_step + 1

    else:
        raise ValueError(f"Cannot recover from checkpoint: {checkpoint.checkpoint_name}")

    # Resume execution
    print(f"Resuming from step {start_index} of {len(plan)}")

    actions_taken = []
    for i in range(start_index, len(plan)):
        step = plan[i]
        result = await self.execute_step(step)
        actions_taken.append({
            'step_index': i,
            'step': step,
            'result': result
        })

        # Checkpoint each step
        await self.state_manager.save_checkpoint(
            task_id,
            f"step_{i}_completed",
            {'step': step, 'result': result}
        )

    # Return final result
    return TaskResult(
        task_id=task_id,
        agent_id=self.config.agent_id,
        status="success",
        output_data=self._aggregate_results(actions_taken),
        actions_taken=actions_taken,
        reasoning="Recovered and completed from checkpoint",
        execution_time=0.0,
        checkpoints=await self.state_manager.get_checkpoints(task_id)
    )
```

### Event Logging

```python
# Log important events during execution
await self.state_manager.log_event(
    task_id=self.current_task.task_id,
    event_type='step_started',
    event_data={
        'step_index': i,
        'tool': step['tool'],
        'timestamp': datetime.utcnow().isoformat()
    }
)

await self.state_manager.log_event(
    task_id=self.current_task.task_id,
    event_type='approval_requested',
    event_data={
        'step': step,
        'validation': validation,
        'timestamp': datetime.utcnow().isoformat()
    }
)

await self.state_manager.log_event(
    task_id=self.current_task.task_id,
    event_type='error_occurred',
    event_data={
        'step_index': i,
        'error': str(error),
        'timestamp': datetime.utcnow().isoformat()
    }
)
```

---

## 9. Complete Example: DatabaseMaintenanceAgent

Let's build a complete, production-ready agent for database maintenance.

```python
"""
DatabaseMaintenanceAgent - Comprehensive database maintenance operations

Capabilities:
- Analyze table statistics
- Rebuild fragmented indexes
- Update table statistics
- Vacuum/optimize tables
- Analyze and fix table corruption
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .base import (
    BaseAgent,
    AgentConfig,
    TaskContext,
    TaskResult,
    AgentCapability,
    AgentState
)


class DatabaseMaintenanceAgent(BaseAgent):
    """
    Intelligent database maintenance agent

    This agent performs comprehensive database maintenance including:
    - Table and index analysis
    - Fragmentation detection and repair
    - Statistics updates
    - Performance optimization
    - Corruption detection and repair

    Example Usage:
        config = AgentConfig(
            agent_id="maint_001",
            agent_type="maintenance",
            capabilities=[
                AgentCapability.DATABASE_READ,
                AgentCapability.SCHEMA_ANALYZE,
                AgentCapability.INDEX_MANAGE
            ],
            llm_config={"model": "llama2", "temperature": 0.3},
            safety_level="moderate"
        )

        agent = DatabaseMaintenanceAgent(config, llm_manager, tool_registry, state_manager)

        task = TaskContext(
            task_id="maint_task_001",
            task_description="Perform weekly database maintenance",
            input_data={
                'maintenance_type': 'full',
                'tables': ['users', 'orders', 'products'],
                'rebuild_indexes': True,
                'update_stats': True
            },
            database_config={'database': 'production'}
        )

        result = await agent.run(task)
    """

    async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
        """
        Create intelligent maintenance plan

        Plans vary based on maintenance_type:
        - 'quick': Basic stats update
        - 'standard': Stats + index analysis
        - 'full': Comprehensive maintenance with optimization
        - 'emergency': Focus on corruption detection and repair
        """
        maintenance_type = task.input_data.get('maintenance_type', 'standard')
        tables = task.input_data.get('tables', [])
        database = task.database_config.get('database') if task.database_config else 'unknown'

        plan = []

        # Step 1: Always analyze current state first
        plan.append({
            'tool': 'analyze_database_health',
            'params': {
                'database': database,
                'tables': tables,
                'check_corruption': maintenance_type in ['full', 'emergency']
            },
            'rationale': 'Assess current database health before maintenance'
        })

        if maintenance_type == 'quick':
            # Quick maintenance: just update statistics
            for table in tables:
                plan.append({
                    'tool': 'update_table_statistics',
                    'params': {'database': database, 'table': table},
                    'rationale': f'Update statistics for {table} to improve query planning'
                })

        elif maintenance_type == 'standard':
            # Standard maintenance: analyze fragmentation and update stats
            for table in tables:
                # Analyze fragmentation
                plan.append({
                    'tool': 'analyze_table_fragmentation',
                    'params': {'database': database, 'table': table},
                    'rationale': f'Check fragmentation level for {table}'
                })

                # Update statistics
                plan.append({
                    'tool': 'update_table_statistics',
                    'params': {'database': database, 'table': table},
                    'rationale': f'Update statistics for {table}'
                })

        elif maintenance_type == 'full':
            # Full maintenance: comprehensive optimization
            for table in tables:
                # Analyze fragmentation
                plan.append({
                    'tool': 'analyze_table_fragmentation',
                    'params': {'database': database, 'table': table},
                    'rationale': f'Analyze fragmentation for {table}'
                })

                # Rebuild fragmented indexes (conditional based on fragmentation)
                if task.input_data.get('rebuild_indexes', True):
                    plan.append({
                        'tool': 'rebuild_fragmented_indexes',
                        'params': {
                            'database': database,
                            'table': table,
                            'fragmentation_threshold': 30  # Rebuild if >30%
                        },
                        'rationale': f'Rebuild fragmented indexes for {table}'
                    })

                # Optimize table
                plan.append({
                    'tool': 'optimize_table',
                    'params': {'database': database, 'table': table},
                    'rationale': f'Optimize table structure for {table}'
                })

                # Update statistics
                plan.append({
                    'tool': 'update_table_statistics',
                    'params': {'database': database, 'table': table},
                    'rationale': f'Update statistics for {table}'
                })

        elif maintenance_type == 'emergency':
            # Emergency maintenance: focus on corruption repair
            plan.append({
                'tool': 'check_table_corruption',
                'params': {'database': database, 'tables': tables},
                'rationale': 'Check for table corruption'
            })

            plan.append({
                'tool': 'repair_corrupted_tables',
                'params': {
                    'database': database,
                    'tables': '${step_1.output.corrupted_tables}',
                    'create_backup': True
                },
                'rationale': 'Repair any corrupted tables found'
            })

        # Final step: Generate maintenance report
        plan.append({
            'tool': 'generate_maintenance_report',
            'params': {
                'database': database,
                'tables': tables,
                'maintenance_type': maintenance_type
            },
            'rationale': 'Generate summary report of maintenance actions'
        })

        return plan

    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute maintenance step with comprehensive error handling
        """
        tool_name = step['tool']
        params = step['params']

        # Substitute variables from previous steps
        params = self._substitute_variables(params)

        # Get tool from registry
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found in registry")

        # Build execution context
        context = {
            'agent_id': self.config.agent_id,
            'task_id': self.current_task.task_id if self.current_task else None,
            'database_config': self.current_task.database_config if self.current_task else None,
            'llm_manager': self.llm_manager,
            'database_module': getattr(self, 'database_module', None)
        }

        # Log step start
        await self.state_manager.log_event(
            self.current_task.task_id,
            'maintenance_step_started',
            {
                'tool': tool_name,
                'params': params,
                'rationale': step.get('rationale'),
                'timestamp': datetime.utcnow().isoformat()
            }
        )

        try:
            # Execute with timeout
            import asyncio
            result = await asyncio.wait_for(
                tool.execute(params, context),
                timeout=tool.max_execution_time
            )

            # Log success
            await self.state_manager.log_event(
                self.current_task.task_id,
                'maintenance_step_completed',
                {
                    'tool': tool_name,
                    'result': result,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )

            return result

        except asyncio.TimeoutError:
            error_msg = f"Step '{tool_name}' exceeded timeout of {tool.max_execution_time}s"
            await self.state_manager.log_event(
                self.current_task.task_id,
                'maintenance_step_timeout',
                {'tool': tool_name, 'error': error_msg}
            )
            raise Exception(error_msg)

        except Exception as e:
            # Log failure
            await self.state_manager.log_event(
                self.current_task.task_id,
                'maintenance_step_failed',
                {
                    'tool': tool_name,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            raise

    def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive safety validation for maintenance operations
        """
        tool_name = step['tool']
        params = step['params']

        # Get tool from registry
        tool = self.tool_registry.get_tool(tool_name)

        # Base validation
        validation = {
            'requires_approval': False,
            'safe': True,
            'risk_level': tool.risk_level.value if tool else 'unknown',
            'risks': [],
            'mitigations': []
        }

        # Analysis operations are safe
        safe_tools = [
            'analyze_database_health',
            'analyze_table_fragmentation',
            'check_table_corruption',
            'generate_maintenance_report'
        ]

        if tool_name in safe_tools:
            validation['risk_level'] = 'safe'
            return validation

        # Statistics updates are low risk
        if tool_name == 'update_table_statistics':
            validation['risk_level'] = 'low'
            validation['risks'] = ['Brief table lock during statistics update']
            validation['mitigations'] = ['Operation is fast, minimal impact']
            return validation

        # Index rebuilds are medium risk
        if tool_name == 'rebuild_fragmented_indexes':
            validation['risk_level'] = 'medium'
            validation['risks'] = [
                'Table may be locked during index rebuild',
                'Temporary disk space required for index rebuild'
            ]
            validation['mitigations'] = [
                'Only rebuilding indexes with >30% fragmentation',
                'Progress will be monitored'
            ]

            # Require approval in strict mode or for large tables
            if self.config.safety_level == 'strict':
                validation['requires_approval'] = True

            table = params.get('table')
            if table and self._is_large_table(table):
                validation['requires_approval'] = True
                validation['risks'].append('Operating on large table')

            return validation

        # Table optimization is medium-high risk
        if tool_name == 'optimize_table':
            validation['risk_level'] = 'medium'
            validation['risks'] = [
                'Table will be locked during optimization',
                'May take significant time on large tables',
                'Temporary disk space required'
            ]
            validation['mitigations'] = [
                'Operation can be monitored and cancelled if needed',
                'Table will be accessible after completion'
            ]

            # Require approval for production databases or large tables
            if self._is_production_database():
                validation['requires_approval'] = True
                validation['risks'].append('Operating on production database')

            table = params.get('table')
            if table and self._is_large_table(table):
                validation['requires_approval'] = True

            return validation

        # Table repair is high risk
        if tool_name == 'repair_corrupted_tables':
            validation['risk_level'] = 'high'
            validation['requires_approval'] = True
            validation['risks'] = [
                'Data modification operation',
                'May result in data loss if corruption is severe',
                'Table will be locked during repair'
            ]
            validation['mitigations'] = [
                'Backup will be created before repair',
                'Only repairing tables identified as corrupted',
                'Repair process is logged for audit'
            ]
            return validation

        # Unknown operation - require approval
        validation['risk_level'] = 'unknown'
        validation['requires_approval'] = True
        validation['safe'] = False
        validation['risks'] = ['Unknown maintenance operation']
        validation['mitigations'] = ['Manual review required']

        return validation

    def _substitute_variables(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Substitute variable references from previous steps"""
        import re

        substituted = {}
        variable_pattern = re.compile(r'\$\{step_(\d+)\.output\.([a-zA-Z_][a-zA-Z0-9_]*)\}')

        for key, value in params.items():
            if isinstance(value, str):
                match = variable_pattern.match(value)
                if match:
                    step_index = int(match.group(1))
                    output_key = match.group(2)

                    # Get value from execution history
                    # (In real implementation, you'd track step outputs)
                    substituted[key] = value  # Placeholder
                else:
                    substituted[key] = value
            else:
                substituted[key] = value

        return substituted

    def _is_large_table(self, table_name: str) -> bool:
        """Check if table is considered large (>1M rows)"""
        # This would query the database for table size
        # Placeholder implementation
        return False

    def _is_production_database(self) -> bool:
        """Check if operating on production database"""
        if self.current_task and self.current_task.database_config:
            db_name = self.current_task.database_config.get('database', '').lower()
            return 'prod' in db_name or 'production' in db_name
        return False

    def _aggregate_results(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate maintenance results into comprehensive summary
        """
        aggregated = {
            'actions_count': len(actions),
            'maintenance_type': self.current_task.input_data.get('maintenance_type', 'unknown') if self.current_task else 'unknown',
            'tables_processed': [],
            'indexes_rebuilt': 0,
            'statistics_updated': 0,
            'tables_optimized': 0,
            'corruption_found': False,
            'corruption_repaired': False
        }

        for action in actions:
            if 'result' not in action or not isinstance(action['result'], dict):
                continue

            result = action['result']
            step = action.get('step', {})
            tool_name = step.get('tool', '')

            # Track tables processed
            if 'table' in step.get('params', {}):
                table = step['params']['table']
                if table not in aggregated['tables_processed']:
                    aggregated['tables_processed'].append(table)

            # Count specific operations
            if tool_name == 'rebuild_fragmented_indexes':
                if result.get('indexes_rebuilt', 0) > 0:
                    aggregated['indexes_rebuilt'] += result['indexes_rebuilt']

            if tool_name == 'update_table_statistics':
                aggregated['statistics_updated'] += 1

            if tool_name == 'optimize_table':
                aggregated['tables_optimized'] += 1

            if tool_name == 'check_table_corruption':
                if result.get('corrupted_tables'):
                    aggregated['corruption_found'] = True
                    aggregated['corrupted_tables'] = result['corrupted_tables']

            if tool_name == 'repair_corrupted_tables':
                aggregated['corruption_repaired'] = True
                aggregated['repaired_tables'] = result.get('repaired_tables', [])

            # Collect fragmentation data
            if tool_name == 'analyze_table_fragmentation':
                if 'fragmentation_data' not in aggregated:
                    aggregated['fragmentation_data'] = {}
                table = step['params']['table']
                aggregated['fragmentation_data'][table] = {
                    'fragmentation_percent': result.get('fragmentation_percent'),
                    'recommendation': result.get('recommendation')
                }

        return aggregated
```

---

## 10. Testing Your Agent

Comprehensive testing ensures your agent works correctly and safely.

### Unit Tests

```python
# tests/agents/test_database_maintenance_agent.py

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from src.agents.database_maintenance import DatabaseMaintenanceAgent
from src.agents.base import AgentConfig, TaskContext, AgentCapability


class TestDatabaseMaintenanceAgent:
    """Unit tests for DatabaseMaintenanceAgent"""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies"""
        return {
            'llm_manager': Mock(),
            'tool_registry': Mock(),
            'state_manager': AsyncMock()
        }

    @pytest.fixture
    def agent_config(self):
        """Create agent configuration"""
        return AgentConfig(
            agent_id="test_agent_001",
            agent_type="maintenance",
            capabilities=[
                AgentCapability.DATABASE_READ,
                AgentCapability.SCHEMA_ANALYZE,
                AgentCapability.INDEX_MANAGE
            ],
            llm_config={"model": "test", "temperature": 0.3},
            safety_level="moderate",
            max_retries=3,
            timeout_seconds=300
        )

    @pytest.fixture
    def agent(self, agent_config, mock_dependencies):
        """Create agent instance"""
        return DatabaseMaintenanceAgent(
            config=agent_config,
            llm_manager=mock_dependencies['llm_manager'],
            tool_registry=mock_dependencies['tool_registry'],
            state_manager=mock_dependencies['state_manager']
        )

    @pytest.mark.asyncio
    async def test_plan_quick_maintenance(self, agent):
        """Test planning for quick maintenance"""
        task = TaskContext(
            task_id="test_task_001",
            task_description="Quick maintenance",
            input_data={
                'maintenance_type': 'quick',
                'tables': ['users', 'orders']
            },
            database_config={'database': 'test_db'}
        )

        plan = await agent.plan(task)

        # Verify plan structure
        assert len(plan) > 0
        assert plan[0]['tool'] == 'analyze_database_health'

        # Should have stats updates for each table
        stats_steps = [s for s in plan if s['tool'] == 'update_table_statistics']
        assert len(stats_steps) == 2

    @pytest.mark.asyncio
    async def test_plan_full_maintenance(self, agent):
        """Test planning for full maintenance"""
        task = TaskContext(
            task_id="test_task_002",
            task_description="Full maintenance",
            input_data={
                'maintenance_type': 'full',
                'tables': ['users'],
                'rebuild_indexes': True
            },
            database_config={'database': 'test_db'}
        )

        plan = await agent.plan(task)

        # Verify comprehensive plan
        tool_names = [step['tool'] for step in plan]
        assert 'analyze_database_health' in tool_names
        assert 'analyze_table_fragmentation' in tool_names
        assert 'rebuild_fragmented_indexes' in tool_names
        assert 'optimize_table' in tool_names
        assert 'update_table_statistics' in tool_names
        assert 'generate_maintenance_report' in tool_names

    def test_validate_safety_safe_operations(self, agent):
        """Test safety validation for safe operations"""
        step = {
            'tool': 'analyze_database_health',
            'params': {'database': 'test_db'}
        }

        # Mock tool
        mock_tool = Mock()
        mock_tool.risk_level = Mock(value='safe')
        agent.tool_registry.get_tool = Mock(return_value=mock_tool)

        validation = agent.validate_safety(step)

        assert validation['safe'] is True
        assert validation['requires_approval'] is False
        assert validation['risk_level'] == 'safe'

    def test_validate_safety_index_rebuild(self, agent):
        """Test safety validation for index rebuild"""
        step = {
            'tool': 'rebuild_fragmented_indexes',
            'params': {'database': 'test_db', 'table': 'users'}
        }

        # Mock tool
        mock_tool = Mock()
        mock_tool.risk_level = Mock(value='medium')
        agent.tool_registry.get_tool = Mock(return_value=mock_tool)

        validation = agent.validate_safety(step)

        assert validation['risk_level'] == 'medium'
        assert len(validation['risks']) > 0
        assert len(validation['mitigations']) > 0

    def test_validate_safety_strict_mode(self, agent):
        """Test safety validation in strict mode"""
        agent.config.safety_level = 'strict'

        step = {
            'tool': 'rebuild_fragmented_indexes',
            'params': {'database': 'test_db', 'table': 'users'}
        }

        mock_tool = Mock()
        mock_tool.risk_level = Mock(value='medium')
        agent.tool_registry.get_tool = Mock(return_value=mock_tool)

        validation = agent.validate_safety(step)

        # Strict mode should require approval for medium risk
        assert validation['requires_approval'] is True

    @pytest.mark.asyncio
    async def test_execute_step_success(self, agent, mock_dependencies):
        """Test successful step execution"""
        step = {
            'tool': 'analyze_table_fragmentation',
            'params': {'database': 'test_db', 'table': 'users'}
        }

        # Mock tool
        mock_tool = AsyncMock()
        mock_tool.max_execution_time = 60
        mock_tool.execute = AsyncMock(return_value={
            'fragmentation_percent': 15.5,
            'recommendation': 'No optimization needed'
        })

        agent.tool_registry.get_tool = Mock(return_value=mock_tool)
        agent.current_task = TaskContext(
            task_id="test_task",
            task_description="Test",
            input_data={},
            database_config={'database': 'test_db'}
        )

        result = await agent.execute_step(step)

        assert result['fragmentation_percent'] == 15.5
        assert mock_tool.execute.called

    @pytest.mark.asyncio
    async def test_execute_step_timeout(self, agent, mock_dependencies):
        """Test step execution timeout"""
        import asyncio

        step = {
            'tool': 'optimize_table',
            'params': {'database': 'test_db', 'table': 'users'}
        }

        # Mock tool that takes too long
        mock_tool = AsyncMock()
        mock_tool.max_execution_time = 1

        async def slow_execute(*args, **kwargs):
            await asyncio.sleep(5)
            return {}

        mock_tool.execute = slow_execute

        agent.tool_registry.get_tool = Mock(return_value=mock_tool)
        agent.current_task = TaskContext(
            task_id="test_task",
            task_description="Test",
            input_data={},
            database_config={'database': 'test_db'}
        )

        with pytest.raises(Exception, match="exceeded timeout"):
            await agent.execute_step(step)

    def test_aggregate_results(self, agent):
        """Test result aggregation"""
        agent.current_task = TaskContext(
            task_id="test",
            task_description="Test",
            input_data={'maintenance_type': 'full'}
        )

        actions = [
            {
                'step_index': 0,
                'step': {'tool': 'analyze_table_fragmentation', 'params': {'table': 'users'}},
                'result': {'fragmentation_percent': 25.0}
            },
            {
                'step_index': 1,
                'step': {'tool': 'rebuild_fragmented_indexes', 'params': {'table': 'users'}},
                'result': {'indexes_rebuilt': 3}
            },
            {
                'step_index': 2,
                'step': {'tool': 'update_table_statistics', 'params': {'table': 'users'}},
                'result': {'statistics_updated': True}
            }
        ]

        aggregated = agent._aggregate_results(actions)

        assert aggregated['actions_count'] == 3
        assert 'users' in aggregated['tables_processed']
        assert aggregated['indexes_rebuilt'] == 3
        assert aggregated['statistics_updated'] == 1
```

### Integration Tests

```python
# tests/integration/test_maintenance_workflow.py

import pytest
from src.agents.orchestrator import WorkflowOrchestrator, WorkflowConfig
from src.agents.manager import AgentManager
from src.agents.state.manager import StateManager


@pytest.mark.integration
class TestMaintenanceWorkflow:
    """Integration tests for maintenance workflows"""

    @pytest.fixture
    async def orchestrator(self, tmpdir):
        """Create orchestrator with real dependencies"""
        state_manager = StateManager(db_path=str(tmpdir / "state.db"))

        # Initialize other dependencies
        llm_manager = ...  # Real LLM manager
        tool_registry = ...  # Real tool registry with registered tools

        agent_manager = AgentManager(llm_manager, tool_registry, state_manager)
        approval_system = ...  # Real or mock approval system

        return WorkflowOrchestrator(agent_manager, state_manager, approval_system)

    @pytest.mark.asyncio
    async def test_full_maintenance_workflow(self, orchestrator):
        """Test complete maintenance workflow end-to-end"""
        config = WorkflowConfig(
            workflow_id="integration_test_001",
            workflow_name="Full Database Maintenance",
            description="Test full maintenance workflow",
            agent_type="maintenance",
            input_data={
                'maintenance_type': 'full',
                'tables': ['test_table'],
                'rebuild_indexes': True,
                'update_stats': True
            },
            database_config={
                'database': 'test_db',
                'host': 'localhost'
            }
        )

        result = await orchestrator.execute_workflow(config)

        # Verify successful completion
        assert result.status == "success"
        assert len(result.actions_taken) > 0
        assert len(result.checkpoints) > 0

        # Verify expected operations occurred
        tool_names = [action['step']['tool'] for action in result.actions_taken]
        assert 'analyze_database_health' in tool_names
        assert 'update_table_statistics' in tool_names

    @pytest.mark.asyncio
    async def test_workflow_recovery(self, orchestrator):
        """Test workflow recovery from checkpoint"""
        # TODO: Implement recovery test
        pass
```

---

## 11. Deployment Best Practices

### Configuration Management

```yaml
# config/agents/maintenance.yaml

maintenance_agent:
  default_config:
    safety_level: strict
    max_execution_time: 3600
    max_retries: 3

  capabilities:
    - database_read
    - schema_analyze
    - index_manage

  safety_constraints:
    - type: max_table_size
      max_rows: 5000000

    - type: production_hours
      allowed_hours: [0, 1, 2, 3, 4, 5, 22, 23]

    - type: backup_required
      before_operations:
        - repair_corrupted_tables
        - optimize_table

  monitoring:
    enabled: true
    metrics:
      - execution_time
      - tables_processed
      - indexes_rebuilt
      - errors_encountered

    alerts:
      - condition: execution_time > 1800
        action: notify_admin

      - condition: errors_encountered > 0
        action: create_incident
```

### Monitoring and Logging

```python
# Add comprehensive logging to your agent

import logging

logger = logging.getLogger(__name__)

class DatabaseMaintenanceAgent(BaseAgent):

    async def run(self, task: TaskContext) -> TaskResult:
        logger.info(
            f"Starting maintenance workflow",
            extra={
                'task_id': task.task_id,
                'maintenance_type': task.input_data.get('maintenance_type'),
                'database': task.database_config.get('database')
            }
        )

        try:
            result = await super().run(task)

            logger.info(
                f"Maintenance workflow completed successfully",
                extra={
                    'task_id': task.task_id,
                    'actions_count': len(result.actions_taken),
                    'execution_time': result.execution_time
                }
            )

            return result

        except Exception as e:
            logger.error(
                f"Maintenance workflow failed",
                extra={
                    'task_id': task.task_id,
                    'error': str(e)
                },
                exc_info=True
            )
            raise
```

### Production Deployment Checklist

- [ ] Comprehensive unit tests (>80% coverage)
- [ ] Integration tests with real database
- [ ] Safety validation tested in strict mode
- [ ] Checkpoint and recovery tested
- [ ] Error handling for all edge cases
- [ ] Logging configured properly
- [ ] Monitoring metrics defined
- [ ] Alert thresholds configured
- [ ] Documentation complete
- [ ] Code review completed
- [ ] Approval workflows tested
- [ ] Performance tested with production-size data
- [ ] Resource limits configured
- [ ] Timeout values tuned
- [ ] Rollback procedures documented

---

## 12. Advanced Patterns

### Multi-Step Workflows with Dependencies

```python
async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
    """Plan with explicit dependencies"""
    return [
        {
            'id': 'step_0',
            'tool': 'create_backup',
            'params': {...},
            'dependencies': []
        },
        {
            'id': 'step_1',
            'tool': 'analyze_schema',
            'params': {...},
            'dependencies': []
        },
        {
            'id': 'step_2',
            'tool': 'execute_migration',
            'params': {...},
            'dependencies': ['step_0', 'step_1']  # Wait for backup and analysis
        },
        {
            'id': 'step_3',
            'tool': 'verify_migration',
            'params': {...},
            'dependencies': ['step_2']
        },
        {
            'id': 'step_4',
            'tool': 'update_statistics',
            'params': {...},
            'dependencies': ['step_2']  # Can run in parallel with verification
        }
    ]
```

### Conditional Execution

```python
async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
    """Execute step with conditional logic"""

    # Check preconditions
    if 'condition' in step:
        condition_met = await self._evaluate_condition(step['condition'])
        if not condition_met:
            return {
                'skipped': True,
                'reason': f"Condition not met: {step['condition']}"
            }

    # Normal execution
    return await super().execute_step(step)

async def _evaluate_condition(self, condition: str) -> bool:
    """Evaluate a condition string"""
    # Example: "fragmentation > 30"
    # In real implementation, parse and evaluate
    return True
```

### Parallel Execution

```python
import asyncio

async def execute_parallel_steps(
    self,
    steps: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Execute multiple independent steps in parallel"""

    tasks = [self.execute_step(step) for step in steps]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle any exceptions
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Parallel step {i} failed: {result}")
            raise result

    return results
```

---

## 13. Debugging Techniques

### Enable Verbose Logging

```python
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add step-by-step execution logging
class DatabaseMaintenanceAgent(BaseAgent):
    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug(f"Executing step: {step}")
        result = await super().execute_step(step)
        logger.debug(f"Step result: {result}")
        return result
```

### Inspect Checkpoints

```python
# View all checkpoints for a task
checkpoints = await state_manager.get_checkpoints(task_id)
for cp_id in checkpoints:
    checkpoint = await state_manager.get_checkpoint(cp_id)
    print(f"{checkpoint.checkpoint_name}: {checkpoint.checkpoint_data}")
```

### Dry Run Mode

```python
class DatabaseMaintenanceAgent(BaseAgent):
    def __init__(self, *args, dry_run=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.dry_run = dry_run

    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        if self.dry_run:
            print(f"[DRY RUN] Would execute: {step}")
            return {'dry_run': True, 'step': step}

        return await super().execute_step(step)
```

---

## 14. Performance Optimization

### Tool Caching

```python
class CachedToolRegistry:
    def __init__(self):
        self._tool_cache = {}

    def get_tool(self, name: str):
        if name not in self._tool_cache:
            self._tool_cache[name] = self._load_tool(name)
        return self._tool_cache[name]
```

### Batch Operations

```python
async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
    """Use batch operations when possible"""
    tables = task.input_data.get('tables', [])

    return [
        {
            'tool': 'batch_update_statistics',
            'params': {'tables': tables},  # Update all at once
            'rationale': 'Batch update statistics for efficiency'
        }
    ]
```

### Connection Pooling

```python
class DatabaseMaintenanceAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection_pool = self._create_connection_pool()

    def _create_connection_pool(self):
        # Create database connection pool
        pass
```

---

## 15. Security Best Practices

1. **Input Validation**: Always validate task inputs
2. **SQL Injection Prevention**: Use parameterized queries
3. **Credential Management**: Never hardcode credentials
4. **Audit Logging**: Log all operations for audit
5. **Least Privilege**: Grant minimal necessary permissions
6. **Approval Requirements**: Require approval for critical ops
7. **Rate Limiting**: Prevent abuse with rate limits
8. **Encryption**: Encrypt sensitive data in checkpoints

---

## 16. Common Pitfalls

### Pitfall 1: Forgetting to Handle Tool Errors

**Problem:**
```python
async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
    tool = self.tool_registry.get_tool(step['tool'])
    return await tool.execute(step['params'], context)  # May raise exception
```

**Solution:**
```python
async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
    tool = self.tool_registry.get_tool(step['tool'])
    if not tool:
        raise ValueError(f"Tool not found: {step['tool']}")

    try:
        return await tool.execute(step['params'], context)
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        raise
```

### Pitfall 2: Not Substituting Variables

**Problem:** Using `${step_0.output.value}` literally instead of substituting.

**Solution:** Implement `_substitute_variables()` as shown in examples.

### Pitfall 3: Missing Safety Validation

**Problem:** Returning same validation for all operations.

**Solution:** Implement comprehensive validation based on tool risk and context.

### Pitfall 4: Poor Error Messages

**Problem:**
```python
raise Exception("Failed")
```

**Solution:**
```python
raise Exception(
    f"Tool '{tool_name}' execution failed for table '{table}': {str(error)}"
)
```

### Pitfall 5: Not Testing Edge Cases

**Problem:** Only testing happy path.

**Solution:** Test timeouts, missing tools, invalid inputs, approval rejections, etc.

---

## Conclusion

You now have a comprehensive understanding of building custom AI agents for AIShell. Remember:

1. **Start simple** - Build basic functionality first
2. **Test thoroughly** - Unit and integration tests are essential
3. **Validate safety** - Always implement comprehensive safety checks
4. **Handle errors** - Expect things to fail and handle gracefully
5. **Document well** - Future you will thank present you
6. **Iterate** - Continuously improve based on real-world usage

Happy agent building!
