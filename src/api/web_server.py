"""
FastAPI Web Server for AI-Shell v2.0
Provides REST API endpoints for web UI
"""

from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import jwt
import secrets
import hashlib
import asyncio
import logging
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

app = FastAPI(
    title="AI-Shell API",
    version="2.0.0",
    description="REST API for AI-Shell Web UI"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# ============================================================================
# Models
# ============================================================================

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

class DatabaseType(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    REDIS = "redis"
    SQLITE = "sqlite"

class ConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

# Request Models
class LoginRequest(BaseModel):
    username: str
    password: str
    twoFactorCode: Optional[str] = None

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class DatabaseConnectionCreate(BaseModel):
    name: str
    type: DatabaseType
    host: str
    port: int
    database: str
    username: str
    password: str
    ssl: Optional[bool] = False

class QueryRequest(BaseModel):
    connectionId: str
    query: str
    parameters: Optional[Dict[str, Any]] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None

# Response Models
class User(BaseModel):
    id: str
    username: str
    email: str
    role: UserRole
    twoFactorEnabled: bool
    createdAt: str
    lastLogin: Optional[str] = None

class AuthTokens(BaseModel):
    accessToken: str
    refreshToken: str
    expiresIn: int
    user: User

class DatabaseConnection(BaseModel):
    id: str
    name: str
    type: DatabaseType
    host: str
    port: int
    database: str
    username: str
    ssl: bool
    status: ConnectionStatus
    createdAt: str
    lastUsed: Optional[str] = None

class QueryResult(BaseModel):
    id: str
    query: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    rowCount: int
    executionTime: int
    timestamp: str

class PerformanceMetric(BaseModel):
    id: str
    connectionId: str
    metric: str
    value: float
    timestamp: str

class AuditLog(BaseModel):
    id: str
    userId: str
    username: str
    action: str
    resource: str
    details: Dict[str, Any]
    timestamp: str
    ipAddress: Optional[str] = None

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    pageSize: int
    totalPages: int

# ============================================================================
# In-Memory Storage (Replace with actual database in production)
# ============================================================================

users_db = {}
connections_db = {}
queries_db = {}
audit_logs_db = []
websocket_connections = []

# ============================================================================
# Authentication Utilities
# ============================================================================

def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Get current user from JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None or user_id not in users_db:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return users_db[user_id]
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def create_audit_log(user_id: str, action: str, resource: str, details: Dict[str, Any]):
    """Create an audit log entry"""
    user = users_db.get(user_id, {})
    log = {
        "id": secrets.token_urlsafe(16),
        "userId": user_id,
        "username": user.get("username", "unknown"),
        "action": action,
        "resource": resource,
        "details": details,
        "timestamp": datetime.utcnow().isoformat(),
        "ipAddress": None
    }
    audit_logs_db.append(log)
    return log

# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/api/auth/register", response_model=ApiResponse)
async def register(request: RegisterRequest):
    """Register a new user"""
    try:
        # Check if user exists
        if any(u["username"] == request.username for u in users_db.values()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )

        # Create user
        user_id = secrets.token_urlsafe(16)
        user = {
            "id": user_id,
            "username": request.username,
            "email": request.email,
            "password": hash_password(request.password),
            "role": UserRole.USER.value,
            "twoFactorEnabled": False,
            "createdAt": datetime.utcnow().isoformat(),
            "lastLogin": None
        }
        users_db[user_id] = user

        # Create audit log
        create_audit_log(user_id, "register", "user", {"username": request.username})

        return ApiResponse(
            success=True,
            message="User registered successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@app.post("/api/auth/login", response_model=ApiResponse)
async def login(request: LoginRequest):
    """Login user and return JWT tokens"""
    try:
        # Find user
        user = None
        for u in users_db.values():
            if u["username"] == request.username:
                user = u
                break

        if not user or not verify_password(request.password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Check 2FA
        if user["twoFactorEnabled"] and not request.twoFactorCode:
            return ApiResponse(
                success=False,
                error="2FA code required",
                data={"requires2FA": True}
            )

        # Create tokens
        access_token = create_access_token(
            data={"sub": user["id"]},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = create_access_token(
            data={"sub": user["id"]},
            expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )

        # Update last login
        user["lastLogin"] = datetime.utcnow().isoformat()

        # Create audit log
        create_audit_log(user["id"], "login", "user", {"username": user["username"]})

        # Return response
        user_data = {k: v for k, v in user.items() if k != "password"}
        return ApiResponse(
            success=True,
            data={
                "accessToken": access_token,
                "refreshToken": refresh_token,
                "expiresIn": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": user_data
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@app.post("/api/auth/logout")
async def logout(current_user: Dict = Depends(get_current_user)):
    """Logout user"""
    create_audit_log(current_user["id"], "logout", "user", {})
    return ApiResponse(success=True, message="Logged out successfully")

@app.get("/api/auth/me", response_model=ApiResponse)
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """Get current user information"""
    user_data = {k: v for k, v in current_user.items() if k != "password"}
    return ApiResponse(success=True, data=user_data)

# ============================================================================
# Database Connection Endpoints
# ============================================================================

@app.get("/api/connections", response_model=ApiResponse)
async def get_connections(current_user: Dict = Depends(get_current_user)):
    """Get all database connections"""
    connections = list(connections_db.values())
    return ApiResponse(success=True, data=connections)

@app.post("/api/connections", response_model=ApiResponse)
async def create_connection(
    connection: DatabaseConnectionCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Create a new database connection"""
    conn_id = secrets.token_urlsafe(16)
    new_conn = {
        "id": conn_id,
        **connection.dict(exclude={"password"}),
        "status": ConnectionStatus.DISCONNECTED.value,
        "createdAt": datetime.utcnow().isoformat(),
        "lastUsed": None
    }
    connections_db[conn_id] = new_conn

    create_audit_log(
        current_user["id"],
        "create",
        "connection",
        {"connectionId": conn_id, "name": connection.name}
    )

    return ApiResponse(success=True, data=new_conn)

@app.put("/api/connections/{connection_id}", response_model=ApiResponse)
async def update_connection(
    connection_id: str,
    connection: DatabaseConnectionCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Update a database connection"""
    if connection_id not in connections_db:
        raise HTTPException(status_code=404, detail="Connection not found")

    connections_db[connection_id].update({
        **connection.dict(exclude={"password"}),
    })

    create_audit_log(
        current_user["id"],
        "update",
        "connection",
        {"connectionId": connection_id}
    )

    return ApiResponse(success=True, data=connections_db[connection_id])

@app.delete("/api/connections/{connection_id}", response_model=ApiResponse)
async def delete_connection(
    connection_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Delete a database connection"""
    if connection_id not in connections_db:
        raise HTTPException(status_code=404, detail="Connection not found")

    del connections_db[connection_id]

    create_audit_log(
        current_user["id"],
        "delete",
        "connection",
        {"connectionId": connection_id}
    )

    return ApiResponse(success=True, message="Connection deleted")

@app.post("/api/connections/{connection_id}/test", response_model=ApiResponse)
async def test_connection(
    connection_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Test a database connection"""
    if connection_id not in connections_db:
        raise HTTPException(status_code=404, detail="Connection not found")

    # Simulate connection test
    connections_db[connection_id]["status"] = ConnectionStatus.CONNECTED.value

    return ApiResponse(success=True, data={"status": "connected"})

# ============================================================================
# Query Execution Endpoints
# ============================================================================

@app.post("/api/queries/execute", response_model=ApiResponse)
async def execute_query(
    request: QueryRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Execute a database query"""
    if request.connectionId not in connections_db:
        raise HTTPException(status_code=404, detail="Connection not found")

    # Simulate query execution
    query_id = secrets.token_urlsafe(16)
    result = {
        "id": query_id,
        "query": request.query,
        "columns": ["id", "name", "email", "created_at"],
        "rows": [
            {"id": 1, "name": "John Doe", "email": "john@example.com", "created_at": "2024-01-01"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "created_at": "2024-01-02"},
        ],
        "rowCount": 2,
        "executionTime": 45,
        "timestamp": datetime.utcnow().isoformat()
    }

    queries_db[query_id] = result
    connections_db[request.connectionId]["lastUsed"] = datetime.utcnow().isoformat()

    create_audit_log(
        current_user["id"],
        "execute",
        "query",
        {"queryId": query_id, "connectionId": request.connectionId}
    )

    return ApiResponse(success=True, data=result)

@app.get("/api/queries/history", response_model=ApiResponse)
async def get_query_history(
    page: int = 1,
    pageSize: int = 20,
    connectionId: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Get query execution history"""
    queries = list(queries_db.values())

    if connectionId:
        # Filter by connection if needed
        pass

    total = len(queries)
    start = (page - 1) * pageSize
    end = start + pageSize
    items = queries[start:end]

    return ApiResponse(
        success=True,
        data={
            "items": items,
            "total": total,
            "page": page,
            "pageSize": pageSize,
            "totalPages": (total + pageSize - 1) // pageSize
        }
    )

# ============================================================================
# User Management Endpoints
# ============================================================================

@app.get("/api/users", response_model=ApiResponse)
async def get_users(
    page: int = 1,
    pageSize: int = 20,
    current_user: Dict = Depends(get_current_user)
):
    """Get all users (admin only)"""
    if current_user["role"] != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Admin access required")

    users = [{k: v for k, v in u.items() if k != "password"} for u in users_db.values()]
    total = len(users)
    start = (page - 1) * pageSize
    end = start + pageSize
    items = users[start:end]

    return ApiResponse(
        success=True,
        data={
            "items": items,
            "total": total,
            "page": page,
            "pageSize": pageSize,
            "totalPages": (total + pageSize - 1) // pageSize
        }
    )

# ============================================================================
# Audit Log Endpoints
# ============================================================================

@app.get("/api/audit", response_model=ApiResponse)
async def get_audit_logs(
    page: int = 1,
    pageSize: int = 20,
    userId: Optional[str] = None,
    action: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Get audit logs"""
    logs = audit_logs_db.copy()

    if userId:
        logs = [log for log in logs if log["userId"] == userId]
    if action:
        logs = [log for log in logs if log["action"] == action]

    logs.sort(key=lambda x: x["timestamp"], reverse=True)

    total = len(logs)
    start = (page - 1) * pageSize
    end = start + pageSize
    items = logs[start:end]

    return ApiResponse(
        success=True,
        data={
            "items": items,
            "total": total,
            "page": page,
            "pageSize": pageSize,
            "totalPages": (total + pageSize - 1) // pageSize
        }
    )

# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    websocket_connections.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages
            logger.info(f"Received WebSocket message: {data}")

            # Broadcast to all connections
            for conn in websocket_connections:
                try:
                    await conn.send_text(f"Echo: {data}")
                except:
                    pass
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
        logger.info("WebSocket disconnected")

# ============================================================================
# Health Check
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
