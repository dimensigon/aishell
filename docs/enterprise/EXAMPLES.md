# Enterprise Feature Examples

## Multi-Tenancy Examples

### Creating and Managing Tenants

```python
from src.enterprise.tenancy import TenantManager, TenantTier

# Initialize manager
tenant_mgr = TenantManager()

# Create enterprise tenant
enterprise_tenant = tenant_mgr.create_tenant(
    name="Acme Corporation",
    slug="acme",
    owner_id="ceo@acme.com",
    tier=TenantTier.ENTERPRISE,
    contact_email="admin@acme.com",
    metadata={
        "industry": "Technology",
        "employees": 5000,
        "founded": 1995
    }
)

print(f"Created tenant: {enterprise_tenant.id}")
print(f"Features: {enterprise_tenant.features}")

# Update tenant
tenant_mgr.update_tenant(
    enterprise_tenant.id,
    max_users=500,
    max_databases=50
)

# List all active tenants
active_tenants = tenant_mgr.list_tenants(status=TenantStatus.ACTIVE)
print(f"Active tenants: {len(active_tenants)}")
```

### Resource Quota Management

```python
from src.enterprise.tenancy import ResourceQuotaManager, QuotaType

quota_mgr = ResourceQuotaManager()

# Set quotas for tenant
quota_mgr.set_quota(
    tenant_id="acme",
    quota_type=QuotaType.QUERIES_PER_HOUR,
    limit=10000,
    soft_limit=8000,  # Warning at 80%
    reset_period="hourly"
)

# Check if operation allowed
check = quota_mgr.check_quota(
    tenant_id="acme",
    quota_type=QuotaType.QUERIES_PER_HOUR,
    amount=1
)

if check['allowed']:
    # Consume quota
    quota_mgr.consume_quota("acme", QuotaType.QUERIES_PER_HOUR, 1)

    # Execute query
    execute_query()
else:
    print(f"Quota exceeded! {check['current_usage']}/{check['limit']}")
```

### Tenant Context Management

```python
from src.enterprise.tenancy import TenantMiddleware, with_tenant

middleware = TenantMiddleware()

# Resolve tenant from HTTP request
tenant_id = middleware.resolve_tenant(
    headers={'X-Tenant-ID': 'acme'},
    host='acme.example.com',
    path='/api/databases',
    base_domain='example.com'
)

# Set tenant context
TenantMiddleware.set_current_tenant(tenant_id)
TenantMiddleware.set_current_user('user@acme.com')

# Use decorator for tenant-specific operations
@with_tenant('acme')
def process_tenant_data():
    current_tenant = TenantMiddleware.get_current_tenant()
    print(f"Processing data for tenant: {current_tenant}")
    # ... tenant-specific logic

process_tenant_data()
```

## RBAC Examples

### Role Management

```python
from src.enterprise.rbac import RoleManager, RoleType

role_mgr = RoleManager()

# Create custom role
analyst_role = role_mgr.create_role(
    name="Senior Data Analyst",
    role_type=RoleType.CUSTOM,
    tenant_id="acme",
    description="Senior analyst with extended permissions",
    permissions=[
        "database:read",
        "database:execute",
        "query:create",
        "query:update",
        "report:*",  # Full report permissions
        "dashboard:read"
    ],
    parent_roles=["role_analyst"]  # Inherit from base analyst role
)

# Assign role to user
role_mgr.assign_role(
    user_id="john@acme.com",
    role_id=analyst_role.id,
    tenant_id="acme",
    assigned_by="admin@acme.com"
)

# Get user's roles
user_roles = role_mgr.get_user_roles("john@acme.com", "acme")
print(f"User has {len(user_roles)} roles")

# Get effective permissions (including inherited)
permissions = role_mgr.get_effective_permissions("john@acme.com", "acme")
print(f"Total permissions: {len(permissions)}")
```

### Permission Checking

