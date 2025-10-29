# Troubleshooting Guide

## Table of Contents

1. [Common Errors and Solutions](#common-errors-and-solutions)
2. [Database Connection Issues](#database-connection-issues)
3. [Command Not Found Errors](#command-not-found-errors)
4. [Performance Issues](#performance-issues)
5. [Backup and Restore Problems](#backup-and-restore-problems)
6. [Security and Authentication Issues](#security-and-authentication-issues)
7. [Integration Problems](#integration-problems)
8. [FAQ](#faq)

---

## Common Errors and Solutions

### Error: "Command not found: aishell"

**Symptoms:**
```bash
$ aishell --version
bash: aishell: command not found
```

**Solutions:**

1. **Check if AI-Shell is installed:**
   ```bash
   npm list -g @aishell/cli
   ```

2. **Install if not present:**
   ```bash
   npm install -g @aishell/cli
   ```

3. **Check npm global bin path:**
   ```bash
   npm bin -g
   # Output: /usr/local/bin (or similar)

   # Ensure it's in your PATH
   echo $PATH | grep $(npm bin -g)
   ```

4. **Add to PATH if missing (add to ~/.bashrc or ~/.zshrc):**
   ```bash
   export PATH="$(npm bin -g):$PATH"
   source ~/.bashrc
   ```

5. **Use npx as alternative:**
   ```bash
   npx @aishell/cli --version
   ```

---

### Error: "Permission denied"

**Symptoms:**
```bash
$ aishell connection add ...
Error: EACCES: permission denied, open '/home/user/.aishell/config.json'
```

**Solutions:**

1. **Check file permissions:**
   ```bash
   ls -la ~/.aishell/
   ```

2. **Fix ownership:**
   ```bash
   sudo chown -R $USER:$USER ~/.aishell/
   chmod -R 755 ~/.aishell/
   ```

3. **Reinstall with correct permissions:**
   ```bash
   npm uninstall -g @aishell/cli
   npm install -g @aishell/cli
   ```

---

### Error: "Configuration file not found"

**Symptoms:**
```bash
Error: Configuration file not found at ~/.aishell/config.json
```

**Solutions:**

1. **Initialize AI-Shell:**
   ```bash
   aishell init
   ```

2. **Manually create config directory:**
   ```bash
   mkdir -p ~/.aishell/{vault,logs,backups}
   aishell init --force
   ```

3. **Use custom config location:**
   ```bash
   export AISHELL_CONFIG_PATH=/path/to/custom/config.json
   aishell init
   ```

---

### Error: "Invalid JSON in configuration"

**Symptoms:**
```bash
Error: Unexpected token } in JSON at position 234
```

**Solutions:**

1. **Validate configuration file:**
   ```bash
   cat ~/.aishell/config.json | json_pp
   ```

2. **Reset configuration:**
   ```bash
   mv ~/.aishell/config.json ~/.aishell/config.json.backup
   aishell init
   ```

3. **Use validation tool:**
   ```bash
   aishell config validate
   ```

---

## Database Connection Issues

### Error: "Connection timeout"

**Symptoms:**
```bash
Error: Connection to database timed out after 30000ms
```

**Solutions:**

1. **Check network connectivity:**
   ```bash
   ping db.example.com
   telnet db.example.com 5432
   ```

2. **Increase timeout:**
   ```bash
   aishell connection update prod-db --timeout 60000
   ```

3. **Check firewall rules:**
   ```bash
   # On database server
   sudo ufw status
   sudo ufw allow from YOUR_IP to any port 5432
   ```

4. **Verify database is running:**
   ```bash
   # PostgreSQL
   sudo systemctl status postgresql

   # MySQL
   sudo systemctl status mysql
   ```

5. **Check connection limits:**
   ```bash
   # PostgreSQL
   aishell query run prod-db --sql "SHOW max_connections"
   aishell query run prod-db --sql "SELECT count(*) FROM pg_stat_activity"
   ```

---

### Error: "Authentication failed"

**Symptoms:**
```bash
Error: password authentication failed for user "dbuser"
```

**Solutions:**

1. **Verify credentials:**
   ```bash
   aishell vault retrieve prod-db-password
   ```

2. **Test connection manually:**
   ```bash
   # PostgreSQL
   psql -h db.example.com -U dbuser -d mydb

   # MySQL
   mysql -h db.example.com -u dbuser -p mydb
   ```

3. **Update password in vault:**
   ```bash
   aishell vault update prod-db-password --value-prompt
   ```

4. **Check pg_hba.conf (PostgreSQL):**
   ```bash
   # On database server
   sudo cat /etc/postgresql/14/main/pg_hba.conf

   # Should have line like:
   # host    all    all    YOUR_IP/32    md5
   ```

5. **Check user permissions:**
   ```bash
   # PostgreSQL
   aishell query run prod-db --sql "
     SELECT * FROM pg_roles WHERE rolname = 'dbuser'
   "
   ```

---

### Error: "SSL connection required"

**Symptoms:**
```bash
Error: Server requires SSL connection
```

**Solutions:**

1. **Enable SSL in connection:**
   ```bash
   aishell connection update prod-db \
     --ssl-mode require \
     --ssl-cert /path/to/client-cert.pem \
     --ssl-key /path/to/client-key.pem \
     --ssl-ca /path/to/ca-cert.pem
   ```

2. **Use self-signed certificate:**
   ```bash
   aishell connection update prod-db --ssl-mode require --ssl-verify-ca false
   ```

3. **Download server certificate:**
   ```bash
   # PostgreSQL
   openssl s_client -connect db.example.com:5432 -starttls postgres < /dev/null 2>/dev/null | openssl x509 -outform PEM > server-cert.pem
   ```

---

### Error: "Too many connections"

**Symptoms:**
```bash
Error: FATAL: sorry, too many clients already
```

**Solutions:**

1. **Check current connections:**
   ```bash
   aishell monitor connections prod-db
   ```

2. **Kill idle connections:**
   ```bash
   # PostgreSQL
   aishell query run prod-db --sql "
     SELECT pg_terminate_backend(pid)
     FROM pg_stat_activity
     WHERE state = 'idle'
     AND state_change < now() - interval '10 minutes'
   "
   ```

3. **Increase max_connections:**
   ```bash
   # PostgreSQL (requires restart)
   aishell query run prod-db --sql "ALTER SYSTEM SET max_connections = 200"
   # Then restart PostgreSQL
   ```

4. **Use connection pooling:**
   ```bash
   aishell connection update prod-db \
     --pool-min 5 \
     --pool-max 20
   ```

---

## Command Not Found Errors

### Error: "Unknown command"

**Symptoms:**
```bash
$ aishell unknown-command
Error: Unknown command: unknown-command
```

**Solutions:**

1. **List available commands:**
   ```bash
   aishell --help
   ```

2. **Check command spelling:**
   ```bash
   aishell connection list  # Correct
   aishell connections list # Incorrect
   ```

3. **Update to latest version:**
   ```bash
   npm update -g @aishell/cli
   ```

---

### Error: "Missing required argument"

**Symptoms:**
```bash
Error: Missing required argument: --name
```

**Solutions:**

1. **Check command syntax:**
   ```bash
   aishell backup create --help
   ```

2. **Provide all required arguments:**
   ```bash
   aishell backup create prod-db --name my-backup
   ```

---

## Performance Issues

### Issue: Slow query execution

**Symptoms:**
- Queries taking longer than expected
- High CPU usage
- Slow application response

**Solutions:**

1. **Analyze query performance:**
   ```bash
   aishell query analyze prod-db \
     --sql "SELECT * FROM orders WHERE user_id = 123" \
     --explain
   ```

2. **Check for missing indexes:**
   ```bash
   aishell optimize suggest-indexes prod-db \
     --sql "SELECT * FROM orders WHERE user_id = 123"
   ```

3. **Find slow queries:**
   ```bash
   aishell optimize slow-queries prod-db \
     --threshold 1000ms \
     --limit 10
   ```

4. **Optimize query:**
   ```bash
   aishell optimize rewrite prod-db \
     --sql "SELECT * FROM orders WHERE user_id = 123"
   ```

5. **Update table statistics:**
   ```bash
   # PostgreSQL
   aishell query run prod-db --sql "ANALYZE orders"

   # MySQL
   aishell query run prod-db --sql "ANALYZE TABLE orders"
   ```

---

### Issue: High memory usage

**Symptoms:**
- Database consuming excessive memory
- System swapping
- Out of memory errors

**Solutions:**

1. **Check memory usage:**
   ```bash
   aishell monitor resources prod-db
   ```

2. **Identify memory-intensive queries:**
   ```bash
   aishell monitor top-queries prod-db \
     --sort-by memory
   ```

3. **Adjust memory settings (PostgreSQL):**
   ```bash
   aishell query run prod-db --sql "
     ALTER SYSTEM SET shared_buffers = '4GB';
     ALTER SYSTEM SET work_mem = '64MB';
     ALTER SYSTEM SET maintenance_work_mem = '512MB';
   "
   # Requires restart
   ```

4. **Clear cache:**
   ```bash
   aishell cache clear prod-db
   ```

---

### Issue: Disk space running out

**Symptoms:**
```bash
Error: No space left on device
```

**Solutions:**

1. **Check disk usage:**
   ```bash
   aishell monitor disk prod-db
   ```

2. **Find large tables:**
   ```bash
   aishell query run prod-db --sql "
     SELECT
       schemaname || '.' || tablename as table,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
     FROM pg_tables
     WHERE schemaname = 'public'
     ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
     LIMIT 10
   "
   ```

3. **Clean up old backups:**
   ```bash
   aishell backup cleanup prod-db --older-than 30d
   ```

4. **Vacuum database:**
   ```bash
   # PostgreSQL
   aishell query run prod-db --sql "VACUUM FULL"
   ```

5. **Archive old data:**
   ```bash
   # Move old logs to archive table
   aishell query run prod-db --sql "
     INSERT INTO logs_archive SELECT * FROM logs WHERE created_at < NOW() - INTERVAL '90 days';
     DELETE FROM logs WHERE created_at < NOW() - INTERVAL '90 days';
   "
   ```

---

## Backup and Restore Problems

### Error: "Backup failed"

**Symptoms:**
```bash
Error: Backup failed: disk quota exceeded
```

**Solutions:**

1. **Check available disk space:**
   ```bash
   df -h ~/.aishell/backups/
   ```

2. **Enable compression:**
   ```bash
   aishell backup create prod-db \
     --name compressed-backup \
     --compress \
     --compression-level 9
   ```

3. **Backup to cloud:**
   ```bash
   aishell backup create prod-db \
     --name cloud-backup \
     --upload s3 \
     --no-local-copy
   ```

4. **Clean up old backups:**
   ```bash
   aishell backup cleanup prod-db --keep-days 7
   ```

---

### Error: "Restore failed: version mismatch"

**Symptoms:**
```bash
Error: Backup was created with PostgreSQL 13, current version is 14
```

**Solutions:**

1. **Check database versions:**
   ```bash
   aishell connection show prod-db
   ```

2. **Use compatible restore method:**
   ```bash
   # Use pg_restore instead of direct copy
   aishell backup restore prod-db \
     --name backup-pg13 \
     --method logical
   ```

3. **Upgrade backup:**
   ```bash
   aishell backup upgrade \
     --name backup-pg13 \
     --to-version 14
   ```

---

### Error: "Backup integrity check failed"

**Symptoms:**
```bash
Error: Backup file is corrupted or incomplete
```

**Solutions:**

1. **Verify backup:**
   ```bash
   aishell backup verify prod-db --name my-backup --verbose
   ```

2. **Use previous backup:**
   ```bash
   aishell backup list prod-db --sort-by date
   aishell backup restore prod-db --name previous-backup
   ```

3. **Restore from cloud:**
   ```bash
   aishell backup download prod-db \
     --source s3://backups/my-backup \
     --verify
   ```

---

## Security and Authentication Issues

### Error: "Vault is locked"

**Symptoms:**
```bash
Error: Vault is locked. Please unlock it first.
```

**Solutions:**

1. **Unlock vault:**
   ```bash
   aishell vault unlock
   ```

2. **Enable auto-unlock:**
   ```bash
   aishell vault configure --auto-unlock
   ```

3. **Reset vault (last resort):**
   ```bash
   aishell vault reset
   # WARNING: This will delete all stored credentials!
   ```

---

### Error: "Insufficient permissions"

**Symptoms:**
```bash
Error: Permission denied: must be owner of table orders
```

**Solutions:**

1. **Check user permissions:**
   ```bash
   aishell security show-privileges prod-db --user current
   ```

2. **Grant required permissions:**
   ```bash
   aishell security grant prod-db \
     --user dbuser \
     --table orders \
     --privileges SELECT,INSERT,UPDATE
   ```

3. **Switch to admin user:**
   ```bash
   aishell connection add prod-db-admin \
     --type postgresql \
     --host db.example.com \
     --database mydb \
     --username postgres
   ```

---

## Integration Problems

### Error: "Slack webhook failed"

**Symptoms:**
```bash
Error: Failed to send message to Slack: invalid_webhook
```

**Solutions:**

1. **Test webhook:**
   ```bash
   curl -X POST -H 'Content-type: application/json' \
     --data '{"text":"Test message"}' \
     YOUR_WEBHOOK_URL
   ```

2. **Reconfigure webhook:**
   ```bash
   aishell integration slack configure \
     --webhook https://hooks.slack.com/services/NEW/WEBHOOK/URL
   ```

3. **Check Slack app permissions:**
   - Go to Slack App settings
   - Verify webhook is active
   - Check channel permissions

---

### Error: "Email delivery failed"

**Symptoms:**
```bash
Error: SMTP connection failed: 535 Authentication failed
```

**Solutions:**

1. **Verify SMTP settings:**
   ```bash
   aishell integration email test --verbose
   ```

2. **Update credentials:**
   ```bash
   aishell integration email configure \
     --smtp smtp.gmail.com:587 \
     --username your-email@gmail.com \
     --password-prompt
   ```

3. **Enable less secure apps (Gmail):**
   - Go to Google Account settings
   - Security → Less secure app access
   - Or use App Password

4. **Test with telnet:**
   ```bash
   telnet smtp.gmail.com 587
   ```

---

## FAQ

### Q: How do I reset my configuration?

**A:**
```bash
# Backup current config
cp ~/.aishell/config.json ~/.aishell/config.json.backup

# Reset
rm ~/.aishell/config.json
aishell init
```

---

### Q: Can I use AI-Shell with multiple databases simultaneously?

**A:** Yes! Add multiple connections:
```bash
aishell connection add prod-db --type postgresql ...
aishell connection add staging-db --type mysql ...
aishell connection add mongo-db --type mongodb ...

# Use with specific connection
aishell query run prod-db --sql "SELECT..."
aishell query run staging-db --sql "SELECT..."
```

---

### Q: How do I migrate data between databases?

**A:**
```bash
# Export from source
aishell data export source-db \
  --table users \
  --output users.csv

# Import to target
aishell data import target-db \
  --table users \
  --input users.csv

# Or use direct transfer
aishell data transfer \
  --source source-db \
  --target target-db \
  --table users
```

---

### Q: How do I schedule automated tasks?

**A:**
```bash
# Using cron
crontab -e

# Add entry:
0 2 * * * /usr/local/bin/aishell backup create prod-db --name daily-backup

# Or use AI-Shell's built-in scheduler
aishell backup schedule prod-db \
  --name daily-backup \
  --schedule "0 2 * * *"
```

---

### Q: How do I upgrade AI-Shell?

**A:**
```bash
# Check current version
aishell --version

# Update to latest
npm update -g @aishell/cli

# Verify update
aishell --version

# Run post-upgrade checks
aishell doctor
```

---

### Q: Where are logs stored?

**A:**
```bash
# Default log location
~/.aishell/logs/

# View logs
tail -f ~/.aishell/logs/aishell.log

# Change log location
aishell config set logging.file /custom/path/aishell.log

# View specific log
aishell logs --type error --limit 50
```

---

### Q: How do I report a bug?

**A:**

1. **Collect diagnostic information:**
   ```bash
   aishell doctor --verbose > diagnostic-report.txt
   ```

2. **Include in bug report:**
   - AI-Shell version
   - Operating system
   - Database type and version
   - Error message
   - Steps to reproduce
   - Diagnostic report

3. **Submit to:**
   - GitHub: https://github.com/your-org/aishell/issues
   - Email: support@aishell.dev

---

### Q: How do I get help?

**A:**

```bash
# General help
aishell --help

# Command-specific help
aishell backup --help
aishell query run --help

# Interactive help
aishell help

# Documentation
aishell docs

# Online resources
# - Documentation: https://docs.aishell.dev
# - Discord: https://discord.gg/aishell
# - Stack Overflow: Tag `aishell-cli`
```

---

## Diagnostic Commands

### System Diagnostics

```bash
# Run full diagnostic check
aishell doctor

# Check specific component
aishell doctor --check connections
aishell doctor --check vault
aishell doctor --check backups

# Export diagnostic report
aishell doctor --export diagnostic-report.json
```

### Debug Mode

```bash
# Enable debug logging
aishell --debug query run prod-db --sql "SELECT * FROM users"

# Verbose output
aishell --verbose backup create prod-db --name debug-backup

# Trace mode (very detailed)
aishell --trace connection test prod-db
```

### Performance Profiling

```bash
# Profile command execution
aishell --profile query run prod-db --sql "..."

# Output:
# Command execution profile:
# - Parse SQL: 2ms
# - Connect to DB: 45ms
# - Execute query: 123ms
# - Format results: 5ms
# - Total: 175ms
```

---

## Getting Additional Help

### Community Resources

- **Discord**: https://discord.gg/aishell
- **Stack Overflow**: Tag questions with `aishell-cli`
- **GitHub Discussions**: https://github.com/your-org/aishell/discussions

### Professional Support

- **Email**: support@aishell.dev
- **Enterprise Support**: enterprise@aishell.dev
- **Training**: training@aishell.dev

### Documentation

- **User Guide**: [/docs/guides/USER_GUIDE.md](./guides/USER_GUIDE.md)
- **Database Operations**: [/docs/guides/DATABASE_OPERATIONS.md](./guides/DATABASE_OPERATIONS.md)
- **Query Optimization**: [/docs/guides/QUERY_OPTIMIZATION.md](./guides/QUERY_OPTIMIZATION.md)
- **Backup & Recovery**: [/docs/guides/BACKUP_RECOVERY.md](./guides/BACKUP_RECOVERY.md)
- **Monitoring**: [/docs/guides/MONITORING_ANALYTICS.md](./guides/MONITORING_ANALYTICS.md)
- **Security**: [/docs/guides/SECURITY_BEST_PRACTICES.md](./guides/SECURITY_BEST_PRACTICES.md)
- **Integration**: [/docs/guides/INTEGRATION_GUIDE.md](./guides/INTEGRATION_GUIDE.md)

---

*Last Updated: 2024-01-15 | Version: 2.0.0*
