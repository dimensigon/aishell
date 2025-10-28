# CLI Wrapper Quick Start Guide

## What is the CLI Wrapper?

The CLI Wrapper Framework bridges REPL-only commands and standalone CLI commands, providing a unified interface with powerful features like flexible formatting, dry-run mode, and AI explanations.

## Installation

Already installed in AI-Shell! Just use it.

## Quick Examples

### Basic Commands

```bash
# Health check
ai-shell health-check

# Optimize query
ai-shell optimize "SELECT * FROM users WHERE active = true"

# List backups
ai-shell backup-list
```

### Output Formats

```bash
# JSON format
ai-shell health-check --format json

# CSV format
ai-shell backup-list --format csv

# Table format (default)
ai-shell cache-stats --format table
```

### Global Flags

```bash
# Verbose mode
ai-shell health-check --verbose

# Dry-run (safe preview)
ai-shell backup --dry-run

# AI explanation
ai-shell restore backup-123 --explain

# Save to file
ai-shell backup-list --output backups.json

# Limit results
ai-shell backup-list --limit 5

# Show timestamps
ai-shell health-check --timestamps
```

### Command Aliases (Shortcuts)

```bash
ai-shell opt "SELECT * FROM users"       # optimize
ai-shell health                           # health-check
ai-shell bak                              # backup
ai-shell backups                          # backup-list
ai-shell exp "SELECT * FROM users"        # explain
ai-shell nl2sql "show all active users"   # translate
```

### Combine Multiple Flags

```bash
ai-shell optimize "SELECT * FROM users" \
  --format json \
  --verbose \
  --explain \
  --output result.json \
  --timestamps
```

## All Available Commands

### Query Optimization
- `optimize` (alias: `opt`) - Optimize SQL queries
- `analyze-slow-queries` (alias: `slow`) - Analyze slow queries

### Health & Monitoring
- `health-check` (alias: `health`) - Database health check
- `monitor` (alias: `mon`) - Real-time monitoring

### Backup & Recovery
- `backup` (alias: `bak`) - Create backup
- `restore` (alias: `res`) - Restore from backup
- `backup-list` (alias: `backups`) - List backups

### Query Federation
- `federate` (alias: `fed`) - Execute federated queries

### Schema Management
- `design-schema` (alias: `design`) - Design schema
- `validate-schema` (alias: `validate`) - Validate schema
- `diff` (alias: `schema-diff`) - Compare schemas

### Cache Management
- `cache-enable` (alias: `cache-on`) - Enable caching
- `cache-stats` (alias: `cache-info`) - Cache statistics
- `cache-clear` (alias: `cache-flush`) - Clear cache

### SQL Tools
- `explain` (alias: `exp`) - Explain SQL
- `translate` (alias: `nl2sql`) - Natural language to SQL

### Migration & Testing
- `test-migration` (alias: `test-mig`) - Test migrations

### Cost Optimization
- `analyze-costs` (alias: `costs`) - Analyze costs

## Environment Variables

Set these for automatic integration:

```bash
export DATABASE_URL="postgresql://localhost:5432/mydb"
export ANTHROPIC_API_KEY="sk-ant-your-key"
export REDIS_URL="redis://localhost:6379"
```

## Common Use Cases

### 1. Query Optimization Workflow

```bash
# Step 1: Explain what optimization does
ai-shell optimize "SELECT * FROM users WHERE id > 100" --explain

# Step 2: Optimize and save results
ai-shell optimize "SELECT * FROM users WHERE id > 100" \
  --format json \
  --output optimization-report.json
```

### 2. Backup Workflow

```bash
# Step 1: Preview backup (dry-run)
ai-shell backup --explain --dry-run

# Step 2: Create actual backup
ai-shell backup --connection production

# Step 3: List recent backups
ai-shell backups --limit 5 --timestamps
```

### 3. Health Monitoring Workflow

```bash
# Quick health check
ai-shell health

# Detailed health check with CSV export
ai-shell health-check \
  --format csv \
  --output health-report-$(date +%Y%m%d).csv \
  --verbose
```

### 4. Schema Management Workflow

```bash
# Compare two schemas
ai-shell diff production staging --format json

# Validate schema file
ai-shell validate schema.json --verbose

# Design new schema interactively
ai-shell design-schema
```

### 5. SQL Translation Workflow

```bash
# Translate natural language to SQL
ai-shell translate "Show me all users created in the last week" \
  --format json \
  --output query.json

# Explain existing SQL
ai-shell explain "SELECT u.*, COUNT(o.id) FROM users u LEFT JOIN orders o" \
  --verbose
```

## Pro Tips

1. **Always dry-run first** for destructive operations:
   ```bash
   ai-shell backup --dry-run
   ```

2. **Use aliases** to save typing:
   ```bash
   ai-shell opt "query"  # Instead of optimize
   ```

3. **Save to files** for large outputs:
   ```bash
   ai-shell backups --output backups.json
   ```

4. **Use explain mode** when unsure:
   ```bash
   ai-shell restore backup-123 --explain
   ```

5. **Combine with shell tools**:
   ```bash
   ai-shell backup-list --format json | jq '.[] | select(.status == "completed")'
   ```

## Troubleshooting

### Command not found
```bash
# Check available commands
ai-shell wrapper-demo
```

### Missing API key
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### Database connection error
```bash
export DATABASE_URL="postgresql://user:pass@host:5432/db"
ai-shell health-check --verbose
```

### Timeout error
```bash
# Increase timeout
ai-shell monitor --timeout 60000
```

## Demo Script

Run the comprehensive demo to see all features:

```bash
npx ts-node examples/cli-wrapper-demo.ts
```

## Documentation

- **User Guide**: `/home/claude/AIShell/aishell/docs/CLI_WRAPPER_USAGE.md`
- **Technical Docs**: `/home/claude/AIShell/aishell/src/cli/README.md`
- **Implementation**: `/home/claude/AIShell/aishell/docs/CLI_WRAPPER_IMPLEMENTATION.md`

## Need Help?

```bash
# Show help
ai-shell --help

# Show command-specific help
ai-shell optimize --help

# Show examples
ai-shell examples

# Show all features
ai-shell features
```

## Advanced: Programmatic Usage

```typescript
import { CLIWrapper } from './src/cli/cli-wrapper';

const wrapper = new CLIWrapper();

const result = await wrapper.executeCommand(
  'health-check',
  [],
  { format: 'json', verbose: true }
);

if (result.success) {
  console.log('Success:', result.data);
} else {
  console.error('Failed:', result.error);
}

await wrapper.cleanup();
```

## That's It!

You're ready to use the CLI Wrapper Framework. Start with simple commands and explore the features as you go.

**Happy coding! 🚀**
