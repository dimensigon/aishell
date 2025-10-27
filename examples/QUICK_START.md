# AI-Shell Examples - Quick Start Guide

## 🚀 Get Started in 3 Commands

```bash
# 1. Navigate to an example
cd examples/ecommerce

# 2. Setup (runs automatically)
./scripts/setup.sh

# 3. Try it out!
./scripts/demo.sh
```

**That's it!** You now have a fully functional multi-database e-commerce platform.

---

## 📋 What You Get

After running setup, you'll have:
- ✅ 3 databases running (PostgreSQL, MongoDB, Redis)
- ✅ 160,000+ sample records loaded
- ✅ AI-Shell configured and ready
- ✅ Interactive demo ready to run

---

## 🎯 Choose Your Example

### For Beginners: E-Commerce
```bash
cd examples/ecommerce
./scripts/setup.sh
```
**Learn**: Multi-database basics, query federation, performance tuning

---

### For SaaS Developers: Multi-Tenant
```bash
cd examples/saas-multitenant
./scripts/setup.sh
```
**Learn**: Tenant isolation, provisioning, cross-tenant analytics

---

### For Data Engineers: Analytics
```bash
cd examples/analytics-pipeline
./scripts/setup.sh
```
**Learn**: Data warehousing, ETL, real-time dashboards

---

### For Architects: Microservices
```bash
cd examples/microservices
./scripts/setup.sh
```
**Learn**: Service-per-database, distributed queries, polyglot persistence

---

### For Migration Projects: Legacy Migration
```bash
cd examples/legacy-migration
./scripts/setup.sh
```
**Learn**: Oracle→PostgreSQL, schema translation, zero-downtime migration

---

## 💡 Try These Queries

Once setup is complete, start AI-Shell and try:

### E-Commerce Queries
```
"Show me top 10 products by revenue with their average ratings"
"Which customers have abandoned carts worth more than $500?"
"Find slow queries and suggest optimizations"
```

### SaaS Queries
```
"Create a new tenant called 'BigCorp' with premium plan"
"Show resource usage across all tenants"
"Which tenants are approaching their plan limits?"
```

### Analytics Queries
```
"Show daily active users for the last 30 days"
"What's the conversion funnel from visit to purchase?"
"Generate cohort retention analysis"
```

---

## 🛠️ Prerequisites

Before starting, you need:
- **Docker** - [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** - Usually comes with Docker
- **4GB RAM** - Minimum (8GB recommended)
- **10GB Disk** - For all examples

Check if you're ready:
```bash
docker --version
docker-compose --version
```

---

## 📊 Example Comparison

| Example | Setup Time | Complexity | Best For |
|---------|-----------|------------|----------|
| E-Commerce | 5 min | Medium | **Start here!** |
| SaaS Multi-Tenant | 5 min | High | Multi-tenancy |
| Analytics | 7 min | Medium | BI & Reporting |
| Microservices | 8 min | High | Distributed systems |
| Migration | 10 min | High | Migrations |

---

## 🔍 What's Running?

After setup, check what's running:

```bash
# View all containers
docker-compose ps

# Check logs
docker-compose logs -f

# Access databases directly
docker-compose exec postgres psql -U admin -d ecommerce
docker-compose exec mongodb mongosh ecommerce
docker-compose exec redis redis-cli
```

---

## 🌐 Web Interfaces

Most examples include admin UIs:

- **Adminer** (PostgreSQL/MySQL): http://localhost:8080
- **Redis Commander**: http://localhost:8081
- **pgAdmin** (SaaS example): http://localhost:5050

---

## 🧹 Cleanup

When done:

```bash
# Stop and remove everything
./scripts/cleanup.sh

# Or manually
docker-compose down -v
```

---

## 📚 Full Documentation

Each example has complete documentation:

```bash
# Read the README
cat README.md

# View example commands
cat commands.txt

# Check configuration
cat config/ai-shell.config.json
```

---

## 🆘 Troubleshooting

### Port Already in Use
```bash
# Find what's using the port
lsof -i :5432

# Change port in docker-compose.yml
# Example: "5433:5432" instead of "5432:5432"
```

### Services Won't Start
```bash
# Check Docker is running
docker ps

# View logs for errors
docker-compose logs

# Restart specific service
docker-compose restart postgres
```

### Out of Memory
```bash
# Check Docker memory
docker stats

# Increase Docker Desktop memory (Settings → Resources)
# Or run fewer examples simultaneously
```

---

## 🎓 Learning Path

**Week 1**: E-Commerce example
- Day 1-2: Setup and basic queries
- Day 3-4: Performance optimization
- Day 5: Custom queries for your use case

**Week 2**: Choose second example
- SaaS for multi-tenancy patterns
- Analytics for data engineering
- Microservices for distributed systems
- Migration for migration projects

**Week 3+**: Advanced topics
- Combine patterns from multiple examples
- Adapt to your production needs
- Build custom examples

---

## 💪 Next Steps

1. ✅ Pick an example
2. ✅ Run setup
3. ✅ Try the demo
4. ✅ Experiment with queries
5. ✅ Read full documentation
6. ✅ Adapt to your needs

---

## 🤝 Get Help

- **Documentation**: See each example's README.md
- **Issues**: Check troubleshooting section
- **Examples**: commands.txt has 100+ examples
- **Community**: GitHub discussions

---

## ⚡ Pro Tips

1. **Start Simple**: Begin with E-Commerce example
2. **Read Logs**: Use `docker-compose logs -f` to watch what happens
3. **Try Commands**: The commands.txt file has copy-paste examples
4. **Modify Data**: Edit SQL files and re-run setup.sh
5. **Learn by Doing**: Best way to learn is to experiment!

---

## 🎉 You're Ready!

Choose an example above and get started.

**Remember**: All examples work out of the box. No configuration needed!

```bash
cd examples/ecommerce && ./scripts/setup.sh
```

Happy querying! 🚀
