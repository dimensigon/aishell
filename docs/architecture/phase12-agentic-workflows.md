# Phase 12: Agentic AI Workflows Architecture

## Executive Summary

This document defines the architecture for Phase 12 of AIShell, implementing autonomous AI agent workflows for database operations. The system provides intelligent, multi-step task execution with safety controls, enabling automated database backup, schema migration, and query optimization through orchestrated AI agents.

**Version:** 1.0.0
**Date:** 2025-10-04
**Status:** Architecture Design

---

## 1. Architecture Overview

### 1.1 Core Principles

1. **Autonomy with Oversight**: Agents operate autonomously within defined boundaries, requiring human approval for critical operations
2. **Tool-Based Execution**: Agents use a registry of validated tools rather than arbitrary code execution
3. **State Persistence**: All workflow states are checkpointed for recovery and audit
4. **Safety-First**: Multi-layer safety mechanisms prevent destructive operations
5. **Composability**: Workflows can be composed from reusable agent tasks

### 1.2 System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    AIShell CLI Interface                    │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼──────┐  ┌────────▼─────────┐
│ Workflow       │  │ Agent       │  │ Safety           │
│ Orchestrator   │◄─┤ Manager     │◄─┤ Controller       │
└───────┬────────┘  └──────┬──────┘  └────────┬─────────┘
        │                  │                   │
        │         ┌────────▼────────┐          │
        │         │ Tool Registry   │          │
        │         └────────┬────────┘          │
        │                  │                   │
┌───────▼────────┬─────────▼────────┬──────────▼─────────┐
│ State Manager  │ LLM Manager      │ Approval System    │
└───────┬────────┴─────────┬────────┴──────────┬─────────┘
        │                  │                   │
        └──────────────────┼───────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼────────┐  ┌──────▼──────┐  ┌──────▼──────┐
│ Database       │  │ MCP Clients │  │ File System │
│ Module         │  │             │  │             │
└────────────────┘  └─────────────┘  └─────────────┘
```

### 1.3 Integration Points

- **LLM Manager**: Provides reasoning, planning, and tool selection capabilities
- **Database Module**: Executes validated SQL operations with risk analysis
- **MCP Clients**: Manages database connections (PostgreSQL, Oracle, SQLite)
- **File System**: Stores backups, migration scripts, and workflow artifacts

---

## 2. Agent Framework Architecture

### 2.1 Base Agent Class Hierarchy

```python
BaseAgent (ABC)
    ├── Capabilities
    ├── Tool Registry Access
    ├── State Management
    ├── LLM Integration
    └── Safety Validation
        │
        ├── DatabaseAgent (ABC)
        │   ├── Database Connection Pool
        │   ├── Transaction Management
        │   └── Risk Analysis Integration
        │       │
        │       ├── BackupAgent
        │       │   ├── Full Backup
        │       │   ├── Incremental Backup
        │       │   ├── Point-in-Time Recovery
        │       │   └── Backup Validation
        │       │
        │       ├── MigrationAgent
        │       │   ├── Schema Analysis
        │       │   ├── Migration Planning
        │       │   ├── Rollback Strategy
        │       │   └── Data Transformation
        │       │
        │       └── OptimizerAgent
        │           ├── Query Analysis
        │           ├── Index Recommendation
        │           ├── Statistics Update
        │           └── Performance Monitoring
        │
        └── CoordinatorAgent
            ├── Workflow Decomposition
            ├── Agent Delegation
            └── Result Aggregation
```

### 2.2 Agent Base Class Design

```python
# src/agents/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass
import asyncio


class AgentState(Enum):
    """Agent execution states"""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING_APPROVAL = "waiting_approval"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentCapability(Enum):
    """Agent capabilities for tool selection"""
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


@dataclass
class AgentConfig:
    """Agent configuration"""
    agent_id: str
    agent_type: str
    capabilities: List[AgentCapability]
    llm_config: Dict[str, Any]
    safety_level: str  # strict, moderate, permissive
    max_retries: int = 3
    timeout_seconds: int = 300


@dataclass
class TaskContext:
    """Context for agent task execution"""
    task_id: str
    task_description: str
    input_data: Dict[str, Any]
    database_config: Optional[Dict[str, Any]] = None
    workflow_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TaskResult:
    """Result of agent task execution"""
    task_id: str
    agent_id: str
    status: str  # success, failure, requires_approval
    output_data: Dict[str, Any]
    actions_taken: List[Dict[str, Any]]
    reasoning: str
    execution_time: float
    checkpoints: List[str]
    error: Optional[str] = None


