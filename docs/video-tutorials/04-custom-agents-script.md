# AI-Shell Custom Agents - Video Tutorial Script (20 minutes)

**Target Duration**: 20:00
**Audience**: Advanced developers, DevOps engineers
**Prerequisites**: AI-Shell installed, Python knowledge, agent concepts

---

## Scene 1: Introduction (0:00 - 1:15)

### Screen: Title Card with Agent Network Animation
**Voice Over**:
> "Welcome to Custom Agents in AI-Shell. Agents are autonomous workers that can handle complex database tasks, automation workflows, and intelligent decision-making. In 20 minutes, you'll build your first custom agent and deploy it to production."

### Screen Capture Notes:
- Show network of agents communicating
- Display agent types: Monitors, Analyzers, Optimizers, Migrations
- Animated code-to-agent transformation

**Timestamp**: 0:00 - 1:15

---

## Scene 2: Agent Architecture (1:15 - 3:30)

### Screen: Architecture Diagram
**Voice Over**:
> "Let's understand how agents work in AI-Shell."

### Display Architecture:
```
┌─────────────────────────────────────────┐
│         AI-Shell Core                   │
│  ┌──────────────────────────────────┐   │
│  │     Agent Runtime Engine         │   │
│  │  ┌────────────┬───────────────┐  │   │
│  │  │ Scheduler  │ Message Queue │  │   │
│  │  └────────────┴───────────────┘  │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
           │              │
    ┌──────┴──────┐  ┌───┴────────┐
    │   Custom    │  │  Built-in  │
    │   Agents    │  │  Agents    │
    └─────────────┘  └────────────┘
         │                  │
    ┌────┴─────┐      ┌────┴─────┐
    │ Database │      │    AI    │
    │ Operations│     │  Models  │
    └──────────┘      └──────────┘
```

### Demo Code - Agent Lifecycle:
```python
# agents/my_agent.py
from ai_shell.agents import BaseAgent, AgentConfig

class MyAgent(BaseAgent):
    """Custom agent lifecycle"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        # 1. Initialize: Setup resources

    async def on_start(self):
        # 2. Start: Called when agent begins
        self.logger.info("Agent starting...")

    async def execute(self, task):
        # 3. Execute: Main logic
        return await self.process_task(task)

    async def on_stop(self):
        # 4. Stop: Cleanup resources
        self.logger.info("Agent stopping...")
```

**Voice Over**:
> "Every agent follows this lifecycle: initialize, start, execute, and stop. Let's build a real agent."

**Timestamp**: 1:15 - 3:30

---

## Scene 3: Building Your First Agent (3:30 - 7:00)

### Screen: Code Editor
**Voice Over**:
> "We'll create a Query Optimizer Agent that monitors slow queries and suggests improvements."

