"""
Database Optimizer Tools

Provides tools for analyzing query performance, recommending indexes,
and optimizing database operations.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random


async def analyze_slow_queries(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze and identify slow-running queries.

    Args:
        params: Analysis parameters
            - database: str
            - threshold_ms: int (default: 1000)
            - limit: int (default: 20)
            - include_explain: bool (default: False)
        context: Execution context

    Returns:
        Dict containing:
            - slow_queries: List of slow query details
            - total_analyzed: int
            - average_duration: float
            - recommendations: List[str]
    """
    # Validate parameters
    if 'database' not in params:
        raise ValueError("Missing required parameter: database")

    database = params['database']
    threshold_ms = params.get('threshold_ms', 1000)
    limit = params.get('limit', 20)
    include_explain = params.get('include_explain', False)

    # Simulate query analysis
    await asyncio.sleep(0.3)

    # Mock slow queries
    slow_queries = [
        {
            'query_id': 'q1',
            'query': 'SELECT * FROM users WHERE email LIKE "%@example.com"',
            'duration_ms': 2340,
            'execution_count': 1523,
            'table': 'users',
            'issue': 'Full table scan due to leading wildcard',
            'suggestion': 'Add index on email or use full-text search'
        },
        {
            'query_id': 'q2',
            'query': 'SELECT o.*, c.name FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.status = "pending"',
            'duration_ms': 1820,
            'execution_count': 892,
            'table': 'orders',
            'issue': 'Missing index on status column',
            'suggestion': 'CREATE INDEX idx_orders_status ON orders(status)'
        },
        {
            'query_id': 'q3',
            'query': 'SELECT product_id, COUNT(*) FROM order_items GROUP BY product_id ORDER BY COUNT(*) DESC',
            'duration_ms': 3100,
            'execution_count': 234,
            'table': 'order_items',
            'issue': 'Large table scan with aggregation',
            'suggestion': 'Consider materialized view for product statistics'
        },
        {
            'query_id': 'q4',
            'query': 'SELECT * FROM logs WHERE created_at BETWEEN "2025-01-01" AND "2025-12-31"',
            'duration_ms': 4500,
            'execution_count': 156,
            'table': 'logs',
            'issue': 'Large date range scan',
            'suggestion': 'Partition table by date or add composite index'
        },
        {
            'query_id': 'q5',
            'query': 'UPDATE users SET last_login = NOW() WHERE id IN (SELECT user_id FROM sessions WHERE active = 1)',
            'duration_ms': 1650,
            'execution_count': 2341,
            'table': 'users',
            'issue': 'Subquery causing multiple scans',
            'suggestion': 'Rewrite using JOIN or add index on sessions.active'
        }
    ]

    # Filter by threshold and limit
    filtered_queries = [q for q in slow_queries if q['duration_ms'] >= threshold_ms]
    filtered_queries = filtered_queries[:limit]

    # Add explain plans if requested
    if include_explain:
        for query in filtered_queries:
            query['explain_plan'] = f"""
Seq Scan on {query['table']}  (cost=0.00..1234.56 rows=10000 width=128)
  Filter: (condition)
  Rows Removed by Filter: 95000
""".strip()

    # Calculate statistics
    total_analyzed = len(slow_queries)
    average_duration = sum(q['duration_ms'] for q in slow_queries) / len(slow_queries) if slow_queries else 0

    # Generate recommendations
    recommendations = [
        f"Found {len(filtered_queries)} queries exceeding {threshold_ms}ms threshold",
        "Prioritize optimizing queries with high execution counts",
        "Consider adding indexes on frequently filtered columns",
        "Review queries with full table scans",
        "Monitor query performance after optimization"
    ]

    return {
        'slow_queries': filtered_queries,
        'total_analyzed': total_analyzed,
        'average_duration': average_duration,
        'threshold_ms': threshold_ms,
        'recommendations': recommendations,
        'database': database,
        'analysis_timestamp': datetime.now().isoformat()
    }


