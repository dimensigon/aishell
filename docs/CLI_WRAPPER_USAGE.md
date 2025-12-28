# CLI Wrapper Framework Usage Guide

## Overview

The CLI Wrapper Framework bridges the gap between REPL-only commands and standalone CLI commands in AI-Shell. It provides a unified interface for executing commands with flexible formatting, comprehensive error handling, and advanced features like dry-run mode and AI explanations.

## Features

- **Command Routing**: Automatic routing to appropriate handlers
- **Multiple Output Formats**: JSON, table, CSV, and raw text
- **Global Flags**: Apply common flags to any command
- **Environment Variables**: Automatic integration with DATABASE_URL, ANTHROPIC_API_KEY, etc.
- **Dry-Run Mode**: Preview changes without executing
- **AI Explanations**: Get AI-powered explanations of commands
- **Timeout Handling**: Configurable timeouts for long-running operations
- **File Output**: Save results to files
- **Command Aliases**: Shorter alternatives for frequently-used commands

## Basic Usage

### Simple Command Execution

```bash
# Execute a command
ai-shell health-check

# Use command alias
ai-shell health  # Same as health-check
```

### Output Formatting

```bash
# JSON format
ai-shell backup-list --format json

# Table format (default)
ai-shell backup-list --format table

# CSV format
ai-shell backup-list --format csv

# Raw format (no formatting)
ai-shell health-check --raw
```

### Saving Output to File

```bash
# Save as JSON
ai-shell backup-list --format json --output backups.json

# Save as CSV
ai-shell health-check --format csv --output health-report.csv
```

## Global Flags

These flags work with any command:

### --format <type>

Specify output format: json, table, csv

```bash
ai-shell optimize "SELECT * FROM users" --format json
```

### --verbose

Enable verbose logging and detailed output

```bash
ai-shell health-check --verbose
```

### --explain

Show AI explanation of what the command will do

```bash
ai-shell backup --explain
```

### --dry-run

Simulate command execution without making changes (for mutating commands)

```bash
ai-shell backup --dry-run
ai-shell restore backup-123 --dry-run
```

### --output <file>

Write output to a file instead of stdout

```bash
ai-shell backup-list --output backups.json
```

### --limit <count>

Limit the number of results

```bash
ai-shell backup-list --limit 10
```

### --timeout <ms>

Set command timeout in milliseconds

```bash
ai-shell monitor --timeout 30000
```

### --timestamps

Show timestamps in output

```bash
ai-shell health-check --timestamps
```

## Environment Variables

The CLI Wrapper automatically uses these environment variables:

- **DATABASE_URL**: Default database connection
- **ANTHROPIC_API_KEY**: Required for AI features
- **REDIS_URL**: For query caching features

```bash
# Set environment variables
export DATABASE_URL="postgresql://localhost:5432/mydb"
export ANTHROPIC_API_KEY="sk-ant-..."
export REDIS_URL="redis://localhost:6379"

# Use in commands
ai-shell health-check  # Uses DATABASE_URL
ai-shell cache-enable  # Uses REDIS_URL
```

## Command Examples

### Query Optimization

```bash
# Optimize a query
ai-shell optimize "SELECT * FROM users WHERE active = true"

# With JSON output
ai-shell optimize "SELECT * FROM users" --format json --output query-analysis.json

# Using alias
ai-shell opt "SELECT * FROM users"
```

### Health Monitoring

```bash
# Quick health check
ai-shell health-check

# Detailed health check with CSV export
ai-shell health-check --format csv --output health-report.csv --verbose

# Start monitoring
ai-shell monitor --interval 5000
```

### Backup Management

```bash
# Create backup (dry-run first)
ai-shell backup --explain --dry-run
ai-shell backup --connection production

# List backups with limit
ai-shell backup-list --limit 5 --timestamps

# Restore from backup
ai-shell restore backup-1234567890 --dry-run
ai-shell restore backup-1234567890
```

### Query Federation

```bash
# Federate query across databases
ai-shell federate "SELECT * FROM users" db1 db2 db3

# Using alias
ai-shell fed "SELECT * FROM orders" production analytics
```

### Schema Management

```bash
# Design schema interactively
ai-shell design-schema

# Validate schema file
ai-shell validate-schema schema.json

# Compare schemas
ai-shell diff production staging --format json --output schema-diff.json
```

### Query Caching

```bash
# Enable cache
ai-shell cache-enable --redis redis://localhost:6379

# Check cache stats
ai-shell cache-stats --format table

# Clear cache (with dry-run)
ai-shell cache-clear --dry-run
ai-shell cache-clear
```

### SQL Explainer

```bash
# Explain SQL query
ai-shell explain "SELECT u.*, COUNT(o.id) FROM users u LEFT JOIN orders o GROUP BY u.id"

# Translate natural language to SQL
ai-shell translate "Show me all users created in the last week"

# Using alias
ai-shell nl2sql "Count orders by user for active users"
```