### Demo Code - Agent Implementation:
```python
# agents/query_optimizer.py
from ai_shell.agents import BaseAgent, AgentConfig, trigger
from ai_shell.database import QueryAnalyzer
from ai_shell.ai import LLMClient
from typing import Dict, List
import asyncio

class QueryOptimizerAgent(BaseAgent):
    """
    Monitors database queries and provides optimization suggestions.

    Features:
    - Real-time query monitoring
    - Performance analysis
    - AI-powered optimization
    - Automatic index suggestions
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.analyzer = QueryAnalyzer()
        self.llm = LLMClient(model="gpt-4")
        self.slow_query_threshold = config.get("threshold_ms", 1000)
        self.check_interval = config.get("interval_seconds", 60)

    async def on_start(self):
        """Initialize monitoring"""
        self.logger.info(f"Starting query optimizer")
        self.logger.info(f"Threshold: {self.slow_query_threshold}ms")
        await self.start_monitoring()

    @trigger(event="query_completed")
    async def on_query_completed(self, event: Dict):
        """Triggered when any query completes"""
        duration_ms = event.get("duration_ms")

        if duration_ms > self.slow_query_threshold:
            await self.analyze_slow_query(event)

    async def analyze_slow_query(self, query_data: Dict):
        """Analyze a slow query and suggest optimizations"""
        query = query_data["sql"]
        duration = query_data["duration_ms"]

        self.logger.warning(f"Slow query detected: {duration}ms")

        # 1. Get execution plan
        explain_plan = await self.analyzer.explain(query)

        # 2. Identify issues
        issues = await self.analyzer.identify_issues(explain_plan)

        # 3. Generate AI suggestions
        prompt = f"""
        Analyze this slow query and suggest optimizations:

        Query: {query}
        Duration: {duration}ms
        Execution Plan: {explain_plan}
        Identified Issues: {issues}

        Provide specific, actionable recommendations.
        """

        suggestions = await self.llm.complete(prompt)

        # 4. Store results
        await self.store_analysis({
            "query": query,
            "duration": duration,
            "issues": issues,
            "suggestions": suggestions,
            "timestamp": query_data["timestamp"]
        })

        # 5. Notify if critical
        if duration > self.slow_query_threshold * 5:
            await self.send_alert(
                severity="high",
                message=f"Critical slow query: {duration}ms",
                details=suggestions
            )

    @trigger(schedule="*/5 * * * *")  # Every 5 minutes
    async def generate_report(self):
        """Generate periodic optimization report"""
        recent_analyses = await self.get_recent_analyses(limit=20)

        if not recent_analyses:
            return

        # Aggregate patterns
        common_issues = self.aggregate_issues(recent_analyses)
        high_impact_optimizations = self.prioritize_suggestions(
            recent_analyses
        )

        report = {
            "period": "last_5_minutes",
            "slow_queries": len(recent_analyses),
            "common_issues": common_issues,
            "recommendations": high_impact_optimizations
        }

        await self.publish_report(report)
        self.logger.info(f"Generated report: {len(recent_analyses)} slow queries")

    async def store_analysis(self, data: Dict):
        """Store analysis in database"""
        await self.db.execute("""
            INSERT INTO query_analyses
            (query, duration, issues, suggestions, analyzed_at)
            VALUES ($1, $2, $3, $4, $5)
        """, data["query"], data["duration"],
            data["issues"], data["suggestions"],
            data["timestamp"])

    async def get_recent_analyses(self, limit: int) -> List[Dict]:
        """Retrieve recent analyses"""
        return await self.db.fetch("""
            SELECT * FROM query_analyses
            WHERE analyzed_at > NOW() - INTERVAL '5 minutes'
            ORDER BY duration DESC
            LIMIT $1
        """, limit)

    def aggregate_issues(self, analyses: List[Dict]) -> Dict:
        """Find common patterns in issues"""
        issue_counts = {}
        for analysis in analyses:
            for issue in analysis["issues"]:
                issue_type = issue["type"]
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1

        return dict(sorted(
            issue_counts.items(),
            key=lambda x: x[1],
            reverse=True
        ))

    def prioritize_suggestions(self, analyses: List[Dict]) -> List[Dict]:
        """Prioritize optimizations by impact"""
        all_suggestions = []

        for analysis in analyses:
            for suggestion in analysis["suggestions"]:
                impact_score = self.calculate_impact(
                    analysis["duration"],
                    suggestion
                )
                all_suggestions.append({
                    "suggestion": suggestion,
                    "impact_score": impact_score,
                    "query": analysis["query"][:100]
                })

        return sorted(
            all_suggestions,
            key=lambda x: x["impact_score"],
            reverse=True
        )[:10]

    def calculate_impact(self, duration: float, suggestion: Dict) -> float:
        """Calculate potential impact of optimization"""
        # Simple scoring: duration * frequency * estimated_improvement
        return duration * suggestion.get("estimated_improvement", 0.5)
```

**Voice Over**:
> "This agent monitors queries in real-time, uses AI to analyze performance, and provides actionable recommendations. Notice the decorators: @trigger for events and schedules."

