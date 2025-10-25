"""
Enterprise features for AI-Shell.

Provides multi-tenancy, advanced RBAC, audit trails, and cloud integrations
for enterprise-grade deployments.
"""

from .tenancy.tenant_manager import TenantManager, Tenant
from .rbac.role_manager import RoleManager, Role
from .rbac.permission_engine import PermissionEngine, Permission
from .audit.audit_logger import AuditLogger, AuditEvent
from .cloud.aws_integration import AWSIntegration
from .cloud.azure_integration import AzureIntegration
from .cloud.gcp_integration import GCPIntegration

__version__ = "1.0.0"

__all__ = [
    "TenantManager",
    "Tenant",
    "RoleManager",
    "Role",
    "PermissionEngine",
    "Permission",
    "AuditLogger",
    "AuditEvent",
    "AWSIntegration",
    "AzureIntegration",
    "GCPIntegration",
]
