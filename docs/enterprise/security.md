# Security Architecture

## Overview

AI-Shell Enterprise implements defense-in-depth security with multiple layers of protection for data, access control, and compliance.

## Security Principles

1. **Least Privilege**: Users and services have minimum necessary permissions
2. **Defense in Depth**: Multiple security layers
3. **Zero Trust**: Verify every request
4. **Encryption Everywhere**: Data encrypted at rest and in transit
5. **Audit Everything**: Comprehensive logging of all actions

## Authentication & Authorization

### Multi-Factor Authentication (MFA)

```python
from src.enterprise.security.mfa import MFAManager

mfa = MFAManager()

# Enable MFA for user
secret = mfa.generate_secret("user_1")

# Verify TOTP code
valid = mfa.verify_totp("user_1", "123456")
```

### OAuth 2.0 / OpenID Connect

Support for enterprise SSO providers:

```yaml
oauth:
  providers:
    - name: okta
      client_id: ${OKTA_CLIENT_ID}
      client_secret: ${OKTA_CLIENT_SECRET}
      authorization_url: https://company.okta.com/oauth2/v1/authorize
      token_url: https://company.okta.com/oauth2/v1/token
```

### RBAC Configuration

```python
from src.enterprise.rbac import RoleManager, PermissionEngine

# Create custom role with specific permissions
role_manager.create_role(
    name="Data Analyst",
    permissions=[
        "database:read",
        "query:execute",
        "query:history",
        "report:create"
    ],
    tenant_id="acme_corp"
)

# Assign role to user
role_manager.assign_role("user_123", "role_analyst", "acme_corp")
```

### Permission Examples

```python
# Check specific permission
if permission_engine.check_permission(
    user_permissions,
    "database:write",
    context={"tenant_id": "acme_corp"}
):
    # Allow write operation
    pass

# Check multiple permissions (all required)
if permission_engine.check_multiple_permissions(
    user_permissions,
    ["database:read", "database:schema"],
    require_all=True
):
    # Allow schema access
    pass
```

## Data Security

### Encryption at Rest

All sensitive data is encrypted using Fernet (symmetric encryption):

```python
from src.enterprise.security.vault import SecureVault

vault = SecureVault(
    master_password="your_secure_master_password",
    auto_redact=True
)

# Store credentials
vault.store_credential(
    name="production_db",
    credential_type=CredentialType.DATABASE,
    data={
        "host": "db.example.com",
        "username": "app_user",
        "password": "secure_password"
    }
)
```

### Encryption in Transit

All network communications use TLS 1.2+:

```nginx
# nginx SSL configuration
server {
    listen 443 ssl http2;
    server_name aishell.example.com;

    ssl_certificate /etc/ssl/certs/aishell.crt;
    ssl_certificate_key /etc/ssl/private/aishell.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
}
```

### Database Encryption

PostgreSQL configuration:

```sql
-- Enable encryption
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = '/path/to/server.crt';
ALTER SYSTEM SET ssl_key_file = '/path/to/server.key';

-- Require SSL for connections
ALTER USER aishell_user SET ssl=on;
```

### Secrets Management

#### AWS Secrets Manager

```python
from src.enterprise.cloud.aws_integration import AWSIntegration

aws = AWSIntegration(config)

# Store secret
aws.store_secret(
    secret_name="aishell/production/db_password",
    secret_value="super_secure_password",
    description="Production database password"
)

# Retrieve secret
password = aws.get_secret("aishell/production/db_password")
```

#### Azure Key Vault

```python
from src.enterprise.cloud.azure_integration import AzureIntegration

azure = AzureIntegration(config)

# Store secret
azure.store_secret(
    vault_name="aishell-vault",
    secret_name="db-password",
    secret_value="super_secure_password"
)
```

## Tenant Isolation

### Database Isolation Strategies

#### 1. Database per Tenant (Highest Security)

```python
manager = TenantDatabaseManager(
    isolation_strategy=IsolationStrategy.DATABASE_PER_TENANT
)

# Each tenant gets completely separate database
schema = manager.create_tenant_database("tenant_1")
# Creates: tenant_1.db (SQLite) or tenant_1 database (PostgreSQL)
```

#### 2. Schema per Tenant (Balanced)

