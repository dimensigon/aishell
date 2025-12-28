/**
 * LLM Integration Usage Examples
 * Demonstrates how to use the AI-Shell LLM integration layer
 */

import {
  ProviderFactory,
  ContextFormatter,
  ResponseParser,
  type LLMConfig,
  type StreamCallback,
} from '../src/llm/index.js';

// Example 1: Basic Query with Ollama
async function basicOllamaExample() {
  console.log('=== Example 1: Basic Ollama Query ===\n');

  const config: LLMConfig = {
    provider: 'ollama',
    baseUrl: 'http://localhost:11434',
    model: 'llama2',
    temperature: 0.7,
    maxTokens: 2000,
  };

  const provider = ProviderFactory.createProvider(config);

  // Test connection
  const isAvailable = await provider.testConnection();
  console.log(`Ollama available: ${isAvailable}\n`);

  if (isAvailable) {
    const response = await provider.generate({
      messages: [
        {
          role: 'user',
          content: 'Write a SQL query to find all users who registered in the last 30 days',
        },
      ],
    });

    console.log('Response:', response.content);
    console.log('\nUsage:', response.usage);
  }
}

// Example 2: Streaming Response
async function streamingExample() {
  console.log('\n=== Example 2: Streaming Response ===\n');

  const provider = ProviderFactory.createProvider({
    provider: 'ollama',
    baseUrl: 'http://localhost:11434',
    model: 'llama2',
  });

  const callback: StreamCallback = {
    onChunk: (chunk) => {
      process.stdout.write(chunk);
    },
    onComplete: (fullResponse) => {
      console.log('\n\n✓ Streaming complete');
      console.log(`Total length: ${fullResponse.length} characters`);
    },
    onError: (error) => {
      console.error('Stream error:', error.message);
    },
  };

  await provider.generateStream(
    {
      messages: [
        {
          role: 'user',
          content: 'Explain database indexing in simple terms',
        },
      ],
    },
    callback
  );
}

// Example 3: Context Formatting with Database Schema
async function schemaAwareExample() {
  console.log('\n=== Example 3: Schema-Aware Query ===\n');

  const formatter = new ContextFormatter();
  const schema = {
    tables: [
      {
        name: 'users',
        columns: [
          { name: 'id', type: 'INTEGER PRIMARY KEY' },
          { name: 'email', type: 'VARCHAR(255)' },
          { name: 'created_at', type: 'TIMESTAMP' },
        ],
      },
      {
        name: 'orders',
        columns: [
          { name: 'id', type: 'INTEGER PRIMARY KEY' },
          { name: 'user_id', type: 'INTEGER' },
          { name: 'total', type: 'DECIMAL(10,2)' },
          { name: 'status', type: 'VARCHAR(50)' },
        ],
      },
    ],
  };

  const messages = formatter.formatWithSchema(
    'Show me all users who have placed orders over $100',
    schema
  );

  console.log('Formatted messages:', JSON.stringify(messages, null, 2));

  const provider = ProviderFactory.createProvider({
    provider: 'ollama',
    baseUrl: 'http://localhost:11434',
    model: 'codellama',
  });

  const response = await provider.generate({ messages });
  console.log('\nResponse:', response.content);
}

// Example 4: Response Parsing
async function responseParsingExample() {
  console.log('\n=== Example 4: Response Parsing ===\n');

  const parser = new ResponseParser();

  const sampleResponse = `
Here's the SQL query you requested:

\`\`\`sql
SELECT u.id, u.email, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
WHERE u.created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY u.id, u.email;
\`\`\`

This query will:
- Find all users registered in the last 30 days
- Count their orders
- Return email and order count

You should also consider adding an index:

\`\`\`sql
CREATE INDEX idx_users_created_at ON users(created_at);
\`\`\`
  `;

  const parsed = parser.parse(sampleResponse);

  console.log('Parsed Response:');
  console.log('- Text (without code):', parsed.text);
  console.log('\n- Code Blocks:', parsed.codeBlocks.length);
  parsed.codeBlocks.forEach((block, i) => {
    console.log(`  ${i + 1}. Language: ${block.language}`);
    console.log(`     Code: ${block.code.substring(0, 60)}...`);
  });

  console.log('\n- SQL Queries:', parsed.sqlQueries.length);
  parsed.sqlQueries.forEach((sql, i) => {
    console.log(`  ${i + 1}. ${sql.substring(0, 60)}...`);
  });

  console.log('\n- Has Error:', parsed.hasError);
}

