# Context Management Guide

Complete guide to managing query contexts, sessions, and configurations in AI Shell.

## Table of Contents

- [Overview](#overview)
- [Core Concepts](#core-concepts)
- [Context Commands](#context-commands)
- [Session Management](#session-management)
- [Use Cases](#use-cases)
- [Best Practices](#best-practices)
- [API Reference](#api-reference)

## Overview

The Context Management system allows you to:

- **Save and restore** database contexts with all settings
- **Manage sessions** for tracking query workflows
- **Export and import** contexts for sharing and backup
- **Compare contexts** to identify differences
- **Track query history** across sessions

### Key Features

- ✅ Save/load contexts with configurations, aliases, and history
- ✅ Session tracking with statistics and analytics
- ✅ Export/import in JSON and YAML formats
- ✅ Context comparison and diff utilities
- ✅ Automatic query history tracking
- ✅ Variable and configuration management

## Core Concepts

### Context

A **context** represents a complete snapshot of your AI Shell environment:

```typescript
interface Context {
  name: string;
  description?: string;
  createdAt: Date;
  updatedAt: Date;
  database?: string;
  queryHistory?: QueryHistoryEntry[];
  aliases?: Record<string, string>;
  configuration?: Record<string, any>;
  variables?: Record<string, any>;
  connections?: ConnectionInfo[];
}
```

### Session

A **session** represents a time-bounded work period:

```typescript
interface Session {
  id: string;
  name: string;
  startTime: Date;
  endTime?: Date;
  context: Context;
  commandHistory: string[];
  statistics?: SessionStatistics;
}
```

## Context Commands

### Save Context

Save your current environment state:

```bash
# Basic save
ai-shell context save my-project

# With description
ai-shell context save production --description "Production database context"

# Include specific components
ai-shell context save dev-env --include-history --include-config

# Save everything
ai-shell context save full-backup \
  --include-history \
  --include-aliases \
  --include-config \
  --include-variables \
  --include-connections
```

#### Options

- `--description <text>` - Add a description
- `--include-history` - Include query history
- `--include-aliases` - Include command aliases
- `--include-config` - Include configuration settings
- `--include-variables` - Include user variables
- `--include-connections` - Include database connection info

### Load Context

Restore a saved context:

```bash
# Load and replace current context
ai-shell context load my-project

# Merge with current context
ai-shell context load dev-env --merge
```

**Load modes:**
- `--overwrite` (default) - Replace current context
- `--merge` - Merge with current context (additive)

### List Contexts

View all saved contexts:

```bash
# Simple list
ai-shell context list

# Detailed view
ai-shell context list --verbose

# JSON output
ai-shell context list --format json
```

**Output includes:**
- Context name
- Description
- Created/updated timestamps
- Size (verbose mode)
- Query count (verbose mode)
- Alias count (verbose mode)

### Delete Context

Remove a saved context:

```bash
# Delete context
ai-shell context delete old-project

# Force delete (even if current)
ai-shell context delete test --force
```

### Export Context

Export context to a file:

```bash
# Export as JSON
ai-shell context export my-project backup.json

# Export as YAML
ai-shell context export production prod-context.yaml --format yaml
```

### Import Context

Import context from a file:

```bash
# Import with original name
ai-shell context import backup.json

# Import with new name
ai-shell context import shared-context.yaml --name team-context
```

### Show Context

Display context details:

```bash
# Show current context
ai-shell context show

# Show specific context
ai-shell context show my-project
```

### Diff Contexts

Compare two contexts:

```bash
# Compare contexts
ai-shell context diff production staging

# Compare versions
ai-shell context diff v1.0 v2.0
```

**Comparison includes:**
- Database differences
- Added/removed/modified aliases
- Configuration changes
- Query history count differences
- Variable changes

### Current Context

View the active context:

```bash
ai-shell context current
```

## Session Management

### Start Session

Begin a new work session:

```bash
ai-shell session start debug-session

ai-shell session start production-analysis
```

**Session automatically tracks:**
- Queries executed
- Success/failure rate
- Total execution time
- Command history

### End Session

Conclude the current session:

```bash
ai-shell session end
```

Session data is saved for later analysis.

### List Sessions

View all saved sessions:

```bash
# Table format
ai-shell session list

# JSON format
ai-shell session list --format json
```

### Restore Session

Resume a previous session:

```bash
# Restore by name
ai-shell session restore debug-session

# Restore by ID
ai-shell session restore session_1234567890_abc
```

### Export Session

Export session data:

```bash
ai-shell session export my-session session-data.json
```

## Use Cases

### 1. Multiple Projects

Manage different database projects:

```bash
# Save project contexts
ai-shell context save ecommerce --include-all
ai-shell context save analytics --include-all
ai-shell context save reporting --include-all

# Switch between projects
ai-shell context load ecommerce
# Work on ecommerce...

ai-shell context load analytics
# Work on analytics...
```

### 2. Development Workflows

Track development stages:

```bash
# Development context
ai-shell session start development
ai-shell context save dev-baseline --include-config

# Testing phase
ai-shell session start testing
ai-shell context load dev-baseline --merge

# Production deployment
ai-shell session start deployment
ai-shell context save production-ready --include-all
```

### 3. Team Collaboration

Share contexts with team members:

```bash
# Save team configuration
ai-shell context save team-setup \
  --description "Standard team configuration" \
  --include-aliases \
  --include-config

# Export for sharing
ai-shell context export team-setup team-context.yaml

# Team member imports
ai-shell context import team-context.yaml
```

### 4. Debugging Sessions

Track debugging workflows:

```bash
# Start debug session
ai-shell session start bug-investigation

# Save state at different stages
ai-shell context save before-fix
# Make changes...
ai-shell context save after-fix

# Compare changes
ai-shell context diff before-fix after-fix

# End session
ai-shell session end
```

### 5. Environment Migration

Move between environments:

```bash
# Export production context
ai-shell context export production prod-backup.json

# Import to staging
ai-shell context import prod-backup.json --name staging-from-prod

# Verify differences
ai-shell context diff production staging-from-prod
```

### 6. Query History Analysis

Track and analyze queries:

```bash
# Start session with history tracking
ai-shell session start analysis
ai-shell context save session-start --include-history

# Run queries...
# SELECT * FROM users WHERE active = true
# SELECT COUNT(*) FROM orders

# Save final state
ai-shell context save session-end --include-history

# Export for analysis
ai-shell session export analysis query-analysis.json
```

## Best Practices

### 1. Naming Conventions

Use descriptive, consistent names:

```bash
# Good names
ai-shell context save prod-2024-01-15
ai-shell context save staging-feature-auth
ai-shell context save dev-john-optimization

# Avoid
ai-shell context save temp
ai-shell context save test123
```

### 2. Regular Backups

Export important contexts:

```bash
# Daily backup
ai-shell context export production prod-$(date +%Y%m%d).json

# Version control
ai-shell context export main-config config-v1.0.json
```

### 3. Session Organization

Structure sessions logically:

```bash
# Feature development
ai-shell session start feature-user-auth
# Work...
ai-shell session end

# Bug fixing
ai-shell session start bugfix-issue-123
# Work...
ai-shell session end
```

### 4. Context Hygiene

Regularly clean up old contexts:

```bash
# Review contexts
ai-shell context list --verbose

# Delete obsolete ones
ai-shell context delete old-test-context
ai-shell context delete temp-debug
```

### 5. Description Usage

Always add descriptions:

```bash
ai-shell context save quarterly-report \
  --description "Q4 2024 analytics queries and configuration" \
  --include-all
```

### 6. Selective Inclusion

Only save what you need:

```bash
# Configuration only
ai-shell context save config-only --include-config

# Queries only
ai-shell context save query-templates --include-history

# Aliases only
ai-shell context save shortcuts --include-aliases
```

## API Reference

### ContextManager Class

```typescript
class ContextManager {
  // Initialization
  async initialize(): Promise<void>;

  // Context operations
  async saveContext(name: string, options?: SaveContextOptions): Promise<void>;
  async loadContext(name: string, merge?: boolean): Promise<Context>;
  async listContexts(verbose?: boolean): Promise<ContextListEntry[]>;
  async deleteContext(name: string, force?: boolean): Promise<void>;

  // Export/Import
  async exportContext(name: string, file: string, format?: 'json' | 'yaml'): Promise<void>;
  async importContext(file: string, name?: string): Promise<void>;

  // Context info
  async showContext(name?: string): Promise<Context>;
  async diffContexts(context1: string, context2: string): Promise<ContextDiff>;
  async getCurrentContext(): Promise<Context | null>;

  // Session management
  async startSession(name: string): Promise<string>;
  async endSession(): Promise<void>;
  async listSessions(): Promise<Session[]>;
  async restoreSession(name: string): Promise<void>;
  async exportSession(name: string, file: string): Promise<void>;

  // Context updates
  updateCurrentContext(updates: Partial<Context>): void;
  addQueryToHistory(entry: QueryHistoryEntry): void;
  setAlias(name: string, value: string): void;
  setConfig(key: string, value: any): void;
  setVariable(key: string, value: any): void;
}
```

### SaveContextOptions

```typescript
interface SaveContextOptions {
  description?: string;
  includeHistory?: boolean;
  includeAliases?: boolean;
  includeConfig?: boolean;
  includeVariables?: boolean;
  includeConnections?: boolean;
}
```

### QueryHistoryEntry

```typescript
interface QueryHistoryEntry {
  query: string;
  timestamp: number;
  duration?: number;
  success: boolean;
  error?: string;
}
```

### SessionStatistics

```typescript
interface SessionStatistics {
  queriesExecuted: number;
  totalDuration: number;
  errorsCount: number;
  successRate: number;
}
```

## Workflows

### Daily Development Workflow

```bash
# Morning: Start fresh session
ai-shell session start dev-2024-01-15
ai-shell context load dev-environment

# During work: Track progress
# Run queries, make changes...

# End of day: Save state
ai-shell context save dev-checkpoint-eod --include-all
ai-shell session end
```

### Code Review Workflow

```bash
# Save baseline
ai-shell context save pre-review --include-all

# Review and make changes
# ...

# Save review state
ai-shell context save post-review --include-all

# Generate diff for review
ai-shell context diff pre-review post-review
```

### Migration Workflow

```bash
# Export current state
ai-shell context export production prod-backup.json

# Create migration context
ai-shell context save pre-migration --include-all

# Perform migration
# ...

# Save post-migration
ai-shell context save post-migration --include-all

# Verify migration
ai-shell context diff pre-migration post-migration
```

## Storage Locations

Contexts and sessions are stored in:

```
~/.ai-shell/
├── contexts/
│   ├── context1.json
│   ├── context2.json
│   └── ...
└── sessions/
    ├── session_123.json
    ├── session_456.json
    └── ...
```

## Troubleshooting

### Context Not Found

```bash
# List available contexts
ai-shell context list

# Check exact name
ai-shell context list --verbose
```

### Cannot Delete Current Context

```bash
# Use force flag
ai-shell context delete context-name --force
```

### Import Fails

```bash
# Verify file format
cat context.json | jq .

# Import with new name
ai-shell context import context.json --name new-name
```

### Session Already Active

```bash
# End current session first
ai-shell session end

# Then start new session
ai-shell session start new-session
```

## Advanced Examples

### Automated Context Backup

Create a shell script for automated backups:

```bash
#!/bin/bash
# backup-contexts.sh

DATE=$(date +%Y%m%d)
BACKUP_DIR="./context-backups/$DATE"

mkdir -p "$BACKUP_DIR"

# Export all contexts
for context in $(ai-shell context list --format json | jq -r '.[].name'); do
  ai-shell context export "$context" "$BACKUP_DIR/${context}.json"
done

echo "Backed up contexts to $BACKUP_DIR"
```

### Context Comparison Report

```bash
#!/bin/bash
# compare-environments.sh

ENVIRONMENTS=("development" "staging" "production")

for i in "${!ENVIRONMENTS[@]}"; do
  for j in "${!ENVIRONMENTS[@]}"; do
    if [ $i -lt $j ]; then
      env1="${ENVIRONMENTS[$i]}"
      env2="${ENVIRONMENTS[$j]}"
      echo "=== Comparing $env1 vs $env2 ==="
      ai-shell context diff "$env1" "$env2"
      echo ""
    fi
  done
done
```

### Session Analytics

```bash
#!/bin/bash
# session-stats.sh

ai-shell session list --format json | jq '{
  total_sessions: length,
  total_queries: map(.statistics.queriesExecuted) | add,
  average_success_rate: (map(.statistics.successRate) | add) / length,
  total_duration: (map(.statistics.totalDuration) | add)
}'
```

## Integration with Other Features

### With Query Optimizer

```bash
ai-shell context save before-optimization --include-history
ai-shell optimize "SELECT * FROM users"
ai-shell context save after-optimization --include-history
ai-shell context diff before-optimization after-optimization
```

### With Health Monitor

```bash
ai-shell session start health-monitoring
ai-shell monitor --interval 5000
ai-shell context save health-baseline --include-config
```

### With Backup System

```bash
ai-shell context save pre-backup --include-all
ai-shell backup --connection production
ai-shell context save post-backup --include-all
```

## Tips and Tricks

1. **Quick context switching**: Create aliases for frequently used contexts
2. **Session templates**: Export session configurations as templates
3. **Version control**: Store exported contexts in git repositories
4. **Automated workflows**: Combine context commands with shell scripts
5. **Team standards**: Establish naming conventions for shared contexts

## Support

For issues or questions:

- GitHub: https://github.com/yourusername/ai-shell/issues
- Documentation: https://github.com/yourusername/ai-shell/docs
- Examples: https://github.com/yourusername/ai-shell/examples

---

**Last Updated**: 2024-01-15
**Version**: 1.0.0
