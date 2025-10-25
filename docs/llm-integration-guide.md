# LLM Integration Layer - Implementation Guide

## Overview

AI-Shell's LLM integration layer provides a unified interface for interacting with local LLM providers, enabling database assistance, SQL generation, and intelligent query analysis.

## Architecture

### Core Components

1. **Provider Interface** (`src/llm/provider.ts`)
   - Abstract base class `ILLMProvider`
   - Standardized methods across all providers
   - Consistent error handling

2. **Supported Providers**
   - **Ollama** (`src/llm/providers/ollama.ts`) - Chat-based models
   - **LlamaCPP** (`src/llm/providers/llamacpp.ts`) - Completion-based models

3. **Context Formatter** (`src/llm/context-formatter.ts`)
   - Schema-aware prompt engineering
   - Conversation history management
   - Token optimization

4. **Response Parser** (`src/llm/response-parser.ts`)
   - SQL query extraction
   - Code block parsing
   - Table data extraction
   - Error detection

5. **Provider Factory** (`src/llm/provider-factory.ts`)
   - Provider instantiation
   - Auto-detection
   - Configuration management

## Provider Support

### Ollama Integration

**Features:**
- Chat API support
- Real-time streaming
- Model management (pull, delete, list)
- Health checks

**API Endpoints:**
- `POST /api/chat` - Generate chat responses
- `GET /api/tags` - List models
- `POST /api/pull` - Download models
- `DELETE /api/delete` - Remove models

**Example:**
```typescript
const provider = new OllamaProvider('http://localhost:11434', 'llama2');

const response = await provider.generate({
  messages: [
    { role: 'user', content: 'Write a SQL query' }
  ]
});
```

### LlamaCPP Integration

**Features:**
- Completion API support
- Token-level streaming
- Tokenization utilities
- Model introspection

**API Endpoints:**
- `POST /completion` - Generate completions
- `GET /health` - Health check
- `POST /tokenize` - Convert text to tokens
- `POST /detokenize` - Convert tokens to text

**Example:**
```typescript
const provider = new LlamaCppProvider('http://localhost:8080', 'default');

const response = await provider.generate({
  messages: [
    { role: 'user', content: 'Explain indexing' }
  ]
});
```

## Streaming Support

Both providers support real-time streaming responses:

```typescript
await provider.generateStream(
  { messages: [{ role: 'user', content: 'Query' }] },
  {
    onChunk: (chunk) => console.log(chunk),
    onComplete: (full) => console.log('Done:', full),
    onError: (err) => console.error(err)
  }
);
```

## Context Formatting

### Basic Query
```typescript
const formatter = new ContextFormatter();
const messages = formatter.formatQuery('Find all active users');
```

### Schema-Aware Queries
```typescript
const messages = formatter.formatWithSchema(
  'Show users with orders',
  {
    tables: [
      { name: 'users', columns: [...] },
      { name: 'orders', columns: [...] }
    ]
  }
);
```

### SQL Analysis
```typescript
const messages = formatter.formatSQLAnalysis(sqlQuery);
```

### Database Design
```typescript
const messages = formatter.formatDatabaseDesign(requirements);
```

### Conversation History
```typescript
const messages = formatter.formatConversation(
  'Current query',
  [
    { user: 'Previous question', assistant: 'Previous answer' }
  ],
  { includeHistory: true, compressionLevel: 'low' }
);
```

## Response Parsing

Extract structured data from LLM responses:

```typescript
const parser = new ResponseParser();
const parsed = parser.parse(llmResponse);

// Access parsed data
console.log(parsed.text);          // Clean text
console.log(parsed.codeBlocks);    // Code blocks with language
console.log(parsed.sqlQueries);    // Extracted SQL
console.log(parsed.jsonData);      // Parsed JSON
console.log(parsed.tables);        // Markdown tables
console.log(parsed.hasError);      // Error detection
```

### Advanced Parsing

```typescript
// Extract CREATE TABLE statements
const schemas = parser.extractSchema(response);

// Extract action items
const items = parser.extractActionItems(response);

// Format SQL for display
const formatted = parser.formatSQL(sqlQuery);
```

## Provider Factory

### Create Provider
```typescript
const config: LLMConfig = {
  provider: 'ollama',
  baseUrl: 'http://localhost:11434',
  model: 'llama2',
  temperature: 0.7,
  maxTokens: 2000,
  stream: false
};

const provider = ProviderFactory.createProvider(config);
```

### Auto-detect Available Providers
```typescript
const providers = await ProviderFactory.detectProviders();

for (const p of providers) {
  console.log(`${p.provider}: ${p.available ? 'available' : 'unavailable'}`);
}
```

