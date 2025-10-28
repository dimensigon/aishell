/**
 * Example Integration: Connecting Slack with AI-Shell Systems
 *
 * This file demonstrates how to integrate the Slack notification system
 * with various AI-Shell components like health monitoring, security auditing,
 * and query execution.
 */

import SlackIntegration from '../../src/cli/notification-slack';

// ============================================================================
// Example 1: Health Monitor Integration
// ============================================================================

/**
 * Integrate Slack with health monitoring system
 * Sends health check results to Slack on schedule
 */
export async function setupHealthMonitorSlackIntegration() {
  const slack = new SlackIntegration();

  // Run health check every hour
  setInterval(async () => {
    try {
      // Simulated health check (replace with actual implementation)
      const healthChecks = {
        database: await checkDatabase(),
        api: await checkAPI(),
        storage: await checkStorage(),
        cache: await checkCache(),
      };

      const allHealthy = Object.values(healthChecks).every(Boolean);
      const status = allHealthy ? 'healthy' : 'degraded';

      // Send to Slack
      await slack.sendHealthUpdate(status, healthChecks, {
        uptime: process.uptime(),
        memory_usage: `${(process.memoryUsage().heapUsed / 1024 / 1024).toFixed(2)} MB`,
        cpu_load: '15%', // Replace with actual CPU metric
      });

      console.log(`✓ Health check sent to Slack: ${status}`);
    } catch (error) {
      console.error('Failed to send health check:', error);
    }
  }, 60 * 60 * 1000); // Every hour
}

async function checkDatabase(): Promise<boolean> {
  // Implement actual database health check
  return true;
}

async function checkAPI(): Promise<boolean> {
  // Implement actual API health check
  return true;
}

async function checkStorage(): Promise<boolean> {
  // Implement actual storage health check
  return true;
}

async function checkCache(): Promise<boolean> {
  // Implement actual cache health check
  return true;
}

// ============================================================================
// Example 2: Security Audit Integration
// ============================================================================

/**
 * Integrate Slack with security auditing system
 * Sends security alerts immediately when threats detected
 */
export async function setupSecurityAuditSlackIntegration() {
  const slack = new SlackIntegration();

  // Monitor for SQL injection attempts
  const securityMonitor = {
    async onSQLInjectionAttempt(details: {
      query: string;
      ip: string;
      timestamp: Date;
    }) {
      await slack.sendSecurityAlert(
        'SQL Injection Attempt Detected',
        `Malicious SQL query blocked from IP ${details.ip}`,
        'critical',
        {
          query: details.query.substring(0, 200),
          ip_address: details.ip,
          timestamp: details.timestamp.toISOString(),
          action_taken: 'Query blocked and IP temporarily banned',
          threat_level: 'high',
        }
      );
    },

    async onAuthenticationFailure(details: {
      username: string;
      ip: string;
      attempts: number;
    }) {
      const severity = details.attempts >= 5 ? 'high' : 'medium';

      await slack.sendSecurityAlert(
        'Multiple Authentication Failures',
        `${details.attempts} failed login attempts for user ${details.username}`,
        severity,
        {
          username: details.username,
          ip_address: details.ip,
          attempts: details.attempts,
          last_attempt: new Date().toISOString(),
          recommendation: details.attempts >= 5 ? 'Account locked' : 'Monitor closely',
        }
      );
    },

    async onSuspiciousActivity(details: {
      type: string;
      description: string;
      user?: string;
      ip?: string;
    }) {
      await slack.sendSecurityAlert(
        'Suspicious Activity Detected',
        details.description,
        'medium',
        {
          activity_type: details.type,
          user: details.user || 'Unknown',
          ip_address: details.ip || 'Unknown',
          timestamp: new Date().toISOString(),
        }
      );
    },
  };

  return securityMonitor;
}

// ============================================================================
// Example 3: Query Execution Integration
// ============================================================================

/**
 * Integrate Slack with query execution system
 * Sends alerts for slow queries or large result sets
 */
