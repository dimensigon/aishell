/**
 * Comprehensive Output Formatters for AI-Shell
 * Supports JSON, CSV, Table, and XML formats with streaming capabilities
 */

import Table from 'cli-table3';
import chalk from 'chalk';
import { Readable, Transform } from 'stream';

/**
 * Formatter options interface
 */
export interface FormatterOptions {
  format: 'json' | 'csv' | 'table' | 'xml';
  pretty?: boolean;
  headers?: boolean;
  colors?: boolean;
  maxRows?: number;
  streaming?: boolean;
}

/**
 * Table formatting options
 */
export interface TableOptions {
  headers?: boolean;
  colors?: boolean;
  borders?: boolean;
  alignment?: ('left' | 'center' | 'right')[];
  columnWidths?: number[];
  maxCellWidth?: number;
  wordWrap?: boolean;
}

/**
 * XML formatting options
 */
export interface XMLOptions {
  rootElement?: string;
  rowElement?: string;
  indent?: number;
  declaration?: boolean;
}

/**
 * CSV formatting options
 */
export interface CSVOptions {
  delimiter?: string;
  quote?: string;
  escape?: string;
  headers?: boolean;
  lineBreak?: string;
}

/**
 * Type guards for special data types
 */
export class TypeGuards {
  static isDate(value: any): value is Date {
    return value instanceof Date && !isNaN(value.getTime());
  }

  static isBuffer(value: any): value is Buffer {
    return Buffer.isBuffer(value);
  }

  static isNull(value: any): value is null {
    return value === null;
  }

  static isUndefined(value: any): value is undefined {
    return value === undefined;
  }

  static isBigInt(value: any): value is bigint {
    return typeof value === 'bigint';
  }

  static isObject(value: any): value is object {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
  }
}

/**
 * Value serializer for special data types
 */
export class ValueSerializer {
  /**
   * Serialize value to string representation
   */
  static serialize(value: any, format: 'json' | 'csv' | 'table' | 'xml' = 'table'): string {
    if (TypeGuards.isNull(value)) {
      return format === 'json' ? 'null' : 'NULL';
    }

    if (TypeGuards.isUndefined(value)) {
      return format === 'json' ? 'null' : 'undefined';
    }

    if (TypeGuards.isDate(value)) {
      return value.toISOString();
    }

    if (TypeGuards.isBuffer(value)) {
      return format === 'json'
        ? `<Buffer ${value.length} bytes>`
        : `[Binary: ${value.length} bytes]`;
    }

    if (TypeGuards.isBigInt(value)) {
      return value.toString();
    }

    if (TypeGuards.isObject(value)) {
      return JSON.stringify(value);
    }

    return String(value);
  }

  /**
   * Colorize value based on type
   */
  static colorize(value: any, colors: boolean = true): string {
    if (!colors) {
      return this.serialize(value);
    }

    if (TypeGuards.isNull(value) || TypeGuards.isUndefined(value)) {
      return chalk.gray(this.serialize(value));
    }

    if (typeof value === 'boolean') {
      return value ? chalk.green(String(value)) : chalk.red(String(value));
    }

    if (typeof value === 'number' || TypeGuards.isBigInt(value)) {
      return chalk.yellow(this.serialize(value));
    }

    if (TypeGuards.isDate(value)) {
      return chalk.blue(this.serialize(value));
    }

    if (TypeGuards.isBuffer(value)) {
      return chalk.magenta(this.serialize(value));
    }

    if (TypeGuards.isObject(value)) {
      return chalk.cyan(this.serialize(value));
    }

    return String(value);
  }
}

/**
 * JSON Formatter
 */
export class JSONFormatter {
  /**
   * Format data as JSON
   */
  static format(data: any, pretty: boolean = true): string {
    if (pretty) {
      return JSON.stringify(data, this.replacer, 2);
    }
    return JSON.stringify(data, this.replacer);
  }

  /**
   * JSON replacer for special types
   */
  private static replacer(key: string, value: any): any {
    // Check the original value using 'this' context
    // In JSON.stringify replacer, 'this' refers to the object being stringified
    const originalValue = (this as any)[key];

    if (TypeGuards.isBuffer(originalValue)) {
      return `<Buffer ${originalValue.length} bytes>`;
    }

    if (TypeGuards.isBigInt(value)) {
      return value.toString();
    }

    if (TypeGuards.isDate(originalValue)) {
      return originalValue.toISOString();
    }

    return value;
  }

