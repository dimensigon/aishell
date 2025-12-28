# AI-Shell Hands-On Tutorial - Part 3: Security & Enterprise Features

**Level:** Intermediate
**Duration:** 60 minutes
**Prerequisites:** Completion of Parts 1 & 2, Active database connection

---

## Table of Contents
1. [SQL Injection Prevention](#sql-injection-prevention)
2. [Role-Based Access Control (RBAC)](#role-based-access-control-rbac)
3. [Data Encryption](#data-encryption)
4. [Audit Logging](#audit-logging)
5. [Multi-Tenancy](#multi-tenancy)
6. [Security Monitoring](#security-monitoring)
7. [Validation Checkpoints](#validation-checkpoints)
8. [Troubleshooting](#troubleshooting)

---

## 1. SQL Injection Prevention

### Step 1.1: Understanding SQL Injection Risks

```python
from ai_shell import SecurityScanner

# Initialize security scanner
scanner = SecurityScanner()

# Examples of vulnerable queries
vulnerable_queries = [
    "SELECT * FROM users WHERE name = '" + user_input + "'",  # BAD
    f"SELECT * FROM users WHERE id = {user_id}",  # BAD
    "SELECT * FROM users; DROP TABLE users; --",  # ATTACK
    "SELECT * FROM users WHERE name = 'admin' OR '1'='1'",  # ATTACK
]

print("=== SQL Injection Risk Assessment ===\n")

for query in vulnerable_queries:
    risk = scanner.assess_injection_risk(query)

    print(f"Query: {query[:60]}...")
    print(f"  Risk Level: {risk.level}")  # safe, low, medium, high, critical
    print(f"  Threats: {risk.threats}")
    print(f"  Severity Score: {risk.score}/100")
    print()
```

**Expected Output:**
```
=== SQL Injection Risk Assessment ===

Query: SELECT * FROM users WHERE name = '" + user_input + "'...
  Risk Level: high
  Threats: ['STRING_CONCATENATION', 'USER_INPUT']
  Severity Score: 85/100

Query: SELECT * FROM users WHERE id = {user_id}...
  Risk Level: high
  Threats: ['STRING_INTERPOLATION', 'USER_INPUT']
  Severity Score: 80/100

Query: SELECT * FROM users; DROP TABLE users; --...
  Risk Level: critical
  Threats: ['MULTIPLE_STATEMENTS', 'DATA_MODIFICATION', 'COMMENT_ATTACK']
  Severity Score: 100/100
```

### Step 1.2: Parameterized Queries (Safe Method)

```python
from ai_shell import SecureExecutor

# Initialize secure executor
secure_executor = SecureExecutor(connector)

# ✓ SAFE: Parameterized query
user_input = "admin' OR '1'='1"  # Attempted injection

result = await secure_executor.execute(
    "SELECT * FROM users WHERE name = :name",
    {"name": user_input}
)

print(f"✓ Query executed safely")
print(f"  Input treated as literal: {user_input}")
print(f"  Rows returned: {len(result.rows)}")  # Returns 0 - no user with that exact name
```

**Expected Output:**
```
✓ Query executed safely
  Input treated as literal: admin' OR '1'='1
  Rows returned: 0
```

### Step 1.3: Input Validation and Sanitization

```python
from ai_shell import InputValidator

# Initialize validator
validator = InputValidator()

# Define validation rules
validator.add_rule("email", pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
validator.add_rule("user_id", type="integer", min=1, max=999999)
validator.add_rule("username", type="string", min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")

# Validate inputs
test_inputs = {
    "email": "user@example.com",
    "user_id": "123",
    "username": "john_doe"
}

print("=== Input Validation ===\n")

for field, value in test_inputs.items():
    result = validator.validate(field, value)

    if result.is_valid:
        print(f"✓ {field}: {value}")
        print(f"  Sanitized: {result.sanitized_value}")
    else:
        print(f"✗ {field}: {value}")
        print(f"  Error: {result.error}")
    print()
```

**Expected Output:**
```
=== Input Validation ===

✓ email: user@example.com
  Sanitized: user@example.com

✓ user_id: 123
  Sanitized: 123

✓ username: john_doe
  Sanitized: john_doe
```

### Step 1.4: SQL Injection Prevention Layers

```python
from ai_shell import SecurityLayer

# Initialize multi-layer security
security = SecurityLayer(connector)

# Layer 1: Input validation
security.enable_input_validation(strict=True)

# Layer 2: Query parameterization (enforced)
security.enforce_parameterization(True)

# Layer 3: Blacklist dangerous patterns
security.add_blacklist([
    r";\s*(DROP|DELETE|TRUNCATE|ALTER)\s+",  # Dangerous statements
    r"--",  # SQL comments
    r"/\*.*\*/",  # Block comments
    r"UNION\s+SELECT",  # Union-based injection
    r"OR\s+['\"]\d+['\"]\s*=\s*['\"]\d+['\"]",  # Tautology
])

# Layer 4: Whitelist allowed operations
security.set_allowed_operations(["SELECT", "INSERT", "UPDATE"])

# Test protection
malicious_inputs = [
    "admin' OR '1'='1",
    "1; DROP TABLE users; --",
    "1 UNION SELECT * FROM passwords",
]

print("=== Multi-Layer Protection Test ===\n")

for malicious_input in malicious_inputs:
    try:
        result = await security.execute_secure(
            "SELECT * FROM users WHERE id = :id",
            {"id": malicious_input}
        )
        print(f"✓ Query blocked or sanitized: {malicious_input}")
    except SecurityError as e:
        print(f"🛡️ Attack blocked: {malicious_input}")
        print(f"  Reason: {e.reason}")
        print()
```

**Expected Output:**
```
=== Multi-Layer Protection Test ===

🛡️ Attack blocked: admin' OR '1'='1
  Reason: Tautology pattern detected

🛡️ Attack blocked: 1; DROP TABLE users; --
  Reason: Multiple statements not allowed

🛡️ Attack blocked: 1 UNION SELECT * FROM passwords
  Reason: UNION-based injection detected
```

### Step 1.5: Automated Security Scanning

```python
# Scan entire codebase for SQL injection vulnerabilities
scanner = SecurityScanner()

# Scan specific files
vulnerabilities = await scanner.scan_directory("/path/to/code")

print(f"\n=== Security Scan Results ===\n")
print(f"Files scanned: {vulnerabilities.files_scanned}")
print(f"Vulnerabilities found: {vulnerabilities.total_count}")
print(f"Critical: {vulnerabilities.critical_count}")
print(f"High: {vulnerabilities.high_count}")
print(f"Medium: {vulnerabilities.medium_count}")

if vulnerabilities.issues:
    print("\nTop Issues:")
    for issue in vulnerabilities.top_issues[:5]:
        print(f"  - {issue.file}:{issue.line}")
        print(f"    {issue.description}")
        print(f"    Severity: {issue.severity}")
        print(f"    Fix: {issue.recommendation}")
        print()
```

---

## 2. Role-Based Access Control (RBAC)

### Step 2.1: Setting Up RBAC

```python
from ai_shell import RBACManager

# Initialize RBAC manager
rbac = RBACManager(connector)

# Create roles
await rbac.create_role(
    name="admin",
    description="Full system access",
    permissions=["*"]  # All permissions
)

await rbac.create_role(
    name="analyst",
    description="Read-only access to data",
    permissions=["SELECT"]
)

await rbac.create_role(
    name="developer",
    description="Read and write access",
    permissions=["SELECT", "INSERT", "UPDATE"]
)

await rbac.create_role(
    name="viewer",
    description="Limited read access",
    permissions=["SELECT"],
    restrictions=["WHERE tenant_id = :current_tenant_id"]
)

print("✓ Roles created successfully")
```

**Expected Output:**
```
✓ Roles created successfully
```

### Step 2.2: Assigning Users to Roles

```python
# Create users and assign roles
await rbac.create_user(
    username="alice",
    email="alice@example.com",
    roles=["admin"]
)

await rbac.create_user(
    username="bob",
    email="bob@example.com",
    roles=["analyst", "viewer"]  # Multiple roles
)

await rbac.create_user(
    username="charlie",
    email="charlie@example.com",
    roles=["developer"]
)

# List users and their roles
users = await rbac.list_users()

print("\n=== Users and Roles ===\n")
for user in users:
    print(f"{user.username} ({user.email})")
    print(f"  Roles: {', '.join(user.roles)}")
    print(f"  Permissions: {', '.join(user.permissions)}")
    print()
```

**Expected Output:**
```
=== Users and Roles ===

alice (alice@example.com)
  Roles: admin
  Permissions: ALL

bob (bob@example.com)
  Roles: analyst, viewer
  Permissions: SELECT

charlie (charlie@example.com)
  Roles: developer
  Permissions: SELECT, INSERT, UPDATE
```

### Step 2.3: Permission Enforcement

```python
from ai_shell import RBACExecutor

# Create RBAC-aware executor
rbac_executor = RBACExecutor(connector, rbac_manager=rbac)

# Authenticate as specific user
rbac_executor.authenticate(username="bob")

# Try to execute queries with different permissions

# ✓ ALLOWED: Bob has SELECT permission
try:
    result = await rbac_executor.execute("SELECT * FROM users LIMIT 10")
    print(f"✓ SELECT query executed: {len(result.rows)} rows")
except PermissionError as e:
    print(f"✗ Permission denied: {e}")

# ✗ DENIED: Bob doesn't have INSERT permission
try:
    result = await rbac_executor.execute(
        "INSERT INTO users (name, email) VALUES ('Test', 'test@example.com')"
    )
    print(f"✓ INSERT query executed")
except PermissionError as e:
    print(f"✗ Permission denied: {e}")

# ✗ DENIED: Bob doesn't have DELETE permission
try:
    result = await rbac_executor.execute("DELETE FROM users WHERE id = 999")
    print(f"✓ DELETE query executed")
except PermissionError as e:
    print(f"✗ Permission denied: {e}")
```

**Expected Output:**
```
✓ SELECT query executed: 10 rows
✗ Permission denied: User 'bob' does not have INSERT permission
✗ Permission denied: User 'bob' does not have DELETE permission
```

### Step 2.4: Fine-Grained Permissions

```python
# Set table-level permissions
await rbac.grant_permission(
    role="analyst",
    operation="SELECT",
    tables=["users", "orders", "products"]  # Specific tables only
)

# Set column-level permissions
await rbac.grant_permission(
    role="viewer",
    operation="SELECT",
    tables=["users"],
    columns=["id", "name", "email"],  # Exclude sensitive columns
    exclude_columns=["password_hash", "ssn", "credit_card"]
)

# Set row-level permissions
await rbac.grant_permission(
    role="regional_manager",
    operation="SELECT",
    tables=["orders"],
    conditions=["WHERE region = :user_region"]  # Only see their region
)

# Test column-level restrictions
rbac_executor.authenticate(username="viewer_user")

# This will automatically filter columns
result = await rbac_executor.execute("SELECT * FROM users LIMIT 5")

print("Columns returned:", result.columns)
# Only allowed columns: ['id', 'name', 'email']
```

**Expected Output:**
```
Columns returned: ['id', 'name', 'email']
```

### Step 2.5: Dynamic Role Assignment

```python
# Assign roles based on conditions
await rbac.create_dynamic_role(
    name="weekend_admin",
    base_role="developer",
    conditions={
        "time": "weekends",  # Only active on weekends
        "ip_range": "10.0.0.0/24"  # From specific network
    },
    elevated_permissions=["DELETE", "TRUNCATE"]
)

# Time-based role activation
await rbac.create_temporary_role(
    user="emergency_user",
    role="admin",
    duration="2h",  # Temporary admin access for 2 hours
    reason="Emergency database maintenance"
)

# Check active roles
active_roles = await rbac.get_active_roles(username="emergency_user")
print(f"Active roles: {active_roles}")
```

---

## 3. Data Encryption

### Step 3.1: Field-Level Encryption Setup

```python
from ai_shell import EncryptionManager

# Initialize encryption manager
encryption = EncryptionManager(
    encryption_key=os.getenv("ENCRYPTION_KEY"),  # 32-byte key
    algorithm="AES-256-GCM"
)

# Define fields to encrypt
encryption.register_encrypted_fields([
    {"table": "users", "column": "email"},
    {"table": "users", "column": "phone"},
    {"table": "users", "column": "ssn"},
    {"table": "payments", "column": "credit_card"},
    {"table": "payments", "column": "bank_account"},
])

print("✓ Encryption configured for sensitive fields")
```

**Expected Output:**
```
✓ Encryption configured for sensitive fields
```

### Step 3.2: Encrypting Data

```python
from ai_shell import EncryptedExecutor

# Create encryption-aware executor
encrypted_executor = EncryptedExecutor(connector, encryption_manager=encryption)

# Insert with automatic encryption
await encrypted_executor.execute(
    """
    INSERT INTO users (name, email, phone, ssn)
    VALUES (:name, :email, :phone, :ssn)
    """,
    {
        "name": "John Doe",
        "email": "john@example.com",  # Will be encrypted
        "phone": "+1-555-0123",  # Will be encrypted
        "ssn": "123-45-6789"  # Will be encrypted
    }
)

print("✓ Data inserted with automatic encryption")

# Verify encryption in database
raw_result = await connector.execute(
    "SELECT email, phone, ssn FROM users WHERE name = 'John Doe'"
)

print("\nRaw encrypted data in database:")
print(f"  Email: {raw_result.rows[0]['email']}")  # Encrypted blob
print(f"  Phone: {raw_result.rows[0]['phone']}")  # Encrypted blob
print(f"  SSN: {raw_result.rows[0]['ssn']}")  # Encrypted blob
```

**Expected Output:**
```
✓ Data inserted with automatic encryption

Raw encrypted data in database:
  Email: 0x4F8A3D2B1C9E7F6A5D4C3B2A1F0E9D8C7B6A5E4D3C2B1A...
  Phone: 0x7B6A5E4D3C2B1A0F9E8D7C6B5A4E3D2C1B0A9F8E7D6C5B...
  SSN: 0x2C1B0A9F8E7D6C5B4A3E2D1C0B9A8F7E6D5C4B3A2E1D0C...
```

### Step 3.3: Decrypting Data

```python
# Query with automatic decryption
result = await encrypted_executor.execute(
    "SELECT name, email, phone, ssn FROM users WHERE name = 'John Doe'"
)

print("\nDecrypted data:")
user = result.rows[0]
print(f"  Name: {user['name']}")
print(f"  Email: {user['email']}")  # Automatically decrypted
print(f"  Phone: {user['phone']}")  # Automatically decrypted
print(f"  SSN: {user['ssn']}")  # Automatically decrypted
```

**Expected Output:**
```
Decrypted data:
  Name: John Doe
  Email: john@example.com
  Phone: +1-555-0123
  SSN: 123-45-6789
```

### Step 3.4: Searchable Encryption

```python
# Enable searchable encryption for encrypted fields
encryption.enable_searchable_encryption(
    fields=[
        {"table": "users", "column": "email"},
    ],
    index_type="hash"  # or "deterministic"
)

# Search on encrypted field
result = await encrypted_executor.execute(
    "SELECT * FROM users WHERE email = :email",
    {"email": "john@example.com"}
)

print(f"✓ Found user with encrypted email search")
print(f"  Rows: {len(result.rows)}")
```

**Expected Output:**
```
✓ Found user with encrypted email search
  Rows: 1
```

### Step 3.5: Key Rotation

```python
# Rotate encryption keys
old_key = os.getenv("OLD_ENCRYPTION_KEY")
new_key = os.getenv("NEW_ENCRYPTION_KEY")

rotation = await encryption.rotate_keys(
    old_key=old_key,
    new_key=new_key,
    tables=["users", "payments"]
)

print("\n=== Key Rotation Results ===\n")
print(f"Tables processed: {rotation.tables_processed}")
print(f"Records re-encrypted: {rotation.records_processed}")
print(f"Duration: {rotation.duration_seconds}s")
print(f"Status: {rotation.status}")
```

**Expected Output:**
```
=== Key Rotation Results ===

Tables processed: 2
Records re-encrypted: 15,432
Duration: 45.3s
Status: completed
```

### Step 3.6: Encryption at Rest and in Transit

```python
# Configure full database encryption
encryption_config = {
    # Encryption at rest
    "at_rest": {
        "enabled": True,
        "algorithm": "AES-256-GCM",
        "key_provider": "AWS-KMS"  # or "Azure-KeyVault", "GCP-KMS"
    },

    # Encryption in transit
    "in_transit": {
        "enabled": True,
        "tls_version": "1.3",
        "cipher_suites": ["TLS_AES_256_GCM_SHA384"],
        "require_client_cert": True
    },

    # Backup encryption
    "backups": {
        "enabled": True,
        "algorithm": "AES-256-CBC"
    }
}

await encryption.configure(encryption_config)
print("✓ Full encryption configured")
```

---

## 4. Audit Logging

### Step 4.1: Enable Audit Logging

```python
from ai_shell import AuditLogger

# Initialize audit logger
audit = AuditLogger(
    connector=connector,
    log_table="audit_log",
    retention_days=90
)

# Enable logging for specific operations
audit.enable_logging(
    operations=["SELECT", "INSERT", "UPDATE", "DELETE"],
    log_level="detailed"  # minimal, standard, detailed
)

print("✓ Audit logging enabled")
```

**Expected Output:**
```
✓ Audit logging enabled
```

### Step 4.2: Logging Database Operations

```python
from ai_shell import AuditedExecutor

# Create audit-aware executor
audited_executor = AuditedExecutor(
    connector=connector,
    audit_logger=audit,
    user_context={"username": "alice", "ip": "192.168.1.100", "role": "admin"}
)

# Execute operations (automatically logged)
await audited_executor.execute(
    "SELECT * FROM sensitive_data WHERE id = :id",
    {"id": 123}
)

await audited_executor.execute(
    "UPDATE users SET email = :email WHERE id = :id",
    {"email": "newemail@example.com", "id": 456}
)

await audited_executor.execute(
    "DELETE FROM archived_records WHERE created_at < :date",
    {"date": "2020-01-01"}
)

print("✓ Operations logged to audit trail")
```

**Expected Output:**
```
✓ Operations logged to audit trail
```

### Step 4.3: Querying Audit Logs

```python
# Query audit logs
logs = await audit.query_logs(
    filters={
        "username": "alice",
        "operation": ["UPDATE", "DELETE"],
        "date_from": "2024-10-01",
        "date_to": "2024-10-11"
    },
    order_by="timestamp DESC",
    limit=10
)

print("\n=== Audit Log Entries ===\n")

for log in logs:
    print(f"[{log.timestamp}] {log.username}@{log.ip}")
    print(f"  Operation: {log.operation}")
    print(f"  Query: {log.query[:60]}...")
    print(f"  Table: {log.table}")
    print(f"  Rows affected: {log.rows_affected}")
    print(f"  Duration: {log.duration_ms}ms")
    print()
```

**Expected Output:**
```
=== Audit Log Entries ===

[2024-10-11 14:32:15] alice@192.168.1.100
  Operation: DELETE
  Query: DELETE FROM archived_records WHERE created_at < :date...
  Table: archived_records
  Rows affected: 1,523
  Duration: 234ms

[2024-10-11 14:31:42] alice@192.168.1.100
  Operation: UPDATE
  Query: UPDATE users SET email = :email WHERE id = :id...
  Table: users
  Rows affected: 1
  Duration: 12ms
```

### Step 4.4: Compliance Reporting

```python
# Generate compliance reports
report = await audit.generate_compliance_report(
    period="last_quarter",
    standards=["SOC2", "GDPR", "HIPAA"]
)

print("\n=== Compliance Report ===\n")
print(f"Period: {report.period}")
print(f"Standards: {', '.join(report.standards)}")
print(f"\nMetrics:")
print(f"  Total queries: {report.total_queries}")
print(f"  Data access events: {report.data_access_events}")
print(f"  Data modifications: {report.data_modifications}")
print(f"  Failed access attempts: {report.failed_attempts}")
print(f"  Suspicious activities: {report.suspicious_activities}")

print(f"\nCompliance Status:")
for standard in report.compliance_status:
    status = "✓" if standard.compliant else "✗"
    print(f"  {status} {standard.name}: {standard.score}%")

if report.violations:
    print(f"\nViolations:")
    for violation in report.violations:
        print(f"  - {violation.description}")
        print(f"    Severity: {violation.severity}")
        print(f"    Date: {violation.date}")
```

**Expected Output:**
```
=== Compliance Report ===

Period: Q3 2024 (Jul 1 - Sep 30)
Standards: SOC2, GDPR, HIPAA

Metrics:
  Total queries: 1,245,321
  Data access events: 987,654
  Data modifications: 145,234
  Failed access attempts: 23
  Suspicious activities: 2

Compliance Status:
  ✓ SOC2: 98%
  ✓ GDPR: 97%
  ✓ HIPAA: 99%

Violations:
  - Unencrypted data access attempt
    Severity: medium
    Date: 2024-09-15
```

### Step 4.5: Real-time Alerting

```python
# Set up real-time alerts
audit.configure_alerts([
    {
        "name": "Suspicious Delete",
        "condition": "operation = 'DELETE' AND rows_affected > 100",
        "severity": "high",
        "notification": ["email", "slack"],
        "recipients": ["security@example.com"]
    },
    {
        "name": "After Hours Access",
        "condition": "EXTRACT(HOUR FROM timestamp) NOT BETWEEN 8 AND 18",
        "severity": "medium",
        "notification": ["email"],
        "recipients": ["audit@example.com"]
    },
    {
        "name": "Failed Authentication",
        "condition": "operation = 'LOGIN' AND status = 'failed'",
        "severity": "high",
        "notification": ["email", "slack", "pagerduty"],
        "recipients": ["security@example.com"]
    }
])

print("✓ Real-time alerts configured")
```

---

## 5. Multi-Tenancy

### Step 5.1: Setting Up Multi-Tenancy

```python
from ai_shell import MultiTenancyManager

# Initialize multi-tenancy manager
tenancy = MultiTenancyManager(
    connector=connector,
    isolation_level="schema"  # "schema", "database", or "row"
)

# Create tenants
await tenancy.create_tenant(
    tenant_id="acme_corp",
    name="Acme Corporation",
    schema_name="acme_corp",
    config={
        "max_connections": 50,
        "storage_quota_gb": 100,
        "features": ["encryption", "audit", "backup"]
    }
)

await tenancy.create_tenant(
    tenant_id="widgets_inc",
    name="Widgets Inc",
    schema_name="widgets_inc",
    config={
        "max_connections": 25,
        "storage_quota_gb": 50,
        "features": ["encryption", "audit"]
    }
)

print("✓ Tenants created with isolated schemas")
```

**Expected Output:**
```
✓ Tenants created with isolated schemas
```

### Step 5.2: Tenant-Aware Queries

```python
from ai_shell import TenantExecutor

# Create tenant-aware executor
tenant_executor = TenantExecutor(
    connector=connector,
    tenancy_manager=tenancy
)

# Set current tenant context
tenant_executor.set_tenant("acme_corp")

# Execute queries (automatically scoped to tenant)
result = await tenant_executor.execute(
    "SELECT * FROM users LIMIT 10"
)
# Actually executes: SELECT * FROM acme_corp.users LIMIT 10

print(f"✓ Query executed in tenant context: acme_corp")
print(f"  Rows: {len(result.rows)}")

# Switch tenant
tenant_executor.set_tenant("widgets_inc")

result = await tenant_executor.execute(
    "SELECT * FROM users LIMIT 10"
)
# Actually executes: SELECT * FROM widgets_inc.users LIMIT 10

print(f"✓ Query executed in tenant context: widgets_inc")
print(f"  Rows: {len(result.rows)}")
```

**Expected Output:**
```
✓ Query executed in tenant context: acme_corp
  Rows: 10
✓ Query executed in tenant context: widgets_inc
  Rows: 10
```

### Step 5.3: Row-Level Multi-Tenancy

```python
# Alternative: Row-level isolation
tenancy_row = MultiTenancyManager(
    connector=connector,
    isolation_level="row"
)

# Add tenant_id column to tables
await tenancy_row.enable_row_level_isolation(
    tables=["users", "orders", "products"]
)

# Queries automatically filter by tenant
tenant_executor.set_tenant("acme_corp")

result = await tenant_executor.execute(
    "SELECT * FROM users"
)
# Actually executes: SELECT * FROM users WHERE tenant_id = 'acme_corp'

print(f"✓ Row-level isolation active")
```

### Step 5.4: Tenant Resource Management

```python
# Monitor tenant resource usage
usage = await tenancy.get_tenant_usage("acme_corp")

print("\n=== Tenant Resource Usage ===\n")
print(f"Tenant: {usage.tenant_name}")
print(f"Storage used: {usage.storage_used_gb:.2f}GB / {usage.storage_quota_gb}GB")
print(f"Active connections: {usage.active_connections} / {usage.max_connections}")
print(f"Queries today: {usage.queries_today}")
print(f"Data transfer: {usage.data_transfer_gb:.2f}GB")
print(f"Status: {usage.status}")

if usage.quota_warnings:
    print(f"\n⚠️ Warnings:")
    for warning in usage.quota_warnings:
        print(f"  - {warning}")
```

**Expected Output:**
```
=== Tenant Resource Usage ===

Tenant: Acme Corporation
Storage used: 45.32GB / 100GB
Active connections: 12 / 50
Queries today: 15,234
Data transfer: 2.34GB
Status: active

⚠️ Warnings:
  - Storage usage at 45% - consider upgrading
```

### Step 5.5: Cross-Tenant Operations

```python
# Enable cross-tenant queries for admin users
admin_executor = TenantExecutor(
    connector=connector,
    tenancy_manager=tenancy,
    allow_cross_tenant=True
)

# Authenticate as admin
admin_executor.authenticate(username="system_admin", role="super_admin")

# Query across all tenants
result = await admin_executor.execute_cross_tenant(
    "SELECT tenant_id, COUNT(*) as user_count FROM users GROUP BY tenant_id"
)

print("\n=== Cross-Tenant Report ===\n")
for row in result.rows:
    print(f"Tenant {row['tenant_id']}: {row['user_count']} users")
```

**Expected Output:**
```
=== Cross-Tenant Report ===

Tenant acme_corp: 1,245 users
Tenant widgets_inc: 567 users
Tenant tech_start: 89 users
```

---

## 6. Security Monitoring

### Step 6.1: Real-Time Security Monitoring

```python
from ai_shell import SecurityMonitor

# Initialize security monitor
security_monitor = SecurityMonitor(connector)

# Start monitoring
await security_monitor.start()

# Monitor for threats
async def monitor_threats():
    async for threat in security_monitor.stream_threats():
        print(f"\n🚨 SECURITY THREAT DETECTED\n")
        print(f"  Type: {threat.type}")
        print(f"  Severity: {threat.severity}")
        print(f"  Description: {threat.description}")
        print(f"  User: {threat.user}")
        print(f"  IP: {threat.ip_address}")
        print(f"  Time: {threat.timestamp}")
        print(f"  Action taken: {threat.action_taken}")

# Run monitoring in background
await monitor_threats()
```

**Expected Output:**
```
🚨 SECURITY THREAT DETECTED

  Type: SQL_INJECTION_ATTEMPT
  Severity: high
  Description: Attempted SQL injection in login form
  User: anonymous
  IP: 203.0.113.45
  Time: 2024-10-11 14:45:23
  Action taken: Request blocked, IP logged
```

### Step 6.2: Security Metrics Dashboard

```python
# Get security metrics
metrics = await security_monitor.get_metrics(period="24h")

print("\n=== Security Metrics (24 hours) ===\n")
print(f"Total requests: {metrics.total_requests:,}")
print(f"Blocked requests: {metrics.blocked_requests:,}")
print(f"Success rate: {metrics.success_rate:.1f}%")
print(f"\nThreats by type:")
for threat_type, count in metrics.threats_by_type.items():
    print(f"  {threat_type}: {count}")

print(f"\nTop attacking IPs:")
for ip, count in metrics.top_attacking_ips[:5]:
    print(f"  {ip}: {count} attempts")

print(f"\nBlocked users:")
print(f"  Temporarily blocked: {metrics.temp_blocked_users}")
print(f"  Permanently blocked: {metrics.perm_blocked_users}")
```

**Expected Output:**
```
=== Security Metrics (24 hours) ===

Total requests: 1,234,567
Blocked requests: 1,234
Success rate: 99.9%

Threats by type:
  SQL_INJECTION_ATTEMPT: 345
  BRUTE_FORCE_ATTACK: 234
  UNAUTHORIZED_ACCESS: 123
  PRIVILEGE_ESCALATION: 45
  DATA_EXFILTRATION: 12

Top attacking IPs:
  203.0.113.45: 234 attempts
  198.51.100.23: 156 attempts
  192.0.2.67: 89 attempts
  203.0.113.89: 67 attempts
  198.51.100.45: 45 attempts

Blocked users:
  Temporarily blocked: 23
  Permanently blocked: 5
```

### Step 6.3: Intrusion Detection System (IDS)

```python
# Configure IDS rules
security_monitor.configure_ids([
    {
        "name": "Rapid Fire Queries",
        "condition": "queries_per_minute > 1000",
        "action": "block_temp",
        "duration": "15m"
    },
    {
        "name": "Unauthorized Table Access",
        "condition": "table IN ('system_config', 'encryption_keys')",
        "action": "block_perm"
    },
    {
        "name": "Large Data Export",
        "condition": "rows_returned > 100000",
        "action": "alert"
    },
    {
        "name": "Off-Hours Admin Access",
        "condition": "role = 'admin' AND HOUR(timestamp) NOT BETWEEN 8 AND 18",
        "action": "alert_critical"
    }
])

print("✓ IDS rules configured")
```

### Step 6.4: Vulnerability Assessment

```python
# Run security vulnerability scan
assessment = await security_monitor.assess_vulnerabilities()

print("\n=== Vulnerability Assessment ===\n")
print(f"Scan date: {assessment.scan_date}")
print(f"Overall security score: {assessment.security_score}/100")

print(f"\nVulnerabilities found: {assessment.vulnerability_count}")
print(f"  Critical: {assessment.critical_count}")
print(f"  High: {assessment.high_count}")
print(f"  Medium: {assessment.medium_count}")
print(f"  Low: {assessment.low_count}")

print(f"\nTop vulnerabilities:")
for vuln in assessment.top_vulnerabilities[:5]:
    print(f"  - {vuln.name} ({vuln.severity})")
    print(f"    {vuln.description}")
    print(f"    Fix: {vuln.remediation}")
    print()
```

**Expected Output:**
```
=== Vulnerability Assessment ===

Scan date: 2024-10-11
Overall security score: 87/100

Vulnerabilities found: 12
  Critical: 0
  High: 2
  Medium: 5
  Low: 5

Top vulnerabilities:
  - Weak Password Policy (high)
    Password requirements do not meet security standards
    Fix: Implement password policy with min 12 chars, complexity requirements

  - Missing Input Validation (high)
    Some endpoints lack proper input validation
    Fix: Add validation middleware to all user input endpoints

  - Outdated Dependencies (medium)
    3 dependencies have known security vulnerabilities
    Fix: Update sqlalchemy, cryptography, and requests libraries
```

### Step 6.5: Security Incident Response

```python
# Configure automated incident response
security_monitor.configure_incident_response([
    {
        "trigger": "SQL_INJECTION_ATTEMPT",
        "actions": [
            "block_ip",
            "alert_security_team",
            "log_incident",
            "capture_request_details"
        ]
    },
    {
        "trigger": "BRUTE_FORCE_ATTACK",
        "actions": [
            "block_ip_temp",
            "increase_rate_limit",
            "alert_security_team",
            "log_incident"
        ]
    },
    {
        "trigger": "DATA_EXFILTRATION",
        "actions": [
            "block_user",
            "alert_security_team_critical",
            "freeze_account",
            "log_incident",
            "notify_compliance"
        ]
    }
])

# View recent incidents
incidents = await security_monitor.get_recent_incidents(limit=5)

print("\n=== Recent Security Incidents ===\n")
for incident in incidents:
    print(f"Incident #{incident.id}")
    print(f"  Type: {incident.type}")
    print(f"  Severity: {incident.severity}")
    print(f"  Time: {incident.timestamp}")
    print(f"  User: {incident.user}")
    print(f"  Status: {incident.status}")
    print(f"  Actions taken: {', '.join(incident.actions_taken)}")
    print()
```

---

## 7. Validation Checkpoints

### Complete Security System Validation

```python
from ai_shell import SecurityValidator

validator = SecurityValidator(connector)

print("\n=== Security System Validation ===\n")

# Test SQL injection prevention
injection_test = await validator.test_injection_prevention()
print(f"✓ SQL Injection Prevention: {injection_test.status}")
print(f"  Attacks blocked: {injection_test.attacks_blocked}/{injection_test.attacks_tested}")

# Test RBAC
rbac_test = await validator.test_rbac()
print(f"✓ RBAC: {rbac_test.status}")
print(f"  Permission checks passed: {rbac_test.checks_passed}/{rbac_test.total_checks}")

# Test encryption
encryption_test = await validator.test_encryption()
print(f"✓ Encryption: {encryption_test.status}")
print(f"  Fields encrypted: {encryption_test.encrypted_fields}/{encryption_test.total_fields}")

# Test audit logging
audit_test = await validator.test_audit_logging()
print(f"✓ Audit Logging: {audit_test.status}")
print(f"  Events logged: {audit_test.events_logged}/{audit_test.events_tested}")

# Test multi-tenancy
tenancy_test = await validator.test_multi_tenancy()
print(f"✓ Multi-Tenancy: {tenancy_test.status}")
print(f"  Isolation verified: {tenancy_test.isolation_verified}")

# Test security monitoring
monitoring_test = await validator.test_security_monitoring()
print(f"✓ Security Monitoring: {monitoring_test.status}")
print(f"  Threats detected: {monitoring_test.threats_detected}/{monitoring_test.threats_simulated}")

print(f"\nOverall Security Status: {'PASS' if validator.all_passed() else 'FAIL'}")
print(f"Security Score: {validator.get_security_score()}/100")
```

**Expected Output:**
```
=== Security System Validation ===

✓ SQL Injection Prevention: PASS
  Attacks blocked: 25/25
✓ RBAC: PASS
  Permission checks passed: 50/50
✓ Encryption: PASS
  Fields encrypted: 15/15
✓ Audit Logging: PASS
  Events logged: 100/100
✓ Multi-Tenancy: PASS
  Isolation verified: True
✓ Security Monitoring: PASS
  Threats detected: 20/20

Overall Security Status: PASS
Security Score: 96/100
```

---

## 8. Troubleshooting

### Issue 1: RBAC Permission Errors

**Symptoms:**
```
PermissionError: User does not have required permission
```

**Solutions:**
```python
# Check user permissions
user_perms = await rbac.get_user_permissions(username="bob")
print(f"User permissions: {user_perms}")

# Grant missing permission
await rbac.grant_permission(
    role="analyst",
    operation="INSERT",
    tables=["reports"]
)

# Verify permission
has_perm = await rbac.check_permission(
    username="bob",
    operation="INSERT",
    table="reports"
)
print(f"Has permission: {has_perm}")

# Force permission refresh
await rbac.refresh_permissions(username="bob")
```

### Issue 2: Encryption Key Issues

**Symptoms:**
```
EncryptionError: Unable to decrypt data
```

**Solutions:**
```python
# Verify encryption key
try:
    test_encrypt = encryption.encrypt("test_data")
    test_decrypt = encryption.decrypt(test_encrypt)
    print("✓ Encryption key is valid")
except Exception as e:
    print(f"✗ Encryption key issue: {e}")

# Check key rotation status
rotation_status = await encryption.get_rotation_status()
print(f"Last rotation: {rotation_status.last_rotation_date}")
print(f"Next rotation: {rotation_status.next_rotation_date}")

# Manually decrypt with old key
old_encryption = EncryptionManager(encryption_key=old_key)
decrypted = old_encryption.decrypt(encrypted_data)
```

### Issue 3: Audit Log Not Recording

**Symptoms:**
```
Queries not appearing in audit log
```

**Solutions:**
```python
# Check audit logger status
status = await audit.get_status()
print(f"Audit logging enabled: {status.enabled}")
print(f"Events logged today: {status.events_today}")

# Verify audit table exists
await audit.verify_audit_table()

# Re-enable logging
await audit.disable()
await audit.enable()

# Test logging manually
await audit.log_event({
    "operation": "TEST",
    "user": "test_user",
    "query": "SELECT 1",
    "timestamp": datetime.now()
})
```

### Issue 4: Multi-Tenancy Data Leakage

**Symptoms:**
```
User seeing data from wrong tenant
```

**Solutions:**
```python
# Verify tenant isolation
isolation_test = await tenancy.test_isolation(
    tenant1="acme_corp",
    tenant2="widgets_inc"
)

if not isolation_test.is_isolated:
    print("⚠️ Isolation breach detected!")
    print(f"  Leak points: {isolation_test.leak_points}")

# Force tenant context
tenant_executor.force_tenant_context(strict=True)

# Verify current tenant
current_tenant = tenant_executor.get_current_tenant()
print(f"Current tenant: {current_tenant}")

# Check for cross-tenant queries
cross_tenant_queries = await tenancy.find_cross_tenant_queries()
print(f"Cross-tenant queries found: {len(cross_tenant_queries)}")
```

### Issue 5: Security Monitor False Positives

**Symptoms:**
```
Legitimate queries being flagged as threats
```

**Solutions:**
```python
# Add whitelist rules
security_monitor.add_whitelist([
    {"user": "analytics_bot", "ip": "10.0.0.50"},
    {"pattern": "SELECT COUNT\\(\\*\\) FROM orders", "reason": "Daily report"},
])

# Adjust sensitivity
security_monitor.set_sensitivity("medium")  # low, medium, high

# Review false positives
false_positives = await security_monitor.get_false_positives(period="7d")
print(f"False positives: {len(false_positives)}")

# Auto-learn from false positives
await security_monitor.learn_from_false_positives(false_positives)
```

---

## Congratulations!

You've completed all three parts of the AI-Shell hands-on tutorial. You now have comprehensive knowledge of:

### Part 1: Basics
- ✓ Installation and setup
- ✓ Database connections
- ✓ Basic query execution
- ✓ Health checks
- ✓ Connection management
- ✓ Error handling

### Part 2: Advanced Queries
- ✓ Natural language to SQL
- ✓ 33 query patterns
- ✓ Query optimization
- ✓ Performance monitoring
- ✓ Slow query detection
- ✓ Query validation

### Part 3: Security & Enterprise
- ✓ SQL injection prevention
- ✓ Role-based access control
- ✓ Data encryption
- ✓ Audit logging
- ✓ Multi-tenancy
- ✓ Security monitoring

---

## Next Steps

### Advanced Topics
- Distributed databases
- Horizontal scaling
- Disaster recovery
- Performance tuning
- Custom security policies

### Integration
- CI/CD pipelines
- Kubernetes deployment
- Monitoring dashboards
- Alert management
- API development

### Certification
- AI-Shell Security Professional
- AI-Shell Performance Engineer
- AI-Shell Enterprise Architect

---

## Quick Reference

### Security Commands

```python
# SQL injection prevention
result = await secure_executor.execute(query, params)

# RBAC enforcement
rbac_executor.authenticate(username="alice")
result = await rbac_executor.execute(query)

# Encryption
result = await encrypted_executor.execute(query)

# Audit logging
audited_executor = AuditedExecutor(connector, audit)
result = await audited_executor.execute(query)

# Multi-tenancy
tenant_executor.set_tenant("acme_corp")
result = await tenant_executor.execute(query)

# Security monitoring
await security_monitor.start()
metrics = await security_monitor.get_metrics()
```

---

## Resources

- **Documentation:** https://ai-shell.readthedocs.io
- **Security Guide:** https://ai-shell.readthedocs.io/security
- **GitHub:** https://github.com/yourusername/ai-shell
- **Support:** support@ai-shell.io
- **Community:** https://discord.gg/ai-shell
- **Security Issues:** security@ai-shell.io

---

**Time to Complete:** 60 minutes
**Difficulty:** Intermediate
**Previous Tutorial:** Part 2 - NLP & Query Features
