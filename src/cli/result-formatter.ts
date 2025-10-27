/**
 * Result Formatter
 * Formats query results in various output formats (table, JSON, CSV, Markdown)
 */

import Table from 'cli-table3';
import chalk from 'chalk';

/**
 * Output format
 */
export enum OutputFormat {
  TABLE = 'table',
  JSON = 'json',
  CSV = 'csv',
  MARKDOWN = 'markdown',
  VERTICAL = 'vertical'
}

/**
 * Format options
 */
export interface FormatOptions {
  maxWidth?: number;
  maxCellWidth?: number;
  colorize?: boolean;
  showIndex?: boolean;
  showStats?: boolean;
  pagination?: {
    page: number;
    pageSize: number;
  };
}

/**
 * Result Formatter
 */
export class ResultFormatter {
  constructor(private options: FormatOptions = {}) {
    this.options = {
      maxWidth: 120,
      maxCellWidth: 50,
      colorize: true,
      showIndex: false,
      showStats: true,
      ...options
    };
  }

  /**
   * Format results in specified format
   */
  format(results: any[], format: OutputFormat = OutputFormat.TABLE): string {
    if (!results || results.length === 0) {
      return this.formatEmpty();
    }

    switch (format) {
      case OutputFormat.TABLE:
        return this.formatTable(results);

      case OutputFormat.JSON:
        return this.formatJSON(results);

      case OutputFormat.CSV:
        return this.formatCSV(results);

      case OutputFormat.MARKDOWN:
        return this.formatMarkdown(results);

      case OutputFormat.VERTICAL:
        return this.formatVertical(results);

      default:
        return this.formatTable(results);
    }
  }

  /**
   * Format as ASCII table
   */
  formatTable(results: any[]): string {
    if (results.length === 0) {
      return this.formatEmpty();
    }

    // Apply pagination if specified
    const paginatedResults = this.applyPagination(results);

    // Get column names from first result
    const columns = Object.keys(paginatedResults[0]);

    // Create table
    const table = new Table({
      head: this.options.colorize
        ? columns.map((col) => chalk.cyan.bold(col))
        : columns,
      style: {
        head: [],
        border: this.options.colorize ? ['gray'] : []
      },
      colWidths: this.calculateColumnWidths(columns, paginatedResults),
      wordWrap: true
    });

    // Add rows
    for (const row of paginatedResults) {
      const values = columns.map((col) => this.formatValue(row[col]));
      table.push(values);
    }

    let output = table.toString();

    // Add statistics
    if (this.options.showStats) {
      output += '\n' + this.formatStats(results.length, paginatedResults.length);
    }

    return output;
  }

  /**
   * Format as JSON
   */
  formatJSON(results: any[]): string {
    return JSON.stringify(results, null, 2);
  }

  /**
   * Format as CSV
   */
  formatCSV(results: any[]): string {
    if (results.length === 0) {
      return '';
    }

    const columns = Object.keys(results[0]);

    // Header row
    const header = columns.map((col) => this.escapeCSV(col)).join(',');

    // Data rows
    const rows = results.map((row) => {
      return columns
        .map((col) => this.escapeCSV(String(row[col] ?? '')))
        .join(',');
    });

    return [header, ...rows].join('\n');
  }

  /**
   * Format as Markdown table
   */
  formatMarkdown(results: any[]): string {
    if (results.length === 0) {
      return '_No results_';
    }

    const columns = Object.keys(results[0]);

    // Header
    const header = `| ${columns.join(' | ')} |`;
    const separator = `| ${columns.map(() => '---').join(' | ')} |`;

    // Rows
    const rows = results.map((row) => {
      const values = columns.map((col) => this.formatValue(row[col]));
      return `| ${values.join(' | ')} |`;
    });

    return [header, separator, ...rows].join('\n');
  }

  /**
   * Format as vertical (one column per line)
   */
  formatVertical(results: any[]): string {
    if (results.length === 0) {
      return this.formatEmpty();
    }

    const output: string[] = [];

    for (let i = 0; i < results.length; i++) {
      const row = results[i];
      const columns = Object.keys(row);

      output.push(this.colorize(`Row ${i + 1}:`, 'yellow', 'bold'));

      const maxKeyLength = Math.max(...columns.map((col) => col.length));

      for (const col of columns) {
        const paddedKey = col.padEnd(maxKeyLength);
        const value = this.formatValue(row[col]);
        output.push(`  ${this.colorize(paddedKey, 'cyan')}: ${value}`);
      }

      if (i < results.length - 1) {
        output.push(''); // Empty line between rows
      }
    }

    return output.join('\n');
  }

  /**
   * Format empty result
   */
  private formatEmpty(): string {
    return this.colorize('No results found', 'yellow');
  }

