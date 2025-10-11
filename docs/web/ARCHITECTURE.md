# AI-Shell Web UI Architecture

## Overview

The AI-Shell Web UI is a modern, full-stack web application built with React, TypeScript, and FastAPI. It provides a comprehensive interface for managing multiple database connections, executing queries, visualizing data, and administering users.

## Technology Stack

### Frontend

- **React 18**: UI framework with hooks
- **TypeScript**: Type-safe JavaScript
- **Vite**: Build tool and dev server
- **Material-UI (MUI)**: Component library
- **React Router**: Client-side routing
- **TanStack Query**: Data fetching and caching
- **Zustand**: State management
- **Monaco Editor**: Code editor
- **Recharts**: Data visualization
- **Socket.IO Client**: WebSocket communication

### Backend

- **FastAPI**: Python web framework
- **Pydantic**: Data validation
- **JWT**: Authentication
- **WebSocket**: Real-time updates
- **Uvicorn**: ASGI server

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Pages     │  │  Components  │  │    Hooks     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                           │                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Services   │  │    Store     │  │    Types     │      │
│  │   (API)      │  │  (Zustand)   │  │ (TypeScript) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ HTTP/REST & WebSocket
                           │
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Routers    │  │  Middleware  │  │   Schemas    │      │
│  │ (Endpoints)  │  │   (Auth)     │  │  (Pydantic)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                           │                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  WebSocket   │  │   Database   │  │    Cache     │      │
│  │   Handler    │  │   Clients    │  │    Layer     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                           │
                           │
┌─────────────────────────────────────────────────────────────┐
│                     Database Layer                           │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │PostgreSQL│  │  MySQL   │  │ MongoDB  │  │  Redis   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
/home/claude/AIShell/
├── web/                          # Frontend application
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── auth/            # Authentication components
│   │   │   ├── database/        # Database management
│   │   │   ├── query/           # Query editor & builder
│   │   │   ├── visualizations/  # Charts and graphs
│   │   │   ├── dashboard/       # Dashboard widgets
│   │   │   ├── admin/           # Admin panels
│   │   │   └── common/          # Shared components
│   │   ├── pages/               # Page components
│   │   ├── services/            # API services
│   │   │   ├── api.ts          # REST API client
│   │   │   └── websocket.ts    # WebSocket client
│   │   ├── store/               # State management
│   │   │   ├── authStore.ts    # Authentication state
│   │   │   └── themeStore.ts   # Theme state
│   │   ├── types/               # TypeScript types
│   │   ├── hooks/               # Custom React hooks
│   │   └── utils/               # Utility functions
│   ├── tests/                   # Test files
│   │   ├── unit/               # Unit tests
│   │   ├── integration/        # Integration tests
│   │   └── e2e/                # End-to-end tests
│   ├── public/                  # Static assets
│   ├── index.html              # HTML template
│   ├── vite.config.ts          # Vite configuration
│   └── package.json            # Dependencies
│
└── src/api/                     # Backend application
    ├── web_server.py           # Main FastAPI server
    ├── routers/                # API route handlers
    ├── middleware/             # Custom middleware
    ├── schemas/                # Pydantic models
    └── websocket/              # WebSocket handlers
```

## Component Architecture

### Authentication Flow

```
┌──────────┐         ┌──────────┐         ┌──────────┐
│  Login   │────────▶│   API    │────────▶│  Backend │
│   Form   │◀────────│ Service  │◀────────│  /auth   │
└──────────┘         └──────────┘         └──────────┘
     │                     │
     └─────────────────────┘
              │
         ┌────▼────┐
         │  Auth   │
         │  Store  │
         │(Zustand)│
         └─────────┘
```

### Query Execution Flow

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│    Query     │──────▶│   Execute    │──────▶│   Backend    │
│   Editor     │       │   Mutation   │       │   /queries   │
└──────────────┘       └──────────────┘       └──────────────┘
                              │                       │
                              │                       ▼
                              │              ┌──────────────┐
                              │              │   Database   │
                              │              │   Clients    │
                              │              └──────────────┘
                              │                       │
                       ┌──────▼───────┐              │
                       │   Results    │◀─────────────┘
                       │   Viewer     │
                       └──────────────┘
```

### Real-time Updates Flow

```
┌──────────────┐                   ┌──────────────┐
│  WebSocket   │◀─────────────────▶│   Backend    │
│   Client     │                   │  WebSocket   │
└──────────────┘                   └──────────────┘
       │                                  │
       │  Subscribe to events             │
       ├─────────────────────────────────▶│
       │                                  │
       │  Metric updates                  │
       │◀─────────────────────────────────│
       │                                  │
       ▼                                  │
┌──────────────┐                          │
│ Performance  │                          │
│  Dashboard   │                          │
└──────────────┘                          │
```

