"""
Multi-tenancy support for enterprise features.

Provides tenant isolation, resource management, and configuration.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import threading


@dataclass
class Tenant:
    """Represents a tenant in the system."""
    tenant_id: str
    config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TenantManager:
    """Manages tenant lifecycle and configuration."""

    def __init__(self):
        self._tenants: Dict[str, Tenant] = {}
        self._lock = threading.Lock()

    def create_tenant(self, tenant_id: str, config: Dict[str, Any]) -> Tenant:
        """Create a new tenant instance."""
        with self._lock:
            if tenant_id in self._tenants:
                raise ValueError(f"Tenant {tenant_id} already exists")

            tenant = Tenant(tenant_id=tenant_id, config=config)
            self._tenants[tenant_id] = tenant
            return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        return self._tenants.get(tenant_id)

    def delete_tenant(self, tenant_id: str) -> bool:
        """Delete a tenant."""
        with self._lock:
            if tenant_id in self._tenants:
                del self._tenants[tenant_id]
                return True
            return False


class TenantContext:
    """Thread-local context for tenant-specific operations."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._data: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def set_data(self, key: str, value: Any) -> None:
        """Store tenant-specific data."""
        with self._lock:
            self._data[key] = value

    def get_data(self, key: str) -> Any:
        """Retrieve tenant-specific data."""
        with self._lock:
            return self._data.get(key)

    def clear_data(self) -> None:
        """Clear all tenant data."""
        with self._lock:
            self._data.clear()


class TenantDatabaseManager:
    """Manages separate database instances per tenant."""

    def __init__(self):
        self._databases: Dict[str, Any] = {}
        self._connections: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def create_tenant_database(self, tenant_id: str) -> None:
        """Create a separate database for a tenant."""
        with self._lock:
            if tenant_id in self._databases:
                raise ValueError(f"Database for tenant {tenant_id} already exists")

            # Simulate database creation
            self._databases[tenant_id] = {
                'created_at': datetime.now(),
                'connection_string': f'db://{tenant_id}'
            }

    def get_connection(self, tenant_id: str) -> Any:
        """Get database connection for a tenant."""
        if tenant_id not in self._databases:
            raise ValueError(f"No database for tenant {tenant_id}")

        # Create unique connection object per tenant
        if tenant_id not in self._connections:
            self._connections[tenant_id] = object()  # Unique connection object

        return self._connections[tenant_id]

    def delete_database(self, tenant_id: str) -> bool:
        """Delete tenant database."""
        with self._lock:
            if tenant_id in self._databases:
                del self._databases[tenant_id]
                if tenant_id in self._connections:
                    del self._connections[tenant_id]
                return True
            return False


class TenantQuotaManager:
    """Manages resource quotas per tenant."""

    def __init__(self):
        self._quotas: Dict[str, Dict[str, int]] = {}
        self._usage: Dict[str, Dict[str, int]] = {}
        self._lock = threading.Lock()

    def set_quota(self, tenant_id: str, **limits) -> None:
        """Set resource quotas for a tenant."""
        with self._lock:
            self._quotas[tenant_id] = limits
            if tenant_id not in self._usage:
                self._usage[tenant_id] = {'queries': 0, 'storage_mb': 0}

    def check_quota(self, tenant_id: str, resource: str) -> bool:
        """Check if tenant is within quota for a resource."""
        if tenant_id not in self._quotas:
            return True  # No quota set, allow

        usage = self._usage.get(tenant_id, {})
        quotas = self._quotas.get(tenant_id, {})

        if resource == 'query':
            current = usage.get('queries', 0)
            limit = quotas.get('max_queries', float('inf'))
            return current < limit

        if resource == 'storage':
            current = usage.get('storage_mb', 0)
            limit = quotas.get('max_storage_mb', float('inf'))
            return current < limit

        return True

    def increment_usage(self, tenant_id: str, resource: str, amount: int = 1) -> None:
        """Increment resource usage for a tenant."""
        with self._lock:
            if tenant_id not in self._usage:
                self._usage[tenant_id] = {}

            current = self._usage[tenant_id].get(resource, 0)
            self._usage[tenant_id][resource] = current + amount

    def get_usage(self, tenant_id: str) -> Dict[str, int]:
        """Get current resource usage for a tenant."""
        return self._usage.get(tenant_id, {}).copy()

    def reset_usage(self, tenant_id: str, resource: Optional[str] = None) -> None:
        """Reset usage counters for a tenant."""
        with self._lock:
            if tenant_id in self._usage:
                if resource:
                    self._usage[tenant_id][resource] = 0
                else:
                    self._usage[tenant_id] = {}


class TenantConfigManager:
    """Manages isolated configuration per tenant."""

    def __init__(self):
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def set_config(self, tenant_id: str, key: str, value: Any) -> None:
        """Set configuration value for a tenant."""
        with self._lock:
            if tenant_id not in self._configs:
                self._configs[tenant_id] = {}
            self._configs[tenant_id][key] = value

    def get_config(self, tenant_id: str, key: str, default: Any = None) -> Any:
        """Get configuration value for a tenant."""
        return self._configs.get(tenant_id, {}).get(key, default)

    def get_all_config(self, tenant_id: str) -> Dict[str, Any]:
        """Get all configuration for a tenant."""
        return self._configs.get(tenant_id, {}).copy()

    def delete_config(self, tenant_id: str, key: Optional[str] = None) -> None:
        """Delete configuration for a tenant."""
        with self._lock:
            if tenant_id in self._configs:
                if key:
                    self._configs[tenant_id].pop(key, None)
                else:
                    del self._configs[tenant_id]


class TenantMigrationManager:
    """Manages tenant data migration between databases."""

    def __init__(self):
        self._migrations: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def migrate_tenant(
        self,
        tenant_id: str,
        source: str,
        destination: str,
        verify: bool = False
    ) -> Dict[str, Any]:
        """Migrate tenant data from source to destination."""
        migration_id = f"migration_{tenant_id}_{datetime.now().timestamp()}"

        migration_record = {
            'migration_id': migration_id,
            'tenant_id': tenant_id,
            'source': source,
            'destination': destination,
            'started_at': datetime.now(),
            'status': 'in_progress'
        }

        with self._lock:
            self._migrations.append(migration_record)

        try:
            # Simulate migration process
            # In real implementation, this would copy data between databases
            migration_record['status'] = 'success'
            migration_record['completed_at'] = datetime.now()
            migration_record['verified'] = verify

            return {
                'status': 'success',
                'migration_id': migration_id,
                'verified': verify
            }

        except Exception as e:
            migration_record['status'] = 'failed'
            migration_record['error'] = str(e)
            return {
                'status': 'failed',
                'migration_id': migration_id,
                'error': str(e)
            }

    def get_migration_status(self, migration_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a migration."""
        for migration in self._migrations:
            if migration['migration_id'] == migration_id:
                return migration.copy()
        return None

    def list_migrations(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all migrations, optionally filtered by tenant."""
        if tenant_id:
            return [m for m in self._migrations if m['tenant_id'] == tenant_id]
        return self._migrations.copy()