export async function setupQueryExecutionSlackIntegration() {
  const slack = new SlackIntegration();

  const queryMonitor = {
    async onQueryExecuted(details: {
      query: string;
      rows: number;
      executionTime: number;
      user?: string;
    }) {
      // Only alert on slow queries (>5 seconds) or large result sets (>1000 rows)
      const isSlow = details.executionTime > 5000;
      const isLarge = details.rows > 1000;

      if (isSlow || isLarge) {
        await slack.sendQueryAlert(
          details.query,
          { rows: Array(details.rows).fill({}) },
          {
            executionTime: details.executionTime,
            user: details.user,
            warning: isSlow ? 'Slow query' : 'Large result set',
          }
        );
      }
    },

    async onQueryError(details: {
      query: string;
      error: string;
      user?: string;
    }) {
      await slack.sendAlert({
        type: 'query',
        severity: 'high',
        title: 'Query Execution Error',
        description: `Query failed: ${details.error}`,
        details: {
          query: details.query.substring(0, 200),
          error_message: details.error,
          user: details.user || 'Unknown',
          timestamp: new Date().toISOString(),
        },
        timestamp: Date.now(),
      });
    },
  };

  return queryMonitor;
}

// ============================================================================
// Example 4: Backup System Integration
// ============================================================================

/**
 * Integrate Slack with backup system
 * Sends backup completion and failure notifications
 */
export async function setupBackupSlackIntegration() {
  const slack = new SlackIntegration();

  const backupMonitor = {
    async onBackupComplete(details: {
      backupPath: string;
      size: number;
      duration: number;
      type: string;
    }) {
      await slack.sendBackupNotification(
        true,
        details.backupPath,
        details.size,
        {
          backup_type: details.type,
          duration: `${(details.duration / 1000).toFixed(2)} seconds`,
          compression: 'gzip',
          timestamp: new Date().toISOString(),
        }
      );
    },

    async onBackupFailed(details: {
      error: string;
      type: string;
      attemptedPath?: string;
    }) {
      await slack.sendBackupNotification(
        false,
        details.attemptedPath || 'Unknown',
        0,
        {
          backup_type: details.type,
          error_message: details.error,
          timestamp: new Date().toISOString(),
          action_required: 'Manual backup recommended',
        }
      );
    },
  };

  return backupMonitor;
}

// ============================================================================
// Example 5: Performance Monitoring Integration
// ============================================================================

/**
 * Integrate Slack with performance monitoring
 * Sends alerts when performance thresholds exceeded
 */
export async function setupPerformanceMonitoringSlackIntegration() {
  const slack = new SlackIntegration();

  // Check performance metrics every 5 minutes
  setInterval(async () => {
    try {
      const metrics = {
        cpu: await getCPUUsage(),
        memory: await getMemoryUsage(),
        diskSpace: await getDiskSpace(),
        connections: await getActiveConnections(),
      };

      // CPU threshold: 80%
      if (metrics.cpu > 80) {
        await slack.sendPerformanceAlert('CPU Usage', metrics.cpu, 80, {
          current_processes: await getTopProcesses(),
          duration: 'Last 5 minutes',
        });
      }

      // Memory threshold: 85%
      if (metrics.memory > 85) {
        await slack.sendPerformanceAlert('Memory Usage', metrics.memory, 85, {
          heap_used: `${(process.memoryUsage().heapUsed / 1024 / 1024).toFixed(2)} MB`,
          heap_total: `${(process.memoryUsage().heapTotal / 1024 / 1024).toFixed(2)} MB`,
        });
      }

      // Disk space threshold: 90%
      if (metrics.diskSpace > 90) {
        await slack.sendPerformanceAlert('Disk Space', metrics.diskSpace, 90, {
          recommendation: 'Clean up old logs and backups',
          critical: 'Yes',
        });
      }

      // Connection threshold: 100
      if (metrics.connections > 100) {
        await slack.sendPerformanceAlert(
          'Active Connections',
          metrics.connections,
          100,
          {
            connection_pool: 'Approaching limit',
            recommendation: 'Scale up or optimize queries',
          }
        );
      }
    } catch (error) {
      console.error('Failed to check performance metrics:', error);
    }
  }, 5 * 60 * 1000); // Every 5 minutes
}

