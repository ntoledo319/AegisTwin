"""
Encryption at Rest

Provides:
- AES-256-GCM encryption for sensitive data
- Key derivation from passwords
- Encrypted file I/O

@ai_prompt: Use EncryptionManager for trace files and audit logs
@context_boundary: aegistwin/security/encryption
"""

import base64
import hashlib
import json
import secrets
from pathlib import Path
from typing import Any

try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


class EncryptionManager:
    """
    Manages encryption for data at rest.

    Uses AES-256-GCM for authenticated encryption.

    Attributes:
        key: 256-bit encryption key
    """

    def __init__(self, key: bytes | None = None, password: str | None = None):
        """
        Initialize with either a raw key or derive from password.

        Args:
            key: 32-byte encryption key
            password: Password to derive key from (requires salt)
        """
        if not HAS_CRYPTO:
            self._key = None
            self._enabled = False
            return

        self._enabled = True

        if key:
            if len(key) != 32:
                raise ValueError("Key must be 32 bytes (256 bits)")
            self._key = key
        elif password:
            self._key = self._derive_key(password)
        else:
            self._key = secrets.token_bytes(32)

    @property
    def enabled(self) -> bool:
        """Check if encryption is enabled."""
        return self._enabled

    @staticmethod
    def _derive_key(password: str, salt: bytes | None = None) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        if salt is None:
            salt = secrets.token_bytes(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,
        )
        return kdf.derive(password.encode())

    def encrypt(self, plaintext: str | bytes) -> bytes:
        """
        Encrypt data using AES-256-GCM.

        Returns:
            Encrypted data with nonce prepended (12 + ciphertext bytes)
        """
        if not self._enabled:
            if isinstance(plaintext, str):
                return plaintext.encode()
            return plaintext

        if isinstance(plaintext, str):
            plaintext = plaintext.encode()

        nonce = secrets.token_bytes(12)
        aesgcm = AESGCM(self._key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        return nonce + ciphertext

    def decrypt(self, ciphertext: bytes) -> bytes:
        """
        Decrypt AES-256-GCM encrypted data.

        Args:
            ciphertext: Encrypted data with nonce prepended

        Returns:
            Decrypted plaintext
        """
        if not self._enabled:
            return ciphertext

        nonce = ciphertext[:12]
        actual_ciphertext = ciphertext[12:]

        aesgcm = AESGCM(self._key)
        return aesgcm.decrypt(nonce, actual_ciphertext, None)

    def encrypt_json(self, data: Any) -> str:
        """Encrypt JSON-serializable data to base64 string."""
        json_bytes = json.dumps(data).encode()
        encrypted = self.encrypt(json_bytes)
        return base64.b64encode(encrypted).decode()

    def decrypt_json(self, encrypted_b64: str) -> Any:
        """Decrypt base64 string to JSON data."""
        encrypted = base64.b64decode(encrypted_b64)
        decrypted = self.decrypt(encrypted)
        return json.loads(decrypted.decode())

    def encrypt_file(self, source: Path, dest: Path | None = None) -> Path:
        """
        Encrypt a file.

        Args:
            source: Source file path
            dest: Destination path (default: source + .enc)

        Returns:
            Path to encrypted file
        """
        if dest is None:
            dest = source.with_suffix(source.suffix + ".enc")

        plaintext = source.read_bytes()
        ciphertext = self.encrypt(plaintext)
        dest.write_bytes(ciphertext)

        return dest

    def decrypt_file(self, source: Path, dest: Path | None = None) -> Path:
        """
        Decrypt a file.

        Args:
            source: Encrypted file path
            dest: Destination path (default: remove .enc suffix)

        Returns:
            Path to decrypted file
        """
        if dest is None:
            if source.suffix == ".enc":
                dest = source.with_suffix("")
            else:
                dest = source.with_suffix(".dec")

        ciphertext = source.read_bytes()
        plaintext = self.decrypt(ciphertext)
        dest.write_bytes(plaintext)

        return dest

    def get_key_fingerprint(self) -> str:
        """Get SHA256 fingerprint of encryption key."""
        if not self._key:
            return "encryption-disabled"
        return hashlib.sha256(self._key).hexdigest()[:16]
