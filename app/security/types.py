from sqlalchemy.types import LargeBinary, TypeDecorator

from app.security.crypto import get_crypto_provider


class EncryptedString(TypeDecorator):
    """SQLAlchemy type for transparently encrypted strings."""

    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return get_crypto_provider().encrypt_str(value)

    def process_result_value(self, value, dialect):
        return get_crypto_provider().decrypt_str(value)


class EncryptedFloat(TypeDecorator):
    """SQLAlchemy type for transparently encrypted floats."""

    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return get_crypto_provider().encrypt_float(value)

    def process_result_value(self, value, dialect):
        return get_crypto_provider().decrypt_float(value)
