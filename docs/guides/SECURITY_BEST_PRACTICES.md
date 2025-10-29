# Security Best Practices Guide

## Table of Contents

1. [Overview](#overview)
2. [Vault Usage for Credentials](#vault-usage-for-credentials)
3. [Permission Management](#permission-management)
4. [Audit Logging](#audit-logging)
5. [Encryption Settings](#encryption-settings)
6. [Compliance Features](#compliance-features)
7. [Security Hardening](#security-hardening)
8. [Incident Response](#incident-response)

---

## Overview

Security is paramount in database management. AI-Shell provides comprehensive security features including encrypted credential storage, audit logging, permission management, and compliance tools.

### Security Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                   Security Architecture                       │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
          ┌────────────────────────────────────────┐
          │         Authentication Layer            │
          │  ┌──────────────────────────────────┐  │
          │  │   - Vault (Credential Storage)   │  │
          │  │   - Multi-Factor Authentication  │  │
          │  │   - API Key Management           │  │
          │  │   - OAuth/SAML Integration       │  │
          │  └──────────────────────────────────┘  │
          └──────────┬─────────────────────────────┘
                     │
          ┌──────────▼─────────────────────────────┐
          │        Authorization Layer             │
          │  ┌──────────────────────────────────┐  │
          │  │   - Role-Based Access Control    │  │
          │  │   - Permission Management        │  │
          │  │   - Database User Privileges     │  │
          │  │   - Command Restrictions         │  │
          │  └──────────────────────────────────┘  │
          └──────────┬─────────────────────────────┘
                     │
          ┌──────────▼─────────────────────────────┐
          │           Audit Layer                  │
          │  ┌──────────────────────────────────┐  │
          │  │   - Activity Logging             │  │
          │  │   - Query Auditing               │  │
          │  │   - Access Tracking              │  │
          │  │   - Compliance Reporting         │  │
          │  └──────────────────────────────────┘  │
          └──────────┬─────────────────────────────┘
                     │
          ┌──────────▼─────────────────────────────┐
          │         Encryption Layer               │
          │  ┌──────────────────────────────────┐  │
          │  │   - Data at Rest (AES-256)       │  │
          │  │   - Data in Transit (TLS 1.3)    │  │
          │  │   - Key Management (KMS)         │  │
          │  │   - Backup Encryption            │  │
          │  └──────────────────────────────────┘  │
          └────────────────────────────────────────┘
```

### Security Principles

1. **Defense in Depth**: Multiple layers of security controls
2. **Least Privilege**: Minimum necessary permissions
3. **Zero Trust**: Verify all access attempts
4. **Encryption Everywhere**: Encrypt data at rest and in transit
5. **Audit Everything**: Comprehensive logging and monitoring
6. **Compliance First**: Meet regulatory requirements

---

## Vault Usage for Credentials

### Initializing the Vault

```bash
# Initialize vault with master password
aishell vault init

# Output:
# ✓ Vault initialized successfully
# ✓ Encryption: AES-256-GCM
# ✓ Master key stored at: ~/.aishell/vault/master.key
#
# ⚠ IMPORTANT: Back up your master key securely!
# ⚠ Without it, you cannot access stored credentials!

# Initialize vault with custom location
aishell vault init \
  --vault-path /secure/location/vault \
  --encryption-algorithm AES-256-GCM

# Initialize with hardware security module (HSM)
aishell vault init \
  --hsm-enabled \
  --hsm-slot 0 \
  --hsm-pin-prompt
```

### Storing Credentials

```bash
# Store database password
aishell vault store \
  --key prod-db-password \
  --value-prompt

# You'll be prompted to enter the password securely
# Password: ************

# Store with metadata
aishell vault store \
  --key prod-db-password \
  --value-prompt \
  --metadata '{"database": "prod-db", "rotation-date": "2024-01-15"}'

# Store multiple credentials
aishell vault store-batch << EOF
prod-db-password: value1
staging-db-password: value2
dev-db-password: value3
EOF

# Store from file (for certificates, keys)
aishell vault store \
  --key ssl-certificate \
  --file /path/to/cert.pem

# Store with expiration
aishell vault store \
  --key api-key \
  --value-prompt \
  --expires-in 90d
```

### Retrieving Credentials

```bash
# Retrieve credential
aishell vault retrieve prod-db-password

# Retrieve to environment variable
export DB_PASSWORD=$(aishell vault retrieve prod-db-password)

# Retrieve with audit logging
aishell vault retrieve prod-db-password \
  --audit-reason "Database maintenance"

# Retrieve with time limit
aishell vault retrieve prod-db-password \
  --valid-for 1h
```

### Managing Credentials

```bash
# List all stored credentials
aishell vault list

# Output:
# Key                  | Created            | Expires    | Last Accessed
# ---------------------|--------------------| -----------|---------------
# prod-db-password     | 2024-01-01 10:00  | Never      | 2024-01-15
# api-key              | 2024-01-10 14:30  | 2024-04-10 | 2024-01-12
# ssl-certificate      | 2024-01-05 09:00  | 2025-01-05 | 2024-01-15

# Show credential details
aishell vault show prod-db-password

# Update credential
aishell vault update prod-db-password \
  --value-prompt

# Delete credential
aishell vault delete api-key

# Rotate credential
aishell vault rotate prod-db-password \
  --keep-history 3
```

### Vault Security

```bash
# Lock vault
aishell vault lock

# Unlock vault
aishell vault unlock

# Change master password
aishell vault change-password

# Backup vault
aishell vault backup \
  --output vault-backup-$(date +%Y%m%d).enc \
  --encrypt

# Restore vault
aishell vault restore \
  --input vault-backup-20240115.enc

# Enable auto-lock
aishell vault configure \
  --auto-lock-timeout 15m

# Enable two-factor authentication
aishell vault configure \
  --enable-2fa \
  --2fa-method totp
```

### Credential Rotation

```bash
# Configure automatic rotation
aishell vault rotation-policy prod-db-password \
  --interval 90d \
  --notify email,slack

# Rotate now
aishell vault rotate prod-db-password

# Rotate all credentials
aishell vault rotate-all \
  --dry-run

# Schedule rotation
aishell vault schedule-rotation \
  --all \
  --schedule "0 2 1 * *"  # First day of month at 2 AM
```

---

## Permission Management

### User Management

```bash
# Create database user
aishell security user create \
  --connection prod-db \
  --username app_user \
  --password-prompt \
  --role read-only

# Grant permissions
aishell security grant prod-db \
  --user app_user \
  --database myapp \
  --privileges SELECT,INSERT,UPDATE

# Revoke permissions
aishell security revoke prod-db \
  --user app_user \
  --database myapp \
  --privileges DELETE,DROP

# List user permissions
aishell security show-privileges prod-db \
  --user app_user
```

### Role-Based Access Control (RBAC)

```bash
# Create role
aishell security role create prod-db \
  --name developer \
  --privileges SELECT,INSERT,UPDATE \
  --schemas public,app

# Create read-only role
aishell security role create prod-db \
  --name readonly \
  --privileges SELECT \
  --all-schemas

# Create admin role
aishell security role create prod-db \
  --name admin \
  --privileges ALL \
  --with-grant-option

# Assign role to user
aishell security grant-role prod-db \
  --user john_doe \
  --role developer

# Remove role from user
aishell security revoke-role prod-db \
  --user john_doe \
  --role developer

# List all roles
aishell security list-roles prod-db
```

### Database-Level Permissions

#### PostgreSQL Permissions

```bash
# Grant database-level permissions
aishell security grant prod-db \
  --user app_user \
  --database myapp \
  --privileges CONNECT,TEMP

# Grant schema permissions
aishell security grant prod-db \
  --user app_user \
  --schema public \
  --privileges USAGE,CREATE

# Grant table permissions
aishell security grant prod-db \
  --user app_user \
  --table orders \
  --privileges SELECT,INSERT,UPDATE

# Grant column-level permissions
aishell security grant prod-db \
  --user analyst \
  --table users \
  --columns id,name,email \
  --privileges SELECT

# Grant function permissions
aishell security grant prod-db \
  --user app_user \
  --function calculate_total \
  --privileges EXECUTE
```

#### MySQL Permissions

```bash
# Grant global permissions
aishell security grant mysql-prod \
  --user app_user \
  --privileges SELECT,INSERT,UPDATE \
  --level global

# Grant database permissions
aishell security grant mysql-prod \
  --user app_user \
  --database ecommerce \
  --privileges ALL

# Grant table permissions
aishell security grant mysql-prod \
  --user app_user \
  --table orders \
  --privileges SELECT,INSERT,UPDATE,DELETE

# Show grants
aishell security show-grants mysql-prod \
  --user app_user
```

#### MongoDB Permissions

```bash
# Create user with read-only access
aishell security user create mongo-prod \
  --username readonly_user \
  --database analytics \
  --role read

# Create user with read-write access
aishell security user create mongo-prod \
  --username app_user \
  --database myapp \
  --role readWrite

# Create user with custom roles
aishell security user create mongo-prod \
  --username admin_user \
  --database admin \
  --roles userAdminAnyDatabase,dbAdminAnyDatabase
```

### Row-Level Security

```bash
# Enable row-level security (PostgreSQL)
aishell security enable-rls prod-db \
  --table orders

# Create policy
aishell security create-policy prod-db \
  --table orders \
  --name user_orders_policy \
  --using "user_id = current_user_id()" \
  --with-check "user_id = current_user_id()"

# Example policies
# Sales rep can only see their own orders
aishell query run prod-db --sql "
  CREATE POLICY sales_rep_policy ON orders
  FOR SELECT
  TO sales_rep
  USING (sales_rep_id = current_user_id());
"

# Manager can see all orders in their region
aishell query run prod-db --sql "
  CREATE POLICY manager_policy ON orders
  FOR ALL
  TO manager
  USING (region = current_user_region());
"
```

---

## Audit Logging

### Enable Audit Logging

```bash
# Enable comprehensive audit logging
aishell security audit enable prod-db \
  --log-level detailed \
  --log-location ~/.aishell/audit/prod-db/ \
  --rotation daily \
  --retention 90d

# Enable for specific operations
aishell security audit enable prod-db \
  --operations DDL,DML,DCL \
  --exclude-select  # Don't log SELECT queries

# Enable with filters
aishell security audit enable prod-db \
  --filter-users admin,dba \
  --filter-tables sensitive_data,financial_records \
  --filter-operations DELETE,UPDATE,DROP
```

### Audit Log Format

```bash
# Configure audit log format
aishell security audit configure prod-db \
  --format json \
  --include-query-text \
  --include-client-info \
  --include-performance-metrics

# Sample audit log entry (JSON):
# {
#   "timestamp": "2024-01-15T14:30:00Z",
#   "user": "admin",
#   "database": "prod-db",
#   "operation": "UPDATE",
#   "table": "users",
#   "query": "UPDATE users SET role = 'admin' WHERE id = 123",
#   "rows_affected": 1,
#   "duration_ms": 12,
#   "client_ip": "192.168.1.100",
#   "client_app": "aishell",
#   "success": true
# }
```

### Viewing Audit Logs

```bash
# View recent audit logs
aishell security audit logs prod-db \
  --limit 100

# Filter by user
aishell security audit logs prod-db \
  --user admin \
  --period 24h

# Filter by operation
aishell security audit logs prod-db \
  --operation DELETE,DROP \
  --period 7d

# Filter by table
aishell security audit logs prod-db \
  --table sensitive_data \
  --period 30d

# Search audit logs
aishell security audit search prod-db \
  --query "DROP TABLE" \
  --period 90d

# Export audit logs
aishell security audit export prod-db \
  --period 30d \
  --format csv \
  --output audit-export-$(date +%Y%m%d).csv
```

### Audit Analytics

```bash
# Generate audit summary
aishell security audit summary prod-db \
  --period 30d

# Output:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Audit Summary (Last 30 days)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  Total Events: 1,234,567
#  Unique Users: 45
#  Failed Attempts: 123 (0.01%)
#
#  TOP USERS BY ACTIVITY:
#  1. app_user: 456,789 operations
#  2. admin: 123,456 operations
#  3. analyst: 89,012 operations
#
#  OPERATIONS BREAKDOWN:
#  - SELECT: 89% (1,098,765)
#  - INSERT: 7% (86,420)
#  - UPDATE: 3% (37,035)
#  - DELETE: 0.5% (6,173)
#  - DDL: 0.5% (6,174)
#
#  SECURITY EVENTS:
#  ⚠ 12 failed login attempts (user: unknown_user)
#  ⚠ 3 privilege escalation attempts (user: temp_user)
#  ✓ 0 SQL injection attempts detected
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Detect suspicious activity
aishell security audit anomalies prod-db \
  --period 30d \
  --sensitivity high

# Compliance report
aishell security audit compliance prod-db \
  --standard SOC2 \
  --period 90d \
  --output compliance-report.pdf
```

### Tamper-Proof Logging

```bash
# Enable tamper-proof logging (blockchain-based)
aishell security audit enable-tamperproof prod-db \
  --blockchain-type private \
  --verification-interval 1h

# Verify log integrity
aishell security audit verify-integrity prod-db \
  --period 30d

# Output:
# ✓ Audit log integrity verified
# ✓ All 1,234,567 entries are intact
# ✓ No tampering detected
# ✓ Blockchain hashes valid
```

---

## Encryption Settings

### Data at Rest Encryption

```bash
# Enable database encryption (PostgreSQL)
aishell security encrypt enable prod-db \
  --method transparent-data-encryption \
  --algorithm AES-256

# Enable tablespace encryption
aishell security encrypt enable prod-db \
  --tablespace pg_default \
  --encryption-key ~/.aishell/keys/db-encryption.key

# Encrypt specific tables
aishell security encrypt-table prod-db \
  --table sensitive_data \
  --algorithm AES-256-GCM

# Encrypt columns
aishell security encrypt-column prod-db \
  --table users \
  --columns ssn,credit_card \
  --algorithm AES-256
```

### Data in Transit Encryption

```bash
# Enable SSL/TLS for connections
aishell security ssl enable prod-db \
  --cert /path/to/server.crt \
  --key /path/to/server.key \
  --ca /path/to/ca.crt \
  --mode require

# Generate self-signed certificate
aishell security ssl generate-cert \
  --hostname db.example.com \
  --output /path/to/certs/

# Verify SSL configuration
aishell security ssl verify prod-db

# Force SSL for all connections
aishell connection update prod-db \
  --ssl-mode require \
  --ssl-verify-ca true
```

### Backup Encryption

```bash
# Enable backup encryption
aishell backup create prod-db \
  --name encrypted-backup \
  --encrypt \
  --encryption-key ~/.aishell/keys/backup.key

# Use password-based encryption
aishell backup create prod-db \
  --name password-encrypted \
  --encrypt \
  --password-prompt

# Configure default backup encryption
aishell config set backup.encryption.enabled true
aishell config set backup.encryption.algorithm AES-256-GCM
```

### Key Management

```bash
# Generate encryption key
aishell security keygen \
  --algorithm AES-256 \
  --output ~/.aishell/keys/database.key

# Rotate encryption keys
aishell security rotate-key prod-db \
  --new-key ~/.aishell/keys/database-new.key \
  --keep-old-key-for 30d

# Use AWS KMS
aishell security configure-kms aws \
  --region us-east-1 \
  --key-id arn:aws:kms:us-east-1:123456789:key/abc-123

# Use Azure Key Vault
aishell security configure-kms azure \
  --vault-name my-key-vault \
  --key-name database-encryption-key

# Use GCP Cloud KMS
aishell security configure-kms gcp \
  --project my-project \
  --location us-central1 \
  --keyring my-keyring \
  --key database-key
```

---

## Compliance Features

### GDPR Compliance

```bash
# Enable GDPR features
aishell security compliance enable gdpr prod-db

# Data subject access request
aishell security gdpr data-export prod-db \
  --user-id 12345 \
  --format json \
  --output user-data-export.json

# Right to be forgotten (delete user data)
aishell security gdpr delete-user prod-db \
  --user-id 12345 \
  --anonymize \
  --audit-log

# Data processing inventory
aishell security gdpr inventory prod-db \
  --output data-processing-inventory.pdf

# Consent management
aishell security gdpr consent-status prod-db \
  --user-id 12345

# Breach notification
aishell security gdpr breach-report prod-db \
  --incident-id INC-2024-001 \
  --output breach-report.pdf
```

### HIPAA Compliance

```bash
# Enable HIPAA features
aishell security compliance enable hipaa prod-db

# Encrypt PHI (Protected Health Information)
aishell security hipaa encrypt-phi prod-db \
  --table patients \
  --phi-columns ssn,medical_record_number,diagnosis

# Access control for PHI
aishell security hipaa access-control prod-db \
  --minimum-necessary-standard \
  --audit-all-access

# Business Associate Agreement (BAA) compliance
aishell security hipaa baa-check prod-db \
  --output baa-compliance-report.pdf
```

### PCI-DSS Compliance

```bash
# Enable PCI-DSS features
aishell security compliance enable pci-dss prod-db

# Secure cardholder data
aishell security pci-dss secure-cardholder-data prod-db \
  --table payments \
  --card-number-column cc_number \
  --cvv-column cvv \
  --tokenize

# Requirement 10: Track and monitor all access
aishell security pci-dss enable-tracking prod-db \
  --comprehensive-audit \
  --log-retention 12m

# Vulnerability scan
aishell security pci-dss scan prod-db \
  --output vulnerability-report.pdf
```

### SOC 2 Compliance

```bash
# Enable SOC 2 features
aishell security compliance enable soc2 prod-db

# Generate SOC 2 compliance report
aishell security soc2 report prod-db \
  --period 12m \
  --trust-service-criteria security,availability \
  --output soc2-report.pdf

# Control testing
aishell security soc2 test-controls prod-db \
  --output control-test-results.pdf
```

---

## Security Hardening

### Database Hardening

```bash
# Run security audit
aishell security audit-database prod-db

# Output:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Database Security Audit
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  ✓ SSL/TLS enabled
#  ✓ Password policy: Strong
#  ⚠ Default 'postgres' user exists
#  ✗ Weak passwords detected (2 users)
#  ✓ Audit logging enabled
#  ⚠ Some users have unnecessary privileges
#  ✓ Encryption at rest enabled
#  ✗ Public schema accessible to all users
#  ✓ No SQL injection vulnerabilities found
#
#  RECOMMENDATIONS:
#  1. Disable or rename default 'postgres' user
#  2. Enforce password rotation for 2 users
#  3. Review and revoke unnecessary privileges
#  4. Restrict public schema access
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Apply hardening recommendations
aishell security harden prod-db \
  --apply-recommendations \
  --dry-run

# Manual hardening steps
aishell security harden prod-db \
  --disable-default-users \
  --enforce-ssl \
  --restrict-public-schema \
  --enable-password-policy
```

### Network Security

```bash
# Configure firewall rules
aishell security firewall prod-db \
  --allow-ip 192.168.1.0/24 \
  --allow-ip 10.0.0.50 \
  --deny-all

# Enable IP whitelisting
aishell security whitelist prod-db \
  --add 192.168.1.100 \
  --add 192.168.1.101 \
  --enable

# Configure connection limits
aishell security limits prod-db \
  --max-connections 100 \
  --max-connections-per-user 10 \
  --connection-timeout 300
```

### Password Policies

```bash
# Configure password policy
aishell security password-policy prod-db \
  --min-length 12 \
  --require-uppercase \
  --require-lowercase \
  --require-numbers \
  --require-special-chars \
  --expiration-days 90 \
  --history-count 5

# Enforce password changes
aishell security enforce-password-change prod-db \
  --all-users \
  --notify

# Check password strength
aishell security check-passwords prod-db \
  --report weak-passwords.txt
```

---

## Incident Response

### Security Incident Workflow

```bash
# Detect security incident
aishell security detect-incident prod-db

# Lock down database (emergency)
aishell security lockdown prod-db \
  --reason "Security incident" \
  --allow-list dba,incident_response

# Investigate incident
aishell security investigate prod-db \
  --incident-id INC-2024-001 \
  --time-range "2024-01-15 10:00 to 2024-01-15 12:00"

# Collect forensic data
aishell security forensics prod-db \
  --collect-logs \
  --collect-queries \
  --collect-connections \
  --output forensics-$(date +%Y%m%d).tar.gz

# Generate incident report
aishell security incident-report \
  --incident-id INC-2024-001 \
  --output incident-report.pdf
```

### Recovery

```bash
# Restore from clean backup
aishell backup restore prod-db \
  --name pre-incident-backup \
  --verify-integrity

# Reset compromised credentials
aishell security reset-credentials prod-db \
  --affected-users user1,user2,user3

# Review and fix vulnerabilities
aishell security vulnerability-scan prod-db \
  --fix-recommended
```

---

## Best Practices Checklist

```bash
# Generate security checklist
aishell security checklist prod-db

# Output:
# SECURITY BEST PRACTICES CHECKLIST
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  AUTHENTICATION & AUTHORIZATION
#  ✓ Vault enabled for credential storage
#  ✓ Strong password policy enforced
#  ✓ Multi-factor authentication enabled
#  ✓ Role-based access control implemented
#  ✓ Least privilege principle applied
#
#  ENCRYPTION
#  ✓ SSL/TLS enabled for connections
#  ✓ Data at rest encrypted
#  ✓ Backup encryption enabled
#  ⚠ Key rotation not scheduled
#
#  AUDITING
#  ✓ Audit logging enabled
#  ✓ Comprehensive event tracking
#  ✓ Log retention configured (90 days)
#  ✓ Tamper-proof logging enabled
#
#  NETWORK SECURITY
#  ✓ Firewall rules configured
#  ✓ IP whitelisting enabled
#  ⚠ VPN recommended for remote access
#
#  COMPLIANCE
#  ✓ GDPR features enabled
#  ✗ PCI-DSS compliance not configured
#  ✓ SOC 2 controls in place
#
#  MONITORING
#  ✓ Security alerts configured
#  ✓ Anomaly detection enabled
#  ✓ Incident response plan documented
#
#  BACKUP & RECOVERY
#  ✓ Regular backups scheduled
#  ✓ Backup verification enabled
#  ✓ Disaster recovery plan tested
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Next Steps

- Configure [Integration Guide](./INTEGRATION_GUIDE.md)
- Review [Monitoring & Analytics](./MONITORING_ANALYTICS.md)
- Check [Troubleshooting Guide](../TROUBLESHOOTING.md)

---

*Last Updated: 2024-01-15 | Version: 2.0.0*
