# Getting Started - AI-Shell Docker Test Environment

## ⚡ Quick Start (60 seconds)

```bash
# 1. Navigate to docker directory
cd /home/claude/AIShell/aishell/docker

# 2. Start all services
./start.sh up

# 3. Wait for services to be healthy (2-3 minutes)
./start.sh status

# 4. Test connections
./test-connections.sh

# 5. You're ready to test! 🎉
```

## 🔌 Connect to Databases

### PostgreSQL
```bash
psql postgresql://postgres:MyPostgresPass123@localhost:5432/testdb
```

### MySQL (Note: Port 3307!)
```bash
mysql -h localhost -P 3307 -u root -pMyMySQLPass123 testdb
```

### MongoDB
```bash
mongosh "mongodb://admin:MyMongoPass123@localhost:27017/testdb?authSource=admin"
```

### Redis
```bash
redis-cli -h localhost -p 6379
```

### Oracle Database
```bash
# CDB
sqlplus sys/MyOraclePass123@//localhost:1521/FREE as sysdba

# PDB
sqlplus system/MyOraclePass123@//localhost:1521/FREEPDB1
```

## 🌐 Web Admin Interfaces

- **Adminer** (SQL): http://localhost:8080
- **Mongo Express**: http://localhost:8081 (admin/pass)
- **Redis Commander**: http://localhost:8082
- **Oracle EM**: https://localhost:5500/em

## 🛠️ Common Tasks

### View Service Status
```bash
./start.sh status
```

### View Logs
```bash
./start.sh logs              # All services
./start.sh logs postgres     # Specific service
```

### Restart a Service
```bash
./start.sh restart postgres
```

### Stop Services
```bash
./start.sh down
```

### Clean Everything (deletes data!)
```bash
./start.sh clean
```

## 📖 Full Documentation

- **README.md** - Comprehensive guide with all details
- **QUICK_REFERENCE.md** - Connection strings and commands
- **IMPLEMENTATION_SUMMARY.md** - What was created and why

## 🎯 Integration with AI-Shell Tests

### Example Node.js Connection
```javascript
// PostgreSQL
const { Client } = require('pg');
const client = new Client({
  connectionString: 'postgresql://postgres:MyPostgresPass123@localhost:5432/testdb'
});

// MySQL (Note: Port 3307!)
const mysql = require('mysql2/promise');
const connection = await mysql.createConnection({
  host: 'localhost',
  port: 3307,
  user: 'root',
  password: 'MyMySQLPass123',
  database: 'testdb'
});

// MongoDB
const { MongoClient } = require('mongodb');
const client = new MongoClient('mongodb://admin:MyMongoPass123@localhost:27017/testdb?authSource=admin');

// Redis
const redis = require('redis');
const client = redis.createClient({
  url: 'redis://localhost:6379'
});

// Oracle
const oracledb = require('oracledb');
const connection = await oracledb.getConnection({
  user: 'system',
  password: 'MyOraclePass123',
  connectString: 'localhost:1521/FREEPDB1'
});
```

## 🧪 Sample Data Available

All databases include:
- 5 test users
- 10 products (Electronics, Furniture, Office Supplies)
- 4 sample orders
- Consistent data across all databases

## ⚠️ Important Notes

1. **Oracle startup**: Takes 2-3 minutes on first run
2. **MySQL port**: Uses 3307 (not 3306)
3. **Data persistence**: Stored in Docker volumes
4. **Testing only**: Not for production use
5. **Resource needs**: 12GB RAM minimum

## 🆘 Troubleshooting

### Services won't start
```bash
docker info                          # Check Docker is running
./start.sh logs                      # View error logs
```

### Connection refused
```bash
./start.sh status                    # Check if services are healthy
./test-connections.sh                # Test each database
```

### Out of memory
```bash
docker stats                         # Check resource usage
# Increase Docker memory: Settings → Resources → Memory → 16GB
```

### Clean slate
```bash
./start.sh clean                     # Remove everything
./start.sh up                        # Start fresh
```

## 📞 Need Help?

1. Check logs: `./start.sh logs [service]`
2. View status: `./start.sh status`
3. Read full docs: `README.md`
4. Run tests: `./test-connections.sh`

## ✅ Validation Checklist

Before running your tests:

- [ ] All services are running: `./start.sh status`
- [ ] All health checks pass: `./test-connections.sh`
- [ ] Can connect to PostgreSQL
- [ ] Can connect to MySQL
- [ ] Can connect to MongoDB
- [ ] Can connect to Redis
- [ ] Can connect to Oracle (CDB and PDB)

---

**You're all set! Start testing with AI-Shell! 🚀**