  /**
   * Create streaming JSON formatter
   */
  static createStream(): Transform {
    let first = true;

    return new Transform({
      objectMode: true,
      transform(chunk: any, encoding: string, callback: Function) {
        try {
          const prefix = first ? '[\n' : ',\n';
          first = false;
          const json = JSON.stringify(chunk, JSONFormatter.replacer, 2);
          // Indent array elements
          const indented = json.split('\n').map(line => '  ' + line).join('\n');
          callback(null, prefix + indented);
        } catch (error) {
          callback(error);
        }
      },
      flush(callback: Function) {
        if (!first) {
          callback(null, '\n]\n');
        } else {
          callback(null, '[]\n');
        }
      }
    });
  }
}

/**
 * CSV Formatter
 */
export class CSVFormatter {
  private options: Required<CSVOptions>;

  constructor(options: CSVOptions = {}) {
    this.options = {
      delimiter: options.delimiter || ',',
      quote: options.quote || '"',
      escape: options.escape || '"',
      headers: options.headers !== false,
      lineBreak: options.lineBreak || '\n'
    };
  }

  /**
   * Format data as CSV
   */
  format(data: any[], headers: boolean = true): string {
    if (!data || data.length === 0) {
      return '';
    }

    const columns = this.extractColumns(data);
    const lines: string[] = [];

    // Add headers
    if (headers && this.options.headers) {
      lines.push(this.formatRow(columns));
    }

    // Add data rows
    for (const row of data) {
      const values = columns.map(col => row[col]);
      lines.push(this.formatRow(values));
    }

    return lines.join(this.options.lineBreak);
  }

  /**
   * Format a single row
   */
  private formatRow(values: any[]): string {
    return values.map(value => this.escapeValue(value)).join(this.options.delimiter);
  }

  /**
   * Escape CSV value
   */
  private escapeValue(value: any): string {
    const serialized = ValueSerializer.serialize(value, 'csv');

    // Check if escaping is needed
    const needsQuoting =
      serialized.includes(this.options.delimiter) ||
      serialized.includes(this.options.quote) ||
      serialized.includes('\n') ||
      serialized.includes('\r');

    if (!needsQuoting) {
      return serialized;
    }

    // Escape quotes
    const escaped = serialized.replace(
      new RegExp(this.options.quote, 'g'),
      this.options.escape + this.options.quote
    );

    return this.options.quote + escaped + this.options.quote;
  }

  /**
   * Extract column names from data
   */
  private extractColumns(data: any[]): string[] {
    const columnsSet = new Set<string>();

    for (const row of data) {
      if (TypeGuards.isObject(row)) {
        Object.keys(row).forEach(key => columnsSet.add(key));
      }
    }

    return Array.from(columnsSet);
  }

  /**
   * Create streaming CSV formatter
   */
  createStream(): Transform {
    let headerWritten = false;
    let columns: string[] = [];

    return new Transform({
      objectMode: true,
      transform: (chunk: any, encoding: string, callback: Function) => {
        try {
          // Write headers on first chunk
          if (!headerWritten && this.options.headers) {
            columns = this.extractColumns([chunk]);
            const headerRow = this.formatRow(columns) + this.options.lineBreak;
            headerWritten = true;
            callback(null, headerRow + this.formatRow(columns.map(col => chunk[col])) + this.options.lineBreak);
          } else {
            if (columns.length === 0) {
              columns = this.extractColumns([chunk]);
            }
            const dataRow = this.formatRow(columns.map(col => chunk[col])) + this.options.lineBreak;
            callback(null, dataRow);
          }
        } catch (error) {
          callback(error);
        }
      }
    });
  }
}

/**
 * Table Formatter
 */
export class TableFormatter {
  private options: Required<TableOptions>;

  constructor(options: TableOptions = {}) {
    this.options = {
      headers: options.headers !== false,
      colors: options.colors !== false,
      borders: options.borders !== false,
      alignment: options.alignment || [],
      columnWidths: options.columnWidths || [],
      maxCellWidth: options.maxCellWidth || 50,
      wordWrap: options.wordWrap !== false
    };
  }

