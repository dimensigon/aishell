/**
 * Tests for Comprehensive Output Formatters
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  ResultFormatter,
  JSONFormatter,
  CSVFormatter,
  TableFormatter,
  XMLFormatter,
  ValueSerializer,
  TypeGuards,
  FormatterOptions,
  TableOptions,
  CSVOptions,
  XMLOptions
} from '../../src/cli/formatters';
import { Readable, Writable } from 'stream';

describe('TypeGuards', () => {
  it('should identify dates correctly', () => {
    expect(TypeGuards.isDate(new Date())).toBe(true);
    expect(TypeGuards.isDate('2024-01-01')).toBe(false);
    expect(TypeGuards.isDate(null)).toBe(false);
  });

  it('should identify buffers correctly', () => {
    expect(TypeGuards.isBuffer(Buffer.from('test'))).toBe(true);
    expect(TypeGuards.isBuffer('test')).toBe(false);
    expect(TypeGuards.isBuffer(null)).toBe(false);
  });

  it('should identify null correctly', () => {
    expect(TypeGuards.isNull(null)).toBe(true);
    expect(TypeGuards.isNull(undefined)).toBe(false);
    expect(TypeGuards.isNull(0)).toBe(false);
  });

  it('should identify undefined correctly', () => {
    expect(TypeGuards.isUndefined(undefined)).toBe(true);
    expect(TypeGuards.isUndefined(null)).toBe(false);
  });

  it('should identify bigint correctly', () => {
    expect(TypeGuards.isBigInt(BigInt(123))).toBe(true);
    expect(TypeGuards.isBigInt(123)).toBe(false);
  });

  it('should identify objects correctly', () => {
    expect(TypeGuards.isObject({})).toBe(true);
    expect(TypeGuards.isObject([])).toBe(false);
    expect(TypeGuards.isObject(null)).toBe(false);
  });
});

describe('ValueSerializer', () => {
  it('should serialize null values', () => {
    expect(ValueSerializer.serialize(null, 'json')).toBe('null');
    expect(ValueSerializer.serialize(null, 'csv')).toBe('NULL');
    expect(ValueSerializer.serialize(null, 'table')).toBe('NULL');
  });

  it('should serialize undefined values', () => {
    expect(ValueSerializer.serialize(undefined, 'json')).toBe('null');
    expect(ValueSerializer.serialize(undefined, 'csv')).toBe('undefined');
  });

  it('should serialize dates', () => {
    const date = new Date('2024-01-01T00:00:00.000Z');
    expect(ValueSerializer.serialize(date)).toBe('2024-01-01T00:00:00.000Z');
  });

  it('should serialize buffers', () => {
    const buffer = Buffer.from('test');
    expect(ValueSerializer.serialize(buffer, 'json')).toContain('<Buffer');
    expect(ValueSerializer.serialize(buffer, 'csv')).toContain('[Binary:');
  });

  it('should serialize bigint', () => {
    const bigInt = BigInt('9007199254740991');
    expect(ValueSerializer.serialize(bigInt)).toBe('9007199254740991');
  });

  it('should serialize objects as JSON', () => {
    const obj = { foo: 'bar' };
    expect(ValueSerializer.serialize(obj)).toBe('{"foo":"bar"}');
  });

  it('should colorize values when enabled', () => {
    const result = ValueSerializer.colorize(123, true);
    expect(result).toContain('123');
  });

  it('should not colorize when disabled', () => {
    const result = ValueSerializer.colorize(123, false);
    expect(result).toBe('123');
  });
});

describe('JSONFormatter', () => {
  const sampleData = [
    { id: 1, name: 'Alice', age: 30 },
    { id: 2, name: 'Bob', age: 25 }
  ];

  it('should format JSON with pretty print', () => {
    const result = JSONFormatter.format(sampleData, true);
    expect(result).toContain('  ');
    expect(result).toContain('"id": 1');
    expect(result).toContain('"name": "Alice"');
  });

  it('should format JSON without pretty print', () => {
    const result = JSONFormatter.format(sampleData, false);
    expect(result).not.toContain('  ');
    expect(result).toContain('"id":1');
  });

  it('should handle special types in JSON', () => {
    const data = {
      date: new Date('2024-01-01'),
      bigint: BigInt(123),
      buffer: Buffer.from('test')
    };
    const result = JSONFormatter.format(data, true);
    expect(result).toContain('2024-01-01');
    expect(result).toContain('123');
    expect(result).toContain('<Buffer'); // Our custom replacer for buffers
  });

  it('should create streaming JSON formatter', async () => {
    const stream = JSONFormatter.createStream();
    const chunks: string[] = [];

    stream.on('data', (chunk: string) => {
      chunks.push(chunk);
    });

    await new Promise<void>((resolve) => {
      stream.on('end', resolve);
      stream.write({ id: 1, name: 'Alice' });
      stream.write({ id: 2, name: 'Bob' });
      stream.end();
    });

    const result = chunks.join('');
    expect(result).toContain('[');
    expect(result).toContain(']');
    expect(result).toContain('Alice');
    expect(result).toContain('Bob');
  });
});

describe('CSVFormatter', () => {
  const sampleData = [
    { id: 1, name: 'Alice', email: 'alice@example.com' },
    { id: 2, name: 'Bob', email: 'bob@example.com' }
  ];

  it('should format CSV with headers', () => {
    const formatter = new CSVFormatter();
    const result = formatter.format(sampleData, true);

    const lines = result.split('\n');
    expect(lines[0]).toContain('id');
    expect(lines[0]).toContain('name');
    expect(lines[0]).toContain('email');
    expect(lines[1]).toContain('1');
    expect(lines[1]).toContain('Alice');
  });

  it('should format CSV without headers', () => {
    const formatter = new CSVFormatter({ headers: false });
    const result = formatter.format(sampleData, false);

    const lines = result.split('\n');
    expect(lines[0]).not.toContain('id');
    expect(lines[0]).toContain('1');
  });

  it('should escape CSV values with commas', () => {
    const formatter = new CSVFormatter();
    const data = [{ name: 'Smith, John' }];
    const result = formatter.format(data);

    expect(result).toContain('"Smith, John"');
  });

  it('should escape CSV values with quotes', () => {
    const formatter = new CSVFormatter();
    const data = [{ name: 'John "Johnny" Smith' }];
    const result = formatter.format(data);

    expect(result).toContain('""Johnny""');
  });

  it('should handle empty data', () => {
    const formatter = new CSVFormatter();
    const result = formatter.format([]);
    expect(result).toBe('');
  });

  it('should use custom delimiter', () => {
    const formatter = new CSVFormatter({ delimiter: ';' });
    const data = [{ a: 1, b: 2 }];
    const result = formatter.format(data);

    expect(result).toContain(';');
    expect(result).not.toContain(',');
  });

  it('should create streaming CSV formatter', async () => {
    const formatter = new CSVFormatter();
    const stream = formatter.createStream();
    const chunks: string[] = [];

    stream.on('data', (chunk: string) => {
      chunks.push(chunk);
    });

    await new Promise<void>((resolve) => {
      stream.on('end', resolve);
      stream.write({ id: 1, name: 'Alice' });
      stream.write({ id: 2, name: 'Bob' });
      stream.end();
    });

    const result = chunks.join('');
    expect(result).toContain('id');
    expect(result).toContain('name');
    expect(result).toContain('Alice');
    expect(result).toContain('Bob');
  });
});

describe('TableFormatter', () => {
  const sampleData = [
    { id: 1, name: 'Alice', status: true },
    { id: 2, name: 'Bob', status: false }
  ];

  it('should format table with headers', () => {
    const formatter = new TableFormatter({ colors: false });
    const result = formatter.format(sampleData);

    expect(result).toContain('id');
    expect(result).toContain('name');
    expect(result).toContain('status');
    expect(result).toContain('Alice');
    expect(result).toContain('Bob');
  });

  it('should format table without colors', () => {
    const formatter = new TableFormatter({ colors: false });
    const result = formatter.format(sampleData);

    // Should not contain ANSI color codes
    expect(result).not.toMatch(/\u001b\[/);
  });

  it('should handle empty data', () => {
    const formatter = new TableFormatter({ colors: false });
    const result = formatter.format([]);

    expect(result).toContain('No results');
  });

  it('should truncate long values', () => {
    const formatter = new TableFormatter({ maxCellWidth: 10, colors: false });
    const data = [{ text: 'This is a very long text that should be truncated' }];
    const result = formatter.format(data);

    expect(result).toContain('...');
  });

  it('should calculate column widths', () => {
    const formatter = new TableFormatter({ colors: false });
    const data = [
      { short: 'a', long: 'This is a longer value' },
      { short: 'b', long: 'x' }
    ];
    const result = formatter.format(data);

    expect(result).toBeTruthy();
  });

  it('should create streaming table formatter', async () => {
    const formatter = new TableFormatter({ colors: false });
    const stream = formatter.createStream();
    const chunks: string[] = [];

    stream.on('data', (chunk: string) => {
      chunks.push(chunk);
    });

    await new Promise<void>((resolve) => {
      stream.on('end', resolve);
      stream.write({ id: 1, name: 'Alice' });
      stream.write({ id: 2, name: 'Bob' });
      stream.end();
    });

    const result = chunks.join('');
    expect(result).toContain('id');
    expect(result).toContain('name');
  });
});

describe('XMLFormatter', () => {
  const sampleData = [
    { id: 1, name: 'Alice', active: true },
    { id: 2, name: 'Bob', active: false }
  ];

  it('should format XML with declaration', () => {
    const formatter = new XMLFormatter({ declaration: true });
    const result = formatter.format(sampleData);

    expect(result).toContain('<?xml version="1.0"');
    expect(result).toContain('<results>');
    expect(result).toContain('</results>');
  });

  it('should format XML without declaration', () => {
    const formatter = new XMLFormatter({ declaration: false });
    const result = formatter.format(sampleData);

    expect(result).not.toContain('<?xml');
    expect(result).toContain('<results>');
  });

  it('should use custom root element', () => {
    const formatter = new XMLFormatter({ rootElement: 'data' });
    const result = formatter.format(sampleData);

    expect(result).toContain('<data>');
    expect(result).toContain('</data>');
  });

  it('should use custom row element', () => {
    const formatter = new XMLFormatter({ rowElement: 'item' });
    const result = formatter.format(sampleData);

    expect(result).toContain('<item>');
    expect(result).toContain('</item>');
  });

  it('should escape XML special characters', () => {
    const formatter = new XMLFormatter();
    const data = [{ text: '<tag> & "quotes" \'apostrophe\'' }];
    const result = formatter.format(data);

    expect(result).toContain('&lt;');
    expect(result).toContain('&gt;');
    expect(result).toContain('&amp;');
    expect(result).toContain('&quot;');
    expect(result).toContain('&apos;');
  });

  it('should sanitize tag names', () => {
    const formatter = new XMLFormatter();
    const data = [{ 'invalid-tag!': 'value', '123number': 'value2' }];
    const result = formatter.format(data);

    expect(result).toContain('<invalid-tag_>');
    expect(result).toContain('<_123number>');
  });

  it('should handle nested objects', () => {
    const formatter = new XMLFormatter();
    const data = [{ user: { name: 'Alice', age: 30 } }];
    const result = formatter.format(data);

    expect(result).toContain('<user>');
    expect(result).toContain('<name>Alice</name>');
    expect(result).toContain('<age>30</age>');
  });

  it('should handle arrays', () => {
    const formatter = new XMLFormatter();
    const data = { items: [1, 2, 3] };
    const result = formatter.format(data);

    expect(result).toContain('<items>');
    expect(result).toContain('<item>1</item>');
  });

  it('should handle null and undefined', () => {
    const formatter = new XMLFormatter();
    const data = [{ nullValue: null, undefinedValue: undefined }];
    const result = formatter.format(data);

    expect(result).toContain('<nullValue />');
    expect(result).toContain('<undefinedValue />');
  });

  it('should create streaming XML formatter', async () => {
    const formatter = new XMLFormatter({ declaration: false });
    const stream = formatter.createStream();
    const chunks: string[] = [];

    stream.on('data', (chunk: string) => {
      chunks.push(chunk);
    });

    await new Promise<void>((resolve) => {
      stream.on('end', resolve);
      stream.write({ id: 1, name: 'Alice' });
      stream.write({ id: 2, name: 'Bob' });
      stream.end();
    });

    const result = chunks.join('');
    expect(result).toContain('<results>');
    expect(result).toContain('</results>');
    expect(result).toContain('Alice');
    expect(result).toContain('Bob');
  });
});

describe('ResultFormatter', () => {
  const sampleData = [
    { id: 1, name: 'Alice', score: 95.5 },
    { id: 2, name: 'Bob', score: 87.3 }
  ];

  it('should format as JSON', () => {
    const result = ResultFormatter.format(sampleData, { format: 'json', pretty: true });
    expect(result).toContain('"id": 1');
    expect(result).toContain('"name": "Alice"');
  });

  it('should format as CSV', () => {
    const result = ResultFormatter.format(sampleData, { format: 'csv', headers: true });
    expect(result).toContain('id,name,score');
    expect(result).toContain('1,Alice,95.5');
  });

  it('should format as table', () => {
    const result = ResultFormatter.format(sampleData, { format: 'table', colors: false });
    expect(result).toContain('Alice');
    expect(result).toContain('Bob');
  });

  it('should format as XML', () => {
    const result = ResultFormatter.format(sampleData, { format: 'xml' });
    expect(result).toContain('<results>');
    expect(result).toContain('<name>Alice</name>');
  });

  it('should limit rows when maxRows is specified', () => {
    const largeData = Array.from({ length: 100 }, (_, i) => ({ id: i }));
    const result = ResultFormatter.format(largeData, { format: 'json', maxRows: 10 });
    const parsed = JSON.parse(result);
    expect(parsed).toHaveLength(10);
  });

  it('should throw error for unsupported format', () => {
    expect(() => {
      ResultFormatter.format(sampleData, { format: 'invalid' as any });
    }).toThrow('Unsupported format');
  });

  it('should create streaming formatter for JSON', () => {
    const stream = ResultFormatter.createStreamingFormatter('json');
    expect(stream).toBeDefined();
  });

  it('should create streaming formatter for CSV', () => {
    const stream = ResultFormatter.createStreamingFormatter('csv');
    expect(stream).toBeDefined();
  });

  it('should create streaming formatter for table', () => {
    const stream = ResultFormatter.createStreamingFormatter('table');
    expect(stream).toBeDefined();
  });

  it('should create streaming formatter for XML', () => {
    const stream = ResultFormatter.createStreamingFormatter('xml');
    expect(stream).toBeDefined();
  });

  it('should handle streaming data', async () => {
    // Create a readable stream from array
    const dataSource = new Readable({
      objectMode: true,
      read() {
        if (sampleData.length === 0) {
          this.push(null);
        } else {
          this.push(sampleData.shift());
        }
      }
    });

    // Create output stream
    const chunks: string[] = [];
    const outputStream = new Writable({
      write(chunk, encoding, callback) {
        chunks.push(chunk.toString());
        callback();
      }
    });

    // Reset sample data
    sampleData.push({ id: 1, name: 'Alice', score: 95.5 });
    sampleData.push({ id: 2, name: 'Bob', score: 87.3 });

    await ResultFormatter.formatStreaming(dataSource, 'json', outputStream);

    const result = chunks.join('');
    expect(result).toBeTruthy();
  });
});

describe('Integration Tests', () => {
  it('should handle complex data with all types', () => {
    const complexData = [
      {
        id: 1,
        name: 'Test',
        date: new Date('2024-01-01'),
        bigInt: BigInt(123),
        buffer: Buffer.from('test'),
        nested: { foo: 'bar' },
        nullValue: null,
        undefinedValue: undefined,
        boolTrue: true,
        boolFalse: false
      }
    ];

    // Test all formats
    const jsonResult = ResultFormatter.format(complexData, { format: 'json' });
    expect(jsonResult).toBeTruthy();

    const csvResult = ResultFormatter.format(complexData, { format: 'csv' });
    expect(csvResult).toBeTruthy();

    const tableResult = ResultFormatter.format(complexData, { format: 'table', colors: false });
    expect(tableResult).toBeTruthy();

    const xmlResult = ResultFormatter.format(complexData, { format: 'xml' });
    expect(xmlResult).toBeTruthy();
  });

  it('should handle large datasets efficiently', () => {
    const largeData = Array.from({ length: 10000 }, (_, i) => ({
      id: i,
      name: `User ${i}`,
      email: `user${i}@example.com`,
      score: Math.random() * 100
    }));

    const start = Date.now();
    const result = ResultFormatter.format(largeData, { format: 'csv', maxRows: 1000 });
    const duration = Date.now() - start;

    expect(result).toBeTruthy();
    expect(duration).toBeLessThan(1000); // Should complete in less than 1 second
  });

  it('should preserve data accuracy across formats', () => {
    const originalData = [
      { id: 1, value: 123.456 },
      { id: 2, value: 789.012 }
    ];

    // JSON round-trip
    const jsonStr = ResultFormatter.format(originalData, { format: 'json' });
    const jsonParsed = JSON.parse(jsonStr);
    expect(jsonParsed[0].value).toBe(123.456);

    // CSV should preserve values
    const csvStr = ResultFormatter.format(originalData, { format: 'csv' });
    expect(csvStr).toContain('123.456');
    expect(csvStr).toContain('789.012');
  });
});
