"""
Security Module Tests

Tests authentication, authorization, encryption, and rate limiting.
"""

import pytest
import time
from unittest.mock import MagicMock

from aegistwin.security.auth import AuthManager, User
from aegistwin.security.rbac import RBACManager, Permission, Role
from aegistwin.security.encryption import EncryptionManager
from aegistwin.security.middleware import RateLimiter, RateLimitConfig


class TestAuthManager:
    """Tests for AuthManager."""
    
    def test_create_api_key(self):
        """Test API key creation."""
        auth = AuthManager()
        raw_key, api_key = auth.create_api_key("test-key", ["read", "write"])
        
        assert raw_key.startswith("aegis_")
        assert api_key.name == "test-key"
        assert api_key.scopes == ["read", "write"]
        assert api_key.is_active
    
    def test_validate_api_key(self):
        """Test API key validation."""
        auth = AuthManager()
        raw_key, _ = auth.create_api_key("test", ["read"])
        
        result = auth.validate_api_key(raw_key)
        assert result is not None
        assert result.name == "test"
    
    def test_invalid_api_key(self):
        """Test invalid API key rejection."""
        auth = AuthManager()
        result = auth.validate_api_key("invalid_key")
        assert result is None
    
    def test_revoke_api_key(self):
        """Test API key revocation."""
        auth = AuthManager()
        raw_key, api_key = auth.create_api_key("test", ["read"])
        
        auth.revoke_api_key(api_key.key_id)
        result = auth.validate_api_key(raw_key)
        assert result is None
    
    def test_authenticate_api_key(self):
        """Test authentication with API key."""
        auth = AuthManager()
        raw_key, _ = auth.create_api_key("test", ["admin"])
        
        user = auth.authenticate(raw_key)
        assert user is not None
        assert user.auth_method == "api_key"
        assert "admin" in user.scopes


class TestRBACManager:
    """Tests for RBACManager."""
    
    def test_default_roles_exist(self):
        """Test default roles are registered."""
        rbac = RBACManager()
        
        assert rbac.get_role("readonly") is not None
        assert rbac.get_role("user") is not None
        assert rbac.get_role("admin") is not None
    
    def test_admin_has_all_permissions(self):
        """Test admin role has all permissions."""
        rbac = RBACManager()
        
        for perm in Permission:
            assert rbac.has_permission("admin", perm)
    
    def test_readonly_cannot_write(self):
        """Test readonly role cannot write."""
        rbac = RBACManager()
        
        assert rbac.has_permission("readonly", Permission.READ_EVENTS)
        assert not rbac.has_permission("readonly", Permission.WRITE_EVENTS)
    
    def test_check_scopes_with_wildcard(self):
        """Test wildcard scope grants all permissions."""
        rbac = RBACManager()
        
        assert rbac.check_scopes(["*"], Permission.ADMIN_SYSTEM)


class TestEncryptionManager:
    """Tests for EncryptionManager."""
    
    def test_encrypt_decrypt_string(self):
        """Test string encryption roundtrip."""
        enc = EncryptionManager()
        if not enc.enabled:
            pytest.skip("Cryptography not installed")
        
        plaintext = "Hello, World!"
        ciphertext = enc.encrypt(plaintext)
        decrypted = enc.decrypt(ciphertext)
        
        assert decrypted.decode() == plaintext
    
    def test_encrypt_decrypt_json(self):
        """Test JSON encryption roundtrip."""
        enc = EncryptionManager()
        if not enc.enabled:
            pytest.skip("Cryptography not installed")
        
        data = {"key": "value", "number": 42}
        encrypted = enc.encrypt_json(data)
        decrypted = enc.decrypt_json(encrypted)
        
        assert decrypted == data
    
    def test_key_fingerprint(self):
        """Test key fingerprint generation."""
        enc = EncryptionManager()
        fingerprint = enc.get_key_fingerprint()
        
        assert len(fingerprint) == 16 or fingerprint == "encryption-disabled"


class TestRateLimiter:
    """Tests for RateLimiter."""
    
    def test_allows_requests_under_limit(self):
        """Test requests under limit are allowed."""
        limiter = RateLimiter(RateLimitConfig(requests_per_minute=10))
        request = MagicMock()
        request.headers = {}
        request.client.host = "127.0.0.1"
        
        for _ in range(5):
            allowed, _ = limiter.check(request)
            assert allowed
    
    def test_blocks_requests_over_limit(self):
        """Test requests over limit are blocked."""
        limiter = RateLimiter(RateLimitConfig(requests_per_minute=5, burst_size=5))
        request = MagicMock()
        request.headers = {}
        request.client.host = "127.0.0.1"
        
        for _ in range(5):
            limiter.check(request)
        
        allowed, headers = limiter.check(request)
        assert not allowed
        assert "Retry-After" in headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