  /**
   * Format data as table
   */
  format(data: any[], options?: Partial<TableOptions>): string {
    if (!data || data.length === 0) {
      return this.options.colors ? chalk.yellow('No results found') : 'No results found';
    }

    const mergedOptions = { ...this.options, ...options };
    const columns = this.extractColumns(data);

    // Create table configuration
    const tableConfig: any = {
      head: mergedOptions.headers && mergedOptions.colors
        ? columns.map(col => chalk.cyan.bold(col))
        : columns,
      style: {
        head: [],
        border: mergedOptions.borders && mergedOptions.colors ? ['gray'] : []
      },
      wordWrap: mergedOptions.wordWrap
    };

    // Set column widths if specified
    if (mergedOptions.columnWidths.length > 0) {
      tableConfig.colWidths = mergedOptions.columnWidths;
    } else {
      tableConfig.colWidths = this.calculateColumnWidths(columns, data);
    }

    // Set column alignment if specified
    if (mergedOptions.alignment.length > 0) {
      tableConfig.colAligns = mergedOptions.alignment;
    }

    const table = new Table(tableConfig);

    // Add rows
    for (const row of data) {
      const values = columns.map(col => {
        const value = row[col];
        const serialized = ValueSerializer.serialize(value, 'table');

        // Truncate if needed
        if (serialized.length > mergedOptions.maxCellWidth) {
          return serialized.substring(0, mergedOptions.maxCellWidth - 3) + '...';
        }

        return mergedOptions.colors
          ? ValueSerializer.colorize(value, true)
          : serialized;
      });
      table.push(values);
    }

    return table.toString();
  }

  /**
   * Extract column names from data
   */
  private extractColumns(data: any[]): string[] {
    const columnsSet = new Set<string>();

    for (const row of data) {
      if (TypeGuards.isObject(row)) {
        Object.keys(row).forEach(key => columnsSet.add(key));
      }
    }

    return Array.from(columnsSet);
  }

  /**
   * Calculate optimal column widths
   */
  private calculateColumnWidths(columns: string[], data: any[]): number[] {
    return columns.map(col => {
      // Get max width for this column
      const values = data.map(row => {
        const value = row[col];
        return ValueSerializer.serialize(value, 'table');
      });

      const maxValueWidth = Math.max(...values.map(v => v.length), 0);
      const headerWidth = col.length;

      return Math.min(
        Math.max(maxValueWidth, headerWidth) + 2,
        this.options.maxCellWidth
      );
    });
  }

  /**
   * Create streaming table formatter
   * Note: Streaming tables are complex due to column width calculation
   * This returns rows as they come, headers first
   */
  createStream(): Transform {
    let headerWritten = false;
    let columns: string[] = [];

    return new Transform({
      objectMode: true,
      transform: (chunk: any, encoding: string, callback: Function) => {
        try {
          if (!headerWritten) {
            columns = this.extractColumns([chunk]);

            // Simple header
            const header = columns.join(' | ');
            const separator = columns.map(c => '-'.repeat(c.length)).join('-+-');
            headerWritten = true;

            callback(null, header + '\n' + separator + '\n' + this.formatRow(chunk, columns) + '\n');
          } else {
            if (columns.length === 0) {
              columns = this.extractColumns([chunk]);
            }
            callback(null, this.formatRow(chunk, columns) + '\n');
          }
        } catch (error) {
          callback(error);
        }
      }
    });
  }

  /**
   * Format a single row for streaming
   */
  private formatRow(row: any, columns: string[]): string {
    return columns.map(col => {
      const value = row[col];
      const serialized = ValueSerializer.serialize(value, 'table');
      return serialized.substring(0, this.options.maxCellWidth);
    }).join(' | ');
  }
}

/**
 * XML Formatter
 */
export class XMLFormatter {
  private options: Required<XMLOptions>;

  constructor(options: XMLOptions = {}) {
    this.options = {
      rootElement: options.rootElement || 'results',
      rowElement: options.rowElement || 'row',
      indent: options.indent || 2,
      declaration: options.declaration !== false
    };
  }

  /**
   * Format data as XML
   */
  format(data: any): string {
    const lines: string[] = [];

    // XML declaration
    if (this.options.declaration) {
      lines.push('<?xml version="1.0" encoding="UTF-8"?>');
    }

    // Root element
    lines.push(`<${this.options.rootElement}>`);

    // Convert data to XML
    if (Array.isArray(data)) {
      for (const item of data) {
        lines.push(this.formatElement(item, this.options.rowElement, 1));
      }
    } else {
      lines.push(this.formatElement(data, 'data', 1));
    }

    lines.push(`</${this.options.rootElement}>`);

    return lines.join('\n');
  }

  /**
   * Format a single element
   */
  private formatElement(data: any, tagName: string, level: number): string {
    const indent = ' '.repeat(level * this.options.indent);

    if (TypeGuards.isNull(data) || TypeGuards.isUndefined(data)) {
      return `${indent}<${tagName} />`;
    }

    if (Array.isArray(data)) {
      const lines: string[] = [];
      lines.push(`${indent}<${tagName}>`);
      for (let i = 0; i < data.length; i++) {
        lines.push(this.formatElement(data[i], 'item', level + 1));
      }
      lines.push(`${indent}</${tagName}>`);
      return lines.join('\n');
    }

    if (TypeGuards.isObject(data)) {
      const lines: string[] = [];
      lines.push(`${indent}<${tagName}>`);

      for (const [key, value] of Object.entries(data)) {
        const safeName = this.sanitizeTagName(key);
        lines.push(this.formatElement(value, safeName, level + 1));
      }

      lines.push(`${indent}</${tagName}>`);
      return lines.join('\n');
    }

    // Primitive value
    const value = this.escapeXML(ValueSerializer.serialize(data, 'xml'));
    return `${indent}<${tagName}>${value}</${tagName}>`;
  }

