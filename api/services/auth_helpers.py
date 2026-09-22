import bcrypt
import secrets
import string

def hash_password(plain_password: str) -> str:
    """Convert a plaintext password to a bcrypt hash."""
    salt = bcrypt.gensalt(rounds=12)  # rounds=12 is the recommended default
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if a plaintext password matches the stored hash."""
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except (ValueError, TypeError):
        return False

def generate_temp_password(length: int = 12) -> str:
    """Generate a random temporary password for new tenants."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))