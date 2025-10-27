# External Oracle Container Setup

## Overview

The AI-Shell test environment connects to an **external Oracle Database 23c Free container** named `23cfree` that should already be running on your system.

## Required Oracle Container Specifications

### Container Details
- **Container Name**: `23cfree` (exactly)
- **Image**: `container-registry.oracle.com/database/free:latest` or compatible
- **SYS Password**: `MyOraclePass123`
- **Port Mapping**: `1521:1521` (host:container)

### Connection Strings

**CDB (Container Database)**:
```
SYS/MyOraclePass123@//localhost:1521/free as SYSDBA
```

**PDB (Pluggable Database)**:
```
SYS/MyOraclePass123@//localhost:1521/freepdb1 as SYSDBA
```

## Verify Existing Oracle Container

Check if the Oracle container is already running:

```bash
# Check if container exists and is running
docker ps | grep 23cfree

# Should show something like:
# CONTAINER ID   IMAGE                                     PORTS                    NAMES
# abc123def456   container-registry.oracle.com/database...  0.0.0.0:1521->1521/tcp   23cfree
```

## Connect to External Oracle Container

### Method 1: Using SQL*Plus inside container
```bash
# Connect to CDB
docker exec -it 23cfree sqlplus sys/MyOraclePass123@//localhost:1521/free as sysdba

# Connect to PDB
docker exec -it 23cfree sqlplus sys/MyOraclePass123@//localhost:1521/freepdb1 as sysdba
```

### Method 2: Using SQL*Plus from host
```bash
# If you have Oracle client installed on host
sqlplus sys/MyOraclePass123@//localhost:1521/free as sysdba
sqlplus sys/MyOraclePass123@//localhost:1521/freepdb1 as sysdba
```

### Method 3: Using docker exec for quick queries
```bash
# Query CDB
docker exec 23cfree bash -c "echo 'SELECT * FROM V\$VERSION;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/free as sysdba"

# Query PDB
docker exec 23cfree bash -c "echo 'SELECT NAME, OPEN_MODE FROM V\$PDBS;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/freepdb1 as sysdba"
```

## Initialize Test Database (Optional)

If the external Oracle container doesn't have test data, you can initialize it:

### Copy and Execute Init Script

```bash
# Copy init script to container
docker cp ./init-scripts/oracle/01-init.sql 23cfree:/tmp/

# Execute initialization script in PDB
docker exec 23cfree bash -c "echo '@/tmp/01-init.sql' | sqlplus sys/MyOraclePass123@//localhost:1521/freepdb1 as sysdba"
```

### Manual Initialization

```bash
# Connect to PDB
docker exec -it 23cfree sqlplus sys/MyOraclePass123@//localhost:1521/freepdb1 as sysdba

-- Inside SQL*Plus:
SQL> CREATE USER test_user IDENTIFIED BY TestPass123;
SQL> GRANT CONNECT, RESOURCE, CREATE SESSION TO test_user;
SQL> GRANT UNLIMITED TABLESPACE TO test_user;
SQL> ALTER USER test_user QUOTA UNLIMITED ON USERS;
SQL> EXIT
```

## Test Connection

### Quick Connection Test
```bash
# Test CDB connection
docker exec 23cfree bash -c "echo 'SELECT 1 FROM DUAL;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/free as sysdba"

# Expected output: 1

# Test PDB connection
docker exec 23cfree bash -c "echo 'SELECT 1 FROM DUAL;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/freepdb1 as sysdba"

# Expected output: 1
```

### Check PDB Status
```bash
docker exec 23cfree bash -c "echo 'SELECT NAME, OPEN_MODE FROM V\$PDBS;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/free as sysdba"

# Expected output:
# NAME         OPEN_MODE
# ------------ ----------
# PDB$SEED     READ ONLY
# FREEPDB1     READ WRITE
```

## If Oracle Container Doesn't Exist

If you need to create the Oracle 23c Free container:

```bash
docker run -d \
  --name 23cfree \
  -p 1521:1521 \
  -p 5500:5500 \
  -e ORACLE_PWD=MyOraclePass123 \
  -e ORACLE_SID=FREE \
  -e ORACLE_PDB=FREEPDB1 \
  -e ORACLE_CHARACTERSET=AL32UTF8 \
  -v oracle_data:/opt/oracle/oradata \
  --shm-size=1g \
  container-registry.oracle.com/database/free:latest
```

**Important**: Wait for Oracle to be ready (this can take 5-10 minutes on first start):

```bash
# Watch logs until you see "DATABASE IS READY TO USE!"
docker logs -f 23cfree

# Wait for this message:
# #########################
# DATABASE IS READY TO USE!
# #########################
```

## Network Considerations

### Option 1: External Container on Same Host
The Oracle container is accessible via `localhost:1521` from the host machine.

### Option 2: Connect to External Container via Docker Network
If you want the AI-Shell test containers to communicate with the external Oracle container:

```bash
# Connect external oracle container to the test network
docker network connect aishell-test-network 23cfree

# Now internal services can use:
# CDB: sys/MyOraclePass123@//23cfree:1521/free as sysdba
# PDB: sys/MyOraclePass123@//23cfree:1521/freepdb1 as sysdba
```

## Oracle-Specific Configuration

### Check Oracle Version
```bash
docker exec 23cfree bash -c "echo 'SELECT * FROM V\$VERSION;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/free as sysdba"
```