### Screen Capture Notes:
- Highlight key methods
- Show trigger decorators
- Display async/await patterns
- Emphasize AI integration

**Timestamp**: 3:30 - 7:00

---

## Scene 4: Agent Configuration (7:00 - 9:15)

### Screen: Configuration Files
**Voice Over**:
> "Now let's configure and deploy our agent."

### Demo Code - Configuration:
```yaml
# config/agents/query_optimizer.yaml
name: query_optimizer
description: "Monitors and optimizes slow database queries"
version: 1.0.0

# Agent settings
enabled: true
instances: 1  # Number of agent instances

# Agent-specific configuration
config:
  threshold_ms: 1000
  interval_seconds: 60
  auto_apply_optimizations: false
  notification_channels:
    - email
    - slack

# Database connections
databases:
  - name: production
    connection_string: "${PROD_DB_URL}"
    role: read_only
    pool_size: 5

# AI model configuration
ai:
  provider: openai
  model: gpt-4
  temperature: 0.2
  max_tokens: 2000

# Triggers
triggers:
  - type: event
    event: query_completed
    enabled: true

  - type: schedule
    schedule: "*/5 * * * *"  # Every 5 minutes
    enabled: true

# Resource limits
resources:
  max_memory_mb: 512
  max_cpu_percent: 50
  max_concurrent_tasks: 10

# Monitoring
monitoring:
  metrics_enabled: true
  log_level: INFO
  performance_tracking: true

# Alerts
alerts:
  - name: high_slow_query_rate
    condition: "slow_queries_per_minute > 10"
    severity: high
    channels: [email, slack]

  - name: agent_error_rate
    condition: "error_rate > 0.05"
    severity: critical
    channels: [pagerduty]
```

### Demo Code - Registration:
```bash
# Register the agent
ai> agent register ./agents/query_optimizer.py \
    --config ./config/agents/query_optimizer.yaml

[AI] Registering custom agent...

Validating agent code... ✓
Validating configuration... ✓
Checking dependencies... ✓
Running safety checks... ✓

Agent registered successfully!

Agent: query_optimizer
Type: Custom
Version: 1.0.0
Status: Registered (not started)

To start: ai> agent start query_optimizer
```

**Voice Over**:
> "Configuration is declarative - define behavior, triggers, resources, and alerts in YAML."

### Screen Capture Notes:
- Show YAML syntax highlighting
- Highlight important config sections
- Display registration process
- Show validation checks

**Timestamp**: 7:00 - 9:15

---

## Scene 5: Testing Agents (9:15 - 11:30)

### Screen: Terminal Split View
**Voice Over**:
> "Before production, let's test our agent thoroughly."

### Demo Code - Local Testing:
```bash
# Start agent in development mode
ai> agent start query_optimizer --mode=development

[AI] Starting agent in development mode...

✓ Loading configuration
✓ Initializing agent
✓ Connecting to databases
✓ Starting monitoring

Agent: query_optimizer
Status: Running
Uptime: 00:00:03
Tasks processed: 0

Development mode features:
  • Verbose logging
  • No external notifications
  • Safe mode (no auto-apply)
  • Hot reload enabled

# Trigger a slow query to test
ai> query "SELECT * FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.created_at > '2024-01-01'" --force-slow

Executing query... (3.2s)

[Agent: query_optimizer] Slow query detected!
[Agent: query_optimizer] Duration: 3,200ms
[Agent: query_optimizer] Analyzing...
[Agent: query_optimizer] Analysis complete:

Issues Found:
1. Missing index on orders.created_at (HIGH)
2. SELECT * fetches unnecessary columns (MEDIUM)
3. No LIMIT clause (MEDIUM)

AI Suggestions:
1. Create index: CREATE INDEX idx_orders_created_at ON orders(created_at);
   Estimated improvement: 85% faster
   Impact score: 8.5/10

2. Rewrite query to fetch specific columns:
   SELECT o.id, o.total, c.name FROM orders o...
   Estimated improvement: 30% faster
   Impact score: 3.2/10

3. Add LIMIT if pagination is possible:
   ... LIMIT 1000;
   Estimated improvement: 50% faster (for large result sets)
   Impact score: 5.0/10

[Agent: query_optimizer] Stored analysis in database
[Agent: query_optimizer] No alert sent (below critical threshold)

# Check agent status
ai> agent status query_optimizer

Agent: query_optimizer
Status: Running
Uptime: 00:02:15
Tasks processed: 1
Success rate: 100%
Average response time: 2.1s

Recent Activity:
  [00:01:45] Analyzed slow query (3,200ms)
  [00:00:30] Started monitoring
  [00:00:00] Agent initialized

Metrics:
  Queries analyzed: 1
  Optimizations suggested: 3
  High-impact suggestions: 1
  Alerts sent: 0
```