```python
from src.enterprise.rbac import PermissionEngine

permission_engine = PermissionEngine()

# Get user permissions
user_permissions = role_mgr.get_effective_permissions("john@acme.com", "acme")

# Check single permission
if permission_engine.check_permission(user_permissions, "database:write"):
    print("✅ User can write to database")
else:
    print("❌ User cannot write to database")

# Check multiple permissions (all required)
if permission_engine.check_multiple_permissions(
    user_permissions,
    ["database:read", "database:execute"],
    require_all=True
):
    print("✅ User can read and execute queries")

# Get explanation of permission check
explanation = permission_engine.explain_permission_check(
    user_permissions,
    "report:create"
)
print(f"Permission granted: {explanation['granted']}")
print(f"Reason: {explanation['reason']}")

# Get all actions user can perform on a resource
actions = permission_engine.get_resource_permissions("database", user_permissions)
print(f"Database actions: {actions}")
```

### Policy-Based Access Control

```python
from src.enterprise.rbac import PolicyEvaluator, Policy, PolicyEffect

evaluator = PolicyEvaluator()

# Define conditional access policy
daytime_access = Policy(
    id="policy_daytime",
    name="Business Hours Access",
    effect=PolicyEffect.ALLOW,
    resources=["database:*"],
    actions=["write", "delete"],
    conditions={
        "time_of_day": "business_hours",
        "department": "engineering"
    },
    priority=10
)

# Evaluate policy with context
context = {
    "time_of_day": "business_hours",
    "department": "engineering",
    "ip_address": "10.0.0.5"
}

allowed = evaluator.evaluate(
    [daytime_access],
    resource="database:production",
    action="write",
    context=context
)

if allowed:
    print("✅ Policy allows access")
```

## Audit & Compliance Examples

### Audit Logging

```python
from src.enterprise.audit import AuditLogger, AuditLevel

audit = AuditLogger()

# Log user login
audit.log(
    action="user.login",
    resource="authentication",
    level=AuditLevel.INFO,
    tenant_id="acme",
    user_id="john@acme.com",
    details={
        "method": "saml_sso",
        "provider": "okta",
        "mfa_verified": True
    },
    ip_address="203.0.113.42",
    user_agent="Mozilla/5.0..."
)

# Log database query execution
audit.log(
    action="database.query",
    resource="customers_db",
    level=AuditLevel.INFO,
    tenant_id="acme",
    user_id="john@acme.com",
    details={
        "query": "SELECT COUNT(*) FROM customers",
        "execution_time_ms": 45,
        "rows_returned": 1
    }
)

# Log security event
audit.log(
    action="security.permission_denied",
    resource="admin_panel",
    level=AuditLevel.WARNING,
    tenant_id="acme",
    user_id="john@acme.com",
    details={
        "required_permission": "admin:access",
        "user_permissions": ["database:read", "query:execute"]
    },
    result="failure"
)

# Query audit logs
logs = audit.query(
    tenant_id="acme",
    user_id="john@acme.com",
    start_time="2025-10-01T00:00:00",
    end_time="2025-10-11T23:59:59",
    limit=100
)

print(f"Found {len(logs)} audit events")
```

### Compliance Reporting

```python
from src.enterprise.audit import ComplianceReporter, ComplianceFramework
from datetime import datetime, timedelta

reporter = ComplianceReporter(audit)

# Generate SOC 2 report for last quarter
soc2_report = reporter.generate_report(
    framework=ComplianceFramework.SOC2,
    start_date=datetime.now() - timedelta(days=90),
    end_date=datetime.now(),
    tenant_id="acme"
)

print("SOC 2 Compliance Report")
print(f"Period: {soc2_report['period']}")
print(f"Total events: {soc2_report['total_events']}")
print(f"Access control events: {soc2_report['access_controls']}")
print(f"Change management: {soc2_report['change_management']}")

# Generate GDPR report
gdpr_report = reporter.generate_report(
    framework=ComplianceFramework.GDPR,
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
    tenant_id="acme"
)

print("\nGDPR Compliance Report")
print(f"Data access events: {gdpr_report['data_access']}")
print(f"Deletion requests: {gdpr_report['data_deletion']}")

# Generate HIPAA report
hipaa_report = reporter.generate_report(
    framework=ComplianceFramework.HIPAA,
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now()
)

print("\nHIPAA Compliance Report")
print(f"PHI access events: {hipaa_report['phi_access']}")
```

