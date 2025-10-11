# AI-Shell v2.0.0 - Quick Reference Guide

## Installation

```bash
# Core v2.0 dependencies (optional)
pip install anthropic pyotp requests-oauthlib python3-saml strawberry-graphql[fastapi] fastapi uvicorn
```

---

## AI Query Assistant

### Basic Setup

```python
from src.ai.query_assistant import QueryAssistant, QueryContext

# Initialize
assistant = QueryAssistant(api_key='your-key')  # or use ANTHROPIC_API_KEY env var

# Create context
context = QueryContext(
    database_type="postgresql",
    schema_info={'users': {'columns': [...]}},
    table_names=['users', 'orders']
)
```

### Generate SQL

```python
result = assistant.generate_sql("show top 10 users by order amount", context)
if result.success:
    print(result.sql_query)
    print(result.explanation)
```

### Explain Query

```python
result = assistant.explain_query(
    "SELECT * FROM users WHERE active = 1",
    context,
    detail_level="medium"  # simple, medium, detailed
)
print(result.explanation)
```

### Optimize Query

```python
result = assistant.optimize_query(
    "SELECT * FROM users",
    context,
    performance_data={'execution_time': 2.5, 'rows_affected': 10000}
)
for suggestion in result.optimization_suggestions:
    print(suggestion)
```

---

## Security Features

### Two-Factor Authentication

```python
from src.security.advanced.advanced_auth import TwoFactorAuth

twofa = TwoFactorAuth(issuer="MyApp")

# Setup
secret = twofa.generate_secret()
uri = twofa.get_provisioning_uri(secret, "user@example.com")

# Verify
is_valid = twofa.verify_code(secret, "123456")

# Backup codes
codes = twofa.generate_backup_codes(10)
```

### SSO (OAuth)

```python
from src.security.advanced.advanced_auth import SSOManager

sso = SSOManager()

# Configure
sso.configure_oauth_provider(
    provider_name="google",
    client_id="...",
    client_secret="...",
    authorization_url="...",
    token_url="...",
    userinfo_url="...",
    scopes=["email", "profile"]
)

# Login
auth_url, state = sso.initiate_oauth_login("google", "https://app/callback")
```

### Activity Monitoring

```python
from src.security.advanced.activity_monitor import ActivityMonitor, EventType

monitor = ActivityMonitor(retention_days=90)

# Log query
monitor.log_query(
    user_id="alice",
    sql_query="SELECT * FROM users",
    execution_time=0.5,
    rows_affected=100,
    success=True,
    ip_address="192.168.1.1"
)

# Get stats
stats = monitor.get_statistics()
```

### Anomaly Detection

```python
from src.security.advanced.activity_monitor import AnomalyDetector

detector = AnomalyDetector(monitor)

# Detect
result = detector.detect_anomalies("alice")
if result.is_anomaly:
    print(f"Threat: {result.threat_level.value}")
    print(f"Reasons: {result.reasons}")
```

---

## GraphQL API

### Server Setup

```python
from src.api.graphql.server import GraphQLServer, GraphQLConfig
import sqlite3

# Configure
config = GraphQLConfig(
    database_url="sqlite:///db.db",
    enable_playground=True,
    enable_subscriptions=True,
    rate_limit_per_minute=100
)

# Create server
server = GraphQLServer(config)

# Generate schema
db = sqlite3.connect('db.db')
server.generate_schema_from_database(db, tables=['users', 'orders'])

# Create FastAPI app
app = server.create_fastapi_app()

# Run
server.run(host="0.0.0.0", port=8000)
```

### GraphQL Queries

```graphql
# List users
{
  users(limit: 10) {
    id
    name
    email
  }
}

# Get user by ID
{
  user(id: 1) {
    id
    name
  }
}

# Create user
mutation {
  createUser(input: {
    email: "new@example.com"
    name: "New User"
  }) {
    id
  }
}

# Subscribe to changes
subscription {
  tableChanges(tableName: "users") {
    operation
    data
  }
}
```

### Real-Time Subscriptions

```python
from src.api.graphql.subscriptions import SubscriptionManager

manager = SubscriptionManager()

# Subscribe
await manager.subscribe("subscriber_id", "topic:users")

# Publish
await manager.publish("topic:users", {"event": "data"})

# Listen
async for message in manager.listen("subscriber_id"):
    print(message)
```

---

## Environment Variables

```bash
# AI Features
export ANTHROPIC_API_KEY='your-claude-api-key'

# OAuth
export OAUTH_CLIENT_ID='your-client-id'
export OAUTH_CLIENT_SECRET='your-secret'

# Security
export JWT_SECRET_KEY='your-jwt-secret'
export SESSION_SECRET_KEY='your-session-secret'

# GraphQL
export GRAPHQL_RATE_LIMIT=100
export GRAPHQL_MAX_DEPTH=10
```

