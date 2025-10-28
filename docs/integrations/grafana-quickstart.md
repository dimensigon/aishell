# Grafana Integration Quick Start Guide

Get up and running with Grafana dashboards for AI-Shell in 5 minutes.

## Prerequisites

- Grafana 8.0+ (Docker or standalone)
- Prometheus with AI-Shell metrics
- Node.js 18+
- AI-Shell installed

## Step 1: Start Grafana (Optional)

If you don't have Grafana running:

```bash
# Using Docker
docker run -d \
  -p 3000:3000 \
  --name=grafana \
  grafana/grafana-oss

# Access Grafana at http://localhost:3000
# Default credentials: admin/admin
```

## Step 2: Generate API Key

1. Open Grafana: http://localhost:3000
2. Login (default: admin/admin)
3. Navigate to: Configuration → API Keys (or `/org/apikeys`)
4. Click "Add API Key"
5. Configure:
   - **Name**: `AI-Shell Integration`
   - **Role**: `Editor`
   - **Time to live**: No expiration
6. Click "Add"
7. **Copy the key immediately** (you won't see it again!)

## Step 3: Configure AI-Shell Grafana Integration

```bash
# One-line setup
aishell-grafana setup \
  --url http://localhost:3000 \
  --api-key YOUR_API_KEY_HERE \
  --prometheus-url http://localhost:9090

# You should see:
# ✓ Connected to Grafana
# ✓ Prometheus data source configured
# ✓ Configuration saved
```

## Step 4: Deploy Dashboards

```bash
# Deploy all dashboards at once
aishell-grafana deploy-dashboards

# You should see:
# Deploying AI-Shell dashboards...
# ✓ Deployed Overview dashboard
# ✓ Deployed Performance dashboard
# ✓ Deployed Security dashboard
# ✓ Deployed Query Analytics dashboard
# ✓ All dashboards deployed
```

## Step 5: View Dashboards

Open Grafana and navigate to:
- Dashboards → Browse → Search for "AI-Shell"
- Or click the URLs shown in the deploy output

## Available Dashboards

### 1. Overview Dashboard (12 panels)
**Purpose**: High-level system health monitoring

**Key Metrics**:
- Total Requests
- Active Sessions
- Success Rate
- Response Time

**URL**: http://localhost:3000/d/aishell-overview

### 2. Performance Dashboard (15 panels)
**Purpose**: Deep dive into performance metrics

**Key Metrics**:
- Response Time Percentiles (p50, p90, p95, p99)
- Request Throughput
- Database Query Performance
- Cache Hit Rate
- Resource Utilization

**URL**: http://localhost:3000/d/aishell-performance

### 3. Security Dashboard (10 panels)
**Purpose**: Monitor security events and threats

**Key Metrics**:
- Failed Authentication Attempts
- Blocked IPs
- Security Alerts
- Suspicious Activity

**URL**: http://localhost:3000/d/aishell-security

### 4. Query Analytics Dashboard (14 panels)
**Purpose**: Analyze AI query performance

**Key Metrics**:
- Query Rate by Model
- Query Duration
- Token Usage
- Success Rate
- Context Window Utilization

**URL**: http://localhost:3000/d/aishell-query-analytics

## Common Commands

```bash
# Setup connection
aishell-grafana setup --url <url> --api-key <key>

# Deploy all dashboards
aishell-grafana deploy-dashboards

# Create specific dashboard
aishell-grafana create-dashboard overview
aishell-grafana create-dashboard performance
aishell-grafana create-dashboard security
aishell-grafana create-dashboard query-analytics

# List dashboards
aishell-grafana list

# Export dashboard
aishell-grafana export <dashboard-uid> --output backup.json

# Import dashboard
aishell-grafana import backup.json
```

## Using NPM Scripts

```bash
# Setup Grafana (requires interactive input)
npm run grafana:setup

# Deploy all dashboards
npm run grafana:deploy

# Run custom Grafana command
npm run grafana -- create-dashboard performance
```

## Troubleshooting

### Issue: "Cannot connect to Grafana"

**Solution**:
1. Check Grafana is running: `curl http://localhost:3000/api/health`
2. Verify URL format includes `http://` or `https://`
3. Check firewall settings

### Issue: "No data in dashboards"

**Solution**:
1. Verify Prometheus is running: `curl http://localhost:9090/api/v1/query?query=up`
2. Check Prometheus is scraping AI-Shell metrics
3. Verify AI-Shell metrics are exposed on the correct port
4. Check time range in Grafana (top-right corner)

### Issue: "API key rejected"

**Solution**:
1. Verify API key has not expired
2. Ensure API key has `Editor` role
3. Check you copied the full API key
4. Generate a new API key if needed

### Issue: "Dashboard import fails"

**Solution**:
1. Ensure data source exists before importing
2. Check JSON file is valid
3. Verify Grafana version compatibility
4. Try creating data source manually first

## Next Steps

1. **Customize Dashboards**: Edit panels to fit your needs
2. **Set Up Alerts**: Configure alert rules for critical metrics
3. **Add Variables**: Create custom dashboard variables
4. **Share Dashboards**: Export and share with your team
5. **Automate**: Set up CI/CD for dashboard deployment

## Configuration File

Configuration is stored in `~/.aishell-grafana.json`:

```json
{
  "url": "http://localhost:3000",
  "apiKey": "eyJrIjoiXXXXXXXXXXXXXXXXXXXXXXXX",
  "organizationId": 1,
  "timeout": 30000
}
```

## Environment Variables

Override configuration:

```bash
export GRAFANA_URL="http://localhost:3000"
export GRAFANA_API_KEY="your-api-key"
export PROMETHEUS_URL="http://localhost:9090"

# Then run commands without --url and --api-key flags
aishell-grafana deploy-dashboards
```

## Dashboard Features

### Variables (Filters)
All dashboards include variables for filtering:
- **instance**: Filter by AI-Shell instance
- **endpoint**: Filter by API endpoint (Performance dashboard)
- **model**: Filter by AI model (Query Analytics dashboard)

### Time Range
- Default: Last 6 hours
- Customizable: Click time picker in top-right corner
- Auto-refresh: 30 seconds (configurable)

### Panel Interactions
- **Click legend**: Toggle series visibility
- **Hover**: Show detailed values
- **Drag**: Zoom into time range
- **Double-click**: Reset zoom

## Production Checklist

- [ ] Grafana secured with HTTPS
- [ ] Strong admin password set
- [ ] API key with minimal permissions
- [ ] Prometheus endpoint secured
- [ ] Dashboard backups configured
- [ ] Alert notifications configured
- [ ] Monitoring for Grafana itself
- [ ] Regular API key rotation
- [ ] Dashboard change tracking (Git)
- [ ] Team access permissions configured

## Resources

- **Full Documentation**: [docs/integrations/grafana.md](./grafana.md)
- **Examples**: [docs/integrations/grafana-examples.md](./grafana-examples.md)
- **Grafana Documentation**: https://grafana.com/docs/
- **Prometheus Documentation**: https://prometheus.io/docs/

## Support

Having issues? Check:
1. [Troubleshooting section](#troubleshooting)
2. [Full documentation](./grafana.md#troubleshooting)
3. Open an issue on GitHub

---

**You're all set!** Your Grafana dashboards are now monitoring AI-Shell in real-time. 🎉
