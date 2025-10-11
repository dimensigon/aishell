# AI-Shell Web UI - Quick Start Guide

## 5-Minute Setup

### Option 1: Automated Script

```bash
cd /home/claude/AIShell
./scripts/start-web-ui.sh
```

This script will:
1. Check prerequisites (Node.js, Python)
2. Install dependencies if needed
3. Start both backend and frontend servers
4. Open your default browser

### Option 2: Manual Setup

#### Step 1: Install Frontend Dependencies

```bash
cd /home/claude/AIShell/web
npm install
```

#### Step 2: Install Backend Dependencies

```bash
cd /home/claude/AIShell
pip install -r requirements-web.txt
```

#### Step 3: Start Backend Server

Open a new terminal:

```bash
cd /home/claude/AIShell
python src/api/web_server.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### Step 4: Start Frontend Server

Open another terminal:

```bash
cd /home/claude/AIShell/web
npm run dev
```

You should see:
```
  VITE v5.0.11  ready in 1234 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

#### Step 5: Open Browser

Navigate to: **http://localhost:3000**

## First Login

### Register New Account

1. Click "Register" on the login page
2. Fill in the form:
   - Username: `admin`
   - Email: `admin@example.com`
   - Password: `password123` (minimum 8 characters)
3. Click "Register"
4. You'll be redirected to the login page

### Login

1. Enter your credentials
2. Click "Login"
3. You'll be redirected to the dashboard

## Quick Tour

### 1. Dashboard (Home)

- View system performance metrics
- Monitor active connections
- See recent activity

### 2. Connections

1. Click "Connections" in the sidebar
2. Click "New Connection"
3. Fill in database details:
   - Name: `Test DB`
   - Type: `PostgreSQL`
   - Host: `localhost`
   - Port: `5432`
   - Database: `testdb`
   - Username: `testuser`
   - Password: `password`
4. Click "Save"
5. Click "Test" to verify connection

### 3. Query Editor

1. Click "Query Editor" in the sidebar
2. Select a connection from the dropdown
3. Write a SQL query:
   ```sql
   SELECT * FROM users LIMIT 10;
   ```
4. Click "Execute" (or press Ctrl+Enter)
5. View results in the Results tab

### 4. Visual Query Builder

1. Click "Visual Query" in the sidebar
2. Add tables by clicking them
3. Add joins and conditions
4. Click "Generate SQL"
5. Click "Execute Query"

### 5. Data Visualization

1. Execute a query with numeric data
2. In the Results tab, click the chart icon
3. Select chart type (bar, line, pie, etc.)
4. Configure X and Y axes
5. View interactive chart

### 6. User Management (Admin Only)

1. Click "Users" in the sidebar
2. View all registered users
3. Edit user roles or delete users
4. View user activity

### 7. Audit Logs

1. Click "Audit Logs" in the sidebar
2. View all system activities
3. Filter by user or action
4. Expand rows for details

### 8. Settings

1. Click "Settings" in the sidebar
2. Update profile information
3. Change password
4. Enable 2FA
5. Toggle dark mode
6. Configure preferences

## Common Tasks

### Execute a Query

```sql
-- Simple SELECT
SELECT * FROM users LIMIT 10;

-- JOIN query
SELECT u.name, o.total
FROM users u
JOIN orders o ON u.id = o.user_id;

-- Aggregate query
SELECT category, COUNT(*) as count
FROM products
GROUP BY category;
```

### Export Query Results

1. Execute a query
2. Click the download icon
3. Results will be downloaded as CSV

### Create Dashboard Widget

1. Go to Dashboard
2. Click "Add Widget"
3. Select widget type
4. Configure data source
5. Click "Save"

### Enable Dark Mode

1. Click the moon icon in the top toolbar
2. Theme will switch to dark mode
3. Preference is saved automatically

## Keyboard Shortcuts

### Query Editor

- `Ctrl+Enter` - Execute query
- `Ctrl+S` - Save query
- `Ctrl+/` - Toggle comment
- `Ctrl+Space` - Autocomplete
- `Ctrl+F` - Find
- `Ctrl+H` - Replace

### General

- `Ctrl+K` - Command palette
- `/` - Focus search
- `Esc` - Close dialog

## Troubleshooting

### Backend not starting

**Error**: `Port 8000 already in use`

**Solution**:
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Frontend not starting

**Error**: `Port 3000 already in use`

**Solution**:
```bash
# Find and kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Cannot connect to database

**Check**:
1. Database server is running
2. Connection details are correct
3. User has necessary permissions
4. Firewall allows connection

### Login not working

**Check**:
1. Backend server is running
2. No CORS errors in browser console
3. Credentials are correct
4. Try clearing browser cache

### WebSocket not connecting

**Check**:
1. Backend WebSocket is running
2. No proxy blocking WebSocket
3. Browser supports WebSocket
4. Check browser console for errors

## API Testing

### Using curl

```bash
# Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"password123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"password123"}'

# Get connections (with token)
curl -X GET http://localhost:8000/api/connections \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Using Postman

1. Import API collection from `docs/web/API_DOCUMENTATION.md`
2. Set base URL: `http://localhost:8000/api`
3. Test endpoints

## Development Mode

### Hot Reload

Both frontend and backend support hot reload:

- **Frontend**: Changes to React components auto-reload
- **Backend**: Restart server manually for changes

### Debug Mode

**Frontend**:
```bash
# Open browser dev tools
F12 or Right-click > Inspect

# React DevTools extension recommended
```

**Backend**:
```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use IDE debugger
```

### View Logs

**Frontend**:
- Browser console (F12)
- Network tab for API calls

**Backend**:
- Terminal output
- Check `logs/` directory (if configured)

## Production Deployment

### Build Frontend

```bash
cd web
npm run build
```

Output in `web/dist/`

### Run Backend in Production

```bash
pip install gunicorn
gunicorn src.api.web_server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Serve with Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /path/to/web/dist;
        try_files $uri /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

## Next Steps

1. ✅ Complete quick start
2. 📚 Read [Architecture Documentation](ARCHITECTURE.md)
3. 🔧 Review [API Documentation](API_DOCUMENTATION.md)
4. 🚀 Deploy to production
5. 📊 Set up monitoring
6. 🔒 Configure security
7. 📈 Optimize performance

## Support

- **Documentation**: `/docs/web/`
- **Issues**: Report on GitHub
- **Email**: support@example.com

## Useful Commands

```bash
# Check versions
node --version
python --version
npm --version

# Clean install
rm -rf web/node_modules web/package-lock.json
cd web && npm install

# Run tests
cd web && npm test

# Build production
cd web && npm run build

# Check backend health
curl http://localhost:8000/api/health

# View frontend bundle size
cd web && npm run build -- --analyze
```

---

**Ready to build something amazing with AI-Shell Web UI!** 🚀
