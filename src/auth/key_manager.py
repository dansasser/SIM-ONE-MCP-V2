"""
API key generation and validation module.
"""
import secrets
import string
import bcrypt
from typing import Optional, Tuple
from .database import insert_api_key, get_api_key_by_hash, update_last_used


def generate_api_key() -> str:
    """
    Generate a secure random API key.
    Format: sk_simone_<32_random_chars>
    """
    # Use alphanumeric characters for the random part
    alphabet = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(32))
    
    return f"sk_simone_{random_part}"


def hash_api_key(key: str) -> str:
    """Hash an API key using bcrypt."""
    salt = bcrypt.gensalt()
    key_hash = bcrypt.hashpw(key.encode('utf-8'), salt)
    return key_hash.decode('utf-8')


def verify_key_hash(key: str, key_hash: str) -> bool:
    """Verify a key against its hash."""
    try:
        return bcrypt.checkpw(key.encode('utf-8'), key_hash.encode('utf-8'))
    except (ValueError, TypeError):
        return False


def get_key_prefix(key: str) -> str:
    """Extract the prefix from an API key for identification."""
    # Return first 18 characters: sk_simone_ + first 8 of random part
    if len(key) >= 18:
        return key[:18]
    return key


def create_api_key(user_email: str, description: Optional[str] = None) -> Tuple[str, int]:
    """
    Create a new API key for a user.
    Returns: (api_key, key_id)
    """
    # Generate key
    api_key = generate_api_key()
    
    # Hash it
    key_hash = hash_api_key(api_key)
    
    # Get prefix
    key_prefix = get_key_prefix(api_key)
    
    # Store in database
    key_id = insert_api_key(key_hash, key_prefix, user_email, description)
    
    return api_key, key_id


def verify_api_key(key: str) -> bool:
    """
    Verify an API key against the database.
    Returns True if valid and active, False otherwise.
    Also updates last_used_at timestamp.
    """
    if not key or not key.startswith("sk_simone_"):
        return False

    # Get the key prefix to narrow down the search
    prefix = get_key_prefix(key)

    # Query only keys matching this prefix (much more efficient)
    from .database import get_db_connection

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT key_hash FROM api_keys
        WHERE is_active = 1 AND key_prefix = ?
    """, (prefix,))

    rows = cursor.fetchall()
    conn.close()

    # Check each hash (should be very few or just one)
    for row in rows:
        stored_hash = row['key_hash']
        if verify_key_hash(key, stored_hash):
            # Valid key found, update last used
            update_last_used(stored_hash)
            return True

    return False


def revoke_api_key(key_prefix: str) -> bool:
    """Revoke an API key by its prefix."""
    from .database import revoke_key_by_prefix
    return revoke_key_by_prefix(key_prefix)


def list_api_keys(user_email: Optional[str] = None) -> list[dict]:
    """List API keys, optionally filtered by user email."""
    from .database import list_all_keys, list_keys_by_email
    
    if user_email:
        return list_keys_by_email(user_email)
    return list_all_keys()

