# Security Commands Reference

**AI-Shell Security CLI - Complete Command Reference**

This document provides a comprehensive reference for all security-related CLI commands in AI-Shell.

---

## Table of Contents

1. [Vault Management](#vault-management)
2. [Role-Based Access Control (RBAC)](#role-based-access-control-rbac)
3. [Audit Logging](#audit-logging)
4. [Encryption Utilities](#encryption-utilities)
5. [Security Operations](#security-operations)
6. [Examples](#examples)

---

## Vault Management

Secure credential storage with AES-256 encryption.

### `vault add`

Add a new credential to the vault.

**Usage:**
```bash
ai-shell vault add <name> <value> [options]
```

**Arguments:**
- `<name>` - Unique identifier for the credential
- `<value>` - The credential value to store

**Options:**
- `--encrypt` - Enable encryption for this credential (default: true)

**Examples:**
```bash
# Add encrypted database password
ai-shell vault add database-prod "mySecretPassword123!" --encrypt

# Add API key
ai-shell vault add openai-api-key "sk-1234567890abcdef"
```

---

### `vault list`

List all credentials in the vault.

**Usage:**
```bash
ai-shell vault list [options]
```

**Options:**
- `--show-passwords` - Display actual credential values (default: false, shows redacted)
- `--format <format>` - Output format: json, table, csv (default: table)

**Examples:**
```bash
# List all credentials (redacted)
ai-shell vault list

# List with actual values (use with caution)
ai-shell vault list --show-passwords

# Export as JSON
ai-shell vault list --format json
```

---

### `vault get`

Retrieve a specific credential from the vault.

**Usage:**
```bash
ai-shell vault get <name>
```

**Arguments:**
- `<name>` - Name of the credential to retrieve

**Examples:**
```bash
# Get database password
ai-shell vault get database-prod
```

---

### `vault delete`

Delete a credential from the vault.

**Usage:**
```bash
ai-shell vault delete <name>
```

**Arguments:**
- `<name>` - Name of the credential to delete

**Examples:**
```bash
# Delete old API key
ai-shell vault delete old-api-key
```

---

### `vault search`

Search for credentials by name or metadata.

**Usage:**
```bash
ai-shell vault search <query>
```

**Arguments:**
- `<query>` - Search term to match against credential names and metadata

**Examples:**
```bash
# Search for database credentials
ai-shell vault search "database"

# Search for production credentials
ai-shell vault search "prod"
```

---

### `vault import`

Bulk import credentials from a JSON file.

**Usage:**
```bash
ai-shell vault import <file>
```

**Arguments:**
- `<file>` - Path to JSON file containing credentials

**File Format:**
```json
[
  {
    "name": "credential-name",
    "value": "credential-value",
    "encrypt": true,
    "metadata": {
      "environment": "production",
      "service": "database"
    }
  }
]
```

**Examples:**
```bash
# Import from file
ai-shell vault import ./credentials.json
```

---

### `vault export`

Bulk export credentials to a JSON file.

**Usage:**
```bash
ai-shell vault export <file> [options]
```

**Arguments:**
- `<file>` - Path where to save exported credentials

**Options:**
- `--include-sensitive` - Include actual credential values (default: false, exports redacted)

**Examples:**
```bash
# Export safely (redacted)
ai-shell vault export ./backup.json

# Export with actual values
ai-shell vault export ./full-backup.json --include-sensitive
```

---

### `vault rotate`

Rotate the vault encryption key.

**Usage:**
```bash
ai-shell vault rotate
```

**Examples:**
```bash
# Rotate encryption key
ai-shell vault rotate
```

**Note:** This re-encrypts all credentials with a new key. Ensure you have backups before rotating.

---

## Role-Based Access Control (RBAC)

Manage roles, permissions, and user access.

### `role create`

Create a new role.

**Usage:**
```bash
ai-shell role create <name> [description]
```

**Arguments:**
- `<name>` - Unique role identifier
- `[description]` - Optional role description

**Examples:**
```bash
# Create admin role
ai-shell role create admin "Administrator with full access"

# Create developer role
ai-shell role create developer "Development team access"
```

---

### `role delete`

Delete an existing role.

**Usage:**
```bash
ai-shell role delete <name>
```

**Arguments:**
- `<name>` - Name of the role to delete

**Examples:**
```bash
# Delete old role
ai-shell role delete deprecated-role
```

---

### `role assign`

Assign a role to a user.

**Usage:**
```bash
ai-shell role assign <user> <role>
```

**Arguments:**
- `<user>` - User identifier
- `<role>` - Role to assign

**Examples:**
```bash
# Assign admin role to user
ai-shell role assign john.doe admin

# Assign developer role
ai-shell role assign jane.smith developer
```

---

### `role unassign`

Remove a role from a user.

**Usage:**
```bash
ai-shell role unassign <user> <role>
```

**Arguments:**
- `<user>` - User identifier
- `<role>` - Role to remove

**Examples:**
```bash
# Remove admin role
ai-shell role unassign john.doe admin
```

---

### `role hierarchy`

Display role hierarchy with inherited permissions.

**Usage:**
```bash
ai-shell role hierarchy <name>
```

**Arguments:**
- `<name>` - Role name to inspect

**Examples:**
```bash
# View developer role hierarchy
ai-shell role hierarchy developer
```

**Output:**
```
📊 Role Hierarchy: developer

Direct Permissions:
  ✓ database.read
  ✓ database.write
  ✓ api.read

Inherits From:
  → viewer

Inherited Permissions:
  ✓ logs.read

Total Permissions: 4
```

---

### `permission grant`

Grant permissions to a role for a resource.

**Usage:**
```bash
ai-shell permission grant <role> <resource> [options]
```

**Arguments:**
- `<role>` - Role to grant permissions to
- `<resource>` - Resource identifier

**Options:**
- `--actions <actions>` - Comma-separated list of actions (default: read,write)

**Permission Format:**
- `resource.action` - Standard permission
- `resource.*` - All actions on resource
- `*` - All permissions (super admin)
- `resource.action.own` - Only user's own resources

**Examples:**
```bash
# Grant read/write to database
ai-shell permission grant developer database --actions read,write

# Grant all API permissions
ai-shell permission grant admin api --actions "*"

# Grant super admin
ai-shell permission grant superadmin "*"

# Grant edit own data only
ai-shell permission grant user data --actions edit.own
```

---

### `permission revoke`

Revoke permissions from a role.

**Usage:**
```bash
ai-shell permission revoke <role> <resource>
```

**Arguments:**
- `<role>` - Role to revoke permissions from
- `<resource>` - Resource to revoke access to

**Examples:**
```bash
# Revoke database access
ai-shell permission revoke developer database
```

---

### `permission list`

List permissions for a user or role.

**Usage:**
```bash
ai-shell permission list [user-or-role] [options]
```

**Arguments:**
- `[user-or-role]` - User or role to list permissions for (optional, lists all roles if omitted)

**Options:**
- `--format <format>` - Output format: json, table (default: table)

**Examples:**
```bash
# List all roles
ai-shell permission list

# List user permissions
ai-shell permission list john.doe

# List role permissions
ai-shell permission list admin --format json
```

---

### `permission check`

Check if a user has a specific permission.

**Usage:**
```bash
ai-shell permission check <user> <resource> <action>
```

**Arguments:**
- `<user>` - User identifier
- `<resource>` - Resource to check
- `<action>` - Action to check

**Examples:**
```bash
# Check if user can write to database
ai-shell permission check john.doe database write

# Check if user can delete API keys
ai-shell permission check jane.smith api delete
```

**Output:**
```
✅ Permission GRANTED
   User: john.doe
   Resource: database
   Action: write
```

---

## Audit Logging

View and manage security audit logs.

### `audit show`

Display audit log entries.

**Usage:**
```bash
ai-shell audit show [options]
```

**Options:**
- `--limit <n>` - Maximum number of entries to show (default: 20)
- `--user <user>` - Filter by user
- `--action <action>` - Filter by action
- `--resource <resource>` - Filter by resource

**Examples:**
```bash
# Show recent logs
ai-shell audit show --limit 50

# Show logs for specific user
ai-shell audit show --user admin

# Show credential operations
ai-shell audit show --action "credential.create"

# Combine filters
ai-shell audit show --user admin --action "role.assign" --limit 10
```

---

### `audit export`

Export audit logs to a file.

**Usage:**
```bash
ai-shell audit export <file> [options]
```

**Arguments:**
- `<file>` - Output file path

**Options:**
- `--format <format>` - Export format: json, csv (default: json)

**Examples:**
```bash
# Export as JSON
ai-shell audit export audit-logs.json

# Export as CSV for Excel
ai-shell audit export audit-logs.csv --format csv
```

---

### `audit stats`

Display audit log statistics.

**Usage:**
```bash
ai-shell audit stats
```

**Examples:**
```bash
# Show statistics
ai-shell audit stats
```

**Output:**
```
📊 Audit Log Statistics:

  Total Logs: 1547
  Retention Days: 90
  Unique Users: 23
  Unique Actions: 15
  Oldest Log: 2025-01-29T10:00:00Z
  Newest Log: 2025-10-29T10:00:00Z
```

---

### `audit search`

Search audit logs by keyword.

**Usage:**
```bash
ai-shell audit search <query>
```

**Arguments:**
- `<query>` - Search term

**Examples:**
```bash
# Search for database operations
ai-shell audit search "database"

# Search for failed operations
ai-shell audit search "error"
```

---

### `audit verify`

Verify audit log integrity using hash chains.

**Usage:**
```bash
ai-shell audit verify
```

**Examples:**
```bash
# Verify log integrity
ai-shell audit verify
```

**Output (Success):**
```
🔍 Verifying audit log integrity...

✅ Audit log integrity verified
   Total Logs: 1547
   Verified At: 2025-10-29T10:00:00Z
```

**Output (Failure):**
```
🔍 Verifying audit log integrity...

❌ Audit log integrity compromised

⚠️  Invalid Logs: 3

  Log ID: log_123
  Expected: abc123...
  Actual: def456...
```

---

### `audit clear`

Clear old audit logs (respects retention policy).

**Usage:**
```bash
ai-shell audit clear --before <date>
```

**Options:**
- `--before <date>` - Clear logs before this date (ISO 8601 format)

**Examples:**
```bash
# Clear logs older than 90 days
ai-shell audit clear --before 2025-07-30

# Clear logs older than 1 year
ai-shell audit clear --before 2024-10-29
```

---

## Encryption Utilities

Encrypt and decrypt data using vault encryption.

### `encrypt`

Encrypt a value.

**Usage:**
```bash
ai-shell encrypt <value>
```

**Arguments:**
- `<value>` - Text to encrypt

**Examples:**
```bash
# Encrypt a password
ai-shell encrypt "mySecretPassword123"
```

**Output:**
```
✅ Value encrypted:
   gAAAAABhZPxQ8x...
```

---

### `decrypt`

Decrypt an encrypted value.

**Usage:**
```bash
ai-shell decrypt <encrypted-value>
```

**Arguments:**
- `<encrypted-value>` - Encrypted text to decrypt

**Examples:**
```bash
# Decrypt a value
ai-shell decrypt "gAAAAABhZPxQ8x..."
```

**Output:**
```
✅ Value decrypted:
   mySecretPassword123
```

---

## Security Operations

Security scanning, compliance, and monitoring.

### `security status`

Display comprehensive security status.

**Usage:**
```bash
ai-shell security status
```

**Examples:**
```bash
# Check security status
ai-shell security status
```

**Output:**
```
🔒 Security Status Overview

Vault:
  ✓ Enabled
  Total Credentials: 42
  Auto-Redact: Yes

RBAC:
  ✓ Enabled
  Total Roles: 5
  Roles: admin, developer, viewer, auditor, guest

Audit Logging:
  ✓ Enabled
  Total Logs: 1547
  Unique Users: 23
  Unique Actions: 15
```

---

### `security scan`

Run comprehensive security scan.

**Usage:**
```bash
ai-shell security scan [options]
```

**Options:**
- `--deep` - Run deep scan (more thorough, takes longer)
- `--output <file>` - Save report to file

**Examples:**
```bash
# Quick scan
ai-shell security scan

# Deep scan with report
ai-shell security scan --deep --output security-report.json
```

**Output:**
```
🔒 Running security scan...

  → Scanning for SQL injection vulnerabilities...
  → Scanning for path traversal vulnerabilities...
  → Scanning for PII exposure...

🔒 Security Scan Report

Generated: 2025-10-29T10:00:00Z

Summary:
  Total Issues: 0
  Critical: 0
  High: 0
  Medium: 0
  Low: 0

Compliance Status:
  GDPR: ✓ Compliant
  SOX:  ✓ Compliant
  HIPAA: ✓ Compliant
```

---

### `security vulnerabilities`

List known vulnerability types.

**Usage:**
```bash
ai-shell security vulnerabilities
```

**Examples:**
```bash
# List vulnerabilities
ai-shell security vulnerabilities
```

**Output:**
```
⚠️  Known Vulnerabilities:

  1. SQL Injection - Check SQL guard configuration
  2. Path Traversal - Validate file paths
  3. PII Exposure - Enable PII redaction
  4. Command Injection - Sanitize shell commands
  5. Rate Limiting - Configure rate limits
```

---

### `security compliance`

Check compliance with security standards.

**Usage:**
```bash
ai-shell security compliance [options]
```

**Options:**
- `--standard <standard>` - Standard to check: gdpr, sox, hipaa, all (default: all)

**Examples:**
```bash
# Check all standards
ai-shell security compliance

# Check GDPR only
ai-shell security compliance --standard gdpr

# Check HIPAA only
ai-shell security compliance --standard hipaa
```

**Output:**
```
✅ Compliance Report

GDPR: Compliant
SOX: Compliant
HIPAA: Compliant
```

---

### `security detect-pii`

Detect personally identifiable information (PII) in text.

**Usage:**
```bash
ai-shell security detect-pii <text>
```

**Arguments:**
- `<text>` - Text to scan for PII

**Examples:**
```bash
# Detect PII
ai-shell security detect-pii "My email is john@example.com and SSN is 123-45-6789"
```

**Output:**
```
🔍 PII Detection Results

⚠️  PII Detected: email, ssn

Detections: 2

  1. EMAIL
     Value: john@example.com
     Position: 12-30

  2. SSN
     Value: 123-45-6789
     Position: 42-53

Masked Output:
  My email is j***@example.com and SSN is ***-**-6789
```

---

## Examples

### Complete Security Setup Workflow

```bash
# 1. Check initial security status
ai-shell security status

# 2. Add credentials
ai-shell vault add prod-db "dbPassword123!" --encrypt
ai-shell vault add api-key "sk-1234567890" --encrypt

# 3. Create roles
ai-shell role create admin "Full system access"
ai-shell role create developer "Development team"
ai-shell role create viewer "Read-only access"

# 4. Configure permissions
ai-shell permission grant admin "*"
ai-shell permission grant developer database --actions read,write
ai-shell permission grant developer api --actions read
ai-shell permission grant viewer database --actions read
ai-shell permission grant viewer logs --actions read

# 5. Assign roles
ai-shell role assign alice.admin admin
ai-shell role assign bob.developer developer
ai-shell role assign charlie.viewer viewer

# 6. Verify permissions
ai-shell permission check bob.developer database write  # Should be granted
ai-shell permission check charlie.viewer database write # Should be denied

# 7. Run security scan
ai-shell security scan --deep --output security-report.json

# 8. Check compliance
ai-shell security compliance --standard all

# 9. Review audit logs
ai-shell audit show --limit 20
ai-shell audit export compliance-audit.json

# 10. Verify audit integrity
ai-shell audit verify
```

### Bulk Credential Management

```bash
# Create import file
cat > credentials.json << EOF
[
  {
    "name": "prod-database",
    "value": "prodDbPass123!",
    "encrypt": true,
    "metadata": {
      "environment": "production",
      "service": "postgresql"
    }
  },
  {
    "name": "staging-database",
    "value": "stagingDbPass456!",
    "encrypt": true,
    "metadata": {
      "environment": "staging",
      "service": "postgresql"
    }
  },
  {
    "name": "api-key-prod",
    "value": "sk-prod-1234567890",
    "encrypt": true,
    "metadata": {
      "service": "openai",
      "environment": "production"
    }
  }
]
EOF

# Import credentials
ai-shell vault import credentials.json

# Verify import
ai-shell vault list
ai-shell vault search "prod"

# Export for backup (safe)
ai-shell vault export backup.json

# Export with sensitive data (for migration)
ai-shell vault export full-backup.json --include-sensitive
```

### PII Detection Workflow

```bash
# Test various PII types
ai-shell security detect-pii "Contact: john.doe@example.com"
ai-shell security detect-pii "SSN: 123-45-6789"
ai-shell security detect-pii "Phone: (555) 123-4567"
ai-shell security detect-pii "Card: 4532-1234-5678-9010"

# Complex text with multiple PII
ai-shell security detect-pii "John Doe, SSN: 123-45-6789, Email: john@test.com, Phone: 555-1234"
```

### Audit Log Analysis

```bash
# View recent activity
ai-shell audit show --limit 50

# Find specific user activity
ai-shell audit show --user admin --limit 100

# Find credential operations
ai-shell audit show --action "credential.create"
ai-shell audit show --action "credential.delete"

# Search for security events
ai-shell audit search "failed"
ai-shell audit search "permission denied"

# Export for compliance
ai-shell audit export compliance-report-2025-10.json

# Verify integrity
ai-shell audit verify

# Get statistics
ai-shell audit stats
```

### RBAC Advanced Scenarios

```bash
# Create role hierarchy
ai-shell role create super-admin "Top level admin"
ai-shell role create admin "Regular admin"
ai-shell role create developer "Developer with write access"
ai-shell role create viewer "Read-only user"

# Configure permissions with inheritance
ai-shell permission grant super-admin "*"
ai-shell permission grant admin database --actions "*"
ai-shell permission grant admin api --actions read,write,delete
ai-shell permission grant developer database --actions read,write
ai-shell permission grant developer api --actions read
ai-shell permission grant viewer database --actions read

# View hierarchy
ai-shell role hierarchy super-admin
ai-shell role hierarchy admin
ai-shell role hierarchy developer

# Test permissions
ai-shell permission check alice.super database delete  # Granted
ai-shell permission check bob.developer database delete # Denied
ai-shell permission check charlie.viewer database read  # Granted
ai-shell permission check charlie.viewer database write # Denied
```

---

## Environment Variables

Configure security settings using environment variables:

```bash
# Vault Configuration
export VAULT_PASSWORD="your-strong-master-password-32-chars-min"
export VAULT_PATH="$HOME/.ai-shell/vault"

# Audit Configuration
export AUDIT_RETENTION_DAYS=90
export ENABLE_TAMPER_PROOF_AUDIT=true

# Security Configuration
export AUTO_REDACT_CREDENTIALS=true
```

---

## Security Best Practices

1. **Strong Passwords:** Use minimum 32-character master password
2. **Regular Rotation:** Rotate vault keys quarterly
3. **Least Privilege:** Grant minimum required permissions
4. **Audit Regularly:** Review audit logs weekly
5. **Backup Safely:** Encrypt backups and store securely
6. **Monitor Access:** Set up alerts for suspicious activity
7. **Verify Integrity:** Run `audit verify` daily
8. **Compliance Checks:** Run security scans before releases
9. **PII Protection:** Scan all data for PII before logging
10. **Role Reviews:** Audit user roles quarterly

---

## Troubleshooting

### Vault Issues

**Problem:** "Invalid master password"
```bash
# Solution: Check environment variable
echo $VAULT_PASSWORD
export VAULT_PASSWORD="your-correct-password"
```

**Problem:** "Credential not found"
```bash
# Solution: List all credentials
ai-shell vault list
ai-shell vault search "partial-name"
```

### RBAC Issues

**Problem:** "Permission denied"
```bash
# Solution: Check user permissions
ai-shell permission list john.doe
ai-shell permission check john.doe resource action
```

**Problem:** "Role not found"
```bash
# Solution: List all roles
ai-shell permission list
ai-shell role create missing-role "Description"
```

### Audit Issues

**Problem:** "Audit integrity failed"
```bash
# Solution: Check for tampering
ai-shell audit verify
ai-shell audit show --limit 100 | grep -i error
```

**Problem:** "Export failed"
```bash
# Solution: Check file permissions
ls -la /path/to/output
mkdir -p /path/to/directory
```

---

## Additional Resources

- **Security Hardening Report:** `/docs/reports/security-hardening-report.md`
- **Security Tutorial:** `/docs/tutorials/security.md`
- **Quick Reference:** `/docs/security-cli-quick-reference.md`
- **Main Security Doc:** `/SECURITY.md`

---

**Last Updated:** 2025-10-29
**Version:** 2.0.0
