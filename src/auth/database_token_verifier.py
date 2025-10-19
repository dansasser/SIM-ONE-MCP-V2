"""
Database-backed token verifier for FastMCP authentication.
"""
from fastmcp.server.auth import AccessToken, Auth
from .key_manager import verify_key_hash, get_key_prefix
from .database import get_db_connection, update_last_used
from .rate_limiter import check_rate_limit


class DatabaseTokenVerifier(Auth):
    """
    Token verifier that validates API keys against SQLite database.

    Supports both Authorization: Bearer and X-API-Key headers.
    Key format: sk_simone_<32_random_chars>
    """

    def __init__(self):
        """Initialize the database token verifier."""
        super().__init__()

    def verify_token(self, token: str) -> AccessToken | None:
        """
        Verify API key against database using bcrypt.

        Args:
            token: The API key to verify (from Authorization or X-API-Key header)

        Returns:
            AccessToken with user info if valid, None otherwise
        """
        # Validate key format
        if not token or not token.startswith("sk_simone_"):
            return None

        # Get the key prefix to narrow down database search
        prefix = get_key_prefix(token)

        # Query database for matching prefix
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT key_hash, user_email, id FROM api_keys
            WHERE is_active = 1 AND key_prefix = ?
        """, (prefix,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        stored_hash = row['key_hash']
        user_email = row['user_email']
        key_id = row['id']

        # Verify key using bcrypt
        if not verify_key_hash(token, stored_hash):
            return None

        # Check rate limit
        if not check_rate_limit(stored_hash):
            return None

        # Update last used timestamp (fire and forget - don't block)
        try:
            update_last_used(stored_hash)
        except Exception:
            # Don't fail auth if timestamp update fails
            pass

        # Return access token with user info
        return AccessToken(
            token=token,
            claims={
                "sub": user_email,  # Subject (user identifier)
                "email": user_email,
                "key_id": key_id,
                "key_prefix": prefix
            },
            scopes=["api:access"]  # Basic API access scope
        )