class BaseAgent(ABC):
    """
    Base class for all agentic workflows

    Provides core functionality:
    - Tool-based execution
    - State management
    - LLM-powered reasoning
    - Safety validation
    - Checkpoint/recovery
    """

    def __init__(self, config: AgentConfig, llm_manager, tool_registry, state_manager):
        self.config = config
        self.llm_manager = llm_manager
        self.tool_registry = tool_registry
        self.state_manager = state_manager

        self.state = AgentState.IDLE
        self.current_task: Optional[TaskContext] = None
        self.execution_history: List[TaskResult] = []

    @abstractmethod
    async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
        """
        Create execution plan for task

        Returns:
            List of planned steps with tools and parameters
        """
        pass

    @abstractmethod
    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single planned step

        Returns:
            Step execution result
        """
        pass

    @abstractmethod
    def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate safety of planned step

        Returns:
            Validation result with approval requirement
        """
        pass

    async def run(self, task: TaskContext) -> TaskResult:
        """
        Main execution loop

        1. Plan task into steps
        2. Validate each step
        3. Execute with checkpointing
        4. Handle approval requests
        5. Return results
        """
        self.current_task = task
        self.state = AgentState.PLANNING

        try:
            # Create execution plan
            plan = await self.plan(task)
            await self.state_manager.save_checkpoint(
                task.task_id, "plan_created", {"plan": plan}
            )

            # Execute steps
            self.state = AgentState.EXECUTING
            actions_taken = []

            for i, step in enumerate(plan):
                # Validate safety
                validation = self.validate_safety(step)

                if validation['requires_approval']:
                    self.state = AgentState.WAITING_APPROVAL
                    approval = await self._request_approval(step, validation)

                    if not approval['approved']:
                        raise Exception(f"Step {i} rejected: {approval['reason']}")

                # Execute step
                result = await self.execute_step(step)
                actions_taken.append({
                    'step_index': i,
                    'step': step,
                    'result': result
                })

                # Checkpoint after each step
                await self.state_manager.save_checkpoint(
                    task.task_id, f"step_{i}_completed", result
                )

            # Complete
            self.state = AgentState.COMPLETED
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.config.agent_id,
                status="success",
                output_data=self._aggregate_results(actions_taken),
                actions_taken=actions_taken,
                reasoning=await self._generate_reasoning(plan, actions_taken),
                execution_time=0.0,  # Calculated by orchestrator
                checkpoints=await self.state_manager.get_checkpoints(task.task_id)
            )

        except Exception as e:
            self.state = AgentState.FAILED
            return TaskResult(
                task_id=task.task_id,
                agent_id=self.config.agent_id,
                status="failure",
                output_data={},
                actions_taken=actions_taken,
                reasoning=str(e),
                execution_time=0.0,
                checkpoints=[],
                error=str(e)
            )

    async def _request_approval(self, step: Dict[str, Any],
                               validation: Dict[str, Any]) -> Dict[str, Any]:
        """Request human approval for risky step"""
        # Implementation delegates to approval system
        pass

    def _aggregate_results(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate results from all actions"""
        # Default implementation
        return {'actions_count': len(actions)}

    async def _generate_reasoning(self, plan: List[Dict[str, Any]],
                                  actions: List[Dict[str, Any]]) -> str:
        """Generate natural language reasoning for execution"""
        prompt = f"""Explain the execution of this plan:

Plan: {plan}
Actions Taken: {actions}

Provide a clear summary of what was done and why."""

        return await self.llm_manager.generate(prompt, max_tokens=200)
```

### 2.3 Agent Capabilities Matrix

| Agent Type | Read DB | Write DB | DDL | Backup | Restore | Schema Analysis | Query Optimize |
|------------|---------|----------|-----|--------|---------|----------------|----------------|
| BackupAgent | ✓ | - | - | ✓ | ✓ | ✓ | - |
| MigrationAgent | ✓ | ✓ | ✓ | - | - | ✓ | - |
| OptimizerAgent | ✓ | - | ✓ (indexes) | - | - | ✓ | ✓ |
| CoordinatorAgent | - | - | - | - | - | - | - |

---

## 3. Specialized Agent Designs

### 3.1 BackupAgent

**Purpose**: Automated database backup with intelligent scheduling and validation

**Capabilities**:
- Full database backups
- Incremental/differential backups
- Point-in-time recovery preparation
- Backup integrity validation
- Automated retention management

**Tools**:
- `backup_database_full`: Create full backup
- `backup_database_incremental`: Create incremental backup
- `validate_backup`: Verify backup integrity
- `list_backups`: List available backups
- `restore_backup`: Restore from backup (requires approval)
- `calculate_backup_size`: Estimate backup size
- `compress_backup`: Compress backup files

**Planning Logic**:
```python
async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
    backup_type = task.input_data.get('backup_type', 'full')

    plan = [
        {
            'tool': 'calculate_backup_size',
            'params': {'database': task.database_config['database']}
        },
        {
            'tool': f'backup_database_{backup_type}',
            'params': {
                'database': task.database_config['database'],
                'destination': task.input_data.get('destination'),
                'compression': True
            }
        },
        {
            'tool': 'validate_backup',
            'params': {'backup_path': '${step_1.output.backup_path}'}
        }
    ]

    # Add retention cleanup if configured
    if task.input_data.get('cleanup_old', False):
        plan.append({
            'tool': 'cleanup_old_backups',
            'params': {
                'retention_days': task.input_data.get('retention_days', 30)
            }
        })

    return plan
```

**Safety Validation**:
- Full backups: Low risk, no approval needed
- Restore operations: High risk, requires approval
- Cleanup operations: Medium risk, requires approval if deleting backups < 7 days old

### 3.2 MigrationAgent

**Purpose**: Intelligent schema migration with safety checks and rollback capability

**Capabilities**:
- Schema change analysis
- Migration script generation
- Dependency resolution
- Data preservation validation
- Automatic rollback preparation

**Tools**:
- `analyze_schema`: Analyze current schema
- `generate_migration`: Generate migration SQL
- `validate_migration`: Check migration safety
- `create_rollback`: Generate rollback script
- `execute_migration`: Execute migration (requires approval)
- `verify_data_integrity`: Verify data after migration
- `backup_before_migration`: Create safety backup

**Planning Logic**:
```python
async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
    migration_type = task.input_data.get('migration_type')
    target_schema = task.input_data.get('target_schema')

    plan = [
        # Always backup first
        {
            'tool': 'backup_before_migration',
            'params': {'database': task.database_config['database']}
        },
        # Analyze current state
        {
            'tool': 'analyze_schema',
            'params': {'database': task.database_config['database']}
        },
        # Generate migration
        {
            'tool': 'generate_migration',
            'params': {
                'current_schema': '${step_1.output.schema}',
                'target_schema': target_schema,
                'migration_type': migration_type
            }
        },
        # Validate safety
        {
            'tool': 'validate_migration',
            'params': {
                'migration_sql': '${step_2.output.migration_sql}',
                'check_data_loss': True
            }
        },
        # Create rollback
        {
            'tool': 'create_rollback',
            'params': {
                'migration_sql': '${step_2.output.migration_sql}',
                'current_schema': '${step_1.output.schema}'
            }
        },
        # Execute migration (requires approval)
        {
            'tool': 'execute_migration',
            'params': {
                'migration_sql': '${step_2.output.migration_sql}',
                'rollback_sql': '${step_4.output.rollback_sql}'
            }
        },
        # Verify integrity
        {
            'tool': 'verify_data_integrity',
            'params': {
                'tables': '${step_1.output.affected_tables}'
            }
        }
    ]

    return plan
```

**Safety Validation**:
- Schema analysis: No risk
- Migration execution: Critical risk, always requires approval
- Data validation: No risk
- Automatic rollback trigger if validation fails

### 3.3 OptimizerAgent

**Purpose**: Intelligent query and database optimization

**Capabilities**:
- Query performance analysis
- Index recommendation
- Statistics updates
- Execution plan analysis
- Slow query identification

**Tools**:
- `analyze_query_performance`: Analyze query execution
- `recommend_indexes`: Suggest beneficial indexes
- `create_index`: Create recommended index (requires approval)
- `update_statistics`: Update table statistics
- `analyze_slow_queries`: Identify slow queries
- `generate_optimized_query`: Rewrite query for better performance
- `estimate_improvement`: Estimate optimization impact

**Planning Logic**:
```python
async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
    optimization_target = task.input_data.get('target')

    if optimization_target == 'query':
        return await self._plan_query_optimization(task)
    elif optimization_target == 'database':
        return await self._plan_database_optimization(task)
    else:
        return await self._plan_general_optimization(task)

async def _plan_query_optimization(self, task: TaskContext) -> List[Dict[str, Any]]:
    query = task.input_data.get('query')

    return [
        {
            'tool': 'analyze_query_performance',
            'params': {'query': query}
        },
        {
            'tool': 'generate_optimized_query',
            'params': {
                'query': query,
                'execution_plan': '${step_0.output.execution_plan}'
            }
        },
        {
            'tool': 'recommend_indexes',
            'params': {
                'query': query,
                'current_indexes': '${step_0.output.used_indexes}'
            }
        },
        {
            'tool': 'estimate_improvement',
            'params': {
                'original_query': query,
                'optimized_query': '${step_1.output.optimized_query}',
                'recommended_indexes': '${step_2.output.indexes}'
            }
        }
    ]
```

**Safety Validation**:
- Query analysis: No risk
- Index creation: Medium risk, requires approval for large tables
- Statistics update: Low risk, no approval needed
- Query rewriting: No risk (suggestion only)

### 3.4 CoordinatorAgent

**Purpose**: Decompose complex workflows and coordinate multiple specialized agents

**Capabilities**:
- Task decomposition
- Agent selection and delegation
- Result aggregation
- Dependency management
- Parallel execution coordination

**Planning Logic**:
```python
async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
    """
    Coordinator doesn't use traditional tools, instead it orchestrates
    other agents through the AgentManager
    """

    # Use LLM to decompose complex task
    decomposition_prompt = f"""
    Decompose this database task into subtasks for specialized agents:

    Task: {task.task_description}
    Input: {task.input_data}

    Available agents:
    - BackupAgent: Database backup and restore
    - MigrationAgent: Schema migrations
    - OptimizerAgent: Query and database optimization

    Return JSON with subtasks:
    {{
        "subtasks": [
            {{
                "agent_type": "BackupAgent",
                "task_description": "...",
                "input_data": {{}},
                "dependencies": []
            }}
        ]
    }}
    """

    decomposition = await self.llm_manager.generate(
        decomposition_prompt, max_tokens=1000
    )

    return json.loads(decomposition)['subtasks']
```

---

## 4. Tool Registry System

### 4.1 Tool Registry Architecture

```python
# src/agents/tools/registry.py

from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass
from enum import Enum


class ToolCategory(Enum):
    """Tool categorization"""
    DATABASE_READ = "database_read"
    DATABASE_WRITE = "database_write"
    DATABASE_DDL = "database_ddl"
    FILE_SYSTEM = "file_system"
    BACKUP = "backup"
    ANALYSIS = "analysis"


class ToolRiskLevel(Enum):
    """Risk levels for tools"""
    SAFE = "safe"          # Read-only, no side effects
    LOW = "low"            # Minor modifications
    MEDIUM = "medium"      # Significant modifications
    HIGH = "high"          # Potentially destructive
    CRITICAL = "critical"  # Irreversible operations


@dataclass
class ToolDefinition:
    """Tool definition with metadata"""
    name: str
    description: str
    category: ToolCategory
    risk_level: ToolRiskLevel
    required_capabilities: List[AgentCapability]
    parameters_schema: Dict[str, Any]
    returns_schema: Dict[str, Any]
    implementation: Callable

    # Safety constraints
    requires_approval: bool
    max_execution_time: int  # seconds
    rate_limit: Optional[int] = None  # calls per minute

    # Documentation
    examples: List[Dict[str, Any]]

    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """Validate parameters against schema"""
        # JSON schema validation
        pass

    async def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool with validated parameters"""
        if not self.validate_parameters(params):
            raise ValueError(f"Invalid parameters for tool {self.name}")

        return await self.implementation(params, context)


class ToolRegistry:
    """
    Central registry for all agent tools

    Provides:
    - Tool registration and discovery
    - Capability-based filtering
    - Safety validation
    - Execution tracking
    """

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._execution_log: List[Dict[str, Any]] = []

    def register_tool(self, tool: ToolDefinition):
        """Register a new tool"""
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name} already registered")

        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get tool by name"""
        return self._tools.get(name)

    def find_tools(self,
                   category: Optional[ToolCategory] = None,
                   max_risk: Optional[ToolRiskLevel] = None,
                   capabilities: Optional[List[AgentCapability]] = None) -> List[ToolDefinition]:
        """Find tools matching criteria"""
        tools = list(self._tools.values())

        if category:
            tools = [t for t in tools if t.category == category]

        if max_risk:
            risk_levels = [ToolRiskLevel.SAFE, ToolRiskLevel.LOW, ToolRiskLevel.MEDIUM,
                          ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL]
            max_index = risk_levels.index(max_risk)
            tools = [t for t in tools if risk_levels.index(t.risk_level) <= max_index]

        if capabilities:
            tools = [t for t in tools
                    if all(cap in t.required_capabilities for cap in capabilities)]

        return tools

    def get_tool_description(self, name: str) -> str:
        """Get human-readable tool description for LLM"""
        tool = self.get_tool(name)
        if not tool:
            return ""

        return f"""
