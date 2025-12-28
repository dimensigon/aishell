# AI-Shell Configuration Reference

Complete configuration reference for AI-Shell, covering all available settings, environment variables, and configuration options.

## Table of Contents

- [Configuration File Location](#configuration-file-location)
- [Configuration File Format](#configuration-file-format)
- [Core Configuration Sections](#core-configuration-sections)
  - [System Settings](#system-settings)
  - [LLM Configuration](#llm-configuration)
  - [Database Connections](#database-connections)
  - [MCP Configuration](#mcp-configuration)
  - [Security Settings](#security-settings)
  - [Performance Tuning](#performance-tuning)
  - [UI Configuration](#ui-configuration)
- [Environment Variables](#environment-variables)
- [Configuration Examples](#configuration-examples)
- [Advanced Configuration](#advanced-configuration)

---

## Configuration File Location

AI-Shell searches for configuration files in the following locations (in order):

1. `~/.ai-shell/config.yaml` (recommended)
2. `./config/ai-shell-config.yaml` (project-specific)
3. `./ai-shell-config.yaml` (current directory)
4. `~/.ai-shell.json` (legacy format)
5. `./.ai-shell.json` (project-specific legacy)
6. `./ai-shell.config.json` (alternative location)

You can also specify a custom configuration file:

```bash
ai-shell --config /path/to/custom-config.yaml
```

---

## Configuration File Format

AI-Shell supports both **YAML** (recommended) and **JSON** configuration formats.

### YAML Format (Recommended)

```yaml
# ~/.ai-shell/config.yaml
system:
  startup_animation: true
  matrix_style: enhanced

llm:
  provider: anthropic
  model: claude-sonnet-4-5-20250929
  temperature: 0.1
  maxTokens: 4096

databases:
  production:
    type: postgres
    host: localhost
    port: 5432
    database: myapp_prod
```

### JSON Format (Legacy)

```json
{
  "mode": "interactive",
  "aiProvider": "anthropic",
  "model": "claude-sonnet-4-5-20250929",
  "timeout": 30000,
  "verbose": false
}
```

---

## Core Configuration Sections

### System Settings

Controls general system behavior and startup options.

```yaml
system:
  # Enable startup animation
  startup_animation: true

  # Animation style: 'enhanced', 'basic', 'none'
  matrix_style: enhanced

  # Logging level: 'debug', 'info', 'warn', 'error'
  log_level: info

  # Enable verbose output
  verbose: false
```

**Available Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `startup_animation` | boolean | `true` | Show animated splash screen on startup |
| `matrix_style` | string | `'enhanced'` | Animation style: `enhanced`, `basic`, `none` |
| `log_level` | string | `'info'` | Logging level: `debug`, `info`, `warn`, `error` |
| `verbose` | boolean | `false` | Enable verbose output for debugging |

---

### LLM Configuration

Configure AI providers and language models.

```yaml
llm:
  # AI Provider: 'anthropic', 'openai', 'ollama', 'llamacpp'
  provider: anthropic

  # Model name
  model: claude-sonnet-4-5-20250929

  # Temperature (0.0 - 1.0)
  temperature: 0.1

  # Max tokens for responses
  maxTokens: 4096

  # Request timeout (milliseconds)
  timeout: 30000

  # Model-specific configurations
  models:
    intent: llama2:7b
    completion: codellama:13b
    anonymizer: mistral:7b

  # Ollama configuration
  ollama_host: localhost:11434

  # Local model path
  model_path: /data0/models
```

**Provider Configuration:**

#### Anthropic (Claude)

```yaml
llm:
  provider: anthropic
  model: claude-sonnet-4-5-20250929
  temperature: 0.1
  maxTokens: 4096
```

**Environment Variable:**
```bash
export ANTHROPIC_API_KEY="your-api-key"
```

#### OpenAI

```yaml
llm:
  provider: openai
  model: gpt-4
  temperature: 0.2
  maxTokens: 2048
```

**Environment Variable:**
```bash
export OPENAI_API_KEY="your-api-key"
```

#### Ollama (Local Models)

```yaml
llm:
  provider: ollama
  model: llama2
  ollama_host: localhost:11434
  models:
    intent: llama2:7b
    completion: codellama:13b
    anonymizer: mistral:7b
```

#### LlamaCPP (Local Models)

```yaml
llm:
  provider: llamacpp
  model_path: /path/to/models
  model: llama-2-7b.gguf
```

**LLM Options Reference:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `provider` | string | `'anthropic'` | AI provider: `anthropic`, `openai`, `ollama`, `llamacpp` |
| `model` | string | `'claude-sonnet-4-5-20250929'` | Model identifier |
| `temperature` | number | `0.1` | Randomness (0.0-1.0). Lower = more deterministic |
| `maxTokens` | number | `4096` | Maximum tokens in response |
| `timeout` | number | `30000` | Request timeout in milliseconds |
| `ollama_host` | string | `'localhost:11434'` | Ollama server address |
| `model_path` | string | `'/data0/models'` | Path to local model files |

---

### Database Connections

Configure connections to multiple databases.

```yaml
databases:
  # Connection name
  production:
    # Database type: 'postgres', 'mysql', 'mongodb', 'redis', 'oracle', 'cassandra'
    type: postgres

    # Connection details
    host: prod.db.example.com
    port: 5432
    database: app_prod
    username: dbuser
    password: ${DB_PASSWORD}  # Use environment variable

    # Connection pooling
    pool:
      min: 5
      max: 20
      idleTimeout: 30000

    # SSL/TLS
    ssl:
      enabled: true
      rejectUnauthorized: true
      ca: /path/to/ca.pem
      cert: /path/to/cert.pem
      key: /path/to/key.pem

  # Redis cache
  cache:
    type: redis
    host: redis.example.com
    port: 6379
    password: ${REDIS_PASSWORD}
    db: 0

  # MongoDB
  documents:
    type: mongodb
    host: mongo.example.com
    port: 27017
    database: app_docs
    authSource: admin
    replicaSet: rs0
```

**Database Type Configuration:**

#### PostgreSQL

```yaml
databases:
  mydb:
    type: postgres
    host: localhost
    port: 5432
    database: myapp
    username: postgres
    password: ${POSTGRES_PASSWORD}
    pool:
      min: 2
      max: 10
    ssl:
      enabled: false
```

**Connection String Format:**
```bash
postgres://username:password@host:port/database
```

#### MySQL/MariaDB

```yaml
databases:
  mysql_db:
    type: mysql
    host: localhost
    port: 3306
    database: myapp
    username: root
    password: ${MYSQL_PASSWORD}
    charset: utf8mb4
```

#### MongoDB

```yaml
databases:
  mongo_db:
    type: mongodb
    host: localhost
    port: 27017
    database: myapp
    authSource: admin
    replicaSet: rs0
```

#### Redis

```yaml
databases:
  redis_cache:
    type: redis
    host: localhost
    port: 6379
    password: ${REDIS_PASSWORD}
    db: 0
```

#### Oracle

```yaml
databases:
  oracle_db:
    type: oracle
    host: localhost
    port: 1521
    database: ORCL
    username: system
    password: ${ORACLE_PASSWORD}
    thin_mode: true
```

**Database Options Reference:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `type` | string | required | Database type: `postgres`, `mysql`, `mongodb`, `redis`, `oracle` |
| `host` | string | `'localhost'` | Database server hostname |
| `port` | number | varies | Port number (varies by database type) |
| `database` | string | required | Database name |
| `username` | string | required | Authentication username |
| `password` | string | required | Authentication password (use env vars!) |
| `pool.min` | number | `2` | Minimum pool size |
| `pool.max` | number | `10` | Maximum pool size |
| `pool.idleTimeout` | number | `30000` | Idle connection timeout (ms) |
| `ssl.enabled` | boolean | `false` | Enable SSL/TLS |

---

### MCP Configuration

Configure Model Context Protocol (MCP) connections.

```yaml
mcp:
  # Maximum concurrent connections
  max_connections: 20

  # Connection timeout
  connection_timeout: 5000

  # Oracle-specific settings
  oracle:
    thin_mode: true
    connection_pool_size: 5

  # PostgreSQL-specific settings
  postgresql:
    connection_pool_size: 5
    statement_timeout: 30000
```

**MCP Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_connections` | number | `20` | Maximum concurrent MCP connections |
| `connection_timeout` | number | `5000` | Connection timeout in milliseconds |
| `oracle.thin_mode` | boolean | `true` | Use Oracle thin client mode |
| `oracle.connection_pool_size` | number | `5` | Oracle connection pool size |
| `postgresql.connection_pool_size` | number | `5` | PostgreSQL pool size |
| `postgresql.statement_timeout` | number | `30000` | Query timeout for PostgreSQL |

---

### Security Settings

Configure security features, encryption, and access control.

```yaml
security:
  # Vault configuration
  vault:
    # Encryption algorithm: 'aes-256', 'aes-128'
    encryption: aes-256

    # Key derivation: 'pbkdf2', 'scrypt'
    keyDerivation: pbkdf2

    # Backend: 'keyring', 'file', 'env'
    vault_backend: keyring

  # Audit logging
  audit:
    enabled: true
    destination: /var/log/ai-shell/audit.log
    format: json
    includeQueryResults: false

  # PII/sensitive data handling
  auto_redaction: true
  redact_patterns:
    - email
    - ssn
    - credit_card
    - api_key

  # Command approval
  sensitive_commands_require_confirmation: true
  dangerous_commands:
    - DROP
    - TRUNCATE
    - DELETE

  # Multi-factor authentication
  mfa:
    enabled: false
    provider: totp
```

**Security Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `vault.encryption` | string | `'aes-256'` | Encryption algorithm |
| `vault.keyDerivation` | string | `'pbkdf2'` | Key derivation function |
| `vault.vault_backend` | string | `'keyring'` | Credential storage backend |
| `audit.enabled` | boolean | `true` | Enable audit logging |
| `audit.destination` | string | required | Log file path |
| `auto_redaction` | boolean | `true` | Automatically redact sensitive data |
| `sensitive_commands_require_confirmation` | boolean | `true` | Require confirmation for dangerous commands |

**Vault Key Configuration:**

```bash
# Set vault master password via environment variable
export AI_SHELL_SECURITY_VAULT_KEY="your-secure-master-password"
```

---

### Performance Tuning

Optimize AI-Shell performance for your workload.

```yaml
performance:
  # Query processing
  queryTimeout: 30000
  cacheSize: 5000
  parallelQueries: 4

  # Worker configuration
  async_workers: 4
  max_concurrent_queries: 10

  # Cache configuration
  cache_size: 1000
  cache_ttl: 3600

  # Vector database
  vector_db_dimension: 384
  similarity_threshold: 0.7

  # Memory limits
  max_memory_mb: 2048
  gc_interval: 300000
```

**Performance Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `queryTimeout` | number | `30000` | Query timeout in milliseconds |
| `cacheSize` | number | `5000` | Number of cached query results |
| `parallelQueries` | number | `4` | Number of parallel query workers |
| `async_workers` | number | `4` | Number of async worker threads |
| `max_concurrent_queries` | number | `10` | Max concurrent query execution |
| `cache_ttl` | number | `3600` | Cache TTL in seconds |
| `vector_db_dimension` | number | `384` | Vector embedding dimensions |
| `max_memory_mb` | number | `2048` | Maximum memory usage in MB |

---

### UI Configuration

Customize the user interface and display options.

```yaml
ui:
  # UI framework: 'textual', 'blessed'
  framework: textual

  # Color theme: 'cyberpunk', 'minimal', 'dark', 'light'
  theme: cyberpunk

  # Panel priority when typing
  panel_priority:
    typing: prompt
    idle: balanced

  # Display options
  show_query_time: true
  show_row_numbers: true
  max_table_width: 120

  # Output formatting
  date_format: YYYY-MM-DD HH:mm:ss
  number_format: en-US
  currency_symbol: $
```

**UI Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `framework` | string | `'textual'` | UI framework: `textual`, `blessed` |
| `theme` | string | `'cyberpunk'` | Color theme |
| `show_query_time` | boolean | `true` | Display query execution time |
| `show_row_numbers` | boolean | `true` | Show row numbers in results |
| `max_table_width` | number | `120` | Maximum table width in characters |

---

## Environment Variables

Environment variables override configuration file settings.

### Core Environment Variables

```bash
# AI-Shell Core
export AI_SHELL_MODE="interactive"           # Mode: 'interactive' or 'command'
export AI_SHELL_CONFIG="/path/to/config"     # Custom config file
export AI_SHELL_LOG_LEVEL="info"             # Log level
export AI_SHELL_VERBOSE="true"               # Verbose output

# LLM Configuration
export AI_SHELL_PROVIDER="anthropic"         # AI provider
export AI_SHELL_MODEL="claude-sonnet-4-5"    # Model name
export ANTHROPIC_API_KEY="sk-ant-..."        # Anthropic API key
export OPENAI_API_KEY="sk-..."               # OpenAI API key

# Database
export DB_PASSWORD="secure-password"         # Database password
export POSTGRES_PASSWORD="pg-pass"           # PostgreSQL password
export MYSQL_PASSWORD="mysql-pass"           # MySQL password
export REDIS_PASSWORD="redis-pass"           # Redis password
export ORACLE_PASSWORD="oracle-pass"         # Oracle password

# Security
export AI_SHELL_SECURITY_VAULT_KEY="master"  # Vault master password

# Performance
export AI_SHELL_TIMEOUT="30000"              # Timeout in ms
export AI_SHELL_CACHE_DIR="/tmp/ai-shell"    # Cache directory
```

### Environment Variable Format

Environment variables follow the pattern: `AI_SHELL_<SECTION>_<KEY>`

**Examples:**

```bash
# System section
export AI_SHELL_SYSTEM_STARTUP_ANIMATION="false"
export AI_SHELL_SYSTEM_LOG_LEVEL="debug"

# LLM section
export AI_SHELL_LLM_PROVIDER="anthropic"
export AI_SHELL_LLM_MODELS_INTENT="mistral:7b"

# Performance section
export AI_SHELL_PERFORMANCE_CACHE_SIZE="1000"
export AI_SHELL_PERFORMANCE_ASYNC_WORKERS="4"
```

---

## Configuration Examples

### Minimal Configuration

```yaml
# Minimal config for local development
llm:
  provider: anthropic
  model: claude-sonnet-4-5-20250929

databases:
  default:
    type: postgres
    host: localhost
    port: 5432
    database: myapp
```

### Production Configuration

```yaml
# Production configuration with all security features
system:
  startup_animation: false
  log_level: warn

llm:
  provider: anthropic
  model: claude-sonnet-4-5-20250929
  temperature: 0.1
  maxTokens: 4096
  timeout: 30000

databases:
  production:
    type: postgres
    host: prod-db.example.com
    port: 5432
    database: app_prod
    username: app_user
    password: ${DB_PASSWORD}
    pool:
      min: 10
      max: 50
      idleTimeout: 30000
    ssl:
      enabled: true
      rejectUnauthorized: true
      ca: /etc/ssl/certs/ca.pem

security:
  vault:
    encryption: aes-256
    keyDerivation: pbkdf2
    vault_backend: keyring
  audit:
    enabled: true
    destination: /var/log/ai-shell/audit.log
    format: json
  auto_redaction: true
  sensitive_commands_require_confirmation: true

performance:
  queryTimeout: 60000
  cacheSize: 10000
  parallelQueries: 8
  async_workers: 8
  max_concurrent_queries: 20

ui:
  framework: textual
  theme: minimal
  show_query_time: true
```

### Multi-Database Federation

```yaml
# Configuration for querying across multiple databases
databases:
  # PostgreSQL (primary data)
  postgres_main:
    type: postgres
    host: pg.example.com
    port: 5432
    database: app_data

  # MySQL (legacy system)
  mysql_legacy:
    type: mysql
    host: mysql.example.com
    port: 3306
    database: old_app

  # MongoDB (documents)
  mongo_docs:
    type: mongodb
    host: mongo.example.com
    port: 27017
    database: documents

  # Redis (cache)
  redis_cache:
    type: redis
    host: redis.example.com
    port: 6379
    db: 0

  # Oracle (ERP system)
  oracle_erp:
    type: oracle
    host: oracle.example.com
    port: 1521
    database: ERP
```

### Development Configuration

```yaml
# Local development with Ollama
system:
  startup_animation: true
  verbose: true

llm:
  provider: ollama
  ollama_host: localhost:11434
  models:
    intent: llama2:7b
    completion: codellama:13b

databases:
  dev:
    type: postgres
    host: localhost
    port: 5432
    database: myapp_dev
    username: dev_user
    password: dev_password

security:
  sensitive_commands_require_confirmation: false
  audit:
    enabled: false

performance:
  async_workers: 2
  cache_size: 100
```

---

## Advanced Configuration

### Custom Connection String

You can use connection strings instead of individual parameters:

```bash
ai-shell connect postgres://user:pass@localhost:5432/mydb
ai-shell connect mongodb://user:pass@localhost:27017/mydb
ai-shell connect redis://localhost:6379/0
```

### Configuration Validation

Validate your configuration file:

```bash
ai-shell config validate
ai-shell config validate --config /path/to/config.yaml
```

### Configuration Management Commands

```bash
# View current configuration
ai-shell config show

# Get specific value
ai-shell config get llm.provider

# Set configuration value
ai-shell config set llm.temperature 0.2

# Save current configuration
ai-shell config save

# Reset to defaults
ai-shell config reset
```

### Configuration Priority

Configuration values are loaded in this order (later values override earlier):

1. Default configuration (built-in)
2. Global config file (`~/.ai-shell/config.yaml`)
3. Project config file (`./ai-shell-config.yaml`)
4. Environment variables (`AI_SHELL_*`)
5. Command-line arguments

### Configuration File Encryption

Encrypt sensitive configuration values:

```bash
# Encrypt a configuration value
ai-shell config encrypt "database.password" "my-password"

# Decrypt configuration
ai-shell config decrypt "database.password"
```

Encrypted values are stored as:

```yaml
databases:
  production:
    password: "encrypted:AES256:abc123..."
```

### Configuration Templates

Generate configuration templates:

```bash
# Generate minimal config
ai-shell config init --minimal

# Generate full config with all options
ai-shell config init --full

# Generate config for specific database
ai-shell config init --database postgres
```

---

## Troubleshooting

### Common Issues

**Configuration not loading:**

```bash
# Check which config file is being used
ai-shell config which

# Validate configuration
ai-shell config validate
```

**Environment variables not working:**

```bash
# List all AI-Shell environment variables
env | grep AI_SHELL

# Test with explicit config
ai-shell --config ~/.ai-shell/config.yaml
```

**Connection issues:**

```bash
# Test database connection
ai-shell test-connection production

# Show connection details
ai-shell config show databases.production
```

---

## Best Practices

1. **Never commit API keys or passwords** - Always use environment variables
2. **Use separate configs for environments** - dev, staging, production
3. **Enable audit logging in production** - Track all database operations
4. **Configure connection pooling** - Optimize for your workload
5. **Set appropriate timeouts** - Prevent hanging queries
6. **Enable SSL/TLS** - Always use encryption in production
7. **Regular backups of config** - Version control your configuration
8. **Use vault for credentials** - Encrypt sensitive data at rest
9. **Monitor performance settings** - Tune based on actual usage
10. **Document custom settings** - Add comments to your config files

---

## See Also

- [CLI Command Reference](./cli-reference.md)
- [Security Best Practices](./enterprise/security.md)
- [Database Federation Guide](./tutorials/database-federation.md)
- [Quick Start Guide](./quick-start.md)
