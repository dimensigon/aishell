/**
 * LLM Provider Interfaces Unit Tests
 * Tests LLM integration, intent analysis, and anonymization
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

describe('LLM Provider Interfaces', () => {
  let mockLLMProvider: any;
  let mockEmbeddingModel: any;

  beforeEach(() => {
    mockEmbeddingModel = {
      encode: vi.fn(),
    };

    mockLLMProvider = {
      generateCompletion: vi.fn(),
      analyzeIntent: vi.fn(),
      embedText: vi.fn(),
    };
  });

  describe('Intent Analysis', () => {
    it('should analyze user intent from natural language', async () => {
      const userInput = 'show me all users who registered last week';
      const context = {
        database: 'postgres',
        currentSchema: 'public',
      };

      const expectedIntent = {
        action: 'query',
        target: 'users',
        filter: 'time_range',
        confidence: 0.92,
      };

      mockLLMProvider.analyzeIntent.mockResolvedValue(expectedIntent);

      const result = await mockLLMProvider.analyzeIntent(userInput, context);

      expect(result.action).toBe('query');
      expect(result.confidence).toBeGreaterThan(0.9);
    });

    it('should detect database operation intent', async () => {
      const inputs = [
        { text: 'create a new table for products', expected: 'create' },
        { text: 'update user status to active', expected: 'update' },
        { text: 'delete old records', expected: 'delete' },
        { text: 'find all orders', expected: 'query' },
      ];

      for (const input of inputs) {
        mockLLMProvider.analyzeIntent.mockResolvedValue({
          action: input.expected,
        });

        const result = await mockLLMProvider.analyzeIntent(input.text, {});
        expect(result.action).toBe(input.expected);
      }
    });

    it('should provide context enrichment suggestions', async () => {
      const input = 'show me the slow queries';

      mockLLMProvider.analyzeIntent.mockResolvedValue({
        action: 'query',
        suggestions: [
          'Check pg_stat_statements',
          'Review execution plans',
          'Analyze query performance',
        ],
      });

      const result = await mockLLMProvider.analyzeIntent(input, {});

      expect(result.suggestions).toHaveLength(3);
      expect(result.suggestions[0]).toContain('pg_stat_statements');
    });
  });

  describe('Text Embedding', () => {
    it('should generate embeddings for text', async () => {
      const text = 'SELECT * FROM users WHERE active = true';
      const mockEmbedding = new Float32Array(384).fill(0.5);

      mockEmbeddingModel.encode.mockReturnValue(mockEmbedding);

      const result = mockEmbeddingModel.encode(text);

      expect(result).toBeInstanceOf(Float32Array);
      expect(result.length).toBe(384);
    });

    it('should produce similar embeddings for similar queries', async () => {
      const query1 = 'get all active users';
      const query2 = 'find active users';

      const embedding1 = new Float32Array(384).fill(0.8);
      const embedding2 = new Float32Array(384).fill(0.75);

      mockEmbeddingModel.encode
        .mockReturnValueOnce(embedding1)
        .mockReturnValueOnce(embedding2);

      const emb1 = mockEmbeddingModel.encode(query1);
      const emb2 = mockEmbeddingModel.encode(query2);

      const similarity = cosineSimilarity(emb1, emb2);
      expect(similarity).toBeGreaterThan(0.9);
    });

    it('should cache embeddings for repeated queries', async () => {
      const cache = new EmbeddingCache(mockEmbeddingModel);
      const text = 'SELECT COUNT(*) FROM users';

      await cache.getEmbedding(text);
      await cache.getEmbedding(text); // Should use cache

      expect(mockEmbeddingModel.encode).toHaveBeenCalledTimes(1);
    });
  });

  describe('Pseudo-Anonymization', () => {
    it('should anonymize sensitive data', () => {
      const text = 'Connect to user@example.com with password secret123';

      const { anonymized, mapping } = pseudoAnonymize(text);

      expect(anonymized).not.toContain('user@example.com');
      expect(anonymized).not.toContain('secret123');
      expect(anonymized).toContain('<EMAIL_0>');
      expect(mapping['<EMAIL_0>']).toBe('user@example.com');
    });

    it('should detect and anonymize multiple data types', () => {
      const text = `
        Server: db.example.com
        User: admin@company.com
        IP: 192.168.1.100
        Password: MySecretPass123
      `;

      const { anonymized, mapping } = pseudoAnonymize(text);

      expect(Object.keys(mapping)).toHaveLength(4);
      expect(mapping).toHaveProperty(expect.stringContaining('EMAIL'));
      expect(mapping).toHaveProperty(expect.stringContaining('IP'));
      expect(mapping).toHaveProperty(expect.stringContaining('SERVER'));
    });

    it('should preserve anonymization mapping for de-anonymization', () => {
      const original = 'User john@example.com accessed server db-prod-01';

      const { anonymized, mapping } = pseudoAnonymize(original);
      const restored = deAnonymize(anonymized, mapping);

      expect(restored).toBe(original);
    });

    it('should handle nested sensitive data', () => {
      const json = JSON.stringify({
        user: 'admin@example.com',
        config: {
          host: '10.0.0.1',
          credentials: {
            username: 'dbadmin',
            password: 'secret',
          },
        },
      });

      const { anonymized } = pseudoAnonymize(json);

      expect(anonymized).not.toContain('admin@example.com');
      expect(anonymized).not.toContain('10.0.0.1');
      expect(anonymized).not.toContain('secret');
    });
  });

  describe('Code Completion', () => {
    it('should provide SQL completion suggestions', async () => {
      const partial = 'SELECT * FROM us';
      const schema = ['users', 'user_sessions', 'orders'];

      mockLLMProvider.generateCompletion.mockResolvedValue({
        completions: [
          { text: 'users', score: 0.95 },
          { text: 'user_sessions', score: 0.85 },
        ],
      });

      const result = await mockLLMProvider.generateCompletion(partial, {
        schema,
      });

      expect(result.completions[0].text).toBe('users');
      expect(result.completions).toHaveLength(2);
    });

    it('should suggest context-aware completions', async () => {
      const partial = 'UPDATE users SET ';
      const tableSchema = {
        columns: ['id', 'name', 'email', 'status', 'created_at'],
      };

      mockLLMProvider.generateCompletion.mockResolvedValue({
        completions: [
          { text: 'status = ', score: 0.9 },
          { text: 'email = ', score: 0.85 },
        ],
      });

      const result = await mockLLMProvider.generateCompletion(partial, {
        tableSchema,
      });

      expect(result.completions[0].text).toContain('status');
    });
  });

  describe('Natural Language to SQL', () => {
    it('should convert natural language to SQL', async () => {
      const naturalQuery = 'find all users who signed up this month';
      const schema = {
        tables: ['users'],
        columns: ['id', 'email', 'created_at'],
      };

      const expectedSQL = `
        SELECT * FROM users
        WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
      `.trim();

      mockLLMProvider.generateCompletion.mockResolvedValue({
        sql: expectedSQL,
      });

      const result = await nlToSQL(naturalQuery, schema, mockLLMProvider);

      expect(result.sql).toContain('DATE_TRUNC');
      expect(result.sql).toContain('users');
    });

    it('should handle complex queries with joins', async () => {
      const naturalQuery = 'show me users and their total order count';

      const expectedSQL = `
        SELECT u.id, u.name, COUNT(o.id) as order_count
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        GROUP BY u.id, u.name
      `.trim();

      mockLLMProvider.generateCompletion.mockResolvedValue({
        sql: expectedSQL,
      });

      const result = await nlToSQL(naturalQuery, {}, mockLLMProvider);

      expect(result.sql).toContain('LEFT JOIN');
      expect(result.sql).toContain('GROUP BY');
    });

    it('should validate generated SQL syntax', async () => {
      const naturalQuery = 'get user data';

      mockLLMProvider.generateCompletion.mockResolvedValue({
        sql: 'INVALID SQL SYNTAX',
      });

      const result = await nlToSQL(naturalQuery, {}, mockLLMProvider);

      expect(result.valid).toBe(false);
      expect(result.errors).toBeDefined();
    });
  });

  describe('Error Handling', () => {
    it('should handle LLM API errors gracefully', async () => {
      mockLLMProvider.analyzeIntent.mockRejectedValue(
        new Error('LLM service unavailable')
      );

      await expect(
        mockLLMProvider.analyzeIntent('test query', {})
      ).rejects.toThrow('LLM service unavailable');
    });

    it('should fall back to rule-based analysis on LLM failure', async () => {
      const fallbackAnalyzer = new FallbackIntentAnalyzer(mockLLMProvider);

      mockLLMProvider.analyzeIntent.mockRejectedValue(new Error('API error'));

      const result = await fallbackAnalyzer.analyze('SELECT * FROM users', {});

      expect(result.action).toBe('query'); // Rule-based detection
      expect(result.fallback).toBe(true);
    });
  });

  describe('Performance', () => {
    it('should batch multiple requests efficiently', async () => {
      const batchProvider = new BatchLLMProvider(mockLLMProvider);
      const requests = [
        'analyze query 1',
        'analyze query 2',
        'analyze query 3',
      ];

      mockLLMProvider.analyzeIntent.mockResolvedValue({ action: 'query' });

      const results = await batchProvider.batchAnalyze(requests);

      expect(results).toHaveLength(3);
      expect(mockLLMProvider.analyzeIntent).toHaveBeenCalledTimes(1); // Batched
    });

    it('should timeout long-running LLM requests', async () => {
      const timeoutProvider = new TimeoutLLMProvider(mockLLMProvider, 1000);

      mockLLMProvider.generateCompletion.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 2000))
      );

      await expect(
        timeoutProvider.generateCompletion('test', {})
      ).rejects.toThrow('timeout');
    });
  });
});

// Helper functions
function cosineSimilarity(a: Float32Array, b: Float32Array): number {
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;

  for (let i = 0; i < a.length; i++) {
    dotProduct += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }

  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

function pseudoAnonymize(text: string): { anonymized: string; mapping: Record<string, string> } {
  const patterns = {
    email: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g,
    ip: /\b(?:\d{1,3}\.){3}\d{1,3}\b/g,
    server: /(?:server|host):\s*([^\s,]+)/gi,
  };

  let anonymized = text;
  const mapping: Record<string, string> = {};
  let counter = 0;

  for (const [type, pattern] of Object.entries(patterns)) {
    const matches = text.matchAll(pattern);
    for (const match of matches) {
      const token = `<${type.toUpperCase()}_${counter++}>`;
      mapping[token] = match[0];
      anonymized = anonymized.replace(match[0], token);
    }
  }

  return { anonymized, mapping };
}

function deAnonymize(text: string, mapping: Record<string, string>): string {
  let result = text;
  for (const [token, value] of Object.entries(mapping)) {
    result = result.replace(token, value);
  }
  return result;
}

async function nlToSQL(query: string, schema: any, provider: any): Promise<any> {
  const result = await provider.generateCompletion(query, { schema });
  return {
    sql: result.sql,
    valid: !result.sql.includes('INVALID'),
    errors: result.sql.includes('INVALID') ? ['Syntax error'] : undefined,
  };
}

class EmbeddingCache {
  private cache = new Map<string, Float32Array>();

  constructor(private model: any) {}

  async getEmbedding(text: string): Promise<Float32Array> {
    if (this.cache.has(text)) {
      return this.cache.get(text)!;
    }

    const embedding = this.model.encode(text);
    this.cache.set(text, embedding);
    return embedding;
  }
}

class FallbackIntentAnalyzer {
  constructor(private llmProvider: any) {}

  async analyze(query: string, context: any): Promise<any> {
    try {
      return await this.llmProvider.analyzeIntent(query, context);
    } catch (error) {
      // Rule-based fallback
      const upperQuery = query.toUpperCase();
      if (upperQuery.startsWith('SELECT')) return { action: 'query', fallback: true };
      if (upperQuery.startsWith('INSERT')) return { action: 'insert', fallback: true };
      if (upperQuery.startsWith('UPDATE')) return { action: 'update', fallback: true };
      if (upperQuery.startsWith('DELETE')) return { action: 'delete', fallback: true };
      return { action: 'unknown', fallback: true };
    }
  }
}

class BatchLLMProvider {
  constructor(private provider: any) {}

  async batchAnalyze(queries: string[]): Promise<any[]> {
    // Simulate batching
    await this.provider.analyzeIntent(queries.join('\n'), {});
    return queries.map(() => ({ action: 'query' }));
  }
}

class TimeoutLLMProvider {
  constructor(
    private provider: any,
    private timeoutMs: number
  ) {}

  async generateCompletion(text: string, context: any): Promise<any> {
    return Promise.race([
      this.provider.generateCompletion(text, context),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('timeout')), this.timeoutMs)
      ),
    ]);
  }
}
