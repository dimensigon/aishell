# AI-Shell Examples - Production-Ready Database Management Scenarios

This directory contains 5 complete, production-realistic examples showcasing AI-Shell's capabilities across different use cases. Each example is fully functional, well-documented, and can be set up in 5-10 minutes.

## Available Examples

### 1. E-Commerce Platform (`ecommerce/`)
**Scenario**: High-traffic e-commerce with multi-database architecture

Demonstrates:
- Multi-database management (PostgreSQL + MongoDB + Redis)
- Query federation across databases
- Black Friday traffic handling
- Performance optimization
- Automated backups and monitoring
- Inventory management
- Customer analytics

**Best For**: Learning multi-database federation, performance tuning, high-scale operations

**Setup Time**: 5 minutes | **Databases**: 3 | **Sample Data**: 160K records

[View Documentation →](./ecommerce/README.md)

---

### 2. SaaS Multi-Tenant (`saas-multitenant/`)
**Scenario**: B2B SaaS platform with complete tenant isolation

Demonstrates:
- Schema-per-tenant architecture
- Automated tenant provisioning
- Cross-tenant analytics (without breaking isolation)
- Per-tenant query optimization
- Resource usage tracking and billing
- Tenant migration and scaling
- Compliance and data isolation

**Best For**: Multi-tenancy patterns, SaaS architecture, compliance requirements

**Setup Time**: 5 minutes | **Databases**: 3 | **Tenants**: 5 sample tenants

[View Documentation →](./saas-multitenant/README.md)

---

### 3. Analytics Dashboard (`analytics-pipeline/`)
**Scenario**: Real-time analytics with multiple data sources

Demonstrates:
- Data warehouse optimization
- Query federation (SQL + NoSQL + Search)
- ETL pipeline management
- Real-time dashboards
- Scheduled data sync
- Cache warming strategies
- Performance monitoring

**Best For**: Data analytics, BI dashboards, ETL processes

**Setup Time**: 7 minutes | **Databases**: 4 | **Data Sources**: Multiple

[View Documentation →](./analytics-pipeline/README.md)

---

### 4. Microservices Data Mesh (`microservices/`)
**Scenario**: Distributed microservices with independent databases

Demonstrates:
- Service-per-database pattern
- Cross-service data queries
- Schema evolution management
- Distributed transactions
- Service mesh integration
- API gateway patterns
- Multi-cloud deployment (AWS + GCP)

**Best For**: Microservices architecture, distributed systems, polyglot persistence

**Setup Time**: 8 minutes | **Services**: 6 | **Databases**: 6

[View Documentation →](./microservices/README.md)

---

### 5. Legacy Migration (`legacy-migration/`)
**Scenario**: Migrating from Oracle to PostgreSQL

Demonstrates:
- Schema comparison and diffing
- Migration testing framework
- Data validation and integrity checks
- Query translation (Oracle SQL → PostgreSQL)
- Zero-downtime migration strategy
- Rollback procedures
- Performance benchmarking

**Best For**: Database migrations, modernization projects, risk mitigation

**Setup Time**: 10 minutes | **Databases**: 2 | **Migration Steps**: 12

[View Documentation →](./legacy-migration/README.md)

---

## Quick Start Guide

### Prerequisites

All examples require:
- **Docker & Docker Compose** - For database containers
- **Node.js 18+** - For AI-Shell
- **4GB RAM minimum** - 8GB recommended
- **10GB disk space** - For all examples

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/aishell.git
cd aishell

# 2. Install AI-Shell
npm install -g aishell

# 3. Configure API key (if using Anthropic)
export AISHELL_API_KEY="your_anthropic_key_here"

# 4. Choose an example and set it up
cd examples/ecommerce
./scripts/setup.sh

# 5. Run the demo
./scripts/demo.sh
```

### Running an Example

Each example follows the same pattern:

```bash
# Navigate to example
cd examples/{example-name}/

# Setup (first time only)
./scripts/setup.sh

# Run interactive demo
./scripts/demo.sh

# Or use AI-Shell directly
ai-shell