## State Management

### Zustand Stores

**AuthStore**: Manages user authentication state
- User information
- JWT tokens
- Login/logout functions
- Token refresh

**ThemeStore**: Manages UI theme
- Light/dark mode
- Theme preferences

### TanStack Query

**Query Keys**:
- `['connections']`: Database connections
- `['queryHistory', connectionId]`: Query history
- `['users', page, pageSize]`: User list
- `['auditLogs', filters]`: Audit logs
- `['metrics', connectionId]`: Performance metrics

## API Client Architecture

### Axios Interceptors

**Request Interceptor**:
- Attach JWT token to headers
- Add correlation IDs
- Log requests (dev mode)

**Response Interceptor**:
- Handle token refresh
- Global error handling
- Response transformation

### Error Handling

```typescript
try {
  const result = await api.executeQuery(request);
  // Success handling
} catch (error) {
  if (error.response?.status === 401) {
    // Redirect to login
  } else if (error.response?.status === 403) {
    // Show permission error
  } else {
    // Generic error toast
  }
}
```

## Security Features

### Authentication

- JWT-based authentication
- Refresh token rotation
- 2FA support (TOTP)
- Password hashing (SHA-256)

### Authorization

- Role-based access control (RBAC)
- Admin, User, Viewer roles
- Route guards
- API endpoint protection

### Security Best Practices

- HTTPS enforcement
- CORS configuration
- SQL injection prevention
- XSS protection
- CSRF tokens
- Rate limiting
- Input validation

## Performance Optimization

### Frontend

1. **Code Splitting**: Route-based lazy loading
2. **Memoization**: React.memo for expensive components
3. **Virtual Scrolling**: Large table rendering
4. **Query Caching**: TanStack Query cache
5. **Image Optimization**: Lazy loading images
6. **Bundle Optimization**: Vite tree-shaking

### Backend

1. **Connection Pooling**: Database connection reuse
2. **Query Optimization**: Indexed queries
3. **Caching**: Redis for frequent queries
4. **Async Operations**: Non-blocking I/O
5. **Pagination**: Limit result sets
6. **Compression**: Gzip responses

## Deployment Architecture

### Development

```
Vite Dev Server (Port 3000)
         │
         ├─ Proxy /api → FastAPI (Port 8000)
         └─ Proxy /ws → WebSocket
```

### Production

```
┌─────────────────┐
│    Nginx        │
│  Reverse Proxy  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│ React │ │FastAPI│
│ Build │ │+Uvicorn│
│(Static)│ │(ASGI) │
└───────┘ └───────┘
```

### Docker Compose

```yaml
services:
  frontend:
    build: ./web
    ports:
      - "3000:80"

  backend:
    build: ./src/api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL
      - SECRET_KEY

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD
```

## Monitoring & Observability

### Metrics

- API response times
- Query execution times
- Connection pool usage
- Error rates
- User activity

### Logging

- Structured logging (JSON)
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Correlation IDs
- User action tracking

### Health Checks

- `/api/health`: API health status
- Database connectivity
- Cache connectivity
- Disk space monitoring

## Testing Strategy

### Unit Tests

- Component testing with Vitest
- Service testing with mocks
- Store testing with Zustand
- 90%+ coverage target

### Integration Tests

- API endpoint testing
- Database integration
- WebSocket communication
- Authentication flows

### E2E Tests

- User workflows
- Critical paths
- Cross-browser testing
- Performance testing

## Scalability Considerations

### Horizontal Scaling

- Stateless API design
- Load balancer ready
- Session store in Redis
- Database read replicas

### Vertical Scaling

- Efficient queries
- Connection pooling
- Memory optimization
- CPU optimization

### Caching Strategy

- Browser cache (static assets)
- API response cache (Redis)
- Query result cache
- CDN for assets

## Future Enhancements

1. **Advanced Query Builder**: Drag-and-drop visual builder
2. **Collaborative Editing**: Real-time multi-user editing
3. **AI-Powered Suggestions**: Query optimization hints
4. **Advanced Visualizations**: Custom chart builders
5. **Mobile App**: React Native mobile app
6. **Data Pipelines**: ETL workflow builder
7. **Scheduled Queries**: Cron-based query execution
8. **Advanced Analytics**: Business intelligence features