Tool: {tool.name}
Description: {tool.description}
Category: {tool.category.value}
Risk Level: {tool.risk_level.value}
Requires Approval: {tool.requires_approval}

Parameters:
{json.dumps(tool.parameters_schema, indent=2)}

Returns:
{json.dumps(tool.returns_schema, indent=2)}

Examples:
{json.dumps(tool.examples, indent=2)}
"""

    def get_available_tools_for_llm(self,
                                    capabilities: List[AgentCapability]) -> str:
        """
        Get formatted tool descriptions for LLM prompt
        """
        tools = self.find_tools(capabilities=capabilities)

        descriptions = [self.get_tool_description(t.name) for t in tools]

        return "\n\n".join(descriptions)
```

### 4.2 Core Tool Implementations

#### Database Tools

```python
# src/agents/tools/database_tools.py

async def backup_database_full(params: Dict[str, Any],
                               context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create full database backup

    Parameters:
        database: Database name
        destination: Backup destination path
        compression: Enable compression (default: true)

    Returns:
        backup_path: Path to created backup
        size_bytes: Backup file size
        duration_seconds: Backup duration
        checksum: Backup file checksum
    """
    database_module = context['database_module']

    # Implementation
    backup_path = await database_module.create_backup(
        database=params['database'],
        backup_type='full',
        destination=params['destination'],
        compression=params.get('compression', True)
    )

    return {
        'backup_path': backup_path,
        'size_bytes': os.path.getsize(backup_path),
        'duration_seconds': 0,  # Calculated
        'checksum': calculate_checksum(backup_path)
    }


