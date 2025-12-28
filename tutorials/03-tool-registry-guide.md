# Tool Registry System - Comprehensive Hands-On Tutorial

## Table of Contents

1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [Quick Start](#quick-start)
4. [Creating Tools](#creating-tools)
5. [Parameter Validation](#parameter-validation)
6. [Risk Levels](#risk-levels)
7. [Tool Categories](#tool-categories)
8. [Capabilities](#capabilities)
9. [LLM Integration](#llm-integration)
10. [Rate Limiting](#rate-limiting)
11. [Execution Logging](#execution-logging)
12. [Complete Example](#complete-example)
13. [Best Practices](#best-practices)

---

## Introduction

### What is the Tool Registry System?

The Tool Registry System is the central infrastructure for managing, validating, and executing agent tools in the AIShell agentic workflow system. It provides:

- **Centralized tool management** - Register, discover, and execute tools
- **Safety validation** - Parameter and return value validation using JSON schemas
- **Risk assessment** - Five-level risk classification system
- **Capability matching** - Ensure agents have required capabilities before execution
- **LLM integration** - Generate LLM-friendly tool descriptions
- **Audit trails** - Complete execution logging for debugging and compliance
- **Rate limiting** - Prevent resource exhaustion

### Why Does It Matter?

In agentic AI workflows, tools are how agents interact with external systems. The Tool Registry ensures:

1. **Safety** - Invalid parameters are caught before execution
2. **Security** - High-risk operations can require approval
3. **Reliability** - Consistent tool interfaces across all agents
4. **Observability** - Complete audit trail of all tool executions
5. **Scalability** - Rate limiting prevents resource exhaustion

---

## Core Concepts

### Tool Definition

A `ToolDefinition` is a complete specification of a tool including:

```python
from src.agents.tools import ToolDefinition, ToolCategory, ToolRiskLevel

tool = ToolDefinition(
    # Identity
    name="backup_database_full",
    description="Create full database backup",

    # Classification
    category=ToolCategory.BACKUP,
    risk_level=ToolRiskLevel.LOW,

    # Requirements
    required_capabilities=["database_read", "backup_create"],

    # Validation schemas
    parameters_schema={...},      # JSON Schema for inputs
    returns_schema={...},          # JSON Schema for outputs

    # Execution
    implementation=backup_func,    # Async callable

    # Safety constraints
    requires_approval=False,
    max_execution_time=3600,      # seconds
    rate_limit=10,                # calls per minute

    # Documentation
    examples=[{...}]
)
```

### Tool Categories

Six built-in categories for organizing tools:

```python
class ToolCategory(Enum):
    DATABASE_READ = "database_read"      # Read operations
    DATABASE_WRITE = "database_write"    # Data modifications
    DATABASE_DDL = "database_ddl"        # Schema changes
    FILE_SYSTEM = "file_system"          # File operations
    BACKUP = "backup"                    # Backup/restore
    ANALYSIS = "analysis"                # Analysis/reporting
```

### Risk Levels

Five-level risk classification:

```python
class ToolRiskLevel(Enum):
    SAFE = "safe"            # Read-only, no side effects
    LOW = "low"              # Minor modifications
    MEDIUM = "medium"        # Significant modifications
    HIGH = "high"            # Potentially destructive
    CRITICAL = "critical"    # Irreversible operations
```

### Tool Registry

The central registry that manages all tools:

```python
from src.agents.tools import ToolRegistry

registry = ToolRegistry()

# Register tools
registry.register_tool(tool)

# Find tools
tools = registry.find_tools(category=ToolCategory.BACKUP)

# Execute tools
result = await tool.execute(params, context)

# Get statistics
stats = registry.get_registry_stats()
```

---

## Quick Start

### 1. Create Your First Tool

```python
import asyncio
from typing import Dict, Any
from src.agents.tools import (
    ToolDefinition,
    ToolCategory,
    ToolRiskLevel,
    ToolRegistry
)

# Define the tool implementation
async def hello_world(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Simple hello world tool"""
    name = params.get('name', 'World')
    return {
        'message': f'Hello, {name}!',
        'status': 'success'
    }

# Create the tool definition
hello_tool = ToolDefinition(
    name="hello_world",
    description="Greet someone by name",
    category=ToolCategory.ANALYSIS,
    risk_level=ToolRiskLevel.SAFE,
    required_capabilities=[],
    parameters_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name to greet"
            }
        },
        "required": []
    },
    returns_schema={
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "status": {"type": "string"}
        },
        "required": ["message", "status"]
    },
    implementation=hello_world,
    requires_approval=False,
    max_execution_time=5
)

# Register and use the tool
async def main():
    registry = ToolRegistry()
    registry.register_tool(hello_tool)

    # Execute the tool
    result = await hello_tool.execute(
        params={"name": "AIShell"},
        context={}
    )

    print(result)  # {'message': 'Hello, AIShell!', 'status': 'success'}

asyncio.run(main())
```

### 2. List Available Tools

```python
# Get all registered tools
tool_names = registry.list_tools()
print(f"Available tools: {tool_names}")

# Get specific tool
tool = registry.get_tool("hello_world")
if tool:
    print(f"Found tool: {tool.name}")
    print(f"Description: {tool.description}")
    print(f"Risk level: {tool.risk_level.value}")
```

### 3. Get Tool Statistics

```python
stats = registry.get_registry_stats()
print(f"Total tools: {stats['total_tools']}")
print(f"By category: {stats['tools_by_category']}")
print(f"By risk level: {stats['tools_by_risk_level']}")
print(f"Total executions: {stats['total_executions']}")
print(f"Success rate: {stats['successful_executions']}/{stats['total_executions']}")
```

---

## Creating Tools

### Step-by-Step Tool Creation

#### Step 1: Define the Implementation

```python
async def calculate_statistics(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate statistics for a dataset

    Args:
        params: Tool parameters (numbers: list of numbers)
        context: Execution context (optional database_module, llm_manager, etc.)

    Returns:
        Dict with mean, median, mode, std_dev

    Raises:
        ValueError: If numbers list is empty
    """
    numbers = params.get('numbers', [])

    if not numbers:
        raise ValueError("Cannot calculate statistics for empty dataset")

    import statistics

    return {
        'count': len(numbers),
        'mean': statistics.mean(numbers),
        'median': statistics.median(numbers),
        'std_dev': statistics.stdev(numbers) if len(numbers) > 1 else 0.0,
        'min': min(numbers),
        'max': max(numbers)
    }
```

#### Step 2: Define JSON Schemas

```python
# Input validation schema
parameters_schema = {
    "type": "object",
    "properties": {
        "numbers": {
            "type": "array",
            "items": {"type": "number"},
            "description": "List of numbers to analyze",
            "minItems": 1
        }
    },
    "required": ["numbers"]
}

# Output validation schema
returns_schema = {
    "type": "object",
    "properties": {
        "count": {"type": "integer", "minimum": 1},
        "mean": {"type": "number"},
        "median": {"type": "number"},
        "std_dev": {"type": "number", "minimum": 0},
        "min": {"type": "number"},
        "max": {"type": "number"}
    },
    "required": ["count", "mean", "median", "std_dev", "min", "max"]
}
```

#### Step 3: Create the ToolDefinition

```python
stats_tool = ToolDefinition(
    name="calculate_statistics",
    description="Calculate descriptive statistics (mean, median, std dev) for a dataset",
    category=ToolCategory.ANALYSIS,
    risk_level=ToolRiskLevel.SAFE,
    required_capabilities=["math"],
    parameters_schema=parameters_schema,
    returns_schema=returns_schema,
    implementation=calculate_statistics,
    requires_approval=False,
    max_execution_time=10,
    rate_limit=100,  # 100 calls per minute
    examples=[
        {
            "description": "Calculate statistics for sample data",
            "params": {
                "numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            },
            "expected_output": {
                "count": 10,
                "mean": 5.5,
                "median": 5.5,
                "std_dev": 3.03,
                "min": 1,
                "max": 10
            }
        }
    ]
)
```

#### Step 4: Register and Test

```python
async def test_stats_tool():
    registry = ToolRegistry()
    registry.register_tool(stats_tool)

    # Test with valid data
    result = await stats_tool.execute(
        params={"numbers": [10, 20, 30, 40, 50]},
        context={}
    )
    print(f"Statistics: {result}")

    # Test validation - this will raise ValueError
    try:
        await stats_tool.execute(params={"numbers": []}, context={})
    except ValueError as e:
        print(f"Validation caught: {e}")

asyncio.run(test_stats_tool())
```

---

## Parameter Validation

### Understanding JSON Schema Validation

The Tool Registry uses JSON Schema to validate both inputs and outputs. This ensures type safety and prevents runtime errors.

### Common Validation Patterns

#### Required Fields

```python
parameters_schema = {
    "type": "object",
    "properties": {
        "database": {"type": "string"},
        "table": {"type": "string"}
    },
    "required": ["database", "table"]  # Both required
}
```

#### Optional Fields with Defaults

```python
parameters_schema = {
    "type": "object",
    "properties": {
        "database": {"type": "string"},
        "compression": {
            "type": "boolean",
            "default": True,
            "description": "Enable compression"
        }
    },
    "required": ["database"]  # Only database required
}
```

#### Enumerations

```python
parameters_schema = {
    "type": "object",
    "properties": {
        "backup_type": {
            "type": "string",
            "enum": ["full", "incremental", "differential"],
            "description": "Type of backup to create"
        }
    },
    "required": ["backup_type"]
}
```

#### String Constraints

```python
parameters_schema = {
    "type": "object",
    "properties": {
        "email": {
            "type": "string",
            "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
            "description": "Valid email address"
        },
        "username": {
            "type": "string",
            "minLength": 3,
            "maxLength": 20,
            "pattern": "^[a-zA-Z0-9_]+$"
        }
    }
}
```

#### Number Constraints

```python
parameters_schema = {
    "type": "object",
    "properties": {
        "port": {
            "type": "integer",
            "minimum": 1024,
            "maximum": 65535
        },
        "percentage": {
            "type": "number",
            "minimum": 0,
            "maximum": 100
        },
        "temperature": {
            "type": "number",
            "multipleOf": 0.1  # Must be multiple of 0.1
        }
    }
}
```

#### Array Constraints

```python
parameters_schema = {
    "type": "object",
    "properties": {
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 10,
            "uniqueItems": True
        },
        "coordinates": {
            "type": "array",
            "items": {"type": "number"},
            "minItems": 2,
            "maxItems": 2  # Exactly 2 items
        }
    }
}
```

#### Nested Objects

```python
parameters_schema = {
    "type": "object",
    "properties": {
        "connection": {
            "type": "object",
            "properties": {
                "host": {"type": "string"},
                "port": {"type": "integer"},
                "ssl": {"type": "boolean"}
            },
            "required": ["host", "port"]
        }
    },
    "required": ["connection"]
}
```

### Manual Validation

You can manually validate parameters before execution:

```python
# Validate parameters
is_valid, error_msg = tool.validate_parameters(params)
if not is_valid:
    print(f"Validation failed: {error_msg}")
else:
    result = await tool.execute(params, context)
```

### Error Handling

```python
async def safe_tool_execution():
    try:
        result = await tool.execute(params, context)
        print(f"Success: {result}")
    except ValueError as e:
        # Parameter validation failed
        print(f"Invalid parameters: {e}")
    except RuntimeError as e:
        # Tool execution or return validation failed
        print(f"Execution error: {e}")
    except Exception as e:
        # Unexpected error
        print(f"Unexpected error: {e}")
```

---

## Risk Levels

### Understanding Risk Levels

Risk levels determine approval requirements and execution constraints.

### SAFE - Read-Only Operations

```python
# Example: Query database
async def query_table(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Read-only query, no side effects"""
    return {"rows": [...], "count": 100}

query_tool = ToolDefinition(
    name="query_table",
    description="Query table with SELECT",
    category=ToolCategory.DATABASE_READ,
    risk_level=ToolRiskLevel.SAFE,  # Read-only
    required_capabilities=["database_read"],
    # ... schemas ...
    implementation=query_table,
    requires_approval=False,  # No approval needed
    max_execution_time=30
)
```

**Characteristics:**
- No data modifications
- No system changes
- No external side effects
- Never requires approval

### LOW - Minor Modifications

```python
# Example: Insert single record
async def insert_record(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a single record"""
    return {"inserted_id": 123, "success": True}

insert_tool = ToolDefinition(
    name="insert_record",
    description="Insert single record into table",
    category=ToolCategory.DATABASE_WRITE,
    risk_level=ToolRiskLevel.LOW,  # Minor modification
    required_capabilities=["database_write"],
    # ... schemas ...
    implementation=insert_record,
    requires_approval=False,  # Usually no approval
    max_execution_time=10
)
```

**Characteristics:**
- Single record modifications
- Easily reversible
- Limited scope
- Usually no approval required

### MEDIUM - Significant Modifications

```python
# Example: Bulk update
async def bulk_update(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Update multiple records"""
    return {"updated_count": 500, "success": True}

bulk_tool = ToolDefinition(
    name="bulk_update",
    description="Update multiple records in table",
    category=ToolCategory.DATABASE_WRITE,
    risk_level=ToolRiskLevel.MEDIUM,  # Significant changes
    required_capabilities=["database_write", "bulk_operations"],
    # ... schemas ...
    implementation=bulk_update,
    requires_approval=True,  # Approval recommended
    max_execution_time=300
)
```

**Characteristics:**
- Multiple record changes
- Reversible with effort
- Significant impact
- Approval recommended

### HIGH - Potentially Destructive

```python
# Example: Delete with cascades
async def delete_cascade(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Delete records with cascading deletes"""
    return {"deleted_count": 1000, "cascaded_count": 500}

delete_tool = ToolDefinition(
    name="delete_cascade",
    description="Delete records with cascade",
    category=ToolCategory.DATABASE_WRITE,
    risk_level=ToolRiskLevel.HIGH,  # Potentially destructive
    required_capabilities=["database_write", "delete_cascade"],
    # ... schemas ...
    implementation=delete_cascade,
    requires_approval=True,  # Approval required
    max_execution_time=600
)
```

**Characteristics:**
- Large-scale deletions
- Cascading effects
- Difficult to reverse
- Approval required

### CRITICAL - Irreversible Operations

```python
# Example: Drop table
async def drop_table(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Drop table permanently"""
    return {"dropped": True, "table": params['table']}

drop_tool = ToolDefinition(
    name="drop_table",
    description="Permanently drop database table",
    category=ToolCategory.DATABASE_DDL,
    risk_level=ToolRiskLevel.CRITICAL,  # Irreversible
    required_capabilities=["database_ddl", "drop_operations"],
    # ... schemas ...
    implementation=drop_table,
    requires_approval=True,  # Mandatory approval
    max_execution_time=60,
    rate_limit=5  # Very limited
)
```

**Characteristics:**
- Irreversible operations
- Schema modifications
- System-wide impact
- Mandatory approval
- Very low rate limits

### Filtering by Risk Level

```python
# Get only safe tools
safe_tools = registry.find_tools(max_risk=ToolRiskLevel.SAFE)

# Get safe and low risk tools
low_risk_tools = registry.find_tools(max_risk=ToolRiskLevel.LOW)

# Get all except critical
non_critical = registry.find_tools(max_risk=ToolRiskLevel.HIGH)
```

---

## Tool Categories

### When to Use Each Category

#### DATABASE_READ

**Use for:**
- SELECT queries
- View definitions
- Schema inspection
- Statistics gathering

```python
async def get_table_info(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Get table metadata"""
    return {
        "table": params['table'],
        "row_count": 10000,
        "columns": ["id", "name", "email"]
    }

ToolDefinition(
    name="get_table_info",
    category=ToolCategory.DATABASE_READ,
    risk_level=ToolRiskLevel.SAFE,
    # ...
)
```

#### DATABASE_WRITE

**Use for:**
- INSERT operations
- UPDATE operations
- DELETE operations
- Data modifications

```python
async def update_user(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Update user record"""
    return {
        "updated_id": params['user_id'],
        "fields_updated": ["email", "last_login"]
    }

ToolDefinition(
    name="update_user",
    category=ToolCategory.DATABASE_WRITE,
    risk_level=ToolRiskLevel.LOW,
    # ...
)
```

#### DATABASE_DDL

**Use for:**
- CREATE TABLE
- ALTER TABLE
- DROP TABLE
- INDEX creation
- Schema migrations

```python
async def create_index(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Create database index"""
    return {
        "index_name": params['index_name'],
        "table": params['table'],
        "created": True
    }

ToolDefinition(
    name="create_index",
    category=ToolCategory.DATABASE_DDL,
    risk_level=ToolRiskLevel.MEDIUM,
    # ...
)
```

#### FILE_SYSTEM

**Use for:**
- File reading/writing
- Directory operations
- File uploads/downloads

```python
async def read_config(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Read configuration file"""
    import json
    with open(params['path'], 'r') as f:
        config = json.load(f)
    return {"config": config}

ToolDefinition(
    name="read_config",
    category=ToolCategory.FILE_SYSTEM,
    risk_level=ToolRiskLevel.SAFE,
    # ...
)
```

#### BACKUP

**Use for:**
- Database backups
- File backups
- Backup validation
- Restore operations

```python
async def create_backup(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Create database backup"""
    return {
        "backup_path": "/backups/db_20250105.sql.gz",
        "size_bytes": 1024000,
        "checksum": "abc123..."
    }

ToolDefinition(
    name="create_backup",
    category=ToolCategory.BACKUP,
    risk_level=ToolRiskLevel.LOW,
    # ...
)
```

#### ANALYSIS

**Use for:**
- Data analysis
- Statistics calculation
- Report generation
- Performance analysis

```python
async def analyze_performance(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze database performance"""
    return {
        "slow_queries": [...],
        "index_usage": {...},
        "recommendations": [...]
    }

ToolDefinition(
    name="analyze_performance",
    category=ToolCategory.ANALYSIS,
    risk_level=ToolRiskLevel.SAFE,
    # ...
)
```

### Filtering by Category

```python
# Get all backup tools
backup_tools = registry.find_tools(category=ToolCategory.BACKUP)

# Get read-only database tools
read_tools = registry.find_tools(
    category=ToolCategory.DATABASE_READ,
    max_risk=ToolRiskLevel.SAFE
)

# Combine filters
safe_analysis = registry.find_tools(
    category=ToolCategory.ANALYSIS,
    max_risk=ToolRiskLevel.SAFE,
    capabilities=["database_read"]
)
```

---

## Capabilities

### What Are Capabilities?

Capabilities are permission strings that agents must possess to use specific tools. They ensure agents only execute tools they're authorized for.

### Defining Required Capabilities

```python
ToolDefinition(
    name="backup_database",
    required_capabilities=[
        "database_read",      # Must be able to read database
        "backup_create",      # Must be able to create backups
        "file_write"          # Must be able to write files
    ],
    # ...
)
```

### Common Capability Patterns

#### Single Capability

```python
# Simple read operation
required_capabilities=["database_read"]
```

#### Multiple Capabilities

```python
# Complex operation requiring multiple permissions
required_capabilities=[
    "database_read",
    "database_write",
    "transaction_control"
]
```

#### No Capabilities Required

```python
# Safe analysis tool anyone can use
required_capabilities=[]
```

### Capability Naming Conventions

Use clear, hierarchical naming:

```python
# Good capability names
"database_read"
"database_write_bulk"
"file_system_read"
"backup_create_full"
"admin_user_management"

# Avoid vague names
"access"
"permission"
"allowed"
```

### Filtering Tools by Capabilities

```python
# Agent with specific capabilities
agent_capabilities = [
    "database_read",
    "database_write",
    "backup_create"
]

# Find tools this agent can use
available_tools = registry.find_tools(capabilities=agent_capabilities)

print(f"Agent can use {len(available_tools)} tools:")
for tool in available_tools:
    print(f"  - {tool.name}: {tool.description}")
```

### Example: Agent with Limited Capabilities

```python
# Junior agent with read-only access
junior_agent_caps = ["database_read", "file_read"]

junior_tools = registry.find_tools(
    capabilities=junior_agent_caps,
    max_risk=ToolRiskLevel.SAFE
)

# Senior agent with full access
senior_agent_caps = [
    "database_read",
    "database_write",
    "database_ddl",
    "backup_create",
    "admin_operations"
]

senior_tools = registry.find_tools(
    capabilities=senior_agent_caps,
    max_risk=ToolRiskLevel.HIGH
)

print(f"Junior agent: {len(junior_tools)} tools")
print(f"Senior agent: {len(senior_tools)} tools")
```

### Capability-Based Tool Design

```python
# Design tools with appropriate capabilities
async def read_only_query(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Read-only query"""
    pass

read_tool = ToolDefinition(
    name="query_table",
    required_capabilities=["database_read"],  # Minimal capability
    risk_level=ToolRiskLevel.SAFE,
    # ...
)

async def admin_operation(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Administrative operation"""
    pass

admin_tool = ToolDefinition(
    name="reset_system",
    required_capabilities=[
        "admin_operations",     # High-level permission
        "system_modification"
    ],
    risk_level=ToolRiskLevel.CRITICAL,
    requires_approval=True,
    # ...
)
```

---

## LLM Integration

### Making Tools LLM-Friendly

The Tool Registry automatically generates LLM-friendly descriptions that can be included in prompts.

### Getting Tool Descriptions

```python
# Get description for a single tool
description = registry.get_tool_description("backup_database_full")
print(description)
```

**Output:**
```
Tool: backup_database_full
Description: Create full database backup with optional compression and validation
Category: backup
Risk Level: low
Requires Approval: False

Parameters:
{
  "type": "object",
  "properties": {
    "database": {
      "type": "string",
      "description": "Database name to backup"
    },
    "destination": {
      "type": "string",
      "description": "Backup destination path"
    },
    "compression": {
      "type": "boolean",
      "description": "Enable compression (default: true)"
    }
  },
  "required": ["database", "destination"]
}

Returns:
{
  "type": "object",
  "properties": {
    "backup_path": {"type": "string"},
    "size_bytes": {"type": "integer"},
    "duration_seconds": {"type": "number"},
    "checksum": {"type": "string"}
  }
}

Examples:
[
  {
    "description": "Create compressed full backup",
    "params": {
      "database": "production",
      "destination": "/backups/prod_backup.sql.gz"
    }
  }
]
```

### Getting All Available Tools for LLM

```python
# Get all tools available to an agent
agent_capabilities = ["database_read", "database_write", "backup_create"]

tools_for_llm = registry.get_available_tools_for_llm(
    capabilities=agent_capabilities,
    max_risk=ToolRiskLevel.MEDIUM,
    category=ToolCategory.BACKUP  # Optional category filter
)

print(tools_for_llm)
```

### Using in LLM Prompts

```python
def create_agent_prompt(task: str, agent_capabilities: list) -> str:
    """Create prompt with available tools"""

    tools_description = registry.get_available_tools_for_llm(
        capabilities=agent_capabilities,
        max_risk=ToolRiskLevel.MEDIUM
    )

    prompt = f"""
You are an AI agent tasked with: {task}

You have access to the following tools:

{tools_description}

To use a tool, respond with JSON in this format:
{{
    "tool": "tool_name",
    "parameters": {{
        "param1": "value1",
        "param2": "value2"
    }}
}}

Please analyze the task and select the appropriate tool.
"""

    return prompt

# Example usage
prompt = create_agent_prompt(
    task="Create a backup of the production database",
    agent_capabilities=["database_read", "backup_create", "file_write"]
)
```

### Adding Examples to Tools

Examples help LLMs understand how to use tools:

```python
ToolDefinition(
    name="analyze_schema",
    # ... other fields ...
    examples=[
        {
            "description": "Analyze schema with all details",
            "params": {
                "database": "production",
                "include_indexes": True,
                "include_constraints": True
            },
            "expected_output": {
                "tables": [{"name": "users", "columns": [...]}],
                "indexes": [{"name": "idx_users_email"}],
                "statistics": {"total_tables": 10}
            }
        },
        {
            "description": "Quick schema overview",
            "params": {
                "database": "staging",
                "include_indexes": False,
                "include_constraints": False
            },
            "expected_output": {
                "tables": [{"name": "products"}],
                "statistics": {"total_tables": 5}
            }
        }
    ]
)
```

### Tool Selection Logic

```python
async def llm_tool_selection(user_request: str, agent_capabilities: list) -> dict:
    """Use LLM to select appropriate tool"""

    # Get available tools
    tools_desc = registry.get_available_tools_for_llm(
        capabilities=agent_capabilities,
        max_risk=ToolRiskLevel.MEDIUM
    )

    # Create prompt
    prompt = f"""
User request: {user_request}

Available tools:
{tools_desc}

Select the best tool and parameters for this request.
Respond with JSON: {{"tool": "name", "parameters": {{...}}}}
"""

    # Get LLM response (pseudo-code)
    # llm_response = await llm_manager.complete(prompt)
    # tool_selection = json.loads(llm_response)

    # For demo, return example
    return {
        "tool": "backup_database_full",
        "parameters": {
            "database": "production",
            "destination": "/backups/prod.sql.gz",
            "compression": True
        }
    }
```

---

## Rate Limiting

### Why Rate Limiting?

Rate limiting prevents:
- Resource exhaustion
- Accidental infinite loops
- Malicious over-use
- Database overload

### Configuring Rate Limits

```python
ToolDefinition(
    name="expensive_query",
    # ... other fields ...
    rate_limit=10,  # Maximum 10 calls per minute
)
```

### How Rate Limiting Works

The registry tracks tool executions over a 60-second sliding window:

1. Each execution is timestamped
2. Before execution, old timestamps (>60s) are removed
3. If execution count >= rate_limit, the call is rejected
4. Otherwise, the call proceeds and is timestamped

### Checking Rate Limits

```python
# Check if tool is within rate limit
is_allowed, error_msg = registry.check_rate_limit("expensive_query")

if is_allowed:
    result = await tool.execute(params, context)
else:
    print(f"Rate limit exceeded: {error_msg}")
```

### Example: Rate-Limited Execution

```python
async def execute_with_rate_limit(tool_name: str, params: dict, context: dict):
    """Execute tool with rate limit check"""

    # Check rate limit
    is_allowed, error_msg = registry.check_rate_limit(tool_name)

    if not is_allowed:
        return {
            "success": False,
            "error": error_msg,
            "retry_after": 60  # seconds
        }

    # Execute tool
    tool = registry.get_tool(tool_name)
    try:
        result = await tool.execute(params, context)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

### Different Rate Limits for Different Tools

```python
# High rate limit for safe read operations
query_tool = ToolDefinition(
    name="query_table",
    risk_level=ToolRiskLevel.SAFE,
    rate_limit=1000,  # 1000 calls per minute
    # ...
)

# Low rate limit for expensive operations
backup_tool = ToolDefinition(
    name="full_backup",
    risk_level=ToolRiskLevel.LOW,
    rate_limit=5,  # Only 5 per minute
    # ...
)

# No rate limit for critical tools (use other safeguards)
admin_tool = ToolDefinition(
    name="admin_operation",
    risk_level=ToolRiskLevel.CRITICAL,
    rate_limit=None,  # No rate limit, approval required instead
    requires_approval=True,
    # ...
)
```

### Testing Rate Limits

```python
async def test_rate_limiting():
    """Test that rate limiting works"""
    registry = ToolRegistry()

    # Tool with very low rate limit
    test_tool = ToolDefinition(
        name="rate_test",
        # ... other fields ...
        rate_limit=2,  # Only 2 per minute
        implementation=lambda p, c: {"result": "success"}
    )

    registry.register_tool(test_tool)

    # First two calls should succeed
    for i in range(2):
        allowed, msg = registry.check_rate_limit("rate_test")
        assert allowed, f"Call {i+1} should be allowed"

    # Third call should fail
    allowed, msg = registry.check_rate_limit("rate_test")
    assert not allowed, "Third call should be blocked"
    assert "Rate limit exceeded" in msg

    print("Rate limiting works correctly!")

asyncio.run(test_rate_limiting())
```

---

## Execution Logging

### Why Log Executions?

Execution logs provide:
- **Audit trail** - Who executed what and when
- **Debugging** - Trace errors and performance issues
- **Analytics** - Usage patterns and optimization opportunities
- **Compliance** - Regulatory requirements

### Automatic Logging

The registry doesn't automatically log executions - you need to call `log_execution()` after each tool run:

```python
import time

async def execute_and_log(tool_name: str, params: dict, context: dict):
    """Execute tool and log the result"""

    tool = registry.get_tool(tool_name)
    start_time = time.time()

    try:
        result = await tool.execute(params, context)
        execution_time = time.time() - start_time

        # Log successful execution
        registry.log_execution(
            tool_name=tool_name,
            params=params,
            result=result,
            execution_time=execution_time,
            success=True
        )

        return result

    except Exception as e:
        execution_time = time.time() - start_time

        # Log failed execution
        registry.log_execution(
            tool_name=tool_name,
            params=params,
            result={},
            execution_time=execution_time,
            success=False,
            error=str(e)
        )

        raise
```

### Retrieving Logs

```python
# Get all execution logs
all_logs = registry.get_execution_log()

# Get logs for specific tool
backup_logs = registry.get_execution_log(tool_name="backup_database_full")

# Get last 10 executions
recent_logs = registry.get_execution_log(limit=10)

# Get recent logs for specific tool
recent_backups = registry.get_execution_log(
    tool_name="backup_database_full",
    limit=5
)
```

### Log Entry Structure

Each log entry contains:

```python
{
    'timestamp': 1704470400.0,              # Unix timestamp
    'tool_name': 'backup_database_full',    # Tool executed
    'params': {                              # Parameters used
        'database': 'production',
        'destination': '/backups/prod.sql.gz'
    },
    'result': {                              # Result (if successful)
        'backup_path': '/backups/prod.sql.gz',
        'size_bytes': 1024000,
        'checksum': 'abc123...'
    },
    'execution_time': 45.2,                  # Seconds
    'success': True,                         # Success/failure
    'error': None                            # Error message (if failed)
}
```

### Analyzing Logs

```python
def analyze_execution_logs(tool_name: str = None):
    """Analyze execution logs for insights"""

    logs = registry.get_execution_log(tool_name=tool_name)

    if not logs:
        print("No execution logs found")
        return

    total = len(logs)
    successful = sum(1 for log in logs if log['success'])
    failed = total - successful

    execution_times = [log['execution_time'] for log in logs if log['success']]
    avg_time = sum(execution_times) / len(execution_times) if execution_times else 0
    max_time = max(execution_times) if execution_times else 0
    min_time = min(execution_times) if execution_times else 0

    print(f"Execution Log Analysis{' for ' + tool_name if tool_name else ''}:")
    print(f"  Total executions: {total}")
    print(f"  Successful: {successful} ({successful/total*100:.1f}%)")
    print(f"  Failed: {failed} ({failed/total*100:.1f}%)")
    print(f"  Avg execution time: {avg_time:.2f}s")
    print(f"  Min/Max time: {min_time:.2f}s / {max_time:.2f}s")

    # Show recent errors
    errors = [log for log in logs if not log['success']]
    if errors:
        print(f"\nRecent errors:")
        for log in errors[-5:]:
            print(f"  - {log['tool_name']}: {log['error']}")

# Usage
analyze_execution_logs()
analyze_execution_logs(tool_name="backup_database_full")
```

### Performance Monitoring

```python
def monitor_slow_executions(threshold_seconds: float = 10.0):
    """Find slow tool executions"""

    all_logs = registry.get_execution_log()
    slow_executions = [
        log for log in all_logs
        if log['execution_time'] > threshold_seconds
    ]

    if not slow_executions:
        print(f"No executions slower than {threshold_seconds}s")
        return

    print(f"Found {len(slow_executions)} slow executions (>{threshold_seconds}s):")

    # Sort by execution time
    slow_executions.sort(key=lambda x: x['execution_time'], reverse=True)

    for log in slow_executions[:10]:
        print(f"  {log['tool_name']}: {log['execution_time']:.2f}s")
        print(f"    Params: {log['params']}")

# Usage
monitor_slow_executions(threshold_seconds=5.0)
```

### Error Tracking

```python
def track_error_patterns():
    """Identify common errors"""

    all_logs = registry.get_execution_log()
    failed_logs = [log for log in all_logs if not log['success']]

    if not failed_logs:
        print("No errors found")
        return

    # Group errors by message
    error_counts = {}
    for log in failed_logs:
        error = log['error']
        error_counts[error] = error_counts.get(error, 0) + 1

    print("Common errors:")
    for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {count}x: {error}")

# Usage
track_error_patterns()
```

---

## Complete Example

### Building a Custom Database Optimization Tool

Let's build a complete, production-ready tool that analyzes and optimizes database performance.

#### Step 1: Implementation

```python
import time
from typing import Dict, Any, List

async def optimize_database(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze database and apply optimizations

    This tool:
    1. Analyzes table statistics
    2. Identifies missing indexes
    3. Finds unused indexes
    4. Suggests query optimizations
    5. Optionally applies recommended changes

    Args:
        params: Tool parameters
            - database (str): Database name
            - analyze_only (bool): If True, only analyze without applying changes
            - min_table_size (int): Minimum table size to analyze (rows)
            - apply_recommendations (bool): Apply recommended changes

        context: Execution context
            - database_module: Database connection module

    Returns:
        Dict containing:
            - analysis_duration (float): Analysis time in seconds
            - tables_analyzed (int): Number of tables analyzed
            - recommendations (list): List of optimization recommendations
            - applied_changes (list): Changes that were applied (if any)
            - estimated_improvement (dict): Estimated performance gains
    """
    start_time = time.time()

    # Extract parameters
    database = params['database']
    analyze_only = params.get('analyze_only', True)
    min_table_size = params.get('min_table_size', 1000)
    apply_recommendations = params.get('apply_recommendations', False)

    # Validate
    if not analyze_only and not apply_recommendations:
        raise ValueError("apply_recommendations must be True when analyze_only is False")

    # Get database module from context
    database_module = context.get('database_module')
    if not database_module:
        # Mock implementation for demo
        pass

    # Analysis results (mock data for demonstration)
    recommendations = [
        {
            "type": "missing_index",
            "table": "users",
            "columns": ["email"],
            "reason": "Column used in WHERE clauses but not indexed",
            "estimated_improvement": "30% query speedup",
            "ddl": "CREATE INDEX idx_users_email ON users(email)"
        },
        {
            "type": "unused_index",
            "table": "orders",
            "index": "idx_orders_legacy",
            "reason": "Not used in any queries in last 30 days",
            "estimated_improvement": "5% write speedup",
            "ddl": "DROP INDEX idx_orders_legacy"
        },
        {
            "type": "table_statistics",
            "table": "products",
            "reason": "Statistics outdated (last updated 45 days ago)",
            "estimated_improvement": "10% query plan improvement",
            "ddl": "ANALYZE products"
        },
        {
            "type": "query_optimization",
            "query_pattern": "SELECT * FROM orders WHERE user_id = ?",
            "reason": "Using SELECT * instead of specific columns",
            "recommendation": "Specify required columns explicitly",
            "estimated_improvement": "20% network bandwidth reduction"
        }
    ]

    applied_changes = []

    # Apply changes if requested
    if apply_recommendations:
        for rec in recommendations:
            if rec['type'] in ['missing_index', 'table_statistics']:
                # In real implementation, would execute DDL
                # await database_module.execute(rec['ddl'])
                applied_changes.append({
                    "recommendation": rec,
                    "applied": True,
                    "timestamp": time.time()
                })

    analysis_duration = time.time() - start_time

    return {
        "database": database,
        "analysis_duration": round(analysis_duration, 2),
        "tables_analyzed": 15,
        "recommendations": recommendations,
        "applied_changes": applied_changes,
        "estimated_improvement": {
            "query_performance": "25% average speedup",
            "write_performance": "5% speedup",
            "storage_savings": "50 MB index overhead reduction"
        },
        "summary": {
            "missing_indexes": 1,
            "unused_indexes": 1,
            "outdated_statistics": 1,
            "query_optimizations": 1,
            "total_recommendations": len(recommendations),
            "changes_applied": len(applied_changes)
        }
    }
```

#### Step 2: Define Schemas

```python
# Parameter schema
optimization_params_schema = {
    "type": "object",
    "properties": {
        "database": {
            "type": "string",
            "description": "Database name to optimize",
            "minLength": 1
        },
        "analyze_only": {
            "type": "boolean",
            "description": "If true, only analyze without applying changes",
            "default": True
        },
        "min_table_size": {
            "type": "integer",
            "description": "Minimum table size (rows) to analyze",
            "minimum": 0,
            "default": 1000
        },
        "apply_recommendations": {
            "type": "boolean",
            "description": "Apply recommended optimizations automatically",
            "default": False
        }
    },
    "required": ["database"]
}

# Return schema
optimization_returns_schema = {
    "type": "object",
    "properties": {
        "database": {"type": "string"},
        "analysis_duration": {"type": "number", "minimum": 0},
        "tables_analyzed": {"type": "integer", "minimum": 0},
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "table": {"type": "string"},
                    "reason": {"type": "string"},
                    "estimated_improvement": {"type": "string"}
                }
            }
        },
        "applied_changes": {
            "type": "array",
            "items": {"type": "object"}
        },
        "estimated_improvement": {"type": "object"},
        "summary": {
            "type": "object",
            "properties": {
                "total_recommendations": {"type": "integer"},
                "changes_applied": {"type": "integer"}
            }
        }
    },
    "required": [
        "database",
        "analysis_duration",
        "tables_analyzed",
        "recommendations",
        "applied_changes",
        "estimated_improvement",
        "summary"
    ]
}
```

#### Step 3: Create Tool Definition

```python
optimization_tool = ToolDefinition(
    name="optimize_database",
    description=(
        "Analyze database performance and apply optimizations. "
        "Identifies missing indexes, unused indexes, outdated statistics, "
        "and query optimization opportunities."
    ),
    category=ToolCategory.ANALYSIS,
    risk_level=ToolRiskLevel.MEDIUM,  # Can modify schema if applied
    required_capabilities=[
        "database_read",
        "database_analyze",
        "database_ddl"  # Only needed if applying changes
    ],
    parameters_schema=optimization_params_schema,
    returns_schema=optimization_returns_schema,
    implementation=optimize_database,
    requires_approval=True,  # Require approval before applying changes
    max_execution_time=600,  # 10 minutes max
    rate_limit=5,  # Only 5 optimizations per minute
    examples=[
        {
            "description": "Analyze database without applying changes",
            "params": {
                "database": "production",
                "analyze_only": True
            },
            "expected_output": {
                "database": "production",
                "analysis_duration": 12.5,
                "tables_analyzed": 15,
                "recommendations": [...],
                "applied_changes": [],
                "summary": {
                    "total_recommendations": 4,
                    "changes_applied": 0
                }
            }
        },
        {
            "description": "Analyze and apply safe optimizations",
            "params": {
                "database": "staging",
                "analyze_only": False,
                "apply_recommendations": True,
                "min_table_size": 5000
            },
            "expected_output": {
                "database": "staging",
                "analysis_duration": 18.3,
                "tables_analyzed": 8,
                "recommendations": [...],
                "applied_changes": [...],
                "summary": {
                    "total_recommendations": 3,
                    "changes_applied": 2
                }
            }
        }
    ]
)
```

#### Step 4: Register and Test

```python
async def test_optimization_tool():
    """Complete test of optimization tool"""

    # Create registry and register tool
    registry = ToolRegistry()
    registry.register_tool(optimization_tool)

    print("=" * 60)
    print("DATABASE OPTIMIZATION TOOL TEST")
    print("=" * 60)

    # Test 1: Analysis only
    print("\nTest 1: Analysis only (safe)")
    params1 = {
        "database": "production",
        "analyze_only": True,
        "min_table_size": 1000
    }

    start_time = time.time()
    result1 = await optimization_tool.execute(params1, {})
    exec_time1 = time.time() - start_time

    # Log execution
    registry.log_execution(
        tool_name="optimize_database",
        params=params1,
        result=result1,
        execution_time=exec_time1,
        success=True
    )

    print(f"Analysis completed in {exec_time1:.2f}s")
    print(f"Tables analyzed: {result1['tables_analyzed']}")
    print(f"Recommendations: {result1['summary']['total_recommendations']}")
    print(f"Changes applied: {result1['summary']['changes_applied']}")

    # Show recommendations
    print("\nRecommendations:")
    for i, rec in enumerate(result1['recommendations'], 1):
        print(f"\n  {i}. {rec['type'].upper()}")
        print(f"     Table: {rec.get('table', 'N/A')}")
        print(f"     Reason: {rec['reason']}")
        print(f"     Impact: {rec['estimated_improvement']}")

    # Test 2: Apply recommendations
    print("\n" + "=" * 60)
    print("\nTest 2: Apply recommendations (requires approval)")
    params2 = {
        "database": "staging",
        "analyze_only": False,
        "apply_recommendations": True,
        "min_table_size": 5000
    }

    # Check rate limit
    is_allowed, error_msg = registry.check_rate_limit("optimize_database")
    if not is_allowed:
        print(f"Rate limit check failed: {error_msg}")
        return

    start_time = time.time()
    result2 = await optimization_tool.execute(params2, {})
    exec_time2 = time.time() - start_time

    registry.log_execution(
        tool_name="optimize_database",
        params=params2,
        result=result2,
        execution_time=exec_time2,
        success=True
    )

    print(f"Optimization completed in {exec_time2:.2f}s")
    print(f"Changes applied: {result2['summary']['changes_applied']}")

    # Show applied changes
    if result2['applied_changes']:
        print("\nApplied changes:")
        for change in result2['applied_changes']:
            rec = change['recommendation']
            print(f"\n  - {rec['type']}: {rec.get('table', 'N/A')}")
            print(f"    DDL: {rec.get('ddl', 'N/A')}")

    # Show execution logs
    print("\n" + "=" * 60)
    print("\nExecution Log Summary:")
    logs = registry.get_execution_log(tool_name="optimize_database")
    print(f"Total executions: {len(logs)}")

    for i, log in enumerate(logs, 1):
        print(f"\n  Execution {i}:")
        print(f"    Database: {log['params']['database']}")
        print(f"    Duration: {log['execution_time']:.2f}s")
        print(f"    Success: {log['success']}")
        print(f"    Recommendations: {log['result']['summary']['total_recommendations']}")
        print(f"    Applied: {log['result']['summary']['changes_applied']}")

    # Show registry stats
    print("\n" + "=" * 60)
    print("\nRegistry Statistics:")
    stats = registry.get_registry_stats()
    print(f"Total tools: {stats['total_tools']}")
    print(f"Total executions: {stats['total_executions']}")
    print(f"Success rate: {stats['successful_executions']}/{stats['total_executions']}")

# Run the test
asyncio.run(test_optimization_tool())
```

#### Step 5: Integration with Agents

```python
async def agent_uses_optimization_tool(agent_capabilities: List[str]):
    """Example of agent using the optimization tool"""

    registry = ToolRegistry()
    registry.register_tool(optimization_tool)

    # Check if agent has required capabilities
    available_tools = registry.find_tools(capabilities=agent_capabilities)

    optimization_available = any(t.name == "optimize_database" for t in available_tools)

    if not optimization_available:
        print("Agent does not have required capabilities for optimization tool")
        print(f"Agent capabilities: {agent_capabilities}")
        print(f"Required: {optimization_tool.required_capabilities}")
        return

    # Agent can use the tool
    print("Agent has access to optimization tool")

    # Get tool description for LLM
    tool_desc = registry.get_tool_description("optimize_database")

    # LLM prompt would include this description
    llm_prompt = f"""
You are a database optimization agent. Your task is to optimize the production database.

You have access to this tool:
{tool_desc}

Recommend the appropriate parameters for this optimization task.
"""

    print("\nLLM Prompt:")
    print(llm_prompt)

    # LLM would select parameters, then execute
    params = {
        "database": "production",
        "analyze_only": True,  # Safe first step
        "min_table_size": 10000
    }

    result = await optimization_tool.execute(params, {})
    print(f"\nOptimization result: {result['summary']}")

# Test with different agent capabilities
print("Test 1: Agent with full capabilities")
asyncio.run(agent_uses_optimization_tool([
    "database_read",
    "database_analyze",
    "database_ddl"
]))

print("\n" + "=" * 60)
print("\nTest 2: Agent with limited capabilities")
asyncio.run(agent_uses_optimization_tool([
    "database_read"  # Missing database_analyze and database_ddl
]))
```

---

## Best Practices

### 1. Tool Design Patterns

#### Keep Tools Focused

```python
# GOOD: Focused, single-purpose tool
async def backup_table(params, context):
    """Backup a single table"""
    pass

# BAD: Tool doing too many things
async def database_operations(params, context):
    """Backup, restore, analyze, or optimize based on 'operation' parameter"""
    pass
```

#### Use Clear, Descriptive Names

```python
# GOOD
"backup_database_full"
"analyze_schema_indexes"
"validate_backup_integrity"

# BAD
"do_backup"
"analyze"
"check"
```

#### Provide Comprehensive Descriptions

```python
# GOOD
description=(
    "Create full database backup with optional compression. "
    "Validates backup integrity with MD5 checksum. "
    "Supports multiple database types: PostgreSQL, MySQL, Oracle."
)

# BAD
description="Backup database"
```

### 2. Parameter Validation Patterns

#### Always Validate Required Fields

```python
parameters_schema = {
    "type": "object",
    "properties": {
        "database": {"type": "string"},
        "table": {"type": "string"}
    },
    "required": ["database", "table"]  # Explicitly required
}
```

#### Provide Sensible Defaults

```python
parameters_schema = {
    "type": "object",
    "properties": {
        "compression": {
            "type": "boolean",
            "default": True  # Sensible default
        },
        "timeout": {
            "type": "integer",
            "default": 300,
            "minimum": 1,
            "maximum": 3600
        }
    }
}
```

#### Use Enums for Limited Choices

```python
parameters_schema = {
    "type": "object",
    "properties": {
        "backup_type": {
            "type": "string",
            "enum": ["full", "incremental", "differential"]  # Limited choices
        }
    }
}
```

### 3. Error Handling

#### Raise Specific Exceptions

```python
async def tool_impl(params, context):
    # Parameter errors
    if not params.get('database'):
        raise ValueError("Parameter 'database' is required")

    # Context errors
    db_module = context.get('database_module')
    if not db_module:
        raise RuntimeError("database_module not available in context")

    # Execution errors
    try:
        result = await db_module.execute(...)
    except ConnectionError as e:
        raise RuntimeError(f"Database connection failed: {e}") from e
    except TimeoutError as e:
        raise RuntimeError(f"Operation timed out: {e}") from e

    return result
```

#### Include Context in Errors

```python
# GOOD: Specific, actionable error
raise ValueError(
    f"Invalid backup_type '{backup_type}'. "
    f"Must be one of: full, incremental, differential"
)

# BAD: Vague error
raise ValueError("Invalid type")
```

### 4. Risk Level Assignment

#### Follow Risk Level Guidelines

```python
# SAFE: Read-only, no modifications
risk_level=ToolRiskLevel.SAFE

# LOW: Single record modifications
risk_level=ToolRiskLevel.LOW

# MEDIUM: Bulk modifications, easily reversible
risk_level=ToolRiskLevel.MEDIUM

# HIGH: Large-scale changes, difficult to reverse
risk_level=ToolRiskLevel.HIGH

# CRITICAL: Irreversible, schema changes
risk_level=ToolRiskLevel.CRITICAL
```

#### Match Approval Requirements to Risk

```python
# SAFE/LOW: Usually no approval
requires_approval=False

# MEDIUM: Approval recommended
requires_approval=True

# HIGH/CRITICAL: Approval mandatory
requires_approval=True
```

### 5. Capability Design

#### Use Hierarchical Capabilities

```python
# Good hierarchy
capabilities = [
    "database",           # Top level
    "database_read",      # More specific
    "database_write",     # Different aspect
    "database_write_bulk" # Even more specific
]

# Bad: Flat, unclear
capabilities = ["db1", "db2", "access"]
```

#### Be Specific About Requirements

```python
# GOOD: Specific capabilities
required_capabilities=[
    "database_read",
    "backup_create",
    "file_write"
]

# BAD: Vague or overly broad
required_capabilities=["admin"]
```

### 6. Rate Limiting Strategy

#### Match Rate Limits to Resource Cost

```python
# Cheap read operations: High limit
rate_limit=1000  # 1000/min

# Moderate operations: Medium limit
rate_limit=100   # 100/min

# Expensive operations: Low limit
rate_limit=10    # 10/min

# Very expensive: Very low limit
rate_limit=2     # 2/min

# Critical operations: No rate limit, use approval instead
rate_limit=None
requires_approval=True
```

### 7. Documentation and Examples

#### Provide Multiple Examples

```python
examples=[
    {
        "description": "Basic usage",
        "params": {"database": "prod"},
        "expected_output": {...}
    },
    {
        "description": "With all optional parameters",
        "params": {
            "database": "prod",
            "compression": True,
            "validate": True
        },
        "expected_output": {...}
    },
    {
        "description": "Minimal configuration",
        "params": {"database": "test"},
        "expected_output": {...}
    }
]
```

#### Document Implementation Details

```python
async def complex_tool(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Complex database operation

    This tool performs the following steps:
    1. Validates database connection
    2. Creates transaction
    3. Executes operations in batch
    4. Validates results
    5. Commits or rolls back

    Args:
        params: Tool parameters
            database (str): Database name
            operations (list): List of operations to perform

        context: Execution context
            database_module: Database connection module

    Returns:
        Dict containing:
            operations_completed (int): Number of successful operations
            rollback (bool): Whether transaction was rolled back
            errors (list): Any errors encountered

    Raises:
        ValueError: If parameters are invalid
        RuntimeError: If database operations fail

    Example:
        >>> result = await complex_tool(
        ...     params={"database": "prod", "operations": [...]},
        ...     context={"database_module": db}
        ... )
    """
    pass
```

### 8. Testing

#### Test All Validation Paths

```python
async def test_tool_validation():
    """Test parameter validation"""

    # Test valid parameters
    result = await tool.execute(
        params={"database": "test", "table": "users"},
        context={}
    )
    assert result is not None

    # Test missing required parameter
    try:
        await tool.execute(params={"database": "test"}, context={})
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "table" in str(e).lower()

    # Test invalid parameter type
    try:
        await tool.execute(
            params={"database": "test", "table": 123},  # Wrong type
            context={}
        )
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
```

#### Test Error Conditions

```python
async def test_error_handling():
    """Test error handling"""

    # Test with missing context
    try:
        await tool.execute(
            params={"database": "test"},
            context={}  # Missing database_module
        )
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "database_module" in str(e)
```

### 9. Performance Optimization

#### Use Async/Await Properly

```python
# GOOD: Properly async
async def tool_impl(params, context):
    db = context['database_module']
    result = await db.query(...)  # Await async operations
    return result

# BAD: Blocking in async function
async def tool_impl(params, context):
    import time
    time.sleep(10)  # Blocks event loop!
    return {}
```

#### Set Appropriate Timeouts

```python
# Fast operations
max_execution_time=5

# Moderate operations
max_execution_time=60

# Long-running operations
max_execution_time=600

# Very long operations
max_execution_time=3600
```

### 10. Security Considerations

#### Sanitize Inputs

```python
async def execute_query(params, context):
    query = params['query']

    # BAD: SQL injection risk
    # result = await db.execute(f"SELECT * FROM {query}")

    # GOOD: Use parameterized queries
    result = await db.execute_safe(query, params.get('bind_vars', []))
    return result
```

#### Validate File Paths

```python
async def read_file(params, context):
    file_path = params['path']

    # Validate path to prevent directory traversal
    import os
    if '..' in file_path or file_path.startswith('/'):
        raise ValueError("Invalid file path")

    # Use safe path joining
    safe_path = os.path.join('/safe/base/dir', file_path)

    with open(safe_path, 'r') as f:
        return {"content": f.read()}
```

#### Limit Resource Usage

```python
async def process_data(params, context):
    data = params['data']

    # Limit data size
    if len(data) > 1000000:  # 1MB limit
        raise ValueError("Data size exceeds limit")

    # Limit execution time internally
    import asyncio
    try:
        result = await asyncio.wait_for(
            expensive_operation(data),
            timeout=30
        )
    except asyncio.TimeoutError:
        raise RuntimeError("Operation timed out")

    return result
```

---

## Summary

The Tool Registry System provides a robust foundation for building safe, validated, and observable agent tools. Key takeaways:

1. **Always validate** - Use JSON schemas for both inputs and outputs
2. **Classify appropriately** - Choose correct risk levels and categories
3. **Be specific** - Clear names, descriptions, and capabilities
4. **Log everything** - Maintain audit trails for debugging and compliance
5. **Limit wisely** - Use rate limits and timeouts to prevent abuse
6. **Document thoroughly** - Help LLMs and humans understand tools
7. **Test comprehensively** - Validate all code paths and error conditions
8. **Prioritize safety** - Require approval for risky operations

The Tool Registry is the cornerstone of safe, reliable agentic AI workflows in AIShell.
