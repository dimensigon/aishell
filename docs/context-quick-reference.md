# Context Management Quick Reference

## Context Commands

### Save Context
```bash
ai-shell context save <name> [options]

Options:
  --description <text>      Context description
  --include-history        Include query history
  --include-aliases        Include aliases
  --include-config         Include configuration
  --include-variables      Include variables
  --include-connections    Include connection info

Example:
  ai-shell context save my-project --description "Production" --include-all
```

### Load Context
```bash
ai-shell context load <name> [options]

Options:
  --merge                  Merge with current context
  --overwrite             Overwrite current (default)

Example:
  ai-shell context load dev-env --merge
```

### List Contexts
```bash
ai-shell context list [options]

Options:
  -v, --verbose           Show detailed info
  -f, --format <type>     Output format (table, json)

Example:
  ai-shell context list --verbose
```

### Delete Context
```bash
ai-shell context delete <name> [--force]

Example:
  ai-shell context delete old-project --force
```

### Export Context
```bash
ai-shell context export <name> <file> [options]

Options:
  -f, --format <type>     Export format (json, yaml)

Example:
  ai-shell context export prod backup.yaml --format yaml
```

### Import Context
```bash
ai-shell context import <file> [options]

Options:
  -n, --name <name>       Import with new name

Example:
  ai-shell context import backup.json --name restored
```

### Show Context
```bash
ai-shell context show [name]

Example:
  ai-shell context show my-project
  ai-shell context show              # Current context
```

### Diff Contexts
```bash
ai-shell context diff <context1> <context2>

Example:
  ai-shell context diff production staging
```

### Current Context
```bash
ai-shell context current
```

## Session Commands

### Start Session
```bash
ai-shell session start <name>

Example:
  ai-shell session start debug-session
```

### End Session
```bash
ai-shell session end
```

### List Sessions
```bash
ai-shell session list [options]

Options:
  -f, --format <type>     Output format (table, json)

Example:
  ai-shell session list --format json
```

### Restore Session
```bash
ai-shell session restore <name>

Example:
  ai-shell session restore debug-session
```

### Export Session
```bash
ai-shell session export <name> <file>

Example:
  ai-shell session export my-session data.json
```

## Common Workflows

### Daily Development
```bash
# Morning
ai-shell session start dev-2024-01-15
ai-shell context load dev-environment

# Work...

# End of day
ai-shell context save dev-checkpoint --include-all
ai-shell session end
```

### Project Switch
```bash
ai-shell context save current-work --include-all
ai-shell context load other-project
# Work on other project...
ai-shell context load current-work
```

### Environment Comparison
```bash
ai-shell context diff production staging
```

### Backup and Share
```bash
ai-shell context export my-context backup.json
# Share backup.json with team
```

### Import Team Configuration
```bash
ai-shell context import team-config.yaml --name team-setup
ai-shell context load team-setup
```

## Storage Locations

- Contexts: `~/.ai-shell/contexts/`
- Sessions: `~/.ai-shell/sessions/`

## Tips

1. Use descriptive names: `prod-2024-01-15`, `staging-feature-auth`
2. Add descriptions: `--description "Production database context"`
3. Export regularly: `ai-shell context export prod backup.json`
4. Use sessions for tracking: `ai-shell session start feature-development`
5. Compare before migrating: `ai-shell context diff old new`
