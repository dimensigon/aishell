# LLM Provider Setup Guide

## Overview

AI-Shell supports multiple LLM providers for AI-powered assistance, including local models (Ollama, LocalAI) and cloud providers (OpenAI, Anthropic, DeepSeek). This guide covers setup and configuration for each provider.

## Supported Providers

| Provider | Type | Privacy | Latency | Cost | Best For |
|----------|------|---------|---------|------|----------|
| Ollama | Local | High | Low | Free | Development, sensitive data |
| LocalAI | Local | High | Low | Free | Custom models, privacy |
| OpenAI | Cloud | Medium | Low | Paid | Production, advanced features |
| Anthropic | Cloud | Medium | Low | Paid | Complex reasoning |
| DeepSeek | Cloud | Medium | Low | Paid | Cost-effective |

## Local LLM Providers

### Ollama Setup

Ollama provides easy local LLM hosting with multiple model formats.

#### Installation

```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# Windows (PowerShell as Administrator)
iwr https://ollama.com/install.ps1 -useb | iex

# Verify installation
ollama --version
```

#### Download Models

```bash
# Intent analysis (lightweight, fast)
ollama pull llama2:7b

# Code completion
ollama pull codellama:13b

# Data anonymization
ollama pull mistral:7b

# General purpose (larger, more capable)
ollama pull llama2:13b

# List installed models
ollama list
```

#### Configuration

Edit `~/.ai-shell/config.yaml`:

```yaml
llm:
  provider: ollama
  ollama:
    host: http://localhost:11434
    models:
      intent: llama2:7b
      completion: codellama:13b
      anonymizer: mistral:7b
      general: llama2:13b

    # Performance settings
    num_predict: 1024  # Max tokens
    temperature: 0.7
    top_k: 40
    top_p: 0.9

    # Timeout settings
    timeout: 30
    stream: true  # Enable streaming responses
```

#### Model Abbreviations

```yaml
# Define shortcuts for quick model selection
llm:
  ollama:
    abbreviations:
      l2: llama2:7b
      cl: codellama:13b
      m7: mistral:7b
      l13: llama2:13b
```

Usage:
```bash
# Use specific model with abbreviation
AI$ > #ai:l13 explain this SQL query
```

#### Advanced Ollama Configuration

```yaml
llm:
  ollama:
    # GPU acceleration
    gpu: true
    gpu_layers: 35  # Number of layers on GPU

    # Model loading
    keep_alive: 5m  # Keep model in memory

    # System prompts
    system_prompts:
      intent: "You are a shell command analyzer. Provide concise, accurate analysis."
      completion: "You are a code completion assistant. Generate only the code needed."
      anonymizer: "You detect and anonymize sensitive data while preserving structure."
```

### LocalAI Setup

LocalAI provides OpenAI-compatible API for local models.

#### Installation

```bash
# Docker installation
docker run -p 8080:8080 \
  -v $PWD/models:/models \
  -v $PWD/prompts:/prompts \
  quay.io/go-skynet/local-ai:latest

# Binary installation
curl -Lo local-ai https://github.com/go-skynet/LocalAI/releases/latest/download/local-ai-Linux-x86_64
chmod +x local-ai
./local-ai
```

#### Configuration

```yaml
llm:
  provider: local-ai
  local_ai:
    base_url: http://localhost:8080
    api_key: null  # No key needed for local

    models:
      intent: gpt-3.5-turbo  # Model name in LocalAI
      completion: codellama
      general: llama-2-7b

    # OpenAI-compatible settings
    temperature: 0.7
    max_tokens: 1024
```

## Cloud LLM Providers

### OpenAI Setup

#### API Key Configuration

```bash
# Add API key to vault
AI$ > vault add openai_key --type standard
Enter value: sk-...your-api-key...

# Or use environment variable
export OPENAI_API_KEY="sk-...your-api-key..."
```

#### Configuration

```yaml
llm:
  provider: openai
  openai:
    api_key: $vault.openai_key
    base_url: https://api.openai.com/v1

    models:
      intent: gpt-3.5-turbo
      completion: gpt-4
      general: gpt-4-turbo-preview

    # Request settings
    temperature: 0.7
    max_tokens: 2048
    top_p: 1.0
    frequency_penalty: 0.0
    presence_penalty: 0.0

    # Rate limiting
    max_requests_per_minute: 60
    max_tokens_per_minute: 90000
```

### Anthropic (Claude) Setup

#### API Key Configuration

```bash
# Add API key
AI$ > vault add anthropic_key --type standard
Enter value: sk-ant-...your-api-key...
```

#### Configuration

