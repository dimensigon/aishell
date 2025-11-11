# AIShell Command Migration Guide

## Overview

This guide helps users transition from deprecated commands to the current AIShell CLI syntax. As AIShell has evolved, some commands have been redesigned for better organization and functionality.

---

## Database Connection Commands

### The `db connect` Command Has Been Deprecated

**Old Syntax (Deprecated)**:
```bash
# ❌ These commands NO LONGER WORK
ai-shell db connect postgres://user:pass@localhost:5432/mydb
ai-shell db connect --interactive
ai-shell db list-connections
ai-shell db switch <name>
```

**New Syntax (Current)**:

#### Option 1: Generic Connection (Auto-detects Database Type)

```bash
# ✅ Generic connection - auto-detects from protocol
ai-shell connect postgres://user:pass@localhost:5432/mydb
ai-shell connect mysql://root:secret@localhost:3306/app
ai-shell connect mongodb://localhost:27017/mydb
ai-shell connect redis://localhost:6379

# With named connection
ai-shell connect postgresql://user:pass@prod.example.com:5432/app_db --name production --ssl
```

#### Option 2: Database-Specific Commands (Recommended)

For database-specific features and better options, use dedicated commands:

**PostgreSQL**:
```bash
ai-shell pg connect postgresql://user:pass@localhost:5432/mydb
ai-shell pg connect --name production --host prod.example.com --port 5432 --database app_db --ssl
```

**MySQL**:
```bash
ai-shell mysql connect mysql://root:secret@localhost:3306/app
ai-shell mysql connect --name local --host localhost --database myapp
```

**MongoDB**:
```bash
ai-shell mongo connect mongodb://localhost:27017/mydb
ai-shell mongo connect --name dev --host localhost --port 27017
```

**Redis**:
```bash
ai-shell redis connect redis://localhost:6379
ai-shell redis connect --name cache --host localhost --port 6379
```

### Connection Management Commands

| Old Command | New Command | Notes |
|-------------|-------------|-------|
| `ai-shell db list-connections` | `ai-shell connections` | Shows all saved connections |
| `ai-shell db switch <name>` | `ai-shell use <name>` | Switch active connection |
| `ai-shell db disconnect` | `ai-shell disconnect [name]` | Disconnect current or specific connection |
| `ai-shell db remove <name>` | `ai-shell disconnect <name>` | Remove saved connection |

---

## Why the Change?

The redesign provides several benefits:

### 1. **Better Organization**
Database-specific commands are grouped under their respective namespaces (`pg`, `mysql`, `mongo`, `redis`), making it easier to find relevant commands.

### 2. **Database-Specific Features**
Each database type has specialized commands that match its unique capabilities:

```bash
# PostgreSQL-specific
ai-shell pg vacuum
ai-shell pg analyze
ai-shell pg reindex
ai-shell pg extensions

# MySQL-specific
ai-shell mysql optimize
ai-shell mysql repair
ai-shell mysql processlist

# MongoDB-specific
ai-shell mongo aggregate
ai-shell mongo createIndex
ai-shell mongo compact

# Redis-specific
ai-shell redis monitor
ai-shell redis flush
ai-shell redis ttl
```

### 3. **Clearer Command Structure**
The new structure follows the pattern: `ai-shell <database> <action> <target>`

```bash
# Old (less clear)
ai-shell db connect postgres://...

# New (clearer intent)
ai-shell pg connect postgresql://...   # PostgreSQL-specific
ai-shell connect postgres://...        # Generic (works for any DB)
```

---

## Quick Migration Checklist

If you have scripts or documentation using the old syntax, update them as follows:

- [ ] Replace `ai-shell db connect` with `ai-shell connect` or `ai-shell <db-type> connect`
- [ ] Replace `ai-shell db list-connections` with `ai-shell connections`
- [ ] Replace `ai-shell db switch` with `ai-shell use`
- [ ] Replace `ai-shell db disconnect` with `ai-shell disconnect`
- [ ] Update any automation/scripts using old commands
- [ ] Update internal documentation and runbooks

---

## Python to Node.js CLI Migration

**If you were using the old Python-based interface**:

### Old Python Commands (Deprecated)
```bash
# ❌ NO LONGER WORKS
python src/main.py connect postgres://localhost:5432/mydb
python src/main.py setup
python src/main.py  # REPL mode
```

### New Node.js CLI Commands (Current)
```bash
# ✅ Current working commands
ai-shell connect postgres://localhost:5432/mydb
ai-shell pg connect postgresql://localhost:5432/mydb --name production

# No REPL mode - use direct commands instead
ai-shell translate "show me all users"
ai-shell optimize "SELECT * FROM users"
ai-shell pg status
```

---

## Connection String Formats

All connection string formats remain the same:

```bash
# PostgreSQL
postgresql://user:password@host:port/database
postgres://user:password@host:port/database

# MySQL
mysql://user:password@host:port/database

# MongoDB
mongodb://host:port/database
mongodb://user:password@host:port/database

# Redis
redis://host:port
redis://user:password@host:port/db

# SQLite
sqlite:///absolute/path/to/database.db
sqlite://./relative/path/to/database.db
```

---

## Examples: Before & After

### Example 1: Connect to Production Database

**Before**:
```bash
ai-shell db connect postgres://admin:secret@prod.db.com:5432/app --name production --ssl
ai-shell db list-connections
ai-shell db switch production
```

**After**:
```bash
ai-shell pg connect postgresql://admin:secret@prod.db.com:5432/app --name production --ssl
ai-shell connections
ai-shell use production
```

### Example 2: Connect to Multiple Databases

**Before**:
```bash
ai-shell db connect postgres://localhost:5432/mydb --name pg-local
ai-shell db connect mysql://localhost:3306/app --name mysql-local
ai-shell db list-connections
```

**After**:
```bash
ai-shell pg connect postgresql://localhost:5432/mydb --name pg-local
ai-shell mysql connect mysql://localhost:3306/app --name mysql-local
ai-shell connections
```

### Example 3: Script Automation

**Before**:
```bash
#!/bin/bash
ai-shell db connect $DATABASE_URL --name production
ai-shell db switch production
# ... perform operations ...
ai-shell db disconnect
```

**After**:
```bash
#!/bin/bash
ai-shell connect $DATABASE_URL --name production
ai-shell use production
# ... perform operations ...
ai-shell disconnect production
```

---

## Need Help?

- **CLI Reference**: See [CLI_REFERENCE.md](./CLI_REFERENCE.md) for complete command documentation
- **Architecture**: See [docs/architecture/](./architecture/) for system design
- **Issues**: Report problems at https://github.com/dimensigon/aishell/issues

---

## Timeline

- **v0.x**: Original `db connect` implementation
- **v1.0.0**: `db connect` deprecated, new connection commands introduced
- **Current**: Use `connect`, `pg connect`, `mysql connect`, etc.

The old `db connect` syntax is no longer supported. Please migrate to the new commands for continued functionality.
