"""
Role-Based Access Control (RBAC)

Provides:
- Role definitions with permission sets
- Permission checking
- Role hierarchy support

@ai_prompt: Use RBACManager to check permissions before sensitive operations
@context_boundary: aegistwin/security/rbac
"""

from enum import Enum

from pydantic import BaseModel


class Permission(str, Enum):
    """System permissions."""
    READ_EVENTS = "events:read"
    READ_RUNS = "runs:read"
    READ_POLICIES = "policies:read"
    READ_AUDIT = "audit:read"
    READ_MEMORY = "memory:read"
    READ_GRAPH = "graph:read"

    WRITE_EVENTS = "events:write"
    WRITE_RUNS = "runs:write"
    WRITE_POLICIES = "policies:write"
    WRITE_MEMORY = "memory:write"
    WRITE_GRAPH = "graph:write"

    ADMIN_USERS = "admin:users"
    ADMIN_SYSTEM = "admin:system"
    ADMIN_TENANTS = "admin:tenants"

    REPLAY = "replay:execute"
    INGEST = "ingest:execute"
    QUERY = "query:execute"
    EXPORT = "export:execute"


class Role(BaseModel):
    """Role definition with permissions."""
    name: str
    description: str
    permissions: set[Permission]
    inherits_from: str | None = None


DEFAULT_ROLES: dict[str, Role] = {
    "readonly": Role(
        name="readonly",
        description="Read-only access to all resources",
        permissions={
            Permission.READ_EVENTS,
            Permission.READ_RUNS,
            Permission.READ_POLICIES,
            Permission.READ_AUDIT,
            Permission.READ_MEMORY,
            Permission.READ_GRAPH,
        },
    ),
    "user": Role(
        name="user",
        description="Standard user with read/write access",
        permissions={
            Permission.READ_EVENTS,
            Permission.READ_RUNS,
            Permission.READ_POLICIES,
            Permission.READ_AUDIT,
            Permission.READ_MEMORY,
            Permission.READ_GRAPH,
            Permission.WRITE_EVENTS,
            Permission.WRITE_RUNS,
            Permission.WRITE_MEMORY,
            Permission.WRITE_GRAPH,
            Permission.REPLAY,
            Permission.INGEST,
            Permission.QUERY,
        },
        inherits_from="readonly",
    ),
    "admin": Role(
        name="admin",
        description="Full administrative access",
        permissions=set(Permission),
        inherits_from="user",
    ),
}


class RBACManager:
    """
    Manages roles and permission checking.

    Attributes:
        roles: Registered role definitions
    """

    def __init__(self):
        self.roles: dict[str, Role] = DEFAULT_ROLES.copy()

    def register_role(self, role: Role) -> None:
        """Register a new role."""
        self.roles[role.name] = role

    def get_role(self, role_name: str) -> Role | None:
        """Get role by name."""
        return self.roles.get(role_name)

    def get_effective_permissions(self, role_name: str) -> set[Permission]:
        """Get all permissions for a role including inherited."""
        role = self.get_role(role_name)
        if not role:
            return set()

        permissions = role.permissions.copy()

        if role.inherits_from:
            permissions |= self.get_effective_permissions(role.inherits_from)

        return permissions

    def has_permission(
        self,
        role_name: str,
        permission: Permission,
    ) -> bool:
        """Check if role has specific permission."""
        permissions = self.get_effective_permissions(role_name)
        return permission in permissions

    def check_scopes(
        self,
        user_scopes: list[str],
        required_permission: Permission,
    ) -> bool:
        """
        Check if user scopes grant a permission.

        Scopes can be:
        - Role names (e.g., "admin")
        - Direct permissions (e.g., "events:read")
        - Wildcards (e.g., "*")
        """
        if "*" in user_scopes:
            return True

        if required_permission.value in user_scopes:
            return True

        for scope in user_scopes:
            if scope in self.roles:
                if self.has_permission(scope, required_permission):
                    return True

        return False


_rbac_manager: RBACManager | None = None


def get_rbac_manager() -> RBACManager:
    """Get or create global RBACManager."""
    global _rbac_manager
    if _rbac_manager is None:
        _rbac_manager = RBACManager()
    return _rbac_manager
