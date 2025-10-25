# AI-Shell Database Setup - Video Tutorial Script (10 minutes)

**Target Duration**: 10:00
**Audience**: Database administrators, developers
**Prerequisites**: AI-Shell installed, basic SQL knowledge

---

## Scene 1: Introduction (0:00 - 0:45)

### Screen: Title Card
**Voice Over**:
> "Welcome to AI-Shell Database Setup. In this 10-minute tutorial, you'll learn how to connect to multiple database types, configure connections, and leverage AI for database operations."

### Screen Capture Notes:
- Show supported databases: PostgreSQL, MySQL, SQLite, MongoDB, Redis
- Display connection icons animating

**Timestamp**: 0:00 - 0:45

---

## Scene 2: Connection Methods (0:45 - 2:30)

### Screen: Terminal Window
**Voice Over**:
> "AI-Shell supports three connection methods: connection strings, configuration files, and environment variables."

### Demo Code - Method 1: Connection String:
```bash
# PostgreSQL
ai> connect postgres://user:password@localhost:5432/mydb

[AI] Connecting to PostgreSQL database...
✓ Connected to mydb@localhost:5432
Database: PostgreSQL 14.5, 42 tables, 15.2 MB

# MySQL
ai> connect mysql://root:password@localhost:3306/production

[AI] Connecting to MySQL database...
✓ Connected to production@localhost:3306
Database: MySQL 8.0.28, 28 tables, 230 MB

# MongoDB
ai> connect mongodb://localhost:27017/analytics

[AI] Connecting to MongoDB database...
✓ Connected to analytics@localhost:27017
Database: MongoDB 5.0.8, 12 collections, 1.4 GB

# SQLite
ai> connect sqlite:///path/to/database.db

[AI] Connecting to SQLite database...
✓ Connected to database.db
Database: SQLite 3.37.0, 8 tables
```

**Voice Over**:
> "Simply use the standard connection URI format for your database type."

### Demo Code - Method 2: Configuration File:
```bash
# Create config file
ai> config database add production

? Database type: PostgreSQL
? Host: db.production.com
? Port: 5432
? Database name: production_db
? Username: admin
? Password: ********
? Save password? Yes (encrypted)
? SSL Mode: require

✓ Configuration saved to ~/.agentic-aishell/databases.yaml

# Connect using saved config
ai> connect production

[AI] Loading connection from configuration...
✓ Connected to production_db@db.production.com:5432
```

**Voice Over**:
> "Configuration files keep your credentials secure and connections organized."

### Demo Code - Method 3: Environment Variables:
```bash
# Set environment variables
export DB_TYPE=postgresql
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=mydb
export DB_USER=admin
export DB_PASSWORD=secret

# Connect using environment
ai> connect --from-env

[AI] Reading connection details from environment...
✓ Connected to mydb@localhost:5432
```

**Voice Over**:
> "Environment variables work great for CI/CD pipelines and containerized deployments."

### Screen Capture Notes:
- Show each method clearly
- Highlight password masking
- Show successful connection indicators
- Display database metadata

**Timestamp**: 0:45 - 2:30

---

## Scene 3: Multi-Database Management (2:30 - 4:15)

### Screen: Split Terminal View
**Voice Over**:
> "AI-Shell can manage multiple database connections simultaneously."

### Demo Code:
```bash
# Connect to multiple databases
ai> connect production postgres://...
✓ Connected as 'production'

ai> connect analytics mongodb://...
✓ Connected as 'analytics'

ai> connect cache redis://localhost:6379
✓ Connected as 'cache'

# List active connections
ai> connections list

Active Connections:
┌────────────┬────────────┬───────────────────────┬──────────┬──────────┐
│ Alias      │ Type       │ Host                  │ Database │ Status   │
├────────────┼────────────┼───────────────────────┼──────────┼──────────┤
│ production │ PostgreSQL │ db.production.com     │ prod_db  │ Active   │
│ analytics  │ MongoDB    │ localhost             │ analytics│ Active   │
│ cache      │ Redis      │ localhost             │ 0        │ Active   │
└────────────┴────────────┴───────────────────────┴──────────┴──────────┘

# Switch between connections
ai> use production
[AI] Switched to production connection

ai> show tables
Tables in production:
  users, orders, products, inventory, logs...

ai> use analytics
[AI] Switched to analytics connection

ai> show collections
Collections in analytics:
  events, sessions, page_views, user_behavior...
```

**Voice Over**:
> "Switch between databases instantly and run queries across multiple sources."

### Demo Code - Cross-Database Queries:
```bash
# AI-assisted cross-database query
ai> compare user count between production and analytics databases

[AI] I'll query both databases and compare:

Production (PostgreSQL):
SELECT COUNT(*) FROM users;
Result: 45,823 users

Analytics (MongoDB):
db.users.count()
Result: 45,820 users

Analysis:
✓ Discrepancy: 3 users
⚠ Recommendation: Check recent user registrations
  Production may have 3 users not yet synced to analytics.
```

