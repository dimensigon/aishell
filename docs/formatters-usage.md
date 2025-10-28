# Output Formatters Usage Guide

Comprehensive formatters for AI-Shell supporting JSON, CSV, Table, and XML output formats with streaming capabilities.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Formatters](#formatters)
  - [JSON Formatter](#json-formatter)
  - [CSV Formatter](#csv-formatter)
  - [Table Formatter](#table-formatter)
  - [XML Formatter](#xml-formatter)
- [Streaming Support](#streaming-support)
- [Special Data Types](#special-data-types)
- [Examples](#examples)

## Installation

The formatters are included in AI-Shell. No additional installation required.

```bash
npm install ai-shell
```

## Quick Start

```typescript
import { ResultFormatter } from './src/cli/formatters';

const data = [
  { id: 1, name: 'Alice', email: 'alice@example.com' },
  { id: 2, name: 'Bob', email: 'bob@example.com' }
];

// Format as JSON
const json = ResultFormatter.format(data, { format: 'json', pretty: true });

// Format as CSV
const csv = ResultFormatter.format(data, { format: 'csv', headers: true });

// Format as Table
const table = ResultFormatter.format(data, { format: 'table', colors: true });

// Format as XML
const xml = ResultFormatter.format(data, { format: 'xml' });
```

## Formatters

### JSON Formatter

Pretty-print or compact JSON output with support for special data types.

```typescript
import { JSONFormatter } from './src/cli/formatters';

const data = {
  id: 1,
  name: 'Alice',
  createdAt: new Date('2024-01-01'),
  balance: BigInt('9007199254740991')
};

// Pretty print
const pretty = JSONFormatter.format(data, true);
console.log(pretty);
/*
{
  "id": 1,
  "name": "Alice",
  "createdAt": "2024-01-01T00:00:00.000Z",
  "balance": "9007199254740991"
}
*/

// Compact
const compact = JSONFormatter.format(data, false);
console.log(compact);
// {"id":1,"name":"Alice","createdAt":"2024-01-01T00:00:00.000Z","balance":"9007199254740991"}
```

**Options:**
- `pretty: boolean` - Enable pretty printing (default: true)

**Features:**
- Automatic Date serialization to ISO 8601
- BigInt conversion to string
- Buffer representation
- Proper null/undefined handling

### CSV Formatter

RFC 4180 compliant CSV with proper escaping and customization.

```typescript
import { CSVFormatter } from './src/cli/formatters';

const data = [
  { id: 1, name: 'Smith, John', email: 'john@example.com' },
  { id: 2, name: 'Doe, Jane', email: 'jane@example.com' }
];

// Default CSV
const formatter = new CSVFormatter();
const csv = formatter.format(data);
console.log(csv);
/*
id,name,email
1,"Smith, John",john@example.com
2,"Doe, Jane",jane@example.com
*/

// Custom delimiter
const tsvFormatter = new CSVFormatter({ delimiter: '\t' });
const tsv = tsvFormatter.format(data);

// Custom options
const customFormatter = new CSVFormatter({
  delimiter: ';',
  quote: "'",
  headers: false,
  lineBreak: '\r\n'
});
```

**Options:**
- `delimiter: string` - Field separator (default: ',')
- `quote: string` - Quote character (default: '"')
- `escape: string` - Escape character (default: '"')
- `headers: boolean` - Include header row (default: true)
- `lineBreak: string` - Line ending (default: '\n')

**Features:**
- Automatic value escaping
- Handles commas, quotes, newlines
- Custom delimiters for TSV, etc.
- Proper null/undefined handling

### Table Formatter

Beautiful ASCII tables with colors, borders, and alignment.

```typescript
import { TableFormatter } from './src/cli/formatters';

const data = [
  { id: 1, name: 'Alice', status: true, score: 95.5 },
  { id: 2, name: 'Bob', status: false, score: 87.3 }
];

// Default table
const formatter = new TableFormatter();
const table = formatter.format(data);
console.log(table);
/*
┌────┬───────┬────────┬───────┐
│ id │ name  │ status │ score │
├────┼───────┼────────┼───────┤
│ 1  │ Alice │ true   │ 95.5  │
│ 2  │ Bob   │ false  │ 87.3  │
└────┴───────┴────────┴───────┘
*/

// Without colors
const noColorFormatter = new TableFormatter({ colors: false });
const noColorTable = noColorFormatter.format(data);

// Custom width and alignment
const customFormatter = new TableFormatter({
  maxCellWidth: 20,
  columnWidths: [5, 15, 10, 10],
  alignment: ['right', 'left', 'center', 'right'],
  borders: true,
  wordWrap: true
});
```

**Options:**
- `headers: boolean` - Show headers (default: true)
- `colors: boolean` - Enable colors (default: true)
- `borders: boolean` - Show borders (default: true)
- `alignment: string[]` - Column alignment (left/center/right)
- `columnWidths: number[]` - Fixed column widths
- `maxCellWidth: number` - Maximum cell width (default: 50)
- `wordWrap: boolean` - Enable word wrap (default: true)

**Features:**
- Auto-calculated column widths
- Color-coded data types
- Automatic value truncation
- Word wrapping for long content

### XML Formatter

Well-formed XML output with proper escaping and customization.

```typescript
import { XMLFormatter } from './src/cli/formatters';

const data = [
  { id: 1, name: 'Alice', active: true },
  { id: 2, name: 'Bob', active: false }
];

// Default XML
const formatter = new XMLFormatter();
const xml = formatter.format(data);
console.log(xml);
/*
<?xml version="1.0" encoding="UTF-8"?>
<results>
  <row>
    <id>1</id>
    <name>Alice</name>
    <active>true</active>
  </row>
  <row>
    <id>2</id>
    <name>Bob</name>
    <active>false</active>
  </row>
</results>
*/

// Custom options
const customFormatter = new XMLFormatter({
  rootElement: 'users',
  rowElement: 'user',
  indent: 4,
  declaration: false
});

const customXml = customFormatter.format(data);
console.log(customXml);
/*
<users>
    <user>
        <id>1</id>
        <name>Alice</name>
        <active>true</active>
    </user>
</users>
*/
```

**Options:**
- `rootElement: string` - Root tag name (default: 'results')
- `rowElement: string` - Row tag name (default: 'row')
- `indent: number` - Indentation spaces (default: 2)
- `declaration: boolean` - Include XML declaration (default: true)

**Features:**
- Automatic XML escaping (&, <, >, ", ')
- Tag name sanitization
- Nested object support
- Array handling

## Streaming Support

Efficiently handle large datasets with streaming formatters.

### Streaming JSON

```typescript
import { JSONFormatter } from './src/cli/formatters';
import { Readable } from 'stream';

// Create data source
const dataSource = Readable.from([
  { id: 1, name: 'Alice' },
  { id: 2, name: 'Bob' },
  { id: 3, name: 'Charlie' }
]);

// Create JSON stream
const jsonStream = JSONFormatter.createStream();

dataSource
  .pipe(jsonStream)
  .pipe(process.stdout);

// Output:
// [
//   { "id": 1, "name": "Alice" },
//   { "id": 2, "name": "Bob" },
//   { "id": 3, "name": "Charlie" }
// ]
```

### Streaming CSV

```typescript
import { CSVFormatter } from './src/cli/formatters';

const formatter = new CSVFormatter({ headers: true });
const csvStream = formatter.createStream();

dataSource
  .pipe(csvStream)
  .pipe(process.stdout);

// Output:
// id,name
// 1,Alice
// 2,Bob
// 3,Charlie
```

### Streaming Table

```typescript
import { TableFormatter } from './src/cli/formatters';

const formatter = new TableFormatter({ colors: false });
const tableStream = formatter.createStream();

dataSource
  .pipe(tableStream)
  .pipe(process.stdout);
```

### High-Level Streaming API

```typescript
import { ResultFormatter } from './src/cli/formatters';
import { Readable } from 'stream';

async function exportLargeDataset() {
  // Create data source (e.g., database query stream)
  const dataSource = Readable.from(getLargeDataset());

  // Stream to file
  const fs = require('fs');
  const outputStream = fs.createWriteStream('output.json');

  await ResultFormatter.formatStreaming(
    dataSource,
    'json',
    outputStream
  );

  console.log('Export complete');
}
```

## Special Data Types

The formatters handle various JavaScript data types intelligently.

### Dates

```typescript
const data = [{
  id: 1,
  createdAt: new Date('2024-01-01T12:00:00Z'),
  updatedAt: new Date()
}];

// All formatters convert dates to ISO 8601
const json = ResultFormatter.format(data, { format: 'json' });
// createdAt: "2024-01-01T12:00:00.000Z"
```

### BigInt

```typescript
const data = [{
  id: BigInt('9007199254740991'),
  value: BigInt(123)
}];

// BigInt values are converted to strings
const json = ResultFormatter.format(data, { format: 'json' });
// id: "9007199254740991"
```

### Buffers

```typescript
const data = [{
  id: 1,
  data: Buffer.from('Hello, World!')
}];

// Buffers show byte count
const table = ResultFormatter.format(data, { format: 'table' });
// data: [Binary: 13 bytes]

const json = ResultFormatter.format(data, { format: 'json' });
// data: "<Buffer 13 bytes>"
```

### Null and Undefined

```typescript
const data = [{
  id: 1,
  value: null,
  missing: undefined
}];

// JSON: both become null
const json = ResultFormatter.format(data, { format: 'json' });
// { "id": 1, "value": null, "missing": null }

// CSV/Table: distinct representation
const csv = ResultFormatter.format(data, { format: 'csv' });
// 1,NULL,undefined
```

### Nested Objects

```typescript
const data = [{
  id: 1,
  user: {
    name: 'Alice',
    email: 'alice@example.com'
  }
}];

// JSON: preserved as-is
const json = ResultFormatter.format(data, { format: 'json' });

// CSV/Table: JSON stringified
const csv = ResultFormatter.format(data, { format: 'csv' });
// 1,"{""name"":""Alice"",""email"":""alice@example.com""}"

// XML: nested elements
const xml = ResultFormatter.format(data, { format: 'xml' });
/*
<row>
  <id>1</id>
  <user>
    <name>Alice</name>
    <email>alice@example.com</email>
  </user>
</row>
*/
```

## Examples

### Database Query Results

```typescript
import { ResultFormatter } from './src/cli/formatters';

async function exportQueryResults(format: 'json' | 'csv' | 'xml') {
  const results = await db.query('SELECT * FROM users LIMIT 1000');

  const output = ResultFormatter.format(results, {
    format,
    pretty: true,
    headers: true,
    colors: false,
    maxRows: 100
  });

  fs.writeFileSync(`export.${format}`, output);
}
```

### API Response Formatting

```typescript
app.get('/api/users', async (req, res) => {
  const users = await getUsers();
  const format = req.query.format || 'json';

  if (format === 'json') {
    res.json(users);
  } else if (format === 'csv') {
    const csv = ResultFormatter.format(users, { format: 'csv' });
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename=users.csv');
    res.send(csv);
  } else if (format === 'xml') {
    const xml = ResultFormatter.format(users, { format: 'xml' });
    res.setHeader('Content-Type', 'application/xml');
    res.send(xml);
  }
});
```

### CLI Output

```typescript
import { ResultFormatter } from './src/cli/formatters';

async function displayResults(query: string, format: string) {
  const results = await executeQuery(query);

  console.log(ResultFormatter.format(results, {
    format: format as any,
    colors: process.stdout.isTTY,
    maxRows: process.env.MAX_ROWS ? parseInt(process.env.MAX_ROWS) : undefined
  }));
}
```

### Large Dataset Export

```typescript
import { ResultFormatter } from './src/cli/formatters';
import { createReadStream, createWriteStream } from 'fs';

async function exportLargeDataset(
  inputFile: string,
  outputFile: string,
  format: 'json' | 'csv' | 'xml'
) {
  const inputStream = createReadStream(inputFile);
  const outputStream = createWriteStream(outputFile);

  // Parse input as JSON lines
  const dataStream = inputStream
    .pipe(new Transform({
      objectMode: true,
      transform(chunk, encoding, callback) {
        try {
          const data = JSON.parse(chunk.toString());
          callback(null, data);
        } catch (error) {
          callback(error);
        }
      }
    }));

  await ResultFormatter.formatStreaming(
    dataStream,
    format,
    outputStream
  );
}
```

### Performance Comparison

```typescript
import { ResultFormatter } from './src/cli/formatters';

function benchmarkFormatters(data: any[]) {
  const formats = ['json', 'csv', 'table', 'xml'] as const;

  for (const format of formats) {
    const start = Date.now();
    ResultFormatter.format(data, { format, colors: false });
    const duration = Date.now() - start;

    console.log(`${format}: ${duration}ms`);
  }
}

// Test with 10,000 rows
const largeDataset = Array.from({ length: 10000 }, (_, i) => ({
  id: i,
  name: `User ${i}`,
  email: `user${i}@example.com`,
  score: Math.random() * 100
}));

benchmarkFormatters(largeDataset);
```

## Performance Tips

1. **Use streaming for large datasets** (>10,000 rows)
2. **Disable colors** when piping to files
3. **Set maxRows** to limit output size
4. **Use compact JSON** when file size matters
5. **Disable headers** for appending CSV data

## Error Handling

All formatters include robust error handling:

```typescript
try {
  const result = ResultFormatter.format(data, { format: 'json' });
  console.log(result);
} catch (error) {
  console.error('Formatting error:', error.message);
}
```

## Type Safety

Full TypeScript support with comprehensive type definitions:

```typescript
import type {
  FormatterOptions,
  TableOptions,
  CSVOptions,
  XMLOptions
} from './src/cli/formatters';

const options: FormatterOptions = {
  format: 'json',
  pretty: true,
  headers: true,
  colors: false,
  maxRows: 1000
};
```

## License

MIT
