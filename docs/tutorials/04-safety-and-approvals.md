# Tutorial 04: Safety and Approval System

## Table of Contents
1. [Introduction](#introduction)
2. [Safety Levels](#safety-levels)
3. [Approval Requirements](#approval-requirements)
4. [Risk Assessment](#risk-assessment)
5. [Interactive Approvals](#interactive-approvals)
6. [Custom Approval Callbacks](#custom-approval-callbacks)
7. [Destructive Operations](#destructive-operations)
8. [SQL Risk Analysis](#sql-risk-analysis)
9. [Audit Trail](#audit-trail)
10. [Safety Configuration](#safety-configuration)
11. [Testing Safety Logic](#testing-safety-logic)
12. [Production Deployment](#production-deployment)

---

## 1. Introduction

### Why Safety Matters in Autonomous Agents

When AI agents autonomously execute database operations, a robust safety system is critical to prevent:

- **Data Loss**: Accidental deletion or truncation of tables
- **Service Disruption**: Schema changes that break applications
- **Security Breaches**: Unauthorized access or privilege escalation
- **Compliance Violations**: Operations that violate regulatory requirements
- **Performance Issues**: Operations that lock tables or cause downtime

The AIShell Safety and Approval System provides **multi-layer protection** with:

1. **Risk Assessment**: Automatic evaluation of operation risk levels
2. **Approval Workflows**: Human-in-the-loop approval for risky operations
3. **SQL Analysis**: Deep inspection of SQL queries for dangerous patterns
4. **Audit Logging**: Complete trail of all approval decisions
5. **Safety Constraints**: Configurable rules and policies

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  Agent Workflow                     │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   Safety Controller   │
         └───────────┬───────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌──────────┐
   │  Risk   │  │   SQL   │  │ Approval │
   │Analyzer │  │Analyzer │  │  System  │
   └─────────┘  └─────────┘  └──────────┘
                     │
                     ▼
            ┌─────────────────┐
            │  Audit Trail    │
            └─────────────────┘
```

---

## 2. Safety Levels

AIShell supports three safety levels that control how strictly operations are validated:

### 2.1 Safety Level: STRICT

**Use Case**: Production databases, critical systems

**Behavior**:
- ✅ Requires approval for HIGH and CRITICAL risk operations
- ✅ Blocks destructive operations without multi-party approval
- ✅ Enforces all safety constraints
- ✅ Comprehensive SQL risk analysis

**Example Configuration**:
```python
from src.agents.base import AgentConfig

strict_config = AgentConfig(
    agent_id="backup_prod_001",
    agent_type="backup",
    capabilities=[...],
    llm_config={...},
    safety_level='strict',  # 🔒 Strictest mode
    max_retries=3,
    timeout_seconds=300
)
```

### 2.2 Safety Level: MODERATE

**Use Case**: Staging environments, development databases with real data

**Behavior**:
- ⚠️ Requires approval only for CRITICAL risk operations
- ⚠️ Optional approval for HIGH risk operations
- ✅ SQL risk analysis for writes and DDL
- ✅ Basic safety constraints

**Example Configuration**:
```python
moderate_config = AgentConfig(
    agent_id="migration_staging_001",
    agent_type="migration",
    capabilities=[...],
    llm_config={...},
    safety_level='moderate',  # ⚠️ Balanced mode
    max_retries=3,
    timeout_seconds=300
)
```

### 2.3 Safety Level: PERMISSIVE

**Use Case**: Local development, test databases, sandboxed environments

**Behavior**:
- 📝 Only requires approval when explicitly set on tool
- 📝 Minimal SQL validation
- 📝 Basic audit logging
- ⚠️ **Not recommended for production**

**Example Configuration**:
```python
permissive_config = AgentConfig(
    agent_id="dev_test_001",
    agent_type="optimizer",
    capabilities=[...],
    llm_config={...},
    safety_level='permissive',  # 📝 Least restrictive
    max_retries=3,
    timeout_seconds=300
)
```

### 2.4 Comparing Safety Levels

| Operation Type | Strict | Moderate | Permissive |
|---------------|--------|----------|------------|
| SELECT queries | ✅ Auto | ✅ Auto | ✅ Auto |
| INSERT/UPDATE with WHERE | 🔒 Approval | ✅ Auto | ✅ Auto |
| UPDATE without WHERE | 🔒 Approval | 🔒 Approval | ✅ Auto |
| DROP/TRUNCATE | 🔒 Multi-Party | 🔒 Approval | 🔒 Approval |
| Schema migrations | 🔒 Approval | 🔒 Approval | ⚠️ Optional |
| Index creation | 🔒 Approval | ⚠️ Optional | ✅ Auto |
| Backup operations | ✅ Auto | ✅ Auto | ✅ Auto |
| Restore operations | 🔒 Approval | 🔒 Approval | 🔒 Approval |

---

## 3. Approval Requirements

The system uses four levels of approval requirements:

### 3.1 ApprovalRequirement.NONE

**Description**: No approval needed, operation is safe to execute automatically

**Triggered For**:
- Read-only SELECT queries
- SHOW/DESCRIBE commands
- Schema analysis
- Backup creation
- Query analysis

**Example**:
```python
# This operation requires no approval
validation = {
    'safe': True,
    'risk_level': 'safe',
    'requires_approval': False,
    'approval_requirement': ApprovalRequirement.NONE,
    'risks': [],
    'mitigations': []
}
```

### 3.2 ApprovalRequirement.OPTIONAL

**Description**: Approval is recommended but not required

**Triggered For**:
- HIGH risk operations in moderate safety mode
- Index creation on small tables
- Data updates with clear WHERE clauses

**Example**:
```python
# In moderate mode, HIGH risk operations are optional approval
if agent_config.safety_level == 'moderate':
    if tool.risk_level == ToolRiskLevel.HIGH:
        validation['approval_requirement'] = ApprovalRequirement.OPTIONAL
```

### 3.3 ApprovalRequirement.REQUIRED

**Description**: Approval must be obtained before execution

**Triggered For**:
- CRITICAL risk operations
- DDL operations (ALTER, CREATE, DROP)
- Data modifications without WHERE clause
- Restore operations
- Production database operations

**Example**:
```python
# DDL operations always require approval
if tool.category == ToolCategory.DATABASE_DDL:
    validation['requires_approval'] = True
    validation['approval_requirement'] = ApprovalRequirement.REQUIRED
```

### 3.4 ApprovalRequirement.MULTI_PARTY

**Description**: Requires multiple approvals (future enhancement)

**Triggered For**:
- Destructive operations (DROP, TRUNCATE)
- Backup deletion
- Database restoration (overwrites current state)
- Production data deletion

**Example**:
```python
# Destructive operations require multi-party approval
if self._is_destructive_operation(step):
    validation['requires_approval'] = True
    validation['approval_requirement'] = ApprovalRequirement.MULTI_PARTY
    validation['risks'].append("Potentially irreversible destructive operation")
    validation['mitigations'].append("Multi-party approval required")
```

---

## 4. Risk Assessment

### 4.1 Risk Levels

The system classifies operations into five risk levels:

#### **SAFE** (Green)
- Read-only operations
- No side effects
- Examples: SELECT, SHOW, DESCRIBE, EXPLAIN

#### **LOW** (Blue)
- Minor modifications
- Easy to reverse
- Examples: INSERT, Full backup creation

#### **MEDIUM** (Yellow)
- Significant modifications
- Reversible with effort
- Examples: UPDATE with WHERE, CREATE INDEX, ALTER TABLE ADD COLUMN

#### **HIGH** (Orange)
- Dangerous operations
- Difficult to reverse
- Examples: DELETE without WHERE, UPDATE without WHERE, DROP INDEX

#### **CRITICAL** (Red)
- Destructive operations
- Irreversible or very difficult to reverse
- Examples: DROP TABLE, TRUNCATE, DROP DATABASE

### 4.2 Risk Assessment Process

The `SafetyController.validate_step()` method performs comprehensive risk assessment:

```python
def validate_step(self, step: Dict[str, Any],
                 agent_config: AgentConfig) -> Dict[str, Any]:
    """
    Multi-stage risk assessment:
    1. Base tool risk level
    2. Safety level enforcement
    3. Category-specific validations
    4. SQL risk analysis
    5. Destructive operation detection
    """

    # Stage 1: Get base risk from tool definition
    tool = step.get('tool_definition')
    validation['risk_level'] = tool.risk_level.value

    # Stage 2: Apply safety level rules
    if agent_config.safety_level == 'strict':
        if tool.risk_level in [ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL]:
            validation['requires_approval'] = True

    # Stage 3: Category-specific rules
    if tool.category == ToolCategory.DATABASE_WRITE:
        validation['risks'].append("Data modification operation")

    # Stage 4: SQL risk analysis
    if 'sql' in tool_params:
        sql_analysis = self.risk_analyzer.analyze(sql)
        if sql_analysis['risk_level'] in ['HIGH', 'CRITICAL']:
            validation['requires_approval'] = True

    # Stage 5: Destructive operation check
    if self._is_destructive_operation(step):
        validation['approval_requirement'] = ApprovalRequirement.MULTI_PARTY

    return validation
```

### 4.3 Practical Example: Risk Assessment Flow

```python
# Example: Assessing a migration operation
from src.agents.safety.controller import SafetyController
from src.database.risk_analyzer import SQLRiskAnalyzer

# Initialize components
risk_analyzer = SQLRiskAnalyzer()
safety_controller = SafetyController(risk_analyzer)

# Define the operation
step = {
    'tool': 'execute_migration',
    'params': {
        'migration_sql': 'ALTER TABLE users ADD COLUMN phone VARCHAR(20)',
        'rollback_sql': 'ALTER TABLE users DROP COLUMN phone'
    },
    'tool_definition': migration_tool  # Tool definition from registry
}

# Validate safety
validation = safety_controller.validate_step(step, agent_config)

print(f"Risk Level: {validation['risk_level']}")
print(f"Requires Approval: {validation['requires_approval']}")
print(f"Approval Type: {validation['approval_requirement']}")
print(f"Risks: {validation['risks']}")
print(f"Mitigations: {validation['mitigations']}")
```

**Output**:
```
Risk Level: critical
Requires Approval: True
Approval Type: required
Risks: ['Schema modification operation', 'DDL operation requires approval']
Mitigations: ['Rollback script generated', 'Backup created before execution']
```

---

## 5. Interactive Approvals

### 5.1 CLI Approval Workflow

When an operation requires approval, the SafetyController displays a comprehensive interactive prompt:

```
======================================================================
⚠️  APPROVAL REQUIRED FOR AGENT OPERATION
======================================================================

🔧 Tool: execute_migration
⚡ Risk Level: CRITICAL
🛡️  Approval Requirement: required

📋 Parameters:
  • migration_sql: ALTER TABLE users ADD COLUMN phone VARCHAR(20)
  • rollback_sql: ALTER TABLE users DROP COLUMN phone

🔍 SQL Analysis:
  • SQL Risk Level: MEDIUM
  • Requires Confirmation: False
  • Issues: []

⚠️  Identified Risks:
  • Schema modification operation
  • DDL operation requires approval

✅ Available Mitigations:
  • Rollback script generated
  • Backup created before execution

======================================================================

⚡ This operation requires your approval to proceed.
Approve this operation? (yes/no):
```

### 5.2 Approval Response Handling

**Approval Granted**:
```python
# User responds: yes
approval = {
    'approved': True,
    'reason': 'User approved via interactive prompt',
    'approver': 'user',
    'timestamp': '2025-10-05T10:30:00.000Z',
    'conditions': []
}
```

**Approval Rejected**:
```python
# User responds: no
# System asks: Rejection reason (optional): Schema change too risky
approval = {
    'approved': False,
    'reason': 'Schema change too risky',
    'approver': 'user',
    'timestamp': '2025-10-05T10:30:15.000Z',
    'conditions': []
}
```

### 5.3 Using Interactive Approval in Agents

```python
from src.agents.safety.controller import SafetyController

async def execute_with_approval(agent, step):
    """Execute step with safety approval"""

    # Validate step
    validation = agent.validate_safety(step)

    if validation['requires_approval']:
        # Request interactive approval
        approval = await safety_controller.request_approval(
            step=step,
            validation=validation,
            approval_callback=None  # None = use interactive CLI
        )

        if not approval['approved']:
            raise Exception(f"Operation rejected: {approval['reason']}")

    # Execute the step
    result = await agent.execute_step(step)
    return result
```

---

## 6. Custom Approval Callbacks

### 6.1 Implementing Custom Approval Logic

For automated or programmatic approvals, implement custom approval callbacks:

```python
async def auto_approve_backups(approval_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Custom approval callback that auto-approves backup operations
    """
    step = approval_request['step']
    validation = approval_request['validation']

    # Auto-approve if it's a backup operation
    if step['tool'] in ['backup_database_full', 'backup_database_incremental']:
        return {
            'approved': True,
            'reason': 'Backup operations auto-approved by policy',
            'approver': 'automated_policy',
            'timestamp': datetime.utcnow().isoformat(),
            'conditions': ['Backup verified after creation']
        }

    # Reject all other operations
    return {
        'approved': False,
        'reason': 'Only backup operations are auto-approved',
        'approver': 'automated_policy',
        'timestamp': datetime.utcnow().isoformat(),
        'conditions': []
    }
```

### 6.2 Time-Based Approval Policy

```python
async def production_hours_approval(approval_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Approve CRITICAL operations only during maintenance windows
    """
    validation = approval_request['validation']
    current_hour = datetime.now().hour

    # Maintenance window: 2 AM - 6 AM
    maintenance_hours = [2, 3, 4, 5]

    if validation['risk_level'] == 'critical':
        if current_hour in maintenance_hours:
            return {
                'approved': True,
                'reason': f'Approved during maintenance window (hour {current_hour})',
                'approver': 'time_based_policy',
                'timestamp': datetime.utcnow().isoformat(),
                'conditions': ['Executed during maintenance window']
            }
        else:
            return {
                'approved': False,
                'reason': f'Critical operations only allowed during maintenance (2-6 AM), current hour: {current_hour}',
                'approver': 'time_based_policy',
                'timestamp': datetime.utcnow().isoformat(),
                'conditions': []
            }

    # Non-critical operations always approved
    return {
        'approved': True,
        'reason': 'Non-critical operation approved',
        'approver': 'time_based_policy',
        'timestamp': datetime.utcnow().isoformat(),
        'conditions': []
    }
```

### 6.3 Multi-Approver Callback

```python
class MultiApproverCallback:
    """Requires approval from multiple users"""

    def __init__(self, required_approvers: List[str]):
        self.required_approvers = required_approvers
        self.approvals: Dict[str, bool] = {}

    async def __call__(self, approval_request: Dict[str, Any]) -> Dict[str, Any]:
        """Request approval from multiple users"""
        step = approval_request['step']

        print(f"\n🔒 MULTI-PARTY APPROVAL REQUIRED")
        print(f"Operation: {step['tool']}")
        print(f"Required approvers: {', '.join(self.required_approvers)}")
        print(f"Current approvals: {sum(self.approvals.values())}/{len(self.required_approvers)}\n")

        for approver in self.required_approvers:
            if approver not in self.approvals:
                response = input(f"Approval from {approver} (yes/no): ").strip().lower()
                self.approvals[approver] = response in ['yes', 'y']

        # Check if all approvers approved
        if all(self.approvals.values()):
            return {
                'approved': True,
                'reason': f'Approved by all required parties: {", ".join(self.required_approvers)}',
                'approver': 'multi_party',
                'timestamp': datetime.utcnow().isoformat(),
                'conditions': [f'Approved by: {", ".join(self.required_approvers)}']
            }
        else:
            rejectors = [name for name, approved in self.approvals.items() if not approved]
            return {
                'approved': False,
                'reason': f'Rejected by: {", ".join(rejectors)}',
                'approver': 'multi_party',
                'timestamp': datetime.utcnow().isoformat(),
                'conditions': []
            }

# Usage
multi_approver = MultiApproverCallback(['admin', 'dba', 'security_lead'])
approval = await safety_controller.request_approval(
    step=step,
    validation=validation,
    approval_callback=multi_approver
)
```

### 6.4 Slack/Teams Integration Callback

```python
import aiohttp

async def slack_approval_callback(approval_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send approval request to Slack and wait for response
    """
    step = approval_request['step']
    validation = approval_request['validation']

    # Create Slack message
    slack_message = {
        "text": "⚠️ Database Operation Approval Required",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Tool:* {step['tool']}\n*Risk Level:* {validation['risk_level']}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Risks:*\n{chr(10).join(validation['risks'])}"},
                    {"type": "mrkdwn", "text": f"*Mitigations:*\n{chr(10).join(validation['mitigations'])}"}
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve"},
                        "style": "primary",
                        "value": "approve"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Reject"},
                        "style": "danger",
                        "value": "reject"
                    }
                ]
            }
        ]
    }

    # Send to Slack
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'https://slack.com/api/chat.postMessage',
            json=slack_message,
            headers={'Authorization': f'Bearer {SLACK_TOKEN}'}
        ) as response:
            message_data = await response.json()

    # Wait for response (implement webhook handler separately)
    # This is a simplified example
    response = await wait_for_slack_response(message_data['ts'])

    return {
        'approved': response['action'] == 'approve',
        'reason': response.get('reason', 'User response via Slack'),
        'approver': response['user'],
        'timestamp': datetime.utcnow().isoformat(),
        'conditions': []
    }
```

---

## 7. Destructive Operations

### 7.1 What Are Destructive Operations?

Destructive operations are those that may result in **irreversible data loss** or **system changes**:

**Destructive Tools**:
- `execute_migration` - Schema changes
- `drop_table` - Deletes entire table
- `drop_database` - Deletes entire database
- `truncate_table` - Removes all rows
- `delete_backup` - Removes backup files
- `restore_backup` - Overwrites current state
- `drop_index` - Removes index
- `drop_schema` - Removes schema

### 7.2 Destructive Pattern Detection

The system detects destructive operations through:

1. **Tool Name Matching**:
```python
def _is_destructive_operation(self, step: Dict[str, Any]) -> bool:
    destructive_tools = [
        'execute_migration',
        'drop_table',
        'drop_database',
        'truncate_table',
        'delete_backup',
        'restore_backup',
        'drop_index',
        'drop_schema'
    ]

    tool_name = step.get('tool', '')
    if tool_name in destructive_tools:
        return True
```

2. **SQL Content Analysis**:
```python
    # Check SQL content for destructive patterns
    params = step.get('params', {})
    sql_content = params.get('sql') or params.get('migration_sql') or ''

    if sql_content:
        destructive_patterns = ['DROP', 'TRUNCATE', 'DELETE FROM']
        sql_upper = sql_content.upper()
        for pattern in destructive_patterns:
            if pattern in sql_upper:
                return True

    return False
```

### 7.3 Handling Destructive Operations

When a destructive operation is detected:

```python
if self._is_destructive_operation(step):
    validation['requires_approval'] = True
    validation['approval_requirement'] = ApprovalRequirement.MULTI_PARTY
    validation['risks'].append("Potentially irreversible destructive operation")
    validation['mitigations'].append("Multi-party approval required")
```

### 7.4 Safeguards for Destructive Operations

**Safeguard 1: Automatic Backups**
```python
# Always backup before destructive migration
plan = [
    {
        'tool': 'backup_before_migration',
        'params': {'database': task.database_config['database']}
    },
    {
        'tool': 'execute_migration',  # Destructive operation
        'params': {
            'migration_sql': '${step_0.output.migration_sql}',
            'rollback_sql': '${step_0.output.rollback_sql}'
        }
    }
]
```

**Safeguard 2: Rollback Scripts**
```python
# Generate rollback before execution
{
    'tool': 'create_rollback',
    'params': {
        'migration_sql': migration_sql,
        'current_schema': current_schema
    }
}
```

**Safeguard 3: Dry-Run Mode**
```python
# Test migration without execution
{
    'tool': 'execute_migration',
    'params': {
        'migration_sql': sql,
        'rollback_sql': rollback,
        'dry_run': True  # Test only, don't execute
    }
}
```

---

## 8. SQL Risk Analysis

### 8.1 SQL Risk Analyzer Architecture

The `SQLRiskAnalyzer` performs deep analysis of SQL queries:

```python
class SQLRiskAnalyzer:
    """Analyzes SQL queries for potential risks"""

    RISK_PATTERNS = {
        # CRITICAL - Destructive operations
        r'\bDROP\s+(TABLE|DATABASE|SCHEMA)\b': RiskLevel.CRITICAL,
        r'\bTRUNCATE\s+TABLE\b': RiskLevel.CRITICAL,

        # HIGH - Dangerous operations without safety checks
        r'\bUPDATE\s+(?!.*\bWHERE\b)': RiskLevel.HIGH,
        r'\bDELETE\s+FROM\s+(?!.*\bWHERE\b)': RiskLevel.HIGH,

        # MEDIUM - Operations with conditions
        r'\bUPDATE\s+.*\bWHERE\b': RiskLevel.MEDIUM,
        r'\bDELETE\s+FROM\s+.*\bWHERE\b': RiskLevel.MEDIUM,
        r'\bALTER\s+TABLE\b': RiskLevel.MEDIUM,

        # LOW - Read operations
        r'\bSELECT\s+': RiskLevel.LOW,
    }
```

### 8.2 Risk Analysis Process

```python
def analyze(self, sql: str) -> Dict[str, any]:
    """
    Comprehensive SQL risk analysis
    Returns:
        - risk_level: LOW/MEDIUM/HIGH/CRITICAL
        - requires_confirmation: bool
        - warnings: List of warnings
        - issues: List of potential issues
        - safe_to_execute: bool
    """
    risk_level = self._detect_risk_level(sql)
    warnings = self._generate_warnings(sql, risk_level)
    issues = self._check_common_issues(sql)

    return {
        'risk_level': risk_level.value,
        'requires_confirmation': risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL],
        'warnings': warnings,
        'issues': issues,
        'sql': sql,
        'safe_to_execute': risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM],
    }
```

### 8.3 SQL Analysis Examples

**Example 1: Safe Query**
```python
sql = "SELECT * FROM users WHERE created_at > '2024-01-01'"
analysis = risk_analyzer.analyze(sql)

# Result:
{
    'risk_level': 'LOW',
    'requires_confirmation': False,
    'warnings': [],
    'issues': ['SELECT * may impact performance - consider specifying columns'],
    'safe_to_execute': True
}
```

**Example 2: Dangerous Query (No WHERE)**
```python
sql = "DELETE FROM users"
analysis = risk_analyzer.analyze(sql)

# Result:
{
    'risk_level': 'HIGH',
    'requires_confirmation': True,
    'warnings': [
        '⚠️  HIGH RISK: DELETE without WHERE clause will remove ALL rows',
        '⚠️  Consider adding a WHERE clause to limit scope'
    ],
    'issues': [],
    'safe_to_execute': False
}
```

**Example 3: Critical Operation**
```python
sql = "DROP TABLE users"
analysis = risk_analyzer.analyze(sql)

# Result:
{
    'risk_level': 'CRITICAL',
    'requires_confirmation': True,
    'warnings': [
        '⚠️  CRITICAL: This operation will permanently delete data',
        '⚠️  This action cannot be undone'
    ],
    'issues': [],
    'safe_to_execute': False
}
```

### 8.4 Common SQL Issues Detection

The analyzer checks for common SQL anti-patterns:

```python
def _check_common_issues(self, sql: str) -> List[str]:
    issues = []

    # SQL Injection patterns
    if re.search(r'[\'\"]\s*OR\s+[\'\"]*\s*1\s*=\s*1', sql, re.IGNORECASE):
        issues.append("Potential SQL injection pattern detected")

    # Missing semicolon
    if not sql.rstrip().endswith(';'):
        issues.append("Query does not end with semicolon")

    # Multiple statements (security risk)
    if sql.count(';') > 1:
        issues.append("Multiple statements detected - ensure this is intentional")

    # SELECT *
    if re.search(r'\bSELECT\s+\*', sql, re.IGNORECASE):
        issues.append("SELECT * may impact performance - consider specifying columns")

    return issues
```

### 8.5 Integration with Safety Controller

The SQL analysis is automatically integrated into the safety validation:

```python
# In SafetyController.validate_step()
if tool.category == ToolCategory.DATABASE_WRITE:
    if 'sql' in tool_params or 'query' in tool_params:
        sql = tool_params.get('sql') or tool_params.get('query')
        sql_analysis = self.risk_analyzer.analyze(sql)
        validation['sql_analysis'] = sql_analysis

        # Upgrade risk level if SQL analysis indicates higher risk
        if sql_analysis['risk_level'] in ['HIGH', 'CRITICAL']:
            validation['requires_approval'] = True
            validation['risks'].extend(sql_analysis.get('warnings', []))
```

---

## 9. Audit Trail

### 9.1 Approval History Tracking

Every approval request and decision is logged to the audit trail:

```python
class SafetyController:
    def __init__(self, risk_analyzer: SQLRiskAnalyzer):
        self.risk_analyzer = risk_analyzer
        self.approval_history: List[Dict[str, Any]] = []

    async def request_approval(self, step, validation, approval_callback=None):
        # ... approval logic ...

        # Log to audit trail
        self.approval_history.append({
            'request': approval_request,
            'approval': approval,
            'decision_timestamp': datetime.utcnow().isoformat()
        })

        return approval
```

### 9.2 Approval History Structure

Each audit entry contains:

```python
{
    'request': {
        'step': {
            'tool': 'execute_migration',
            'params': {...},
            'tool_definition': {...}
        },
        'validation': {
            'risk_level': 'critical',
            'requires_approval': True,
            'approval_requirement': 'required',
            'risks': [...],
            'mitigations': [...]
        },
        'timestamp': '2025-10-05T10:30:00.000Z'
    },
    'approval': {
        'approved': True,
        'reason': 'User approved via interactive prompt',
        'approver': 'user',
        'timestamp': '2025-10-05T10:30:45.000Z',
        'conditions': []
    },
    'decision_timestamp': '2025-10-05T10:30:45.000Z'
}
```

### 9.3 Querying Approval History

**Get All Approvals**:
```python
history = safety_controller.get_approval_history()
print(f"Total approvals: {len(history)}")
```

**Get Recent Approvals**:
```python
recent = safety_controller.get_approval_history(limit=10)
for entry in recent:
    print(f"Tool: {entry['request']['step']['tool']}")
    print(f"Approved: {entry['approval']['approved']}")
    print(f"By: {entry['approval']['approver']}")
    print(f"At: {entry['decision_timestamp']}")
    print("---")
```

**Get Only Approved Operations**:
```python
approved = safety_controller.get_approval_history(approved_only=True)
print(f"Approved operations: {len(approved)}")
```

### 9.4 Audit Trail Analysis

```python
def analyze_approval_patterns(safety_controller):
    """Analyze approval patterns for insights"""
    history = safety_controller.get_approval_history()

    # Calculate approval rate
    total = len(history)
    approved = len([h for h in history if h['approval']['approved']])
    approval_rate = (approved / total * 100) if total > 0 else 0

    # Group by approver
    by_approver = {}
    for entry in history:
        approver = entry['approval']['approver']
        by_approver[approver] = by_approver.get(approver, 0) + 1

    # Group by risk level
    by_risk = {}
    for entry in history:
        risk = entry['request']['validation']['risk_level']
        by_risk[risk] = by_risk.get(risk, 0) + 1

    print(f"📊 Approval Analytics")
    print(f"Total Requests: {total}")
    print(f"Approval Rate: {approval_rate:.1f}%")
    print(f"\nBy Approver: {by_approver}")
    print(f"By Risk Level: {by_risk}")
```

### 9.5 Compliance Reporting

```python
def generate_compliance_report(safety_controller, start_date, end_date):
    """Generate compliance report for audit"""
    history = safety_controller.get_approval_history()

    # Filter by date range
    filtered = [
        h for h in history
        if start_date <= h['decision_timestamp'] <= end_date
    ]

    report = {
        'period': {
            'start': start_date,
            'end': end_date
        },
        'summary': {
            'total_operations': len(filtered),
            'approved': len([h for h in filtered if h['approval']['approved']]),
            'rejected': len([h for h in filtered if not h['approval']['approved']]),
        },
        'critical_operations': [
            h for h in filtered
            if h['request']['validation']['risk_level'] == 'critical'
        ],
        'approvers': list(set([h['approval']['approver'] for h in filtered]))
    }

    return report
```

---

## 10. Safety Configuration

### 10.1 Agent-Level Configuration

Configure safety settings per agent:

```python
# config/agents.yaml

agents:
  migration:
    safety_level: strict
    max_execution_time: 1800

    default_config:
      create_backup: true
      generate_rollback: true
      dry_run_first: true

    safety_constraints:
      - type: max_table_size
        max_rows: 1000000

      - type: production_hours
        allowed_hours: [0, 1, 2, 3, 4, 5]

      - type: backup_required
        before_operations:
          - execute_migration
          - drop_table
```

### 10.2 Environment-Specific Configuration

```python
# config/environments/production.yaml

safety:
  default_level: strict

  approval_requirements:
    critical_operations: multi_party
    production_database: required
    large_tables: required

  constraints:
    - type: production_hours
      allowed_hours: [2, 3, 4, 5]
      applicable_to: [migration, restore]

    - type: max_table_size
      max_rows: 5000000
      action: require_approval

    - type: backup_before
      operations: [migration, restore, drop_table]
      retention_days: 30

# config/environments/staging.yaml

safety:
  default_level: moderate

  approval_requirements:
    critical_operations: required
    production_database: none

  constraints:
    - type: max_table_size
      max_rows: 10000000
```

### 10.3 Dynamic Configuration

```python
class DynamicSafetyConfig:
    """Dynamically adjust safety based on context"""

    def get_safety_level(self, context: Dict[str, Any]) -> str:
        """Determine safety level based on context"""

        # Production database = strict
        if context.get('database') == 'production':
            return 'strict'

        # Large tables = strict
        if context.get('table_size', 0) > 1_000_000:
            return 'strict'

        # During business hours = strict
        if 9 <= datetime.now().hour <= 17:
            return 'strict'

        # Default to moderate
        return 'moderate'

    def get_approval_callback(self, context: Dict[str, Any]):
        """Select appropriate approval callback"""

        # Critical operations require multi-party
        if context.get('risk_level') == 'critical':
            return MultiApproverCallback(['dba', 'security', 'manager'])

        # Production requires Slack approval
        if context.get('database') == 'production':
            return slack_approval_callback

        # Default to interactive
        return None
```

### 10.4 Best Practices for Configuration

1. **Principle of Least Privilege**
   - Start with `strict` and relax only as needed
   - Never use `permissive` in production

2. **Defense in Depth**
   - Combine multiple safety mechanisms
   - Don't rely on a single safeguard

3. **Separation of Environments**
   - Different configs for dev/staging/prod
   - Stricter rules for production

4. **Audit Everything**
   - Log all operations, even approved ones
   - Regular review of approval patterns

5. **Time-Based Controls**
   - Restrict critical operations to maintenance windows
   - Auto-reject during business hours

---

## 11. Testing Safety Logic

### 11.1 Unit Tests for Safety Controller

```python
# tests/test_safety_controller.py

import pytest
from src.agents.safety.controller import SafetyController, ApprovalRequirement
from src.database.risk_analyzer import SQLRiskAnalyzer
from src.agents.base import AgentConfig, AgentCapability
from src.agents.tools.registry import ToolDefinition, ToolCategory, ToolRiskLevel

@pytest.fixture
def safety_controller():
    risk_analyzer = SQLRiskAnalyzer()
    return SafetyController(risk_analyzer)

@pytest.fixture
def strict_agent_config():
    return AgentConfig(
        agent_id="test_agent",
        agent_type="migration",
        capabilities=[AgentCapability.DATABASE_DDL],
        llm_config={},
        safety_level='strict',
        max_retries=3,
        timeout_seconds=300
    )

class TestSafetyValidation:

    def test_safe_operation_no_approval(self, safety_controller, strict_agent_config):
        """Test that safe operations don't require approval"""
        tool = ToolDefinition(
            name="analyze_schema",
            description="Analyze database schema",
            category=ToolCategory.ANALYSIS,
            risk_level=ToolRiskLevel.SAFE,
            required_capabilities=[AgentCapability.DATABASE_READ],
            parameters_schema={},
            returns_schema={},
            implementation=lambda p, c: {},
            requires_approval=False,
            max_execution_time=60,
            examples=[]
        )

        step = {
            'tool': 'analyze_schema',
            'params': {'database': 'test'},
            'tool_definition': tool
        }

        validation = safety_controller.validate_step(step, strict_agent_config)

        assert validation['safe'] == True
        assert validation['requires_approval'] == False
        assert validation['approval_requirement'] == ApprovalRequirement.NONE

    def test_critical_operation_requires_approval(self, safety_controller, strict_agent_config):
        """Test that critical operations require approval in strict mode"""
        tool = ToolDefinition(
            name="execute_migration",
            description="Execute schema migration",
            category=ToolCategory.DATABASE_DDL,
            risk_level=ToolRiskLevel.CRITICAL,
            required_capabilities=[AgentCapability.DATABASE_DDL],
            parameters_schema={},
            returns_schema={},
            implementation=lambda p, c: {},
            requires_approval=True,
            max_execution_time=1800,
            examples=[]
        )

        step = {
            'tool': 'execute_migration',
            'params': {
                'migration_sql': 'ALTER TABLE users ADD COLUMN phone VARCHAR(20)'
            },
            'tool_definition': tool
        }

        validation = safety_controller.validate_step(step, strict_agent_config)

        assert validation['requires_approval'] == True
        assert validation['approval_requirement'] == ApprovalRequirement.REQUIRED
        assert validation['risk_level'] == 'critical'

    def test_destructive_operation_multi_party(self, safety_controller, strict_agent_config):
        """Test that destructive operations require multi-party approval"""
        tool = ToolDefinition(
            name="drop_table",
            description="Drop database table",
            category=ToolCategory.DATABASE_DDL,
            risk_level=ToolRiskLevel.CRITICAL,
            required_capabilities=[AgentCapability.DATABASE_DDL],
            parameters_schema={},
            returns_schema={},
            implementation=lambda p, c: {},
            requires_approval=True,
            max_execution_time=300,
            examples=[]
        )

        step = {
            'tool': 'drop_table',
            'params': {'table': 'users'},
            'tool_definition': tool
        }

        validation = safety_controller.validate_step(step, strict_agent_config)

        assert validation['requires_approval'] == True
        assert validation['approval_requirement'] == ApprovalRequirement.MULTI_PARTY
        assert "Potentially irreversible destructive operation" in validation['risks']

    def test_sql_risk_analysis_integration(self, safety_controller, strict_agent_config):
        """Test SQL risk analysis is included in validation"""
        tool = ToolDefinition(
            name="execute_query",
            description="Execute SQL query",
            category=ToolCategory.DATABASE_WRITE,
            risk_level=ToolRiskLevel.MEDIUM,
            required_capabilities=[AgentCapability.DATABASE_WRITE],
            parameters_schema={},
            returns_schema={},
            implementation=lambda p, c: {},
            requires_approval=False,
            max_execution_time=300,
            examples=[]
        )

        # Query without WHERE clause (dangerous)
        step = {
            'tool': 'execute_query',
            'params': {
                'sql': 'DELETE FROM users'
            },
            'tool_definition': tool
        }

        validation = safety_controller.validate_step(step, strict_agent_config)

        assert 'sql_analysis' in validation
        assert validation['sql_analysis']['risk_level'] == 'HIGH'
        assert validation['requires_approval'] == True
```

### 11.2 Integration Tests

```python
# tests/integration/test_approval_workflow.py

import pytest
import asyncio
from src.agents.orchestrator import WorkflowOrchestrator, WorkflowConfig
from src.agents.manager import AgentManager
from src.agents.state.manager import StateManager
from src.agents.safety.controller import SafetyController

@pytest.fixture
async def orchestrator():
    agent_manager = AgentManager(llm_manager, tool_registry, state_manager)
    state_manager = StateManager()
    safety_controller = SafetyController(risk_analyzer)

    return WorkflowOrchestrator(agent_manager, state_manager, safety_controller)

@pytest.mark.asyncio
async def test_approval_workflow_approved(orchestrator):
    """Test successful approval workflow"""

    # Custom approval callback that auto-approves
    async def auto_approve(request):
        return {
            'approved': True,
            'reason': 'Test auto-approval',
            'approver': 'test',
            'timestamp': datetime.utcnow().isoformat(),
            'conditions': []
        }

    config = WorkflowConfig(
        workflow_id="test_001",
        workflow_name="Test Migration",
        description="Test migration workflow",
        agent_type="migration",
        input_data={
            'migration_type': 'add_column',
            'target_schema': {'table': 'users', 'column': 'phone', 'type': 'VARCHAR(20)'}
        },
        database_config={'database': 'test'},
        approval_callback=auto_approve
    )

    result = await orchestrator.execute_workflow(config)

    assert result.status == 'success'
    assert len(result.actions_taken) > 0

@pytest.mark.asyncio
async def test_approval_workflow_rejected(orchestrator):
    """Test workflow rejection"""

    # Custom approval callback that rejects
    async def auto_reject(request):
        return {
            'approved': False,
            'reason': 'Test auto-rejection',
            'approver': 'test',
            'timestamp': datetime.utcnow().isoformat(),
            'conditions': []
        }

    config = WorkflowConfig(
        workflow_id="test_002",
        workflow_name="Test Migration",
        description="Test migration workflow",
        agent_type="migration",
        input_data={
            'migration_type': 'drop_table',
            'target_schema': {'table': 'users'}
        },
        database_config={'database': 'test'},
        approval_callback=auto_reject
    )

    result = await orchestrator.execute_workflow(config)

    assert result.status == 'failure'
    assert 'rejected' in result.error.lower()
```

### 11.3 Safety Constraint Tests

```python
# tests/test_safety_constraints.py

import pytest
from src.agents.safety.constraints import (
    MaxTableSizeConstraint,
    ProductionHoursConstraint
)

class TestSafetyConstraints:

    def test_max_table_size_constraint(self):
        """Test max table size constraint"""
        constraint = MaxTableSizeConstraint(max_rows=100000)

        step = {
            'tool': 'execute_migration',
            'params': {'table': 'users'}
        }

        # Small table - should pass
        context = {'table_sizes': {'users': 50000}}
        assert constraint.validate(step, context) == True

        # Large table - should fail
        context = {'table_sizes': {'users': 150000}}
        assert constraint.validate(step, context) == False

    def test_production_hours_constraint(self):
        """Test production hours constraint"""
        # Maintenance window: 2 AM - 6 AM
        constraint = ProductionHoursConstraint(allowed_hours=[2, 3, 4, 5])

        from unittest.mock import patch
        from datetime import datetime

        tool = ToolDefinition(
            name="execute_migration",
            risk_level=ToolRiskLevel.CRITICAL,
            # ... other fields
        )

        step = {
            'tool': 'execute_migration',
            'tool_definition': tool,
            'params': {}
        }

        # During maintenance window - should pass
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 10, 5, 3, 0)  # 3 AM
            assert constraint.validate(step, {}) == True

        # During business hours - should fail
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2025, 10, 5, 14, 0)  # 2 PM
            assert constraint.validate(step, {}) == False
```

---

## 12. Production Deployment

### 12.1 Security Hardening

**1. Secrets Management**
```python
# config/production.py

import os
from typing import Dict

def load_secrets() -> Dict[str, str]:
    """Load secrets from secure storage"""
    return {
        'database_password': os.environ.get('DB_PASSWORD'),
        'slack_token': os.environ.get('SLACK_TOKEN'),
        'encryption_key': os.environ.get('ENCRYPTION_KEY')
    }

# Never hardcode secrets in configuration files
```

**2. Approval Callback Security**
```python
class SecureApprovalCallback:
    """Secure approval callback with authentication"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def __call__(self, approval_request: Dict[str, Any]) -> Dict[str, Any]:
        # Verify API key
        if not self._verify_api_key():
            raise SecurityError("Invalid API key")

        # Request approval through secure channel
        response = await self._request_secure_approval(approval_request)

        # Verify signature
        if not self._verify_signature(response):
            raise SecurityError("Invalid approval signature")

        return response
```

**3. Audit Log Security**
```python
# Encrypt sensitive data in audit logs
import hashlib
from cryptography.fernet import Fernet

class SecureAuditLogger:
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)

    def log_approval(self, entry: Dict[str, Any]):
        # Hash sensitive parameters
        if 'params' in entry['request']['step']:
            params = entry['request']['step']['params']
            if 'password' in params:
                params['password'] = self._hash_value(params['password'])

        # Encrypt SQL content
        if 'sql' in entry['request']['step']['params']:
            sql = entry['request']['step']['params']['sql']
            entry['request']['step']['params']['sql_encrypted'] = self._encrypt(sql)
            del entry['request']['step']['params']['sql']

        # Store encrypted entry
        self._store_entry(entry)

    def _hash_value(self, value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    def _encrypt(self, value: str) -> str:
        return self.cipher.encrypt(value.encode()).decode()
```

### 12.2 Monitoring and Alerting

```python
# monitoring/safety_monitor.py

import asyncio
from typing import List
import aiohttp

class SafetyMonitor:
    """Monitor safety events and send alerts"""

    def __init__(self, alert_webhook: str):
        self.alert_webhook = alert_webhook
        self.alert_rules = []

    def add_alert_rule(self, rule: Dict[str, Any]):
        """Add alert rule"""
        self.alert_rules.append(rule)

    async def check_approval_event(self, approval_entry: Dict[str, Any]):
        """Check if approval event triggers alerts"""

        for rule in self.alert_rules:
            if self._matches_rule(approval_entry, rule):
                await self._send_alert(approval_entry, rule)

    def _matches_rule(self, entry: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """Check if entry matches alert rule"""

        # Alert on rejected critical operations
        if rule['type'] == 'rejected_critical':
            return (
                not entry['approval']['approved'] and
                entry['request']['validation']['risk_level'] == 'critical'
            )

        # Alert on multiple rejections
        if rule['type'] == 'multiple_rejections':
            # Check recent history for patterns
            pass

        # Alert on off-hours critical operations
        if rule['type'] == 'off_hours_critical':
            from datetime import datetime
            hour = datetime.fromisoformat(entry['decision_timestamp']).hour
            return (
                entry['request']['validation']['risk_level'] == 'critical' and
                9 <= hour <= 17  # Business hours
            )

        return False

    async def _send_alert(self, entry: Dict[str, Any], rule: Dict[str, Any]):
        """Send alert notification"""
        alert = {
            'severity': rule.get('severity', 'warning'),
            'title': rule.get('title', 'Safety Alert'),
            'message': self._format_alert_message(entry, rule),
            'timestamp': entry['decision_timestamp'],
            'entry': entry
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.alert_webhook, json=alert) as response:
                if response.status != 200:
                    print(f"Failed to send alert: {response.status}")

    def _format_alert_message(self, entry: Dict[str, Any], rule: Dict[str, Any]) -> str:
        step = entry['request']['step']
        validation = entry['request']['validation']
        approval = entry['approval']

        return f"""
🚨 {rule.get('title', 'Safety Alert')}

Tool: {step['tool']}
Risk Level: {validation['risk_level']}
Approved: {approval['approved']}
Approver: {approval['approver']}
Reason: {approval['reason']}

Risks: {', '.join(validation['risks'])}
"""

# Usage
monitor = SafetyMonitor(alert_webhook='https://alerts.example.com/webhook')

# Add alert rules
monitor.add_alert_rule({
    'type': 'rejected_critical',
    'severity': 'high',
    'title': 'Critical Operation Rejected'
})

monitor.add_alert_rule({
    'type': 'off_hours_critical',
    'severity': 'medium',
    'title': 'Critical Operation During Business Hours'
})

# Monitor approval events
async def monitor_approvals(safety_controller):
    while True:
        history = safety_controller.get_approval_history(limit=1)
        if history:
            await monitor.check_approval_event(history[0])
        await asyncio.sleep(5)
```

### 12.3 Compliance Configuration

```python
# compliance/soc2_config.py

"""SOC 2 Compliance Configuration"""

SOC2_CONFIG = {
    'safety': {
        'default_level': 'strict',
        'approval_requirements': {
            'critical_operations': 'multi_party',
            'production_database': 'required',
            'data_deletion': 'multi_party',
            'privilege_escalation': 'multi_party'
        }
    },

    'audit': {
        'retention_days': 2555,  # 7 years for SOC 2
        'encryption': True,
        'immutable': True,
        'backup_frequency': 'daily'
    },

    'access_control': {
        'mfa_required': True,
        'session_timeout': 900,  # 15 minutes
        'ip_whitelist': ['10.0.0.0/8']
    },

    'constraints': [
        {
            'type': 'backup_before_modify',
            'operations': ['execute_migration', 'restore_backup', 'drop_table'],
            'retention_days': 90
        },
        {
            'type': 'change_window',
            'allowed_days': ['saturday', 'sunday'],
            'allowed_hours': [2, 3, 4, 5]
        },
        {
            'type': 'separation_of_duties',
            'require_different_approvers': True,
            'minimum_approvers': 2
        }
    ]
}

# HIPAA Compliance Configuration
HIPAA_CONFIG = {
    'safety': {
        'default_level': 'strict',
        'approval_requirements': {
            'phi_access': 'required',
            'phi_modification': 'multi_party',
            'phi_export': 'multi_party'
        }
    },

    'audit': {
        'retention_days': 2190,  # 6 years for HIPAA
        'encryption': True,
        'access_logging': True,
        'phi_tracking': True
    },

    'constraints': [
        {
            'type': 'phi_protection',
            'encrypt_at_rest': True,
            'encrypt_in_transit': True,
            'redact_in_logs': True
        },
        {
            'type': 'access_control',
            'minimum_necessary': True,
            'role_based': True
        }
    ]
}
```

### 12.4 Deployment Checklist

**Pre-Deployment**:
- [ ] Review and update safety configurations
- [ ] Configure environment-specific settings
- [ ] Set up secure secrets management
- [ ] Configure approval callbacks (Slack/Teams/Email)
- [ ] Enable audit logging with encryption
- [ ] Set up monitoring and alerting
- [ ] Configure backup policies
- [ ] Test approval workflows in staging
- [ ] Conduct security review
- [ ] Document compliance requirements

**Deployment**:
- [ ] Deploy with `strict` safety level
- [ ] Enable all safety constraints
- [ ] Activate multi-party approval for critical ops
- [ ] Configure production hours restrictions
- [ ] Enable real-time monitoring
- [ ] Set up alert escalation paths
- [ ] Verify audit log retention
- [ ] Test emergency rollback procedures

**Post-Deployment**:
- [ ] Monitor approval patterns
- [ ] Review audit logs daily
- [ ] Analyze rejected operations
- [ ] Tune safety thresholds
- [ ] Update documentation
- [ ] Conduct regular compliance audits
- [ ] Train team on approval process
- [ ] Establish incident response procedures

### 12.5 Emergency Procedures

```python
# emergency/safety_override.py

"""Emergency safety override procedures"""

class EmergencyOverride:
    """Emergency override for critical situations"""

    def __init__(self, audit_logger):
        self.audit_logger = audit_logger
        self.override_active = False

    async def enable_override(self, justification: str, authorized_by: List[str]):
        """Enable emergency override with justification"""

        # Require multiple authorizations
        if len(authorized_by) < 2:
            raise SecurityError("Emergency override requires at least 2 authorizations")

        # Log override activation
        self.audit_logger.log_critical_event({
            'event': 'emergency_override_enabled',
            'justification': justification,
            'authorized_by': authorized_by,
            'timestamp': datetime.utcnow().isoformat()
        })

        self.override_active = True

        # Send alerts
        await self._send_override_alert(justification, authorized_by)

    async def disable_override(self, completed_by: str):
        """Disable emergency override"""

        self.audit_logger.log_critical_event({
            'event': 'emergency_override_disabled',
            'completed_by': completed_by,
            'timestamp': datetime.utcnow().isoformat()
        })

        self.override_active = False

    def is_override_active(self) -> bool:
        """Check if override is active"""
        return self.override_active
```

---

## Summary

The AIShell Safety and Approval System provides comprehensive protection for autonomous AI agent operations through:

1. **Multi-Level Safety**: Strict, moderate, and permissive modes for different environments
2. **Risk Assessment**: Automatic evaluation of operation risk with SQL analysis
3. **Approval Workflows**: Interactive and automated approval with custom callbacks
4. **Destructive Operation Protection**: Special handling for irreversible operations
5. **Comprehensive Auditing**: Complete trail of all decisions and operations
6. **Production-Ready**: Security hardening, monitoring, and compliance features

### Key Takeaways

✅ **Always use `strict` mode in production**
✅ **Implement multi-party approval for destructive operations**
✅ **Enable comprehensive audit logging with encryption**
✅ **Set up real-time monitoring and alerting**
✅ **Test approval workflows thoroughly before deployment**
✅ **Document compliance requirements and configurations**
✅ **Establish emergency procedures and override protocols**

### Next Steps

1. Review your environment requirements
2. Configure appropriate safety levels
3. Implement custom approval callbacks
4. Set up monitoring and alerting
5. Conduct security audit
6. Train team on approval processes
7. Deploy with comprehensive testing

For more information, see:
- Tutorial 01: Getting Started with Agentic Workflows
- Tutorial 02: Tool Registry and Custom Tools
- Tutorial 03: Workflow Orchestration
- Phase 12 Architecture Documentation

---

**Generated by AIShell Safety and Approval System Tutorial**
**Version 1.0.0 | Updated: 2025-10-05**
