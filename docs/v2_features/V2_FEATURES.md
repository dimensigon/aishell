# AI-Shell v2.0.0 - New Features Guide

## Overview

AI-Shell v2.0.0 introduces three major feature sets that enhance database operations with AI-powered assistance, enterprise security, and modern API capabilities.

## Table of Contents

1. [AI-Powered Query Assistant](#ai-powered-query-assistant)
2. [Advanced Security Features](#advanced-security-features)
3. [GraphQL API Layer](#graphql-api-layer)
4. [Installation](#installation)
5. [Quick Start](#quick-start)
6. [Performance](#performance)

---

## AI-Powered Query Assistant

Transform natural language into complex SQL queries with AI assistance.

### Features

- **Natural Language to SQL**: Convert plain English to complex SQL queries
- **Query Explanation**: Understand SQL queries in plain English
- **Performance Optimization**: Get AI-powered optimization suggestions
- **Query Correction**: Automatically fix SQL syntax errors
- **Schema Understanding**: AI learns from your database structure
- **Conversational Context**: Multi-turn conversations with memory

### Usage Example

```python
from src.ai.query_assistant import QueryAssistant, QueryContext

# Initialize assistant (requires ANTHROPIC_API_KEY)
assistant = QueryAssistant()

# Create context with your schema
context = QueryContext(
    database_type="postgresql",
    schema_info={
        'users': {
            'columns': [
                {'name': 'id', 'type': 'INTEGER'},
                {'name': 'email', 'type': 'TEXT'},
                {'name': 'created_at', 'type': 'TIMESTAMP'}
            ]
        }
    },
    table_names=['users', 'orders', 'products']
)

# Generate SQL from natural language
result = assistant.generate_sql(
    "show me the top 10 users by total order amount from last month",
    context
)

if result.success:
    print(f"SQL: {result.sql_query}")
    print(f"Explanation: {result.explanation}")
```

### Query Explanation

```python
# Explain existing SQL
result = assistant.explain_query(
    "SELECT u.name, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id",
    context,
    detail_level="medium"
)

print(result.explanation)
```

### Query Optimization

```python
# Get optimization suggestions
result = assistant.optimize_query(
    "SELECT * FROM users WHERE status = 'active'",
    context,
    performance_data={'execution_time': 2.5, 'rows_affected': 10000}
)

for suggestion in result.optimization_suggestions:
    print(f"- {suggestion}")
```

### API Requirements

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

Or pass it directly:

```python
assistant = QueryAssistant(api_key='your-key')
```

**Fallback Mode**: Without an API key, the assistant uses pattern-based SQL generation (limited capabilities).

---

## Advanced Security Features

Enterprise-grade security for database operations.

### 1. Two-Factor Authentication (2FA/TOTP)

Compatible with Google Authenticator, Authy, and other TOTP apps.

```python
from src.security.advanced.advanced_auth import TwoFactorAuth

# Initialize 2FA
twofa = TwoFactorAuth(issuer="AI-Shell")

# Generate secret for user
secret = twofa.generate_secret()

# Get QR code URI
uri = twofa.get_provisioning_uri(secret, "user@example.com", "User Name")

# User scans QR code with authenticator app

# Verify TOTP code
is_valid = twofa.verify_code(secret, "123456")

# Generate backup codes
backup_codes = twofa.generate_backup_codes(10)
```

### 2. SSO Integration

Support for OAuth 2.0 and SAML 2.0.

```python
from src.security.advanced.advanced_auth import SSOManager

sso = SSOManager()

# Configure OAuth provider (Google, GitHub, etc.)
sso.configure_oauth_provider(
    provider_name="google",
    client_id="your-client-id",
    client_secret="your-client-secret",
    authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
    token_url="https://oauth2.googleapis.com/token",
    userinfo_url="https://www.googleapis.com/oauth2/v3/userinfo",
    scopes=["openid", "email", "profile"]
)

# Initiate login
auth_url, state = sso.initiate_oauth_login(
    "google",
    redirect_uri="https://yourapp.com/callback"
)

# Complete login after callback
user_info = sso.complete_oauth_login(
    "google",
    authorization_response="https://yourapp.com/callback?code=...",
    state=state
)
```

### 3. Certificate-Based Authentication

```python
from src.security.advanced.advanced_auth import CertificateAuth

cert_auth = CertificateAuth(ca_cert_path="/path/to/ca.crt")

# Verify client certificate
with open("client.crt", "rb") as f:
    cert_data = f.read()

is_valid, cert_info = cert_auth.verify_certificate(cert_data)

if is_valid:
    print(f"Valid certificate: {cert_info['subject']}")
```

### 4. Database Activity Monitoring

Real-time monitoring of all database operations.

```python
from src.security.advanced.activity_monitor import ActivityMonitor, EventType

monitor = ActivityMonitor(retention_days=90)

# Log query execution
monitor.log_query(
    user_id="alice",
    sql_query="SELECT * FROM sensitive_data",
    execution_time=0.5,
    rows_affected=100,
    success=True,
    ip_address="192.168.1.1"
)

# Get statistics
stats = monitor.get_statistics()
print(f"Total events: {stats['total_events']}")

# Get user activity
summary = monitor.get_user_activity_summary("alice")
```

### 5. Anomaly Detection

Detect suspicious patterns and potential security threats.

```python
from src.security.advanced.activity_monitor import AnomalyDetector

detector = AnomalyDetector(monitor)

# Detect anomalies for user
result = detector.detect_anomalies("alice")

if result.is_anomaly:
    print(f"Threat Level: {result.threat_level.value}")
    print("Reasons:")
    for reason in result.reasons:
        print(f"  - {reason}")
    print(f"Action: {result.recommended_action}")

# Get threat dashboard
dashboard = detector.get_threat_dashboard()
print(f"High threats (24h): {dashboard['high_threat_events_24h']}")
```

### Security Dependencies

```bash
pip install pyotp requests-oauthlib python3-saml
```

---

## GraphQL API Layer

Modern GraphQL interface with automatic schema generation.

### Features

- **Automatic Schema Generation**: Generate schema from database tables
- **CRUD Operations**: Query and Mutation types for all tables
- **Real-Time Subscriptions**: WebSocket-based live data updates
- **Query Optimization**: DataLoader batching, caching, N+1 prevention
- **Authentication Integration**: JWT, RBAC, field-level permissions
- **Rate Limiting**: Per-user/role request limiting

### Setup

```python
from src.api.graphql.server import GraphQLServer, GraphQLConfig
import sqlite3

# Configure server
config = GraphQLConfig(
    database_url="sqlite:///./database.db",
    enable_playground=True,
    enable_subscriptions=True,
    max_query_depth=10,
    max_query_complexity=1000,
    rate_limit_per_minute=100
)

# Create server
server = GraphQLServer(config)

# Generate schema from database
db = sqlite3.connect('database.db')
server.generate_schema_from_database(db, tables=['users', 'orders'])

# Create FastAPI app
app = server.create_fastapi_app()

# Run server
server.run(host="0.0.0.0", port=8000)
```

### GraphQL Queries

```graphql
# List users with pagination
query {
  users(limit: 10, offset: 0) {
    id
    email
    name
    active
  }
}

# Get user with relationships
query {
  user(id: 1) {
    id
    name
    posts {
      id
      title
    }
  }
}

# Filter and search
query {
  users(where: "age > 25 AND active = 1") {
    id
    name
    age
  }
}
```

### GraphQL Mutations

```graphql
# Create user
mutation {
  createUser(input: {
    email: "newuser@example.com"
    name: "New User"
    age: 30
  }) {
    id
    email
    name
  }
}

# Update user
mutation {
  updateUser(id: 1, input: {
    name: "Updated Name"
  }) {
    id
    name
  }
}

# Delete user
mutation {
  deleteUser(id: 1)
}
```

### Real-Time Subscriptions

```graphql
# Subscribe to table changes
subscription {
  tableChanges(tableName: "users", operation: "INSERT") {
    operation
    table
    recordId
    data
  }
}

# Subscribe to specific query updates
subscription {
  queryResults(queryId: "active-users") {
    id
    name
    status
  }
}
```

### Python Client Example

```python
import requests

# Query example
query = '''
query {
  users(limit: 10) {
    id
    name
    email
  }
}
'''

response = requests.post(
    'http://localhost:8000/graphql',
    json={'query': query}
)

data = response.json()
print(data['data']['users'])
```

### GraphQL Dependencies

```bash
pip install strawberry-graphql[fastapi] fastapi uvicorn
```

---

## Installation

### Core Dependencies

```bash
pip install -r requirements.txt
```

### Optional v2.0 Features

```bash
# AI Query Assistant
pip install anthropic

# Advanced Security
pip install pyotp requests-oauthlib python3-saml

# GraphQL API
pip install strawberry-graphql[fastapi] fastapi uvicorn
```

### All v2.0 Features

```bash
pip install anthropic pyotp requests-oauthlib python3-saml strawberry-graphql[fastapi] fastapi uvicorn
```

---

## Quick Start

### 1. Run AI Query Demo

```bash
# Set API key (optional)
export ANTHROPIC_API_KEY='your-key'

# Run demo
python examples/v2_features/ai_query_assistant_demo.py
```

### 2. Run Security Demo

```bash
python examples/v2_features/security_features_demo.py
```

### 3. Run GraphQL Demo

```bash
python examples/v2_features/graphql_api_demo.py
```

### 4. Run Performance Benchmarks

```bash
python examples/v2_features/performance_benchmarks.py
```

### 5. Start GraphQL Server

```bash
# Create server script (server.py)
from src.api.graphql.server import GraphQLServer, GraphQLConfig
import sqlite3

config = GraphQLConfig(database_url="sqlite:///./test.db")
server = GraphQLServer(config)

db = sqlite3.connect('test.db')
server.generate_schema_from_database(db)
app = server.create_fastapi_app()

# Run with uvicorn
# uvicorn server:app --reload
```

Then visit: http://localhost:8000/graphql

---

## Performance

### Benchmarks (Development Hardware)

**AI Query Generation:**
- Simple queries: ~10-50 ms (fallback)
- Complex queries: ~20-100 ms (fallback)
- With Claude API: ~500-2000 ms (network dependent)

**Security Monitoring:**
- Event logging: ~0.1-0.5 ms (>10,000 ops/sec)
- Anomaly detection: ~1-5 ms (>200 ops/sec)
- Event retrieval: ~0.5-2 ms

**Authentication:**
- 2FA code generation: ~0.05-0.2 ms
- 2FA code verification: ~0.1-0.5 ms

**GraphQL Subscriptions:**
- Subscription creation: ~0.1-0.5 ms
- Message delivery: ~0.5-2 ms
- Throughput: >1000 messages/sec

---

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Test Specific Features

```bash
# AI features
pytest tests/ai/ -v

# Security features
pytest tests/security/advanced/ -v

# GraphQL features
pytest tests/api/ -v
```

### Test Coverage

```bash
pytest --cov=src --cov-report=html
```

---

## Configuration

### Environment Variables

```bash
# AI Query Assistant
export ANTHROPIC_API_KEY='your-key'

# OAuth Configuration
export OAUTH_CLIENT_ID='your-client-id'
export OAUTH_CLIENT_SECRET='your-secret'

# Security
export SESSION_SECRET_KEY='your-secret-key'
export JWT_SECRET_KEY='your-jwt-secret'

# GraphQL
export GRAPHQL_RATE_LIMIT=100  # requests per minute
export GRAPHQL_MAX_DEPTH=10
```

### Configuration File

Create `config/v2_features.yaml`:

```yaml
ai_assistant:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  temperature: 0.7
  max_tokens: 4096

security:
  two_factor:
    enabled: true
    issuer: "AI-Shell"
  sso:
    enabled: true
    providers:
      - name: google
        type: oauth2
  activity_monitor:
    retention_days: 90
    anomaly_detection: true

graphql:
  enable_playground: true
  enable_introspection: true
  enable_subscriptions: true
  rate_limit_per_minute: 100
  max_query_depth: 10
  cache_ttl: 300
```

---

## Production Considerations

### AI Query Assistant

1. **API Key Security**: Store API keys securely (environment variables, key vault)
2. **Rate Limiting**: Implement rate limiting for API calls
3. **Caching**: Cache common queries to reduce API calls
4. **Fallback**: Ensure fallback mode works when API is unavailable
5. **Monitoring**: Track API usage and costs

### Security Features

1. **2FA Recovery**: Implement secure backup code storage
2. **SSO Configuration**: Use production OAuth/SAML credentials
3. **Certificate Management**: Implement certificate rotation
4. **Activity Logs**: Store logs in persistent storage
5. **Anomaly Alerts**: Configure real-time alerting

### GraphQL API

1. **Authentication**: Implement JWT or session-based auth
2. **Authorization**: Configure RBAC for field-level permissions
3. **Rate Limiting**: Enforce per-user/role limits
4. **Query Complexity**: Limit query depth and complexity
5. **HTTPS/TLS**: Enable encryption in production
6. **CORS**: Configure CORS appropriately
7. **Monitoring**: Track query performance and errors

---

## Troubleshooting

### AI Query Assistant

**Issue**: API calls failing
- Check `ANTHROPIC_API_KEY` is set correctly
- Verify network connectivity
- Check API rate limits

**Issue**: Fallback mode not working
- Ensure pattern-based converter is installed
- Check database schema info is provided

### Security Features

**Issue**: 2FA codes not verifying
- Install `pyotp`: `pip install pyotp`
- Check system time is synchronized
- Verify secret is stored correctly

**Issue**: SSO not redirecting
- Install required packages
- Verify OAuth/SAML configuration
- Check redirect URIs match

### GraphQL API

**Issue**: Schema not generating
- Install `strawberry-graphql`: `pip install strawberry-graphql[fastapi]`
- Verify database connection
- Check table permissions

**Issue**: Subscriptions not working
- Install WebSocket support: `pip install uvicorn[standard]`
- Check WebSocket port is open
- Verify subscription protocol

---

## API Reference

See individual module documentation:

- [AI Query Assistant API](../api/ai_query_assistant.md)
- [Security Features API](../api/security_features.md)
- [GraphQL API Reference](../api/graphql_api.md)

---

## Support

For issues and questions:

1. Check the [documentation](../README.md)
2. Run the demo scripts for examples
3. Check the test files for usage patterns
4. Review the API reference

---

## License

See LICENSE file in the repository root.
