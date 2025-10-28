# Email Notifications - Quick Start Guide

Get up and running with AI-Shell email notifications in 5 minutes.

## Step 1: Install Dependencies

```bash
npm install nodemailer @types/nodemailer
```

## Step 2: Configure SMTP

### Option A: Gmail (Recommended for Testing)

1. Enable 2-factor authentication in your Google Account
2. Generate an App Password:
   - Go to Google Account Settings
   - Security → 2-Step Verification → App Passwords
   - Generate password for "Mail"

3. Create `.env` file:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-16-char-app-password
EMAIL_FROM=ai-shell@your-domain.com
```

### Option B: SendGrid (Recommended for Production)

1. Create SendGrid account
2. Generate API key
3. Create `.env` file:
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=your-sendgrid-api-key
EMAIL_FROM=ai-shell@your-domain.com
```

## Step 3: Initialize Service

```typescript
import { getEmailService } from './cli/notification-email';

const emailService = getEmailService({
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
  fromName: 'AI-Shell Alerts'
});

await emailService.initialize();
```

## Step 4: Send Test Email

```typescript
const success = await emailService.sendTestEmail('your-email@example.com');
console.log('Test email sent:', success);
```

## Step 5: Send Your First Alert

```typescript
await emailService.sendTemplateEmail(
  'query_failure',
  'dba@example.com',
  {
    severity: 'high',
    queryName: 'monthly_report',
    database: 'production',
    timestamp: new Date().toISOString(),
    error: 'Connection timeout after 30 seconds',
    query: 'SELECT * FROM large_table WHERE date > NOW() - INTERVAL 30 DAY'
  }
);
```

## Common Use Cases

### 1. Query Failure Alerts

```typescript
try {
  await database.query(sql);
} catch (error) {
  await emailService.sendTemplateEmail('query_failure', 'dba@example.com', {
    severity: 'high',
    queryName: 'critical_query',
    database: 'production',
    timestamp: new Date().toISOString(),
    error: error.message,
    query: sql
  });
}
```

### 2. Security Alerts

```typescript
await emailService.sendTemplateEmail('security_violation', 'security@example.com', {
  violationType: 'Unauthorized Access',
  user: req.user,
  ipAddress: req.ip,
  timestamp: new Date().toISOString(),
  details: 'Multiple failed login attempts',
  action: 'Account locked for 1 hour'
});
```

### 3. Backup Notifications

```typescript
await emailService.sendTemplateEmail('backup_completion', 'admin@example.com', {
  database: 'production',
  status: 'Success',
  startTime: '02:00:00',
  endTime: '02:45:30',
  duration: '45m 30s',
  backupSize: '2.3 GB',
  location: '/backups/prod.sql.gz',
  statusColor: '#4caf50'
});
```

### 4. Performance Alerts

```typescript
if (responseTime > threshold) {
  await emailService.sendTemplateEmail('performance_degradation', 'ops@example.com', {
    metricName: 'Query Response Time',
    database: 'production',
    severity: 'medium',
    currentValue: `${responseTime}ms`,
    threshold: `${threshold}ms`,
    timestamp: new Date().toISOString(),
    impact: 'Slow queries affecting user experience',
    recommendations: [
      'Add index on user_id column',
      'Review query execution plan',
      'Consider caching'
    ],
    historicalData: 'Avg: 850ms, P95: 1200ms'
  });
}
```

### 5. Daily Health Reports

```typescript
// Run daily at midnight
cron.schedule('0 0 * * *', async () => {
  await emailService.sendTemplateEmail('system_health', 'team@example.com', {
    date: new Date().toLocaleDateString(),
    overallStatus: 'Healthy',
    uptime: '99.98%',
    queriesExecuted: '1,234,567',
    successRate: '99.95',
    avgResponseTime: '145',
    activeConnections: '42',
    recentAlerts: ['Disk at 75%', 'Slow query at 14:32']
  });
});
```

## Managing Recipients

### Add Recipients

```typescript
// Single recipient
await emailService.addRecipient({
  email: 'john@example.com',
  name: 'John Doe',
  groups: ['developers', 'alerts']
});

// With preferences
await emailService.addRecipient({
  email: 'ops@example.com',
  groups: ['operations'],
  preferences: {
    severity: ['critical', 'high'],
    categories: ['security_violation', 'performance_degradation']
  }
});
```

### Send to Group

```typescript
const recipients = await emailService.getRecipientsByGroup('developers');
const emails = recipients.map(r => r.email);

await emailService.sendTemplateEmail('system_health', emails, {
  // ... template variables
});
```

## Monitoring

### Check Statistics

```typescript
const stats = emailService.getStats();
console.log(`Sent: ${stats.sent}, Failed: ${stats.failed}, Pending: ${stats.pending}`);
```

### Monitor Events

```typescript
emailService.on('sent', ({ messageId }) => {
  console.log('Email sent:', messageId);
});

emailService.on('failed', ({ messageId, error }) => {
  console.error('Email failed:', messageId, error);
});

emailService.on('retry', ({ messageId, attempt }) => {
  console.log(`Retrying ${messageId}, attempt ${attempt}`);
});
```

## Next Steps

- **[Full Documentation](./email-notifications.md)** - Complete guide with all features
- **[API Reference](./email-notifications.md#api-reference)** - Detailed API documentation
- **[Troubleshooting](./email-notifications.md#troubleshooting)** - Common issues and solutions
- **[Best Practices](./email-notifications.md#best-practices)** - Production deployment tips

## Troubleshooting Quick Fixes

### Gmail Authentication Error
```typescript
// Use app-specific password, not your regular password
// Enable 2FA first, then generate app password
```

### Connection Timeout
```typescript
// Check firewall, try different port
const config = {
  smtp: {
    port: 465,    // Try port 465
    secure: true  // Enable TLS
  }
};
```

### Rate Limited
```typescript
// Increase rate limit or enable batching
const config = {
  rateLimitPerMinute: 100,
  enableBatching: true,
  batchSize: 20
};
```

## Support

Need help? Check:
- [Full Documentation](./email-notifications.md)
- [Implementation Details](./email-notifications-implementation.md)
- [Test Examples](../../tests/cli/notification-email.test.ts)
