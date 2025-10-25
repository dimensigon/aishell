# Part 7: GraphQL API & Web UI

**Level:** Expert
**Duration:** 60 minutes
**Prerequisites:** Parts 1-6 completed

## Overview

In this tutorial, you'll master AI-Shell's GraphQL API and Web UI, enabling powerful query capabilities and visual data exploration.

## Table of Contents

1. [GraphQL API Setup](#graphql-api-setup)
2. [Basic Queries](#basic-queries)
3. [Mutations (CRUD Operations)](#mutations-crud-operations)
4. [Real-time Subscriptions](#real-time-subscriptions)
5. [Web UI Walkthrough](#web-ui-walkthrough)
6. [Query Editor](#query-editor)
7. [Visual Query Builder](#visual-query-builder)
8. [Dashboard Creation](#dashboard-creation)
9. [Admin Panel](#admin-panel)
10. [Challenge Exercises](#challenge-exercises)

---

## 1. GraphQL API Setup

### Starting the GraphQL Server

```bash
# Start AI-Shell with GraphQL API enabled
ai-shell --api --port 8080

# Or with specific configuration
ai-shell --api --port 8080 --api-key "your-secure-key"

# With CORS enabled for web development
ai-shell --api --port 8080 --cors "*"
```

### API Endpoints

- **GraphQL Endpoint:** `http://localhost:8080/graphql`
- **GraphQL Playground:** `http://localhost:8080/playground`
- **REST API:** `http://localhost:8080/api`
- **WebSocket (Subscriptions):** `ws://localhost:8080/subscriptions`

### Configuration File

Create `config/graphql-config.yaml`:

```yaml
api:
  enabled: true
  port: 8080
  host: "0.0.0.0"

  auth:
    enabled: true
    api_key: "${API_KEY}"
    jwt_secret: "${JWT_SECRET}"

  cors:
    enabled: true
    origins:
      - "http://localhost:3000"
      - "https://yourdomain.com"

  rate_limiting:
    enabled: true
    max_requests: 100
    window_seconds: 60

  graphql:
    introspection: true
    playground: true
    depth_limit: 10
    complexity_limit: 1000
```

### Testing the API

```bash
# Test with curl
curl -X POST http://localhost:8080/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{"query": "{ __schema { types { name } } }"}'
```

---

## 2. Basic Queries

### Schema Introspection

```graphql
# Get all available types
query GetSchema {
  __schema {
    types {
      name
      kind
      description
    }
  }
}

# Get specific type details
query GetTypeDetails {
  __type(name: "Database") {
    name
    fields {
      name
      type {
        name
        kind
      }
    }
  }
}
```

### Database Queries

```graphql
# List all databases
query ListDatabases {
  databases {
    id
    name
    type
    host
    port
    status
    createdAt
  }
}

# Get specific database with tables
query GetDatabase($id: ID!) {
  database(id: $id) {
    id
    name
    type
    tables {
      name
      schema
      rowCount
      sizeBytes
    }
  }
}

# Variables:
{
  "id": "db-001"
}
```

### Table Queries

```graphql
# Query table data with filters
query QueryTable(
  $database: String!
  $table: String!
  $filter: FilterInput
  $limit: Int = 10
  $offset: Int = 0
) {
  queryTable(
    database: $database
    table: $table
    filter: $filter
    limit: $limit
    offset: $offset
  ) {
    columns
    rows
    totalCount
    hasMore
  }
}

# Variables:
{
  "database": "sales_db",
  "table": "orders",
  "filter": {
    "status": { "eq": "completed" },
    "total": { "gt": 1000 }
  },
  "limit": 20,
  "offset": 0
}
```

### Complex Filtering

```graphql
query ComplexQuery {
  queryTable(
    database: "ecommerce"
    table: "orders"
    filter: {
      AND: [
        { status: { in: ["pending", "processing"] } }
        {
          OR: [
            { total: { gt: 500 } }
            { priority: { eq: "high" } }
          ]
        }
        { created_at: { gte: "2024-01-01" } }
      ]
    }
    orderBy: { field: "created_at", direction: DESC }
    limit: 50
  ) {
    columns
    rows
    aggregations {
      sum(field: "total")
      avg(field: "total")
      count
    }
  }
}
```

### Aggregation Queries

```graphql
query SalesAnalytics {
  analytics: queryTable(
    database: "sales_db"
    table: "orders"
    filter: {
      created_at: { gte: "2024-01-01" }
    }
  ) {
    aggregations {
      totalRevenue: sum(field: "total")
      avgOrderValue: avg(field: "total")
      orderCount: count
      maxOrder: max(field: "total")
      minOrder: min(field: "total")
    }

    groupBy(field: "status") {
      key
      count
      sum(field: "total")
    }
  }
}
```

---

## 3. Mutations (CRUD Operations)

### Create Operations

```graphql
# Add new database connection
mutation AddDatabase($input: DatabaseInput!) {
  addDatabase(input: $input) {
    id
    name
    status
    message
  }
}

# Variables:
{
  "input": {
    "name": "analytics_db",
    "type": "POSTGRESQL",
    "host": "localhost",
    "port": 5432,
    "database": "analytics",
    "username": "admin",
    "password": "secure_password"
  }
}
```

### Update Operations

```graphql
# Update database configuration
mutation UpdateDatabase($id: ID!, $input: DatabaseUpdateInput!) {
  updateDatabase(id: $id, input: $input) {
    id
    name
    status
    updatedAt
  }
}

# Variables:
{
  "id": "db-001",
  "input": {
    "host": "new-host.example.com",
    "port": 5433,
    "maxConnections": 50
  }
}
```

### Delete Operations

```graphql
# Remove database connection
mutation RemoveDatabase($id: ID!) {
  removeDatabase(id: $id) {
    success
    message
  }
}

# Variables:
{
  "id": "db-001"
}
```

### Batch Operations

```graphql
# Execute multiple mutations in one request
mutation BatchOperations {
  createOrder: insertRow(
    database: "sales_db"
    table: "orders"
    data: {
      customer_id: 123
      total: 299.99
      status: "pending"
    }
  ) {
    id
    success
  }

  updateInventory: updateRow(
    database: "sales_db"
    table: "inventory"
    id: 456
    data: {
      quantity: { decrement: 1 }
    }
  ) {
    success
  }

  logTransaction: insertRow(
    database: "sales_db"
    table: "transactions"
    data: {
      order_id: "$createOrder.id"
      type: "sale"
      timestamp: "now()"
    }
  ) {
    id
    success
  }
}
```

---

## 4. Real-time Subscriptions

### Setting Up Subscriptions

```javascript
// JavaScript WebSocket client
const ws = new WebSocket('ws://localhost:8080/subscriptions');

ws.onopen = () => {
  // Subscribe to database changes
  ws.send(JSON.stringify({
    type: 'subscribe',
    query: `
      subscription OnDatabaseChange($database: String!) {
        databaseChanged(database: $database) {
          table
          operation
          data
          timestamp
        }
      }
    `,
    variables: {
      database: 'sales_db'
    }
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Database change:', data);
};
```

### Subscription Queries

```graphql
# Subscribe to table changes
subscription OnTableChange($database: String!, $table: String!) {
  tableChanged(database: $database, table: $table) {
    operation  # INSERT, UPDATE, DELETE
    rowId
    oldData
    newData
    timestamp
    user
  }
}

# Subscribe to query results
subscription OnQueryResults($queryId: ID!) {
  queryResultsUpdated(queryId: $queryId) {
    rows
    totalCount
    lastUpdated
  }
}

# Subscribe to system events
subscription OnSystemEvents {
  systemEvent {
    type      # CONNECTION, QUERY, ERROR, WARNING
    severity
    message
    details
    timestamp
  }
}
```

### Real-time Dashboard Example

```graphql
subscription RealtimeDashboard {
  # Live order count
  orderCount: tableChanged(
    database: "sales_db"
    table: "orders"
  ) {
    aggregation {
      count
    }
  }

  # New orders
  newOrders: tableChanged(
    database: "sales_db"
    table: "orders"
    filter: { operation: INSERT }
  ) {
    newData
    timestamp
  }

  # Revenue updates
  revenueUpdate: tableChanged(
    database: "sales_db"
    table: "orders"
    filter: { status: { eq: "completed" } }
  ) {
    aggregation {
      sum(field: "total")
    }
  }
}
```

---

## 5. Web UI Walkthrough

### Accessing the Web UI

1. Start AI-Shell with web UI enabled:
   ```bash
   ai-shell --web --port 3000
   ```

2. Open browser: `http://localhost:3000`

### UI Layout Overview

**Main Interface Description:**
```
┌─────────────────────────────────────────────────────────┐
│  [AI-Shell Logo]  Connections  Queries  Dashboards  ⚙️ │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Sidebar (Left)              Main Content Area          │
│  ┌──────────────┐           ┌──────────────────────┐   │
│  │ 🗄️ Databases  │           │                      │   │
│  │  ├─ sales_db  │           │   Query Results      │   │
│  │  │  ├─ orders │           │                      │   │
│  │  │  ├─ users  │           │   [Data Grid]        │   │
│  │  │  └─ ...    │           │                      │   │
│  │  └─ analytics │           │                      │   │
│  │                │           └──────────────────────┘   │
│  │ 📊 Dashboards │                                       │
│  │  ├─ Sales     │           Bottom Panel               │
│  │  └─ Metrics   │           ┌──────────────────────┐   │
│  │                │           │ Query Editor         │   │
│  │ 🔍 History    │           │ SELECT * FROM ...    │   │
│  └──────────────┘           └──────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Key Features

1. **Connection Management Panel:**
   - Add/edit/delete database connections
   - Test connection status (green = connected, red = error)
   - View connection details and stats

2. **Database Explorer:**
   - Tree view of all databases and tables
   - Schema viewer with data types
   - Row counts and size information
   - Quick actions (query, export, etc.)

3. **Query Results Grid:**
   - Sortable columns
   - Filterable data
   - Pagination controls
   - Export options (CSV, JSON, Excel)
   - Copy to clipboard

4. **Status Bar:**
   - Query execution time
   - Rows returned
   - Database connection status
   - Active queries indicator

---

## 6. Query Editor

### Basic Features

**Query Editor Interface:**
```
┌─────────────────────────────────────────────────┐
│ File  Edit  Run  Format  Help    [▶ Run] [💾]  │
├─────────────────────────────────────────────────┤
│  1  SELECT o.id, o.total, c.name               │
│  2  FROM orders o                               │
│  3  JOIN customers c ON o.customer_id = c.id   │
│  4  WHERE o.status = 'completed'                │
│  5  ORDER BY o.created_at DESC                  │
│  6  LIMIT 100;                                  │
│                                                  │
│  [Syntax highlighting, auto-complete active]    │
└─────────────────────────────────────────────────┘
```

### Advanced Editor Features

1. **Syntax Highlighting:**
   - SQL keywords in blue
   - Strings in green
   - Numbers in orange
   - Comments in gray

2. **Auto-completion:**
   ```sql
   -- Type "SEL" → suggests "SELECT"
   -- Type "FROM or" → suggests "orders" table
   -- Type "o." → suggests columns from orders table
   ```

3. **Query Templates:**
   ```sql
   -- Select template
   SELECT ${columns}
   FROM ${table}
   WHERE ${condition}
   ORDER BY ${order}
   LIMIT ${limit};

   -- Join template
   SELECT a.*, b.*
   FROM ${table1} a
   JOIN ${table2} b ON a.${key} = b.${key}
   WHERE ${condition};

   -- Aggregation template
   SELECT
     ${group_column},
     COUNT(*) as count,
     SUM(${sum_column}) as total
   FROM ${table}
   GROUP BY ${group_column}
   HAVING ${having_condition}
   ORDER BY count DESC;
   ```

4. **Multi-database Queries:**
   ```sql
   -- Query across multiple databases
   -- @database: sales_db
   SELECT * FROM orders WHERE total > 1000

   -- @database: analytics_db
   INSERT INTO daily_sales
   SELECT date, SUM(total) FROM [sales_db].orders
   GROUP BY date;
   ```

### Keyboard Shortcuts

```
Ctrl + Enter     - Execute query
Ctrl + S         - Save query
Ctrl + F         - Find
Ctrl + H         - Find and replace
Ctrl + /         - Comment/uncomment
Ctrl + Space     - Trigger auto-complete
Ctrl + Shift + F - Format query
Alt + Up/Down    - Move line up/down
Ctrl + D         - Duplicate line
```

---

## 7. Visual Query Builder

### Building Queries Visually

**Query Builder Interface:**
```
┌──────────────────────────────────────────────────┐
│ Visual Query Builder                   [SQL View]│
├──────────────────────────────────────────────────┤
│                                                   │
│  1. SELECT Columns                                │
│  ┌────────────────────────────────────────────┐  │
│  │ [✓] id          [✓] customer_name          │  │
│  │ [✓] total       [ ] created_at             │  │
│  │ [✓] status      [ ] updated_at             │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  2. FROM Table                                    │
│  ┌────────────────────────────────────────────┐  │
│  │ Database: [sales_db ▼]                     │  │
│  │ Table:    [orders ▼]                       │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  3. JOINs                                         │
│  ┌────────────────────────────────────────────┐  │
│  │ + Add JOIN                                  │  │
│  │   [customers ▼] ON orders.customer_id =    │  │
│  │                    customers.id             │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  4. WHERE Conditions                              │
│  ┌────────────────────────────────────────────┐  │
│  │ [status ▼] [equals ▼] [completed      ]   │  │
│  │ AND [total ▼] [greater than ▼] [1000  ]   │  │
│  │ + Add condition                             │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  5. ORDER BY                                      │
│  ┌────────────────────────────────────────────┐  │
│  │ [created_at ▼] [DESC ▼]                    │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  [Preview SQL] [Run Query]                       │
└──────────────────────────────────────────────────┘
```

### Step-by-Step Example

**Build a Sales Report Query:**

1. **Select Database and Table:**
   - Database: `sales_db`
   - Table: `orders`

2. **Choose Columns:**
   - ✓ id
   - ✓ customer_id
   - ✓ total
   - ✓ status
   - ✓ created_at

3. **Add JOIN to customers:**
   - Type: INNER JOIN
   - Table: customers
   - Condition: orders.customer_id = customers.id
   - Select: customers.name, customers.email

4. **Add Filters:**
   - status equals 'completed'
   - total greater than 500
   - created_at between '2024-01-01' and '2024-12-31'

5. **Group and Aggregate:**
   - Group by: customer_id, customers.name
   - Aggregates: COUNT(*) as order_count, SUM(total) as total_spent

6. **Sort Results:**
   - Order by: total_spent DESC
   - Limit: 50

**Generated SQL:**
```sql
SELECT
  c.name,
  c.email,
  COUNT(*) as order_count,
  SUM(o.total) as total_spent
FROM orders o
INNER JOIN customers c ON o.customer_id = c.id
WHERE
  o.status = 'completed'
  AND o.total > 500
  AND o.created_at BETWEEN '2024-01-01' AND '2024-12-31'
GROUP BY c.id, c.name, c.email
ORDER BY total_spent DESC
LIMIT 50;
```

---

## 8. Dashboard Creation

### Creating Your First Dashboard

**Step 1: New Dashboard**
```
Click: Dashboards → New Dashboard
Name: "Sales Overview"
Description: "Real-time sales metrics and trends"
```

**Step 2: Add Widgets**

```yaml
# Widget 1: Total Revenue (KPI Card)
type: kpi_card
title: "Total Revenue"
query: |
  SELECT SUM(total) as revenue
  FROM orders
  WHERE status = 'completed'
refresh: 30s
format: currency

# Widget 2: Orders Over Time (Line Chart)
type: line_chart
title: "Orders by Day"
query: |
  SELECT
    DATE(created_at) as date,
    COUNT(*) as orders,
    SUM(total) as revenue
  FROM orders
  GROUP BY DATE(created_at)
  ORDER BY date DESC
  LIMIT 30
x_axis: date
y_axis: [orders, revenue]
refresh: 60s

# Widget 3: Top Products (Bar Chart)
type: bar_chart
title: "Top 10 Products"
query: |
  SELECT
    p.name,
    COUNT(*) as sales,
    SUM(oi.quantity) as units
  FROM order_items oi
  JOIN products p ON oi.product_id = p.id
  GROUP BY p.id, p.name
  ORDER BY sales DESC
  LIMIT 10
x_axis: name
y_axis: sales
refresh: 120s

# Widget 4: Order Status (Pie Chart)
type: pie_chart
title: "Order Status Distribution"
query: |
  SELECT
    status,
    COUNT(*) as count
  FROM orders
  GROUP BY status
label: status
value: count
refresh: 60s

# Widget 5: Recent Orders (Table)
type: table
title: "Recent Orders"
query: |
  SELECT
    o.id,
    c.name as customer,
    o.total,
    o.status,
    o.created_at
  FROM orders o
  JOIN customers c ON o.customer_id = c.id
  ORDER BY o.created_at DESC
  LIMIT 20
columns:
  - id
  - customer
  - total
  - status
  - created_at
refresh: 30s
```

### Dashboard Layout

**Dashboard Configuration:**
```json
{
  "name": "Sales Overview",
  "layout": {
    "type": "grid",
    "columns": 12,
    "rows": "auto"
  },
  "widgets": [
    {
      "id": "revenue-kpi",
      "position": { "x": 0, "y": 0, "w": 3, "h": 2 }
    },
    {
      "id": "order-count-kpi",
      "position": { "x": 3, "y": 0, "w": 3, "h": 2 }
    },
    {
      "id": "avg-order-kpi",
      "position": { "x": 6, "y": 0, "w": 3, "h": 2 }
    },
    {
      "id": "conversion-kpi",
      "position": { "x": 9, "y": 0, "w": 3, "h": 2 }
    },
    {
      "id": "orders-timeline",
      "position": { "x": 0, "y": 2, "w": 8, "h": 4 }
    },
    {
      "id": "status-pie",
      "position": { "x": 8, "y": 2, "w": 4, "h": 4 }
    },
    {
      "id": "top-products",
      "position": { "x": 0, "y": 6, "w": 6, "h": 4 }
    },
    {
      "id": "recent-orders",
      "position": { "x": 6, "y": 6, "w": 6, "h": 4 }
    }
  ],
  "refresh": {
    "auto": true,
    "interval": 60
  },
  "filters": {
    "date_range": {
      "type": "daterange",
      "default": "last_30_days"
    },
    "status": {
      "type": "multiselect",
      "options": ["pending", "processing", "completed", "cancelled"]
    }
  }
}
```

### Interactive Dashboards

**Adding Interactivity:**

1. **Click-through Actions:**
   ```javascript
   // When clicking on a chart element
   onWidgetClick: {
     action: "navigate",
     target: "/orders/{id}",
     params: {
       id: "${clicked.row.id}"
     }
   }
   ```

2. **Dashboard Filters:**
   ```yaml
   filters:
     - name: date_range
       type: daterange
       default: last_30_days
       applies_to: [all]

     - name: customer_segment
       type: select
       options:
         - VIP
         - Regular
         - New
       applies_to: [revenue-kpi, orders-timeline]

     - name: product_category
       type: multiselect
       source:
         query: "SELECT DISTINCT category FROM products"
       applies_to: [top-products]
   ```

3. **Drill-down Capabilities:**
   ```yaml
   drill_down:
     - from: orders-by-region
       to: orders-by-city
       parameter: region

     - from: orders-by-city
       to: order-details
       parameter: city
   ```

---

## 9. Admin Panel

### Accessing Admin Features

**Admin Panel Layout:**
```
┌────────────────────────────────────────────────┐
│ Admin Panel                         [⚙️ Settings]│
├────────────────────────────────────────────────┤
│ 📊 System Overview                             │
│ ┌──────────────────────────────────────────┐   │
│ │ CPU: [████████░░] 80%                    │   │
│ │ Memory: [██████░░░░] 60%                 │   │
│ │ Disk: [███░░░░░░░] 30%                   │   │
│ │ Active Connections: 15 / 100             │   │
│ │ Queries/sec: 47                          │   │
│ └──────────────────────────────────────────┘   │
│                                                 │
│ 👥 User Management                             │
│ ┌──────────────────────────────────────────┐   │
│ │ User          Role      Status    Actions │   │
│ │ admin         Admin     Active    [Edit]  │   │
│ │ analyst1      Analyst   Active    [Edit]  │   │
│ │ readonly1     Viewer    Active    [Edit]  │   │
│ │ [+ Add User]                              │   │
│ └──────────────────────────────────────────┘   │
│                                                 │
│ 🔐 Security & Audit                            │
│ ┌──────────────────────────────────────────┐   │
│ │ Recent Activity:                          │   │
│ │ • User login: analyst1 (2 mins ago)      │   │
│ │ • Query executed: SELECT * FROM orders   │   │
│ │ • Dashboard viewed: Sales Overview       │   │
│ │ [View Full Audit Log]                    │   │
│ └──────────────────────────────────────────┘   │
│                                                 │
│ ⚡ Performance & Monitoring                    │
│ ┌──────────────────────────────────────────┐   │
│ │ Slow Queries: 3                           │   │
│ │ Failed Connections: 0                     │   │
│ │ Cache Hit Rate: 87%                       │   │
│ │ [View Detailed Metrics]                   │   │
│ └──────────────────────────────────────────┘   │
└────────────────────────────────────────────────┘
```

### User Management

**Creating Users via GraphQL:**

```graphql
# Create new user
mutation CreateUser($input: UserInput!) {
  createUser(input: $input) {
    id
    username
    email
    role
    permissions
  }
}

# Variables:
{
  "input": {
    "username": "analyst2",
    "email": "analyst2@company.com",
    "password": "SecurePass123!",
    "role": "ANALYST",
    "permissions": [
      "READ_DATA",
      "EXECUTE_QUERIES",
      "CREATE_DASHBOARDS"
    ],
    "databases": ["sales_db", "analytics_db"]
  }
}
```

**Role Definitions:**

```yaml
roles:
  admin:
    permissions:
      - ALL
    description: "Full system access"

  analyst:
    permissions:
      - READ_DATA
      - EXECUTE_QUERIES
      - CREATE_DASHBOARDS
      - EXPORT_DATA
    restrictions:
      - NO_DELETE
      - NO_SCHEMA_CHANGES
    description: "Data analysis and reporting"

  developer:
    permissions:
      - READ_DATA
      - WRITE_DATA
      - EXECUTE_QUERIES
      - MANAGE_SCHEMA
    restrictions:
      - NO_USER_MANAGEMENT
    description: "Development and testing"

  viewer:
    permissions:
      - READ_DATA
      - VIEW_DASHBOARDS
    restrictions:
      - NO_EXPORT
      - NO_QUERIES
    description: "Read-only access to dashboards"
```

### Audit Logging

**Query Audit Logs:**

```graphql
query AuditLogs(
  $startDate: DateTime!
  $endDate: DateTime!
  $userId: ID
  $action: String
  $limit: Int = 100
) {
  auditLogs(
    startDate: $startDate
    endDate: $endDate
    userId: $userId
    action: $action
    limit: $limit
  ) {
    id
    timestamp
    user {
      id
      username
    }
    action
    resource
    details
    ipAddress
    success
  }
}
```

**Example Audit Log Entry:**

```json
{
  "id": "audit-12345",
  "timestamp": "2024-01-15T10:30:45Z",
  "user": {
    "id": "user-001",
    "username": "analyst1"
  },
  "action": "QUERY_EXECUTED",
  "resource": "sales_db.orders",
  "details": {
    "query": "SELECT * FROM orders WHERE total > 1000",
    "rows_returned": 47,
    "execution_time_ms": 234
  },
  "ipAddress": "192.168.1.100",
  "success": true
}
```

### System Monitoring

**Monitoring Dashboard Query:**

```graphql
query SystemMetrics {
  systemMetrics {
    cpu {
      usage
      load_average
    }
    memory {
      total
      used
      available
      usage_percent
    }
    database {
      connections_active
      connections_idle
      connections_max
      queries_per_second
      slow_queries_count
    }
    cache {
      hit_rate
      miss_rate
      size_mb
      evictions
    }
    api {
      requests_per_minute
      avg_response_time_ms
      error_rate
    }
  }
}
```

---

## 10. Challenge Exercises

### Challenge 1: Advanced Dashboard

**Objective:** Create a comprehensive sales analytics dashboard with:
- Real-time KPIs
- Interactive charts with drill-down
- Custom filters
- Automated alerts

**Requirements:**
1. At least 6 different widget types
2. Cross-filtering between widgets
3. Refresh intervals optimized for performance
4. Mobile-responsive layout

**Hints:**
- Use subscriptions for real-time updates
- Implement caching for expensive queries
- Add loading states for better UX

### Challenge 2: Multi-Database Query

**Objective:** Create a GraphQL query that:
- Joins data from PostgreSQL and MongoDB
- Aggregates results
- Handles different data types
- Optimizes performance

**Sample Scenario:**
```
PostgreSQL (orders):     MongoDB (products):
- order_id               - product_id
- product_id             - name
- quantity               - category
- price                  - metadata
- created_at             - reviews []
```

**Your Task:**
Create a query that shows:
- Product name and category
- Total sales per product
- Average review rating
- Revenue by category

### Challenge 3: Custom API Integration

**Objective:** Build a custom GraphQL resolver that:
- Fetches data from external API
- Transforms and combines with local data
- Implements caching
- Handles errors gracefully

**Example Use Case:**
Integrate weather data with store sales to analyze correlation.

### Challenge 4: Security Implementation

**Objective:** Implement comprehensive security:
- Row-level security
- API rate limiting
- Query complexity limiting
- Audit logging for sensitive operations

**Requirements:**
```yaml
security:
  row_level:
    - table: orders
      rule: "user_id = current_user_id OR role = 'admin'"

  rate_limiting:
    per_user: 100 requests/minute
    per_ip: 200 requests/minute

  complexity:
    max_depth: 10
    max_complexity: 1000

  audit:
    log_queries: true
    log_mutations: true
    log_sensitive_data: false
```

### Challenge 5: Performance Optimization

**Objective:** Optimize slow dashboard queries:

**Scenario:**
A dashboard with 10 widgets takes 30 seconds to load.

**Your Tasks:**
1. Identify slow queries using monitoring
2. Add appropriate indexes
3. Implement query caching
4. Use query batching
5. Optimize widget refresh intervals

**Success Criteria:**
- Dashboard loads in under 3 seconds
- All widgets refresh smoothly
- No database overload

---

## Solutions

### Solution 1: Advanced Dashboard

```yaml
dashboard:
  name: "Sales Analytics Pro"
  layout:
    type: grid
    responsive: true

  widgets:
    # Real-time KPIs
    - type: kpi_card
      id: revenue
      title: "Revenue (Live)"
      query: |
        SELECT SUM(total) FROM orders
        WHERE status = 'completed'
      subscription: true
      refresh: 5s
      format: currency
      comparison:
        period: yesterday
        show_trend: true

    # Interactive line chart with drill-down
    - type: line_chart
      id: revenue_trend
      title: "Revenue Trend"
      query: |
        SELECT
          DATE_TRUNC('day', created_at) as date,
          SUM(total) as revenue
        FROM orders
        WHERE created_at >= NOW() - INTERVAL '30 days'
        GROUP BY DATE_TRUNC('day', created_at)
        ORDER BY date
      drill_down:
        enabled: true
        target: hourly_revenue
        parameter: date
      filters:
        date_range: enabled

    # Heatmap with interactions
    - type: heatmap
      id: sales_heatmap
      title: "Sales by Hour & Day"
      query: |
        SELECT
          EXTRACT(DOW FROM created_at) as day_of_week,
          EXTRACT(HOUR FROM created_at) as hour,
          COUNT(*) as orders
        FROM orders
        GROUP BY day_of_week, hour
      on_click:
        action: filter
        target: [order_table]

    # Filters panel
    - type: filters
      id: global_filters
      filters:
        - name: date_range
          type: daterange
          default: last_30_days
        - name: region
          type: multiselect
          query: "SELECT DISTINCT region FROM stores"
        - name: category
          type: multiselect
          query: "SELECT DISTINCT category FROM products"

  alerts:
    - name: "Low Sales"
      condition: "revenue < 10000"
      notification:
        type: email
        recipients: ["manager@company.com"]

    - name: "High Error Rate"
      condition: "error_rate > 0.05"
      notification:
        type: slack
        channel: "#alerts"
```

### Solution 2: Multi-Database Query

```graphql
type Query {
  productAnalytics(
    dateRange: DateRangeInput!
    category: String
  ): [ProductAnalytic!]!
}

type ProductAnalytic {
  productId: ID!
  name: String!
  category: String!
  totalSales: Int!
  revenue: Float!
  averageRating: Float
  reviewCount: Int!
  metadata: JSON
}
```

**Resolver Implementation:**

```javascript
const resolvers = {
  Query: {
    productAnalytics: async (_, { dateRange, category }, context) => {
      // Query PostgreSQL for sales data
      const salesData = await context.postgres.query(`
        SELECT
          product_id,
          COUNT(*) as total_sales,
          SUM(price * quantity) as revenue
        FROM orders
        WHERE created_at BETWEEN $1 AND $2
        ${category ? 'AND product_id IN (SELECT id FROM products WHERE category = $3)' : ''}
        GROUP BY product_id
      `, [dateRange.start, dateRange.end, category]);

      // Query MongoDB for product data
      const productIds = salesData.rows.map(r => r.product_id);
      const productsData = await context.mongo
        .collection('products')
        .find({ product_id: { $in: productIds } })
        .toArray();

      // Combine and transform data
      return salesData.rows.map(sale => {
        const product = productsData.find(p => p.product_id === sale.product_id);
        const avgRating = product?.reviews
          ? product.reviews.reduce((sum, r) => sum + r.rating, 0) / product.reviews.length
          : null;

        return {
          productId: sale.product_id,
          name: product?.name || 'Unknown',
          category: product?.category || 'Uncategorized',
          totalSales: parseInt(sale.total_sales),
          revenue: parseFloat(sale.revenue),
          averageRating: avgRating,
          reviewCount: product?.reviews?.length || 0,
          metadata: product?.metadata || {}
        };
      });
    }
  }
};
```

### Solution 3: Performance Optimization

**Step 1: Identify Slow Queries**

```graphql
query SlowQueries {
  systemMetrics {
    slowQueries(threshold: 1000) {
      query
      execution_time_ms
      count
      table
    }
  }
}
```

**Step 2: Add Indexes**

```sql
-- Add indexes for common queries
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_customer_id ON orders(customer_id);

-- Composite index for common filter combination
CREATE INDEX idx_orders_status_date ON orders(status, created_at);

-- Partial index for completed orders
CREATE INDEX idx_orders_completed ON orders(created_at)
WHERE status = 'completed';
```

**Step 3: Implement Caching**

```javascript
// Redis caching for expensive queries
const cacheKey = `dashboard:sales:${date}`;
const cached = await redis.get(cacheKey);

if (cached) {
  return JSON.parse(cached);
}

const result = await executeQuery(query);
await redis.setex(cacheKey, 300, JSON.stringify(result)); // 5 min cache
return result;
```

**Step 4: Query Batching**

```javascript
// Use DataLoader for batching
const productLoader = new DataLoader(async (productIds) => {
  const products = await db.query(
    'SELECT * FROM products WHERE id = ANY($1)',
    [productIds]
  );
  return productIds.map(id => products.find(p => p.id === id));
});

// Usage in resolver
const product = await productLoader.load(order.product_id);
```

---

## Summary

You've learned:
- ✅ GraphQL API setup and configuration
- ✅ Writing queries, mutations, and subscriptions
- ✅ Using the Web UI for data exploration
- ✅ Building visual queries without SQL
- ✅ Creating interactive dashboards
- ✅ Managing users and security
- ✅ Performance optimization techniques

## Next Steps

1. **Practice:** Build your own dashboard with real data
2. **Experiment:** Try advanced GraphQL features
3. **Optimize:** Use monitoring to improve performance
4. **Secure:** Implement proper authentication and authorization
5. **Scale:** Move to Part 8 for production scenarios

## Additional Resources

- GraphQL Documentation: https://graphql.org
- Apollo Client: https://www.apollographql.com/docs/react
- Dashboard Best Practices: [link]
- Security Guidelines: [link]

---

**Time to Complete:** 60 minutes
**Difficulty:** Expert
**Prerequisites:** Parts 1-6

Happy querying!
