# Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### Python Version Mismatch

**Problem:** Error during installation about Python version

```bash
ERROR: AI-Shell requires Python 3.11 or later
```

**Solution:**
```bash
# Check Python version
python --version

# Install Python 3.11+ (Ubuntu/Debian)
sudo apt update
sudo apt install python3.11 python3.11-venv

# Use specific version
python3.11 -m venv venv
source venv/bin/activate
pip install ai-shell
```

#### Package Conflicts

**Problem:** Dependency conflicts during pip install

```bash
ERROR: pip's dependency resolver does not currently take into account
all the packages that are installed
```

**Solution:**
```bash
# Create fresh virtual environment
python3.11 -m venv --clear venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install AI-Shell
pip install ai-shell

# Or install from requirements with --no-deps for testing
pip install --no-deps ai-shell
pip install -r requirements.txt
```

### LLM Provider Issues

#### Ollama Connection Failed

**Problem:** Cannot connect to Ollama

```bash
Error: Could not connect to Ollama at localhost:11434
```

**Solution:**
```bash
# 1. Check if Ollama is running
systemctl status ollama

# 2. Start Ollama if stopped
systemctl start ollama

# Or run manually
ollama serve

# 3. Test connection
curl http://localhost:11434/api/tags

# 4. Check firewall
sudo ufw allow 11434

# 5. Verify in AI-Shell config
cat ~/.ai-shell/config.yaml | grep -A 5 ollama
```

#### Ollama Model Not Found

**Problem:** Model not available error

```bash
Error: model 'llama2:7b' not found
```

**Solution:**
```bash
# List installed models
ollama list

# Pull required model
ollama pull llama2:7b
ollama pull codellama:13b
ollama pull mistral:7b

# Verify download
ollama list

# Test model
ollama run llama2:7b "test prompt"
```

#### OpenAI API Key Issues

**Problem:** Invalid API key or authentication error

```bash
Error: Invalid API key provided
```

**Solution:**
```bash
# 1. Verify API key in vault
ai-shell
AI$ > vault get openai_key

# 2. Update API key
AI$ > vault update openai_key
Enter new value: sk-...

# 3. Or use environment variable
export OPENAI_API_KEY="sk-..."

# 4. Test connection
AI$ > llm test openai

# 5. Check rate limits
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

#### High LLM Latency

**Problem:** Slow AI responses

**Solution:**
```yaml
# config.yaml - Optimize settings

llm:
  # Use local LLM for speed
  provider: ollama

  ollama:
    # Reduce max tokens
    num_predict: 512  # Instead of 2048

    # Enable GPU
    gpu: true
    gpu_layers: 35

    # Keep model loaded
    keep_alive: 30m

  # Set timeouts
  timeout: 10

  # Enable caching
  cache_responses: true
  cache_ttl: 3600
```

### Database Connection Issues

#### Oracle Thin Mode Not Working

**Problem:** Error about Oracle client not found

```bash
Error: Oracle Client library has not been initialized
```

**Solution:**
```python
# Verify cx_Oracle version supports thin mode
pip show cx-Oracle
# Must be >= 8.0

# Check config.yaml
mcp:
  oracle:
    thin_mode: true  # MUST be true

# Test thin mode explicitly
python3 << 'EOF'
import cx_Oracle
# This is the key - lib_dir=None enables thin mode
cx_Oracle.init_oracle_client(lib_dir=None)
print("Thin mode enabled successfully")
EOF
```

**Alternative if thin mode fails:**
```bash
# Install Oracle Instant Client (if thin mode not available)
# Download from: https://www.oracle.com/database/technologies/instant-client/downloads.html

# Ubuntu/Debian
sudo apt install alien
alien -i oracle-instantclient-basic-*.rpm

# Set LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/usr/lib/oracle/21/client64/lib:$LD_LIBRARY_PATH

# Update config to use thick mode
mcp:
  oracle:
    thin_mode: false
```

#### PostgreSQL SSL Certificate Error

**Problem:** SSL certificate verification failed

```bash
Error: SSL error: certificate verify failed
```

**Solution:**
```yaml
# config.yaml - Adjust SSL mode

mcp:
  postgresql:
    # Option 1: Disable SSL (development only)
    sslmode: disable

    # Option 2: Prefer SSL but don't verify
    sslmode: prefer

    # Option 3: Require SSL with CA verification
    sslmode: verify-full
    sslrootcert: /path/to/ca-cert.pem

