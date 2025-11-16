# Public LLM Providers - Dual Functionality Guide

AI-Shell now supports **dual functionality** - you can use both self-hosted models (Ollama, LlamaCpp) AND public API providers (OpenAI, Claude, DeepSeek) for the three core LLM functions:

- **Intent Analysis** - Understanding database query intent
- **Code Completion** - Generating SQL and code completions
- **Data Anonymization** - Pseudo-anonymizing sensitive data

## Supported Providers

### Self-Hosted (Default)
- **Ollama** - Local models via Ollama server
- **LlamaCpp** - Local models via llama.cpp server
- **Transformers** - Hugging Face transformers library

### Public APIs (New!)
- **OpenAI** - GPT-3.5, GPT-4, GPT-4 Turbo
- **Anthropic Claude** - Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
- **DeepSeek** - DeepSeek Chat, DeepSeek Coder

## Quick Start

### 1. Set Environment Variables

Create a `.env` file in your project root:

```bash
# OpenAI (optional)
export OPENAI_API_KEY="sk-..."

# Anthropic Claude (optional)
export ANTHROPIC_API_KEY="sk-ant-..."

# DeepSeek (optional)
export DEEPSEEK_API_KEY="sk-..."
```

### 2. Configure Per-Function Providers

Edit `config/ai-shell-config.yaml`:

```yaml
llm:
  # Option 1: All self-hosted (default)
  models:
    intent: "llama2:7b"
    completion: "codellama:13b"
    anonymizer: "mistral:7b"

  # Option 2: Mix self-hosted + public APIs (dual mode)
  function_providers:
    intent:
      provider: "openai"
      model: "gpt-3.5-turbo"
      api_key_env: "OPENAI_API_KEY"

    completion:
      provider: "ollama"        # Keep local for code completion
      model: "codellama:13b"

    anonymizer:
      provider: "deepseek"
      model: "deepseek-chat"
      api_key_env: "DEEPSEEK_API_KEY"
```

### 3. Python Usage Example

```python
from src.llm.manager import LocalLLMManager, FunctionProviderConfig

# Initialize manager with per-function providers
manager = LocalLLMManager()

manager.initialize_function_providers(
    intent_config=FunctionProviderConfig(
        provider_type="openai",
        model_name="gpt-3.5-turbo",
        api_key="sk-..."  # Or reads from OPENAI_API_KEY
    ),
    completion_config=FunctionProviderConfig(
        provider_type="ollama",
        model_name="codellama:13b"
    ),
    anonymizer_config=FunctionProviderConfig(
        provider_type="deepseek",
        model_name="deepseek-chat",
        api_key="sk-..."  # Or reads from DEEPSEEK_API_KEY
    )
)

# Now use the manager - it automatically routes to the right provider
intent_result = manager.analyze_intent("SELECT * FROM users WHERE email = 'test@example.com'")
# ^ Uses OpenAI GPT-3.5

explanation = manager.explain_query("SELECT COUNT(*) FROM orders")
# ^ Uses Ollama CodeLlama

anonymized, mapping = manager.anonymize_query("SELECT * FROM users WHERE ssn = '123-45-6789'")
# ^ Uses DeepSeek
```

### 4. TypeScript Usage Example

```typescript
import { OpenAIProvider } from './src/llm/providers/openai.js';
import { DeepSeekProvider } from './src/llm/providers/deepseek.js';
import { OllamaProvider } from './src/llm/providers/ollama.js';

// Initialize providers
const intentProvider = new OpenAIProvider(
  process.env.OPENAI_API_KEY,
  'gpt-3.5-turbo'
);

const completionProvider = new OllamaProvider(
  'http://localhost:11434',
  'codellama:13b'
);

const anonymizerProvider = new DeepSeekProvider(
  process.env.DEEPSEEK_API_KEY,
  'deepseek-chat'
);

// Use for intent analysis
const intentResponse = await intentProvider.generate({
  messages: [
    { role: 'user', content: 'Analyze this query: SELECT * FROM users' }
  ],
  temperature: 0.3,
  maxTokens: 200
});

// Use for code completion
const completionResponse = await completionProvider.generate({
  messages: [
    { role: 'user', content: 'Complete this SQL: SELECT name FROM' }
  ],
  temperature: 0.7,
  maxTokens: 500
});

// Use for anonymization with streaming
await anonymizerProvider.generateStream(
  {
    messages: [
      { role: 'user', content: 'Anonymize: email@example.com' }
    ]
  },
  {
    onChunk: (chunk) => console.log(chunk),
    onComplete: (full) => console.log('Done:', full)
  }
);
```

## Provider Comparison

| Provider | Pros | Cons | Best For |
|----------|------|------|----------|
| **Ollama** | Free, private, no API limits | Requires local GPU, slower | Development, privacy-sensitive |
| **OpenAI** | Fast, high quality, reliable | Costs money, sends data to cloud | Production, quick setup |
| **Anthropic** | Very capable, good reasoning | More expensive than OpenAI | Complex queries, analysis |
| **DeepSeek** | Affordable, code-specialized | Newer, less proven | Code generation, cost-conscious |

