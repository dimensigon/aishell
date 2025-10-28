/**
 * Formatters Demo
 * Demonstrates the usage of all output formatters
 */

import {
  ResultFormatter,
  JSONFormatter,
  CSVFormatter,
  TableFormatter,
  XMLFormatter,
  ValueSerializer,
  TypeGuards
} from '../src/cli/formatters';

// Sample data
const users = [
  {
    id: 1,
    name: 'Alice Johnson',
    email: 'alice@example.com',
    balance: 1234.56,
    active: true,
    joinedAt: new Date('2024-01-15')
  },
  {
    id: 2,
    name: 'Bob Smith',
    email: 'bob@example.com',
    balance: 789.01,
    active: false,
    joinedAt: new Date('2024-02-20')
  },
  {
    id: 3,
    name: 'Charlie Brown',
    email: 'charlie@example.com',
    balance: 0,
    active: true,
    joinedAt: new Date('2024-03-10')
  }
];

console.log('='.repeat(80));
console.log('FORMATTERS DEMONSTRATION');
console.log('='.repeat(80));

// JSON Formatter
console.log('\n1. JSON FORMAT (Pretty)');
console.log('-'.repeat(80));
const jsonPretty = ResultFormatter.format(users, { format: 'json', pretty: true });
console.log(jsonPretty);

console.log('\n2. JSON FORMAT (Compact)');
console.log('-'.repeat(80));
const jsonCompact = ResultFormatter.format(users, { format: 'json', pretty: false });
console.log(jsonCompact);

// CSV Formatter
console.log('\n3. CSV FORMAT (With Headers)');
console.log('-'.repeat(80));
const csvWithHeaders = ResultFormatter.format(users, { format: 'csv', headers: true });
console.log(csvWithHeaders);

console.log('\n4. CSV FORMAT (No Headers)');
console.log('-'.repeat(80));
const csvNoHeaders = ResultFormatter.format(users, { format: 'csv', headers: false });
console.log(csvNoHeaders);

// Table Formatter
console.log('\n5. TABLE FORMAT (With Colors)');
console.log('-'.repeat(80));
const tableWithColors = ResultFormatter.format(users, { format: 'table', colors: true });
console.log(tableWithColors);

console.log('\n6. TABLE FORMAT (No Colors)');
console.log('-'.repeat(80));
const tableNoColors = ResultFormatter.format(users, { format: 'table', colors: false });
console.log(tableNoColors);

// XML Formatter
console.log('\n7. XML FORMAT');
console.log('-'.repeat(80));
const xml = ResultFormatter.format(users, { format: 'xml' });
console.log(xml);

// Custom Table Options
console.log('\n8. CUSTOM TABLE (Max Cell Width)');
console.log('-'.repeat(80));
const customTable = new TableFormatter({ maxCellWidth: 15, colors: false });
console.log(customTable.format(users));

// Custom CSV Options
console.log('\n9. CUSTOM CSV (TSV - Tab Separated)');
console.log('-'.repeat(80));
const tsvFormatter = new CSVFormatter({ delimiter: '\t' });
console.log(tsvFormatter.format(users));

// Special Data Types
console.log('\n10. SPECIAL DATA TYPES');
console.log('-'.repeat(80));
const specialData = [
  {
    id: 1,
    name: 'Test',
    date: new Date('2024-01-01T12:00:00Z'),
    bigInt: BigInt('9007199254740991'),
    buffer: Buffer.from('Hello, World!'),
    nested: { foo: 'bar', baz: 123 },
    nullValue: null,
    undefinedValue: undefined
  }
];

console.log('JSON:');
console.log(JSONFormatter.format(specialData, true));

console.log('\nTable:');
console.log(new TableFormatter({ colors: false }).format(specialData));

console.log('\nXML:');
console.log(new XMLFormatter().format(specialData));

// Type Guards Demo
console.log('\n11. TYPE GUARDS DEMO');
console.log('-'.repeat(80));
const testValues = [
  { value: new Date(), type: 'Date' },
  { value: Buffer.from('test'), type: 'Buffer' },
  { value: BigInt(123), type: 'BigInt' },
  { value: null, type: 'null' },
  { value: undefined, type: 'undefined' },
  { value: { foo: 'bar' }, type: 'Object' }
];

for (const { value, type } of testValues) {
  const isDate = TypeGuards.isDate(value);
  const isBuffer = TypeGuards.isBuffer(value);
  const isBigInt = TypeGuards.isBigInt(value);
  const isNull = TypeGuards.isNull(value);
  const isUndefined = TypeGuards.isUndefined(value);
  const isObject = TypeGuards.isObject(value);

  console.log(`${type}:`, {
    isDate,
    isBuffer,
    isBigInt,
    isNull,
    isUndefined,
    isObject
  });
}

// Value Serializer Demo
console.log('\n12. VALUE SERIALIZER DEMO');
console.log('-'.repeat(80));
for (const { value, type } of testValues) {
  console.log(`${type} -> JSON:`, ValueSerializer.serialize(value, 'json'));
  console.log(`${type} -> CSV:`, ValueSerializer.serialize(value, 'csv'));
  console.log(`${type} -> Table:`, ValueSerializer.serialize(value, 'table'));
  console.log(`${type} -> XML:`, ValueSerializer.serialize(value, 'xml'));
  console.log('---');
}

// Max Rows Demo
console.log('\n13. MAX ROWS LIMIT');
console.log('-'.repeat(80));
const largeDataset = Array.from({ length: 100 }, (_, i) => ({
  id: i + 1,
  name: `User ${i + 1}`,
  score: Math.round(Math.random() * 100)
}));

console.log('Limited to 5 rows:');
const limited = ResultFormatter.format(largeDataset, {
  format: 'table',
  colors: false,
  maxRows: 5
});
console.log(limited);

// Nested Objects Demo
console.log('\n14. NESTED OBJECTS IN XML');
console.log('-'.repeat(80));
const nestedData = [
  {
    user: {
      id: 1,
      name: 'Alice',
      address: {
        street: '123 Main St',
        city: 'Springfield',
        zip: '12345'
      }
    },
    orders: [
      { id: 101, total: 99.99 },
      { id: 102, total: 149.99 }
    ]
  }
];

const xmlFormatter = new XMLFormatter({
  rootElement: 'data',
  rowElement: 'record',
  indent: 4
});
console.log(xmlFormatter.format(nestedData));

// CSV with Special Characters
console.log('\n15. CSV WITH SPECIAL CHARACTERS');
console.log('-'.repeat(80));
const specialCharsData = [
  { name: 'Smith, John', note: 'He said "Hello"' },
  { name: 'Doe, Jane', note: 'Line 1\nLine 2' }
];
const csvFormatter = new CSVFormatter();
console.log(csvFormatter.format(specialCharsData));

console.log('\n' + '='.repeat(80));
console.log('DEMO COMPLETE');
console.log('='.repeat(80));
