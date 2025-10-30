# N+1 Query Detection

Automated detection of N+1 query patterns that cause severe performance degradation in database applications.

## Overview

The N+1 query problem occurs when:
1. An initial query loads records (1 query)
2. For each record, another query loads related data (N queries)
3. Total: N+1 queries when only 1-2 queries should be needed

**Example Problem:**
```python
# BAD: N+1 queries
users = db.query("SELECT * FROM users")          # 1 query
for user in users:
    orders = db.query("SELECT * FROM orders WHERE user_id = ?", user.id)  # N queries!
    print(f"{user.name} has {len(orders)} orders")

# Result: 1 + 20 = 21 queries for 20 users!
```

**Solution:**
```python
# GOOD: Single JOIN query
results = db.query("""
    SELECT users.*, orders.*
    FROM users
    LEFT JOIN orders ON orders.user_id = users.id
""")

# Result: 1 query total!
```

## Features

- **Automatic Detection**: Analyzes query logs to identify N+1 patterns
- **Pattern Matching**: Normalizes queries to detect similar patterns
- **Sequential ID Detection**: Identifies loop-based query execution
- **Batch Suggestions**: Recommends IN clause or JOIN optimizations
- **Configurable Thresholds**: Customize sensitivity for detection
- **Performance Metrics**: Estimates potential speed improvements

## Quick Start

### Basic Usage

```python
from src.database.query_optimizer import QueryOptimizer

# Create optimizer
optimizer = QueryOptimizer(database_type='postgresql')

# Analyze query log
query_log = [
    {'query': 'SELECT * FROM users', 'timestamp': 0.0, 'params': []},
    {'query': 'SELECT * FROM orders WHERE user_id = 1', 'timestamp': 10.0, 'params': [1]},
    {'query': 'SELECT * FROM orders WHERE user_id = 2', 'timestamp': 20.0, 'params': [2]},
    # ... 18 more similar queries
]

suggestions = optimizer.analyze_query_log(query_log)

for suggestion in suggestions:
    print(f"Found N+1 pattern: {suggestion.message}")
    print(f"Fix: {suggestion.suggested_query}")
    print(f"Improvement: {suggestion.estimated_improvement}")
```

### Analyze from File

```python
import json

# Save query log to file
with open('query_log.json', 'w') as f:
    json.dump(query_log, f)

# Analyze from file
suggestions = optimizer.analyze_query_log_file('query_log.json')
```

### Custom Detection Parameters

```python
# Detect smaller patterns (5+ queries)
suggestions = optimizer.detect_n_plus_one(
    query_log,
    threshold=5,          # Minimum queries to flag
    time_window_ms=2000   # Time window to consider
)
```

## Detection Algorithm

### 1. Query Normalization

Queries are normalized to templates by replacing parameters:

```python
# Original queries:
"SELECT * FROM orders WHERE user_id = 1"
"SELECT * FROM orders WHERE user_id = 2"
"SELECT * FROM orders WHERE user_id = 3"

# Normalized template:
"SELECT * FROM ORDERS WHERE USER_ID = ?"
```

### 2. Pattern Analysis

Patterns are identified by:
- **Query Count**: Must exceed threshold (default: 10)
- **Time Window**: Must occur within time window (default: 1000ms)
- **Parameter Pattern**: Parameters suggest loop iteration

### 3. Parameter Analysis

Loop detection checks for:
- Sequential numeric IDs (1, 2, 3, 4, ...)
- Distinct values (different ID each time)
- Consistent patterns

### 4. Suggestion Generation

Generates optimized queries using:
- **IN Clause**: `WHERE id IN (1, 2, 3, ...)`
- **JOIN**: `JOIN table ON condition`
- **Batch Loading**: Fetch all at once

## Configuration Options

### NPlusOneDetector Parameters

```python
from src.database.n_plus_one_detector import NPlusOneDetector

detector = NPlusOneDetector(
    time_window_ms=1000,  # Time window in milliseconds
    threshold=10          # Minimum queries to flag as N+1
)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `time_window_ms` | 1000 | Time window to consider queries related (ms) |
| `threshold` | 10 | Minimum number of similar queries to flag |

### Recommended Settings

**Production Monitoring:**
```python
detector = NPlusOneDetector(
    time_window_ms=1000,  # 1 second
    threshold=10          # Flag patterns with 10+ queries
)
```

**Development/Testing:**
```python
detector = NPlusOneDetector(
    time_window_ms=500,   # 500ms (stricter)
    threshold=5           # Flag patterns with 5+ queries
)
```

**Performance Profiling:**
```python
detector = NPlusOneDetector(
    time_window_ms=2000,  # 2 seconds (more lenient)
    threshold=20          # Only flag severe patterns
)
```

## Query Log Format

### Required Format

```python
query_log = [
    {
        'query': str,        # SQL query string
        'timestamp': float,  # Timestamp in milliseconds
        'params': list      # Query parameters (optional)
    },
    # ...
]
```

### Example

```python
query_log = [
    {
        'query': 'SELECT * FROM orders WHERE user_id = ?',
        'timestamp': 1234567890.123,
        'params': [1]
    },
    {
        'query': 'SELECT * FROM orders WHERE user_id = ?',
        'timestamp': 1234567890.133,
        'params': [2]
    },
    # ...
]
```

## Suggestion Output

### OptimizationSuggestion Fields

```python
@dataclass
class OptimizationSuggestion:
    type: OptimizationType          # N_PLUS_ONE
    level: OptimizationLevel        # CRITICAL
    message: str                    # Description
    original_query: str             # Example from pattern
    suggested_query: str            # Optimized version
    estimated_improvement: str      # Performance gain
    explanation: str                # Detailed explanation
    details: Dict[str, Any]         # Additional info
