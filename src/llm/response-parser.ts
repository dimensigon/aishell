/**
 * Response Parser - Parses and extracts structured data from LLM responses
 * Handles code blocks, SQL queries, JSON data, and error detection
 */

export interface ParsedResponse {
  text: string;
  codeBlocks: CodeBlock[];
  sqlQueries: string[];
  jsonData: any[];
  tables: TableData[];
  hasError: boolean;
  errorMessage?: string;
}

export interface CodeBlock {
  language: string;
  code: string;
  startLine: number;
  endLine: number;
}

export interface TableData {
  headers: string[];
  rows: string[][];
}

export class ResponseParser {
  /**
   * Parse LLM response and extract structured data
   */
  parse(response: string): ParsedResponse {
    const codeBlocks = this.extractCodeBlocks(response);
    const sqlQueries = this.extractSQLQueries(codeBlocks);
    const jsonData = this.extractJSONData(response);
    const tables = this.extractTables(response);
    const errorInfo = this.detectError(response);

    return {
      text: this.stripCodeBlocks(response),
      codeBlocks,
      sqlQueries,
      jsonData,
      tables,
      hasError: errorInfo.hasError,
      errorMessage: errorInfo.message,
    };
  }

  /**
   * Extract code blocks from markdown-formatted response
   */
  extractCodeBlocks(text: string): CodeBlock[] {
    const blocks: CodeBlock[] = [];
    const regex = /```(\w+)?\n([\s\S]*?)```/g;
    let match;
    let lineNumber = 0;

    while ((match = regex.exec(text)) !== null) {
      const language = match[1] || 'text';
      const code = match[2].trim();
      const startLine = text.substring(0, match.index).split('\n').length;
      const endLine = startLine + code.split('\n').length;

      blocks.push({
        language,
        code,
        startLine,
        endLine,
      });
    }

    return blocks;
  }

  /**
   * Extract SQL queries from code blocks or inline
   */
  extractSQLQueries(codeBlocks: CodeBlock[]): string[] {
    const queries: string[] = [];

    for (const block of codeBlocks) {
      if (block.language.toLowerCase() === 'sql') {
        // Split on semicolons to get individual queries
        const blockQueries = block.code
          .split(';')
          .map(q => q.trim())
          .filter(q => q.length > 0 && !q.startsWith('--'));

        queries.push(...blockQueries);
      }
    }

    return queries;
  }

  /**
   * Extract JSON data from response
   */
  extractJSONData(text: string): any[] {
    const jsonObjects: any[] = [];

    // Try to find JSON objects or arrays
    const jsonRegex = /(\{[\s\S]*?\}|\[[\s\S]*?\])/g;
    let match;

    while ((match = jsonRegex.exec(text)) !== null) {
      try {
        const parsed = JSON.parse(match[1]);
        jsonObjects.push(parsed);
      } catch (e) {
        // Not valid JSON, skip
      }
    }

    return jsonObjects;
  }

  /**
   * Extract markdown tables
   */
  extractTables(text: string): TableData[] {
    const tables: TableData[] = [];
    const lines = text.split('\n');
    let i = 0;

    while (i < lines.length) {
      const line = lines[i].trim();

      // Check if line looks like a table header
      if (line.includes('|') && line.split('|').filter(c => c.trim()).length > 1) {
        const headers = line.split('|').map(h => h.trim()).filter(h => h);

        // Check for separator line
        if (i + 1 < lines.length) {
          const separator = lines[i + 1].trim();
          if (separator.includes('|') && separator.includes('-')) {
            i += 2; // Skip separator
            const rows: string[][] = [];

            // Extract rows
            while (i < lines.length) {
              const rowLine = lines[i].trim();
              if (!rowLine.includes('|')) break;

              const cells = rowLine.split('|').map(c => c.trim()).filter(c => c);
              if (cells.length === headers.length) {
                rows.push(cells);
              }
              i++;
            }

            if (rows.length > 0) {
              tables.push({ headers, rows });
            }
            continue;
          }
        }
      }
      i++;
    }

    return tables;
  }

  /**
   * Strip code blocks from text to get clean explanation
   */
  stripCodeBlocks(text: string): string {
    return text.replace(/```[\w+]?\n[\s\S]*?```/g, '').trim();
  }

  /**
   * Detect errors in LLM response
   */
  detectError(text: string): { hasError: boolean; message?: string } {
    const errorPatterns = [
      /error:/i,
      /exception:/i,
      /failed:/i,
      /cannot/i,
      /unable to/i,
      /invalid/i,
      /syntax error/i,
    ];

    for (const pattern of errorPatterns) {
      const match = text.match(pattern);
      if (match) {
        // Extract error context (next 100 chars after error keyword)
        const index = match.index || 0;
        const errorContext = text.substring(index, index + 100).split('\n')[0];

        return {
          hasError: true,
          message: errorContext.trim(),
        };
      }
    }

    return { hasError: false };
  }

  /**
   * Format SQL queries for display
   */
  formatSQL(sql: string): string {
    const keywords = [
      'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER',
      'ON', 'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT', 'INSERT', 'UPDATE',
      'DELETE', 'CREATE', 'ALTER', 'DROP', 'TABLE', 'INDEX', 'VIEW',
    ];

    let formatted = sql;

    // Add line breaks before major keywords
    const majorKeywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP BY', 'ORDER BY'];
    for (const keyword of majorKeywords) {
      const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
      formatted = formatted.replace(regex, `\n${keyword}`);
    }

    // Indent JOIN conditions
    formatted = formatted.replace(/\n(INNER|LEFT|RIGHT|OUTER)?\s*JOIN/gi, '\n  $1 JOIN');

    return formatted.trim();
  }

  /**
   * Extract action items or recommendations from response
   */
  extractActionItems(text: string): string[] {
    const items: string[] = [];
    const lines = text.split('\n');

    for (const line of lines) {
      const trimmed = line.trim();
      // Look for bullet points, numbered lists, or recommendation markers
      if (
        trimmed.match(/^[-*•]\s+/) ||
        trimmed.match(/^\d+\.\s+/) ||
        trimmed.toLowerCase().includes('recommend') ||
        trimmed.toLowerCase().includes('should') ||
        trimmed.toLowerCase().includes('consider')
      ) {
        items.push(trimmed.replace(/^[-*•]\s+|\d+\.\s+/, '').trim());
      }
    }

    return items;
  }

  /**
   * Extract database schema from CREATE TABLE statements
   */
  extractSchema(response: string): Array<{ table: string; sql: string }> {
    const schemas: Array<{ table: string; sql: string }> = [];
    const createTableRegex = /CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\(([\s\S]*?)\);/gi;
    let match;

    while ((match = createTableRegex.exec(response)) !== null) {
      schemas.push({
        table: match[1],
        sql: match[0],
      });
    }

    return schemas;
  }
}
