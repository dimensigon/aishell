# Slack Integration - AI-Shell P3 Feature

**Status**: Priority 3 (P3) Integration
**Version**: 1.0.0
**Last Updated**: 2025-10-28

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Slash Commands](#slash-commands)
- [Notifications](#notifications)
- [Interactive Components](#interactive-components)
- [Bot Commands](#bot-commands)
- [Workflows](#workflows)
- [Use Cases](#use-cases)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Overview

Slack integration brings AI-Shell capabilities directly into your team's Slack workspace, enabling:

- **Real-Time Alerts**: Instant notifications for database events
- **Slash Commands**: Execute queries from Slack
- **Interactive Bot**: Natural language database queries
- **Team Collaboration**: Share query results and insights
- **Workflow Automation**: Trigger actions from Slack
- **Status Updates**: Regular database health reports

### Key Benefits

✅ **Stay Informed**: Alerts delivered to your team
✅ **Quick Access**: Run queries without leaving Slack
✅ **Collaboration**: Share results in channels
✅ **Automation**: Scheduled reports and updates
✅ **Mobile Ready**: Access from Slack mobile app
✅ **Secure**: OAuth 2.0 authentication

---

## Installation

### Prerequisites

```bash
# Install AI-Shell
npm install -g aishell

# Install Slack integration
npm install -g @aishell/slack-integration
```

### Create Slack App

1. **Go to** https://api.slack.com/apps
2. **Click** "Create New App"
3. **Choose** "From scratch"
4. **Enter** App Name: "AI-Shell"
5. **Select** your workspace
6. **Click** "Create App"

### Configure OAuth & Permissions

Add OAuth scopes:

**Bot Token Scopes**:
- `chat:write` - Send messages
- `chat:write.public` - Send to public channels
- `commands` - Add slash commands
- `files:write` - Upload files
- `im:history` - Read DMs
- `im:write` - Send DMs

**User Token Scopes**:
- `chat:write` - Send as user
- `channels:read` - List channels
- `users:read` - Get user info

### Install AI-Shell Slack Integration

```bash
# Initialize Slack integration
aishell slack init

# Follow prompts:
# Enter Bot Token: xoxb-your-bot-token
# Enter App Token: xapp-your-app-token
# Enter Signing Secret: your-signing-secret

# Verify installation
aishell slack status

# Output:
# ✓ Slack integration enabled
# ✓ Connected to workspace: YourTeam
# ✓ Bot user: @AI-Shell
# ✓ Slash commands registered
# ✓ Ready to receive alerts
```

---

## Quick Start

### Example 1: Send Alert to Slack

```bash
# Configure alert channel
aishell slack config --channel "#database-alerts"

# Send test message
aishell slack send "Test alert from AI-Shell"

# Output in Slack:
# [AI-Shell] Test alert from AI-Shell
```

### Example 2: Execute Query from Slack

In Slack, type:
```
/aishell query SELECT COUNT(*) FROM users
```

AI-Shell responds:
```
Query Results:
┌───────┐
│ count │
├───────┤
│ 1,234 │
└───────┘
Execution time: 23ms
```

### Example 3: Get Database Status

In Slack, type:
```
/aishell status
```

Response:
```
📊 Database Status

🟢 Status: Healthy
⚡ QPS: 45.2
⏱️ Avg Latency: 23ms
🔗 Connections: 12/100
💾 Cache Hit: 94.5%

Last updated: 2025-10-28 10:45:32
```

---

## Slash Commands

### Register Slash Commands

In Slack App settings, add these commands:

#### `/aishell query`
Execute database query.

**Usage**:
```
/aishell query <SQL>
```

**Example**:
```
/aishell query SELECT * FROM users WHERE status='active' LIMIT 10
```

#### `/aishell status`
Get database status.

**Usage**:
```
/aishell status [database]
```

**Example**:
```
/aishell status production
```

#### `/aishell slow`
View slow queries.

**Usage**:
```
/aishell slow [hours] [limit]
```

**Example**:
```
/aishell slow 24 10
```

#### `/aishell report`
Generate report.

**Usage**:
```
/aishell report <type> [period]
```

**Example**:
```
/aishell report performance 7d
```

### Configure Command Handlers

`~/.aishell/slack-commands.yaml`:

```yaml
commands:
  query:
    enabled: true
    permissions: ["admin", "developer"]
    rate_limit: 10  # per minute
    timeout: 30  # seconds
    response_type: "in_channel"  # or "ephemeral"
    
  status:
    enabled: true
    permissions: ["everyone"]
    cache_ttl: 60  # seconds
    response_type: "ephemeral"
    
  slow:
    enabled: true
    permissions: ["admin", "dba"]
    default_hours: 24
    default_limit: 10
    
  report:
    enabled: true
    permissions: ["admin", "manager"]
    allowed_types: ["performance", "security", "usage"]
    max_period: "30d"
```

---

## Notifications

### Alert Configuration

`~/.aishell/slack-alerts.yaml`:

```yaml
alerts:
  channel: "#database-alerts"
  mention_on_critical: "@channel"
  mention_on_warning: "@dba-oncall"
  
  templates:
    critical: |
      🔴 *CRITICAL ALERT*
      {{ alert.title }}
      
      *Details:*
      {{ alert.description }}
      
      *Action Required:*
      {{ alert.action }}
      
      <{{ alert.link }}|View Dashboard>
    
    warning: |
      ⚠️ *WARNING*
      {{ alert.title }}
      
      {{ alert.description }}
      
      <{{ alert.link }}|View Details>
    
    info: |
      ℹ️ {{ alert.title }}
      {{ alert.description }}
  
  rules:
    - name: High QPS
      condition: "qps > 1000"
      severity: critical
      throttle: 300  # 5 minutes
      
    - name: Slow Queries
      condition: "slow_query_count > 10"
      severity: warning
      throttle: 600  # 10 minutes
      
    - name: Connection Pool Near Full
      condition: "connection_utilization > 0.9"
      severity: warning
      throttle: 300
```

### Send Alerts Programmatically

```typescript
import { SlackNotifier } from '@aishell/slack';

const notifier = new SlackNotifier({
  token: process.env.SLACK_BOT_TOKEN,
  channel: '#database-alerts'
});

// Send simple message
await notifier.send('Database backup completed');

// Send formatted message
await notifier.send({
  text: 'High QPS Alert',
  blocks: [
    {
      type: 'header',
      text: {
        type: 'plain_text',
        text: '🔴 Critical: High Query Rate'
      }
    },
    {
      type: 'section',
      fields: [
        { type: 'mrkdwn', text: '*Current QPS:*\n1,250' },
        { type: 'mrkdwn', text: '*Threshold:*\n1,000' },
        { type: 'mrkdwn', text: '*Duration:*\n5 minutes' }
      ]
    },
    {
      type: 'actions',
      elements: [
        {
          type: 'button',
          text: { type: 'plain_text', text: 'View Dashboard' },
          url: 'http://dashboard/performance'
        },
        {
          type: 'button',
          text: { type: 'plain_text', text: 'Acknowledge' },
          action_id: 'ack_alert'
        }
      ]
    }
  ]
});

// Upload file
await notifier.uploadFile({
  file: 'report.csv',
  filename: 'daily-report.csv',
  title: 'Daily Database Report',
  initial_comment: 'Here is today\'s database report'
});
```

---

## Interactive Components

### Interactive Messages

```typescript
// Send message with buttons
await notifier.send({
  text: 'Slow query detected',
  blocks: [
    {
      type: 'section',
      text: {
        type: 'mrkdwn',
        text: 'A slow query was detected:\n```SELECT * FROM large_table WHERE...```\nExecution time: 5.2s'
      }
    },
    {
      type: 'actions',
      elements: [
        {
          type: 'button',
          text: { type: 'plain_text', text: 'Optimize' },
          action_id: 'optimize_query',
          value: 'query_123'
        },
        {
          type: 'button',
          text: { type: 'plain_text', text: 'Kill Query' },
          action_id: 'kill_query',
          value: 'query_123',
          style: 'danger'
        },
        {
          type: 'button',
          text: { type: 'plain_text', text: 'Ignore' },
          action_id: 'ignore_query',
          value: 'query_123'
        }
      ]
    }
  ]
});

// Handle button clicks
aishell.slack.onAction('optimize_query', async (action) => {
  const queryId = action.value;
  const suggestions = await getOptimizationSuggestions(queryId);
  
  await notifier.send({
    channel: action.channel.id,
    thread_ts: action.message.ts,
    text: `Optimization suggestions:\n${suggestions}`
  });
});
```

### Select Menus

```typescript
// Database selector
await notifier.send({
  text: 'Select database',
  blocks: [
    {
      type: 'section',
      text: { type: 'mrkdwn', text: 'Select database to query:' },
      accessory: {
        type: 'static_select',
        action_id: 'select_database',
        placeholder: { type: 'plain_text', text: 'Choose database' },
        options: [
          { text: { type: 'plain_text', text: 'Production' }, value: 'prod' },
          { text: { type: 'plain_text', text: 'Staging' }, value: 'staging' },
          { text: { type: 'plain_text', text: 'Development' }, value: 'dev' }
        ]
      }
    }
  ]
});
```

### Modal Dialogs

```typescript
// Open modal for query input
await notifier.openModal({
  trigger_id: triggerId,
  view: {
    type: 'modal',
    callback_id: 'query_modal',
    title: { type: 'plain_text', text: 'Execute Query' },
    submit: { type: 'plain_text', text: 'Execute' },
    blocks: [
      {
        type: 'input',
        block_id: 'database',
        label: { type: 'plain_text', text: 'Database' },
        element: {
          type: 'static_select',
          action_id: 'database_select',
          options: [...]
        }
      },
      {
        type: 'input',
        block_id: 'query',
        label: { type: 'plain_text', text: 'SQL Query' },
        element: {
          type: 'plain_text_input',
          action_id: 'query_input',
          multiline: true
        }
      }
    ]
  }
});
```

---

## Bot Commands

### Configure AI-Shell Bot

Enable conversational interface:

```yaml
bot:
  enabled: true
  name: "@AI-Shell"
  channels: ["#database", "#dev"]
  dm_enabled: true
  
  commands:
    - pattern: "what is the (.*) on (.*)"
      handler: natural_language_query
    
    - pattern: "show me slow queries"
      handler: show_slow_queries
    
    - pattern: "database status"
      handler: show_status
    
    - pattern: "help"
      handler: show_help
```

### Natural Language Queries

In Slack:
```
@AI-Shell what is the total revenue today?
```

Bot responds:
```
💰 Total Revenue Today

$45,231.50

Breakdown:
• Orders: 287
• Avg order value: $157.62
• Top product: Widget Pro ($8,450)

📊 Trend: +15% vs yesterday
```

### Scheduled Reports

```yaml
scheduled_reports:
  - name: Daily Summary
    schedule: "0 9 * * *"  # 9 AM daily
    channel: "#database-reports"
    template: daily_summary
    
  - name: Weekly Performance
    schedule: "0 9 * * MON"  # 9 AM Monday
    channel: "#management"
    template: weekly_performance
    
  - name: Monthly Capacity
    schedule: "0 9 1 * *"  # 9 AM 1st of month
    channel: "#infrastructure"
    template: capacity_report
```

---

## Workflows

### Workflow Builder Integration

Create Slack workflows that use AI-Shell:

1. **Open** Slack Workflow Builder
2. **Create** new workflow
3. **Add** webhook step
4. **Configure** webhook URL: `http://your-server/aishell/webhook`
5. **Add** AI-Shell actions

**Example Workflow**:
- Trigger: Scheduled (daily at 9 AM)
- Action 1: Call AI-Shell webhook
- Action 2: Post results to #reports
- Action 3: Notify @management if issues

### Custom Workflow Actions

```typescript
// Register custom action
aishell.slack.registerWorkflowAction('run_report', async (inputs) => {
  const { report_type, period, channel } = inputs;
  
  // Generate report
  const report = await generateReport(report_type, period);
  
  // Post to channel
  await notifier.send({
    channel,
    text: `${report_type} Report`,
    blocks: [
      { type: 'header', text: { type: 'plain_text', text: report.title } },
      { type: 'section', text: { type: 'mrkdwn', text: report.summary } }
    ],
    files: [{ file: report.data, filename: `${report_type}-${period}.csv` }]
  });
  
  return { success: true, report_url: report.url };
});
```

---

## Use Cases

### Use Case 1: Real-Time Alerting

Configure alerts for critical events:

```bash
# Configure high QPS alert
aishell slack alert add \
  --name "High QPS" \
  --condition "qps > 1000" \
  --severity critical \
  --channel "#database-alerts" \
  --mention "@channel"

# Configure slow query alert
aishell slack alert add \
  --name "Slow Queries" \
  --condition "slow_query_count > 10" \
  --severity warning \
  --channel "#database-alerts" \
  --mention "@dba-oncall"
```

Result in Slack:
```
🔴 @channel CRITICAL ALERT
High Query Rate Detected

Current QPS: 1,250
Threshold: 1,000
Duration: 5 minutes

Action Required: Scale database resources

[View Dashboard] [Acknowledge] [Investigate]
```

### Use Case 2: Team Collaboration

Share query results with team:

```bash
# Execute query and share
aishell query "SELECT * FROM users WHERE created_today" \
  --output slack \
  --channel "#analytics"
```

Result in Slack:
```
📊 Query Results

SELECT * FROM users WHERE created_today

┌────┬──────────────┬─────────────────────┐
│ id │ name         │ email               │
├────┼──────────────┼─────────────────────┤
│ 1  │ John Doe     │ john@example.com    │
│ 2  │ Jane Smith   │ jane@example.com    │
└────┴──────────────┴─────────────────────┘

Total: 2 users
Execution time: 23ms

[Download CSV] [Run Again] [Share]
```

### Use Case 3: Automated Reports

Daily database health report:

```yaml
# Configure daily report
schedule:
  name: Daily Health Report
  cron: "0 9 * * *"
  channel: "#database-reports"
  report:
    - Database status
    - Query performance (last 24h)
    - Slow queries
    - Error summary
    - Capacity trends
```

Report in Slack at 9 AM:
```
📊 Daily Database Health Report
2025-10-28

✅ Overall Status: Healthy

Performance:
• QPS: 45.2 avg
• Latency: 23ms avg (P95: 120ms)
• Errors: 0.01%

Slow Queries: 5
• Top offender: 2.4s avg

Capacity:
• Storage: 65% used
• Connections: 12% used
• Growth: +2% this week

[View Full Report] [Download Data]
```

---

## Troubleshooting

### Issue 1: Bot Not Responding

```bash
# Check bot status
aishell slack status

# Test connection
aishell slack test

# Check logs
aishell logs --grep "slack"

# Verify token
aishell config get slack.botToken
```

### Issue 2: Missing Permissions

```bash
# Check required scopes
aishell slack check-permissions

# Output shows missing scopes:
# ❌ chat:write - Required for sending messages
# ✓ commands - Slash commands enabled

# Fix: Add missing scopes in Slack App settings
```

### Issue 3: Rate Limiting

```bash
# Configure rate limits
aishell config set slack.rateLimit.messagesPerMinute 60
aishell config set slack.rateLimit.commandsPerMinute 10

# Enable rate limit warnings
aishell config set slack.rateLimitWarnings true
```

---

## Best Practices

1. **Use Threads** for follow-up messages
2. **Mention Sparingly** - avoid @channel abuse
3. **Format Messages** - use blocks for rich formatting
4. **Throttle Alerts** - prevent alert fatigue
5. **Secure Tokens** - never commit to git
6. **Test First** - use test workspace
7. **Document Commands** - create Slack /help
8. **Monitor Usage** - track command frequency
9. **Graceful Errors** - user-friendly error messages
10. **Backup Config** - export Slack app config

---

## Summary

Slack integration provides:

- 🚨 **Real-Time Alerts** - Instant notifications
- 💬 **Slash Commands** - Execute queries from Slack
- 🤖 **Interactive Bot** - Natural language queries
- 📊 **Automated Reports** - Scheduled updates
- 🔗 **Team Collaboration** - Share insights
- 📱 **Mobile Access** - Work from anywhere

For more information:
- [Enhanced Dashboard](../features/enhanced-dashboard.md)
- [Email Notifications](../features/email-notifications.md)
- [Pattern Detection](../features/pattern-detection.md)

---

**Need Help?**
- 📖 [Slack API Docs](https://api.slack.com/docs)
- 💬 [Community Forum](https://github.com/yourusername/aishell/discussions)
- 🐛 [Report Issues](https://github.com/yourusername/aishell/issues)
