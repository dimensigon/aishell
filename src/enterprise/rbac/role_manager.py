"""
Role Manager

Hierarchical role-based access control system with:
- Role inheritance
- Dynamic role assignment
- Role hierarchies
- Custom role creation
"""

import json
import sqlite3
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path


class RoleType(Enum):
    """Built-in role types"""
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    TENANT_OWNER = "tenant_owner"
    DATABASE_ADMIN = "database_admin"
    DEVELOPER = "developer"
    ANALYST = "analyst"
    VIEWER = "viewer"
    CUSTOM = "custom"


@dataclass
class Role:
    """Role entity with permissions and hierarchy"""
    id: str
    name: str
    role_type: RoleType
    tenant_id: Optional[str]  # None for system-wide roles
    description: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    parent_roles: List[str] = field(default_factory=list)  # Role inheritance
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_system: bool = False  # System roles can't be deleted

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['role_type'] = self.role_type.value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Role':
        """Create from dictionary"""
        data['role_type'] = RoleType(data['role_type'])
        return cls(**data)

    def has_permission(self, permission: str) -> bool:
        """Check if role has a specific permission"""
        return permission in self.permissions


class RoleManager:
    """
    Manages roles and role hierarchies.

    Features:
    - CRUD operations for roles
    - Role inheritance and hierarchies
    - Permission aggregation
    - User-role assignment
    - Role templates
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        """
        Initialize role manager.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path or str(Path.home() / '.ai-shell' / 'rbac.db')
        self._init_database()
        self._init_system_roles()

    def _init_database(self) -> None:
        """Initialize RBAC database schema"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS roles (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    role_type TEXT NOT NULL,
                    tenant_id TEXT,
                    description TEXT,
                    permissions TEXT,
                    parent_roles TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_system INTEGER DEFAULT 0
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_roles (
                    user_id TEXT NOT NULL,
                    role_id TEXT NOT NULL,
                    tenant_id TEXT,
                    assigned_at TEXT NOT NULL,
                    assigned_by TEXT,
                    expires_at TEXT,
                    PRIMARY KEY (user_id, role_id, tenant_id),
                    FOREIGN KEY (role_id) REFERENCES roles(id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_roles_tenant
                ON roles(tenant_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_roles_user
                ON user_roles(user_id)
            """)

    def _init_system_roles(self) -> None:
        """Initialize built-in system roles"""
        system_roles = [
            {
                'id': 'role_super_admin',
                'name': 'Super Admin',
                'role_type': RoleType.SUPER_ADMIN,
                'description': 'Full system access',
                'permissions': ['*'],  # All permissions
                'is_system': True,
            },
            {
                'id': 'role_tenant_admin',
                'name': 'Tenant Admin',
                'role_type': RoleType.TENANT_ADMIN,
                'description': 'Full tenant access',
                'permissions': [
                    'tenant:*',
                    'database:*',
                    'user:*',
                    'role:*',
                ],
                'is_system': True,
            },
            {
                'id': 'role_database_admin',
                'name': 'Database Admin',
                'role_type': RoleType.DATABASE_ADMIN,
                'description': 'Database management',
                'permissions': [
                    'database:read',
                    'database:write',
                    'database:execute',
                    'database:schema',
                    'database:backup',
                ],
                'is_system': True,
            },
            {
                'id': 'role_developer',
                'name': 'Developer',
                'role_type': RoleType.DEVELOPER,
                'description': 'Development access',
                'permissions': [
                    'database:read',
                    'database:write',
                    'database:execute',
                    'query:*',
                ],
                'is_system': True,
            },
            {
                'id': 'role_analyst',
                'name': 'Analyst',
                'role_type': RoleType.ANALYST,
                'description': 'Read and query access',
                'permissions': [
                    'database:read',
                    'query:execute',
                    'query:history',
                ],
                'is_system': True,
            },
            {
                'id': 'role_viewer',
                'name': 'Viewer',
                'role_type': RoleType.VIEWER,
                'description': 'Read-only access',
                'permissions': [
                    'database:read',
                    'query:history',
                ],
                'is_system': True,
            },
        ]

        for role_data in system_roles:
            role_id = str(role_data['id'])
            if not self.get_role(role_id):
                self.create_role(
                    role_id=role_id,
                    name=str(role_data['name']),
                    role_type=RoleType(role_data['role_type']),
                    tenant_id=None,
                    description=str(role_data.get('description', '')),
                    permissions=list(role_data.get('permissions', [])),
                    is_system=bool(role_data.get('is_system', False)),
                )

    def create_role(
        self,
        name: str,
        role_type: RoleType,
        tenant_id: Optional[str] = None,
        description: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        parent_roles: Optional[List[str]] = None,
        role_id: Optional[str] = None,
        is_system: bool = False,
    ) -> Role:
        """
        Create a new role.

        Args:
            name: Role name
            role_type: Type of role
            tenant_id: Tenant ID (None for system-wide)
            description: Role description
            permissions: List of permissions
            parent_roles: Parent role IDs for inheritance
            role_id: Optional custom role ID
            is_system: If True, role is protected

        Returns:
            Created role
        """
        import uuid

        role_id = role_id or f"role_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()

        role = Role(
            id=role_id,
            name=name,
            role_type=role_type,
            tenant_id=tenant_id,
            description=description,
            permissions=permissions or [],
            parent_roles=parent_roles or [],
            created_at=now,
            updated_at=now,
            is_system=is_system,
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO roles (
                    id, name, role_type, tenant_id, description,
                    permissions, parent_roles, metadata,
                    created_at, updated_at, is_system
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                role.id,
                role.name,
                role.role_type.value,
                role.tenant_id,
                role.description,
                json.dumps(role.permissions),
                json.dumps(role.parent_roles),
                json.dumps(role.metadata),
                role.created_at,
                role.updated_at,
                1 if role.is_system else 0,
            ))

        return role

    def get_role(self, role_id: str) -> Optional[Role]:
        """Get role by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM roles WHERE id = ?",
                (role_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_role(dict(row))

    def update_role(
        self,
        role_id: str,
        **updates
    ) -> bool:
        """
        Update role properties.

        Args:
            role_id: Role ID
            **updates: Properties to update

        Returns:
            True if updated successfully
        """
        role = self.get_role(role_id)
        if not role or role.is_system:
            return False

        allowed_fields = {
            'name', 'description', 'permissions', 'parent_roles', 'metadata'
        }

        update_fields = []
        update_values = []

        for key, value in updates.items():
            if key in allowed_fields:
                if key in ['permissions', 'parent_roles', 'metadata']:
                    value = json.dumps(value)

                update_fields.append(f"{key} = ?")
                update_values.append(value)

        if not update_fields:
            return False

        update_fields.append("updated_at = ?")
        update_values.append(datetime.now().isoformat())
        update_values.append(role_id)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"UPDATE roles SET {', '.join(update_fields)} WHERE id = ?",
                update_values
            )

        return True

    def delete_role(self, role_id: str) -> bool:
        """Delete a role (system roles cannot be deleted)"""
        role = self.get_role(role_id)
        if not role or role.is_system:
            return False

        with sqlite3.connect(self.db_path) as conn:
            # Remove role assignments
            conn.execute("DELETE FROM user_roles WHERE role_id = ?", (role_id,))
            # Delete role
            conn.execute("DELETE FROM roles WHERE id = ?", (role_id,))

        return True

    def list_roles(
        self,
        tenant_id: Optional[str] = None,
        role_type: Optional[RoleType] = None,
        include_system: bool = True,
    ) -> List[Role]:
        """
        List roles with optional filtering.

        Args:
            tenant_id: Filter by tenant
            role_type: Filter by role type
            include_system: Include system roles

        Returns:
            List of roles
        """
        query = "SELECT * FROM roles WHERE 1=1"
        params = []

        if tenant_id is not None:
            query += " AND (tenant_id = ? OR tenant_id IS NULL)"
            params.append(tenant_id)

        if role_type:
            query += " AND role_type = ?"
            params.append(role_type.value)

        if not include_system:
            query += " AND is_system = 0"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_role(dict(row)) for row in rows]

    def assign_role(
        self,
        user_id: str,
        role_id: str,
        tenant_id: Optional[str] = None,
        assigned_by: Optional[str] = None,
        expires_at: Optional[str] = None,
    ) -> bool:
        """
        Assign a role to a user.

        Args:
            user_id: User ID
            role_id: Role ID
            tenant_id: Tenant context
            assigned_by: ID of user who assigned the role
            expires_at: Optional expiration timestamp

        Returns:
            True if assigned successfully
        """
        # Verify role exists
        role = self.get_role(role_id)
        if not role:
            return False

        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO user_roles (
                    user_id, role_id, tenant_id, assigned_at, assigned_by, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, role_id, tenant_id, now, assigned_by, expires_at))

        return True

    def revoke_role(
        self,
        user_id: str,
        role_id: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Revoke a role from a user"""
        with sqlite3.connect(self.db_path) as conn:
            if tenant_id:
                conn.execute("""
                    DELETE FROM user_roles
                    WHERE user_id = ? AND role_id = ? AND tenant_id = ?
                """, (user_id, role_id, tenant_id))
            else:
                conn.execute("""
                    DELETE FROM user_roles
                    WHERE user_id = ? AND role_id = ?
                """, (user_id, role_id))

        return True

    def get_user_roles(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
    ) -> List[Role]:
        """
        Get all roles assigned to a user.

        Args:
            user_id: User ID
            tenant_id: Optional tenant context

        Returns:
            List of roles
        """
        query = """
            SELECT r.* FROM roles r
            JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = ?
        """
        params = [user_id]

        if tenant_id:
            query += " AND (ur.tenant_id = ? OR ur.tenant_id IS NULL)"
            params.append(tenant_id)

        # Filter expired roles
        query += " AND (ur.expires_at IS NULL OR ur.expires_at > ?)"
        params.append(datetime.now().isoformat())

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_role(dict(row)) for row in rows]

    def get_effective_permissions(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
    ) -> Set[str]:
        """
        Get all effective permissions for a user (including inherited).

        Args:
            user_id: User ID
            tenant_id: Optional tenant context

        Returns:
            Set of permission strings
        """
        roles = self.get_user_roles(user_id, tenant_id)
        permissions = set()

        for role in roles:
            # Add direct permissions
            permissions.update(role.permissions)

            # Add inherited permissions
            for parent_role_id in role.parent_roles:
                parent_role = self.get_role(parent_role_id)
                if parent_role:
                    permissions.update(parent_role.permissions)

        return permissions

    def _row_to_role(self, row: Dict[str, Any]) -> Role:
        """Convert database row to Role object"""
        return Role(
            id=row['id'],
            name=row['name'],
            role_type=RoleType(row['role_type']),
            tenant_id=row['tenant_id'],
            description=row['description'],
            permissions=json.loads(row['permissions']) if row['permissions'] else [],
            parent_roles=json.loads(row['parent_roles']) if row['parent_roles'] else [],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            is_system=bool(row['is_system']),
        )