  /**
   * Escape XML special characters
   */
  private escapeXML(value: string): string {
    return value
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&apos;');
  }

  /**
   * Sanitize tag name for XML
   */
  private sanitizeTagName(name: string): string {
    // XML tag names must start with letter or underscore
    // and can only contain letters, digits, hyphens, underscores, and periods
    let sanitized = name.replace(/[^a-zA-Z0-9_.-]/g, '_');

    if (!/^[a-zA-Z_]/.test(sanitized)) {
      sanitized = '_' + sanitized;
    }

    return sanitized;
  }

  /**
   * Create streaming XML formatter
   */
  createStream(): Transform {
    let first = true;

    return new Transform({
      objectMode: true,
      transform: (chunk: any, encoding: string, callback: Function) => {
        try {
          if (first) {
            let output = '';
            if (this.options.declaration) {
              output += '<?xml version="1.0" encoding="UTF-8"?>\n';
            }
            output += `<${this.options.rootElement}>\n`;
            output += this.formatElement(chunk, this.options.rowElement, 1) + '\n';
            first = false;
            callback(null, output);
          } else {
            callback(null, this.formatElement(chunk, this.options.rowElement, 1) + '\n');
          }
        } catch (error) {
          callback(error);
        }
      },
      flush: (callback: Function) => {
        if (!first) {
          callback(null, `</${this.options.rootElement}>\n`);
        } else {
          let output = '';
          if (this.options.declaration) {
            output += '<?xml version="1.0" encoding="UTF-8"?>\n';
          }
          output += `<${this.options.rootElement}></${this.options.rootElement}>\n`;
          callback(null, output);
        }
      }
    });
  }
}

/**
 * Main Result Formatter
 */
export class ResultFormatter {
  /**
   * Format data based on options
   */
  static format(data: any, options: FormatterOptions): string {
    const { format, pretty = true, headers = true, colors = true, maxRows } = options;

    // Limit rows if specified
    let limitedData = data;
    if (maxRows && Array.isArray(data)) {
      limitedData = data.slice(0, maxRows);
    }

    switch (format) {
      case 'json':
        return this.formatJSON(limitedData, pretty);

      case 'csv':
        return this.formatCSV(limitedData, headers);

      case 'table':
        return this.formatTable(limitedData, { headers, colors });

      case 'xml':
        return this.formatXML(limitedData);

      default:
        throw new Error(`Unsupported format: ${format}`);
    }
  }

  /**
   * Format as JSON
   */
  static formatJSON(data: any, pretty: boolean = true): string {
    return JSONFormatter.format(data, pretty);
  }

  /**
   * Format as CSV
   */
  static formatCSV(data: any[], headers: boolean = true): string {
    const formatter = new CSVFormatter({ headers });
    return formatter.format(data, headers);
  }

  /**
   * Format as table
   */
  static formatTable(data: any[], options: TableOptions = {}): string {
    const formatter = new TableFormatter(options);
    return formatter.format(data, options);
  }

  /**
   * Format as XML
   */
  static formatXML(data: any): string {
    const formatter = new XMLFormatter();
    return formatter.format(data);
  }

  /**
   * Create streaming formatter
   */
  static createStreamingFormatter(format: 'json' | 'csv' | 'table' | 'xml'): Transform {
    switch (format) {
      case 'json':
        return JSONFormatter.createStream();

      case 'csv':
        return new CSVFormatter().createStream();

      case 'table':
        return new TableFormatter().createStream();

      case 'xml':
        return new XMLFormatter().createStream();

      default:
        throw new Error(`Unsupported streaming format: ${format}`);
    }
  }

  /**
   * Format large dataset with streaming
   */
  static async formatStreaming(
    dataSource: Readable,
    format: 'json' | 'csv' | 'table' | 'xml',
    outputStream: NodeJS.WritableStream = process.stdout
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const formatter = this.createStreamingFormatter(format);

      dataSource
        .pipe(formatter)
        .pipe(outputStream)
        .on('finish', resolve)
        .on('error', reject);
    });
  }
}

// Note: Classes are already exported above, no need to re-export
