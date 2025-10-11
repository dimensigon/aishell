# AI-Shell Web UI Installation Guide

## Prerequisites

### Required Software

- **Node.js**: v18+ ([Download](https://nodejs.org/))
- **Python**: 3.9+ ([Download](https://python.org/))
- **npm** or **yarn**: Package manager (comes with Node.js)
- **pip**: Python package manager (comes with Python)

### Optional

- **Docker**: For containerized deployment
- **PostgreSQL**: For persistent storage (optional, uses in-memory by default)
- **Redis**: For caching (optional)

## Quick Start

### 1. Clone Repository

```bash
cd /home/claude/AIShell
```

### 2. Install Frontend Dependencies

```bash
cd web
npm install
```

### 3. Install Backend Dependencies

```bash
cd ../
pip install fastapi uvicorn pydantic python-jose[cryptography] python-multipart websockets
```

### 4. Start Development Servers

#### Terminal 1 - Backend Server

```bash
cd /home/claude/AIShell
python src/api/web_server.py
```

The backend will start on **http://localhost:8000**

#### Terminal 2 - Frontend Dev Server

```bash
cd /home/claude/AIShell/web
npm run dev
```

The frontend will start on **http://localhost:3000**

### 5. Access the Application

Open your browser and navigate to:

```
http://localhost:3000
```

## Detailed Installation

### Frontend Setup

1. **Navigate to web directory**:
   ```bash
   cd /home/claude/AIShell/web
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Environment Configuration** (optional):
   Create `.env` file:
   ```env
   VITE_API_URL=http://localhost:8000
   VITE_WS_URL=ws://localhost:8000
   ```

4. **Development Server**:
   ```bash
   npm run dev
   ```

5. **Build for Production**:
   ```bash
   npm run build
   ```

6. **Preview Production Build**:
   ```bash
   npm run preview
   ```

### Backend Setup

1. **Create Virtual Environment** (recommended):
   ```bash
   cd /home/claude/AIShell
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   Or manually install:
   ```bash
   pip install fastapi uvicorn pydantic python-jose[cryptography] \
               python-multipart websockets pyjwt passlib bcrypt
   ```

3. **Environment Configuration**:
   Create `.env` file in project root:
   ```env
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=postgresql://user:password@localhost:5432/aishell
   REDIS_URL=redis://localhost:6379/0
   ```

4. **Run Development Server**:
   ```bash
   python src/api/web_server.py
   ```

   Or with uvicorn:
   ```bash
   uvicorn src.api.web_server:app --reload --host 0.0.0.0 --port 8000
   ```

## Docker Installation

### Using Docker Compose

1. **Create docker-compose.yml**:
   ```yaml
   version: '3.8'

   services:
     frontend:
       build:
         context: ./web
         dockerfile: Dockerfile
       ports:
         - "3000:80"
       depends_on:
         - backend

     backend:
       build:
         context: .
         dockerfile: Dockerfile.backend
       ports:
         - "8000:8000"
       environment:
         - SECRET_KEY=${SECRET_KEY}
         - DATABASE_URL=${DATABASE_URL}
       depends_on:
         - postgres

     postgres:
       image: postgres:15
       environment:
         - POSTGRES_USER=aishell
         - POSTGRES_PASSWORD=secret
         - POSTGRES_DB=aishell
       ports:
         - "5432:5432"
       volumes:
         - postgres_data:/var/lib/postgresql/data

   volumes:
     postgres_data:
   ```

2. **Create Frontend Dockerfile** (`web/Dockerfile`):
   ```dockerfile
   FROM node:18-alpine AS builder

   WORKDIR /app
   COPY package*.json ./
   RUN npm ci

   COPY . .
   RUN npm run build

   FROM nginx:alpine
   COPY --from=builder /app/dist /usr/share/nginx/html
   COPY nginx.conf /etc/nginx/conf.d/default.conf

   EXPOSE 80
   CMD ["nginx", "-g", "daemon off;"]
   ```

3. **Create Backend Dockerfile** (`Dockerfile.backend`):
   ```dockerfile
   FROM python:3.9-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY src/ ./src/

   EXPOSE 8000

   CMD ["uvicorn", "src.api.web_server:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

4. **Start Services**:
   ```bash
   docker-compose up -d
   ```

## Configuration

### Frontend Configuration

**vite.config.ts**:
```typescript
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
});
```

### Backend Configuration

**web_server.py**:
```python
# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
```

## Database Setup

### PostgreSQL (Recommended for Production)

1. **Install PostgreSQL**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib

   # macOS
   brew install postgresql
   ```

2. **Create Database**:
   ```bash
   sudo -u postgres psql
   CREATE DATABASE aishell;
   CREATE USER aishell WITH PASSWORD 'your-password';
   GRANT ALL PRIVILEGES ON DATABASE aishell TO aishell;
   ```

3. **Update Backend Configuration**:
   ```env
   DATABASE_URL=postgresql://aishell:your-password@localhost:5432/aishell
   ```

### SQLite (Development)

For development, SQLite is used by default with in-memory storage. No additional setup required.

## Testing

### Frontend Tests

```bash
cd web

# Run tests
npm test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

### Backend Tests

```bash
cd /home/claude/AIShell

# Run tests
pytest

# Run with coverage
pytest --cov=src/api --cov-report=html
```

## Troubleshooting

### Port Already in Use

If ports 3000 or 8000 are in use:

```bash
# Find process using port
lsof -i :3000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Module Not Found Errors

**Frontend**:
```bash
cd web
rm -rf node_modules package-lock.json
npm install
```

**Backend**:
```bash
pip install --upgrade -r requirements.txt
```

### CORS Errors

Ensure backend CORS configuration includes your frontend URL:
```python
allow_origins=["http://localhost:3000"]
```

### WebSocket Connection Failed

1. Check backend is running on port 8000
2. Verify WebSocket endpoint is accessible
3. Check browser console for detailed errors

### Database Connection Errors

1. Verify database is running
2. Check connection string format
3. Ensure database user has correct permissions

## Production Deployment

### Build Frontend

```bash
cd web
npm run build
```

Output will be in `web/dist/`

### Production Server Setup

1. **Nginx Configuration**:
   ```nginx
   server {
       listen 80;
       server_name example.com;

       location / {
           root /var/www/aishell/dist;
           try_files $uri $uri/ /index.html;
       }

       location /api {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       location /ws {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

2. **Run Backend with Gunicorn**:
   ```bash
   pip install gunicorn
   gunicorn src.api.web_server:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

3. **Process Manager (Systemd)**:
   ```ini
   [Unit]
   Description=AI-Shell Backend
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/var/www/aishell
   ExecStart=/usr/bin/gunicorn src.api.web_server:app -w 4 -k uvicorn.workers.UvicornWorker

   [Install]
   WantedBy=multi-user.target
   ```

## Performance Optimization

### Frontend

1. **Enable compression** in Nginx
2. **Use CDN** for static assets
3. **Implement service worker** for caching
4. **Lazy load components** and routes

### Backend

1. **Use Redis** for caching
2. **Enable connection pooling**
3. **Implement rate limiting**
4. **Use async database drivers**

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use HTTPS in production
- [ ] Enable CORS only for trusted origins
- [ ] Implement rate limiting
- [ ] Regular security updates
- [ ] Enable 2FA for admin accounts
- [ ] Use strong database passwords
- [ ] Regular backups

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-repo/issues
- Documentation: /docs/web/
- Email: support@example.com

## Version Information

- **Frontend**: React 18.2+ with TypeScript 5.3+
- **Backend**: Python 3.9+ with FastAPI
- **Node.js**: v18+
- **npm**: v9+
