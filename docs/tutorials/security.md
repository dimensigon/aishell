# Security Tutorial

> **📋 Implementation Status**
>
> **Current Status:** In Development
> **CLI Availability:** Partial
> **Completeness:** 38%
>
> **What Works Now:**
> - Basic credential management
> - Environment variable configuration
> - Connection string support
>
> **Coming Soon:**
> - Encrypted credential vault
> - Role-based access control (RBAC)
> - Comprehensive audit logging
> - Data redaction and PII protection
> - Command approval workflows
> - Multi-factor authentication (MFA)
> - Secret scanning and leak prevention
>
> **Note:** This tutorial describes the intended functionality. Check the [Gap Analysis Report](../FEATURE_GAP_ANALYSIS_REPORT.md) for detailed implementation status.

## Table of Contents
- [Introduction](#introduction)
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Step-by-Step Instructions](#step-by-step-instructions)
- [Common Use Cases](#common-use-cases)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

---

## Introduction

Enterprise-grade security is critical for database management. AI-Shell provides zero-compromise security features out of the box, including encryption, role-based access control, audit logging, and sensitive data protection.

**What You'll Learn:**
- How to securely store and manage database credentials
- Implementing role-based access control (RBAC)
- Enabling comprehensive audit logging
- Protecting sensitive data with redaction
- Setting up command approval workflows
- Configuring multi-factor authentication

**Time to Complete:** 30-40 minutes

---

## Overview

AI-Shell's security framework provides comprehensive protection at every level:

### Security Features

- **Credential Encryption**: AES-256 encryption for all stored credentials
- **Role-Based Access Control (RBAC)**: Fine-grained permissions management
- **Audit Logging**: Complete audit trail of all operations
- **Data Redaction**: Automatic PII/sensitive data protection
- **Approval Workflows**: Multi-person authorization for critical commands
- **MFA Support**: Multi-factor authentication integration
- **Secret Scanning**: Prevent credential leaks
- **Secure Vault**: Encrypted credential storage

### Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AI-Shell Security                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Encrypted  │  │     RBAC     │  │    Audit     │ │
│  │    Vault     │  │   Engine     │  │     Log      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         ▲                  ▲                  ▲        │
│         └──────────────────┴──────────────────┘        │
│                           │                            │
│                 ┌─────────▼──────────┐                 │
│                 │  Security Manager  │                 │
│                 └─────────┬──────────┘                 │
│                           │                            │
│         ┌─────────────────┼─────────────────┐          │
│         ▼                 ▼                 ▼          │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐    │
│  │   Query    │   │  Command   │   │    Data    │    │
│  │ Protection │   │  Approval  │   │ Redaction  │    │
│  └────────────┘   └────────────┘   └────────────┘    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Key Benefits

| Feature | Benefit |
|---------|---------|
| Zero-setup security | Works securely out of the box |
| Compliance ready | SOC2, GDPR, HIPAA compatible |
| No credential exposure | Never stores plaintext passwords |
| Complete audit trail | Track all database operations |
| Proactive protection | Prevent issues before they happen |

---

## Prerequisites

### Required

- AI-Shell installed ([Installation Guide](../installation.md))
- Administrative access to your system
- Database connection(s) to secure

### Optional

- Email/Slack for alert notifications
- OAuth provider for SSO integration
- Hardware security key for MFA
- Centralized logging system (Splunk, ELK)

### System Requirements

- OpenSSL 1.1.1 or higher (for encryption)
- File system with proper permissions support
- Secure storage location for vault

---

## Getting Started

### Quick Security Setup

```bash
# Initialize secure vault
ai-shell vault init

# Add your first secured connection
ai-shell vault add production --interactive
```

**Interactive Setup:**

```
🔐 Secure Vault Setup

Creating encrypted vault...
  ✓ Vault location: ~/.ai-shell/vault/
  ✓ Encryption: AES-256-GCM
  ✓ Key derivation: PBKDF2 (100,000 iterations)

Enter master password: ********
Confirm master password: ********
  ✓ Master password set

Security options:
  1. Add MFA (recommended)
  2. Set password expiration
  3. Enable audit logging
  4. Configure backup location
  5. Continue without additional security

Select options [1,3,4]: 1,3

Multi-factor authentication:
  1. TOTP (Google Authenticator, Authy)
  2. Hardware key (YubiKey, etc.)
  3. SMS (not recommended)

Select MFA method: 1

Scan this QR code with your authenticator app:
[QR CODE DISPLAYED]

Or enter this secret manually: JBSWY3DPEHPK3PXP

Enter TOTP code to verify: 123456
  ✓ MFA enabled

Audit logging:
  Log location: ~/.ai-shell/logs/audit.log
  ✓ Audit logging enabled

✅ Vault initialized successfully!

Next steps:
  → Add credentials: ai-shell vault add production
  → Set up RBAC: ai-shell permissions setup
  → Configure alerts: ai-shell alert config
```

---

## Step-by-Step Instructions

### Step 1: Initialize Secure Vault

The vault securely stores all database credentials using AES-256 encryption.

```bash
# Initialize vault with defaults
ai-shell vault init

# Initialize with custom settings
ai-shell vault init \
  --encryption aes-256-gcm \
  --key-derivation pbkdf2 \
  --iterations 200000 \
  --location /secure/path/vault
```

**Vault Configuration:**

```yaml
# ~/.ai-shell/vault/config.yaml
encryption:
  algorithm: aes-256-gcm
  keyDerivation: pbkdf2
  iterations: 100000
  saltLength: 32

security:
  mfa:
    enabled: true
    method: totp
  passwordPolicy:
    minLength: 16
    requireUppercase: true
    requireLowercase: true
    requireNumbers: true
    requireSymbols: true
    expirationDays: 90

  sessionTimeout: 3600  # 1 hour
  maxLoginAttempts: 3
  lockoutDuration: 900  # 15 minutes

backup:
  enabled: true
  location: /backup/vault/
  schedule: daily
  retention: 30  # days
```

### Step 2: Add Encrypted Credentials

```bash
# Add database credentials interactively
ai-shell vault add production --interactive

# Add with command-line options
ai-shell vault add production \
  --type postgres \
  --host prod.db.example.com \
  --port 5432 \
  --database app_prod \
  --username dbadmin \
  --encrypt

# Add with environment-based password (more secure)
export DB_PASSWORD="secure-password"
ai-shell vault add production \
  --password-env DB_PASSWORD \
  --encrypt

# Add with connection string
ai-shell vault add production \
  --url "postgres://user@host:5432/db" \
  --encrypt
```

**Credential Management:**

```bash
# List stored credentials (passwords never shown)
ai-shell vault list

# Output:
# 📦 Stored Credentials
#
# Name         Type        Host                    Encrypted
# ────────────────────────────────────────────────────────────
# production   postgres    prod.db.example.com     ✓
# staging      postgres    staging.db.example.com  ✓
# cache        redis       redis.example.com       ✓
# analytics    mongodb     mongo.example.com       ✓

# Update credentials
ai-shell vault update production --password-env NEW_PASSWORD

# Rotate credentials (generates new password)
ai-shell vault rotate production

# Remove credentials
ai-shell vault remove production

# Export encrypted backup
ai-shell vault export --output vault-backup.enc
```

### Step 3: Configure Role-Based Access Control (RBAC)

Define roles and permissions for team members:

```bash
# Create roles
ai-shell permissions role create developer
ai-shell permissions role create dba
ai-shell permissions role create read-only
ai-shell permissions role create admin

# Define permissions for each role
ai-shell permissions role edit developer
```

**Role Configuration:**

```yaml
# ~/.ai-shell/rbac/roles.yaml
roles:
  admin:
    description: "Full administrative access"
    permissions:
      - "*"  # All permissions

  dba:
    description: "Database administrator"
    permissions:
      - "query:execute"
      - "query:explain"
      - "schema:modify"
      - "index:create"
      - "backup:create"
      - "backup:restore"
      - "monitor:view"
      - "optimize:apply"
    restrictions:
      - "!data:delete:production"  # Cannot delete in production

  developer:
    description: "Application developer"
    permissions:
      - "query:execute:read"
      - "query:explain"
      - "schema:view"
      - "monitor:view"
    databases:
      - "development"
      - "staging"
    approval_required:
      - "query:execute:write"  # Write queries need approval

  read-only:
    description: "Read-only access"
    permissions:
      - "query:execute:read"
      - "schema:view"
    restrictions:
      - "!query:execute:write"
      - "!schema:modify"
      - "!backup:*"

# User assignments
users:
  alice@example.com:
    roles: [admin]
    mfa_required: true

  bob@example.com:
    roles: [dba]
    mfa_required: true
    allowed_hours:
      start: "09:00"
      end: "17:00"
      timezone: "America/New_York"

  charlie@example.com:
    roles: [developer]
    databases: [development, staging]

  team@example.com:
    roles: [read-only]
```

**Assign Users to Roles:**

```bash
# Grant role to user
ai-shell permissions grant developer --to charlie@example.com

# Grant database-specific access
ai-shell permissions grant developer \
  --to charlie@example.com \
  --database staging

# Grant temporary access
ai-shell permissions grant dba \
  --to bob@example.com \
  --expires "24h"

# Revoke permissions
ai-shell permissions revoke developer --from charlie@example.com

# View user permissions
ai-shell permissions show charlie@example.com
```

### Step 4: Enable Audit Logging

Track all database operations for compliance and security:

```bash
# Enable audit logging
ai-shell audit-log enable

# Configure what to log
ai-shell audit-log config

# View recent audit logs
ai-shell audit-log show

# Filter logs by user
ai-shell audit-log show --user charlie@example.com

# Filter logs by time
ai-shell audit-log show --last 24h

# Filter logs by action
ai-shell audit-log show --action "query:execute"

# Export audit logs
ai-shell audit-log export --format json --output audit-2025-10.json
```

**Audit Log Configuration:**

```yaml
# ~/.ai-shell/audit/config.yaml
audit:
  enabled: true

  # What to log
  events:
    - authentication  # Login/logout attempts
    - authorization   # Permission checks
    - queries         # All executed queries
    - schema_changes  # DDL operations
    - data_changes    # DML operations
    - admin_actions   # Administrative commands
    - errors          # Failed operations

  # Query logging options
  queries:
    logParameters: true
    logResults: false  # Don't log result data
    logSlowQueries: true
    slowQueryThreshold: 100ms
    redactSensitive: true  # Redact PII/passwords

  # Log destinations
  destinations:
    - type: file
      path: ~/.ai-shell/logs/audit.log
      rotation: daily
      retention: 90  # days

    - type: syslog
      host: syslog.example.com
      port: 514
      protocol: tcp

    - type: elasticsearch
      url: https://elasticsearch.example.com
      index: ai-shell-audit

  # Alerting
  alerts:
    - event: failed_login
      threshold: 3
      window: 5m
      action: lock_account

    - event: unauthorized_access
      action: notify_security_team

    - event: bulk_delete
      threshold: 1000  # rows
      action: require_approval
```

**Sample Audit Log Entry:**

```json
{
  "timestamp": "2025-10-28T14:23:45.123Z",
  "event_id": "evt_7f8g9h0i1j2k",
  "event_type": "query:execute",
  "user": {
    "email": "charlie@example.com",
    "role": "developer",
    "ip": "192.168.1.100",
    "session_id": "sess_abc123"
  },
  "database": {
    "name": "staging",
    "host": "staging.db.example.com",
    "type": "postgres"
  },
  "query": {
    "sql": "SELECT id, email FROM users WHERE status = $1",
    "parameters": ["active"],
    "duration_ms": 23,
    "rows_affected": 1234
  },
  "result": "success",
  "metadata": {
    "client": "ai-shell-cli",
    "version": "1.0.0"
  }
}
```

### Step 5: Configure Data Redaction

Protect sensitive data from being exposed in logs or output:

```bash
# Enable automatic PII redaction
ai-shell security redaction enable

# Configure redaction rules
ai-shell security redaction config
```

**Redaction Configuration:**

```yaml
# ~/.ai-shell/security/redaction.yaml
redaction:
  enabled: true

  # Automatic detection patterns
  patterns:
    - type: email
      regex: '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
      replacement: '[EMAIL_REDACTED]'

    - type: ssn
      regex: '\b\d{3}-\d{2}-\d{4}\b'
      replacement: '[SSN_REDACTED]'

    - type: credit_card
      regex: '\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
      replacement: '[CC_REDACTED]'

    - type: password
      regex: 'password["\s:=]+[^\s]+'
      replacement: 'password="[REDACTED]"'

    - type: api_key
      regex: '[a-z0-9]{32,}'
      replacement: '[API_KEY_REDACTED]'

    - type: phone
      regex: '\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
      replacement: '[PHONE_REDACTED]'

  # Column-level redaction
  columns:
    - database: production
      table: users
      columns: [password, ssn, credit_card]
      redact_in: [logs, query_results, exports]

    - database: production
      table: customers
      columns: [email, phone]
      redact_in: [logs]

  # Table-level redaction
  tables:
    - database: production
      tables: [payment_methods, personal_identifiable_info]
      redact_in: [logs, exports]
```

**Testing Redaction:**

```bash
# Test redaction rules
ai-shell security redaction test "john.doe@example.com"
# Output: [EMAIL_REDACTED]

ai-shell security redaction test "SSN: 123-45-6789"
# Output: SSN: [SSN_REDACTED]

# View redacted query
ai-shell query "SELECT email, password FROM users" --dry-run
# Output: SELECT [EMAIL_REDACTED], [REDACTED] FROM users
```

### Step 6: Set Up Command Approval Workflows

Require approval for critical operations:

```bash
# Enable approval workflows
ai-shell approval enable

# Configure approval rules
ai-shell approval config
```

**Approval Configuration:**

```yaml
# ~/.ai-shell/approval/rules.yaml
approval:
  enabled: true

  rules:
    # Require approval for production write operations
    - name: production_writes
      condition:
        database: production
        operation: [insert, update, delete]
      approvers:
        required: 2
        roles: [dba, admin]
        timeout: 1h
      notification:
        - slack
        - email

    # Require approval for schema changes
    - name: schema_changes
      condition:
        operation: [create, alter, drop]
        object_type: [table, index, column]
      approvers:
        required: 1
        roles: [dba]
        timeout: 4h

    # Require approval for bulk deletes
    - name: bulk_deletes
      condition:
        operation: delete
        estimated_rows: ">1000"
      approvers:
        required: 2
        roles: [admin]
        timeout: 30m

    # Require approval for backup restoration
    - name: restore_operations
      condition:
        operation: restore
      approvers:
        required: 2
        roles: [admin]
        timeout: 2h
      require_reason: true
      simulate_first: true

  notifications:
    slack:
      webhook: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
      channel: "#db-approvals"

    email:
      from: approvals@example.com
      to: [dba-team@example.com, admin-team@example.com]
```

**Using Approval Workflows:**

```bash
# Execute command requiring approval
ai-shell query "DELETE FROM users WHERE last_login < '2020-01-01'"

# Output:
# ⏳ Approval Required
#
# Command: DELETE FROM users WHERE last_login < '2020-01-01'
# Database: production
# Estimated impact: 2,340 rows
# Rule: bulk_deletes
#
# Required approvers: 2 from [admin]
#
# Approval request sent to:
#   - admin-team@example.com
#   - Slack: #db-approvals
#
# Request ID: req_abc123
# Timeout: 30 minutes
#
# Track approval status: ai-shell approval status req_abc123

# Check approval status
ai-shell approval status req_abc123

# Output:
# Approval Status: req_abc123
#
# Command: DELETE FROM users WHERE last_login < '2020-01-01'
# Requested by: charlie@example.com
# Requested at: 2025-10-28 14:23:45
#
# Approvals (1/2 required):
#   ✓ alice@example.com - approved at 14:25:12
#   ⏳ bob@example.com - pending
#
# Status: PENDING
# Timeout: 28 minutes remaining

# Approve a request (as admin)
ai-shell approval approve req_abc123 --reason "Cleanup approved in ticket #1234"

# Reject a request
ai-shell approval reject req_abc123 --reason "Need more information"

# Cancel your own request
ai-shell approval cancel req_abc123
```

### Step 7: Configure Multi-Factor Authentication (MFA)

Add an extra layer of security with MFA:

```bash
# Enable MFA
ai-shell security mfa enable

# Choose MFA method
ai-shell security mfa setup --method totp

# Configure for hardware keys
ai-shell security mfa setup --method hardware-key
```

**MFA Setup Process:**

```
🔐 Multi-Factor Authentication Setup

Method: TOTP (Time-based One-Time Password)

Step 1: Install an authenticator app
  - Google Authenticator (iOS/Android)
  - Authy (iOS/Android/Desktop)
  - 1Password (iOS/Android/Desktop)
  - Microsoft Authenticator (iOS/Android)

Step 2: Scan QR code
[QR CODE DISPLAYED]

Or enter this secret manually:
  JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP

Step 3: Verify setup
Enter the 6-digit code from your app: 123456
  ✓ MFA verified successfully

Backup codes (store these securely):
  1. 8f7d-9c2e
  2. 3a1b-6f4g
  3. 9h2j-5k7m
  4. 4n8p-2q6r
  5. 7s3t-1u9v

⚠️ Important:
  - Store backup codes in a secure location
  - You'll need them if you lose your device
  - Each backup code can only be used once

✅ MFA enabled successfully!

From now on, you'll be prompted for:
  1. Master password
  2. MFA code

To disable MFA: ai-shell security mfa disable
```

**MFA Configuration:**

```yaml
# ~/.ai-shell/security/mfa.yaml
mfa:
  enabled: true
  method: totp

  # When to require MFA
  require_for:
    - login
    - vault_access
    - production_operations
    - approval_actions
    - security_changes

  # Grace period after successful auth
  grace_period: 8h

  # Backup codes
  backup_codes:
    enabled: true
    count: 5
    regenerate_after_use: true

  # Account recovery
  recovery:
    enabled: true
    require_email_verification: true
    cooldown_period: 24h  # Prevent rapid recovery attempts
```

### Step 8: Prevent Credential Leaks

Scan for accidentally exposed credentials:

```bash
# Scan current directory for secrets
ai-shell security scan

# Scan specific files
ai-shell security scan --path /path/to/project

# Scan git history
ai-shell security scan --git-history

# Configure pre-commit hook
ai-shell security install-hooks
```

**Secret Scanning:**

```bash
ai-shell security scan --path .

# Output:
# 🔍 Scanning for exposed credentials...
#
# ❌ Found 3 potential secrets
#
# File: config/database.yml
# Line 12: password: "prod-secret-123"
#   Type: Plaintext password
#   Risk: HIGH
#   Fix: Use environment variable or vault
#
# File: scripts/backup.sh
# Line 8: export DB_URL="postgres://admin:password@..."
#   Type: Connection string with password
#   Risk: HIGH
#   Fix: Use vault reference or env var
#
# File: .env.example
# Line 5: ANTHROPIC_API_KEY=sk-ant-1234567890
#   Type: API key
#   Risk: MEDIUM
#   Fix: Use placeholder instead of real key
#
# Recommendations:
#   1. Move secrets to vault: ai-shell vault add
#   2. Use environment variables
#   3. Add sensitive files to .gitignore
#   4. Install pre-commit hooks: ai-shell security install-hooks
#
# Scan complete: 3 issues found
```

---

## Common Use Cases

### Use Case 1: Onboarding New Team Member

**Scenario:** Grant appropriate access to a new developer

```bash
# Create user account
ai-shell permissions user create sarah@example.com

# Assign role
ai-shell permissions grant developer --to sarah@example.com

# Grant database access
ai-shell permissions grant database:staging --to sarah@example.com

# Set access schedule (business hours only)
ai-shell permissions configure sarah@example.com \
  --hours "09:00-17:00" \
  --timezone "America/New_York" \
  --days "Monday-Friday"

# Require MFA
ai-shell permissions configure sarah@example.com --require-mfa

# Send welcome email with setup instructions
ai-shell permissions invite sarah@example.com
```

**Welcome Email Template:**

```
Subject: Welcome to AI-Shell Database Access

Hi Sarah,

You've been granted access to AI-Shell database management.

Your Role: Developer
Databases: staging
Access Hours: Mon-Fri, 9 AM - 5 PM EST

Getting Started:
1. Install AI-Shell: npm install -g ai-shell
2. Set up your account: ai-shell setup --user sarah@example.com
3. Configure MFA: ai-shell security mfa enable
4. View your permissions: ai-shell permissions show

Available Commands:
  - Query data: ai-shell query "..."
  - View schema: ai-shell schema show
  - Monitor performance: ai-shell monitor start

Need help? Contact: devops@example.com

Best regards,
DevOps Team
```

### Use Case 2: Quarterly Access Review

**Scenario:** Review and update team permissions quarterly

```bash
# Generate access report
ai-shell permissions report --all-users

# Output:
# 📊 Access Review Report
# Generated: 2025-10-28
#
# Total Users: 12
# Active Roles: 4 (admin, dba, developer, read-only)
# Inactive Users: 2
#
# Users by Role:
#   Admin:     2 users
#   DBA:       3 users
#   Developer: 5 users
#   Read-only: 2 users
#
# Recommendations:
#   ⚠️ 2 users inactive for >90 days
#   ⚠️ 1 user has overly broad permissions
#   ⚠️ 3 users missing MFA
#
# Details:
#
# alice@example.com
#   Role: Admin
#   MFA: ✓ Enabled
#   Last login: 2025-10-27
#   Status: ✓ Active
#
# bob@example.com
#   Role: DBA
#   MFA: ✓ Enabled
#   Last login: 2025-10-28
#   Status: ✓ Active
#
# charlie@example.com
#   Role: Developer
#   MFA: ✓ Enabled
#   Last login: 2025-10-28
#   Status: ✓ Active
#
# dave@example.com
#   Role: Developer
#   MFA: ❌ Not enabled
#   Last login: 2025-07-15 (104 days ago)
#   Status: ⚠️ Inactive - consider removal
#
# eve@example.com
#   Role: Admin
#   MFA: ❌ Not enabled
#   Last login: 2025-10-20
#   Status: ⚠️ Missing MFA - security risk

# Review specific user
ai-shell permissions audit dave@example.com

# Disable inactive user
ai-shell permissions disable dave@example.com

# Enforce MFA for all users
ai-shell permissions require-mfa --all-users

# Export audit report
ai-shell permissions report --export pdf --output access-review-2025-Q4.pdf
```

### Use Case 3: Security Incident Response

**Scenario:** Respond to suspected unauthorized access

```bash
# Check recent authentication attempts
ai-shell audit-log show --event authentication --last 24h

# Identify suspicious activity
ai-shell security analyze --suspicious

# Output:
# 🚨 Security Analysis
#
# Suspicious Activity Detected:
#
# 1. Multiple failed login attempts
#    User: unknown@external.com
#    IP: 203.0.113.45 (Unknown location)
#    Attempts: 15 in last hour
#    Status: ⚠️ Account locked after 3 attempts
#
# 2. Unusual query pattern
#    User: charlie@example.com
#    Database: production
#    Time: 2025-10-28 02:34:00 (outside normal hours)
#    Queries: 234 in 5 minutes
#    Status: ⚠️ Possible data exfiltration
#
# 3. Permission escalation attempt
#    User: sarah@example.com
#    Action: Attempted admin operation
#    Result: Denied (insufficient permissions)
#    Status: ⚠️ Monitor user activity

# Lock compromised account
ai-shell permissions lock charlie@example.com --reason "Suspicious activity"

# Revoke active sessions
ai-shell security revoke-sessions --user charlie@example.com

# Change credentials
ai-shell vault rotate production --force

# Review queries executed
ai-shell audit-log show \
  --user charlie@example.com \
  --since "2025-10-28 02:00:00" \
  --type query

# Block suspicious IP
ai-shell security block-ip 203.0.113.45

# Generate incident report
ai-shell security incident-report \
  --user charlie@example.com \
  --timeframe "2025-10-28 02:00-03:00" \
  --output incident-report-2025-10-28.pdf

# Notify security team
ai-shell alert notify security-team \
  --severity critical \
  --message "Potential security incident - account charlie@example.com"
```

### Use Case 4: Compliance Audit Preparation

**Scenario:** Prepare for SOC2/GDPR audit

```bash
# Generate compliance report
ai-shell compliance report --standard soc2

# Output:
# 📋 SOC2 Compliance Report
#
# Organization: Example Corp
# Period: 2025-01-01 to 2025-10-28
# Generated: 2025-10-28
#
# ✅ Passed Controls: 42/45 (93%)
# ⚠️  Warnings: 3
# ❌ Failed: 0
#
# Access Control (CC6.1):
#   ✅ Role-based access control implemented
#   ✅ Principle of least privilege enforced
#   ✅ Multi-factor authentication enabled
#   ✅ Regular access reviews conducted (quarterly)
#   ✅ Terminated user access revoked within 24h
#
# Logical and Physical Access (CC6.2):
#   ✅ Encrypted credential storage (AES-256)
#   ✅ Strong password policy enforced
#   ✅ Session timeout configured (1 hour)
#   ✅ Failed login attempt monitoring
#   ⚠️  3 users missing MFA (non-compliance)
#
# System Operations (CC7.2):
#   ✅ Comprehensive audit logging enabled
#   ✅ Log retention: 90 days (compliant)
#   ✅ Logs tamper-proof and encrypted
#   ✅ Security monitoring active
#   ✅ Incident response procedures documented
#
# Change Management (CC8.1):
#   ✅ Approval workflows for production changes
#   ✅ All changes logged and auditable
#   ⚠️  Missing approval for 2 recent changes
#   ✅ Rollback capability tested and verified
#
# Risk Mitigation (CC9.2):
#   ✅ Data encryption at rest and in transit
#   ✅ PII redaction in logs
#   ✅ Regular security scanning
#   ⚠️  1 outdated dependency with known CVE
#
# Recommendations:
#   1. Enforce MFA for remaining 3 users
#   2. Review approval bypass incidents
#   3. Update dependency: pg library to v8.11.3
#
# Export Options:
#   PDF: ai-shell compliance report --export pdf
#   Evidence: ai-shell compliance evidence --period 2025-Q3

# Export evidence package
ai-shell compliance evidence \
  --standard soc2 \
  --period "2025-Q3" \
  --output soc2-evidence-2025-Q3.zip

# Fix compliance issues
ai-shell permissions require-mfa --users sarah@example.com,dave@example.com,eve@example.com
ai-shell audit-log review --missing-approvals
npm update pg  # Update vulnerable dependency
```

### Use Case 5: Rotating Credentials

**Scenario:** Regularly rotate database credentials for security

```bash
# Schedule automatic credential rotation
ai-shell vault rotate-schedule --every 90days

# Manually rotate credentials
ai-shell vault rotate production

# Output:
# 🔄 Rotating Credentials: production
#
# Step 1: Generating new password...
#   ✓ New password generated (32 chars, high entropy)
#   ✓ Password meets complexity requirements
#
# Step 2: Testing new credentials...
#   ✓ Connection successful with new password
#   ✓ Permissions verified
#
# Step 3: Updating database...
#   ✓ ALTER USER command executed
#   ✓ New password active
#
# Step 4: Updating vault...
#   ✓ Old password backed up
#   ✓ New password stored in vault
#   ✓ Vault re-encrypted
#
# Step 5: Notifying applications...
#   ✓ Updated connection pool
#   ✓ Tested application connectivity
#   ⚠️  Manual update required for: backup-script.sh
#
# Step 6: Audit logging...
#   ✓ Rotation logged
#   ✓ Security team notified
#
# ✅ Credential rotation complete
#
# Old password backed up to: vault/backup/production-2025-10-28.enc
# Backup expires in: 30 days
#
# Next rotation: 2026-01-26

# Rotate all credentials
ai-shell vault rotate --all --batch

# Emergency rotation (suspected compromise)
ai-shell vault rotate production --emergency
```

---

## Advanced Features

### Custom Security Policies

Define organization-specific security policies:

```yaml
# ~/.ai-shell/security/policies.yaml
policies:
  # Password policy
  password:
    minLength: 16
    requireUppercase: true
    requireLowercase: true
    requireNumbers: true
    requireSymbols: true
    expirationDays: 90
    preventReuse: 5  # Last 5 passwords
    maxAge: 90  # days

  # Session policy
  session:
    timeout: 3600  # 1 hour
    maxConcurrent: 3
    ipWhitelist:
      - "192.168.0.0/16"
      - "10.0.0.0/8"
    geoRestrictions:
      allowedCountries: [US, CA, UK]

  # Query policy
  query:
    maxExecutionTime: 30000  # 30 seconds
    maxResultRows: 10000
    preventFullTableScans: true
    requireWhereClauses: true  # For DELETE/UPDATE
    blockDangerousOperations:
      - "DROP TABLE"
      - "DROP DATABASE"
      - "TRUNCATE"
    requireApprovalFor:
      - operation: DELETE
        condition: "estimated_rows > 1000"
      - operation: UPDATE
        condition: "estimated_rows > 5000"

  # Audit policy
  audit:
    retention: 90  # days
    immutable: true
    encrypt: true
    offsite_backup: true

  # Compliance
  compliance:
    standards: [SOC2, GDPR, HIPAA]
    pii_handling:
      detect: true
      redact: true
      log_access: true
    data_residency:
      region: us-east-1
      crossRegionReplication: false
```

### Integration with SSO

Integrate with existing identity providers:

```bash
# Configure SSO
ai-shell security sso configure

# Support for multiple providers
# - Okta
# - Auth0
# - Azure AD
# - Google Workspace
# - OneLogin
```

**SSO Configuration:**

```yaml
# ~/.ai-shell/security/sso.yaml
sso:
  enabled: true
  provider: okta

  okta:
    domain: example.okta.com
    clientId: YOUR_CLIENT_ID
    clientSecret: ${OKTA_CLIENT_SECRET}  # Use env var
    redirectUri: http://localhost:8080/callback

    # SAML configuration
    saml:
      entryPoint: https://example.okta.com/app/xxx/sso/saml
      issuer: http://www.okta.com/xxx
      cert: /path/to/okta.cert

    # User provisioning
    provisioning:
      autoCreate: true
      defaultRole: developer
      syncGroups: true
      groupMapping:
        "DB-Admins": dba
        "DB-Developers": developer
        "DB-ReadOnly": read-only

    # Session settings
    session:
      lifetime: 8h
      renewalThreshold: 1h
```

### Security Scanning Integration

```bash
# Integrate with security scanners
ai-shell security integrate snyk
ai-shell security integrate dependabot

# Run security scan
ai-shell security scan --full

# Output:
# 🔍 Security Scan Results
#
# Vulnerabilities:
#   ❌ Critical: 0
#   ⚠️  High: 1
#   ⚠️  Medium: 2
#   ℹ️  Low: 5
#
# High Severity:
#   Package: pg@8.10.0
#   CVE: CVE-2024-12345
#   Fix: Update to pg@8.11.3
#   Command: npm update pg
#
# Configuration Issues:
#   ⚠️  Weak password policy detected
#   ⚠️  MFA not enforced for all users
#   ⚠️  Audit log retention < recommended
#
# Recommendations:
#   1. Update vulnerable dependencies
#   2. Strengthen password requirements
#   3. Enforce MFA organization-wide
#   4. Increase audit log retention to 90 days
```

---

## Troubleshooting

### Issue 1: Cannot Access Vault

**Symptoms:**
```
Error: Failed to unlock vault
Cause: Invalid master password or corrupted vault
```

**Solution:**

```bash
# Verify vault integrity
ai-shell vault verify

# Reset vault password (requires backup)
ai-shell vault reset-password

# Restore from backup
ai-shell vault restore --from /backup/vault-2025-10-27.enc

# Last resort: reinitialize (loses all data)
ai-shell vault reinit
```

### Issue 2: MFA Code Not Working

**Symptoms:**
- MFA codes rejected
- "Invalid authentication code" error

**Solution:**

```bash
# Check time synchronization
ai-shell system check-time

# Sync time with NTP server
sudo ntpdate -s time.nist.gov

# Use backup code
ai-shell login --backup-code 8f7d-9c2e

# Disable and re-enable MFA
ai-shell security mfa disable --use-backup-code
ai-shell security mfa enable
```

### Issue 3: Audit Logs Not Recording

**Symptoms:**
- Empty audit logs
- Missing log entries

**Solution:**

```bash
# Check audit configuration
ai-shell audit-log config --show

# Verify log file permissions
ls -la ~/.ai-shell/logs/audit.log

# Enable audit logging
ai-shell audit-log enable

# Increase log verbosity
ai-shell config set audit.verbosity detailed

# Check disk space
df -h ~/.ai-shell/logs/
```

### Issue 4: Permission Denied Errors

**Symptoms:**
```
Error: Permission denied for operation: query:execute
User: charlie@example.com
```

**Solution:**

```bash
# Check user permissions
ai-shell permissions show charlie@example.com

# Grant required permission
ai-shell permissions grant query:execute --to charlie@example.com

# Check role configuration
ai-shell permissions role show developer

# View audit log for denied operations
ai-shell audit-log show --event unauthorized_access --user charlie@example.com
```

### Issue 5: Credential Rotation Failed

**Symptoms:**
```
Error: Failed to rotate credentials
Cause: New password rejected by database
```

**Solution:**

```bash
# Check password policy requirements
ai-shell vault password-policy --check

# Manually set password meeting requirements
ai-shell vault update production --password-env NEW_PASSWORD

# Test connection
ai-shell test connection production

# Review rotation logs
ai-shell audit-log show --action vault:rotate --last 1h
```

---

## Next Steps

### Recommended Learning Path

1. **Master Security Basics** (Completed ✓)
   - You now understand AI-Shell security fundamentals

2. **Explore Audit Logging** (Next: 20 mins)
   - Deep dive into compliance and auditing
   - [Compliance Guide](../enterprise/compliance.md)

3. **Set Up Anomaly Detection** (Next: 25 mins)
   - [Anomaly Detection Tutorial](./anomaly-detection.md)
   - Detect security threats automatically

4. **Implement Autonomous Operations** (Next: 45 mins)
   - [Autonomous DevOps Tutorial](./autonomous-devops.md)
   - Secure autonomous database operations

### Related Documentation

- [Enterprise Security Guide](../enterprise/security.md)
- [Compliance Standards](../enterprise/compliance.md)
- [RBAC Best Practices](../guides/rbac-best-practices.md)
- [Incident Response Playbook](../guides/incident-response.md)

### Security Checklist

**Essential Security Measures:**
- [ ] Vault initialized with strong master password
- [ ] MFA enabled for all users
- [ ] RBAC configured with least privilege
- [ ] Audit logging enabled
- [ ] PII redaction configured
- [ ] Approval workflows set up
- [ ] Credential rotation scheduled
- [ ] Security scanning enabled
- [ ] Backup and recovery tested
- [ ] Incident response plan documented

**Optional Enhancements:**
- [ ] SSO integration configured
- [ ] Hardware key MFA enabled
- [ ] Custom security policies defined
- [ ] Compliance automation enabled
- [ ] Security monitoring integrated
- [ ] Penetration testing scheduled

---

## Feedback

Help us improve security:
- [Report a security issue](https://github.com/your-org/ai-shell/security/advisories/new)
- [Suggest security improvements](https://github.com/your-org/ai-shell/discussions/new)
- [Join security discussion](https://discord.gg/ai-shell)

---

**Last Updated:** 2025-10-28
**Version:** 1.0.0
**Difficulty:** Intermediate
**Security Level:** Enterprise-Grade