async def recommend_indexes(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recommend indexes based on query patterns and table statistics.

    Args:
        params: Recommendation parameters
            - database: str
            - queries: List[str] (optional, for query-based analysis)
            - min_impact_score: float (default: 0.5, range 0-1)
        context: Execution context

    Returns:
        Dict containing:
            - recommendations: List of index recommendations
            - total_potential_impact: float
            - estimated_storage: str
    """
    # Validate parameters
    if 'database' not in params:
        raise ValueError("Missing required parameter: database")

    database = params['database']
    queries = params.get('queries', [])
    min_impact_score = params.get('min_impact_score', 0.5)

    # Simulate index analysis
    await asyncio.sleep(0.25)

    # Mock index recommendations
    recommendations = [
        {
            'table': 'users',
            'columns': ['email'],
            'index_name': 'idx_users_email',
            'impact_score': 0.92,
            'reason': 'Frequently used in WHERE clauses and JOINs',
            'create_sql': 'CREATE INDEX idx_users_email ON users(email)',
            'estimated_size_kb': 2048,
            'selectivity': 0.98,
            'affected_queries': 45
        },
        {
            'table': 'orders',
            'columns': ['status', 'created_at'],
            'index_name': 'idx_orders_status_created',
            'impact_score': 0.87,
            'reason': 'Composite index for status filtering with date sorting',
            'create_sql': 'CREATE INDEX idx_orders_status_created ON orders(status, created_at)',
            'estimated_size_kb': 4096,
            'selectivity': 0.75,
            'affected_queries': 23
        },
        {
            'table': 'order_items',
            'columns': ['product_id'],
            'index_name': 'idx_order_items_product',
            'impact_score': 0.78,
            'reason': 'Improve JOIN performance and GROUP BY queries',
            'create_sql': 'CREATE INDEX idx_order_items_product ON order_items(product_id)',
            'estimated_size_kb': 3072,
            'selectivity': 0.65,
            'affected_queries': 18
        },
        {
            'table': 'sessions',
            'columns': ['user_id', 'active'],
            'index_name': 'idx_sessions_user_active',
            'impact_score': 0.71,
            'reason': 'Speed up active session lookups per user',
            'create_sql': 'CREATE INDEX idx_sessions_user_active ON sessions(user_id, active)',
            'estimated_size_kb': 1536,
            'selectivity': 0.82,
            'affected_queries': 31
        },
        {
            'table': 'products',
            'columns': ['category_id', 'price'],
            'index_name': 'idx_products_category_price',
            'impact_score': 0.64,
            'reason': 'Optimize category browsing with price sorting',
            'create_sql': 'CREATE INDEX idx_products_category_price ON products(category_id, price)',
            'estimated_size_kb': 2560,
            'selectivity': 0.55,
            'affected_queries': 12
        },
        {
            'table': 'logs',
            'columns': ['created_at'],
            'index_name': 'idx_logs_created',
            'impact_score': 0.58,
            'reason': 'Time-based queries and log analysis',
            'create_sql': 'CREATE INDEX idx_logs_created ON logs(created_at)',
            'estimated_size_kb': 8192,
            'selectivity': 0.45,
            'affected_queries': 8
        }
    ]

    # Filter by impact score
    filtered_recommendations = [r for r in recommendations if r['impact_score'] >= min_impact_score]

    # Calculate totals
    total_potential_impact = sum(r['impact_score'] for r in filtered_recommendations)
    total_storage_kb = sum(r['estimated_size_kb'] for r in filtered_recommendations)

    # Format storage estimate
    if total_storage_kb < 1024:
        estimated_storage = f"{total_storage_kb} KB"
    elif total_storage_kb < 1024 * 1024:
        estimated_storage = f"{total_storage_kb / 1024:.2f} MB"
    else:
        estimated_storage = f"{total_storage_kb / (1024 * 1024):.2f} GB"

    return {
        'recommendations': filtered_recommendations,
        'total_recommendations': len(filtered_recommendations),
        'total_potential_impact': round(total_potential_impact, 2),
        'estimated_storage': estimated_storage,
        'min_impact_score': min_impact_score,
        'database': database,
        'analysis_timestamp': datetime.now().isoformat()
    }


async def create_index(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a database index with performance tracking.

    Args:
        params: Index creation parameters
            - table: str
            - columns: List[str]
            - index_name: str (optional, auto-generated if not provided)
            - unique: bool (default: False)
            - concurrent: bool (default: True, for PostgreSQL)
        context: Execution context

    Returns:
        Dict containing:
            - success: bool
            - index_name: str
            - size_kb: int
            - creation_time: float (seconds)
            - sql_executed: str
    """
    # Validate parameters
    required = ['table', 'columns']
    missing = [p for p in required if p not in params]
    if missing:
        raise ValueError(f"Missing required parameters: {missing}")

    table = params['table']
    columns = params['columns']
    unique = params.get('unique', False)
    concurrent = params.get('concurrent', True)

    # Generate index name if not provided
    if 'index_name' in params:
        index_name = params['index_name']
    else:
        columns_str = '_'.join(columns)
        index_name = f"idx_{table}_{columns_str}"

    start_time = datetime.now()

    # Simulate index creation
    await asyncio.sleep(0.4)

    # Build SQL
    unique_clause = "UNIQUE" if unique else ""
    concurrent_clause = "CONCURRENTLY" if concurrent else ""
    columns_str = ", ".join(columns)

    sql_executed = f"CREATE {unique_clause} INDEX {concurrent_clause} {index_name} ON {table}({columns_str})".strip()

    creation_time = (datetime.now() - start_time).total_seconds()

    # Estimate index size based on number of columns and table name
    base_size = 1024  # KB
    column_multiplier = len(columns) * 512
    estimated_size_kb = base_size + column_multiplier

    return {
        'success': True,
        'index_name': index_name,
        'table': table,
        'columns': columns,
        'size_kb': estimated_size_kb,
        'creation_time': creation_time,
        'sql_executed': sql_executed,
        'unique': unique,
        'concurrent': concurrent,
        'created_at': datetime.now().isoformat()
    }


async def update_table_statistics(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update table statistics for query optimizer.

    Args:
        params: Statistics update parameters
            - database: str
            - tables: List[str] (optional, all tables if not specified)
            - analyze_sample_percent: int (default: 100)
        context: Execution context

    Returns:
        Dict containing:
            - tables_updated: List[str]
            - rows_analyzed: int
            - duration: float (seconds)
            - statistics: Dict (per-table stats)
    """
    # Validate parameters
    if 'database' not in params:
        raise ValueError("Missing required parameter: database")

    database = params['database']
    tables = params.get('tables', ['users', 'orders', 'products', 'order_items', 'sessions'])
    sample_percent = params.get('analyze_sample_percent', 100)

    start_time = datetime.now()

    # Simulate statistics update
    await asyncio.sleep(0.5)

    # Generate mock statistics for each table
    statistics = {}
    total_rows = 0

    for table in tables:
        rows = random.randint(1000, 100000)
        total_rows += rows

        statistics[table] = {
            'rows': rows,
            'pages': rows // 100,
            'avg_row_length': random.randint(100, 500),
            'indexes': random.randint(1, 5),
            'last_analyzed': datetime.now().isoformat(),
            'null_fraction': round(random.uniform(0.0, 0.3), 3),
            'distinct_values': random.randint(100, rows),
            'most_common_values': ['value1', 'value2', 'value3']
        }

    duration = (datetime.now() - start_time).total_seconds()

    # Determine actual rows analyzed based on sample percent
    rows_analyzed = int(total_rows * (sample_percent / 100))

    return {
        'tables_updated': tables,
        'total_tables': len(tables),
        'rows_analyzed': rows_analyzed,
        'duration': duration,
        'statistics': statistics,
        'sample_percent': sample_percent,
        'database': database,
        'updated_at': datetime.now().isoformat(),
        'recommendations': [
            'Statistics updated successfully',
            'Query planner will use new statistics for optimization',
            f'Analyzed {sample_percent}% of table data',
            'Consider running ANALYZE regularly for accurate statistics'
        ]
    }


# Tool registration metadata
OPTIMIZER_TOOLS = [
    {
        'name': 'analyze_slow_queries',
        'func': analyze_slow_queries,
        'schema': {
            'type': 'object',
            'required': ['database'],
            'properties': {
                'database': {'type': 'string'},
                'threshold_ms': {'type': 'integer', 'default': 1000},
                'limit': {'type': 'integer', 'default': 20},
                'include_explain': {'type': 'boolean', 'default': False}
            }
        }
    },
    {
        'name': 'recommend_indexes',
        'func': recommend_indexes,
        'schema': {
            'type': 'object',
            'required': ['database'],
            'properties': {
                'database': {'type': 'string'},
                'queries': {'type': 'array', 'items': {'type': 'string'}},
                'min_impact_score': {'type': 'number', 'default': 0.5, 'minimum': 0, 'maximum': 1}
            }
        }
    },
    {
        'name': 'create_index',
        'func': create_index,
        'schema': {
            'type': 'object',
            'required': ['table', 'columns'],
            'properties': {
                'table': {'type': 'string'},
                'columns': {'type': 'array', 'items': {'type': 'string'}},
                'index_name': {'type': 'string'},
                'unique': {'type': 'boolean', 'default': False},
                'concurrent': {'type': 'boolean', 'default': True}
            }
        }
    },
    {
        'name': 'update_table_statistics',
        'func': update_table_statistics,
        'schema': {
            'type': 'object',
            'required': ['database'],
            'properties': {
                'database': {'type': 'string'},
                'tables': {'type': 'array', 'items': {'type': 'string'}},
                'analyze_sample_percent': {'type': 'integer', 'default': 100, 'minimum': 1, 'maximum': 100}
            }
        }
    }
]
