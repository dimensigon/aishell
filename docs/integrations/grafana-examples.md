# Grafana Integration Examples

Practical examples for using the Grafana integration in various scenarios.

## Table of Contents

- [Quick Start Examples](#quick-start-examples)
- [Dashboard Creation](#dashboard-creation)
- [Custom Panels](#custom-panels)
- [Alert Configuration](#alert-configuration)
- [Automation Scripts](#automation-scripts)
- [Advanced Scenarios](#advanced-scenarios)

## Quick Start Examples

### Example 1: Basic Setup

```bash
# Step 1: Setup Grafana connection
aishell-grafana setup \
  --url http://localhost:3000 \
  --api-key eyJrIjoiYWJjZGVmZ2hpamtsbW5vcA \
  --prometheus-url http://localhost:9090

# Step 2: Deploy all dashboards
aishell-grafana deploy-dashboards

# Step 3: List deployed dashboards
aishell-grafana list
```

### Example 2: Single Dashboard Deployment

```bash
# Deploy only the performance dashboard
aishell-grafana create-dashboard performance

# Deploy only the security dashboard
aishell-grafana create-dashboard security
```

### Example 3: Dashboard Backup

```bash
# Export all dashboards
aishell-grafana list | grep UID | awk '{print $3}' | while read uid; do
  aishell-grafana export "$uid" --output "backup-${uid}.json"
done

# Import dashboard from backup
aishell-grafana import backup-overview-123.json
```

## Dashboard Creation

### Example 1: Simple Custom Dashboard

```typescript
import { DashboardBuilder, GrafanaClient } from './grafana-integration';

async function createSimpleDashboard() {
  // Initialize client
  const client = new GrafanaClient({
    url: 'http://localhost:3000',
    apiKey: process.env.GRAFANA_API_KEY!,
  });

  // Create dashboard
  const builder = new DashboardBuilder('My First Dashboard', ['custom', 'test']);

  // Add a stat panel
  builder.addStatPanel(
    'Total Requests',
    'sum(aishell_requests_total)',
    0, 0, 6, 4
  );

  // Add a graph panel
  builder.addGraphPanel(
    'Request Rate',
    [
      {
        expr: 'rate(aishell_requests_total[5m])',
        legendFormat: 'Requests/sec',
        refId: 'A',
      },
    ],
    6, 0, 18, 8
  );

  // Save dashboard
  const dashboard = builder.build();
  const result = await client.saveDashboard(dashboard);

  console.log('Dashboard created!');
  console.log(`URL: http://localhost:3000/d/${result.dashboard.uid}`);
}

createSimpleDashboard();
```

### Example 2: Multi-Variable Dashboard

```typescript
async function createMultiVariableDashboard() {
  const client = new GrafanaClient({
    url: 'http://localhost:3000',
    apiKey: process.env.GRAFANA_API_KEY!,
  });

  const builder = new DashboardBuilder('Multi-Variable Dashboard');

  // Add instance variable
  builder.addVariable({
    name: 'instance',
    type: 'query',
    datasource: 'AI-Shell-Prometheus',
    query: 'label_values(aishell_requests_total, instance)',
    refresh: 1,
    multi: false,
    includeAll: false,
  });

  // Add endpoint variable (multi-select)
  builder.addVariable({
    name: 'endpoint',
    type: 'query',
    datasource: 'AI-Shell-Prometheus',
    query: 'label_values(aishell_requests_total{instance=~"$instance"}, endpoint)',
    refresh: 1,
    multi: true,
    includeAll: true,
  });

  // Add status code variable
  builder.addVariable({
    name: 'status',
    type: 'query',
    datasource: 'AI-Shell-Prometheus',
    query: 'label_values(aishell_requests_total, status)',
    refresh: 1,
    multi: true,
    includeAll: true,
  });

  // Add panels using variables
  builder.addGraphPanel(
    'Filtered Request Rate',
    [
      {
        expr: 'sum(rate(aishell_requests_total{instance=~"$instance",endpoint=~"$endpoint",status=~"$status"}[5m])) by (endpoint)',
        legendFormat: '{{endpoint}}',
        refId: 'A',
      },
    ],
    0, 0, 24, 8
  );

  const dashboard = builder.build();
  await client.saveDashboard(dashboard);
}
```

### Example 3: Complete Application Dashboard

```typescript
async function createApplicationDashboard() {
  const builder = new DashboardBuilder('Application Monitoring', ['app', 'monitoring']);

  // Variables
  builder.addVariable({
    name: 'env',
    type: 'custom',
    datasource: 'AI-Shell-Prometheus',
    query: 'production,staging,development',
    refresh: 0,
    multi: false,
    includeAll: false,
  });

  // Row 1: Business Metrics
  builder.addStatPanel(
    'Daily Active Users',
    'count(count_over_time(aishell_user_activity{env="$env"}[24h]))',
    0, 0, 4, 4
  );

  builder.addStatPanel(
    'Total Revenue',
    'sum(aishell_revenue_total{env="$env"})',
    4, 0, 4, 4
  );

  builder.addStatPanel(
    'Conversion Rate',
    '100 * sum(aishell_conversions_total{env="$env"}) / sum(aishell_visitors_total{env="$env"})',
    8, 0, 4, 4
  );

  builder.addStatPanel(
    'Avg Session Duration',
    'avg(aishell_session_duration_seconds{env="$env"}) / 60',
    12, 0, 4, 4
  );

  // Row 2: Performance
  builder.addGraphPanel(
    'Page Load Time',
    [
      {
        expr: 'histogram_quantile(0.95, sum(rate(aishell_page_load_seconds_bucket{env="$env"}[5m])) by (le, page))',
        legendFormat: '{{page}} (p95)',
        refId: 'A',
      },
    ],
    0, 4, 12, 8
  );

  builder.addGraphPanel(
    'API Response Time',
    [
      {
        expr: 'histogram_quantile(0.95, sum(rate(aishell_api_duration_seconds_bucket{env="$env"}[5m])) by (le, endpoint))',
        legendFormat: '{{endpoint}} (p95)',
        refId: 'A',
      },
    ],
    12, 4, 12, 8
  );

  // Row 3: Errors
  builder.addGraphPanel(
    'Error Rate by Type',
    [
      {
        expr: 'sum(rate(aishell_errors_total{env="$env"}[5m])) by (type)',
        legendFormat: '{{type}}',
        refId: 'A',
      },
    ],
    0, 12, 12, 8
  );

  builder.addTablePanel(
    'Top Errors',
    [
      {
        expr: 'topk(10, sum by (message, endpoint) (increase(aishell_errors_total{env="$env"}[1h])))',
        refId: 'A',
      },
    ],
    12, 12, 12, 8
  );

  const client = new GrafanaClient({
    url: 'http://localhost:3000',
    apiKey: process.env.GRAFANA_API_KEY!,
  });

  const dashboard = builder.build();
  await client.saveDashboard(dashboard);
}
```

## Custom Panels

### Example 1: Custom Gauge Panel

```typescript
builder.addPanel({
  title: 'Custom Gauge',
  type: 'gauge',
  gridPos: { x: 0, y: 0, w: 6, h: 6 },
  targets: [
    {
      expr: 'aishell_custom_metric',
      refId: 'A',
    },
  ],
  options: {
    reduceOptions: {
      values: false,
      calcs: ['lastNotNull'],
    },
    showThresholdLabels: true,
    showThresholdMarkers: true,
  },
  fieldConfig: {
    defaults: {
      min: 0,
      max: 1000,
      thresholds: {
        mode: 'absolute',
        steps: [
          { value: 0, color: 'green' },
          { value: 500, color: 'yellow' },
          { value: 800, color: 'orange' },
          { value: 900, color: 'red' },
        ],
      },
      unit: 'ms',
      decimals: 2,
    },
  },
});
```

### Example 2: Custom Bar Chart

```typescript
builder.addPanel({
  title: 'Top Endpoints',
  type: 'barchart',
  gridPos: { x: 0, y: 0, w: 12, h: 8 },
  targets: [
    {
      expr: 'topk(10, sum by (endpoint) (rate(aishell_requests_total[5m])))',
      legendFormat: '{{endpoint}}',
      refId: 'A',
    },
  ],
  options: {
    orientation: 'horizontal',
    xTickLabelRotation: 0,
    xTickLabelSpacing: 0,
    showValue: 'auto',
    stacking: 'none',
    groupWidth: 0.7,
    barWidth: 0.97,
  },
  fieldConfig: {
    defaults: {
      color: {
        mode: 'palette-classic',
      },
    },
  },
});
```

### Example 3: Custom Pie Chart

```typescript
builder.addPanel({
  title: 'Request Distribution',
  type: 'piechart',
  gridPos: { x: 0, y: 0, w: 8, h: 8 },
  targets: [
    {
      expr: 'sum by (type) (aishell_requests_total)',
      legendFormat: '{{type}}',
      refId: 'A',
    },
  ],
  options: {
    legend: {
      displayMode: 'table',
      placement: 'right',
      values: ['value', 'percent'],
    },
    pieType: 'pie',
    tooltip: {
      mode: 'single',
    },
    displayLabels: ['name', 'percent'],
  },
});
```

## Alert Configuration

### Example 1: High Error Rate Alert

```typescript
builder.addPanel({
  title: 'Error Rate Monitor',
  type: 'graph',
  gridPos: { x: 0, y: 0, w: 12, h: 8 },
  targets: [
    {
      expr: '100 * sum(rate(aishell_requests_total{status="error"}[5m])) / sum(rate(aishell_requests_total[5m]))',
      refId: 'A',
    },
  ],
  alert: {
    name: 'High Error Rate',
    conditions: [
      {
        evaluator: {
          params: [5], // Alert if error rate > 5%
          type: 'gt',
        },
        operator: {
          type: 'and',
        },
        query: {
          params: ['A', '5m', 'now'],
        },
        reducer: {
          params: [],
          type: 'avg',
        },
        type: 'query',
      },
    ],
    frequency: '1m',
    handler: 1,
    message: 'Error rate is above 5% for the last 5 minutes',
    notifications: [],
  },
});
```

### Example 2: Memory Usage Alert

```typescript
builder.addPanel({
  title: 'Memory Usage',
  type: 'graph',
  gridPos: { x: 0, y: 0, w: 12, h: 8 },
  targets: [
    {
      expr: '100 * aishell_memory_usage_bytes / aishell_memory_total_bytes',
      refId: 'A',
    },
  ],
  alert: {
    name: 'High Memory Usage',
    conditions: [
      {
        evaluator: {
          params: [85],
          type: 'gt',
        },
        operator: {
          type: 'and',
        },
        query: {
          params: ['A', '5m', 'now'],
        },
        reducer: {
          params: [],
          type: 'max',
        },
        type: 'query',
      },
    ],
    frequency: '1m',
    handler: 1,
    message: 'Memory usage exceeded 85%',
    notifications: [],
  },
});
```

### Example 3: Response Time Alert

```typescript
builder.addPanel({
  title: 'Response Time (p95)',
  type: 'graph',
  gridPos: { x: 0, y: 0, w: 12, h: 8 },
  targets: [
    {
      expr: 'histogram_quantile(0.95, sum(rate(aishell_response_duration_seconds_bucket[5m])) by (le)) * 1000',
      refId: 'A',
    },
  ],
  alert: {
    name: 'Slow Response Time',
    conditions: [
      {
        evaluator: {
          params: [500], // Alert if p95 > 500ms
          type: 'gt',
        },
        operator: {
          type: 'and',
        },
        query: {
          params: ['A', '5m', 'now'],
        },
        reducer: {
          params: [],
          type: 'avg',
        },
        type: 'query',
      },
    ],
    frequency: '1m',
    handler: 1,
    message: 'P95 response time exceeded 500ms',
    notifications: [],
  },
});
```

## Automation Scripts

### Example 1: Nightly Dashboard Backup

```bash
#!/bin/bash
# backup-dashboards.sh

BACKUP_DIR="./grafana-backups/$(date +%Y-%m-%d)"
mkdir -p "$BACKUP_DIR"

# Get all dashboard UIDs
aishell-grafana list | grep UID | awk '{print $3}' | while read uid; do
  echo "Backing up $uid..."
  aishell-grafana export "$uid" --output "$BACKUP_DIR/${uid}.json"
done

# Compress backup
tar -czf "grafana-backup-$(date +%Y-%m-%d).tar.gz" "$BACKUP_DIR"

echo "Backup complete: grafana-backup-$(date +%Y-%m-%d).tar.gz"
```

### Example 2: Dashboard Sync Script

```typescript
// sync-dashboards.ts
import { GrafanaClient, DashboardTemplates } from './grafana-integration';
import fs from 'fs/promises';

async function syncDashboards() {
  const client = new GrafanaClient({
    url: process.env.GRAFANA_URL!,
    apiKey: process.env.GRAFANA_API_KEY!,
  });

  // Get current dashboards
  const existing = await client.searchDashboards('ai-shell');
  const existingTitles = new Set(existing.map((d) => d.title));

  // Define required dashboards
  const required = [
    { title: 'AI-Shell Overview', create: DashboardTemplates.createOverviewDashboard },
    { title: 'AI-Shell Performance', create: DashboardTemplates.createPerformanceDashboard },
    { title: 'AI-Shell Security', create: DashboardTemplates.createSecurityDashboard },
    { title: 'AI-Shell Query Analytics', create: DashboardTemplates.createQueryAnalyticsDashboard },
  ];

  // Create missing dashboards
  for (const { title, create } of required) {
    if (!existingTitles.has(title)) {
      console.log(`Creating missing dashboard: ${title}`);
      const dashboard = create();
      await client.saveDashboard(dashboard);
    } else {
      console.log(`Dashboard exists: ${title}`);
    }
  }

  console.log('Dashboard sync complete');
}

syncDashboards();
```

### Example 3: Multi-Environment Deployment

```typescript
// deploy-multi-env.ts
import { GrafanaClient, DashboardTemplates } from './grafana-integration';

const ENVIRONMENTS = [
  { name: 'production', url: 'https://grafana.prod.example.com', apiKey: process.env.PROD_API_KEY },
  { name: 'staging', url: 'https://grafana.staging.example.com', apiKey: process.env.STAGING_API_KEY },
  { name: 'development', url: 'https://grafana.dev.example.com', apiKey: process.env.DEV_API_KEY },
];

async function deployToAllEnvironments() {
  for (const env of ENVIRONMENTS) {
    console.log(`\nDeploying to ${env.name}...`);

    const client = new GrafanaClient({
      url: env.url,
      apiKey: env.apiKey!,
    });

    // Test connection
    const connected = await client.testConnection();
    if (!connected) {
      console.error(`Failed to connect to ${env.name}`);
      continue;
    }

    // Deploy dashboards
    const dashboards = [
      DashboardTemplates.createOverviewDashboard(),
      DashboardTemplates.createPerformanceDashboard(),
      DashboardTemplates.createSecurityDashboard(),
      DashboardTemplates.createQueryAnalyticsDashboard(),
    ];

    for (const dashboard of dashboards) {
      try {
        await client.saveDashboard(dashboard);
        console.log(`  ✓ Deployed: ${dashboard.title}`);
      } catch (error) {
        console.error(`  ✗ Failed: ${dashboard.title}`, error);
      }
    }
  }

  console.log('\nDeployment complete');
}

deployToAllEnvironments();
```

## Advanced Scenarios

### Example 1: Dynamic Panel Generation

```typescript
async function createDynamicDashboard(services: string[]) {
  const builder = new DashboardBuilder('Dynamic Service Dashboard');

  let y = 0;
  for (const service of services) {
    // Add stat panel for each service
    builder.addStatPanel(
      `${service} - Requests`,
      `sum(aishell_requests_total{service="${service}"})`,
      0,
      y,
      6,
      4
    );

    builder.addGraphPanel(
      `${service} - Request Rate`,
      [
        {
          expr: `rate(aishell_requests_total{service="${service}"}[5m])`,
          legendFormat: service,
          refId: 'A',
        },
      ],
      6,
      y,
      18,
      8
    );

    y += 8;
  }

  const client = new GrafanaClient({
    url: 'http://localhost:3000',
    apiKey: process.env.GRAFANA_API_KEY!,
  });

  const dashboard = builder.build();
  await client.saveDashboard(dashboard);
}

// Usage
createDynamicDashboard(['api', 'worker', 'scheduler', 'cache']);
```

### Example 2: Template-Based Dashboards

```typescript
interface DashboardTemplate {
  title: string;
  rows: Array<{
    title: string;
    panels: Array<{
      type: 'stat' | 'graph' | 'table';
      title: string;
      query: string;
    }>;
  }>;
}

async function createFromTemplate(template: DashboardTemplate) {
  const builder = new DashboardBuilder(template.title);

  let y = 0;
  for (const row of template.rows) {
    let x = 0;
    for (const panel of row.panels) {
      const width = 24 / row.panels.length;

      if (panel.type === 'stat') {
        builder.addStatPanel(panel.title, panel.query, x, y, width, 4);
      } else if (panel.type === 'graph') {
        builder.addGraphPanel(
          panel.title,
          [{ expr: panel.query, refId: 'A' }],
          x,
          y,
          width,
          8
        );
      } else if (panel.type === 'table') {
        builder.addTablePanel(
          panel.title,
          [{ expr: panel.query, refId: 'A' }],
          x,
          y,
          width,
          8
        );
      }

      x += width;
    }
    y += 8;
  }

  const client = new GrafanaClient({
    url: 'http://localhost:3000',
    apiKey: process.env.GRAFANA_API_KEY!,
  });

  const dashboard = builder.build();
  await client.saveDashboard(dashboard);
}

// Usage
const template: DashboardTemplate = {
  title: 'Template Dashboard',
  rows: [
    {
      title: 'Metrics Row',
      panels: [
        { type: 'stat', title: 'Total', query: 'sum(metric_total)' },
        { type: 'stat', title: 'Rate', query: 'rate(metric_total[5m])' },
      ],
    },
    {
      title: 'Graphs Row',
      panels: [
        { type: 'graph', title: 'Trend', query: 'metric_total' },
      ],
    },
  ],
};

createFromTemplate(template);
```

### Example 3: A/B Testing Dashboard

```typescript
async function createABTestingDashboard() {
  const builder = new DashboardBuilder('A/B Testing Results', ['ab-testing', 'experiments']);

  // Variable for experiment selection
  builder.addVariable({
    name: 'experiment',
    type: 'query',
    datasource: 'AI-Shell-Prometheus',
    query: 'label_values(aishell_experiment_metric, experiment_id)',
    refresh: 1,
    multi: false,
    includeAll: false,
  });

  // Conversion Rate Comparison
  builder.addGraphPanel(
    'Conversion Rate: Control vs Treatment',
    [
      {
        expr: '100 * sum(rate(aishell_conversions_total{experiment_id="$experiment",variant="control"}[5m])) / sum(rate(aishell_visitors_total{experiment_id="$experiment",variant="control"}[5m]))',
        legendFormat: 'Control',
        refId: 'A',
      },
      {
        expr: '100 * sum(rate(aishell_conversions_total{experiment_id="$experiment",variant="treatment"}[5m])) / sum(rate(aishell_visitors_total{experiment_id="$experiment",variant="treatment"}[5m]))',
        legendFormat: 'Treatment',
        refId: 'B',
      },
    ],
    0,
    0,
    12,
    8
  );

  // Statistical Significance
  builder.addStatPanel(
    'Confidence Level',
    'aishell_ab_test_confidence{experiment_id="$experiment"}',
    12,
    0,
    6,
    4
  );

  builder.addStatPanel(
    'P-Value',
    'aishell_ab_test_pvalue{experiment_id="$experiment"}',
    18,
    0,
    6,
    4
  );

  // Sample Size
  builder.addGraphPanel(
    'Sample Size Over Time',
    [
      {
        expr: 'sum(aishell_ab_test_samples{experiment_id="$experiment"}) by (variant)',
        legendFormat: '{{variant}}',
        refId: 'A',
      },
    ],
    0,
    8,
    12,
    8
  );

  // Results Table
  builder.addTablePanel(
    'Detailed Results',
    [
      {
        expr: 'aishell_ab_test_results{experiment_id="$experiment"}',
        refId: 'A',
      },
    ],
    12,
    8,
    12,
    8
  );

  const client = new GrafanaClient({
    url: 'http://localhost:3000',
    apiKey: process.env.GRAFANA_API_KEY!,
  });

  const dashboard = builder.build();
  await client.saveDashboard(dashboard);
}
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Deploy Grafana Dashboards

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm install

      - name: Configure Grafana
        run: |
          node -e "
            const { GrafanaIntegrationCLI } = require('./dist/cli/grafana-integration');
            const cli = new GrafanaIntegrationCLI();
            cli.setup('${{ secrets.GRAFANA_URL }}', '${{ secrets.GRAFANA_API_KEY }}');
          "

      - name: Deploy dashboards
        run: |
          node -e "
            const { GrafanaIntegrationCLI } = require('./dist/cli/grafana-integration');
            const cli = new GrafanaIntegrationCLI();
            cli.deployDashboards();
          "

      - name: Verify deployment
        run: |
          node -e "
            const { GrafanaIntegrationCLI } = require('./dist/cli/grafana-integration');
            const cli = new GrafanaIntegrationCLI();
            cli.listDashboards();
          "
```

## Best Practices

1. **Version Control**: Store dashboard JSON in Git for change tracking
2. **Automation**: Use CI/CD for consistent deployments
3. **Testing**: Test dashboards in staging before production
4. **Documentation**: Document custom metrics and panels
5. **Monitoring**: Set up alerts for dashboard availability
6. **Backup**: Regular automated backups of dashboards
7. **Permissions**: Use least-privilege API keys
8. **Variables**: Use dashboard variables for flexibility
9. **Naming**: Consistent naming conventions
10. **Organization**: Group related dashboards in folders