# Or use environment variable
export PGSSLMODE=prefer
```

#### Database Connection Timeout

**Problem:** Connection timeout errors

```bash
Error: could not connect to server: Connection timed out
```

**Solution:**
```yaml
# config.yaml - Increase timeouts

mcp:
  oracle:
    timeout: 60  # Increase from 30
    connect_timeout: 30  # Increase from 10

  postgresql:
    timeout: 60
    connect_timeout: 30

# Check network connectivity
ping database-host.example.com

# Test port access
nc -zv database-host.example.com 1521

# Check firewall rules
sudo ufw status
```

#### Connection Pool Exhausted

**Problem:** All connections busy error

```bash
Error: connection pool exhausted
```

**Solution:**
```yaml
# config.yaml - Increase pool size

mcp:
  oracle:
    connection_pool_size: 15  # Increase from 5
    max_pool_size: 25

  postgresql:
    connection_pool_size: 15
    max_pool_size: 25

# Or check for connection leaks
AI$ > db pool status

# Kill idle connections
AI$ > db pool cleanup
```

### UI and Display Issues

#### Garbled or Incorrect Display

**Problem:** UI elements not rendering correctly

**Solution:**
```bash
# 1. Check terminal capabilities
echo $TERM
# Should be: xterm-256color or screen-256color

# 2. Set proper TERM
export TERM=xterm-256color

# 3. Update terminal emulator
# Recommended: alacritty, kitty, wezterm

# 4. Disable features if needed
# config.yaml
ui:
  syntax_highlighting: false  # If colors broken
  auto_size_panels: false     # If sizing broken
```

#### Panels Not Updating

**Problem:** Module panel not showing updates

**Solution:**
```yaml
# config.yaml - Check update settings

ui:
  module_panel:
    update_interval: 500  # Reduce for faster updates

performance:
  async_workers: 8  # Increase workers

# Check event bus
AI$ > debug events status

# Restart AI-Shell
exit
ai-shell
```

#### Text Overflow or Truncation

**Problem:** Output cut off or wrapped incorrectly

**Solution:**
```yaml
# config.yaml - Adjust output settings

ui:
  output:
    max_table_width: null  # Auto-detect terminal width
    word_wrap: true
    auto_page: true
    page_threshold: 50

# Or use less pager
AI$ > SELECT * FROM large_table | less
```

### Performance Issues

#### High Memory Usage

**Problem:** AI-Shell consuming too much memory

**Solution:**
```yaml
# config.yaml - Reduce memory footprint

performance:
  # Reduce caches
  cache_size: 500  # Reduce from 1000
  command_history_size: 5000

  # Memory limits
  max_memory_mb: 1024

  # Garbage collection
  gc_threshold: 700

mcp:
  # Reduce connection pools
  oracle:
    connection_pool_size: 3
    max_pool_size: 5

# Monitor memory
AI$ > debug memory

# Clear caches
AI$ > cache clear
```

#### Slow Auto-completion

**Problem:** Completion suggestions take too long

**Solution:**
```yaml
# config.yaml - Optimize completion

autocomplete:
  # Reduce similarity threshold
  min_similarity: 0.7  # Higher = fewer results

  # Limit vector search
  vector_top_k: 5  # Reduce from 10

  # Disable heavy sources
  sources:
    - commands
    - files
    # - database_objects  # Disable if slow
    # - vault_secrets

# Rebuild vector index
AI$ > vector rebuild --optimize
```

#### Background Tasks Blocking

**Problem:** Background enrichment blocking UI

**Solution:**
```yaml
# config.yaml - Tune async processing

performance:
  async_workers: 16  # Increase workers

  # Background task priorities
  background_tasks:
    - intent_analysis: priority_low
    - panel_enrichment: priority_low
    - vector_indexing: priority_low

# Disable features if needed
modules:
  ai_helper:
    enable_agents: false  # If causing issues
```

### Vault and Security Issues

#### Cannot Access Vault

**Problem:** Keyring access denied

```bash
Error: Could not access keyring
```

**Solution:**
```bash
# 1. Check keyring backend
python3 -c "import keyring; print(keyring.get_keyring())"

# 2. Install keyring backend (Ubuntu)
sudo apt install gnome-keyring

# 3. Or use file-based vault
# config.yaml
security:
  vault_backend: file
  vault_file: ~/.ai-shell/vault.enc

