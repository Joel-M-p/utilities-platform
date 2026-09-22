"""Password hashing and generation.

Passwords were originally stored as a single unsalted SHA-256 round. SHA-256 is a fast
general-purpose hash with no work factor, so those hashes are crackable at very high speed
on commodity GPUs, and without a per-user salt identical passwords produce identical hashes
(rainbow-table friendly).

This module moves new and changed passwords to bcrypt while still accepting the old hashes,
so nobody is locked out. auth.py calls needs_rehash() after a successful login and silently
upgrades that user's stored hash to bcrypt - meaning the legacy hashes drain away on their
own as people log in, with no forced password reset.
"""
import hashlib
import hmac
import secrets
import string

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:  # pragma: no cover
    BCRYPT_AVAILABLE = False


def _legacy_sha256(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _is_legacy_hash(stored_hash: str) -> bool:
    """A legacy hash is 64 hex chars; a bcrypt hash starts with $2b$/$2a$/$2y$."""
    if not stored_hash:
        return False
    return len(stored_hash) == 64 and all(c in "0123456789abcdef" for c in stored_hash.lower())


def hash_password(password: str) -> str:
    """Hash a new password. Uses bcrypt when available, falls back to legacy if not."""
    if not BCRYPT_AVAILABLE:
        # Fall back rather than crash, so a missing dependency can't take down user
        # creation. Install bcrypt (it is in requirements.txt) to get the real protection.
        return _legacy_sha256(password)
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, stored_hash: str) -> bool:
    """Check a password against either a bcrypt hash or a legacy SHA-256 hash.

    Returns False (rather than raising) when stored_hash is None, so callers can invoke this
    even for a username that does not exist and keep the response time constant.
    """
    if not password:
        return False

    if not stored_hash:
        # Do a throwaway hash so a nonexistent user costs roughly the same time as a real
        # one, avoiding a timing side channel that would enumerate valid usernames.
        if BCRYPT_AVAILABLE:
            bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return False

    if _is_legacy_hash(stored_hash):
        return hmac.compare_digest(_legacy_sha256(password), stored_hash)

    if not BCRYPT_AVAILABLE:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def needs_rehash(stored_hash: str) -> bool:
    """True if this hash is legacy SHA-256 and should be upgraded to bcrypt on next login."""
    return BCRYPT_AVAILABLE and _is_legacy_hash(stored_hash)


def generate_temp_password(length: int = 12) -> str:
    """Generate a cryptographically random temporary password for new tenants.

    Uses the secrets module (not random) for cryptographic security.
    Contains uppercase, lowercase, digits, and special characters.
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    # Guarantee at least one of each character class for strength
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*"),
    ]
    # Fill the rest randomly
    password += [secrets.choice(alphabet) for _ in range(length - 4)]
    # Shuffle so the guaranteed chars aren't always at the start
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)