async def analyze_schema(params: Dict[str, Any],
                        context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze database schema

    Parameters:
        database: Database name
        include_indexes: Include index information
        include_constraints: Include constraint information

    Returns:
        tables: List of table definitions
        indexes: List of indexes
        constraints: List of constraints
        statistics: Schema statistics
    """
    database_module = context['database_module']

    schema_info = await database_module.get_schema_info(
        database=params['database'],
        include_indexes=params.get('include_indexes', True),
        include_constraints=params.get('include_constraints', True)
    )

    return schema_info


async def recommend_indexes(params: Dict[str, Any],
                           context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recommend indexes for query optimization

    Parameters:
        query: SQL query to optimize
        current_indexes: List of existing indexes
        max_recommendations: Maximum number of recommendations

    Returns:
        recommendations: List of index recommendations
        estimated_improvement: Estimated performance improvement
        creation_cost: Estimated cost to create indexes
    """
    llm_manager = context['llm_manager']

    # Use LLM to analyze query and recommend indexes
    prompt = f"""
    Analyze this SQL query and recommend indexes:

    Query: {params['query']}
    Current Indexes: {params.get('current_indexes', [])}

    Return JSON with index recommendations:
    {{
        "recommendations": [
            {{
                "table": "table_name",
                "columns": ["col1", "col2"],
                "type": "btree",
                "rationale": "...",
                "estimated_improvement": "50%"
            }}
        ]
    }}
    """

    response = await llm_manager.generate(prompt, max_tokens=500)

    return json.loads(response)
```

### 4.3 Tool Registration

```python
# src/agents/tools/__init__.py

def register_core_tools(registry: ToolRegistry):
    """Register all core tools with the registry"""

    # Backup tools
    registry.register_tool(ToolDefinition(
        name="backup_database_full",
        description="Create full database backup with compression",
        category=ToolCategory.BACKUP,
        risk_level=ToolRiskLevel.LOW,
        required_capabilities=[AgentCapability.DATABASE_READ, AgentCapability.BACKUP_CREATE],
        parameters_schema={
            "type": "object",
            "properties": {
                "database": {"type": "string"},
                "destination": {"type": "string"},
                "compression": {"type": "boolean", "default": True}
            },
            "required": ["database", "destination"]
        },
        returns_schema={
            "type": "object",
            "properties": {
                "backup_path": {"type": "string"},
                "size_bytes": {"type": "integer"},
                "duration_seconds": {"type": "number"},
                "checksum": {"type": "string"}
            }
        },
        implementation=backup_database_full,
        requires_approval=False,
        max_execution_time=3600,
        examples=[{
            "params": {
                "database": "production",
                "destination": "/backups/prod_backup.sql.gz",
                "compression": True
            },
            "expected_output": {
                "backup_path": "/backups/prod_backup.sql.gz",
                "size_bytes": 1024000,
                "duration_seconds": 45.2,
                "checksum": "abc123..."
            }
        }]
    ))

    # Schema analysis tools
    registry.register_tool(ToolDefinition(
        name="analyze_schema",
        description="Analyze database schema structure and statistics",
        category=ToolCategory.ANALYSIS,
        risk_level=ToolRiskLevel.SAFE,
        required_capabilities=[AgentCapability.DATABASE_READ, AgentCapability.SCHEMA_ANALYZE],
        parameters_schema={
            "type": "object",
            "properties": {
                "database": {"type": "string"},
                "include_indexes": {"type": "boolean", "default": True},
                "include_constraints": {"type": "boolean", "default": True}
            },
            "required": ["database"]
        },
        returns_schema={
            "type": "object",
            "properties": {
                "tables": {"type": "array"},
                "indexes": {"type": "array"},
                "constraints": {"type": "array"},
                "statistics": {"type": "object"}
            }
        },
        implementation=analyze_schema,
        requires_approval=False,
        max_execution_time=60,
        examples=[{
            "params": {"database": "production", "include_indexes": True},
            "expected_output": {
                "tables": ["users", "orders", "products"],
                "indexes": [{"name": "idx_users_email", "table": "users"}],
                "statistics": {"total_tables": 3, "total_rows": 100000}
            }
        }]
    ))

    # Migration tools
    registry.register_tool(ToolDefinition(
        name="execute_migration",
        description="Execute schema migration with rollback capability",
        category=ToolCategory.DATABASE_DDL,
        risk_level=ToolRiskLevel.CRITICAL,
        required_capabilities=[AgentCapability.DATABASE_WRITE, AgentCapability.SCHEMA_MODIFY],
        parameters_schema={
            "type": "object",
            "properties": {
                "migration_sql": {"type": "string"},
                "rollback_sql": {"type": "string"},
                "dry_run": {"type": "boolean", "default": False}
            },
            "required": ["migration_sql", "rollback_sql"]
        },
        returns_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "executed_statements": {"type": "integer"},
                "rollback_available": {"type": "boolean"},
                "affected_objects": {"type": "array"}
            }
        },
        implementation=execute_migration,
        requires_approval=True,  # Always requires approval
        max_execution_time=1800,
        examples=[{
            "params": {
                "migration_sql": "ALTER TABLE users ADD COLUMN phone VARCHAR(20)",
                "rollback_sql": "ALTER TABLE users DROP COLUMN phone"
            },
            "expected_output": {
                "success": True,
                "executed_statements": 1,
                "rollback_available": True,
                "affected_objects": ["users"]
            }
        }]
    ))
```

---

## 5. Workflow Orchestration Engine

### 5.1 Orchestrator Architecture

```python
# src/agents/orchestrator.py

from typing import Dict, Any, List, Optional
import asyncio
from dataclasses import dataclass
from enum import Enum


