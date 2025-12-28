# Security CLI Quick Reference

Quick command reference for AI-Shell security CLI.

## Vault Commands

```bash
# Add credential (encrypted)
ai-shell vault-add api-key "sk-12345" --encrypt

# List credentials
ai-shell vault-list                    # Redacted
ai-shell vault-list --show-passwords   # Show actual values
ai-shell vault-list --format json      # JSON output

# Get specific credential
ai-shell vault-get api-key

# Remove credential
ai-shell vault-remove old-key

# Encrypt/decrypt
ai-shell vault-encrypt "sensitive-data"
ai-shell vault-decrypt "encrypted-string"

# Rotate encryption key
ai-shell vault-rotate-key
```

## Audit Log Commands

```bash
# Show logs
ai-shell audit-show                          # Recent logs
ai-shell audit-show --limit 50               # Limit results
ai-shell audit-show --user admin             # Filter by user
ai-shell audit-show --action login           # Filter by action
ai-shell audit-show --resource database      # Filter by resource

# Export logs
ai-shell audit-export logs.json --format json
ai-shell audit-export logs.csv --format csv

# Statistics
ai-shell audit-stats

# Search
ai-shell audit-search "failed login"

# Clean old logs
ai-shell audit-clear --before 2024-01-01
```

## RBAC Commands

```bash
# Create role
ai-shell role-create admin --description "Administrator"

# Delete role
ai-shell role-delete deprecated-role

# Grant permissions
ai-shell permissions-grant admin database --actions read,write,delete
ai-shell permissions-grant editor api --actions read,write

# Revoke permissions
ai-shell permissions-revoke editor api

# List permissions
ai-shell permissions-list                # All roles
ai-shell permissions-list john.doe       # User permissions
ai-shell permissions-list --format json  # JSON output

# Check permission
ai-shell permissions-check john.doe database write

# Assign role
ai-shell role-assign john.doe admin

# Unassign role
ai-shell role-unassign john.doe admin
```

## Security Scanning Commands

```bash
# Run scan
ai-shell security-scan                           # Basic scan
ai-shell security-scan --deep                    # Deep scan
ai-shell security-scan --output report.json      # Save report

# Generate report
ai-shell security-report
ai-shell security-report --format json

# List vulnerabilities
ai-shell security-vulnerabilities

# Check compliance
ai-shell security-compliance                     # All standards
ai-shell security-compliance --standard gdpr
ai-shell security-compliance --standard sox
ai-shell security-compliance --standard hipaa
ai-shell security-compliance --format json
```

## Common Workflows

### Setup New User
```bash
ai-shell role-create editor
ai-shell permissions-grant editor content --actions read,write
ai-shell role-assign new-user editor
ai-shell permissions-check new-user content write
```

### Security Audit
```bash
ai-shell security-scan --deep --output scan.json
ai-shell security-compliance --format json > compliance.json
ai-shell audit-export audit-$(date +%Y%m%d).json
```

### Credential Management
```bash
ai-shell vault-add db-prod "postgresql://..." --encrypt
ai-shell vault-list
ai-shell vault-get db-prod
```

### Investigation
```bash
ai-shell audit-show --user suspicious-user
ai-shell audit-show --action failed_login --limit 100
ai-shell audit-search "unauthorized"
```

## Environment Variables

```bash
export VAULT_PASSWORD="your-strong-password"
export AUDIT_LOG_PATH="/var/log/aishell/audit.log"
export PYTHON_PATH="/usr/bin/python3"
```

## Output Formats

Most commands support multiple formats:
- `--format table` (default) - Pretty table
- `--format json` - JSON output
- `--format csv` - CSV format

## Quick Tips

1. **Always encrypt sensitive credentials**: Use `--encrypt` flag
2. **Never use --show-passwords in logs**: Keep credentials redacted
3. **Export audit logs regularly**: For compliance requirements
4. **Run security scans daily**: Catch vulnerabilities early
5. **Use least privilege**: Grant minimal required permissions
6. **Rotate keys quarterly**: `vault-rotate-key` every 90 days
7. **Monitor failed logins**: Check for suspicious activity
8. **Backup your vault**: Export as JSON regularly

## Help

Get help for any command:
```bash
ai-shell vault-add --help
ai-shell audit-show --help
ai-shell permissions-grant --help
ai-shell security-scan --help
```

## Full Documentation

- Complete Guide: `docs/security-cli-guide.md`
- Implementation: `src/cli/README-SECURITY.md`
- Tests: `tests/cli/security-cli.test.ts`
