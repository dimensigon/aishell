"""
Tenant Management System

Provides complete multi-tenancy support with:
- Tenant lifecycle management
- Isolation and resource management
- Tenant configuration and metadata
- Hierarchical tenant structures
"""

import uuid
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import sqlite3


class TenantStatus(Enum):
    """Tenant status states"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"
    TRIAL = "trial"
    PENDING = "pending"


class TenantTier(Enum):
    """Tenant subscription tiers"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


@dataclass
class Tenant:
    """Tenant entity with full configuration"""
    id: str
    name: str
    slug: str
    status: TenantStatus
    tier: TenantTier
    owner_id: str
    created_at: str
    updated_at: str
    parent_tenant_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    features: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    contact_email: Optional[str] = None
    billing_email: Optional[str] = None
    max_users: int = 10
    max_databases: int = 5
    trial_ends_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['status'] = self.status.value
        result['tier'] = self.tier.value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tenant':
        """Create from dictionary"""
        data['status'] = TenantStatus(data['status'])
        data['tier'] = TenantTier(data['tier'])
        return cls(**data)

    def is_active(self) -> bool:
        """Check if tenant is active"""
        if self.status != TenantStatus.ACTIVE and self.status != TenantStatus.TRIAL:
            return False

        # Check trial expiration
        if self.status == TenantStatus.TRIAL and self.trial_ends_at:
            trial_end = datetime.fromisoformat(self.trial_ends_at)
            if datetime.now() > trial_end:
                return False

        return True

    def has_feature(self, feature: str) -> bool:
        """Check if tenant has a specific feature enabled"""
        return feature in self.features