### Demo Code - Unit Testing:
```python
# tests/test_query_optimizer.py
import pytest
from agents.query_optimizer import QueryOptimizerAgent
from ai_shell.testing import AgentTestCase, mock_query

class TestQueryOptimizer(AgentTestCase):
    """Test suite for QueryOptimizerAgent"""

    async def setup_method(self):
        """Setup test agent"""
        self.agent = await self.create_agent(
            QueryOptimizerAgent,
            config={"threshold_ms": 1000}
        )

    @pytest.mark.asyncio
    async def test_slow_query_detection(self):
        """Test that slow queries are detected"""
        # Simulate slow query event
        event = {
            "sql": "SELECT * FROM users",
            "duration_ms": 2000,
            "timestamp": "2025-10-11T10:00:00Z"
        }

        await self.agent.on_query_completed(event)

        # Verify analysis was performed
        analyses = await self.agent.get_recent_analyses(limit=1)
        assert len(analyses) == 1
        assert analyses[0]["duration"] == 2000

    @pytest.mark.asyncio
    async def test_fast_query_ignored(self):
        """Test that fast queries are ignored"""
        event = {
            "sql": "SELECT * FROM users WHERE id = 1",
            "duration_ms": 50,
            "timestamp": "2025-10-11T10:00:00Z"
        }

        await self.agent.on_query_completed(event)

        # Verify no analysis was performed
        analyses = await self.agent.get_recent_analyses(limit=1)
        assert len(analyses) == 0

    @pytest.mark.asyncio
    async def test_critical_alert(self):
        """Test that critical slow queries trigger alerts"""
        event = {
            "sql": "SELECT * FROM huge_table",
            "duration_ms": 10000,  # 10 seconds
            "timestamp": "2025-10-11T10:00:00Z"
        }

        with self.mock_alert() as alert_mock:
            await self.agent.on_query_completed(event)

            # Verify alert was sent
            alert_mock.assert_called_once()
            assert alert_mock.call_args["severity"] == "high"

    @pytest.mark.asyncio
    async def test_report_generation(self):
        """Test periodic report generation"""
        # Create some test data
        for i in range(5):
            await self.agent.store_analysis({
                "query": f"SELECT * FROM table_{i}",
                "duration": 2000 + (i * 100),
                "issues": [{"type": "missing_index"}],
                "suggestions": [{"type": "add_index", "estimated_improvement": 0.8}],
                "timestamp": "2025-10-11T10:00:00Z"
            })

        # Generate report
        await self.agent.generate_report()

        # Verify report was created
        report = await self.agent.get_latest_report()
        assert report["slow_queries"] == 5
        assert "missing_index" in report["common_issues"]

# Run tests
# pytest tests/test_query_optimizer.py -v
```

**Voice Over**:
> "Comprehensive testing ensures your agent behaves correctly in all scenarios."

### Screen Capture Notes:
- Show live agent output
- Display test execution
- Highlight assertions
- Show code coverage

**Timestamp**: 9:15 - 11:30

---

## Scene 6: Deployment & Monitoring (11:30 - 14:00)

### Screen: Production Dashboard
**Voice Over**:
> "Let's deploy to production and monitor our agent."