# 4. Unlock keyring
gnome-keyring-daemon --unlock

# 5. Reset vault if corrupted
ai-shell
AI$ > vault reset
```

#### Secrets Not Auto-redacting

**Problem:** Passwords visible in history

**Solution:**
```yaml
# config.yaml - Verify redaction settings

security:
  auto_redaction: true

  # Add custom patterns
  redaction_patterns:
    - type: password
      regex: 'password[:=]\s*([^\s,]+)'

# Test redaction
AI$ > debug redaction test "password=secret123"

# Clear history if leaked
AI$ > history clear
```

### Module Issues

#### Module Failed to Load

**Problem:** Module initialization error

```bash
Error: Module 'database' failed to initialize
```

**Solution:**
```bash
# 1. Check module dependencies
AI$ > debug modules dependencies

# 2. View error details
AI$ > debug modules errors database

# 3. Disable problematic module
# config.yaml
modules:
  database:
    enabled: false

# 4. Reinstall module
pip uninstall ai-shell-database
pip install ai-shell-database

# 5. Check logs
tail -f ~/.ai-shell/logs/ai-shell.log
```

#### Custom Module Not Recognized

**Problem:** Custom plugin not loading

```bash
Error: Plugin 'my-plugin' not found
```

**Solution:**
```bash
# 1. Check plugin directory
ls -la ~/.ai-shell/plugins/

# 2. Verify plugin structure
my-plugin/
├── __init__.py  # Must have register() function
├── commands.py
└── config.yaml

# 3. Check plugin registration
# __init__.py must have:
def register(shell):
    return MyModule()

# 4. Reload plugins
AI$ > plugins reload

# 5. Enable in config
# config.yaml
plugins:
  enabled: true
  installed:
    - name: my-plugin
      enabled: true
```

## Debugging Tools

### Built-in Debug Commands

```bash
# System health
AI$ > debug health

# Component status
AI$ > debug status --all

# Memory usage
AI$ > debug memory

# Event bus
AI$ > debug events

# LLM providers
AI$ > llm health

# Database connections
AI$ > db health

# Performance metrics
AI$ > debug performance
```

### Log Analysis

```bash
# View real-time logs
tail -f ~/.ai-shell/logs/ai-shell.log

# Error logs only
grep ERROR ~/.ai-shell/logs/ai-shell.log

# LLM requests
grep "LLM Request" ~/.ai-shell/logs/llm.log

# Database queries
grep "SQL Execute" ~/.ai-shell/logs/database.log

# Audit trail
tail -f ~/.ai-shell/logs/audit.log
```

### Verbose Mode

```bash
# Enable debug logging
export AI_SHELL_DEBUG=1
ai-shell

# Or in config
# config.yaml
system:
  log_level: DEBUG

# Per-component logging
logging:
  llm:
    level: DEBUG
  database:
    level: DEBUG
  mcp:
    level: DEBUG
```

## Getting Help

### Collect Diagnostic Information

```bash
# Generate diagnostic report
AI$ > debug report --output ~/ai-shell-debug.txt

# Report includes:
# - System information
# - Configuration (redacted)
# - Component status
# - Recent errors
# - Performance metrics
```

### Community Support

- GitHub Issues: https://github.com/yourusername/ai-shell/issues
- Discussions: https://github.com/yourusername/ai-shell/discussions
- Discord: https://discord.gg/ai-shell
- Stack Overflow: Tag `ai-shell`

### Bug Reports

When reporting issues, include:

1. AI-Shell version: `ai-shell --version`
2. Python version: `python --version`
3. Operating system: `uname -a`
4. Relevant config (redacted)
5. Error messages and logs
6. Steps to reproduce

### Feature Requests

Use GitHub Discussions for feature requests:
- Describe the use case
- Explain expected behavior
- Provide examples
- Consider implementation approach

## Quick Fixes Checklist

- [ ] Restart AI-Shell
- [ ] Check configuration syntax
- [ ] Verify credentials in vault
- [ ] Test LLM provider connectivity
- [ ] Check database connection
- [ ] Review recent logs
- [ ] Clear caches
- [ ] Update dependencies
- [ ] Restart Ollama (if using local LLM)
- [ ] Check disk space
- [ ] Verify file permissions

## Next Steps

- [Configuration Guide](./configuration.md) - Detailed config options
- [Architecture Overview](../architecture/overview.md) - System design
- [API Reference](../api/core.md) - Development docs