  /**
   * Format statistics
   */
  private formatStats(totalRows: number, displayedRows: number): string {
    let stats = this.colorize(`\n${displayedRows} rows`, 'gray');

    if (totalRows > displayedRows) {
      stats += this.colorize(` (${totalRows} total)`, 'gray');
    }

    return stats;
  }

  /**
   * Format individual value
   */
  private formatValue(value: any): string {
    if (value === null || value === undefined) {
      return this.colorize('NULL', 'gray');
    }

    if (typeof value === 'boolean') {
      return this.colorize(String(value), value ? 'green' : 'red');
    }

    if (typeof value === 'number') {
      return this.colorize(String(value), 'yellow');
    }

    if (value instanceof Date) {
      return this.colorize(value.toISOString(), 'blue');
    }

    if (typeof value === 'object') {
      return JSON.stringify(value);
    }

    // Truncate long strings
    const str = String(value);
    if (this.options.maxCellWidth && str.length > this.options.maxCellWidth) {
      return str.substring(0, this.options.maxCellWidth - 3) + '...';
    }

    return str;
  }

  /**
   * Escape CSV value
   */
  private escapeCSV(value: string): string {
    // Wrap in quotes if contains comma, quote, or newline
    if (/[,"\n]/.test(value)) {
      return `"${value.replace(/"/g, '""')}"`;
    }
    return value;
  }

  /**
   * Apply pagination
   */
  private applyPagination(results: any[]): any[] {
    if (!this.options.pagination) {
      return results;
    }

    const { page, pageSize } = this.options.pagination;
    const start = (page - 1) * pageSize;
    const end = start + pageSize;

    return results.slice(start, end);
  }

  /**
   * Calculate column widths
   */
  private calculateColumnWidths(columns: string[], results: any[]): number[] {
    const maxCellWidth = this.options.maxCellWidth || 50;

    return columns.map((col) => {
      // Get max width for this column
      const values = results.map((row) => String(row[col] || ''));
      const maxValueWidth = Math.max(...values.map((v) => v.length));
      const headerWidth = col.length;

      return Math.min(Math.max(maxValueWidth, headerWidth) + 2, maxCellWidth);
    });
  }

  /**
   * Colorize text
   */
  private colorize(text: string, color?: string, style?: string): string {
    if (!this.options.colorize) {
      return text;
    }

    let colorized = text;

    // Apply color
    if (color) {
      const colorFn = (chalk as any)[color];
      if (colorFn) {
        colorized = colorFn(colorized);
      }
    }

    // Apply style
    if (style) {
      const styleFn = (chalk as any)[style];
      if (styleFn) {
        colorized = styleFn(colorized);
      }
    }

    return colorized;
  }

  /**
   * Format query execution summary
   */
  formatExecutionSummary(result: {
    rowCount: number;
    executionTime: number;
    affectedRows?: number;
  }): string {
    const lines: string[] = [];

    lines.push(this.colorize('Execution Summary:', 'cyan', 'bold'));
    lines.push(`  Rows returned: ${this.colorize(String(result.rowCount), 'yellow')}`);

    if (result.affectedRows !== undefined) {
      lines.push(`  Rows affected: ${this.colorize(String(result.affectedRows), 'yellow')}`);
    }

    lines.push(
      `  Execution time: ${this.colorize(`${result.executionTime}ms`, 'yellow')}`
    );

    return lines.join('\n');
  }

  /**
   * Format error message
   */
  formatError(error: Error): string {
    return this.colorize(`Error: ${error.message}`, 'red', 'bold');
  }

  /**
   * Format warning message
   */
  formatWarning(message: string): string {
    return this.colorize(`Warning: ${message}`, 'yellow', 'bold');
  }

  /**
   * Format success message
   */
  formatSuccess(message: string): string {
    return this.colorize(`✓ ${message}`, 'green', 'bold');
  }

  /**
   * Format info message
   */
  formatInfo(message: string): string {
    return this.colorize(`ℹ ${message}`, 'blue');
  }

  /**
   * Create progress bar
   */
  formatProgressBar(current: number, total: number, width: number = 40): string {
    const percentage = Math.round((current / total) * 100);
    const filledWidth = Math.round((current / total) * width);
    const emptyWidth = width - filledWidth;

    const filled = this.colorize('█'.repeat(filledWidth), 'green');
    const empty = this.colorize('░'.repeat(emptyWidth), 'gray');

    return `[${filled}${empty}] ${percentage}%`;
  }

  /**
   * Format diff (for schema changes)
   */
  formatDiff(oldValue: any, newValue: any): string {
    const lines: string[] = [];

    lines.push(this.colorize('- ' + JSON.stringify(oldValue), 'red'));
    lines.push(this.colorize('+ ' + JSON.stringify(newValue), 'green'));

    return lines.join('\n');
  }
}