### Demo Code - Production Deployment:
```bash
# Deploy to production
ai> agent deploy query_optimizer --environment=production

[AI] Deploying agent to production...

Pre-deployment checks:
  ✓ All tests passing
  ✓ Configuration validated
  ✓ Database connections verified
  ✓ Resource limits acceptable
  ✓ Monitoring configured
  ✓ Alerts configured

Deployment steps:
  [1/5] Building agent package... ✓
  [2/5] Uploading to production... ✓
  [3/5] Installing dependencies... ✓
  [4/5] Starting agent instances... ✓
  [5/5] Health check... ✓

Deployment successful!

Agent: query_optimizer
Environment: production
Instances: 1 (running)
Endpoint: https://agents.ai-shell.io/query_optimizer
Dashboard: https://dashboard.ai-shell.io/agents/query_optimizer

# Monitor agent in real-time
ai> agent monitor query_optimizer --follow

[10:30:15] Agent started successfully
[10:30:16] Connected to production database
[10:30:16] Monitoring initialized
[10:30:45] Slow query detected (2,340ms)
[10:30:47] Analysis complete: 2 issues, 3 suggestions
[10:31:15] Report generated: 1 slow query in last 5 minutes
[10:35:15] Report generated: 5 slow queries in last 5 minutes
[10:35:16] Alert sent: High slow query rate detected
[10:40:15] Report generated: 3 slow queries in last 5 minutes
...

# Check metrics
ai> agent metrics query_optimizer --period=1h

Agent Metrics: query_optimizer (Last 1 hour)
═══════════════════════════════════════════════

Performance:
  Tasks processed: 127
  Success rate: 99.2% (126/127)
  Failed tasks: 1
  Average response time: 1.8s
  95th percentile: 3.2s

Business Metrics:
  Slow queries detected: 23
  Optimizations suggested: 67
  High-impact suggestions: 12
  Alerts triggered: 2

Resource Usage:
  CPU: 12% (avg), 45% (peak)
  Memory: 234 MB (avg), 387 MB (peak)
  Network: 2.3 MB sent, 15.6 MB received

Database Operations:
  Queries executed: 145
  Average query time: 45ms
  Connection pool usage: 60%

Errors:
  Total: 1
  Last error: "Timeout connecting to AI model" (10:45:23)
  Error rate: 0.8%
```

### Demo Code - Production Dashboard:
```bash
# Open web dashboard
ai> agent dashboard query_optimizer

Opening dashboard at: https://dashboard.ai-shell.io/agents/query_optimizer

[Browser opens showing real-time dashboard]

Dashboard Features:
  📊 Real-time metrics and graphs
  📋 Recent activity log
  🔔 Alert history
  📈 Performance trends
  🔍 Query analysis details
  ⚙️ Configuration management
  🔄 Agent control panel
```

**Voice Over**:
> "Production monitoring gives you complete visibility into agent performance and health."

### Screen Capture Notes:
- Show deployment progress
- Display real-time monitoring
- Highlight metrics dashboard
- Show web UI

**Timestamp**: 11:30 - 14:00

---

## Scene 7: Advanced Agent Patterns (14:00 - 17:00)

### Screen: Code Editor with Multiple Files
**Voice Over**:
> "Let's explore advanced patterns for building powerful agents."

### Pattern 1: Multi-Agent Coordination
```python
# agents/coordinator.py
from ai_shell.agents import BaseAgent, AgentCoordinator

class MigrationCoordinator(AgentCoordinator):
    """Coordinates multiple agents for complex migrations"""

    async def execute_migration(self, source_db, target_db):
        # Spawn multiple agents
        schema_agent = await self.spawn_agent("schema_migrator")
        data_agent = await self.spawn_agent("data_migrator")
        validator_agent = await self.spawn_agent("migration_validator")

        # Execute in sequence with coordination
        schema_result = await schema_agent.migrate_schema(
            source_db, target_db
        )

        if schema_result.success:
            # Data migration can run in parallel batches
            data_tasks = []
            for table in schema_result.tables:
                task = data_agent.migrate_table(table, source_db, target_db)
                data_tasks.append(task)

            data_results = await self.execute_parallel(data_tasks, max_workers=5)

            # Validation
            validation_result = await validator_agent.validate_migration(
                source_db, target_db, schema_result, data_results
            )

            return validation_result
```