### Change Tracking

```python
from src.enterprise.audit import ChangeTracker

tracker = ChangeTracker()

# Track schema change
tracker.track_change(
    change_type="schema",
    operation="ALTER",
    tenant_id="acme",
    user_id="admin@acme.com",
    table_name="users",
    sql_statement="ALTER TABLE users ADD COLUMN phone VARCHAR(20)",
    after_value={"column": "phone", "type": "VARCHAR(20)"}
)

# Track data update
tracker.track_change(
    change_type="data",
    operation="UPDATE",
    tenant_id="acme",
    user_id="john@acme.com",
    table_name="customers",
    before_value={"status": "active", "plan": "basic"},
    after_value={"status": "active", "plan": "professional"}
)

# Query changes for audit
changes = tracker.get_changes(
    tenant_id="acme",
    table_name="customers",
    start_time="2025-10-01T00:00:00",
    limit=50
)

for change in changes:
    print(f"{change['timestamp']}: {change['operation']} on {change['table_name']}")
```

## Cloud Integration Examples

### AWS Integration

```python
from src.enterprise.cloud import AWSIntegration, AWSConfig

# Configure AWS
aws_config = AWSConfig(
    region="us-east-1",
    access_key_id="AKIAIOSFODNN7EXAMPLE",
    secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
)

aws = AWSIntegration(aws_config)

# Get RDS connection string
rds_conn = aws.get_rds_connection_string(
    instance_identifier="aishell-prod",
    database_name="aishell_db",
    use_iam_auth=True
)

print(f"RDS Connection: {rds_conn}")

# Store secret in Secrets Manager
aws.store_secret(
    secret_name="aishell/prod/db_password",
    secret_value="super_secure_password",
    description="Production database password"
)

# Retrieve secret
db_password = aws.get_secret("aishell/prod/db_password")

# Upload backup to S3
with open("backup.db", "rb") as f:
    backup_data = f.read()

aws.upload_to_s3(
    bucket="aishell-backups",
    key="tenants/acme/backup_2025_10_11.db.gz",
    data=backup_data,
    metadata={"tenant": "acme", "type": "daily"}
)

# Send logs to CloudWatch
aws.send_cloudwatch_logs(
    log_group="/aishell/production",
    log_stream="audit",
    messages=[
        {"timestamp": "2025-10-11T10:00:00", "message": "System started"},
        {"timestamp": "2025-10-11T10:01:00", "message": "Connected to database"}
    ]
)
```

### Cloud Backup Management

```python
from src.enterprise.cloud import CloudBackupManager, BackupConfig, CloudProvider

# Configure backup
backup_config = BackupConfig(
    provider=CloudProvider.AWS,
    schedule="0 2 * * *",  # Daily at 2 AM
    retention_days=30,
    compression=True,
    encryption=True
)

backup_mgr = CloudBackupManager(
    config=backup_config,
    aws_integration=aws
)

# Create backup
backup_id = backup_mgr.create_backup(
    tenant_id="acme",
    database_path="/var/lib/aishell/tenants/acme.db",
    metadata={
        "type": "daily",
        "triggered_by": "scheduled"
    }
)

print(f"Backup created: {backup_id}")

# List backups
backups = backup_mgr.list_backups("acme")
for backup in backups:
    print(f"Backup: {backup['id']} - {backup['created_at']}")

# Restore backup
success = backup_mgr.restore_backup(
    backup_id=backup_id,
    tenant_id="acme",
    restore_path="/var/lib/aishell/restore/acme.db"
)

if success:
    print("✅ Backup restored successfully")

# Cleanup old backups
deleted = backup_mgr.cleanup_old_backups("acme")
print(f"Deleted {deleted} old backups")
```

## Complete Workflow Example