class WorkflowState(Enum):
    """Workflow execution states"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowConfig:
    """Workflow configuration"""
    workflow_id: str
    workflow_name: str
    description: str
    agent_type: str
    input_data: Dict[str, Any]
    database_config: Optional[Dict[str, Any]] = None
    max_execution_time: int = 3600
    enable_checkpoints: bool = True
    approval_callback: Optional[Callable] = None


class WorkflowOrchestrator:
    """
    Orchestrates agent workflow execution

    Responsibilities:
    - Agent lifecycle management
    - Execution monitoring
    - Checkpoint/recovery
    - Approval management
    - Result aggregation
    """

    def __init__(self, agent_manager, state_manager, approval_system):
        self.agent_manager = agent_manager
        self.state_manager = state_manager
        self.approval_system = approval_system

        self.active_workflows: Dict[str, Dict[str, Any]] = {}

    async def execute_workflow(self, config: WorkflowConfig) -> TaskResult:
        """
        Execute agent workflow

        1. Create agent instance
        2. Initialize task context
        3. Execute with monitoring
        4. Handle approvals
        5. Return results
        """

        # Create agent
        agent = self.agent_manager.create_agent(
            agent_type=config.agent_type,
            config=self._build_agent_config(config)
        )

        # Create task context
        task = TaskContext(
            task_id=config.workflow_id,
            task_description=config.description,
            input_data=config.input_data,
            database_config=config.database_config,
            workflow_id=config.workflow_id
        )

        # Register workflow
        self.active_workflows[config.workflow_id] = {
            'config': config,
            'agent': agent,
            'task': task,
            'state': WorkflowState.RUNNING,
            'start_time': time.time()
        }

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                agent.run(task),
                timeout=config.max_execution_time
            )

            self.active_workflows[config.workflow_id]['state'] = WorkflowState.COMPLETED
            return result

        except asyncio.TimeoutError:
            self.active_workflows[config.workflow_id]['state'] = WorkflowState.FAILED
            raise Exception(f"Workflow {config.workflow_id} exceeded timeout")

        except Exception as e:
            self.active_workflows[config.workflow_id]['state'] = WorkflowState.FAILED
            raise

    async def execute_multi_agent_workflow(self,
                                          coordinator_task: TaskContext) -> TaskResult:
        """
        Execute workflow requiring multiple agents

        Uses CoordinatorAgent to decompose and delegate
        """

        coordinator = self.agent_manager.create_agent(
            agent_type="coordinator",
            config=self._build_agent_config({
                'workflow_id': coordinator_task.task_id,
                'workflow_name': 'Multi-Agent Workflow'
            })
        )

        # Coordinator plans subtasks
        subtasks = await coordinator.plan(coordinator_task)

        # Execute subtasks in order, respecting dependencies
        results = []
        for subtask_def in subtasks:
            # Check dependencies
            if subtask_def.get('dependencies'):
                await self._wait_for_dependencies(
                    subtask_def['dependencies'], results
                )

            # Execute subtask
            subtask_config = WorkflowConfig(
                workflow_id=f"{coordinator_task.task_id}_sub_{len(results)}",
                workflow_name=subtask_def['task_description'],
                description=subtask_def['task_description'],
                agent_type=subtask_def['agent_type'],
                input_data=subtask_def['input_data']
            )

            result = await self.execute_workflow(subtask_config)
            results.append(result)

        # Aggregate results
        return self._aggregate_multi_agent_results(coordinator_task, results)

    async def pause_workflow(self, workflow_id: str):
        """Pause running workflow"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            workflow['state'] = WorkflowState.PAUSED
            workflow['agent'].state = AgentState.PAUSED

    async def resume_workflow(self, workflow_id: str):
        """Resume paused workflow"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            if workflow['state'] == WorkflowState.PAUSED:
                workflow['state'] = WorkflowState.RUNNING
                workflow['agent'].state = AgentState.EXECUTING

    async def cancel_workflow(self, workflow_id: str):
        """Cancel running workflow"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            workflow['state'] = WorkflowState.CANCELLED
            # Cleanup resources

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current workflow status"""
        if workflow_id not in self.active_workflows:
            return {'status': 'not_found'}

        workflow = self.active_workflows[workflow_id]

        return {
            'workflow_id': workflow_id,
            'state': workflow['state'].value,
            'agent_state': workflow['agent'].state.value,
            'elapsed_time': time.time() - workflow['start_time'],
            'current_step': len(workflow['agent'].execution_history)
        }
```

### 5.2 Agent Manager

```python
# src/agents/manager.py

class AgentManager:
    """
    Manages agent instances and lifecycle

    Responsibilities:
    - Agent creation and configuration
    - Resource management
    - Agent registry
    """

    def __init__(self, llm_manager, tool_registry, state_manager):
        self.llm_manager = llm_manager
        self.tool_registry = tool_registry
        self.state_manager = state_manager

        self._agent_classes: Dict[str, Type[BaseAgent]] = {}
        self._active_agents: Dict[str, BaseAgent] = {}

        # Register default agents
        self._register_default_agents()

    def _register_default_agents(self):
        """Register built-in agent types"""
        from src.agents.database.backup import BackupAgent
        from src.agents.database.migration import MigrationAgent
        from src.agents.database.optimizer import OptimizerAgent
        from src.agents.coordinator import CoordinatorAgent

        self.register_agent_class("backup", BackupAgent)
        self.register_agent_class("migration", MigrationAgent)
        self.register_agent_class("optimizer", OptimizerAgent)
        self.register_agent_class("coordinator", CoordinatorAgent)

    def register_agent_class(self, agent_type: str, agent_class: Type[BaseAgent]):
        """Register custom agent type"""
        self._agent_classes[agent_type] = agent_class

    def create_agent(self, agent_type: str, config: Dict[str, Any]) -> BaseAgent:
        """Create agent instance"""
        if agent_type not in self._agent_classes:
            raise ValueError(f"Unknown agent type: {agent_type}")

        agent_class = self._agent_classes[agent_type]

        agent_config = AgentConfig(
            agent_id=config.get('agent_id', f"{agent_type}_{int(time.time())}"),
            agent_type=agent_type,
            capabilities=self._get_agent_capabilities(agent_type),
            llm_config=config.get('llm_config', {}),
            safety_level=config.get('safety_level', 'strict'),
            max_retries=config.get('max_retries', 3),
            timeout_seconds=config.get('timeout_seconds', 300)
        )

        agent = agent_class(
            config=agent_config,
            llm_manager=self.llm_manager,
            tool_registry=self.tool_registry,
            state_manager=self.state_manager
        )

        self._active_agents[agent_config.agent_id] = agent

        return agent

    def _get_agent_capabilities(self, agent_type: str) -> List[AgentCapability]:
        """Get default capabilities for agent type"""
        capability_map = {
            "backup": [
                AgentCapability.DATABASE_READ,
                AgentCapability.BACKUP_CREATE,
                AgentCapability.BACKUP_RESTORE,
                AgentCapability.FILE_WRITE
            ],
            "migration": [
                AgentCapability.DATABASE_READ,
                AgentCapability.DATABASE_WRITE,
                AgentCapability.DATABASE_DDL,
                AgentCapability.SCHEMA_ANALYZE,
                AgentCapability.SCHEMA_MODIFY
            ],
            "optimizer": [
                AgentCapability.DATABASE_READ,
                AgentCapability.QUERY_OPTIMIZE,
                AgentCapability.INDEX_MANAGE,
                AgentCapability.SCHEMA_ANALYZE
            ],
            "coordinator": []  # Coordinator uses other agents
        }

        return capability_map.get(agent_type, [])
```

---

## 6. State Management and Checkpointing

### 6.1 State Manager Design

```python
# src/agents/state/manager.py

from typing import Dict, Any, List, Optional
import sqlite3
import json
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Checkpoint:
    """Workflow checkpoint"""
    checkpoint_id: str
    task_id: str
    checkpoint_name: str
    checkpoint_data: Dict[str, Any]
    timestamp: datetime
    sequence_number: int


class StateManager:
    """
    Manages workflow state and checkpointing

    Responsibilities:
    - State persistence
    - Checkpoint creation/retrieval
    - Recovery support
    - Audit logging
    """

    def __init__(self, db_path: str = ".aishell/workflow_state.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize state database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                checkpoint_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                checkpoint_name TEXT NOT NULL,
                checkpoint_data TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                sequence_number INTEGER NOT NULL,
                INDEX idx_task_id (task_id),
                INDEX idx_sequence (task_id, sequence_number)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_state (
                task_id TEXT PRIMARY KEY,
                workflow_type TEXT NOT NULL,
                current_state TEXT NOT NULL,
                state_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_log (
                log_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                INDEX idx_task_log (task_id)
            )
        """)

        conn.commit()
        conn.close()

    async def save_checkpoint(self, task_id: str, checkpoint_name: str,
                            data: Dict[str, Any]) -> str:
        """Save workflow checkpoint"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get next sequence number
        cursor.execute(
            "SELECT COALESCE(MAX(sequence_number), 0) + 1 FROM checkpoints WHERE task_id = ?",
            (task_id,)
        )
        sequence_number = cursor.fetchone()[0]

        checkpoint_id = f"{task_id}_cp_{sequence_number}"

        cursor.execute("""
            INSERT INTO checkpoints
            (checkpoint_id, task_id, checkpoint_name, checkpoint_data, timestamp, sequence_number)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            checkpoint_id,
            task_id,
            checkpoint_name,
            json.dumps(data),
            datetime.utcnow().isoformat(),
            sequence_number
        ))

        conn.commit()
        conn.close()

        return checkpoint_id

    async def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Retrieve specific checkpoint"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT checkpoint_id, task_id, checkpoint_name, checkpoint_data,
                   timestamp, sequence_number
            FROM checkpoints
            WHERE checkpoint_id = ?
        """, (checkpoint_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Checkpoint(
            checkpoint_id=row[0],
            task_id=row[1],
            checkpoint_name=row[2],
            checkpoint_data=json.loads(row[3]),
            timestamp=datetime.fromisoformat(row[4]),
            sequence_number=row[5]
        )

    async def get_checkpoints(self, task_id: str) -> List[str]:
        """Get all checkpoint IDs for task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT checkpoint_id
            FROM checkpoints
            WHERE task_id = ?
            ORDER BY sequence_number
        """, (task_id,))

        checkpoints = [row[0] for row in cursor.fetchall()]
        conn.close()

        return checkpoints

    async def get_latest_checkpoint(self, task_id: str) -> Optional[Checkpoint]:
        """Get most recent checkpoint for task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT checkpoint_id, task_id, checkpoint_name, checkpoint_data,
                   timestamp, sequence_number
            FROM checkpoints
            WHERE task_id = ?
            ORDER BY sequence_number DESC
            LIMIT 1
        """, (task_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Checkpoint(
            checkpoint_id=row[0],
            task_id=row[1],
            checkpoint_name=row[2],
            checkpoint_data=json.loads(row[3]),
            timestamp=datetime.fromisoformat(row[4]),
            sequence_number=row[5]
        )

    async def restore_from_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Restore workflow state from checkpoint"""
        checkpoint = await self.get_checkpoint(checkpoint_id)

        if not checkpoint:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        return checkpoint.checkpoint_data

    async def log_event(self, task_id: str, event_type: str, event_data: Dict[str, Any]):
        """Log workflow event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        log_id = f"{task_id}_{event_type}_{int(time.time())}"

        cursor.execute("""
            INSERT INTO execution_log
            (log_id, task_id, event_type, event_data, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            log_id,
            task_id,
            event_type,
            json.dumps(event_data),
            datetime.utcnow().isoformat()
        ))

        conn.commit()
        conn.close()