### Get Default Configuration
```typescript
const config = ProviderFactory.getDefaultConfig('ollama');
```

## Configuration

### Environment Variables
```bash
# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# LlamaCPP
LLAMACPP_BASE_URL=http://localhost:8080
LLAMACPP_MODEL=default

# Common
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
LLM_TIMEOUT=30000
```

### Runtime Configuration
```typescript
const config: LLMConfig = {
  provider: 'ollama',
  baseUrl: process.env.OLLAMA_BASE_URL || 'http://localhost:11434',
  model: process.env.OLLAMA_MODEL || 'llama2',
  temperature: parseFloat(process.env.LLM_TEMPERATURE || '0.7'),
  maxTokens: parseInt(process.env.LLM_MAX_TOKENS || '2000'),
  timeout: parseInt(process.env.LLM_TIMEOUT || '30000')
};
```

## Error Handling

All providers implement consistent error handling:

```typescript
try {
  const response = await provider.generate(options);
} catch (error) {
  // Error format: "{Provider} {operation} failed: {details}"
  console.error(error.message);
}
```

Common error scenarios:
- Connection failures (provider not running)
- Timeout errors (slow responses)
- Invalid model (model not found)
- API errors (malformed requests)

## Best Practices

### 1. Connection Testing
```typescript
const isAvailable = await provider.testConnection();
if (!isAvailable) {
  console.error('Provider not available');
  return;
}
```

### 2. Provider Caching
```typescript
// Factory automatically caches providers
const provider1 = ProviderFactory.createProvider(config);
const provider2 = ProviderFactory.createProvider(config);
// provider1 === provider2 (same instance)
```

### 3. Token Management
```typescript
const formatter = new ContextFormatter();
const tokenCount = formatter.estimateTokens(text);
const truncated = formatter.truncateMessages(messages, maxTokens);
```

### 4. Streaming for Long Responses
```typescript
// Use streaming for better UX
if (expectedLongResponse) {
  await provider.generateStream(options, callbacks);
} else {
  await provider.generate(options);
}
```

### 5. Schema Context
```typescript
// Always include schema for SQL queries
const messages = formatter.formatWithSchema(query, dbSchema);
```

## Integration with AI-Shell

### CLI Integration
```typescript
// In CLI command handler
const provider = ProviderFactory.createProvider(cliConfig.llm);
const formatter = new ContextFormatter();
const parser = new ResponseParser();

const messages = formatter.formatQuery(userQuery);
const response = await provider.generate({ messages });
const parsed = parser.parse(response.content);

// Display parsed SQL
if (parsed.sqlQueries.length > 0) {
  console.log('Generated SQL:');
  parsed.sqlQueries.forEach(sql => console.log(parser.formatSQL(sql)));
}
```

### MCP Integration
```typescript
// In MCP tool handler
export async function handleLLMQuery(params: any) {
  const provider = ProviderFactory.createProvider(params.config);
  const response = await provider.generate({
    messages: params.messages
  });

  return {
    content: response.content,
    usage: response.usage
  };
}
```

## Performance Considerations

1. **Provider Caching**: Factory caches provider instances
2. **Token Estimation**: Rough estimate at ~4 chars/token
3. **History Compression**: Configurable levels (none/low/high)
4. **Streaming**: Reduces perceived latency
5. **Connection Pooling**: Axios instances are reused

## Testing

See `/home/claude/dbacopilot/examples/llm-usage-example.ts` for comprehensive examples.

## Troubleshooting

### Ollama Not Available
```bash
# Start Ollama
ollama serve

# Pull a model
ollama pull llama2
```

### LlamaCPP Not Available
```bash
# Start llama.cpp server
./llama-server -m model.gguf -c 2048 --port 8080
```

### Timeout Errors
```typescript
// Increase timeout
const config: LLMConfig = {
  ...baseConfig,
  timeout: 60000 // 60 seconds
};
```

## Future Enhancements

Potential additions:
- OpenAI-compatible API support
- Local Anthropic Claude integration
- Multi-model ensembles
- Async batch processing
- Response caching
- Fine-tuning support

## Files Reference

| File | Purpose |
|------|---------|
| `/src/types/llm.ts` | Type definitions |
| `/src/llm/provider.ts` | Base provider interface |
| `/src/llm/providers/ollama.ts` | Ollama implementation |
| `/src/llm/providers/llamacpp.ts` | LlamaCPP implementation |
| `/src/llm/context-formatter.ts` | Prompt engineering |
| `/src/llm/response-parser.ts` | Response parsing |
| `/src/llm/provider-factory.ts` | Provider management |
| `/src/llm/index.ts` | Main exports |
| `/examples/llm-usage-example.ts` | Usage examples |
