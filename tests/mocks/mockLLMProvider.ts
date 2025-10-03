/**
 * Mock LLM Provider for Testing
 * Simulates LLM responses without external API calls
 */

export class MockLLMProvider {
  private intentPatterns: Map<string, any> = new Map();
  private sqlTemplates: Map<string, string> = new Map();
  private completionCache: Map<string, any[]> = new Map();

  constructor() {
    this.initializeMockPatterns();
  }

  private initializeMockPatterns(): void {
    // Intent patterns
    this.intentPatterns.set('query', {
      keywords: ['show', 'find', 'get', 'list', 'select', 'display'],
      action: 'query',
      confidence: 0.9,
    });

    this.intentPatterns.set('create', {
      keywords: ['create', 'add', 'insert', 'new'],
      action: 'create',
      confidence: 0.85,
    });

    this.intentPatterns.set('update', {
      keywords: ['update', 'modify', 'change', 'edit'],
      action: 'update',
      confidence: 0.88,
    });

    this.intentPatterns.set('delete', {
      keywords: ['delete', 'remove', 'drop'],
      action: 'delete',
      confidence: 0.92,
    });

    // SQL templates
    this.sqlTemplates.set('all users', 'SELECT * FROM users');
    this.sqlTemplates.set('active users', 'SELECT * FROM users WHERE active = true');
    this.sqlTemplates.set('user count', 'SELECT COUNT(*) FROM users');
    this.sqlTemplates.set('recent orders', 'SELECT * FROM orders ORDER BY created_at DESC LIMIT 10');
    this.sqlTemplates.set('users last week',
      "SELECT * FROM users WHERE created_at >= NOW() - INTERVAL '7 days'");
  }

  async analyzeIntent(
    userInput: string,
    context: any
  ): Promise<{
    action: string;
    confidence: number;
    target?: string;
    suggestions?: string[];
  }> {
    const lowerInput = userInput.toLowerCase();

    // Match intent patterns
    for (const [key, pattern] of this.intentPatterns) {
      if (pattern.keywords.some((kw: string) => lowerInput.includes(kw))) {
        const target = this.extractTarget(lowerInput);

        return {
          action: pattern.action,
          confidence: pattern.confidence,
          target,
          suggestions: this.generateSuggestions(pattern.action, context),
        };
      }
    }

    // Default intent
    return {
      action: 'unknown',
      confidence: 0.5,
      suggestions: ['Try a more specific command'],
    };
  }

  private extractTarget(input: string): string | undefined {
    const tables = ['users', 'orders', 'products', 'customers'];
    return tables.find(table => input.includes(table));
  }

  private generateSuggestions(action: string, context: any): string[] {
    const suggestions: Record<string, string[]> = {
      query: [
        'Use SELECT to retrieve data',
        'Add WHERE clause for filtering',
        'Consider using LIMIT for large results',
      ],
      create: [
        'Use INSERT INTO to add records',
        'Specify all required columns',
        'Use RETURNING to get inserted ID',
      ],
      update: [
        'Use UPDATE SET to modify records',
        'Always include WHERE clause',
        'Consider using transactions',
      ],
      delete: [
        'Use DELETE FROM with caution',
        'Always include WHERE clause',
        'Consider soft deletes instead',
      ],
    };

    return suggestions[action] || ['Check documentation for syntax'];
  }

  async generateSQL(
    naturalLanguage: string,
    schema: any
  ): Promise<string> {
    const lowerNL = naturalLanguage.toLowerCase();

    // Check template matches
    for (const [pattern, sql] of this.sqlTemplates) {
      if (lowerNL.includes(pattern)) {
        return sql;
      }
    }

    // Generate SQL based on intent
    const intent = await this.analyzeIntent(naturalLanguage, {});

    if (intent.action === 'query' && intent.target) {
      let sql = `SELECT * FROM ${intent.target}`;

      if (lowerNL.includes('count')) {
        sql = `SELECT COUNT(*) FROM ${intent.target}`;
      }

      if (lowerNL.includes('active')) {
        sql += ' WHERE active = true';
      }

      if (lowerNL.includes('last week') || lowerNL.includes('recent')) {
        sql += " WHERE created_at >= NOW() - INTERVAL '7 days'";
      }

      if (lowerNL.includes('limit') || lowerNL.match(/\d+/)) {
        const limitMatch = lowerNL.match(/(\d+)/);
        sql += ` LIMIT ${limitMatch?.[1] || '10'}`;
      }

      return sql;
    }

    return 'SELECT 1'; // Fallback
  }