**Voice Over**:
> "AI-Shell can even help you spot inconsistencies across databases."

### Screen Capture Notes:
- Show multiple terminal tabs/windows
- Highlight connection switching
- Visualize cross-database comparison
- Display AI analysis with icons

**Timestamp**: 2:30 - 4:15

---

## Scene 4: Advanced Connection Features (4:15 - 6:30)

### Screen: Terminal with Configuration Panel
**Voice Over**:
> "Let's explore advanced connection features like SSH tunneling, read replicas, and connection pooling."

### Demo Code - SSH Tunneling:
```bash
# Connect through SSH tunnel
ai> connect production --ssh-tunnel

? SSH Host: bastion.example.com
? SSH User: admin
? SSH Key: ~/.ssh/id_rsa
? Database Host: internal-db.local
? Database Port: 5432

[AI] Creating SSH tunnel...
✓ SSH tunnel established: localhost:15432 -> internal-db.local:5432
✓ Connected to production via SSH tunnel

# Verify connection
ai> query "SELECT current_database(), inet_server_addr()"

┌──────────────────┬──────────────────┐
│ current_database │ inet_server_addr │
├──────────────────┼──────────────────┤
│ production_db    │ 10.0.1.42        │
└──────────────────┴──────────────────┘
```

### Demo Code - Read Replicas:
```bash
# Configure primary and replica
ai> connect production-primary postgres://primary.db.com/prod --role=primary
ai> connect production-replica postgres://replica.db.com/prod --role=replica

# AI automatically routes queries
ai> query "SELECT * FROM users WHERE id = 123" --optimize

[AI] Routing to read replica (read-only query)...
Using connection: production-replica

ai> query "UPDATE users SET status = 'active' WHERE id = 123"

[AI] Routing to primary (write operation)...
Using connection: production-primary
```

### Demo Code - Connection Pooling:
```bash
# Configure connection pool
ai> config connection-pool set production

? Min connections: 5
? Max connections: 20
? Connection timeout: 30s
? Idle timeout: 10m
? Enable statement timeout: Yes (30s)

✓ Connection pool configured

# Monitor pool status
ai> pool status production

Connection Pool: production
┌─────────────┬───────┐
│ Metric      │ Value │
├─────────────┼───────┤
│ Total       │ 20    │
│ Active      │ 8     │
│ Idle        │ 12    │
│ Waiting     │ 0     │
│ Total Hits  │ 1,234 │
│ Efficiency  │ 94%   │
└─────────────┴───────┘
```

**Voice Over**:
> "Connection pooling optimizes performance for high-traffic applications."

### Screen Capture Notes:
- Show SSH tunnel creation process
- Highlight query routing decisions
- Display pool metrics visualization
- Show performance improvements

**Timestamp**: 4:15 - 6:30

---

## Scene 5: Security Best Practices (6:30 - 8:00)

### Screen: Security Dashboard
**Voice Over**:
> "Security is critical. Let's review best practices for managing database credentials."

### Demo Code - Encrypted Storage:
```bash
# Initialize secure credential storage
ai> security init

? Set master password: ********
? Confirm password: ********
? Enable biometric unlock: Yes

✓ Secure credential storage initialized
Credentials encrypted with AES-256

# Store credentials securely
ai> security add-credential production-db

? Username: admin
? Password: ********
? Save SSH key: Yes
? SSH Key path: ~/.ssh/prod_key

✓ Credentials stored in encrypted vault

# Use stored credentials
ai> connect production --use-stored-credentials

[AI] Loading encrypted credentials...
✓ Authenticated with stored credentials
✓ Connected to production_db
```

### Demo Code - SSL/TLS Configuration:
```bash
# Configure SSL connection
ai> connect production-secure \
    postgres://db.example.com/prod \
    --ssl-mode=require \
    --ssl-cert=client.crt \
    --ssl-key=client.key \
    --ssl-root-cert=ca.crt

[AI] Configuring SSL/TLS connection...
✓ SSL certificate validated
✓ Secure connection established (TLS 1.3)
```

### Demo Code - Audit Logging:
```bash
# Enable audit logging
ai> config audit enable

? Log level: INFO
? Log destination: ~/.agentic-aishell/logs/audit.log
? Rotate logs: Daily
? Retention: 90 days

✓ Audit logging enabled

# View audit log
ai> audit log --tail 5

[2025-10-11 10:30:15] INFO  Connection established: production (admin@10.0.1.42)
[2025-10-11 10:30:42] INFO  Query executed: SELECT * FROM users LIMIT 10
[2025-10-11 10:31:05] WARN  Failed login attempt: staging (user: unknown)
[2025-10-11 10:32:10] INFO  Connection closed: production (duration: 2m 15s)
[2025-10-11 10:33:20] INFO  Backup initiated: production -> s3://backups/prod/
```

