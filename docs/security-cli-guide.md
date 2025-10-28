# Security CLI Guide

Comprehensive security command interface for AI-Shell, exposing 15 security modules via CLI.

## Table of Contents

1. [Overview](#overview)
2. [Vault Commands](#vault-commands)
3. [Audit Log Commands](#audit-log-commands)
4. [RBAC Commands](#rbac-commands)
5. [Security Scanning](#security-scanning)
6. [Best Practices](#best-practices)
7. [Examples](#examples)

## Overview

The Security CLI provides enterprise-grade security features:

- **Vault**: Encrypted credential storage
- **Audit**: Comprehensive audit trail
- **RBAC**: Role-based access control
- **Scanning**: Vulnerability detection
- **Compliance**: GDPR, SOX, HIPAA checking

## Vault Commands

### Add Credential

Store a credential securely in the vault:

```bash
# Basic storage
ai-shell vault add my-key "secret-value"

# With encryption
ai-shell vault add api-key "sk-12345" --encrypt

# Database credential
ai-shell vault add db-prod "postgresql://user:pass@host:5432/db" --encrypt
```

### List Credentials

View all stored credentials:

```bash
# List with redacted values
ai-shell vault list

# Show actual values (use carefully!)
ai-shell vault list --show-passwords

# Export as JSON
ai-shell vault list --format json > vault-backup.json
```

### Get Credential

Retrieve a specific credential:

```bash
ai-shell vault get my-key
ai-shell vault get db-prod
```

### Remove Credential

Delete a credential from the vault:

```bash
ai-shell vault remove old-key
ai-shell vault remove deprecated-api-key
```

### Encryption Utilities

Encrypt and decrypt values:

```bash
# Encrypt a value
ai-shell vault encrypt "sensitive-data"
# Output: gAAAAABh...encrypted-string

# Decrypt a value
ai-shell vault decrypt "gAAAAABh...encrypted-string"
# Output: sensitive-data
```

### Rotate Encryption Key

Rotate the vault's master encryption key:

```bash
ai-shell vault rotate-key
```

**Warning**: This re-encrypts all credentials. Ensure you have backups!

## Audit Log Commands

### View Audit Logs

Display security audit trail:

```bash
# Show recent logs
ai-shell audit show

# Limit results
ai-shell audit show --limit 50

# Filter by user
ai-shell audit show --user admin

# Filter by action
ai-shell audit show --action login

# Filter by resource
ai-shell audit show --resource database

# Combine filters
ai-shell audit show --user admin --action login --limit 10
```

### Export Audit Logs

Export logs for compliance:

```bash
# Export as JSON
ai-shell audit export audit-logs.json --format json

# Export as CSV
ai-shell audit export audit-logs.csv --format csv

# Export date range
ai-shell audit export logs.json --start 2024-01-01 --end 2024-12-31
```

### Clear Old Logs

Remove logs older than specified date:

```bash
# Clear logs before date
ai-shell audit clear --before 2024-01-01

# Clear logs older than 90 days
ai-shell audit clear --before $(date -d '90 days ago' +%Y-%m-%d)
```

### Audit Statistics

View audit log statistics:

```bash
ai-shell audit stats
```

Output:
```
📊 Audit Log Statistics:

  Total Logs: 1,542
  Retention Days: 90
  Unique Users: 23
  Unique Actions: 15
  Oldest Log: 2024-01-15T10:30:00Z
  Newest Log: 2024-03-15T14:22:00Z
```

### Search Audit Logs

Search logs by keyword:

```bash
ai-shell audit search "failed login"
ai-shell audit search "unauthorized access"
```

## RBAC Commands

### Role Management

Create and manage roles:

```bash
# Create role
ai-shell role create admin --description "Administrator role"
ai-shell role create editor --description "Content editor"
ai-shell role create viewer --description "Read-only access"

# Delete role
ai-shell role delete deprecated-role

# List all roles
ai-shell permissions list
```

### Grant Permissions

Grant permissions to roles:

```bash
# Single action
ai-shell permissions grant admin database --actions read

# Multiple actions
ai-shell permissions grant editor api --actions read,write

# Wildcard permissions
ai-shell permissions grant admin * --actions read,write,delete

# Resource-specific
ai-shell permissions grant viewer users --actions read
ai-shell permissions grant editor posts --actions read,write
```

### Revoke Permissions

Remove permissions from roles:

```bash
ai-shell permissions revoke editor api
ai-shell permissions revoke viewer sensitive-data
```

### User Role Assignment

Assign and unassign roles to users:

```bash
# Assign role
ai-shell role assign john.doe admin
ai-shell role assign jane.smith editor

# Unassign role
ai-shell role unassign john.doe admin

# List user roles
ai-shell permissions list john.doe
```

### Check Permissions

Verify if a user has permission:

```bash
ai-shell permissions check john.doe database read
# Output: ✅ Permission GRANTED or ❌ Permission DENIED

ai-shell permissions check jane.smith api write
ai-shell permissions check guest.user admin-panel access
```

### List Permissions

View permissions for users or roles:

```bash
# List user permissions
ai-shell permissions list john.doe

# List all roles
ai-shell permissions list

# Export as JSON
ai-shell permissions list john.doe --format json
```

## Security Scanning

### Run Security Scan

Perform comprehensive security scan:

```bash
# Basic scan
ai-shell security scan

# Deep scan (more thorough)
ai-shell security scan --deep

# Export report
ai-shell security scan --output security-report.json
```

### Generate Security Report

Create detailed security report:

```bash
# Table format
ai-shell security report

# JSON format
ai-shell security report --format json

# Save to file
ai-shell security report --format json > security-$(date +%Y%m%d).json
```

### List Vulnerabilities

Show known vulnerabilities:

```bash
ai-shell security vulnerabilities
```

Output:
```
⚠️  Known Vulnerabilities:

  1. SQL Injection - Check SQL guard configuration
  2. Path Traversal - Validate file paths
  3. PII Exposure - Enable PII redaction
  4. Command Injection - Sanitize shell commands
  5. Rate Limiting - Configure rate limits
```

### Compliance Checking

Check compliance with standards:

```bash
# Check all standards
ai-shell security compliance

# Check specific standard
ai-shell security compliance --standard gdpr
ai-shell security compliance --standard sox
ai-shell security compliance --standard hipaa

# Export compliance report
ai-shell security compliance --format json > compliance-report.json
```

## Best Practices

### Vault Security

1. **Use Strong Master Password**
   ```bash
   export VAULT_PASSWORD="$(openssl rand -base64 32)"
   ```

2. **Rotate Keys Regularly**
   ```bash
   # Rotate every 90 days
   ai-shell vault rotate-key
   ```

3. **Backup Vault**
   ```bash
   ai-shell vault list --format json > vault-backup-$(date +%Y%m%d).json
   ```

4. **Never Show Passwords in Logs**
   ```bash
   # Always use redacted output
   ai-shell vault list  # Don't use --show-passwords
   ```

### Audit Log Best Practices

1. **Regular Exports**
   ```bash
   # Weekly export
   ai-shell audit export weekly-audit-$(date +%Y%m%d).json
   ```

2. **Monitor Failed Logins**
   ```bash
   ai-shell audit show --action "failed_login" --limit 100
   ```

3. **Track Privileged Actions**
   ```bash
   ai-shell audit show --user admin --action delete
   ```

4. **Set Retention Policy**
   ```bash
   # Clear logs older than 90 days
   ai-shell audit clear --before $(date -d '90 days ago' +%Y-%m-%d)
   ```

### RBAC Best Practices

1. **Principle of Least Privilege**
   ```bash
   # Grant minimal permissions needed
   ai-shell permissions grant viewer users --actions read
   ```

2. **Regular Permission Audits**
   ```bash
   # Review all user permissions monthly
   for user in $(list-users); do
     ai-shell permissions list $user
   done
   ```

3. **Separate Admin Roles**
   ```bash
   ai-shell role create super-admin --description "Full system access"
   ai-shell role create db-admin --description "Database administration"
   ai-shell role create user-admin --description "User management"
   ```

4. **Document Role Hierarchy**
   ```bash
   ai-shell permissions list --format json > roles-$(date +%Y%m%d).json
   ```

### Security Scanning Best Practices

1. **Regular Scans**
   ```bash
   # Daily security scan
   ai-shell security scan --deep --output daily-scan-$(date +%Y%m%d).json
   ```

2. **Monitor Vulnerabilities**
   ```bash
   ai-shell security vulnerabilities | mail -s "Security Alert" security@company.com
   ```

3. **Compliance Checks**
   ```bash
   # Monthly compliance check
   ai-shell security compliance --format json > compliance-$(date +%Y%m).json
   ```

4. **Automated Remediation**
   ```bash
   # Run scan and alert on issues
   if ai-shell security scan | grep -q "critical"; then
     echo "Critical vulnerabilities found!" | mail -s "URGENT: Security Alert" security@company.com
   fi
   ```

## Examples

### Example 1: Secure Database Setup

Complete workflow for securing a database connection:

```bash
# Store encrypted database credential
ai-shell vault add prod-db "postgresql://user:pass@prod.db:5432/myapp" --encrypt

# Create database admin role
ai-shell role create db-admin --description "Database administrator"

# Grant database permissions
ai-shell permissions grant db-admin database --actions read,write,delete
ai-shell permissions grant db-admin backups --actions read,write

# Assign role to DBA
ai-shell role assign john.dba db-admin

# Verify permissions
ai-shell permissions check john.dba database write

# Audit database access
ai-shell audit show --resource database --limit 50
```

### Example 2: API Key Management

Manage API keys securely:

```bash
# Store API keys
ai-shell vault add stripe-key "sk_live_..." --encrypt
ai-shell vault add sendgrid-key "SG...." --encrypt
ai-shell vault add aws-key "AKIA..." --encrypt

# Create API role
ai-shell role create api-user --description "API access"
ai-shell permissions grant api-user api --actions read,write

# List all API keys (redacted)
ai-shell vault list | grep key

# Rotate keys quarterly
ai-shell vault rotate-key
```

### Example 3: User Access Management

Complete user access control:

```bash
# Create roles
ai-shell role create admin
ai-shell role create editor
ai-shell role create viewer

# Grant permissions
ai-shell permissions grant admin * --actions read,write,delete
ai-shell permissions grant editor content --actions read,write
ai-shell permissions grant viewer content --actions read

# Assign roles
ai-shell role assign alice admin
ai-shell role assign bob editor
ai-shell role assign charlie viewer

# Verify access
ai-shell permissions check alice content delete    # ✅ GRANTED
ai-shell permissions check bob content delete      # ❌ DENIED
ai-shell permissions check charlie content write   # ❌ DENIED

# Audit user actions
ai-shell audit show --user alice
ai-shell audit show --user bob --action write
```

### Example 4: Compliance Reporting

Generate compliance reports:

```bash
# Run comprehensive security scan
ai-shell security scan --deep --output security-report.json

# Check all compliance standards
ai-shell security compliance --format json > compliance-report.json

# Export audit logs for SOX compliance
ai-shell audit export sox-audit-$(date +%Y%m).csv --format csv

# Generate monthly security report
cat << EOF > monthly-report.md
# Security Report - $(date +%B\ %Y)

## Security Scan Results
$(ai-shell security scan)

## Compliance Status
$(ai-shell security compliance)

## Audit Summary
$(ai-shell audit stats)

## Vulnerabilities
$(ai-shell security vulnerabilities)
EOF
```

### Example 5: Automated Security Pipeline

CI/CD security checks:

```bash
#!/bin/bash
# security-check.sh

set -e

echo "🔒 Running security checks..."

# 1. Scan for vulnerabilities
echo "→ Scanning for vulnerabilities..."
if ! ai-shell security scan --deep --output scan-results.json; then
  echo "❌ Security scan failed!"
  exit 1
fi

# 2. Check compliance
echo "→ Checking compliance..."
ai-shell security compliance --format json > compliance.json

# 3. Verify critical permissions
echo "→ Verifying permissions..."
if ai-shell permissions check deploy-user production write; then
  echo "✅ Deploy permissions verified"
else
  echo "❌ Insufficient permissions"
  exit 1
fi

# 4. Audit log check
echo "→ Checking audit logs..."
FAILED_LOGINS=$(ai-shell audit show --action failed_login --limit 100 | wc -l)
if [ $FAILED_LOGINS -gt 10 ]; then
  echo "⚠️  High number of failed logins detected!"
fi

# 5. Vault integrity check
echo "→ Verifying vault..."
ai-shell vault list > /dev/null

echo "✅ All security checks passed!"
```

## Environment Variables

Configure security CLI behavior:

```bash
# Vault password (required)
export VAULT_PASSWORD="your-strong-password"

# Audit log location
export AUDIT_LOG_PATH="/var/log/aishell/audit.log"

# Python interpreter
export PYTHON_PATH="/usr/bin/python3"

# Security scan depth
export SECURITY_SCAN_DEEP=true

# Compliance standards to check
export COMPLIANCE_STANDARDS="gdpr,sox,hipaa"
```

## Troubleshooting

### Common Issues

1. **Vault Not Found**
   ```bash
   # Initialize vault
   mkdir -p .vault
   export VAULT_PASSWORD="your-password"
   ai-shell vault add test "value"
   ```

2. **Python Script Fails**
   ```bash
   # Check Python installation
   python3 --version

   # Install dependencies
   pip install cryptography
   ```

3. **Permission Denied**
   ```bash
   # Fix file permissions
   chmod 700 .vault
   chmod 600 .vault/credentials.vault
   ```

4. **Audit Log Too Large**
   ```bash
   # Clear old logs
   ai-shell audit clear --before $(date -d '30 days ago' +%Y-%m-%d)
   ```

## Security Considerations

1. **Master Password**: Store vault password in secure location (e.g., AWS Secrets Manager, HashiCorp Vault)
2. **File Permissions**: Ensure vault files have 600 permissions (owner read/write only)
3. **Audit Logs**: Regularly export and backup audit logs
4. **Key Rotation**: Rotate vault keys every 90 days
5. **Access Control**: Use RBAC to limit who can access security commands
6. **Compliance**: Run regular compliance checks
7. **Monitoring**: Set up alerts for failed authentication attempts

## Integration with Other Tools

### HashiCorp Vault

```bash
# Store vault password in Vault
vault kv put secret/aishell/vault password="$(ai-shell vault encrypt 'master-password')"

# Retrieve in scripts
export VAULT_PASSWORD=$(vault kv get -field=password secret/aishell/vault | ai-shell vault decrypt)
```

### AWS Secrets Manager

```bash
# Store in AWS
aws secretsmanager create-secret \
  --name aishell/vault-password \
  --secret-string "$(ai-shell vault encrypt 'master-password')"

# Retrieve
export VAULT_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id aishell/vault-password \
  --query SecretString \
  --output text | ai-shell vault decrypt)
```

### Datadog Monitoring

```bash
# Send security events to Datadog
ai-shell audit show --format json | \
  curl -X POST "https://api.datadoghq.com/api/v1/events" \
    -H "DD-API-KEY: ${DD_API_KEY}" \
    -d @-
```

## Additional Resources

- [Security Module Documentation](../src/security/README.md)
- [RBAC Implementation](../src/security/rbac.py)
- [Audit Logging](../src/security/audit.py)
- [Vault Implementation](../src/security/vault.py)
- [Compliance Checking](../src/security/compliance.py)

## Support

For security-related issues or questions:

- GitHub Issues: https://github.com/yourusername/aishell/issues
- Security Email: security@aishell.io
- Documentation: https://docs.aishell.io/security
