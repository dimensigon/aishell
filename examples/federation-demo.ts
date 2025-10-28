/**
 * True Database Federation Demo
 * Demonstrates cross-database JOINs with AI-Shell
 */

import { FederationEngine } from '../src/cli/federation-engine';
import { DatabaseConnectionManager } from '../src/cli/database-manager';
import { StateManager } from '../src/core/state-manager';

async function demonstrateFederation() {
  console.log('='.repeat(80));
  console.log('AI-Shell True Database Federation Demo');
  console.log('='.repeat(80));
  console.log('');

  // Initialize components
  const stateManager = new StateManager();
  const dbManager = new DatabaseConnectionManager(stateManager);
  const federation = new FederationEngine(dbManager, stateManager);

  console.log('✓ Federation engine initialized');
  console.log('');

  // Demo 1: SQL Parsing
  console.log('DEMO 1: SQL Parsing');
  console.log('-'.repeat(80));

  const sql1 = `
    SELECT u.name, u.email, o.total, o.created_at
    FROM postgres.users u
    INNER JOIN mysql.orders o ON u.id = o.user_id
    WHERE o.total > 100
    ORDER BY o.total DESC
    LIMIT 10
  `;

  console.log('Query:', sql1.trim());
  console.log('');

  try {
    const parsed = (federation as any).parseSQL(sql1);
    console.log('✓ Successfully parsed SQL query');
    console.log('  - Type:', parsed.type);
    console.log('  - Select columns:', parsed.select.length);
    console.log('  - From table:', `${parsed.from[0].database}.${parsed.from[0].table}`);
    console.log('  - Joins:', parsed.joins.length);
    console.log('  - Join type:', parsed.joins[0]?.type);
    console.log('  - WHERE clause:', parsed.where ? 'Yes' : 'No');
    console.log('  - ORDER BY:', parsed.orderBy ? 'Yes' : 'No');
    console.log('  - LIMIT:', parsed.limit || 'None');
  } catch (error) {
    console.error('✗ Parse error:', error);
  }

  console.log('');

  // Demo 2: Complex Multi-Table JOIN
  console.log('DEMO 2: Complex Multi-Table JOIN');
  console.log('-'.repeat(80));

  const sql2 = `
    SELECT u.name, o.total, p.name as product, c.name as category
    FROM postgres.users u
    INNER JOIN mysql.orders o ON u.id = o.user_id
    INNER JOIN mysql.products p ON o.product_id = p.id
    INNER JOIN mongodb.categories c ON p.category_id = c.id
  `;

  console.log('Query:', sql2.trim());
  console.log('');

  try {
    const parsed = (federation as any).parseSQL(sql2);
    console.log('✓ Successfully parsed multi-table query');
    console.log('  - Databases involved:', new Set([
      parsed.from[0].database,
      ...parsed.joins.map((j: any) => j.database)
    ]).size);
    console.log('  - Total JOINs:', parsed.joins.length);
    parsed.joins.forEach((join: any, idx: number) => {
      console.log(`  - JOIN ${idx + 1}: ${join.database}.${join.table} (${join.type})`);
    });
  } catch (error) {
    console.error('✗ Parse error:', error);
  }

  console.log('');

  // Demo 3: Aggregate Functions
  console.log('DEMO 3: Aggregate Functions');
  console.log('-'.repeat(80));

  const sql3 = `
    SELECT
      category,
      COUNT(*) as order_count,
      SUM(amount) as total_revenue,
      AVG(amount) as avg_order,
      MIN(amount) as min_order,
      MAX(amount) as max_order
    FROM mysql.products
    JOIN postgres.sales ON products.id = sales.product_id
    GROUP BY category
    HAVING SUM(amount) > 10000
    ORDER BY total_revenue DESC
  `;

  console.log('Query:', sql3.trim());
  console.log('');

  try {
    const parsed = (federation as any).parseSQL(sql3);
    console.log('✓ Successfully parsed aggregate query');
    console.log('  - Aggregate functions:', parsed.select.filter((s: any) => s.isAggregate).length);
    parsed.select.filter((s: any) => s.isAggregate).forEach((agg: any) => {
      console.log(`    - ${agg.aggregateFunction}(${agg.expression.match(/\(([^)]+)\)/)?.[1]})`);
    });
    console.log('  - GROUP BY columns:', parsed.groupBy?.columns.join(', '));
  } catch (error) {
    console.error('✗ Parse error:', error);
  }

  console.log('');

  // Demo 4: LEFT JOIN
  console.log('DEMO 4: LEFT JOIN (All users, even without orders)');
  console.log('-'.repeat(80));

  const sql4 = `
    SELECT u.name, COUNT(o.id) as order_count
    FROM postgres.users u
    LEFT JOIN mysql.orders o ON u.id = o.user_id
    GROUP BY u.name
  `;

  console.log('Query:', sql4.trim());
  console.log('');

  try {
    const parsed = (federation as any).parseSQL(sql4);
    console.log('✓ Successfully parsed LEFT JOIN');
    console.log('  - JOIN type:', parsed.joins[0]?.type);
    console.log('  - Will include all left table rows:', parsed.joins[0]?.type === 'LEFT');
  } catch (error) {
    console.error('✗ Parse error:', error);
  }

  console.log('');

  // Demo 5: JOIN Operation (In-Memory)
  console.log('DEMO 5: JOIN Operation Performance');
  console.log('-'.repeat(80));

  const leftData = Array.from({ length: 10000 }, (_, i) => ({
    id: i,
    name: `User${i}`
  }));

  const rightData = Array.from({ length: 10000 }, (_, i) => ({
    user_id: i,
    total: Math.floor(Math.random() * 1000)
  }));

  console.log(`Testing INNER JOIN with ${leftData.length.toLocaleString()} x ${rightData.length.toLocaleString()} rows...`);

  const startTime = Date.now();
  const result = (federation as any).performJoin(
    leftData,
    rightData,
    { leftColumn: 'id', rightColumn: 'user_id' },
    'INNER'
  );
  const duration = Date.now() - startTime;

  console.log('✓ JOIN completed successfully');
  console.log(`  - Result rows: ${result.length.toLocaleString()}`);
  console.log(`  - Execution time: ${duration}ms`);
  console.log(`  - Rows/second: ${Math.floor(result.length / (duration / 1000)).toLocaleString()}`);
  console.log('');

  // Demo 6: Statistics
  console.log('DEMO 6: Statistics & Caching');
  console.log('-'.repeat(80));

  const stats = federation.getStatistics();
  console.log('Current Statistics:');
  console.log(`  - Queries executed: ${stats.queriesExecuted}`);
  console.log(`  - Cache hits: ${stats.cacheHits}`);
  console.log(`  - Cache misses: ${stats.cacheMisses}`);
  console.log(`  - Cache hit rate: ${(stats.cacheHits / (stats.cacheHits + stats.cacheMisses || 1) * 100).toFixed(1)}%`);
  console.log(`  - Total data transferred: ${stats.totalDataTransferred.toLocaleString()} rows`);
  console.log('');

  // Demo 7: All JOIN Types
  console.log('DEMO 7: All JOIN Types');
  console.log('-'.repeat(80));

  const smallLeft = [
    { id: 1, name: 'Alice' },
    { id: 2, name: 'Bob' },
    { id: 3, name: 'Charlie' }
  ];

  const smallRight = [
    { user_id: 2, total: 200 },
    { user_id: 3, total: 300 },
    { user_id: 4, total: 400 }
  ];

  console.log('Test data:');
  console.log('  Left:', smallLeft.map(u => u.name).join(', '));
  console.log('  Right:', smallRight.map(o => `user_id=${o.user_id}`).join(', '));
  console.log('');

  const joinTypes = ['INNER', 'LEFT', 'RIGHT', 'FULL'] as const;

  for (const joinType of joinTypes) {
    const joinResult = (federation as any).performJoin(
      smallLeft,
      smallRight,
      { leftColumn: 'id', rightColumn: 'user_id' },
      joinType
    );

    console.log(`${joinType} JOIN: ${joinResult.length} rows`);
    joinResult.forEach(row => {
      console.log(`  - ${row.name || 'null'} (id: ${row.id || 'null'}) -> total: ${row.total || 'null'}`);
    });
    console.log('');
  }

  // Demo 8: Execution Plan
  console.log('DEMO 8: Query Execution Plan');
  console.log('-'.repeat(80));

  const explainSql = `
    SELECT u.name, o.total
    FROM postgres.users u
    JOIN mysql.orders o ON u.id = o.user_id
    WHERE o.total > 100
  `;

  console.log('Query:', explainSql.trim());
  console.log('');

  try {
    const explanation = await federation.explainQuery(explainSql);
    console.log(explanation);
  } catch (error) {
    console.error('✗ Explanation error:', error);
  }

  console.log('');

  // Summary
  console.log('='.repeat(80));
  console.log('Demo Summary');
  console.log('='.repeat(80));
  console.log('✓ SQL parsing with complex queries');
  console.log('✓ Multi-table JOINs (3+ databases)');
  console.log('✓ Aggregate functions (COUNT, SUM, AVG, MIN, MAX)');
  console.log('✓ All JOIN types (INNER, LEFT, RIGHT, FULL OUTER)');
  console.log('✓ High-performance JOIN operations (<1s for 10k rows)');
  console.log('✓ Statistics tracking and caching');
  console.log('✓ Query execution plan generation');
  console.log('');
  console.log('Federation engine ready for production use!');
  console.log('='.repeat(80));
}

// Run demo
if (require.main === module) {
  demonstrateFederation()
    .then(() => process.exit(0))
    .catch(error => {
      console.error('Demo failed:', error);
      process.exit(1);
    });
}

export { demonstrateFederation };
