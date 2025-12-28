# E-Commerce Platform - AI-Shell Example

## Scenario: Complete E-Commerce Database Management

This example demonstrates managing a production-scale e-commerce platform with multiple databases, handling millions of products, orders, and customer data. Perfect for Black Friday traffic and real-time inventory management.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI-Shell Management Layer                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │   MongoDB    │  │    Redis     │      │
│  │              │  │              │  │              │      │
│  │  - Products  │  │  - Reviews   │  │  - Sessions  │      │
│  │  - Orders    │  │  - Logs      │  │  - Cart      │      │
│  │  - Customers │  │  - Analytics │  │  - Cache     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

- **Multi-Database Management**: Postgres for transactions, MongoDB for reviews/logs, Redis for caching
- **Federation Queries**: Cross-database queries combining product, review, and inventory data
- **Performance Optimization**: Automated indexing, query analysis, and cache warming
- **Black Friday Ready**: Load testing, connection pooling, read replicas
- **Automated Operations**: Backup scheduling, health monitoring, alerting
- **Cost Tracking**: Database usage monitoring and optimization recommendations

## Prerequisites

- Docker & Docker Compose
- AI-Shell installed (`npm install -g aishell`)
- 4GB RAM minimum
- 10GB disk space

## Quick Start

### 1. Setup Environment

```bash
cd examples/ecommerce
./scripts/setup.sh
```

This will:
- Start PostgreSQL, MongoDB, and Redis containers
- Load 10,000 products, 50,000 orders, and 100,000 reviews
- Create indexes and optimize schemas
- Configure AI-Shell connections

### 2. Run the Demo

```bash
./scripts/demo.sh
```

This demonstrates:
- Natural language queries across databases
- Performance monitoring and optimization
- Black Friday traffic simulation
- Automated backup and recovery
- Cost analysis and recommendations

### 3. Interactive Usage

```bash
# Start AI-Shell
ai-shell

# Try these natural language queries:
"Show me top 10 products by revenue with their average ratings"
"Which customers have abandoned carts worth more than $500?"
"Find slow queries in the last hour and suggest optimizations"
"What's the current cache hit rate and should we scale Redis?"
"Schedule daily backups at 2 AM and keep 7 days of history"
```

## Example Queries

### 1. Product Performance Analysis
```
"Show products with high sales but low ratings - might have quality issues"
```

Expected: Federated query joining PostgreSQL orders with MongoDB reviews

### 2. Inventory Optimization
```
"Find products with stock below reorder point and check if they're trending"
```

Expected: Real-time inventory check with sales trend analysis

### 3. Customer Insights
```
"List VIP customers (>$10k lifetime value) with recent cart abandonment"
```

Expected: Customer segmentation with behavioral analysis

### 4. Performance Tuning
```
"Analyze query performance and suggest indexes for slow queries"
```

Expected: Automatic index recommendations with impact estimation

### 5. Black Friday Preparation
```
"Simulate 10x traffic load and identify bottlenecks"
```

Expected: Load testing with scaling recommendations

## Sample Data

### Products (PostgreSQL)
- 10,000 products across 50 categories
- SKU, name, price, stock, cost, images
- Realistic price ranges ($1 - $5000)
- Stock levels (0 - 10000 units)

### Orders (PostgreSQL)
- 50,000 orders over 12 months
- Order status: pending, processing, shipped, delivered, cancelled
- Payment methods: credit_card, paypal, crypto
- Shipping addresses and tracking

### Reviews (MongoDB)
- 100,000 product reviews
- Ratings (1-5 stars)
- Verified purchases
- Helpful votes and moderation flags
- Review text with sentiment scores

### Cache (Redis)
- Product details (TTL: 1 hour)
- Cart data (TTL: 24 hours)
- Session data (TTL: 30 days)
- Rate limiting counters

## Configuration

### Database Connections

```yaml
# config/ai-shell.config.json
{
  "connections": {
    "ecommerce_main": {
      "type": "postgres",
      "host": "localhost",
      "port": 5432,
      "database": "ecommerce",
      "schema": "public"
    },
    "ecommerce_reviews": {
      "type": "mongodb",
      "host": "localhost",
      "port": 27017,
      "database": "ecommerce"
    },
    "ecommerce_cache": {
      "type": "redis",
      "host": "localhost",
      "port": 6379,
      "database": 0
    }
  },
  "federation": {
    "enabled": true,
    "primary": "ecommerce_main"
  }
}
```

### Environment Variables

```bash
# .env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ecommerce
POSTGRES_USER=admin
POSTGRES_PASSWORD=ecommerce123

MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DB=ecommerce

REDIS_HOST=localhost
REDIS_PORT=6379

# Performance tuning
MAX_CONNECTIONS=100
POOL_SIZE=20
CACHE_TTL=3600
QUERY_TIMEOUT=30000
```

## Scripts

### setup.sh
Initializes all databases, loads sample data, creates indexes

### demo.sh
Runs interactive demonstration of all capabilities

### cleanup.sh
Stops containers and removes all data

### load-test.sh
Simulates Black Friday traffic (10,000 req/sec)

### backup.sh
Creates full backup of all databases

### restore.sh
Restores from backup

## Performance Benchmarks

### Expected Performance (on 4-core machine)

- Simple product query: < 10ms
- Complex federated query: < 100ms
- Order creation: < 50ms
- Cache hit rate: > 95%
- Concurrent users: 10,000+
- Requests/second: 5,000+

### Optimization Tips

1. **Enable connection pooling** (included)
2. **Use Redis for hot data** (product details, cart)
3. **Partition orders table** by date
4. **Read replicas** for analytics queries
5. **CDN for product images**
6. **Elasticsearch** for product search (optional)

## Monitoring

The example includes:

- Real-time performance dashboard
- Slow query log (> 1 second)
- Connection pool monitoring
- Cache hit rate tracking
- Error rate and alerting
- Backup success tracking

Access dashboards:
- Adminer (DB admin): http://localhost:8080
- Redis Commander: http://localhost:8081

## Scaling Strategies

### Horizontal Scaling
```bash
# Add read replicas
docker-compose -f docker-compose.scale.yml up -d
```

### Vertical Scaling
```bash
# Increase resources
docker-compose up -d --scale postgres=1 --scale postgres-replica=2
```

## Troubleshooting

### Slow Queries
```
"Analyze slow queries and suggest optimizations"
```

### Connection Pool Exhaustion
```
"Show current connection usage and recommend pool size"
```

### High Cache Miss Rate
```
"Analyze cache effectiveness and suggest TTL adjustments"
```

### Disk Space Issues
```
"Check database sizes and suggest cleanup strategies"
```

## Next Steps

1. **Add Elasticsearch**: Full-text product search
2. **Set up Replication**: High availability
3. **Implement Sharding**: Scale beyond single instance
4. **Add Monitoring**: Prometheus + Grafana
5. **CDN Integration**: Image and static asset delivery
6. **GraphQL API**: Modern API layer

## Learn More

- [AI-Shell Documentation](../../docs/)
- [Query Federation Guide](../../docs/FEDERATION.md)
- [Performance Tuning](../../docs/PERFORMANCE.md)
- [Backup Strategies](../../docs/BACKUP.md)

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/aishell/issues
- Documentation: ../../docs/

---

**Ready to scale your e-commerce platform? Start with `./scripts/demo.sh`**