  async getCompletions(
    partial: string,
    context: { schema?: any; tables?: string[]; columns?: string[] }
  ): Promise<Array<{ text: string; score: number; type: string }>> {
    const completions: Array<{ text: string; score: number; type: string }> = [];
    const lowerPartial = partial.toLowerCase();

    // SQL keyword completions
    const keywords = ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP'];
    keywords.forEach(kw => {
      if (kw.toLowerCase().startsWith(lowerPartial)) {
        completions.push({
          text: kw,
          score: 0.9,
          type: 'keyword',
        });
      }
    });

    // Table completions
    if (context.tables) {
      context.tables.forEach(table => {
        if (table.toLowerCase().startsWith(lowerPartial)) {
          completions.push({
            text: table,
            score: 0.95,
            type: 'table',
          });
        }
      });
    }

    // Column completions
    if (context.columns) {
      context.columns.forEach(col => {
        if (col.toLowerCase().startsWith(lowerPartial)) {
          completions.push({
            text: col,
            score: 0.85,
            type: 'column',
          });
        }
      });
    }

    // Sort by score
    return completions.sort((a, b) => b.score - a.score).slice(0, 10);
  }

  async embedText(text: string): Promise<Float32Array> {
    // Generate deterministic mock embedding based on text
    const embedding = new Float32Array(384);
    const hash = this.simpleHash(text);

    for (let i = 0; i < 384; i++) {
      embedding[i] = Math.sin(hash + i) * 0.5;
    }

    return embedding;
  }

  private simpleHash(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return hash;
  }

  pseudoAnonymize(text: string): {
    anonymized: string;
    mapping: Record<string, string>;
  } {
    const patterns = {
      email: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g,
      ip: /\b(?:\d{1,3}\.){3}\d{1,3}\b/g,
      password: /password[:\s]+([^\s,]+)/gi,
      server: /(?:server|host)[:\s]+([^\s,]+)/gi,
    };

    let anonymized = text;
    const mapping: Record<string, string> = {};
    let counter = 0;

    for (const [type, pattern] of Object.entries(patterns)) {
      const matches = text.matchAll(pattern);
      for (const match of matches) {
        const value = match[1] || match[0];
        const token = `<${type.toUpperCase()}_${counter++}>`;
        mapping[token] = value;
        anonymized = anonymized.replace(value, token);
      }
    }

    return { anonymized, mapping };
  }

  deAnonymize(
    text: string,
    mapping: Record<string, string>
  ): string {
    let result = text;
    for (const [token, value] of Object.entries(mapping)) {
      result = result.replace(token, value);
    }
    return result;
  }

  async suggestFix(sql: string): Promise<{ corrected: string; changes: string[] }> {
    const corrections: Array<{ pattern: RegExp; replacement: string; description: string }> = [
      { pattern: /SELCT/gi, replacement: 'SELECT', description: 'Fixed SELECT typo' },
      { pattern: /FORM/gi, replacement: 'FROM', description: 'Fixed FROM typo' },
      { pattern: /WHRE/gi, replacement: 'WHERE', description: 'Fixed WHERE typo' },
      { pattern: /UDPATE/gi, replacement: 'UPDATE', description: 'Fixed UPDATE typo' },
      { pattern: /INSER\s/gi, replacement: 'INSERT ', description: 'Fixed INSERT typo' },
    ];

    let corrected = sql;
    const changes: string[] = [];

    for (const { pattern, replacement, description } of corrections) {
      if (pattern.test(corrected)) {
        corrected = corrected.replace(pattern, replacement);
        changes.push(description);
      }
    }

    return { corrected, changes };
  }

  async validateSQL(sql: string): Promise<{ valid: boolean; errors: string[] }> {
    const errors: string[] = [];

    // Basic validation
    const normalizedSQL = sql.trim().toUpperCase();

    if (!normalizedSQL) {
      errors.push('Empty SQL statement');
    }

    if (normalizedSQL.startsWith('SELCT')) {
      errors.push('Invalid keyword: SELCT (did you mean SELECT?)');
    }

    if (normalizedSQL.includes('DELETE') && !normalizedSQL.includes('WHERE')) {
      errors.push('DELETE without WHERE clause - this will delete all rows');
    }

    if (normalizedSQL.includes('UPDATE') && !normalizedSQL.includes('WHERE')) {
      errors.push('UPDATE without WHERE clause - this will update all rows');
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }
}

export default MockLLMProvider;