```yaml
llm:
  provider: anthropic
  anthropic:
    api_key: $vault.anthropic_key
    base_url: https://api.anthropic.com/v1

    models:
      intent: claude-3-haiku-20240307
      completion: claude-3-sonnet-20240229
      general: claude-3-opus-20240229

    # Model settings
    max_tokens: 4096
    temperature: 0.7

    # System prompts
    system_prompt: "You are a helpful AI assistant for shell operations."
```

### DeepSeek Setup

#### API Key Configuration

```bash
# Add API key
AI$ > vault add deepseek_key --type standard
Enter value: ...your-api-key...
```

#### Configuration

```yaml
llm:
  provider: deepseek
  deepseek:
    api_key: $vault.deepseek_key
    base_url: https://api.deepseek.com/v1

    models:
      intent: deepseek-chat
      completion: deepseek-coder
      general: deepseek-chat

    # Model parameters
    temperature: 0.7
    max_tokens: 2048
```

## Multi-Provider Configuration

### Fallback Strategy

Configure multiple providers with automatic fallback:

```yaml
llm:
  # Primary provider
  provider: ollama

  # Fallback chain
  fallback:
    - provider: openai
      condition: ollama_unavailable
    - provider: anthropic
      condition: openai_rate_limit

  # Provider configurations
  ollama:
    host: http://localhost:11434
    models:
      intent: llama2:7b

  openai:
    api_key: $vault.openai_key
    models:
      intent: gpt-3.5-turbo

  anthropic:
    api_key: $vault.anthropic_key
    models:
      intent: claude-3-haiku-20240307
```

### Hybrid Strategy

Use different providers for different tasks:

```yaml
llm:
  # Task-specific providers
  providers:
    intent:
      provider: ollama
      model: llama2:7b
      reason: "Fast, local, privacy-safe"

    completion:
      provider: openai
      model: gpt-4
      reason: "Best code quality"

    anonymizer:
      provider: ollama
      model: mistral:7b
      reason: "Sensitive data stays local"

    general:
      provider: anthropic
      model: claude-3-opus-20240229
      reason: "Complex reasoning"
```

## Model Selection Guide

### Intent Analysis

**Requirements:** Fast, lightweight, privacy-safe

**Recommended:**
- Local: `llama2:7b` (Ollama) - 5-10ms latency
- Cloud: `gpt-3.5-turbo` (OpenAI) - 100-200ms latency

### Code Completion

**Requirements:** Accurate, context-aware

**Recommended:**
- Local: `codellama:13b` (Ollama) - 50-100ms latency
- Cloud: `gpt-4` (OpenAI) - 300-500ms latency

### Data Anonymization

**Requirements:** Privacy-preserving, pattern recognition

**Recommended:**
- Local: `mistral:7b` (Ollama) - Must be local for sensitive data
- Cloud: Never use cloud for sensitive data anonymization

### General Assistance

**Requirements:** Complex reasoning, multi-step tasks

**Recommended:**
- Local: `llama2:13b` (Ollama) - Good balance
- Cloud: `claude-3-opus` (Anthropic) - Best reasoning

## Usage Examples

### Model Selection in Commands

```bash
# Use default provider/model
AI$ > #ai explain this command
AI$ > ps aux | grep nginx

# Specify provider with abbreviation
AI$ > #ai:openai explain with detailed analysis
AI$ > ps aux | grep nginx

# Specify exact model
AI$ > #ai:anthropic:claude-3-opus complex query analysis
AI$ > SELECT * FROM users WHERE ...
```

### File Editor AI Integration

```bash
AI$ > edit app.py

# Inside editor, use model selection
#ai:codellama add error handling for database connections

#ai:gpt-4 refactor this function to be more efficient

#ai:local optimize for performance
```

### Background Analysis

```bash
# Intent analysis (automatic, uses configured intent model)
AI$ > rm -rf /var/log/*
# Background: Ollama llama2:7b analyzing risk...

# Explicit model for complex analysis
AI$ > #ai:claude analyze impact and suggest alternatives
AI$ > rm -rf /var/log/*
```

## Performance Optimization

### Local Model Optimization

```yaml
llm:
  ollama:
    # Preload models at startup
    preload_models: true
    preload_list:
      - llama2:7b
      - codellama:13b

    # GPU optimization
    gpu: true
    gpu_layers: 35

    # Memory management
    keep_alive: 10m  # Keep in memory longer

    # Context window
    num_ctx: 4096  # Larger context for better results
```

### Cloud Provider Optimization

```yaml
llm:
  openai:
    # Caching
    cache_responses: true
    cache_ttl: 3600

    # Batching
    batch_requests: true
    batch_size: 5
    batch_timeout: 100  # ms

    # Rate limiting
    max_concurrent_requests: 10
```

### Response Streaming

```yaml
llm:
  # Enable streaming for better UX
  stream_responses: true

  # Provider-specific streaming
  ollama:
    stream: true

  openai:
    stream: true

  anthropic:
    stream: true
```