```python
manager = TenantDatabaseManager(
    isolation_strategy=IsolationStrategy.SCHEMA_PER_TENANT
)

# Each tenant gets separate schema in shared database
schema = manager.create_tenant_database("tenant_1")
# Creates: schema tenant_1 in shared database
```

#### 3. Shared Database with Row-level Security (Most Efficient)

```python
manager = TenantDatabaseManager(
    isolation_strategy=IsolationStrategy.SHARED_DATABASE
)

# All tenants share database, isolated by tenant_id column
# Queries automatically filtered
```

PostgreSQL Row-Level Security:

```sql
-- Enable RLS
ALTER TABLE queries ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY tenant_isolation ON queries
    USING (tenant_id = current_setting('app.tenant_id')::text);

-- Set tenant context
SET app.tenant_id = 'tenant_1';
```

## Audit & Compliance

### Comprehensive Audit Logging

```python
from src.enterprise.audit import AuditLogger, AuditLevel

audit_logger = AuditLogger()

# Log security event
audit_logger.log(
    action="user.login",
    resource="authentication",
    level=AuditLevel.INFO,
    tenant_id="acme_corp",
    user_id="user_123",
    details={
        "method": "password",
        "mfa_verified": True,
        "ip_address": "203.0.113.1"
    },
    ip_address="203.0.113.1",
    user_agent="Mozilla/5.0..."
)

# Log failed access attempt
audit_logger.log(
    action="database.access_denied",
    resource="database_123",
    level=AuditLevel.WARNING,
    tenant_id="acme_corp",
    user_id="user_123",
    details={
        "reason": "insufficient_permissions",
        "required_permission": "database:admin"
    },
    result="failure"
)
```

### Compliance Reporting

```python
from src.enterprise.audit import ComplianceReporter, ComplianceFramework
from datetime import datetime, timedelta

reporter = ComplianceReporter(audit_logger)

# Generate SOC 2 report
report = reporter.generate_report(
    framework=ComplianceFramework.SOC2,
    start_date=datetime.now() - timedelta(days=90),
    end_date=datetime.now(),
    tenant_id="acme_corp"
)

print(report['access_controls'])
print(report['change_management'])
print(report['monitoring'])
```

### GDPR Compliance

```python
# Data export (Right to Access)
def export_user_data(user_id: str) -> dict:
    return {
        "profile": get_user_profile(user_id),
        "queries": get_user_queries(user_id),
        "audit_trail": audit_logger.query(user_id=user_id),
    }

# Data deletion (Right to Erasure)
def delete_user_data(user_id: str):
    # Anonymize audit logs
    anonymize_audit_logs(user_id)

    # Delete user data
    delete_user_profile(user_id)
    delete_user_queries(user_id)

    # Log deletion
    audit_logger.log(
        action="user.data_deleted",
        resource="user_data",
        level=AuditLevel.INFO,
        details={"user_id": user_id, "reason": "gdpr_request"}
    )
```

## Network Security

### Firewall Rules

```bash
# Allow only necessary ports
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw enable
```

### IP Whitelisting

```python
# Configure IP whitelist
allowed_ips = [
    "203.0.113.0/24",    # Office network
    "198.51.100.1",      # VPN gateway
]

# In middleware
def check_ip_whitelist(request):
    client_ip = request.headers.get("X-Real-IP")
    if not is_ip_allowed(client_ip, allowed_ips):
        raise PermissionError("IP not whitelisted")
```

### Rate Limiting

```python
from src.enterprise.security.rate_limiter import RateLimiter

rate_limiter = RateLimiter()

# Configure limits
rate_limiter.set_limit(
    identifier="user_123",
    limit=100,
    window=3600  # 100 requests per hour
)

# Check before processing request
if not rate_limiter.check("user_123"):
    raise TooManyRequestsError()
```

## API Security

### API Key Management

```python
from src.enterprise.security.api_keys import APIKeyManager

api_key_manager = APIKeyManager()

# Generate API key
api_key = api_key_manager.create_key(
    user_id="user_123",
    tenant_id="acme_corp",
    permissions=["database:read", "query:execute"],
    expires_in_days=90
)

# Validate API key
is_valid = api_key_manager.validate_key(api_key)
```

### Request Signing

