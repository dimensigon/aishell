# P3 Quick Reference - AI-Shell

**Version**: 2.0.0
**Last Updated**: 2025-10-28

---

## Quick Command Reference

### Query Builder

```bash
# Start interactive builder
aishell qb

# Build specific query type
aishell qb select <table> -c "col1,col2" -w "condition"
aishell qb insert <table> --values '{"key":"value"}'
aishell qb update <table> --set "col=value" --where "id=1"
aishell qb delete <table> --where "id=1"

# Template management
aishell qb save <name> --description "desc"
aishell qb load <name> --param key=value
aishell qb templates list
aishell qb templates show <name>

# Query operations
aishell qb execute --query "SQL"
aishell qb validate --query "SQL"
aishell qb optimize --query "SQL"
```

---

### Template System

```bash
# Create template
aishell templates create <name> --file template.yaml
aishell templates create --from-query "SQL"

# List and show
aishell templates list --category reports
aishell templates show <name> --example

# Run template
aishell templates run <name> -p key=value
aishell templates run <name> --dry-run

# Manage templates
aishell templates edit <name>
aishell templates delete <name>
aishell templates export <name> output.yaml
aishell templates import --file template.yaml

# Testing
aishell templates validate <name>
aishell templates test <name> --all-combinations

# Versioning
aishell templates versions <name> list
aishell templates versions <name> diff v1 v2
aishell templates versions <name> rollback v1
```

---

### Enhanced Dashboard

```bash
# Launch dashboard
aishell dashboard
aishell dashboard --layout performance
aishell dashboard --layout dba
aishell dashboard --layout debug

# Configuration
aishell dashboard config metrics --position top-left
aishell dashboard add-widget line-chart --metric qps
aishell dashboard remove-widget <id>

# Layouts
aishell dashboard layouts list
aishell dashboard layouts show <name>
aishell dashboard layouts create <name>

# Export
aishell dashboard export --format png -o dashboard.png
aishell dashboard export --format html -o dashboard.html
```

---

### Pattern Detection

```bash
# Detect patterns
aishell patterns detect --hours 24
aishell patterns detect --types "performance,security"
aishell patterns detect --realtime

# List and show
aishell patterns list --type performance
aishell patterns list --severity critical
aishell patterns show <pattern-id> --recommendations

# Fix patterns
aishell patterns fix <pattern-id> --dry-run
aishell patterns fix all --type missing-index

# Monitoring
aishell patterns monitor --realtime --alert
aishell patterns alert add --pattern "n-plus-one"

# Reporting
aishell patterns report --period 7d --output report.html
```

---

### Prometheus Integration

```bash
# Start exporter
aishell prometheus start --port 9090

# Status and testing
aishell prometheus status
aishell prometheus test

# Export dashboard
aishell prometheus export-dashboard -o dashboard.json

# Query metrics
curl http://localhost:9090/metrics
curl 'http://localhost:9091/api/v1/query?query=aishell_query_total'
```

---

### Grafana Integration

```bash
# Export dashboard
aishell grafana export --dashboard performance -o perf.json

# Import dashboard
aishell grafana import --dashboard dba

# Create custom dashboard
aishell grafana create-dashboard --name "My Dashboard"
```

---

### Slack Integration

```bash
# Initialize
aishell slack init

# Configuration
aishell slack config --channel "#database-alerts"

# Send messages
aishell slack send "Test message"

# Alerts
aishell slack alert add --name "High QPS" --condition "qps > 1000"

# Status
aishell slack status
aishell slack test
```

---

## Common Workflows

### Workflow 1: Build and Save Query

```bash
# 1. Start query builder
aishell qb

# 2. Build query interactively
# Select table: users
# Select columns: id, name, email
# Add filter: status = 'active'
# Order by: name ASC

# 3. Save as template
aishell qb save active-users --parameters "status"

# 4. Use template later
aishell qb load active-users --param status=premium
```

---

### Workflow 2: Monitor Performance

```bash
# 1. Start dashboard
aishell dashboard --layout performance

# 2. Start Prometheus exporter
aishell prometheus start

# 3. Configure Grafana dashboards
aishell grafana import --dashboard performance

# 4. Set up Slack alerts
aishell slack alert add --name "Slow Queries" \
  --condition "slow_query_count > 10"
```

---

### Workflow 3: Detect and Fix Issues

```bash
# 1. Detect patterns
aishell patterns detect --hours 24

# 2. Review findings
aishell patterns list --severity critical

# 3. View recommendations
aishell patterns show <pattern-id> --recommendations

# 4. Apply fixes
aishell patterns fix <pattern-id> --backup

# 5. Generate report
aishell patterns report --period 7d --output report.pdf
```

---

## Configuration Files

### Query Builder
`~/.aishell/config/query-builder.json`