```python
"""
Complete enterprise workflow demonstrating all features
"""

from src.enterprise import (
    TenantManager, TenantTier,
    RoleManager, RoleType, PermissionEngine,
    AuditLogger, AuditLevel,
    AWSIntegration, CloudBackupManager
)

# 1. Create tenant
tenant_mgr = TenantManager()
tenant = tenant_mgr.create_tenant(
    name="Acme Corp",
    slug="acme",
    owner_id="ceo@acme.com",
    tier=TenantTier.ENTERPRISE
)
print(f"✅ Created tenant: {tenant.name}")

# 2. Set up RBAC
role_mgr = RoleManager()
analyst_role = role_mgr.create_role(
    name="Data Analyst",
    role_type=RoleType.ANALYST,
    tenant_id=tenant.id
)

role_mgr.assign_role("john@acme.com", analyst_role.id, tenant.id)
print(f"✅ Assigned role to user")

# 3. Check permissions
permission_engine = PermissionEngine()
user_perms = role_mgr.get_effective_permissions("john@acme.com", tenant.id)

if permission_engine.check_permission(user_perms, "database:read"):
    print("✅ User has database read permission")

    # 4. Log access
    audit = AuditLogger()
    audit.log(
        action="database.access",
        resource="production_db",
        level=AuditLevel.INFO,
        tenant_id=tenant.id,
        user_id="john@acme.com"
    )
    print("✅ Audit log created")

# 5. Set up cloud backup
aws = AWSIntegration()
backup_mgr = CloudBackupManager(aws_integration=aws)

backup_id = backup_mgr.create_backup(
    tenant_id=tenant.id,
    database_path=f"/data/{tenant.id}.db"
)
print(f"✅ Backup created: {backup_id}")

print("\n🎉 Enterprise workflow completed successfully!")
```

## Testing Examples

```python
"""
Test your enterprise implementation
"""

import pytest
from src.enterprise import TenantManager, RoleManager

def test_tenant_creation():
    """Test tenant creation workflow"""
    mgr = TenantManager(db_path=":memory:")

    tenant = mgr.create_tenant(
        name="Test Corp",
        slug="test",
        owner_id="test@example.com"
    )

    assert tenant.id is not None
    assert tenant.is_active()
    print("✅ Tenant creation test passed")

def test_permission_checking():
    """Test permission system"""
    from src.enterprise.rbac import PermissionEngine

    engine = PermissionEngine()
    user_perms = {"database:*"}

    assert engine.check_permission(user_perms, "database:read")
    assert engine.check_permission(user_perms, "database:write")
    print("✅ Permission checking test passed")

if __name__ == "__main__":
    test_tenant_creation()
    test_permission_checking()
    print("\n🎉 All tests passed!")
```

## Production Deployment Example

```bash
#!/bin/bash
# deploy-enterprise.sh

# Set environment
export ENV=production
export DB_HOST=prod-db.example.com
export DB_NAME=aishell_prod
export CLOUD_PROVIDER=aws
export AWS_REGION=us-east-1

# Initialize database
python -m src.enterprise.scripts.init_database

# Create system roles
python -m src.enterprise.scripts.init_roles

# Create first tenant
python -m src.enterprise.scripts.create_tenant \
    --name "Acme Corporation" \
    --slug "acme" \
    --tier enterprise \
    --owner "admin@acme.com"

# Configure backups
python -m src.enterprise.scripts.configure_backups \
    --provider aws \
    --schedule "0 2 * * *" \
    --retention-days 30

# Start application
gunicorn -w 4 -b 0.0.0.0:8000 src.main:app

echo "✅ Enterprise deployment complete"
```

## Monitoring Example

```python
"""
Monitor enterprise metrics
"""

from src.enterprise import TenantManager, ResourceQuotaManager, AuditLogger

# Get system statistics
tenant_mgr = TenantManager()
stats = tenant_mgr.get_stats()

print("System Statistics:")
print(f"Total tenants: {stats['total_tenants']}")
print(f"Active tenants: {stats['active_tenants']}")
print(f"Enterprise tier: {stats['enterprise_tier_tenants']}")

# Check quota usage
quota_mgr = ResourceQuotaManager()
quotas = quota_mgr.get_all_quotas("acme")

for quota in quotas:
    usage_pct = quota.percentage_used()
    print(f"{quota.quota_type.value}: {usage_pct:.1f}% used")

# Audit statistics
audit = AuditLogger()
audit_stats = audit.get_statistics("acme")

for stat in audit_stats:
    print(f"{stat['level']}: {stat['total']} events")
```
