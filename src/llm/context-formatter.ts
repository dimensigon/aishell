/**
 * Context Formatter - Formats prompts and context for LLM consumption
 * Optimizes context length and applies prompt engineering best practices
 */

import { LLMMessage } from '../types/llm.js';

export interface ContextOptions {
  maxTokens?: number;
  systemPrompt?: string;
  includeHistory?: boolean;
  compressionLevel?: 'none' | 'low' | 'high';
}

export class ContextFormatter {
  private readonly DEFAULT_SYSTEM_PROMPT = `You are an AI database assistant. You help users with SQL queries, database design, and data analysis.
Provide clear, concise answers with code examples when appropriate.`;

  /**
   * Format a user query with system context
   */
  formatQuery(query: string, options: ContextOptions = {}): LLMMessage[] {
    const messages: LLMMessage[] = [];

    // Add system prompt
    messages.push({
      role: 'system',
      content: options.systemPrompt || this.DEFAULT_SYSTEM_PROMPT,
    });

    // Add user query
    messages.push({
      role: 'user',
      content: query,
    });

    return messages;
  }

  /**
   * Format a conversation with history
   */
  formatConversation(
    query: string,
    history: Array<{ user: string; assistant: string }>,
    options: ContextOptions = {}
  ): LLMMessage[] {
    const messages: LLMMessage[] = [];

    // Add system prompt
    messages.push({
      role: 'system',
      content: options.systemPrompt || this.DEFAULT_SYSTEM_PROMPT,
    });

    // Add conversation history if enabled
    if (options.includeHistory !== false && history.length > 0) {
      const compressedHistory = this.compressHistory(history, options.compressionLevel);

      for (const turn of compressedHistory) {
        messages.push({
          role: 'user',
          content: turn.user,
        });
        messages.push({
          role: 'assistant',
          content: turn.assistant,
        });
      }
    }

    // Add current query
    messages.push({
      role: 'user',
      content: query,
    });

    return messages;
  }

  /**
   * Format database schema context
   */
  formatWithSchema(
    query: string,
    schema: {
      tables: Array<{ name: string; columns: Array<{ name: string; type: string }> }>;
    },
    options: ContextOptions = {}
  ): LLMMessage[] {
    const schemaContext = this.formatSchemaAsText(schema);

    const systemPrompt = `${options.systemPrompt || this.DEFAULT_SYSTEM_PROMPT}

Database Schema:
${schemaContext}

Use this schema to provide accurate SQL queries and recommendations.`;

    return [
      {
        role: 'system',
        content: systemPrompt,
      },
      {
        role: 'user',
        content: query,
      },
    ];
  }

  /**
   * Format SQL query analysis request
   */
  formatSQLAnalysis(sqlQuery: string): LLMMessage[] {
    return [
      {
        role: 'system',
        content: `You are an SQL expert. Analyze the following SQL query for:
- Correctness and syntax
- Performance optimization opportunities
- Security issues (SQL injection, etc.)
- Best practices violations

Provide specific, actionable feedback.`,
      },
      {
        role: 'user',
        content: `Analyze this SQL query:\n\n\`\`\`sql\n${sqlQuery}\n\`\`\``,
      },
    ];
  }

  /**
   * Format database design request
   */
  formatDatabaseDesign(requirements: string): LLMMessage[] {
    return [
      {
        role: 'system',
        content: `You are a database architect. Design a database schema based on requirements.
Provide:
- Table structures with appropriate data types
- Primary and foreign key relationships
- Indexes for performance
- Constraints for data integrity
- CREATE TABLE statements`,
      },
      {
        role: 'user',
        content: `Design a database schema for:\n\n${requirements}`,
      },
    ];
  }

  /**
   * Compress conversation history based on level
   */
  private compressHistory(
    history: Array<{ user: string; assistant: string }>,
    level: 'none' | 'low' | 'high' = 'low'
  ): Array<{ user: string; assistant: string }> {
    if (level === 'none') {
      return history;
    }

    if (level === 'low') {
      // Keep last 5 exchanges
      return history.slice(-5);
    }

    if (level === 'high') {
      // Keep only last 2 exchanges
      return history.slice(-2);
    }

    return history;
  }

  /**
   * Format database schema as readable text
   */
  private formatSchemaAsText(schema: {
    tables: Array<{ name: string; columns: Array<{ name: string; type: string }> }>;
  }): string {
    return schema.tables
      .map(table => {
        const columns = table.columns
          .map(col => `  - ${col.name}: ${col.type}`)
          .join('\n');
        return `Table: ${table.name}\n${columns}`;
      })
      .join('\n\n');
  }

  /**
   * Estimate token count (rough approximation)
   */
  estimateTokens(text: string): number {
    // Rough estimate: 1 token ≈ 4 characters
    return Math.ceil(text.length / 4);
  }

  /**
   * Truncate messages to fit within token limit
   */
  truncateMessages(messages: LLMMessage[], maxTokens: number): LLMMessage[] {
    let totalTokens = 0;
    const result: LLMMessage[] = [];

    // Always keep system message
    if (messages.length > 0 && messages[0].role === 'system') {
      result.push(messages[0]);
      totalTokens += this.estimateTokens(messages[0].content);
    }

    // Add messages in reverse order until we hit the limit
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'system') continue;

      const tokens = this.estimateTokens(messages[i].content);
      if (totalTokens + tokens > maxTokens) {
        break;
      }

      result.unshift(messages[i]);
      totalTokens += tokens;
    }

    return result;
  }
}
