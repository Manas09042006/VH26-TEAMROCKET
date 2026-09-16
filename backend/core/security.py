import hashlib
import hmac
import os
import secrets


def get_password_hash(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a random salt."""
    salt = os.urandom(16).hex()
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=100000
    ).hex()
    return f"{salt}${key}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the stored salt$hash string."""
    if not hashed_password or "$" not in hashed_password:
        return False
    try:
        salt, stored_hash = hashed_password.split("$", 1)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=100000
        ).hex()
        return hmac.compare_digest(key, stored_hash)
    except Exception:
        return False


def generate_token() -> str:
    """Generate a random cryptographic bearer token."""
    return secrets.token_hex(32)
