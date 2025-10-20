"""
Database-backed token verifier for FastMCP authentication.
"""
import logging
from fastmcp.server.auth import AccessToken, TokenVerifier
from .key_manager import verify_key_hash, get_key_prefix
from .database import get_db_connection, update_last_used
from .rate_limiter import check_rate_limit

# Configure detailed logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class DatabaseTokenVerifier(TokenVerifier):
    """
    Token verifier that validates API keys against SQLite database.

    Supports both Authorization: Bearer and X-API-Key headers.
    Key format: sk_simone_<32_random_chars>
    """

    def __init__(self):
        """Initialize the database token verifier."""
        super().__init__()

    async def verify_token(self, token: str) -> AccessToken | None:
        """
        Verify API key against database using bcrypt.

        Args:
            token: The API key to verify (from Authorization or X-API-Key header)

        Returns:
            AccessToken with user info if valid, None otherwise
        """
        logger.info("=" * 80)
        logger.info("DATABASE TOKEN VERIFIER: verify_token called")
        logger.info(f"Token provided: {bool(token)}")
        if token:
            logger.info(f"Token format: {token[:18]}... (length: {len(token)})")
        else:
            logger.warning("[FAIL] No token provided")
            return None

        # Validate key format
        if not token.startswith("sk_simone_"):
            logger.error(f"[FAIL] Invalid token format - doesn't start with 'sk_simone_'")
            logger.error(f"Token starts with: {token[:10]}")
            return None

        logger.info("[OK] Token format valid (starts with 'sk_simone_')")

        # Get the key prefix to narrow down database search
        prefix = get_key_prefix(token)
        logger.info(f"Key prefix extracted: {prefix}")

        # Query database for matching prefix
        logger.debug("Connecting to database...")
        conn = get_db_connection()

        try:
            cursor = conn.cursor()

            logger.debug(f"Querying for active keys with prefix: {prefix}")
            cursor.execute("""
                SELECT key_hash, user_email, id FROM api_keys
                WHERE is_active = 1 AND key_prefix = ?
            """, (prefix,))

            rows = cursor.fetchall()  # Get ALL matching rows
            logger.info(f"Found {len(rows)} candidate key(s) in database")
        finally:
            conn.close()  # Always close connection
            logger.debug("Database connection closed")

        if not rows:
            logger.warning(f"[FAIL] No active keys found for prefix: {prefix}")
            return None

        # Try each candidate with bcrypt verification
        logger.debug(f"Verifying token against {len(rows)} candidate(s) with bcrypt...")
        for idx, row in enumerate(rows, 1):
            stored_hash = row['key_hash']
            logger.debug(f"Candidate {idx}: Trying hash {stored_hash[:20]}...")

            # Verify key using bcrypt
            if not verify_key_hash(token, stored_hash):
                logger.debug(f"Candidate {idx}: [FAIL] bcrypt verification failed")
                continue  # Try next candidate

            logger.info(f"Candidate {idx}: [OK] bcrypt verification passed!")

            # Found valid key, extract user info
            user_email = row['user_email']
            key_id = row['id']
            logger.info(f"[OK] Valid key found - User: {user_email}, Key ID: {key_id}")

            # Check rate limit
            logger.debug("Checking rate limit...")
            if not check_rate_limit(stored_hash):
                logger.error("[FAIL] Rate limit exceeded")
                return None
            logger.info("[OK] Rate limit check passed")

            # Update last used timestamp (fire and forget - don't block)
            logger.debug("Updating last_used timestamp...")
            try:
                update_last_used(stored_hash)
                logger.debug("[OK] Timestamp updated")
            except Exception as e:
                logger.warning(f"Failed to update timestamp (non-fatal): {e}")
                pass

            # Return access token with user info
            logger.info("[OK] Returning AccessToken with user claims")
            logger.info(f"Claims: sub={user_email}, key_id={key_id}, prefix={prefix}")
            logger.info(f"Scopes: ['api:access']")
            logger.info("=" * 80)
            return AccessToken(
                token=token,
                client_id=user_email,  # Required field
                claims={
                    "sub": user_email,  # Subject (user identifier)
                    "email": user_email,
                    "key_id": key_id,
                    "key_prefix": prefix
                },
                scopes=["api:access"]  # Basic API access scope
            )

        # No valid key found after checking all candidates
        logger.warning(f"[FAIL] bcrypt verification failed for all {len(rows)} candidate(s)")
        logger.info("=" * 80)
        return None