### Pattern 2: Stateful Agents
```python
# agents/stateful_monitor.py
from ai_shell.agents import StatefulAgent

class DatabaseHealthMonitor(StatefulAgent):
    """Maintains state across executions"""

    async def execute(self):
        # Load previous state
        previous_metrics = await self.load_state("metrics")

        # Collect current metrics
        current_metrics = await self.collect_metrics()

        # Compare with historical data
        trends = self.analyze_trends(previous_metrics, current_metrics)

        # Detect anomalies
        anomalies = self.detect_anomalies(trends)

        # Save state for next execution
        await self.save_state("metrics", current_metrics)
        await self.save_state("trends", trends)

        if anomalies:
            await self.send_alert(anomalies)

    def detect_anomalies(self, trends):
        """Use statistical methods and ML to detect anomalies"""
        anomalies = []

        # Z-score analysis
        for metric, values in trends.items():
            z_score = self.calculate_z_score(values)
            if abs(z_score) > 3:
                anomalies.append({
                    "metric": metric,
                    "z_score": z_score,
                    "severity": "high" if abs(z_score) > 4 else "medium"
                })

        return anomalies
```

### Pattern 3: AI-Powered Decision Making
```python
# agents/intelligent_optimizer.py
from ai_shell.agents import AIAgent

class IntelligentOptimizer(AIAgent):
    """Uses AI for complex decision making"""

    async def optimize_database(self):
        # Gather context
        context = await self.gather_context()

        # Use AI to analyze and decide
        decision = await self.ai_decide(
            prompt=f"""
            Analyze this database context and provide optimization strategy:

            Context: {context}

            Consider:
            1. Current workload patterns
            2. Resource constraints
            3. Business priorities
            4. Risk tolerance

            Provide specific, actionable recommendations with reasoning.
            """,
            schema={
                "type": "object",
                "properties": {
                    "strategy": {"type": "string"},
                    "actions": {"type": "array"},
                    "reasoning": {"type": "string"},
                    "risk_level": {"type": "string"},
                    "estimated_impact": {"type": "object"}
                }
            }
        )

        # Execute recommended actions
        results = await self.execute_actions(decision.actions)

        # Learn from outcomes
        await self.learn_from_results(decision, results)

        return results

    async def gather_context(self):
        """Gather comprehensive context for AI decision"""
        return {
            "workload": await self.analyze_workload(),
            "resources": await self.get_resource_usage(),
            "history": await self.get_optimization_history(),
            "constraints": await self.get_constraints(),
            "business_context": await self.get_business_metrics()
        }
```

### Pattern 4: Event-Driven Agents
```python
# agents/event_driven.py
from ai_shell.agents import BaseAgent, trigger

class EventDrivenAgent(BaseAgent):
    """Responds to various database events"""

    @trigger(event="schema_change")
    async def on_schema_change(self, event):
        """React to schema modifications"""
        table = event["table"]
        change_type = event["type"]

        await self.analyze_impact(table, change_type)
        await self.update_documentation(table)
        await self.notify_stakeholders(event)

    @trigger(event="high_cpu_usage", condition="cpu > 80")
    async def on_high_cpu(self, event):
        """Auto-scale or optimize on high CPU"""
        # Identify expensive queries
        expensive_queries = await self.find_expensive_queries()

        # Try to optimize automatically
        for query in expensive_queries[:3]:
            await self.auto_optimize(query)

        # If still high, alert and scale
        if await self.check_cpu() > 80:
            await self.send_alert("sustained_high_cpu")
            await self.auto_scale_resources()

    @trigger(event="backup_completed")
    async def on_backup_completed(self, event):
        """Verify backup integrity"""
        backup_id = event["backup_id"]

        # Verify backup
        is_valid = await self.verify_backup(backup_id)

        if is_valid:
            await self.update_backup_catalog(backup_id)
        else:
            await self.send_critical_alert(
                f"Backup {backup_id} verification failed"
            )
            await self.retry_backup()

    @trigger(schedule="0 2 * * *")  # Daily at 2 AM
    async def daily_maintenance(self):
        """Perform daily maintenance tasks"""
        await self.vacuum_tables()
        await self.update_statistics()
        await self.rotate_logs()
        await self.cleanup_temp_data()
```

