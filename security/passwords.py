"""Password hashing and verification helpers for Personal Habit Tracker."""

import base64
import hashlib
import hmac
import secrets

_ALGORITHM = "pbkdf2_sha256"
_ITERATIONS = 600_000
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    """Return a salted PBKDF2-SHA256 hash in a self-describing format."""
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")

    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _ITERATIONS
    )
    salt_text = base64.urlsafe_b64encode(salt).decode("ascii")
    return f"{_ALGORITHM}${_ITERATIONS}${salt_text}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> tuple[bool, bool]:
    """Return (matches, needs_rehash); accepts legacy unsalted SHA-256 once.

    Legacy SHA-256 support is only for existing accounts created by the earlier
    project prototype. A successful legacy login should be upgraded immediately.
    """
    if not isinstance(password, str) or not isinstance(stored_hash, str):
        return False, False

    parts = stored_hash.split("$")
    if len(parts) == 4 and parts[0] == _ALGORITHM:
        try:
            iterations = int(parts[1])
            salt = base64.urlsafe_b64decode(parts[2].encode("ascii"))
            expected = bytes.fromhex(parts[3])
            actual = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt, iterations
            )
        except (ValueError, TypeError, UnicodeError):
            return False, False
        return hmac.compare_digest(actual, expected), False

    # Earlier signup_window.py stored plain SHA-256 hex digests. Preserve those
    # accounts, but upgrade the hash after a successful login.
    if len(stored_hash) == 64:
        try:
            int(stored_hash, 16)
        except ValueError:
            return False, False
        legacy_digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy_digest, stored_hash.lower()), True

    return False, False