```

### Example Output

```python
suggestion = OptimizationSuggestion(
    type=OptimizationType.N_PLUS_ONE,
    level=OptimizationLevel.CRITICAL,
    message="N+1 query detected: 20 similar queries in 190ms",
    original_query="SELECT * FROM orders WHERE user_id = 1",
    suggested_query="SELECT * FROM orders WHERE user_id IN (?)",
    estimated_improvement="20x faster with batch loading or JOIN",
    explanation="Detected 20 similar queries...",
    details={
        'pattern_count': 20,
        'time_window_ms': 190.0,
        'table': 'orders',
        'sample_params': [[1], [2], [3], ...]
    }
)
```

## Integration Examples

### Django ORM

```python
# Enable query logging
import logging
logging.basicConfig()
logging.getLogger('django.db.backends').setLevel(logging.DEBUG)

# Collect queries
from django.db import connection

# Your code that triggers N+1
users = User.objects.all()
for user in users:
    orders = user.orders.all()  # N+1!

# Analyze queries
query_log = [
    {
        'query': q['sql'],
        'timestamp': q['time'] * 1000,
        'params': []
    }
    for q in connection.queries
]

suggestions = optimizer.analyze_query_log(query_log)
```

### SQLAlchemy

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

# Track queries
queries = []

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    queries.append({
        'query': statement,
        'timestamp': time.time() * 1000,
        'params': parameters
    })

# Your code
session.query(User).all()
for user in users:
    session.query(Order).filter_by(user_id=user.id).all()  # N+1!

# Analyze
suggestions = optimizer.analyze_query_log(queries)
```

### Raw SQL

```python
import time

class QueryLogger:
    def __init__(self):
        self.queries = []

    def log_query(self, query, params=None):
        self.queries.append({
            'query': query,
            'timestamp': time.time() * 1000,
            'params': params or []
        })
        # Execute query...
        return db.execute(query, params)

logger = QueryLogger()

# Your code
users = logger.log_query("SELECT * FROM users")
for user in users:
    orders = logger.log_query(
        "SELECT * FROM orders WHERE user_id = ?",
        [user['id']]
    )

# Analyze
suggestions = optimizer.analyze_query_log(logger.queries)
```

## CLI Usage

### Analyze Query Log File

```bash
# Create analysis script
cat > analyze_queries.py << 'EOF'
from src.database.query_optimizer import QueryOptimizer
import sys

optimizer = QueryOptimizer()
suggestions = optimizer.analyze_query_log_file(sys.argv[1])

for suggestion in suggestions:
    print(f"\n{'='*60}")
    print(f"N+1 Pattern Detected!")
    print(f"{'='*60}")
    print(f"Count: {suggestion.details['pattern_count']} queries")
    print(f"Table: {suggestion.details['table']}")
    print(f"Time: {suggestion.details['time_window_ms']:.1f}ms")
    print(f"\nOriginal:")
    print(f"  {suggestion.original_query}")
    print(f"\nSuggested Fix:")
    print(f"  {suggestion.suggested_query}")
    print(f"\nImprovement: {suggestion.estimated_improvement}")
EOF

# Run analysis
python analyze_queries.py query_log.json
```

## Real-World Examples

### Example 1: User Orders

**Problem:**
```python
# Load users and their orders
users = db.query("SELECT * FROM users LIMIT 50")
for user in users:
    orders = db.query("SELECT * FROM orders WHERE user_id = ?", user.id)
    print(f"{user.name}: {len(orders)} orders")

# Result: 51 queries!
```

**Detection:**
```python
suggestions = optimizer.analyze_query_log(query_log)
# Detected: 50 similar queries in 245ms
```

**Solution:**
```sql
-- Single query with JOIN
SELECT
    users.id,
    users.name,
    COUNT(orders.id) as order_count
FROM users
LEFT JOIN orders ON orders.user_id = users.id
GROUP BY users.id, users.name
LIMIT 50;

-- Result: 1 query total!
```