---

## Running Demos

```bash
# AI Query Assistant
python examples/v2_features/ai_query_assistant_demo.py

# Security Features
python examples/v2_features/security_features_demo.py

# GraphQL API
python examples/v2_features/graphql_api_demo.py

# Performance Benchmarks
python examples/v2_features/performance_benchmarks.py
```

---

## Testing

```bash
# All v2.0 tests
pytest tests/ai tests/security/advanced tests/api -v

# Specific feature
pytest tests/ai -v

# With coverage
pytest --cov=src.ai --cov=src.security.advanced --cov=src.api.graphql
```

---

## Common Patterns

### AI Query with Conversation Context

```python
from src.ai.conversation_manager import ConversationManager

manager = ConversationManager()
session_id = manager.start_session()

# Add messages
manager.add_user_message("show all users", session_id)
manager.add_assistant_message("Generated: SELECT * FROM users", session_id)

# Get history
history = manager.get_conversation_history(session_id)
```

### Security Event Dashboard

```python
# Get threat dashboard
dashboard = detector.get_threat_dashboard()

print(f"High threats (24h): {dashboard['high_threat_events_24h']}")
print(f"Active users: {dashboard['total_active_users']}")
print(f"Anomalies: {len(dashboard['users_with_anomalies'])}")
```

### GraphQL with Authentication

```python
from src.api.graphql.server import GraphQLContext

context = GraphQLContext(
    request=request,
    db_connection=db,
    user_id="alice",
    user_roles=["admin", "user"]
)

# Check permission in resolver
if context.has_permission("admin"):
    # Allow operation
    pass
```

---

## File Locations

### Source Code
- `/home/claude/AIShell/src/ai/` - AI query assistant
- `/home/claude/AIShell/src/security/advanced/` - Advanced security
- `/home/claude/AIShell/src/api/graphql/` - GraphQL API

### Tests
- `/home/claude/AIShell/tests/ai/` - AI tests
- `/home/claude/AIShell/tests/security/advanced/` - Security tests
- `/home/claude/AIShell/tests/api/` - GraphQL tests

### Examples
- `/home/claude/AIShell/examples/v2_features/` - All demos

### Documentation
- `/home/claude/AIShell/docs/v2_features/` - Feature documentation

---

## Performance Tips

### AI Assistant
- Cache common queries
- Use fallback for simple patterns
- Batch API calls when possible
- Set appropriate timeouts

### Security
- Index activity logs for fast queries
- Use ring buffer for high throughput
- Update baselines periodically
- Archive old logs

### GraphQL
- Enable query caching
- Use DataLoader for batching
- Limit query depth and complexity
- Monitor subscription connections

---

## Troubleshooting

### AI Assistant
```python
# Check if API available
if assistant.available:
    # Use API
else:
    # Using fallback
```

### Security
```python
# Check 2FA available
if twofa.available:
    # Use 2FA
else:
    # Install pyotp
```

### GraphQL
```python
# Check schema generated
if server.schema:
    # Schema ready
else:
    # Generate schema
```

---

## API Response Formats

### AI Query Response
```python
{
    'success': bool,
    'sql_query': str,
    'explanation': str,
    'optimization_suggestions': list,
    'warnings': list,
    'confidence': float,
    'metadata': dict
}
```

### Security Event
```python
{
    'event_type': str,
    'user_id': str,
    'timestamp': datetime,
    'threat_level': str,
    'description': str,
    'metadata': dict
}
```

### Anomaly Result
```python
{
    'is_anomaly': bool,
    'threat_level': str,
    'reasons': list,
    'confidence': float,
    'recommended_action': str
}
```

---

## Best Practices

### AI Assistant
1. Always provide schema context
2. Use appropriate detail levels
3. Handle API failures gracefully
4. Cache repetitive queries
5. Monitor API usage

### Security
1. Store secrets securely
2. Rotate keys regularly
3. Monitor anomalies continuously
4. Archive logs appropriately
5. Test authentication flows

### GraphQL
1. Implement authentication
2. Set rate limits
3. Limit query complexity
4. Use HTTPS in production
5. Monitor performance

---

## Support Resources

- Full Documentation: `/home/claude/AIShell/docs/v2_features/V2_FEATURES.md`
- Implementation Summary: `/home/claude/AIShell/docs/v2_features/IMPLEMENTATION_SUMMARY.md`
- Test Examples: `/home/claude/AIShell/tests/`
- Demo Scripts: `/home/claude/AIShell/examples/v2_features/`

---

**Version**: 2.0.0
**Last Updated**: 2025-10-11