```json
{
  "enabled": true,
  "defaultDatabase": "postgres",
  "autoSave": true,
  "ui": { "theme": "dark", "showHints": true }
}
```

---

### Templates
`~/.aishell/config/templates.yaml`

```yaml
templates:
  directory: ~/.aishell/templates
  autoBackup: true
  shareEnabled: false
```

---

### Dashboard
`~/.aishell/dashboard.yaml`

```yaml
dashboard:
  refreshInterval: 2
  theme: dark
  mouse: true
```

---

### Pattern Detection
`~/.aishell/pattern-detection.yaml`

```yaml
patternDetection:
  sensitivity: medium
  autoLearn: true
  analysisWindow: 24
```

---

### Prometheus
`~/.aishell/prometheus.yaml`

```yaml
prometheus:
  enabled: true
  port: 9090
  path: /metrics
```

---

### Slack
`~/.aishell/slack.yaml`

```yaml
slack:
  enabled: true
  botToken: xoxb-...
  channel: "#database-alerts"
```

---

## Environment Variables

```bash
# Database connection
export AISHELL_DB_URL="postgresql://user:pass@localhost:5432/db"

# Slack token
export SLACK_BOT_TOKEN="xoxb-..."
export SLACK_APP_TOKEN="xapp-..."

# Prometheus
export PROMETHEUS_PORT=9090

# Grafana
export GRAFANA_URL="http://localhost:3000"
export GRAFANA_API_KEY="..."

# Logging
export AISHELL_LOG_LEVEL="info"
export AISHELL_LOG_FILE="~/.aishell/logs/aishell.log"

# Features
export AISHELL_QUERY_BUILDER_ENABLED=true
export AISHELL_TEMPLATES_ENABLED=true
export AISHELL_DASHBOARD_ENABLED=true
export AISHELL_PATTERNS_ENABLED=true
```

---

## Troubleshooting Flowchart

```
Issue?
│
├─ Command not found
│  └─> Check installation: npm list -g aishell
│
├─ Feature not enabled
│  └─> Enable: aishell config set features.<feature> true
│
├─ Connection error
│  └─> Test connection: aishell connect test --database <db>
│
├─ Permission denied
│  └─> Check permissions: aishell config get auth
│
├─ Template not found
│  └─> List templates: aishell templates list
│
├─ Dashboard not rendering
│  └─> Check terminal: echo $TERM (should be xterm-256color)
│
├─ Pattern detection slow
│  └─> Reduce window: aishell config set patternDetection.analysisWindow 12
│
├─ Prometheus no data
│  └─> Check endpoint: curl http://localhost:9090/metrics
│
├─ Grafana no dashboard
│  └─> Import: aishell grafana import --dashboard performance
│
└─ Slack bot not responding
   └─> Check status: aishell slack status
```

---

## Status Codes

```
Exit Codes:
  0  - Success
  1  - General error
  2  - Command parse error
  3  - Database connection error
  4  - Permission denied
  5  - Feature not enabled
  6  - Configuration error
  7  - Template not found
  8  - Pattern detection error
  9  - Integration error (Prometheus, Grafana, Slack)
  10 - Unknown error
```

---

## Keyboard Shortcuts

### Query Builder
```
Tab       - Autocomplete
Ctrl+E    - Execute query
Ctrl+S    - Save template
Ctrl+O    - Optimize query
Esc       - Cancel
```

### Dashboard
```
Q         - Quit
R         - Refresh
L         - Change layout
F         - Filter
E         - Export
H         - Help
Arrow keys - Navigate widgets
```

---

## Useful Queries

### Check AI-Shell Status
```bash
aishell status --verbose
```

### List All Features
```bash
aishell features list
```

### View Configuration
```bash
aishell config get
```

### Check Logs
```bash
tail -f ~/.aishell/logs/aishell.log
```

---

## Quick Tips

1. **Tab Completion**: Press Tab for autocomplete in most commands
2. **Dry Run**: Use `--dry-run` to preview changes
3. **Verbose Mode**: Add `-v` or `--verbose` for detailed output
4. **Help**: Add `--help` to any command for usage info
5. **Config**: Use `aishell config set <key> <value>` to change settings

---

## Getting Help

```bash
# Command help
aishell <command> --help

# Feature guide
aishell docs <feature>

# All documentation
aishell docs

# Version info
aishell --version

# Status check
aishell status
```

---

**For full documentation, see:**
- Query Builder: `docs/features/query-builder.md`
- Templates: `docs/features/template-system.md`
- Dashboard: `docs/features/enhanced-dashboard.md`
- Patterns: `docs/features/pattern-detection.md`
- Prometheus: `docs/integrations/prometheus.md`
- Grafana: `docs/integrations/grafana.md`
- Slack: `docs/integrations/slack.md`

---

**Quick Reference Version**: 1.0.0
**Last Updated**: 2025-10-28