### Check Tablespace Usage
```bash
docker exec 23cfree bash -c "echo 'SELECT TABLESPACE_NAME, SUM(BYTES)/1024/1024 AS MB FROM DBA_DATA_FILES GROUP BY TABLESPACE_NAME;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/free as sysdba"
```

### List Users
```bash
docker exec 23cfree bash -c "echo 'SELECT USERNAME, ACCOUNT_STATUS FROM DBA_USERS ORDER BY USERNAME;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/free as sysdba"
```

## Troubleshooting

### Container Not Found
```bash
# List all containers (including stopped)
docker ps -a | grep 23cfree

# If stopped, start it
docker start 23cfree

# Check logs
docker logs 23cfree
```

### Port Already in Use
```bash
# Check what's using port 1521
lsof -i :1521

# If another process is using it, stop that process or use a different port
```

### Connection Refused
```bash
# Check if Oracle listener is running
docker exec 23cfree lsnrctl status

# Check if database is open
docker exec 23cfree bash -c "echo 'SELECT STATUS FROM V\$INSTANCE;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/free as sysdba"

# Expected output: OPEN
```

### PDB Not Open
```bash
# Check PDB status
docker exec 23cfree bash -c "echo 'SELECT NAME, OPEN_MODE FROM V\$PDBS;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/free as sysdba"

# If PDB is MOUNTED, open it:
docker exec 23cfree bash -c "echo 'ALTER PLUGGABLE DATABASE FREEPDB1 OPEN;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/free as sysdba"
```

### Authentication Failed
```bash
# Reset SYS password
docker exec 23cfree bash -c "./setPassword.sh MyOraclePass123"

# Or manually:
docker exec 23cfree bash -c "echo 'ALTER USER SYS IDENTIFIED BY MyOraclePass123;' | sqlplus -s / as sysdba"
```

### Slow Performance
```bash
# Oracle 23c Free requires at least:
# - 2GB RAM
# - 1GB shared memory
# - 10GB disk space

# Check container resources
docker stats 23cfree

# Increase shared memory if needed
docker update --shm-size=2g 23cfree
```

## Integration with AI-Shell Tests

The AI-Shell integration tests will connect to the external Oracle container using:

```typescript
// Connection configuration for CDB in tests
const oracleCDBConfig = {
  user: 'sys',
  password: 'MyOraclePass123',
  connectString: 'localhost:1521/free',
  privilege: oracledb.SYSDBA
};

// Connection configuration for PDB in tests
const oraclePDBConfig = {
  user: 'sys',
  password: 'MyOraclePass123',
  connectString: 'localhost:1521/freepdb1',
  privilege: oracledb.SYSDBA
};
```

## Health Checks

The external Oracle container should respond to health checks:

```bash
# Manual health check for CDB
docker exec 23cfree bash -c "echo 'SELECT 1 FROM DUAL;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/free as sysdba" | grep -q "1"
echo $?  # Should output: 0

# Manual health check for PDB
docker exec 23cfree bash -c "echo 'SELECT 1 FROM DUAL;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/freepdb1 as sysdba" | grep -q "1"
echo $?  # Should output: 0
```

## Performance Optimization

### Recommended Settings
```bash
# Set Oracle to use more memory (if available)
docker exec 23cfree bash -c "echo 'ALTER SYSTEM SET SGA_TARGET=1G SCOPE=SPFILE;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/free as sysdba"

# Enable automatic memory management
docker exec 23cfree bash -c "echo 'ALTER SYSTEM SET MEMORY_TARGET=2G SCOPE=SPFILE;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/free as sysdba"

# Restart required for changes to take effect
docker restart 23cfree
```

## Security Note

⚠️ **WARNING**: These configurations are for **TESTING PURPOSES ONLY**!

- Simple password for development convenience
- SYS user with SYSDBA privilege (full access)
- No encryption configured
- Ports exposed to host

For production environments, use:
- Strong, random passwords
- Limited user privileges (don't use SYS for applications)
- Transparent Data Encryption (TDE)
- Network encryption (SQLNet)
- Firewall restrictions
- Regular security patches

## Oracle License

Oracle Database 23c Free is free to use for:
- Development
- Testing
- Prototyping
- Education

**License Terms**: Oracle Database Free Use Terms and Conditions

## Summary

The AI-Shell test environment expects an **external Oracle container** to exist with:
- Container name: `23cfree`
- SYS password: `MyOraclePass123`
- Port: `1521` (host) → `1521` (container)
- CDB Connection: `SYS/MyOraclePass123@//localhost:1521/free as SYSDBA`
- PDB Connection: `SYS/MyOraclePass123@//localhost:1521/freepdb1 as SYSDBA`

Ensure this container is running before executing AI-Shell Oracle database integration tests.

## Quick Reference

```bash
# Check if running
docker ps | grep 23cfree

# Start if stopped
docker start 23cfree

# Test CDB connection
docker exec 23cfree bash -c "echo 'SELECT 1 FROM DUAL;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/free as sysdba"

# Test PDB connection
docker exec 23cfree bash -c "echo 'SELECT 1 FROM DUAL;' | sqlplus -s sys/MyOraclePass123@//localhost:1521/freepdb1 as sysdba"

# Check logs
docker logs 23cfree

# Connect interactively
docker exec -it 23cfree sqlplus sys/MyOraclePass123@//localhost:1521/freepdb1 as sysdba
```