## Configuration Patterns

### Pattern 1: All Public APIs
```yaml
function_providers:
  intent:
    provider: "openai"
    model: "gpt-3.5-turbo"
  completion:
    provider: "openai"
    model: "gpt-4"
  anonymizer:
    provider: "openai"
    model: "gpt-3.5-turbo"
```

### Pattern 2: All Self-Hosted
```yaml
models:
  intent: "llama2:7b"
  completion: "codellama:13b"
  anonymizer: "mistral:7b"
```

### Pattern 3: Hybrid (Recommended)
```yaml
function_providers:
  intent:
    provider: "openai"           # Fast intent classification
    model: "gpt-3.5-turbo"
  completion:
    provider: "ollama"           # Keep code local
    model: "codellama:13b"
  anonymizer:
    provider: "deepseek"         # Cost-effective anonymization
    model: "deepseek-chat"
```

### Pattern 4: Cost-Optimized
```yaml
function_providers:
  intent:
    provider: "deepseek"         # Cheapest option
    model: "deepseek-chat"
  completion:
    provider: "ollama"           # Free local model
    model: "codellama:13b"
  anonymizer:
    provider: "ollama"           # Free local model
    model: "mistral:7b"
```

## API Key Management

### Environment Variables (Recommended)
```bash
# .env file
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DEEPSEEK_API_KEY=sk-...
```

### Configuration File
```yaml
providers:
  openai:
    api_key_env: "OPENAI_API_KEY"
  anthropic:
    api_key_env: "ANTHROPIC_API_KEY"
  deepseek:
    api_key_env: "DEEPSEEK_API_KEY"
```

### Programmatic
```python
manager.initialize_function_providers(
    intent_config=FunctionProviderConfig(
        provider_type="openai",
        model_name="gpt-3.5-turbo",
        api_key="sk-..."  # Direct API key
    )
)
```

## Cost Considerations

| Provider | Model | Price (per 1M tokens) | Best Use Case |
|----------|-------|----------------------|---------------|
| OpenAI | gpt-3.5-turbo | Input: $0.50 / Output: $1.50 | Intent classification |
| OpenAI | gpt-4-turbo | Input: $10.00 / Output: $30.00 | Complex analysis |
| Anthropic | claude-3-haiku | Input: $0.25 / Output: $1.25 | Budget-friendly |
| Anthropic | claude-3.5-sonnet | Input: $3.00 / Output: $15.00 | High-quality completion |
| DeepSeek | deepseek-chat | Input: $0.14 / Output: $0.28 | Most affordable |
| DeepSeek | deepseek-coder | Input: $0.14 / Output: $0.28 | Code-specific tasks |
| Ollama | Any | $0.00 | All tasks (requires local GPU) |

## Error Handling

All providers handle errors gracefully:

```python
try:
    result = manager.analyze_intent(query)
except RuntimeError as e:
    print(f"Provider error: {e}")
    # Falls back to rule-based intent detection
```

## Switching Providers at Runtime

```python
# Start with OpenAI
manager.initialize_function_providers(
    intent_config=FunctionProviderConfig(
        provider_type="openai",
        model_name="gpt-3.5-turbo"
    )
)

# Switch to DeepSeek if OpenAI fails or is too expensive
manager.initialize_function_providers(
    intent_config=FunctionProviderConfig(
        provider_type="deepseek",
        model_name="deepseek-chat"
    )
)
```

## Testing with Mock Provider

For development and testing without API calls:

```python
manager.initialize(provider_type="mock", model_name="mock-model")
```

## Troubleshooting

### API Key Not Found
```
Error: No OpenAI API key found. Set OPENAI_API_KEY env var.
```
**Solution:** Set the environment variable or provide `api_key` directly.

### Connection Timeout
```
Error: OpenAI API error (timeout)
```
**Solution:** Increase timeout in config or check network connectivity.

### Invalid Model
```
Error: Unknown model: gpt-5
```
**Solution:** Check supported models for each provider.

## Supported Models

### OpenAI
- gpt-3.5-turbo
- gpt-4
- gpt-4-turbo
- gpt-4-turbo-preview

### Anthropic
- claude-3-5-sonnet-20241022
- claude-3-opus-20240229
- claude-3-sonnet-20240229
- claude-3-haiku-20240307

### DeepSeek
- deepseek-chat
- deepseek-coder

### Ollama (Self-Hosted)
- llama2, llama2:7b, llama2:13b, llama2:70b
- codellama, codellama:7b, codellama:13b, codellama:34b
- mistral, mistral:7b
- Any model available in Ollama registry

## Security Best Practices

1. **Never commit API keys** - Use environment variables
2. **Use .gitignore** - Exclude `.env` files
3. **Rotate keys regularly** - Especially if exposed
4. **Monitor usage** - Set billing alerts on provider dashboards
5. **Use least privilege** - Create separate API keys for different environments

## Next Steps

- [API Reference](./API_REFERENCE.md)
- [Configuration Guide](./CONFIGURATION.md)
- [Performance Tuning](./PERFORMANCE.md)
- [Security Guide](./SECURITY.md)