## Privacy & Security

### Data Handling

```yaml
security:
  # Use local LLM for sensitive operations
  sensitive_data_handler: ollama

  # Auto-redaction before cloud calls
  auto_redact_for_cloud: true
  redaction_patterns:
    - ip_addresses
    - email_addresses
    - passwords
    - api_keys
    - user_paths

  # Anonymization
  pseudo_anonymize: true
  anonymization_map_storage: encrypted
```

### Provider-Specific Security

```yaml
llm:
  openai:
    # Disable data retention
    disable_training: true

    # Request headers
    headers:
      OpenAI-Organization: your-org-id

  anthropic:
    # Privacy headers
    headers:
      anthropic-version: "2023-06-01"
```

## Monitoring & Debugging

### Enable LLM Logging

```yaml
logging:
  llm:
    level: INFO
    file: ~/.ai-shell/logs/llm.log

    # Log requests/responses
    log_requests: true
    log_responses: true

    # Performance metrics
    log_latency: true
    log_token_usage: true
```

### Health Checks

```bash
# Check LLM provider status
AI$ > llm health

LLM Provider Health:
├── Ollama (localhost:11434)
│   ├── Status: ✓ Healthy
│   ├── Models: 4 loaded
│   └── Latency: 8ms
│
├── OpenAI (api.openai.com)
│   ├── Status: ✓ Healthy
│   ├── Rate Limit: 45/60 rpm
│   └── Latency: 156ms
│
└── Anthropic (api.anthropic.com)
    ├── Status: ✓ Healthy
    ├── Credits: 85%
    └── Latency: 203ms

# Test specific provider
AI$ > llm test ollama
Testing Ollama...
✓ Connection successful
✓ Model llama2:7b responsive
✓ Average latency: 12ms
```

### Usage Statistics

```bash
# View token usage
AI$ > llm stats

Token Usage (Last 24h):
┌──────────┬──────────┬─────────┬──────┐
│ Provider │ Requests │ Tokens  │ Cost │
├──────────┼──────────┼─────────┼──────┤
│ Ollama   │ 234      │ 45,892  │ $0   │
│ OpenAI   │ 12       │ 8,234   │ $0.42│
│ Anthropic│ 5        │ 3,120   │ $0.18│
└──────────┴──────────┴─────────┴──────┘

Total Cost: $0.60
```

## Troubleshooting

### Ollama Issues

**Model not found**
```bash
# List available models
ollama list

# Pull missing model
ollama pull llama2:7b
```

**Connection refused**
```bash
# Check Ollama service
systemctl status ollama

# Start Ollama
systemctl start ollama

# Or run manually
ollama serve
```

**Slow responses**
```yaml
# Optimize for speed
llm:
  ollama:
    num_predict: 512  # Reduce max tokens
    gpu: true  # Enable GPU
    keep_alive: 30m  # Keep model loaded
```

### Cloud Provider Issues

**Rate limit errors**
```yaml
llm:
  openai:
    max_requests_per_minute: 30  # Reduce rate
    retry_on_rate_limit: true
    retry_delay: 2  # seconds
```

**API key invalid**
```bash
# Verify API key
AI$ > vault get openai_key

# Update API key
AI$ > vault update openai_key
```

**High latency**
```yaml
llm:
  # Add timeout and fallback
  timeout: 10
  fallback:
    - provider: ollama  # Fall back to local
      condition: cloud_timeout
```

## Best Practices

### 1. Local First for Sensitive Data

```yaml
# Always use local LLM for sensitive operations
llm:
  providers:
    anonymizer:
      provider: ollama  # Never cloud
      model: mistral:7b
```

### 2. Cost Optimization

```yaml
# Use cheaper models for simple tasks
llm:
  providers:
    intent:
      provider: openai
      model: gpt-3.5-turbo  # Cheaper

    complex_reasoning:
      provider: openai
      model: gpt-4  # More expensive, only when needed
```

### 3. Fallback Strategy

```yaml
# Always have local fallback
llm:
  provider: openai
  fallback:
    - provider: ollama
      condition: always  # Local always available
```

### 4. Model Versioning

```yaml
# Pin model versions for consistency
llm:
  openai:
    models:
      intent: gpt-3.5-turbo-0125  # Specific version
      completion: gpt-4-0613
```

## Next Steps

- [Custom Command Development](./custom-commands.md) - Extend AI capabilities
- [Database Module](./database-module.md) - AI-powered database operations
- [MCP Integration](./mcp-integration.md) - Database connectivity

## Support

- Ollama: https://ollama.com/docs
- OpenAI: https://platform.openai.com/docs
- Anthropic: https://docs.anthropic.com
- AI-Shell Issues: https://github.com/yourusername/ai-shell/issues