class TenantManager:
    """
    Manages tenant lifecycle and configuration.

    Features:
    - CRUD operations for tenants
    - Hierarchical tenant structures
    - Tenant isolation and validation
    - Feature flag management
    - Usage tracking and quotas
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        """
        Initialize tenant manager.

        Args:
            db_path: Path to SQLite database for tenant storage
        """
        self.db_path = db_path or str(Path.home() / '.ai-shell' / 'tenants.db')
        self._init_database()

    def _init_database(self) -> None:
        """Initialize tenant database schema"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tenants (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    slug TEXT UNIQUE NOT NULL,
                    status TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    parent_tenant_id TEXT,
                    contact_email TEXT,
                    billing_email TEXT,
                    max_users INTEGER DEFAULT 10,
                    max_databases INTEGER DEFAULT 5,
                    trial_ends_at TEXT,
                    metadata TEXT,
                    config TEXT,
                    features TEXT,
                    domains TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (parent_tenant_id) REFERENCES tenants(id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tenant_slug ON tenants(slug)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tenant_status ON tenants(status)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tenant_owner ON tenants(owner_id)
            """)

    def create_tenant(
        self,
        name: str,
        slug: str,
        owner_id: str,
        tier: TenantTier = TenantTier.FREE,
        parent_tenant_id: Optional[str] = None,
        contact_email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
        features: Optional[List[str]] = None,
        trial_days: int = 30,
    ) -> Tenant:
        """
        Create a new tenant.

        Args:
            name: Tenant display name
            slug: Unique tenant slug for URLs
            owner_id: ID of the tenant owner user
            tier: Subscription tier
            parent_tenant_id: Parent tenant ID for hierarchical structures
            contact_email: Primary contact email
            metadata: Additional metadata
            config: Tenant-specific configuration
            features: List of enabled features
            trial_days: Trial period in days for trial tenants

        Returns:
            Created tenant
        """
        tenant_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        # Set trial end date for trial tenants
        status = TenantStatus.TRIAL if tier == TenantTier.FREE else TenantStatus.ACTIVE
        trial_ends_at = None
        if status == TenantStatus.TRIAL:
            trial_ends_at = (datetime.now() + timedelta(days=trial_days)).isoformat()

        # Default features based on tier
        default_features = self._get_tier_features(tier)
        features = features or default_features

        tenant = Tenant(
            id=tenant_id,
            name=name,
            slug=slug,
            status=status,
            tier=tier,
            owner_id=owner_id,
            parent_tenant_id=parent_tenant_id,
            contact_email=contact_email,
            billing_email=contact_email,
            metadata=metadata or {},
            config=config or {},
            features=features,
            domains=[],
            created_at=now,
            updated_at=now,
            trial_ends_at=trial_ends_at,
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO tenants (
                    id, name, slug, status, tier, owner_id, parent_tenant_id,
                    contact_email, billing_email, max_users, max_databases,
                    trial_ends_at, metadata, config, features, domains,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tenant.id,
                tenant.name,
                tenant.slug,
                tenant.status.value,
                tenant.tier.value,
                tenant.owner_id,
                tenant.parent_tenant_id,
                tenant.contact_email,
                tenant.billing_email,
                tenant.max_users,
                tenant.max_databases,
                tenant.trial_ends_at,
                json.dumps(tenant.metadata),
                json.dumps(tenant.config),
                json.dumps(tenant.features),
                json.dumps(tenant.domains),
                tenant.created_at,
                tenant.updated_at,
            ))

        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM tenants WHERE id = ?",
                (tenant_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_tenant(dict(row))

    def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM tenants WHERE slug = ?",
                (slug,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_tenant(dict(row))

    def update_tenant(
        self,
        tenant_id: str,
        **updates
    ) -> bool:
        """
        Update tenant properties.

        Args:
            tenant_id: Tenant ID
            **updates: Properties to update

        Returns:
            True if updated successfully
        """
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False

        # Update allowed fields
        allowed_fields = {
            'name', 'status', 'tier', 'contact_email', 'billing_email',
            'max_users', 'max_databases', 'metadata', 'config', 'features', 'domains'
        }

        update_fields = []
        update_values = []

        for key, value in updates.items():
            if key in allowed_fields:
                if key == 'status' and isinstance(value, TenantStatus):
                    value = value.value
                elif key == 'tier' and isinstance(value, TenantTier):
                    value = value.value
                elif key in ['metadata', 'config', 'features', 'domains']:
                    value = json.dumps(value)

                update_fields.append(f"{key} = ?")
                update_values.append(value)

        if not update_fields:
            return False

        update_fields.append("updated_at = ?")
        update_values.append(datetime.now().isoformat())
        update_values.append(tenant_id)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"UPDATE tenants SET {', '.join(update_fields)} WHERE id = ?",
                update_values
            )

        return True

    def delete_tenant(self, tenant_id: str, hard_delete: bool = False) -> bool:
        """
        Delete or archive a tenant.

        Args:
            tenant_id: Tenant ID
            hard_delete: If True, permanently delete; otherwise archive

        Returns:
            True if deleted successfully
        """
        if hard_delete:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM tenants WHERE id = ?", (tenant_id,))
        else:
            self.update_tenant(tenant_id, status=TenantStatus.ARCHIVED)

        return True

    def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        tier: Optional[TenantTier] = None,
        parent_tenant_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Tenant]:
        """
        List tenants with optional filtering.

        Args:
            status: Filter by status
            tier: Filter by tier
            parent_tenant_id: Filter by parent tenant
            limit: Maximum results
            offset: Results offset

        Returns:
            List of tenants
        """
        query = "SELECT * FROM tenants WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status.value)

        if tier:
            query += " AND tier = ?"
            params.append(tier.value)

        if parent_tenant_id:
            query += " AND parent_tenant_id = ?"
            params.append(parent_tenant_id)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([str(limit), str(offset)])

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_tenant(dict(row)) for row in rows]

    def get_tenant_hierarchy(self, tenant_id: str) -> List[Tenant]:
        """Get all child tenants in the hierarchy"""
        tenants = []

        def get_children(parent_id: str):
            children = self.list_tenants(parent_tenant_id=parent_id)
            for child in children:
                tenants.append(child)
                get_children(child.id)

        get_children(tenant_id)
        return tenants

    def _row_to_tenant(self, row: Dict[str, Any]) -> Tenant:
        """Convert database row to Tenant object"""
        return Tenant(
            id=row['id'],
            name=row['name'],
            slug=row['slug'],
            status=TenantStatus(row['status']),
            tier=TenantTier(row['tier']),
            owner_id=row['owner_id'],
            parent_tenant_id=row['parent_tenant_id'],
            contact_email=row['contact_email'],
            billing_email=row['billing_email'],
            max_users=row['max_users'],
            max_databases=row['max_databases'],
            trial_ends_at=row['trial_ends_at'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            config=json.loads(row['config']) if row['config'] else {},
            features=json.loads(row['features']) if row['features'] else [],
            domains=json.loads(row['domains']) if row['domains'] else [],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )

    def _get_tier_features(self, tier: TenantTier) -> List[str]:
        """Get default features for a tier"""
        base_features = ['basic_queries', 'history', 'autocomplete']

        if tier in [TenantTier.STARTER, TenantTier.PROFESSIONAL, TenantTier.ENTERPRISE]:
            base_features.extend(['advanced_queries', 'vector_search', 'ai_assistance'])

        if tier in [TenantTier.PROFESSIONAL, TenantTier.ENTERPRISE]:
            base_features.extend(['audit_logs', 'rbac', 'api_access', 'webhooks'])

        if tier == TenantTier.ENTERPRISE:
            base_features.extend([
                'sso', 'custom_domains', 'dedicated_support',
                'sla_guarantee', 'advanced_security', 'compliance_reports'
            ])

        return base_features

    def get_stats(self) -> Dict[str, Any]:
        """Get tenant statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN status = 'trial' THEN 1 ELSE 0 END) as trial,
                    SUM(CASE WHEN status = 'suspended' THEN 1 ELSE 0 END) as suspended,
                    SUM(CASE WHEN tier = 'free' THEN 1 ELSE 0 END) as free_tier,
                    SUM(CASE WHEN tier = 'enterprise' THEN 1 ELSE 0 END) as enterprise_tier
                FROM tenants
            """)
            row = cursor.fetchone()

            return {
                'total_tenants': row[0],
                'active_tenants': row[1],
                'trial_tenants': row[2],
                'suspended_tenants': row[3],
                'free_tier_tenants': row[4],
                'enterprise_tier_tenants': row[5],
            }