```

### 6.2 Recovery System

```python
# src/agents/state/recovery.py

class RecoverySystem:
    """
    Handles workflow recovery from failures

    Strategies:
    - Checkpoint-based recovery
    - Partial re-execution
    - State reconciliation
    """

    def __init__(self, state_manager: StateManager, agent_manager: AgentManager):
        self.state_manager = state_manager
        self.agent_manager = agent_manager

    async def recover_workflow(self, task_id: str) -> TaskResult:
        """
        Recover failed workflow from last checkpoint

        1. Load latest checkpoint
        2. Recreate agent with restored state
        3. Resume from checkpoint
        """

        # Get latest checkpoint
        checkpoint = await self.state_manager.get_latest_checkpoint(task_id)

        if not checkpoint:
            raise ValueError(f"No checkpoints found for task {task_id}")

        # Restore state
        restored_data = checkpoint.checkpoint_data

        # Recreate agent
        agent = self.agent_manager.create_agent(
            agent_type=restored_data['agent_type'],
            config=restored_data['agent_config']
        )

        # Resume execution from checkpoint
        remaining_steps = restored_data['plan'][checkpoint.sequence_number:]

        # Execute remaining steps
        # (Implementation details)

        return result
```

---

## 7. Safety and Approval System

### 7.1 Safety Controller

```python
# src/agents/safety/controller.py

from typing import Dict, Any, List
from enum import Enum


class ApprovalRequirement(Enum):
    """Approval requirement levels"""
    NONE = "none"
    OPTIONAL = "optional"
    REQUIRED = "required"
    MULTI_PARTY = "multi_party"  # Requires multiple approvals