### Example 2: Nested N+1

**Problem:**
```python
# Triple N+1 pattern!
users = db.query("SELECT * FROM users LIMIT 10")
for user in users:
    orders = db.query("SELECT * FROM orders WHERE user_id = ?", user.id)
    for order in orders:
        items = db.query("SELECT * FROM order_items WHERE order_id = ?", order.id)

# Result: 1 + 10 + (10 * avg_orders) queries!
```

**Detection:**
```python
suggestions = optimizer.analyze_query_log(query_log)
# Detected: Multiple N+1 patterns
# - 10 queries for orders
# - 50+ queries for order_items
```

**Solution:**
```sql
-- Single query with multiple JOINs
SELECT
    users.*,
    orders.*,
    order_items.*
FROM users
LEFT JOIN orders ON orders.user_id = users.id
LEFT JOIN order_items ON order_items.order_id = orders.id
WHERE users.id IN (1, 2, 3, ..., 10);
```

## Performance Impact

### Before Optimization (N+1)

```
Queries: 101 (1 + 100)
Time: 1,050ms
Network: 101 round trips
CPU: High
```

### After Optimization (JOIN)

```
Queries: 1
Time: 15ms
Network: 1 round trip
CPU: Low

Improvement: 70x faster! 🚀
```

## Best Practices

### 1. Enable Query Logging in Development

```python
# Always log queries in development
if settings.DEBUG:
    enable_query_logging()
```

### 2. Regular Analysis

```python
# Analyze logs periodically
def analyze_recent_queries():
    """Analyze last hour of queries"""
    query_log = load_queries_from_last_hour()
    suggestions = optimizer.analyze_query_log(query_log)

    if suggestions:
        alert_developers(suggestions)
```

### 3. CI/CD Integration

```bash
# Add to CI pipeline
python -m pytest tests/ --n-plus-one-check
```

### 4. ORM Awareness

```python
# Use select_related (Django) or joinedload (SQLAlchemy)

# Django
users = User.objects.select_related('profile').all()

# SQLAlchemy
users = session.query(User).options(joinedload(User.orders)).all()
```

### 5. Monitoring in Production

```python
# Log slow query patterns
if detected_n_plus_one:
    logger.warning(
        f"N+1 detected: {pattern_count} queries",
        extra={'endpoint': request.path}
    )
```

## Troubleshooting

### False Positives

**Issue:** Legitimate repeated queries flagged as N+1

**Solution:** Increase threshold
```python
detector = NPlusOneDetector(threshold=20)  # Higher threshold
```

### False Negatives

**Issue:** N+1 patterns not detected

**Solutions:**
1. Lower threshold: `threshold=5`
2. Increase time window: `time_window_ms=2000`
3. Check query log format
4. Verify timestamps are in milliseconds

### Performance Issues

**Issue:** Analysis takes too long

**Solutions:**
1. Limit query log size
2. Sample queries for analysis
3. Run analysis asynchronously

```python
# Analyze sample
sample_size = 1000
sample_log = random.sample(query_log, min(sample_size, len(query_log)))
suggestions = optimizer.analyze_query_log(sample_log)
```

## API Reference

### QueryOptimizer

```python
class QueryOptimizer:
    def analyze_query_log(self, query_log: List[Dict]) -> List[OptimizationSuggestion]
    def analyze_query_log_file(self, log_file_path: str) -> List[OptimizationSuggestion]
    def detect_n_plus_one(
        self,
        query_log: List[Dict],
        time_window_ms: Optional[int] = None,
        threshold: Optional[int] = None
    ) -> List[OptimizationSuggestion]
```

### NPlusOneDetector

```python
class NPlusOneDetector:
    def __init__(self, time_window_ms: int = 1000, threshold: int = 10)
    def detect_n_plus_one(self, query_log: List[Dict]) -> List[OptimizationSuggestion]
```

## Testing

Run the test suite:

```bash
# All N+1 detector tests
python -m pytest tests/database/test_n_plus_one_detector.py -v

# Specific test categories
python -m pytest tests/database/test_n_plus_one_detector.py::TestBasicN1Detection -v
python -m pytest tests/database/test_n_plus_one_detector.py::TestRealWorldScenarios -v

# With coverage
python -m pytest tests/database/test_n_plus_one_detector.py --cov=src.database.n_plus_one_detector
```

## Demo

Run the interactive demo:

```bash
python docs/examples/n_plus_one_detection_demo.py
```

## Additional Resources

- [Query Optimization Guide](query-optimization.md)
- [Database Performance Best Practices](performance-best-practices.md)
- [ORM N+1 Prevention](orm-n-plus-one-prevention.md)

## Support

For issues or questions:
- File an issue on GitHub
- Check existing documentation
- Review test cases for examples
