# AI-Shell Web UI API Documentation

## Overview

The AI-Shell Web UI provides a comprehensive REST API for managing database connections, executing queries, and administering users. All endpoints require authentication via JWT tokens except for registration and login.

## Base URL

```
http://localhost:8000/api
```

## Authentication

### Register User

**POST** `/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string (min 8 characters)"
}
```

**Response:**
```json
{
  "success": true,
  "message": "User registered successfully"
}
```

### Login

**POST** `/auth/login`

Authenticate and receive JWT tokens.

**Request Body:**
```json
{
  "username": "string",
  "password": "string",
  "twoFactorCode": "string (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "accessToken": "string",
    "refreshToken": "string",
    "expiresIn": 1800,
    "user": {
      "id": "string",
      "username": "string",
      "email": "string",
      "role": "admin|user|viewer",
      "twoFactorEnabled": false,
      "createdAt": "2024-01-01T00:00:00Z"
    }
  }
}
```

### Logout

**POST** `/auth/logout`

Invalidate current session.

**Headers:**
```
Authorization: Bearer {accessToken}
```

### Get Current User

**GET** `/auth/me`

Get information about the authenticated user.

**Headers:**
```
Authorization: Bearer {accessToken}
```

## Database Connections

### List Connections

**GET** `/connections`

Get all database connections for the current user.

**Headers:**
```
Authorization: Bearer {accessToken}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "string",
      "name": "string",
      "type": "postgresql|mysql|mongodb|redis|sqlite",
      "host": "string",
      "port": 5432,
      "database": "string",
      "username": "string",
      "ssl": false,
      "status": "connected|disconnected|error",
      "createdAt": "2024-01-01T00:00:00Z",
      "lastUsed": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Create Connection

**POST** `/connections`

Create a new database connection.

**Request Body:**
```json
{
  "name": "string",
  "type": "postgresql|mysql|mongodb|redis|sqlite",
  "host": "string",
  "port": 5432,
  "database": "string",
  "username": "string",
  "password": "string",
  "ssl": false
}
```

### Update Connection

**PUT** `/connections/{connectionId}`

Update an existing database connection.

### Delete Connection

**DELETE** `/connections/{connectionId}`

Delete a database connection.

### Test Connection

**POST** `/connections/{connectionId}/test`

Test a database connection.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "connected"
  }
}
```

## Query Execution

### Execute Query

**POST** `/queries/execute`

Execute a SQL query on a database connection.

**Request Body:**
```json
{
  "connectionId": "string",
  "query": "SELECT * FROM users LIMIT 10",
  "parameters": {
    "key": "value"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "query": "string",
    "columns": ["id", "name", "email"],
    "rows": [
      {"id": 1, "name": "John", "email": "john@example.com"}
    ],
    "rowCount": 1,
    "executionTime": 45,
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

### Get Query History

**GET** `/queries/history`

Get query execution history.

**Query Parameters:**
- `page` (number): Page number (default: 1)
- `pageSize` (number): Items per page (default: 20)
- `connectionId` (string): Filter by connection

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [],
    "total": 100,
    "page": 1,
    "pageSize": 20,
    "totalPages": 5
  }
}
```

### Get Table Schema

**GET** `/connections/{connectionId}/schema/{tableName}`

Get schema information for a specific table.

### Get Tables

**GET** `/connections/{connectionId}/tables`

List all tables in a database connection.

## Performance Metrics

### Get Metrics

**GET** `/metrics`

Get performance metrics for database connections.

**Query Parameters:**
- `connectionId` (string): Connection ID
- `metric` (string): Specific metric name
- `startTime` (ISO 8601): Start time
- `endTime` (ISO 8601): End time

## User Management (Admin Only)

### List Users

**GET** `/users`

Get all users (admin only).

**Query Parameters:**
- `page` (number): Page number
- `pageSize` (number): Items per page

### Update User

**PUT** `/users/{userId}`

Update user information (admin only).

**Request Body:**
```json
{
  "email": "string",
  "role": "admin|user|viewer"
}
```

### Delete User

**DELETE** `/users/{userId}`

Delete a user (admin only).

## Audit Logs

### Get Audit Logs

**GET** `/audit`

Get audit logs.

**Query Parameters:**
- `userId` (string): Filter by user
- `action` (string): Filter by action type
- `page` (number): Page number
- `pageSize` (number): Items per page

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "string",
        "userId": "string",
        "username": "string",
        "action": "login|logout|create|update|delete|execute",
        "resource": "string",
        "details": {},
        "timestamp": "2024-01-01T00:00:00Z",
        "ipAddress": "192.168.1.1"
      }
    ],
    "total": 500,
    "page": 1,
    "pageSize": 25,
    "totalPages": 20
  }
}
```

## Export Data

### Export Query Results

**POST** `/export`

Export query results to various formats.

**Request Body:**
```json
{
  "format": "csv|json|xlsx",
  "queryResult": {
    "columns": ["id", "name"],
    "rows": [{"id": 1, "name": "Test"}]
  }
}
```

**Response:** Binary file download

## WebSocket

### Connect

**WebSocket** `/ws`

Connect to real-time updates WebSocket.

**Authentication:**
```javascript
const socket = io('ws://localhost:8000', {
  auth: { token: 'your-jwt-token' }
});
```

**Message Types:**
- `query_result`: Real-time query results
- `metric_update`: Performance metric updates
- `connection_status`: Connection status changes
- `notification`: System notifications

## Error Responses

All endpoints return errors in the following format:

```json
{
  "success": false,
  "error": "Error message",
  "message": "Additional details"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

## Rate Limiting

API endpoints are rate-limited to:
- **Authentication**: 5 requests per minute
- **Queries**: 60 requests per minute
- **Other endpoints**: 100 requests per minute

## Best Practices

1. **Always use HTTPS** in production
2. **Store tokens securely** (httpOnly cookies recommended)
3. **Implement token refresh** before expiration
4. **Handle errors gracefully** with retry logic
5. **Use pagination** for large datasets
6. **Cache responses** where appropriate
7. **Monitor rate limits** and implement backoff

## SDK Example

```typescript
import api from '@services/api';

// Login
const { data } = await api.login({
  username: 'user',
  password: 'pass'
});

// Execute query
const result = await api.executeQuery({
  connectionId: 'conn-123',
  query: 'SELECT * FROM users'
});

// Get connections
const connections = await api.getConnections();
```