// Example 5: LlamaCPP Integration
async function llamaCppExample() {
  console.log('\n=== Example 5: LlamaCPP Provider ===\n');

  const provider = ProviderFactory.createProvider({
    provider: 'llamacpp',
    baseUrl: 'http://localhost:8080',
    model: 'default',
    temperature: 0.5,
  });

  const isAvailable = await provider.testConnection();
  console.log(`LlamaCPP available: ${isAvailable}\n`);

  if (isAvailable) {
    const response = await provider.generate({
      messages: [
        {
          role: 'system',
          content: 'You are a database expert assistant.',
        },
        {
          role: 'user',
          content: 'What are the best practices for database normalization?',
        },
      ],
    });

    console.log('Response:', response.content);
  }
}

// Example 6: SQL Analysis
async function sqlAnalysisExample() {
  console.log('\n=== Example 6: SQL Query Analysis ===\n');

  const formatter = new ContextFormatter();
  const sqlToAnalyze = `
    SELECT * FROM users
    WHERE email = '" + userInput + "'
  `;

  const messages = formatter.formatSQLAnalysis(sqlToAnalyze);

  const provider = ProviderFactory.createProvider({
    provider: 'ollama',
    baseUrl: 'http://localhost:11434',
    model: 'codellama',
  });

  const response = await provider.generate({ messages });
  const parser = new ResponseParser();
  const parsed = parser.parse(response.content);

  console.log('Analysis:', parsed.text);
  console.log('\nAction Items:');
  const actionItems = parser.extractActionItems(response.content);
  actionItems.forEach((item, i) => {
    console.log(`  ${i + 1}. ${item}`);
  });
}

// Example 7: Auto-detect Providers
async function autoDetectExample() {
  console.log('\n=== Example 7: Auto-detect Providers ===\n');

  const providers = await ProviderFactory.detectProviders();

  console.log('Available Providers:');
  providers.forEach((p) => {
    console.log(`  - ${p.provider} (${p.baseUrl}): ${p.available ? '✓ Available' : '✗ Not available'}`);
  });

  // Use the first available provider
  const available = providers.find((p) => p.available);
  if (available) {
    console.log(`\nUsing ${available.provider}...`);
    const config = ProviderFactory.getDefaultConfig(available.provider as any);
    const provider = ProviderFactory.createProvider(config);

    const response = await provider.generate({
      messages: [
        {
          role: 'user',
          content: 'Hello! What LLM are you?',
        },
      ],
    });

    console.log('Response:', response.content);
  }
}

// Example 8: Conversation with History
async function conversationExample() {
  console.log('\n=== Example 8: Conversation with History ===\n');

  const formatter = new ContextFormatter();
  const history = [
    {
      user: 'What is a primary key?',
      assistant: 'A primary key is a unique identifier for each record in a database table.',
    },
    {
      user: 'Can a table have multiple primary keys?',
      assistant: 'No, a table can have only one primary key, but it can be a composite key made of multiple columns.',
    },
  ];

  const messages = formatter.formatConversation(
    'How do I create a composite primary key in SQL?',
    history,
    { includeHistory: true, compressionLevel: 'low' }
  );

  console.log('Conversation messages:', messages.length);

  const provider = ProviderFactory.createProvider({
    provider: 'ollama',
    baseUrl: 'http://localhost:11434',
    model: 'llama2',
  });

  const response = await provider.generate({ messages });
  console.log('Response:', response.content);
}

// Run all examples
async function main() {
  try {
    // Uncomment the examples you want to run:

    // await basicOllamaExample();
    // await streamingExample();
    // await schemaAwareExample();
    await responseParsingExample();
    // await llamaCppExample();
    // await sqlAnalysisExample();
    // await autoDetectExample();
    // await conversationExample();

    console.log('\n✓ Examples completed successfully!');
  } catch (error) {
    console.error('Error running examples:', error);
  }
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
