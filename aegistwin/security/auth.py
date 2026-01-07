"""
API Key and JWT Authentication

Provides:
- API key generation and validation
- JWT token generation and validation
- FastAPI dependency injection for auth

@ai_prompt: Use require_auth() as FastAPI dependency for protected endpoints
@context_boundary: aegistwin/security/auth
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

try:
    import jwt
    HAS_JWT = True
except ImportError:
    HAS_JWT = False


class APIKey(BaseModel):
    """API Key metadata."""
    key_id: str
    name: str
    scopes: list[str]
    created_at: datetime
    expires_at: datetime | None = None
    is_active: bool = True


class User(BaseModel):
    """Authenticated user context."""
    user_id: str
    scopes: list[str]
    auth_method: str
    metadata: dict[str, Any] = {}


class AuthManager:
    """
    Manages API keys and JWT tokens.

    Attributes:
        secret_key: Secret for JWT signing
        algorithm: JWT algorithm (default HS256)
        api_keys: In-memory API key store (replace with DB in production)
    """

    def __init__(
        self,
        secret_key: str = "aegistwin-secret-change-in-production",
        algorithm: str = "HS256",
        token_expiry_hours: int = 24,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expiry_hours = token_expiry_hours
        self._api_keys: dict[str, APIKey] = {}
        self._key_hashes: dict[str, str] = {}

    def create_api_key(
        self,
        name: str,
        scopes: list[str],
        expires_in_days: int | None = None,
    ) -> tuple[str, APIKey]:
        """
        Generate a new API key.

        Args:
            name: Human-readable name for the key
            scopes: List of permission scopes
            expires_in_days: Optional expiry in days

        Returns:
            Tuple of (raw_key, APIKey metadata)
        """
        key_id = secrets.token_urlsafe(8)
        raw_key = f"aegis_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        api_key = APIKey(
            key_id=key_id,
            name=name,
            scopes=scopes,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
        )

        self._api_keys[key_id] = api_key
        self._key_hashes[key_hash] = key_id

        return raw_key, api_key

    def validate_api_key(self, raw_key: str) -> APIKey | None:
        """Validate an API key and return its metadata."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_id = self._key_hashes.get(key_hash)

        if not key_id:
            return None

        api_key = self._api_keys.get(key_id)
        if not api_key or not api_key.is_active:
            return None

        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            return None

        return api_key

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key by ID."""
        if key_id in self._api_keys:
            self._api_keys[key_id].is_active = False
            return True
        return False

    def create_jwt(
        self,
        subject: str,
        scopes: list[str],
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a JWT token."""
        if not HAS_JWT:
            raise RuntimeError("PyJWT not installed. Install with: pip install PyJWT")

        if expires_delta is None:
            expires_delta = timedelta(hours=self.token_expiry_hours)

        expire = datetime.now(timezone.utc) + expires_delta
        payload = {
            "sub": subject,
            "scopes": scopes,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def validate_jwt(self, token: str) -> dict | None:
        """Validate a JWT token and return payload."""
        if not HAS_JWT:
            return None
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.InvalidTokenError:
            return None

    def authenticate(self, token: str) -> User | None:
        """
        Authenticate a token (API key or JWT).

        Args:
            token: Raw API key or JWT token

        Returns:
            User object if valid, None otherwise
        """
        if token.startswith("aegis_"):
            api_key = self.validate_api_key(token)
            if api_key:
                return User(
                    user_id=api_key.key_id,
                    scopes=api_key.scopes,
                    auth_method="api_key",
                    metadata={"name": api_key.name},
                )

        payload = self.validate_jwt(token)
        if payload:
            return User(
                user_id=payload.get("sub", "unknown"),
                scopes=payload.get("scopes", []),
                auth_method="jwt",
            )

        return None


_auth_manager: AuthManager | None = None


def get_auth_manager() -> AuthManager:
    """Get or create global AuthManager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


def set_auth_manager(manager: AuthManager) -> None:
    """Set global AuthManager instance."""
    global _auth_manager
    _auth_manager = manager


security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User | None:
    """
    FastAPI dependency to get current authenticated user.

    Returns None if no valid auth provided (use require_auth for mandatory auth).
    """
    if credentials is None:
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return get_auth_manager().authenticate(api_key)
        return None

    return get_auth_manager().authenticate(credentials.credentials)


async def require_auth(
    user: User | None = Depends(get_current_user),
) -> User:
    """
    FastAPI dependency that requires authentication.

    Raises HTTPException 401 if not authenticated.
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_scope(required_scope: str):
    """
    Factory for FastAPI dependency that requires a specific scope.

    Usage:
        @app.get("/admin", dependencies=[Depends(require_scope("admin"))])
    """
    async def check_scope(user: User = Depends(require_auth)) -> User:
        if required_scope not in user.scopes and "*" not in user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Scope '{required_scope}' required",
            )
        return user
    return check_scope