async function getCPUUsage(): Promise<number> {
  // Implement actual CPU usage measurement
  return Math.random() * 100;
}

async function getMemoryUsage(): Promise<number> {
  const usage = process.memoryUsage();
  return (usage.heapUsed / usage.heapTotal) * 100;
}

async function getDiskSpace(): Promise<number> {
  // Implement actual disk space check
  return Math.random() * 100;
}

async function getActiveConnections(): Promise<number> {
  // Implement actual connection count
  return Math.floor(Math.random() * 150);
}

async function getTopProcesses(): Promise<string> {
  // Implement actual process listing
  return 'node (45%), postgres (30%), redis (10%)';
}

// ============================================================================
// Example 6: Custom Alert with Thread Support
// ============================================================================

/**
 * Example of using thread support for incident tracking
 */
export class IncidentTracker {
  private slack: SlackIntegration;
  private incidentId: string;

  constructor() {
    this.slack = new SlackIntegration();
    this.incidentId = `incident-${Date.now()}`;
  }

  async reportIncident(title: string, description: string) {
    await this.slack.sendAlert({
      type: 'security',
      severity: 'high',
      title,
      description,
      threadId: this.incidentId,
      timestamp: Date.now(),
    });
  }

  async updateIncident(update: string) {
    await this.slack.sendAlert({
      type: 'security',
      severity: 'medium',
      title: 'Incident Update',
      description: update,
      threadId: this.incidentId,
      timestamp: Date.now(),
    });
  }

  async resolveIncident(resolution: string) {
    await this.slack.sendAlert({
      type: 'security',
      severity: 'info',
      title: 'Incident Resolved',
      description: resolution,
      threadId: this.incidentId,
      timestamp: Date.now(),
    });
  }
}

// ============================================================================
// Example 7: Batch Alert Processing
// ============================================================================

/**
 * Example of batching alerts to avoid rate limiting
 */
export class BatchAlertProcessor {
  private slack: SlackIntegration;
  private queue: any[] = [];
  private batchSize = 5;
  private batchInterval = 60000; // 1 minute

  constructor() {
    this.slack = new SlackIntegration();
    this.startBatchProcessor();
  }

  addAlert(alert: any) {
    this.queue.push(alert);
  }

  private startBatchProcessor() {
    setInterval(async () => {
      if (this.queue.length === 0) return;

      const batch = this.queue.splice(0, this.batchSize);

      await this.slack.sendAlert({
        type: 'system',
        severity: 'info',
        title: `Batch Alert: ${batch.length} Events`,
        description: 'Multiple events processed',
        details: {
          event_count: batch.length,
          events: batch.map((e) => e.title || e.description).join(', '),
        },
        timestamp: Date.now(),
      });
    }, this.batchInterval);
  }
}

// ============================================================================
// Example 8: Full System Integration
// ============================================================================

/**
 * Initialize all Slack integrations for AI-Shell
 */
export async function initializeAllSlackIntegrations() {
  console.log('Initializing Slack integrations...');

  // Setup all integrations
  await setupHealthMonitorSlackIntegration();
  console.log('✓ Health monitor integration ready');

  const securityMonitor = await setupSecurityAuditSlackIntegration();
  console.log('✓ Security audit integration ready');

  const queryMonitor = await setupQueryExecutionSlackIntegration();
  console.log('✓ Query execution integration ready');

  const backupMonitor = await setupBackupSlackIntegration();
  console.log('✓ Backup system integration ready');

  await setupPerformanceMonitoringSlackIntegration();
  console.log('✓ Performance monitoring integration ready');

  console.log('\n✅ All Slack integrations initialized successfully!');

  return {
    securityMonitor,
    queryMonitor,
    backupMonitor,
  };
}

// ============================================================================
// Main Entry Point
// ============================================================================

if (require.main === module) {
  initializeAllSlackIntegrations()
    .then(() => {
      console.log('\n🚀 AI-Shell Slack Integration is running...');
    })
    .catch((error) => {
      console.error('Failed to initialize Slack integrations:', error);
      process.exit(1);
    });
}