```python
import hmac
import hashlib

def sign_request(payload: str, secret: str) -> str:
    """Generate HMAC signature for request"""
    return hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

def verify_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify request signature"""
    expected = sign_request(payload, secret)
    return hmac.compare_digest(expected, signature)
```

## Security Monitoring

### Anomaly Detection

```python
from src.enterprise.security.anomaly_detector import AnomalyDetector

detector = AnomalyDetector()

# Analyze user behavior
anomaly_score = detector.analyze_user_activity(
    user_id="user_123",
    activities=recent_activities
)

if anomaly_score > 0.8:
    # Trigger alert
    send_security_alert(
        "Unusual activity detected",
        user_id="user_123",
        score=anomaly_score
    )
```

### Security Alerts

```python
# Configure alerts
alerts = {
    "failed_login_threshold": 5,
    "suspicious_query_patterns": [
        "DROP TABLE",
        "DELETE FROM .* WHERE 1=1"
    ],
    "unusual_access_hours": {
        "start": "22:00",
        "end": "06:00"
    }
}

# Monitor and alert
def check_security_events():
    # Check failed logins
    failed_logins = count_failed_logins(last_hour)
    if failed_logins > alerts['failed_login_threshold']:
        send_alert("Multiple failed login attempts")

    # Check for suspicious queries
    recent_queries = get_recent_queries()
    for query in recent_queries:
        for pattern in alerts['suspicious_query_patterns']:
            if re.search(pattern, query, re.IGNORECASE):
                send_alert(f"Suspicious query detected: {query}")
```

## Incident Response

### Security Incident Procedure

1. **Detection**: Automated alerts or manual reporting
2. **Containment**: Isolate affected systems
3. **Investigation**: Analyze audit logs and system state
4. **Remediation**: Fix vulnerability
5. **Recovery**: Restore normal operations
6. **Post-mortem**: Document and improve

### Incident Response Playbook

```python
from src.enterprise.security.incident_response import IncidentManager

incident_mgr = IncidentManager()

# Create incident
incident = incident_mgr.create_incident(
    severity="high",
    type="unauthorized_access",
    description="Suspicious access to tenant database",
    affected_tenants=["tenant_1"]
)

# Lock affected accounts
incident_mgr.lock_accounts(incident.id)

# Notify stakeholders
incident_mgr.notify(
    incident.id,
    channels=["email", "slack", "pagerduty"]
)

# Document investigation
incident_mgr.add_note(
    incident.id,
    "Found SQL injection attempt in query parameter"
)

# Resolve incident
incident_mgr.resolve(
    incident.id,
    resolution="Patched vulnerability, no data compromised"
)
```

## Security Best Practices

### Development

- ✅ Use parameterized queries (prevent SQL injection)
- ✅ Validate and sanitize all inputs
- ✅ Keep dependencies updated
- ✅ Code review for security issues
- ✅ Run security scans (SAST/DAST)

### Operations

- ✅ Principle of least privilege
- ✅ Regular security audits
- ✅ Automated patch management
- ✅ Backup encryption
- ✅ Disaster recovery testing

### Compliance

- ✅ Regular compliance audits
- ✅ Security awareness training
- ✅ Incident response drills
- ✅ Documentation and policies
- ✅ Third-party security assessments

## Security Checklist

### Pre-Production

- [ ] SSL/TLS certificates configured
- [ ] Firewall rules configured
- [ ] Database encryption enabled
- [ ] Secrets in vault (not in code)
- [ ] Authentication configured
- [ ] RBAC roles defined
- [ ] Audit logging enabled
- [ ] Backup encryption enabled
- [ ] Security scanning completed
- [ ] Penetration testing completed

### Ongoing

- [ ] Weekly security updates
- [ ] Monthly access reviews
- [ ] Quarterly penetration testing
- [ ] Annual compliance audits
- [ ] Continuous monitoring
- [ ] Regular backup testing

## Security Contacts

- **Security Team**: security@aishell.example.com
- **Vulnerability Reports**: security-vulns@aishell.example.com
- **Security Incidents**: +1-555-SECURITY (24/7)
- **Bug Bounty**: https://aishell.example.com/security/bounty

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [SOC 2 Compliance](https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/soc2.html)