**Voice Over**:
> "These patterns solve real-world problems: coordination, state management, AI decisions, and event-driven workflows."

### Screen Capture Notes:
- Show pattern comparisons
- Highlight key differences
- Display use cases for each
- Show architectural diagrams

**Timestamp**: 14:00 - 17:00

---

## Scene 8: Best Practices & Troubleshooting (17:00 - 19:00)

### Screen: Best Practices Checklist
**Voice Over**:
> "Let's review best practices for building robust agents."

### Best Practices Display:
```
✅ Agent Development Best Practices

1. Design Principles:
   ✓ Single Responsibility: One agent, one purpose
   ✓ Idempotency: Safe to retry operations
   ✓ Graceful Degradation: Handle failures elegantly
   ✓ Observable: Log everything important

2. Performance:
   ✓ Use async/await for I/O operations
   ✓ Implement connection pooling
   ✓ Add request timeouts
   ✓ Cache frequently accessed data
   ✓ Batch operations when possible

3. Error Handling:
   ✓ Catch and log all exceptions
   ✓ Implement retry logic with backoff
   ✓ Define circuit breakers
   ✓ Provide detailed error messages

4. Security:
   ✓ Validate all inputs
   ✓ Use parameterized queries
   ✓ Encrypt sensitive data
   ✓ Follow principle of least privilege
   ✓ Audit all operations

5. Testing:
   ✓ Unit tests for business logic
   ✓ Integration tests for databases
   ✓ Load tests for performance
   ✓ Chaos tests for resilience

6. Monitoring:
   ✓ Track success/failure rates
   ✓ Monitor resource usage
   ✓ Set up alerts for anomalies
   ✓ Maintain audit logs
```

### Demo Code - Error Handling:
```python
# agents/robust_agent.py
from ai_shell.agents import BaseAgent
from ai_shell.retry import with_retry, exponential_backoff
from ai_shell.circuit_breaker import CircuitBreaker
import logging

class RobustAgent(BaseAgent):
    """Demonstrates robust error handling"""

    def __init__(self, config):
        super().__init__(config)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )

    @with_retry(
        max_attempts=3,
        backoff=exponential_backoff(base=2),
        exceptions=(ConnectionError, TimeoutError)
    )
    async def execute_with_retry(self, task):
        """Automatically retries on transient failures"""
        try:
            result = await self.process_task(task)
            return result

        except Exception as e:
            self.logger.error(f"Task failed: {e}", exc_info=True)

            # Track error for monitoring
            await self.record_error(e)

            # Rethrow for retry logic
            raise

    async def execute_with_circuit_breaker(self, task):
        """Prevents cascading failures"""
        try:
            async with self.circuit_breaker:
                result = await self.process_task(task)
                return result

        except CircuitBreaker.CircuitOpen:
            self.logger.warning("Circuit breaker open, using fallback")
            return await self.fallback_behavior(task)

    async def fallback_behavior(self, task):
        """Define graceful degradation"""
        # Return cached result, default value, or error response
        return {"status": "degraded", "message": "Using cached data"}
```

