import base64
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class CryptoProvider:
    """Interface for PHI encryption providers."""

    def encrypt_str(self, s: Optional[str]) -> Optional[bytes]:
        raise NotImplementedError

    def decrypt_str(self, b: Optional[bytes]) -> Optional[str]:
        raise NotImplementedError

    def encrypt_float(self, x: Optional[float]) -> Optional[bytes]:
        raise NotImplementedError

    def decrypt_float(self, b: Optional[bytes]) -> Optional[float]:
        raise NotImplementedError


class AppCryptoProvider(CryptoProvider):
    """Encrypt/decrypt using Fernet (AES-128 CBC with HMAC)."""

    def __init__(self, key_b64: str):
        self._fernet = Fernet(key_b64.encode())

    def encrypt_str(self, s: Optional[str]) -> Optional[bytes]:
        if s is None:
            return None
        return self._fernet.encrypt(s.encode())

    def decrypt_str(self, b: Optional[bytes]) -> Optional[str]:
        if b is None:
            return None
        try:
            return self._fernet.decrypt(b).decode()
        except InvalidToken:
            raise ValueError("Invalid encryption token")

    def encrypt_float(self, x: Optional[float]) -> Optional[bytes]:
        if x is None:
            return None
        return self._fernet.encrypt(str(x).encode())

    def decrypt_float(self, b: Optional[bytes]) -> Optional[float]:
        if b is None:
            return None
        try:
            return float(self._fernet.decrypt(b).decode())
        except InvalidToken:
            raise ValueError("Invalid encryption token")


class PgcryptoProvider(CryptoProvider):
    """Placeholder for PostgreSQL pgcrypto-based encryption."""

    def __init__(self, *args, **kwargs):  # pragma: no cover - placeholder
        raise NotImplementedError("Pgcrypto provider not implemented")


_provider: Optional[CryptoProvider] = None


def get_crypto_provider() -> CryptoProvider:
    """Return a cached crypto provider instance based on settings."""
    global _provider
    if _provider is None:
        if settings.PHI_PROVIDER == "app":
            _provider = AppCryptoProvider(settings.PHI_ENCRYPTION_KEY)
        elif settings.PHI_PROVIDER == "pgcrypto":  # pragma: no cover - future option
            _provider = PgcryptoProvider()
        else:
            raise ValueError(f"Unknown PHI provider: {settings.PHI_PROVIDER}")
    return _provider


def reset_crypto_provider() -> None:
    """Reset cached provider (e.g. after key rotation)."""
    global _provider
    _provider = None
