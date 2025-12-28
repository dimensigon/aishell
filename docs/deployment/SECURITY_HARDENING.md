# Security Hardening Guide

Comprehensive security hardening guidelines for AIShell production deployments covering credential management, network security, access control, audit logging, compliance, and encryption.

## Table of Contents

1. [Credential Management](#credential-management)
2. [Network Security](#network-security)
3. [Database Access Control](#database-access-control)
4. [Audit Logging Configuration](#audit-logging-configuration)
5. [Compliance Requirements](#compliance-requirements)
6. [Encryption Settings](#encryption-settings)
7. [Security Scanning](#security-scanning)
8. [Incident Response](#incident-response)

---

## Credential Management

### 1. Vault Configuration

AIShell includes a secure vault for credential storage with AES-256 encryption.

```yaml
# Security configuration
security:
  vault:
    enabled: true
    encryption: aes-256-gcm          # AES-256-GCM encryption
    keyDerivation: pbkdf2            # PBKDF2 key derivation
    iterations: 100000               # 100,000 iterations
    saltLength: 32                   # 32-byte salt
    keyFile: /secure/vault.key       # Secure key storage
    dataFile: /secure/vault.data     # Encrypted data storage
    backupEnabled: true
    backupLocation: /secure/backups/
```

### 2. Storing Credentials

```bash
# Add database credential
ai-shell vault-add DATABASE_URL \
  "postgresql://user:password@host:5432/db" \
  --encrypt

# Add API key
ai-shell vault-add ANTHROPIC_API_KEY \
  "your-api-key-here" \
  --encrypt

# Add Redis password
ai-shell vault-add REDIS_PASSWORD \
  "your-redis-password" \
  --encrypt

# List credentials (masked)
ai-shell vault-list

# Retrieve credential
ai-shell vault-get DATABASE_URL
```

### 3. Environment Variable Management

```bash
# NEVER store credentials in plain text environment files
# Use vault or secret management services

# ❌ WRONG - Plain text credentials
export DATABASE_URL="postgresql://user:password@host/db"

# ✅ CORRECT - Use vault
export DATABASE_URL=$(ai-shell vault-get DATABASE_URL)

# ✅ CORRECT - Use cloud secret manager
export DATABASE_URL=$(aws secretsmanager get-secret-value \
  --secret-id ai-shell/database-url \
  --query SecretString \
  --output text)
```

### 4. Secret Rotation Policy

```yaml
security:
  rotation:
    enabled: true
    policies:
      database_passwords:
        interval: 90                 # Days
        notification: 7              # Days before expiry
      api_keys:
        interval: 180                # Days
        notification: 14
      encryption_keys:
        interval: 365                # Days
        notification: 30
```

### 5. AWS Secrets Manager Integration

```yaml
secrets:
  provider: aws-secretsmanager
  region: us-east-1
  secrets:
    - name: ai-shell/database-url
      key: DATABASE_URL
    - name: ai-shell/anthropic-key
      key: ANTHROPIC_API_KEY
    - name: ai-shell/redis-password
      key: REDIS_PASSWORD
```

```bash
# Grant IAM permissions
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:*:secret:ai-shell/*"
    }
  ]
}
```

---

## Network Security

### 1. Firewall Configuration

```bash
# UFW (Ubuntu/Debian)
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (restrict to specific IPs)
sudo ufw allow from 10.0.0.0/8 to any port 22

# Allow application port (behind load balancer only)
sudo ufw allow from 10.0.1.0/24 to any port 3000

# Allow PostgreSQL (internal network only)
sudo ufw allow from 10.0.2.0/24 to any port 5432

# Allow Redis (internal network only)
sudo ufw allow from 10.0.2.0/24 to any port 6379

# Enable firewall
sudo ufw enable
sudo ufw status
```

### 2. TLS/SSL Configuration

```yaml
security:
  tls:
    enabled: true
    minVersion: TLSv1.2              # Minimum TLS 1.2
    maxVersion: TLSv1.3              # Prefer TLS 1.3
    ciphers:
      - TLS_AES_128_GCM_SHA256
      - TLS_AES_256_GCM_SHA384
      - TLS_CHACHA20_POLY1305_SHA256
      - ECDHE-RSA-AES128-GCM-SHA256
      - ECDHE-RSA-AES256-GCM-SHA384
    certificateFile: /etc/ssl/certs/ai-shell.crt
    keyFile: /etc/ssl/private/ai-shell.key
    caFile: /etc/ssl/certs/ca-bundle.crt
    honorCipherOrder: true
    sessionTickets: false
```

### 3. Database Connection Security

```yaml
databases:
  production:
    ssl:
      enabled: true
      rejectUnauthorized: true       # Verify certificates
      ca: /etc/ssl/certs/db-ca.crt
      cert: /etc/ssl/certs/db-client.crt
      key: /etc/ssl/private/db-client.key
      minVersion: TLSv1.2
```

### 4. Network Segmentation

```yaml
# Network zones
networks:
  public:
    cidr: 0.0.0.0/0
    access: load-balancer-only

  dmz:
    cidr: 10.0.1.0/24
    resources:
      - application-servers
      - load-balancers
    access: public-http

  private:
    cidr: 10.0.2.0/24
    resources:
      - databases
      - cache-servers
    access: dmz-only

  management:
    cidr: 10.0.3.0/24
    resources:
      - monitoring
      - logging
    access: vpn-only
```

### 5. VPN Configuration

```bash
# OpenVPN server configuration
# /etc/openvpn/server.conf
port 1194
proto udp
dev tun
ca /etc/openvpn/ca.crt
cert /etc/openvpn/server.crt
key /etc/openvpn/server.key
dh /etc/openvpn/dh.pem
server 10.8.0.0 255.255.255.0
push "route 10.0.0.0 255.255.0.0"
keepalive 10 120
cipher AES-256-GCM
auth SHA256
user nobody
group nogroup
persist-key
persist-tun
verb 3
```

---

## Database Access Control

### 1. PostgreSQL Security

```sql
-- Create database user with limited privileges
CREATE USER ai_shell_app WITH PASSWORD 'secure-password';

-- Grant minimal required privileges
GRANT CONNECT ON DATABASE ai_shell_prod TO ai_shell_app;
GRANT USAGE ON SCHEMA public TO ai_shell_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ai_shell_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO ai_shell_app;

-- Revoke dangerous privileges
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- Read-only user for reporting
CREATE USER ai_shell_readonly WITH PASSWORD 'secure-password';
GRANT CONNECT ON DATABASE ai_shell_prod TO ai_shell_readonly;
GRANT USAGE ON SCHEMA public TO ai_shell_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ai_shell_readonly;
```

```sql
-- pg_hba.conf - Host-based authentication
# TYPE  DATABASE        USER            ADDRESS                 METHOD
# Reject connections from public networks
hostnossl all         all             0.0.0.0/0               reject

# Allow SSL connections from application servers
hostssl   ai_shell_prod ai_shell_app   10.0.1.0/24            cert
hostssl   ai_shell_prod ai_shell_app   10.0.1.0/24            scram-sha-256

# Allow read-only from reporting tools
hostssl   ai_shell_prod ai_shell_readonly 10.0.3.0/24         scram-sha-256

# Allow local connections with password
local     all           all                                    scram-sha-256
```

```sql
-- postgresql.conf security settings
ssl = on
ssl_cert_file = '/etc/postgresql/server.crt'
ssl_key_file = '/etc/postgresql/server.key'
ssl_ca_file = '/etc/postgresql/root.crt'
ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL'
ssl_prefer_server_ciphers = on
ssl_min_protocol_version = 'TLSv1.2'

password_encryption = scram-sha-256
log_connections = on
log_disconnections = on
log_hostname = off
log_line_prefix = '%t [%p]: user=%u,db=%d,app=%a,client=%h '
```

### 2. Role-Based Access Control (RBAC)

```yaml
security:
  rbac:
    enabled: true
    roles:
      # Admin role - full access
      admin:
        permissions:
          - "databases:*"
          - "queries:*"
          - "backups:*"
          - "security:*"
          - "monitoring:*"

      # Developer role - read/write data
      developer:
        permissions:
          - "databases:connect"
          - "databases:query:read"
          - "databases:query:write"
          - "monitoring:view"

      # Analyst role - read-only
      analyst:
        permissions:
          - "databases:connect"
          - "databases:query:read"
          - "monitoring:view"

      # Operator role - operations
      operator:
        permissions:
          - "databases:connect"
          - "backups:create"
          - "backups:restore"
          - "monitoring:*"

    # User assignments
    users:
      - email: admin@example.com
        role: admin
      - email: dev@example.com
        role: developer
      - email: analyst@example.com
        role: analyst
```

### 3. MySQL Security

```sql
-- Create application user
CREATE USER 'ai_shell_app'@'10.0.1.%' IDENTIFIED BY 'secure-password';
GRANT SELECT, INSERT, UPDATE, DELETE ON ai_shell_prod.* TO 'ai_shell_app'@'10.0.1.%';

-- Require SSL
ALTER USER 'ai_shell_app'@'10.0.1.%' REQUIRE SSL;

-- Create read-only user
CREATE USER 'ai_shell_readonly'@'10.0.3.%' IDENTIFIED BY 'secure-password';
GRANT SELECT ON ai_shell_prod.* TO 'ai_shell_readonly'@'10.0.3.%';
REQUIRE SSL;

FLUSH PRIVILEGES;
```

### 4. MongoDB Security

```javascript
// Create application user
use ai_shell_prod

db.createUser({
  user: "ai_shell_app",
  pwd: "secure-password",
  roles: [
    { role: "readWrite", db: "ai_shell_prod" }
  ]
})

// Create read-only user
db.createUser({
  user: "ai_shell_readonly",
  pwd: "secure-password",
  roles: [
    { role: "read", db: "ai_shell_prod" }
  ]
})
```

---

## Audit Logging Configuration

### 1. Audit Log Settings

```yaml
security:
  audit:
    enabled: true
    destination: /var/log/ai-shell/audit.log
    format: json
    level: info

    # Events to audit
    events:
      - authentication
      - authorization
      - database_connections
      - query_execution
      - data_modifications
      - configuration_changes
      - security_events
      - backup_operations
      - user_management

    # Log rotation
    rotation:
      enabled: true
      frequency: daily
      maxFiles: 365                  # 1 year retention
      maxSize: 100m
      compress: true

    # Log shipping
    shipping:
      enabled: true
      destinations:
        - type: s3
          bucket: ai-shell-audit-logs
          region: us-east-1
          prefix: audit/
        - type: siem
          url: https://siem.example.com/api/logs
          apiKey: ${SIEM_API_KEY}
```

### 2. Audit Log Format

```json
{
  "timestamp": "2025-10-29T10:30:00.000Z",
  "eventType": "query_execution",
  "severity": "info",
  "user": {
    "id": "user-123",
    "email": "dev@example.com",
    "role": "developer",
    "ip": "10.0.1.50"
  },
  "resource": {
    "type": "database",
    "name": "production",
    "operation": "SELECT"
  },
  "details": {
    "query": "SELECT * FROM users WHERE id = $1",
    "parameters": "[REDACTED]",
    "duration": 45,
    "rows": 1
  },
  "outcome": "success",
  "sessionId": "session-456"
}
```

### 3. Security Event Logging

```yaml
security:
  events:
    # Authentication events
    authentication:
      - login_success
      - login_failure
      - logout
      - session_expired
      - mfa_required
      - mfa_success
      - mfa_failure

    # Authorization events
    authorization:
      - access_granted
      - access_denied
      - permission_changed
      - role_changed

    # Security events
    security:
      - sql_injection_detected
      - rate_limit_exceeded
      - suspicious_activity
      - credential_leaked
      - unauthorized_access_attempt

    # Data events
    data:
      - sensitive_data_accessed
      - bulk_data_export
      - data_deletion
      - schema_change
```

---

## Compliance Requirements

### 1. GDPR Compliance

```yaml
compliance:
  gdpr:
    enabled: true

    # Personal data handling
    personal_data:
      encryption: true
      anonymization: true
      retention: 730                 # 2 years max
      rightToErasure: true
      rightToPortability: true

    # Data processing records
    processing_records:
      enabled: true
      location: /var/log/ai-shell/gdpr/

    # Consent management
    consent:
      required: true
      granular: true
      revocable: true
      audit: true

    # Data breach notification
    breach_notification:
      enabled: true
      timeframe: 72                  # Hours
      contacts:
        - dpo@example.com
        - security@example.com
```

### 2. SOX Compliance

```yaml
compliance:
  sox:
    enabled: true

    # Access controls
    access_controls:
      segregation_of_duties: true
      least_privilege: true
      periodic_review: 90            # Days

    # Audit requirements
    audit:
      financial_data_access: true
      configuration_changes: true
      privileged_operations: true
      retention: 2555                # 7 years

    # Change management
    change_management:
      approval_required: true
      testing_required: true
      rollback_plan_required: true
      documentation_required: true
```

### 3. HIPAA Compliance

```yaml
compliance:
  hipaa:
    enabled: true

    # PHI protection
    phi_protection:
      encryption_at_rest: true
      encryption_in_transit: true
      access_controls: true
      audit_logs: true

    # Business associate agreements
    baa:
      required: true
      vendors:
        - anthropic                  # Claude AI
        - aws                        # Cloud provider
        - monitoring_provider

    # Breach notification
    breach_notification:
      enabled: true
      timeframe: 60                  # Days
      authorities:
        - HHS Office for Civil Rights

    # Data retention
    retention:
      minimum: 2190                  # 6 years
      disposal: secure_erasure
```

### 4. PCI DSS Compliance

```yaml
compliance:
  pci_dss:
    enabled: false                   # Only if handling credit cards

    # If enabled:
    requirements:
      - network_security_firewall
      - no_default_passwords
      - cardholder_data_protection
      - encrypted_transmission
      - anti_virus_software
      - secure_systems
      - access_control
      - unique_ids
      - physical_access_restriction
      - network_monitoring
      - security_testing
      - security_policy
```

---

## Encryption Settings

### 1. Data at Rest Encryption

```yaml
encryption:
  at_rest:
    enabled: true

    # Database encryption
    database:
      algorithm: aes-256-gcm
      keyManagement: aws-kms
      kmsKeyId: arn:aws:kms:us-east-1:123456789:key/abc-123
      rotate: true
      rotationInterval: 365          # Days

    # File encryption
    files:
      enabled: true
      algorithm: aes-256-gcm
      backups: true
      logs: true

    # Full disk encryption
    disk:
      enabled: true
      algorithm: aes-xts-256
      provider: luks                 # Linux
```

### 2. Data in Transit Encryption

```yaml
encryption:
  in_transit:
    # Application TLS
    application:
      enabled: true
      minVersion: TLSv1.2
      preferServerCiphers: true
      ciphers:
        - TLS_AES_256_GCM_SHA384
        - TLS_CHACHA20_POLY1305_SHA256
        - ECDHE-RSA-AES256-GCM-SHA384

    # Database connections
    database:
      ssl: required
      verifyServerCert: true
      minVersion: TLSv1.2

    # Redis connections
    redis:
      tls: true
      rejectUnauthorized: true
      minVersion: TLSv1.2

    # Internal service communication
    internal:
      mTLS: true                     # Mutual TLS
      certificateAuthority: /etc/ssl/internal-ca.crt
```

### 3. Application-Level Encryption

```yaml
security:
  application_encryption:
    # Encrypt sensitive query parameters
    query_parameters:
      enabled: true
      algorithm: aes-256-gcm

    # Encrypt PII in logs
    pii_encryption:
      enabled: true
      patterns:
        - email
        - phone
        - ssn
        - credit_card

    # Field-level encryption
    field_level:
      enabled: true
      fields:
        - users.ssn
        - users.credit_card
        - users.bank_account
```

---

## Security Scanning

### 1. Vulnerability Scanning

```bash
# NPM audit
npm audit
npm audit fix --only=prod

# Dependency scanning with Snyk
npm install -g snyk
snyk auth
snyk test
snyk monitor

# Container scanning
docker scan aishell/ai-shell:latest

# SAST (Static Application Security Testing)
npm install -g @microsoft/applicationinsights
npm run lint:security
```

### 2. Penetration Testing Schedule

```yaml
security:
  penetration_testing:
    frequency: quarterly
    scope:
      - web_application
      - api_endpoints
      - database_access
      - network_infrastructure

    vendors:
      - approved_vendor_1
      - approved_vendor_2

    remediation:
      critical: 7                    # Days
      high: 30
      medium: 90
      low: 180
```

### 3. Security Scanning Automation

```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 0 * * 0'              # Weekly

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Run Snyk
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

      - name: Run npm audit
        run: npm audit --production

      - name: SAST scan
        uses: github/codeql-action/analyze@v2
```

---

## Incident Response

### 1. Security Incident Response Plan

```yaml
incident_response:
  # Detection
  detection:
    sources:
      - audit_logs
      - security_alerts
      - monitoring_dashboards
      - user_reports

  # Classification
  classification:
    severity_levels:
      critical:
        examples:
          - data_breach
          - ransomware
          - system_compromise
        response_time: 15             # Minutes
      high:
        examples:
          - sql_injection_attempt
          - unauthorized_access
          - ddos_attack
        response_time: 60
      medium:
        examples:
          - suspicious_activity
          - failed_login_attempts
        response_time: 240
      low:
        examples:
          - policy_violations
          - minor_vulnerabilities
        response_time: 1440

  # Response team
  team:
    primary:
      - role: Security Lead
        contact: security-lead@example.com
        phone: +1-555-SECURE
    secondary:
      - role: DevOps Lead
        contact: devops-lead@example.com
      - role: DBA
        contact: dba@example.com
    escalation:
      - role: CISO
        contact: ciso@example.com

  # Response procedures
  procedures:
    1_detection:
      - identify_incident
      - assess_severity
      - activate_team
    2_containment:
      - isolate_affected_systems
      - preserve_evidence
      - stop_attack_vector
    3_eradication:
      - remove_threat
      - patch_vulnerabilities
      - strengthen_defenses
    4_recovery:
      - restore_systems
      - verify_security
      - resume_operations
    5_post_incident:
      - document_lessons_learned
      - update_procedures
      - improve_defenses

  # Communication
  communication:
    internal:
      - security_team
      - management
      - legal
    external:
      - customers (if data breach)
      - authorities (if required)
      - partners
```

### 2. Data Breach Response

```yaml
data_breach_response:
  immediate_actions:
    - stop_data_exfiltration
    - secure_systems
    - preserve_evidence
    - notify_security_team

  assessment:
    - identify_compromised_data
    - determine_number_of_affected_users
    - assess_impact
    - document_timeline

  notification:
    users:
      timeframe: 72                  # Hours
      method: email
      content: detailed_description
    authorities:
      gdpr: 72                       # Hours
      hipaa: 60                      # Days
    partners:
      timeframe: 24                  # Hours

  remediation:
    - credential_rotation
    - security_patches
    - access_revocation
    - monitoring_enhancement
```

---

**Document Version:** 1.0.0
**Last Updated:** October 29, 2025
**Maintained By:** AIShell Security Team
**Review Cycle:** Quarterly

---

## Security Checklist

- [ ] All credentials stored in vault
- [ ] TLS 1.2+ enabled for all connections
- [ ] Database access restricted to application servers
- [ ] RBAC configured and tested
- [ ] Audit logging enabled
- [ ] Log rotation configured
- [ ] Encryption at rest enabled
- [ ] Encryption in transit enabled
- [ ] Firewall rules configured
- [ ] VPN configured for management access
- [ ] Security scanning automated
- [ ] Incident response plan documented
- [ ] Security team trained
- [ ] Compliance requirements met
- [ ] Vulnerability patching process defined
- [ ] Regular security audits scheduled