### Troubleshooting Guide:
```bash
# Common Issues and Solutions

# Issue: Agent won't start
ai> agent logs query_optimizer --tail 50

[ERROR] Failed to connect to database
Solution: Check database connection string and credentials

# Issue: Agent using too much memory
ai> agent stats query_optimizer

Memory: 2.3 GB (exceeds limit)
Solution: Reduce batch size or implement pagination

# Issue: Slow agent performance
ai> agent profile query_optimizer --duration=60s

Hotspots:
  1. analyze_query() - 78% of time
  2. llm.complete() - 15% of time

Solution: Cache analysis results, use faster AI model

# Issue: Agent crashes on errors
ai> agent debug query_optimizer

Enable debug mode and reproduce issue:
ai> agent set-log-level query_optimizer DEBUG

# Issue: Test database cleanup
ai> agent test-cleanup query_optimizer

Removing test data...
✓ Cleaned up 1,234 test records
✓ Reset agent state
```

**Voice Over**:
> "Following best practices and knowing how to troubleshoot will save you hours of debugging."

### Screen Capture Notes:
- Show checklist animation
- Display error handling code
- Highlight debugging commands
- Show problem resolution

**Timestamp**: 17:00 - 19:00

---

## Scene 9: Conclusion & Resources (19:00 - 20:00)

### Screen: Summary Dashboard
**Voice Over**:
> "Congratulations! You've mastered custom agent development in AI-Shell."

### Summary Display:
```
🎓 Skills Learned:

✓ Agent Architecture
  - Lifecycle management
  - Event triggers
  - Scheduled tasks

✓ Implementation
  - Writing custom agents
  - Configuration
  - Testing strategies

✓ Deployment
  - Production deployment
  - Monitoring and metrics
  - Error handling

✓ Advanced Patterns
  - Multi-agent coordination
  - Stateful agents
  - AI-powered decisions
  - Event-driven workflows
```

### Next Steps:
```
📚 Continue Learning:

1. Explore Built-in Agents
   - Study included agent implementations
   - Learn from production patterns

2. Join Community
   - Share your agents
   - Get feedback and help
   - Contribute improvements

3. Build Real Agents
   - Start with simple use cases
   - Iterate based on feedback
   - Scale gradually

4. Advanced Topics
   - Distributed agents
   - Multi-database coordination
   - Custom AI integrations
```

### Resources:
```
📖 Documentation:
   https://docs.ai-shell.io/agents

🔧 Agent SDK Reference:
   https://docs.ai-shell.io/sdk

💬 Community Forum:
   https://community.ai-shell.io

📦 Agent Marketplace:
   https://marketplace.ai-shell.io

🎥 Next Tutorial:
   05-enterprise-deployment-script.md
```

**Voice Over**:
> "Ready for enterprise deployment? Our next tutorial covers production hardening, high availability, and security. See you there!"

### Screen Capture Notes:
- Show skills checklist
- Display resource links
- Preview next tutorial
- End with call-to-action

**Timestamp**: 19:00 - 20:00

---

## Production Notes

### Visual Style:
- Code-focused with agent architecture diagrams
- Real IDE/editor for authentic feel
- Split screens for showing multiple agents
- Animated state transitions

### Code Examples:
- Use realistic production code
- Include error handling
- Show complete implementations
- Demonstrate testing

### Demonstrations:
- Live coding (with slight speedup)
- Real database operations
- Actual AI responses
- Production deployment process

---

## Resources

- **Agent Development Guide**: https://docs.ai-shell.io/agents/development
- **Agent SDK Reference**: https://docs.ai-shell.io/sdk
- **Example Agents**: https://github.com/yourusername/ai-shell/tree/main/examples/agents
- **Next Tutorial**: 05-enterprise-deployment-script.md

---

## Video Metadata

**Title**: Build Custom AI Agents in AI-Shell - Complete Tutorial (20 min)
**Description**: Learn to build, test, and deploy custom AI agents in AI-Shell. Covers agent architecture, implementation patterns, production deployment, and advanced coordination techniques.

**Tags**: ai-shell, agents, automation, python, ai, machine-learning, database, devops, tutorial, microservices, event-driven