# Cleanup when done
./scripts/cleanup.sh
```

## Example Comparison Matrix

| Feature | E-Commerce | SaaS Multi-Tenant | Analytics | Microservices | Migration |
|---------|------------|-------------------|-----------|---------------|-----------|
| **Complexity** | Medium | High | Medium | High | High |
| **Setup Time** | 5 min | 5 min | 7 min | 8 min | 10 min |
| **Databases** | 3 | 3 | 4 | 6 | 2 |
| **Sample Data** | 160K | 50K | 1M+ | 200K | 100K |
| **Federation** | ✓ | ✓ | ✓ | ✓ | - |
| **Best For** | Multi-DB | Isolation | Analytics | Distributed | Migration |

## What Each Example Teaches

### E-Commerce Platform
- ✅ Multi-database federation (Postgres + Mongo + Redis)
- ✅ Performance optimization under load
- ✅ Caching strategies
- ✅ Inventory management
- ✅ Customer segmentation
- ✅ Automated operations

### SaaS Multi-Tenant
- ✅ Schema-per-tenant isolation
- ✅ Automated provisioning
- ✅ Cross-tenant analytics
- ✅ Resource tracking and billing
- ✅ Tenant migration
- ✅ Compliance (GDPR, SOC2)

### Analytics Dashboard
- ✅ Data warehouse design
- ✅ ETL pipelines
- ✅ Real-time queries
- ✅ Polyglot persistence
- ✅ Cache optimization
- ✅ Scheduled jobs

### Microservices Data Mesh
- ✅ Service-per-database
- ✅ Distributed queries
- ✅ Schema evolution
- ✅ Event-driven architecture
- ✅ Multi-cloud setup
- ✅ API composition

### Legacy Migration
- ✅ Schema comparison
- ✅ Migration planning
- ✅ Data validation
- ✅ Query translation
- ✅ Zero-downtime migration
- ✅ Rollback strategies

## Common Commands Across Examples

All examples support these AI-Shell natural language queries:

### Health & Monitoring
```
"Run health check on all databases"
"Show current connection pool usage"
"Find queries running longer than 5 seconds"
"What's the replication lag?"
```

### Performance
```
"Find slow queries and suggest optimizations"
"Analyze query patterns and recommend indexes"
"Show table sizes and growth trends"
"Check for table bloat that needs vacuuming"
```

### Operations
```
"Schedule daily backups at 2 AM"
"Create a backup right now"
"Show last backup status"
"Restore from yesterday's backup"
```

### Analytics
```
"Show top 10 most expensive queries"
"What's our query cache hit rate?"
"Compare performance week over week"
"Identify unused indexes"
```

## Example Data Volume

All examples include realistic data volumes:

- **E-Commerce**: 10K products, 50K orders, 100K reviews
- **SaaS**: 5 tenants, 200+ users, 1000+ projects
- **Analytics**: 1M+ events, 100K users, 50K sessions
- **Microservices**: 6 services, 30K+ records each
- **Migration**: 100K legacy records for testing

## Architecture Patterns Demonstrated

### Database Patterns
- Schema-per-tenant (SaaS)
- Database-per-service (Microservices)
- CQRS with read replicas (Analytics)
- Event sourcing (Microservices)
- Multi-master replication (E-Commerce)

### Integration Patterns
- Query federation
- API composition
- Database joins across systems
- Cache-aside pattern
- Event-driven updates

### Operational Patterns
- Automated provisioning
- Blue-green deployment
- Zero-downtime migration
- Automated failover
- Backup and recovery

## Troubleshooting

### Docker Issues
```bash
# Check if Docker is running
docker ps

# Restart Docker daemon
sudo systemctl restart docker

# Clean up old containers
docker system prune -a
```

### Port Conflicts
```bash
# Check what's using a port
lsof -i :5432

# Stop the example
cd examples/{name}
docker-compose down
```

### Database Connection Issues
```bash
# Check container logs
docker-compose logs postgres

# Restart specific service
docker-compose restart postgres

# Re-run setup
./scripts/cleanup.sh && ./scripts/setup.sh
```

### AI-Shell Issues
```bash
# Check AI-Shell version
ai-shell --version

# Update to latest
npm install -g aishell@latest

# Check API key
echo $AISHELL_API_KEY
```

## Best Practices from Examples

### 1. Connection Management
- Use connection pooling (all examples)
- Set appropriate timeouts
- Handle connection failures gracefully
- Monitor pool utilization

### 2. Query Optimization
- Index frequently queried columns
- Use EXPLAIN for complex queries
- Avoid N+1 queries
- Implement query result caching

### 3. Data Isolation
- Use schemas for multi-tenancy
- Implement row-level security
- Audit data access
- Encrypt sensitive data

### 4. Monitoring & Alerting
- Track slow queries
- Monitor connection pools
- Set up health checks
- Alert on threshold breaches

### 5. Backup & Recovery
- Automate backups
- Test restore procedures
- Implement point-in-time recovery
- Document recovery steps

## Learning Path

Recommended order for learning:

1. **Start with E-Commerce** (easiest)
   - Learn multi-database basics
   - Understand query federation
   - Practice performance tuning

2. **Move to SaaS Multi-Tenant** (medium)
   - Learn isolation patterns
   - Understand provisioning
   - Practice cross-tenant queries

3. **Try Analytics Dashboard** (medium)
   - Learn data warehousing
   - Understand ETL
   - Practice aggregations

4. **Explore Microservices** (advanced)
   - Learn distributed patterns
   - Understand service mesh
   - Practice polyglot persistence

5. **Study Legacy Migration** (advanced)
   - Learn migration strategies
   - Understand compatibility
   - Practice validation

## Contributing

Want to add more examples? We welcome:

- Industry-specific scenarios (healthcare, finance, etc.)
- Cloud-specific examples (AWS RDS, GCP CloudSQL, Azure)
- Specialized databases (TimescaleDB, CockroachDB, etc.)
- Advanced patterns (sharding, partitioning, etc.)

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## Support & Resources

- **Documentation**: [Main Docs](../docs/)
- **API Reference**: [API.md](../docs/API.md)
- **GitHub Issues**: [Issues](https://github.com/yourusername/aishell/issues)
- **Community**: [Discussions](https://github.com/yourusername/aishell/discussions)

## License

All examples are MIT licensed. Use them freely in your projects!

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                    Example Quick Reference                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Setup:    ./scripts/setup.sh                               │
│  Demo:     ./scripts/demo.sh                                │
│  Start:    docker-compose up -d                             │
│  Stop:     docker-compose down                              │
│  Logs:     docker-compose logs -f                           │
│  Cleanup:  ./scripts/cleanup.sh                             │
│                                                              │
│  AI-Shell: ai-shell                                         │
│  Config:   config/ai-shell.config.json                      │
│  Docs:     README.md                                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Next Steps

1. **Choose an example** that matches your use case
2. **Run the setup** script
3. **Try the demo** to see capabilities
4. **Experiment** with your own queries
5. **Adapt** the example to your needs

Happy database managing! 🚀