### Migration Testing

```bash
# Test migration file
ai-shell test-migration migrations/001_add_users.sql --verbose

# Using alias
ai-shell test-mig ./migrations/002_alter_orders.sql
```

### Cost Optimization

```bash
# Analyze costs
ai-shell analyze-costs aws us-east-1 --format json

# Using alias
ai-shell costs gcp us-central1 --verbose
```

## Advanced Usage

### Combining Multiple Flags

```bash
# Complex query optimization with full options
ai-shell optimize "SELECT * FROM users WHERE id > 100" \
  --format json \
  --output optimization-report.json \
  --verbose \
  --explain \
  --timestamps
```

### Dry-Run with Explanation

```bash
# Understand and preview changes before executing
ai-shell backup --explain --dry-run --verbose
```

### Batch Operations with File Output

```bash
# Generate multiple reports
ai-shell health-check --format csv --output health-$(date +%Y%m%d).csv
ai-shell backup-list --format json --output backups-$(date +%Y%m%d).json
ai-shell cache-stats --format table --output cache-stats-$(date +%Y%m%d).txt
```

### Piping and Command Chaining

```bash
# Use output in scripts
ai-shell backup-list --format json | jq '.[] | select(.status == "completed")'

# Chain commands
ai-shell backup && ai-shell backup-list --limit 1
```

## Command Aliases

Shorter alternatives for commonly-used commands:

| Command | Alias |
|---------|-------|
| optimize | opt |
| analyze-slow-queries | slow |
| health-check | health |
| monitor | mon |
| backup | bak |
| restore | res |
| backup-list | backups |
| federate | fed |
| design-schema | design |
| validate-schema | validate |
| diff | schema-diff |
| cache-enable | cache-on |
| cache-stats | cache-info |
| cache-clear | cache-flush |
| test-migration | test-mig |
| explain | exp |
| translate | nl2sql |
| analyze-costs | costs |

## Error Handling

The CLI Wrapper provides comprehensive error handling:

```bash
# Unknown command
ai-shell unknown-command
# Error: Unknown command: unknown-command

# Missing required arguments
ai-shell optimize
# Error: Command 'optimize' requires 1 argument(s), got 0

# Invalid file
ai-shell validate-schema nonexistent.json
# Error: File not found: nonexistent.json

# Timeout
ai-shell monitor --timeout 1000
# Error: Command timeout after 1000ms
```

## Programmatic Usage

You can also use the CLI Wrapper programmatically in TypeScript:

```typescript
import { CLIWrapper, CLIOptions } from './src/cli/cli-wrapper';

const wrapper = new CLIWrapper();

// Execute a command
const result = await wrapper.executeCommand(
  'optimize',
  ['SELECT * FROM users'],
  {
    format: 'json',
    verbose: true,
    dryRun: false
  }
);

if (result.success) {
  console.log('Command succeeded:', result.data);
} else {
  console.error('Command failed:', result.error);
}

// Get registered commands
const commands = wrapper.getRegisteredCommands();
console.log('Available commands:', commands.length);

// Cleanup
await wrapper.cleanup();
```

## Command Registration

To add new commands to the CLI Wrapper:

```typescript
// In CLIWrapper class
this.registerCommand({
  name: 'my-command',
  aliases: ['mc', 'cmd'],
  description: 'My custom command',
  requiredArgs: 1,
  handler: this.handleMyCommand.bind(this),
  mutates: true // If command modifies data
});

// Add handler method
private async handleMyCommand(
  args: string[],
  options: CLIOptions,
  context: CommandContext
): Promise<CommandResult> {
  // Command implementation
  return { success: true, data: { result: 'done' } };
}
```

## Testing

The CLI Wrapper includes comprehensive test coverage:

```bash
# Run tests
npm test tests/cli/cli-wrapper.test.ts

# Run with coverage
npm test -- --coverage tests/cli/cli-wrapper.test.ts
```

## Best Practices

1. **Always use --dry-run first** for mutating commands (backup, restore, cache-clear)
2. **Use --explain** to understand what a command will do
3. **Set appropriate --timeout** for long-running operations
4. **Use --format json --output** for scripting and automation
5. **Enable --verbose** when debugging issues
6. **Use command aliases** to save typing
7. **Check --help** for command-specific options

## Troubleshooting

### Command Not Found

```bash
# Check available commands
ai-shell wrapper-demo

# List all commands
ai-shell --help
```

### API Key Missing

```bash
# Set API key
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Verify
echo $ANTHROPIC_API_KEY
```

### Database Connection Issues

```bash
# Set database URL
export DATABASE_URL="postgresql://user:pass@host:5432/database"

# Test connection
ai-shell health-check --verbose
```

### Timeout Errors

```bash
# Increase timeout
ai-shell monitor --timeout 60000  # 60 seconds
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/ai-shell/issues
- Documentation: https://github.com/yourusername/ai-shell/docs

## License

MIT
