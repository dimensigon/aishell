# 🚀 AIShell Quick Reference Card

**Fast lookup for commands, patterns, APIs, and configurations**

Version: 2.0.0 | Last Updated: October 2025

---

## Table of Contents

1. [33 NLP Patterns](#33-nlp-patterns)
2. [Common Commands](#common-commands)
3. [API Endpoints](#api-endpoints)
4. [Configuration Examples](#configuration-examples)
5. [Agent Development Patterns](#agent-development-patterns)
6. [Tool Registry](#tool-registry)
7. [Safety & Security](#safety--security)
8. [Common Errors & Solutions](#common-errors--solutions)
9. [Performance Tips](#performance-tips)
10. [Security Checklist](#security-checklist)

---

## 33 NLP Patterns

AIShell supports 33 natural language patterns for intuitive command execution:

### File Operations (7 patterns)
```bash
# Pattern 1: Create file
"create a file called config.json"

# Pattern 2: Read file
"show me the contents of config.json"

# Pattern 3: Edit file
"update config.json to change port to 8080"

# Pattern 4: Delete file
"remove the file logs.txt"

# Pattern 5: Copy file
"copy database.db to backup/database.db"

# Pattern 6: Move file
"move old_config.json to archive/"

# Pattern 7: Search files
"find all Python files modified today"
```

### Database Operations (8 patterns)
```bash
# Pattern 8: Query data
"show me all users from the database"

# Pattern 9: Insert data
"add a new user with name John and email john@example.com"

# Pattern 10: Update data
"change user status to active for user_id 123"

# Pattern 11: Delete data
"remove all users created before 2020"

# Pattern 12: Create table
"create a table called products with columns id, name, price"

# Pattern 13: Drop table
"delete the temporary_data table"

# Pattern 14: Backup database
"create a backup of the users database"

# Pattern 15: Restore database
"restore database from backup_2025.sql"
```

### System Operations (6 patterns)
```bash
# Pattern 16: Process management
"list all running Python processes"

# Pattern 17: Disk usage
"show me disk space usage"

# Pattern 18: Memory usage
"check current memory consumption"

# Pattern 19: Network status
"test connection to api.example.com"

# Pattern 20: Service status
"check if nginx is running"

# Pattern 21: System info
"show system information"
```

### Agent Operations (5 patterns)
```bash
# Pattern 22: Run agent
"run the backup agent for database production_db"

# Pattern 23: Create agent
"create a new agent for log analysis"

# Pattern 24: List agents
"show all available agents"

# Pattern 25: Agent status
"check status of migration agent"

# Pattern 26: Stop agent
"stop the running backup agent"
```

### Workflow Operations (4 patterns)
```bash
# Pattern 27: Execute workflow
"run the nightly maintenance workflow"

# Pattern 28: Create workflow
"create a workflow to backup, optimize, and verify database"

# Pattern 29: Schedule workflow
"schedule the backup workflow to run daily at 2am"

# Pattern 30: Workflow status
"show status of all running workflows"
```

### Analysis Operations (3 patterns)
```bash
# Pattern 31: Analyze performance
"analyze query performance for slow queries"

# Pattern 32: Generate report
"create a report of database usage this month"

# Pattern 33: Optimize
"suggest optimizations for the users table"
```

---

## Common Commands

### Installation & Setup
```bash
# Install AIShell
git clone https://github.com/dimensigon/aishell.git
cd aishell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run AIShell
python -m aishell

# Run with config file
python -m aishell --config ~/.aishell/config.yaml

# Run in development mode
python -m aishell --debug
```

### Health Checks
```bash
# Run all health checks
python -m aishell health check

# Check specific component
python -m aishell health check --component database
python -m aishell health check --component llm
python -m aishell health check --component filesystem

# Run health check with timeout
python -m aishell health check --timeout 30
```

### Agent Commands
```bash
# List all agents
python -m aishell agent list

# Run specific agent
python -m aishell agent run BackupAgent --params '{"database": "prod"}'

# Create custom agent
python -m aishell agent create --template backup --name MyBackupAgent

# Agent status
python -m aishell agent status <agent_id>

# Stop agent
python -m aishell agent stop <agent_id>
```

### Tool Commands
```bash
# List registered tools
python -m aishell tool list

# Register new tool
python -m aishell tool register --file tools/my_tool.json

# Get tool info
python -m aishell tool info database_backup

# Validate tool
python -m aishell tool validate database_backup
```

### Database Commands
```bash
# List connections
python -m aishell db list

# Add connection
python -m aishell db add --name prod --type postgresql --host localhost

# Test connection
python -m aishell db test prod

# Execute query
python -m aishell db query prod "SELECT * FROM users LIMIT 10"

# Backup database
python -m aishell db backup prod --output /backups/prod_backup.sql
```

### Configuration Commands
```bash
# Show current config
python -m aishell config show

# Set config value
python -m aishell config set llm.model gpt-4

# Validate config
python -m aishell config validate

# Export config
python -m aishell config export --output config_backup.yaml
```

---

## API Endpoints

### Health Check API
```python
from src.health.health_check import HealthCheckService

# Initialize service
health_service = HealthCheckService(config)

# Check all components
status = await health_service.check_all()
# Returns: {'overall': 'healthy', 'components': {...}}

# Check specific component
db_status = await health_service.check_component('database')
# Returns: {'status': 'healthy', 'latency': 0.15, 'details': {...}}

# Get health metrics
metrics = await health_service.get_metrics()
# Returns: {'uptime': 3600, 'checks_performed': 120, ...}
```

### Agent API
```python
from src.agents.base import BaseAgent, AgentConfig, TaskContext

# Create agent config
config = AgentConfig(
    agent_id="agent_001",
    agent_type="backup",
    capabilities=[AgentCapability.DATABASE_READ, AgentCapability.BACKUP_CREATE]
)

# Initialize agent
agent = BackupAgent(config, llm_manager, tool_registry, state_manager)

# Run agent
task = TaskContext(
    task_id="task_001",
    task_description="Backup production database",
    parameters={"database": "prod", "output_path": "/backups/"}
)
result = await agent.run(task)
# Returns: {'success': True, 'backup_path': '/backups/prod_2025.sql', ...}

# Get agent status
status = agent.get_status()
# Returns: {'state': 'idle', 'last_task': 'task_001', ...}
```

### Tool Registry API
```python
from src.tools.tool_registry import ToolRegistry, ToolDefinition

# Initialize registry
registry = ToolRegistry()

# Register tool
tool_def = ToolDefinition(
    name="database_backup",
    category="database",
    risk_level="medium",
    description="Create database backup",
    parameters_schema={
        "type": "object",
        "properties": {
            "database": {"type": "string"},
            "output_path": {"type": "string"}
        },
        "required": ["database"]
    }
)
registry.register_tool(tool_def, backup_function)

# Find tools
db_tools = registry.find_tools(category="database")
# Returns: [ToolDefinition(...), ToolDefinition(...)]

# Execute tool
result = await registry.execute_tool(
    "database_backup",
    {"database": "prod", "output_path": "/backups/"}
)
# Returns: {'success': True, 'output': {...}}
```

### State Management API
```python
from src.state.state_manager import StateManager

# Initialize state manager
state_manager = StateManager(config)

# Save checkpoint
await state_manager.save_checkpoint(
    task_id="task_001",
    checkpoint_name="after_backup",
    data={"backup_path": "/backups/prod.sql", "timestamp": "2025-10-11"}
)

# List checkpoints
checkpoints = await state_manager.list_checkpoints("task_001")
# Returns: [{'name': 'after_backup', 'timestamp': '2025-10-11', ...}]

# Restore checkpoint
checkpoint_data = await state_manager.restore_checkpoint("checkpoint_id_123")
# Returns: {"backup_path": "/backups/prod.sql", ...}

# Delete checkpoint
await state_manager.delete_checkpoint("checkpoint_id_123")
```

### Safety System API
```python
from src.safety.safety_manager import SafetyManager, RiskLevel

# Initialize safety manager
safety_manager = SafetyManager(config)

# Assess risk
risk_assessment = safety_manager.assess_risk(
    operation_type="database_write",
    parameters={"query": "DELETE FROM users WHERE created_at < '2020-01-01'"}
)
# Returns: {'risk_level': 'high', 'requires_approval': True, ...}

# Request approval
approval = await safety_manager.request_approval(
    operation={"type": "database_write", "query": "DELETE ..."},
    risk_level=RiskLevel.HIGH
)
# Returns: {'approved': True, 'approved_by': 'admin', ...}

# Validate SQL
sql_validation = safety_manager.validate_sql(
    "SELECT * FROM users WHERE id = ?"
)
# Returns: {'safe': True, 'issues': []}
```

---

## Configuration Examples

### Basic Configuration
```yaml
# ~/.aishell/config.yaml

# LLM Configuration
llm:
  provider: openai
  model: gpt-4
  temperature: 0.7
  max_tokens: 2000
  timeout: 30

# Database Configuration
database:
  default_connection: prod
  connections:
    prod:
      type: postgresql
      host: localhost
      port: 5432
      database: production_db
      username: admin
      # Password stored in encrypted vault
    dev:
      type: postgresql
      host: localhost
      port: 5432
      database: dev_db
      username: developer

# Agent Configuration
agents:
  max_concurrent: 5
  default_timeout: 300
  checkpoint_dir: ~/.aishell/checkpoints
  retry_attempts: 3

# Safety Configuration
safety:
  enabled: true
  require_approval_for: [high, critical]
  sql_validation: true
  audit_logging: true
  audit_log_path: ~/.aishell/audit.log

# Health Check Configuration
health:
  enabled: true
  check_interval: 60
  timeout: 10
  components:
    - database
    - llm
    - filesystem
    - memory

# Logging Configuration
logging:
  level: INFO
  file: ~/.aishell/aishell.log
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### Advanced Configuration
```yaml
# Advanced configuration with all options

llm:
  provider: openai
  model: gpt-4
  api_key_env: OPENAI_API_KEY
  temperature: 0.7
  max_tokens: 2000
  timeout: 30
  retry_attempts: 3
  retry_delay: 2
  streaming: true
  cache_enabled: true
  cache_ttl: 3600

database:
  connection_pool:
    min_size: 5
    max_size: 20
    timeout: 30
  query_timeout: 60
  auto_commit: false
  isolation_level: read_committed

agents:
  coordinator:
    max_concurrent_workflows: 3
    workflow_timeout: 1800
  worker:
    max_concurrent_tasks: 10
    task_timeout: 600
  scheduler:
    enabled: true
    check_interval: 60

tools:
  registry_path: ~/.aishell/tools
  auto_discover: true
  validation_enabled: true
  rate_limiting:
    enabled: true
    max_requests_per_minute: 60

safety:
  risk_assessment:
    enabled: true
    custom_rules: ~/.aishell/safety_rules.yaml
  approval:
    callback: custom_approval_function
    timeout: 300
  sql_validation:
    block_patterns:
      - DROP TABLE
      - TRUNCATE
      - xp_cmdshell
    require_where_clause: true

monitoring:
  metrics_enabled: true
  metrics_port: 9090
  prometheus_export: true
  alert_thresholds:
    error_rate: 0.05
    response_time: 5.0
```

### Docker Configuration
```dockerfile
# Dockerfile for AIShell

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create config directory
RUN mkdir -p /root/.aishell

# Copy config
COPY config/docker_config.yaml /root/.aishell/config.yaml

# Expose metrics port
EXPOSE 9090

# Run AIShell
CMD ["python", "-m", "aishell"]
```

### Docker Compose
```yaml
# docker-compose.yml

version: '3.8'

services:
  aishell:
    build: .
    container_name: aishell
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_PASSWORD=${DATABASE_PASSWORD}
    volumes:
      - ./config:/root/.aishell
      - ./data:/data
      - ./backups:/backups
    ports:
      - "9090:9090"
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:15
    container_name: aishell_postgres
    environment:
      - POSTGRES_DB=aishell
      - POSTGRES_USER=aishell
      - POSTGRES_PASSWORD=${DATABASE_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

---

## Agent Development Patterns

### Basic Agent Template
```python
from src.agents.base import BaseAgent, AgentConfig, TaskContext, AgentCapability
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MyCustomAgent(BaseAgent):
    """Custom agent template"""

    def __init__(self, config: AgentConfig, llm_manager, tool_registry, state_manager):
        super().__init__(config, llm_manager, tool_registry, state_manager)
        self.setup_tools()

    def setup_tools(self):
        """Register required tools"""
        required_tools = ['tool1', 'tool2', 'tool3']
        for tool_name in required_tools:
            if not self.tool_registry.has_tool(tool_name):
                raise ValueError(f"Required tool not found: {tool_name}")

    async def plan(self, task: TaskContext) -> List[Dict[str, Any]]:
        """Generate execution plan using LLM"""
        logger.info(f"Planning for task: {task.task_description}")

        # Build planning prompt
        prompt = self._build_planning_prompt(task)

        # Generate plan using LLM
        plan = await self.llm_manager.generate_plan(prompt)

        # Validate plan
        self._validate_plan(plan)

        logger.info(f"Generated plan with {len(plan)} steps")
        return plan

    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute single step in plan"""
        logger.info(f"Executing step: {step['tool']}")

        # Get tool from registry
        tool = self.tool_registry.get_tool(step['tool'])

        # Execute tool with parameters
        result = await tool.execute(step['params'], self.context)

        # Validate result
        if not result.get('success'):
            raise AgentExecutionError(f"Step failed: {result.get('error')}")

        return result

    def validate_safety(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Validate step safety"""
        risk_level = self._assess_risk(step)

        return {
            'requires_approval': risk_level in ['high', 'critical'],
            'safe': risk_level != 'critical',
            'risk_level': risk_level,
            'risks': self._identify_risks(step),
            'mitigations': self._suggest_mitigations(step)
        }

    def _build_planning_prompt(self, task: TaskContext) -> str:
        """Build LLM prompt for planning"""
        available_tools = self.tool_registry.find_tools(
            capabilities=self.config.capabilities
        )

        return f"""
        Task: {task.task_description}

        Available tools:
        {self._format_tools(available_tools)}

        Generate a step-by-step plan to accomplish this task.
        Each step should specify:
        - tool: The tool to use
        - params: Parameters for the tool
        - rationale: Why this step is needed
        """

    def _assess_risk(self, step: Dict[str, Any]) -> str:
        """Assess risk level of step"""
        tool = self.tool_registry.get_tool(step['tool'])
        return tool.risk_level

    def _validate_plan(self, plan: List[Dict[str, Any]]):
        """Validate generated plan"""
        if not plan:
            raise ValueError("Generated plan is empty")

        for i, step in enumerate(plan):
            if 'tool' not in step:
                raise ValueError(f"Step {i} missing 'tool' field")
            if 'params' not in step:
                raise ValueError(f"Step {i} missing 'params' field")
```

### Multi-Step Workflow Agent
```python
class WorkflowAgent(BaseAgent):
    """Agent that orchestrates multi-step workflows"""

    async def run(self, task: TaskContext) -> Dict[str, Any]:
        """Execute complete workflow"""
        logger.info(f"Starting workflow: {task.task_id}")

        # Generate plan
        plan = await self.plan(task)

        # Save initial checkpoint
        await self.save_checkpoint('plan_generated', {'plan': plan})

        results = []
        for i, step in enumerate(plan):
            logger.info(f"Executing step {i+1}/{len(plan)}")

            # Validate safety
            safety_check = self.validate_safety(step)
            if not safety_check['safe']:
                raise SecurityError(f"Unsafe operation: {safety_check['risks']}")

            # Request approval if needed
            if safety_check['requires_approval']:
                approved = await self.request_approval(step, safety_check)
                if not approved:
                    raise ApprovalDeniedError(f"Step {i} approval denied")

            try:
                # Execute step
                result = await self.execute_step(step)
                results.append(result)

                # Save checkpoint
                await self.save_checkpoint(
                    f'step_{i}_complete',
                    {'step': i, 'result': result}
                )

            except Exception as e:
                logger.error(f"Step {i} failed: {e}")

                # Save error checkpoint
                await self.save_checkpoint(
                    f'step_{i}_failed',
                    {'step': i, 'error': str(e)}
                )

                # Attempt recovery
                if self.config.retry_on_failure:
                    result = await self.retry_step(step, e)
                    results.append(result)
                else:
                    raise

        return {
            'success': True,
            'task_id': task.task_id,
            'steps_completed': len(results),
            'results': results
        }
```

### Parallel Execution Agent
```python
import asyncio

class ParallelAgent(BaseAgent):
    """Agent that executes steps in parallel when possible"""

    async def run(self, task: TaskContext) -> Dict[str, Any]:
        """Execute workflow with parallel steps"""

        # Generate plan
        plan = await self.plan(task)

        # Identify independent steps
        dependency_graph = self._build_dependency_graph(plan)

        # Group steps by execution level
        execution_levels = self._topological_sort(dependency_graph)

        all_results = {}

        # Execute each level in parallel
        for level, steps in enumerate(execution_levels):
            logger.info(f"Executing level {level} with {len(steps)} parallel steps")

            # Create tasks for parallel execution
            tasks = [
                self.execute_step_with_dependencies(step, all_results)
                for step in steps
            ]

            # Execute in parallel
            level_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check for errors
            for step, result in zip(steps, level_results):
                if isinstance(result, Exception):
                    logger.error(f"Step failed: {step['tool']} - {result}")
                    raise result
                all_results[step['id']] = result

        return {
            'success': True,
            'results': all_results,
            'parallel_levels': len(execution_levels)
        }

    async def execute_step_with_dependencies(
        self,
        step: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute step with access to previous results"""

        # Resolve variable references
        params = self._resolve_variables(step['params'], previous_results)

        # Execute with resolved parameters
        step['params'] = params
        return await self.execute_step(step)

    def _resolve_variables(
        self,
        params: Dict[str, Any],
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve ${step_id.field} references"""
        resolved = {}

        for key, value in params.items():
            if isinstance(value, str) and value.startswith('${'):
                # Extract reference: ${step_0.output.field}
                ref = value[2:-1]  # Remove ${ and }
                parts = ref.split('.')

                result = results[parts[0]]
                for part in parts[1:]:
                    result = result[part]

                resolved[key] = result
            else:
                resolved[key] = value

        return resolved
```

---

## Tool Registry

### Tool Definition Schema
```json
{
  "name": "database_backup",
  "category": "database",
  "risk_level": "medium",
  "description": "Create a backup of a database",
  "llm_description": "Use this tool to create a backup of a PostgreSQL or MySQL database. Specify the database name and output path. The backup will be created in SQL format.",
  "parameters_schema": {
    "type": "object",
    "properties": {
      "database": {
        "type": "string",
        "description": "Name of the database to backup"
      },
      "output_path": {
        "type": "string",
        "description": "Path where backup file should be saved"
      },
      "compression": {
        "type": "boolean",
        "description": "Whether to compress the backup",
        "default": true
      }
    },
    "required": ["database", "output_path"]
  },
  "capabilities_required": [
    "DATABASE_READ",
    "BACKUP_CREATE",
    "FILE_WRITE"
  ],
  "rate_limit": {
    "max_calls_per_minute": 5,
    "max_calls_per_hour": 20
  },
  "timeout_seconds": 300,
  "retry_config": {
    "max_attempts": 3,
    "backoff_multiplier": 2,
    "initial_delay": 1
  }
}
```

### Tool Implementation
```python
from src.tools.base import BaseTool, ToolResult

class DatabaseBackupTool(BaseTool):
    """Tool for creating database backups"""

    async def execute(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ToolResult:
        """Execute database backup"""

        # Validate parameters
        self.validate_parameters(params)

        database = params['database']
        output_path = params['output_path']
        compression = params.get('compression', True)

        try:
            # Create backup
            backup_path = await self._create_backup(
                database,
                output_path,
                compression
            )

            # Verify backup
            is_valid = await self._verify_backup(backup_path)

            if not is_valid:
                raise ToolExecutionError("Backup verification failed")

            return ToolResult(
                success=True,
                output={
                    'backup_path': backup_path,
                    'size_bytes': os.path.getsize(backup_path),
                    'compressed': compression,
                    'timestamp': datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                details={'database': database, 'output_path': output_path}
            )
```

### Registering Tools
```python
# Register tool programmatically
from src.tools.tool_registry import ToolRegistry, ToolDefinition

registry = ToolRegistry()

tool_def = ToolDefinition(
    name="database_backup",
    category="database",
    risk_level="medium",
    description="Create database backup",
    parameters_schema={...},
    capabilities_required=[
        AgentCapability.DATABASE_READ,
        AgentCapability.BACKUP_CREATE
    ]
)

registry.register_tool(tool_def, DatabaseBackupTool())

# Or register from JSON file
registry.register_from_file('tools/database_backup.json')
```

---

## Safety & Security

### Risk Levels
```python
class RiskLevel(Enum):
    SAFE = "safe"          # Read-only, no side effects
    LOW = "low"            # Minimal impact, easily reversible
    MEDIUM = "medium"      # Moderate impact, reversible with effort
    HIGH = "high"          # Significant impact, difficult to reverse
    CRITICAL = "critical"  # Severe impact, potentially irreversible
```

### Risk Assessment
```python
def assess_operation_risk(operation: Dict[str, Any]) -> RiskLevel:
    """Assess risk level of an operation"""

    # Database write operations
    if operation['type'] == 'database_write':
        query = operation.get('query', '').upper()

        if 'DROP TABLE' in query or 'TRUNCATE' in query:
            return RiskLevel.CRITICAL
        elif 'DELETE' in query and 'WHERE' not in query:
            return RiskLevel.CRITICAL
        elif 'DELETE' in query or 'UPDATE' in query:
            return RiskLevel.HIGH
        elif 'INSERT' in query:
            return RiskLevel.MEDIUM

    # File operations
    elif operation['type'] == 'file_operation':
        if operation['action'] == 'delete':
            if operation.get('path', '').startswith('/'):
                return RiskLevel.CRITICAL
            return RiskLevel.HIGH
        elif operation['action'] == 'write':
            return RiskLevel.MEDIUM
        elif operation['action'] == 'read':
            return RiskLevel.SAFE

    # System commands
    elif operation['type'] == 'system_command':
        dangerous_commands = ['rm -rf', 'dd', 'mkfs', 'fdisk']
        command = operation.get('command', '')

        if any(cmd in command for cmd in dangerous_commands):
            return RiskLevel.CRITICAL
        return RiskLevel.HIGH

    return RiskLevel.LOW
```

### SQL Validation
```python
import re

class SQLValidator:
    """Validate SQL queries for safety"""

    DANGEROUS_PATTERNS = [
        r';\s*DROP\s+TABLE',
        r';\s*DROP\s+DATABASE',
        r';\s*DELETE\s+FROM',
        r';\s*TRUNCATE',
        r'--\s*.*',  # SQL comments
        r'/\*.*?\*/',  # Multi-line comments
        r'UNION\s+SELECT',
        r'xp_cmdshell',
        r'EXEC\s*\(',
        r'EXECUTE\s*\('
    ]

    def validate(self, sql: str) -> Dict[str, Any]:
        """Validate SQL query"""
        issues = []

        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                issues.append(f"Dangerous pattern detected: {pattern}")

        # Check for missing WHERE clause in DELETE/UPDATE
        if re.search(r'\b(DELETE|UPDATE)\b', sql, re.IGNORECASE):
            if not re.search(r'\bWHERE\b', sql, re.IGNORECASE):
                issues.append("DELETE/UPDATE without WHERE clause")

        # Check for proper parameterization
        if re.search(r"=\s*['\"]", sql):
            issues.append("Possible SQL injection risk - use parameters")

        return {
            'safe': len(issues) == 0,
            'issues': issues,
            'risk_level': 'critical' if issues else 'safe'
        }
```

### Approval Workflow
```python
class ApprovalManager:
    """Manage approval workflows"""

    async def request_approval(
        self,
        operation: Dict[str, Any],
        risk_assessment: Dict[str, Any]
    ) -> bool:
        """Request approval for high-risk operation"""

        # Create approval request
        request_id = str(uuid.uuid4())

        request = {
            'request_id': request_id,
            'operation': operation,
            'risk_assessment': risk_assessment,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }

        # Store request
        await self.store_request(request)

        # Send notification
        await self.notify_approvers(request)

        # Wait for approval (with timeout)
        timeout = self.config.approval_timeout
        approved = await self.wait_for_approval(request_id, timeout)

        # Log decision
        await self.log_approval_decision(request_id, approved)

        return approved

    async def wait_for_approval(
        self,
        request_id: str,
        timeout: int
    ) -> bool:
        """Wait for approval decision"""

        start_time = asyncio.get_event_loop().time()

        while True:
            # Check if approved
            request = await self.get_request(request_id)

            if request['status'] == 'approved':
                return True
            elif request['status'] == 'denied':
                return False

            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                # Timeout - deny by default
                await self.update_request_status(request_id, 'denied')
                return False

            # Wait before checking again
            await asyncio.sleep(1)
```

---

## Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'src'` | Python path not set | Run from project root: `python -m aishell` |
| `asyncio.TimeoutError` | Operation timeout | Increase timeout in config: `timeout: 60` |
| `ToolNotFoundError: Tool 'xyz' not found` | Tool not registered | Register tool: `registry.register_tool(...)` |
| `CheckpointNotFoundError` | Invalid checkpoint ID | Verify checkpoint exists: `list_checkpoints()` |
| `ValidationError: Invalid parameters` | Parameter type mismatch | Check tool schema and fix parameter types |
| `PermissionError: Access denied` | Insufficient file permissions | Check permissions: `chmod 644 file` |
| `DatabaseError: Connection refused` | Database not running | Start database: `systemctl start postgresql` |
| `LLMError: Rate limit exceeded` | Too many API calls | Implement rate limiting and backoff |
| `SecurityError: Unsafe operation` | Operation blocked by safety | Reduce risk or request approval |
| `ApprovalDeniedError` | Operation not approved | Modify operation or get approval |

### Debugging Tips
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('aishell')
logger.setLevel(logging.DEBUG)

# Log LLM prompts and responses
llm_manager.enable_debug_logging()

# Inspect agent state
agent_state = agent.get_state()
print(f"Agent state: {agent_state}")

# List checkpoints
checkpoints = await state_manager.list_checkpoints(task_id)
print(f"Available checkpoints: {checkpoints}")

# Test tool independently
tool = registry.get_tool('tool_name')
result = await tool.execute(params, context)
print(f"Tool result: {result}")

# Dry run mode
agent.set_dry_run(True)  # Execute without side effects
result = await agent.run(task)
```

---

## Performance Tips

### 1. Use Async Operations
```python
# ❌ SLOW: Sequential execution
result1 = await operation1()
result2 = await operation2()
result3 = await operation3()

# ✅ FAST: Parallel execution
results = await asyncio.gather(
    operation1(),
    operation2(),
    operation3()
)
```

### 2. Implement Caching
```python
from functools import lru_cache
import asyncio

# Cache LLM prompts
@lru_cache(maxsize=100)
def build_prompt(task_type: str) -> str:
    return template.render(task_type=task_type)

# Cache async results
class AsyncLRUCache:
    def __init__(self, maxsize=128):
        self.cache = {}
        self.maxsize = maxsize

    async def get_or_compute(self, key, compute_fn):
        if key in self.cache:
            return self.cache[key]

        result = await compute_fn()
        self.cache[key] = result

        if len(self.cache) > self.maxsize:
            # Remove oldest entry
            self.cache.pop(next(iter(self.cache)))

        return result
```

### 3. Use Connection Pooling
```python
# Database connection pool
pool = await asyncpg.create_pool(
    dsn=connection_string,
    min_size=10,
    max_size=20,
    command_timeout=60
)

# Reuse connections
async with pool.acquire() as conn:
    result = await conn.fetch(query)
```

### 4. Batch Operations
```python
# ❌ SLOW: One-by-one inserts
for record in records:
    await db.execute('INSERT INTO table VALUES ($1, $2)', record)

# ✅ FAST: Batch insert
await db.executemany(
    'INSERT INTO table VALUES ($1, $2)',
    records
)
```

### 5. Optimize LLM Calls
```python
# Use cheaper models for simple tasks
if task.complexity == 'simple':
    config.llm_model = 'gpt-3.5-turbo'  # Faster, cheaper
else:
    config.llm_model = 'gpt-4'  # More capable

# Use streaming for faster perceived response
async for chunk in llm_manager.stream_generate(prompt):
    process_chunk(chunk)

# Reduce token usage
config.max_tokens = 1000  # Instead of 2000
config.temperature = 0.5  # More focused responses
```

---

## Security Checklist

### Before Deployment
- [ ] All credentials stored in encrypted vault
- [ ] No hardcoded API keys or passwords
- [ ] SQL injection validation enabled
- [ ] Approval workflows configured for HIGH/CRITICAL operations
- [ ] Audit logging enabled and monitored
- [ ] File system permissions restricted
- [ ] Database connections use least privilege
- [ ] Input validation on all user inputs
- [ ] Rate limiting enabled on API endpoints
- [ ] Error messages don't leak sensitive info

### Configuration Security
- [ ] Config files have restricted permissions (600)
- [ ] Environment variables used for secrets
- [ ] TLS/SSL enabled for database connections
- [ ] API keys rotated regularly
- [ ] Backup encryption enabled
- [ ] Log files access controlled
- [ ] Debug mode disabled in production

### Runtime Security
- [ ] Operations logged to audit trail
- [ ] High-risk operations require approval
- [ ] Failed authentication attempts logged
- [ ] Resource limits enforced (CPU, memory, disk)
- [ ] Timeout protection on all async operations
- [ ] Graceful error handling (no crashes)
- [ ] Regular security updates applied

### Monitoring
- [ ] Failed operations alerted
- [ ] Unusual activity detected
- [ ] Performance metrics tracked
- [ ] Audit logs reviewed regularly
- [ ] Backup integrity verified
- [ ] Health checks passing
- [ ] Dependencies scanned for vulnerabilities

---

## Quick Tips

### General
- Always run from project root: `python -m aishell`
- Use virtual environment to avoid dependency conflicts
- Keep configuration in `~/.aishell/config.yaml`
- Enable debug logging when troubleshooting: `--debug`

### Agent Development
- Start with small, simple agents
- Test each step independently before full workflow
- Use checkpoints for long-running tasks
- Implement proper error handling and recovery
- Log extensively for debugging

### Tool Registry
- Validate tool schemas before registration
- Use appropriate risk levels
- Provide clear LLM descriptions
- Implement rate limiting for expensive operations
- Test tools independently before agent integration

### Safety
- Always validate SQL queries
- Require approval for destructive operations
- Log all high-risk operations
- Use dry-run mode for testing
- Implement rollback capabilities

### Performance
- Use async/await for I/O operations
- Enable connection pooling
- Cache frequent computations
- Batch database operations
- Monitor and optimize slow operations

---

**Need more help?** Check the [Complete Guide](./HANDS_ON_COMPLETE_GUIDE.md) or [open an issue](https://github.com/dimensigon/aishell/issues).

*Last updated: October 2025 | AIShell v2.0.0*