**Voice Over**:
> "Audit logs help you track all database operations and maintain compliance."

### Screen Capture Notes:
- Show encrypted credential storage
- Highlight SSL certificate validation
- Display audit log with color coding
- Show security dashboard metrics

**Timestamp**: 6:30 - 8:00

---

## Scene 6: Troubleshooting & Tips (8:00 - 9:15)

### Screen: Troubleshooting Panel
**Voice Over**:
> "Let's cover common connection issues and how to debug them."

### Demo Code - Connection Diagnostics:
```bash
# Test connection
ai> diagnose connection production

Running diagnostics for: production
┌─────────────────────────┬────────┬──────────────────────┐
│ Check                   │ Status │ Details              │
├─────────────────────────┼────────┼──────────────────────┤
│ Network connectivity    │ ✓ PASS │ Host reachable       │
│ Port accessibility      │ ✓ PASS │ Port 5432 open       │
│ DNS resolution          │ ✓ PASS │ Resolved to 10.0.1.5 │
│ Authentication          │ ✗ FAIL │ Invalid password     │
│ Database exists         │ ⏸ SKIP │ Can't verify         │
│ Privileges              │ ⏸ SKIP │ Can't verify         │
└─────────────────────────┴────────┴──────────────────────┘

[AI] Detected issue: Authentication failed
Suggestion: Check password or use stored credentials
```

### Demo Code - Network Testing:
```bash
# Test network path
ai> network test db.example.com:5432

Testing connection to db.example.com:5432...
├─ DNS Lookup: ✓ 45ms (10.0.1.42)
├─ TCP Connect: ✓ 120ms
├─ SSL Handshake: ✓ 89ms (TLS 1.3)
└─ Total: 254ms

Network quality: Excellent

# Check firewall rules
ai> check firewall 5432

Checking port 5432 accessibility...
✓ Port 5432 is open
✓ No firewall blocking detected
✓ SELinux policy allows connection
```

### Demo Code - Common Issues:
```bash
# Ask AI for help
ai> why can't I connect to my database?

[AI] Let me help troubleshoot. Common issues:

1. Wrong credentials - Try: diagnose connection <name>
2. Network/firewall - Try: network test <host>:<port>
3. Database not running - Check service status
4. SSL required - Add --ssl-mode=require
5. Connection limit - Check max_connections

What error message are you seeing?
```

**Voice Over**:
> "AI-Shell's diagnostic tools help you quickly identify and fix connection issues."

### Screen Capture Notes:
- Show diagnostic output with visual status
- Highlight failed checks in red
- Display AI suggestions prominently
- Show resolution process

**Timestamp**: 8:00 - 9:15

---

## Scene 7: Conclusion & Next Steps (9:15 - 10:00)

### Screen: Summary Dashboard
**Voice Over**:
> "You now know how to connect to any database, manage multiple connections, and troubleshoot issues."

### Key Takeaways (Display on screen):
```
✓ Connection Methods:
  - URI strings for quick access
  - Config files for organization
  - Environment variables for automation

✓ Advanced Features:
  - SSH tunneling for secure access
  - Read replicas for performance
  - Connection pooling for scale

✓ Security:
  - Encrypted credential storage
  - SSL/TLS connections
  - Audit logging

✓ Troubleshooting:
  - Built-in diagnostics
  - Network testing
  - AI-assisted debugging
```

**Voice Over**:
> "Next, explore our AI Features tutorial to learn how AI-Shell can write queries, optimize performance, and automate database tasks. See you there!"

### Screen Capture Notes:
- Show key takeaways checklist
- Display next tutorial preview
- Show resource links
- End with call-to-action

**Timestamp**: 9:15 - 10:00

---

## Production Notes

### Visual Style:
- Split-screen for multiple connections
- Color-coded database types (PostgreSQL=blue, MySQL=orange, MongoDB=green)
- Security features highlighted with lock icons
- Diagnostic results with traffic light colors

### Demonstrations:
- Use real databases (Docker containers for consistency)
- Show actual connection times
- Display real error messages
- Demonstrate recovery procedures

### Graphics:
- Network topology diagrams for SSH tunneling
- Connection pool visualization
- Security encryption animation
- Timeline for audit logs

---

## Resources

- **Connection String Reference**: https://docs.ai-shell.io/connections
- **Security Guide**: https://docs.ai-shell.io/security
- **Troubleshooting**: https://docs.ai-shell.io/troubleshooting
- **Next Tutorial**: 03-ai-features-script.md

---

## Video Metadata

**Title**: AI-Shell Database Setup - Complete Connection Guide (10 min)
**Description**: Master database connections in AI-Shell. Learn connection methods, multi-database management, SSH tunneling, security best practices, and troubleshooting.

**Tags**: ai-shell, database, postgresql, mysql, mongodb, redis, sqlite, connection, security, tutorial, ssh-tunnel, ssl, tls
