"""
AegisTwin Security Module

Provides authentication, authorization, encryption, and rate limiting.

@ai_prompt: Import AuthManager, RBACManager, EncryptionManager from this module
@context_boundary: aegistwin/security
"""

from aegistwin.security.auth import AuthManager, get_current_user, require_auth
from aegistwin.security.encryption import EncryptionManager
from aegistwin.security.middleware import RateLimiter, SecurityMiddleware
from aegistwin.security.rbac import Permission, RBACManager, Role

__all__ = [
    "AuthManager",
    "get_current_user",
    "require_auth",
    "RBACManager",
    "Role",
    "Permission",
    "EncryptionManager",
    "RateLimiter",
    "SecurityMiddleware",
]
