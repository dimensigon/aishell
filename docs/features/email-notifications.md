# Email Notification System

Comprehensive email delivery system for AI-Shell with template support, queuing, batching, and intelligent retry logic.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Email Templates](#email-templates)
- [Recipient Management](#recipient-management)
- [Queue Management](#queue-management)
- [Rate Limiting](#rate-limiting)
- [Batch Processing](#batch-processing)
- [Retry Logic](#retry-logic)
- [SMTP Providers](#smtp-providers)
- [CLI Commands](#cli-commands)
- [API Reference](#api-reference)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The Email Notification System provides enterprise-grade email delivery for AI-Shell alerts, reports, and notifications. It features:

- **Template-based composition** with HTML and plain-text support
- **Connection pooling** for high-throughput scenarios
- **Queue system** with persistent storage
- **Rate limiting** to prevent overwhelming recipients
- **Batch processing** for efficient bulk sending
- **Exponential backoff** retry logic
- **Recipient groups** for easy management
- **Multiple SMTP providers** (Gmail, SendGrid, AWS SES, custom)

## Features

### Core Capabilities

1. **SMTP Configuration**
   - Multiple provider support
   - Connection pooling
   - TLS/SSL encryption
   - Authentication

2. **Email Templates**
   - Pre-built templates for common alerts
   - Custom template support
   - Variable substitution
   - Conditional rendering
   - Loop support

3. **Delivery Management**
   - Queue system with persistence
   - Batch processing
   - Rate limiting
   - Priority handling
   - Scheduled sending

4. **Reliability**
   - Retry with exponential backoff
   - Error tracking
   - Delivery statistics
   - Event notifications

5. **Recipient Management**
   - Group-based organization
   - Individual preferences
   - Quiet hours support
   - Severity filtering

## Installation

### Dependencies

Add required packages to your project:

```bash
npm install nodemailer @types/nodemailer
```

### Module Import

```typescript
import {
  EmailNotificationService,
  getEmailService,
  SMTPConfig,
  EmailTemplate
} from './cli/notification-email';
```

## Configuration

### Basic Configuration

```typescript
const config = {
  smtp: {
    host: 'smtp.gmail.com',
    port: 587,
    secure: false,
    auth: {
      user: 'your-email@gmail.com',
      pass: 'your-app-password'
    },
    pool: true,
    maxConnections: 5,
    maxMessages: 100
  },
  fromAddress: 'ai-shell@your-domain.com',
  fromName: 'AI-Shell Alerts',
  replyTo: 'support@your-domain.com',
  maxRetries: 3,
  retryDelayMs: 5000,
  batchSize: 10,
  rateLimitPerMinute: 60,
  enableBatching: true,
  batchWindowMs: 30000
};

const emailService = new EmailNotificationService(config);
await emailService.initialize();
```

### Environment Variables

Store sensitive configuration in environment variables:

```bash
# .env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
EMAIL_FROM=ai-shell@your-domain.com
EMAIL_FROM_NAME="AI-Shell Notifications"
```

Load configuration:

```typescript
const config = {
  smtp: {
    host: process.env.SMTP_HOST!,
    port: parseInt(process.env.SMTP_PORT!),
    secure: false,
    auth: {
      user: process.env.SMTP_USER!,
      pass: process.env.SMTP_PASS!
    }
  },
  fromAddress: process.env.EMAIL_FROM!,
  fromName: process.env.EMAIL_FROM_NAME!
};
```

## Quick Start

### Initialize Service

```typescript
import { getEmailService } from './cli/notification-email';

const emailService = getEmailService({
  smtp: {
    host: 'smtp.gmail.com',
    port: 587,
    secure: false,
    auth: {
      user: 'your-email@gmail.com',
      pass: 'your-app-password'
    }
  },
  fromAddress: 'ai-shell@example.com'
});

await emailService.initialize();
```

### Send Test Email

```typescript
const success = await emailService.sendTestEmail('recipient@example.com');
console.log('Test email sent:', success);
```

### Send Alert Using Template

```typescript
await emailService.sendTemplateEmail(
  'query_failure',
  'dba@example.com',
  {
    severity: 'high',
    queryName: 'monthly_report',
    database: 'production',
    timestamp: new Date().toISOString(),
    error: 'Connection timeout after 30s',
    query: 'SELECT * FROM large_table WHERE date > NOW() - INTERVAL 30 DAY'
  }
);
```

## Email Templates

### Available Templates

#### 1. Query Failure Alert

**Template ID:** `query_failure`

**Variables:**
- `severity` - Alert severity (critical, high, medium, low)
- `queryName` - Name/identifier of the query
- `database` - Database name
- `timestamp` - Time of failure
- `error` - Error message
- `query` - SQL query that failed

**Example:**
```typescript
await emailService.sendTemplateEmail('query_failure', 'dba@example.com', {
  severity: 'high',
  queryName: 'sales_report',
  database: 'production',
  timestamp: new Date().toISOString(),
  error: 'Table "sales_data" does not exist',
  query: 'SELECT SUM(amount) FROM sales_data WHERE date = CURRENT_DATE'
});
```

#### 2. Security Violation Alert

**Template ID:** `security_violation`

**Variables:**
- `violationType` - Type of security violation
- `user` - Username or identifier
- `ipAddress` - IP address of the request
- `timestamp` - Time of violation
- `details` - Detailed description
- `action` - Action taken by system

**Example:**
```typescript
await emailService.sendTemplateEmail('security_violation', 'security@example.com', {
  violationType: 'Unauthorized Access Attempt',
  user: 'anonymous',
  ipAddress: '192.168.1.100',
  timestamp: new Date().toISOString(),
  details: 'Multiple failed login attempts with invalid credentials',
  action: 'IP address blocked for 24 hours'
});
```

#### 3. Backup Completion

**Template ID:** `backup_completion`

**Variables:**
- `database` - Database name
- `status` - Success or Failed
- `startTime` - Backup start time
- `endTime` - Backup end time
- `duration` - Total duration
- `backupSize` - Size of backup file
- `location` - Backup file location
- `compression` - Compression method (optional)
- `error` - Error message if failed (optional)
- `statusColor` - HTML color for status

**Example:**
```typescript
await emailService.sendTemplateEmail('backup_completion', 'admin@example.com', {
  database: 'production',
  status: 'Success',
  startTime: '02:00:00',
  endTime: '02:45:30',
  duration: '45m 30s',
  backupSize: '2.3 GB',
  location: '/backups/prod-2024-01-15.sql.gz',
  compression: 'gzip',
  statusColor: '#4caf50'
});
```

#### 4. Performance Degradation

**Template ID:** `performance_degradation`

**Variables:**
- `metricName` - Name of the metric
- `database` - Database name
- `severity` - Alert severity
- `currentValue` - Current metric value
- `threshold` - Alert threshold
- `timestamp` - Time of detection
- `impact` - Impact description
- `recommendations` - Array of recommendations
- `historicalData` - Historical metric data

**Example:**
```typescript
await emailService.sendTemplateEmail('performance_degradation', 'ops@example.com', {
  metricName: 'Query Response Time',
  database: 'production',
  severity: 'medium',
  currentValue: '2500ms',
  threshold: '1000ms',
  timestamp: new Date().toISOString(),
  impact: 'Slow queries affecting user experience',
  recommendations: [
    'Add index on user_id column',
    'Review query execution plan',
    'Consider query result caching'
  ],
  historicalData: 'Average: 850ms, P95: 1200ms, P99: 2100ms'
});
```

#### 5. System Health Report

**Template ID:** `system_health`

**Variables:**
- `date` - Report date
- `overallStatus` - Overall system status
- `uptime` - System uptime
- `queriesExecuted` - Total queries executed
- `successRate` - Success rate percentage
- `avgResponseTime` - Average response time
- `activeConnections` - Number of active connections
- `recentAlerts` - Array of recent alerts

**Example:**
```typescript
await emailService.sendTemplateEmail('system_health', 'team@example.com', {
  date: new Date().toLocaleDateString(),
  overallStatus: 'Healthy',
  uptime: '99.98%',
  queriesExecuted: '1,234,567',
  successRate: '99.95',
  avgResponseTime: '145',
  activeConnections: '42',
  recentAlerts: [
    'Disk usage at 75% on server-1',
    'Slow query detected at 14:32',
    'Connection pool utilization above 80%'
  ]
});
```

### Custom Templates

Create custom templates for specific use cases:

```typescript
const customTemplate: EmailTemplate = {
  id: 'maintenance_window',
  name: 'Maintenance Window Notification',
  subject: 'Scheduled Maintenance: {{system}} on {{date}}',
  htmlBody: `
    <html>
      <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #ff9800; color: white; padding: 20px;">
          <h1>Scheduled Maintenance</h1>
        </div>
        <div style="padding: 20px;">
          <h2>{{system}}</h2>
          <p><strong>Date:</strong> {{date}}</p>
          <p><strong>Start Time:</strong> {{startTime}}</p>
          <p><strong>End Time:</strong> {{endTime}}</p>
          <p><strong>Duration:</strong> {{duration}}</p>
          <h3>What to expect:</h3>
          <p>{{description}}</p>
          <h3>Impact:</h3>
          <ul>
            {{#each impactItems}}
            <li>{{this}}</li>
            {{/each}}
          </ul>
          <p>For questions, contact {{contactEmail}}</p>
        </div>
      </body>
    </html>
  `,
  textBody: `
Scheduled Maintenance

System: {{system}}
Date: {{date}}
Start Time: {{startTime}}
End Time: {{endTime}}
Duration: {{duration}}

What to expect:
{{description}}

Impact:
{{#each impactItems}}
- {{this}}
{{/each}}

For questions, contact {{contactEmail}}
  `,
  category: 'custom',
  severity: 'info',
  variables: ['system', 'date', 'startTime', 'endTime', 'duration', 'description', 'impactItems', 'contactEmail']
};

await emailService.addTemplate(customTemplate);

// Use the custom template
await emailService.sendTemplateEmail('maintenance_window', ['team@example.com'], {
  system: 'Production Database',
  date: '2024-02-01',
  startTime: '02:00 AM EST',
  endTime: '06:00 AM EST',
  duration: '4 hours',
  description: 'We will be upgrading the database server and applying security patches.',
  impactItems: [
    'Database will be unavailable during the maintenance window',
    'Application services will be offline',
    'Scheduled backups will be delayed'
  ],
  contactEmail: 'support@example.com'
});
```

### Template Syntax

The template engine supports:

#### Variable Substitution
```
{{variableName}}
```

#### Conditionals
```
{{#if condition}}
  Content shown when condition is true
{{/if}}
```

#### Loops
```
{{#each arrayName}}
  {{this}} - for simple arrays
  {{propertyName}} - for object arrays
{{/each}}
```

## Recipient Management

### Add Recipients

```typescript
await emailService.addRecipient({
  email: 'john.doe@example.com',
  name: 'John Doe',
  groups: ['developers', 'admins']
});
```

### Add Recipients with Preferences

```typescript
await emailService.addRecipient({
  email: 'ops-team@example.com',
  name: 'Operations Team',
  groups: ['operations', 'alerts'],
  preferences: {
    severity: ['critical', 'high'], // Only receive critical and high severity alerts
    categories: ['security_violation', 'performance_degradation'],
    quietHours: {
      start: '22:00',
      end: '08:00'
    }
  }
});
```

### Remove Recipients

```typescript
await emailService.removeRecipient('john.doe@example.com');
```

### Get Recipients by Group

```typescript
const developers = await emailService.getRecipientsByGroup('developers');
console.log('Developer recipients:', developers);
```

### List All Recipients

```typescript
const allRecipients = await emailService.listRecipients();
console.log('Total recipients:', allRecipients.length);

// Filter by group
const opsTeam = await emailService.listRecipients('operations');
```

### Send to Group

```typescript
const recipients = await emailService.getRecipientsByGroup('security');
const emailAddresses = recipients.map(r => r.email);

await emailService.sendTemplateEmail(
  'security_violation',
  emailAddresses,
  {
    violationType: 'Brute Force Attack',
    user: 'attacker',
    ipAddress: '203.0.113.42',
    timestamp: new Date().toISOString(),
    details: '100+ failed login attempts in 5 minutes',
    action: 'IP blocked, incident logged'
  }
);
```

## Queue Management

### Queue Email

```typescript
const messageId = await emailService.queueEmail({
  id: crypto.randomUUID(),
  to: ['recipient@example.com'],
  subject: 'Test Email',
  html: '<p>This is a test</p>',
  text: 'This is a test',
  severity: 'info',
  category: 'custom',
  createdAt: new Date()
});

console.log('Queued with ID:', messageId);
```

### Check Queue Status

```typescript
const queueStatus = await emailService.getQueueStatus();
console.log('Pending emails:', queueStatus.filter(i => i.status === 'pending').length);
console.log('Failed emails:', queueStatus.filter(i => i.status === 'failed').length);
```

### Get Statistics

```typescript
const stats = emailService.getStats();
console.log('Total sent:', stats.sent);
console.log('Total failed:', stats.failed);
console.log('Currently pending:', stats.pending);
console.log('In queue:', stats.queued);
console.log('Last sent:', stats.lastSent);
console.log('Last error:', stats.lastError);
```

## Rate Limiting

Rate limiting prevents overwhelming email servers and recipients:

```typescript
const emailService = new EmailNotificationService({
  smtp: { /* ... */ },
  rateLimitPerMinute: 30 // Max 30 emails per minute
});
```

The rate limiter:
- Automatically throttles email sending
- Refills tokens every minute
- Queues excess emails for later delivery
- Prevents SMTP server blocks

## Batch Processing

Batch processing improves efficiency for bulk emails:

```typescript
const emailService = new EmailNotificationService({
  smtp: { /* ... */ },
  enableBatching: true,
  batchSize: 20, // Process 20 emails at once
  batchWindowMs: 30000 // Wait up to 30 seconds to collect batch
});
```

Benefits:
- Reduced connection overhead
- Better throughput for bulk operations
- Configurable batch size and timing
- Automatic batch processing when full

### Event Monitoring

```typescript
emailService.on('batch_processed', ({ count }) => {
  console.log(`Processed batch of ${count} emails`);
});
```

## Retry Logic

Automatic retry with exponential backoff:

```typescript
const emailService = new EmailNotificationService({
  smtp: { /* ... */ },
  maxRetries: 5, // Try up to 5 times
  retryDelayMs: 5000 // Initial delay of 5 seconds
});
```

Retry behavior:
- **Attempt 1:** 5 seconds delay
- **Attempt 2:** 10 seconds delay
- **Attempt 3:** 20 seconds delay
- **Attempt 4:** 40 seconds delay
- **Attempt 5:** 80 seconds delay

After max retries, email is marked as failed.

### Monitor Retries

```typescript
emailService.on('retry', ({ messageId, attempt }) => {
  console.log(`Retrying email ${messageId}, attempt ${attempt}`);
});

emailService.on('failed', ({ messageId, error }) => {
  console.log(`Email ${messageId} failed permanently:`, error);
});
```

## SMTP Providers

### Gmail

```typescript
const config = {
  smtp: {
    host: 'smtp.gmail.com',
    port: 587,
    secure: false,
    auth: {
      user: 'your-email@gmail.com',
      pass: 'your-app-password' // Generate app password in Google Account settings
    }
  }
};
```

**Setup:**
1. Enable 2-factor authentication
2. Generate App Password in Google Account settings
3. Use app password (not your regular password)

### SendGrid

```typescript
const config = {
  smtp: {
    host: 'smtp.sendgrid.net',
    port: 587,
    secure: false,
    auth: {
      user: 'apikey',
      pass: 'your-sendgrid-api-key'
    }
  }
};
```

**Setup:**
1. Create SendGrid account
2. Generate API key
3. Use 'apikey' as username
4. Use API key as password

### AWS SES

```typescript
const config = {
  smtp: {
    host: 'email-smtp.us-east-1.amazonaws.com',
    port: 587,
    secure: false,
    auth: {
      user: 'your-smtp-username',
      pass: 'your-smtp-password'
    }
  }
};
```

**Setup:**
1. Create SMTP credentials in AWS SES console
2. Verify sender email addresses
3. Request production access (if needed)

### Office 365

```typescript
const config = {
  smtp: {
    host: 'smtp.office365.com',
    port: 587,
    secure: false,
    auth: {
      user: 'your-email@yourdomain.com',
      pass: 'your-password'
    }
  }
};
```

### Custom SMTP

```typescript
const config = {
  smtp: {
    host: 'mail.your-domain.com',
    port: 465, // or 587
    secure: true, // true for port 465
    auth: {
      user: 'username',
      pass: 'password'
    },
    // Connection pooling
    pool: true,
    maxConnections: 5,
    maxMessages: 100,
    // Rate limiting at SMTP level
    rateDelta: 1000,
    rateLimit: 10
  }
};
```

## CLI Commands

### Setup Email Configuration

```bash
# Interactive setup
ai-shell notification setup-email

# Direct configuration
ai-shell notification setup-email \
  --host smtp.gmail.com \
  --port 587 \
  --user your-email@gmail.com \
  --pass your-app-password \
  --from ai-shell@your-domain.com
```

### Send Test Email

```bash
ai-shell notification send-test --to recipient@example.com
```

### Configure Alerts

```bash
# Enable specific alert types
ai-shell notification configure-alerts \
  --enable query_failure \
  --enable security_violation \
  --severity critical,high

# Set recipients for alert category
ai-shell notification configure-alerts \
  --category security_violation \
  --recipients security@example.com,admin@example.com
```

### List Templates

```bash
ai-shell notification list-templates
ai-shell notification list-templates --category security_violation
```

### Add Recipient

```bash
ai-shell notification add-recipient \
  --email john@example.com \
  --name "John Doe" \
  --groups developers,admins

# Add with preferences
ai-shell notification add-recipient \
  --email ops@example.com \
  --groups operations \
  --severity critical,high \
  --quiet-hours 22:00-08:00
```

### Remove Recipient

```bash
ai-shell notification remove-recipient --email john@example.com
```

### List Recipients

```bash
ai-shell notification list-recipients
ai-shell notification list-recipients --group developers
```

### View Statistics

```bash
ai-shell notification stats
ai-shell notification queue-status
```

## API Reference

### EmailNotificationService

#### Constructor

```typescript
new EmailNotificationService(config?: Partial<EmailNotificationConfig>)
```

#### Methods

##### initialize()
```typescript
async initialize(): Promise<void>
```
Initialize SMTP connection and verify configuration.

##### setupEmail()
```typescript
async setupEmail(smtpConfig: Partial<SMTPConfig>): Promise<void>
```
Update SMTP configuration and reinitialize.

##### sendTestEmail()
```typescript
async sendTestEmail(to: string): Promise<boolean>
```
Send test email to verify configuration.

##### sendTemplateEmail()
```typescript
async sendTemplateEmail(
  templateId: string,
  to: string | string[],
  variables: Record<string, any>,
  options?: {
    cc?: string[];
    bcc?: string[];
    attachments?: EmailAttachment[];
    priority?: 'high' | 'normal' | 'low';
  }
): Promise<string>
```
Send email using template.

##### queueEmail()
```typescript
async queueEmail(message: EmailMessage): Promise<string>
```
Queue email for later delivery.

##### addRecipient()
```typescript
async addRecipient(recipient: Omit<Recipient, 'enabled'>): Promise<void>
```
Add recipient to database.

##### removeRecipient()
```typescript
async removeRecipient(email: string): Promise<void>
```
Remove recipient from database.

##### getRecipientsByGroup()
```typescript
async getRecipientsByGroup(group: string): Promise<Recipient[]>
```
Get all recipients in a group.

##### listRecipients()
```typescript
async listRecipients(filterGroup?: string): Promise<Recipient[]>
```
List all recipients, optionally filtered by group.

##### addTemplate()
```typescript
async addTemplate(template: EmailTemplate): Promise<void>
```
Add custom template.

##### removeTemplate()
```typescript
async removeTemplate(templateId: string): Promise<void>
```
Remove custom template (cannot remove defaults).

##### listTemplates()
```typescript
listTemplates(): EmailTemplate[]
```
List all available templates.

##### getTemplate()
```typescript
getTemplate(templateId: string): EmailTemplate | undefined
```
Get specific template by ID.

##### getStats()
```typescript
getStats(): EmailStats
```
Get delivery statistics.

##### getQueueStatus()
```typescript
async getQueueStatus(): Promise<EmailQueueItem[]>
```
Get current queue status.

##### shutdown()
```typescript
async shutdown(): Promise<void>
```
Gracefully shutdown service.

#### Events

```typescript
emailService.on('initialized', ({ timestamp }) => {});
emailService.on('queued', ({ messageId, message }) => {});
emailService.on('sent', ({ messageId }) => {});
emailService.on('retry', ({ messageId, attempt }) => {});
emailService.on('failed', ({ messageId, error }) => {});
emailService.on('batch_processed', ({ count }) => {});
emailService.on('error', ({ type, error }) => {});
emailService.on('shutdown', ({ timestamp }) => {});
```

## Best Practices

### Security

1. **Never hardcode credentials**
   ```typescript
   // ❌ Don't do this
   const config = {
     auth: { user: 'myemail@gmail.com', pass: 'mypassword123' }
   };

   // ✅ Do this
   const config = {
     auth: {
       user: process.env.SMTP_USER!,
       pass: process.env.SMTP_PASS!
     }
   };
   ```

2. **Use app-specific passwords** for Gmail and other providers

3. **Enable TLS/SSL** for production:
   ```typescript
   const config = {
     smtp: {
       port: 465,
       secure: true // Enable TLS
     }
   };
   ```

### Performance

1. **Enable connection pooling** for high volume:
   ```typescript
   const config = {
     smtp: {
       pool: true,
       maxConnections: 10,
       maxMessages: 100
     }
   };
   ```

2. **Use batching** for bulk operations:
   ```typescript
   const config = {
     enableBatching: true,
     batchSize: 50
   };
   ```

3. **Set appropriate rate limits**:
   ```typescript
   const config = {
     rateLimitPerMinute: 100 // Based on provider limits
   };
   ```

### Reliability

1. **Monitor events**:
   ```typescript
   emailService.on('failed', ({ messageId, error }) => {
     logger.error('Email failed', { messageId, error });
     // Alert ops team, store in database, etc.
   });
   ```

2. **Configure retries** appropriately:
   ```typescript
   const config = {
     maxRetries: 5,
     retryDelayMs: 5000
   };
   ```

3. **Implement fallback**:
   ```typescript
   try {
     await emailService.sendTemplateEmail(/* ... */);
   } catch (error) {
     // Fallback to alternative notification method
     await sendSlackNotification(/* ... */);
   }
   ```

### Email Content

1. **Always provide both HTML and text versions**

2. **Keep templates simple and responsive**

3. **Include unsubscribe links** (for marketing emails)

4. **Test templates** with various email clients

5. **Use descriptive subjects**

## Troubleshooting

### Connection Issues

**Problem:** Cannot connect to SMTP server

**Solutions:**
- Verify host and port
- Check firewall rules
- Ensure correct security settings (TLS/SSL)
- Verify credentials
- Check for IP restrictions

```typescript
// Test connection
try {
  await emailService.initialize();
  console.log('Connection successful');
} catch (error) {
  console.error('Connection failed:', error.message);
}
```

### Authentication Failures

**Problem:** Authentication failed

**Solutions:**
- Use app-specific passwords (Gmail)
- Verify username/password
- Check for 2FA requirements
- Ensure account is not locked

### Rate Limiting

**Problem:** Emails being rate limited

**Solutions:**
- Increase `rateLimitPerMinute`
- Check provider limits
- Enable batching
- Spread sending over time

```typescript
// Configure for high volume
const config = {
  rateLimitPerMinute: 100,
  enableBatching: true,
  batchSize: 50
};
```

### Queue Not Processing

**Problem:** Emails stuck in queue

**Solutions:**
- Check service is initialized
- Verify queue processor is running
- Check for errors in logs
- Ensure sufficient retries configured

```typescript
// Monitor queue
const status = await emailService.getQueueStatus();
console.log('Pending:', status.filter(i => i.status === 'pending').length);
console.log('Failed:', status.filter(i => i.status === 'failed').length);
```

### Template Rendering Issues

**Problem:** Variables not replaced in template

**Solutions:**
- Verify variable names match
- Check for typos
- Ensure variables are provided
- Test with simple template first

```typescript
// Debug template rendering
const template = 'Hello {{name}}';
const rendered = emailService['renderTemplate'](template, { name: 'World' });
console.log('Rendered:', rendered); // Should be "Hello World"
```

### Delivery Failures

**Problem:** Emails not being delivered

**Solutions:**
- Check spam folders
- Verify recipient addresses
- Review bounce messages
- Check SPF/DKIM/DMARC records
- Monitor statistics

```typescript
// Check delivery stats
const stats = emailService.getStats();
console.log('Success rate:', (stats.sent / (stats.sent + stats.failed)) * 100);
```

## Examples

### Complete Monitoring Setup

```typescript
import { getEmailService } from './cli/notification-email';

// Initialize service
const emailService = getEmailService({
  smtp: {
    host: process.env.SMTP_HOST!,
    port: parseInt(process.env.SMTP_PORT!),
    secure: false,
    auth: {
      user: process.env.SMTP_USER!,
      pass: process.env.SMTP_PASS!
    },
    pool: true,
    maxConnections: 10
  },
  fromAddress: process.env.EMAIL_FROM!,
  fromName: 'AI-Shell Monitor',
  rateLimitPerMinute: 60,
  enableBatching: true
});

await emailService.initialize();

// Add recipients
await emailService.addRecipient({
  email: 'dba@example.com',
  name: 'Database Admin',
  groups: ['database', 'critical-alerts'],
  preferences: {
    severity: ['critical', 'high'],
    categories: ['query_failure', 'performance_degradation']
  }
});

await emailService.addRecipient({
  email: 'security@example.com',
  name: 'Security Team',
  groups: ['security', 'critical-alerts'],
  preferences: {
    categories: ['security_violation']
  }
});

// Monitor events
emailService.on('sent', ({ messageId }) => {
  console.log('Email sent:', messageId);
});

emailService.on('failed', ({ messageId, error }) => {
  console.error('Email failed:', messageId, error);
});

// Send alerts based on events
async function sendQueryFailureAlert(query: any, error: Error) {
  const recipients = await emailService.getRecipientsByGroup('database');
  await emailService.sendTemplateEmail(
    'query_failure',
    recipients.map(r => r.email),
    {
      severity: 'high',
      queryName: query.name,
      database: query.database,
      timestamp: new Date().toISOString(),
      error: error.message,
      query: query.sql
    },
    { priority: 'high' }
  );
}

async function sendSecurityAlert(violation: any) {
  const recipients = await emailService.getRecipientsByGroup('security');
  await emailService.sendTemplateEmail(
    'security_violation',
    recipients.map(r => r.email),
    {
      violationType: violation.type,
      user: violation.user,
      ipAddress: violation.ip,
      timestamp: new Date().toISOString(),
      details: violation.details,
      action: violation.action
    },
    { priority: 'high' }
  );
}

// Daily health report
async function sendDailyHealthReport() {
  const recipients = await emailService.getRecipientsByGroup('reports');
  await emailService.sendTemplateEmail(
    'system_health',
    recipients.map(r => r.email),
    {
      date: new Date().toLocaleDateString(),
      overallStatus: 'Healthy',
      uptime: '99.98%',
      queriesExecuted: '1,234,567',
      successRate: '99.95',
      avgResponseTime: '145',
      activeConnections: '42',
      recentAlerts: ['Disk usage at 75%', 'Slow query at 14:32']
    }
  );
}

// Schedule daily report
setInterval(sendDailyHealthReport, 24 * 60 * 60 * 1000);
```

---

**Next Steps:**
- [Security Audit Log](./security-audit.md)
- [Backup System](./backup-system.md)
- [Performance Monitoring](./performance-monitoring.md)
