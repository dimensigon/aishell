# AI-Shell Use Cases

This directory contains practical examples demonstrating common use cases for AI-Shell.

## Examples

### 1. Data Migration (`data-migration.py`)

Migrate data between different database systems with schema mapping and validation.

**Features:**
- Multi-database support (PostgreSQL, MySQL, SQLite, etc.)
- Intelligent schema mapping
- Batch processing with progress tracking
- Data validation and integrity checks
- Parallel table migration

**Usage:**
```bash
# Basic migration
python data-migration.py \
  --source "postgresql://localhost/source_db" \
  --target "mysql://localhost/target_db"

# With custom batch size
python data-migration.py \
  --source "postgresql://localhost/source_db" \
  --target "mysql://localhost/target_db" \
  --batch-size 5000 \
  --parallel 5

# Dry run (test without writing)
python data-migration.py \
  --source "postgresql://localhost/source_db" \
  --target "mysql://localhost/target_db" \
  --dry-run
```

### 2. Automated Monitoring (`automated-monitoring.py`)

Monitor database health, performance, and automatically respond to issues.

**Features:**
- Real-time health checks
- Performance metric collection
- Anomaly detection
- Automatic alerting
- Self-healing capabilities

**Usage:**
```bash
# Monitor with default settings
python automated-monitoring.py --database "postgresql://localhost/mydb"

# Custom monitoring intervals
python automated-monitoring.py \
  --database "postgresql://localhost/mydb" \
  --interval 30 \
  --alert-threshold 80

# Multiple databases
python automated-monitoring.py \
  --databases "prod:postgresql://...","staging:mysql://..."
```

### 3. Query Optimization (`query-optimization.py`)

Analyze and optimize database queries automatically.

**Features:**
- Slow query detection
- Execution plan analysis
- Index recommendations
- Query rewriting
- Performance benchmarking

**Usage:**
```bash
# Analyze specific query
python query-optimization.py \
  --database "postgresql://localhost/mydb" \
  --query "SELECT * FROM users WHERE created_at > '2024-01-01'"

# Monitor and optimize all queries
python query-optimization.py \
  --database "postgresql://localhost/mydb" \
  --monitor \
  --threshold 1000
```

### 4. Custom LLM Provider (`custom-llm-provider.py`)

Integrate custom LLM providers for AI-powered database operations.

**Features:**
- Custom LLM integration
- Local model support (Ollama, LM Studio)
- API-based models (OpenAI, Anthropic, etc.)
- Prompt customization
- Response caching

**Usage:**
```bash
# Use local Ollama model
python custom-llm-provider.py \
  --provider ollama \
  --model llama2 \
  --database "postgresql://localhost/mydb"

# Use OpenAI with custom settings
python custom-llm-provider.py \
  --provider openai \
  --model gpt-4 \
  --temperature 0.2 \
  --database "postgresql://localhost/mydb"
```

## Requirements

Install dependencies:
```bash
pip install ai-shell[examples]
```

Or install individually:
```bash
pip install ai-shell asyncio psycopg2 pymysql pymongo redis pandas
```

## Common Patterns

### Database Connection

All examples support connection strings:

```python
# PostgreSQL
"postgresql://user:password@host:port/database"

# MySQL
"mysql://user:password@host:port/database"

# SQLite
"sqlite:///path/to/database.db"

# MongoDB
"mongodb://host:port/database"

# Redis
"redis://host:port/db"
```

### Error Handling

All examples include comprehensive error handling:

```python
try:
    result = await agent.execute()
except DatabaseError as e:
    print(f"Database error: {e}")
except ConnectionError as e:
    print(f"Connection failed: {e}")
finally:
    await agent.cleanup()
```

### Async Operations

All examples use async/await for better performance:

```python
import asyncio

async def main():
    agent = MyAgent(config)
    await agent.on_start()
    result = await agent.execute()
    await agent.on_stop()

asyncio.run(main())
```

## Configuration

Examples can be configured via:

1. **Command-line arguments**
2. **Environment variables**
3. **Configuration files** (YAML/JSON)

Example config file (`config.yaml`):

```yaml
database:
  type: postgresql
  host: localhost
  port: 5432
  database: mydb
  username: user
  password: ${DB_PASSWORD}

monitoring:
  interval: 60
  threshold: 80
  alerts:
    - type: email
      recipients: [admin@example.com]
    - type: slack
      webhook: ${SLACK_WEBHOOK}

optimization:
  auto_apply: false
  threshold_ms: 1000
  max_suggestions: 10
```

Use in code:
```python
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)

agent = MonitoringAgent(config)
```

## Best Practices

1. **Always use connection pooling** for production workloads
2. **Implement proper error handling** and logging
3. **Test with dry-run mode** before production
4. **Monitor resource usage** during operations
5. **Use batching** for large data operations
6. **Validate results** after migrations or changes
7. **Keep credentials secure** using environment variables

## Troubleshooting

### Connection Issues

```bash
# Test connection
python -c "from ai_shell import AIShell; \
           shell = AIShell(); \
           shell.connect('postgresql://localhost/mydb'); \
           print('Connected!')"
```

### Performance Issues

- Increase batch size for large datasets
- Adjust parallel workers
- Enable connection pooling
- Monitor resource usage

### Import Errors

```bash
# Verify installation
pip show ai-shell

# Reinstall if needed
pip install --upgrade ai-shell
```

## Contributing

Have a useful example? Contribute it!

1. Fork the repository
2. Create your example in `examples/use-cases/`
3. Add documentation to this README
4. Add tests in `tests/examples/`
5. Submit a pull request

## License

All examples are provided under the MIT License.

## Support

- Documentation: https://docs.ai-shell.io
- Issues: https://github.com/yourusername/ai-shell/issues
- Community: https://discord.gg/ai-shell