class SafetyController:
    """
    Central safety validation and approval system

    Responsibilities:
    - Risk assessment
    - Approval requirement determination
    - Safety constraint enforcement
    - Audit logging
    """

    def __init__(self, risk_analyzer):
        self.risk_analyzer = risk_analyzer
        self.approval_history: List[Dict[str, Any]] = []

    def validate_step(self, step: Dict[str, Any],
                     agent_config: AgentConfig) -> Dict[str, Any]:
        """
        Validate step safety

        Returns:
            {
                'safe': bool,
                'risk_level': str,
                'requires_approval': bool,
                'approval_requirement': ApprovalRequirement,
                'risks': List[str],
                'mitigations': List[str]
            }
        """

        tool_name = step['tool']
        tool_params = step['params']

        # Get tool definition
        tool = step.get('tool_definition')

        # Base validation
        validation = {
            'safe': True,
            'risk_level': tool.risk_level.value,
            'requires_approval': tool.requires_approval,
            'approval_requirement': ApprovalRequirement.NONE,
            'risks': [],
            'mitigations': []
        }

        # Check safety level compatibility
        if agent_config.safety_level == 'strict':
            if tool.risk_level in [ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL]:
                validation['requires_approval'] = True
                validation['approval_requirement'] = ApprovalRequirement.REQUIRED

        elif agent_config.safety_level == 'moderate':
            if tool.risk_level == ToolRiskLevel.CRITICAL:
                validation['requires_approval'] = True
                validation['approval_requirement'] = ApprovalRequirement.REQUIRED

        # Special validations for database operations
        if tool.category == ToolCategory.DATABASE_WRITE:
            validation['risks'].append("Data modification operation")
            validation['mitigations'].append("Backup created before execution")

        if tool.category == ToolCategory.DATABASE_DDL:
            validation['risks'].append("Schema modification operation")
            validation['mitigations'].append("Rollback script generated")
            validation['approval_requirement'] = ApprovalRequirement.REQUIRED

        # Check for destructive operations
        if self._is_destructive_operation(step):
            validation['requires_approval'] = True
            validation['approval_requirement'] = ApprovalRequirement.MULTI_PARTY
            validation['risks'].append("Potentially irreversible operation")

        return validation

    def _is_destructive_operation(self, step: Dict[str, Any]) -> bool:
        """Check if operation is potentially destructive"""
        destructive_tools = [
            'execute_migration',
            'drop_table',
            'truncate_table',
            'delete_backup',
            'restore_backup'
        ]

        return step['tool'] in destructive_tools

    async def request_approval(self, step: Dict[str, Any],
                              validation: Dict[str, Any],
                              approval_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Request approval for risky step

        Returns:
            {
                'approved': bool,
                'reason': str,
                'approver': str,
                'timestamp': str,
                'conditions': List[str]
            }
        """

        approval_request = {
            'step': step,
            'validation': validation,
            'timestamp': datetime.utcnow().isoformat()
        }

        if approval_callback:
            approval = await approval_callback(approval_request)
        else:
            # Interactive approval
            approval = await self._interactive_approval(approval_request)

        # Log approval
        self.approval_history.append({
            'request': approval_request,
            'approval': approval
        })

        return approval

    async def _interactive_approval(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Interactive CLI approval prompt"""

        print("\n" + "="*60)
        print("APPROVAL REQUIRED")
        print("="*60)
        print(f"\nTool: {request['step']['tool']}")
        print(f"Risk Level: {request['validation']['risk_level']}")
        print(f"\nParameters:")
        for key, value in request['step']['params'].items():
            print(f"  {key}: {value}")

        if request['validation']['risks']:
            print(f"\nRisks:")
            for risk in request['validation']['risks']:
                print(f"  - {risk}")

        if request['validation']['mitigations']:
            print(f"\nMitigations:")
            for mitigation in request['validation']['mitigations']:
                print(f"  - {mitigation}")

        print("\n" + "="*60)

        response = input("Approve this operation? (yes/no): ").strip().lower()

        if response in ['yes', 'y']:
            return {
                'approved': True,
                'reason': 'User approved',
                'approver': 'user',
                'timestamp': datetime.utcnow().isoformat(),
                'conditions': []
            }
        else:
            reason = input("Rejection reason: ").strip()
            return {
                'approved': False,
                'reason': reason or 'User rejected',
                'approver': 'user',
                'timestamp': datetime.utcnow().isoformat(),
                'conditions': []
            }
```

### 7.2 Safety Constraints

```python
# src/agents/safety/constraints.py

class SafetyConstraint(ABC):
    """Base class for safety constraints"""

    @abstractmethod
    def validate(self, step: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Validate step against constraint"""
        pass

    @abstractmethod
    def get_violation_message(self) -> str:
        """Get message for constraint violation"""
        pass


class MaxTableSizeConstraint(SafetyConstraint):
    """Prevent operations on tables exceeding size limit"""

    def __init__(self, max_rows: int = 1000000):
        self.max_rows = max_rows

    def validate(self, step: Dict[str, Any], context: Dict[str, Any]) -> bool:
        if step['tool'] in ['execute_migration', 'create_index']:
            table = step['params'].get('table')
            if table:
                row_count = context.get('table_sizes', {}).get(table, 0)
                return row_count <= self.max_rows
        return True

    def get_violation_message(self) -> str:
        return f"Table exceeds maximum size of {self.max_rows} rows"


class ProductionHoursConstraint(SafetyConstraint):
    """Prevent risky operations during production hours"""

    def __init__(self, allowed_hours: List[int] = list(range(0, 6))):
        self.allowed_hours = allowed_hours

    def validate(self, step: Dict[str, Any], context: Dict[str, Any]) -> bool:
        if step.get('tool_definition').risk_level == ToolRiskLevel.CRITICAL:
            current_hour = datetime.now().hour
            return current_hour in self.allowed_hours
        return True

    def get_violation_message(self) -> str:
        return f"Critical operations only allowed during hours: {self.allowed_hours}"
```

---

## 8. Integration Architecture

### 8.1 Integration with Existing Modules

```python
# src/agents/integration/database.py

class DatabaseIntegration:
    """
    Integration layer between agents and database module

    Provides:
    - Connection pooling
    - Transaction management
    - Risk analysis integration
    - Query execution
    """

    def __init__(self, database_module, risk_analyzer):
        self.database_module = database_module
        self.risk_analyzer = risk_analyzer

    async def execute_query(self, query: str,
                           params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute query through database module with risk analysis"""

        # Analyze risk
        risk_analysis = self.risk_analyzer.analyze(query)

        # Execute through database module
        result = self.database_module.execute_sql(
            sql=query,
            params=params,
            skip_confirmation=True  # Agent handles approval
        )

        return {
            'result': result,
            'risk_analysis': risk_analysis
        }

    async def get_schema_info(self, database: str) -> Dict[str, Any]:
        """Get database schema information"""
        # Implementation using database module
        pass
```

### 8.2 LLM Integration

```python
# src/agents/integration/llm.py

class LLMIntegration:
    """
    Integration layer for LLM-powered agent reasoning

    Provides:
    - Task planning
    - Tool selection
    - Parameter generation
    - Result interpretation
    """

    def __init__(self, llm_manager):
        self.llm_manager = llm_manager

    async def plan_task(self, task_description: str,
                       available_tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """Use LLM to plan task execution"""

        tools_description = self._format_tools_for_llm(available_tools)

        prompt = f"""
You are an AI agent planning database operations. Create a step-by-step plan.

Task: {task_description}

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

Important:
- Use only the listed tools
- Each step should have clear parameters
- Explain the rationale for each step
- Consider safety and dependencies
"""

        response = await self.llm_manager.generate(prompt, max_tokens=1000)

        plan = json.loads(response)

        return plan

    def _format_tools_for_llm(self, tools: List[ToolDefinition]) -> str:
        """Format tool definitions for LLM prompt"""
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

---

## 9. Deployment Architecture

### 9.1 File Structure

```
src/agents/
├── __init__.py
├── base.py                      # BaseAgent class
├── manager.py                   # AgentManager
├── orchestrator.py              # WorkflowOrchestrator
│
├── database/
│   ├── __init__.py
│   ├── backup.py                # BackupAgent
│   ├── migration.py             # MigrationAgent
│   └── optimizer.py             # OptimizerAgent
│
├── coordinator.py               # CoordinatorAgent
│
├── tools/
│   ├── __init__.py
│   ├── registry.py              # ToolRegistry
│   ├── database_tools.py        # Database tool implementations
│   ├── backup_tools.py          # Backup tool implementations
│   ├── migration_tools.py       # Migration tool implementations
│   └── optimizer_tools.py       # Optimizer tool implementations
│
├── state/
│   ├── __init__.py
│   ├── manager.py               # StateManager
│   └── recovery.py              # RecoverySystem
│
├── safety/
│   ├── __init__.py
│   ├── controller.py            # SafetyController
│   └── constraints.py           # Safety constraints
│
└── integration/
    ├── __init__.py
    ├── database.py              # Database integration
    └── llm.py                   # LLM integration
```

### 9.2 Configuration

```yaml
# config/agents.yaml

agents:
  backup:
    safety_level: moderate
    max_execution_time: 3600
    capabilities:
      - database_read
      - backup_create
      - backup_restore
      - file_write

    default_config:
      compression: true
      verify_backup: true
      retention_days: 30

  migration:
    safety_level: strict
    max_execution_time: 1800
    capabilities:
      - database_read
      - database_write
      - database_ddl
      - schema_analyze
      - schema_modify

    default_config:
      create_backup: true
      generate_rollback: true
      dry_run_first: true

  optimizer:
    safety_level: moderate
    max_execution_time: 600
    capabilities:
      - database_read
      - query_optimize
      - index_manage
      - schema_analyze

    default_config:
      analyze_only: false
      auto_apply_indexes: false
      threshold_improvement: 0.2

safety:
  constraints:
    - type: max_table_size
      max_rows: 1000000

    - type: production_hours
      allowed_hours: [0, 1, 2, 3, 4, 5]

    - type: backup_required
      before_operations:
        - execute_migration
        - drop_table

  approval_requirements:
    critical_operations: required
    production_database: required
    large_tables: required

llm:
  provider: ollama
  model: llama2
  temperature: 0.3
  max_tokens: 1000
```

---

## 10. Usage Examples

### 10.1 Automated Backup

```python
# Example: Create automated backup workflow

from src.agents.orchestrator import WorkflowOrchestrator, WorkflowConfig

orchestrator = WorkflowOrchestrator(agent_manager, state_manager, approval_system)

backup_config = WorkflowConfig(
    workflow_id="backup_prod_001",
    workflow_name="Production Database Backup",
    description="Create full backup of production database",
    agent_type="backup",
    input_data={
        'backup_type': 'full',
        'destination': '/backups/prod',
        'compression': True,
        'verify': True,
        'cleanup_old': True,
        'retention_days': 30
    },
    database_config={
        'database': 'production',
        'host': 'localhost',
        'port': 5432
    }
)

result = await orchestrator.execute_workflow(backup_config)

print(f"Backup Status: {result.status}")
print(f"Backup Path: {result.output_data['backup_path']}")
print(f"Actions Taken: {len(result.actions_taken)}")
```

### 10.2 Schema Migration

```python
# Example: Execute schema migration with safety checks

migration_config = WorkflowConfig(
    workflow_id="migration_001",
    workflow_name="Add User Phone Column",
    description="Add phone column to users table",
    agent_type="migration",
    input_data={
        'migration_type': 'add_column',
        'target_schema': {
            'table': 'users',
            'column': 'phone',
            'type': 'VARCHAR(20)',
            'nullable': True
        }
    },
    database_config={
        'database': 'production',
        'host': 'localhost'
    },
    approval_callback=custom_approval_handler
)

result = await orchestrator.execute_workflow(migration_config)

if result.status == 'success':
    print("Migration completed successfully")
    print(f"Rollback script: {result.output_data['rollback_path']}")
else:
    print(f"Migration failed: {result.error}")
```

### 10.3 Query Optimization

```python
# Example: Optimize slow query

optimizer_config = WorkflowConfig(
    workflow_id="optimize_001",
    workflow_name="Optimize User Search Query",
    description="Optimize slow user search query",
    agent_type="optimizer",
    input_data={
        'target': 'query',
        'query': '''
            SELECT u.*, COUNT(o.id) as order_count
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            WHERE u.created_at > '2024-01-01'
            GROUP BY u.id
        ''',
        'apply_recommendations': False  # Analyze only
    },
    database_config={
        'database': 'production'
    }
)

result = await orchestrator.execute_workflow(optimizer_config)

print("Optimization Recommendations:")
for rec in result.output_data['recommendations']:
    print(f"- {rec['type']}: {rec['description']}")
    print(f"  Estimated improvement: {rec['estimated_improvement']}")
```

### 10.4 Multi-Agent Workflow

```python
# Example: Complex workflow with multiple agents

coordinator_task = TaskContext(
    task_id="complex_workflow_001",
    task_description="""
    Prepare production database for new feature deployment:
    1. Create backup
    2. Apply schema migration
    3. Optimize related queries
    4. Verify data integrity
    """,
    input_data={
        'feature': 'user_notifications',
        'migration_scripts': [...],
        'affected_queries': [...]
    },
    database_config={
        'database': 'production'
    }
)

result = await orchestrator.execute_multi_agent_workflow(coordinator_task)

print(f"Workflow completed with {len(result.actions_taken)} steps")
```

---

## 11. Architecture Decision Records

### ADR-001: Agent-Based Architecture

**Status**: Accepted

**Context**: Need autonomous multi-step workflows for database operations

**Decision**: Implement agent-based architecture with tool registry and LLM planning

**Consequences**:
- (+) Flexible and extensible
- (+) Autonomous with oversight
- (+) Composable workflows
- (-) Complexity in coordination
- (-) LLM dependency

### ADR-002: Tool Registry Pattern

**Status**: Accepted

**Context**: Need safe, validated execution without arbitrary code

**Decision**: Use tool registry with predefined, validated tools

**Consequences**:
- (+) Safe execution
- (+) Clear capabilities
- (+) Easy to audit
- (-) Less flexible than code execution
- (-) Requires tool implementation for each operation

### ADR-003: Checkpoint-Based Recovery

**Status**: Accepted

**Context**: Long-running workflows need recovery capability

**Decision**: Implement checkpoint system with state persistence

**Consequences**:
- (+) Recovery from failures
- (+) Audit trail
- (+) Debugging capability
- (-) Storage overhead
- (-) Complexity in state management

### ADR-004: Multi-Layer Safety

**Status**: Accepted

**Context**: Database operations require safety guarantees

**Decision**: Implement multi-layer safety with approval system

**Consequences**:
- (+) Prevents destructive operations
- (+) User oversight for critical operations
- (+) Configurable safety levels
- (-) User interruption for approvals
- (-) May slow down workflows

### ADR-005: LLM-Powered Planning

**Status**: Accepted

**Context**: Need intelligent task decomposition and planning

**Decision**: Use LLM for task planning and tool selection

**Consequences**:
- (+) Intelligent planning
- (+) Natural language understanding
- (+) Adaptive to new scenarios
- (-) LLM inference cost
- (-) Non-deterministic planning
- (-) Requires prompt engineering

---

## 12. Performance Considerations

### 12.1 Optimization Strategies

1. **Tool Caching**: Cache tool definitions and schemas
2. **Parallel Execution**: Execute independent steps in parallel
3. **Lazy Loading**: Load tools only when needed
4. **Connection Pooling**: Reuse database connections
5. **Checkpoint Batching**: Batch checkpoint writes

### 12.2 Scalability

- Support for distributed execution (future)
- Async/await for concurrent operations
- Resource limits per agent
- Timeout management

---

## 13. Security Considerations

### 13.1 Security Measures

1. **Input Validation**: Validate all tool parameters
2. **SQL Injection Prevention**: Use parameterized queries
3. **Access Control**: Tool-level permissions
4. **Audit Logging**: Log all operations
5. **Secrets Management**: Secure credential storage

### 13.2 Threat Model

- Malicious prompts leading to destructive operations
- SQL injection through LLM-generated queries
- Unauthorized access to sensitive data
- Resource exhaustion attacks

### 13.3 Mitigations

- Approval requirements for critical operations
- Tool whitelist per agent type
- Rate limiting
- Resource quotas
- Automated rollback on errors

---

## 14. Testing Strategy

### 14.1 Unit Tests

- Agent planning logic
- Tool implementations
- Safety validations
- State management

### 14.2 Integration Tests

- End-to-end workflows
- Database integration
- LLM integration
- Recovery scenarios

### 14.3 Safety Tests

- Approval system
- Constraint validation
- Error handling
- Rollback mechanisms

---

## 15. Future Enhancements

### 15.1 Phase 13+ Features

1. **Learning System**: Learn from successful workflows
2. **Natural Language Interface**: Chat-based workflow execution
3. **Distributed Execution**: Multi-node agent coordination
4. **Advanced Monitoring**: Real-time metrics and alerting
5. **Agent Marketplace**: Community-contributed agents
6. **Visual Workflow Builder**: GUI for workflow creation
7. **Integration Hub**: Connect with external systems

### 15.2 Research Directions

- Reinforcement learning for optimization
- Multi-agent collaboration patterns
- Formal verification of workflows
- Predictive failure detection

---

## 16. Conclusion

This architecture provides a robust foundation for Phase 12: Agentic AI Workflows in AIShell. The design prioritizes:

1. **Safety**: Multi-layer safety mechanisms with approval workflows
2. **Autonomy**: AI-powered planning and execution
3. **Reliability**: Checkpoint-based recovery and state management
4. **Extensibility**: Tool registry and agent framework for easy extension
5. **Integration**: Seamless integration with existing AIShell modules

The system enables sophisticated database operations through autonomous agents while maintaining strict safety controls and user oversight.

---

## Appendix A: API Reference

### Agent API

```python
# Create agent
agent = agent_manager.create_agent("backup", config)

# Execute workflow
result = await orchestrator.execute_workflow(workflow_config)

# Check status
status = orchestrator.get_workflow_status(workflow_id)

# Pause/Resume
await orchestrator.pause_workflow(workflow_id)
await orchestrator.resume_workflow(workflow_id)
```

### Tool API

```python
# Register tool
registry.register_tool(tool_definition)

# Get tool
tool = registry.get_tool("backup_database_full")

# Find tools
tools = registry.find_tools(category=ToolCategory.BACKUP)

# Execute tool
result = await tool.execute(params, context)
```

### State API

```python
# Save checkpoint
checkpoint_id = await state_manager.save_checkpoint(task_id, name, data)

# Get checkpoint
checkpoint = await state_manager.get_checkpoint(checkpoint_id)

# Restore
data = await state_manager.restore_from_checkpoint(checkpoint_id)

# Log event
await state_manager.log_event(task_id, event_type, event_data)
```

---

## Appendix B: Configuration Examples

See section 9.2 for complete configuration examples.

---

**End of Architecture Document**
